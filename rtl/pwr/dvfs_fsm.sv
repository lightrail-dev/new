// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     dvfs_fsm
// DESCRIPTION: Dynamic Voltage and Frequency Scaling state machine.
//              Monitors temperature and workload to transition between
//              power/performance states. Issues voltage change commands
//              via PMBus and frequency change requests to the PLL.
//
// DVFS LEVELS:
//   TURBO     — V_CORE=0.85V, Freq=2.0GHz, Power=900W
//   NOMINAL   — V_CORE=0.80V, Freq=1.8GHz, Power=750W
//   LOW_POWER — V_CORE=0.72V, Freq=1.2GHz, Power=400W
//   EMERGENCY — V_CORE=0.65V, Freq=0.8GHz, Power=250W (thermal throttle)
// =========================================================================

module dvfs_fsm (
    input  wire        clk,
    input  wire        rst_n,

    // Telemetry inputs (from PMBus reads)
    input  wire [15:0] temperature,    // degC × 256 (8.8 fixed-point)
    input  wire [15:0] current_amps,   // A × 256
    input  wire [15:0] voltage_mv,     // mV

    // Workload hint (from NCE core, 0=idle, 255=max)
    input  wire [7:0]  workload_level,

    // DVFS control outputs
    output reg  [1:0]  dvfs_state,     // 0=TURBO, 1=NOMINAL, 2=LOW_POWER, 3=EMERGENCY
    output reg  [15:0] target_voltage, // mV
    output reg  [15:0] target_freq,    // MHz
    output reg         dvfs_change_req,

    // Override from host register
    input  wire        dvfs_force_en,
    input  wire [1:0]  dvfs_force_level,

    // Thermal emergency
    output reg         thermal_shutdown
);

    localparam [1:0] LVL_TURBO     = 2'd0,
                     LVL_NOMINAL   = 2'd1,
                     LVL_LOW_POWER = 2'd2,
                     LVL_EMERGENCY = 2'd3;

    // Temperature thresholds (8.8 fixed-point, degC)
    localparam [15:0] TEMP_TURBO_MAX   = 16'h4D00;  // 77°C
    localparam [15:0] TEMP_NOM_MAX     = 16'h5500;  // 85°C
    localparam [15:0] TEMP_LP_MAX      = 16'h5F00;  // 95°C
    localparam [15:0] TEMP_SHUTDOWN    = 16'h6400;  // 100°C

    // Hysteresis (2°C)
    localparam [15:0] TEMP_HYST = 16'h0200;

    // Voltage/frequency lookup
    function automatic [31:0] dvfs_lookup;
        input [1:0] level;
        begin
            case (level)
                LVL_TURBO:     dvfs_lookup = {16'd850,  16'd2000};
                LVL_NOMINAL:   dvfs_lookup = {16'd800,  16'd1800};
                LVL_LOW_POWER: dvfs_lookup = {16'd720,  16'd1200};
                LVL_EMERGENCY: dvfs_lookup = {16'd650,  16'd800};
            endcase
        end
    endfunction

    reg [1:0] next_level;
    reg [19:0] debounce_cnt;
    reg [31:0] dvfs_lut_val;
    localparam [19:0] DEBOUNCE_MAX = 20'hFFFFF; // ~5ms at 200MHz

    always @(posedge clk) begin
        if (!rst_n) begin
            dvfs_state      <= LVL_NOMINAL;
            target_voltage  <= 16'd800;
            target_freq     <= 16'd1800;
            dvfs_change_req <= 1'b0;
            thermal_shutdown <= 1'b0;
            debounce_cnt    <= 20'd0;
            next_level      <= LVL_NOMINAL;
            dvfs_lut_val    <= 32'd0;
        end else begin
            dvfs_change_req  <= 1'b0;
            thermal_shutdown <= 1'b0;

            // Thermal shutdown check (unconditional)
            if (temperature >= TEMP_SHUTDOWN) begin
                thermal_shutdown <= 1'b1;
                next_level       <= LVL_EMERGENCY;
                debounce_cnt     <= DEBOUNCE_MAX; // immediate
            end

            // Force mode from host
            if (dvfs_force_en) begin
                next_level <= dvfs_force_level;
                debounce_cnt <= DEBOUNCE_MAX;
            end else begin
                // Auto DVFS based on temperature and workload
                if (temperature >= TEMP_LP_MAX) begin
                    next_level <= LVL_EMERGENCY;
                end else if (temperature >= TEMP_NOM_MAX) begin
                    next_level <= LVL_LOW_POWER;
                end else if (temperature >= TEMP_TURBO_MAX) begin
                    next_level <= LVL_NOMINAL;
                end else if (workload_level > 8'd200) begin
                    next_level <= LVL_TURBO;
                end else if (workload_level > 8'd100) begin
                    next_level <= LVL_NOMINAL;
                end else begin
                    next_level <= LVL_LOW_POWER;
                end
            end

            // Debounce and transition
            if (next_level != dvfs_state) begin
                if (debounce_cnt >= DEBOUNCE_MAX) begin
                    dvfs_lut_val    = dvfs_lookup(next_level);
                    dvfs_state      <= next_level;
                    target_voltage  <= dvfs_lut_val[31:16];
                    target_freq     <= dvfs_lut_val[15:0];
                    dvfs_change_req <= 1'b1;
                    debounce_cnt    <= 20'd0;
                end else begin
                    debounce_cnt <= debounce_cnt + 20'd1;
                end
            end else begin
                debounce_cnt <= 20'd0;
            end
        end
    end

endmodule

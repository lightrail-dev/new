// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     pwr_mgt_controller
// DESCRIPTION: Power and Thermal Management Controller. Integrates an
//              I2C/PMBus master for VRM telemetry and a DVFS FSM for
//              dynamic voltage/frequency scaling. Periodically polls
//              VRM controllers for voltage, current, and temperature,
//              then drives DVFS state transitions.
//
// INTERFACE:  Register-mapped from host_interface (0x0800–0x08FF)
//
// REGISTER MAP (8-bit sub-address):
//   0x00: PWR_CTRL       — bit 0: telemetry enable, bit 1: DVFS force en
//   0x04: PWR_STATUS     — bit[1:0]: DVFS state, bit[2]: thermal shutdown
//   0x08: TEMP_READ      — latest temperature (16-bit 8.8 FP)
//   0x0C: CURRENT_READ   — latest current (16-bit)
//   0x10: VOLTAGE_READ   — latest voltage (16-bit mV)
//   0x14: DVFS_FORCE_LVL — force DVFS level [1:0]
//   0x18: WORKLOAD_HINT  — software workload hint [7:0]
//   0x1C: TARGET_VOLTAGE — current target voltage (RO)
//   0x20: TARGET_FREQ    — current target frequency (RO)
// =========================================================================

module pwr_mgt_controller #(
    parameter integer CLK_FREQ_HZ    = 200_000_000,
    parameter integer I2C_FREQ_HZ    = 400_000,
    parameter integer POLL_INTERVAL  = 200_000_000  // 1 second at 200 MHz
)(
    input  wire        clk,
    input  wire        rst_n,

    // Register interface (from host_interface)
    input  wire [7:0]  reg_addr,
    input  wire [31:0] reg_wdata,
    input  wire        reg_wen,
    input  wire        reg_ren,
    output reg  [31:0] reg_rdata,
    output reg         reg_rvalid,

    // I2C PHY
    output wire        scl_out,
    output wire        scl_oen,
    input  wire        scl_in,
    output wire        sda_out,
    output wire        sda_oen,
    input  wire        sda_in,

    // DVFS output to PLL / voltage regulator
    output wire [1:0]  dvfs_state,
    output wire [15:0] target_voltage,
    output wire [15:0] target_freq,
    output wire        dvfs_change_req,
    output wire        thermal_shutdown
);

    // ---- Internal Registers ----
    reg        telemetry_enable;
    reg        dvfs_force_en;
    reg [1:0]  dvfs_force_level;
    reg [7:0]  workload_hint;
    reg [15:0] temp_reading;
    reg [15:0] current_reading;
    reg [15:0] voltage_reading;

    // ---- I2C Master ----
    reg        i2c_cmd_valid;
    reg        i2c_cmd_read;
    reg [6:0]  i2c_slave_addr;
    reg [7:0]  i2c_reg_addr;
    reg [7:0]  i2c_wdata;
    wire [7:0] i2c_rdata;
    wire       i2c_done;
    wire       i2c_ack_err;

    i2c_master #(
        .CLK_FREQ_HZ(CLK_FREQ_HZ),
        .I2C_FREQ_HZ(I2C_FREQ_HZ)
    ) u_i2c (
        .clk           (clk),
        .rst_n         (rst_n),
        .cmd_valid     (i2c_cmd_valid),
        .cmd_read      (i2c_cmd_read),
        .cmd_slave_addr(i2c_slave_addr),
        .cmd_reg_addr  (i2c_reg_addr),
        .cmd_wdata     (i2c_wdata),
        .cmd_rdata     (i2c_rdata),
        .cmd_done      (i2c_done),
        .cmd_ack_err   (i2c_ack_err),
        .scl_out       (scl_out),
        .scl_oen       (scl_oen),
        .scl_in        (scl_in),
        .sda_out       (sda_out),
        .sda_oen       (sda_oen),
        .sda_in        (sda_in)
    );

    // ---- DVFS FSM ----
    dvfs_fsm u_dvfs (
        .clk             (clk),
        .rst_n           (rst_n),
        .temperature     (temp_reading),
        .current_amps    (current_reading),
        .voltage_mv      (voltage_reading),
        .workload_level  (workload_hint),
        .dvfs_state      (dvfs_state),
        .target_voltage  (target_voltage),
        .target_freq     (target_freq),
        .dvfs_change_req (dvfs_change_req),
        .dvfs_force_en   (dvfs_force_en),
        .dvfs_force_level(dvfs_force_level),
        .thermal_shutdown(thermal_shutdown)
    );

    // ---- Telemetry Polling FSM ----
    // Polls VRM temperature, current, and voltage in round-robin
    localparam [6:0] VRM_I2C_ADDR = 7'h40; // ISL69260 default address
    localparam [7:0] PMBUS_READ_TEMP  = 8'h8D;
    localparam [7:0] PMBUS_READ_IOUT  = 8'h8C;
    localparam [7:0] PMBUS_READ_VOUT  = 8'h8B;

    localparam [2:0] POLL_IDLE      = 3'd0,
                     POLL_TEMP_CMD  = 3'd1,
                     POLL_TEMP_WAIT = 3'd2,
                     POLL_IOUT_CMD  = 3'd3,
                     POLL_IOUT_WAIT = 3'd4,
                     POLL_VOUT_CMD  = 3'd5,
                     POLL_VOUT_WAIT = 3'd6;

    reg [2:0]  poll_state;
    reg [27:0] poll_timer;
    reg [7:0]  telemetry_hi; // high byte accumulator for 16-bit reads

    always @(posedge clk) begin
        if (!rst_n) begin
            poll_state      <= POLL_IDLE;
            poll_timer      <= 28'd0;
            i2c_cmd_valid   <= 1'b0;
            i2c_cmd_read    <= 1'b0;
            i2c_slave_addr  <= 7'd0;
            i2c_reg_addr    <= 8'd0;
            i2c_wdata       <= 8'd0;
            temp_reading    <= 16'd0;
            current_reading <= 16'd0;
            voltage_reading <= 16'd0;
            telemetry_hi    <= 8'd0;
        end else begin
            i2c_cmd_valid <= 1'b0;

            case (poll_state)
                POLL_IDLE: begin
                    if (telemetry_enable) begin
                        if (poll_timer >= POLL_INTERVAL[27:0]) begin
                            poll_timer <= 28'd0;
                            poll_state <= POLL_TEMP_CMD;
                        end else begin
                            poll_timer <= poll_timer + 28'd1;
                        end
                    end
                end

                POLL_TEMP_CMD: begin
                    i2c_cmd_valid  <= 1'b1;
                    i2c_cmd_read   <= 1'b1;
                    i2c_slave_addr <= VRM_I2C_ADDR;
                    i2c_reg_addr   <= PMBUS_READ_TEMP;
                    poll_state     <= POLL_TEMP_WAIT;
                end

                POLL_TEMP_WAIT: begin
                    if (i2c_done) begin
                        temp_reading <= {i2c_rdata, 8'd0};
                        poll_state   <= POLL_IOUT_CMD;
                    end
                end

                POLL_IOUT_CMD: begin
                    i2c_cmd_valid  <= 1'b1;
                    i2c_cmd_read   <= 1'b1;
                    i2c_slave_addr <= VRM_I2C_ADDR;
                    i2c_reg_addr   <= PMBUS_READ_IOUT;
                    poll_state     <= POLL_IOUT_WAIT;
                end

                POLL_IOUT_WAIT: begin
                    if (i2c_done) begin
                        current_reading <= {i2c_rdata, 8'd0};
                        poll_state      <= POLL_VOUT_CMD;
                    end
                end

                POLL_VOUT_CMD: begin
                    i2c_cmd_valid  <= 1'b1;
                    i2c_cmd_read   <= 1'b1;
                    i2c_slave_addr <= VRM_I2C_ADDR;
                    i2c_reg_addr   <= PMBUS_READ_VOUT;
                    poll_state     <= POLL_VOUT_WAIT;
                end

                POLL_VOUT_WAIT: begin
                    if (i2c_done) begin
                        voltage_reading <= {i2c_rdata, 8'd0};
                        poll_state      <= POLL_IDLE;
                    end
                end

                default: poll_state <= POLL_IDLE;
            endcase
        end
    end

    // ---- Register Interface ----
    always @(posedge clk) begin
        if (!rst_n) begin
            telemetry_enable <= 1'b0;
            dvfs_force_en    <= 1'b0;
            dvfs_force_level <= 2'd1;  // NOMINAL default
            workload_hint    <= 8'd128;
            reg_rdata        <= 32'd0;
            reg_rvalid       <= 1'b0;
        end else begin
            reg_rvalid <= 1'b0;

            if (reg_wen) begin
                case (reg_addr)
                    8'h00: begin
                        telemetry_enable <= reg_wdata[0];
                        dvfs_force_en    <= reg_wdata[1];
                    end
                    8'h14: dvfs_force_level <= reg_wdata[1:0];
                    8'h18: workload_hint    <= reg_wdata[7:0];
                    default: ;
                endcase
            end

            if (reg_ren) begin
                reg_rvalid <= 1'b1;
                case (reg_addr)
                    8'h00: reg_rdata <= {30'd0, dvfs_force_en, telemetry_enable};
                    8'h04: reg_rdata <= {29'd0, thermal_shutdown, dvfs_state};
                    8'h08: reg_rdata <= {16'd0, temp_reading};
                    8'h0C: reg_rdata <= {16'd0, current_reading};
                    8'h10: reg_rdata <= {16'd0, voltage_reading};
                    8'h14: reg_rdata <= {30'd0, dvfs_force_level};
                    8'h18: reg_rdata <= {24'd0, workload_hint};
                    8'h1C: reg_rdata <= {16'd0, target_voltage};
                    8'h20: reg_rdata <= {16'd0, target_freq};
                    default: reg_rdata <= 32'd0;
                endcase
            end
        end
    end

endmodule

// =========================================================================
// COMPANY:    LightRail AI — Open Compute Project (OCP) Compatible TFLN Core
// MODULE:     tfln_qpu_trigger_matrix
// DESCRIPTION: Decodes phase configurations from CXL/PCIe host and executes
//              zero-skew synchronized RF pulses to 100 GHz Interleaved DACs.
//              Part of the OCP Multi-Chip Module (MCM) accelerator sled.
//
// INTERFACE:   CXL 2.0 memory-mapped registers → shadow buffer → DAC sync
// CLOCK:       250 MHz system clock (from host FPGA PLL)
// RESET:       Active-low synchronous reset
//
// REGISTER MAP:
//   0x0000_1000  PHASE_SET       — Write phase vector into shadow buffer
//   0x0000_1004  TRIGGER_EXEC    — Commit shadow buffer to DAC bus + sync pulse
//   0x0000_1008  STATUS          — Read trigger state and channel health
//   0x0000_100C  FAULT_MASK      — Per-channel fault mask register
//   0x0000_1010  TELEMETRY_CTRL  — Telemetry sampling control
//
// NOTES:
//   - Two-stage pipeline ensures zero-skew between phase_set and dac_sync.
//   - Shadow buffer allows atomic phase vector updates across all channels.
//   - Fault detection monitors per-channel optical power via SNSPD feedback.
// =========================================================================

module tfln_qpu_trigger_matrix #(
    parameter integer NUM_CHANNELS   = 8,
    parameter integer PHASE_WIDTH    = 16,
    parameter integer FAULT_WIDTH    = 8,
    parameter integer TELEMETRY_BITS = 32
)(
    // System
    input  wire                                    clk_250mhz,
    input  wire                                    rst_n,

    // CXL / PCIe Host Interface
    input  wire                                    cxl_valid,
    input  wire [63:0]                             cxl_addr,
    input  wire [(NUM_CHANNELS*PHASE_WIDTH)-1:0]   cxl_data,
    output reg                                     cxl_ready,

    // DAC Interface (to 100 GHz Interleaved DACs)
    output reg                                     dac_sync_trigger,
    output reg  [(NUM_CHANNELS*PHASE_WIDTH)-1:0]   dac_phase_bus,

    // SNSPD Fault Feedback (from photodetectors)
    input  wire [NUM_CHANNELS-1:0]                 snspd_power_ok,

    // Telemetry (to OpenBMC via CXL MMIO)
    output reg  [TELEMETRY_BITS-1:0]               telemetry_status,

    // Fault Mitigation
    output reg                                     fault_interrupt,
    output reg  [NUM_CHANNELS-1:0]                 channel_reroute
);

    // ---- Register Addresses ----
    localparam [31:0] ADDR_PHASE_SET      = 32'h0000_1000;
    localparam [31:0] ADDR_TRIGGER_EXEC   = 32'h0000_1004;
    localparam [31:0] ADDR_STATUS         = 32'h0000_1008;
    localparam [31:0] ADDR_FAULT_MASK     = 32'h0000_100C;
    localparam [31:0] ADDR_TELEMETRY_CTRL = 32'h0000_1010;

    // ---- Internal Registers ----
    reg [(NUM_CHANNELS*PHASE_WIDTH)-1:0] phase_shadow_buffer;
    reg                                  trigger_pipeline;
    reg [NUM_CHANNELS-1:0]               fault_mask;
    reg [NUM_CHANNELS-1:0]               fault_latch;
    reg [15:0]                           trigger_count;
    reg [15:0]                           fault_count;
    reg                                  telemetry_enable;

    // ---- Optical Power Monitoring (3 dB drop detection) ----
    reg [NUM_CHANNELS-1:0] snspd_prev;
    wire [NUM_CHANNELS-1:0] power_drop = snspd_prev & ~snspd_power_ok;

    // ---- Main Control Logic ----
    always @(posedge clk_250mhz) begin
        if (!rst_n) begin
            cxl_ready           <= 1'b0;
            phase_shadow_buffer <= {NUM_CHANNELS*PHASE_WIDTH{1'b0}};
            dac_phase_bus       <= {NUM_CHANNELS*PHASE_WIDTH{1'b0}};
            dac_sync_trigger    <= 1'b0;
            trigger_pipeline    <= 1'b0;
            fault_mask          <= {NUM_CHANNELS{1'b1}};  // all channels enabled
            fault_latch         <= {NUM_CHANNELS{1'b0}};
            trigger_count       <= 16'd0;
            fault_count         <= 16'd0;
            telemetry_enable    <= 1'b0;
            fault_interrupt     <= 1'b0;
            channel_reroute     <= {NUM_CHANNELS{1'b0}};
            snspd_prev          <= {NUM_CHANNELS{1'b1}};
            telemetry_status    <= {TELEMETRY_BITS{1'b0}};
        end else begin
            cxl_ready        <= 1'b1;
            dac_sync_trigger <= 1'b0;
            fault_interrupt  <= 1'b0;

            // ---- CXL Register Decode ----
            if (cxl_valid && cxl_ready) begin
                case (cxl_addr[31:0])
                    ADDR_PHASE_SET: begin
                        phase_shadow_buffer <= cxl_data;
                    end
                    ADDR_TRIGGER_EXEC: begin
                        // Atomic commit: shadow → DAC bus
                        dac_phase_bus    <= phase_shadow_buffer;
                        trigger_pipeline <= 1'b1;
                        trigger_count    <= trigger_count + 16'd1;
                    end
                    ADDR_FAULT_MASK: begin
                        fault_mask <= cxl_data[NUM_CHANNELS-1:0];
                    end
                    ADDR_TELEMETRY_CTRL: begin
                        telemetry_enable <= cxl_data[0];
                    end
                    default: ;
                endcase
            end

            // ---- Zero-Skew DAC Sync (1-cycle pipeline) ----
            if (trigger_pipeline) begin
                dac_sync_trigger <= 1'b1;
                trigger_pipeline <= 1'b0;
            end

            // ---- SNSPD Fault Detection ----
            snspd_prev <= snspd_power_ok;
            if (|(power_drop & fault_mask)) begin
                fault_latch     <= fault_latch | (power_drop & fault_mask);
                fault_interrupt <= 1'b1;
                fault_count     <= fault_count + 16'd1;
                // Automatic waveguide rerouting: reroute faulted channels
                // to standby parallel MZI paths on the TFLN chip
                channel_reroute <= power_drop & fault_mask;
            end

            // ---- Telemetry Status Register ----
            if (telemetry_enable) begin
                telemetry_status <= {fault_count, trigger_count};
            end
        end
    end

endmodule


// =========================================================================
// MODULE:     tfln_dac_lvds_serializer
// DESCRIPTION: Serializes parallel phase data onto LVDS lanes for the
//              100 GHz Interleaved DAC array. Uses DDR output registers
//              for maximum throughput on Megtron-7 substrate.
// =========================================================================

module tfln_dac_lvds_serializer #(
    parameter integer NUM_CHANNELS = 8,
    parameter integer PHASE_WIDTH  = 16
)(
    input  wire                                    clk_500mhz,     // 2x system clock for DDR
    input  wire                                    clk_250mhz,     // system clock
    input  wire                                    rst_n,
    input  wire                                    dac_sync_trigger,
    input  wire [(NUM_CHANNELS*PHASE_WIDTH)-1:0]   dac_phase_bus,
    output reg  [NUM_CHANNELS-1:0]                 lvds_data_p,
    output reg  [NUM_CHANNELS-1:0]                 lvds_data_n,
    output reg                                     lvds_sync_p,
    output reg                                     lvds_sync_n
);

    reg [4:0] bit_counter;
    reg       active;
    reg [(NUM_CHANNELS*PHASE_WIDTH)-1:0] shift_reg;

    always @(posedge clk_500mhz) begin
        if (!rst_n) begin
            lvds_data_p <= {NUM_CHANNELS{1'b0}};
            lvds_data_n <= {NUM_CHANNELS{1'b1}};
            lvds_sync_p <= 1'b0;
            lvds_sync_n <= 1'b1;
            bit_counter <= 5'd0;
            active      <= 1'b0;
            shift_reg   <= {NUM_CHANNELS*PHASE_WIDTH{1'b0}};
        end else begin
            lvds_sync_p <= 1'b0;
            lvds_sync_n <= 1'b1;

            if (dac_sync_trigger && !active) begin
                active      <= 1'b1;
                shift_reg   <= dac_phase_bus;
                bit_counter <= 5'd0;
                lvds_sync_p <= 1'b1;
                lvds_sync_n <= 1'b0;
            end

            if (active) begin
                // Shift out MSB-first for each channel
                for (integer ch = 0; ch < NUM_CHANNELS; ch = ch + 1) begin
                    lvds_data_p[ch] <=  shift_reg[(ch+1)*PHASE_WIDTH - 1];
                    lvds_data_n[ch] <= ~shift_reg[(ch+1)*PHASE_WIDTH - 1];
                end

                // Shift all channels left by 1
                for (integer ch = 0; ch < NUM_CHANNELS; ch = ch + 1) begin
                    shift_reg[(ch+1)*PHASE_WIDTH-1 -: PHASE_WIDTH] <=
                        {shift_reg[(ch+1)*PHASE_WIDTH-2 -: (PHASE_WIDTH-1)], 1'b0};
                end

                bit_counter <= bit_counter + 5'd1;
                if (bit_counter == PHASE_WIDTH - 1) begin
                    active <= 1'b0;
                end
            end
        end
    end

endmodule

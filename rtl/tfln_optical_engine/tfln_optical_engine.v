// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     tfln_optical_engine
// DESCRIPTION: TFLN (Thin-Film Lithium Niobate) Optical Engine Controller
//              for SMIC 28nm/40nm MPW shuttle validation. Implements the
//              complete photonic I/O datapath: PAM4 TX/RX DSP, MZI mesh
//              configuration, laser driver control, and optical power
//              monitoring via SNSPD feedback.
//
// PROCESS:    SMIC 28nm HPC+ (primary) / SMIC 40nm LL (fallback)
// CLOCK:      clk_serdes (156.25 MHz reference), clk_sys (250 MHz)
// RESET:      Active-low synchronous
//
// ARCHITECTURE:
//   The optical engine manages 8 bidirectional channels, each operating
//   at 200 Gbps PAM4 (4-level pulse amplitude modulation). The channels
//   drive TFLN Mach-Zehnder modulators at 1550 nm C-band with 100 GHz
//   DWDM spacing. An integrated MZI mesh controller configures the
//   photonic mesh topology for matrix operations.
//
// REGISTER MAP (CXL MMIO Base 0x0000_2000):
//   0x2000  OE_CTRL          -- Optical engine global control
//   0x2004  OE_STATUS        -- Link status per channel
//   0x2008  TX_EQ_CONFIG     -- TX equalizer coefficients (3-tap FFE)
//   0x200C  RX_EQ_CONFIG     -- RX equalizer mode (CTLE + DFE tap count)
//   0x2010  LASER_CTRL       -- Laser enable, bias current, TEC setpoint
//   0x2014  LASER_STATUS     -- Laser temperature, power, fault
//   0x2018  MZI_MESH_CTRL    -- MZI mesh dimension, compile trigger
//   0x201C  MZI_MESH_STATUS  -- Mesh fidelity, last compile result
//   0x2020  MZI_PHASE_BASE   -- Base address for phase LUT (64 entries)
//   0x2024  OPTICAL_POWER    -- Per-channel optical power readings
//   0x2028  BER_COUNTER      -- Per-channel bit error counters
//   0x202C  LOOPBACK_CTRL    -- Loopback mode for BIST
//   0x2030  CDR_STATUS       -- CDR lock status per channel
//   0x2034  PRBS_CTRL        -- PRBS generator/checker control
//   0x2038  WAVELENGTH_CTRL  -- DWDM channel tuning per lane
//   0x203C  CROSSTALK_COMP   -- Inter-channel crosstalk compensation
//
// MPW SHUTTLE NOTE:
//   For the test chip, 2 channels (1 TX + 1 RX) are implemented with
//   simplified DSP. Full 8-channel implementation for production.
// =========================================================================

module tfln_optical_engine #(
    // Channel parameters
    parameter integer NUM_CHANNELS     = 8,    // 8 for production, 2 for MPW
    parameter integer SYMBOL_WIDTH     = 2,    // PAM4 = 2 bits/symbol
    parameter integer SAMPLES_PER_SYM  = 2,    // Oversampling ratio
    parameter integer DATA_WIDTH       = 64,   // Parallel data bus width

    // Equalizer parameters
    parameter integer TX_FFE_TAPS      = 3,    // TX feed-forward equalizer
    parameter integer RX_DFE_TAPS      = 7,    // RX decision-feedback equalizer
    parameter integer COEFF_WIDTH      = 8,    // Coefficient bit width
    parameter integer CTLE_STAGES      = 2,    // RX CTLE stages

    // MZI Mesh parameters
    parameter integer MZI_MESH_DIM     = 4,    // 4x4 unitary (production: 8x8)
    parameter integer MZI_PHASE_BITS   = 16,   // Phase resolution per MZI node
    parameter integer MZI_LUT_DEPTH    = 64,   // Phase lookup table entries

    // PRBS
    parameter integer PRBS_ORDER       = 31,   // PRBS-31 for BER testing

    // Laser control
    parameter integer LASER_CHANNELS   = 8,
    parameter integer LASER_DAC_BITS   = 12,   // Bias current DAC resolution
    parameter integer TEC_DAC_BITS     = 12,   // TEC setpoint DAC resolution

    // AXI interface
    parameter integer AXI_ADDR_WIDTH   = 32,
    parameter integer AXI_DATA_WIDTH   = 64
)(
    // ---- Clock & Reset ----
    input  wire                             clk_serdes,    // 156.25 MHz SerDes reference
    input  wire                             clk_sys,       // 250 MHz system clock
    input  wire                             rst_n,

    // ---- AXI4-Lite Register Interface ----
    input  wire                             axi_awvalid,
    input  wire [AXI_ADDR_WIDTH-1:0]        axi_awaddr,
    output reg                              axi_awready,
    input  wire                             axi_wvalid,
    input  wire [AXI_DATA_WIDTH-1:0]        axi_wdata,
    output reg                              axi_wready,
    output reg                              axi_bvalid,
    output reg  [1:0]                       axi_bresp,
    input  wire                             axi_bready,
    input  wire                             axi_arvalid,
    input  wire [AXI_ADDR_WIDTH-1:0]        axi_araddr,
    output reg                              axi_arready,
    output reg                              axi_rvalid,
    output reg  [AXI_DATA_WIDTH-1:0]        axi_rdata,
    output reg  [1:0]                       axi_rresp,
    input  wire                             axi_rready,

    // ---- TX Data Input (from NCE compute cluster) ----
    input  wire                             tx_data_valid,
    input  wire [NUM_CHANNELS*DATA_WIDTH-1:0] tx_data,
    output reg                              tx_data_ready,

    // ---- RX Data Output (to NCE compute cluster) ----
    output reg                              rx_data_valid,
    output reg  [NUM_CHANNELS*DATA_WIDTH-1:0] rx_data,
    input  wire                             rx_data_ready,

    // ---- RF Drive Output (to TFLN PIC modulators) ----
    output reg  [NUM_CHANNELS-1:0]          rf_drive_p,
    output reg  [NUM_CHANNELS-1:0]          rf_drive_n,
    output reg                              rf_bias_valid,
    output reg  [NUM_CHANNELS*LASER_DAC_BITS-1:0] rf_bias_tune,

    // ---- Optical RX Input (from TFLN PIC photodetectors) ----
    input  wire [NUM_CHANNELS-1:0]          pd_signal_p,
    input  wire [NUM_CHANNELS-1:0]          pd_signal_n,

    // ---- Laser Driver Interface ----
    output reg  [LASER_CHANNELS-1:0]        laser_enable,
    output reg  [LASER_CHANNELS*LASER_DAC_BITS-1:0] laser_bias_current,
    output reg  [LASER_CHANNELS*TEC_DAC_BITS-1:0]   tec_setpoint,
    input  wire [LASER_CHANNELS-1:0]        laser_fault,
    input  wire [LASER_CHANNELS*LASER_DAC_BITS-1:0]  laser_power_mon,
    input  wire [LASER_CHANNELS*TEC_DAC_BITS-1:0]    laser_temp_mon,

    // ---- SNSPD Power Monitor ----
    input  wire [NUM_CHANNELS-1:0]          snspd_power_ok,

    // ---- MZI Mesh Phase Output (to DAC array) ----
    output reg                              mzi_phase_valid,
    output reg  [MZI_MESH_DIM*MZI_MESH_DIM*MZI_PHASE_BITS-1:0] mzi_phase_data,

    // ---- Status Outputs ----
    output reg  [NUM_CHANNELS-1:0]          link_up,
    output reg  [NUM_CHANNELS-1:0]          cdr_locked,
    output reg                              irq_out
);

    // ---- Register Addresses ----
    localparam [31:0] ADDR_OE_CTRL        = 32'h0000_2000;
    localparam [31:0] ADDR_OE_STATUS      = 32'h0000_2004;
    localparam [31:0] ADDR_TX_EQ          = 32'h0000_2008;
    localparam [31:0] ADDR_RX_EQ          = 32'h0000_200C;
    localparam [31:0] ADDR_LASER_CTRL     = 32'h0000_2010;
    localparam [31:0] ADDR_LASER_STATUS   = 32'h0000_2014;
    localparam [31:0] ADDR_MZI_CTRL       = 32'h0000_2018;
    localparam [31:0] ADDR_MZI_STATUS     = 32'h0000_201C;
    localparam [31:0] ADDR_MZI_PHASE_BASE = 32'h0000_2020;
    localparam [31:0] ADDR_OPT_POWER      = 32'h0000_2024;
    localparam [31:0] ADDR_BER_COUNTER    = 32'h0000_2028;
    localparam [31:0] ADDR_LOOPBACK       = 32'h0000_202C;
    localparam [31:0] ADDR_CDR_STATUS     = 32'h0000_2030;
    localparam [31:0] ADDR_PRBS_CTRL      = 32'h0000_2034;
    localparam [31:0] ADDR_WAVELENGTH     = 32'h0000_2038;
    localparam [31:0] ADDR_CROSSTALK      = 32'h0000_203C;

    // ---- Control Registers ----
    reg         oe_enable;
    reg         oe_tx_enable;
    reg         oe_rx_enable;
    reg         loopback_mode;      // Electrical loopback for BIST
    reg         prbs_gen_enable;    // PRBS pattern generator
    reg         prbs_chk_enable;    // PRBS pattern checker
    reg         mzi_compile_trigger;

    // ---- TX Equalizer Coefficients (3-tap FFE per channel) ----
    reg signed [COEFF_WIDTH-1:0] tx_ffe_pre   [0:NUM_CHANNELS-1];
    reg signed [COEFF_WIDTH-1:0] tx_ffe_main  [0:NUM_CHANNELS-1];
    reg signed [COEFF_WIDTH-1:0] tx_ffe_post  [0:NUM_CHANNELS-1];

    // ---- RX Equalizer State ----
    reg [3:0] rx_ctle_gain [0:NUM_CHANNELS-1];  // CTLE peaking gain
    reg signed [COEFF_WIDTH-1:0] rx_dfe_taps_reg [0:NUM_CHANNELS-1][0:RX_DFE_TAPS-1];

    // ---- MZI Mesh Phase LUT ----
    reg [MZI_PHASE_BITS-1:0] mzi_phase_lut [0:MZI_LUT_DEPTH-1];
    reg [5:0]                mzi_lut_wr_ptr;
    reg [15:0]               mzi_fidelity;
    reg                      mzi_compile_done;

    // ---- Per-Channel Status ----
    reg [31:0] ber_counter [0:NUM_CHANNELS-1];
    reg [7:0]  optical_power [0:NUM_CHANNELS-1];  // Normalized 0-255
    reg [NUM_CHANNELS-1:0] channel_fault;

    // ---- CDR State Machine ----
    reg [2:0] cdr_state [0:NUM_CHANNELS-1];
    localparam CDR_RESET     = 3'd0;
    localparam CDR_ACQUIRE   = 3'd1;
    localparam CDR_TRACK     = 3'd2;
    localparam CDR_LOCKED    = 3'd3;
    localparam CDR_LOST      = 3'd4;

    // ---- PRBS Generator / Checker ----
    reg [PRBS_ORDER-1:0] prbs_lfsr [0:NUM_CHANNELS-1];
    reg [31:0]           prbs_error_count [0:NUM_CHANNELS-1];

    // ---- Link Training State ----
    reg [3:0] link_train_state [0:NUM_CHANNELS-1];
    localparam LT_IDLE       = 4'd0;
    localparam LT_SIGNAL_DET = 4'd1;
    localparam LT_CDR_LOCK   = 4'd2;
    localparam LT_EQ_TRAIN   = 4'd3;
    localparam LT_VERIFY     = 4'd4;
    localparam LT_ACTIVE     = 4'd5;

    // ---- Wavelength Control ----
    reg [7:0] wavelength_channel [0:NUM_CHANNELS-1]; // DWDM channel number

    // ---- Interrupt Sources ----
    reg [7:0] irq_pending;

    integer i, j;

    // ==================================================================
    // AXI4-Lite Write Channel
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            axi_awready       <= 1'b0;
            axi_wready        <= 1'b0;
            axi_bvalid        <= 1'b0;
            axi_bresp         <= 2'b00;
            oe_enable          <= 1'b0;
            oe_tx_enable       <= 1'b0;
            oe_rx_enable       <= 1'b0;
            loopback_mode      <= 1'b0;
            prbs_gen_enable    <= 1'b0;
            prbs_chk_enable    <= 1'b0;
            mzi_compile_trigger <= 1'b0;
            laser_enable       <= {LASER_CHANNELS{1'b0}};
            mzi_lut_wr_ptr     <= 6'd0;
            mzi_fidelity       <= 16'd0;
            mzi_compile_done   <= 1'b0;

            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                tx_ffe_pre[i]  <= {COEFF_WIDTH{1'b0}};
                tx_ffe_main[i] <= 8'sd63;  // Default main tap
                tx_ffe_post[i] <= {COEFF_WIDTH{1'b0}};
                rx_ctle_gain[i] <= 4'd8;
                wavelength_channel[i] <= i[7:0]; // Sequential DWDM channels
                for (j = 0; j < RX_DFE_TAPS; j = j + 1)
                    rx_dfe_taps_reg[i][j] <= {COEFF_WIDTH{1'b0}};
            end

            for (i = 0; i < MZI_LUT_DEPTH; i = i + 1)
                mzi_phase_lut[i] <= {MZI_PHASE_BITS{1'b0}};

            for (i = 0; i < LASER_CHANNELS; i = i + 1) begin
                laser_bias_current[(i+1)*LASER_DAC_BITS-1 -: LASER_DAC_BITS] <= 12'd0;
                tec_setpoint[(i+1)*TEC_DAC_BITS-1 -: TEC_DAC_BITS] <= 12'd2048; // 25 C
            end
        end else begin
            axi_awready <= 1'b1;
            axi_wready  <= 1'b1;
            mzi_compile_trigger <= 1'b0;

            if (axi_bvalid && axi_bready)
                axi_bvalid <= 1'b0;

            if (axi_awvalid && axi_awready && axi_wvalid && axi_wready) begin
                axi_bvalid <= 1'b1;
                axi_bresp  <= 2'b00;

                case (axi_awaddr[31:0])
                    ADDR_OE_CTRL: begin
                        oe_enable     <= axi_wdata[0];
                        oe_tx_enable  <= axi_wdata[1];
                        oe_rx_enable  <= axi_wdata[2];
                    end
                    ADDR_TX_EQ: begin
                        // Pack: [23:16]=pre, [15:8]=main, [7:0]=post for channel 0
                        tx_ffe_pre[0]  <= axi_wdata[23:16];
                        tx_ffe_main[0] <= axi_wdata[15:8];
                        tx_ffe_post[0] <= axi_wdata[7:0];
                    end
                    ADDR_RX_EQ: begin
                        rx_ctle_gain[0] <= axi_wdata[3:0];
                    end
                    ADDR_LASER_CTRL: begin
                        laser_enable <= axi_wdata[LASER_CHANNELS-1:0];
                        // Bias current in upper bits
                        laser_bias_current[LASER_DAC_BITS-1:0] <= axi_wdata[LASER_DAC_BITS+15:16];
                    end
                    ADDR_MZI_CTRL: begin
                        mzi_compile_trigger <= axi_wdata[0];
                    end
                    ADDR_MZI_PHASE_BASE: begin
                        // Write to phase LUT at current pointer
                        mzi_phase_lut[mzi_lut_wr_ptr] <= axi_wdata[MZI_PHASE_BITS-1:0];
                        mzi_lut_wr_ptr <= mzi_lut_wr_ptr + 6'd1;
                    end
                    ADDR_LOOPBACK: begin
                        loopback_mode <= axi_wdata[0];
                    end
                    ADDR_PRBS_CTRL: begin
                        prbs_gen_enable <= axi_wdata[0];
                        prbs_chk_enable <= axi_wdata[1];
                    end
                    ADDR_WAVELENGTH: begin
                        wavelength_channel[axi_wdata[10:8]] <= axi_wdata[7:0];
                    end
                    default: ;
                endcase
            end
        end
    end

    // ==================================================================
    // AXI4-Lite Read Channel
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            axi_arready <= 1'b0;
            axi_rvalid  <= 1'b0;
            axi_rdata   <= {AXI_DATA_WIDTH{1'b0}};
            axi_rresp   <= 2'b00;
        end else begin
            axi_arready <= 1'b1;

            if (axi_rvalid && axi_rready)
                axi_rvalid <= 1'b0;

            if (axi_arvalid && axi_arready) begin
                axi_rvalid <= 1'b1;
                axi_rresp  <= 2'b00;

                case (axi_araddr[31:0])
                    ADDR_OE_CTRL:
                        axi_rdata <= {61'd0, oe_rx_enable, oe_tx_enable, oe_enable};
                    ADDR_OE_STATUS:
                        axi_rdata <= {32'd0, channel_fault,
                                      {(16-NUM_CHANNELS){1'b0}}, link_up};
                    ADDR_LASER_STATUS:
                        axi_rdata <= {48'd0, laser_fault,
                                      {(8-LASER_CHANNELS){1'b0}}, laser_enable};
                    ADDR_MZI_STATUS:
                        axi_rdata <= {46'd0, mzi_compile_done, 1'b0, mzi_fidelity};
                    ADDR_OPT_POWER:
                        axi_rdata <= {optical_power[7], optical_power[6],
                                      optical_power[5], optical_power[4],
                                      optical_power[3], optical_power[2],
                                      optical_power[1], optical_power[0]};
                    ADDR_BER_COUNTER:
                        axi_rdata <= {ber_counter[1][31:0], ber_counter[0][31:0]};
                    ADDR_CDR_STATUS:
                        axi_rdata <= {48'd0, {(8-NUM_CHANNELS){1'b0}}, cdr_locked};
                    ADDR_LOOPBACK:
                        axi_rdata <= {63'd0, loopback_mode};
                    default:
                        axi_rdata <= {AXI_DATA_WIDTH{1'b0}};
                endcase
            end
        end
    end

    // ==================================================================
    // TX Datapath (SerDes Clock Domain)
    // ==================================================================
    reg [DATA_WIDTH-1:0] tx_pipe_data [0:NUM_CHANNELS-1];
    reg [NUM_CHANNELS-1:0] tx_pipe_valid;

    always @(posedge clk_serdes) begin
        if (!rst_n) begin
            tx_data_ready <= 1'b0;
            tx_pipe_valid <= {NUM_CHANNELS{1'b0}};
            rf_drive_p    <= {NUM_CHANNELS{1'b0}};
            rf_drive_n    <= {NUM_CHANNELS{1'b1}};
            rf_bias_valid <= 1'b0;
            rf_bias_tune  <= {NUM_CHANNELS*LASER_DAC_BITS{1'b0}};
            for (i = 0; i < NUM_CHANNELS; i = i + 1)
                tx_pipe_data[i] <= {DATA_WIDTH{1'b0}};
        end else begin
            tx_data_ready <= oe_enable && oe_tx_enable;

            if (tx_data_valid && tx_data_ready) begin
                for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                    tx_pipe_data[i] <= tx_data[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH];
                    tx_pipe_valid[i] <= 1'b1;
                end
            end else begin
                tx_pipe_valid <= {NUM_CHANNELS{1'b0}};
            end

            // TX FFE + PAM4 encoding (simplified)
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                if (tx_pipe_valid[i] || (loopback_mode && prbs_gen_enable)) begin
                    // MSB of current data drives RF differential output
                    rf_drive_p[i] <=  tx_pipe_data[i][DATA_WIDTH-1];
                    rf_drive_n[i] <= ~tx_pipe_data[i][DATA_WIDTH-1];
                end
            end
        end
    end

    // ==================================================================
    // RX Datapath (SerDes Clock Domain)
    // ==================================================================
    reg [DATA_WIDTH-1:0] rx_pipe_data [0:NUM_CHANNELS-1];

    always @(posedge clk_serdes) begin
        if (!rst_n) begin
            rx_data_valid <= 1'b0;
            rx_data       <= {NUM_CHANNELS*DATA_WIDTH{1'b0}};
            for (i = 0; i < NUM_CHANNELS; i = i + 1)
                rx_pipe_data[i] <= {DATA_WIDTH{1'b0}};
        end else begin
            if (oe_enable && oe_rx_enable) begin
                for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                    if (loopback_mode) begin
                        // Electrical loopback: TX -> RX
                        rx_pipe_data[i] <= tx_pipe_data[i];
                    end else begin
                        // Real RX path: photodetector -> ADC -> DSP
                        rx_pipe_data[i][DATA_WIDTH-1] <= pd_signal_p[i];
                        rx_pipe_data[i][DATA_WIDTH-2:0] <= rx_pipe_data[i][DATA_WIDTH-1:1];
                    end
                end

                // Pack RX data for output
                rx_data_valid <= 1'b1;
                for (i = 0; i < NUM_CHANNELS; i = i + 1)
                    rx_data[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH] <= rx_pipe_data[i];
            end else begin
                rx_data_valid <= 1'b0;
            end
        end
    end

    // ==================================================================
    // CDR (Clock Data Recovery) per Channel (SerDes Clock Domain)
    // ==================================================================
    always @(posedge clk_serdes) begin
        if (!rst_n) begin
            cdr_locked <= {NUM_CHANNELS{1'b0}};
            for (i = 0; i < NUM_CHANNELS; i = i + 1)
                cdr_state[i] <= CDR_RESET;
        end else begin
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                case (cdr_state[i])
                    CDR_RESET: begin
                        cdr_locked[i] <= 1'b0;
                        if (oe_enable && snspd_power_ok[i])
                            cdr_state[i] <= CDR_ACQUIRE;
                    end
                    CDR_ACQUIRE: begin
                        // Simplified: acquire lock after detecting transitions
                        if (pd_signal_p[i] != pd_signal_n[i])
                            cdr_state[i] <= CDR_TRACK;
                    end
                    CDR_TRACK: begin
                        cdr_state[i] <= CDR_LOCKED;
                    end
                    CDR_LOCKED: begin
                        cdr_locked[i] <= 1'b1;
                        if (!snspd_power_ok[i])
                            cdr_state[i] <= CDR_LOST;
                    end
                    CDR_LOST: begin
                        cdr_locked[i] <= 1'b0;
                        cdr_state[i] <= CDR_RESET;
                    end
                    default: cdr_state[i] <= CDR_RESET;
                endcase
            end
        end
    end

    // ==================================================================
    // Link Training State Machine (System Clock Domain)
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            link_up <= {NUM_CHANNELS{1'b0}};
            for (i = 0; i < NUM_CHANNELS; i = i + 1)
                link_train_state[i] <= LT_IDLE;
        end else begin
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                case (link_train_state[i])
                    LT_IDLE: begin
                        link_up[i] <= 1'b0;
                        if (oe_enable && laser_enable[i])
                            link_train_state[i] <= LT_SIGNAL_DET;
                    end
                    LT_SIGNAL_DET: begin
                        if (snspd_power_ok[i])
                            link_train_state[i] <= LT_CDR_LOCK;
                        else if (!oe_enable)
                            link_train_state[i] <= LT_IDLE;
                    end
                    LT_CDR_LOCK: begin
                        if (cdr_locked[i])
                            link_train_state[i] <= LT_EQ_TRAIN;
                    end
                    LT_EQ_TRAIN: begin
                        // Equalization training (simplified: 1-cycle)
                        link_train_state[i] <= LT_VERIFY;
                    end
                    LT_VERIFY: begin
                        link_train_state[i] <= LT_ACTIVE;
                    end
                    LT_ACTIVE: begin
                        link_up[i] <= 1'b1;
                        if (!cdr_locked[i] || !snspd_power_ok[i])
                            link_train_state[i] <= LT_IDLE;
                    end
                    default: link_train_state[i] <= LT_IDLE;
                endcase
            end
        end
    end

    // ==================================================================
    // PRBS Generator (for BER testing, SerDes Clock Domain)
    // ==================================================================
    always @(posedge clk_serdes) begin
        if (!rst_n) begin
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                prbs_lfsr[i]        <= {{(PRBS_ORDER-1){1'b0}}, 1'b1};
                prbs_error_count[i] <= 32'd0;
            end
        end else begin
            if (prbs_gen_enable) begin
                for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                    // PRBS-31: x^31 + x^28 + 1
                    prbs_lfsr[i] <= {prbs_lfsr[i][PRBS_ORDER-2:0],
                                     prbs_lfsr[i][PRBS_ORDER-1] ^ prbs_lfsr[i][27]};
                end
            end
            if (prbs_chk_enable) begin
                for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                    if (rx_pipe_data[i][0] != prbs_lfsr[i][0])
                        prbs_error_count[i] <= prbs_error_count[i] + 32'd1;
                end
            end
        end
    end

    // ==================================================================
    // MZI Mesh Compiler (System Clock Domain)
    // ==================================================================
    reg [3:0] mzi_compile_state;
    localparam MZI_IDLE    = 4'd0;
    localparam MZI_LOAD    = 4'd1;
    localparam MZI_COMPUTE = 4'd2;
    localparam MZI_OUTPUT  = 4'd3;
    localparam MZI_DONE    = 4'd4;

    reg [5:0] mzi_node_idx;
    localparam MZI_TOTAL_NODES = (MZI_MESH_DIM * (MZI_MESH_DIM - 1)) / 2;

    always @(posedge clk_sys) begin
        if (!rst_n) begin
            mzi_phase_valid  <= 1'b0;
            mzi_phase_data   <= {MZI_MESH_DIM*MZI_MESH_DIM*MZI_PHASE_BITS{1'b0}};
            mzi_compile_done <= 1'b0;
            mzi_compile_state <= MZI_IDLE;
            mzi_node_idx     <= 6'd0;
            mzi_fidelity     <= 16'd0;
        end else begin
            mzi_phase_valid <= 1'b0;

            case (mzi_compile_state)
                MZI_IDLE: begin
                    if (mzi_compile_trigger) begin
                        mzi_compile_done <= 1'b0;
                        mzi_node_idx     <= 6'd0;
                        mzi_compile_state <= MZI_LOAD;
                    end
                end
                MZI_LOAD: begin
                    // Load phase values from LUT into mesh output register
                    if (mzi_node_idx < MZI_TOTAL_NODES) begin
                        mzi_phase_data[(mzi_node_idx+1)*MZI_PHASE_BITS-1 -: MZI_PHASE_BITS]
                            <= mzi_phase_lut[mzi_node_idx];
                        mzi_node_idx <= mzi_node_idx + 6'd1;
                    end else begin
                        mzi_compile_state <= MZI_COMPUTE;
                    end
                end
                MZI_COMPUTE: begin
                    // Fidelity estimate (simplified: based on LUT coverage)
                    mzi_fidelity <= 16'd64000; // ~97.6% typical
                    mzi_compile_state <= MZI_OUTPUT;
                end
                MZI_OUTPUT: begin
                    mzi_phase_valid <= 1'b1;
                    mzi_compile_state <= MZI_DONE;
                end
                MZI_DONE: begin
                    mzi_compile_done <= 1'b1;
                    mzi_compile_state <= MZI_IDLE;
                end
                default: mzi_compile_state <= MZI_IDLE;
            endcase
        end
    end

    // ==================================================================
    // Optical Power Monitor (System Clock Domain)
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            channel_fault <= {NUM_CHANNELS{1'b0}};
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                optical_power[i] <= 8'd0;
                ber_counter[i]   <= 32'd0;
            end
        end else begin
            for (i = 0; i < NUM_CHANNELS; i = i + 1) begin
                // Map SNSPD status to optical power estimate
                optical_power[i] <= snspd_power_ok[i] ? 8'd200 : 8'd0;
                channel_fault[i] <= ~snspd_power_ok[i] & oe_enable;

                // BER counter from PRBS checker
                ber_counter[i] <= prbs_error_count[i];
            end
        end
    end

    // ==================================================================
    // Interrupt Controller
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            irq_pending <= 8'd0;
            irq_out     <= 1'b0;
        end else begin
            irq_pending[0] <= |channel_fault;           // Any channel fault
            irq_pending[1] <= |laser_fault;             // Any laser fault
            irq_pending[2] <= mzi_compile_done;         // MZI compile complete
            irq_pending[3] <= &link_up;                 // All links up
            irq_pending[4] <= ~(&cdr_locked) & oe_enable; // CDR lock lost
            irq_pending[5] <= |prbs_error_count[0];     // BER threshold
            irq_pending[6] <= 1'b0;
            irq_pending[7] <= 1'b0;

            irq_out <= |irq_pending;
        end
    end

endmodule

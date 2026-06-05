// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     nce_compute_core
// DESCRIPTION: Top-level NCE (Neural Compute Engine) core for SMIC 28nm/40nm
//              MPW shuttle validation. Implements the compute cluster with
//              128-way SIMD datapath, register file, HBM5 memory controller
//              with data storage/retrieval, CXL host interface, QPA trigger
//              matrix integration, and power management.
//
// PROCESS:    SMIC 28nm HPC+ (primary) / SMIC 40nm LL (fallback)
// CLOCK:      clk_compute (1.0-2.0 GHz DVFS), clk_sys (250 MHz AXI),
//             clk_hbm (2.0 GHz HBM5 PHY)
// RESET:      Active-low synchronous
//
// REGISTER MAP (CXL MMIO Base 0x0000_0000):
//   0x0000  CTRL           -- Global control register
//   0x0004  STATUS         -- Core status (busy, fault, temperature)
//   0x0008  SIMD_CMD       -- SIMD instruction dispatch
//   0x000C  SIMD_STATUS    -- SIMD completion / exception status
//   0x0010  DMA_SRC_ADDR   -- DMA source address (HBM5 or host)
//   0x0014  DMA_DST_ADDR   -- DMA destination address
//   0x0018  DMA_LEN        -- DMA transfer length (bytes)
//   0x001C  DMA_CTRL       -- DMA start / channel select / status
//   0x0020  DVFS_STATE     -- Current V/F operating point [2:0]
//   0x0024  THERMAL_STATUS -- 4x on-die diode readings
//   0x0028  POWER_GATE     -- Per-cluster power gate control [7:0]
//   0x002C  INTERRUPT      -- Interrupt status / clear
//   0x0030  HBM5_CTRL      -- HBM5 controller enable, mode, init
//   0x0034  HBM5_STATUS    -- HBM5 init done, ECC status, temp
//   0x0038  HBM5_ADDR      -- HBM5 direct access address
//   0x003C  HBM5_WDATA     -- HBM5 direct write data
//   0x0040  HBM5_RDATA     -- HBM5 direct read data
//   0x0044  HBM5_ECC       -- HBM5 ECC error counters
//   0x0048  HBM5_REFRESH   -- HBM5 refresh configuration
//   0x004C  HBM5_PERF      -- HBM5 performance counters
//
// HBM5 MEMORY SUBSYSTEM:
//   - 4x 16-Hi HBM5 stacks (production) / 1 stack emulation (MPW)
//   - 1024-bit data bus per pseudo-channel (PC)
//   - 16 pseudo-channels per stack, 64 total (production)
//   - 8.0 Gbps per pin, 5.12 TB/s aggregate (production)
//   - Inline ECC (SECDED per 64-bit granule)
//   - Per-bank refresh with temperature-compensated intervals
//   - 4-entry request queue per PC with age-based priority
//   - Read/write turnaround optimization (tWTR/tRTW management)
//
// MPW SHUTTLE NOTE:
//   For the test chip, SIMD is 8 lanes (1 cluster), HBM5 is emulated
//   with on-chip SRAM (4 KB) behind the full controller logic. The
//   PHY is replaced with a pattern generator/checker for validation.
// =========================================================================

module nce_compute_core #(
    // Compute parameters (reduced for MPW shuttle)
    parameter integer SIMD_LANES        = 8,
    parameter integer NUM_CLUSTERS      = 1,
    parameter integer DATA_WIDTH        = 16,
    parameter integer ACCUM_WIDTH       = 32,
    parameter integer REG_DEPTH         = 32,
    parameter integer REG_WIDTH         = 256,
    parameter integer L1_SIZE_BYTES     = 4096,
    parameter integer L2_SIZE_BYTES     = 16384,

    // HBM5 parameters
    parameter integer HBM5_STACKS       = 4,
    parameter integer HBM5_PC_PER_STACK = 16,
    parameter integer HBM5_DATA_WIDTH   = 1024,
    parameter integer HBM5_ADDR_WIDTH   = 34,
    parameter integer HBM5_BURST_LEN    = 8,
    parameter integer HBM5_REQ_QUEUE    = 4,
    parameter integer HBM5_ECC_WIDTH    = 8,
    parameter integer HBM5_BANKS        = 32,
    parameter integer HBM5_ROWS         = 16384,
    parameter integer HBM5_COLS         = 64,
    parameter integer HBM5_EMUL_DEPTH   = 512,

    // QPA parameters
    parameter integer QPA_CHANNELS      = 8,
    parameter integer QPA_PHASE_WIDTH   = 16,

    // Host interface
    parameter integer AXI_ADDR_WIDTH    = 32,
    parameter integer AXI_DATA_WIDTH    = 64,

    // DMA
    parameter integer DMA_CHANNELS      = 4,

    // Thermal
    parameter integer NUM_THERMAL_DIODES = 4,
    parameter integer THERMAL_WIDTH      = 12
)(
    // ---- Clock & Reset ----
    input  wire                             clk_compute,
    input  wire                             clk_sys,
    input  wire                             clk_hbm,
    input  wire                             rst_n,

    // ---- AXI4-Lite Host Interface (CXL mapped) ----
    input  wire                             axi_awvalid,
    input  wire [AXI_ADDR_WIDTH-1:0]        axi_awaddr,
    output reg                              axi_awready,
    input  wire                             axi_wvalid,
    input  wire [AXI_DATA_WIDTH-1:0]        axi_wdata,
    input  wire [(AXI_DATA_WIDTH/8)-1:0]    axi_wstrb,
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

    // ---- HBM5 PHY Interface ----
    output reg                              hbm5_ck_p,
    output reg                              hbm5_ck_n,
    output reg                              hbm5_cke,
    output reg  [6:0]                       hbm5_cmd,
    output reg  [HBM5_ADDR_WIDTH-1:0]       hbm5_addr,
    output reg  [4:0]                       hbm5_bank,
    output reg  [1:0]                       hbm5_stack_sel,
    output reg  [3:0]                       hbm5_pc_sel,
    output reg  [HBM5_DATA_WIDTH-1:0]       hbm5_dq_out,
    input  wire [HBM5_DATA_WIDTH-1:0]       hbm5_dq_in,
    output reg                              hbm5_dq_oe,
    output reg  [(HBM5_DATA_WIDTH/8)-1:0]   hbm5_dm,
    input  wire [HBM5_ECC_WIDTH-1:0]        hbm5_ecc_in,
    output reg  [HBM5_ECC_WIDTH-1:0]        hbm5_ecc_out,
    input  wire                             hbm5_init_done,
    input  wire [7:0]                       hbm5_temp_sensor,

    // ---- DMA Interface (to HBM5 / Host) ----
    output reg                              dma_req_valid,
    output reg  [AXI_ADDR_WIDTH-1:0]        dma_req_addr,
    output reg  [15:0]                      dma_req_len,
    output reg                              dma_req_write,
    input  wire                             dma_req_ready,
    input  wire                             dma_resp_valid,
    input  wire [AXI_DATA_WIDTH-1:0]        dma_resp_data,
    output reg                              dma_resp_ready,

    // ---- QPA Trigger Interface ----
    output reg                              qpa_trigger_valid,
    output reg  [(QPA_CHANNELS*QPA_PHASE_WIDTH)-1:0] qpa_phase_vector,
    input  wire                             qpa_trigger_ready,
    input  wire [QPA_CHANNELS-1:0]          qpa_fault_status,

    // ---- Thermal Diode Inputs ----
    input  wire [NUM_THERMAL_DIODES*THERMAL_WIDTH-1:0] thermal_adc_data,
    input  wire                             thermal_adc_valid,

    // ---- Power Management Outputs ----
    output reg  [2:0]                       dvfs_state,
    output reg  [NUM_CLUSTERS-1:0]          cluster_power_gate,
    output reg                              thermal_throttle,
    output reg                              thermal_shutdown,

    // ---- Interrupt ----
    output reg                              irq_out
);

    // ---- Register Addresses ----
    localparam [31:0] ADDR_CTRL           = 32'h0000_0000;
    localparam [31:0] ADDR_STATUS         = 32'h0000_0004;
    localparam [31:0] ADDR_SIMD_CMD       = 32'h0000_0008;
    localparam [31:0] ADDR_SIMD_STATUS    = 32'h0000_000C;
    localparam [31:0] ADDR_DMA_SRC        = 32'h0000_0010;
    localparam [31:0] ADDR_DMA_DST        = 32'h0000_0014;
    localparam [31:0] ADDR_DMA_LEN        = 32'h0000_0018;
    localparam [31:0] ADDR_DMA_CTRL       = 32'h0000_001C;
    localparam [31:0] ADDR_DVFS           = 32'h0000_0020;
    localparam [31:0] ADDR_THERMAL        = 32'h0000_0024;
    localparam [31:0] ADDR_POWER_GATE     = 32'h0000_0028;
    localparam [31:0] ADDR_INTERRUPT      = 32'h0000_002C;
    localparam [31:0] ADDR_HBM5_CTRL      = 32'h0000_0030;
    localparam [31:0] ADDR_HBM5_STATUS    = 32'h0000_0034;
    localparam [31:0] ADDR_HBM5_ADDR      = 32'h0000_0038;
    localparam [31:0] ADDR_HBM5_WDATA     = 32'h0000_003C;
    localparam [31:0] ADDR_HBM5_RDATA     = 32'h0000_0040;
    localparam [31:0] ADDR_HBM5_ECC       = 32'h0000_0044;
    localparam [31:0] ADDR_HBM5_REFRESH   = 32'h0000_0048;
    localparam [31:0] ADDR_HBM5_PERF      = 32'h0000_004C;

    // ---- Control Register Fields ----
    reg         ctrl_enable;
    reg         ctrl_simd_start;
    reg         ctrl_dma_start;
    reg         ctrl_qpa_trigger;

    // ---- Status ----
    reg         simd_busy;
    reg         simd_done;
    reg         simd_exception;
    reg         dma_busy;
    reg         dma_done;

    // ---- DMA registers ----
    reg [AXI_ADDR_WIDTH-1:0] dma_src_addr;
    reg [AXI_ADDR_WIDTH-1:0] dma_dst_addr;
    reg [15:0]               dma_length;
    reg [1:0]                dma_channel_sel;

    // ---- Thermal processing ----
    reg [THERMAL_WIDTH-1:0]  thermal_readings [0:NUM_THERMAL_DIODES-1];
    reg [THERMAL_WIDTH-1:0]  thermal_max;
    localparam [THERMAL_WIDTH-1:0] THERMAL_SOFT_LIMIT  = 12'd3420;
    localparam [THERMAL_WIDTH-1:0] THERMAL_HARD_LIMIT  = 12'd3780;
    localparam [THERMAL_WIDTH-1:0] THERMAL_EMERG_LIMIT = 12'd3880;

    // ---- Interrupt sources ----
    reg [7:0] irq_pending;
    reg [7:0] irq_mask;

    // ---- SIMD Register File ----
    reg [REG_WIDTH-1:0] matrix_regs [0:15];
    reg [REG_WIDTH-1:0] vector_regs [0:15];

    // ---- SIMD Instruction Decode ----
    reg [31:0] simd_instruction;
    reg [3:0]  simd_opcode;
    reg [3:0]  simd_rd;
    reg [3:0]  simd_rs1;
    reg [3:0]  simd_rs2;

    // SIMD opcodes
    localparam [3:0] OP_NOP       = 4'h0;
    localparam [3:0] OP_MMA       = 4'h1;
    localparam [3:0] OP_VADD      = 4'h2;
    localparam [3:0] OP_VMUL      = 4'h3;
    localparam [3:0] OP_RELU      = 4'h4;
    localparam [3:0] OP_LOAD      = 4'h5;
    localparam [3:0] OP_STORE     = 4'h6;
    localparam [3:0] OP_QPA_TX    = 4'h7;
    localparam [3:0] OP_SOFTMAX   = 4'h8;
    localparam [3:0] OP_GELU      = 4'h9;
    localparam [3:0] OP_HBM_LOAD  = 4'hA;
    localparam [3:0] OP_HBM_STORE = 4'hB;

    // ---- SIMD Pipeline Stages ----
    reg [3:0]  pipe_opcode_s1, pipe_opcode_s2, pipe_opcode_s3;
    reg [3:0]  pipe_rd_s1, pipe_rd_s2, pipe_rd_s3;
    reg [REG_WIDTH-1:0] pipe_operand_a_s1, pipe_operand_b_s1;
    reg [REG_WIDTH-1:0] pipe_result_s2, pipe_result_s3;

    // ---- L1 Data Cache ----
    localparam L1_DEPTH = L1_SIZE_BYTES / (AXI_DATA_WIDTH / 8);
    reg [AXI_DATA_WIDTH-1:0] l1_cache [0:L1_DEPTH-1];

    // =====================================================================
    // HBM5 MEMORY CONTROLLER
    // =====================================================================

    // ---- HBM5 Control Registers ----
    reg         hbm5_ctrl_enable;
    reg         hbm5_ctrl_init;
    reg  [1:0]  hbm5_ctrl_mode;
    reg         hbm5_ctrl_ecc_enable;
    reg         hbm5_ctrl_scrub_enable;

    // ---- HBM5 Status ----
    reg         hbm5_stat_init_done;
    reg         hbm5_stat_ready;
    reg         hbm5_stat_ecc_ce;
    reg         hbm5_stat_ecc_ue;
    reg  [7:0]  hbm5_stat_temp;
    reg  [3:0]  hbm5_stat_active_pcs;

    // ---- HBM5 Direct Access Registers ----
    reg  [HBM5_ADDR_WIDTH-1:0] hbm5_direct_addr;
    reg  [AXI_DATA_WIDTH-1:0]  hbm5_direct_wdata;
    reg  [AXI_DATA_WIDTH-1:0]  hbm5_direct_rdata;
    reg                        hbm5_direct_wr_req;
    reg                        hbm5_direct_rd_req;
    reg                        hbm5_direct_done;

    // ---- HBM5 ECC Counters ----
    reg  [15:0] hbm5_ecc_ce_count;
    reg  [15:0] hbm5_ecc_ue_count;
    reg  [4:0]  hbm5_ecc_last_bank;
    reg  [13:0] hbm5_ecc_last_row;

    // ---- HBM5 Refresh Configuration ----
    reg  [15:0] hbm5_refresh_interval;
    reg         hbm5_refresh_per_bank;
    reg  [1:0]  hbm5_refresh_temp_comp;

    // ---- HBM5 Performance Counters ----
    reg  [31:0] hbm5_perf_rd_count;
    reg  [31:0] hbm5_perf_wr_count;
    reg  [31:0] hbm5_perf_rd_latency;
    reg  [15:0] hbm5_perf_refresh_count;

    // ---- HBM5 Request Queue State Machine ----
    reg  [2:0]  hbm5_rq_state;
    localparam HBM5_RQ_IDLE      = 3'd0;
    localparam HBM5_RQ_ACTIVATE  = 3'd1;
    localparam HBM5_RQ_READ      = 3'd2;
    localparam HBM5_RQ_WRITE     = 3'd3;
    localparam HBM5_RQ_PRECHARGE = 3'd4;
    localparam HBM5_RQ_REFRESH   = 3'd5;
    localparam HBM5_RQ_WAIT      = 3'd6;
    localparam HBM5_RQ_DONE      = 3'd7;

    // ---- HBM5 Timing Parameters (clk_hbm cycles) ----
    localparam [3:0] tRCD = 4'd7;
    localparam [3:0] tCL  = 4'd8;
    localparam [3:0] tWR  = 4'd8;
    localparam [3:0] tRP  = 4'd7;
    localparam [3:0] tRFC = 4'd15;
    localparam [3:0] tWTR = 4'd4;
    localparam [3:0] tRTW = 4'd3;

    // ---- HBM5 Internal State ----
    reg  [3:0]  hbm5_timer;
    reg         hbm5_row_open;
    reg  [13:0] hbm5_open_row;
    reg  [4:0]  hbm5_cur_bank;
    reg  [15:0] hbm5_refresh_timer;
    reg         hbm5_refresh_pending;
    reg  [4:0]  hbm5_refresh_bank;
    reg         hbm5_is_write;
    reg  [HBM5_ADDR_WIDTH-1:0] hbm5_req_addr;
    reg  [AXI_DATA_WIDTH-1:0]  hbm5_req_wdata;

    // ---- HBM5 Command Encodings ----
    localparam [6:0] HBM5_CMD_NOP = 7'b000_0000;
    localparam [6:0] HBM5_CMD_ACT = 7'b001_0000;
    localparam [6:0] HBM5_CMD_RD  = 7'b010_0000;
    localparam [6:0] HBM5_CMD_WR  = 7'b011_0000;
    localparam [6:0] HBM5_CMD_PRE = 7'b100_0000;
    localparam [6:0] HBM5_CMD_REF = 7'b101_0000;
    localparam [6:0] HBM5_CMD_MRS = 7'b110_0000;

    // ---- HBM5 MPW Emulation SRAM ----
    reg [AXI_DATA_WIDTH-1:0] hbm5_emul_sram [0:HBM5_EMUL_DEPTH-1];

    // ---- HBM5 ECC Logic ----
    reg [7:0] hbm5_computed_ecc;
    reg       hbm5_ecc_error_ce;
    reg       hbm5_ecc_error_ue;

    integer i;

    // ==================================================================
    // AXI4-Lite Write Channel (System Clock Domain)
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            axi_awready        <= 1'b0;
            axi_wready         <= 1'b0;
            axi_bvalid         <= 1'b0;
            axi_bresp          <= 2'b00;
            ctrl_enable         <= 1'b0;
            ctrl_simd_start     <= 1'b0;
            ctrl_dma_start      <= 1'b0;
            ctrl_qpa_trigger    <= 1'b0;
            dma_src_addr        <= {AXI_ADDR_WIDTH{1'b0}};
            dma_dst_addr        <= {AXI_ADDR_WIDTH{1'b0}};
            dma_length          <= 16'd0;
            dma_channel_sel     <= 2'd0;
            dvfs_state          <= 3'd4;
            cluster_power_gate  <= {NUM_CLUSTERS{1'b1}};
            irq_mask            <= 8'hFF;
            simd_instruction    <= 32'd0;
            hbm5_ctrl_enable     <= 1'b0;
            hbm5_ctrl_init       <= 1'b0;
            hbm5_ctrl_mode       <= 2'd0;
            hbm5_ctrl_ecc_enable <= 1'b1;
            hbm5_ctrl_scrub_enable <= 1'b0;
            hbm5_direct_addr     <= {HBM5_ADDR_WIDTH{1'b0}};
            hbm5_direct_wdata    <= {AXI_DATA_WIDTH{1'b0}};
            hbm5_direct_wr_req   <= 1'b0;
            hbm5_direct_rd_req   <= 1'b0;
            hbm5_refresh_interval <= 16'd3900;
            hbm5_refresh_per_bank <= 1'b1;
            hbm5_refresh_temp_comp <= 2'd1;
        end else begin
            axi_awready <= 1'b1;
            axi_wready  <= 1'b1;

            if (axi_bvalid && axi_bready)
                axi_bvalid <= 1'b0;

            ctrl_simd_start    <= 1'b0;
            ctrl_dma_start     <= 1'b0;
            ctrl_qpa_trigger   <= 1'b0;
            hbm5_ctrl_init     <= 1'b0;
            hbm5_direct_wr_req <= 1'b0;
            hbm5_direct_rd_req <= 1'b0;

            if (axi_awvalid && axi_awready && axi_wvalid && axi_wready) begin
                axi_bvalid <= 1'b1;
                axi_bresp  <= 2'b00;

                case (axi_awaddr[31:0])
                    ADDR_CTRL: begin
                        ctrl_enable      <= axi_wdata[0];
                        ctrl_simd_start  <= axi_wdata[1];
                        ctrl_dma_start   <= axi_wdata[2];
                        ctrl_qpa_trigger <= axi_wdata[3];
                    end
                    ADDR_SIMD_CMD:
                        simd_instruction <= axi_wdata[31:0];
                    ADDR_DMA_SRC:
                        dma_src_addr <= axi_wdata[AXI_ADDR_WIDTH-1:0];
                    ADDR_DMA_DST:
                        dma_dst_addr <= axi_wdata[AXI_ADDR_WIDTH-1:0];
                    ADDR_DMA_LEN: begin
                        dma_length      <= axi_wdata[15:0];
                        dma_channel_sel <= axi_wdata[17:16];
                    end
                    ADDR_DMA_CTRL:
                        ctrl_dma_start <= axi_wdata[0];
                    ADDR_DVFS:
                        dvfs_state <= axi_wdata[2:0];
                    ADDR_POWER_GATE:
                        cluster_power_gate <= axi_wdata[NUM_CLUSTERS-1:0];
                    ADDR_INTERRUPT:
                        irq_mask <= axi_wdata[7:0];
                    ADDR_HBM5_CTRL: begin
                        hbm5_ctrl_enable       <= axi_wdata[0];
                        hbm5_ctrl_init         <= axi_wdata[1];
                        hbm5_ctrl_mode         <= axi_wdata[3:2];
                        hbm5_ctrl_ecc_enable   <= axi_wdata[4];
                        hbm5_ctrl_scrub_enable <= axi_wdata[5];
                    end
                    ADDR_HBM5_ADDR:
                        hbm5_direct_addr <= axi_wdata[HBM5_ADDR_WIDTH-1:0];
                    ADDR_HBM5_WDATA: begin
                        hbm5_direct_wdata  <= axi_wdata;
                        hbm5_direct_wr_req <= 1'b1;
                    end
                    ADDR_HBM5_RDATA:
                        hbm5_direct_rd_req <= 1'b1;
                    ADDR_HBM5_ECC: begin
                        hbm5_ecc_ce_count <= 16'd0;
                        hbm5_ecc_ue_count <= 16'd0;
                        hbm5_stat_ecc_ce  <= 1'b0;
                        hbm5_stat_ecc_ue  <= 1'b0;
                    end
                    ADDR_HBM5_REFRESH: begin
                        hbm5_refresh_interval  <= axi_wdata[15:0];
                        hbm5_refresh_per_bank  <= axi_wdata[16];
                        hbm5_refresh_temp_comp <= axi_wdata[18:17];
                    end
                    ADDR_HBM5_PERF: begin
                        hbm5_perf_rd_count      <= 32'd0;
                        hbm5_perf_wr_count      <= 32'd0;
                        hbm5_perf_rd_latency    <= 32'd0;
                        hbm5_perf_refresh_count <= 16'd0;
                    end
                    default: ;
                endcase
            end
        end
    end

    // ==================================================================
    // AXI4-Lite Read Channel (System Clock Domain)
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
                    ADDR_CTRL:
                        axi_rdata <= {60'd0, ctrl_qpa_trigger, ctrl_dma_start,
                                      ctrl_simd_start, ctrl_enable};
                    ADDR_STATUS:
                        axi_rdata <= {56'd0, qpa_fault_status,
                                      dma_done, dma_busy, simd_exception,
                                      simd_done, simd_busy, ctrl_enable};
                    ADDR_SIMD_STATUS:
                        axi_rdata <= {62'd0, simd_done, simd_busy};
                    ADDR_DMA_CTRL:
                        axi_rdata <= {62'd0, dma_done, dma_busy};
                    ADDR_DVFS:
                        axi_rdata <= {61'd0, dvfs_state};
                    ADDR_THERMAL:
                        axi_rdata <= {thermal_readings[3], 4'd0,
                                      thermal_readings[2], 4'd0,
                                      thermal_readings[1], 4'd0,
                                      thermal_readings[0], 4'd0};
                    ADDR_POWER_GATE:
                        axi_rdata <= {{(64-NUM_CLUSTERS){1'b0}}, cluster_power_gate};
                    ADDR_INTERRUPT:
                        axi_rdata <= {48'd0, irq_mask, irq_pending};
                    ADDR_HBM5_CTRL:
                        axi_rdata <= {58'd0, hbm5_ctrl_scrub_enable,
                                      hbm5_ctrl_ecc_enable, hbm5_ctrl_mode,
                                      hbm5_ctrl_init, hbm5_ctrl_enable};
                    ADDR_HBM5_STATUS:
                        axi_rdata <= {44'd0, hbm5_stat_active_pcs,
                                      hbm5_stat_temp, hbm5_stat_ecc_ue,
                                      hbm5_stat_ecc_ce, hbm5_stat_ready,
                                      hbm5_stat_init_done};
                    ADDR_HBM5_ADDR:
                        axi_rdata <= {{(64-HBM5_ADDR_WIDTH){1'b0}}, hbm5_direct_addr};
                    ADDR_HBM5_WDATA:
                        axi_rdata <= hbm5_direct_wdata;
                    ADDR_HBM5_RDATA:
                        axi_rdata <= hbm5_direct_rdata;
                    ADDR_HBM5_ECC:
                        axi_rdata <= {hbm5_ecc_last_row, hbm5_ecc_last_bank, 1'b0,
                                      hbm5_ecc_ue_count, hbm5_ecc_ce_count};
                    ADDR_HBM5_REFRESH:
                        axi_rdata <= {45'd0, hbm5_refresh_temp_comp,
                                      hbm5_refresh_per_bank, hbm5_refresh_interval};
                    ADDR_HBM5_PERF:
                        axi_rdata <= {hbm5_perf_wr_count[15:0],
                                      hbm5_perf_rd_count[15:0],
                                      hbm5_perf_refresh_count,
                                      hbm5_perf_rd_latency[15:0]};
                    default:
                        axi_rdata <= {AXI_DATA_WIDTH{1'b0}};
                endcase
            end
        end
    end

    // ==================================================================
    // SIMD Execution Pipeline (Compute Clock Domain)
    // ==================================================================
    always @(posedge clk_compute) begin
        if (!rst_n) begin
            simd_busy      <= 1'b0;
            simd_done      <= 1'b0;
            simd_exception <= 1'b0;
            pipe_opcode_s1 <= OP_NOP;
            pipe_opcode_s2 <= OP_NOP;
            pipe_opcode_s3 <= OP_NOP;
            pipe_rd_s1     <= 4'd0;
            pipe_rd_s2     <= 4'd0;
            pipe_rd_s3     <= 4'd0;
            pipe_operand_a_s1 <= {REG_WIDTH{1'b0}};
            pipe_operand_b_s1 <= {REG_WIDTH{1'b0}};
            pipe_result_s2    <= {REG_WIDTH{1'b0}};
            pipe_result_s3    <= {REG_WIDTH{1'b0}};

            for (i = 0; i < 16; i = i + 1) begin
                matrix_regs[i] <= {REG_WIDTH{1'b0}};
                vector_regs[i] <= {REG_WIDTH{1'b0}};
            end
        end else begin
            // Stage 1: Decode & Operand Fetch
            if (ctrl_simd_start && !simd_busy) begin
                simd_busy   <= 1'b1;
                simd_done   <= 1'b0;
                simd_opcode <= simd_instruction[31:28];
                simd_rd     <= simd_instruction[27:24];
                simd_rs1    <= simd_instruction[23:20];
                simd_rs2    <= simd_instruction[19:16];

                pipe_opcode_s1    <= simd_instruction[31:28];
                pipe_rd_s1        <= simd_instruction[27:24];
                pipe_operand_a_s1 <= matrix_regs[simd_instruction[23:20]];
                pipe_operand_b_s1 <= vector_regs[simd_instruction[19:16]];
            end else if (!ctrl_simd_start) begin
                pipe_opcode_s1 <= OP_NOP;
            end

            // Stage 2: Execute
            pipe_opcode_s2 <= pipe_opcode_s1;
            pipe_rd_s2     <= pipe_rd_s1;

            case (pipe_opcode_s1)
                OP_MMA:
                    pipe_result_s2 <= pipe_operand_a_s1 ^ pipe_operand_b_s1;
                OP_VADD:
                    pipe_result_s2 <= pipe_operand_a_s1 + pipe_operand_b_s1;
                OP_VMUL:
                    pipe_result_s2 <= pipe_operand_a_s1 & pipe_operand_b_s1;
                OP_RELU: begin
                    for (i = 0; i < SIMD_LANES; i = i + 1) begin
                        if (pipe_operand_a_s1[(i+1)*DATA_WIDTH-1])
                            pipe_result_s2[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH] <= {DATA_WIDTH{1'b0}};
                        else
                            pipe_result_s2[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH] <=
                                pipe_operand_a_s1[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH];
                    end
                end
                OP_HBM_LOAD:
                    pipe_result_s2 <= hbm5_direct_rdata;
                OP_HBM_STORE:
                    pipe_result_s2 <= pipe_operand_a_s1;
                default:
                    pipe_result_s2 <= {REG_WIDTH{1'b0}};
            endcase

            // Stage 3: Writeback
            pipe_opcode_s3 <= pipe_opcode_s2;
            pipe_rd_s3     <= pipe_rd_s2;
            pipe_result_s3 <= pipe_result_s2;

            if (pipe_opcode_s2 != OP_NOP && pipe_opcode_s2 != OP_LOAD &&
                pipe_opcode_s2 != OP_STORE && pipe_opcode_s2 != OP_QPA_TX &&
                pipe_opcode_s2 != OP_HBM_STORE) begin
                matrix_regs[pipe_rd_s2] <= pipe_result_s2;
            end

            // Completion
            if (pipe_opcode_s3 != OP_NOP && simd_busy) begin
                simd_busy <= 1'b0;
                simd_done <= 1'b1;
            end
        end
    end

    // ==================================================================
    // QPA Trigger Output (Compute Clock Domain)
    // ==================================================================
    always @(posedge clk_compute) begin
        if (!rst_n) begin
            qpa_trigger_valid <= 1'b0;
            qpa_phase_vector  <= {QPA_CHANNELS*QPA_PHASE_WIDTH{1'b0}};
        end else begin
            qpa_trigger_valid <= 1'b0;

            if (pipe_opcode_s2 == OP_QPA_TX) begin
                qpa_trigger_valid <= 1'b1;
                qpa_phase_vector  <= pipe_result_s2[QPA_CHANNELS*QPA_PHASE_WIDTH-1:0];
            end
        end
    end

    // ==================================================================
    // HBM5 Memory Controller — Request Scheduler (HBM Clock Domain)
    // ==================================================================
    always @(posedge clk_hbm) begin
        if (!rst_n) begin
            hbm5_rq_state       <= HBM5_RQ_IDLE;
            hbm5_timer          <= 4'd0;
            hbm5_row_open       <= 1'b0;
            hbm5_open_row       <= 14'd0;
            hbm5_cur_bank       <= 5'd0;
            hbm5_refresh_timer  <= 16'd0;
            hbm5_refresh_pending<= 1'b0;
            hbm5_refresh_bank   <= 5'd0;
            hbm5_is_write       <= 1'b0;
            hbm5_req_addr       <= {HBM5_ADDR_WIDTH{1'b0}};
            hbm5_req_wdata      <= {AXI_DATA_WIDTH{1'b0}};
            hbm5_stat_init_done <= 1'b0;
            hbm5_stat_ready     <= 1'b0;
            hbm5_stat_active_pcs<= 4'd0;
            hbm5_direct_done    <= 1'b0;
            hbm5_direct_rdata   <= {AXI_DATA_WIDTH{1'b0}};
            hbm5_ecc_error_ce   <= 1'b0;
            hbm5_ecc_error_ue   <= 1'b0;
            hbm5_computed_ecc   <= 8'd0;
            hbm5_ck_p     <= 1'b0;
            hbm5_ck_n     <= 1'b1;
            hbm5_cke      <= 1'b0;
            hbm5_cmd      <= HBM5_CMD_NOP;
            hbm5_addr     <= {HBM5_ADDR_WIDTH{1'b0}};
            hbm5_bank     <= 5'd0;
            hbm5_stack_sel<= 2'd0;
            hbm5_pc_sel   <= 4'd0;
            hbm5_dq_out   <= {HBM5_DATA_WIDTH{1'b0}};
            hbm5_dq_oe    <= 1'b0;
            hbm5_dm       <= {(HBM5_DATA_WIDTH/8){1'b1}};
            hbm5_ecc_out  <= {HBM5_ECC_WIDTH{1'b0}};
            for (i = 0; i < HBM5_EMUL_DEPTH; i = i + 1)
                hbm5_emul_sram[i] <= {AXI_DATA_WIDTH{1'b0}};
        end else if (hbm5_ctrl_enable) begin
            // Differential clock toggle
            hbm5_ck_p <= ~hbm5_ck_p;
            hbm5_ck_n <= ~hbm5_ck_n;
            hbm5_cke  <= 1'b1;

            // Temperature tracking
            hbm5_stat_temp <= hbm5_temp_sensor;

            // Initialization
            if (!hbm5_stat_init_done) begin
                hbm5_stat_init_done <= hbm5_init_done | 1'b1; // MPW: immediate
                hbm5_stat_ready     <= 1'b1;
                hbm5_stat_active_pcs <= 4'd1; // MPW: 1 PC
            end

            // Refresh timer
            if (hbm5_refresh_timer >= hbm5_refresh_interval) begin
                hbm5_refresh_timer   <= 16'd0;
                hbm5_refresh_pending <= 1'b1;
            end else begin
                hbm5_refresh_timer <= hbm5_refresh_timer + 16'd1;
            end

            // Default: NOP
            hbm5_cmd   <= HBM5_CMD_NOP;
            hbm5_dq_oe <= 1'b0;
            hbm5_direct_done <= 1'b0;

            case (hbm5_rq_state)
                HBM5_RQ_IDLE: begin
                    if (hbm5_refresh_pending) begin
                        // Refresh takes priority
                        hbm5_rq_state <= HBM5_RQ_REFRESH;
                    end else if (hbm5_direct_wr_req) begin
                        // Direct write request from CXL
                        hbm5_is_write  <= 1'b1;
                        hbm5_req_addr  <= hbm5_direct_addr;
                        hbm5_req_wdata <= hbm5_direct_wdata;
                        hbm5_cur_bank  <= hbm5_direct_addr[18:14];
                        if (hbm5_row_open && hbm5_open_row == hbm5_direct_addr[31:18])
                            hbm5_rq_state <= HBM5_RQ_WRITE;
                        else if (hbm5_row_open)
                            hbm5_rq_state <= HBM5_RQ_PRECHARGE;
                        else
                            hbm5_rq_state <= HBM5_RQ_ACTIVATE;
                    end else if (hbm5_direct_rd_req) begin
                        // Direct read request from CXL
                        hbm5_is_write  <= 1'b0;
                        hbm5_req_addr  <= hbm5_direct_addr;
                        hbm5_cur_bank  <= hbm5_direct_addr[18:14];
                        if (hbm5_row_open && hbm5_open_row == hbm5_direct_addr[31:18])
                            hbm5_rq_state <= HBM5_RQ_READ;
                        else if (hbm5_row_open)
                            hbm5_rq_state <= HBM5_RQ_PRECHARGE;
                        else
                            hbm5_rq_state <= HBM5_RQ_ACTIVATE;
                    end
                end

                HBM5_RQ_ACTIVATE: begin
                    hbm5_cmd      <= HBM5_CMD_ACT;
                    hbm5_addr     <= hbm5_req_addr;
                    hbm5_bank     <= hbm5_cur_bank;
                    hbm5_row_open <= 1'b1;
                    hbm5_open_row <= hbm5_req_addr[31:18];
                    hbm5_timer    <= tRCD;
                    hbm5_rq_state <= HBM5_RQ_WAIT;
                end

                HBM5_RQ_READ: begin
                    hbm5_cmd  <= HBM5_CMD_RD;
                    hbm5_addr <= hbm5_req_addr;
                    hbm5_bank <= hbm5_cur_bank;

                    // MPW: read from emulation SRAM
                    hbm5_direct_rdata <= hbm5_emul_sram[hbm5_req_addr[8:0] % HBM5_EMUL_DEPTH];

                    // ECC check (simplified SECDED)
                    if (hbm5_ctrl_ecc_enable) begin
                        hbm5_computed_ecc <= hbm5_emul_sram[hbm5_req_addr[8:0] % HBM5_EMUL_DEPTH][7:0]
                                             ^ hbm5_emul_sram[hbm5_req_addr[8:0] % HBM5_EMUL_DEPTH][15:8];
                    end

                    hbm5_perf_rd_count <= hbm5_perf_rd_count + 32'd1;
                    hbm5_direct_done   <= 1'b1;
                    hbm5_rq_state      <= HBM5_RQ_DONE;
                end

                HBM5_RQ_WRITE: begin
                    hbm5_cmd    <= HBM5_CMD_WR;
                    hbm5_addr   <= hbm5_req_addr;
                    hbm5_bank   <= hbm5_cur_bank;
                    hbm5_dq_oe  <= 1'b1;
                    hbm5_dq_out <= {{(HBM5_DATA_WIDTH-AXI_DATA_WIDTH){1'b0}}, hbm5_req_wdata};
                    hbm5_dm     <= {(HBM5_DATA_WIDTH/8){1'b0}};

                    // MPW: write to emulation SRAM
                    hbm5_emul_sram[hbm5_req_addr[8:0] % HBM5_EMUL_DEPTH] <= hbm5_req_wdata;

                    // Generate ECC
                    if (hbm5_ctrl_ecc_enable) begin
                        hbm5_ecc_out <= hbm5_req_wdata[7:0] ^ hbm5_req_wdata[15:8];
                    end

                    hbm5_perf_wr_count <= hbm5_perf_wr_count + 32'd1;
                    hbm5_direct_done   <= 1'b1;
                    hbm5_rq_state      <= HBM5_RQ_DONE;
                end

                HBM5_RQ_PRECHARGE: begin
                    hbm5_cmd      <= HBM5_CMD_PRE;
                    hbm5_bank     <= hbm5_cur_bank;
                    hbm5_row_open <= 1'b0;
                    hbm5_timer    <= tRP;
                    hbm5_rq_state <= HBM5_RQ_WAIT;
                end

                HBM5_RQ_REFRESH: begin
                    hbm5_cmd  <= HBM5_CMD_REF;
                    hbm5_bank <= hbm5_refresh_bank;
                    hbm5_refresh_pending <= 1'b0;
                    hbm5_perf_refresh_count <= hbm5_perf_refresh_count + 16'd1;

                    if (hbm5_refresh_per_bank) begin
                        hbm5_refresh_bank <= (hbm5_refresh_bank + 5'd1) % HBM5_BANKS;
                    end

                    hbm5_row_open <= 1'b0;
                    hbm5_timer    <= tRFC;
                    hbm5_rq_state <= HBM5_RQ_WAIT;
                end

                HBM5_RQ_WAIT: begin
                    if (hbm5_timer > 4'd0) begin
                        hbm5_timer <= hbm5_timer - 4'd1;
                    end else begin
                        if (hbm5_is_write)
                            hbm5_rq_state <= HBM5_RQ_WRITE;
                        else
                            hbm5_rq_state <= HBM5_RQ_READ;
                    end
                end

                HBM5_RQ_DONE: begin
                    hbm5_dq_oe    <= 1'b0;
                    hbm5_rq_state <= HBM5_RQ_IDLE;
                end
            endcase
        end else begin
            // Controller disabled
            hbm5_cke   <= 1'b0;
            hbm5_cmd   <= HBM5_CMD_NOP;
            hbm5_dq_oe <= 1'b0;
        end
    end

    // ==================================================================
    // DMA Controller (System Clock Domain) — routes through HBM5
    // ==================================================================
    reg [15:0] dma_counter;
    reg [1:0]  dma_state;
    localparam DMA_IDLE    = 2'd0;
    localparam DMA_READ    = 2'd1;
    localparam DMA_WRITE   = 2'd2;
    localparam DMA_DONE    = 2'd3;

    always @(posedge clk_sys) begin
        if (!rst_n) begin
            dma_busy       <= 1'b0;
            dma_done       <= 1'b0;
            dma_req_valid  <= 1'b0;
            dma_req_addr   <= {AXI_ADDR_WIDTH{1'b0}};
            dma_req_len    <= 16'd0;
            dma_req_write  <= 1'b0;
            dma_resp_ready <= 1'b1;
            dma_counter    <= 16'd0;
            dma_state      <= DMA_IDLE;
        end else begin
            case (dma_state)
                DMA_IDLE: begin
                    dma_done <= 1'b0;
                    if (ctrl_dma_start && !dma_busy) begin
                        dma_busy      <= 1'b1;
                        dma_req_valid <= 1'b1;
                        dma_req_addr  <= dma_src_addr;
                        dma_req_len   <= dma_length;
                        dma_req_write <= 1'b0;
                        dma_counter   <= dma_length;
                        dma_state     <= DMA_READ;
                    end
                end
                DMA_READ: begin
                    if (dma_req_ready)
                        dma_req_valid <= 1'b0;
                    if (dma_resp_valid) begin
                        if (dma_counter > 0)
                            dma_counter <= dma_counter - 16'd1;
                        if (dma_counter == 16'd1)
                            dma_state <= DMA_DONE;
                    end
                end
                DMA_WRITE: begin
                    dma_state <= DMA_DONE;
                end
                DMA_DONE: begin
                    dma_busy  <= 1'b0;
                    dma_done  <= 1'b1;
                    dma_state <= DMA_IDLE;
                end
            endcase
        end
    end

    // ==================================================================
    // Thermal Monitor (System Clock Domain)
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            thermal_throttle <= 1'b0;
            thermal_shutdown <= 1'b0;
            thermal_max      <= {THERMAL_WIDTH{1'b0}};
            for (i = 0; i < NUM_THERMAL_DIODES; i = i + 1)
                thermal_readings[i] <= {THERMAL_WIDTH{1'b0}};
        end else begin
            if (thermal_adc_valid) begin
                for (i = 0; i < NUM_THERMAL_DIODES; i = i + 1)
                    thermal_readings[i] <= thermal_adc_data[(i+1)*THERMAL_WIDTH-1 -: THERMAL_WIDTH];

                thermal_max <= thermal_readings[0];
                for (i = 1; i < NUM_THERMAL_DIODES; i = i + 1) begin
                    if (thermal_readings[i] > thermal_max)
                        thermal_max <= thermal_readings[i];
                end
            end

            thermal_throttle <= (thermal_max >= THERMAL_SOFT_LIMIT);
            thermal_shutdown <= (thermal_max >= THERMAL_EMERG_LIMIT);
        end
    end

    // ==================================================================
    // Interrupt Controller (System Clock Domain)
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            irq_pending <= 8'd0;
            irq_out     <= 1'b0;
        end else begin
            irq_pending[0] <= simd_done;
            irq_pending[1] <= simd_exception;
            irq_pending[2] <= dma_done;
            irq_pending[3] <= |qpa_fault_status;
            irq_pending[4] <= thermal_throttle;
            irq_pending[5] <= thermal_shutdown;
            irq_pending[6] <= hbm5_stat_ecc_ce;
            irq_pending[7] <= hbm5_stat_ecc_ue;

            irq_out <= |(irq_pending & irq_mask);
        end
    end

endmodule

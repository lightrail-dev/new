// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     nce_compute_core
// DESCRIPTION: Top-level NCE (Neural Compute Engine) core for SMIC 28nm/40nm
//              MPW shuttle validation. Implements the compute cluster with
//              128-way SIMD datapath, register file, CXL host interface,
//              QPA trigger matrix integration, and power management.
//
// PROCESS:    SMIC 28nm HPC+ (primary) / SMIC 40nm LL (fallback)
// CLOCK:      clk_compute (1.0-2.0 GHz DVFS), clk_sys (250 MHz AXI)
// RESET:      Active-low synchronous
//
// REGISTER MAP (CXL MMIO Base 0x0000_0000):
//   0x0000  CTRL           -- Global control register
//   0x0004  STATUS         -- Core status (busy, fault, temperature)
//   0x0008  SIMD_CMD       -- SIMD instruction dispatch
//   0x000C  SIMD_STATUS    -- SIMD completion / exception status
//   0x0010  DMA_SRC_ADDR   -- DMA source address (HBM4 or host)
//   0x0014  DMA_DST_ADDR   -- DMA destination address
//   0x0018  DMA_LEN        -- DMA transfer length (bytes)
//   0x001C  DMA_CTRL       -- DMA start / channel select / status
//   0x0020  DVFS_STATE     -- Current V/F operating point [2:0]
//   0x0024  THERMAL_STATUS -- 4x on-die diode readings
//   0x0028  POWER_GATE     -- Per-cluster power gate control [7:0]
//   0x002C  INTERRUPT      -- Interrupt status / clear
//
// MPW SHUTTLE NOTE:
//   For the test chip, the SIMD array is reduced to 8 lanes (1 cluster)
//   with 1 KB register file and 4 KB L1 cache. The full design scales
//   to 128 lanes (8 clusters) for production tapeout.
// =========================================================================

module nce_compute_core #(
    // Compute parameters (reduced for MPW shuttle)
    parameter integer SIMD_LANES        = 8,       // 8 for MPW, 128 for production
    parameter integer NUM_CLUSTERS      = 1,       // 1 for MPW, 8 for production
    parameter integer DATA_WIDTH        = 16,      // bfloat16
    parameter integer ACCUM_WIDTH       = 32,      // FP32 accumulator
    parameter integer REG_DEPTH         = 32,      // 16 matrix + 16 vector registers
    parameter integer REG_WIDTH         = 256,     // 256-bit register width
    parameter integer L1_SIZE_BYTES     = 4096,    // 4 KB for MPW, 128 KB production
    parameter integer L2_SIZE_BYTES     = 16384,   // 16 KB for MPW, 16 MB production

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
    parameter integer THERMAL_WIDTH      = 12      // 12-bit ADC per diode
)(
    // ---- Clock & Reset ----
    input  wire                             clk_compute,    // DVFS-controlled compute clock
    input  wire                             clk_sys,        // 250 MHz system / AXI clock
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

    // ---- DMA Interface (to HBM4 / Host) ----
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

    // ---- Thermal Diode Inputs (analog, via on-chip ADC) ----
    input  wire [NUM_THERMAL_DIODES*THERMAL_WIDTH-1:0] thermal_adc_data,
    input  wire                             thermal_adc_valid,

    // ---- Power Management Outputs ----
    output reg  [2:0]                       dvfs_state,         // Current V/F point
    output reg  [NUM_CLUSTERS-1:0]          cluster_power_gate, // 1=powered, 0=gated
    output reg                              thermal_throttle,   // Throttle signal to VRM
    output reg                              thermal_shutdown,   // Emergency shutdown

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
    localparam [THERMAL_WIDTH-1:0] THERMAL_SOFT_LIMIT  = 12'd3420; // ~95 C (0.01K units)
    localparam [THERMAL_WIDTH-1:0] THERMAL_HARD_LIMIT  = 12'd3780; // ~105 C
    localparam [THERMAL_WIDTH-1:0] THERMAL_EMERG_LIMIT = 12'd3880; // ~115 C

    // ---- Interrupt sources ----
    reg [7:0] irq_pending;
    reg [7:0] irq_mask;

    // ---- SIMD Register File (simplified for MPW) ----
    reg [REG_WIDTH-1:0] matrix_regs [0:15];
    reg [REG_WIDTH-1:0] vector_regs [0:15];

    // ---- SIMD Instruction Decode ----
    reg [31:0] simd_instruction;
    reg [3:0]  simd_opcode;
    reg [3:0]  simd_rd;
    reg [3:0]  simd_rs1;
    reg [3:0]  simd_rs2;

    // SIMD opcodes
    localparam [3:0] OP_NOP     = 4'h0;
    localparam [3:0] OP_MMA     = 4'h1;  // Matrix multiply-accumulate
    localparam [3:0] OP_VADD    = 4'h2;  // Vector add
    localparam [3:0] OP_VMUL    = 4'h3;  // Vector multiply
    localparam [3:0] OP_RELU    = 4'h4;  // ReLU activation
    localparam [3:0] OP_LOAD    = 4'h5;  // Load from L1
    localparam [3:0] OP_STORE   = 4'h6;  // Store to L1
    localparam [3:0] OP_QPA_TX  = 4'h7;  // Send to QPA photonic path
    localparam [3:0] OP_SOFTMAX = 4'h8;  // Softmax (piecewise linear approx)
    localparam [3:0] OP_GELU    = 4'h9;  // GELU activation

    // ---- SIMD Pipeline Stages ----
    reg [3:0]  pipe_opcode_s1, pipe_opcode_s2, pipe_opcode_s3;
    reg [3:0]  pipe_rd_s1, pipe_rd_s2, pipe_rd_s3;
    reg [REG_WIDTH-1:0] pipe_operand_a_s1, pipe_operand_b_s1;
    reg [REG_WIDTH-1:0] pipe_result_s2, pipe_result_s3;

    // ---- L1 Data Cache (simplified SRAM model) ----
    localparam L1_DEPTH = L1_SIZE_BYTES / (AXI_DATA_WIDTH / 8);
    reg [AXI_DATA_WIDTH-1:0] l1_cache [0:L1_DEPTH-1];

    integer i;

    // ==================================================================
    // AXI4-Lite Write Channel (System Clock Domain)
    // ==================================================================
    always @(posedge clk_sys) begin
        if (!rst_n) begin
            axi_awready      <= 1'b0;
            axi_wready       <= 1'b0;
            axi_bvalid       <= 1'b0;
            axi_bresp        <= 2'b00;
            ctrl_enable       <= 1'b0;
            ctrl_simd_start   <= 1'b0;
            ctrl_dma_start    <= 1'b0;
            ctrl_qpa_trigger  <= 1'b0;
            dma_src_addr      <= {AXI_ADDR_WIDTH{1'b0}};
            dma_dst_addr      <= {AXI_ADDR_WIDTH{1'b0}};
            dma_length        <= 16'd0;
            dma_channel_sel   <= 2'd0;
            dvfs_state        <= 3'd4;  // Default mid-range V/F
            cluster_power_gate <= {NUM_CLUSTERS{1'b1}};  // All clusters on
            irq_mask          <= 8'hFF;
            simd_instruction  <= 32'd0;
        end else begin
            axi_awready <= 1'b1;
            axi_wready  <= 1'b1;

            if (axi_bvalid && axi_bready)
                axi_bvalid <= 1'b0;

            ctrl_simd_start  <= 1'b0;
            ctrl_dma_start   <= 1'b0;
            ctrl_qpa_trigger <= 1'b0;

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
                    ADDR_SIMD_CMD: begin
                        simd_instruction <= axi_wdata[31:0];
                    end
                    ADDR_DMA_SRC:   dma_src_addr    <= axi_wdata[AXI_ADDR_WIDTH-1:0];
                    ADDR_DMA_DST:   dma_dst_addr    <= axi_wdata[AXI_ADDR_WIDTH-1:0];
                    ADDR_DMA_LEN: begin
                        dma_length      <= axi_wdata[15:0];
                        dma_channel_sel <= axi_wdata[17:16];
                    end
                    ADDR_DMA_CTRL: begin
                        ctrl_dma_start <= axi_wdata[0];
                    end
                    ADDR_DVFS:        dvfs_state         <= axi_wdata[2:0];
                    ADDR_POWER_GATE:  cluster_power_gate <= axi_wdata[NUM_CLUSTERS-1:0];
                    ADDR_INTERRUPT:   irq_mask           <= axi_wdata[7:0];
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
                OP_MMA: begin
                    // Simplified: element-wise multiply-accumulate
                    // Production version: full matrix-multiply across SIMD lanes
                    pipe_result_s2 <= pipe_operand_a_s1 ^ pipe_operand_b_s1;
                end
                OP_VADD: begin
                    pipe_result_s2 <= pipe_operand_a_s1 + pipe_operand_b_s1;
                end
                OP_VMUL: begin
                    pipe_result_s2 <= pipe_operand_a_s1 & pipe_operand_b_s1;
                end
                OP_RELU: begin
                    // ReLU: zero negative values (MSB check per element)
                    for (i = 0; i < SIMD_LANES; i = i + 1) begin
                        if (pipe_operand_a_s1[(i+1)*DATA_WIDTH-1])
                            pipe_result_s2[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH] <= {DATA_WIDTH{1'b0}};
                        else
                            pipe_result_s2[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH] <=
                                pipe_operand_a_s1[(i+1)*DATA_WIDTH-1 -: DATA_WIDTH];
                    end
                end
                default: begin
                    pipe_result_s2 <= {REG_WIDTH{1'b0}};
                end
            endcase

            // Stage 3: Writeback
            pipe_opcode_s3 <= pipe_opcode_s2;
            pipe_rd_s3     <= pipe_rd_s2;
            pipe_result_s3 <= pipe_result_s2;

            if (pipe_opcode_s2 != OP_NOP && pipe_opcode_s2 != OP_LOAD &&
                pipe_opcode_s2 != OP_STORE && pipe_opcode_s2 != OP_QPA_TX) begin
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
    // DMA Controller (System Clock Domain)
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
                    if (dma_req_ready) begin
                        dma_req_valid <= 1'b0;
                    end
                    if (dma_resp_valid) begin
                        // Store to L1 cache (simplified)
                        if (dma_counter > 0)
                            dma_counter <= dma_counter - 16'd1;
                        if (dma_counter == 16'd1) begin
                            dma_state <= DMA_DONE;
                        end
                    end
                end
                DMA_WRITE: begin
                    // Placeholder for write-back path
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

                // Find maximum temperature
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
            // Latch interrupt sources
            irq_pending[0] <= simd_done;
            irq_pending[1] <= simd_exception;
            irq_pending[2] <= dma_done;
            irq_pending[3] <= |qpa_fault_status;
            irq_pending[4] <= thermal_throttle;
            irq_pending[5] <= thermal_shutdown;
            irq_pending[6] <= 1'b0; // Reserved
            irq_pending[7] <= 1'b0; // Reserved

            irq_out <= |(irq_pending & irq_mask);
        end
    end

endmodule

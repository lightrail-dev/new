// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     dma_engine
// DESCRIPTION: Scatter-gather DMA engine for bulk data transfer between
//              host memory (via PCIe) and the inter-chip bridge. Supports
//              up to 8 descriptor ring entries. Generates completion
//              interrupts.
//
// INTERFACE:  AXI4-Lite register access + internal bridge TX/RX bus
// =========================================================================

module dma_engine #(
    parameter integer DESC_DEPTH = 8,
    parameter integer DATA_WIDTH = 64
)(
    input  wire                    clk,
    input  wire                    rst_n,

    // Register interface (from AXI4-Lite decoder)
    input  wire [7:0]              reg_addr,
    input  wire [31:0]             reg_wdata,
    input  wire                    reg_wen,
    input  wire                    reg_ren,
    output reg  [31:0]             reg_rdata,
    output reg                     reg_rvalid,

    // Bridge TX interface
    output reg                     brg_tx_req,
    output reg  [7:0]              brg_tx_pkt_type,
    output reg  [31:0]             brg_tx_addr,
    output reg  [DATA_WIDTH-1:0]   brg_tx_data,
    output reg                     brg_tx_data_valid,
    output reg                     brg_tx_data_last,
    input  wire                    brg_tx_ready,

    // Bridge RX interface
    input  wire [DATA_WIDTH-1:0]   brg_rx_data,
    input  wire                    brg_rx_data_valid,
    input  wire                    brg_rx_pkt_valid,

    // Interrupt output
    output reg                     dma_done_irq,
    output reg                     dma_error_irq
);

    // DMA descriptor format (simplified):
    // [31:0]  src_addr
    // [63:32] dst_addr
    // [79:64] length (beats)
    // [80]    direction (0=TX to bridge, 1=RX from bridge)
    // [81]    irq_on_complete

    localparam DESC_W = 96;

    reg [DESC_W-1:0]            desc_ring [0:DESC_DEPTH-1];
    reg [$clog2(DESC_DEPTH)-1:0] head_ptr;
    reg [$clog2(DESC_DEPTH)-1:0] tail_ptr;
    reg                          dma_enable;

    // Current descriptor fields
    wire [31:0] cur_src    = desc_ring[head_ptr][31:0];
    wire [31:0] cur_dst    = desc_ring[head_ptr][63:32];
    wire [15:0] cur_len    = desc_ring[head_ptr][79:64];
    wire        cur_dir    = desc_ring[head_ptr][80];
    wire        cur_irq_en = desc_ring[head_ptr][81];

    // DMA state machine
    localparam [2:0] DMA_IDLE     = 3'd0,
                     DMA_FETCH    = 3'd1,
                     DMA_TX_DATA  = 3'd2,
                     DMA_RX_WAIT  = 3'd3,
                     DMA_COMPLETE = 3'd4;

    reg [2:0]  dma_state;
    reg [15:0] beat_count;
    reg [31:0] cur_addr;

    // Register decode
    // 0x00: DMA_CTRL     (bit 0 = enable, bit 1 = soft reset)
    // 0x04: DMA_STATUS   (bit 0 = busy, bit 1 = error)
    // 0x08: DESC_HEAD    (write to push descriptor)
    // 0x0C: DESC_TAIL    (read-only, completed pointer)
    // 0x10–0x1F: DESC_DATA[0..2] (3 × 32-bit writes = one 96-bit descriptor)

    reg [31:0] desc_data [0:2];
    reg [1:0]  desc_word_idx;
    reg        dma_busy;
    reg        dma_err;

    always @(posedge clk) begin
        if (!rst_n) begin
            dma_enable    <= 1'b0;
            head_ptr      <= {$clog2(DESC_DEPTH){1'b0}};
            tail_ptr      <= {$clog2(DESC_DEPTH){1'b0}};
            dma_state     <= DMA_IDLE;
            beat_count    <= 16'd0;
            cur_addr      <= 32'd0;
            dma_done_irq  <= 1'b0;
            dma_error_irq <= 1'b0;
            dma_busy      <= 1'b0;
            dma_err       <= 1'b0;
            desc_word_idx <= 2'd0;
            brg_tx_req        <= 1'b0;
            brg_tx_pkt_type   <= 8'd0;
            brg_tx_addr       <= 32'd0;
            brg_tx_data       <= {DATA_WIDTH{1'b0}};
            brg_tx_data_valid <= 1'b0;
            brg_tx_data_last  <= 1'b0;
            reg_rdata         <= 32'd0;
            reg_rvalid        <= 1'b0;
        end else begin
            dma_done_irq  <= 1'b0;
            dma_error_irq <= 1'b0;
            brg_tx_req        <= 1'b0;
            brg_tx_data_valid <= 1'b0;
            brg_tx_data_last  <= 1'b0;
            reg_rvalid        <= 1'b0;

            // Register writes
            if (reg_wen) begin
                case (reg_addr)
                    8'h00: begin
                        dma_enable <= reg_wdata[0];
                        if (reg_wdata[1]) begin
                            head_ptr  <= {$clog2(DESC_DEPTH){1'b0}};
                            tail_ptr  <= {$clog2(DESC_DEPTH){1'b0}};
                            dma_state <= DMA_IDLE;
                            dma_busy  <= 1'b0;
                            dma_err   <= 1'b0;
                        end
                    end
                    8'h10: desc_data[0] <= reg_wdata;
                    8'h14: desc_data[1] <= reg_wdata;
                    8'h18: begin
                        desc_data[2] <= reg_wdata;
                        // Auto-commit descriptor
                        desc_ring[tail_ptr] <= {reg_wdata, desc_data[1], desc_data[0]};
                        tail_ptr <= tail_ptr + 1'b1;
                    end
                    default: ;
                endcase
            end

            // Register reads
            if (reg_ren) begin
                reg_rvalid <= 1'b1;
                case (reg_addr)
                    8'h00: reg_rdata <= {30'd0, 1'b0, dma_enable};
                    8'h04: reg_rdata <= {30'd0, dma_err, dma_busy};
                    8'h08: reg_rdata <= {{(32-$clog2(DESC_DEPTH)){1'b0}}, head_ptr};
                    8'h0C: reg_rdata <= {{(32-$clog2(DESC_DEPTH)){1'b0}}, tail_ptr};
                    default: reg_rdata <= 32'd0;
                endcase
            end

            // DMA state machine
            case (dma_state)
                DMA_IDLE: begin
                    dma_busy <= 1'b0;
                    if (dma_enable && (head_ptr != tail_ptr)) begin
                        dma_state  <= DMA_FETCH;
                        dma_busy   <= 1'b1;
                        beat_count <= 16'd0;
                        cur_addr   <= cur_src;
                    end
                end

                DMA_FETCH: begin
                    if (!cur_dir) begin
                        // TX path: send data to bridge
                        brg_tx_req      <= 1'b1;
                        brg_tx_pkt_type <= 8'h01;   // DMA write
                        brg_tx_addr     <= cur_dst;
                        dma_state       <= DMA_TX_DATA;
                    end else begin
                        // RX path: wait for data from bridge
                        dma_state <= DMA_RX_WAIT;
                    end
                end

                DMA_TX_DATA: begin
                    if (brg_tx_ready) begin
                        brg_tx_data       <= {DATA_WIDTH{1'b0}} | cur_addr; // placeholder data
                        brg_tx_data_valid <= 1'b1;
                        beat_count        <= beat_count + 16'd1;
                        cur_addr          <= cur_addr + 32'd8;
                        if (beat_count == cur_len - 16'd1) begin
                            brg_tx_data_last <= 1'b1;
                            dma_state        <= DMA_COMPLETE;
                        end
                    end
                end

                DMA_RX_WAIT: begin
                    if (brg_rx_pkt_valid) begin
                        dma_state <= DMA_COMPLETE;
                    end
                end

                DMA_COMPLETE: begin
                    head_ptr <= head_ptr + 1'b1;
                    if (cur_irq_en) begin
                        dma_done_irq <= 1'b1;
                    end
                    dma_state <= DMA_IDLE;
                end

                default: dma_state <= DMA_IDLE;
            endcase
        end
    end

endmodule

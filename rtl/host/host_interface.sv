// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     host_interface
// DESCRIPTION: Top-level host interface unit combining AXI4-Lite target,
//              DMA engine, and interrupt controller. Connects to the
//              PCIe Gen 6 root complex for configuration, bulk data
//              transfer, and interrupt handling.
//
// ADDRESS MAP (16-bit, 64 KB per NCE):
//   0x0000–0x00FF: Bridge Control/Status
//   0x0100–0x04FF: DMA Descriptors & Control
//   0x0400–0x043F: Interrupt Controller
//   0x0800–0x08FF: Power Management (routed to pwr_mgt_controller)
//   0x1000–0x103F: Node Discovery
// =========================================================================

module host_interface #(
    parameter integer ADDR_WIDTH = 16,
    parameter integer DATA_WIDTH = 32,
    parameter integer BRG_WIDTH  = 64
)(
    input  wire                     aclk,
    input  wire                     aresetn,

    // AXI4-Lite Slave Interface
    input  wire [ADDR_WIDTH-1:0]    s_axi_awaddr,
    input  wire                     s_axi_awvalid,
    output wire                     s_axi_awready,
    input  wire [DATA_WIDTH-1:0]    s_axi_wdata,
    input  wire [DATA_WIDTH/8-1:0]  s_axi_wstrb,
    input  wire                     s_axi_wvalid,
    output wire                     s_axi_wready,
    output wire [1:0]               s_axi_bresp,
    output wire                     s_axi_bvalid,
    input  wire                     s_axi_bready,
    input  wire [ADDR_WIDTH-1:0]    s_axi_araddr,
    input  wire                     s_axi_arvalid,
    output wire                     s_axi_arready,
    output wire [DATA_WIDTH-1:0]    s_axi_rdata,
    output wire [1:0]               s_axi_rresp,
    output wire                     s_axi_rvalid,
    input  wire                     s_axi_rready,

    // Bridge TX interface
    output wire                     brg_tx_req,
    output wire [7:0]               brg_tx_pkt_type,
    output wire [31:0]              brg_tx_addr,
    output wire [BRG_WIDTH-1:0]     brg_tx_data,
    output wire                     brg_tx_data_valid,
    output wire                     brg_tx_data_last,
    input  wire                     brg_tx_ready,

    // Bridge RX interface
    input  wire [BRG_WIDTH-1:0]     brg_rx_data,
    input  wire                     brg_rx_data_valid,
    input  wire                     brg_rx_pkt_valid,

    // Bridge statistics (read-only)
    input  wire [31:0]              brg_stat_tx_packets,
    input  wire [31:0]              brg_stat_rx_packets,
    input  wire [31:0]              brg_stat_crc_errors,
    input  wire                     brg_link_up,

    // Power management register bus (to pwr_mgt_controller)
    output wire [7:0]               pwr_reg_addr,
    output wire [31:0]              pwr_reg_wdata,
    output wire                     pwr_reg_wen,
    output wire                     pwr_reg_ren,
    input  wire [31:0]              pwr_reg_rdata,
    input  wire                     pwr_reg_rvalid,

    // Node identity
    input  wire                     node_id,
    input  wire [31:0]              fw_version,
    input  wire                     partner_link_up,

    // IRQ output
    output wire                     irq_out
);

    // ---- AXI4-Lite decoder wires ----
    wire [ADDR_WIDTH-1:0]    reg_addr;
    wire [DATA_WIDTH-1:0]    reg_wdata;
    wire [DATA_WIDTH/8-1:0]  reg_wstrb;
    wire                     reg_wen;
    wire                     reg_ren;
    reg  [DATA_WIDTH-1:0]    reg_rdata;
    reg                      reg_rvalid;

    axi4lite_target #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_axi (
        .aclk          (aclk),
        .aresetn       (aresetn),
        .s_axi_awaddr  (s_axi_awaddr),
        .s_axi_awvalid (s_axi_awvalid),
        .s_axi_awready (s_axi_awready),
        .s_axi_wdata   (s_axi_wdata),
        .s_axi_wstrb   (s_axi_wstrb),
        .s_axi_wvalid  (s_axi_wvalid),
        .s_axi_wready  (s_axi_wready),
        .s_axi_bresp   (s_axi_bresp),
        .s_axi_bvalid  (s_axi_bvalid),
        .s_axi_bready  (s_axi_bready),
        .s_axi_araddr  (s_axi_araddr),
        .s_axi_arvalid (s_axi_arvalid),
        .s_axi_arready (s_axi_arready),
        .s_axi_rdata   (s_axi_rdata),
        .s_axi_rresp   (s_axi_rresp),
        .s_axi_rvalid  (s_axi_rvalid),
        .s_axi_rready  (s_axi_rready),
        .reg_addr      (reg_addr),
        .reg_wdata     (reg_wdata),
        .reg_wstrb     (reg_wstrb),
        .reg_wen       (reg_wen),
        .reg_ren       (reg_ren),
        .reg_rdata     (reg_rdata),
        .reg_rvalid    (reg_rvalid)
    );

    // ---- Address Decode ----
    wire addr_is_bridge = (reg_addr[15:8] == 8'h00);
    wire addr_is_dma    = (reg_addr[15:8] == 8'h01);
    wire addr_is_irq    = (reg_addr[15:8] == 8'h04);
    wire addr_is_pwr    = (reg_addr[15:8] == 8'h08);
    wire addr_is_node   = (reg_addr[15:8] == 8'h10);

    // ---- DMA Engine ----
    wire [31:0] dma_rdata;
    wire        dma_rvalid;
    wire        dma_done_irq;
    wire        dma_error_irq;

    dma_engine #(
        .DESC_DEPTH(8),
        .DATA_WIDTH(BRG_WIDTH)
    ) u_dma (
        .clk               (aclk),
        .rst_n             (aresetn),
        .reg_addr          (reg_addr[7:0]),
        .reg_wdata         (reg_wdata),
        .reg_wen           (reg_wen && addr_is_dma),
        .reg_ren           (reg_ren && addr_is_dma),
        .reg_rdata         (dma_rdata),
        .reg_rvalid        (dma_rvalid),
        .brg_tx_req        (brg_tx_req),
        .brg_tx_pkt_type   (brg_tx_pkt_type),
        .brg_tx_addr       (brg_tx_addr),
        .brg_tx_data       (brg_tx_data),
        .brg_tx_data_valid (brg_tx_data_valid),
        .brg_tx_data_last  (brg_tx_data_last),
        .brg_tx_ready      (brg_tx_ready),
        .brg_rx_data       (brg_rx_data),
        .brg_rx_data_valid (brg_rx_data_valid),
        .brg_rx_pkt_valid  (brg_rx_pkt_valid),
        .dma_done_irq      (dma_done_irq),
        .dma_error_irq     (dma_error_irq)
    );

    // ---- Interrupt Controller ----
    wire [31:0] irq_rdata;
    wire        irq_rvalid;

    wire [15:0] irq_sources = {
        12'd0,
        dma_error_irq,      // bit 3
        dma_done_irq,       // bit 2
        ~brg_link_up,       // bit 1: link-down
        1'b0                // bit 0: reserved
    };

    interrupt_controller #(.NUM_IRQS(16)) u_irq (
        .clk        (aclk),
        .rst_n      (aresetn),
        .irq_sources(irq_sources),
        .reg_addr   (reg_addr[3:0]),
        .reg_wdata  (reg_wdata),
        .reg_wen    (reg_wen && addr_is_irq),
        .reg_ren    (reg_ren && addr_is_irq),
        .reg_rdata  (irq_rdata),
        .reg_rvalid (irq_rvalid),
        .irq_out    (irq_out)
    );

    // ---- Power Management passthrough ----
    assign pwr_reg_addr  = reg_addr[7:0];
    assign pwr_reg_wdata = reg_wdata;
    assign pwr_reg_wen   = reg_wen && addr_is_pwr;
    assign pwr_reg_ren   = reg_ren && addr_is_pwr;

    // ---- Bridge CSR (read-only statistics + control) ----
    reg [31:0] brg_csr_rdata;
    reg        brg_csr_rvalid;
    reg        brg_loopback_en;

    always @(posedge aclk) begin
        if (!aresetn) begin
            brg_csr_rdata  <= 32'd0;
            brg_csr_rvalid <= 1'b0;
            brg_loopback_en <= 1'b0;
        end else begin
            brg_csr_rvalid <= 1'b0;
            if (reg_wen && addr_is_bridge && reg_addr[7:0] == 8'h00)
                brg_loopback_en <= reg_wdata[0];
            if (reg_ren && addr_is_bridge) begin
                brg_csr_rvalid <= 1'b1;
                case (reg_addr[7:0])
                    8'h00: brg_csr_rdata <= {31'd0, brg_loopback_en};
                    8'h04: brg_csr_rdata <= {31'd0, brg_link_up};
                    8'h08: brg_csr_rdata <= brg_stat_tx_packets;
                    8'h0C: brg_csr_rdata <= brg_stat_rx_packets;
                    8'h10: brg_csr_rdata <= brg_stat_crc_errors;
                    default: brg_csr_rdata <= 32'd0;
                endcase
            end
        end
    end

    // ---- Node Discovery (read-only) ----
    reg [31:0] node_rdata;
    reg        node_rvalid;

    always @(posedge aclk) begin
        if (!aresetn) begin
            node_rdata  <= 32'd0;
            node_rvalid <= 1'b0;
        end else begin
            node_rvalid <= 1'b0;
            if (reg_ren && addr_is_node) begin
                node_rvalid <= 1'b1;
                case (reg_addr[7:0])
                    8'h00: node_rdata <= {31'd0, node_id};
                    8'h04: node_rdata <= fw_version;
                    8'h08: node_rdata <= {31'd0, partner_link_up};
                    default: node_rdata <= 32'd0;
                endcase
            end
        end
    end

    // ---- Read Data Mux ----
    always @(*) begin
        if (brg_csr_rvalid)       begin reg_rdata = brg_csr_rdata; reg_rvalid = 1'b1; end
        else if (dma_rvalid)      begin reg_rdata = dma_rdata;     reg_rvalid = 1'b1; end
        else if (irq_rvalid)      begin reg_rdata = irq_rdata;     reg_rvalid = 1'b1; end
        else if (pwr_reg_rvalid)  begin reg_rdata = pwr_reg_rdata; reg_rvalid = 1'b1; end
        else if (node_rvalid)     begin reg_rdata = node_rdata;    reg_rvalid = 1'b1; end
        else                      begin reg_rdata = 32'd0;         reg_rvalid = 1'b0; end
    end

endmodule

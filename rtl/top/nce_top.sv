// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     nce_top
// DESCRIPTION: Top-level chip wrapper for the Neural Compute Engine (NCE).
//              Instantiates the inter-chip bridge controller, host interface
//              (AXI4-Lite), and power management controller. The same RTL
//              is used for both Node A (left) and Node B (right); the
//              NODE_ID strap pin selects the identity.
//
// CLOCKS:
//   sys_clk     — 200 MHz system/control clock
//   brg_clk     — 500 MHz source-synchronous bridge clock
//
// STRAP PINS:
//   node_id     — 0 = Node A (left), 1 = Node B (right)
// =========================================================================

module nce_top #(
    parameter integer BRG_DATA_WIDTH = 64,
    parameter integer AXI_ADDR_WIDTH = 16,
    parameter integer AXI_DATA_WIDTH = 32,
    parameter integer MAX_CREDITS    = 16,
    parameter [31:0]  FW_VERSION     = 32'h0001_0000  // v1.0.0
)(
    // ---- System ----
    input  wire        sys_clk,        // 200 MHz
    input  wire        sys_rst_n,
    input  wire        brg_clk,        // 500 MHz
    input  wire        brg_rst_n,

    // ---- Strap Pins ----
    input  wire        node_id,        // 0 = Node A, 1 = Node B

    // ---- AXI4-Lite Host Interface (PCIe Gen 6) ----
    input  wire [AXI_ADDR_WIDTH-1:0]   s_axi_awaddr,
    input  wire                         s_axi_awvalid,
    output wire                         s_axi_awready,
    input  wire [AXI_DATA_WIDTH-1:0]   s_axi_wdata,
    input  wire [AXI_DATA_WIDTH/8-1:0] s_axi_wstrb,
    input  wire                         s_axi_wvalid,
    output wire                         s_axi_wready,
    output wire [1:0]                   s_axi_bresp,
    output wire                         s_axi_bvalid,
    input  wire                         s_axi_bready,
    input  wire [AXI_ADDR_WIDTH-1:0]   s_axi_araddr,
    input  wire                         s_axi_arvalid,
    output wire                         s_axi_arready,
    output wire [AXI_DATA_WIDTH-1:0]   s_axi_rdata,
    output wire [1:0]                   s_axi_rresp,
    output wire                         s_axi_rvalid,
    input  wire                         s_axi_rready,

    // ---- Inter-Chip Bridge PHY ----
    output wire [BRG_DATA_WIDTH-1:0]   brg_data_out,
    output wire                         brg_valid_out,
    output wire                         brg_last_out,
    input  wire [BRG_DATA_WIDTH-1:0]   brg_data_in,
    input  wire                         brg_valid_in,
    input  wire                         brg_last_in,

    // Credit channel
    output wire [3:0]                   brg_credit_out,
    output wire                         brg_credit_out_valid,
    input  wire [3:0]                   brg_credit_in,
    input  wire                         brg_credit_in_valid,

    // Error / ACK
    input  wire                         brg_err_in,
    output wire                         brg_ack_out,

    // Forwarded clock output (to remote node)
    output wire                         brg_fwd_clk_p,
    output wire                         brg_fwd_clk_n,

    // ---- I2C / PMBus (to VRM) ----
    output wire        i2c_scl_out,
    output wire        i2c_scl_oen,
    input  wire        i2c_scl_in,
    output wire        i2c_sda_out,
    output wire        i2c_sda_oen,
    input  wire        i2c_sda_in,

    // ---- Interrupt (to PCIe MSI-X) ----
    output wire        irq_out,

    // ---- DVFS outputs ----
    output wire [1:0]  dvfs_state,
    output wire        thermal_shutdown
);

    // ---- Forwarded Clock (LVDS-style) ----
    assign brg_fwd_clk_p =  brg_clk;
    assign brg_fwd_clk_n = ~brg_clk;

    // ---- Internal wires: host ↔ bridge ----
    wire        host_brg_tx_req;
    wire [7:0]  host_brg_tx_pkt_type;
    wire [31:0] host_brg_tx_addr;
    wire [BRG_DATA_WIDTH-1:0] host_brg_tx_data;
    wire        host_brg_tx_data_valid;
    wire        host_brg_tx_data_last;
    wire        host_brg_tx_ready;

    wire [7:0]  brg_rx_pkt_type;
    wire [31:0] brg_rx_addr;
    wire [BRG_DATA_WIDTH-1:0] brg_rx_data;
    wire        brg_rx_data_valid;
    wire        brg_rx_data_last;
    wire        brg_rx_pkt_valid;

    // Bridge statistics
    wire [31:0] brg_stat_tx, brg_stat_rx, brg_stat_crc;
    wire        brg_link_up;

    // Power management register bus
    wire [7:0]  pwr_reg_addr;
    wire [31:0] pwr_reg_wdata;
    wire        pwr_reg_wen;
    wire        pwr_reg_ren;
    wire [31:0] pwr_reg_rdata;
    wire        pwr_reg_rvalid;

    // DVFS wires
    wire [15:0] target_voltage;
    wire [15:0] target_freq;
    wire        dvfs_change_req;

    // ---- Bridge Controller (runs on brg_clk) ----
    chip_to_chip_bridge #(
        .DATA_WIDTH  (BRG_DATA_WIDTH),
        .MAX_CREDITS (MAX_CREDITS),
        .MAX_BEATS   (8),
        .CREDIT_WIDTH(4)
    ) u_bridge (
        .clk                 (brg_clk),
        .rst_n               (brg_rst_n),
        .node_id             (node_id),
        .tx_req              (host_brg_tx_req),
        .tx_pkt_type         (host_brg_tx_pkt_type),
        .tx_addr             (host_brg_tx_addr),
        .tx_data             (host_brg_tx_data),
        .tx_data_valid       (host_brg_tx_data_valid),
        .tx_data_last        (host_brg_tx_data_last),
        .tx_ready            (host_brg_tx_ready),
        .rx_pkt_type         (brg_rx_pkt_type),
        .rx_addr             (brg_rx_addr),
        .rx_data             (brg_rx_data),
        .rx_data_valid       (brg_rx_data_valid),
        .rx_data_last        (brg_rx_data_last),
        .rx_pkt_valid        (brg_rx_pkt_valid),
        .brg_data_out        (brg_data_out),
        .brg_valid_out       (brg_valid_out),
        .brg_data_in         (brg_data_in),
        .brg_valid_in        (brg_valid_in),
        .brg_last_in         (brg_last_in),
        .brg_last_out        (brg_last_out),
        .brg_credit_out      (brg_credit_out),
        .brg_credit_out_valid(brg_credit_out_valid),
        .brg_credit_in       (brg_credit_in),
        .brg_credit_in_valid (brg_credit_in_valid),
        .brg_err_in          (brg_err_in),
        .brg_ack_out         (brg_ack_out),
        .stat_tx_packets     (brg_stat_tx),
        .stat_rx_packets     (brg_stat_rx),
        .stat_crc_errors     (brg_stat_crc),
        .link_up             (brg_link_up)
    );

    // ---- Host Interface (runs on sys_clk / aclk) ----
    host_interface #(
        .ADDR_WIDTH(AXI_ADDR_WIDTH),
        .DATA_WIDTH(AXI_DATA_WIDTH),
        .BRG_WIDTH (BRG_DATA_WIDTH)
    ) u_host (
        .aclk               (sys_clk),
        .aresetn             (sys_rst_n),
        .s_axi_awaddr       (s_axi_awaddr),
        .s_axi_awvalid      (s_axi_awvalid),
        .s_axi_awready      (s_axi_awready),
        .s_axi_wdata        (s_axi_wdata),
        .s_axi_wstrb        (s_axi_wstrb),
        .s_axi_wvalid       (s_axi_wvalid),
        .s_axi_wready       (s_axi_wready),
        .s_axi_bresp        (s_axi_bresp),
        .s_axi_bvalid       (s_axi_bvalid),
        .s_axi_bready       (s_axi_bready),
        .s_axi_araddr       (s_axi_araddr),
        .s_axi_arvalid      (s_axi_arvalid),
        .s_axi_arready      (s_axi_arready),
        .s_axi_rdata        (s_axi_rdata),
        .s_axi_rresp        (s_axi_rresp),
        .s_axi_rvalid       (s_axi_rvalid),
        .s_axi_rready       (s_axi_rready),
        .brg_tx_req         (host_brg_tx_req),
        .brg_tx_pkt_type    (host_brg_tx_pkt_type),
        .brg_tx_addr        (host_brg_tx_addr),
        .brg_tx_data        (host_brg_tx_data),
        .brg_tx_data_valid  (host_brg_tx_data_valid),
        .brg_tx_data_last   (host_brg_tx_data_last),
        .brg_tx_ready       (host_brg_tx_ready),
        .brg_rx_data        (brg_rx_data),
        .brg_rx_data_valid  (brg_rx_data_valid),
        .brg_rx_pkt_valid   (brg_rx_pkt_valid),
        .brg_stat_tx_packets(brg_stat_tx),
        .brg_stat_rx_packets(brg_stat_rx),
        .brg_stat_crc_errors(brg_stat_crc),
        .brg_link_up        (brg_link_up),
        .pwr_reg_addr       (pwr_reg_addr),
        .pwr_reg_wdata      (pwr_reg_wdata),
        .pwr_reg_wen        (pwr_reg_wen),
        .pwr_reg_ren        (pwr_reg_ren),
        .pwr_reg_rdata      (pwr_reg_rdata),
        .pwr_reg_rvalid     (pwr_reg_rvalid),
        .node_id            (node_id),
        .fw_version         (FW_VERSION),
        .partner_link_up    (brg_link_up),
        .irq_out            (irq_out)
    );

    // ---- Power Management Controller (runs on sys_clk) ----
    pwr_mgt_controller #(
        .CLK_FREQ_HZ  (200_000_000),
        .I2C_FREQ_HZ  (400_000),
        .POLL_INTERVAL (200_000_000)
    ) u_pwr (
        .clk             (sys_clk),
        .rst_n           (sys_rst_n),
        .reg_addr        (pwr_reg_addr),
        .reg_wdata       (pwr_reg_wdata),
        .reg_wen         (pwr_reg_wen),
        .reg_ren         (pwr_reg_ren),
        .reg_rdata       (pwr_reg_rdata),
        .reg_rvalid      (pwr_reg_rvalid),
        .scl_out         (i2c_scl_out),
        .scl_oen         (i2c_scl_oen),
        .scl_in          (i2c_scl_in),
        .sda_out         (i2c_sda_out),
        .sda_oen         (i2c_sda_oen),
        .sda_in          (i2c_sda_in),
        .dvfs_state      (dvfs_state),
        .target_voltage  (target_voltage),
        .target_freq     (target_freq),
        .dvfs_change_req (dvfs_change_req),
        .thermal_shutdown(thermal_shutdown)
    );

endmodule

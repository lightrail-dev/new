// -----------------------------------------------------------------------------
// LR-NCE-A0 — Neural Compute Engine ASIC top-level
// Copyright (c) 2026 LightRail AI.  All rights reserved.
// -----------------------------------------------------------------------------
// 4 compute clusters × 64 systolic lanes (256 lanes total), 4 HBM4 stacks
// (1024-bit each, 6.4 Tbps aggregate), PCIe Gen 6 ×16 host link, JTAG/UCIe.
// 116 M gate-count estimate (post-synth).  600 W TDP envelope.
// -----------------------------------------------------------------------------
`default_nettype none

module lr_nce_top #(
    parameter int unsigned NUM_CLUSTERS = 4,
    parameter int unsigned LANES_PER_CL = 64,
    parameter int unsigned NUM_HBM      = 4,
    parameter int unsigned HBM_WIDTH    = 1024
) (
    // ---- clocks
    input  wire                                   clk_core,        // 1.5 GHz
    input  wire                                   clk_mem,         // 1.6 GHz (HBM4 logic)
    input  wire [NUM_HBM-1:0]                     clk_hbm_phy,     // 6.4 Gbps/pin/2 = 3.2 GHz
    input  wire                                   clk_pcie,        // PCIe Gen 6 32 GT/s aux
    input  wire                                   clk_ucie_tx,
    input  wire                                   clk_ucie_rx,
    input  wire                                   clk_jtag,
    input  wire                                   clk_aux,
    // ---- resets
    input  wire                                   por_rst_n,
    input  wire                                   warm_rst_n,
    input  wire                                   jtag_rst_n,
    // ---- HBM4 PHY interface (4 stacks × 1024-bit DQ + cmd)
    output logic [NUM_HBM-1:0][HBM_WIDTH-1:0]     hbm_dq_o,
    input  wire  [NUM_HBM-1:0][HBM_WIDTH-1:0]     hbm_dq_i,
    output logic [NUM_HBM-1:0][HBM_WIDTH-1:0]     hbm_dq_oe,
    output logic [NUM_HBM-1:0][31:0]              hbm_cmd,
    // ---- PCIe Gen 6 ×16
    output logic [15:0]                           pcie_tx_p,
    output logic [15:0]                           pcie_tx_n,
    input  wire  [15:0]                           pcie_rx_p,
    input  wire  [15:0]                           pcie_rx_n,
    // ---- UCIe D2D to switch-ASIC fabric (4 lanes per cluster)
    output logic [NUM_CLUSTERS-1:0][63:0]         ucie_tx_data,
    output logic [NUM_CLUSTERS-1:0]               ucie_tx_valid,
    input  wire  [NUM_CLUSTERS-1:0]               ucie_tx_ready,
    input  wire  [NUM_CLUSTERS-1:0][63:0]         ucie_rx_data,
    input  wire  [NUM_CLUSTERS-1:0]               ucie_rx_valid,
    output logic [NUM_CLUSTERS-1:0]               ucie_rx_ready,
    // ---- JTAG
    input  wire                                   tck,
    input  wire                                   tms,
    input  wire                                   tdi,
    output logic                                  tdo,
    // ---- BMC APB
    input  wire  [15:0]                           bmc_paddr,
    input  wire                                   bmc_psel,
    input  wire                                   bmc_penable,
    input  wire                                   bmc_pwrite,
    input  wire  [31:0]                           bmc_pwdata,
    output logic [31:0]                           bmc_prdata,
    output logic                                  bmc_pready,
    output logic                                  irq_top
);

    // ---- synchronised resets
    wire por_core_n, por_mem_n, por_aux_n;
    lr_reset_sync u_por_core (.clk(clk_core), .async_rst_n(por_rst_n), .sync_rst_n(por_core_n));
    lr_reset_sync u_por_mem  (.clk(clk_mem),  .async_rst_n(por_rst_n), .sync_rst_n(por_mem_n));
    lr_reset_sync u_por_aux  (.clk(clk_aux),  .async_rst_n(por_rst_n), .sync_rst_n(por_aux_n));

    // ---- 4 compute clusters
    genvar c;
    generate
        for (c = 0; c < NUM_CLUSTERS; c++) begin : g_cluster
            lr_nce_cluster #(.LANES(LANES_PER_CL)) u_cl (
                .clk_core    (clk_core),
                .clk_mem     (clk_mem),
                .rst_n       (por_core_n),
                .ucie_tx_data (ucie_tx_data[c]),
                .ucie_tx_valid(ucie_tx_valid[c]),
                .ucie_tx_ready(ucie_tx_ready[c]),
                .ucie_rx_data (ucie_rx_data[c]),
                .ucie_rx_valid(ucie_rx_valid[c]),
                .ucie_rx_ready(ucie_rx_ready[c])
            );
        end
    endgenerate

    // ---- 4 HBM4 controllers
    generate
        for (c = 0; c < NUM_HBM; c++) begin : g_hbm
            lr_hbm4_ctl #(.WIDTH(HBM_WIDTH)) u_hbm (
                .clk_mem    (clk_mem),
                .clk_phy    (clk_hbm_phy[c]),
                .rst_n      (por_mem_n),
                .dq_o       (hbm_dq_o[c]),
                .dq_i       (hbm_dq_i[c]),
                .dq_oe      (hbm_dq_oe[c]),
                .cmd_o      (hbm_cmd[c])
            );
        end
    endgenerate

    // ---- PCIe Gen 6 host PHY/MAC (vendor IP)
    lr_pcie6_x16 u_pcie (
        .clk_pcie  (clk_pcie),
        .rst_n     (por_core_n),
        .tx_p      (pcie_tx_p),
        .tx_n      (pcie_tx_n),
        .rx_p      (pcie_rx_p),
        .rx_n      (pcie_rx_n)
    );

    // ---- BMC CSR bank
    logic [63:0][31:0] csr_shadow;
    logic [63:0]       csr_wr_stb;
    lr_reg_bank #(.NUM_REGS(64), .ADDR_BITS(16)) u_csr (
        .clk(clk_aux), .rst_n(por_aux_n),
        .paddr(bmc_paddr[15:0]),
        .psel(bmc_psel), .penable(bmc_penable),
        .pwrite(bmc_pwrite), .pwdata(bmc_pwdata),
        .prdata(bmc_prdata), .pready(bmc_pready), .pslverr(),
        .shadow(csr_shadow), .wr_stb(csr_wr_stb),
        .irq_set(32'h0), .irq(irq_top)
    );

    lr_jtag_tap u_jtag (
        .tck(tck), .tms(tms), .tdi(tdi), .tdo(tdo), .trst_n(jtag_rst_n));

endmodule

`default_nettype wire

// -----------------------------------------------------------------------------
// LR-CSW-51T2 — 51.2 Tbps Co-Packaged-Optics switch ASIC top-level
// Copyright (c) 2026 LightRail AI.  All rights reserved.
// -----------------------------------------------------------------------------
// Top-level integration of the 256-lane × 200G PAM4 packet processor:
//   - 16 quadrants (`lr_csw_quad`), each handling 16 lanes
//   - shared 80×80 crossbar fabric (`lr_csw_fabric`)
//   - 32 UCIe-D2D bridges to the on-interposer CPO engines
//   - APB CSR bank, JTAG TAP, BMC sideband, PLL wrappers
// 10 clock domains: CORE (2.0 GHz), MEM (1.5 GHz), SERDES_TX/RX (1.6 GHz),
// UCIE_TX/RX (4.0 GHz), PCIE_AUX (250 MHz), JTAG (50 MHz), REFCLK (156.25 MHz),
// AUX (100 MHz).  4 reset domains (POR, WARM, SOFT, JTAG).
// -----------------------------------------------------------------------------
`default_nettype none

module lr_csw_top #(
    parameter int unsigned NUM_QUADRANTS = 16,
    parameter int unsigned LANES_PER_Q   = 16,
    parameter int unsigned NUM_LANES     = NUM_QUADRANTS * LANES_PER_Q,
    parameter int unsigned NUM_CPO       = 32,
    parameter int unsigned MTU_BYTES     = 9216
) (
    // ---- clocks
    input  wire                                 clk_core,
    input  wire                                 clk_mem,
    input  wire [NUM_QUADRANTS-1:0]             clk_serdes_tx,
    input  wire [NUM_QUADRANTS-1:0]             clk_serdes_rx,
    input  wire                                 clk_ucie_tx,
    input  wire                                 clk_ucie_rx,
    input  wire                                 clk_pcie_aux,
    input  wire                                 clk_jtag,
    input  wire                                 clk_refclk,
    input  wire                                 clk_aux,
    // ---- resets (async, active-low)
    input  wire                                 por_rst_n,
    input  wire                                 warm_rst_n,
    input  wire                                 soft_rst_n,
    input  wire                                 jtag_rst_n,
    // ---- 256 SerDes lanes (Tx+Rx 224 G PAM4)
    output logic [NUM_LANES-1:0]                serdes_tx_p,
    output logic [NUM_LANES-1:0]                serdes_tx_n,
    input  wire  [NUM_LANES-1:0]                serdes_rx_p,
    input  wire  [NUM_LANES-1:0]                serdes_rx_n,
    // ---- UCIe-D2D bus to 32 on-interposer CPO engines
    output logic [NUM_CPO-1:0][63:0]            ucie_tx_data,
    output logic [NUM_CPO-1:0]                  ucie_tx_valid,
    input  wire  [NUM_CPO-1:0]                  ucie_tx_ready,
    input  wire  [NUM_CPO-1:0][63:0]            ucie_rx_data,
    input  wire  [NUM_CPO-1:0]                  ucie_rx_valid,
    output logic [NUM_CPO-1:0]                  ucie_rx_ready,
    // ---- PCIe Gen 5 aux to daughterboard BMC
    inout  wire  [15:0]                         pcie_aux_io,
    // ---- BMC / management (APB)
    input  wire  [15:0]                         bmc_paddr,
    input  wire                                 bmc_psel,
    input  wire                                 bmc_penable,
    input  wire                                 bmc_pwrite,
    input  wire  [31:0]                         bmc_pwdata,
    output logic [31:0]                         bmc_prdata,
    output logic                                bmc_pready,
    // ---- JTAG TAP
    input  wire                                 tck,
    input  wire                                 tms,
    input  wire                                 tdi,
    output logic                                tdo,
    // ---- top-level interrupt to BMC
    output logic                                irq_top
);

    // ---- synchronised resets per domain
    wire por_core_n, por_mem_n, por_aux_n;
    lr_reset_sync u_por_core (.clk(clk_core), .async_rst_n(por_rst_n), .sync_rst_n(por_core_n));
    lr_reset_sync u_por_mem  (.clk(clk_mem),  .async_rst_n(por_rst_n), .sync_rst_n(por_mem_n));
    lr_reset_sync u_por_aux  (.clk(clk_aux),  .async_rst_n(por_rst_n), .sync_rst_n(por_aux_n));

    // ---- 16 quadrants (each owns 16 lanes + ingress queue + egress queue)
    logic [NUM_QUADRANTS-1:0][127:0] fabric_in_data;
    logic [NUM_QUADRANTS-1:0]        fabric_in_valid;
    logic [NUM_QUADRANTS-1:0]        fabric_in_ready;
    logic [NUM_QUADRANTS-1:0][127:0] fabric_out_data;
    logic [NUM_QUADRANTS-1:0]        fabric_out_valid;
    logic [NUM_QUADRANTS-1:0]        fabric_out_ready;

    genvar q;
    generate
        for (q = 0; q < NUM_QUADRANTS; q++) begin : g_quad
            lr_csw_quad #(.LANES(LANES_PER_Q)) u_quad (
                .clk_core      (clk_core),
                .clk_serdes_tx (clk_serdes_tx[q]),
                .clk_serdes_rx (clk_serdes_rx[q]),
                .rst_n         (por_core_n),
                .serdes_tx_p   (serdes_tx_p[(q+1)*LANES_PER_Q-1 -: LANES_PER_Q]),
                .serdes_tx_n   (serdes_tx_n[(q+1)*LANES_PER_Q-1 -: LANES_PER_Q]),
                .serdes_rx_p   (serdes_rx_p[(q+1)*LANES_PER_Q-1 -: LANES_PER_Q]),
                .serdes_rx_n   (serdes_rx_n[(q+1)*LANES_PER_Q-1 -: LANES_PER_Q]),
                .fabric_in_data  (fabric_in_data[q]),
                .fabric_in_valid (fabric_in_valid[q]),
                .fabric_in_ready (fabric_in_ready[q]),
                .fabric_out_data (fabric_out_data[q]),
                .fabric_out_valid(fabric_out_valid[q]),
                .fabric_out_ready(fabric_out_ready[q])
            );
        end
    endgenerate

    // ---- shared 80×80 crossbar fabric
    lr_csw_fabric #(.N_IN(NUM_QUADRANTS), .N_OUT(NUM_QUADRANTS)) u_fabric (
        .clk         (clk_core),
        .rst_n       (por_core_n),
        .in_data     (fabric_in_data),
        .in_valid    (fabric_in_valid),
        .in_ready    (fabric_in_ready),
        .out_data    (fabric_out_data),
        .out_valid   (fabric_out_valid),
        .out_ready   (fabric_out_ready)
    );

    // ---- UCIe bridges (one per CPO engine).  3.2 T per engine at 4.0 GHz x 64 bits.
    generate
        for (q = 0; q < NUM_CPO; q++) begin : g_ucie
            lr_ucie_bridge u_ucie (
                .clk_core     (clk_core),
                .clk_ucie_tx  (clk_ucie_tx),
                .clk_ucie_rx  (clk_ucie_rx),
                .rst_n        (por_core_n),
                .tx_data_o    (ucie_tx_data[q]),
                .tx_valid_o   (ucie_tx_valid[q]),
                .tx_ready_i   (ucie_tx_ready[q]),
                .rx_data_i    (ucie_rx_data[q]),
                .rx_valid_i   (ucie_rx_valid[q]),
                .rx_ready_o   (ucie_rx_ready[q])
            );
        end
    endgenerate

    // ---- APB CSR bank
    logic [63:0][31:0] csr_shadow;
    logic [63:0]       csr_wr_stb;
    lr_reg_bank #(.NUM_REGS(64), .ADDR_BITS(16)) u_csr (
        .clk        (clk_aux),
        .rst_n      (por_aux_n),
        .paddr      (bmc_paddr[15:0]),
        .psel       (bmc_psel),
        .penable    (bmc_penable),
        .pwrite     (bmc_pwrite),
        .pwdata     (bmc_pwdata),
        .prdata     (bmc_prdata),
        .pready     (bmc_pready),
        .pslverr    (),
        .shadow     (csr_shadow),
        .wr_stb     (csr_wr_stb),
        .irq_set    (32'h0),
        .irq        (irq_top)
    );

    // ---- JTAG TAP (IEEE 1149.1 + 1149.6 for AC-coupled SerDes BSDL)
    lr_jtag_tap u_jtag (
        .tck     (tck),
        .tms     (tms),
        .tdi     (tdi),
        .tdo     (tdo),
        .trst_n  (jtag_rst_n)
    );

endmodule

`default_nettype wire

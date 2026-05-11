// -----------------------------------------------------------------------------
// LR-CSW — single quadrant (16 lanes × 200 G PAM4 + parser + queue)
// -----------------------------------------------------------------------------
`default_nettype none

module lr_csw_quad #(
    parameter int unsigned LANES = 16
) (
    input  wire                clk_core,
    input  wire                clk_serdes_tx,
    input  wire                clk_serdes_rx,
    input  wire                rst_n,
    output logic [LANES-1:0]   serdes_tx_p,
    output logic [LANES-1:0]   serdes_tx_n,
    input  wire  [LANES-1:0]   serdes_rx_p,
    input  wire  [LANES-1:0]   serdes_rx_n,
    output logic [127:0]       fabric_in_data,
    output logic               fabric_in_valid,
    input  wire                fabric_in_ready,
    input  wire  [127:0]       fabric_out_data,
    input  wire                fabric_out_valid,
    output logic               fabric_out_ready
);

    // ---- 16 SerDes lane wrappers (vendor-IP black-box)
    logic [LANES-1:0][63:0] rx_lane_data;
    logic [LANES-1:0]       rx_lane_valid;
    logic [LANES-1:0][63:0] tx_lane_data;
    logic [LANES-1:0]       tx_lane_ready;
    genvar l;
    generate
        for (l = 0; l < LANES; l++) begin : g_lane
            lr_serdes_lane u_lane (
                .clk_tx        (clk_serdes_tx),
                .clk_rx        (clk_serdes_rx),
                .rst_n         (rst_n),
                .serdes_tx_p   (serdes_tx_p[l]),
                .serdes_tx_n   (serdes_tx_n[l]),
                .serdes_rx_p   (serdes_rx_p[l]),
                .serdes_rx_n   (serdes_rx_n[l]),
                .tx_data_i     (tx_lane_data[l]),
                .tx_ready_o    (tx_lane_ready[l]),
                .rx_data_o     (rx_lane_data[l]),
                .rx_valid_o    (rx_lane_valid[l])
            );
        end
    endgenerate

    // ---- 64-bit Ethernet parser ➔ 128-bit fabric (placeholder pipeline)
    lr_csw_parser u_parser (
        .clk            (clk_core),
        .rst_n          (rst_n),
        .rx_lane_data   (rx_lane_data),
        .rx_lane_valid  (rx_lane_valid),
        .out_data       (fabric_in_data),
        .out_valid      (fabric_in_valid),
        .out_ready      (fabric_in_ready)
    );

    // ---- output queue + scheduler
    lr_csw_sched u_sched (
        .clk            (clk_core),
        .rst_n          (rst_n),
        .in_data        (fabric_out_data),
        .in_valid       (fabric_out_valid),
        .in_ready       (fabric_out_ready),
        .tx_lane_data   (tx_lane_data),
        .tx_lane_ready  (tx_lane_ready)
    );

endmodule

`default_nettype wire

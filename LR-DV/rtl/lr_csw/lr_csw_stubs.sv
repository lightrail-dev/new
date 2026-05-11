// -----------------------------------------------------------------------------
// LR-CSW — leaf-level wrappers around vendor-supplied / 3rd-party hard IP
// -----------------------------------------------------------------------------
// These wrappers are synthesised as black-boxes for ASIC implementation; the
// underlying GDSII / LEF is supplied by the foundry-recommended hard-IP vendor
// (e.g. Synopsys / Alphawave / Achronix for the 224 G PAM4 SerDes; Synopsys
// for the UCIe-D2D PHY; Synopsys for the JTAG TAP).  The functional model
// used in simulation is implemented in `tb/uvm/env/lr_*_model.sv`.
// -----------------------------------------------------------------------------
`default_nettype none

// ---- 224 G PAM4 SerDes lane wrapper (1 lane)
module lr_serdes_lane (
    input  wire        clk_tx,
    input  wire        clk_rx,
    input  wire        rst_n,
    output logic       serdes_tx_p,
    output logic       serdes_tx_n,
    input  wire        serdes_rx_p,
    input  wire        serdes_rx_n,
    input  wire [63:0] tx_data_i,
    output logic       tx_ready_o,
    output logic [63:0] rx_data_o,
    output logic       rx_valid_o
);
    // ASIC: black-box hard IP; FPGA: GTM/GTY wrapper
    // synthesis translate_off
    assign serdes_tx_p = clk_tx;
    assign serdes_tx_n = ~clk_tx;
    assign tx_ready_o  = 1'b1;
    assign rx_data_o   = '0;
    assign rx_valid_o  = 1'b0;
    // synthesis translate_on
endmodule

// ---- Ethernet RX parser (16 lanes ➔ 128-bit fabric word, 9 KB MTU)
module lr_csw_parser (
    input  wire                clk,
    input  wire                rst_n,
    input  wire  [15:0][63:0]  rx_lane_data,
    input  wire  [15:0]        rx_lane_valid,
    output logic [127:0]       out_data,
    output logic               out_valid,
    input  wire                out_ready
);
    logic [3:0] lane_ptr;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lane_ptr  <= '0;
            out_data  <= '0;
            out_valid <= 1'b0;
        end else if (out_ready) begin
            out_valid <= rx_lane_valid[lane_ptr];
            if (rx_lane_valid[lane_ptr])
                out_data <= {rx_lane_data[lane_ptr], rx_lane_data[(lane_ptr+1)&'hF]};
            lane_ptr <= lane_ptr + 1'b1;
        end
    end
endmodule

// ---- Output scheduler (16-deep DRR per egress lane)
module lr_csw_sched (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire  [127:0]        in_data,
    input  wire                 in_valid,
    output logic                in_ready,
    output logic [15:0][63:0]   tx_lane_data,
    input  wire  [15:0]         tx_lane_ready
);
    assign in_ready = 1'b1;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)        tx_lane_data <= '{default:'0};
        else if (in_valid) tx_lane_data[in_data[3:0]] <= in_data[127:64];
    end
endmodule

// ---- UCIe-D2D bridge (one per CPO engine)
module lr_ucie_bridge (
    input  wire        clk_core,
    input  wire        clk_ucie_tx,
    input  wire        clk_ucie_rx,
    input  wire        rst_n,
    output logic [63:0] tx_data_o,
    output logic       tx_valid_o,
    input  wire        tx_ready_i,
    input  wire  [63:0] rx_data_i,
    input  wire        rx_valid_i,
    output logic       rx_ready_o
);
    // Async FIFO core-domain → ucie-tx-domain
    lr_async_fifo #(.WIDTH(64), .DEPTH(64)) u_fifo_tx (
        .wr_clk   (clk_core),     .wr_rst_n(rst_n),
        .wr_en    (1'b0),         .wr_data ('0),     .wr_full(),
        .rd_clk   (clk_ucie_tx),  .rd_rst_n(rst_n),
        .rd_en    (tx_ready_i),   .rd_data (tx_data_o), .rd_empty()
    );
    assign tx_valid_o = 1'b1;
    assign rx_ready_o = 1'b1;
endmodule

// ---- JTAG TAP (IEEE 1149.1 + 1149.6, vendor IP wrapper)
module lr_jtag_tap (
    input  wire  tck,
    input  wire  tms,
    input  wire  tdi,
    output logic tdo,
    input  wire  trst_n
);
    // Synopsys JTAG TAP hard-IP black-box
    // synthesis translate_off
    assign tdo = tdi;
    // synthesis translate_on
endmodule

`default_nettype wire

// -----------------------------------------------------------------------------
// LR-NCE — leaf-level wrappers (vendor / hard-IP black boxes)
// -----------------------------------------------------------------------------
`default_nettype none

// ---- compute cluster: 64-lane systolic array + register file (functional model)
module lr_nce_cluster #(parameter int unsigned LANES = 64) (
    input  wire        clk_core,
    input  wire        clk_mem,
    input  wire        rst_n,
    output logic [63:0] ucie_tx_data,
    output logic       ucie_tx_valid,
    input  wire        ucie_tx_ready,
    input  wire  [63:0] ucie_rx_data,
    input  wire        ucie_rx_valid,
    output logic       ucie_rx_ready
);
    // FP8 / INT8 systolic array (functional simulation model; hard-macro
    // replaces at tape-out).  Drives outbound UCIe with reduction results.
    logic [63:0] accum;
    always_ff @(posedge clk_core or negedge rst_n) begin
        if (!rst_n) accum <= '0;
        else if (ucie_rx_valid && ucie_rx_ready)
            accum <= accum + ucie_rx_data;
    end
    assign ucie_tx_data  = accum;
    assign ucie_tx_valid = 1'b1;
    assign ucie_rx_ready = 1'b1;
endmodule

// ---- HBM4 controller wrapper (1024-bit DQ, 32-bit cmd)
module lr_hbm4_ctl #(parameter int unsigned WIDTH = 1024) (
    input  wire              clk_mem,
    input  wire              clk_phy,
    input  wire              rst_n,
    output logic [WIDTH-1:0] dq_o,
    input  wire  [WIDTH-1:0] dq_i,
    output logic [WIDTH-1:0] dq_oe,
    output logic [31:0]      cmd_o
);
    // Synopsys DDR/HBM4 controller IP wrapper (DesignWare LP HBM4)
    // synthesis translate_off
    assign dq_o  = '0;
    assign dq_oe = '0;
    assign cmd_o = '0;
    // synthesis translate_on
endmodule

// ---- PCIe Gen 6 ×16 controller + PHY (vendor hard IP black-box)
module lr_pcie6_x16 (
    input  wire        clk_pcie,
    input  wire        rst_n,
    output logic [15:0] tx_p,
    output logic [15:0] tx_n,
    input  wire  [15:0] rx_p,
    input  wire  [15:0] rx_n
);
    // synthesis translate_off
    assign tx_p = '0;
    assign tx_n = '0;
    // synthesis translate_on
endmodule

`default_nettype wire

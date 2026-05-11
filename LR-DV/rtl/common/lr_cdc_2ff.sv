// -----------------------------------------------------------------------------
// LR-DV common — 2-flop synchroniser for single-bit CDC signals
// -----------------------------------------------------------------------------
// Async-assert / sync-deassert downstream reset; 2-stage metastability flop.
// CDC strategy is documented per-instance via `lr_cdc_lib` SDC excerpts.
// -----------------------------------------------------------------------------
`default_nettype none

module lr_cdc_2ff #(
    parameter int unsigned WIDTH = 1
) (
    input  wire              dst_clk,
    input  wire              dst_rst_n,
    input  wire  [WIDTH-1:0] src_data,
    output logic [WIDTH-1:0] dst_data
);
    (* ASYNC_REG = "TRUE" *) logic [WIDTH-1:0] q1;
    (* ASYNC_REG = "TRUE" *) logic [WIDTH-1:0] q2;

    always_ff @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            q1 <= '0;
            q2 <= '0;
        end else begin
            q1 <= src_data;
            q2 <= q1;
        end
    end

    assign dst_data = q2;

endmodule

`default_nettype wire

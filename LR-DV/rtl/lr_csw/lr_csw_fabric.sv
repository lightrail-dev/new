// -----------------------------------------------------------------------------
// LR-CSW — shared crossbar fabric (N_IN × N_OUT, fair round-robin per egress)
// -----------------------------------------------------------------------------
`default_nettype none

module lr_csw_fabric #(
    parameter int unsigned N_IN  = 16,
    parameter int unsigned N_OUT = 16,
    parameter int unsigned W     = 128
) (
    input  wire                       clk,
    input  wire                       rst_n,
    input  wire  [N_IN-1:0][W-1:0]    in_data,
    input  wire  [N_IN-1:0]           in_valid,
    output logic [N_IN-1:0]           in_ready,
    output logic [N_OUT-1:0][W-1:0]   out_data,
    output logic [N_OUT-1:0]          out_valid,
    input  wire  [N_OUT-1:0]          out_ready
);

    // packet header carries destination egress index in low log2(N_OUT) bits
    logic [N_OUT-1:0][N_IN-1:0] req;
    logic [N_OUT-1:0][N_IN-1:0] gnt;

    always_comb begin
        req = '{default:'0};
        for (int i = 0; i < N_IN; i++) begin
            if (in_valid[i]) begin
                req[in_data[i][$clog2(N_OUT)-1:0]][i] = 1'b1;
            end
        end
    end

    // one fair-round-robin arbiter per egress
    genvar o;
    generate
        for (o = 0; o < N_OUT; o++) begin : g_arb
            lr_arb_rr #(.N(N_IN)) u_arb (
                .clk   (clk),
                .rst_n (rst_n),
                .req   (req[o] & {N_IN{out_ready[o]}}),
                .gnt   (gnt[o])
            );
        end
    endgenerate

    // grant ⇒ data forward + in_ready
    always_comb begin
        in_ready  = '0;
        out_valid = '0;
        out_data  = '{default:'0};
        for (int o = 0; o < N_OUT; o++) begin
            for (int i = 0; i < N_IN; i++) begin
                if (gnt[o][i]) begin
                    in_ready[i]  = 1'b1;
                    out_valid[o] = 1'b1;
                    out_data[o]  = in_data[i];
                end
            end
        end
    end

endmodule

`default_nettype wire

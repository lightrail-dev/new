// -----------------------------------------------------------------------------
// LR-DV common — N-way fair round-robin arbiter (one-hot grant)
// -----------------------------------------------------------------------------
// Pointer advances to the position past the last grant on every cycle a grant
// is issued.  Combinational fair grant within a single cycle, latency-free.
// -----------------------------------------------------------------------------
`default_nettype none

module lr_arb_rr #(
    parameter int unsigned N = 8
) (
    input  wire            clk,
    input  wire            rst_n,
    input  wire  [N-1:0]   req,
    output logic [N-1:0]   gnt
);
    logic [$clog2(N)-1:0] ptr;
    logic [2*N-1:0]       rot_req;
    logic [2*N-1:0]       rot_gnt;

    assign rot_req = {req, req} >> ptr;
    // priority-encode lowest set bit in rotated vector
    always_comb begin
        rot_gnt = '0;
        for (int i = 0; i < N; i++)
            if (rot_req[i] && rot_gnt == '0)
                rot_gnt[i] = 1'b1;
    end

    always_comb begin
        gnt = '0;
        for (int i = 0; i < N; i++)
            gnt[(i + ptr) % N] = rot_gnt[i];
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)            ptr <= '0;
        else if (|gnt) begin
            for (int i = 0; i < N; i++)
                if (gnt[i]) ptr <= (i + 1) % N;
        end
    end
endmodule

`default_nettype wire

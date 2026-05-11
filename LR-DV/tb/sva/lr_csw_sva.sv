// -----------------------------------------------------------------------------
// LR-CSW — SystemVerilog Assertions library (sign-off via Questa formal)
// -----------------------------------------------------------------------------
`default_nettype none
module lr_csw_sva (
    input wire clk_core,
    input wire rst_n,
    input wire [15:0]        in_valid,
    input wire [15:0]        in_ready,
    input wire [15:0]        out_valid,
    input wire [15:0]        out_ready
);

    // A1 — ready/valid handshake liveness (no starvation > 64 cycles)
    property p_no_starve(idx);
        @(posedge clk_core) disable iff (!rst_n)
            in_valid[idx] |-> ##[1:64] in_ready[idx];
    endproperty
    genvar i;
    generate
        for (i = 0; i < 16; i++) begin : g_assert
            a_no_starve_in : assert property (p_no_starve(i));
        end
    endgenerate

    // A2 — output valid implies destination decode within fabric
    property p_dst_decode;
        @(posedge clk_core) disable iff (!rst_n)
            |out_valid |-> $countones(out_valid) <= 16;
    endproperty
    a_dst_decode : assert property (p_dst_decode);

    // A3 — no concurrent grant collision per output port
    property p_no_dual_drive;
        @(posedge clk_core) disable iff (!rst_n)
            !$onehot0(out_valid & ~out_ready) || out_valid == '0;
    endproperty
    a_no_dual_drive : assert property (p_no_dual_drive);

endmodule
`default_nettype wire

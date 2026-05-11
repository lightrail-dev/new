// -----------------------------------------------------------------------------
// LR-DV common — asynchronous-assert / synchronous-deassert reset synchroniser
// Copyright (c) 2026 LightRail AI.  All rights reserved.
// -----------------------------------------------------------------------------
// Async-assert / sync-deassert reset synchroniser.  3 stages metastability
// chain.  Active-low reset out for all downstream logic.
// -----------------------------------------------------------------------------
`default_nettype none

module lr_reset_sync #(
    parameter int unsigned STAGES = 3
) (
    input  wire clk,
    input  wire async_rst_n,
    output wire sync_rst_n
);

    (* ASYNC_REG = "TRUE" *) logic [STAGES-1:0] sync_chain;

    always_ff @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n) begin
            sync_chain <= '0;
        end else begin
            sync_chain <= {sync_chain[STAGES-2:0], 1'b1};
        end
    end

    assign sync_rst_n = sync_chain[STAGES-1];

endmodule

`default_nettype wire

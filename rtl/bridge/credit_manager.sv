// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     credit_manager
// DESCRIPTION: Manages credit-based flow control for the inter-chip bridge.
//              Tracks available TX credits and generates credit returns for
//              the RX path. Credit pool depth is parameterizable.
// =========================================================================

module credit_manager #(
    parameter integer MAX_CREDITS  = 16,
    parameter integer CREDIT_WIDTH = 4
)(
    input  wire                     clk,
    input  wire                     rst_n,

    // TX credit interface
    input  wire                     tx_pkt_sent,      // pulse: packet transmitted
    input  wire [CREDIT_WIDTH-1:0]  rx_credit_return,  // credit return from remote
    input  wire                     rx_credit_valid,
    output wire                     tx_credit_avail,   // credits available to send
    output wire [CREDIT_WIDTH-1:0]  tx_credit_count,

    // RX credit interface
    input  wire                     rx_pkt_consumed,   // pulse: packet read from FIFO
    output reg  [CREDIT_WIDTH-1:0]  tx_credit_release, // credits to return to remote
    output reg                      tx_credit_release_valid
);

    reg [CREDIT_WIDTH:0] credit_pool;   // TX credits available
    reg [CREDIT_WIDTH:0] rx_pending;    // RX credits pending return

    assign tx_credit_avail = (credit_pool > 0);
    assign tx_credit_count = credit_pool[CREDIT_WIDTH-1:0];

    // TX credit tracking
    always @(posedge clk) begin
        if (!rst_n) begin
            credit_pool <= MAX_CREDITS[CREDIT_WIDTH:0];
        end else begin
            case ({tx_pkt_sent, rx_credit_valid})
                2'b10:   credit_pool <= credit_pool - 1'b1;
                2'b01:   credit_pool <= credit_pool + rx_credit_return;
                2'b11:   credit_pool <= credit_pool + rx_credit_return - 1'b1;
                default: credit_pool <= credit_pool;
            endcase
        end
    end

    // RX credit accumulation and return
    always @(posedge clk) begin
        if (!rst_n) begin
            rx_pending             <= {(CREDIT_WIDTH+1){1'b0}};
            tx_credit_release       <= {CREDIT_WIDTH{1'b0}};
            tx_credit_release_valid <= 1'b0;
        end else begin
            tx_credit_release_valid <= 1'b0;

            if (rx_pkt_consumed) begin
                rx_pending <= rx_pending + 1'b1;
            end

            // Batch return when we have accumulated enough or on timeout
            if (rx_pending >= 4 || (rx_pending > 0 && rx_pkt_consumed)) begin
                tx_credit_release       <= rx_pending[CREDIT_WIDTH-1:0];
                tx_credit_release_valid <= 1'b1;
                rx_pending              <= rx_pkt_consumed ? 1'b1 : {(CREDIT_WIDTH+1){1'b0}};
            end
        end
    end

endmodule

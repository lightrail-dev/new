// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     bridge_rx
// DESCRIPTION: Receive datapath for the inter-chip bridge. Depacketizes
//              incoming data, validates CRC-32, manages sequence numbers,
//              and signals error/retry when CRC fails.
//
// CLOCK:      brg_clk (500 MHz recovered from forwarded clock)
// =========================================================================

module bridge_rx #(
    parameter integer DATA_WIDTH = 64,
    parameter integer MAX_BEATS  = 8
)(
    input  wire                    clk,
    input  wire                    rst_n,

    // Bridge PHY interface (from remote TX)
    input  wire [DATA_WIDTH-1:0]   brg_data_in,
    input  wire                    brg_valid_in,
    input  wire                    brg_last_in,

    // Internal bus interface (to host/core)
    output reg  [7:0]              rx_pkt_type,
    output reg  [31:0]             rx_addr,
    output reg  [DATA_WIDTH-1:0]   rx_data,
    output reg                     rx_data_valid,
    output reg                     rx_data_last,
    output reg                     rx_pkt_valid,   // full packet received & CRC OK

    // CRC engine interface
    output wire                    crc_init,
    output wire                    crc_valid,
    output wire [DATA_WIDTH-1:0]   crc_data,
    input  wire [31:0]             crc_result,

    // Error / retry signaling
    output reg                     crc_error,       // pulse on CRC mismatch
    output reg  [3:0]              error_seq,       // sequence that failed
    output reg                     ack_valid,       // pulse: packet OK
    output reg  [3:0]              ack_seq,         // sequence acknowledged

    // Packet consumed (for credit return)
    output wire                    pkt_consumed
);

    localparam [2:0] ST_IDLE   = 3'd0,
                     ST_HEADER = 3'd1,
                     ST_ADDR   = 3'd2,
                     ST_DATA   = 3'd3,
                     ST_CRC    = 3'd4;

    reg [2:0]  state;
    reg [3:0]  beat_cnt;
    reg [2:0]  rx_seq;
    reg [31:0] received_crc;
    reg        pkt_done;

    assign crc_init = (state == ST_IDLE) && brg_valid_in;
    assign crc_valid = brg_valid_in && (state != ST_CRC) && (state != ST_IDLE);
    assign crc_data  = brg_data_in;
    assign pkt_consumed = pkt_done;

    always @(posedge clk) begin
        if (!rst_n) begin
            state        <= ST_IDLE;
            rx_pkt_type  <= 8'd0;
            rx_addr      <= 32'd0;
            rx_data      <= {DATA_WIDTH{1'b0}};
            rx_data_valid <= 1'b0;
            rx_data_last <= 1'b0;
            rx_pkt_valid <= 1'b0;
            crc_error    <= 1'b0;
            error_seq    <= 4'd0;
            ack_valid    <= 1'b0;
            ack_seq      <= 4'd0;
            beat_cnt     <= 4'd0;
            rx_seq       <= 3'd0;
            received_crc <= 32'd0;
            pkt_done     <= 1'b0;
        end else begin
            rx_data_valid <= 1'b0;
            rx_data_last  <= 1'b0;
            rx_pkt_valid  <= 1'b0;
            crc_error     <= 1'b0;
            ack_valid     <= 1'b0;
            pkt_done      <= 1'b0;

            case (state)
                ST_IDLE: begin
                    if (brg_valid_in) begin
                        state <= ST_HEADER;
                    end
                end

                ST_HEADER: begin
                    if (brg_valid_in) begin
                        rx_pkt_type <= brg_data_in[7:0];
                        rx_seq      <= brg_data_in[2:0];
                        state       <= ST_ADDR;
                    end
                end

                ST_ADDR: begin
                    if (brg_valid_in) begin
                        rx_addr  <= brg_data_in[31:0];
                        beat_cnt <= 4'd0;
                        state    <= brg_last_in ? ST_CRC : ST_DATA;
                    end
                end

                ST_DATA: begin
                    if (brg_valid_in) begin
                        rx_data       <= brg_data_in;
                        rx_data_valid <= 1'b1;
                        beat_cnt      <= beat_cnt + 4'd1;
                        if (brg_last_in) begin
                            state <= ST_CRC;
                        end
                    end
                end

                ST_CRC: begin
                    if (brg_valid_in) begin
                        received_crc <= brg_data_in[31:0];
                        // Compare CRC: the engine has been computing over hdr+addr+data
                        if (crc_result == brg_data_in[31:0]) begin
                            rx_pkt_valid <= 1'b1;
                            rx_data_last <= 1'b1;
                            ack_valid    <= 1'b1;
                            ack_seq      <= {1'b0, rx_seq};
                            pkt_done     <= 1'b1;
                        end else begin
                            crc_error <= 1'b1;
                            error_seq <= {1'b0, rx_seq};
                        end
                        state <= ST_IDLE;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule

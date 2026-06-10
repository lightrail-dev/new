// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     retry_buffer
// DESCRIPTION: Circular buffer storing transmitted packets for automatic
//              retransmission on CRC error. Packets are freed when
//              acknowledged by the receiver. Depth = MAX_CREDITS to
//              guarantee space for all in-flight packets.
// =========================================================================

module retry_buffer #(
    parameter integer DATA_WIDTH   = 64,
    parameter integer PKT_BEATS    = 10,   // max beats per packet (hdr+addr+8data+crc)
    parameter integer BUFFER_DEPTH = 16
)(
    input  wire                     clk,
    input  wire                     rst_n,

    // Store interface (from TX path)
    input  wire                     store_valid,
    input  wire [DATA_WIDTH-1:0]    store_data,
    input  wire                     store_eop,   // end of packet
    output wire                     store_ready,

    // Acknowledge interface
    input  wire                     ack_valid,   // remote acknowledged packet
    input  wire [3:0]               ack_seq,     // sequence number acknowledged

    // Retry interface
    input  wire                     retry_req,   // CRC error, retransmit
    input  wire [3:0]               retry_seq,   // sequence to retransmit from
    output reg                      retry_valid,
    output reg  [DATA_WIDTH-1:0]    retry_data,
    output reg                      retry_eop,
    input  wire                     retry_ready
);

    localparam TOTAL_WORDS = BUFFER_DEPTH * PKT_BEATS;
    localparam ADDR_W      = $clog2(TOTAL_WORDS);

    reg [DATA_WIDTH-1:0] mem [0:TOTAL_WORDS-1];
    reg [ADDR_W-1:0]     pkt_start [0:BUFFER_DEPTH-1];
    reg [ADDR_W-1:0]     pkt_end   [0:BUFFER_DEPTH-1];

    reg [ADDR_W-1:0] wr_ptr;
    reg [3:0]        wr_seq;
    reg [3:0]        rd_seq;    // oldest unacknowledged
    reg              replaying;
    reg [ADDR_W-1:0] replay_ptr;
    reg [ADDR_W-1:0] replay_end;

    wire buffer_has_space = ((wr_seq - rd_seq) < BUFFER_DEPTH[3:0]);
    assign store_ready = buffer_has_space && !replaying;

    // Store path
    always @(posedge clk) begin
        if (!rst_n) begin
            wr_ptr <= {ADDR_W{1'b0}};
            wr_seq <= 4'd0;
        end else if (store_valid && store_ready) begin
            mem[wr_ptr] <= store_data;
            if (store_eop) begin
                pkt_end[wr_seq[3:0]]   <= wr_ptr;
                wr_seq                 <= wr_seq + 4'd1;
                wr_ptr                 <= wr_ptr + 1'b1;
            end else begin
                if (wr_ptr == pkt_start[wr_seq[3:0]] || store_valid) begin
                    // first beat sets start
                end
                wr_ptr <= wr_ptr + 1'b1;
            end
        end
    end

    // Track packet start addresses
    always @(posedge clk) begin
        if (!rst_n) begin
            integer i;
            for (i = 0; i < BUFFER_DEPTH; i = i + 1)
                pkt_start[i] <= {ADDR_W{1'b0}};
        end else if (store_valid && store_ready && store_eop) begin
            pkt_start[wr_seq + 4'd1] <= wr_ptr + 1'b1;
        end
    end

    // Acknowledge path
    always @(posedge clk) begin
        if (!rst_n) begin
            rd_seq <= 4'd0;
        end else if (ack_valid) begin
            rd_seq <= ack_seq + 4'd1;
        end
    end

    // Replay path
    always @(posedge clk) begin
        if (!rst_n) begin
            replaying  <= 1'b0;
            replay_ptr <= {ADDR_W{1'b0}};
            replay_end <= {ADDR_W{1'b0}};
            retry_valid <= 1'b0;
            retry_data  <= {DATA_WIDTH{1'b0}};
            retry_eop   <= 1'b0;
        end else if (retry_req && !replaying) begin
            replaying  <= 1'b1;
            replay_ptr <= pkt_start[retry_seq];
            replay_end <= wr_ptr;
            retry_valid <= 1'b0;
        end else if (replaying) begin
            if (retry_ready || !retry_valid) begin
                retry_data  <= mem[replay_ptr];
                retry_valid <= 1'b1;
                retry_eop   <= (replay_ptr == pkt_end[retry_seq]);
                if (replay_ptr == replay_end) begin
                    replaying <= 1'b0;
                end else begin
                    replay_ptr <= replay_ptr + 1'b1;
                end
            end
        end else begin
            retry_valid <= 1'b0;
        end
    end

endmodule

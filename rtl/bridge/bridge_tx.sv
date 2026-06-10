// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     bridge_tx
// DESCRIPTION: Transmit datapath for the inter-chip bridge. Packetizes
//              data from the internal bus, appends CRC-32, manages
//              sequence numbers, and interfaces with the credit manager
//              and retry buffer.
//
// CLOCK:      brg_clk (500 MHz source-synchronous forwarded clock)
// =========================================================================

module bridge_tx #(
    parameter integer DATA_WIDTH = 64,
    parameter integer MAX_BEATS  = 8
)(
    input  wire                    clk,
    input  wire                    rst_n,

    // Internal bus interface (from host/core)
    input  wire                    tx_req,
    input  wire [7:0]              tx_pkt_type,
    input  wire [31:0]             tx_addr,
    input  wire [DATA_WIDTH-1:0]   tx_data,
    input  wire                    tx_data_valid,
    input  wire                    tx_data_last,
    output wire                    tx_ready,

    // Bridge PHY interface
    output reg  [DATA_WIDTH-1:0]   brg_data_out,
    output reg                     brg_valid_out,
    output reg                     brg_last_out,

    // CRC engine interface
    output wire                    crc_init,
    output wire                    crc_valid,
    output wire [DATA_WIDTH-1:0]   crc_data,
    input  wire [31:0]             crc_result,

    // Credit manager
    input  wire                    credit_avail,
    output wire                    pkt_sent,

    // Retry buffer store
    output wire                    store_valid,
    output wire [DATA_WIDTH-1:0]   store_data,
    output wire                    store_eop,
    input  wire                    store_ready,

    // Sequence tracking
    output reg  [3:0]              tx_seq_num
);

    localparam [2:0] ST_IDLE   = 3'd0,
                     ST_HEADER = 3'd1,
                     ST_ADDR   = 3'd2,
                     ST_DATA   = 3'd3,
                     ST_CRC    = 3'd4;

    reg [2:0]  state;
    reg [3:0]  beat_cnt;
    reg [7:0]  pkt_type_r;
    reg [31:0] addr_r;

    assign tx_ready    = (state == ST_IDLE) && credit_avail && store_ready;
    assign pkt_sent    = (state == ST_CRC) && brg_valid_out;
    assign crc_init    = (state == ST_IDLE) && tx_req;
    assign store_valid = brg_valid_out;
    assign store_data  = brg_data_out;
    assign store_eop   = brg_last_out;

    // CRC feeds on every beat except CRC beat itself
    assign crc_valid   = brg_valid_out && (state != ST_CRC);
    assign crc_data    = brg_data_out;

    always @(posedge clk) begin
        if (!rst_n) begin
            state         <= ST_IDLE;
            brg_data_out  <= {DATA_WIDTH{1'b0}};
            brg_valid_out <= 1'b0;
            brg_last_out  <= 1'b0;
            beat_cnt      <= 4'd0;
            tx_seq_num    <= 4'd0;
            pkt_type_r    <= 8'd0;
            addr_r        <= 32'd0;
        end else begin
            brg_valid_out <= 1'b0;
            brg_last_out  <= 1'b0;

            case (state)
                ST_IDLE: begin
                    if (tx_req && credit_avail && store_ready) begin
                        pkt_type_r <= tx_pkt_type;
                        addr_r     <= tx_addr;
                        state      <= ST_HEADER;
                    end
                end

                ST_HEADER: begin
                    brg_data_out  <= {{(DATA_WIDTH-8){1'b0}},
                                      pkt_type_r[7:3], tx_seq_num[2:0]};
                    brg_valid_out <= 1'b1;
                    state         <= ST_ADDR;
                end

                ST_ADDR: begin
                    brg_data_out  <= {{(DATA_WIDTH-32){1'b0}}, addr_r};
                    brg_valid_out <= 1'b1;
                    beat_cnt      <= 4'd0;
                    state         <= tx_data_valid ? ST_DATA : ST_CRC;
                end

                ST_DATA: begin
                    if (tx_data_valid) begin
                        brg_data_out  <= tx_data;
                        brg_valid_out <= 1'b1;
                        beat_cnt      <= beat_cnt + 4'd1;
                        if (tx_data_last || beat_cnt == MAX_BEATS[3:0] - 4'd1) begin
                            state <= ST_CRC;
                        end
                    end
                end

                ST_CRC: begin
                    brg_data_out  <= {{(DATA_WIDTH-32){1'b0}}, crc_result};
                    brg_valid_out <= 1'b1;
                    brg_last_out  <= 1'b1;
                    tx_seq_num    <= tx_seq_num + 4'd1;
                    state         <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule

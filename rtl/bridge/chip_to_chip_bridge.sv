// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     chip_to_chip_bridge
// DESCRIPTION: Top-level inter-chip bridge controller. Implements an
//              ultra-low-latency packetized source-synchronous interface
//              with credit-based flow control, CRC-32 error detection,
//              and automatic retransmission.
//
// PROTOCOL:   Custom point-to-point, 64-bit DDR, 500 MHz forwarded clock.
// BANDWIDTH:  64 Gbps raw (58 Gbps usable).
//
// FEATURES:
//   - Credit-based flow control (16-deep)
//   - CRC-32 integrity on every packet
//   - Automatic retry on CRC error (retry buffer holds 16 packets)
//   - Source-synchronous forwarded clock
//   - Configurable as Node A or Node B via NODE_ID strap
// =========================================================================

module chip_to_chip_bridge #(
    parameter integer DATA_WIDTH   = 64,
    parameter integer MAX_CREDITS  = 16,
    parameter integer MAX_BEATS    = 8,
    parameter integer CREDIT_WIDTH = 4
)(
    // System
    input  wire                     clk,          // 500 MHz bridge clock
    input  wire                     rst_n,

    // Configuration
    input  wire                     node_id,      // 0 = Node A, 1 = Node B

    // Internal bus interface (upstream: host/core side)
    input  wire                     tx_req,
    input  wire [7:0]               tx_pkt_type,
    input  wire [31:0]              tx_addr,
    input  wire [DATA_WIDTH-1:0]    tx_data,
    input  wire                     tx_data_valid,
    input  wire                     tx_data_last,
    output wire                     tx_ready,

    output wire [7:0]               rx_pkt_type,
    output wire [31:0]              rx_addr,
    output wire [DATA_WIDTH-1:0]    rx_data,
    output wire                     rx_data_valid,
    output wire                     rx_data_last,
    output wire                     rx_pkt_valid,

    // Bridge PHY pins (directly to PCB traces)
    output wire [DATA_WIDTH-1:0]    brg_data_out,
    output wire                     brg_valid_out,
    input  wire [DATA_WIDTH-1:0]    brg_data_in,
    input  wire                     brg_valid_in,
    input  wire                     brg_last_in,
    output wire                     brg_last_out,

    // Credit return channel
    output wire [CREDIT_WIDTH-1:0]  brg_credit_out,
    output wire                     brg_credit_out_valid,
    input  wire [CREDIT_WIDTH-1:0]  brg_credit_in,
    input  wire                     brg_credit_in_valid,

    // Error / ACK channel
    input  wire                     brg_err_in,
    output wire                     brg_ack_out,

    // Status / statistics
    output wire [31:0]              stat_tx_packets,
    output wire [31:0]              stat_rx_packets,
    output wire [31:0]              stat_crc_errors,
    output wire                     link_up
);

    // ---- Statistics Counters ----
    reg [31:0] tx_pkt_cnt;
    reg [31:0] rx_pkt_cnt;
    reg [31:0] crc_err_cnt;
    reg        link_up_r;

    assign stat_tx_packets = tx_pkt_cnt;
    assign stat_rx_packets = rx_pkt_cnt;
    assign stat_crc_errors = crc_err_cnt;
    assign link_up         = link_up_r;

    // ---- Internal Wires ----
    wire        tx_credit_avail;
    wire [3:0]  tx_credit_count;
    wire        tx_pkt_sent;
    wire [3:0]  tx_seq_num;

    wire        rx_crc_error;
    wire [3:0]  rx_error_seq;
    wire        rx_ack_valid;
    wire [3:0]  rx_ack_seq;
    wire        rx_pkt_consumed;

    // TX CRC wires
    wire        tx_crc_init;
    wire        tx_crc_valid;
    wire [DATA_WIDTH-1:0] tx_crc_data;
    wire [31:0] tx_crc_result;

    // RX CRC wires
    wire        rx_crc_init;
    wire        rx_crc_valid;
    wire [DATA_WIDTH-1:0] rx_crc_data;
    wire [31:0] rx_crc_result;

    // Retry buffer wires
    wire        store_valid;
    wire [DATA_WIDTH-1:0] store_data;
    wire        store_eop;
    wire        store_ready;

    wire        retry_valid;
    wire [DATA_WIDTH-1:0] retry_data;
    wire        retry_eop;
    wire        retry_ready = 1'b1; // always accept replays

    // ---- TX CRC Engine ----
    crc32_engine #(.DATA_WIDTH(DATA_WIDTH)) u_tx_crc (
        .clk      (clk),
        .rst_n    (rst_n),
        .init     (tx_crc_init),
        .valid    (tx_crc_valid),
        .data_in  (tx_crc_data),
        .crc_out  (tx_crc_result),
        .crc_valid()
    );

    // ---- RX CRC Engine ----
    crc32_engine #(.DATA_WIDTH(DATA_WIDTH)) u_rx_crc (
        .clk      (clk),
        .rst_n    (rst_n),
        .init     (rx_crc_init),
        .valid    (rx_crc_valid),
        .data_in  (rx_crc_data),
        .crc_out  (rx_crc_result),
        .crc_valid()
    );

    // ---- TX Datapath ----
    bridge_tx #(
        .DATA_WIDTH(DATA_WIDTH),
        .MAX_BEATS (MAX_BEATS)
    ) u_tx (
        .clk           (clk),
        .rst_n         (rst_n),
        .tx_req        (tx_req),
        .tx_pkt_type   (tx_pkt_type),
        .tx_addr       (tx_addr),
        .tx_data       (tx_data),
        .tx_data_valid (tx_data_valid),
        .tx_data_last  (tx_data_last),
        .tx_ready      (tx_ready),
        .brg_data_out  (brg_data_out),
        .brg_valid_out (brg_valid_out),
        .brg_last_out  (brg_last_out),
        .crc_init      (tx_crc_init),
        .crc_valid     (tx_crc_valid),
        .crc_data      (tx_crc_data),
        .crc_result    (tx_crc_result),
        .credit_avail  (tx_credit_avail),
        .pkt_sent      (tx_pkt_sent),
        .store_valid   (store_valid),
        .store_data    (store_data),
        .store_eop     (store_eop),
        .store_ready   (store_ready),
        .tx_seq_num    (tx_seq_num)
    );

    // ---- RX Datapath ----
    bridge_rx #(
        .DATA_WIDTH(DATA_WIDTH),
        .MAX_BEATS (MAX_BEATS)
    ) u_rx (
        .clk           (clk),
        .rst_n         (rst_n),
        .brg_data_in   (brg_data_in),
        .brg_valid_in  (brg_valid_in),
        .brg_last_in   (brg_last_in),
        .rx_pkt_type   (rx_pkt_type),
        .rx_addr       (rx_addr),
        .rx_data       (rx_data),
        .rx_data_valid (rx_data_valid),
        .rx_data_last  (rx_data_last),
        .rx_pkt_valid  (rx_pkt_valid),
        .crc_init      (rx_crc_init),
        .crc_valid     (rx_crc_valid),
        .crc_data      (rx_crc_data),
        .crc_result    (rx_crc_result),
        .crc_error     (rx_crc_error),
        .error_seq     (rx_error_seq),
        .ack_valid     (rx_ack_valid),
        .ack_seq       (rx_ack_seq),
        .pkt_consumed  (rx_pkt_consumed)
    );

    // ---- Credit Manager ----
    credit_manager #(
        .MAX_CREDITS (MAX_CREDITS),
        .CREDIT_WIDTH(CREDIT_WIDTH)
    ) u_credits (
        .clk                    (clk),
        .rst_n                  (rst_n),
        .tx_pkt_sent            (tx_pkt_sent),
        .rx_credit_return       (brg_credit_in),
        .rx_credit_valid        (brg_credit_in_valid),
        .tx_credit_avail        (tx_credit_avail),
        .tx_credit_count        (tx_credit_count),
        .rx_pkt_consumed        (rx_pkt_consumed),
        .tx_credit_release      (brg_credit_out),
        .tx_credit_release_valid(brg_credit_out_valid)
    );

    // ---- Retry Buffer ----
    retry_buffer #(
        .DATA_WIDTH  (DATA_WIDTH),
        .PKT_BEATS   (MAX_BEATS + 2),
        .BUFFER_DEPTH(MAX_CREDITS)
    ) u_retry (
        .clk         (clk),
        .rst_n       (rst_n),
        .store_valid (store_valid),
        .store_data  (store_data),
        .store_eop   (store_eop),
        .store_ready (store_ready),
        .ack_valid   (rx_ack_valid),
        .ack_seq     (rx_ack_seq),
        .retry_req   (brg_err_in),
        .retry_seq   (rx_error_seq),
        .retry_valid (retry_valid),
        .retry_data  (retry_data),
        .retry_eop   (retry_eop),
        .retry_ready (retry_ready)
    );

    // ACK output = RX ack
    assign brg_ack_out = rx_ack_valid;

    // ---- Link-Up Detection ----
    reg [7:0] heartbeat_cnt;

    always @(posedge clk) begin
        if (!rst_n) begin
            link_up_r     <= 1'b0;
            heartbeat_cnt <= 8'd0;
        end else begin
            if (brg_valid_in || rx_pkt_valid) begin
                link_up_r     <= 1'b1;
                heartbeat_cnt <= 8'd0;
            end else if (heartbeat_cnt < 8'hFF) begin
                heartbeat_cnt <= heartbeat_cnt + 8'd1;
            end else begin
                link_up_r <= 1'b0;
            end
        end
    end

    // ---- Statistics ----
    always @(posedge clk) begin
        if (!rst_n) begin
            tx_pkt_cnt  <= 32'd0;
            rx_pkt_cnt  <= 32'd0;
            crc_err_cnt <= 32'd0;
        end else begin
            if (tx_pkt_sent)   tx_pkt_cnt  <= tx_pkt_cnt  + 32'd1;
            if (rx_pkt_valid)  rx_pkt_cnt  <= rx_pkt_cnt  + 32'd1;
            if (rx_crc_error)  crc_err_cnt <= crc_err_cnt + 32'd1;
        end
    end

endmodule

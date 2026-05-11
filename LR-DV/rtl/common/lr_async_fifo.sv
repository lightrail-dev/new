// -----------------------------------------------------------------------------
// LR-DV common — Gray-coded asynchronous FIFO for multi-bit CDC bus transport
// -----------------------------------------------------------------------------
// Power-of-two depth, dual-port memory, binary↔Gray pointer conversion,
// pointer synchronisers on opposite clock domains.  Used wherever a multi-bit
// CDC bus crosses a Questa-CDC verified domain boundary.
// -----------------------------------------------------------------------------
`default_nettype none

module lr_async_fifo #(
    parameter int unsigned WIDTH = 64,
    parameter int unsigned DEPTH = 16,                 // must be power of 2
    parameter int unsigned ADDR  = $clog2(DEPTH)
) (
    // write clock domain
    input  wire              wr_clk,
    input  wire              wr_rst_n,
    input  wire              wr_en,
    input  wire  [WIDTH-1:0] wr_data,
    output logic             wr_full,
    // read clock domain
    input  wire              rd_clk,
    input  wire              rd_rst_n,
    input  wire              rd_en,
    output logic [WIDTH-1:0] rd_data,
    output logic             rd_empty
);

    logic [WIDTH-1:0] mem [DEPTH-1:0];

    // ---- pointers
    logic [ADDR:0] wr_ptr_bin, wr_ptr_gray;
    logic [ADDR:0] rd_ptr_bin, rd_ptr_gray;
    logic [ADDR:0] wr_ptr_gray_rd, rd_ptr_gray_wr;

    // ---- write side
    always_ff @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            wr_ptr_bin  <= '0;
            wr_ptr_gray <= '0;
        end else if (wr_en && !wr_full) begin
            mem[wr_ptr_bin[ADDR-1:0]] <= wr_data;
            wr_ptr_bin  <= wr_ptr_bin + 1'b1;
            wr_ptr_gray <= (wr_ptr_bin + 1'b1) ^ ((wr_ptr_bin + 1'b1) >> 1);
        end
    end
    assign wr_full = (wr_ptr_gray ==
        { ~rd_ptr_gray_wr[ADDR:ADDR-1], rd_ptr_gray_wr[ADDR-2:0] });

    // ---- read side
    always_ff @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_ptr_bin  <= '0;
            rd_ptr_gray <= '0;
        end else if (rd_en && !rd_empty) begin
            rd_ptr_bin  <= rd_ptr_bin + 1'b1;
            rd_ptr_gray <= (rd_ptr_bin + 1'b1) ^ ((rd_ptr_bin + 1'b1) >> 1);
        end
    end
    assign rd_empty = (rd_ptr_gray == wr_ptr_gray_rd);
    assign rd_data  = mem[rd_ptr_bin[ADDR-1:0]];

    // ---- Gray-pointer CDC synchronisers (covered by lr_cdc_2ff)
    lr_cdc_2ff #(.WIDTH(ADDR+1)) u_wr2rd (
        .dst_clk(rd_clk), .dst_rst_n(rd_rst_n),
        .src_data(wr_ptr_gray), .dst_data(wr_ptr_gray_rd));
    lr_cdc_2ff #(.WIDTH(ADDR+1)) u_rd2wr (
        .dst_clk(wr_clk), .dst_rst_n(wr_rst_n),
        .src_data(rd_ptr_gray), .dst_data(rd_ptr_gray_wr));

endmodule

`default_nettype wire

// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     crc32_engine
// DESCRIPTION: Parameterizable CRC-32 (IEEE 802.3) computation engine.
//              Supports 8/32/64-bit data widths with single-cycle throughput.
//              Used by the inter-chip bridge for packet integrity checking.
//
// POLYNOMIAL: 0x04C11DB7 (IEEE 802.3 / Ethernet)
// =========================================================================

module crc32_engine #(
    parameter integer DATA_WIDTH = 64
)(
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    init,       // pulse to reset CRC to seed
    input  wire                    valid,      // input data valid
    input  wire [DATA_WIDTH-1:0]   data_in,
    output wire [31:0]             crc_out,    // current CRC value
    output wire                    crc_valid   // CRC output is valid
);

    reg [31:0] crc_reg;
    reg        out_valid;

    // Bit-serial CRC with full unroll for single-cycle computation
    function automatic [31:0] crc_next;
        input [31:0] crc_prev;
        input [DATA_WIDTH-1:0] data;
        reg [31:0] c;
        integer i;
        begin
            c = crc_prev;
            for (i = DATA_WIDTH - 1; i >= 0; i = i - 1) begin
                if (c[31] ^ data[i]) begin
                    c = {c[30:0], 1'b0} ^ 32'h04C11DB7;
                end else begin
                    c = {c[30:0], 1'b0};
                end
            end
            crc_next = c;
        end
    endfunction

    always @(posedge clk) begin
        if (!rst_n) begin
            crc_reg   <= 32'hFFFFFFFF;
            out_valid <= 1'b0;
        end else if (init) begin
            crc_reg   <= 32'hFFFFFFFF;
            out_valid <= 1'b0;
        end else if (valid) begin
            crc_reg   <= crc_next(crc_reg, data_in);
            out_valid <= 1'b1;
        end else begin
            out_valid <= 1'b0;
        end
    end

    assign crc_out   = ~crc_reg;  // complement per IEEE 802.3
    assign crc_valid = out_valid;

endmodule

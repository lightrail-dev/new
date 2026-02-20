lightrail.v
// LightRail AI MVP NPU Model
module LightRail_Spiking_NPU (
    input wire clk, reset_n,
    input wire [31:0] data_in,
    input wire enable_laser,
    output reg spike_out,
    output reg [31:0] out_val
);
    reg [31:0] accumulation;
    parameter THRESHOLD = 32'h0000_FFFF;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            accumulation <= 32'b0;
            spike_out <= 1'b0;
            out_val <= 32'b0;
        end else if (enable_laser) begin
            if (data_in > 0) begin
                accumulation <= accumulation + data_in;
                if (accumulation >= THRESHOLD) begin
                    spike_out <= 1'b1;
                    out_val <= accumulation;
                    accumulation <= 32'b0;
                end else begin
                    spike_out <= 1'b0;
                end
            end
        end
    end
endmodule
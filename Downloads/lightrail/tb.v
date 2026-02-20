`timescale 1ns/1ps

module tb;
    reg clk;
    reg reset_n;
    reg enable_laser;
    reg [31:0] data_in;
    wire spike_out;
    wire [31:0] out_val;
    
    LightRail_Spiking_NPU dut (
        .clk(clk), 
        .reset_n(reset_n), 
        .data_in(data_in),
        .enable_laser(enable_laser), 
        .spike_out(spike_out), 
        .out_val(out_val)
    );
    
    initial begin 
        clk = 0; 
        forever #5 clk = ~clk; 
    end
    
    initial begin
        reset_n = 0; 
        enable_laser = 0; 
        data_in = 0;
        #20 reset_n = 1; 
        enable_laser = 1;
        #10 data_in = 32'd20000;
        #10 data_in = 32'd20000;
        #10 data_in = 32'd20000;
        #10 data_in = 0;
        #100 $finish;
    end
endmodule
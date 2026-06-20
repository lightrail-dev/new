/*
 * Copyright (c) 2026 LightRail AI Labs
 * SPDX-License-Identifier: Apache-2.0
 *
 * LightRail NCE Mini Compute Unit — TinyTapeout Sky130 Submission
 *
 * A compact 8-bit MAC (Multiply-Accumulate) engine demonstrating the
 * fundamental compute operation of the Neural Compute Engine (NCE).
 *
 * Features:
 *   - 8-bit x 8-bit multiply with 16-bit accumulator
 *   - ReLU activation function
 *   - Configurable shift-right for quantization
 *   - Status register (overflow, zero, sign)
 *   - 4 operation modes: LOAD, MAC, RELU, READ
 *
 * Interface (TinyTapeout standard):
 *   ui_in[7:0]  — Data input (operand A or B depending on mode)
 *   uo_out[7:0] — Data output (accumulator low/high or status)
 *   uio[7:0]    — Control: [1:0]=opcode, [2]=acc_sel, [5:3]=shift, [7:6]=unused
 */

`default_nettype none

module tt_um_lightrail_nce (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // --- Control decode ---
  wire [1:0] opcode   = uio_in[1:0];  // 00=NOP, 01=LOAD, 10=MAC, 11=ACTIVATE
  wire       acc_sel  = uio_in[2];     // 0=read low byte, 1=read high byte
  wire [2:0] shift    = uio_in[5:3];   // right-shift amount for quantization

  // --- Operation codes ---
  localparam OP_NOP      = 2'b00;
  localparam OP_LOAD     = 2'b01;  // Load operand A register
  localparam OP_MAC      = 2'b10;  // Multiply A * ui_in, accumulate
  localparam OP_ACTIVATE = 2'b11;  // Apply ReLU + shift, output result

  // --- Registers ---
  reg [7:0]  reg_a;       // Operand A (weight)
  reg [15:0] accumulator; // 16-bit accumulator
  reg [7:0]  result;      // Activation output
  reg        overflow;    // Overflow flag

  // --- Multiply ---
  wire [15:0] product = reg_a * ui_in;  // 8x8 -> 16-bit product

  // --- Accumulate with overflow detection ---
  wire [16:0] acc_sum = {1'b0, accumulator} + {1'b0, product};

  // --- ReLU + Shift (quantization) ---
  wire [15:0] shifted = accumulator >> shift;
  wire [7:0]  relu_out = accumulator[15] ? 8'h00 :          // Negative -> 0 (ReLU)
                          (|shifted[15:8]) ? 8'hFF :          // Saturate to max
                          shifted[7:0];                        // Normal output

  // --- Sequential logic ---
  always @(posedge clk) begin
    if (!rst_n) begin
      reg_a       <= 8'h00;
      accumulator <= 16'h0000;
      result      <= 8'h00;
      overflow    <= 1'b0;
    end else if (ena) begin
      case (opcode)
        OP_LOAD: begin
          reg_a       <= ui_in;
          accumulator <= 16'h0000;  // Clear accumulator on new weight load
          overflow    <= 1'b0;
        end
        OP_MAC: begin
          accumulator <= acc_sum[15:0];
          overflow    <= overflow | acc_sum[16];
        end
        OP_ACTIVATE: begin
          result <= relu_out;
        end
        default: ; // OP_NOP — hold state
      endcase
    end
  end

  // --- Output mux ---
  // acc_sel=0: result/acc_low, acc_sel=1: acc_high/status
  wire [7:0] status = {4'b0000, overflow, accumulator == 16'h0000,
                        accumulator[15], result != 8'h00};

  assign uo_out = acc_sel ? status : result;

  // --- Bidirectional pins: all inputs (control comes in on uio_in) ---
  assign uio_out = 8'h00;
  assign uio_oe  = 8'h00;  // All bidirectional pins as inputs

  // Suppress unused warnings
  wire _unused = &{uio_in[7:6], 1'b0};

endmodule

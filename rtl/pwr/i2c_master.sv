// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     i2c_master
// DESCRIPTION: Simple I2C/PMBus master controller for interfacing with
//              ISL69260 VRM controllers and on-board thermal sensors.
//              Supports standard-mode (100 kHz) and fast-mode (400 kHz).
//
// INTERFACE:  Register-based command/status with auto-generated
//             START/STOP/ACK sequences.
// =========================================================================

module i2c_master #(
    parameter integer CLK_FREQ_HZ  = 200_000_000,
    parameter integer I2C_FREQ_HZ  = 400_000
)(
    input  wire        clk,
    input  wire        rst_n,

    // Command interface
    input  wire        cmd_valid,
    input  wire        cmd_read,      // 1 = read, 0 = write
    input  wire [6:0]  cmd_slave_addr,
    input  wire [7:0]  cmd_reg_addr,
    input  wire [7:0]  cmd_wdata,
    output reg  [7:0]  cmd_rdata,
    output reg         cmd_done,
    output reg         cmd_ack_err,

    // I2C PHY (directly to pads)
    output reg         scl_out,
    output reg         scl_oen,    // 1 = output enable (drive low)
    input  wire        scl_in,
    output reg         sda_out,
    output reg         sda_oen,    // 1 = output enable (drive low)
    input  wire        sda_in
);

    localparam integer CLK_DIV = CLK_FREQ_HZ / (I2C_FREQ_HZ * 4);
    localparam integer CNT_W   = $clog2(CLK_DIV + 1);

    // I2C states
    localparam [3:0] ST_IDLE      = 4'd0,
                     ST_START     = 4'd1,
                     ST_ADDR_W    = 4'd2,
                     ST_ADDR_ACK  = 4'd3,
                     ST_REG       = 4'd4,
                     ST_REG_ACK   = 4'd5,
                     ST_WR_DATA   = 4'd6,
                     ST_WR_ACK    = 4'd7,
                     ST_RESTART   = 4'd8,
                     ST_ADDR_R    = 4'd9,
                     ST_ADDR_R_ACK = 4'd10,
                     ST_RD_DATA   = 4'd11,
                     ST_RD_NACK   = 4'd12,
                     ST_STOP      = 4'd13;

    reg [3:0]       state;
    reg [CNT_W-1:0] clk_cnt;
    reg [1:0]       phase;    // 0..3 quarter-cycle phases
    reg [3:0]       bit_cnt;
    reg [7:0]       shift_out;
    reg [7:0]       shift_in;
    reg             is_read;
    reg [6:0]       slave_addr_r;
    reg [7:0]       reg_addr_r;
    reg [7:0]       wdata_r;

    wire phase_tick = (clk_cnt == CLK_DIV[CNT_W-1:0] - 1);

    always @(posedge clk) begin
        if (!rst_n) begin
            clk_cnt <= {CNT_W{1'b0}};
            phase   <= 2'd0;
        end else begin
            if (phase_tick) begin
                clk_cnt <= {CNT_W{1'b0}};
                phase   <= phase + 2'd1;
            end else begin
                clk_cnt <= clk_cnt + 1'b1;
            end
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            state       <= ST_IDLE;
            scl_out     <= 1'b1;
            scl_oen     <= 1'b0;
            sda_out     <= 1'b1;
            sda_oen     <= 1'b0;
            cmd_done    <= 1'b0;
            cmd_ack_err <= 1'b0;
            cmd_rdata   <= 8'd0;
            bit_cnt     <= 4'd0;
            shift_out   <= 8'd0;
            shift_in    <= 8'd0;
        end else if (phase_tick) begin
            cmd_done    <= 1'b0;
            cmd_ack_err <= 1'b0;

            case (state)
                ST_IDLE: begin
                    scl_out <= 1'b1; scl_oen <= 1'b0;
                    sda_out <= 1'b1; sda_oen <= 1'b0;
                    if (cmd_valid) begin
                        is_read      <= cmd_read;
                        slave_addr_r <= cmd_slave_addr;
                        reg_addr_r   <= cmd_reg_addr;
                        wdata_r      <= cmd_wdata;
                        state        <= ST_START;
                    end
                end

                ST_START: begin
                    case (phase)
                        2'd0: begin sda_out <= 1'b1; sda_oen <= 1'b0; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin sda_out <= 1'b0; sda_oen <= 1'b1; end // SDA low while SCL high = START
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= {slave_addr_r, 1'b0}; // write address
                            bit_cnt   <= 4'd7;
                            state     <= ST_ADDR_W;
                        end
                    endcase
                end

                ST_ADDR_W: begin
                    case (phase)
                        2'd0: begin sda_out <= shift_out[7]; sda_oen <= 1'b1; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: ;
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= {shift_out[6:0], 1'b0};
                            if (bit_cnt == 4'd0) state <= ST_ADDR_ACK;
                            else bit_cnt <= bit_cnt - 4'd1;
                        end
                    endcase
                end

                ST_ADDR_ACK: begin
                    case (phase)
                        2'd0: begin sda_oen <= 1'b0; end // release SDA
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin
                            if (sda_in) cmd_ack_err <= 1'b1; // NACK
                        end
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= reg_addr_r;
                            bit_cnt   <= 4'd7;
                            state     <= ST_REG;
                        end
                    endcase
                end

                ST_REG: begin
                    case (phase)
                        2'd0: begin sda_out <= shift_out[7]; sda_oen <= 1'b1; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: ;
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= {shift_out[6:0], 1'b0};
                            if (bit_cnt == 4'd0) state <= ST_REG_ACK;
                            else bit_cnt <= bit_cnt - 4'd1;
                        end
                    endcase
                end

                ST_REG_ACK: begin
                    case (phase)
                        2'd0: begin sda_oen <= 1'b0; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin
                            if (sda_in) cmd_ack_err <= 1'b1;
                        end
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            if (is_read) begin
                                state <= ST_RESTART;
                            end else begin
                                shift_out <= wdata_r;
                                bit_cnt   <= 4'd7;
                                state     <= ST_WR_DATA;
                            end
                        end
                    endcase
                end

                ST_WR_DATA: begin
                    case (phase)
                        2'd0: begin sda_out <= shift_out[7]; sda_oen <= 1'b1; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: ;
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= {shift_out[6:0], 1'b0};
                            if (bit_cnt == 4'd0) state <= ST_WR_ACK;
                            else bit_cnt <= bit_cnt - 4'd1;
                        end
                    endcase
                end

                ST_WR_ACK: begin
                    case (phase)
                        2'd0: begin sda_oen <= 1'b0; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin
                            if (sda_in) cmd_ack_err <= 1'b1;
                        end
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            state   <= ST_STOP;
                        end
                    endcase
                end

                ST_RESTART: begin
                    case (phase)
                        2'd0: begin sda_out <= 1'b1; sda_oen <= 1'b0; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin sda_out <= 1'b0; sda_oen <= 1'b1; end
                        2'd3: begin
                            scl_out   <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= {slave_addr_r, 1'b1}; // read address
                            bit_cnt   <= 4'd7;
                            state     <= ST_ADDR_R;
                        end
                    endcase
                end

                ST_ADDR_R: begin
                    case (phase)
                        2'd0: begin sda_out <= shift_out[7]; sda_oen <= 1'b1; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: ;
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            shift_out <= {shift_out[6:0], 1'b0};
                            if (bit_cnt == 4'd0) state <= ST_ADDR_R_ACK;
                            else bit_cnt <= bit_cnt - 4'd1;
                        end
                    endcase
                end

                ST_ADDR_R_ACK: begin
                    case (phase)
                        2'd0: begin sda_oen <= 1'b0; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin
                            if (sda_in) cmd_ack_err <= 1'b1;
                        end
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            bit_cnt <= 4'd7;
                            state   <= ST_RD_DATA;
                        end
                    endcase
                end

                ST_RD_DATA: begin
                    case (phase)
                        2'd0: begin sda_oen <= 1'b0; end // release SDA for slave
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin shift_in <= {shift_in[6:0], sda_in}; end
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            if (bit_cnt == 4'd0) begin
                                cmd_rdata <= {shift_in[6:0], sda_in};
                                state     <= ST_RD_NACK;
                            end else begin
                                bit_cnt <= bit_cnt - 4'd1;
                            end
                        end
                    endcase
                end

                ST_RD_NACK: begin
                    case (phase)
                        2'd0: begin sda_out <= 1'b1; sda_oen <= 1'b1; end // NACK
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: ;
                        2'd3: begin
                            scl_out <= 1'b0; scl_oen <= 1'b1;
                            state   <= ST_STOP;
                        end
                    endcase
                end

                ST_STOP: begin
                    case (phase)
                        2'd0: begin sda_out <= 1'b0; sda_oen <= 1'b1; end
                        2'd1: begin scl_out <= 1'b1; scl_oen <= 1'b0; end
                        2'd2: begin sda_out <= 1'b1; sda_oen <= 1'b0; end // SDA high while SCL high = STOP
                        2'd3: begin
                            cmd_done <= 1'b1;
                            state    <= ST_IDLE;
                        end
                    endcase
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule

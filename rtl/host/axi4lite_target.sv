// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     axi4lite_target
// DESCRIPTION: AXI4-Lite subordinate (target) interface. Decodes read/write
//              transactions from the PCIe root complex and routes them to
//              internal register banks (bridge CSR, DMA, IRQ, power mgmt,
//              node discovery).
//
// DATA WIDTH:  32-bit (AXI4-Lite standard)
// ADDR WIDTH:  16-bit (64 KB address space per NCE)
// =========================================================================

module axi4lite_target #(
    parameter integer ADDR_WIDTH = 16,
    parameter integer DATA_WIDTH = 32
)(
    input  wire                     aclk,
    input  wire                     aresetn,

    // AXI4-Lite Write Address Channel
    input  wire [ADDR_WIDTH-1:0]    s_axi_awaddr,
    input  wire                     s_axi_awvalid,
    output reg                      s_axi_awready,

    // AXI4-Lite Write Data Channel
    input  wire [DATA_WIDTH-1:0]    s_axi_wdata,
    input  wire [DATA_WIDTH/8-1:0]  s_axi_wstrb,
    input  wire                     s_axi_wvalid,
    output reg                      s_axi_wready,

    // AXI4-Lite Write Response Channel
    output reg  [1:0]               s_axi_bresp,
    output reg                      s_axi_bvalid,
    input  wire                     s_axi_bready,

    // AXI4-Lite Read Address Channel
    input  wire [ADDR_WIDTH-1:0]    s_axi_araddr,
    input  wire                     s_axi_arvalid,
    output reg                      s_axi_arready,

    // AXI4-Lite Read Data Channel
    output reg  [DATA_WIDTH-1:0]    s_axi_rdata,
    output reg  [1:0]               s_axi_rresp,
    output reg                      s_axi_rvalid,
    input  wire                     s_axi_rready,

    // Register interface (to internal logic)
    output reg  [ADDR_WIDTH-1:0]    reg_addr,
    output reg  [DATA_WIDTH-1:0]    reg_wdata,
    output reg  [DATA_WIDTH/8-1:0]  reg_wstrb,
    output reg                      reg_wen,
    output reg                      reg_ren,
    input  wire [DATA_WIDTH-1:0]    reg_rdata,
    input  wire                     reg_rvalid
);

    // AXI4-Lite response codes
    localparam [1:0] RESP_OKAY   = 2'b00;
    localparam [1:0] RESP_SLVERR = 2'b10;

    // ---- Write State Machine ----
    localparam [1:0] WR_IDLE = 2'd0,
                     WR_DATA = 2'd1,
                     WR_RESP = 2'd2;

    reg [1:0] wr_state;
    reg [ADDR_WIDTH-1:0] wr_addr_r;

    always @(posedge aclk) begin
        if (!aresetn) begin
            wr_state       <= WR_IDLE;
            s_axi_awready  <= 1'b0;
            s_axi_wready   <= 1'b0;
            s_axi_bvalid   <= 1'b0;
            s_axi_bresp    <= RESP_OKAY;
            reg_wen        <= 1'b0;
            reg_wdata      <= {DATA_WIDTH{1'b0}};
            reg_wstrb      <= {(DATA_WIDTH/8){1'b0}};
            wr_addr_r      <= {ADDR_WIDTH{1'b0}};
        end else begin
            reg_wen <= 1'b0;

            case (wr_state)
                WR_IDLE: begin
                    s_axi_awready <= 1'b1;
                    s_axi_wready  <= 1'b1;
                    s_axi_bvalid  <= 1'b0;
                    if (s_axi_awvalid && s_axi_awready) begin
                        wr_addr_r     <= s_axi_awaddr;
                        s_axi_awready <= 1'b0;
                        if (s_axi_wvalid && s_axi_wready) begin
                            reg_addr  <= s_axi_awaddr;
                            reg_wdata <= s_axi_wdata;
                            reg_wstrb <= s_axi_wstrb;
                            reg_wen   <= 1'b1;
                            s_axi_wready <= 1'b0;
                            wr_state  <= WR_RESP;
                        end else begin
                            wr_state <= WR_DATA;
                        end
                    end
                end

                WR_DATA: begin
                    if (s_axi_wvalid && s_axi_wready) begin
                        reg_addr  <= wr_addr_r;
                        reg_wdata <= s_axi_wdata;
                        reg_wstrb <= s_axi_wstrb;
                        reg_wen   <= 1'b1;
                        s_axi_wready <= 1'b0;
                        wr_state  <= WR_RESP;
                    end
                end

                WR_RESP: begin
                    s_axi_bvalid <= 1'b1;
                    s_axi_bresp  <= RESP_OKAY;
                    if (s_axi_bvalid && s_axi_bready) begin
                        s_axi_bvalid <= 1'b0;
                        wr_state     <= WR_IDLE;
                    end
                end

                default: wr_state <= WR_IDLE;
            endcase
        end
    end

    // ---- Read State Machine ----
    localparam [1:0] RD_IDLE = 2'd0,
                     RD_WAIT = 2'd1,
                     RD_RESP = 2'd2;

    reg [1:0] rd_state;

    always @(posedge aclk) begin
        if (!aresetn) begin
            rd_state      <= RD_IDLE;
            s_axi_arready <= 1'b0;
            s_axi_rvalid  <= 1'b0;
            s_axi_rdata   <= {DATA_WIDTH{1'b0}};
            s_axi_rresp   <= RESP_OKAY;
            reg_ren       <= 1'b0;
        end else begin
            reg_ren <= 1'b0;

            case (rd_state)
                RD_IDLE: begin
                    s_axi_arready <= 1'b1;
                    s_axi_rvalid  <= 1'b0;
                    if (s_axi_arvalid && s_axi_arready) begin
                        reg_addr      <= s_axi_araddr;
                        reg_ren       <= 1'b1;
                        s_axi_arready <= 1'b0;
                        rd_state      <= RD_WAIT;
                    end
                end

                RD_WAIT: begin
                    if (reg_rvalid) begin
                        s_axi_rdata <= reg_rdata;
                        s_axi_rresp <= RESP_OKAY;
                        s_axi_rvalid <= 1'b1;
                        rd_state     <= RD_RESP;
                    end
                end

                RD_RESP: begin
                    if (s_axi_rvalid && s_axi_rready) begin
                        s_axi_rvalid <= 1'b0;
                        rd_state     <= RD_IDLE;
                    end
                end

                default: rd_state <= RD_IDLE;
            endcase
        end
    end

endmodule

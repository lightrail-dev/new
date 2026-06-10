// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     interrupt_controller
// DESCRIPTION: Level-sensitive interrupt controller with mask, status,
//              and clear registers. Supports 16 interrupt sources for
//              bridge, DMA, power, and thermal events.
// =========================================================================

module interrupt_controller #(
    parameter integer NUM_IRQS = 16
)(
    input  wire                  clk,
    input  wire                  rst_n,

    // Interrupt sources
    input  wire [NUM_IRQS-1:0]   irq_sources,

    // Register interface
    input  wire [3:0]            reg_addr,   // 4-bit sub-address
    input  wire [31:0]           reg_wdata,
    input  wire                  reg_wen,
    input  wire                  reg_ren,
    output reg  [31:0]           reg_rdata,
    output reg                   reg_rvalid,

    // IRQ output (active-high, directly to PCIe MSI-X or INTA#)
    output wire                  irq_out
);

    // Register map (4-bit address within IRQ block)
    // 0x0: IRQ_STATUS (R/W1C)
    // 0x4: IRQ_MASK   (R/W)
    // 0x8: IRQ_RAW    (RO)
    // 0xC: IRQ_SET    (WO, for SW-triggered IRQs / debug)

    reg [NUM_IRQS-1:0] irq_status;
    reg [NUM_IRQS-1:0] irq_mask;    // 1 = enabled

    wire [NUM_IRQS-1:0] irq_pending = irq_status & irq_mask;
    assign irq_out = |irq_pending;

    // Latch rising edges of interrupt sources
    reg [NUM_IRQS-1:0] irq_prev;
    wire [NUM_IRQS-1:0] irq_edge = irq_sources & ~irq_prev;

    always @(posedge clk) begin
        if (!rst_n) begin
            irq_status <= {NUM_IRQS{1'b0}};
            irq_mask   <= {NUM_IRQS{1'b0}};
            irq_prev   <= {NUM_IRQS{1'b0}};
            reg_rdata  <= 32'd0;
            reg_rvalid <= 1'b0;
        end else begin
            irq_prev   <= irq_sources;
            irq_status <= irq_status | irq_edge;
            reg_rvalid <= 1'b0;

            // Register writes
            if (reg_wen) begin
                case (reg_addr)
                    4'h0: irq_status <= irq_status & ~reg_wdata[NUM_IRQS-1:0]; // W1C
                    4'h4: irq_mask   <= reg_wdata[NUM_IRQS-1:0];
                    4'hC: irq_status <= irq_status | reg_wdata[NUM_IRQS-1:0];  // SW set
                    default: ;
                endcase
            end

            // Register reads
            if (reg_ren) begin
                reg_rvalid <= 1'b1;
                case (reg_addr)
                    4'h0: reg_rdata <= {{(32-NUM_IRQS){1'b0}}, irq_status};
                    4'h4: reg_rdata <= {{(32-NUM_IRQS){1'b0}}, irq_mask};
                    4'h8: reg_rdata <= {{(32-NUM_IRQS){1'b0}}, irq_sources};
                    default: reg_rdata <= 32'd0;
                endcase
            end
        end
    end

endmodule

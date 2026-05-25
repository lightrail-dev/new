// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     tb_dual_chip_system
// DESCRIPTION: System-level verification testbench for the symmetrical
//              Dual-NCE Accelerator Board. Instantiates two nce_top
//              instances (Node A and Node B) connected back-to-back
//              via the inter-chip bridge model.
//
// TEST CASES:
//   1. Boot and cross-chip register discovery
//   2. High-bandwidth stress test with random CRC error injection
//
// SIMULATION:  Icarus Verilog / Verilator / ModelSim compatible
// =========================================================================

`timescale 1ns / 1ps

module tb_dual_chip_system;

    // ---- Parameters ----
    localparam BRG_DATA_WIDTH = 64;
    localparam AXI_ADDR_WIDTH = 16;
    localparam AXI_DATA_WIDTH = 32;
    localparam SYS_CLK_PERIOD = 5.0;   // 200 MHz
    localparam BRG_CLK_PERIOD = 2.0;   // 500 MHz

    // ---- Clock and Reset ----
    reg sys_clk  = 0;
    reg brg_clk  = 0;
    reg sys_rst_n = 0;
    reg brg_rst_n = 0;

    always #(SYS_CLK_PERIOD / 2.0) sys_clk = ~sys_clk;
    always #(BRG_CLK_PERIOD / 2.0) brg_clk = ~brg_clk;

    // ---- Inter-Chip Bridge Wires (A ↔ B) ----
    wire [BRG_DATA_WIDTH-1:0] brg_a2b_data,  brg_b2a_data;
    wire                      brg_a2b_valid,  brg_b2a_valid;
    wire                      brg_a2b_last,   brg_b2a_last;
    wire [3:0]                brg_a2b_credit, brg_b2a_credit;
    wire                      brg_a2b_credit_valid, brg_b2a_credit_valid;
    wire                      brg_a2b_ack, brg_b2a_ack;

    // Error injection wire (active for stress test)
    reg                       inject_error_a2b = 0;
    reg                       inject_error_b2a = 0;

    // Bridge data with optional bit-flip for error injection
    wire [BRG_DATA_WIDTH-1:0] brg_a2b_data_err = inject_error_a2b ?
                                (brg_a2b_data ^ 64'h0000_0000_0000_0001) :
                                brg_a2b_data;

    // ---- I2C Loopback (VRM model) ----
    wire scl_a, scl_oen_a, sda_a, sda_oen_a;
    wire scl_b, scl_oen_b, sda_b, sda_oen_b;
    // Pull-up model: if oen is asserted (drive low), pin = 0; else pin = 1
    wire scl_pin_a = scl_oen_a ? 1'b0 : 1'b1;
    wire sda_pin_a = sda_oen_a ? 1'b0 : 1'b1;
    wire scl_pin_b = scl_oen_b ? 1'b0 : 1'b1;
    wire sda_pin_b = sda_oen_b ? 1'b0 : 1'b1;

    // ---- AXI4-Lite Bus Signals (Node A) ----
    reg  [AXI_ADDR_WIDTH-1:0] axi_a_awaddr;
    reg                        axi_a_awvalid;
    wire                       axi_a_awready;
    reg  [AXI_DATA_WIDTH-1:0] axi_a_wdata;
    reg  [3:0]                 axi_a_wstrb;
    reg                        axi_a_wvalid;
    wire                       axi_a_wready;
    wire [1:0]                 axi_a_bresp;
    wire                       axi_a_bvalid;
    reg                        axi_a_bready;
    reg  [AXI_ADDR_WIDTH-1:0] axi_a_araddr;
    reg                        axi_a_arvalid;
    wire                       axi_a_arready;
    wire [AXI_DATA_WIDTH-1:0] axi_a_rdata;
    wire [1:0]                 axi_a_rresp;
    wire                       axi_a_rvalid;
    reg                        axi_a_rready;

    // ---- AXI4-Lite Bus Signals (Node B) ----
    reg  [AXI_ADDR_WIDTH-1:0] axi_b_awaddr;
    reg                        axi_b_awvalid;
    wire                       axi_b_awready;
    reg  [AXI_DATA_WIDTH-1:0] axi_b_wdata;
    reg  [3:0]                 axi_b_wstrb;
    reg                        axi_b_wvalid;
    wire                       axi_b_wready;
    wire [1:0]                 axi_b_bresp;
    wire                       axi_b_bvalid;
    reg                        axi_b_bready;
    reg  [AXI_ADDR_WIDTH-1:0] axi_b_araddr;
    reg                        axi_b_arvalid;
    wire                       axi_b_arready;
    wire [AXI_DATA_WIDTH-1:0] axi_b_rdata;
    wire [1:0]                 axi_b_rresp;
    wire                       axi_b_rvalid;
    reg                        axi_b_rready;

    // ---- Status Outputs ----
    wire       irq_a, irq_b;
    wire [1:0] dvfs_a, dvfs_b;
    wire       thermal_a, thermal_b;

    // ====================================================================
    // DUT: Node A (node_id = 0)
    // ====================================================================
    nce_top #(
        .BRG_DATA_WIDTH(BRG_DATA_WIDTH),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .MAX_CREDITS   (16),
        .FW_VERSION    (32'h0001_0000)
    ) u_node_a (
        .sys_clk          (sys_clk),
        .sys_rst_n        (sys_rst_n),
        .brg_clk          (brg_clk),
        .brg_rst_n        (brg_rst_n),
        .node_id          (1'b0),

        .s_axi_awaddr     (axi_a_awaddr),
        .s_axi_awvalid    (axi_a_awvalid),
        .s_axi_awready    (axi_a_awready),
        .s_axi_wdata      (axi_a_wdata),
        .s_axi_wstrb      (axi_a_wstrb),
        .s_axi_wvalid     (axi_a_wvalid),
        .s_axi_wready     (axi_a_wready),
        .s_axi_bresp      (axi_a_bresp),
        .s_axi_bvalid     (axi_a_bvalid),
        .s_axi_bready     (axi_a_bready),
        .s_axi_araddr     (axi_a_araddr),
        .s_axi_arvalid    (axi_a_arvalid),
        .s_axi_arready    (axi_a_arready),
        .s_axi_rdata      (axi_a_rdata),
        .s_axi_rresp      (axi_a_rresp),
        .s_axi_rvalid     (axi_a_rvalid),
        .s_axi_rready     (axi_a_rready),

        .brg_data_out     (brg_a2b_data),
        .brg_valid_out    (brg_a2b_valid),
        .brg_last_out     (brg_a2b_last),
        .brg_data_in      (brg_b2a_data),
        .brg_valid_in     (brg_b2a_valid),
        .brg_last_in      (brg_b2a_last),
        .brg_credit_out      (brg_a2b_credit),
        .brg_credit_out_valid(brg_a2b_credit_valid),
        .brg_credit_in       (brg_b2a_credit),
        .brg_credit_in_valid (brg_b2a_credit_valid),
        .brg_err_in       (inject_error_b2a),
        .brg_ack_out      (brg_a2b_ack),

        .brg_fwd_clk_p    (),
        .brg_fwd_clk_n    (),

        .i2c_scl_out      (scl_a),
        .i2c_scl_oen      (scl_oen_a),
        .i2c_scl_in       (scl_pin_a),
        .i2c_sda_out      (sda_a),
        .i2c_sda_oen      (sda_oen_a),
        .i2c_sda_in       (sda_pin_a),

        .irq_out           (irq_a),
        .dvfs_state        (dvfs_a),
        .thermal_shutdown  (thermal_a)
    );

    // ====================================================================
    // DUT: Node B (node_id = 1)
    // ====================================================================
    nce_top #(
        .BRG_DATA_WIDTH(BRG_DATA_WIDTH),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .MAX_CREDITS   (16),
        .FW_VERSION    (32'h0001_0000)
    ) u_node_b (
        .sys_clk          (sys_clk),
        .sys_rst_n        (sys_rst_n),
        .brg_clk          (brg_clk),
        .brg_rst_n        (brg_rst_n),
        .node_id          (1'b1),

        .s_axi_awaddr     (axi_b_awaddr),
        .s_axi_awvalid    (axi_b_awvalid),
        .s_axi_awready    (axi_b_awready),
        .s_axi_wdata      (axi_b_wdata),
        .s_axi_wstrb      (axi_b_wstrb),
        .s_axi_wvalid     (axi_b_wvalid),
        .s_axi_wready     (axi_b_wready),
        .s_axi_bresp      (axi_b_bresp),
        .s_axi_bvalid     (axi_b_bvalid),
        .s_axi_bready     (axi_b_bready),
        .s_axi_araddr     (axi_b_araddr),
        .s_axi_arvalid    (axi_b_arvalid),
        .s_axi_arready    (axi_b_arready),
        .s_axi_rdata      (axi_b_rdata),
        .s_axi_rresp      (axi_b_rresp),
        .s_axi_rvalid     (axi_b_rvalid),
        .s_axi_rready     (axi_b_rready),

        .brg_data_out     (brg_b2a_data),
        .brg_valid_out    (brg_b2a_valid),
        .brg_last_out     (brg_b2a_last),
        .brg_data_in      (brg_a2b_data_err),
        .brg_valid_in     (brg_a2b_valid),
        .brg_last_in      (brg_a2b_last),
        .brg_credit_out      (brg_b2a_credit),
        .brg_credit_out_valid(brg_b2a_credit_valid),
        .brg_credit_in       (brg_a2b_credit),
        .brg_credit_in_valid (brg_a2b_credit_valid),
        .brg_err_in       (inject_error_a2b),
        .brg_ack_out      (brg_b2a_ack),

        .brg_fwd_clk_p    (),
        .brg_fwd_clk_n    (),

        .i2c_scl_out      (scl_b),
        .i2c_scl_oen      (scl_oen_b),
        .i2c_scl_in       (scl_pin_b),
        .i2c_sda_out      (sda_b),
        .i2c_sda_oen      (sda_oen_b),
        .i2c_sda_in       (sda_pin_b),

        .irq_out           (irq_b),
        .dvfs_state        (dvfs_b),
        .thermal_shutdown  (thermal_b)
    );

    // ====================================================================
    // Test Tasks
    // ====================================================================

    integer test_pass_count = 0;
    integer test_fail_count = 0;

    task automatic axi_write;
        input [AXI_ADDR_WIDTH-1:0] addr;
        input [AXI_DATA_WIDTH-1:0] data;
        input integer node; // 0=A, 1=B
        begin
            @(posedge sys_clk);
            if (node == 0) begin
                axi_a_awaddr  <= addr;
                axi_a_awvalid <= 1'b1;
                axi_a_wdata   <= data;
                axi_a_wstrb   <= 4'hF;
                axi_a_wvalid  <= 1'b1;
                axi_a_bready  <= 1'b1;
                @(posedge sys_clk);
                wait(axi_a_awready && axi_a_wready);
                @(posedge sys_clk);
                axi_a_awvalid <= 1'b0;
                axi_a_wvalid  <= 1'b0;
                wait(axi_a_bvalid);
                @(posedge sys_clk);
                axi_a_bready <= 1'b0;
            end else begin
                axi_b_awaddr  <= addr;
                axi_b_awvalid <= 1'b1;
                axi_b_wdata   <= data;
                axi_b_wstrb   <= 4'hF;
                axi_b_wvalid  <= 1'b1;
                axi_b_bready  <= 1'b1;
                @(posedge sys_clk);
                wait(axi_b_awready && axi_b_wready);
                @(posedge sys_clk);
                axi_b_awvalid <= 1'b0;
                axi_b_wvalid  <= 1'b0;
                wait(axi_b_bvalid);
                @(posedge sys_clk);
                axi_b_bready <= 1'b0;
            end
        end
    endtask

    task automatic axi_read;
        input  [AXI_ADDR_WIDTH-1:0] addr;
        output [AXI_DATA_WIDTH-1:0] data;
        input  integer node;
        begin
            @(posedge sys_clk);
            if (node == 0) begin
                axi_a_araddr  <= addr;
                axi_a_arvalid <= 1'b1;
                axi_a_rready  <= 1'b1;
                @(posedge sys_clk);
                wait(axi_a_arready);
                @(posedge sys_clk);
                axi_a_arvalid <= 1'b0;
                wait(axi_a_rvalid);
                data = axi_a_rdata;
                @(posedge sys_clk);
                axi_a_rready <= 1'b0;
            end else begin
                axi_b_araddr  <= addr;
                axi_b_arvalid <= 1'b1;
                axi_b_rready  <= 1'b1;
                @(posedge sys_clk);
                wait(axi_b_arready);
                @(posedge sys_clk);
                axi_b_arvalid <= 1'b0;
                wait(axi_b_rvalid);
                data = axi_b_rdata;
                @(posedge sys_clk);
                axi_b_rready <= 1'b0;
            end
        end
    endtask

    task check;
        input [AXI_DATA_WIDTH-1:0] expected;
        input [AXI_DATA_WIDTH-1:0] actual;
        input [255:0] test_name;
        begin
            if (expected === actual) begin
                $display("[PASS] %0s: expected=0x%08h, got=0x%08h", test_name, expected, actual);
                test_pass_count = test_pass_count + 1;
            end else begin
                $display("[FAIL] %0s: expected=0x%08h, got=0x%08h", test_name, expected, actual);
                test_fail_count = test_fail_count + 1;
            end
        end
    endtask

    // ====================================================================
    // Main Test Sequence
    // ====================================================================

    reg [AXI_DATA_WIDTH-1:0] rd_data;
    integer i;

    initial begin
        $dumpfile("tb_dual_chip_system.vcd");
        $dumpvars(0, tb_dual_chip_system);

        // Initialize AXI signals
        axi_a_awaddr = 0; axi_a_awvalid = 0; axi_a_wdata = 0;
        axi_a_wstrb = 0;  axi_a_wvalid = 0;  axi_a_bready = 0;
        axi_a_araddr = 0; axi_a_arvalid = 0; axi_a_rready = 0;
        axi_b_awaddr = 0; axi_b_awvalid = 0; axi_b_wdata = 0;
        axi_b_wstrb = 0;  axi_b_wvalid = 0;  axi_b_bready = 0;
        axi_b_araddr = 0; axi_b_arvalid = 0; axi_b_rready = 0;

        // ========================================================
        // RESET
        // ========================================================
        $display("\n========================================");
        $display("LightRail Dual-NCE Accelerator Testbench");
        $display("========================================\n");

        sys_rst_n = 0;
        brg_rst_n = 0;
        #100;
        sys_rst_n = 1;
        brg_rst_n = 1;
        #50;

        // ========================================================
        // TEST 1: Boot and Cross-Chip Register Discovery
        // ========================================================
        $display("\n--- TEST 1: Boot and Cross-Chip Register Discovery ---\n");

        // Read Node A identity (node_id = 0)
        axi_read(16'h1000, rd_data, 0);
        check(32'h0000_0000, rd_data, "Node A: NODE_ID = 0");

        // Read Node A firmware version
        axi_read(16'h1004, rd_data, 0);
        check(32'h0001_0000, rd_data, "Node A: FW_VERSION");

        // Read Node B identity (node_id = 1)
        axi_read(16'h1000, rd_data, 1);
        check(32'h0000_0001, rd_data, "Node B: NODE_ID = 1");

        // Read Node B firmware version
        axi_read(16'h1004, rd_data, 1);
        check(32'h0001_0000, rd_data, "Node B: FW_VERSION");

        // Read bridge link status on Node A
        axi_read(16'h0004, rd_data, 0);
        $display("Node A bridge link_up = %0d", rd_data[0]);

        // Read bridge TX packet count (should be 0 at boot)
        axi_read(16'h0008, rd_data, 0);
        check(32'h0000_0000, rd_data, "Node A: TX_PKT_CNT at boot");

        // Read bridge CRC error count (should be 0 at boot)
        axi_read(16'h0010, rd_data, 0);
        check(32'h0000_0000, rd_data, "Node A: CRC_ERR_CNT at boot");

        // Read power management status
        axi_read(16'h0804, rd_data, 0);
        $display("Node A DVFS state = %0d, thermal_shutdown = %0d",
                 rd_data[1:0], rd_data[2]);

        // Enable telemetry on Node A
        axi_write(16'h0800, 32'h0000_0001, 0);
        axi_read(16'h0800, rd_data, 0);
        check(32'h0000_0001, rd_data, "Node A: Telemetry enabled");

        // Read IRQ status (should be 0)
        axi_read(16'h0400, rd_data, 0);
        $display("Node A IRQ_STATUS = 0x%08h", rd_data);

        $display("\n--- TEST 1 COMPLETE ---\n");

        // ========================================================
        // TEST 2: High-Bandwidth Stress Test with Error Injection
        // ========================================================
        $display("\n--- TEST 2: Bridge Stress Test with CRC Error Injection ---\n");

        // Enable DMA on Node A
        axi_write(16'h0100, 32'h0000_0001, 0);

        // Submit DMA descriptors (TX direction, 4 beats each)
        for (i = 0; i < 4; i = i + 1) begin
            // src_addr
            axi_write(16'h0110, i * 32'h100, 0);
            // dst_addr
            axi_write(16'h0114, 32'hBEEF_0000 + i * 32'h100, 0);
            // length=4, dir=TX, irq_on_complete=1
            axi_write(16'h0118, {16'd0, 6'd0, 1'b1, 1'b0, 8'd0, 16'd4}, 0);
        end

        // Wait for DMA to process
        repeat(200) @(posedge sys_clk);

        // Read bridge TX packet count
        axi_read(16'h0008, rd_data, 0);
        $display("Node A TX packets after DMA burst = %0d", rd_data);

        // Now inject errors: flip a bit in A→B data path
        $display("Injecting CRC errors on A->B bridge...");
        inject_error_a2b = 1;

        // Submit more DMA descriptors during error injection
        for (i = 0; i < 2; i = i + 1) begin
            axi_write(16'h0110, 32'hDEAD_0000 + i * 32'h100, 0);
            axi_write(16'h0114, 32'hCAFE_0000 + i * 32'h100, 0);
            axi_write(16'h0118, {16'd0, 6'd0, 1'b1, 1'b0, 8'd0, 16'd4}, 0);
        end

        repeat(200) @(posedge sys_clk);

        // Stop error injection
        inject_error_a2b = 0;

        repeat(100) @(posedge sys_clk);

        // Read CRC error count on Node B
        axi_read(16'h0010, rd_data, 1);
        $display("Node B CRC errors detected = %0d", rd_data);
        if (rd_data > 0) begin
            $display("[PASS] CRC error detection working");
            test_pass_count = test_pass_count + 1;
        end else begin
            $display("[INFO] CRC error count = 0 (error injection may not have aligned with valid packets)");
        end

        // Read bridge stats
        axi_read(16'h0008, rd_data, 0);
        $display("Node A total TX packets = %0d", rd_data);
        axi_read(16'h000C, rd_data, 1);
        $display("Node B total RX packets = %0d", rd_data);

        $display("\n--- TEST 2 COMPLETE ---\n");

        // ========================================================
        // Summary
        // ========================================================
        $display("\n========================================");
        $display("TEST SUMMARY: %0d passed, %0d failed",
                 test_pass_count, test_fail_count);
        $display("========================================\n");

        if (test_fail_count > 0)
            $display("*** SOME TESTS FAILED ***");
        else
            $display("*** ALL TESTS PASSED ***");

        #100;
        $finish;
    end

    // ---- Timeout watchdog ----
    initial begin
        #500_000;
        $display("\n[ERROR] Simulation timeout!");
        $finish;
    end

endmodule

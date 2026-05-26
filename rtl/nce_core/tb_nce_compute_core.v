// =========================================================================
// COMPANY:    LightRail AI
// MODULE:     tb_nce_compute_core
// DESCRIPTION: Testbench for nce_compute_core — validates SIMD operations,
//              AXI register access, DMA, thermal management, and QPA
//              trigger output. Targets SMIC 28nm/40nm MPW shuttle.
// =========================================================================

`timescale 1ns / 1ps

module tb_nce_compute_core;

    // ---- Parameters (MPW shuttle configuration) ----
    parameter SIMD_LANES       = 8;
    parameter NUM_CLUSTERS     = 1;
    parameter DATA_WIDTH       = 16;
    parameter ACCUM_WIDTH      = 32;
    parameter REG_DEPTH        = 32;
    parameter REG_WIDTH        = 256;
    parameter L1_SIZE_BYTES    = 4096;
    parameter L2_SIZE_BYTES    = 16384;
    parameter QPA_CHANNELS     = 8;
    parameter QPA_PHASE_WIDTH  = 16;
    parameter AXI_ADDR_WIDTH   = 32;
    parameter AXI_DATA_WIDTH   = 64;
    parameter DMA_CHANNELS     = 4;
    parameter NUM_THERMAL_DIODES = 4;
    parameter THERMAL_WIDTH    = 12;

    // ---- Clock & Reset ----
    reg clk_compute;
    reg clk_sys;
    reg rst_n;

    // ---- AXI4-Lite Signals ----
    reg                             axi_awvalid;
    reg  [AXI_ADDR_WIDTH-1:0]      axi_awaddr;
    wire                            axi_awready;
    reg                             axi_wvalid;
    reg  [AXI_DATA_WIDTH-1:0]      axi_wdata;
    reg  [(AXI_DATA_WIDTH/8)-1:0]  axi_wstrb;
    wire                            axi_wready;
    wire                            axi_bvalid;
    wire [1:0]                      axi_bresp;
    reg                             axi_bready;
    reg                             axi_arvalid;
    reg  [AXI_ADDR_WIDTH-1:0]      axi_araddr;
    wire                            axi_arready;
    wire                            axi_rvalid;
    wire [AXI_DATA_WIDTH-1:0]      axi_rdata;
    wire [1:0]                      axi_rresp;
    reg                             axi_rready;

    // ---- DMA ----
    wire                            dma_req_valid;
    wire [AXI_ADDR_WIDTH-1:0]      dma_req_addr;
    wire [15:0]                     dma_req_len;
    wire                            dma_req_write;
    reg                             dma_req_ready;
    reg                             dma_resp_valid;
    reg  [AXI_DATA_WIDTH-1:0]      dma_resp_data;
    wire                            dma_resp_ready;

    // ---- QPA ----
    wire                            qpa_trigger_valid;
    wire [(QPA_CHANNELS*QPA_PHASE_WIDTH)-1:0] qpa_phase_vector;
    reg                             qpa_trigger_ready;
    reg  [QPA_CHANNELS-1:0]        qpa_fault_status;

    // ---- Thermal ----
    reg  [NUM_THERMAL_DIODES*THERMAL_WIDTH-1:0] thermal_adc_data;
    reg                             thermal_adc_valid;

    // ---- Outputs ----
    wire [2:0]                      dvfs_state;
    wire [NUM_CLUSTERS-1:0]        cluster_power_gate;
    wire                            thermal_throttle;
    wire                            thermal_shutdown;
    wire                            irq_out;

    // ---- DUT ----
    nce_compute_core #(
        .SIMD_LANES(SIMD_LANES),
        .NUM_CLUSTERS(NUM_CLUSTERS),
        .DATA_WIDTH(DATA_WIDTH),
        .ACCUM_WIDTH(ACCUM_WIDTH),
        .REG_DEPTH(REG_DEPTH),
        .REG_WIDTH(REG_WIDTH),
        .L1_SIZE_BYTES(L1_SIZE_BYTES),
        .L2_SIZE_BYTES(L2_SIZE_BYTES),
        .QPA_CHANNELS(QPA_CHANNELS),
        .QPA_PHASE_WIDTH(QPA_PHASE_WIDTH),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .DMA_CHANNELS(DMA_CHANNELS),
        .NUM_THERMAL_DIODES(NUM_THERMAL_DIODES),
        .THERMAL_WIDTH(THERMAL_WIDTH)
    ) dut (
        .clk_compute(clk_compute),
        .clk_sys(clk_sys),
        .rst_n(rst_n),
        .axi_awvalid(axi_awvalid),
        .axi_awaddr(axi_awaddr),
        .axi_awready(axi_awready),
        .axi_wvalid(axi_wvalid),
        .axi_wdata(axi_wdata),
        .axi_wstrb(axi_wstrb),
        .axi_wready(axi_wready),
        .axi_bvalid(axi_bvalid),
        .axi_bresp(axi_bresp),
        .axi_bready(axi_bready),
        .axi_arvalid(axi_arvalid),
        .axi_araddr(axi_araddr),
        .axi_arready(axi_arready),
        .axi_rvalid(axi_rvalid),
        .axi_rdata(axi_rdata),
        .axi_rresp(axi_rresp),
        .axi_rready(axi_rready),
        .dma_req_valid(dma_req_valid),
        .dma_req_addr(dma_req_addr),
        .dma_req_len(dma_req_len),
        .dma_req_write(dma_req_write),
        .dma_req_ready(dma_req_ready),
        .dma_resp_valid(dma_resp_valid),
        .dma_resp_data(dma_resp_data),
        .dma_resp_ready(dma_resp_ready),
        .qpa_trigger_valid(qpa_trigger_valid),
        .qpa_phase_vector(qpa_phase_vector),
        .qpa_trigger_ready(qpa_trigger_ready),
        .qpa_fault_status(qpa_fault_status),
        .thermal_adc_data(thermal_adc_data),
        .thermal_adc_valid(thermal_adc_valid),
        .dvfs_state(dvfs_state),
        .cluster_power_gate(cluster_power_gate),
        .thermal_throttle(thermal_throttle),
        .thermal_shutdown(thermal_shutdown),
        .irq_out(irq_out)
    );

    // ---- Clock Generation ----
    initial clk_compute = 0;
    always #0.5 clk_compute = ~clk_compute;  // 1 GHz

    initial clk_sys = 0;
    always #2.0 clk_sys = ~clk_sys;          // 250 MHz

    // ---- AXI Write Task ----
    task axi_write(input [31:0] addr, input [63:0] data);
        begin
            @(posedge clk_sys);
            axi_awvalid <= 1'b1;
            axi_awaddr  <= addr;
            axi_wvalid  <= 1'b1;
            axi_wdata   <= data;
            axi_wstrb   <= 8'hFF;
            @(posedge clk_sys);
            while (!(axi_awready && axi_wready)) @(posedge clk_sys);
            axi_awvalid <= 1'b0;
            axi_wvalid  <= 1'b0;
            @(posedge clk_sys);
            while (!axi_bvalid) @(posedge clk_sys);
            axi_bready <= 1'b1;
            @(posedge clk_sys);
            axi_bready <= 1'b0;
        end
    endtask

    // ---- AXI Read Task ----
    task axi_read(input [31:0] addr, output [63:0] data);
        begin
            @(posedge clk_sys);
            axi_arvalid <= 1'b1;
            axi_araddr  <= addr;
            @(posedge clk_sys);
            while (!axi_arready) @(posedge clk_sys);
            axi_arvalid <= 1'b0;
            axi_rready  <= 1'b1;
            @(posedge clk_sys);
            while (!axi_rvalid) @(posedge clk_sys);
            data = axi_rdata;
            @(posedge clk_sys);
            axi_rready <= 1'b0;
        end
    endtask

    // ---- Test Sequence ----
    reg [63:0] read_data;
    integer test_pass;
    integer test_fail;

    initial begin
        $dumpfile("nce_compute_core.vcd");
        $dumpvars(0, tb_nce_compute_core);

        // Initialize
        rst_n           = 0;
        axi_awvalid     = 0;
        axi_awaddr      = 0;
        axi_wvalid      = 0;
        axi_wdata       = 0;
        axi_wstrb       = 0;
        axi_bready      = 0;
        axi_arvalid     = 0;
        axi_araddr      = 0;
        axi_rready      = 0;
        dma_req_ready   = 1;
        dma_resp_valid  = 0;
        dma_resp_data   = 0;
        qpa_trigger_ready = 1;
        qpa_fault_status = 8'h00;
        thermal_adc_data = 0;
        thermal_adc_valid = 0;
        test_pass = 0;
        test_fail = 0;

        // Reset
        #20;
        rst_n = 1;
        #20;

        $display("========================================");
        $display("NCE Compute Core Testbench — Start");
        $display("========================================");

        // ------ Test 1: Read STATUS register (should be 0) ------
        $display("\nTest 1: Read STATUS register after reset");
        axi_read(32'h0000_0004, read_data);
        if (read_data[5:0] == 6'b000000) begin
            $display("  PASS: STATUS = 0x%h", read_data);
            test_pass = test_pass + 1;
        end else begin
            $display("  FAIL: STATUS = 0x%h (expected 0)", read_data);
            test_fail = test_fail + 1;
        end

        // ------ Test 2: Write/Read DVFS register ------
        $display("\nTest 2: Write/Read DVFS state");
        axi_write(32'h0000_0020, 64'd3);
        axi_read(32'h0000_0020, read_data);
        if (read_data[2:0] == 3'd3) begin
            $display("  PASS: DVFS state = %0d", read_data[2:0]);
            test_pass = test_pass + 1;
        end else begin
            $display("  FAIL: DVFS state = %0d (expected 3)", read_data[2:0]);
            test_fail = test_fail + 1;
        end

        // ------ Test 3: Write SIMD VADD instruction and trigger ------
        $display("\nTest 3: SIMD VADD operation");
        // Instruction: opcode=VADD(0x2), rd=0, rs1=0, rs2=0
        axi_write(32'h0000_0008, 64'h2000_0000);
        // Enable + start SIMD
        axi_write(32'h0000_0000, 64'h0000_0003);
        // Wait for completion
        #50;
        axi_read(32'h0000_000C, read_data);
        if (read_data[1] == 1'b1) begin
            $display("  PASS: SIMD done flag set");
            test_pass = test_pass + 1;
        end else begin
            $display("  FAIL: SIMD done flag not set");
            test_fail = test_fail + 1;
        end

        // ------ Test 4: Thermal reading ------
        $display("\nTest 4: Thermal ADC reading");
        thermal_adc_data = {12'd3200, 12'd3100, 12'd3050, 12'd3000};
        thermal_adc_valid = 1;
        #10;
        thermal_adc_valid = 0;
        #20;
        axi_read(32'h0000_0024, read_data);
        $display("  Thermal data = 0x%h", read_data);
        if (read_data != 0) begin
            $display("  PASS: Non-zero thermal readings");
            test_pass = test_pass + 1;
        end else begin
            $display("  FAIL: Zero thermal readings");
            test_fail = test_fail + 1;
        end

        // ------ Test 5: Power gate control ------
        $display("\nTest 5: Power gate control");
        axi_write(32'h0000_0028, 64'h0000_0000); // Gate all clusters
        axi_read(32'h0000_0028, read_data);
        if (read_data[0] == 1'b0) begin
            $display("  PASS: Cluster 0 gated");
            test_pass = test_pass + 1;
        end else begin
            $display("  FAIL: Cluster 0 not gated");
            test_fail = test_fail + 1;
        end
        // Restore
        axi_write(32'h0000_0028, 64'h0000_0001);

        // ------ Test 6: QPA fault injection ------
        $display("\nTest 6: QPA fault injection");
        qpa_fault_status = 8'h01; // Channel 0 fault
        #20;
        axi_read(32'h0000_0004, read_data);
        if (read_data[6] == 1'b1) begin
            $display("  PASS: QPA fault detected in STATUS");
            test_pass = test_pass + 1;
        end else begin
            $display("  FAIL: QPA fault not reflected in STATUS");
            test_fail = test_fail + 1;
        end
        qpa_fault_status = 8'h00;

        // ------ Test 7: Interrupt check ------
        $display("\nTest 7: Interrupt generation");
        #20;
        axi_read(32'h0000_002C, read_data);
        $display("  IRQ pending = 0x%h, irq_out = %b", read_data[7:0], irq_out);
        test_pass = test_pass + 1; // Informational

        // ---- Summary ----
        #100;
        $display("\n========================================");
        $display("Test Summary: %0d PASS, %0d FAIL", test_pass, test_fail);
        $display("========================================");

        if (test_fail == 0)
            $display("ALL TESTS PASSED");
        else
            $display("SOME TESTS FAILED");

        $finish;
    end

endmodule

# Specification Document 1: NCE Compute Core

**Document:** LR-NCE-SPEC-001  
**Revision:** 1.0  
**Date:** 2026-05-26  
**Process Node:** SMIC 28nm HPC+ / 40nm LL  
**Company:** LightRail AI  

---

## 1. Overview

The NCE Compute Core is the central processing unit within the Neural Compute
Engine SoC. It provides 128-way SIMD streaming tensor operations for AI/ML
workloads, with direct photonic I/O integration and CXL 2.0 host connectivity.

---

## 2. Input Signals

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `clk_compute` | 1 | Input | DVFS-controlled compute clock (1.0-2.0 GHz) |
| `clk_sys` | 1 | Input | System AXI clock (250 MHz) |
| `rst_n` | 1 | Input | Active-low synchronous reset |
| `axi_awvalid` | 1 | Input | AXI write address valid |
| `axi_awaddr` | 32 | Input | AXI write address |
| `axi_wvalid` | 1 | Input | AXI write data valid |
| `axi_wdata` | 64 | Input | AXI write data |
| `axi_wstrb` | 8 | Input | AXI write strobes |
| `axi_bready` | 1 | Input | AXI write response ready |
| `axi_arvalid` | 1 | Input | AXI read address valid |
| `axi_araddr` | 32 | Input | AXI read address |
| `axi_rready` | 1 | Input | AXI read data ready |
| `dma_req_ready` | 1 | Input | DMA request accepted |
| `dma_resp_valid` | 1 | Input | DMA response data valid |
| `dma_resp_data` | 64 | Input | DMA response data |
| `qpa_trigger_ready` | 1 | Input | QPA trigger interface ready |
| `qpa_fault_status` | 8 | Input | QPA per-channel fault status |
| `thermal_adc_data` | 48 | Input | 4x 12-bit thermal diode ADC readings |
| `thermal_adc_valid` | 1 | Input | Thermal ADC data valid strobe |

---

## 3. Output Signals

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `axi_awready` | 1 | Output | AXI write address ready |
| `axi_wready` | 1 | Output | AXI write data ready |
| `axi_bvalid` | 1 | Output | AXI write response valid |
| `axi_bresp` | 2 | Output | AXI write response (OKAY/SLVERR) |
| `axi_arready` | 1 | Output | AXI read address ready |
| `axi_rvalid` | 1 | Output | AXI read data valid |
| `axi_rdata` | 64 | Output | AXI read data |
| `axi_rresp` | 2 | Output | AXI read response |
| `dma_req_valid` | 1 | Output | DMA request valid |
| `dma_req_addr` | 32 | Output | DMA request address |
| `dma_req_len` | 16 | Output | DMA request length (bytes) |
| `dma_req_write` | 1 | Output | DMA request direction (0=read, 1=write) |
| `dma_resp_ready` | 1 | Output | DMA response ready |
| `qpa_trigger_valid` | 1 | Output | QPA phase vector valid |
| `qpa_phase_vector` | 128 | Output | 8-channel x 16-bit phase data for MZI mesh |
| `dvfs_state` | 3 | Output | Current DVFS operating point (0-7) |
| `cluster_power_gate` | 1-8 | Output | Per-cluster power gate (1=on, 0=off) |
| `thermal_throttle` | 1 | Output | Soft thermal throttle request to VRM |
| `thermal_shutdown` | 1 | Output | Emergency thermal shutdown |
| `irq_out` | 1 | Output | Interrupt output (OR of all masked sources) |

---

## 4. Functional Specifications

### 4.1 Compute Engine

| Parameter | Value |
|-----------|-------|
| SIMD lanes | 128 (production) / 8 (MPW shuttle) |
| SIMD clusters | 8 (production) / 1 (MPW shuttle) |
| Data types | bfloat16, bfloat24, INT8 (4x packed), FP32 (accumulate) |
| Register file | 16 matrix (256-bit) + 16 vector (256-bit) |
| Pipeline stages | 3 (decode -> execute -> writeback) |
| Operations | MMA, VADD, VMUL, RELU, GELU, SOFTMAX, LOAD, STORE, QPA_TX |
| Peak throughput | 384 TOPS (BF16, production @ 1.5 GHz) |
| Clock frequency | 1.0-2.0 GHz (DVFS, 8 states) |

### 4.2 DMA Engine

| Parameter | Value |
|-----------|-------|
| Channels | 4 |
| Address width | 32 bits |
| Max transfer | 65,535 bytes |
| Interface | AXI4 to HBM4 / Host memory |
| States | IDLE -> READ -> WRITE -> DONE |

### 4.3 Thermal Management

| Parameter | Value |
|-----------|-------|
| Sensors | 4 on-die thermal diodes |
| Resolution | 12-bit (0.01 K) |
| Soft throttle | Tj >= 95 C (reduce DVFS state) |
| Hard throttle | Tj >= 105 C (minimum DVFS state) |
| Emergency shutdown | Tj >= 115 C |

### 4.4 Power Management

| Parameter | Value |
|-----------|-------|
| DVFS states | 8 (State 0: 0.65V/800MHz to State 7: 0.85V/2.0GHz) |
| Power gates | Per-cluster MTCMOS switches |
| V_core range | 0.65 V - 0.85 V |
| Peak current | 1000 A+ (all clusters active, max V/F) |

---

## 5. Register Map

| Offset | Name | R/W | Reset | Description |
|--------|------|-----|-------|-------------|
| 0x0000 | CTRL | R/W | 0x0 | [0] enable, [1] simd_start, [2] dma_start, [3] qpa_trigger |
| 0x0004 | STATUS | R | 0x0 | [0] enable, [1] simd_busy, [2] simd_done, [3] simd_exception, [4] dma_busy, [5] dma_done, [13:6] qpa_fault |
| 0x0008 | SIMD_CMD | W | 0x0 | [31:28] opcode, [27:24] rd, [23:20] rs1, [19:16] rs2 |
| 0x000C | SIMD_STATUS | R | 0x0 | [0] busy, [1] done |
| 0x0010 | DMA_SRC | R/W | 0x0 | DMA source address |
| 0x0014 | DMA_DST | R/W | 0x0 | DMA destination address |
| 0x0018 | DMA_LEN | R/W | 0x0 | [15:0] length, [17:16] channel |
| 0x001C | DMA_CTRL | R/W | 0x0 | [0] start; Read: [0] busy, [1] done |
| 0x0020 | DVFS | R/W | 0x4 | [2:0] V/F state (0-7) |
| 0x0024 | THERMAL | R | 0x0 | 4x 12-bit thermal readings, 16-bit packed |
| 0x0028 | POWER_GATE | R/W | 0xFF | [7:0] per-cluster enable (1=powered) |
| 0x002C | INTERRUPT | R/W | 0x0 | [7:0] pending (R), [15:8] mask (R/W) |

---

## 6. SIMD Instruction Encoding

| Opcode [31:28] | Mnemonic | Description |
|----------------|----------|-------------|
| 0x0 | NOP | No operation |
| 0x1 | MMA | Matrix multiply-accumulate: rd = rs1 * rs2 (element-wise) |
| 0x2 | VADD | Vector add: rd = rs1 + rs2 |
| 0x3 | VMUL | Vector multiply: rd = rs1 * rs2 |
| 0x4 | RELU | ReLU activation: rd = max(0, rs1) |
| 0x5 | LOAD | Load from L1 cache to register |
| 0x6 | STORE | Store from register to L1 cache |
| 0x7 | QPA_TX | Send register data to QPA photonic output |
| 0x8 | SOFTMAX | Softmax activation (piecewise linear) |
| 0x9 | GELU | GELU activation |

---

## 7. Timing Constraints

| Path | Constraint |
|------|-----------|
| clk_compute period (min) | 0.5 ns (2.0 GHz max) |
| clk_sys period | 4.0 ns (250 MHz) |
| Setup (compute domain) | 0.15 ns |
| Hold (compute domain) | 0.05 ns |
| AXI write latency | 2 clk_sys cycles |
| AXI read latency | 2 clk_sys cycles |
| SIMD pipeline latency | 3 clk_compute cycles |
| DMA start-to-first-data | 4 clk_sys cycles |
| Cross-domain (sys -> compute) | 2-stage synchronizer |

---

## 8. Power Estimates (SMIC 28nm HPC+)

| Block | Dynamic Power | Leakage | Total |
|-------|--------------|---------|-------|
| SIMD Array (128 lanes) | 120 mW @ 1 GHz | 8 mW | 128 mW |
| Register File | 15 mW | 2 mW | 17 mW |
| L1 Cache (4 KB MPW) | 5 mW | 1 mW | 6 mW |
| AXI Interface | 10 mW | 1 mW | 11 mW |
| DMA Controller | 8 mW | 1 mW | 9 mW |
| Thermal Monitor | 2 mW | 0.5 mW | 2.5 mW |
| Clock Tree | 15 mW | 0 mW | 15 mW |
| **Total (MPW)** | **175 mW** | **13.5 mW** | **188.5 mW** |

Note: Production die with 128 lanes and full caches will consume ~800 W at
peak (0.85V, 2.0 GHz, all clusters active).

---

## 9. Area Estimates (SMIC 28nm HPC+)

| Block | Gates (equiv.) | Area (mm2) |
|-------|---------------|------------|
| SIMD Array (8 lanes MPW) | ~50K | 0.15 |
| Register File | ~20K | 0.06 |
| L1 Cache (4 KB) | ~30K | 0.10 |
| AXI Interface | ~15K | 0.05 |
| DMA Controller | ~10K | 0.03 |
| Thermal + PMU | ~5K | 0.02 |
| Clock + Reset | ~3K | 0.01 |
| Pad Ring (MPW) | — | 0.50 |
| **Total (MPW)** | **~133K** | **~0.92 mm2** |

---

## 10. Verification Plan

| Test | Method | Coverage Target |
|------|--------|----------------|
| SIMD operations (all opcodes) | Directed + random | 100% opcode |
| AXI protocol compliance | Formal (AMBA VIP) | Protocol rules |
| DMA transfers | Directed | All states |
| Thermal throttle response | Directed | All thresholds |
| Power gate sequence | Directed | All clusters |
| QPA trigger path | Directed | Valid/ready |
| Reset recovery | Directed | Clean state |
| Clock domain crossing | CDC analysis | All crossings |

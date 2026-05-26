# Specification Document 3: QPA Trigger Matrix & System Integration

**Document:** LR-QPA-SPEC-001  
**Revision:** 1.0  
**Date:** 2026-05-26  
**Process Node:** SMIC 28nm HPC+ / 40nm LL  
**Company:** LightRail AI  

---

## 1. Overview

The Quantum Photonic Accelerator (QPA) Trigger Matrix is the real-time
control subsystem that bridges the NCE compute core with the TFLN photonic
mesh. It manages phase-vector programming of MZI arrays via CXL 2.0
memory-mapped registers, synchronizes DAC outputs with zero skew, monitors
optical health via SNSPD feedback, and provides telemetry to OpenBMC. This
document also covers system-level integration of all NCE subsystems.

---

## 2. Input Signals

### 2.1 Trigger Matrix (FPGA RTL — `tfln_qpu_trigger_matrix`)

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `clk_250mhz` | 1 | Input | 250 MHz system clock (from host FPGA PLL) |
| `rst_n` | 1 | Input | Active-low synchronous reset |
| `cxl_valid` | 1 | Input | CXL register write valid |
| `cxl_addr` | 64 | Input | CXL register address |
| `cxl_data` | 128 | Input | CXL write data (8ch x 16-bit phase) |
| `snspd_power_ok` | 8 | Input | Per-channel SNSPD optical power OK status |

### 2.2 LVDS Serializer (`tfln_dac_lvds_serializer`)

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `clk_500mhz` | 1 | Input | 2x system clock for DDR serialization |
| `clk_250mhz` | 1 | Input | System clock |
| `rst_n` | 1 | Input | Active-low synchronous reset |
| `dac_sync_trigger` | 1 | Input | From trigger matrix: commit signal |
| `dac_phase_bus` | 128 | Input | From trigger matrix: 8ch x 16-bit phase |

---

## 3. Output Signals

### 3.1 Trigger Matrix

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `cxl_ready` | 1 | Output | CXL interface ready to accept writes |
| `dac_sync_trigger` | 1 | Output | Zero-skew DAC commit pulse |
| `dac_phase_bus` | 128 | Output | 8-channel x 16-bit phase data to DACs |
| `telemetry_status` | 32 | Output | [31:16] fault_count, [15:0] trigger_count |
| `fault_interrupt` | 1 | Output | Optical fault interrupt to BMC |
| `channel_reroute` | 8 | Output | Per-channel reroute command to FPGA |

### 3.2 LVDS Serializer

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `lvds_data_p` | 8 | Output | LVDS data positive (8 channels) |
| `lvds_data_n` | 8 | Output | LVDS data negative (8 channels) |
| `lvds_sync_p` | 1 | Output | LVDS sync positive (frame marker) |
| `lvds_sync_n` | 1 | Output | LVDS sync negative (frame marker) |

---

## 4. Functional Specifications

### 4.1 Trigger Matrix Core

| Parameter | Value |
|-----------|-------|
| Channels | 8 |
| Phase resolution | 16-bit per channel |
| Phase range | 0 to 2*pi (0x0000 to 0xFFFF) |
| Update mechanism | Shadow buffer + atomic commit |
| Pipeline depth | 2 stages (shadow -> DAC, DAC -> sync) |
| Sync skew | Zero (single-cycle commit) |
| CXL interface | Memory-mapped registers |
| Clock | 250 MHz system clock |

### 4.2 CXL Register Map

| Offset | Name | R/W | Width | Description |
|--------|------|-----|-------|-------------|
| 0x1000 | PHASE_SET | W | 128-bit | Write phase vector to shadow buffer |
| 0x1004 | TRIGGER_EXEC | W | 1-bit | Atomic commit: shadow -> DAC bus + sync |
| 0x1008 | STATUS | R | 32-bit | [31:16] fault_count, [15:0] trigger_count |
| 0x100C | FAULT_MASK | R/W | 8-bit | Per-channel fault enable (1=monitored) |
| 0x1010 | TELEMETRY_CTRL | R/W | 1-bit | [0] telemetry_enable |

### 4.3 SNSPD Fault Detection

| Parameter | Value |
|-----------|-------|
| Detection method | 3 dB power drop (edge detect on snspd_power_ok) |
| Latency | 1 clock cycle |
| Fault latch | Sticky (cleared by reset only) |
| Fault mask | Per-channel programmable |
| Auto-reroute | Faulted channels routed to standby MZI paths |
| Interrupt | Pulse on first fault detection |

### 4.4 LVDS Serializer

| Parameter | Value |
|-----------|-------|
| Serialization | MSB-first, DDR (rising + falling edge) |
| Bit rate | 500 Mbps per LVDS lane (250 MHz DDR) |
| Frame length | 16 bits per channel (PHASE_WIDTH) |
| Frame sync | lvds_sync pulse at frame start |
| Differential standard | LVDS (100 Ohm, 3.5 mA) |
| Substrate | Megtron-7 (matched to PCB stackup) |

### 4.5 Telemetry

| Parameter | Value |
|-----------|-------|
| Interface | CXL MMIO -> OpenBMC via CXL BAR |
| Polling rate | 1 Hz (configurable) |
| Telemetry registers | See firmware `openbmc_tfln_telemetry.py` |
| Metrics | Temperature, V_pi drift, insertion loss, trigger count, fault count, channel status, MZI fidelity, laser temp |
| Fault thresholds | Insertion loss < -3.0 dBm, drift > 50 mV, laser temp > 350 K |

---

## 5. System Integration Specifications

### 5.1 NCE SoC Integration Block

```
+------------------------------------------------------------------+
|                     NCE SoC (BGA-2500)                            |
|                                                                    |
|  +---------------+  +------------------+  +-------------------+   |
|  | nce_compute   |  | tfln_optical     |  | tfln_qpu_trigger  |   |
|  | _core         |  | _engine          |  | _matrix           |   |
|  |               |  |                  |  |                   |   |
|  | SIMD + DMA    |  | TX/RX DSP + CDR  |  | Phase + Fault     |   |
|  | + Thermal     |  | + Laser + MZI    |  | + LVDS serializer |   |
|  +-------+-------+  +--------+---------+  +---------+---------+   |
|          |                   |                      |              |
|          +-------------------+----------------------+              |
|                              |                                     |
|                     AXI4 Interconnect (250 MHz)                    |
|                              |                                     |
|                     +--------+--------+                            |
|                     | PCIe Gen 6      |                            |
|                     | Root Complex    |                            |
|                     | + CXL 2.0       |                            |
|                     +-----------------+                            |
+------------------------------------------------------------------+
```

### 5.2 Board-Level Integration (LR-P3A)

| Interface | NCE Side | Board Side | Signal Count |
|-----------|----------|------------|-------------|
| PCIe Gen 6 | x32 (split x16+x16) | Edge connector + retimer | 144 balls |
| TFLN RF Drive | 16 diff pairs | TFLN PIC A/B electrodes | 96 balls |
| HBM4 Side-Channel | REFCK, JTAG, status | HBM4 module BGA | 32 balls |
| HBM4 Data Bus | 4096 lanes | Silicon interposer (internal) | — |
| V_CORE | 0.8V supply | 24-phase DrMOS array | 612 balls |
| GND | Ground reference | Board planes | 624 balls |
| Management | I2C, SPI, JTAG, PMBus | BMC / flash | 32 balls |
| Thermal | 4 diode pads | External ADC or direct | 4 balls |

### 5.3 QPA External Components

| Component | Ref Des | Function | Interface |
|-----------|---------|----------|-----------|
| FPGA (Trigger) | U401, U402 | QPA trigger matrix host | LVDS to DACs |
| DAC (100 GHz) | U411, U412 | Phase-to-voltage conversion | LVDS from FPGA |
| RF Driver | U421-U428 | Amplify DAC output to TFLN drive level | Analog |
| SNSPD | U431, U432 | Single-photon detection (quantum readout) | Digital output |
| Quantum Memory | U441, U442 | Optical quantum state storage | Control bus |
| CXL Switch | U450 | CXL 2.0 fabric switch | CXL lanes |

### 5.4 Clock Tree Integration

| Clock | Source | Frequency | Destination |
|-------|--------|-----------|-------------|
| REFCLK | Si5395A | 100 MHz | PCIe PHY, PLL input |
| SerDes REF | Si5395A | 156.25 MHz | TFLN SerDes PHY |
| HBM4 REFCK | Si5395A | 200 MHz | HBM4 stacks (per stack) |
| DAC Trigger | Si5395A | 10 MHz | QPA trigger sync |
| Compute | PLL2 (on-die) | 1.0-2.0 GHz | SIMD array |
| System | PLL0 (on-die) | 250 MHz | AXI fabric |
| DDR | PLL1 (on-die) | 500 MHz | LVDS serializer |

---

## 6. Power Budget (System Level)

| Subsystem | Typical | Peak |
|-----------|---------|------|
| NCE Compute (per die) | 400 W | 800 W |
| TFLN Optical Engine (per die) | 0.3 W | 0.5 W |
| QPA Controller (per die) | 0.1 W | 0.2 W |
| HBM4 (4 stacks per module) | 60 W | 100 W |
| I/O + Management | 40 W | 70 W |
| **Per NCE Module** | **~500 W** | **~971 W** |
| **Board Total (2 modules)** | **~1040 W** | **~2000 W** |

---

## 7. Verification Plan (System Integration)

| Test | Method | Coverage |
|------|--------|----------|
| NCE -> QPA data path | Directed | Phase vector -> DAC output |
| NCE -> TFLN TX path | Directed | Compute -> PAM4 optical output |
| TFLN RX -> NCE path | Directed | Optical input -> compute register |
| Full loopback (TX -> RX) | Self-checking | All channels, BER < 1e-12 |
| CXL register map | Formal + directed | All addresses, R/W permissions |
| Thermal throttle chain | Directed | Sensor -> throttle -> VRM -> PLL |
| Power gate sequence | Directed | Gate on/off per cluster |
| DMA HBM4 -> compute -> TFLN | End-to-end | Data integrity check |
| SNSPD fault -> reroute | Directed | All 8 channels |
| MZI compile -> verify | Directed | Fidelity > 97% |

---

## 8. MPW Shuttle Configuration

For the SMIC 28nm/40nm MPW shuttle, the system is partitioned into a
reduced test chip to validate key functionality within shuttle area
constraints (~4-9 mm2 reticle).

| Feature | Production | MPW Shuttle |
|---------|-----------|-------------|
| SIMD lanes | 128 | 8 |
| SIMD clusters | 8 | 1 |
| Optical channels | 8 TX + 8 RX | 1 TX + 1 RX |
| MZI mesh | 8x8 | 4x4 |
| L1 cache | 128 KB | 4 KB |
| L2 cache | 16 MB | 16 KB |
| L3 cache | 64 MB | None |
| HBM4 PHY | 4-stack | Test pattern gen |
| PCIe PHY | x32 Gen 6 | AXI4-Lite test port |
| Die size | ~10.5 x 10.5 mm | ~2.5 x 2.5 mm |
| Package | BGA-2500 | QFN-64 or wire-bond |
| V_core | 0.8 V, 1000 A | 0.9 V, < 1 A |

---

## 9. Design-for-Test (System Level)

| Feature | Implementation |
|---------|---------------|
| JTAG boundary scan | IEEE 1149.1 on all chip I/Os |
| IEEE 1500 wrappers | On each major block (compute, optical, QPA) |
| Scan chains | Full-scan, 64:1 compression |
| Memory BIST | March-C+ for all SRAM arrays |
| SerDes BIST | PRBS-31 loopback per channel |
| MZI mesh test | Identity matrix program -> verify output |
| Analog loopback | TX DAC -> RX ADC per channel |
| Production ATE | Advantest V93000 (digital + mixed-signal) |

---

## 10. Deliverable Summary

| # | Deliverable | File Path | Format |
|---|------------|-----------|--------|
| 1 | NCE Functional Breakdown | `docs/chip_design/NCE_Functional_Breakdown.md` | Markdown |
| 2 | NCE Block Diagram | `docs/chip_design/NCE_Block_Diagram.md` | Markdown (ASCII diagrams) |
| 3 | NCE Compute Core RTL | `rtl/nce_core/nce_compute_core.v` | Verilog |
| 4 | TFLN Optical Engine RTL | `rtl/tfln_optical_engine/tfln_optical_engine.v` | Verilog |
| 5 | QPA Trigger Matrix RTL | `rtl/tfln_qpu_trigger_matrix.v` | Verilog (existing) |
| 6 | LVDS Serializer RTL | `rtl/tfln_qpu_trigger_matrix.v` | Verilog (existing, same file) |
| 7 | Spec: NCE Compute Core | `docs/chip_design/Spec_01_NCE_Compute_Core.md` | Markdown |
| 8 | Spec: TFLN Optical Engine | `docs/chip_design/Spec_02_TFLN_Optical_Engine.md` | Markdown |
| 9 | Spec: QPA + Integration | `docs/chip_design/Spec_03_QPA_Trigger_Matrix.md` | Markdown |
| 10 | MPW Shuttle Plan | `docs/chip_design/MPW_Shuttle_Plan.md` | Markdown |
| 11 | KiCAD PCB/Schematic | `LightRail_LPO_1.6T.kicad_*` | KiCAD 8 |
| 12 | Gerber Package | `fab/Dual_NCE_Accelerator_Fab_Release_v1/` | Gerber X2 + Excellon |
| 13 | BOM | `fab/BOM.csv` | CSV |
| 14 | HDL Testbench | `rtl/nce_core/tb_nce_compute_core.v` | Verilog |
| 15 | HDL Testbench | `rtl/tfln_optical_engine/tb_tfln_optical_engine.v` | Verilog |

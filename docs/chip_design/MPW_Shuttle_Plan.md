# MPW Shuttle Plan — LightRail NCE + TFLN Test Chip

**Document:** LR-MPW-PLAN-001  
**Revision:** 1.0  
**Date:** 2026-05-26  
**Process:** SMIC 28nm HPC+ (primary) / SMIC 40nm LL (fallback)  
**Company:** LightRail AI  

---

## 1. Executive Summary

This document defines the Multi-Project Wafer (MPW) shuttle test chip plan
for validating the LightRail NCE (Neural Compute Engine) and TFLN Optical
Engine core IP before committing to a full production tapeout. The test chip
targets SMIC 28nm HPC+ via an MPW shuttle service (e.g., CMP/Europractice/
MOSIS) with a die area budget of approximately 4-9 mm2.

**Goals:**
1. Validate NCE compute cluster (8-lane SIMD subset) silicon functionality
2. Validate TFLN optical engine digital controller (2-channel subset)
3. Validate QPA trigger matrix + LVDS serializer
4. Characterize power, performance, and thermal behavior
5. Verify DFT infrastructure (scan, BIST, JTAG)
6. Provide silicon data for production tapeout sign-off

---

## 2. Shuttle Service Options

| Shuttle | Node | Die Size | Schedule | Notes |
|---------|------|----------|----------|-------|
| CMP (France) | SMIC 28nm HPC+ | 5x5 mm max | Q3 2026 | Academic pricing available |
| Europractice | SMIC 28nm/40nm | 5x5 mm max | Q4 2026 | EU-based, SMIC access |
| MOSIS | SMIC 40nm LL | 4x4 mm max | Quarterly | US-based, 40nm only |
| TinyTapeout | SMIC 130nm | 0.16x0.23 mm | Monthly | Not suitable (too coarse) |

**Recommended:** CMP or Europractice SMIC 28nm HPC+ shuttle for Q3/Q4 2026.

---

## 3. Test Chip Architecture

### 3.1 Die Floorplan

```
+-----------------------------------------------------------+
|                                                           |
|   +-------+  +------------------+  +------------------+  |
|   | PAD   |  |                  |  |                  |  |
|   | RING  |  |  NCE Compute     |  |  TFLN Optical    |  |
|   |       |  |  Core (8-lane)   |  |  Engine (2-ch)   |  |
|   | QFN-64|  |                  |  |                  |  |
|   | or    |  |  0.92 mm2        |  |  0.82 mm2        |  |
|   | wire  |  |                  |  |                  |  |
|   | bond  |  +------------------+  +------------------+  |
|   |       |                                              |
|   |       |  +------------------+  +------------------+  |
|   |       |  |  QPA Trigger     |  |  Test / Debug    |  |
|   |       |  |  Matrix + LVDS   |  |  Infrastructure  |  |
|   |       |  |                  |  |                  |  |
|   |       |  |  0.35 mm2        |  |  0.50 mm2        |  |
|   |       |  |                  |  |  (JTAG, BIST,    |  |
|   |       |  +------------------+  |   PLL, scan)     |  |
|   |       |                        +------------------+  |
|   |       |                                              |
|   +-------+  +---------------------------------------+  |
|              |       Power / Clock / Reset            |  |
|              |       0.30 mm2                          |  |
|              +---------------------------------------+  |
|                                                          |
|   Total die: ~2.5 x 2.5 mm = 6.25 mm2                   |
|   (fits CMP/Europractice 5x5 mm reticle)                |
+----------------------------------------------------------+
```

### 3.2 Block Area Budget

| Block | Area (28nm) | Area (40nm) | % of Die |
|-------|------------|------------|----------|
| NCE Compute Core (8-lane) | 0.92 mm2 | 1.50 mm2 | 14.7% |
| TFLN Optical Engine (2-ch) | 0.82 mm2 | 1.30 mm2 | 13.1% |
| QPA Trigger Matrix + LVDS | 0.35 mm2 | 0.60 mm2 | 5.6% |
| Test Infrastructure | 0.50 mm2 | 0.80 mm2 | 8.0% |
| Power / Clock / Reset | 0.30 mm2 | 0.45 mm2 | 4.8% |
| Pad Ring (QFN-64) | 2.50 mm2 | 3.00 mm2 | 40.0% |
| Routing overhead | 0.86 mm2 | 1.10 mm2 | 13.8% |
| **Total** | **6.25 mm2** | **8.75 mm2** | **100%** |

---

## 4. Reduced Feature Set (MPW vs. Production)

| Feature | Production | MPW Shuttle | Validation Goal |
|---------|-----------|-------------|-----------------|
| SIMD lanes | 128 | 8 (1 cluster) | Verify datapath, opcodes, pipeline |
| Matrix registers | 16 x 256-bit | 16 x 256-bit | Full register file |
| Vector registers | 16 x 256-bit | 16 x 256-bit | Full register file |
| L1 cache | 128 KB | 4 KB | Cache controller logic |
| L2 cache | 16 MB | 16 KB | Cache hierarchy |
| L3 cache | 64 MB | Omitted | Not on shuttle |
| Optical channels | 8 TX + 8 RX | 1 TX + 1 RX | Link training, CDR, DSP |
| MZI mesh | 8x8 | 4x4 | Mesh compiler, phase LUT |
| HBM4 PHY | 4-stack, 4096 lanes | Pattern gen/check | PHY validation stub |
| PCIe PHY | x32 Gen 6 | AXI4-Lite port | Host interface logic |
| CXL controller | Type 2 | Register-only stub | Register map validation |
| PRBS engine | 8-channel | 2-channel | BER testing |
| DMA engine | 4-channel | 2-channel | DMA controller logic |
| Thermal diodes | 4 | 2 | ADC interface, throttle logic |
| Power gates | 8 clusters | 1 cluster | Gate switch validation |
| DVFS | 8 states | 4 states | Voltage/frequency scaling |

---

## 5. I/O Plan (QFN-64 Package)

| Pin # | Signal | Direction | Type | Description |
|-------|--------|-----------|------|-------------|
| 1-4 | VDD_CORE | Power | 0.9V | Core power supply |
| 5-8 | VSS | Power | GND | Ground |
| 9-12 | VDD_IO | Power | 1.8V/3.3V | I/O power supply |
| 13 | CLK_SYS | Input | LVCMOS | 250 MHz system clock |
| 14 | CLK_SERDES | Input | LVDS+ | 156.25 MHz SerDes ref |
| 15 | CLK_SERDES_N | Input | LVDS- | SerDes ref complement |
| 16 | RST_N | Input | LVCMOS | Active-low reset |
| 17-24 | AXI_DATA[7:0] | Bidir | LVCMOS | AXI data (muxed) |
| 25-28 | AXI_ADDR[3:0] | Input | LVCMOS | AXI address (muxed) |
| 29 | AXI_WR | Input | LVCMOS | AXI write enable |
| 30 | AXI_RD | Input | LVCMOS | AXI read enable |
| 31 | AXI_READY | Output | LVCMOS | AXI ready |
| 32 | AXI_VALID | Output | LVCMOS | AXI valid |
| 33-34 | RF_DRIVE_P/N | Output | LVDS | TX channel 0 RF drive |
| 35-36 | PD_SIGNAL_P/N | Input | LVDS | RX channel 0 PD input |
| 37-40 | LVDS_DATA_P[3:0] | Output | LVDS | QPA LVDS data (4 lanes) |
| 41-44 | LVDS_DATA_N[3:0] | Output | LVDS | QPA LVDS data complement |
| 45 | LVDS_SYNC_P | Output | LVDS | QPA LVDS frame sync |
| 46 | LVDS_SYNC_N | Output | LVDS | QPA LVDS sync complement |
| 47 | SNSPD_OK | Input | LVCMOS | SNSPD power OK |
| 48 | LASER_EN | Output | LVCMOS | Laser enable |
| 49 | LASER_FAULT | Input | LVCMOS | Laser fault |
| 50 | TEC_PWM | Output | LVCMOS | TEC control PWM |
| 51 | IRQ_OUT | Output | LVCMOS | Interrupt output |
| 52 | THERMAL_THROTTLE | Output | LVCMOS | Thermal throttle |
| 53 | TCK | Input | LVCMOS | JTAG clock |
| 54 | TMS | Input | LVCMOS | JTAG mode select |
| 55 | TDI | Input | LVCMOS | JTAG data in |
| 56 | TDO | Output | LVCMOS | JTAG data out |
| 57 | TRST_N | Input | LVCMOS | JTAG reset |
| 58 | SCAN_EN | Input | LVCMOS | Scan chain enable |
| 59 | SCAN_IN | Input | LVCMOS | Scan chain input |
| 60 | SCAN_OUT | Output | LVCMOS | Scan chain output |
| 61-64 | SPARE[3:0] | Bidir | LVCMOS | Spare / debug |

---

## 6. Test Board Design

### 6.1 Test Board Requirements

| Parameter | Value |
|-----------|-------|
| Board size | 100 x 100 mm (4-layer) |
| Power supply | 0.9V core (LDO, 2A max), 1.8V I/O, 3.3V aux |
| Clock sources | 250 MHz oscillator, 156.25 MHz VCXO |
| JTAG | Standard 2x10 header |
| AXI interface | FPGA breakout (via Xilinx Artix-7 or similar) |
| RF connectors | 2x SMA (TX/RX loopback) |
| LVDS | 4-pair LVDS to external DAC evaluation board |
| Monitoring | Current sense on VDD_CORE, thermal via NTC |
| Debug | 16-pin logic analyzer header |
| Programming | SPI flash for FPGA bitstream |

### 6.2 Test Board Block Diagram

```
+-------------------+     +-----------------+
|  Host PC          |     | FPGA            |
|  (Python scripts) +---->| (Artix-7)       |
|                   | USB | - AXI master    |
+-------------------+     | - JTAG master   |
                          | - Pattern gen   |
                          +--------+--------+
                                   |
                            AXI + JTAG + LVDS
                                   |
                          +--------v--------+
                          |  DUT (NCE Test  |
                          |  Chip, QFN-64)  |
                          |                 |
                          +---+----+----+---+
                              |    |    |
                    RF_DRIVE  |    |    |  SNSPD_OK
                              v    |    v
                          SMA loop |  External SNSPD
                          back     |  emulator
                                   |
                              Thermal ADC
                              (external NTC)
```

---

## 7. Test Plan

### 7.1 Silicon Bring-Up (Week 1-2 after die arrival)

| Test # | Test Name | Equipment | Pass Criteria |
|--------|-----------|-----------|---------------|
| T1 | Power-on current | SMU (Keithley 2400) | I_core < 100 mA @ 0.9V |
| T2 | JTAG chain verify | FPGA JTAG master | ID code matches |
| T3 | Scan chain test | ATE / FPGA | All chains pass |
| T4 | PLL lock | Spectrum analyzer | Lock within 1 ms |
| T5 | Clock output verify | Oscilloscope | 250 MHz +/- 100 ppm |

### 7.2 Functional Validation (Week 3-6)

| Test # | Test Name | Method | Pass Criteria |
|--------|-----------|--------|---------------|
| F1 | AXI register R/W | FPGA pattern | All regs accessible |
| F2 | SIMD NOP | AXI + status read | busy -> done transition |
| F3 | SIMD VADD | AXI + verify | Correct sum in register |
| F4 | SIMD VMUL | AXI + verify | Correct product |
| F5 | SIMD MMA | AXI + verify | Correct MAC result |
| F6 | SIMD RELU | AXI + verify | Negative values zeroed |
| F7 | DMA transfer | FPGA pattern gen | Data integrity check |
| F8 | QPA phase set | AXI + LVDS capture | Correct phase on LVDS |
| F9 | QPA trigger | AXI + LVDS capture | Sync pulse + data |
| F10 | SNSPD fault inject | External signal | Fault latch + interrupt |
| F11 | Optical TX loopback | SMA cable | PRBS-31 BER < 1e-9 |
| F12 | CDR lock test | External clock | Lock within 50 us |
| F13 | MZI compile | AXI + verify | Fidelity > 95% |
| F14 | Thermal readout | NTC + ADC | Correct temperature |
| F15 | Thermal throttle | Heater + NTC | Throttle at threshold |

### 7.3 Characterization (Week 7-10)

| Test # | Test Name | Method | Measurement |
|--------|-----------|--------|-------------|
| C1 | Fmax (compute) | Freq sweep + SIMD | Max passing frequency |
| C2 | Fmax (LVDS) | Freq sweep + BER | Max LVDS data rate |
| C3 | Power vs frequency | SMU + freq sweep | mW/MHz curve |
| C4 | Power vs voltage | SMU + Vdd sweep | mW/mV curve |
| C5 | Shmoo plot | V/F matrix | Pass/fail boundary |
| C6 | Leakage vs temp | Oven + SMU | nA/um vs temperature |
| C7 | DVFS transition | FPGA + scope | Transition time, glitch |
| C8 | Power gate leakage | SMU (gated cluster) | Gated vs ungated |
| C9 | LVDS eye diagram | Scope (Keysight) | Eye height, width |
| C10 | Jitter measurement | Phase noise analyzer | RMS jitter |

---

## 8. Schedule

| Milestone | Target Date | Owner |
|-----------|-------------|-------|
| RTL freeze | 2026-06-15 | Design team |
| Synthesis + STA | 2026-07-01 | Backend team |
| DFT insertion | 2026-07-15 | DFT team |
| P&R + signoff | 2026-08-01 | Backend team |
| GDS submission to shuttle | 2026-08-15 | Tapeout lead |
| Shuttle fabrication | 2026-09-01 to 2026-11-30 | Foundry (SMIC) |
| Die delivery | 2026-12-01 | Foundry |
| Wire-bond / QFN packaging | 2026-12-15 | OSAT |
| Test board assembly | 2027-01-01 | PCB team |
| Silicon bring-up | 2027-01-15 | Validation team |
| Functional validation | 2027-02-15 | Validation team |
| Characterization complete | 2027-03-15 | Validation team |
| Production tapeout decision | 2027-04-01 | Program manager |

---

## 9. Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| SMIC 28nm shuttle unavailable | High | Medium | Fallback to SMIC 40nm LL |
| Die area exceeds reticle | Medium | Low | Reduce L1/L2 cache further |
| PLL fails to lock | High | Low | Include ring oscillator backup |
| LVDS eye closure | Medium | Medium | Include adjustable pre-emphasis |
| Thermal diode mismatch | Low | Medium | Calibrate via JTAG trim |
| JTAG chain break | High | Low | Include bypass MUX |
| Power grid IR drop | Medium | Medium | Multiple VDD/VSS pads |
| ESD failure | High | Low | Standard I/O ESD cells (2 kV HBM) |

---

## 10. Deliverables for Shuttle Submission

| # | Deliverable | Format | Status |
|---|------------|--------|--------|
| 1 | GDS-II layout | .gds | Pending (after P&R) |
| 2 | LEF/DEF | .lef / .def | Pending |
| 3 | Timing constraints (SDC) | .sdc | Pending |
| 4 | DRC clean report | .rpt | Pending |
| 5 | LVS clean report | .rpt | Pending |
| 6 | Antenna check report | .rpt | Pending |
| 7 | IR drop analysis | .rpt | Pending |
| 8 | STA signoff (all corners) | .rpt | Pending |
| 9 | Scan pattern (ATPG) | .stil | Pending |
| 10 | Pad ring coordinates | .csv | Pending |
| 11 | Bond diagram | .pdf | Pending |
| 12 | Test plan | This document | Complete |
| 13 | RTL source | .v | **Complete** |
| 14 | Testbenches | .v | **Complete** |
| 15 | Spec documents | .md | **Complete** |



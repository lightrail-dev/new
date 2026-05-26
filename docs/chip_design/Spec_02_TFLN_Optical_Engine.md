# Specification Document 2: TFLN Optical Engine Controller

**Document:** LR-TFLN-SPEC-001  
**Revision:** 1.0  
**Date:** 2026-05-26  
**Process Node:** SMIC 28nm HPC+ / 40nm LL  
**Company:** LightRail AI  

---

## 1. Overview

The TFLN Optical Engine Controller manages the complete photonic I/O datapath
for the LightRail LR-P3A compute node. It handles 8 bidirectional channels of
200 Gbps PAM4 optical communication through Thin-Film Lithium Niobate (TFLN)
Mach-Zehnder modulators, including TX/RX DSP, CDR, link training, laser
control, MZI mesh configuration, and BER testing.

---

## 2. Input Signals

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `clk_serdes` | 1 | Input | SerDes reference clock (156.25 MHz) |
| `clk_sys` | 1 | Input | System AXI clock (250 MHz) |
| `rst_n` | 1 | Input | Active-low synchronous reset |
| `axi_awvalid` | 1 | Input | AXI write address valid |
| `axi_awaddr` | 32 | Input | AXI write address |
| `axi_wvalid` | 1 | Input | AXI write data valid |
| `axi_wdata` | 64 | Input | AXI write data |
| `axi_wready` | — | — | (output, listed below) |
| `axi_bready` | 1 | Input | AXI write response ready |
| `axi_arvalid` | 1 | Input | AXI read address valid |
| `axi_araddr` | 32 | Input | AXI read address |
| `axi_rready` | 1 | Input | AXI read data ready |
| `tx_data_valid` | 1 | Input | TX data from compute cluster valid |
| `tx_data` | 512 | Input | TX data bus (8 channels x 64-bit) |
| `rx_data_ready` | 1 | Input | RX data consumer ready |
| `pd_signal_p` | 8 | Input | Photodetector positive signals (per channel) |
| `pd_signal_n` | 8 | Input | Photodetector negative signals (per channel) |
| `laser_fault` | 8 | Input | Per-laser fault indicators |
| `laser_power_mon` | 96 | Input | 8x 12-bit laser power monitor |
| `laser_temp_mon` | 96 | Input | 8x 12-bit laser temperature monitor |
| `snspd_power_ok` | 8 | Input | Per-channel SNSPD optical power OK |

---

## 3. Output Signals

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `axi_awready` | 1 | Output | AXI write address ready |
| `axi_wready` | 1 | Output | AXI write data ready |
| `axi_bvalid` | 1 | Output | AXI write response valid |
| `axi_bresp` | 2 | Output | AXI write response |
| `axi_arready` | 1 | Output | AXI read address ready |
| `axi_rvalid` | 1 | Output | AXI read data valid |
| `axi_rdata` | 64 | Output | AXI read data |
| `axi_rresp` | 2 | Output | AXI read response |
| `tx_data_ready` | 1 | Output | Ready to accept TX data |
| `rx_data_valid` | 1 | Output | RX data valid to consumer |
| `rx_data` | 512 | Output | RX data bus (8 channels x 64-bit) |
| `rf_drive_p` | 8 | Output | RF drive positive (to TFLN MZI electrodes) |
| `rf_drive_n` | 8 | Output | RF drive negative (to TFLN MZI electrodes) |
| `rf_bias_valid` | 1 | Output | RF bias tune data valid |
| `rf_bias_tune` | 96 | Output | 8x 12-bit bias tune voltages |
| `laser_enable` | 8 | Output | Per-laser enable |
| `laser_bias_current` | 96 | Output | 8x 12-bit laser bias DAC values |
| `tec_setpoint` | 96 | Output | 8x 12-bit TEC temperature setpoints |
| `mzi_phase_valid` | 1 | Output | MZI phase configuration valid |
| `mzi_phase_data` | 4096 | Output | MZI mesh phase data (16x16x16-bit) |
| `link_up` | 8 | Output | Per-channel link status |
| `cdr_locked` | 8 | Output | Per-channel CDR lock status |
| `irq_out` | 1 | Output | Interrupt output |

---

## 4. Functional Specifications

### 4.1 Optical Transceiver

| Parameter | Value |
|-----------|-------|
| Channels | 8 TX + 8 RX (production) / 2 (MPW) |
| Line rate | 200 Gbps PAM4 per lane |
| Modulation | PAM4 (4-level, 2 bits/symbol) |
| Wavelength | 1550 nm C-band DWDM |
| Channel spacing | 100 GHz |
| Aggregate bandwidth | 1.6 Tbps half-duplex, 3.2 Tbps full-duplex |
| Drive voltage | +/- 1.5 V differential, 50 Ohm SE / 100 Ohm diff |
| Interconnect energy | 5-10 pJ/bit |

### 4.2 TX DSP (per channel)

| Parameter | Value |
|-----------|-------|
| Feed-forward equalizer | 3-tap FFE |
| Coefficient width | 8-bit signed |
| Default taps | pre=0, main=63, post=0 |
| PAM4 encoding | Gray-coded 2-bit symbols |
| DAC resolution | Implied by SerDes analog |

### 4.3 RX DSP (per channel)

| Parameter | Value |
|-----------|-------|
| CTLE | 2-stage, 4-bit gain control (0-15) |
| Decision-feedback EQ | 7-tap DFE, 8-bit signed coefficients |
| ADC | Implied by SerDes analog |
| Oversampling | 2x |

### 4.4 Clock Data Recovery (CDR)

| Parameter | Value |
|-----------|-------|
| Type | Per-lane bang-bang CDR |
| Reference clock | 156.25 MHz |
| Jitter tolerance | 0.1 UI |
| Lock acquisition | ~1000 symbols typical |
| States | RESET -> ACQUIRE -> TRACK -> LOCKED / LOST |
| Lock indicator | Per-channel `cdr_locked` output |

### 4.5 Link Training

| Parameter | Value |
|-----------|-------|
| States | IDLE -> SIGNAL_DET -> CDR_LOCK -> EQ_TRAIN -> VERIFY -> ACTIVE |
| Auto-negotiation | Speed / modulation detection |
| Training sequence | PRBS-based equalization adaptation |
| Link-up indicator | Per-channel `link_up` output |
| Recovery | Automatic retrain on CDR loss |

### 4.6 Laser Driver Control

| Parameter | Value |
|-----------|-------|
| Channels | 8 (one DFB laser per optical channel) |
| Wavelength | 1550 nm |
| Laser type | DFB (Distributed Feedback) |
| Bias current DAC | 12-bit resolution |
| TEC setpoint DAC | 12-bit (default 25 C) |
| Laser power | 20 mW per channel |
| Fault detection | Over-temperature, over-current, loss-of-light |

### 4.7 MZI Mesh Controller

| Parameter | Value |
|-----------|-------|
| Mesh dimension | 4x4 (MPW) / 8x8 (production) |
| Phase resolution | 16-bit per MZI node |
| Phase LUT depth | 64 entries |
| Total MZI nodes | 6 (4x4) / 28 (8x8) |
| Compile states | IDLE -> LOAD -> COMPUTE -> OUTPUT -> DONE |
| Fidelity metric | 16-bit (0=worst, 65535=perfect) |
| Typical fidelity | ~97.6% (64000/65535) |

### 4.8 PRBS / BER Testing

| Parameter | Value |
|-----------|-------|
| PRBS order | 31 (PRBS-31, ITU-T O.150) |
| Polynomial | x^31 + x^28 + 1 |
| Error counter | 32-bit per channel |
| Modes | Generator only, Checker only, Both |
| Loopback | Electrical loopback (TX -> RX) |

---

## 5. Register Map

| Offset | Name | R/W | Reset | Description |
|--------|------|-----|-------|-------------|
| 0x2000 | OE_CTRL | R/W | 0x0 | [0] enable, [1] tx_enable, [2] rx_enable |
| 0x2004 | OE_STATUS | R | 0x0 | [7:0] link_up, [15:8] channel_fault |
| 0x2008 | TX_EQ | R/W | 0x003F00 | [23:16] pre, [15:8] main, [7:0] post (ch0) |
| 0x200C | RX_EQ | R/W | 0x8 | [3:0] CTLE gain (ch0) |
| 0x2010 | LASER_CTRL | R/W | 0x0 | [7:0] laser_enable, [27:16] bias_current |
| 0x2014 | LASER_STATUS | R | 0x0 | [7:0] laser_enable, [15:8] laser_fault |
| 0x2018 | MZI_CTRL | W | 0x0 | [0] compile_trigger |
| 0x201C | MZI_STATUS | R | 0x0 | [15:0] fidelity, [17] compile_done |
| 0x2020 | MZI_PHASE_BASE | W | 0x0 | Write phase LUT entry (auto-increment) |
| 0x2024 | OPT_POWER | R | 0x0 | 8x 8-bit normalized power readings |
| 0x2028 | BER_COUNTER | R | 0x0 | [31:0] ch0 errors, [63:32] ch1 errors |
| 0x202C | LOOPBACK | R/W | 0x0 | [0] loopback_mode |
| 0x2030 | CDR_STATUS | R | 0x0 | [7:0] cdr_locked per channel |
| 0x2034 | PRBS_CTRL | R/W | 0x0 | [0] gen_enable, [1] chk_enable |
| 0x2038 | WAVELENGTH | R/W | 0x0 | [7:0] DWDM ch#, [10:8] channel select |
| 0x203C | CROSSTALK | R/W | 0x0 | Crosstalk compensation coefficients |

---

## 6. Timing Constraints

| Path | Constraint |
|------|-----------|
| clk_serdes period | 6.4 ns (156.25 MHz) |
| clk_sys period | 4.0 ns (250 MHz) |
| RF drive setup | 0.2 ns before clk_serdes edge |
| RF drive hold | 0.1 ns after clk_serdes edge |
| CDR acquisition time | < 6400 clk_serdes cycles (~41 us) |
| Link training time | < 100 ms (all 5 states) |
| MZI compile latency | MZI_TOTAL_NODES + 3 clk_sys cycles |
| Cross-domain (serdes -> sys) | 2-stage synchronizer |
| Laser enable to power stable | < 1 ms (external) |
| TEC settle time | < 10 s (external, thermal mass) |

---

## 7. Optical Link Budget

| Parameter | Value |
|-----------|-------|
| Laser output power | +13 dBm (20 mW) |
| TFLN modulator insertion loss | -4 dB |
| Fiber coupling loss (MPO-24) | -1 dB |
| Fiber propagation loss | -0.2 dB/km x 2 km = -0.4 dB |
| Receiver coupling loss | -1 dB |
| Receiver sensitivity (PAM4) | -12 dBm (BER 1e-12) |
| **Link margin** | **+4.6 dB** |

---

## 8. Power Estimates (SMIC 28nm HPC+)

| Block | Dynamic Power | Leakage | Total |
|-------|--------------|---------|-------|
| TX DSP (8 channels) | 80 mW | 5 mW | 85 mW |
| RX DSP (8 channels) | 120 mW | 8 mW | 128 mW |
| CDR (8 channels) | 40 mW | 3 mW | 43 mW |
| Link Training FSM | 5 mW | 0.5 mW | 5.5 mW |
| Laser Driver Interface | 10 mW | 1 mW | 11 mW |
| MZI Mesh Controller | 15 mW | 2 mW | 17 mW |
| PRBS Gen/Check | 8 mW | 1 mW | 9 mW |
| AXI Interface | 10 mW | 1 mW | 11 mW |
| Clock Tree | 12 mW | 0 mW | 12 mW |
| **Total** | **300 mW** | **21.5 mW** | **321.5 mW** |

Note: MPW shuttle with 2 channels will consume ~100 mW.

---

## 9. Area Estimates (SMIC 28nm HPC+)

| Block | Gates (equiv.) | Area (mm2) |
|-------|---------------|------------|
| TX DSP (2 ch MPW) | ~30K | 0.09 |
| RX DSP (2 ch MPW) | ~45K | 0.14 |
| CDR (2 ch) | ~15K | 0.05 |
| Link Training | ~5K | 0.02 |
| Laser Interface | ~8K | 0.03 |
| MZI Controller | ~12K | 0.04 |
| PRBS | ~6K | 0.02 |
| AXI Interface | ~10K | 0.03 |
| Pad Ring (MPW) | — | 0.40 |
| **Total (MPW)** | **~131K** | **~0.82 mm2** |

---

## 10. Verification Plan

| Test | Method | Coverage Target |
|------|--------|----------------|
| TX/RX loopback | Directed | All channels |
| PAM4 encoding/decoding | Directed + random | All symbol levels |
| CDR lock/unlock | Directed | All FSM states |
| Link training sequence | Directed | All LT states |
| Laser enable/disable | Directed | All channels |
| MZI mesh compile | Directed | Full LUT + verify fidelity |
| PRBS-31 BER | Self-checking | 0 errors in loopback |
| AXI register access | Formal | AMBA protocol |
| Interrupt generation | Directed | All sources |
| Wavelength tuning | Directed | All DWDM channels |
| Cross-talk compensation | Directed | Adjacent channels |

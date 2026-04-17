# Simulation Scope: SI, PI, Thermal

The KiCad scaffold in this repo does **not** include any simulation results.
This document scopes the simulation work required before tape-out and lists
the tools, models, and artifacts a simulation team should produce.

## 1. Signal integrity (SI)

### 1.1 PCIe Gen 6 x16 (64 GT/s PAM4)

**Goal:** End-to-end channel meets PCIe 6.0 CEM receiver tolerancing.

| Item                         | Value / source                                                     |
| ---------------------------- | ------------------------------------------------------------------ |
| Simulator                    | Keysight ADS / Cadence Sigrity SystemSI / Ansys HFSS               |
| Channel model                | 3D EM (HFSS SIwave) for vias + fanout; 2D Q3D for long traces      |
| Package model                | From SoC vendor (IBIS-AMI 6.0 + package s4p)                        |
| Retimer model                | ASTERA PT6 / Montage Aries IBIS-AMI                                |
| Pass criteria                | EOH ≥ 20 mV, EOW ≥ 0.25 UI, BER 1e-12, statistical + time-domain    |
| Loss budget                  | ≤ 32 dB @ 16 GHz (Nyquist) edge → SoC                              |
| Corners                      | SS / TT / FF × PVT (V ± 5 %, T: 0 / 25 / 85 °C)                    |
| Output artifact              | `sim/si/pcie_gen6_channel_report.pdf`                              |

### 1.2 TFLN RF drive (200 Gbps PAM4 per lane, 16 lanes)

| Item                         | Value / source                                                     |
| ---------------------------- | ------------------------------------------------------------------ |
| Simulator                    | Ansys HFSS (3D full-wave) + ADS                                     |
| Frequency range              | 1 GHz – 80 GHz                                                     |
| Return loss                  | ≤ −12 dB up to 16 GHz                                              |
| Insertion loss               | ≤ 6 dB @ 16 GHz per diff pair (SoC driver → TFLN pad)              |
| Common-mode rejection        | ≥ 30 dB @ 16 GHz                                                   |
| Crosstalk (NEXT + FEXT)      | ≤ −25 dB within each 8-channel group                                |
| TFLN model                   | S-parameters from vendor (Lightmatter / HyperLight / Ayar)         |
| Output artifact              | `sim/si/tfln_rf_s_params.s16p`                                     |

### 1.3 DDR5-8800

| Item                         | Value / source                                                     |
| ---------------------------- | ------------------------------------------------------------------ |
| Simulator                    | Cadence Sigrity SystemSI + PowerSI                                  |
| Topology                     | Fly-by CA/CLK, point-to-point DQ                                   |
| Setup / hold margin          | > 0.1 UI across all corners                                        |
| SSN (simultaneous switching) | ≤ 150 mV / rail                                                    |
| Length match                 | ±0.05 mm per byte lane, ±2 mil across lanes                        |
| Output artifact              | `sim/si/ddr5_timing_report.xlsx`                                    |

### 1.4 REFCLK / SerDes reference

- Si5395A output phase noise ≤ −140 dBc/Hz @ 10 kHz offset.
- Integrated RMS jitter (10 kHz – 20 MHz) < 100 fs for PCIe REFCLK.
- Measure with Holzworth / Keysight E5052B; correlate with simulation.

## 2. Power integrity (PI)

### 2.1 V_core PDN

| Item                         | Value                                                              |
| ---------------------------- | ------------------------------------------------------------------ |
| Simulator                    | Ansys SIwave / Cadence PowerDC + PowerSI                            |
| DC IR drop                   | ≤ 10 mV @ 1000 A peak per SoC                                      |
| AC target Z                  | ≤ 0.5 mΩ from 10 kHz to 10 MHz                                     |
| Bulk cap                     | 10× 470 µF polymer + 20× 100 µF polymer per SoC                     |
| MLCC decoupling              | 200× 10 µF / 100× 1 µF / 300× 100 nF (0201/0402 mix) per SoC       |
| Via count (plane ↔ BGA)     | ≥ 1 via per 4 mA peak = ~250 vias per SoC V_core domain            |
| VRM loop bandwidth           | 200 kHz target; phase margin ≥ 45°                                 |
| Transient (di/dt = 200 A/µs) | V_core excursion ≤ ± 30 mV                                         |
| Output artifact              | `sim/pi/vcore_pdn_report.pdf`                                       |

### 2.2 Aux rails

- 3.3 V, 1.8 V, 1.2 V, 1.05 V, 0.9 V each simulated for IR drop and PDN Z.
- 1.1 V VDDQ + 1.8 V VPP: DDR5 DIMM load models included.

### 2.3 Decoupling strategy (by frequency)

| Frequency range          | Component                              | Placement                    |
| ------------------------ | -------------------------------------- | ---------------------------- |
| DC – 1 kHz               | Bulk polymer (470 µF)                  | Near VRM output              |
| 1 kHz – 100 kHz          | 100 µF polymer                         | Between VRM and SoC          |
| 100 kHz – 10 MHz         | 10 µF MLCC (0402)                      | SoC periphery                |
| 10 MHz – 100 MHz         | 1 µF MLCC (0201)                       | Under BGA (reverse side)     |
| 100 MHz – 1 GHz          | 100 nF MLCC (0201)                     | Between BGA via pairs         |
| > 1 GHz                  | Package decoupling (on-die)            | SoC package (vendor)         |

## 3. Thermal

### 3.1 Compute units

| Item                         | Value                                                              |
| ---------------------------- | ------------------------------------------------------------------ |
| Simulator                    | Ansys Icepak / 6SigmaET / Mentor FloTHERM                          |
| Model source                 | SoC vendor thermal model (`.rpt` + package + heat-spreader)         |
| Cold plate                   | Copper microchannel, 1.0 L/min water @ 40 kPa, 25 °C inlet         |
| Target Tj                    | ≤ 95 °C at 800 W TDP, ≤ 85 °C at 400 W typical                     |
| Contact resistance           | 0.05 K·cm²/W (TIM: Honeywell PTM7950)                              |
| Output artifact              | `sim/thermal/compute_unit_thermal_report.pdf`                      |

### 3.2 VRM array (24 phases × 2)

| Item                         | Value                                                              |
| ---------------------------- | ------------------------------------------------------------------ |
| Per-phase dissipation        | 3.5 W @ 42 A, V_in 12 V / V_out 0.8 V (efficiency ~93 %)           |
| Array total                  | 84 W per VRM × 2 = 168 W                                           |
| Cooling                      | 200 CFM board-level + heat-spreader strip over all 24 inductors     |
| Target inductor temp         | ≤ 105 °C at 55 °C inlet                                             |

### 3.3 TFLN PICs

- TEC-stabilized at 25 ± 2 °C.
- TEC power 15–20 W per PIC at 15 °C ambient delta.
- Thermal bypass to chassis cold plate via a short copper strap.

### 3.4 DDR5 DIMMs

- Airflow across the DIMM bank.
- Target Ta ≤ 85 °C at 5 W per module (DDR5-8800 RDIMM).

### 3.5 Whole-board CFD

- Inlet air 35 °C (front-panel side) / coolant 25 °C.
- Outlet air ≤ 55 °C / coolant ≤ 35 °C.
- Acoustic: fan PWM curve tuned for 45 dBA at idle, 65 dBA max.

## 4. Co-simulation

- **SI + PI:** Run PowerSI for PDN S-parameters + SystemSI channel sim
  with shared package model (SoC vendor `.s96p`). Target: no > 2 dB loss
  increase due to PI coupling.
- **PI + Thermal:** Chain PowerDC (IR drop → power map) → Icepak
  (temperature map) → update resistance → iterate until ΔT < 1 °C.

## 5. Simulation artifacts to commit

Do **not** commit raw simulator project files (often binary, GB-scale).
Commit only report PDFs and summary CSVs:

```
sim/
  si/
    pcie_gen6_channel_report.pdf
    pcie_gen6_eye_corners.csv
    ddr5_timing_report.xlsx
    tfln_rf_s_params.s16p
  pi/
    vcore_pdn_report.pdf
    vcore_ir_drop_map.csv
    aux_rails_pdn_summary.csv
  thermal/
    compute_unit_thermal_report.pdf
    whole_board_cfd_report.pdf
    vrm_thermal_map.csv
```

## 6. Sign-off criteria

| Domain     | Criterion                                                 | Owner |
| ---------- | --------------------------------------------------------- | ----- |
| SI PCIe    | All receiver masks pass margin ≥ 10 %                     | SI lead |
| SI DDR5    | Setup/hold margin > 0.1 UI at all corners                 | SI lead |
| SI TFLN    | Insertion loss ≤ 6 dB, CMRR ≥ 30 dB @ 16 GHz              | SI lead |
| PI V_core  | IR drop ≤ 10 mV; Z ≤ 0.5 mΩ in-band                       | PI lead |
| Thermal    | Tj ≤ 95 °C, TFLN at 25 °C ± 2 °C                          | Thermal lead |
| EMC        | Radiated Class A (pre-compliance)                          | Compliance |

Sign-off is a prerequisite for the tape-out gate in
`docs/Tapeout_Checklist.md` §0.

# LR-S1A 1U CPO Switch Motherboard — Rev 1.0 Design Package

| | |
|---|---|
| Programme | LR-S1A 1U Co-Packaged-Optics Switch |
| Revision | Rev 1.0 |
| Date | 2026-04-19 |
| Designer | LightRail AI — Design Automation |
| Outline | 440 × 550 mm 1U rack-mount motherboard |
| Aggregate throughput | 51.2 Tbps (256 × 200 G PAM4 lanes) |
| Switch ASIC | LR-CSW-51T2-A0 (TSMC N3, CoWoS-L) |
| CPO engines | 16 × LR-CPO-3T2-A0 (3.2 T per engine, silicon photonics) |
| Laser source | 8 × ELSFP CW (1310 nm DFB, hot-swap, front-panel) |
| Front-panel ports | 32 × OSFP-XD (224 G PAM4 × 8 lanes per port) |

## 1. System architecture

The LR-S1A is a 1U rack-mount Co-Packaged-Optics switch motherboard built around the LR-CSW-51T2 51.2 Tbps switch ASIC, with 16 co-packaged optical engines mounted on a shared silicon interposer immediately adjacent to the switch silicon. By co-packaging the optical engines with the switch ASIC, the SerDes electrical reach shrinks from front-panel-pluggable (≥ 100 mm) to interposer-trace (≤ 20 mm), reducing SerDes power by approximately 40 % at 224 G PAM4 line rate.

The Continuous-Wave (CW) laser sources are factored out of the CPO module and migrated to the front-panel as 8 ELSFP modules; this keeps the high-failure-rate DFB laser cavities in a field-replaceable form factor while keeping the modulator + receiver silicon adjacent to the ASIC. Laser light is delivered to the CPO engines via 8 internal SMF ribbon assemblies through SENKO SN-MT mid-board connectors.

Each of the 32 OSFP-XD front-panel cages carries 8 lanes × 224 G PAM4, providing 1.6 Tbps per port and 51.2 Tbps total. The OSFP-XD pluggables are passive copper or DSP-based active-optical, since the entire optical conversion stage is internal to the CPO engines.

## 2. Stackup and material set

The motherboard uses an 18-layer high-density-interconnect (HDI) stackup with three distinct dielectric materials:

- **Megtron-7** signal layers — low-loss substrate (Dk ≈ 3.4, Df ≈ 0.002 @ 10 GHz) for 224 G PAM4 SerDes routing
- **High-Tg FR-4** plane layers — standard reference / power planes
- **Faradflex BC24** embedded-capacitance core — distributed bypass between V_ASIC plane pair (In7-In8)

Finished board thickness 2.40 mm ± 10 %. ENIG + immersion-Ag surface finish. IPC-6012 Class 3 acceptance criteria.

## 3. Power delivery network

| Rail | Voltage | Peak Current | Phases | Regulator | Output Inductor |
|---|---|---|---|---|---|
| V_ASIC_0V85 | 0.85 V | 1,680 A | 24 | MPS MP86957 (70 A DrMOS) | 100 nH / 75 A |
| V_OPT_1V2 | 1.20 V | 480 A | 8 | MPS MP86957 (60 A DrMOS) | 150 nH / 60 A |
| V_AUX_3V3 | 3.30 V | 80 A | 4 | MPS MP2965 | 1 µH / 25 A |

The V_ASIC ring is the dominant PDN, delivering 1.43 kW to the switch ASIC at 0.85 V. Distributed embedded-capacitance bypass between In7-In8 (Oak-Mitsui Faradflex BC24, 24 nF/in² nominal) provides sub-100 ps loop-inductance decoupling between the ASIC core and the V_ASIC plane pair, supplementing the 96 × 10 µF bulk-decoupling ring around the ASIC body.

System power is delivered by 2 × CRPS-1U 3 kW Titanium power supplies (94 % efficient at 50 % load) configured as 1+1 redundant.

## 4. Signal integrity

- **OSFP-XD lanes** — 224 G PAM4 (112 GBaud), differential trace impedance 85 Ω ± 7 %, total channel insertion loss budget ≤ 28 dB at Nyquist (56 GHz)
- **CPO engine ↔ ASIC** — 224 G PAM4 over silicon-interposer (≤ 20 mm reach), no PCB SerDes hop
- **PCIe / management** — Gen 4 ×4 to control-plane daughterboard, 85 Ω differential
- **JTAG / I²C / SPI** — single-ended, no impedance control required

## 5. Thermal

| Heat source | Power | Cooling |
|---|---|---|
| LR-CSW-51T2 ASIC + CPO composite | 1.6 kW | Asetek CPC microchannel cold plate, liquid-cooled (quick-disconnect LQ4) |
| Daughterboard CPU | 250 W | Air-cooled (active heatsink) |
| DrMOS rings (24 + 8 + 4 phases) | 250 W | Air-cooled (PCB copper spreader + 7 × San Ace 40 fans) |
| Misc (PHY, BMC, peripherals) | 100 W | Air-cooled |

Liquid loop: 30 °C inlet, 4 L/min, 25 kPa pressure drop, < 5 K rise across the cold plate at 1.6 kW. Air loop: front-to-back, 7 × 40 × 28 mm Sanyo Denki San Ace counter-rotating fans, 250 CFM total at 25 mmH₂O.

## 6. Front-panel layout

- **Centre** — 8 × ELSFP CW laser modules (1310 nm DFB), orange pull-tabs, hot-swap
- **Left lower / left upper** — 16 × OSFP-XD ports (ports 1–16)
- **Right lower / right upper** — 16 × OSFP-XD ports (ports 17–32)
- **Far right** — RJ-45 OOB management, USB-A console, RJ-45 RS-232 console, status LEDs

## 7. Architectural BOM summary

| § | Section | Lines | Parts |
|---|---|---:|---:|
| 1 | Core processing & optical (CPO assembly) | 17 | ~100 |
| 2 | Optical routing & cable management | 10 | ~200 |
| 3 | Front-panel interfaces (I/O & lasers) | 14 | ~110 |
| 4 | Secondary circuitry & power delivery | 32 | ~1,800 |
| 5 | Chassis hardware | 17 | ~110 |
| **Total** | | **90** | **~2,320** |

Full BOM is in `BOM.csv` and the narrative is in `docs/LR-S1A_CPO_Switch_BOM.md`.

## 8. Standards and compliance

- **IPC-6012 Class 3** — printed-board acceptance
- **IPC-2221** — generic standard on printed-board design
- **IPC-2581 Rev C** — digital product-data exchange (included in this package)
- **IPC-A-610 Class 3** — assembly acceptance
- **IPC-7351** — surface-mount land patterns
- **JEDEC JESD238B / OIF-CEI-224G-LR** — 224 G PAM4 channel compliance

## 9. Deliverable manifest

See `FAB_READINESS_SIGNOFF.md` §6 for the complete deliverable manifest. Headlines:

- Native KiCad 8 PCB (schema 20240108)
- 27-layer Gerber RS-274X
- Excellon 2.0 drill (PTH + NPTH)
- IPC-2581 Rev C unified package
- STEP AP242 mechanical model
- 27 per-layer PDFs
- Fab + Assembly drawings (top + bottom)
- 2,320-part architectural BOM
- Pick-and-place CSV (both sides)
- DRC sign-off report (0 errors, IPC-6012 Class 3)

End of document.

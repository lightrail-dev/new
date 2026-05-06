# Stackup & Controlled Impedance (LR-P3A Rev 6.0)

## 1. 32-layer HDI stackup

Rev 6.0 migrates the board from the 10-layer Megtron-7 baseline to a
symmetric **32-layer HDI** stackup with three material systems:

| Domain                | Material             | εr   | tan δ (1 GHz) | Where used                                  |
|-----------------------|----------------------|------|---------------|---------------------------------------------|
| High-speed signal     | Panasonic Megtron-7  | 3.3  | 0.002         | All Megtron prepreg/core on signal layers   |
| Power / plane         | High-Tg FR-4 (Tg≥170) | 4.2  | 0.015         | In10..In14 & In17..In20 separation          |
| Embedded capacitance  | Faradflex BC24       | 14.0 | 0.02          | In15 ↔ In16 electrode sandwich (core)       |

The stackup is **symmetric about the mid-plane (between In15 and In16)**
for warpage control during reflow (spec §II — "symmetrical 32-layer
stackup"). All P/G prepreg/core thicknesses are ≤ 3 mil (76 µm) — well
under the `< 5 mil` requirement — so the V_CORE/GND plane pairs form a
distributed capacitance fabric in parallel with the central Faradflex
embedded-capacitance sandwich.

### 1.1 Layer-by-layer table

Thicknesses are `.kicad_pcb` nominals; fab selects exact prepreg
combinations to hit these values within ±10 %.

| #  | Layer   | Type   | Thickness | Material       | Role                                              |
|----|---------|--------|-----------|----------------|---------------------------------------------------|
|    | F.SilkS | silk   | —         | white epoxy    | top silkscreen                                    |
|    | F.Paste | paste  | —         | —              | top paste stencil                                 |
|    | F.Mask  | mask   | 0.010 mm  | LPI            | top soldermask                                    |
| 1  | F.Cu    | copper | 0.070 mm  | Cu (2 oz)      | NCE / TFLN / DrMOS fanout + PDN escape            |
|    | PP 1    | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 2  | In1.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref for F.Cu stripline                        |
|    | C 1     | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 3  | In2.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | HBM4 side-channel stripline (REFCK diff, JTAG)    |
|    | PP 2    | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 4  | In3.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | SerDes 100G PAM4 stripline (upper group)          |
|    | C 2     | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 5  | In4.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | PP 3    | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 6  | In5.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | PCIe Gen 6 diff stripline (upper group)           |
|    | C 3     | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 7  | In6.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | PP 4    | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 8  | In7.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | TFLN RF stripline (direct-drive, >100 GHz)        |
|    | C 4     | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 9  | In8.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | PP 5    | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 10 | In9.Cu  | copper | 0.0175 mm | Cu (0.5 oz)   | I²C / SPI / BMC management                        |
|    | C 5     | core   | 0.076 mm  | High-Tg FR-4   | **P/G spacing = 3 mil**                           |
| 11 | In10.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_CORE_U0 plane                                   |
|    | PP 6    | prepreg | 0.076 mm | High-Tg FR-4   | **P/G spacing = 3 mil**                           |
| 12 | In11.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_CORE_U0 plane (paralleled)                      |
|    | C 6     | core   | 0.076 mm  | High-Tg FR-4   | —                                                 |
| 13 | In12.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_CORE_U1 plane                                   |
|    | PP 7    | prepreg | 0.076 mm | High-Tg FR-4   | —                                                 |
| 14 | In13.Cu | copper | 0.070 mm  | Cu (2 oz)     | GND heavy plane                                   |
|    | C 7     | core   | 0.076 mm  | High-Tg FR-4   | —                                                 |
| 15 | In14.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_CORE_U1 plane (paralleled)                      |
|    | C 8     | core   | 0.024 mm  | Faradflex BC24 | **embedded-capacitance dielectric (εr = 14)**     |
| 16 | In15.Cu | copper | 0.035 mm  | Cu (1 oz)     | Faradflex BC24 electrode A — GND                  |
|    | C 9     | core   | 0.024 mm  | Faradflex BC24 | **embedded-capacitance dielectric (εr = 14)**     |
| 17 | In16.Cu | copper | 0.070 mm  | Cu (2 oz)     | Faradflex BC24 electrode B — V_AUX                |
|    | PP 8    | prepreg | 0.076 mm | High-Tg FR-4   | —                                                 |
| 18 | In17.Cu | copper | 0.070 mm  | Cu (2 oz)     | GND heavy plane                                   |
|    | C 10    | core   | 0.076 mm  | High-Tg FR-4   | —                                                 |
| 19 | In18.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_CORE_U0 plane mirror                            |
|    | PP 9    | prepreg | 0.076 mm | High-Tg FR-4   | —                                                 |
| 20 | In19.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_CORE_U1 plane mirror                            |
|    | C 11    | core   | 0.076 mm  | High-Tg FR-4   | —                                                 |
| 21 | In20.Cu | copper | 0.070 mm  | Cu (2 oz)     | V_AUX / HBM4 VDDC / VDDQL / VPP islands           |
|    | PP 10   | prepreg | 0.076 mm | High-Tg FR-4   | **P/G → signal domain transition**                |
| 22 | In21.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | C 12    | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 23 | In22.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | I²C / SPI / PMBus mirror                          |
|    | PP 11   | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 24 | In23.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | C 13    | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 25 | In24.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | TFLN RF stripline (Unit 1 mirror)                 |
|    | PP 12   | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 26 | In25.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | C 14    | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 27 | In26.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | PCIe Gen 6 diff stripline (lower group)           |
|    | PP 13   | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 28 | In27.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref                                           |
|    | C 15    | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 29 | In28.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | SerDes 100G PAM4 stripline (lower group)          |
|    | PP 14   | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 30 | In29.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | HBM4 side-channel stripline (mirror)              |
|    | C 16    | core   | 0.076 mm  | Megtron-7      | —                                                 |
| 31 | In30.Cu | copper | 0.0175 mm | Cu (0.5 oz)   | GND ref for B.Cu stripline                        |
|    | PP 15   | prepreg | 0.076 mm | Megtron-7      | —                                                 |
| 32 | B.Cu    | copper | 0.070 mm  | Cu (2 oz)     | Vertical power delivery — 24-phase DrMOS + caps   |
|    | B.Mask  | mask   | 0.010 mm  | LPI            | bottom soldermask                                 |
|    | B.Paste | paste  | —         | —              | bottom paste stencil                              |
|    | B.SilkS | silk   | —         | —              | bottom silkscreen                                 |

**Total nominal thickness:** 3.48 mm ± 10 % (≈ 137 mil)
**Copper weights:** 2 oz outer, 0.5 oz inner signal / GND reference,
2 oz inner power plane, 1 oz Faradflex electrode A.
**Finish:** ENIG per IPC-4552 Class 3 (Ni ≥ 3 µm, Au 0.05 µm min.).
**Soldermask:** LPI (black for thermal emissivity).
**Symmetric construction** around the In15–In16 embedded-capacitance
sandwich for low warpage on a 32-layer HDI panel. The Faradflex BC24
electrode pair is **intentionally asymmetric by copper weight**:

- **In15** (electrode A, GND return) is 1 oz (0.035 mm) — kept thin so
  the BC24 dielectric (εr = 14, 24 µm) dominates the plane-pair
  capacitance density. A thick electrode here adds series inductance
  on the return path and attenuates the mid-frequency (50–500 MHz)
  decoupling role of the embedded capacitor without improving DC
  performance.
- **In16** (electrode B, V_AUX — HBM4 VDDC / VDDQL / VPP return path)
  is 2 oz (0.070 mm) to carry the V_AUX domain current without IR
  drop.

Bow/twist budget is held to ≤ 0.75 % per IPC-6012 Class 3 by the
outer symmetry about the In15↔In16 midplane (In1…In14 mirrors
In17…In30 in both copper weight and dielectric choice — see rows above)
and by the balanced Megtron-7 / High-Tg FR-4 material distribution;
the 1 oz / 2 oz midplane electrode delta is a local CTE perturbation,
not a stackup-wide imbalance. Fabricator is to confirm bow/twist
≤ 0.75 % post-reflow on the qual coupon.

### 1.2 Key electrical properties

| Parameter                                    | Value                                    |
|----------------------------------------------|------------------------------------------|
| P/G plane pair spacing (In10↔In11, In13↔In14, …) | 0.076 mm (3 mil) — spec §II "≤5 mil"     |
| Distributed plane capacitance (per in²)      | ~0.5 nF (FR-4 core, 3 mil) + 4 nF (BC24 @ 1 mil) |
| Total in-board decoupling capacitance (420 cm² active area) | ≈ 4.9 µF (embedded) + 5.5 µF (plane-pair) = **≈ 10 µF** embedded |
| Stripline coupling (Megtron-7, 3 mil prepreg) | ~38 dB crosstalk floor at 10 mm parallel run |
| Skin-depth @ 30 GHz, Cu                      | 0.38 µm — well inside 0.5 oz copper     |
| Insertion loss budget, 25 Gbaud/lane SerDes  | ≤ 1.1 dB / in inner stripline            |

### 1.3 HBM4 PCB-side routing stays "side-channel only"

The HBM4 **2048-lane data bus** (11.7–13.0 Gbps/pin per spec §III, ~3.3
TB/s per stack) is contained entirely inside the vendor-supplied silicon
interposer co-packaged with the NCE. It never crosses a PCB copper
feature. Only the package-level side-channel signals cross onto PCB:

- Differential `REFCK_P/N` pair (up to 1.6 GHz reference clock)
- `CATTRIP`, `PWR_GOOD` (slow status)
- IEEE-1500 `TCK/TMS/TDI/TDO` test bus
- Per-stack power rails (`VDDC` / `VDDQL` / `VDDQ` / `VPP` / `VSS`)

These fit on In2.Cu / In29.Cu (fast stripline) and In9.Cu / In22.Cu
(slow I²C / JTAG). The 32-layer stackup is sized by the PDN +
TFLN / PCIe Gen 6 density, not by HBM4 escape.

## 2. Controlled-impedance table

| Net class          | Topology              | Trace W | Diff gap | Reference plane             | Target Z    | Tolerance |
|--------------------|-----------------------|---------|----------|-----------------------------|-------------|-----------|
| `SERDES_100G_PAM4` | stripline (In3/In28)  | 0.09 mm | 0.09 mm  | GND (In4/In27) / GND (In1/In30) | 100 Ω diff | ±5 %     |
| `PCIe_Gen6`        | stripline (In5/In26)  | 0.12 mm | 0.18 mm  | GND (In4/In27) / GND (In6/In25) | 85 Ω diff  | ±5 %     |
| `TFLN_RF`          | stripline (In7/In24)  | 0.15 mm | 0.20 mm  | GND (In6/In25) / GND (In8/In23) | 100 Ω diff | ±5 %     |
| `TFLN_ELEC_TRANSITION` | microstrip (F.Cu) | 0.09 mm | 0.127 mm | GND (In1)                   | 100 Ω diff  | ±5 %     |
| `RF_50OHM_DIFF`    | stripline (In3)       | 0.10 mm | 0.10 mm  | GND (In1) / GND (In4)       | 100 Ω diff  | ±5 %     |
| `HBM4_Interposer`  | stripline (In2/In29)  | 0.10 mm | 0.15 mm  | GND (In1/In30) / GND (In4/In27) | 100 Ω diff | ±5 %     |
| single-ended HBM4  | stripline (In2/In29)  | 0.10 mm | —        | GND (In1/In30) / GND (In4/In27) | 50 Ω SE    | ±5 %     |
| USB3 / USB4        | microstrip (F.Cu)     | 0.10 mm | 0.10 mm  | GND (In1)                   | 90 Ω diff   | ±10 %    |
| I²C / SPI / GPIO   | any                   | 0.15 mm | —        | GND                         | —           | —        |

Every high-speed class now has **GND-on-both-sides symmetric stripline**
(no asymmetric V_CORE reference) since the 32-layer stack frees up
enough GND reference planes for all signal groups — this is the primary
signal-integrity reason for the layer-count bump from Rev 5.0.

Request impedance coupons on every panel for Z-measurement sign-off
(fabs that routinely run this stackup: Sierra Circuits, TTM, AT&S, NCAB).

## 3. Via types & aspect ratios (IPC-6012 Class 3)

| Type         | Diameter | Drill   | Span                       | Aspect ratio | Used for                               |
|--------------|----------|---------|----------------------------|--------------|----------------------------------------|
| Microvia     | 0.20 mm  | 0.10 mm | F.Cu ↔ In1, In30 ↔ B.Cu    | 1:1 (laser)  | BGA breakout (NCE, TFLN, HBM4 module, DrMOS) |
| Buried       | 0.25 mm  | 0.125 mm| any 2-layer inner span     | ≤ 6:1        | Stripline → reference via              |
| Blind        | 0.25 mm  | 0.125 mm| F.Cu ↔ In3 / B.Cu ↔ In28   | ≤ 5:1        | High-speed escape                      |
| Signal PTH   | 0.30 mm  | 0.15 mm | through                    | **11.6:1**   | Mid-layer signal transitions           |
| Power PTH    | 1.20 mm  | 0.60 mm | through                    | 5.8:1        | V_CORE, V_12V, GND PDN bus bar         |
| Mounting     | 3.20 mm  | 3.20 mm | through (NPTH)             | 1:1          | M3 standoff                            |

**Aspect ratio budget:** The through-via minimum drill is 0.30 mm, which
on the 3.48 mm nominal board gives 11.6:1 — comfortably inside the
IPC-6012 Class 3 `≤ 12:1` ceiling for pulse-plate copper (spec §II).
Any smaller drill (e.g. 0.25 mm via stub) must be a buried or blind via
that does not span the full stack. The DRC rule
`through_via_min_drill_aspect_ratio` in `fab/drc_custom.kicad_dru`
enforces this.

**Minimum hole-wall copper:** 20 µm after plating, tested on every
panel via microsection coupon (spec §VI HDI fab rules). Covered by
`annular_ring_class3` + fab agreement on pulse-plate process.

## 4. Back-drill table (spec §II — residual stub ≤ 5 mil)

Back-drill is required on every through-via that carries a high-speed
signal where the used-span + 5 mil would otherwise leave a resonant
stub visible in the S-parameter response. Fab cuts the unused portion
of the barrel from whichever side leaves the shortest stub.

| Net class           | Normal span   | Back-drill from | Target depth        | Residual stub |
|---------------------|---------------|-----------------|---------------------|---------------|
| `SERDES_100G_PAM4`  | F.Cu → In28   | B.Cu side       | through → In29      | ≤ 0.127 mm    |
| `PCIe_Gen6`         | F.Cu → In26   | B.Cu side       | through → In27      | ≤ 0.127 mm    |
| `TFLN_RF` U0        | F.Cu → In7    | B.Cu side       | through → In8       | ≤ 0.127 mm    |
| `TFLN_RF` U1        | F.Cu → In24   | B.Cu side       | through → In25      | ≤ 0.127 mm    |
| `HBM4_Interposer`   | F.Cu → In29   | B.Cu side       | through → In30      | ≤ 0.127 mm    |
| `RF_50OHM_DIFF`     | F.Cu → In3    | B.Cu side       | through → In4       | ≤ 0.127 mm    |

The fab records residual stub for each back-drilled via on the fab
drawing in microsection-coupon form. The DRC rule
`backdrill_required_high_speed` flags any through-via in these classes
so routing review can confirm back-drill is requested in the fab note.

## 5. Solder mask & silkscreen

- **Mask dam:** 0.05 mm min between pads; 0.05 mm clearance around BGA.
- **Mask expansion:** ≥ 0.05 mm (2 mil) per side on every pad
  (`soldermask_expansion_min` DRC rule — spec §V).
- **Paste:** 80 % area pad ratio on thermal pads; 100 % on QFN ground.
- **Silk:** ≥ 0.8 mm text height, ≥ 0.12 mm stroke; no silk over copper
  (`silk_over_copper` DRC rule).

## 6. Fabrication tolerances

| Parameter                       | Target               |
|---------------------------------|----------------------|
| Trace width (inner)             | ±10 % or ±0.025 mm   |
| Hole location                   | ±0.05 mm             |
| Layer-to-layer registration     | ±0.05 mm             |
| Board thickness                 | ±10 %                |
| Impedance (diff / SE, coupon)   | ±5 % (RF-critical classes) |
| Copper weight variation         | ±10 %                |
| Min hole-wall copper            | ≥ 20 µm (IPC-6012 C3) |
| Residual back-drill stub        | ≤ 0.127 mm (5 mil)   |
| Plane dielectric spacing        | ≤ 0.076 mm (3 mil)   |

## 7. Test coupons

Include on every panel:

- **Impedance coupon** — 4 pairs per impedance target (diff + SE), per
  IPC-TM-650 2.5.5.7.
- **Microsection coupon** — plating thickness verification (≥ 20 µm
  hole wall, IPC-A-600 Class 3).
- **D-coupon** (IPC-4761) — via integrity (HAST / IST thermal cycling).
- **Back-drill stub coupon** — one per high-speed net class, depth
  measured per IPC-2221 §4.3.2.
- **CAF coupon** — conductive-anodic-filament resistance under
  humidity + bias (essential for 0.3 mm drill + 3 mil P/G).

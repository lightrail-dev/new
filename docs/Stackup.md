# Stackup & Controlled Impedance

## 1. 10-layer Megtron-7 stackup (as scaffolded)

> **Scaffold note.** The KiCad file declares a symmetric 10-layer stackup with
> Megtron-7 core + prepreg. A production Compute Node at this performance tier
> typically needs 20–26 layers with dedicated reference planes for each
> high-speed pair. The table below describes what the repo contains today and
> the target stackup for tape-out.

### 1.1 Current scaffold (from `.kicad_pcb`)

| # | Layer      | Type        | Thickness | Material     | εr / tan δ   | Role                             |
|---|------------|-------------|-----------|--------------|--------------|----------------------------------|
|   | F.SilkS    | silk        | —         | —            | —            | top silkscreen                   |
|   | F.Paste    | paste       | —         | —            | —            | top paste stencil                |
|   | F.Mask     | mask        | 0.010 mm  | LPI          | —            | top soldermask                   |
| 1 | F.Cu       | copper      | 0.070 mm  | Cu (2 oz)    | —            | SIG: PCIe/TFLN RF + BGA fanout   |
|   | PP1        | prepreg     | 0.099 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 2 | In1.Cu     | copper      | 0.0175 mm | Cu (0.5 oz)  | —            | GND reference (solid)            |
|   | C1         | core        | 0.200 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 3 | In2.Cu     | copper      | 0.0175 mm | Cu (0.5 oz)  | —            | SIG: DDR5 byte lanes 0–1         |
|   | PP2        | prepreg     | 0.099 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 4 | In3.Cu     | copper      | 0.070 mm  | Cu (2 oz)    | —            | V_CORE_U0 plane                  |
|   | C2         | core        | 0.200 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 5 | In4.Cu     | copper      | 0.070 mm  | Cu (2 oz)    | —            | V_CORE_U0 plane (split)          |
|   | PP3        | prepreg     | 0.099 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 6 | In5.Cu     | copper      | 0.070 mm  | Cu (2 oz)    | —            | V_CORE_U1 plane                  |
|   | C3         | core        | 0.200 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 7 | In6.Cu     | copper      | 0.070 mm  | Cu (2 oz)    | —            | V_CORE_U1 plane (paralleled)     |
|   | PP4        | prepreg     | 0.099 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 8 | In7.Cu     | copper      | 0.0175 mm | Cu (0.5 oz)  | —            | GND reference (solid)            |
|   | C4         | core        | 0.200 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
| 9 | In8.Cu     | copper      | 0.0175 mm | Cu (0.5 oz)  | —            | SIG: aux I/O, PMBus, SPI         |
|   | PP5        | prepreg     | 0.099 mm  | Megtron-7    | 3.3 / 0.002  | —                                |
|10 | B.Cu       | copper      | 0.070 mm  | Cu (2 oz)    | —            | SIG: NVMe, fanout, decoupling    |
|   | B.Mask     | mask        | 0.010 mm  | LPI          | —            | bottom soldermask                |
|   | B.Paste    | paste       | —         | —            | —            | bottom paste stencil             |
|   | B.SilkS    | silk        | —         | —            | —            | bottom silkscreen                |

**Total nominal thickness:** 1.81 mm ± 10 %
**Copper weight:** 2 oz outer / 0.5 oz inner signal & GND references / 2 oz V_core planes (symmetric about stack center for bow/twist control)
**Finish:** ENIG (2 µm Au min. over 5 µm Ni)
**Soldermask:** LPI, green (default); matte black available

> **DDR5 byte lanes 2–3 in the 10-layer scaffold** are planned for outer
> (B.Cu) + In8.Cu stripline-like routing in the scaffold. A genuine
> tape-out build must adopt the 22–24 layer target in §1.2 where each
> DDR5 byte lane has its own dedicated stripline between two GND planes.

### 1.2 Tape-out target stackup (recommended)

For 1000 A V_core + 32 DDR5 DIMM + PCIe Gen 6 + TFLN RF, a realistic
production stackup is 22–24 layers along these lines:

- 4× dedicated V_core planes (each 2 oz, ~8 oz total for <1 mΩ AC PDN)
- 4× GND reference planes (one per signal cluster)
- 6–8× signal layers split between DDR5 (stripline pairs) and PCIe/TFLN
  (stripline pairs with dedicated GND reference on each side)
- Buried capacitance layer (Faradflex or equivalent) across one core for
  bulk decoupling
- M6 prepreg on inner high-speed layers for lower insertion loss at 16 GHz
- Megtron-7N or Megtron-8 for outer RF-critical cores if full-link loss
  budget requires it

## 2. Controlled-impedance table

Impedance targets for the stackup in §1.1, assumed trace geometry
(stripline on In2/In8, microstrip on F.Cu/B.Cu) at 20 °C. All widths and
gaps are **design intents** — the fab will reconcile with their own
coupon-measured εr and tolerance.

| Net class          | Topology    | Trace W | Diff gap | Reference plane | Target Z  | Tolerance |
| ------------------ | ----------- | ------- | -------- | --------------- | --------- | --------- |
| `SERDES_100G_PAM4` | stripline   | 0.09 mm | 0.09 mm  | GND (In1/In3)   | 100 Ω diff | ±10 %    |
| `PCIe_Gen6`        | stripline   | 0.12 mm | 0.18 mm  | GND (In1/In3)   | 85 Ω diff  | ±10 %    |
| `TFLN_RF`          | microstrip  | 0.15 mm | 0.20 mm  | GND (In1)       | 100 Ω diff | ±7 %     |
| `RF_50OHM_DIFF`    | stripline   | 0.10 mm | 0.10 mm  | GND (In1/In3)   | 100 Ω diff | ±10 %    |
| `DDR5_Data`        | stripline   | 0.10 mm | 0.15 mm  | GND (In1/In3)   | 80 Ω diff  | ±10 %    |
| single-ended DDR5  | stripline   | 0.10 mm | —        | GND (In1/In3)   | 40 Ω SE    | ±10 %    |
| USB3 / USB4        | microstrip  | 0.10 mm | 0.10 mm  | GND (In1)       | 90 Ω diff  | ±10 %    |
| I²C / SPI / GPIO   | any         | 0.15 mm | —        | GND             | —          | —         |

Refer to the fab's impedance control capabilities (e.g. Sierra Circuits, TTM,
AT&S, NCAB). Request coupons on every panel for Z-measurement sign-off.

## 3. Via types

| Type         | Diameter | Drill  | Aspect ratio | Used for                            |
| ------------ | -------- | ------ | ------------ | ----------------------------------- |
| Microvia     | 0.20 mm  | 0.10 mm | 1:1         | BGA breakout (SoC, TFLN PIC, DrMOS) |
| Standard PTH | 0.30 mm  | 0.15 mm | ~10:1       | Signal & small power                |
| Power PTH    | 0.80 mm  | 0.40 mm | ~4:1        | V_core, 12 V                        |
| Mounting hole| 3.20 mm  | 3.20 mm | —           | M3 mechanical (no plating)          |

## 4. Solder mask & silkscreen

- **Mask**: 0.05 mm dam between pads; 0.05 mm clearance around BGA pads.
- **Paste**: 80 % area pad ratio on thermal pads; 100 % on QFN ground.
- **Silk**: ≥0.8 mm text height, ≥0.12 mm stroke; no silk over copper.

## 5. Fabrication tolerances

| Parameter                       | Target           |
| ------------------------------- | ---------------- |
| Trace width (inner)             | ±10 % or ±0.025 mm |
| Hole location                   | ±0.05 mm         |
| Layer-to-layer registration     | ±0.05 mm         |
| Board thickness                 | ±10 %            |
| Impedance (diff/SE, coupon)     | ±10 % (RF ±7 %)  |
| Copper weight variation         | ±10 %            |

## 6. Test coupons

Include on every panel:

- **Impedance coupon:** 4 pairs per impedance target (diff + SE).
- **Microsection coupon:** for plating thickness verification.
- **D-coupon (IPC-4761):** via integrity (HAST / IST).

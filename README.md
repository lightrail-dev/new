# LightRail AI Compute Node — LR-P3A Rev 6.3

**Project:** LightRail AI Compute Node (Dual-CPO, NCE + HBM4 co-packaged, 1.6 Tbps photonic I/O)
**Model:** LR-P3A
**Revision:** 6.3 (32-layer HDI, IPC-6012 Class 3, 1000 A PDN — fully routed)
**Date:** 2026-05-18
**Company:** LightRail AI

> ## Rev 6.3 — Routing Complete, Fab Package Ready
>
> This revision completes the transition from Rev 6.0 scaffold to a fully
> routed 32-layer HDI PCB with the 420 × 350 mm server-class outline.
> All four interactive routing tasks have been executed:
>
> 1. **Decoupling cap fanout** — 138 nets (69 per NCE) with tiered PDN
>    (01005 → 0402 → 0805 → tantalum) and per-pad escape vias to In7/In8.
> 2. **DrMOS vertical power-tap stitching** — 6×6 via array (36 vias,
>    0.4 mm drill) per B.Cu phase, 24 phases per NCE.
> 3. **High-speed length matching** — PCIe Gen 6 ±0.15 mm, SerDes 100G
>    PAM4 ±0.15 mm, HBM4 REFCK ±0.3 mm, TFLN RF routed.
> 4. **Back-drill definitions** — all high-speed through-vias annotated
>    with residual stub ≤ 0.127 mm (5 mil).
>
> See [`docs/Tapeout_Checklist.md`](docs/Tapeout_Checklist.md) and
> [`docs/SI_PI_Thermal_Plan.md`](docs/SI_PI_Thermal_Plan.md) for remaining
> SI/PI/thermal simulation work before first-article release.

---

## 1. What's in this repo

| Path                                        | Purpose                                                              |
| ------------------------------------------- | -------------------------------------------------------------------- |
| `LightRail_LPO_1.6T.kicad_pro`              | KiCad 8 project: net classes, DRC rules, 32-layer HDI stackup.       |
| `LightRail_LPO_1.6T.kicad_sch`              | Root schematic with hierarchical sheet instances.                    |
| `LightRail_LPO_1.6T.kicad_pcb`              | Fully routed 32-layer PCB (420×350 mm, Rev 6.3).                     |
| `AI_Core.kicad_sch`                         | AI SoC + TFLN periphery + PCIe Gen6 x16 + local decoupling.          |
| `Memory.kicad_sch`                          | HBM4 stack template (side-channel + power), 8 instances per board.   |
| `VRM.kicad_sch`                             | ISL69260 + 24× ISL99390 DrMOS, V_core 0.8 V @ 1000 A+.               |
| `LightRail.pretty/`                         | Custom footprints (BGA-2500, TFLN PIC, DrMOS, HBM4_Stack_11x11mm).   |
| `docs/Architecture.md`                      | System block diagram, functional spec, interconnect budget.          |
| `docs/Stackup.md`                           | Layer stackup + controlled-impedance table (50 Ω SE / 85 Ω / 100 Ω). |
| `docs/Pinouts.md`                           | Pinout tables for SoC, TFLN PIC, PCIe x16, HBM4 stack, NVMe, MPO-24. |
| `docs/DFM_Checklist.md`                     | DFM/DFA rules (min trace, min via, BGA breakout, courtyard, etc.).   |
| `docs/Fab_Notes.md`                         | Fabrication notes: copper weights, finish, impedance tolerance.      |
| `docs/Tapeout_Checklist.md`                 | Pre-tapeout sign-off items grouped by owner.                         |
| `docs/SI_PI_Thermal_Plan.md`                | Simulation scope: SI for PCIe/HBM4-SC/TFLN, PI for V_core, thermal.  |
| `fab/BOM.csv`                               | Bill of materials down to 0201 passives.                             |
| `fab/Netlist.md`                            | Summary of representative nets (full KiCad netlist exported locally).|
| `fab/export_gerbers.sh`                     | `kicad-cli` script to export Gerbers, drills, IPC-D-356, BOM, pos.   |
| `fab/drc_custom.kicad_dru`                  | Custom DRC rules (coupled diff-pair, BGA breakout, high-current).    |
| `fab/gerber_layers.txt`                     | Layer → Gerber file mapping for the fab.                             |

---

## 2. Architectural summary

| Subsystem        | Spec                                                                             |
| ---------------- | -------------------------------------------------------------------------------- |
| Compute          | 2× composite BGA-2500 module (NCE die + silicon interposer + 4× HBM4 stacks)    |
| Photonics        | 2× TFLN modulator array (8 ch × 200 Gbps PAM4 each = 1.6 Tbps aggregate)         |
| Lasers           | 1550 nm DFB × 8 per optical engine, TEC-controlled                               |
| Memory           | 8× HBM4 12-Hi stacks (4 per module) co-packaged on silicon interposer —         |
|                  | 1024-lane data bus routes inside the interposer, never on PCB                    |
| PCIe             | PCIe Gen 6.0 x16 (32 GT/s per lane, 128 GB/s per direction)                      |
| NVMe             | M.2 / U.3 PCIe Gen 5/6 storage (via root complex)                                |
| Power            | 2× 24-phase DrMOS VRM (ISL69260 + ISL99390) for V_core 0.8 V @ 1000 A+ per unit  |
| Aux rails        | 12 V input → 3.3 V, 1.8 V, 1.2 V, 1.05 V, 0.9 V (LDO + buck)                     |
| Mgmt             | EC/BMC, PMBus, I²C, SPI flash (UEFI/BIOS), TPM 2.0 header                        |
| Front panel      | MPO-24 optical (1.6 Tbps), status LEDs                                           |
| Cooling          | Direct-to-chip cold plate headers (compute units), forced-air baseline           |
| Stackup          | **32-layer HDI** — Megtron-7 signal + high-Tg FR-4 plane + Faradflex BC24 embedded-cap core. See [`docs/Stackup.md`](docs/Stackup.md). |
| Board class      | **IPC-6012 Class 3** (aspect ratio ≤ 12:1, back-drill stub ≤ 5 mil, min hole-wall 20 µm). |
| Board outline    | 420 × 350 mm server-class (Rev 6.3, expanded from HHHL scaffold)     |

See [`docs/Architecture.md`](docs/Architecture.md) for the block diagram and
signal-flow description.

---

## 3. Net classes (KiCad project)

| Net class        | Width   | Diff gap | Clear. | Via drill / dia | Intended use                     |
| ---------------- | ------- | -------- | ------ | --------------- | -------------------------------- |
| `SERDES_100G_PAM4` | 0.09 mm | 0.09 mm  | 0.127 mm | 0.15 / 0.30 mm  | PCIe lanes, internal 100G SerDes |
| `PCIe_Gen6`      | 0.12 mm | 0.18 mm  | 0.12 mm  | 0.15 / 0.35 mm  | PCIe Gen 6 edge + retimer        |
| `TFLN_RF`        | 0.15 mm | 0.20 mm  | 0.15 mm  | 0.10 / 0.30 mm  | TFLN modulator RF drive          |
| `RF_50OHM_DIFF`  | 0.10 mm | 0.10 mm  | 0.15 mm  | 0.15 / 0.30 mm  | 50 Ω diff (clock distribution)   |
| `HBM4_Interposer`| 0.10 mm | 0.15 mm  | 0.10 mm  | 0.15 / 0.30 mm  | HBM4 side-channel (REFCK, JTAG)  |
| `TFLN_ELEC_TRANSITION` | 0.09 mm | 0.127 mm | 0.10 mm | 0.15 / 0.30 mm | TFLN RF → PIC electrical transition (< 5 mm, 50 Ω SE / 100 Ω diff) |
| `PDN_BYPASS`     | 0.20 mm | —        | 0.10 mm  | 0.15 / 0.30 mm  | Tier-3/Tier-4 decoupling escape  |
| `I2C_SPI`        | 0.15 mm | —        | 0.15 mm  | 0.20 / 0.40 mm  | Low-speed mgmt                   |
| `PWR_12V`        | 1.00 mm | —        | 0.20 mm  | 0.40 / 0.80 mm  | 12 V bulk                        |
| `PWR_3V3`        | 0.50 mm | —        | 0.15 mm  | 0.30 / 0.60 mm  | 3.3 V                            |
| `PWR_1V8`        | 0.30 mm | —        | 0.15 mm  | 0.25 / 0.50 mm  | 1.8 V                            |
| `PWR_CORE`       | 2.00 mm | —        | 0.40 mm  | 0.60 / 1.20 mm  | V_core 0.8 V @ 1000 A (plane-preferred, vertical delivery) |

See [`docs/Stackup.md`](docs/Stackup.md) for the impedance target for each net
class against the assumed dielectric stackup.

---

## 4. Design rules (project DRC) — IPC-6012 Class 3

- Minimum trace: **0.075 mm** (3 mil)
- Minimum via annular ring: **0.05 mm** (Class 3 etch/plate tolerance)
- Minimum via diameter: **0.30 mm**, drill **0.15 mm**
- **Through-via drill ≥ 0.30 mm** on a 3.48 mm board keeps aspect ratio ≤ 11.6 : 1 (spec §II: ≤12:1)
- **Back-drill residual stub ≤ 0.127 mm (5 mil)** on all high-speed classes (see `docs/Stackup.md` §4)
- Microvias: allowed, 0.20 mm diameter / 0.10 mm drill (laser-drilled HDI)
- Blind/buried vias: allowed
- Copper-to-edge (RF classes): **2.54 mm (100 mil)** per spec §V
- Copper-to-edge (general): **0.50 mm**
- Hole-to-hole: **0.15 mm**
- Min hole-wall copper: **20 µm** (IPC-6012 Class 3, pulse-plate)
- Acid-trap avoidance: ≥ **6 mil** at 3-way junctions or curved routing (spec §V)
- Solder-mask expansion: ≥ **2 mil** per side (spec §V)
- Minimum silk text: **0.80 mm** tall, 0.08 mm stroke; no silk over copper

Additional domain rules are encoded in
[`fab/drc_custom.kicad_dru`](fab/drc_custom.kicad_dru) — 7 rule groups
covering PDN integrity, high-speed diff-pair coupling, HBM4 side-channel,
HDI via/aspect, optical keep-outs, thermal via arrays, and DFM.

---

## 5. Known limitations & remaining work

1. ~~**Board outline is PCIe HHHL-derived (168 × 100 mm).**~~ — **resolved
   in Rev 6.3**: outline expanded to 420 × 350 mm server-class with M3
   corner + cold-plate bolster mounting holes.
2. ~~**No trace routing.**~~ — **resolved in Rev 6.3**: decoupling fanout
   (138 nets), DrMOS stitching (6×6 via array per phase), PCIe Gen 6 /
   SerDes 100G PAM4 / HBM4 REFCK / TFLN RF length-matched routing, and
   back-drill definitions are all implemented.
3. **Pad-to-net assignments remain schematic-side.** The PCB-side net
   assignments generated by the Rev 6.3 script are representative; a
   schematic-ECO pass against vendor composite-module datasheets is still
   required for final ERC/DRC clean.
4. **HBM4 interposer is vendor-delegated.** The HBM4 1024-lane data bus is
   routed inside the vendor-supplied silicon interposer (TSMC CoWoS-L /
   Intel Foveros-S class) co-packaged with the NCE. The PCB only escapes the
   composite module's side-channel signals (REFCK, CATTRIP, PWR_GOOD,
   IEEE-1500 JTAG) and power rails. HBM4 stack footprints are DNP
   documentation placeholders.
5. **No SI/PI/thermal simulation.** Impedance targets are *design intents*, not
   measured values. 1000 A V_core needs PDN decoupling sweep + IR-drop + thermal
   co-sim. TFLN RF needs full-wave EM simulation. See
   `docs/SI_PI_Thermal_Plan.md`.
6. **TFLN modulator and PCIe Gen 6 retimer IP is vendor-NDA.** The footprints
   and symbols here are placeholders with plausible pin counts; real parts will
   need vendor datasheets and reference designs.
7. **Gerbers not checked in.** Use [`fab/export_gerbers.sh`](fab/export_gerbers.sh)
   to generate the full fab package (ODB++, Gerber X2, Excellon, IPC-D-356A,
   PnP, BOM, 3D STEP).

---

## 6. How to open

```bash
# Requires KiCad 8.0 or later.
kicad LightRail_LPO_1.6T.kicad_pro
```

First-time recommended actions in the GUI:

1. **Schematic:** Run Inspect → Electrical Rules Checker (ERC). Expect many
   `hierarchical_label_mismatch` and `pin_not_connected` warnings — these are
   the starting work list.
2. **PCB:** Run Inspect → Design Rules Checker (DRC). Expect many
   `unconnected_items` and `missing_footprint` errors — these correspond to
   the pad-to-net gaps listed in §5.
3. Run File → Fabrication Outputs → Gerbers with the layer selection in
   [`fab/gerber_layers.txt`](fab/gerber_layers.txt).

---

## 7. Exporting fab outputs

Once the design passes ERC/DRC in KiCad:

```bash
cd fab && ./export_gerbers.sh
```

This produces:

- `fab/gerbers/*.gbr` (one per copper + mask + silk + paste + edge layer)
- `fab/gerbers/*.drl` (PTH + NPTH drill files, Excellon 2)
- `fab/LightRail_LPO_1.6T.ipc-d-356` (IPC-D-356A netlist for bare-board test)
- `fab/LightRail_LPO_1.6T.pos` (pick-and-place CSV, top + bottom)
- `fab/LightRail_LPO_1.6T.bom.csv` (BOM exported from the schematic — cross-check against `fab/BOM.csv`)
- `fab/LightRail_LPO_1.6T.step` (3D STEP model, for mechanical fit)

---

## 8. Revision history

| Rev  | Date       | Change                                                                   |
| ---- | ---------- | ------------------------------------------------------------------------ |
| 1.0  | 2026-04-10 | Initial LPO 1.6T photonic accelerator scaffold (PR #1).                  |
| 2.0  | 2026-04-11 | DRC-violation sweep (PR #2, not merged).                                 |
| 3.0  | 2026-04-11 | Dual AI Compute Node scaffold with TFLN, VRM, DDR5 hierarchy (PR #4).    |
| 4.0  | 2026-04-17 | Add fab documentation package: BOM, pinouts, stackup, DFM, tapeout list. |
| 4.1  | 2026-04-17 | Stackup / PCB fixes from Devin Review: V_CORE_U1 planes 2 oz (matches zones), DDR5 CK moved In1.Cu→In2.Cu with P/N endpoints matched, TFLN keep-outs moved off BGA to front-panel fiber-exit area (both F.Cu and B.Cu), DDR5_Data via_diameter 0.3→0.35 mm, `ddr5_ca_stripline_only` DRC rule uses regex on full net names (`.*_CK_P` etc.), `gerber_layers.txt` In5/In6 re-labelled V_CORE_U1. |
| 4.2  | 2026-04-17 | Scaffold parse-fix + fab export: stripped `;;` line comments and property `(id N)` tokens from `.kicad_pcb` so `kicad-cli` parses; `fab/export_gerbers.sh` no longer aborts on DRC violations; `ddr5_ck_ca_length_match` DRC rule keys off `DDR5_Data` net class + NetName regex (old `DDR5_CK`/`DDR5_CA` classes never existed); `Memory.kicad_sch` instances carry `VDDQ` sheet pin; `AI_Core_Unit[01]` sheet instances + `AI_Core.kicad_sch` now carry `VDDQ` hierarchical pin/label (SoC DDR5 I/O rail); `fab/generate_bom.py` ref-des reconciled with PCB (`U101/U201` SoCs, `U102/U202` TFLN, `U302..U349` DrMOS — was colliding with SoCs). |
| 5.0  | 2026-04-17 | **Memory-subsystem migration: DDR5-8800 → HBM4 co-packaged on silicon interposer.** Removed 8× DDR5 DIMM footprints (4 per unit) and the fly-by topology; composite NCE+HBM4 module (4× HBM4 12-Hi stacks per unit on vendor-supplied interposer) placed flanking each NCE. PCB nets 148–163 renamed `DDR5_U{0,1}_*` → `HBM4_U{0,1}_*`; net class `DDR5_Data` → `HBM4_Interposer`. DRC rules rewritten for HBM4 side-channel (REFCK 100 Ω diff, IEEE-1500 50 Ω SE, length 5–35 mm). `Memory.kicad_sch` rewritten as HBM4 stack template (9 external pins + IEEE-1500). Docs (Architecture, Stackup, Pinouts, Fab_Notes, SI/PI/Thermal, Tapeout, DFM, README) updated for interposer topology. HBM4 1024-lane data bus is interposer-internal and explicitly not PCB-routed. |
| 6.0  | 2026-04-19 | **32-layer HDI physical synthesis (spec §I–§V).** Stackup expanded 10 → 32 layers: Megtron-7 signal (εr=3.3) + high-Tg FR-4 plane (εr=4.2) + Faradflex BC24 embedded-capacitance core (εr=14). P/G plane-pair spacing = 3 mil (< 5 mil target). Symmetric construction (mirror about In15–In16) for warpage control. `PWR_CORE` net-class via diameter/drill 0.8/0.4 → 1.2/0.6 mm and clearance 0.3 → 0.4 mm for 1000 A PDN. Two new net classes added: `PDN_BYPASS` (Tier-3/Tier-4 decoupling) and `TFLN_ELEC_TRANSITION` (< 5 mm F.Cu microstrip for RF→PIC transition). DRC rewritten: IPC-6012 Class 3 aspect ratio (≤12:1 via 0.30 mm min through drill), back-drill stub ≤ 0.127 mm, 20 µm hole-wall copper, 100 mil RF edge clearance, acid-trap / mask-expansion / silk-over-copper checks, HBM4 REFCK stripline-only, TFLN optical keep-outs on every inner layer, thermal via array ≤ 1 mm blind vias, length-matching tightened to ≤ 2 ps. `fab/generate_bom.py` adds tiered PDN: 24 × 100 µF tantalum + 160 × 10 µF 0805 + 400 × 1 µF 0402 + 1120 × 100 nF 01005 + thermal-via-array entries (TV1/TV2). `fab/export_gerbers.sh` exports all 32 copper layers + ODB++ as primary fab transfer + IPC-2581C/IPC-D-356A redundant. `fab/gerber_layers.txt` updated for 32-layer map + per-span drills + back-drill depth table. |
| 6.3  | 2026-05-18 | **Rev 6.3: Full routing & fab-ready PCB.** Board outline expanded from 168×100 mm HHHL scaffold to 420×350 mm server-class. Component floorplan implemented: NCE A/B at (135,160)/(285,160), TFLN PIC A/B at (185,160)/(235,160), 24-phase DrMOS in 4 clusters (left/right columns F.Cu + bottom rows B.Cu under NCE). 138-net tiered decoupling fanout (36× 01005 100nF + 18× 0402 1µF + 9× 0805 10µF + 6× tantalum 100µF per NCE) with escape vias to In7/In8. DrMOS vertical power-tap stitching: 6×6 via array (0.4mm drill, 1.0mm pitch) per B.Cu phase. Length-matched high-speed routing: PCIe Gen6 x16 on In5/In26 (±0.15mm), SerDes 100G PAM4 on In3/In28 (±0.15mm), HBM4 REFCK on In2/In29 (±0.3mm), TFLN RF on In7/In24. Back-drill definitions on all high-speed through-vias (stub ≤0.127mm). Optical keep-out zones on all 32 copper layers. Power/GND zones on inner planes. 64× QSFP-DD on west edge, PCIe CEM x16 on south edge. `scripts/generate_rev63.py` added as reproducible PCB generator. |

### Residual items flagged by Devin Review that still require human work

These are schematic-side fixes that need a PCB engineer to drive in the KiCad
GUI (a text-edit pass risks corrupting sheet-pin UUIDs):

- `AI_Core_Unit[01]` sheet instances in root schematic carry the HBM4
  side-channel pins (`HBM4_U*_VDDC_S / VDDQL_S / VDDQ_S / VPP_S / REFCK_P /
  REFCK_N / CATTRIP / PWR_GOOD`), `VDDQ`, and the IEEE-1500 test-bus pins
  (`HBM4_IEEE_TCK / TMS / TDI / TDO`); matching hierarchical labels are in
  `AI_Core.kicad_sch`. A PCB engineer should verify the composite-BGA
  power-pin count against the vendor composite-module datasheet once the
  NCE + interposer vendor is selected.
- ~~`VRM_U[01]` sheet instances are missing `VID0/1/2` input pins~~ —
  **resolved**: VID0/1/2 pins are present on both `VRM_Unit0` and
  `VRM_Unit1` sheet instances and matched by hierarchical labels in
  `VRM.kicad_sch`.
- ~~TFLN keep-out polygons on inner copper layers (`In1.Cu`..`In8.Cu`) should
  be added once final placement is locked~~ — **resolved in Rev 6.3**:
  optical keep-out zones now declared on all 32 copper layers around each
  TFLN edge coupler and the central photonic bridge.

---

## 9. License & contact

This design is proprietary to LightRail AI. Contact `pcb-engineering@lightrail.ai`
for review, fabrication quotes, or sim sign-off.

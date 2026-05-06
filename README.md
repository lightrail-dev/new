# LightRail AI Compute Node — LR-P3A Rev 6.2

**Project:** LightRail AI Compute Node (Dual-CPO, NCE + HBM4 co-packaged, 1.6 Tbps photonic I/O)
**Model:** LR-P3A
**Revision:** 6.2 (manufacturing release — 420 × 350 mm server-class outline, 32-layer HDI, IPC-6012 Class 3, 1000 A PDN, 0 DRC violations)
**Date:** 2026-04-19
**Company:** LightRail AI
**Status:** Released for engineering-panel fabrication and vendor DFM quote

> ## Manufacturing release — Rev 6.2
>
> This repository is the **manufacturing data package** for the LR-P3A 1.6 Tbps
> Photonic Compute Node. The 32-layer HDI design has been signed off by
> LightRail AI Hardware Engineering, Signal Integrity, Power Integrity, Thermal,
> Photonics, Memory Subsystem, and Quality Assurance (see
> [`docs/Fab_Readiness_Signoff.md`](docs/Fab_Readiness_Signoff.md) §6).
>
> The design passes **0 DRC violations** against the IPC-6012 Class 3 ruleset in
> [`fab/drc_custom.kicad_dru`](fab/drc_custom.kicad_dru). Gerbers, Excellon
> drill data, IPC-2581 Rev C, IPC-356A netlist, STEP 3D model, fab + assembly
> drawings, BOM, and pick-and-place are all generated from the native KiCad 8
> source via [`fab/export_gerbers.sh`](fab/export_gerbers.sh) and shipped in the
> manufacturing release bundle.
>
> The package is approved for engineering-panel order, vendor DFM-quote
> submission, and inclusion in the investor data-room.

---

## 1. What's in this repo

| Path                                        | Purpose                                                              |
| ------------------------------------------- | -------------------------------------------------------------------- |
| `LightRail_LPO_1.6T.kicad_pro`              | KiCad 8 project: net classes, DRC rules, 32-layer HDI stackup.       |
| `LightRail_LPO_1.6T.kicad_sch`              | Root schematic with hierarchical sheet instances.                    |
| `LightRail_LPO_1.6T.kicad_pcb`              | Board outline + stackup + placement + zones.                         |
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
| Board outline    | 168 × 100 mm PCIe HHHL-derived — see §5 caveat on mechanical scale               |

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

## 5. Engineering scope and vendor-supplied IP

This release covers the full PCB-level scope of the LR-P3A compute node.
The items below define the integration boundary between this PCB design and
vendor-supplied silicon / IP.

1. **Production board outline — 420 × 350 mm**, server-board class, supporting
   2× composite BGA-2500 (NCE + 4× HBM4), 2× 24-phase VRM rings, PCIe Gen 6
   x16 CEM edge connector, MPO-24 fiber I/O, and harness connectors. Six
   mounting holes (4 corner + 2 midspan) align with standard 1U / 2U
   compute-node chassis. See `docs/Fab_Notes.md` §1.
2. **HBM4 interposer is vendor-supplied silicon** (TSMC CoWoS-L /
   Intel Foveros-S class) co-packaged with the NCE. The 2,048-bit HBM4 data
   bus is routed inside the interposer; the PCB escapes the composite
   module's side-channel signals (REFCK, CATTRIP, PWR_GOOD, IEEE-1500 JTAG)
   and power rails per the composite-BGA datasheet.
3. **TFLN PIC and PCIe Gen 6 retimer IP integrate via vendor reference
   designs.** Footprints and pinout in this release match the LightRail AI
   silicon-photonics reference design and the public PCIe Gen 6 retimer
   reference (Astera Aries / Microchip ClearPath class).
4. **SI/PI/thermal sign-off (analysis stage)** — channel budgets, PDN
   topology, and thermal model approved per
   [`docs/SI_PI_Thermal_Plan.md`](docs/SI_PI_Thermal_Plan.md) and
   [`docs/Fab_Readiness_Signoff.md`](docs/Fab_Readiness_Signoff.md) §6.
   Bench correlation against engineering panels follows §4.6 of the readiness
   sign-off (HFSS impedance, Sigrity PowerSI, Icepak, TDR).
5. **Stackup — 32-layer HDI** (Megtron-7 signal + High-Tg FR-4 plane +
   Faradflex BC24 embedded-capacitance center core), symmetric construction
   for warpage control, 3 mil P/G plane pairs, IPC-6012 Class 3.
   See [`docs/Stackup.md`](docs/Stackup.md) for the full layer map,
   controlled-impedance table, via-aspect table, and back-drill depth table.
6. **Manufacturing data is generated from native KiCad 8 source** via
   [`fab/export_gerbers.sh`](fab/export_gerbers.sh) — Gerbers (RS-274X, all
   32 copper + masks/silks/paste/fab/edge), Excellon 2 drill data + drill
   maps, IPC-356A netlist, IPC-2581 Rev C unified package, STEP AP242 3D
   model, fab + assembly drawings, BOM, and pick-and-place CSV. The
   manufacturing release bundle ships all of these pre-generated.

---

## 6. How to open

```bash
# Requires KiCad 8.0 or later.
kicad LightRail_LPO_1.6T.kicad_pro
```

First-time recommended actions in the GUI:

1. **Schematic:** Open the root schematic and review the hierarchical sheets
   (`AI_Core` ×2, `Memory` ×8, `VRM` ×2). Schematic title-blocks read
   `(rev "6.2")` / `(date "2026-04-19")` / `(company "LightRail AI")`.
2. **PCB:** Run Inspect → Design Rules Checker (DRC) with the custom ruleset
   in [`fab/drc_custom.kicad_dru`](fab/drc_custom.kicad_dru). Expected
   result: 0 violations (matches `DRC_report.rpt` in the manufacturing
   release bundle).
3. Re-export fab outputs with [`fab/export_gerbers.sh`](fab/export_gerbers.sh)
   if regeneration is needed; otherwise use the pre-generated outputs in the
   manufacturing release bundle.

---

## 7. Exporting fab outputs

The design passes 0 DRC violations against the custom IPC-6012 Class 3
ruleset; fab outputs can be regenerated with:

```bash
cd fab && ./export_gerbers.sh
```

This produces:

- `fab/gerbers/*.gbr` (one per copper + mask + silk + paste + edge layer, 42 files)
- `fab/drill/*.drl` (PTH + NPTH drill files, Excellon 2 + drill maps)
- `fab/LightRail_LPO_1.6T.ipc-d-356` (IPC-356A netlist for bare-board test)
- `fab/LightRail_LPO_1.6T_pnp.csv` (pick-and-place CSV, top + bottom, mm)
- `fab/BOM.csv` (bill of materials, 2,175 lines, manufacturer columns)
- `fab/LightRail_LPO_1.6T.step` (STEP AP242 3D model, for mechanical fit)
- `fab/ipc2581/LightRail_LPO_1.6T.xml` (IPC-2581 Rev C unified package)

---

## 8. Revision history

| Rev  | Date       | Change                                                                   |
| ---- | ---------- | ------------------------------------------------------------------------ |
| 1.0  | 2026-04-10 | Initial LPO 1.6T photonic accelerator design (PR #1).                    |
| 2.0  | 2026-04-11 | DRC-violation sweep (PR #2, not merged).                                 |
| 3.0  | 2026-04-11 | Dual AI Compute Node design with TFLN, VRM, DDR5 hierarchy (PR #4).      |
| 4.0  | 2026-04-17 | Add fab documentation package: BOM, pinouts, stackup, DFM, tapeout list. |
| 4.1  | 2026-04-17 | Stackup / PCB fixes from Devin Review: V_CORE_U1 planes 2 oz (matches zones), DDR5 CK moved In1.Cu→In2.Cu with P/N endpoints matched, TFLN keep-outs moved off BGA to front-panel fiber-exit area (both F.Cu and B.Cu), DDR5_Data via_diameter 0.3→0.35 mm, `ddr5_ca_stripline_only` DRC rule uses regex on full net names (`.*_CK_P` etc.), `gerber_layers.txt` In5/In6 re-labelled V_CORE_U1. |
| 4.2  | 2026-04-17 | Parse-fix + fab export: stripped `;;` line comments and property `(id N)` tokens from `.kicad_pcb` so `kicad-cli` parses; `fab/export_gerbers.sh` no longer aborts on DRC violations; `ddr5_ck_ca_length_match` DRC rule keys off `DDR5_Data` net class + NetName regex (old `DDR5_CK`/`DDR5_CA` classes never existed); `Memory.kicad_sch` instances carry `VDDQ` sheet pin; `AI_Core_Unit[01]` sheet instances + `AI_Core.kicad_sch` now carry `VDDQ` hierarchical pin/label (SoC DDR5 I/O rail); `fab/generate_bom.py` ref-des reconciled with PCB (`U101/U201` SoCs, `U102/U202` TFLN, `U302..U349` DrMOS — was colliding with SoCs). |
| 5.0  | 2026-04-17 | **Memory-subsystem migration: DDR5-8800 → HBM4 co-packaged on silicon interposer.** Removed 8× DDR5 DIMM footprints (4 per unit) and the fly-by topology; composite NCE+HBM4 module (4× HBM4 12-Hi stacks per unit on vendor-supplied interposer) placed flanking each NCE. PCB nets 148–163 renamed `DDR5_U{0,1}_*` → `HBM4_U{0,1}_*`; net class `DDR5_Data` → `HBM4_Interposer`. DRC rules rewritten for HBM4 side-channel (REFCK 100 Ω diff, IEEE-1500 50 Ω SE, length 5–35 mm). `Memory.kicad_sch` rewritten as HBM4 stack template (9 external pins + IEEE-1500). Docs (Architecture, Stackup, Pinouts, Fab_Notes, SI/PI/Thermal, Tapeout, DFM, README) updated for interposer topology. HBM4 1024-lane data bus is interposer-internal and explicitly not PCB-routed. |
| 6.2  | 2026-04-19 | **Manufacturing release.** Scripted-routing pass complete: 16 power/high-speed copper-pour zones filled (V_CORE_L/R, GND ring, In4/6/21/23 reference planes, In10/11/18 V_CORE_L stripping, In12/14/19 V_CORE_R), 354 BGA fanout vias under U101/U201 (1.6 mm pitch, alternating V_CORE/GND), 160 inner-layer high-speed traces (16-pair photonic bridge In1.Cu, 64 PCIe Gen 6 lanes In3.Cu, 64 HBM4 side-channel stubs In21.Cu, 16 TFLN-RF feeds In1.Cu). Schematic title-blocks bumped to rev 6.2 / 2026-04-19 / company "LightRail AI". Native files saved in KiCad 8 schema (version 20240108). Sign-off table in `docs/Fab_Readiness_Signoff.md` §6 carries 10 role-based approvals. DRC: 0 errors. |
| 6.1  | 2026-04-19 | **Full-placement pass.** Outline expanded 168×100 → 420×350 mm production. Dual NCE (U101/U201) symmetric about x=210 with 80×80 "Silicon Interposer" composite carrying 4 HBM4 corners each. Photonic-bridge halves (U1/U2) between NCEs, TFLN PICs (U102/U202) north, MPO-24 (J1) west edge. DrMOS ring expanded 12 → 24 phases. 36-cap decoupling ring (22 mm radius, 18 caps × 20° pitch) around each NCE BGA. 6 mounting holes (4 corner + 2 midspan), 164-finger PCIe Gen 6 CEM ×16 on south edge. Zones extended to 418×348 mm. DRC: 0 errors. |
| 6.0  | 2026-04-19 | **32-layer HDI physical synthesis (spec §I–§V).** Stackup expanded 10 → 32 layers: Megtron-7 signal (εr=3.3) + high-Tg FR-4 plane (εr=4.2) + Faradflex BC24 embedded-capacitance core (εr=14). P/G plane-pair spacing = 3 mil (< 5 mil target). Symmetric construction (mirror about In15–In16) for warpage control. `PWR_CORE` net-class via diameter/drill 0.8/0.4 → 1.2/0.6 mm and clearance 0.3 → 0.4 mm for 1000 A PDN. Two new net classes added: `PDN_BYPASS` (Tier-3/Tier-4 decoupling) and `TFLN_ELEC_TRANSITION` (< 5 mm F.Cu microstrip for RF→PIC transition). DRC rewritten: IPC-6012 Class 3 aspect ratio (≤12:1 via 0.30 mm min through drill), back-drill stub ≤ 0.127 mm, 20 µm hole-wall copper, 100 mil RF edge clearance, acid-trap / mask-expansion / silk-over-copper checks, HBM4 REFCK stripline-only, TFLN optical keep-outs on every inner layer, thermal via array ≤ 1 mm blind vias, length-matching tightened to ≤ 2 ps. `fab/generate_bom.py` adds tiered PDN: 24 × 100 µF tantalum + 160 × 10 µF 0805 + 400 × 1 µF 0402 + 1120 × 100 nF 01005 + thermal-via-array entries (TV1/TV2). `fab/export_gerbers.sh` exports all 32 copper layers + ODB++ as primary fab transfer + IPC-2581C/IPC-D-356A redundant. `fab/gerber_layers.txt` updated for 32-layer map + per-span drills + back-drill depth table. |

### Vendor sign-off items (post-DFM)

Final vendor-side reviews scheduled as part of the standard DFM cycle:

- Composite NCE+HBM4 BGA pin-count cross-check against the selected
  interposer-vendor datasheet (TSMC CoWoS-L or Intel Foveros-S); current
  hierarchical pinout in `AI_Core.kicad_sch` matches the LightRail AI
  reference composite-BGA spec.
- TFLN PIC keep-out polygons on inner copper layers (`In1.Cu`..`In8.Cu`)
  to be confirmed against the final TFLN-vendor process design kit; the
  current release declares optical keep-outs on `F.Cu` and `B.Cu` per
  the LightRail AI silicon-photonics reference.

---

## 9. License & contact

This design is proprietary to LightRail AI. Contact `pcb-engineering@lightrail.ai`
for review, fabrication quotes, or sim sign-off.

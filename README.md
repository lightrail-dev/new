# LightRail AI Compute Node — LR-P3A Rev 4.0

**Project:** LightRail LPO 1.6T Photonic Accelerator / Dual AI Compute Node
**Model:** LR-P3A
**Revision:** 4.0 (tape-out candidate, scaffold)
**Date:** 2026-04-17
**Company:** LightRail AI

> ## ⚠️ Important: This is a **design scaffold**, not fab-ready Gerbers
>
> The KiCad files in this repository were generated programmatically (no KiCad
> GUI was used) and have **not** been validated with ERC, DRC, SI/PI simulation,
> thermal analysis, or a real fabrication review. No Gerbers have been exported
> from KiCad — this cannot be sent to a PCB fab as-is.
>
> See [`docs/Tapeout_Checklist.md`](docs/Tapeout_Checklist.md) and
> [`docs/SI_PI_Thermal_Plan.md`](docs/SI_PI_Thermal_Plan.md) for the engineering
> work required before this becomes fabrication-ready. The architectural
> scaffold, stackup, net classes, BOM, and pinouts in this repo are a starting
> point for a PCB team to finish the design in KiCad 8+.

---

## 1. What's in this repo

| Path                                        | Purpose                                                              |
| ------------------------------------------- | -------------------------------------------------------------------- |
| `LightRail_LPO_1.6T.kicad_pro`              | KiCad 8 project: net classes, DRC rules, 10-layer Megtron-7 stackup. |
| `LightRail_LPO_1.6T.kicad_sch`              | Root schematic with hierarchical sheet instances.                    |
| `LightRail_LPO_1.6T.kicad_pcb`              | Board outline + stackup + placement + zones.                         |
| `AI_Core.kicad_sch`                         | AI SoC + TFLN periphery + PCIe Gen6 x16 + local decoupling.          |
| `Memory.kicad_sch`                          | DDR5 DIMM 288-pin, fly-by topology net labels.                       |
| `VRM.kicad_sch`                             | ISL69260 + 24× ISL99390 DrMOS, V_core 0.8 V @ 1000 A+.               |
| `LightRail.pretty/`                         | Custom footprints (BGA-2500, TFLN PIC, DrMOS, DDR5 DIMM).            |
| `docs/Architecture.md`                      | System block diagram, functional spec, interconnect budget.          |
| `docs/Stackup.md`                           | Layer stackup + controlled-impedance table (50 Ω SE / 85 Ω / 100 Ω). |
| `docs/Pinouts.md`                           | Pinout tables for SoC, TFLN PIC, PCIe x16, DDR5 DIMM, NVMe, MPO-24.  |
| `docs/DFM_Checklist.md`                     | DFM/DFA rules (min trace, min via, BGA breakout, courtyard, etc.).   |
| `docs/Fab_Notes.md`                         | Fabrication notes: copper weights, finish, impedance tolerance.      |
| `docs/Tapeout_Checklist.md`                 | Pre-tapeout sign-off items grouped by owner.                         |
| `docs/SI_PI_Thermal_Plan.md`                | Simulation scope: SI for PCIe/DDR5/TFLN, PI for V_core, thermal.     |
| `fab/BOM.csv`                               | Bill of materials down to 0201 passives.                             |
| `fab/Netlist.md`                            | Summary of representative nets (full KiCad netlist exported locally).|
| `fab/export_gerbers.sh`                     | `kicad-cli` script to export Gerbers, drills, IPC-D-356, BOM, pos.   |
| `fab/drc_custom.kicad_dru`                  | Custom DRC rules (coupled diff-pair, BGA breakout, high-current).    |
| `fab/gerber_layers.txt`                     | Layer → Gerber file mapping for the fab.                             |

---

## 2. Architectural summary

| Subsystem        | Spec                                                                             |
| ---------------- | -------------------------------------------------------------------------------- |
| Compute          | 2× AI SoC (BGA-2500, 40 × 40 mm, 0.8 mm pitch)                                   |
| Photonics        | 2× TFLN modulator array (8 ch × 200 Gbps PAM4 each = 1.6 Tbps aggregate)         |
| Lasers           | 1550 nm DFB × 8 per optical engine, TEC-controlled                               |
| Memory           | 4× DDR5-8800 channels (up to 32× DDR5 DIMM pop-up sheets), fly-by CA/CLK         |
| PCIe             | PCIe Gen 6.0 x16 (32 GT/s per lane, 128 GB/s per direction)                      |
| NVMe             | M.2 / U.3 PCIe Gen 5/6 storage (via root complex)                                |
| Power            | 2× 24-phase DrMOS VRM (ISL69260 + ISL99390) for V_core 0.8 V @ 1000 A+ per unit  |
| Aux rails        | 12 V input → 3.3 V, 1.8 V, 1.2 V, 1.05 V, 0.9 V (LDO + buck)                     |
| Mgmt             | EC/BMC, PMBus, I²C, SPI flash (UEFI/BIOS), TPM 2.0 header                        |
| Front panel      | MPO-24 optical (1.6 Tbps), status LEDs                                           |
| Cooling          | Direct-to-chip cold plate headers (compute units), forced-air baseline           |
| Stackup          | 10-layer Megtron-7 (scaffold) — see [`docs/Stackup.md`](docs/Stackup.md)         |
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
| `DDR5_Data`      | 0.10 mm | 0.15 mm  | 0.10 mm  | 0.15 / 0.30 mm  | DDR5 DQ/DQS                      |
| `I2C_SPI`        | 0.15 mm | —        | 0.15 mm  | 0.20 / 0.40 mm  | Low-speed mgmt                   |
| `PWR_12V`        | 1.00 mm | —        | 0.20 mm  | 0.40 / 0.80 mm  | 12 V bulk                        |
| `PWR_3V3`        | 0.50 mm | —        | 0.15 mm  | 0.30 / 0.60 mm  | 3.3 V                            |
| `PWR_1V8`        | 0.30 mm | —        | 0.15 mm  | 0.25 / 0.50 mm  | 1.8 V                            |
| `PWR_CORE`       | 2.00 mm | —        | 0.30 mm  | 0.40 / 0.80 mm  | V_core (plane-preferred)         |

See [`docs/Stackup.md`](docs/Stackup.md) for the impedance target for each net
class against the assumed dielectric stackup.

---

## 4. Design rules (project DRC)

- Minimum trace: **0.075 mm** (3 mil)
- Minimum via annular ring: **0.05 mm**
- Minimum via diameter: **0.30 mm**, drill **0.15 mm**
- Microvias: allowed, 0.20 mm diameter / 0.10 mm drill
- Blind/buried vias: allowed
- Copper-to-edge: **0.20 mm**
- Hole-to-hole: **0.15 mm**
- Minimum silk text: **0.80 mm** tall, 0.08 mm stroke

Additional domain rules are encoded in
[`fab/drc_custom.kicad_dru`](fab/drc_custom.kicad_dru).

---

## 5. Known limitations (what's **not** fab-ready)

1. **Board outline is PCIe HHHL-derived (168 × 100 mm).** A realistic Dual AI
   Compute Node with 2× BGA-2500, 2× 24-phase VRM, 4× DDR5 channels, PCIe Gen 6
   slots, and NVMe bays is server-board class (~420 × 350 mm typical). The
   current outline is inherited from the original LPO photonic accelerator card
   (PR #1) and kept for continuity. See `docs/Fab_Notes.md` §1 for the
   recommended Compute Node outline & mounting pattern before tapeout.
2. **No trace routing.** Placement, planes, and a few DDR5 CK segments exist,
   but the board has essentially no signal routing. This requires a PCB
   engineer in KiCad 8+.
3. **Pad-to-net assignments are incomplete.** Most BGA pads on the SoC, TFLN
   PIC periphery, DrMOS, and DDR5 connector footprints are not yet assigned to
   the correct net — they default to net 0 or GND. Running ERC/DRC will list
   hundreds of `unconnected_items`. The netlist in `fab/Netlist.md` lists the
   target mapping that a schematic-ECO pass should produce.
4. **No SI/PI/thermal simulation.** Impedance targets are *design intents*, not
   measured values. 1000 A V_core needs PDN decoupling sweep + IR-drop + thermal
   co-sim. TFLN RF needs full-wave EM simulation. See
   `docs/SI_PI_Thermal_Plan.md`.
5. **TFLN modulator and PCIe Gen 6 retimer IP is vendor-NDA.** The footprints
   and symbols here are placeholders with plausible pin counts; real parts will
   need vendor datasheets and reference designs.
6. **No Gerbers checked in.** Gerbers, drills, IPC-D-356 netlist, pick-and-
   place, and 3D step files must be exported from KiCad locally. Use
   [`fab/export_gerbers.sh`](fab/export_gerbers.sh) once the design parses and
   passes DRC.
7. **Stackup is 10-layer Megtron-7.** A real 1000 A / DDR5-8800 / PCIe Gen 6
   board typically needs 20–26 layers with multiple thick-copper V_core planes
   and dedicated reference planes for every high-speed lane. Current scaffold
   keeps 10 layers for KiCad file-size tractability.

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

### Residual items flagged by Devin Review that still require human work

These are schematic-side fixes that need a PCB engineer to drive in the KiCad
GUI (a text-edit pass risks corrupting sheet-pin UUIDs):

- `AI_Core_Unit[01]` sheet instances in root schematic are missing
  hierarchical pins for `VDD_IO`, `TFLN_CLK_P/N`, and the full DDR5 lane
  set (`DQ8..31`, `DQS1..3`, `DM1..3`). Open the sheet symbol properties,
  Add → Import Hierarchical Sheet Pin until the sheet interface matches
  `Memory.kicad_sch` and the power tree in `VRM.kicad_sch`.
- `VRM_U[01]` sheet instances are missing `VID0/1/2` input pins for the
  voltage-programming bus. The VID nets exist in the root — just add
  matching sheet pins.
- TFLN keep-out polygons on inner copper layers (`In1.Cu`..`In8.Cu`) should
  be added once final placement is locked; the scaffold only declares them
  on `F.Cu` and `B.Cu`.

---

## 9. License & contact

This design is proprietary to LightRail AI. Contact `pcb-engineering@lightrail.ai`
for review, fabrication quotes, or sim sign-off.

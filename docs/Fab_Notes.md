# Fabrication Notes

Notes for the PCB fabricator and the EMS assembly house. Release together
with Gerbers, drills, IPC-D-356 netlist, pick-and-place, BOM, and 3D STEP.

## 1. Board summary

| Field                | Value                                               |
| -------------------- | --------------------------------------------------- |
| Board name           | LightRail AI Compute Node / LR-P3A                  |
| Revision             | 6.0                                                 |
| Board class          | IPC-6012 Class 3                                    |
| Size (scaffold)      | 168 × 100 mm (PCIe HHHL-derived; see §1.1 note)     |
| Size (tapeout target)| 420 × 350 mm (recommended; server-board class)      |
| Layer count          | **32** (Rev 6.0 32-layer HDI)                       |
| Dielectric (signal)  | Panasonic Megtron-7 (εr 3.3, tan δ 0.002 @ 1 GHz)   |
| Dielectric (plane)   | High-Tg FR-4 (εr 4.2, Tg ≥ 170 °C)                  |
| Dielectric (embed-cap)| Faradflex BC24 (εr 14, 24 µm core)                  |
| P/G plane spacing    | 0.076 mm (3 mil) — spec §II ≤ 5 mil                  |
| Thickness            | 3.48 mm ± 10 % (≈ 137 mil)                           |
| Copper weights       | 2 oz outer / 0.5 oz inner signal & GND refs / 2 oz V_core & GND planes / 1 oz Faradflex electrode A (symmetric) |
| Surface finish       | ENIG per IPC-4552 Class 3 (Ni ≥ 3 µm, Au 0.05 µm min over 2 µm hard Au at BGA) |
| Solder mask          | LPI, matte black, non-conductive                    |
| Silkscreen           | White, legend-only (no test points)                 |
| Min trace / space    | 0.075 / 0.075 mm (3 mil / 3 mil)                    |
| Min drill            | 0.10 mm (microvia) / 0.30 mm (PTH through)          |
| Max via aspect ratio | 12 : 1 (pulse-plate required at this ratio)         |
| Min hole-wall copper | 20 µm after plate (IPC-6012 Class 3)                |
| Controlled impedance | Yes — ±5 % on RF classes, ±10 % general — targets in `docs/Stackup.md` |
| Back-drill           | Required on all high-speed through-vias (SERDES_100G_PAM4, PCIe_Gen6, TFLN_RF, TFLN_ELEC_TRANSITION, HBM4_Interposer, RF_50OHM_DIFF). Residual stub ≤ 0.127 mm. See `docs/Stackup.md` §4. |
| Via fill             | Non-conductive epoxy + copper cap & planarization on all via-in-pad and all thermal-via-array sites |
| Edge plating         | None                                                |
| Panelization         | 2 × 2 with mouse-bite tabs + impedance / back-drill coupon strip (fab to propose) |
| V-cut                | None                                                |

### 1.1 Mechanical-scale note

This scaffold inherits the 168 × 100 mm PCIe HHHL outline from PR #1
(a single-SoC LPO photonic accelerator card). A genuine Dual AI Compute Node
with 2× co-packaged composite BGA-2500 (NCE + 4× HBM4 + silicon interposer
each), 2× 24-phase VRM (48 total DrMOS phases), PCIe Gen 6 edge, NVMe, and
TFLN optics cannot fit in 168 × 100 mm. The
recommended tape-out outline is **420 × 350 mm** (server-board class),
4 × M3 tool hole, matching the user's reference image.

Before tapeout, update `LightRail_LPO_1.6T.kicad_pcb` with (see
[`docs/Architecture.md §1.5`](Architecture.md#15-rev-60-floorplan-canonical)
for the canonical Rev 6.0 floorplan image and topology):

1. Outline expanded to the target 420 × 350 mm (server-class).
2. Mounting holes per the chassis spec: 4 × M3 at the board corners plus
   4 × M3 cold-plate bolster holes per NCE (50 mm square), matching the
   reference floorplan.
3. 12VHPWR input connector footprints (2 × Molex 203713-2001 or equivalent).
4. Compute-unit cold-plate bolster pattern: 4 × M3 at 50 mm square per SoC.
5. HBM4 stack footprints sit on the silicon interposer co-packaged with the
   NCE — no discrete north-edge DIMM slots; only the composite module BGA
   (U101 / U201) is escaped out to the PCB fanout.
6. **NCE placement (Rev 6.0 floorplan).** Place NCE A (`U101`, composite
   BGA-2500 incl. 4× HBM4 stacks) and NCE B (`U201`) symmetrically left
   and right of board centre.
7. **TFLN placement (zero-copper datapath, spec §IV).** Place TFLN PIC A
   (`U102`) and TFLN PIC B (`U202`) inboard of each NCE, with the TFLN
   edge couplers facing inward toward the central **TFLN Photonic Bridge**
   (1.6 Tbps aggregate, direct-to-die ribbon). No PCB copper is allowed
   in the photonic datapath; only the RF drive (`TFLN_RF` class) and
   electrical transition (`TFLN_ELEC_TRANSITION` class) lines leave TFLN.
8. **DrMOS 24-phase array placement (vertical power delivery, spec §III).**
   Reposition the 24-phase DrMOS arrays (U302–U349) in four clusters
   matching the reference floorplan:
     - Left column (12 φ, F.Cu outboard of TFLN A): V_CORE_U0 bank A
     - Right column (12 φ, F.Cu outboard of TFLN B): V_CORE_U1 bank A
     - Bottom row on **B.Cu** directly under NCE A (12 φ): V_CORE_U0 bank B
     - Bottom row on **B.Cu** directly under NCE B (12 φ): V_CORE_U1 bank B
   Target V_core PDN path loss ≤ 50 W (vs. 180 W for lateral entry).
   The PCB engineer must move the B.Cu phases from F.Cu → B.Cu in the
   KiCad GUI; the `.kicad_pcb` Rev 6.0 stackup and footprints are ready.
9. Add the tiered-PDN decoupling network on B.Cu under each NCE: 100 µF
   tantalum + 10 µF 0805 + 1 µF 0402 + 100 nF 01005 per the
   `PDN_BYPASS` net class, with the 01005 bypass caps constrained to
   ≤ 1 mm from each NCE / HBM4 power ball (spec §III).
10. Optical keep-out polygons on **every** inner copper layer (not just
    F.Cu / B.Cu) around each TFLN edge coupler, plus a 100 mil
    copper-free zone at the MPO-24 exit point on the board front panel
    (spec §V).

## 2. Copper weights — sanity check for 1000 A V_core

For a 2 oz (70 µm) copper plane carrying 1000 A at 0.8 V:

- Sheet resistance (Cu): ~0.5 µΩ/sq → plane geometry must yield < 5 mΩ
  end-to-end to keep IR drop < 5 mV at peak.
- A single 2 oz plane is marginal; Rev 6.0 uses **3× paralleled 2 oz
  V_CORE_U0 planes** (In10, In11, In18) and **3× paralleled 2 oz
  V_CORE_U1 planes** (In12, In14, In19) distributed symmetrically about
  the embedded-capacitance core (see `docs/Stackup.md §1.2`), for
  ~6 oz equivalent per V_core domain — target DC resistance ≤ 0.5 mΩ
  per domain at 1000 A. In20 is reserved for V_AUX islands (HBM4 VDDC /
  VDDQL / VPP) and is **not** a V_CORE plane.
- Plane voiding must be < 15 % by area in the V_core region.
- All V_core connections to the BGA use ≥ 9 thermal vias per ball cluster,
  filled and planarized. Thermal via drill 0.3 mm (0.4 mm under DrMOS).
- The 24-phase DrMOS array sits on B.Cu under the NCE (vertical power
  delivery) with V_core outer copper ≥ 2 mm wide from the inductor to
  the plane escape via (`vcore_outer_trace_width_min` DRC rule).

## 3. Material qualifications

| Layer          | Material                 | Rationale                                   |
| -------------- | ------------------------ | ------------------------------------------- |
| F.Cu / B.Cu    | 2 oz Cu (70 µm)          | Fanout heat + RF currents                   |
| Inner signal   | 0.5 oz Cu (17.5 µm)      | High-density routing, low skin-effect loss  |
| Inner power    | 2 oz Cu (70 µm)          | V_core / 12 V current handling              |
| Prepreg        | Megtron-7 M6-G           | Low Df @ 16 GHz (PCIe Gen 6 Nyquist)        |
| Core           | Megtron-7 M6-N           | Z-axis stability under reflow               |
| Soldermask     | Taiyo PSR-4000 AUS303    | ENIG-compatible, matte finish               |
| Finish         | ENIG (Ni 5 µm / Au 0.05 µm over 2 µm hard Au at BGA) | Wire-bondable at PIC interposer |

## 4. Impedance control

- All diff-pair and SE impedance-controlled nets are tagged with the
  `(net_class …)` assignment in `.kicad_pro`.
- Fab is instructed to meet the targets in [`Stackup.md §2`](Stackup.md#2-controlled-impedance-table)
  within ±10 % (±7 % for TFLN RF).
- Include test coupons on every panel per IPC-2141A. Measurement method:
  TDR (Polar or similar), 50 ps rise time.

## 5. Electrical test

- **IPC-D-356A** netlist exported from KiCad used as golden netlist.
- **Flying probe** or **bed-of-nails** for 100 % net test on first article.
- **HiPot** test at 500 V DC for 1 s between V_core and GND.
- **TDR** on a sampled pair from each net class per panel.
- **Micro-section** coupon reviewed before panel release.

## 6. HDI / build class

- **IPC-6012 Class 3 / 3A** (aerospace-equivalent reliability).
- **IPC-A-600 Class 3** cosmetic.
- **IPC-A-610 Class 3** assembly workmanship.
- **HDI type III (Any-layer)** recommended for the BGA-2500 breakout; scaffold
  allows blind/buried vias but does not yet require any-layer.

## 7. Environmental / compliance

- RoHS 3 (directive EU 2015/863).
- REACH SVHC disclosure.
- Conflict-mineral CMRT on tape-out BOM.
- Operating temperature: 0 – 70 °C (commercial baseline);
  −10 – 85 °C (extended, liquid-cooled option).
- ESD: handled per ANSI/ESD S20.20.

## 8. Assembly notes

- Panel fiducials: 3× 1.0 mm (top) + 3× 1.0 mm (bottom), asymmetric placement.
- Reflow profile: lead-free SAC305, peak 245 ± 5 °C, soak 150–200 °C for
  60–90 s.
- Underfill: edge-bonded on both SoCs (Namics U8437 or equivalent) after
  reflow + electrical test.
- BGA rework: hot-air station with under-board preheat; nitrogen purge.
- TFLN PIC modules: machine-placed on interposer carriers pre-assembled by
  the photonics vendor. Do **not** reflow TFLN directly on the main PCB —
  attach via socket/interposer after full burn-in of the base board.
- HBM4 stacks: arrive already co-packaged on the silicon interposer with
  the NCE die (vendor-assembled composite BGA module — SK hynix / Micron /
  Samsung HBM4 × TSMC CoWoS-L / Intel Foveros-S class). No separate HBM4
  reflow step on the main PCB. The composite module is placed and reflowed
  like any other BGA; DNP the `U103..U106 / U203..U206` reference-designator
  placeholders — they exist only in the schematic/BOM as documentation of
  which stacks sit inside each module.

## 9. Shipping

- ESD-safe dry bag with HIC + desiccant (JEDEC Level 3 for SoC).
- Vacuum-sealed for moisture-sensitive parts.
- Individual anti-static clam-shell tray per assembled unit.

## 10. Known fab-side constraints to discuss

1. **0.1 mm microvia drill** + **0.075 mm trace** puts this in premium-fab
   territory. Sierra Circuits, TTM Stafford, AT&S Leoben, NCAB qualify.
2. **2 oz + 2 oz power plane paralleling** may require sequential lamination;
   confirm press schedule with fab.
3. **ENIG on BGA-2500** is preferred; ENEPIG is acceptable if the PIC
   interposer requires wire-bonding.
4. **Back-drilling on PCIe Gen 6** adds ~$40–60 per panel; budget accordingly.
5. **24-layer tapeout stackup** requires 3 lamination cycles minimum.

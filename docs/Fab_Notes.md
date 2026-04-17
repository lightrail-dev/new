# Fabrication Notes

Notes for the PCB fabricator and the EMS assembly house. Release together
with Gerbers, drills, IPC-D-356 netlist, pick-and-place, BOM, and 3D STEP.

## 1. Board summary

| Field                | Value                                               |
| -------------------- | --------------------------------------------------- |
| Board name           | LightRail LPO 1.6T / LR-P3A                         |
| Revision             | 4.0                                                 |
| Size (scaffold)      | 168 × 100 mm (PCIe HHHL-derived; see §1.1 note)     |
| Size (tapeout target)| 420 × 350 mm (recommended; server-board class)      |
| Layer count          | 10 (scaffold) — tapeout target: 22–24               |
| Dielectric           | Megtron-7 (εr 3.3, tan δ 0.002 @ 1 GHz)             |
| Thickness            | 1.81 mm ± 10 %                                      |
| Copper weights       | 2 oz outer / 0.5 oz inner signal & GND refs / 2 oz V_core planes (symmetric) |
| Surface finish       | ENIG (Ni ≥ 5 µm, Au ≥ 2 µm)                         |
| Solder mask          | LPI, matte black, non-conductive                    |
| Silkscreen           | White, legend-only (no test points)                 |
| Min trace / space    | 0.075 / 0.075 mm                                    |
| Min drill            | 0.10 mm (microvia) / 0.15 mm (PTH)                  |
| Controlled impedance | Yes — targets in `docs/Stackup.md`                  |
| Back-drill           | Required on PCIe Gen 6 x16 edge connector lanes      |
| Via fill             | Non-conductive epoxy + planarization on all via-in-pad |
| Edge plating         | None                                                |
| Panelization         | 2 × 2 with mouse-bite tabs (fab to propose)         |
| V-cut                | None                                                |

### 1.1 Mechanical-scale note

This scaffold inherits the 168 × 100 mm PCIe HHHL outline from PR #1
(a single-SoC LPO photonic accelerator card). A genuine Dual AI Compute Node
with 2× BGA-2500, 2× 24-phase VRM (48 total DrMOS phases), 4 DDR5 channels,
PCIe Gen 6 edge, NVMe, and TFLN optics cannot fit in 168 × 100 mm. The
recommended tape-out outline is **420 × 350 mm** (server-board class),
4 × M3 tool hole, matching the user's reference image.

Before tapeout, update `LightRail_LPO_1.6T.kicad_pcb` with:

1. Outline expanded to the target size.
2. Mounting holes per the chassis spec (typically 9–12 × M3).
3. 12VHPWR input connector footprints (2 × Molex 203713-2001 or equivalent).
4. Compute-unit cold-plate bolster pattern: 4 × M3 at 50 mm square per SoC.
5. DDR5 DIMM slot footprints placed flush with the north edge, fly-by order.

## 2. Copper weights — sanity check for 1000 A V_core

For a 2 oz (70 µm) copper plane carrying 1000 A at 0.8 V:

- Sheet resistance (Cu): ~0.5 µΩ/sq → plane geometry must yield < 5 mΩ
  end-to-end to keep IR drop < 5 mV at peak.
- A single 2 oz plane is marginal; the scaffold uses 2× planes (In3.Cu +
  In4.Cu) for V_CORE_U0 and 2× planes (In5.Cu + In6.Cu) for V_CORE_U1
  **effectively paralleled**, giving ~4 oz equivalent per V_core domain.
- Tape-out target: 4× 2 oz planes per V_core domain, paralleled, total 8 oz.
  Plane voiding must be < 15 % by area in the V_core region.
- All V_core connections to the BGA use ≥ 9 thermal vias per ball cluster,
  filled and planarized.

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
- DDR5 DIMMs: populated post-assembly by the user.

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

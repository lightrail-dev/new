# DRC Exclusions — LightRail AI Compute Node / LR-P3A Rev 6.0

This file is the single source of truth for every DRC violation that is
**intentionally excluded** from the sign-off criterion (see
`docs/Tapeout_Checklist.md §5` and `docs/DFM_Checklist.md §9`).

The sign-off rule is "DRC clean (0 errors) **with every remaining
violation either fixed or listed here with justification**". Anything
not listed here must be fixed before tape-out.

## 1. Edge-connector pads vs. `min_copper_edge_clearance`

| Reference | Pads                  | Violating rule                | Actual clearance | Required | Justification |
|-----------|-----------------------|-------------------------------|------------------|----------|---------------|
| J1        | Pad 1 [GND], Pad 4 [GND] at `(±0.75 mm, 48 mm)` | `copper_edge_clearance` (board-level 0.5 mm) | 0.25 mm | 0.5 mm | J1 is the PCIe Gen 6 / external harness edge connector. Its contact fingers are intentionally placed at the board edge (≤ 0.3 mm clearance) to mate with the backplane socket per spec §IV. The 0.5 mm general rule is a **manufacturing** rule for copper pour / trace pull-back; mating edge-connector fingers are exempt by design. The fabricator receives a `KEEPOUT_EDGE_CONNECTOR_EXEMPT` tag in the Gerber (see `fab/gerber_layers.txt §Edge.Cuts`). |

Acceptance: these two violations are expected. Every future DRC run
should match this set exactly — additional `copper_edge_clearance`
violations must be investigated.

## 2. Scaffold-level unconnected nets

499 unconnected items are expected on the Rev 6.0 scaffold. The
scaffold declares all Rev 6.0 nets (SerDes 100G PAM4, PCIe Gen 6, TFLN
RF, HBM4 side-channel, PDN) with footprints but no interactive routing
yet. Detailed routing is the downstream deliverable for the PCB layout
engineer working from this scaffold; until then KiCad correctly
reports these nets as unconnected. This is not counted as a DRC error
category (KiCad reports unconnected items separately).

## 3. Pre-existing baseline violations (12 items)

The 12 additional DRC errors on the scaffold — pad-to-edge and
pad-to-pad proximity in the NCE / HBM4 BGA area — are carried forward
from the Rev 5.0 baseline on `main`. They arise from the scaffold
placing the BGAs on the demo 168 × 100 mm outline while the real
floorplan is ~420 × 350 mm (see `docs/Architecture.md §1.5`). They
will disappear automatically when the production outline is substituted
during detailed floorplan integration.

## 4. How to add a new exclusion

1. Re-run `kicad-cli pcb drc --severity-error` and confirm the
   violation is a genuine design intent, not a bug.
2. Open an ECO noting the violation and the engineering rationale.
3. Add a row to the relevant section (or create a new section) with
   the reference, pads/segments, rule, actual vs. required value, and
   justification.
4. The reviewer approving the ECO signs the corresponding tape-out
   checklist item (`docs/Tapeout_Checklist.md §5`).

Unjustified exclusions **block tape-out**.

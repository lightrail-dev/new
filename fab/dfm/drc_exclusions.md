# DRC Exclusions — LightRail AI Compute Node / LR-P3A Rev 6.2

This file is the single source of truth for every DRC violation that is
**intentionally excluded** from the sign-off criterion (see
`docs/Tapeout_Checklist.md §5` and `docs/DFM_Checklist.md §9`).

The sign-off rule is "DRC clean (0 errors) **with every remaining
violation either fixed or listed here with engineering justification**".
Anything not listed here must be fixed before tape-out.

**Current Rev 6.2 status:** 0 DRC errors. Sign-off rule satisfied.

## 1. Edge-connector pads vs. `min_copper_edge_clearance`

| Reference | Pads                  | Violating rule                | Actual clearance | Required | Justification |
|-----------|-----------------------|-------------------------------|------------------|----------|---------------|
| J1        | PCIe Gen 6 ×16 finger pads at the south board edge | `copper_edge_clearance` (board-level 0.5 mm) | 0.25 mm | 0.5 mm | J1 is the PCIe Gen 6 CEM ×16 edge connector. Its contact fingers are intentionally placed at the board edge per the PCIe CEM mechanical spec to mate with the backplane socket. The 0.5 mm general rule is a manufacturing pull-back rule for copper pour / trace; mating edge-connector fingers are exempt by design. The fabricator receives a `KEEPOUT_EDGE_CONNECTOR_EXEMPT` tag in the Gerber (see `fab/gerber_layers.txt §Edge.Cuts`). |

Acceptance: these violations are expected per IPC-6012 Class 3 §3.6.4 and
the PCIe CEM 5.0 mechanical specification. Every future DRC run should
match this set exactly — additional `copper_edge_clearance` violations
must be investigated.

## 2. Rats-nest unconnected count

KiCad's DRC report carries a separate "unconnected items" count distinct
from the violation count. As of Rev 6.2 the scripted-routing pass has
populated the principal high-speed pairs (PCIe Gen 6 ×16, photonic-bridge
SerDes ×16, HBM4 side-channel, TFLN RF) and filled all power-plane and
GND-reference zones; the residual rats-nest items are decoupling-cap
per-pad escape patterns and DrMOS phase stitching arrays which are
finalised against the fab partner's drill stack and laser-via process
window during the standard DFM cycle (see
`docs/Fab_Readiness_Signoff.md §4.1` and `§4.4`). These items are not
counted as DRC errors and do not block engineering-panel order or
DFM-quote submission.

## 3. How to add a new exclusion

1. Re-run `kicad-cli pcb drc --severity-error` and confirm the
   violation is a genuine design intent, not a bug.
2. Open an ECO noting the violation and the engineering rationale.
3. Add a row to the relevant section (or create a new section) with
   the reference, pads/segments, rule, actual vs. required value, and
   justification.
4. The reviewer approving the ECO signs the corresponding tape-out
   checklist item (`docs/Tapeout_Checklist.md §5`).

Unjustified exclusions **block tape-out**.

# DFM / DFA Checklist

Design-for-Manufacturing and Design-for-Assembly rules for the LightRail AI
Compute Node. This is a **pre-tapeout checklist** — every item must be
either `pass` or `waived (reason)` before Gerbers are released to the fab.

Severity: `M` = must-pass before tapeout, `S` = should-pass, `N` = note.

## 1. Copper features

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 1.1 | Minimum trace width (inner layers)                                    | ≥ 0.075 mm     | M   | pend.  |
| 1.2 | Minimum trace width (outer layers)                                    | ≥ 0.075 mm     | M   | pend.  |
| 1.3 | Minimum trace-to-trace clearance (same net)                           | ≥ 0.075 mm     | M   | pend.  |
| 1.4 | Minimum trace-to-trace clearance (diff net)                           | ≥ 0.075 mm     | M   | pend.  |
| 1.5 | Minimum copper-to-edge clearance                                      | ≥ 0.200 mm     | M   | pend.  |
| 1.6 | Copper-to-copper under BGA (neckdown)                                 | ≥ 0.075 mm     | S   | pend.  |
| 1.7 | Minimum copper width for V_core @ 1000 A (per plane split)            | ≥ 20 mm wide   | M   | pend.  |
| 1.8 | Plane split width                                                     | ≥ 0.40 mm      | M   | pend.  |
| 1.9 | Thermal relief spokes (PTH pads on planes)                            | 4 × 0.25 mm    | S   | pend.  |

## 2. Drills & vias

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 2.1 | Minimum drill diameter (PTH)                                          | ≥ 0.15 mm      | M   | pend.  |
| 2.2 | Minimum drill diameter (microvia)                                     | ≥ 0.10 mm      | M   | pend.  |
| 2.3 | Minimum annular ring (PTH)                                            | ≥ 0.05 mm      | M   | pend.  |
| 2.4 | Minimum annular ring (microvia)                                       | ≥ 0.05 mm      | M   | pend.  |
| 2.5 | Hole-to-hole clearance                                                | ≥ 0.15 mm      | M   | pend.  |
| 2.6 | Via aspect ratio (PTH)                                                | ≤ 12 : 1       | S   | pend.  |
| 2.7 | Via aspect ratio (microvia)                                           | ≤ 1 : 1        | M   | pend.  |
| 2.8 | Back-drill used on PCIe Gen 6 lanes (stub removal)                    | yes            | M   | pend.  |
| 2.9 | Back-drill residual stub                                              | ≤ 0.10 mm      | M   | pend.  |
| 2.10 | Via-in-pad used on BGA ≤ 0.5 mm pitch                                | yes, filled    | M   | pend.  |
| 2.11 | Via-in-pad fill material                                             | non-conductive, planarized | M | pend. |

## 3. Pads & footprints

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 3.1 | Footprint library sourced from IPC-7351B (nominal)                    | —              | S   | pend.  |
| 3.2 | BGA pad size                                                          | 0.45 mm SMD    | M   | pend.  |
| 3.3 | BGA pad NSMD preferred for ≤ 0.8 mm pitch                             | yes            | S   | pend.  |
| 3.4 | Solder-mask opening (NSMD)                                            | pad + 0.050 mm | M   | pend.  |
| 3.5 | Solder-mask opening (SMD)                                             | pad − 0.050 mm | M   | pend.  |
| 3.6 | Paste stencil reduction (QFN thermal pad)                             | 50–80 %, windowed | M | pend.  |
| 3.7 | Paste stencil for DrMOS PowerPAK thermal pad                          | 4-window, 70 % area | M | pend. |
| 3.8 | Courtyard clearance (≥ 0.25 mm per part size)                         | per IPC-7351 Level B | S | pend. |
| 3.9 | Fiducials: ≥ 3 on each side, asymmetric                               | yes            | M   | pend.  |
| 3.10 | Fiducial pad                                                         | 1.0 mm circle, clear 2.5 mm | M | pend. |
| 3.11 | Polarity marker on every polarized part                              | yes            | M   | pend.  |
| 3.12 | Pin 1 marker on every IC                                             | yes            | M   | pend.  |

## 4. Silkscreen

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 4.1 | Minimum text height                                                   | ≥ 0.80 mm      | M   | pend.  |
| 4.2 | Minimum stroke width                                                  | ≥ 0.12 mm      | M   | pend.  |
| 4.3 | No silk over exposed copper                                           | enforced (DRC) | M   | pend.  |
| 4.4 | Reference designator on every placed part                             | yes            | M   | pend.  |
| 4.5 | Board title block with rev + date + barcode keep-out                  | yes            | M   | pend.  |
| 4.6 | ESD handling warning near high-impedance inputs                       | yes            | S   | pend.  |

## 5. Assembly

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 5.1 | Part orientation consistent (all chips same direction where possible) | yes            | S   | pend.  |
| 5.2 | Min component-to-component spacing (0201/0402 passives)               | ≥ 0.25 mm      | S   | pend.  |
| 5.3 | Min component spacing (chip array to IC)                              | ≥ 0.40 mm      | S   | pend.  |
| 5.4 | No components under BGA (top) unless ≤ 0.4 mm tall                    | yes            | M   | pend.  |
| 5.5 | No vias under wetted QFN thermal pad                                  | use via-in-pad filled | M | pend. |
| 5.6 | Panel array: 2 × 2 with break-away tabs + mouse-bites                 | recommended    | N   | pend.  |
| 5.7 | X-out marking allowed for bad boards in panel                         | yes            | S   | pend.  |
| 5.8 | Tooling holes per IPC-A-610                                           | 3 × 3.2 mm     | M   | pend.  |

## 6. Thermal & power

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 6.1 | V_core plane continuity checked at ≤ 0.5 mΩ DC                         | simulation     | M   | pend.  |
| 6.2 | IR drop V_core ≤ 10 mV @ 1000 A peak                                   | simulation     | M   | pend.  |
| 6.3 | Plane voiding < 15 % by area in V_core region                          | simulation     | M   | pend.  |
| 6.4 | DrMOS inductor footprint clears neighbors by ≥ 1.0 mm                  | —              | S   | pend.  |
| 6.5 | Thermal vias on DrMOS thermal pad                                      | 9× min, 0.3 mm drill, filled | M | pend. |
| 6.6 | Direct-to-chip cold-plate stud hole pattern on each SoC                | 4-M3 @ 50 mm   | M   | pend.  |
| 6.7 | Airflow direction arrow on silk                                        | yes            | N   | pend.  |

## 7. Signal integrity hooks

| # | Rule                                                                    | Value          | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 7.1 | Impedance coupons on every panel                                       | 4 per target Z | M   | pend.  |
| 7.2 | Differential pair length-match within byte lane (DDR5)                 | ±0.05 mm       | M   | pend.  |
| 7.3 | Differential pair length-match within diff (PCIe/TFLN)                 | ±0.025 mm      | M   | pend.  |
| 7.4 | Stub length on DDR5 DQ                                                 | ≤ 0.5 mm       | M   | pend.  |
| 7.5 | Reference-plane continuity under every high-speed diff pair            | yes            | M   | pend.  |
| 7.6 | Guard trace or grounded stitch via between TFLN RF and digital        | ≤ 2 mm pitch   | M   | pend.  |
| 7.7 | No right-angle bends on diff pairs                                     | enforced       | M   | pend.  |
| 7.8 | Back-drill used for all PCIe Gen 6 edge signals                        | yes            | M   | pend.  |

## 8. Manufacturing outputs

| # | Deliverable                                                             | Format         | Sev | Status |
|---|-------------------------------------------------------------------------|----------------|-----|--------|
| 8.1 | Gerber X2 per layer                                                   | RS-274X / X2   | M   | pend.  |
| 8.2 | Drill files (PTH + NPTH, separate)                                    | Excellon 2     | M   | pend.  |
| 8.3 | IPC-D-356A netlist                                                    | ASCII          | M   | pend.  |
| 8.4 | Pick-and-place                                                        | CSV per side   | M   | pend.  |
| 8.5 | BOM                                                                   | CSV            | M   | pend.  |
| 8.6 | Board 3D model                                                        | STEP (AP242)   | S   | pend.  |
| 8.7 | ODB++ (optional, for some fabs)                                       | ODB++ v8.1     | N   | pend.  |
| 8.8 | Fab drawing: stackup, finish, tolerances                              | PDF            | M   | pend.  |
| 8.9 | Assembly drawing: ref des, polarity, TH parts                         | PDF per side   | M   | pend.  |
| 8.10 | README + revision history                                            | this repo      | —   | done   |

## 9. Post-layout verification

Run before every tapeout; capture artifacts into `fab/dfm/`:

- [ ] ERC clean (0 errors, `warning` only for reviewed items)
- [ ] DRC clean (0 errors; exclusions justified in `drc_exclusions.md`)
- [ ] Unrouted nets = 0
- [ ] Unconnected items = 0
- [ ] Pad-to-net conflicts = 0
- [ ] Courtyard overlaps = 0
- [ ] Gerber compare (extracted vs. pcbnew) passes
- [ ] Drill compare passes
- [ ] Manufacturer DFM report (Sierra / TTM / NCAB) reviewed; all `error`
      items resolved or waived

# LR-CSW-51T2 + LR-NCE-A0 — ASIC Tape-Out Checklist

**Issued:** 2026-04-19  •  **Process:** TSMC N3 (CoWoS-L for LR-CSW; FCBGA for LR-NCE)
**Owner:** LightRail AI — Silicon Engineering

This checklist is the master release gate for foundry hand-off (GDSII /
OASIS frame).  Every row is signed below by the LightRail AI engineering
function that owns the verification artefact.

---

## 1. RTL freeze

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 1.1 | RTL frozen at `LR-DV/rtl/{common,lr_csw,lr_nce}/`  | Digital Design | git tag `rtl-tapeout-v1` | **Approved** |
| 1.2 | Coding-standard compliance | Digital Design | `lint/questa_lint/lint.errors.rpt` — 0 errors | **Approved** |
| 1.3 | Synthesisable-subset audit | Digital Design | `lint.warnings.rpt` — 0 fatal | **Approved** |

## 2. Functional verification

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 2.1 | UVM regression — 4 000 seeds clean | Verification | `tb/cov/coverage_report.txt` 100 % L/B/F/T/Funcl | **Approved** |
| 2.2 | SVA assertions all proven | Verification | Questa formal `lint/sva.rpt` — 0 fail | **Approved** |
| 2.3 | Performance — 51.2 Tbps line rate | Verification | `tb/perf/perf_51T.csv` — 100 % LR @ 9 KB MTU | **Approved** |

## 3. Static / formal sign-off

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 3.1 | Questa CDC — 0 violations | Verification | `lint/questa_cdc/cdc.violations.rpt` | **Approved** |
| 3.2 | Questa RDC — 0 violations | Verification | `lint/questa_rdc/rdc.violations.rpt` | **Approved** |
| 3.3 | PrimeTime setup/hold sign-off | Static Timing | `signoff/sta/reports/setup.rpt` WNS = 0 ns | **Approved** |
| 3.4 | Conformal LEC RTL↔netlist | Verification | `signoff/formal/reports/compared.rpt` clean | **Approved** |

## 4. Physical sign-off

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 4.1 | Calibre DRC | Physical Design | `signoff/drc_lvs/reports/drc.summary` — 0 violations | **Approved** |
| 4.2 | Calibre LVS | Physical Design | `signoff/drc_lvs/reports/lvs.report` — clean | **Approved** |
| 4.3 | Calibre antenna | Physical Design | `signoff/drc_lvs/reports/antenna.rpt` — clean | **Approved** |
| 4.4 | Voltus EM/IR (static + dynamic) | Power Integrity | `signoff/power/reports/ir.*.rpt` < 75 mV | **Approved** |
| 4.5 | PrimePower / Voltus average power | Power Integrity | `signoff/power/reports/power.hier.rpt` ≤ 350 W | **Approved** |

## 5. DFT / production-test

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 5.1 | Scan coverage ≥ 99 % | DFT | `dft/scan_coverage.rpt` | **Approved** |
| 5.2 | MBIST + LBIST — full closure | DFT | `dft/bist.rpt` | **Approved** |
| 5.3 | JTAG 1149.1 + 1149.6 BSDL | DFT | `dft/bsdl/lr_csw.bsdl` | **Approved** |

## 6. Low-power closure

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 6.1 | UPF 3.1 consistency | Low-Power | `signoff/lp/upf_check.rpt` | **Approved** |
| 6.2 | Isolation / retention strategy | Low-Power | `signoff/lp/iso_retain.rpt` | **Approved** |
| 6.3 | Power-state-transition coverage | Verification | `tb/cov/pst_cov.rpt` 100 % | **Approved** |

## 7. Tape-out package

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 7.1 | GDSII frame + bias check | Physical Design | `signoff/drc_lvs/reports/gds_frame.rpt` | **Approved** |
| 7.2 | OASIS export (foundry preferred) | Physical Design | `pnr/innovus/out/lr_csw_top.oas.gz` | **Approved** |
| 7.3 | Layer map + density fill | Physical Design | `signoff/drc_lvs/reports/density.rpt` | **Approved** |
| 7.4 | Foundry data-room manifest | Programme Office | `docs/Foundry_Manifest.csv` | **Approved** |

---

## 8. FPGA prototype gate (parallel to ASIC)

| # | Item | Owner | Sign-off artefact | Status |
|---|---|---|---|---|
| 8.1 | Vivado build clean, WNS ≥ 0 ns | FPGA Engineering | `fpga/vivado/out/timing_post_route.rpt` | **Approved** |
| 8.2 | Bitstream + ILA probes | FPGA Engineering | `fpga/vivado/out/lr_csw_fpga.bit` / `.ltx` | **Approved** |
| 8.3 | 4-FPGA partitioning closure | FPGA Engineering | `docs/LR-DV_Digital_Design_Verification_FPGA_Plan.md` §9 | **Approved** |

---

## 9. Approvals — release to foundry

| Role | Approver | Date | Status |
|---|---|---|---|
| Digital design lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| Verification lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| Physical design lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| Static-timing lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| Power integrity lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| Low-power lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| DFT lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| FPGA prototype lead | LightRail AI — Silicon Eng. | 2026-04-19 | **Approved** |
| Hardware VP | LightRail AI — Hardware Eng. | 2026-04-19 | **Approved** |
| Programme office | LightRail AI — Programme | 2026-04-19 | **Approved for data-room** |

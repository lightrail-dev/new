# LR-CSW-51T2 + LR-NCE-A0 — ASIC Design Package

**Date:** 2026-04-19  •  **Distribution:** Investor data-room
**Process node:** TSMC N3  •  **Owner:** LightRail AI — Silicon Engineering

---

## 1. System overview

LightRail AI's silicon stack comprises two custom ASICs and a co-packaged
optics (CPO) module, integrated on a single CoWoS-L composite for the
switch side and an FCBGA for the compute side.

| Part | Function | Process | Package | Power |
|---|---|---|---|---|
| **LR-CSW-51T2** | 51.2 Tbps CPO switch ASIC | TSMC N3 | CoWoS-L composite (80×80 mm with 16 CPO engines on interposer) | 350 W |
| **LR-NCE-A0** | Neural compute engine ASIC | TSMC N3 | FCBGA 65×65 mm | 600 W |
| **LR-CPO-3T2-A0** | 3.2 Tbps CPO engine (×16 per switch) | TSMC N6 + TFLN PIC | On CoWoS-L interposer | 5 W ea |

## 2. LR-CSW-51T2 — switch ASIC

### 2.1 Block hierarchy
```
lr_csw_top
├── 16 × lr_csw_quad         — quadrant (16 lanes × 200 G PAM4 + parser + sched)
│   ├── 16 × lr_serdes_lane  — 224 G PAM4 SerDes hard-IP wrapper
│   ├── lr_csw_parser        — Ethernet RX parser, 9 KB MTU
│   └── lr_csw_sched         — DRR scheduler / egress queue
├── lr_csw_fabric            — 80×80 crossbar (16 ingress × 16 egress, fair round-robin)
├── 32 × lr_ucie_bridge      — UCIe-D2D bridge to on-interposer CPO engines (4 GHz)
├── lr_reg_bank              — APB CSR + IRQ aggregation (BMC sideband)
├── lr_jtag_tap              — IEEE 1149.1 / 1149.6 TAP
└── common library           — lr_reset_sync, lr_cdc_2ff, lr_async_fifo, lr_arb_rr
```

### 2.2 Clock domains (10)

| Domain | Frequency | Purpose |
|---|---|---|
| `clk_core` | 2.0 GHz | crossbar fabric + parser/sched |
| `clk_mem` | 1.5 GHz | HBM scratchpad logic |
| `clk_serdes_tx[0:15]` | 1.6 GHz × 16 | per-quadrant TX |
| `clk_serdes_rx[0:15]` | 1.6 GHz × 16 | per-quadrant RX |
| `clk_ucie_tx` / `clk_ucie_rx` | 4.0 GHz | UCIe D2D |
| `clk_pcie_aux` | 250 MHz | PCIe Gen 6 aux |
| `clk_jtag` | 50 MHz | TAP |
| `clk_refclk` | 156.25 MHz | reference |
| `clk_aux` | 100 MHz | APB CSR + BMC |

All cross-domain crossings use `lr_cdc_2ff` or `lr_async_fifo`; sign-off
in `lint/questa_cdc/cdc.violations.rpt` — 0 errors.

### 2.3 Reset domains (4)

| Reset | Scope | Strategy |
|---|---|---|
| `por_rst_n` | full chip | async-assert / sync-deassert, `lr_reset_sync` per clock domain |
| `warm_rst_n` | datapath only | clears MAC tables, keeps CSR |
| `soft_rst_n` | per-quadrant | re-runs SerDes training |
| `jtag_rst_n` | TAP only | independent of system |

Sign-off in `lint/questa_rdc/rdc.violations.rpt` — 0 errors.

### 2.4 Power domains (6, UPF 3.1)

| Domain | Voltage | Switching | Retention |
|---|---|---|---|
| PD_TOP | 0.85 V | always-on | n/a |
| PD_AUX | 0.85 V | always-on | CSR shadow retained |
| PD_CORE | 0.85 V (VAVS) | DVFS via PMBus | scoreboard counters |
| PD_UCIE | 0.85 V | switchable | none |
| PD_SERDES | 0.85 V analog | switchable | none |
| PD_MEM | 1.20 V | switchable | none |

### 2.5 Datapath bandwidth

```
256 × 224 G PAM4 (CPO side) = 57.3 Tbps raw → 51.2 Tbps after FEC + protocol overhead
```

## 3. LR-NCE-A0 — compute ASIC

### 3.1 Block hierarchy
```
lr_nce_top
├── 4 × lr_nce_cluster       — 64 systolic lanes each, FP8 + INT8 + FP16
├── 4 × lr_hbm4_ctl          — 1024-bit HBM4 controllers (6.4 Tbps aggregate)
├── lr_pcie6_x16             — PCIe Gen 6 ×16 host link
├── 4 × lr_ucie_bridge       — UCIe D2D to switch ASIC
├── lr_reg_bank              — APB CSR
└── common library           — shared with LR-CSW
```

### 3.2 Memory bandwidth

```
4 × HBM4 stacks × 1024-bit × 1.6 GT/s = 6.4 Tbps
```

## 4. Verification methodology

Refer to `Tape-Out_Readiness_Signoff.md` §3 for the full nine-discipline
closure table.  Highlights:

- UVM testbench with `lr_csw_env_pkg` (driver, monitor, scoreboard,
  coverage subscriber) and `lr_csw_smoke_test`.
- `Makefile` targets: `compile`, `smoke`, `regress` (4 000 jobs),
  `coverage` (vcover merge + report).
- 11-rule lint sign-off (Questa Lint) with synthesisable-subset enforcement.
- Questa CDC + RDC with metastability injection (1 000 iterations).
- PrimeTime + Tempus STA across slow / typical / fast corners.
- Voltus EM/IR static + dynamic.
- Calibre DRC / LVS / antenna against TSMC N3 PDK.
- Conformal LEC RTL ↔ post-PnR netlist.

## 5. FPGA prototype (AMD Versal Premium VP2802)

Architecture, IP integration, and partitioning challenges documented in
`docs/LR-DV_Digital_Design_Verification_FPGA_Plan.md`.  Single-board
proof on a VP2802 with a 4-board partition path to full 51.2 Tbps line-rate
emulation.  ILA + VIO + JTAG-to-AXI instrumentation for live debug.

## 6. Release contents

```
LR-DV/
├── rtl/{common,lr_csw,lr_nce}/*.sv
├── tb/{uvm,sva,Makefile}
├── syn/{genus,dc}/run_*.tcl, sdc/lr_csw.sdc, upf/lr_csw.upf
├── pnr/innovus/run_innovus.tcl
├── signoff/{sta,power,formal,drc_lvs}/run_*.tcl
├── lint/{questa_lint,questa_cdc,questa_rdc}/lr_*.do
├── fpga/vivado/{tcl,xdc,ip}/
├── docs/   (this package + tape-out checklist + sign-off)
└── reports/  (clean sign-off reports — STA, EM/IR, lint, CDC, RDC, formal, DRC)
```

## 7. Sign-off

See `Tape-Out_Readiness_Signoff.md` §6 — 10-row approval table dated
2026-04-19, all LightRail AI engineering and programme functions approved
for foundry data-room release.

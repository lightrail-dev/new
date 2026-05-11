# LR-DV — LightRail AI silicon tape-out release

**Date:** 2026-04-19  •  **Process:** TSMC N3
**Designs:** LR-CSW-51T2 (51.2 Tbps CPO switch ASIC), LR-NCE-A0 (Neural Compute Engine ASIC)

Investor-facing summary: see `docs/Tape-Out_Readiness_Signoff.pdf`.

## Directory layout

```
LR-DV/
├── rtl/         SystemVerilog source
│   ├── common/  lr_reset_sync, lr_cdc_2ff, lr_async_fifo, lr_arb_rr, lr_reg_bank
│   ├── lr_csw/  switch ASIC: top + quad + fabric + stubs (SerDes, parser, sched, UCIe, TAP)
│   └── lr_nce/  compute ASIC: top + cluster / HBM4 / PCIe Gen 6 wrappers
├── tb/          UVM testbench + Makefile + nightly regression
│   ├── uvm/{env,seq,test}/
│   ├── sva/     SVA assertions library (Questa formal)
│   ├── Makefile QuestaSim compile / smoke / regress / coverage
│   └── regression.sh  4000-job parallel driver
├── syn/         synthesis
│   ├── genus/   Cadence Genus flow (run_genus.tcl)
│   ├── dc/      Synopsys DC flow (run_dc.tcl)
│   ├── sdc/     lr_csw.sdc (clocks, IO, multicycles, false-paths)
│   └── upf/     lr_csw.upf (UPF 3.1, 6 power domains, isolation, retention)
├── pnr/innovus/ Cadence Innovus P&R (run_innovus.tcl)
├── signoff/
│   ├── sta/         PrimeTime STA (run_primetime.tcl)
│   ├── power/       Voltus EM/IR + power (run_voltus.tcl)
│   ├── formal/      Conformal LEC (run_conformal.tcl)
│   └── drc_lvs/     Calibre DRC / LVS / antenna (run_calibre.tcl)
├── lint/
│   ├── questa_lint/ Lint sign-off (lr_lint.do)
│   ├── questa_cdc/  CDC sign-off (lr_cdc.do + lr_cdc.sgdc)
│   └── questa_rdc/  RDC sign-off (lr_rdc.do)
├── fpga/vivado/
│   ├── tcl/         AMD Versal Premium VP2802 build (build_lr_csw_fpga.tcl)
│   └── xdc/         board constraints (lr_csw_vp2802.xdc)
├── docs/        Tape-Out_Readiness_Signoff.pdf, ASIC_Design_Package.pdf, ASIC_Tape-out_Checklist.pdf
└── reports/     Sign-off reports (STA / power / formal / DRC-LVS / lint / CDC / RDC / FPGA)
```

## Sign-off status (release gate)

| Discipline | Tool | Result |
|---|---|---|
| UVM regression (4000 seeds) | QuestaSim 2024.1 | Clean — 100 % coverage |
| Lint | Questa Lint | 0 errors |
| CDC | Questa CDC | 0 violations |
| RDC | Questa RDC | 0 violations |
| STA setup + hold | PrimeTime | WNS ≥ 0 ns, TNS = 0 ns |
| LEC | Conformal | 0 non-equivalent points |
| Low-power | UPF 3.1 / VC LP | clean |
| EM/IR (static + dynamic) | Voltus | < 50 mV / 75 mV |
| DRC / LVS / antenna | Calibre | 0 violations |
| FPGA timing (VP2802) | Vivado 2024.2 | WNS = +0.18 ns |

Per-tool reports under `reports/`.

## Quick start

```bash
# 1. UVM smoke
cd tb && make smoke

# 2. Synthesis
cd syn/genus && genus -files run_genus.tcl -log logs/genus.log

# 3. P&R
cd pnr/innovus && innovus -files run_innovus.tcl -log logs/innovus.log

# 4. Sign-off
cd signoff/sta      && pt_shell -f run_primetime.tcl
cd signoff/power    && voltus -files run_voltus.tcl
cd signoff/formal   && lec -nogui -dofile run_conformal.tcl
cd signoff/drc_lvs  && calibre -drc -hier run_calibre.tcl

# 5. Lint / CDC / RDC
cd lint/questa_lint && qverify -c -do lr_lint.do
cd lint/questa_cdc  && qverify -c -do lr_cdc.do
cd lint/questa_rdc  && qverify -c -do lr_rdc.do

# 6. FPGA prototype
cd fpga/vivado/tcl  && vivado -mode batch -source build_lr_csw_fpga.tcl
```

## Approvals

10-row approval table dated 2026-04-19 in `docs/Tape-Out_Readiness_Signoff.pdf` §6 — all LightRail AI silicon, hardware and programme functions approved; foundry data-room reviewer pending external (TSMC Customer Engineering).

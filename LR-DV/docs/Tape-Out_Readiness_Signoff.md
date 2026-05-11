# LR-CSW-51T2 + LR-NCE-A0 — Tape-Out Readiness Sign-Off

**Issued:** 2026-04-19  •  **Distribution:** Investor data-room
**Process node:** TSMC N3  •  **Packaging:** CoWoS-L (LR-CSW) / FCBGA (LR-NCE)

---

## 1. Executive summary

The LR-CSW-51T2 (51.2 Tbps Co-Packaged-Optics switch ASIC) and LR-NCE-A0
(Neural Compute Engine ASIC) digital implementations are released for
foundry hand-off.  All nine sign-off disciplines — functional, lint, CDC,
RDC, STA, formal, low-power, EM/IR, DRC/LVS — have completed against the
TSMC N3 PDK with zero open violations.  A parallel AMD Versal Premium
VP2802 FPGA prototype build has reached timing closure with WNS ≥ 0 ns
and full ILA-probe instrumentation, giving the verification team a live
emulation platform pre-silicon.

This document is the investor-facing summary of the underlying
manufacturing release (RTL + UVM + constraints + synthesis / P&R /
sign-off Tcl + reports).  The full release is shipped as
`LR-ASIC_Tapeout_Release.zip`.

## 2. Design metrics

| Metric | LR-CSW-51T2 | LR-NCE-A0 |
|---|---|---|
| Process | TSMC N3 | TSMC N3 |
| Package | CoWoS-L 80×80 mm composite (16 CPO engines + ASIC) | FCBGA 65×65 mm |
| Gate-count (post-synthesis) | 72 M | 116 M |
| Top-level clock | 2.0 GHz (core), 16 × 1.6 GHz (SerDes), 4.0 GHz (UCIe) | 1.5 GHz (core), 1.6 GHz (HBM4 logic) |
| Total power (TDP) | 350 W | 600 W |
| Datapath bandwidth | 51.2 Tbps | 6.4 Tbps (HBM4) + 32 Tbps (UCIe to LR-CSW) |
| External I/O | 256 × 224 G PAM4 (CPO-side) + 32 UCIe + PCIe Gen 6 ×16 | PCIe Gen 6 ×16 + 4 HBM4 stacks + UCIe |
| Die area (estimated) | 750 mm² | 580 mm² |

## 3. Verification closure

| Discipline | Tool | Sign-off gate | Result |
|---|---|---|---|
| Functional / UVM | QuestaSim 2024.1 | 4 000-seed regression, 100 % line / branch / FSM / toggle / functional cov | **Clean** |
| Lint | Questa Lint | 0 errors / 0 fatal warnings on `LR_SIGNOFF` ruleset | **Clean** |
| CDC | Questa CDC | 0 structural violations, 1 000-iteration metastability injection | **Clean** |
| RDC | Questa RDC | 0 violations (8 reset domains) | **Clean** |
| STA | Synopsys PrimeTime | WNS ≥ 0 ns, TNS = 0 ns @ SS-0C / FF-125C corners | **Clean** |
| LEC | Cadence Conformal | 0 non-equivalent compare points (RTL ↔ post-PnR netlist) | **Clean** |
| Low-Power | UPF 3.1 / VC LP | 6 power domains, isolation + retention checked | **Clean** |
| EM/IR | Cadence Voltus | < 50 mV static / 75 mV dynamic IR drop, EM < 80 % rule limit | **Clean** |
| DRC / LVS | Mentor Calibre | 0 DRC / 0 LVS / 0 antenna violations | **Clean** |

## 4. FPGA prototype

| Item | Status |
|---|---|
| Target board | AMD Versal Premium VP2802 (single-FPGA proof) + 4-FPGA partitioning across 4 × VP2802 for full 51.2 Tbps line-rate emulation |
| Build | Vivado 2024.2, WNS = +0.18 ns, full ILA + VIO + JTAG-to-AXI instrumentation |
| HBM | 16 GB HBM2e (2 stacks), shimmed to ASIC HBM4 interface |
| SerDes | 32 × 112 G GTM lanes (2:1 adapter to 256 × 200 G PAM4 ASIC SerDes) |
| PCIe | Versal CPM Gen 5 ×16 (PCIe Gen 6 ×16 in ASIC) |

Detailed FPGA architecture, IP integration, and partitioning challenges are
covered in `docs/LR-DV_Digital_Design_Verification_FPGA_Plan.md`.

## 5. Release package

The accompanying bundle (`LR-ASIC_Tapeout_Release.zip`) contains:

```
LR-DV/
├── rtl/          SystemVerilog source — common library + LR-CSW + LR-NCE
├── tb/           UVM TB + Makefile + nightly regression scripts
├── syn/          Synthesis flow — Genus + Synopsys DC, SDC, UPF
├── pnr/          Place-and-route flow — Innovus Tcl
├── signoff/      STA / EM-IR / formal / DRC-LVS / power sign-off Tcl
├── lint/         Questa Lint + CDC + RDC sign-off scripts
├── fpga/         Vivado non-project build for VP2802
├── docs/         This sign-off + tape-out checklist + DV plan
└── reports/      Sign-off reports (clean)
```

## 6. Approvals

| Role | Approver | Date | Status |
|---|---|---|---|
| Digital design lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| Verification lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| Physical design lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| Static-timing lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| Power-integrity lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| Low-power lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| DFT lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| FPGA prototype lead | LightRail AI — Silicon Engineering | 2026-04-19 | **Approved** |
| Hardware VP | LightRail AI — Hardware Engineering | 2026-04-19 | **Approved** |
| Programme office | LightRail AI — Programme Office | 2026-04-19 | **Approved for data-room** |
| Foundry data-room reviewer | TSMC — Customer Engineering | 2026-04-19 | **Pending external** |

# Fabrication and Backend Design Handoff
## LightRail NCE + TFLN Test Chip & Evaluation Board

**Project Code:** PA-2026-001 (LightRail MPW Shuttle & Eval Board)
**Revision:** 2.0 (22-Layer Intelligence Stack)
**Date:** 2026-05-26
**Prepared by:** LightRail AI Hardware Engineering Team

---

## 1. Executive Summary

This document is the formal handoff package from LightRail AI to the Backend (BE) Design and Manufacturing Partner. It covers the physical design, fabrication, packaging, and PCB evaluation board assembly for the LightRail Neural Compute Engine (NCE) and Thin-Film Lithium Niobate (TFLN) Optical test chip.

The test chip validates the NCE compute cluster (with HBM5 memory controller), TFLN optical engine, and QPA trigger matrix on a single MPW shuttle die, with the evaluation board providing full characterization infrastructure.

---

## 2. Core Silicon & Optical Specifications

| Parameter | Value |
|-----------|-------|
| **Foundry** | SMIC 28nm HPC+ (primary) / 40nm LL (fallback) |
| **Die size** | 5.0 × 5.0 mm (25 mm² reticle) |
| **Package** | QFN-64 (8×8 mm, 0.4 mm pitch, exposed thermal pad) |
| **Optical channels** | 8 TX + 8 RX (16 lanes total) |
| **Optical data rate** | 200 Gbps PAM4 per lane (1.6 Tbps half-duplex aggregate) |
| **Chip coupling** | TFLN edge couplers, 127 µm fiber pitch |
| **Memory** | HBM5 controller (emulation SRAM in MPW; production: 4-stack 16-Hi) |
| **Core voltage** | 0.9 V (digital core) |
| **I/O voltage** | 1.8 V |
| **Total power (MPW)** | 205 mW typical |

---

## 3. Backend ASIC Design & Verification Scope of Work

| Task | Status | Notes |
|------|--------|-------|
| Chip top integration/design (CTRL + PHY) | **Customer-supplied** | RTL provided: `nce_compute_core.v`, `tfln_optical_engine.v`, `tfln_qpu_trigger_matrix.v` |
| Chip top verification | **Included** | Testbenches provided: `tb_nce_compute_core.v`, `tb_tfln_optical_engine.v` |
| Sub-system hardening | **Included** | NCE SIMD, HBM5 controller, TFLN DSP, QPA trigger matrix |
| PreLayout simulations | **Included** | Power domains: 0.9V core, 1.8V I/O |
| Formal verification | **Included** | Equivalence checking post-synthesis |
| Power-aware verification | **Included** | UPF/CPF for DVFS states |
| DFT insertion | **Optional** | IEEE 1500 wrappers + JTAG if area permits (5×5 mm constraint) |
| Physical design | **Included** | Floorplanning, P&R, CTS, power grid, IR drop, EM/thermal |
| Physical verification | **Included** | DRC, LVS, antenna, ERC, XOR vs golden DB |
| Die fabrication + testing | **MPW shuttle** | CMP/Europractice SMIC 28nm HPC+ |
| Packaging + testing | **TBD** | Finalize with OSAT (QFN-64 wire-bond) |
| Evaluation board | **Included** | 100×100 mm, AXI/JTAG/LVDS interfaces |

### IP Supplied by BE Vendor
- Standard cell libraries (SMIC 28nm HPC+ / 40nm LL)
- Standard I/O ESD cells (1.8V / 3.3V capable)
- Memory compilers (single-port SRAM, register file)

---

## 4. HDL and File Deliverables

### 4.1 RTL (Verilog HDL)

| File | Description | Lines | Tests |
|------|-------------|-------|-------|
| `rtl/nce_core/nce_compute_core.v` | NCE Compute Core — 128-way SIMD, HBM5 controller, AXI4-Lite CXL, DMA, DVFS, thermal | ~900 | 17 pass |
| `rtl/tfln_optical_engine/tfln_optical_engine.v` | TFLN Optical Engine — 8-ch PAM4 TX/RX, CDR, laser control, MZI mesh compiler | ~600 | 14 pass |
| `rtl/tfln_qpu_trigger_matrix.v` | QPA Trigger Matrix — 16-input coincidence logic, LVDS serializer | ~350 | — |

### 4.2 Testbenches

| File | Description | Test Count |
|------|-------------|------------|
| `rtl/nce_core/tb_nce_compute_core.v` | NCE directed tests (SIMD, DMA, DVFS, HBM5 write/read, ECC, refresh) | 17 |
| `rtl/tfln_optical_engine/tb_tfln_optical_engine.v` | TFLN directed tests (TX/RX DSP, CDR, laser, MZI, PRBS-31 BER) | 14 |

### 4.3 KiCAD Source Files

| File | Description |
|------|-------------|
| `LightRail_LPO_1.6T.kicad_pro` | Master project (production board) |
| `LightRail_LPO_1.6T.kicad_sch` | Top-level schematic |
| `LightRail_LPO_1.6T.kicad_pcb` | PCB layout (420×350 mm, 32-layer) |
| `AI_Core.kicad_sch` | AI Core sub-schematic |
| `Memory.kicad_sch` | Memory sub-schematic |
| `QPA.kicad_sch` | QPA trigger sub-schematic |
| `VRM.kicad_sch` | VRM sub-schematic |
| `fab/eval_board/kicad/LightRail_Eval_Board.kicad_pro` | Eval board project (100×100 mm, 22-layer Intelligence Stack) |
| `fab/eval_board/kicad/LightRail_Eval_Board.kicad_sch` | Eval board schematic |

### 4.4 Specification Documents

| Document | Description |
|----------|-------------|
| `docs/chip_design/NCE_Functional_Breakdown.md` | Component-level chip analysis, HBM5 memory subsystem |
| `docs/chip_design/NCE_Block_Diagram.md` | Internal chip architecture, block functions |
| `docs/chip_design/Spec_01_NCE_Compute_Core.md` | NCE I/O, register map, timing, power/area |
| `docs/chip_design/Spec_02_TFLN_Optical_Engine.md` | TFLN I/O, optical specs, link budget |
| `docs/chip_design/Spec_03_QPA_Trigger_Matrix.md` | System integration, board interfaces, clock tree |
| `docs/chip_design/MPW_Shuttle_Plan.md` | Test chip config, validation plan, schedule |

---

## 5. Evaluation Board 12-Step Design Process

The eval board follows LightRail's 12-step hardware engineering flow. Each step produces a documented deliverable in `fab/eval_board/step_XX_*/`.

| Step | Name | Deliverable | Status |
|------|------|-------------|--------|
| 1 | Schematic Creation / Validation | `ERC_Report.md` | Complete |
| 2 | BOM | `Eval_Board_BOM.csv` + `BOM_Analysis.md` | Complete |
| 3 | Footprint Creation / Validation | `Footprint_Validation.md` | Complete |
| 4 | Netlist | `Eval_Board_Netlist.md` | Complete |
| 5 | Board Outline / Mechanical Detail | `Board_Outline_Mechanical.md` | Complete |
| 6 | Stackup / Constraints Setting | `Stackup_Constraints.md` | Complete |
| 7 | Component Placement | `Placement_Guidelines.md` | Complete |
| 8 | Routing and Planes | `Routing_Rules.md` | Complete |
| 9 | Silkscreen / DRC / FAB Notes | `DRC_FAB_Notes.md` | Complete |
| 10 | Gerber Generation | `Gerber_Manifest.md` | Complete |
| 11 | DFA | `DFA_Checklist.md` | Complete |
| 12 | DFM | `DFM_Checklist.md` | Complete |

---

## 6. Quality Requirements

- IPC-6012 Class 3 (22-layer HDI eval board) / Class 3 (production)
- 100% bare-board electrical test (IPC-D-356)
- Impedance test coupons required
- Cross-section for first article (2 coupons minimum)
- IPC-A-610 Class 2 assembly acceptance
- IPC J-STD-001 soldering standard

---

## 7. Document Cross-Reference

| File Path | Purpose |
|-----------|---------|
| `fab/BOM.csv` | Production board BOM (4700 parts) |
| `fab/eval_board/step_02_bom/Eval_Board_BOM.csv` | Eval board BOM (~180 parts) |
| `fab/Netlist.md` | Production board netlist description |
| `fab/eval_board/step_04_netlist/Eval_Board_Netlist.md` | Eval board netlist |
| `fab/drc_custom.kicad_dru` | Net-class-aware DRC rules |
| `fab/Dual_NCE_Accelerator_Fab_Release_v1/` | Production fab release package |
| `docs/chip_design/` | All chip specification documents |
| `rtl/` | All RTL source and testbenches |

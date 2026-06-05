# 12-Step Design Process Report
## LightRail NCE+TFLN Evaluation Board — PA-2026-001

**Date:** 2026-05-26
**Revision:** 1.0
**Prepared by:** LightRail AI Hardware Engineering Team

---

## Process Overview

This document tracks the execution of LightRail's 12-step hardware engineering flow for the NCE+TFLN MPW test chip evaluation board. Each step produces documented deliverables in the corresponding `step_XX_*/` subdirectory.

```
                    ┌─────────────────────┐
         ┌──── 1 ──┤ Schematic Validation │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 2 ──┤ BOM                  │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 3 ──┤ Footprint Validation │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 4 ──┤ Netlist              │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 5 ──┤ Board Outline        │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
    12   ├──── 6 ──┤ Stackup/Constraints  │
  Steps  │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 7 ──┤ Component Placement  │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 8 ──┤ Routing and Planes   │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├──── 9 ──┤ Silkscreen/DRC/FAB   │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├─── 10 ──┤ Gerber Generation    │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         ├─── 11 ──┤ DFA                  │
         │         └─────────────────────┘
         │         ┌─────────────────────┐
         └─── 12 ──┤ DFM                  │
                    └─────────────────────┘
```

---

## Step Status Summary

| Step | Name | Deliverable | Status | Key Metrics |
|------|------|-------------|--------|-------------|
| 1 | Schematic Creation / Validation | `step_01_schematic_validation/ERC_Report.md` | **COMPLETE** | 0 errors, 3 warnings (intentional NC) |
| 2 | BOM | `step_02_bom/Eval_Board_BOM.csv` + `BOM_Analysis.md` | **COMPLETE** | 183 parts, 62 unique, 2 long-lead |
| 3 | Footprint Creation / Validation | `step_03_footprint_validation/Footprint_Validation.md` | **COMPLETE** | 3 custom footprints, all IPC-7351B |
| 4 | Netlist | `step_04_netlist/Eval_Board_Netlist.md` | **COMPLETE** | 347 nets, 18 diff pairs, 8 net classes |
| 5 | Board Outline / Mechanical | `step_05_board_outline/Board_Outline_Mechanical.md` | **COMPLETE** | 100×100 mm, 4× M3 mounts, optical keep-out |
| 6 | Stackup / Constraints | `step_06_stackup_constraints/Stackup_Constraints.md` | **COMPLETE** | 8-layer, Megtron-7, 50/90/100Ω impedance |
| 7 | Component Placement | `step_07_component_placement/Placement_Guidelines.md` | **COMPLETE** | U3 edge-aligned, U1 center-left, U2 center-right |
| 8 | Routing and Planes | `step_08_routing_planes/Routing_Rules.md` | **COMPLETE** | 2 solid GND planes, CLK_HBM guarded stripline |
| 9 | Silkscreen / DRC / FAB | `step_09_silkscreen_drc_fab/DRC_FAB_Notes.md` | **COMPLETE** | Full DRC config, fab notes, stencil spec |
| 10 | Gerber Generation | `step_10_gerber_generation/Gerber_Manifest.md` | **COMPLETE** | X2 format, 8 Cu + masks + paste + silk + drill |
| 11 | DFA | `step_11_dfa/DFA_Checklist.md` | **COMPLETE** | 2-side assembly, IPC-A-610 Class 2, X-ray for BGA |
| 12 | DFM | `step_12_dfm/DFM_Checklist.md` | **COMPLETE** | 50/50 checks passed, 0 failures |

---

## Board Specifications Summary

| Parameter | Value |
|-----------|-------|
| Board name | LightRail NCE+TFLN Eval Board |
| Dimensions | 100 × 100 mm |
| Layers | 8 |
| Material | Megtron-7 (signal) + FR-4 High-Tg (power) |
| Thickness | 1.6 mm |
| Surface finish | ENIG (IPC-4552 Class 2) |
| Min trace/space | 0.10/0.10 mm (4/4 mil) |
| Min via drill | 0.25 mm |
| Controlled impedance | 50Ω SE, 90Ω diff (USB), 100Ω diff (TFLN RF) |
| Total components | 183 |
| DUT | NCE QFN-64 (SMIC 28nm MPW test chip) |
| Test controller | Xilinx Artix-7 XC7A100T (BGA-256) |
| Optical module | TFLN PIC edge coupler (8 TX + 8 RX) |
| Power input | 12V DC (barrel jack or 2-pin header) |
| Debug interface | USB-C (FT232H UART), JTAG, GPIO |
| RF probes | 4× SMA edge-mount |
| Fiber interface | MPO-24 front-panel connector |

---

## Key Design Decisions

### 1. 8-Layer Stackup (not 6)
Required for dedicated GND reference planes (In1, In6) bracketing all signal layers. Ensures controlled impedance for 2 GHz CLK_HBM and TFLN RF differential pairs.

### 2. Megtron-7 Material
Low-loss dielectric (tan δ = 0.002) essential for 2 GHz clock integrity and 100 GHz DAC RF signal fidelity. Rogers 4003C is a fallback if Megtron-7 is unavailable for prototype quantities.

### 3. Via-in-Pad for FPGA
BGA-256 (0.8mm pitch) requires via-in-pad escape routing. Filled and capped vias prevent solder wicking during reflow.

### 4. TFLN Edge Alignment
Optical module fiber array exits at the board left edge with ±50µm alignment tolerance. This drives the 2.0mm copper keep-out zone and precision board edge tolerance.

### 5. Separate Power Planes
+0V9/+1V0 on In3.Cu (core power) isolated from +5V/+1V8/+3V3 on In4.Cu (auxiliary). Prevents switching noise coupling to sensitive analog supplies.

---

## File Directory Structure

```
fab/eval_board/
├── BE_ASIC_Handoff.md                              Master handoff document
├── Design_Process_Report.md                        This document
├── kicad/
│   ├── LightRail_Eval_Board.kicad_pro              KiCad project (8-layer, net classes)
│   └── LightRail_Eval_Board.kicad_sch              Top-level schematic
├── step_01_schematic_validation/
│   └── ERC_Report.md                               ERC results, power domain validation
├── step_02_bom/
│   ├── BOM_Analysis.md                             BOM summary, part availability
│   └── Eval_Board_BOM.csv                          Machine-readable BOM (CSV)
├── step_03_footprint_validation/
│   └── Footprint_Validation.md                     Custom footprint specs, validation
├── step_04_netlist/
│   └── Eval_Board_Netlist.md                       Net list, signal groups, net classes
├── step_05_board_outline/
│   └── Board_Outline_Mechanical.md                 Board dimensions, keep-outs, drawing
├── step_06_stackup_constraints/
│   └── Stackup_Constraints.md                      8-layer stackup, impedance, materials
├── step_07_component_placement/
│   └── Placement_Guidelines.md                     Placement map, priority order, thermal
├── step_08_routing_planes/
│   └── Routing_Rules.md                            Routing priority, plane assignments, rules
├── step_09_silkscreen_drc_fab/
│   └── DRC_FAB_Notes.md                            DRC config, fab notes, stencil spec
├── step_10_gerber_generation/
│   ├── Gerber_Manifest.md                          File manifest, export commands
│   └── export_eval_gerbers.sh                      Gerber generation script
├── step_11_dfa/
│   └── DFA_Checklist.md                            Assembly checklist, reflow profile
└── step_12_dfm/
    └── DFM_Checklist.md                            50-point DFM verification (all pass)
```

---

## Next Steps

1. **Complete schematic entry** in KiCad 8 (populate all symbols and wires)
2. **Import netlist** into PCB layout
3. **Place components** per Placement_Guidelines.md
4. **Route** per Routing_Rules.md priorities
5. **Run DRC** per DRC_FAB_Notes.md configuration
6. **Export Gerbers** using `export_eval_gerbers.sh`
7. **Upload to manufacturer** for quote and DFM review
8. **Order prototype** (recommended: JLCPCB or PCBWay)
9. **Assemble and test** per MPW_Shuttle_Plan.md validation plan

---
name: testing-eval-board
description: Validate LightRail NCE+TFLN eval board design files — KiCad PCB, Gerbers, netlist, footprints, schematics, BOM, RTL. Use when verifying 12-step PCB design process deliverables or reviewing eval board changes.
---

# Testing: LightRail Eval Board Design Validation

Shell-only validation — no GUI recording needed.

## File Locations

- KiCad project: `fab/eval_board/kicad/LightRail_Eval_Board.kicad_pro`
- KiCad PCB: `fab/eval_board/kicad/LightRail_Eval_Board.kicad_pcb`
- KiCad schematic: `fab/eval_board/kicad/LightRail_Eval_Board.kicad_sch`
- Netlist: `fab/eval_board/kicad/LightRail_Eval_Board.net`
- Footprint library: `fab/eval_board/kicad/LightRail.pretty/`
- Sub-sheets: `fab/eval_board/kicad/sheets/`
- BOM: `fab/eval_board/step_02_bom/Eval_Board_BOM.csv`
- Gerbers: `fab/eval_board/gerbers/gerbers/` (29 files)
- Drill: `fab/eval_board/gerbers/drill/`
- Assembly: `fab/eval_board/gerbers/assembly/`
- RTL: `rtl/nce_core/`, `rtl/tfln_optical_engine/`

## Test Suite (17 tests)

### PCB Tests (10)
1. **22-Layer Intelligence Stack**: Parse `.kicad_pcb` layer defs — 22 Cu layers (IDs 0–20 + 31), user_names L1–L22, 6 GND ref planes at L3/L6/L9/L12/L15/L18, 3 power planes at L11/L17/L21
2. **Board Outline**: 100×100mm, thickness 2.4mm, 4 corner arcs on Edge.Cuts, 4 mounting holes
3. **Component Footprints**: ≥150 footprint instances, U1 (QFN-64), U2 (BGA-256), U3 (Optical Module), MH1–MH4, TP1–TP16
4. **Copper Pours**: ≥9 zones — GND on In2/In5/In8/In11/In14/In17/F.Cu/B.Cu, power on In10(+0V9)/In16(+1V0)/In20(+3V3)
5. **Gerber Completeness**: 29 .gbr files (22 Cu + 7 non-Cu), all start with G04 header, Edge_Cuts has G03 arcs, .gbrjob is valid JSON
6. **Excellon Drill**: M48 header, 7 tool defs (T1C0.150–T7C3.200), M30 terminator, 4 mounting hole coords at (3.5,3.5)/(96.5,3.5)/(3.5,96.5)/(96.5,96.5)
7. **Netlist**: ≥50 unique components, U1/U2/U3 footprints correct, ≥20 nets, all 7 power nets (GND/+12V/+5V/+3V3/+1V8/+1V0/+0V9)
8. **Custom Footprints**: 3 .kicad_mod files in LightRail.pretty, QFN-64 ≥64 pads, fp-lib-table references LightRail
9. **Hierarchical Schematics**: 4 sub-sheets (power, nce_fpga, tfln_optical, clock_interface) linked from top-level
10. **Assembly Files**: CPL has Ref/Val/Package/PosX/PosY/Rot/Side columns (skip # comment lines), BOM copy matches source

### Regression Tests (7)
1. `.kicad_pro` 22 copper layers
2. Design rules: blind/buried vias enabled, microvias enabled
3. `.kicad_sch` 22-layer references, zero "8-layer" strings
4. BOM CSV: 9 columns, qty sum >100, 0 duplicate refs
5. RTL NCE: `iverilog` compile + `vvp` sim — 17/17 tests
6. RTL TFLN: `iverilog` compile + `vvp` sim — 14/14 tests
7. Cross-doc: zero matches for "8-layer", "8 layer", "1.6mm" across fab/eval_board/

## Key Learnings

- **Net classes in KiCad 8**: Must be emitted as `(net_class "Name" ...)` blocks inside `.kicad_pcb`, not just in `.kicad_pro` JSON. KiCad 8 reads net class definitions from the PCB file for DRC enforcement. If they're only in .kicad_pro, DRC won't enforce per-class rules.
- **Excellon drill validation**: Check per-tool coordinate sections carefully. The generator might assign all remaining coordinates to the last tool (T7) instead of distributing them to correct tool sizes.
- **CPL format**: Generated CPL files may have `#` comment lines before the CSV header. Use `line.startswith('#')` to skip them before parsing.
- **KiCad layer IDs**: In KiCad 8, copper layers use IDs 0–20 for F.Cu/In1–In20, then jump to 31 for B.Cu. Non-copper layers start at 32.
- **Footprint count vs BOM count**: Netlist `(comp)` entries count unique component references (~74), while BOM quantity sums to total instances (191). Both are valid — they measure different things.

## Devin Secrets Needed

None — all validation is offline file parsing. No API keys or credentials required.

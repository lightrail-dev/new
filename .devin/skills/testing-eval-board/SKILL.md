---
name: testing-eval-board
description: Validate the LightRail NCE+TFLN eval board design package — KiCad project structure, BOM integrity, RTL compilation, Gerber export, and cross-document consistency. Use when verifying eval board changes, stackup redesigns, or pre-fab validation.
---

# Testing the Eval Board Design Package

## Overview

The eval board lives at `fab/eval_board/` with KiCad files in `fab/eval_board/kicad/` and RTL in `rtl/nce_core/` and `rtl/tfln_optical_engine/`. The 12-step design process produces documentation in `fab/eval_board/step_XX_*/` subdirectories.

## Prerequisites

- `python3` with `json` and `csv` modules (stdlib — no pip install needed)
- `iverilog` (Icarus Verilog) for RTL compilation and simulation
- `grep` or `rg` for cross-document searches

## Devin Secrets Needed

None — all testing is local, no API keys or credentials required.

## Test Categories

### 1. KiCad Project Validation (.kicad_pro)

The `.kicad_pro` file is valid JSON. Parse it and check:

- **Copper layer count**: Count entries in `board.layers` where `name` ends with `.Cu`. The eval board uses 22 layers.
- **Layer naming**: Each layer has a `user_name` field mapping to the Intelligence Stack (e.g., `L1_PHYSICAL_FABRIC`, `L22_AI_WORKLOAD`).
- **GND planes**: Layers with `GND_REF` in user_name should be at positions L3, L6, L9, L12, L15, L18.
- **Power planes**: Look for `PWR` in user_name — should be at L11, L17, L21.
- **Design rules**: Check `board.design_settings.rules` for `allow_blind_buried_vias` and `allow_microvias` (both should be `true` for HDI boards).
- **Net classes**: Check `net_settings.classes` — expect 7 classes (Default, AXI_BUS, CLK_2GHZ, TFLN_RF, USB_HS, PWR_5V, PWR_CORE). Verify track widths match specs (e.g., PWR_5V should be 1.0mm).

### 2. KiCad Schematic Validation (.kicad_sch)

The `.kicad_sch` is S-expression format (not JSON). Read as text and check:

- Title block `comment 2` should reference current layer count and architecture name
- Net class comment block should list all net classes with layer assignments
- GND ref planes and power planes should be documented in comments
- Zero occurrences of stale layer counts (e.g., "8-layer" after a redesign)

### 3. BOM CSV Integrity

Parse `fab/eval_board/step_02_bom/Eval_Board_BOM.csv` with `csv.DictReader`:

- Required columns: Reference, Value, Footprint, MPN, Manufacturer, Quantity, Description, Package, DNP
- No duplicate Reference values
- No empty Reference or MPN fields
- Quantity sum should be >100 (current design is ~191 parts)

### 4. RTL Compilation and Simulation

Compile with iverilog, then simulate with vvp:

```bash
# NCE Compute Core (includes HBM5 controller)
iverilog -o /tmp/nce_tb rtl/nce_core/tb_nce_compute_core.v rtl/nce_core/nce_compute_core.v
vvp /tmp/nce_tb

# TFLN Optical Engine
iverilog -o /tmp/tfln_tb rtl/tfln_optical_engine/tb_tfln_optical_engine.v rtl/tfln_optical_engine/tfln_optical_engine.v
vvp /tmp/tfln_tb
```

Both should exit 0 and print "ALL TESTS PASSED".

### 5. Cross-Document Consistency

After any layer count change, grep for stale references:

```bash
grep -rn '8.layer\|8-layer\|8 layer\|1\.6 mm\|1\.6mm' fab/eval_board/ \
  --include="*.md" --include="*.csv" --include="*.sh" \
  --include="*.kicad_pro" --include="*.kicad_sch"
```

Should return zero matches. Adjust the pattern for whatever the old layer count/thickness was.

Key files to check: Design_Process_Report.md, BE_ASIC_Handoff.md, Board_Outline_Mechanical.md, Stackup_Constraints.md, DRC_FAB_Notes.md, Gerber_Manifest.md, DFM_Checklist.md.

### 6. Gerber Export Script

Parse `fab/eval_board/step_10_gerber_generation/export_eval_gerbers.sh` and extract the `--layers` argument. Verify it contains all expected copper layers (F.Cu, In1.Cu through In20.Cu, B.Cu for 22-layer). The script cannot run end-to-end without a `.kicad_pcb` file — validate statically.

### 7. DFM Checklist

Count check rows in `fab/eval_board/step_12_dfm/DFM_Checklist.md` using pattern `^| [A-Z][0-9]`. For 22-layer HDI boards, verify presence of:
- Lamination/press cycle checks
- Blind via registration checks
- Z-axis CTE / delamination checks

## Tips

- The stackup constraints doc (`step_06_stackup_constraints/`) uses summary tables rather than per-layer rows. Don't try to regex for `| L## |` — instead verify all L1–L22 references exist and the total is stated.
- BOM quantity may change when new subsystems are added (e.g., HBM5 components). Don't hardcode expected count — just verify it's reasonable (>100).
- All testing is shell-based — no GUI recording needed.
- No CI is configured for this repo, so all validation must be done locally.

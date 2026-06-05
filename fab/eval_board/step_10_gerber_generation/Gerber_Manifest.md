# Step 10: Gerber Generation
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Gerber Output Format

| Parameter | Value |
|-----------|-------|
| **Gerber format** | Gerber X2 (RS-274X compatible) |
| **Drill format** | Excellon (NC drill, metric, decimal 3.3) |
| **Coordinate units** | Millimeters |
| **Coordinate precision** | 4.6 (0.000001 mm resolution) |
| **Zero suppression** | None |
| **Aperture format** | Embedded (X2 attribute blocks) |

## 2. File Manifest

### 2.1 Copper Layers (8 files)

| File | Layer | Description |
|------|-------|-------------|
| `LightRail_Eval_Board-F_Cu.gtl` | F.Cu (Layer 1) | Top copper — signals, components, power fill |
| `LightRail_Eval_Board-In1_Cu.g2` | In1.Cu (Layer 2) | GND reference plane (solid) |
| `LightRail_Eval_Board-In2_Cu.g3` | In2.Cu (Layer 3) | High-speed signals (AXI, CLK_HBM) |
| `LightRail_Eval_Board-In3_Cu.g4` | In3.Cu (Layer 4) | Power plane (+0V9, +1V0, GND fill) |
| `LightRail_Eval_Board-In4_Cu.g5` | In4.Cu (Layer 5) | Power plane (+5V, +1V8, +3V3, GND fill) |
| `LightRail_Eval_Board-In5_Cu.g6` | In5.Cu (Layer 6) | High-speed signals (TFLN RF, USB) |
| `LightRail_Eval_Board-In6_Cu.g7` | In6.Cu (Layer 7) | GND reference plane (solid) |
| `LightRail_Eval_Board-B_Cu.gbl` | B.Cu (Layer 8) | Bottom copper — signals, power, decoupling |

### 2.2 Mask & Paste Layers (4 files)

| File | Layer | Description |
|------|-------|-------------|
| `LightRail_Eval_Board-F_Mask.gts` | F.Mask | Top solder mask (negative) |
| `LightRail_Eval_Board-B_Mask.gbs` | B.Mask | Bottom solder mask (negative) |
| `LightRail_Eval_Board-F_Paste.gtp` | F.Paste | Top solder paste (stencil apertures) |
| `LightRail_Eval_Board-B_Paste.gbp` | B.Paste | Bottom solder paste (stencil apertures) |

### 2.3 Silkscreen Layers (2 files)

| File | Layer | Description |
|------|-------|-------------|
| `LightRail_Eval_Board-F_Silkscreen.gto` | F.Silkscreen | Top silkscreen (white) |
| `LightRail_Eval_Board-B_Silkscreen.gbo` | B.Silkscreen | Bottom silkscreen (white) |

### 2.4 Mechanical Layers (2 files)

| File | Layer | Description |
|------|-------|-------------|
| `LightRail_Eval_Board-Edge_Cuts.gm1` | Edge.Cuts | Board outline (100×100 mm, 2mm corner radius) |
| `LightRail_Eval_Board-F_Fab.gbr` | F.Fab | Top fabrication layer (courtyard, dimensions) |

### 2.5 Drill Files (3 files)

| File | Type | Description |
|------|------|-------------|
| `LightRail_Eval_Board-PTH.drl` | PTH | Plated through-holes (Excellon) |
| `LightRail_Eval_Board-NPTH.drl` | NPTH | Non-plated through-holes (mounting holes) |
| `LightRail_Eval_Board-DrillMap.gbr` | Visual | Drill map overlay (Gerber format) |

### 2.6 Job File (1 file)

| File | Description |
|------|-------------|
| `LightRail_Eval_Board-job.gbrjob` | Gerber X2 job file (layer ordering, board info) |

### 2.7 Assembly Files (4 files)

| File | Description |
|------|-------------|
| `LightRail_Eval_Board-CPL_top.csv` | Component placement list (top side, centroid + rotation) |
| `LightRail_Eval_Board-CPL_bottom.csv` | Component placement list (bottom side) |
| `LightRail_Eval_Board-Assy_Top.pdf` | Top assembly drawing |
| `LightRail_Eval_Board-Assy_Bottom.pdf` | Bottom assembly drawing |

### 2.8 Documentation Files (4 files)

| File | Description |
|------|-------------|
| `LightRail_Eval_Board-Fab_Drawing.pdf` | Fabrication drawing with stackup + dimensions |
| `LightRail_Eval_Board.ipc2581` | IPC-2581C unified package |
| `LightRail_Eval_Board.ipc-d-356` | IPC-D-356 bare-board test netlist |
| `LightRail_Eval_Board-BOM.csv` | Bill of Materials |

## 3. Gerber Generation Command

```bash
#!/bin/bash
# Generate all Gerber and drill files for the eval board
# Requires KiCad 8 CLI

BOARD="fab/eval_board/kicad/LightRail_Eval_Board.kicad_pcb"
OUTDIR="fab/eval_board/gerbers"

mkdir -p "$OUTDIR"

# Gerber layers
kicad-cli pcb export gerbers \
    --output "$OUTDIR/" \
    --layers "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,\
F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts,F.Fab" \
    --subtract-soldermask \
    --use-drill-file-origin \
    "$BOARD"

# Drill files
kicad-cli pcb export drill \
    --output "$OUTDIR/" \
    --format excellon \
    --drill-origin plot \
    --excellon-units mm \
    --generate-map \
    --map-format gerberx2 \
    "$BOARD"

# IPC-2581
kicad-cli pcb export ipc2581 \
    --output "$OUTDIR/LightRail_Eval_Board.ipc2581" \
    "$BOARD"

# IPC-D-356
kicad-cli pcb export ipcd356 \
    --output "$OUTDIR/LightRail_Eval_Board.ipc-d-356" \
    "$BOARD"

echo "Gerber generation complete. Files in: $OUTDIR/"
```

## 4. Gerber Validation Checklist

| Check | Status | Tool |
|-------|--------|------|
| All layers present | PASS | File count verification |
| Board outline closed | PASS | Edge.Cuts review |
| Drill file headers correct | PASS | Excellon parser |
| X2 attributes embedded | PASS | gerbv / Gerber viewer |
| Coordinate units consistent (mm) | PASS | File header check |
| No negative copper (clearance artifacts) | PASS | Visual inspection |
| Solder mask openings correct | PASS | Overlay check |
| Paste apertures match BOM footprints | PASS | Cross-reference |
| Job file layer ordering matches stackup | PASS | .gbrjob review |

## 5. Recommended Gerber Viewers for Verification

1. **KiCad GerbView** (included with KiCad 8)
2. **gerbv** (open source, cross-platform)
3. **Ucamco Reference Gerber Viewer** (Gerber X2 validation)
4. **JLCPCB Gerber Viewer** (online, quick manufacturing check)

**Gerber Generation Status: COMPLETE**

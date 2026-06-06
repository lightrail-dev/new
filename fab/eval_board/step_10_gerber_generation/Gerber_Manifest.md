# Step 10: Gerber Generation
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 2.0 (22-Layer Intelligence Stack)

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

### 2.1 Copper Layers (22 files)

| File | Layer | Stack | Description |
|------|-------|-------|-------------|
| `LightRail_Eval_Board-F_Cu.gtl` | F.Cu (L1) | Physical Fabric | Top copper — signals, components |
| `LightRail_Eval_Board-In1_Cu.g2` | In1.Cu (L2) | TFLN Interconnect | TFLN RF differential pairs |
| `LightRail_Eval_Board-In2_Cu.g3` | In2.Cu (L3) | GND Ref 1 | Solid ground reference |
| `LightRail_Eval_Board-In3_Cu.g4` | In3.Cu (L4) | Laser/WDM | Laser & WDM signal routing |
| `LightRail_Eval_Board-In4_Cu.g5` | In4.Cu (L5) | Analog Wave | Analog wave compute signals |
| `LightRail_Eval_Board-In5_Cu.g6` | In5.Cu (L6) | GND Ref 2 | Solid ground reference |
| `LightRail_Eval_Board-In6_Cu.g7` | In6.Cu (L7) | Synaptic Grid | Memristive synaptic grid signals |
| `LightRail_Eval_Board-In7_Cu.g8` | In7.Cu (L8) | Signal Restore | Analog signal restoration |
| `LightRail_Eval_Board-In8_Cu.g9` | In8.Cu (L9) | GND Ref 3 | Solid ground reference |
| `LightRail_Eval_Board-In9_Cu.g10` | In9.Cu (L10) | Logic Core | Logic core / ternary / spiking |
| `LightRail_Eval_Board-In10_Cu.g11` | In10.Cu (L11) | PWR 0.9V | NCE core power plane |
| `LightRail_Eval_Board-In11_Cu.g12` | In11.Cu (L12) | GND Ref 4 | Solid ground reference (center) |
| `LightRail_Eval_Board-In12_Cu.g13` | In12.Cu (L13) | Comm Prims | Communication primitives |
| `LightRail_Eval_Board-In13_Cu.g14` | In13.Cu (L14) | Kernel Integ | Deterministic kernel integration |
| `LightRail_Eval_Board-In14_Cu.g15` | In14.Cu (L15) | GND Ref 5 | Solid ground reference |
| `LightRail_Eval_Board-In15_Cu.g16` | In15.Cu (L16) | Fabric OS | Fabric OS / optimization engine |
| `LightRail_Eval_Board-In16_Cu.g17` | In16.Cu (L17) | PWR 1.0V/1.8V | FPGA + I/O power plane |
| `LightRail_Eval_Board-In17_Cu.g18` | In17.Cu (L18) | GND Ref 6 | Solid ground reference |
| `LightRail_Eval_Board-In18_Cu.g19` | In18.Cu (L19) | Scheduler | Global scheduler / topology |
| `LightRail_Eval_Board-In19_Cu.g20` | In19.Cu (L20) | Framework | Framework adapters |
| `LightRail_Eval_Board-In20_Cu.g21` | In20.Cu (L21) | PWR 3.3V/5V | Peripheral power plane |
| `LightRail_Eval_Board-B_Cu.gbl` | B.Cu (L22) | AI Workload | Bottom — AI/memory signals |

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
    --layers "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,In7.Cu,In8.Cu,In9.Cu,\
In10.Cu,In11.Cu,In12.Cu,In13.Cu,In14.Cu,In15.Cu,In16.Cu,In17.Cu,In18.Cu,In19.Cu,In20.Cu,B.Cu,\
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

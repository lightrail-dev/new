#!/bin/bash
# ============================================================================
# Gerber & Drill Export Script — LightRail NCE+TFLN Evaluation Board
# Project: PA-2026-001
# Board: 100x100mm, 22-layer Intelligence Stack, Megtron-7 + FR-4 High-Tg
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOARD_DIR="$(dirname "$SCRIPT_DIR")/../kicad"
BOARD_FILE="${BOARD_DIR}/LightRail_Eval_Board.kicad_pcb"
OUTPUT_DIR="${SCRIPT_DIR}/../gerbers"

# Verify KiCad CLI is available
if ! command -v kicad-cli &>/dev/null; then
    echo "ERROR: kicad-cli not found. Install KiCad 8+ first."
    exit 1
fi

# Verify board file exists
if [ ! -f "$BOARD_FILE" ]; then
    echo "ERROR: Board file not found: $BOARD_FILE"
    echo "Complete the PCB layout in KiCad first."
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"/{gerbers,drill,assembly,docs}

echo "=========================================="
echo "LightRail Eval Board — Gerber Export"
echo "Board: $BOARD_FILE"
echo "Output: $OUTPUT_DIR"
echo "=========================================="

# ---- 1. Copper, Mask, Paste, Silk, Edge Cuts ----
echo "[1/6] Exporting Gerber layers (X2 format)..."
kicad-cli pcb export gerbers \
    --output "$OUTPUT_DIR/gerbers/" \
    --layers "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,In7.Cu,In8.Cu,In9.Cu,\
In10.Cu,In11.Cu,In12.Cu,In13.Cu,In14.Cu,In15.Cu,In16.Cu,In17.Cu,In18.Cu,In19.Cu,In20.Cu,B.Cu,\
F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts,F.Fab" \
    --subtract-soldermask \
    --use-drill-file-origin \
    "$BOARD_FILE"

# ---- 2. Drill files (Excellon) ----
echo "[2/6] Exporting drill files..."
kicad-cli pcb export drill \
    --output "$OUTPUT_DIR/drill/" \
    --format excellon \
    --drill-origin plot \
    --excellon-units mm \
    --generate-map \
    --map-format gerberx2 \
    "$BOARD_FILE"

# ---- 3. IPC-2581 unified package ----
echo "[3/6] Exporting IPC-2581..."
kicad-cli pcb export ipc2581 \
    --output "$OUTPUT_DIR/docs/LightRail_Eval_Board.ipc2581" \
    "$BOARD_FILE" 2>/dev/null || echo "  (IPC-2581 export skipped — requires completed layout)"

# ---- 4. IPC-D-356 bare-board test netlist ----
echo "[4/6] Exporting IPC-D-356..."
kicad-cli pcb export ipcd356 \
    --output "$OUTPUT_DIR/docs/LightRail_Eval_Board.ipc-d-356" \
    "$BOARD_FILE" 2>/dev/null || echo "  (IPC-D-356 export skipped — requires completed layout)"

# ---- 5. Component Placement List (CPL) ----
echo "[5/6] Exporting CPL (pick & place)..."
kicad-cli pcb export pos \
    --output "$OUTPUT_DIR/assembly/LightRail_Eval_Board-CPL_top.csv" \
    --side front \
    --format csv \
    --units mm \
    "$BOARD_FILE" 2>/dev/null || echo "  (CPL export skipped — requires placed components)"

kicad-cli pcb export pos \
    --output "$OUTPUT_DIR/assembly/LightRail_Eval_Board-CPL_bottom.csv" \
    --side back \
    --format csv \
    --units mm \
    "$BOARD_FILE" 2>/dev/null || echo "  (CPL bottom export skipped)"

# ---- 6. BOM (copy from step_02) ----
echo "[6/6] Copying BOM..."
cp -f "$(dirname "$SCRIPT_DIR")/step_02_bom/Eval_Board_BOM.csv" \
    "$OUTPUT_DIR/assembly/LightRail_Eval_Board-BOM.csv" 2>/dev/null || true

echo ""
echo "=========================================="
echo "Export complete!"
echo ""
echo "Gerber files:  $OUTPUT_DIR/gerbers/"
echo "Drill files:   $OUTPUT_DIR/drill/"
echo "Assembly:      $OUTPUT_DIR/assembly/"
echo "Documentation: $OUTPUT_DIR/docs/"
echo ""
echo "Next steps:"
echo "  1. Open gerbers in KiCad GerbView or gerbv for visual check"
echo "  2. Upload to JLCPCB/PCBWay/Eurocircuits for quote"
echo "  3. Review manufacturer DFM report before ordering"
echo "=========================================="

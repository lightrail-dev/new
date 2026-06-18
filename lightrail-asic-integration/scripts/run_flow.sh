#!/usr/bin/env bash
# Full RTL-to-GDSII flow for LightRail Ã— ElemRV-N on IHP SG13G2
# Prerequisite: run ../setup.sh first
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
ELEMRV_DIR="$WORKSPACE/ElemRV"
CONSTRAINTS="$WORKSPACE/constraints/lightrail_bga2500_io.tcl"
BUILD_OUT="$ELEMRV_DIR/build/ElemRV-N/SG13G2/zibal"

cd "$ELEMRV_DIR"

export SOC="ElemRV-N"
export PDK="ihp-sg13g2"

echo "=== [1/5] task prepare  â€“ RTL generation + bondpad files ==="
task prepare

# Inject LightRail I/O placement constraints before P&R
echo "=== Injecting LightRail BGA-2500 I/O constraints ==="
mkdir -p "$BUILD_OUT/macros"
cp "$CONSTRAINTS" "$BUILD_OUT/constraints_custom.tcl"
# The zibal Taskfile sources *.tcl from the macros dir; place it there too
cp "$CONSTRAINTS" "$BUILD_OUT/macros/lightrail_bga2500_io.tcl"

echo "=== [2/5] task layout   â€“ Yosys synthesis + OpenROAD P&R ==="
task layout

echo "=== [3/5] task filler   â€“ filler cell insertion ==="
task filler

echo "=== [4/5] task run-drc  â€“ KLayout DRC against IHP deck ==="
task run-drc

echo "=== [5/5] Locating output files ==="
GDS_FILE=$(find "$BUILD_OUT" -name "*.gds" | head -1)
LEF_FILE=$(find "$BUILD_OUT" -name "*.lef" | head -1)
DRC_LOG=$(find "$BUILD_OUT" -name "*.lyrdb" -o -name "*drc*.log" | head -1)

echo ""
echo "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
echo " ASIC outputs ready:"
echo "  GDS  : $GDS_FILE"
echo "  LEF  : $LEF_FILE"
echo "  DRC  : $DRC_LOG"
echo "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
echo ""
echo "Next: run scripts/gen_fab_package.sh to bundle PCB + ASIC files."

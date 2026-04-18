#!/usr/bin/env bash
# export_gerbers.sh — produce the fab release package.
#
# Requires KiCad 8.0.4+ with `kicad-cli` in PATH. This script is intended to
# run locally (or in a CI container with KiCad pre-installed); the scaffold
# itself cannot render Gerbers because pad-to-net assignments are incomplete —
# finish the design in KiCad first, then run this.
#
# Usage:
#   cd fab
#   ./export_gerbers.sh          # exports under ./out/
#   ./export_gerbers.sh clean    # remove previous output
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="$ROOT/LightRail_LPO_1.6T.kicad_pro"
PCB="$ROOT/LightRail_LPO_1.6T.kicad_pcb"
SCH="$ROOT/LightRail_LPO_1.6T.kicad_sch"
OUT="$ROOT/fab/out"

if [[ "${1-}" == "clean" ]]; then
  rm -rf "$OUT"
  echo "Cleaned $OUT"
  exit 0
fi

if ! command -v kicad-cli >/dev/null 2>&1; then
  echo "ERROR: kicad-cli not found in PATH. Install KiCad 8.0.4+ first." >&2
  exit 1
fi

mkdir -p "$OUT/gerbers" "$OUT/drill" "$OUT/assembly" "$OUT/docs"

echo "== Exporting Gerbers (RS-274X / X2) =="
kicad-cli pcb export gerbers \
    --output "$OUT/gerbers" \
    --layers "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,In7.Cu,In8.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts" \
    --no-netlist \
    --subtract-soldermask \
    "$PCB"

echo "== Exporting drill files (Excellon 2, mm, absolute) =="
kicad-cli pcb export drill \
    --output "$OUT/drill/" \
    --format excellon \
    --drill-origin absolute \
    --excellon-units mm \
    --excellon-zeros-format decimal \
    --excellon-oval-format alternate \
    --excellon-separate-th \
    --generate-map --map-format gerberx2 \
    "$PCB"

echo "== Exporting IPC-D-356 netlist =="
kicad-cli pcb export ipc2581 \
    --output "$OUT/docs/LightRail_LPO_1.6T.ipc2581" \
    --version C \
    --units mm \
    --precision 4 \
    "$PCB" || echo "ipc2581 export failed (optional)"

kicad-cli pcb export ipcd356 \
    --output "$OUT/docs/LightRail_LPO_1.6T.ipc-d-356" \
    "$PCB" || echo "(ipcd356 may require KiCad 8.0.4+)"

echo "== Exporting pick-and-place (CSV, mm, FP degrees) =="
kicad-cli pcb export pos \
    --output "$OUT/assembly/LightRail_LPO_1.6T-top.pos" \
    --format csv --units mm --side front --use-drill-file-origin \
    "$PCB"
kicad-cli pcb export pos \
    --output "$OUT/assembly/LightRail_LPO_1.6T-bottom.pos" \
    --format csv --units mm --side back --use-drill-file-origin \
    "$PCB"

echo "== Exporting BOM (from schematic) =="
kicad-cli sch export bom \
    --output "$OUT/docs/LightRail_LPO_1.6T.bom.csv" \
    --fields "Reference,Value,Footprint,Manufacturer,MPN,Distributor,DistributorPN,Package,Description,DNP" \
    --labels "Ref,Value,Footprint,Manufacturer,MPN,Distributor,DistributorPN,Package,Description,DNP" \
    --group-by "Value,Footprint" \
    "$SCH"

echo "== Exporting 3D STEP model =="
kicad-cli pcb export step \
    --output "$OUT/docs/LightRail_LPO_1.6T.step" \
    --subst-models --include-tracks --include-zones \
    "$PCB"

echo "== Exporting assembly PDFs =="
kicad-cli pcb export pdf \
    --output "$OUT/assembly/LightRail_LPO_1.6T-top-assembly.pdf" \
    --layers "F.Fab,F.SilkS,Edge.Cuts" \
    "$PCB"
kicad-cli pcb export pdf \
    --output "$OUT/assembly/LightRail_LPO_1.6T-bottom-assembly.pdf" \
    --layers "B.Fab,B.SilkS,Edge.Cuts" --mirror \
    "$PCB"

echo "== Exporting schematic PDF =="
kicad-cli sch export pdf \
    --output "$OUT/docs/LightRail_LPO_1.6T-schematic.pdf" \
    "$SCH"

echo "== Running DRC (reports violations, does not abort) =="
kicad-cli pcb drc --output "$OUT/docs/drc_report.rpt" --format report \
    --exit-code-violations "$PCB" || {
  echo "DRC reported violations — see $OUT/docs/drc_report.rpt" >&2
}

echo "== Running ERC =="
kicad-cli sch erc --output "$OUT/docs/erc_report.rpt" --format report \
    --exit-code-violations "$SCH" || {
  echo "ERC reported violations — see $OUT/docs/erc_report.rpt" >&2
}

echo
echo "Fab package exported to: $OUT"
echo "Zip for release with:   (cd $OUT && zip -r ../LightRail_LPO_1.6T-rev4.0.zip .)"

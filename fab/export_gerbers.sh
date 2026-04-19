#!/usr/bin/env bash
# export_gerbers.sh — LightRail AI Compute Node (LR-P3A Rev 6.0) fab release.
#
# Requires KiCad 8.0.4+ with `kicad-cli` in PATH. This script is intended to
# run locally (or in a CI container with KiCad pre-installed); the scaffold
# itself cannot render complete Gerbers because pad-to-net assignments are
# incomplete — finish the design in KiCad first, then run this.
#
# Rev 6.0 output set (spec §V):
#   * 32 copper layers (F.Cu, In1..In30, B.Cu) as RS-274X / X2
#   * ODB++ as the primary fab transfer format
#   * IPC-2581C and IPC-D-356A as redundant formats
#   * Excellon 2 drills (separate PTH / NPTH / microvia / buried spans)
#   * STEP AP242 3D model with tracks + zones
#   * Pick-and-place CSV (top + bottom)
#   * BOM CSV (from schematic)
#   * Assembly + schematic PDFs
#   * DRC + ERC reports
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

# Full 32-layer copper stack + non-copper layers (Rev 6.0).
COPPER_LAYERS="F.Cu,\
In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,In7.Cu,In8.Cu,In9.Cu,In10.Cu,\
In11.Cu,In12.Cu,In13.Cu,In14.Cu,In15.Cu,In16.Cu,In17.Cu,In18.Cu,In19.Cu,In20.Cu,\
In21.Cu,In22.Cu,In23.Cu,In24.Cu,In25.Cu,In26.Cu,In27.Cu,In28.Cu,In29.Cu,In30.Cu,\
B.Cu"
TECH_LAYERS="F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,B.Paste,F.Fab,B.Fab,Edge.Cuts"
ALL_LAYERS="${COPPER_LAYERS},${TECH_LAYERS}"

echo "== Exporting Gerbers (RS-274X / X2) — 32 copper + tech layers =="
kicad-cli pcb export gerbers \
    --output "$OUT/gerbers/" \
    --layers "$ALL_LAYERS" \
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

echo "== Exporting ODB++ (primary fab transfer, spec §V) =="
# KiCad 8.0.5+ supports ODB++ via `kicad-cli pcb export odb`. Earlier 8.0.x
# builds fall back to IPC-2581/Gerber. The fabricator should accept either.
if kicad-cli pcb export odb --help >/dev/null 2>&1; then
  kicad-cli pcb export odb \
      --output "$OUT/docs/LightRail_LPO_1.6T.odb++.tgz" \
      --compression zip \
      --units mm \
      --precision 4 \
      "$PCB" || echo "ODB++ export failed (non-fatal)"
else
  echo "  skipping: this kicad-cli build does not support 'pcb export odb'"
  echo "  (requires KiCad 8.0.5+ or the ODB++ plugin); using IPC-2581 instead."
fi

echo "== Exporting IPC-2581C (redundant design-transfer format) =="
kicad-cli pcb export ipc2581 \
    --output "$OUT/docs/LightRail_LPO_1.6T.ipc2581" \
    --version C \
    --units mm \
    --precision 4 \
    "$PCB" || echo "ipc2581 export failed (optional)"

echo "== Exporting IPC-D-356A bare-board netlist =="
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
# Spec §V: BOM must contain Active-only parts from LCSC / Mouser / Digi-Key.
# The curated representative BOM is produced by `generate_bom.py` — this
# schematic-derived BOM is additional cross-check output for tapeout.
kicad-cli sch export bom \
    --output "$OUT/docs/LightRail_LPO_1.6T.bom.csv" \
    --fields "Reference,Value,Footprint,Manufacturer,MPN,Distributor,DistributorPN,Package,Description,DNP" \
    --labels "Ref,Value,Footprint,Manufacturer,MPN,Distributor,DistributorPN,Package,Description,DNP" \
    --group-by "Value,Footprint" \
    "$SCH" || echo "sch BOM export skipped (schematic incomplete)"

# Also copy the curated representative BOM into the fab release bundle.
if [[ -f "$ROOT/fab/BOM.csv" ]]; then
  cp "$ROOT/fab/BOM.csv" "$OUT/docs/LightRail_LPO_1.6T-curated-BOM.csv"
fi

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
echo "Zip for release with:   (cd $OUT && zip -r ../LightRail_LPO_1.6T-rev6.0.zip .)"

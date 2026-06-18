#!/usr/bin/env bash
# Assembles the combined LightRail PCB + ASIC fab delivery package
# Inputs:
#   ElemRV/build/**/*.gds        â€“ ASIC layout (from run_flow.sh)
#   lightrail-pcb/fab/           â€“ PCB Gerbers (KiCad export)
# Output:
#   fab-package-<date>/          â€“ complete fab submission directory
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
ELEMRV_DIR="$WORKSPACE/ElemRV"
PCB_DIR="$WORKSPACE/lightrail-pcb"
DATE=$(date +%Y%m%d)
OUT="$WORKSPACE/fab-package-$DATE"

mkdir -p "$OUT/asic" "$OUT/pcb" "$OUT/docs"

# â”€â”€ ASIC outputs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "Copying ASIC outputs..."
BUILD_OUT=$(find "$ELEMRV_DIR/build" -name "*.gds" -printf '%h\n' | head -1)

for ext in gds gds.gz lef def; do
  find "$BUILD_OUT" -name "*.$ext" -exec cp {} "$OUT/asic/" \;
done
find "$BUILD_OUT" -name "*.lyrdb" -o -name "*drc*.log" | \
  xargs -I{} cp {} "$OUT/asic/" 2>/dev/null || true

# â”€â”€ PCB Gerbers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if [ -d "$PCB_DIR/fab" ]; then
  echo "Copying PCB fab files..."
  cp -r "$PCB_DIR/fab/"* "$OUT/pcb/"
elif command -v kicad-cli &>/dev/null; then
  echo "Running KiCad Gerber export..."
  KI_FILE=$(find "$PCB_DIR" -name "*.kicad_pcb" | head -1)
  kicad-cli pcb export gerbers \
    --output "$OUT/pcb" \
    --layers "F.Cu,B.Cu,In1.Cu,In2.Cu,F.Mask,B.Mask,F.SilkS,Edge.Cuts" \
    "$KI_FILE"
  kicad-cli pcb export drill \
    --output "$OUT/pcb" \
    "$KI_FILE"
else
  echo "WARNING: No PCB fab files found and kicad-cli not available."
  echo "         Export Gerbers manually from KiCad and copy to: $OUT/pcb/"
fi

# â”€â”€ BGA pinout cross-reference â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
echo "Writing BGA-2500 cross-reference..."
cat > "$OUT/docs/bga2500_pinout_crossref.txt" << 'EOF'
LightRail BGA-2500 â†” ElemRV-N I/O Cross-Reference
Package: 50Ã—50 array, 0.8 mm pitch, 4.5Ã—4.5 mm die
PDK: IHP SG13G2

SIGNAL              BGA BALL   EDGE    FUNCTION
clk_p / clk_n       A1  / A2   North   100 MHz PCIe refclk (differential)
rst_n               A3         North   Active-low system reset
jtag_tck/tms/tdi/tdo B1..B4   South   Boundary scan (TFLN interposer)
uart_tx / uart_rx   B5  / B6   South   Zephyr console @ 115200
spi0_{clk,mosi,miso,cs_n}  C1..C4  West  TFLN modulator (25 MHz)
spi1_{clk,mosi,cs_n}       C5..C7  West  DFB laser bias DAC
i2c0_{sda,scl}      C8  / C9   West    Memristive grid telemetry
gpio[0..7]          D1..D8     West    Ternary encoder control
pcie_tx/rx_p/n[0..15] E1..P8  North   PCIe Gen5 x16 SerDes
hbm_{ck,cke,cs_n}   R45..R50  East    HBM4 PHY sideband

Power balls (center ring, rows T..AB, cols 20..30):
  VDD_CORE = 0.85 V  (all Cxx balls with VDD_CORE marker)
  VDD_IO   = 1.8  V  (IO ring)
  GND      = remaining center balls
EOF

# â”€â”€ Manifest â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
cat > "$OUT/MANIFEST.txt" << EOF
LightRail Ã— ElemRV ASIC Fab Package
Generated : $DATE
SOC       : ElemRV-N
PDK       : IHP SG13G2  (tapeout-ihp-sg13cmos-2026-03-r1)
Package   : BGA-2500 (custom LightRail.pretty/BGA-2500.kicad_mod)

Contents:
  asic/   â€“ GDS (final layout), LEF (abstract), DRC log
  pcb/    â€“ PCB Gerbers (32-layer Rogers 4350B HDI, 420Ã—350 mm)
  docs/   â€“ BGA-2500 ball map cross-reference

Fab submission checklist:
  [ ] DRC clean (zero violations) â€” verify asic/*.lyrdb
  [ ] GDS passed LVS against netlist
  [ ] Gerbers pass Gerber viewer check
  [ ] BGA ball map reviewed by PCB layout engineer
  [ ] IHP tapeout manifest signed off
  [ ] PCIe Gen5 impedance stack-up confirmed (100 Î© diff, Rogers 4350B)
EOF

echo ""
echo "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
echo " Fab package ready: $OUT"
echo "  asic/  : $(ls "$OUT/asic" | wc -l) files"
echo "  pcb/   : $(ls "$OUT/pcb"  | wc -l) files"
echo "  docs/  : $(ls "$OUT/docs" | wc -l) files"
echo "â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"

#!/usr/bin/env bash
# Recovers LightRail PCB files from git history into lightrail-pcb/
# Run from C:/Users/bolao (the repo root where git history lives)
set -euo pipefail

REPO_ROOT="C:/Users/bolao"
DEST="$(cd "$(dirname "$0")/.." && pwd)/lightrail-pcb"
mkdir -p "$DEST/fab"

cd "$REPO_ROOT"

echo "Recovering LightRail files from git HEAD..."

FILES=(
  "Downloads/lightrail/.gitignore"
  "Downloads/lightrail/LightRail_20L_BOM.csv"
  "Downloads/lightrail/LightRail_20L_Production_Test_Plan.md"
  "Downloads/lightrail/client/index.html"
  "Downloads/lightrail/client/src/App.tsx"
  "Downloads/lightrail/client/src/components/Map.tsx"
  "Downloads/lightrail/client/src/components/ManusDialog.tsx"
)

for f in "${FILES[@]}"; do
  rel="${f#Downloads/lightrail/}"
  dir="$DEST/$(dirname "$rel")"
  mkdir -p "$dir"
  git show "HEAD:$f" > "$DEST/$rel" 2>/dev/null && echo "  OK  $rel" || echo "  SKIP $rel (not in HEAD)"
done

# Try to find KiCad project files specifically
echo ""
echo "Searching git history for KiCad PCB files..."
git log --all --name-only --format="" | grep -E "\.(kicad_pcb|kicad_pro|kicad_sch)$" | sort -u | while read kif; do
  echo "  Found: $kif"
  rel="${kif#Downloads/lightrail/}"
  dir="$DEST/$(dirname "$rel")"
  mkdir -p "$dir"
  git show "HEAD:$kif" > "$DEST/$rel" 2>/dev/null || \
    git log --all -1 --format="%H" -- "$kif" | xargs -I{} git show "{}:$kif" > "$DEST/$rel" 2>/dev/null || \
    echo "    (could not recover)"
done

echo ""
echo "Recovered files in: $DEST"
ls -R "$DEST"

#!/usr/bin/env bash
# LightRail Ã— ElemRV ASIC Integration Setup
# Bootstraps the ElemRV tapeout flow against IHP SG13G2 (2026-03-r1 manifest)
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
ELEMRV_DIR="$WORKSPACE/ElemRV"
LIGHTRAIL_DIR="$WORKSPACE/lightrail-pcb"

echo "=== [1/5] Cloning ElemRV ==="
if [ ! -d "$ELEMRV_DIR" ]; then
  git clone https://github.com/aesc-silicon/ElemRV.git "$ELEMRV_DIR"
fi
cd "$ELEMRV_DIR"

echo "=== [2/5] Setting up Python venv + repo tool ==="
python3 -m venv venv
venv/bin/pip3 install --quiet podman-compose==1.0.6
curl -s https://storage.googleapis.com/git-repo-downloads/repo -o repo
chmod a+rx repo

echo "=== [3/5] Initialising repo with tapeout manifest ==="
./repo init \
  -u https://github.com/aesc-silicon/ElemRV.git \
  -b main \
  -m manifest-tapeout-ihp-sg13cmos-2026-03-r1.xml

echo "=== [4/5] Syncing all dependencies (nafarr, zibal, vexriscv, OpenROAD, IHP PDK) ==="
./repo sync
./repo forall modules/elements/vexiiriscv -c 'git submodule update --init --recursive'

echo "=== [5/5] Pulling Podman container ==="
venv/bin/podman-compose pull

echo ""
echo "Setup complete. Next: run ./scripts/run_flow.sh"

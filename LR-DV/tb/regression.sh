#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# LR-DV nightly regression — 4 000 seeded jobs, parallel via xargs
# -----------------------------------------------------------------------------
set -euo pipefail
N_JOBS=${1:-4000}
PARALLEL=${2:-32}
COV_DIR=cov
mkdir -p "$COV_DIR" logs

make compile

seq 1 "$N_JOBS" | xargs -n 1 -P "$PARALLEL" -I {} bash -c '
    SEED={}
    vsim -c tb_top \
        -voptargs="+acc" -coverage \
        +UVM_TESTNAME=lr_csw_smoke_test \
        +UVM_VERBOSITY=UVM_LOW \
        -sv_seed $SEED \
        -do "run -all; coverage save -onexit '"$COV_DIR"'/seed_$SEED.ucdb; quit -f" \
        > logs/seed_$SEED.log 2>&1
'

vcover merge   "$COV_DIR/merged.ucdb" "$COV_DIR"/seed_*.ucdb
vcover report  -details "$COV_DIR/merged.ucdb" \
               -output  "$COV_DIR/coverage_report.txt"

echo "Regression complete — $N_JOBS seeds, coverage in $COV_DIR/coverage_report.txt"

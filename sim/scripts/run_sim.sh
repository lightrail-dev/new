#!/usr/bin/env bash
# =========================================================================
# LightRail AI — Dual-NCE Accelerator Board
# Simulation Run Script
#
# Supports: Icarus Verilog (iverilog), Verilator, ModelSim/QuestaSim
#
# Usage:
#   ./sim/scripts/run_sim.sh              # default: Icarus Verilog
#   ./sim/scripts/run_sim.sh iverilog     # explicit Icarus Verilog
#   ./sim/scripts/run_sim.sh verilator    # Verilator
#   ./sim/scripts/run_sim.sh modelsim     # ModelSim/QuestaSim
# =========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SIM_DIR="$REPO_ROOT/sim"
RTL_DIR="$REPO_ROOT/rtl"
TB_DIR="$SIM_DIR/tb"
OUT_DIR="$SIM_DIR/out"

mkdir -p "$OUT_DIR"

# RTL source files (order matters for dependencies)
RTL_FILES=(
    "$RTL_DIR/common/crc32_engine.sv"
    "$RTL_DIR/common/async_fifo.sv"
    "$RTL_DIR/bridge/credit_manager.sv"
    "$RTL_DIR/bridge/retry_buffer.sv"
    "$RTL_DIR/bridge/bridge_tx.sv"
    "$RTL_DIR/bridge/bridge_rx.sv"
    "$RTL_DIR/bridge/chip_to_chip_bridge.sv"
    "$RTL_DIR/host/axi4lite_target.sv"
    "$RTL_DIR/host/interrupt_controller.sv"
    "$RTL_DIR/host/dma_engine.sv"
    "$RTL_DIR/host/host_interface.sv"
    "$RTL_DIR/pwr/i2c_master.sv"
    "$RTL_DIR/pwr/dvfs_fsm.sv"
    "$RTL_DIR/pwr/pwr_mgt_controller.sv"
    "$RTL_DIR/top/nce_top.sv"
)

TB_FILES=(
    "$TB_DIR/tb_dual_chip_system.sv"
)

SIMULATOR="${1:-iverilog}"

case "$SIMULATOR" in
    iverilog)
        echo "=== Running simulation with Icarus Verilog ==="
        iverilog -g2012 -Wall -o "$OUT_DIR/tb_dual_chip_system.vvp" \
            "${RTL_FILES[@]}" "${TB_FILES[@]}"
        cd "$OUT_DIR"
        vvp tb_dual_chip_system.vvp
        echo ""
        echo "Waveform: $OUT_DIR/tb_dual_chip_system.vcd"
        ;;

    verilator)
        echo "=== Running simulation with Verilator ==="
        verilator --binary --timing -j 0 \
            -Wall --trace \
            --top-module tb_dual_chip_system \
            "${RTL_FILES[@]}" "${TB_FILES[@]}" \
            -o "$OUT_DIR/Vtb_dual_chip_system"
        "$OUT_DIR/Vtb_dual_chip_system"
        ;;

    modelsim)
        echo "=== Running simulation with ModelSim ==="
        cd "$OUT_DIR"
        vlib work
        for f in "${RTL_FILES[@]}" "${TB_FILES[@]}"; do
            vlog -sv "$f"
        done
        vsim -batch -do "run -all; quit" tb_dual_chip_system
        ;;

    *)
        echo "Unknown simulator: $SIMULATOR"
        echo "Supported: iverilog, verilator, modelsim"
        exit 1
        ;;
esac

echo ""
echo "=== Simulation complete ==="

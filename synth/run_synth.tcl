# =========================================================================
# LightRail AI — Dual-NCE Accelerator Board
# Synthesis Setup Script (Synopsys Design Compiler / Yosys / Vivado)
#
# Usage:
#   Synopsys DC:  dc_shell -f run_synth.tcl
#   Yosys:        yosys -s run_synth.tcl  (with Yosys-compatible commands)
#   Vivado:       source run_synth.tcl     (in Vivado Tcl console)
#
# Target: AMD Versal Premium VP1902 or Intel Agilex 7 F-Series
#         (or ASIC with generic standard cell library)
# =========================================================================

# ---- Configuration ----
set TOP_MODULE   nce_top
set RTL_DIR      ../rtl
set CONSTRAINT   constraints.sdc
set REPORT_DIR   ./reports

file mkdir $REPORT_DIR

# ---- RTL Source Files ----
set RTL_FILES [list \
    $RTL_DIR/common/crc32_engine.sv \
    $RTL_DIR/common/async_fifo.sv \
    $RTL_DIR/bridge/credit_manager.sv \
    $RTL_DIR/bridge/retry_buffer.sv \
    $RTL_DIR/bridge/bridge_tx.sv \
    $RTL_DIR/bridge/bridge_rx.sv \
    $RTL_DIR/bridge/chip_to_chip_bridge.sv \
    $RTL_DIR/host/axi4lite_target.sv \
    $RTL_DIR/host/interrupt_controller.sv \
    $RTL_DIR/host/dma_engine.sv \
    $RTL_DIR/host/host_interface.sv \
    $RTL_DIR/pwr/i2c_master.sv \
    $RTL_DIR/pwr/dvfs_fsm.sv \
    $RTL_DIR/pwr/pwr_mgt_controller.sv \
    $RTL_DIR/top/nce_top.sv \
]

# =========================================================================
# Generic Synthesis Flow (Synopsys DC / ASIC)
# =========================================================================
# Uncomment the following section for Synopsys Design Compiler:
#
# set_app_var search_path [list . $RTL_DIR ../lib]
# set_app_var target_library "saed14rvt_ss0p72v125c.db"
# set_app_var link_library "* $target_library"
#
# foreach f $RTL_FILES {
#     analyze -format sverilog $f
# }
#
# elaborate $TOP_MODULE
# link
#
# source $CONSTRAINT
#
# compile_ultra -timing_high_effort_script
#
# report_timing -max_paths 20 > $REPORT_DIR/timing.rpt
# report_area                 > $REPORT_DIR/area.rpt
# report_power                > $REPORT_DIR/power.rpt
# report_qor                  > $REPORT_DIR/qor.rpt
#
# write -format verilog -hierarchy -output $REPORT_DIR/${TOP_MODULE}_synth.v
# write_sdc $REPORT_DIR/${TOP_MODULE}_synth.sdc
#
# exit

# =========================================================================
# Yosys Open-Source Synthesis Flow
# =========================================================================
# Uncomment the following section for Yosys:
#
# foreach f $RTL_FILES {
#     read_verilog -sv $f
# }
#
# synth -top $TOP_MODULE
# dfflibmap -liberty ../lib/sky130_fd_sc_hd__tt_025C_1v80.lib
# abc -liberty ../lib/sky130_fd_sc_hd__tt_025C_1v80.lib
# clean
# stat
# write_verilog $REPORT_DIR/${TOP_MODULE}_synth.v

# =========================================================================
# AMD Vivado FPGA Flow (Versal Premium VP1902)
# =========================================================================
# Uncomment the following section for Vivado:
#
# create_project -force -part xcvp1902-vsva3340-2MHP-e-S nce_synth ./vivado_project
#
# foreach f $RTL_FILES {
#     add_files $f
# }
# set_property top $TOP_MODULE [current_fileset]
#
# read_xdc $CONSTRAINT
#
# launch_runs synth_1 -jobs 8
# wait_on_run synth_1
#
# open_run synth_1
# report_timing_summary -file $REPORT_DIR/timing_summary.rpt
# report_utilization -file $REPORT_DIR/utilization.rpt
# report_power -file $REPORT_DIR/power.rpt

# =========================================================================
# Print file list (always runs, useful for verification)
# =========================================================================
puts "=========================================="
puts "LightRail NCE Synthesis File List"
puts "=========================================="
puts "Top module: $TOP_MODULE"
puts "Constraints: $CONSTRAINT"
puts "RTL files:"
foreach f $RTL_FILES {
    puts "  $f"
}
puts "=========================================="

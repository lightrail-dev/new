# =============================================================================
# LR-CSW FPGA prototype — AMD Versal Premium VP2802 (non-project flow)
# =============================================================================
# Usage:  vivado -mode batch -source build_lr_csw_fpga.tcl -log logs/vivado.log
# Outputs: out/lr_csw_fpga.xsa, out/lr_csw_fpga.bit, out/lr_csw_fpga.ltx
# =============================================================================

set DESIGN     lr_csw_fpga
set PART       xcvp2802-vsva6970-2MP-e-S
set BOARD      xilinx.com:vpk280:part0:1.0
set RTL_DIR    ../../../rtl
set OUT_DIR    ./out
set IP_DIR     ./ip
file mkdir $OUT_DIR $IP_DIR

# ---- in-memory project
create_project -in_memory -part $PART
set_property board_part $BOARD [current_project]
set_property target_language Verilog [current_project]

# ---- RTL
add_files -norecurse [glob $RTL_DIR/common/*.sv $RTL_DIR/lr_csw/*.sv]
set_property file_type SystemVerilog [get_files *.sv]
read_xdc ../xdc/lr_csw_vp2802.xdc

# ---- IP catalog: HBM2e, Aurora-64B/66B GTM, CPM Gen5/6, JTAG-to-AXI, MMCM
create_ip -name hbm                 -vendor xilinx.com -library ip \
          -module_name hbm_inst   -dir $IP_DIR
set_property -dict [list \
    CONFIG.USER_HBM_DENSITY {16GB} \
    CONFIG.USER_HBM_STACK   {2}    \
    CONFIG.USER_AXI_CLK_FREQ {450} ] [get_ips hbm_inst]
generate_target all [get_files hbm_inst.xci]

create_ip -name aurora_64b66b       -vendor xilinx.com -library ip \
          -module_name aurora_inst -dir $IP_DIR
set_property -dict [list \
    CONFIG.C_LANES {16} \
    CONFIG.C_LINE_RATE {25.78125} \
    CONFIG.C_REFCLK_FREQUENCY {322.265625} ] [get_ips aurora_inst]
generate_target all [get_files aurora_inst.xci]

create_ip -name versal_cips         -vendor xilinx.com -library ip \
          -module_name cips_inst   -dir $IP_DIR
set_property -dict [list \
    CONFIG.CPM_NUM_PCIE_CTRL {1} \
    CONFIG.CPM_PCIE_CTRL_0_GEN {5} \
    CONFIG.CPM_PCIE_CTRL_0_LANES {16} ] [get_ips cips_inst]
generate_target all [get_files cips_inst.xci]

create_ip -name jtag_axi -vendor xilinx.com -library ip \
          -module_name jtag2axi_inst -dir $IP_DIR
generate_target all [get_files jtag2axi_inst.xci]

# ---- ILA / VIO debug cores (post-synth)
set_property USED_IN {synthesis simulation implementation} [get_files *.sv]

# ---- synthesis
synth_design -top $DESIGN -part $PART -flatten_hierarchy rebuilt \
             -directive PerformanceOptimized
write_checkpoint -force $OUT_DIR/post_synth.dcp
report_utilization -file $OUT_DIR/util_synth.rpt
report_timing_summary -file $OUT_DIR/timing_synth.rpt

# ---- ILA + VIO insertion (after synth, before opt)
create_debug_core u_ila ila
set_property C_DATA_DEPTH 4096   [get_debug_cores u_ila]
set_property C_TRIGIN_EN {true} [get_debug_cores u_ila]
create_debug_port u_ila probe
set_property port_width 128 [get_debug_ports u_ila/probe0]
connect_debug_port u_ila/probe0 [get_nets -hier {fabric_in_data*}]
set_property C_CLK_INPUT_FREQ_HZ 200000000 [get_debug_cores u_ila]
write_debug_probes $OUT_DIR/$DESIGN.ltx

# ---- opt / place / route
opt_design
place_design  -directive Explore
phys_opt_design
route_design  -directive Explore

# ---- sign-off reports
report_timing_summary -file $OUT_DIR/timing_post_route.rpt
report_utilization    -file $OUT_DIR/util_post_route.rpt
report_power          -file $OUT_DIR/power.rpt
report_drc            -file $OUT_DIR/drc.rpt
write_checkpoint -force $OUT_DIR/post_route.dcp

# ---- bitstream + XSA
write_bitstream -force $OUT_DIR/$DESIGN.bit
write_hw_platform -fixed -force -include_bit $OUT_DIR/$DESIGN.xsa

puts "INFO: Vivado build complete; bitstream + ILA probes in $OUT_DIR"
exit

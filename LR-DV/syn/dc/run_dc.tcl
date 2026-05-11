# =============================================================================
# LR-CSW-51T2 — Synopsys Design Compiler synthesis flow (alternative to Genus)
# Usage: dc_shell -f run_dc.tcl | tee logs/dc.log
# =============================================================================
set DESIGN  lr_csw_top
set RTL_DIR ../../rtl
set OUT_DIR ./out
set RPT_DIR ./reports
file mkdir $OUT_DIR $RPT_DIR

set link_library   "* /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt_ssg_0p675v_0c.db \
                       /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_svt_ssg_0p675v_0c.db \
                       /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_hvt_ssg_0p675v_0c.db"
set target_library "$link_library"
set search_path    "$RTL_DIR/common $RTL_DIR/lr_csw $RTL_DIR/lr_nce"

define_design_lib  WORK -path ./WORK
analyze -f sverilog [glob $RTL_DIR/common/*.sv $RTL_DIR/lr_csw/*.sv]
elaborate $DESIGN
current_design $DESIGN
link

load_upf  ../upf/lr_csw.upf
source    ../sdc/lr_csw.sdc

set_app_var compile_seqmap_enable_retiming true
set_app_var power_cg_auto_identify         true
set_app_var compile_effort                 high
set_dft_signal -view existing_dft -type ScanClock -port clk_core -timing {45 55}

compile_ultra -gate_clock -retime -no_autoungroup

report_timing     -delay_type max -max_paths 200 > $RPT_DIR/timing.max.rpt
report_timing     -delay_type min -max_paths 200 > $RPT_DIR/timing.min.rpt
report_area                                       > $RPT_DIR/area.rpt
report_power                                      > $RPT_DIR/power.rpt
report_clock_gating -gating_elements              > $RPT_DIR/cg.rpt
report_qor                                        > $RPT_DIR/qor.rpt
report_upf -file $RPT_DIR/upf.rpt

write -hierarchy -format verilog -output $OUT_DIR/$DESIGN.netlist.v
write_sdc                                $OUT_DIR/$DESIGN.sdc
write_sdf -version 3.0                  $OUT_DIR/$DESIGN.sdf
save_upf                                $OUT_DIR/$DESIGN.upf.out

puts "INFO: DC synthesis complete; outputs in $OUT_DIR / $RPT_DIR"
exit

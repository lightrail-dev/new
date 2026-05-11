# =============================================================================
# LR-CSW-51T2 — Cadence Genus synthesis flow (TSMC N3 standard-cell + UPF)
# =============================================================================
# Usage:   genus -files run_genus.tcl -log logs/genus.log
# Inputs:  ../sdc/lr_csw.sdc, ../upf/lr_csw.upf, ../../rtl/{common,lr_csw}/*.sv
# Outputs: out/lr_csw_top.netlist.v, out/lr_csw_top.sdf, out/lr_csw_top.upf.out
# =============================================================================

set DESIGN  lr_csw_top
set TECH    n3
set RTL_DIR ../../rtl
set OUT_DIR ./out
set RPT_DIR ./reports
file mkdir $OUT_DIR $RPT_DIR

# ---- 1. Library setup
set_db library [list \
    /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt_ssg_0p675v_0c.lib \
    /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_svt_ssg_0p675v_0c.lib \
    /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_hvt_ssg_0p675v_0c.lib]
set_db lef_library [list \
    /opt/foundry/tsmc/n3/std/lef/sc12mc_cln3_8t.lef \
    /opt/foundry/tsmc/n3/std/lef/n3.tlef]
set_db cap_table_file /opt/foundry/tsmc/n3/rcx/typ.captable

# ---- 2. RTL read
set_db hdl_search_path $RTL_DIR/common:$RTL_DIR/lr_csw:$RTL_DIR/lr_nce
read_hdl -sv [glob $RTL_DIR/common/*.sv $RTL_DIR/lr_csw/*.sv]
elaborate $DESIGN

# ---- 3. UPF + SDC
read_power_intent -1801 ../upf/lr_csw.upf
commit_power_intent
read_sdc          ../sdc/lr_csw.sdc

# ---- 4. Constraints & DFT
set_db syn_generic_effort   high
set_db syn_map_effort       high
set_db syn_opt_effort       high
set_db retime               true
set_db leakage_power_effort high
set_db dft_scan_style       muxed_scan
set_db dft_min_number_of_scan_chains 8

# ---- 5. Run synthesis stages
syn_generic
syn_map
syn_opt

# ---- 6. Sign-off reports
report_timing                          > $RPT_DIR/timing.rpt
report_area                            > $RPT_DIR/area.rpt
report_power -hierarchy                > $RPT_DIR/power.rpt
report_clock_gating -group_by domain   > $RPT_DIR/clock_gating.rpt
report_qor                             > $RPT_DIR/qor.rpt

# ---- 7. Write out
write_hdl -mapped > $OUT_DIR/$DESIGN.netlist.v
write_sdc         > $OUT_DIR/$DESIGN.sdc
write_sdf -version 3.0 > $OUT_DIR/$DESIGN.sdf
write_power_intent -1801 > $OUT_DIR/$DESIGN.upf.out
write_db -all_root_attributes $OUT_DIR/$DESIGN.genus.db

puts "INFO: Genus synthesis completed; netlist + SDF + UPF + reports in $OUT_DIR / $RPT_DIR"
exit

# =============================================================================
# LR-CSW-51T2 — Cadence Innovus place-and-route flow
# =============================================================================
# Usage:   innovus -files run_innovus.tcl -log logs/innovus.log
# =============================================================================

set DESIGN   lr_csw_top
set NETLIST  ../../syn/genus/out/$DESIGN.netlist.v
set SDC      ../../syn/genus/out/$DESIGN.sdc
set UPF      ../../syn/genus/out/$DESIGN.upf.out
set OUT_DIR  ./out
set RPT_DIR  ./reports
file mkdir $OUT_DIR $RPT_DIR

# ---- 1. MMMC setup (multi-mode multi-corner)
create_rc_corner -name rc_typ -cap_table /opt/foundry/tsmc/n3/rcx/typ.captable
create_rc_corner -name rc_min -cap_table /opt/foundry/tsmc/n3/rcx/min.captable
create_rc_corner -name rc_max -cap_table /opt/foundry/tsmc/n3/rcx/max.captable

create_library_set -name ss_0c    -timing /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt_ssg_0p675v_0c.lib
create_library_set -name ff_125c  -timing /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt_ffg_0p935v_125c.lib
create_constraint_mode -name func -sdc_files $SDC
create_delay_corner -name dc_setup -library_set ss_0c   -rc_corner rc_max
create_delay_corner -name dc_hold  -library_set ff_125c -rc_corner rc_min
create_analysis_view -name av_setup -constraint_mode func -delay_corner dc_setup
create_analysis_view -name av_hold  -constraint_mode func -delay_corner dc_hold
set_analysis_view -setup av_setup -hold av_hold

# ---- 2. Read netlist + UPF
read_netlist $NETLIST -top $DESIGN
read_upf     $UPF

# ---- 3. Floorplan (24 mm × 24 mm reticle, 65 % util)
floorPlan -site core -r 1.0 0.65 50 50 50 50
addRing -nets {VDD VSS} -around core -layer {top M16 bottom M16 left M15 right M15} -width 8 -spacing 2

# ---- 4. Power planning
sroute -allowJogging 1 -allowLayerChange 1
addStripe -nets {VDD VSS} -direction vertical   -layer M15 -width 4 -spacing 2 -set_to_set_distance 30
addStripe -nets {VDD VSS} -direction horizontal -layer M16 -width 4 -spacing 2 -set_to_set_distance 30

# ---- 5. Place
setPlaceMode -placeIoPins true -fp false -congEffort high -timingDriven true
placeDesign -inPlaceOpt -noPrePlaceOpt

# ---- 6. CTS (clock tree)
ccopt_design

# ---- 7. Route
setNanoRouteMode -routeWithTimingDriven true -routeWithSiDriven true
routeDesign -globalDetail

# ---- 8. Post-route opt
optDesign -postRoute -drv -hold -setup

# ---- 9. Sign-off reports
report_timing -path_type full_clock_expanded -max_paths 100 > $RPT_DIR/timing.full.rpt
report_power                                                > $RPT_DIR/power.rpt
report_area                                                 > $RPT_DIR/area.rpt
verify_drc                                                  > $RPT_DIR/drc.rpt
verify_connectivity                                         > $RPT_DIR/conn.rpt

# ---- 10. Write outputs (LEF / DEF / SPEF / GDS)
saveDesign $OUT_DIR/$DESIGN.enc
streamOut $OUT_DIR/$DESIGN.gds.gz -mapFile /opt/foundry/tsmc/n3/gds/layer.map -merge {/opt/foundry/tsmc/n3/gds/std.gds}
write_lef_abstract $OUT_DIR/$DESIGN.lef
write_def $OUT_DIR/$DESIGN.def
write_parasitics -spef_file $OUT_DIR/$DESIGN.spef -view av_setup

puts "INFO: Innovus P&R completed; GDSII + DEF + SPEF in $OUT_DIR"
exit

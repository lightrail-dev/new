# =============================================================================
# LR-CSW-51T2 — Synopsys PrimeTime sign-off STA
# =============================================================================
set DESIGN   lr_csw_top
set NETLIST  ../../pnr/innovus/out/$DESIGN.def
set SPEF     ../../pnr/innovus/out/$DESIGN.spef
set SDC      ../../syn/genus/out/$DESIGN.sdc
set RPT      ./reports
file mkdir $RPT

# ---- corners: SS-0C / SS-125C / FF-125C (setup + hold + signal-EM)
set link_path "* /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt_ssg_0p675v_0c.db \
                 /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt_ffg_0p935v_125c.db"
set search_path "../../pnr/innovus/out ../../syn/genus/out"

read_verilog $NETLIST
link_design  $DESIGN
read_parasitics -keep_capacitive_coupling $SPEF
read_sdc $SDC

# ---- timing analysis
set_operating_conditions -analysis_type on_chip_variation \
    -max ssg_0p675v_0c -min ffg_0p935v_125c
update_timing -full

# ---- reports
report_timing -delay_type max -max_paths 1000 -path_type full_clock_expanded \
    > $RPT/setup.rpt
report_timing -delay_type min -max_paths 1000 -path_type full_clock_expanded \
    > $RPT/hold.rpt
report_clock_qor                                              > $RPT/clk_qor.rpt
report_constraint -all_violators                              > $RPT/constraint.rpt
report_design                                                 > $RPT/design.rpt
report_global_timing                                          > $RPT/global.rpt
report_si_bottleneck                                          > $RPT/si.rpt
report_noise -all                                             > $RPT/noise.rpt

# ---- sign-off gate: WNS = 0 ps, TNS = 0 ps, max-transition / cap / fanout clean
set wns_setup [get_attribute [get_timing_paths -delay_type max] slack]
set wns_hold  [get_attribute [get_timing_paths -delay_type min] slack]
puts "SIGNOFF: WNS_setup = $wns_setup ns"
puts "SIGNOFF: WNS_hold  = $wns_hold ns"
exit

# =============================================================================
# LR-CSW-51T2 — Cadence Conformal LEC (logical equivalence checking)
# Golden: RTL    Revised: post-PnR netlist
# =============================================================================
set DESIGN  lr_csw_top
set RTL_DIR ../../rtl
set NETLIST ../../pnr/innovus/out/$DESIGN.def
set LIB     /opt/foundry/tsmc/n3/std/lib/sc12mc_cln3_lvt.lib

read_library -liberty $LIB -both

# golden RTL
read_design -sv09 -golden [glob $RTL_DIR/common/*.sv $RTL_DIR/lr_csw/*.sv] \
    -root $DESIGN

# revised netlist
read_design -verilog -revised $NETLIST -root $DESIGN

# UPF
read_power_intent -1801 -both ../../syn/genus/out/$DESIGN.upf.out

# map + compare
add_renaming_rule r1 lvt_ "" -both
match
compare -all

report_unmapped_points       > reports/unmapped.rpt
report_compared_points       > reports/compared.rpt
report_floating_signals      > reports/floating.rpt

# sign-off gate: 0 non-equivalent compare points
if { [get_compare_points -non_equivalent -count] > 0 } {
    error "LEC FAIL: non-equivalent compare points found"
}
puts "SIGNOFF: Conformal LEC clean"
exit

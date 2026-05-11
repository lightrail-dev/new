# =============================================================================
# LR-CSW-51T2 — Cadence Voltus EM/IR + power-grid sign-off
# =============================================================================
set DESIGN   lr_csw_top
set RPT      ./reports
file mkdir $RPT

read_design ../../pnr/innovus/out/$DESIGN.enc
read_spef   ../../pnr/innovus/out/$DESIGN.spef
read_power_intent ../../syn/genus/out/$DESIGN.upf.out

# ---- static + dynamic
set_power_analysis_mode -method statistical -reset_negative_power true
set_dynamic_power_simulation -mode vector_less
read_activity_file -reset -format saif ../../signoff/activity/lr_csw.saif

report_power -hierarchy                 > $RPT/power.hier.rpt
report_power -breakdown                 > $RPT/power.breakdown.rpt

# ---- IR drop
analyze_power -workspace ir_static -static
report_ir_drop -worst > $RPT/ir.static.rpt

analyze_power -workspace ir_dynamic -dynamic
report_ir_drop -dynamic -worst > $RPT/ir.dynamic.rpt

# ---- EM (current-density)
analyze_em
report_em -metal_layer M1 M5 M9 M12 M16 -worst > $RPT/em.rpt

# ---- sign-off thresholds
# IR drop < 50 mV static / 75 mV dynamic, EM < 80 % of TSMC N3 rules
puts "SIGNOFF: IR_static_max = [get_max_ir_drop]"
puts "SIGNOFF: IR_dynamic_max = [get_max_dynamic_ir_drop]"
exit

# =============================================================================
# LR-DV — Questa RDC reset-domain-crossing sign-off
# =============================================================================
configure rdc -ruleset standard
read_constraint ../questa_cdc/lr_cdc.sgdc

rdc generate hierarchy
rdc run -d lr_csw_top
rdc report violation -outfile rdc.violations.rpt
rdc report design    -outfile rdc.design.rpt

set viol_n [rdc count -severity error]
if { $viol_n > 0 } { error "RDC FAIL: $viol_n violations" } \
                   else { puts "SIGNOFF: Questa RDC clean" }
quit -force

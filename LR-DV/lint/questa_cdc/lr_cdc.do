# =============================================================================
# LR-DV — Questa CDC clock-domain-crossing sign-off
# =============================================================================
# Methodology:
#   1. Enumerate clocks via SGDC (constraint file).
#   2. Run CDC structural + metastability injection.
#   3. 0-error gate; all crossings must be 2-flop or async-FIFO synchronised.
# =============================================================================
configure cdc -ruleset standard

read_constraint lr_cdc.sgdc
cdc generate hierarchy
cdc preference set -property AllowSimpleSync         -value true
cdc preference set -property AllowGrayCodedSync      -value true
cdc preference set -property AllowAsyncFifoSync      -value true
cdc preference set -property TreatHandshakeAsSync    -value true

cdc run -d lr_csw_top -fields {clk reset}
cdc report violation -outfile cdc.violations.rpt
cdc report design    -outfile cdc.design.rpt

# metastability injection
cdc inject metastability -mode random -count 1000 -seed 1
cdc report metastability -outfile cdc.meta.rpt

set viol_n [cdc count -severity error]
if { $viol_n > 0 } { error "CDC FAIL: $viol_n violations" } \
                   else { puts "SIGNOFF: Questa CDC clean" }
quit -force

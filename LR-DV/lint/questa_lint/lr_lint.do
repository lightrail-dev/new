# =============================================================================
# LR-DV — Questa Lint run script (sign-off ruleset)
# =============================================================================
# Invocation:  qverify -c -do lr_lint.do
# Output:      lint.db + lint.rpt
# Sign-off gate: 0 errors, 0 fatal warnings on the LR_SIGNOFF preset.
# =============================================================================

# load preset + custom add-ons
configure ruleset -import   {STD synthesizable_subset uvm low_power}
configure ruleset -from STD -severity error \
    {NO_TRIVIAL_CASE_ITEM ALWAYS_NO_SENSITIVITY ALWAYS_FF_NO_RESET \
     UNCONDITIONAL_LATCH MULTIPLE_DRIVERS COMB_LOOP UNREAD_NETS    \
     ASSIGN_MIX_DRIVE STD_TASK_NO_TIMING NONBLOCK_ASSIGN_IN_COMB   \
     CASE_IS_NOT_FULL}

# RTL load
do ../rtl_filelist.do
compile -L uvm-1.2

# run
lint -reset
lint -all
lint -severity error  -outfile lint.errors.rpt
lint -severity warning -outfile lint.warnings.rpt
save -file lint.db

# gate
set err_n [lint -count -severity error]
if { $err_n > 0 } { error "LINT FAIL: $err_n errors" } \
                  else { puts "SIGNOFF: Questa Lint clean" }
quit -force

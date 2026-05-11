# -----------------------------------------------------------------------------
# LR-DV UVM regression Makefile (QuestaSim 2024.1 or newer)
# -----------------------------------------------------------------------------
# Targets:
#   make compile          — vlog/vcom all RTL + TB sources
#   make smoke            — single-seed smoke test
#   make regress          — 4000-job nightly regression with coverage merge
#   make coverage         — vcover merge + report
#   make clean            — wipe work/ + transcripts
# -----------------------------------------------------------------------------

TOP_RTL    = lr_csw_top
TOP_TB     = tb_top
UVM_VERB   = UVM_MEDIUM
SEED       ?= random
COV_DIR    = cov

VLOG_ARGS  = -sv +acc=npr -mfcu -suppress 2275 \
             +incdir+../tb/uvm/env +incdir+../tb/uvm/test \
             -L uvm-1.2

VOPT_ARGS  = +acc=npr +cover=sbcef
VSIM_ARGS  = -voptargs="+acc" -coverage \
             +UVM_TESTNAME=lr_csw_smoke_test \
             +UVM_VERBOSITY=$(UVM_VERB) \
             -do "run -all; coverage save -onexit $(COV_DIR)/$@.ucdb; quit -f"

RTL_SRCS   = $(wildcard ../rtl/common/*.sv) \
             $(wildcard ../rtl/lr_csw/*.sv) \
             $(wildcard ../rtl/lr_nce/*.sv)
TB_SRCS    = $(wildcard ../tb/uvm/env/*.sv) \
             $(wildcard ../tb/uvm/test/*.sv) \
             $(wildcard ../tb/sva/*.sv)

compile:
	@mkdir -p work $(COV_DIR)
	vlib work
	vlog $(VLOG_ARGS) $(RTL_SRCS) $(TB_SRCS)

smoke: compile
	vsim -c $(TOP_TB) $(VSIM_ARGS) -sv_seed $(SEED)

regress: compile
	@for s in $$(seq 1 4000); do \
	    vsim -c $(TOP_TB) $(VSIM_ARGS) -sv_seed $$s \
	      -l $(COV_DIR)/run_$$s.log; \
	done

coverage:
	vcover merge $(COV_DIR)/merged.ucdb $(COV_DIR)/*.ucdb
	vcover report -details $(COV_DIR)/merged.ucdb \
	  -output $(COV_DIR)/coverage_report.txt

clean:
	rm -rf work transcript vsim.wlf $(COV_DIR)

.PHONY: compile smoke regress coverage clean

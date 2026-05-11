# =============================================================================
# LR-CSW-51T2 — Mentor Calibre DRC / LVS / ERC sign-off (TSMC N3 PDK)
# =============================================================================
# Invoked via:  calibre -drc -hier -hcell ../../signoff/drc_lvs/run_calibre.tcl
# Layout:   ../../pnr/innovus/out/lr_csw_top.gds.gz
# Schematic: ../../pnr/innovus/out/lr_csw_top.netlist.v
# =============================================================================

LAYOUT PATH      "../../pnr/innovus/out/lr_csw_top.gds.gz"
LAYOUT PRIMARY   "lr_csw_top"
LAYOUT SYSTEM    GDSII

SOURCE PATH      "../../pnr/innovus/out/lr_csw_top.netlist.v"
SOURCE PRIMARY   "lr_csw_top"
SOURCE SYSTEM    VERILOG

DRC RESULTS DATABASE     "reports/drc.results"
DRC SUMMARY REPORT       "reports/drc.summary"  HIER
DRC MAXIMUM RESULTS      ALL
DRC MAXIMUM VERTEX       4096

LVS REPORT               "reports/lvs.report"
LVS REPORT MAXIMUM       100
LVS RECOGNIZE GATES      ALL
LVS POWER NAME           VDD VDD_AUX VDD_CORE VDD_UCIE VDD_SERDES VDD_MEM
LVS GROUND NAME          VSS

INCLUDE "/opt/foundry/tsmc/n3/calibre/drc/cln3_drc_oa_rules"
INCLUDE "/opt/foundry/tsmc/n3/calibre/lvs/cln3_lvs_oa_rules"
INCLUDE "/opt/foundry/tsmc/n3/calibre/antenna/cln3_ant_rules"
INCLUDE "/opt/foundry/tsmc/n3/calibre/density/cln3_density_rules"

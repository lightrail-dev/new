# =========================================================================
# OpenROAD P&R flow for NCE top — SkyWater 130nm HD
# =========================================================================

set PLATFORM_DIR "/home/ubuntu/orfs/flow/platforms/sky130hd"
set DESIGN_NAME  "nce_top"
set NETLIST      "nce_top_netlist.v"
set SDC          "nce_top.sdc"
set OUTPUT_DIR   "results"

file mkdir $OUTPUT_DIR

# ---- Read Libraries ----
read_liberty $PLATFORM_DIR/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_lef $PLATFORM_DIR/lef/sky130_fd_sc_hd.tlef
read_lef $PLATFORM_DIR/lef/sky130_fd_sc_hd_merged.lef
read_verilog $NETLIST
link_design $DESIGN_NAME

# ---- Read SDC ----
read_sdc $SDC

# ---- Floorplan ----
# Die area: 800um x 800um (ample room for ~3600 cells at 130nm)
# Core margin 50um each side
initialize_floorplan -die_area "0 0 800 800" \
    -core_area "50 50 750 750" \
    -site unithd

# ---- Make Tracks ----
source $PLATFORM_DIR/make_tracks.tcl

# ---- IO Placement ----
place_pins -hor_layers met3 \
           -ver_layers met2 \
           -random

# ---- Tap Cells ----
set ::env(TAP_CELL_NAME) sky130_fd_sc_hd__tapvpwrvgnd_1
tapcell -distance 14 \
        -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1

# ---- PDN ----
source $PLATFORM_DIR/pdn.tcl

# ---- Global Placement ----
global_placement -density 0.60 \
                 -pad_left 2 \
                 -pad_right 2

# ---- IO Placement (optimized after global placement) ----
place_pins -hor_layers met3 \
           -ver_layers met2

# ---- Resizing ----
estimate_parasitics -placement
repair_design -max_wire_length 400
repair_timing -hold -hold_margin 0.1
repair_timing -setup

# ---- Detailed Placement ----
detailed_placement
check_placement -verbose
optimize_mirroring

# ---- CTS ----
clock_tree_synthesis -buf_list {sky130_fd_sc_hd__clkbuf_1 sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8 sky130_fd_sc_hd__clkbuf_16} \
                     -root_buf sky130_fd_sc_hd__clkbuf_16

# Post-CTS optimization
estimate_parasitics -placement
repair_timing -hold -hold_margin 0.1
repair_timing -setup

# Legalize again after CTS buffer insertion
detailed_placement

# ---- Filler Cells ----
filler_placement "sky130_fd_sc_hd__fill_1 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_8"
check_placement

# ---- Global Routing ----
set_global_routing_layer_adjustment met1-met5 0.2
set_routing_layers -signal met1-met5
set_routing_layers -clock met3-met5

global_route -guide_file $OUTPUT_DIR/${DESIGN_NAME}_route.guide \
             -congestion_iterations 100 \
             -verbose

# ---- Detailed Routing ----
detailed_route -output_drc $OUTPUT_DIR/${DESIGN_NAME}_drc.rpt \
               -output_maze $OUTPUT_DIR/${DESIGN_NAME}_maze.log \
               -bottom_routing_layer met1 \
               -top_routing_layer met5 \
               -verbose 1

# ---- Post-route timing ----
estimate_parasitics -global_routing

# ---- Reports ----
report_checks -path_delay min_max -format full_clock_expanded > $OUTPUT_DIR/${DESIGN_NAME}_timing.rpt
report_design_area > $OUTPUT_DIR/${DESIGN_NAME}_area.rpt
report_power > $OUTPUT_DIR/${DESIGN_NAME}_power.rpt

# ---- Write outputs ----
write_def $OUTPUT_DIR/${DESIGN_NAME}_final.def
write_verilog $OUTPUT_DIR/${DESIGN_NAME}_final.v
write_db $OUTPUT_DIR/${DESIGN_NAME}_final.odb

puts "=== P&R COMPLETE ==="
puts "DEF:     $OUTPUT_DIR/${DESIGN_NAME}_final.def"
puts "ODB:     $OUTPUT_DIR/${DESIGN_NAME}_final.odb"
exit

# =============================================================================
# LR-CSW FPGA prototype constraints — AMD Versal Premium VP2802
# =============================================================================

# ---- clocks (board-supplied)
set_property PACKAGE_PIN AT41 [get_ports clk_core]
set_property IOSTANDARD LVCMOS18 [get_ports clk_core]
create_clock -period 5.000 -name clk_core_pin [get_ports clk_core]

set_property PACKAGE_PIN AU41 [get_ports clk_mem]
set_property IOSTANDARD LVCMOS18 [get_ports clk_mem]
create_clock -period 6.400 -name clk_mem_pin  [get_ports clk_mem]

# ---- 16 GTM SerDes quads (200 G PAM4 → 112 G GTM 2:1 adapter)
foreach quad {Q224 Q225 Q226 Q227 Q228 Q229 Q230 Q231 \
              Q232 Q233 Q234 Q235 Q236 Q237 Q238 Q239} {
    set_property PACKAGE_PIN_RANGE "$quad" [get_ports serdes_tx_p[*]]
}

# ---- async clock groups (matches lr_csw.sdc)
set_clock_groups -asynchronous \
    -group [get_clocks clk_core_pin] \
    -group [get_clocks clk_mem_pin] \
    -group [get_clocks -of_objects [get_pins aurora_inst/inst/user_clk]] \
    -group [get_clocks -of_objects [get_pins cips_inst/inst/pcie_axi_clk]]

# ---- power
set_operating_conditions -voltage 0.85 -ambient 25

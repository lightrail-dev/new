# =============================================================================
# LR-CSW-51T2 — top-level SDC constraints (PrimeTime / Tempus / Genus)
# Process: TSMC N3, signoff temperature 0 / 25 / 125 °C, slow / typ / fast.
# =============================================================================

set CORE_PERIOD     0.500  ;# 2.0 GHz
set MEM_PERIOD      0.667  ;# 1.5 GHz
set SERDES_PERIOD   0.625  ;# 1.6 GHz (224 G PAM4 / 2 / 224 = 112 G symbol / 4)
set UCIE_PERIOD     0.250  ;# 4.0 GHz
set PCIE_PERIOD     4.000  ;# 250 MHz aux
set JTAG_PERIOD    20.000  ;# 50 MHz
set REF_PERIOD      6.400  ;# 156.25 MHz
set AUX_PERIOD     10.000  ;# 100 MHz

# -----------------------------------------------------------------------------
# Clocks
# -----------------------------------------------------------------------------
create_clock -name clk_core        -period $CORE_PERIOD   [get_ports clk_core]
create_clock -name clk_mem         -period $MEM_PERIOD    [get_ports clk_mem]
create_clock -name clk_ucie_tx     -period $UCIE_PERIOD   [get_ports clk_ucie_tx]
create_clock -name clk_ucie_rx     -period $UCIE_PERIOD   [get_ports clk_ucie_rx]
create_clock -name clk_pcie_aux    -period $PCIE_PERIOD   [get_ports clk_pcie_aux]
create_clock -name clk_jtag        -period $JTAG_PERIOD   [get_ports clk_jtag]
create_clock -name clk_refclk      -period $REF_PERIOD    [get_ports clk_refclk]
create_clock -name clk_aux         -period $AUX_PERIOD    [get_ports clk_aux]

# Per-quadrant SerDes TX/RX (16 quadrants ⇒ 32 clocks)
for {set q 0} {$q < 16} {incr q} {
    create_clock -name clk_serdes_tx_$q -period $SERDES_PERIOD \
        [get_ports clk_serdes_tx[$q]]
    create_clock -name clk_serdes_rx_$q -period $SERDES_PERIOD \
        [get_ports clk_serdes_rx[$q]]
}

# -----------------------------------------------------------------------------
# Asynchronous clock groups (all CDC paths are timing-quasi-static)
# -----------------------------------------------------------------------------
set_clock_groups -name async_groups -asynchronous \
    -group {clk_core clk_mem} \
    -group {clk_ucie_tx clk_ucie_rx} \
    -group {clk_pcie_aux} \
    -group {clk_jtag} \
    -group {clk_aux} \
    -group {clk_refclk} \
    -group [get_clocks clk_serdes_tx_*] \
    -group [get_clocks clk_serdes_rx_*]

# -----------------------------------------------------------------------------
# Clock uncertainty (jitter + skew) — sign-off corners
# -----------------------------------------------------------------------------
set_clock_uncertainty 0.030 [get_clocks clk_core]
set_clock_uncertainty 0.030 [get_clocks clk_mem]
set_clock_uncertainty 0.010 [get_clocks clk_ucie_*]
set_clock_uncertainty 0.040 [get_clocks clk_serdes_*]
set_clock_uncertainty 0.020 [get_clocks clk_aux]
set_clock_transition  0.020 [all_clocks]

# -----------------------------------------------------------------------------
# I/O constraints
# -----------------------------------------------------------------------------
# JTAG TAP is synchronous within clk_jtag — input/output delays per IEEE 1149.1
set_input_delay  -clock clk_jtag 4.0 [get_ports {tms tdi}]
set_output_delay -clock clk_jtag 4.0 [get_ports {tdo}]

# UCIe bus is source-synchronous, eye centred — derate ±0.05 UI
set_input_delay  -clock clk_ucie_rx -max 0.075 [get_ports {ucie_rx_data ucie_rx_valid}]
set_input_delay  -clock clk_ucie_rx -min 0.025 [get_ports {ucie_rx_data ucie_rx_valid}]
set_output_delay -clock clk_ucie_tx -max 0.075 [get_ports {ucie_tx_data ucie_tx_valid}]
set_output_delay -clock clk_ucie_tx -min 0.025 [get_ports {ucie_tx_data ucie_tx_valid}]

# BMC APB — single-cycle, derated 30 %
set_input_delay  -clock clk_aux  3.0 [get_ports {bmc_p*}]
set_output_delay -clock clk_aux  3.0 [get_ports {bmc_p* irq_top}]

# -----------------------------------------------------------------------------
# False paths
# -----------------------------------------------------------------------------
set_false_path -from [get_ports {por_rst_n warm_rst_n soft_rst_n jtag_rst_n}]
set_false_path -through [get_pins -hierarchical *u_*_2ff/q1_reg*/D]
set_false_path -through [get_pins -hierarchical *u_*_2ff/q2_reg*/D]

# -----------------------------------------------------------------------------
# Multicycle paths (CSR-shadow ⇒ design, 2-cycle propagation)
# -----------------------------------------------------------------------------
set_multicycle_path -setup 2 -from [get_pins -hierarchical *u_csr/regs_reg*/Q]
set_multicycle_path -hold  1 -from [get_pins -hierarchical *u_csr/regs_reg*/Q]

# -----------------------------------------------------------------------------
# Maximum transition / capacitance / fanout — physical-design hygiene
# -----------------------------------------------------------------------------
set_max_transition  0.150 [current_design]
set_max_capacitance 0.500 [current_design]
set_max_fanout      32    [current_design]

# -----------------------------------------------------------------------------
# Operating conditions (slow-corner sign-off)
# -----------------------------------------------------------------------------
set_operating_conditions -analysis_type on_chip_variation \
    -max ssg_0p675v_0c   -min ffg_0p935v_125c

puts "INFO: lr_csw.sdc loaded — [llength [all_clocks]] clocks defined"

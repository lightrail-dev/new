# =========================================================================
# LightRail AI — Dual-NCE Accelerator Board
# Synopsys Design Constraints (SDC) for nce_top
#
# Clock domains:
#   sys_clk  — 200 MHz system/control clock
#   brg_clk  — 500 MHz source-synchronous inter-chip bridge clock
#   i2c_clk  — derived from sys_clk, 400 kHz (internal to i2c_master)
# =========================================================================

# ---- Primary Clocks ----
create_clock -name sys_clk -period 5.000 [get_ports sys_clk]
create_clock -name brg_clk -period 2.000 [get_ports brg_clk]

# ---- Generated Clocks ----
# Forwarded bridge clock (LVDS output)
create_generated_clock -name brg_fwd_clk \
    -source [get_ports brg_clk] \
    -divide_by 1 \
    [get_ports brg_fwd_clk_p]

# ---- Clock Groups (asynchronous domains) ----
set_clock_groups -asynchronous \
    -group [get_clocks sys_clk] \
    -group [get_clocks brg_clk]

# ---- Input Delays ----
# AXI4-Lite interface (sys_clk domain, from PCIe root complex)
set_input_delay -clock sys_clk -max 1.500 [get_ports {s_axi_*}]
set_input_delay -clock sys_clk -min 0.500 [get_ports {s_axi_*}]

# Bridge PHY inputs (brg_clk domain, source-synchronous from remote NCE)
set_input_delay -clock brg_clk -max 0.400 [get_ports {brg_data_in[*]}]
set_input_delay -clock brg_clk -min 0.100 [get_ports {brg_data_in[*]}]
set_input_delay -clock brg_clk -max 0.400 [get_ports {brg_valid_in}]
set_input_delay -clock brg_clk -min 0.100 [get_ports {brg_valid_in}]
set_input_delay -clock brg_clk -max 0.400 [get_ports {brg_last_in}]
set_input_delay -clock brg_clk -min 0.100 [get_ports {brg_last_in}]
set_input_delay -clock brg_clk -max 0.400 [get_ports {brg_credit_in[*]}]
set_input_delay -clock brg_clk -min 0.100 [get_ports {brg_credit_in[*]}]
set_input_delay -clock brg_clk -max 0.400 [get_ports {brg_credit_in_valid}]
set_input_delay -clock brg_clk -min 0.100 [get_ports {brg_credit_in_valid}]
set_input_delay -clock brg_clk -max 0.400 [get_ports {brg_err_in}]
set_input_delay -clock brg_clk -min 0.100 [get_ports {brg_err_in}]

# I2C inputs (sys_clk domain, slow bus)
set_input_delay -clock sys_clk -max 2.000 [get_ports {i2c_scl_in i2c_sda_in}]
set_input_delay -clock sys_clk -min 0.000 [get_ports {i2c_scl_in i2c_sda_in}]

# Strap pin (static, but constrain for tool happiness)
set_input_delay -clock sys_clk -max 2.000 [get_ports {node_id}]
set_input_delay -clock sys_clk -min 0.000 [get_ports {node_id}]

# Reset inputs
set_input_delay -clock sys_clk -max 2.000 [get_ports {sys_rst_n}]
set_input_delay -clock sys_clk -min 0.000 [get_ports {sys_rst_n}]
set_input_delay -clock brg_clk -max 0.500 [get_ports {brg_rst_n}]
set_input_delay -clock brg_clk -min 0.000 [get_ports {brg_rst_n}]

# ---- Output Delays ----
# AXI4-Lite outputs
set_output_delay -clock sys_clk -max 1.500 [get_ports {s_axi_*}]
set_output_delay -clock sys_clk -min 0.500 [get_ports {s_axi_*}]

# Bridge PHY outputs
set_output_delay -clock brg_clk -max 0.300 [get_ports {brg_data_out[*]}]
set_output_delay -clock brg_clk -min 0.100 [get_ports {brg_data_out[*]}]
set_output_delay -clock brg_clk -max 0.300 [get_ports {brg_valid_out}]
set_output_delay -clock brg_clk -min 0.100 [get_ports {brg_valid_out}]
set_output_delay -clock brg_clk -max 0.300 [get_ports {brg_last_out}]
set_output_delay -clock brg_clk -min 0.100 [get_ports {brg_last_out}]
set_output_delay -clock brg_clk -max 0.300 [get_ports {brg_credit_out[*]}]
set_output_delay -clock brg_clk -min 0.100 [get_ports {brg_credit_out[*]}]
set_output_delay -clock brg_clk -max 0.300 [get_ports {brg_credit_out_valid}]
set_output_delay -clock brg_clk -min 0.100 [get_ports {brg_credit_out_valid}]
set_output_delay -clock brg_clk -max 0.300 [get_ports {brg_ack_out}]
set_output_delay -clock brg_clk -min 0.100 [get_ports {brg_ack_out}]

# Forwarded clock output
set_output_delay -clock brg_clk -max 0.200 [get_ports {brg_fwd_clk_p brg_fwd_clk_n}]
set_output_delay -clock brg_clk -min 0.050 [get_ports {brg_fwd_clk_p brg_fwd_clk_n}]

# I2C outputs
set_output_delay -clock sys_clk -max 2.000 [get_ports {i2c_scl_out i2c_scl_oen i2c_sda_out i2c_sda_oen}]
set_output_delay -clock sys_clk -min 0.000 [get_ports {i2c_scl_out i2c_scl_oen i2c_sda_out i2c_sda_oen}]

# IRQ and status outputs
set_output_delay -clock sys_clk -max 2.000 [get_ports {irq_out dvfs_state[*] thermal_shutdown}]
set_output_delay -clock sys_clk -min 0.000 [get_ports {irq_out dvfs_state[*] thermal_shutdown}]

# ---- False Paths ----
# Node ID strap is a static configuration pin
set_false_path -from [get_ports node_id]

# Reset synchronizers (async reset release is handled internally)
set_false_path -from [get_ports sys_rst_n]
set_false_path -from [get_ports brg_rst_n]

# ---- Max Delay for CDC paths ----
# Async FIFO gray-coded pointers crossing between sys_clk and brg_clk
# The 2-FF synchronizer path must complete within one destination clock period
set_max_delay -from [get_clocks sys_clk] -to [get_clocks brg_clk] -datapath_only 2.000
set_max_delay -from [get_clocks brg_clk] -to [get_clocks sys_clk] -datapath_only 5.000

# ---- Design Rule Constraints ----
set_max_transition 0.150 [current_design]
set_max_fanout 32 [current_design]
set_max_capacitance 0.100 [all_outputs]

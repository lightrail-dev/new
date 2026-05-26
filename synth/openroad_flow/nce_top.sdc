# SDC for OpenROAD P&R — NCE top-level
# Two clock domains: sys_clk (200 MHz) and brg_clk (500 MHz)

create_clock -name sys_clk -period 5.0 [get_ports sys_clk]
create_clock -name brg_clk -period 2.0 [get_ports brg_clk]

set_clock_groups -asynchronous \
    -group [get_clocks sys_clk] \
    -group [get_clocks brg_clk]

# I/O delays — AXI (sys_clk domain)
set_input_delay  -clock sys_clk 1.5 [get_ports {s_axi_*}]
set_output_delay -clock sys_clk 1.5 [get_ports {s_axi_*}]

# I/O delays — Bridge (brg_clk domain)
set_input_delay  -clock brg_clk 0.4 [get_ports {brg_data_in* brg_valid_in brg_last_in brg_credit_in* brg_credit_in_valid brg_err_in}]
set_output_delay -clock brg_clk 0.3 [get_ports {brg_data_out* brg_valid_out brg_last_out brg_credit_out* brg_credit_out_valid brg_ack_out brg_fwd_clk_p brg_fwd_clk_n}]

# I2C (slow)
set_input_delay  -clock sys_clk 2.0 [get_ports {i2c_scl_in i2c_sda_in}]
set_output_delay -clock sys_clk 2.0 [get_ports {i2c_scl_out i2c_scl_oen i2c_sda_out i2c_sda_oen}]

# Misc
set_input_delay  -clock sys_clk 2.0 [get_ports {node_id sys_rst_n}]
set_input_delay  -clock brg_clk 0.5 [get_ports {brg_rst_n}]
set_output_delay -clock sys_clk 2.0 [get_ports {irq_out dvfs_state* thermal_shutdown}]

# False paths
set_false_path -from [get_ports node_id]
set_false_path -from [get_ports sys_rst_n]
set_false_path -from [get_ports brg_rst_n]

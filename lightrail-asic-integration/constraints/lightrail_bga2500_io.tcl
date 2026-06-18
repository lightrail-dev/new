# LightRail BGA-2500 → ElemRV-N I/O placement constraints
# PDK: IHP SG13G2  |  Package: BGA-2500 (50×50 array, 0.8 mm pitch)
# Die size target: 4.5 mm × 4.5 mm (fits inside BGA keepout)
#
# Ball assignment follows LightRail schematic convention:
#   - North edge  : PCIe Gen5 x16 SerDes lanes
#   - East edge   : HBM4 PHY (JTAG, SERDES, power)
#   - South edge  : TFLN interposer optical I/O control (SPI, I2C, GPIO)
#   - West edge   : DFB laser array bias / VCSEL control (PWM, SPI)
#   - Center ring : Power (VDD_CORE 0.85 V, VDD_IO 1.8 V, GND)

# ── Die floorplan ─────────────────────────────────────────────────────────────
set_die_area   0 0 4500 4500   ;# µm
set_core_area  100 100 4400 4400

# ── Clock input ───────────────────────────────────────────────────────────────
# BGA ball A1 → differential 100 MHz reference (from PCIe refclk)
place_pin -pin_name clk_p    -layer Metal5 -location {100 4400} -pin_size {10 50}
place_pin -pin_name clk_n    -layer Metal5 -location {100 4340} -pin_size {10 50}

# ── Reset ─────────────────────────────────────────────────────────────────────
place_pin -pin_name rst_n    -layer Metal5 -location {150 4400} -pin_size {10 50}

# ── JTAG debug (TFLN interposer boundary scan) ────────────────────────────────
place_pin -pin_name jtag_tck -layer Metal5 -location {200 0}   -pin_size {10 50}
place_pin -pin_name jtag_tms -layer Metal5 -location {250 0}   -pin_size {10 50}
place_pin -pin_name jtag_tdi -layer Metal5 -location {300 0}   -pin_size {10 50}
place_pin -pin_name jtag_tdo -layer Metal5 -location {350 0}   -pin_size {10 50}

# ── UART console (Zephyr boot log) ────────────────────────────────────────────
place_pin -pin_name uart_tx  -layer Metal5 -location {400 0}   -pin_size {10 50}
place_pin -pin_name uart_rx  -layer Metal5 -location {450 0}   -pin_size {10 50}

# ── SPI0 → TFLN modulator control ─────────────────────────────────────────────
place_pin -pin_name spi0_clk  -layer Metal5 -location {0 100}  -pin_size {50 10}
place_pin -pin_name spi0_mosi -layer Metal5 -location {0 150}  -pin_size {50 10}
place_pin -pin_name spi0_miso -layer Metal5 -location {0 200}  -pin_size {50 10}
place_pin -pin_name spi0_cs_n -layer Metal5 -location {0 250}  -pin_size {50 10}

# ── SPI1 → DFB laser array bias DAC ──────────────────────────────────────────
place_pin -pin_name spi1_clk  -layer Metal5 -location {0 300}  -pin_size {50 10}
place_pin -pin_name spi1_mosi -layer Metal5 -location {0 350}  -pin_size {50 10}
place_pin -pin_name spi1_cs_n -layer Metal5 -location {0 400}  -pin_size {50 10}

# ── I2C0 → memristive grid telemetry ──────────────────────────────────────────
place_pin -pin_name i2c0_sda  -layer Metal5 -location {0 450}  -pin_size {50 10}
place_pin -pin_name i2c0_scl  -layer Metal5 -location {0 500}  -pin_size {50 10}

# ── GPIO bank (ternary encoder enable / ternary data lines) ───────────────────
foreach {idx y} {0 600 1 650 2 700 3 750 4 800 5 850 6 900 7 950} {
  place_pin -pin_name gpio_$idx -layer Metal5 -location "0 $y" -pin_size {50 10}
}

# ── PCIe x16 SerDes (North, pairs mapped to BGA row A..P col 25..40) ─────────
set pcie_x 500
foreach lane {0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15} {
  set bx [expr {$pcie_x + $lane * 220}]
  place_pin -pin_name pcie_tx_p_$lane -layer Metal5 -location "$bx 4400" -pin_size {10 50}
  place_pin -pin_name pcie_tx_n_$lane -layer Metal5 -location "$bx 4350" -pin_size {10 50}
  place_pin -pin_name pcie_rx_p_$lane -layer Metal5 -location "$bx 4300" -pin_size {10 50}
  place_pin -pin_name pcie_rx_n_$lane -layer Metal5 -location "$bx 4250" -pin_size {10 50}
}

# ── HBM4 PHY control sideband (East, BGA col 45..50) ─────────────────────────
place_pin -pin_name hbm_ck_p   -layer Metal5 -location {4400 1000} -pin_size {50 10}
place_pin -pin_name hbm_ck_n   -layer Metal5 -location {4400 1050} -pin_size {50 10}
place_pin -pin_name hbm_cke    -layer Metal5 -location {4400 1100} -pin_size {50 10}
place_pin -pin_name hbm_cs_n   -layer Metal5 -location {4400 1150} -pin_size {50 10}

# ── Timing constraints ────────────────────────────────────────────────────────
create_clock -name sys_clk -period 10.0 [get_ports clk_p]  ;# 100 MHz
set_input_delay  -clock sys_clk  2.0 [all_inputs]
set_output_delay -clock sys_clk  2.0 [all_outputs]

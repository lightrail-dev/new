#!/usr/bin/env python3
"""
Generate the LightRail NCE Gen3 82-Component KiCad 8 Schematic.

7 Sections, 86 component instances, proper net connectivity via labels at pin endpoints.
"""
import os

_uuid_counter = 0

def uid():
    global _uuid_counter
    _uuid_counter += 1
    return f"a{_uuid_counter:07x}-0000-4000-8000-{_uuid_counter:012x}"

# ── Pin and symbol primitives ────────────────────────────────────────────

class Pin:
    def __init__(self, elec, px, py, angle, name, number):
        self.elec = elec
        self.px = px
        self.py = py
        self.angle = angle
        self.name = name
        self.number = number

    def lib_line(self):
        return (f'        (pin {self.elec} line (at {self.px} {self.py} {self.angle}) '
                f'(length 2.54) '
                f'(name "{self.name}" (effects (font (size 1.27 1.27)))) '
                f'(number "{self.number}" (effects (font (size 1.27 1.27)))))')

    def global_pos(self, sx, sy):
        """Pin endpoint in global schematic coords. KiCad inverts Y."""
        return (sx + self.px, sy - self.py)


class SymDef:
    def __init__(self, lib_name, ref_prefix, default_value, footprint, mpn, desc):
        self.lib_name = lib_name
        self.ref_prefix = ref_prefix
        self.default_value = default_value
        self.footprint = footprint
        self.mpn = mpn
        self.desc = desc
        self.pins = []
        self._pin_map = {}

    def add(self, elec, px, py, angle, name, number):
        p = Pin(elec, px, py, angle, name, number)
        self.pins.append(p)
        self._pin_map[name] = p
        return self

    def pin(self, name):
        return self._pin_map[name]

    def lib_block(self):
        short = self.lib_name.split(':')[1]
        pins_str = "\n".join(p.lib_line() for p in self.pins)
        return f"""    (symbol "{self.lib_name}" (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "{self.ref_prefix}" (at 0 0 0) (effects (font (size 1.27 1.27))))
      (property "Value" "{self.default_value}" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "{self.footprint}" (at 0 -5.08 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "{self.desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "MPN" "{self.mpn}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "{short}_1_1"
{pins_str}
      )
    )"""


# ── Symbol definitions ───────────────────────────────────────────────────

def def_nce():
    s = SymDef("LightRail:NCE_Gen3_SpikingBrain", "U", "NCE_Gen3_SpikingBrain",
               "LightRail:BGA-2500_40x40mm_P0.8mm", "LR-NCE-G3-BGA2500-001",
               "8x8mm SMIC 28nm 0.8V/1000A 35W")
    for i in range(8):
        y = 50.80 - i * 3.81
        s.add("output", -43.18, y, 0, f"RF_TX_{i}P", f"A{2*i+1}")
        s.add("output", -43.18, y - 1.27, 0, f"RF_TX_{i}N", f"A{2*i+2}")
    for i in range(16):
        y = 15.24 - i * 2.54
        s.add("bidirectional", -43.18, y, 0, f"PCIE_TX{i}P", f"B{2*i+1}")
        s.add("bidirectional", -43.18, y - 1.27, 0, f"PCIE_TX{i}N", f"B{2*i+2}")
    for i in range(16):
        y = 50.80 - i * 2.54
        s.add("bidirectional", 43.18, y, 180, f"HBM_CH{i}", f"C{i+1}")
    s.add("output", 43.18, 10.16, 180, "HBM_REFCK_P", "D1")
    s.add("output", 43.18, 8.89, 180, "HBM_REFCK_N", "D2")
    s.add("passive", 43.18, 6.35, 180, "HBM_CATTRIP", "D3")
    s.add("passive", 43.18, 3.81, 180, "HBM_PWR_GOOD", "D4")
    s.add("bidirectional", -43.18, -40.64, 0, "I2C_SDA", "CTRL1")
    s.add("input", -43.18, -41.91, 0, "I2C_SCL", "CTRL2")
    s.add("input", -43.18, -44.45, 0, "SPI_MOSI", "CTRL3")
    s.add("output", -43.18, -45.72, 0, "SPI_MISO", "CTRL3B")
    s.add("input", -43.18, -46.99, 0, "SPI_SCK", "CTRL4")
    s.add("input", -43.18, -48.26, 0, "SPI_CS", "CTRL5")
    s.add("output", -43.18, -50.80, 0, "TFLN_CLK_P", "TFLN1")
    s.add("output", -43.18, -52.07, 0, "TFLN_CLK_N", "TFLN2")

    s.add("power_in", -10.16, 55.88, 270, "V_CORE", "PWR1")
    s.add("power_in", -5.08, 55.88, 270, "VDD_IO", "PWR2")
    s.add("power_in", 0, 55.88, 270, "VDDQ", "PWR3")
    s.add("power_in", 0, -55.88, 90, "GND", "GND1")
    return s


def def_hbm4():
    s = SymDef("LightRail:HBM4_16GB_12Hi", "U", "HBM4-16GB",
               "LightRail:BGA-1024_12x9mm", "SK_HBM4_16GB_12H",
               "16GB 12-Hi 8.4Gbps/pin 1.2V")
    s.add("power_in", -12.70, 15.24, 0, "VDDC", "1")
    s.add("power_in", -12.70, 12.70, 0, "VDDQL", "2")
    s.add("power_in", -12.70, 10.16, 0, "VDDQ", "3")
    s.add("power_in", -12.70, 7.62, 0, "VPP", "4")
    s.add("power_in", -12.70, 5.08, 0, "VSS", "5")
    s.add("input", 12.70, 15.24, 180, "REFCK_P", "6")
    s.add("input", 12.70, 12.70, 180, "REFCK_N", "7")
    s.add("open_collector", 12.70, 10.16, 180, "CATTRIP", "8")
    s.add("open_collector", 12.70, 7.62, 180, "PWR_GOOD", "9")
    s.add("bidirectional", 12.70, 5.08, 180, "IEEE1500_TCK", "10")
    s.add("bidirectional", 12.70, 2.54, 180, "IEEE1500_TMS", "11")
    s.add("bidirectional", 12.70, 0, 180, "IEEE1500_TDI", "12")
    s.add("bidirectional", 12.70, -2.54, 180, "IEEE1500_TDO", "13")
    s.add("bidirectional", -12.70, -5.08, 0, "DATA_CH", "14")
    return s


def def_tfln():
    s = SymDef("LightRail:TFLN_PIC_4xMZM", "U", "TFLN_PIC_4xMZM",
               "LightRail:Custom_Optical_Module_25x8mm", "TFLN-MZM-400G-C",
               "X-cut LiNbO3 Vpi<2V 100GHz BW 4ch")
    for i in range(4):
        y = 12.7 - i * 3.81
        s.add("input", -15.24, y, 0, f"RF_IN_{i}P", f"A{2*i+1}")
        s.add("input", -15.24, y - 1.27, 0, f"RF_IN_{i}N", f"A{2*i+2}")
    for i in range(4):
        y = 12.7 - i * 3.81
        s.add("output", 15.24, y, 180, f"OPT_OUT_{i}", f"E{i+1}")
    for i in range(4):
        y = -3.81 - i * 2.54
        s.add("input", 15.24, y, 180, f"OPT_IN_{i}", f"G{i+1}")
    for i in range(4):
        s.add("input", i * 2.54, 17.78, 270, f"VBIAS_{i}", f"J{i+1}")
    s.add("power_in", -5.08, 17.78, 270, "VDD_1V8", "P1")
    s.add("power_in", -7.62, 17.78, 270, "VDD_3V3", "P2")
    s.add("power_in", 0, -17.78, 90, "GND", "P3")
    s.add("bidirectional", -12.7, -15.24, 0, "SDA", "M1")
    s.add("input", -12.7, -16.51, 0, "SCL", "M2")
    s.add("input", -15.24, -10.16, 0, "CLK_P", "C1")
    s.add("input", -15.24, -11.43, 0, "CLK_N", "C2")
    return s


def def_hmc8410():
    s = SymDef("LightRail:HMC8410", "U", "HMC8410",
               "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm", "HMC8410LP2FE",
               "100GHz RF Driver")
    s.add("input", -10.16, 5.08, 0, "RF_INP", "1")
    s.add("input", -10.16, 3.81, 0, "RF_INN", "2")
    s.add("output", 10.16, 5.08, 180, "RF_OUTP", "3")
    s.add("output", 10.16, 3.81, 180, "RF_OUTN", "4")
    s.add("power_in", -10.16, -2.54, 0, "VCC1", "5")
    s.add("power_in", -10.16, -3.81, 0, "VCC2", "6")
    s.add("input", 10.16, 0, 180, "GAIN_ADJ", "7")
    s.add("power_in", 0, -8.89, 90, "GND", "8")
    return s


def def_isl69260():
    s = SymDef("LightRail:ISL69260", "U", "ISL69260",
               "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", "ISL69260IRAZ",
               "24-phase VRM Controller")
    for i in range(6):
        y = 15.24 - i * 2.54
        s.add("output", 15.24, y, 180, f"PWM{i}", str(i + 1))
    s.add("power_in", -5.08, 20.32, 270, "VCC", "30")
    s.add("power_in", 0, -20.32, 90, "GND", "31")
    s.add("bidirectional", -15.24, 10.16, 0, "SDA", "32")
    s.add("input", -15.24, 8.89, 0, "SCL", "33")
    s.add("input", -15.24, 5.08, 0, "VID0", "34")
    s.add("input", -15.24, 3.81, 0, "VID1", "35")
    s.add("input", -15.24, 2.54, 0, "VID2", "36")
    s.add("input", -15.24, 0, 0, "VSEN_P", "37")
    s.add("input", -15.24, -1.27, 0, "VSEN_N", "38")
    s.add("output", -15.24, -5.08, 0, "PGOOD", "39")
    s.add("input", -15.24, -7.62, 0, "EN", "40")
    return s


def def_isl99390():
    s = SymDef("LightRail:ISL99390", "U", "ISL99390",
               "LightRail:PQFN-40_5x6mm", "ISL99390FRAZ",
               "90A DrMOS")
    s.add("power_in", -10.16, 5.08, 0, "PVCC", "1")
    s.add("input", -10.16, 2.54, 0, "PWM", "2")
    s.add("input", -10.16, 0, 0, "DRVH", "3")
    s.add("input", -10.16, -2.54, 0, "DRVL", "4")
    s.add("passive", 10.16, 5.08, 180, "PHASE", "5")
    s.add("output", 10.16, 0, 180, "IMON", "6")
    s.add("power_in", 0, -10.16, 90, "PGND", "7")
    s.add("power_in", -10.16, -5.08, 0, "BOOT", "8")
    return s


def def_adp7118():
    s = SymDef("LightRail:ADP7118", "U", "ADP7118-0.9V",
               "Package_TO_SOT_SMD:SOT-23-5", "ADP7118AUJZ-0.9-R7",
               "0.9V LDO for TFLN RF")
    s.add("power_in", -7.62, 1.27, 0, "IN", "1")
    s.add("input", -7.62, -1.27, 0, "EN", "3")
    s.add("power_out", 7.62, 1.27, 180, "OUT", "5")
    s.add("passive", 7.62, -1.27, 180, "NR_SS", "4")
    s.add("power_in", 0, -6.35, 90, "GND", "2")
    return s


def def_si5395a():
    s = SymDef("LightRail:Si5395A", "U", "Si5395A",
               "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", "Si5395A-A-GM",
               "sub-50fs Jitter Cleaner")
    s.add("input", -12.7, 8.89, 0, "IN0P", "1")
    s.add("input", -12.7, 7.62, 0, "IN0N", "2")
    s.add("input", -12.7, 5.08, 0, "IN1P", "3")
    s.add("input", -12.7, 3.81, 0, "IN1N", "4")
    s.add("input", -12.7, 1.27, 0, "XA", "5")
    s.add("input", -12.7, 0, 0, "XB", "6")
    s.add("bidirectional", -12.7, -3.81, 0, "SDA", "15")
    s.add("input", -12.7, -5.08, 0, "SCL", "16")
    s.add("input", -12.7, -7.62, 0, "RST", "17")
    s.add("output", 12.7, 8.89, 180, "OUT0P", "7")
    s.add("output", 12.7, 7.62, 180, "OUT0N", "8")
    s.add("output", 12.7, 5.08, 180, "OUT1P", "9")
    s.add("output", 12.7, 3.81, 180, "OUT1N", "10")
    s.add("output", 12.7, 1.27, 180, "OUT2P", "11")
    s.add("output", 12.7, 0, 180, "OUT2N", "12")
    s.add("output", 12.7, -2.54, 180, "OUT3P", "13")
    s.add("output", 12.7, -3.81, 180, "OUT3N", "14")
    s.add("power_in", -2.54, 13.97, 270, "VDD", "18")
    s.add("power_in", -5.08, 13.97, 270, "VDDA", "19")
    s.add("power_in", 0, -13.97, 90, "GND", "20")
    return s


def def_bcm84881():
    s = SymDef("LightRail:BCM84881", "U", "BCM84881",
               "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", "BCM84881B0KFSBG",
               "400G PAM4 SerDes Retimer")
    for i in range(4):
        y = 10.16 - i * 3.81
        s.add("input", -15.24, y, 0, f"HRX_{i}P", f"A{2*i+1}")
        s.add("input", -15.24, y - 1.27, 0, f"HRX_{i}N", f"A{2*i+2}")
    for i in range(4):
        y = 10.16 - i * 3.81
        s.add("output", -15.24, y - 17.78, 0, f"HTX_{i}P", f"B{2*i+1}")
        s.add("output", -15.24, y - 19.05, 0, f"HTX_{i}N", f"B{2*i+2}")
    for i in range(4):
        y = 10.16 - i * 3.81
        s.add("output", 15.24, y, 180, f"LTX_{i}P", f"C{2*i+1}")
        s.add("output", 15.24, y - 1.27, 180, f"LTX_{i}N", f"C{2*i+2}")
    for i in range(4):
        y = 10.16 - i * 3.81
        s.add("input", 15.24, y - 17.78, 180, f"LRX_{i}P", f"D{2*i+1}")
        s.add("input", 15.24, y - 19.05, 180, f"LRX_{i}N", f"D{2*i+2}")
    s.add("input", 0, 17.78, 270, "REFCLK_P", "E1")
    s.add("input", 2.54, 17.78, 270, "REFCLK_N", "E2")
    s.add("bidirectional", -15.24, -30.48, 0, "MDIO_DATA", "F1")
    s.add("input", -15.24, -31.75, 0, "MDIO_CLK", "F2")
    s.add("power_in", -5.08, 17.78, 270, "VDD_0V9", "P1")
    s.add("power_in", -7.62, 17.78, 270, "VDD_1V8", "P2")
    s.add("power_in", 0, -35.56, 90, "GND", "P3")
    return s


def def_pex88096():
    s = SymDef("LightRail:PEX88096", "U", "PEX88096",
               "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", "PEX88096-CA80BI",
               "PCIe 5.0 96-lane Switch")
    for i in range(16):
        y = 25.4 - i * 2.54
        s.add("bidirectional", -17.78, y, 0, f"UP_LANE{i}", f"A{i+1}")
    for i in range(4):
        y = -5.08 - i * 5.08
        s.add("bidirectional", 17.78, y, 180, f"DN{i}_BUS", f"B{i+1}")
    s.add("input", 0, 30.48, 270, "REFCLK_P", "C1")
    s.add("input", 2.54, 30.48, 270, "REFCLK_N", "C2")
    s.add("bidirectional", -17.78, -25.4, 0, "SMBUS_DATA", "D1")
    s.add("input", -17.78, -26.67, 0, "SMBUS_CLK", "D2")
    s.add("power_in", -5.08, 30.48, 270, "VDD_0V9", "P1")
    s.add("power_in", -7.62, 30.48, 270, "VDD_1V8", "P2")
    s.add("power_in", 0, -30.48, 90, "GND", "P3")
    return s


def def_ast2600():
    s = SymDef("LightRail:AST2600", "U", "AST2600",
               "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm", "AST2600A3-T",
               "BMC System Management")
    s.add("bidirectional", -12.7, 10.16, 0, "I2C0_SDA", "1")
    s.add("output", -12.7, 8.89, 0, "I2C0_SCL", "2")
    s.add("bidirectional", -12.7, 6.35, 0, "I2C1_SDA", "3")
    s.add("bidirectional", -12.7, 5.08, 0, "I2C1_SCL", "4")
    s.add("output", -12.7, 2.54, 0, "SPI0_MOSI", "5")
    s.add("input", -12.7, 1.27, 0, "SPI0_MISO", "6")
    s.add("output", -12.7, 0, 0, "SPI0_SCK", "7")
    s.add("output", -12.7, -1.27, 0, "SPI0_CS0", "8")
    s.add("output", 12.7, 10.16, 180, "UART0_TX", "9")
    s.add("input", 12.7, 8.89, 180, "UART0_RX", "10")
    s.add("bidirectional", 12.7, 6.35, 180, "ETH0_TXD", "11")
    s.add("bidirectional", 12.7, 5.08, 180, "ETH0_RXD", "12")
    s.add("output", 12.7, 2.54, 180, "GPIO_0_7", "13")
    s.add("input", 12.7, 0, 180, "JTAG_TCK", "14")
    s.add("input", 12.7, -1.27, 180, "JTAG_TMS", "15")
    s.add("input", 12.7, -2.54, 180, "JTAG_TDI", "16")
    s.add("output", 12.7, -3.81, 180, "JTAG_TDO", "17")
    s.add("input", 0, 15.24, 270, "CLK_25MHZ", "18")
    s.add("input", -12.7, -5.08, 0, "RST_N", "19")
    s.add("power_in", -5.08, 15.24, 270, "VDD_1V8", "P1")
    s.add("power_in", -7.62, 15.24, 270, "VDD_3V3", "P2")
    s.add("power_in", 0, -10.16, 90, "GND", "P3")
    return s


def def_pcie_slot():
    s = SymDef("LightRail:PCIe_x16_SLOT", "J", "PCIe_x16_SLOT",
               "LightRail:PCIE_x16_SLOT", "2-2337939-3",
               "TE Gen5/6 164-pin PCIe x16 Slot")
    for i in range(16):
        y = 25.4 - i * 2.54
        s.add("bidirectional", -10.16, y, 0, f"PET{i}P", f"A{2*i+1}")
        s.add("bidirectional", -10.16, y - 1.27, 0, f"PET{i}N", f"A{2*i+2}")
    for i in range(16):
        y = 25.4 - i * 2.54
        s.add("bidirectional", 10.16, y, 180, f"PER{i}P", f"B{2*i+1}")
        s.add("bidirectional", 10.16, y - 1.27, 180, f"PER{i}N", f"B{2*i+2}")
    s.add("input", 0, 30.48, 270, "REFCLK_P", "C1")
    s.add("input", 2.54, 30.48, 270, "REFCLK_N", "C2")
    s.add("power_in", -5.08, 30.48, 270, "P12V", "D1")
    s.add("power_in", -7.62, 30.48, 270, "P3V3", "D2")
    s.add("power_in", 0, -20.32, 90, "GND", "D3")
    s.add("input", 5.08, 30.48, 270, "PRSNT_N", "E1")
    s.add("output", 7.62, 30.48, 270, "PERST_N", "E2")
    return s


# ── Passive & power lib symbols ─────────────────────────────────────────

LIB_CAP = """    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "C" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "Capacitor" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
        (pin passive line (at 0 -3.81 90) (length 2.794) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      )
    )"""

def lib_power(name):
    return f"""    (symbol "power:{name}" (power) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Value" "{name}" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "{name}_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "{name}_1_1"
        (pin power_in line (at 0 0 90) (length 0) (name "{name}" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""

LIB_PWR_FLAG = """    (symbol "power:PWR_FLAG" (power) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "#FLG" (at 0 1.905 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "PWR_FLAG_0_1"
        (pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""

LIB_GND = """    (symbol "power:GND" (power) (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0) (name "GND" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      )
    )"""


# ── Output helpers ───────────────────────────────────────────────────────

class SchWriter:
    def __init__(self):
        self.lines = []

    def w(self, s):
        self.lines.append(s)

    def place(self, symdef, ref, value, sx, sy, footprint=None, mpn=None, lib_id=None):
        fp = footprint or (symdef.footprint if symdef else "")
        mp = mpn or (symdef.mpn if symdef else "")
        lid = lib_id or (symdef.lib_name if symdef else "Device:C")
        u = uid()
        self.w(f'  (symbol (lib_id "{lid}") (at {sx} {sy} 0) (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes)')
        self.w(f'    (uuid "{u}")')
        self.w(f'    (property "Reference" "{ref}" (at {sx} {sy - 5} 0) (effects (font (size 1.27 1.27))))')
        self.w(f'    (property "Value" "{value}" (at {sx} {sy + 5} 0) (effects (font (size 1.27 1.27))))')
        if fp:
            self.w(f'    (property "Footprint" "{fp}" (at {sx} {sy + 2} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        self.w(f'    (property "Datasheet" "" (at {sx} {sy} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        if mp:
            self.w(f'    (property "MPN" "{mp}" (at {sx} {sy} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        self.w('  )')

    def wire(self, x1, y1, x2, y2):
        self.w(f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))')

    def label_at_pin(self, symdef, pin_name, sx, sy, net_name, is_global=False, shape="bidirectional"):
        """Place a label at the exact pin endpoint with a short wire stub."""
        p = symdef.pin(pin_name)
        gx, gy = p.global_pos(sx, sy)
        # Wire stub extends 5mm from pin in the pin's direction
        if p.angle == 0:
            wx, wy = gx - 5, gy
            la = 180
        elif p.angle == 180:
            wx, wy = gx + 5, gy
            la = 0
        elif p.angle == 270:
            wx, wy = gx, gy - 5
            la = 270
        else:  # 90
            wx, wy = gx, gy + 5
            la = 90
        self.wire(gx, gy, wx, wy)
        if is_global:
            self.w(f'  (global_label "{net_name}" (shape {shape}) (at {wx} {wy} {la}) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
        else:
            self.w(f'  (label "{net_name}" (at {wx} {wy} {la}) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    def no_connect(self, symdef, pin_name, sx, sy):
        p = symdef.pin(pin_name)
        gx, gy = p.global_pos(sx, sy)
        self.w(f'  (no_connect (at {gx} {gy}) (uuid "{uid()}"))')

    def no_connect_xy(self, gx, gy):
        self.w(f'  (no_connect (at {gx} {gy}) (uuid "{uid()}"))')

    def note(self, text, x, y, sz=2.54):
        self.w(f'  (text "{text}" (at {x} {y} 0) (effects (font (size {sz} {sz})) (justify left)))')

    def pwr_flag(self, net_name, x, y):
        """Place a PWR_FLAG + power symbol to mark a net as driven."""
        u = uid()
        self.w(f'  (symbol (lib_id "power:PWR_FLAG") (at {x} {y} 0) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes)')
        self.w(f'    (uuid "{u}")')
        self.w(f'    (property "Reference" "#FLG{uid()[:4]}" (at {x} {y - 3} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        self.w(f'    (property "Value" "PWR_FLAG" (at {x} {y - 5} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        self.w(f'    (property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        self.w(f'    (property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
        self.w('  )')
        # Connect to appropriate global label via wire stub
        self.wire(x, y, x, y + 5)
        self.w(f'  (global_label "{net_name}" (shape input) (at {x} {y + 5} 270) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    def result(self):
        return "\n".join(self.lines) + "\n"


# ── Main generation ──────────────────────────────────────────────────────

def generate():
    # Build symbol defs
    NCE = def_nce()
    HBM = def_hbm4()
    TFLN = def_tfln()
    HMC = def_hmc8410()
    ISL_VRM = def_isl69260()
    ISL_DRM = def_isl99390()
    ADP = def_adp7118()
    SI = def_si5395a()
    BCM = def_bcm84881()
    PEX = def_pex88096()
    AST = def_ast2600()
    PCIE = def_pcie_slot()

    w = SchWriter()

    w.w('(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")')
    w.w(f'  (uuid "{uid()}")')
    w.w('  (paper "A0")')
    w.w('  (title_block')
    w.w('    (title "LightRail NCE Gen3 - 86-Component Accelerator Board")')
    w.w('    (date "2026-06-23")')
    w.w('    (rev "7.0")')
    w.w('    (company "LightRail AI")')
    w.w('    (comment 1 "Dual NCE Gen3 | 16x HBM4-16GB | TFLN 400G Photonic I/O")')
    w.w('    (comment 2 "4x ISL69260 VRM | 24x ISL99390 DrMOS | 4x ADP7118 LDO")')
    w.w('    (comment 3 "2x Si5395A | 4x BCM84881 | 4x PEX88096 | AST2600 BMC")')
    w.w('    (comment 4 "4x PCIe x16 Slots | 16x 100nF Decoupling")')
    w.w('  )')

    # ── lib_symbols
    w.w('  (lib_symbols')
    w.w(NCE.lib_block())
    w.w(HBM.lib_block())
    w.w(TFLN.lib_block())
    w.w(HMC.lib_block())
    w.w(ISL_VRM.lib_block())
    w.w(ISL_DRM.lib_block())
    w.w(ADP.lib_block())
    w.w(SI.lib_block())
    w.w(BCM.lib_block())
    w.w(PEX.lib_block())
    w.w(AST.lib_block())
    w.w(PCIE.lib_block())
    w.w(LIB_CAP)
    w.w(LIB_GND)
    w.w(LIB_PWR_FLAG)
    for rail in ["+12V", "+3V3", "+1V8", "+0V9", "+0V8"]:
        w.w(lib_power(rail))
    w.w('  )')

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1: AI COMPUTE CORE
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 1: AI COMPUTE CORE - Dual NCE Gen3 Spiking Brain", 25, 30, 3.0)

    nce_positions = [(200, 180, "NCE0"), (550, 180, "NCE1")]
    for sx, sy, pfx in nce_positions:
        ref = "U1" if pfx == "NCE0" else "U4"
        w.place(NCE, ref, "NCE_Gen3_SpikingBrain", sx, sy)
        # RF TX outputs: only channels 0-3 on NCE0 go to HMC8410 drivers
        for i in range(8):
            if pfx == "NCE0" and i < 4:
                w.label_at_pin(NCE, f"RF_TX_{i}P", sx, sy, f"{pfx}_RF_TX_{i}P")
                w.label_at_pin(NCE, f"RF_TX_{i}N", sx, sy, f"{pfx}_RF_TX_{i}N")
            else:
                w.no_connect(NCE, f"RF_TX_{i}P", sx, sy)
                w.no_connect(NCE, f"RF_TX_{i}N", sx, sy)
        # PCIe outputs: 8 channels per NCE to retimers (4 retimers x 4 lanes)
        for i in range(16):
            if i < 8:
                w.label_at_pin(NCE, f"PCIE_TX{i}P", sx, sy, f"{pfx}_PCIE_{i}P")
                w.label_at_pin(NCE, f"PCIE_TX{i}N", sx, sy, f"{pfx}_PCIE_{i}N")
            else:
                w.no_connect(NCE, f"PCIE_TX{i}P", sx, sy)
                w.no_connect(NCE, f"PCIE_TX{i}N", sx, sy)
        # HBM channels: 8 per NCE (8 HBM modules each)
        for i in range(16):
            if i < 8:
                w.label_at_pin(NCE, f"HBM_CH{i}", sx, sy, f"{pfx}_HBM_CH{i}")
            else:
                w.no_connect(NCE, f"HBM_CH{i}", sx, sy)
        # HBM control
        w.label_at_pin(NCE, "HBM_REFCK_P", sx, sy, f"{pfx}_HBM_REFCK_P")
        w.label_at_pin(NCE, "HBM_REFCK_N", sx, sy, f"{pfx}_HBM_REFCK_N")
        w.label_at_pin(NCE, "HBM_CATTRIP", sx, sy, f"{pfx}_CATTRIP")
        w.label_at_pin(NCE, "HBM_PWR_GOOD", sx, sy, f"{pfx}_PWR_GOOD")
        # I2C
        w.label_at_pin(NCE, "I2C_SDA", sx, sy, "I2C_SDA", is_global=True)
        w.label_at_pin(NCE, "I2C_SCL", sx, sy, "I2C_SCL", is_global=True, shape="input")
        # SPI (BMC is master, NCE is slave) – only NCE0 connects to BMC SPI
        if pfx == "NCE0":
            w.label_at_pin(NCE, "SPI_MOSI", sx, sy, "SPI_MOSI", is_global=True, shape="input")
            w.label_at_pin(NCE, "SPI_MISO", sx, sy, "SPI_MISO", is_global=True, shape="output")
            w.label_at_pin(NCE, "SPI_SCK", sx, sy, "SPI_SCK", is_global=True, shape="input")
            w.label_at_pin(NCE, "SPI_CS", sx, sy, "SPI_CS", is_global=True, shape="input")
        else:
            for sp in ["SPI_MOSI", "SPI_MISO", "SPI_SCK", "SPI_CS"]:
                w.no_connect(NCE, sp, sx, sy)
        # TFLN clock – only NCE0 drives TFLN; NCE1 unused
        if pfx == "NCE0":
            w.label_at_pin(NCE, "TFLN_CLK_P", sx, sy, "TFLN_CLK_P")
            w.label_at_pin(NCE, "TFLN_CLK_N", sx, sy, "TFLN_CLK_N")
        else:
            w.no_connect(NCE, "TFLN_CLK_P", sx, sy)
            w.no_connect(NCE, "TFLN_CLK_N", sx, sy)
        # Power
        w.label_at_pin(NCE, "V_CORE", sx, sy, "+0V8", is_global=True, shape="input")
        w.label_at_pin(NCE, "VDD_IO", sx, sy, "+1V8", is_global=True, shape="input")
        w.label_at_pin(NCE, "VDDQ", sx, sy, "+1V8", is_global=True, shape="input")
        w.label_at_pin(NCE, "GND", sx, sy, "GND", is_global=True, shape="passive")

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2: HBM4 MEMORY ARRAY
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 2: HBM4 MEMORY - 16x 16GB 12-Hi (256GB total)", 25, 310, 3.0)

    for idx in range(16):
        col = idx % 8
        row = idx // 8
        sx = 100 + col * 80
        sy = 380 + row * 80
        pfx = "NCE0" if idx < 8 else "NCE1"
        ch = idx if idx < 8 else idx - 8
        w.place(HBM, f"U{30 + idx}", "HBM4-16GB", sx, sy)
        # Data channel to NCE
        w.label_at_pin(HBM, "DATA_CH", sx, sy, f"{pfx}_HBM_CH{ch}")
        w.label_at_pin(HBM, "VDDC", sx, sy, "+0V8", is_global=True, shape="input")
        w.label_at_pin(HBM, "VDDQL", sx, sy, "+0V8", is_global=True, shape="input")
        w.label_at_pin(HBM, "VDDQ", sx, sy, "+1V8", is_global=True, shape="input")
        w.label_at_pin(HBM, "VPP", sx, sy, "+1V8", is_global=True, shape="input")
        w.label_at_pin(HBM, "VSS", sx, sy, "GND", is_global=True, shape="passive")
        w.label_at_pin(HBM, "REFCK_P", sx, sy, f"{pfx}_HBM_REFCK_P")
        w.label_at_pin(HBM, "REFCK_N", sx, sy, f"{pfx}_HBM_REFCK_N")
        w.label_at_pin(HBM, "CATTRIP", sx, sy, f"{pfx}_CATTRIP")
        w.label_at_pin(HBM, "PWR_GOOD", sx, sy, f"{pfx}_PWR_GOOD")
        # IEEE1500 test – no connect for now
        for tp in ["IEEE1500_TCK", "IEEE1500_TMS", "IEEE1500_TDI", "IEEE1500_TDO"]:
            w.no_connect(HBM, tp, sx, sy)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3: PHOTONIC I/O
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 3: PHOTONIC I/O - TFLN 400G + HMC8410 RF Drivers", 25, 530, 3.0)

    tfln_x, tfln_y = 400, 600
    w.place(TFLN, "U3", "TFLN_PIC_4xMZM", tfln_x, tfln_y)
    for i in range(4):
        w.label_at_pin(TFLN, f"RF_IN_{i}P", tfln_x, tfln_y, f"TFLN_RF_{i}P")
        w.label_at_pin(TFLN, f"RF_IN_{i}N", tfln_x, tfln_y, f"TFLN_RF_{i}N")
        w.no_connect(TFLN, f"OPT_OUT_{i}", tfln_x, tfln_y)
        w.no_connect(TFLN, f"OPT_IN_{i}", tfln_x, tfln_y)
        w.label_at_pin(TFLN, f"VBIAS_{i}", tfln_x, tfln_y, f"TFLN_VBIAS_{i}")
    w.label_at_pin(TFLN, "CLK_P", tfln_x, tfln_y, "TFLN_CLK_P")
    w.label_at_pin(TFLN, "CLK_N", tfln_x, tfln_y, "TFLN_CLK_N")
    w.label_at_pin(TFLN, "VDD_1V8", tfln_x, tfln_y, "+1V8", is_global=True, shape="input")
    w.label_at_pin(TFLN, "VDD_3V3", tfln_x, tfln_y, "+3V3", is_global=True, shape="input")
    w.label_at_pin(TFLN, "GND", tfln_x, tfln_y, "GND", is_global=True, shape="passive")
    w.label_at_pin(TFLN, "SDA", tfln_x, tfln_y, "I2C_SDA", is_global=True)
    w.label_at_pin(TFLN, "SCL", tfln_x, tfln_y, "I2C_SCL", is_global=True, shape="input")

    # RF Drivers
    for i in range(4):
        sx = 100 + i * 100
        sy = 700
        w.place(HMC, f"U{50 + i}", "HMC8410", sx, sy)
        # Input from NCE0
        w.label_at_pin(HMC, "RF_INP", sx, sy, f"NCE0_RF_TX_{i}P")
        w.label_at_pin(HMC, "RF_INN", sx, sy, f"NCE0_RF_TX_{i}N")
        # Output to TFLN
        w.label_at_pin(HMC, "RF_OUTP", sx, sy, f"TFLN_RF_{i}P")
        w.label_at_pin(HMC, "RF_OUTN", sx, sy, f"TFLN_RF_{i}N")
        # Power
        w.label_at_pin(HMC, "VCC1", sx, sy, "+0V9", is_global=True, shape="input")
        w.label_at_pin(HMC, "VCC2", sx, sy, "+0V9", is_global=True, shape="input")
        w.label_at_pin(HMC, "GND", sx, sy, "GND", is_global=True, shape="passive")
        w.no_connect(HMC, "GAIN_ADJ", sx, sy)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4: POWER DELIVERY
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 4: POWER - VRM + DrMOS + LDO", 25, 780, 3.0)

    # VRM Controllers
    for i in range(4):
        sx = 100 + i * 180
        sy = 870
        w.place(ISL_VRM, f"U{200 + i}", "ISL69260", sx, sy)
        for ph in range(6):
            w.label_at_pin(ISL_VRM, f"PWM{ph}", sx, sy, f"VRM{i}_PWM{ph}")
        w.label_at_pin(ISL_VRM, "VCC", sx, sy, "+12V", is_global=True, shape="input")
        w.label_at_pin(ISL_VRM, "GND", sx, sy, "GND", is_global=True, shape="passive")
        w.label_at_pin(ISL_VRM, "SDA", sx, sy, "I2C_SDA", is_global=True)
        w.label_at_pin(ISL_VRM, "SCL", sx, sy, "I2C_SCL", is_global=True, shape="input")
        w.label_at_pin(ISL_VRM, "VSEN_P", sx, sy, "+0V8", is_global=True, shape="input")
        w.no_connect(ISL_VRM, "PGOOD", sx, sy)
        w.label_at_pin(ISL_VRM, "EN", sx, sy, "+3V3", is_global=True, shape="input")
        # VID pins – no connect
        for v in ["VID0", "VID1", "VID2", "VSEN_N"]:
            w.no_connect(ISL_VRM, v, sx, sy)

    # DrMOS stages
    for i in range(24):
        col = i % 6
        row = i // 6
        sx = 100 + col * 100
        sy = 1000 + row * 55
        vrm_idx = i // 6
        phase_idx = i % 6
        w.place(ISL_DRM, f"U{210 + i}", "ISL99390", sx, sy)
        w.label_at_pin(ISL_DRM, "PWM", sx, sy, f"VRM{vrm_idx}_PWM{phase_idx}")
        w.label_at_pin(ISL_DRM, "PVCC", sx, sy, "+12V", is_global=True, shape="input")
        w.label_at_pin(ISL_DRM, "PHASE", sx, sy, "+0V8", is_global=True, shape="output")
        w.label_at_pin(ISL_DRM, "PGND", sx, sy, "GND", is_global=True, shape="passive")
        w.no_connect(ISL_DRM, "DRVH", sx, sy)
        w.no_connect(ISL_DRM, "DRVL", sx, sy)
        w.no_connect(ISL_DRM, "IMON", sx, sy)
        w.no_connect(ISL_DRM, "BOOT", sx, sy)

    # LDOs
    for i in range(4):
        sx = 100 + i * 120
        sy = 1260
        w.place(ADP, f"U{240 + i}", "ADP7118-0.9V", sx, sy)
        w.label_at_pin(ADP, "IN", sx, sy, "+3V3", is_global=True, shape="input")
        w.label_at_pin(ADP, "EN", sx, sy, "+3V3", is_global=True, shape="input")
        w.label_at_pin(ADP, "OUT", sx, sy, f"TFLN_VBIAS_{i}")
        w.label_at_pin(ADP, "GND", sx, sy, "GND", is_global=True, shape="passive")
        w.no_connect(ADP, "NR_SS", sx, sy)

    # PWR_FLAG symbols for each power rail
    pwr_rails = ["+12V", "+3V3", "+1V8", "+0V9", "+0V8", "GND"]
    for idx, rail in enumerate(pwr_rails):
        w.pwr_flag(rail, 100 + idx * 40, 1320)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5: CLOCKING
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 5: CLOCKING - Si5395A Jitter Cleaners", 25, 1320, 3.0)

    for i in range(2):
        sx = 200 + i * 250
        sy = 1400
        w.place(SI, f"U{250 + i}", "Si5395A", sx, sy)
        w.label_at_pin(SI, "SDA", sx, sy, "I2C_SDA", is_global=True)
        w.label_at_pin(SI, "SCL", sx, sy, "I2C_SCL", is_global=True, shape="input")
        for out in range(4):
            w.label_at_pin(SI, f"OUT{out}P", sx, sy, f"CLK{i}_OUT{out}P")
            w.label_at_pin(SI, f"OUT{out}N", sx, sy, f"CLK{i}_OUT{out}N")
        w.label_at_pin(SI, "VDD", sx, sy, "+3V3", is_global=True, shape="input")
        w.label_at_pin(SI, "VDDA", sx, sy, "+3V3", is_global=True, shape="input")
        w.label_at_pin(SI, "GND", sx, sy, "GND", is_global=True, shape="passive")
        # Clock inputs/crystal – no connect for now
        for nc in ["IN0P", "IN0N", "IN1P", "IN1N", "XA", "XB", "RST"]:
            w.no_connect(SI, nc, sx, sy)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6: HIGH-SPEED I/O
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 6: HIGH-SPEED I/O - Retimers + PCIe Switches + Slots", 25, 1490, 3.0)

    # BCM84881 Retimers
    for i in range(4):
        sx = 100 + i * 180
        sy = 1580
        pfx = "NCE0" if i < 2 else "NCE1"
        pcie_base = (i % 2) * 4
        w.place(BCM, f"U{260 + i}", "BCM84881", sx, sy)
        for lane in range(4):
            w.label_at_pin(BCM, f"HRX_{lane}P", sx, sy, f"{pfx}_PCIE_{pcie_base + lane}P")
            w.label_at_pin(BCM, f"HRX_{lane}N", sx, sy, f"{pfx}_PCIE_{pcie_base + lane}N")
            w.label_at_pin(BCM, f"LTX_{lane}P", sx, sy, f"RETIMER{i}_TX{lane}P")
            w.no_connect(BCM, f"LTX_{lane}N", sx, sy)
        # HTX/LRX – no connect (simplex connection model)
        for lane in range(4):
            w.no_connect(BCM, f"HTX_{lane}P", sx, sy)
            w.no_connect(BCM, f"HTX_{lane}N", sx, sy)
            w.no_connect(BCM, f"LRX_{lane}P", sx, sy)
            w.no_connect(BCM, f"LRX_{lane}N", sx, sy)
        w.label_at_pin(BCM, "REFCLK_P", sx, sy, f"CLK{i // 2}_OUT{i % 2}P")
        w.label_at_pin(BCM, "REFCLK_N", sx, sy, f"CLK{i // 2}_OUT{i % 2}N")
        w.label_at_pin(BCM, "VDD_0V9", sx, sy, "+0V9", is_global=True, shape="input")
        w.label_at_pin(BCM, "VDD_1V8", sx, sy, "+1V8", is_global=True, shape="input")
        w.label_at_pin(BCM, "GND", sx, sy, "GND", is_global=True, shape="passive")
        w.no_connect(BCM, "MDIO_DATA", sx, sy)
        w.no_connect(BCM, "MDIO_CLK", sx, sy)

    # PEX88096 PCIe Switches
    for i in range(4):
        sx = 100 + i * 180
        sy = 1790
        w.place(PEX, f"U{270 + i}", "PEX88096", sx, sy)
        # Connect upstream lanes from retimers
        for lane in range(4):
            w.label_at_pin(PEX, f"UP_LANE{lane}", sx, sy, f"RETIMER{i}_TX{lane}P")
        # N-side labels not needed (PEX uses single-ended bus labels)
        for lane in range(4, 16):
            w.no_connect(PEX, f"UP_LANE{lane}", sx, sy)
        # Downstream: only DN0 connects to PCIe slot, rest no-connect for now
        w.label_at_pin(PEX, "DN0_BUS", sx, sy, f"PCIESW{i}_DN0")
        for dn in range(1, 4):
            w.no_connect(PEX, f"DN{dn}_BUS", sx, sy)
        w.label_at_pin(PEX, "REFCLK_P", sx, sy, f"CLK{i // 2}_OUT{(i % 2) + 2}P")
        w.label_at_pin(PEX, "REFCLK_N", sx, sy, f"CLK{i // 2}_OUT{(i % 2) + 2}N")
        w.label_at_pin(PEX, "SMBUS_DATA", sx, sy, "I2C_SDA", is_global=True)
        w.label_at_pin(PEX, "SMBUS_CLK", sx, sy, "I2C_SCL", is_global=True, shape="input")
        w.label_at_pin(PEX, "VDD_0V9", sx, sy, "+0V9", is_global=True, shape="input")
        w.label_at_pin(PEX, "VDD_1V8", sx, sy, "+1V8", is_global=True, shape="input")
        w.label_at_pin(PEX, "GND", sx, sy, "GND", is_global=True, shape="passive")

    # PCIe Slots
    for i in range(4):
        sx = 100 + i * 180
        sy = 2020
        w.place(PCIE, f"J{20 + i}", "PCIe_x16_SLOT", sx, sy)
        # Connect first lane pair from PCIe switch
        w.label_at_pin(PCIE, "PET0P", sx, sy, f"PCIESW{i}_DN0")
        for lane in range(1, 16):
            w.no_connect(PCIE, f"PET{lane}P", sx, sy)
            w.no_connect(PCIE, f"PET{lane}N", sx, sy)
        w.no_connect(PCIE, "PET0N", sx, sy)
        for lane in range(16):
            w.no_connect(PCIE, f"PER{lane}P", sx, sy)
            w.no_connect(PCIE, f"PER{lane}N", sx, sy)
        w.no_connect(PCIE, "REFCLK_P", sx, sy)
        w.no_connect(PCIE, "REFCLK_N", sx, sy)
        w.label_at_pin(PCIE, "P12V", sx, sy, "+12V", is_global=True, shape="input")
        w.label_at_pin(PCIE, "P3V3", sx, sy, "+3V3", is_global=True, shape="input")
        w.label_at_pin(PCIE, "GND", sx, sy, "GND", is_global=True, shape="passive")
        w.no_connect(PCIE, "PRSNT_N", sx, sy)
        w.no_connect(PCIE, "PERST_N", sx, sy)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 7: SYSTEM MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════
    w.note("SECTION 7: SYSTEM MANAGEMENT - BMC + Decoupling", 25, 2100, 3.0)

    bmc_x, bmc_y = 200, 2170
    w.place(AST, "U380", "AST2600", bmc_x, bmc_y)
    w.label_at_pin(AST, "I2C0_SDA", bmc_x, bmc_y, "I2C_SDA", is_global=True)
    w.label_at_pin(AST, "I2C0_SCL", bmc_x, bmc_y, "I2C_SCL", is_global=True, shape="input")
    w.label_at_pin(AST, "I2C1_SDA", bmc_x, bmc_y, "I2C_SDA", is_global=True)
    w.label_at_pin(AST, "I2C1_SCL", bmc_x, bmc_y, "I2C_SCL", is_global=True, shape="input")
    w.label_at_pin(AST, "SPI0_MOSI", bmc_x, bmc_y, "SPI_MOSI", is_global=True, shape="output")
    w.label_at_pin(AST, "SPI0_MISO", bmc_x, bmc_y, "SPI_MISO", is_global=True, shape="input")
    w.label_at_pin(AST, "SPI0_SCK", bmc_x, bmc_y, "SPI_SCK", is_global=True, shape="output")
    w.label_at_pin(AST, "SPI0_CS0", bmc_x, bmc_y, "SPI_CS", is_global=True, shape="output")
    w.label_at_pin(AST, "VDD_1V8", bmc_x, bmc_y, "+1V8", is_global=True, shape="input")
    w.label_at_pin(AST, "VDD_3V3", bmc_x, bmc_y, "+3V3", is_global=True, shape="input")
    w.label_at_pin(AST, "GND", bmc_x, bmc_y, "GND", is_global=True, shape="passive")
    # Unconnected BMC pins
    for nc in ["UART0_TX", "UART0_RX", "ETH0_TXD", "ETH0_RXD", "GPIO_0_7",
               "JTAG_TCK", "JTAG_TMS", "JTAG_TDI", "JTAG_TDO", "CLK_25MHZ", "RST_N"]:
        w.no_connect(AST, nc, bmc_x, bmc_y)

    # Decoupling caps
    # Device:C has pins at (0, 3.81, 270) and (0, -3.81, 90) so
    # global: pin1 at (sx, sy - 3.81), pin2 at (sx, sy + 3.81)
    cap_pins_p1 = Pin("passive", 0, 3.81, 270, "~", "1")
    cap_pins_p2 = Pin("passive", 0, -3.81, 90, "~", "2")
    rails = ["+0V8"]*4 + ["+1V8"]*4 + ["+3V3"]*4 + ["+0V9"]*4
    for i in range(16):
        col = i % 8
        row = i // 8
        sx = 80 + col * 60
        sy = 2260 + row * 30
        w.place(None, f"C{i + 1}", "100nF", sx, sy,
                footprint="Capacitor_SMD:C_0402_1005Metric", mpn="GRM155R71C104KA88")
        # Pin 1 (positive)
        gx1, gy1 = cap_pins_p1.global_pos(sx, sy)
        w.wire(gx1, gy1, gx1, gy1 - 5)
        w.w(f'  (global_label "{rails[i]}" (shape input) (at {gx1} {gy1 - 5} 90) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
        # Pin 2 (GND)
        gx2, gy2 = cap_pins_p2.global_pos(sx, sy)
        w.wire(gx2, gy2, gx2, gy2 + 5)
        w.w(f'  (global_label "GND" (shape passive) (at {gx2} {gy2 + 5} 270) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    w.note(
        "BOARD: 1.6Tbps BW | 256GB HBM4 | 4x24ph VRM 1000A@0.8V | 32L HDI Megtron-7 | 86 components",
        25, 2340, 2.0)

    w.w(')')
    return w.result()


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo, "NCE_Gen3_82comp.kicad_sch")
    content = generate()
    with open(path, 'w') as f:
        f.write(content)
    n = content.count('(lib_id ')
    wires = content.count('(wire ')
    labels = content.count('(label ')
    glabels = content.count('(global_label ')
    ncs = content.count('(no_connect ')
    print(f"Generated {path}")
    print(f"Components: {n}  Wires: {wires}  Labels: {labels}  Global labels: {glabels}  No-connects: {ncs}")


if __name__ == "__main__":
    main()

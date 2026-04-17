#!/usr/bin/env python3
"""Generate pinout CSVs under docs/ for the LightRail AI Compute Node."""
from __future__ import annotations
import csv
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
DOCS.mkdir(exist_ok=True)


def write_csv(name: str, header: list[str], rows: list[list]):
    path = DOCS / name
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"Wrote {path}  ({len(rows)} rows)")


# -------- PCIe Gen 6 x16 edge (CEM 6.0) --------
# Side B (top), A (bottom). 82 pins per side.
# For brevity, focus on the canonical signals; TX/RX pairs filled programmatically.
pcie_rows = []
# Fixed B-side pins
pcie_rows.extend([
    ["B1",  "+12V",     "power",  "Main 12V rail",         "PWR_12V"],
    ["B2",  "+12V",     "power",  "Main 12V rail",         "PWR_12V"],
    ["B3",  "+12V",     "power",  "Main 12V rail",         "PWR_12V"],
    ["B4",  "GND",      "power",  "Return",                "GND"],
    ["B5",  "SMCLK",    "i/o",    "SMBus clock",           "I2C_SPI"],
    ["B6",  "SMDAT",    "i/o",    "SMBus data",            "I2C_SPI"],
    ["B7",  "GND",      "power",  "Return",                "GND"],
    ["B8",  "+3.3V",    "power",  "3.3V aux",              "PWR_3V3"],
    ["B9",  "TRST#",    "in",     "JTAG reset",            "I2C_SPI"],
    ["B10", "3.3Vaux",  "power",  "3.3V always-on",        "PWR_3V3"],
    ["B11", "WAKE#",    "o_oc",   "Wake request",          "I2C_SPI"],
    ["B12", "RSVD",     "nc",     "Reserved",              "-"],
    ["B13", "GND",      "power",  "Return",                "GND"],
    ["B14", "PET0_P",   "out",    "TX lane 0 +",           "PCIe_Gen6"],
    ["B15", "PET0_N",   "out",    "TX lane 0 −",           "PCIe_Gen6"],
    ["B16", "GND",      "power",  "Return",                "GND"],
    ["B17", "PRSNT#2",  "in",     "Presence detect 2",     "I2C_SPI"],
    ["B18", "GND",      "power",  "Return",                "GND"],
])
# B19 onwards: TX1..TX15 pairs (each occupies 3 pins: P, N, GND)
# Simpler canonical layout: every 3rd pin is GND, followed by TX_P / TX_N
# Actual CEM has specific GND interleaving; we document conceptually.
next_pin = 19
for lane in range(1, 16):
    pcie_rows.append([f"B{next_pin}",  f"PET{lane}_P", "out", f"TX lane {lane} +", "PCIe_Gen6"])
    pcie_rows.append([f"B{next_pin+1}", f"PET{lane}_N", "out", f"TX lane {lane} −", "PCIe_Gen6"])
    pcie_rows.append([f"B{next_pin+2}", "GND", "power", "Return", "GND"])
    next_pin += 3
# pad remaining pins to B82
while next_pin <= 82:
    pcie_rows.append([f"B{next_pin}", "RSVD", "nc", "Reserved", "-"])
    next_pin += 1

# A-side fixed
pcie_rows.extend([
    ["A1",  "PRSNT#1",  "in",     "Presence detect 1",     "I2C_SPI"],
    ["A2",  "+12V",     "power",  "Main 12V rail",         "PWR_12V"],
    ["A3",  "+12V",     "power",  "Main 12V rail",         "PWR_12V"],
    ["A4",  "GND",      "power",  "Return",                "GND"],
    ["A5",  "TCK",      "in",     "JTAG clock",            "I2C_SPI"],
    ["A6",  "TDI",      "in",     "JTAG data-in",          "I2C_SPI"],
    ["A7",  "TDO",      "out",    "JTAG data-out",         "I2C_SPI"],
    ["A8",  "TMS",      "in",     "JTAG mode select",      "I2C_SPI"],
    ["A9",  "+3.3V",    "power",  "3.3V",                  "PWR_3V3"],
    ["A10", "+3.3V",    "power",  "3.3V",                  "PWR_3V3"],
    ["A11", "PERST#",   "in",     "Fundamental reset",     "I2C_SPI"],
    ["A12", "GND",      "power",  "Return",                "GND"],
    ["A13", "REFCLK+",  "in",     "100 MHz ref clock +",   "RF_50OHM_DIFF"],
    ["A14", "REFCLK-",  "in",     "100 MHz ref clock −",   "RF_50OHM_DIFF"],
    ["A15", "GND",      "power",  "Return",                "GND"],
    ["A16", "PER0_P",   "in",     "RX lane 0 +",           "PCIe_Gen6"],
    ["A17", "PER0_N",   "in",     "RX lane 0 −",           "PCIe_Gen6"],
    ["A18", "GND",      "power",  "Return",                "GND"],
])
next_pin = 19
for lane in range(1, 16):
    pcie_rows.append([f"A{next_pin}",  f"PER{lane}_P", "in", f"RX lane {lane} +", "PCIe_Gen6"])
    pcie_rows.append([f"A{next_pin+1}", f"PER{lane}_N", "in", f"RX lane {lane} −", "PCIe_Gen6"])
    pcie_rows.append([f"A{next_pin+2}", "GND", "power", "Return", "GND"])
    next_pin += 3
while next_pin <= 82:
    pcie_rows.append([f"A{next_pin}", "RSVD", "nc", "Reserved", "-"])
    next_pin += 1

write_csv("pinout_PCIe_x16.csv",
          ["Pin", "Signal", "Direction", "Description", "NetClass"],
          pcie_rows)


# -------- AI SoC BGA-2500 (50x50, 0.8mm pitch) --------
# Full map would be 2500 rows. Emit grouped summary rows (domain + ball ranges)
# plus every 100th ball explicit for illustration.
soc_rows = []
domains = [
    ("V_CORE",    "N10..AK38",  612, "V_CORE_U{unit}",        "PWR_CORE"),
    ("GND",       "distributed", 624, "GND",                  "GND"),
    ("VDD_IO",    "rings",       96,  "VDD_IO",               "PWR_1V8"),
    ("VDDQ_DDR5", "east",        80,  "VDDQ",                 "PWR_1V8"),
    ("VPP_DDR5",  "east",        16,  "VPP",                  "PWR_1V8"),
    ("DDR5_Ch0",  "NE quad",    160, "DDR5_CH0_*",           "DDR5_Data"),
    ("DDR5_Ch1",  "SE quad",    160, "DDR5_CH1_*",           "DDR5_Data"),
    ("DDR5_Ch2",  "NW quad",    160, "DDR5_CH2_*",           "DDR5_Data"),
    ("DDR5_Ch3",  "SW quad",    160, "DDR5_CH3_*",           "DDR5_Data"),
    ("PCIe_x16_0","S edge",     72,  "PET0_*/PER0_*",        "PCIe_Gen6"),
    ("PCIe_x16_1","S edge",     72,  "PET1_*/PER1_*",        "PCIe_Gen6"),
    ("TFLN_SerDes 16ch","N edge",96, "TFLN_TX*/TFLN_RX*",    "TFLN_RF"),
    ("Mgmt",      "NW corner",  32,  "I2C/SPI/JTAG",         "I2C_SPI"),
    ("Thermal",   "center",      4,  "TDIODE_P/N",           "-"),
    ("Reserved",  "distributed",156, "RSVD",                 "-"),
]
for name, loc, cnt, netname, nc in domains:
    soc_rows.append([name, loc, cnt, netname, nc])
write_csv("pinout_SoC_BGA2500.csv",
          ["Domain", "Ball-Grid Location", "Count", "Representative Net", "NetClass"],
          soc_rows)


# -------- TFLN PIC periphery pinout --------
tfln_rows = []
for ch in range(8):
    tfln_rows.append([f"RF{ch}_P", "in",  f"RF drive channel {ch}, + side", "TFLN_RF"])
    tfln_rows.append([f"RF{ch}_N", "in",  f"RF drive channel {ch}, − side", "TFLN_RF"])
    tfln_rows.append([f"BIAS{ch}", "in",  f"DC bias tune channel {ch} (0-5V)", "I2C_SPI"])
    tfln_rows.append([f"PD{ch}_MON", "out", f"Tap photodiode monitor channel {ch}", "I2C_SPI"])
tfln_rows.extend([
    ["TEC_TH_A", "i/o", "TEC thermistor A", "I2C_SPI"],
    ["TEC_TH_B", "i/o", "TEC drive B",       "I2C_SPI"],
    ["VCC_RF",   "power", "RF analog supply 0.9V or 1.2V", "PWR_1V8"],
    ["VCC_BIAS", "power", "Bias supply (5V)", "PWR_3V3"],
    ["GND",      "power", "Analog / RF ground (≥40 pins)", "GND"],
])
# Fiber I/O
for f in range(1, 25):
    tfln_rows.append([f"FIBER{f:02d}", "optical",
                      f"Fiber {f}: {'TX' if f<=8 else 'RX' if f<=16 else 'MON'}",
                      "-"])
write_csv("pinout_TFLN_PIC.csv",
          ["Pin", "Direction", "Description", "NetClass"],
          tfln_rows)


# -------- DDR5 DIMM 288-pin summary --------
ddr5_rows = []
# Byte lanes 0..7
for byte in range(8):
    for bit in range(8):
        ddr5_rows.append([f"DQ{byte*8+bit}", "i/o", f"Data byte {byte} bit {bit}", "DDR5_Data"])
    ddr5_rows.append([f"DQS{byte}_t", "i/o", f"Byte {byte} strobe +", "DDR5_Data"])
    ddr5_rows.append([f"DQS{byte}_c", "i/o", f"Byte {byte} strobe −", "DDR5_Data"])
    ddr5_rows.append([f"DM{byte}",   "in",  f"Byte {byte} data mask", "DDR5_Data"])
# Command / address
for i in range(14):
    ddr5_rows.append([f"CA{i}", "in", f"Command/address {i}", "DDR5_Data"])
ddr5_rows.extend([
    ["CK_t",    "in",    "Clock +",              "DDR5_Data"],
    ["CK_c",    "in",    "Clock −",              "DDR5_Data"],
    ["CS0#",    "in",    "Chip select rank 0",   "DDR5_Data"],
    ["CS1#",    "in",    "Chip select rank 1",   "DDR5_Data"],
    ["ODT0",    "in",    "On-die termination 0", "DDR5_Data"],
    ["ODT1",    "in",    "On-die termination 1", "DDR5_Data"],
    ["RESET#",  "in",    "Reset",                "I2C_SPI"],
    ["ALERT#",  "o_oc",  "Alert",                "I2C_SPI"],
    ["EVENT#",  "o_oc",  "Event",                "I2C_SPI"],
])
# SPD + PMIC
for p in ["SA0", "SA1", "SA2", "SDA", "SCL", "WP"]:
    ddr5_rows.append([p, "i/o", f"SPD {p}", "I2C_SPI"])
# Power
ddr5_rows.append(["VDDQ",  "power", "DDR5 VDDQ (1.1V, ~32 pins)",  "PWR_1V8"])
ddr5_rows.append(["VPP",   "power", "DDR5 VPP  (1.8V, ~4 pins)",   "PWR_1V8"])
ddr5_rows.append(["VDD",   "power", "DDR5 VDD  (1.1V)",            "PWR_1V8"])
ddr5_rows.append(["GND",   "power", "Return (≥80 pins)",            "GND"])
write_csv("pinout_DDR5_DIMM.csv",
          ["Signal", "Direction", "Description", "NetClass"],
          ddr5_rows)


# -------- NVMe M.2 Key-M --------
# M.2 Key-M has 75 pins
nvme_rows = []
mappings = {
    1: ("GND",        "power",  "Ground"),
    2: ("+3.3V",      "power",  "3.3V main"),
    3: ("GND",        "power",  "Ground"),
    4: ("+3.3V",      "power",  "3.3V main"),
    5: ("PETn3",      "out",    "PCIe TX lane 3 −"),
    6: ("+3.3V",      "power",  "3.3V main"),
    7: ("PETp3",      "out",    "PCIe TX lane 3 +"),
    8: ("RSVD",       "nc",     "Reserved"),
    9: ("GND",        "power",  "Ground"),
    10: ("LED_DAS",    "o_oc",   "Drive Activity Status LED"),
    11: ("PERn3",      "in",     "PCIe RX lane 3 −"),
    12: ("+3.3V",      "power",  "3.3V main"),
    13: ("PERp3",      "in",     "PCIe RX lane 3 +"),
    14: ("+3.3V",      "power",  "3.3V main"),
    15: ("GND",        "power",  "Ground"),
    16: ("+3.3V",      "power",  "3.3V main"),
    17: ("PETn2",      "out",    "PCIe TX lane 2 −"),
    18: ("+3.3V",      "power",  "3.3V main"),
    19: ("PETp2",      "out",    "PCIe TX lane 2 +"),
    20: ("RSVD",       "nc",     "Reserved"),
    21: ("GND",        "power",  "Ground"),
    22: ("RSVD",       "nc",     "Reserved"),
    23: ("PERn2",      "in",     "PCIe RX lane 2 −"),
    24: ("RSVD",       "nc",     "Reserved"),
    25: ("PERp2",      "in",     "PCIe RX lane 2 +"),
    26: ("RSVD",       "nc",     "Reserved"),
    27: ("GND",        "power",  "Ground"),
    28: ("RSVD",       "nc",     "Reserved"),
    29: ("PETn1",      "out",    "PCIe TX lane 1 −"),
    30: ("RSVD",       "nc",     "Reserved"),
    31: ("PETp1",      "out",    "PCIe TX lane 1 +"),
    32: ("RSVD",       "nc",     "Reserved"),
    33: ("GND",        "power",  "Ground"),
    34: ("RSVD",       "nc",     "Reserved"),
    35: ("PERn1",      "in",     "PCIe RX lane 1 −"),
    36: ("RSVD",       "nc",     "Reserved"),
    37: ("PERp1",      "in",     "PCIe RX lane 1 +"),
    38: ("DEVSLP",     "in",     "Device sleep"),
    39: ("GND",        "power",  "Ground"),
    40: ("SMB_CLK",    "i/o",    "SMBus clock"),
    41: ("PETn0",      "out",    "PCIe TX lane 0 −"),
    42: ("SMB_DATA",   "i/o",    "SMBus data"),
    43: ("PETp0",      "out",    "PCIe TX lane 0 +"),
    44: ("ALERT#",     "o_oc",   "SMBus alert"),
    45: ("GND",        "power",  "Ground"),
    46: ("DPWRDIS",    "in",     "Dual port disable"),
    47: ("PERn0",      "in",     "PCIe RX lane 0 −"),
    48: ("DPWREN",     "out",    "Dual port enable"),
    49: ("PERp0",      "in",     "PCIe RX lane 0 +"),
    50: ("PERST#",     "out",    "PCIe reset"),
    51: ("GND",        "power",  "Ground"),
    52: ("CLKREQ#",    "o_oc",   "Clock request"),
    53: ("REFCLKn",    "in",     "100 MHz ref clock −"),
    54: ("PEWAKE#",    "o_oc",   "PCIe wake"),
    55: ("REFCLKp",    "in",     "100 MHz ref clock +"),
    56: ("RSVD",       "nc",     "Reserved"),
    57: ("GND",        "power",  "Ground"),
    58: ("RSVD",       "nc",     "Reserved"),
    # 59..66 are the Key-M notch (Key)
    67: ("RSVD",       "nc",     "Reserved"),
    68: ("SUSCLK",     "in",     "Suspend clock"),
    69: ("PEDET",      "o_oc",   "PCIe detect"),
    70: ("+3.3V",      "power",  "3.3V main"),
    71: ("GND",        "power",  "Ground"),
    72: ("+3.3V",      "power",  "3.3V main"),
    73: ("GND",        "power",  "Ground"),
    74: ("+3.3V",      "power",  "3.3V main"),
    75: ("GND",        "power",  "Ground"),
}
for p in range(1, 76):
    if p in mappings:
        sig, dirn, desc = mappings[p]
    else:
        sig, dirn, desc = ("KEY", "nc", "Key-M notch")
    nc = {
        "PETp3": "PCIe_Gen6", "PETn3": "PCIe_Gen6", "PERp3": "PCIe_Gen6", "PERn3": "PCIe_Gen6",
        "PETp2": "PCIe_Gen6", "PETn2": "PCIe_Gen6", "PERp2": "PCIe_Gen6", "PERn2": "PCIe_Gen6",
        "PETp1": "PCIe_Gen6", "PETn1": "PCIe_Gen6", "PERp1": "PCIe_Gen6", "PERn1": "PCIe_Gen6",
        "PETp0": "PCIe_Gen6", "PETn0": "PCIe_Gen6", "PERp0": "PCIe_Gen6", "PERn0": "PCIe_Gen6",
        "REFCLKp": "RF_50OHM_DIFF", "REFCLKn": "RF_50OHM_DIFF",
        "+3.3V": "PWR_3V3", "GND": "GND",
    }.get(sig, "I2C_SPI")
    nvme_rows.append([p, sig, dirn, desc, nc])
write_csv("pinout_NVMe_M2.csv",
          ["Pin", "Signal", "Direction", "Description", "NetClass"],
          nvme_rows)

print("All pinout CSVs generated.")

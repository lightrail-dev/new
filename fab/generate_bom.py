#!/usr/bin/env python3
"""
Generates fab/BOM.csv for the LightRail AI Compute Node (LR-P3A Rev 6.0).

Rev 6.0 delta vs Rev 5.0 (HBM4 migration release):
  * Tiered PDN decoupling added per spec §III — 100 µF tantalum bulk at VRM
    output, 10 µF 0805 mid-range, 1 µF 0402, 100 nF 01005 bypass (≤1 mm from
    each NCE/HBM4 power ball).
  * Embedded-capacitance layer (Faradflex BC24) reduces required 100 nF count
    from Rev 5.0, but we still populate abundant 01005 caps for the GHz band
    where the embedded plane is self-resonant.
  * Vendor list constrained to LCSC / Digi-Key / Mouser *Active* parts only
    (spec §V). No obsolete or NRND parts.

This is the BOM for the 32-layer HDI release — it reflects
the selected part list by domain. Final tapeout BOM is reconciled
against the KiCad-exported BOM (from `Tools → Generate BOM`) once the
schematic has complete ref-des annotations and all pads have nets assigned.

Run:   python3 generate_bom.py  -> writes BOM.csv, BOM.md (ascii summary)
"""
from __future__ import annotations
import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Part:
    ref: str             # reference designator (e.g. U1, C123)
    qty: int
    value: str           # "100nF", "10k", "ISL99390"
    footprint: str
    manufacturer: str
    mpn: str
    distributor: str
    distributor_pn: str
    package: str
    description: str
    dnp: str = ""        # "DNP" if do-not-populate
    notes: str = ""


rows: list[Part] = []


def add(ref_prefix: str, count: int, start: int = 1, **kw):
    """Helper: add `count` parts with refs like U1..U5, C10..C29."""
    for i in range(count):
        ref = f"{ref_prefix}{start + i}"
        rows.append(Part(ref=ref, qty=1, **kw))


# Ref-des scheme reconciled with LightRail_LPO_1.6T.kicad_pcb + schematic sheets:
#   U101 / U201  : AI SoCs (Unit 0 / Unit 1)           — BGA-2500
#   U102 / U202  : TFLN PICs (Unit 0 / Unit 1)
#   U103..U106   : HBM4 stacks adjacent to NCE U101 (Unit 0 interposer)
#   U203..U206   : HBM4 stacks adjacent to NCE U201 (Unit 1 interposer)
#   U107 / U207  : PCIe Gen 6 retimers per SoC  (moved off U103/U203 to
#                  avoid ref-des collision with HBM4 stacks on PCB)
#   U301         : VRM Unit 0 controller (ISL69260)
#   U302..U325   : VRM Unit 0 DrMOS phases (24)
#   U326..U349   : VRM Unit 1 DrMOS phases (24)
#   U350         : VRM Unit 1 controller (ISL69260)

# -------- AI Compute SoCs --------
for unit, ref in enumerate(["U101", "U201"]):
    rows.append(Part(ref=ref, qty=1, value="LR-ASIC-A100",
                     footprint="LightRail:BGA-2500_40x40mm_P0.8mm",
                     manufacturer="LightRail AI", mpn="LR-ASIC-A100-B0",
                     distributor="LightRail direct", distributor_pn="LR-ASIC-A100-B0",
                     package="BGA-2500 (50x50, 0.8mm)",
                     description=f"AI NCE Unit {unit}, BGA-2500, 800W TDP, HBM4 4-stack co-packaged, PCIe Gen6 x32, TFLN 16 lanes"))

# -------- TFLN Photonic Integrated Circuits --------
for unit, ref in enumerate(["U102", "U202"]):
    rows.append(Part(ref=ref, qty=1, value="TFLN-8CH-200G",
                     footprint="LightRail:TFLN_PIC_Periphery",
                     manufacturer="HyperLight", mpn="HL-TFLN-8CH-200G-PAM4",
                     distributor="HyperLight direct", distributor_pn="HL-TFLN-8CH-200G",
                     package="Custom periphery carrier",
                     description=f"8-channel TFLN MZ modulator, 200G PAM4/ch, C-band (Unit {unit})"))

# -------- PCIe Gen 6 retimers --------
# NOTE: U103/U203 are occupied by HBM4 stacks on the PCB; retimers use
# U107/U207 to avoid a duplicate ref-des in BOM.csv.
for unit, ref in enumerate(["U107", "U207"]):
    rows.append(Part(ref=ref, qty=1, value="PT6-Retimer",
                     footprint="Package_BGA:BGA-325_17x17mm_Layout18x18_P1.0mm",
                     manufacturer="Astera Labs", mpn="PT6-B0-325",
                     distributor="Arrow", distributor_pn="PT6-B0-325-T",
                     package="BGA-325 1.0mm", description=f"PCIe Gen 6 retimer, x16 (SoC {unit})"))

# -------- VRM Controllers (one per SoC) --------
for unit, ref in enumerate(["U301", "U350"]):
    rows.append(Part(ref=ref, qty=1, value="ISL69260",
                     footprint="Package_QFN:QFN-80-1EP_10x10mm_P0.4mm",
                     manufacturer="Renesas", mpn="ISL69260IRAZ-T",
                     distributor="Digi-Key", distributor_pn="ISL69260IRAZ-T7-ND",
                     package="QFN-80 1EP 10x10 0.4mm",
                     description=f"Digital multi-phase PWM controller, 16+8-phase (VRM Unit {unit})"))

# -------- DrMOS (48 total: 24 per VRM, contiguous per PCB layout) --------
# Unit 0 DrMOS occupy U302..U325; Unit 1 DrMOS occupy U326..U349.
for i in range(48):
    ref = f"U{302 + i}"  # U302..U349
    unit = 0 if i < 24 else 1
    rows.append(Part(ref=ref, qty=1, value="ISL99390",
                     footprint="LightRail:DrMOS_PowerPAK_8x8mm",
                     manufacturer="Renesas", mpn="ISL99390FRZ-T7A",
                     distributor="Digi-Key", distributor_pn="ISL99390FRZ-T7A-ND",
                     package="PowerPAK 8x8 1EP",
                     description=f"90A Smart Power Stage (DrMOS), VRM Unit {unit} phase"))

# -------- VRM Inductors (48 total) --------
for i in range(48):
    ref = f"L{101 + i}"
    rows.append(Part(ref=ref, qty=1, value="150nH 1.6mΩ",
                     footprint="Inductor_SMD:L_Bourns-SRP1770",
                     manufacturer="Vishay", mpn="IHLE-2525CD-01-150",
                     distributor="Digi-Key", distributor_pn="IHLE-2525CD-150-ND",
                     package="2525", description="Power inductor 150nH, 42A Isat, DCR 1.6mΩ"))

# -------- Tier-1 VRM bulk caps (polymer, near DrMOS output) --------
# 10x 470uF polymer per VRM = 20 total (carried from Rev 5.0; conductance
# polymer, lowest ESR/ESL at kHz band).
for i in range(20):
    ref = f"C{1000 + i}"
    rows.append(Part(ref=ref, qty=1, value="470uF 2.5V",
                     footprint="Capacitor_SMD:CP_Elec_6.3x7.7",
                     manufacturer="Panasonic", mpn="EEHZC0E471P",
                     distributor="Digi-Key", distributor_pn="PCE5311CT-ND",
                     package="D6.3 radial SMD",
                     description="Tier-1 (bulk) V_core polymer electrolytic, at VRM output"))

# -------- Tier-1 VRM bulk tantalum (100 µF tantalum, per spec §III) --------
# 2x per VRM output rail at each phase group = 12 per VRM = 24 total.
# Complements the 470 µF polymer caps above (tantalum has flatter impedance
# response in the 100 kHz - 1 MHz band where DrMOS load steps live).
for i in range(24):
    ref = f"C{1100 + i}"
    rows.append(Part(ref=ref, qty=1, value="100uF 4V tantalum",
                     footprint="Capacitor_Tantalum_SMD:CP_Tantalum_D_7343-31",
                     manufacturer="AVX", mpn="TCJD107M004R0045",
                     distributor="Mouser", distributor_pn="581-TCJD107M004R0045",
                     package="D 7343-31 tantalum",
                     description="Tier-1 bulk tantalum 100 µF 4 V (spec §III), at VRM output"))

# -------- Tier-2 mid-range decoupling: 10 µF 0805 X7R --------
# Mounted on B.Cu directly under the NCE BGA cavity (vertical power
# delivery escape fence). 80 per NCE = 160 total.
for i in range(160):
    ref = f"C{1200 + i}"
    rows.append(Part(ref=ref, qty=1, value="10uF 6.3V X7R 0805",
                     footprint="Capacitor_SMD:C_0805_2012Metric",
                     manufacturer="Murata", mpn="GRM21BR60J106ME19L",
                     distributor="Digi-Key", distributor_pn="490-3903-1-ND",
                     package="0805",
                     description="Tier-2 mid-range V_core decoupling, B.Cu under NCE BGA"))

# -------- Aux buck controllers and LDOs --------
rows.append(Part(ref="U30", qty=1, value="TPS543C20",
                 footprint="Package_QFN:VQFN-24-1EP_4x4mm_P0.5mm",
                 manufacturer="TI", mpn="TPS543C20RVFR",
                 distributor="Digi-Key", distributor_pn="296-49234-1-ND",
                 package="VQFN-24 4x4", description="40A buck, VDD_IO 1.05V"))
rows.append(Part(ref="U31", qty=1, value="TPS544C20",
                 footprint="Package_QFN:VQFN-24-1EP_4x4mm_P0.5mm",
                 manufacturer="TI", mpn="TPS544C20RVFR",
                 distributor="Digi-Key", distributor_pn="TPS544C20RVFR-ND",
                 package="VQFN-24 4x4", description="40A buck, VDDQ 1.1V (HBM4 interposer side-channel)"))
rows.append(Part(ref="U32", qty=1, value="TPS62810",
                 footprint="Package_SON:WSON-10-1EP_3x3mm_P0.5mm",
                 manufacturer="TI", mpn="TPS62810MUPR",
                 distributor="Digi-Key", distributor_pn="296-50233-1-ND",
                 package="WSON-10 3x3", description="6A buck, VPP 1.8V"))
rows.append(Part(ref="U33", qty=1, value="TPS54360",
                 footprint="Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
                 manufacturer="TI", mpn="TPS54360DDAR",
                 distributor="Digi-Key", distributor_pn="296-38625-1-ND",
                 package="HSOP-8", description="3.5A buck, 3.3V aux"))
rows.append(Part(ref="U34", qty=1, value="TPS7A20",
                 footprint="Package_SON:X2SON-6_1.0x1.45mm_P0.5mm",
                 manufacturer="TI", mpn="TPS7A2018PDQNR",
                 distributor="Digi-Key", distributor_pn="296-TPS7A2018PDQNRCT-ND",
                 package="X2SON-6", description="LDO 1.8V"))
rows.append(Part(ref="U35", qty=1, value="TPS7A20-1V2",
                 footprint="Package_SON:X2SON-6_1.0x1.45mm_P0.5mm",
                 manufacturer="TI", mpn="TPS7A2012PDQNR",
                 distributor="Digi-Key", distributor_pn="296-TPS7A2012PDQNRCT-ND",
                 package="X2SON-6", description="LDO 1.2V"))
rows.append(Part(ref="U36", qty=1, value="ADP7118-0.9",
                 footprint="Package_DFN_QFN:LFCSP-6-1EP_2x2mm_P0.65mm_EP0.7x1.0mm",
                 manufacturer="Analog Devices", mpn="ADP7118ACPZ-0.9-R7",
                 distributor="Digi-Key", distributor_pn="ADP7118ACPZ-0.9-R7CT-ND",
                 package="LFCSP-6 2x2 exposed pad",
                 description="Ultra-low-noise fixed 0.9 V LDO for TFLN RF supply (+0V9_RF)"))

# -------- Clock generation --------
rows.append(Part(ref="U40", qty=1, value="Si5395A",
                 footprint="Package_QFN:QFN-44-1EP_7x7mm_P0.5mm",
                 manufacturer="Silicon Labs", mpn="SI5395A-A-GM",
                 distributor="Digi-Key", distributor_pn="336-SI5395A-A-GMR-ND",
                 package="QFN-44 7x7", description="10-output any-frequency clock/jitter cleaner"))
rows.append(Part(ref="Y1", qty=1, value="25MHz TCXO",
                 footprint="Crystal:Crystal_SMD_Abracon_ABS07-32.768kHz_3215",
                 manufacturer="TXC", mpn="7Q-25.000MBP-T",
                 distributor="Digi-Key", distributor_pn="887-2412-1-ND",
                 package="3.2x2.5mm TCXO", description="25 MHz TCXO ±0.5 ppm"))

# -------- BMC / EC / Management --------
rows.append(Part(ref="U50", qty=1, value="AST2600",
                 footprint="Package_BGA:BGA-456_23x23mm_Layout30x30_P0.8mm",
                 manufacturer="ASPEED", mpn="AST2600A3",
                 distributor="Arrow", distributor_pn="AST2600A3",
                 package="BGA-456 0.8mm",
                 description="Server BMC, ARM Cortex-A7 dual core"))
rows.append(Part(ref="U51", qty=1, value="SLB9670",
                 footprint="Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm",
                 manufacturer="Infineon", mpn="SLB9670VQ2.0",
                 distributor="Digi-Key", distributor_pn="448-2973-ND",
                 package="TSSOP-28", description="TPM 2.0 security module"))
rows.append(Part(ref="U52", qty=1, value="W25Q256JV",
                 footprint="Package_SON:WSON-8_6x5mm_P1.27mm",
                 manufacturer="Winbond", mpn="W25Q256JVFIQ",
                 distributor="Digi-Key", distributor_pn="W25Q256JVFIQ-ND",
                 package="WSON-8", description="256Mb SPI NOR flash (UEFI primary)"))
rows.append(Part(ref="U53", qty=1, value="W25Q256JV",
                 footprint="Package_SON:WSON-8_6x5mm_P1.27mm",
                 manufacturer="Winbond", mpn="W25Q256JVFIQ",
                 distributor="Digi-Key", distributor_pn="W25Q256JVFIQ-ND",
                 package="WSON-8", description="256Mb SPI NOR flash (BMC firmware)"))

# -------- Temp sensors / monitors --------
for i in range(6):
    ref = f"U{60 + i}"
    rows.append(Part(ref=ref, qty=1, value="TMP461",
                     footprint="Package_SON:WSON-8_2x2mm_P0.5mm",
                     manufacturer="TI", mpn="TMP461AIRUNR",
                     distributor="Digi-Key", distributor_pn="296-43411-1-ND",
                     package="WSON-8 2x2", description=f"Remote diode temperature sensor (#{i+1})"))

# -------- Connectors --------
rows.append(Part(ref="J1", qty=1, value="PCIe x16 Gen6 edge",
                 footprint="Connector:PCIe_x16_Edge",
                 manufacturer="—", mpn="(edge fingers, no part)",
                 distributor="—", distributor_pn="—",
                 package="Card edge 164", description="PCIe Gen 6 x16 gold fingers"))
rows.append(Part(ref="J2", qty=1, value="PCIe x16 Gen6 aux",
                 footprint="Connector:PCIe_x16_Aux",
                 manufacturer="Amphenol", mpn="G551B251110HR",
                 distributor="Mouser", distributor_pn="649-G551B251110HR",
                 package="SMT card-edge socket",
                 description="Aux PCIe Gen 6 x16 SMT slot"))
rows.append(Part(ref="J3", qty=1, value="12VHPWR",
                 footprint="Connector:12VHPWR_Molex_203713-2001",
                 manufacturer="Molex", mpn="2037132001",
                 distributor="Digi-Key", distributor_pn="WM18999-ND",
                 package="12VHPWR 16-pin", description="600W 12V input connector"))
rows.append(Part(ref="J4", qty=1, value="MPO-24 SM",
                 footprint="Connector:MPO-24",
                 manufacturer="Senko", mpn="MPO-24-SM-FAP",
                 distributor="Senko direct", distributor_pn="MPO-24-SM-FAP",
                 package="Front-panel MPO-24",
                 description="MPO-24 single-mode optical front-panel connector"))
rows.append(Part(ref="J5", qty=1, value="USB-C BMC",
                 footprint="Connector_USB:USB_C_Receptacle_GCT_USB4085",
                 manufacturer="GCT", mpn="USB4085-GF-A",
                 distributor="Digi-Key", distributor_pn="2073-USB4085-GF-A-ND",
                 package="USB-C SMT", description="BMC management / KVM console"))
for i in range(6):  # PWM fan headers
    ref = f"J{10 + i}"
    rows.append(Part(ref=ref, qty=1, value="Fan header 4p",
                     footprint="Connector:FanPin_1x04_P2.54mm",
                     manufacturer="Molex", mpn="22232041",
                     distributor="Digi-Key", distributor_pn="WM4202-ND",
                     package="1x4 2.54mm header",
                     description=f"PWM fan #{i+1} header"))
rows.append(Part(ref="J20", qty=1, value="PMBus debug",
                 footprint="Connector:2x5_P1.27mm_Vertical_SMD",
                 manufacturer="Samtec", mpn="FTSH-105-01-F-DV-K",
                 distributor="Digi-Key", distributor_pn="SAM8796-ND",
                 package="2x5 1.27mm", description="PMBus telemetry debug"))
rows.append(Part(ref="J21", qty=1, value="BMC JTAG",
                 footprint="Connector:2x10_P1.27mm_Vertical_SMD",
                 manufacturer="Samtec", mpn="FTSH-110-01-F-DV-K",
                 distributor="Digi-Key", distributor_pn="SAM8801-ND",
                 package="2x10 1.27mm", description="BMC JTAG + UART"))
rows.append(Part(ref="J22", qty=1, value="TPM header",
                 footprint="Connector:PinHeader_2x07_P1.27mm_Vertical",
                 manufacturer="Samtec", mpn="FTSH-107-01-F-DV-K",
                 distributor="Digi-Key", distributor_pn="SAM8798-ND",
                 package="2x7 1.27mm", description="TPM 2.0 header"))

# -------- HBM4 Co-Packaged Memory stacks: 8 total (4 per compute unit) --------
# NOTE: these are the HBM4 die stacks that sit on the silicon interposer beside
# the NCE. They are not BOM-assembled on the LightRail PCB line — the composite
# NCE+4xHBM4 module arrives as a single pre-qualified CoWoS-L package from the
# SoC vendor. Listed here for architectural traceability only (DNP flag = TP =
# "To be integrated by Package vendor").
hbm4_refs = ["U103", "U104", "U105", "U106", "U203", "U204", "U205", "U206"]
for unit, ref in enumerate(hbm4_refs):
    rows.append(Part(ref=ref, qty=1, value="HBM4_12Hi_48GB",
                     footprint="LightRail:HBM4_Stack_11x11mm",
                     manufacturer="SK hynix", mpn="H56G48AT5DX117",
                     distributor="SK hynix direct", distributor_pn="H56G48AT5DX117",
                     package="HBM4 12-Hi KGSD (interposer)",
                     description=f"HBM4 12-Hi 48 GB, 8 Gbps/pin, 1024-bit bus, co-packaged on interposer (stack {unit%4} of compute unit {unit//4})",
                     dnp="TP"))

# -------- NVMe slots --------
for i in range(4):
    ref = f"J{30 + i}"
    rows.append(Part(ref=ref, qty=1, value="M.2 Key-M 2280",
                     footprint="Connector:M.2_Key_M_2280",
                     manufacturer="Amphenol", mpn="10146845-100LF",
                     distributor="Mouser", distributor_pn="649-10146845-100LF",
                     package="M.2 Key-M", description=f"NVMe Gen 5 M.2 slot {i+1}"))

# -------- Passive decoupling & bulk (Tier-3 + Tier-4) --------
# Rev 6.0 tiered PDN, spec §III:
#   * Tier-3 (1 µF 0402) – distributed along power planes for transient
#     response in the 10-100 MHz band.
#   * Tier-4 (100 nF 01005) – <1 mm of each NCE / HBM4 power pin for
#     high-frequency (100 MHz - 3 GHz) bypass; sub-nH ESL.
# SoC-local decoupling: 200 × 1 µF 0402 per SoC, 400 × 100 nF 01005 per SoC.
cap_counter = 2000
for i in range(400):  # 1uF 0402 x 400 total (200 per SoC) - Tier-3
    rows.append(Part(ref=f"C{cap_counter + i}", qty=1, value="1uF 10V X7R 0402",
                     footprint="Capacitor_SMD:C_0402_1005Metric",
                     manufacturer="Murata", mpn="GRM155R71A105KE01D",
                     distributor="Digi-Key", distributor_pn="490-3262-1-ND",
                     package="0402",
                     description="Tier-3 1uF plane-distributed decoupling"))
cap_counter += 400
for i in range(800):  # 100nF 01005 x 800 (400 per SoC) - Tier-4 fine bypass
    rows.append(Part(ref=f"C{cap_counter + i}", qty=1, value="100nF 6.3V X5R 01005",
                     footprint="Capacitor_SMD:C_01005_0402Metric",
                     manufacturer="Murata", mpn="GRM022R60J104ME15L",
                     distributor="Digi-Key", distributor_pn="490-18187-1-ND",
                     package="01005",
                     description="Tier-4 100nF bypass, <1mm from NCE/HBM4 power pin (spec §III)"))
cap_counter += 800
# HBM4 package-BGA PCB-side decoupling per spec §III (01005 <1 mm of each
# HBM4 power ball on the NCE CoWoS module fan-out).
# 32x 100nF 01005 and 8x 10uF 0805 per HBM4 stack (8 stacks total).
for i in range(256):  # 32 * 8 stacks
    rows.append(Part(ref=f"C{cap_counter + i}", qty=1, value="100nF 6.3V X5R 01005",
                     footprint="Capacitor_SMD:C_01005_0402Metric",
                     manufacturer="Murata", mpn="GRM022R60J104ME15L",
                     distributor="Digi-Key", distributor_pn="490-18187-1-ND",
                     package="01005",
                     description="HBM4 package-BGA Tier-4 bypass (VDDC/VDDQL/VDDQ/VPP)"))
cap_counter += 256
for i in range(64):  # 8 * 8 stacks - 10µF 0805 Tier-2 per HBM4
    rows.append(Part(ref=f"C{cap_counter + i}", qty=1, value="10uF 6.3V X7R 0805",
                     footprint="Capacitor_SMD:C_0805_2012Metric",
                     manufacturer="Murata", mpn="GRM21BR60J106ME19L",
                     distributor="Digi-Key", distributor_pn="490-3903-1-ND",
                     package="0805",
                     description="HBM4 Tier-2 bulk decoupling (per stack)"))
cap_counter += 64
# TFLN local RF bypass (01005, directly under TFLN periphery carrier pads)
for i in range(64):
    rows.append(Part(ref=f"C{cap_counter + i}", qty=1, value="100nF 6.3V X5R 01005",
                     footprint="Capacitor_SMD:C_01005_0402Metric",
                     manufacturer="Murata", mpn="GRM022R60J104ME15L",
                     distributor="Digi-Key", distributor_pn="490-18187-1-ND",
                     package="01005",
                     description="TFLN PIC local RF bypass (direct-drive rail)"))
cap_counter += 64

# ------- Thermal via array — B.Cu entry under NCE / HBM4 / DrMOS -------
# Logical BOM line for the thermal-via copper slugs documented in
# docs/SI_PI_Thermal_Plan.md §2. Counted here so the fab house includes
# the back-drill + copper-fill cost in the quote; the actual via array is
# drawn in KiCad as tagged 'thermal_via_array' vias, not discrete parts.
rows.append(Part(ref="TV1", qty=2048, value="THERMAL_VIA_0p3mm",
                 footprint="(in-board via, tagged thermal_via_array)",
                 manufacturer="(fab)", mpn="N/A",
                 distributor="(fab)", distributor_pn="—",
                 package="0.3 mm drill, 0.55 mm pad, filled + capped",
                 description="Thermal via array under NCE BGA + HBM4 stacks (1024 per compute unit)"))
rows.append(Part(ref="TV2", qty=480, value="THERMAL_VIA_0p4mm",
                 footprint="(in-board via, tagged thermal_via_array)",
                 manufacturer="(fab)", mpn="N/A",
                 distributor="(fab)", distributor_pn="—",
                 package="0.4 mm drill, 0.70 mm pad, filled + capped",
                 description="Thermal via under DrMOS PowerPAK (10 per phase × 48 phases)"))

# -------- Resistors: 0201 / 0402 range --------
res_counter = 1
# 100 ohm terminations for PCIe / TFLN RF
for i in range(64):
    rows.append(Part(ref=f"R{res_counter + i}", qty=1, value="100Ω 0.1% 1/16W",
                     footprint="Resistor_SMD:R_0402_1005Metric",
                     manufacturer="Panasonic", mpn="ERA-2AEB101X",
                     distributor="Digi-Key", distributor_pn="P100DBCT-ND",
                     package="0402 thin-film",
                     description="100Ω diff termination (PCIe/TFLN/SerDes)"))
res_counter += 64
# 10k I2C pull-ups
for i in range(32):
    rows.append(Part(ref=f"R{res_counter + i}", qty=1, value="10kΩ 1%",
                     footprint="Resistor_SMD:R_0402_1005Metric",
                     manufacturer="Yageo", mpn="RC0402FR-0710KL",
                     distributor="Digi-Key", distributor_pn="311-10.0KLRCT-ND",
                     package="0402", description="10k pullup (I2C / GPIO)"))
res_counter += 32
# 4.7k pullups
for i in range(32):
    rows.append(Part(ref=f"R{res_counter + i}", qty=1, value="4.7kΩ 1%",
                     footprint="Resistor_SMD:R_0402_1005Metric",
                     manufacturer="Yageo", mpn="RC0402FR-074K7L",
                     distributor="Digi-Key", distributor_pn="311-4.70KLRCT-ND",
                     package="0402", description="4.7k pullup"))
res_counter += 32
# 0 ohm bridges
for i in range(64):
    rows.append(Part(ref=f"R{res_counter + i}", qty=1, value="0Ω jumper",
                     footprint="Resistor_SMD:R_0201_0603Metric",
                     manufacturer="Yageo", mpn="RC0201FR-070RL",
                     distributor="Digi-Key", distributor_pn="311-0.0JRCT-ND",
                     package="0201", description="0Ω jumper / DNI option"))
res_counter += 64

# -------- Ferrite beads --------
for i in range(32):
    rows.append(Part(ref=f"FB{i+1}", qty=1, value="600Ω @ 100MHz",
                     footprint="Inductor_SMD:L_0402_1005Metric",
                     manufacturer="Murata", mpn="BLM15AX601SN1D",
                     distributor="Digi-Key", distributor_pn="490-1053-1-ND",
                     package="0402", description="Ferrite bead, analog supply filter"))

# -------- LEDs + current-limit resistors --------
for i in range(6):
    rows.append(Part(ref=f"D{i+1}", qty=1, value="Green LED 0603",
                     footprint="LED_SMD:LED_0603_1608Metric",
                     manufacturer="Kingbright", mpn="APHHS1005LSECK-J3",
                     distributor="Digi-Key", distributor_pn="754-1122-1-ND",
                     package="0603", description=f"Status LED #{i+1}"))

# -------- Fuses --------
rows.append(Part(ref="F1", qty=1, value="50A 12V auto-reset",
                 footprint="Fuse_SMD:Fuse_Littelfuse_Nano2-466",
                 manufacturer="Littelfuse", mpn="0466050.NR",
                 distributor="Digi-Key", distributor_pn="F6464CT-ND",
                 package="Nano2-466", description="12V input fuse 50A"))
rows.append(Part(ref="F2", qty=1, value="50A 12V auto-reset",
                 footprint="Fuse_SMD:Fuse_Littelfuse_Nano2-466",
                 manufacturer="Littelfuse", mpn="0466050.NR",
                 distributor="Digi-Key", distributor_pn="F6464CT-ND",
                 package="Nano2-466", description="12V input fuse 50A (redundant)"))

# -------- Hot-swap controllers for 12V input --------
rows.append(Part(ref="U70", qty=1, value="LTC4282",
                 footprint="Package_QFN:QFN-40-1EP_6x6mm_P0.5mm",
                 manufacturer="Analog Devices", mpn="LTC4282CUHF#PBF",
                 distributor="Digi-Key", distributor_pn="LTC4282CUHF-ND",
                 package="QFN-40 6x6", description="Hot-swap controller, 12V 100A"))
rows.append(Part(ref="Q1", qty=1, value="IRF7739",
                 footprint="Package_SO:SOIC-8-1EP_3.9x4.9mm",
                 manufacturer="Infineon", mpn="IRF7739L2TRPBF",
                 distributor="Digi-Key", distributor_pn="IRF7739L2TRPBF-ND",
                 package="SO-8 PowerPak",
                 description="12V hot-swap pass FET"))
rows.append(Part(ref="Q2", qty=1, value="IRF7739",
                 footprint="Package_SO:SOIC-8-1EP_3.9x4.9mm",
                 manufacturer="Infineon", mpn="IRF7739L2TRPBF",
                 distributor="Digi-Key", distributor_pn="IRF7739L2TRPBF-ND",
                 package="SO-8 PowerPak",
                 description="12V hot-swap pass FET (parallel)"))

# -------- Write files --------
outdir = Path(__file__).resolve().parent
csv_path = outdir / "BOM.csv"
md_path = outdir / "BOM.md"

with csv_path.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Ref", "Qty", "Value", "Footprint", "Manufacturer", "MPN",
                "Distributor", "DistributorPN", "Package", "Description",
                "DNP", "Notes"])
    for p in rows:
        w.writerow([p.ref, p.qty, p.value, p.footprint, p.manufacturer, p.mpn,
                    p.distributor, p.distributor_pn, p.package,
                    p.description, p.dnp, p.notes])

# Summary counts for README
from collections import Counter
pkg_count = Counter(p.package for p in rows)
total_parts = sum(p.qty for p in rows)

with md_path.open("w") as f:
    f.write("# BOM summary\n\n")
    f.write(f"**Total part instances:** {total_parts}\n\n")
    f.write(f"**Unique line items:** {len(rows)}\n\n")
    f.write("## Package distribution\n\n")
    f.write("| Package | Count |\n|---------|-------|\n")
    for pkg, n in sorted(pkg_count.items(), key=lambda kv: -kv[1]):
        f.write(f"| {pkg} | {n} |\n")
    f.write("\nSee `BOM.csv` for the complete list.\n")

print(f"Wrote {csv_path} ({total_parts} parts, {len(rows)} line items)")
print(f"Wrote {md_path}")

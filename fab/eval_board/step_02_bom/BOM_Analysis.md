# Step 2: BOM — Bill of Materials Analysis
## LightRail NCE+TFLN Evaluation Board (100×100 mm)

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. BOM Summary

| Metric | Value |
|--------|-------|
| **Total part instances** | 183 |
| **Unique line items** | 62 |
| **SMD parts (top)** | 168 |
| **SMD parts (bottom)** | 8 |
| **Through-hole parts** | 7 |
| **Board assembly sides** | 2 (top primary, bottom decoupling only) |

## 2. Package Distribution

| Package | Qty | Notes |
|---------|-----|-------|
| 0402 | 72 | Bypass caps, pull-up/pull-down resistors |
| 0603 | 18 | Power path caps, LED series resistors |
| 0805 | 8 | Bulk decoupling, power input caps |
| QFN-64 (8×8 mm) | 1 | NCE test chip U1 |
| BGA-256 (14×14 mm) | 1 | Xilinx Artix-7 XC7A100T U2 |
| Custom optical module | 1 | TFLN PIC U3 |
| SOT-23-5 | 6 | LDO regulators |
| D-PAK / SOT-223 | 2 | 5V buck, power MOSFETs |
| QFN-48 (7×7 mm) | 1 | FT232H USB-UART bridge |
| QFN-28 (5×5 mm) | 1 | Si5395A PLL |
| 3.2×2.5 mm | 1 | 100 MHz TCXO |
| SMA edge-mount | 4 | RF probe connectors |
| USB-C SMT | 1 | USB interface |
| 2×5 1.27mm header | 1 | JTAG |
| 2×7 1.27mm header | 1 | GPIO expansion |
| Barrel jack | 1 | 12V power input |
| 2-pin power header | 1 | Alternative 12V input |
| M.2 Key-M | 0 | Not on eval board |
| Test point (0.8mm pad) | 16 | Power rail + signal TPs |

## 3. Key Components

### 3.1 Active ICs

| Ref | Part | MPN | Package | Function |
|-----|------|-----|---------|----------|
| U1 | NCE Test Chip | LR-NCE-MPW-001 | QFN-64 | DUT — Neural Compute Engine |
| U2 | Artix-7 FPGA | XC7A100T-1FTG256C | BGA-256 | AXI master, test controller |
| U3 | TFLN PIC | LR-TFLN-PIC-001 | Custom | Optical transceiver module |
| U10 | LDO 0.9V | ADP7118AUJZ-0.9-R7 | TSOT-5 | NCE VDD_CORE |
| U11 | LDO 1.8V | TPS7A2018DBVR | SOT-23-5 | NCE VDD_IO |
| U12 | LDO 1.0V | TPS7A2010DBVR | SOT-23-5 | FPGA VCCINT |
| U13 | LDO 3.3V | TPS7A3301DBVR | SOT-23-5 | FPGA VCCAUX |
| U14 | LDO 1.8V | TPS7A2018DBVR | SOT-23-5 | FPGA VCCO bank |
| U15 | Buck 5V | TPS54360DDAR | HSOP-8 | Main 12V→5V converter |
| U20 | PLL | Si5395A-A-GM | QFN-28 | Clock synthesis (100 MHz, 2 GHz, 156.25 MHz) |
| U21 | ADC | AD7928BRUZ | TSSOP-20 | TFLN photodetector monitor |
| U22 | USB-UART | FT232HQ | QFN-48 | USB debug interface |
| U23 | SPI Flash | W25Q128JVSIQ | WSON-8 | FPGA configuration bitstream |
| U24 | DAC | AD5684RBRUZ | TSSOP-16 | TFLN bias control (4-ch) |
| U25 | Temp sensor | TMP461AIDR | WSON-8 | NCE die temperature (via I2C) |

### 3.2 Passive Summary

| Type | Quantity | Values |
|------|----------|--------|
| Ceramic caps (MLCC) | 98 | 100pF–22µF (0402, 0603, 0805) |
| Resistors | 42 | 0Ω–100kΩ (0402, 0603) |
| Inductors | 3 | 4.7µH (TPS54360), ferrite beads |
| Tantalum caps | 2 | 100µF/16V (input bulk) |
| Crystal / TCXO | 1 | 100 MHz TCXO (Si531) |
| LEDs | 4 | Power, Activity, Fault, Link |

## 4. Part Availability Assessment

| Component | Source | Lead Time | Risk |
|-----------|--------|-----------|------|
| XC7A100T-1FTG256C | DigiKey/Mouser | 8–12 weeks | Medium — check allocation |
| FT232HQ | DigiKey | In stock | Low |
| Si5395A-A-GM | Mouser | 6–8 weeks | Low |
| AD7928BRUZ | DigiKey | In stock | Low |
| AD5684RBRUZ | DigiKey | In stock | Low |
| ADP7118AUJZ-0.9 | DigiKey | In stock | Low |
| TPS7A2018DBVR | DigiKey | In stock | Low |
| TPS54360DDAR | DigiKey | In stock | Low |
| W25Q128JVSIQ | LCSC/DigiKey | In stock | Low |
| TMP461AIDR | DigiKey | In stock | Low |
| NCE test chip (U1) | MPW shuttle | 16–20 weeks | Custom — schedule-dependent |
| TFLN PIC (U3) | Custom fab | 12–16 weeks | Custom — vendor-dependent |

**Long-lead items:** Artix-7 FPGA (order immediately), NCE die (MPW schedule), TFLN PIC (custom).

## 5. BOM Export Formats

| Format | File | Purpose |
|--------|------|---------|
| CSV (full) | `Eval_Board_BOM.csv` | Master BOM for procurement |
| CSV (JLCPCB) | `Eval_Board_BOM_JLCPCB.csv` | JLCPCB assembly format |
| CSV (PCBWay) | `Eval_Board_BOM_PCBWay.csv` | PCBWay turnkey format |
| Markdown | This document | Human review |

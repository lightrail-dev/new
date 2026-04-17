# Pinouts

Pinout tables for major connectors and ICs. CSV versions in this folder
(`pinout_*.csv`) are authoritative and track the KiCad schematic.

## 1. PCIe Gen 6 x16 edge connector (CEM 6.0)

See [`pinout_PCIe_x16.csv`](pinout_PCIe_x16.csv). Summary:

| Side B (top)   | Signal            |   | Side A (bottom)| Signal            |
| -------------- | ----------------- | - | -------------- | ----------------- |
| B1             | +12V              |   | A1             | PRSNT#1           |
| B2             | +12V              |   | A2             | +12V              |
| B3             | +12V              |   | A3             | +12V              |
| B4             | GND               |   | A4             | GND               |
| B5             | SMCLK             |   | A5             | JTAG2             |
| B6             | SMDAT             |   | A6             | JTAG3             |
| B7             | GND               |   | A7             | JTAG4             |
| B8             | +3.3V             |   | A8             | JTAG5             |
| B9             | JTAG1_TRST#       |   | A9             | +3.3V             |
| B10            | 3.3Vaux           |   | A10            | +3.3V             |
| B11            | WAKE#             |   | A11            | PERST#            |
| B12            | RSVD              |   | A12            | GND               |
| B13            | GND               |   | A13            | REFCLK+           |
| B14            | TX0+              |   | A14            | REFCLK-           |
| B15            | TX0-              |   | A15            | GND               |
| B16            | GND               |   | A16            | RX0+              |
| B17            | PRSNT#2           |   | A17            | RX0-              |
| B18            | GND               |   | A18            | GND               |
| B19..B82       | TX1..TX15 diff    |   | A19..A82       | RX1..RX15 diff    |

PERST#, REFCLK, WAKE#, SMCLK/SMDAT routed to the SoC via PCIe switch /
retimer. All 16 diff pairs: 85 Ω diff (Gen 6 target), max insertion loss
32 dB @ 16 GHz end-to-end (edge → retimer → SoC).

## 2. AI SoC BGA-2500 (U1, U2) — pin map overview

Full 2500-ball map in [`pinout_SoC_BGA2500.csv`](pinout_SoC_BGA2500.csv).
Summary by functional domain:

| Domain               | Balls | Placement                          |
| -------------------- | ----- | ---------------------------------- |
| V_CORE               | 612   | Central core (cols N–AK, rows 10–38) |
| GND                  | 624   | Distributed                        |
| VDD_IO (1.05 V)      | 96    | Peripheral rings                   |
| VDDQ_DDR5 (1.1 V)    | 80    | DDR5 PHY region (east side)        |
| VPP_DDR5 (1.8 V)     | 16    | DDR5 PHY region                    |
| DDR5 Ch0 (DQ/DQS/CA) | 160   | East-north quadrant                |
| DDR5 Ch1             | 160   | East-south quadrant                |
| DDR5 Ch2             | 160   | West-north quadrant                |
| DDR5 Ch3             | 160   | West-south quadrant                |
| PCIe Gen 6 x32       | 144   | South edge (x16 + x16)             |
| TFLN SerDes 16 ch    | 96    | North edge                         |
| Mgmt I²C / SPI / JTAG| 32    | Corner (NW)                        |
| Thermal diode        | 4     | Center                             |
| Reserved / NC        | 156   | Distributed                        |
| **Total**            | **2500** |                                 |

Ball pitch: 0.8 mm. Package size: 40 mm × 40 mm. Collapse height 0.45 mm.

## 3. TFLN PIC (U3, U4) — RF interface

Placeholder periphery footprint; real TFLN PICs are vendor-NDA (Lightmatter,
Ayar Labs, HyperLight). Typical RF interface, 8-channel push-pull drive:

| Pin group        | Count | Signal                                  |
| ---------------- | ----- | --------------------------------------- |
| RF_DRIVE_P / N   | 16    | 8× differential pairs (200G PAM4)       |
| BIAS_TUNE        | 8     | Phase-bias DC tune (0–5 V)              |
| TEC_TH           | 2     | TEC thermistor + TEC drive              |
| PD_MON           | 8     | Tap photodiode monitor (μA)             |
| VCC_RF           | 4     | RF supply (0.9 V or 1.2 V)              |
| VCC_BIAS         | 2     | Bias circuit supply                     |
| GND              | ≥40   | —                                       |
| FIBER_IN / OUT   | 24    | MPO-24 optical (16 SM + 8 monitor)      |

See [`pinout_TFLN_PIC.csv`](pinout_TFLN_PIC.csv).

## 4. DDR5 DIMM 288-pin connector (per slot)

Full pin map in [`pinout_DDR5_DIMM.csv`](pinout_DDR5_DIMM.csv). Summary:

| Group            | Pins       | Count | Topology  |
| ---------------- | ---------- | ----- | --------- |
| DQ0..DQ63        | per byte   | 64    | Point-to-point (T-branch) |
| DQS0..DQS7 P/N   | per byte   | 16    | Differential              |
| DM0..DM7 / DBI#  | per byte   | 8     | Point-to-point            |
| CA0..CA13        | —          | 14    | Fly-by                    |
| CK_t / CK_c      | —          | 2     | Fly-by differential       |
| CS0# / CS1#      | —          | 2     | Fly-by                    |
| ODT0 / ODT1      | —          | 2     | Fly-by                    |
| RESET#           | —          | 1     | —                         |
| SPD (I²C)        | SA0..2, SDA, SCL, WP | 6 | I²C               |
| PMIC (DIMM)      | —          | 6     | Control                   |
| ALERT#, EVENT#   | —          | 2     | Open-drain                |
| VDDQ (1.1 V)     | —          | 32    | Plane                     |
| VPP (1.8 V)      | —          | 4     | Plane                     |
| GND              | —          | ≥80   | Plane                     |
| **Total**        |            | **288** |                         |

Termination: on-DIMM RCD (Register Clock Driver); on-die termination for DQ.

## 5. NVMe M.2 (key-M) / U.3 SFF-TA-1001

See [`pinout_NVMe_M2.csv`](pinout_NVMe_M2.csv). Gen 5/6 capable.
Uses 4 PCIe lanes (x4) from the SoC root or switch, 3.3 V + 3.3 V aux.

## 6. MPO-24 optical front-panel

24-fiber single-mode MPO connector, 12 channels up + 12 channels down,
with 8 of the 24 fibers reserved for monitor / calibration loopback.

| Fiber # | Function        | Mode  |
| ------- | --------------- | ----- |
| 1–8     | PIC A TX (8 ch) | SM    |
| 9–16    | PIC A RX (8 ch) | SM    |
| 17–20   | PIC A monitor   | SM    |
| 21–24   | PIC B monitor   | SM    |

(In a dual-PIC design the host-side MPO typically pairs with a second
MPO-24 for PIC B; this scaffold provisions one connector for simplicity.)

## 7. BMC / EC headers

| Header | Pin count | Interface                           |
| ------ | --------- | ----------------------------------- |
| J_BMC_DBG | 20     | BMC UART0, JTAG, GPIO, I²C          |
| J_EC_PMBUS | 10    | PMBus to VRMs, DIMM PMIC telemetry  |
| J_FP_USB  | 4      | USB-C BMC management                |
| J_FAN     | 6×4    | PWM + tach per fan, 12 V            |
| J_TPM     | 14     | SPI + INT + RST                     |
| J_LPC     | 20     | Legacy LPC bus (optional)           |

## 8. Schematic-to-pinout cross-reference

Every signal listed above should have:
- A hierarchical label in the corresponding `*.kicad_sch` sheet.
- A matching net name in the `.kicad_pcb`.
- A row in `fab/BOM.csv` if it maps to a discrete passive / connector.

When pad-to-net assignments in the PCB are completed (see README §5.3), the
KiCad-exported netlist (`pcbnew → File → Export → Netlist`) should match
the tables in this document.

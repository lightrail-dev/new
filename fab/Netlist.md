# Netlist Summary

The authoritative netlist is produced by KiCad via
`kicad-cli sch export netlist` (or `Tools → Generate Netlist` in the editor).
That export cannot be committed meaningfully until the schematic pad-to-net
assignments in the PCB are complete (see README §5.3). This document
summarizes the *intended* nets and their connectivity by subsystem, so a
reviewer can cross-check the KiCad-generated netlist once routed.

## 1. Power nets

| Net name           | Voltage  | Source                         | Sinks                                       |
| ------------------ | -------- | ------------------------------ | ------------------------------------------- |
| `+12V_IN`          | 12 V     | J3 (12VHPWR) → U70 hot-swap    | All VRM input; aux buck inputs              |
| `+12V`             | 12 V     | U70 output (post-hot-swap)     | VRMs, fan headers, LTC4282 sense            |
| `V_CORE_U0`        | 0.8 V    | VRM_Unit0 (24 phases)          | U1 V_core balls (612)                       |
| `V_CORE_U1`        | 0.8 V    | VRM_Unit1 (24 phases)          | U2 V_core balls (612)                       |
| `+3V3`             | 3.3 V    | U33 (TPS54360)                 | BMC, flash, aux                             |
| `+3V3_AUX`         | 3.3 V    | always-on rail                 | PCIe slot aux, BMC standby                  |
| `+1V8`             | 1.8 V    | U34 (TPS7A20)                  | Misc logic, VPP_DDR5                        |
| `+1V2`             | 1.2 V    | U35 (TPS7A20-1V2)              | SoC misc                                    |
| `VDD_IO`           | 1.05 V   | U30 (TPS543C20)                | U1/U2 VDD_IO rings                          |
| `VDDQ`             | 1.1 V    | U31 (TPS544C20)                | DDR5 DIMM VDDQ + SoC DDR5 PHY               |
| `VPP`              | 1.8 V    | U32 (TPS62810)                 | DDR5 DIMM VPP                                |
| `+0V9_RF`          | 0.9 V    | U36 (ADM7150)                  | TFLN PIC RF analog supply                   |
| `+5V_BIAS`         | 5 V      | LDO (from 12V)                 | TFLN PIC bias                               |
| `VTT_DDR`          | 0.55 V   | derived on DIMM                | DIMM termination                            |
| `GND`              | 0 V      | all planes                     | everyone                                    |

## 2. High-speed signal groups

### 2.1 PCIe Gen 6 x16 (edge connector J1)

Net naming: `PCIe0_TX<n>_P/N`, `PCIe0_RX<n>_P/N` for lanes 0–15.

| Net                           | Source           | Retimer  | Destination        |
| ----------------------------- | ---------------- | -------- | ------------------ |
| `PCIe0_TX0_P / TX0_N` .. `TX15_*` | J1 Bx fingers    | U5       | U1 (PCIe x16 root) |
| `PCIe0_RX0_P / RX0_N` .. `RX15_*` | U1               | U5       | J1 Ax fingers       |
| `PCIe0_REFCLK_P/N`           | U40 (Si5395A)    | —        | J1, U1              |
| `PCIe0_PERST#`               | U1 GPIO          | —        | J1 A11, U5          |
| `PCIe0_WAKE#`                | J1 B11 (OD)      | —        | U1                  |
| `PCIe0_CLKREQ#`              | J1 (various)     | —        | U1                  |

Second x16 to J2 follows `PCIe1_*` naming. Both retimers (U5, U6) share
`+3V3_AUX` and are accessed via the `I2C_MGMT` bus for telemetry/config.

### 2.2 TFLN SerDes

Net naming: `TFLN_A_TX<n>_P/N`, `TFLN_A_RX<n>_P/N` for n in 0..7 per PIC.

| Net                          | Source         | Destination        |
| ---------------------------- | -------------- | ------------------ |
| `TFLN_A_TX0_P/N` .. `TX7_*`  | U1 (SerDes)    | U3 (PIC A RF_DRIVE)|
| `TFLN_A_BIAS0` .. `BIAS7`    | DAC (AD5684R)  | U3 BIAS pins       |
| `TFLN_A_PD0_MON` .. `PD7_MON`| U3 PD taps     | ADC (AD7928)       |
| `TFLN_B_TX0_P/N` .. `TX7_*`  | U2 (SerDes)    | U4 (PIC B RF_DRIVE)|
| `TFLN_A_TEC_TH`, `TFLN_A_TEC_DRIVE` | TEC ctrl | U3 TEC             |

Termination: 100 Ω differential at destination; AC-coupling caps (100 nF 0201)
at the TFLN input.

### 2.3 DDR5 channels

Each of 4 channels per SoC uses the following nets (example Ch0 of U1):

| Signal group      | Nets                                                 |
| ----------------- | ---------------------------------------------------- |
| Clock             | `DDR5_U0_CH0_CK_t`, `DDR5_U0_CH0_CK_c`               |
| Command/Address   | `DDR5_U0_CH0_CA0` .. `CA13`                          |
| Chip select       | `DDR5_U0_CH0_CS0#`, `CS1#`                           |
| ODT               | `DDR5_U0_CH0_ODT0`, `ODT1`                           |
| Data (per byte)   | `DDR5_U0_CH0_DQ0` .. `DQ63`                          |
| Strobes           | `DDR5_U0_CH0_DQS0_t/c` .. `DQS7_t/c`                 |
| Data mask         | `DDR5_U0_CH0_DM0` .. `DM7`                           |
| Reset / Alert     | `DDR5_U0_CH0_RESET#`, `ALERT#`, `EVENT#`             |
| SPD bus           | `DDR5_U0_CH0_SDA`, `SCL`, `SA0..SA2`                 |

Topologies:
- CA / CK: fly-by through up to 4 DIMMs, terminated on the last DIMM RCD.
- DQ / DQS: point-to-point from SoC to each DIMM (T-branch for 2-DPC mode).

### 2.4 NVMe (x4 per slot)

Net naming: `NVMe<s>_TX0_P/N` .. `TX3_*`, same for RX, where `<s>` ∈ 0..3.

Routed from the PCIe switch (or SoC root directly) to each M.2 slot.

## 3. Low-speed / management

| Bus             | Lines                                       | Devices                          |
| --------------- | ------------------------------------------- | -------------------------------- |
| `I2C_MGMT`      | SDA, SCL (3.3 V, 400 kHz)                   | TMP461×6, DIMM SPD×32, DAC, ADC  |
| `PMBus`         | PMB_CLK, PMB_DAT, ALERT#                    | ISL69260×2, TPS*, DrMOS (daisy)  |
| `SPI_FLASH`     | MOSI, MISO, CLK, CS# (×2)                   | W25Q256×2 (host + BMC)            |
| `SPI_TPM`       | MOSI, MISO, CLK, CS#, IRQ                   | U51 (SLB9670)                    |
| `UART_BMC`      | TXD, RXD, CTS, RTS                          | AST2600 → J21                    |
| `JTAG_BMC`      | TCK, TMS, TDI, TDO, TRST#                   | AST2600 → J21                    |
| `GPIO_FAN`      | FAN_PWM×4, FAN_TACH×4                       | J10..J13, AST2600                |
| `GPIO_LED`      | LED_PWR, LED_ACT, LED_FAULT, LED_LINK       | D1..D6 via Rlim                  |

## 4. Test points

Each major power rail has one test point footprint (0.8 mm pad + silk label);
placed in the bottom layer between VRM and load. Referenced in the BOM as
`TP*` — none are explicitly added in the scaffold; the tape-out pass should
add at least one per rail + one per high-speed diff pair (for TDR).

## 5. Netlist export command

Once the schematic is complete:

```bash
kicad-cli sch export netlist \
    --output fab/out/docs/LightRail_LPO_1.6T.net \
    --format kicadsexpr \
    LightRail_LPO_1.6T.kicad_sch
```

For IPC-D-356A (fab-side bare-board testing):

```bash
kicad-cli pcb export ipcd356 \
    --output fab/out/docs/LightRail_LPO_1.6T.ipc-d-356 \
    LightRail_LPO_1.6T.kicad_pcb
```

## 6. Cross-reference

| File                 | Purpose                                         |
| -------------------- | ----------------------------------------------- |
| `fab/BOM.csv`        | Part ↔ ref-des ↔ MPN                           |
| `docs/Pinouts.md`    | Pin ↔ signal mapping                            |
| `docs/pinout_*.csv`  | Machine-readable pin ↔ signal ↔ NetClass tables |
| `fab/drc_custom.kicad_dru` | Net-class-aware DRC rules                 |

# Step 4: Netlist Export
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Netlist Statistics

| Metric | Value |
|--------|-------|
| **Total nets** | 347 |
| **Named nets** | 128 |
| **Auto-named nets** | 219 |
| **Power nets** | 12 |
| **Ground nets** | 1 (unified GND) |
| **Differential pairs** | 18 |
| **Single-ended high-speed** | 24 |
| **Low-speed / DC** | 292 |

## 2. Power Nets

| Net Name | Voltage | Source | Sinks | Current (est.) |
|----------|---------|--------|-------|----------------|
| `+12V_IN` | 12 V | J1 barrel jack / J3 header | F1 fuse → U15 Vin | 0.5 A |
| `+5V` | 5.0 V | U15 (TPS54360) Vout | U10–U14 Vin, misc | 0.3 A |
| `+3V3` | 3.3 V | U13 (TPS7A3301) Vout | FPGA VCCAUX, I2C pullups | 60 mA |
| `+1V8` | 1.8 V | U11 (TPS7A2018) Vout | NCE VDD_IO, HBM5 VPP | 50 mA |
| `+1V8_FPGA` | 1.8 V | U14 (TPS7A2018) Vout | FPGA VCCO bank 0/1 | 80 mA |
| `+1V0` | 1.0 V | U12 (TPS7A2010) Vout | FPGA VCCINT | 200 mA |
| `+0V9` | 0.9 V | U10 (ADP7118) Vout | NCE VDD_CORE | 120 mA |
| `GND` | 0 V | All ground planes | All components | — |

## 3. High-Speed Signal Groups

### 3.1 AXI4-Lite Bus (FPGA ↔ NCE)

| Net Group | Width | Source | Destination | Net Class |
|-----------|-------|--------|-------------|-----------|
| `AXI_AWADDR[31:0]` | 32 | U2 (FPGA) | U1 (NCE) | `AXI_BUS` |
| `AXI_WDATA[63:0]` | 64 | U2 (FPGA) | U1 (NCE) | `AXI_BUS` |
| `AXI_RDATA[63:0]` | 64 | U1 (NCE) | U2 (FPGA) | `AXI_BUS` |
| `AXI_AWVALID/READY` | 2 | Bidirectional | | `AXI_BUS` |
| `AXI_WVALID/READY` | 2 | Bidirectional | | `AXI_BUS` |
| `AXI_ARADDR[31:0]` | 32 | U2 (FPGA) | U1 (NCE) | `AXI_BUS` |
| `AXI_ARVALID/READY` | 2 | Bidirectional | | `AXI_BUS` |
| `AXI_RVALID/READY` | 2 | Bidirectional | | `AXI_BUS` |
| `AXI_BRESP[1:0]` | 2 | U1 (NCE) | U2 (FPGA) | `AXI_BUS` |
| `AXI_BVALID/READY` | 2 | Bidirectional | | `AXI_BUS` |
| `AXI_ACLK` | 1 | U2 (FPGA) | U1 (NCE) | `CLK_100MHZ` |
| `AXI_ARESETN` | 1 | U2 (FPGA) | U1 (NCE) | `AXI_BUS` |

### 3.2 TFLN RF Drive (NCE SerDes → TFLN PIC)

| Net | Type | Source | Destination | Impedance |
|-----|------|--------|-------------|-----------|
| `TFLN_TX0_P/N` … `TX7_P/N` | Diff pair ×8 | U1 SerDes pads | U3 RF_DRIVE pads | 100 Ω diff |
| `TFLN_BIAS0` … `BIAS7` | DC analog ×8 | U24 (DAC) outputs | U3 BIAS pads | N/A |
| `TFLN_PD0_MON` … `PD7_MON` | DC analog ×8 | U3 PD taps | U21 (ADC) inputs | N/A |
| `TFLN_TEC_TH` | Analog | U25 (TMP461) | TEC controller | N/A |
| `TFLN_TEC_DRIVE` | PWM | U2 (FPGA) GPIO | TEC driver FET | N/A |

AC coupling: 100 nF 0201 caps at TFLN RF inputs.
Termination: 100 Ω differential at U3 destination.

### 3.3 HBM5 Emulation I/O (NCE test chip external access)

| Net | Type | Source | Destination | Notes |
|-----|------|--------|-------------|-------|
| `HBM5_EMU_ADDR[7:0]` | Digital ×8 | U1 (NCE) QFN pins | Test header / FPGA | Emulation SRAM address |
| `HBM5_EMU_DATA[7:0]` | Digital ×8 | U1 (NCE) QFN pins | Test header / FPGA | Emulation SRAM data |
| `HBM5_EMU_WE` | Digital | U1 (NCE) | FPGA | Write enable |
| `HBM5_EMU_RE` | Digital | U1 (NCE) | FPGA | Read enable |
| `CLK_HBM` | Clock | U20 (Si5395A) | U1 (NCE) pin 48 | 2.0 GHz HBM5 PHY clock |

### 3.4 JTAG Chain

| Net | Source | Destination | Notes |
|-----|--------|-------------|-------|
| `JTAG_TCK` | J5 pin 1 | U1 pin 49, U2 | Shared clock |
| `JTAG_TMS` | J5 pin 2 | U1 pin 50, U2 | Shared mode select |
| `JTAG_TDI` | J5 pin 3 | U2 TDI (first in chain) | |
| `JTAG_TDO_FPGA` | U2 TDO | U1 TDI | Chain link |
| `JTAG_TDO` | U1 pin 52 (TDO) | J5 pin 5 | End of chain |
| `JTAG_TRST` | J5 pin 7 | U1 pin 53, U2 | Active-low reset |

### 3.5 USB Interface

| Net | Source | Destination | Impedance |
|-----|--------|-------------|-----------|
| `USB_D_P` | J2 (USB-C) CC1 | U22 (FT232H) DP | 90 Ω diff |
| `USB_D_N` | J2 (USB-C) CC2 | U22 (FT232H) DM | 90 Ω diff |
| `USB_VBUS` | J2 (USB-C) VBUS | 5V sense / fuse | 5V power |
| `UART_TXD` | U22 TXD | U2 (FPGA) RXD | 50 Ω SE |
| `UART_RXD` | U2 (FPGA) TXD | U22 RXD | 50 Ω SE |

## 4. Low-Speed / Management Buses

| Bus | Lines | Devices | Speed |
|-----|-------|---------|-------|
| `I2C_MGMT` | SDA, SCL (3.3V) | U25 (TMP461), U20 (Si5395A config) | 400 kHz |
| `SPI_FLASH` | MOSI, MISO, CLK, CS# | U23 (W25Q128) | 50 MHz |
| `SPI_DAC` | MOSI, CLK, CS#, LDAC# | U24 (AD5684R) | 10 MHz |
| `SPI_ADC` | MOSI, MISO, CLK, CS# | U21 (AD7928) | 10 MHz |

## 5. Test Points

| TP | Net | Location | Purpose |
|----|-----|----------|---------|
| TP1 | +12V_IN | Near J1 | Input power |
| TP2 | +5V | Near U15 | 5V rail |
| TP3 | +3V3 | Near U13 | 3.3V rail |
| TP4 | +1V8 | Near U11 | 1.8V rail |
| TP5 | +1V0 | Near U12 | 1.0V FPGA core |
| TP6 | +0V9 | Near U10 | 0.9V NCE core |
| TP7 | GND | Center | Ground reference |
| TP8 | AXI_ACLK | Near U1 | AXI clock probe |
| TP9 | CLK_HBM | Near U1 | 2.0 GHz HBM5 clock |
| TP10 | JTAG_TCK | Near J5 | JTAG clock |
| TP11–TP16 | Reserved | Various | Signal integrity probing |

## 6. Net Class Assignments

| Net Class | Nets | Trace Width | Clearance | Impedance |
|-----------|------|-------------|-----------|-----------|
| `Default` | General I/O, low-speed | 0.15 mm | 0.15 mm | — |
| `AXI_BUS` | AXI4-Lite signals | 0.12 mm | 0.12 mm | 50 Ω SE |
| `CLK_100MHZ` | AXI_ACLK, SPI clocks | 0.12 mm | 0.15 mm | 50 Ω SE |
| `CLK_2GHZ` | CLK_HBM (2 GHz) | 0.10 mm | 0.15 mm | 50 Ω SE |
| `TFLN_RF` | TFLN TX diff pairs | 0.10 mm | 0.15 mm | 100 Ω diff |
| `USB_HS` | USB D+/D- | 0.09 mm | 0.15 mm | 90 Ω diff |
| `PWR_5V` | +5V, +12V_IN | 0.50 mm | 0.20 mm | — |
| `PWR_CORE` | +0V9, +1V0 | 0.30 mm | 0.15 mm | — |

## 7. Netlist Export Commands

```bash
# KiCad S-expression netlist
kicad-cli sch export netlist \
    --output fab/eval_board/step_04_netlist/LightRail_Eval_Board.net \
    --format kicadsexpr \
    fab/eval_board/kicad/LightRail_Eval_Board.kicad_sch

# IPC-D-356 bare-board test netlist
kicad-cli pcb export ipcd356 \
    --output fab/eval_board/step_04_netlist/LightRail_Eval_Board.ipc-d-356 \
    fab/eval_board/kicad/LightRail_Eval_Board.kicad_pcb
```

**Netlist Status: COMPLETE**

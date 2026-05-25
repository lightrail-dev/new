# Dual-ASIC Accelerator Board — Inter-Chip Bridge Architecture

**Revision:** 1.0
**Date:** 2026-05-25
**Author:** LightRail AI Hardware Team

---

## 1. Overview

The LR-P3A dual-NCE accelerator board features two identical Neural Compute
Engine (NCE) ASICs in a perfectly mirrored topology. Each ASIC can be
configured as **Node A** (left) or **Node B** (right) via a single hardware
strap pin (`NODE_ID`). The two NCEs communicate through a high-density,
ultra-low-latency, point-to-point **central bridge interface** with
matched trace lengths (visible as the central fan-out structure in the
board layout).

---

## 2. Inter-Chip Bridge Pinout

The bridge interface is a 64-bit source-synchronous DDR parallel bus with
credit-based flow control. All differential pairs are length-matched to
±0.15 mm on Megtron-7 symmetric stripline (layers In5.Cu / In6.Cu).

| Signal Group       | Width | Direction (Node A→B) | Impedance | Notes                          |
| ------------------ | ----- | -------------------- | --------- | ------------------------------ |
| `BRG_DATA[63:0]`   | 64    | Bidirectional (TDD)  | 85 Ω diff | Source-synchronous DDR         |
| `BRG_CLK_P/N`      | 1     | Unidirectional       | 100 Ω diff| Forwarded clock, 500 MHz       |
| `BRG_CREDIT[3:0]`  | 4     | Reverse              | 50 Ω SE   | Credit return channel          |
| `BRG_VALID`        | 1     | Forward              | 50 Ω SE   | Data-valid strobe              |
| `BRG_ACK`          | 1     | Reverse              | 50 Ω SE   | Packet acknowledge             |
| `BRG_ERR`          | 1     | Reverse              | 50 Ω SE   | CRC error flag (triggers retry)|
| `BRG_RST_N`        | 1     | Bidirectional (OD)   | —         | Open-drain reset               |
| GND                | ≥32   | —                    | —         | Return path, shielding         |
| **Total PCB pins** | **104**|                      |           |                                |

### 2.1 Clocking

- **Forwarded clock:** 500 MHz differential (1.0 GT/s SDR, 2.0 GT/s DDR).
- **Effective bandwidth:** 64 bits × 2 (DDR) × 500 MHz = **64 Gbps** raw,
  ~58 Gbps usable after packet overhead and CRC.
- **Clock-data alignment:** Source-synchronous with ¼-cycle centering at
  the receiver (calibrated at boot via DLL in the bridge controller).

### 2.2 Packet Format

```
┌──────────┬──────────┬────────────────────────┬──────────┐
│ Header   │ Address  │ Payload (0–8 beats)    │ CRC-32   │
│ [7:0]    │ [31:0]   │ [64b × N beats]        │ [31:0]   │
└──────────┴──────────┴────────────────────────┴──────────┘
```

| Field     | Bits  | Description                                       |
| --------- | ----- | ------------------------------------------------- |
| Header    | 8     | Packet type, credit class, sequence number [2:0]  |
| Address   | 32    | Destination register / memory address              |
| Payload   | 0–512 | 0 to 8 × 64-bit data beats                        |
| CRC-32    | 32    | IEEE 802.3 CRC over header + address + payload     |

### 2.3 Credit-Based Flow Control

- **Credit pool:** 16 credits per direction, each credit = 1 packet slot
  in the receiver FIFO.
- **Return path:** 4-bit `BRG_CREDIT` bus returns credits asynchronously.
- **Backpressure:** Transmitter stalls when credit count reaches zero.

---

## 3. Host Interface (AXI4-Lite)

Each NCE exposes an AXI4-Lite target interface to the PCIe Gen 6 root
complex for configuration, DMA descriptor injection, and interrupt handling.

| Register Block         | Base Address    | Size   | Function                       |
| ---------------------- | --------------- | ------ | ------------------------------ |
| Bridge Control/Status  | `0x0000_0000`  | 256 B  | Bridge enable, loopback, stats |
| DMA Descriptors        | `0x0000_0100`  | 1 KB   | Scatter-gather DMA rings       |
| Interrupt Controller   | `0x0000_0400`  | 64 B   | IRQ mask, status, clear        |
| Power Management       | `0x0000_0800`  | 256 B  | DVFS, thermal, PMBus telemetry |
| Node Discovery         | `0x0000_1000`  | 64 B   | Node ID, partner status, FW rev|

---

## 4. Power Delivery Network Topology

```
12 V input (12VHPWR 600 W connector)
    │
    ├── VRM Left (24-phase ISL69260 + ISL99390 DrMOS)
    │   └── V_CORE_A  0.8 V @ 1000 A+ → NCE A
    │
    ├── VRM Right (24-phase ISL69260 + ISL99390 DrMOS)
    │   └── V_CORE_B  0.8 V @ 1000 A+ → NCE B
    │
    └── Aux buck/LDO tree
        ├── 3.3 V  (PCIe, JTAG, I/O)
        ├── 1.8 V  (HBM4 VPP, LVDS)
        ├── 1.2 V  (SerDes analog)
        ├── 1.05 V (VDD_IO)
        └── 0.9 V  (TFLN RF drive)
```

### 4.1 PMBus Telemetry

The digital `pwr_mgt_controller` inside each NCE monitors all power rails
via a PMBus/I2C master connected to the VRM controllers and on-die thermal
diodes. DVFS state transitions:

| DVFS Level | V_CORE | Frequency | Power Envelope |
| ---------- | ------ | --------- | -------------- |
| TURBO      | 0.85 V | 2.0 GHz   | 900 W          |
| NOMINAL    | 0.80 V | 1.8 GHz   | 750 W          |
| LOW_POWER  | 0.72 V | 1.2 GHz   | 400 W          |
| EMERGENCY  | 0.65 V | 0.8 GHz   | 250 W          |

---

## 5. RTL Module Hierarchy

```
nce_top (rtl/top/nce_top.sv)
├── chip_to_chip_bridge (rtl/bridge/chip_to_chip_bridge.sv)
│   ├── bridge_tx (rtl/bridge/bridge_tx.sv)
│   ├── bridge_rx (rtl/bridge/bridge_rx.sv)
│   ├── crc32_engine (rtl/common/crc32_engine.sv)
│   ├── retry_buffer (rtl/bridge/retry_buffer.sv)
│   └── credit_manager (rtl/bridge/credit_manager.sv)
├── host_interface (rtl/host/host_interface.sv)
│   ├── axi4lite_target (rtl/host/axi4lite_target.sv)
│   ├── dma_engine (rtl/host/dma_engine.sv)
│   └── interrupt_controller (rtl/host/interrupt_controller.sv)
├── pwr_mgt_controller (rtl/pwr/pwr_mgt_controller.sv)
│   ├── i2c_master (rtl/pwr/i2c_master.sv)
│   └── dvfs_fsm (rtl/pwr/dvfs_fsm.sv)
└── async_fifo (rtl/common/async_fifo.sv)
```

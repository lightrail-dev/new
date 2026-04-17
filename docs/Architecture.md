# LightRail AI Compute Node — System Architecture

## 1. Block diagram

```
                 ┌───────────── FRONT PANEL ─────────────┐
                 │  MPO-24 Optical  |  Status LEDs  |  USB-C BMC  │
                 └────────┬───────────────────────┬────────────────┘
                          │ 8 TX / 8 RX / monitor │
              ┌───────────┴───────┐       ┌───────┴───────────┐
              │ Optical Engine A   │       │ Optical Engine B   │
              │ 8× DFB 1550 nm +   │       │ 8× DFB 1550 nm +   │
              │ TEC + PD + TIA     │       │ TEC + PD + TIA     │
              └─────┬───────┬──────┘       └─────┬───────┬─────┘
                    │ RF    │ BIAS               │ RF    │ BIAS
                    ▼       ▼                    ▼       ▼
              ┌──────────────────┐         ┌──────────────────┐
              │ TFLN PIC A        │         │ TFLN PIC B        │
              │ 8 ch × 200G PAM4  │         │ 8 ch × 200G PAM4  │
              │ (1.6 Tbps aggreg) │         │ (1.6 Tbps aggreg) │
              └────────┬─────────┘         └────────┬─────────┘
                       │ RF diff drive              │ RF diff drive
                       ▼                            ▼
     ┌──────────────────────────┐        ┌──────────────────────────┐
     │ AI SoC A                 │◀──PCIe Gen 6 x16──▶│ PCIe Switch   │
     │ BGA-2500, 40×40, 0.8mm   │        │ AI SoC B                 │
     │ — TFLN SerDes (16×)      │        │ BGA-2500, 40×40, 0.8mm   │
     │ — DDR5 PHY (4 ch)        │        │ — same as A              │
     │ — PCIe Gen 6 root (x32)  │        └──────┬──────┬────────────┘
     │ — V_core: 0.8 V, 1000 A  │               │      │
     └──┬───┬───┬───┬────┬──────┘               │      │
        │   │   │   │    │                       │      │
        │   │   │   │    └── PCIe Gen 6 edge ───►│      │── NVMe M.2 / U.3
        │   │   │   │                                   │
        │   │   │   └───── DDR5-8800 Ch3 DIMM ─┐        │
        │   │   └──────── DDR5-8800 Ch2 DIMM ─┤        │
        │   └─────────── DDR5-8800 Ch1 DIMM ─┤        │
        └──────────────── DDR5-8800 Ch0 DIMM ─┘        │
                                                       │
                                         EC / PMBus / I²C / SPI flash
                                                       │
                                                       ▼
                                               System Management
                                          (BMC, sensors, fan ctl, TPM)

  Power input: 12 V ── 2× 24-phase DrMOS VRM (ISL69260 + ISL99390) ─► V_core
                    └─ LDO/buck tree ─► 3.3 V, 1.8 V, 1.2 V, 1.05 V, 0.9 V
```

## 2. Functional specification

### 2.1 Compute

| Parameter                 | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| AI SoC count              | 2                                                              |
| SoC package               | BGA-2500 (50 × 50 grid, 40 mm × 40 mm, 0.8 mm pitch)           |
| SoC V_core                | 0.8 V typ., 1000 A+ peak per SoC                               |
| SoC I/O                   | VDD_IO 1.05 V / 1.2 V, VDDQ 1.1 V (DDR5)                       |
| PCIe root                 | Gen 6.0, x32 per SoC (split x16 + x16)                         |
| DDR5 channels             | 4 per SoC, DDR5-8800 (4400 MT/s clock)                          |
| TFLN SerDes               | 16 lanes @ 200 G PAM4 per SoC (8 TX + 8 RX)                    |
| Power target (peak)       | 800 W per SoC (V_core) + 100 W (I/O + mem) = 900 W per SoC     |

### 2.2 Photonics

| Parameter                 | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| Modulator type            | Thin-Film Lithium Niobate (TFLN), Mach-Zehnder, push-pull       |
| Channels                  | 8 per PIC, 2 PICs (16 total)                                   |
| Wavelength                | 1550 nm C-band DWDM grid, 100 GHz spacing                      |
| Line rate                 | 200 Gbps PAM4 per lane                                         |
| Aggregate BW              | 16 × 200 G = **1.6 Tbps** (half-duplex), 3.2 Tbps FD equivalent |
| Vπ · L                    | ~2.5 V · cm (typical TFLN)                                      |
| RF drive                  | ±1.5 V differential, 50 Ω terminated                           |
| Laser                     | 1550 nm DFB, 20 mW, TEC + thermistor                           |
| Detector                  | InGaAs PIN-PD, TIA (on TFLN carrier or chiplet)                |
| Optical connector         | MPO-24 (16 fiber SM + 8 fiber monitor/cal)                      |

### 2.3 Memory

| Parameter                 | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| DIMMs                     | Up to 4 per channel × 4 channels × 2 SoCs = 32 max (1 DPC min) |
| Speed                     | DDR5-8800 (JEDEC target)                                        |
| Topology                  | Fly-by CA/CLK, T-branch DQ, on-DIMM RCD                        |
| ODT / termination         | On-die; VTT derived from VPP                                   |
| VDDQ / VPP                | 1.1 V / 1.8 V                                                  |

### 2.4 PCIe

| Parameter                 | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| Generation                | PCIe Gen 6.0 (64 GT/s per lane, PAM4)                          |
| Edge connectors           | 1 × x16 primary, 1 × x16 expansion (via switch or direct)      |
| Retimers                  | Required (e.g. ASTERA PT6, MONTAGE M88RT51632); NDA parts      |
| Reference clock           | 100 MHz LP-HCSL, SRC0..1                                       |

### 2.5 Power

| Rail                      | Source                  | Voltage | Current (peak) | Regulator              |
| ------------------------- | ----------------------- | ------- | -------------- | ---------------------- |
| +12 V input               | PCIe 12VHPWR (600 W×2)  | 12 V    | 150 A          | —                      |
| V_core A / B              | 24-phase DrMOS          | 0.8 V   | 1000 A+        | ISL69260 + 24× ISL99390 |
| VDD_IO                    | Multi-phase buck        | 1.05 V  | 40 A           | TPS543C20 × 4          |
| VDDQ (DDR5)               | Buck                    | 1.1 V   | 40 A           | TPS544C20              |
| VPP (DDR5)                | Buck                    | 1.8 V   | 8 A            | TPS62810               |
| 3.3 V aux                 | Buck                    | 3.3 V   | 15 A           | TPS54360               |
| 1.8 V aux                 | LDO                     | 1.8 V   | 3 A            | TPS7A20                |
| 1.2 V aux                 | LDO                     | 1.2 V   | 2 A            | TPS7A20                |
| 0.9 V (TFLN RF)           | LDO, low-noise          | 0.9 V   | 1 A            | ADP7118-0.9 (fixed)    |

### 2.6 Management

- **BMC / EC:** AST2600 or MEC172x (footprint placeholder)
- **PMBus:** VRM telemetry (V, I, T, phase count) @ 400 kHz
- **I²C:** DIMM SPD, TFLN TEC driver, sensors
- **SPI flash:** UEFI/BIOS + BMC firmware, redundant (A/B)
- **TPM 2.0:** SLB 9670 on LPC/SPI
- **Sensors:** 6× thermal diodes (2 per SoC, 1 per VRM, 1 inlet)
- **Fans / pump:** 4× PWM PWM tach, direct-to-chip header

## 3. Power budget

| Domain                    | Typical | Peak  |
| ------------------------- | ------- | ----- |
| SoC A V_core              | 400 W   | 800 W |
| SoC B V_core              | 400 W   | 800 W |
| SoC I/O + TFLN RF (both)  | 80 W    | 140 W |
| DDR5 (up to 32 DIMM)      | 120 W   | 200 W |
| PCIe retimers + switch    | 25 W    | 40 W  |
| BMC + aux                 | 15 W    | 20 W  |
| **Total**                 | **1040 W** | **2000 W** |

## 4. Signal-flow notes

- **Host path:** PCIe Gen 6 edge → retimer → SoC root complex. Max trace +
  retimer insertion loss budget: 32 dB @ Nyquist (16 GHz), per PCIe 6.0 CEM.
- **Optical TX path:** SoC SerDes → TFLN RF drive (differential, 100 Ω diff) →
  TFLN modulator → DFB laser bias tee → MPO-24.
- **Optical RX path:** MPO-24 → PD array → TIA → SoC SerDes RX.
- **DDR5 CA/CLK:** Fly-by to DIMM slots, matched length ±2 mil per rank.
- **DDR5 DQ/DQS:** Point-to-point SoC ↔ DIMM, matched within byte lane ±2 mil.
- **V_core:** Plane-to-plane delivery; ≥4 mΩ target DC, <1 mΩ AC @ 1 MHz–100 MHz.

## 5. Clock tree

```
12 MHz XTAL ─► Si5395A (jitter cleaner) ─┬─► 100 MHz HCSL → PCIe REFCLK (4×)
                                         ├─► 156.25 MHz LVPECL → SerDes ref
                                         ├─► 200 MHz LVDS → DDR5 PHY PLL
                                         └─► 10 MHz sync → TFLN DAC trigger
```

Jitter budget: <100 fs RMS (10 kHz – 20 MHz) for PCIe Gen 6 REFCLK.

## 6. Thermal plan summary

- Liquid cold plate on each SoC (expected TDP 800 W peak).
- Airflow across VRM inductors (each 30 A × 0.4 mΩ DCR = 0.36 W × 24 = 8.6 W per VRM).
- TFLN PIC held at 25 ± 2 °C via TEC.
- Inlet air or coolant ≤ 45 °C; full spec in `docs/SI_PI_Thermal_Plan.md` §3.

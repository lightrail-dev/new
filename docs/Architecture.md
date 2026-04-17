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
     │ NCE A + 4× HBM4          │◀──PCIe Gen 6 x16──▶│ PCIe Switch   │
     │ (co-packaged on silicon  │        │ NCE B + 4× HBM4          │
     │  interposer, BGA-2500)   │        │ (same composite module)  │
     │ — NCE die, 40×40, 0.8mm  │        │ — same as A              │
     │ — 4× HBM4 12-Hi stacks   │        └──────┬──────┬────────────┘
     │ — TFLN SerDes (16×)      │               │      │
     │ — PCIe Gen 6 root (x32)  │               │      │── NVMe M.2 / U.3
     │ — V_core: 0.8 V, 1000 A+ │               │      │
     └─────────────┬────────────┘               │      │
                   │                            │      │
                   │ 1024-lane HBM4 data bus is INTERNAL to the interposer
                   │ (never reaches PCB copper). PCB only carries HBM4
                   │ side-channel signals: REFCK_P/N, CATTRIP, PWR_GOOD,
                   │ IEEE1500 test bus (TCK/TMS/TDI/TDO), and the
                   │ VDDC/VDDQL/VDDQ/VPP power rails into the module BGA.
                   └── PCIe Gen 6 edge ──────────┘
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
| SoC package               | BGA-2500 composite (NCE + interposer + 4× HBM4), 40 × 40 mm    |
| SoC V_core                | 0.8 V typ., 1000 A+ peak per module (NCE + 4× HBM4 combined)   |
| SoC I/O                   | VDD_IO 1.05 V / 1.2 V, HBM4 VDDQ 1.1 V                         |
| PCIe root                 | Gen 6.0, x32 per SoC (split x16 + x16)                         |
| Memory                    | 4× HBM4 12-Hi per module (interposer-coupled, see §2.3)        |
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

### 2.3 Memory (HBM4, co-packaged)

| Parameter                 | Value                                                          |
| ------------------------- | -------------------------------------------------------------- |
| Topology                  | HBM4 on silicon interposer, co-packaged with NCE as single BGA |
| Stacks per module         | 4 × HBM4 12-Hi, 48 GB per stack → 192 GB per module            |
| Modules                   | 2 (one per NCE) → 384 GB aggregate                             |
| Data bus per stack        | 1024 lanes @ 8 Gbps/pin (1.0 TB/s per stack, 4.0 TB/s/module)  |
| Data-bus routing          | Entirely INTERPOSER-INTERNAL — never reaches PCB copper        |
| PCB-routed side-channel   | REFCK_P/N, CATTRIP, PWR_GOOD, IEEE1500 (TCK/TMS/TDI/TDO)       |
| Power rails (into module) | VDDC 0.7 V, VDDQL 0.4 V, VDDQ 1.1 V, VPP 1.8 V, VSS            |
| Interposer                | Vendor-supplied (TSMC CoWoS-L / Intel Foveros-S class); board  |
|                           | sees only the composite BGA footprint + side-channel pins      |

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
| VDDC (HBM4)               | Buck                    | 0.7 V   | 60 A           | TPS543C20              |
| VDDQL (HBM4)              | Buck                    | 0.4 V   | 30 A           | TPS543C20              |
| VDDQ (HBM4)               | Buck                    | 1.1 V   | 40 A           | TPS544C20              |
| VPP (HBM4)                | Buck                    | 1.8 V   | 8 A            | TPS62810               |
| 3.3 V aux                 | Buck                    | 3.3 V   | 15 A           | TPS54360               |
| 1.8 V aux                 | LDO                     | 1.8 V   | 3 A            | TPS7A20                |
| 1.2 V aux                 | LDO                     | 1.2 V   | 2 A            | TPS7A20                |
| 0.9 V (TFLN RF)           | LDO, low-noise          | 0.9 V   | 1 A            | ADP7118-0.9 (fixed)    |

### 2.6 Management

- **BMC / EC:** AST2600 or MEC172x (footprint placeholder)
- **PMBus:** VRM telemetry (V, I, T, phase count) @ 400 kHz
- **I²C:** HBM4 module SPD/ID (via module BGA), TFLN TEC driver, sensors
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
| HBM4 (8 stacks, 2 mods)   | 120 W   | 200 W |
| PCIe retimers + switch    | 25 W    | 40 W  |
| BMC + aux                 | 15 W    | 20 W  |
| **Total**                 | **1040 W** | **2000 W** |

## 4. Signal-flow notes

- **Host path:** PCIe Gen 6 edge → retimer → SoC root complex. Max trace +
  retimer insertion loss budget: 32 dB @ Nyquist (16 GHz), per PCIe 6.0 CEM.
- **Optical TX path:** SoC SerDes → TFLN RF drive (differential, 100 Ω diff) →
  TFLN modulator → DFB laser bias tee → MPO-24.
- **Optical RX path:** MPO-24 → PD array → TIA → SoC SerDes RX.
- **HBM4 side-channel (PCB):** REFCK_P/N differential pair (100 Ω) ±2 mil; CATTRIP / PWR_GOOD routed as single-ended slow status signals; IEEE1500 JTAG routed as 50 Ω SE with series-term.
- **HBM4 data bus:** NOT on PCB — 1024 lanes × 4 stacks = 4096 lanes per module routed inside the vendor-supplied silicon interposer.
- **V_core:** Plane-to-plane delivery; ≥4 mΩ target DC, <1 mΩ AC @ 1 MHz–100 MHz.

## 5. Clock tree

```
12 MHz XTAL ─► Si5395A (jitter cleaner) ─┬─► 100 MHz HCSL → PCIe REFCLK (4×)
                                         ├─► 156.25 MHz LVPECL → SerDes ref
                                         ├─► 200 MHz LVDS → HBM4 REFCK (per stack)
                                         └─► 10 MHz sync → TFLN DAC trigger
```

Jitter budget: <100 fs RMS (10 kHz – 20 MHz) for PCIe Gen 6 REFCLK.

## 6. Thermal plan summary

- Liquid cold plate on each SoC (expected TDP 800 W peak).
- Airflow across VRM inductors (each 30 A × 0.4 mΩ DCR = 0.36 W × 24 = 8.6 W per VRM).
- TFLN PIC held at 25 ± 2 °C via TEC.
- Inlet air or coolant ≤ 45 °C; full spec in `docs/SI_PI_Thermal_Plan.md` §3.

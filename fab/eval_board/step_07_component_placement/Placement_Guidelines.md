# Step 7: Component Placement
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Placement Priority Order

Components are placed in strict priority order to optimize signal integrity, thermal performance, and manufacturability:

| Priority | Component Group | Placement Constraint |
|----------|----------------|---------------------|
| 1 | **Fixed-position items** | Connectors at board edges, mounting holes at corners |
| 2 | **TFLN optical module (U3)** | Left edge — fiber exit aligned to board edge ±50 µm |
| 3 | **NCE test chip (U1)** | Center-left — minimum trace length to TFLN and FPGA |
| 4 | **FPGA (U2)** | Center-right — close to NCE for AXI bus, near JTAG/GPIO headers |
| 5 | **Si5395A PLL (U20)** | Between U1 and U2 — equal-length clock distribution |
| 6 | **Power regulators** | Near board edges — heat dissipation, away from sensitive analog |
| 7 | **Decoupling capacitors** | Within 2 mm of each IC power pin |
| 8 | **ADC/DAC (U21/U24)** | Near TFLN — short analog traces |
| 9 | **USB/UART bridge (U22)** | Near USB-C connector (J2) |
| 10 | **SPI flash (U23)** | Near FPGA — short SPI bus |
| 11 | **Test points, LEDs** | Accessible locations, board edges |

## 2. Detailed Placement Map

```
     ← 100 mm →
 ┌──────────────────────────────────────────────────┐
 │ MH1    J7(SMA)  J8(SMA)  J9(SMA)  J10(SMA) MH2 │ Top edge
 │  ○      ╤         ╤        ╤        ╤      ○    │ (SMA RF probes)
 │         │         │        │        │            │
 │   TP1-TP6 (power rail test points along top)     │
 │                                                   │
 │  ┌────────┐  ┌────────┐ U20  ┌──────────────┐   │
 │  │ U3     │  │        │ PLL  │              │   │
MPO │ TFLN   │  │  U1    │ [□]  │    U2        │ J5│ JTAG
J11 │ PIC    │  │  NCE   │      │   FPGA       │ ■ │
 │  │ 12×6mm │  │ QFN-64 │      │  BGA-256     │   │
 │  │        │  │ 8×8mm  │      │  14×14mm     │ J6│ GPIO
 │  └────────┘  │        │      │              │ ■ │
 │    U24[DAC]  └────────┘      └──────────────┘   │
 │    U21[ADC]                    U23[Flash]        │
 │                                                   │
 │  ┌─────┐                                         │
 │  │U15  │ (Buck 5V)   U10  U11  U12  U13  U14   │ (LDOs)
 │  │TPS  │               □    □    □    □    □    │
 │  └─────┘                                         │
 │  D1-D4                                           │
 │  ● ● ● ● (LEDs)     U22[FT232H]  U25[Temp]    │
 │                        ┌───┐                     │
 │  J1(12V) J3(2pin)      │USB│                     │
 │  ⊙        ■             └───┘                    │ Bottom edge
 │ MH3        SW1(Reset)    J2(USB-C)          MH4 │
 │  ○                                           ○  │
 └──────────────────────────────────────────────────┘
```

## 3. Critical Placement Rules

### 3.1 NCE Test Chip (U1)

| Rule | Requirement |
|------|-------------|
| Distance to U3 (TFLN) | ≤ 25 mm (RF trace length budget) |
| Distance to U2 (FPGA) | ≤ 30 mm (AXI bus length) |
| Decoupling caps | 8× 100nF 0402 within 1.5 mm of VDD_CORE/VDD_IO pins |
| Thermal vias | 16× under exposed pad, connected to GND on In1.Cu |
| Orientation | Pin 1 top-left, dot marker on silkscreen |

### 3.2 TFLN PIC Module (U3)

| Rule | Requirement |
|------|-------------|
| Board edge alignment | Fiber exit flush with left board edge (±50 µm) |
| Copper keep-out | 2.0 mm around fiber exit on ALL copper layers |
| RF trace entry | Ground-signal-ground pads facing U1 direction |
| Bias/monitor traces | Routed to U24/U21 (≤ 15 mm) |

### 3.3 FPGA (U2)

| Rule | Requirement |
|------|-------------|
| Decoupling caps | 24× 100nF 0402 + 8× 4.7uF 0402 within 2 mm of power balls |
| 4× 1uF 0402 on VCCINT, 4× on VCCAUX | |
| SPI flash (U23) | Within 15 mm — short SPI bus |
| JTAG header (J5) | Within 20 mm — accessible at board edge |
| BGA escape | Via-in-pad with filled+capped vias (0.3mm drill) |

### 3.4 Clock Generator (U20 — Si5395A)

| Rule | Requirement |
|------|-------------|
| Position | Between U1 and U2 for equal-length clock distribution |
| 2 GHz output to U1 | Stripline on In2.Cu, length ≤ 20 mm |
| 100 MHz output to U2 | Microstrip on F.Cu, length ≤ 25 mm |
| Decoupling | 4× 100nF + 2× 10nF within 1 mm of VDD pins |
| Guard ring | GND copper pour around U20 on F.Cu |

### 3.5 Power Regulators

| Rule | Requirement |
|------|-------------|
| U15 (Buck 5V) | Bottom-left quadrant, away from sensitive analog |
| Inductor L1 | Within 5 mm of U15 SW pin |
| Input caps (C1, C11) | Within 3 mm of U15 VIN |
| LDOs (U10–U14) | Bottom edge, downstream of U15 |
| Thermal relief | LDO tab pads connected to GND via thermal vias |

## 4. Thermal Considerations

| Component | Power (est.) | Thermal Strategy |
|-----------|-------------|-----------------|
| U1 (NCE) | 205 mW | 16× thermal vias + GND plane spreading, optional heatsink |
| U2 (FPGA) | 700 mW | Via-in-pad BGA, GND plane spreading |
| U15 (Buck) | 100 mW | Exposed pad thermal vias + copper pour |
| U3 (TFLN) | 50 mW | TEC control loop, thermal monitoring |
| Total board | ~2.5 W | Adequate for natural convection + optional fan |

## 5. Assembly Orientation

| Side | Components | Notes |
|------|-----------|-------|
| Top (F.Cu) | All active ICs, most passives, connectors | Primary assembly side |
| Bottom (B.Cu) | 8× decoupling caps (FPGA), thermal vias | Secondary — reflow compatible |

**Placement Status: COMPLETE**

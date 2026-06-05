# Step 8: Routing and Planes
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 2.0 (22-Layer Intelligence Stack)

---

## 1. Routing Priority Order

| Priority | Signal Group | Layer(s) | Technique |
|----------|-------------|----------|-----------|
| 1 | **Power delivery** | L11, L17, L21 (planes), L1/L22 (decoupling) | Wide traces + plane fills |
| 2 | **CLK_HBM (2 GHz)** | L4 (stripline between GND L3 and GND L6) | 50 Ω SE, guarded, length ≤ 20 mm |
| 3 | **TFLN RF diff pairs** | L2 (stripline between L1 and GND L3) | 100 Ω diff, AC-coupled, length-matched |
| 4 | **USB Hi-Speed** | L20 (stripline between GND L18 and PWR L21) | 90 Ω diff, length-matched ±0.1 mm |
| 5 | **AXI4-Lite bus** | L10 / L13 (stripline, Logic Core / Comm Prims) | 50 Ω SE, group-matched ±2 mm |
| 6 | **SPI buses** | L1 (microstrip) or L16 (Fabric OS stripline) | 50 Ω SE, length ≤ 30 mm |
| 7 | **I2C, JTAG, GPIO** | L1 or L22 | Default rules |
| 8 | **LEDs, test points** | L1 | Last |

## 2. Power Plane Assignments

### L11 (In10.Cu) — Core Power Plane (+0.9V)

```
┌──────────────────────────────────────────────────┐
│                                                   │
│              ┌───────────────────┐                │
│              │                   │                │
│              │   +0V9 (NCE)      │                │
│              │   ADP7118 output  │                │
│              │                   │                │
│              └───────────────────┘                │
│                                                   │
│           GND fill (remainder)                    │
│                                                   │
└──────────────────────────────────────────────────┘
```

### L17 (In16.Cu) — Digital Power Plane (+1.0V / +1.8V)

```
┌──────────────────────────────────────────────────┐
│                                                   │
│  ┌──────────────────┐  ┌───────────────────────┐ │
│  │  +1V0 (FPGA)     │  │     +1V8 (I/O)        │ │
│  │  TPS7A20 output  │  │     TPS7A20 output    │ │
│  │                  │  │                       │ │
│  └──────────────────┘  └───────────────────────┘ │
│                                                   │
│           GND fill (remainder)                    │
│                                                   │
└──────────────────────────────────────────────────┘
```

### L21 (In20.Cu) — Peripheral Power Plane (+3.3V / +5V)

```
┌──────────────────────────────────────────────────┐
│                                                   │
│  ┌────────┐  ┌────────────────────────────────┐  │
│  │  +5V   │  │        +3V3                    │  │
│  │ TPS543 │  │    TPS7A33 output              │  │
│  │ output │  │                                │  │
│  └────────┘  └────────────────────────────────┘  │
│                                                   │
│           GND fill (remainder)                    │
│                                                   │
└──────────────────────────────────────────────────┘
```

### GND Reference Planes (6 planes — L3, L6, L9, L12, L15, L18)

No splits. No signal routing. Solid copper fill connected to GND.
Thermal relief on via connections (4-spoke, 0.25 mm gap).
Plane integrity is critical for controlled impedance.
Every signal layer has an adjacent solid GND reference.

## 3. Critical Signal Routing Details

### 3.1 CLK_HBM (2.0 GHz) — U20 → U1

| Parameter | Value |
|-----------|-------|
| Layer | L4 / In3.Cu (stripline between GND L3 and GND L6) |
| Trace width | 0.08 mm |
| Impedance | 50 Ω ±10% |
| Max length | 20 mm |
| Guard traces | GND guard on both sides, 0.12 mm gap, stitched every 3 mm |
| Via transitions | Max 1 blind via (L1→L4) |
| No crossing | No other signals cross this trace on adjacent layers |

### 3.2 TFLN RF Differential Pairs (×8) — U1 → U3

| Parameter | Value |
|-----------|-------|
| Layer | L2 / In1.Cu (stripline between L1 and GND L3) |
| Trace width | 0.08 mm |
| Pair gap | 0.10 mm |
| Impedance | 100 Ω differential ±10% |
| Length matching | ±0.1 mm intra-pair, ±1.0 mm inter-pair |
| AC coupling | 100 nF 0201 caps at U3 input (inline, no stubs) |
| Termination | 100 Ω at U3 destination |
| Ground return | Solid GND L3 below, stitching vias at layer transitions |

### 3.3 USB Hi-Speed — J2 → U22

| Parameter | Value |
|-----------|-------|
| Layer | L20 / In19.Cu (stripline between GND L18 and PWR L21) |
| Trace width | 0.09 mm |
| Pair gap | 0.12 mm |
| Impedance | 90 Ω differential ±10% |
| Length matching | ±0.1 mm intra-pair |
| ESD diodes | Placed at J2, before USB traces |
| Series resistors | 22 Ω at U22 side (optional, per FT232H reference) |

### 3.4 AXI4-Lite Bus — U2 ↔ U1

| Parameter | Value |
|-----------|-------|
| Layer | L10 / In9.Cu (Logic Core stripline) or L13 / In12.Cu (Comm Prims) |
| Trace width | 0.12 mm |
| Impedance | 50 Ω SE |
| Group length matching | ±2.0 mm within each AXI channel |
| Max length | 30 mm |
| Bus topology | Point-to-point (no stubs, no tees) |

### 3.5 SPI Buses (Flash, DAC, ADC)

| Parameter | Value |
|-----------|-------|
| Layer | L1 / F.Cu (microstrip) or L16 / In15.Cu (Fabric OS) |
| Trace width | 0.15 mm |
| Max length | 30 mm |
| CLK routing | Series-terminated at source (33 Ω) |

## 4. Via Strategy (22-Layer HDI)

| Via Type | Drill | Pad | Span | Use |
|----------|-------|-----|------|-----|
| Through-hole | 0.25 mm | 0.50 mm | L1–L22 | General signal routing |
| Power through-hole | 0.40 mm | 0.80 mm | L1–L22 | VDD/GND power delivery |
| Blind via (top) | 0.15 mm | 0.40 mm | L1–L6 | Physical Fabric to Core transitions |
| Blind via (bottom) | 0.15 mm | 0.40 mm | L18–L22 | Control Plane to Summit transitions |
| Buried via | 0.20 mm | 0.45 mm | L6–L18 | Core to Control Plane routing |
| BGA escape (via-in-pad) | 0.15 mm | 0.35 mm | L1–L3 | FPGA U2 dog-bone pattern |
| Thermal via | 0.30 mm | 0.60 mm | L1–L22 | Under NCE/FPGA/LDO exposed pads |
| Stitching via | 0.25 mm | 0.50 mm | L1–L22 | GND plane stitching every 5 mm |

## 5. Copper Pour Strategy

| Layer | Pour | Net | Notes |
|-------|------|-----|-------|
| L1 (F.Cu) | Partial fill | GND | Around components, not covering high-speed traces |
| L2 (In1.Cu) | No pour | — | TFLN RF signal layer only |
| L3 (In2.Cu) | Solid plane | GND | GND Reference 1 — no cuts, no routing |
| L4 (In3.Cu) | No pour | — | Laser/WDM signal layer |
| L5 (In4.Cu) | No pour | — | Analog Wave signal layer |
| L6 (In5.Cu) | Solid plane | GND | GND Reference 2 — no cuts, no routing |
| L7 (In6.Cu) | No pour | — | Synaptic Grid signal layer |
| L8 (In7.Cu) | No pour | — | Signal Restoration signal layer |
| L9 (In8.Cu) | Solid plane | GND | GND Reference 3 |
| L10 (In9.Cu) | No pour | — | Logic Core signal layer |
| L11 (In10.Cu) | Split plane | +0V9, GND | Power with 0.5 mm gap |
| L12 (In11.Cu) | Solid plane | GND | GND Reference 4 — board center |
| L13 (In12.Cu) | No pour | — | Communication Primitives signal layer |
| L14 (In13.Cu) | No pour | — | Kernel Integration signal layer |
| L15 (In14.Cu) | Solid plane | GND | GND Reference 5 |
| L16 (In15.Cu) | No pour | — | Fabric OS signal layer |
| L17 (In16.Cu) | Split plane | +1V0, +1V8, GND | Power with 0.5 mm gap |
| L18 (In17.Cu) | Solid plane | GND | GND Reference 6 |
| L19 (In18.Cu) | No pour | — | Scheduler signal layer |
| L20 (In19.Cu) | No pour | — | Framework signal layer |
| L21 (In20.Cu) | Split plane | +5V, +3V3, GND | Power with 0.5 mm gap |
| L22 (B.Cu) | Partial fill | GND | Bottom-side decoupling return path |

## 6. Routing Rules Summary

| Rule | Value |
|------|-------|
| Use 45° angles only | Yes (no acute angles) |
| Minimize via count | Max 3 vias per net (typical for 22L HDI) |
| No trace under crystal/TCXO | Yes — guarded region |
| No trace crossing high-speed pairs | Yes — no perpendicular crossings on adjacent layers |
| Return path continuity | Stitching via at every layer transition within 2 mm |
| Diff pair spacing from other nets | ≥ 3× trace width |
| Power trace current budget | 0.5 mm = 300 mA (1 oz inner), 1.0 mm = 700 mA (1 oz outer) |
| Back-drilling | Required for through-vias on L2 TFLN RF signals (stub ≤ 0.2 mm) |
| Blind/buried via usage | Preferred over through-vias for signal integrity |

**Routing Status: COMPLETE (Rev 2.0 — 22-Layer)**

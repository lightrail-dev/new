# Step 8: Routing and Planes
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Routing Priority Order

| Priority | Signal Group | Layer(s) | Technique |
|----------|-------------|----------|-----------|
| 1 | **Power delivery** | In3.Cu, In4.Cu (planes), F.Cu/B.Cu (decoupling) | Wide traces + plane fills |
| 2 | **CLK_HBM (2 GHz)** | In2.Cu (stripline) | 50 Ω SE, guarded, length ≤ 20 mm |
| 3 | **TFLN RF diff pairs** | In5.Cu (stripline) | 100 Ω diff, AC-coupled, length-matched |
| 4 | **USB Hi-Speed** | In5.Cu (stripline) | 90 Ω diff, length-matched ±0.1 mm |
| 5 | **AXI4-Lite bus** | F.Cu / In2.Cu | 50 Ω SE, group-matched ±2 mm |
| 6 | **SPI buses** | F.Cu | 50 Ω SE, length ≤ 30 mm |
| 7 | **I2C, JTAG, GPIO** | F.Cu | Default rules |
| 8 | **LEDs, test points** | F.Cu | Last |

## 2. Power Plane Assignments

### In3.Cu — Core Power Plane

```
┌──────────────────────────────────────────────────┐
│                                                   │
│    ┌───────────────────┐  ┌───────────────────┐  │
│    │                   │  │                   │  │
│    │   +0V9 (NCE)      │  │    +1V0 (FPGA)    │  │
│    │   ADP7118 output  │  │    TPS7A20 output │  │
│    │                   │  │                   │  │
│    └───────────────────┘  └───────────────────┘  │
│                                                   │
│           GND fill (remainder)                    │
│                                                   │
└──────────────────────────────────────────────────┘
```

### In4.Cu — Auxiliary Power Plane

```
┌──────────────────────────────────────────────────┐
│                                                   │
│  ┌────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  +5V   │  │  +1V8    │  │     +3V3         │ │
│  │ TPS543 │  │ TPS7A20  │  │    TPS7A33       │ │
│  │ output │  │ output   │  │    output         │ │
│  └────────┘  └──────────┘  └──────────────────┘ │
│                                                   │
│           GND fill (remainder)                    │
│                                                   │
└──────────────────────────────────────────────────┘
```

### In1.Cu and In6.Cu — Solid GND Reference Planes

No splits. No signal routing. Solid copper fill connected to GND.
Thermal relief on via connections (4-spoke, 0.25 mm gap).
Plane integrity is critical for controlled impedance.

## 3. Critical Signal Routing Details

### 3.1 CLK_HBM (2.0 GHz) — U20 → U1

| Parameter | Value |
|-----------|-------|
| Layer | In2.Cu (stripline between In1 GND and In3 power) |
| Trace width | 0.10 mm |
| Impedance | 50 Ω ±10% |
| Max length | 20 mm |
| Guard traces | GND guard on both sides, 0.15 mm gap, stitched every 3 mm |
| Via transitions | Max 1 via (U20 BGA escape → In2 → U1 QFN pad) |
| No crossing | No other signals cross this trace on adjacent layers |

### 3.2 TFLN RF Differential Pairs (×8) — U1 → U3

| Parameter | Value |
|-----------|-------|
| Layer | In5.Cu (stripline between In4 power and In6 GND) |
| Trace width | 0.10 mm |
| Pair gap | 0.15 mm |
| Impedance | 100 Ω differential ±10% |
| Length matching | ±0.1 mm intra-pair, ±1.0 mm inter-pair |
| AC coupling | 100 nF 0201 caps at U3 input (inline, no stubs) |
| Termination | 100 Ω at U3 destination |
| Ground return | Solid In6.Cu GND below, stitching vias at layer transitions |

### 3.3 USB Hi-Speed — J2 → U22

| Parameter | Value |
|-----------|-------|
| Layer | In5.Cu (stripline) |
| Trace width | 0.11 mm |
| Pair gap | 0.15 mm |
| Impedance | 90 Ω differential ±10% |
| Length matching | ±0.1 mm intra-pair |
| ESD diodes | Placed at J2, before USB traces |
| Series resistors | 22 Ω at U22 side (optional, per FT232H reference) |

### 3.4 AXI4-Lite Bus — U2 ↔ U1

| Parameter | Value |
|-----------|-------|
| Layer | F.Cu (microstrip), In2.Cu (stripline for inner signals) |
| Trace width | 0.12 mm |
| Impedance | 50 Ω SE |
| Group length matching | ±2.0 mm within each AXI channel |
| Max length | 30 mm |
| Bus topology | Point-to-point (no stubs, no tees) |

### 3.5 SPI Buses (Flash, DAC, ADC)

| Parameter | Value |
|-----------|-------|
| Layer | F.Cu (microstrip) |
| Trace width | 0.15 mm |
| Max length | 30 mm |
| CLK routing | Series-terminated at source (33 Ω) |

## 4. Via Strategy

| Via Type | Drill | Pad | Use |
|----------|-------|-----|-----|
| Standard through-hole | 0.30 mm | 0.60 mm | General signal routing |
| Power via | 0.40 mm | 0.80 mm | VDD/GND power delivery |
| BGA escape (via-in-pad) | 0.25 mm | 0.50 mm | FPGA U2 dog-bone pattern |
| Thermal via | 0.30 mm | 0.60 mm | Under NCE/FPGA/LDO exposed pads |
| Stitching via | 0.25 mm | 0.50 mm | GND plane stitching every 5 mm |

## 5. Copper Pour Strategy

| Layer | Pour | Net | Notes |
|-------|------|-----|-------|
| F.Cu | Partial fill | GND | Around components, not covering high-speed traces |
| In1.Cu | Solid plane | GND | No cuts, no signal routing |
| In2.Cu | No pour | — | Signal layer only |
| In3.Cu | Split plane | +0V9, +1V0, GND | Plane splits with 0.5 mm gap |
| In4.Cu | Split plane | +5V, +1V8, +3V3, GND | Plane splits with 0.5 mm gap |
| In5.Cu | No pour | — | Signal layer only |
| In6.Cu | Solid plane | GND | No cuts, no signal routing |
| B.Cu | Partial fill | GND | Bottom-side decoupling return path |

## 6. Routing Rules Summary

| Rule | Value |
|------|-------|
| Use 45° angles only | Yes (no acute angles) |
| Minimize via count | Max 2 vias per net (typical) |
| No trace under crystal/TCXO | Yes — guarded region |
| No trace crossing high-speed pairs | Yes — no perpendicular crossings on adjacent layers |
| Return path continuity | Stitching via at every layer transition within 2 mm |
| Diff pair spacing from other nets | ≥ 3× trace width |
| Power trace current budget | 0.5 mm = 300 mA (1 oz inner), 1.0 mm = 700 mA (1 oz outer) |

**Routing Status: COMPLETE**

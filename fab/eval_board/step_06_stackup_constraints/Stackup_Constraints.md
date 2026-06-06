# Step 6: Stackup / Constraints Setting
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 2.0 (22-Layer Intelligence Stack)

---

## 1. Layer Stackup (22-Layer Intelligence Stack)

The evaluation board uses a 22-layer stackup mapped directly to the LightRail Intelligence Stack architecture. Each PCB layer corresponds to a functional tier in the 22-layer system model, providing dedicated signal/power/ground planes with maximum isolation between analog, digital, and optical domains.

```
══════════════════════════════════════════════════════════════════════════════════════
 PCB     Stack    KiCad       Cu Wt       Diel.   Material            Function
 Layer   Layer    Name        (oz)        (µm)
══════════════════════════════════════════════════════════════════════════════════════
 L1      L1       F.Cu        1 oz ENIG    —      —                   Physical Fabric (top components)
                              prepreg      75     Megtron-7 (εr=3.3)
 L2      L2       In1.Cu      0.5 oz       —      —                   TFLN Interconnect (RF diff pairs)
                              core         75     Megtron-7 (εr=3.3)
 L3      —        In2.Cu      1 oz         —      —                   GND Reference 1 (solid)
                              prepreg      75     Megtron-7 (εr=3.3)
 L4      L3–4     In3.Cu      0.5 oz       —      —                   Laser/WDM signal routing
                              core         75     Megtron-7 (εr=3.3)
 L5      L5       In4.Cu      0.5 oz       —      —                   Analog Wave Compute signals
                              prepreg      75     Megtron-7 (εr=3.3)
 L6      —        In5.Cu      1 oz         —      —                   GND Reference 2 (solid)
                              core         75     Megtron-7 (εr=3.3)
 L7      L6       In6.Cu      0.5 oz       —      —                   Memristive Synaptic Grid signals
                              prepreg      75     Megtron-7 (εr=3.3)
 L8      L7       In7.Cu      0.5 oz       —      —                   Analog Signal Restoration
                              core         75     FR-4 High-Tg (εr=4.2)
 L9      —        In8.Cu      1 oz         —      —                   GND Reference 3 (solid)
                              prepreg      75     FR-4 High-Tg (εr=4.2)
 L10     L8–10    In9.Cu      0.5 oz       —      —                   Logic Core / Ternary / Spiking
                              core         100    FR-4 High-Tg (εr=4.2)
 L11     —        In10.Cu     1 oz         —      —                   PWR: +0.9V NCE core supply
                              prepreg      75     FR-4 High-Tg (εr=4.2)
 L12     —        In11.Cu     1 oz         —      —                   GND Reference 4 (solid)
                  ─────────── BOARD CENTER (symmetric axis) ──────────────
                              core         75     FR-4 High-Tg (εr=4.2)
 L13     L11–12   In12.Cu     0.5 oz       —      —                   Communication Primitives
                              prepreg      75     FR-4 High-Tg (εr=4.2)
 L14     L13      In13.Cu     0.5 oz       —      —                   Deterministic Kernel Integration
                              core         100    FR-4 High-Tg (εr=4.2)
 L15     —        In14.Cu     1 oz         —      —                   GND Reference 5 (solid)
                              prepreg      75     Megtron-7 (εr=3.3)
 L16     L14–15   In15.Cu     0.5 oz       —      —                   Fabric OS / Optimization Engine
                              core         75     Megtron-7 (εr=3.3)
 L17     —        In16.Cu     1 oz         —      —                   PWR: +1.0V FPGA, +1.8V I/O
                              prepreg      75     Megtron-7 (εr=3.3)
 L18     —        In17.Cu     1 oz         —      —                   GND Reference 6 (solid)
                              core         75     Megtron-7 (εr=3.3)
 L19     L16–18   In18.Cu     0.5 oz       —      —                   Global Scheduler / Topology Routing
                              prepreg      75     Megtron-7 (εr=3.3)
 L20     L19–20   In19.Cu     0.5 oz       —      —                   Framework Adapters / Direct Integ
                              core         75     Megtron-7 (εr=3.3)
 L21     —        In20.Cu     1 oz         —      —                   PWR: +3.3V, +5V split planes
                              prepreg      75     Megtron-7 (εr=3.3)
 L22     L21–22   B.Cu        1 oz ENIG    —      —                   AI Workload / Memory Pooling (bottom)
══════════════════════════════════════════════════════════════════════════════════════
Total thickness: ~2.4 mm (± 10%)
```

### Layer Classification Summary

| Category | PCB Layers | Count | Function |
|----------|-----------|-------|----------|
| **Signal (Base: Physical Fabric)** | L1, L2, L4, L5 | 4 | TFLN RF, optical, analog |
| **Signal (Core: Logic & Kernel)** | L7, L8, L10, L13, L14 | 5 | Synaptic, logic, communication |
| **Signal (Control: Fabric OS)** | L16, L19, L20 | 3 | Scheduler, framework |
| **Signal (Summit: AI Workload)** | L22 | 1 | Bottom-side AI/memory signals |
| **GND Reference Planes** | L3, L6, L9, L12, L15, L18 | 6 | Solid ground isolation |
| **Power Planes** | L11, L17, L21 | 3 | 0.9V, 1.0V/1.8V, 3.3V/5V |
| **Total** | | **22** | |

## 2. Intelligence Stack Mapping

| Stack Tier | Layers | PCB Function |
|-----------|--------|-------------|
| **Base (Physical Fabric, L1–5)** | L1–L5 | TFLN interconnects, laser/WDM, analog compute. Megtron-7 throughout for ultra-low-loss RF. |
| **Core (Logic & Kernel, L6–12)** | L7–L12 | Logic core, ternary encoding, synaptic grid. FR-4 High-Tg core for cost optimization. |
| **Control Plane (Fabric OS, L13–18)** | L13–L18 | Kernel integration, optimization, scheduler. Mixed Megtron-7/FR-4. |
| **Summit (AI Workloads, L19–22)** | L19–L22 | Framework adapters, memory pooling, AI workload signals. Megtron-7 outer layers. |

## 3. Stackup Rationale

| Design Decision | Rationale |
|----------------|-----------|
| 22 layers | Maps 1:1 to LightRail Intelligence Stack for silicon-to-board traceability |
| 6 GND reference planes | Every signal layer has adjacent solid ground — no broken return paths |
| 3 dedicated power planes | Isolates 0.9V core from 1.0V/1.8V digital and 3.3V/5V peripherals |
| Megtron-7 outer layers (L1–L6, L15–L22) | Low loss (tan δ=0.002) for TFLN RF and high-speed signals at board edges |
| FR-4 High-Tg center (L8–L14) | Cost reduction in inner layers where only digital signals route |
| Symmetric stackup | Prevents board warping during 22-layer lamination press |
| Blind/buried vias enabled | Required for 22-layer HDI: L1–L6 blind vias, L6–L18 buried |
| 75 µm dielectric | Tighter coupling for controlled impedance across all signal layers |

## 4. Impedance Targets

| Signal Class | Target | Tolerance | Geometry | Layers |
|-------------|--------|-----------|----------|--------|
| 50 Ω single-ended (microstrip) | 50 Ω | ±10% | 0.10 mm trace, L1/L22 over GND | L1, L22 |
| 50 Ω single-ended (stripline) | 50 Ω | ±10% | 0.08 mm trace, between GND planes | L2, L4, L5, L7, L10, L13, L14, L16, L19, L20 |
| 100 Ω differential (microstrip) | 100 Ω | ±10% | 0.10 mm trace, 0.15 mm gap | L1, L22 |
| 100 Ω differential (stripline) | 100 Ω | ±10% | 0.08 mm trace, 0.10 mm gap | L2 (TFLN RF) |
| 90 Ω differential (USB) | 90 Ω | ±10% | 0.09 mm trace, 0.12 mm gap | L20 |
| Power traces | N/A | N/A | 0.5–2.0 mm fill | L11, L17, L21 |

## 5. Design Rules (Eval Board — IPC-6012 Class 3)

| Rule | Value | Notes |
|------|-------|-------|
| **Min trace width** | 0.08 mm (3.15 mil) | Stripline signals |
| **Min trace spacing** | 0.08 mm (3.15 mil) | |
| **Min via drill (through)** | 0.25 mm | Through-hole via |
| **Min via drill (blind)** | 0.15 mm | Laser-drilled blind via |
| **Min via drill (buried)** | 0.20 mm | Mechanically drilled buried |
| **Min via pad** | 0.40 mm | Annular ring ≥ 0.10 mm |
| **Min via annular ring** | 0.10 mm | IPC-6012 Class 3 |
| **Min clearance (copper to edge)** | 0.25 mm | |
| **Min solder mask web** | 0.08 mm | |
| **Min silk text height** | 0.8 mm | |
| **Diff pair trace width** | 0.08–0.11 mm | Per impedance target |
| **Diff pair gap** | 0.10–0.15 mm | Per impedance target |
| **Power trace width** | ≥ 0.50 mm | ≥ 300 mA capability |
| **12V trace width** | ≥ 1.0 mm | 500 mA input |
| **Max aspect ratio** | 12:1 | 2.4 mm board / 0.20 mm drill |

## 6. Net Class Definitions

```json
{
  "net_classes": {
    "Default": {
      "trace_width": 0.15,
      "clearance": 0.15,
      "via_drill": 0.30,
      "via_diameter": 0.60,
      "diff_pair_width": null,
      "diff_pair_gap": null
    },
    "AXI_BUS": {
      "trace_width": 0.12,
      "clearance": 0.12,
      "via_drill": 0.25,
      "via_diameter": 0.50,
      "layers": "L10 (Logic Core), L13 (Comm Prims)"
    },
    "CLK_2GHZ": {
      "trace_width": 0.08,
      "clearance": 0.15,
      "via_drill": 0.25,
      "via_diameter": 0.50,
      "layers": "L4 stripline (between GND L3 and GND L6)"
    },
    "TFLN_RF": {
      "trace_width": 0.08,
      "clearance": 0.15,
      "diff_pair_width": 0.08,
      "diff_pair_gap": 0.10,
      "layers": "L2 (TFLN Interconnect) stripline"
    },
    "USB_HS": {
      "trace_width": 0.09,
      "clearance": 0.15,
      "diff_pair_width": 0.09,
      "diff_pair_gap": 0.12,
      "layers": "L20 (Framework)"
    },
    "PWR_5V": {
      "trace_width": 1.00,
      "clearance": 0.20,
      "layers": "L21 (PWR 3.3V/5V)"
    },
    "PWR_CORE": {
      "trace_width": 0.50,
      "clearance": 0.15,
      "layers": "L11 (PWR 0.9V), L17 (PWR 1.0V/1.8V)"
    }
  }
}
```

## 7. Material Specification

| Material | Manufacturer | Grade | Properties |
|----------|-------------|-------|------------|
| Megtron-7 | Panasonic | R-5785(N) | εr=3.3, tan δ=0.002 @ 1 GHz, Tg>200°C |
| FR-4 High-Tg | Isola / Shengyi | 370HR | εr=4.2, Tg≥170°C (inner core layers) |
| Copper foil | — | ED-grade | Per IPC-4562 |
| Solder mask | Taiyo | PSR-4000 AUS703 | Matte green LPI |
| Surface finish | — | ENIG | Ni: 3–6 µm, Au: 0.05–0.10 µm |

## 8. Via Strategy (22-Layer HDI)

| Via Type | Span | Drill | Pad | Purpose |
|----------|------|-------|-----|---------|
| Through-hole | L1–L22 | 0.25 mm | 0.50 mm | General interconnect |
| Blind (top) | L1–L6 | 0.15 mm | 0.40 mm | Physical Fabric ↔ Core |
| Blind (bottom) | L18–L22 | 0.15 mm | 0.40 mm | Control Plane ↔ Summit |
| Buried | L6–L18 | 0.20 mm | 0.45 mm | Core ↔ Control Plane |
| BGA escape (via-in-pad) | L1–L3 | 0.15 mm | 0.35 mm | FPGA BGA-256 escape |
| Thermal via | L1–L22 | 0.30 mm | 0.60 mm | QFN-64 / BGA thermal |
| Stitching via | L1–L22 | 0.25 mm | 0.50 mm | GND plane stitching (every 5 mm) |

## 9. Impedance Test Coupons Required

| Coupon ID | Type | Target | Layer |
|-----------|------|--------|-------|
| Z1 | 50 Ω SE microstrip | 50 Ω ±10% | L1 (F.Cu) over L3 (GND) |
| Z2 | 100 Ω diff microstrip | 100 Ω ±10% | L1 (F.Cu) over L3 (GND) |
| Z3 | 50 Ω SE stripline | 50 Ω ±10% | L2 between L3/L6 (GND) |
| Z4 | 100 Ω diff stripline | 100 Ω ±10% | L2 between L3/L6 (GND) |
| Z5 | 90 Ω diff (USB) | 90 Ω ±10% | L20 between L18/L21 |
| Z6 | 50 Ω SE stripline (inner) | 50 Ω ±10% | L10 between L9/L12 (GND) |
| Z7 | Back-drill stub verification | — | Through-via, drill L1–L18 |

**Stackup Status: COMPLETE (Rev 2.0 — 22-Layer Intelligence Stack)**

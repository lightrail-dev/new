# Step 5: Board Outline / Mechanical Detail
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Board Dimensions

| Parameter | Value |
|-----------|-------|
| **Length** | 100.0 mm (3.937 in) |
| **Width** | 100.0 mm (3.937 in) |
| **Thickness** | 1.6 mm ± 10% |
| **Corner radius** | 2.0 mm (all 4 corners) |
| **Board outline tolerance** | ± 0.15 mm |
| **Form factor** | Custom square eval board |

## 2. Mounting Holes

| ID | Type | Drill | Location (mm) | Notes |
|----|------|-------|---------------|-------|
| MH1 | M3 NPTH | 3.2 mm | (5.0, 5.0) | Corner mounting |
| MH2 | M3 NPTH | 3.2 mm | (95.0, 5.0) | Corner mounting |
| MH3 | M3 NPTH | 3.2 mm | (5.0, 95.0) | Corner mounting |
| MH4 | M3 NPTH | 3.2 mm | (95.0, 95.0) | Corner mounting |

Copper clearance around mounting holes: 1.0 mm annular (all layers).

## 3. Component Keep-Out Zones

### 3.1 NCE Test Chip (U1) Region

```
Center: (40.0, 50.0) mm
QFN-64 body: 8×8 mm
Keep-out (copper): 1.0 mm around body (all layers)
Thermal pad zone: 5.6×5.6 mm with 16× thermal vias
Heat sink attach area: 12×12 mm on B.Cu (optional external heatsink)
```

### 3.2 FPGA (U2) Region

```
Center: (65.0, 50.0) mm
BGA-256 body: 14×14 mm
Keep-out (copper): 0.5 mm around body
Escape routing: via-in-pad, dog-bone pattern
Decoupling zone: 0402 caps within 2 mm of power balls
```

### 3.3 TFLN Optical Module (U3) Region

```
Center: (15.0, 50.0) mm (left edge, fiber exits board left edge)
Module body: 12×6 mm
Optical keep-out: 2.0 mm clearance around fiber exit (ALL copper layers)
Alignment tolerance: ±50 µm (requires precision placement datum)
Board edge clearance: Module fiber array flush with board left edge
```

### 3.4 Connector Zones

```
J1 (Barrel jack): Bottom-left corner (10.0, 90.0) — through-hole, 5mm edge clearance
J2 (USB-C): Bottom edge center (50.0, 97.0) — edge-mount
J5 (JTAG): Right edge (95.0, 30.0) — through-hole header
J6 (GPIO): Right edge (95.0, 70.0) — through-hole header
J7–J10 (SMA): Top edge (25.0/40.0/55.0/70.0, 3.0) — edge-mount
J11 (MPO fiber): Left edge (3.0, 50.0) — co-located with U3 optical exit
```

## 4. Board Outline Drawing

```
        ← 100 mm →
    ┌─────────────────────────────────────────┐ ↑
    │ MH1                   SMA×4         MH2 │ │
    │  ○                 J7 J8 J9 J10      ○  │ │
    │                                         │ │
    │  ┌──────┐    ┌──────┐   ┌────────┐      │ │
    │  │      │    │      │   │        │ J5   │ │
MPO─┤  │ U3   │    │ U1   │   │  U2    │ JTAG│ │ 100 mm
J11 │  │ TFLN │    │ NCE  │   │ FPGA   │      │ │
    │  │      │    │QFN-64│   │BGA-256 │ J6   │ │
    │  └──────┘    └──────┘   └────────┘ GPIO │ │
    │                                         │ │
    │  J1                                     │ │
    │  ⊙ 12V    ┌─────┐                      │ │
    │            │USB-C│                      │ │
    │ MH3        J2                       MH4 │ │
    │  ○                                   ○  │ ↓
    └─────────────────────────────────────────┘
```

## 5. Mechanical Constraints

| Constraint | Value | Reference |
|------------|-------|-----------|
| Max component height (top) | 10 mm | Heatsink clearance |
| Max component height (bottom) | 3 mm | PCB standoff height |
| Board warp/twist | ≤ 0.75% | IPC-6012 Class 2 |
| V-score / panelization | Not required (single board) | — |
| Fiducial marks | 3× (top side) | 1.0 mm dia, 2.0 mm clearance |
| Tooling holes | 2× (panel corners, if panelized) | 2.4 mm NPTH |
| Optical alignment datum | ±50 µm | U3 fiber exit |

## 6. Edge Clearance Requirements

| Edge | Clearance | Reason |
|------|-----------|--------|
| Left edge (fiber exit) | 2.0 mm copper-free zone | Optical module fiber array |
| All edges (general) | 0.5 mm | Manufacturing rail clearance |
| Connector edges | Per connector footprint spec | Mechanical interference |

**Board Outline Status: COMPLETE**

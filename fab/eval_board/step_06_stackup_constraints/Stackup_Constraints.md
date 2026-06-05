# Step 6: Stackup / Constraints Setting
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Layer Stackup (8-Layer)

The evaluation board uses an 8-layer stackup optimized for signal integrity of the 2 GHz HBM5 clock, TFLN RF differential pairs, and USB Hi-Speed signals, while maintaining solid power delivery.

```
═══════════════════════════════════════════════════════════════
Layer    Type          Cu Weight    Diel. Thick    Material         Function
═══════════════════════════════════════════════════════════════
F.Cu     Signal+Pwr    1 oz (35µm)  —              ENIG surface     Top components, critical signals
         Prepreg                     100 µm         Megtron-7 (εr=3.3)
In1.Cu   Ground        1 oz (35µm)  —              —                GND reference plane (solid)
         Core                        200 µm         Megtron-7 (εr=3.3)
In2.Cu   Signal        0.5 oz (18µm) —             —                High-speed signals (AXI, CLK_HBM)
         Prepreg                     200 µm         Megtron-7 (εr=3.3)
In3.Cu   Power         1 oz (35µm)  —              —                +0V9, +1V0 power planes
         Core                        200 µm         FR-4 High-Tg (εr=4.2)
In4.Cu   Power         1 oz (35µm)  —              —                +1V8, +3V3, +5V split planes
         Prepreg                     200 µm         Megtron-7 (εr=3.3)
In5.Cu   Signal        0.5 oz (18µm) —             —                TFLN RF, USB diff pairs
         Core                        200 µm         Megtron-7 (εr=3.3)
In6.Cu   Ground        1 oz (35µm)  —              —                GND reference plane (solid)
         Prepreg                     100 µm         Megtron-7 (εr=3.3)
B.Cu     Signal+Pwr    1 oz (35µm)  —              ENIG surface     Bottom components, power fill
═══════════════════════════════════════════════════════════════
Total thickness: ~1.6 mm (± 10%)
```

## 2. Stackup Rationale

| Design Decision | Rationale |
|----------------|-----------|
| 8 layers (not 6) | Required for 2 dedicated GND planes bracketing all signal layers |
| Megtron-7 for signal layers | Low loss (tan δ = 0.002) for 2 GHz CLK_HBM and RF signals |
| GND on In1 and In6 | Every signal layer has an adjacent solid ground reference |
| Power split on In3/In4 | Separates sensitive 0.9V/1.0V from noisier 5V/3.3V |
| Symmetric stackup | Prevents board warping during reflow |
| 100 µm prepreg at outer | Tight coupling for F.Cu/B.Cu controlled impedance |

## 3. Impedance Targets

| Signal Class | Target | Tolerance | Geometry | Layers |
|-------------|--------|-----------|----------|--------|
| 50 Ω single-ended (microstrip) | 50 Ω | ±10% | 0.12 mm trace, F.Cu/B.Cu over GND | F.Cu, B.Cu |
| 50 Ω single-ended (stripline) | 50 Ω | ±10% | 0.10 mm trace, In2/In5 between GND planes | In2.Cu, In5.Cu |
| 100 Ω differential (microstrip) | 100 Ω | ±10% | 0.10 mm trace, 0.15 mm gap, F.Cu over GND | F.Cu |
| 100 Ω differential (stripline) | 100 Ω | ±10% | 0.09 mm trace, 0.12 mm gap, In2/In5 | In2.Cu, In5.Cu |
| 90 Ω differential (USB) | 90 Ω | ±10% | 0.11 mm trace, 0.15 mm gap | In5.Cu |
| Power traces | N/A | N/A | 0.5–2.0 mm width | In3.Cu, In4.Cu |

## 4. Design Rules (Eval Board — IPC-6012 Class 2)

| Rule | Value | Notes |
|------|-------|-------|
| **Min trace width** | 0.10 mm (4 mil) | Standard signals |
| **Min trace spacing** | 0.10 mm (4 mil) | |
| **Min via drill** | 0.25 mm | Through-hole via |
| **Min via pad** | 0.50 mm | Annular ring ≥ 0.125 mm |
| **Min via annular ring** | 0.125 mm | IPC-6012 Class 2 |
| **Min clearance (copper to edge)** | 0.25 mm | |
| **Min solder mask web** | 0.10 mm | |
| **Min silk text height** | 0.8 mm | Readability |
| **Min silk line width** | 0.15 mm | |
| **Diff pair trace width** | 0.09–0.12 mm | Per impedance target |
| **Diff pair gap** | 0.12–0.20 mm | Per impedance target |
| **Power trace width** | ≥ 0.50 mm | ≥ 300 mA capability |
| **12V trace width** | ≥ 1.0 mm | 500 mA input |

## 5. Net Class Definitions

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
      "via_diameter": 0.50
    },
    "CLK_2GHZ": {
      "trace_width": 0.10,
      "clearance": 0.15,
      "via_drill": 0.25,
      "via_diameter": 0.50
    },
    "TFLN_RF": {
      "trace_width": 0.10,
      "clearance": 0.15,
      "diff_pair_width": 0.10,
      "diff_pair_gap": 0.15
    },
    "USB_HS": {
      "trace_width": 0.11,
      "clearance": 0.15,
      "diff_pair_width": 0.11,
      "diff_pair_gap": 0.15
    },
    "PWR_5V": {
      "trace_width": 1.00,
      "clearance": 0.20
    },
    "PWR_CORE": {
      "trace_width": 0.50,
      "clearance": 0.15
    }
  }
}
```

## 6. Material Specification

| Material | Manufacturer | Grade | Properties |
|----------|-------------|-------|------------|
| Megtron-7 | Panasonic | R-5785(N) | εr=3.3, tan δ=0.002 @ 1 GHz, Tg>200°C |
| FR-4 High-Tg | Isola / Shengyi | 370HR | εr=4.2, Tg≥170°C (power core only) |
| Copper foil | — | ED-grade | Per IPC-4562 |
| Solder mask | Taiyo | PSR-4000 AUS703 | Matte green LPI |
| Surface finish | — | ENIG | Ni: 3–6 µm, Au: 0.05–0.10 µm |

## 7. Impedance Test Coupons Required

| Coupon ID | Type | Target | Layer |
|-----------|------|--------|-------|
| Z1 | 50 Ω SE microstrip | 50 Ω ±10% | F.Cu over In1.Cu |
| Z2 | 100 Ω diff microstrip | 100 Ω ±10% | F.Cu over In1.Cu |
| Z3 | 50 Ω SE stripline | 50 Ω ±10% | In2.Cu between In1/In3 |
| Z4 | 100 Ω diff stripline | 100 Ω ±10% | In5.Cu between In4/In6 |
| Z5 | 90 Ω diff (USB) | 90 Ω ±10% | In5.Cu |

**Stackup Status: COMPLETE**

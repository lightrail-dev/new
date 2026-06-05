# Step 9: Silkscreen / DRC / FAB Notes
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Silkscreen Design

### 1.1 Top Silkscreen (F.Silkscreen)

| Element | Location | Font/Size |
|---------|----------|-----------|
| Board title: "LightRail NCE+TFLN Eval v1.0" | Top-left corner | 1.5 mm height |
| Revision: "Rev 1.0" | Below title | 1.0 mm height |
| Date: "2026-05" | Below revision | 1.0 mm height |
| Project code: "PA-2026-001" | Below date | 1.0 mm height |
| LightRail logo | Top-right corner | 8×4 mm |
| All reference designators (U, R, C, J, etc.) | Adjacent to each component | 0.8 mm min height |
| Pin 1 dots on all ICs | Pin 1 corner of each IC | 0.3 mm dot |
| Polarity marks on tantalum caps | Near + terminal | Standard "+" symbol |
| Connector pin 1 marks | Near pin 1 of all headers | Arrow or dot |
| Test point labels (TP1–TP16) | Adjacent to test pads | 0.8 mm height |
| Power rail voltage labels | Near each regulator output | 1.0 mm height |
| "12V IN" label | Near J1 barrel jack | 1.2 mm height |
| "USB" label | Near J2 USB-C | 1.2 mm height |
| "JTAG" label | Near J5 header | 1.0 mm height |
| "GPIO" label | Near J6 header | 1.0 mm height |
| "RESET" label | Near SW1 | 1.0 mm height |
| Optical fiber alignment marks | Near U3 fiber exit | Cross-hair fiducials |

### 1.2 Bottom Silkscreen (B.Silkscreen)

| Element | Location | Font/Size |
|---------|----------|-----------|
| Board title (mirrored) | Center | 1.2 mm height |
| "BOTTOM SIDE" indicator | Center | 1.0 mm height |
| Bottom component ref-des | Adjacent to bottom components | 0.8 mm height |
| QR code (linking to docs URL) | Bottom-right | 8×8 mm |

### 1.3 Silkscreen Rules

| Rule | Value |
|------|-------|
| Min text height | 0.8 mm |
| Min line width | 0.15 mm |
| Silkscreen not on pads | Enforced (DRC check) |
| Silkscreen clearance from mask openings | 0.10 mm |
| Silkscreen over via tenting | Allowed (tented vias only) |
| Polarity marks on all polarized parts | Required |

## 2. Design Rule Check (DRC) Configuration

### 2.1 DRC Rule Set

| Rule Category | Rule | Value | Severity |
|--------------|------|-------|----------|
| **Clearance** | Min trace-to-trace | 0.10 mm | Error |
| | Min trace-to-pad | 0.10 mm | Error |
| | Min trace-to-via | 0.10 mm | Error |
| | Min copper-to-edge | 0.25 mm | Error |
| | Min copper-to-hole | 0.125 mm | Error |
| **Trace width** | Min trace width | 0.10 mm | Error |
| | Min power trace width | 0.50 mm | Warning |
| **Via** | Min via drill | 0.25 mm | Error |
| | Min via annular ring | 0.125 mm | Error |
| | Min via-to-via | 0.15 mm | Error |
| **Diff pair** | Gap out of range | Per net class | Error |
| | Uncoupled length too long | 2.0 mm | Error |
| | Skew | Per signal class | Error |
| **Silk** | Silk over copper pad | — | Warning |
| | Silk overlap | — | Warning |
| **Courtyard** | Overlap | — | Error |
| **Unconnected** | Unrouted nets | — | Error |

### 2.2 DRC Results Target

| Category | Target |
|----------|--------|
| Errors | **0** |
| Warnings | **0** (all resolved or documented) |
| Unrouted nets | **0** |
| DRC exclusions | 0 (no intentional violations) |

### 2.3 Custom DRC Rules (eval board specific)

```
# CLK_HBM guard trace enforcement
(rule "clk_hbm_guard"
  (constraint clearance (min 0.15mm))
  (condition "A.NetName == 'CLK_HBM' && B.NetClass != 'CLK_2GHZ'")
)

# TFLN RF pair intra-pair skew
(rule "tfln_rf_intra_pair_skew"
  (constraint skew (max 0.1mm))
  (condition "A.NetClass == 'TFLN_RF'")
  (severity error)
)

# USB intra-pair skew
(rule "usb_intra_pair_skew"
  (constraint skew (max 0.1mm))
  (condition "A.NetClass == 'USB_HS'")
  (severity error)
)

# No signal routing on GND plane layers
(rule "gnd_plane_no_signals"
  (constraint disallow track)
  (condition "A.Layer == 'In1.Cu' || A.Layer == 'In6.Cu'")
  (severity error)
)
```

## 3. Fabrication Notes

### 3.1 General Specifications

| Parameter | Value |
|-----------|-------|
| Board dimensions | 100.0 × 100.0 mm |
| Layer count | 8 |
| Board thickness | 1.6 mm ±10% |
| Surface finish | ENIG (IPC-4552 Class 2) |
| Solder mask | Matte green LPI (both sides) |
| Silkscreen | White epoxy ink (both sides) |
| Material | Megtron-7 signal layers + FR-4 High-Tg power core |
| Copper weights | See Stackup_Constraints.md |
| Min trace/space | 0.10/0.10 mm (4/4 mil) |
| Min drill | 0.25 mm |
| Aspect ratio | ≤ 6.4:1 (1.6mm / 0.25mm) |
| Controlled impedance | Yes — see impedance targets in Stackup_Constraints.md |

### 3.2 Special Fabrication Instructions

1. **Impedance control required** — manufacturer must provide test coupons (see Stackup_Constraints.md §7)
2. **Via-in-pad** (FPGA U2 BGA area) — vias must be filled with non-conductive epoxy and capped/plated flat
3. **ENIG finish** — required for BGA reliability and fine-pitch QFN soldering
4. **Board edge tolerance** — ±0.15 mm for optical module alignment
5. **Fiducial marks** — 3× on top side (1.0 mm copper circle, 2.0 mm clearance ring)
6. **No V-score** — single board, route with 2.0 mm corner radius
7. **Electrical test** — 100% bare-board test per IPC-D-356 netlist

### 3.3 Solder Mask Details

| Parameter | Value |
|-----------|-------|
| Color | Matte green |
| Min web width | 0.10 mm (4 mil) |
| Pad-to-mask clearance | 0.051 mm per side |
| Via tenting | All vias ≤ 0.40 mm drill tented both sides |
| BGA openings | NSMD (non-solder mask defined) |
| QFN openings | SMD (solder mask defined) for NCE |

### 3.4 Paste Stencil Notes

| Parameter | Value |
|-----------|-------|
| Stencil thickness | 0.12 mm (0402 and BGA) |
| 0402 aperture | 1:1 pad size (area ratio > 0.66) |
| 0201 aperture | 0.9:1 reduction (area ratio > 0.50) |
| QFN-64 exposed pad | 4× window pattern (50% coverage) |
| BGA-256 aperture | 0.35 mm circular (87.5% of 0.40 mm pad) |

## 4. Fabrication Drawing Checklist

| Item | Included | Notes |
|------|----------|-------|
| Board outline with dimensions | Y | See Board_Outline_Mechanical.md |
| Layer stackup table | Y | See Stackup_Constraints.md |
| Drill chart (PTH, NPTH) | Y | In gerber package |
| Impedance callouts | Y | On fab drawing |
| Material callout | Y | Megtron-7 + FR-4 High-Tg |
| Surface finish callout | Y | ENIG IPC-4552 |
| Solder mask specification | Y | PSR-4000 AUS703 |
| Special instructions | Y | Via-in-pad, fiducials, test |
| IPC class callout | Y | IPC-6012 Class 2 |
| Acceptance criteria | Y | IPC-A-600 Class 2 |

**DRC / FAB Notes Status: COMPLETE**

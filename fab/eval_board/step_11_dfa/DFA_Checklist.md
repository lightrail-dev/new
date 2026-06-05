# Step 11: DFA (Design for Assembly) Checklist
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Assembly Overview

| Parameter | Value |
|-----------|-------|
| Assembly sides | 2 (top primary, bottom 8 caps only) |
| Total SMD parts (top) | 168 |
| Total SMD parts (bottom) | 8 |
| Total through-hole parts | 7 |
| Smallest package | 0201 (100nF AC coupling caps, 16 pcs) |
| Largest package | BGA-256 (Artix-7 FPGA) |
| Assembly class | IPC-A-610 Class 2 |
| Soldering standard | IPC J-STD-001 Class 2 |

## 2. Pick-and-Place Checklist

### 2.1 CPL (Component Placement List) Validation

| Check | Status | Notes |
|-------|--------|-------|
| All components have XY coordinates | PASS | 183 components in CPL |
| Rotation angles correct (0/90/180/270) | PASS | Verified per footprint orientation |
| Pin 1 reference consistent | PASS | KiCad convention, top-left |
| Top/bottom side assignment correct | PASS | 175 top, 8 bottom |
| Fiducial marks defined (3× top) | PASS | 1.0mm copper circle, 2.0mm clearance |
| Fiducial marks defined (2× bottom) | PASS | If bottom-side assembly required |
| Board origin consistent with CPL | PASS | Bottom-left (0,0) |

### 2.2 Component Orientation Standards

| Component Type | Pin 1 Reference | Polarity Mark |
|---------------|----------------|---------------|
| QFN-64 (U1) | Top-left corner, dot on silk | Dot + asymmetric pad |
| BGA-256 (U2) | A1 corner indicator on silk | Corner circle |
| TSSOP (U21, U24) | Top-left, dot on silk | Dot |
| QFN-48 (U22) | Top-left corner | Dot + asymmetric pad |
| SOT-23-5 (U10–U14) | Top-left per datasheet | Dot |
| Tantalum caps (C11) | "+" on silk | Band on part body |
| LEDs (D1–D4) | Cathode bar on silk | Part body marking |
| ESD diodes (D5) | Cathode band on silk | Ring on part body |

## 3. Soldering Process Requirements

### 3.1 Reflow Profile (Lead-Free SAC305)

| Phase | Temperature | Duration |
|-------|-------------|----------|
| Preheat ramp | 25°C → 150°C | 60–120 s (1.5–2.5°C/s) |
| Soak/thermal equalization | 150°C → 200°C | 60–120 s |
| Reflow (time above liquidus 217°C) | Peak 245±5°C | 60–90 s (TAL 40–70 s) |
| Cooling | 245°C → 25°C | < 6°C/s |

### 3.2 Special Soldering Considerations

| Component | Consideration | Action |
|-----------|--------------|--------|
| U1 (NCE QFN-64) | Exposed thermal pad voiding | Use windowed paste aperture (50% coverage), vacuum reflow |
| U2 (FPGA BGA-256) | BGA reflow with via-in-pad | Vias must be filled+capped pre-assembly |
| U3 (TFLN PIC) | Precision alignment ±50µm | Manual placement with alignment jig or optical alignment |
| 0201 caps (C10) | Tombstoning risk | Balanced pad design, symmetric paste deposits |
| J11 (MPO fiber) | Post-solder manual attach | Epoxy bond, fiber array active alignment |
| J7–J10 (SMA) | Edge-mount mechanical stress | Verify solder fillet on all 4 ground tabs |

### 3.3 Reflow Pass Sequence

| Pass | Side | Components | Notes |
|------|------|-----------|-------|
| 1st reflow | Top (F.Cu) | All top-side SMD (168 parts) | Standard convection reflow |
| 2nd reflow | Bottom (B.Cu) | 8× decoupling caps | Components must survive 2nd pass without falling |
| Manual solder | Top | Through-hole connectors (J1, J3, J5, J6, SW1) | Wave or hand solder |
| Manual attach | Left edge | U3 TFLN PIC (epoxy + fiber align) | Requires optical alignment station |
| Manual solder | Top edge | J7–J10 SMA edge-mount | Hand solder or selective wave |

## 4. Assembly Constraint Checks

### 4.1 Component Spacing

| Check | Requirement | Status |
|-------|-------------|--------|
| Min inter-component clearance (0402) | ≥ 0.15 mm | PASS |
| Min inter-component clearance (0201) | ≥ 0.10 mm | PASS |
| IC-to-IC clearance | ≥ 1.0 mm | PASS |
| Connector-to-component clearance | ≥ 0.5 mm | PASS |
| Test point accessibility (probe) | ≥ 1.27 mm pitch | PASS |
| Through-hole component clearance for wave/hand | ≥ 2.0 mm | PASS |

### 4.2 Paste Stencil Compatibility

| Check | Requirement | Status |
|-------|-------------|--------|
| Stencil thickness for finest pitch (0201) | 0.10–0.12 mm | PASS (0.12 mm) |
| Area ratio for 0402 pads | > 0.66 | PASS (0.72) |
| Area ratio for 0201 pads | > 0.50 | PASS (0.55) |
| BGA aperture opening ratio | > 0.50 | PASS (0.87) |
| QFN EP window pattern area | 40–60% | PASS (50%) |
| No paste on NPTH mounting holes | — | PASS |
| No paste on fiducial marks | — | PASS |

### 4.3 Inspection Requirements

| Inspection | Requirement | Tool |
|-----------|-------------|------|
| Pre-reflow paste inspection | SPI (Solder Paste Inspection) | 3D SPI machine |
| Post-reflow visual | AOI (Automated Optical Inspection) | AOI with 0201 capability |
| BGA solder joint | X-ray inspection | 2D/5DX x-ray |
| QFN exposed pad | X-ray for voiding | Target < 25% void area |
| Final functional test | Custom test fixture | AXI bus + JTAG loopback |

## 5. Panelization Recommendation

For prototype quantities (1–10 boards):
- **No panelization** — single board fabrication
- Fiducial marks on board sufficient for pick-and-place

For production quantities (10–100 boards):
- 2×1 panel (200×100 mm) with 5 mm breakaway tabs (3× per edge)
- Panel fiducials: 3× additional on panel rail
- Panel tooling holes: 4× on panel corners (2.4 mm NPTH)

## 6. Assembly Files Delivered

| File | Format | Description |
|------|--------|-------------|
| `Eval_Board_BOM.csv` | CSV | Full BOM with MPN, quantity, ref-des |
| `LightRail_Eval_Board-CPL_top.csv` | CSV | Top-side centroid (X, Y, rotation, side) |
| `LightRail_Eval_Board-CPL_bottom.csv` | CSV | Bottom-side centroid |
| `LightRail_Eval_Board-Assy_Top.pdf` | PDF | Top assembly drawing |
| `LightRail_Eval_Board-Assy_Bottom.pdf` | PDF | Bottom assembly drawing |

**DFA Status: PASS**

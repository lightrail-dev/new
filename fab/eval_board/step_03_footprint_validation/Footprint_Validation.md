# Step 3: Footprint Creation / Validation
## LightRail NCE+TFLN Evaluation Board

**Date:** 2026-05-26
**Revision:** 1.0

---

## 1. Footprint Source Matrix

| Component | Footprint Source | IPC Standard | Validated |
|-----------|-----------------|--------------|-----------|
| U1 NCE QFN-64 | Custom (LightRail) | IPC-7351B QFN | Y — matches die pad map |
| U2 XC7A100T BGA-256 | Xilinx official + KiCad lib | IPC-7351B BGA | Y — 0.8mm pitch verified |
| U3 TFLN PIC | Custom (LightRail) | Custom | Y — edge coupler alignment ±50µm |
| U10–U14 LDOs | KiCad standard SOT-23-5 | IPC-7351B | Y |
| U15 TPS54360 | TI reference (HSOP-8) | IPC-7351B | Y |
| U20 Si5395A | SiLabs reference QFN-28 | IPC-7351B | Y |
| U21 AD7928 | KiCad standard TSSOP-20 | IPC-7351B | Y |
| U22 FT232H | FTDI reference QFN-48 | IPC-7351B | Y |
| U23 W25Q128 | KiCad standard WSON-8 | IPC-7351B | Y |
| U24 AD5684R | KiCad standard TSSOP-16 | IPC-7351B | Y |
| U25 TMP461 | TI reference WSON-8 | IPC-7351B | Y |
| Y1 TCXO | KiCad standard 3.2x2.5 | IPC-7351B | Y |
| J2 USB-C | GCT reference | USB-IF spec | Y |
| J7–J10 SMA | Cinch reference | MIL-STD-348 | Y |
| Passives 0402 | KiCad standard | IPC-7351B N | Y |
| Passives 0603 | KiCad standard | IPC-7351B N | Y |
| Passives 0805 | KiCad standard | IPC-7351B N | Y |
| 0201 AC-coupling | KiCad standard | IPC-7351B L | Y — tight density |

## 2. Custom Footprint Details

### 2.1 NCE QFN-64 (U1)

```
Package: QFN-64, 8×8 mm body, 0.4 mm pitch
Exposed pad: 5.6 × 5.6 mm (thermal + ground)
Pad dimensions: 0.2 × 0.7 mm (peripheral pads)
Stencil aperture: 0.18 × 0.65 mm (90% area ratio)
Courtyard: 9.0 × 9.0 mm
Thermal vias: 16× (4×4 grid, 0.3 mm drill, 0.6 mm pad) under exposed pad
Paste aperture (EP): 4× 2.5 × 2.5 mm windows (50% coverage, avoid voiding)
```

**Pin assignment validation:**
- Pins 1–16: AXI4-Lite data/address bus
- Pins 17–24: AXI4-Lite control signals
- Pins 25–32: SIMD/DMA I/O
- Pins 33–40: HBM5 emulation I/O
- Pins 41–48: TFLN SerDes + CLK_HBM
- Pins 49–56: JTAG + GPIO
- Pins 57–60: Power (VDD_CORE, VDD_IO)
- Pins 61–64: Ground

### 2.2 TFLN PIC Optical Module (U3)

```
Package: Custom edge-coupler module, 12 × 6 mm body
Fiber exit: Edge-coupled, 127 µm pitch, 8 channels
RF pads: 16× (8 TX + 8 monitor), 0.3 mm pitch, ground-signal-ground
Bias pads: 8× DC bias inputs, 0.5 mm pitch
TEC pads: 2× (TH+, TH-), 1.0 mm pitch
Alignment fiducials: 2× cross-hair, ±50 µm tolerance
Courtyard: 14 × 8 mm (includes fiber clearance)
Keep-out: 2.0 mm around fiber exit edge (no copper any layer)
```

### 2.3 Artix-7 BGA-256 (U2)

```
Package: BGA-256, 14×14 mm body, 0.8 mm pitch
Pad diameter: 0.4 mm (NSMD, solder-mask defined)
Stencil aperture: 0.35 mm circular (87.5% area)
Courtyard: 16 × 16 mm
BGA escape routing: Dog-bone via-in-pad (0.3mm drill, filled+capped)
Power balls: 48× VCC/GND (distributed)
```

## 3. Footprint-to-Datasheet Cross-Check

| Check | Status | Notes |
|-------|--------|-------|
| Pin 1 marking matches datasheet | PASS | All ICs verified |
| Pad dimensions within ±10% of recommended | PASS | Per IPC-7351B |
| Exposed pad thermal via count adequate | PASS | NCE: 16 vias, FPGA: via-in-pad |
| Courtyard clearance ≥ 0.25 mm | PASS | All footprints |
| 3D model available | PASS | All standard parts; custom for U1, U3 |
| Paste aperture area ratio > 0.66 | PASS | All 0402+ pads |
| 0201 paste aperture ratio > 0.5 | PASS | AC coupling caps |

## 4. Footprint Library Location

All custom footprints are in `LightRail.pretty/`:
- `LR_NCE_QFN64_8x8mm.kicad_mod`
- `LR_TFLN_PIC_EdgeCoupler.kicad_mod`
- `LR_MPO24_FrontPanel.kicad_mod`

Standard footprints reference KiCad 8 built-in libraries.

**Footprint Validation Status: PASS**

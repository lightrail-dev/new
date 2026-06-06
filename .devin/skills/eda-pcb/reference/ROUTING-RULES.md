---
name: routing-rules
description: Trace width calculation and routing rules for PCB design.
---

# Routing Rules

## Trace Width by Current (1oz copper, outer layer)

| Current (A) | Min Width (mm) | Recommended Width (mm) |
|-------------|----------------|------------------------|
| 0.1 | 0.10 | 0.15 |
| 0.3 | 0.15 | 0.20 |
| 0.5 | 0.20 | 0.30 |
| 1.0 | 0.30 | 0.50 |
| 2.0 | 0.60 | 1.00 |
| 3.0 | 1.00 | 1.50 |
| 5.0 | 1.80 | 2.50 |

Note: Internal layers carry ~50% of outer layer current for same width.

## Default Trace Widths

| Signal Type | Width (mm) | Notes |
|-------------|------------|-------|
| General signals | 0.15 - 0.20 | Standard digital I/O |
| Power (< 500mA) | 0.30 - 0.50 | VCC/VDD rails |
| Power (500mA-2A) | 0.50 - 1.00 | Regulator outputs |
| Power (> 2A) | 1.00 - 2.50+ | Main power bus |
| Ground | 0.30+ or pour | Prefer copper pour |
| USB D+/D- | Per impedance calc | 90 Ohm differential |
| Crystal | 0.15 | Short, guarded |

## Routing Priority

1. **Power delivery** - Wide traces, pours, via stitching
2. **Crystal / oscillator** - Short, straight, guard ground
3. **USB differential pairs** - 90 Ohm, length matched within 0.1mm
4. **High-speed SPI/I2C** - Keep short, over ground plane
5. **Sensitive analog** - Short, shielded, away from digital
6. **General digital** - Standard width, minimize vias
7. **Non-critical** - LED, debug, test points

## Differential Pair Rules

| Standard | Impedance | Trace/Space (typical 4L 1.6mm) |
|----------|-----------|-------------------------------|
| USB 2.0 | 90 Ohm diff | 0.20mm trace, 0.15mm space |
| USB 3.x | 85 Ohm diff | Use impedance calculator |
| LVDS | 100 Ohm diff | 0.15mm trace, 0.20mm space |
| Ethernet | 100 Ohm diff | 0.15mm trace, 0.18mm space |

## Via Usage

| Via Type | Drill | Pad | Use Case |
|----------|-------|-----|----------|
| Standard | 0.3mm | 0.6mm | General signal routing |
| Power | 0.4mm | 0.8mm | Power delivery |
| Thermal | 0.3mm | 0.6mm | Under thermal pads (array) |
| Micro | 0.1mm | 0.25mm | HDI (if supported) |

## Length Matching

| Signal Group | Match Tolerance |
|--------------|-----------------|
| USB 2.0 D+/D- | +/- 0.15mm |
| USB 3.x | +/- 0.1mm |
| DDR data to strobe | +/- 0.5mm |
| DDR address/command | +/- 2.0mm |
| Ethernet TX+/TX- | +/- 0.1mm |

## Routing Best Practices

- Use 45-degree angles (no acute angles)
- Minimize via count (each via adds ~0.5nH inductance)
- Avoid routing under crystals/oscillators
- Keep return path intact (no ground plane splits under signals)
- Add teardrops to via connections (improves reliability)
- Maintain minimum clearance to board edge (0.25mm)
- Route clock signals on inner layers (shielded)

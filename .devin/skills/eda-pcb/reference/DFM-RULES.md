---
name: dfm-rules
description: Design for Manufacturing rules targeting common PCB fabs (JLCPCB, PCBWay, etc).
---

# Design for Manufacturing (DFM) Rules

## JLCPCB Standard Capabilities

| Parameter | Standard | Advanced |
|-----------|----------|----------|
| Min trace width | 0.127mm (5mil) | 0.09mm (3.5mil) |
| Min clearance | 0.127mm (5mil) | 0.09mm (3.5mil) |
| Min via drill | 0.3mm | 0.2mm |
| Min via pad | 0.6mm | 0.45mm |
| Annular ring | 0.13mm | 0.1mm |
| Min hole-to-hole | 0.5mm | 0.35mm |
| Min hole-to-edge | 0.4mm | 0.3mm |
| Board thickness | 0.4 - 2.4mm | Same |
| Copper weight | 1oz, 2oz | 0.5 - 4oz |
| Layers | 1 - 32 | Same |
| Solder mask min | 0.1mm | 0.075mm |
| Silkscreen min width | 0.15mm | 0.1mm |
| Silkscreen min height | 0.8mm | 0.6mm |

## PCBWay Standard Capabilities

| Parameter | Value |
|-----------|-------|
| Min trace width | 0.1mm (4mil) |
| Min clearance | 0.1mm (4mil) |
| Min via drill | 0.2mm |
| Min annular ring | 0.15mm |
| Board outline tolerance | +/- 0.2mm |

## Critical DFM Checks

### Board Outline
- Closed polygon (no gaps)
- Minimum corner radius: 0.5mm (sharp corners may break)
- Slots minimum width: 1.0mm (standard), 0.8mm (advanced)
- Board-edge-to-copper clearance: 0.3mm minimum

### Copper Features
- No copper slivers < 0.1mm
- No isolated copper pads without thermal relief
- Polygon pour min width: 0.2mm
- Thermal relief spoke width: 0.25mm min

### Drill
- Minimum finished hole size: 0.2mm
- Maximum aspect ratio (depth:diameter): 10:1 (standard)
- NPTH tolerance: +/- 0.05mm
- PTH tolerance: +/- 0.075mm

### Solder Mask
- Solder mask opening >= pad size + 0.05mm per side
- No solder mask between fine-pitch pads (use solder dam if possible)
- Solder mask dam min width: 0.1mm

### Silkscreen
- No silkscreen on exposed pads
- Min line width: 0.15mm
- Min text height: 0.8mm
- Maintain polarity marks on all ICs
- Reference designators visible after assembly

## Panelization Guidelines

| Parameter | Value |
|-----------|-------|
| V-score min distance to hole | 0.4mm |
| Tab width | 2.0mm |
| Mouse-bite hole diameter | 0.5mm |
| Mouse-bite hole spacing | 0.8mm |
| Panel margin | 5.0mm per side |
| Panel max size | 350 x 250mm (JLCPCB) |

## Common DFM Violations

| Issue | Impact | Fix |
|-------|--------|-----|
| Acid trap (acute copper angle) | Etching issues | Use 45/90 degree angles |
| Copper sliver | Short circuit risk | Increase clearance |
| Starved thermal relief | Poor soldering | Increase spoke width |
| Missing paste aperture | Component not soldered | Add paste layer opening |
| Silkscreen on pad | Assembly confusion | Move or remove silkscreen |
| Drill too close to edge | Board breakage | Move hole or adjust outline |

---
name: drc-violations-guide
description: Common DRC errors in KiCad and how to fix them.
---

# DRC Violations Guide

## Common DRC Errors and Fixes

### Clearance Violations

| Error | Cause | Fix |
|-------|-------|-----|
| Copper clearance | Traces too close | Re-route with larger spacing |
| Pad clearance | Component too close | Move component or adjust pad |
| Via clearance | Via too close to pad/trace | Move via or use smaller via |
| Edge clearance | Copper too close to board edge | Move trace/pour inward |
| Courtyard overlap | Components overlapping | Move one component |

### Connectivity Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Unconnected net | Missing trace or via | Route the connection |
| Isolated copper | Pour island not connected | Add via to ground or delete |
| Missing connection | Netlist vs PCB mismatch | Update PCB from schematic |

### Drill/Via Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Annular ring too small | Pad size vs drill | Increase pad or reduce drill |
| Hole too close to edge | Drill near board outline | Move hole inward |
| Drill overlap | Two holes touching | Separate or merge |
| Min drill size | Below fab minimum | Increase drill diameter |

### Copper Pour Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Min width violation | Narrow copper sliver | Increase pour clearance |
| Isolated island | Pour section cut off | Add via or remove island |
| Thermal relief too narrow | Spoke width too small | Increase thermal spoke width |

### Silkscreen Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Silk on pad | Text over exposed copper | Move silkscreen reference |
| Silk clipped by courtyard | Text extends beyond part | Resize or reposition |
| Overlapping silk | Two references overlap | Move or resize |

## KiCad DRC Settings (Recommended)

```
Clearance: 0.15mm (signals), 0.30mm (power)
Track width: 0.15mm min, 0.20mm default
Via: 0.3mm drill, 0.6mm outer diameter
Annular ring: 0.13mm minimum
Copper-to-edge: 0.3mm
Courtyard: 0.25mm minimum
Silkscreen: 0.15mm line width, 0.8mm text height
```

## Intentional DRC Exception Documentation

When a DRC violation is intentional, document it:

```
| Violation | Location | Reason |
|-----------|----------|--------|
| Clearance: U1 pad 5 to C3 | Near MCU | Required for decoupling cap proximity |
| Courtyard: J1 to SW1 | Board edge | Mechanical fit verified in 3D model |
```

## DRC Workflow

1. Run DRC frequently during layout (not just at end)
2. Fix all errors as they appear
3. Re-run after major changes (component moves, re-routing)
4. Final DRC must be 0 errors before manufacturing
5. Warnings are acceptable if documented and justified
6. Export DRC report for design review records

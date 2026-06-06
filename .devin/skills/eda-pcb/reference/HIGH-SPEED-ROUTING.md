---
name: high-speed-routing
description: Routing guidelines for USB, SPI, I2C, antenna, and other high-speed interfaces.
---

# High-Speed Routing Guidelines

## USB 2.0 (Full/High Speed)

| Parameter | Value |
|-----------|-------|
| Impedance | 90 Ohm differential |
| Trace width | ~0.20mm (depends on stackup) |
| Pair spacing | ~0.15mm (edge-to-edge) |
| Length matching | +/- 0.15mm |
| Max length | 100mm (on PCB) |
| Clearance to other signals | >= 3x trace width |
| Reference plane | Solid GND below |
| Vias | Avoid; if needed, use ground vias adjacent |
| Coupling | Route as tightly coupled pair |
| Termination | None needed on PCB (built into IC) |

### USB Layout Checklist
- [ ] D+/D- routed as differential pair
- [ ] Solid ground plane underneath entire route
- [ ] Series resistors within 5mm of IC (if required)
- [ ] ESD protection at connector
- [ ] Common-mode choke between IC and connector
- [ ] Length matched within tolerance
- [ ] No stubs or tees
- [ ] Shield ground connected to chassis/connector shell

## SPI (Standard and High-Speed)

| Parameter | Standard SPI | High-Speed SPI (>20MHz) |
|-----------|-------------|-------------------------|
| Impedance | Not critical | 50 Ohm single-ended |
| Max trace length | 100mm | 50mm |
| Series termination | Not needed | 22-33 Ohm at source |
| Ground reference | Recommended | Required (unbroken) |
| CLK routing | Match or shorter than data | Must be shorter than data |

### SPI Best Practices
- Keep CLK trace shorter or equal to data traces
- Add series termination resistor at CLK source for >20MHz
- Route CLK away from other signals (3x spacing)
- Place decoupling cap at slave CS pin
- Avoid routing over plane splits

## I2C

| Parameter | Standard (100kHz) | Fast (400kHz) | Fast+ (1MHz) |
|-----------|-------------------|---------------|---------------|
| Max bus capacitance | 400pF | 400pF | 550pF |
| Max trace length | ~500mm | ~200mm | ~100mm |
| Pull-up location | Master or central | Near master | At master |
| Impedance | Not critical | Not critical | Not critical |

### I2C Layout Notes
- Calculate total bus capacitance (trace + pin + via)
- ~1pF per mm of trace (rough estimate)
- Pull-up resistors close to master device
- Route SDA and SCL together (noise rejection)
- Keep away from high-speed switching signals

## Ethernet (10/100/1000)

| Parameter | Value |
|-----------|-------|
| Impedance | 100 Ohm differential |
| Length matching (pair) | +/- 0.1mm |
| Length matching (pairs) | +/- 5mm (GbE) |
| Max PCB trace length | 150mm |
| Guard clearance | 0.5mm to other pairs |
| Magnetics placement | Within 25mm of PHY |

## Antenna / RF Routing

| Rule | Details |
|------|---------|
| Keep-out zone | No copper/components within 5-10mm of antenna |
| Feed line impedance | 50 Ohm microstrip or coplanar waveguide |
| Ground plane | Solid, unbroken below feed line |
| No vias in feed | Zero vias in antenna feed path |
| Matching network | Place within 5mm of antenna feed point |
| Ground plane edge | Antenna should extend beyond ground plane edge |

## General High-Speed Rules

1. **Reference plane**: All high-speed signals need continuous reference plane
2. **Via transitions**: Add ground vias adjacent to signal vias (return current)
3. **Crosstalk**: Maintain 3x trace-width spacing to adjacent signals
4. **Stubs**: Zero length stubs (use inline topology)
5. **Termination**: Match to characteristic impedance at endpoints
6. **Layer transitions**: Minimize; add reference vias when crossing layers
7. **Impedance calculator**: Always use stackup-specific calculator (e.g., Saturn PCB, KiCad built-in)

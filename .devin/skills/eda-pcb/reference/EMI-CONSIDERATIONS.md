---
name: emi-considerations
description: EMI/EMC best practices for PCB layout.
---

# EMI/EMC Considerations

## General Principles

1. **Minimize loop area** - Every signal has a return path; keep them close
2. **Solid ground plane** - Unbroken ground plane under all signals
3. **Contain high-speed signals** - Route on inner layers, use shielding
4. **Filter at boundaries** - I/O connectors need filtering
5. **Decouple locally** - Every IC needs local bypass capacitors

## Ground Plane Rules

- Never split ground plane under high-speed signals
- If split is necessary, bridge with capacitors at crossing points
- Stitch vias every 5-10mm along plane edges
- Maintain ground continuity under all clock signals
- Ground pour on unused areas (stitched to main ground)

## Clock Signal Routing

| Rule | Reason |
|------|--------|
| Route on inner layers | Shielded by ground planes |
| No stubs | Reflections cause harmonics |
| Series termination at source | Reduce edge rate at load |
| Guard traces (grounded) | Reduce coupling to adjacent |
| Keep short (< lambda/20) | Reduce radiation |

## Power Supply Layout for Low EMI

### Buck Converter Critical Loop

```
         Vin
          |
     +----+----+
     |  Input  |
     |   Cap   |    <-- This loop must be SMALL
     +----+----+
          |
    SW node (HOT!)
          |
     +----+----+
     |Inductor |
     +----+----+
          |
     +----+----+
     | Output  |
     |   Cap   |
     +----+----+
          |
         GND
```

- Input cap as close as possible to IC Vin and PGND
- Keep SW (switching node) copper area SMALL
- Output inductor close to IC
- Short, wide ground connections

## I/O Connector Filtering

| Connector Type | Filter |
|----------------|--------|
| USB | Common-mode choke + ESD TVS |
| Ethernet | Magnetics (built-in) + TVS |
| SPI/I2C (off-board) | Series resistor + TVS |
| Power input | Pi filter (C-L-C) |
| Antenna | Bandpass matching network |

## Shielding Techniques

- Via fence around sensitive analog areas (every 1-2mm)
- Ground pour with stitching vias on all layers
- Shield can pads for RF sections
- Faraday cage (via fence + top/bottom ground) for critical areas

## Component Placement for EMI

- Keep switching regulators away from board edges
- Place clock sources near center
- I/O filtering components at connector (before entry to board)
- Separate analog and digital power domains
- High-power components away from sensitive analog

## PCB Stackup for EMI (4-layer)

| Layer | Assignment | Notes |
|-------|------------|-------|
| L1 (Top) | Signals + Components | Route high-speed on inner |
| L2 | GND plane | Unbroken reference plane |
| L3 | Power plane | Split for multi-rail |
| L4 (Bottom) | Signals + Components | Secondary routing |

Key: L2 GND must be continuous under all high-speed signals on L1.

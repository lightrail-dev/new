---
name: placement-strategy
description: Component placement guidelines for PCB layout.
---

# Component Placement Strategy

## Placement Priority Order

### 1. Fixed-Position Components
- **Connectors**: Place at board edges per mechanical constraints
- **Mounting holes**: As defined in board outline
- **Switches/buttons**: User-accessible locations
- **LEDs**: Visible positions

### 2. MCU / Main IC
- Central or near-center placement
- Rotate for optimal pin routing
- Consider thermal pad orientation (heatsink side)
- Ensure adequate clearance for decoupling caps

### 3. Clock Components (Crystal/Oscillator)
- Within 5mm of MCU clock pins
- Guard traces on both sides
- No routing underneath crystal area
- Ground plane intact below crystal

### 4. Power Supply Components
- Near power input connector
- Buck converter: Input cap -> IC -> output cap -> inductor (tight loop)
- LDO: Input cap close to Vin, output cap close to Vout
- Consider thermal dissipation (place away from sensitive components)
- Keep switching node area small (reduces EMI)

### 5. Decoupling Capacitors
- Place as close to IC power pins as possible (< 2mm)
- Route directly to IC pin and ground via
- Smallest value caps closest to IC
- Bulk caps can be slightly further

### 6. Sensitive Analog Components
- Isolate from digital/switching noise sources
- Separate analog and digital ground regions (join at one point)
- Keep analog signal paths short
- Shield with ground pour

### 7. Remaining Components
- Group by functional block (matches schematic pages)
- Minimize trace lengths between connected parts
- Maintain consistent orientation for assembly
- Consider testability (test points accessible)

## Thermal Considerations

| Component | Guideline |
|-----------|-----------|
| QFN / DFN pads | Thermal vias (0.3mm, array of 4-9) under exposed pad |
| Power MOSFETs | Wide copper pour connected to drain |
| Voltage regulators | Thermal pad vias + copper pour |
| High-power resistors | Adequate copper area, away from ICs |

## Clearance Rules

| Area | Minimum Clearance |
|------|-------------------|
| Board edge to components | 1.0mm (0.5mm for SMD) |
| Board edge to traces | 0.5mm |
| Mounting hole to components | 2.0mm |
| High-voltage to low-voltage | Per creepage/clearance standard |

## Common Mistakes

- Crystal too far from MCU (causes clock integrity issues)
- Decoupling caps too far from IC pins
- Switching regulator with large loop area (EMI)
- Thermal pad without vias (overheating)
- Analog components near switching noise
- Connectors blocking adjacent component access

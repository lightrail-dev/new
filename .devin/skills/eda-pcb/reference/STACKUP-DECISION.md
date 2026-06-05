---
name: stackup-decision
description: Layer stackup selection guide for PCB design.
---

# PCB Layer Stackup Decision Guide

## When to Use Each Layer Count

| Layers | Use Case | Cost Factor |
|--------|----------|-------------|
| 2 | Simple designs, low-speed, hobby | 1x |
| 4 | Most commercial designs, USB, SPI | 2-3x |
| 6 | DDR, multiple power rails, RF | 4-5x |
| 8+ | High-speed digital, server, AI accelerator | 6-10x+ |

## 2-Layer Stackup

```
Layer 1 (Top)    : Signals + Components
Layer 2 (Bottom) : GND pour + Signals
```

**Suitable for:**
- Simple MCU designs (< 20 MHz clock)
- Low pin-count ICs
- No impedance-controlled signals
- Total power < 1W

**Limitations:**
- No shielded routing
- Poor EMI performance
- Cannot achieve controlled impedance reliably
- Limited routing density

## 4-Layer Stackup (Recommended Default)

```
Layer 1 (Top)    : Signals + Components
Layer 2 (Inner)  : GND plane (solid)
Layer 3 (Inner)  : Power plane (may split)
Layer 4 (Bottom) : Signals + Components
```

**Suitable for:**
- USB 2.0 (90 Ohm impedance achievable)
- SPI up to 50 MHz
- I2C any speed
- BLE/WiFi (with antenna keep-out)
- Moderate power designs (< 5W)
- Most commercial products

**Key benefit:** Solid GND on L2 gives controlled impedance for L1 signals.

## 6-Layer Stackup

```
Layer 1 : Signals (high-speed)
Layer 2 : GND
Layer 3 : Signals (general)
Layer 4 : Power
Layer 5 : GND
Layer 6 : Signals + Components
```

**Suitable for:**
- DDR3/DDR4 memory interfaces
- Gigabit Ethernet
- Multiple impedance requirements
- Dense BGA routing

## 32-Layer HDI Stackup (LightRail Accelerator)

For the LR-P3A 1.6T AI Compute Node:

```
Layers 1-4   : High-speed signals (PAM4, CXL)
Layer 5      : GND reference
Layers 6-10  : Signal routing (general)
Layer 11     : Power (VDD_CORE 0.8V)
Layer 12     : GND reference
Layers 13-20 : Signal + power distribution
Layer 21     : GND reference
Layer 22     : Power (VDD_IO)
Layers 23-28 : Signal routing
Layer 29     : GND reference
Layers 30-32 : Power delivery + signals
```

Material: Megtron-7 (Dk=3.4, Df=0.002 @ 10GHz)

## Stackup Selection Criteria

| Factor | 2-Layer | 4-Layer | 6-Layer | 8+ Layer |
|--------|---------|---------|---------|----------|
| Max clock speed | 20 MHz | 200 MHz | 1 GHz | 10+ GHz |
| Impedance control | No | Yes | Yes | Yes |
| EMI compliance | Difficult | Good | Very good | Excellent |
| Power integrity | Fair | Good | Very good | Excellent |
| Routing density | Low | Medium | High | Very high |
| Cost | Low | Medium | High | Very high |
| Lead time | Short | Standard | Longer | Longest |

## Thickness Options

| Total Thickness | Layers | Per-Layer |
|-----------------|--------|-----------|
| 0.8mm | 2-4 | Flex/thin |
| 1.0mm | 4 | Compact |
| 1.6mm | 2-6 | Standard |
| 2.0mm | 6-8 | Thick |
| 2.4mm+ | 8+ | HDI |

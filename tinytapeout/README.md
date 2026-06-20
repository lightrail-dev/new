# LightRail NCE Mini Compute Unit — TinyTapeout Sky130 Submission

![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg)

## Overview

An 8-bit Multiply-Accumulate (MAC) engine implementing the core compute cell of the **LightRail Neural Compute Engine (NCE)** — fabricated on SkyWater Sky130 via TinyTapeout shuttle.

### Features
- 8×8 unsigned multiply with 16-bit accumulator
- ReLU activation function (clips negative to zero)
- Configurable 0–7 bit right-shift for INT8 quantization
- Overflow/zero/sign status flags
- 4 operation modes: NOP, LOAD, MAC, ACTIVATE
- Runs at up to 50 MHz on Sky130

### Architecture
```
Weight Load → 8×8 Multiplier → 16-bit Accumulator → ReLU → Quantize Shift → Output
```

## Pinout

| Pin | Direction | Function |
|-----|-----------|----------|
| ui_in[7:0] | Input | Data (weight or activation) |
| uo_out[7:0] | Output | Result or status |
| uio_in[1:0] | Input | Opcode (NOP/LOAD/MAC/ACTIVATE) |
| uio_in[2] | Input | Output select (0=result, 1=status) |
| uio_in[5:3] | Input | Shift amount for quantization |
| clk | Input | System clock |
| rst_n | Input | Active-low reset |

## Usage

See [docs/info.md](docs/info.md) for detailed operation and test examples.

## Building

GDSII is generated automatically via GitHub Actions using the TinyTapeout `tt-gds-action@ttsky26c` (LibreLane + Sky130A PDK).

## Project Structure

```
tinytapeout/
├── src/
│   ├── project.v        # RTL: tt_um_lightrail_nce MAC unit
│   └── config.json      # OpenLane/LibreLane configuration
├── test/
│   ├── tb.v             # Verilog testbench wrapper
│   ├── test.py          # cocotb functional tests (5 tests)
│   └── Makefile         # cocotb simulation makefile
├── docs/
│   └── info.md          # Design documentation
├── info.yaml            # TinyTapeout project metadata
└── .github/workflows/   # GDS build + test CI
```

## Part of the LightRail AI Hardware Platform

This MAC unit is the fundamental building block of the full NCE compute core (128-way SIMD, HBM5 memory subsystem, TFLN optical interconnect). The TinyTapeout submission validates the core datapath in real silicon before scaling to the production 28nm SMIC tapeout.

---
*LightRail AI Labs — PA-2026-001*

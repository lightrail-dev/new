## How it works

The LightRail NCE Mini Compute Unit is a compact 8-bit Multiply-Accumulate (MAC) engine that demonstrates the fundamental compute operation of the Neural Compute Engine (NCE) — the core AI accelerator silicon designed by LightRail AI Labs.

### Architecture

```
ui_in[7:0] ──┬──────────────────────┐
             │                      │
         ┌───▼───┐            ┌─────▼─────┐
         │ reg_A │            │ Multiplier │
         │(weight)│──────────►│  8x8→16   │
         └───────┘            └─────┬─────┘
                                    │ product[15:0]
                              ┌─────▼─────┐
                              │Accumulator│◄── feedback
                              │  16-bit   │
                              └─────┬─────┘
                                    │
                              ┌─────▼─────┐
                              │   ReLU    │
                              │ + Shift   │
                              └─────┬─────┘
                                    │
                              ┌─────▼─────┐
                              │  Output   │──► uo_out[7:0]
                              │   Mux     │
                              └───────────┘
```

### Operation Modes (uio_in[1:0])

| Opcode | Name | Description |
|--------|------|-------------|
| 00 | NOP | Hold state, read outputs |
| 01 | LOAD | Load weight into reg_A, clear accumulator |
| 10 | MAC | Multiply reg_A × ui_in, add to accumulator |
| 11 | ACTIVATE | Apply ReLU + configurable right-shift |

### Control Bits (uio_in)

- `[1:0]` — Opcode (operation select)
- `[2]` — acc_sel: 0=read result, 1=read status register
- `[5:3]` — shift: right-shift amount (0–7) for post-MAC quantization
- `[7:6]` — Unused

### Status Register (uo_out when acc_sel=1)

- Bit 0: result_nonzero (activation output ≠ 0)
- Bit 1: sign (accumulator MSB, indicates "negative")
- Bit 2: zero (accumulator == 0)
- Bit 3: overflow (accumulator overflowed at any point)

## How to test

1. **Reset**: Assert rst_n low for ≥5 clock cycles
2. **Load weight**: Set ui_in = weight_value, uio_in = 0x01 (OP_LOAD), clock once
3. **MAC operation**: Set ui_in = activation_value, uio_in = 0x02 (OP_MAC), clock once per accumulation
4. **Activate**: Set uio_in = 0x03 | (shift << 3) (OP_ACTIVATE + shift amount), clock once
5. **Read result**: Set uio_in = 0x00 (OP_NOP), read uo_out

### Example: Compute 3×7 = 21

```
cycle 1: ui_in=3, uio_in=0x01  → Load weight=3
cycle 2: ui_in=7, uio_in=0x02  → MAC: acc = 3*7 = 21
cycle 3: uio_in=0x03           → Activate: ReLU(21) = 21
cycle 4: uio_in=0x00           → Read: uo_out = 21
```

### Example: Dot product [5,5]·[4,6] = 50

```
cycle 1: ui_in=5, uio_in=0x01  → Load weight=5
cycle 2: ui_in=4, uio_in=0x02  → MAC: acc = 5*4 = 20
cycle 3: ui_in=6, uio_in=0x02  → MAC: acc = 20 + 5*6 = 50
cycle 4: uio_in=0x03           → Activate: ReLU(50) = 50
cycle 5: uio_in=0x00           → Read: uo_out = 50
```

## External hardware

No external hardware required for basic operation. Connect:
- Clock source (up to 50 MHz) to clk
- Active-low reset to rst_n
- Data bus to ui_in[7:0]
- Control bus to uio_in[7:0]
- Read results from uo_out[7:0]

For neural network inference, chain multiple tiles: output of one MAC feeds ui_in of the next.

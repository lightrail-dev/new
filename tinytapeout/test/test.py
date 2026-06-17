# SPDX-FileCopyrightText: © 2026 LightRail AI Labs
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# Opcodes
OP_NOP      = 0b00
OP_LOAD     = 0b01
OP_MAC      = 0b10
OP_ACTIVATE = 0b11


def ctrl(opcode, acc_sel=0, shift=0):
    """Build control byte for uio_in."""
    return (opcode & 0x3) | ((acc_sel & 0x1) << 2) | ((shift & 0x7) << 3)


@cocotb.test()
async def test_mac_basic(dut):
    """Test basic multiply-accumulate: 3 * 7 = 21."""
    dut._log.info("Test: Basic MAC 3*7=21")
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Load weight A = 3
    dut.ui_in.value = 3
    dut.uio_in.value = ctrl(OP_LOAD)
    await ClockCycles(dut.clk, 1)

    # MAC: A(3) * input(7) -> accumulator = 21
    dut.ui_in.value = 7
    dut.uio_in.value = ctrl(OP_MAC)
    await ClockCycles(dut.clk, 1)

    # Activate (ReLU + no shift)
    dut.uio_in.value = ctrl(OP_ACTIVATE, shift=0)
    await ClockCycles(dut.clk, 1)

    # NOP + read result
    dut.uio_in.value = ctrl(OP_NOP, acc_sel=0)
    await ClockCycles(dut.clk, 1)

    assert dut.uo_out.value == 21, f"Expected 21, got {int(dut.uo_out.value)}"
    dut._log.info("PASS: 3*7 = 21")


@cocotb.test()
async def test_mac_accumulate(dut):
    """Test accumulation: 5*4 + 5*6 = 20 + 30 = 50."""
    dut._log.info("Test: Accumulate 5*4 + 5*6 = 50")
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Load weight A = 5
    dut.ui_in.value = 5
    dut.uio_in.value = ctrl(OP_LOAD)
    await ClockCycles(dut.clk, 1)

    # MAC: 5 * 4 = 20
    dut.ui_in.value = 4
    dut.uio_in.value = ctrl(OP_MAC)
    await ClockCycles(dut.clk, 1)

    # MAC: 5 * 6 = 30, accumulator = 20+30 = 50
    dut.ui_in.value = 6
    dut.uio_in.value = ctrl(OP_MAC)
    await ClockCycles(dut.clk, 1)

    # Activate
    dut.uio_in.value = ctrl(OP_ACTIVATE, shift=0)
    await ClockCycles(dut.clk, 1)

    # Read result
    dut.uio_in.value = ctrl(OP_NOP, acc_sel=0)
    await ClockCycles(dut.clk, 1)

    assert dut.uo_out.value == 50, f"Expected 50, got {int(dut.uo_out.value)}"
    dut._log.info("PASS: 5*4 + 5*6 = 50")


@cocotb.test()
async def test_relu_negative(dut):
    """Test ReLU clips negative accumulator to 0."""
    dut._log.info("Test: ReLU negative -> 0")
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Load weight A = 255 (will cause large product, simulating negative via overflow)
    # Actually, let's make the accumulator wrap negative:
    # Load A=200, MAC with 200 -> 200*200 = 40000 -> accumulator = 40000
    # 40000 in 16-bit = 0x9C40, MSB=1 -> treated as negative by ReLU
    dut.ui_in.value = 200
    dut.uio_in.value = ctrl(OP_LOAD)
    await ClockCycles(dut.clk, 1)

    dut.ui_in.value = 200
    dut.uio_in.value = ctrl(OP_MAC)
    await ClockCycles(dut.clk, 1)

    # Activate - accumulator MSB is 1, so ReLU should output 0
    dut.uio_in.value = ctrl(OP_ACTIVATE, shift=0)
    await ClockCycles(dut.clk, 1)

    # Read
    dut.uio_in.value = ctrl(OP_NOP, acc_sel=0)
    await ClockCycles(dut.clk, 1)

    assert dut.uo_out.value == 0, f"Expected 0 (ReLU negative), got {int(dut.uo_out.value)}"
    dut._log.info("PASS: ReLU clips negative to 0")


@cocotb.test()
async def test_shift_quantization(dut):
    """Test shift-right quantization: 128 >> 2 = 32."""
    dut._log.info("Test: Shift quantization 128>>2 = 32")
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # Load A=16, MAC with 8 -> 16*8 = 128
    dut.ui_in.value = 16
    dut.uio_in.value = ctrl(OP_LOAD)
    await ClockCycles(dut.clk, 1)

    dut.ui_in.value = 8
    dut.uio_in.value = ctrl(OP_MAC)
    await ClockCycles(dut.clk, 1)

    # Activate with shift=2 -> 128 >> 2 = 32
    dut.uio_in.value = ctrl(OP_ACTIVATE, shift=2)
    await ClockCycles(dut.clk, 1)

    # Read
    dut.uio_in.value = ctrl(OP_NOP, acc_sel=0)
    await ClockCycles(dut.clk, 1)

    assert dut.uo_out.value == 32, f"Expected 32, got {int(dut.uo_out.value)}"
    dut._log.info("PASS: 128>>2 = 32")


@cocotb.test()
async def test_status_register(dut):
    """Test status register readback."""
    dut._log.info("Test: Status register")
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # After reset, accumulator=0, result=0, overflow=0
    # Status: {4'b0, overflow=0, zero=1, sign=0, result_nonzero=0} = 0b00000100 = 4
    dut.uio_in.value = ctrl(OP_NOP, acc_sel=1)
    await ClockCycles(dut.clk, 1)

    status = int(dut.uo_out.value)
    dut._log.info(f"Status after reset: 0x{status:02x} (binary: {status:08b})")
    # zero flag should be set (bit 2)
    assert (status & 0x04) != 0, f"Zero flag not set, status=0x{status:02x}"
    dut._log.info("PASS: Zero flag set after reset")

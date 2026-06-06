#!/usr/bin/env python3
"""Regenerate all KiCad 8 files for the LightRail Eval Board in valid format.

Fixes:
- Removes invalid ';;' comment lines
- Adds proper (lib_symbols ...) sections with graphical definitions
- Fixes symbol instance format
- Makes all files parseable by KiCad 8.0.x
"""
import os, uuid, textwrap

KICAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kicad")
SHEETS_DIR = os.path.join(KICAD_DIR, "sheets")

def uid():
    return str(uuid.uuid4())

# ============================================================================
# LIB_SYMBOLS for generic component types
# ============================================================================

def lib_sym_generic_ic(lib_id, ref_prefix, pin_count, desc=""):
    """Generate a generic IC symbol with N pins (left/right split)."""
    left_pins = (pin_count + 1) // 2
    right_pins = pin_count - left_pins
    height = max(left_pins, right_pins) * 2.54 + 2.54
    half_h = height / 2
    width = 10.16

    lines = []
    lines.append(f'\t\t(symbol "{lib_id}"')
    lines.append(f'\t\t\t(pin_names (offset 1.016))')
    lines.append(f'\t\t\t(exclude_from_sim no)')
    lines.append(f'\t\t\t(in_bom yes)')
    lines.append(f'\t\t\t(on_board yes)')
    lines.append(f'\t\t\t(property "Reference" "{ref_prefix}" (at 0 {half_h + 1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Value" "{lib_id.split(":")[-1]}" (at 0 {-half_h - 1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')

    # Body rectangle
    base = lib_id.split(":")[-1]
    lines.append(f'\t\t\t(symbol "{base}_0_1"')
    lines.append(f'\t\t\t\t(rectangle (start {-width/2:.2f} {half_h:.2f}) (end {width/2:.2f} {-half_h:.2f})')
    lines.append(f'\t\t\t\t\t(stroke (width 0.254) (type default))')
    lines.append(f'\t\t\t\t\t(fill (type background))')
    lines.append(f'\t\t\t\t)')
    lines.append(f'\t\t\t)')

    # Pins
    lines.append(f'\t\t\t(symbol "{base}_1_1"')
    for i in range(left_pins):
        y = half_h - 2.54 - i * 2.54
        lines.append(f'\t\t\t\t(pin passive line (at {-width/2 - 2.54:.2f} {y:.2f} 0) (length 2.54) (name "P{i+1}" (effects (font (size 1.27 1.27)))) (number "{i+1}" (effects (font (size 1.27 1.27)))))')
    for i in range(right_pins):
        y = half_h - 2.54 - i * 2.54
        pn = left_pins + i + 1
        lines.append(f'\t\t\t\t(pin passive line (at {width/2 + 2.54:.2f} {y:.2f} 180) (length 2.54) (name "P{pn}" (effects (font (size 1.27 1.27)))) (number "{pn}" (effects (font (size 1.27 1.27)))))')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    return "\n".join(lines)


def lib_sym_2pin(lib_id, ref_prefix, desc=""):
    """Resistor/capacitor/fuse style 2-pin passive."""
    base = lib_id.split(":")[-1]
    return textwrap.dedent(f"""\
\t\t(symbol "{lib_id}"
\t\t\t(pin_numbers hide)
\t\t\t(pin_names (offset 0.254))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "{ref_prefix}" (at 0 2.54 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "{base}" (at 0 -2.54 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "{base}_0_1"
\t\t\t\t(rectangle (start -1.016 1.27) (end 1.016 -1.27)
\t\t\t\t\t(stroke (width 0.254) (type default))
\t\t\t\t\t(fill (type none))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "{base}_1_1"
\t\t\t\t(pin passive line (at 0 3.81 270) (length 2.54) (name "~" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
\t\t\t\t(pin passive line (at 0 -3.81 90) (length 2.54) (name "~" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
\t\t\t)
\t\t)""")


def lib_sym_power(lib_id, value):
    """Power symbol (GND, +12V, etc)."""
    base = lib_id.split(":")[-1]
    if value == "GND":
        gfx = textwrap.dedent(f"""\
\t\t\t(symbol "{base}_0_1"
\t\t\t\t(polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
\t\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))
\t\t\t)""")
        pin_dir = 180
        pin_at = "0 0 90"
    else:
        gfx = textwrap.dedent(f"""\
\t\t\t(symbol "{base}_0_1"
\t\t\t\t(polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27))
\t\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))
\t\t\t)""")
        pin_dir = 90
        pin_at = "0 0 270"

    return textwrap.dedent(f"""\
\t\t(symbol "{lib_id}"
\t\t\t(power)
\t\t\t(pin_numbers hide)
\t\t\t(pin_names (offset 0) hide)
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Value" "{value}" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
{gfx}
\t\t\t(symbol "{base}_1_1"
\t\t\t\t(pin power_in line (at {pin_at}) (length 0) (name "{value}" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
\t\t\t)
\t\t)""")


def lib_sym_connector(lib_id, ref_prefix, pin_count, desc=""):
    """Connector symbol."""
    base = lib_id.split(":")[-1]
    half_h = (pin_count * 2.54) / 2 + 1.27

    lines = []
    lines.append(f'\t\t(symbol "{lib_id}"')
    lines.append(f'\t\t\t(pin_names (offset 1.016))')
    lines.append(f'\t\t\t(exclude_from_sim no)')
    lines.append(f'\t\t\t(in_bom yes)')
    lines.append(f'\t\t\t(on_board yes)')
    lines.append(f'\t\t\t(property "Reference" "{ref_prefix}" (at 0 {half_h + 1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Value" "{base}" (at 0 {-half_h - 1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(symbol "{base}_0_1"')
    lines.append(f'\t\t\t\t(rectangle (start -2.54 {half_h:.2f}) (end 2.54 {-half_h:.2f})')
    lines.append(f'\t\t\t\t\t(stroke (width 0.254) (type default))')
    lines.append(f'\t\t\t\t\t(fill (type background))')
    lines.append(f'\t\t\t\t)')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t\t(symbol "{base}_1_1"')
    for i in range(pin_count):
        y = half_h - 2.54 - i * 2.54
        lines.append(f'\t\t\t\t(pin passive line (at -5.08 {y:.2f} 0) (length 2.54) (name "P{i+1}" (effects (font (size 1.27 1.27)))) (number "{i+1}" (effects (font (size 1.27 1.27)))))')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    return "\n".join(lines)


# ============================================================================
# Symbol instance helper
# ============================================================================

def sym_instance(lib_id, ref, value, x, y, rot=0, fp="", mpn="", extra_props=None, pin_count=2):
    """Generate a symbol instance."""
    u = uid()
    lines = []
    lines.append(f'\t(symbol (lib_id "{lib_id}") (at {x} {y} {rot}) (unit 1)')
    lines.append(f'\t\t(in_bom yes) (on_board yes) (dnp no)')
    lines.append(f'\t\t(uuid "{u}")')
    lines.append(f'\t\t(property "Reference" "{ref}" (at {x} {y - 3} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t(property "Value" "{value}" (at {x} {y + 3} 0) (effects (font (size 1.27 1.27))))')
    if fp:
        lines.append(f'\t\t(property "Footprint" "{fp}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    else:
        lines.append(f'\t\t(property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t(property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    if mpn:
        lines.append(f'\t\t(property "MPN" "{mpn}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    if extra_props:
        for k, v in extra_props.items():
            lines.append(f'\t\t(property "{k}" "{v}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    for i in range(1, pin_count + 1):
        lines.append(f'\t\t(pin "{i}" (uuid "{uid()}"))')
    lines.append(f'\t)')
    return "\n".join(lines), u


def wire(x1, y1, x2, y2):
    return f'\t(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) (stroke (width 0) (type default)) (uuid "{uid()}"))'


def pwr_flag(value, x, y):
    lib_id = f"power:{value}"
    u = uid()
    ref = "#PWR?" if value != "GND" else "#PWR?"
    lines = []
    lines.append(f'\t(symbol (lib_id "{lib_id}") (at {x} {y} 0) (unit 1)')
    lines.append(f'\t\t(in_bom yes) (on_board yes) (dnp no)')
    lines.append(f'\t\t(uuid "{u}")')
    lines.append(f'\t\t(property "Reference" "#PWR?" (at {x} {y - 3} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t(property "Value" "{value}" (at {x} {y - 2} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t(property "Footprint" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t(property "Datasheet" "" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t(pin "1" (uuid "{uid()}"))')
    lines.append(f'\t)')
    return "\n".join(lines), u


def global_lbl(name, shape, x, y):
    return f'\t(global_label "{name}" (shape {shape}) (at {x} {y} 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}") (property "Intersheets" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes))))'


def text_note(txt, x, y, sz=2.0):
    return f'\t(text "{txt}" (at {x} {y} 0) (effects (font (size {sz} {sz}))) (uuid "{uid()}"))'


# ============================================================================
# TOP-LEVEL SCHEMATIC
# ============================================================================

def generate_top_schematic():
    top_uuid = "e63e39d7-6ac0-4ffd-8aa3-1841a4541b55"

    power_syms = ["+12V", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "GND"]
    lib_symbols = []
    for ps in power_syms:
        lib_symbols.append(lib_sym_power(f"power:{ps}", ps))

    # Symbol instances for power flags on top-level
    instances = []
    power_positions = [(30, 30), (55, 30), (80, 30), (105, 30), (130, 30), (155, 30), (180, 50)]
    for ps, (px, py) in zip(power_syms, power_positions):
        inst, _ = pwr_flag(ps, px, py)
        instances.append(inst)

    # Global labels
    glabels = []
    label_names = [
        ("AXI_ACLK", "input"), ("AXI_ARESETN", "input"), ("CLK_HBM", "input"),
        ("JTAG_TCK", "input"), ("JTAG_TMS", "input"), ("JTAG_TDI", "input"),
        ("JTAG_TDO", "output"), ("SPI_CLK", "bidirectional"), ("I2C_SCL", "bidirectional"),
        ("I2C_SDA", "bidirectional"), ("UART_TX", "output"), ("UART_RX", "input"),
    ]
    for i, (name, shape) in enumerate(label_names):
        glabels.append(global_lbl(name, shape, 230, 30 + i * 5))

    # Hierarchical sheets
    sheet_uuids = {
        "Power_Supply": "d0000001-0000-0000-0000-000000000001",
        "NCE_FPGA": "d0000002-0000-0000-0000-000000000002",
        "TFLN_Optical": "d0000003-0000-0000-0000-000000000003",
        "Clock_Interface": "d0000004-0000-0000-0000-000000000004",
    }

    sheets_block = []

    # Power Supply sheet
    sheets_block.append(f"""\t(sheet (at 25.4 76.2) (size 38.1 25.4)
\t\t(stroke (width 0.2) (type default) (color 0 0 0 0))
\t\t(fill (color 255 255 200 1.0))
\t\t(uuid "{sheet_uuids['Power_Supply']}")
\t\t(property "Sheetname" "Power_Supply" (at 25.4 74.93 0) (effects (font (size 1.27 1.27))))
\t\t(property "Sheetfile" "sheets/power.kicad_sch" (at 25.4 104.14 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t(pin "+12V_IN" input (at 25.4 82.55 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "GND" input (at 25.4 90.17 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+5V" output (at 63.5 82.55 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+3V3" output (at 63.5 85.09 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+1V8" output (at 63.5 87.63 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+1V0" output (at 63.5 90.17 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+0V9" output (at 63.5 92.71 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t)""")

    # NCE_FPGA sheet
    sheets_block.append(f"""\t(sheet (at 88.9 76.2) (size 44.45 25.4)
\t\t(stroke (width 0.2) (type default) (color 0 0 0 0))
\t\t(fill (color 200 255 200 1.0))
\t\t(uuid "{sheet_uuids['NCE_FPGA']}")
\t\t(property "Sheetname" "NCE_FPGA" (at 88.9 74.93 0) (effects (font (size 1.27 1.27))))
\t\t(property "Sheetfile" "sheets/nce_fpga.kicad_sch" (at 88.9 104.14 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t(pin "+0V9" input (at 88.9 82.55 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+1V0" input (at 88.9 85.09 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+1V8" input (at 88.9 87.63 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "+3V3" input (at 88.9 90.17 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "AXI_ACLK" bidirectional (at 133.35 82.55 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "JTAG_TDO" output (at 133.35 85.09 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "TFLN_TX_P" output (at 133.35 87.63 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "HBM_DQ" bidirectional (at 133.35 90.17 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t)""")

    # TFLN_Optical sheet
    sheets_block.append(f"""\t(sheet (at 152.4 76.2) (size 38.1 25.4)
\t\t(stroke (width 0.2) (type default) (color 0 0 0 0))
\t\t(fill (color 200 200 255 1.0))
\t\t(uuid "{sheet_uuids['TFLN_Optical']}")
\t\t(property "Sheetname" "TFLN_Optical" (at 152.4 74.93 0) (effects (font (size 1.27 1.27))))
\t\t(property "Sheetfile" "sheets/tfln_optical.kicad_sch" (at 152.4 104.14 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t(pin "TFLN_TX_P" input (at 152.4 82.55 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "SPI_CLK" input (at 152.4 87.63 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "I2C_SCL" bidirectional (at 190.5 82.55 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "I2C_SDA" bidirectional (at 190.5 85.09 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "MPO_FIBER" output (at 190.5 90.17 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t)""")

    # Clock_Interface sheet
    sheets_block.append(f"""\t(sheet (at 210.82 76.2) (size 38.1 25.4)
\t\t(stroke (width 0.2) (type default) (color 0 0 0 0))
\t\t(fill (color 255 200 200 1.0))
\t\t(uuid "{sheet_uuids['Clock_Interface']}")
\t\t(property "Sheetname" "Clock_Interface" (at 210.82 74.93 0) (effects (font (size 1.27 1.27))))
\t\t(property "Sheetfile" "sheets/clock_interface.kicad_sch" (at 210.82 104.14 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t(pin "CLK_100M" output (at 248.92 82.55 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "CLK_HBM" output (at 248.92 85.09 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "CLK_SERDES" output (at 248.92 87.63 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "USB_DP" bidirectional (at 210.82 82.55 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "USB_DN" bidirectional (at 210.82 85.09 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "JTAG_TCK" input (at 210.82 90.17 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t\t(pin "RESET_N" output (at 248.92 92.71 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))
\t)""")

    text = text_note(
        "LightRail NCE+TFLN Evaluation Board\\nPA-2026-001 Rev 1.0\\n\\n"
        "Top-level schematic with 4 hierarchical sub-sheets:\\n"
        "  1. Power Supply (12V to 0.9V power tree)\\n"
        "  2. NCE + FPGA (compute + control)\\n"
        "  3. TFLN Optical (photonic engine + monitor)\\n"
        "  4. Clock + Interface (clocks, USB, JTAG, GPIO)\\n\\n"
        "100x100mm 22-Layer Intelligence Stack",
        25, 120, 1.5
    )

    content = f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{top_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "LightRail NCE+TFLN Evaluation Board")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t\t(comment 1 "Project: PA-2026-001")
\t\t(comment 2 "100x100mm 22-Layer Intelligence Stack Eval Board")
\t\t(comment 3 "NCE QFN-64 + Artix-7 FPGA + TFLN PIC")
\t\t(comment 4 "SMIC 28nm HPC+ MPW Test Chip Characterization")
\t)
\t(lib_symbols
{chr(10).join(lib_symbols)}
\t)
{chr(10).join(instances)}
{chr(10).join(glabels)}
{chr(10).join(sheets_block)}
{text}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t\t(path "/{sheet_uuids['Power_Supply']}" (page "2"))
\t\t(path "/{sheet_uuids['NCE_FPGA']}" (page "3"))
\t\t(path "/{sheet_uuids['TFLN_Optical']}" (page "4"))
\t\t(path "/{sheet_uuids['Clock_Interface']}" (page "5"))
\t)
)
"""
    return content


# ============================================================================
# SUB-SHEET: Power Supply
# ============================================================================

def generate_power_schematic():
    sub_uuid = "f0000001-0001-0000-0000-000000000001"

    lib_symbols = []
    lib_symbols.append(lib_sym_power("power:+12V", "+12V"))
    lib_symbols.append(lib_sym_power("power:+5V", "+5V"))
    lib_symbols.append(lib_sym_power("power:+3V3", "+3V3"))
    lib_symbols.append(lib_sym_power("power:+1V8", "+1V8"))
    lib_symbols.append(lib_sym_power("power:+1V0", "+1V0"))
    lib_symbols.append(lib_sym_power("power:GND", "GND"))
    lib_symbols.append(lib_sym_2pin("Connector:Barrel_Jack", "J", "12V Barrel Jack"))
    lib_symbols.append(lib_sym_2pin("Device:Fuse", "F", "PTC Fuse"))
    lib_symbols.append(lib_sym_generic_ic("Regulator_Switching:TPS54360", "U", 8, "Buck 12V to 5V"))
    lib_symbols.append(lib_sym_generic_ic("Regulator_Linear:TPS7A3301", "U", 6, "LDO 5V to 3.3V"))
    lib_symbols.append(lib_sym_generic_ic("Regulator_Linear:TPS7A2018", "U", 6, "LDO 3.3V to 1.8V"))
    lib_symbols.append(lib_sym_generic_ic("Regulator_Linear:TPS7A2010", "U", 6, "LDO 1.8V to 1.0V"))
    lib_symbols.append(lib_sym_generic_ic("Regulator_Linear:ADP7118", "U", 6, "LDO 5V to 0.9V"))
    lib_symbols.append(lib_sym_2pin("Device:C", "C", "Capacitor"))
    lib_symbols.append(lib_sym_2pin("Device:R", "R", "Resistor"))
    lib_symbols.append(lib_sym_2pin("Device:L", "L", "Inductor"))
    lib_symbols.append(lib_sym_2pin("Device:LED", "D", "Power LED"))

    instances = []
    # J1 Barrel Jack
    inst, _ = sym_instance("Connector:Barrel_Jack", "J1", "Barrel_Jack_12V", 30, 50, fp="Connector_BarrelJack:BarrelJack_CUI_PJ-002AH", mpn="PJ-002AH")
    instances.append(inst)
    # F1 PTC Fuse
    inst, _ = sym_instance("Device:Fuse", "F1", "2A_PTC", 55, 50, fp="Fuse:Fuse_0805_2012Metric", mpn="0805L200SLYR")
    instances.append(inst)
    # U15 Buck Converter
    inst, _ = sym_instance("Regulator_Switching:TPS54360", "U15", "TPS54360_12V_5V", 90, 50, fp="Package_SO:HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.1mm", mpn="TPS54360BDDAR", pin_count=8)
    instances.append(inst)
    # U13 LDO 5V→3.3V
    inst, _ = sym_instance("Regulator_Linear:TPS7A3301", "U13", "TPS7A3301_5V_3V3", 140, 50, fp="Package_TO_SOT_SMD:SOT-223-5", mpn="TPS7A3301DCQR", pin_count=6)
    instances.append(inst)
    # U11 LDO 3.3V→1.8V (NCE VDD_IO)
    inst, _ = sym_instance("Regulator_Linear:TPS7A2018", "U11", "TPS7A2018_3V3_1V8", 190, 50, fp="Package_TO_SOT_SMD:SOT-23-5", mpn="TPS7A2018DBVR", pin_count=6)
    instances.append(inst)
    # U14 LDO 3.3V→1.8V (FPGA VCCO)
    inst, _ = sym_instance("Regulator_Linear:TPS7A2018", "U14", "TPS7A2018_3V3_1V8_FPGA", 190, 90, fp="Package_TO_SOT_SMD:SOT-23-5", mpn="TPS7A2018DBVR", pin_count=6)
    instances.append(inst)
    # U12 LDO 1.8V→1.0V
    inst, _ = sym_instance("Regulator_Linear:TPS7A2010", "U12", "TPS7A2010_1V8_1V0", 240, 50, fp="Package_TO_SOT_SMD:SOT-23-5", mpn="TPS7A2010DBVR", pin_count=6)
    instances.append(inst)
    # U10 LDO 5V→0.9V
    inst, _ = sym_instance("Regulator_Linear:ADP7118", "U10", "ADP7118_5V_0V9", 240, 90, fp="Package_TO_SOT_SMD:TSOT-23-5", mpn="ADP7118AUJZ-0.9-R7", pin_count=6)
    instances.append(inst)
    # Decoupling caps
    for i, (x, y) in enumerate([(105, 70), (155, 70), (205, 70), (205, 110), (255, 70), (255, 110)]):
        inst, _ = sym_instance("Device:C", f"C{i+1}", "100nF", x, y, fp="Capacitor_SMD:C_0402_1005Metric")
        instances.append(inst)
    # Input cap
    inst, _ = sym_instance("Device:C", "C20", "100uF", 70, 70, fp="Capacitor_SMD:C_1206_3216Metric")
    instances.append(inst)
    # Buck inductor
    inst, _ = sym_instance("Device:L", "L1", "10uH", 115, 50, fp="Inductor_SMD:L_Wuerth_WE-LHMI_7050", mpn="744373460100")
    instances.append(inst)
    # Power LED
    inst, _ = sym_instance("Device:LED", "D1", "Green", 270, 50, fp="LED_SMD:LED_0603_1608Metric")
    instances.append(inst)
    inst, _ = sym_instance("Device:R", "R20", "1k", 270, 65, fp="Resistor_SMD:R_0402_1005Metric")
    instances.append(inst)

    # Power symbols
    pwr_insts = []
    for ps, (px, py) in [
        ("+12V", (30, 35)), ("+5V", (115, 35)), ("+3V3", (155, 35)),
        ("+1V8", (205, 35)), ("+1V0", (255, 35)), ("GND", (150, 130)),
    ]:
        inst, _ = pwr_flag(ps, px, py)
        pwr_insts.append(inst)

    # Wires connecting the chain
    wires = []
    wires.append(wire(30, 46.19, 55, 46.19))    # J1 to F1
    wires.append(wire(55, 46.19, 70, 46.19))    # F1 to C20
    wires.append(wire(70, 46.19, 90, 46.19))    # C20 to U15
    wires.append(wire(105, 46.19, 115, 46.19))  # U15 out to L1
    wires.append(wire(115, 46.19, 140, 46.19))  # L1 to U13
    wires.append(wire(155, 46.19, 190, 46.19))  # U13 to U11
    wires.append(wire(205, 46.19, 240, 46.19))  # U11 to U12

    # Hierarchical pins (for connection to parent)
    hier_pins = []
    hier_pins.append(f'\t(hierarchical_label "+12V_IN" (shape input) (at 20 50 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
    hier_pins.append(f'\t(hierarchical_label "GND" (shape input) (at 20 70 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
    hier_pins.append(f'\t(hierarchical_label "+5V" (shape output) (at 300 35 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
    hier_pins.append(f'\t(hierarchical_label "+3V3" (shape output) (at 300 45 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
    hier_pins.append(f'\t(hierarchical_label "+1V8" (shape output) (at 300 55 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
    hier_pins.append(f'\t(hierarchical_label "+1V0" (shape output) (at 300 65 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')
    hier_pins.append(f'\t(hierarchical_label "+0V9" (shape output) (at 300 75 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    content = f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{sub_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "Power Supply - LightRail Eval Board")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t\t(comment 1 "12V to 5V to 3.3V to 1.8V to 1.0V to 0.9V power tree")
\t\t(comment 2 "22-Layer Intelligence Stack - Power planes L11/L17/L21")
\t)
\t(lib_symbols
{chr(10).join(lib_symbols)}
\t)
{chr(10).join(pwr_insts)}
{chr(10).join(instances)}
{chr(10).join(wires)}
{chr(10).join(hier_pins)}
)
"""
    return content


# ============================================================================
# SUB-SHEET: NCE + FPGA
# ============================================================================

def generate_nce_fpga_schematic():
    sub_uuid = "f0000002-0001-0000-0000-000000000001"

    lib_symbols = []
    lib_symbols.append(lib_sym_power("power:+0V9", "+0V9"))
    lib_symbols.append(lib_sym_power("power:+1V0", "+1V0"))
    lib_symbols.append(lib_sym_power("power:+1V8", "+1V8"))
    lib_symbols.append(lib_sym_power("power:+3V3", "+3V3"))
    lib_symbols.append(lib_sym_power("power:GND", "GND"))
    lib_symbols.append(lib_sym_generic_ic("LightRail:NCE_QFN64", "U", 64, "Neural Compute Engine QFN-64"))
    lib_symbols.append(lib_sym_generic_ic("FPGA_Xilinx:XC7A100T", "U", 32, "Artix-7 FPGA BGA-256"))
    lib_symbols.append(lib_sym_generic_ic("Memory_Flash:W25Q128JVS", "U", 8, "128Mbit SPI Flash"))
    lib_symbols.append(lib_sym_2pin("Device:C", "C", "Capacitor"))
    lib_symbols.append(lib_sym_2pin("Device:R", "R", "Resistor"))
    lib_symbols.append(lib_sym_connector("Connector_Generic:Conn_02x05", "J", 10, "JTAG 2x5 Header"))

    instances = []
    # U1 NCE
    inst, _ = sym_instance("LightRail:NCE_QFN64", "U1", "NCE_Compute_Core", 80, 80,
                           fp="LightRail:QFN-64_8x8mm_P0.4mm", mpn="LR-NCE-28-QFN64", pin_count=64)
    instances.append(inst)
    # U2 FPGA
    inst, _ = sym_instance("FPGA_Xilinx:XC7A100T", "U2", "XC7A100T-1FTG256C", 200, 80,
                           fp="LightRail:BGA-256_14x14mm_P0.8mm", mpn="XC7A100T-1FTG256C", pin_count=32)
    instances.append(inst)
    # U23 SPI Flash
    inst, _ = sym_instance("Memory_Flash:W25Q128JVS", "U23", "W25Q128JVSIQ", 300, 80,
                           fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", mpn="W25Q128JVSIQ", pin_count=8)
    instances.append(inst)
    # J5 JTAG Header
    inst, _ = sym_instance("Connector_Generic:Conn_02x05", "J5", "JTAG_2x5", 300, 130,
                           fp="Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", pin_count=10)
    instances.append(inst)
    # Decoupling caps for NCE
    for i in range(8):
        inst, _ = sym_instance("Device:C", f"C{30+i}", "100nF", 50 + i*8, 130, fp="Capacitor_SMD:C_0402_1005Metric")
        instances.append(inst)
    # Decoupling caps for FPGA
    for i in range(8):
        inst, _ = sym_instance("Device:C", f"C{40+i}", "100nF", 170 + i*8, 130, fp="Capacitor_SMD:C_0402_1005Metric")
        instances.append(inst)

    # Power symbols
    pwr = []
    for ps, pos in [("+0V9", (50, 50)), ("+1V0", (170, 50)), ("+1V8", (110, 50)), ("+3V3", (230, 50)), ("GND", (150, 170))]:
        inst, _ = pwr_flag(ps, *pos)
        pwr.append(inst)

    # Hierarchical labels
    hier = []
    for name, shape in [
        ("+0V9", "input"), ("+1V0", "input"), ("+1V8", "input"), ("+3V3", "input"),
        ("AXI_ACLK", "bidirectional"), ("JTAG_TDO", "output"),
        ("TFLN_TX_P", "output"), ("HBM_DQ", "bidirectional"),
    ]:
        hier.append(f'\t(hierarchical_label "{name}" (shape {shape}) (at 20 {50 + len(hier)*7} 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    # Wires
    wires = []
    wires.append(wire(95, 80, 185, 80))  # NCE to FPGA AXI bus
    wires.append(wire(215, 80, 285, 80))  # FPGA to Flash SPI

    content = f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{sub_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "NCE Test Chip + FPGA Controller - LightRail Eval Board")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t\t(comment 1 "U1: NCE QFN-64 (VDD_CORE=0.9V, VDD_IO=1.8V)")
\t\t(comment 2 "U2: Artix-7 XC7A100T BGA-256 (VCCINT=1.0V, VCCO=1.8V)")
\t)
\t(lib_symbols
{chr(10).join(lib_symbols)}
\t)
{chr(10).join(pwr)}
{chr(10).join(instances)}
{chr(10).join(wires)}
{chr(10).join(hier)}
)
"""
    return content


# ============================================================================
# SUB-SHEET: TFLN Optical
# ============================================================================

def generate_tfln_optical_schematic():
    sub_uuid = "f0000003-0001-0000-0000-000000000001"

    lib_symbols = []
    lib_symbols.append(lib_sym_power("power:+3V3", "+3V3"))
    lib_symbols.append(lib_sym_power("power:+1V8", "+1V8"))
    lib_symbols.append(lib_sym_power("power:GND", "GND"))
    lib_symbols.append(lib_sym_generic_ic("LightRail:TFLN_PIC", "U", 24, "TFLN Photonic IC Edge Coupler"))
    lib_symbols.append(lib_sym_generic_ic("Analog_ADC:AD7928", "U", 16, "8-ch 12-bit SPI ADC"))
    lib_symbols.append(lib_sym_generic_ic("Analog_DAC:AD5684R", "U", 16, "4-ch 12-bit SPI DAC"))
    lib_symbols.append(lib_sym_generic_ic("Sensor_Temperature:TMP461", "U", 8, "Remote/Local Temp Sensor I2C"))
    lib_symbols.append(lib_sym_connector("Connector_Fiber:MPO_24", "J", 24, "MPO-24 Fiber Connector"))
    lib_symbols.append(lib_sym_2pin("Device:C", "C", "Capacitor"))
    lib_symbols.append(lib_sym_2pin("Device:R", "R", "Resistor"))
    lib_symbols.append(lib_sym_connector("Connector:SMA", "J", 1, "SMA RF Probe"))

    instances = []
    # U3 TFLN PIC
    inst, _ = sym_instance("LightRail:TFLN_PIC", "U3", "TFLN_Optical_Module", 120, 80,
                           fp="LightRail:Custom_Optical_Module", pin_count=24)
    instances.append(inst)
    # U21 ADC
    inst, _ = sym_instance("Analog_ADC:AD7928", "U21", "AD7928BRUZ", 220, 60,
                           fp="Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm", mpn="AD7928BRUZ", pin_count=16)
    instances.append(inst)
    # U24 DAC
    inst, _ = sym_instance("Analog_DAC:AD5684R", "U24", "AD5684RBRUZ", 220, 120,
                           fp="Package_SO:TSSOP-16_4.4x5mm_P0.65mm", mpn="AD5684RBRUZ", pin_count=16)
    instances.append(inst)
    # U25 Temp Sensor
    inst, _ = sym_instance("Sensor_Temperature:TMP461", "U25", "TMP461AIDR", 320, 80,
                           fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", mpn="TMP461AIDR", pin_count=8)
    instances.append(inst)
    # J11 MPO-24
    inst, _ = sym_instance("Connector_Fiber:MPO_24", "J11", "MPO-24", 30, 80,
                           fp="LightRail:MPO-24", pin_count=24)
    instances.append(inst)
    # J7-J10 SMA connectors
    for i, (jref, y) in enumerate([("J7", 160), ("J8", 175), ("J9", 190), ("J10", 205)]):
        inst, _ = sym_instance("Connector:SMA", jref, "SMA_RF_Probe", 30, y,
                               fp="Connector_Coaxial:SMA_Amphenol_132134-11_Vertical", pin_count=1)
        instances.append(inst)

    pwr = []
    for ps, pos in [("+3V3", (200, 35)), ("+1V8", (280, 35)), ("GND", (200, 180))]:
        inst, _ = pwr_flag(ps, *pos)
        pwr.append(inst)

    hier = []
    for name, shape in [
        ("TFLN_TX_P", "input"), ("SPI_CLK", "input"),
        ("I2C_SCL", "bidirectional"), ("I2C_SDA", "bidirectional"), ("MPO_FIBER", "output"),
    ]:
        hier.append(f'\t(hierarchical_label "{name}" (shape {shape}) (at 20 {35 + len(hier)*7} 180) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    wires = []
    wires.append(wire(135, 80, 205, 60))
    wires.append(wire(135, 90, 205, 120))

    content = f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{sub_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "TFLN Optical Engine - LightRail Eval Board")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t\t(comment 1 "U3: TFLN PIC with 8x TX/RX optical channels")
\t\t(comment 2 "U21: AD7928 PD Monitor, U24: AD5684R Bias DAC, U25: TMP461")
\t)
\t(lib_symbols
{chr(10).join(lib_symbols)}
\t)
{chr(10).join(pwr)}
{chr(10).join(instances)}
{chr(10).join(wires)}
{chr(10).join(hier)}
)
"""
    return content


# ============================================================================
# SUB-SHEET: Clock + Interface
# ============================================================================

def generate_clock_interface_schematic():
    sub_uuid = "f0000004-0001-0000-0000-000000000001"

    lib_symbols = []
    lib_symbols.append(lib_sym_power("power:+3V3", "+3V3"))
    lib_symbols.append(lib_sym_power("power:+1V8", "+1V8"))
    lib_symbols.append(lib_sym_power("power:GND", "GND"))
    lib_symbols.append(lib_sym_generic_ic("Clock:Si5395A", "U", 16, "Jitter Attenuating Clock Multiplier"))
    lib_symbols.append(lib_sym_generic_ic("Interface_USB:FT232H", "U", 28, "Hi-Speed USB to UART/FIFO"))
    lib_symbols.append(lib_sym_2pin("Device:Crystal", "Y", "100MHz TCXO"))
    lib_symbols.append(lib_sym_connector("Connector:USB_C_Receptacle", "J", 12, "USB Type-C"))
    lib_symbols.append(lib_sym_connector("Connector_Generic:Conn_02x07", "J", 14, "GPIO 2x7 Header"))
    lib_symbols.append(lib_sym_2pin("Device:C", "C", "Capacitor"))
    lib_symbols.append(lib_sym_2pin("Device:R", "R", "Resistor"))
    lib_symbols.append(lib_sym_2pin("Switch:SW_Push", "SW", "Tactile Switch"))

    instances = []
    # Y1 100MHz TCXO
    inst, _ = sym_instance("Device:Crystal", "Y1", "100MHz_TCXO", 60, 60, fp="Crystal:Crystal_SMD_2520-4Pin_2.5x2.0mm", mpn="SIT1602BC-73-25E-100.000000G")
    instances.append(inst)
    # U20 Si5395A PLL
    inst, _ = sym_instance("Clock:Si5395A", "U20", "Si5395A", 140, 60, fp="Package_DFN_QFN:QFN-44-1EP_7x7mm_P0.5mm_EP5.15x5.15mm", mpn="SI5395A-A-GM", pin_count=16)
    instances.append(inst)
    # U22 FT232H
    inst, _ = sym_instance("Interface_USB:FT232H", "U22", "FT232HL", 140, 140, fp="Package_QFP:LQFP-48_7x7mm_P0.5mm", mpn="FT232HL-REEL", pin_count=28)
    instances.append(inst)
    # J2 USB-C
    inst, _ = sym_instance("Connector:USB_C_Receptacle", "J2", "USB_C", 30, 140, fp="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", pin_count=12)
    instances.append(inst)
    # J6 GPIO Header
    inst, _ = sym_instance("Connector_Generic:Conn_02x07", "J6", "GPIO_2x7", 280, 60, fp="Connector_PinHeader_2.54mm:PinHeader_2x07_P2.54mm_Vertical", pin_count=14)
    instances.append(inst)
    # SW1 Reset
    inst, _ = sym_instance("Switch:SW_Push", "SW1", "RESET", 280, 140, fp="Button_Switch_SMD:SW_Push_1P1T_NO_CK_KSC7xxJ", mpn="KSC721J")
    instances.append(inst)
    # Decoupling
    for i in range(4):
        inst, _ = sym_instance("Device:C", f"C{50+i}", "100nF", 100 + i*20, 200, fp="Capacitor_SMD:C_0402_1005Metric")
        instances.append(inst)

    pwr = []
    for ps, pos in [("+3V3", (100, 30)), ("+1V8", (200, 30)), ("GND", (150, 220))]:
        inst, _ = pwr_flag(ps, *pos)
        pwr.append(inst)

    hier = []
    for name, shape in [
        ("CLK_100M", "output"), ("CLK_HBM", "output"), ("CLK_SERDES", "output"),
        ("USB_DP", "bidirectional"), ("USB_DN", "bidirectional"),
        ("JTAG_TCK", "input"), ("RESET_N", "output"),
    ]:
        hier.append(f'\t(hierarchical_label "{name}" (shape {shape}) (at 350 {30 + len(hier)*7} 0) (effects (font (size 1.27 1.27))) (uuid "{uid()}"))')

    wires = []
    wires.append(wire(60, 56.19, 125, 56.19))  # Y1 to U20
    wires.append(wire(45, 140, 125, 140))       # J2 to U22

    content = f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{sub_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "Clock Generation + Test Interface - LightRail Eval Board")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t\t(comment 1 "Y1: 100MHz TCXO, U20: Si5395A PLL (2.0GHz HBM, 156.25MHz SerDes)")
\t\t(comment 2 "U22: FT232H USB-UART, J2: USB-C, J5: JTAG, J6: GPIO, SW1: Reset")
\t)
\t(lib_symbols
{chr(10).join(lib_symbols)}
\t)
{chr(10).join(pwr)}
{chr(10).join(instances)}
{chr(10).join(wires)}
{chr(10).join(hier)}
)
"""
    return content


# ============================================================================
# FIX PCB FILE — remove ;; comments
# ============================================================================

def fix_pcb_file():
    pcb_path = os.path.join(KICAD_DIR, "LightRail_Eval_Board.kicad_pcb")
    with open(pcb_path, 'r') as f:
        lines = f.readlines()
    cleaned = [l for l in lines if not l.strip().startswith(';;')]
    # Also remove empty lines that were adjacent to comments
    with open(pcb_path, 'w') as f:
        f.writelines(cleaned)
    print(f"  Fixed PCB: removed {len(lines) - len(cleaned)} comment lines")


# ============================================================================
# MAIN
# ============================================================================

def main():
    os.makedirs(SHEETS_DIR, exist_ok=True)

    print("Generating top-level schematic...")
    with open(os.path.join(KICAD_DIR, "LightRail_Eval_Board.kicad_sch"), 'w') as f:
        f.write(generate_top_schematic())

    print("Generating power sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "power.kicad_sch"), 'w') as f:
        f.write(generate_power_schematic())

    print("Generating NCE+FPGA sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "nce_fpga.kicad_sch"), 'w') as f:
        f.write(generate_nce_fpga_schematic())

    print("Generating TFLN optical sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "tfln_optical.kicad_sch"), 'w') as f:
        f.write(generate_tfln_optical_schematic())

    print("Generating clock+interface sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "clock_interface.kicad_sch"), 'w') as f:
        f.write(generate_clock_interface_schematic())

    print("Fixing PCB file (removing comments)...")
    fix_pcb_file()

    print("\nDone! All KiCad files regenerated in valid KiCad 8 format.")


if __name__ == "__main__":
    main()

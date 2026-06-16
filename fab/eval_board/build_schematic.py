#!/usr/bin/env python3
"""Build complete, fully-connected KiCad 8 schematics for the LightRail Eval Board.

Produces 5 hierarchical .kicad_sch files with:
- Real named pins for every IC
- Wire stubs + labels on every pin (connectivity via net names)
- Power symbols for rails/GND
- Global labels for cross-sheet signals
- Hierarchical labels for sheet-pin connectivity

Author: LightRail AI Hardware Engineering
"""
import os, uuid, math, json

KICAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kicad")
SHEETS_DIR = os.path.join(KICAD_DIR, "sheets")

# Connectivity registry: ref -> {value, lib_id, footprint, pins:{pad:net}}
# Captured by place_instance() so the PCB builder shares the schematic's
# single source of truth for net membership (keeps schematic and layout LVS-consistent).
NETLIST = {}

# Deterministic UUIDs for reproducibility
_uuid_counter = 0
def uid():
    global _uuid_counter
    _uuid_counter += 1
    return f"a{_uuid_counter:07d}-0000-4000-8000-{_uuid_counter:012d}"

# Pin length from body edge to tip
PIN_LEN = 2.54
STUB_LEN = 5.08  # wire stub length from pin tip
GRID = 1.27  # KiCad default ERC grid

def snap(v):
    """Snap a coordinate to the 1.27mm grid."""
    return round(v / GRID) * GRID

# Power rails
POWER_RAILS = {"+12V", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "+12V_RAW", "+5V_USB"}
GND_NETS = {"GND", "GNDA"}
# Global nets (cross-sheet)
GLOBAL_NETS = {
    "AXI_ACLK", "AXI_ARESETN", "AXI_AWADDR", "AXI_AWVALID", "AXI_AWREADY",
    "AXI_WDATA", "AXI_WVALID", "AXI_WREADY", "AXI_BRESP", "AXI_BVALID",
    "AXI_ARADDR", "AXI_ARVALID", "AXI_ARREADY", "AXI_RDATA", "AXI_RVALID",
    "CLK_CORE", "CLK_REF", "CLK_SERDES", "CLK_HBM", "CLK_100M",
    "SPI_CLK", "SPI_MOSI", "SPI_MISO", "SPI_CS_FLASH", "SPI_CS_ADC", "SPI_CS_DAC",
    "I2C_SCL", "I2C_SDA",
    "JTAG_TCK", "JTAG_TMS", "JTAG_TDI", "JTAG_TDO", "JTAG_TRST",
    "UART_TX", "UART_RX",
    "RESET_N",
    "TFLN_TX_P0", "TFLN_TX_N0", "TFLN_TX_P1", "TFLN_TX_N1",
    "TFLN_TX_P2", "TFLN_TX_N2", "TFLN_TX_P3", "TFLN_TX_N3",
    "USB_DP", "USB_DN",
    "TEMP_ALERT",
}


# ============================================================================
# SYMBOL LIBRARY GENERATION
# ============================================================================

def make_lib_sym_ic(lib_id, ref_prefix, left_pins, right_pins, desc=""):
    """Generate IC lib symbol. left/right_pins = list of (number, name)."""
    n_left = len(left_pins)
    n_right = len(right_pins)
    height = max(n_left, n_right) * 2.54 + 5.08
    half_h = height / 2
    width = 12.7
    half_w = width / 2

    base = lib_id.split(":")[-1]
    lines = []
    lines.append(f'\t\t(symbol "{lib_id}"')
    lines.append(f'\t\t\t(pin_names (offset 1.016))')
    lines.append(f'\t\t\t(exclude_from_sim no) (in_bom yes) (on_board yes)')
    lines.append(f'\t\t\t(property "Reference" "{ref_prefix}" (at 0 {half_h+1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Value" "{base}" (at 0 {-half_h-1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    # Body
    lines.append(f'\t\t\t(symbol "{base}_0_1"')
    lines.append(f'\t\t\t\t(rectangle (start {-half_w:.2f} {half_h:.2f}) (end {half_w:.2f} {-half_h:.2f})')
    lines.append(f'\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))')
    lines.append(f'\t\t\t)')
    # Pins
    lines.append(f'\t\t\t(symbol "{base}_1_1"')
    pin_geom = {}  # name -> (lib_x, lib_y, side)
    for i, (num, name) in enumerate(left_pins):
        y = half_h - 2.54 - i * 2.54
        x = -half_w - PIN_LEN
        lines.append(f'\t\t\t\t(pin passive line (at {x:.2f} {y:.2f} 0) (length {PIN_LEN:.2f}) (name "{name}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))')
        pin_geom[str(num)] = (x, y, 'L')
    for i, (num, name) in enumerate(right_pins):
        y = half_h - 2.54 - i * 2.54
        x = half_w + PIN_LEN
        lines.append(f'\t\t\t\t(pin passive line (at {x:.2f} {y:.2f} 180) (length {PIN_LEN:.2f}) (name "{name}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))')
        pin_geom[str(num)] = (x, y, 'R')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    return '\n'.join(lines), pin_geom


def make_lib_sym_passive(lib_id, ref_prefix, desc=""):
    """2-pin passive (R/C/L/Fuse/LED/Ferrite). Vertical. Pin 1 top, pin 2 bottom."""
    base = lib_id.split(":")[-1]
    lines = []
    lines.append(f'\t\t(symbol "{lib_id}"')
    lines.append(f'\t\t\t(pin_names (offset 0) hide) (exclude_from_sim no) (in_bom yes) (on_board yes)')
    lines.append(f'\t\t\t(property "Reference" "{ref_prefix}" (at 2.54 0 90) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Value" "{base}" (at -2.54 0 90) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(symbol "{base}_0_1"')
    lines.append(f'\t\t\t\t(rectangle (start -1.016 2.54) (end 1.016 -2.54)')
    lines.append(f'\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t\t(symbol "{base}_1_1"')
    lines.append(f'\t\t\t\t(pin passive line (at 0 3.81 270) (length 1.27) (name "1" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0)))))')
    lines.append(f'\t\t\t\t(pin passive line (at 0 -3.81 90) (length 1.27) (name "2" (effects (font (size 1.0 1.0)))) (number "2" (effects (font (size 1.0 1.0)))))')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    # Pin geometry: pin 1 tip at (0, 3.81) going UP, pin 2 at (0, -3.81) going DOWN
    pin_geom = {"1": (0, 3.81, 'U'), "2": (0, -3.81, 'D')}
    return '\n'.join(lines), pin_geom


def make_lib_sym_power(value):
    """Power symbol. Pin at (0,0). GND: glyph below, others: glyph above."""
    lib_id = f"power:{value}"
    is_gnd = value in ("GND", "GNDA")
    lines = []
    lines.append(f'\t\t(symbol "{lib_id}"')
    lines.append(f'\t\t\t(power) (pin_names (offset 0)) (exclude_from_sim no) (in_bom no) (on_board yes)')
    lines.append(f'\t\t\t(property "Reference" "#{value}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Value" "{value}" (at 0 {-2.54 if not is_gnd else 2.54:.2f} 0) (effects (font (size 1.0 1.0))))')
    lines.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    if is_gnd:
        lines.append(f'\t\t\t(symbol "{value}_0_1"')
        lines.append(f'\t\t\t\t(polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0.254) (type default)) (fill (type none)))')
        lines.append(f'\t\t\t\t(polyline (pts (xy -0.762 -0.508) (xy 0.762 -0.508)) (stroke (width 0.254) (type default)) (fill (type none)))')
        lines.append(f'\t\t\t\t(polyline (pts (xy -0.254 -1.016) (xy 0.254 -1.016)) (stroke (width 0.254) (type default)) (fill (type none)))')
        lines.append(f'\t\t\t)')
        lines.append(f'\t\t\t(symbol "{value}_1_1"')
        lines.append(f'\t\t\t\t(pin power_in line (at 0 0 270) (length 0) (name "{value}" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0)))))')
        lines.append(f'\t\t\t)')
    else:
        lines.append(f'\t\t\t(symbol "{value}_0_1"')
        lines.append(f'\t\t\t\t(polyline (pts (xy -0.762 0.508) (xy 0 1.27) (xy 0.762 0.508)) (stroke (width 0.254) (type default)) (fill (type none)))')
        lines.append(f'\t\t\t)')
        lines.append(f'\t\t\t(symbol "{value}_1_1"')
        lines.append(f'\t\t\t\t(pin power_in line (at 0 0 90) (length 0) (name "{value}" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0)))))')
        lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    return '\n'.join(lines)


def make_lib_sym_pwr_flag():
    """PWR_FLAG symbol to mark a net as power-driven for ERC."""
    lines = []
    lines.append('\t\t(symbol "power:PWR_FLAG"')
    lines.append('\t\t\t(power) (pin_numbers hide) (pin_names (offset 0)) (exclude_from_sim no) (in_bom no) (on_board yes)')
    lines.append('\t\t\t(property "Reference" "#FLG" (at 0 1.905 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append('\t\t\t(property "Value" "PWR_FLAG" (at 0 3.81 0) (effects (font (size 1.27 1.27))))')
    lines.append('\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append('\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append('\t\t\t(symbol "PWR_FLAG_0_0"')
    lines.append('\t\t\t\t(pin power_out line (at 0 0 90) (length 0) (name "pwr" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))')
    lines.append('\t\t\t)')
    lines.append('\t\t\t(symbol "PWR_FLAG_0_1"')
    lines.append('\t\t\t\t(polyline (pts (xy 0 0) (xy 0 1.016) (xy -1.016 1.524) (xy 0 2.032) (xy 1.016 1.524) (xy 0 1.016)) (stroke (width 0) (type default)) (fill (type none)))')
    lines.append('\t\t\t)')
    lines.append('\t\t)')
    return '\n'.join(lines)


def place_pwr_flag(net, x, y):
    """Place a PWR_FLAG on a net via a short wire to a power symbol."""
    x = snap(x); y = snap(y)
    lines = []
    # power symbol at (x,y) pin up, wire up to flag
    rot = 0
    lines.append(f'\t(symbol (lib_id "power:{net}") (at {x:.2f} {y:.2f} {rot}) (unit 1)')
    lines.append(f'\t\t(in_bom no) (on_board yes) (dnp no)')
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append(f'\t\t(property "Reference" "#{net}F" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.0 1.0)) (hide yes)))')
    lines.append(f'\t\t(property "Value" "{net}" (at {x-2.54:.2f} {y:.2f} 0) (effects (font (size 0.762 0.762))))')
    lines.append(f'\t\t(pin "1" (uuid "{uid()}"))')
    lines.append(f'\t)')
    # wire from power pin (at x,y) up to flag location
    fy = y - STUB_LEN
    lines.append(f'\t(wire (pts (xy {x:.2f} {y:.2f}) (xy {x:.2f} {fy:.2f})) (stroke (width 0) (type default)))')
    lines.append(f'\t(symbol (lib_id "power:PWR_FLAG") (at {x:.2f} {fy:.2f} 0) (unit 1)')
    lines.append(f'\t\t(in_bom no) (on_board yes) (dnp no)')
    lines.append(f'\t\t(uuid "{uid()}")')
    lines.append(f'\t\t(property "Reference" "#FLG_{net}" (at {x:.2f} {fy-2.54:.2f} 0) (effects (font (size 1.0 1.0)) (hide yes)))')
    lines.append(f'\t\t(property "Value" "PWR_FLAG" (at {x:.2f} {fy+2.54:.2f} 0) (effects (font (size 0.762 0.762))))')
    lines.append(f'\t\t(pin "1" (uuid "{uid()}"))')
    lines.append(f'\t)')
    return '\n'.join(lines)


def make_lib_sym_connector(lib_id, ref_prefix, pin_names, desc=""):
    """Connector symbol with named pins on left side."""
    n = len(pin_names)
    height = n * 2.54 + 5.08
    half_h = height / 2
    width = 7.62
    half_w = width / 2
    base = lib_id.split(":")[-1]
    lines = []
    lines.append(f'\t\t(symbol "{lib_id}"')
    lines.append(f'\t\t\t(pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)')
    lines.append(f'\t\t\t(property "Reference" "{ref_prefix}" (at 0 {half_h+1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Value" "{base}" (at 0 {-half_h-1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    lines.append(f'\t\t\t(symbol "{base}_0_1"')
    lines.append(f'\t\t\t\t(rectangle (start {-half_w:.2f} {half_h:.2f}) (end {half_w:.2f} {-half_h:.2f})')
    lines.append(f'\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t\t(symbol "{base}_1_1"')
    pin_geom = {}
    for i, pname in enumerate(pin_names):
        y = half_h - 2.54 - i * 2.54
        x = -half_w - PIN_LEN
        num = str(i + 1)
        lines.append(f'\t\t\t\t(pin passive line (at {x:.2f} {y:.2f} 0) (length {PIN_LEN:.2f}) (name "{pname}" (effects (font (size 1.0 1.0)))) (number "{num}" (effects (font (size 1.0 1.0)))))')
        pin_geom[num] = (x, y, 'L')
    lines.append(f'\t\t\t)')
    lines.append(f'\t\t)')
    return '\n'.join(lines), pin_geom


# ============================================================================
# INSTANCE + WIRING GENERATION
# ============================================================================

def place_instance(lib_id, ref, value, ix, iy, pin_geom, pin_nets, footprint="", mpn=""):
    """Place a component instance and generate wire stubs + labels for each pin.
    
    pin_nets: dict {pin_number_str: net_name}. Pins not in dict are left unconnected.
    Returns (instance_text, wires_and_labels_text).
    """
    base = lib_id.split(":")[-1]
    ix = snap(ix); iy = snap(iy)
    # Record connectivity for the PCB builder (single source of truth)
    NETLIST[ref] = {
        "value": value,
        "lib_id": lib_id,
        "footprint": footprint,
        "mpn": mpn,
        "sch_x": ix,
        "sch_y": iy,
        "pins": dict(pin_nets),
    }
    inst_lines = []
    inst_lines.append(f'\t(symbol (lib_id "{lib_id}") (at {ix:.2f} {iy:.2f} 0) (unit 1)')
    inst_lines.append(f'\t\t(in_bom yes) (on_board yes) (dnp no)')
    inst_lines.append(f'\t\t(uuid "{uid()}")')
    inst_lines.append(f'\t\t(property "Reference" "{ref}" (at {ix:.2f} {iy-2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
    inst_lines.append(f'\t\t(property "Value" "{value}" (at {ix:.2f} {iy+2.54:.2f} 0) (effects (font (size 1.27 1.27))))')
    if footprint:
        inst_lines.append(f'\t\t(property "Footprint" "{footprint}" (at {ix:.2f} {iy:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    if mpn:
        inst_lines.append(f'\t\t(property "MPN" "{mpn}" (at {ix:.2f} {iy:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    # Pin UUIDs
    for pnum in sorted(pin_geom.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        inst_lines.append(f'\t\t(pin "{pnum}" (uuid "{uid()}"))')
    inst_lines.append(f'\t)')
    
    # Generate wires and labels for connected pins
    conn_lines = []
    for pnum, net in pin_nets.items():
        if pnum not in pin_geom:
            continue
        lib_x, lib_y, side = pin_geom[pnum]
        # Sheet coordinates (Y flip: sheet Y down, lib Y up)
        tip_x = ix + lib_x
        tip_y = iy - lib_y
        
        # Stub direction
        if side == 'L':
            end_x, end_y = tip_x - STUB_LEN, tip_y
            label_angle = 180
        elif side == 'R':
            end_x, end_y = tip_x + STUB_LEN, tip_y
            label_angle = 0
        elif side == 'U':
            end_x, end_y = tip_x, tip_y - STUB_LEN
            label_angle = 90
        else:  # D
            end_x, end_y = tip_x, tip_y + STUB_LEN
            label_angle = 270
        
        # Wire from tip to stub end
        conn_lines.append(f'\t(wire (pts (xy {tip_x:.2f} {tip_y:.2f}) (xy {end_x:.2f} {end_y:.2f}))')
        conn_lines.append(f'\t\t(stroke (width 0) (type default)))')
        
        # Label or power symbol at stub end
        if net in GND_NETS or net in POWER_RAILS:
            # Place power symbol
            rot = 0 if side == 'D' else (180 if side == 'U' else (90 if side == 'L' else 270))
            pwr_val = net
            conn_lines.append(f'\t(symbol (lib_id "power:{pwr_val}") (at {end_x:.2f} {end_y:.2f} {rot}) (unit 1)')
            conn_lines.append(f'\t\t(in_bom no) (on_board yes) (dnp no)')
            conn_lines.append(f'\t\t(uuid "{uid()}")')
            conn_lines.append(f'\t\t(property "Reference" "#{pwr_val}" (at {end_x:.2f} {end_y:.2f} 0) (effects (font (size 1.0 1.0)) (hide yes)))')
            conn_lines.append(f'\t\t(property "Value" "{pwr_val}" (at {end_x+1.27:.2f} {end_y:.2f} 0) (effects (font (size 0.762 0.762))))')
            conn_lines.append(f'\t\t(pin "1" (uuid "{uid()}"))')
            conn_lines.append(f'\t)')
        elif net in GLOBAL_NETS:
            conn_lines.append(f'\t(global_label "{net}" (shape bidirectional) (at {end_x:.2f} {end_y:.2f} {label_angle})')
            conn_lines.append(f'\t\t(effects (font (size 1.27 1.27)))')
            conn_lines.append(f'\t\t(uuid "{uid()}"))')
        else:
            conn_lines.append(f'\t(label "{net}" (at {end_x:.2f} {end_y:.2f} {label_angle})')
            conn_lines.append(f'\t\t(effects (font (size 1.27 1.27)))')
            conn_lines.append(f'\t\t(uuid "{uid()}"))')
    
    return '\n'.join(inst_lines), '\n'.join(conn_lines)


def hier_label(name, shape, x, y, angle=0):
    """Hierarchical label."""
    return f'\t(hierarchical_label "{name}" (shape {shape}) (at {x:.2f} {y:.2f} {angle})\n\t\t(effects (font (size 1.27 1.27)))\n\t\t(uuid "{uid()}"))'


def text_note(text, x, y, sz=1.27):
    """Text annotation."""
    return f'\t(text "{text}" (at {x:.2f} {y:.2f} 0) (effects (font (size {sz:.2f} {sz:.2f}))))'


# ============================================================================
# SHEET DEFINITIONS
# ============================================================================

SHEET_UUIDS = {
    "Power_Supply": "aa000001-1111-4000-8000-000000000001",
    "NCE_FPGA": "aa000002-2222-4000-8000-000000000002",
    "TFLN_Optical": "aa000003-3333-4000-8000-000000000003",
    "Clock_Interface": "aa000004-4444-4000-8000-000000000004",
}
TOP_UUID = "bb000000-0000-4000-8000-000000000000"


# ============================================================================
# TOP-LEVEL SCHEMATIC
# ============================================================================

def generate_top():
    """Top-level schematic: hierarchical sheet symbols with pins + inter-sheet wires."""
    # Collect power symbols needed
    power_syms = set()
    for rail in ["+12V", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "GND"]:
        power_syms.add(rail)
    
    lib_syms = []
    for p in sorted(power_syms):
        lib_syms.append(make_lib_sym_power(p))
    
    content_parts = []
    
    # Sheet symbols for 4 sub-sheets
    sheets = []
    
    # Power Supply sheet (left side)
    pwr_pins = [
        ("+12V_IN", "input", 0),
        ("GND", "input", 2.54),
        ("+5V", "output", 5.08),
        ("+3V3", "output", 7.62),
        ("+1V8", "output", 10.16),
        ("+1V0", "output", 12.7),
        ("+0V9", "output", 15.24),
    ]
    sheets.append(_sheet_block("Power_Supply", "sheets/power.kicad_sch",
                               30, 30, 40, 22, pwr_pins, "255 255 194"))
    
    # NCE + FPGA sheet (center-left)
    nce_pins = [
        ("AXI_ACLK", "input", 0),
        ("AXI_ARESETN", "input", 2.54),
        ("CLK_CORE", "input", 5.08),
        ("CLK_REF", "input", 7.62),
        ("JTAG_TCK", "input", 10.16),
        ("JTAG_TMS", "input", 12.7),
        ("JTAG_TDI", "input", 15.24),
        ("JTAG_TDO", "output", 17.78),
        ("SPI_CLK", "output", 20.32),
        ("TFLN_TX_P0", "output", 22.86),
        ("TFLN_TX_N0", "output", 25.4),
        ("UART_TX", "output", 27.94),
        ("UART_RX", "input", 30.48),
    ]
    sheets.append(_sheet_block("NCE_FPGA", "sheets/nce_fpga.kicad_sch",
                               80, 30, 45, 38, nce_pins, "194 255 194"))
    
    # TFLN Optical sheet (center-right)
    tfln_pins = [
        ("TFLN_TX_P0", "input", 0),
        ("TFLN_TX_N0", "input", 2.54),
        ("SPI_CLK", "input", 5.08),
        ("SPI_MOSI", "input", 7.62),
        ("SPI_MISO", "output", 10.16),
        ("SPI_CS_ADC", "input", 12.7),
        ("SPI_CS_DAC", "input", 15.24),
        ("I2C_SCL", "bidirectional", 17.78),
        ("I2C_SDA", "bidirectional", 20.32),
        ("TEMP_ALERT", "output", 22.86),
    ]
    sheets.append(_sheet_block("TFLN_Optical", "sheets/tfln_optical.kicad_sch",
                               135, 30, 45, 30, tfln_pins, "194 220 255"))
    
    # Clock + Interface sheet (right)
    clk_pins = [
        ("CLK_CORE", "output", 0),
        ("CLK_REF", "output", 2.54),
        ("CLK_SERDES", "output", 5.08),
        ("CLK_HBM", "output", 7.62),
        ("CLK_100M", "output", 10.16),
        ("USB_DP", "bidirectional", 12.7),
        ("USB_DN", "bidirectional", 15.24),
        ("JTAG_TCK", "output", 17.78),
        ("RESET_N", "output", 20.32),
        ("UART_TX", "input", 22.86),
        ("UART_RX", "output", 25.4),
    ]
    sheets.append(_sheet_block("Clock_Interface", "sheets/clock_interface.kicad_sch",
                               190, 30, 45, 32, clk_pins, "255 210 210"))
    
    # Cross-sheet connectivity is via design-wide global labels placed inside each
    # sub-sheet (on wired pins). The top sheet stays clean: organizational boxes only.
    glabels = []
    
    text = text_note(
        "LightRail NCE+TFLN Evaluation Board\\n"
        "PA-2026-001 Rev 1.0\\n"
        "100x100mm 22-Layer Intelligence Stack\\n\\n"
        "4 Hierarchical Sub-Sheets:\\n"
        "1. Power Supply (12V → 0.9V)\\n"
        "2. NCE + FPGA Compute\\n"
        "3. TFLN Optical Engine\\n"
        "4. Clock + Interface",
        30, 75, 1.5
    )
    
    return f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{TOP_UUID}")
\t(paper "A3")
\t(title_block
\t\t(title "LightRail NCE+TFLN Evaluation Board")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t\t(comment 1 "PA-2026-001 | 22-Layer Intelligence Stack")
\t\t(comment 2 "NCE QFN-64 + Artix-7 FPGA + TFLN PIC + Si5395A PLL")
\t)
\t(lib_symbols
{chr(10).join(lib_syms)}
\t)
{chr(10).join(sheets)}
{chr(10).join(glabels)}
{text}
\t(sheet_instances
\t\t(path "/" (page "1"))
\t\t(path "/{SHEET_UUIDS['Power_Supply']}" (page "2"))
\t\t(path "/{SHEET_UUIDS['NCE_FPGA']}" (page "3"))
\t\t(path "/{SHEET_UUIDS['TFLN_Optical']}" (page "4"))
\t\t(path "/{SHEET_UUIDS['Clock_Interface']}" (page "5"))
\t)
)
"""


def _sheet_block(name, filename, x, y, w, h, pins, fill_rgb):
    """Generate a sheet block with pins."""
    r, g, b = fill_rgb.split()
    lines = []
    lines.append(f'\t(sheet (at {x:.2f} {y:.2f}) (size {w:.2f} {h:.2f})')
    lines.append(f'\t\t(stroke (width 0.2) (type default) (color 0 0 0 0))')
    lines.append(f'\t\t(fill (color {r} {g} {b} 1.0))')
    lines.append(f'\t\t(uuid "{SHEET_UUIDS[name]}")')
    lines.append(f'\t\t(property "Sheetname" "{name}" (at {x:.2f} {y-1.27:.2f} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'\t\t(property "Sheetfile" "{filename}" (at {x:.2f} {y+h+1.27:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))')
    # Sheets are organizational; cross-sheet nets connect via design-wide global labels.
    lines.append(f'\t)')
    return '\n'.join(lines)


# ============================================================================
# POWER SUPPLY SUB-SHEET
# ============================================================================

def generate_power():
    """Full power supply schematic: 12V barrel jack → fuse → buck 5V → LDOs."""
    lib_syms = []
    instances = []
    connections = []
    
    # Power symbols needed
    for rail in ["+12V", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "GND", "+12V_RAW"]:
        lib_syms.append(make_lib_sym_power(rail))
    
    # -- J1 Barrel Jack (2 pins: Tip=+12V_RAW, Sleeve=GND)
    j1_lib, j1_geom = make_lib_sym_passive("Connector:Barrel_Jack", "J", "12V DC Input")
    lib_syms.append(j1_lib)
    j1_nets = {"1": "+12V_RAW", "2": "GND"}
    inst, conn = place_instance("Connector:Barrel_Jack", "J1", "DC_12V", 40, 50, j1_geom, j1_nets,
                                 "Connector_BarrelJack:BarrelJack_CUI_PJ-002AH", "PJ-002AH")
    instances.append(inst); connections.append(conn)
    
    # -- F1 PTC Fuse 2A
    f1_lib, f1_geom = make_lib_sym_passive("Device:Fuse", "F", "2A PTC Resettable")
    lib_syms.append(f1_lib)
    f1_nets = {"1": "+12V_RAW", "2": "+12V"}
    inst, conn = place_instance("Device:Fuse", "F1", "2A", 55, 50, f1_geom, f1_nets,
                                 "Fuse:Fuse_0805", "0805L200SLYR")
    instances.append(inst); connections.append(conn)
    
    # -- C11 bulk tantalum 100uF at input
    c_lib, c_geom = make_lib_sym_passive("Device:C", "C", "Capacitor")
    lib_syms.append(c_lib)
    inst, conn = place_instance("Device:C", "C11", "100uF", 70, 55, c_geom,
                                 {"1": "+12V", "2": "GND"}, "Capacitor_SMD:C_7343", "T520D107M016ATE070")
    instances.append(inst); connections.append(conn)
    
    # -- C1a bulk 22uF input
    inst, conn = place_instance("Device:C", "C1a", "22uF", 80, 55, c_geom,
                                 {"1": "+12V", "2": "GND"}, "Capacitor_SMD:C_0805", "GRM21BR61E226ME44L")
    instances.append(inst); connections.append(conn)
    
    # -- U15 TPS54360 Buck 12V→5V (8 pins)
    u15_left = [("1", "BOOT"), ("2", "VIN"), ("3", "EN"), ("4", "RT/CLK")]
    u15_right = [("5", "FB"), ("6", "COMP"), ("7", "GND"), ("8", "PH")]
    u15_lib, u15_geom = make_lib_sym_ic("Regulator_Switching:TPS54360", "U", u15_left, u15_right, "3.5A Buck 12V→5V")
    lib_syms.append(u15_lib)
    u15_nets = {"2": "+12V", "3": "+12V", "7": "GND", "8": "SW_5V",
                "5": "FB_5V", "6": "COMP_5V", "1": "BOOT_5V", "4": "GND"}
    inst, conn = place_instance("Regulator_Switching:TPS54360", "U15", "TPS54360", 110, 50,
                                 u15_geom, u15_nets, "Package_SO:HSOP-8", "TPS54360DDAR")
    instances.append(inst); connections.append(conn)
    
    # -- L1 Inductor (SW→+5V)
    l_lib, l_geom = make_lib_sym_passive("Device:L", "L", "Power Inductor")
    lib_syms.append(l_lib)
    inst, conn = place_instance("Device:L", "L1", "4.7uH", 135, 50, l_geom,
                                 {"1": "SW_5V", "2": "+5V"}, "Inductor_SMD:L_5x5mm", "744043004R7")
    instances.append(inst); connections.append(conn)
    
    # -- C1b output cap 22uF
    inst, conn = place_instance("Device:C", "C1b", "22uF", 145, 55, c_geom,
                                 {"1": "+5V", "2": "GND"}, "Capacitor_SMD:C_0805", "GRM21BR61E226ME44L")
    instances.append(inst); connections.append(conn)
    
    # -- U13 LDO 5V→3.3V (6 pins)
    ldo_left = [("1", "IN"), ("2", "EN"), ("3", "NR/SS")]
    ldo_right = [("4", "OUT"), ("5", "GND"), ("6", "NC")]
    u13_lib, u13_geom = make_lib_sym_ic("Regulator_Linear:TPS7A3301", "U", ldo_left, ldo_right, "LDO 3.3V 300mA")
    lib_syms.append(u13_lib)
    u13_nets = {"1": "+5V", "2": "+5V", "3": "NR_3V3", "4": "+3V3", "5": "GND", "6": "GND"}
    inst, conn = place_instance("Regulator_Linear:TPS7A3301", "U13", "TPS7A3301", 170, 45,
                                 u13_geom, u13_nets, "Package_TO_SOT_SMD:SOT-23-5", "TPS7A3301DBVR")
    instances.append(inst); connections.append(conn)
    
    # -- Decoupling on 3.3V
    inst, conn = place_instance("Device:C", "C2a", "10uF", 195, 50, c_geom,
                                 {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0603", "GRM188R61E106MA73D")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:C", "C5a", "100nF", 205, 50, c_geom,
                                 {"1": "+3V3", "2": "GND"}, "Capacitor_SMD:C_0402", "GRM155R71E104KA88D")
    instances.append(inst); connections.append(conn)
    
    # -- U11 LDO 3.3V→1.8V
    u11_lib, u11_geom = make_lib_sym_ic("Regulator_Linear:TPS7A2018", "U", ldo_left, ldo_right, "LDO 1.8V 300mA")
    lib_syms.append(u11_lib)
    u11_nets = {"1": "+3V3", "2": "+3V3", "3": "NR_1V8", "4": "+1V8", "5": "GND", "6": "GND"}
    inst, conn = place_instance("Regulator_Linear:TPS7A2018", "U11", "TPS7A2018", 170, 80,
                                 u11_geom, u11_nets, "Package_TO_SOT_SMD:SOT-23-5", "TPS7A2018DBVR")
    instances.append(inst); connections.append(conn)
    
    # Decoupling 1.8V
    inst, conn = place_instance("Device:C", "C2b", "10uF", 195, 85, c_geom,
                                 {"1": "+1V8", "2": "GND"}, "Capacitor_SMD:C_0603", "GRM188R61E106MA73D")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:C", "C5b", "100nF", 205, 85, c_geom,
                                 {"1": "+1V8", "2": "GND"}, "Capacitor_SMD:C_0402", "GRM155R71E104KA88D")
    instances.append(inst); connections.append(conn)
    
    # -- U14 LDO 3.3V→1.8V (FPGA VCCO, same rail)
    inst, conn = place_instance("Regulator_Linear:TPS7A2018", "U14", "TPS7A2018", 230, 45,
                                 u11_geom, {"1": "+3V3", "2": "+3V3", "3": "NR_1V8F", "4": "+1V8", "5": "GND", "6": "GND"},
                                 "Package_TO_SOT_SMD:SOT-23-5", "TPS7A2018DBVR")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:C", "C2c", "10uF", 255, 50, c_geom,
                                 {"1": "+1V8", "2": "GND"}, "Capacitor_SMD:C_0603", "GRM188R61E106MA73D")
    instances.append(inst); connections.append(conn)
    
    # -- U12 LDO 1.8V→1.0V
    u12_lib, u12_geom = make_lib_sym_ic("Regulator_Linear:TPS7A2010", "U", ldo_left, ldo_right, "LDO 1.0V 300mA")
    lib_syms.append(u12_lib)
    u12_nets = {"1": "+1V8", "2": "+1V8", "3": "NR_1V0", "4": "+1V0", "5": "GND", "6": "GND"}
    inst, conn = place_instance("Regulator_Linear:TPS7A2010", "U12", "TPS7A2010", 230, 80,
                                 u12_geom, u12_nets, "Package_TO_SOT_SMD:SOT-23-5", "TPS7A2010DBVR")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:C", "C4a", "1uF", 255, 85, c_geom,
                                 {"1": "+1V0", "2": "GND"}, "Capacitor_SMD:C_0402", "GRM155R61E105KA12D")
    instances.append(inst); connections.append(conn)
    
    # -- U10 ADP7118 LDO 1.8V→0.9V (5-pin)
    adp_left = [("1", "IN"), ("2", "EN"), ("3", "GND")]
    adp_right = [("4", "OUT"), ("5", "NR")]
    u10_lib, u10_geom = make_lib_sym_ic("Regulator_Linear:ADP7118", "U", adp_left, adp_right, "LDO 0.9V 150mA")
    lib_syms.append(u10_lib)
    u10_nets = {"1": "+1V8", "2": "+1V8", "3": "GND", "4": "+0V9", "5": "NR_0V9"}
    inst, conn = place_instance("Regulator_Linear:ADP7118", "U10", "ADP7118", 290, 50,
                                 u10_geom, u10_nets, "Package_TO_SOT_SMD:TSOT-23-5", "ADP7118AUJZ-0.9-R7")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:C", "C4b", "1uF", 315, 55, c_geom,
                                 {"1": "+0V9", "2": "GND"}, "Capacitor_SMD:C_0402", "GRM155R61E105KA12D")
    instances.append(inst); connections.append(conn)
    
    # -- D1 Power LED + R5 current limit
    r_lib, r_geom = make_lib_sym_passive("Device:R", "R", "Resistor")
    lib_syms.append(r_lib)
    d_lib, d_geom = make_lib_sym_passive("Device:LED", "D", "LED")
    lib_syms.append(d_lib)
    inst, conn = place_instance("Device:R", "R5a", "330", 330, 50, r_geom,
                                 {"1": "+3V3", "2": "LED_A"}, "Resistor_SMD:R_0402", "RC0402FR-07330RL")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:LED", "D1", "Green", 330, 65, d_geom,
                                 {"1": "LED_A", "2": "GND"}, "LED_SMD:LED_0603", "150060GS75000")
    instances.append(inst); connections.append(conn)
    
    # PWR_FLAG on each rail so ERC sees them as driven (all rails are global power symbols)
    lib_syms.append(make_lib_sym_pwr_flag())
    extras = []
    flag_rails = ["+12V_RAW", "+12V", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "GND"]
    for i, rail in enumerate(flag_rails):
        extras.append(place_pwr_flag(rail, 30 + i*12, 130))
    hlabels = extras
    
    text = text_note("Power Supply Tree: 12V→5V→3.3V→1.8V→1.0V→0.9V\\nAll rails locally decoupled", 30, 120, 1.5)
    
    return _wrap_subsheet("Power Supply - LightRail Eval Board",
                          "f0000001-0001-4000-8000-000000000001",
                          lib_syms, instances, connections, hlabels, text)


# ============================================================================
# NCE + FPGA SUB-SHEET
# ============================================================================

def generate_nce_fpga():
    """NCE test chip + Artix-7 FPGA + SPI Flash + JTAG."""
    lib_syms = []
    instances = []
    connections = []
    
    for rail in ["+0V9", "+1V0", "+1V8", "+3V3", "GND"]:
        lib_syms.append(make_lib_sym_power(rail))
    
    c_lib, c_geom = make_lib_sym_passive("Device:C", "C", "Capacitor")
    lib_syms.append(c_lib)
    r_lib, r_geom = make_lib_sym_passive("Device:R", "R", "Resistor")
    lib_syms.append(r_lib)
    
    # -- U1 NCE Test Chip QFN-64 (key pins)
    u1_left = [
        ("1", "VDD_CORE"), ("2", "VDD_CORE"), ("3", "VDD_IO"), ("4", "VDD_IO"),
        ("5", "GND"), ("6", "GND"), ("7", "GND"), ("8", "GND"),
        ("9", "AXI_ACLK"), ("10", "AXI_ARESETN"),
        ("11", "AXI_AWADDR"), ("12", "AXI_AWVALID"), ("13", "AXI_AWREADY"),
        ("14", "AXI_WDATA"), ("15", "AXI_WVALID"), ("16", "AXI_WREADY"),
        ("17", "AXI_BRESP"), ("18", "AXI_BVALID"),
        ("19", "AXI_ARADDR"), ("20", "AXI_ARVALID"), ("21", "AXI_ARREADY"),
        ("22", "AXI_RDATA"), ("23", "AXI_RVALID"),
        ("24", "CLK_CORE"), ("25", "CLK_REF"),
        ("26", "JTAG_TCK"), ("27", "JTAG_TMS"), ("28", "JTAG_TDI"), ("29", "JTAG_TDO"),
        ("30", "SPI_CLK"), ("31", "SPI_MOSI"), ("32", "SPI_MISO"),
    ]
    u1_right = [
        ("33", "TFLN_TX_P0"), ("34", "TFLN_TX_N0"), ("35", "TFLN_TX_P1"), ("36", "TFLN_TX_N1"),
        ("37", "TFLN_TX_P2"), ("38", "TFLN_TX_N2"), ("39", "TFLN_TX_P3"), ("40", "TFLN_TX_N3"),
        ("41", "HBM_DQ0"), ("42", "HBM_DQ1"), ("43", "HBM_DQ2"), ("44", "HBM_DQ3"),
        ("45", "HBM_DQ4"), ("46", "HBM_DQ5"), ("47", "HBM_DQ6"), ("48", "HBM_DQ7"),
        ("49", "I2C_SCL"), ("50", "I2C_SDA"),
        ("51", "UART_TX"), ("52", "UART_RX"),
        ("53", "GPIO0"), ("54", "GPIO1"), ("55", "GPIO2"), ("56", "GPIO3"),
        ("57", "TEMP_ALERT"), ("58", "PG_CORE"), ("59", "STATUS_LED"),
        ("60", "RESET_N"),
        ("61", "GND"), ("62", "GND"), ("63", "VDD_CORE"), ("64", "VDD_IO"),
    ]
    u1_lib, u1_geom = make_lib_sym_ic("LightRail:NCE_QFN64", "U", u1_left, u1_right, "Neural Compute Engine SMIC 28nm")
    lib_syms.append(u1_lib)
    u1_nets = {
        "1": "+0V9", "2": "+0V9", "3": "+1V8", "4": "+1V8",
        "5": "GND", "6": "GND", "7": "GND", "8": "GND",
        "9": "AXI_ACLK", "10": "AXI_ARESETN",
        "11": "AXI_AWADDR", "12": "AXI_AWVALID", "13": "AXI_AWREADY",
        "14": "AXI_WDATA", "15": "AXI_WVALID", "16": "AXI_WREADY",
        "17": "AXI_BRESP", "18": "AXI_BVALID",
        "19": "AXI_ARADDR", "20": "AXI_ARVALID", "21": "AXI_ARREADY",
        "22": "AXI_RDATA", "23": "AXI_RVALID",
        "24": "CLK_CORE", "25": "CLK_REF",
        "26": "JTAG_TCK", "27": "JTAG_TMS", "28": "JTAG_TDI", "29": "JTAG_TDO",
        "30": "SPI_CLK", "31": "SPI_MOSI", "32": "SPI_MISO",
        "33": "TFLN_TX_P0", "34": "TFLN_TX_N0", "35": "TFLN_TX_P1", "36": "TFLN_TX_N1",
        "37": "TFLN_TX_P2", "38": "TFLN_TX_N2", "39": "TFLN_TX_P3", "40": "TFLN_TX_N3",
        "41": "HBM_DQ0", "42": "HBM_DQ1", "43": "HBM_DQ2", "44": "HBM_DQ3",
        "45": "HBM_DQ4", "46": "HBM_DQ5", "47": "HBM_DQ6", "48": "HBM_DQ7",
        "49": "I2C_SCL", "50": "I2C_SDA",
        "51": "UART_TX", "52": "UART_RX",
        "53": "NCE_GPIO0", "54": "NCE_GPIO1", "55": "NCE_GPIO2", "56": "NCE_GPIO3",
        "57": "TEMP_ALERT", "58": "NCE_PG", "59": "NCE_STATUS",
        "60": "RESET_N",
        "61": "GND", "62": "GND", "63": "+0V9", "64": "+1V8",
    }
    inst, conn = place_instance("LightRail:NCE_QFN64", "U1", "NCE_TEST_CHIP", 80, 80,
                                 u1_geom, u1_nets, "Package_DFN_QFN:QFN-64_8x8mm_P0.4mm", "LR-NCE-MPW-001")
    instances.append(inst); connections.append(conn)
    
    # NCE decoupling: 4x 100nF on 0.9V, 4x 100nF on 1.8V
    for i, xoff in enumerate([60, 65, 70, 75]):
        ref = f"C{30+i}"
        inst, conn = place_instance("Device:C", ref, "100nF", xoff, 140, c_geom,
                                     {"1": "+0V9", "2": "GND"})
        instances.append(inst); connections.append(conn)
    for i, xoff in enumerate([80, 85, 90, 95]):
        ref = f"C{34+i}"
        inst, conn = place_instance("Device:C", ref, "100nF", xoff, 140, c_geom,
                                     {"1": "+1V8", "2": "GND"})
        instances.append(inst); connections.append(conn)
    
    # -- U2 Artix-7 FPGA (simplified 32-pin representation of key signals)
    u2_left = [
        ("1", "VCCINT"), ("2", "VCCINT"), ("3", "VCCAUX"), ("4", "VCCO"),
        ("5", "GND"), ("6", "GND"), ("7", "GND"), ("8", "GND"),
        ("9", "AXI_ACLK"), ("10", "AXI_ARESETN"),
        ("11", "AXI_AWADDR"), ("12", "AXI_AWVALID"), ("13", "AXI_WDATA"), ("14", "AXI_WVALID"),
        ("15", "AXI_RDATA"), ("16", "AXI_RVALID"),
    ]
    u2_right = [
        ("17", "CFG_MOSI"), ("18", "CFG_MISO"), ("19", "CFG_SCK"), ("20", "CFG_CS"),
        ("21", "JTAG_TCK"), ("22", "JTAG_TMS"), ("23", "JTAG_TDI"), ("24", "JTAG_TDO"),
        ("25", "CLK_CORE"), ("26", "CLK_REF"),
        ("27", "UART_TX"), ("28", "UART_RX"),
        ("29", "GPIO_0"), ("30", "GPIO_1"), ("31", "GPIO_2"), ("32", "GPIO_3"),
    ]
    u2_lib, u2_geom = make_lib_sym_ic("FPGA_Xilinx:XC7A100T", "U", u2_left, u2_right, "Artix-7 100T FPGA")
    lib_syms.append(u2_lib)
    u2_nets = {
        "1": "+1V0", "2": "+1V0", "3": "+1V8", "4": "+1V8",
        "5": "GND", "6": "GND", "7": "GND", "8": "GND",
        "9": "AXI_ACLK", "10": "AXI_ARESETN",
        "11": "AXI_AWADDR", "12": "AXI_AWVALID", "13": "AXI_WDATA", "14": "AXI_WVALID",
        "15": "AXI_RDATA", "16": "AXI_RVALID",
        "17": "FLASH_MOSI", "18": "FLASH_MISO", "19": "FLASH_SCK", "20": "FLASH_CS",
        "21": "JTAG_TCK", "22": "JTAG_TMS", "23": "JTAG_TDI", "24": "JTAG_TDO",
        "25": "CLK_CORE", "26": "CLK_REF",
        "27": "UART_TX", "28": "UART_RX",
        "29": "FPGA_GPIO0", "30": "FPGA_GPIO1", "31": "FPGA_GPIO2", "32": "FPGA_GPIO3",
    }
    inst, conn = place_instance("FPGA_Xilinx:XC7A100T", "U2", "XC7A100T", 220, 80,
                                 u2_geom, u2_nets, "Package_BGA:BGA-256_14x14mm_P0.8mm", "XC7A100T-1FTG256C")
    instances.append(inst); connections.append(conn)
    
    # FPGA decoupling: 8x 4.7uF + 8x 100nF
    for i in range(4):
        inst, conn = place_instance("Device:C", f"C{38+i}", "4.7uF", 200+i*5, 140, c_geom,
                                     {"1": "+1V0", "2": "GND"})
        instances.append(inst); connections.append(conn)
    for i in range(4):
        inst, conn = place_instance("Device:C", f"C{42+i}", "100nF", 225+i*5, 140, c_geom,
                                     {"1": "+1V8", "2": "GND"})
        instances.append(inst); connections.append(conn)
    
    # -- U23 SPI Flash W25Q128
    u23_pins = ["CS", "DO/IO1", "WP/IO2", "GND", "DI/IO0", "CLK", "HOLD/IO3", "VCC"]
    u23_left = [(str(i+1), u23_pins[i]) for i in range(4)]
    u23_right = [(str(i+5), u23_pins[i+4]) for i in range(4)]
    u23_lib, u23_geom = make_lib_sym_ic("Memory_Flash:W25Q128JVS", "U", u23_left, u23_right, "128Mbit SPI Flash")
    lib_syms.append(u23_lib)
    u23_nets = {"1": "FLASH_CS", "2": "FLASH_MISO", "3": "+3V3", "4": "GND",
                "5": "FLASH_MOSI", "6": "FLASH_SCK", "7": "+3V3", "8": "+3V3"}
    inst, conn = place_instance("Memory_Flash:W25Q128JVS", "U23", "W25Q128JVS", 300, 60,
                                 u23_geom, u23_nets, "Package_SON:WSON-8_2x3mm", "W25Q128JVSIQ")
    instances.append(inst); connections.append(conn)
    
    # -- J5 JTAG 2x5 connector
    jtag_pins = ["TCK", "GND", "TDO", "VCC", "TMS", "GND", "NC", "NC", "TDI", "TRST"]
    j5_lib, j5_geom = make_lib_sym_connector("Connector:JTAG_2x5", "J", jtag_pins, "ARM JTAG 10-pin")
    lib_syms.append(j5_lib)
    j5_nets = {"1": "JTAG_TCK", "2": "GND", "3": "JTAG_TDO", "4": "+3V3",
               "5": "JTAG_TMS", "6": "GND", "9": "JTAG_TDI", "10": "JTAG_TRST"}
    inst, conn = place_instance("Connector:JTAG_2x5", "J5", "JTAG", 300, 100,
                                 j5_geom, j5_nets, "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical")
    instances.append(inst); connections.append(conn)
    
    # Cross-sheet nets connect via global labels on the wired pins (see place_instance)
    hlabels = []
    
    text = text_note("NCE + FPGA Compute Block\\nNCE: SMIC 28nm QFN-64, AXI4-Lite Master\\nFPGA: Artix-7 100T, Config via SPI Flash", 30, 155, 1.5)
    
    return _wrap_subsheet("NCE + FPGA - LightRail Eval Board",
                          "f0000002-0002-4000-8000-000000000002",
                          lib_syms, instances, connections, hlabels, text)


# ============================================================================
# TFLN OPTICAL SUB-SHEET
# ============================================================================

def generate_tfln_optical():
    """TFLN Photonic IC + ADC monitor + DAC bias + Temp sensor + fiber/RF connectors."""
    lib_syms = []
    instances = []
    connections = []
    
    for rail in ["+3V3", "+1V8", "GND"]:
        lib_syms.append(make_lib_sym_power(rail))
    
    c_lib, c_geom = make_lib_sym_passive("Device:C", "C", "Capacitor")
    lib_syms.append(c_lib)
    r_lib, r_geom = make_lib_sym_passive("Device:R", "R", "Resistor")
    lib_syms.append(r_lib)
    
    # -- U3 TFLN PIC Module (custom footprint)
    u3_left = [
        ("1", "VDD"), ("2", "GND"), ("3", "GND"),
        ("4", "RF_IN_P0"), ("5", "RF_IN_N0"), ("6", "RF_IN_P1"), ("7", "RF_IN_N1"),
        ("8", "RF_IN_P2"), ("9", "RF_IN_N2"), ("10", "RF_IN_P3"), ("11", "RF_IN_N3"),
        ("12", "BIAS_V1"), ("13", "BIAS_V2"), ("14", "BIAS_V3"), ("15", "BIAS_V4"),
        ("16", "TEMP_D"),
    ]
    u3_right = [
        ("17", "OPT_TX0"), ("18", "OPT_TX1"), ("19", "OPT_TX2"), ("20", "OPT_TX3"),
        ("21", "OPT_RX0"), ("22", "OPT_RX1"), ("23", "OPT_RX2"), ("24", "OPT_RX3"),
        ("25", "MON_PD0"), ("26", "MON_PD1"), ("27", "MON_PD2"), ("28", "MON_PD3"),
        ("29", "MON_PD4"), ("30", "MON_PD5"), ("31", "MON_PD6"), ("32", "MON_PD7"),
    ]
    u3_lib, u3_geom = make_lib_sym_ic("LightRail:TFLN_PIC", "U", u3_left, u3_right, "TFLN Photonic Integrated Circuit")
    lib_syms.append(u3_lib)
    u3_nets = {
        "1": "+1V8", "2": "GND", "3": "GND",
        "4": "TFLN_TX_P0", "5": "TFLN_TX_N0", "6": "TFLN_TX_P1", "7": "TFLN_TX_N1",
        "8": "TFLN_TX_P2", "9": "TFLN_TX_N2", "10": "TFLN_TX_P3", "11": "TFLN_TX_N3",
        "12": "DAC_V1", "13": "DAC_V2", "14": "DAC_V3", "15": "DAC_V4",
        "16": "TEMP_DIODE",
        "17": "OPT_TX0", "18": "OPT_TX1", "19": "OPT_TX2", "20": "OPT_TX3",
        "21": "OPT_RX0", "22": "OPT_RX1", "23": "OPT_RX2", "24": "OPT_RX3",
        "25": "MON_CH0", "26": "MON_CH1", "27": "MON_CH2", "28": "MON_CH3",
        "29": "MON_CH4", "30": "MON_CH5", "31": "MON_CH6", "32": "MON_CH7",
    }
    inst, conn = place_instance("LightRail:TFLN_PIC", "U3", "TFLN_PIC", 100, 70,
                                 u3_geom, u3_nets, "LightRail:TFLN_PIC_Module", "LR-TFLN-PIC-001")
    instances.append(inst); connections.append(conn)
    
    # -- U21 AD7928 8-ch ADC (monitors photodiode currents)
    u21_left = [
        ("1", "VDD"), ("2", "VREF"), ("3", "GND"), ("4", "AGND"),
        ("5", "CH0"), ("6", "CH1"), ("7", "CH2"), ("8", "CH3"),
        ("9", "CH4"), ("10", "CH5"),
    ]
    u21_right = [
        ("11", "CH6"), ("12", "CH7"),
        ("13", "SCLK"), ("14", "DIN"), ("15", "DOUT"), ("16", "CS"),
        ("17", "VDD2"), ("18", "GND2"), ("19", "NC"), ("20", "NC2"),
    ]
    u21_lib, u21_geom = make_lib_sym_ic("Analog_ADC:AD7928", "U", u21_left, u21_right, "8-ch 12-bit 1MSPS ADC")
    lib_syms.append(u21_lib)
    u21_nets = {
        "1": "+3V3", "2": "+3V3", "3": "GND", "4": "GND",
        "5": "MON_CH0", "6": "MON_CH1", "7": "MON_CH2", "8": "MON_CH3",
        "9": "MON_CH4", "10": "MON_CH5", "11": "MON_CH6", "12": "MON_CH7",
        "13": "SPI_CLK", "14": "SPI_MOSI", "15": "SPI_MISO", "16": "SPI_CS_ADC",
        "17": "+3V3", "18": "GND",
    }
    inst, conn = place_instance("Analog_ADC:AD7928", "U21", "AD7928", 250, 50,
                                 u21_geom, u21_nets, "Package_SO:TSSOP-20", "AD7928BRUZ")
    instances.append(inst); connections.append(conn)
    
    # -- U24 AD5684R Quad DAC (bias voltages for TFLN modulators)
    u24_left = [("1", "VDD"), ("2", "VREF"), ("3", "GND"), ("4", "GND2"),
                ("5", "OUTA"), ("6", "OUTB"), ("7", "OUTC"), ("8", "OUTD")]
    u24_right = [("9", "SCLK"), ("10", "SYNC"), ("11", "DIN"), ("12", "LDAC"),
                 ("13", "CLR"), ("14", "RSTSEL"), ("15", "NC"), ("16", "NC2")]
    u24_lib, u24_geom = make_lib_sym_ic("Analog_DAC:AD5684R", "U", u24_left, u24_right, "Quad 12-bit DAC")
    lib_syms.append(u24_lib)
    u24_nets = {
        "1": "+3V3", "2": "+3V3", "3": "GND", "4": "GND",
        "5": "DAC_V1", "6": "DAC_V2", "7": "DAC_V3", "8": "DAC_V4",
        "9": "SPI_CLK", "10": "SPI_CS_DAC", "11": "SPI_MOSI", "12": "GND",
        "13": "+3V3", "14": "+3V3",
    }
    inst, conn = place_instance("Analog_DAC:AD5684R", "U24", "AD5684R", 250, 110,
                                 u24_geom, u24_nets, "Package_SO:TSSOP-16", "AD5684RBRUZ")
    instances.append(inst); connections.append(conn)
    
    # -- U25 TMP461 Temperature Sensor (I2C)
    u25_left = [("1", "VDD"), ("2", "GND"), ("3", "SDA"), ("4", "SCL")]
    u25_right = [("5", "ALERT"), ("6", "ADDR"), ("7", "DXP"), ("8", "DXN")]
    u25_lib, u25_geom = make_lib_sym_ic("Sensor_Temperature:TMP461", "U", u25_left, u25_right, "I2C Temp Sensor")
    lib_syms.append(u25_lib)
    u25_nets = {
        "1": "+3V3", "2": "GND", "3": "I2C_SDA", "4": "I2C_SCL",
        "5": "TEMP_ALERT", "6": "GND", "7": "TEMP_DIODE", "8": "GND",
    }
    inst, conn = place_instance("Sensor_Temperature:TMP461", "U25", "TMP461", 250, 155,
                                 u25_geom, u25_nets, "Package_SON:WSON-8_2x2mm", "TMP461AIDR")
    instances.append(inst); connections.append(conn)
    
    # -- J11 MPO-24 Fiber Connector
    j11_pins = [f"FIBER_{i}" for i in range(1, 25)]
    j11_lib, j11_geom = make_lib_sym_connector("Connector_Fiber:MPO_24", "J", j11_pins, "MPO-24 Fiber Array")
    lib_syms.append(j11_lib)
    j11_nets = {}
    for i in range(8):
        j11_nets[str(i+1)] = f"OPT_TX{i}" if i < 4 else f"OPT_RX{i-4}"
    inst, conn = place_instance("Connector_Fiber:MPO_24", "J11", "MPO-24", 40, 170,
                                 j11_geom, j11_nets, "Connector:MPO_24_SMT")
    instances.append(inst); connections.append(conn)
    
    # -- J7-J10 SMA RF probe connectors (AC coupled to TFLN TX)
    sma_pins = ["SIG", "GND"]
    sma_lib, sma_geom = make_lib_sym_passive("Connector:SMA", "J", "SMA Edge RF")
    lib_syms.append(sma_lib)
    for i, (ref, net) in enumerate([("J7", "TFLN_TX_P0"), ("J8", "TFLN_TX_N0"),
                                     ("J9", "TFLN_TX_P1"), ("J10", "TFLN_TX_N1")]):
        # AC coupling cap (top, TFLN signal in) feeding SMA below it (GND at bottom)
        cref = f"C10_{chr(97+i)}"
        inst, conn = place_instance("Device:C", cref, "100nF", 40+i*15, 22, c_geom,
                                     {"1": net, "2": f"SMA_{ref}"})
        instances.append(inst); connections.append(conn)
        inst, conn = place_instance("Connector:SMA", ref, "SMA", 40+i*15, 42, sma_geom,
                                     {"1": f"SMA_{ref}", "2": "GND"}, "Connector_Coaxial:SMA_Edge")
        instances.append(inst); connections.append(conn)
    
    # Decoupling
    for i in range(4):
        inst, conn = place_instance("Device:C", f"C5_{chr(100+i)}", "100nF", 230+i*7, 175, c_geom,
                                     {"1": "+3V3", "2": "GND"})
        instances.append(inst); connections.append(conn)
    
    # Cross-sheet nets connect via global labels on the wired pins (see place_instance)
    hlabels = []
    
    text = text_note("TFLN Optical Engine Block\\n8-ch 200G PAM4 Optical TX/RX\\nAD7928 monitor + AD5684R bias + TMP461 thermal", 30, 195, 1.5)
    
    return _wrap_subsheet("TFLN Optical - LightRail Eval Board",
                          "f0000003-0003-4000-8000-000000000003",
                          lib_syms, instances, connections, hlabels, text)


# ============================================================================
# CLOCK + INTERFACE SUB-SHEET
# ============================================================================

def generate_clock_interface():
    """Si5395A PLL + FT232H USB-UART + TCXO + USB-C + GPIO + Reset."""
    lib_syms = []
    instances = []
    connections = []
    
    for rail in ["+3V3", "+1V8", "+5V", "GND", "+5V_USB"]:
        lib_syms.append(make_lib_sym_power(rail))
    
    c_lib, c_geom = make_lib_sym_passive("Device:C", "C", "Capacitor")
    lib_syms.append(c_lib)
    r_lib, r_geom = make_lib_sym_passive("Device:R", "R", "Resistor")
    lib_syms.append(r_lib)
    
    # -- Y1 100MHz TCXO
    y1_pins = ["VDD", "OE", "GND", "OUT"]
    y1_left = [("1", "VDD"), ("2", "OE")]
    y1_right = [("3", "GND"), ("4", "OUT")]
    y1_lib, y1_geom = make_lib_sym_ic("Device:Crystal_4Pin", "Y", y1_left, y1_right, "100MHz TCXO 2.5ppm")
    lib_syms.append(y1_lib)
    y1_nets = {"1": "+3V3", "2": "+3V3", "3": "GND", "4": "CLK_100M"}
    inst, conn = place_instance("Device:Crystal_4Pin", "Y1", "100MHz", 50, 50,
                                 y1_geom, y1_nets, "Crystal:Crystal_SMD_3215-4Pin", "SiT5356AI-33-25E-100.000000")
    instances.append(inst); connections.append(conn)
    
    # -- U20 Si5395A PLL Clock Generator (QFN-28)
    u20_left = [
        ("1", "VDD"), ("2", "VDDA"), ("3", "GND"), ("4", "GND2"),
        ("5", "IN0"), ("6", "IN0B"), ("7", "IN1"), ("8", "IN1B"),
        ("9", "SDA"), ("10", "SCL"), ("11", "RSTB"), ("12", "INTRB"),
        ("13", "OEB"), ("14", "LOLB"),
    ]
    u20_right = [
        ("15", "OUT0"), ("16", "OUT0B"), ("17", "OUT1"), ("18", "OUT1B"),
        ("19", "OUT2"), ("20", "OUT2B"), ("21", "OUT3"), ("22", "OUT3B"),
        ("23", "OUT4"), ("24", "OUT4B"),
        ("25", "VDDO0"), ("26", "VDDO1"), ("27", "VDDO2"), ("28", "GND3"),
    ]
    u20_lib, u20_geom = make_lib_sym_ic("Clock:Si5395A", "U", u20_left, u20_right, "Any-Rate PLL Jitter Attenuator")
    lib_syms.append(u20_lib)
    u20_nets = {
        "1": "+3V3", "2": "+1V8", "3": "GND", "4": "GND",
        "5": "CLK_100M", "6": "GND", "7": "GND", "8": "GND",
        "9": "I2C_SDA", "10": "I2C_SCL", "11": "RESET_N", "12": "PLL_LOL",
        "13": "+3V3", "14": "PLL_LOL",
        "15": "CLK_CORE", "16": "CLK_CORE_N", "17": "CLK_REF", "18": "CLK_REF_N",
        "19": "CLK_SERDES", "20": "CLK_SERDES_N", "21": "CLK_HBM", "22": "CLK_HBM_N",
        "23": "CLK_100M_BUF", "24": "CLK_100M_BUF_N",
        "25": "+1V8", "26": "+1V8", "27": "+1V8", "28": "GND",
    }
    inst, conn = place_instance("Clock:Si5395A", "U20", "Si5395A", 130, 55,
                                 u20_geom, u20_nets, "Package_DFN_QFN:QFN-28_5x5mm", "Si5395A-A-GM")
    instances.append(inst); connections.append(conn)
    
    # PLL decoupling
    for i in range(4):
        inst, conn = place_instance("Device:C", f"C50_{i}", "100nF", 105+i*5, 120, c_geom,
                                     {"1": "+1V8", "2": "GND"})
        instances.append(inst); connections.append(conn)
    
    # -- U22 FT232H USB to UART/FIFO (QFN-48, simplified)
    u22_left = [
        ("1", "VCC"), ("2", "VCCIO"), ("3", "GND"), ("4", "GND2"),
        ("5", "USBDP"), ("6", "USBDM"),
        ("7", "RESET"), ("8", "EECS"), ("9", "EECLK"), ("10", "EEDATA"),
        ("11", "OSCI"), ("12", "OSCO"),
    ]
    u22_right = [
        ("13", "TXD"), ("14", "RXD"), ("15", "RTS"), ("16", "CTS"),
        ("17", "DTR"), ("18", "DSR"), ("19", "DCD"), ("20", "RI"),
        ("21", "PWREN"), ("22", "TXLED"), ("23", "RXLED"), ("24", "SUSPEND"),
    ]
    u22_lib, u22_geom = make_lib_sym_ic("Interface_USB:FT232H", "U", u22_left, u22_right, "USB Hi-Speed UART/FIFO")
    lib_syms.append(u22_lib)
    u22_nets = {
        "1": "+3V3", "2": "+3V3", "3": "GND", "4": "GND",
        "5": "USB_DP", "6": "USB_DN",
        "7": "RESET_N", "11": "CLK_12M", "12": "CLK_12M_OUT",
        "13": "UART_TX", "14": "UART_RX", "15": "UART_RTS", "16": "UART_CTS",
        "21": "FT_PWREN", "22": "FT_TXLED", "23": "FT_RXLED",
    }
    inst, conn = place_instance("Interface_USB:FT232H", "U22", "FT232H", 250, 55,
                                 u22_geom, u22_nets, "Package_DFN_QFN:QFN-48_7x7mm", "FT232HQ")
    instances.append(inst); connections.append(conn)
    
    # -- J2 USB-C Connector
    usb_pins = ["VBUS", "CC1", "CC2", "DP", "DN", "SBU1", "SBU2", "GND", "SHIELD"]
    j2_lib, j2_geom = make_lib_sym_connector("Connector:USB_C_16Pin", "J", usb_pins, "USB Type-C Receptacle")
    lib_syms.append(j2_lib)
    j2_nets = {"1": "+5V_USB", "4": "USB_DP", "5": "USB_DN", "8": "GND", "9": "GND"}
    inst, conn = place_instance("Connector:USB_C_16Pin", "J2", "USB-C", 315, 50,
                                 j2_geom, j2_nets, "Connector_USB:USB_C_Receptacle_GCT_USB4110", "USB4110-GF-A")
    instances.append(inst); connections.append(conn)
    
    # ESD protection D5
    d5_lib, d5_geom = make_lib_sym_passive("Device:D_TVS", "D", "USB ESD Protection")
    lib_syms.append(d5_lib)
    inst, conn = place_instance("Device:D_TVS", "D5a", "PRTR5V0U2X", 305, 80, d5_geom,
                                 {"1": "USB_DP", "2": "GND"}, "Package_SOD:SOD-323", "PRTR5V0U2X")
    instances.append(inst); connections.append(conn)
    inst, conn = place_instance("Device:D_TVS", "D5b", "PRTR5V0U2X", 315, 80, d5_geom,
                                 {"1": "USB_DN", "2": "GND"}, "Package_SOD:SOD-323", "PRTR5V0U2X")
    instances.append(inst); connections.append(conn)
    
    # -- J6 GPIO Header 2x7
    gpio_pins = ["+3V3", "GND", "GPIO0", "GPIO1", "GPIO2", "GPIO3",
                 "GPIO4", "GPIO5", "GPIO6", "GPIO7", "GPIO8", "GPIO9", "I2C_SCL", "I2C_SDA"]
    j6_lib, j6_geom = make_lib_sym_connector("Connector:PinHeader_2x07", "J", gpio_pins, "GPIO Expansion")
    lib_syms.append(j6_lib)
    j6_nets = {"1": "+3V3", "2": "GND", "3": "FPGA_GPIO0", "4": "FPGA_GPIO1",
               "5": "FPGA_GPIO2", "6": "FPGA_GPIO3", "13": "I2C_SCL", "14": "I2C_SDA"}
    inst, conn = place_instance("Connector:PinHeader_2x07", "J6", "GPIO", 315, 120,
                                 j6_geom, j6_nets, "Connector_PinHeader_1.27mm:PinHeader_2x07_P1.27mm_Vertical")
    instances.append(inst); connections.append(conn)
    
    # -- SW1 Reset switch + R1 pull-up + C debounce
    sw_lib, sw_geom = make_lib_sym_passive("Switch:SW_Push", "SW", "Tactile Reset")
    lib_syms.append(sw_lib)
    inst, conn = place_instance("Switch:SW_Push", "SW1", "RESET", 50, 130, sw_geom,
                                 {"1": "RESET_N", "2": "GND"}, "Button_Switch_SMD:Tactile_4.5x4.5mm", "B3F-1000")
    instances.append(inst); connections.append(conn)
    # Pull-up resistor
    inst, conn = place_instance("Device:R", "R1a", "10k", 60, 125, r_geom,
                                 {"1": "+3V3", "2": "RESET_N"}, "Resistor_SMD:R_0402", "RC0402FR-0710KL")
    instances.append(inst); connections.append(conn)
    # Debounce cap
    inst, conn = place_instance("Device:C", "C9a", "100nF", 70, 135, c_geom,
                                 {"1": "RESET_N", "2": "GND"}, "Capacitor_SMD:C_0402")
    instances.append(inst); connections.append(conn)
    
    # Activity LEDs
    d_lib, d_geom = make_lib_sym_passive("Device:LED", "D", "LED")
    lib_syms.append(d_lib)
    for i, (dref, dval, net) in enumerate([("D2", "Blue", "FT_TXLED"), ("D3", "Red", "FT_RXLED")]):
        inst, conn = place_instance("Device:R", f"R5_{chr(98+i)}", "330", 280+i*12, 125, r_geom,
                                     {"1": net, "2": f"LED_{dref}"}, "Resistor_SMD:R_0402")
        instances.append(inst); connections.append(conn)
        inst, conn = place_instance("Device:LED", dref, dval, 280+i*12, 138, d_geom,
                                     {"1": f"LED_{dref}", "2": "GND"}, "LED_SMD:LED_0603")
        instances.append(inst); connections.append(conn)
    
    # Cross-sheet nets connect via global labels on the wired pins (see place_instance)
    # +5V_USB is sourced locally from the USB-C VBUS, so flag it as driven for ERC.
    lib_syms.append(make_lib_sym_pwr_flag())
    hlabels = [place_pwr_flag("+5V_USB", 300, 30)]
    
    text = text_note("Clock Generation + Interface Block\\nSi5395A: 100MHz TCXO → CLK_CORE/REF/SERDES/HBM\\nFT232H: USB-C → UART\\nGPIO header + Reset circuit", 30, 160, 1.5)
    
    return _wrap_subsheet("Clock + Interface - LightRail Eval Board",
                          "f0000004-0004-4000-8000-000000000004",
                          lib_syms, instances, connections, hlabels, text)


# ============================================================================
# HELPER
# ============================================================================

def _wrap_subsheet(title, file_uuid, lib_syms, instances, connections, hlabels, text):
    """Wrap sub-sheet content into a complete .kicad_sch file."""
    return f"""(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{file_uuid}")
\t(paper "A3")
\t(title_block
\t\t(title "{title}")
\t\t(date "2026-05-26")
\t\t(rev "1.0")
\t\t(company "LightRail AI")
\t)
\t(lib_symbols
{chr(10).join(lib_syms)}
\t)
{chr(10).join(instances)}
{chr(10).join(connections)}
{chr(10).join(hlabels)}
{text}
)
"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    os.makedirs(SHEETS_DIR, exist_ok=True)
    
    print("Generating top-level schematic...")
    with open(os.path.join(KICAD_DIR, "LightRail_Eval_Board.kicad_sch"), 'w') as f:
        f.write(generate_top())
    
    print("Generating Power Supply sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "power.kicad_sch"), 'w') as f:
        f.write(generate_power())
    
    print("Generating NCE + FPGA sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "nce_fpga.kicad_sch"), 'w') as f:
        f.write(generate_nce_fpga())
    
    print("Generating TFLN Optical sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "tfln_optical.kicad_sch"), 'w') as f:
        f.write(generate_tfln_optical())
    
    print("Generating Clock + Interface sub-sheet...")
    with open(os.path.join(SHEETS_DIR, "clock_interface.kicad_sch"), 'w') as f:
        f.write(generate_clock_interface())
    
    # Dump the captured connectivity so the PCB builder can consume it.
    netlist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "netlist.json")
    with open(netlist_path, 'w') as f:
        json.dump(NETLIST, f, indent=1, sort_keys=True)
    n_nodes = sum(len(c["pins"]) for c in NETLIST.values())
    print(f"Wrote netlist.json: {len(NETLIST)} components, {n_nodes} pin-nodes.")
    print("Done! All 5 schematic files generated.")


if __name__ == "__main__":
    main()

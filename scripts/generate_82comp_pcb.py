#!/usr/bin/env python3
"""Generate KiCad PCB for the 82-component NCE Gen3 dual-accelerator board.

Reproduces the reference layout:
  - 420 x 350 mm board with PCIe card-edge notch
  - 32-layer HDI stackup (Megtron-7 outer, High-Tg-FR4 inner, Faradflex embedded cap)
  - Symmetric dual-NCE placement with HBM flanking arrays
  - TFLN photonic module centered between NCEs
  - DrMOS power stages on left/right edges
  - PCIe slots along bottom edge
  - Full power plane zones and routed interconnects
"""

import os
import uuid
import math

def uid():
    return str(uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════════
# NET DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════

def build_nets():
    """Build net list mapping net names to net IDs."""
    nets = {"": 0, "GND": 1, "+12V": 2, "+3V3": 3, "+1V8": 4, "+0V9": 5, "+0V8": 6}
    nid = 7
    # I2C/SPI
    for n in ["I2C_SDA", "I2C_SCL", "SPI_MOSI", "SPI_MISO", "SPI_SCK", "SPI_CS"]:
        nets[n] = nid; nid += 1
    # HBM channels per NCE
    for nce in range(2):
        pfx = f"NCE{nce}"
        for i in range(8):
            nets[f"{pfx}_HBM_CH{i}"] = nid; nid += 1
        nets[f"{pfx}_CATTRIP"] = nid; nid += 1
        nets[f"{pfx}_PWR_GOOD"] = nid; nid += 1
    # RF channels
    for i in range(4):
        for pol in ["P", "N"]:
            nets[f"RF_TX{i}_{pol}"] = nid; nid += 1
            nets[f"RF_DRV{i}_{pol}"] = nid; nid += 1
    # VRM PWM
    for vrm in range(4):
        for ph in range(6):
            nets[f"VRM{vrm}_PWM{ph}"] = nid; nid += 1
    # TFLN VBIAS
    for i in range(4):
        nets[f"TFLN_VBIAS_{i}"] = nid; nid += 1
    # Clocking
    for i in range(2):
        for ch in range(4):
            nets[f"CLK{i}_OUT{ch}_P"] = nid; nid += 1
            nets[f"CLK{i}_OUT{ch}_N"] = nid; nid += 1
    nets["TFLN_CLK_P"] = nid; nid += 1
    nets["TFLN_CLK_N"] = nid; nid += 1
    # PCIe switch lanes
    for sw in range(4):
        for ln in range(4):
            nets[f"PCIESW{sw}_UP{ln}"] = nid; nid += 1
        nets[f"PCIESW{sw}_DN0"] = nid; nid += 1
    # Retimer
    for i in range(4):
        nets[f"RET{i}_RX_P"] = nid; nid += 1
    # HBM ref clock
    for nce in range(2):
        for i in range(8):
            nets[f"NCE{nce}_REFCK{i}_P"] = nid; nid += 1
            nets[f"NCE{nce}_REFCK{i}_N"] = nid; nid += 1
    return nets


# ══════════════════════════════════════════════════════════════════════════
# STACKUP (32 copper layers, Megtron-7 / High-Tg-FR4 / Faradflex)
# ══════════════════════════════════════════════════════════════════════════

def stackup_block():
    lines = []
    lines.append('    (stackup')
    lines.append('      (layer "F.SilkS" (type "Top Silk Screen"))')
    lines.append('      (layer "F.Paste" (type "Top Solder Paste"))')
    lines.append('      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))')
    # Top copper - thick for power
    lines.append('      (layer "F.Cu" (type "copper") (thickness 0.0700))')

    # Layers 1-9: Megtron-7 signal layers (thin copper for impedance)
    for i in range(1, 10):
        mat = "Megtron-7"
        dtype = "prepreg" if (i % 2 == 1) else "core"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "{mat}") (epsilon_r 3.3) (loss_tangent 0.002))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0175))')

    # Layers 10-14: High-Tg-FR4 power/ground planes (thick copper)
    for i in range(10, 15):
        dtype = "core" if (i % 2 == 0) else "prepreg"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "High-Tg-FR4") (epsilon_r 4.2) (loss_tangent 0.015))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0700))')

    # Layer 15: Faradflex embedded capacitance
    lines.append('      (layer "dielectric 15" (type "core") (thickness 0.0240) (material "Faradflex-BC24") (epsilon_r 14.0) (loss_tangent 0.02))')
    lines.append('      (layer "In15.Cu" (type "copper") (thickness 0.0350))')
    lines.append('      (layer "dielectric 16" (type "core") (thickness 0.0240) (material "Faradflex-BC24") (epsilon_r 14.0) (loss_tangent 0.02))')
    lines.append('      (layer "In16.Cu" (type "copper") (thickness 0.0700))')

    # Layers 17-20: High-Tg-FR4 (mirror of 10-14)
    for i in range(17, 21):
        dtype = "prepreg" if (i % 2 == 1) else "core"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "High-Tg-FR4") (epsilon_r 4.2) (loss_tangent 0.015))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0700))')

    # Layers 21-30: Megtron-7 signal layers (mirror of 1-9)
    for i in range(21, 31):
        mat = "Megtron-7"
        dtype = "prepreg" if (i % 2 == 1) else "core"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "{mat}") (epsilon_r 3.3) (loss_tangent 0.002))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0175))')

    # Bottom
    lines.append('      (layer "dielectric 31" (type "prepreg") (thickness 0.0760) (material "Megtron-7") (epsilon_r 3.3) (loss_tangent 0.002))')
    lines.append('      (layer "B.Cu" (type "copper") (thickness 0.0700))')
    lines.append('      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))')
    lines.append('      (layer "B.Paste" (type "Bottom Solder Paste"))')
    lines.append('      (layer "B.SilkS" (type "Bottom Silk Screen"))')
    lines.append('      (copper_finish "ENIG")')
    lines.append('    )')
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# NET CLASSES
# ══════════════════════════════════════════════════════════════════════════

NET_CLASSES = [
    ("Default",            "Default net class",                   0.10, 0.15, 0.4, 0.2, None, None),
    ("SERDES_100G_PAM4",   "100G PAM4 SerDes diff pairs",         0.127, 0.09, 0.3, 0.15, 0.09, 0.09),
    ("PCIe_Gen5",          "PCIe Gen 5.0 32GT/s diff pairs",      0.127, 0.12, 0.3, 0.15, 0.18, 0.12),
    ("TFLN_RF",            "TFLN RF modulator drive",              0.15, 0.15, 0.3, 0.15, 0.20, 0.15),
    ("RF_50OHM_DIFF",      "50-ohm RF differential",              0.15, 0.10, 0.3, 0.15, 0.10, 0.10),
    ("HBM4_Interposer",   "HBM4 side-channel diff",              0.127, 0.10, 0.3, 0.15, 0.15, 0.10),
    ("PDN_BYPASS",         "PDN bypass decoupling network",        0.10, 0.30, 0.6, 0.3, None, None),
    ("PWR_CORE",           "V_CORE 0.8V high-current power",      0.20, 2.00, 1.2, 0.6, None, None),
    ("PWR_12V",            "12V power distribution",               0.20, 1.00, 0.8, 0.4, None, None),
    ("PWR_3V3",            "3.3V power distribution",              0.15, 0.50, 0.6, 0.3, None, None),
    ("PWR_1V8",            "1.8V power distribution",              0.15, 0.30, 0.5, 0.25, None, None),
    ("I2C_SPI",            "Low-speed control buses",              0.15, 0.15, 0.4, 0.2, None, None),
]


def net_classes_block():
    lines = []
    for name, desc, clr, tw, vd, vdr, dpg, dpw in NET_CLASSES:
        lines.append(f'  (net_class "{name}" "{desc}"')
        lines.append(f'    (clearance {clr}) (trace_width {tw}) (via_dia {vd}) (via_drill {vdr}) (uvia_dia 0.3) (uvia_drill 0.1)')
        if dpg is not None:
            lines.append(f'    (diff_pair_gap {dpg}) (diff_pair_width {dpw})')
        lines.append('  )')
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# FOOTPRINT GENERATORS
# ══════════════════════════════════════════════════════════════════════════

def fp_bga(ref, value, x, y, fp_name, pad_pitch, rows, cols, pad_size, ep_size=None, angle=0):
    """Generate a BGA footprint placement with perimeter-only pads for readability."""
    lines = []
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y} {angle})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 {-(rows*pad_pitch/2 + 3)}) (layer "F.SilkS") (effects (font (size 1.5 1.5) (thickness 0.15))))')
    lines.append(f'    (fp_text value "{value}" (at 0 {rows*pad_pitch/2 + 3}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    # BGA pads - perimeter rings only (4 rows deep) to keep file manageable
    depth = min(4, rows // 2)
    placed = set()
    for r in range(rows):
        for c in range(cols):
            if not (r < depth or r >= rows - depth or c < depth or c >= cols - depth):
                continue
            px = (c - (cols-1)/2) * pad_pitch
            py = (r - (rows-1)/2) * pad_pitch
            row_letter = chr(65 + r) if r < 26 else chr(65 + r // 26 - 1) + chr(65 + r % 26)
            pname = f"{row_letter}{c+1}"
            lines.append(f'    (pad "{pname}" smd circle (at {px:.4f} {py:.4f}) (size {pad_size} {pad_size}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    if ep_size:
        lines.append(f'    (pad "EP" smd rect (at 0 0) (size {ep_size} {ep_size}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    # Courtyard
    hw = rows * pad_pitch / 2 + 1
    lines.append(f'    (fp_rect (start {-hw} {-hw}) (end {hw} {hw}) (layer "F.CrtYd") (width 0.05))')
    lines.append('  )')
    return "\n".join(lines)


def fp_qfn(ref, value, x, y, fp_name, pin_count, body_size, pad_pitch, pad_w, pad_h, ep_size=None, angle=0):
    """Generate a QFN footprint placement."""
    lines = []
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y} {angle})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 {-(body_size/2 + 2)}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'    (fp_text value "{value}" (at 0 {body_size/2 + 2}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    ppside = pin_count // 4
    half = body_size / 2 + pad_h / 2  # pads centered on body edge
    for i in range(ppside):
        offset = (i - (ppside-1)/2) * pad_pitch
        # Left side
        lines.append(f'    (pad "{i+1}" smd rect (at {-half:.4f} {offset:.4f}) (size {pad_h} {pad_w}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        # Bottom
        lines.append(f'    (pad "{ppside+i+1}" smd rect (at {offset:.4f} {half:.4f}) (size {pad_w} {pad_h}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        # Right
        lines.append(f'    (pad "{2*ppside+i+1}" smd rect (at {half:.4f} {-offset:.4f}) (size {pad_h} {pad_w}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        # Top
        lines.append(f'    (pad "{3*ppside+i+1}" smd rect (at {-offset:.4f} {-half:.4f}) (size {pad_w} {pad_h}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    if ep_size:
        lines.append(f'    (pad "{pin_count+1}" smd rect (at 0 0) (size {ep_size} {ep_size}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    # Courtyard
    crt = half + pad_h / 2 + 0.5
    lines.append(f'    (fp_rect (start {-crt:.4f} {-crt:.4f}) (end {crt:.4f} {crt:.4f}) (layer "F.CrtYd") (width 0.05))')
    lines.append('  )')
    return "\n".join(lines)


def fp_sot23(ref, value, x, y, angle=0):
    """SOT-23-5 for ADP7118 LDO."""
    lines = []
    fp_name = "Package_TO_SOT_SMD:SOT-23-5"
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y} {angle})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'    (fp_text value "{value}" (at 0 2.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    # SOT-23-5 pads
    for i, (px, py) in enumerate([(-1.1, -0.95), (-1.1, 0), (-1.1, 0.95), (1.1, 0.95), (1.1, -0.95)]):
        lines.append(f'    (pad "{i+1}" smd rect (at {px} {py}) (size 1.0 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    lines.append('  )')
    return "\n".join(lines)


def fp_cap_0402(ref, value, x, y, angle=0, net1_id=0, net1_name="", net2_id=0, net2_name=""):
    """0402 capacitor footprint with optional net assignments."""
    lines = []
    lines.append(f'  (footprint "Capacitor_SMD:C_0402_1005Metric" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y} {angle})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -1.2) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.1))))')
    lines.append(f'    (fp_text value "{value}" (at 0 1.2) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.1))))')
    lines.append(f'    (pad "1" smd roundrect (at -0.48 0) (size 0.56 0.62) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {net1_id} "{net1_name}"))')
    lines.append(f'    (pad "2" smd roundrect (at 0.48 0) (size 0.56 0.62) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (net {net2_id} "{net2_name}"))')
    lines.append('  )')
    return "\n".join(lines)


def fp_pcie_x16(ref, x, y):
    """PCIe x16 card edge connector."""
    lines = []
    fp_name = "LightRail:PCIE_x16_SLOT"
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -5) (layer "F.SilkS") (effects (font (size 1.5 1.5) (thickness 0.15))))')
    lines.append(f'    (fp_text value "PCIe_x16_SLOT" (at 0 5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    # 164-pin edge connector: 82 pins per side, 1.0mm pitch
    for i in range(82):
        px = (i - 40.5) * 1.0
        lines.append(f'    (pad "A{i+1}" smd rect (at {px} -1.5) (size 0.6 2.0) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        lines.append(f'    (pad "B{i+1}" smd rect (at {px} 1.5) (size 0.6 2.0) (layers "B.Cu" "B.Paste" "B.Mask") (net 0 ""))')
    lines.append('  )')
    return "\n".join(lines)


def fp_mounting_hole(ref, x, y):
    lines = []
    lines.append(f'  (footprint "MountingHole:MountingHole_3.2mm_M3" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -3) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'    (fp_text value "MountingHole" (at 0 3) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    lines.append(f'    (pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers *.Cu *.Mask))')
    lines.append('  )')
    return "\n".join(lines)


def fp_fiducial(ref, x, y):
    lines = []
    lines.append(f'  (footprint "Fiducial:Fiducial_1mm_Mask2.5mm" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -2) (layer "F.SilkS") (effects (font (size 0.5 0.5) (thickness 0.1))))')
    lines.append(f'    (fp_text value "Fiducial" (at 0 2) (layer "F.Fab") (effects (font (size 0.5 0.5) (thickness 0.1))))')
    lines.append(f'    (pad "1" smd circle (at 0 0) (size 1 1) (layers "F.Cu" "F.Mask") (net 0 ""))')
    lines.append('  )')
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# ROUTING HELPERS
# ══════════════════════════════════════════════════════════════════════════

def segment(x1, y1, x2, y2, width, layer, net_id):
    return f'  (segment (start {x1} {y1}) (end {x2} {y2}) (width {width}) (layer "{layer}") (net {net_id}) (tstamp "{uid()}"))'


def via(x, y, size, drill, net_id, layers=("F.Cu", "B.Cu")):
    # Ensure minimum via/drill sizes for board-level constraints
    size = max(size, 0.5)
    drill = max(drill, 0.3)
    return f'  (via (at {x} {y}) (size {size}) (drill {drill}) (layers "{layers[0]}" "{layers[1]}") (net {net_id}) (tstamp "{uid()}"))'


def diff_pair_route(x1, y1, x2, y2, width, gap, layer, net_p, net_n, vertical=False):
    """Route a differential pair between two points."""
    lines = []
    half = gap / 2 + width / 2
    if vertical:
        lines.append(segment(x1 - half, y1, x2 - half, y2, width, layer, net_p))
        lines.append(segment(x1 + half, y1, x2 + half, y2, width, layer, net_n))
    else:
        lines.append(segment(x1, y1 - half, x2, y2 - half, width, layer, net_p))
        lines.append(segment(x1, y1 + half, x2, y2 + half, width, layer, net_n))
    return "\n".join(lines)


def zone_pour(net_name, net_id, layer, points, priority=0):
    """Create a filled zone (copper pour)."""
    lines = []
    lines.append(f'  (zone (net {net_id}) (net_name "{net_name}") (layer "{layer}") (tstamp "{uid()}") (hatch edge 0.508)')
    lines.append(f'    (priority {priority})')
    lines.append('    (connect_pads (clearance 0.2))')
    lines.append('    (min_thickness 0.1)')
    lines.append('    (fill yes (thermal_gap 0.3) (thermal_bridge_width 0.3))')
    lines.append('    (polygon (pts')
    for px, py in points:
        lines.append(f'      (xy {px} {py})')
    lines.append('    ))')
    lines.append('  )')
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════
# MAIN GENERATION
# ══════════════════════════════════════════════════════════════════════════

def generate():
    nets = build_nets()
    L = []

    # ── Header ──
    L.append('(kicad_pcb (version 20240108) (generator "generate_82comp_pcb.py")')
    L.append('  (general (thickness 3.48) (legacy_teardrops no))')
    L.append('  (paper "A1")')

    # ── Layers ──
    L.append('  (layers')
    L.append('    (0 "F.Cu" signal)')
    for i in range(1, 31):
        L.append(f'    ({i} "In{i}.Cu" signal)')
    L.append('    (31 "B.Cu" signal)')
    for lid, name in [(32, "B.Adhes"), (33, "F.Adhes"), (34, "B.Paste"), (35, "F.Paste"),
                       (36, "B.SilkS"), (37, "F.SilkS"), (38, "B.Mask"), (39, "F.Mask"),
                       (40, "Dwgs.User"), (41, "Cmts.User"), (42, "Eco1.User"), (43, "Eco2.User"),
                       (44, "Edge.Cuts"), (45, "Margin"), (46, "B.CrtYd"), (47, "F.CrtYd"),
                       (48, "B.Fab"), (49, "F.Fab")]:
        L.append(f'    ({lid} "{name}" user)')
    L.append('  )')

    # ── Setup ──
    L.append('  (setup')
    L.append(stackup_block())
    L.append('    (pad_to_mask_clearance 0.051)')
    L.append('    (allow_soldermask_bridges_in_footprints yes)')
    L.append('    (pcb_text_width 0.3)')
    L.append('    (aux_axis_origin 0 0)')
    L.append('    (grid_origin 0 0)')
    L.append('    (pcbplotparams (layerselection 0x00010fc_ffffffff) (plot_on_all_layers_selection 0x0000000_00000000))')
    L.append('  )')

    # ── Net classes ──
    L.append(net_classes_block())

    # ── Nets ──
    for name, nid in sorted(nets.items(), key=lambda x: x[1]):
        L.append(f'  (net {nid} "{name}")')

    # ══════════════════════════════════════════════════════════════════════
    # BOARD OUTLINE - 420 x 350mm with PCIe card-edge notch
    # ══════════════════════════════════════════════════════════════════════
    board_edges = [
        (0, 0, 420, 0),
        (420, 0, 420, 350),
        (420, 350, 293, 350),
        (293, 350, 293, 355),
        (293, 355, 127, 355),
        (127, 355, 127, 350),
        (127, 350, 0, 350),
        (0, 350, 0, 0),
    ]
    for x1, y1, x2, y2 in board_edges:
        L.append(f'  (gr_line (start {x1} {y1}) (end {x2} {y2}) (layer "Edge.Cuts") (width 0.05) (tstamp "{uid()}"))')

    # ══════════════════════════════════════════════════════════════════════
    # COMPONENT PLACEMENT (matching reference image layout)
    # ══════════════════════════════════════════════════════════════════════

    # Board center = 210, vertical center ~ 160
    # NCE0 (left) center, NCE1 (right) center
    NCE0_X, NCE0_Y = 145, 160
    NCE1_X, NCE1_Y = 275, 160

    # ── NCE Gen3 SoCs (BGA-2500, 40x40mm, 0.8mm pitch → 50x50 grid) ──
    L.append(fp_bga("U1", "NCE_Gen3", NCE0_X, NCE0_Y,
                     "LightRail:NCE_BGA2500_40x40mm", 0.8, 50, 50, 0.4))
    L.append(fp_bga("U4", "NCE_Gen3", NCE1_X, NCE1_Y,
                     "LightRail:NCE_BGA2500_40x40mm", 0.8, 50, 50, 0.4))

    # ── TFLN Photonic Module (centered between NCEs) ──
    TFLN_X = (NCE0_X + NCE1_X) / 2  # 210
    TFLN_Y = NCE0_Y  # 160
    L.append(fp_qfn("U3", "TFLN_PIC_4xMZM", TFLN_X, TFLN_Y,
                     "LightRail:Custom_Optical_Module_25x8mm", 32, 8, 0.5, 0.25, 1.0))

    # ── HBM4 stacks: 8 per NCE, flanking top and bottom ──
    # NCE0 HBMs (U30-U37): 4 above, 4 below
    # HBM4 on interposer uses microbumps; PCB representation uses reduced-pin land pattern
    for i in range(8):
        col = i % 4
        row = i // 4  # 0=top row, 1=bottom row
        hx = NCE0_X - 30 + col * 20  # 20mm spacing for 12mm body + clearance
        hy = NCE0_Y - 42 + row * 84  # above/below NCE
        L.append(fp_bga(f"U{30+i}", "HBM4-16GB", hx, hy,
                        "LightRail:BGA-1024_12x9mm", 0.65, 16, 16, 0.35))

    # NCE1 HBMs (U38-U45): 4 above, 4 below
    for i in range(8):
        col = i % 4
        row = i // 4
        hx = NCE1_X - 30 + col * 20
        hy = NCE1_Y - 42 + row * 84
        L.append(fp_bga(f"U{38+i}", "HBM4-16GB", hx, hy,
                        "LightRail:BGA-1024_12x9mm", 0.65, 16, 16, 0.35))

    # ── HMC8410 RF Drivers (QFN-32, 5x5mm) - near TFLN ──
    for i in range(4):
        rx = TFLN_X - 20 + i * 13
        ry = TFLN_Y - 15  # above TFLN
        L.append(fp_qfn(f"U{50+i}", "HMC8410", rx, ry,
                        "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm",
                        32, 5, 0.5, 0.25, 0.8, 3.1))

    # ── VRM Controllers (QFN-48, 7x7mm) - left/right edges ──
    vrm_positions = [
        (30, 100),   # VRM0 - left upper
        (30, 220),   # VRM1 - left lower
        (390, 100),  # VRM2 - right upper
        (390, 220),  # VRM3 - right lower
    ]
    for i, (vx, vy) in enumerate(vrm_positions):
        L.append(fp_qfn(f"U{200+i}", "ISL69260", vx, vy,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # ── DrMOS stages (PQFN-40, 5x6mm) - 24 total, flanking left & right ──
    # 12 per side, in 2 columns of 6
    for i in range(24):
        side = 0 if i < 12 else 1  # left or right
        local_idx = i % 12
        col = local_idx // 6
        row = local_idx % 6
        if side == 0:
            dx = 55 + col * 10
            dy = 80 + row * 28
        else:
            dx = 355 + col * 10
            dy = 80 + row * 28
        L.append(fp_qfn(f"U{210+i}", "ISL99390", dx, dy,
                        "LightRail:PQFN-40_5x6mm", 40, 6, 0.4, 0.2, 0.7, 3.5))

    # ── LDO regulators (SOT-23-5) - near TFLN ──
    for i in range(4):
        lx = TFLN_X - 15 + i * 10
        ly = TFLN_Y + 15
        L.append(fp_sot23(f"U{240+i}", "ADP7118-0.9V", lx, ly))

    # ── Jitter Cleaners Si5395A (QFN-48) - top center ──
    for i in range(2):
        jx = 170 + i * 80
        jy = 30
        L.append(fp_qfn(f"U{250+i}", "Si5395A", jx, jy,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # ── Retimers BCM84881 (QFN-48) - bottom area ──
    for i in range(4):
        rtx = 130 + i * 50
        rty = 290
        L.append(fp_qfn(f"U{260+i}", "BCM84881", rtx, rty,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # ── PCIe Switches PEX88096 (QFN-48) - bottom area ──
    for i in range(4):
        psx = 130 + i * 50
        psy = 310
        L.append(fp_qfn(f"U{270+i}", "PEX88096", psx, psy,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # ── BMC AST2600 (QFN-48) - bottom left ──
    L.append(fp_qfn("U380", "AST2600", 50, 45,
                     "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                     48, 7, 0.5, 0.25, 0.8, 5.6))

    # ── PCIe x16 Slots - bottom edge (105mm spacing for 82mm slot width) ──
    for i in range(4):
        sx = 60 + i * 105  # 60, 165, 270, 375
        sy = 343
        L.append(fp_pcie_x16(f"J{20+i}", sx, sy))

    # ── Decoupling Capacitors (0402) - between NCEs (clear of HBM routing) ──
    rails = ["+0V8"]*4 + ["+1V8"]*4 + ["+3V3"]*4 + ["+0V9"]*4
    # Place in the gap between NCE0 and NCE1 (x: 167-253, centered at 210)
    for i in range(16):
        col = i % 4
        row = i // 4
        cx = 185 + col * 5.0  # between NCEs (NCE0 at 145, NCE1 at 275)
        cy = NCE0_Y - 20 + row * 4.0  # rows from 140 to 152
        rail_name = rails[i]
        L.append(fp_cap_0402(f"C{i+1}", "100nF", cx, cy,
                             net1_id=nets[rail_name], net1_name=rail_name,
                             net2_id=nets["GND"], net2_name="GND"))

    # ── Mounting Holes ── (away from components and slot areas)
    mh_positions = [(8, 8), (412, 8), (8, 320), (412, 320),
                    (100, 60), (320, 60), (100, 265), (320, 265)]
    for i, (mx, my) in enumerate(mh_positions):
        L.append(fp_mounting_hole(f"MH{i+1}", mx, my))

    # ── Fiducials ──
    for i, (fx, fy) in enumerate([(15, 15), (405, 15), (15, 335), (405, 335)]):
        L.append(fp_fiducial(f"FID{i+1}", fx, fy))

    # ══════════════════════════════════════════════════════════════════════
    # ZONE POURS - Power distribution planes
    # ══════════════════════════════════════════════════════════════════════

    board_pts = [(0, 0), (420, 0), (420, 350), (0, 350)]
    inner_pts = [(0, 0), (420, 0), (420, 330), (0, 330)]  # avoid PCIe slot area
    # Full-board ground planes on multiple inner layers
    for gnd_layer in ["In3.Cu", "In6.Cu", "In9.Cu",
                      "In12.Cu", "In14.Cu", "In16.Cu", "In18.Cu",
                      "In21.Cu", "In24.Cu", "In27.Cu", "In30.Cu", "B.Cu"]:
        L.append(zone_pour("GND", nets["GND"], gnd_layer, inner_pts, priority=0))

    # V_CORE (0.8V) planes - power layers near center
    vcore_pts = [(40, 70), (380, 70), (380, 270), (40, 270)]
    for pwr_layer in ["In10.Cu", "In11.Cu", "In19.Cu", "In20.Cu"]:
        L.append(zone_pour("+0V8", nets["+0V8"], pwr_layer, vcore_pts, priority=1))

    # +12V plane
    v12_pts = [(0, 0), (420, 0), (420, 60), (0, 60)]
    L.append(zone_pour("+12V", nets["+12V"], "In13.Cu", v12_pts, priority=1))

    # +3V3 plane
    v33_pts = [(0, 0), (80, 0), (80, 350), (0, 350)]
    L.append(zone_pour("+3V3", nets["+3V3"], "In15.Cu", v33_pts, priority=1))

    # +1V8 plane
    v18_pts = [(340, 0), (420, 0), (420, 350), (340, 350)]
    L.append(zone_pour("+1V8", nets["+1V8"], "In15.Cu", v18_pts, priority=1))

    # Front copper ground pour - avoid BGA and slot areas
    # Left section (below NCE0 BGA)
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(0, 0), (NCE0_X - 22, 0), (NCE0_X - 22, 330), (0, 330)], priority=0))
    # Right section (above NCE1 BGA)
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(NCE1_X + 22, 0), (420, 0), (420, 330), (NCE1_X + 22, 330)], priority=0))
    # Top strip (above both NCEs)
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(NCE0_X - 22, 0), (NCE1_X + 22, 0), (NCE1_X + 22, NCE0_Y - 22),
         (NCE0_X - 22, NCE0_Y - 22)], priority=0))
    # Bottom strip (below both NCEs)
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(NCE0_X - 22, NCE0_Y + 22), (NCE1_X + 22, NCE0_Y + 22),
         (NCE1_X + 22, 330), (NCE0_X - 22, 330)], priority=0))

    # ══════════════════════════════════════════════════════════════════════
    # SIGNAL ROUTING
    # ══════════════════════════════════════════════════════════════════════

    # ── HBM data channels: NCE → HBM (short, high-speed on Megtron-7 layers) ──
    # NCE BGA extends ±20mm from center; vias must be outside pad field
    nce_bga_half = 21  # 50*0.8/2 = 20mm, add 1mm margin
    # NCE0 HBM channels on In1.Cu / In2.Cu
    for i in range(8):
        col = i % 4
        row = i // 4
        hbm_x = NCE0_X - 30 + col * 20
        hbm_y = NCE0_Y - 42 + row * 84
        net_id = nets.get(f"NCE0_HBM_CH{i}", 0)
        layer = "In1.Cu" if i < 4 else "In2.Cu"
        via_x = NCE0_X - 18 + i * 4
        via_y = NCE0_Y - nce_bga_half - 1  # outside BGA field
        L.append(segment(via_x, via_y, via_x, via_y - 10, 0.10, layer, net_id))
        L.append(segment(via_x, via_y - 10, hbm_x, hbm_y + 6, 0.10, layer, net_id))
        L.append(via(via_x, via_y, 0.5, 0.3, net_id, ("F.Cu", layer)))

    # NCE1 HBM channels on In22.Cu / In23.Cu
    for i in range(8):
        col = i % 4
        row = i // 4
        hbm_x = NCE1_X - 30 + col * 20
        hbm_y = NCE1_Y - 42 + row * 84
        net_id = nets.get(f"NCE1_HBM_CH{i}", 0)
        layer = "In22.Cu" if i < 4 else "In23.Cu"
        via_x = NCE1_X - 18 + i * 4
        via_y = NCE1_Y - nce_bga_half - 1
        L.append(segment(via_x, via_y, via_x, via_y - 10, 0.10, layer, net_id))
        L.append(segment(via_x, via_y - 10, hbm_x, hbm_y + 6, 0.10, layer, net_id))
        L.append(via(via_x, via_y, 0.5, 0.3, net_id, ("F.Cu", layer)))

    # ── RF differential pairs: NCE0 → HMC8410 → TFLN ──
    for i in range(4):
        net_p = nets.get(f"RF_TX{i}_P", 0)
        net_n = nets.get(f"RF_TX{i}_N", 0)
        net_drv_p = nets.get(f"RF_DRV{i}_P", 0)
        net_drv_n = nets.get(f"RF_DRV{i}_N", 0)

        # NCE0 RF output → HMC8410 input (In4.Cu/In5.Cu differential)
        nce_rf_x = NCE0_X + nce_bga_half + 2  # outside BGA field
        nce_rf_y = NCE0_Y - 10 + i * 6
        hmc_x = TFLN_X - 20 + i * 13
        hmc_y = TFLN_Y - 15

        L.append(diff_pair_route(nce_rf_x, nce_rf_y, hmc_x - 3, hmc_y,
                                 0.09, 0.09, "In4.Cu", net_p, net_n))

        # HMC8410 output → TFLN input (alternate layers to avoid crossings)
        tfln_rf_y = TFLN_Y - 5 + i * 3
        rf_out_layer = "In5.Cu" if i % 2 == 0 else "In28.Cu"
        L.append(diff_pair_route(hmc_x + 3, hmc_y, TFLN_X - 4, tfln_rf_y,
                                 0.15, 0.20, rf_out_layer, net_drv_p, net_drv_n))

    # ── PCIe lanes: NCE → Retimer → Switch → Slot ──
    slot_positions = [60, 165, 270, 375]
    for i in range(4):
        # NCE → Retimer
        nce_pcie_x = (NCE0_X if i < 2 else NCE1_X) + nce_bga_half + 2
        nce_pcie_y = (NCE0_Y if i < 2 else NCE1_Y) + nce_bga_half + 2 + (i % 2) * 5
        ret_x = 130 + i * 50
        ret_y = 290
        net_id = nets.get(f"RET{i}_RX_P", 0)
        L.append(segment(nce_pcie_x, nce_pcie_y, ret_x, ret_y - 5, 0.12, "In7.Cu", net_id))
        L.append(via(nce_pcie_x, nce_pcie_y, 0.5, 0.3, net_id, ("F.Cu", "In7.Cu")))

        # Retimer → Switch
        sw_x = 130 + i * 50
        sw_y = 310
        L.append(segment(ret_x, ret_y + 5, sw_x, sw_y - 5, 0.12, "In8.Cu", net_id))

        # Switch → Slot
        slot_x = slot_positions[i]
        slot_y = 343
        sw_dn_net = nets.get(f"PCIESW{i}_DN0", 0)
        L.append(segment(sw_x, sw_y + 5, slot_x, slot_y - 3, 0.12, "In8.Cu", sw_dn_net))

    # ── Power routing: VRM → DrMOS (PWM signals on I2C_SPI layer) ──
    for vrm_idx in range(4):
        vx, vy = vrm_positions[vrm_idx]
        for ph in range(6):
            drmos_idx = vrm_idx * 6 + ph
            side = 0 if drmos_idx < 12 else 1
            local_idx = drmos_idx % 12
            col = local_idx // 6
            row = local_idx % 6
            if side == 0:
                dx = 55 + col * 10
                dy = 80 + row * 28
            else:
                dx = 355 + col * 10
                dy = 80 + row * 28
            net_id = nets.get(f"VRM{vrm_idx}_PWM{ph}", 0)
            L.append(segment(vx, vy + 2 + ph, dx, dy, 0.15, "In9.Cu", net_id))

    # ── DrMOS PHASE → V_CORE power plane ──
    # In final design, EP thermal vias connect DrMOS to In10.Cu V_CORE plane.
    # Zone pour on In10.Cu provides the power connection.
    # GND stitching vias between DrMOS columns for return path
    gnd_stitch = nets["GND"]
    for row in range(6):
        dy = 80 + row * 28
        # Left bank stitching (between two columns at x=55,65)
        L.append(via(47, dy + 14, 0.5, 0.3, gnd_stitch, ("F.Cu", "In3.Cu")))
        # Right bank stitching
        L.append(via(373, dy + 14, 0.5, 0.3, gnd_stitch, ("F.Cu", "In3.Cu")))

    # ── 12V input traces to VRMs (on In13.Cu 12V plane, via at board edge) ──
    v12_net = nets["+12V"]
    for vx, vy in vrm_positions:
        # Via at top edge → route on 12V plane layer to VRM
        L.append(via(vx, 5, 0.8, 0.4, v12_net, ("F.Cu", "In13.Cu")))
        L.append(segment(vx, 5, vx, vy - 10, 1.0, "In13.Cu", v12_net))
        L.append(via(vx, vy - 10, 0.8, 0.4, v12_net, ("In13.Cu", "F.Cu")))

    # ── I2C bus: BMC → NCE0 → NCE1 ──
    i2c_sda_net = nets["I2C_SDA"]
    i2c_scl_net = nets["I2C_SCL"]
    bmc_x, bmc_y = 50, 45
    # BMC → NCE0 (routed outside BGA field)
    nce_edge = nce_bga_half + 2
    L.append(segment(bmc_x + 5, bmc_y, NCE0_X - nce_edge, NCE0_Y + nce_edge, 0.15, "In9.Cu", i2c_sda_net))
    L.append(segment(bmc_x + 5, bmc_y + 1.5, NCE0_X - nce_edge, NCE0_Y + nce_edge + 1.5, 0.15, "In9.Cu", i2c_scl_net))
    # NCE0 → NCE1
    L.append(segment(NCE0_X + nce_edge, NCE0_Y + nce_edge, NCE1_X - nce_edge, NCE1_Y + nce_edge, 0.15, "In9.Cu", i2c_sda_net))
    L.append(segment(NCE0_X + nce_edge, NCE0_Y + nce_edge + 1.5, NCE1_X - nce_edge, NCE1_Y + nce_edge + 1.5, 0.15, "In9.Cu", i2c_scl_net))
    # Vias
    L.append(via(bmc_x + 5, bmc_y, 0.4, 0.2, i2c_sda_net, ("F.Cu", "In9.Cu")))
    L.append(via(bmc_x + 5, bmc_y + 1.5, 0.4, 0.2, i2c_scl_net, ("F.Cu", "In9.Cu")))

    # ── SPI bus: BMC → NCE0 ──
    spi_nets = {n: nets[n] for n in ["SPI_MOSI", "SPI_MISO", "SPI_SCK", "SPI_CS"]}
    for idx, (name, nid) in enumerate(spi_nets.items()):
        L.append(segment(bmc_x + 5, bmc_y + 4 + idx * 1.5, NCE0_X - nce_edge, NCE0_Y + nce_edge + 4 + idx * 1.5, 0.15, "In9.Cu", nid))
        L.append(via(bmc_x + 5, bmc_y + 4 + idx * 1.5, 0.5, 0.3, nid, ("F.Cu", "In9.Cu")))

    # ── Clock distribution: Si5395A → Retimers/Switches ──
    # CLK0 (at x=170) routes to retimers, CLK1 (at x=250) routes to switches
    # Each on its own layer to avoid crossings between the two jitter cleaners
    for clk_idx in range(2):
        clk_x = 170 + clk_idx * 80
        clk_y = 30
        clk_layer = "In25.Cu" if clk_idx == 0 else "In26.Cu"
        for ch in range(4):
            net_p = nets.get(f"CLK{clk_idx}_OUT{ch}_P", 0)
            net_n = nets.get(f"CLK{clk_idx}_OUT{ch}_N", 0)
            target_x = 130 + ch * 50
            target_y = 290 if clk_idx == 0 else 310
            L.append(diff_pair_route(clk_x + (ch - 1.5) * 0.4, clk_y + 5,
                                     target_x, target_y - 5,
                                     0.10, 0.10, clk_layer, net_p, net_n, vertical=True))

    # ── TFLN clock from NCE0 ──
    tfln_clk_p = nets.get("TFLN_CLK_P", 0)
    tfln_clk_n = nets.get("TFLN_CLK_N", 0)
    L.append(diff_pair_route(NCE0_X + nce_edge, NCE0_Y + 15, TFLN_X - 4, TFLN_Y + 4,
                             0.10, 0.10, "In4.Cu", tfln_clk_p, tfln_clk_n))

    # ── Decoupling cap connections (short traces to power plane vias) ──
    rails_list = ["+0V8"]*4 + ["+1V8"]*4 + ["+3V3"]*4 + ["+0V9"]*4
    gnd_net = nets["GND"]
    for i in range(16):
        col = i % 4
        row = i // 4
        cx = 185 + col * 5.0
        cy = NCE0_Y - 20 + row * 4.0
        rail_net = nets[rails_list[i]]
        L.append(segment(cx - 0.48, cy, cx - 1.8, cy, 0.3, "F.Cu", rail_net))
        L.append(segment(cx + 0.48, cy, cx + 1.8, cy, 0.3, "F.Cu", gnd_net))
        # Through-hole vias (no HBM routing in this area between NCEs)
        L.append(via(cx - 1.8, cy, 0.5, 0.3, rail_net))
        L.append(via(cx + 1.8, cy, 0.5, 0.3, gnd_net))

    # ══════════════════════════════════════════════════════════════════════
    # DESIGN ANNOTATIONS
    # ══════════════════════════════════════════════════════════════════════

    # Substrate regions (green in reference image)
    for nce_x, nce_y, label in [(NCE0_X, NCE0_Y, "NCE0 Substrate"),
                                  (NCE1_X, NCE1_Y, "NCE1 Substrate")]:
        L.append(f'  (gr_rect (start {nce_x-30} {nce_y-35}) (end {nce_x+30} {nce_y+35}) (layer "Eco1.User") (width 0.5) (fill solid) (tstamp "{uid()}"))')
        L.append(f'  (gr_text "{label}" (at {nce_x} {nce_y+40}) (layer "Cmts.User") (effects (font (size 2 2) (thickness 0.3)))  (tstamp "{uid()}"))')

    # TFLN region
    L.append(f'  (gr_rect (start {TFLN_X-13} {TFLN_Y-5}) (end {TFLN_X+13} {TFLN_Y+5}) (layer "Eco2.User") (width 0.3) (fill solid) (tstamp "{uid()}"))')
    L.append(f'  (gr_text "TFLN Photonic Bridge" (at {TFLN_X} {TFLN_Y+10}) (layer "Cmts.User") (effects (font (size 1.5 1.5) (thickness 0.2)))  (tstamp "{uid()}"))')

    # Board title
    L.append(f'  (gr_text "LightRail NCE Gen3 Dual Accelerator" (at 210 -5) (layer "F.SilkS") (effects (font (size 3 3) (thickness 0.3)))  (tstamp "{uid()}"))')
    L.append(f'  (gr_text "420x350mm | 32L HDI Megtron-7 | 256GB HBM4 | 1000A@0.8V" (at 210 358) (layer "B.SilkS") (effects (font (size 2 2) (thickness 0.2)))  (tstamp "{uid()}"))')

    L.append(')')
    return "\n".join(L) + "\n"


def main():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(repo, "NCE_Gen3_82comp.kicad_pcb")
    content = generate()
    with open(path, 'w') as f:
        f.write(content)
    segs = content.count('(segment ')
    vias = content.count('(via ')
    zones = content.count('(zone ')
    fps = content.count('(footprint ')
    nets_count = content.count('(net ') - fps  # subtract net refs in footprints
    print(f"Generated {path}")
    print(f"Footprints: {fps}  Segments: {segs}  Vias: {vias}  Zones: {zones}")


if __name__ == "__main__":
    main()

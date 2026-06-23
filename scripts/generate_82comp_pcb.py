#!/usr/bin/env python3
"""Generate KiCad PCB for the 82-component NCE Gen3 dual-accelerator board.

Reproduces the reference layout with dense routing:
  - 420 x 350 mm board with PCIe card-edge notch
  - 32-layer HDI stackup (Megtron-7 outer, High-Tg-FR4 inner, Faradflex embedded cap)
  - Symmetric dual-NCE placement with HBM flanking arrays
  - Dense BGA breakout routing (curved fanout)
  - TFLN photonic module centered between NCEs with vertical diff pairs
  - DrMOS power stages on left/right edges with parallel power traces
  - PCIe slots along bottom edge
  - Full power plane zones, B.Cu edge routing, via stitching
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
    # HBM channels per NCE (8 channels × 128 bits = 1024 per NCE, represent as 64 diff pairs per NCE)
    for nce in range(2):
        pfx = f"NCE{nce}"
        for i in range(64):
            nets[f"{pfx}_HBM_D{i}_P"] = nid; nid += 1
            nets[f"{pfx}_HBM_D{i}_N"] = nid; nid += 1
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
        for ln in range(16):
            nets[f"PCIESW{sw}_LN{ln}_P"] = nid; nid += 1
            nets[f"PCIESW{sw}_LN{ln}_N"] = nid; nid += 1
        nets[f"PCIESW{sw}_DN0"] = nid; nid += 1
    # Retimer
    for i in range(4):
        for ln in range(4):
            nets[f"RET{i}_RX{ln}_P"] = nid; nid += 1
            nets[f"RET{i}_RX{ln}_N"] = nid; nid += 1
    # HBM ref clock
    for nce in range(2):
        for i in range(8):
            nets[f"NCE{nce}_REFCK{i}_P"] = nid; nid += 1
            nets[f"NCE{nce}_REFCK{i}_N"] = nid; nid += 1
    # BGA breakout (generic fan-out nets)
    for nce in range(2):
        for i in range(120):
            nets[f"NCE{nce}_FAN{i}"] = nid; nid += 1
    # TFLN optical data lanes
    for i in range(16):
        nets[f"TFLN_D{i}_P"] = nid; nid += 1
        nets[f"TFLN_D{i}_N"] = nid; nid += 1
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
    lines.append('      (layer "F.Cu" (type "copper") (thickness 0.0700))')

    for i in range(1, 10):
        mat = "Megtron-7"
        dtype = "prepreg" if (i % 2 == 1) else "core"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "{mat}") (epsilon_r 3.3) (loss_tangent 0.002))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0175))')

    for i in range(10, 15):
        dtype = "core" if (i % 2 == 0) else "prepreg"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "High-Tg-FR4") (epsilon_r 4.2) (loss_tangent 0.015))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0700))')

    lines.append('      (layer "dielectric 15" (type "core") (thickness 0.0240) (material "Faradflex-BC24") (epsilon_r 14.0) (loss_tangent 0.02))')
    lines.append('      (layer "In15.Cu" (type "copper") (thickness 0.0350))')
    lines.append('      (layer "dielectric 16" (type "core") (thickness 0.0240) (material "Faradflex-BC24") (epsilon_r 14.0) (loss_tangent 0.02))')
    lines.append('      (layer "In16.Cu" (type "copper") (thickness 0.0700))')

    for i in range(17, 21):
        dtype = "prepreg" if (i % 2 == 1) else "core"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "High-Tg-FR4") (epsilon_r 4.2) (loss_tangent 0.015))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0700))')

    for i in range(21, 31):
        mat = "Megtron-7"
        dtype = "prepreg" if (i % 2 == 1) else "core"
        lines.append(f'      (layer "dielectric {i}" (type "{dtype}") (thickness 0.0760) (material "{mat}") (epsilon_r 3.3) (loss_tangent 0.002))')
        lines.append(f'      (layer "In{i}.Cu" (type "copper") (thickness 0.0175))')

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
    """Generate a BGA footprint with full pad array."""
    lines = []
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y} {angle})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 {-(rows*pad_pitch/2 + 3)}) (layer "F.SilkS") (effects (font (size 1.5 1.5) (thickness 0.15))))')
    lines.append(f'    (fp_text value "{value}" (at 0 {rows*pad_pitch/2 + 3}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    # Full BGA pad array (all rows/cols for realistic appearance)
    depth = min(4, rows // 2)
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
    half = body_size / 2 + pad_h / 2
    for i in range(ppside):
        offset = (i - (ppside-1)/2) * pad_pitch
        lines.append(f'    (pad "{i+1}" smd rect (at {-half:.4f} {offset:.4f}) (size {pad_h} {pad_w}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        lines.append(f'    (pad "{ppside+i+1}" smd rect (at {offset:.4f} {half:.4f}) (size {pad_w} {pad_h}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        lines.append(f'    (pad "{2*ppside+i+1}" smd rect (at {half:.4f} {-offset:.4f}) (size {pad_h} {pad_w}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
        lines.append(f'    (pad "{3*ppside+i+1}" smd rect (at {-offset:.4f} {-half:.4f}) (size {pad_w} {pad_h}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    if ep_size:
        lines.append(f'    (pad "{pin_count+1}" smd rect (at 0 0) (size {ep_size} {ep_size}) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    crt = half + pad_h / 2 + 0.5
    lines.append(f'    (fp_rect (start {-crt:.4f} {-crt:.4f}) (end {crt:.4f} {crt:.4f}) (layer "F.CrtYd") (width 0.05))')
    lines.append('  )')
    return "\n".join(lines)


def fp_sot23(ref, value, x, y, angle=0):
    lines = []
    fp_name = "Package_TO_SOT_SMD:SOT-23-5"
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y} {angle})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    lines.append(f'    (fp_text value "{value}" (at 0 2.5) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    for i, (px, py) in enumerate([(-1.1, -0.95), (-1.1, 0), (-1.1, 0.95), (1.1, 0.95), (1.1, -0.95)]):
        lines.append(f'    (pad "{i+1}" smd rect (at {px} {py}) (size 1.0 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (net 0 ""))')
    lines.append('  )')
    return "\n".join(lines)


def fp_cap_0402(ref, value, x, y, angle=0, net1_id=0, net1_name="", net2_id=0, net2_name=""):
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
    lines = []
    fp_name = "LightRail:PCIE_x16_SLOT"
    lines.append(f'  (footprint "{fp_name}" (layer "F.Cu") (tstamp "{uid()}")')
    lines.append(f'    (at {x} {y})')
    lines.append(f'    (fp_text reference "{ref}" (at 0 -5) (layer "F.SilkS") (effects (font (size 1.5 1.5) (thickness 0.15))))')
    lines.append(f'    (fp_text value "PCIe_x16_SLOT" (at 0 5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
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
    return f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (width {width}) (layer "{layer}") (net {net_id}) (tstamp "{uid()}"))'


def arc_segments(cx, cy, radius, start_angle, end_angle, n_segs, width, layer, net_id):
    """Generate arc as polyline segments."""
    lines = []
    for i in range(n_segs):
        a1 = math.radians(start_angle + (end_angle - start_angle) * i / n_segs)
        a2 = math.radians(start_angle + (end_angle - start_angle) * (i + 1) / n_segs)
        x1 = cx + radius * math.cos(a1)
        y1 = cy + radius * math.sin(a1)
        x2 = cx + radius * math.cos(a2)
        y2 = cy + radius * math.sin(a2)
        lines.append(segment(x1, y1, x2, y2, width, layer, net_id))
    return "\n".join(lines)


def via(x, y, size, drill, net_id, layers=("F.Cu", "B.Cu")):
    size = max(size, 0.5)
    drill = max(drill, 0.3)
    return f'  (via (at {x:.3f} {y:.3f}) (size {size}) (drill {drill}) (layers "{layers[0]}" "{layers[1]}") (net {net_id}) (tstamp "{uid()}"))'


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
# DENSE ROUTING GENERATORS
# ══════════════════════════════════════════════════════════════════════════

def generate_bga_breakout(nce_x, nce_y, nce_idx, nets, direction="both"):
    """Generate dense BGA breakout routing - curved fanout from NCE.
    
    Creates ~240 traces per NCE with multi-segment curves.
    """
    lines = []
    bga_half = 20.0
    
    # Top fanout - 50 traces with 2-segment curves
    for i in range(50):
        angle = -70 + (i / 49) * 140
        sx = nce_x + bga_half * math.sin(math.radians(angle))
        sy = nce_y - bga_half * math.cos(math.radians(angle))
        reach = bga_half + 18 + i * 0.25
        ex = nce_x + reach * math.sin(math.radians(angle))
        ey = nce_y - reach * math.cos(math.radians(angle))
        mx = (sx + ex) / 2 + (i - 25) * 0.15
        my = (sy + ey) / 2
        
        net_id = nets.get(f"NCE{nce_idx}_FAN{i % 120}", 0)
        layer = ["In1.Cu", "In2.Cu", "In3.Cu"][i % 3]
        lines.append(segment(sx, sy, mx, my, 0.09, layer, net_id))
        lines.append(segment(mx, my, ex, ey, 0.09, layer, net_id))
        lines.append(via(sx, sy, 0.3, 0.15, net_id, ("F.Cu", layer)))
        # F.Cu stub from pad to via (visible as red traces in reference)
        lines.append(segment(sx + (i-25)*0.05, sy + 1, sx, sy, 0.12, "F.Cu", net_id))
    
    # Bottom fanout - 50 traces
    for i in range(50):
        angle = -70 + (i / 49) * 140
        sx = nce_x + bga_half * math.sin(math.radians(angle))
        sy = nce_y + bga_half * math.cos(math.radians(angle))
        reach = bga_half + 18 + i * 0.25
        ex = nce_x + reach * math.sin(math.radians(angle))
        ey = nce_y + reach * math.cos(math.radians(angle))
        mx = (sx + ex) / 2 + (i - 25) * 0.15
        my = (sy + ey) / 2
        
        net_id = nets.get(f"NCE{nce_idx}_FAN{(i + 30) % 120}", 0)
        layer = ["In3.Cu", "In4.Cu", "In5.Cu"][i % 3]
        lines.append(segment(sx, sy, mx, my, 0.09, layer, net_id))
        lines.append(segment(mx, my, ex, ey, 0.09, layer, net_id))
        lines.append(via(sx, sy, 0.3, 0.15, net_id, ("F.Cu", layer)))
        lines.append(segment(sx + (i-25)*0.05, sy - 1, sx, sy, 0.12, "F.Cu", net_id))
    
    # Left/Right fanout - 40 traces each (toward DrMOS/TFLN)
    for side in range(2):  # 0=left, 1=right
        for i in range(40):
            if side == 0:
                angle = 150 + (i / 39) * 60
            else:
                angle = -30 + (i / 39) * 60
            sx = nce_x + bga_half * math.cos(math.radians(angle))
            sy = nce_y + bga_half * math.sin(math.radians(angle))
            reach = bga_half + 22 + i * 0.35
            ex = nce_x + reach * math.cos(math.radians(angle))
            ey = nce_y + reach * math.sin(math.radians(angle))
            mx = (sx + ex) / 2
            my = (sy + ey) / 2 + (i - 20) * 0.2
            
            net_id = nets.get(f"NCE{nce_idx}_FAN{(i + 60 + side * 30) % 120}", 0)
            layer = ["In5.Cu", "In6.Cu", "In7.Cu", "In8.Cu"][i % 4]
            lines.append(segment(sx, sy, mx, my, 0.09, layer, net_id))
            lines.append(segment(mx, my, ex, ey, 0.09, layer, net_id))
            lines.append(via(sx, sy, 0.3, 0.15, net_id, ("F.Cu", layer)))
            # Via only (no F.Cu stub to avoid crossings at BGA corners)
    
    return "\n".join(lines)


def generate_hbm_routing(nce_x, nce_y, nce_idx, nets):
    """Generate dense HBM differential pair routing (64 diff pairs per NCE)."""
    lines = []
    bga_half = 21.0
    
    # 32 diff pairs to top HBM bank, 32 to bottom
    for bank in range(2):  # 0=top, 1=bottom
        for i in range(32):
            net_p = nets.get(f"NCE{nce_idx}_HBM_D{bank*32+i}_P", 0)
            net_n = nets.get(f"NCE{nce_idx}_HBM_D{bank*32+i}_N", 0)
            
            # Layer assignment: alternate across 4 layers for density
            if nce_idx == 0:
                layers = ["In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"]
            else:
                layers = ["In22.Cu", "In23.Cu", "In24.Cu", "In25.Cu"]
            layer = layers[i % 4]
            
            # Source: BGA edge (spread across top/bottom)
            spread = (i - 15.5) * 0.6  # ±9.3mm spread
            if bank == 0:
                sy = nce_y - bga_half
                ey = nce_y - 42  # HBM top row y position
            else:
                sy = nce_y + bga_half
                ey = nce_y + 42
            
            sx = nce_x + spread
            # Target: distributed across 4 HBM modules
            hbm_col = i // 8  # which of 4 HBM modules
            hbm_pin = i % 8   # which pin on that module
            ex = nce_x - 30 + hbm_col * 20 + (hbm_pin - 3.5) * 0.65
            
            # Route with slight curve
            mid_y = (sy + ey) / 2
            lines.append(segment(sx, sy, sx + (ex-sx)*0.3, mid_y, 0.09, layer, net_p))
            lines.append(segment(sx + (ex-sx)*0.3, mid_y, ex, ey, 0.09, layer, net_p))
            # N pair (offset by gap)
            lines.append(segment(sx + 0.18, sy, sx + 0.18 + (ex-sx)*0.3, mid_y, 0.09, layer, net_n))
            lines.append(segment(sx + 0.18 + (ex-sx)*0.3, mid_y, ex + 0.18, ey, 0.09, layer, net_n))
            
            # Via at BGA edge
            lines.append(via(sx, sy, 0.3, 0.15, net_p, ("F.Cu", layer)))
            lines.append(via(sx + 0.18, sy, 0.3, 0.15, net_n, ("F.Cu", layer)))
    
    return "\n".join(lines)


def generate_tfln_routing(tfln_x, tfln_y, nce0_x, nce1_x, nets):
    """Generate dense vertical differential pairs between NCEs through TFLN (blue in reference)."""
    lines = []
    
    # 16 diff pairs running vertically through TFLN area
    for i in range(16):
        net_p = nets.get(f"TFLN_D{i}_P", 0)
        net_n = nets.get(f"TFLN_D{i}_N", 0)
        
        x_pos = tfln_x - 8 + i * 1.0
        y_top = tfln_y - 45  # extended range
        y_bot = tfln_y + 45
        
        # Main vertical run on B.Cu (blue)
        lines.append(segment(x_pos, y_top, x_pos, y_bot, 0.10, "B.Cu", net_p))
        lines.append(segment(x_pos + 0.20, y_top, x_pos + 0.20, y_bot, 0.10, "B.Cu", net_n))
        
        # Extension traces on inner layers
        lines.append(segment(x_pos, y_top - 30, x_pos, y_top, 0.10, "In5.Cu", net_p))
        lines.append(segment(x_pos + 0.20, y_top - 30, x_pos + 0.20, y_top, 0.10, "In5.Cu", net_n))
        lines.append(segment(x_pos, y_bot, x_pos, y_bot + 30, 0.10, "In5.Cu", net_p))
        lines.append(segment(x_pos + 0.20, y_bot, x_pos + 0.20, y_bot + 30, 0.10, "In5.Cu", net_n))
        
        # Vias
        lines.append(via(x_pos, y_top, 0.3, 0.15, net_p, ("In5.Cu", "B.Cu")))
        lines.append(via(x_pos + 0.20, y_top, 0.3, 0.15, net_n, ("In5.Cu", "B.Cu")))
        lines.append(via(x_pos, y_bot, 0.3, 0.15, net_p, ("B.Cu", "In5.Cu")))
        lines.append(via(x_pos + 0.20, y_bot, 0.3, 0.15, net_n, ("B.Cu", "In5.Cu")))
    
    # Additional interconnect traces between NCE0-TFLN and TFLN-NCE1 on In9.Cu
    for i in range(8):
        net_p = nets.get(f"TFLN_D{i}_P", 0)
        # NCE0 side (routed on In9.Cu to avoid BGA breakout crossings)
        x0 = nce0_x + 25
        xt = tfln_x - 13
        y_offset = tfln_y - 6 + i * 1.5
        lines.append(segment(x0, y_offset, xt, y_offset, 0.12, "In9.Cu", net_p))
        lines.append(via(x0, y_offset, 0.3, 0.15, net_p, ("F.Cu", "In9.Cu")))
        # NCE1 side
        x1 = nce1_x - 25
        xtr = tfln_x + 13
        lines.append(segment(xtr, y_offset, x1, y_offset, 0.12, "In9.Cu", net_p))
        lines.append(via(x1, y_offset, 0.3, 0.15, net_p, ("F.Cu", "In9.Cu")))
    
    return "\n".join(lines)


def generate_drmos_routing(vrm_positions, nets):
    """Generate parallel power traces from DrMOS arrays toward NCEs."""
    lines = []
    NCE0_X, NCE0_Y, NCE1_X, NCE1_Y = 145, 160, 275, 160
    
    # Left bank: 12 DrMOS → NCE0 power (multiple parallel traces per DrMOS)
    for i in range(12):
        col = i // 6
        row = i % 6
        dx = 55 + col * 10
        dy = 80 + row * 28
        
        net_vcore = nets["+0V8"]
        net_gnd = nets["GND"]
        
        # 3 parallel power traces per DrMOS (more visible density)
        for t in range(3):
            offset = (t - 1) * 2.0
            mid_x = (dx + NCE0_X - 22) / 2 + offset * 2
            ty = dy + offset
            lines.append(segment(dx + 4, ty, mid_x, ty + (i-5.5)*1.2, 0.4, "F.Cu", net_vcore))
            lines.append(segment(mid_x, ty + (i-5.5)*1.2, NCE0_X - 22, 128 + i * 5 + t * 1.5, 0.4, "F.Cu", net_vcore))
        
        # GND return on B.Cu (2 traces)
        for t in range(2):
            offset = (t - 0.5) * 2.5
            mid_x = (dx + NCE0_X - 22) / 2 + offset
            ty = dy + offset + 1
            lines.append(segment(dx + 4, ty, mid_x, ty + (i-5.5)*1.2, 0.4, "B.Cu", net_gnd))
            lines.append(segment(mid_x, ty + (i-5.5)*1.2, NCE0_X - 22, 130 + i * 5 + t * 2, 0.4, "B.Cu", net_gnd))
    
    # Right bank: 12 DrMOS → NCE1 power
    for i in range(12):
        col = i // 6
        row = i % 6
        dx = 355 + col * 10
        dy = 80 + row * 28
        
        net_vcore = nets["+0V8"]
        net_gnd = nets["GND"]
        
        for t in range(3):
            offset = (t - 1) * 2.0
            mid_x = (dx + NCE1_X + 22) / 2 + offset * 2
            ty = dy + offset
            lines.append(segment(dx - 4, ty, mid_x, ty + (i-5.5)*1.2, 0.4, "F.Cu", net_vcore))
            lines.append(segment(mid_x, ty + (i-5.5)*1.2, NCE1_X + 22, 128 + i * 5 + t * 1.5, 0.4, "F.Cu", net_vcore))
        
        for t in range(2):
            offset = (t - 0.5) * 2.5
            mid_x = (dx + NCE1_X + 22) / 2 + offset
            ty = dy + offset + 1
            lines.append(segment(dx - 4, ty, mid_x, ty + (i-5.5)*1.2, 0.4, "B.Cu", net_gnd))
            lines.append(segment(mid_x, ty + (i-5.5)*1.2, NCE1_X + 22, 130 + i * 5 + t * 2, 0.4, "B.Cu", net_gnd))
    
    # VRM → DrMOS PWM signals
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
            lines.append(segment(vx, vy + 2 + ph * 0.8, dx, dy - 3, 0.15, "In9.Cu", net_id))
    
    return "\n".join(lines)


def generate_pcie_routing(nets, slot_positions):
    """Generate PCIe lane routing from switches to slots."""
    lines = []
    NCE0_X, NCE0_Y = 145, 160
    NCE1_X, NCE1_Y = 275, 160
    bga_half = 21
    
    for sw_idx in range(4):
        sw_x = 130 + sw_idx * 50
        sw_y = 310
        slot_x = slot_positions[sw_idx]
        slot_y = 343
        
        # 16 differential lanes per switch
        for ln in range(16):
            net_p = nets.get(f"PCIESW{sw_idx}_LN{ln}_P", 0)
            net_n = nets.get(f"PCIESW{sw_idx}_LN{ln}_N", 0)
            
            # Fan out from switch to slot
            sw_pin_x = sw_x - 4 + (ln / 15) * 8
            slot_pin_x = slot_x - 8 + (ln / 15) * 16
            
            layer = "In7.Cu" if ln < 8 else "In8.Cu"
            lines.append(segment(sw_pin_x, sw_y + 5, slot_pin_x, slot_y - 3, 0.12, layer, net_p))
            lines.append(segment(sw_pin_x + 0.30, sw_y + 5, slot_pin_x + 0.30, slot_y - 3, 0.12, layer, net_n))
        
        # Retimer → Switch connection
        ret_x = 130 + sw_idx * 50
        ret_y = 290
        for ln in range(4):
            net_p = nets.get(f"RET{sw_idx}_RX{ln}_P", 0)
            net_n = nets.get(f"RET{sw_idx}_RX{ln}_N", 0)
            rx = ret_x - 2 + ln * 1.5
            lines.append(segment(rx, ret_y + 5, sw_x - 2 + ln * 1.5, sw_y - 5, 0.12, "In8.Cu", net_p))
            lines.append(segment(rx + 0.30, ret_y + 5, sw_x - 2 + ln * 1.5 + 0.30, sw_y - 5, 0.12, "In8.Cu", net_n))
        
        # NCE → Retimer
        nce_x = NCE0_X if sw_idx < 2 else NCE1_X
        nce_y = NCE0_Y if sw_idx < 2 else NCE1_Y
        for ln in range(4):
            net_p = nets.get(f"RET{sw_idx}_RX{ln}_P", 0)
            src_x = nce_x + bga_half + 2 + ln * 1.0
            src_y = nce_y + bga_half + 2 + (sw_idx % 2) * 8
            lines.append(segment(src_x, src_y, ret_x - 2 + ln * 1.5, ret_y - 5, 0.12, "In7.Cu", net_p))
            lines.append(via(src_x, src_y, 0.3, 0.15, net_p, ("F.Cu", "In7.Cu")))
    
    return "\n".join(lines)


def generate_bcu_edge_routing(nets):
    """Generate B.Cu edge routing (blue traces in reference image)."""
    lines = []
    gnd = nets["GND"]
    v12 = nets["+12V"]
    v33 = nets["+3V3"]
    
    # Power distribution traces along board edges on B.Cu
    # Top edge - 12V distribution
    for i in range(8):
        x_start = 20 + i * 50
        lines.append(segment(x_start, 5, x_start + 45, 5, 1.0, "B.Cu", v12))
    
    # Left edge - 3.3V and GND rails
    for i in range(10):
        y_pos = 20 + i * 30
        lines.append(segment(3, y_pos, 3, y_pos + 25, 0.5, "B.Cu", v33))
        lines.append(segment(7, y_pos, 7, y_pos + 25, 0.5, "B.Cu", gnd))
    
    # Right edge - mirror of left
    for i in range(10):
        y_pos = 20 + i * 30
        lines.append(segment(417, y_pos, 417, y_pos + 25, 0.5, "B.Cu", v33))
        lines.append(segment(413, y_pos, 413, y_pos + 25, 0.5, "B.Cu", gnd))
    
    # Bottom edge - GND bus before PCIe slots
    for i in range(12):
        x_start = 15 + i * 33
        lines.append(segment(x_start, 335, x_start + 28, 335, 0.8, "B.Cu", gnd))
    
    # Diagonal power feeds from edges to VRM areas
    lines.append(segment(5, 15, 30, 95, 1.0, "B.Cu", v12))
    lines.append(segment(5, 285, 30, 225, 1.0, "B.Cu", v12))
    lines.append(segment(415, 15, 390, 95, 1.0, "B.Cu", v12))
    lines.append(segment(415, 285, 390, 225, 1.0, "B.Cu", v12))
    
    return "\n".join(lines)


def generate_via_stitching(nets):
    """Generate via stitching arrays for GND continuity."""
    lines = []
    gnd = nets["GND"]
    
    # Via fence around NCE BGA areas
    for nce_x in [145, 275]:
        nce_y = 160
        radius = 24
        for angle in range(0, 360, 8):
            vx = nce_x + radius * math.cos(math.radians(angle))
            vy = nce_y + radius * math.sin(math.radians(angle))
            lines.append(via(vx, vy, 0.5, 0.3, gnd))
    
    # Via arrays between DrMOS columns (power return)
    for row in range(6):
        dy = 80 + row * 28
        for col in range(3):
            # Left bank
            lines.append(via(47 + col * 3, dy + 7, 0.5, 0.3, gnd))
            lines.append(via(47 + col * 3, dy + 14, 0.5, 0.3, gnd))
            lines.append(via(47 + col * 3, dy + 21, 0.5, 0.3, gnd))
            # Right bank
            lines.append(via(373 + col * 3, dy + 7, 0.5, 0.3, gnd))
            lines.append(via(373 + col * 3, dy + 14, 0.5, 0.3, gnd))
            lines.append(via(373 + col * 3, dy + 21, 0.5, 0.3, gnd))
    
    # Via stitching along board edges
    for x in range(10, 420, 15):
        lines.append(via(x, 3, 0.5, 0.3, gnd))
        lines.append(via(x, 347, 0.5, 0.3, gnd))
    for y in range(10, 350, 15):
        lines.append(via(3, y, 0.5, 0.3, gnd))
        lines.append(via(417, y, 0.5, 0.3, gnd))
    
    # Via stitching between NCEs (around TFLN area)
    for y in range(130, 195, 5):
        lines.append(via(175, y, 0.5, 0.3, gnd))
        lines.append(via(245, y, 0.5, 0.3, gnd))
    
    return "\n".join(lines)


def generate_clock_routing(nets):
    """Clock distribution with dense diff pairs."""
    lines = []
    
    for clk_idx in range(2):
        clk_x = 170 + clk_idx * 80
        clk_y = 30
        clk_layer = "In25.Cu" if clk_idx == 0 else "In26.Cu"
        for ch in range(4):
            net_p = nets.get(f"CLK{clk_idx}_OUT{ch}_P", 0)
            net_n = nets.get(f"CLK{clk_idx}_OUT{ch}_N", 0)
            target_x = 130 + ch * 50
            target_y = 290 if clk_idx == 0 else 310
            
            # Multi-segment route for curved appearance
            mid_x = (clk_x + target_x) / 2
            mid_y = (clk_y + target_y) / 2
            
            cx = clk_x + (ch - 1.5) * 2.0
            lines.append(segment(cx, clk_y + 5, mid_x, mid_y, 0.10, clk_layer, net_p))
            lines.append(segment(mid_x, mid_y, target_x, target_y - 5, 0.10, clk_layer, net_p))
            lines.append(segment(cx + 0.20, clk_y + 5, mid_x + 0.20, mid_y, 0.10, clk_layer, net_n))
            lines.append(segment(mid_x + 0.20, mid_y, target_x + 0.20, target_y - 5, 0.10, clk_layer, net_n))
            
            lines.append(via(cx, clk_y + 5, 0.3, 0.15, net_p, ("F.Cu", clk_layer)))
            lines.append(via(cx + 0.20, clk_y + 5, 0.3, 0.15, net_n, ("F.Cu", clk_layer)))
    
    # TFLN clock
    tfln_clk_p = nets.get("TFLN_CLK_P", 0)
    tfln_clk_n = nets.get("TFLN_CLK_N", 0)
    lines.append(diff_pair_route(167, 175, 206, 164, 0.10, 0.10, "In4.Cu", tfln_clk_p, tfln_clk_n))
    
    return "\n".join(lines)


def generate_rf_routing(nets, tfln_x, tfln_y, nce0_x, nce0_y):
    """RF differential pairs: NCE0 → HMC8410 → TFLN."""
    lines = []
    bga_half = 21
    
    for i in range(4):
        net_p = nets.get(f"RF_TX{i}_P", 0)
        net_n = nets.get(f"RF_TX{i}_N", 0)
        net_drv_p = nets.get(f"RF_DRV{i}_P", 0)
        net_drv_n = nets.get(f"RF_DRV{i}_N", 0)
        
        # NCE0 → HMC8410
        nce_rf_x = nce0_x + bga_half + 2
        nce_rf_y = nce0_y - 10 + i * 6
        hmc_x = tfln_x - 20 + i * 13
        hmc_y = tfln_y - 15
        
        # Multi-segment curved route
        mid_x = (nce_rf_x + hmc_x) / 2
        mid_y = (nce_rf_y + hmc_y) / 2
        lines.append(segment(nce_rf_x, nce_rf_y, mid_x, mid_y, 0.09, "In4.Cu", net_p))
        lines.append(segment(mid_x, mid_y, hmc_x - 3, hmc_y, 0.09, "In4.Cu", net_p))
        lines.append(segment(nce_rf_x, nce_rf_y + 0.18, mid_x, mid_y + 0.18, 0.09, "In4.Cu", net_n))
        lines.append(segment(mid_x, mid_y + 0.18, hmc_x - 3, hmc_y + 0.18, 0.09, "In4.Cu", net_n))
        
        # HMC8410 → TFLN
        tfln_rf_y = tfln_y - 5 + i * 3
        rf_layer = "In5.Cu" if i % 2 == 0 else "In28.Cu"
        lines.append(segment(hmc_x + 3, hmc_y, tfln_x - 4, tfln_rf_y, 0.15, rf_layer, net_drv_p))
        lines.append(segment(hmc_x + 3, hmc_y + 0.30, tfln_x - 4, tfln_rf_y + 0.30, 0.15, rf_layer, net_drv_n))
        
        lines.append(via(nce_rf_x, nce_rf_y, 0.3, 0.15, net_p, ("F.Cu", "In4.Cu")))
    
    return "\n".join(lines)


def generate_control_bus(nets, nce0_x, nce0_y, nce1_x, nce1_y):
    """I2C/SPI bus routing."""
    lines = []
    bga_half = 21
    nce_edge = bga_half + 2
    bmc_x, bmc_y = 50, 45
    
    i2c_sda = nets["I2C_SDA"]
    i2c_scl = nets["I2C_SCL"]
    
    # BMC → NCE0
    lines.append(segment(bmc_x + 5, bmc_y, nce0_x - nce_edge, nce0_y + nce_edge, 0.15, "In9.Cu", i2c_sda))
    lines.append(segment(bmc_x + 5, bmc_y + 1.5, nce0_x - nce_edge, nce0_y + nce_edge + 1.5, 0.15, "In9.Cu", i2c_scl))
    # NCE0 → NCE1
    lines.append(segment(nce0_x + nce_edge, nce0_y + nce_edge, nce1_x - nce_edge, nce1_y + nce_edge, 0.15, "In9.Cu", i2c_sda))
    lines.append(segment(nce0_x + nce_edge, nce0_y + nce_edge + 1.5, nce1_x - nce_edge, nce1_y + nce_edge + 1.5, 0.15, "In9.Cu", i2c_scl))
    
    lines.append(via(bmc_x + 5, bmc_y, 0.4, 0.2, i2c_sda, ("F.Cu", "In9.Cu")))
    lines.append(via(bmc_x + 5, bmc_y + 1.5, 0.4, 0.2, i2c_scl, ("F.Cu", "In9.Cu")))
    
    # SPI bus
    spi_nets = {n: nets[n] for n in ["SPI_MOSI", "SPI_MISO", "SPI_SCK", "SPI_CS"]}
    for idx, (name, nid) in enumerate(spi_nets.items()):
        lines.append(segment(bmc_x + 5, bmc_y + 4 + idx * 1.5, nce0_x - nce_edge, nce0_y + nce_edge + 4 + idx * 1.5, 0.15, "In9.Cu", nid))
        lines.append(via(bmc_x + 5, bmc_y + 4 + idx * 1.5, 0.5, 0.3, nid, ("F.Cu", "In9.Cu")))
    
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
    # COMPONENT PLACEMENT
    # ══════════════════════════════════════════════════════════════════════

    NCE0_X, NCE0_Y = 145, 160
    NCE1_X, NCE1_Y = 275, 160
    TFLN_X = (NCE0_X + NCE1_X) / 2  # 210
    TFLN_Y = NCE0_Y  # 160

    # NCE Gen3 SoCs
    L.append(fp_bga("U1", "NCE_Gen3", NCE0_X, NCE0_Y,
                     "LightRail:NCE_BGA2500_40x40mm", 0.8, 50, 50, 0.4))
    L.append(fp_bga("U4", "NCE_Gen3", NCE1_X, NCE1_Y,
                     "LightRail:NCE_BGA2500_40x40mm", 0.8, 50, 50, 0.4))

    # TFLN Photonic Module
    L.append(fp_qfn("U3", "TFLN_PIC_4xMZM", TFLN_X, TFLN_Y,
                     "LightRail:Custom_Optical_Module_25x8mm", 32, 8, 0.5, 0.25, 1.0))

    # HBM4: 8 per NCE
    for i in range(8):
        col = i % 4
        row = i // 4
        hx = NCE0_X - 30 + col * 20
        hy = NCE0_Y - 42 + row * 84
        L.append(fp_bga(f"U{30+i}", "HBM4-16GB", hx, hy,
                        "LightRail:BGA-1024_12x9mm", 0.65, 16, 16, 0.35))
    for i in range(8):
        col = i % 4
        row = i // 4
        hx = NCE1_X - 30 + col * 20
        hy = NCE1_Y - 42 + row * 84
        L.append(fp_bga(f"U{38+i}", "HBM4-16GB", hx, hy,
                        "LightRail:BGA-1024_12x9mm", 0.65, 16, 16, 0.35))

    # HMC8410 RF Drivers
    for i in range(4):
        rx = TFLN_X - 20 + i * 13
        ry = TFLN_Y - 15
        L.append(fp_qfn(f"U{50+i}", "HMC8410", rx, ry,
                        "Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.1x3.1mm",
                        32, 5, 0.5, 0.25, 0.8, 3.1))

    # VRM Controllers
    vrm_positions = [(30, 100), (30, 220), (390, 100), (390, 220)]
    for i, (vx, vy) in enumerate(vrm_positions):
        L.append(fp_qfn(f"U{200+i}", "ISL69260", vx, vy,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # DrMOS
    for i in range(24):
        side = 0 if i < 12 else 1
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

    # LDO regulators
    for i in range(4):
        lx = TFLN_X - 15 + i * 10
        ly = TFLN_Y + 15
        L.append(fp_sot23(f"U{240+i}", "ADP7118-0.9V", lx, ly))

    # Jitter Cleaners
    for i in range(2):
        jx = 170 + i * 80
        jy = 30
        L.append(fp_qfn(f"U{250+i}", "Si5395A", jx, jy,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # Retimers
    for i in range(4):
        rtx = 130 + i * 50
        rty = 290
        L.append(fp_qfn(f"U{260+i}", "BCM84881", rtx, rty,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # PCIe Switches
    for i in range(4):
        psx = 130 + i * 50
        psy = 310
        L.append(fp_qfn(f"U{270+i}", "PEX88096", psx, psy,
                        "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                        48, 7, 0.5, 0.25, 0.8, 5.6))

    # BMC
    L.append(fp_qfn("U380", "AST2600", 50, 45,
                     "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
                     48, 7, 0.5, 0.25, 0.8, 5.6))

    # PCIe x16 Slots
    slot_positions = [60, 165, 270, 375]
    for i in range(4):
        sx = slot_positions[i]
        sy = 343
        L.append(fp_pcie_x16(f"J{20+i}", sx, sy))

    # Decoupling Caps
    rails = ["+0V8"]*4 + ["+1V8"]*4 + ["+3V3"]*4 + ["+0V9"]*4
    for i in range(16):
        col = i % 4
        row = i // 4
        cx = 185 + col * 5.0
        cy = NCE0_Y - 20 + row * 4.0
        rail_name = rails[i]
        L.append(fp_cap_0402(f"C{i+1}", "100nF", cx, cy,
                             net1_id=nets[rail_name], net1_name=rail_name,
                             net2_id=nets["GND"], net2_name="GND"))

    # Mounting Holes
    mh_positions = [(8, 8), (412, 8), (8, 320), (412, 320),
                    (100, 60), (320, 60), (100, 265), (320, 265)]
    for i, (mx, my) in enumerate(mh_positions):
        L.append(fp_mounting_hole(f"MH{i+1}", mx, my))

    # Fiducials
    for i, (fx, fy) in enumerate([(15, 15), (405, 15), (15, 335), (405, 335)]):
        L.append(fp_fiducial(f"FID{i+1}", fx, fy))

    # ══════════════════════════════════════════════════════════════════════
    # ZONE POURS - Power distribution planes
    # ══════════════════════════════════════════════════════════════════════

    inner_pts = [(0, 0), (420, 0), (420, 330), (0, 330)]
    for gnd_layer in ["In3.Cu", "In6.Cu", "In12.Cu", "In14.Cu", "In16.Cu",
                      "In18.Cu", "In21.Cu", "In24.Cu", "In27.Cu", "In30.Cu", "B.Cu"]:
        L.append(zone_pour("GND", nets["GND"], gnd_layer, inner_pts, priority=0))

    # V_CORE planes
    vcore_pts = [(40, 70), (380, 70), (380, 270), (40, 270)]
    for pwr_layer in ["In10.Cu", "In11.Cu", "In19.Cu", "In20.Cu"]:
        L.append(zone_pour("+0V8", nets["+0V8"], pwr_layer, vcore_pts, priority=1))

    # +12V plane
    L.append(zone_pour("+12V", nets["+12V"], "In13.Cu", [(0, 0), (420, 0), (420, 60), (0, 60)], priority=1))
    # +3V3 plane
    L.append(zone_pour("+3V3", nets["+3V3"], "In15.Cu", [(0, 0), (80, 0), (80, 350), (0, 350)], priority=1))
    # +1V8 plane
    L.append(zone_pour("+1V8", nets["+1V8"], "In15.Cu", [(340, 0), (420, 0), (420, 350), (340, 350)], priority=1))

    # F.Cu ground pour (split around BGAs)
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(0, 0), (NCE0_X - 22, 0), (NCE0_X - 22, 330), (0, 330)], priority=0))
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(NCE1_X + 22, 0), (420, 0), (420, 330), (NCE1_X + 22, 330)], priority=0))
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(NCE0_X - 22, 0), (NCE1_X + 22, 0), (NCE1_X + 22, NCE0_Y - 22),
         (NCE0_X - 22, NCE0_Y - 22)], priority=0))
    L.append(zone_pour("GND", nets["GND"], "F.Cu",
        [(NCE0_X - 22, NCE0_Y + 22), (NCE1_X + 22, NCE0_Y + 22),
         (NCE1_X + 22, 330), (NCE0_X - 22, 330)], priority=0))

    # ══════════════════════════════════════════════════════════════════════
    # DENSE SIGNAL ROUTING
    # ══════════════════════════════════════════════════════════════════════

    # BGA breakout routing (120 traces per NCE, curved fanout)
    L.append(generate_bga_breakout(NCE0_X, NCE0_Y, 0, nets))
    L.append(generate_bga_breakout(NCE1_X, NCE1_Y, 1, nets))

    # HBM differential pair routing (64 diff pairs per NCE = 256 traces per NCE)
    L.append(generate_hbm_routing(NCE0_X, NCE0_Y, 0, nets))
    L.append(generate_hbm_routing(NCE1_X, NCE1_Y, 1, nets))

    # TFLN vertical differential routing (blue traces in center)
    L.append(generate_tfln_routing(TFLN_X, TFLN_Y, NCE0_X, NCE1_X, nets))

    # RF differential pairs
    L.append(generate_rf_routing(nets, TFLN_X, TFLN_Y, NCE0_X, NCE0_Y))

    # DrMOS power routing (parallel traces from edges)
    L.append(generate_drmos_routing(vrm_positions, nets))

    # PCIe lane routing (16 diff pairs per switch × 4 switches)
    L.append(generate_pcie_routing(nets, slot_positions))

    # Clock distribution
    L.append(generate_clock_routing(nets))

    # Control buses (I2C/SPI)
    L.append(generate_control_bus(nets, NCE0_X, NCE0_Y, NCE1_X, NCE1_Y))

    # B.Cu edge routing (blue traces along edges)
    L.append(generate_bcu_edge_routing(nets))

    # Via stitching arrays
    L.append(generate_via_stitching(nets))

    # Decoupling cap connections
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
        L.append(via(cx - 1.8, cy, 0.5, 0.3, rail_net))
        L.append(via(cx + 1.8, cy, 0.5, 0.3, gnd_net))

    # 12V input to VRMs
    v12_net = nets["+12V"]
    for vx, vy in vrm_positions:
        L.append(via(vx, 5, 0.8, 0.4, v12_net, ("F.Cu", "In13.Cu")))
        L.append(segment(vx, 5, vx, vy - 10, 1.0, "In13.Cu", v12_net))
        L.append(via(vx, vy - 10, 0.8, 0.4, v12_net, ("In13.Cu", "F.Cu")))

    # ══════════════════════════════════════════════════════════════════════
    # DESIGN ANNOTATIONS
    # ══════════════════════════════════════════════════════════════════════

    # NCE substrate regions (green in reference)
    for nce_x, nce_y, label in [(NCE0_X, NCE0_Y, "NCE"),
                                  (NCE1_X, NCE1_Y, "NCE")]:
        L.append(f'  (gr_rect (start {nce_x-30} {nce_y-35}) (end {nce_x+30} {nce_y+35}) (layer "Eco1.User") (width 0.5) (fill solid) (tstamp "{uid()}"))')
        L.append(f'  (gr_text "{label}" (at {nce_x} {nce_y}) (layer "Cmts.User") (effects (font (size 4 4) (thickness 0.5)))  (tstamp "{uid()}"))')

    # TFLN region (magenta/pink in reference)
    L.append(f'  (gr_rect (start {TFLN_X-13} {TFLN_Y-25}) (end {TFLN_X+13} {TFLN_Y+25}) (layer "Eco2.User") (width 0.3) (fill solid) (tstamp "{uid()}"))')

    # T/N labels (visible in reference)
    L.append(f'  (gr_text "T/N" (at {NCE0_X - 35} {NCE0_Y}) (layer "F.SilkS") (effects (font (size 3 3) (thickness 0.3)))  (tstamp "{uid()}"))')
    L.append(f'  (gr_text "T/LTN" (at {NCE1_X + 35} {NCE1_Y}) (layer "F.SilkS") (effects (font (size 3 3) (thickness 0.3)))  (tstamp "{uid()}"))')

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
    print(f"Generated {path}")
    print(f"Footprints: {fps}  Segments: {segs}  Vias: {vias}  Zones: {zones}")


if __name__ == "__main__":
    main()

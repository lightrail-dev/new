#!/usr/bin/env python3
"""
Rebuild LightRail LPO 1.6T PCB with production-quality footprints.

All standard IC footprints use exact pad coordinates from KiCad official library.
Custom photonic footprints are in LightRail.pretty.
"""

import os

REPO = "/home/ubuntu/new"
PCB_PATH = os.path.join(REPO, "LightRail_LPO_1.6T.kicad_pcb")
LIB_DIR = os.path.join(REPO, "LightRail.pretty")
FP_LIB_TABLE = os.path.join(REPO, "fp-lib-table")

BW, BH = 168.0, 100.0
TAB_W, TAB_H = 89.0, 5.0
TAB_X0 = (BW - TAB_W) / 2.0
TAB_X1 = TAB_X0 + TAB_W

LAYERS_SMD = '"F.Cu" "F.Paste" "F.Mask"'
LAYERS_SMD_NOPASTE = '"F.Cu" "F.Mask"'
LAYERS_TH = '"*.Cu" "*.Mask"'
LAYERS_BCU = '"B.Cu" "B.Mask"'
LAYERS_PASTE = '"F.Paste"'


def net(nid, nname):
    return f'(net {nid} "{nname}")'


def fmtf(v):
    """Format float without trailing zeros."""
    return f"{v:.4f}".rstrip("0").rstrip(".")


def pad_smd_rr(num, x, y, w, h, rratio, net_str=""):
    ns = f" {net_str}" if net_str else ""
    return f'    (pad "{num}" smd roundrect (at {fmtf(x)} {fmtf(y)}) (size {w} {h}) (layers {LAYERS_SMD}) (roundrect_rratio {rratio}){ns})'


def pad_smd_rect(num, x, y, w, h, layers, net_str=""):
    ns = f" {net_str}" if net_str else ""
    return f'    (pad "{num}" smd rect (at {x} {y}) (size {w} {h}) (layers {layers}){ns})'


def pad_smd_circle(num, x, y, d, net_str=""):
    ns = f" {net_str}" if net_str else ""
    return f'    (pad "{num}" smd circle (at {fmtf(x)} {fmtf(y)}) (size {d} {d}) (layers {LAYERS_SMD}){ns})'


def pad_paste_rr(x, y, w, h, rratio):
    return f'    (pad "" smd roundrect (at {x} {y}) (size {w} {h}) (layers {LAYERS_PASTE}) (roundrect_rratio {rratio}))'


def fp_line(x0, y0, x1, y1, layer, width):
    return f'    (fp_line (start {x0} {y0}) (end {x1} {y1}) (layer "{layer}") (width {width}))'


def box_lines(hw, hh, layer, width):
    return [
        fp_line(-hw, -hh, hw, -hh, layer, width),
        fp_line(hw, -hh, hw, hh, layer, width),
        fp_line(hw, hh, -hw, hh, layer, width),
        fp_line(-hw, hh, -hw, -hh, layer, width),
    ]


def ref_text(ref, y_off):
    return f'    (fp_text reference "{ref}" (at 0 {y_off}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))'


def val_text(val, y_off):
    return f'    (fp_text value "{val}" (at 0 {y_off}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))'


def user_text(sz=1):
    return f'    (fp_text user "%R" (at 0 0) (layer "F.Fab") (effects (font (size {sz} {sz}) (thickness {sz*0.15:.2f}))))'


def create_custom_footprints():
    os.makedirs(LIB_DIR, exist_ok=True)

    # BGA-196 for TFLN Modulator
    with open(os.path.join(LIB_DIR, 'BGA-196_15x15mm_P1.0mm.kicad_mod'), 'w') as f:
        f.write('(module BGA-196_15x15mm_P1.0mm (layer F.Cu) (tedit 0)\n')
        f.write('  (descr "BGA-196, 14x14, 1.0mm pitch, 15x15mm body, TFLN Modulator")\n')
        f.write('  (tags "BGA 196")\n  (attr smd)\n')
        f.write('  (fp_text reference REF** (at 0 -9) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))\n')
        f.write('  (fp_text value BGA-196_15x15mm_P1.0mm (at 0 9) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n')
        for lyr, w, sz in [("F.Fab", 0.1, 7.5), ("F.CrtYd", 0.05, 8.5)]:
            for s0, s1 in [((-sz,-sz),(sz,-sz)),((sz,-sz),(sz,sz)),((sz,sz),(-sz,sz)),((-sz,sz),(-sz,-sz))]:
                f.write(f'  (fp_line (start {s0[0]} {s0[1]}) (end {s1[0]} {s1[1]}) (layer {lyr}) (width {w}))\n')
        f.write('  (fp_circle (center -7 -7) (end -6.5 -7) (layer F.SilkS) (width 0.12))\n')
        letters = "ABCDEFGHJKLMNP"
        for r in range(14):
            for c in range(14):
                f.write(f'  (pad "{letters[r]}{c+1}" smd circle (at {-6.5+c} {-6.5+r}) (size 0.5 0.5) (layers F.Cu F.Mask F.Paste))\n')
        f.write('  (fp_text user %R (at 0 0) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n)\n')

    # COB-Photonic for DFB Laser
    with open(os.path.join(LIB_DIR, 'COB-Photonic_14x10mm.kicad_mod'), 'w') as f:
        f.write('(module COB-Photonic_14x10mm (layer F.Cu) (tedit 0)\n')
        f.write('  (descr "Chip-on-Board Photonic, 14x10mm, 22 pins, DFB Laser")\n')
        f.write('  (tags "COB photonic laser")\n  (attr smd)\n')
        f.write('  (fp_text reference REF** (at 0 -7) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))\n')
        f.write('  (fp_text value COB-Photonic_14x10mm (at 0 7) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n')
        for lyr, w, hw, hh in [("F.Fab", 0.1, 7, 5), ("F.CrtYd", 0.05, 8, 6)]:
            for s0, s1 in [((-hw,-hh),(hw,-hh)),((hw,-hh),(hw,hh)),((hw,hh),(-hw,hh)),((-hw,hh),(-hw,-hh))]:
                f.write(f'  (fp_line (start {s0[0]} {s0[1]}) (end {s1[0]} {s1[1]}) (layer {lyr}) (width {w}))\n')
        for i in range(11):
            f.write(f'  (pad "{i+1}" smd roundrect (at -6.5 {-4.5+i*0.9:.1f}) (size 1.6 0.5) (layers F.Cu F.Mask F.Paste) (roundrect_rratio 0.25))\n')
        for i in range(11):
            f.write(f'  (pad "{i+12}" smd roundrect (at 6.5 {-4.5+i*0.9:.1f}) (size 1.6 0.5) (layers F.Cu F.Mask F.Paste) (roundrect_rratio 0.25))\n')
        f.write('  (fp_text user %R (at 0 0) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n)\n')

    # MPO-24 Receptacle
    with open(os.path.join(LIB_DIR, 'MPO-24_Receptacle.kicad_mod'), 'w') as f:
        f.write('(module MPO-24_Receptacle (layer F.Cu) (tedit 0)\n')
        f.write('  (descr "MPO-24 Fiber Optic Receptacle")\n')
        f.write('  (tags "MPO fiber optic")\n  (attr through_hole)\n')
        f.write('  (fp_text reference REF** (at 0 -8) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))\n')
        f.write('  (fp_text value MPO-24_Receptacle (at 0 8) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n')
        for lyr, w, hw, hh in [("F.Fab", 0.1, 9, 5), ("F.CrtYd", 0.05, 10, 6)]:
            for s0, s1 in [((-hw,-hh),(hw,-hh)),((hw,-hh),(hw,hh)),((hw,hh),(-hw,hh)),((-hw,hh),(-hw,-hh))]:
                f.write(f'  (fp_line (start {s0[0]} {s0[1]}) (end {s1[0]} {s1[1]}) (layer {lyr}) (width {w}))\n')
        f.write('  (pad "" thru_hole circle (at -7 0) (size 2.0 2.0) (drill 1.5) (layers *.Cu *.Mask))\n')
        f.write('  (pad "" thru_hole circle (at 7 0) (size 2.0 2.0) (drill 1.5) (layers *.Cu *.Mask))\n')
        for i in range(12):
            f.write(f'  (pad "{i+1}" smd roundrect (at {-4.125+i*0.75:.3f} -2.5) (size 0.5 1.2) (layers F.Cu F.Mask F.Paste) (roundrect_rratio 0.25))\n')
        for i in range(12):
            f.write(f'  (pad "{i+13}" smd roundrect (at {-4.125+i*0.75:.3f} 2.5) (size 0.5 1.2) (layers F.Cu F.Mask F.Paste) (roundrect_rratio 0.25))\n')
        f.write('  (fp_text user %R (at 0 0) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n)\n')

    # PCIe x16 Edge Connector
    with open(os.path.join(LIB_DIR, 'PCIe_x16_EdgeConnector.kicad_mod'), 'w') as f:
        f.write('(module PCIe_x16_EdgeConnector (layer F.Cu) (tedit 0)\n')
        f.write('  (descr "PCIe x16 Edge Connector, 164 pins")\n')
        f.write('  (tags "PCIe edge connector")\n  (attr smd)\n')
        f.write('  (fp_text reference REF** (at 0 -5) (layer F.SilkS) (effects (font (size 1 1) (thickness 0.15))))\n')
        f.write('  (fp_text value PCIe_x16_EdgeConnector (at 0 5) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n')
        hw = TAB_W / 2.0
        for s0, s1 in [((-hw,-2),(hw,-2)),((hw,-2),(hw,2)),((hw,2),(-hw,2)),((-hw,2),(-hw,-2))]:
            f.write(f'  (fp_line (start {s0[0]} {s0[1]}) (end {s1[0]} {s1[1]}) (layer F.Fab) (width 0.1))\n')
        for s0, s1 in [((-hw-1,-3),(hw+1,-3)),((hw+1,-3),(hw+1,3)),((hw+1,3),(-hw-1,3)),((-hw-1,3),(-hw-1,-3))]:
            f.write(f'  (fp_line (start {s0[0]} {s0[1]}) (end {s1[0]} {s1[1]}) (layer F.CrtYd) (width 0.05))\n')
        for i in range(82):
            px = -40.5 + i
            f.write(f'  (pad "A{i+1}" smd rect (at {px} -0.75) (size 0.6 2.0) (layers F.Cu F.Mask))\n')
            f.write(f'  (pad "B{i+1}" smd rect (at {px} 0.75) (size 0.6 2.0) (layers B.Cu B.Mask))\n')
        f.write('  (fp_text user %R (at 0 0) (layer F.Fab) (effects (font (size 1 1) (thickness 0.15))))\n)\n')

    print("Created custom footprint library")


def create_fp_lib_table():
    with open(FP_LIB_TABLE, 'w') as f:
        f.write('(fp_lib_table\n')
        f.write('  (lib (name "LightRail") (type "KiCad") (uri "${KIPRJMOD}/LightRail.pretty") (options "") (descr "LightRail LPO 1.6T custom footprints"))\n')
        f.write(')\n')
    print(f"Created {FP_LIB_TABLE}")

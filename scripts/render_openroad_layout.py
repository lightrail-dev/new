#!/usr/bin/env python3
"""
Render a genuine GDS-II layout image from OpenROAD P&R results.
Uses KLayout's LEF/DEF reader to load the placed-and-routed design
with sky130 standard cell library, then exports GDS and renders PNG.
"""

import os
import sys
import shutil

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'synth', 'openroad_flow', 'results')
PLATFORM_DIR = '/home/ubuntu/orfs/flow/platforms/sky130hd'
DEF_FILE = os.path.join(RESULTS_DIR, 'nce_top_final.def')
TECH_LEF = os.path.join(PLATFORM_DIR, 'lef', 'sky130_fd_sc_hd.tlef')
SC_LEF = os.path.join(PLATFORM_DIR, 'lef', 'sky130_fd_sc_hd_merged.lef')
SC_GDS = os.path.join(PLATFORM_DIR, 'gds', 'sky130_fd_sc_hd.gds')
LYP_FILE = os.path.join(PLATFORM_DIR, 'sky130hd.lyp')

OUTPUT_GDS = os.path.join(RESULTS_DIR, 'nce_top_final.gds')
OUTPUT_PNG = '/home/ubuntu/Downloads/nce_top_openroad_layout.png'
OUTPUT_GDS_COPY = '/home/ubuntu/Downloads/nce_top_openroad_layout.gds'


def render_layout():
    import klayout.db as db
    import klayout.lay as lay

    print("Loading DEF with LEF tech using KLayout LEF/DEF reader...")

    layout = db.Layout()

    # Configure LEF/DEF reader
    lo = db.LoadLayoutOptions()
    lc = lo.lefdef_config

    # Tell KLayout where to find the LEF files for cell definitions
    lc.lef_files = [TECH_LEF, SC_LEF]
    lc.read_lef_with_def = True
    lc.produce_routing = True
    lc.produce_special_routing = True
    lc.produce_via_geometry = True
    lc.produce_pins = True
    lc.produce_lef_pins = True
    lc.produce_fills = True
    lc.produce_blockages = True
    lc.produce_obstructions = True
    lc.produce_labels = True
    lc.produce_cell_outlines = True
    lc.macro_layout_files = [SC_GDS]

    # Read DEF (will also read the LEF files configured above)
    layout.read(DEF_FILE, lo)

    print(f"Loaded: {layout.cells()} cells")

    top = layout.top_cell()
    if top is None:
        for ci in range(layout.cells()):
            c = layout.cell(ci)
            if c.name == 'nce_top':
                top = c
                break

    if top is None:
        print("ERROR: Could not find top cell")
        sys.exit(1)

    print(f"Top cell: {top.name}")
    print(f"Bounding box: {top.bbox()}")

    # Write GDS
    layout.write(OUTPUT_GDS)
    print(f"GDS written: {OUTPUT_GDS} ({os.path.getsize(OUTPUT_GDS) / 1e6:.1f} MB)")

    # Copy to Downloads
    os.makedirs('/home/ubuntu/Downloads', exist_ok=True)
    shutil.copy2(OUTPUT_GDS, OUTPUT_GDS_COPY)
    print(f"GDS copied: {OUTPUT_GDS_COPY}")

    # Render image using LayoutView
    print("Rendering layout image...")
    lv = lay.LayoutView()
    cv = lv.cellview(lv.load_layout(OUTPUT_GDS, 0))
    lv.max_hier()

    # Try to load the sky130 layer properties file for correct colors
    if os.path.exists(LYP_FILE):
        try:
            lv.load_layer_props(LYP_FILE)
            print(f"Loaded layer properties: {LYP_FILE}")
        except Exception as e:
            print(f"Could not load .lyp file: {e}")

    # Zoom to full design
    lv.zoom_fit()

    # Export high-res image
    bbox = top.bbox()
    w = 4096
    h = int(w * bbox.height() / bbox.width()) if bbox.width() > 0 else 4096
    h = max(h, 1)

    lv.save_image(OUTPUT_PNG, w, h)
    print(f"PNG rendered: {OUTPUT_PNG} ({w}x{h})")


def render_from_def_fallback():
    """Fallback renderer using PIL to parse DEF directly."""
    import re
    from PIL import Image, ImageDraw

    print("Fallback: Rendering from DEF with PIL...")

    with open(DEF_FILE, 'r') as f:
        lines = f.readlines()

    # Parse die area
    die_x1, die_y1, die_x2, die_y2 = 0, 0, 800000, 800000
    for line in lines:
        m = re.match(r'DIEAREA\s*\(\s*(\d+)\s+(\d+)\s*\)\s*\(\s*(\d+)\s+(\d+)\s*\)', line)
        if m:
            die_x1, die_y1, die_x2, die_y2 = [int(x) for x in m.groups()]
            break

    die_w = die_x2 - die_x1
    die_h = die_y2 - die_y1
    img_w = 4096
    img_h = int(img_w * die_h / die_w) if die_w > 0 else 4096
    scale = img_w / die_w

    def to_px(x, y):
        return int((x - die_x1) * scale), img_h - int((y - die_y1) * scale)

    img = Image.new('RGB', (img_w, img_h), (10, 10, 25))
    draw = ImageDraw.Draw(img)

    # Parse and draw components
    cell_h = 2720
    section = None
    comp_count = 0
    net_seg_count = 0
    current_layer = None
    last_x, last_y = None, None

    cell_colors = {
        'clkbuf': (50, 180, 50), 'dfxtp': (50, 50, 180), 'buf_': (50, 150, 50),
        'inv_': (60, 140, 60), 'nand': (180, 50, 50), 'nor': (180, 80, 30),
        'and': (160, 50, 50), 'or_': (160, 80, 30), 'xor': (150, 50, 150),
        'xnor': (130, 50, 130), 'mux': (50, 150, 150), 'conb': (180, 180, 50),
        'fill_': (20, 20, 35), 'tap': (18, 18, 30), 'a2': (120, 70, 70),
        'o2': (120, 90, 50),
    }

    wire_colors = {
        'met1': (200, 40, 40), 'met2': (40, 80, 220), 'met3': (40, 180, 40),
        'met4': (200, 120, 20), 'met5': (200, 40, 200),
    }

    def cell_color(name):
        n = name.lower()
        for k, c in cell_colors.items():
            if k in n:
                return c
        return (90, 90, 110)

    def cell_width(name):
        if '_16' in name: return 7360
        if '_8' in name and 'fill' not in name: return 4600
        if '_4' in name and 'fill' not in name: return 2760
        if '_2' in name and 'fill' not in name: return 1840
        if 'fill_8' in name: return 3680
        if 'fill_4' in name: return 1840
        if 'fill_2' in name: return 920
        if 'fill_1' in name: return 460
        return 1380

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('COMPONENTS '):
            section = 'COMP'
            continue
        elif stripped == 'END COMPONENTS':
            section = None
            continue
        elif stripped.startswith('SPECIALNETS '):
            section = 'SNET'
            continue
        elif stripped == 'END SPECIALNETS':
            section = None
            continue
        elif re.match(r'^NETS \d+', stripped):
            section = 'NET'
            continue
        elif stripped == 'END NETS':
            section = None
            continue

        if section == 'COMP':
            m = re.search(r'-\s+\S+\s+(\S+).*?\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)', stripped)
            if m:
                cell, x, y = m.group(1), int(m.group(2)), int(m.group(3))
                w = cell_width(cell)
                px1, py1 = to_px(x, y + cell_h)
                px2, py2 = to_px(x + w, y)
                draw.rectangle([px1, py1, px2, py2], fill=cell_color(cell))
                comp_count += 1

        elif section in ('SNET', 'NET'):
            # Track current layer from ROUTED/NEW keywords
            layer_m = re.search(r'(?:ROUTED|NEW)\s+(\w+)', stripped)
            if layer_m:
                current_layer = layer_m.group(1).lower()
                last_x, last_y = None, None

            # Parse RECT for special nets
            for rm in re.finditer(r'RECT\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)\s*\(\s*(-?\d+)\s+(-?\d+)\s*\)', stripped):
                rx1, ry1, rx2, ry2 = [int(v) for v in rm.groups()]
                px1, py1 = to_px(rx1, max(ry1, ry2))
                px2, py2 = to_px(rx2, min(ry1, ry2))
                color = wire_colors.get(current_layer, (100, 100, 100))
                draw.rectangle([px1, py1, px2, py2], fill=color)
                net_seg_count += 1

            # Parse path coordinates
            coords = re.findall(r'\(\s*(-?\d+|\*)\s+(-?\d+|\*)\s*\)', stripped)
            if coords and current_layer:
                color = wire_colors.get(current_layer, (100, 100, 100))
                for cx, cy in coords:
                    if cx == '*':
                        cx = last_x if last_x is not None else 0
                    else:
                        cx = int(cx)
                    if cy == '*':
                        cy = last_y if last_y is not None else 0
                    else:
                        cy = int(cy)

                    if last_x is not None and last_y is not None:
                        px1, py1 = to_px(last_x, last_y)
                        px2, py2 = to_px(cx, cy)
                        draw.line([px1, py1, px2, py2], fill=color, width=1)
                        net_seg_count += 1

                    last_x, last_y = cx, cy

    # Die outline
    px1, py1 = to_px(die_x1, die_y2)
    px2, py2 = to_px(die_x2, die_y1)
    draw.rectangle([px1, py1, px2, py2], outline=(80, 80, 180), width=3)

    print(f"Drew {comp_count} components, {net_seg_count} wire segments")

    os.makedirs('/home/ubuntu/Downloads', exist_ok=True)
    img.save(OUTPUT_PNG, 'PNG')
    print(f"PNG saved: {OUTPUT_PNG} ({img_w}x{img_h})")


if __name__ == '__main__':
    os.makedirs('/home/ubuntu/Downloads', exist_ok=True)

    try:
        render_layout()
    except Exception as e:
        print(f"KLayout rendering failed: {e}")
        print("Trying fallback...")
        render_from_def_fallback()

    print("\nDone!")

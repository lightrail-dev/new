#!/usr/bin/env python3
"""Build a real, netted KiCad 8 PCB from the schematic's netlist.json.

Uses the pcbnew Python API to:
  1. Create a 22-layer board (100 × 100 mm, 2.4 mm thick)
  2. Load real KiCad library footprints for every component
  3. Assign every pad to its schematic net (LVS-consistent)
  4. Add GND/power copper pours on the six reference planes + three power planes
  5. Set design rules + net classes
  6. Export Specctra DSN for autorouting

Run with system python:  /usr/bin/python3 build_pcb.py
"""
import json, os, sys, uuid

# pcbnew ships with the system python (3.10) on the snapshot VM
import pcbnew

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE       = os.path.dirname(os.path.abspath(__file__))
KICAD_DIR  = os.path.join(HERE, "kicad")
CUSTOM_LIB = os.path.join(KICAD_DIR, "LightRail.pretty")
NETLIST_JSON = os.path.join(HERE, "netlist.json")
OUT_PCB    = os.path.join(KICAD_DIR, "LightRail_Eval_Board.kicad_pcb")
DSN_FILE   = os.path.join(HERE, "LightRail_Eval_Board.dsn")
SYSTEM_FP  = "/usr/share/kicad/footprints"

# Board geometry (mm)
BOARD_W, BOARD_H = 100.0, 100.0
ORIGIN_X, ORIGIN_Y = 100.0, 100.0   # KiCad page origin offset
MH_INSET = 4.0

# All 22 copper layer KiCad names
CU_LAYERS = [
    "F.Cu",                                                          # L1
    "In1.Cu","In2.Cu","In3.Cu","In4.Cu","In5.Cu",                   # L2-L6
    "In6.Cu","In7.Cu","In8.Cu","In9.Cu","In10.Cu",                  # L7-L11
    "In11.Cu","In12.Cu","In13.Cu","In14.Cu","In15.Cu",              # L12-L16
    "In16.Cu","In17.Cu","In18.Cu","In19.Cu","In20.Cu",              # L17-L21
    "B.Cu",                                                          # L22
]

# GND reference planes (L3,L6,L9,L12,L15,L18 → In2,In5,In8,In11,In14,In17)
GND_PLANE_LAYERS = ["In2.Cu","In5.Cu","In8.Cu","In11.Cu","In14.Cu","In17.Cu"]
# Power planes: L11=+0.9V (In10.Cu), L17=mixed (In16.Cu), L21=mixed (In20.Cu)
PWR_PLANE_LAYERS = {
    "In10.Cu": "+0V9",
    "In16.Cu": "+1V8",
    "In20.Cu": "+3V3",
}

# ---------------------------------------------------------------------------
# Placement (from generate_design_files PLACEMENT, all in mm from page origin)
# ---------------------------------------------------------------------------
PLACEMENT = {
    # ICs
    "U1":  (ORIGIN_X + 40, ORIGIN_Y + 45, 0),
    "U2":  (ORIGIN_X + 60, ORIGIN_Y + 45, 0),
    "U3":  (ORIGIN_X + 50, ORIGIN_Y + 20, 0),
    "U15": (ORIGIN_X + 15, ORIGIN_Y + 80, 0),
    "U13": (ORIGIN_X + 25, ORIGIN_Y + 80, 0),
    "U11": (ORIGIN_X + 35, ORIGIN_Y + 85, 0),
    "U14": (ORIGIN_X + 35, ORIGIN_Y + 80, 0),
    "U12": (ORIGIN_X + 45, ORIGIN_Y + 85, 0),
    "U10": (ORIGIN_X + 45, ORIGIN_Y + 80, 0),
    "U20": (ORIGIN_X + 70, ORIGIN_Y + 35, 0),
    "Y1":  (ORIGIN_X + 75, ORIGIN_Y + 35, 0),
    "U21": (ORIGIN_X + 35, ORIGIN_Y + 25, 0),
    "U22": (ORIGIN_X + 85, ORIGIN_Y + 60, 0),
    "U23": (ORIGIN_X + 75, ORIGIN_Y + 50, 0),
    "U24": (ORIGIN_X + 65, ORIGIN_Y + 25, 0),
    "U25": (ORIGIN_X + 30, ORIGIN_Y + 50, 0),
    # Connectors
    "J1":  (ORIGIN_X + 5,  ORIGIN_Y + 90, 0),
    "J2":  (ORIGIN_X + 90, ORIGIN_Y + 65, 90),
    "J5":  (ORIGIN_X + 90, ORIGIN_Y + 40, 90),
    "J6":  (ORIGIN_X + 90, ORIGIN_Y + 50, 90),
    "J7":  (ORIGIN_X + 20, ORIGIN_Y + 5, 0),
    "J8":  (ORIGIN_X + 35, ORIGIN_Y + 5, 0),
    "J9":  (ORIGIN_X + 65, ORIGIN_Y + 5, 0),
    "J10": (ORIGIN_X + 80, ORIGIN_Y + 5, 0),
    "J11": (ORIGIN_X + 50, ORIGIN_Y + 5, 0),
    # Passives / misc
    "L1":  (ORIGIN_X + 15, ORIGIN_Y + 75, 0),
    "F1":  (ORIGIN_X + 10, ORIGIN_Y + 85, 0),
    "SW1": (ORIGIN_X + 85, ORIGIN_Y + 85, 0),
}

# ---------------------------------------------------------------------------
# Footprint resolution: schematic lib_id + hint → (library_path, fp_name)
# ---------------------------------------------------------------------------
FP_MAP = {
    # Passives
    ("Device:C", ""):                       ("Capacitor_SMD.pretty", "C_0402_1005Metric"),
    ("Device:C", "Capacitor_SMD:C_0402"):   ("Capacitor_SMD.pretty", "C_0402_1005Metric"),
    ("Device:C", "Capacitor_SMD:C_0603"):   ("Capacitor_SMD.pretty", "C_0603_1608Metric"),
    ("Device:C", "Capacitor_SMD:C_0805"):   ("Capacitor_SMD.pretty", "C_0805_2012Metric"),
    ("Device:C", "Capacitor_SMD:C_7343"):   ("Capacitor_Tantalum_SMD.pretty", "CP_EIA-7343-15_Kemet-W"),
    ("Device:R", ""):                       ("Resistor_SMD.pretty", "R_0402_1005Metric"),
    ("Device:R", "Resistor_SMD:R_0402"):    ("Resistor_SMD.pretty", "R_0402_1005Metric"),
    ("Device:L", ""):                       ("Inductor_SMD.pretty", "L_12x12mm_H4.5mm"),
    ("Device:L", "Inductor_SMD:L_5x5mm"):   ("Inductor_SMD.pretty", "L_12x12mm_H4.5mm"),
    ("Device:LED", ""):                     ("LED_SMD.pretty", "LED_0603_1608Metric"),
    ("Device:LED", "LED_SMD:LED_0603"):     ("LED_SMD.pretty", "LED_0603_1608Metric"),
    ("Device:Fuse", ""):                    ("Fuse.pretty", "Fuse_0805_2012Metric"),
    ("Device:Fuse", "Fuse:Fuse_0805"):      ("Fuse.pretty", "Fuse_0805_2012Metric"),
    ("Device:D_TVS", ""):                   ("Diode_SMD.pretty", "D_SOD-323"),
    ("Device:D_TVS", "Package_SOD:SOD-323"):("Diode_SMD.pretty", "D_SOD-323"),
    ("Device:Crystal_4Pin", ""):            ("Crystal.pretty", "Crystal_SMD_3225-4Pin_3.2x2.5mm"),
    ("Device:Crystal_4Pin", "Crystal:Crystal_SMD_3215-4Pin"): ("Crystal.pretty", "Crystal_SMD_3225-4Pin_3.2x2.5mm"),
    # Switch
    ("Switch:SW_Push", ""):                 ("Button_Switch_SMD.pretty", "SW_SPST_B3U-1000P"),
    ("Switch:SW_Push", "Button_Switch_SMD:Tactile_4.5x4.5mm"): ("Button_Switch_SMD.pretty", "SW_SPST_B3U-1000P"),
    # Regulators
    ("Regulator_Switching:TPS54360", ""):    ("Package_SO.pretty", "HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.3x2.3mm"),
    ("Regulator_Switching:TPS54360", "Package_SO:HSOP-8"): ("Package_SO.pretty", "HSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.3x2.3mm"),
    ("Regulator_Linear:TPS7A3301", ""):     ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    ("Regulator_Linear:TPS7A3301", "Package_TO_SOT_SMD:SOT-23-5"): ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    ("Regulator_Linear:TPS7A2018", ""):     ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    ("Regulator_Linear:TPS7A2018", "Package_TO_SOT_SMD:SOT-23-5"): ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    ("Regulator_Linear:TPS7A2010", ""):     ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    ("Regulator_Linear:TPS7A2010", "Package_TO_SOT_SMD:SOT-23-5"): ("Package_TO_SOT_SMD.pretty", "SOT-23-5"),
    ("Regulator_Linear:ADP7118", ""):       ("Package_TO_SOT_SMD.pretty", "TSOT-23-5"),
    ("Regulator_Linear:ADP7118", "Package_TO_SOT_SMD:TSOT-23-5"): ("Package_TO_SOT_SMD.pretty", "TSOT-23-5"),
    # ICs
    ("Analog_ADC:AD7928", ""):              ("Package_SO.pretty", "TSSOP-20_4.4x5mm_P0.4mm"),
    ("Analog_ADC:AD7928", "Package_SO:TSSOP-20"): ("Package_SO.pretty", "TSSOP-20_4.4x5mm_P0.4mm"),
    ("Analog_DAC:AD5684R", ""):             ("Package_SO.pretty", "TSSOP-16_4.4x5mm_P0.65mm"),
    ("Analog_DAC:AD5684R", "Package_SO:TSSOP-16"): ("Package_SO.pretty", "TSSOP-16_4.4x5mm_P0.65mm"),
    ("Clock:Si5395A", ""):                  ("Package_DFN_QFN.pretty", "QFN-28-1EP_3x6mm_P0.5mm_EP1.7x4.75mm"),
    ("Clock:Si5395A", "Package_DFN_QFN:QFN-28_5x5mm"): ("Package_DFN_QFN.pretty", "QFN-28-1EP_3x6mm_P0.5mm_EP1.7x4.75mm"),
    ("Interface_USB:FT232H", ""):           ("Package_DFN_QFN.pretty", "QFN-48-1EP_5x5mm_P0.35mm_EP3.7x3.7mm"),
    ("Interface_USB:FT232H", "Package_DFN_QFN:QFN-48_7x7mm"): ("Package_DFN_QFN.pretty", "QFN-48-1EP_5x5mm_P0.35mm_EP3.7x3.7mm"),
    ("Memory_Flash:W25Q128JVS", ""):        ("Package_SON.pretty", "WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"),
    ("Memory_Flash:W25Q128JVS", "Package_SON:WSON-8_2x3mm"): ("Package_SON.pretty", "WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"),
    ("Sensor_Temperature:TMP461", ""):      ("Package_SON.pretty", "WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"),
    ("Sensor_Temperature:TMP461", "Package_SON:WSON-8_2x2mm"): ("Package_SON.pretty", "WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"),
    # Connectors
    ("Connector:Barrel_Jack", ""):          ("Connector_BarrelJack.pretty", "BarrelJack_CUI_PJ-036AH-SMT_Horizontal"),
    ("Connector:Barrel_Jack", "Connector_BarrelJack:BarrelJack_CUI_PJ-002AH"): ("Connector_BarrelJack.pretty", "BarrelJack_CUI_PJ-036AH-SMT_Horizontal"),
    ("Connector:SMA", ""):                  ("Connector_Coaxial.pretty", "SMA_Amphenol_132289_EdgeMount"),
    ("Connector:SMA", "Connector_Coaxial:SMA_Edge"): ("Connector_Coaxial.pretty", "SMA_Amphenol_132289_EdgeMount"),
    ("Connector:JTAG_2x5", ""):             ("Connector_PinHeader_1.27mm.pretty", "PinHeader_2x05_P1.27mm_Vertical"),
    ("Connector:JTAG_2x5", "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical"): ("Connector_PinHeader_1.27mm.pretty", "PinHeader_2x05_P1.27mm_Vertical"),
    ("Connector:PinHeader_2x07", ""):       ("Connector_PinHeader_1.27mm.pretty", "PinHeader_2x07_P1.27mm_Vertical"),
    ("Connector:PinHeader_2x07", "Connector_PinHeader_1.27mm:PinHeader_2x07_P1.27mm_Vertical"): ("Connector_PinHeader_1.27mm.pretty", "PinHeader_2x07_P1.27mm_Vertical"),
    ("Connector:USB_C_16Pin", ""):          (None, "USB_C_Numeric"),  # custom
    ("Connector:USB_C_16Pin", "Connector_USB:USB_C_Receptacle_GCT_USB4110"): (None, "USB_C_Numeric"),
    ("Connector_Fiber:MPO_24", ""):         (None, "MPO-24"),         # custom
    ("Connector_Fiber:MPO_24", "Connector:MPO_24_SMT"): (None, "MPO-24"),
    # FPGA — custom numeric BGA
    ("FPGA_Xilinx:XC7A100T", ""):           (None, "BGA-256_Numeric"),
    ("FPGA_Xilinx:XC7A100T", "Package_BGA:BGA-256_14x14mm_P0.8mm"): (None, "BGA-256_Numeric"),
    # NCE — custom numeric QFN-64
    ("LightRail:NCE_QFN64", ""):            (None, "QFN-64_8x8mm_P0.4mm"),
    ("LightRail:NCE_QFN64", "Package_DFN_QFN:QFN-64_8x8mm_P0.4mm"): (None, "QFN-64_8x8mm_P0.4mm"),
    # TFLN — custom optical module
    ("LightRail:TFLN_PIC", ""):             (None, "Custom_Optical_Module"),
    ("LightRail:TFLN_PIC", "LightRail:TFLN_PIC_Module"): (None, "Custom_Optical_Module"),
}

MM = pcbnew.FromMM  # 1 mm in KiCad internal units (nanometers)

def pos(x_mm, y_mm):
    return pcbnew.VECTOR2I(int(MM(x_mm)), int(MM(y_mm)))

# ---------------------------------------------------------------------------
# Custom footprint generators (for parts that need numeric pad names)
# ---------------------------------------------------------------------------
def _make_bga256_numeric():
    """16×16 BGA, 0.8 mm pitch, numeric pads 1..256."""
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("LightRail", "BGA-256_Numeric"))
    n = 1
    for row in range(16):
        for col in range(16):
            p = pcbnew.PAD(fp)
            p.SetNumber(str(n))
            p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
            p.SetSize(pcbnew.VECTOR2I(int(MM(0.35)), int(MM(0.35))))
            p.SetLayerSet(pcbnew.PAD(fp).GetLayerSet())  # default SMD F.Cu
            lset = pcbnew.LSET()
            lset.AddLayer(pcbnew.F_Cu)
            lset.AddLayer(pcbnew.F_Mask)
            lset.AddLayer(pcbnew.F_Paste)
            p.SetLayerSet(lset)
            x = (col - 7.5) * 0.8
            y = (row - 7.5) * 0.8
            p.SetPosition(pos(x, y))
            fp.Add(p)
            n += 1
    return fp

def _make_usbc_numeric():
    """USB-C receptacle with numeric pads 1..16."""
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("LightRail", "USB_C_Numeric"))
    for i in range(1, 17):
        p = pcbnew.PAD(fp)
        p.SetNumber(str(i))
        p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetSize(pcbnew.VECTOR2I(int(MM(0.3)), int(MM(1.0))))
        lset = pcbnew.LSET()
        lset.AddLayer(pcbnew.F_Cu)
        lset.AddLayer(pcbnew.F_Mask)
        lset.AddLayer(pcbnew.F_Paste)
        p.SetLayerSet(lset)
        x = (i - 8.5) * 0.5
        p.SetPosition(pos(x, 0))
        fp.Add(p)
    return fp

CUSTOM_FP_GENERATORS = {
    "BGA-256_Numeric": _make_bga256_numeric,
    "USB_C_Numeric":   _make_usbc_numeric,
}

# ---------------------------------------------------------------------------
# Build the board
# ---------------------------------------------------------------------------
def load_netlist():
    with open(NETLIST_JSON) as f:
        return json.load(f)

def resolve_fp(lib_id, hint):
    key = (lib_id, hint)
    if key in FP_MAP:
        return FP_MAP[key]
    key0 = (lib_id, "")
    if key0 in FP_MAP:
        return FP_MAP[key0]
    return None

def build():
    netlist = load_netlist()
    board = pcbnew.BOARD()

    # --- Set copper layer count FIRST (must precede any inner-layer access) ---
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(22)

    # --- Enable all 22 copper layers ---
    enabled = pcbnew.LSET()
    for name in CU_LAYERS:
        lid = board.GetLayerID(name)
        enabled.AddLayer(lid)
    # non-copper layers
    for extra in ["F.Silkscreen","B.Silkscreen","F.Mask","B.Mask","F.Paste","B.Paste",
                   "F.Courtyard","B.Courtyard","F.Fab","B.Fab","Edge.Cuts"]:
        enabled.AddLayer(board.GetLayerID(extra))
    board.SetEnabledLayers(enabled)

    # Name the inner layers for the Intelligence Stack
    layer_names = {
        "In1.Cu":"In1.Cu (L2 Sig)",  "In2.Cu":"In2.Cu (L3 GND)",
        "In3.Cu":"In3.Cu (L4 Sig)",  "In4.Cu":"In4.Cu (L5 Sig)",
        "In5.Cu":"In5.Cu (L6 GND)",  "In6.Cu":"In6.Cu (L7 Sig)",
        "In7.Cu":"In7.Cu (L8 Sig)",  "In8.Cu":"In8.Cu (L9 GND)",
        "In9.Cu":"In9.Cu (L10 Sig)", "In10.Cu":"In10.Cu (L11 PWR 0V9)",
        "In11.Cu":"In11.Cu (L12 GND center)",
        "In12.Cu":"In12.Cu (L13 Sig)","In13.Cu":"In13.Cu (L14 Sig)",
        "In14.Cu":"In14.Cu (L15 GND)","In15.Cu":"In15.Cu (L16 Sig)",
        "In16.Cu":"In16.Cu (L17 PWR 1V8)","In17.Cu":"In17.Cu (L18 GND)",
        "In18.Cu":"In18.Cu (L19 Sig)","In19.Cu":"In19.Cu (L20 Sig)",
        "In20.Cu":"In20.Cu (L21 PWR 3V3)",
    }
    for k, v in layer_names.items():
        lid = board.GetLayerID(k)
        board.SetLayerName(lid, v)

    # --- Design rules ---
    ds.m_TrackMinWidth = int(MM(0.1))
    ds.m_ViasMinSize = int(MM(0.45))
    ds.m_ViasMinDrill = int(MM(0.2))
    ds.SetBoardThickness(int(MM(2.4)))

    # --- Create all nets ---
    all_nets = set()
    for ref, comp in netlist.items():
        for pad_num, net_name in comp["pins"].items():
            if net_name:
                all_nets.add(net_name)
    net_map = {}  # name -> NETINFO_ITEM
    for i, net_name in enumerate(sorted(all_nets), start=1):
        ni = pcbnew.NETINFO_ITEM(board, net_name, i)
        board.Add(ni)
        net_map[net_name] = ni
    print(f"Created {len(net_map)} nets")

    # --- Place footprints ---
    auto_x, auto_y = ORIGIN_X + 10, ORIGIN_Y + 60
    placed = 0
    skipped = []
    for ref, comp in sorted(netlist.items()):
        lib_id = comp["lib_id"]
        hint = comp["footprint"]
        resolved = resolve_fp(lib_id, hint)
        if resolved is None:
            skipped.append((ref, lib_id, hint))
            continue

        lib_path, fp_name = resolved

        # Load or generate footprint
        if lib_path is None:
            # custom footprint: either from LightRail.pretty or generator
            if fp_name in CUSTOM_FP_GENERATORS:
                fp = CUSTOM_FP_GENERATORS[fp_name]()
            else:
                fp = pcbnew.FootprintLoad(CUSTOM_LIB, fp_name)
        else:
            full_path = os.path.join(SYSTEM_FP, lib_path)
            fp = pcbnew.FootprintLoad(full_path, fp_name)

        if fp is None:
            skipped.append((ref, lib_id, f"load failed: {lib_path}/{fp_name}"))
            continue

        fp.SetReference(ref)
        fp.SetValue(comp["value"])

        # Position
        if ref in PLACEMENT:
            px, py, rot = PLACEMENT[ref]
        else:
            px, py, rot = auto_x, auto_y, 0
            auto_x += 5
            if auto_x > ORIGIN_X + 95:
                auto_x = ORIGIN_X + 10
                auto_y += 5

        fp.SetPosition(pos(px, py))
        if rot:
            fp.SetOrientationDegrees(rot)

        # Assign pad nets
        pin_nets = comp["pins"]
        for pad in fp.Pads():
            pad_name = pad.GetNumber()
            if pad_name in pin_nets:
                net_name = pin_nets[pad_name]
                if net_name and net_name in net_map:
                    pad.SetNet(net_map[net_name])

        board.Add(fp)
        placed += 1

    print(f"Placed {placed} footprints, skipped {len(skipped)}")
    for s in skipped:
        print(f"  SKIP: {s}")

    # --- Board outline (Edge.Cuts) ---
    edge_layer = board.GetLayerID("Edge.Cuts")
    corners = [
        (ORIGIN_X, ORIGIN_Y),
        (ORIGIN_X + BOARD_W, ORIGIN_Y),
        (ORIGIN_X + BOARD_W, ORIGIN_Y + BOARD_H),
        (ORIGIN_X, ORIGIN_Y + BOARD_H),
    ]
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pos(x1, y1))
        seg.SetEnd(pos(x2, y2))
        seg.SetLayer(edge_layer)
        seg.SetWidth(int(MM(0.05)))
        board.Add(seg)

    # --- Mounting holes (4 corners) ---
    mh_positions = [
        (ORIGIN_X + MH_INSET, ORIGIN_Y + MH_INSET),
        (ORIGIN_X + BOARD_W - MH_INSET, ORIGIN_Y + MH_INSET),
        (ORIGIN_X + MH_INSET, ORIGIN_Y + BOARD_H - MH_INSET),
        (ORIGIN_X + BOARD_W - MH_INSET, ORIGIN_Y + BOARD_H - MH_INSET),
    ]
    for i, (mx, my) in enumerate(mh_positions, 1):
        try:
            mh_fp = pcbnew.FootprintLoad(
                os.path.join(SYSTEM_FP, "MountingHole.pretty"),
                "MountingHole_3.2mm_M3"
            )
            mh_fp.SetReference(f"MH{i}")
            mh_fp.SetValue("M3")
            mh_fp.SetPosition(pos(mx, my))
            board.Add(mh_fp)
        except Exception as e:
            print(f"  MH{i} skipped: {e}")

    # --- Test points (TP1..TP7 on key power rails) ---
    tp_nets = ["+12V", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "GND"]
    tp_x = ORIGIN_X + 10
    for i, net_name in enumerate(tp_nets, 1):
        try:
            tp_fp = pcbnew.FootprintLoad(
                os.path.join(SYSTEM_FP, "TestPoint.pretty"),
                "TestPoint_Pad_D1.0mm"
            )
            tp_fp.SetReference(f"TP{i}")
            tp_fp.SetValue(net_name)
            tp_fp.SetPosition(pos(tp_x + i * 4, ORIGIN_Y + 95))
            if net_name in net_map:
                for pad in tp_fp.Pads():
                    pad.SetNet(net_map[net_name])
            board.Add(tp_fp)
        except Exception as e:
            print(f"  TP{i} skipped: {e}")

    # --- Copper zones (GND on 6 reference planes + F.Cu + B.Cu) ---
    gnd_net = net_map.get("GND")
    zone_layers = GND_PLANE_LAYERS + ["F.Cu", "B.Cu"]
    for lname in zone_layers:
        lid = board.GetLayerID(lname)
        zone = pcbnew.ZONE(board)
        zone.SetNet(gnd_net)
        zone.SetLayer(lid)
        zone.SetIsRuleArea(False)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowCopperPour(False)
        outline = zone.Outline()
        outline.NewOutline()
        for cx, cy in corners:
            outline.Append(int(MM(cx)), int(MM(cy)))
        zone.SetMinThickness(int(MM(0.2)))
        zone.SetThermalReliefGap(int(MM(0.3)))
        zone.SetThermalReliefSpokeWidth(int(MM(0.4)))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        board.Add(zone)

    # --- Power plane zones ---
    for lname, pnet in PWR_PLANE_LAYERS.items():
        if pnet not in net_map:
            continue
        lid = board.GetLayerID(lname)
        zone = pcbnew.ZONE(board)
        zone.SetNet(net_map[pnet])
        zone.SetLayer(lid)
        zone.SetIsRuleArea(False)
        zone.SetDoNotAllowTracks(False)
        zone.SetDoNotAllowVias(False)
        zone.SetDoNotAllowPads(False)
        zone.SetDoNotAllowCopperPour(False)
        outline = zone.Outline()
        outline.NewOutline()
        for cx, cy in corners:
            outline.Append(int(MM(cx)), int(MM(cy)))
        zone.SetMinThickness(int(MM(0.3)))
        zone.SetThermalReliefGap(int(MM(0.3)))
        zone.SetThermalReliefSpokeWidth(int(MM(0.4)))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        zone.SetAssignedPriority(1)
        board.Add(zone)

    # NOTE: zone fill is done later via kicad-cli (ZONE_FILLER segfaults headless)
    print(f"Added {len(board.Zones())} zones (unfilled)")

    # --- Save ---
    board.Save(OUT_PCB)
    print(f"Board saved: {OUT_PCB}")

    # --- Export DSN for autorouting ---
    ok = pcbnew.ExportSpecctraDSN(board, DSN_FILE)
    if ok:
        print(f"DSN exported: {DSN_FILE}")
    else:
        print("DSN export failed!")

    return board


if __name__ == "__main__":
    build()

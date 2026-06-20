"""
LightRail Eval Board — KiCad 9 pcbnew routing script.

22-layer stackup:
  L1  F.Cu     signal
  L2  In1.Cu   signal (differential fan-out)
  L3  In2.Cu   GND plane
  L4  In3.Cu   AXI bus
  L5  In4.Cu   AXI_B bus
  L6  In5.Cu   GND plane
  L7  In6.Cu   TFLN/HBM diff pairs
  L8  In7.Cu   TFLN_B/HBM_B diff pairs
  L9  In8.Cu   GND plane
  L10 In9.Cu   CLK (100M / SERDES)
  L11 In10.Cu  PWR 0V9
  L12 In11.Cu  GND center
  L13 In12.Cu  PWR 1V8
  L14 In13.Cu  PWR 3V3
  L15 In14.Cu  GND
  L16 In15.Cu  signal
  L17 In16.Cu  signal
  L18 In17.Cu  signal
  L19 In18.Cu  signal
  L20 In19.Cu  signal
  L21 In20.Cu  GND
  L22 B.Cu     signal

Board outline: (100,75) → (300,225)  =  200 × 150 mm
"""

import sys
import os

KICAD_BIN = r"C:\Program Files\KiCad\9.0\bin"
sys.path.insert(0, os.path.join(KICAD_BIN, "Lib", "site-packages"))
os.add_dll_directory(KICAD_BIN)

import pcbnew  # noqa: E402

PCB_IN  = r"C:\Users\bolao\Downloads\DeepPCB_Extract\LightRail_Eval_Board.kicad_pcb"
PCB_OUT = r"C:\Users\bolao\Downloads\DeepPCB_Extract\LightRail_Eval_Board_Routed.kicad_pcb"
GERBER_DIR = r"C:\Users\bolao\Downloads\DeepPCB_Extract\Gerbers"

# ── helpers ──────────────────────────────────────────────────────────────────

def mm(v):
    return pcbnew.FromMM(v)

def net(board, name):
    return board.FindNet(name)

def layer_id(board, name):
    return board.GetLayerID(name)

def add_track(board, x1, y1, x2, y2, layer, width_mm, net_obj):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetLayer(layer)
    t.SetWidth(mm(width_mm))
    if net_obj:
        t.SetNet(net_obj)
    board.Add(t)
    return t

def add_via(board, x, y, drill_mm, outer_mm, net_obj, via_type=pcbnew.VIATYPE_THROUGH):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetDrillDefault()
    v.SetDrill(mm(drill_mm))
    v.SetWidth(mm(outer_mm))
    v.SetViaType(via_type)
    if net_obj:
        v.SetNet(net_obj)
    board.Add(v)
    return v

def add_zone(board, net_obj, layer, corners_mm, clearance_mm=0.2, min_width_mm=0.2):
    """corners_mm: list of (x, y) tuples (mm)."""
    z = pcbnew.ZONE(board)
    z.SetNet(net_obj)
    z.SetLayer(layer)
    z.SetLocalClearance(mm(clearance_mm))
    z.SetMinThickness(mm(min_width_mm))
    z.SetIsFilled(True)
    z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
    outline = z.Outline()
    outline.NewOutline()
    for (x, y) in corners_mm:
        outline.Append(mm(x), mm(y))
    board.Add(z)
    return z

def fill_zones(board):
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

# ── design rules ──────────────────────────────────────────────────────────────

def configure_design_rules(board):
    ds = board.GetDesignSettings()

    # KiCad 9 uses direct member assignment
    ds.m_MinClearance      = mm(0.1)
    ds.m_TrackMinWidth     = mm(0.1)
    ds.m_ViasMinSize       = mm(0.3)
    ds.m_MicroViasMinSize  = mm(0.2)
    ds.m_MicroViasMinDrill = mm(0.1)
    ds.m_ViasMinAnnularWidth = mm(0.08)

    print("  Design rules configured")

# ── stackup ──────────────────────────────────────────────────────────────────

LAYER_MAP = {
    "F.Cu":    0,
    "In1.Cu":  1,   # L2  signal
    "In2.Cu":  2,   # L3  GND
    "In3.Cu":  3,   # L4  AXI
    "In4.Cu":  4,   # L5  AXI_B
    "In5.Cu":  5,   # L6  GND
    "In6.Cu":  6,   # L7  TFLN/HBM
    "In7.Cu":  7,   # L8  TFLN_B/HBM_B
    "In8.Cu":  8,   # L9  GND
    "In9.Cu":  9,   # L10 CLK
    "In10.Cu": 10,  # L11 PWR 0V9
    "In11.Cu": 11,  # L12 GND center
    "In12.Cu": 12,  # L13 PWR 1V8
    "In13.Cu": 13,  # L14 PWR 3V3
    "In14.Cu": 14,  # L15 GND
    "In15.Cu": 15,  # L16 signal
    "In16.Cu": 16,  # L17 signal
    "In17.Cu": 17,  # L18 signal
    "In18.Cu": 18,  # L19 signal
    "In19.Cu": 19,  # L20 signal
    "In20.Cu": 20,  # L21 GND
    "B.Cu":    31,
}

# ── power planes (full-board zones) ──────────────────────────────────────────

BOARD_RECT = [(101, 76), (299, 76), (299, 224), (101, 224)]

POWER_PLANES = [
    # (net_name, layer_name, inset_mm)
    ("GND",  "In2.Cu",  0.5),   # L3
    ("GND",  "In5.Cu",  0.5),   # L6
    ("GND",  "In8.Cu",  0.5),   # L9
    ("GND",  "In11.Cu", 0.5),   # L12
    ("GND",  "In14.Cu", 0.5),   # L15
    ("GND",  "In20.Cu", 0.5),   # L21
    ("+0V9", "In10.Cu", 0.5),   # L11
    ("+1V8", "In12.Cu", 0.5),   # L13
    ("+3V3", "In13.Cu", 0.5),   # L14
]

def add_power_planes(board):
    print("  Adding power planes...")
    for net_name, layer_name, inset in POWER_PLANES:
        n = board.FindNet(net_name)
        if n is None:
            print(f"    WARNING: net {net_name!r} not found — skipping")
            continue
        lid = board.GetLayerID(layer_name)
        if lid < 0:
            print(f"    WARNING: layer {layer_name!r} not found — skipping")
            continue
        corners = [
            (BOARD_RECT[0][0]+inset, BOARD_RECT[0][1]+inset),
            (BOARD_RECT[1][0]-inset, BOARD_RECT[1][1]+inset),
            (BOARD_RECT[2][0]-inset, BOARD_RECT[2][1]-inset),
            (BOARD_RECT[3][0]+inset, BOARD_RECT[3][1]-inset),
        ]
        add_zone(board, n, lid, corners)
        print(f"    Plane: {net_name} on {layer_name}")

# ── differential pair routing ─────────────────────────────────────────────────

DP_WIDTH  = 0.12   # mm — controlled-impedance inner layer
DP_GAP    = 0.12   # mm — edge-to-edge gap within pair
VIA_D     = 0.4    # mm — via outer diameter
VIA_DR    = 0.2    # mm — via drill

def route_diff_pair(board, net_p, net_n, layer, pts_p, pts_n):
    """Route a differential pair.  pts_p/pts_n are lists of (x,y) waypoints."""
    np_ = board.FindNet(net_p)
    nn  = board.FindNet(net_n)
    if np_ is None or nn is None:
        return
    for i in range(len(pts_p)-1):
        add_track(board, pts_p[i][0], pts_p[i][1], pts_p[i+1][0], pts_p[i+1][1], layer, DP_WIDTH, np_)
        add_track(board, pts_n[i][0], pts_n[i][1], pts_n[i+1][0], pts_n[i+1][1], layer, DP_WIDTH, nn)

def add_dp_via(board, net_p, net_n, x_p, y, x_n):
    np_ = board.FindNet(net_p)
    nn  = board.FindNet(net_n)
    add_via(board, x_p, y, VIA_DR, VIA_D, np_)
    add_via(board, x_n, y, VIA_DR, VIA_D, nn)


# ── component pad helper ──────────────────────────────────────────────────────

def get_pad_pos(board, ref, pad_num):
    """Return (x_mm, y_mm) of a pad, or None."""
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            for pad in fp.Pads():
                if pad.GetNumber() == str(pad_num):
                    pos = pad.GetPosition()
                    return (pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))
    return None

def get_fp_pos(board, ref):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            pos = fp.GetPosition()
            return (pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))
    return None

# ── critical signal routing ───────────────────────────────────────────────────

def route_clocks(board):
    """Route differential clock pairs on In9.Cu (L10 CLK layer)."""
    print("  Routing clock pairs...")
    clk_layer = board.GetLayerID("In9.Cu")

    # CLK_CORE differential pair: Y1 → U1 area (approx coords)
    # Y1 at (240,145), U1 at (165,135), U4 at (235,135)
    route_diff_pair(board,
        "CLK_CORE",   "CLK_CORE_N",   clk_layer,
        [(240, 145), (240, 140), (235, 138), (230, 138)],
        [(240, 147), (240, 142), (235, 140), (230, 140)],
    )
    # CLK_SERDES differential pair: Y1 → U4 (BGA-256)
    route_diff_pair(board,
        "CLK_SERDES", "CLK_SERDES_N", clk_layer,
        [(241, 145), (241, 137), (237, 136)],
        [(241, 147), (241, 139), (237, 138)],
    )
    # CLK_HBM differential pair: Y1 → U2
    route_diff_pair(board,
        "CLK_HBM",    "CLK_HBM_N",    clk_layer,
        [(240, 145), (220, 145), (205, 158)],
        [(240, 147), (220, 147), (205, 160)],
    )
    # CLK_REF from Si5335A (U20 at 230,150) → connectors
    route_diff_pair(board,
        "CLK_REF",    "CLK_REF_N",    clk_layer,
        [(232, 150), (242, 150)],
        [(232, 152), (242, 152)],
    )

def route_tfln_optical(board):
    """Route TFLN TX differential pairs on In6.Cu (L7)."""
    print("  Routing TFLN optical pairs...")
    tfln_layer = board.GetLayerID("In6.Cu")
    tfln_b_layer = board.GetLayerID("In7.Cu")

    # U3 (MPO-24, at 200,120) → U21 TFLN PIC area (≈182,112) → U1 (165,135)
    for i in range(4):
        y_offset = i * 2.5
        # TFLN A side
        route_diff_pair(board,
            f"TFLN_TX_P{i}", f"TFLN_TX_N{i}", tfln_layer,
            [(200, 120+y_offset), (190, 118+y_offset), (183, 116+y_offset)],
            [(200, 121+y_offset), (190, 119+y_offset), (183, 117+y_offset)],
        )
        # TFLN B side
        route_diff_pair(board,
            f"TFLN_TX_P{i}_B", f"TFLN_TX_N{i}_B", tfln_b_layer,
            [(200, 120+y_offset), (210, 118+y_offset), (217, 116+y_offset)],
            [(200, 121+y_offset), (210, 119+y_offset), (217, 117+y_offset)],
        )

def route_hbm(board):
    """Route HBM data signals on In6/In7.Cu."""
    print("  Routing HBM data signals...")
    hbm_layer = board.GetLayerID("In6.Cu")
    hbm_b_layer = board.GetLayerID("In7.Cu")
    # U2 at (200,160), U4 BGA at (235,135)
    for i in range(8):
        x = 200 + i * 1.5
        add_track(board, x, 160, x, 150, hbm_layer, 0.1, board.FindNet(f"HBM_DQ{i}"))
        add_track(board, x, 150, x+35, 135, hbm_layer, 0.1, board.FindNet(f"HBM_DQ{i}"))
        # B side mirrored
        add_track(board, x, 160, x, 155, hbm_b_layer, 0.1, board.FindNet(f"HBM_DQ{i}_B"))

def route_axi_bus(board):
    """Route AXI bus on In3.Cu (L4) and In4.Cu (L5)."""
    print("  Routing AXI bus...")
    axi_layer   = board.GetLayerID("In3.Cu")
    axi_b_layer = board.GetLayerID("In4.Cu")
    # AXI: U1(165,135) → U2(200,160) — horizontal bus lanes
    axi_nets_a = [
        "AXI_ACLK","AXI_ARADDR","AXI_ARESETN","AXI_ARREADY","AXI_ARVALID",
        "AXI_AWADDR","AXI_AWREADY","AXI_AWVALID","AXI_BRESP","AXI_BVALID",
        "AXI_RDATA","AXI_RVALID","AXI_WDATA","AXI_WREADY","AXI_WVALID",
    ]
    axi_nets_b = [n+"_B" for n in axi_nets_a]
    # Lay bus on defined layer with 0.12mm tracks, 0.12mm gaps
    for idx, name in enumerate(axi_nets_a):
        n = board.FindNet(name)
        if n is None:
            continue
        y = 136 + idx * 0.25
        add_track(board, 170, y, 198, y, axi_layer, 0.12, n)
    for idx, name in enumerate(axi_nets_b):
        n = board.FindNet(name)
        if n is None:
            continue
        y = 136 + idx * 0.25
        add_track(board, 202, y, 230, y, axi_b_layer, 0.12, n)

def route_spi(board):
    """Route SPI bus on F.Cu (short traces to flash U23 at 218,168)."""
    print("  Routing SPI bus...")
    fcu = board.GetLayerID("F.Cu")
    spi = {
        "SPI_CLK":  (218, 165),
        "SPI_MOSI": (216, 165),
        "SPI_MISO": (220, 165),
        "SPI_CS_ADC": (214, 165),
        "SPI_CS_DAC": (222, 165),
    }
    # U1 at (165,135), U23 at (218,168), U21 at (182,112)
    for net_name, end in spi.items():
        n = board.FindNet(net_name)
        if n is None:
            continue
        add_track(board, 168, 138, end[0], end[1], fcu, 0.15, n)
        add_via(board, end[0], end[1], 0.2, 0.4, n)

def route_uart_usb(board):
    """Route UART and USB on F.Cu."""
    print("  Routing UART / USB...")
    fcu = board.GetLayerID("F.Cu")
    # UART: U10/U11 USB bridge area (182/162, 205) → J2 connector (258,175)
    uart = {
        "UART_TX": [(183, 205), (258, 175)],
        "UART_RX": [(183, 207), (258, 177)],
    }
    for net_name, pts in uart.items():
        n = board.FindNet(net_name)
        if n is None:
            continue
        for i in range(len(pts)-1):
            add_track(board, pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fcu, 0.15, n)

    # USB D+/D- differential pair — 90 Ω on F.Cu (0.2mm/0.2mm over GND plane In2.Cu)
    usb_layer = board.GetLayerID("F.Cu")
    route_diff_pair(board,
        "USB_DP", "USB_DN", usb_layer,
        [(183, 205), (183, 215), (180, 218)],
        [(185, 205), (185, 215), (182, 218)],
    )

def route_jtag(board):
    """Route JTAG headers on F.Cu."""
    print("  Routing JTAG...")
    fcu = board.GetLayerID("F.Cu")
    # J5 at (288,135), J6 at (288,155) — JTAG A and B
    jtag_a = {"JTAG_TCK":(285,135),"JTAG_TDI":(285,137),"JTAG_TDO":(285,139),"JTAG_TMS":(285,141)}
    jtag_b = {"JTAG_TCK_B":(285,155),"JTAG_TDI_B":(285,157),"JTAG_TDO_B":(285,159),"JTAG_TMS_B":(285,161)}
    for d in (jtag_a, jtag_b):
        for net_name, end in d.items():
            n = board.FindNet(net_name)
            if n is None:
                continue
            add_track(board, 240, end[1], end[0], end[1], fcu, 0.15, n)

def route_opt_sma(board):
    """Route OPT_RX/TX to SMA connectors on In1.Cu (L2 signal)."""
    print("  Routing optical SMA signals...")
    layer = board.GetLayerID("In1.Cu")
    # SMA connectors J7-J10 at top edge ~(160/180/220/240, 83)
    # MPO J11 at (200,83)
    sma_map = {
        "OPT_TX0": (160, 83), "OPT_TX1": (180, 83),
        "OPT_RX0": (220, 83), "OPT_RX1": (240, 83),
        "SMA_J7":  (160, 83), "SMA_J8":  (180, 83),
        "SMA_J9":  (220, 83), "SMA_J10": (240, 83),
    }
    for net_name, end in sma_map.items():
        n = board.FindNet(net_name)
        if n is None:
            continue
        add_track(board, 200, 100, end[0], end[1], layer, 0.12, n)

def route_power_traces(board):
    """Heavy power traces on F.Cu and B.Cu; decoupling connections."""
    print("  Routing power distribution traces...")
    fcu = board.GetLayerID("F.Cu")
    bcu = board.GetLayerID("B.Cu")

    # 12V input: J1(110,210) → L1 inductor(138,212) → U15 TPS54560(132,205)
    v12 = board.FindNet("+12V_RAW")
    v12_reg = board.FindNet("+12V")
    if v12:
        add_track(board, 110, 210, 125, 210, fcu, 0.8, v12)
        add_track(board, 125, 210, 132, 210, fcu, 0.8, v12)
    if v12_reg:
        add_track(board, 132, 205, 165, 135, fcu, 0.5, v12_reg)

    # 5V rail: U15 → spread
    v5 = board.FindNet("+5V")
    if v5:
        add_track(board, 132, 205, 160, 200, fcu, 0.4, v5)
        add_track(board, 160, 200, 200, 200, fcu, 0.4, v5)

    # 3V3 rail: U14 TPS7A2010 → decoupling caps and U1
    v33 = board.FindNet("+3V3")
    if v33:
        add_track(board, 172, 205, 172, 168, fcu, 0.3, v33)
        add_track(board, 172, 168, 165, 138, fcu, 0.3, v33)

    # 1V8 rail: U13 TPS7A33D1(152,205) → U1 and analog ICs
    v18 = board.FindNet("+1V8")
    if v18:
        add_track(board, 152, 205, 152, 168, fcu, 0.3, v18)
        add_track(board, 152, 168, 165, 137, fcu, 0.3, v18)

    # 1V0 rail: U1D ADB311B(182,205) → U4 BGA core
    v10 = board.FindNet("+1V0")
    if v10:
        add_track(board, 182, 205, 220, 205, fcu, 0.3, v10)
        add_track(board, 220, 205, 235, 140, fcu, 0.3, v10)

    # 0V9 rail: U22 at (245,175) → NCE chip U1/U4
    v09 = board.FindNet("+0V9")
    if v09:
        add_track(board, 245, 175, 245, 140, fcu, 0.3, v09)
        add_track(board, 245, 140, 235, 137, fcu, 0.3, v09)

def route_i2c_gpio(board):
    """Route I2C (U25 TMP461, U20 Si5335A) and GPIO on F.Cu."""
    print("  Routing I2C / GPIO...")
    fcu = board.GetLayerID("F.Cu")
    # I2C: U1(165,135) → U25(158,150) → U20(230,150) → J6 GPIO (288,155)
    i2c_scl = board.FindNet("I2C_SCL")
    i2c_sda = board.FindNet("I2C_SDA")
    if i2c_scl:
        add_track(board, 165, 137, 158, 150, fcu, 0.15, i2c_scl)
        add_track(board, 158, 150, 230, 150, fcu, 0.15, i2c_scl)
        add_track(board, 230, 150, 288, 155, fcu, 0.15, i2c_scl)
    if i2c_sda:
        add_track(board, 165, 138, 158, 151, fcu, 0.15, i2c_sda)
        add_track(board, 158, 151, 230, 151, fcu, 0.15, i2c_sda)
        add_track(board, 230, 151, 288, 157, fcu, 0.15, i2c_sda)

    # GPIO: U1 → J5 (288,135)
    gpio_nets = ["FPGA_GPIO0","FPGA_GPIO1","FPGA_GPIO2","FPGA_GPIO3"]
    for i, gname in enumerate(gpio_nets):
        n = board.FindNet(gname)
        if n:
            y = 137 + i * 0.5
            add_track(board, 168, y, 288, 137+i, fcu, 0.15, n)

def route_misc_signals(board):
    """Reset, NCE status, flash nets on F.Cu/B.Cu."""
    print("  Routing misc signals...")
    fcu = board.GetLayerID("F.Cu")
    bcu = board.GetLayerID("B.Cu")

    # RESET: SW1(285,200) → U1(165,135)
    rst = board.FindNet("RESET_N")
    if rst:
        add_track(board, 285, 200, 240, 170, fcu, 0.15, rst)
        add_track(board, 240, 170, 168, 138, fcu, 0.15, rst)

    # Flash: U23(218,168) → U1(165,135) SPI already done; CS
    flash_cs = board.FindNet("FLASH_CS")
    if flash_cs:
        add_track(board, 215, 168, 168, 140, fcu, 0.15, flash_cs)

    # LED indicators: D1-D3 (115-125, 180)
    led_a = board.FindNet("LED_A")
    if led_a:
        add_track(board, 115, 180, 115, 190, fcu, 0.15, led_a)

    # NCE power good / status
    ncepg = board.FindNet("NCE_PG")
    if ncepg:
        add_track(board, 240, 140, 245, 178, fcu, 0.15, ncepg)

def route_decoupling(board):
    """Connect decoupling caps to their respective power/GND nets."""
    print("  Connecting decoupling capacitors...")
    fcu = board.GetLayerID("F.Cu")
    gnd = board.FindNet("GND")
    v18 = board.FindNet("+1V8")
    v33 = board.FindNet("+3V3")
    v09 = board.FindNet("+0V9")
    v10 = board.FindNet("+1V0")
    v5  = board.FindNet("+5V")

    # C10 group (160-166, 128) near U4 BGA — 0V9 decoupling
    for x in [160, 163, 166]:
        if v09:
            add_track(board, x, 128, x, 133, fcu, 0.2, v09)
            add_track(board, x, 128, x, 123, fcu, 0.2, gnd)

    # C30-C37 row at (192-208, 168) and (192/208, 153) — 3V3 decoupling
    for x in range(192, 212, 3):
        if v33:
            add_track(board, x, 168, x, 165, fcu, 0.2, v33)
            add_track(board, x, 168, x, 171, fcu, 0.2, gnd)

    # C1a, C1b, C2a-C2c (127-148, 200) — 1V8 decoupling near U13
    for x in range(127, 151, 3):
        if v18:
            add_track(board, x, 200, x, 203, fcu, 0.2, v18)
            add_track(board, x, 200, x, 197, fcu, 0.2, gnd)

    # C50_x (226-235, 144) — 1V0 near U4 BGA
    for x in range(226, 237, 3):
        if v10:
            add_track(board, x, 144, x, 141, fcu, 0.2, v10)
            add_track(board, x, 144, x, 147, fcu, 0.2, gnd)

    # C38-C41 (192-208, 112) — 3V3 near U21/U24 ADC/DAC
    for x in [192, 195, 205, 208]:
        if v33:
            add_track(board, x, 112, x, 115, fcu, 0.2, v33)
            add_track(board, x, 112, x, 109, fcu, 0.2, gnd)


# ── GND stitching vias ────────────────────────────────────────────────────────

def add_gnd_stitching(board):
    """Add GND stitching vias on a grid throughout the board."""
    print("  Adding GND stitching vias...")
    gnd = board.FindNet("GND")
    if gnd is None:
        return
    # 5mm grid, inset 5mm from edge
    x = 107
    while x < 295:
        y = 82
        while y < 220:
            add_via(board, x, y, 0.2, 0.4, gnd)
            y += 5.0
        x += 5.0
    print(f"  GND stitching complete")


# ── Gerber / drill export ─────────────────────────────────────────────────────

def export_gerbers(board):
    os.makedirs(GERBER_DIR, exist_ok=True)
    print(f"  Exporting Gerbers to {GERBER_DIR} ...")

    plot_ctrl = pcbnew.PLOT_CONTROLLER(board)
    plot_opts = plot_ctrl.GetPlotOptions()

    plot_opts.SetOutputDirectory(GERBER_DIR)
    plot_opts.SetPlotFrameRef(False)
    plot_opts.SetPlotValue(True)
    plot_opts.SetPlotReference(True)
    plot_opts.SetSketchPadsOnFabLayers(False)
    plot_opts.SetSubtractMaskFromSilk(False)
    plot_opts.SetFormat(pcbnew.PLOT_FORMAT_GERBER)
    plot_opts.SetGerberPrecision(6)
    plot_opts.SetUseGerberX2format(True)
    plot_opts.SetIncludeGerberNetlistInfo(True)
    plot_opts.SetCreateGerberJobFile(True)
    plot_opts.SetUseGerberProtelExtensions(False)
    plot_opts.SetUseGerberAttributes(True)

    copper_layers = [
        (pcbnew.F_Cu,  "F.Cu"),
        (pcbnew.In1_Cu, "In1.Cu"), (pcbnew.In2_Cu, "In2.Cu"),
        (pcbnew.In3_Cu, "In3.Cu"), (pcbnew.In4_Cu, "In4.Cu"),
        (pcbnew.In5_Cu, "In5.Cu"), (pcbnew.In6_Cu, "In6.Cu"),
        (pcbnew.In7_Cu, "In7.Cu"), (pcbnew.In8_Cu, "In8.Cu"),
        (pcbnew.In9_Cu, "In9.Cu"), (pcbnew.In10_Cu, "In10.Cu"),
        (pcbnew.In11_Cu, "In11.Cu"), (pcbnew.In12_Cu, "In12.Cu"),
        (pcbnew.In13_Cu, "In13.Cu"), (pcbnew.In14_Cu, "In14.Cu"),
        (pcbnew.In15_Cu, "In15.Cu"), (pcbnew.In16_Cu, "In16.Cu"),
        (pcbnew.In17_Cu, "In17.Cu"), (pcbnew.In18_Cu, "In18.Cu"),
        (pcbnew.In19_Cu, "In19.Cu"), (pcbnew.In20_Cu, "In20.Cu"),
        (pcbnew.B_Cu,  "B.Cu"),
    ]
    non_copper = [
        (pcbnew.F_SilkS, "F.SilkS"),
        (pcbnew.B_SilkS, "B.SilkS"),
        (pcbnew.F_Mask,  "F.Mask"),
        (pcbnew.B_Mask,  "B.Mask"),
        (pcbnew.F_Paste, "F.Paste"),
        (pcbnew.B_Paste, "B.Paste"),
        (pcbnew.Edge_Cuts, "Edge.Cuts"),
    ]

    for layer_id, layer_name in copper_layers + non_copper:
        plot_ctrl.SetLayer(layer_id)
        plot_ctrl.OpenPlotfile(layer_name.replace(".", "_"), pcbnew.PLOT_FORMAT_GERBER, layer_name)
        plot_ctrl.PlotLayer()
        plot_ctrl.ClosePlot()
        print(f"    Gerber: {layer_name}")

    # Drill file
    drill = pcbnew.EXCELLON_WRITER(board)
    drill.SetOptions(False, True, pcbnew.VECTOR2I(0, 0), True)
    drill.SetFormat(True)
    drill.CreateDrillandMapFilesSet(GERBER_DIR, True, True)
    print("  Drill files written")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading: {PCB_IN}")
    board = pcbnew.LoadBoard(PCB_IN)
    print(f"  Nets: {board.GetNetCount()}")
    print(f"  Footprints: {len(list(board.GetFootprints()))}")

    print("\n[1] Configuring design rules...")
    configure_design_rules(board)

    print("\n[2] Adding power planes...")
    add_power_planes(board)

    print("\n[3] Routing critical signals...")
    route_clocks(board)
    route_tfln_optical(board)
    route_hbm(board)
    route_axi_bus(board)
    route_spi(board)
    route_uart_usb(board)
    route_jtag(board)
    route_opt_sma(board)
    route_power_traces(board)
    route_i2c_gpio(board)
    route_misc_signals(board)
    route_decoupling(board)

    print("\n[4] GND stitching vias...")
    add_gnd_stitching(board)

    print("\n[5] Filling copper zones...")
    fill_zones(board)

    print(f"\n[6] Saving routed PCB → {PCB_OUT}")
    board.Save(PCB_OUT)

    print("\n[7] Exporting Gerbers...")
    board2 = pcbnew.LoadBoard(PCB_OUT)
    export_gerbers(board2)

    print("\nDone.")
    print(f"  PCB:     {PCB_OUT}")
    print(f"  Gerbers: {GERBER_DIR}")

if __name__ == "__main__":
    main()

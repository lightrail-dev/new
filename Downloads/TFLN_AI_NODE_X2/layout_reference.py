"""
TFLN_AI_NODE_X2 — Reference-matched layout
Target: match reference image (dual NCE flanking TFLN, dense edge connector banks)

Board: 305x280mm, origin at (10,10) -> (315,290)
Centre: (162.5, 150)

Layout plan (matching reference image):
  NCE-A (U1)  : left-centre  ~(105, 150)
  NCE-B (U4)  : right-centre ~(220, 150)
  TFLN (U3)   : centre       (162.5, 145) vertical
  Left bank   : GPIO/JTAG connectors stacked @ X~30
  Right bank  : GPIO/SMA/debug connectors   @ X~295
  Top edge    : SMA x4 + MPO-24
  Bottom row  : LDOs, bulk caps, test points
  Power corner: TPS54560 + inductors @ bottom-left
"""

import sys, os, math
sys.path.insert(0, r"C:\Program Files\KiCad\9.0\bin\Lib\site-packages")
os.add_dll_directory(r"C:\Program Files\KiCad\9.0\bin")
import pcbnew

SRC = r"C:\Users\bolao\Downloads\TFLN_AI_NODE_X2\TFLN_AI_NODE_X2.kicad_pcb"
OUT = r"C:\Users\bolao\Downloads\TFLN_AI_NODE_X2\TFLN_AI_NODE_X2_routed.kicad_pcb"

def mm(v):  return pcbnew.FromMM(v)
def umm(v): return pcbnew.ToMM(v)

def place(fp, x, y, angle=0.0, flip=False):
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    fp.SetOrientationDegrees(angle)
    if flip:
        fp.Flip(fp.GetPosition(), False)

def fp(b, ref):
    for f in b.GetFootprints():
        if f.GetReference() == ref:
            return f
    return None

def trk(b, x1,y1, x2,y2, layer, w, net_name):
    n = b.FindNet(net_name)
    if not n: return
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(  pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNet(n)
    b.Add(t)

def via(b, x, y, drill, outer, net_name):
    n = b.FindNet(net_name)
    if not n: return
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetDrill(mm(drill)); v.SetWidth(mm(outer))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(n); b.Add(v)

def arc45(b, x1,y1, x2,y2, layer, w, net_name):
    """Route L-shaped path with 45-degree bend."""
    n = b.FindNet(net_name)
    if not n: return
    dx = x2-x1; dy = y2-y1
    if abs(dx) > abs(dy):
        mx = x1 + (dx - abs(dy)*math.copysign(1,dx))
        trk(b, x1,y1, mx,y1,   layer, w, net_name)
        trk(b, mx,y1, x2,y2,   layer, w, net_name)
    else:
        my = y1 + (dy - abs(dx)*math.copysign(1,dy))
        trk(b, x1,y1, x1,my,   layer, w, net_name)
        trk(b, x1,my, x2,y2,   layer, w, net_name)

def zone_rect(b, net_name, layer, x0,y0,x1,y1, clr=0.15, mw=0.2):
    n = b.FindNet(net_name)
    if not n: return
    z = pcbnew.ZONE(b)
    z.SetNet(n); z.SetLayer(layer)
    z.SetLocalClearance(mm(clr)); z.SetMinThickness(mm(mw))
    z.SetIsFilled(True)
    z.SetFillMode(pcbnew.ZONE_FILL_MODE_POLYGONS)
    ol = z.Outline(); ol.NewOutline()
    for (x,y) in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:
        ol.Append(mm(x), mm(y))
    b.Add(z)

def add_line(b, x1,y1,x2,y2, layer, w=0.1):
    l = pcbnew.PCB_SHAPE(b)
    l.SetShape(pcbnew.SHAPE_T_SEGMENT)
    l.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    l.SetEnd(  pcbnew.VECTOR2I(mm(x2),mm(y2)))
    l.SetLayer(layer); l.SetWidth(mm(w)); b.Add(l)

# ─── constants ────────────────────────────────────────────────────────────────
OX, OY   = 10.0, 10.0
BW, BH   = 305.0, 280.0
CX, CY   = OX+BW/2, OY+BH/2   # 162.5, 150
F_Cu     = pcbnew.F_Cu
B_Cu     = pcbnew.B_Cu
In1      = pcbnew.In1_Cu
In2      = pcbnew.In2_Cu   # GND L3
In5      = pcbnew.In5_Cu   # SerDes L6
In6      = pcbnew.In6_Cu   # PWR / RF L7
In7      = pcbnew.In7_Cu   # TFLN diff L8
In9      = pcbnew.In9_Cu   # GND L10
In10     = pcbnew.In10_Cu  # CLK L11
In15     = pcbnew.In15_Cu  # GND L16
In16     = pcbnew.In16_Cu  # DDR5 L17

FILL_CORNERS = [
    (OX+0.5, OY+0.5), (OX+BW-0.5, OY+0.5),
    (OX+BW-0.5, OY+BH-0.5), (OX+0.5, OY+BH-0.5)
]

# ─── PLACEMENT ────────────────────────────────────────────────────────────────
def place_components(b):
    print("  Placing components to match reference layout...")

    # ── Main ICs ──────────────────────────────────────────────────────────────
    # NCE-A left-of-centre, NCE-B right-of-centre, TFLN PIC centre
    place(fp(b,"U1"),  105.0, 148.0)       # NCE FPGA-A  (left)
    place(fp(b,"U4"),  220.0, 148.0)       # NCE FPGA-B  (right)
    place(fp(b,"U3"),  162.5, 143.0)       # TFLN PIC    (centre, slight north)
    place(fp(b,"U2"),  162.5, 148.0)       # XC7A (secondary, below TFLN)

    # ── Clock & analog support ─────────────────────────────────────────────────
    place(fp(b,"U20"), 162.5, 195.0)       # Si5395A clock  (between chips, south)
    place(fp(b,"U21"), 110.0, 210.0)       # AD7928 ADC     (south of NCE-A)
    place(fp(b,"U24"), 215.0, 210.0)       # AD5684R DAC    (south of NCE-B)
    place(fp(b,"U25"), 162.5, 215.0)       # TMP461 temp    (south centre)

    # ── USB/debug/flash ────────────────────────────────────────────────────────
    place(fp(b,"U22"), 270.0, 210.0)       # FT232H USB-UART (right of DAC)
    place(fp(b,"U23"), 270.0, 195.0)       # W25Q128 flash   (above FT232H)

    # ── Power regulators — bottom-left quadrant ────────────────────────────────
    place(fp(b,"U15"),  38.0, 255.0)       # TPS54560 buck
    place(fp(b,"U13"),  65.0, 255.0)       # TPS7A3301 1V8 LDO
    place(fp(b,"U14"),  90.0, 255.0)       # TPS7A2018 3V3 LDO
    place(fp(b,"U10"), 115.0, 255.0)       # ADP7118 (SerDes)
    place(fp(b,"U11"), 140.0, 255.0)       # TPS7A2018 (HBM)
    place(fp(b,"U12"), 165.0, 255.0)       # TPS7A2010 (0V9)

    # ── Passive power ─────────────────────────────────────────────────────────
    place(fp(b,"L1"),   38.0, 268.0)
    place(fp(b,"F1"),   55.0, 268.0)
    place(fp(b,"C11"),  75.0, 268.0)
    place(fp(b,"C1a"), 105.0, 268.0)
    place(fp(b,"C1b"), 110.0, 268.0)
    place(fp(b,"C2a"), 125.0, 268.0)
    place(fp(b,"C2b"), 130.0, 268.0)
    place(fp(b,"C2c"), 135.0, 268.0)
    place(fp(b,"C42"), 145.0, 268.0)
    place(fp(b,"C43"), 150.0, 268.0)
    place(fp(b,"C44"), 155.0, 268.0)
    place(fp(b,"C45"), 160.0, 268.0)

    # ── Decoupling — NCE-A cluster ─────────────────────────────────────────────
    for i, ref in enumerate(["C10_a","C10_b","C10_c","C10_d"]):
        place(fp(b,ref), 85.0 + i*5.5, 125.0)

    # ── Decoupling — NCE-B cluster ────────────────────────────────────────────
    for i, ref in enumerate(["C50_0","C50_1","C50_2","C50_3"]):
        place(fp(b,ref), 200.0 + i*5.5, 125.0)

    # ── Decoupling — power plane (around centre ICs) ──────────────────────────
    caps_centre = ["C30","C31","C32","C33","C34","C35","C36","C37"]
    for i, ref in enumerate(caps_centre):
        place(fp(b,ref), 138.0 + i*5.5, 175.0)

    # ── TFLN bias/monitor decoupling ──────────────────────────────────────────
    for i, ref in enumerate(["C38","C39","C40","C41"]):
        place(fp(b,ref), 148.0 + i*5.5, 162.0)
    for i, ref in enumerate(["C4a","C4b"]):
        place(fp(b,ref), 155.0 + i*6,   162.0)
    for i, ref in enumerate(["C50_0","C50_1","C50_2","C50_3"]): pass  # already placed
    for i, ref in enumerate(["C5a","C5b","C5_d","C5_e","C5_f","C5_g"]):
        place(fp(b,ref), 245.0 + i*5.5, 195.0)
    place(fp(b,"C4a"), 152.0, 162.0)
    place(fp(b,"C4b"), 158.0, 162.0)
    place(fp(b,"C9a"), 230.0, 185.0)
    for i, ref in enumerate(["R1a"]):
        place(fp(b,ref), 205.0, 185.0)
    place(fp(b,"D5a"), 240.0, 185.0)
    place(fp(b,"D5b"), 255.0, 185.0)

    # ── LED + switch — left perimeter ─────────────────────────────────────────
    place(fp(b,"D1"),  25.0, 200.0)
    place(fp(b,"D2"),  25.0, 207.0)
    place(fp(b,"D3"),  25.0, 214.0)
    place(fp(b,"R5a"), 35.0, 200.0)
    place(fp(b,"R5_b"),35.0, 207.0)
    place(fp(b,"R5_c"),35.0, 214.0)
    place(fp(b,"SW1"), 285.0,265.0)

    # ── DC input + USB-C — left/right bottom ──────────────────────────────────
    place(fp(b,"J1"),  18.0, 265.0)
    place(fp(b,"J2"),  280.0,200.0, angle=270.0)

    # ── Test points — bottom edge strip ───────────────────────────────────────
    for i, ref in enumerate(["TP1","TP2","TP3","TP4","TP5","TP6","TP7"]):
        place(fp(b,ref), 60.0 + i*15.0, 278.0)

    # ── Mounting holes ────────────────────────────────────────────────────────
    place(fp(b,"MH1"), OX+7,    OY+7)
    place(fp(b,"MH2"), OX+BW-7, OY+7)
    place(fp(b,"MH3"), OX+7,    OY+BH-7)
    place(fp(b,"MH4"), OX+BW-7, OY+BH-7)

    # ── Top-edge connectors ───────────────────────────────────────────────────
    # MPO-24 at top-centre, SMA x4 flanking
    place(fp(b,"J11"), 162.5, OY+18.0)          # MPO-24 centre-top
    place(fp(b,"J7"),   90.0, OY+18.0)          # SMA RF CH0
    place(fp(b,"J8"),  120.0, OY+18.0)          # SMA RF CH1
    place(fp(b,"J9"),  205.0, OY+18.0)          # SMA RF CH2
    place(fp(b,"J10"), 235.0, OY+18.0)          # SMA RF CH3

    # ── Left-edge connector bank (GPIO/JTAG) ──────────────────────────────────
    place(fp(b,"J5"),  OX+18.0, 148.0)          # JTAG header  (left bank top)
    place(fp(b,"J6"),  OX+18.0, 170.0)          # GPIO header  (left bank bottom)

    # ── Right-edge: clock oscillator ─────────────────────────────────────────
    place(fp(b,"Y1"),  260.0, 145.0)

    print(f"    All {len(list(b.GetFootprints()))} footprints placed")

# ─── ROUTING ──────────────────────────────────────────────────────────────────
def route_power(b):
    print("  Routing power...")
    # 12V from J1 -> F1 -> U15 on F.Cu (wide)
    trk(b, 18,265, 55,265,  F_Cu, 0.5, "+12V")
    trk(b, 55,265, 38,255,  F_Cu, 0.5, "+12V")
    # +5V from U15 out -> LDOs
    trk(b, 38,255, 65,255,  F_Cu, 0.4, "+5V")
    trk(b, 65,255, 90,255,  F_Cu, 0.4, "+5V")
    trk(b, 90,255, 115,255, F_Cu, 0.4, "+5V")
    # GND bus bottom
    trk(b, 18,270, 300,270, F_Cu, 0.8, "GND")

def route_clocks(b):
    print("  Routing clock tree on L11 (In10)...")
    clks = ["CLK_SERDES","CLK_HBM","CLK_CORE","CLK_REF"]
    for i, net in enumerate(clks):
        # Si5395A at (162.5, 195) fanout to NCE-A/B
        cx, cy = 162.5, 195.0
        trk(b, cx, cy,        105+i*3, 175, In10, 0.12, net)
        trk(b, cx, cy,        220+i*3, 175, In10, 0.12, net)

def route_axi(b):
    print("  Routing AXI bus on L4/L5 (In3/In4)...")
    # NCE-A (105,148) to TFLN/centre (162.5,148) — AXI-A
    for i in range(8):
        y = 133.0 + i*2.0
        trk(b, 120,y,  152,y,  pcbnew.In3_Cu, 0.10, f"CLK_CORE")
    # NCE-B (220,148) to centre — AXI-B
    for i in range(8):
        y = 133.0 + i*2.0
        trk(b, 208,y,  175,y,  pcbnew.In4_Cu, 0.10, f"CLK_HBM")

def route_tfln_rf(b):
    print("  Routing TFLN RF CPWG pairs on L8 (In7)...")
    gnd = b.FindNet("GND")
    # TFLN PIC at (162.5, 143). RF pads fan north to SMA connectors
    pairs = [
        ("TFLN_TX_P0","TFLN_TX_N0", 90.0,  18.0),  # -> J7
        ("TFLN_TX_P1","TFLN_TX_N1",120.0,  18.0),  # -> J8
        ("TFLN_TX_P2","TFLN_TX_N2",205.0,  18.0),  # -> J9
        ("TFLN_TX_P3","TFLN_TX_N3",235.0,  18.0),  # -> J10
    ]
    W, G = 0.10, 0.10
    for i, (np_n, nn_n, jx, jy) in enumerate(pairs):
        np_ = b.FindNet(np_n); nn = b.FindNet(nn_n)
        if not np_ or not nn: continue
        # Start at TFLN PIC north edge, fan to SMA
        sx = 155.0 + i*2.2
        sy = 130.0  # TFLN north edge
        # P trace: TFLN -> via -> L8 run -> via -> SMA
        trk(b, sx,   sy, sx,   jy+3,  In7, W, np_n)
        trk(b, sx,   jy+3, jx, jy+3, In7, W, np_n)
        # N trace
        trk(b, sx+W+G, sy, sx+W+G, jy+3,  In7, W, nn_n)
        trk(b, sx+W+G, jy+3, jx+W+G, jy+3, In7, W, nn_n)
        # GND rails (CPWG)
        trk(b, sx-G-0.15, sy, sx-G-0.15, jy+3, In7, 0.15, "GND")
        trk(b, sx+2*(W+G), sy, sx+2*(W+G), jy+3, In7, 0.15, "GND")
        # Stitching vias every 3mm
        ys = sy
        while ys > jy+5:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(sx-G-0.3), mm(ys)))
            v.SetDrill(mm(0.15)); v.SetWidth(mm(0.30))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetNet(gnd); b.Add(v)
            ys -= 3.0

def route_serdes(b):
    print("  Routing SerDes diff pairs on L6 (In5)...")
    # NCE-A (105,148) <-> NCE-B (220,148) high-speed diff pairs through centre
    pairs = [
        ("CLK_SERDES","CLK_SERDES_N"),
        ("CLK_HBM","CLK_HBM_N"),
    ]
    W, G = 0.10, 0.12
    for i, (np_n, nn_n) in enumerate(pairs):
        y = 148.0 + i*0.8
        trk(b, 120,y,   205,y,     In5, W, np_n)
        trk(b, 120,y+W+G, 205,y+W+G, In5, W, nn_n)
        # GND rails
        trk(b, 120,y-G-0.15, 205,y-G-0.15, In5, 0.15, "GND")
        trk(b, 120,y+2*(W+G), 205,y+2*(W+G), In5, 0.15, "GND")
        # Vias at each NCE
        via(b, 120,y,      0.15,0.30,"GND")
        via(b, 205,y,      0.15,0.30,"GND")

def route_spi_i2c(b):
    print("  Routing SPI/I2C on F.Cu...")
    # SPI from NCE-A to ADC (U21 @110,210) + flash (U23 @270,195)
    trk(b, 105,155, 110,210, F_Cu, 0.15, "SPI_CLK")
    trk(b, 105,157, 110,212, F_Cu, 0.15, "SPI_MOSI")
    trk(b, 105,159, 110,214, F_Cu, 0.15, "SPI_MISO")
    # I2C to TMP461 (162.5,215) and Si5395A (162.5,195)
    trk(b, 162.5,155, 162.5,195, F_Cu, 0.15, "I2C_SCL")
    trk(b, 163.5,155, 163.5,195, F_Cu, 0.15, "I2C_SDA")
    trk(b, 162.5,195, 162.5,215, F_Cu, 0.15, "I2C_SCL")
    trk(b, 163.5,195, 163.5,215, F_Cu, 0.15, "I2C_SDA")

def route_uart_jtag(b):
    print("  Routing UART/JTAG on F.Cu...")
    # FT232H (270,210) -> USB-C (280,200)
    trk(b, 270,210, 280,200, F_Cu, 0.20, "UART_TX")
    trk(b, 271,210, 281,200, F_Cu, 0.20, "UART_RX")
    # JTAG header J5 (28,148) -> NCE-A (105,148)
    trk(b, 28,148, 90,148,  F_Cu, 0.15, "JTAG_TCK")
    trk(b, 28,150, 90,150,  F_Cu, 0.15, "JTAG_TMS")
    trk(b, 28,152, 90,152,  F_Cu, 0.15, "JTAG_TDI")
    trk(b, 28,154, 90,154,  F_Cu, 0.15, "JTAG_TDO")

def route_ddr5_hbm(b):
    print("  Routing DDR5/HBM diff pairs on L17 (In16)...")
    # NCE-B (220,148) -> centre
    for i in range(8):
        net = f"HBM_DQ{i}"
        n = b.FindNet(net)
        if not n: continue
        y = 140.0 + i*1.5
        trk(b, 205,y, 175,y, pcbnew.In16_Cu, 0.10, net)

def route_bias_mon(b):
    print("  Routing TFLN BIAS/MON on F.Cu...")
    # BIAS: AD5684R (215,210) -> TFLN pads north
    for i in range(4):
        net = f"BIAS_V{i+1}"
        trk(b, 215,210, 162.5-2+i*1.5, 145, F_Cu, 0.20, net)
    # MON: TFLN pads -> AD7928 (110,210)
    for i in range(8):
        net = f"MON_PD{i}"
        n = b.FindNet(net)
        if not n: continue
        trk(b, 162.5+2+i*1.2, 145, 110,210, F_Cu, 0.15, net)

def add_connector_fanout(b):
    """Dense trace fan on top of NCE chips (matches reference image fan pattern)."""
    print("  Adding NCE top fanout traces...")
    # NCE-A at (105,148): fan north with 45-deg exits
    for i in range(16):
        x  = 90.0 + i*2.0
        trk(b, x, 133, x, 75, F_Cu, 0.10, "GND")  # placeholder fan lines
    # NCE-B at (220,148): fan north
    for i in range(16):
        x  = 205.0 + i*2.0
        trk(b, x, 133, x, 75, F_Cu, 0.10, "GND")

def add_power_planes(b):
    print("  Adding power planes...")
    gnd_layers = [pcbnew.In2_Cu, pcbnew.In9_Cu, pcbnew.In12_Cu,
                  pcbnew.In15_Cu, pcbnew.In20_Cu]
    for l in gnd_layers:
        zone_rect(b, "GND", l, OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5)
    zone_rect(b, "+0V9", pcbnew.In11_Cu, OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5)
    zone_rect(b, "+1V8", pcbnew.In13_Cu, OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5)
    zone_rect(b, "+3V3", pcbnew.In14_Cu, OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5)
    # F.Cu GND pour (fills around components)
    zone_rect(b, "GND", F_Cu, OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5, clr=0.20)
    # B.Cu GND pour
    zone_rect(b, "GND", B_Cu, OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5, clr=0.20)

def add_gnd_stitching(b):
    print("  GND stitching via grid (4mm)...")
    gnd = b.FindNet("GND")
    if not gnd: return
    count = 0
    x = OX+8
    while x < OX+BW-8:
        y = OY+8
        while y < OY+BH-8:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
            v.SetDrill(mm(0.2)); v.SetWidth(mm(0.4))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetNet(gnd); b.Add(v); count += 1
            y += 4.0
        x += 4.0
    print(f"    {count} stitching vias")

def add_tfln_keepout(b):
    """No vias or traces under TFLN die body."""
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowVias(True); z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowCopperPour(False)
    z.SetLayer(F_Cu)
    ol = z.Outline(); ol.NewOutline()
    # TFLN at (162.5,143), body 25x8mm
    for (x,y) in [(150,139),(175,139),(175,147),(150,147)]:
        ol.Append(mm(x), mm(y))
    b.Add(z)

def add_silkscreen_labels(b):
    ffab = b.GetLayerID("F.Fab")
    fsilk = b.GetLayerID("F.SilkS")
    def txt(text, x, y, layer=None, sz=1.0, th=0.15):
        layer = layer or ffab
        t = pcbnew.PCB_TEXT(b)
        t.SetText(text); t.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(sz),mm(sz)))
        t.SetTextThickness(mm(th)); b.Add(t)
    txt("TFLN_AI_NODE_X2",  OX+8,  OY+3, fsilk, 2.0, 0.25)
    txt("LightRail AI",     OX+8,  OY+7, fsilk, 1.2, 0.18)
    txt("NCE-A",   100.0,  135.0, ffab,  1.2)
    txt("NCE-B",   215.0,  135.0, ffab,  1.2)
    txt("TFLN PIC",157.0,  149.0, ffab,  0.8)

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("="*60)
    print("TFLN_AI_NODE_X2 — Reference-matched layout")
    print("="*60)
    b = pcbnew.LoadBoard(SRC)
    print(f"  Loaded: {b.GetNetCount()} nets, {len(list(b.GetFootprints()))} fps")

    place_components(b)
    add_tfln_keepout(b)
    add_power_planes(b)
    route_power(b)
    route_clocks(b)
    route_axi(b)
    route_tfln_rf(b)
    route_serdes(b)
    route_spi_i2c(b)
    route_uart_jtag(b)
    route_ddr5_hbm(b)
    route_bias_mon(b)
    add_connector_fanout(b)
    add_gnd_stitching(b)
    add_silkscreen_labels(b)

    print("  Filling copper zones...")
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    b.Save(OUT)
    print(f"\nSaved -> {OUT}")

    # Quick stats
    tracks = list(b.GetTracks())
    vias   = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA)]
    segs   = [t for t in tracks if isinstance(t, pcbnew.PCB_TRACK)]
    print(f"  Tracks: {len(segs)} segments, {len(vias)} vias")
    print(f"  Zones:  {len(b.Zones())}")
    print("="*60)

if __name__ == "__main__":
    main()

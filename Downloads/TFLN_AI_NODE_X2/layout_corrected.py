"""
TFLN_AI_NODE_X2 — Corrected layout matching exact die positions and TFLN connectivity

Original board space: (100,75)->(300,225), 200x150mm
New board space:      (10,10)->(315,290),  305x280mm
Scale: Sx=305/200=1.525, Sy=280/150=1.8667

Exact die positions (original space -> scaled):
  U3  TFLN_PIC  (200,120) -> (162.5,  94.0)   ← top-centre between NCE dies
  U1  NCE-A     (165,135) -> (109.1, 122.0)   ← left NCE die
  U4  NCE-B     (235,135) -> (215.9, 122.0)   ← right NCE die
  U2  Artix-7   (200,160) -> (162.5, 168.7)   ← centre FPGA

TFLN connectivity:
  U3 → U1 : TFLN_TX_P0-3 / N0-3  on In6.Cu (L7)  — 4 diff pairs
  U3 → U4 : TFLN_TX_P0_B-P3_B    on In7.Cu (L8)  — 4 diff pairs  ← NEW
  U3 → J11 : OPT_TX0-3 + OPT_RX0-3  F.Cu stubs to MPO-24 (top edge)
  U3 → U21 : MON_CH0-7   F.Cu   — optical power monitoring ADC
  U3 → U24 : DAC_V1-4    F.Cu   — MZI phase tuning DAC
  U3 → U25 : TEMP_DIODE  F.Cu   — temp sensor
  Keep-out: copper-free zone under TFLN body (no embedded waveguides)
"""

import sys, os, math
sys.path.insert(0, r"C:\Program Files\KiCad\9.0\bin\Lib\site-packages")
os.add_dll_directory(r"C:\Program Files\KiCad\9.0\bin")
import pcbnew

SRC = r"C:\Users\bolao\Downloads\TFLN_AI_NODE_X2\TFLN_AI_NODE_X2.kicad_pcb"
OUT = r"C:\Users\bolao\Downloads\TFLN_AI_NODE_X2\TFLN_AI_NODE_X2_routed.kicad_pcb"

# Board constants
OX, OY   = 10.0, 10.0
BW, BH   = 305.0, 280.0
SX, SY   = 305.0/200.0, 280.0/150.0   # 1.525, 1.8667
X0, Y0   = 100.0, 75.0                  # original board origin

def sc(ox, oy):
    """Scale original coords to new board space."""
    return (OX + (ox - X0)*SX, OY + (oy - Y0)*SY)

def mm(v):  return pcbnew.FromMM(v)
def umm(v): return pcbnew.ToMM(v)

def fp(b, ref):
    for f in b.GetFootprints():
        if f.GetReference() == ref:
            return f
    return None

def place(b, ref, ox, oy, angle=0.0):
    """Place footprint using original-space coordinates."""
    x, y = sc(ox, oy)
    f = fp(b, ref)
    if not f:
        print(f"    WARN: {ref} not found")
        return
    f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    f.SetOrientationDegrees(angle)

def place_xy(b, ref, x, y, angle=0.0):
    """Place footprint using already-scaled coordinates."""
    f = fp(b, ref)
    if not f:
        print(f"    WARN: {ref} not found")
        return
    f.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    f.SetOrientationDegrees(angle)

def trk(b, x1, y1, x2, y2, layer, w, net_name):
    n = b.FindNet(net_name)
    if not n:
        return
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(  pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetLayer(layer); t.SetWidth(mm(w)); t.SetNet(n)
    b.Add(t)

def via_th(b, x, y, drill, outer, net_name):
    n = b.FindNet(net_name)
    if not n:
        return
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetDrill(mm(drill)); v.SetWidth(mm(outer))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(n); b.Add(v)

def cpwg_pair(b, np_name, nn_name, x1, y1, x2, y2, layer,
              W=0.10, G=0.10, gnd_w=0.15, stitch_mm=2.0):
    """Route a CPWG differential pair with GND rails and stitching vias."""
    gnd = b.FindNet("GND")
    dx = x2-x1; dy = y2-y1
    length = math.sqrt(dx*dx + dy*dy)

    trk(b, x1,       y1,       x2,       y2,       layer, W,     np_name)
    trk(b, x1+W+G,   y1,       x2+W+G,   y2,       layer, W,     nn_name)
    trk(b, x1-G-gnd_w/2, y1,  x2-G-gnd_w/2, y2,   layer, gnd_w, "GND")
    trk(b, x1+2*W+2*G+gnd_w/2, y1, x2+2*W+2*G+gnd_w/2, y2, layer, gnd_w, "GND")

    # Stitching vias along run
    if gnd and length > stitch_mm:
        steps = int(length / stitch_mm)
        for i in range(steps+1):
            t = i / max(steps,1)
            vx = x1 + t*dx; vy = y1 + t*dy
            via_th(b, vx - G - gnd_w, vy, 0.15, 0.30, "GND")
            via_th(b, vx + 2*W+2*G+gnd_w, vy, 0.15, 0.30, "GND")

def zone_rect(b, net_name, layer, x0, y0, x1, y1, clr=0.15, mw=0.2):
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

def add_line(b, x1,y1,x2,y2, layer, w=0.12):
    l = pcbnew.PCB_SHAPE(b)
    l.SetShape(pcbnew.SHAPE_T_SEGMENT)
    l.SetStart(pcbnew.VECTOR2I(mm(x1),mm(y1)))
    l.SetEnd(  pcbnew.VECTOR2I(mm(x2),mm(y2)))
    l.SetLayer(layer); l.SetWidth(mm(w)); b.Add(l)

def add_text(b, text, x, y, layer, sz=1.0, th=0.15):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(text)
    t.SetPosition(pcbnew.VECTOR2I(mm(x),mm(y)))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(sz),mm(sz)))
    t.SetTextThickness(mm(th)); b.Add(t)

# ─── Scaled die positions (pre-computed) ────────────────────────────────────
# TFLN_PIC  original (200,120)
T3X, T3Y   = sc(200, 120)   # (162.5, 94.0)
# NCE-A      original (165,135)
U1X, U1Y   = sc(165, 135)   # (109.1, 122.0)
# NCE-B      original (235,135)
U4X, U4Y   = sc(235, 135)   # (215.9, 122.0)
# Artix-7    original (200,160)
U2X, U2Y   = sc(200, 160)   # (162.5, 168.7)

# TFLN body: 25x8mm, centred at (T3X, T3Y)
TFLN_HW = 25.0/2   # half-width in board space (not scaled — physical SMD size)
TFLN_HH =  8.0/2

# MPO-24 at top edge, original (200, 24.9) → but clamp to board top
MPO_X  = T3X          # same X as TFLN
MPO_Y  = OY + 20.0    # top edge + 20mm setback

# SMA connectors: flanking MPO on top edge
SMA_Y  = OY + 20.0
SMA_J7_X  = U1X - 18.0    # left of NCE-A
SMA_J8_X  = U1X -  4.0
SMA_J9_X  = U4X +  4.0
SMA_J10_X = U4X + 18.0

# Support ICs (original positions scaled)
U20X, U20Y = sc(230, 150)   # Si5395A clock
U21X, U21Y = sc(182, 112)   # AD7928 ADC  (near TFLN, for MON_CH)
U24X, U24Y = sc(218, 112)   # AD5684R DAC (near TFLN, for DAC_V)
U25X, U25Y = sc(158, 150)   # TMP461 temp sensor

# ─── STEP 1: Component placement ─────────────────────────────────────────────
def place_all(b):
    print("  [7] Placing components...")

    # ── Primary dies (user-specified exact positions) ──────────────────────
    place(b, "U3",  200, 120)          # TFLN_PIC  — top centre
    place(b, "U1",  165, 135)          # NCE-A     — left die
    place(b, "U4",  235, 135)          # NCE-B     — right die
    place(b, "U2",  200, 160)          # Artix-7   — centre FPGA

    # ── Top-edge optical/RF connectors ─────────────────────────────────────
    place_xy(b, "J11", MPO_X,  MPO_Y)          # MPO-24 centre-top
    place_xy(b, "J7",  SMA_J7_X,  SMA_Y)       # SMA RF CH0
    place_xy(b, "J8",  SMA_J8_X,  SMA_Y)       # SMA RF CH1
    place_xy(b, "J9",  SMA_J9_X,  SMA_Y)       # SMA RF CH2
    place_xy(b, "J10", SMA_J10_X, SMA_Y)       # SMA RF CH3

    # ── Analog support (close to TFLN for short signal paths) ─────────────
    place(b, "U20", 230, 150)       # Si5395A clock gen
    place(b, "U21", 182, 112)       # AD7928 ADC  — MON_CH0-7
    place(b, "U24", 218, 112)       # AD5684R DAC — DAC_V1-4
    place(b, "U25", 158, 150)       # TMP461      — TEMP_DIODE

    # ── USB/debug/flash ────────────────────────────────────────────────────
    place(b, "U22", 245, 175)       # FT4232H USB-UART
    place(b, "U23", 245, 160)       # W25Q128 flash

    # ── Power regulators — bottom-left ────────────────────────────────────
    place(b, "U15", 120, 208)       # TPS54560 buck  (12V→5V)
    place(b, "U13", 135, 208)       # TPS7A3301 1V8
    place(b, "U14", 150, 208)       # TPS7A2018 3V3
    place(b, "U10", 165, 208)       # ADP7118   1V0 SerDes
    place(b, "U11", 180, 208)       # TPS7A2018 1V0 HBM
    place(b, "U12", 195, 208)       # TPS7A2010 0V9

    # ── Power passives ─────────────────────────────────────────────────────
    place(b, "L1",  120, 218)
    place(b, "F1",  130, 218)
    place(b, "C11", 140, 218)
    place(b, "C1a", 150, 218); place(b, "C1b", 155, 218)
    place(b, "C2a", 160, 218); place(b, "C2b", 165, 218); place(b, "C2c", 170, 218)
    place(b, "C42", 175, 218); place(b, "C43", 180, 218)
    place(b, "C44", 185, 218); place(b, "C45", 190, 218)

    # ── Decoupling — NCE-A cluster (above U1) ─────────────────────────────
    for i, ref in enumerate(["C10_a","C10_b","C10_c","C10_d"]):
        place(b, ref, 155 + i*3, 127)

    # ── Decoupling — NCE-B cluster (above U4) ─────────────────────────────
    for i, ref in enumerate(["C50_0","C50_1","C50_2","C50_3"]):
        place(b, ref, 220 + i*3, 127)

    # ── Decoupling — centre ICs ────────────────────────────────────────────
    for i, ref in enumerate(["C30","C31","C32","C33","C34","C35","C36","C37"]):
        place(b, ref, 180 + i*3, 168)

    # ── TFLN bias/MON decoupling (near U21/U24) ───────────────────────────
    for i, ref in enumerate(["C38","C39"]):
        place(b, ref, 177 + i*4, 107)
    for i, ref in enumerate(["C40","C41"]):
        place(b, ref, 213 + i*4, 107)
    for i, ref in enumerate(["C4a","C4b"]):
        place(b, ref, 190 + i*4, 107)
    for i, ref in enumerate(["C5a","C5b","C5_d","C5_e","C5_f","C5_g"]):
        place(b, ref, 230 + i*3, 167)
    place(b, "C9a", 235, 158)
    place(b, "R1a",  195, 115)
    place(b, "D5a",  238, 158)
    place(b, "D5b",  245, 158)
    place(b, "C4a",  193, 107)
    place(b, "C4b",  197, 107)

    # ── LEDs + reset ───────────────────────────────────────────────────────
    place_xy(b, "D1",  OX+22, OY+90)
    place_xy(b, "D2",  OX+22, OY+97)
    place_xy(b, "D3",  OX+22, OY+104)
    place_xy(b, "R5a", OX+30, OY+90)
    place_xy(b, "R5_b",OX+30, OY+97)
    place_xy(b, "R5_c",OX+30, OY+104)
    place_xy(b, "SW1", OX+BW-25, OY+BH-25)

    # ── DC Jack + USB-C ────────────────────────────────────────────────────
    place_xy(b, "J1",  OX+18,    OY+BH-18)
    place_xy(b, "J2",  OX+BW-18, OY+105, 270.0)

    # ── GPIO/JTAG headers — left edge ─────────────────────────────────────
    place_xy(b, "J5",  OX+18, OY+140)
    place_xy(b, "J6",  OX+18, OY+160)

    # ── Test points ────────────────────────────────────────────────────────
    for i, ref in enumerate(["TP1","TP2","TP3","TP4","TP5","TP6","TP7"]):
        place_xy(b, ref, OX+50 + i*18, OY+BH-12)

    # ── Mounting holes ─────────────────────────────────────────────────────
    place_xy(b, "MH1", OX+7,    OY+7)
    place_xy(b, "MH2", OX+BW-7, OY+7)
    place_xy(b, "MH3", OX+7,    OY+BH-7)
    place_xy(b, "MH4", OX+BW-7, OY+BH-7)

    # ── Clock oscillator ───────────────────────────────────────────────────
    place(b, "Y1", 235, 143)

    print(f"    {len(list(b.GetFootprints()))} footprints placed")

# ─── STEP 2: TFLN keep-out zone ──────────────────────────────────────────────
def add_tfln_keepout(b):
    """
    Copper-free keep-out under the TFLN PIC body.
    U3 is a surface-mount component on F.Cu; this prevents copper pours,
    routing and vias from running under the die body.
    NOT an embedded waveguide zone — that would require a different fab process.
    """
    print(f"  [8b] TFLN keep-out zone at ({T3X:.1f},{T3Y:.1f})...")
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetLayer(pcbnew.F_Cu)
    ol = z.Outline(); ol.NewOutline()
    for (x,y) in [
        (T3X-TFLN_HW, T3Y-TFLN_HH),
        (T3X+TFLN_HW, T3Y-TFLN_HH),
        (T3X+TFLN_HW, T3Y+TFLN_HH),
        (T3X-TFLN_HW, T3Y+TFLN_HH),
    ]:
        ol.Append(mm(x), mm(y))
    b.Add(z)
    print(f"    Keep-out: {TFLN_HW*2:.0f}x{TFLN_HH*2:.0f}mm body, "
          f"no vias/tracks/copper-pour under die")

# ─── STEP 3: TFLN RF routing ─────────────────────────────────────────────────
def route_tfln_rf(b):
    """
    U3 TFLN_PIC at (T3X,T3Y) north face → U1 NCE-A on In6.Cu (L7)
                                         → U4 NCE-B on In7.Cu (L8)
    4 diff pairs each side, 100 Ω CPWG geometry.
    Pairs fan south from TFLN_PIC bottom edge to each NCE die.
    """
    print("  [8c] TFLN RF routing U3→U1 (L7) and U3→U4 (L8)...")
    L7 = pcbnew.In6_Cu
    L8 = pcbnew.In7_Cu
    W, G = 0.10, 0.10   # 100 Ω differential CPWG

    # TFLN PIC pad exits: south face of die (y = T3Y + TFLN_HH + 0.5mm margin)
    # 4 pairs fan out with 0.8mm spacing
    TFLN_S = T3Y + TFLN_HH + 0.5   # south exit point Y

    # ── U3 → U1 NCE-A  (L7, In6.Cu) ─────────────────────────────────────
    # Pairs land on U1 north face (U1Y - some offset)
    NCE_A_N = U1Y - 8.0   # NCE-A north approach Y

    for i in range(4):
        # Pair P/N exits at X positions around TFLN centre, biased left
        px = T3X - 3.0 + i * 0.8
        np_name = f"TFLN_TX_P{i}"
        nn_name = f"TFLN_TX_N{i}"
        n_p = b.FindNet(np_name); n_n = b.FindNet(nn_name)
        if not n_p or not n_n:
            print(f"    SKIP {np_name}/{nn_name} (net not found)")
            continue

        # Blind via F.Cu -> L7 at die edge
        via_th(b, px,       TFLN_S, 0.15, 0.30, np_name)
        via_th(b, px+W+G,   TFLN_S, 0.15, 0.30, nn_name)

        # CPWG run on L7 south to NCE-A north face
        cpwg_pair(b, np_name, nn_name,
                  px, TFLN_S, px, NCE_A_N,
                  L7, W, G, 0.15, 2.0)

        # Via L7 -> F.Cu at NCE-A entry
        via_th(b, px,     NCE_A_N, 0.15, 0.30, np_name)
        via_th(b, px+W+G, NCE_A_N, 0.15, 0.30, nn_name)

        print(f"    L7 pair {i}: {np_name}/{nn_name} "
              f"({px:.2f},{TFLN_S:.2f})->({px:.2f},{NCE_A_N:.2f})")

    # ── U3 → U4 NCE-B  (L8, In7.Cu) ─────────────────────────────────────
    NCE_B_N = U4Y - 8.0   # NCE-B north approach Y

    for i in range(4):
        # Pairs biased right of centre for NCE-B
        px = T3X + 0.2 + i * 0.8
        np_name = f"TFLN_TX_P{i}_B"
        nn_name = f"TFLN_TX_N{i}_B"
        n_p = b.FindNet(np_name); n_n = b.FindNet(nn_name)
        if not n_p or not n_n:
            # Fall back to alternate net names
            np_name2 = f"TFLN_TX_P{i}"
            nn_name2 = f"TFLN_TX_N{i}"
            n_p = b.FindNet(np_name2); n_n = b.FindNet(nn_name2)
            if not n_p or not n_n:
                print(f"    SKIP L8 pair {i} (nets not found)")
                continue
            np_name, nn_name = np_name2, nn_name2

        via_th(b, px,       TFLN_S, 0.15, 0.30, np_name)
        via_th(b, px+W+G,   TFLN_S, 0.15, 0.30, nn_name)

        cpwg_pair(b, np_name, nn_name,
                  px, TFLN_S, px, NCE_B_N,
                  L8, W, G, 0.15, 2.0)

        via_th(b, px,     NCE_B_N, 0.15, 0.30, np_name)
        via_th(b, px+W+G, NCE_B_N, 0.15, 0.30, nn_name)

        print(f"    L8 pair {i}: {np_name}/{nn_name} "
              f"({px:.2f},{TFLN_S:.2f})->({px:.2f},{NCE_B_N:.2f})")

# ─── STEP 4: TFLN optical stub routing ───────────────────────────────────────
def route_tfln_optical(b):
    """
    U3 → J11 MPO-24: OPT_TX0-3, OPT_RX0-3
    Short F.Cu stubs north from TFLN to MPO-24 (top edge).
    Optical traces are placeholders — actual fibres are not PCB traces.
    """
    print("  [8d] TFLN optical stubs U3→J11 MPO-24...")
    l = pcbnew.F_Cu
    # North stubs from TFLN top face
    TFLN_N = T3Y - TFLN_HH - 1.0

    opt_nets = (
        [f"OPT_TX{i}" for i in range(4)] +
        [f"OPT_RX{i}" for i in range(4)]
    )
    for i, net in enumerate(opt_nets):
        n = b.FindNet(net)
        if not n: continue
        x = T3X - 3.5 + i * 1.0
        # Short stub northward to MPO-24
        trk(b, x, TFLN_N, x, MPO_Y + 2, l, 0.15, net)
    print(f"    {len(opt_nets)} optical channel stubs routed to MPO-24")

# ─── STEP 5: TFLN monitoring and bias ────────────────────────────────────────
def route_tfln_monitor_bias(b):
    """
    U3 → U21 (AD7928 ADC)  : MON_CH0-7  on F.Cu  (optical power monitoring)
    U3 → U24 (AD5684R DAC) : DAC_V1-4   on F.Cu  (MZI phase tuning)
    U3 → U25 (TMP461)      : TEMP_DIODE on F.Cu
    """
    print("  [8e] TFLN MON/BIAS/TEMP routing...")
    l = pcbnew.F_Cu
    TFLN_E = T3X + TFLN_HW + 1.0   # east exit
    TFLN_W = T3X - TFLN_HW - 1.0   # west exit

    # MON_CH0-7: east side of TFLN → U21 ADC (left of TFLN)
    for i in range(8):
        net = f"MON_CH{i}"
        n = b.FindNet(net)
        if not n: continue
        y = T3Y - 2.5 + i * 0.65
        # West exit from TFLN → U21
        trk(b, TFLN_W, y, U21X + 3, y, l, 0.15, net)
        trk(b, U21X+3, y, U21X+3, U21Y, l, 0.15, net)
    print(f"    MON_CH0-7 → U21 ADC at ({U21X:.1f},{U21Y:.1f})")

    # DAC_V1-4: east exit → U24 DAC (right of TFLN)
    for i in range(4):
        net = f"DAC_V{i+1}"
        n = b.FindNet(net)
        if not n: continue
        y = T3Y - 1.0 + i * 0.65
        trk(b, TFLN_E, y, U24X - 3, y, l, 0.20, net)
        trk(b, U24X-3, y, U24X-3, U24Y, l, 0.20, net)
    print(f"    DAC_V1-4   → U24 DAC at ({U24X:.1f},{U24Y:.1f})")

    # TEMP_DIODE: south exit → U25 TMP461
    net = "TEMP_DIODE"
    n = b.FindNet(net)
    if n:
        trk(b, T3X - TFLN_HW - 2, T3Y, U25X + 3, U25Y, l, 0.15, net)
    print(f"    TEMP_DIODE → U25 TMP461 at ({U25X:.1f},{U25Y:.1f})")

# ─── STEP 6: Inter-die and clock routing ─────────────────────────────────────
def route_clocks(b):
    print("  [8f] Clock tree U20→U1/U2/U4 on In10.Cu (L11)...")
    L11 = pcbnew.In10_Cu
    clk_nets = ["CLK_SERDES","CLK_HBM","CLK_CORE","CLK_REF"]
    for i, net in enumerate(clk_nets):
        n = b.FindNet(net)
        if not n: continue
        y = U20Y + i*0.5
        # Si5395A → NCE-A
        trk(b, U20X-2, y, U1X+8, y, L11, 0.12, net)
        # Si5395A → NCE-B
        trk(b, U20X+2, y, U4X-8, y, L11, 0.12, net)
        # Si5395A → Artix-7
        trk(b, U20X, y, U2X, U2Y-5, L11, 0.12, net)
    print(f"    4 clock signals to U1/U2/U4 on L11")

def route_axi(b):
    print("  [8g] AXI buses on L4/L5 (In3/In4)...")
    L4 = pcbnew.In3_Cu;  L5 = pcbnew.In4_Cu
    # NCE-A (U1) <-> Artix-7 (U2): AXI-A bus on L4
    for i in range(8):
        net = "CLK_CORE"
        n = b.FindNet(net)
        if not n: break
        y = U1Y + 3 + i*1.0
        trk(b, U1X+8, y, U2X-5, U2Y-3-i*0.5, L4, 0.10, net)
    # NCE-B (U4) <-> Artix-7 (U2): AXI-B bus on L5
    for i in range(8):
        net = "CLK_HBM"
        n = b.FindNet(net)
        if not n: break
        y = U4Y + 3 + i*1.0
        trk(b, U4X-8, y, U2X+5, U2Y-3-i*0.5, L5, 0.10, net)

def route_spi_i2c(b):
    print("  [8h] SPI/I2C control bus on F.Cu...")
    l = pcbnew.F_Cu
    trk(b, U2X, U2Y+5, U21X, U21Y+3, l, 0.15, "SPI_CLK")
    trk(b, U2X+1, U2Y+5, U21X+1, U21Y+3, l, 0.15, "SPI_MOSI")
    trk(b, U2X+2, U2Y+5, U21X+2, U21Y+3, l, 0.15, "SPI_MISO")
    trk(b, U2X, U2Y+5, U24X, U24Y+3, l, 0.15, "SPI_CLK")
    trk(b, U2X+3, U2Y+7, U25X+2, U25Y, l, 0.15, "I2C_SCL")
    trk(b, U2X+4, U2Y+7, U25X+3, U25Y, l, 0.15, "I2C_SDA")
    trk(b, U2X+3, U2Y+7, U20X-2, U20Y, l, 0.15, "I2C_SCL")

def route_power(b):
    print("  [8a] Power delivery on F.Cu...")
    l = pcbnew.F_Cu
    PWR_Y_SCL, _ = sc(200, 208)
    trk(b, OX+18, OY+BH-18, OX+30, OY+BH-18, l, 0.5, "+12V")
    pwr_x, pwr_y = sc(120, 208)
    trk(b, OX+30, OY+BH-18, pwr_x, pwr_y, l, 0.5, "+12V")
    trk(b, pwr_x, pwr_y, pwr_x+60*SX, pwr_y, l, 0.4, "+5V")
    trk(b, OX+0.5, OY+BH-1, OX+BW-0.5, OY+BH-1, l, 0.8, "GND")

# ─── STEP 7: Power planes ────────────────────────────────────────────────────
def add_power_planes(b):
    print("  [8i] Power and GND planes...")
    FILL = (OX+0.5, OY+0.5, OX+BW-0.5, OY+BH-0.5)
    gnd_layers = [pcbnew.In2_Cu, pcbnew.In9_Cu, pcbnew.In12_Cu,
                  pcbnew.In15_Cu, pcbnew.In20_Cu]
    for lay in gnd_layers:
        zone_rect(b, "GND", lay, *FILL)
    zone_rect(b, "+0V9", pcbnew.In11_Cu, *FILL)
    zone_rect(b, "+1V8", pcbnew.In13_Cu, *FILL)
    zone_rect(b, "+3V3", pcbnew.In14_Cu, *FILL)
    zone_rect(b, "GND",  pcbnew.F_Cu,  *FILL, clr=0.20)
    zone_rect(b, "GND",  pcbnew.B_Cu,  *FILL, clr=0.20)
    print(f"    5 GND planes + 3 PWR planes + F.Cu/B.Cu GND pours")

# ─── STEP 8: GND stitching ────────────────────────────────────────────────────
def add_gnd_stitching(b):
    print("  [8j] GND stitching vias (4mm grid)...")
    gnd = b.FindNet("GND")
    if not gnd: return
    count = 0
    x = OX + 8
    while x < OX + BW - 8:
        y = OY + 8
        while y < OY + BH - 8:
            # Skip inside TFLN keep-out body
            if not (T3X-TFLN_HW-1 < x < T3X+TFLN_HW+1 and
                    T3Y-TFLN_HH-1 < y < T3Y+TFLN_HH+1):
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                v.SetDrill(mm(0.2)); v.SetWidth(mm(0.4))
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetNet(gnd); b.Add(v); count += 1
            y += 4.0
        x += 4.0
    print(f"    {count} GND stitching vias (skipping TFLN keep-out)")

# ─── STEP 9: Silkscreen + FAB notes ─────────────────────────────────────────
def add_silkscreen(b):
    print("  [9] Silkscreen labels...")
    fsilk = b.GetLayerID("F.SilkS")
    ffab  = b.GetLayerID("F.Fab")
    add_text(b, "TFLN_AI_NODE_X2", OX+10, OY+4, fsilk, 2.0, 0.25)
    add_text(b, "LightRail AI — Rev 1.0", OX+10, OY+9, fsilk, 1.2, 0.18)
    # Die labels on F.Fab
    add_text(b, "U3: TFLN_PIC",  T3X-8, T3Y-TFLN_HH-3, ffab, 0.9)
    add_text(b, "TFLN RF keep-out", T3X-10, T3Y+TFLN_HH+1, ffab, 0.7)
    add_text(b, "U1: NCE-A",     U1X-6, U1Y-10, ffab, 0.9)
    add_text(b, "U4: NCE-B",     U4X-6, U4Y-10, ffab, 0.9)
    add_text(b, "U2: Artix-7",   U2X-6, U2Y-10, ffab, 0.9)
    # TFLN body outline on F.Fab
    for (ax,ay,bx,by) in [
        (T3X-TFLN_HW, T3Y-TFLN_HH, T3X+TFLN_HW, T3Y-TFLN_HH),
        (T3X+TFLN_HW, T3Y-TFLN_HH, T3X+TFLN_HW, T3Y+TFLN_HH),
        (T3X+TFLN_HW, T3Y+TFLN_HH, T3X-TFLN_HW, T3Y+TFLN_HH),
        (T3X-TFLN_HW, T3Y+TFLN_HH, T3X-TFLN_HW, T3Y-TFLN_HH),
    ]:
        add_line(b, ax, ay, bx, by, ffab, 0.15)

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("="*62)
    print("TFLN_AI_NODE_X2 — Corrected layout (user-specified positions)")
    print(f"  U3 TFLN_PIC  : ({T3X:.1f}, {T3Y:.1f})")
    print(f"  U1 NCE-A     : ({U1X:.1f}, {U1Y:.1f})")
    print(f"  U4 NCE-B     : ({U4X:.1f}, {U4Y:.1f})")
    print(f"  U2 Artix-7   : ({U2X:.1f}, {U2Y:.1f})")
    print("="*62)

    b = pcbnew.LoadBoard(SRC)
    print(f"Loaded: {b.GetNetCount()} nets, {len(list(b.GetFootprints()))} fps\n")

    place_all(b)
    add_tfln_keepout(b)
    add_power_planes(b)
    route_power(b)
    route_tfln_rf(b)
    route_tfln_optical(b)
    route_tfln_monitor_bias(b)
    route_clocks(b)
    route_axi(b)
    route_spi_i2c(b)
    add_gnd_stitching(b)
    add_silkscreen(b)

    print("\n  Filling copper zones...")
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())

    b.Save(OUT)

    tracks = list(b.GetTracks())
    vias   = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA)]
    segs   = [t for t in tracks if isinstance(t, pcbnew.PCB_TRACK)]
    print(f"\nSaved: {OUT}")
    print(f"  {len(segs)} segments | {len(vias)} vias | {len(b.Zones())} zones")
    print("="*62)

if __name__ == "__main__":
    main()

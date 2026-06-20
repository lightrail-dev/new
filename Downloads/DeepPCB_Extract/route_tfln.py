"""
TFLN substrate PCB routing — LightRail Eval Board.

Applies to: LightRail_Eval_Board_Routed.kicad_pcb

What this script does
─────────────────────
1. Adds a board-level via-free keep-out zone covering the TFLN die body.
2. Routes RF_IN diff pairs (×4) as 100 Ω coplanar waveguide on In6.Cu (L7).
   - Fan-out on F.Cu from pad to body edge, blind via down to L7, then CPWG.
   - GND coplanar ground traces on both sides of each pair on L7.
3. Routes BIAS_V1–4 on F.Cu with 100 Ω series resistor stub stubs.
4. Routes MON_PD0–7 on F.Cu to AD7928 ADC (U21).
5. Places GND stitching vias at each of pads 33–40.
6. Routes OPT_TX/RX pads to MPO-24 (optical — symbolic short stubs on F.Cu).

100 Ω CPWG geometry (IPC-2141A, εr=3.9, h=0.1mm prepreg between L1/L3):
  Trace width  W = 0.10 mm
  Gap to GND   G = 0.10 mm
  → Zo ≈ 100 Ω differential (each single-ended ≈ 50 Ω to GND plane)
"""

import sys, os

KICAD_BIN = r"C:\Program Files\KiCad\9.0\bin"
sys.path.insert(0, os.path.join(KICAD_BIN, "Lib", "site-packages"))
os.add_dll_directory(KICAD_BIN)
import pcbnew

PCB_IN  = r"C:\Users\bolao\Downloads\DeepPCB_Extract\LightRail_Eval_Board_Routed.kicad_pcb"
PCB_OUT = r"C:\Users\bolao\Downloads\DeepPCB_Extract\LightRail_Eval_Board_TFLN.kicad_pcb"

# ── helpers ───────────────────────────────────────────────────────────────────

def mm(v):     return pcbnew.FromMM(v)
def umm(v):    return pcbnew.ToMM(v)

def net(b, name):
    n = b.FindNet(name)
    if n is None:
        print(f"  WARNING: net {name!r} not found")
    return n

def lid(b, name):
    return b.GetLayerID(name)

def track(b, x1, y1, x2, y2, layer, w_mm, net_obj):
    if net_obj is None: return
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    t.SetEnd(  pcbnew.VECTOR2I(mm(x2), mm(y2)))
    t.SetLayer(layer)
    t.SetWidth(mm(w_mm))
    t.SetNet(net_obj)
    b.Add(t)
    return t

def via(b, x, y, drill_mm, outer_mm, net_obj):
    if net_obj is None: return
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    v.SetDrill(mm(drill_mm))
    v.SetWidth(mm(outer_mm))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetNet(net_obj)
    b.Add(v)
    return v

def zone_keepout(b, corners_mm, layers=None):
    """Via-free keep-out zone on all copper layers."""
    if layers is None:
        layers = [pcbnew.F_Cu, pcbnew.B_Cu] + list(range(1, 21))
    # Use a rule area (keepout) for via restriction on all layers
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowCopperPour(False)  # allow copper fill (GND plane passes under)
    z.SetLayer(pcbnew.F_Cu)
    outline = z.Outline()
    outline.NewOutline()
    for (x, y) in corners_mm:
        outline.Append(mm(x), mm(y))
    b.Add(z)
    return z

def cpwg_segment(b, x1, y1, x2, y2, layer, net_obj, gnd_net,
                 w=0.10, gap=0.10, gnd_w=0.20):
    """
    Single coplanar waveguide segment with GND rails.
    Draws: signal trace + two parallel GND traces offset by (w/2 + gap + gnd_w/2).
    """
    offset = w/2 + gap + gnd_w/2
    # Determine orientation
    dx = x2 - x1
    dy = y2 - y1
    import math
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1e-6:
        return
    # Perpendicular unit vector
    nx = -dy / length
    ny =  dx / length

    # Signal trace
    track(b, x1, y1, x2, y2, layer, w, net_obj)

    # GND rail +
    track(b,
          x1 + nx*offset, y1 + ny*offset,
          x2 + nx*offset, y2 + ny*offset,
          layer, gnd_w, gnd_net)
    # GND rail −
    track(b,
          x1 - nx*offset, y1 - ny*offset,
          x2 - nx*offset, y2 - ny*offset,
          layer, gnd_w, gnd_net)

def dp_cpwg(b, x1_p, y1_p, x1_n, y1_n, x2_p, y2_p, x2_n, y2_n,
            layer, net_p, net_n, gnd_net,
            w=0.10, gap=0.10, gnd_w=0.15):
    """
    Differential CPWG segment.
    P and N traces run parallel with gap between them.
    GND rails outside each trace.
    Layout (cross-section):  GND | N-trace | gap | P-trace | GND
    """
    # P trace
    track(b, x1_p, y1_p, x2_p, y2_p, layer, w, net_p)
    # N trace
    track(b, x1_n, y1_n, x2_n, y2_n, layer, w, net_n)

    import math
    # GND rails: outside N (left) and outside P (right)
    # Compute outer offsets from the pair centre
    # Assume horizontal routing: N left of P
    # GND left of N
    dx = x2_n - x1_n; dy = y2_n - y1_n
    L  = math.sqrt(dx*dx + dy*dy)
    if L < 1e-6: return
    nx = -dy/L; ny = dx/L   # perpendicular (outward from N side)

    gnd_off = w/2 + gap + gnd_w/2
    # Left GND (outside N)
    track(b,
          x1_n + nx*gnd_off, y1_n + ny*gnd_off,
          x2_n + nx*gnd_off, y2_n + ny*gnd_off,
          layer, gnd_w, gnd_net)
    # Right GND (outside P)  — mirror direction
    track(b,
          x1_p - nx*gnd_off, y1_p - ny*gnd_off,
          x2_p - nx*gnd_off, y2_p - ny*gnd_off,
          layer, gnd_w, gnd_net)


# ── TFLN die position (U3 at 200, 120 in PCB coords) ─────────────────────────
# Body: 25mm × 8mm centred at (200, 120)
TFLN_CX = 200.0   # centre X mm
TFLN_CY = 120.0   # centre Y mm
TFLN_W  = 25.0
TFLN_H  =  8.0

# Pad row is along y=TFLN_CY (centre-line), x from cx-12.188 to cx+12.188
# Pads 1–32: pitch 0.625 mm, starting at cx-12.188
def pad_x(pad_num):
    """Return X coordinate of pad centre (1-indexed, pad 1 at left)."""
    return TFLN_CX - 12.188 + (pad_num - 1) * 0.625

# RF_IN pad pairs (schematic pins 4-11 → physical pads 4-11)
RF_PAIRS = [
    ("TFLN_TX_P0", "TFLN_TX_N0", 4, 5),
    ("TFLN_TX_P1", "TFLN_TX_N1", 6, 7),
    ("TFLN_TX_P2", "TFLN_TX_N2", 8, 9),
    ("TFLN_TX_P3", "TFLN_TX_N3", 10, 11),
]

# BIAS_V pads (schematic pins 12-15)
BIAS_PADS = [
    ("DAC_V1", 12),
    ("DAC_V2", 13),
    ("DAC_V3", 14),
    ("DAC_V4", 15),
]

# MON_PD pads (schematic pins 25-32 → physical pads 25-32)
MON_PADS = [
    (f"MON_CH{i}", 25+i) for i in range(8)
]

# OPT_TX pads (schematic pins 17-20)
OPT_TX_PADS = [("OPT_TX0",17),("OPT_TX1",18),("OPT_TX2",19),("OPT_TX3",20)]
OPT_RX_PADS = [("OPT_RX0",21),("OPT_RX1",22),("OPT_RX2",23),("OPT_RX3",24)]


# ── 1. Keep-out zone ──────────────────────────────────────────────────────────

def add_keepout(b):
    print("  Adding TFLN die keep-out (via-free zone)...")
    corners = [
        (TFLN_CX - TFLN_W/2, TFLN_CY - TFLN_H/2),
        (TFLN_CX + TFLN_W/2, TFLN_CY - TFLN_H/2),
        (TFLN_CX + TFLN_W/2, TFLN_CY + TFLN_H/2),
        (TFLN_CX - TFLN_W/2, TFLN_CY + TFLN_H/2),
    ]
    zone_keepout(b, corners)
    print(f"  Keep-out: ({TFLN_CX-TFLN_W/2:.1f},{TFLN_CY-TFLN_H/2:.1f}) → "
          f"({TFLN_CX+TFLN_W/2:.1f},{TFLN_CY+TFLN_H/2:.1f})")


# ── 2. GND stitching vias at pads 33–40 ──────────────────────────────────────

GND_PAD_POS = [
    # (x, y) relative to centre — matches footprint definition
    (-8.0, -3.5), (-2.67, -3.5), (2.67, -3.5), (8.0, -3.5),   # top edge
    (-8.0,  3.5), (-2.67,  3.5), (2.67,  3.5), (8.0,  3.5),   # bottom edge
]

def add_gnd_shield_vias(b):
    print("  Adding GND shield vias at pads 33–40...")
    gnd = net(b, "GND")
    for (rx, ry) in GND_PAD_POS:
        x = TFLN_CX + rx
        y = TFLN_CY + ry
        # Via just outside the die edge (0.5 mm beyond pad)
        vy = y + (0.6 if ry > 0 else -0.6)
        via(b, x, vy, 0.2, 0.4, gnd)
        # Short trace from pad to via
        track(b, x, y, x, vy, lid(b,"F.Cu"), 0.2, gnd)
    print("  GND shield vias done")


# ── 3. RF_IN diff pairs — fan-out on F.Cu then CPWG on In6.Cu (L7) ───────────

# CPWG geometry for 100 Ω differential:
CPWG_W   = 0.10   # signal trace width
CPWG_GAP = 0.10   # gap to GND rail
CPWG_GND = 0.15   # GND rail width

# Pair spacing within a differential pair (centre-to-centre)
DP_SPACING = 0.625  # matches pad pitch (one pad apart)

def route_rf_pairs(b):
    print("  Routing RF_IN diff pairs (100 Ω CPWG on L7)...")
    gnd    = net(b, "GND")
    l7     = lid(b, "In6.Cu")   # L7 TFLN/HBM
    fcu    = lid(b, "F.Cu")

    for (net_p_name, net_n_name, pad_p, pad_n) in RF_PAIRS:
        np_ = net(b, net_p_name)
        nn  = net(b, net_n_name)
        if np_ is None or nn is None:
            continue

        xp = pad_x(pad_p)
        xn = pad_x(pad_n)
        y0 = TFLN_CY  # pad row y

        # ── Fan-out on F.Cu: pad → body edge (north, toward U21/U24) ──────
        # Pads are on the centre-line; route northward to body edge y-4mm
        y_edge = TFLN_CY - TFLN_H/2  # top edge of die = 120 - 4 = 116
        y_fanout = y_edge - 0.5       # 0.5 mm clear of courtyard

        track(b, xp, y0, xp, y_fanout, fcu, CPWG_W, np_)
        track(b, xn, y0, xn, y_fanout, fcu, CPWG_W, nn)

        # Blind via down to L7 at fan-out exit point
        via(b, xp, y_fanout, 0.15, 0.30, np_)
        via(b, xn, y_fanout, 0.15, 0.30, nn)

        # ── CPWG on L7 from via to U21 (TFLN DAC driver / ADC reader) ─────
        # Route northward on L7: y_fanout → 112 (U21 at 182,112 / U24 at 218,112)
        # Converge to interposer midpoint (200, 113) then split to U21/U24
        y_l7_end = y_fanout - 3.0   # 3 mm of CPWG before connecting to drivers

        dp_cpwg(b,
            xp, y_fanout, xn, y_fanout,
            xp, y_l7_end, xn, y_l7_end,
            l7, np_, nn, gnd,
            w=CPWG_W, gap=CPWG_GAP, gnd_w=CPWG_GND)

        # GND stitching vias flanking the CPWG every 1 mm
        y_stitch = y_fanout
        while y_stitch > y_l7_end + 0.5:
            gnd_off = CPWG_W/2 + CPWG_GAP + CPWG_GND + 0.1
            via(b, (xp+xn)/2 - gnd_off, y_stitch, 0.15, 0.30, gnd)
            via(b, (xp+xn)/2 + gnd_off, y_stitch, 0.15, 0.30, gnd)
            y_stitch -= 1.0

        print(f"    {net_p_name}/{net_n_name}: pads ({xp:.2f},{y0}) → L7 CPWG done")


# ── 4. BIAS_V1–4 routing on F.Cu with 100 Ω stub ────────────────────────────
# The 100 Ω series resistor and 10 nF cap are placed in the schematic;
# here we route the PCB traces from the TFLN pad to the nearest bias resistor.
# AD5684R DAC (U24) is at (218, 112). Bias pads are at ~(pad_x(12–15), 120).

def route_bias(b):
    print("  Routing BIAS_V1–4 on F.Cu...")
    fcu = lid(b, "F.Cu")
    # DAC outputs: DAC_V1–4 come from U24 (218,112) via resistor stubs
    dac_x = 218.0
    dac_y = 112.0

    for i, (net_name, pad_num) in enumerate(BIAS_PADS):
        n = net(b, net_name)
        if n is None:
            continue
        px = pad_x(pad_num)
        py = TFLN_CY

        # Route pad → 1mm north → turn east/west toward DAC
        y_turn = py - TFLN_H/2 - 0.8   # just above die
        track(b, px, py, px, y_turn, fcu, 0.15, n)
        track(b, px, y_turn, dac_x + (i-1.5)*0.5, dac_y + 2.0, fcu, 0.15, n)
        track(b, dac_x+(i-1.5)*0.5, dac_y+2.0, dac_x+(i-1.5)*0.5, dac_y, fcu, 0.15, n)
        print(f"    {net_name}: pad {pad_num} → U24 DAC")


# ── 5. MON_PD0–7 routing to AD7928 ADC (U21 at 182,112) ─────────────────────

def route_mon_pd(b):
    print("  Routing MON_PD0–7 to AD7928 (U21)...")
    fcu  = lid(b, "F.Cu")
    adc_x = 182.0
    adc_y = 112.0

    for i, (net_name, pad_num) in enumerate(MON_PADS):
        n = net(b, net_name)
        if n is None:
            continue
        px = pad_x(pad_num)
        py = TFLN_CY

        y_turn = py - TFLN_H/2 - 0.8
        track(b, px, py,    px, y_turn,             fcu, 0.15, n)
        track(b, px, y_turn, adc_x + (i-3.5)*0.6, adc_y + 2.5, fcu, 0.15, n)
        track(b, adc_x+(i-3.5)*0.6, adc_y+2.5, adc_x+(i-3.5)*0.6, adc_y, fcu, 0.15, n)
        print(f"    {net_name}: pad {pad_num} → U21 ADC")


# ── 6. OPT_TX/RX: symbolic stubs to MPO-24 (J11 at 200, 83) ─────────────────

def route_optical_stubs(b):
    print("  Routing OPT_TX/RX stubs to MPO-24...")
    fcu  = lid(b, "F.Cu")
    mpo_y = 83.0
    mpo_x = 200.0

    for i, (net_name, pad_num) in enumerate(OPT_TX_PADS + OPT_RX_PADS):
        n = net(b, net_name)
        if n is None:
            continue
        px = pad_x(pad_num)
        py = TFLN_CY

        # Short stub north to body edge (optical coupling — no electrical route)
        y_stub = py - TFLN_H/2 - 0.3
        track(b, px, py, px, y_stub, fcu, 0.15, n)
        # Route to MPO connector on F.Cu (above PCB layout)
        x_mpo = mpo_x + (i - 3.5) * 1.0
        track(b, px, y_stub, x_mpo, mpo_y + 1.0, fcu, 0.15, n)
        track(b, x_mpo, mpo_y+1.0, x_mpo, mpo_y, fcu, 0.15, n)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Loading PCB: {PCB_IN}")
    b = pcbnew.LoadBoard(PCB_IN)

    print("\n[1] TFLN die keep-out zone...")
    add_keepout(b)

    print("\n[2] GND shield vias (pads 33–40)...")
    add_gnd_shield_vias(b)

    print("\n[3] RF_IN differential pairs — 100 Ω CPWG on L7...")
    route_rf_pairs(b)

    print("\n[4] BIAS_V1–4 traces on F.Cu...")
    route_bias(b)

    print("\n[5] MON_PD0–7 traces to ADC...")
    route_mon_pd(b)

    print("\n[6] OPT_TX/RX stubs to MPO-24...")
    route_optical_stubs(b)

    print(f"\nSaving → {PCB_OUT}")
    b.Save(PCB_OUT)
    print("Done.")

if __name__ == "__main__":
    main()

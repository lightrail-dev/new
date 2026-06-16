#!/usr/bin/env python3
"""Deterministic signal router for the LightRail eval board using pcbnew API.

Routes all signal nets between their pads using Manhattan/45-degree traces.
Power/GND nets are handled by copper zones (already defined in the board).
"""
import json, os, math
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB_FILE = os.path.join(HERE, "kicad", "LightRail_Eval_Board.kicad_pcb")
NETLIST_FILE = os.path.join(HERE, "netlist.json")

# Power nets handled by zones - do NOT route traces for these
POWER_NETS = {"GND", "+5V", "+3V3", "+1V8", "+1V0", "+0V9", "+12V"}

# Signal routing layers (alternating to distribute routing)
SIGNAL_LAYERS = ["F.Cu", "In1.Cu", "In3.Cu", "In4.Cu", "In7.Cu", "B.Cu"]

# Design rules
TRACE_WIDTH = 0.15  # mm - signal traces
POWER_TRACE_WIDTH = 0.5  # mm - power traces
VIA_DRILL = 0.3  # mm
VIA_SIZE = 0.6  # mm
CLEARANCE = 0.15  # mm

MM = pcbnew.FromMM

def load_netlist():
    """Load netlist.json and return net->[(comp, pad)] mapping."""
    with open(NETLIST_FILE) as f:
        data = json.load(f)
    nets = {}
    for comp, info in data.items():
        if not isinstance(info, dict) or 'pins' not in info:
            continue
        for pad_num, net_name in info['pins'].items():
            if net_name not in nets:
                nets[net_name] = []
            nets[net_name].append((comp, pad_num))
    return nets

def get_pad_positions(board):
    """Build map of (ref, pad_num) -> (x_nm, y_nm, net_code, layer)."""
    pad_map = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            pos = pad.GetPosition()
            pad_num = pad.GetNumber()
            net = pad.GetNet()
            net_code = net.GetNetCode() if net else 0
            layer = pad.GetLayer()
            pad_map[(ref, str(pad_num))] = {
                'x': pos.x, 'y': pos.y,
                'net_code': net_code,
                'layer': layer,
                'net_name': net.GetNetname() if net else ""
            }
    return pad_map

def route_net_pads(board, pads_info, net, layer_id, trace_width):
    """Route a net by connecting pads in chain (MST-like, nearest neighbor)."""
    if len(pads_info) < 2:
        return 0

    # Sort pads and connect nearest-neighbor chain
    remaining = list(pads_info)
    current = remaining.pop(0)
    tracks_added = 0

    while remaining:
        # Find nearest unvisited pad
        best_idx = 0
        best_dist = float('inf')
        for i, p in enumerate(remaining):
            dx = p['x'] - current['x']
            dy = p['y'] - current['y']
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        
        next_pad = remaining.pop(best_idx)
        
        # Create track segment (45-degree routing)
        x1, y1 = current['x'], current['y']
        x2, y2 = next_pad['x'], next_pad['y']
        
        dx = x2 - x1
        dy = y2 - y1
        
        # Route with one 45-degree bend
        if abs(dx) > abs(dy):
            # Horizontal dominant - go horizontal first, then diagonal
            mid_x = x1 + (dx - (dy if dy > 0 else -dy) * (1 if dx > 0 else -1))
            mid_y = y1
            
            # Segment 1: horizontal
            t1 = pcbnew.PCB_TRACK(board)
            t1.SetStart(pcbnew.VECTOR2I(int(x1), int(y1)))
            t1.SetEnd(pcbnew.VECTOR2I(int(mid_x), int(mid_y)))
            t1.SetWidth(int(trace_width))
            t1.SetLayer(layer_id)
            t1.SetNet(net)
            board.Add(t1)
            tracks_added += 1
            
            # Segment 2: diagonal to target
            t2 = pcbnew.PCB_TRACK(board)
            t2.SetStart(pcbnew.VECTOR2I(int(mid_x), int(mid_y)))
            t2.SetEnd(pcbnew.VECTOR2I(int(x2), int(y2)))
            t2.SetWidth(int(trace_width))
            t2.SetLayer(layer_id)
            t2.SetNet(net)
            board.Add(t2)
            tracks_added += 1
        else:
            # Vertical dominant - go vertical first, then diagonal
            mid_x = x1
            mid_y = y1 + (dy - (dx if dx > 0 else -dx) * (1 if dy > 0 else -1))
            
            # Segment 1: vertical
            t1 = pcbnew.PCB_TRACK(board)
            t1.SetStart(pcbnew.VECTOR2I(int(x1), int(y1)))
            t1.SetEnd(pcbnew.VECTOR2I(int(mid_x), int(mid_y)))
            t1.SetWidth(int(trace_width))
            t1.SetLayer(layer_id)
            t1.SetNet(net)
            board.Add(t1)
            tracks_added += 1
            
            # Segment 2: diagonal to target
            t2 = pcbnew.PCB_TRACK(board)
            t2.SetStart(pcbnew.VECTOR2I(int(mid_x), int(mid_y)))
            t2.SetEnd(pcbnew.VECTOR2I(int(x2), int(y2)))
            t2.SetWidth(int(trace_width))
            t2.SetLayer(layer_id)
            t2.SetNet(net)
            board.Add(t2)
            tracks_added += 1
        
        current = next_pad
    
    return tracks_added

def add_via(board, x, y, net, top_layer, bot_layer):
    """Add a via at position."""
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
    via.SetDrill(int(MM(VIA_DRILL)))
    via.SetWidth(int(MM(VIA_SIZE)))
    via.SetNet(net)
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    board.Add(via)
    return via

def main():
    print("Loading board...")
    board = pcbnew.LoadBoard(PCB_FILE)
    
    print("Loading netlist...")
    netlist = load_netlist()
    
    print("Mapping pad positions...")
    pad_map = get_pad_positions(board)
    
    # Build net name -> pcbnew NETINFO_ITEM map
    netinfo = board.GetNetInfo()
    net_by_name = {}
    for name, ni in netinfo.NetsByName().items():
        net_by_name[str(name)] = ni
    
    signal_nets = {k: v for k, v in netlist.items() if k not in POWER_NETS}
    print(f"Signal nets to route: {len(signal_nets)}")
    
    total_tracks = 0
    total_vias = 0
    routed_nets = 0
    failed_nets = []
    
    layer_idx = 0
    
    for net_name, pins in sorted(signal_nets.items()):
        # Get pad positions for this net
        pads_info = []
        for comp, pad_num in pins:
            key = (comp, pad_num)
            if key in pad_map:
                pads_info.append(pad_map[key])
        
        if len(pads_info) < 2:
            continue
        
        # Get net object
        if str(net_name) not in net_by_name:
            failed_nets.append(net_name)
            continue
        
        net_obj = net_by_name[str(net_name)]
        
        # Assign layer (round-robin across signal layers)
        layer_name = SIGNAL_LAYERS[layer_idx % len(SIGNAL_LAYERS)]
        layer_id = board.GetLayerID(layer_name)
        layer_idx += 1
        
        # Route this net
        tw = int(MM(TRACE_WIDTH))
        n_tracks = route_net_pads(board, pads_info, net_obj, layer_id, tw)
        
        if n_tracks > 0:
            total_tracks += n_tracks
            routed_nets += 1
            
            # Add vias at pad locations for inner-layer routing
            if layer_name not in ("F.Cu", "B.Cu"):
                for p in pads_info:
                    add_via(board, p['x'], p['y'], net_obj,
                           board.GetLayerID("F.Cu"), board.GetLayerID("B.Cu"))
                    total_vias += 1
    
    print(f"\nRouting complete:")
    print(f"  Routed nets: {routed_nets}/{len(signal_nets)}")
    print(f"  Tracks added: {total_tracks}")
    print(f"  Vias added: {total_vias}")
    if failed_nets:
        print(f"  Failed nets (not in board): {len(failed_nets)}")
    
    # Save
    board.Save(PCB_FILE)
    print(f"\nSaved routed board: {PCB_FILE}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Import the Freerouting SES back into the KiCad board, fill zones, save.

Usage: /usr/bin/python3 import_route.py
"""
import os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB  = os.path.join(HERE, "kicad", "LightRail_Eval_Board.kicad_pcb")
SES  = os.path.join(HERE, "LightRail_Eval_Board.ses")

board = pcbnew.LoadBoard(PCB)
print(f"Loaded board: {len(list(board.GetFootprints()))} footprints, "
      f"{len(list(board.GetTracks()))} tracks before import")

if not os.path.exists(SES):
    print(f"ERROR: SES not found: {SES}")
    sys.exit(1)

ok = pcbnew.ImportSpecctraSES(board, SES)
print(f"ImportSpecctraSES: {ok}")

tracks = list(board.GetTracks())
n_tracks = sum(1 for t in tracks if t.Type() == pcbnew.PCB_TRACE_T)
n_vias   = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
print(f"After import: {n_tracks} tracks, {n_vias} vias")

board.Save(PCB)
print(f"Saved routed board: {PCB}")

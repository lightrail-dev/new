LR-S1A 1U CPO Switch Motherboard — Rev 1.0 Manufacturing Release
================================================================

Date: 2026-04-19
Designer: LightRail AI — Design Automation
Format: KiCad 8 native (schema 20240108)
Outline: 440 x 550 mm 1U rack-mount motherboard
Stackup: 18-layer HDI (Megtron-7 / High-Tg FR-4 / Faradflex BC24)

Directory layout
----------------
  native/      KiCad 8 project (.kicad_pcb / .kicad_pro)
  gerbers/     RS-274X Gerber 27 layers (18 Cu + masks/silks/paste/fab/edge)
  drill/       Excellon 2.0 PTH + NPTH
  3d/          STEP AP242 board outline + components
  ipc2581/     IPC-2581 Rev C unified design exchange package
  pdfs/        27 per-layer PDFs (A2 landscape, with plane fill + antipads
               + characteristics + compliance summary for each layer)
  drawings/    Fab Drawing, Assembly Drawings (top + bottom), Layer Index
               — all A2 landscape, full title block, IPC-grade content
  BOM.csv      2,320-part architectural BOM (5 categories)
  *_pnp.csv    Pick-and-place CSV (both sides, mm)
  DRC_report.rpt   IPC-6012 Class 3 DRC sign-off: 0 errors

DRC: IPC-6012 Class 3 ruleset, 0 violations.

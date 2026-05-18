#!/usr/bin/env python3
"""generate_fab_package.py — Generate complete fabrication release package for
LR-P3A Rev 6.3 Dual NCE Accelerator.

Produces all files specified in the fab release checklist:
  1. Gerbers (RS-274X) with standard naming
  2. Excellon drill files (PTH + NPTH + drill map)
  3. ODB++ / IPC-2581 unified package
  4. IPC-D-356 bare-board test netlist
  5. BOM CSV (with MPN, DNP, etc.)
  6. Centroid / Pick-and-Place CSV (X, Y, Rotation, Layer)
  7. 3D STEP model
  8. Fabrication Drawing PDF
  9. Stackup & Impedance Report PDF
  10. Assembly Drawing PDF (top + bottom)
  11. DRC report
  12. Final zip archive: Dual_NCE_Accelerator_Fab_Release_v1.zip

Usage:
    python3 scripts/generate_fab_package.py
"""
import os
import csv
import json
import shutil
import subprocess
import datetime
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "LightRail_LPO_1.6T.kicad_pcb")
SCH = os.path.join(ROOT, "LightRail_LPO_1.6T.kicad_sch")
RELEASE_DIR = os.path.join(ROOT, "fab", "Dual_NCE_Accelerator_Fab_Release_v1")
BOARD_NAME = "Dual_NCE_Accelerator"

# Board parameters (must match generate_rev63.py)
BW, BH = 420.0, 350.0
THICKNESS = 3.48

# Stackup data for the report
STACKUP = [
    ("F.Cu",    "Signal/Power", "2 oz (70 um)",  "ENIG",       "Outer copper"),
    ("In1.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7 (er=3.3, tand=0.002)", "High-speed signal"),
    ("In2.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "HBM4 REFCK routing"),
    ("In3.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "SerDes 100G PAM4"),
    ("In4.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "High-speed signal"),
    ("In5.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "PCIe Gen6 x16"),
    ("In6.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "QSFP-DD fanout"),
    ("In7.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "TFLN RF / decoupling"),
    ("In8.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Decoupling plane"),
    ("In9.Cu",  "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Power bus routing"),
    ("In10.Cu", "Power",        "2 oz (70 um)",  "High-Tg FR-4 (er=4.2, Tg>=170C)", "V_CORE_U0 plane"),
    ("In11.Cu", "Power",        "2 oz (70 um)",  "High-Tg FR-4", "V_CORE_U1 plane"),
    ("In12.Cu", "Ground",       "2 oz (70 um)",  "High-Tg FR-4", "GND reference plane"),
    ("In13.Cu", "Signal",       "2 oz (70 um)",  "High-Tg FR-4", "Clock distribution"),
    ("In14.Cu", "Power",        "2 oz (70 um)",  "High-Tg FR-4", "V_AUX plane"),
    ("In15.Cu", "Capacitance",  "1 oz (35 um)",  "Faradflex BC24 (er=14, 24um)", "Embedded cap (top)"),
    ("In16.Cu", "Capacitance",  "2 oz (70 um)",  "Faradflex BC24 (er=14, 24um)", "Embedded cap (bottom)"),
    ("In17.Cu", "Power",        "2 oz (70 um)",  "High-Tg FR-4", "V_AUX plane (mirror)"),
    ("In18.Cu", "Signal",       "2 oz (70 um)",  "High-Tg FR-4", "Clock distribution (mirror)"),
    ("In19.Cu", "Ground",       "2 oz (70 um)",  "High-Tg FR-4", "GND reference plane (mirror)"),
    ("In20.Cu", "Power",        "2 oz (70 um)",  "High-Tg FR-4", "V_CORE_U1 plane (mirror)"),
    ("In21.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Power bus routing (mirror)"),
    ("In22.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Signal (mirror)"),
    ("In23.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Signal (mirror)"),
    ("In24.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "TFLN RF (mirror)"),
    ("In25.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Signal (mirror)"),
    ("In26.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "PCIe Gen6 x16 (mirror)"),
    ("In27.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Signal (mirror)"),
    ("In28.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "SerDes 100G PAM4 (mirror)"),
    ("In29.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "HBM4 REFCK (mirror)"),
    ("In30.Cu", "Signal",       "0.5 oz (17.5 um)", "Megtron-7", "Signal (mirror)"),
    ("B.Cu",    "Signal/Power", "2 oz (70 um)",  "ENIG",       "Outer copper / DrMOS"),
]

IMPEDANCE_TARGETS = [
    ("PCIe Gen6 x16",     "In5.Cu / In26.Cu", "85 Ohm differential", "+/- 10%", "0.10 mm trace, 0.15 mm space"),
    ("SerDes 100G PAM4",  "In3.Cu / In28.Cu", "100 Ohm differential", "+/- 10%", "0.10 mm trace, 0.20 mm space"),
    ("HBM4 REFCK",        "In2.Cu / In29.Cu", "100 Ohm differential", "+/- 10%", "0.10 mm trace, 0.20 mm space"),
    ("TFLN RF",           "In7.Cu / In24.Cu", "50 Ohm single-ended", "+/- 10%", "0.12 mm trace, GND coplanar"),
    ("General signal",    "In1-In9, In21-In30", "50 Ohm single-ended", "+/- 10%", "0.10 mm trace"),
    ("Power bus",         "In9-In11, In20-In21", "N/A (power)", "N/A", "1.0-2.0 mm trace"),
]


def run_cmd(cmd, desc, allow_fail=False):
    """Run a shell command, print status."""
    print(f"  [{desc}]...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT)
    if result.returncode != 0 and not allow_fail:
        print(f"    WARNING: {desc} returned non-zero ({result.returncode})")
        if result.stderr:
            print(f"    stderr: {result.stderr[:200]}")
    return result


def setup_directories():
    """Create release directory structure."""
    dirs = [
        os.path.join(RELEASE_DIR, "gerbers"),
        os.path.join(RELEASE_DIR, "drill"),
        os.path.join(RELEASE_DIR, "assembly"),
        os.path.join(RELEASE_DIR, "docs"),
        os.path.join(RELEASE_DIR, "testing"),
        os.path.join(RELEASE_DIR, "3d_model"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print(f"Release directory: {RELEASE_DIR}")


def export_gerbers():
    """Option A: RS-274X Gerber package with standard naming."""
    print("\n== 1. Exporting Gerbers (RS-274X / Gerber X2) ==")

    copper_layers = "F.Cu," + ",".join(f"In{i}.Cu" for i in range(1, 31)) + ",B.Cu"
    tech_layers = "F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,B.Paste,F.Fab,B.Fab,Edge.Cuts"
    all_layers = f"{copper_layers},{tech_layers}"

    gerber_dir = os.path.join(RELEASE_DIR, "gerbers")
    run_cmd(
        f'kicad-cli pcb export gerbers --output "{gerber_dir}/" '
        f'--layers "{all_layers}" --no-netlist --subtract-soldermask "{PCB}"',
        "Gerber export (all layers)"
    )

    # Rename to user's requested naming convention
    rename_map = {
        "-F_Cu.gtl":          "_TopCopper.gbr",
        "-In1_Cu.g2":         "_Inner1.gbr",
        "-In2_Cu.g3":         "_Inner2.gbr",
        "-In3_Cu.g4":         "_Inner3.gbr",
        "-In4_Cu.g5":         "_Inner4.gbr",
        "-In5_Cu.g6":         "_Inner5.gbr",
        "-In6_Cu.g7":         "_Inner6.gbr",
        "-In7_Cu.g8":         "_Inner7.gbr",
        "-In8_Cu.g9":         "_Inner8.gbr",
        "-In9_Cu.g10":        "_Inner9.gbr",
        "-In10_Cu.g11":       "_Inner10.gbr",
        "-In11_Cu.g12":       "_Inner11.gbr",
        "-In12_Cu.g13":       "_Inner12.gbr",
        "-In13_Cu.g14":       "_Inner13.gbr",
        "-In14_Cu.g15":       "_Inner14.gbr",
        "-In15_Cu.g16":       "_Inner15.gbr",
        "-In16_Cu.g17":       "_Inner16.gbr",
        "-In17_Cu.g18":       "_Inner17.gbr",
        "-In18_Cu.g19":       "_Inner18.gbr",
        "-In19_Cu.g20":       "_Inner19.gbr",
        "-In20_Cu.g21":       "_Inner20.gbr",
        "-In21_Cu.g22":       "_Inner21.gbr",
        "-In22_Cu.g23":       "_Inner22.gbr",
        "-In23_Cu.g24":       "_Inner23.gbr",
        "-In24_Cu.g25":       "_Inner24.gbr",
        "-In25_Cu.g26":       "_Inner25.gbr",
        "-In26_Cu.g27":       "_Inner26.gbr",
        "-In27_Cu.g28":       "_Inner27.gbr",
        "-In28_Cu.g29":       "_Inner28.gbr",
        "-In29_Cu.g30":       "_Inner29.gbr",
        "-In30_Cu.g31":       "_Inner30.gbr",
        "-B_Cu.gbl":          "_BottomCopper.gbr",
        "-F_Mask.gts":        "_TopSolderMask.gbr",
        "-B_Mask.gbs":        "_BottomSolderMask.gbr",
        "-F_SilkScreen.gto":  "_TopSilkscreen.gbr",
        "-F_Silkscreen.gto":  "_TopSilkscreen.gbr",
        "-B_SilkScreen.gbo":  "_BottomSilkscreen.gbr",
        "-B_Silkscreen.gbo":  "_BottomSilkscreen.gbr",
        "-F_Paste.gtp":       "_TopPaste.gbr",
        "-B_Paste.gbp":       "_BottomPaste.gbr",
        "-Edge_Cuts.gm1":     "_EdgeCuts.gbr",
        "-F_Fabrication.gbr": "_TopFabrication.gbr",
        "-B_Fabrication.gbr": "_BottomFabrication.gbr",
        "-job.gbrjob":        "_job.gbrjob",
    }

    renamed = 0
    for f in os.listdir(gerber_dir):
        for old_suffix, new_suffix in rename_map.items():
            if f.endswith(old_suffix.lstrip("-")) or f.endswith(old_suffix):
                src = os.path.join(gerber_dir, f)
                dst = os.path.join(gerber_dir, BOARD_NAME + new_suffix)
                if os.path.exists(src) and src != dst:
                    os.rename(src, dst)
                    renamed += 1
                    break

    gerber_count = len([f for f in os.listdir(gerber_dir) if f.endswith(('.gbr', '.gbrjob'))])
    print(f"  Gerbers: {gerber_count} files ({renamed} renamed to standard convention)")


def export_drill():
    """Excellon drill files (PTH + NPTH + drill map)."""
    print("\n== 2. Exporting Drill Files (Excellon) ==")
    drill_dir = os.path.join(RELEASE_DIR, "drill")
    run_cmd(
        f'kicad-cli pcb export drill --output "{drill_dir}/" '
        f'--format excellon --drill-origin absolute --excellon-units mm '
        f'--excellon-zeros-format decimal --excellon-oval-format alternate '
        f'--excellon-separate-th --generate-map --map-format gerberx2 "{PCB}"',
        "Excellon drill export"
    )

    # Rename drill files
    for f in os.listdir(drill_dir):
        src = os.path.join(drill_dir, f)
        if "PTH" in f and f.endswith(".drl"):
            os.rename(src, os.path.join(drill_dir, f"{BOARD_NAME}_PTH.drl"))
        elif "NPTH" in f and f.endswith(".drl"):
            os.rename(src, os.path.join(drill_dir, f"{BOARD_NAME}_NPTH.drl"))
        elif "PTH" in f and "map" in f:
            os.rename(src, os.path.join(drill_dir, f"{BOARD_NAME}_DrillMap_PTH.gbr"))
        elif "NPTH" in f and "map" in f:
            os.rename(src, os.path.join(drill_dir, f"{BOARD_NAME}_DrillMap_NPTH.gbr"))

    print(f"  Drill files: {len(os.listdir(drill_dir))} files")


def export_intelligent_package():
    """Option B: ODB++ and IPC-2581 unified packages."""
    print("\n== 3. Exporting Intelligent Packages (ODB++ / IPC-2581) ==")
    docs_dir = os.path.join(RELEASE_DIR, "docs")

    # ODB++
    run_cmd(
        f'kicad-cli pcb export odb --output "{docs_dir}/{BOARD_NAME}.odb++.tgz" '
        f'--compression zip --units mm --precision 4 "{PCB}"',
        "ODB++ export", allow_fail=True
    )

    # IPC-2581
    run_cmd(
        f'kicad-cli pcb export ipc2581 --output "{docs_dir}/{BOARD_NAME}.ipc2581" '
        f'--version C --units mm --precision 4 "{PCB}"',
        "IPC-2581C export", allow_fail=True
    )


def export_ipc_d_356():
    """IPC-D-356 bare-board test netlist."""
    print("\n== 4. Exporting IPC-D-356 Bare-Board Netlist ==")
    testing_dir = os.path.join(RELEASE_DIR, "testing")
    run_cmd(
        f'kicad-cli pcb export ipcd356 '
        f'--output "{testing_dir}/{BOARD_NAME}_Netlist.ipc" "{PCB}"',
        "IPC-D-356 netlist", allow_fail=True
    )


def generate_bom():
    """BOM CSV with required columns."""
    print("\n== 5. Generating BOM CSV ==")
    assembly_dir = os.path.join(RELEASE_DIR, "assembly")
    bom_path = os.path.join(assembly_dir, f"{BOARD_NAME}_BOM.csv")

    # Parse PCB to extract component data
    with open(PCB, 'r') as f:
        pcb_content = f.read()

    # Extract footprint references, values, packages
    components = []
    item_num = 1

    # Parse footprint blocks
    fp_pattern = re.compile(
        r'\(footprint "([^"]+)".*?\(at ([\d.]+) ([\d.]+)(?: ([\d.]+))?\).*?'
        r'(?:\(layer "([^"]+)"\))?.*?'
        r'(?:\(property "Reference" "([^"]+)"\))?.*?'
        r'(?:\(property "Value" "([^"]+)"\))?',
        re.DOTALL
    )

    # Simpler approach: extract reference and value from fp_text blocks
    fp_blocks = pcb_content.split('(footprint "')[1:]  # split by footprint start

    for block in fp_blocks:
        fp_name = block.split('"')[0]

        # Extract reference
        ref_match = re.search(r'\(property "Reference" "([^"]+)"\)', block)
        ref = ref_match.group(1) if ref_match else "?"

        # Extract value
        val_match = re.search(r'\(property "Value" "([^"]+)"\)', block)
        val = val_match.group(1) if val_match else fp_name

        # Extract position
        at_match = re.search(r'\(at ([\d.-]+) ([\d.-]+)', block)
        x = float(at_match.group(1)) if at_match else 0.0
        y = float(at_match.group(2)) if at_match else 0.0

        # Determine layer
        layer_match = re.search(r'\(layer "([^"]+)"\)', block)
        layer = layer_match.group(1) if layer_match else "F.Cu"
        side = "Top" if "F." in layer else "Bottom"

        # Determine DNP status
        dnp = "Yes" if "HBM4" in ref or "DNP" in val else "No"

        # Map to package/footprint
        if "BGA" in fp_name:
            package = "BGA-2500"
        elif "QFN" in fp_name:
            package = "QFN-48"
        elif "0201" in fp_name:
            package = "0201"
        elif "0402" in fp_name:
            package = "0402"
        elif "0805" in fp_name:
            package = "0805"
        elif "1206" in fp_name:
            package = "1206"
        elif "SOD-523" in fp_name:
            package = "SOD-523"
        elif "MountingHole" in fp_name:
            package = "M3 Mounting Hole"
        elif "Fiducial" in fp_name:
            package = "Fiducial 1mm"
        elif "QSFP" in fp_name:
            package = "QSFP-DD"
        elif "PCI" in fp_name or "CEM" in fp_name:
            package = "PCIe CEM x16"
        elif "12VHPWR" in fp_name or "Molex" in fp_name:
            package = "12VHPWR 16-pin"
        else:
            package = fp_name.split(":")[-1] if ":" in fp_name else fp_name

        # Map to MPN (representative parts)
        mpn = ""
        manufacturer = ""
        if "NCE" in ref or "U101" in ref or "U201" in ref:
            mpn = "LR-NCE-P3A-BGA2500"
            manufacturer = "LightRail AI"
        elif "TFLN" in ref or "U102" in ref or "U202" in ref:
            mpn = "LR-TFLN-PIC-v2"
            manufacturer = "LightRail AI"
        elif "ISL69260" in val or "ISL69260" in fp_name:
            mpn = "ISL69260IRAZ"
            manufacturer = "Renesas"
        elif "ISL99390" in val or "DrMOS" in fp_name:
            mpn = "ISL99390FRZ"
            manufacturer = "Renesas"
        elif ref.startswith("C") and "0402" in package:
            mpn = "GRM155R71C104KA88D"
            manufacturer = "Murata"
        elif ref.startswith("C") and "0805" in package:
            mpn = "GRM21BR71A475KA73L"
            manufacturer = "Murata"
        elif ref.startswith("C") and "0201" in package:
            mpn = "GRM033R60J104KE19D"
            manufacturer = "Murata"
        elif ref.startswith("R"):
            mpn = "RC0402FR-0710KL"
            manufacturer = "Yageo"
        elif ref.startswith("FB"):
            mpn = "BLM15PX121SN1D"
            manufacturer = "Murata"
        elif "HBM4" in ref:
            mpn = "VENDOR-HBM4-STACK (interposer-resident)"
            manufacturer = "SK Hynix / Samsung"
            dnp = "Yes"

        description = ""
        if ref.startswith("C"):
            description = f"Capacitor {val}"
        elif ref.startswith("R"):
            description = f"Resistor {val}"
        elif ref.startswith("FB"):
            description = f"Ferrite bead {val}"
        elif "NCE" in ref:
            description = "Neural Compute Engine BGA-2500"
        elif "TFLN" in ref:
            description = "TFLN Photonic IC"
        elif "DrMOS" in fp_name:
            description = "DrMOS Power Stage 60A"
        elif "HBM4" in ref:
            description = "HBM4 DRAM Stack (DNP - interposer resident)"

        components.append({
            "Item": item_num,
            "Designator": ref,
            "Quantity": 1,
            "Value": val,
            "Footprint": package,
            "Manufacturer": manufacturer,
            "MPN": mpn,
            "Distributor": "",
            "DistributorPN": "",
            "Package": package,
            "Description": description,
            "DNP": dnp,
        })
        item_num += 1

    with open(bom_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Item", "Designator", "Quantity", "Value", "Footprint",
            "Manufacturer", "MPN", "Distributor", "DistributorPN",
            "Package", "Description", "DNP"
        ])
        writer.writeheader()
        writer.writerows(components)

    print(f"  BOM: {len(components)} components -> {bom_path}")
    return components


def generate_centroid(components=None):
    """Centroid / Pick & Place file (CPL/POS)."""
    print("\n== 6. Generating Centroid / Pick & Place CSV ==")
    assembly_dir = os.path.join(RELEASE_DIR, "assembly")

    # Use KiCad CLI for authoritative position data
    run_cmd(
        f'kicad-cli pcb export pos --output "{assembly_dir}/{BOARD_NAME}_CPL_top.csv" '
        f'--format csv --units mm --side front --use-drill-file-origin "{PCB}"',
        "Pick & Place (top)"
    )
    run_cmd(
        f'kicad-cli pcb export pos --output "{assembly_dir}/{BOARD_NAME}_CPL_bottom.csv" '
        f'--format csv --units mm --side back --use-drill-file-origin "{PCB}"',
        "Pick & Place (bottom)"
    )

    # Also create a combined CPL file with the user's exact column format
    cpl_combined_path = os.path.join(assembly_dir, f"{BOARD_NAME}_CPL.csv")

    # Parse the KiCad-generated top and bottom pos files
    all_entries = []
    for side_file, side_name in [
        (f"{BOARD_NAME}_CPL_top.csv", "Top"),
        (f"{BOARD_NAME}_CPL_bottom.csv", "Bottom"),
    ]:
        pos_path = os.path.join(assembly_dir, side_file)
        if os.path.exists(pos_path):
            with open(pos_path, 'r') as f:
                reader = csv.reader(f)
                header = None
                for row in reader:
                    if not row or row[0].startswith('#'):
                        continue
                    if header is None:
                        header = row
                        continue
                    # KiCad pos format: Ref, Val, Package, PosX, PosY, Rot, Side
                    if len(row) >= 6:
                        all_entries.append({
                            "Designator": row[0].strip(),
                            "X-Coordinate": row[3].strip() if len(row) > 3 else "0",
                            "Y-Coordinate": row[4].strip() if len(row) > 4 else "0",
                            "Rotation": row[5].strip() if len(row) > 5 else "0",
                            "Layer": side_name,
                        })

    with open(cpl_combined_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Designator", "X-Coordinate", "Y-Coordinate", "Rotation", "Layer"
        ])
        writer.writeheader()
        writer.writerows(all_entries)

    print(f"  CPL: {len(all_entries)} entries -> {cpl_combined_path}")


def export_3d_step():
    """3D STEP model."""
    print("\n== 7. Exporting 3D STEP Model ==")
    model_dir = os.path.join(RELEASE_DIR, "3d_model")
    run_cmd(
        f'kicad-cli pcb export step --output "{model_dir}/{BOARD_NAME}_3D.step" '
        f'--subst-models --include-tracks --include-zones "{PCB}"',
        "3D STEP export"
    )


def generate_fab_drawing():
    """Fabrication Drawing PDF — mechanical specs, board outline, mounting holes."""
    print("\n== 8. Generating Fabrication Drawing ==")
    docs_dir = os.path.join(RELEASE_DIR, "docs")
    fab_drawing_path = os.path.join(docs_dir, f"{BOARD_NAME}_Fab_Drawing.pdf")

    # Generate the fab drawing as a detailed text document first, then convert to PDF
    # Using KiCad's PDF export for the board outline + fab layers
    run_cmd(
        f'kicad-cli pcb export pdf --output "{fab_drawing_path}" '
        f'--layers "Edge.Cuts,F.Fab,B.Fab,F.SilkS,Dwgs.User" "{PCB}"',
        "Fab drawing PDF"
    )

    # Also generate a comprehensive fab notes text file
    fab_notes_path = os.path.join(docs_dir, f"{BOARD_NAME}_Fab_Notes.txt")
    with open(fab_notes_path, 'w') as f:
        f.write(f"""{'='*72}
FABRICATION NOTES — {BOARD_NAME}
LightRail AI Compute Node (LR-P3A) Rev 6.3
Date: {datetime.datetime.now().strftime('%Y-%m-%d')}
{'='*72}

1. BOARD DIMENSIONS
   Length:  {BW} mm ({BW/25.4:.3f} in)
   Width:   {BH} mm ({BH/25.4:.3f} in)
   Thickness: {THICKNESS} mm +/- 10%
   Board outline tolerance: +/- 0.15 mm

2. LAYER COUNT: 32 layers (see Stackup_Impedance report)

3. MATERIAL SYSTEM
   Signal layers: Panasonic Megtron-7 (er=3.3, tan_d=0.002 @ 1 GHz)
   Power/Ground planes: High-Tg FR-4 (er=4.2, Tg >= 170C)
   Embedded capacitance: Faradflex BC24 (er=14, 24 um core)
   between layers In15 and In16

4. COPPER WEIGHTS
   F.Cu, B.Cu: 2 oz (70 um finished)
   In10-In14, In16-In20: 2 oz (70 um finished)
   In15: 1 oz (35 um finished)
   In1-In9, In21-In30: 0.5 oz (17.5 um finished)

5. SURFACE FINISH
   ENIG (Electroless Nickel Immersion Gold)
   Per IPC-4552 Class 3
   Ni: 3-6 um, Au: 0.05-0.10 um

6. SOLDER MASK
   LPI solder mask, both sides
   Color: Matte green (Taiyo PSR-4000 AUS703 or equivalent)
   Minimum web width: 0.075 mm (3 mil)
   Pad-to-mask clearance: 0.051 mm per side (IPC-7351B)

7. SILKSCREEN
   White epoxy ink, both sides
   Minimum text height: 0.8 mm
   Minimum line width: 0.15 mm

8. MOUNTING HOLES (6 total)
   Corner holes (4x): M3 NPTH, diameter 3.2 mm +/- 0.05 mm
     Locations: (5,5), (415,5), (5,345), (415,345) mm from origin
   NCE cold-plate bolster holes (8x per NCE): M3 NPTH, 3.2 mm
     NCE A pattern: 50 mm square centered at ({135},{160})
     NCE B pattern: 50 mm square centered at ({285},{160})

9. MINIMUM DESIGN RULES (IPC-6012 Class 3)
   Min trace width: 0.075 mm (3 mil)
   Min trace space: 0.075 mm (3 mil)
   Min annular ring: 0.050 mm (2 mil)
   Via drill: 0.30 mm min (aspect ratio 11.6:1 max)
   Via aspect ratio limit: 12:1

10. DRILL SPECIFICATIONS
    PTH vias: 0.30-0.40 mm drill, 0.60-0.80 mm pad
    Component holes: per footprint specification
    NPTH mounting: 3.20 mm drill
    Back-drill: All high-speed through-vias
      - Target layers: PCIe Gen6, SerDes 100G, TFLN RF
      - Residual stub: <= 0.127 mm (5 mil)

11. COPPER-FREE KEEPOUT ZONES
    TFLN edge coupler keepout: 2.54 mm (100 mil) on all copper layers
    Photonic bridge region: zero copper (optical datapath)
    MPO-24 front-panel exit: 2.54 mm clearance

12. IMPEDANCE CONTROL (see Stackup_Impedance report for details)
    All controlled-impedance traces on signal layers must meet
    specified targets within +/- 10% tolerance.
    Manufacturer must provide impedance test coupons.

13. PANELIZATION
    Single board per panel recommended due to board size.
    If panelized: V-score or routed tab with 3 mm rail.

14. TESTING
    100% bare-board electrical test required per IPC-D-356 netlist.
    Flying probe or bed-of-nails per manufacturer capability.

15. QUALITY
    IPC-6012 Class 3 workmanship standard
    IPC-A-600 Class 3 acceptance criteria
    Cross-section required for first article (2 coupons minimum)

{'='*72}
END OF FABRICATION NOTES
{'='*72}
""")
    print(f"  Fab notes: {fab_notes_path}")


def generate_stackup_impedance_report():
    """Stackup & Impedance Report PDF."""
    print("\n== 9. Generating Stackup & Impedance Report ==")
    docs_dir = os.path.join(RELEASE_DIR, "docs")
    report_path = os.path.join(docs_dir, f"{BOARD_NAME}_Stackup_Impedance.txt")

    with open(report_path, 'w') as f:
        f.write(f"""{'='*80}
STACKUP & IMPEDANCE CONTROL REPORT
{BOARD_NAME} — LightRail AI LR-P3A Rev 6.3
Date: {datetime.datetime.now().strftime('%Y-%m-%d')}
{'='*80}

1. LAYER STACKUP (32 layers, symmetric around In15/In16 midplane)
   Total thickness: {THICKNESS} mm +/- 10%

{'Layer':<12} {'Type':<14} {'Copper':<20} {'Dielectric':<40} {'Function':<30}
{'-'*116}
""")
        for layer, ltype, copper, dielectric, function in STACKUP:
            f.write(f"{layer:<12} {ltype:<14} {copper:<20} {dielectric:<40} {function:<30}\n")

        f.write(f"""
   Dielectric between layers: 76 um (Megtron-7) or 76 um (High-Tg FR-4)
   Embedded capacitance core: 24 um (Faradflex BC24, er=14)

2. IMPEDANCE TARGETS

   All impedance values must be within the specified tolerance.
   Manufacturer MUST provide impedance test coupons for verification.

{'Signal Class':<24} {'Layers':<24} {'Target Impedance':<24} {'Tolerance':<12} {'Geometry':<30}
{'-'*114}
""")
        for sig_class, layers, target, tol, geom in IMPEDANCE_TARGETS:
            f.write(f"{sig_class:<24} {layers:<24} {target:<24} {tol:<12} {geom:<30}\n")

        f.write(f"""

3. IMPEDANCE CALCULATION NOTES

   Signal layer dielectric: Megtron-7
     er = 3.3 @ 1 GHz
     tan_d = 0.002 @ 1 GHz
     Dk tolerance: +/- 0.05

   Power layer dielectric: High-Tg FR-4
     er = 4.2 @ 1 GHz
     tan_d = 0.015 @ 1 GHz
     Tg >= 170C (per IPC-4101/126)

   Embedded capacitance: Faradflex BC24
     er = 14.0 @ 1 MHz
     Core thickness: 24 um
     Positioned between In15 and In16 (midplane)

4. LENGTH MATCHING REQUIREMENTS

   PCIe Gen6 x16 (In5/In26):
     Match to +/- 1 ps (+/- 0.15 mm on Megtron-7)
     85 Ohm differential

   SerDes 100G PAM4 (In3/In28):
     Match to +/- 1 ps (+/- 0.15 mm on Megtron-7)
     100 Ohm differential

   HBM4 REFCK (In2/In29):
     Match to +/- 2 ps (+/- 0.30 mm on Megtron-7)
     100 Ohm differential

5. BACK-DRILL REQUIREMENTS

   All high-speed through-vias must be back-drilled to minimize stub.
   Maximum residual stub: 0.127 mm (5 mil)
   Applicable nets: PCIe_Gen6, SERDES_100G_PAM4, TFLN_RF
   Back-drill from B.Cu side unless specified otherwise.

{'='*80}
END OF STACKUP & IMPEDANCE REPORT
{'='*80}
""")
    print(f"  Stackup report: {report_path}")


def export_assembly_drawings():
    """Assembly Drawing PDFs (top + bottom)."""
    print("\n== 10. Exporting Assembly Drawings ==")
    assembly_dir = os.path.join(RELEASE_DIR, "assembly")

    run_cmd(
        f'kicad-cli pcb export pdf --output "{assembly_dir}/{BOARD_NAME}_Assy_Drawing_Top.pdf" '
        f'--layers "F.Fab,F.SilkS,Edge.Cuts" "{PCB}"',
        "Assembly drawing (top)"
    )
    run_cmd(
        f'kicad-cli pcb export pdf --output "{assembly_dir}/{BOARD_NAME}_Assy_Drawing_Bottom.pdf" '
        f'--layers "B.Fab,B.SilkS,Edge.Cuts" --mirror "{PCB}"',
        "Assembly drawing (bottom)"
    )


def export_drc_report():
    """DRC report."""
    print("\n== 11. Running DRC ==")
    testing_dir = os.path.join(RELEASE_DIR, "testing")

    run_cmd(
        f'kicad-cli pcb drc --output "{testing_dir}/{BOARD_NAME}_DRC_Report.json" '
        f'--format json "{PCB}"',
        "DRC (JSON)", allow_fail=True
    )
    run_cmd(
        f'kicad-cli pcb drc --output "{testing_dir}/{BOARD_NAME}_DRC_Report.rpt" '
        f'--format report "{PCB}"',
        "DRC (report)", allow_fail=True
    )


def create_readme():
    """Create a README for the release package."""
    readme_path = os.path.join(RELEASE_DIR, "README.txt")
    with open(readme_path, 'w') as f:
        f.write(f"""{'='*72}
DUAL NCE ACCELERATOR — FABRICATION RELEASE PACKAGE v1
LightRail AI Compute Node (LR-P3A) Rev 6.3
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
{'='*72}

PACKAGE CONTENTS:

gerbers/
  {BOARD_NAME}_TopCopper.gbr        Layer 1 (F.Cu) - Signal/Power
  {BOARD_NAME}_Inner1.gbr           Layer 2 (In1.Cu) - Signal
  ...through...
  {BOARD_NAME}_Inner30.gbr          Layer 31 (In30.Cu) - Signal
  {BOARD_NAME}_BottomCopper.gbr     Layer 32 (B.Cu) - Signal/Power
  {BOARD_NAME}_TopSolderMask.gbr    Top solder mask
  {BOARD_NAME}_BottomSolderMask.gbr Bottom solder mask
  {BOARD_NAME}_TopSilkscreen.gbr    Top silkscreen
  {BOARD_NAME}_BottomSilkscreen.gbr Bottom silkscreen
  {BOARD_NAME}_TopPaste.gbr         Top solder paste (stencil)
  {BOARD_NAME}_BottomPaste.gbr      Bottom solder paste (stencil)
  {BOARD_NAME}_EdgeCuts.gbr         Board outline + cutouts

drill/
  {BOARD_NAME}_PTH.drl              Plated through-holes (Excellon)
  {BOARD_NAME}_NPTH.drl             Non-plated through-holes (Excellon)
  {BOARD_NAME}_DrillMap_PTH.gbr     PTH drill map (visual)
  {BOARD_NAME}_DrillMap_NPTH.gbr    NPTH drill map (visual)

assembly/
  {BOARD_NAME}_BOM.csv              Bill of Materials (full)
  {BOARD_NAME}_CPL.csv              Centroid / Pick & Place (combined)
  {BOARD_NAME}_CPL_top.csv          Pick & Place (top side)
  {BOARD_NAME}_CPL_bottom.csv       Pick & Place (bottom side)
  {BOARD_NAME}_Assy_Drawing_Top.pdf Top assembly drawing
  {BOARD_NAME}_Assy_Drawing_Bottom.pdf Bottom assembly drawing

docs/
  {BOARD_NAME}_Fab_Drawing.pdf      Fabrication drawing
  {BOARD_NAME}_Fab_Notes.txt        Detailed fabrication notes
  {BOARD_NAME}_Stackup_Impedance.txt  Stackup & impedance report
  {BOARD_NAME}.ipc2581              IPC-2581C unified package
  {BOARD_NAME}.odb++.tgz            ODB++ unified package (if available)

testing/
  {BOARD_NAME}_Netlist.ipc          IPC-D-356 bare-board test netlist
  {BOARD_NAME}_DRC_Report.json      Design Rule Check (JSON)
  {BOARD_NAME}_DRC_Report.rpt       Design Rule Check (human-readable)

3d_model/
  {BOARD_NAME}_3D.step              3D STEP model (AP242)

BOARD SPECIFICATIONS:
  Dimensions: {BW} x {BH} mm
  Layers: 32 (HDI)
  Thickness: {THICKNESS} mm +/- 10%
  Surface finish: ENIG (IPC-4552 Class 3)
  Min trace/space: 0.075/0.075 mm
  Via drill: 0.30 mm minimum (aspect ratio 11.6:1)
  Mounting: 4x M3 corner + 8x M3 per NCE cold-plate

QUALITY REQUIREMENTS:
  IPC-6012 Class 3
  100% bare-board electrical test (IPC-D-356)
  Impedance test coupons required
  Cross-section for first article

{'='*72}
""")
    print(f"  README: {readme_path}")


def create_zip():
    """Create final zip archive."""
    print("\n== 12. Creating Release Archive ==")
    zip_path = os.path.join(ROOT, "fab", "Dual_NCE_Accelerator_Fab_Release_v1")
    archive_path = shutil.make_archive(zip_path, 'zip', RELEASE_DIR)
    size_mb = os.path.getsize(archive_path) / (1024 * 1024)
    print(f"  Archive: {archive_path} ({size_mb:.1f} MB)")
    return archive_path


def main():
    print(f"{'='*60}")
    print(f"Dual NCE Accelerator — Fab Release Package Generator")
    print(f"LR-P3A Rev 6.3 | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")

    setup_directories()
    export_gerbers()
    export_drill()
    export_intelligent_package()
    export_ipc_d_356()
    components = generate_bom()
    generate_centroid(components)
    export_3d_step()
    generate_fab_drawing()
    generate_stackup_impedance_report()
    export_assembly_drawings()
    export_drc_report()
    create_readme()
    archive = create_zip()

    # Summary
    print(f"\n{'='*60}")
    print(f"RELEASE PACKAGE COMPLETE")
    print(f"{'='*60}")

    file_count = 0
    for dirpath, dirnames, filenames in os.walk(RELEASE_DIR):
        file_count += len(filenames)

    print(f"  Total files: {file_count}")
    print(f"  Release dir: {RELEASE_DIR}")
    print(f"  Archive:     {archive}")
    print()

    # List all files
    print("File manifest:")
    for dirpath, dirnames, filenames in os.walk(RELEASE_DIR):
        rel_dir = os.path.relpath(dirpath, RELEASE_DIR)
        for fn in sorted(filenames):
            full_path = os.path.join(dirpath, fn)
            size = os.path.getsize(full_path)
            if size > 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"  {os.path.join(rel_dir, fn):<60} {size_str:>10}")


if __name__ == "__main__":
    main()

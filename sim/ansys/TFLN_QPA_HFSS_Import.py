#!/usr/bin/env python3
"""
Ansys HFSS / SIwave Import Helper — DXF Generator
LightRail AI LR-P3A Rev 6.3 — Quantum Photonic Accelerator

Generates DXF files from the QPA PCB design for import into:
  - Ansys HFSS (3D EM simulation of RF structures)
  - Ansys SIwave (PCB signal/power integrity)
  - Ansys Icepak (thermal analysis)

Also generates an HFSS setup script (.py) for PyAEDT automation.

Usage:
    python3 TFLN_QPA_HFSS_Import.py

Output files:
    TFLN_QPA_RF_CPW.dxf         — RF coplanar waveguide structures
    TFLN_QPA_MZI_Electrodes.dxf — MZI electrode geometry
    TFLN_QPA_HFSS_Setup.py      — PyAEDT automation script
"""

import math
import os

# Board parameters (mm)
BOARD_W = 420.0
BOARD_H = 350.0
CENTER_X = BOARD_W / 2.0
CENTER_Y = BOARD_H / 2.0

# MZI parameters (um → mm)
MZI_ARM_LENGTH = 0.500       # 500 um
MZI_ARM_SPACING = 0.005      # 5 um
WG_WIDTH = 0.0008            # 800 nm
ELECTRODE_WIDTH = 0.005      # 5 um
ELECTRODE_GAP = 0.003        # 3 um from waveguide

# RF CPW parameters (mm)
CPW_TRACE_W = 0.080          # 80 um signal trace
CPW_GAP = 0.040              # 40 um gap
CPW_GND_W = 0.200            # 200 um ground plane width


def write_dxf_header(f, name="QPA_Export"):
    """Write DXF file header (AutoCAD R14 compatible)."""
    f.write("0\nSECTION\n2\nHEADER\n")
    f.write("9\n$ACADVER\n1\nAC1014\n")
    f.write("9\n$INSUNITS\n70\n4\n")  # millimeters
    f.write("0\nENDSEC\n")
    # Tables
    f.write("0\nSECTION\n2\nTABLES\n")
    # Layer table
    f.write("0\nTABLE\n2\nLAYER\n70\n10\n")
    layers = [
        ("RF_CPW_SIGNAL", 1),      # Red
        ("RF_CPW_GROUND", 3),      # Green
        ("MZI_WAVEGUIDE", 5),      # Blue
        ("MZI_ELECTRODE_S", 6),    # Magenta
        ("MZI_ELECTRODE_G", 8),    # Gray
        ("BOARD_OUTLINE", 7),      # White
        ("TFLN_REGION", 4),        # Cyan
        ("CXL_TRACES", 2),        # Yellow
        ("SNSPD_READOUT", 30),    # Orange
        ("ANNOTATIONS", 7),        # White
    ]
    for lname, color in layers:
        f.write(f"0\nLAYER\n2\n{lname}\n70\n0\n62\n{color}\n6\nCONTINUOUS\n")
    f.write("0\nENDTAB\n")
    f.write("0\nENDSEC\n")
    # Entities section
    f.write("0\nSECTION\n2\nENTITIES\n")


def write_dxf_footer(f):
    """Write DXF file footer."""
    f.write("0\nENDSEC\n0\nEOF\n")


def dxf_line(f, layer, x1, y1, x2, y2):
    """Write a LINE entity."""
    f.write(f"0\nLINE\n8\n{layer}\n"
            f"10\n{x1:.6f}\n20\n{y1:.6f}\n30\n0.0\n"
            f"11\n{x2:.6f}\n21\n{y2:.6f}\n31\n0.0\n")


def dxf_lwpolyline(f, layer, points, closed=False):
    """Write a LWPOLYLINE entity."""
    flag = 1 if closed else 0
    f.write(f"0\nLWPOLYLINE\n8\n{layer}\n"
            f"90\n{len(points)}\n70\n{flag}\n")
    for x, y in points:
        f.write(f"10\n{x:.6f}\n20\n{y:.6f}\n")


def dxf_circle(f, layer, cx, cy, r):
    """Write a CIRCLE entity."""
    f.write(f"0\nCIRCLE\n8\n{layer}\n"
            f"10\n{cx:.6f}\n20\n{cy:.6f}\n30\n0.0\n40\n{r:.6f}\n")


def dxf_text(f, layer, x, y, height, text):
    """Write a TEXT entity."""
    f.write(f"0\nTEXT\n8\n{layer}\n"
            f"10\n{x:.6f}\n20\n{y:.6f}\n30\n0.0\n"
            f"40\n{height:.4f}\n1\n{text}\n")


def dxf_rect(f, layer, x, y, w, h):
    """Write a closed rectangle as LWPOLYLINE."""
    pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
    dxf_lwpolyline(f, layer, pts, closed=True)


def generate_rf_cpw_dxf(filepath):
    """Generate DXF of RF coplanar waveguide structures for HFSS."""
    with open(filepath, "w") as f:
        write_dxf_header(f, "QPA_RF_CPW")

        # Board outline
        dxf_rect(f, "BOARD_OUTLINE", 0, 0, BOARD_W, BOARD_H)

        # TFLN PIC regions (2x, symmetric)
        for side, sx in [("A", CENTER_X - 60), ("B", CENTER_X + 10)]:
            dxf_rect(f, "TFLN_REGION", sx, CENTER_Y - 25, 50, 50)
            dxf_text(f, "ANNOTATIONS", sx + 5, CENTER_Y + 27,
                     1.5, f"TFLN_PIC_{side}")

        # RF CPW traces: DAC → RF Driver → TFLN electrodes
        # 8 channels per side (Side A and Side B)
        for side_idx, x_base in enumerate([CENTER_X - 80, CENTER_X + 60]):
            for ch in range(8):
                y_offset = CENTER_Y - 14 + ch * 4.0

                # Signal trace
                x1 = x_base
                x2 = x_base + (20 if side_idx == 0 else -20)
                sign = 1 if side_idx == 0 else -1

                # CPW signal conductor
                pts_sig = [
                    (x1, y_offset - CPW_TRACE_W / 2),
                    (x1 + sign * 20, y_offset - CPW_TRACE_W / 2),
                    (x1 + sign * 20, y_offset + CPW_TRACE_W / 2),
                    (x1, y_offset + CPW_TRACE_W / 2),
                ]
                dxf_lwpolyline(f, "RF_CPW_SIGNAL", pts_sig, closed=True)

                # CPW ground (top)
                pts_gnd_t = [
                    (x1, y_offset + CPW_TRACE_W / 2 + CPW_GAP),
                    (x1 + sign * 20,
                     y_offset + CPW_TRACE_W / 2 + CPW_GAP),
                    (x1 + sign * 20,
                     y_offset + CPW_TRACE_W / 2 + CPW_GAP + CPW_GND_W),
                    (x1,
                     y_offset + CPW_TRACE_W / 2 + CPW_GAP + CPW_GND_W),
                ]
                dxf_lwpolyline(f, "RF_CPW_GROUND", pts_gnd_t, closed=True)

                # CPW ground (bottom)
                pts_gnd_b = [
                    (x1, y_offset - CPW_TRACE_W / 2 - CPW_GAP - CPW_GND_W),
                    (x1 + sign * 20,
                     y_offset - CPW_TRACE_W / 2 - CPW_GAP - CPW_GND_W),
                    (x1 + sign * 20,
                     y_offset - CPW_TRACE_W / 2 - CPW_GAP),
                    (x1,
                     y_offset - CPW_TRACE_W / 2 - CPW_GAP),
                ]
                dxf_lwpolyline(f, "RF_CPW_GROUND", pts_gnd_b, closed=True)

            dxf_text(f, "ANNOTATIONS", x_base + (2 if side_idx == 0 else -18),
                     CENTER_Y + 20, 1.0,
                     f"RF_CPW_8CH_{'A' if side_idx == 0 else 'B'}")

        # CXL 2.0 differential pairs (simplified)
        for ch in range(8):
            y_off = CENTER_Y - 28 + ch * 8.0
            dxf_line(f, "CXL_TRACES",
                     CENTER_X - 30, y_off, CENTER_X + 30, y_off)
            dxf_line(f, "CXL_TRACES",
                     CENTER_X - 30, y_off + 0.15,
                     CENTER_X + 30, y_off + 0.15)

        # SNSPD readout traces
        for side_idx, x_base in enumerate([CENTER_X - 45, CENTER_X + 45]):
            for ch in range(8):
                y_off = CENTER_Y - 10 + ch * 2.5
                sign = 1 if side_idx == 0 else -1
                dxf_line(f, "SNSPD_READOUT",
                         x_base, y_off, x_base + sign * 15, y_off)

        write_dxf_footer(f)
    print(f"  Generated: {filepath}")


def generate_mzi_electrode_dxf(filepath):
    """Generate DXF of MZI electrode geometry for HFSS EM simulation."""
    with open(filepath, "w") as f:
        write_dxf_header(f, "QPA_MZI_Electrodes")

        # Single MZI unit cell (in micrometers, scaled to mm)
        # Origin at center of MZI

        # Waveguide paths (upper and lower arms)
        arm_half = MZI_ARM_LENGTH / 2
        arm_y = MZI_ARM_SPACING / 2

        # Upper arm waveguide
        dxf_rect(f, "MZI_WAVEGUIDE",
                 -arm_half, arm_y - WG_WIDTH / 2,
                 MZI_ARM_LENGTH, WG_WIDTH)

        # Lower arm waveguide
        dxf_rect(f, "MZI_WAVEGUIDE",
                 -arm_half, -arm_y - WG_WIDTH / 2,
                 MZI_ARM_LENGTH, WG_WIDTH)

        # Y-splitter input (simplified as tapered region)
        pts_split = [
            (-arm_half - 0.030, 0),
            (-arm_half, arm_y),
            (-arm_half, -arm_y),
        ]
        dxf_lwpolyline(f, "MZI_WAVEGUIDE", pts_split, closed=True)

        # Y-combiner output
        pts_comb = [
            (arm_half + 0.030, 0),
            (arm_half, arm_y),
            (arm_half, -arm_y),
        ]
        dxf_lwpolyline(f, "MZI_WAVEGUIDE", pts_comb, closed=True)

        # Signal electrode (between arms, on upper arm)
        elec_y = arm_y + WG_WIDTH / 2 + ELECTRODE_GAP
        dxf_rect(f, "MZI_ELECTRODE_S",
                 -arm_half + 0.010, elec_y,
                 MZI_ARM_LENGTH - 0.020, ELECTRODE_WIDTH)

        # Ground electrodes (outside each arm)
        gnd_y_top = arm_y + WG_WIDTH / 2 + ELECTRODE_GAP + ELECTRODE_WIDTH + 0.002
        dxf_rect(f, "MZI_ELECTRODE_G",
                 -arm_half + 0.010, gnd_y_top,
                 MZI_ARM_LENGTH - 0.020, ELECTRODE_WIDTH * 2)

        gnd_y_bot = -arm_y - WG_WIDTH / 2 - ELECTRODE_GAP - ELECTRODE_WIDTH
        dxf_rect(f, "MZI_ELECTRODE_G",
                 -arm_half + 0.010, gnd_y_bot,
                 MZI_ARM_LENGTH - 0.020, ELECTRODE_WIDTH)

        # Annotations
        dxf_text(f, "ANNOTATIONS", -arm_half, arm_y + 0.020, 0.003,
                 "TFLN MZI Unit Cell")
        dxf_text(f, "ANNOTATIONS", -arm_half, arm_y + 0.016, 0.002,
                 f"Arm length: {MZI_ARM_LENGTH*1000:.0f} um")
        dxf_text(f, "ANNOTATIONS", -arm_half, arm_y + 0.013, 0.002,
                 f"Arm spacing: {MZI_ARM_SPACING*1000:.1f} um")
        dxf_text(f, "ANNOTATIONS", -arm_half, arm_y + 0.010, 0.002,
                 f"WG width: {WG_WIDTH*1e6:.0f} nm")

        write_dxf_footer(f)
    print(f"  Generated: {filepath}")


def generate_pyaedt_script(filepath):
    """Generate PyAEDT automation script for HFSS setup."""
    script = '''#!/usr/bin/env python3
"""
PyAEDT Automation Script — TFLN QPA RF Structure Simulation
LightRail AI LR-P3A Rev 6.3

Sets up an Ansys HFSS simulation for the 100 GHz RF coplanar waveguide
structures used in the QPA DAC-to-TFLN electrode routing.

Prerequisites:
    pip install pyaedt
    Ansys Electronics Desktop 2024 R1+ installed

Usage:
    python3 TFLN_QPA_HFSS_Setup.py
"""

try:
    from pyaedt import Hfss
except ImportError:
    print("PyAEDT not installed. Install with: pip install pyaedt")
    print("This script requires Ansys Electronics Desktop to be installed.")
    print("")
    print("Manual HFSS import instructions:")
    print("  1. Open HFSS → File → Import → select TFLN_QPA_RF_CPW.dxf")
    print("  2. Map layers: RF_CPW_SIGNAL → signal conductor")
    print("  3. Map layers: RF_CPW_GROUND → ground plane")
    print("  4. Set material: TFLN substrate (LiNbO3, er=28.7 @ 100 GHz)")
    print("  5. Add wave ports at CPW ends")
    print("  6. Set frequency sweep: 1-120 GHz")
    exit(0)


def setup_hfss_cpw_simulation():
    """Set up HFSS simulation for QPA RF CPW."""

    # Create new HFSS project
    hfss = Hfss(
        projectname="TFLN_QPA_RF_CPW",
        designname="CPW_100GHz",
        solution_type="DrivenTerminal",
        new_desktop_session=True
    )

    # Set units to micrometers for RF structures
    hfss.modeler.model_units = "um"

    # Material definitions
    # TFLN substrate (X-cut Lithium Niobate)
    tfln_mat = hfss.materials.add_material("TFLN_Xcut")
    tfln_mat.permittivity = 28.7    # extraordinary at 100 GHz
    tfln_mat.loss_tangent = 0.001
    tfln_mat.conductivity = 0

    # SiO2 buried oxide
    sio2_mat = hfss.materials.add_material("SiO2_BOX")
    sio2_mat.permittivity = 3.9
    sio2_mat.loss_tangent = 0.0001

    # CPW geometry parameters (micrometers)
    cpw_signal_w = 80       # Signal conductor width
    cpw_gap = 40            # Gap between signal and ground
    cpw_gnd_w = 200         # Ground plane width
    cpw_length = 5000       # 5 mm CPW length
    metal_t = 0.2           # 200 nm gold thickness
    tfln_t = 0.6            # 600 nm TFLN film
    box_t = 2.0             # 2 um BOX
    si_t = 10.0             # 10 um Si handle (truncated)

    # Build substrate stack
    # Silicon handle
    hfss.modeler.create_box(
        [0, -cpw_gnd_w - cpw_gap - cpw_signal_w/2, -si_t - box_t - tfln_t],
        [cpw_length, 2*(cpw_gnd_w + cpw_gap) + cpw_signal_w, si_t],
        name="Si_Handle", matname="silicon"
    )

    # BOX layer
    hfss.modeler.create_box(
        [0, -cpw_gnd_w - cpw_gap - cpw_signal_w/2, -box_t - tfln_t],
        [cpw_length, 2*(cpw_gnd_w + cpw_gap) + cpw_signal_w, box_t],
        name="SiO2_BOX", matname="SiO2_BOX"
    )

    # TFLN film
    hfss.modeler.create_box(
        [0, -cpw_gnd_w - cpw_gap - cpw_signal_w/2, -tfln_t],
        [cpw_length, 2*(cpw_gnd_w + cpw_gap) + cpw_signal_w, tfln_t],
        name="TFLN_Film", matname="TFLN_Xcut"
    )

    # CPW conductors (gold)
    # Signal
    hfss.modeler.create_box(
        [0, -cpw_signal_w/2, 0],
        [cpw_length, cpw_signal_w, metal_t],
        name="CPW_Signal", matname="gold"
    )

    # Ground top
    hfss.modeler.create_box(
        [0, cpw_signal_w/2 + cpw_gap, 0],
        [cpw_length, cpw_gnd_w, metal_t],
        name="CPW_Gnd_Top", matname="gold"
    )

    # Ground bottom
    hfss.modeler.create_box(
        [0, -cpw_signal_w/2 - cpw_gap - cpw_gnd_w, 0],
        [cpw_length, cpw_gnd_w, metal_t],
        name="CPW_Gnd_Bot", matname="gold"
    )

    # Frequency sweep: 1 GHz to 120 GHz
    setup = hfss.create_setup("Setup_100GHz")
    setup.props["Frequency"] = "100GHz"
    setup.props["MaximumPasses"] = 20
    setup.props["MaxDeltaS"] = 0.01

    sweep = setup.add_sweep()
    sweep.props["RangeType"] = "LinearStep"
    sweep.props["RangeStart"] = "1GHz"
    sweep.props["RangeStop"] = "120GHz"
    sweep.props["RangeStep"] = "1GHz"
    sweep.props["Type"] = "Interpolating"

    # Add wave ports
    hfss.wave_port(
        signal_name="CPW_Signal",
        reference_names=["CPW_Gnd_Top", "CPW_Gnd_Bot"],
        name="Port1"
    )

    print("HFSS simulation setup complete.")
    print(f"  CPW: {cpw_signal_w} um signal, {cpw_gap} um gap, {cpw_gnd_w} um ground")
    print(f"  Frequency: 1-120 GHz (1 GHz step)")
    print(f"  Substrate: TFLN X-cut (er=28.7) on SiO2 BOX")
    print("")
    print("Run the simulation with: hfss.analyze_setup('Setup_100GHz')")

    return hfss


if __name__ == "__main__":
    hfss = setup_hfss_cpw_simulation()
'''
    with open(filepath, "w") as f:
        f.write(script)
    os.chmod(filepath, 0o755)
    print(f"  Generated: {filepath}")


def generate_siwave_import_notes(filepath):
    """Generate instructions for SIwave PCB import."""
    notes = """########################################################################
# Ansys SIwave Import Instructions
# LightRail AI LR-P3A Rev 6.3 — Quantum Photonic Accelerator
########################################################################

SUPPORTED IMPORT FORMATS (already generated):
=============================================

1. ODB++ (.tgz)
   - Not yet generated; SIwave prefers this for full PCB import
   - Can be exported from KiCad via third-party plugin or Allegro

2. IPC-2581 (.xml)
   - File: fab/Dual_NCE_Accelerator_Fab_Release_v1/docs/Dual_NCE_Accelerator.ipc2581
   - Import: SIwave → File → Import → IPC2581 → select file
   - Contains full stackup, netlist, and copper geometry

3. GDSII (.gds)
   - File: fab/Dual_NCE_Accelerator_Fab_Release_v1/Dual_NCE_Accelerator.gds
   - Import: SIwave → File → Import → GDSII → select file
   - Layer mapping file: Dual_NCE_Accelerator_GDS_LayerMap.txt
   - Map GDS layers to SIwave signal/plane/via layers

4. Gerber Files (.gbr)
   - Directory: fab/Dual_NCE_Accelerator_Fab_Release_v1/gerbers/
   - 42 Gerber RS-274X files (32 copper + masks + silk + paste)
   - Import via HFSS 3D Layout → File → Import → Gerber

5. DXF Files (.dxf)
   - File: sim/ansys/TFLN_QPA_RF_CPW.dxf (RF structures only)
   - File: sim/ansys/TFLN_QPA_MZI_Electrodes.dxf (MZI unit cell)
   - Import: SIwave → File → Import → DXF → select file


RECOMMENDED WORKFLOW:
=====================

For PCB Signal Integrity (SIwave):
  1. Import IPC-2581 file (contains full board with stackup)
  2. Verify 32-layer stackup matches spec (Megtron-7 signal, FR-4 planes)
  3. Run DC IR drop analysis on QPA power nets (VDD_QPA_0V85, VDD_QPA_1V8)
  4. Run AC impedance analysis on CXL 2.0 differential pairs
  5. Extract S-parameters for QPA signal buses

For RF EM Simulation (HFSS):
  1. Import GDSII or DXF of RF CPW structures
  2. Set up driven terminal simulation (1-120 GHz)
  3. Validate 50-ohm CPW impedance on TFLN substrate
  4. Extract S21 (insertion loss) and S11 (return loss)
  5. Verify 100 GHz bandwidth for DAC output routing

For Thermal Analysis (Icepak):
  1. Import 3D STEP model from fab/Dual_NCE_Accelerator_Fab_Release_v1/3d_model/
  2. Set power dissipation for QPA components:
     - FPGA (U401/U402): 15W each
     - DAC (U411/U412): 5W each
     - RF Drivers (U421-U428): 1W each
     - SNSPD (U431/U432): 0.001W each (cryogenic, <4K)
     - CXL Switch (U450): 10W
  3. Model cryogenic interface (diamond substrate, 2000 W/mK)
  4. Verify thermal gradient across TFLN PIC region


STACKUP FOR IMPEDANCE SIMULATION:
==================================

Layer  | Name     | Type    | Material    | Thickness | Cu Weight
-------|----------|---------|-------------|-----------|----------
1      | F.Cu     | Signal  | Megtron-7   | 70 um     | 2 oz
2      | In1.Cu   | Signal  | Megtron-7   | 17.5 um   | 0.5 oz
3      | In2.Cu   | Plane   | FR-4 HiTg   | 35 um     | 2 oz
...
15     | In14.Cu  | Signal  | Megtron-7   | 17.5 um   | 0.5 oz
16     | In15.Cu  | Plane   | Faradflex   | 35 um     | 1 oz
17     | In16.Cu  | Plane   | Faradflex   | 35 um     | 2 oz
...
32     | B.Cu     | Signal  | Megtron-7   | 70 um     | 2 oz

Target Impedances:
  - PCIe Gen 6 differential: 85 ohm +/- 10%
  - SerDes 100G PAM4: 100 ohm differential +/- 10%
  - TFLN RF CPW: 50 ohm single-ended +/- 5%
  - CXL 2.0 differential: 85 ohm +/- 10%
  - LVDS trigger: 100 ohm differential +/- 10%
"""
    with open(filepath, "w") as f:
        f.write(notes)
    print(f"  Generated: {filepath}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating Ansys HFSS / SIwave import files...")
    print(f"Output directory: {out_dir}")
    print()

    generate_rf_cpw_dxf(os.path.join(out_dir, "TFLN_QPA_RF_CPW.dxf"))
    generate_mzi_electrode_dxf(
        os.path.join(out_dir, "TFLN_QPA_MZI_Electrodes.dxf"))
    generate_pyaedt_script(
        os.path.join(out_dir, "TFLN_QPA_HFSS_Setup.py"))
    generate_siwave_import_notes(
        os.path.join(out_dir, "SIwave_Import_Instructions.txt"))

    print()
    print("Done. Files ready for Ansys import.")

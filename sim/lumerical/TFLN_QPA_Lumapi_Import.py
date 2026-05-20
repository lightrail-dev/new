#!/usr/bin/env python3
"""
Lumerical Python API (lumapi) Import Script
LightRail AI LR-P3A Rev 6.3 — Quantum Photonic Accelerator

Automates GDSII import and simulation setup using Lumerical's Python API.
Works with FDTD, MODE, and INTERCONNECT products.

Prerequisites:
    - Lumerical 2024 R1+ installed
    - lumapi Python module accessible:
      Windows: C:\\Program Files\\Lumerical\\v241\\api\\python\\lumapi.py
      Linux:   /opt/lumerical/v241/api/python/lumapi.py
    - Add lumapi path to PYTHONPATH or sys.path before import

Usage:
    python3 TFLN_QPA_Lumapi_Import.py

If lumapi is not installed, the script prints manual import instructions.
"""

import os
import sys
import json

# --------------------------------------------------------------------------
# Design Constants (from QPA Architecture Spec)
# --------------------------------------------------------------------------

DESIGN = {
    "name": "LightRail LR-P3A Rev 6.3 — TFLN QPA",
    "board_width_mm": 420.0,
    "board_height_mm": 350.0,
    "wavelength_nm": 1550.0,
    "tfln_thickness_nm": 600,
    "slab_height_nm": 200,
    "wg_width_nm": 800,
    "n_eff": 2.211,
    "n_group": 2.35,
    "v_pi": 3.5,
    "num_channels": 8,
    "mzi_arm_length_um": 500,
    "mzi_arm_spacing_um": 5.0,
    "bend_radius_um": 50,
    "electrode_gap_um": 3.0,
    "electrode_width_um": 5.0,
}

# GDSII layer mapping (from GDS_LayerMap.txt)
GDS_LAYERS = {
    0:   {"name": "F.Cu",       "desc": "Top copper (electrodes, pads)"},
    31:  {"name": "B.Cu",       "desc": "Bottom copper"},
    32:  {"name": "F.SilkS",    "desc": "Top silkscreen"},
    33:  {"name": "B.SilkS",    "desc": "Bottom silkscreen"},
    34:  {"name": "F.Mask",     "desc": "Top solder mask"},
    35:  {"name": "B.Mask",     "desc": "Bottom solder mask"},
    36:  {"name": "F.Fab",      "desc": "Fabrication (NCE die pads)"},
    37:  {"name": "B.Fab",      "desc": "Bottom fabrication"},
    38:  {"name": "F.Paste",    "desc": "Top solder paste"},
    39:  {"name": "B.Paste",    "desc": "Bottom solder paste"},
    40:  {"name": "Dwgs.User",  "desc": "MZI photonic waveguides"},
    41:  {"name": "Cmts.User",  "desc": "Comments/annotations"},
    44:  {"name": "Edge.Cuts",  "desc": "Board outline"},
    46:  {"name": "B.CrtYd",    "desc": "Bottom courtyard"},
    47:  {"name": "F.CrtYd",    "desc": "Front courtyard"},
    48:  {"name": "Eco1.User",  "desc": "Green substrate fills (NCE/TFLN)"},
    49:  {"name": "Eco2.User",  "desc": "Photonic bridge region (magenta)"},
}
# Inner copper layers: GDS 100-129 → In1.Cu through In30.Cu
for i in range(30):
    GDS_LAYERS[100 + i] = {
        "name": f"In{i+1}.Cu",
        "desc": f"Inner copper layer {i+1}"
    }


def try_import_lumapi():
    """Try to import lumapi from standard installation paths."""
    lumapi_paths = [
        # Windows paths
        r"C:\Program Files\Lumerical\v241\api\python",
        r"C:\Program Files\Lumerical\v232\api\python",
        r"C:\Program Files\Lumerical\v231\api\python",
        r"C:\Program Files\Lumerical\v224\api\python",
        # Linux paths
        "/opt/lumerical/v241/api/python",
        "/opt/lumerical/v232/api/python",
        "/opt/lumerical/v231/api/python",
        "/opt/lumerical/v224/api/python",
        # macOS paths
        "/Applications/Lumerical/v241/api/python",
    ]

    for path in lumapi_paths:
        if os.path.isdir(path):
            sys.path.insert(0, path)
            try:
                import lumapi
                return lumapi
            except ImportError:
                continue

    return None


def setup_fdtd(lumapi, gds_file):
    """Set up FDTD simulation with GDSII import."""
    fdtd = lumapi.FDTD()

    # Import photonic waveguide layer
    fdtd.gdsimport(gds_file, "MZI_Waveguides", 40, 0,
                   0, DESIGN["tfln_thickness_nm"] * 1e-9,
                   "LiNbO3 (Lithium Niobate) - Ordinary")

    # Import electrode layer
    fdtd.gdsimport(gds_file, "Electrodes", 0, 0,
                   DESIGN["tfln_thickness_nm"] * 1e-9,
                   (DESIGN["tfln_thickness_nm"] + 200) * 1e-9,
                   "Au (Gold) - CRC")

    # Add mode source
    fdtd.addmode()
    fdtd.set("name", "mode_src")
    fdtd.set("injection axis", "x-axis")
    fdtd.set("wavelength start", 1500e-9)
    fdtd.set("wavelength stop", 1600e-9)

    # Add FDTD region
    fdtd.addfdtd()
    fdtd.set("mesh accuracy", 3)
    fdtd.set("simulation time", 5000e-15)

    # Add monitors
    fdtd.addpower()
    fdtd.set("name", "T_output")
    fdtd.set("monitor type", "2D X-normal")

    fdtd.addpower()
    fdtd.set("name", "field_profile")
    fdtd.set("monitor type", "2D Z-normal")
    fdtd.set("z", DESIGN["tfln_thickness_nm"] * 1e-9 / 2)

    print("FDTD simulation setup complete.")
    return fdtd


def setup_mode(lumapi, gds_file):
    """Set up MODE simulation for waveguide cross-section analysis."""
    mode = lumapi.MODE()

    # Create TFLN rib waveguide structure
    mode.addrect()
    mode.set("name", "BOX")
    mode.set("x span", 10e-6)
    mode.set("y min", -2e-6)
    mode.set("y max", 0)
    mode.set("material", "SiO2 (Glass) - Palik")

    mode.addrect()
    mode.set("name", "TFLN_Slab")
    mode.set("x span", 10e-6)
    mode.set("y min", 0)
    mode.set("y max", DESIGN["slab_height_nm"] * 1e-9)
    mode.set("material", "LiNbO3 (Lithium Niobate) - Ordinary")

    mode.addrect()
    mode.set("name", "TFLN_Rib")
    mode.set("x span", DESIGN["wg_width_nm"] * 1e-9)
    mode.set("y min", DESIGN["slab_height_nm"] * 1e-9)
    mode.set("y max", DESIGN["tfln_thickness_nm"] * 1e-9)
    mode.set("material", "LiNbO3 (Lithium Niobate) - Ordinary")

    # Add FDE solver
    mode.addfde()
    mode.set("solver type", "2D X normal")
    mode.set("wavelength", DESIGN["wavelength_nm"] * 1e-9)
    mode.set("number of trial modes", 6)
    mode.set("mesh cells y", 200)
    mode.set("mesh cells z", 200)

    print("MODE simulation setup complete.")
    return mode


def setup_interconnect(lumapi):
    """Set up INTERCONNECT circuit simulation for 8-channel MZI mesh."""
    ic = lumapi.INTERCONNECT()

    # MZI mesh configuration from mesh compiler
    mesh_config = [
        (1, 0, 0.42, 0.15), (1, 2, 0.67, 0.33),
        (1, 4, 0.55, 0.22), (1, 6, 0.81, 0.48),
        (2, 1, 0.38, 0.12), (2, 3, 0.72, 0.41),
        (2, 5, 0.59, 0.28),
        (3, 0, 0.44, 0.19), (3, 2, 0.63, 0.37),
        (3, 4, 0.51, 0.26), (3, 6, 0.77, 0.44),
        (4, 1, 0.35, 0.14), (4, 3, 0.69, 0.39),
        (4, 5, 0.56, 0.31),
        (5, 0, 0.48, 0.21), (5, 2, 0.61, 0.35),
        (5, 4, 0.53, 0.24), (5, 6, 0.73, 0.42),
        (6, 1, 0.41, 0.17), (6, 3, 0.66, 0.38),
        (6, 5, 0.57, 0.29),
        (7, 0, 0.46, 0.20), (7, 2, 0.64, 0.36),
        (7, 4, 0.52, 0.25), (7, 6, 0.75, 0.43),
    ]

    # Add CW laser source
    ic.addelement("CW Laser")
    ic.set("frequency", 3e8 / (DESIGN["wavelength_nm"] * 1e-9))
    ic.set("power", 0.01)  # 10 mW

    # Add MZI elements
    for layer, ch, theta_frac, phi_frac in mesh_config:
        name = f"MZI_L{layer}_CH{ch}"
        ic.addelement("Optical Mach-Zehnder Modulator")
        ic.set("name", name)

    # Add optical power meters at outputs
    for ch in range(DESIGN["num_channels"]):
        ic.addelement("Optical Power Meter")
        ic.set("name", f"PM_CH{ch}")

    print(f"INTERCONNECT setup complete: {len(mesh_config)} MZI nodes, "
          f"{DESIGN['num_channels']} output channels.")
    return ic


def print_manual_instructions():
    """Print manual import instructions when lumapi is not available."""
    print("=" * 70)
    print("TFLN QPA — Lumerical Import Instructions")
    print("LightRail AI LR-P3A Rev 6.3")
    print("=" * 70)
    print()
    print("lumapi not found. Use these manual import steps:")
    print()
    print("--- GDSII File ---")
    print("  File: Dual_NCE_Accelerator.gds (3.3 MB)")
    print("  Location: fab/Dual_NCE_Accelerator_Fab_Release_v1/")
    print()
    print("--- Lumerical FDTD (MZI Waveguide Simulation) ---")
    print("  1. Open Lumerical FDTD Solutions")
    print("  2. File > Script File Editor > Open: TFLN_MZI_FDTD.lsf")
    print("  3. Click Run (or type 'run;' in console)")
    print("  4. Or: File > Import > GDSII > select .gds file")
    print("     - Layer 40 (Dwgs.User) = MZI waveguides")
    print("     - z min = 0, z max = 600 nm")
    print("     - Material: LiNbO3")
    print()
    print("--- Lumerical MODE (Waveguide Mode Analysis) ---")
    print("  1. Open Lumerical MODE Solutions")
    print("  2. File > Script File Editor > Open: TFLN_Waveguide_MODE.lsf")
    print("  3. Click Run — computes TE/TM modes + width sweep")
    print()
    print("--- Lumerical INTERCONNECT (Circuit Simulation) ---")
    print("  1. Open Lumerical INTERCONNECT")
    print("  2. File > Script File Editor > Open: TFLN_QPA_INTERCONNECT.lsf")
    print("  3. Click Run — builds 8x8 MZI mesh circuit")
    print()
    print("--- GDSII Layer Mapping ---")
    for layer_num in sorted(GDS_LAYERS.keys()):
        info = GDS_LAYERS[layer_num]
        print(f"  GDS Layer {layer_num:>3d} → {info['name']:<12s} ({info['desc']})")
    print()
    print("--- Key Photonic Layers for Lumerical ---")
    print("  Layer 40 (Dwgs.User)  → MZI waveguide paths (import as TFLN)")
    print("  Layer 0  (F.Cu)       → Electrodes (import as Au)")
    print("  Layer 49 (Eco2.User)  → Photonic bridge region")
    print("  Layer 48 (Eco1.User)  → Substrate fill regions")
    print()
    print("--- S-Parameter Files (for INTERCONNECT co-simulation) ---")
    print("  sim/sparam/TFLN_CPW_50ohm_100GHz.s2p")
    print("  sim/sparam/TFLN_MZI_Optical_2x2.s2p")
    print("  sim/sparam/CXL_Diff_Pair_85ohm.s4p")
    print("  sim/sparam/LVDS_Trigger_100ohm.s2p")


def export_design_json(filepath):
    """Export design parameters as JSON for tool interop."""
    data = {
        "project": DESIGN,
        "gds_layers": {str(k): v for k, v in GDS_LAYERS.items()},
        "photonic_layers": {
            "waveguides": 40,
            "electrodes": 0,
            "photonic_bridge": 49,
            "substrate_fill": 48,
            "board_outline": 44,
        },
        "simulation_files": {
            "fdtd_script": "TFLN_MZI_FDTD.lsf",
            "mode_script": "TFLN_Waveguide_MODE.lsf",
            "interconnect_script": "TFLN_QPA_INTERCONNECT.lsf",
            "gds_import_script": "TFLN_GDS_Import.lsf",
            "lumapi_script": "TFLN_QPA_Lumapi_Import.py",
        },
        "sparam_files": [
            "TFLN_CPW_50ohm_100GHz.s2p",
            "TFLN_MZI_Optical_2x2.s2p",
            "CXL_Diff_Pair_85ohm.s4p",
            "LVDS_Trigger_100ohm.s2p",
        ],
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Design parameters exported to: {filepath}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Export design parameters JSON
    export_design_json(os.path.join(script_dir, "design_params.json"))

    # Try lumapi
    lumapi = try_import_lumapi()

    if lumapi is None:
        print_manual_instructions()
    else:
        gds_file = os.path.join(
            script_dir, "..", "..", "fab",
            "Dual_NCE_Accelerator_Fab_Release_v1",
            "Dual_NCE_Accelerator.gds"
        )

        if not os.path.exists(gds_file):
            print(f"GDSII file not found at: {gds_file}")
            print("Update the path to your local copy of Dual_NCE_Accelerator.gds")
        else:
            print(f"GDSII file: {gds_file}")
            print()
            setup_fdtd(lumapi, gds_file)
            setup_mode(lumapi, gds_file)
            setup_interconnect(lumapi)

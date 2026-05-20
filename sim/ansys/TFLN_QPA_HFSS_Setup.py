#!/usr/bin/env python3
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

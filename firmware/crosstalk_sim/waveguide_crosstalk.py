#!/usr/bin/env python3
"""
Spatial Crosstalk Simulation — Coupled-Mode Theory

Simulates optical power transfer between parallel TFLN waveguides to ensure
minimum spacing requirements are met for the LR-P3A quantum photonic
accelerator. Uses evanescent coupling theory:

    κ² ∝ exp(-α · d)

where d is the waveguide gap and α is the decay constant.

OCP infrastructure requires crosstalk < -30 dB, mandating minimum
waveguide gap of ≥ 5.0 µm at 1550 nm operating wavelength.

This simulation is used during PCB layout validation to verify that
the MZI photonic waveguide mesh meets isolation requirements.
"""

import numpy as np
from typing import Tuple, List, Dict


def simulate_waveguide_crosstalk(
    length_mm: float,
    gap_um: float,
    wavelength_nm: float = 1550.0,
    coupling_base: float = 1.2,
    decay_alpha: float = 0.85
) -> Tuple[float, float, float]:
    """Simulate optical power transfer between two parallel TFLN waveguides.

    Args:
        length_mm: Interaction length in millimeters.
        gap_um: Waveguide center-to-center gap in micrometers.
        wavelength_nm: Operating wavelength (default 1550 nm C-band).
        coupling_base: Base coupling strength (material-dependent).
        decay_alpha: Evanescent field decay constant.

    Returns:
        (power_ch0, power_ch1, crosstalk_db): Power in each channel and
        crosstalk in dB. Negative dB values indicate good isolation.
    """
    kappa = coupling_base * np.exp(-decay_alpha * gap_um)
    power_ch1 = np.sin(kappa * length_mm) ** 2
    power_ch0 = 1.0 - power_ch1
    crosstalk_db = 10.0 * np.log10(power_ch1 / (power_ch0 + 1e-12))
    return power_ch0, power_ch1, crosstalk_db


def find_minimum_gap(
    length_mm: float,
    target_crosstalk_db: float = -30.0,
    wavelength_nm: float = 1550.0,
    search_range: Tuple[float, float] = (1.0, 10.0),
    resolution: float = 0.1
) -> float:
    """Find the minimum waveguide gap that meets crosstalk target.

    Uses bisection search to find the smallest gap where crosstalk
    is below the target threshold.
    """
    lo, hi = search_range
    while hi - lo > resolution:
        mid = (lo + hi) / 2.0
        _, _, xt_db = simulate_waveguide_crosstalk(length_mm, mid, wavelength_nm)
        if xt_db < target_crosstalk_db:
            hi = mid
        else:
            lo = mid
    return hi


def simulate_mzi_array_crosstalk(
    num_channels: int,
    pitch_um: float,
    interaction_length_mm: float,
    wavelength_nm: float = 1550.0
) -> Dict[str, float]:
    """Simulate crosstalk across an array of parallel MZI waveguides.

    Models nearest-neighbor and next-nearest-neighbor coupling for
    the full MZI mesh array used in the NCE photonic accelerator.

    Returns:
        Dictionary with worst-case and average crosstalk metrics.
    """
    nearest_xt = []
    next_nearest_xt = []

    for i in range(num_channels - 1):
        _, _, xt = simulate_waveguide_crosstalk(
            interaction_length_mm, pitch_um, wavelength_nm
        )
        nearest_xt.append(xt)

    for i in range(num_channels - 2):
        _, _, xt = simulate_waveguide_crosstalk(
            interaction_length_mm, 2.0 * pitch_um, wavelength_nm
        )
        next_nearest_xt.append(xt)

    return {
        "num_channels": num_channels,
        "pitch_um": pitch_um,
        "interaction_length_mm": interaction_length_mm,
        "worst_case_nearest_db": max(nearest_xt) if nearest_xt else -999.0,
        "avg_nearest_db": np.mean(nearest_xt) if nearest_xt else -999.0,
        "worst_case_next_nearest_db": max(next_nearest_xt) if next_nearest_xt else -999.0,
        "ocp_compliant": all(xt < -30.0 for xt in nearest_xt),
    }


def generate_crosstalk_report(
    gaps_um: List[float] = None,
    interaction_length_mm: float = 2.5,
    wavelength_nm: float = 1550.0
) -> str:
    """Generate a formatted crosstalk analysis report for design review."""
    if gaps_um is None:
        gaps_um = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]

    lines = [
        "=" * 65,
        "TFLN Waveguide Spatial Crosstalk Analysis",
        f"Interaction Length: {interaction_length_mm} mm | λ = {wavelength_nm} nm",
        "OCP Requirement: Crosstalk < -30 dB",
        "=" * 65,
        f"{'Gap (µm)':>10} {'P_main':>10} {'P_coupled':>12} {'Crosstalk':>12} {'Status':>10}",
        "-" * 65,
    ]

    for gap in gaps_um:
        p0, p1, xt = simulate_waveguide_crosstalk(
            interaction_length_mm, gap, wavelength_nm
        )
        status = "PASS" if xt < -30.0 else "FAIL"
        lines.append(
            f"{gap:>10.1f} {p0:>10.6f} {p1:>12.2e} {xt:>12.1f} dB {status:>10}"
        )

    min_gap = find_minimum_gap(interaction_length_mm, -30.0, wavelength_nm)
    lines.append("-" * 65)
    lines.append(f"Minimum gap for -30 dB isolation: {min_gap:.1f} µm")

    # 8-channel and 16-channel array analysis
    lines.append("")
    lines.append("--- MZI Array Crosstalk (per NCE) ---")
    for nch, pitch in [(8, 5.0), (8, 6.0), (16, 5.0), (16, 6.0)]:
        result = simulate_mzi_array_crosstalk(
            nch, pitch, interaction_length_mm, wavelength_nm
        )
        lines.append(
            f"  {nch}ch @ {pitch}µm pitch: "
            f"worst={result['worst_case_nearest_db']:.1f} dB, "
            f"avg={result['avg_nearest_db']:.1f} dB — "
            f"{'OCP COMPLIANT' if result['ocp_compliant'] else 'NON-COMPLIANT'}"
        )

    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_crosstalk_report())

#!/usr/bin/env python3
"""
Block Diagram Generator - LightRail AI LR-P3A Rev 6.3
Full Motherboard Architecture - Landscape Layout

TFLN Quantum Photonic Accelerator (QPA) + Dual Neural Compute Engine (NCE)
420 x 350 mm | 32-Layer HDI | Megtron-7/Faradflex | ENIG

Output: docs/LR_P3A_QPA_Block_Diagram.png
        docs/LR_P3A_QPA_Block_Diagram.pdf
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def draw_block(ax, x, y, w, h, label, color="#2196F3", text_color="white",
               fontsize=9, alpha=0.9, sublabel=None, style="round",
               linewidth=1.5, edgecolor=None):
    if edgecolor is None:
        edgecolor = color
    if style == "round":
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015",
                             facecolor=color, edgecolor=edgecolor,
                             alpha=alpha, linewidth=linewidth, zorder=2)
    else:
        box = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0.008",
                             facecolor=color, edgecolor=edgecolor,
                             alpha=alpha, linewidth=linewidth, zorder=2)
    ax.add_patch(box)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 + 0.012, label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color=text_color, zorder=3)
        ax.text(x + w / 2, y + h / 2 - 0.010, sublabel,
                ha="center", va="center", fontsize=fontsize - 1.5,
                color=text_color, alpha=1.0, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color=text_color, zorder=3)


def draw_arrow(ax, x1, y1, x2, y2, color="#333333", style="->", lw=1.0,
               connectionstyle="arc3,rad=0", label=None, label_fontsize=7):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, color=color,
                            connectionstyle=connectionstyle,
                            linewidth=lw, zorder=4, mutation_scale=10)
    ax.add_patch(arrow)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.008, label, ha="center", va="center",
                fontsize=label_fontsize, color=color, fontweight="bold",
                zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                          edgecolor="none", alpha=0.9))


def draw_bus(ax, x1, y1, x2, y2, color="#FF5722", lw=3.0, label=None,
             label_fontsize=7):
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, zorder=3,
            solid_capstyle="round")
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.003, my + 0.008, label, ha="center", va="center",
                fontsize=label_fontsize, color=color, zorder=5,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                          edgecolor=color, alpha=0.95, linewidth=0.6))


def draw_region(ax, x, y, w, h, label, color="#E3F2FD", edgecolor="#1565C0",
                fontsize=9, alpha=0.25):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.008",
                                    facecolor=color, edgecolor=edgecolor,
                                    alpha=alpha, linewidth=2.0,
                                    linestyle="--", zorder=1)
    ax.add_patch(rect)
    ax.text(x + 0.004, y + h - 0.010, label,
            ha="left", va="top", fontsize=fontsize,
            fontweight="bold", color=edgecolor, alpha=1.0, zorder=2)


def generate_block_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(36, 22), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    # CONFIDENTIAL banner (top)
    ax.text(0.5, 0.985, "CONFIDENTIAL \u2014 Property of LightRail AI Labs",
            ha="center", va="center", fontsize=12, fontweight="bold",
            color="#B71C1C", zorder=10,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFEBEE",
                      edgecolor="#B71C1C", alpha=0.95, linewidth=1.5))

    ax.text(0.5, 0.968, "LightRail AI LR-P3A Rev 6.3 \u2014 Motherboard System Block Diagram",
            ha="center", va="center", fontsize=18, fontweight="bold", color="#0D47A1")
    ax.text(0.5, 0.955, "TFLN Quantum Photonic Accelerator (QPA) + Dual Neural Compute Engine (NCE)",
            ha="center", va="center", fontsize=11, fontweight="bold", color="#424242")
    ax.text(0.5, 0.944,
            "420 x 350 mm  |  32-Layer HDI  |  Megtron-7 / Faradflex  |  "
            "ENIG  |  9,418 Pads  |  142 Nets  |  22,493 Traces",
            ha="center", va="center", fontsize=8, color="#666666")

    # Region boundaries
    draw_region(ax, 0.01, 0.85, 0.98, 0.08, "HOST CPU / SERVER PLATFORM", "#FFF3E0", "#BF360C", fontsize=9)
    draw_region(ax, 0.01, 0.38, 0.28, 0.46, "NCE-A (Neural Compute Engine A)", "#E3F2FD", "#1565C0", fontsize=8)
    draw_region(ax, 0.30, 0.28, 0.40, 0.56, "QUANTUM PHOTONIC ACCELERATOR (QPA)", "#F3E5F5", "#6A1B9A", fontsize=9)
    draw_region(ax, 0.71, 0.38, 0.28, 0.46, "NCE-B (Neural Compute Engine B)", "#E3F2FD", "#1565C0", fontsize=8)
    draw_region(ax, 0.01, 0.14, 0.28, 0.23, "HIGH-SPEED NETWORKING & I/O", "#FFF8E1", "#F57F17", fontsize=8)
    draw_region(ax, 0.30, 0.04, 0.40, 0.23, "POWER DELIVERY NETWORK (PDN)", "#E8F5E9", "#2E7D32", fontsize=8)
    draw_region(ax, 0.71, 0.14, 0.28, 0.23, "THERMAL / STORAGE / EXPANSION", "#FFEBEE", "#B71C1C", fontsize=8)
    draw_region(ax, 0.01, 0.04, 0.28, 0.09, "BOARD MANAGEMENT & DEBUG", "#E0E0E0", "#424242", fontsize=7)
    draw_region(ax, 0.71, 0.04, 0.28, 0.09, "CLOCK DISTRIBUTION", "#E8EAF6", "#283593", fontsize=7)

    # HOST CPU / SERVER PLATFORM
    draw_block(ax, 0.02, 0.86, 0.14, 0.06, "Host CPU", "#B71C1C", sublabel="Xeon / EPYC\nLGA-4677 / SP5", fontsize=10)
    draw_block(ax, 0.17, 0.87, 0.08, 0.045, "DDR5", "#1565C0", sublabel="8-Ch RDIMM\n512 GB Total", fontsize=7.5)
    draw_block(ax, 0.26, 0.87, 0.09, 0.045, "PCIe Gen6", "#E65100", sublabel="Root Complex\n128 Lanes", fontsize=7.5)
    draw_block(ax, 0.36, 0.87, 0.09, 0.045, "CXL 2.0", "#AD1457", sublabel="Type 3 Host\n68 Lanes", fontsize=7.5)
    draw_block(ax, 0.46, 0.86, 0.12, 0.06, "Platform Controller\nHub (PCH)", "#37474F", sublabel="USB 3.2 / SATA / LPC / SPI", fontsize=8)
    draw_block(ax, 0.59, 0.86, 0.10, 0.06, "BMC (AST2600)", "#546E7A", sublabel="OpenBMC\nIPMI 2.0 / Redfish", fontsize=7.5)
    draw_block(ax, 0.70, 0.87, 0.07, 0.045, "UEFI Flash", "#455A64", sublabel="64 MB SPI\nSecure Boot", fontsize=7)
    draw_block(ax, 0.78, 0.87, 0.06, 0.045, "TPM 2.0", "#455A64", sublabel="SPI / I2C\nAttestation", fontsize=7)
    draw_block(ax, 0.85, 0.86, 0.07, 0.06, "ATX 24-pin", "#2E7D32", sublabel="Main Power\nInput", fontsize=7)
    draw_block(ax, 0.93, 0.86, 0.06, 0.06, "EPS 8-pin", "#2E7D32", sublabel="CPU 12V\nx 2", fontsize=7)

    # NCE-A COMPUTE COMPLEX
    draw_block(ax, 0.03, 0.68, 0.24, 0.12, "NCE-A Die", "#0D47A1", sublabel="AI Accelerator ASIC\nBGA-2500 | 250W TDP | 5nm", fontsize=11)
    draw_block(ax, 0.03, 0.62, 0.055, 0.05, "HBM4-A1", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.095, 0.62, 0.055, 0.05, "HBM4-A2", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.16, 0.62, 0.055, 0.05, "HBM4-A3", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.225, 0.62, 0.055, 0.05, "HBM4-A4", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.03, 0.56, 0.12, 0.05, "SerDes 100G", "#006064", sublabel="PAM4 x 16 lanes", fontsize=7.5)
    draw_block(ax, 0.16, 0.56, 0.12, 0.05, "PCIe Gen6 x16", "#006064", sublabel="To Host CPU", fontsize=7.5)
    draw_block(ax, 0.03, 0.49, 0.25, 0.06, "TFLN CPO-A", "#4A148C", sublabel="Co-Packaged Optics | 1.6T Bandwidth | 16 Channels", fontsize=9, alpha=0.95)
    draw_block(ax, 0.03, 0.40, 0.12, 0.07, "DrMOS VRM\nNCE-A", "#2E7D32", sublabel="6-Phase ISL69260\n0.85V Core", fontsize=7.5)
    draw_block(ax, 0.16, 0.40, 0.12, 0.07, "Decoupling\nArray A", "#4CAF50", sublabel="138 Caps\n01005 to Tantalum", fontsize=7.5)

    # NCE-B COMPUTE COMPLEX (mirror)
    draw_block(ax, 0.73, 0.68, 0.24, 0.12, "NCE-B Die", "#0D47A1", sublabel="AI Accelerator ASIC\nBGA-2500 | 250W TDP | 5nm", fontsize=11)
    draw_block(ax, 0.73, 0.62, 0.055, 0.05, "HBM4-B1", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.795, 0.62, 0.055, 0.05, "HBM4-B2", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.86, 0.62, 0.055, 0.05, "HBM4-B3", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.925, 0.62, 0.055, 0.05, "HBM4-B4", "#1B5E20", sublabel="32 GB", fontsize=7)
    draw_block(ax, 0.73, 0.56, 0.12, 0.05, "SerDes 100G", "#006064", sublabel="PAM4 x 16 lanes", fontsize=7.5)
    draw_block(ax, 0.86, 0.56, 0.12, 0.05, "PCIe Gen6 x16", "#006064", sublabel="To Host CPU", fontsize=7.5)
    draw_block(ax, 0.73, 0.49, 0.25, 0.06, "TFLN CPO-B", "#4A148C", sublabel="Co-Packaged Optics | 1.6T Bandwidth | 16 Channels", fontsize=9, alpha=0.95)
    draw_block(ax, 0.73, 0.40, 0.12, 0.07, "DrMOS VRM\nNCE-B", "#2E7D32", sublabel="6-Phase ISL69260\n0.85V Core", fontsize=7.5)
    draw_block(ax, 0.86, 0.40, 0.12, 0.07, "Decoupling\nArray B", "#4CAF50", sublabel="138 Caps\n01005 to Tantalum", fontsize=7.5)

    # QPA PHOTONIC ACCELERATOR (center)
    draw_block(ax, 0.38, 0.74, 0.24, 0.08, "CXL 2.0 Switch", "#AD1457", sublabel="Microchip PM40028\n68 Lanes | Type 3 Pooling", fontsize=10)
    draw_block(ax, 0.31, 0.64, 0.09, 0.08, "FPGA-1", "#E65100", sublabel="Kintex\nUltraScale+\nTrigger Matrix", fontsize=7)
    draw_block(ax, 0.41, 0.64, 0.09, 0.08, "DAC-1", "#C62828", sublabel="100 GHz\nInterleaved\n14-bit", fontsize=7)
    draw_block(ax, 0.51, 0.64, 0.09, 0.08, "DAC-2", "#C62828", sublabel="100 GHz\nInterleaved\n14-bit", fontsize=7)
    draw_block(ax, 0.61, 0.64, 0.08, 0.08, "FPGA-2", "#E65100", sublabel="Kintex\nUltraScale+\nCXL Host IF", fontsize=7)

    draw_block(ax, 0.31, 0.53, 0.38, 0.10, "RF Driver Array", "#BF360C", sublabel="8x BiCMOS SiGe RF Drivers  |  Push-Pull  |  6 Vpp Swing  |  60 GHz BW  |  CPW 50\u03A9", fontsize=9)

    draw_block(ax, 0.31, 0.38, 0.38, 0.14, "TFLN MZI Mesh", "#4A148C",
               sublabel="8x8 Clements Decomposition  |  25 MZI Nodes\n"
               "500 \u00b5m Arm Length  |  5 \u00b5m Spacing  |  800 nm WG Width\n"
               "600 nm TFLN  |  1550 nm C-band  |  EO Phase Shifters",
               fontsize=10, alpha=0.95)

    draw_block(ax, 0.31, 0.30, 0.12, 0.07, "SNSPD Array 1", "#311B92", sublabel="8-Ch NbN Detectors\n< 50 ps Jitter", fontsize=7.5)
    draw_block(ax, 0.44, 0.30, 0.12, 0.07, "SNSPD Array 2", "#311B92", sublabel="8-Ch NbN Detectors\n< 50 ps Jitter", fontsize=7.5)
    draw_block(ax, 0.57, 0.30, 0.12, 0.07, "Q-Memory", "#1A237E", sublabel="Quantum Memory\nCoherence Buffer\nRare-Earth Ion", fontsize=7.5)

    # HIGH-SPEED NETWORKING & I/O
    draw_block(ax, 0.02, 0.30, 0.12, 0.06, "QSFP-DD x8", "#E65100", sublabel="400G / 800G\nOptical Cages", fontsize=8)
    draw_block(ax, 0.15, 0.30, 0.12, 0.06, "Optical TRX", "#BF360C", sublabel="DR4/FR4\nTransceivers", fontsize=8)
    draw_block(ax, 0.02, 0.23, 0.08, 0.06, "100GbE", "#00695C", sublabel="ASIC Switch\nMellanox", fontsize=7)
    draw_block(ax, 0.11, 0.23, 0.08, 0.06, "InfiniBand", "#004D40", sublabel="HDR 200G\nConnectX-7", fontsize=7)
    draw_block(ax, 0.20, 0.23, 0.08, 0.06, "USB 3.2", "#37474F", sublabel="Gen2 x2\nType-C x4", fontsize=7)
    draw_block(ax, 0.02, 0.15, 0.08, 0.06, "UART", "#546E7A", sublabel="Console\n115200 bps", fontsize=7)
    draw_block(ax, 0.11, 0.15, 0.08, 0.06, "Eth Mgmt", "#455A64", sublabel="1G RJ45\nBMC Port", fontsize=7)
    draw_block(ax, 0.20, 0.15, 0.08, 0.06, "GPIO / LED", "#607D8B", sublabel="Status / Fault\nIndicators", fontsize=7)

    # POWER DELIVERY NETWORK
    draw_block(ax, 0.31, 0.20, 0.10, 0.06, "12V Main\nATX Input", "#1B5E20", sublabel="24-pin + EPS\n1200W Total", fontsize=8)
    draw_block(ax, 0.42, 0.20, 0.08, 0.06, "VRM NCE-A", "#2E7D32", sublabel="6-Phase\n0.85V / 300A", fontsize=7)
    draw_block(ax, 0.51, 0.20, 0.08, 0.06, "VRM NCE-B", "#2E7D32", sublabel="6-Phase\n0.85V / 300A", fontsize=7)
    draw_block(ax, 0.60, 0.20, 0.08, 0.06, "VRM QPA", "#388E3C", sublabel="4-Phase\n1.2V / 80A", fontsize=7)
    draw_block(ax, 0.31, 0.13, 0.08, 0.06, "VRM HBM4", "#43A047", sublabel="1.1V\n2x 60A", fontsize=7)
    draw_block(ax, 0.40, 0.13, 0.08, 0.06, "VRM DDR5", "#4CAF50", sublabel="1.1V\n4-Ch", fontsize=7)
    draw_block(ax, 0.49, 0.13, 0.08, 0.06, "VRM CPU", "#66BB6A", sublabel="1.8V\n8-Phase", fontsize=7)
    draw_block(ax, 0.58, 0.13, 0.09, 0.06, "Standby +5V", "#81C784", sublabel="Always-On\nBMC / RTC", fontsize=7)
    draw_block(ax, 0.31, 0.05, 0.36, 0.06, "PCB Power Plane Stackup", "#A5D6A7",
               text_color="#1B5E20",
               sublabel="In3: VCC_NCE_A (0.85V)  |  In4: VCC_NCE_B (0.85V)  |  In5: VCC_QPA (1.2V)  |  In6: GND  |  In7: VCC_HBM (1.1V)  |  In8: VCC_DDR5 (1.1V)",
               fontsize=7)

    # THERMAL / STORAGE / EXPANSION
    draw_block(ax, 0.72, 0.30, 0.12, 0.06, "CVD Diamond\nSubstrate", "#B71C1C", sublabel="NCE Heat Spreader\n2000 W/mK", fontsize=7.5)
    draw_block(ax, 0.85, 0.30, 0.13, 0.06, "Liquid Cold\nPlate", "#C62828", sublabel="CPU + NCE Loop\n500W Capacity", fontsize=7.5)
    draw_block(ax, 0.72, 0.23, 0.08, 0.06, "Fan Hdr x6", "#E53935", sublabel="4-pin PWM\nTach Monitor", fontsize=7)
    draw_block(ax, 0.81, 0.23, 0.08, 0.06, "Temp\nSensors", "#EF5350", sublabel="8x NTC\nI2C / SMBus", fontsize=7)
    draw_block(ax, 0.90, 0.23, 0.08, 0.06, "Pressure\nSensor", "#EF5350", sublabel="Coolant\nFlow Rate", fontsize=7)
    draw_block(ax, 0.72, 0.15, 0.10, 0.06, "NVMe M.2", "#37474F", sublabel="Gen5 x4\n2 Slots", fontsize=7.5)
    draw_block(ax, 0.83, 0.15, 0.10, 0.06, "U.2 / EDSFF", "#455A64", sublabel="Gen5 x4\n4 Bays", fontsize=7.5)
    draw_block(ax, 0.94, 0.15, 0.05, 0.06, "SATA\nx4", "#546E7A", sublabel="6 Gbps", fontsize=6)

    # BOARD MANAGEMENT & DEBUG
    draw_block(ax, 0.02, 0.045, 0.06, 0.06, "JTAG", "#424242", sublabel="Chain\nBoundary\nScan", fontsize=6.5)
    draw_block(ax, 0.09, 0.045, 0.06, 0.06, "I2C /\nSMBus", "#424242", sublabel="Mux\n8-Channel", fontsize=6.5)
    draw_block(ax, 0.16, 0.045, 0.06, 0.06, "SPI Flash", "#424242", sublabel="BIOS\n+ BMC FW", fontsize=6.5)
    draw_block(ax, 0.23, 0.045, 0.05, 0.06, "CPLD", "#424242", sublabel="Lattice\nMachXO3", fontsize=6.5)

    # CLOCK DISTRIBUTION
    draw_block(ax, 0.72, 0.045, 0.08, 0.06, "Ref Clock", "#283593", sublabel="100 MHz\nOCXO / TCXO", fontsize=7)
    draw_block(ax, 0.81, 0.045, 0.09, 0.06, "PLL / Jitter\nCleaner", "#283593", sublabel="Si5345B\n< 100 fs RMS", fontsize=7)
    draw_block(ax, 0.91, 0.045, 0.08, 0.06, "Clock\nFanout", "#283593", sublabel="1:12 LVDS\nTree Buffer", fontsize=7)

    # ===== DATA FLOW CONNECTIONS =====

    # Host CPU -> NCE-A (PCIe Gen6)
    draw_bus(ax, 0.16, 0.86, 0.16, 0.80, "#E65100", lw=3, label="PCIe Gen6 x16")
    draw_arrow(ax, 0.16, 0.80, 0.22, 0.80, "#E65100", lw=1.5)
    # Host CPU -> NCE-B (PCIe Gen6)
    draw_bus(ax, 0.30, 0.87, 0.30, 0.84, "#E65100", lw=3)
    draw_arrow(ax, 0.84, 0.86, 0.84, 0.80, "#E65100", lw=1.5)
    draw_bus(ax, 0.84, 0.86, 0.92, 0.86, "#E65100", lw=1)
    # Host CPU -> QPA (CXL 2.0)
    draw_bus(ax, 0.40, 0.87, 0.40, 0.82, "#AD1457", lw=3.5, label="CXL 2.0 x68")
    draw_arrow(ax, 0.50, 0.87, 0.50, 0.82, "#AD1457", lw=2)
    # Host CPU <-> DDR5
    draw_bus(ax, 0.16, 0.89, 0.17, 0.89, "#1565C0", lw=4, label="DDR5-6400")
    # Host CPU -> PCH
    draw_bus(ax, 0.35, 0.89, 0.46, 0.89, "#37474F", lw=2, label="DMI 4.0")
    # PCH -> BMC
    draw_bus(ax, 0.58, 0.89, 0.59, 0.89, "#546E7A", lw=1.5, label="LPC/eSPI")
    # NCE-A CPO <-> QPA (optical)
    draw_bus(ax, 0.28, 0.52, 0.31, 0.52, "#9C27B0", lw=4, label="1.6T Optical")
    draw_bus(ax, 0.28, 0.50, 0.31, 0.50, "#9C27B0", lw=4)
    # NCE-B CPO <-> QPA (optical)
    draw_bus(ax, 0.69, 0.52, 0.73, 0.52, "#9C27B0", lw=4, label="1.6T Optical")
    draw_bus(ax, 0.69, 0.50, 0.73, 0.50, "#9C27B0", lw=4)
    # QPA internal dataflow
    draw_arrow(ax, 0.50, 0.74, 0.50, 0.72, "#AD1457", lw=2, label="CXL Fabric")
    draw_arrow(ax, 0.36, 0.64, 0.36, 0.63, "#E65100", lw=1.5)
    draw_arrow(ax, 0.46, 0.64, 0.46, 0.63, "#C62828", lw=1.5)
    draw_arrow(ax, 0.56, 0.64, 0.56, 0.63, "#C62828", lw=1.5)
    draw_arrow(ax, 0.50, 0.53, 0.50, 0.52, "#BF360C", lw=2, label="RF Drive")
    draw_arrow(ax, 0.50, 0.38, 0.50, 0.37, "#4A148C", lw=2, label="Photon Detect")
    # NCE-A -> HBM4 stacks
    draw_bus(ax, 0.06, 0.68, 0.06, 0.67, "#1B5E20", lw=3, label="HBM4 IF")
    draw_bus(ax, 0.12, 0.68, 0.12, 0.67, "#1B5E20", lw=3)
    draw_bus(ax, 0.19, 0.68, 0.19, 0.67, "#1B5E20", lw=3)
    draw_bus(ax, 0.25, 0.68, 0.25, 0.67, "#1B5E20", lw=3)
    # NCE-B -> HBM4 stacks
    draw_bus(ax, 0.76, 0.68, 0.76, 0.67, "#1B5E20", lw=3, label="HBM4 IF")
    draw_bus(ax, 0.82, 0.68, 0.82, 0.67, "#1B5E20", lw=3)
    draw_bus(ax, 0.89, 0.68, 0.89, 0.67, "#1B5E20", lw=3)
    draw_bus(ax, 0.95, 0.68, 0.95, 0.67, "#1B5E20", lw=3)
    # NCE-A SerDes -> QSFP-DD
    draw_arrow(ax, 0.09, 0.56, 0.09, 0.36, "#006064", lw=1.5, label="100G SerDes")
    # NCE-B SerDes -> QSFP-DD
    draw_arrow(ax, 0.79, 0.56, 0.79, 0.36, "#006064", lw=1.5, label="100G SerDes")
    # Power delivery arrows
    draw_arrow(ax, 0.36, 0.26, 0.36, 0.27, "#1B5E20", lw=1.5, label="12V Rail")
    draw_arrow(ax, 0.46, 0.26, 0.15, 0.40, "#2E7D32", lw=1.0, label="0.85V NCE-A")
    draw_arrow(ax, 0.55, 0.26, 0.85, 0.40, "#2E7D32", lw=1.0, label="0.85V NCE-B")
    draw_arrow(ax, 0.64, 0.26, 0.64, 0.30, "#388E3C", lw=1.0, label="1.2V QPA")
    # Clock distribution
    draw_arrow(ax, 0.80, 0.075, 0.81, 0.075, "#283593", lw=1.5)
    draw_arrow(ax, 0.90, 0.075, 0.91, 0.075, "#283593", lw=1.5)
    draw_arrow(ax, 0.95, 0.105, 0.95, 0.15, "#283593", lw=1.0, label="Clocks")
    # Board mgmt -> all subsystems
    draw_bus(ax, 0.15, 0.11, 0.85, 0.11, "#757575", lw=1.5, label="I2C / SMBus Management Bus")

    # ===== IMPEDANCE CALLOUTS =====
    impedance_text = (
        "Impedance Targets:\n"
        "PCIe Gen6: 85\u03A9 diff  |  CXL 2.0: 85\u03A9 diff  |  "
        "SerDes: 100\u03A9 diff  |  DDR5: 40\u03A9 SE\n"
        "RF CPW: 50\u03A9 SE  |  LVDS Clk: 100\u03A9 diff  |  "
        "USB 3.2: 90\u03A9 diff  |  HBM4 PHY: 40\u03A9 SE"
    )
    ax.text(0.5, 0.005, impedance_text,
            ha="center", va="bottom", fontsize=7, color="#37474F",
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#ECEFF1",
                      edgecolor="#90A4AE", alpha=0.9, linewidth=0.8))

    # ===== LEGEND =====
    legend_items = [
        ("#B71C1C", "Host CPU / Server"),
        ("#0D47A1", "NCE Die (AI ASIC)"),
        ("#1B5E20", "HBM4 Memory"),
        ("#4A148C", "TFLN Photonic (CPO/MZI)"),
        ("#AD1457", "CXL 2.0 Fabric"),
        ("#E65100", "PCIe Gen6 / FPGA"),
        ("#C62828", "DAC / RF Analog"),
        ("#311B92", "SNSPD / Q-Memory"),
        ("#006064", "SerDes / High-Speed I/O"),
        ("#2E7D32", "Power Delivery"),
        ("#B71C1C", "Thermal Management"),
        ("#283593", "Clock Distribution"),
    ]
    lx = 0.01
    ly = 0.002
    for i, (color, name) in enumerate(legend_items):
        xi = lx + i * 0.082
        ax.add_patch(mpatches.Rectangle((xi, ly), 0.012, 0.012,
                                         facecolor=color, edgecolor="white",
                                         linewidth=0.5, zorder=5))
        ax.text(xi + 0.015, ly + 0.006, name, fontsize=6, va="center",
                color="#333333", fontweight="bold", zorder=5)

    # CONFIDENTIAL banner (bottom)
    ax.text(0.5, 0.935, "",
            ha="center", va="center", fontsize=1, color="white")
    fig.text(0.5, 0.008, "CONFIDENTIAL \u2014 Property of LightRail AI Labs  |  "
             "LR-P3A Rev 6.3  |  Do Not Distribute",
             ha="center", va="bottom", fontsize=9, fontweight="bold",
             color="#B71C1C",
             bbox=dict(boxstyle="round,pad=0.25", facecolor="#FFEBEE",
                       edgecolor="#B71C1C", alpha=0.95, linewidth=1.5))

    # Light background
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FFFFFF")

    # Save outputs
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(out_dir, "LR_P3A_QPA_Block_Diagram.png")
    pdf_path = os.path.join(out_dir, "LR_P3A_QPA_Block_Diagram.pdf")

    plt.tight_layout(pad=1.5)
    fig.savefig(png_path, dpi=300, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"Generated: {png_path}")
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    generate_block_diagram()


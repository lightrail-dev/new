#!/usr/bin/env python3
"""
Block Diagram Generator - LightRail AI LR-P3A Rev 6.3
Full Motherboard Architecture - Landscape Layout
Black & White Sketch Style

Output: docs/LR_P3A_QPA_Block_Diagram.png
        docs/LR_P3A_QPA_Block_Diagram.pdf
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def draw_block(ax, x, y, w, h, label, fontsize=10, sublabel=None,
               linewidth=1.8, fill="white", hatch="", bold_border=False):
    lw = 2.5 if bold_border else linewidth
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                         facecolor=fill, edgecolor="black",
                         alpha=1.0, linewidth=lw, zorder=2, hatch=hatch)
    ax.add_patch(box)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 + 0.013, label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color="black", zorder=3,
                fontfamily="sans-serif")
        ax.text(x + w / 2, y + h / 2 - 0.012, sublabel,
                ha="center", va="center", fontsize=fontsize - 1.5,
                color="#333333", zorder=3, fontfamily="sans-serif")
    else:
        ax.text(x + w / 2, y + h / 2, label,
                ha="center", va="center", fontsize=fontsize,
                fontweight="bold", color="black", zorder=3,
                fontfamily="sans-serif")


def draw_arrow(ax, x1, y1, x2, y2, style="->", lw=1.2,
               connectionstyle="arc3,rad=0", label=None, label_fontsize=8,
               dashed=False):
    ls = "--" if dashed else "-"
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, color="black",
                            connectionstyle=connectionstyle,
                            linewidth=lw, zorder=4, mutation_scale=12,
                            linestyle=ls)
    ax.add_patch(arrow)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.009, label, ha="center", va="center",
                fontsize=label_fontsize, color="black", fontweight="bold",
                zorder=5, fontfamily="sans-serif",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                          edgecolor="black", alpha=1.0, linewidth=0.6))


def draw_bus(ax, x1, y1, x2, y2, lw=3.0, label=None, label_fontsize=8,
             dashed=False):
    ls = "--" if dashed else "-"
    ax.plot([x1, x2], [y1, y2], color="black", linewidth=lw, zorder=3,
            solid_capstyle="round", linestyle=ls)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx + 0.003, my + 0.009, label, ha="center", va="center",
                fontsize=label_fontsize, color="black", zorder=5,
                fontweight="bold", fontfamily="sans-serif",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                          edgecolor="black", alpha=1.0, linewidth=0.7))


def draw_region(ax, x, y, w, h, label, fill="#F5F5F5", fontsize=10):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.008",
                                    facecolor=fill, edgecolor="black",
                                    alpha=0.4, linewidth=1.5,
                                    linestyle="--", zorder=1)
    ax.add_patch(rect)
    ax.text(x + 0.005, y + h - 0.008, label,
            ha="left", va="top", fontsize=fontsize,
            fontweight="bold", color="black", alpha=1.0, zorder=2,
            fontfamily="sans-serif")


def generate_block_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(36, 22), dpi=300)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    # CONFIDENTIAL banner (top)
    ax.text(0.5, 0.985, "CONFIDENTIAL \u2014 Property of LightRail AI Labs",
            ha="center", va="center", fontsize=14, fontweight="bold",
            color="black", zorder=10, fontfamily="sans-serif",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="black", alpha=1.0, linewidth=2.0))

    ax.text(0.5, 0.966, "LightRail AI LR-P3A Rev 6.3 \u2014 Motherboard System Block Diagram",
            ha="center", va="center", fontsize=20, fontweight="bold",
            color="black", fontfamily="sans-serif")
    ax.text(0.5, 0.953, "TFLN Quantum Photonic Accelerator (QPA) + Dual Neural Compute Engine (NCE)",
            ha="center", va="center", fontsize=13, fontweight="bold",
            color="#333333", fontfamily="sans-serif")
    ax.text(0.5, 0.942,
            "420 x 350 mm  |  32-Layer HDI  |  Megtron-7 / Faradflex  |  "
            "ENIG  |  9,418 Pads  |  142 Nets  |  22,493 Traces",
            ha="center", va="center", fontsize=9, color="#555555",
            fontfamily="sans-serif")

    # Region boundaries
    draw_region(ax, 0.01, 0.85, 0.98, 0.08, "HOST CPU / SERVER PLATFORM", "#EEEEEE", fontsize=10)
    draw_region(ax, 0.01, 0.38, 0.28, 0.46, "NCE-A (Neural Compute Engine A)", "#F0F0F0", fontsize=9)
    draw_region(ax, 0.30, 0.28, 0.40, 0.56, "QUANTUM PHOTONIC ACCELERATOR (QPA)", "#E8E8E8", fontsize=10)
    draw_region(ax, 0.71, 0.38, 0.28, 0.46, "NCE-B (Neural Compute Engine B)", "#F0F0F0", fontsize=9)
    draw_region(ax, 0.01, 0.14, 0.28, 0.23, "HIGH-SPEED NETWORKING & I/O", "#F5F5F5", fontsize=9)
    draw_region(ax, 0.30, 0.04, 0.40, 0.23, "POWER DELIVERY NETWORK (PDN)", "#F2F2F2", fontsize=9)
    draw_region(ax, 0.71, 0.14, 0.28, 0.23, "THERMAL / STORAGE / EXPANSION", "#F5F5F5", fontsize=9)
    draw_region(ax, 0.01, 0.04, 0.28, 0.09, "BOARD MANAGEMENT & DEBUG", "#F0F0F0", fontsize=8)
    draw_region(ax, 0.71, 0.04, 0.28, 0.09, "CLOCK DISTRIBUTION", "#F0F0F0", fontsize=8)

    # HOST CPU / SERVER PLATFORM
    draw_block(ax, 0.02, 0.86, 0.14, 0.06, "Host CPU", fontsize=12, sublabel="Xeon / EPYC\nLGA-4677 / SP5", bold_border=True)
    draw_block(ax, 0.17, 0.865, 0.08, 0.05, "DDR5", fontsize=9, sublabel="8-Ch RDIMM\n512 GB Total")
    draw_block(ax, 0.26, 0.865, 0.09, 0.05, "PCIe Gen6", fontsize=9, sublabel="Root Complex\n128 Lanes")
    draw_block(ax, 0.36, 0.865, 0.09, 0.05, "CXL 2.0", fontsize=9, sublabel="Type 3 Host\n68 Lanes")
    draw_block(ax, 0.46, 0.86, 0.12, 0.06, "Platform Controller\nHub (PCH)", fontsize=9, sublabel="USB 3.2 / SATA / LPC / SPI")
    draw_block(ax, 0.59, 0.86, 0.10, 0.06, "BMC (AST2600)", fontsize=9, sublabel="OpenBMC\nIPMI 2.0 / Redfish")
    draw_block(ax, 0.70, 0.865, 0.07, 0.05, "UEFI Flash", fontsize=8, sublabel="64 MB SPI\nSecure Boot")
    draw_block(ax, 0.78, 0.865, 0.06, 0.05, "TPM 2.0", fontsize=8, sublabel="SPI / I2C\nAttestation")
    draw_block(ax, 0.85, 0.86, 0.07, 0.06, "ATX 24-pin", fontsize=8, sublabel="Main Power\nInput", fill="#E8E8E8")
    draw_block(ax, 0.93, 0.86, 0.06, 0.06, "EPS 8-pin", fontsize=8, sublabel="CPU 12V\nx 2", fill="#E8E8E8")

    # NCE-A COMPUTE COMPLEX
    draw_block(ax, 0.03, 0.68, 0.24, 0.12, "NCE-A Die", fontsize=13, sublabel="AI Accelerator ASIC\nBGA-2500 | 250W TDP | 5nm", bold_border=True, fill="#F0F0F0")
    draw_block(ax, 0.03, 0.62, 0.055, 0.05, "HBM4-A1", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.095, 0.62, 0.055, 0.05, "HBM4-A2", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.16, 0.62, 0.055, 0.05, "HBM4-A3", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.225, 0.62, 0.055, 0.05, "HBM4-A4", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.03, 0.56, 0.12, 0.05, "SerDes 100G", fontsize=9, sublabel="PAM4 x 16 lanes")
    draw_block(ax, 0.16, 0.56, 0.12, 0.05, "PCIe Gen6 x16", fontsize=9, sublabel="To Host CPU")
    draw_block(ax, 0.03, 0.49, 0.25, 0.06, "TFLN CPO-A", fontsize=11, sublabel="Co-Packaged Optics | 1.6T Bandwidth | 16 Channels", fill="#D8D8D8", bold_border=True)
    draw_block(ax, 0.03, 0.40, 0.12, 0.07, "DrMOS VRM\nNCE-A", fontsize=9, sublabel="6-Phase ISL69260\n0.85V Core", fill="#E8E8E8")
    draw_block(ax, 0.16, 0.40, 0.12, 0.07, "Decoupling\nArray A", fontsize=9, sublabel="138 Caps\n01005 to Tantalum", fill="#E8E8E8")

    # NCE-B COMPUTE COMPLEX (mirror)
    draw_block(ax, 0.73, 0.68, 0.24, 0.12, "NCE-B Die", fontsize=13, sublabel="AI Accelerator ASIC\nBGA-2500 | 250W TDP | 5nm", bold_border=True, fill="#F0F0F0")
    draw_block(ax, 0.73, 0.62, 0.055, 0.05, "HBM4-B1", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.795, 0.62, 0.055, 0.05, "HBM4-B2", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.86, 0.62, 0.055, 0.05, "HBM4-B3", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.925, 0.62, 0.055, 0.05, "HBM4-B4", fontsize=8, sublabel="32 GB", fill="#E0E0E0")
    draw_block(ax, 0.73, 0.56, 0.12, 0.05, "SerDes 100G", fontsize=9, sublabel="PAM4 x 16 lanes")
    draw_block(ax, 0.86, 0.56, 0.12, 0.05, "PCIe Gen6 x16", fontsize=9, sublabel="To Host CPU")
    draw_block(ax, 0.73, 0.49, 0.25, 0.06, "TFLN CPO-B", fontsize=11, sublabel="Co-Packaged Optics | 1.6T Bandwidth | 16 Channels", fill="#D8D8D8", bold_border=True)
    draw_block(ax, 0.73, 0.40, 0.12, 0.07, "DrMOS VRM\nNCE-B", fontsize=9, sublabel="6-Phase ISL69260\n0.85V Core", fill="#E8E8E8")
    draw_block(ax, 0.86, 0.40, 0.12, 0.07, "Decoupling\nArray B", fontsize=9, sublabel="138 Caps\n01005 to Tantalum", fill="#E8E8E8")

    # QPA PHOTONIC ACCELERATOR (center)
    draw_block(ax, 0.38, 0.74, 0.24, 0.08, "CXL 2.0 Switch", fontsize=12, sublabel="Microchip PM40028\n68 Lanes | Type 3 Pooling", bold_border=True)
    draw_block(ax, 0.31, 0.64, 0.09, 0.08, "FPGA-1", fontsize=9, sublabel="Kintex\nUltraScale+\nTrigger Matrix")
    draw_block(ax, 0.41, 0.64, 0.09, 0.08, "DAC-1", fontsize=9, sublabel="100 GHz\nInterleaved\n14-bit")
    draw_block(ax, 0.51, 0.64, 0.09, 0.08, "DAC-2", fontsize=9, sublabel="100 GHz\nInterleaved\n14-bit")
    draw_block(ax, 0.61, 0.64, 0.08, 0.08, "FPGA-2", fontsize=9, sublabel="Kintex\nUltraScale+\nCXL Host IF")

    draw_block(ax, 0.31, 0.53, 0.38, 0.10, "RF Driver Array", fontsize=11, sublabel="8x BiCMOS SiGe RF Drivers  |  Push-Pull  |  6 Vpp Swing  |  60 GHz BW  |  CPW 50\u03A9", fill="#E8E8E8")

    draw_block(ax, 0.31, 0.38, 0.38, 0.14, "TFLN MZI Mesh", fontsize=13,
               sublabel="8x8 Clements Decomposition  |  25 MZI Nodes\n"
               "500 \u00b5m Arm Length  |  5 \u00b5m Spacing  |  800 nm WG Width\n"
               "600 nm TFLN  |  1550 nm C-band  |  EO Phase Shifters",
               fill="#D8D8D8", bold_border=True)

    draw_block(ax, 0.31, 0.30, 0.12, 0.07, "SNSPD Array 1", fontsize=9, sublabel="8-Ch NbN Detectors\n< 50 ps Jitter")
    draw_block(ax, 0.44, 0.30, 0.12, 0.07, "SNSPD Array 2", fontsize=9, sublabel="8-Ch NbN Detectors\n< 50 ps Jitter")
    draw_block(ax, 0.57, 0.30, 0.12, 0.07, "Q-Memory", fontsize=9, sublabel="Quantum Memory\nCoherence Buffer\nRare-Earth Ion")

    # HIGH-SPEED NETWORKING & I/O
    draw_block(ax, 0.02, 0.30, 0.12, 0.06, "QSFP-DD x8", fontsize=10, sublabel="400G / 800G\nOptical Cages", bold_border=True)
    draw_block(ax, 0.15, 0.30, 0.12, 0.06, "Optical TRX", fontsize=10, sublabel="DR4/FR4\nTransceivers")
    draw_block(ax, 0.02, 0.23, 0.08, 0.06, "100GbE", fontsize=8, sublabel="ASIC Switch\nMellanox")
    draw_block(ax, 0.11, 0.23, 0.08, 0.06, "InfiniBand", fontsize=8, sublabel="HDR 200G\nConnectX-7")
    draw_block(ax, 0.20, 0.23, 0.08, 0.06, "USB 3.2", fontsize=8, sublabel="Gen2 x2\nType-C x4")
    draw_block(ax, 0.02, 0.15, 0.08, 0.06, "UART", fontsize=8, sublabel="Console\n115200 bps")
    draw_block(ax, 0.11, 0.15, 0.08, 0.06, "Eth Mgmt", fontsize=8, sublabel="1G RJ45\nBMC Port")
    draw_block(ax, 0.20, 0.15, 0.08, 0.06, "GPIO / LED", fontsize=8, sublabel="Status / Fault\nIndicators")

    # POWER DELIVERY NETWORK
    draw_block(ax, 0.31, 0.20, 0.10, 0.06, "12V Main\nATX Input", fontsize=9, sublabel="24-pin + EPS\n1200W Total", fill="#E0E0E0", bold_border=True)
    draw_block(ax, 0.42, 0.20, 0.08, 0.06, "VRM NCE-A", fontsize=8, sublabel="6-Phase\n0.85V / 300A", fill="#E8E8E8")
    draw_block(ax, 0.51, 0.20, 0.08, 0.06, "VRM NCE-B", fontsize=8, sublabel="6-Phase\n0.85V / 300A", fill="#E8E8E8")
    draw_block(ax, 0.60, 0.20, 0.08, 0.06, "VRM QPA", fontsize=8, sublabel="4-Phase\n1.2V / 80A", fill="#E8E8E8")
    draw_block(ax, 0.31, 0.13, 0.08, 0.06, "VRM HBM4", fontsize=8, sublabel="1.1V\n2x 60A", fill="#E8E8E8")
    draw_block(ax, 0.40, 0.13, 0.08, 0.06, "VRM DDR5", fontsize=8, sublabel="1.1V\n4-Ch", fill="#E8E8E8")
    draw_block(ax, 0.49, 0.13, 0.08, 0.06, "VRM CPU", fontsize=8, sublabel="1.8V\n8-Phase", fill="#E8E8E8")
    draw_block(ax, 0.58, 0.13, 0.09, 0.06, "Standby +5V", fontsize=8, sublabel="Always-On\nBMC / RTC", fill="#E8E8E8")
    draw_block(ax, 0.31, 0.05, 0.36, 0.06, "PCB Power Plane Stackup", fontsize=9,
               sublabel="In3: VCC_NCE_A (0.85V)  |  In4: VCC_NCE_B (0.85V)  |  In5: VCC_QPA (1.2V)  |  In6: GND  |  In7: VCC_HBM (1.1V)  |  In8: VCC_DDR5 (1.1V)",
               fill="#F0F0F0")

    # THERMAL / STORAGE / EXPANSION
    draw_block(ax, 0.72, 0.30, 0.12, 0.06, "CVD Diamond\nSubstrate", fontsize=9, sublabel="NCE Heat Spreader\n2000 W/mK")
    draw_block(ax, 0.85, 0.30, 0.13, 0.06, "Liquid Cold\nPlate", fontsize=9, sublabel="CPU + NCE Loop\n500W Capacity")
    draw_block(ax, 0.72, 0.23, 0.08, 0.06, "Fan Hdr x6", fontsize=8, sublabel="4-pin PWM\nTach Monitor")
    draw_block(ax, 0.81, 0.23, 0.08, 0.06, "Temp\nSensors", fontsize=8, sublabel="8x NTC\nI2C / SMBus")
    draw_block(ax, 0.90, 0.23, 0.08, 0.06, "Pressure\nSensor", fontsize=8, sublabel="Coolant\nFlow Rate")
    draw_block(ax, 0.72, 0.15, 0.10, 0.06, "NVMe M.2", fontsize=9, sublabel="Gen5 x4\n2 Slots")
    draw_block(ax, 0.83, 0.15, 0.10, 0.06, "U.2 / EDSFF", fontsize=9, sublabel="Gen5 x4\n4 Bays")
    draw_block(ax, 0.94, 0.15, 0.05, 0.06, "SATA\nx4", fontsize=7, sublabel="6 Gbps")

    # BOARD MANAGEMENT & DEBUG
    draw_block(ax, 0.02, 0.045, 0.06, 0.06, "JTAG", fontsize=8, sublabel="Chain\nBoundary Scan")
    draw_block(ax, 0.09, 0.045, 0.06, 0.06, "I2C /\nSMBus", fontsize=8, sublabel="Mux\n8-Channel")
    draw_block(ax, 0.16, 0.045, 0.06, 0.06, "SPI Flash", fontsize=8, sublabel="BIOS\n+ BMC FW")
    draw_block(ax, 0.23, 0.045, 0.05, 0.06, "CPLD", fontsize=8, sublabel="Lattice\nMachXO3")

    # CLOCK DISTRIBUTION
    draw_block(ax, 0.72, 0.045, 0.08, 0.06, "Ref Clock", fontsize=8, sublabel="100 MHz\nOCXO / TCXO")
    draw_block(ax, 0.81, 0.045, 0.09, 0.06, "PLL / Jitter\nCleaner", fontsize=8, sublabel="Si5345B\n< 100 fs RMS")
    draw_block(ax, 0.91, 0.045, 0.08, 0.06, "Clock\nFanout", fontsize=8, sublabel="1:12 LVDS\nTree Buffer")

    # ===== DATA FLOW CONNECTIONS =====

    # Host CPU -> NCE-A (PCIe Gen6)
    draw_bus(ax, 0.16, 0.86, 0.16, 0.80, lw=3, label="PCIe Gen6 x16")
    draw_arrow(ax, 0.16, 0.80, 0.22, 0.80, lw=1.5)
    # Host CPU -> NCE-B (PCIe Gen6)
    draw_bus(ax, 0.30, 0.87, 0.30, 0.84, lw=3)
    draw_arrow(ax, 0.84, 0.86, 0.84, 0.80, lw=1.5)
    draw_bus(ax, 0.84, 0.86, 0.92, 0.86, lw=1)
    # Host CPU -> QPA (CXL 2.0)
    draw_bus(ax, 0.40, 0.87, 0.40, 0.82, lw=3.5, label="CXL 2.0 x68")
    draw_arrow(ax, 0.50, 0.87, 0.50, 0.82, lw=2)
    # Host CPU <-> DDR5
    draw_bus(ax, 0.16, 0.89, 0.17, 0.89, lw=4, label="DDR5-6400")
    # Host CPU -> PCH
    draw_bus(ax, 0.35, 0.89, 0.46, 0.89, lw=2, label="DMI 4.0")
    # PCH -> BMC
    draw_bus(ax, 0.58, 0.89, 0.59, 0.89, lw=1.5, label="LPC/eSPI")
    # NCE-A CPO <-> QPA (optical)
    draw_bus(ax, 0.28, 0.52, 0.31, 0.52, lw=4, label="1.6T Optical")
    draw_bus(ax, 0.28, 0.50, 0.31, 0.50, lw=4)
    # NCE-B CPO <-> QPA (optical)
    draw_bus(ax, 0.69, 0.52, 0.73, 0.52, lw=4, label="1.6T Optical")
    draw_bus(ax, 0.69, 0.50, 0.73, 0.50, lw=4)
    # QPA internal dataflow
    draw_arrow(ax, 0.50, 0.74, 0.50, 0.72, lw=2, label="CXL Fabric")
    draw_arrow(ax, 0.36, 0.64, 0.36, 0.63, lw=1.5)
    draw_arrow(ax, 0.46, 0.64, 0.46, 0.63, lw=1.5)
    draw_arrow(ax, 0.56, 0.64, 0.56, 0.63, lw=1.5)
    draw_arrow(ax, 0.50, 0.53, 0.50, 0.52, lw=2, label="RF Drive")
    draw_arrow(ax, 0.50, 0.38, 0.50, 0.37, lw=2, label="Photon Detect")
    # NCE-A -> HBM4 stacks
    draw_bus(ax, 0.06, 0.68, 0.06, 0.67, lw=3, label="HBM4 IF")
    draw_bus(ax, 0.12, 0.68, 0.12, 0.67, lw=3)
    draw_bus(ax, 0.19, 0.68, 0.19, 0.67, lw=3)
    draw_bus(ax, 0.25, 0.68, 0.25, 0.67, lw=3)
    # NCE-B -> HBM4 stacks
    draw_bus(ax, 0.76, 0.68, 0.76, 0.67, lw=3, label="HBM4 IF")
    draw_bus(ax, 0.82, 0.68, 0.82, 0.67, lw=3)
    draw_bus(ax, 0.89, 0.68, 0.89, 0.67, lw=3)
    draw_bus(ax, 0.95, 0.68, 0.95, 0.67, lw=3)
    # NCE-A SerDes -> QSFP-DD
    draw_arrow(ax, 0.09, 0.56, 0.09, 0.36, lw=1.5, label="100G SerDes")
    # NCE-B SerDes -> QSFP-DD
    draw_arrow(ax, 0.79, 0.56, 0.79, 0.36, lw=1.5, label="100G SerDes")
    # Power delivery arrows
    draw_arrow(ax, 0.36, 0.26, 0.36, 0.27, lw=1.5, label="12V Rail")
    draw_arrow(ax, 0.46, 0.26, 0.15, 0.40, lw=1.0, label="0.85V NCE-A", dashed=True)
    draw_arrow(ax, 0.55, 0.26, 0.85, 0.40, lw=1.0, label="0.85V NCE-B", dashed=True)
    draw_arrow(ax, 0.64, 0.26, 0.64, 0.30, lw=1.0, label="1.2V QPA", dashed=True)
    # Clock distribution
    draw_arrow(ax, 0.80, 0.075, 0.81, 0.075, lw=1.5)
    draw_arrow(ax, 0.90, 0.075, 0.91, 0.075, lw=1.5)
    draw_arrow(ax, 0.95, 0.105, 0.95, 0.15, lw=1.0, label="Clocks")
    # Board mgmt -> all subsystems
    draw_bus(ax, 0.15, 0.11, 0.85, 0.11, lw=1.5, label="I2C / SMBus Management Bus", dashed=True)

    # ===== IMPEDANCE CALLOUTS =====
    impedance_text = (
        "Impedance Targets:\n"
        "PCIe Gen6: 85\u03A9 diff  |  CXL 2.0: 85\u03A9 diff  |  "
        "SerDes: 100\u03A9 diff  |  DDR5: 40\u03A9 SE\n"
        "RF CPW: 50\u03A9 SE  |  LVDS Clk: 100\u03A9 diff  |  "
        "USB 3.2: 90\u03A9 diff  |  HBM4 PHY: 40\u03A9 SE"
    )
    ax.text(0.5, 0.005, impedance_text,
            ha="center", va="bottom", fontsize=8, color="black",
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="black", alpha=1.0, linewidth=1.0))

    # ===== LEGEND =====
    legend_items = [
        ("white", "Host CPU / Server", 2.0),
        ("#F0F0F0", "NCE Die (AI ASIC)", 1.5),
        ("#E0E0E0", "HBM4 Memory", 1.5),
        ("#D8D8D8", "TFLN Photonic", 1.5),
        ("white", "CXL 2.0 Fabric", 2.0),
        ("white", "PCIe / FPGA", 1.5),
        ("white", "DAC / RF Analog", 1.5),
        ("white", "SNSPD / Q-Memory", 1.5),
        ("white", "SerDes / High-Speed I/O", 1.5),
        ("#E8E8E8", "Power Delivery", 1.5),
        ("white", "Thermal Management", 1.5),
        ("white", "Clock Distribution", 1.5),
    ]
    lx = 0.01
    ly = 0.002
    for i, (fill, name, lw) in enumerate(legend_items):
        xi = lx + i * 0.082
        ax.add_patch(mpatches.Rectangle((xi, ly), 0.012, 0.012,
                                         facecolor=fill, edgecolor="black",
                                         linewidth=lw, zorder=5))
        ax.text(xi + 0.016, ly + 0.006, name, fontsize=7, va="center",
                color="black", fontweight="bold", zorder=5,
                fontfamily="sans-serif")

    # CONFIDENTIAL banner (bottom)
    fig.text(0.5, 0.008, "CONFIDENTIAL \u2014 Property of LightRail AI Labs  |  "
             "LR-P3A Rev 6.3  |  Do Not Distribute",
             ha="center", va="bottom", fontsize=11, fontweight="bold",
             color="black", fontfamily="sans-serif",
             bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                       edgecolor="black", alpha=1.0, linewidth=2.0))

    # Pure white background
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Save outputs
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(out_dir, "LR_P3A_QPA_Block_Diagram.png")
    pdf_path = os.path.join(out_dir, "LR_P3A_QPA_Block_Diagram.pdf")

    plt.tight_layout(pad=1.5)
    fig.savefig(png_path, dpi=300, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    fig.savefig(pdf_path, format="pdf", bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print(f"Generated: {png_path}")
    print(f"Generated: {pdf_path}")


if __name__ == "__main__":
    generate_block_diagram()


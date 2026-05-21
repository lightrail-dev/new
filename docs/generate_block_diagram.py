#!/usr/bin/env python3
"""
Block Diagram Generator — LightRail AI LR-P3A Rev 6.3
TFLN Quantum Photonic Accelerator (QPA) + Neural Compute Engine (NCE)

Generates a comprehensive system block diagram showing all major
subsystems, data flows, and interfaces.

Output: docs/LR_P3A_QPA_Block_Diagram.png
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np


def draw_block(ax, x, y, w, h, label, color='#2196F3', text_color='white',
               fontsize=7, alpha=0.9, sublabel=None, style='round',
               linewidth=1.0, edgecolor=None):
    """Draw a rounded rectangle block with label."""
    if edgecolor is None:
        edgecolor = color
    if style == 'round':
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                             facecolor=color, edgecolor=edgecolor,
                             alpha=alpha, linewidth=linewidth,
                             zorder=2)
    else:
        box = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0.01",
                             facecolor=color, edgecolor=edgecolor,
                             alpha=alpha, linewidth=linewidth,
                             zorder=2)
    ax.add_patch(box)
    if sublabel:
        ax.text(x + w/2, y + h/2 + 0.008, label,
                ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color=text_color, zorder=3)
        ax.text(x + w/2, y + h/2 - 0.012, sublabel,
                ha='center', va='center', fontsize=fontsize - 1.5,
                color=text_color, alpha=0.85, zorder=3)
    else:
        ax.text(x + w/2, y + h/2, label,
                ha='center', va='center', fontsize=fontsize,
                fontweight='bold', color=text_color, zorder=3)


def draw_arrow(ax, x1, y1, x2, y2, color='#333333', style='->', lw=1.0,
               connectionstyle='arc3,rad=0', label=None, label_fontsize=5):
    """Draw an arrow between two points."""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                            arrowstyle=style, color=color,
                            connectionstyle=connectionstyle,
                            linewidth=lw, zorder=4,
                            mutation_scale=8)
    ax.add_patch(arrow)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.008, label, ha='center', va='center',
                fontsize=label_fontsize, color=color, zorder=5,
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor='none', alpha=0.8))


def draw_bus(ax, x1, y1, x2, y2, color='#FF5722', lw=2.5, label=None,
             label_fontsize=5):
    """Draw a thick bus line."""
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=lw, zorder=3,
            solid_capstyle='round')
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.008, label, ha='center', va='center',
                fontsize=label_fontsize, color=color, zorder=5,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor=color, alpha=0.9, linewidth=0.5))


def draw_region(ax, x, y, w, h, label, color='#E3F2FD', edgecolor='#1565C0',
                fontsize=8, alpha=0.3):
    """Draw a dashed region boundary."""
    rect = mpatches.FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.01",
                                    facecolor=color, edgecolor=edgecolor,
                                    alpha=alpha, linewidth=1.5,
                                    linestyle='--', zorder=1)
    ax.add_patch(rect)
    ax.text(x + 0.005, y + h - 0.012, label,
            ha='left', va='top', fontsize=fontsize,
            fontweight='bold', color=edgecolor, alpha=0.8, zorder=2)


def generate_block_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(24, 16), dpi=200)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')

    # Title
    ax.text(0.5, 0.975, 'LightRail AI LR-P3A Rev 6.3 — System Block Diagram',
            ha='center', va='center', fontsize=14, fontweight='bold',
            color='#0D47A1')
    ax.text(0.5, 0.958, 'TFLN Quantum Photonic Accelerator (QPA) + Dual Neural Compute Engine (NCE)',
            ha='center', va='center', fontsize=9, color='#424242')
    ax.text(0.5, 0.944, '420 × 350 mm | 32-Layer HDI | Megtron-7/Faradflex | ENIG | OCP Server-Class',
            ha='center', va='center', fontsize=7, color='#757575')

    # =====================================================================
    # Region boundaries
    # =====================================================================

    # Host / Server interface (top)
    draw_region(ax, 0.02, 0.875, 0.96, 0.055,
                'HOST / SERVER INTERFACE', '#FFF3E0', '#E65100', fontsize=7)

    # NCE A region (left)
    draw_region(ax, 0.02, 0.42, 0.30, 0.44,
                'NCE-A (Neural Compute Engine A)', '#E3F2FD', '#1565C0')

    # NCE B region (right)
    draw_region(ax, 0.68, 0.42, 0.30, 0.44,
                'NCE-B (Neural Compute Engine B)', '#E3F2FD', '#1565C0')

    # QPA region (center)
    draw_region(ax, 0.33, 0.30, 0.34, 0.58,
                'QUANTUM PHOTONIC ACCELERATOR (QPA)', '#F3E5F5', '#6A1B9A')

    # Power / VRM region (bottom)
    draw_region(ax, 0.02, 0.05, 0.96, 0.24,
                'POWER DELIVERY NETWORK (PDN)', '#E8F5E9', '#2E7D32', fontsize=7)

    # I/O region (bottom-left)
    draw_region(ax, 0.02, 0.30, 0.30, 0.11,
                'HIGH-SPEED I/O', '#FFF8E1', '#F57F17', fontsize=7)

    # Thermal region (bottom-right)
    draw_region(ax, 0.68, 0.30, 0.30, 0.11,
                'THERMAL MANAGEMENT', '#FFEBEE', '#B71C1C', fontsize=7)

    # =====================================================================
    # Host Interface blocks (top row)
    # =====================================================================

    draw_block(ax, 0.04, 0.885, 0.12, 0.035,
               'PCIe Gen 6 x16', '#E65100', sublabel='CEM Connector',
               fontsize=6)
    draw_block(ax, 0.18, 0.885, 0.12, 0.035,
               'PCIe Gen 6 x16', '#E65100', sublabel='CEM Connector',
               fontsize=6)
    draw_block(ax, 0.35, 0.885, 0.10, 0.035,
               'CXL 2.0', '#AD1457', sublabel='68-Lane Switch',
               fontsize=6)
    draw_block(ax, 0.48, 0.885, 0.12, 0.035,
               'BMC / IPMI', '#37474F', sublabel='OpenBMC Telemetry',
               fontsize=6)
    draw_block(ax, 0.63, 0.885, 0.10, 0.035,
               'JTAG/SWD', '#37474F', sublabel='Debug Interface',
               fontsize=6)
    draw_block(ax, 0.76, 0.885, 0.10, 0.035,
               'I2C / SMBus', '#37474F', sublabel='Management Bus',
               fontsize=6)
    draw_block(ax, 0.88, 0.885, 0.08, 0.035,
               'SPI Flash', '#37474F', sublabel='Config ROM',
               fontsize=6)

    # =====================================================================
    # NCE-A blocks (left column)
    # =====================================================================

    # NCE-A die
    draw_block(ax, 0.05, 0.72, 0.24, 0.10,
               'NCE-A Die', '#0D47A1',
               sublabel='AI Accelerator ASIC\nBGA-2500 | 250W TDP',
               fontsize=8)

    # HBM4 stacks around NCE-A
    draw_block(ax, 0.05, 0.66, 0.055, 0.045,
               'HBM4-A1', '#1B5E20', sublabel='32 GB', fontsize=5)
    draw_block(ax, 0.115, 0.66, 0.055, 0.045,
               'HBM4-A2', '#1B5E20', sublabel='32 GB', fontsize=5)
    draw_block(ax, 0.18, 0.66, 0.055, 0.045,
               'HBM4-A3', '#1B5E20', sublabel='32 GB', fontsize=5)
    draw_block(ax, 0.245, 0.66, 0.055, 0.045,
               'HBM4-A4', '#1B5E20', sublabel='32 GB', fontsize=5)

    # NCE-A SerDes
    draw_block(ax, 0.05, 0.60, 0.11, 0.045,
               'SerDes 100G', '#006064', sublabel='PAM4 × 16 lanes',
               fontsize=5.5)
    draw_block(ax, 0.17, 0.60, 0.11, 0.045,
               'PCIe Gen6', '#006064', sublabel='x16 Interface',
               fontsize=5.5)

    # TFLN CPO A
    draw_block(ax, 0.05, 0.53, 0.24, 0.055,
               'TFLN CPO-A', '#4A148C',
               sublabel='Co-Packaged Optics | 1.6T Bandwidth',
               fontsize=7, alpha=0.95)

    # NCE-A local VRM
    draw_block(ax, 0.05, 0.44, 0.11, 0.07,
               'DrMOS VRM\nNCE-A', '#2E7D32',
               sublabel='6-Phase | ISL69260',
               fontsize=5.5)
    draw_block(ax, 0.17, 0.44, 0.11, 0.07,
               'Decoupling\nArray A', '#4CAF50',
               sublabel='138 caps\n01005→Tantalum',
               fontsize=5.5)

    # =====================================================================
    # NCE-B blocks (right column) — mirror of NCE-A
    # =====================================================================

    draw_block(ax, 0.71, 0.72, 0.24, 0.10,
               'NCE-B Die', '#0D47A1',
               sublabel='AI Accelerator ASIC\nBGA-2500 | 250W TDP',
               fontsize=8)

    draw_block(ax, 0.71, 0.66, 0.055, 0.045,
               'HBM4-B1', '#1B5E20', sublabel='32 GB', fontsize=5)
    draw_block(ax, 0.775, 0.66, 0.055, 0.045,
               'HBM4-B2', '#1B5E20', sublabel='32 GB', fontsize=5)
    draw_block(ax, 0.84, 0.66, 0.055, 0.045,
               'HBM4-B3', '#1B5E20', sublabel='32 GB', fontsize=5)
    draw_block(ax, 0.905, 0.66, 0.055, 0.045,
               'HBM4-B4', '#1B5E20', sublabel='32 GB', fontsize=5)

    draw_block(ax, 0.71, 0.60, 0.11, 0.045,
               'SerDes 100G', '#006064', sublabel='PAM4 × 16 lanes',
               fontsize=5.5)
    draw_block(ax, 0.83, 0.60, 0.11, 0.045,
               'PCIe Gen6', '#006064', sublabel='x16 Interface',
               fontsize=5.5)

    draw_block(ax, 0.71, 0.53, 0.24, 0.055,
               'TFLN CPO-B', '#4A148C',
               sublabel='Co-Packaged Optics | 1.6T Bandwidth',
               fontsize=7, alpha=0.95)

    draw_block(ax, 0.71, 0.44, 0.11, 0.07,
               'DrMOS VRM\nNCE-B', '#2E7D32',
               sublabel='6-Phase | ISL69260',
               fontsize=5.5)
    draw_block(ax, 0.83, 0.44, 0.11, 0.07,
               'Decoupling\nArray B', '#4CAF50',
               sublabel='138 caps\n01005→Tantalum',
               fontsize=5.5)

    # =====================================================================
    # QPA blocks (center column)
    # =====================================================================

    # CXL Switch
    draw_block(ax, 0.40, 0.81, 0.20, 0.05,
               'CXL 2.0 Switch (U450)', '#AD1457',
               sublabel='BGA-256 | 68-Lane Crossbar | Cache Coherent',
               fontsize=6.5)

    # FPGA Trigger Matrix A
    draw_block(ax, 0.34, 0.72, 0.13, 0.07,
               'FPGA-A (U401)', '#BF360C',
               sublabel='Kintex UltraScale+\nBGA-676 | Trigger Matrix',
               fontsize=6)

    # FPGA Trigger Matrix B
    draw_block(ax, 0.53, 0.72, 0.13, 0.07,
               'FPGA-B (U402)', '#BF360C',
               sublabel='Kintex UltraScale+\nBGA-676 | Trigger Matrix',
               fontsize=6)

    # DAC A
    draw_block(ax, 0.34, 0.64, 0.13, 0.06,
               'DAC-A (U411)', '#FF6F00',
               sublabel='100 GHz Interleaved\nQFN-64 | 16-bit',
               fontsize=5.5)

    # DAC B
    draw_block(ax, 0.53, 0.64, 0.13, 0.06,
               'DAC-B (U412)', '#FF6F00',
               sublabel='100 GHz Interleaved\nQFN-64 | 16-bit',
               fontsize=5.5)

    # RF Drivers (8x)
    draw_block(ax, 0.34, 0.57, 0.13, 0.055,
               'RF Drivers A', '#E65100',
               sublabel='U421-U424 | BiCMOS\nQFN-32 × 4',
               fontsize=5.5)
    draw_block(ax, 0.53, 0.57, 0.13, 0.055,
               'RF Drivers B', '#E65100',
               sublabel='U425-U428 | BiCMOS\nQFN-32 × 4',
               fontsize=5.5)

    # TFLN MZI Mesh (central photonic processor)
    draw_block(ax, 0.37, 0.46, 0.26, 0.09,
               'TFLN MZI Mesh', '#6A1B9A',
               sublabel='8×8 Clements Decomposition | 25 MZI Nodes\n'
                        'V_pi = 3.5V | < 0.1 dB/cm loss | 1550 nm C-band\n'
                        'Pure Light Compute — Matrix-Vector Multiply @ Speed of Light',
               fontsize=7, alpha=0.95)

    # SNSPD arrays
    draw_block(ax, 0.34, 0.38, 0.13, 0.06,
               'SNSPD-A (U431)', '#1A237E',
               sublabel='8-Ch Photodetector\nLGA-16 | < 4K Cryo',
               fontsize=5.5)
    draw_block(ax, 0.53, 0.38, 0.13, 0.06,
               'SNSPD-B (U432)', '#1A237E',
               sublabel='8-Ch Photodetector\nLGA-16 | < 4K Cryo',
               fontsize=5.5)

    # Quantum Memory
    draw_block(ax, 0.34, 0.315, 0.13, 0.05,
               'Q-Memory A (U441)', '#0D47A1',
               sublabel='TFLN Cavity | LGA-24',
               fontsize=5.5)
    draw_block(ax, 0.53, 0.315, 0.13, 0.05,
               'Q-Memory B (U442)', '#0D47A1',
               sublabel='TFLN Cavity | LGA-24',
               fontsize=5.5)

    # =====================================================================
    # High-Speed I/O blocks (bottom-left)
    # =====================================================================

    draw_block(ax, 0.04, 0.32, 0.12, 0.07,
               'QSFP-DD × 8', '#F57F17',
               sublabel='64 ports | 100G/lane\n12.8 Tbps aggregate',
               fontsize=5.5, text_color='black')
    draw_block(ax, 0.17, 0.32, 0.12, 0.07,
               'Optical\nTransceivers', '#FBC02D',
               sublabel='1550 nm SMF\nC-band DWDM',
               fontsize=5.5, text_color='black')

    # =====================================================================
    # Thermal Management (bottom-right)
    # =====================================================================

    draw_block(ax, 0.70, 0.32, 0.13, 0.07,
               'CVD Diamond\nSubstrate', '#B71C1C',
               sublabel='2,000 W/mK\nDirect-to-Chip',
               fontsize=5.5)
    draw_block(ax, 0.84, 0.32, 0.13, 0.07,
               'Liquid Cold\nPlate', '#D32F2F',
               sublabel='4× M3 Bolsters/NCE\nDirect Contact',
               fontsize=5.5)

    # =====================================================================
    # Power Delivery blocks (bottom)
    # =====================================================================

    draw_block(ax, 0.04, 0.14, 0.12, 0.08,
               '12V Input', '#1B5E20',
               sublabel='Server PSU\nOCP 3.0',
               fontsize=6)

    draw_block(ax, 0.18, 0.14, 0.12, 0.08,
               'VRM NCE-A', '#2E7D32',
               sublabel='0.85V Core\n6-Phase DrMOS\nISL69260 × 3',
               fontsize=5.5)

    draw_block(ax, 0.32, 0.14, 0.12, 0.08,
               'VRM NCE-B', '#2E7D32',
               sublabel='0.85V Core\n6-Phase DrMOS\nISL69260 × 3',
               fontsize=5.5)

    draw_block(ax, 0.46, 0.14, 0.12, 0.08,
               'VRM QPA', '#2E7D32',
               sublabel='0.85V / 1.8V / 3.3V\nFPGA + DAC + RF',
               fontsize=5.5)

    draw_block(ax, 0.60, 0.14, 0.12, 0.08,
               'VRM HBM4', '#388E3C',
               sublabel='1.1V VDDQ\n8 Stacks',
               fontsize=5.5)

    draw_block(ax, 0.74, 0.14, 0.10, 0.08,
               'Clock Tree', '#004D40',
               sublabel='250 MHz Ref\nLVDS Fanout',
               fontsize=5.5)

    draw_block(ax, 0.86, 0.14, 0.10, 0.08,
               'PDN Filter', '#00695C',
               sublabel='EMI Filter\nCommon Mode',
               fontsize=5.5)

    # Stackup info
    draw_block(ax, 0.04, 0.06, 0.92, 0.06,
               '32-Layer HDI PCB Stackup: F.Cu | In1–In30 | B.Cu  ·  '
               'Megtron-7 Signal / FR-4 HiTg Planes / Faradflex Embedded Cap  ·  '
               'PCIe Gen6: 85Ω diff | SerDes: 100Ω diff | RF CPW: 50Ω SE | '
               'CXL: 85Ω diff | LVDS: 100Ω diff',
               '#37474F', fontsize=5.5, alpha=0.85)

    # =====================================================================
    # Connections / Data Flow Arrows
    # =====================================================================

    # Host → CXL Switch
    draw_arrow(ax, 0.40, 0.885, 0.40, 0.86, '#AD1457', lw=1.5,
               label='CXL 2.0')
    draw_arrow(ax, 0.60, 0.885, 0.60, 0.86, '#AD1457', lw=1.0)

    # CXL Switch → FPGAs
    draw_arrow(ax, 0.43, 0.81, 0.405, 0.79, '#AD1457', lw=1.5,
               label='CXL')
    draw_arrow(ax, 0.57, 0.81, 0.595, 0.79, '#AD1457', lw=1.5)

    # CXL Switch → NCE-A / NCE-B
    draw_arrow(ax, 0.40, 0.835, 0.29, 0.80, '#AD1457', lw=1.2,
               connectionstyle='arc3,rad=0.15', label='CXL 2.0')
    draw_arrow(ax, 0.60, 0.835, 0.71, 0.80, '#AD1457', lw=1.2,
               connectionstyle='arc3,rad=-0.15', label='CXL 2.0')

    # PCIe → NCE-A / NCE-B
    draw_arrow(ax, 0.10, 0.885, 0.17, 0.82, '#E65100', lw=1.2,
               connectionstyle='arc3,rad=0.1', label='PCIe Gen6')
    draw_arrow(ax, 0.24, 0.885, 0.83, 0.82, '#E65100', lw=1.2,
               connectionstyle='arc3,rad=-0.2', label='PCIe Gen6')

    # FPGA → DAC (LVDS trigger)
    draw_bus(ax, 0.405, 0.72, 0.405, 0.70, '#FF5722', lw=2.0,
             label='LVDS')
    draw_bus(ax, 0.595, 0.72, 0.595, 0.70, '#FF5722', lw=2.0,
             label='LVDS')

    # DAC → RF Drivers (100 GHz analog)
    draw_bus(ax, 0.405, 0.64, 0.405, 0.625, '#FF6F00', lw=2.0,
             label='100 GHz')
    draw_bus(ax, 0.595, 0.64, 0.595, 0.625, '#FF6F00', lw=2.0)

    # RF Drivers → MZI Mesh (RF to photonic)
    draw_bus(ax, 0.405, 0.57, 0.405, 0.55, '#E65100', lw=2.5,
             label='RF Drive')
    draw_bus(ax, 0.595, 0.57, 0.595, 0.55, '#E65100', lw=2.5)

    # MZI Mesh → SNSPD (optical output)
    draw_bus(ax, 0.405, 0.46, 0.405, 0.44, '#7B1FA2', lw=2.5,
             label='Photons')
    draw_bus(ax, 0.595, 0.46, 0.595, 0.44, '#7B1FA2', lw=2.5)

    # SNSPD → Q-Memory
    draw_arrow(ax, 0.405, 0.38, 0.405, 0.365, '#1A237E', lw=1.0,
               label='Readout')
    draw_arrow(ax, 0.595, 0.38, 0.595, 0.365, '#1A237E', lw=1.0)

    # NCE-A ↔ TFLN CPO-A
    draw_bus(ax, 0.17, 0.72, 0.17, 0.585, '#4A148C', lw=2.0,
             label='1.6T Optical')

    # NCE-B ↔ TFLN CPO-B
    draw_bus(ax, 0.83, 0.72, 0.83, 0.585, '#4A148C', lw=2.0,
             label='1.6T Optical')

    # TFLN CPO-A ↔ MZI Mesh (photonic bridge)
    draw_bus(ax, 0.29, 0.555, 0.37, 0.51, '#9C27B0', lw=2.0,
             label='Photonic Bridge')

    # TFLN CPO-B ↔ MZI Mesh
    draw_bus(ax, 0.71, 0.555, 0.63, 0.51, '#9C27B0', lw=2.0,
             label='Photonic Bridge')

    # NCE → SerDes
    draw_arrow(ax, 0.10, 0.72, 0.10, 0.645, '#006064', lw=1.0)
    draw_arrow(ax, 0.22, 0.72, 0.22, 0.645, '#006064', lw=1.0)
    draw_arrow(ax, 0.76, 0.72, 0.76, 0.645, '#006064', lw=1.0)
    draw_arrow(ax, 0.88, 0.72, 0.88, 0.645, '#006064', lw=1.0)

    # SerDes → QSFP-DD
    draw_arrow(ax, 0.10, 0.60, 0.10, 0.39, '#F57F17', lw=1.2,
               connectionstyle='arc3,rad=0', label='100G PAM4')

    # QSFP → Optical
    draw_arrow(ax, 0.16, 0.355, 0.17, 0.355, '#F57F17', lw=1.0)

    # 12V → VRMs
    draw_bus(ax, 0.16, 0.18, 0.18, 0.18, '#1B5E20', lw=3.0)
    draw_bus(ax, 0.30, 0.18, 0.32, 0.18, '#1B5E20', lw=3.0)
    draw_bus(ax, 0.44, 0.18, 0.46, 0.18, '#1B5E20', lw=3.0)
    draw_bus(ax, 0.58, 0.18, 0.60, 0.18, '#1B5E20', lw=3.0)

    # VRM → NCE (power)
    draw_arrow(ax, 0.24, 0.22, 0.17, 0.44, '#2E7D32', lw=1.0,
               connectionstyle='arc3,rad=0.1', label='0.85V')
    draw_arrow(ax, 0.38, 0.22, 0.83, 0.44, '#2E7D32', lw=1.0,
               connectionstyle='arc3,rad=-0.2', label='0.85V')

    # BMC telemetry arrows
    draw_arrow(ax, 0.54, 0.885, 0.50, 0.86, '#37474F', lw=0.8,
               connectionstyle='arc3,rad=0', label='OpenBMC')

    # =====================================================================
    # Legend
    # =====================================================================

    legend_x = 0.02
    legend_y = 0.005
    legend_items = [
        ('#0D47A1', 'NCE ASIC'),
        ('#1B5E20', 'HBM4 Memory'),
        ('#6A1B9A', 'TFLN Photonic'),
        ('#BF360C', 'FPGA'),
        ('#FF6F00', 'DAC / RF'),
        ('#1A237E', 'SNSPD Detector'),
        ('#AD1457', 'CXL 2.0'),
        ('#2E7D32', 'Power / VRM'),
        ('#F57F17', 'High-Speed I/O'),
        ('#B71C1C', 'Thermal'),
    ]
    for i, (color, label) in enumerate(legend_items):
        lx = legend_x + i * 0.098
        ax.add_patch(mpatches.Rectangle((lx, legend_y), 0.012, 0.012,
                                         facecolor=color, edgecolor='none',
                                         zorder=10))
        ax.text(lx + 0.015, legend_y + 0.006, label,
                ha='left', va='center', fontsize=5, color='#333333',
                zorder=10)

    # =====================================================================
    # Data flow legend (right side)
    # =====================================================================

    ax.text(0.92, 0.005, '→ Signal  ═ Bus', fontsize=5, color='#666666',
            ha='center')

    # Save
    output_path = 'docs/LR_P3A_QPA_Block_Diagram.png'
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"Block diagram saved to: {output_path}")
    return output_path


if __name__ == '__main__':
    generate_block_diagram()

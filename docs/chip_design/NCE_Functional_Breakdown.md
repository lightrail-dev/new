# NCE (Neural Compute Engine) — Functional Breakdown

**Document:** LR-NCE-FUNC-001  
**Revision:** 1.0  
**Date:** 2026-05-26  
**Process Node:** SMIC 28nm HPC+ / 40nm LL (MPW shuttle candidates)  
**Company:** LightRail AI  

---

## 1. Executive Summary

The Neural Compute Engine (NCE) is a proprietary AI SoC at the heart of the
LightRail LR-P3A photonic AI compute node. Each LR-P3A board hosts two NCE
dice, each co-packaged with four HBM4 12-Hi stacks on a silicon interposer
(BGA-2500 composite module). The NCE provides 128-way SIMD streaming compute,
direct-drive TFLN photonic I/O at 1.6 Tbps aggregate bandwidth, PCIe Gen 6
host connectivity, and CXL 2.0 memory-mapped control of the Quantum Photonic
Accelerator (QPA) subsystem.

---

## 2. Top-Level Component Hierarchy

```
NCE SoC Die (40 x 40 mm BGA-2500 composite)
|
+-- Compute Cluster
|   +-- 128-way SIMD Core Array (bfloat16/24)
|   +-- 16x Matrix Registers (256-bit)
|   +-- 16x Vector Registers (256-bit)
|   +-- Instruction Fetch/Decode/Issue Pipeline
|   +-- Shared L2 Cache (16 MB, 8-way)
|   +-- DMA Engine (4-channel)
|
+-- Memory Subsystem
|   +-- HBM4 PHY Controller (4-stack, 1024 lanes/stack)
|   +-- HBM4 Side-Channel Controller (REFCK, JTAG, PWR_GOOD)
|   +-- L3 Cache / Last-Level Cache (64 MB, 16-way)
|   +-- Memory Scheduler & Arbiter
|
+-- Photonic I/O Subsystem
|   +-- TFLN SerDes TX (8 channels x 200G PAM4)
|   +-- TFLN SerDes RX (8 channels x 200G PAM4)
|   +-- RF Drive Interface (differential, 100 Ohm)
|   +-- Clock Data Recovery (CDR) per lane
|   +-- PAM4 DSP (TX equalization, RX adaptation)
|
+-- QPA Control Subsystem (CXL 2.0 Mapped)
|   +-- Trigger Matrix Controller
|   +-- DAC Phase Bus Interface (8-ch, 16-bit)
|   +-- SNSPD Fault Monitor
|   +-- MZI Mesh Compiler Accelerator
|   +-- Telemetry Register File
|
+-- Host Interface
|   +-- PCIe Gen 6.0 Root Complex (x32, split x16+x16)
|   +-- CXL 2.0 Controller (Type 2 device)
|   +-- JTAG/IEEE 1500 Debug Port
|   +-- PMBus / I2C Management Interface
|
+-- Power Management
|   +-- DVFS Controller (Voltage/Frequency Scaling)
|   +-- Power Gate Array (per-cluster shutdown)
|   +-- Thermal Diode Interface (4x on-die sensors)
|   +-- VRM Telemetry (PMBus)
|
+-- Clock & Reset
|   +-- PLL Array (4x): 250 MHz sys, 500 MHz DDR, GHz compute, SerDes ref
|   +-- Clock Distribution Tree (H-tree, low-skew)
|   +-- Reset Sequencer (power-on, warm, watchdog)
```

---

## 3. Detailed Block Descriptions

### 3.1 Compute Cluster

| Parameter | Value |
|-----------|-------|
| Architecture | 128-way SIMD load/store streaming |
| Data types | bfloat16, bfloat24, INT8, FP32 (accumulate) |
| Register file | 16 matrix (256-bit) + 16 vector (256-bit) |
| L1 I-Cache | 64 KB per cluster, 4-way |
| L1 D-Cache | 128 KB per cluster, 8-way |
| L2 Cache | 16 MB shared, 8-way, inclusive |
| Peak throughput | 128 bfloat16 MACs/cycle @ 1.5 GHz = 384 TOPS (BF16) |
| Pipeline | 12-stage in-order for SIMD, 6-stage for scalar |
| DMA | 4-channel, scatter-gather, HBM4-to-L2 direct path |

The compute cluster is the primary tensor processing engine. It executes
matrix-multiply-accumulate (MMA) operations on streaming data from HBM4,
with results optionally routed directly to the TFLN photonic I/O for
distributed all-reduce operations.

### 3.2 Memory Subsystem

| Parameter | Value |
|-----------|-------|
| HBM4 stacks | 4 per NCE module |
| Bandwidth per stack | 1.0 TB/s (1024 lanes x 8 Gbps/pin) |
| Aggregate BW | 4.0 TB/s per NCE module |
| PHY lanes | 4096 total (interposer-internal) |
| Side-channel (PCB) | REFCK_P/N, CATTRIP, PWR_GOOD, IEEE 1500 |
| L3 / LLC | 64 MB, 16-way, exclusive of L2 |
| ECC | SECDED on all data paths |
| Capacity | 4 x 48 GB = 192 GB per NCE module |

The HBM4 data bus (1024 lanes per stack) is routed entirely within the
vendor-supplied silicon interposer. The NCE die communicates with HBM4
through micro-bump connections on the interposer. Only side-channel
signals and power rails escape to the PCB.

### 3.3 Photonic I/O Subsystem

| Parameter | Value |
|-----------|-------|
| Channels | 8 TX + 8 RX per NCE |
| Line rate | 200 Gbps PAM4 per lane |
| Aggregate BW | 1.6 Tbps (half-duplex), 3.2 Tbps full-duplex |
| Modulation | PAM4 (4-level pulse amplitude) |
| SerDes type | Direct-drive TFLN (zero-copper datapath) |
| Drive voltage | +/- 1.5 V differential, 50 Ohm terminated |
| Wavelength | 1550 nm C-band DWDM, 100 GHz spacing |
| CDR | Per-lane, 0.1 UI jitter tolerance |
| Equalization | TX: 3-tap FFE; RX: CTLE + 7-tap DFE |
| Interconnect energy | 5-10 pJ/bit (vs 15-20 pJ/bit pluggable) |

### 3.4 QPA Control Subsystem

| Parameter | Value |
|-----------|-------|
| Interface | CXL 2.0 memory-mapped registers |
| Trigger matrix | 8-channel, 16-bit phase resolution |
| DAC interface | 100 GHz interleaved, zero-skew sync |
| SNSPD monitor | 8-channel optical power feedback |
| Telemetry | 32-bit status (fault_count + trigger_count) |
| Fault response | Automatic waveguide rerouting via FPGA |
| Register base | 0x0000_1000 (PHASE_SET, TRIGGER_EXEC, STATUS, FAULT_MASK) |

The QPA subsystem provides real-time control of the MZI photonic mesh.
The trigger matrix accepts phase vectors from the host via CXL, commits
them atomically to the DAC bus, and monitors optical power via SNSPD
feedback for fault detection and automatic rerouting.

### 3.5 Host Interface

| Parameter | Value |
|-----------|-------|
| PCIe generation | 6.0 (64 GT/s per lane, PAM4) |
| Lanes | x32 per SoC (split x16 + x16) |
| Bandwidth | 128 GB/s per direction (x16) |
| CXL | 2.0, Type 2 (memory + compute) |
| JTAG | IEEE 1149.1 + IEEE 1500 |
| Management | PMBus 1.3.1, I2C 400 kHz |
| Retimers | External (Astera PT6 / Montage M88RT51632) |

### 3.6 Power Management

| Parameter | Value |
|-----------|-------|
| V_core | 0.8 V typical, 1000 A+ peak |
| VDD_IO | 1.05 V / 1.2 V |
| Peak power | 800 W (V_core) + 100 W (I/O + mem) = 900 W |
| DVFS states | 8 (0.65 V / 800 MHz to 0.85 V / 2.0 GHz) |
| Power gates | Per-cluster (128 SIMD lanes as 8 clusters of 16) |
| Thermal sensors | 4x on-die diodes, 0.5 C resolution |
| Throttle trigger | Tj > 95 C (soft), Tj > 105 C (hard) |

### 3.7 Clock & Reset

| Clock Domain | Frequency | Source |
|-------------|-----------|--------|
| System (AXI fabric) | 250 MHz | PLL0 from 100 MHz REFCLK |
| DDR (LVDS serializer) | 500 MHz | PLL1 from 100 MHz REFCLK |
| Compute (SIMD array) | 1.0 - 2.0 GHz | PLL2, DVFS-controlled |
| SerDes reference | 156.25 MHz | PLL3 from 100 MHz REFCLK |
| HBM4 REFCK | 200 MHz | External Si5395A |
| DAC trigger | 10 MHz | External Si5395A sync |

---

## 4. I/O Ball Map Summary (BGA-2500)

| Domain | Ball Count | Location |
|--------|-----------|----------|
| V_CORE | 612 | Central core (cols N-AK, rows 10-38) |
| GND | 624 | Distributed |
| VDD_IO (1.05 V) | 96 | Peripheral rings |
| VDDC_HBM4 (0.7 V) | 40 | Interposer face (east) |
| VDDQL_HBM4 (0.4 V) | 40 | Interposer face (east) |
| VDDQ_HBM4 (1.1 V) | 40 | Interposer face (east) |
| VPP_HBM4 (1.8 V) | 16 | Interposer face (east) |
| HBM4 side-channel | 32 | Interposer face (4 stacks) |
| PCIe Gen 6 x32 | 144 | South edge |
| TFLN SerDes 16 ch | 96 | North edge |
| Mgmt I2C/SPI/JTAG | 32 | Corner (NW) |
| Thermal diode | 4 | Center |
| Reserved / NC | 156 | Distributed |
| **Total PCB-visible** | **2500** | |

Ball pitch: 0.8 mm. Package: 40 x 40 mm. Collapse height: 0.45 mm.

---

## 5. Process Node Considerations (SMIC 28nm / 40nm)

### 5.1 SMIC 28nm HPC+ (Primary Target)

| Parameter | SMIC 28nm HPC+ |
|-----------|----------------|
| Feature size | 28 nm |
| Gate type | High-Performance Compact (HPC+) |
| Metal layers | 10M (1P10M, Cu BEOL) |
| Vdd nominal | 0.9 V (core), scalable to 0.8 V |
| Frequency target | 1.0 - 1.5 GHz (compute cluster) |
| Leakage | ~100 nA/um (typical) |
| Standard cells | 9T library, drive strengths x1 to x16 |
| SRAM density | ~1.2 Mb/mm2 (6T) |
| I/O library | 1.8V / 3.3V tolerant, LVCMOS/LVDS |
| MPW availability | Via CMP / Europractice / MOSIS shuttle |

### 5.2 SMIC 40nm LL (Fallback)

| Parameter | SMIC 40nm LL |
|-----------|-------------|
| Feature size | 40 nm |
| Gate type | Low Leakage (LL) |
| Metal layers | 8M (1P8M, Cu BEOL) |
| Vdd nominal | 1.1 V (core) |
| Frequency target | 500 MHz - 1.0 GHz (compute cluster) |
| Leakage | ~10 nA/um (typical) |
| Standard cells | 12T library |
| SRAM density | ~0.8 Mb/mm2 (6T) |
| I/O library | 1.8V / 3.3V tolerant |
| MPW availability | Broader availability |

### 5.3 Die Area Estimate

| Block | Area (28nm) | Area (40nm) |
|-------|------------|------------|
| Compute Cluster (128-way SIMD) | ~12 mm2 | ~25 mm2 |
| L2 Cache (16 MB) | ~14 mm2 | ~20 mm2 |
| L3 Cache (64 MB) | ~54 mm2 | ~80 mm2 |
| HBM4 PHY (4-stack) | ~8 mm2 | ~14 mm2 |
| PCIe Gen 6 PHY (x32) | ~6 mm2 | ~10 mm2 |
| TFLN SerDes (16 lanes) | ~4 mm2 | ~7 mm2 |
| QPA Controller | ~1 mm2 | ~2 mm2 |
| PLL + Clock tree | ~1 mm2 | ~1.5 mm2 |
| Power management | ~0.5 mm2 | ~1 mm2 |
| Pad ring + ESD | ~8 mm2 | ~12 mm2 |
| **Total (est.)** | **~109 mm2** | **~173 mm2** |

**Note:** For the MPW shuttle test chip, a reduced-functionality die will
be taped out (see `MPW_Shuttle_Plan.md`), targeting ~4-9 mm2 to fit within
shuttle reticle constraints.

---

## 6. Functional Block Interactions

```
              +------------------+
              |   PCIe Gen 6     |<--- Host CPU / Switch
              |   Root Complex   |
              +--------+---------+
                       |
                       v
              +--------+---------+
              |  CXL 2.0 Ctrl   |
              |  (Memory-Mapped) |
              +---+---------+----+
                  |         |
       +----------+   +----+----------+
       |              |               |
       v              v               v
+------+------+ +-----+-------+ +----+----------+
| Compute     | | QPA Control | | Memory        |
| Cluster     | | (Trigger    | | Subsystem     |
| 128-way SIMD| | Matrix +    | | HBM4 PHY +   |
|             | | DAC + SNSPD)| | L3 Cache      |
+------+------+ +-----+-------+ +-------+-------+
       |               |                 |
       |         +-----+-------+         |
       |         | TFLN SerDes |         |
       |         | 16-ch PAM4  |         |
       |         +-----+-------+         |
       |               |                 |
       +-------+-------+---------+-------+
               |                 |
               v                 v
        +------+------+  +------+------+
        | Power Mgmt  |  | Clock/Reset |
        | DVFS + Gates|  | 4x PLL     |
        +-------------+  +-------------+
```

---

## 7. Design-for-Test (DFT)

| Feature | Implementation |
|---------|---------------|
| Scan chains | Full-scan insertion, compression ratio 64:1 |
| BIST | Memory BIST for all SRAM arrays (L1/L2/L3) |
| JTAG | IEEE 1149.1 boundary scan + IEEE 1500 wrapper |
| At-speed test | Launch-on-capture for compute cluster |
| Analog test | Loopback mode on all SerDes channels |
| Thermal | On-die diode calibration via JTAG |
| Production | Wafer sort + final test (ATE: Advantest V93000) |

---

## 8. Packaging

| Parameter | Value |
|-----------|-------|
| Package type | Organic FC-BGA (composite with interposer) |
| Ball count | 2500 (PCB-visible) |
| Ball pitch | 0.8 mm |
| Package size | 40 x 40 mm |
| Die size | ~10.5 x 10.5 mm (28nm) / ~13.2 x 13.2 mm (40nm) |
| Interposer | TSMC CoWoS-L / Intel Foveros-S class |
| Substrate layers | 12 (2-2-2-2-2-2) |
| Thermal interface | Lid-less, direct cold plate |
| Collapse height | 0.45 mm |

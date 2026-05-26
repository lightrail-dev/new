# NCE (Neural Compute Engine) — Internal Block Diagram

**Document:** LR-NCE-BLK-001  
**Revision:** 1.0  
**Date:** 2026-05-26  
**Process Node:** SMIC 28nm HPC+ / 40nm LL  
**Company:** LightRail AI  

---

## 1. Top-Level Block Diagram

```
+===========================================================================================+
|                              NCE SoC Die (BGA-2500)                                       |
|                                                                                           |
|  +-------+  +-------+  +-------+  +-------+                                              |
|  | JTAG  |  | PMBus |  | SPI   |  | I2C   |     <-- Management I/O (NW corner)           |
|  | Debug |  | Mgmt  |  | Flash |  | Bus   |                                              |
|  +---+---+  +---+---+  +---+---+  +---+---+                                              |
|      |          |          |          |                                                    |
|      +----------+----------+----------+                                                   |
|                 |                                                                         |
|           +-----+------+                                                                  |
|           | System Bus |    AXI4 Interconnect Fabric (250 MHz)                            |
|           | Crossbar   +----------------------------------------------------------+       |
|           +--+---------+--+-----------+--+-----------+--+-----------+--+          |       |
|              |            |             |              |              |            |       |
|              v            v             v              v              v            v       |
|  +-----------+--+ +------+------+ +----+------+ +-----+-----+ +-----+-----+ +----+----+  |
|  | COMPUTE      | | MEMORY      | | PHOTONIC  | | QPA       | | HOST      | | POWER   |  |
|  | CLUSTER      | | SUBSYSTEM   | | I/O       | | CONTROL   | | INTERFACE | | MGMT    |  |
|  +-----------+--+ +------+------+ +----+------+ +-----+-----+ +-----+-----+ +----+----+  |
|              |            |             |              |              |            |       |
|  (detail     |  (detail   |  (detail    |   (detail    |   (detail    |  (detail   |      |
|   below)     |   below)   |   below)    |    below)    |    below)    |   below)   |      |
|              |            |             |              |              |            |       |
+===========================================================================================+
```

---

## 2. Compute Cluster Block Diagram

```
+=========================================================================+
|                        COMPUTE CLUSTER                                  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |                    Instruction Frontend                           |  |
|  |  +----------------+  +-----------------+  +-------------------+  |  |
|  |  | Instr Fetch    |  | Instr Decode    |  | Issue / Dispatch  |  |  |
|  |  | Unit (IFU)     |->| Unit (IDU)      |->| Unit              |  |  |
|  |  | L1 I$ 64KB     |  | bfloat16/24     |  | In-order SIMD     |  |  |
|  |  | 4-way assoc    |  | INT8, FP32      |  | Scalar bypass     |  |  |
|  |  +----------------+  +-----------------+  +--------+----------+  |  |
|  +------------------------------------------------------------------+  |
|                                                       |                |
|                                    +------------------+--------+       |
|                                    |                           |       |
|                                    v                           v       |
|  +----------------------------------+   +------------------------+     |
|  |     SIMD Execution Engine        |   | Scalar Execution Unit  |     |
|  |                                  |   |                        |     |
|  |  +----------------------------+  |   | +--------------------+ |     |
|  |  | 128-way SIMD Array         |  |   | | ALU (INT/FP)       | |     |
|  |  | 8 clusters x 16 lanes     |  |   | | Branch Unit        | |     |
|  |  |                            |  |   | | Address Gen        | |     |
|  |  | Each lane:                 |  |   | +--------------------+ |     |
|  |  |   bfloat16 MAC unit        |  |   +------------------------+     |
|  |  |   bfloat24 MAC unit        |  |                                  |
|  |  |   INT8 MAC unit (4x pack)  |  |                                  |
|  |  |   FP32 accumulator         |  |                                  |
|  |  +----------------------------+  |                                  |
|  |                                  |                                  |
|  |  +----------------------------+  |                                  |
|  |  | Register File              |  |                                  |
|  |  | 16x Matrix Regs (256-bit)  |  |                                  |
|  |  | 16x Vector Regs (256-bit)  |  |                                  |
|  |  | 8x Scalar Regs (64-bit)    |  |                                  |
|  |  +----------------------------+  |                                  |
|  +----------------------------------+                                  |
|                     |                                                  |
|                     v                                                  |
|  +----------------------------------+                                  |
|  |      Memory Access Pipeline      |                                  |
|  |  +-------------+  +----------+   |                                  |
|  |  | Load/Store  |  | L1 D$    |   |                                  |
|  |  | Unit (LSU)  |->| 128 KB   |   |                                  |
|  |  | Scatter/    |  | 8-way    |   |                                  |
|  |  | Gather      |  | assoc    |   |                                  |
|  |  +-------------+  +----+-----+   |                                  |
|  +----------------------------------+                                  |
|                            |                                           |
|                            v                                           |
|  +----------------------------------+                                  |
|  |       L2 Cache (Shared)          |                                  |
|  |  16 MB, 8-way, inclusive         |                                  |
|  |  64-byte lines, write-back       |                                  |
|  |  4 DMA channels (scatter-gather) |                                  |
|  +----------------------------------+                                  |
|                                                                        |
+========================================================================+
```

**Function:** Executes AI/ML tensor operations (matrix multiply, convolution,
activation) on streaming data. The 128-way SIMD array processes 128 bfloat16
multiply-accumulate operations per cycle. Data flows from HBM4 through the
cache hierarchy into the register file, and results can be sent to the TFLN
photonic I/O for distributed all-reduce.

---

## 3. Memory Subsystem Block Diagram

```
+=========================================================================+
|                      MEMORY SUBSYSTEM                                   |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |                 L3 / Last-Level Cache                             |  |
|  |  64 MB, 16-way set-associative, exclusive of L2                  |  |
|  |  128-byte lines, write-back, pseudo-LRU                          |  |
|  |  Coherence: MOESI (for CXL.mem shared memory)                    |  |
|  +---+------------------------------------------+-------------------+  |
|      |                                          |                      |
|      v                                          v                      |
|  +---+------------------+   +-------------------+-------------------+  |
|  | Memory Scheduler     |   | HBM4 Side-Channel Controller         |  |
|  | & Arbiter            |   |                                       |  |
|  | - Request queue      |   | - REFCK_P/N generation                |  |
|  | - Bank interleaving  |   | - CATTRIP / PWR_GOOD monitoring      |  |
|  | - Refresh management |   | - IEEE 1500 JTAG (TCK/TMS/TDI/TDO)  |  |
|  | - ECC encode/decode  |   | - Temperature readout                 |  |
|  +---+------------------+   +---+-----------------------------------+  |
|      |                          |                                      |
|      v                          v                                      |
|  +---+-------------------------------------------------+              |
|  |           HBM4 PHY Controller                       |              |
|  |                                                     |              |
|  |  Stack 0     Stack 1     Stack 2     Stack 3        |              |
|  |  +--------+  +--------+  +--------+  +--------+    |              |
|  |  |1024 ln |  |1024 ln |  |1024 ln |  |1024 ln |    |              |
|  |  |8Gbps/  |  |8Gbps/  |  |8Gbps/  |  |8Gbps/  |    |              |
|  |  |pin     |  |pin     |  |pin     |  |pin     |    |              |
|  |  |1 TB/s  |  |1 TB/s  |  |1 TB/s  |  |1 TB/s  |    |              |
|  |  +--------+  +--------+  +--------+  +--------+    |              |
|  |                                                     |              |
|  |  Total: 4096 lanes, 4.0 TB/s aggregate              |              |
|  |  (All lanes routed on silicon interposer)           |              |
|  +-----------------------------------------------------+              |
|                                                                        |
+========================================================================+
```

**Function:** Provides 4.0 TB/s memory bandwidth to the compute cluster via
four HBM4 12-Hi stacks. The L3 cache serves as a victim cache for L2 misses.
The memory scheduler implements bank-level parallelism and ECC for data integrity.

---

## 4. Photonic I/O Subsystem Block Diagram

```
+=========================================================================+
|                    PHOTONIC I/O SUBSYSTEM                               |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |                     TX Path (8 channels)                          |  |
|  |                                                                   |  |
|  |  +----------+  +----------+  +----------+  +----------+          |  |
|  |  | TX DSP   |  | PAM4     |  | DAC      |  | RF Drive |  --> To  |  |
|  |  | 3-tap    |->| Encoder  |->| (SerDes  |->| Buffer   |  TFLN   |  |
|  |  | FFE      |  |          |  |  analog) |  | +/- 1.5V |  PIC    |  |
|  |  +----------+  +----------+  +----------+  +----------+          |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |                     RX Path (8 channels)                          |  |
|  |                                                                   |  |
|  |  From   +----------+  +----------+  +----------+  +----------+   |  |
|  |  TFLN ->| TIA /    |->| ADC      |->| PAM4     |->| RX DSP   |   |  |
|  |  PIC    | AGC      |  | (SerDes  |  | Decoder  |  | CTLE +   |   |  |
|  |         |          |  |  analog) |  |          |  | 7-tap DFE|   |  |
|  |         +----------+  +----------+  +----------+  +----------+   |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |                   CDR & Link Training                             |  |
|  |                                                                   |  |
|  |  +-------------------+  +-------------------+                     |  |
|  |  | Clock Data        |  | Link Training     |                     |  |
|  |  | Recovery (CDR)    |  | State Machine     |                     |  |
|  |  | per-lane          |  | Auto-negotiation  |                     |  |
|  |  | 0.1 UI tolerance  |  | Loopback modes    |                     |  |
|  |  +-------------------+  +-------------------+                     |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  Channel Summary:                                                       |
|  8 TX + 8 RX = 16 lanes total                                          |
|  200 Gbps PAM4 per lane = 1.6 Tbps half-duplex                         |
|  Direct-drive to TFLN modulator (zero-copper datapath)                  |
|  1550 nm C-band DWDM, 100 GHz channel spacing                          |
|                                                                         |
+=========================================================================+
```

**Function:** Converts electrical data from the compute cluster into optical
signals via direct-drive TFLN modulators. The TX path applies DSP equalization,
encodes to PAM4, and drives the TFLN MZI electrodes. The RX path receives
optical signals from photodetectors, digitizes, and recovers data with adaptive
equalization.

---

## 5. QPA Control Subsystem Block Diagram

```
+=========================================================================+
|                    QPA CONTROL SUBSYSTEM                                |
|                                                                         |
|  CXL 2.0 Memory-Mapped Interface                                       |
|  Base: 0x0000_1000                                                      |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |              CXL Register Decoder                                 |  |
|  |                                                                   |  |
|  |  0x1000: PHASE_SET      -- Write phase vector into shadow buffer  |  |
|  |  0x1004: TRIGGER_EXEC   -- Atomic commit shadow -> DAC bus        |  |
|  |  0x1008: STATUS         -- Read trigger state & channel health    |  |
|  |  0x100C: FAULT_MASK     -- Per-channel fault enable mask          |  |
|  |  0x1010: TELEMETRY_CTRL -- Telemetry sampling on/off              |  |
|  +---+------+----------+--------+------+----------------------------+  |
|      |      |          |        |      |                               |
|      v      v          |        v      v                               |
|  +---+---+ +--+--+     |  +----+---+ ++----+                          |
|  |Shadow | |Trig | |   |  |Fault   | |Telem|                          |
|  |Buffer | |Pipe | |   |  |Mask    | |Ctrl |                          |
|  |128-bit| |line | |   |  |Reg     | |Reg  |                          |
|  +---+---+ +--+--+     |  +----+---+ +--+--+                          |
|      |        |         |       |        |                             |
|      v        v         |       v        v                             |
|  +---+--------+---+    |  +----+--------+---+                         |
|  | DAC Phase Bus  |    |  | Telemetry Status |                        |
|  | 8ch x 16-bit   |    |  | {fault_cnt[15:0],|                        |
|  | Zero-skew sync |    |  |  trig_cnt[15:0]} |                        |
|  +-------+---------+    |  +-----------------+                         |
|          |              |                                              |
|          v              v                                              |
|  +-------+---------+  +---+-------------------+                       |
|  | 100 GHz DACs    |  | SNSPD Fault Detector  |                       |
|  | (external)      |  | 3 dB drop detection   |                       |
|  | Interleaved     |  | Per-channel latch      |                       |
|  +-----------------+  | Auto-reroute output    |                       |
|                       +------------------------+                       |
|                                                                        |
+=========================================================================+
```

**Function:** Provides real-time programmable control of the MZI photonic mesh.
The shadow buffer allows atomic updates of all phase channels simultaneously.
A one-cycle pipeline ensures zero-skew synchronization between phase setting
and DAC trigger. SNSPD feedback detects optical power drops and triggers
automatic waveguide rerouting.

---

## 6. Host Interface Block Diagram

```
+=========================================================================+
|                      HOST INTERFACE                                     |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |              PCIe Gen 6.0 Root Complex                            |  |
|  |                                                                   |  |
|  |  Port 0 (x16)                    Port 1 (x16)                    |  |
|  |  +-------------------+           +-------------------+           |  |
|  |  | 16 lanes          |           | 16 lanes          |           |  |
|  |  | 64 GT/s PAM4      |           | 64 GT/s PAM4      |           |  |
|  |  | 128 GB/s bidir    |           | 128 GB/s bidir    |           |  |
|  |  +-------------------+           +-------------------+           |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |              CXL 2.0 Controller (Type 2)                          |  |
|  |                                                                   |  |
|  |  +-------------+  +-------------+  +-------------+               |  |
|  |  | CXL.io      |  | CXL.cache   |  | CXL.mem     |               |  |
|  |  | (PCIe TLP)  |  | (coherent   |  | (shared     |               |  |
|  |  |             |  |  cache)     |  |  memory)    |               |  |
|  |  +-------------+  +-------------+  +-------------+               |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |              Debug & Management                                   |  |
|  |                                                                   |  |
|  |  +----------+  +----------+  +----------+  +----------+          |  |
|  |  | JTAG     |  | PMBus    |  | I2C      |  | SPI      |          |  |
|  |  | IEEE1149 |  | 1.3.1    |  | 400 kHz  |  | Flash    |          |  |
|  |  | IEEE1500 |  | VRM tele |  | HBM4 SPD |  | FW boot  |          |  |
|  |  +----------+  +----------+  +----------+  +----------+          |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
+=========================================================================+
```

---

## 7. Power Management Block Diagram

```
+=========================================================================+
|                     POWER MANAGEMENT UNIT                               |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |            DVFS Controller                                        |  |
|  |                                                                   |  |
|  |  +-------------------+  +------------------+                      |  |
|  |  | Voltage Request   |  | Frequency Select |                      |  |
|  |  | Generator         |->| (PLL relock)     |                      |  |
|  |  |                   |  |                   |                      |  |
|  |  | 8 V/F states:     |  | State 0: 0.65V / 800MHz               |  |
|  |  | PMBus -> VRM      |  | State 1: 0.70V / 1.0GHz               |  |
|  |  |                   |  | State 2: 0.75V / 1.2GHz               |  |
|  |  |                   |  | ...                                    |  |
|  |  |                   |  | State 7: 0.85V / 2.0GHz               |  |
|  |  +-------------------+  +------------------+                      |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |            Power Gate Array                                       |  |
|  |                                                                   |  |
|  |  Cluster 0  Cluster 1  ...  Cluster 7                             |  |
|  |  +------+   +------+       +------+                               |  |
|  |  | 16   |   | 16   |       | 16   |   <-- Each cluster: 16 SIMD  |  |
|  |  | SIMD |   | SIMD |       | SIMD |       lanes + header switch   |  |
|  |  | lanes|   | lanes|       | lanes|                               |  |
|  |  +--+---+   +--+---+       +--+---+                               |  |
|  |     |          |              |                                    |  |
|  |  [gate]     [gate]         [gate]    <-- MTCMOS power switches    |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |            Thermal Monitor                                        |  |
|  |                                                                   |  |
|  |  +--------+  +--------+  +--------+  +--------+                  |  |
|  |  |Diode 0 |  |Diode 1 |  |Diode 2 |  |Diode 3 |                  |  |
|  |  |Compute |  |Compute |  |SerDes  |  |Memory  |                  |  |
|  |  |cluster |  |cluster |  |PHY     |  |PHY     |                  |  |
|  |  +---+----+  +---+----+  +---+----+  +---+----+                  |  |
|  |      |           |           |           |                        |  |
|  |      +-----+-----+-----+-----+                                   |  |
|  |            |                                                      |  |
|  |      +-----v---------+                                            |  |
|  |      | Thermal Ctrl  |  Tj > 95C: soft throttle (reduce V/F)     |  |
|  |      | State Machine |  Tj > 105C: hard throttle (min V/F)       |  |
|  |      |               |  Tj > 115C: emergency shutdown            |  |
|  |      +---------------+                                            |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
+=========================================================================+
```

---

## 8. Clock Distribution Block Diagram

```
+=========================================================================+
|                     CLOCK & RESET SUBSYSTEM                             |
|                                                                         |
|         External 100 MHz REFCLK (from Si5395A)                          |
|                         |                                               |
|                  +------v------+                                        |
|                  | Input       |                                        |
|                  | Buffer/Mux  |                                        |
|                  +--+--+--+--++                                         |
|                     |  |  |  |                                          |
|         +-----------+  |  |  +-----------+                              |
|         |              |  |              |                               |
|    +----v----+   +-----v-+   +----v----+  +----v----+                   |
|    | PLL0    |   | PLL1  |   | PLL2    |  | PLL3    |                   |
|    | 250 MHz |   | 500MHz|   | 1-2 GHz |  | 156.25  |                   |
|    | System  |   | DDR   |   | Compute |  | MHz     |                   |
|    | AXI bus |   | LVDS  |   | DVFS    |  | SerDes  |                   |
|    +----+----+   +---+---+   +----+----+  +----+----+                   |
|         |            |            |            |                         |
|         v            v            v            v                         |
|    H-tree       H-tree       H-tree       H-tree                       |
|    distrib.     distrib.     distrib.     distrib.                      |
|    (low skew    (to LVDS     (to SIMD     (to SerDes                    |
|     < 50 ps)    serializer)  clusters)    PHY lanes)                    |
|                                                                         |
|  +------------------------------------------------------------------+  |
|  |              Reset Sequencer                                      |  |
|  |                                                                   |  |
|  |  Power-on Reset (POR) --> Boot ROM --> PLL lock wait -->          |  |
|  |  Release compute --> Release I/O --> System ready                 |  |
|  |                                                                   |  |
|  |  Warm reset: re-initialize without PLL relock                     |  |
|  |  Watchdog reset: 32-bit downcounter, NMI before reset             |  |
|  |                                                                   |  |
|  +------------------------------------------------------------------+  |
|                                                                         |
+=========================================================================+
```

---

## 9. Complete Chip Floorplan (Conceptual)

```
+-------------------------------------------------------------------+
|                          PAD RING (2500 balls)                     |
|  +------+------+------+------+------+------+------+------+       |
|  | JTAG | I2C  | SPI  | PMBus|      |      |      |      |  NW   |
|  +------+------+------+------+      |      |      |      |       |
|                                      |      |      |      |       |
|  +-----------------------------------+      |      |      |       |
|  |         TFLN SerDes PHY (N edge)  |      |      |      |       |
|  |    8 TX + 8 RX @ 200G PAM4       |      |      |      |       |
|  +-----------------------------------+      |      |      |       |
|                                              |      |      |       |
|  +------------------+  +-------------------+ |      |      |       |
|  |                  |  |                   | |      |      |       |
|  |   COMPUTE        |  |   L3 CACHE        | |      |      |       |
|  |   CLUSTER        |  |   64 MB            | |      |      |       |
|  |   128-way SIMD   |  |                   | |      |      |       |
|  |   + L1/L2        |  |                   | |      |      |       |
|  |   12 mm2 (28nm)  |  |   54 mm2 (28nm)   | |      |      |       |
|  |                  |  |                   | |      |      |       |
|  +------------------+  +-------------------+ |      |      |       |
|                                              |      |      |       |
|  +---------+  +--------+  +--------+        |      |      |       |
|  | QPA Ctrl|  | Power  |  | Clock  |        |      |      |       |
|  | 1 mm2   |  | Mgmt   |  | PLLs   |        |      |      |       |
|  +---------+  +--------+  +--------+        |      |      |       |
|                                              |      |      |       |
|  +-------------------------------------------+      |      |       |
|  |   HBM4 PHY Controller (interposer interface)     |      |       |
|  |   4-stack, micro-bump connections                 |      |       |
|  +-------------------------------------------+------+      |       |
|                                                             |       |
|  +----------------------------------------------------------+       |
|  |              PCIe Gen 6 PHY (S edge)                      |       |
|  |    x32 lanes (split x16 + x16) @ 64 GT/s PAM4            |       |
|  +-----------------------------------------------------------+       |
|                                                                      |
+----------------------------------------------------------------------+
```

---

## 10. Data Flow Summary

| Path | Source | Destination | Bandwidth | Latency |
|------|--------|-------------|-----------|---------|
| Compute -> HBM4 | SIMD cluster | HBM4 stacks | 4.0 TB/s | ~100 ns |
| HBM4 -> Compute | HBM4 stacks | SIMD cluster | 4.0 TB/s | ~100 ns |
| Compute -> TFLN TX | SIMD cluster | Photonic I/O | 1.6 Tbps | ~10 ns |
| TFLN RX -> Compute | Photonic I/O | SIMD cluster | 1.6 Tbps | ~10 ns |
| Host -> NCE | PCIe Gen 6 | CXL controller | 128 GB/s | ~500 ns |
| Host -> QPA | PCIe/CXL | QPA registers | MMIO | ~200 ns |
| QPA -> DAC | Trigger matrix | 100 GHz DACs | 8 x 16-bit | 2 cycles |
| SNSPD -> QPA | Photodetectors | Fault monitor | 8-bit | 1 cycle |

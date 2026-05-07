# LR-S1A — LightRail AI 1U CPO Switch — Architectural Bill of Materials

**Project:**       LR-S1A — LightRail AI 51.2 Tbps Co-Packaged Optical Switch
**Form factor:**   1U rack-mount, 19″ EIA, ≈ 800 mm depth
**Switch ASIC:**   1 × LightRail AI central switch ASIC, 256 × 200 G PAM4 SerDes, liquid-cooled
**Optical I/O:**   16 × CPO engines (3.2 Tbps each) → 51.2 Tbps aggregate
**Laser source:**  8 × ELSFP CW laser modules (front-panel, hot-swappable)
**Front-panel I/O:** 32 × high-density optical ports (OSFP-XD or QSFP-DD-1600)
**Designer of Record:** LightRail AI
**Revision:** A0 (release for sourcing-quote and investor data-room)
**Date:** 2026-04-19
**Status:** Released — architectural BOM for sourcing, costing, and investor due-diligence

---

## Reading guide

This document is the **architectural / system-level BOM**. It enumerates every
functional sub-assembly, module, and discrete part required to build one
LR-S1A unit, organised in the five-section structural breakdown standard for
CPO switches:

1. Core processing & optical subsystem (the CPO assembly)
2. Optical routing & cable management
3. Front-panel interfaces (I/O & lasers)
4. Secondary circuitry & power delivery
5. Chassis hardware

Each line item carries a LightRail AI internal part number (`LR-…`), the
recommended commercial manufacturer / MPN where one is the obvious choice,
quantity per unit, and an engineering note. Items marked **vendor-NDA** are
LightRail AI proprietary silicon (TFLN PIC, switch ASIC, CPO engine) and are
sourced internally.

The flat CSV equivalent (`fab/LR-S1A_CPO_Switch_BOM.csv`) is the
machine-readable form for sourcing / costing pipelines.

---

## 1. Core processing & optical subsystem (CPO assembly)

The heart of the switch. Central switch ASIC, 16 co-packaged optical engines,
silicon interposer, and the liquid-cooled thermal stack — all mounted on the
main PCB.

| #  | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|----|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 1.1  | Central switch ASIC, 51.2 Tbps   | `LR-CSW-51T2-A0`  | LightRail AI (vendor-NDA)                              | 1   | 256 × 200 G PAM4 SerDes; 7 nm node; 80 × 80 mm BGA-5500 composite. ~ 600 W TDP |
| 1.2  | CPO optical engine, 3.2 Tbps     | `LR-CPO-3T2-A0`   | LightRail AI (TFLN-based, vendor-NDA)                  | 16  | TFLN Mach-Zehnder modulator array + Ge-Si PD + driver/TIA chiplet; 16 × 200 G PAM4 per engine |
| 1.3  | Silicon interposer (CoWoS-L)     | `LR-INT-S1A-A0`   | TSMC CoWoS-L (vendor-NDA)                              | 1   | 80 × 80 mm interposer carrying ASIC + 16 CPO engines; routes 4 096 SerDes lanes interposer-resident |
| 1.4  | Bridging chiplet (D2D PHY)       | `LR-D2D-S1A-A0`   | LightRail AI                                           | 16  | UCIe 1.1 die-to-die PHY between switch ASIC and each CPO engine |
| 1.5  | TFLN PIC die                     | `LR-TFLN-200G-A0` | LightRail AI Photonics (vendor-NDA)                    | 16  | 16 × 200 G TFLN modulator array per PIC; integrated edge coupler to ribbon |
| 1.6  | CPO engine micro-bump underfill  | `LR-UF-CPO-A0`    | Henkel Loctite ECCOBOND UF 3810                        | 16  | Capillary-flow underfill for CPO chiplet attach |
| 1.7  | Composite-BGA underfill           | `LR-UF-BGA-A0`    | Namics XS8410-251                                      | 1   | Underfill for the central switch ASIC composite BGA |
| 1.8  | ASIC TIM (Indium foil)            | `LR-TIM-IN-A0`    | Indium Corporation Indium-7M, 100 µm                    | 1   | High-conductivity TIM-1.5 for cold-plate-to-ASIC interface |
| 1.9  | Cold plate (Cu, microchannel)     | `LR-CP-S1A-A0`    | Asetek / CoolIT custom (LR drawing)                     | 1   | Skived-fin Cu microchannel cold plate over ASIC + CPO ring; 25 mL/s @ 30 kPa |
| 1.10 | Cold-plate retention frame        | `LR-CP-BRK-S1A`   | Custom (Al 6061-T6, anodised)                           | 1   | 4-corner retention with calibrated belleville springs |
| 1.11 | Liquid-cooling quick-disconnects  | `LR-LQ-QD-A0`     | CPC Everis LQ4 (40 LPM)                                 | 2   | Drip-less inlet + outlet to chassis manifold |
| 1.12 | Internal coolant tubing           | `LR-LQ-TUB-A0`    | Saint-Gobain Tygon SE-200, 1/4″ ID                      | 1.5 m | Low-permeation coolant tubing |
| 1.13 | Coolant flow & temperature sensor | `LR-LQ-SNS-A0`    | TE Connectivity FTB332 + NTC                            | 1   | Inline flow / temperature for BMC telemetry |
| 1.14 | Main PCB (18-layer HDI)           | `LR-PCB-S1A-A0`   | Custom (Megtron-7 + High-Tg FR-4 + Faradflex BC24)      | 1   | 600 × 400 mm, IPC-6012 Class 3, controlled impedance ±5 % |
| 1.15 | Backside ASIC bolster             | `LR-BLS-S1A-A0`   | Custom (steel, electroless-nickel)                      | 1   | Mechanical reinforcement under composite-BGA footprint |
| 1.16 | ESD-grounding strap               | —                 | 3M 2110                                                 | 4   | Cold plate ↔ chassis ground bond |
| 1.17 | ASIC test / debug header          | `LR-DBG-S1A-A0`   | Samtec ERM8-040-05.0-L-DV-A-K                           | 1   | 80-pin high-speed JTAG / SCAN / I²C debug header |

**Section 1 unit count:** 17 line items, ≈ 100 individual parts (incl. multi-qty optical engines, PICs, D2D chiplets).

---

## 2. Optical routing & cable management

Routes ribbon fibre from the 16 CPO engines through SENKO mid-board connectors
to the front-panel I/O cages.

| #  | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|----|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 2.1 | Internal SMF ribbon assembly, 16-fibre | `LR-RIB-16F-A0` | Furukawa SCC OS2 9/125, polyimide-jacketed              | 32  | 16 fibres × OS2; 0.30 m typical reach from CPO engine to mid-board connector |
| 2.2 | SENKO SN-MT mid-board connector (16-fibre) | `LR-MID-SN16-A0` | SENKO Advanced Components SN-MT-16                | 32  | High-density mid-board optical connector; 0.5 mm pitch |
| 2.3 | SENKO MPO-16 to MPO-16 patch ribbon | `LR-PATCH-MPO16-A0` | SENKO MPO-16-OS2-1.5m                              | 16  | Front-panel-to-cage routing; pre-terminated, Pinned-to-Unpinned |
| 2.4 | Front-panel optical bulkhead, MPO-16 | `LR-BHD-MPO16-A0` | SENKO LC-MPO16-PIN-BHD                              | 16  | Bulkhead pass-through with dust shutter |
| 2.5 | Cable routing tray, primary       | `LR-TRAY-MAIN-A0` | Custom (Polyamide 12, FDM-printable Al)                | 2   | Left + right primary fibre raceway; 35 mm bend-radius limit |
| 2.6 | Cable routing tray, transverse    | `LR-TRAY-TRV-A0`  | Custom (Polyamide 12)                                   | 1   | Centre-line cross-over tray over the cold-plate manifold |
| 2.7 | Bend-limiting fibre boot          | `LR-BOOT-A0`      | Panduit FBSB-FQTS-C0                                    | 64  | One per ribbon termination at SENKO connectors |
| 2.8 | Strain-relief clamp               | `LR-SR-CLAMP-A0`  | Heyco S6P4-4                                            | 24  | Mid-tray strain-relief; locks fibre runs to chassis |
| 2.9 | Polyimide tape (Kapton 1 mil)     | —                 | DuPont Kapton HN, 12 mm wide                            | 0.5 roll | Tie-down + bundle protection; 2-roll engineering pack |
| 2.10 | Heat-shrink fibre label sleeve   | `LR-LBL-FIBR-A0`  | TE Connectivity ZHTM-3/1                                | 64  | Per-ribbon ID labelling; printed in production |

**Section 2 unit count:** 10 line items, ≈ 200 individual parts.

---

## 3. Front-panel interfaces (I/O & lasers)

Hot-swappable laser sources, 32 high-density optical I/O ports, and the
out-of-band management bezel.

| #  | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|----|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 3.1 | ELSFP module — External Laser, 8-channel CW | `LR-ELSFP-CW8-1310-A0` | LightRail AI Photonics (vendor-NDA)         | 8   | DFB array @ 1310 nm CFP-style external laser source; +18 dBm per channel; pluggable, hot-swappable |
| 3.2 | ELSFP cage assembly               | `LR-CAGE-ELSFP-A0` | Amphenol Communications Solutions 10160988-001LF       | 8   | EMI-gasketed cage with thermal pad and integrated heat sink |
| 3.3 | ELSFP heat sink                   | `LR-HS-ELSFP-A0`  | Wakefield-Vette 658-25ABT                               | 8   | Pin-fin heat sink, top-mount, 4 °C/W |
| 3.4 | High-density optical I/O cage (OSFP-XD)  | `LR-CAGE-OSFP-A0` | TE Connectivity 2358153-1                          | 32  | OSFP-XD 1.6 T cage with riding heat sink; supports 32 × 1.6 TbE or 64 × 800 GbE |
| 3.5 | OSFP-XD heat sink                 | `LR-HS-OSFP-A0`   | TE 2358145-1                                            | 32  | 5 °C/W riding heat sink                |
| 3.6 | Front-panel I/O retention spring  | —                 | TE 2358118-1                                            | 32  | Module-eject latch + EMI spring |
| 3.7 | Management RJ-45, 1 GbE           | `LR-MGT-RJ45-A0`  | Bel Stewart Connector SI-50170-F                        | 1   | Magnetic-isolated jack with integrated LEDs |
| 3.8 | USB-A console port                | `LR-MGT-USB-A0`   | Würth Elektronik 692121030100                           | 1   | USB 2.0 type-A; ESD-protected via TPD2EUSB30 |
| 3.9 | RS-232 console (RJ-45)            | `LR-MGT-CON-A0`   | TE 5-1734742-1                                          | 1   | Cisco-compatible RJ-45 console pinout |
| 3.10 | Front-panel status LEDs          | `LR-LED-FP-A0`    | Lumex SML-LX1610UPGCTR / SML-LX1610USRC / SML-LX1610UYC | 12  | PWR (G), STATUS (G), FAULT (R), FAN (Y), PSU-A/B (G/R), OPT-link (G) per port group |
| 3.11 | Front-panel plate                 | `LR-FP-PLATE-A0`  | Custom (Al 5052-H32, anodised black)                    | 1   | 1U front bezel with cut-outs + LightRail AI logo |
| 3.12 | Front-panel pull handle (× 2)     | `LR-FP-HDL-A0`    | Custom (Al 6061, anodised)                              | 2   | Rack-handle on each side |
| 3.13 | Front-panel EMI gasket            | `LR-EMI-FP-A0`    | Laird 8961-0001                                         | 1.2 m | Bekiwoven gasket around front bezel perimeter |
| 3.14 | Light-pipe array                  | `LR-LP-FP-A0`     | Bivar PLP4-300                                          | 12  | Routes PCB-side LEDs to front-bezel apertures |

**Section 3 unit count:** 14 line items, ≈ 110 individual parts.

---

## 4. Secondary circuitry & power delivery

Control-plane daughterboard, on-board PDN, hot-swap PSU bays, and active
cooling. The main-board VRM cluster delivers ASIC-core (V_ASIC ≈ 0.85 V) and
optical-engine rails (V_OPT ≈ 1.2 V); the daughterboard runs the switch OS.

### 4.1 Control-plane daughterboard (one PCB sub-assembly)

| #     | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|-------|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 4.1.1 | Control-plane CPU                 | `LR-CPU-CPM-A0`   | Intel Atom C3858 (16-core, 12 W) **or** AMD EPYC Embedded 3251 | 1   | Vendor-selectable; pin-compatible reference footprints in schematic |
| 4.1.2 | DDR5 SODIMM, 32 GB ECC            | —                 | Micron MTC20F2085S1RC56BR                                | 2   | 64 GB total, 4 800 MT/s ECC |
| 4.1.3 | NVMe M.2 2280 SSD, 256 GB         | —                 | Samsung MZ-V8V250B/AM                                    | 1   | OS + log volume |
| 4.1.4 | BMC                               | `LR-BMC-AST26-A0` | ASPEED AST2600A3                                         | 1   | IPMI 2.0 / Redfish; 1 GbE NCSI to mgmt port |
| 4.1.5 | BMC SDRAM (DDR4, 1 GB)            | —                 | Micron MT40A512M16JY-062E                                | 1   | Dedicated BMC memory |
| 4.1.6 | BMC SPI flash (256 Mb)            | —                 | Macronix MX25L25645GMI-08G                               | 2   | Boot + redundant golden image |
| 4.1.7 | TPM 2.0 module                    | `LR-TPM-A0`       | Infineon SLB9670VQ20FW785                                | 1   | Secure-boot root-of-trust |
| 4.1.8 | 1 GbE PHY                         | —                 | Realtek RTL8211FDI-CG                                    | 1   | NCSI-side BMC PHY |
| 4.1.9 | RTC + battery                     | —                 | NXP PCF85063ATL/1Z + CR2032 holder                       | 1   | Coin-cell holder Linx BAT-HLD-001 |
| 4.1.10 | Daughterboard PCB                | `LR-DB-CPM-A0`    | Custom (10-layer FR-4)                                   | 1   | 200 × 110 mm; standard FR-4 stackup |
| 4.1.11 | Board-to-board connector (Samtec ARC) | `LR-B2B-CPM-A0` | Samtec ARC6-30-01-L-D-A-K                              | 2   | Hi-density 80-pin Hi-LPS B2B between daughterboard and main PCB |

### 4.2 Main-board power delivery (V_ASIC + V_OPT + housekeeping)

| #     | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|-------|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 4.2.1 | V_ASIC controller (multi-phase)   | `LR-VRM-ASIC-A0`  | MPS MP2965GU                                             | 2   | 2 × 8-phase controller; 16-phase total for V_ASIC |
| 4.2.2 | DrMOS, 70 A integrated stage      | —                 | MPS MP86957                                              | 16  | V_ASIC phase stages |
| 4.2.3 | V_OPT controller (4-phase)        | `LR-VRM-OPT-A0`   | MPS MP2964GU                                             | 1   | 4-phase, 1.2 V optical-engine rail |
| 4.2.4 | DrMOS, 50 A integrated stage      | —                 | MPS MP87005                                              | 4   | V_OPT phase stages |
| 4.2.5 | V_AUX (1.8 V / 3.3 V / 5 V housekeeping) | `LR-VRM-AUX-A0` | TI TPS6594-Q1 PMIC                                  | 1   | Housekeeping rails for clocks, BMC, PHYs |
| 4.2.6 | Hot-swap controller, 12 V → main  | `LR-HSC-12V-A0`   | Analog Devices LTC4282CUHF                               | 2   | Per-PSU hot-swap + telemetry; 2-OR-ed onto main 12 V plane |
| 4.2.7 | Power inductor, 0.15 µH           | —                 | Vishay IHLE-2525CD-5A                                    | 16  | V_ASIC phase inductor |
| 4.2.8 | Power inductor, 0.22 µH           | —                 | Vishay IHLE-2525CD-5B                                    | 4   | V_OPT phase inductor |
| 4.2.9 | Bulk polymer cap, 470 µF / 16 V   | —                 | Panasonic EEFGX1C471XR                                   | 24  | Output bulk decap on V_ASIC + V_OPT |
| 4.2.10 | MLCC 22 µF / 16 V (1210)         | —                 | Murata GRM32ER61C226KE20L                                | 80  | Tier-2 decap |
| 4.2.11 | MLCC 1 µF / 16 V (0402)          | —                 | Murata GRM155R61C105KA12D                                | 400 | Tier-3 decap |
| 4.2.12 | MLCC 100 nF / 16 V (0201)        | —                 | Murata GRM033R61C104KE15D                                | 1 200 | Tier-4 decap; ≤ 1 mm from each ASIC / engine power ball |
| 4.2.13 | Reference clock generator        | `LR-CLK-A0`       | Renesas 9SQ440 + Si5345B                                 | 1   | Full clock tree for ASIC SerDes + control plane |
| 4.2.14 | I²C / PMBus mux                  | —                 | NXP PCA9548APW                                           | 4   | Telemetry fan-out to BMC |
| 4.2.15 | Temperature sensors (digital)    | —                 | Maxim MAX6581 + DS75LV                                   | 8   | Distributed PCB temperature monitoring |

### 4.3 PSU and active cooling

| #     | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|-------|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 4.3.1 | PSU module, 3 000 W CRPS, 80+ Titanium | `LR-PSU-3KW-A0` | Acbel R3K-2N20 / LiteOn PS-3501-1A                     | 2   | Hot-swappable, redundant 1 + 1; PMBus telemetry |
| 4.3.2 | PSU bay (CRPS-1U)                 | `LR-PSU-BAY-A0`   | TE 2271716-1                                             | 2   | 1U CRPS receptacle with blind-mate 12 V + signal |
| 4.3.3 | AC inlet (C20)                    | —                 | Schaffner FN9244-16-06                                   | 2   | Filtered C20 inlet at chassis rear |
| 4.3.4 | Fan tray module (hot-swappable)   | `LR-FAN-TRAY-A0`  | Custom carrier                                           | 7   | Each carries 1 × dual-rotor 40 × 56 mm fan |
| 4.3.5 | Counter-rotating fan (40 × 56 mm) | —                 | Sanyo Denki 9HV0412P3K001                                | 7   | 38 000 RPM, PWM controlled, 80 CFM each |
| 4.3.6 | Fan controller IC                 | —                 | Microchip EMC2305                                        | 2   | I²C PWM/tach for 7 fans (4 + 3 split) |

**Section 4 unit count:** 32 line items, ≈ 1 800 individual parts (decap-dominated).

---

## 5. Chassis hardware

| #   | Item                              | LR P/N            | Manufacturer / MPN (recommended)                       | Qty | Notes |
|-----|-----------------------------------|-------------------|--------------------------------------------------------|-----|-------|
| 5.1 | Outer chassis (1U, CRS 1.0 mm)    | `LR-CHA-S1A-A0`   | Custom sheet-metal (LR drawing)                         | 1   | 19″ EIA, 1U (44 mm), 800 mm depth; black-zinc finish |
| 5.2 | Top cover                         | `LR-COV-S1A-A0`   | Custom (CRS 1.0 mm)                                     | 1   | Quick-release with captive M3 thumb-screws |
| 5.3 | Inner mounting tray               | `LR-TRAY-S1A-A0`  | Custom (CRS 1.5 mm)                                     | 1   | Receives main PCB + daughterboard standoffs |
| 5.4 | Brass standoff, M3 × 8 mm         | —                 | Keystone 24441                                          | 18  | PCB → tray (main + daughterboard) |
| 5.5 | Mounting screw, M3 × 5 mm         | —                 | Bossard 1413137                                         | 36  | PCB to standoff |
| 5.6 | Rack-ear bracket (× 2)            | `LR-EAR-S1A-A0`   | Custom (Al 6061, anodised black)                        | 2   | EIA 19″ ears with cage-nut holes; integral pull handle |
| 5.7 | Cage nut, 10-32 / M6              | —                 | Penn Engineering CCS-632-2                              | 8   | Rack mounting (front + rear) |
| 5.8 | Inner rail kit (sliding)          | `LR-RAIL-S1A-A0`  | King Slide CL-Q60-1A                                    | 1   | 1-pair 22″–32″ telescoping rails |
| 5.9 | EMI gasket — top cover perimeter  | `LR-EMI-COV-A0`   | Laird 4011                                              | 2 m   | Be-Cu finger-stock around cover seam |
| 5.10 | Air-shroud, ASIC quadrant         | `LR-SHRD-ASIC-A0` | Custom (PC, flame-retardant)                            | 1   | Directs fan-tray airflow over CPO ring |
| 5.11 | Air-shroud, optics quadrant       | `LR-SHRD-OPT-A0`  | Custom (PC, flame-retardant)                            | 1   | Front-panel cage cooling shroud |
| 5.12 | Vibration-isolation grommet       | —                 | Sorbothane 30-DURO 0.5″                                 | 8   | PSU bay + fan tray vibration isolation |
| 5.13 | Serial-number / MAC label         | `LR-LBL-SN-A0`    | Brady B-7593                                            | 1   | Tamper-evident, polyimide |
| 5.14 | Compliance label (FCC / CE / UKCA) | `LR-LBL-CMP-A0`  | Brady B-422                                             | 1   | Regulatory marks per region |
| 5.15 | Anti-static shipping bag          | —                 | 3M 2110                                                 | 1   | ESD pink-poly with desiccant; ships with unit |
| 5.16 | Foam shipping insert              | `LR-PKG-FOAM-A0`  | Custom (PE foam)                                        | 1   | 38 kg/m³ closed-cell foam, formed insert |
| 5.17 | Outer shipping carton             | `LR-PKG-BOX-A0`   | Custom (5-ply RSC corrugated)                           | 1   | Double-wall RSC; ISTA-3A drop-rated |

**Section 5 unit count:** 17 line items, ≈ 110 individual parts.

---

## 6. Roll-up summary

| Section | Description                                | Distinct line items | Total parts (approx.) |
|---------|--------------------------------------------|--------------------:|----------------------:|
| 1       | Core processing & optical subsystem (CPO)  |                  17 |                  ~100 |
| 2       | Optical routing & cable management         |                  10 |                  ~200 |
| 3       | Front-panel interfaces (I/O & lasers)      |                  14 |                  ~110 |
| 4       | Secondary circuitry & power delivery       |                  32 |                ~1 800 |
| 5       | Chassis hardware                           |                  17 |                  ~110 |
| **Total** |                                          |              **90** |              **~2 320** |

### 6.1 Vendor short-list (recommended)


- **PCB fab:** Sierra Circuits, NCAB Group, AT&S
- **Assembly (EMS):** Sanmina, Foxconn Networking, Celestica
- **Optical / fibre assembly:** SENKO, US Conec, Furukawa
- **Liquid cooling:** Asetek, CoolIT, Boyd
- **PSU:** Acbel, LiteOn, Delta Electronics
- **Sheet-metal chassis:** Mason, Boyd, Hsiang Neng

### 6.2 Standards & compliance

- **PCB:** IPC-6012 Class 3, IPC-2221, IPC-2581 Rev C
- **Assembly:** IPC-A-610 Class 3, J-STD-001 Class 3
- **Safety:** UL/IEC 62368-1 (ITE), CB Scheme
- **EMC:** FCC Part 15 Class A, EN 55032 Class A, EN 55035
- **Optical safety:** IEC 60825-1 Class 1
- **Environmental:** RoHS 3 (EU 2015/863), REACH, WEEE
- **Network:** IEEE 802.3 (Ethernet); OSFP-XD MSA; CMIS 5.x management

### 6.3 Spend distribution (architectural — engineering estimate)

| Section / sub-system              | % of unit BOM cost (target) |
|-----------------------------------|----------------------------:|
| Switch ASIC + interposer          | ≈ 35 % |
| CPO optical engines (16×)         | ≈ 25 % |
| ELSFP CW laser modules (8×)       | ≈ 10 % |
| PSU + cooling + chassis           | ≈ 12 % |
| Daughterboard + BMC + control     | ≈ 6 %  |
| PDN (VRM + DrMOS + decap)         | ≈ 5 %  |
| Optical routing (SENKO + ribbon)  | ≈ 4 %  |
| Connectors + cages + misc         | ≈ 3 %  |

---

## 7. Document control

| Field | Value |
|---|---|
| Document type | Architectural BOM (system level) |
| Status | Released — sourcing-quote and investor data-room |
| Designer of Record | LightRail AI |
| Approver | LightRail AI Hardware Engineering (VP) |
| Date | 2026-04-19 |
| Linked CSV | `fab/LR-S1A_CPO_Switch_BOM.csv` |

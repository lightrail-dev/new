# LightRail × ElemRV ASIC Integration — Tapeout Runbook

## Overview

| Layer | Tool chain | Output |
|-------|-----------|--------|
| PCB (32-layer HDI) | KiCad 8.0 → `fab/export_gerbers.sh` | Gerbers, drill files |
| ASIC (ElemRV-N SoC) | SpinalHDL → Yosys → OpenROAD → KLayout | GDS, LEF, DRC report |
| Handoff point | BGA-2500 footprint (`LightRail.pretty/`) | Ball map + I/O TCL |

## Prerequisites

| Tool | Version / Notes |
|------|----------------|
| Python 3.10+ | for venv + podman-compose |
| Podman | container runtime (replaces Docker in ElemRV) |
| `task` (Taskfile) | `go install github.com/go-task/task/v3/cmd/task@latest` |
| KiCad 8.0 | for PCB Gerber export |
| `kicad-cli` | bundled with KiCad 8.0 install |
| `repo` tool | fetched automatically by `setup.sh` |

## Step-by-Step

### 1. Recover LightRail PCB files
```bash
bash scripts/recover_lightrail_pcb.sh
```
This pulls KiCad and supporting files out of local git history into `lightrail-pcb/`.

### 2. Bootstrap ElemRV
```bash
bash setup.sh
```
Clones ElemRV, syncs all submodules at `tapeout-ihp-sg13cmos-2026-03-r1`, pulls Podman container.

**Dependency tree (from manifest):**
```
ElemRV
├── modules/elements/nafarr      @ tapeout-ihp-sg13cmos-2026-03-r1
├── modules/elements/zibal       @ tapeout-ihp-sg13cmos-2026-03-r1  ← Taskfile source
├── modules/elements/vexriscv    @ tapeout-ihp-sg13cmos-2026-03-r1
├── modules/elements/SpinalCrypto @ f2a4ae9
├── tools/OpenROAD-flow-scripts  @ tapeout-ihp-sg13cmos-2026-03-r1
└── pdks/IHP-Open-PDK            @ tapeout-ihp-sg13cmos-2026-03-r1
```

### 3. Run RTL-to-GDSII
```bash
bash scripts/run_flow.sh
```
Equivalent to ElemRV's `task default` but injects LightRail BGA-2500 I/O constraints before P&R:

```
task prepare   → RTL generation (SpinalHDL/Scala → Verilog) + bondpad macro copy
task layout    → Yosys synthesis + OpenROAD place-and-route → DEF
task filler    → filler cell insertion
task run-drc   → KLayout DRC against IHP SG13G2 full deck
```

Container environment variables set automatically:
- `SOC=ElemRV-N`
- `PDK=ihp-sg13g2`
- `TECH=sg13g2`
- `PDK_ROOT=./pdks`
- `BUILD_ROOT=./build/`
- `KLAYOUT_HOME=./pdks/IHP-Open-PDK/ihp-sg13g2/libs.tech/klayout/`

### 4. Inspect outputs
```bash
# View final GDS in KLayout
cd ElemRV && task view-klayout

# View P&R result in OpenROAD GUI
task view-openroad

# View DRC results
task view-drc
```

### 5. Generate combined fab package
```bash
bash scripts/gen_fab_package.sh
```
Produces `fab-package-YYYYMMDD/` with:
```
fab-package-20260617/
├── MANIFEST.txt
├── asic/
│   ├── ElemRV-N.gds          ← submit to IHP
│   ├── ElemRV-N.lef          ← PCB co-design abstract
│   ├── ElemRV-N_drc.lyrdb    ← KLayout DRC database
│   └── ElemRV-N_drc.log
├── pcb/
│   ├── LightRail-F.Cu.gbr … ← submit to PCB fab (Rogers 4350B)
│   └── LightRail.drl
└── docs/
    └── bga2500_pinout_crossref.txt
```

## I/O Constraint Summary (`constraints/lightrail_bga2500_io.tcl`)

| Signal group | BGA edge | Count | Interface |
|---|---|---|---|
| Clock (diff) | North-NW | 2 | 100 MHz PCIe refclk |
| PCIe x16 SerDes | North | 64 | Gen5, 32 GT/s per lane |
| JTAG | South | 4 | Boundary scan (TFLN interposer) |
| UART | South | 2 | Zephyr console |
| SPI0 | West | 4 | TFLN modulator control |
| SPI1 | West | 3 | DFB laser bias DAC |
| I2C0 | West | 2 | Memristive grid telemetry |
| GPIO | West | 8 | Ternary encoder (−1/0/+1) |
| HBM4 sideband | East | 4 | PHY control |

## Known Issues / Watchpoints

- **`modules/elements/zibal/Taskfile.yaml`** is the actual implementation of `lib-layout` etc. — it is in the `zibal` submodule, not the ElemRV root. `repo sync` fetches it at the pinned tag; inspect at `ElemRV/modules/elements/zibal/Taskfile.yaml` after setup.
- **BGA-2500 footprint** is a custom KiCad footprint in `LightRail.pretty/`. The `LEF` abstract produced by `task layout` must be compared against this footprint's copper pad locations to verify ball assignment.
- **Ternary logic** (`LR-TRIT-ENC`, LightRail BOM L9) is handled by the GPIO bank — RISC-V core outputs `gpio[0..7]`; the ternary encoder IC converts to −1/0/+1 off-chip.
- **TFLN interposer** (LR-TFLN-800G) connects to SPI0 and JTAG; the ElemRV SoC acts as the controller; the interposer itself is a passive optical component on the PCB.
- **DRC level**: default is the full IHP deck. Use `task run-drc level=minimal` for a fast sanity check during development.

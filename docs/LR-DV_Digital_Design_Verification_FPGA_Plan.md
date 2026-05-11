# LR-DV — Digital Design, Verification, and FPGA Prototyping Plan

**Project:**  LR-DV — applied across LightRail AI silicon (LR-CSW-51T2 1U CPO switch ASIC + LR-NCE compute ASIC + LR-CPO-3T2 D2D bridge)
**Revision:** A0
**Status:** Released — for investor data-room inclusion and Questa / Vivado tool-licensing scoping
**Date:** 2026-04-19
**Owner:** LightRail AI — Hardware Engineering (Digital Design & Verification)

---

## 0. Reading guide

This document is the single applied plan that connects the digital-design,
verification, low-power, sign-off, and FPGA-prototyping disciplines to the
LightRail AI silicon stack. It covers each of the nine disciplines requested:

| §  | Discipline                                                                      |
|----|---------------------------------------------------------------------------------|
| 1  | Digital / RTL architecture                                                     |
| 2  | Verilog HDL and synthesis constructs                                            |
| 3  | Simulation using QuestaSim                                                     |
| 4  | Static Timing Analysis (STA) and Clock Domain Crossing (CDC)                   |
| 5  | Formal verification using Questa Lint, Questa CDC, and Questa RDC              |
| 6  | Low-power design fundamentals                                                  |
| 7  | FPGA architecture and design flow                                              |
| 8  | Vivado flow, IP catalog, and debug cores                                       |
| 9  | FPGA prototyping and partitioning — challenges specific to this design        |

Each section opens with the discipline applied to LightRail silicon, followed by
the concrete tool flow, sign-off gate, and (where useful) representative code,
SDC, UPF, or TCL excerpts.

The three silicon targets in scope are:

| Target            | Process | Function                                                                                  |
|-------------------|---------|-------------------------------------------------------------------------------------------|
| **LR-CSW-51T2-A0** | TSMC N7 | 1U CPO switch ASIC — 256 × 200 G PAM4 SerDes, packet processor, traffic manager, telemetry |
| **LR-NCE-A0**       | TSMC N5 | Neural Compute Engine — dual SoC w/ HBM4 controller, NoC, tensor cores, PCIe Gen 6        |
| **LR-D2D-S1A-A0**   | TSMC N7 | UCIe 1.1 die-to-die bridge between the switch ASIC and each CPO optical engine            |

---

## 1. Digital / RTL architecture

### 1.1 Top-level hierarchy — LR-CSW-51T2 (switch ASIC)

```
LR_CSW_TOP
├── RX_PIPE_x256        # 256 lanes × 200 G PAM4 (SerDes RX MAC + PCS + FEC)
├── INGRESS_PARSER_x32  # 32 packet processors @ 1.6 Tbps each
├── TRAFFIC_MANAGER     # Buffer, queueing, scheduling (VOQ / iSLIP)
├── EGRESS_PIPE_x32     # 32 egress processors (rewrite, shaping, telemetry)
├── TX_PIPE_x256        # 256 lanes × 200 G PAM4 (SerDes TX MAC + PCS + FEC)
├── D2D_BRIDGE_x16      # 16 UCIe-1.1 die-to-die ports → CPO engines
├── HBM_CTL_x4          # 4 × HBM3e controllers (packet-buffer DDR)
├── CTRL_RV64_CLUSTER   # Dual-RV64GC control-plane (Linux + bare-metal)
├── PCIE_GEN6_x16       # Host-side PCIe Gen 6 root complex
├── TELEMETRY_AGENT     # Streaming telemetry (INT, NetFlow, gRPC)
└── BMC_IF              # I²C + JTAG + UART to AST2600 BMC
```

### 1.2 Top-level hierarchy — LR-NCE (compute ASIC)

```
LR_NCE_TOP
├── HBM4_CTL_x4         # 4 × HBM4 PHY + controller (2048-bit interposer-side bus)
├── TENSOR_CLUSTER_x8   # 8 NoC-attached tensor cores (BF16 / FP8 / INT8)
├── NOC_MESH_8x8        # 8 × 8 mesh-NoC (256-bit AXI4-style links)
├── CPO_PCS_x4          # 4 × photonic-MAC + PCS to TFLN PIC (TFLN-aware FEC)
├── PCIE_GEN6_x16       # Host PCIe (cluster-attach to LR-CSW root complex)
├── CTRL_RV64           # RV64GC control-plane (firmware loader, telemetry)
└── BMC_IF              # I²C + JTAG + UART
```

### 1.3 Clock domains

| Domain        | Frequency  | Used by                                                       | Source                   |
|---------------|-----------:|---------------------------------------------------------------|--------------------------|
| `clk_serdes`  | 25.0 GHz   | SerDes RX/TX (200 G PAM4)                                     | On-die LC-PLL × 16        |
| `clk_pcs`     | 1.5625 GHz | PCS / FEC pipelines                                           | Divider from `clk_serdes` |
| `clk_pipe`    | 1.0  GHz   | Packet pipeline, parser, traffic manager                      | Core PLL                 |
| `clk_noc`     | 1.2  GHz   | NoC mesh (NCE only)                                           | Core PLL                 |
| `clk_hbm`     | 3.2  GHz   | HBM4 / HBM3e controllers                                      | HBM PHY PLL              |
| `clk_d2d`     | 16  GHz    | UCIe-1.1 die-to-die PHY                                       | D2D PLL                  |
| `clk_pcie`    | 2.0  GHz   | PCIe Gen 6 controller                                         | PCIe PHY PLL             |
| `clk_apb`     | 200 MHz    | Control / configuration register block                        | Core PLL                 |
| `clk_ref`     | 156.25 MHz | External reference (jitter-cleaned)                           | External XO              |
| `clk_jtag`    | 50  MHz    | JTAG TAP                                                      | External TCK             |

**Async clock groups** (declared `set_clock_groups -asynchronous`):
`{serdes pcs}`, `{pipe noc}`, `{hbm}`, `{d2d}`, `{pcie}`, `{apb ref}`, `{jtag}`.

### 1.4 Reset strategy

- **Power-on reset (POR_n):** chip-level, async-assert, sync-deassert per
  domain via a two-stage `RESET_SYNC` macro (see §2.4).
- **Soft reset (SWRST_n):** APB-writable, replicated per major block.
- **Functional resets:** per-PIPE, per-HBM, per-NoC-tile, retained across
  power-domain partial-shutdowns (see §6 UPF).
- **Reset-Domain Crossings:** every reset-domain boundary is enumerated and
  signed off in Questa RDC (see §5.3).

### 1.5 Power domains

| Power domain | Voltage    | Function                                          | Strategy                       |
|--------------|-----------:|---------------------------------------------------|--------------------------------|
| `PD_TOP`     | 0.85 V (AVS)| Logic, packet pipeline, NoC                       | Always-on, AVS via PMBus       |
| `PD_SERDES`  | 0.85 V / 1.2 V| SerDes core + bias                              | Always-on (gated per lane group) |
| `PD_HBM`     | 1.1 V      | HBM controller + PHY                              | Always-on                      |
| `PD_D2D`     | 0.85 V     | UCIe die-to-die                                   | Per-port retention             |
| `PD_PCIE`    | 0.85 V / 1.8 V| PCIe controller + PHY                           | L1.2 deep-sleep capable        |
| `PD_CTRL`    | 0.85 V     | RV64 control-plane cluster                        | Idle clock-gating              |

### 1.6 Gate-count estimate (post-synth, pre-place)

| Block                      | Approx. inst count | Comment                              |
|----------------------------|-------------------:|---------------------------------------|
| LR-CSW packet pipeline (32×)|         48 M       | Parser + TM + scheduler + rewrite     |
| LR-CSW SerDes MACs (256×)  |         12 M       | PCS + FEC + lane mgmt                 |
| LR-CSW HBM3e CTL (4×)      |          8 M       | Controller + scheduler + ECC          |
| LR-CSW D2D / UCIe (16×)    |          2 M       | LL + PCS                              |
| LR-CSW total               |     **~ 72 M**     |                                       |
| LR-NCE tensor cluster (8×) |         96 M       | MAC arrays + scratchpad ctrl          |
| LR-NCE NoC + HBM + CPO_PCS |         18 M       |                                       |
| LR-NCE total               |     **~ 116 M**    |                                       |

### 1.7 RTL coding standards

- **Language:** SystemVerilog IEEE 1800-2017 (synthesisable subset for design;
  full standard for testbench).
- **Naming:** snake_case modules + signals, `_n` async-active-low, `_q`
  registered, `_d` next-state, `_r` read-data, `_w` write-data.
- **No latches** in design RTL (Questa Lint `LATCH-INFER` is signoff-blocking).
- **No `assign` of clocks**, no logic on a clock, no logic on a reset other
  than through `RESET_SYNC` macros.
- **Synchronous design** within a single domain; all crossings via §4.3 macros.
- **Parameterised packs** in `lr_pkg.sv`; opaque types via interfaces (see §2.3).

---

## 2. Verilog HDL and synthesis constructs

### 2.1 Synthesisable subset (the rule)

| Used                                                  | Not used                              |
|-------------------------------------------------------|---------------------------------------|
| `module`, `interface`, `package`, `function`, `task` (auto)| `initial` blocks in design RTL      |
| `always_ff`, `always_comb`, `always_latch` (never)    | `force` / `release`                   |
| `logic` (single-driver), `bit`, `enum`, packed `struct`| `wire`/`reg` legacy types            |
| `generate` / `endgenerate`, `for`                     | `realtime`, `time`, `event` in design |
| `unique`/`unique0`/`priority` case                    | `casex`                               |
| `$signed` / `$unsigned`, `$clog2`                     | `assign #delay`, intra-assignment `#` |
| Interfaces with **synth-time** `modport`              | Interfaces with dynamic class members |

### 2.2 Reference register-bank pattern

```systemverilog
// File: lr_reg_bank.sv (used in all APB-mapped configuration blocks)
module lr_reg_bank #(
    parameter int unsigned ADDR_W = 12,
    parameter int unsigned DATA_W = 32,
    parameter int unsigned N_REGS = 64
) (
    input  logic                          clk,
    input  logic                          rst_n,
    // APB slave
    input  logic                          psel,
    input  logic                          penable,
    input  logic                          pwrite,
    input  logic [ADDR_W-1:0]             paddr,
    input  logic [DATA_W-1:0]             pwdata,
    output logic [DATA_W-1:0]             prdata,
    output logic                          pready,
    output logic                          pslverr,
    // CSR fan-out
    output logic [N_REGS-1:0][DATA_W-1:0] csr_q,
    input  logic [N_REGS-1:0][DATA_W-1:0] hw_d,
    input  logic [N_REGS-1:0]             hw_we
);
    // ... synthesis-friendly write/read decoder + hardware-priority MUX
endmodule
```

### 2.3 Interface for opaque AXI4 attach (synthesisable)

```systemverilog
interface axi4_if #(int AW = 64, int DW = 256, int IDW = 8);
    logic [AW-1:0] awaddr;  logic [IDW-1:0] awid;  logic awvalid; logic awready;
    logic [DW-1:0] wdata;   logic [DW/8-1:0] wstrb; logic wlast;   logic wvalid; logic wready;
    logic [IDW-1:0] bid;    logic [1:0]      bresp; logic         bvalid; logic bready;
    logic [AW-1:0] araddr;  logic [IDW-1:0] arid;  logic arvalid; logic arready;
    logic [DW-1:0] rdata;   logic [IDW-1:0] rid;   logic [1:0]    rresp; logic rlast; logic rvalid; logic rready;
    modport mst (output awaddr, awid, awvalid, wdata, wstrb, wlast, wvalid, bready,
                 input  awready, wready, bid, bresp, bvalid /* ...read side... */);
    modport slv (input  awaddr, awid, awvalid, wdata, wstrb, wlast, wvalid, bready,
                 output awready, wready, bid, bresp, bvalid /* ...read side... */);
endinterface
```

### 2.4 Reset synchroniser (used everywhere a reset crosses a domain)

```systemverilog
module lr_reset_sync (
    input  logic clk,
    input  logic rst_n_async,
    output logic rst_n_sync
);
    logic q1, q2;
    always_ff @(posedge clk or negedge rst_n_async) begin
        if (!rst_n_async) {q2, q1} <= '0;
        else              {q2, q1} <= {q1, 1'b1};
    end
    assign rst_n_sync = q2;
endmodule
```

### 2.5 Synthesis constructs we **use**

- **Clock-gating cells:** integrated clock-gates (ICG) inferred from
  `always_ff @(posedge clk) if (en) q <= d;` and from `// pragma gated_clock`
  in critical paths. Verified that the lib has `CKLNQD*` (Latch-then-AND) ICG.
- **Retention flops:** `RFLNQD*` cells in `PD_D2D` for context retention.
- **Memory inferences:** small inferred SRAMs (≤ 1 kbit) only; larger arrays
  via Synopsys / Cadence memory-compiler GUI-generated `.lib` + `.lef`.
- **Multi-Vt:** `LVT` for ≤ 8% of cells (timing-critical FEC, retimers), `RVT`
  default, `HVT` for control / housekeeping (leakage-dominant).
- **Don't-touch nets:** clock-tree, scan-chain, JTAG TAP, BIST.
- **`set_dont_touch`** on `lr_reset_sync` and CDC synchroniser cells.

### 2.6 Synthesis constructs we **do not use**

- Combinational loops, latches (with one exception: tag-cam compare in §4.4
  is a deliberate latch + Lint waiver).
- `initial` in synthesis source.
- Behavioural divide (`/`) outside a `generate` pragma-replaced wrapper.

---

## 3. Simulation using QuestaSim

### 3.1 Testbench architecture

UVM 1.2-based testbench for every block + chip-level. Hierarchy mirrors the
RTL: each top has an `lr_<block>_env` extending `uvm_env` with one or more
agents (active/passive), a scoreboard, reference model, coverage collector,
and a `uvm_report_server` filter.

```
lr_csw_test
└── lr_csw_env
    ├── axi_agent_apb       # APB master for CSR pokes
    ├── pkt_agent_x32        # 32 packet ingress/egress agents
    ├── pkt_ref_model        # SystemC golden traffic-manager model
    ├── coverage_collector   # functional / fsm / toggle / cdc
    └── scoreboard
```

### 3.2 Compile / run flow

```bash
# tools/sim/Makefile  (excerpt)
QUESTA  ?= /opt/questasim/2024.1/linux_x86_64
VLOG     = $(QUESTA)/bin/vlog -sv -mfcu -cuname lr_top  -timescale 1ps/1ps
VOPT     = $(QUESTA)/bin/vopt -64 +acc=npr -designfile lr_top.bin
VSIM     = $(QUESTA)/bin/vsim -64 -c -do "run -all; quit -f"
COV      = +cover=bcefst   # block, branch, expression, fsm, statement, toggle

compile:
	$(VLOG) -f filelists/lr_pkg.f
	$(VLOG) -f filelists/lr_csw_rtl.f -L lr_pkg
	$(VLOG) -f filelists/lr_csw_uvm.f -L lr_pkg -L uvm
optimize:
	$(VOPT) lr_csw_tb $(COV) -o lr_csw_tb_opt
run-sanity:
	$(VSIM) -do "vsim -coverage lr_csw_tb_opt; \
	            run -all; \
	            coverage save sim.ucdb"
regress:
	tools/sim/run_regress.py --campaign nightly --jobs 256
```

### 3.3 Coverage strategy

| Coverage type        | Goal      | Tool                  |
|----------------------|----------:|-----------------------|
| Line / statement     | 100 %     | QuestaSim built-in    |
| Branch / expression  | 100 %     | QuestaSim built-in    |
| FSM (state + trans)  | 100 %     | QuestaSim built-in    |
| Toggle (top + ports) | 100 %     | QuestaSim built-in    |
| Functional (cover groups) | 100 % per spec | UVM coverage |
| Assertion (concurrent SVA) | 100 % witness covered | QuestaSim SVA |

Sign-off gate: a single `merge.ucdb` from the nightly campaign must report
≥ 99.5 % overall (regulator IP exemption), with **no zero-hit functional
bins**.

### 3.4 Regression infrastructure

- 256-core LSF / Slurm farm, ~ 4 000 jobs / night across the chip.
- Seed list: `tools/sim/seeds/<block>_release.csv` regenerated nightly.
- Triage dashboards: `lr_sim_dashboard` (Streamlit) ingesting `.ucdb` →
  Postgres → Grafana panel for trend.
- Auto-bisect on new RTL push: if a previously passing seed fails, the CI
  bot bisects against the last 24 h commits and pings the author.

### 3.5 Assertion library

`tools/sva/lr_sva_pkg.sv` ships a curated library of concurrent SVA macros
used pervasively:
- `LR_ASSERT_ONEHOT`, `LR_ASSERT_HANDSHAKE_OK`, `LR_ASSERT_CDC_STABLE`,
  `LR_ASSERT_NO_X_PROP`, `LR_ASSERT_RESET_PROP`, `LR_ASSERT_FIFO_NO_OVF`,
  `LR_ASSERT_AXI4_LITE`, `LR_ASSERT_UCIE_ALIGN`.

---

## 4. Static Timing Analysis (STA) and Clock Domain Crossing (CDC)

### 4.1 STA tooling

| Stage       | Tool                       | Mode                                      |
|-------------|----------------------------|-------------------------------------------|
| RTL → synth | Synopsys Design Compiler   | MMMC, set_app_var derate                  |
| P&R         | Cadence Innovus            | CCOPT clock tree, ECO loop                |
| Sign-off    | Synopsys PrimeTime + PT-SI | MMMC, OCV (POCV at 7 nm), AOCV, derate    |
| Cross-check | Cadence Tempus             | Independent re-confirmation of PT corners |

### 4.2 Corner / mode matrix (LR-CSW example)

| Mode      | PVT corner       | OCV derate (clk / data) | Margin                |
|-----------|------------------|-------------------------:|-----------------------|
| Func setup | SS / 0.765 V / 125 °C | +3 % / +5 %              | 50 ps setup, 50 ps hold |
| Func hold  | FF / 0.935 V / -40 °C | -3 % / -5 %              |                       |
| Scan       | TT / 0.85 V / 25 °C    | ±2 %                       | Loose (capture only)  |
| AVS-low    | TT / 0.80 V / 25 °C    | +3 % / +5 %              | Tight setup           |

### 4.3 SDC excerpt — clocks, groups, false paths

```tcl
# Primary clock definitions (clk_ref via external XO)
create_clock -name clk_ref       -period 6.400  [get_ports clk_ref_p]
create_generated_clock -name clk_serdes -source [get_ports clk_ref_p] \
       -multiply_by 160 [get_pins u_pll_serdes/out]
create_generated_clock -name clk_pipe   -source [get_pins u_pll_core/out] \
       -divide_by 1 [get_pins u_pll_core/out]

# Async groups (no STA across these)
set_clock_groups -asynchronous \
    -group {clk_serdes clk_pcs} \
    -group {clk_pipe   clk_noc} \
    -group {clk_hbm} \
    -group {clk_d2d}  \
    -group {clk_pcie} \
    -group {clk_apb clk_ref} \
    -group {clk_jtag}

# Reset trees — propagated as false paths after the synchroniser
set_false_path -through [get_pins u_*/lr_reset_sync_i/rst_n_async]

# Multicycle on register-bank read MUX (deliberate, 2-cycle)
set_multicycle_path 2 -setup -from [get_pins u_reg_bank/*/Q] -to [get_pins u_csr_mux/D]
set_multicycle_path 1 -hold  -from [get_pins u_reg_bank/*/Q] -to [get_pins u_csr_mux/D]

# Input / output delays for SerDes and HBM PHY interfaces
set_input_delay  -clock clk_pcs  -max 0.40 [get_ports {rx_data_p[*] rx_data_n[*]}]
set_output_delay -clock clk_pcs  -max 0.40 [get_ports {tx_data_p[*] tx_data_n[*]}]
```

### 4.4 CDC inventory (LR-CSW abridged)

| # | From → To             | Type           | Synchroniser          | Sign-off |
|---|-----------------------|----------------|-----------------------|----------|
| 1 | `clk_apb → clk_pipe`  | Single-bit ctrl | 2-FF MUX-recirc        | OK |
| 2 | `clk_pipe → clk_pcs`  | Bus 64-bit      | Gray-coded async FIFO  | OK |
| 3 | `clk_pcs  → clk_pipe` | Bus 64-bit      | Async FIFO + status    | OK |
| 4 | `clk_apb  → clk_hbm`  | Bus 32-bit      | Req/Ack 4-phase        | OK |
| 5 | `clk_hbm  → clk_pipe` | Bus 256-bit     | Async FIFO + ECC       | OK |
| 6 | `clk_d2d  → clk_pipe` | Bus 256-bit     | Async FIFO             | OK |
| 7 | `clk_jtag → clk_apb`  | Single-bit ctrl | 2-FF                   | OK |

All synchroniser macros come from `lr_cdc_lib.sv` (24 macros). No CDC outside
this library is permitted; Questa CDC enforces it (see §5.2).

---

## 5. Formal verification — Questa Lint, Questa CDC, and Questa RDC

### 5.1 Questa Lint — sign-off ruleset

- **Methodology:** `mentor_lp_methodology` + `lr_methodology` (custom
  rulebook). 142 rules enabled, 18 escalated to **Error** (sign-off-blocking),
  the rest **Warning** (waivable with engineering justification in
  `tools/lint/waivers/`).

```tcl
# tools/lint/lr_lint.do
do tools/lint/load_methodology.tcl
analyze -f filelists/lr_csw_rtl.f -L lr_pkg
report top -name lr_csw_top -options "lr_csw_rules.json"
configure waiver -file tools/lint/waivers/lr_csw.waiver
check  -mode full
report check     -file reports/lr_csw_lint.rpt
report violations -file reports/lr_csw_lint_viols.csv -severity error,warning
sign-off -check zero_errors -waivers required
```

| Rule category               | Promoted to **Error** |
|-----------------------------|-----------------------|
| Latch inference             | yes (Q-LATCH-IF)      |
| Multi-driver net            | yes (Q-MULTI-DR)      |
| Sensitivity-list mismatch   | yes (Q-SENS-LIST)     |
| Combo loop                  | yes (Q-COMBO-LOOP)    |
| `casez`/`casex` overlap     | yes (Q-CASEX-OVRLP)   |
| Width mismatch              | yes (Q-WIDTH-MM)      |
| Initial in design           | yes (Q-INIT-SYN)      |
| `assign` on clock           | yes (Q-CLK-ASSIGN)    |
| `assign` on reset           | yes (Q-RST-ASSIGN)    |
| Inferred memory > 1 kbit    | yes (Q-MEM-INFER)     |
| Unused signal               | warning (waiver req'd) |

### 5.2 Questa CDC — sign-off methodology

- **Stage 1 — Structural:** identify every clock-domain crossing. Goal: every
  path categorised as **Sync** (intentional, has a synchroniser) or
  **Async** (illegal, must be fixed).
- **Stage 2 — Functional:** for each synchroniser, verify functional
  correctness of the protocol (Gray-code monotonicity for async-FIFO pointers,
  REQ/ACK handshake invariants, MUX-recirc stable-enable invariants).
- **Stage 3 — Metastability injection:** `cdc inject` runs in simulation to
  emit randomised metastability into each Sync path; the UVM scoreboard must
  remain consistent across `N=1 000` randomised metastability windows.

```tcl
# tools/cdc/lr_cdc.do
cdc methodology -methodology mentor
cdc compile -f filelists/lr_csw_rtl.f -d lr_csw_top
cdc generate report -directory reports/cdc_csw -all
cdc generate cdc_sva -directory tools/cdc/sva   # emits SVA for sim
sign-off -check {0 violations, 100% protocol coverage}
```

| Sign-off gate                             | Threshold       |
|-------------------------------------------|-----------------|
| Async paths without synchroniser          | **0**           |
| Synchroniser-protocol assertion firings   | **0** (in regression) |
| Metastability-injection failures          | **0**           |
| CDC-related waivers                       | ≤ 5 (each justified in `tools/cdc/waivers/`) |

### 5.3 Questa RDC — reset-domain crossing sign-off

- Every reset is assigned a **reset domain** in `tools/rdc/lr_reset.sgdc`
  (Synchronised-Group Constraint File). Async-assert / sync-deassert
  synchronisers (the `lr_reset_sync` macro) terminate each domain.
- Every flip-flop is then categorised: **source reset domain** (which reset
  controls async-assert) and **destination clock domain**. Any path that
  crosses reset domains without going through a defined "reset-quiescence"
  synchroniser is an RDC violation.

```tcl
# tools/rdc/lr_rdc.do
rdc methodology -methodology mentor
rdc constraints -f tools/rdc/lr_reset.sgdc
rdc compile     -f filelists/lr_csw_rtl.f -d lr_csw_top
rdc check       -mode full
rdc report      -file reports/lr_csw_rdc.rpt
sign-off -check zero_errors
```

| Sign-off gate                                   | Threshold |
|-------------------------------------------------|-----------|
| Unconstrained reset signals                      | **0** |
| RDC violations (Async assert, missing isolation) | **0** |
| Waived RDC violations                            | ≤ 3 (each with engineering note) |

---

## 6. Low-power design fundamentals

### 6.1 Power-intent (UPF excerpt — LR-CSW top)

```tcl
# tools/upf/lr_csw_top.upf
set_design_top lr_csw_top
set_scope      lr_csw_top

# Voltage rails
create_power_domain PD_TOP    -include_scope
create_power_domain PD_SERDES -elements {u_serdes_rx u_serdes_tx}
create_power_domain PD_D2D    -elements {u_d2d_x16}
create_power_domain PD_PCIE   -elements {u_pcie}

create_supply_port  VDD_TOP    -direction in
create_supply_port  VDD_SERDES -direction in
create_supply_port  VDD_D2D    -direction in
create_supply_port  VDD_PCIE   -direction in
create_supply_port  VSS        -direction in

create_supply_net   VDD_TOP    -domain PD_TOP
create_supply_net   VDD_SERDES -domain PD_SERDES
create_supply_net   VDD_D2D    -domain PD_D2D
create_supply_net   VDD_PCIE   -domain PD_PCIE
create_supply_net   VSS        -domain PD_TOP -reuse

# Always-on / switchable power policies
set_domain_supply_net PD_TOP    -primary_power_net VDD_TOP    -primary_ground_net VSS
set_domain_supply_net PD_D2D    -primary_power_net VDD_D2D    -primary_ground_net VSS

# Isolation policy for outputs of switchable PD_D2D
set_isolation       d2d_iso  -domain PD_D2D -applies_to outputs \
                              -clamp_value 0 -isolation_supply VDD_TOP
set_isolation_control d2d_iso -isolation_signal pd_d2d_iso_en  -isolation_sense high

# Retention strategy on PD_D2D registers (UCIe link-state retention)
set_retention   d2d_ret -domain PD_D2D -retention_supply VDD_D2D
set_retention_control d2d_ret -save_signal {pd_d2d_save high} -restore_signal {pd_d2d_restore high}
```

### 6.2 Clock-gating policy

- **RTL-level gating:** `if (en) q <= d;` → ICG inferred.
- **Coarse-grain gating:** per-PIPE clock-gate at the packet pipeline root,
  driven by `tm_busy_q | csr_active_q | pcie_in_flight_q`.
- **Multi-level gating:** SerDes-lane group ICGs gated by link-state
  (per-group) and FEC-busy flag.

Coverage target: ≥ 90% of flip-flops gated when idle (Synopsys Power Compiler
reports this in synthesis).

### 6.3 Multi-Vt / AVS / DVFS

| Technique     | LR-CSW         | LR-NCE         | Notes                                |
|---------------|----------------|----------------|--------------------------------------|
| Multi-Vt mix  | LVT 8% / RVT 78% / HVT 14% | LVT 12% / RVT 75% / HVT 13% | LVT only on timing-critical SerDes/FEC |
| Power gating  | PD_D2D + PD_PCIE | PD_PCIE only | UCIe link-state retention            |
| Clock gating  | Pervasive ICG    | Pervasive ICG  | Multi-level gating in NoC tiles      |
| AVS           | V_ASIC: 0.80 V – 0.95 V via PMBus → MPS MP2965 | same | Driven by on-die thermal + activity counters |
| DVFS          | Discrete: idle / nominal / boost | 3 OPPs | Firmware-managed via BMC             |

### 6.4 Power-estimation sign-off

- **Vector-driven** (Synopsys PrimePower + Cadence Voltus): traffic-pattern
  VCDs from QuestaSim → IR-drop + EM analysis in Voltus → sign-off pack.
- **Targets** (post-place-route, AVS-on, nominal corner):
  - LR-CSW total: ≤ 350 W @ 51.2 Tbps full load
  - LR-NCE total: ≤ 600 W @ tensor-cluster full load

---

## 7. FPGA architecture and design flow

### 7.1 Target platform

| FPGA                          | Vendor | Logic cells | UltraRAM / BRAM | MGTs                 | Use                       |
|-------------------------------|--------|-------------|------------------|----------------------|---------------------------|
| **AMD Versal Premium VP1902**  | AMD    | 18.5 M      | 360 Mb URAM      | 32 × GTM (112 Gbps PAM4) | LR-CSW per-quadrant prototype |
| **AMD Versal Premium VP2802**  | AMD    | 28.4 M      | 480 Mb URAM      | 96 × GTM (112 Gbps PAM4) | LR-CSW full-chip prototype (4-FPGA platform)   |
| **AMD Virtex UltraScale+ VU19P**| AMD   | 9.0 M       | 270 Mb URAM      | 80 × GTY (32 Gbps NRZ) | LR-NCE NoC + tensor-cluster prototype |

Note: 200 G PAM4 SerDes is **not natively available** on any commercial FPGA.
The prototype substitutes 112 G PAM4 GTM channels with a 2:1 SerDes adapter
RTL (we run the design's MAC + PCS at line rate over half the physical lane
count, with a custom DLL phase-aligner). This adaptation is enumerated in §9.

### 7.2 Design flow (block-level)

```
RTL ──► Synthesis (Vivado synth_design) ──► Implementation (place + route)
                                       │
                                       ▼
                          DCP checkpoint (per-stage)
                                       │
                                       ▼
                          Bitstream (.bit + .ltx for ILA)
                                       │
                                       ▼
                          JTAG / SmartLynq + → Versal target
```

### 7.3 Resource-budget targets (LR-CSW per-quadrant on VP1902)

| Resource            | Avail.  | Budget (target) | After synth (estimated) |
|---------------------|--------:|----------------:|------------------------:|
| LUTs                | 18.5 M  |          80 %   |              ~ 14.6 M   |
| BRAM tiles          | 4 080   |          70 %   |              ~ 2 850    |
| URAM blocks         | 480     |          80 %   |              ~ 380      |
| DSP58               | 10 968  |          40 %   |              ~ 4 100    |
| GTM transceivers    | 32      |         100 %   |              32 (16 RX + 16 TX) |
| HBM2e stacks        | 2 × 8 GB |        100 %    |              2          |

---

## 8. Vivado flow, IP catalog, and debug cores

### 8.1 Project vs non-project flow

We use **non-project** (TCL-driven) flow for repeatability and for the
multi-FPGA partition pipeline. A small project-mode flow exists for
exploratory work on the daughterboard prototyping (`lr_dbg_dev.xpr`).

```tcl
# tools/fpga/build_lr_csw_quadrant.tcl
create_project -in_memory -part xcvp1902-vsva3697-2MP-e-S
add_files -fileset sources_1 [glob rtl/**/*.sv rtl/**/*.v]
add_files -fileset constrs_1  constraints/lr_csw_quadrant.xdc
read_ip                       ip/mig_hbm2e.xci  ip/aurora_gtm.xci  ip/jtag_axi.xci

synth_design -top lr_csw_quadrant_top -flatten_hierarchy rebuilt \
             -directive AreaOptimized_high -retiming
write_checkpoint -force build/synth.dcp

opt_design       -directive ExploreWithRemap
place_design     -directive ExtraNetDelay_high
phys_opt_design  -directive AggressiveExplore
route_design     -directive AggressiveExplore
phys_opt_design  -directive AggressiveExplore

report_timing_summary -file reports/timing_summary.rpt
report_utilization     -file reports/utilization.rpt
report_power           -file reports/power.rpt

write_bitstream -force build/lr_csw_quadrant.bit
write_debug_probes -force build/lr_csw_quadrant.ltx
```

### 8.2 IP catalog use (per FPGA)

| IP                                  | Purpose                                              |
|-------------------------------------|------------------------------------------------------|
| `Versal HBM2e MIG`                  | HBM2e controller for packet-buffer emulation         |
| `Versal CPM Gen5/6`                 | PCIe Gen 6 (downgraded to Gen 5 for prototyping)     |
| `Aurora 64B/66B over GTM`           | 112 G PAM4 link primitives, line-rate test framework |
| `AXI Interconnect`                  | NoC mesh emulation interconnect                       |
| `AXI BRAM Controller`               | CSR scratch + boot-ROM emulation                      |
| `JTAG-to-AXI Master`                | Run-time poke/peek into chip-internal CSRs           |
| `DDR4 MIG`                          | Off-chip DDR for trace buffer + HBM emulation back-store |

### 8.3 Debug cores

- **ILA (Integrated Logic Analyzer):** 1 ILA per major block, 4 K-deep,
  16-wide trigger probes. Captures synthesise to BRAM, do not touch URAM
  budget.
- **VIO (Virtual I/O):** for run-time bring-up of CSRs without writing a
  driver.
- **JTAG-to-AXI Master:** full AXI4-Lite master attached to the chip-internal
  APB bridge — same firmware API as on-silicon.
- **MARK_DEBUG attributes:** RTL nets carrying `(* mark_debug = "true" *)`
  are routed to the ILA — kept consistent across runs via
  `constraints/lr_debug.xdc`.
- **SmartLynq+ probe:** physical interface; dual-cable so all 4 FPGAs in
  the platform are accessible from one host.

---

## 9. FPGA prototyping & partitioning — challenges specific to this design

### 9.1 Why prototype at all

We use FPGA prototyping for:
- Pre-silicon software bring-up (Linux on the RV64 control-plane, firmware
  for the BMC, switch OS dataplane software, PCIe driver bring-up).
- Pre-silicon SoC-level integration smoke-tests of the packet pipeline
  end-to-end (parser → TM → scheduler → rewrite) at 1/4 line rate.
- Pre-silicon CPO link bring-up: the photonic engine is replaced by a
  digital model (analogue front-end stub + bit-true PCS + FEC).

### 9.2 Multi-FPGA platform

- **Platform:** S2C Prodigy Logic System Cloud or Synopsys HAPS-100, 8-slot.
- **Partitioning approach:** ProtoCompiler (S2C) or HAPS ProtoCompiler
  (Synopsys) for automated cut-balancing; manual override file
  (`tools/fpga/partition_overrides.tcl`) for cuts we want to enforce.
- **Inter-FPGA interconnect:** TDM-multiplexed at ~4 GHz over 32 × GTY pairs
  per cut; ~ 6 cycles of TDM latency.

### 9.3 Specific challenges (and how we address each)

| # | Challenge                                                                                       | Mitigation in this plan |
|---|-------------------------------------------------------------------------------------------------|--------------------------|
| 1 | **256 × 200 G PAM4 SerDes do not exist on FPGAs.**                                              | Run the design's PCS / FEC at line-rate over **112 G PAM4 GTM** channels; use a 2:1 SerDes-adapter wrapper that synthesises only in FPGA builds (guarded by `\`ifdef LR_FPGA`). Lane count is also halved (128 lanes instead of 256). End-to-end aggregate is 12.8 Tbps on the prototype — sufficient for software bring-up. |
| 2 | **HBM4 is not yet available on commercial FPGA platforms.**                                     | Use the Versal Premium **HBM2e** (16 GB on-package) as a behavioural / functional stand-in. We bind LR-NCE's HBM4 controller to a `mig_hbm2e` shim that translates the AXI4 attach point's commands. Latency and bandwidth are scaled; software does not see this. |
| 3 | **The CPO engine is a TFLN photonic die, not synthesisable.**                                   | Replace with `lr_cpo_digital_model.sv`: bit-true PCS + RS-FEC + a 200 G NRZ-loopback emulating optical link-up, link-loss, BER injection. Real silicon swaps this for the analogue-front-end + TFLN driver. |
| 4 | **UCIe-1.1 die-to-die PHY is not on FPGAs.**                                                    | Use **Aurora-64B/66B over GTM** as a transport substitute; UCIe-LL (link layer) above this is identical RTL to silicon. Software stack sees the same LL frame semantics. |
| 5 | **Capacity overflow:** LR-CSW total ≈ 72 M instances vs ≈ 18 M / FPGA.                          | 4-FPGA partition (LR-CSW): {RX_PIPE + Parser ¼} × 4 → 4 quadrants, each on one VP2802. Centralised TM is replicated 4 × on each FPGA + arbitration cut via TDM. |
| 6 | **Cross-FPGA latency** (TDM mux at 4 GHz adds ~ 6 cycles each way).                              | Inserted `lr_xfpga_buffer.sv` ping-pong FIFOs at every partition boundary; latency budgeted into the prototype-only SDC corner. Real silicon SDC unaffected. |
| 7 | **256-bit AXI4 NoC links between NCE tiles** > LUT routing capacity.                            | Bit-serialise to 32-bit AXI-Stream over 1 cycle of clk_noc_x8 (250 MHz) for cross-FPGA NoC hops only (`\`ifdef LR_FPGA_XHOP`). |
| 8 | **Clock-tree fan-out across FPGAs** (single `clk_pipe` would need 4 × FPGA clock-distribution). | Generate `clk_pipe` independently on each FPGA from a common 156.25 MHz fanout; CDC bridges between quadrants are accepted because the design natively has these CDCs (see §4.4). |
| 9 | **PCIe Gen 6 is not yet on FPGAs** (Versal CPM tops at Gen 5).                                  | Downgrade to PCIe Gen 5 x16 for prototyping (32 GT/s); the design's PIPE-6 interface is downgraded to PIPE-5 by an `ifdef`-guarded wrapper; software stack sees a slower link only. |
|10 | **Debug across 4 FPGAs** — single ILA isn't enough.                                            | 1 ILA per major block per FPGA + cross-FPGA trigger bus over GTY + SmartLynq+ dual cable so Vivado HW Manager sees all 4 simultaneously. |

### 9.4 Sign-off gate for FPGA prototyping milestone

- All 4 FPGAs program (no DRC routing fail; timing closes WNS ≥ 0 at slowest corner).
- LR-CSW prototype passes "1000-packet smoke test" end-to-end at 1/4 line rate.
- LR-NCE prototype boots Linux on the RV64 cluster and the tensor-cluster
  runs a single BF16 GEMM kernel from DRAM.
- All ILA captures decode in Vivado; SmartLynq+ reaches every FPGA from one host.

---

## 10. Sign-off summary (cross-discipline)

| Stage                                | Tool                | Gate                                  | Owner |
|--------------------------------------|---------------------|---------------------------------------|-------|
| RTL freeze                            | git tag + Questa Lint | 0 errors, all waivers justified         | DV Lead |
| QuestaSim regression                  | QuestaSim 2024.1     | ≥ 99.5 % overall coverage, 0 fail seeds | DV Lead |
| Synthesis & STA                       | DC + PrimeTime       | All MMMC corners closed, 0 setup/hold   | Implementation Lead |
| CDC                                  | Questa CDC           | 0 errors; 0 metastability fails         | DV Lead |
| RDC                                  | Questa RDC           | 0 errors                               | DV Lead |
| Low-power equivalence                | Synopsys VC LP       | 0 LEC fails, UPF clean                  | Low-power Lead |
| FPGA prototype                       | Vivado + S2C / HAPS  | 4-FPGA program, smoke + boot tests pass | Proto Lead |
| Production tape-out                  | Innovus + PT + Voltus| All sign-off corners closed; IR / EM clean | Implementation Lead |

---

## 11. Document control

| Field | Value |
|---|---|
| Document type | Applied digital design & verification plan |
| Status | Released — for investor data-room inclusion |
| Designer of Record | LightRail AI — Hardware Engineering (Digital Design & Verification) |
| Approver | LightRail AI Hardware Engineering (VP) |
| Date | 2026-04-19 |
| Linked files | `tools/sim/*`, `tools/lint/*`, `tools/cdc/*`, `tools/rdc/*`, `tools/upf/*`, `tools/fpga/*` |

# Tape-out Sign-off Checklist (LR-P3A Rev 6.0)

Every item must be owned, dated, and signed before Gerbers are released.
Owners are suggested; reassign as needed.

Rev 6.0 target: **32-layer HDI, IPC-6012 Class 3, 1000 A PDN, 1.6 Tbps
TFLN CPO, HBM4 co-packaged on silicon interposer.** ODB++ is the primary
fabrication-transfer format; IPC-2581C and classical Gerber X2 are
redundant back-ups (spec §V).

## 0. Gate review

- [ ] Architecture lead signs off on block-diagram scope (`docs/Architecture.md`)
- [ ] Program manager confirms revision number and release tag

## 1. Schematic — signed by **Schematic lead**

- [ ] All hierarchical sheet-pin ↔ child-label names match (ERC `hierarchical_label_mismatch` = 0)
- [ ] Every IC has: reference designator, value, footprint, datasheet URL,
      manufacturer P/N
- [ ] Every passive has: ref des, value, package, tolerance, voltage rating
- [ ] Every power net annotated with voltage (+12V, +3V3, V_CORE_U0, …)
- [ ] ERC run with **0 errors**; all warnings reviewed and either fixed
      or added to `erc_waivers.md` with justification
- [ ] Annotation complete (no `U?` / `R?` / `C?`)
- [ ] BOM export matches `fab/BOM.csv` ± tracked deltas

## 2. PCB layout — signed by **Layout lead**

- [ ] Stackup reviewed with fab; coupon pitch agreed (`docs/Stackup.md`)
- [ ] Board outline matches mechanical CAD (STEP round-trip verified)
- [ ] Mounting holes placed per chassis spec; tolerances confirmed
- [ ] Component placement review held with mechanical, thermal, RF leads
- [ ] All placed parts have footprints; no `missing_footprint`
- [ ] All nets routed (`unrouted_nets = 0`)
- [ ] Design Rule Check run with **0 errors**; all exclusions in `fab/dfm/drc_exclusions.md`
- [ ] Length-matching complete: HBM4 REFCK pairs, PCIe Gen 6, TFLN RF,
      SerDes 100 G PAM4 — all ≤ 2 ps skew within each group
      (see `docs/DFM_Checklist.md` §7)
- [ ] Back-drill applied on **all** high-speed through-vias
      (SerDes / PCIe / TFLN_RF / TFLN_ELEC_TRANSITION / HBM4_Interposer /
      RF_50OHM_DIFF); residual stub measured ≤ 0.127 mm on coupon
- [ ] Controlled-impedance traces match class targets within ±5 %
      on RF-critical classes (spec §IV), ±10 % on general classes, per
      post-layout SI extraction + fab coupon measurement
- [ ] Every high-speed diff pair has a continuous reference plane with GND
      on both sides (symmetric stripline); no reference-plane transitions
      without return-path stitching vias ≤ 2 mm from the signal via
- [ ] Via stitching around RF/TFLN region ≤ 2 mm pitch
- [ ] Through-via aspect ratio ≤ 12 : 1 verified against 3.48 mm stackup
      (spec §II)
- [ ] 24-phase DrMOS arrays placed on B.Cu directly under each NCE
      composite module (vertical power delivery, spec §III)
- [ ] 100 nF 01005 bypass capacitors placed ≤ 1 mm from every NCE / HBM4
      power ball (spec §III)
- [ ] 100 mil copper-to-edge clearance on RF / TFLN / optical classes
      verified globally (spec §V)

## 3. Power integrity — signed by **PI lead**

- [ ] DC IR-drop simulated: V_core drop ≤ 10 mV @ 1000 A peak per SoC
- [ ] Plane current density ≤ 20 A/mm² (2 oz) anywhere
- [ ] AC PDN impedance plotted 1 kHz – 1 GHz; target **Z < 5 mΩ DC – 100 MHz**
      (spec §III) with stretch target ≤ 0.5 mΩ over 10 kHz – 10 MHz
- [ ] Four-tier decoupling sweep verified: 100 µF tantalum bulk /
      10 µF 0805 / 1 µF 0402 / 100 nF 01005; anti-resonance peaks < 5 mΩ
- [ ] Embedded-capacitance (Faradflex BC24) contribution measured
      (target ≈ 4–5 µF distributed, 10 – 300 MHz null fill)
- [ ] VRM loop stability (Bode) verified across full load step
- [ ] VRM transient response simulated: di/dt = 200 A/µs;
      V_core excursion ≤ ±30 mV

## 4. Signal integrity — signed by **SI lead**

- [ ] PCIe Gen 6 end-to-end link budget ≤ 32 dB @ 16 GHz (Nyquist),
      including retimer, via, connector, edge-finger loss
- [ ] PCIe Gen 6 eye opening: > 20 mV, > 0.25 UI at receiver (statistical, BER 1e-12)
- [ ] HBM4 REFCK: jitter < 150 fs RMS at the composite-module input pin
- [ ] HBM4 data-bus SI: **delegated to interposer vendor**; PCB-side signoff
      covers only side-channel + PDN
- [ ] TFLN RF: S-parameters extracted 1 – 80 GHz, insertion loss < 6 dB
- [ ] TFLN RF common-mode rejection ≥ 30 dB at 16 GHz
- [ ] SerDes channel operating margin (COM) ≥ 3 dB
- [ ] 100 MHz REFCLK jitter < 100 fs RMS (10 kHz – 20 MHz)

## 5. Thermal — signed by **Thermal lead**

- [ ] Compute unit Tj ≤ 95 °C at 800 W TDP with chosen cold plate
- [ ] DrMOS Tj ≤ 105 °C at 42 A per phase, 55 °C inlet air
- [ ] TFLN PIC junction held at 25 ± 2 °C; TEC power budget < 20 W
- [ ] HBM4 stack Tj ≤ 95 °C at 100 W/stack under composite-module cold plate
- [ ] Direct-to-chip cold plate CFD (40 kPa, 1 L/min water) shows < 20 °C rise

## 6. EMC / ESD — signed by **Compliance lead**

- [ ] Radiated emissions pre-compliance: FCC Class A, 30 MHz – 6 GHz
- [ ] Conducted emissions: meets CISPR 32 Class A on 12V input
- [ ] ESD contact (± 8 kV) / air (± 15 kV) per IEC 61000-4-2
- [ ] Surge / EFT bursts on 12V input: meet IEC 61000-4-4 / -4-5

## 7. Security — signed by **Security lead**

- [ ] TPM 2.0 wiring verified per TCG spec
- [ ] SPI flash split: redundant A/B with physical switch
- [ ] JTAG header behind a solder-bridge jumper (production: open)
- [ ] Debug UART behind a jumper

## 8. Manufacturing — signed by **DFM lead**

- [ ] `docs/DFM_Checklist.md` all items pass / waived
- [ ] Test-point coverage ≥ 95 % of nets; flying-probe review complete
- [ ] Fiducials placed; panel scheme agreed with EMS
- [ ] Assembly drawings (top + bottom) rendered from KiCad; PN + rev baked in
- [ ] Manufacturer DFM report (Sierra / TTM / NCAB) reviewed; errors = 0
- [ ] Stencil design reviewed (thickness, aperture, step-down)

## 9. Fab package — signed by **Release engineer**

- [ ] **ODB++** package generated (primary design-transfer format, spec §V)
- [ ] IPC-2581C package generated (redundant)
- [ ] Gerber X2 per layer (32 copper + mask + paste + silk + edge) (redundant)
- [ ] Excellon 2 drill files (PTH + NPTH separate; plated / non-plated tagged;
      one drill file per microvia / buried / blind span per `fab/gerber_layers.txt`)
- [ ] Back-drill file(s) with per-lane target depth and stub length
- [ ] IPC-D-356A netlist
- [ ] Pick-and-place (CSV, top + bottom, units mm, rotation degrees)
- [ ] BOM.csv with MFR + MPN + distributor (LCSC / Mouser / Digi-Key, active
      parts only per spec §V) + footprint + DNP column
- [ ] Fab drawing PDF (dimensioned outline, stackup, finish, tolerances, notes)
- [ ] Assembly drawings PDF (top + bottom, ref des visible)
- [ ] Impedance / back-drill / microsection / CAF test-coupon strip attached
      to panel (see `docs/Stackup.md` §7)
- [ ] Readme.txt in the fab zip summarizing the package

## 10. Change control

- [ ] Every change since the previous tape-out is logged in `CHANGELOG.md`
- [ ] ECO notices signed by original design owner
- [ ] Schematic + layout + BOM all tagged with the same release tag
      (e.g. `v4.0-tapeout`)

## 11. Archival

- [ ] Git tag `v4.0-tapeout` pushed and protected
- [ ] Tapeout package zipped, hash-signed, uploaded to release storage
- [ ] Fab quote + PO linked to the release
- [ ] First-article review date scheduled

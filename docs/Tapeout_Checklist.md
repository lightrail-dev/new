# Tape-out Sign-off Checklist

Every item must be owned, dated, and signed before Gerbers are released.
Owners are suggested; reassign as needed.

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
- [ ] Length-matching complete: DDR5 byte lanes, PCIe Gen 6, TFLN RF
      (see `docs/DFM_Checklist.md` §7)
- [ ] Back-drill applied on PCIe Gen 6 edge lanes
- [ ] Controlled-impedance traces match class targets within ±10 %
      (±7 % for TFLN RF) per post-layout SI extraction
- [ ] Every high-speed diff pair has a continuous reference plane
- [ ] Via stitching around RF/TFLN region ≤ 2 mm pitch

## 3. Power integrity — signed by **PI lead**

- [ ] DC IR-drop simulated: V_core drop ≤ 10 mV @ 1000 A peak per SoC
- [ ] Plane current density ≤ 20 A/mm² (2 oz) anywhere
- [ ] AC PDN impedance plotted 1 kHz – 1 GHz; target Z ≤ 0.5 mΩ
      across 10 kHz – 10 MHz band
- [ ] Decoupling topology reviewed: bulk, MLCC, package, on-die
- [ ] VRM loop stability (Bode) verified across full load step
- [ ] VRM transient response simulated: di/dt = 200 A/µs;
      V_core excursion ≤ ±30 mV

## 4. Signal integrity — signed by **SI lead**

- [ ] PCIe Gen 6 end-to-end link budget ≤ 32 dB @ 16 GHz (Nyquist),
      including retimer, via, connector, edge-finger loss
- [ ] PCIe Gen 6 eye opening: > 20 mV, > 0.25 UI at receiver (statistical, BER 1e-12)
- [ ] DDR5-8800 timing closure: setup/hold margin > 0.1 UI at all corners
- [ ] DDR5 SSN analysis: ≤ 150 mV per rail
- [ ] TFLN RF: S-parameters extracted 1 – 80 GHz, insertion loss < 6 dB
- [ ] TFLN RF common-mode rejection ≥ 30 dB at 16 GHz
- [ ] SerDes channel operating margin (COM) ≥ 3 dB
- [ ] 100 MHz REFCLK jitter < 100 fs RMS (10 kHz – 20 MHz)

## 5. Thermal — signed by **Thermal lead**

- [ ] Compute unit Tj ≤ 95 °C at 800 W TDP with chosen cold plate
- [ ] DrMOS Tj ≤ 105 °C at 42 A per phase, 55 °C inlet air
- [ ] TFLN PIC junction held at 25 ± 2 °C; TEC power budget < 20 W
- [ ] DDR5 DIMM Ta ≤ 85 °C at 5 W per module
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

- [ ] Gerber X2 per layer (copper, mask, paste, silk, edge)
- [ ] Excellon 2 drill files (PTH + NPTH separate; plated / non-plated tagged)
- [ ] IPC-D-356A netlist
- [ ] Pick-and-place (CSV, top + bottom, units mm, rotation degrees)
- [ ] BOM.csv with MFR + MPN + distributor + footprint + DNP column
- [ ] Fab drawing PDF (dimensioned outline, stackup, finish, tolerances, notes)
- [ ] Assembly drawings PDF (top + bottom, ref des visible)
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

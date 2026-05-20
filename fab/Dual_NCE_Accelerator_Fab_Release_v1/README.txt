========================================================================
DUAL NCE ACCELERATOR — FABRICATION RELEASE PACKAGE v1
LightRail AI Compute Node (LR-P3A) Rev 6.3
Generated: 2026-05-19 06:21 UTC
========================================================================

PACKAGE CONTENTS:

gerbers/
  Dual_NCE_Accelerator_TopCopper.gbr        Layer 1 (F.Cu) - Signal/Power
  Dual_NCE_Accelerator_Inner1.gbr           Layer 2 (In1.Cu) - Signal
  ...through...
  Dual_NCE_Accelerator_Inner30.gbr          Layer 31 (In30.Cu) - Signal
  Dual_NCE_Accelerator_BottomCopper.gbr     Layer 32 (B.Cu) - Signal/Power
  Dual_NCE_Accelerator_TopSolderMask.gbr    Top solder mask
  Dual_NCE_Accelerator_BottomSolderMask.gbr Bottom solder mask
  Dual_NCE_Accelerator_TopSilkscreen.gbr    Top silkscreen
  Dual_NCE_Accelerator_BottomSilkscreen.gbr Bottom silkscreen
  Dual_NCE_Accelerator_TopPaste.gbr         Top solder paste (stencil)
  Dual_NCE_Accelerator_BottomPaste.gbr      Bottom solder paste (stencil)
  Dual_NCE_Accelerator_EdgeCuts.gbr         Board outline + cutouts

drill/
  Dual_NCE_Accelerator_PTH.drl              Plated through-holes (Excellon)
  Dual_NCE_Accelerator_NPTH.drl             Non-plated through-holes (Excellon)
  Dual_NCE_Accelerator_DrillMap_PTH.gbr     PTH drill map (visual)
  Dual_NCE_Accelerator_DrillMap_NPTH.gbr    NPTH drill map (visual)

assembly/
  Dual_NCE_Accelerator_BOM.csv              Bill of Materials (full)
  Dual_NCE_Accelerator_CPL.csv              Centroid / Pick & Place (combined)
  Dual_NCE_Accelerator_CPL_top.csv          Pick & Place (top side)
  Dual_NCE_Accelerator_CPL_bottom.csv       Pick & Place (bottom side)
  Dual_NCE_Accelerator_Assy_Drawing_Top.pdf Top assembly drawing
  Dual_NCE_Accelerator_Assy_Drawing_Bottom.pdf Bottom assembly drawing

docs/
  Dual_NCE_Accelerator_Fab_Drawing.pdf      Fabrication drawing
  Dual_NCE_Accelerator_Fab_Notes.txt        Detailed fabrication notes
  Dual_NCE_Accelerator_Stackup_Impedance.txt  Stackup & impedance report
  Dual_NCE_Accelerator.ipc2581              IPC-2581C unified package
  Dual_NCE_Accelerator.odb++.tgz            ODB++ unified package (if available)

testing/
  Dual_NCE_Accelerator_Netlist.ipc          IPC-D-356 bare-board test netlist
  Dual_NCE_Accelerator_DRC_Report.json      Design Rule Check (JSON)
  Dual_NCE_Accelerator_DRC_Report.rpt       Design Rule Check (human-readable)

3d_model/
  Dual_NCE_Accelerator_3D.step              3D STEP model (AP242)

BOARD SPECIFICATIONS:
  Dimensions: 420.0 x 350.0 mm
  Layers: 32 (HDI)
  Thickness: 3.48 mm +/- 10%
  Surface finish: ENIG (IPC-4552 Class 3)
  Min trace/space: 0.075/0.075 mm
  Via drill: 0.30 mm minimum (aspect ratio 11.6:1)
  Mounting: 4x M3 corner + 8x M3 per NCE cold-plate

QUALITY REQUIREMENTS:
  IPC-6012 Class 3
  100% bare-board electrical test (IPC-D-356)
  Impedance test coupons required
  Cross-section for first article

========================================================================

# Merge plan: integrated surface-water + groundwater PFAS paper

**Decision (2026-06-22, Vahid):** merge the SWAT+↔MODFLOW 6 coupling paper into the PFAS
surface-water paper to produce one integrated paper — **PFAS fate and transport through both
surface water and groundwater in SWAT+/MODFLOW 6** — unified on the **Rogue River (04118500)**.
This directly answers the open problem named by Raschke (2022) and Rafiei (2023): a continuous
watershed-scale PFAS mass balance spanning soil → surface water AND soil → groundwater → stream.

## Source papers
- **A — PFAS surface-water** (`publication/swatplus-pfas-fate-transport/`): mature, near-submission
  (Water Research). SWAT+ PFAS engine (soil 3-phase Freundlich+Langmuir AWI → land mobilization →
  in-stream linear-partition routing → reservoirs + point sources). Validated on the Rogue
  (04118500) vs 29 EGLE PFOS stations; mainstem log-RMSE 0.15 dex; 120-member UA. Routes runoff,
  lateral, leaching, sediment — **but NOT groundwater discharge** (named explicitly as a pathway
  it integrates but does not route).
- **B — SWAT+↔MF6 coupling** (`publication/swatplus-modflow6-coupling/paper/`): thin standalone.
  Automated SWAT+→MF6 generation; two-way recharge/baseflow; baseflow-constrained calibration;
  GW PFAS (GWT Freundlich) + SFR/SFT in-stream routing. Demonstrated on 04124500 with a synthetic
  source. First SWAT+↔MF6 coupling.

## Unification thesis
B supplies the exact missing pathway A names (groundwater discharge), and the SFT in-stream return
delivers GW-borne PFAS into the same channel network A already routes surface-water PFAS through.
The merged paper closes the soil→{SW,GW}→stream PFAS mass balance on one watershed against real
observations — the continuous mass balance prior reviews said did not exist.

## Key scientific hook
A's largest residual is the lower-Rogue underprediction near Wolverine/House Street (modeled
14.7–15.4 vs observed 19–27 ng/L), attributed to "the concentrated point source." That site is a
**groundwater-borne plume**, so the GW→stream PFAS discharge (SFT) is the physically correct
mechanism to close that residual. Target result: the integrated SW+GW model reproduces the
lower-mainstem peak that the SW-only model underpredicts.

## Work plan (unify on Rogue)
1. **Build Rogue MF6+SFR model** via MODGenX (`MODFLOW_sfr`, 04118500/0405). [IN PROGRESS]
2. **Calibrate Rogue GW** — heads + baseflow (streambed-K tune; PEST++ if needed).
3. **GW PFAS transport** — GWT Freundlich with a Wolverine/House-Street-anchored source; SFT
   routes GW-discharged PFAS to reaches.
4. **Integration** — add the SFT GW→stream PFAS load to A's land-derived in-stream load; produce
   combined in-stream PFOS; compare to the 7 mainstem EGLE reaches; test whether GW closes the
   lower-mainstem residual.
5. **Merge manuscripts** — combined intro / methods (engine [A] + generation+coupling+GW-PFAS [B]
   + integration) / Rogue study area / results (correctness + SW gradient + GW calib + integrated
   PFAS + UA) / discussion. Target Water Research; explicit complement to Rafiei (2023).

## Risks
- GW source magnitude adds an equifinality knob alongside soil-loading — constrain with House
  Street plume data if available, else report jointly.
- Rogue (606 km²) is ~4× larger than 04124500 → bigger MF6 model, slower calibration.
- Delays Paper A's submission; the merged paper is the stronger contribution.

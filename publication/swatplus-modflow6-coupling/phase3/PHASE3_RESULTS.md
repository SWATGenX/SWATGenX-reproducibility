# Phase 3 — PFAS groundwater fate & transport (MF6 GWT, 04124500)

**Status: DONE.** A MODFLOW 6 groundwater-transport (GWT) model is coupled to the calibrated
steady-state flow field via the GWF6–GWT6 exchange, with **Freundlich** PFAS sorption. A
contaminated-site source migrates downgradient and discharges to the streams — the groundwater
leg of the PFAS pathway, and the differentiator over a static/frozen RT3D coupling. Both a
sorbing PFAS plume and a conservative reference tracer run on the same flow field for comparison.

## What Phase 3 does (`phase3_pfas_gwt.py`)
- Loads the frozen calibrated GWF (`MODFLOW_wl_cal`, baseflow-matched realization, see
  `../pest/PEST_RESULT.md`) and couples a GWT model to it on the identical grid via
  `GWF6-GWT6` exchange (steady flow, transient transport, 40 yr).
- Transport physics: TVD advection, dispersion (αL=10 m, αT=1 m at the 250 m grid), and
  **Freundlich sorption** (MST `sorption='freundlich'`, `distcoef=Kf`, `sp2=n`).
- Source: a constant-concentration (CNC) cell of 100 ng/L at the highest-head (upgradient)
  active cell, layer 0. SSM carries the cell concentration on outflow to streams/wells/drains
  — i.e. the GW→stream PFAS discharge.
- Outputs: final plume rasters (PFAS vs conservative) + a breakthrough time series at the
  stream cell the plume reaches. Figure: `phase3_pfas_plume.png`.

## Result — sorption retards and delays the plume
| | conservative tracer | Freundlich PFAS |
|---|---|---|
| plume footprint (>1 ng/L), 40 yr | **270 cells** | **17 cells** |
| GW→stream breakthrough at discharge cell | ~year 28–30, rising to 2.5 ng/L | **no arrival in 40 yr** (stays at background) |

The conservative tracer forms a broad downgradient plume that reaches and discharges to the
stream within ~30 yr. The Freundlich-sorbed PFAS plume is retarded by ~an order of magnitude
(R≈10, below) — it stays tightly clustered near the source and has **not** broken through to
the stream within the 40 yr horizon. This is the expected PFAS persistence/retardation signature
and demonstrates the coupled GWF→GWT→stream pathway end to end.

## Numerical fixes (the convergence work)
The conservative tracer converged immediately. The **Freundlich** run did not: the transport
solver stalled mid-run (period ~24–26) even after ATS cut the time step to <6 days. Root cause
is the Freundlich retardation term `R = 1 + (ρb/θ)·Kf·n·C^(n-1)`, which is **singular as C→0**
(n<1 ⇒ `C^(n-1)→∞`) at the spreading plume front. Fixes:
1. **Ambient background concentration** `C_background = 0.1 ng/L` as the transport initial
   condition (sorbing model only). Physically real — diffuse atmospheric/land-applied PFAS
   makes low-level PFAS ubiquitous in shallow groundwater — and keeps `C>0` everywhere, removing
   the `C^(n-1)` singularity. This is the fix that made it converge.
2. **Adaptive time stepping (ATS)** on TDIS (`ModflowUtlats`, parent = TDIS package; `dtfailadj=4`)
   so the solver cuts dt on a failed step and recovers instead of aborting. (flopy gotcha: ATS
   must have the *TDIS package* as parent, not the simulation, or the `ATS6 FILEIN` record is
   never written; and `iperats` is written 1-based from a 0-based perioddata index.)
3. Transport IMS: `COMPLEX`/BICGSTAB, `outer_maximum=200`.

## Parameter note (review point)
`Kf=0.05`/`n=0.8` (the initial Li-et-al-range guess) implies retardation **R≈96** at C=100 ng/L
in MF6's units (ρb=1800 kg/m³, θ=0.30, conc ng/L) — far above the literature PFOS range for
low-foc sand (R≈5–10) and gives only a 1-cell plume. Lowered to **`Kf=0.005`** (R≈10.6) for unit
consistency and a realistic, visibly-retarded plume. `n=0.8` retained. If a specific site Kf/n
is preferred, change the two constants at the top of `phase3_pfas_gwt.py` and re-run.

## Files
- `phase3_pfas_gwt.py` — builds + runs both GWT models, writes `phase3_plumes.npz` (next to the
  model, www-data-writable).
- `phase3_plot.py` — 3-panel figure (conservative plume / PFAS plume / breakthrough).
- `build_calibrated_gwf.py` — freezes `MODFLOW_wl_cal` from the PEST++ posterior (Phase 3 prereq).
- `phase3_pfas_plume.png` — the figure.

## Next (deferred)
RIV→SFR streams would let PFAS route *in-stream* after groundwater discharge (closing the loop
back into the SWAT+ channel PFAS module from Phase 1–2 of the engine work). The GW leg is done.

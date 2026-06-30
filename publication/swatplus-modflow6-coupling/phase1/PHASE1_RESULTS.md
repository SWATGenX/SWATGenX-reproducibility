# Phase 1 — SWAT+ daily percolation → MODFLOW 6 recharge (one-way handoff)

**Status: DONE.** Demonstrated end-to-end on Michigan-LP model **04124500** (Pere Marquette).

## What Phase 1 establishes

The first of the three coupling links: the SWAT+ **land phase** drives the MODFLOW 6
**groundwater flow** solution. Daily per-HRU percolation leaving the SWAT+ soil profile
becomes the spatially-distributed recharge boundary of the MF6 model, applied one stress
period (one day) at a time through the MF6 BMI/XMI API — no file round-trips, no restart.

## Pipeline (`MODFLOW/MODGenX/swatmf_phase1_driver.py`)

1. **Spatial link** (`swatmf_coupling.build_hru_cell_map`, Phase-1a deliverable):
   area-weighted intersection of the 5 549 SWAT+ HRU polygons (`hrus1.shp`) with the
   5 520-cell MF6 grid → 22 897 (HRU, cell) overlaps. Median cell HRU-coverage = 1.00.
2. **Temporal source**: SWAT+ re-run with `hru_wb` daily enabled → `hru_wb_day.nc`
   (`perc`, mm day⁻¹, 1 096 days × 5 549 HRUs, 2022–2024; obj_id = HRU id).
3. **Distribution** (vectorised as a sparse matrix-multiply): per-cell recharge
   `R[c,t] = Σ_HRU(perc[h,t]·overlap[h,c]) / cell_area[c]`, mm→m.
4. **Transient MF6**: the converged steady model is rewritten as 1 096 daily stress
   periods (period 0 = steady spin-up at long-term-mean recharge; STO transient, Sy 0.15,
   Ss 1e-5) and driven stepwise through `modflowapi`: at each `stress_period_start` the
   day's recharge field is written in place to the `RCHA/RECHARGE` BMI pointer, then MF6
   solves that day's flow.

## Result (`phase1_result.json`, `phase1_coupling.png`)

| metric | value |
|---|---|
| daily steps solved | **1096 / 1096** (every step converged) |
| simulated window | 2022-01-01 … 2024-12-31 |
| basin-mean percolation | 0.782 mm day⁻¹ |
| steady baseline mean head | 232.41 m |
| transient mean head range | 232.28 – 232.61 m (Δ ≈ 0.32 m) |
| wall time | 65 s (local, single model) |

The domain-mean groundwater head tracks the seasonal recharge signal with the expected
storage lag — rising through the high-recharge spring of 2024, drawing down in dry spells —
oscillating physically about the steady-state baseline. This confirms the handoff is both
**numerically stable** (no step fails) and **dynamically responsive**.

## Validation — average-annual simulated vs observed heads (`validate_heads.py`)

510 Wellogic observation wells (520 total, 10 dropped by the corrupt-SWL gate). The
observations are static depth-to-water snapshots, so we compare them against the
**average-annual** SWAT+-driven simulated head at each well cell (mean within each year,
then across 2022–2024), extracted from the 1 096-day `.hds`.

| fit (510 wells) | avg-annual transient | steady baseline (MODGenX) |
|---|---|---|
| NSE | −0.77 | −0.75 |
| KGE | 0.27 | 0.28 |
| RMSE | 22.2 m | 22.1 m |
| PBIAS | +8.1 % | +8.1 % |
| R² | 0.43 | 0.45 |

**Reading it honestly:** the avg-annual transient fit is statistically identical to the
steady baseline, and the year-to-year metrics are flat (interannual well-mean head spread
is only 0.20 m). So the misfit is **not a coupling artifact** — it is the *uncalibrated*
MODGenX model sitting ~8 % / 22 m high (heads pinned near land surface by `strt=top` and
uncalibrated K; see the simulated-head "floor" near 218 m in `phase1_validation.png`).
Convergence and the SWAT+ handoff are sound; matching observed heads is the **calibration**
step (gwflow-zone / MF6 parameter estimation), which runs after and is unchanged by Phase 1.

> 04124500 happens to be a poorly-conditioned *uncalibrated* model. Two of the other
> converged Michigan-LP models (04080206, 040900010212) already fit observed heads
> excellently *before* calibration (NSE 0.92–0.94); re-running this transient validation on
> one of those would show the coupling on a well-conditioned model.

## Next

- **Phase 2** — bidirectional: return MF6 GW↔river/lake exchange (GET RIV SIMVALS per
  step) back into the SWAT+ channel balance; switch lakes to GHB (two-way) for the coupled
  runs. The MF6 builder already has the `lake_method='ghb'` toggle for this.
- **Phase 3** — PFAS-GWT: add the MF6 GWT model so the calibrated channel/soil PFAS source
  terms transport through groundwater.

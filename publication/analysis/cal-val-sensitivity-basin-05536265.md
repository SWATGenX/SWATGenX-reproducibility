# Controlled evaluation basin — 05536265 (VPUID 0712)

**Role in manuscript (Objective 4):** Second controlled HUC12 domain for calibration, verification, and Morris sensitivity—Illinois hydroclimate complement to Florida basin `02297600`.

**Publication status:** **Exported (2026-06-01).** Run label `controlled_eval_05536265_split20260601`; scenario `Default_calval_split202606`; Morris remains on `Default_initialized`.

---

## Split-sample windows (`Default_calval_split202606`)

| Stage | ModelProcessing settings | Scored window | Notes |
|-------|-------------------------|---------------|--------|
| Calibration | `CAL_START_YEAR=2018`, `CAL_END_YEAR=2024`, `CAL_NYSKIP=2` | **2020-01-01**–**2024-12-31** | Post-2018 warm-up. |
| Verification | `VER_START_YEAR=2011`, `VER_END_YEAR=2015`, `VER_NYSKIP=1` | **2012-01-01**–**2015-12-31** | Pre-calibration holdout; no overlap with cal. |

---

## Model identity

| Field | Value |
|-------|--------|
| **model_id** | `0712/usgs_station/05536265` |
| **USGS site** | `05536265` |
| **VPUID** | `0712` |
| **State** | IL (~59 km²) |
| **Gage channel (GIS)** | **25** (`streamflow_data/25_05536265.csv`) |
| **Calibration scenario** | `Default_initialized` |
| **User tree** | `${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0712/usgs_station/05536265/` |

---

## Workflow settings (frozen snapshots)

**Cal/val** — `calibration_artifacts/Default_initialized/calval_settings_snapshot.json`:

| Setting | Value |
|---------|--------|
| CAL_START_YEAR / CAL_END_YEAR / CAL_NYSKIP | 2018 / 2024 / 2 |
| VER_START_YEAR / VER_END_YEAR / VER_NYSKIP | 2011 / 2015 / 1 |
| CAL_POOL_SIZE / MAX_CONCURRENT / MAX_ITERATIONS | 24 / 6 / 50 |
| STAGNATION_ITERATIONS | 10 |

Scored calibration window: **2020-01-01**–**2024-12-31**.  
Verification holdout: **2012-01-01**–**2015-12-31**.

**Morris sensitivity** — `sensitivity/sensitivity_settings_snapshot.json`:

| Setting | Value |
|---------|--------|
| sen_total_evaluations | 1000 |
| num_trajectories × (n_params + 1) | 27 trajectories, 4 levels |
| max_concurrent | 5 |
| Simulation window | Same as calibration (2018–2024, nyskip 2) |

Top Morris μ* drivers: `melt_min`, `k`, `cn3_swf`, `perco`, `melt_max`, `urban_cn_c`, `mann`, `surq_lag`.

---

## Manuscript deliverables

| Deliverable | Target | Status |
|-------------|--------|--------|
| Tab-Metrics rows | `tab-metrics.csv` HM-07--HM-12 | **exported** |
| Tab-Sensitivity-Morris | append with `model_id` column | **exported** |
| Fig-CalValHydrograph | `fig-cal-val-05536265-hydrographs-3panel.png` | **exported** |
| Fig-MorrisSpider | `fig-morris-spider-controlled-basins.png` | **exported** (FL top-8; IL top-6) |
| tab-calibration-run-settings | `controlled_eval_05536265_20260601` | **exported** |

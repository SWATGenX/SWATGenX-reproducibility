# Controlled evaluation basin — 02297600 (VPUID 0310)

**Role in manuscript (Objective 4):** Single **controlled** HUC12 domain for initialization, split-sample **calibration**, **verification**, and **Morris global sensitivity** using the platform `init_cal_val` workflow. Supersedes the earlier proof-basin designation for `01567500` (2026-05-31 protocol amendment).

**Publication status:** **Exported (2026-06-01).** Run label `controlled_eval_02297600_split20260601`; scenario `Default_calval_split202606`; metrics and hydrographs frozen via `export_objectives_4_5.py`.

---

## Post-run checklist (before `export_objectives_4_5.py`)

1. Florida verification scores **2019–2024** (`VER_START=2019`, `VER_END=2024`, `VER_NYSKIP=0`), not 2012–2015 or 2020–2024 only.
2. Bundled/wrong Florida verification under `Default_calval_split202606` is absent or not exported; export reads `Default_calval_split202606` artifacts only.
3. `calval_settings_snapshot.json`, `CentralPerformance.txt`, Table~8 (`tab-metrics.csv`), hydrograph metadata, and this protocol agree on scored windows.
4. Manuscript states **basin-specific independent verification windows**, not symmetric split-sample semantics.
5. Run: `python publication/analysis/scripts/verify_calval_split202606_postrun.py`

---

## Split-sample windows (`Default_calval_split202606`)

| Stage | ModelProcessing settings | Scored window | Notes |
|-------|-------------------------|---------------|--------|
| Calibration | `CAL_START_YEAR=2010`, `CAL_END_YEAR=2018`, `CAL_NYSKIP=3` | **2013-01-01**–**2018-12-31** | NWIS daily 00060 begins **2009-10-01**; planned 2003–2010 cal is infeasible (~84% missing → objective 0). |
| Verification | `VER_START_YEAR=2019`, `VER_END_YEAR=2024`, `VER_NYSKIP=0` | **2019-01-01**–**2024-12-31** | Independent of calibration; no overlap with 2013–2018 scored cal. |

Illinois companion basin **05536265** uses scored cal **2020–2024** and ver **2012–2015** (independent holdout before calibration period).

---

## Workflow settings (frozen snapshots — prior `Default_initialized` export)

**Cal/val** — `calibration_artifacts/Default_initialized/calval_settings_snapshot.json`:

| Setting | Value |
|---------|--------|
| CAL_START_YEAR / CAL_END_YEAR / CAL_NYSKIP | 2010 / 2018 / 3 |
| VER_START_YEAR / VER_END_YEAR / VER_NYSKIP | 2011 / 2015 / 1 |
| CAL_POOL_SIZE / MAX_CONCURRENT / MAX_ITERATIONS | 48 / 6 / 70 |
| STAGNATION_ITERATIONS | 20 |

Scored calibration window: **2013-01-01**–**2018-12-31** (3-y warm-up from 2010).  
Verification in the 2026-05-31 export: **2012-01-01**–**2015-12-31** — **overlapped calibration**; superseded by independent **2019–2024** verification in `Default_calval_split202606`.

---

## Model identity

| Field | Value |
|-------|--------|
| **model_id** | `0310/huc12/02297600` |
| **USGS site** | `02297600` |
| **VPUID** | `0310` |
| **LEVEL** | `huc12` |
| **NAME** | `02297600` |
| **MODEL_NAME** | `SWAT_MODEL_Web_Application` |
| **User tree** | `${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc12/02297600/` |
| **Calibration scenario** | `Default_calval_split202606` (rerun); Morris on `Default_initialized` |
| **Gage channel (GIS)** | **2** (`streamflow_data/2_02297600.csv`) |

**Morris sensitivity** — `calibration_artifacts/Default_initialized/sensitivity/sensitivity_settings_snapshot.json`:

| Setting | Value |
|---------|--------|
| sen_total_evaluations | 1000 |
| num_trajectories × (n_params + 1) | 27 trajectories, 4 levels |
| max_concurrent | 5 |
| Window | Same calibration period as PSO |

---

## Artifacts (admin tree)

| Artifact | Path (under `calibration_artifacts/Default_initialized/`) |
|----------|--------------------------------------------------------------|
| Cal/val settings | `calval_settings_snapshot.json` |
| Best / local best parameters | `best_solution_*.txt`, `local_best_solution_*.txt` |
| Performance log | `../../CentralPerformance.txt` |
| Cal figures | `figures_SWAT_MODEL_Web_Application/SF/calibration/` |
| Verification figures / NPZ | `figures_*/SF/verification/`, `ensemble/m*_s2.npz` |
| Morris indices | `sensitivity/morris_Si_SWAT_MODEL_Web_Application.csv` |
| Morris samples | `sensitivity/morris_samples_SWAT_MODEL_Web_Application.csv` |
| Sensitivity ensemble | `sensitivity/ensemble/m{NNN}_s2.npz` |
| Sensitivity QC | `sensitivity/sensitivity_qc_report.json` (when written) |
| Tornado / ensemble PNGs | `figures_*/SF/sensitivity/` |

---

## Indicative skill (global best — verify before freezing tab-metrics)

From `CentralPerformance.txt` cache rows (calibration global best, channel 2):

| Stage | Daily NSE | Monthly NSE | PBIAS (%) |
|-------|-----------|-------------|-----------|
| Calibration | 0.847 | 0.912 | −1.6 |
| Verification (global best) | ~0.666–0.679 | ~0.718–0.726 | +2–9 |

Top Morris μ* drivers (see `morris_Si_*.csv`): `perco`, `revap_co`, `cn2`, `revap_min`, `alpha_bf` (domain QC: snow pass, low reservoir influence).

---

## Manuscript deliverables (Objective 4 — planned)

| Deliverable | Target path | Status |
|-------------|-------------|--------|
| **Tab-Metrics** | `publication/tables/tab-metrics.csv` | Replace 01567500 rows with frozen 02297600 rows |
| **Tab-Calibration-Run-Settings** | `tab-calibration-run-settings.csv` | Add completed row for 02297600 |
| **Tab-Sensitivity-Morris** | `tab-sensitivity-morris.csv` (new) | Export top μ* from Morris CSV |
| **Fig-CalValHydrograph** | `figures/final/fig-cal-val-02297600-hydrographs-3panel.png` | `python publication/analysis/scripts/render_calval_hydrographs.py --site-no 02297600` |
| **Fig-MorrisSpider** | `figures/final/fig-morris-spider-controlled-basins.png` (panel a) | From `plot_morris_spider.py` |
| **Results §** | `manuscript/sections/results.tex` | Replace 01567500 subsection |

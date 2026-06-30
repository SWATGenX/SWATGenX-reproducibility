# Calibration / validation plan — Small locked basin (Florida)

**Basin:** `model_id` = `0308/usgs_station/02239501` (NWIS `02239501`, VPU `0308`, ~52.64 km²).  
**Purpose:** Pre-specify a **lightweight hydrologic plausibility** exercise acceptable to reviewers **without** reframing the JAWRA manuscript as a regional calibration study.  
**Status:** Planning only — **no** calibration jobs are mandated on this branch.

---

## Evidence and code anchors

- **Evaluation protocol:** `publication/analysis/evaluation-protocol.md` (Phase 1 currently has hydrologic evaluation **No** — any manuscript move requires an **amendment** + frozen observation tables).
- **Observation audit:** `publication/analysis/calibration-data-availability.md` and `publication/tables/tab-streamflow-availability.csv`.
- **Objective implementation:** `ModelProcessing/ModelProcessing/evaluation.py` (sum of **daily NSE** and **monthly NSE** per station; negated for minimization).
- **PSO driver:** `ModelProcessing/ModelProcessing/PSO_calibration.py`, `ModelProcessing/ModelProcessing/processing_program.py`.
- **Parameter bounds:** `bin/cal_parms_SWAT_MODEL_Web_Application.cal` (copy resolved under each model tree as `cal_parms_{MODEL_NAME}.cal`).

---

## Warm-up, calibration, and validation periods (recommended defaults)

**Design principle:** Use **contiguous calendar years** with a **clear split** so validation is not a subset of calibration days. **After** the NWIS audit (2026-05-13), the **default** windows below are **defensible for FL and PA** locked outlets; they remain **invalid for KS `07174000`** until modern daily Q is resolved.

| Phase | Recommended span | Notes |
|-------|------------------|--------|
| **Warm-up inside calibration run** | `START_YEAR=2000`, `nyskip=3` | First three calendar years simulated but **not scored**; observations should still exist for overlap checks from **2000-01-01** onward. |
| **Calibration scoring window** | **2003-01-01** through **2010-12-31** | Matches `START_YEAR=2000`, `END_YEAR=2010`, `nyskip=3` in `ModelProcessing/ModelProcessing/config.py`. |
| **Validation scoring window** | **2012-01-01** through **2015-12-31** | Matches `Ver_START_YEAR=2011`, `Ver_END_YEAR=2015`, `Ver_nyskip=1` (first verification year used for spin-up only). |

**Justification for split:** Standard **split-sample** logic — parameters are not scored on validation-year daily flows. Lengths balance **metric stability** vs **runtime** for a single-gage sanity check.

**SWATGenX gap rule:** `read_observed_data` / `evaluation.py` effectively require **≤10%** missing daily observations in the evaluated window or the station contributes score `0`. The NWIS audit confirms **0%** missing daily values in the listed windows for **02239501** and **01451800**.

**Temporal resolution:** The pipeline scores **daily** and **monthly** (`evaluation.py`). **Recommendation:** use **daily hydrographs** for shape/timing in the **supplement** first; keep **monthly** aggregation in the narrative because it is already part of the scalar objective and stabilizes water-balance bias discussion. **Daily objective components** remain documented in supplement / methods text, not promoted as a separate “extra” benchmark beyond what the code minimizes.

---

## Candidate metrics (reporting, not all in objective)

| Metric | Role today | Manuscript use |
|--------|------------|----------------|
| **NSE** (daily + monthly) | **Inside PSO objective** | Primary plausibility headline; disclose sum-of-NSE objective. |
| **KGE, PBIAS, RMSE, MAPE** | Logged to `CentralPerformance.txt` | Supplementary diagnostics. |
| **R²** | Not computed in `calculate_metrics` | Optional post-process only. |
| **Log-flow NSE** | Not implemented | Requires explicit code change — not first pass. |

---

## Optimizer and workload

Defaults live in `ModelProcessing/ModelProcessing/config.py` and `ModelProcessing/main.py`. **Publication pilot knobs** (separate from code defaults) are recorded in `publication/tables/tab-calibration-run-settings.csv` — e.g. **48 particles**, **50 iterations**, **6 concurrent** simulations on a **10-core** host. Expect **workstation-scale** wall time (highly HRU-dependent); the **Large** KS model is **not** prioritized for streamflow PSO until NWIS data exist in the target windows.

---

## Optional manuscript placement

| Artifact | Main text | Supplement |
|----------|-----------|------------|
| Daily hydrograph (cal + val) | Only if protocol amended and page budget allows | Preferred first home |
| Tab of NSE/KGE/PBIAS (cal vs val) | Optional compact table | Preferred |
| Uncalibrated baseline hydrograph | If run once | Supplement — shows package prior to PSO |

---

## Recommended manuscript framing

1. **Hydrologic plausibility demonstration** — not universal predictive skill.  
2. **Not a regional validation study** — locked outlets only; no CONUS claims.  
3. **Not a national calibration benchmark.**  
4. **Center of gravity stays infrastructure** — NHDPlus HR preprocessing and reproducible SWAT+ packaging remain the core contribution.

---

## Preconditions before any implementation branch

1. **Protocol amendment** in `evaluation-protocol.md` if hydrologic evaluation moves to **Yes**.  
2. **Observation CSV QA** under each model’s `streamflow_data/` (filename stem = `site_no`).  
3. **Weather coverage** for all simulated years.  
4. **Archival policy** for `CentralPerformance.txt`, `best_solution_*.txt`, plots.

---

## Observation data audit and pilot-basin decision (2026-05-13)

**Evidence:** `publication/analysis/calibration-data-availability.md`, `publication/tables/tab-streamflow-availability.csv` (NWIS dv, parameter **00060**, retrieval date **2026-05-13**).

### Florida small basin (`02239501`)

- **Enough daily streamflow for default windows?** **Yes.** NWIS reports continuous daily values from **1932-10-01** through **2026-05-12** with **0%** missing days in **2000–2002**, **2003–2010**, and **2012–2015**.  
- **Selected warm-up (observation coverage):** **2000-01-01**–**2002-12-31** (aligns with `nyskip=3` after `START_YEAR=2000`).  
- **Selected calibration scoring:** **2003-01-01**–**2010-12-31**.  
- **Selected validation scoring:** **2012-01-01**–**2015-12-31** (`Ver_nyskip=1`).  
- **Split reason:** Holdout validation period; compatible with built-in `ModelConfig` defaults and SWATGenX gap rules.  
- **Monthly aggregation for manuscript reporting?** **Yes** — already in the objective; use for bias-stable commentary.  
- **Daily metrics / hydrographs in supplement?** **Yes** — preferred location for daily hydrographs and daily NSE context unless a reviewer forces a single main-text figure.

### Pennsylvania medium basin (`01451800`)

- **Enough daily Q for the same default windows?** **Yes** — **0** missing NWIS days in each listed window. The full NWIS span has **~0.35%** missing days overall (minor gaps outside the pilot windows).  
- **Same recommended periods** as FL for cross-tier comparability **if** a streamflow pilot is later expanded.

### Kansas large basin (`07174000`)

- **NWIS daily 00060** in this audit ends **1958-09-29**. **Default 2000–2015 windows are empty** of NWIS daily values → **do not** treat this tier as streamflow-ready for the planned modern-period pilot until the outlet / gage data issue is resolved.

### Pilot-basin execution decision

- **Proceed with FL `0308/usgs_station/02239501` as the first streamflow pilot** under the audited periods and `tab-calibration-run-settings.csv` **ready_for_execution** row — **after** a dedicated execution branch prepares model + `streamflow_data` CSV + weather (still **not** run on this audit branch).  
- **PA** is **data-ready** on the same windows; **compute cost** (many HRUs) is the practical gate, not NWIS gaps.  
- **KS** row in run-settings remains **`needs_data_review`**.

---

## Suggested next implementation branch (execution)

`agent/hydro-calibration-pilot-fl-huc12-02239501-<YYYYMMDD>` — single outlet, frozen NWIS export, settings from `tab-calibration-run-settings.csv`, archive supplement artifacts only.

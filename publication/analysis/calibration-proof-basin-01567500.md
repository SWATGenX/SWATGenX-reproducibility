# Calibration proof basin — 01567500 (VPUID 0205)

> **Superseded (2026-05-31):** Manuscript Objective~4 now uses **`0310/usgs_station/02297600`** for calibration, verification, and Morris sensitivity. This document and frozen artifacts for `01567500` are retained for audit only; do not cite in new manuscript text unless comparing withdrawn runs.

**Role in manuscript (historical):** Functional water-balance and routing sanity case — **no major lake/reservoir** immediately upstream of the calibration gage, unlike urban/lake-dominated pilots (e.g. 02294217). Demonstrates that SWATGenX assembly + weather + the platform `init_cal_val` workflow can produce **plausible streamflow timing and volume** when the network is not lake-controlled.

**Publication status:** **Completed** (2026-05-18). Results in `manuscript/sections/results.tex` (hydrologic plausibility subsection); metrics in `publication/tables/tab-metrics.csv`; figure `figures/final/fig-cal-proof-01567500-hydrographs-3panel.png`.

---

## Model identity

| Field | Value |
|-------|--------|
| **model_id** | `0205/usgs_station/01567500` |
| **USGS site** | `01567500` |
| **VPUID** | `0205` |
| **LEVEL** | `huc12` |
| **NAME** | `01567500` |
| **MODEL_NAME** | `SWAT_MODEL_Web_Application` |
| **User tree** | `${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0205/usgs_station/01567500/` |
| **Calibration scenario** | `Default_initialized` |
| **QSWAT+** | `use_lakes=False` (lakes shapefile present for GIS; **no** `hydrology.res` / reservoir objects in TxtInOut) |

---

## Model structure (Default_initialized)

| Item | Value / note |
|------|----------------|
| **HRUs** | ~2,235 (`hru.con`) |
| **Model domain area** | ~51.0 km² — union of `subs1.shp` subbasins (`basin_area_sqkm` / catalog method; matches `flood_station.drainage_area_sqkm` NHDPlus fallback ~51.04) |
| **USGS station drainage area** | ~38.85 km² — NWIS `drain_area_va` = 15.0 mi² (`flood_station.usgs_drainage_area_sqmi`; UI ``USGS drainage'') |
| **Why they differ** | Gage is not at the HUC12 outlet; 51 km² is the assembled study domain, 38.85 km² is contributing area at the streamgage per USGS |
| **SWAT channel at gage** | GIS **7** (station-linked channel for streamflow scoring) |
| **Reservoirs / ponds in SWAT** | None (`reservoir.con` absent; `hydrology.res` not used) |
| **Wetlands** | `hydrology.wet` present |
| **Urban** | Present in land cover but not the dominant failure mode for this pilot |

---

## Workflow (init → calibrate → verify)

Command (`init_cal_val.sh` via `www-data`, 2026-05-18):

```bash
SKIP_INIT=0 SKIP_CALIBRATION=0 SKIP_VERIFICATION=0
CAL_POOL_SIZE=48 MAX_CONCURRENT=6 MAX_ITERATIONS=70
STAGNATION_ITERATIONS=20 INIT_WARMUP_SAMPLES=0
CALIBRATION_PLOT_POLICY=best_each_iteration
CAL_START_YEAR=2000 CAL_END_YEAR=2010 CAL_NYSKIP=3
VER_START_YEAR=2011 VER_END_YEAR=2015 VER_NYSKIP=1
```

| Stage | Implementation | Scored period (USGS 00060) |
|-------|----------------|----------------------------|
| **1. Initialization** | `initialize_model.py` copies `Default` → `Default_initialized`, assigns streamgage to channel 7 | *(no parameter optimization)* |
| **2. Calibration** | PSO minimizes $-(NSE_{daily} + NSE_{monthly})$ on calibration window | **2003-01-01**–**2010-12-31** (3-y warm-up from 2000) |
| **3. Verification** | Holdout simulation with global-best parameters (`verification_stage_5`) | **2012-01-01**–**2015-12-31** (`Ver_START_YEAR=2011`, `Ver_nyskip=1`) |

Settings recorded in `publication/tables/tab-calibration-run-settings.csv` (`run_label`: `proof_wb_01567500_20260518`).

---

## Frozen skill metrics (Table~\ref{tab:hydrologic-metrics})

Source: `CentralPerformance.txt` (calibration / init pool) and `verification_ensemble/m005_s7.npz` (verification global best). Full rows: `publication/tables/tab-metrics.csv`.

| Workflow stage | Daily NSE | Monthly NSE | PBIAS (\%) | Notes |
|----------------|-----------|-------------|------------|--------|
| Init. pool best (pre-PSO) | 0.413 | 0.567 | −33.1 | Best of 48 LHS particles |
| Calibration global best | 0.601 | 0.678 | −27.5 | PSO objective −1.279; stagnation after iter 24 |
| Verification global best | 0.633 | 0.213 | −40.7 | Holdout; wet bias persists on volume |

**Interpretation:** Calibration improves timing and calibration-period volume bias modestly; verification daily shape remains reasonable (NSE 0.63) but monthly skill and volume bias degrade—expected for a single-basin plausibility pilot, **not** national predictive performance.

---

## Figures

| Artifact | Path |
|----------|------|
| Manuscript 3-panel daily hydrographs | `publication/figures/final/fig-cal-proof-01567500-hydrographs-3panel.png` |
| Source init daily | `calibration_artifacts/.../SF/calibration/init/daily/7_daily.png` |
| Source cal daily | `.../SF/calibration/iter_0024/daily/7_daily.png` |
| Source ver daily | `.../SF/verification/VerificationEnsemble_daily.png` |

Regenerate: `python3 publication/analysis/scripts/assemble_cal_proof_hydrographs.py`

---

## Manuscript framing (fixed)

- **Hydrologic plausibility demonstration** — not universal predictive skill.
- **Not a regional validation study** — single proof basin outside the three structural showcase tiers.
- **Infrastructure remains the core contribution** — this basin supports credibility that packages can be exercised through initialization, calibration, and split-sample verification.

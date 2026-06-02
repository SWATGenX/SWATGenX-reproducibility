# Calibration / validation — source map (ModelProcessing + web hooks)

**Scope:** Map where SWATGenX runs **streamflow-driven PSO calibration** and **holdout verification** today.  
**Audience:** Authors preparing `calibration-plan.md`, `calibration-data-availability.md`, and execution branches.  
**Non-scope:** MODFLOW/MODGenX archived PSO (`MODFLOW/MODGenX/archive/`) — separate stack unless explicitly revived.

---

## Primary entry points

| Entry | Path | Role |
|-------|------|------|
| **CLI (recommended for reproducible pilots)** | `ModelProcessing/main.py` | Parses `--config` JSON **or** builds `ModelConfig` from flags; instantiates `ProcessingProgram` and calls `SWATGenX_SCV()`. |
| **Shell orchestration (init → cal → val)** | `ModelProcessing/init_cal_val.sh` | Wraps `initialize_model` + `main.py`; documents env overrides (`CAL_POOL_SIZE`, `MAX_CONCURRENT`, `MAX_ITERATIONS`, …). |
| **Web / Celery** | `web_application/app/swatgenx_tasks.py` (`MODELPROCESSING_SCRIPT_PATH` → `init_cal_val.sh`, template `ModelProcessing/settings.json`) | Merges user **calibration_settings** into JSON; may cap `max_concurrent` vs host CPU. |
| **One-off tests** | `ModelProcessing/calibration_test.sh`, `ModelProcessing/verification_test.sh` | Thin wrappers for local QA. |

**Calibration entry (code):** `ProcessingProgram.SWATGenX_SCV()` in `ModelProcessing/ModelProcessing/processing_program.py` — branches on `sensitivity_flag`, `calibration_flag`, `verification_flag`; calibration path calls `PSO_optimization()` after problem setup.

**Verification entry:** Same `SWATGenX_SCV()` with `verification_flag=True` (and optionally `calibration_flag=False` for verification-only reuse of `best_solution_*`).

---

## PSO implementation

| Module | Path | Notes |
|--------|------|------|
| Optimizer core | `ModelProcessing/ModelProcessing/PSO_calibration.py` | `PSOOptimizer`: inertia schedule, multiprocessing pool per iteration (`run_pso_iteration_self_healing_pool`), self-healing retries for failed particles. |
| Orchestration | `ModelProcessing/ModelProcessing/processing_program.py` | `PSO_optimization()` builds `PSOOptimizer`, optional warm start, `tell` / `ask`, `save_final_results`. |
| Benchmark harness | `ModelProcessing/ModelProcessing/pso_benchmark.py` | Optional performance experiments. |

---

## Objective function (what is actually minimized)

| Piece | Path | Contract |
|-------|------|------------|
| Wrapper | `ModelProcessing/ModelProcessing/evaluation.py` — `simulate_and_evaluate_swat_model_wrapper` | Builds `SwatModelEvaluator`, runs SWAT+ exe in copied `Scenario_*` tree, returns scalar. |
| Objective | `SwatModelEvaluator.model_evaluation` → `cal_streamflow_obj_val` | For each `streamflow_data/*.csv`, returns **daily NSE + monthly NSE** (sum). `model_evaluation` **negates the sum** for minimization. |
| Failure tokens | Same file (module docstring) | `9999` (`no_value`) for missing/invalid runs; `0` if obs empty or **>10% gaps**; **raises** `RuntimeError` if all simulated flows are zero. |
| Other metrics | `calculate_metrics` | **NSE, MAPE, PBIAS, RMSE, KGE** for logging/plots; **not** in the scalar objective unless code changes. |

**Observation ingestion:** CSV under  
`{BASE_PATH}/SWATplus_by_VPUID/{VPUID}/{LEVEL}/{NAME}/streamflow_data/*.csv`  
read by `read_observed_data`; dates filtered to `[START_YEAR+nyskip, END_YEAR]` (calibration) or `[Ver_START_YEAR+Ver_nyskip, Ver_END_YEAR]` (verification). Gauge filenames follow **`{swat_unit}_{usgs_site_no}.csv`** (e.g. `21_02295013.csv` → SWAT channel **21**); objective code uses the leading integer as `unit` and falls back to `channel-lte.cha` GIS mapping when needed.

**Simulation output (NetCDF, calibration default):** Each PSO / verification SWAT+ run writes **`channel_sd_day.nc`** in the particle `Scenario_*` workspace (cwd = scenario `TxtInOut`). The objective loader is `ModelProcessing/ModelProcessing/channel_sd_output.py` — `load_channel_sd_day()` reads `flo_out` from NetCDF variable **`v41`** (0-based column index **40**, same packing as `channel_sd_day.txt`). Dates come from NC data variables **`yrc`**, **`mo`**, **`day_mo`** (preferred over the CF `time` coordinate when `nyskip > 0`). `flo_out` is **m³/s**; evaluation converts to cfs with `cms_to_cfs` before NSE. Minimum **30** overlapping days after merge.

**Print setup (written before each cal/verify batch):** `ProcessingProgram.update_model_time_and_printing()` calls `ensure_calibration_nc_print()` in `ModelProcessing/ModelProcessing/print_prt.py`:

| File | Role |
|------|------|
| `print.prt` | `cdfout=y`, `csvout=n`, `dbout=n`; only **`channel_sd`** **daily** enabled (monthly/yearly/avann off for smaller NC). |
| `print_filter.prt` | Optional; lists 1-based SWAT channel indices to retain. Built from `streamflow_data/*.csv` via `discover_streamflow_channel_units()`. Omit file = all channels (not used in production cal). |
| `lsunit_wb` / map export | **`activate_ET_print()`** runs only in the **verification** stage (not during PSO calibration). |

**SWAT+ binary:** `codes/bin/swatplus` (fork with NetCDF + `print_filter`; see `swatplus_perf/` parity harness). `SWATPLUS_EXE` in `ModelProcessing/ModelProcessing/paths.py`.

**Pilot evidence (2026-05-28):** `0310/huc12/02295013` — PSO calibration + holdout verification completed with NC + filter (channel **21**); verification objective ≈ **−0.74** (daily NSE ≈ 0.40, monthly ≈ 0.34 on holdout window).

**Legacy TXT:** `channel_sd_day.txt` is no longer read by `model_evaluation`. Parity tooling may still compare TXT vs NC (`swatplus_perf/scripts/compare_channel5_streamflow.py`, `verify_nc_vs_txt.py`).

---

## Parameter handling

| Step | Path | Behavior |
|------|------|----------|
| Canonical cal file | `bin/cal_parms_{MODEL_NAME}.cal` (`ModelProcessing/ModelProcessing/paths.py` — `cal_parms_source`) | Copied to `{model_base}/cal_parms_{MODEL_NAME}.cal` at run start (`copy_original_cal_file`). |
| Parse problem | `read_control_file` (via `ModelProcessing.utils` / `swat_io`) | `problem['names']`, `problem['bounds']`, `param_files`, `operation_types`, `absolute_bounds`. |
| Apply parameters | `ModelProcessing/ModelProcessing/utils.py` — `write_model_parameters` | `replace|multiply|add|percentage|power` per row; optional `abs_min`/`abs_max` clamps. |

**Active web model name:** `SWAT_MODEL_Web_Application` → `bin/cal_parms_SWAT_MODEL_Web_Application.cal`.

---

## Visualization & reports

| Output | Location (typical) | Producer |
|--------|-------------------|----------|
| Hydrographs (daily/monthly) | `figures_{MODEL_NAME}/SF/{calibration|verification}/...` | `ModelProcessing/visualization.py` via evaluator when plot policy allows. |
| Global best trace | `figures_{MODEL_NAME}/GlobalBestImprovement.png` | PSO calibration |
| Performance log | `{model_base}/CentralPerformance.txt` | `write_performance_scores` — tab-separated NSE/MPE/PBIAS/RMSE/KGE per station/time_step/stage. |
| Best / local-best vectors | `best_solution_{MODEL}.txt`, `local_best_solution_{MODEL}.txt` under `calibration_artifacts_root` (or `model_base` for `Default` scenario) | PSO + checkpoints |
| Verification ensemble | `verification_ensemble/*.npz` | Optional slices when `verification_member_index` set |
| Web metrics digest | `swatgenx_tasks.py` helpers parsing `CentralPerformance.txt` | Email/API summaries — not archival science by themselves. |

---

## Execution settings compatibility

Publication intent (**10** CPU cores available, **6** concurrent SWAT+ processes, **48** particles, **50** iterations) maps to existing configuration surfaces — **no production code edits** are required to express these values at runtime.

| Setting | Where configured | Notes |
|---------|------------------|--------|
| **Particle count** | `ModelConfig.cal_pool_size` | CLI: `ModelProcessing/main.py` `--cal-pool-size`. JSON config key `cal_pool_size`. Shell: `init_cal_val.sh` env **`CAL_POOL_SIZE`** (see script header defaults). |
| **Iteration cap** | `ModelConfig.max_cal_iterations` | CLI: `--max-iterations`. JSON: `max_cal_iterations` / merged web template keys as used by tasks. Shell env **`MAX_ITERATIONS`**. |
| **Concurrent simulations** | `ModelConfig.max_concurrent_processes` | CLI: `--max-concurrent`. JSON: `max_concurrent_processes` / `max_concurrent`. Shell env **`MAX_CONCURRENT`**. `PSO_calibration.py` caps active futures at this value per iteration. |
| **CPU cores** | Host / Celery worker | **Not** a dedicated `ModelConfig` field; web path uses `_cap_max_concurrent` in `swatgenx_tasks.py` to avoid oversubscription vs `cpu_count()`. A **10-core** machine with **`max_concurrent_processes=6`** is valid. |
| **Calibration / validation years** | `ModelConfig` + CLI flags | `main.py`: `--start-year`, `--end-year`, `--nyskip`, `--ver-start-year`, `--ver-end-year`, `--ver-nyskip`; mirrored in JSON configs passed from the web app. |
| **Station list** | `streamflow_data/*.csv` | One file per gage; stem = USGS `site_no`. Optional `ModelConfig.excluded_stations` to drop IDs from the objective. |
| **Parameter file** | `bin/cal_parms_{MODEL_NAME}.cal` | Web model uses `SWAT_MODEL_Web_Application` → `bin/cal_parms_SWAT_MODEL_Web_Application.cal` in repo. |
| **Output root** | `ProcessingProgram` / `paths.py` | Under `{BASE_PATH}/SWATplus_by_VPUID/{VPUID}/{LEVEL}/{NAME}/` (and `calibration_artifacts/...` when scenario is non-Default); **environment-specific** `BASE_PATH`. |

**Parity reminder:** Web-initiated runs merge `ModelProcessing/settings.json` with per-request `calibration_settings`; log the **effective JSON** for reproducibility audits.

---

## Dependencies & runtime assumptions

- **SWAT+ binary:** `SWATPLUS_EXE` from `paths.py` (default `…/codes/bin/swatplus`); must be NC-capable build.
- **Climate via `pcp_path`:** Each PSO scenario `prepare_scenario_files` skips `r<row>_c<col>.{pcp,tmp,slr,hmd,wnd}` data files during `copytree` and patches `file.cio` with quoted `<NAME>/PRISM/` paths so the Fortran reads climate from the shared model `PRISM/` (≈ tens of MB saved per particle, bit-exact `channel_sd_day.nc` parity). Disable with `SWATGENX_DISABLE_PCP_PATH=1`; override location with `SWATGENX_PRISM_DIR=…`. Fallback to legacy copy when `<NAME>/PRISM/` is missing or empty. Implementation: `ModelProcessing/climate_paths.py`.
- **Python stack:** GeoPandas/pandas/numpy/**xarray**/netCDF4; multiprocessing; `skopt.space.Real` for bounds.
- **Disk layout:** `ModelConfig` defaults `BASE_PATH` to `${SWATGENX_USER_PATH}{username}` unless overridden — **environment-specific**.
- **Timeouts:** `define_timeout` in `evaluation.py` scales with HRU count; calibration floor **3 h**, verification floor **8 h** per run (wall-clock guard).

---

## Risks / unknowns (planning)

1. **Objective ≠ full metric suite:** PSO score is **NSE_daily + NSE_monthly** only.  
2. **Gap policy:** \>10% missing obs → station score `0` — always window-check before PSO.  
3. **NWIS vs operational CSV:** Audit used live NWIS; local CSV export must match dates/units expected by `read_observed_data`.  
4. **Single-gage small basin:** Objective sums all `streamflow_data` CSVs — keep **one** consistent gage unless multi-site behavior is intended.  
5. **`recharg_output_*` path:** Verification may log `Error writing verification performance` if `recharg_output_{MODEL}/` is absent (MODFLOW/gwflow layout); streamflow verification and ensemble plots still complete.  
6. **NC `obj_id` / `gis_id`:** Often NaN in current binary; rely on `print_filter.prt` channel list + `unit` column from loader, with `channel-lte.cha` fallback.

---

## Quick start — Small Florida pilot (after execution branch)

1. Confirm model tree exists for `0308/huc12/02239501` + `SWAT_MODEL_Web_Application`.  
2. Confirm `streamflow_data/{site_no}.csv` (daily) for audited windows.  
3. Run `ModelProcessing/main.py` with publication settings from `tab-calibration-run-settings.csv`.  
4. Archive `CentralPerformance.txt`, `best_solution_*.txt`, and selected plots for supplement evidence.

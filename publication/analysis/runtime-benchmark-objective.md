# Objective 5 — SWAT+ simulation runtime benchmark

**Manuscript objective:** Present measured **SWAT+ simulation and calibration-time performance** for representative SWATGenX-built models, distinct from **model-generation wall time** (Tab-Runtime, Objective 3 context).

**Public reference (canonical):** https://www.swatgenx.com/swat-plus-runtime-benchmark  
(Legacy alias `/swat-plus-calibration-runtime-benchmark` redirects here.)

---

## Scope boundary

| Topic | Objective / table | What it measures |
|-------|-------------------|------------------|
| Package **generation** (GIS + weather + export) | Tab-Runtime; three locked showcase basins | End-to-end build wall time on one host |
| **SWAT+ simulation** runtime | **Objective 5**; this document | Seconds per simulated day, compiler matrix, HRU scaling |
| Hydrologic **cal/val/sensitivity** | Objective 4; basin `02297600` | NSE/KGE/Morris μ* — not performance benchmarking |

Objective 5 does **not** claim cross-tool superiority (HAWQS, manual builds, etc.). It documents reproducible measurement methodology and curated results already published on the site.

---

## Source artifacts

| Layer | Path |
|-------|------|
| **Frontend catalog** | `web_application/frontend/src/data/swatPlusRuntimeBenchmarkCatalog.json` (`generatedAt`: 2026-05-31) |
| **Page** | `web_application/frontend/src/pages/marketing/SwatPlusRuntimeBenchmark.js` |
| **Panel / charts** | `web_application/frontend/src/components/marketing/SwatPlusRuntimeBenchmarkPanel.jsx` |
| **Raw benchmarks** | `swatplus_perf/benchmark-results/_archive/accepted/` (gitignored runs; curated copies) |
| **Regenerate catalog** | `swatplus_perf/scripts/export_1yr_benchmark_catalog.py`, `export_hru_scaling_catalog.py`, `export_runtime_benchmark_catalog.py` |

---

## Benchmark model set (site page — not the JAWRA structural trio)

| Tier | Model ID | Label | HRUs | Channels |
|------|----------|-------|------|----------|
| S | `03080102` | Oklawaha (FL) | 473 | 45 |
| M | `09471300` | Upper San Pedro (AZ) | 11,284 | 350 |
| L | `03100101` | Peace River HUC-8 | 94,303 | 8,181 |

**Methodology (from catalog):** 365 simulated days (calendar 2021); Intel ifx `release_o3_ipo`; wall-clock seconds and seconds/simulated-day; parity checks on `channel_sd_day.nc`; AMD EPYC 7282 guest (10 vCPU).

Additional panels: compiler variant matrix, HRU scaling ladder, calibration-time estimates where measured.

---

## Manuscript deliverables (Objective 5)

| Deliverable | Target | Status |
|-------------|--------|--------|
| **Tab-RuntimeBenchmark** | `publication/tables/tab-runtime-benchmark.csv` | Done (2026-05-31) |
| **Print scope / NC vs TXT / compiler / HRU / VTune tables** | `tab-runtime-benchmark-*.csv` | Done |
| **Fig-RuntimeBenchmark** | `fig-runtime-benchmark-hru-scaling.png`, `fig-runtime-benchmark-print-scope.png` | Done |
| **Results §** | `results.tex` § Objective 5 (methodology + five subsubsections) | Done |
| **Discussion §** | `discussion.tex` § Simulation runtime benchmark | Done |
| **Data availability** | URL + catalog JSON + export scripts | Done |

Export: `python3 publication/analysis/scripts/export_benchmark_objective5.py`  
LaTeX emit: `python3 publication/analysis/scripts/emit_tab_runtime_benchmark_suite_tex.py`  
Figures: `python3 publication/analysis/scripts/render_benchmark_figures.py`

**Do not** merge Objective 5 numbers into Tab-Runtime (generation) without explicit relabeling.

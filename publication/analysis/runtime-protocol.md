# Runtime profiling protocol (SWATGenX publication)

**Scope:** Phase-resolved timing for **reproducibility and transparency**, not product benchmarking. This document governs pilot and future locked-basin timing runs under `publication/analysis/scripts/`.

## Non-goals

- No comparison to HAWQS, QSWAT+, or manual workflows.
- No claim of fastest, cheapest, or universally representative wall time.
- No claim that timings transfer across hardware, storage backends, or network paths.

## Phase categories

| `phase_group` | Meaning |
|---------------|--------|
| `external_acquisition` | Time dominated by **remote or service-mediated** acquisition: national data downloads, Google Earth Engine exports, reading large third-party archives over slow or remote mounts, NSRDB extraction from operator-hosted stores, etc. **Excluded** from `core_processing_time`. |
| `local_input_preprocessing` | **Local** preparation after inputs exist on disk: CRS checks, resampling or warping **without** a new GEE session, clipping, validation, small derived grids. **Included** in `core_processing_time` when `include_in_processing_total=Y`. |
| `nhdplus_hr_preprocessing` | NHDPlus HR **topology and attribute harmonization** used for SWAT+ routing (e.g. preprocessing stage on unpacked HR vectors). **Included** in core total when flagged `Y`. |
| `hydrography_topology_construction` | Construction of watershed / channel geometry used by SWAT+ from prepared inputs (e.g. SWAT+ shape generation from HR layers). **Included** in core total. |
| `swatplus_project_assembly` | QSWAT+ delineation / HRU build, raster prep tied to the project, SWAT+ Editor import and simulation steps that produce the runnable tree. **Included** in core total. |
| `qa_manifest_logging` | Meta files, simulation output verification, and similar **package integrity** steps that are part of the official project deliverable. **Included** in core total when flagged `Y`. |
| `packaging` | ZIP or report bundling **only** when defined as part of the official deliverable for that run; otherwise `include_in_processing_total=N` with a note. |

## `core_processing_time`

Sum of `elapsed_seconds` for rows where **`include_in_processing_total=Y`** for the run. This is **processing time after inputs are available locally**, not a full end-to-end “user waited for the internet” metric.

## `external_acquisition_time`

Sum of `elapsed_seconds` for rows where **`phase_group=external_acquisition`** (regardless of `include_in_processing_total`, which should be `N` for those rows).

## `cache_state` (per run)

| Value | Meaning |
|-------|--------|
| `cold_external` | Run expected to hit remote/service paths (e.g. first-time GEE NLCD, first HR download for VPU). |
| `warm_local` | Inputs and VPU caches already present on fast local disk; minimal remote work. |
| `mixed` | Some layers warm, some cold. |
| `unknown` | Not classified. |

## `storage_mode` (per run)

| Value | Meaning |
|-------|--------|
| `low_storage_on_demand` | Mostly on-demand reads without a full local mirror of national layers. |
| `local_cache` | Significant read-after-write cache under operator `USER_PATH` / GenXAppData-style trees. |
| `full_local_mirror` | Full or near-full national mirrors available locally. |
| `unknown` | Not classified. |

## Environment fields to record

Recorded in `tab-runtime-phases.csv` / JSONL merge step where applicable:

- `git_sha` — short SHA of the repository checkout.
- `hostname` — machine host name (no internal FQDN secrets required; may be redacted in public exports).
- `cpu_count` — `os.cpu_count()` or similar.
- `ram_gb` — best-effort from `/proc/meminfo` on Linux when readable; else empty / `unknown`.
- `environment_id` — optional operator-defined label (e.g. env var `SWATGENX_RUNTIME_ENVIRONMENT_ID`); never store credentials.

## Pilot run procedure

1. Use a **single** locked row from `publication/tables/tab-model-complexity.csv` (`status=locked_from_inventory`, `level=huc12`). Default pilot `--model-id` is Small `0308/usgs_station/02239501`; pass another locked `model_id` (e.g. Medium `0204/usgs_station/01451800`, Large `1107/usgs_station/07174000`) for tier-specific timing.
2. Set `SWATGENX_RUNTIME_PROFILE=1` and `SWATGENX_RUNTIME_JSONL` to a JSONL path (pilot script sets an absolute path under `--runtime-runs-dir` or the default `runtime-runs/`).
3. Run `python3 publication/analysis/scripts/time_locked_model_generation.py --model-id … --run-id …` from the **repository root**, with `PYTHONPATH` including `SWATGenX` as required by existing command modules. If the process user cannot write under `publication/analysis/runtime-runs/`, pass `--runtime-runs-dir` (or `SWATGENX_RUNTIME_RUNS_DIR`) to a writable directory; the script then defaults CSV append to `<that-dir>/tab-runtime-phases-append.csv` unless you set `--runtime-phases-csv` / `SWATGENX_RUNTIME_PHASES_CSV` or `--skip-csv-append`. To always use the canonical table path from a service account, pass `--runtime-phases-csv` explicitly (requires that path to be writable) or merge later.
4. On **successful** completion, append flattened rows to the chosen runtime phases CSV (canonical path by default) and write `<run_id>-summary.md` next to the JSONL.
5. Do not overwrite prior JSONL or CSV rows unless `--force` is passed (pilot script policy).

## Known limitations

- Some boundaries (e.g. entire `check_configuration`) can bundle **both** acquisition and local validation; finer splits live in `generate_geospatial_vpuid.py` where practical.
- PRISM/NSRDB “external” time includes **large sequential reads** from operator-chosen archives; that is not the same as “HTTP download” only.
- Celery, web timeouts, and concurrent users are **out of scope** for this pilot script (single-process invocation).

## Troubleshooting (permissions)

- **GenXAppData / gSSURGO / NHD caches:** The OS user running the pilot must be able to create directories under your configured data root (e.g. `GenXAppData/gSSURGO/VPUID/<vpuid>`). A login user often lacks write access if caches were populated by `www-data`; align user and ownership, or run as the same user that owns the tree.
- **NHDPlus HR `zipped/` and `unzipped_*`:** First-time HR acquisition writes under `GenXAppData/NHDPlusHR/` (including `zipped/*.zip`). If a partial zip exists and is owned by another user, `www-data` will get “permission denied” on download. Remove or `chown` the conflicting path, or run as the user that owns `GenXAppData`.
- **`publication/analysis/runtime-runs/*.jsonl`:** Files are created by whichever user runs the script. A service user often **cannot** write inside the git checkout. Use `--runtime-runs-dir /path/writable/by/that/user` or set `SWATGENX_RUNTIME_RUNS_DIR` (the pilot sets `SWATGENX_RUNTIME_JSONL` to an absolute path under that directory). If you first run as your login user and later run `sudo -u www-data … --force`, removal of an existing JSONL in the default directory can fail; `sudo rm` the stale file, use a new `--run-id`, or keep one consistent user.
- **CSV append:** Successful runs append to `publication/tables/tab-runtime-phases.csv` when using the default runs directory. With a custom `--runtime-runs-dir`, the pilot defaults to `<that-dir>/tab-runtime-phases-append.csv` so service users need not write under `publication/tables/`. Override with `--runtime-phases-csv`, `SWATGENX_RUNTIME_PHASES_CSV`, or `--skip-csv-append`.
- **PRISM years:** If CONUS PRISM archives stop before your configured end year, station CLI validation fails and `SWATGenXCommand` now **raises** (no longer treats stale `simulation.out` as success). Refresh PRISM data before relying on a timing run.

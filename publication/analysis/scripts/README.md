# Analysis scripts (placeholder plan)

**Status:** path checks and **draft** basin maps are scripted; other generators remain planned. Do **not** invent runtime, CPU, RAM, or environment values in tables.

## Conventions

- **Locked basins** — `0308/huc12/030801020804` (Small, FL), `1505/huc12/09471300` (Medium, AZ), `0310/huc8/03100101` (Large, FL HUC8). See [`../evaluation-protocol.md`](../evaluation-protocol.md).
- **Showcase user** — `admin` (per protocol “official outputs”).
- **`USER_PATH`** — Default in many installs: `${SWATGENX_USER_PATH}` (override via env when running scripts on another machine).
- **Workspace root pattern** —  
  `{USER_PATH}/admin/SWATplus_by_VPUID/<vpuid>/huc12/<site_no>/<MODEL_DIR>/`  
  where `<vpuid>` and `<site_no>` come from splitting `model_id` (`vpuid/huc12/site_no`), and `<MODEL_DIR>` is typically the web-application SWAT+ workspace folder (e.g. `SWAT_MODEL_Web_Application` — **confirm on disk** before scripting; align with `resolve_swat_model_workspace_base` in `web_application/app/model_utils.py` when wiring a real script).

---

## 1. Tab-ModelComplexity → manuscript-ready LaTeX tabular

**Inputs:** [`../../tables/tab-model-complexity.csv`](../../tables/tab-model-complexity.csv)

**Script:** [`emit_tab_model_complexity_tex.py`](emit_tab_model_complexity_tex.py)

**Behavior:**

- Reads rows with `status=locked_from_inventory` (Small → Large sort).
- Writes [`../../tables/generated/tab-model-complexity.tex`](../../tables/generated/tab-model-complexity.tex) — a **booktabs** `tabular` fragment (no `table` float): tier, model ID, state, area (km$^2$), HRUs, channels, subbasins, catchments, lakes, DEM (m). Count columns are copied verbatim from the CSV; area and DEM are formatted to **two decimal places** for the manuscript. Blank CSV cells render as `{---}` in LaTeX (including blank lake counts; the script does **not** assert ``0 or not present'' without a verified CSV field).
- **Does not** add hydrologic metrics or runtime columns.

**Build:** `publication/tables/generated/` is gitignored except `.gitignore`; run this script **before** `pdflatex` so `\input{../tables/generated/tab-model-complexity}` resolves (see **Results** in `publication/manuscript/sections/results.tex`).

**Validation:** Count columns in the generated `.tex` must match the CSV exactly; area and DEM must match the CSV values rounded to two decimals. Amend the CSV first if source numbers change.

**Usage (from repo root):**

```bash
python3 publication/analysis/scripts/emit_tab_model_complexity_tex.py
python3 publication/analysis/scripts/emit_tab_model_complexity_tex.py --csv publication/tables/tab-model-complexity.csv --out publication/tables/generated/tab-model-complexity.tex
python3 publication/analysis/scripts/emit_tab_model_complexity_tex.py --help
```

---

## 2. Locate official admin showcase workspaces

**Script:** [`print_locked_basin_paths.py`](print_locked_basin_paths.py) — **read-only** path check.

**Behavior:**

- Reads rows with `status=locked_from_inventory` from [`../../tables/tab-model-complexity.csv`](../../tables/tab-model-complexity.csv).
- Parses each `model_id` as `vpuid/level/site_no` and resolves  
  `{USER_PATH}/{username}/SWATplus_by_VPUID/{vpuid}/{level}/{site_no}/{SWAT_SHOWCASE_MODEL_DIR}/`  
  (defaults: `USER_PATH=${SWATGENX_USER_PATH}`, `EXAMPLE_MODELS_USERNAME=admin`, `SWAT_SHOWCASE_MODEL_DIR=SWAT_MODEL_Web_Application`).
- Prints whether the workspace root and `Watershed/Shapes` exist, and whether these exist:  
  `SWAT_plus_streams.shp`, `SWAT_plus_watersheds.shp`, `SWAT_plus_subbasins.shp` (**required**);  
  `SWAT_plus_lakes.shp` (**optional** — reported but does not affect exit code).
- **Does not** modify files or generate figures.
- **Exit code:** `0` if all required paths exist; `1` if the CSV is missing, no locked rows, or any required path is missing.

**Usage (from repo root):**

```bash
python3 publication/analysis/scripts/print_locked_basin_paths.py
USER_PATH=/path/to/Users EXAMPLE_MODELS_USERNAME=admin python3 publication/analysis/scripts/print_locked_basin_paths.py
python3 publication/analysis/scripts/print_locked_basin_paths.py --help
```

Optional flags: `--csv`, `--user-path`, `--username`, `--model-dir` (see `--help`).

---

## 3. Fig-ExampleBasinMaps — static maps (no web tiles)

**Spec:** [`../../figures/figure-specifications.md`](../../figures/figure-specifications.md) — **Fig-ExampleBasinMaps**

**Script:** [`render_example_basin_maps.py`](render_example_basin_maps.py)

**Shared path logic:** [`_locked_basin_paths.py`](_locked_basin_paths.py) (also used by [`print_locked_basin_paths.py`](print_locked_basin_paths.py)).

**Inputs (per basin):**

- Same CSV and workspace resolution as §2 (`USER_PATH`, `EXAMPLE_MODELS_USERNAME`, `SWAT_SHOWCASE_MODEL_DIR`).
- **Required:** `Watershed/Shapes/SWAT_plus_streams.shp`, `SWAT_plus_subbasins.shp`.
- **Optional:** `SWAT_plus_lakes.shp` (drawn when the file exists).
- **No web basemaps** — only local shapefile layers (GeoPandas + Matplotlib).

**Behavior:**

- Reads `status=locked_from_inventory` rows; orders panels Small → Medium → Large when `--layout combined`.
- Renders subbasin polygons (light fill), optional lake polygons, stream polylines; draft mode lists tier, `model_id`, state, counts on the map.
- **Draft mode (default):** writes **`publication/figures/drafts/`** — per-tier PNG/PDF **or** one combined multi-panel file; filenames `example-basin-map-draft-*`; includes a visible “Draft” banner.
- **Manuscript mode (`--final --layout combined`):** writes **`publication/figures/final/`** (`fig-example-basin-maps-combined-<n>panel.png`), default **300 dpi**. **Single row:** each basin is **independently zoomed** (square viewport centered on merged extent; not equal-scale across panels); light subbasin fill, readable streams (extra weight for the Kansas tier), lakes where present; journal titles \textbf{(a)--(c)}; light panel frames; per-panel scale bars; compact shared legend; **no** on-map numeric stats (use **Tab-ModelComplexity**). **`--final` + `separate`:** one file per basin with optional stats line.
- Writes a sidecar **`*-metadata.json`** next to the images (paths relative to repo root, CSV echo, layout, dpi, `final` flag). Combined layout filenames use `<stem>-combined-<n>panel.<ext>`.

**Dependencies:** `geopandas`, `matplotlib`, and a working GDAL/Fiona stack for ESRI Shapefile reads.

**Usage (from repo root):**

```bash
# After §2 passes (workspaces and shapefiles exist on disk):
python3 publication/analysis/scripts/render_example_basin_maps.py
python3 publication/analysis/scripts/render_example_basin_maps.py --layout combined --dpi 200
python3 publication/analysis/scripts/render_example_basin_maps.py --final --layout combined
python3 publication/analysis/scripts/render_example_basin_maps.py --final --layout combined --dpi 200
python3 publication/analysis/scripts/render_example_basin_maps.py --out-dir publication/figures/drafts --format pdf
python3 publication/analysis/scripts/render_example_basin_maps.py --help
```

Confirm **`print_locked_basin_paths.py` exits 0** before running the renderer (renderer requires streams + subbasins; it does not require `SWAT_plus_watersheds.shp` for drawing).

---

## 4. Fig-NHDWorkflow (small Florida basin)

**Spec:** [`../../figures/figure-specifications.md`](../../figures/figure-specifications.md) — **Fig-NHDWorkflow**

**Primary basin:** `0308/huc12/02239501` (Small, FL).

**Two allowed tracks (pick one per submission art direction):**

| Track | Description |
|-------|-------------|
| **A — Schematic** | Mermaid / TikZ / vector tool: swimlanes match Methods text and `documents/NHDPlus_HR_SWATPlus_Methods.md` **without** fabricating intermediate counts. |
| **B — Map / light GIS** | Use **only** exports from the Florida workspace (or frozen GeoJSON derived from the same build) for inset maps (divergence QA, lakes, etc.). Any numeric badge on the figure must match `tab-model-complexity.csv` or a one-off amendment log entry. |

**Planned script(s):** `export_nhd_workflow_geojson.py` (optional) + manual design step; or pure `fig-nhd-workflow.mmd` source under `publication/figures/sources/` (TBD).

**Do not** hand-draw topology that contradicts code.

---

## 5. Tab-Runtime — fresh timed reruns

**Inputs:** [`../../tables/tab-runtime.csv`](../../tables/tab-runtime.csv); [`../evaluation-protocol.md`](../evaluation-protocol.md) (pilot host + 2026-05-14 runs logged; full conda/container runbook row still **TBD**).

**Phase-resolved pilot (locked inventory basins):** [`runtime_recorder.py`](runtime_recorder.py) (stdlib JSONL helper) + [`time_locked_model_generation.py`](time_locked_model_generation.py). Protocol: [`../runtime-protocol.md`](../runtime-protocol.md). Flattened rows append to [`../../tables/tab-runtime-phases.csv`](../../tables/tab-runtime-phases.csv) after a successful run when using default paths; with `--runtime-runs-dir`, CSV defaults to `<dir>/tab-runtime-phases-append.csv` unless you pass `--runtime-phases-csv` / `SWATGENX_RUNTIME_PHASES_CSV` or `--skip-csv-append`. Per-phase JSONL defaults to [`../runtime-runs/`](../runtime-runs/) (gitignored except `.gitignore`) or `--runtime-runs-dir` / `SWATGENX_RUNTIME_RUNS_DIR` when the checkout is not writable by the service user. Use `--rm-site-output` to delete the target site’s `SWATplus_by_VPUID/...` directory before a timed fresh build.

```bash
# From repo root; use the project venv if system python lacks rasterio/geopandas:
/data/SWATGenXApp/codes/.venv/bin/python publication/analysis/scripts/time_locked_model_generation.py \
  --model-id 0308/huc12/02239501 --run-id 20260514-small-pilot-001

# If the process user cannot write under the repo (e.g. sudo -u www-data), JSONL + CSV + summary
# can all go under a writable dir (CSV defaults to .../tab-runtime-phases-append.csv there):
#   --runtime-runs-dir /tmp/swx-runtime-runs
# Optional: only JSONL + summary, merge table later:
#   --skip-csv-append
```

Requires write access to national data caches (e.g. `GenXAppData` trees) when VPU layers are cold. This is **artifact lifecycle / transparency** timing, not a cross-tool benchmark (see protocol).

**Planned script (aggregate table):** `time_model_generation.py` (future) — wraps the **same** generation entrypoint the product uses (or a documented subprocess), captures:

- `fresh_rerun_wall_min` (monotonic wall clock, document timezone → store UTC in `run_datetime`),
- optional `peak_ram_gb`, `cpu_count`, `worker_count` **only** from measured logs,
- `git_sha` from `git rev-parse HEAD` in the **frozen** checkout,
- `env_id` from an agreed label (conda env name, container digest path, etc.) — **never** guessed.

**Behavior:**

- After each run, patch `tab-runtime.csv` (or regenerate from a YAML run log committed beside the CSV — design choice TBD).
- Set row `status` from `pending_fresh_rerun` to a completed label only in the same change set that supplies non-`TBD` measured fields.
- **`provisional_inventory_wall_min`** remains for audit only; manuscript text uses **`fresh_rerun_wall_min`** after freeze.

---

## Dependency order (suggested)

1. Freeze runtime environment block in `evaluation-protocol.md` (git SHA, hardware, env label).  
2. Run timed jobs → update `tab-runtime.csv`.  
3. Confirm workspace paths → export / map for **Fig-ExampleBasinMaps** and optional **Fig-NHDWorkflow** track B.  
4. Regenerate **Tab-ModelComplexity** LaTeX with `emit_tab_model_complexity_tex.py` when the CSV changes (before `pdflatex` if Results includes the table).

---

## Out of scope (first manuscript pass)

## 4. Proof-basin hydrologic metrics and figure

**Spec:** proof basin `0205/huc12/01567500` — see `calibration-proof-basin-01567500.md`

| Script | Output |
|--------|--------|
| [`assemble_cal_proof_hydrographs.py`](assemble_cal_proof_hydrographs.py) | `figures/final/fig-cal-proof-01567500-hydrographs-3panel.png` |
| [`emit_tab_metrics_tex.py`](emit_tab_metrics_tex.py) | `tables/generated/tab-metrics.tex` from [`tab-metrics.csv`](../../tables/tab-metrics.csv) |

Run both before `pdflatex` when the proof-basin hydro subsection changes.

Hydrologic evaluation for the **three showcase basins** remains **off** per `evaluation-protocol.md`.

---

## 5b. Tab-Runtime → manuscript LaTeX tabular

**Inputs:** [`../../tables/tab-runtime.csv`](../../tables/tab-runtime.csv) (rows with `status=measured_scripted_rerun`); HRU column joined from [`../../tables/tab-model-complexity.csv`](../../tables/tab-model-complexity.csv).

**Script:** [`emit_tab_runtime_tex.py`](emit_tab_runtime_tex.py)

**Output:** [`../../tables/generated/tab-runtime.tex`](../../tables/generated/tab-runtime.tex) — used by `\input` in **Results** (`Table~\ref{tab:runtime}`).

```bash
python3 publication/analysis/scripts/emit_tab_runtime_tex.py
```

---

## 5c. Tab-ToolContrast → manuscript LaTeX tabular

**Inputs:** [`../../tables/tab-tool-contrast.csv`](../../tables/tab-tool-contrast.csv)

**Script:** [`emit_tab_tool_contrast_tex.py`](emit_tab_tool_contrast_tex.py)

**Output:** [`../../tables/generated/tab-tool-contrast.tex`](../../tables/generated/tab-tool-contrast.tex) — Discussion Table~\ref{tab:tool-contrast}.

```bash
python3 publication/analysis/scripts/emit_tab_tool_contrast_tex.py
```

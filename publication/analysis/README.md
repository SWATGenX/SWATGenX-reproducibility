# Publication analysis — JAWRA evaluation workspace

This folder holds **evaluation protocol**, **basin inventories**, and **planned** analysis scripts for manuscript tables and figures. It does **not** contain final figure PDFs (those live under [`../figures/`](../figures/) when produced).

## Locked basins (Phase 1)

Authoritative narrative and policy: [`evaluation-protocol.md`](evaluation-protocol.md) (**lock date 2026-05-13**).

| Tier | `model_id` | NWIS `site_no` | VPUID | State (postal) |
|------|------------|----------------|-------|----------------|
| Small | `0308/huc12/030801020804` | 0310 | 030801020804 | FL |
| Medium | `1505/huc12/09471300` | 1505 | 09471300 | AZ |
| Large | `0310/huc8/03100101` | 0310 | 03100101 | FL (HUC8) |

Structural counts for tables: [`../tables/tab-model-complexity.csv`](../tables/tab-model-complexity.csv) (`locked_from_inventory`). Runtime summaries (pilot timed reruns, 2026-05-14): [`../tables/tab-runtime.csv`](../tables/tab-runtime.csv); phase-level rows: [`../tables/tab-runtime-phases.csv`](../tables/tab-runtime-phases.csv).

Disk inventory narrative (showcase user `admin`): [`example-models-inventory.md`](example-models-inventory.md). Machine-readable rows: [`example-models-inventory.csv`](example-models-inventory.csv).

## Planned artifact generation (overview)

Detailed steps and script placeholders: [`scripts/README.md`](scripts/README.md).

Summary:

1. **Tab-ModelComplexity (manuscript LaTeX fragment)** — Run `publication/analysis/scripts/emit_tab_model_complexity_tex.py` to write `publication/tables/generated/tab-model-complexity.tex` (gitignored except `generated/.gitignore`); `\input` from `sections/results.tex` after regenerating from [`../tables/tab-model-complexity.csv`](../tables/tab-model-complexity.csv).
2. **Official workspaces** — Resolve paths under `{USER_PATH}/admin/SWATplus_by_VPUID/<vpuid>/huc12/<site_no>/…` per [`evaluation-protocol.md`](evaluation-protocol.md); confirm `SWAT_MODEL_Web_Application` (or current model folder name) via app resolver or directory listing on the frozen host.
3. **Fig-ExampleBasinMaps** — From exported **basin / subbasin / stream** vectors in each workspace’s `Watershed/Shapes/` (names per internal README / `NHD_SWATPlus_Extractor` outputs, e.g. `SWAT_plus_streams.shp`, `SWAT_plus_subbasins.shp`, watershed polygons as applicable); same CRS across panels; outlet marker tied to NWIS `site_no` for HUC12 station runs.
4. **Fig-NHDWorkflow** — Prefer **small Florida** basin (`0308/huc12/030801020804`, catalog `03080102`): either (a) diagram-only from frozen rule checklist + protocol text, or (b) light-weight GeoJSON / static maps from **that** workspace’s intermediate QA exports if present, without claiming counts not in `tab-model-complexity.csv` / workspace. No final figure committed until art direction is set (see [`../figures/figure-specifications.md`](../figures/figure-specifications.md)).
5. **Tab-Runtime** — Pilot **measured_scripted_rerun** rows (2026-05-14) populate `publication/tables/tab-runtime.csv`; do **not** treat `provisional_inventory_wall_min` as final. Future re-runs should append phase rows and amend CSV notes; a full conda/container digest in `evaluation-protocol.md` remains follow-on work.
6. **Phase-resolved pilot timing** — Protocol and CSV schema: [`runtime-protocol.md`](runtime-protocol.md), [`../tables/tab-runtime-phases.csv`](../tables/tab-runtime-phases.csv). Raw JSONL defaults under [`runtime-runs/`](runtime-runs/) (gitignored) or use `--runtime-runs-dir` (then CSV append defaults next to JSONL unless overridden). Use `--runtime-phases-csv` or `--skip-csv-append` when you need a different layout. Pilot driver: [`scripts/time_locked_model_generation.py`](scripts/time_locked_model_generation.py) (any `huc12` row with `locked_from_inventory` in `tab-model-complexity.csv`; use the repo `.venv` with GDAL/rasterio; requires write access to national data trees such as `GenXAppData` on first VPU build, including `NHDPlusHR/zipped/`). **Not** a performance benchmark; see protocol non-goals.

## Scripts

See [`scripts/README.md`](scripts/README.md). Run **`scripts/print_locked_basin_paths.py`** to verify locked-basin workspaces; run **`scripts/emit_tab_model_complexity_tex.py`** before building the manuscript when Results includes the generated table.

## Related manuscript assets

- Evidence wiring: [`../evidence-matrix.md`](../evidence-matrix.md)  
- Figure contracts: [`../figures/figure-specifications.md`](../figures/figure-specifications.md)  
- Table contracts: [`../tables/table-specifications.md`](../tables/table-specifications.md)

**Do not** invent wall times, CPU counts, RAM, or environment IDs; follow `evaluation-protocol.md` and `tab-runtime.csv` notes.

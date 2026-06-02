# Table specifications — SWATGenX JAWRA manuscript

**Purpose:** Define each manuscript table’s **ID**, **section**, **role**, **sources**, **column contract**, **freeze status**, and **validation rules** before LaTeX or final numeric cells are written.

**Upstream anchors**

- [../evidence-matrix.md](../evidence-matrix.md) — claim ↔ table wiring.
- [../figures/figure-specifications.md](../figures/figure-specifications.md) — figure ↔ table cross-links.
- [../analysis/evaluation-protocol.md](../analysis/evaluation-protocol.md) — basin lock, metrics, runtime gates (must be **frozen** before Results numerics).
- [../source-bank/extracted-nhdplus-hr.md](../source-bank/extracted-nhdplus-hr.md) — N-P0 rows (NHDPlus HR methods + README).
- [../source-bank/extracted-methods.md](../source-bank/extracted-methods.md) — M-P0-30 module index.
- [../source-bank/extracted-platform-architecture.md](../source-bank/extracted-platform-architecture.md) — T-P1 orchestration (qualitative only unless measured).
- `documents/NHDPlus_HR_SWATPlus_Methods.md` — authoritative preprocessing prose.
- `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md` — pipeline / acquisition / artifact paths.

**Status legend**

| Status | Meaning |
|--------|---------|
| **planned** | Structure only; no frozen data. |
| **partial** | Some columns fillable from docs; versions / counts / timings still **TBD**. |
| **frozen** | Locked with evaluation-protocol amendment; manuscript numbers must match CSV. |
| **locked_from_inventory** | Row populated from `example-models-inventory.csv` at evaluation-protocol lock; structural counts are fixed until amendment (still cross-check workspace exports if Methods requires exact parity). |
| **pending_fresh_rerun** | **Tab-Runtime** row: manuscript-official wall time and resource fields await scripted reruns under the frozen environment. |

**Rule:** Do **not** invent dataset versions, wall-clock runtimes, file counts, ZIP sizes, or QA pass rates. Use **`TBD`** or **`SEE_NOTE`** in CSV cells until measured or audited.

---

## Tab-DataMaster

| Field | Content |
|-------|--------|
| **Table ID** | Tab-DataMaster |
| **Manuscript section** | Materials and Methods — Terrestrial / meteorological / national inputs; Abstract one-line cross-ref if used. |
| **Purpose** | Single auditable list of **external datasets** (and major derived rasters such as aligned DEM) used in the paper’s **frozen** builds: role in SWAT+, public locator (URL or DOI), **declared** version or access date, native resolution, and where the running stack resolves them (config key / module name — not a performance claim). |
| **Source documents** | `evidence-matrix.md` (national inputs rows); `readme.md` (high-level bullets — **audit against code**); `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md` §4–§7 (NHDPlus HR acquisition, `elev_cm`, 30 m DEM alignment); `publication/source-bank/rejected-or-stale-claims.md` (NSRDB 4 km vs 2 km and similar conflicts — **do not** guess). |
| **Machine-readable stub** | [tab-data-master.csv](tab-data-master.csv) |
| **Required columns** | `row_id`, `dataset_or_layer`, `provider`, `citation_key`, `role_in_swatgenx`, `native_resolution_or_scale`, `processed_resolution_or_use`, `version_or_snapshot`, `access_date_or_snapshot_date`, `acquisition_or_storage_mode`, `preprocessing_summary`, `status`, `notes` |
| **Current status** | **partial** — rows populated from documented pipeline prose and bibliography keys; **version_or_snapshot** / **access_date_or_snapshot_date** use `audit_required_before_submission` where pins are not yet verified (no invented vintages). |
| **Validation notes** | Each auditable field must match preprocessor / template config for the **same** git SHA recorded on **Tab-ReproChecklist**. Conflicting product docs (e.g., NSRDB spacing) stay explicit in **notes** until a single archive build is recorded. |

---

## Tab-NHDRules

| Field | Content |
|-------|--------|
| **Table ID** | Tab-NHDRules |
| **Manuscript section** | Materials and Methods — Hydrography / NHDPlus HR preprocessing (**priority**). |
| **Purpose** | Catalog of **implemented** rules: what is done, why, and how it affects SWAT+ topology / inputs. Supports **Fig-NHDWorkflow**, **Fig-OneOutletPartition**, **Fig-QAExample**, **Fig-TopologyBeforeAfter** without duplicating prose. |
| **Source documents** | `documents/NHDPlus_HR_SWATPlus_Methods.md` (S1.1–S1.6); `publication/source-bank/extracted-nhdplus-hr.md` (N-P0-01–N-P0-12, N-P0-23–N-P0-25). |
| **Machine-readable stub** | [tab-nhd-rules.csv](tab-nhd-rules.csv) |
| **Required columns** | `rule_id`, `rule_name`, `purpose`, `input_fields_or_layers`, `processing_action`, `output_or_check`, `locked_basin_metric_available`, `status`, `notes` |
| **Current status** | **partial** — rules documented from `documents/NHDPlus_HR_SWATPlus_Methods.md`; per-rule pass/fail or before/after counts remain **needs_metric** until logs are summarized. |
| **Validation notes** | **`locked_basin_metric_available`** is `no` unless a measured column exists in a locked export. **62.5 km²** merge threshold stays documented as an implementation parameter; do not invent global statistics. |

---

## Tab-PackageManifest

| Field | Content |
|-------|--------|
| **Table ID** | Tab-PackageManifest |
| **Manuscript section** | Materials and Methods — SWAT+ project assembly; optional Data Availability cross-ref. |
| **Purpose** | Enumerate **artifact classes** delivered with a generated project (vectors, weather, text inputs, metadata, optional QA sidecars). Supports **Fig-PackageDirectoryTree** and package-integrity claims in the evidence matrix. |
| **Source documents** | `evidence-matrix.md` (assembly + integrity rows); `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md` §8 (`SWAT_plus_*.shp`, `Watershed/Shapes/`); `publication/source-bank/extracted-nhdplus-hr.md` (N-P0-25). |
| **Machine-readable stub** | [tab-package-manifest.csv](tab-package-manifest.csv) |
| **Required columns** | `artifact_id`, `artifact_class`, `path_pattern`, `purpose`, `always_optional`, `integrity_check_tbd`, `counts_or_size_note`, `linked_fig_tab`, `status`, `notes` |
| **Current status** | **partial** — repo-relative `path_pattern` entries for core vectors, weather text, CLI lists, sidecars, and publication maps; ZIP sizing and optional QA counts still `audit_required_before_submission` where noted. |
| **Validation notes** | Use angle-bracket patterns (`<VPUID>/<LEVEL>/<NAME>/…`); never paste private absolute server paths. **`integrity_check_tbd`** uses `required_before_submission` / `deferred_by_protocol` / `documented` instead of vague `TBD`. |

---

## Tab-ReproChecklist

| Field | Content |
|-------|--------|
| **Table ID** | Tab-ReproChecklist |
| **Manuscript section** | Materials and Methods — Software / reproducibility; Data Availability Statement (subset mirror). |
| **Purpose** | Checklist mapping **reproducibility claims** to concrete artifacts: repository revision, environment export, basin IDs, preprocessor listing provenance, optional public API bundle pointer — without asserting commercial ops details. |
| **Source documents** | `evidence-matrix.md` (reproducibility row); `publication/journal-notes.md` (Wiley DAS); `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md` §2, §4.1, §9; `publication/source-bank/extracted-nhdplus-hr.md` (N-P0-20–N-P0-22, N-P0-26); `publication/source-bank/extracted-methods.md` (M-P0-30); `publication/source-bank/extracted-platform-architecture.md` (T-P1 — **qualitative** unless env frozen). |
| **Machine-readable stub** | [tab-repro-checklist.csv](tab-repro-checklist.csv) |
| **Required columns** | `item_id`, `artifact`, `where_obtained`, `evaluation_protocol_gate`, `freeze_dependency`, `uncertainty_note`, `status` |
| **Current status** | **partial** — concrete script paths and protocol dates filled; submission archive / conda pin / runtime pilot merge remain explicitly flagged. |
| **Validation notes** | Replace placeholder git SHA with the archival tag at submission. Do not copy **conflicting** default concurrency values from internal queue docs without a measured host value (`rejected-or-stale-claims.md`). |

---

## Tab-ModelComplexity

| Field | Content |
|-------|--------|
| **Table ID** | Tab-ModelComplexity |
| **Manuscript section** | Results — model size / discretization credibility. |
| **Purpose** | One row per **evaluation-protocol** basin: area, HRU, channel, subbasin, lake, and related counts so scalability claims map to frozen builds. |
| **Source documents** | [../analysis/evaluation-protocol.md](../analysis/evaluation-protocol.md) (lock **2026-05-13**); [../analysis/example-models-inventory.csv](../analysis/example-models-inventory.csv); official `admin` showcase workspaces (cross-check if manuscript text requires export parity). |
| **Machine-readable stub** | [tab-model-complexity.csv](tab-model-complexity.csv) — **three rows locked from inventory** (`Small` / `Medium` / `Large`). |
| **Required columns** | `model_id`, `tier`, `state`, `area_km2`, `n_hrus`, `n_channels`, `n_ls_units`, `n_subbasins`, `n_catchments`, `n_lakes`, `dem_resolution_m`, `model_kind`, `level`, `status`, `notes` |
| **Current status** | **locked_from_inventory** — structural numerics match `example-models-inventory.csv` for the three `model_id` keys at protocol lock; **not** the same as a hydrologic or calibration freeze. |
| **Validation notes** | If workspace re-export disagrees with inventory, amend protocol or re-sync CSV with documented reason. Manuscript counts should match this CSV after any sync. |

---

## Tab-Runtime

| Field | Content |
|-------|--------|
| **Table ID** | Tab-Runtime |
| **Manuscript section** | Results — wall time (and optional memory) for end-to-end generation. |
| **Purpose** | Report **fresh** timed reruns for the three locked basins. Pilot rows (2026-05-14) use one instrumented host and single-process runs; a fully pinned software bill of materials remains future work. |
| **Source documents** | [../analysis/evaluation-protocol.md](../analysis/evaluation-protocol.md) (official outputs policy); [tab-runtime.csv](tab-runtime.csv); [tab-runtime-phases.csv](tab-runtime-phases.csv); JSONL pilots under `publication/analysis/runtime-runs/` or operator-chosen `--runtime-runs-dir`. |
| **Machine-readable stub** | [tab-runtime.csv](tab-runtime.csv) — three basin rows; **`provisional_inventory_wall_min`** only where inventory had `generation_wall_min`. |
| **Required columns** | `tier`, `model_id`, `provisional_inventory_wall_min`, `fresh_rerun_wall_min`, `cpu_count`, `worker_count`, `peak_ram_gb`, `git_sha`, `env_id`, `run_datetime`, `status`, `notes` |
| **Current status** | **measured_scripted_rerun** — pilot wall times, CPU, worker count (single process), and `run_datetime` populated from instrumented runs; `peak_ram_gb` empty (not profiled); `git_sha` documents the repository commit containing merged phase rows. Inventory wall time is **not** manuscript-official. |
| **Validation notes** | If inventory disagrees with rerun, **rerun wins** for the manuscript. Re-runs should append new phase rows rather than silently rewriting prior pilots unless a protocol amendment says otherwise. |

---

## Other table IDs (evidence matrix; CSV specs still deferred)

**Tab-Metrics** — machine-readable stub: [tab-metrics.csv](tab-metrics.csv); LaTeX via `emit_tab_metrics_tex.py`. **Status:** **frozen** for proof basin `0205/huc12/01567500` only (2026-05-19).

**Tab-ToolContrast** — machine-readable stub: [tab-tool-contrast.csv](tab-tool-contrast.csv); LaTeX via `emit_tab_tool_contrast_tex.py`. **Status:** **documented_qualitative** (2026-05-19); three rows only (HAWQS, BASINS, SWATGenX). QSWAT+/Editor excluded (preparation toolchain). Columns: delivery, SWAT engine, hydrography, preprocessing/aggregation, simulation/outputs. No performance columns.

These appear in [../evidence-matrix.md](../evidence-matrix.md) but **do not** have CSV stubs in this folder yet: **Tab-QASummary**, **Tab-ComponentMap**, **Tab-Stack**, **Tab-OpsParams**, **Tab-DomainModes**, **Tab-SubbasinStats**, **Tab-HRURulesSummary**. **Tab-Metrics** stays deferred while hydrologic evaluation remains **No** in [../analysis/evaluation-protocol.md](../analysis/evaluation-protocol.md).

---

## Maintenance

1. When `analysis/evaluation-protocol.md` is amended, bump affected tables from **partial** → **frozen** only for columns that have measured backing.
2. Keep CSVs UTF-8; quote fields that contain commas.
3. Link new rows to **Linked Fig/Tab** IDs exactly as in `evidence-matrix.md` / `figure-specifications.md`.

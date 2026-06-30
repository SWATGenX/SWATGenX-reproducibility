# Evaluation protocol (pre-specify before writing Results)

**Status:** Phase 1 — **LOCKED** (basin set, structural reporting, and runtime policy). Hydrologic skill reporting is **out of scope** for the first manuscript pass unless this document is amended.

**Lock date:** **2026-05-13** (after lock, change basin rows, metrics scope, or official outputs only via **Amendment log** with reason).

**Source for locked basins:** [example-models-inventory.csv](example-models-inventory.csv) (disk metrics for showcase user `admin` at lock date).

## Purpose

1. **Stop Results drift:** every number in **Tab-ModelComplexity** and **Tab-Runtime** must trace to this protocol and the cited workspaces. **Tab-Metrics** and **Fig-Hydrograph** are **not** in scope for the first pass (see Hydrologic block below).
2. **Scope the story:** this paper is **not** a continental evaluation of hundreds of models; it demonstrates a **reproducible workflow** and **representative** structural behavior and **fresh** build timing where reported (see [../evidence-matrix.md](../evidence-matrix.md)).
3. **Protect claims:** NSE / KGE / PBIAS and hydrographs appear **only** if hydrologic evaluation is set to **Yes** and the observation + period blocks are completed; until then, **do not** populate **Tab-Metrics** or **Fig-Hydrograph** from email summaries or ad hoc runs.

## Scientific emphasis (agreed direction)

The primary **technical** contribution is expected to read as:

> Reproducible computational workflow for automated **high-resolution** SWAT+ watershed model generation using **national datasets** and **NHDPlus HR** hydrography—with explicit topology, **one-outlet** partitioning, divergence handling, waterbody integration, routing consistency, QA, and harmonization rules.

SWAT “button pushing” alone is weaker than **documented national-scale hydrography preprocessing** tied to SWAT+-compatible structures. Methods text should align with `documents/NHDPlus_HR_SWATPlus_Methods.md`; evaluation here supports **credibility** (sizes, **timed** builds where reported), not replace that contribution.

**Canonical roster:** [model-roster.md](model-roster.md) and [../tables/tab-model-roster.csv](../tables/tab-model-roster.csv) define **three non-overlapping sets** used in the manuscript:
1. **Benchmark S/M/L** (`03080102`, `09471300`, `03100101`) — Objective 3 structural + generation cost; Objective 5 primary simulation rows.
2. **Benchmark X20/X40/X60** (`03152000`, `07174000`, `15060105`) — Objective 5 scaling ladder only.
3. **Calibration gages** (`02297600`, `05536265`) — Objective 4 only.

Manuscript tables display **catalog Model ID** (benchmark page convention), not internal workspace paths.

## Phase 1 — decisions (frozen)

| Decision | Choice | Why it matters |
|----------|--------|----------------|
| **Basin IDs** | Three tiers below (`model_id` keys) | Controls every map and structural table |
| **Domain scales** | **S** = Oklawaha FL (`03080102`); **M** = Upper San Pedro AZ (`09471300`); **L** = Peace River HUC8 FL (`03100101`) — same packages as `/swat-plus-runtime-benchmark` | Objective 3 structural tables; Objective 5 primary simulation |
| **Simulation scaling** | **X20** (`03152000`), **X40** (`07174000`), **X60** (`15060105`) | Objective 5 HRU-scaling ladder only; not in structural maps |
| **Hydrologic calibration / validation / sensitivity** | **Controlled** — gages `02297600` (FL) and `05536265` (IL); **not** benchmark S/M/L | Objective 4 only; supersedes legacy proof basin `01567500` |
| **SWAT+ simulation runtime benchmark** | **Objective 5** — public page `/swat-plus-runtime-benchmark` (see `runtime-benchmark-objective.md`) | **Tab-RuntimeBenchmark** (planned); distinct from **Tab-Runtime** (generation wall time) |
| **Runtime environment** | **Pilot logged (2026-05-14):** single Linux host (`vmi2525606.contaboserver.net`), 10 vCPU, approximately 31.35 GB RAM; instrumented single-process runs merged into `publication/tables/tab-runtime-phases.csv` with summaries in `tab-runtime.csv`. JSONL pilots omitted `git_sha`; the committed `tab-runtime.csv` rows carry the repository short SHA that contains the merged phase table. A **full** frozen runbook entry (conda or container digest, `USER_PATH`, worker/queue parity with production) remains **TBD** for stricter reproducibility claims. Disk-derived `generation_wall_min` in the inventory is **not** authoritative. | Reproducibility of **Tab-Runtime** |
| **Official outputs** | **(1)** Existing **admin** showcase SWAT+ web-application workspaces under `…/admin/SWATplus_by_VPUID/<vpuid>/<level>/<site_no>/…` (`level` = `usgs_station` | `huc12_outlet` | `huc8`) for the three `model_id` rows (structural counts, maps, **Tab-ModelComplexity**, **Fig-ExampleBasinMaps**, **Fig-NHDWorkflow** inputs). **(2)** **Fresh scripted timed reruns** (same recipe, frozen env) **only** for values that appear in **Tab-Runtime** / runtime figures. | Prevents swapping numbers between ad hoc disk mtimes and paper-ready timing |

### Runtime values (explicit)

- Values in [example-models-inventory.csv](example-models-inventory.csv) under `generation_wall_min` are **provisional** (from disk metadata where present); they are **not** manuscript-official until replaced by **Tab-Runtime** rows from **fresh timed reruns** under the **frozen** runtime environment row above.
- Missing `generation_wall_min` in the inventory does **not** imply zero time; run timed jobs for **Tab-Runtime**.

## Locked basin tiers (3 study models — benchmark-aligned)

Structural fields below are measured from admin showcase workspaces (2026-05-31 realignment to match `/swat-plus-runtime-benchmark` S/M/L models).

| Tier | Catalog ID | Workspace `model_id` | Level | State | Basin area (km²) | HRUs | Channels | Subbasins | Lakes | Role |
|------|------------|---------------------|-------|-------|------------------|------|----------|-----------|-------|------|
| **S** | `03080102` | `0308/huc12_outlet/030801020804` | huc12 | FL | 52.61 | 473 | 45 | 4 | 4 | Obj 3 + 5 |
| **M** | `09471300` | `1505/usgs_station/09471300` | huc12 | AZ | 579.83 | 11,284 | 1,371 | 12 | — | Obj 3 + 5 |
| **L** | `03100101` | `0310/huc8/03100101` | huc8 | FL | 5,982.53 | 94,303 | 8,181 | 162 | — | Obj 3 + 5 |

**Outlet / extent:** S and M are HUC12-scale packages; L is whole-HUC8. Objective 4 uses gages `02297600` and `05536265` only (see `tab-model-roster.csv`).

## Simulation period

| Item | Value | Status |
|------|-------|--------|
| Warm-up (years) | TBD | Not required for structural-only first pass |
| Evaluation period | TBD | Not required for structural-only first pass |
| Forcing source (PRISM / other) | TBD | Document when hydro is enabled |

## Hydrologic evaluation — **controlled basin (Objective 4)**

| Item | Value |
|------|-------|
| Calibrate / validate / Morris sensitivity | **Yes** for `0310/usgs_station/02297600` (exported) and `0712/usgs_station/05536265` (Illinois; export pending Morris); see basin protocol docs |
| Supersedes | `0205/usgs_station/01567500` proof basin (2026-05-19 amendment **withdrawn** for manuscript purposes; artifacts retained in repo for audit) |
| Three locked showcase basins (FL / PA / KS) | **No** hydrologic or sensitivity metrics in manuscript |
| **Tab-Metrics** | To be frozen in `publication/tables/tab-metrics.csv` for 02297600 (replaces 01567500 rows) |
| **Tab-Sensitivity-Morris** | Planned CSV from `morris_Si_*.csv` |
| **Fig-CalValHydrograph** | Planned 3-panel daily hydrographs for 02297600 |
| **Fig-MorrisTornado** | Planned Morris μ* ranked chart |

## SWAT+ simulation runtime benchmark (**Objective 5**)

| Item | Value |
|------|-------|
| Public page | `/swat-plus-runtime-benchmark` (catalog JSON + `swatplus_perf` accepted archive) |
| Protocol doc | `runtime-benchmark-objective.md` |
| **Tab-RuntimeBenchmark** | Planned export from site catalog (S/M/L models: `03080102`, `09471300`, `03100101`) |
| **Not in scope** | Cross-tool performance claims; conflation with Tab-Runtime generation times |

## Observations (controlled basin)

| Gauge / dataset | USGS ID or source | Variable | Frequency | Status |
|-----------------|-------------------|----------|-----------|--------|
| USGS NWIS daily | `02297600` | 00060 (discharge) | Daily | **Frozen** — gage channel GIS **2**; see `cal-val-sensitivity-basin-02297600.md` |

## Metrics (controlled basin)

| Metric | Formula / tool | Threshold / benchmark | Status |
|--------|------------------|----------------------|--------|
| NSE (daily + monthly) | `ModelProcessing/ModelProcessing/evaluation.py` | Inside PSO objective | **Complete** in admin tree; **pending** freeze in `tab-metrics.csv` |
| KGE, PBIAS, RMSE, MAPE | Same module | Supplementary diagnostics | Same |
| Morris μ*, σ | SALib Morris + `sensitivity.py` | Domain QC thresholds in `sensitivity_qc.py` | **Complete**; pending manuscript table/figure |

## Structural and computational reporting (core for this paper type)

| Reported quantity | How computed | Table/Fig ID (see evidence matrix) | Status |
|-------------------|--------------|-------------------------------------|--------|
| Subbasin / HRU / channel (and related) counts | From **official** admin workspace exports / GIS for the three `model_id` rows | **Tab-ModelComplexity**; **Fig-ExampleBasinMaps**; **Fig-NHDWorkflow** (inputs) | **Authorized** (locked basins) |
| Wall time (build) | **Fresh** scripted timing runs; **not** inventory `generation_wall_min` unless replaced. Pilot instrumented reruns (2026-05-14) populate **Tab-Runtime** for three locked basins; full environment freeze still **TBD** per runtime row above. | **Tab-Runtime**; **Fig-RuntimeVsArea** or **Fig-RuntimeBar** | **Pilot measured** (single host); figures still optional |
| Memory (if measured) | `ps`/profiler / job log | **Tab-Runtime** | Optional; same rerun batch as wall time |
| QA pass / checklist | From platform QA artifacts | **Tab-QASummary** (optional) | TBD if claimed in text |

## Comparisons (optional; qualitative vs measured)

| Comparator | Evidence type allowed | Status |
|------------|------------------------|--------|
| HAWQS / QSWAT+ / manual | **Qualitative** (features, workflow) unless a controlled rebuild is run and logged | TBD |

Per [../evidence-matrix.md](../evidence-matrix.md): no “faster/better/more accurate” without controlled experiments.

## Exclusions

Document basins or conditions **excluded** after protocol lock (with reason).

*(None at lock; add rows only via amendment.)*

## Amendment log

| Date | Change | Author |
|------|--------|--------|
| 2026-05-13 | Phase 1 lock: three basin `model_id` rows from `example-models-inventory.csv`; hydrologic evaluation **No**; **Tab-Metrics** / **Fig-Hydrograph** out of scope; official outputs = admin workspaces + fresh timed reruns for **Tab-Runtime** only; runtime from inventory provisional until rerun. | Publication workflow |
| 2026-05-14 | Instrumented single-process pilot timing completed for all three locked basins; `tab-runtime.csv` and `tab-runtime-phases.csv` populated from merged JSONL (Small run excluded an abandoned same-`run_id` prefix before restart). Full conda/container runbook row remains TBD. | Publication workflow |
| 2026-05-19 | Hydrologic block **limited Yes**: completed `init_cal_val` for proof basin `0205/usgs_station/01567500`; `tab-metrics.csv`, Fig-CalProofHydrograph, Results subsection added. Showcase trio unchanged (structural-only). | Publication workflow |
| 2026-05-31 | **Objective 4/5 realignment:** Controlled cal/val/sensitivity basin changed to `0310/usgs_station/02297600` (supersedes 01567500 for manuscript). **Objective 5** added: SWAT+ simulation runtime benchmark from public page `/swat-plus-runtime-benchmark`. | Publication workflow |
| 2026-05-31 | **Structural showcase realignment:** locked tiers changed to benchmark S/M/L models (`030801020804`, `09471300`, `03100101`); Tab-Runtime fresh reruns **deferred** (prior pilot used superseded basins). | Publication workflow |
| 2026-06-01 | **Model roster clarity:** three non-overlapping sets (benchmark S/M/L, scaling X20/X40/X60, cal gages 02297600/05536265); manuscript tables use catalog Model IDs; legacy pilots excluded from prose. | Publication workflow |

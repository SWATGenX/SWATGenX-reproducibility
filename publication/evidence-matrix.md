# Evidence matrix (SWATGenX manuscript)

Each row is a **scientific or infrastructure claim** to support in the JAWRA-targeted draft. Before submission, every row should have its **Fig / Tab / Data** cells satisfied or the claim scoped down.

**Legend — Defense**

| Value | Meaning |
|-------|--------|
| **Defensible** | Supported today by repo documentation, public datasets, or already-archived outputs without new experiments. |
| **Partial** | Partly documented; needs figures, version pins, or light measurement (e.g. timing one build). |
| **Needs validation** | Requires planned runs, basins, metrics, or third-party comparison per `analysis/evaluation-protocol.md`. |

**Priorities baked in:** NHDPlus HR preprocessing; reproducibility/automation; national data integration; scalability; runtime/model-size; HAWQS / QSWAT+ / manual contrast (honest scope).

---

## Abstract (mirror of tightened claims only)

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| SWAT+ model preparation at national resolution is a reproducibility and labor bottleneck | `readme.md`, `architecture.md`; intro memos not for bibliometric numbers — `documents/SWAT_trend_publication/deep-research-report-19.md` (positioning only) | — | — | Optional: cite **one** peer-reviewed review for “widespread SWAT use” without new bibliometrics | Bieger et al. 2017 JAWRA; optional Tan et al. or similar review if used | Partial |
| SWATGenX automates SWAT+ watershed model generation from U.S. national datasets with NHDPlus HR as hydrographic backbone | `documents/NHDPlus_HR_SWATPlus_Methods.md`, `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md`, `web_application/frontend/src/pages/PlatformOverview.js` | Fig-Workflow (CONUS pipeline) | Tab-DataMaster (abridged one-liner counts of sources) | None in abstract beyond what Results will prove | NHDPlus HR program documentation (USGS); dataset citations from Tab-DataMaster | **Partial** — workflow fig + abridged data table in manuscript (2026-06-01 uplift) |
| Platform delivers reproducible packages (and optional QA / calibration hooks) | `documents/web/model-order-queue-architecture.md`, `documents/web/README_queue_email_logic.md` (if claiming queue behavior); `publication/journal-notes.md` (DAS wording only) | — | — | If claimed: “typical” wall-clock range → must match measured Tab-Runtime | SWAT+ Editor / QSWAT+ where relevant as **reader context** | Needs validation for any numeric performance claim |

---

## Keywords

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Taxonomy only (no scientific claim) | — | — | — | — | — | Defensible |

---

## Introduction

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| SWAT+ is a credible engine for multidisciplinary water-resources assessment; JAWRA is an appropriate outlet | `publication/bib/references.bib` (Bieger); `publication/journal-notes.md` (Uddameri 2018 editorial DOI for positioning) | — | — | — | Bieger 2017; Uddameri 2018 | Defensible |
| Manual / desktop workflows (QSWAT+, ArcSWAT+, ad hoc GIS) impose repeatability and staffing costs | Internal comparison notes if any; otherwise **qualitative** only | — | Tab-ToolContrast (features, **not** performance unless measured) | None unless you run a controlled rebuild | QSWAT+ / ArcGIS SWAT documentation; HAWQS Yen et al. 2016 *Water* | Partial — tool contrast table must avoid unsourced performance claims |
| National cyberinfrastructure (e.g. HAWQS) exists but differs in scope, resolution, governance, or openness | `documents/SWAT_trend_publication/deep-research-report-19.md` (hypothesis checklist only); any internal `documents/HAWQS*` if present in repo | — | Tab-ToolContrast | None | HAWQS paper; EPA/USDA materials as appropriate | Partial — requires careful **qualitative** comparison and citations |
| SWATGenX contribution: automated, NHDPlus-HR-centric, CONUS-oriented SWAT+ assembly with defined preprocessing rules | `documents/NHDPlus_HR_SWATPlus_Methods.md`, `PlatformOverview.js`, `readme.md` | Fig-Workflow | Tab-ToolContrast (narrow rows for SWATGenX) | Optional: count of VPUs / dataset versions if stated | NHDPlus HR; WBD; PRISM; NLCD; gSSURGO manuals | Partial until workflow + contrast table fixed |
| ML surge vs process models (one paragraph max) | — | — | — | **No** fabricated bibliometric trends | One survey or editorial if cited | Defensible only if **no** new quantitative trend analysis |

---

## Materials and Methods — System Overview

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| System is layered so long-running work does not block interactive use | `web_application/frontend/src/pages/PlatformOverview.js`, `architecture.md` | Fig-ArchitectureLayers (UI → API → orchestration → workers → artifacts) | Tab-ComponentMap (component ↔ responsibility) | Optional: queue depth / slot caps if asserted numerically | Celery/Redis pattern citations only if you claim novelty beyond standard practice | **Partial** — Fig-ArchitectureLayers in manuscript (2026-06-01) |
| User-facing scope includes model ordering, Explorer, downloads, optional calibration | `PlatformOverview.js`; `readme.md` | Fig-Workflow (overlap ok) | — | — | SWAT+ calibration literature if calibration path emphasized | Partial |

---

## Materials and Methods — Domain Definition

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Domains supported: USGS gage–based watershed, HUC12 outlet, whole HUC8 | `readme.md`, `PlatformOverview.js`; code pointers TBD in SWATGenX engine docs | Fig-DomainSchematic (three domain types) | Tab-DomainModes (inputs required per mode) | Example: HUC count / area stats for case study basins | USGS NWIS; WBD documentation | Needs validation for case-study maps and areas |
| Outlet / extent semantics are unambiguous for routing extraction | `documents/NHDPlus_HR_SWATPlus_Methods.md` (HUC joins, outlets) | Fig-ExampleBasinMaps (1–3 panels) | — | Basin area (km²), outlet coordinates | Same as above | Needs validation for published basins |

---

## Materials and Methods — Hydrography and NHDPlus HR Preprocessing (**priority**)

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Hydrography is derived from NHDPlus HR vector and elevation attributes within VPU workflow | `documents/NHDPlus_HR_SWATPlus_Methods.md`, `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md` | Fig-NHDWorkflow (sub-steps: CRS, cleaning, graph, partitions) | Tab-NHDRules (rule → rationale → SWAT+ impact) | Counts: reaches dropped/merged (example basin), before/after edge counts if available | Moore et al. / USGS NHDPlus HR methodology; McKay et al. as applicable | Partial — rules defensible from doc; **counts** need validation |
| Divergence code 2 reaches excluded; catchments merged to conserve area | `documents/NHDPlus_HR_SWATPlus_Methods.md` §S1.2 | Fig-QAExample (maps: removed reaches, merged catchments) | Tab-NHDRules | Area conservation check (ha) for at least one test basin | NHDPlus HR attribute dictionary | Needs validation |
| Network reduced to tree-like routing compatible with SWAT+ | same | Fig-TopologyBeforeAfter (schematic) | Tab-NHDRules | Graph stats: nodes, edges, # outlets | SWAT+ routing documentation | Partial |
| One-outlet subbasin partition for HUC12-scale conflicts | `documents/NHDPlus_HR_SWATPlus_Methods.md` §S1.4 | Fig-OneOutletPartition (conceptual diagram) | Tab-SubbasinStats (# subbasins before/after split for example) | # subbasins, # outlets pre/post | Bieger 2017 (SWAT+ structure context) | Needs validation for numeric stats |
| Channel drop and length from NHDPlus HR smoothed elevations; km→m | `documents/NHDPlus_HR_SWATPlus_Methods.md` §S1.2 | — | Tab-NHDRules | Distribution of drop (m) for sample reaches (optional) | NHDPlus HR elevation fields documentation | Partial |
| Waterbody / lake integration and refinement rules | `documents/NHDPlus_HR_SWATPlus_Methods.md` (sections after S1.5 in full file) | Fig-LakeNetworkExample (optional) | Tab-NHDRules | Waterbody count linked to subbasins | NHD waterbody documentation | Partial — read full methods doc for completeness |

---

## Materials and Methods — Terrestrial and Meteorological Inputs (**national dataset integration**)

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| SWATGenX pulls a defined set of national layers (land cover, soils, weather, crops, water use, DEM tiering, etc.) | `readme.md`, `architecture.md`, `documents/SWAT_trend_publication/deep-research-report-19.md` (enumeration checklist), `documents/NHDPlus_HR_SWATPlus_Methods.md` where spatial joins described | — | **Tab-DataMaster** (dataset, version, resolution, role in SWAT+, public URL or DOI) | Version dates / raster resolution must match actual preprocessor config in code or config templates | PRISM, NLCD, gSSURGO, NASS CDL, USGS water use, NSRDB product guides | Partial — table must be audited against **runtime** config |
| DEM / flood workflows respect project tier rules if claimed | `.cursor/rules/flood-dem-resolution-tiers.mdc` (repo rule); link to any `documents/web/*flood*` if cited in product | — | Tab-DataMaster or footnote | — | Literature on DEM scale effects if claimed | Partial |

---

## Materials and Methods — SWAT+ Project Assembly

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Exporter produces a complete SWAT+ project package (GIS + weather + text + metadata) suitable for QSWAT+ / SWAT+ Editor | `readme.md`, `architecture.md`; engine paths TBD when traced | Fig-PackageDirectoryTree (screenshot or schematic) | **Tab-PackageManifest** (file type, purpose, always/optional) | File counts, total ZIP size (MB) for 2–3 basins | SWAT+ / QSWAT+ documentation | Needs validation |
| HRU / land use–soil–slope logic is documented and stable | `documents/NHDPlus_HR_SWATPlus_Methods.md`; code cross-ref TBD | — | Tab-HRURulesSummary | HRU counts per basin | SWAT+ theoretical docs | Needs validation |
| QA products (e.g. flood screening, logs) ship with certain configurations | `documents/web/README_queue_email_logic.md` (QC mentions); product docs TBD | Fig-QAReportThumbnail (optional) | Tab-PackageManifest (QA rows) | Pass/fail counts if reported | — | Needs validation |

---

## Materials and Methods — Software Implementation and Reproducibility (**automation**)

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Web stack separates static marketing, SPA app, and API (deployment model) | `web_application/README.md`, `architecture.md` | Fig-ArchitectureLayers (shared) | Tab-Stack (language, role) | — | Standard patterns (Flask, Celery) if needed | Defensible at high level |
| Async model builds use brokered tasks and capacity controls | `documents/web/model-order-queue-architecture.md`, `documents/web/README_queue_email_logic.md`, `scripts/RUNBOOK.md` | — | Tab-OpsParams (queue names, slot semantics — **only if claimed**) | Wait-time or slot utilization if claimed | Redis/Celery generic refs only if needed | Partial — **do not over-claim** novelty |
| Reproducibility: versioned inputs/outputs, public API / site for access | `readme.md`; `publication/journal-notes.md` (DAS); public URL policy | — | Tab-ReproChecklist (item → artifact) | Build IDs, git SHA, container/conda if applicable | FAIR / FORCE11 if DAS language borrowed | Partial |

---

## Results (**scalability, runtime, model-size**)

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Generated models span range of basin scales with predictable complexity growth | `analysis/evaluation-protocol.md` (pre-locked basins) | Fig-ExampleBasinMaps | **Tab-ModelComplexity** (basin ID, area, #subbasins, #HRUs, #channels, #hydro-inlets…) | All columns measured from exports | — | **Defensible** (2026-05-31 realignment) |
| Wall-time and resource use for end-to-end generation | Server logs or scripted timing; `analysis/evaluation-protocol.md` | Fig-RuntimeVsArea (scatter) or **Fig-RuntimeBar** | **Tab-Runtime** (basin, wall time, CPU, RAM if available) | Wall time (min), peak RAM | — | **Partial** — Small tier pilot + HRU-scaled/inventory estimates for M/L (2026-06-01) |
| QA pass rates or checklist outcomes | QA logs / manifests | Fig-QABar (optional) | Tab-QASummary | % runs passing each gate | — | Needs validation |
| Hydrologic skill (only if evaluation protocol executed) | `analysis/evaluation-protocol.md` | Fig-Hydrograph | **Tab-Metrics** (NSE, KGE, PBIAS, …) | Period-of-record stats | USGS for observations; Moriasi et al. for metrics | **Defensible** for 02297600 + 05536265 cal/val; Morris IL pending |
| Package integrity (checksums, file presence) | Export scripts / CI TBD | — | Tab-PackageManifest (validation column) | % files present | — | Needs validation |

---

## Discussion

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Strengths vs HAWQS / QSWAT+ / manual: automation, NHDPlus HR backbone, reproducible ZIP, API | Same as Intro tool contrast; **no** unsubstantiated speed claims | — | Tab-ToolContrast (add “evidence column” = measured / qualitative) | Only metrics already in Tab-Runtime / Tab-Metrics | HAWQS; QSWAT+ docs | Partial — ethics: compare on **documented** dimensions |
| Limitations: calibration still user’s burden; large-basin cost; waterbody simplifications; data currency | `documents/NHDPlus_HR_SWATPlus_Methods.md`; `evaluation-protocol.md` | — | — | Optional: failure cases or timeouts | SWAT+ limitation papers | Defensible qualitatively; stronger with one **example** |
| Not a substitute for professional judgment in regulatory submissions | — | — | — | — | Policy / modeling guidance cites if used | Defensible (framing) |
| Future work: ML-assisted calibration, additional datasets, PostGIS at scale, etc. | `.cursor/plans` / internal roadmaps **not** for citation | — | — | — | ML-hydrology surveys if cited | Defensible as forward-looking |

---

## Conclusions

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Three–five sentence recap only; no new results | Must mirror Results tables | — | — | Numbers must match Tab-Runtime / Tab-ModelComplexity | Bieger; NHDPlus HR | Needs validation (consistency check) |

---

## Data Availability Statement (front matter block)

| Scientific claim | Supporting repo document(s) | Required figure(s) | Required table(s) | Required quantitative evidence | External citations likely needed | Defense |
|------------------|----------------------------|--------------------|--------------------|----------------------------------|-----------------------------------|---------|
| Code, example identifiers, and data dependencies are stated accurately | `readme.md`, `publication/journal-notes.md` (Wiley DAS expectation), public site URL | — | Tab-ReproChecklist (mirror subset) | DOIs for **public** datasets used in paper | Dataset DOIs | Partial until URLs and versions frozen |

---

## Cross-cutting figure / table index (planned IDs)

Field-level specs (purpose, inputs, script, dependencies, status): [figures/figure-specifications.md](figures/figure-specifications.md).

| ID | Description | First used in |
|----|-------------|-----------------|
| Fig-Workflow | End-to-end SWATGenX pipeline (domain → package) | Intro, Methods overview |
| Fig-ArchitectureLayers | UI / API / workers / artifacts | Methods overview, Software |
| Fig-NHDWorkflow | NHDPlus HR preprocessing sub-pipeline | Methods hydrography |
| Fig-OneOutletPartition | Concept of partitioning to SWAT+-legal outlets | Methods hydrography |
| Fig-TopologyBeforeAfter | Optional graph simplification schematic | Methods hydrography |
| Fig-QAExample | Map-based QA for divergence / catchment merge | Methods hydrography or Results |
| Fig-ExampleBasinMaps | Study basin maps | Methods domain, Results |
| Fig-RuntimeVsArea / Fig-RuntimeBar | Scalability evidence | Results |
| Fig-Hydrograph | Only if hydrologic evaluation done | Results |
| Tab-DataMaster | National inputs | Methods inputs |
| Tab-NHDRules | Preprocessing rule catalog | Methods hydrography |
| Tab-ModelComplexity | Size metrics per basin | Results |
| Tab-Runtime | Wall time (+ resources) | Results |
| Tab-PackageManifest | ZIP / project contents | Methods assembly |
| Tab-ToolContrast | SWATGenX vs HAWQS / QSWAT+ / manual | Intro, Discussion |
| Tab-ReproChecklist | Reproducibility artifacts | Methods software, DAS |
| Tab-Metrics | NSE / KGE / … | Results (optional) |
| Tab-QASummary | QA gates | Results (optional) |

---

## Repo anchors (non-exhaustive)

- `documents/NHDPlus_HR_SWATPlus_Methods.md` — **primary** technical defensibility for hydrography.
- `documents/SWATGenX/README_NHDPlus_HR_SWATPlus.md` — pipeline / data orientation.
- `web_application/frontend/src/pages/PlatformOverview.js` — user-facing scope and layer narrative.
- `readme.md`, `architecture.md` — stack, datasets at high level.
- `documents/web/model-order-queue-architecture.md`, `documents/web/README_queue_email_logic.md` — only if operational behavior is claimed quantitatively.
- `scripts/RUNBOOK.md` — service boundaries for ops claims.
- `publication/analysis/evaluation-protocol.md` — lock before filling **Tab-Metrics**, **Tab-Runtime**, case-study rows.

---

## Maintenance

- Remove or demote **Results** rows (hydrologic metrics, QA rates) if the evaluation protocol is not executed.
- When bibliometric **trend** claims are forbidden unless a reproducible bundle exists (`publication/bibliometrics/` — not created here); keep Introduction qualitative or cite **one** external review only.

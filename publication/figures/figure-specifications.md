# Figure specifications (SWATGenX manuscript)

**Purpose:** Define what each figure **proves**, what **inputs** it uses, how it is **generated**, and which **claims / tables** depend on it—**before** investing in final graphics.

**Canonical IDs:** Match [../evidence-matrix.md](../evidence-matrix.md). **Alias:** “Fig-WorkflowOverview” in discussions = **Fig-Workflow** here.

**Status legend**

| Status | Meaning |
|--------|--------|
| **planned** | Intent only; no frozen assets |
| **reproducible** | Script + data path defined; can be regenerated |
| **frozen** | Locked for submission (change only via evaluation-protocol amendment) |

**Global prerequisites:** Fill [../analysis/evaluation-protocol.md](../analysis/evaluation-protocol.md) (basins, lock date, official outputs, runtime environment) before marking any figure **frozen**.

---

## Fig-NHDWorkflow (highest priority)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-NHDWorkflow |
| **Purpose** | Supports the core claim that **national NHDPlus HR** is transformed into a **SWAT+-compatible** hydrography product via explicit, reproducible rules (not generic “GIS automation”). |
| **Manuscript claims supported** | Evidence-matrix rows: NHDPlus HR backbone; divergence-2 handling; tree-like routing; preprocessing stages; link to **Tab-NHDRules**. |
| **Inputs** | NHDPlus HR vectors + VAA + catchments + smoothed elevations for **one locked basin** (small tier preferred for legibility); optional WBD clip. Use **same build** as **Tab-SubbasinStats** / **Tab-NHDRules** if those exist. |
| **Generation workflow** | TBD script path (e.g. `publication/analysis/scripts/`): export intermediate layers or summary GeoJSON from a known model build **or** diagram-only from frozen attribute tables if vector export is heavy. **Do not** hand-draw topology that contradicts code. |
| **Visual structure** | **Horizontal or vertical swimlanes:** (1) raw HR reach/catchment subset → (2) CRS / length / drop prep → (3) divergence-2 removal + catchment merge → (4) topology clean (isolated/coastal rules) → (5) **one-outlet** partition → (6) SWAT+ channel / subbasin linkage schematic → (7) **QA** map/icon panel. Use **one real basin** inset map for geographic grounding. |
| **Quantitative dependency** | Optional on-figure badges: reach count before/after, #subbasins after partition (must match **Tab-ModelComplexity** or **Tab-SubbasinStats**). If numbers shown, they must be **frozen** from that build. |
| **Tables / figs tied to** | **Tab-NHDRules**; **Tab-ModelComplexity** (channel/reach-related columns if present); **Fig-OneOutletPartition** (may be merged panel or separate figure). |
| **Status** | planned |

---

## Fig-Workflow (alias: Fig-WorkflowOverview)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-Workflow |
| **Purpose** | End-to-end **SWATGenX** pipeline for readers: domain selection → hydrography preprocessing → terrain/land/soil/climate integration → HRU generation → SWAT+ package assembly → **QA artifacts** → downloadable project. |
| **Manuscript claims supported** | Automation + reproducibility at system level; complements (does not replace) **Fig-NHDWorkflow**. |
| **Inputs** | `documents/NHDPlus_HR_SWATPlus_Methods.md`, `readme.md`, `PlatformOverview.js`, `architecture.md` (conceptual fidelity). |
| **Generation workflow** | Diagram tool (Mermaid → PDF/SVG), Illustrator, or LaTeX TikZ; **no fabricated step** not in docs. |
| **Visual structure** | Single flowchart, **7–9 nodes**, arrows; QA and “download ZIP” as terminal nodes. Optional side color for “user vs worker” if aligned with **Fig-ArchitectureLayers**. |
| **Quantitative dependency** | None required on figure. |
| **Tables / figs tied to** | **Tab-DataMaster** (cited in caption as “inputs summarized in Table X”). |
| **Status** | planned |

---

## Fig-ArchitectureLayers

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-ArchitectureLayers |
| **Purpose** | Shows **UI → API → orchestration → workers → artifacts** so long-running work does not block the SPA; supports reproducibility / ops narrative without overselling novelty. |
| **Manuscript claims supported** | Software / infrastructure layering; optional link to queue docs if claims stay qualitative. |
| **Inputs** | `web_application/frontend/src/pages/PlatformOverview.js`, `architecture.md`, `web_application/README.md`. |
| **Generation workflow** | Block diagram from prose; no live infra screenshot required unless desired. |
| **Visual structure** | 5 horizontal layers or stacked boxes; single arrow top-to-bottom; **one** side note for Redis/Celery if mentioned in text. |
| **Quantitative dependency** | None unless **Tab-OpsParams** is published—then caption may reference slots/queues **only** if measured. |
| **Tables / figs tied to** | **Tab-ComponentMap** (if used); avoid **Tab-OpsParams** unless validated. |
| **Status** | planned |

---

## Fig-DomainSchematic

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-DomainSchematic |
| **Purpose** | Clarifies **three domain modes**: USGS gage watershed, HUC12 outlet, whole HUC8. |
| **Manuscript claims supported** | Domain definition section; scoping of evaluation basins. |
| **Inputs** | `readme.md`, `PlatformOverview.js`; WBD / NWIS icons fair-use or simple schematic shapes. |
| **Generation workflow** | Three-panel schematic + legend; not necessarily real geography. |
| **Visual structure** | 3 columns: mode name, input geometry sketch, outlet symbol. |
| **Quantitative dependency** | None. |
| **Tables / figs tied to** | **Tab-DomainModes**. |
| **Status** | planned |

---

## Fig-CalProofHydrograph (proof basin 01567500)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-CalProofHydrograph |
| **Purpose** | Daily observed vs simulated discharge for proof basin `0205/huc12/01567500` across initialization (best initial pool), calibration, and verification stages. |
| **Manuscript claims supported** | Hydrologic plausibility (not national validation); complements **Tab-Metrics**. |
| **Inputs** | Admin model tree hydrograph PNGs under `calibration_artifacts/Default_initialized/figures_.../SF/`. |
| **Generation workflow** | `python3 publication/analysis/scripts/assemble_cal_proof_hydrographs.py` |
| **Visual structure** | 1×3 panels (a) init pool best (b) calibration best (c) verification best |
| **Tables / figs tied to** | **Tab-Metrics**; `tab-calibration-run-settings.csv` |
| **Status** | **frozen** (2026-05-19) |

---

## Fig-ExampleBasinMaps

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-ExampleBasinMaps |
| **Purpose** | Maps for **evaluation-protocol** locked basins (small / medium / large): extent, outlet, optional stream network overlay. |
| **Manuscript claims supported** | Geographic credibility; scalability story; optional link to hydrographs if **Fig-Hydrograph** exists. |
| **Inputs** | Frozen basin boundaries (shapefile or GeoJSON from same build); WBD/NHD overlay as allowed by data license. |
| **Generation workflow** | Reproducible: `python3 publication/analysis/scripts/render_example_basin_maps.py --final --layout combined` (default **300 dpi** for `--final`; override with `--dpi`). Writes `publication/figures/final/fig-example-basin-maps-combined-3panel.png`; requires locked showcase workspaces and `SWAT_plus_streams.shp` / `SWAT_plus_subbasins.shp` per basin; optional `SWAT_plus_lakes.shp`. Same path resolution as `print_locked_basin_paths.py`. No web tiles. **Manuscript row:** three **independently zoomed** panels (merged vector bounds, square viewport centered on each extent so basins sit consistently in-panel under equal aspect); **per-panel scale bars**; shared vector legend; journal titles **(a)--(c)**. **Quantitative** footprint area, HRU/channel/subbasin/lake counts, and cross-basin scale comparison belong in **Table~\ref{tab:model-complexity}**—not encoded visually across panels. |
| **Visual structure** | 1×3 panels; equal aspect; light cartography; optional very light panel outline; scale bars in data units per panel. |
| **Quantitative dependency** | Basin area (km²) in caption or **Tab-ModelComplexity** only—must match protocol. |
| **Tables / figs tied to** | **Tab-ModelComplexity**; **Tab-Runtime** (by basin ID). |
| **Status** | reproducible |

---

## Fig-OneOutletPartition

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-OneOutletPartition |
| **Purpose** | Explains **SWAT+ one-outlet rule** vs HUC12 administrative cuts; shows partition concept. |
| **Manuscript claims supported** | Core NHDPlus HR / subbasin logic in `documents/NHDPlus_HR_SWATPlus_Methods.md` §S1.4. |
| **Inputs** | Schematic **or** real subbasin polygons before/after split for one locked example. |
| **Generation workflow** | Prefer **real** split from export; else conceptual diagram **labeled “schematic”** if not from code. |
| **Visual structure** | Before: multi-outlet HUC12 group; after: colored subbasins each with single outlet; arrows to downstream. |
| **Quantitative dependency** | If “before/after” counts shown → must match **Tab-SubbasinStats** or **Tab-ModelComplexity**. |
| **Tables / figs tied to** | **Tab-NHDRules**; **Fig-NHDWorkflow** (cross-reference). |
| **Status** | planned |

---

## Fig-TopologyBeforeAfter

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-TopologyBeforeAfter |
| **Purpose** | Optional graph-level illustration of **tree-like** routing after cleaning (vs ambiguous graph). |
| **Manuscript claims supported** | Topology cleaning; SWAT+ compatibility. |
| **Inputs** | Network edge list or small subgraph from one basin export **or** schematic only. |
| **Generation workflow** | TBD: NetworkX plot from exported graph; **or** hand schematic with “not to scale” if no export. |
| **Visual structure** | Two small graphs side-by-side (before / after); node count optional. |
| **Quantitative dependency** | Node/edge counts only if from frozen script output. |
| **Tables / figs tied to** | **Tab-NHDRules**. |
| **Status** | planned |

---

## Fig-QAExample

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-QAExample |
| **Purpose** | Map-based **QA**: e.g. divergence-2 reaches removed, catchment merge, or isolated reach flags. |
| **Manuscript claims supported** | QA defensibility; transparency of preprocessing side effects. |
| **Inputs** | QA GIS layers or logs from **official outputs** in evaluation-protocol. |
| **Generation workflow** | TBD: map export from same build as **Fig-ExampleBasinMaps**. |
| **Visual structure** | Main map + inset legend (removed reaches in highlight color). |
| **Quantitative dependency** | Area conservation (ha) optional in caption → must match supplementary or **Tab-NHDRules** footnote. |
| **Tables / figs tied to** | **Tab-NHDRules**; **Tab-QASummary** if used. |
| **Status** | planned |

---

## Fig-LakeNetworkExample (optional)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-LakeNetworkExample |
| **Purpose** | Waterbody / lake integration and routing refinement (only if Methods text commits to it). |
| **Manuscript claims supported** | `documents/NHDPlus_HR_SWATPlus_Methods.md` sections after S1.5. |
| **Inputs** | Basin with meaningful lake coverage from locked set. |
| **Generation workflow** | TBD. |
| **Visual structure** | Flowlines + waterbody polygons + subbasin boundaries. |
| **Quantitative dependency** | Lake / waterbody counts optional → match export stats. |
| **Tables / figs tied to** | **Tab-NHDRules**. |
| **Status** | planned |

---

## Fig-PackageDirectoryTree

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-PackageDirectoryTree |
| **Purpose** | Shows **deliverable ZIP / project layout** (reproducible artifact), not UI. |
| **Manuscript claims supported** | “Complete package” claim; **Tab-PackageManifest** visual anchor. |
| **Inputs** | Directory listing from **official outputs** of one frozen build (`tree` or Python walk). |
| **Generation workflow** | `tree -L` → stylized diagram; redact user-specific paths. |
| **Visual structure** | Hierarchical tree; icons optional for GIS vs text vs weather. |
| **Quantitative dependency** | File count / ZIP size (MB) in caption → must match **Tab-PackageManifest**. |
| **Tables / figs tied to** | **Tab-PackageManifest**. |
| **Status** | planned |

---

## Fig-QAReportThumbnail (optional)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-QAReportThumbnail |
| **Purpose** | Example **QA report** or log excerpt (flood screening, checks) if product ships it. |
| **Manuscript claims supported** | QA products in assembly section. |
| **Inputs** | Sanitized screenshot or PDF crop from frozen build. |
| **Generation workflow** | Manual export; ensure no secrets / PII. |
| **Visual structure** | Single-page crop + caption describing check type. |
| **Quantitative dependency** | Pass/fail only if tied to **Tab-QASummary**. |
| **Tables / figs tied to** | **Tab-PackageManifest**; **Tab-QASummary**. |
| **Status** | planned |

---

## Fig-RuntimeVsArea and/or Fig-RuntimeBar

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-RuntimeVsArea **or** Fig-RuntimeBar (pick one primary; other supplementary if needed) |
| **Purpose** | **Operational infrastructure:** wall-time vs basin area or vs tier (small/medium/large)—not “speed vs HAWQS” unless controlled. |
| **Manuscript claims supported** | Scalability; runtime discipline in evidence matrix. |
| **Inputs** | **Tab-Runtime** rows only (from frozen **evaluation-protocol** environment). |
| **Generation workflow** | TBD: `publication/analysis/scripts/plot_runtime.py` reading a committed CSV exported from logs. |
| **Visual structure** | Scatter: area (km²) vs wall time (min), labeled by basin ID; **or** bar chart by tier with error bars only if **repeated runs** exist. |
| **Quantitative dependency** | **All** plotted points must appear in **Tab-Runtime** with same MS# / build SHA. |
| **Tables / figs tied to** | **Tab-Runtime**; **Tab-ModelComplexity** (area column). |
| **Status** | planned |

---

## Fig-Hydrograph (optional — **gated**)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-Hydrograph |
| **Purpose** | Observed vs simulated flow **only if** evaluation-protocol enables hydrologic evaluation. |
| **Manuscript claims supported** | Optional “infrastructure + demonstration” path; **omit entirely** if hydro = No. |
| **Inputs** | USGS NWIS discharge + SWAT+ (or SWATGenX pipeline) simulated series; period per protocol. |
| **Generation workflow** | TBD script; align time zone and units. |
| **Visual structure** | One panel per basin or multi-line single panel; period shaded warm-up if shown. |
| **Quantitative dependency** | **Tab-Metrics** (NSE/KGE/PBIAS) must cite same period and gauge. |
| **Tables / figs tied to** | **Tab-Metrics**; **Fig-ExampleBasinMaps**. |
| **Status** | planned (disabled until protocol gate opened) |

---

## Fig-QABar (optional)

| Field | Content |
|-------|--------|
| **Figure ID** | Fig-QABar |
| **Purpose** | Summary of QA gate pass rates across runs or across components. |
| **Manuscript claims supported** | QA summary claims in Results. |
| **Inputs** | Aggregated QA JSON/CSV from **official outputs** (define in protocol). |
| **Generation workflow** | TBD script from committed summary table. |
| **Visual structure** | Horizontal bar % pass; **no** p-hacking across many undeclared basins. |
| **Quantitative dependency** | Must match **Tab-QASummary**. |
| **Tables / figs tied to** | **Tab-QASummary**. |
| **Status** | planned |

---

## Related high-risk **table** (not a figure)

### Tab-ToolContrast

| Field | Content |
|-------|--------|
| **Table ID** | Tab-ToolContrast |
| **Purpose** | **Capability** comparison only: automation scope, NHD resolution, delivery form, openness, **qualitative** workflow. |
| **Reviewer protection** | **No** speed, accuracy, or “better” unless a **controlled** experiment row exists with citation to measurement script and **Tab-Runtime** parity. |
| **Columns (suggested)** | Capability \| SWATGenX \| HAWQS \| QSWAT+ / manual \| Evidence type (**qualitative** / **measured**) \| Source |
| **Status** | planned |

---

## Dependency summary (figure → tables)

| Figure | Primary tables |
|--------|----------------|
| Fig-NHDWorkflow | Tab-NHDRules; Tab-ModelComplexity (optional counts) |
| Fig-Workflow | Tab-DataMaster (caption) |
| Fig-ArchitectureLayers | Tab-ComponentMap (optional) |
| Fig-DomainSchematic | Tab-DomainModes |
| Fig-ExampleBasinMaps | Tab-ModelComplexity; Tab-Runtime |
| Fig-OneOutletPartition | Tab-NHDRules; Tab-SubbasinStats / Tab-ModelComplexity |
| Fig-TopologyBeforeAfter | Tab-NHDRules |
| Fig-QAExample | Tab-NHDRules; Tab-QASummary |
| Fig-LakeNetworkExample | Tab-NHDRules |
| Fig-PackageDirectoryTree | Tab-PackageManifest |
| Fig-QAReportThumbnail | Tab-PackageManifest; Tab-QASummary |
| Fig-RuntimeVsArea / Fig-RuntimeBar | Tab-Runtime; Tab-ModelComplexity |
| Fig-Hydrograph | Tab-Metrics |
| Fig-QABar | Tab-QASummary |

---

## Changelog

| Date | Change |
|------|--------|
| TBD | Initial specifications |
| 2026-05-14 | **Fig-ExampleBasinMaps:** manuscript `figures/final/` via `--final --layout combined` (**300 dpi**): single-row **independently zoomed** panels with **per-panel scale bars**; square viewport centered on each basin extent; **Table~\ref{tab:model-complexity}** for quantitative / cross-basin scale comparison. |

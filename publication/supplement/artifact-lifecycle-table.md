# Supplement: SWATGenX artifact lifecycle (human-readable)

This page expands the rows in [`tab-artifact-lifecycle.csv`](tab-artifact-lifecycle.csv). It is **design documentation** for supplementary material: qualitative **lifecycle**, **storage**, and **CPU/RAM** classes are **not** measured benchmarks and must not be read as universal performance claims.

---

## NHDPlus HR hydrography vectors (NHDFlowline; NHDPlusFlowlineVAA; NHDPlusCatchment; NHDWaterbody)

| Field | Value |
|--------|--------|
| **Source** | USGS The National Map NHDPlus High Resolution product family |
| **Role** | Hydrography backbone; preprocessing to a SWAT+-compatible stream graph and lake linkage |
| **Lifecycle** | `persistent_reference` + `cached` VPU extracts |
| **Storage** | `very_large` |
| **CPU/RAM** | `high` |
| **Reproducibility** | Document VPU scope and access date when freezing a study; keep vector and raster product branches consistent. |
| **Manuscript** | Methods |
| **Evidence** | `documents/NHDPlus_HR_SWATPlus_Methods.md`; `SWATGenX/NHDPlus_preprocessing.py`; `publication/tables/tab-data-master.csv` (DM-01) |
| **Status** | `partial` |

---

## WBD HU8 and HU12 polygons

| Field | Value |
|--------|--------|
| **Source** | USGS Watershed Boundary Dataset (WBD) |
| **Role** | HUC attribution; spatial joins to catchments; domain clipping |
| **Lifecycle** | `persistent_reference` + `cached` with HR extracts |
| **Storage** | `large` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | Multipart HUC handling per methods narrative; keep WBD edition consistent with the NHD HR snapshot. |
| **Manuscript** | Methods |
| **Evidence** | `documents/NHDPlus_HR_SWATPlus_Methods.md`; `publication/tables/tab-data-master.csv` (DM-02) |
| **Status** | `partial` |

---

## NHDPlus HR packaged elevation (elev_cm) and derived projected DEM rasters

| Field | Value |
|--------|--------|
| **Source** | USGS NHDPlus HR raster distribution (same product family as vectors) |
| **Role** | Reach elevation and drop; terrain stack aligned to stream CRS |
| **Lifecycle** | `cached` per VPU |
| **Storage** | `large` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | `elev_cm` discovery and resample behavior live in the raster download path; CRS must match `streams.pkl` for a frozen build. |
| **Manuscript** | Methods |
| **Evidence** | `SWATGenX/NHDPlus_raster_downloads.py`; `publication/tables/tab-data-master.csv` (DM-03, DM-04) |
| **Status** | `partial` |

---

## USGS 3DEP DEM via Google Earth Engine export

| Field | Value |
|--------|--------|
| **Source** | USGS 3DEP (10 m) on the Google Earth Engine catalog |
| **Role** | On-demand terrain GeoTIFF for selected web workflows (e.g. floodplain terrain tiers); **separate** from the bundled NHD `elev_cm` path |
| **Lifecycle** | `generated_on_demand` |
| **Storage** | `variable` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | Requires operator-configured Earth Engine access; implementation retries coarser export resolution on quota or size limits (not a performance claim). |
| **Manuscript** | Methods |
| **Evidence** | `web_application/app/floodplain.py` |
| **Status** | `verified` |

---

## PRISM gridded precipitation and temperature

| Field | Value |
|--------|--------|
| **Source** | Oregon State University PRISM Climate Group |
| **Role** | SWAT+ climate station files (PCP/TMP) and CLI wiring from mesh-guided subset |
| **Lifecycle** | `cached` (CONUS or regional archives); per-model extract is smaller |
| **Storage** | `very_large` (archives) |
| **CPU/RAM** | `variable` |
| **Reproducibility** | Year span and directory layout come from `SWATGenXPaths` and environment; large archive reads can be sensitive to where files live and how they are mounted—document that layout for a frozen rerun, not as a timing guarantee. |
| **Manuscript** | Methods; Data Availability |
| **Evidence** | `SWATGenX/PRISM_extraction.py`; `SWATGenX/core.py`; `publication/tables/tab-data-master.csv` (DM-05) |
| **Status** | `partial` |

---

## NSRDB gridded solar and related meteorology

| Field | Value |
|--------|--------|
| **Source** | NREL National Solar Radiation Database |
| **Role** | SWAT+ weather component where the pipeline enables NSRDB extraction |
| **Lifecycle** | `cached` (annual or multi-year archives on operator storage); domain subset |
| **Storage** | `very_large` |
| **CPU/RAM** | `variable` |
| **Reproducibility** | Grid index and archive layout are installation-specific; audit before asserting a single public path in manuscript prose. |
| **Manuscript** | Methods; Data Availability |
| **Evidence** | `SWATGenX/NSRDB_SWATplus_extraction.py`; `publication/tables/tab-data-master.csv` (DM-06) |
| **Status** | `partial` |

---

## NLCD land cover rasters via Google Earth Engine

| Field | Value |
|--------|--------|
| **Source** | MRLC NLCD releases exposed through Earth Engine |
| **Role** | HRU land-use raster aligned to the soil reference grid; optional warp from coarser NLCD if a fine export fails |
| **Lifecycle** | `generated_on_demand` |
| **Storage** | `moderate` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | Epoch year and resolution must match configuration; Earth Engine authentication is maintained outside the public repository. |
| **Manuscript** | Methods |
| **Evidence** | `SWATGenX/NLCD_google_download.py`; `SWATGenX/generate_geospatial_vpuid.py`; `publication/tables/tab-data-master.csv` (DM-07) |
| **Status** | `partial` |

---

## gSSURGO map unit raster and CONUS soil context

| Field | Value |
|--------|--------|
| **Source** | USDA NRCS gSSURGO / SSURGO family |
| **Role** | Soil class raster and linkage into SWAT+ HRU soil logic |
| **Lifecycle** | `persistent_reference` + `cached` CONUS-scale reference |
| **Storage** | `very_large` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | Operator maintains MapunitRaster and GDB paths referenced in `SWATGenXPaths`; national soil grids are not redistributed inside git. |
| **Manuscript** | Methods |
| **Evidence** | `SWATGenX/gssurgo_extraction.py`; `SWATGenX/SWATGenXConfigPars.py`; `publication/tables/tab-data-master.csv` (DM-08) |
| **Status** | `partial` |

---

## SWAT+ soil SQLite and exported SSURGO CSV tables

| Field | Value |
|--------|--------|
| **Source** | SWAT+ soil database plus SWATGenX export helpers |
| **Role** | Populate SSURGO-derived tables used when building HRU soils |
| **Lifecycle** | `cached` |
| **Storage** | `moderate` |
| **CPU/RAM** | `low` |
| **Reproducibility** | CSV exports can be regenerated from SQLite when missing from expected paths. |
| **Manuscript** | Methods |
| **Evidence** | `SWATGenX/SWAT_gssurgo.py`; `SWATGenX/generate_swatplus_rasters.py` |
| **Status** | `partial` |

---

## Preprocessed hydrography caches (e.g. streams.pkl)

| Field | Value |
|--------|--------|
| **Source** | Derived from NHDPlus HR preprocessing |
| **Role** | Reuse of derived topology for repeated builds; consistent routing object for downstream steps |
| **Lifecycle** | `cached` per VPU |
| **Storage** | `moderate` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | Tied to preprocessing code version; invalidate when HR rules change materially. |
| **Manuscript** | Methods |
| **Evidence** | `SWATGenX/configuration.py`; `SWATGenX/NHDPlus_extract_by_VPUID.py` (pickle outputs per pipeline) |
| **Status** | `partial` |

---

## Generated SWAT+ workspace (project tree)

| Field | Value |
|--------|--------|
| **Source** | SWATGenX pipeline and web workers |
| **Role** | Runnable SWAT+ directory with Watershed shapes, weather, HRU tables |
| **Lifecycle** | `generated_on_demand` |
| **Storage** | `variable` |
| **CPU/RAM** | `high` |
| **Reproducibility** | Per-user or per-run output is **not** assumed to be a public archive; ZIP is a separate deliverable row. |
| **Manuscript** | Methods |
| **Evidence** | `SWATGenX/core.py`; `web_application/app/utils.py` (`single_swatplus_model_creation`) |
| **Status** | `partial` |

---

## SWAT+ model ZIP deliverables (cached archives)

| Field | Value |
|--------|--------|
| **Source** | Same workspace tree compressed for download |
| **Role** | End-user or example-model package distribution |
| **Lifecycle** | `generated_on_demand` |
| **Storage** | `variable` |
| **CPU/RAM** | `moderate` |
| **Reproducibility** | Async task builds or reuses a `_zips` cache beside the model directory. |
| **Manuscript** | Methods |
| **Evidence** | `web_application/app/swatgenx_tasks.py`; `web_application/app/user_auth.py` (download routes) |
| **Status** | `verified` |

---

## QA logs, stage logs, and report ZIP bundles

| Field | Value |
|--------|--------|
| **Source** | Application and worker logging; optional report export routes |
| **Role** | Traceability diagnostics and optional packaged reports |
| **Lifecycle** | `not_archived` |
| **Storage** | `small` |
| **CPU/RAM** | `low` |
| **Reproducibility** | Operational retention policy; Data Availability already states these are **not** treated as archival scientific datasets for submission. |
| **Manuscript** | Supplement only |
| **Evidence** | `publication/manuscript/sections/data-availability.tex`; `web_application/app/viz_report.py` |
| **Status** | `partial` |

---

## Publication example-model inventory and evaluation protocol rows

| Field | Value |
|--------|--------|
| **Source** | Repository CSV plus protocol markdown |
| **Role** | Lock structural showcase basins and counts for reproducible figures and tables |
| **Lifecycle** | `archived_example` |
| **Storage** | `small` |
| **CPU/RAM** | `low` |
| **Reproducibility** | `status=locked_from_inventory` rows drive publication scripts; not a substitute for independent hydrologic archives. |
| **Manuscript** | Data Availability; Supplement |
| **Evidence** | `publication/tables/tab-model-complexity.csv`; `publication/analysis/evaluation-protocol.md`; `publication/analysis/scripts/_locked_basin_paths.py` |
| **Status** | `verified` |

---

## Publication runtime and resource table (tab-runtime)

| Field | Value |
|--------|--------|
| **Source** | Measured reruns when populated |
| **Role** | Planned transparency for elapsed time and resource use under a frozen environment |
| **Lifecycle** | `TBD` |
| **Storage** | `small` |
| **CPU/RAM** | `TBD` |
| **Reproducibility** | Fields remain TBD until the evaluation-protocol environment block and timed reruns complete; avoid performance claims in the main text until then. |
| **Manuscript** | Supplement only |
| **Evidence** | `publication/tables/tab-runtime.csv`; `publication/manuscript/sections/results.tex` |
| **Status** | `needs_audit` |

---

## Publication data-master and NHD rules tables

| Field | Value |
|--------|--------|
| **Source** | Repository CSV specifications |
| **Role** | Traceability from Methods claims to dataset families and rule IDs |
| **Lifecycle** | `archived_example` |
| **Storage** | `small` |
| **CPU/RAM** | `low` |
| **Reproducibility** | Editorial contract tables; update when dataset versions freeze. |
| **Manuscript** | Supplement |
| **Evidence** | `publication/tables/tab-data-master.csv`; `publication/tables/tab-nhd-rules.csv` |
| **Status** | `partial` |

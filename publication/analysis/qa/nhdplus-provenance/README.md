# NHDPlus HR provenance & version control

NHDPlus High Resolution is **not** a single-resolution product. Its flowlines come
from the National Hydrography Dataset, whose source map scale was contributed by
state stewards and **varies by region** (e.g., lower-Michigan VPUs are sourced only
at 1:24,000, while Illinois and Florida VPUs carry local 1:1,200–1:4,800 data). Each
generated SWAT+ model therefore inherits the resolution and publication vintage of
its VPU. This subsystem records that provenance per model and across the archive.

## Where the provenance lives (in the source data)

Inside every HU4 geodatabase (`NHDPLUS_H_<VPU>_HU4[_<YYYYMMDD>]_GDB.zip`):

- **`NHDSourceCitation`** table → field **`SourceScaleDenominator`** (e.g. `24000` =
  1:24,000). The set of denominators present is the per-VPU source-scale fingerprint.
- **`NHDFlowline`** → `LengthKM`, `VisibilityFilter`, `Resolution`; reach count / VPU
  area is a resolution proxy (reach density, km⁻²).
- **`WBDHU4`** → `loaddate`, `states`, `name`, `areasqkm`.
- The USGS **publication date** is encoded in the original zip filename.

## Components

| File | Role |
|---|---|
| `SWATGenX/nhdplus_version.py` | **Authoritative per-VPU version reader.** Recovers the USGS publication date from the geodatabase metadata (max `<CreaDate>`) + source-scale distribution + reach density, reading the zip in place via GDAL `/vsizip` (no extraction). Writes `nhdplus_version.json` into each VPU dir; `--backfill-all` rebuilds the registry; `--cleanup-unzips` removes leftover unzipped GDBs. Imported by the extraction pipeline. |
| `SWATGenX/NHDPlus_extract_by_VPUID.py` | Extraction pipeline — now captures `nhdplus_version.json` at extract time and **removes the unzipped GDB** afterward (keeps only artifacts). |
| `publication/analysis/scripts/nhdplus_provenance_inventory.py` | CONUS-scale scan (source-scale distribution, reach density). Writes `nhdplus_hr_inventory.{json,csv}`. |
| `/data/SWATGenXApp/GenXAppData/NHDPlusHR/nhdplus_hr_versions.json` | Per-VPU registry (pubdate + scales + density) read at model-build time. A snapshot is tracked at `publication/analysis/qa/nhdplus-provenance/nhdplus_hr_versions.json`. |
| `SWATGenX/model_provenance.py` | Writes `README.md` + `provenance.json` into a model dir. Imported by `core.py` (auto on every build) and runnable standalone for backfill. |
| `publication/analysis/scripts/emit_tab_nhdplus_provenance_tex.py` | Renders the manuscript supplementary provenance table from the catalog models' `provenance.json`. |

### Vintage is recovered from the data, not the filename

The USGS publication date is embedded in every HU4 geodatabase's ESRI metadata as
`<CreaDate>`; the **maximum CreaDate equals the published snapshot date** (verified:
VPU 0101 → 20220901, matching its filename). `nhdplus_version.py` reads it via
`/vsizip` with no download or extraction, so the 49 filename-stripped zips recover
their true vintages (e.g. Peace `0310` → 2018-03, Illinois `0712` → 2017-03).

## What each model now carries

At build time (`core.py`, right after `meta.txt`), every model directory gets:

- **`README.md`** — human-readable: SWATGenX version, build time, delineation method
  + thresholds, and a data-sources table (NHDPlus vintage + finest source scale +
  reach density, DEM, NLCD epoch, gSSURGO, PRISM/NSRDB, WBD) with citations.
- **`provenance.json`** — the same as a machine-readable record (`schema_version 1.0`).

The provenance write is best-effort and never raises into the build.

## Refresh / update procedure (when USGS republishes a VPU)

1. Place the new HU4 geodatabase zip in `NHDPlusHR/zipped/`. The filename date is
   optional — the true vintage is read from the geodatabase metadata regardless.
2. Rebuild per-VPU version artifacts + registry (run as `www-data`):
   `python SWATGenX/nhdplus_version.py --backfill-all --cleanup-unzips`.
3. Refresh existing models' sidecars:
   `python -m SWATGenX.model_provenance --model-dir <model_dir>`
   (new builds update automatically via `core.py`).
4. Regenerate the manuscript table + tracked registry snapshot:
   `python publication/analysis/scripts/emit_tab_nhdplus_provenance_tex.py`;
   copy `nhdplus_hr_versions.json` into `publication/analysis/qa/nhdplus-provenance/`.

## Coverage and known gaps

- **All 234 local VPU dirs carry `nhdplus_version.json`.** 69 have full provenance
  (real pubdate + source scale + density) from a retained zip; **165 are `partial`
  (`needs_refresh: true`)** — their zip was not retained, so pubdate/scale recover only
  when that VPU is next fetched (the extraction pipeline now captures it automatically).
- **VPU `1111` zip is corrupt** (fails to open) — re-download to complete its record.
- Recovered pubdates span ~2017–2022; filename-date gaps no longer block vintage
  recovery (read from `<CreaDate>`).

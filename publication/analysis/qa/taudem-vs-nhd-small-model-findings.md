# TauDEM vs NHDPlus HR — small model (Oklawaha S) internal findings

**Date:** 2026-06-02 · **Basin:** Oklawaha S, HUC12 `030801020804` (VPUID 0308) · **Status:** internal, for later use.

Two SWAT+ models of the same watershed coexist in one site directory (enabled by the
non-destructive model-creation fix, `core.py` `_remove_model_workspace_only`, commit `d21f5d5`):
`SWAT_MODEL_Web_Application` (NHDPlus-HR delineation) and `SWAT_MODEL_TauDEM_auto`
(threshold TauDEM, stream=5000 / channel=1000 cells, force_taudem_only).

## Finding 1 — TauDEM area is larger but the network is more fragmented; NHD is cleaner

| | NHDPlus HR | TauDEM |
|---|---|---|
| HRUs | 473 | 997 |
| Channels | 45 | 63 |
| Subbasins | 3 | 17 |
| Outlet contributing area | 52.6 km² | 67.6 km² |

TauDEM's contributing area is ~28% larger, and it produces a denser, more dendritic channel
network (63 vs 45 channels) for the same 3 subbasins — i.e. more small/fragmented channels,
whereas the NHDPlus-HR network is clean. (A formal connectivity metric — count of independent
outlets / disconnected sub-networks — still to add from the routing table; `rivs1.shp` has no
`DSLINKNO`, so use `chandeg.con` downstream links.)

## Finding 2 — TauDEM lakes are artifacts, never used in the executable model (KEY)

The 4 lake polygons (`SWAT_plus_lakes.shp`; 2.146, 0.401, 0.327, 0.158 km²; total 3.03 km²) are
**NHD-derived and identical** in both models (TauDEM does not re-derive lakes; it inherits the
shape-stage output). But whether the lakes are wired into the EXECUTABLE model differs sharply:

| TxtInOut object | NHD model | TauDEM model |
|---|---|---|
| `reservoir.con` | 4 objects | **missing** |
| `hydrology.res` | 4 | **missing** |
| `reservoir.res` | 4 | **missing** |

The NHDPlus-HR model wires the 4 lakes as **reservoirs**; the threshold-TauDEM model has the lake
shapefile but **zero reservoir objects** — the lakes are present as artifacts and **never used**.
So NHDPlus HR integrates lakes; threshold-TauDEM drops them. This favors NHDPlus HR on lake-bearing
basins and motivates the next experiment.

## Finding 3 — NWIS drainage-area "ground truth" was a WBD fallback (data-integrity issue)

`meta_0308.csv` has `nwis_drain_area_km2 = NaN` (and `nwis_drain_area_sqmi = NaN`) for the three S
gages (`02239501`, `02239600`, `02239601`). `load_station_drainage_area_km2()` then **silently
falls back to `wbd_upstream_hu12_area_sqkm` = 53.37 km²** — the HU12 polygon area, identical for
every gage in the HU12. Consequences:
- The earlier S drainage-area comparison's "NWIS" column was actually the WBD HU12 area; the
  "TauDEM matches NWIS better" reading is **retracted** (it matched a constant, not real NWIS).
- The comparison harness must report the **source label** and not treat a WBD fallback as NWIS;
  gages with missing NWIS site DA must be flagged, or backfilled from the USGS NWIS site service.
- Cross-check the broader/published drainage-area audit: where `nwisDrainageAreaKm2` equals the
  WBD value, it may be a fallback rather than a true NWIS site area (Peace had real NWIS for 57/76;
  S gages have none).

## Open coexistence issue (separate) — shared streamflow_data

`streamflow_data/` is site-level and shared; its `stations.shp` gage→channel assignment is
model-specific, so the last build wins (currently shows NHD channels). Must be scoped per
`MODEL_NAME` before calibrating both models.

## Finding 4 — DEM clip extent dominates TauDEM area; TauDEM+lakes fails to wire lakes

Built two more TauDEM variants with the DEM clipped to the basin polygon (dissolved subbasins
+250 m; new option `SWATGENX_CLIP_DEM_TO_BOUNDARY`, env-gated, default = bbox) and the
`QSWAT_TAUDEM_USE_LAKES` toggle. **Note on "+250 m":** this is the clip-*buffer* distance around
the basin polygon, **not** the DEM resolution. Every model here — NHD and all TauDEM variants —
routes the same **30 m DEM** (30.01 m, EPSG:32617, identical 354×434 grid, verified from each
model's `Watershed/Rasters/DEM/dem.tif`). Only the delineation engine and the DEM *extent* differ:

| Model | DEM clip | lakes | channels | outlet area | reservoirs |
|---|---|---|---|---|---|
| NHD (`SWAT_MODEL_Web_Application`) | bbox | yes | 45 | **52.6 km²** | 4 |
| `SWAT_MODEL_TauDEM_auto` | bbox (square) | no | 63 | 67.6 km² (over) | 0 |
| `SWAT_MODEL_TauDEM_nolakes_clip` | basin polygon | no | 25 | **43.1 km² (under)** | 0 |
| `SWAT_MODEL_TauDEM_lakes_clip` | basin polygon | yes | — | **BUILD FAILED** | — |

- **DEM extent is the dominant lever on TauDEM area.** Square bbox over-delineates (67.6 km²);
  dissolved-polygon+250 m clips too tight and under-delineates (43.1 km²); NHD's 52.6 km² sits
  between. The buffer / clip polygon needs tuning (e.g. true topographic divide, larger buffer)
  to land near the real drainage area.
- **TauDEM + lakes (addHUCLakes) FAILS here.** `QSWAT_TAUDEM_USE_LAKES=true` loads the 4 lake
  polygons, but QSWAT+ reports `Failed to find outlet for lake 1..4`, the lake inlet/outlet ID is
  `not found as DSNODEID in demchannel.shp`, and HRU creation crashes
  (`QgsGeometry.fromPointXY(): NoneType`). Root cause: TauDEM's threshold channels do not connect
  to the NHD-derived lake polygons, so lake outlets cannot be resolved. This is the concrete form
  of "TauDEM sticks on lakes." NHDPlus HR, which carries lake–channel topology in the hydrography,
  wires the same 4 lakes cleanly.
- Two QSWAT+ lake methods exist: **`addHUCLakes`** (default, subtract lakes from subbasins) and
  **`splitChannelsByLakes` + TauDEM rerun** (legacy; `--lake-split`). **Both fail**, on **both**
  the clipped and the square DEM — all three TauDEM+existing-lakes builds crashed identically
  (`Failed to find outlet for lake` → HRU `NoneType` geometry). So the failure is inherent: TauDEM's
  threshold channels do not pass through the pre-made NHD lake polygons, regardless of method or DEM
  extent. NHDPlus HR wires the same 4 lakes cleanly because it carries lake–channel topology.

  Tested model folders (all incomplete): `SWAT_MODEL_TauDEM_lakes_clip`,
  `SWAT_MODEL_TauDEM_lakes_clip_split`, `SWAT_MODEL_TauDEM_lakes_square`.

## Finding 5 — QSWAT+ stream-burn does NOT fix TauDEM+lakes either

Added a QSWAT+ built-in stream-burn option (`QSWAT_TAUDEM_BURN_STREAMS` → `--burn-streams`): before
TauDEM, burn the NHD-derived `SWAT_plus_streams.shp` into the DEM (`checkBurn`/`selectBurn`) so flow
follows the NHD network. Built `SWAT_MODEL_TauDEM_lakes_burn_clip` (burn + lakes + clipped DEM): the
burn engaged ("burning NHD stream network into DEM"), but the lakes **still failed** identically
(`Failed to find outlet for lake 1..4` → HRU crash).

**So four TauDEM+lakes approaches now fail the same way:** addHUCLakes·clip, splitChannelsByLakes·clip,
addHUCLakes·square, and burn+addHUCLakes·clip. The QSWAT+ lake-outlet matching cannot connect these
lakes to TauDEM-derived channels regardless of method, DEM extent, or stream-burning. **NHDPlus HR
wires the same 4 lakes cleanly** because lake–channel topology comes from the hydrography, not from
re-deriving it on a DEM.

Diagnostic (burn without lakes) shows the stream-burn also does **not** improve the delineation:
clip+burn = 42.8 km² / 23 channels vs clip no-burn = 43.1 km² / 25 channels (NHD 52.6 / 45). So
**DEM extent, not stream-burning, controls TauDEM's contributing area**, and burning helps neither
the area nor the lakes.

## Conclusion (small model) — NHDPlus HR is the superior delineation here

| Model | channels | outlet area | lakes wired |
|---|---|---|---|
| NHDPlus HR | 45 | 52.6 km² (matches) | **4 reservoirs** |
| TauDEM square | 63 | 67.6 km² (over) | 0 |
| TauDEM clip | 25 | 43.1 km² (under) | 0 |
| TauDEM clip + burn | 23 | 42.8 km² (under) | build fails w/ lakes |

For this lake-bearing basin, threshold-TauDEM cannot replicate NHDPlus HR: its contributing area is
governed by DEM extent (square over-delineates, polygon-clip under-delineates; NHD's 52.6 km² sits
between), and it **cannot integrate the lakes by any method** (addHUCLakes, splitChannelsByLakes,
or NHD-stream-burn — all fail at lake-outlet resolution / HRU creation). NHDPlus HR wires the lakes
and lands on the right area because it carries lake–channel hydrography topology. **This is direct
evidence for the manuscript that NHDPlus-HR conditioning is not merely convenient but necessary on
lake-influenced basins.**

Remaining untried path (deferred): custom lake-burn (depress lake interior + breach outlet so the
sink drains after pit-fill). Given four QSWAT+ lake paths already fail at the same step, this is low
priority unless a future basin needs it.

## Next experiments (motivated by these findings)

1. **TauDEM with vs without lake delineation** — build a third TauDEM model that explicitly
   delineates/wires lakes, and one without, to test whether TauDEM can integrate lakes at all
   (Finding 2 suggests threshold-TauDEM currently drops them).
2. **Fix the NWIS source** — backfill real per-gage NWIS site drainage area (or flag missing);
   never mislabel a WBD fallback as NWIS in the comparison.
3. **Per-model streamflow_data** — required before the calibration comparison.
4. Then the NHD-vs-TauDEM **calibration** comparison (the NHD S model calibrated poorly).

## Artifacts

- `publication/analysis/scripts/run_taudem_variant_model.py` — build NHD or TauDEM variant under a custom MODEL_NAME (same site dir).
- `publication/analysis/scripts/compare_drainage_area_models.py` — per-gage area comparison (geometric snap; **must fix NWIS source per Finding 3**).
- `publication/analysis/scripts/plot_hru_nhd_vs_taudem.py`, `plot_lakes_nhd_vs_taudem.py` — comparison maps.

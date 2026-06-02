# Peace phase 3 — pipeline trace results

**Stage D label:** `swatgenx_postprocessed_polygon_upstream_km2` = upstream Σ of **watersheds.pkl**
polygon areas (orphan-dissolved national artifact), domain-clipped to Peace HUC-12s — **not** the
per-project QSWAT `Watershed/Shapes` (missing for Peace HUC-8 on disk).

**Stage E:** `AreaC` from `streamflow_data/README.md` at gage-assignment time (when rivs1 existed).

**Stage G:** `TotDASqKm` on the crosswalk reach in national `streams.pkl` (NHD VAA carried through
preprocessing; **not** written to `SWAT_plus_streams.shp`, which has no drainage-area field).

Panel: `peace-drainage-area-phase3-panel.csv` · Output: `peace-drainage-area-pipeline-trace.csv`

## Fork summary (10 gages)

| Site | Role | NHD TDA | D polygons | E AreaC | F chandeg | Fork | First exceed |
|---|---|---:|---:|---:|---:|---|---|
| 02294650 | mainstem_15_17 | 856.95 | 874.22 | 1002.2 | 1002.195074 | qswat_swatplus_export_or_chandeg_assignment | E_qswat_areac_assignment |
| 02294760 | mainstem_15_17 | 891.56 | 914.81 | 1046.57 | 1046.57317 | qswat_swatplus_export_or_chandeg_assignment | E_qswat_areac_assignment |
| 02294898 | mainstem_15_17 | 995.39 | 1021.98 | 15.13 | 1162.6722525 | qswat_swatplus_export_or_chandeg_assignment | F_chandeg |
| 02295420 | moderate_20_40 | 181.28 | 186.22 | 231.22 | 231.21846409999998 | qswat_swatplus_export_or_chandeg_assignment | E_qswat_areac_assignment |
| 02296389 | moderate_20_40 | nan | nan | 176.08 | 176.0835783 | insufficient_data | unknown |
| 02294747 | outlier_low | 13.19 | 19.16 | 12.08 | 22.98132 | assignment_outlier_not_area_pipeline | D_watershed_polygons |
| 02295440 | outlier_low | 1.76 | 1.76 | 25.13 | 1.7565802 | assignment_outlier_not_area_pipeline | E_qswat_areac_assignment |
| 02293694 | lake_canal | 78.53 | 9.82 | 209.01 | 9.800630700000001 | swat_below_nhd_review_assignment | E_qswat_areac_assignment |
| 02294330 | lake_named | 44.99 | 44.99 | 59.84 | 59.8350959 | qswat_swatplus_export_or_chandeg_assignment | E_qswat_areac_assignment |
| 02297600 | control_good | 153.72 | 157.23 | 165.61 | 165.60747909999998 | both_polygon_and_export_contribute | none_exceed_before_F |

## Mainstem pattern

Median SWAT/NHD at stage F: 1.169
Median polygon/NHD at stage D: 1.026
Median AreaC/NHD at stage E: 1.169

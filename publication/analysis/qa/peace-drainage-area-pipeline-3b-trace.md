# Peace phase 3b — rivs1 / sqlite vs NHD and chandeg

**Model base:** `${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101/SWAT_MODEL_Web_Application`

## Artifact status

| Artifact | Status |
|---|---|
| `rivs1.shp` | ok: ${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101/SWAT_MODEL_Web_Application/Watershed/Shapes/rivs1.shp (8085 channels) |
| Project SQLite | ok: ${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101/SWAT_MODEL_Web_Application/SWAT_MODEL_Web_Application.sqlite (gis_channels=8169, channel_con=0) |
| `SWAT_plus_streams.shp` area fields | none_expected — ok: no drainage-area fields (14 cols) |

When artifacts are missing, `stage_h_*` columns are empty and `fork_3b` is `artifacts_missing_rerun_when_restored`. Re-run this script after restore.

## Panel trace

| Site | Role | NHD A | G pickle | rivs1 H | sqlite | chandeg F | fork_3b |
|---|---|---:|---:|---:|---:|---:|---|
| 02294650 | mainstem_15_17 | 856.95 | 856.94659979 | 1002.2 | 1002.20 | 1002.195074 | offset_in_rivs1_before_chandeg_export |
| 02294760 | mainstem_15_17 | 891.56 | 891.56249983 | 1046.57 | 1046.57 | 1046.57317 | offset_in_rivs1_before_chandeg_export |
| 02294898 | mainstem_15_17 | 995.39 | 995.38719978 | 1162.67 | 1162.67 | 1162.6722525 | offset_in_rivs1_before_chandeg_export |
| 02295420 | moderate_20_40 | 181.28 | 181.27969986 | 231.22 | 231.22 | 231.21846409999998 | offset_in_rivs1_before_chandeg_export |
| 02296389 | moderate_20_40 | nan | nan | 176.08 | 176.08 | 176.0835783 | rivs1_matches_chandeg |
| 02294747 | outlier_low | 13.19 | 13.19030001 | 22.98 | 22.98 | 22.98132 | offset_in_rivs1_before_chandeg_export |
| 02295440 | outlier_low | 1.76 | 1.7585000000000002 | 1.76 | 1.76 | 1.7565802 | rivs1_matches_chandeg |
| 02293694 | lake_canal | 78.53 | 78.53100002 | 9.8 | 9.80 | 9.800630700000001 | rivs1_matches_chandeg |
| 02294330 | lake_named | 44.99 | 44.99320008 | 59.84 | 59.84 | 59.8350959 | offset_in_rivs1_before_chandeg_export |
| 02297600 | control_good | 153.72 | 153.71659989 | 165.61 | 165.61 | 165.60747909999998 | rivs1_matches_chandeg |

## Interpretation (when rivs1 is restored)

- **H ≈ F ≈ E and all ≫ A:** offset is in QSWAT/TauDEM channel `AreaC`, not TxtInOut export.
- **H low, F high:** offset introduced during SWAT+ text export.
- **G ≈ A, H high:** supports TauDEM recompute vs NHD VAA (not pre-inflated pickle attribute).

Output: `peace-drainage-area-pipeline-3b-trace.csv`

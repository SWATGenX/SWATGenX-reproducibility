# Peace station → channel assignment evaluation

Stations: 76 · Search radius: 500 m (EPSG:5070) · Candidates: chandeg channel points with crosswalk NHD `TotDASqKm`.

**Scope:** Peace HUC-8 only. Does **not** change `stations.shp` or rerun streamflow export.

## Strategy summary (vs NHD `TotDASqKm` at crosswalk reach)

| Strategy | Would change channel | Median |Δ| vs NHD | Notes |
|---|---:|---:|---|
| **assigned (current)** | — | 10.2% | Production README match (rivs1 AreaC at build) |
| distance_only | 57 | 8.5% | Closest chandeg point in band |
| match_usgs_areac | 44 | 10.1% | Mirrors production: log-match chandeg area to USGS NWIS DA |
| min_areac_in_band | 60 | 5.6% | Smallest chandeg area in band (tributary heuristic) |
| match_nhd_tda_at_crosswalk | 54 | 4.6% | Min log |chandeg − NHD TDA| at crosswalk reach |
| nhd_gage_pick_gis | 44 | 9.6% | NHD gage-pick reach (TotDASqKm vs USGS) → GIS with same crosswalk NHD ID |
| nhd_local_pick_gis | 50 | 9.4% | NHD pick by local `AreaSqKm` vs USGS → matching GIS |

## Stations where an alternate beats current by >5% |Δ| vs NHD (29)

| Site | Assigned | |Δ| assign | Best alt | Alt |Δ| | USGS km² |
|---|---:|---:|---|---:|---:|
| 02295580 | 695 | 37229.1% | distance_only | 0.1% | 121.85402973360566 |
| 02294747 | 2896 | 74.2% | match_usgs_areac | 50.9% | 1448.2658499695908 |
| 02294775 | 2615 | 74.1% | match_usgs_areac | 50.9% | 1448.2658499695908 |
| 280441081520200 | 9317 | 53.8% | distance_only | 0.4% | 159.4730888687525 |
| 02297153 | 632 | 48.2% | distance_only | 33.3% | 100.49818651704904 |
| 02297155 | 603 | 40.9% | min_areac_in_band | 0.2% | 300.9085169861849 |
| 02294330 | 2232 | 33.0% | min_areac_in_band | 0.2% | 54.90073831050262 |
| 02294491 | 755 | 18.9% | min_areac_in_band | 0.8% | 369.9183661447064 |
| 02294650 | 437 | 16.9% | min_areac_in_band | 0.1% | 1448.2658499695908 |
| 02295607 | 281 | 15.8% | match_nhd_tda_at_crosswalk | 0.1% | 2028.3491288320545 |
| 02295637 | 269 | 15.6% | distance_only | 0.6% | 2190.90261722901 |
| 02294161 | 451 | 14.8% | distance_only | 6.5% | 593.0547223889886 |
| 02295203 | 322 | 14.5% | distance_only | 1.1% | 2028.3491288320545 |
| 02296525 | 242 | 12.4% | distance_only | 0.1% | 3257.1980523767875 |
| 02297345 | 181 | 11.4% | distance_only | 0.4% | 4599.151207517376 |
| 02297350 | 166 | 11.3% | min_areac_in_band | 0.7% | 4599.151207517376 |
| 02297460 | 58 | 11.3% | distance_only | 0.0% | 5746.509142333588 |
| 02297310 | 333 | 9.6% | min_areac_in_band | 1.7% | 627.9560024184627 |
| 02297635 | 1863 | 9.4% | min_areac_in_band | 0.1% | 247.11337708765703 |
| 02297600 | 2718 | 7.7% | distance_only | 2.6% | 198.1594209755774 |

## Interpretation hooks

- If **match_usgs_areac** ≈ assigned but both disagree with NHD, assignment is consistent with production rules; remaining gap is likely QSWAT/TauDEM vs NHD VAA (phase 3), not wrong channel id.
- If **nhd_local_pick_gis** or **min_areac_in_band** greatly improves |Δ| vs NHD for tributary gages, production `da_distance` on **cumulative** AreaC may be selecting mainstem channels inside 500 m.
- Changing assignment requires re-running `fetch_streamflow_for_watershed` and recalibration — **Peace proof first**, then portfolio decision.

Detail: `peace-station-channel-assignment-evaluation.csv`

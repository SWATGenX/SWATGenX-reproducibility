# Peace improved station assignment (swatgenx_v2)

Dual-scale NHD target reach (tributary: local AreaSqKm vs USGS; cumulative: TotDASqKm vs USGS), then GIS channel by crosswalk NHD ID or composite score (SWAT area vs NHD TDA + USGS + distance + stream order). Excludes crosswalk snaps >150 m when better candidates exist. Proposal only — does not update stations.shp.

## Summary vs production assignment

| Metric | Current (production) | Improved (v2) |
|---|---:|---:|
| Stations | 76 | 76 |
| Channel changed | — | **46** |
| Median \|Δ\| vs NHD TDA | 10.2% | 10.7% |
| Improved \|Δ\| vs NHD (count) | — | **18** |
| Median log-error vs USGS | 0.36 | 0.39 |
| Within 0.5–2.0× SWAT/NHD | 64 | 73 |
| Tributary-mode gages | 2 | (2 channel changes) |

## What improved

- **Tributary / small-basin gages** (USGS DA ≪ mainstem TDA in band): v2 picks local-scale NHD + matching channel — fixes gross mismatches like **02294760**.
- **SWAT/NHD ratio band**: more stations land in 0.5–2.0× (64 → 73); median \|Δ\| vs NHD TDA is **unchanged** (~10%) because mainstem QSWAT offset dominates.
- **Does not remove** mainstem ~15–17% QSWAT vs NHD offset on correctly assigned mainstem channels.

Detail: `peace-improved-station-assignment.csv`

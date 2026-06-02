# Station assignment v3 — portfolio inventory (evaluation roster (8 models))

NHD-first reference reach (no SWAT area), SWAT-second map to `chandeg.con`. **v3 is the production assignment method** used by `fetch_streamflow_for_watershed`.

**Peace (`03100101`) rows are frozen** from the prior inventory while that watershed model is rebuilt.

## Portfolio totals

| Metric | Value |
|--------|------:|
| Models in roster | 8 |
| Models in inventory | 8 |
| Models skipped (no shadow artifact) | 0 |
| USGS stations | 99 |
| Calibration-ready | 69 (69.7%) |
| Review class | 28 |
| Exclude / missing | 2 |
| Same GIS channel as legacy `stations.shp` | 45 (45.5%) |
| Changed vs legacy GIS channel | 54 (54.5%) |

## Per model

| Catalog ID | Workspace | Stations | Cal-ready | Review | Exclude | Legacy unchanged | Legacy changed |
|------------|-----------|---------:|----------:|-------:|--------:|----------------:|---------------:|
| `02297600` | `0310/huc12/02297600` | 1 | 1 | 0 | 0 | 1 | 0 |
| `03080102` | `0308/huc12/030801020804` | 4 | 3 | 0 | 1 | 0 | 4 |
| `03100101` | `0310/huc8/03100101` | 76 | 54 | 22 | 0 | 38 | 38 |
| `03152000` | `0503/huc12/03152000` | 6 | 3 | 3 | 0 | 2 | 4 |
| `05536265` | `0712/huc12/05536265` | 2 | 1 | 1 | 0 | 1 | 1 |
| `07174000` | `1107/huc12/07174000` | 3 | 1 | 1 | 1 | 1 | 2 |
| `09471300` | `1505/huc12/09471300` | 3 | 3 | 0 | 0 | 1 | 2 |
| `15060105` | `1506/huc8/15060105` | 4 | 3 | 1 | 0 | 1 | 3 |

Detail: `station-assignment-v3-inventory-detail.csv`

Shadow per-model artifacts were archived under `publication/analysis/qa/archive/` (inventory closed 2026-05-31).

# Station assignment v3 — portfolio inventory (showcase disk inventory (~70 models))

NHD-first reference reach (no SWAT area), SWAT-second map to `chandeg.con`. **v3 is the production assignment method** used by `fetch_streamflow_for_watershed`.

**Peace (`03100101`) rows are frozen** from the prior inventory while that watershed model is rebuilt.

## Portfolio totals

| Metric | Value |
|--------|------:|
| Models in roster | 70 |
| Models in inventory | 60 |
| Models skipped (no shadow artifact) | 10 |
| USGS stations | 254 |
| Calibration-ready | 179 (70.5%) |
| Review class | 66 |
| Exclude / missing | 9 |
| Same GIS channel as legacy `stations.shp` | 106 (41.7%) |
| Changed vs legacy GIS channel | 148 (58.3%) |

## Per model

| Catalog ID | Workspace | Stations | Cal-ready | Review | Exclude | Legacy unchanged | Legacy changed |
|------------|-----------|---------:|----------:|-------:|--------:|----------------:|---------------:|
| `01012515` | `0101/usgs_station/01012515` | 3 | 2 | 1 | 0 | 1 | 2 |
| `01073587` | `0106/usgs_station/01073587` | 2 | 2 | 0 | 0 | 0 | 2 |
| `01109090` | `0109/usgs_station/01109090` | 1 | 1 | 0 | 0 | 0 | 1 |
| `01115185` | `0109/usgs_station/01115185` | 4 | 4 | 0 | 0 | 1 | 3 |
| `01126000` | `0110/usgs_station/01126000` | 1 | 1 | 0 | 0 | 0 | 1 |
| `01443900` | `0204/usgs_station/01443900` | 4 | 4 | 0 | 0 | 0 | 4 |
| `01451800` | `0204/usgs_station/01451800` | 2 | 1 | 0 | 1 | 0 | 2 |
| `01480095` | `0204/usgs_station/01480095` | 2 | 2 | 0 | 0 | 1 | 1 |
| `01625900` | `0207/usgs_station/01625900` | 1 | 0 | 0 | 1 | 0 | 1 |
| `02135501` | `0304/usgs_station/02135501` | 4 | 3 | 0 | 1 | 1 | 3 |
| `02197598` | `0306/usgs_station/02197598` | 2 | 2 | 0 | 0 | 1 | 1 |
| `02231396` | `0308/usgs_station/02231396` | 1 | 1 | 0 | 0 | 1 | 0 |
| `02234990` | `0308/usgs_station/02234990` | 3 | 1 | 2 | 0 | 2 | 1 |
| `02239501` | `0308/usgs_station/02239501` | 4 | 3 | 0 | 1 | 0 | 4 |
| `02294217` | `0310/usgs_station/02294217` | 9 | 1 | 7 | 1 | 8 | 1 |
| `02294405` | `0310/usgs_station/02294405` | 12 | 2 | 10 | 0 | 8 | 4 |
| `02294760` | `0310/usgs_station/02294760` | 2 | 2 | 0 | 0 | 2 | 0 |
| `02297600` | `0310/usgs_station/02297600` | 1 | 1 | 0 | 0 | 1 | 0 |
| `02301738` | `0310/usgs_station/02301738` | 4 | 3 | 1 | 0 | 2 | 2 |
| `02398950` | `0315/usgs_station/02398950` | 1 | 1 | 0 | 0 | 0 | 1 |
| `03075500` | `0502/usgs_station/03075500` | 5 | 4 | 1 | 0 | 2 | 3 |
| `03100101` | `0310/huc8/03100101` | 76 | 54 | 22 | 0 | 38 | 38 |
| `031001010304` | `0310/huc12_outlet/031001010304` | 1 | 1 | 0 | 0 | 1 | 0 |
| `03141870` | `0504/usgs_station/03141870` | 1 | 1 | 0 | 0 | 1 | 0 |
| `03152000` | `0503/usgs_station/03152000` | 6 | 3 | 3 | 0 | 2 | 4 |
| `03252300` | `0510/usgs_station/03252300` | 1 | 0 | 1 | 0 | 0 | 1 |
| `03262001` | `0509/usgs_station/03262001` | 1 | 1 | 0 | 0 | 0 | 1 |
| `03302300` | `0514/usgs_station/03302300` | 1 | 1 | 0 | 0 | 0 | 1 |
| `03345000` | `0512/usgs_station/03345000` | 9 | 5 | 4 | 0 | 5 | 4 |
| `03441440` | `0601/usgs_station/03441440` | 1 | 1 | 0 | 0 | 0 | 1 |
| `03565250` | `0602/usgs_station/03565250` | 4 | 4 | 0 | 0 | 1 | 3 |
| `0407809265` | `0403/usgs_station/0407809265` | 1 | 1 | 0 | 0 | 1 | 0 |
| `04080206` | `0408/huc8/04080206` | 2 | 1 | 1 | 0 | 1 | 1 |
| `040900010212` | `0409/huc12_outlet/040900010212` | 2 | 1 | 0 | 1 | 0 | 2 |
| `04160398` | `0409/usgs_station/04160398` | 1 | 1 | 0 | 0 | 0 | 1 |
| `04288295` | `0430/usgs_station/04288295` | 4 | 4 | 0 | 0 | 4 | 0 |
| `05536265` | `0712/usgs_station/05536265` | 2 | 1 | 1 | 0 | 1 | 1 |
| `05580950` | `0713/usgs_station/05580950` | 1 | 0 | 0 | 1 | 0 | 1 |
| `06230500` | `1008/usgs_station/06230500` | 10 | 6 | 4 | 0 | 3 | 7 |
| `06439430` | `1012/usgs_station/06439430` | 1 | 0 | 0 | 1 | 0 | 1 |
| `06445590` | `1014/usgs_station/06445590` | 1 | 1 | 0 | 0 | 1 | 0 |
| `07062575` | `1101/usgs_station/07062575` | 9 | 6 | 3 | 0 | 4 | 5 |
| `07174000` | `1107/usgs_station/07174000` | 3 | 1 | 1 | 1 | 1 | 2 |
| `07375300` | `0807/usgs_station/07375300` | 2 | 2 | 0 | 0 | 0 | 2 |
| `08380400` | `1306/usgs_station/08380400` | 7 | 7 | 0 | 0 | 0 | 7 |
| `09312500` | `1406/usgs_station/09312500` | 3 | 3 | 0 | 0 | 2 | 1 |
| `09426500` | `1503/usgs_station/09426500` | 1 | 1 | 0 | 0 | 0 | 1 |
| `09471300` | `1505/usgs_station/09471300` | 3 | 3 | 0 | 0 | 1 | 2 |
| `09513860` | `1507/usgs_station/09513860` | 1 | 1 | 0 | 0 | 0 | 1 |
| `10246940` | `1606/usgs_station/10246940` | 1 | 1 | 0 | 0 | 0 | 1 |
| `10348850` | `1605/usgs_station/10348850` | 2 | 2 | 0 | 0 | 1 | 1 |
| `11152650` | `1806/usgs_station/11152650` | 2 | 1 | 1 | 0 | 0 | 2 |
| `11176145` | `1805/usgs_station/11176145` | 4 | 2 | 2 | 0 | 1 | 3 |
| `11458000` | `1805/usgs_station/11458000` | 10 | 10 | 0 | 0 | 5 | 5 |
| `11481200` | `1801/usgs_station/11481200` | 1 | 1 | 0 | 0 | 0 | 1 |
| `13329500` | `1706/usgs_station/13329500` | 1 | 1 | 0 | 0 | 0 | 1 |
| `14013500` | `1707/usgs_station/14013500` | 1 | 1 | 0 | 0 | 0 | 1 |
| `14111700` | `1707/usgs_station/14111700` | 1 | 1 | 0 | 0 | 0 | 1 |
| `14161500` | `1709/usgs_station/14161500` | 4 | 4 | 0 | 0 | 1 | 3 |
| `15060105` | `1506/huc8/15060105` | 4 | 3 | 1 | 0 | 0 | 4 |

## Skipped

- 050800010801: no station-assignment-v3-shadow-showcase-20260531/050800010801/stations_assignment_v3.csv
- 12096865: no station-assignment-v3-shadow-showcase-20260531/12096865/stations_assignment_v3.csv
- 02270000: no station-assignment-v3-shadow-showcase-20260531/02270000/stations_assignment_v3.csv
- 04087257: no station-assignment-v3-shadow-showcase-20260531/04087257/stations_assignment_v3.csv
- 04124500: no station-assignment-v3-shadow-showcase-20260531/04124500/stations_assignment_v3.csv
- 040400010207: no station-assignment-v3-shadow-showcase-20260531/040400010207/stations_assignment_v3.csv
- 102002030803: no station-assignment-v3-shadow-showcase-20260531/102002030803/stations_assignment_v3.csv
- 02271500: no station-assignment-v3-shadow-showcase-20260531/02271500/stations_assignment_v3.csv
- 04148140: no station-assignment-v3-shadow-showcase-20260531/04148140/stations_assignment_v3.csv
- 02269520: no station-assignment-v3-shadow-showcase-20260531/02269520/stations_assignment_v3.csv

Detail: `station-assignment-v3-showcase-inventory-detail.csv`

Shadow per-model artifacts were archived under `publication/analysis/qa/archive/` (inventory closed 2026-05-31).

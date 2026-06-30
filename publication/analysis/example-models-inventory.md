# Example SWAT+ models inventory (showcase disk)

**Purpose:** Choose candidate basins for the JAWRA evaluation protocol (e.g., small / medium / large tiers) from **successful on-disk** SWATGenX web-application workspaces.

**Source:** Disk scan of ``{USER_PATH}/admin/SWATplus_by_VPUID`` using ``web_application/app/example_models_catalog.py::build_disk_only_rows`` plus ``scripts/state_swat_modeling_sync_lib`` for ``model_kind`` and state resolution (same logic as ``scripts/example_models_disk_metrics.py``).

**Counts (this snapshot):**

| Metric | Value |
|--------|------:|
| Total successful workspaces | **70** |
| Level ``huc12`` | **67** |
| Level ``huc8`` | **3** |
| ``model_kind`` = ``usgs_station`` | **62** |
| ``model_kind`` = ``huc12_outlet`` | **5** |
| ``model_kind`` = ``huc8`` | **3** |
| US state resolved (2-letter) | **58** |
| State **not** resolved (manual follow-up) | **12** |
| ``generation_wall_min`` present | **18** (remainder not recorded from disk mtime pipeline) |

**Note on “67 models”:** The public ``/example-models`` catalog can differ slightly (e.g., HUC12 rows dropped when no ``FloodStation`` match, suppression list, or materialized JSON revision). This inventory is the **full disk-success set** for user ``admin``.

**Basin area (km²) quartiles (non-null):**  
{0.0: 25.25, 0.25: 107.69, 0.5: 213.39, 0.75: 478.84, 1.0: 3868.56}

**Machine-readable table:** [example-models-inventory.csv](example-models-inventory.csv) (sort in a spreadsheet; ``model_id`` matches internal path keys).

---

## Full model table (sorted by ``basin_area_sqkm``, then ``model_id``)

Empty cells mean unknown / not extracted from disk for that row.

| model_id                | model_kind   | state_abbr   | state_resolved   | basin_area_sqkm   |   n_hrus |   n_channels | n_subbasins   | n_lakes   | dem_resolution_m   | generation_wall_min   |
|:------------------------|:-------------|:-------------|:-----------------|:------------------|---------:|-------------:|:--------------|:----------|:-------------------|:----------------------|
| 0310/huc8/03100101      | huc8         |              | N                |                   |    94303 |         8181 |               |           |                    | 67.58                 |
| 0204/usgs_station/01480095     | usgs_station | DE           | Y                | 25.25             |      909 |           49 | 1.0           |           | 29.73              |                       |
| 1605/usgs_station/10348850     | usgs_station | NV           | Y                | 49.06             |      769 |           39 | 2.0           |           | 30.06              | 0.18                  |
| 1707/usgs_station/14013500     | usgs_station | WA           | Y                | 51.21             |     2344 |          379 | 1.0           |           | 30.03              | 0.95                  |
| 0308/usgs_station/02239501     | usgs_station | FL           | Y                | 52.64             |      473 |           45 | 4.0           | 4.0       | 30.01              | 0.13                  |
| 0712/usgs_station/05536265     | usgs_station | IL           | Y                | 58.94             |     1573 |          206 | 8.0           |           | 29.92              |                       |
| 1709/usgs_station/14161500     | usgs_station | OR           | Y                | 63.67             |     1316 |          790 | 8.0           |           | 30.0               | 0.47                  |
| 0508/huc12_outlet/050800010801 | huc12_outlet |              | N                | 65.97             |      824 |           43 | 1.0           |           | 29.89              |                       |
| 0514/usgs_station/03302300     | usgs_station | IN           | Y                | 67.94             |     9439 |         1659 | 4.0           |           | 30.05              |                       |
| 0310/usgs_station/02294760     | usgs_station | FL           | Y                | 75.38             |     1052 |           34 | 12.0          | 1.0       | 30.09              | 0.4                   |
| 1706/usgs_station/13329500     | usgs_station | OR           | Y                | 82.17             |     1453 |          533 | 1.0           |           | 29.99              |                       |
| 0109/usgs_station/01115185     | usgs_station | RI           | Y                | 85.34             |     3999 |          332 | 1.0           | 4.0       | 29.88              |                       |
| 0509/usgs_station/03262001     | usgs_station | KY           | Y                | 85.5              |     6469 |          770 | 1.0           |           | 30.03              |                       |
| 0109/usgs_station/01109090     | usgs_station | MA           | Y                | 89.74             |     4578 |          291 | 1.0           | 4.0       | 29.88              |                       |
| 0713/usgs_station/05580950     | usgs_station | IL           | Y                | 94.98             |     2553 |           94 | 3.0           |           | 29.93              |                       |
| 1711/usgs_station/12096865     | usgs_station | WA           | Y                | 97.06             |     4638 |         1147 | 2.0           |           | 29.87              | 2.48                  |
| 0310/usgs_station/02301738     | usgs_station | FL           | Y                | 105.78            |     2794 |          338 | 12.0          |           | 30.09              | 0.72                  |
| 0601/usgs_station/03441440     | usgs_station | NC           | Y                | 107.24            |    11824 |         2397 | 4.0           | 4.0       | 29.98              |                       |
| 0207/usgs_station/01625900     | usgs_station | VA           | Y                | 107.69            |     2754 |          234 | 2.0           |           | 29.94              |                       |
| 1801/usgs_station/11481200     | usgs_station | CA           | Y                | 116.01            |     2228 |          159 | 1.0           |           | 30.06              |                       |
| 1707/usgs_station/14111700     | usgs_station | WA           | Y                | 125.92            |     4348 |          472 | 1.0           |           | 30.03              |                       |
| 1014/usgs_station/06445590     | usgs_station | NE           | Y                | 128.45            |     5010 |          505 | 1.0           |           | 30.08              |                       |
| 0315/usgs_station/02398950     | usgs_station | AL           | Y                | 128.59            |     5911 |          457 | 2.0           | 1.0       | 29.89              |                       |
| 0309/usgs_station/02270000     | usgs_station | FL           | Y                | 144.31            |     1603 |           65 | 10.0          | 5.0       | 30.2               | 0.37                  |
| 0404/usgs_station/04087257     | usgs_station | WI           | Y                | 147.56            |     1512 |          147 | 4.0           |           | 29.9               |                       |
| 0406/usgs_station/04124500     | usgs_station | MI           | Y                | 158.04            |     5549 |          216 | 11.0          | 1.0       | 29.94              | 2.22                  |
| 0310/usgs_station/02294217     | usgs_station | FL           | Y                | 159.38            |     3302 |          174 | 6.0           | 13.0      | 30.09              | 0.75                  |
| 0310/huc12_outlet/031001010304 | huc12_outlet |              | N                | 165.38            |     3281 |          247 | 8.0           | 10.0      | 30.09              |                       |
| 0306/usgs_station/02197598     | usgs_station | GA           | Y                | 166.58            |     7650 |          529 | 1.0           | 3.0       | 29.9               |                       |
| 0101/usgs_station/01012515     | usgs_station | ME           | Y                | 176.52            |     2543 |           71 | 2.0           | 3.0       | 30.04              |                       |
| 0106/usgs_station/01073587     | usgs_station | NH           | Y                | 186.84            |    10736 |          760 | 3.0           | 8.0       | 29.91              |                       |
| 0310/usgs_station/02297600     | usgs_station | FL           | Y                | 189.12            |      778 |           37 | 4.0           |           | 30.09              | 3.08                  |
| 0110/usgs_station/01126000     | usgs_station | CT           | Y                | 197.82            |     8809 |         1133 | 3.0           | 22.0      | 29.89              |                       |
| 1507/usgs_station/09513860     | usgs_station | AZ           | Y                | 198.75            |     3926 |          459 | 4.0           |           | 30.07              |                       |
| 1805/usgs_station/11176145     | usgs_station | CA           | Y                | 202.67            |     4242 |          385 | 6.0           |           | 30.04              |                       |
| 0204/usgs_station/01451800     | usgs_station | PA           | Y                | 213.39            |     9296 |          520 | 4.0           |           | 29.73              |                       |
| 0308/usgs_station/02231396     | usgs_station | FL           | Y                | 226.72            |     1968 |          216 | 6.0           | 3.0       | 30.01              | 0.52                  |
| 0504/usgs_station/03141870     | usgs_station |              | N                | 237.4             |     9920 |          579 | 3.0           |           | 29.87              |                       |
| 0404/huc12_outlet/040400010207 | huc12_outlet |              | N                | 254.12            |     7385 |          593 | 9.0           | 5.0       | 29.9               |                       |
| 1306/usgs_station/08380400     | usgs_station | NM           | Y                | 254.5             |     3187 |          423 | 8.0           |           | 29.89              |                       |
| 0403/usgs_station/0407809265   | usgs_station | WI           | Y                | 262.24            |     3974 |          121 | 3.0           | 1.0       | 29.98              |                       |
| 0308/usgs_station/02234990     | usgs_station | FL           | Y                | 263.78            |     3823 |          166 | 8.0           | 9.0       | 30.01              | 0.82                  |
| 1406/usgs_station/09312500     | usgs_station | UT           | Y                | 264.1             |     4584 |          434 | 3.0           |           | 30.01              |                       |
| 1020/huc12_outlet/102002030803 | huc12_outlet |              | N                | 270.5             |     1786 |          123 | 2.0           |           | 30.29              |                       |
| 0430/usgs_station/04288295     | usgs_station | VT           | Y                | 290.03            |    13344 |         1239 | 4.0           | 2.0       | 29.96              |                       |
| 1806/usgs_station/11152650     | usgs_station | CA           | Y                | 290.82            |    11295 |         1484 | 3.0           | 1.0       | 29.97              |                       |
| 1012/usgs_station/06439430     | usgs_station | SD           | Y                | 315.78            |     9621 |         1142 | 8.0           |           | 30.05              |                       |
| 0602/usgs_station/03565250     | usgs_station | TN           | Y                | 344.92            |    18244 |          875 | 12.0          |           | 30.01              |                       |
| 0309/usgs_station/02271500     | usgs_station | FL           | Y                | 348.02            |     4397 |          283 | 15.0          | 16.0      | 30.2               | 1.08                  |
| 0310/usgs_station/02294405     | usgs_station | FL           | Y                | 370.16            |     7487 |          371 | 12.0          | 28.0      | 30.09              | 2.63                  |
| 1606/usgs_station/10246940     | usgs_station | NV           | Y                | 392.34            |     3046 |          379 | 9.0           |           | 30.02              |                       |
| 0204/usgs_station/01443900     | usgs_station | NJ           | Y                | 450.21            |    21296 |         2664 | 112.0         | 19.0      | 29.73              |                       |
| 0502/usgs_station/03075500     | usgs_station |              | N                | 478.84            |    16386 |          667 | 4.0           | 7.0       | 29.78              |                       |
| 0409/huc12_outlet/040900010212 | huc12_outlet |              | N                | 479.79            |    10702 |          561 | 5.0           | 2.0       | 29.97              |                       |
| 0510/usgs_station/03252300     | usgs_station |              | N                | 488.06            |    18988 |         1323 | 7.0           |           | 29.95              |                       |
| 0409/usgs_station/04160398     | usgs_station | MI           | Y                | 504.26            |     9790 |          489 | 7.0           |           | 29.97              |                       |
| 0408/usgs_station/04148140     | usgs_station | MI           | Y                | 531.0             |     2530 |           35 | 3.0           | 10.0      | 250.0              |                       |
| 1505/usgs_station/09471300     | usgs_station | AZ           | Y                | 580.26            |    11284 |         1371 | 12.0          |           | 30.03              |                       |
| 0408/huc8/04080206      | huc8         |              | N                | 650.44            |     5976 |          579 | 12.0          | 1.0       | 29.99              |                       |
| 1503/usgs_station/09426500     | usgs_station | AZ           | Y                | 681.81            |     4008 |          597 | 7.0           |           | 30.01              |                       |
| 1805/usgs_station/11458000     | usgs_station | CA           | Y                | 733.36            |    21980 |         2512 | 17.0          | 5.0       | 30.04              |                       |
| 0309/usgs_station/02269520     | usgs_station | FL           | Y                | 791.58            |     6987 |          386 | 25.0          | 17.0      | 30.2               | 1.95                  |
| 0807/usgs_station/07375300     | usgs_station | LA           | Y                | 824.95            |    28570 |         1826 | 32.0          | 2.0       | 29.99              |                       |
| 0503/usgs_station/03152000     | usgs_station |              | N                | 1017.1            |    19530 |         1615 | 10.0          | 1.0       | 29.82              |                       |
| 1107/usgs_station/07174000     | usgs_station | KS           | Y                | 1116.28           |    36855 |         2370 | 9.0           | 15.0      | 30.0               | 17.03                 |
| 0304/usgs_station/02135501     | usgs_station | SC           | Y                | 1168.35           |    35137 |         4467 | 13.0          | 21.0      | 29.91              |                       |
| 1008/usgs_station/06230500     | usgs_station | WY           | Y                | 1712.39           |    21532 |         2657 | 54.0          | 35.0      | 30.01              |                       |
| 1506/huc8/15060105      | huc8         |              | N                | 2715.83           |    51685 |        17296 | 28.0          |           | 30.08              |                       |
| 1101/usgs_station/07062575     | usgs_station | MO           | Y                | 2940.95           |    77493 |         5788 | 40.0          | 10.0      | 30.04              |                       |
| 0512/usgs_station/03345000     | usgs_station | IL           | Y                | 3868.56           |    79467 |         5456 | 64.0          | 5.0       | 29.9               |                       |

---

## Selection hints (non-binding)

- **Small tier:** lower quartile of ``basin_area_sqkm`` (roughly under ~110 km² among resolved areas)—favor ``state_resolved=Y`` and ``usgs_station`` if you want NWIS naming consistency.
- **Medium tier:** near median (~213 km²).
- **Large tier:** upper quartile to max; expect high ``n_hrus`` / ``n_channels`` (e.g., one HUC8 row reaches 94k HRUs—likely too heavy for a default “large” case unless intentionally stress-testing).
- **HUC12 outlet vs USGS gage:** ``huc12_outlet`` rows are not in the FPS gage list; treat outlet semantics separately from NWIS-titled basins.
- **DEM column:** values near **30** m are the nominal NHD-aligned pipeline; **250** m flags a different DEM tier—check flood/DEM policy before using in a paper case study.
- **Runtime:** ``generation_wall_min`` is only populated when derivable from disk metadata; do **not** treat missing cells as zero—use a fresh timed run for **Tab-Runtime** per the evaluation protocol.

**TODO:** Pick three basin ``model_id`` values and lock them in ``publication/analysis/evaluation-protocol.md``.

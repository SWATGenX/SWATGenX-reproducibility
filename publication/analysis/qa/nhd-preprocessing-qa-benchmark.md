# NHD preprocessing QA (original zip vs delivered product)

Generated at 2026-05-31T19:29:41Z.

**Input:** USGS NHDPlus HR HU4 GDB zip (temporary unzip, then deleted).
**Output:** admin workspace `rivs1.shp` / `subs1.shp` / `SWAT_plus_watersheds.shp`.

| Tier | Model | Orig. catch. | Orig. flow | Div-2 | Isol. reach | Isol. cat. | Orphan cat. | No-VAA | Final ch. | Final ws. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S | `03080102` | 56 | 56 | 2 | 2 | 2 | 4 | 0 | 45 | 53 |
| M | `09471300` | 1382 | 1382 | 11 | 0 | 0 | 11 | 0 | 1371 | 1371 |
| L | `03100101` | 9739 | 9705 | 194 | 88 | 88 | 282 | 34 | 8181 |  |
| X20 | `03152000` | 1659 | 1659 | 2 | 0 | 0 | 2 | 0 | 1615 | 1657 |
| X40 | `07174000` | 2473 | 2473 | 12 | 2 | 2 | 14 | 0 | 2329 | 2418 |
| X60 | `15060105` | 17469 | 17469 | 173 | 0 | 0 | 173 | 0 | 17296 | 17296 |
| calibration | `02297600` | 41 | 41 | 0 | 4 | 4 | 4 | 0 | 37 | 37 |
| calibration | `05536265` | 224 | 224 | 6 | 13 | 13 | 19 | 0 | 206 | 206 |

- **Isol. reach / cat.** = isolated flowlines (both hydroseq links zero) and their catchment polygons, removed and dissolved into neighbours.
- **Orphan cat.** = catchments whose original flowline was dropped by div-2/isolated/coastal rules (polygon merged, not retained as standalone).

Manuscript CSV: `tab-nhd-preprocessing-qa.csv`

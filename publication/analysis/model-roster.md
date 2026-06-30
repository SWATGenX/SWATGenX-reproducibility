# Manuscript model roster (canonical)

Readers see **three non-overlapping evaluation sets**. No other model IDs appear in manuscript tables or Results claims.

## 1. Benchmark package trio (S / M / L)

Same three SWATGenX packages as the public page [/swat-plus-runtime-benchmark](https://www.swatgenx.com/swat-plus-runtime-benchmark).

| Tier | Model ID | Basin | Objectives |
|------|----------|-------|------------|
| S | `03080102` | Oklawaha (FL) | 3 (structure, generation cost), 5 (simulation) |
| M | `09471300` | Upper San Pedro (AZ) | 3, 5 |
| L | `03100101` | Peace River HUC-8 (FL) | 3, 5 |

**Tables:** Tab-ModelComplexity, Tab-ProductMetrics, Tab-Runtime (generation), Tab-RuntimeBenchmark (primary S/M/L rows).

Workspace paths (`0308/huc12_outlet/030801020804`, etc.) are internal only; manuscript tables use **catalog Model ID**.

## 2. Simulation scaling ladder (X20 / X40 / X60)

Three additional benchmark packages **only** for Objective 5 HRU scaling, routing-density discussion, and limitations (not structural showcase maps).

| Tier | Model ID | Basin |
|------|----------|-------|
| X20 | `03152000` | Little Kanawaha (WV) |
| X40 | `07174000` | Verdigris River (KS) |
| X60 | `15060105` | Upper Gila HUC-8 (AZ) |

**Tables:** Tab-RuntimeBenchmark-HRUScaling (six-point ladder S→L).

## 3. Calibration / sensitivity pair

Compact HUC12 gage watersheds **separate** from the benchmark set; used only for Objective 4 workflow evidence.

| Site | Model ID | State |
|------|----------|-------|
| `02297600` | `0310/usgs_station/02297600` | Florida |
| `05536265` | `0712/usgs_station/05536265` | Illinois |

**Tables:** Tab-Metrics, Tab-Sensitivity-Morris (Florida complete), cal/val figures.

## Excluded from manuscript

Legacy pilots and proof basins (`02239501`, `01451800`, `01567500`, etc.) remain in repo audit CSVs but are **not** cited in manuscript prose or official tables.

Machine-readable roster: `publication/tables/tab-model-roster.csv`.

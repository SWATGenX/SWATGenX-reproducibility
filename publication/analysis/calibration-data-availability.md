# Streamflow observation availability — locked evaluation basins

**Purpose:** Support a defensible calibration / validation **period choice** before any SWATGenX PSO execution.  
**Constraint:** This document **does not** assert hydrologic skill, calibrated performance, or manuscript Results claims.

---

## Locked basins (source of truth)

Rows are taken from `publication/tables/tab-model-complexity.csv` (`status=locked_from_inventory`).

| model_id | tier | site_no | state | area (km²) |
|----------|------|---------|-------|------------|
| 0308/huc12/02239501 | Small | 02239501 | FL | 52.64 |
| 0204/huc12/01451800 | Medium | 01451800 | PA | 213.39 |
| 1107/huc12/07174000 | Large | 07174000 | KS | 1116.28 |

---

## Data source and retrieval

- **Source:** USGS NWIS **daily values** (dv) service, parameter **`00060`** (discharge, cfs), `siteStatus=all`, JSON response.
- **Request pattern:** `https://waterservices.usgs.gov/nwis/dv/?sites=<site_no>&parameterCd=00060&startDT=1850-01-01&endDT=2026-12-31&siteStatus=all&format=json`
- **Retrieval date (audit):** **2026-05-13** (repository audit run; use the same date when citing this audit).
- **Local repo copies:** No `streamflow_data/*.csv` files for these sites are committed under this repository. Operational runs expect operator-provided daily CSVs under the per-user model tree (see `publication/analysis/calibration-source-map.md` — **no private absolute host paths** in manuscript-facing tables).

---

## Definitions (aligned with tables)

- **total_days:** Calendar span `(last_date − first_date) + 1` for which NWIS returned at least one daily value in the series.
- **available_days:** Distinct dates with a numeric daily value in that span.
- **missing_days:** `total_days − available_days` (days within the NWIS-reported span with no daily record).
- **missing_fraction:** `missing_days / total_days` for the NWIS span (not automatically the same as SWATGenX `read_observed_data` gap logic inside a chosen evaluation window).
- **longest continuous:** Longest run of consecutive calendar days **with** a daily value (within `first_date`–`last_date`).
- **SWATGenX gap rule (downstream):** `ModelProcessing/ModelProcessing/evaluation.py` treats **>10%** missing daily observations in the evaluated window as failing that station for the objective (score `0`). Windows in `tab-streamflow-availability.csv` were checked for **calendar completeness** of NWIS daily values.

---

## Summary outcomes

| site_no | NWIS daily 00060 span | Missing (full NWIS span) | Default manuscript windows (2000–2002 warm / 2003–2010 cal / 2012–2015 val) | Verdict |
|---------|----------------------|----------------------------|--------------------------------------------------------------------------------|---------|
| **02239501** | 1932-10-01 → 2026-05-12 | 0% | **0% missing days** in each window | Suitable for pilot calibration / validation **if** forcing and model tree cover those years. |
| **01451800** | 1966-02-01 → 2026-05-12 | ~0.35% overall; longest contiguous block ends before final NWIS day | **0% missing** in each listed window | Suitable for streamflow-driven calibration **if** model package exists; overall record has minor gaps elsewhere. |
| **07174000** | **1943-10-01 → 1958-09-29 only** | 0% within that legacy span | **100% missing** in 2000–2002, 2003–2010, and 2012–2015 (no NWIS daily values returned for those dates) | **Not usable** for the default 2000s–2010s calibration split without a **different gage** or a **historical-only** protocol (not proposed here). |

---

## Recommended periods (for FL / PA pilot aligned with `ModelConfig` defaults)

These match `ModelProcessing/ModelProcessing/config.py` and `ModelProcessing/main.py` defaults (`START_YEAR=2000`, `END_YEAR=2010`, `nyskip=3`, `Ver_START_YEAR=2011`, `Ver_END_YEAR=2015`, `Ver_nyskip=1`):

- **Warm-up (scoring exclusion, not “missing NWIS”):** SWAT uses **`nyskip=3`** full calendar years after `START_YEAR`; daily observations should exist from **`2000-01-01`** through the end of calibration so overlap checks succeed.
- **Calibration scoring (daily + monthly NSE in code):** **`2003-01-01`–`2010-12-31`** inclusive.
- **Validation scoring:** **`2012-01-01`–`2015-12-31`** inclusive (first verification calendar year skipped via `Ver_nyskip=1`).

**Split rationale:** Holdout period after calibration end; standard split-sample narrative for a plausibility demo (see `publication/analysis/calibration-plan.md`).

---

## Kansas large basin (07174000) — explicit decision

NWIS daily discharge for **`07174000`** in this audit **does not extend past 1958-09-29**. Any workflow that assumes **2000–2015** NWIS daily Q at this ID will have **no observations** in those years.

**Planned actions (outside this branch):**

1. Confirm NHDPlus / model outlet pairing (correct legacy vs active site, agency code, or relocated gage).
2. If no modern NWIS daily site exists for that outlet, keep **1107/huc12/07174000** as a **package / scalability** tier only until hydrology data are resolved.
3. Do **not** claim calibration or validation for KS under the default windows until observation availability is fixed.

---

## Artifacts

- Machine-readable table: `publication/tables/tab-streamflow-availability.csv`
- Execution intent (not run on this branch): `publication/tables/tab-calibration-run-settings.csv`

# Legacy `/huc12/` path audit summary

**Date:** 2026-06-14  
**Tool:** `scripts/audit_and_fix_legacy_huc12_paths.py`  
**Machine-readable log:** [legacy-huc12-path-audit.csv](legacy-huc12-path-audit.csv)

## What was replaced

Legacy model workspace keys `{vpuid}/huc12/{site}` → kind-specific levels:

| `model_kind` | New level segment |
|--------------|-------------------|
| USGS gage | `usgs_station` |
| HUC12 outlet catalog | `huc12_outlet` |
| HUC8 basin | `huc8` (unchanged) |

Replacement patterns applied across the repo:

- Short `model_id` keys: `0310/huc12/02297600` → `0310/usgs_station/02297600`
- Full workspace paths: `SWATplus_by_VPUID/{vpuid}/huc12/{site}`
- Floodplain asset paths: `floodplain/huc12/{site}` → `floodplain/{kind}/{site}`

Classification source: `publication/analysis/example-models-inventory.csv` plus `classify_catalog_model_kind` for any additional `(vpuid, site)` pairs found in scanned files.

## Intentionally left as `/huc12/`

| Category | Examples | Reason |
|----------|----------|--------|
| **Flood Explorer API** | `/api/flood/huc12/…`, `/api/flood/explorer/huc12/…` | HUC12 *watershed* endpoints, not model level dirs |
| **Migration tooling** | `scripts/migrate_legacy_huc12_dirs.py` | Documents the legacy layout being removed |
| **GenXAppData gwflow tree** | `GenXAppData/…/0000/huc12/{name}` | Separate MODFLOW/gwflow data layout |
| **MODFLOW archive** | `MODGenX/archive/*.py` | Historical `0000/huc12` test harness |
| **Dev one-offs** | `NSRDB_elev_correction.py`, `test_climate_check.py` | Parameterized `{VPUID}/huc12/{NAME}` dev paths — update when those scripts are next touched |
| **Archived run logs** | `swatplus_perf/benchmark-results/.../run.log` | Immutable historical logs |

## Code fixes bundled with the sweep

- `export_objectives_4_5.py` — workspace paths derived from `model_id` level segment
- `verify_calval_split202606_postrun.py` — `level: usgs_station` in basin specs
- `stateSwatExplorerDeepLink.js` + `fileBrowserUtils.js` — accept `usgs_station` / `huc12_outlet` model ids for Explorer deep links
- Publication README / evaluation-protocol / scripts README — template paths use `<level>` not hardcoded `huc12`

## Re-run

```bash
.venv/bin/python scripts/audit_and_fix_legacy_huc12_paths.py --audit-only
.venv/bin/python scripts/audit_and_fix_legacy_huc12_paths.py --apply
```

## Follow-ups (optional)

1. Regenerate `catalogModelPages.generated.json` / `stateSwatModelingRecords.generated.json` from export scripts so `cdl_raster_summary_path` uses on-disk floodplain level dirs.
2. Run `scripts/migrate_legacy_huc12_dirs.py --apply` for any remaining on-disk `Users/.../huc12/` trees.
3. Phase 4: drop FPS-membership kind inference once DB + disk are fully migrated.

# Peace station assignment — v3 inventory (canonical)

Merged **Phase 1b** (NHD-first reference) + **Phase 2** (SWAT-second map) + **drainage investigation v2** (TxtInOut vs NHD at v1b and production GIS channels).

- **Stations:** 76
- **Calibration-ready:** 54 (`mainstem_clean`, `tributary_clean`, `mainstem_known_nhd_offset` with `chandeg_present`)
- **Exact crosswalk:** 61
- **Missing chandeg map:** 0

## Assignment class

| Class | n |
|-------|---:|
| `tributary_clean` | 36 |
| `mainstem_known_nhd_offset` | 16 |
| `lake_outlet_review` | 13 |
| `canal_or_artificial_review` | 9 |
| `mainstem_clean` | 2 |

## Mapping method

| Method | n |
|--------|---:|
| `exact_crosswalk` | 61 |
| `lake_outlet_replacement` | 10 |
| `downstream_replacement` | 5 |

## Column groups

| Group | Fields |
|-------|--------|
| NWIS | `site_no`, `station_name`, `usgs_da_km2`, name tokens |
| NHD-first | `v1b_nhdplusid`, `reference_*`, `v1b_pick_rule`, Phase 1b comparison |
| SWAT-second | `swat_gis_id`, `mapping_method`, `mapped_nhdplusid`, `replacement_steps_downstream` |
| Audit | `nhd_tda_km2`, `swat_da_km2`, `swat_nhd_ratio`, `audit_v1b_*`, `audit_prod_*` |
| Decision | `assignment_class`, `calibration_eligible`, `reason_code` |

Full table: `peace-station-assignment-v3-inventory.csv`

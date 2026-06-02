#!/usr/bin/env python3
"""Merge Peace Phase 1b + Phase 2 + drainage audit into canonical v3 inventory.

Outputs:
  - publication/analysis/qa/peace-station-assignment-v3-inventory.csv
  - publication/analysis/qa/peace-station-assignment-v3-inventory.md
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
PHASE0 = REPO / "publication/analysis/qa/peace-station-assignment-phase0-inventory.csv"
PHASE1B = REPO / "publication/analysis/qa/peace-station-assignment-phase1b-comparison.csv"
PHASE2 = REPO / "publication/analysis/qa/peace-station-assignment-phase2-swat-map.csv"
DRAIN_V2 = REPO / "publication/analysis/qa/peace-drainage-area-investigation-v2.csv"
OUT_CSV = REPO / "publication/analysis/qa/peace-station-assignment-v3-inventory.csv"
OUT_MD = REPO / "publication/analysis/qa/peace-station-assignment-v3-inventory.md"

CALIBRATION_READY = frozenset({"mainstem_clean", "tributary_clean", "mainstem_known_nhd_offset"})

REASON_BY_CLASS = {
    "mainstem_clean": "calibration_ready",
    "tributary_clean": "calibration_ready",
    "mainstem_known_nhd_offset": "calibration_ready_documented_nhd_offset",
    "lake_outlet_review": "lake_outlet_manual_review",
    "canal_or_artificial_review": "canal_or_artificial_manual_review",
    "assignment_ambiguous": "assignment_ambiguous",
    "missing_output_channel": "missing_output_channel",
    "exclude_from_auto_calibration": "exclude_from_auto_calibration",
}


def _zsite(s: pd.Series) -> pd.Series:
    return s.astype(str).str.zfill(8)


def _pct_diff(swat: float | None, ref: float | None) -> float | None:
    if swat is None or ref is None or ref <= 0:
        return None
    return (swat - ref) / ref * 100.0


def calibration_eligible(row: pd.Series) -> bool:
    if not bool(row.get("chandeg_present")):
        return False
    return str(row.get("assignment_class") or "") in CALIBRATION_READY


def reason_code(row: pd.Series) -> str:
    if not bool(row.get("chandeg_present")):
        return "missing_chandeg"
    ac = str(row.get("assignment_class") or "")
    if ac in REASON_BY_CLASS:
        return REASON_BY_CLASS[ac]
    return "manual_review"


def main() -> None:
    p2 = pd.read_csv(PHASE2, dtype={"site_no": str})
    p2["site_no"] = _zsite(p2["site_no"])

    p1b = pd.read_csv(PHASE1B, dtype={"usgs_site_no": str})
    p1b["site_no"] = _zsite(p1b["usgs_site_no"])
    p1b = p1b.drop(columns=["usgs_site_no"], errors="ignore")

    p0 = pd.read_csv(PHASE0, dtype={"usgs_site_no": str})
    p0["site_no"] = _zsite(p0["usgs_site_no"])
    p0_cols = [
        "site_no",
        "usgs_da_km2",
        "usgs_da_source",
        "name_peace_river",
        "name_tributary",
        "name_lake_outlet",
        "name_lake",
        "name_canal",
        "production_nhdplusid",
        "production_nhd_pick_rule",
        "nhd_first_totdasqkm",
        "nhd_first_streamorde",
        "nhd_first_ftype",
        "nhd_first_gnis",
    ]
    p0 = p0[[c for c in p0_cols if c in p0.columns]]

    aud = pd.read_csv(DRAIN_V2, dtype={"usgs_site_no": str})
    aud["site_no"] = _zsite(aud["usgs_site_no"])
    aud = aud.rename(columns={"gis_channel": "audit_gis_channel"})
    aud_v1b = aud.add_prefix("audit_v1b_").rename(columns={"audit_v1b_site_no": "site_no"})
    aud_v1b = aud_v1b.rename(columns={"audit_v1b_audit_gis_channel": "swat_gis_id"})
    aud_prod = aud.add_prefix("audit_prod_").rename(columns={"audit_prod_site_no": "site_no"})
    aud_prod = aud_prod.rename(columns={"audit_prod_audit_gis_channel": "production_gis_channel"})

    df = p2.merge(p1b, on="site_no", how="left", suffixes=("", "_p1b"))
    if "station_name_p1b" in df.columns:
        df = df.drop(columns=["station_name_p1b"])
    df = df.merge(p0, on="site_no", how="left", suffixes=("", "_p0"))
    df = df.merge(
        aud_v1b,
        on=["site_no", "swat_gis_id"],
        how="left",
    )
    df = df.merge(
        aud_prod,
        on=["site_no", "production_gis_channel"],
        how="left",
    )

    df["calibration_eligible"] = df.apply(calibration_eligible, axis=1)
    df["reason_code"] = df.apply(reason_code, axis=1)
    df["swat_nhd_pct_diff"] = df.apply(
        lambda r: _pct_diff(
            float(r["swat_da_km2"]) if pd.notna(r.get("swat_da_km2")) else None,
            float(r["nhd_tda_km2"]) if pd.notna(r.get("nhd_tda_km2")) else None,
        ),
        axis=1,
    )
    df["prod_eq_v1b_nhd"] = df["production_nhdplusid"] == df["v1b_nhdplusid"]
    df["prod_eq_v1b_gis"] = df["production_gis_channel"] == df["swat_gis_id"]

    col_order = [
        "site_no",
        "station_name",
        "usgs_da_km2",
        "usgs_da_source",
        "name_peace_river",
        "name_tributary",
        "name_lake_outlet",
        "name_lake",
        "name_canal",
        "v1b_nhdplusid",
        "v1b_pick_rule",
        "reference_class",
        "reference_gnis",
        "reference_ftype",
        "reference_has_wb_link",
        "nhd_first_totdasqkm",
        "nhd_first_streamorde",
        "nhd_first_ftype",
        "nhd_first_gnis",
        "swat_gis_id",
        "swat_lcha",
        "mapping_method",
        "mapped_nhdplusid",
        "replacement_steps_downstream",
        "chandeg_present",
        "nhd_tda_km2",
        "swat_da_km2",
        "swat_nhd_ratio",
        "swat_nhd_pct_diff",
        "assignment_class",
        "calibration_eligible",
        "reason_code",
        "production_gis_channel",
        "production_nhdplusid",
        "production_nhd_pick_rule",
        "production_nhdplusid_p1b",
        "v1_draft_nhdplusid",
        "production_pick_rule",
        "v1_draft_pick_rule",
        "v1b_context",
        "prod_eq_v1b",
        "prod_eq_v1b_nhd",
        "prod_eq_v1b_gis",
        "v1b_changed_from_draft",
        "audit_v1b_ratio_swat_vs_tda",
        "audit_v1b_pct_diff_vs_tda",
        "audit_v1b_ratio_swat_vs_orig_up",
        "audit_prod_ratio_swat_vs_tda",
        "audit_prod_pct_diff_vs_tda",
        "notes",
    ]
    present = [c for c in col_order if c in df.columns]
    rest = [c for c in df.columns if c not in present]
    df = df[present + rest].sort_values("site_no")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    n = len(df)
    n_cal = int(df["calibration_eligible"].sum())
    by_class = df["assignment_class"].value_counts()
    by_map = df["mapping_method"].value_counts()

    lines = [
        "# Peace station assignment — v3 inventory (canonical)",
        "",
        "Merged **Phase 1b** (NHD-first reference) + **Phase 2** (SWAT-second map) + "
        "**drainage investigation v2** (TxtInOut vs NHD at v1b and production GIS channels).",
        "",
        f"- **Stations:** {n}",
        f"- **Calibration-ready:** {n_cal} (`mainstem_clean`, `tributary_clean`, `mainstem_known_nhd_offset` with `chandeg_present`)",
        f"- **Exact crosswalk:** {int((df['mapping_method'] == 'exact_crosswalk').sum())}",
        f"- **Missing chandeg map:** {int((df['mapping_method'] == 'missing').sum())}",
        "",
        "## Assignment class",
        "",
        "| Class | n |",
        "|-------|---:|",
    ]
    for cls, cnt in by_class.items():
        lines.append(f"| `{cls}` | {cnt} |")
    lines.extend(
        [
            "",
            "## Mapping method",
            "",
            "| Method | n |",
            "|--------|---:|",
        ]
    )
    for meth, cnt in by_map.items():
        lines.append(f"| `{meth}` | {cnt} |")
    lines.extend(
        [
            "",
            "## Column groups",
            "",
            "| Group | Fields |",
            "|-------|--------|",
            "| NWIS | `site_no`, `station_name`, `usgs_da_km2`, name tokens |",
            "| NHD-first | `v1b_nhdplusid`, `reference_*`, `v1b_pick_rule`, Phase 1b comparison |",
            "| SWAT-second | `swat_gis_id`, `mapping_method`, `mapped_nhdplusid`, `replacement_steps_downstream` |",
            "| Audit | `nhd_tda_km2`, `swat_da_km2`, `swat_nhd_ratio`, `audit_v1b_*`, `audit_prod_*` |",
            "| Decision | `assignment_class`, `calibration_eligible`, `reason_code` |",
            "",
            f"Full table: `{OUT_CSV.name}`",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_CSV} ({n} rows, {n_cal} calibration-ready)")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

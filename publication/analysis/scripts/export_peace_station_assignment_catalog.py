#!/usr/bin/env python3
"""Export Peace pilot station-assignment summary + v3 table for the public CRA page."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
V3 = REPO / "publication/analysis/qa/peace-station-assignment-v3-inventory.csv"
OUT = REPO / "web_application/frontend/src/data/peaceStationAssignmentCatalog.json"
PAGE_CATALOG = REPO / "web_application/frontend/src/data/stationAssignmentPageCatalog.json"

CALIBRATION_READY = frozenset({"mainstem_clean", "tributary_clean", "mainstem_known_nhd_offset"})


def _json_val(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    if isinstance(v, (np.integer, np.floating)):
        return float(v) if isinstance(v, np.floating) else int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    return v


def _row_record(r: pd.Series) -> dict:
    return {
        "siteNo": str(r["site_no"]),
        "stationName": str(r["station_name"]) if pd.notna(r["station_name"]) else None,
        "usgsDaKm2": _json_val(r.get("usgs_da_km2")),
        "v1bNhdplusid": _json_val(r.get("v1b_nhdplusid")),
        "referenceClass": str(r["reference_class"]) if pd.notna(r.get("reference_class")) else None,
        "referenceGnis": str(r["reference_gnis"]) if pd.notna(r.get("reference_gnis")) else None,
        "swatGisId": _json_val(r.get("swat_gis_id")),
        "productionGisId": _json_val(r.get("production_gis_channel")),
        "mappingMethod": str(r["mapping_method"]) if pd.notna(r.get("mapping_method")) else None,
        "assignmentClass": str(r["assignment_class"]) if pd.notna(r.get("assignment_class")) else None,
        "calibrationEligible": bool(r.get("calibration_eligible")),
        "reasonCode": str(r["reason_code"]) if pd.notna(r.get("reason_code")) else None,
        "nhdTdaKm2": _json_val(r.get("nhd_tda_km2")),
        "swatDaKm2": _json_val(r.get("swat_da_km2")),
        "swatNhdRatio": _json_val(r.get("swat_nhd_ratio")),
        "swatNhdPctDiff": _json_val(r.get("swat_nhd_pct_diff")),
        "prodEqV1bGis": _json_val(r.get("prod_eq_v1b_gis")),
    }


def main() -> None:
    if not V3.is_file():
        raise SystemExit(f"Missing v3 inventory — run build_peace_station_assignment_v3_inventory.py first: {V3}")

    df = pd.read_csv(V3, dtype={"site_no": str})
    df["site_no"] = df["site_no"].str.zfill(8)
    cal = df[df["calibration_eligible"] == True]  # noqa: E712
    ratios = cal["swat_nhd_ratio"].dropna()

    peace = {
        "pilotHuc8": "03100101",
        "pilotLabel": "Peace River HUC-8",
        "nStations": int(len(df)),
        "mappingMethod": {k: int(v) for k, v in df["mapping_method"].value_counts().items()},
        "assignmentClass": {k: int(v) for k, v in df["assignment_class"].value_counts().items()},
        "nCalibrationReady": int(len(cal)),
        "nExactCrosswalk": int((df["mapping_method"] == "exact_crosswalk").sum()),
        "nDownstreamReplacement": int(df["mapping_method"].str.contains("replacement", na=False).sum()),
        "nMissing": int((df["mapping_method"] == "missing").sum()),
        "medianSwatNhdRatioCalibrationReady": float(ratios.median()) if len(ratios) else None,
        "productionVsV1bSameGis": int(df["prod_eq_v1b_gis"].sum()) if "prod_eq_v1b_gis" in df.columns else None,
        "productionVsV1bTotal": int(len(df)),
        "anchors": [],
        "stations": [_row_record(r) for _, r in df.sort_values("site_no").iterrows()],
    }

    for site in ("02294760", "02294650"):
        r = df[df["site_no"] == site].iloc[0]
        peace["anchors"].append(
            {
                "siteNo": site,
                "stationName": str(r["station_name"]),
                "v1bNhdplusid": _json_val(r["v1b_nhdplusid"]),
                "swatGisId": _json_val(r["swat_gis_id"]),
                "productionGisId": _json_val(r["production_gis_channel"]),
                "mappingMethod": str(r["mapping_method"]),
                "assignmentClass": str(r["assignment_class"]),
                "swatNhdRatio": _json_val(r["swat_nhd_ratio"]),
                "referenceClass": str(r["reference_class"]),
                "calibrationEligible": bool(r["calibration_eligible"]),
            }
        )

    payload = {
        "methodVersion": "peace_v3_nhd_first_v1b_swat_second_phase2",
        "inventorySource": "peace-station-assignment-v3-inventory.csv",
        "productionMethodSummary": (
            "Within 500 m, select channel whose QSWAT AreaC best matches NWIS drainage area in log-space (da_distance)."
        ),
        "improvedMethodSummary": (
            "NHD-first reference reach (hydrography + NWIS context, no SWAT area), then SWAT-second map to chandeg.con."
        ),
        "peacePilot": peace,
        "calibrationReadyClasses": list(CALIBRATION_READY),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(peace['stations'])} stations)")
    if PAGE_CATALOG.is_file():
        print(f"(page catalog: run export_station_assignment_page_catalog.py — {PAGE_CATALOG.name})")


if __name__ == "__main__":
    main()

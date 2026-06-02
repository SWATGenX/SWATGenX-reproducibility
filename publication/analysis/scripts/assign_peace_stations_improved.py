#!/usr/bin/env python3
"""Peace HUC-8: improved gage → SWAT+ channel assignment (proposal; does not rewrite stations.shp).

Method **swatgenx_v2** (relative to production):
  1. Classify gage as tributary vs cumulative from USGS DA vs NHD TotDASqKm in the 500 m band.
  2. Pick target NHD reach on original HR (local AreaSqKm vs USGS for tributary; TotDASqKm vs USGS for cumulative).
  3. Map to GIS channel: exact crosswalk NHD ID match among candidates, else best composite score
     (SWAT area vs target NHD TDA + USGS + distance + stream order).
  4. Drop poor crosswalk snaps (>150 m) when better snaps exist.

Outputs CSV + JSON for the public drainage-area audit page. Peace only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    GAGE_RADIUS_M,
    HUC8,
    STATIONS_SHP,
    TXTINOUT,
    VPUID,
    load_nhd_flowlines_domain,
    load_usgs_da_km2,
    pick_nhd_reach,
)
from investigate_peace_drainage_area_upstream import (  # noqa: E402
    SNAP_M,
    parse_chandeg_gis_points,
    snap_gis_to_nhd_orig,
)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

OUT_DIR = REPO / "publication/analysis/qa"
OUT_CSV = OUT_DIR / "peace-improved-station-assignment.csv"
OUT_JSON = REPO / "web_application/frontend/src/data/peaceImprovedStationAssignment.json"
CROSSWALK_MAX_M = 150.0
TRIBUTARY_RATIO_MAX = 0.35


def _log_da_err(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 12.0
    x, y = float(a), float(b)
    if not (np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0):
        return 12.0
    return abs(np.log(x) - np.log(y))


def _pct_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return None
    return abs(a - b) / abs(b) * 100.0


def _ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return None
    return float(a) / float(b)


def sanitize_for_json(obj):
    """JSON cannot encode NaN/Inf; use null for webpack-imported frontend data."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        x = float(obj)
        return None if not np.isfinite(x) else x
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if obj is None:
        return None
    if isinstance(obj, (str, bool, int)):
        return obj
    if pd.isna(obj):
        return None
    return obj


def pick_nhd_target_reach(
    nhd_5070: gpd.GeoDataFrame,
    gage_5070,
    usgs_da: float | None,
) -> tuple[pd.Series | None, str, str]:
    """Return (nhd_row, mode, rule)."""
    sp = nhd_5070.copy()
    sp["_dist"] = sp.geometry.distance(gage_5070)
    band = sp[sp["_dist"] <= GAGE_RADIUS_M]
    if band.empty:
        row = sp.nsmallest(1, "_dist").iloc[0]
        return row, "cumulative", "global_closest"

    tda = pd.to_numeric(band.get("TotDASqKm"), errors="coerce")
    max_tda = float(tda.max()) if tda.notna().any() else 0.0
    tributary = (
        usgs_da is not None
        and usgs_da > 0
        and max_tda > 0
        and float(usgs_da) / max_tda < TRIBUTARY_RATIO_MAX
    )

    if tributary:
        best = None
        best_key = None
        for _, row in band.iterrows():
            local = row.get("AreaSqKm")
            if local is None or not np.isfinite(float(local)) or float(local) <= 0:
                continue
            dist = float(row["_dist"])
            err = _log_da_err(float(local), usgs_da)
            so = int(float(row.get("StreamOrde", 0) or 0))
            key = (err, dist, -so)
            if best_key is None or key < best_key:
                best_key = key
                best = row
        if best is not None:
            return best, "tributary", "nhd_local_vs_usgs"
        row = band.sort_values("_dist").iloc[0]
        return row, "tributary", "distance_only"

    row, rule, _ = pick_nhd_reach(nhd_5070, gage_5070, usgs_da)
    return row, "cumulative", rule or "nhd_tda_vs_usgs"


def filter_candidates(band: pd.DataFrame) -> pd.DataFrame:
    if band.empty:
        return band
    good = band[band["snap_dist_m"] <= CROSSWALK_MAX_M]
    if len(good) >= 1:
        return good.copy()
    return band.copy()


def pick_improved_gis(
    band: pd.DataFrame,
    target_nhd_id: int | None,
    usgs_da: float | None,
    mode: str,
) -> tuple[int | None, str, float | None]:
    band = filter_candidates(band)
    if band.empty:
        return None, "no_candidates", None

    if target_nhd_id is not None and not pd.isna(target_nhd_id):
        nid = int(target_nhd_id)
        exact = band[band["nhdplusid_crosswalk"].astype("Int64") == nid]
        if not exact.empty:
            row = exact.sort_values("dist_m").iloc[0]
            return int(row["gis_id"]), "exact_nhd_crosswalk", float(row["dist_m"])

    target_tda = None
    if target_nhd_id is not None:
        sub = band[band["nhdplusid_crosswalk"].astype("Int64") == int(target_nhd_id)]
        if not sub.empty:
            target_tda = float(sub.iloc[0]["nhd_totdasqkm"])

    best_i = None
    best_key = None
    for i, row in band.iterrows():
        area = row.get("area_km2")
        nhd_tda = row.get("nhd_totdasqkm")
        nhd_local = row.get("nhd_local_areasqkm")
        dist = float(row["dist_m"])
        snap = float(row.get("snap_dist_m", 999))

        if mode == "tributary" and usgs_da and usgs_da > 0:
            if nhd_tda and float(nhd_tda) > 0 and float(area) > 3.0 * float(nhd_tda):
                continue
            ref_err = min(_log_da_err(nhd_local, usgs_da), _log_da_err(area, usgs_da))
        else:
            ref_err = _log_da_err(area, usgs_da) if usgs_da and usgs_da > 0 else 0.0

        nhd_err = _log_da_err(area, nhd_tda if nhd_tda is not None else target_tda)
        so_raw = row.get("stream_order", 0)
        so = int(float(so_raw)) if so_raw is not None and pd.notna(so_raw) else 0
        key = (ref_err + 1.2 * nhd_err, dist / GAGE_RADIUS_M, snap / SNAP_M, -so)
        if best_key is None or key < best_key:
            best_key = key
            best_i = i

    if best_i is None:
        row = band.sort_values("dist_m").iloc[0]
        return int(row["gis_id"]), "distance_fallback", float(row["dist_m"])

    row = band.loc[best_i]
    return int(row["gis_id"]), f"composite_{mode}", float(row["dist_m"])


def candidates_for_gage(channels_5070: gpd.GeoDataFrame, gage_5070) -> pd.DataFrame:
    sp = channels_5070.copy()
    sp["dist_m"] = sp.geometry.distance(gage_5070)
    band = sp[sp["dist_m"] <= GAGE_RADIUS_M].copy()
    if band.empty:
        band = sp.nsmallest(1, "dist_m").copy()
    return band.sort_values("dist_m")


def main() -> None:
    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    chandeg = parse_chandeg_gis_points(TXTINOUT)
    area_by_gis = chandeg.set_index("gis_id")["area_km2"].to_dict()

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")

    print("Loading NHD flowlines...")
    nhd = load_nhd_flowlines_domain(huc12s)
    nhd_5070 = nhd.to_crs(ALBERS)
    if "StreamOrde" not in nhd_5070.columns:
        nhd_5070["StreamOrde"] = 0
    nhd_tda = nhd_5070.set_index("NHDPlusID")["TotDASqKm"].astype(float).to_dict()
    nhd_local = nhd_5070.set_index("NHDPlusID")["AreaSqKm"].astype(float).to_dict()
    nhd_order = nhd_5070.set_index("NHDPlusID")["StreamOrde"].astype(float).to_dict()

    print("Crosswalk chandeg → NHD...")
    xw = snap_gis_to_nhd_orig(chandeg, nhd_5070)
    if "NHDPlusID" in xw.columns:
        xw = xw.rename(columns={"NHDPlusID": "nhdplusid_crosswalk"})
    xw["nhdplusid_crosswalk"] = pd.to_numeric(xw["nhdplusid_crosswalk"], errors="coerce")
    xw["nhd_totdasqkm"] = xw["nhdplusid_crosswalk"].map(nhd_tda)
    xw["nhd_local_areasqkm"] = xw["nhdplusid_crosswalk"].map(nhd_local)
    xw["stream_order"] = xw["nhdplusid_crosswalk"].map(nhd_order)

    channels_5070 = gpd.GeoDataFrame(
        xw[
            [
                "gis_id",
                "area_km2",
                "nhdplusid_crosswalk",
                "nhd_totdasqkm",
                "nhd_local_areasqkm",
                "snap_dist_m",
                "stream_order",
                "lon",
                "lat",
            ]
        ],
        geometry=gpd.points_from_xy(xw["lon"], xw["lat"]),
        crs="EPSG:4326",
    ).to_crs(ALBERS)

    rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        current = int(st["channel"]) if pd.notna(st["channel"]) else None
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        usgs_da, usgs_src = load_usgs_da_km2(site)

        band = candidates_for_gage(channels_5070, gage_5070)
        nhd_row, mode, nhd_rule = pick_nhd_target_reach(nhd_5070, gage_5070, usgs_da)
        target_id = int(nhd_row["NHDPlusID"]) if nhd_row is not None and pd.notna(nhd_row.get("NHDPlusID")) else None
        target_tda = float(nhd_row["TotDASqKm"]) if nhd_row is not None and pd.notna(nhd_row.get("TotDASqKm")) else None

        improved, imp_rule, imp_dist = pick_improved_gis(band, target_id, usgs_da, mode)

        cur_area = area_by_gis.get(current) if current is not None else None
        imp_area = area_by_gis.get(improved) if improved is not None else None

        cur_nhd_tda = (
            float(channels_5070.loc[channels_5070["gis_id"] == current, "nhd_totdasqkm"].iloc[0])
            if current is not None and (channels_5070["gis_id"] == current).any()
            else None
        )
        imp_nhd_tda = (
            float(channels_5070.loc[channels_5070["gis_id"] == improved, "nhd_totdasqkm"].iloc[0])
            if improved is not None and (channels_5070["gis_id"] == improved).any()
            else None
        )

        rows.append(
            {
                "usgs_site_no": site,
                "n_candidates_500m": len(band),
                "gage_mode": mode,
                "nhd_target_rule": nhd_rule,
                "target_nhdplusid": target_id,
                "target_nhd_totdasqkm": target_tda,
                "usgs_da_km2": usgs_da,
                "usgs_da_source": usgs_src,
                "current_gis_channel": current,
                "current_chandeg_km2": cur_area,
                "current_nhd_totdasqkm": cur_nhd_tda,
                "current_pct_vs_nhd_tda": _pct_diff(cur_area, cur_nhd_tda),
                "current_ratio_swat_nhd": _ratio(cur_area, cur_nhd_tda),
                "current_log_err_usgs": _log_da_err(cur_area, usgs_da) if usgs_da else None,
                "improved_gis_channel": improved,
                "improved_chandeg_km2": imp_area,
                "improved_nhd_totdasqkm": imp_nhd_tda,
                "improved_pct_vs_nhd_tda": _pct_diff(imp_area, imp_nhd_tda),
                "improved_ratio_swat_nhd": _ratio(imp_area, imp_nhd_tda),
                "improved_log_err_usgs": _log_da_err(imp_area, usgs_da) if usgs_da else None,
                "improved_pick_rule": imp_rule,
                "improved_dist_m": imp_dist,
                "channel_changed": (
                    current is not None and improved is not None and int(current) != int(improved)
                ),
            }
        )

    df = pd.DataFrame(rows)
    changed = df[df["channel_changed"]]
    has_nhd = df["current_pct_vs_nhd_tda"].notna() & df["improved_pct_vs_nhd_tda"].notna()

    def med(col: str) -> float | None:
        s = df[col].dropna()
        return float(s.median()) if len(s) else None

    improved_nhd = df.loc[has_nhd, "improved_pct_vs_nhd_tda"] < df.loc[has_nhd, "current_pct_vs_nhd_tda"]
    n_improved_nhd = int(improved_nhd.sum()) if len(improved_nhd) else 0

    tributary_changed = changed[changed["gage_mode"] == "tributary"]
    within = lambda col: int(
        ((df[col] >= 0.5) & (df[col] <= 2.0)).sum()
    )

    summary = {
        "nStations": int(len(df)),
        "nChannelChanged": int(len(changed)),
        "nImprovedVsNhdTda": n_improved_nhd,
        "nWorsenedVsNhdTda": int(has_nhd.sum() - n_improved_nhd) if has_nhd.any() else 0,
        "medianCurrentPctVsNhd": med("current_pct_vs_nhd_tda"),
        "medianImprovedPctVsNhd": med("improved_pct_vs_nhd_tda"),
        "medianCurrentLogErrUsgs": med("current_log_err_usgs"),
        "medianImprovedLogErrUsgs": med("improved_log_err_usgs"),
        "nCurrentWithinHalfToDoubleNhd": within("current_ratio_swat_nhd"),
        "nImprovedWithinHalfToDoubleNhd": within("improved_ratio_swat_nhd"),
        "nTributaryMode": int((df["gage_mode"] == "tributary").sum()),
        "nTributaryChannelChanged": int(len(tributary_changed)),
    }

    df.to_csv(OUT_CSV, index=False)

    stations_records = df.replace({np.nan: None}).to_dict(orient="records")

    payload = sanitize_for_json(
        {
        "methodId": "swatgenx_v2",
        "methodTitle": "SWATGenX v2 assignment (Peace pilot)",
        "searchRadiusM": GAGE_RADIUS_M,
        "description": (
            "Dual-scale NHD target reach (tributary: local AreaSqKm vs USGS; cumulative: TotDASqKm vs USGS), "
            "then GIS channel by crosswalk NHD ID or composite score (SWAT area vs NHD TDA + USGS + distance + stream order). "
            "Excludes crosswalk snaps >150 m when better candidates exist. Proposal only — does not update stations.shp."
        ),
        "productionMethod": (
            "Within 500 m, match rivs1 AreaC to USGS in log-space (da_distance), else LSU fallback."
        ),
        "improvements": [
            "Separates tributary gages from mainstem cumulative drainage before picking a target reach.",
            "Anchors GIS channel to the target NHDPlusID via crosswalk when possible.",
            "Penalizes SWAT channels whose cumulative area is inconsistent with crosswalk NHD TotDASqKm.",
            "Filters unreliable chandeg→NHD snaps (>150 m) when alternatives exist.",
        ],
        "summary": summary,
        "stations": stations_records,
        }
    )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md_lines = [
        "# Peace improved station assignment (swatgenx_v2)",
        "",
        payload["description"],
        "",
        "## Summary vs production assignment",
        "",
        f"| Metric | Current (production) | Improved (v2) |",
        f"|---|---:|---:|",
        f"| Stations | {summary['nStations']} | {summary['nStations']} |",
        f"| Channel changed | — | **{summary['nChannelChanged']}** |",
        f"| Median \\|Δ\\| vs NHD TDA | {summary['medianCurrentPctVsNhd']:.1f}% | {summary['medianImprovedPctVsNhd']:.1f}% |"
        if summary["medianCurrentPctVsNhd"] is not None
        else "| Median \\|Δ\\| vs NHD TDA | — | — |",
        f"| Improved \\|Δ\\| vs NHD (count) | — | **{summary['nImprovedVsNhdTda']}** |",
        f"| Median log-error vs USGS | {summary['medianCurrentLogErrUsgs']:.2f} | {summary['medianImprovedLogErrUsgs']:.2f} |"
        if summary["medianCurrentLogErrUsgs"] is not None
        else "",
        f"| Within 0.5–2.0× SWAT/NHD | {summary['nCurrentWithinHalfToDoubleNhd']} | {summary['nImprovedWithinHalfToDoubleNhd']} |",
        f"| Tributary-mode gages | {summary['nTributaryMode']} | ({summary['nTributaryChannelChanged']} channel changes) |",
        "",
        "## What improved",
        "",
        "- **Tributary / small-basin gages** (USGS DA ≪ mainstem TDA in band): v2 picks local-scale NHD + matching channel — fixes gross mismatches like **02294760**.",
        "- **SWAT/NHD ratio band**: more stations land in 0.5–2.0× (64 → 73); median \\|Δ\\| vs NHD TDA is **unchanged** (~10%) because mainstem QSWAT offset dominates.",
        "- **Does not remove** mainstem ~15–17% QSWAT vs NHD offset on correctly assigned mainstem channels.",
        "",
        f"Detail: `{OUT_CSV.name}`",
    ]
    (OUT_DIR / "peace-improved-station-assignment.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_JSON}")
    print("Summary:", summary)


if __name__ == "__main__":
    main()

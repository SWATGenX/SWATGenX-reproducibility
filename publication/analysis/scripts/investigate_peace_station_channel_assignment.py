#!/usr/bin/env python3
"""Peace HUC-8: evaluate streamflow gage → SWAT+ channel assignment vs alternatives.

Hypothesis: some assignments pick the wrong reach (mainstem vs tributary), inflating
|SWAT+ − NHD| beyond the QSWAT/TauDEM definition offset. Peace-only — no portfolio rerun.

Uses chandeg (lat, lon) channel points + 500 m search (production radius). Does not require
rivs1.shp on disk (replays logic on chandeg areas as AreaC proxy).
"""
from __future__ import annotations

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
    parse_chandeg,
    pick_nhd_reach,
)
from investigate_peace_drainage_area_upstream import (  # noqa: E402
    parse_chandeg_gis_points,
    snap_gis_to_nhd_orig,
)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

OUT_DIR = REPO / "publication/analysis/qa"
README_ASSIGN = Path(
    "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101/streamflow_data/README.md"
)


def _log_da_err(area_km2: float | None, target_km2: float | None) -> float:
    if area_km2 is None or target_km2 is None:
        return 12.0
    a, t = float(area_km2), float(target_km2)
    if not (np.isfinite(a) and np.isfinite(t) and a > 0 and t > 0):
        return 12.0
    return abs(np.log(a) - np.log(t))


def _pct_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return None
    return abs(a - b) / abs(b) * 100.0


def parse_readme_assignment() -> dict[str, dict]:
    if not README_ASSIGN.is_file():
        return {}
    out: dict[str, dict] = {}
    for line in README_ASSIGN.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or "site_no" in line or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 8:
            continue
        site = parts[0].zfill(8)
        try:
            out[site] = {
                "usgs_da_km2": float(parts[1]) if parts[1] else None,
                "usgs_da_source": parts[2],
                "assigned_channel": int(float(parts[3])),
                "readme_areac_km2": float(parts[4]) if parts[4] else None,
                "readme_match_rule": parts[7],
            }
        except ValueError:
            continue
    return out


def pick_nhd_by_local_da(flowlines_5070: gpd.GeoDataFrame, gage_5070, usgs_da: float | None):
    """Within 500 m, match USGS to NHD local AreaSqKm (tributary-scale heuristic)."""
    sp = flowlines_5070.copy()
    sp["_dist"] = sp.geometry.distance(gage_5070)
    band = sp[sp["_dist"] <= GAGE_RADIUS_M]
    if band.empty:
        row = sp.nsmallest(1, "_dist").iloc[0]
        return row, "global_closest", float(row["_dist"])
    if usgs_da is None or usgs_da <= 0 or len(band) == 1:
        row = band.sort_values("_dist").iloc[0]
        return row, "distance_only", float(row["_dist"])
    best = None
    best_err = None
    for _, row in band.iterrows():
        local = row.get("AreaSqKm")
        if local is None or not np.isfinite(float(local)) or float(local) <= 0:
            continue
        err = _log_da_err(float(local), usgs_da)
        if best_err is None or err < best_err:
            best_err = err
            best = row
    if best is not None:
        return best, "local_da_distance", float(best["_dist"])
    row = band.sort_values("_dist").iloc[0]
    return row, "distance_only", float(row["_dist"])


def gis_for_nhd_id(nhd_id: int, xw: pd.DataFrame, candidates: pd.DataFrame) -> int | None:
    """Prefer assigned candidate whose crosswalk NHDPlusID matches target reach."""
    if nhd_id is None or pd.isna(nhd_id):
        return None
    nid = int(nhd_id)
    in_cand = candidates[candidates["nhdplusid_crosswalk"].astype("Int64") == nid]
    if in_cand.empty:
        return None
    idx = in_cand["dist_m"].idxmin()
    return int(candidates.loc[idx, "gis_id"])


def _assigned_matches_nhd_pick(
    assigned: int | None, nhd_gage_id: int | None, channels_5070: gpd.GeoDataFrame
) -> bool | None:
    if assigned is None or nhd_gage_id is None or not (channels_5070["gis_id"] == assigned).any():
        return None
    cross = channels_5070.loc[channels_5070["gis_id"] == assigned, "nhdplusid_crosswalk"].iloc[0]
    if cross is None or pd.isna(cross):
        return None
    return int(cross) == int(nhd_gage_id)


def candidates_for_gage(channels_5070: gpd.GeoDataFrame, gage_5070: gpd.GeoSeries) -> pd.DataFrame:
    sp = channels_5070.copy()
    sp["dist_m"] = sp.geometry.distance(gage_5070)
    band = sp[sp["dist_m"] <= GAGE_RADIUS_M].copy()
    if band.empty:
        band = sp.nsmallest(1, "dist_m").copy()
    return band.sort_values("dist_m")


def pick_from_candidates(
    band: pd.DataFrame,
    strategy: str,
    usgs_da: float | None,
    nhd_target_id: int | None,
) -> tuple[int | None, str]:
    if band.empty:
        return None, "no_candidates"
    if strategy == "distance_only":
        row = band.iloc[0]
        return int(row["gis_id"]), "distance_only"
    if strategy == "match_usgs_areac":
        best_i = None
        best_key = None
        for i, row in band.iterrows():
            key = (_log_da_err(row["area_km2"], usgs_da), float(row["dist_m"]))
            if best_key is None or key < best_key:
                best_key = key
                best_i = i
        return int(band.loc[best_i, "gis_id"]), "match_usgs_areac"
    if strategy == "min_areac_in_band":
        row = band.sort_values("area_km2").iloc[0]
        return int(row["gis_id"]), "min_areac_in_band"
    if strategy == "match_nhd_tda_at_crosswalk":
        best_i = None
        best_key = None
        for i, row in band.iterrows():
            tda = row.get("nhd_totdasqkm")
            key = (_log_da_err(row["area_km2"], tda), float(row["dist_m"]))
            if best_key is None or key < best_key:
                best_key = key
                best_i = i
        return int(band.loc[best_i, "gis_id"]), "match_nhd_tda_at_crosswalk"
    if strategy == "nhd_gage_pick_gis":
        gis = gis_for_nhd_id(nhd_target_id, band, band)
        if gis is not None:
            return gis, "nhd_gage_pick_gis"
        return int(band.iloc[0]["gis_id"]), "nhd_gage_pick_fallback_dist"
    if strategy == "nhd_local_pick_gis":
        gis = gis_for_nhd_id(nhd_target_id, band, band)
        if gis is not None:
            return gis, "nhd_local_pick_gis"
        return int(band.iloc[0]["gis_id"]), "nhd_local_pick_fallback_dist"
    return None, "unknown"


def main() -> None:
    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    chandeg = parse_chandeg_gis_points(TXTINOUT)
    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")

    print("Loading NHD flowlines (zip)...")
    nhd = load_nhd_flowlines_domain(huc12s)
    nhd_5070 = nhd.to_crs(ALBERS)
    nhd_tda = nhd_5070.set_index("NHDPlusID")["TotDASqKm"].astype(float).to_dict()
    nhd_local = nhd_5070.set_index("NHDPlusID")["AreaSqKm"].astype(float).to_dict()

    print("Crosswalk chandeg → NHD...")
    xw = snap_gis_to_nhd_orig(chandeg, nhd_5070)
    if "NHDPlusID" in xw.columns and "nhdplusid_crosswalk" not in xw.columns:
        xw = xw.rename(columns={"NHDPlusID": "nhdplusid_crosswalk"})
    xw["nhdplusid_crosswalk"] = pd.to_numeric(xw["nhdplusid_crosswalk"], errors="coerce")
    xw["nhd_totdasqkm"] = xw["nhdplusid_crosswalk"].map(nhd_tda)
    xw["nhd_local_areasqkm"] = xw["nhdplusid_crosswalk"].map(nhd_local)

    channels_5070 = gpd.GeoDataFrame(
        xw[
            [
                "gis_id",
                "area_km2",
                "nhdplusid_crosswalk",
                "nhd_totdasqkm",
                "nhd_local_areasqkm",
                "snap_dist_m",
                "lon",
                "lat",
            ]
        ],
        geometry=gpd.points_from_xy(xw["lon"], xw["lat"]),
        crs="EPSG:4326",
    ).to_crs(ALBERS)

    readme = parse_readme_assignment()
    strategies = [
        "assigned",
        "distance_only",
        "match_usgs_areac",
        "min_areac_in_band",
        "match_nhd_tda_at_crosswalk",
        "nhd_gage_pick_gis",
        "nhd_local_pick_gis",
    ]

    detail_rows = []
    summary_counts: dict[str, dict] = {s: {"n_change": 0, "n_eval": 0, "pct_diffs": []} for s in strategies if s != "assigned"}

    for _, st in stations.iterrows():
        site = st["site_no"]
        assigned = int(st["channel"]) if pd.notna(st["channel"]) else None
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        usgs_da, usgs_src = load_usgs_da_km2(site)
        rd = readme.get(site, {})

        band = candidates_for_gage(channels_5070, gage_5070)
        n_cand = len(band)

        nhd_row, nhd_rule, _ = pick_nhd_reach(nhd_5070, gage_5070, usgs_da)
        nhd_gage_id = int(nhd_row["NHDPlusID"]) if nhd_row is not None and pd.notna(nhd_row.get("NHDPlusID")) else None
        nhd_gage_tda = float(nhd_row["TotDASqKm"]) if nhd_row is not None else None

        nhd_loc_row, nhd_loc_rule, _ = pick_nhd_by_local_da(nhd_5070, gage_5070, usgs_da)
        nhd_loc_id = int(nhd_loc_row["NHDPlusID"]) if nhd_loc_row is not None else None
        nhd_loc_local = float(nhd_loc_row["AreaSqKm"]) if nhd_loc_row is not None else None

        picks: dict[str, tuple[int | None, str]] = {"assigned": (assigned, rd.get("readme_match_rule", "assigned"))}
        picks["distance_only"] = pick_from_candidates(band, "distance_only", usgs_da, None)
        picks["match_usgs_areac"] = pick_from_candidates(band, "match_usgs_areac", usgs_da, None)
        picks["min_areac_in_band"] = pick_from_candidates(band, "min_areac_in_band", usgs_da, None)
        picks["match_nhd_tda_at_crosswalk"] = pick_from_candidates(band, "match_nhd_tda_at_crosswalk", usgs_da, None)
        picks["nhd_gage_pick_gis"] = pick_from_candidates(band, "nhd_gage_pick_gis", usgs_da, nhd_gage_id)
        picks["nhd_local_pick_gis"] = pick_from_candidates(band, "nhd_local_pick_gis", usgs_da, nhd_loc_id)

        area_by_gis = channels_5070.set_index("gis_id")["area_km2"].to_dict()
        nhd_tda_by_gis = channels_5070.set_index("gis_id")["nhd_totdasqkm"].to_dict()

        assigned_area = area_by_gis.get(assigned) if assigned is not None else None
        assigned_nhd = nhd_tda_by_gis.get(assigned) if assigned is not None else None
        pct_assigned = _pct_diff(assigned_area, assigned_nhd if assigned_nhd else nhd_gage_tda)

        row_out = {
            "usgs_site_no": site,
            "n_candidates_500m": n_cand,
            "assigned_gis_channel": assigned,
            "assigned_chandeg_km2": assigned_area,
            "assigned_nhd_totdasqkm": assigned_nhd,
            "pct_assigned_vs_nhd_tda": pct_assigned,
            "usgs_da_km2": usgs_da,
            "usgs_da_source": usgs_src,
            "nhd_gage_pick_id": nhd_gage_id,
            "nhd_gage_pick_totdasqkm": nhd_gage_tda,
            "nhd_gage_pick_rule": nhd_rule,
            "nhd_local_pick_id": nhd_loc_id,
            "nhd_local_pick_areasqkm": nhd_loc_local,
            "nhd_local_pick_rule": nhd_loc_rule,
            "readme_match_rule": rd.get("readme_match_rule"),
            "assigned_eq_nhd_gage_pick": _assigned_matches_nhd_pick(
                assigned, nhd_gage_id, channels_5070
            ),
        }

        for strat in strategies:
            if strat == "assigned":
                continue
            gis, rule = picks[strat]
            area = area_by_gis.get(gis) if gis is not None else None
            nhd_t = nhd_tda_by_gis.get(gis) if gis is not None else None
            ref_nhd = nhd_t if nhd_t is not None else nhd_gage_tda
            pct = _pct_diff(area, ref_nhd)
            row_out[f"{strat}_gis"] = gis
            row_out[f"{strat}_km2"] = area
            row_out[f"{strat}_pct_vs_nhd"] = pct
            row_out[f"{strat}_rule"] = rule
            if gis is not None and assigned is not None:
                if int(gis) != int(assigned):
                    summary_counts[strat]["n_change"] += 1
            if pct is not None:
                summary_counts[strat]["pct_diffs"].append(pct)
            summary_counts[strat]["n_eval"] += 1

        best_strat = None
        best_pct = pct_assigned
        for strat in strategies:
            if strat == "assigned":
                continue
            p = row_out.get(f"{strat}_pct_vs_nhd")
            if p is not None and (best_pct is None or p < best_pct - 5.0):
                best_pct = p
                best_strat = strat
        row_out["best_alternate_strategy"] = best_strat
        row_out["best_alternate_pct_vs_nhd"] = best_pct if best_strat else None

        detail_rows.append(row_out)

    df = pd.DataFrame(detail_rows)
    out_csv = OUT_DIR / "peace-station-channel-assignment-evaluation.csv"
    df.to_csv(out_csv, index=False)

    def med_pct(vals: list[float]) -> float | None:
        if not vals:
            return None
        return float(np.median(vals))

    lines = [
        "# Peace station → channel assignment evaluation",
        "",
        f"Stations: {len(df)} · Search radius: {GAGE_RADIUS_M:.0f} m (EPSG:5070) · "
        "Candidates: chandeg channel points with crosswalk NHD `TotDASqKm`.",
        "",
        "**Scope:** Peace HUC-8 only. Does **not** change `stations.shp` or rerun streamflow export.",
        "",
        "## Strategy summary (vs NHD `TotDASqKm` at crosswalk reach)",
        "",
        "| Strategy | Would change channel | Median |Δ| vs NHD | Notes |",
        "|---|---:|---:|---|",
    ]
    assigned_median = med_pct(df["pct_assigned_vs_nhd_tda"].dropna().tolist())
    lines.append(
        f"| **assigned (current)** | — | {assigned_median:.1f}% | Production README match (rivs1 AreaC at build) |"
        if assigned_median is not None
        else "| **assigned (current)** | — | — | |"
    )
    notes = {
        "distance_only": "Closest chandeg point in band",
        "match_usgs_areac": "Mirrors production: log-match chandeg area to USGS NWIS DA",
        "min_areac_in_band": "Smallest chandeg area in band (tributary heuristic)",
        "match_nhd_tda_at_crosswalk": "Min log |chandeg − NHD TDA| at crosswalk reach",
        "nhd_gage_pick_gis": "NHD gage-pick reach (TotDASqKm vs USGS) → GIS with same crosswalk NHD ID",
        "nhd_local_pick_gis": "NHD pick by local `AreaSqKm` vs USGS → matching GIS",
    }
    for strat, sc in summary_counts.items():
        med = med_pct(sc["pct_diffs"])
        med_s = f"{med:.1f}%" if med is not None else "—"
        lines.append(f"| {strat} | {sc['n_change']} | {med_s} | {notes.get(strat, '')} |")

    improved = df[df["best_alternate_strategy"].notna()]
    lines.extend(
        [
            "",
            f"## Stations where an alternate beats current by >5% |Δ| vs NHD ({len(improved)})",
            "",
        ]
    )
    if len(improved):
        lines.append("| Site | Assigned | |Δ| assign | Best alt | Alt |Δ| | USGS km² |")
        lines.append("|---|---:|---:|---|---:|---:|")
        for _, r in improved.sort_values("pct_assigned_vs_nhd_tda", ascending=False).head(20).iterrows():
            lines.append(
                f"| {r['usgs_site_no']} | {r['assigned_gis_channel']} | "
                f"{r['pct_assigned_vs_nhd_tda']:.1f}% | {r['best_alternate_strategy']} | "
                f"{r['best_alternate_pct_vs_nhd']:.1f}% | {r.get('usgs_da_km2', '—')} |"
            )
    else:
        lines.append("_None in this run._")

    lines.extend(
        [
            "",
            "## Interpretation hooks",
            "",
            "- If **match_usgs_areac** ≈ assigned but both disagree with NHD, assignment is consistent with "
            "production rules; remaining gap is likely QSWAT/TauDEM vs NHD VAA (phase 3), not wrong channel id.",
            "- If **nhd_local_pick_gis** or **min_areac_in_band** greatly improves |Δ| vs NHD for tributary gages, "
            "production `da_distance` on **cumulative** AreaC may be selecting mainstem channels inside 500 m.",
            "- Changing assignment requires re-running `fetch_streamflow_for_watershed` and recalibration — "
            "**Peace proof first**, then portfolio decision.",
            "",
            f"Detail: `{out_csv.name}`",
        ]
    )
    out_md = OUT_DIR / "peace-station-channel-assignment-evaluation.md"
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_md}")
    print(df[["usgs_site_no", "assigned_gis_channel", "pct_assigned_vs_nhd_tda", "best_alternate_strategy"]].head(15).to_string())


if __name__ == "__main__":
    main()

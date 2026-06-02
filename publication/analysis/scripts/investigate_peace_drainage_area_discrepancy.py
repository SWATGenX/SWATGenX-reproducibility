#!/usr/bin/env python3
"""Peace HUC-8: diagnose SWAT+ chandeg vs NHD TotDASqKm gaps (orphan merge vs lakes vs assignment).

Outputs under publication/analysis/qa/ — not wired to the public audit page.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.strtree import STRtree

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    HUC8,
    MODEL_BASE,
    SCENARIO,
    STATIONS_SHP,
    TXTINOUT,
    VPUID,
    load_nhd_flowlines_domain,
    load_station_names,
    load_usgs_da_km2,
    parse_chandeg,
    parse_rout_unit_areas,
    pick_nhd_reach,
    upstream_chandeg_ids,
)
from run_nhd_preprocessing_qa_benchmark import (  # noqa: E402
    _assign_catchments_to_huc12,
    _normalize_huc12,
    _normalize_nhdplus_id,
    _original_nhd_vpuid,
    _pick_vaa_columns,
    _simulate_preprocess_drops,
    resolve_domain_huc12s,
)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

OUT_DIR = REPO / "publication/analysis/qa"
VPU_PKL = Path(SWATGenXPaths.NHDPlus_VPUID_path) / VPUID


def _pct_diff(swat: float | None, nhd: float | None, ratio: float | None) -> float | None:
    if swat is not None and nhd is not None and nhd > 0:
        return abs(swat - nhd) / nhd * 100.0
    if ratio is not None and np.isfinite(ratio):
        return abs(ratio - 1.0) * 100.0
    return None


def _bucket(pct: float | None) -> str:
    if pct is None:
        return "missing"
    if pct <= 10:
        return "0-10%"
    if pct <= 20:
        return "10-20%"
    if pct <= 40:
        return "20-40%"
    if pct <= 100:
        return "40-100%"
    return ">100%"


def _orphan_area_by_target_catchment(
    catch_in_domain: gpd.GeoDataFrame,
    retained_nhd_ids: set[int],
) -> dict[int, float]:
    """Approximate km² of orphan catchment polygons dissolved into each retained catchment."""
    catch = catch_in_domain.copy()
    if "AreaSqKm" not in catch.columns:
        for col in ("areasqkm", "AreaSqKM", "Shape_Area"):
            if col in catch.columns:
                catch["AreaSqKm"] = pd.to_numeric(catch[col], errors="coerce")
                break
    if "AreaSqKm" not in catch.columns:
        catch_5070 = catch.to_crs(ALBERS)
        catch["AreaSqKm"] = catch_5070.geometry.area / 1e6

    retained = catch[catch["NHDPlusID"].isin(retained_nhd_ids)].copy()
    orphans = catch[~catch["NHDPlusID"].isin(retained_nhd_ids)].copy()
    if orphans.empty or retained.empty:
        return {}

    retained = retained.reset_index(drop=True)
    ret_geoms = retained.geometry.values
    tree = STRtree(ret_geoms)
    ret_ids = retained["NHDPlusID"].astype("int64").values
    acc: dict[int, float] = {}
    for _, row in orphans.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        pos = tree.nearest(geom)
        if pos is None:
            continue
        target = int(ret_ids[pos])
        acc[target] = acc.get(target, 0.0) + float(row["AreaSqKm"])
    return acc


def _waterbody_km2_in_catchment(
    catch_id: int,
    catch_polys: gpd.GeoDataFrame,
    waterbodies: gpd.GeoDataFrame,
) -> tuple[float, int]:
    poly = catch_polys.loc[catch_polys["NHDPlusID"] == catch_id, "geometry"]
    if poly.empty:
        return 0.0, 0
    geom = poly.iloc[0]
    wb = waterbodies
    if "AreaSqKm" not in wb.columns:
        wb = wb.copy()
        wb["AreaSqKm"] = pd.to_numeric(wb.get("AreaSqKM", wb.get("areasqkm")), errors="coerce")
    wb_pts = wb.copy()
    wb_pts["geometry"] = wb_pts.geometry.representative_point()
    hits = wb_pts[wb_pts.intersects(geom)]
    if hits.empty:
        return 0.0, 0
    key = "Permanent_Identifier" if "Permanent_Identifier" in hits.columns else "NHDPlusID"
    n = int(hits.drop_duplicates(subset=key).shape[0])
    area = float(pd.to_numeric(hits["AreaSqKm"], errors="coerce").fillna(0).sum())
    return area, n


def _diagnostic_hint(row: pd.Series) -> str:
    pct = row.get("pct_diff_nhd")
    if pd.isna(pct):
        return "missing_swat_or_nhd"
    swat = row.get("swat_km2")
    nhd = row.get("nhd_tda_km2")
    rtu = row.get("rout_unit_upstream_km2")
    orphan = row.get("orphan_merged_into_catchment_km2") or 0
    wb = row.get("waterbody_in_catchment_km2") or 0
    usgs = row.get("usgs_da_km2")
    name = str(row.get("station_name") or "").upper()

    if swat is not None and nhd is not None and swat < 0.25 * nhd:
        return "likely_tributary_or_wrong_reach_assignment"
    if usgs is not None and nhd is not None and usgs > 0 and nhd > 2.5 * usgs and swat is not None and swat < 0.5 * usgs:
        return "nhd_mainstem_vs_tributary_gage"
    if rtu is not None and swat is not None and rtu > 0 and swat > 0 and abs(rtu - swat) / swat < 0.05 and pct > 15:
        return "chandeg_vs_nhd_not_rout_unit_mismatch"
    if orphan > 5 and swat is not None and nhd is not None and swat > nhd:
        return "possible_orphan_merge_inflating_swat_catchment"
    if wb > 1 and swat is not None and nhd is not None and swat < nhd:
        return "possible_lake_waterbody_in_nhd_not_in_swat_channel_area"
    if "LAKE" in name or "RESERVOIR" in name or "POND" in name:
        return "lake_named_station_review_channel_link"
    if 10 <= pct <= 40:
        return "moderate_gap_review_orphan_lake_and_reach_pick"
    if pct <= 10:
        return "good_agreement"
    return "large_gap_review_assignment"


def main() -> None:
    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    h12_domain = {h.zfill(12) for h in huc12s}

    chandeg = parse_chandeg(TXTINOUT)
    gis_to_area = chandeg.set_index("gis_id")["area_km2"].to_dict()
    gis_to_lcha = chandeg.set_index("gis_id")["lcha"].to_dict()
    rtu_ha_by_ch = parse_rout_unit_areas(TXTINOUT)

    upstream_adj: dict[int, list[int]] = {}
    for _, row in chandeg.iterrows():
        cid = int(row["chandeg_id"])
        if str(row.get("obj_typ", "")).lower() == "sdc":
            downstream = int(float(row["obj_id"]))
            upstream_adj.setdefault(downstream, []).append(cid)

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")
    names = load_station_names()

    print("Loading original NHD domain layers…")
    nhd_flows = load_nhd_flowlines_domain(huc12s)
    nhd_5070 = nhd_flows.to_crs(ALBERS)

    with _original_nhd_vpuid(VPUID) as layers:
        catchment = _normalize_nhdplus_id(
            gpd.GeoDataFrame(layers["NHDPlusCatchment"], geometry="geometry")
        )
        if catchment.crs is None:
            catchment = catchment.set_crs("EPSG:4326", allow_override=True)
        wbd = _normalize_huc12(gpd.GeoDataFrame(layers["WBDHU12"], geometry="geometry"))
        catch_in_domain = _assign_catchments_to_huc12(catchment, wbd, h12_domain)
        domain_catch_ids = set(catch_in_domain["NHDPlusID"].dropna().astype("int64"))

        flowline = _normalize_nhdplus_id(layers["NHDFlowline"].copy())
        vaa_full = _pick_vaa_columns(layers["NHDPlusFlowlineVAA"])
        vaa_cols = [
            "NHDPlusID",
            "TotDASqKm",
            "AreaSqKm",
            "LengthKM",
            "StreamOrde",
            "Divergence",
            "HydroSeq",
            "DnHydroSeq",
            "UpHydroSeq",
        ]
        vaa_cols = [c for c in vaa_cols if c in vaa_full.columns]
        fl_cols = ["NHDPlusID", "FType", "Permanent_Identifier"]
        fl_cols = [c for c in fl_cols if c in flowline.columns]
        merged = flowline[fl_cols].merge(vaa_full[vaa_cols], on="NHDPlusID", how="inner")
        flows_in = merged[merged["NHDPlusID"].isin(domain_catch_ids)].copy()
        drops = _simulate_preprocess_drops(flows_in, domain_catch_ids)
        s = flows_in.loc[flows_in["Divergence"] != 2].copy()
        if "Permanent_Identifier" in s.columns:
            s = s.loc[~s["Permanent_Identifier"].astype(str).str.startswith("C")]
        s = s[s["NHDPlusID"].isin(domain_catch_ids)]
        hydroseq_set = set(s["HydroSeq"].astype("int64"))
        s = s.copy()
        s["DnHydroSeq"] = s["DnHydroSeq"].where(s["DnHydroSeq"].isin(hydroseq_set), 0)
        s["UpHydroSeq"] = s["UpHydroSeq"].where(s["UpHydroSeq"].isin(hydroseq_set), 0)
        s = s.loc[~((s["UpHydroSeq"] == 0) & (s["DnHydroSeq"] == 0))]
        retained_ids = set(s["NHDPlusID"].astype("int64"))
        orphan_by_target = _orphan_area_by_target_catchment(catch_in_domain, retained_ids)
        ftype_by_nhd = flowline.set_index("NHDPlusID")["FType"].to_dict() if "FType" in flowline.columns else {}
        waterbodies = gpd.GeoDataFrame(layers["NHDWaterbody"], geometry="geometry", crs=catchment.crs)

    streams_post = pd.read_pickle(VPU_PKL / "streams.pkl")
    streams_post["NHDPlusID"] = streams_post["NHDPlusID"].astype("int64")
    post_by_nhd = streams_post.set_index("NHDPlusID", drop=False)

    rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        gis_ch = int(st["channel"]) if pd.notna(st["channel"]) else None
        swat_km2 = float(gis_to_area[gis_ch]) if gis_ch in gis_to_area else None
        lcha = int(gis_to_lcha[gis_ch]) if gis_ch in gis_to_lcha else None
        chandeg_id = None
        if gis_ch is not None:
            hit = chandeg.loc[chandeg["gis_id"] == gis_ch]
            if len(hit):
                chandeg_id = int(hit.iloc[0]["chandeg_id"])

        rtu_km2 = None
        if chandeg_id is not None:
            up_ids = upstream_chandeg_ids(chandeg_id, upstream_adj)
            rtu_km2 = sum(rtu_ha_by_ch.get(cid, 0.0) for cid in up_ids) / 100.0

        usgs_da, _ = load_usgs_da_km2(site)
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        nhd_row, nhd_rule, nhd_dist = pick_nhd_reach(nhd_5070, gage_5070, usgs_da)
        nhd_id = int(nhd_row["NHDPlusID"]) if nhd_row is not None else None
        nhd_tda = float(nhd_row["TotDASqKm"]) if nhd_row is not None and pd.notna(nhd_row.get("TotDASqKm")) else None
        nhd_local = float(nhd_row["AreaSqKm"]) if nhd_row is not None and pd.notna(nhd_row.get("AreaSqKm")) else None
        ftype = None
        if nhd_id is not None and nhd_id in ftype_by_nhd:
            fv = ftype_by_nhd[nhd_id]
            if pd.notna(fv):
                ftype = int(fv)

        ratio = (swat_km2 / nhd_tda) if swat_km2 and nhd_tda else None
        pct = _pct_diff(swat_km2, nhd_tda, ratio)

        orphan_km2 = float(orphan_by_target.get(nhd_id, 0.0)) if nhd_id else 0.0
        wb_km2, wb_n = _waterbody_km2_in_catchment(nhd_id, catch_in_domain, waterbodies) if nhd_id else (0.0, 0)

        post_row = post_by_nhd.loc[nhd_id] if nhd_id in post_by_nhd.index else None
        post_tda = float(post_row["TotDASqKm"]) if post_row is not None and pd.notna(post_row.get("TotDASqKm")) else None
        wb_link = (
            str(post_row["WBArea_Permanent_Identifier"])
            if post_row is not None and pd.notna(post_row.get("WBArea_Permanent_Identifier"))
            else ""
        )

        swat_minus_nhd = (swat_km2 - nhd_tda) if swat_km2 is not None and nhd_tda is not None else None
        nhd_tda_minus_local = (nhd_tda - nhd_local) if nhd_tda is not None and nhd_local is not None else None

        rows.append(
            {
                "usgs_site_no": site,
                "station_name": names.get(site, ""),
                "gis_channel": gis_ch,
                "swat_lcha": lcha,
                "gis_eq_lcha": gis_ch == lcha if gis_ch is not None and lcha is not None else None,
                "chandeg_id": chandeg_id,
                "swat_km2": round(swat_km2, 2) if swat_km2 is not None else None,
                "rout_unit_upstream_km2": round(rtu_km2, 2) if rtu_km2 is not None else None,
                "nhd_nhdplusid": nhd_id,
                "nhd_totdasqkm_km2": round(nhd_tda, 2) if nhd_tda is not None else None,
                "nhd_local_areasqkm_km2": round(nhd_local, 2) if nhd_local is not None else None,
                "nhd_postprocess_totdasqkm_km2": round(post_tda, 2) if post_tda is not None else None,
                "nhd_ftype": ftype,
                "nhd_pick_rule": nhd_rule,
                "nhd_pick_dist_m": round(nhd_dist, 1) if nhd_dist is not None else None,
                "usgs_da_km2": round(usgs_da, 2) if usgs_da is not None else None,
                "ratio_swat_nhd": round(ratio, 4) if ratio else None,
                "pct_diff_nhd": round(pct, 2) if pct is not None else None,
                "diff_bucket": _bucket(pct),
                "swat_minus_nhd_km2": round(swat_minus_nhd, 2) if swat_minus_nhd is not None else None,
                "nhd_upstream_of_local_km2": round(nhd_tda_minus_local, 2) if nhd_tda_minus_local is not None else None,
                "orphan_merged_into_catchment_km2": round(orphan_km2, 2),
                "waterbody_in_catchment_km2": round(wb_km2, 2),
                "waterbody_count_in_catchment": wb_n,
                "nhd_wbarea_link_on_reach": wb_link[:32] if wb_link else "",
                "preprocess_orphan_catchments_domain": drops["orphan_catchments_merged"],
                "preprocess_no_vaa_catchments": drops.get("divergence2_catchments_merged", 0),
            }
        )

    df = pd.DataFrame(rows)
    df["diagnostic_hint"] = df.apply(_diagnostic_hint, axis=1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUT_DIR / "peace-drainage-area-investigation.csv"
    df.to_csv(out_csv, index=False)

    # Summary markdown
    matched = df.dropna(subset=["swat_km2", "nhd_totdasqkm_km2"]).copy()
    bucket_counts = matched["diff_bucket"].value_counts().sort_index()
    mod = matched[matched["diff_bucket"].isin(["20-40%", "10-20%"])]

    lines = [
        "# Peace River (`03100101`) — drainage-area discrepancy investigation",
        "",
        "Internal QA only (not on the public audit page). Compares SWAT+ `chandeg.con` area to "
        "original NHDPlus HR `TotDASqKm` at the gage-picked reach, with diagnostics for **orphan catchment "
        "merge** and **NHD waterbodies**.",
        "",
        f"**{len(matched)}** gages with both SWAT+ and NHD · domain preprocess (simulated): "
        f"**{drops['orphan_catchments_merged']}** orphan catchments merged nationally in HUC12 domain, "
        f"**{drops['isolated_reaches_removed']}** isolated reaches removed.",
        "",
        "## Percent-difference buckets (|SWAT+ − NHD| / NHD × 100)",
        "",
        "| Bucket | Count |",
        "|---|---:|",
    ]
    for bkt, cnt in bucket_counts.items():
        lines.append(f"| {bkt} | {cnt} |")

    lines.extend(
        [
            "",
            "## 10–40% band — dominant diagnostic hints",
            "",
            "| Hint | Count |",
            "|---|---:|",
        ]
    )
    hint_counts = mod["diagnostic_hint"].value_counts()
    for hint, cnt in hint_counts.items():
        lines.append(f"| {hint} | {cnt} |")

    lines.extend(
        [
            "",
            "## Hypothesis notes",
            "",
            "1. **Orphan catchments:** Preprocessing dissolves catchments without a retained flowline into the "
            "nearest networked catchment (`orphan_merged_into_catchment_km2`). SWAT+ `chandeg.con` reflects "
            "TauDEM/QSWAT+ delineation after that merge; NHD `TotDASqKm` is the **original** VAA cumulative "
            "drainage and does not gain orphan polygon area the same way. Large positive SWAT−NHD with "
            "high `orphan_merged_into_catchment_km2` supports this path.",
            "",
            "2. **Lakes / waterbodies:** NHD assigns `TotDASqKm` along the flow network; lake and reservoir "
            "features appear as `NHDWaterbody` polygons and as `WBArea_Permanent_Identifier` on flowlines. "
            "SWAT+ routes many lakes as separate `res` objects — channel `chandeg` area may exclude open-water "
            "area that NHD still counts toward cumulative drainage at a pick reach. Stations with "
            "`waterbody_in_catchment_km2` > 0 and SWAT < NHD are candidates; **lake-named gages** need "
            "channel-assignment review even when NHD pick is close.",
            "",
            "3. **Gage–reach assignment (not conversion error):** When `nhd_totdasqkm` ≫ `usgs_da` but "
            "`swat_km2` ≪ both, the gage is likely on a tributary while NHD pick is mainstem (`nhd_pick_rule`).",
            "",
            "`rout_unit_upstream_km2` is **not** equivalent to `chandeg.con` area — do not use it alone as SWAT drainage.",
            "",
            "## Largest 20–40% gaps",
            "",
            "| Site | SWAT+ | NHD | % diff | Orphan→catch km² | WB in catch km² | Hint |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    focus = mod.nlargest(15, "pct_diff_nhd")
    for _, r in focus.iterrows():
        lines.append(
            f"| {r['usgs_site_no']} | {r['swat_km2']} | {r['nhd_totdasqkm_km2']} | {r['pct_diff_nhd']}% | "
            f"{r['orphan_merged_into_catchment_km2']} | {r['waterbody_in_catchment_km2']} | {r['diagnostic_hint']} |"
        )

    md_path = OUT_DIR / "peace-drainage-area-investigation.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {md_path}")
    print("\nBucket counts:")
    print(bucket_counts.to_string())
    print("\n20–40% hint counts:")
    print(hint_counts.to_string())


if __name__ == "__main__":
    main()

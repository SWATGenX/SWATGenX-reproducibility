#!/usr/bin/env python3
"""Peace HUC-8 phase 2: GIS→NHDPlusID crosswalk, upstream catchment & waterbody totals, multi-metric compare.

Order of analysis (per user):
  1. Exact GIS channel (chandeg gis_id) → NHDPlusID crosswalk
  2. Upstream cumulative catchment polygon area (not local-only)
  3. Upstream NHD waterbody area
  4. SWAT+ chandeg vs NHD local AreaSqKm, TotDASqKm, upstream catchment sums
     (original HR network vs SWATGenX-cleaned streams.pkl network)

Internal QA only — not published on the marketing audit page.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    HUC8,
    STATIONS_SHP,
    TXTINOUT,
    VPUID,
    load_nhd_flowlines_domain,
    load_station_names,
    load_usgs_da_km2,
    parse_chandeg,
    pick_nhd_reach,
)
from run_nhd_preprocessing_qa_benchmark import (  # noqa: E402
    _assign_catchments_to_huc12,
    _normalize_huc12,
    _normalize_nhdplus_id,
    _original_nhd_vpuid,
    _pick_vaa_columns,
    _simulate_preprocess_drops,
)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

OUT_DIR = REPO / "publication/analysis/qa"
VPU_PKL = Path(SWATGenXPaths.NHDPlus_VPUID_path) / VPUID
SNAP_M = 150.0


def _pct_diff(swat: float | None, ref: float | None) -> float | None:
    if swat is None or ref is None or not (np.isfinite(swat) and np.isfinite(ref)) or ref <= 0:
        return None
    return abs(swat - ref) / ref * 100.0


def _ratio(swat: float | None, ref: float | None) -> float | None:
    if swat is None or ref is None or not (np.isfinite(swat) and np.isfinite(ref)) or ref <= 0:
        return None
    return swat / ref


def parse_chandeg_gis_points(txtinout: Path) -> pd.DataFrame:
    path = txtinout / "chandeg.con"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headers = lines[1].split()
    rows = []
    for line in lines[2:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < len(headers):
            continue
        row = dict(zip(headers, parts[: len(headers)]))
        rows.append(row)
    df = pd.DataFrame(rows)
    df["chandeg_id"] = pd.to_numeric(df["id"], errors="coerce")
    df["gis_id"] = pd.to_numeric(df["gis_id"], errors="coerce")
    df["lcha"] = pd.to_numeric(df["lcha"], errors="coerce")
    df["area_km2"] = pd.to_numeric(df["area"], errors="coerce") / 100.0
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df


def snap_gis_to_nhd_orig(
    gis_df: pd.DataFrame,
    nhd_5070: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """Snap each chandeg (lat,lon) to nearest original-domain NHD flowline → crosswalk NHDPlusID."""
    pts = gpd.GeoDataFrame(
        gis_df,
        geometry=gpd.points_from_xy(gis_df["lon"], gis_df["lat"]),
        crs="EPSG:4326",
    ).to_crs(ALBERS)
    nhd = nhd_5070.copy()
    joined = gpd.sjoin_nearest(pts, nhd[["NHDPlusID", "geometry"]], how="left", max_distance=SNAP_M, distance_col="snap_dist_m")
    joined = joined.drop(columns=["index_right"], errors="ignore")
    return joined


def build_upstream_by_dn(flows: pd.DataFrame) -> dict[int, list[int]]:
    by_dn: dict[int, list[int]] = {}
    for _, r in flows.iterrows():
        hs = int(r["HydroSeq"])
        dn = int(r["DnHydroSeq"]) if pd.notna(r["DnHydroSeq"]) and int(r["DnHydroSeq"]) != 0 else 0
        if dn:
            by_dn.setdefault(dn, []).append(hs)
    return by_dn


def upstream_hydroseq_set(start_hs: int, by_dn: dict[int, list[int]], *, include_self: bool) -> set[int]:
    seen: set[int] = set()
    stack = [start_hs]
    while stack:
        h = stack.pop()
        if h in seen:
            continue
        seen.add(h)
        for up in by_dn.get(h, []):
            if up not in seen:
                stack.append(up)
    if not include_self:
        seen.discard(start_hs)
    return seen


def sum_upstream_metrics(
    start_nhd: int,
    flows: pd.DataFrame,
    wb_by_perm: dict[str, float],
    by_dn: dict[int, list[int]],
) -> dict[str, float]:
    row = flows.loc[flows["NHDPlusID"] == start_nhd]
    if row.empty:
        return {
            "n_upstream_reaches": 0,
            "upstream_catchment_area_km2": 0.0,
            "upstream_waterbody_km2": 0.0,
            "local_areasqkm_km2": 0.0,
            "totdasqkm_km2": 0.0,
        }
    r0 = row.iloc[0]
    hs = int(r0["HydroSeq"])
    up_hs = upstream_hydroseq_set(hs, by_dn, include_self=True)
    sub = flows[flows["HydroSeq"].isin(up_hs)]
    # Cumulative land catchment: sum VAA AreaSqKm (one catchment per reach), not polygon file.
    catch_sum = float(pd.to_numeric(sub["AreaSqKm"], errors="coerce").fillna(0).sum())
    wb_sum = 0.0
    seen_wb: set[str] = set()
    for perm in sub["WBArea_Permanent_Identifier"].dropna().astype(str):
        if not perm or perm in seen_wb:
            continue
        seen_wb.add(perm)
        wb_sum += wb_by_perm.get(perm, 0.0)
    local_a = float(r0["AreaSqKm"]) if pd.notna(r0.get("AreaSqKm")) else 0.0
    tda = float(r0["TotDASqKm"]) if pd.notna(r0.get("TotDASqKm")) else 0.0
    return {
        "n_upstream_reaches": int(len(up_hs)),
        "upstream_catchment_area_km2": round(catch_sum, 2),
        "upstream_waterbody_km2": round(wb_sum, 2),
        "local_areasqkm_km2": round(local_a, 2),
        "totdasqkm_km2": round(tda, 2),
    }


def main() -> None:
    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    h12_domain = {h.zfill(12) for h in huc12s}

    print("Loading chandeg GIS points…")
    chandeg_gis = parse_chandeg_gis_points(TXTINOUT)
    chandeg = parse_chandeg(TXTINOUT)

    print("Loading original NHD HR flowlines (domain-clipped)…")
    nhd_orig = load_nhd_flowlines_domain(huc12s)
    nhd_orig_5070 = nhd_orig.to_crs(ALBERS)

    print("Snapping gis_id → NHDPlusID (original flowlines)…")
    cross = snap_gis_to_nhd_orig(chandeg_gis, nhd_orig_5070)
    crosswalk = cross[
        [
            "gis_id",
            "chandeg_id",
            "lcha",
            "area_km2",
            "lat",
            "lon",
            "NHDPlusID",
            "snap_dist_m",
        ]
    ].copy()
    crosswalk["NHDPlusID"] = pd.to_numeric(crosswalk["NHDPlusID"], errors="coerce").astype("Int64")
    crosswalk = crosswalk.rename(
        columns={
            "area_km2": "swat_chandeg_km2",
            "NHDPlusID": "nhdplusid_crosswalk",
            "snap_dist_m": "crosswalk_snap_dist_m",
        }
    )
    xw_path = OUT_DIR / "peace-drainage-area-gis-nhd-crosswalk.csv"
    crosswalk.to_csv(xw_path, index=False)
    print(f"Wrote {xw_path} ({len(crosswalk)} channels)")

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
        vaa = _pick_vaa_columns(layers["NHDPlusFlowlineVAA"])
        vaa_cols = [
            "NHDPlusID",
            "TotDASqKm",
            "AreaSqKm",
            "HydroSeq",
            "DnHydroSeq",
            "UpHydroSeq",
            "Divergence",
        ]
        vaa_cols = [c for c in vaa_cols if c in vaa.columns]
        fl_cols = ["NHDPlusID", "FType", "Permanent_Identifier", "WBArea_Permanent_Identifier"]
        fl_cols = [c for c in fl_cols if c in flowline.columns]
        flows_orig = flowline[fl_cols].merge(vaa[vaa_cols], on="NHDPlusID", how="inner")
        flows_orig = flows_orig[flows_orig["NHDPlusID"].isin(domain_catch_ids)].copy()
        for c in ("TotDASqKm", "AreaSqKm"):
            flows_orig[c] = pd.to_numeric(flows_orig[c], errors="coerce")
        flows_orig["HydroSeq"] = pd.to_numeric(flows_orig["HydroSeq"], errors="coerce").astype("int64")
        flows_orig["DnHydroSeq"] = pd.to_numeric(flows_orig["DnHydroSeq"], errors="coerce").fillna(0).astype("int64")
        flows_orig["NHDPlusID"] = flows_orig["NHDPlusID"].astype("int64")

        wb_gdf = gpd.GeoDataFrame(layers["NHDWaterbody"], geometry="geometry", crs=catchment.crs)
        if "AreaSqKm" not in wb_gdf.columns:
            wb_gdf["AreaSqKm"] = pd.to_numeric(wb_gdf.get("AreaSqKM"), errors="coerce")
        perm_col = "Permanent_Identifier" if "Permanent_Identifier" in wb_gdf.columns else None
        wb_by_perm: dict[str, float] = {}
        if perm_col:
            for _, wr in wb_gdf.dropna(subset=[perm_col]).iterrows():
                wb_by_perm[str(wr[perm_col])] = float(wr["AreaSqKm"]) if pd.notna(wr["AreaSqKm"]) else 0.0

    by_dn_orig = build_upstream_by_dn(flows_orig)

    print("Loading SWATGenX-cleaned streams.pkl (HUC-8 subset)…")
    streams_clean = pd.read_pickle(VPU_PKL / "streams.pkl")
    streams_clean = streams_clean[streams_clean["huc8"].astype(str).str.zfill(8) == HUC8.zfill(8)].copy()
    streams_clean["NHDPlusID"] = streams_clean["NHDPlusID"].astype("int64")
    streams_clean["HydroSeq"] = pd.to_numeric(streams_clean["HydroSeq"], errors="coerce").astype("int64")
    streams_clean["DnHydroSeq"] = pd.to_numeric(streams_clean["DnHydroSeq"], errors="coerce").fillna(0).astype("int64")
    for c in ("TotDASqKm", "AreaSqKm"):
        streams_clean[c] = pd.to_numeric(streams_clean[c], errors="coerce")
    by_dn_clean = build_upstream_by_dn(streams_clean)

    xw_by_gis = crosswalk.set_index("gis_id")

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")
    names = load_station_names()

    rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        gis_ch = int(st["channel"]) if pd.notna(st["channel"]) else None
        swat_km2 = None
        nhd_xw = None
        snap_m = None
        if gis_ch is not None and gis_ch in xw_by_gis.index:
            xw = xw_by_gis.loc[gis_ch]
            if isinstance(xw, pd.DataFrame):
                xw = xw.iloc[0]
            swat_km2 = float(xw["swat_chandeg_km2"]) if pd.notna(xw["swat_chandeg_km2"]) else None
            nhd_xw = int(xw["nhdplusid_crosswalk"]) if pd.notna(xw["nhdplusid_crosswalk"]) else None
            snap_m = float(xw["crosswalk_snap_dist_m"]) if pd.notna(xw["crosswalk_snap_dist_m"]) else None

        usgs_da, _ = load_usgs_da_km2(site)
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        nhd_row, nhd_rule, nhd_dist = pick_nhd_reach(nhd_orig_5070, gage_5070, usgs_da)
        nhd_gage = int(nhd_row["NHDPlusID"]) if nhd_row is not None else None
        crosswalk_matches_gage_pick = nhd_xw == nhd_gage if nhd_xw and nhd_gage else None

        orig_m = sum_upstream_metrics(nhd_xw, flows_orig, wb_by_perm, by_dn_orig) if nhd_xw else {}
        clean_m = sum_upstream_metrics(nhd_xw, streams_clean, wb_by_perm, by_dn_clean) if nhd_xw else {}

        row = {
            "usgs_site_no": site,
            "station_name": names.get(site, ""),
            "gis_channel": gis_ch,
            "nhdplusid_crosswalk": nhd_xw,
            "crosswalk_snap_dist_m": round(snap_m, 1) if snap_m is not None else None,
            "nhdplusid_gage_pick_500m": nhd_gage,
            "crosswalk_eq_gage_pick": crosswalk_matches_gage_pick,
            "nhd_gage_pick_rule": nhd_rule,
            "swat_chandeg_km2": round(swat_km2, 2) if swat_km2 is not None else None,
            "nhd_local_areasqkm_km2": orig_m.get("local_areasqkm_km2"),
            "nhd_totdasqkm_km2": orig_m.get("totdasqkm_km2"),
            "nhd_orig_upstream_catchment_sum_km2": orig_m.get("upstream_catchment_area_km2"),
            "nhd_clean_upstream_catchment_sum_km2": clean_m.get("upstream_catchment_area_km2"),
            "nhd_orig_upstream_waterbody_km2": orig_m.get("upstream_waterbody_km2"),
            "nhd_orig_upstream_n_reaches": orig_m.get("n_upstream_reaches"),
            "nhd_clean_upstream_n_reaches": clean_m.get("n_upstream_reaches"),
            "usgs_da_km2": round(usgs_da, 2) if usgs_da is not None else None,
        }
        for ref_key, ref_col in [
            ("local", "nhd_local_areasqkm_km2"),
            ("tda", "nhd_totdasqkm_km2"),
            ("orig_up", "nhd_orig_upstream_catchment_sum_km2"),
            ("clean_up", "nhd_clean_upstream_catchment_sum_km2"),
        ]:
            ref = row.get(ref_col)
            pdiff = _pct_diff(swat_km2, ref)
            row[f"pct_diff_vs_{ref_key}"] = round(pdiff, 2) if pdiff is not None else None
            rat = _ratio(swat_km2, ref)
            row[f"ratio_swat_vs_{ref_key}"] = round(rat, 4) if rat is not None else None
        rows.append(row)

    df = pd.DataFrame(rows)
    out_csv = OUT_DIR / "peace-drainage-area-investigation-v2.csv"
    df.to_csv(out_csv, index=False)

    matched = df.dropna(subset=["swat_chandeg_km2", "nhd_totdasqkm_km2"])
    mainstem = matched[(matched["pct_diff_vs_tda"] >= 10) & (matched["pct_diff_vs_tda"] <= 20) & (matched["nhd_totdasqkm_km2"] > 500)]

    def med(col: str) -> float | None:
        s = matched[col].dropna()
        return float(s.median()) if len(s) else None

    lines = [
        "# Peace drainage-area investigation (phase 2)",
        "",
        "Internal QA. Uses **chandeg (lat,lon) → nearest original NHD flowline** as the GIS-channel crosswalk "
        f"(≤{SNAP_M:.0f} m), then **upstream** cumulative catchment `AreaSqKm` and linked waterbody area.",
        "",
        f"- Crosswalk: `{xw_path.name}` ({len(crosswalk)} channels)",
        f"- Station metrics: `{out_csv.name}`",
        "",
        "## Crosswalk vs gage-pick",
        "",
        f"- Channels snapped (≤{SNAP_M:.0f} m): **{len(crosswalk)}** / {len(chandeg_gis)} chandeg rows",
        f"- Stations where crosswalk NHDPlusID **equals** 500 m gage-pick reach: "
        f"**{int(df['crosswalk_eq_gage_pick'].sum())}** / {int(df['crosswalk_eq_gage_pick'].notna().sum())}",
        "",
        "Peace HUC-8 has no `Watershed/Shapes/rivs1.shp` on disk; crosswalk is **chandeg lat/lon → original NHD HR "
        "flowline** (not QSWAT `LINKNO`). Where shapes exist on other models, prefer `rivs1.Channel` = `gis_id` joined "
        "to `SWAT_plus_streams.NHDPlusID`.",
        "",
        "## Median |SWAT+ − ref| / ref × 100 (matched gages)",
        "",
        "| NHD reference | Median % diff |",
        "|---|---:|",
        f"| Local `AreaSqKm` (reach) | {med('pct_diff_vs_local')}% |",
        f"| Cumulative `TotDASqKm` | {med('pct_diff_vs_tda')}% |",
        f"| Upstream Σ AreaSqKm (original HR network) | {med('pct_diff_vs_orig_up')}% |",
        f"| Upstream Σ AreaSqKm (cleaned streams.pkl) | {med('pct_diff_vs_clean_up')}% |",
        "",
        "## Mainstem 10–20% vs `TotDASqKm` band",
        "",
        "| Site | SWAT+ | TotDASqKm | % vs TDA | % vs orig upstream | % vs clean upstream | WB upstream km² |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in mainstem.sort_values("pct_diff_vs_tda", ascending=False).iterrows():
        lines.append(
            f"| {r['usgs_site_no']} | {r['swat_chandeg_km2']} | {r['nhd_totdasqkm_km2']} | {r['pct_diff_vs_tda']}% | "
            f"{r.get('pct_diff_vs_orig_up', '—')}% | {r.get('pct_diff_vs_clean_up', '—')}% | "
            f"{r.get('nhd_orig_upstream_waterbody_km2', '—')} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation guide",
            "",
            "- If **% vs orig upstream** ≪ **% vs TotDASqKm**, the gap is mostly **NHD VAA cumulative definition**, not SWAT orphan merge.",
            "- If **% vs clean upstream** < **% vs orig upstream**, preprocessing drops changed network extent.",
            "- If **% vs local** is huge but **% vs TotDASqKm** is ~15%, SWAT `chandeg` is **cumulative** (like TDA), not local reach `AreaSqKm`.",
            "- **`nhd_orig_upstream_waterbody_km2`** tests lake hypothesis along upstream WB-linked reaches.",
        ]
    )
    md_path = OUT_DIR / "peace-drainage-area-investigation-v2.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {md_path}")
    print(f"Crosswalk equals gage pick: {int(df['crosswalk_eq_gage_pick'].sum())}/{df['crosswalk_eq_gage_pick'].notna().sum()}")
    print("Median pct diff vs local / tda / orig_up / clean_up:", med("pct_diff_vs_local"), med("pct_diff_vs_tda"), med("pct_diff_vs_orig_up"), med("pct_diff_vs_clean_up"))


if __name__ == "__main__":
    main()

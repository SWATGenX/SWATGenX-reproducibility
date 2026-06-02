#!/usr/bin/env python3
"""Phase 0: Peace HUC-8 station assignment inventory for NHD-first / SWAT-second method design.

Does not change production assignment. Produces:
  - peace-station-assignment-phase0-artifacts.md   (data layers + paths)
  - peace-station-assignment-phase0-inventory.csv (per-station)
  - peace-station-assignment-phase0-method.md     (production NHD pick vs NHD-first draft)

Scientific principle: choose NHDPlus HR reference reach without SWAT AreaC/chandeg area,
then map to SWAT+ via crosswalk only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    CONUS_STATIONS_CSV,
    GAGE_RADIUS_M,
    HUC8,
    MODEL_BASE,
    STATIONS_SHP,
    TXTINOUT,
    USER_ROOT,
    VPUID,
    load_station_names,
    load_usgs_da_km2,
    pick_nhd_reach,
)
from investigate_peace_drainage_area_upstream import (  # noqa: E402
    SNAP_M,
    parse_chandeg_gis_points,
    snap_gis_to_nhd_orig,
)
from run_nhd_preprocessing_qa_benchmark import (  # noqa: E402
    _assign_catchments_to_huc12,
    _normalize_huc12,
    _normalize_nhdplus_id,
    _original_nhd_vpuid,
    _pick_vaa_columns,
)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

OUT_DIR = REPO / "publication/analysis/qa"
OUT_CSV = OUT_DIR / "peace-station-assignment-phase0-inventory.csv"
OUT_ARTIFACTS = OUT_DIR / "peace-station-assignment-phase0-artifacts.md"
OUT_METHOD = OUT_DIR / "peace-station-assignment-phase0-method.md"
MODEL = "SWAT_MODEL_Web_Application"
TRIBUTARY_RATIO = 0.35


def _log_err(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 12.0
    x, y = float(a), float(b)
    if not (np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0):
        return 12.0
    return abs(np.log(x) - np.log(y))


def tokenize_station_name(name: str | None) -> dict[str, bool]:
    u = (name or "").upper()
    return {
        "peace_river": "PEACE RIVER" in u or " PEACE R" in u,
        "tributary": any(t in u for t in (" BRANCH", " CREEK", " CR ", " BROOK", " RUN")),
        "lake_outlet": "OUTLET" in u or ("BELOW" in u and "LAKE" in u),
        "lake": " LAKE " in f" {u} " or "RESERVOIR" in u,
        "canal": "CANAL" in u or " DITCH" in u,
    }


def infer_gage_context(
    tokens: dict[str, bool],
    site_tp: str | None,
    usgs_da: float | None,
    max_tda_band: float,
) -> str:
    st = (site_tp or "").upper()
    if tokens["canal"] or st in ("CA", "CN"):
        return "canal"
    if tokens["lake_outlet"]:
        return "lake_outlet"
    if tokens["lake"] and not tokens["peace_river"]:
        return "lake_related"
    if usgs_da and max_tda_band > 0 and float(usgs_da) / max_tda_band < TRIBUTARY_RATIO:
        return "tributary"
    if tokens["tributary"] and not tokens["peace_river"]:
        return "tributary"
    if tokens["peace_river"]:
        return "mainstem"
    return "cumulative"


def load_nhd_enriched_domain(huc12s: list[str]) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, dict[str, float]]:
    h12_domain = {h.zfill(12) for h in huc12s}
    with _original_nhd_vpuid(VPUID) as layers:
        catchment = _normalize_nhdplus_id(
            gpd.GeoDataFrame(layers["NHDPlusCatchment"], geometry="geometry")
        )
        if catchment.crs is None:
            catchment = catchment.set_crs("EPSG:4326", allow_override=True)
        wbd = _normalize_huc12(gpd.GeoDataFrame(layers["WBDHU12"], geometry="geometry"))
        catch_in = _assign_catchments_to_huc12(catchment, wbd, h12_domain)
        domain_ids = set(catch_in["NHDPlusID"].dropna().astype("int64"))

        flowline = _normalize_nhdplus_id(layers["NHDFlowline"].copy())
        vaa = _pick_vaa_columns(layers["NHDPlusFlowlineVAA"])
        vaa_cols = [
            "NHDPlusID",
            "TotDASqKm",
            "AreaSqKm",
            "StreamOrde",
            "StreamLeve",
            "HydroSeq",
            "DnHydroSeq",
            "UpHydroSeq",
            "LevelPathI",
            "Divergence",
        ]
        vaa_cols = [c for c in vaa_cols if c in vaa.columns]
        fl_cols = ["NHDPlusID", "FType", "FCode", "GNIS_Name", "WBArea_Permanent_Identifier"]
        fl_cols = [c for c in fl_cols if c in flowline.columns]
        flows = flowline[fl_cols].merge(vaa[vaa_cols], on="NHDPlusID", how="inner")
        flows = flows[flows["NHDPlusID"].isin(domain_ids)].copy()
        for c in ("TotDASqKm", "AreaSqKm", "StreamOrde", "StreamLeve", "LevelPathI", "Divergence"):
            if c in flows.columns:
                flows[c] = pd.to_numeric(flows[c], errors="coerce")
        flows["HydroSeq"] = pd.to_numeric(flows["HydroSeq"], errors="coerce").astype("Int64")
        flows["DnHydroSeq"] = pd.to_numeric(flows["DnHydroSeq"], errors="coerce").fillna(0).astype("Int64")

        wb_gdf = gpd.GeoDataFrame(layers["NHDWaterbody"], geometry="geometry", crs=catchment.crs)
        wb_by_perm: dict[str, float] = {}
        perm_col = "Permanent_Identifier" if "Permanent_Identifier" in wb_gdf.columns else None
        if perm_col:
            for _, wr in wb_gdf.dropna(subset=[perm_col]).iterrows():
                a = wr.get("AreaSqKm", wr.get("AreaSqKM"))
                wb_by_perm[str(wr[perm_col])] = float(a) if pd.notna(a) else 0.0

    fl_geom = flowline[["NHDPlusID", "geometry"]].drop_duplicates("NHDPlusID")
    merged = flows.merge(fl_geom, on="NHDPlusID", how="left")
    gdf = gpd.GeoDataFrame(merged, geometry="geometry", crs=catchment.crs)
    return gdf, wb_gdf.to_crs(ALBERS), wb_by_perm


def gage_waterbody_context(gage_5070, wb_5070: gpd.GeoDataFrame) -> dict:
    if wb_5070.empty:
        return {"dist_to_lake_m": None, "inside_waterbody": False}
    wb_5070 = wb_5070.copy()
    wb_5070["dist_m"] = wb_5070.geometry.distance(gage_5070)
    nearest = wb_5070.nsmallest(1, "dist_m").iloc[0]
    dist = float(nearest["dist_m"])
    inside = bool((wb_5070.distance(gage_5070) < 1.0).any())
    return {"dist_to_lake_m": dist, "inside_waterbody": inside}


def pick_nhd_reference_nhd_first(
    flows_5070: gpd.GeoDataFrame,
    gage_5070,
    usgs_da: float | None,
    station_name: str | None,
    site_tp: str | None,
) -> tuple[pd.Series | None, str, str]:
    """NHD-only reference reach (no SWAT areas). Returns (row, rule, context)."""
    tokens = tokenize_station_name(station_name)
    sp = flows_5070.copy()
    sp["_dist"] = sp.geometry.distance(gage_5070)
    band = sp[sp["_dist"] <= GAGE_RADIUS_M].copy()
    if band.empty:
        row = sp.nsmallest(1, "_dist").iloc[0]
        ctx = infer_gage_context(tokens, site_tp, usgs_da, 0.0)
        return row, "global_closest", ctx

    tda = pd.to_numeric(band["TotDASqKm"], errors="coerce")
    max_tda = float(tda.max()) if tda.notna().any() else 0.0
    ctx = infer_gage_context(tokens, site_tp, usgs_da, max_tda)

    if ctx == "tributary":
        sub = band.copy()
        if usgs_da and usgs_da > 0:
            sub = sub[sub["TotDASqKm"].fillna(np.inf) <= max(3.0 * float(usgs_da), max_tda * 0.5)]
            if sub.empty:
                sub = band.copy()
        best = None
        best_key = None
        for _, row in sub.iterrows():
            local = row.get("AreaSqKm")
            so = int(float(row.get("StreamOrde") or 0))
            gnis = str(row.get("GNIS_Name") or "")
            gnis_bonus = 0.0
            if tokens["tributary"] and gnis:
                for frag in ("BRANCH", "CREEK", "CR.", "BROOK", "RUN"):
                    if frag in gnis.upper():
                        gnis_bonus = -0.15
                        break
            key = (
                _log_err(float(local) if pd.notna(local) else None, usgs_da) + gnis_bonus,
                float(row["_dist"]) / GAGE_RADIUS_M,
                so,
            )
            if best_key is None or key < best_key:
                best_key = key
                best = row
        if best is not None:
            return best, "nhd_first_tributary_local_gnis", ctx

    if ctx in ("mainstem", "cumulative"):
        sub = band.copy()
        so = pd.to_numeric(sub["StreamOrde"], errors="coerce")
        if so.notna().any():
            max_so = float(so.max())
            sub = sub[so >= max_so - 1]
        if "LevelPathI" in sub.columns and sub["LevelPathI"].notna().any():
            top = sub.loc[sub["StreamOrde"] == sub["StreamOrde"].max(), "LevelPathI"]
            lp = top.mode()
            if len(lp):
                sub_lp = sub[sub["LevelPathI"] == lp.iloc[0]]
                if len(sub_lp):
                    sub = sub_lp
        if tokens["peace_river"] and "GNIS_Name" in sub.columns:
            peace = sub[sub["GNIS_Name"].astype(str).str.contains("Peace", case=False, na=False)]
            if len(peace):
                sub = peace
        best = None
        best_key = None
        for _, row in sub.iterrows():
            tda_v = row.get("TotDASqKm")
            so_v = int(float(row.get("StreamOrde") or 0))
            key = (
                float(row["_dist"]) / GAGE_RADIUS_M,
                -so_v * 0.01,
                0.25 * _log_err(float(tda_v) if pd.notna(tda_v) else None, usgs_da),
            )
            if best_key is None or key < best_key:
                best_key = key
                best = row
        if best is not None:
            return best, "nhd_first_mainstem_levelpath_gnis", ctx

    if ctx == "lake_outlet":
        wb_col = "WBArea_Permanent_Identifier"
        if wb_col in band.columns:
            linked = band[band[wb_col].notna() & (band[wb_col].astype(str) != "")]
            if len(linked):
                row = linked.sort_values("_dist").iloc[0]
                return row, "nhd_first_lake_wb_link", ctx
        row = band.sort_values("_dist").iloc[0]
        return row, "nhd_first_lake_outlet_nearest", ctx

    if ctx == "canal":
        if "FType" in band.columns:
            canalish = band[pd.to_numeric(band["FType"], errors="coerce").isin([336, 428, 460])]
            if len(canalish):
                row = canalish.sort_values("_dist").iloc[0]
                return row, "nhd_first_canal_ftype", ctx

    row = band.sort_values("_dist").iloc[0]
    return row, "nhd_first_distance_fallback", ctx


def load_conus_meta() -> pd.DataFrame:
    if not CONUS_STATIONS_CSV.is_file():
        return pd.DataFrame()
    return pd.read_csv(CONUS_STATIONS_CSV, dtype={"site_no": str})


def inventory_artifacts(huc12s: list[str]) -> dict:
    shapes_huc8 = MODEL_BASE / "Watershed" / "Shapes"
    rivs1_huc8 = shapes_huc8 / "rivs1.shp"
    sqlite_huc8 = MODEL_BASE / f"{MODEL}.sqlite"
    huc12_with_rivs1 = []
    for h in huc12s:
        p = USER_ROOT / VPUID / "huc12" / h.zfill(12) / MODEL / "Watershed" / "Shapes" / "rivs1.shp"
        if p.is_file():
            huc12_with_rivs1.append(h.zfill(12))
    chandeg = TXTINOUT / "chandeg.con"
    gis_ids = set()
    if chandeg.is_file():
        df = parse_chandeg_gis_points(TXTINOUT)
        gis_ids = set(df["gis_id"].dropna().astype(int).tolist())
    return {
        "stations_shp": STATIONS_SHP.is_file(),
        "chandeg_con": chandeg.is_file(),
        "n_gis_channels_chandeg": len(gis_ids),
        "rivs1_huc8": rivs1_huc8.is_file(),
        "sqlite_huc8": sqlite_huc8.is_file(),
        "rivs1_huc12_count": len(huc12_with_rivs1),
        "rivs1_huc12_total": len(huc12s),
        "huc12_with_rivs1_sample": huc12_with_rivs1[:5],
    }


def gis_for_nhd(nhd_id: int | None, xw: pd.DataFrame) -> tuple[int | None, float | None]:
    if nhd_id is None or pd.isna(nhd_id):
        return None, None
    sub = xw[xw["nhdplusid_crosswalk"].astype("Int64") == int(nhd_id)]
    if sub.empty:
        return None, None
    row = sub.sort_values("snap_dist_m").iloc[0]
    return int(row["gis_id"]), float(row["snap_dist_m"])


def main() -> None:
    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    artifacts = inventory_artifacts(huc12s)
    names = load_station_names()
    conus = load_conus_meta()
    conus_idx = conus.set_index("site_no") if not conus.empty and "site_no" in conus.columns else None

    print("Loading enriched NHD HR (original zip)…")
    flows, wb, _ = load_nhd_enriched_domain(huc12s)
    flows_5070 = flows.to_crs(ALBERS)
    wb_5070 = wb

    chandeg = parse_chandeg_gis_points(TXTINOUT)
    xw = snap_gis_to_nhd_orig(chandeg, flows_5070)
    if "NHDPlusID" in xw.columns:
        xw = xw.rename(columns={"NHDPlusID": "nhdplusid_crosswalk"})
    xw["nhdplusid_crosswalk"] = pd.to_numeric(xw["nhdplusid_crosswalk"], errors="coerce")

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    prod_by_site = stations.set_index("site_no")["channel"].astype("Int64")

    nhd_cols = [c for c in flows.columns if c != "geometry"]
    rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        usgs_da, usgs_src = load_usgs_da_km2(site)
        nm = names.get(site, "")
        site_tp = None
        coord_acy = None
        if conus_idx is not None and site in conus_idx.index:
            cr = conus_idx.loc[site]
            if isinstance(cr, pd.DataFrame):
                cr = cr.iloc[0]
            site_tp = cr.get("site_tp_cd")
            coord_acy = cr.get("coord_acy_cd")

        wb_ctx = gage_waterbody_context(gage_5070, wb_5070)
        tokens = tokenize_station_name(nm)

        sp = flows_5070.copy()
        sp["_dist"] = sp.geometry.distance(gage_5070)
        band = sp[sp["_dist"] <= GAGE_RADIUS_M]
        n_band = len(band)

        prod_row, prod_rule, _ = pick_nhd_reach(flows_5070, gage_5070, usgs_da)
        first_row, first_rule, first_ctx = pick_nhd_reference_nhd_first(
            flows_5070, gage_5070, usgs_da, nm, str(site_tp) if site_tp is not None else None
        )

        prod_nid = int(prod_row["NHDPlusID"]) if prod_row is not None and pd.notna(prod_row.get("NHDPlusID")) else None
        first_nid = int(first_row["NHDPlusID"]) if first_row is not None and pd.notna(first_row.get("NHDPlusID")) else None

        prod_gis, prod_snap = gis_for_nhd(prod_nid, xw)
        first_gis, first_snap = gis_for_nhd(first_nid, xw)

        prod_ch = int(prod_by_site[site]) if site in prod_by_site.index and pd.notna(prod_by_site[site]) else None

        rows.append(
            {
                "usgs_site_no": site,
                "station_name": nm,
                "site_tp_cd": site_tp,
                "coord_acy_cd": coord_acy,
                "usgs_da_km2": usgs_da,
                "usgs_da_source": usgs_src,
                "name_peace_river": tokens["peace_river"],
                "name_tributary": tokens["tributary"],
                "name_lake_outlet": tokens["lake_outlet"],
                "name_lake": tokens["lake"],
                "name_canal": tokens["canal"],
                "dist_to_lake_m": wb_ctx["dist_to_lake_m"],
                "inside_waterbody": wb_ctx["inside_waterbody"],
                "n_nhd_candidates_500m": n_band,
                "production_gis_channel": prod_ch,
                "production_nhdplusid": prod_nid,
                "production_nhd_pick_rule": prod_rule,
                "production_gis_via_crosswalk": prod_gis,
                "production_crosswalk_snap_m": prod_snap,
                "nhd_first_context": first_ctx,
                "nhd_first_nhdplusid": first_nid,
                "nhd_first_pick_rule": first_rule,
                "nhd_first_gis_via_crosswalk": first_gis,
                "nhd_first_crosswalk_snap_m": first_snap,
                "nhd_production_vs_first_same_id": (
                    prod_nid is not None and first_nid is not None and prod_nid == first_nid
                ),
                "production_gis_vs_nhd_first_gis": (
                    prod_ch is not None and first_gis is not None and int(prod_ch) == int(first_gis)
                ),
                "nhd_first_totdasqkm": float(first_row["TotDASqKm"])
                if first_row is not None and pd.notna(first_row.get("TotDASqKm"))
                else None,
                "nhd_first_areasqkm": float(first_row["AreaSqKm"])
                if first_row is not None and pd.notna(first_row.get("AreaSqKm"))
                else None,
                "nhd_first_streamorde": int(float(first_row["StreamOrde"]))
                if first_row is not None and pd.notna(first_row.get("StreamOrde"))
                else None,
                "nhd_first_ftype": int(float(first_row["FType"]))
                if first_row is not None and "FType" in first_row and pd.notna(first_row.get("FType"))
                else None,
                "nhd_first_gnis": str(first_row.get("GNIS_Name") or "") if first_row is not None else "",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    n_same_nhd = int(df["nhd_production_vs_first_same_id"].sum())
    n_same_gis = int(df["production_gis_vs_nhd_first_gis"].sum())
    n_disagree_nhd = int((~df["nhd_production_vs_first_same_id"]).sum())
    n_first_no_gis = int(df["nhd_first_gis_via_crosswalk"].isna().sum())

    art_lines = [
        "# Peace station assignment — Phase 0 artifact inventory",
        "",
        f"**HUC-8:** `{HUC8}` · **Model base:** `{MODEL_BASE}`",
        "",
        "## SWAT / QSWAT artifacts",
        "",
        "| Artifact | Present |",
        "|----------|---------|",
        f"| `stations.shp` | {artifacts['stations_shp']} |",
        f"| `TxtInOut/chandeg.con` | {artifacts['chandeg_con']} ({artifacts['n_gis_channels_chandeg']} GIS ids) |",
        f"| HUC-8 `Watershed/Shapes/rivs1.shp` | {artifacts['rivs1_huc8']} |",
        f"| HUC-8 project SQLite | {artifacts['sqlite_huc8']} |",
        f"| HUC-12 `rivs1.shp` (under Peace) | {artifacts['rivs1_huc12_count']} / {artifacts['rivs1_huc12_total']} |",
        "",
        "**Implication:** Production assignment used `rivs1` + `AreaC` at build time; HUC-8 shapes are absent on disk. "
        "Phase 0 NHD-first mapping uses **chandeg→NHD crosswalk** only until HUC-8 `rivs1` is restored or merged from HUC-12 exports.",
        "",
        f"Sample HUC-12 with rivs1: `{', '.join(artifacts['huc12_with_rivs1_sample'])}` …",
        "",
        "## NWIS / station metadata",
        "",
        f"| Source | Path |",
        f"|--------|------|",
        f"| VPU meta (drainage area) | `{Path(SWATGenXPaths.streamflow_vpuid_path) / VPUID / f'meta_{VPUID}.csv'}` |",
        f"| CONUS site table | `{CONUS_STATIONS_CSV}` |",
        "",
        "CONUS columns used in Phase 0: `station_nm`, `site_tp_cd`, `coord_acy_cd`, `huc_cd`.",
        "",
        "## NHDPlus HR (original HU4 zip)",
        "",
        f"Enriched flowline fields loaded: `{', '.join(nhd_cols)}`.",
        "",
        "Available for NHD-first rules: `TotDASqKm`, `AreaSqKm`, `StreamOrde`, `LevelPathI`, `HydroSeq`, "
        "`Divergence`, `FType`, `GNIS_Name`, `WBArea_Permanent_Identifier`, gage distance to `NHDWaterbody`.",
        "",
        f"Detail per station: `{OUT_CSV.name}`",
    ]
    OUT_ARTIFACTS.write_text("\n".join(art_lines) + "\n", encoding="utf-8")

    method_lines = [
        "# Peace station assignment — Phase 0 method comparison",
        "",
        "## Recommended scientific method (NHD-first / SWAT-second)",
        "",
        "1. **Reference reach (NHD only)** — Choose NHDPlus HR reach using coordinates, NWIS DA, "
        "station name (weak prior), GNIS, `FType`/`FCode`, stream order, `LevelPathI`, `Divergence`, "
        "and lake/waterbody context. **Do not use** QSWAT `AreaC` or `chandeg.con` area in this step.",
        "2. **SWAT map** — Map `NHDPlusID` → `gis_id` via crosswalk; if reach absent from `chandeg.con`, "
        "apply documented replacement (downstream active channel, lake outlet path) or mark unavailable.",
        "3. **Drainage-area audit** — Only then compare NHD VAA, polygon sums, QSWAT `AreaC`, `chandeg`, and NWIS.",
        "",
        "This removes circularity: assignment no longer optimizes the same SWAT cumulative area being evaluated.",
        "",
        "## Phase 0 draft: `pick_nhd_reference_nhd_first`",
        "",
        "Implemented in `inventory_peace_station_assignment_phase0.py` (exploratory, not production).",
        "",
        "| Context | Rule sketch |",
        "|---------|-------------|",
        "| `tributary` | USGS DA ≪ band max TDA and/or name; match local `AreaSqKm` + GNIS branch tokens; exclude mainstem-scale TDA |",
        "| `mainstem` | Dominant `LevelPathI` + high `StreamOrde`; GNIS Peace River; distance before low-weight TDA tie-break |",
        "| `lake_outlet` | Prefer `WBArea_Permanent_Identifier` link, else nearest in band |",
        "| `canal` | Prefer canal `FType` (336/428/460) when name/context indicates |",
        "",
        "## Peace pilot comparison (production NHD pick vs NHD-first draft)",
        "",
        f"| Metric | Count (of {len(df)}) |",
        f"|--------|----------------:|",
        f"| Same NHDPlusID (prod `da_distance` vs NHD-first) | {n_same_nhd} |",
        f"| Different NHDPlusID | {n_disagree_nhd} |",
        f"| Production `stations.shp` channel = GIS from NHD-first crosswalk | {n_same_gis} |",
        f"| NHD-first target has no chandeg crosswalk within {SNAP_M:.0f} m | {n_first_no_gis} |",
        "",
        "**Interpretation:**",
        "",
        "- Disagreements are expected where production used **log TotDASqKm vs USGS** without level-path/GNIS constraints.",
        "- NHD-first should **not** be judged by improving median SWAT–NHD error alone; judge by whether the reference reach "
        "matches hydrologic position (mainstem vs tributary vs lake/canal).",
        "- Mainstem Peace gages with ~15–17% SWAT vs NHD offset should keep the **mainstem NHD-first** reach; "
        "the offset is reported in the audit step, not fixed by reassignment.",
        "",
        "## Stations where NHD-first ≠ production NHD (review list)",
        "",
    ]
    disagree = df[~df["nhd_production_vs_first_same_id"]].sort_values("usgs_site_no")
    for _, r in disagree.head(25).iterrows():
        method_lines.append(
            f"- **{r['usgs_site_no']}** {r['station_name'][:50]} — prod `{r['production_nhdplusid']}` "
            f"({r['production_nhd_pick_rule']}) → first `{r['nhd_first_nhdplusid']}` "
            f"({r['nhd_first_pick_rule']}, ctx={r['nhd_first_context']})"
        )
    if len(disagree) > 25:
        method_lines.append(f"- … and {len(disagree) - 25} more in `{OUT_CSV.name}`")

    method_lines.extend(
        [
            "",
            "## Next steps (before rewriting inventory)",
            "",
            "1. Manual review of disagreement list (especially lake/canal/tributary names).",
            "2. Restore or define HUC-8 `rivs1` ↔ `gis_id` mapping for SWAT-second step.",
            "3. Formalize SWAT-second replacement rules (dropped reach, lake object, no `chandeg`).",
            "4. Implement v3 classifier on top of fixed NHD reference + SWAT map (calibration eligibility).",
            "",
            f"CSV: `{OUT_CSV.name}`",
        ]
    )
    OUT_METHOD.write_text("\n".join(method_lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_ARTIFACTS}")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_METHOD}")
    print(
        f"Summary: same NHD {n_same_nhd}/{len(df)}, same GIS {n_same_gis}/{len(df)}, "
        f"NHD-first no crosswalk {n_first_no_gis}/{len(df)}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Peace phase 3: pipeline trace — where SWAT+ − NHD offset first appears (10-gage panel).

Stages:
  A  original NHD TotDASqKm (zip VAA)
  B  original upstream Σ AreaSqKm (zip flowlines)
  C  cleaned streams.pkl upstream Σ AreaSqKm
  D  SWATGenX post-processed polygon upstream Σ (watersheds.pkl, domain-clipped)
  D′ streams.pkl upstream Σ AreaSqKm on cleaned network (cross-check vs D)
  E  QSWAT AreaC at station assignment (streamflow_data/README.md; rivs1 era, not live shapes)
  F  TxtInOut chandeg.con

Internal QA only.
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
    HUC8,
    TXTINOUT,
    VPUID,
    load_usgs_da_km2,
    parse_chandeg,
)
from investigate_peace_drainage_area_upstream import (  # noqa: E402
    build_upstream_by_dn,
    upstream_hydroseq_set,
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
VPU_PKL = Path(SWATGenXPaths.NHDPlus_VPUID_path) / VPUID
PANEL = OUT_DIR / "peace-drainage-area-phase3-panel.csv"
V2 = OUT_DIR / "peace-drainage-area-investigation-v2.csv"
CROSSWALK = OUT_DIR / "peace-drainage-area-gis-nhd-crosswalk.csv"
README_ASSIGN = Path(
    "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101/streamflow_data/README.md"
)
REL_TOL = 0.08  # 8% relative match for fork classification


def _rel_close(a: float | None, b: float | None, tol: float = REL_TOL) -> bool:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return False
    return abs(a - b) / abs(b) <= tol


def _pct_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return None
    return abs(a - b) / abs(b) * 100.0


def load_domain_catchment_ids(h12_domain: set[str]) -> set[int]:
    with _original_nhd_vpuid(VPUID) as layers:
        catchment = _normalize_nhdplus_id(
            gpd.GeoDataFrame(layers["NHDPlusCatchment"], geometry="geometry")
        )
        if catchment.crs is None:
            catchment = catchment.set_crs("EPSG:4326", allow_override=True)
        wbd = _normalize_huc12(gpd.GeoDataFrame(layers["WBDHU12"], geometry="geometry"))
        catch_in = _assign_catchments_to_huc12(catchment, wbd, h12_domain)
    return set(catch_in["NHDPlusID"].dropna().astype("int64"))


def load_flows_orig_zip(domain_ids: set[int]) -> pd.DataFrame:
    with _original_nhd_vpuid(VPUID) as layers:
        flowline = _normalize_nhdplus_id(layers["NHDFlowline"].copy())
        vaa = _pick_vaa_columns(layers["NHDPlusFlowlineVAA"])
        cols = ["NHDPlusID", "TotDASqKm", "AreaSqKm", "HydroSeq", "DnHydroSeq", "UpHydroSeq", "Divergence"]
        cols = [c for c in cols if c in vaa.columns]
        merged = flowline[["NHDPlusID"]].merge(vaa[cols], on="NHDPlusID", how="inner")
        flows = merged[merged["NHDPlusID"].isin(domain_ids)].copy()
    flows["NHDPlusID"] = flows["NHDPlusID"].astype("int64")
    flows["HydroSeq"] = pd.to_numeric(flows["HydroSeq"], errors="coerce").astype("int64")
    flows["DnHydroSeq"] = pd.to_numeric(flows["DnHydroSeq"], errors="coerce").fillna(0).astype("int64")
    for c in ("TotDASqKm", "AreaSqKm"):
        flows[c] = pd.to_numeric(flows[c], errors="coerce")
    return flows


def load_streams_clean(domain_ids: set[int]) -> pd.DataFrame:
    s = pd.read_pickle(VPU_PKL / "streams.pkl")
    s = s[s["NHDPlusID"].astype("int64").isin(domain_ids)].copy()
    s["NHDPlusID"] = s["NHDPlusID"].astype("int64")
    s["HydroSeq"] = pd.to_numeric(s["HydroSeq"], errors="coerce").astype("int64")
    s["DnHydroSeq"] = pd.to_numeric(s["DnHydroSeq"], errors="coerce").fillna(0).astype("int64")
    for c in ("TotDASqKm", "AreaSqKm"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    return s


def load_watershed_polygon_area_km2(domain_ids: set[int]) -> dict[int, float]:
    w = pd.read_pickle(VPU_PKL / "watersheds.pkl")
    w = w[w["NHDPlusID"].astype("int64").isin(domain_ids)].copy()
    w5070 = w.to_crs(ALBERS)
    w["area_km2"] = w5070.geometry.area / 1e6
    return w.set_index("NHDPlusID")["area_km2"].astype(float).to_dict()


def upstream_area_km2(
    nhd_id: int,
    flows: pd.DataFrame,
    area_by_nhd: dict[int, float],
    by_dn: dict[int, list[int]],
) -> tuple[float, int]:
    row = flows.loc[flows["NHDPlusID"] == nhd_id]
    if row.empty:
        return float("nan"), 0
    hs = int(row.iloc[0]["HydroSeq"])
    up = upstream_hydroseq_set(hs, by_dn, include_self=True)
    sub = flows[flows["HydroSeq"].isin(up)]
    n_ids = sub["NHDPlusID"].astype(int).unique()
    total = sum(area_by_nhd.get(int(n), 0.0) for n in n_ids)
    return round(total, 2), int(len(up))


def parse_readme_assignment() -> dict[str, float]:
    """Historical swat_channel_area_km2 from streamflow README (rivs1 AreaC at assignment time)."""
    if not README_ASSIGN.is_file():
        return {}
    text = README_ASSIGN.read_text(encoding="utf-8")
    out: dict[str, float] = {}
    for line in text.splitlines():
        if not line.startswith("|") or "site_no" in line or "---" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) < 5:
            continue
        site = parts[0].zfill(8)
        try:
            area = float(parts[4])
        except ValueError:
            continue
        out[site] = area
    return out


def classify_fork(row: pd.Series) -> str:
    role = str(row.get("panel_role", ""))
    if "outlier" in role:
        return "assignment_outlier_not_area_pipeline"
    nhd = row.get("stage_a_nhd_totdasqkm_zip")
    poly = row.get("stage_d_swatgenx_postprocessed_polygon_upstream_km2")
    ch = row.get("stage_f_chandeg_km2")
    if not all(np.isfinite(x) for x in (nhd, poly, ch) if x is not None):
        return "insufficient_data"
    nhd, poly, ch = float(nhd), float(poly), float(ch)
    if _rel_close(poly, nhd) and not _rel_close(ch, nhd) and ch > nhd:
        return "qswat_swatplus_export_or_chandeg_assignment"
    if _rel_close(poly, ch) and ch > nhd * (1 + REL_TOL):
        return "swatgenx_postprocessed_polygon_construction"
    if nhd < poly < ch or (nhd < poly and _rel_close(ch, poly)):
        return "both_polygon_and_export_contribute"
    if _rel_close(ch, nhd):
        return "agreement_at_all_stages"
    if ch < nhd:
        return "swat_below_nhd_review_assignment"
    return "mixed_review"


def first_offset_stage(row: pd.Series) -> str:
    """First stage where SWAT-side cumulative exceeds NHD TotDASqKm by >REL_TOL."""
    nhd = row.get("stage_a_nhd_totdasqkm_zip")
    if nhd is None or not np.isfinite(nhd):
        return "unknown"
    nhd = float(nhd)
    stages = [
        ("C_clean_streams_upstream", "stage_c_clean_streams_upstream_areasqkm_km2"),
        ("D_watershed_polygons", "stage_d_swatgenx_postprocessed_polygon_upstream_km2"),
        ("E_qswat_areac_assignment", "stage_e_qswat_areac_at_assignment_km2"),
        ("F_chandeg", "stage_f_chandeg_km2"),
    ]
    for label, col in stages:
        v = row.get(col)
        if v is not None and np.isfinite(v) and float(v) > nhd * (1 + REL_TOL):
            return label
    return "none_exceed_before_F" if float(row.get("stage_f_chandeg_km2", 0)) <= nhd * (1 + REL_TOL) else "F_chandeg"


def main() -> None:
    panel = pd.read_csv(PANEL, dtype={"usgs_site_no": str})
    panel["usgs_site_no"] = panel["usgs_site_no"].str.zfill(8)
    v2 = pd.read_csv(V2, dtype={"usgs_site_no": str})
    v2["usgs_site_no"] = v2["usgs_site_no"].str.zfill(8)
    xw = pd.read_csv(CROSSWALK)
    xw["gis_id"] = pd.to_numeric(xw["gis_id"], errors="coerce")
    readme_areas = parse_readme_assignment()
    chandeg = parse_chandeg(TXTINOUT)
    gis_area = chandeg.set_index("gis_id")["area_km2"].to_dict()

    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    h12_domain = {h.zfill(12) for h in huc12s}
    domain_ids = load_domain_catchment_ids(h12_domain)

    print("Loading zip original flowlines…")
    flows_orig = load_flows_orig_zip(domain_ids)
    by_dn_orig = build_upstream_by_dn(flows_orig)
    area_orig_reach = flows_orig.set_index("NHDPlusID")["AreaSqKm"].astype(float).to_dict()

    print("Loading cleaned streams.pkl…")
    streams_clean = load_streams_clean(domain_ids)
    by_dn_clean = build_upstream_by_dn(streams_clean)

    print("Loading watersheds.pkl polygon areas (post-processed)…")
    ws_area = load_watershed_polygon_area_km2(domain_ids)

    v2_idx = v2.set_index("usgs_site_no")
    xw_gis = xw.set_index("gis_id")

    rows = []
    for _, pr in panel.iterrows():
        site = pr["usgs_site_no"]
        role = pr["role"]
        gis_ch = None
        if site in v2_idx.index:
            gis_ch = v2_idx.loc[site, "gis_channel"]
            if isinstance(gis_ch, pd.Series):
                gis_ch = gis_ch.iloc[0]
        nhd_xw = None
        if gis_ch is not None and not pd.isna(gis_ch) and int(gis_ch) in xw_gis.index:
            xr = xw_gis.loc[int(gis_ch)]
            nhd_xw = int(xr["nhdplusid_crosswalk"]) if not pd.isna(xr["nhdplusid_crosswalk"]) else None

        stage_a = float(v2_idx.loc[site, "nhd_totdasqkm_km2"]) if site in v2_idx.index else None
        stage_b = float(v2_idx.loc[site, "nhd_orig_upstream_catchment_sum_km2"]) if site in v2_idx.index else None
        stage_c = float(v2_idx.loc[site, "nhd_clean_upstream_catchment_sum_km2"]) if site in v2_idx.index else None
        stage_f = float(gis_area.get(int(gis_ch))) if gis_ch is not None and int(gis_ch) in gis_area else None
        stage_e = readme_areas.get(site)

        stage_d = stage_d_stream = float("nan")
        n_up_d = 0
        stage_g_reach_tda = None
        if nhd_xw is not None:
            stage_d, n_up_d = upstream_area_km2(nhd_xw, streams_clean, ws_area, by_dn_clean)
            stage_d_stream, _ = upstream_area_km2(
                nhd_xw, streams_clean, streams_clean.set_index("NHDPlusID")["AreaSqKm"].astype(float).to_dict(), by_dn_clean
            )
            tda_row = streams_clean.loc[streams_clean["NHDPlusID"] == nhd_xw, "TotDASqKm"]
            if not tda_row.empty and pd.notna(tda_row.iloc[0]):
                stage_g_reach_tda = float(tda_row.iloc[0])

        row = {
            "usgs_site_no": site,
            "panel_role": role,
            "gis_channel": int(gis_ch) if gis_ch is not None and not pd.isna(gis_ch) else None,
            "nhdplusid_crosswalk": nhd_xw,
            "stage_a_nhd_totdasqkm_zip": stage_a,
            "stage_b_nhd_orig_upstream_areasqkm_zip": stage_b,
            "stage_c_clean_streams_upstream_areasqkm_km2": stage_c,
            "stage_g_streams_pkl_reach_totdasqkm": stage_g_reach_tda,
            "stage_g_note": "VAA TotDASqKm on crosswalk reach in national streams.pkl (pre-QSWAT attribute; not in SWAT_plus_streams.shp)",
            "stage_d_swatgenx_postprocessed_polygon_upstream_km2": stage_d,
            "stage_d_prime_streams_upstream_areasqkm_clean": stage_d_stream,
            "stage_d_polygon_minus_stream_areasqkm": round(stage_d - stage_d_stream, 2)
            if np.isfinite(stage_d) and np.isfinite(stage_d_stream)
            else None,
            "stage_d_upstream_n_reaches": n_up_d,
            "stage_e_qswat_areac_at_assignment_km2": stage_e,
            "stage_e_note": "from streamflow_data/README.md (rivs1 at assignment; shapes not on disk now)",
            "stage_f_chandeg_km2": stage_f,
            "pct_f_vs_a": _pct_diff(stage_f, stage_a),
            "pct_d_vs_a": _pct_diff(stage_d, stage_a),
            "pct_e_vs_a": _pct_diff(stage_e, stage_a),
            "pct_f_vs_d": _pct_diff(stage_f, stage_d),
            "pct_g_vs_a": _pct_diff(stage_g_reach_tda, stage_a),
            "pct_e_vs_g": _pct_diff(stage_e, stage_g_reach_tda),
            "first_stage_swat_side_exceeds_nhd_tda": None,
            "fork_classification": None,
        }
        row["first_stage_swat_side_exceeds_nhd_tda"] = first_offset_stage(pd.Series(row))
        row["fork_classification"] = classify_fork(pd.Series(row))
        rows.append(row)

    df = pd.DataFrame(rows)
    out_csv = OUT_DIR / "peace-drainage-area-pipeline-trace.csv"
    df.to_csv(out_csv, index=False)

    mainstem = df[df["panel_role"].str.startswith("mainstem")]
    lines = [
        "# Peace phase 3 — pipeline trace results",
        "",
        "**Stage D label:** `swatgenx_postprocessed_polygon_upstream_km2` = upstream Σ of **watersheds.pkl**",
        "polygon areas (orphan-dissolved national artifact), domain-clipped to Peace HUC-12s — **not** the",
        "per-project QSWAT `Watershed/Shapes` (missing for Peace HUC-8 on disk).",
        "",
        "**Stage E:** `AreaC` from `streamflow_data/README.md` at gage-assignment time (when rivs1 existed).",
        "",
        "**Stage G:** `TotDASqKm` on the crosswalk reach in national `streams.pkl` (NHD VAA carried through",
        "preprocessing; **not** written to `SWAT_plus_streams.shp`, which has no drainage-area field).",
        "",
        f"Panel: `{PANEL.name}` · Output: `{out_csv.name}`",
        "",
        "## Fork summary (10 gages)",
        "",
        "| Site | Role | NHD TDA | D polygons | E AreaC | F chandeg | Fork | First exceed |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['usgs_site_no']} | {r['panel_role']} | {r.get('stage_a_nhd_totdasqkm_zip', '—')} | "
            f"{r.get('stage_d_swatgenx_postprocessed_polygon_upstream_km2', '—')} | "
            f"{r.get('stage_e_qswat_areac_at_assignment_km2', '—')} | {r.get('stage_f_chandeg_km2', '—')} | "
            f"{r.get('fork_classification', '—')} | {r.get('first_stage_swat_side_exceeds_nhd_tda', '—')} |"
        )

    if len(mainstem):
        lines.extend(
            [
                "",
                "## Mainstem pattern",
                "",
                f"Median SWAT/NHD at stage F: {(mainstem['stage_f_chandeg_km2'] / mainstem['stage_a_nhd_totdasqkm_zip']).median():.3f}",
                f"Median polygon/NHD at stage D: {(mainstem['stage_d_swatgenx_postprocessed_polygon_upstream_km2'] / mainstem['stage_a_nhd_totdasqkm_zip']).median():.3f}",
                f"Median AreaC/NHD at stage E: {(mainstem['stage_e_qswat_areac_at_assignment_km2'] / mainstem['stage_a_nhd_totdasqkm_zip']).median():.3f}",
            ]
        )

    md_path = OUT_DIR / "peace-drainage-area-pipeline-trace.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_csv}")
    print(f"Wrote {md_path}")
    print(df[["usgs_site_no", "panel_role", "fork_classification", "first_stage_swat_side_exceeds_nhd_tda"]].to_string())


if __name__ == "__main__":
    main()

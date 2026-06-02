#!/usr/bin/env python3
"""Export drainage-area audit (chandeg.con vs NHD HR vs NWIS) for all paper evaluation models."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402
from run_nhd_preprocessing_qa_benchmark import (  # noqa: E402
    _assign_catchments_to_huc12,
    _normalize_huc12,
    _normalize_nhdplus_id,
    _original_nhd_vpuid,
    _pick_vaa_columns,
    resolve_domain_huc12s,
)
from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    USER_ROOT,
    load_station_names,
    parse_chandeg,
    pick_nhd_reach,
)
from streamflow_drainage_area import (  # noqa: E402
    load_station_drainage_area_km2,
    load_wbd_upstream_area_km2,
)


def load_nwis_da_km2(site_no: str, meta_csv: Path) -> float | None:
    """USGS NWIS site catalog drainage area (km²), not WBD HU12 sum."""
    da, _ = load_station_drainage_area_km2(site_no, meta_csv)
    return da

ROSTER = REPO / "publication/tables/tab-model-roster.csv"
OUT_JSON = REPO / "web_application/frontend/src/data/drainageAreaAuditCatalog.json"
OUT_INVESTIGATION_JSON = REPO / "web_application/frontend/src/data/drainageAreaAuditInvestigation.json"
OUT_DIR = REPO / "publication/analysis/qa/drainage-area-audit"
QA_DIR = REPO / "publication/analysis/qa"
PIPELINE_TRACE = QA_DIR / "peace-drainage-area-pipeline-trace.csv"
PEACE_V3_ASSIGNMENT = QA_DIR / "peace-station-assignment-v3-inventory.csv"

_nhd_cache: dict[str, gpd.GeoDataFrame] = {}
_peace_v3_gis_cache: dict[str, int] | None = None


def _peace_v3_gis_by_site() -> dict[str, int]:
    global _peace_v3_gis_cache
    if _peace_v3_gis_cache is not None:
        return _peace_v3_gis_cache
    if not PEACE_V3_ASSIGNMENT.is_file():
        _peace_v3_gis_cache = {}
        return _peace_v3_gis_cache
    df = pd.read_csv(PEACE_V3_ASSIGNMENT, dtype={"site_no": str})
    df["site_no"] = df["site_no"].str.zfill(8)
    out: dict[str, int] = {}
    for _, r in df.iterrows():
        gis = pd.to_numeric(r.get("swat_gis_id"), errors="coerce")
        if pd.notna(gis):
            out[str(r["site_no"])] = int(gis)
    _peace_v3_gis_cache = out
    return _peace_v3_gis_cache


def _load_nhd_domain(vpuid: str, huc12s: list[str]) -> gpd.GeoDataFrame:
    key = f"{vpuid}:{','.join(sorted(huc12s))}"
    if key in _nhd_cache:
        return _nhd_cache[key]
    h12_domain = {h.zfill(12) for h in huc12s}
    with _original_nhd_vpuid(vpuid) as layers:
        catchment = _normalize_nhdplus_id(
            gpd.GeoDataFrame(layers["NHDPlusCatchment"], geometry="geometry")
        )
        if catchment.crs is None:
            catchment = catchment.set_crs("EPSG:4326", allow_override=True)
        wbd = _normalize_huc12(gpd.GeoDataFrame(layers["WBDHU12"], geometry="geometry"))
        if wbd.crs is None:
            wbd = wbd.set_crs("EPSG:4326", allow_override=True)
        catch_in_domain = _assign_catchments_to_huc12(catchment, wbd, h12_domain)
        domain_catch_ids = set(catch_in_domain["NHDPlusID"].dropna().astype("int64"))
        flowline = _normalize_nhdplus_id(layers["NHDFlowline"].copy())
        vaa = _pick_vaa_columns(layers["NHDPlusFlowlineVAA"])
        tda_col = next(
            (c for c in vaa.columns if str(c).lower() in ("totdasqkm", "tot_da_sqkm")),
            None,
        )
        vaa_cols = ["NHDPlusID"] + ([tda_col] if tda_col else [])
        merged = flowline.merge(vaa[vaa_cols], on="NHDPlusID", how="inner")
        flows_in = merged[merged["NHDPlusID"].isin(domain_catch_ids)].copy()
        if tda_col and tda_col != "TotDASqKm":
            flows_in = flows_in.rename(columns={tda_col: "TotDASqKm"})
        flows_in["TotDASqKm"] = pd.to_numeric(flows_in.get("TotDASqKm"), errors="coerce")
    gdf = gpd.GeoDataFrame(flows_in, geometry="geometry", crs=catchment.crs)
    _nhd_cache[key] = gdf
    return gdf


def _tier_label(row: dict) -> str:
    tier_val = row.get("tier")
    if tier_val is None or (isinstance(tier_val, float) and pd.isna(tier_val)):
        if str(row.get("cohort") or "").lower() == "calibration":
            return "Cal"
        return ""
    return str(tier_val).strip()


def _json_safe(obj):
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, (np.floating, np.integer)):
        v = float(obj)
        return None if np.isnan(v) or np.isinf(v) else v
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj


def _ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return None
    return float(a / b)


def _classify_row(swat: float | None, nhd: float | None, nwis: float | None, r_sn: float | None) -> str:
    if swat is None:
        return "missing_chandeg"
    if nhd is None:
        return "missing_nhd"
    if r_sn is not None and 0.5 <= r_sn <= 2.0:
        return "swat_nhd_ok"
    if r_sn is not None and r_sn < 0.2:
        return "assignment_outlier_low"
    if r_sn is not None and r_sn > 5.0:
        return "assignment_outlier_high"
    return "swat_nhd_moderate"


def audit_model(row: dict, names: dict[str, str]) -> dict | None:
    ws_id = row["workspace_model_id"].strip()
    label = row["label"]
    parts = ws_id.split("/")
    vpuid, level, name = parts[0], parts[1], parts[2]
    meta_csv = Path(SWATGenXPaths.streamflow_vpuid_path) / vpuid / f"meta_{vpuid}.csv"

    model_base = USER_ROOT / ws_id / "SWAT_MODEL_Web_Application"
    txtinout = model_base / "Scenarios" / "Default" / "TxtInOut"
    stations_shp = model_base.parent / "streamflow_data" / "stations.shp"
    if not stations_shp.is_file() or not (txtinout / "chandeg.con").is_file():
        print(f"  skip {ws_id}: missing stations or chandeg.con")
        return None

    if level == "huc8":
        huc12s = derive_huc12_list_for_huc8(name, vpuid=vpuid)
    else:
        huc12s = resolve_domain_huc12s(vpuid, level, name)
    if not huc12s:
        print(f"  skip {ws_id}: no HUC12 domain")
        return None

    chandeg = parse_chandeg(txtinout)
    gis_ids = set(chandeg["gis_id"].dropna().astype(int))
    gis_to_area = chandeg.set_index("gis_id")["area_km2"].to_dict()
    gis_to_lcha = chandeg.set_index("gis_id")["lcha"].to_dict()
    gis_to_chandeg_id = chandeg.set_index("gis_id")["chandeg_id"].to_dict()

    nhd = _load_nhd_domain(vpuid, huc12s)
    nhd_5070 = nhd.to_crs(ALBERS)

    stations = gpd.read_file(stations_shp)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")

    catalog_id = str(row["catalog_model_id"]).zfill(8)
    v3_gis = _peace_v3_gis_by_site() if catalog_id == "03100101" else {}

    station_rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        gis_ch = v3_gis.get(site)
        if gis_ch is None:
            gis_ch = int(st["channel"]) if pd.notna(st["channel"]) else None
        swat_km2 = float(gis_to_area[gis_ch]) if gis_ch is not None and gis_ch in gis_ids else None
        lcha = int(gis_to_lcha[gis_ch]) if gis_ch is not None and gis_ch in gis_to_lcha else None
        usgs_da = load_nwis_da_km2(site, meta_csv)
        wbd_da = load_wbd_upstream_area_km2(site, meta_csv)
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        nhd_row, _, _ = pick_nhd_reach(nhd_5070, gage_5070, usgs_da)
        nhd_km2 = float(nhd_row["TotDASqKm"]) if nhd_row is not None and pd.notna(nhd_row.get("TotDASqKm")) else None
        r_sn = _ratio(swat_km2, nhd_km2)
        r_su = _ratio(swat_km2, usgs_da)
        station_rows.append(
            {
                "usgsSiteNo": site,
                "stationName": names.get(site, ""),
                "gisChannel": gis_ch,
                "swatLcha": lcha,
                "swatplusDrainageAreaKm2": round(swat_km2, 2) if swat_km2 is not None else None,
                "nhdHrTotdasqkmKm2": round(nhd_km2, 2) if nhd_km2 is not None else None,
                "nwisDrainageAreaKm2": round(usgs_da, 2) if usgs_da is not None else None,
                "wbdUpstreamHu12AreaKm2": round(wbd_da, 2) if wbd_da is not None else None,
                "ratioSwatNhd": round(r_sn, 4) if r_sn is not None else None,
                "ratioSwatNwis": round(r_su, 4) if r_su is not None else None,
                "auditClass": _classify_row(swat_km2, nhd_km2, usgs_da, r_sn),
            }
        )

    df = pd.DataFrame(station_rows)
    matched = df.dropna(subset=["swatplusDrainageAreaKm2", "nhdHrTotdasqkmKm2"])
    ratios = matched["ratioSwatNhd"].astype(float)
    within = int(((ratios >= 0.5) & (ratios <= 2.0)).sum()) if len(ratios) else 0

    summary = {
        "nStations": int(len(df)),
        "nSwatplus": int(df["swatplusDrainageAreaKm2"].notna().sum()),
        "nNhd": int(df["nhdHrTotdasqkmKm2"].notna().sum()),
        "nNwis": int(df["nwisDrainageAreaKm2"].notna().sum()),
        "nMatchedSwatNhd": int(len(matched)),
        "medianSwatNhdRatio": round(float(ratios.median()), 4) if len(ratios) else None,
        "p10SwatNhdRatio": round(float(ratios.quantile(0.1)), 4) if len(ratios) else None,
        "p90SwatNhdRatio": round(float(ratios.quantile(0.9)), 4) if len(ratios) else None,
        "withinHalfToDouble": within,
        "nMissingChandeg": int((df["auditClass"] == "missing_chandeg").sum()),
        "nAssignmentOutliers": int(
            df["auditClass"].isin(["assignment_outlier_low", "assignment_outlier_high"]).sum()
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / f"drainage-area-{row['catalog_model_id']}.csv"
    df.to_csv(
        csv_path,
        index=False,
        columns=[
            "usgsSiteNo",
            "stationName",
            "gisChannel",
            "swatLcha",
            "swatplusDrainageAreaKm2",
            "nhdHrTotdasqkmKm2",
            "nwisDrainageAreaKm2",
            "wbdUpstreamHu12AreaKm2",
            "ratioSwatNhd",
            "ratioSwatNwis",
            "auditClass",
        ],
    )

    return {
        "catalogModelId": str(row["catalog_model_id"]).strip().zfill(8),
        "workspaceModelId": ws_id,
        "label": label,
        "tier": _tier_label(row),
        "cohort": row.get("cohort") or "",
        "state": row.get("state") or "",
        "objectives": row.get("objectives") or "",
        "summary": summary,
        "stations": station_rows,
        "csvPath": str(csv_path.relative_to(REPO)),
    }


def export_peace_investigation(catalog: dict) -> None:
    """Peace HUC-8 deep-dive: scrutiny answers + pipeline trace for public audit discussion."""
    peace = next((m for m in catalog.get("models", []) if m.get("catalogModelId") == "03100101"), None)
    ps = peace.get("summary", {}) if peace else {}

    panel_rows = []
    if PIPELINE_TRACE.is_file():
        trace = pd.read_csv(PIPELINE_TRACE, dtype={"usgs_site_no": str})
        trace["usgs_site_no"] = trace["usgs_site_no"].str.zfill(8)
        for _, r in trace.iterrows():
            panel_rows.append(
                {
                    "usgsSiteNo": r["usgs_site_no"],
                    "panelRole": r.get("panel_role"),
                    "nhdTotdasqkmKm2": _json_safe(r.get("stage_a_nhd_totdasqkm_zip")),
                    "streamsPklTotdasqkmKm2": _json_safe(r.get("stage_g_streams_pkl_reach_totdasqkm")),
                    "polygonUpstreamKm2": _json_safe(r.get("stage_d_swatgenx_postprocessed_polygon_upstream_km2")),
                    "qswatAreacKm2": _json_safe(r.get("stage_e_qswat_areac_at_assignment_km2")),
                    "chandegKm2": _json_safe(r.get("stage_f_chandeg_km2")),
                    "rivs1AreacKm2": None,
                    "pctChandegVsNhd": _json_safe(r.get("pct_f_vs_a")),
                    "firstExceedStage": r.get("first_stage_swat_side_exceeds_nhd_tda"),
                    "forkClassification": r.get("fork_classification"),
                }
            )

    scrutiny = [
        {
            "id": "cumulative-not-local",
            "phase": 1,
            "title": "Comparing cumulative SWAT+ to local NHD reach area",
            "status": "ruled_out",
            "question": "Is the gap because chandeg.con is cumulative but we compared to local AreaSqKm?",
            "verdict": "No — headline metrics use NHD TotDASqKm (cumulative VAA).",
            "evidence": [
                "Peace @ SR 60 (02294650): NHD TotDASqKm 857 km² vs local reach AreaSqKm ~3.6 km²; SWAT+ chandeg 1002 km² aligns with cumulative scale.",
                "Median |Δ| vs TotDASqKm on 73 matched Peace gages: ~10.2%; vs local reach area: misleading (~14,900% median).",
            ],
        },
        {
            "id": "original-nhd-not-merged-pickle",
            "phase": 2,
            "title": "Accidentally comparing to post-processed streams.pkl / watersheds.pkl",
            "status": "ruled_out",
            "question": "Does the offset come from comparing SWAT+ to already-merged national artifacts?",
            "verdict": "No — headline NHD is from the original HU4 geodatabase zip, not merged pickles.",
            "evidence": [
                "nhd_totdasqkm_km2 and upstream Σ AreaSqKm are computed from unzipped NHDPlusFlowlineVAA on the domain-clipped zip.",
                "Cleaned streams.pkl upstream Σ is only ~1–2% below zip on mainstem — far smaller than the ~15–17% SWAT+ excess.",
            ],
        },
        {
            "id": "nhd-vaa-inconsistency",
            "phase": 2,
            "title": "NHD TotDASqKm inconsistent with upstream Σ AreaSqKm",
            "status": "ruled_out",
            "question": "Is NHD VAA internally inconsistent on mainstem reaches?",
            "verdict": "No on Peace mainstem — TotDASqKm and upstream Σ AreaSqKm agree (e.g. 857 km² at 02294650).",
            "evidence": [
                "Phase 2 crosswalk: original zip TotDASqKm matches original upstream catchment sum on mainstem picks.",
                "The ~145 km² SWAT−NHD gap (1002 − 857) is not explained by VAA definition mismatch alone.",
            ],
        },
        {
            "id": "orphan-merge",
            "phase": 1,
            "title": "Orphan catchment merge onto mainstem",
            "status": "ruled_out",
            "question": "Did orphan-catchment dissolution pile extra area onto mainstem NHD IDs?",
            "verdict": "Unlikely for the systematic mainstem +10–17% band.",
            "evidence": [
                "Domain preprocess merges hundreds of orphans nationally; per-gage geometry tests did not stack orphan area on Peace mainstem NHD IDs.",
                "Post-processed polygon upstream Σ (stage D) is only ~+2–3% vs NHD — not +15–17%.",
            ],
        },
        {
            "id": "lake-omission",
            "phase": 1,
            "title": "SWAT+ omits lakes that NHD counts",
            "status": "ruled_out",
            "question": "Does lake/waterbody handling explain SWAT+ > NHD on mainstem?",
            "verdict": "Not the dominant pattern — SWAT+ is higher than NHD, not lower.",
            "evidence": [
                "Lake omission would bias SWAT+ low vs NHD; mainstem shows systematic positive bias (60/73 matched gages SWAT+ > NHD).",
                "Upstream WB-linked waterbody area at 02294650 (~126 km²) is too small to explain ~145 km² SWAT−NHD alone.",
            ],
        },
        {
            "id": "preinflated-totdasqkm",
            "phase": 3,
            "title": "SWATGenX pre-inflated TotDASqKm before QSWAT",
            "status": "ruled_out",
            "question": "Did streams.pkl or preprocessing corrupt the reach drainage attribute before QSWAT?",
            "verdict": "No — reach TotDASqKm in streams.pkl matches original zip NHD within <0.1% on the panel.",
            "evidence": [
                "02294650: zip 856.95 km² vs streams.pkl 856.95 km²; QSWAT AreaC (README) 1002.2 km².",
                "02294760: zip 891.56 vs streams.pkl 891.56; AreaC 1046.57 km².",
            ],
        },
        {
            "id": "polygon-stage-d",
            "phase": 3,
            "title": "SWATGenX post-processed watershed polygons",
            "status": "ruled_out",
            "question": "Does national watersheds.pkl upstream area carry the mainstem offset?",
            "verdict": "Not as the primary source — stage D is ~+2–3% vs NHD on mainstem panel.",
            "evidence": [
                "02294650: polygon upstream Σ 874 km² vs NHD 857 km² (+2%); chandeg 1002 km² (+17%).",
                "Median polygon/NHD ≈ 1.03 on three mainstem panel gages; median chandeg/NHD ≈ 1.17.",
            ],
        },
        {
            "id": "qswat-copied-shapefile-column",
            "phase": 3,
            "title": "QSWAT copied a wrong drainage column from SWAT_plus_streams.shp",
            "status": "ruled_out",
            "question": "Did QSWAT copy an inflated area field we exported on the channel shapefile?",
            "verdict": "Unlikely — SWAT_plus_streams.shp has no TotDASqKm or AreaC column.",
            "evidence": [
                "SWATGenX write_output exports topology, length, elevations, and lake flags only — not drainage-area attributes.",
                "Offset appears at QSWAT AreaC / chandeg, not at reach attributes in streams.pkl.",
            ],
        },
        {
            "id": "qswat-taudem-vs-nhd-vaa",
            "phase": 3,
            "title": "QSWAT/TauDEM contributing area vs NHD VAA",
            "status": "leading",
            "question": "Why does SWAT+ cumulative drainage exceed original NHD on mainstem?",
            "verdict": "Leading explanation: delineation-definition difference, not necessarily a preprocessing bug.",
            "evidence": [
                "Polygons and NHD reach attributes agree; QSWAT AreaC and chandeg.con jump ~+15–17% at the same stage.",
                "Protects NHDPlus HR preprocessing; narrows issue to QSWAT/TauDEM channel-area semantics or SWAT+ export.",
            ],
        },
        {
            "id": "rivs1-sqlite-stage-h",
            "phase": 3,
            "title": "Live rivs1.AreaC / SQLite before chandeg export",
            "status": "pending",
            "question": "Is the offset already in rivs1 before TxtInOut, or introduced at text export?",
            "verdict": "Pending — Peace Watershed/Shapes not on disk; re-run phase 3b after restore.",
            "evidence": [
                "If rivs1 AreaC ≈ chandeg ≫ NHD: QSWAT/TauDEM channel area creates the offset.",
                "If rivs1 ≈ NHD but chandeg high: SWAT+ text export introduces the offset.",
            ],
        },
        {
            "id": "assignment-outliers",
            "phase": 1,
            "title": "Gage–channel assignment outliers",
            "status": "separate_class",
            "question": "What about extreme SWAT/NHD ratios on tributary or mis-assigned gages?",
            "verdict": "Separate class — not basin-wide conversion failure.",
            "evidence": [
                f"Peace: {ps.get('nAssignmentOutliers', 4)} assignment outliers flagged; e.g. tiny SWAT+ vs large NHD on tributary picks.",
                "Three gages lack chandeg rows (reservoir/auxiliary channels) — reported explicitly, not folded into headline metrics.",
            ],
        },
    ]

    stages = [
        {"code": "A", "label": "Original NHD TotDASqKm (zip VAA)", "mainstemMedianRatio": 1.0, "role": "Reference"},
        {"code": "G", "label": "streams.pkl reach TotDASqKm", "mainstemMedianRatio": 1.0, "role": "Pre-QSWAT attribute"},
        {"code": "B", "label": "Original upstream Σ AreaSqKm (zip)", "mainstemMedianRatio": 1.0, "role": "Cross-check"},
        {"code": "C", "label": "Cleaned streams.pkl upstream Σ", "mainstemMedianRatio": 0.99, "role": "Secondary"},
        {
            "code": "D",
            "label": "watersheds.pkl upstream polygon Σ",
            "mainstemMedianRatio": 1.03,
            "role": "SWATGenX post-processed polygons (national clip; not per-project QSWAT shapes)",
        },
        {"code": "E", "label": "QSWAT AreaC at assignment", "mainstemMedianRatio": 1.17, "role": "First large exceed"},
        {"code": "F", "label": "chandeg.con (executable SWAT+)", "mainstemMedianRatio": 1.17, "role": "Headline audit column"},
        {"code": "H", "label": "rivs1.AreaC / SQLite (live)", "mainstemMedianRatio": None, "role": "Pending artifact restore"},
    ]

    payload = {
        "lastUpdated": catalog.get("lastUpdated"),
        "peaceCatalogModelId": "03100101",
        "peaceLabel": peace.get("label") if peace else "Peace River HUC-8",
        "peaceSummary": ps,
        "exampleMainstem": {
            "usgsSiteNo": "02294650",
            "stationLabel": "Peace River at SR 60 near Bartow",
            "nhdTotdasqkmKm2": 856.95,
            "nhdLocalAreasqkmKm2": 3.6,
            "swatChandegKm2": 1002.2,
            "pctVsTotdasqkm": 17.0,
        },
        "auditChainSummary": (
            "Original NHD and streams.pkl reach TotDASqKm match; post-processed polygon upstream "
            "area is ~+2–3% vs NHD; QSWAT AreaC and chandeg.con are ~+15–17% on mainstem. "
            "The offset first appears at the QSWAT/SWAT+ channel-area stage."
        ),
        "pipelineStages": stages,
        "scrutiny": scrutiny,
        "peacePanelTrace": panel_rows,
        "internalArtifactsNote": (
            "Stage D uses national watersheds.pkl clipped to Peace HUC-12s — not necessarily "
            "identical to per-project QSWAT Watershed/Shapes when those files are missing."
        ),
    }
    OUT_INVESTIGATION_JSON.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")
    print(f"Wrote {OUT_INVESTIGATION_JSON}")


def main() -> None:
    roster = pd.read_csv(ROSTER, dtype={"catalog_model_id": str})
    names = load_station_names()
    models = []
    total_stations = 0
    total_matched = 0
    total_within = 0

    print(f"Auditing {len(roster)} evaluation models from {ROSTER.name}")
    for _, row in roster.iterrows():
        print(f"  {row['catalog_model_id']} {row['label']}...")
        result = audit_model(row.to_dict(), names)
        if result:
            models.append(result)
            s = result["summary"]
            total_stations += s["nStations"]
            total_matched += s["nMatchedSwatNhd"]
            total_within += s["withinHalfToDouble"]

    catalog = {
        "lastUpdated": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "methodology": {
            "swatSource": (
                "TxtInOut/chandeg.con column area (hectares ÷ 100), row matched by GIS channel id "
                "(v3 NHD-first/SWAT-second assignment for Peace 03100101; stations.shp channel elsewhere)"
            ),
            "nhdSource": "Original NHDPlus HR HU4 geodatabase flowline TotDASqKm within 500 m of gage (domain-clipped)",
            "nwisSource": "meta_{VPUID}.csv nwis_drain_area_km2 (USGS NWIS site-service drain_area_va / contrib)",
            "wbdSource": "meta_{VPUID}.csv wbd_upstream_hu12_area_sqkm (sum of upstream WBD HU12 polygons; model context only)",
            "modelsRoot": "admin SWATplus_by_VPUID workspaces used in the publication evaluation",
        },
        "portfolioSummary": {
            "nModels": len(models),
            "nStations": total_stations,
            "nMatchedSwatNhd": total_matched,
            "nWithinHalfToDouble": total_within,
        },
        "models": models,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(_json_safe(catalog), indent=2), encoding="utf-8")
    print(f"\nWrote {OUT_JSON} ({len(models)} models, {total_stations} stations)")
    export_peace_investigation(catalog)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""NHD-first / SWAT-second USGS station assignment (v3) for any evaluation workspace."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    CONUS_STATIONS_CSV,
    USER_ROOT,
    load_station_names,
    parse_chandeg,
)
from streamflow_drainage_area import load_station_drainage_area_km2  # noqa: E402
from investigate_peace_drainage_area_upstream import (  # noqa: E402
    SNAP_M,
    parse_chandeg_gis_points,
    snap_gis_to_nhd_orig,
)
from inventory_peace_station_assignment_phase0 import (  # noqa: E402
    _assign_catchments_to_huc12,
    _normalize_huc12,
    _normalize_nhdplus_id,
    _original_nhd_vpuid,
    _pick_vaa_columns,
)
from map_peace_swat_second_phase2 import (  # noqa: E402
    assignment_class_for_row,
    build_hydroseq_maps,
    build_nhd_to_gis,
    map_reference_to_swat,
    normalize_reference_class,
)
from peace_nhd_first_pick import pick_nhd_reference_v1b  # noqa: E402
from review_peace_nhd_first_disagreements_phase1 import reach_attrs  # noqa: E402
from run_nhd_preprocessing_qa_benchmark import resolve_domain_huc12s  # noqa: E402
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

CALIBRATION_READY = frozenset({"mainstem_clean", "tributary_clean", "mainstem_known_nhd_offset"})
REVIEW_CLASSES = frozenset(
    {"lake_outlet_review", "canal_or_artificial_review", "assignment_ambiguous", "review"}
)
EXCLUDE_CLASSES = frozenset({"missing_output_channel", "exclude_from_auto_calibration"})

_VAA_RENAME = {
    "totdasqkm": "TotDASqKm",
    "tot_da_sqkm": "TotDASqKm",
    "areasqkm": "AreaSqKm",
    "streamorde": "StreamOrde",
    "streamorder": "StreamOrde",
    "streamleve": "StreamLeve",
    "levelpathi": "LevelPathI",
    "divergence": "Divergence",
    "hydroseq": "HydroSeq",
    "dnhydroseq": "DnHydroSeq",
    "uphydroseq": "UpHydroSeq",
}


def _normalize_vaa_columns(vaa: pd.DataFrame) -> pd.DataFrame:
    out = _normalize_nhdplus_id(vaa.copy())
    mapping: dict[str, str] = {}
    for c in out.columns:
        key = str(c).lower().replace(" ", "")
        if key in _VAA_RENAME:
            mapping[c] = _VAA_RENAME[key]
    return out.rename(columns=mapping)


@dataclass(frozen=True)
class AssignmentInputs:
    """Shared inputs for production streamflow assignment and shadow inventory."""

    vpuid: str
    level: str
    name: str
    txtinout: Path
    meta_csv: Path
    catalog_model_id: str = ""
    workspace_model_id: str = ""
    label: str = ""


@dataclass(frozen=True)
class ModelPaths:
    catalog_model_id: str
    workspace_model_id: str
    label: str
    vpuid: str
    level: str
    name: str
    txtinout: Path
    stations_shp: Path
    meta_csv: Path

    def as_assignment_inputs(self) -> AssignmentInputs:
        return AssignmentInputs(
            vpuid=self.vpuid,
            level=self.level,
            name=self.name,
            txtinout=self.txtinout,
            meta_csv=self.meta_csv,
            catalog_model_id=self.catalog_model_id,
            workspace_model_id=self.workspace_model_id,
            label=self.label,
        )


def load_nhd_enriched_domain(vpuid: str, huc12s: list[str]) -> gpd.GeoDataFrame:
    h12_domain = {h.zfill(12) for h in huc12s}
    with _original_nhd_vpuid(vpuid) as layers:
        catchment = _normalize_nhdplus_id(gpd.GeoDataFrame(layers["NHDPlusCatchment"], geometry="geometry"))
        if catchment.crs is None:
            catchment = catchment.set_crs("EPSG:4326", allow_override=True)
        wbd = _normalize_huc12(gpd.GeoDataFrame(layers["WBDHU12"], geometry="geometry"))
        catch_in = _assign_catchments_to_huc12(catchment, wbd, h12_domain)
        domain_ids = set(catch_in["NHDPlusID"].dropna().astype("int64"))

        flowline = _normalize_nhdplus_id(layers["NHDFlowline"].copy())
        vaa = _normalize_vaa_columns(_pick_vaa_columns(layers["NHDPlusFlowlineVAA"]))
        vaa_cols = [
            c
            for c in (
                "NHDPlusID",
                "TotDASqKm",
                "AreaSqKm",
                "StreamOrde",
                "HydroSeq",
                "DnHydroSeq",
                "LevelPathI",
                "Divergence",
            )
            if c in vaa.columns
        ]
        fl_cols = ["NHDPlusID", "FType", "FCode", "GNIS_Name", "WBArea_Permanent_Identifier"]
        for alt in ("StreamOrde", "StreamOrder", "StreamLeve"):
            if alt in flowline.columns and alt not in fl_cols:
                fl_cols.append(alt)
        fl_cols = [c for c in fl_cols if c in flowline.columns]
        flows = flowline[fl_cols].merge(vaa[vaa_cols], on="NHDPlusID", how="inner")
        if "StreamOrder" in flows.columns and "StreamOrde" not in flows.columns:
            flows = flows.rename(columns={"StreamOrder": "StreamOrde"})
        flows = flows[flows["NHDPlusID"].isin(domain_ids)].copy()
        for c in ("TotDASqKm", "AreaSqKm", "StreamOrde", "LevelPathI", "Divergence"):
            if c in flows.columns:
                flows[c] = pd.to_numeric(flows[c], errors="coerce")
        flows["HydroSeq"] = pd.to_numeric(flows["HydroSeq"], errors="coerce").astype("Int64")
        flows["DnHydroSeq"] = pd.to_numeric(flows["DnHydroSeq"], errors="coerce").fillna(0).astype("Int64")
        fl_geom = flowline[["NHDPlusID", "geometry"]].drop_duplicates("NHDPlusID")
        merged = flows.merge(fl_geom, on="NHDPlusID", how="left")
    return gpd.GeoDataFrame(merged, geometry="geometry", crs=catchment.crs)


def resolve_model_paths(row: dict) -> ModelPaths | None:
    ws_id = str(row["workspace_model_id"]).strip()
    parts = ws_id.split("/")
    if len(parts) != 3:
        return None
    vpuid, level, name = parts
    from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402

    model_base = USER_ROOT / ws_id / "SWAT_MODEL_Web_Application"
    txtinout = model_base / "Scenarios" / "Default" / "TxtInOut"
    stations_shp = model_base / "streamflow_data" / "stations.shp"
    if not stations_shp.is_file():
        stations_shp = model_base.parent / "streamflow_data" / "stations.shp"  # legacy site-level
    if not stations_shp.is_file() or not (txtinout / "chandeg.con").is_file():
        return None
    meta_csv = Path(SWATGenXPaths.streamflow_vpuid_path) / vpuid / f"meta_{vpuid}.csv"
    return ModelPaths(
        catalog_model_id=str(row["catalog_model_id"]).strip().zfill(8),
        workspace_model_id=ws_id,
        label=str(row.get("label") or ""),
        vpuid=vpuid,
        level=level,
        name=name,
        txtinout=txtinout,
        stations_shp=stations_shp,
        meta_csv=meta_csv,
    )


def domain_huc12s_for(vpuid: str, level: str, name: str) -> list[str]:
    if level == "huc8":
        return derive_huc12_list_for_huc8(name, vpuid=vpuid)
    return resolve_domain_huc12s(vpuid, level, name)


def domain_huc12s(paths: ModelPaths) -> list[str]:
    return domain_huc12s_for(paths.vpuid, paths.level, paths.name)


def load_conus_site_tp() -> dict[str, str]:
    if not CONUS_STATIONS_CSV.is_file():
        return {}
    df = pd.read_csv(CONUS_STATIONS_CSV, dtype={"site_no": str})
    df["site_no"] = df["site_no"].str.zfill(8)
    if "site_tp_cd" not in df.columns:
        return {}
    return df.set_index("site_no")["site_tp_cd"].astype(str).to_dict()


def load_nwis_da_for_vpuid(meta_csv: Path) -> dict[str, float]:
    """Per-site USGS NWIS catalog drainage area (km²) from meta, not WBD HU12 sum."""
    from streamflow_drainage_area import load_station_drainage_area_km2

    if not meta_csv.is_file():
        return {}
    meta = pd.read_csv(meta_csv, dtype={"site_no": str})
    meta["site_no"] = meta["site_no"].str.zfill(8)
    out: dict[str, float] = {}
    for sn in meta["site_no"].unique():
        da, _ = load_station_drainage_area_km2(sn, meta_csv)
        if da is not None and da > 0:
            out[sn] = da
    return out


def assign_stations_v3(
    inputs: AssignmentInputs,
    stations: gpd.GeoDataFrame,
    *,
    production_channels: dict[str, int] | None = None,
    names: dict[str, str] | None = None,
    site_tp: dict[str, str] | None = None,
    flows_gdf: gpd.GeoDataFrame | None = None,
) -> pd.DataFrame:
    """NHD-first / SWAT-second channel assignment for in-watershed USGS gages."""
    if not (inputs.txtinout / "chandeg.con").is_file():
        raise FileNotFoundError(f"Missing chandeg.con: {inputs.txtinout / 'chandeg.con'}")

    names = names or load_station_names()
    site_tp = site_tp or load_conus_site_tp()
    huc12s = domain_huc12s_for(inputs.vpuid, inputs.level, inputs.name)
    if not huc12s:
        raise ValueError(f"No HUC12 domain for {inputs.workspace_model_id or inputs.name}")

    if flows_gdf is None:
        flows_gdf = load_nhd_enriched_domain(inputs.vpuid, huc12s)
    flows_5070 = flows_gdf.to_crs(ALBERS)
    flows = flows_gdf.drop(columns=["geometry"], errors="ignore")
    hs_map, nhd_to_hs = build_hydroseq_maps(flows)

    chandeg_df = parse_chandeg(inputs.txtinout)
    chandeg_gis = set(chandeg_df["gis_id"].dropna().astype(int).tolist())
    chandeg_by_gis = chandeg_df.set_index("gis_id")[["lcha", "area_km2", "chandeg_id"]].to_dict("index")

    gis_pts = parse_chandeg_gis_points(inputs.txtinout)
    xw = snap_gis_to_nhd_orig(gis_pts, flows_gdf.to_crs("EPSG:5070"))
    if "NHDPlusID" in xw.columns:
        xw = xw.rename(columns={"NHDPlusID": "nhdplusid_crosswalk"})
    xw["nhdplusid_crosswalk"] = pd.to_numeric(xw["nhdplusid_crosswalk"], errors="coerce")
    nhd_to_gis = build_nhd_to_gis(xw, chandeg_gis)

    st = stations.copy()
    st["site_no"] = st["site_no"].astype(str).str.zfill(8)
    st = st.drop_duplicates(subset="site_no", keep="first")

    rows = []
    for _, row in st.iterrows():
        site = row["site_no"]
        prod_gis = None
        if production_channels is not None:
            prod_gis = production_channels.get(site)
        nm = names.get(site, row.get("station_name") or row.get("StationName") or "")
        usgs_da, usgs_src = load_station_drainage_area_km2(site, inputs.meta_csv)
        gage = gpd.GeoSeries([row.geometry], crs=st.crs).to_crs(ALBERS).iloc[0]
        tp = site_tp.get(site, "")

        ref_row, v1b_rule, v1b_ctx = pick_nhd_reference_v1b(flows_5070, gage, usgs_da, nm, tp)
        ref_nhd = int(ref_row["NHDPlusID"]) if ref_row is not None and pd.notna(ref_row.get("NHDPlusID")) else None
        ref_class = normalize_reference_class(v1b_ctx)
        ref_attr = reach_attrs(flows, ref_nhd) if ref_nhd else {}
        nhd_tda = ref_attr.get("totdasqkm")

        gis_id = None
        mapping_method = "missing"
        steps = 0
        mapped_nhd = None
        notes = ""

        if ref_nhd is not None:
            gis_id, mapping_method, steps, mapped_nhd = map_reference_to_swat(
                ref_nhd,
                hs_map,
                nhd_to_hs,
                nhd_to_gis,
                chandeg_gis,
                ref_class,
                ref_attr,
            )

        chandeg_present = gis_id is not None and int(gis_id) in chandeg_by_gis
        swat_da = None
        swat_lcha = None
        if chandeg_present:
            ent = chandeg_by_gis[int(gis_id)]
            swat_da = float(ent["area_km2"])
            swat_lcha = float(ent["lcha"]) if pd.notna(ent.get("lcha")) else None

        ratio = (swat_da / nhd_tda) if swat_da and nhd_tda and nhd_tda > 0 else None
        if mapping_method == "missing":
            notes = "No chandeg.con channel for reference reach or downstream walk."
        elif steps > 0 and mapped_nhd is not None:
            notes = f"Mapped at downstream step {steps} to NHD {mapped_nhd} (ref {ref_nhd})."

        assignment_class = assignment_class_for_row(
            ref_class,
            mapping_method,
            chandeg_present,
            ratio,
            ref_attr,
            steps,
        )
        cal_eligible = chandeg_present and assignment_class in CALIBRATION_READY
        same_gis = prod_gis is not None and gis_id is not None and int(prod_gis) == int(gis_id)

        rows.append(
            {
                "catalog_model_id": inputs.catalog_model_id,
                "workspace_model_id": inputs.workspace_model_id,
                "label": inputs.label,
                "site_no": site,
                "station_name": nm,
                "usgs_da_km2": usgs_da,
                "usgs_da_source": usgs_src,
                "v1b_nhdplusid": ref_nhd,
                "v1b_pick_rule": v1b_rule,
                "reference_class": ref_class,
                "reference_gnis": ref_attr.get("gnis_name"),
                "reference_ftype": ref_attr.get("ftype"),
                "reference_has_wb_link": ref_attr.get("has_wb_link"),
                "swat_gis_id": gis_id,
                "swat_lcha": swat_lcha,
                "mapping_method": mapping_method,
                "mapped_nhdplusid": mapped_nhd,
                "replacement_steps_downstream": steps,
                "chandeg_present": chandeg_present,
                "nhd_tda_km2": nhd_tda,
                "swat_da_km2": swat_da,
                "swat_nhd_ratio": ratio,
                "assignment_class": assignment_class,
                "calibration_eligible": cal_eligible,
                "production_gis_channel": prod_gis,
                "same_gis_as_production": same_gis if production_channels is not None else None,
                "notes": notes,
            }
        )

    return pd.DataFrame(rows)


def summarize_assignment_v3(df: pd.DataFrame, inputs: AssignmentInputs) -> dict:
    cal = df[df["calibration_eligible"] == True]  # noqa: E712
    ratios = cal["swat_nhd_ratio"].dropna().astype(float)
    n_v3 = int(df["swat_gis_id"].notna().sum())
    has_prod = df["production_gis_channel"].notna().any()
    n_changed = int((df["same_gis_as_production"] == False).sum()) if has_prod else 0  # noqa: E712

    return {
        "catalog_model_id": inputs.catalog_model_id,
        "workspace_model_id": inputs.workspace_model_id,
        "label": inputs.label,
        "vpuid": inputs.vpuid,
        "n_stations": int(len(df)),
        "n_production_assigned": int(df["production_gis_channel"].notna().sum()) if has_prod else None,
        "n_v3_assigned": n_v3,
        "n_same_gis": int((df["same_gis_as_production"] == True).sum()) if has_prod else None,  # noqa: E712
        "n_changed_gis": n_changed if has_prod else None,
        "pct_unchanged": round(100.0 * (len(df) - n_changed) / len(df), 1) if has_prod and len(df) else None,
        "n_exact_crosswalk": int((df["mapping_method"] == "exact_crosswalk").sum()),
        "n_downstream_replacement": int(
            df["mapping_method"].astype(str).str.contains("downstream_replacement", na=False).sum()
        ),
        "n_lake_outlet_replacement": int((df["mapping_method"] == "lake_outlet_replacement").sum()),
        "n_canal_or_artificial_review": int((df["assignment_class"] == "canal_or_artificial_review").sum()),
        "n_lake_outlet_review": int((df["assignment_class"] == "lake_outlet_review").sum()),
        "n_missing_output_channel": int(
            df["assignment_class"].isin(["missing_output_channel", "exclude_from_auto_calibration"]).sum()
        ),
        "n_calibration_ready": int(len(cal)),
        "n_review": int(df["assignment_class"].isin(REVIEW_CLASSES).sum()),
        "n_exclude": int(df["assignment_class"].isin(EXCLUDE_CLASSES).sum()),
        "median_swat_nhd_ratio_cal_ready": float(ratios.median()) if len(ratios) else None,
        "n_cal_outside_half_to_double": int(((ratios < 0.5) | (ratios > 2.0)).sum()) if len(ratios) else 0,
        "n_cal_outside_0_8_1_25": int(((ratios < 0.8) | (ratios > 1.25)).sum()) if len(ratios) else 0,
    }


def assign_model_v3(
    paths: ModelPaths,
    *,
    names: dict[str, str] | None = None,
    site_tp: dict[str, str] | None = None,
    nwis_da: dict[str, float] | None = None,
    flows_gdf: gpd.GeoDataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Return per-station detail rows and per-model summary dict (shadow vs production)."""
    stations = gpd.read_file(paths.stations_shp)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")
    production_channels = {
        str(r["site_no"]).zfill(8): int(r["channel"])
        for _, r in stations.iterrows()
        if pd.notna(r["channel"])
    }
    inputs = paths.as_assignment_inputs()
    df = assign_stations_v3(
        inputs,
        stations,
        production_channels=production_channels,
        names=names,
        site_tp=site_tp,
        flows_gdf=flows_gdf,
    )
    summary = summarize_assignment_v3(df, inputs)
    return df, summary


def comparison_frame(detail: pd.DataFrame) -> pd.DataFrame:
    """Production vs v3 side-by-side for shadow reports."""
    return detail[
        [
            "catalog_model_id",
            "site_no",
            "station_name",
            "production_gis_channel",
            "swat_gis_id",
            "same_gis_as_production",
            "v1b_nhdplusid",
            "mapping_method",
            "assignment_class",
            "calibration_eligible",
            "swat_nhd_ratio",
            "notes",
        ]
    ].rename(
        columns={
            "swat_gis_id": "v3_gis_channel",
            "production_gis_channel": "production_gis_channel",
        }
    )


def write_shadow_products(
    detail: pd.DataFrame,
    summary: dict,
    shadow_root: Path,
) -> None:
    mid = summary["catalog_model_id"]
    mdir = shadow_root / mid
    mdir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(mdir / "stations_assignment_v3.csv", index=False)
    comparison_frame(detail).to_csv(mdir / "stations_assignment_comparison.csv", index=False)
    payload = {
        "summary": summary,
        "stations": detail.replace({np.nan: None}).to_dict(orient="records"),
    }
    (mdir / "stations_assignment_v3.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

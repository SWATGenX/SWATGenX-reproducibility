#!/usr/bin/env python3
"""Compare SWAT+ TxtInOut channel areas (chandeg.con) vs original NHDPlus HR TotDASqKm for Peace HUC8 gages."""
from __future__ import annotations

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
)

from _swatgenx_paths import USER_ROOT  # noqa: E402  env-overridable: SWATGENX_USER_PATH / SWATGENX_EXAMPLE_USER
VPUID = "0310"
HUC8 = "03100101"
MODEL = "SWAT_MODEL_Web_Application"
SCENARIO = "Default"
GAGE_RADIUS_M = 500.0
ALBERS = "EPSG:5070"

MODEL_BASE = USER_ROOT / VPUID / "huc8" / HUC8 / MODEL
TXTINOUT = MODEL_BASE / "Scenarios" / SCENARIO / "TxtInOut"
STATIONS_SHP = MODEL_BASE.parent / "streamflow_data" / "stations.shp"
META_CSV = Path(SWATGenXPaths.streamflow_vpuid_path) / VPUID / f"meta_{VPUID}.csv"
CONUS_STATIONS_CSV = Path(SWATGenXPaths.USGS_CONUS_stations_path)
ZIP_DIR = Path(SWATGenXPaths.NHDPlus_VPUID_zipped_path)
OUT_DIR = REPO / "publication/analysis/qa"


def parse_chandeg(txtinout: Path) -> pd.DataFrame:
    """Parse chandeg.con; ``area`` is hectares (channel contributing / drainage area in SWAT+)."""
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
    df["lcha"] = pd.to_numeric(df["lcha"], errors="coerce")
    df["area_ha"] = pd.to_numeric(df["area"], errors="coerce")
    df["area_km2"] = df["area_ha"] / 100.0
    df["gis_id"] = pd.to_numeric(df["gis_id"], errors="coerce")
    return df


def parse_rout_unit_areas(txtinout: Path) -> dict[int, float]:
    """Sum rout_unit.con area (ha) by downstream SWAT channel id (obj_id when obj_typ=sdc)."""
    path = txtinout / "rout_unit.con"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    headers = lines[1].split()
    by_ch: dict[int, float] = {}
    for line in lines[2:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < len(headers):
            continue
        row = dict(zip(headers, parts[: len(headers)]))
        if str(row.get("obj_typ", "")).lower() != "sdc":
            continue
        ch = int(float(row["obj_id"]))
        by_ch[ch] = by_ch.get(ch, 0.0) + float(row["area"])
    return by_ch


def upstream_chandeg_ids(target_id: int, upstream_adj: dict[int, list[int]]) -> set[int]:
    seen: set[int] = set()
    stack = [target_id]
    while stack:
        cid = stack.pop()
        if cid in seen:
            continue
        seen.add(cid)
        for up in upstream_adj.get(cid, []):
            stack.append(up)
    return seen


def load_station_names() -> dict[str, str]:
    if not CONUS_STATIONS_CSV.is_file():
        return {}
    df = pd.read_csv(CONUS_STATIONS_CSV, dtype={"site_no": str})
    name_col = "station_nm" if "station_nm" in df.columns else "station_name"
    if name_col not in df.columns:
        return {}
    out = {}
    for _, row in df.iterrows():
        sn = str(row["site_no"]).strip().zfill(8)
        nm = row.get(name_col)
        if pd.notna(nm):
            out[sn] = str(nm).strip()
    return out


def load_usgs_da_km2(site_no: str) -> tuple[float | None, str]:
    from streamflow_drainage_area import load_station_drainage_area_km2

    return load_station_drainage_area_km2(site_no, META_CSV)


def load_nhd_flowlines_domain(huc12s: list[str]) -> gpd.GeoDataFrame:
    h12_domain = {h.zfill(12) for h in huc12s}
    with _original_nhd_vpuid(VPUID) as layers:
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
        vaa_cols = ["NHDPlusID", "TotDASqKm", "AreaSqKm", "LengthKM"]
        vaa_cols = [c for c in vaa_cols if c in vaa.columns]
        merged = flowline.merge(vaa[vaa_cols], on="NHDPlusID", how="inner")
        flows_in = merged[merged["NHDPlusID"].isin(domain_catch_ids)].copy()
    flows_in["TotDASqKm"] = pd.to_numeric(flows_in["TotDASqKm"], errors="coerce")
    return gpd.GeoDataFrame(flows_in, geometry="geometry", crs=catchment.crs)


def pick_nhd_reach(flowlines_5070: gpd.GeoDataFrame, gage_5070, usgs_da: float | None) -> tuple[pd.Series | None, str, float | None]:
    """Mirror floodplain gage-to-reach selection on original NHD TotDASqKm."""
    sp = flowlines_5070.copy()
    sp["_dist"] = sp.geometry.distance(gage_5070)
    band = sp[sp["_dist"] <= GAGE_RADIUS_M]
    if band.empty:
        band = sp.nsmallest(1, "_dist")
        rule = "global_closest"
    else:
        rule = "distance_only"
    if usgs_da is not None and usgs_da > 0 and len(band) > 1:
        best = None
        best_err = None
        for _, row in band.iterrows():
            tda = row.get("TotDASqKm")
            if tda is None or not np.isfinite(float(tda)) or float(tda) <= 0:
                continue
            err = abs(np.log(float(tda)) - np.log(usgs_da))
            if best_err is None or err < best_err:
                best_err = err
                best = row
        if best is not None:
            return best, "da_distance", float(best["_dist"])
    row = band.sort_values("_dist").iloc[0]
    return row, rule, float(row["_dist"])


def main() -> None:
    if not STATIONS_SHP.is_file():
        raise SystemExit(f"Missing stations: {STATIONS_SHP}")
    if not (TXTINOUT / "chandeg.con").is_file():
        raise SystemExit(f"Missing chandeg.con: {TXTINOUT}")

    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    if not huc12s:
        raise SystemExit(f"No HUC12 list for {HUC8}")

    chandeg = parse_chandeg(TXTINOUT)
    gis_to_chandeg = chandeg.set_index("gis_id")["chandeg_id"].to_dict()
    gis_to_area = chandeg.set_index("gis_id")["area_km2"].to_dict()
    gis_to_lcha = chandeg.set_index("gis_id")["lcha"].to_dict()

    upstream_adj: dict[int, list[int]] = {}
    for _, row in chandeg.iterrows():
        cid = int(row["chandeg_id"])
        if str(row.get("obj_typ", "")).lower() == "sdc":
            downstream = int(float(row["obj_id"]))
            upstream_adj.setdefault(downstream, []).append(cid)
    rtu_ha_by_ch = parse_rout_unit_areas(TXTINOUT)

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations["channel"] = pd.to_numeric(stations["channel"], errors="coerce")

    print("Loading original NHDPlus HR flowlines (HU4 GDB, domain-clipped by HUC12)...")
    nhd = load_nhd_flowlines_domain(huc12s)
    nhd_5070 = nhd.to_crs(ALBERS)

    rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        gis_ch = int(st["channel"]) if pd.notna(st["channel"]) else None
        chandeg_id = int(gis_to_chandeg[gis_ch]) if gis_ch in gis_to_chandeg else None
        txt_km2 = float(gis_to_area[gis_ch]) if gis_ch in gis_to_area else None
        lcha = int(gis_to_lcha[gis_ch]) if gis_ch in gis_to_lcha else None
        rtu_upstream_km2 = None
        if chandeg_id is not None:
            up_ids = upstream_chandeg_ids(chandeg_id, upstream_adj)
            rtu_upstream_km2 = sum(rtu_ha_by_ch.get(cid, 0.0) for cid in up_ids) / 100.0
        usgs_da, usgs_src = load_usgs_da_km2(site)
        gage_5070 = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        nhd_row, nhd_rule, nhd_dist = pick_nhd_reach(nhd_5070, gage_5070, usgs_da)
        nhd_km2 = float(nhd_row["TotDASqKm"]) if nhd_row is not None and pd.notna(nhd_row.get("TotDASqKm")) else None
        nhd_id = str(nhd_row["NHDPlusID"]) if nhd_row is not None else None

        def ratio(a, b):
            if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
                return None
            return a / b

        rows.append(
            {
                "site_no": site,
                "gis_channel": gis_ch,
                "chandeg_id": chandeg_id,
                "swat_lcha": lcha,
                "txtinout_chandeg_area_km2": round(txt_km2, 2) if txt_km2 is not None else None,
                "txtinout_rout_unit_upstream_km2": round(rtu_upstream_km2, 2)
                if rtu_upstream_km2 is not None
                else None,
                "nhd_totdasqkm_km2": round(nhd_km2, 2) if nhd_km2 is not None else None,
                "nhd_nhdplusid": nhd_id,
                "usgs_da_km2": round(usgs_da, 2) if usgs_da is not None else None,
                "usgs_da_source": usgs_src,
                "ratio_chandeg_nhd": round(ratio(txt_km2, nhd_km2), 4) if ratio(txt_km2, nhd_km2) else None,
                "ratio_chandeg_usgs": round(ratio(txt_km2, usgs_da), 4) if ratio(txt_km2, usgs_da) else None,
                "ratio_routup_nhd": round(ratio(rtu_upstream_km2, nhd_km2), 4)
                if ratio(rtu_upstream_km2, nhd_km2)
                else None,
                "ratio_nhd_usgs": round(ratio(nhd_km2, usgs_da), 4) if ratio(nhd_km2, usgs_da) else None,
                "nhd_pick_rule": nhd_rule,
                "nhd_pick_dist_m": round(nhd_dist, 1) if nhd_dist is not None else None,
                "station_match_rule": st.get("match_rule"),
            }
        )

    df = pd.DataFrame(rows)
    names = load_station_names()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def channel_label(row: pd.Series) -> str:
        gis = row.get("gis_channel")
        lcha = row.get("swat_lcha")
        if pd.isna(gis):
            return ""
        if pd.isna(lcha) or int(lcha) == int(gis):
            return str(int(gis))
        return f"{int(gis)} (lcha {int(lcha)})"

    table = pd.DataFrame(
        {
            "usgs_site_no": df["site_no"],
            "station_name": df["site_no"].map(lambda s: names.get(s, "")),
            "gis_channel": df["gis_channel"].astype("Int64"),
            "swat_lcha": df["swat_lcha"].astype("Int64"),
            "channel_label": df.apply(channel_label, axis=1),
            "swatplus_drainage_area_km2": df["txtinout_chandeg_area_km2"],
            "nhdplus_hr_totdasqkm_km2": df["nhd_totdasqkm_km2"],
            "nwis_drainage_area_km2": df["usgs_da_km2"],
        }
    ).sort_values("usgs_site_no")

    publish = table[
        [
            "usgs_site_no",
            "station_name",
            "gis_channel",
            "swat_lcha",
            "swatplus_drainage_area_km2",
            "nhdplus_hr_totdasqkm_km2",
            "nwis_drainage_area_km2",
        ]
    ]
    out_table = OUT_DIR / "peace-drainage-area-station-table.csv"
    publish.to_csv(out_table, index=False)

    out_csv = OUT_DIR / "peace-drainage-area-txtinout-vs-nhd.csv"
    df.to_csv(out_csv, index=False)

    md_path = OUT_DIR / "peace-drainage-area-station-table.md"
    md_lines = [
        "# Peace River HUC-8 (`03100101`) — drainage area comparison",
        "",
        "Model: `admin/0310/huc8/03100101` · SWAT+ area from `TxtInOut/chandeg.con` "
        "(ha÷100, row matched by **GIS channel** = `stations.shp` channel). "
        "NHD: original `NHDPLUS_H_0310_HU4_GDB` flowline `TotDASqKm` within 500 m of gage. "
        "NWIS: `meta_0310.csv` `drainage_area_sqkm`.",
        "",
        f"**{len(publish)}** stations · **{publish['swatplus_drainage_area_km2'].notna().sum()}** with SWAT+ area · "
        f"**{publish['nhdplus_hr_totdasqkm_km2'].notna().sum()}** with NHD · "
        f"**{publish['nwis_drainage_area_km2'].notna().sum()}** with NWIS metadata.",
        "",
        "| USGS site | Station name | GIS channel | SWAT lcha | SWAT+ DA (km²) | NHD HR DA (km²) | NWIS DA (km²) |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, r in publish.iterrows():
        def cell(v):
            if pd.isna(v) or v == "":
                return "—"
            if isinstance(v, (int, np.integer)):
                return str(int(v))
            if isinstance(v, float):
                return f"{v:.2f}"
            return str(v)

        md_lines.append(
            "| "
            + " | ".join(
                [
                    cell(r["usgs_site_no"]),
                    (cell(r["station_name"])[:48] + "…")
                    if isinstance(r["station_name"], str) and len(str(r["station_name"])) > 48
                    else cell(r["station_name"]),
                    cell(r["gis_channel"]),
                    cell(r["swat_lcha"]),
                    cell(r["swatplus_drainage_area_km2"]),
                    cell(r["nhdplus_hr_totdasqkm_km2"]),
                    cell(r["nwis_drainage_area_km2"]),
                ]
            )
            + " |"
        )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Summary stats where all three exist
    triple = df.dropna(subset=["txtinout_chandeg_area_km2", "nhd_totdasqkm_km2", "usgs_da_km2"])
    dual_txt_nhd = df.dropna(subset=["txtinout_chandeg_area_km2", "nhd_totdasqkm_km2"])

    def summarize(sub: pd.DataFrame, col: str, txt_col: str = "txtinout_chandeg_area_km2", ref: str = "nhd_totdasqkm_km2") -> dict:
        r = sub[col].astype(float)
        log_err = np.log(sub[txt_col].astype(float)) - np.log(sub[ref].astype(float))
        return {
            "n": len(sub),
            "median_ratio": float(r.median()),
            "p10_ratio": float(r.quantile(0.1)),
            "p90_ratio": float(r.quantile(0.9)),
            "median_abs_log_err": float(np.abs(log_err).median()),
        }

    print(f"\nPeace River HUC8 ({HUC8}): {len(df)} gages with channel assignment")
    print(
        f"TxtInOut source: {TXTINOUT / 'chandeg.con'} area (ha→km²) by GIS channel id; "
        f"optional check: sum {TXTINOUT.name}/rout_unit.con upstream of chandeg id"
    )
    outlet = chandeg.loc[chandeg["chandeg_id"] == 1, "area_km2"]
    outlet_km2 = float(outlet.iloc[0]) if len(outlet) else float("nan")
    hru_sum = sum(parse_rout_unit_areas(TXTINOUT).values()) / 100.0
    print(f"Whole-domain check: chandeg id=1 area={outlet_km2:.1f} km²; sum rout_unit={hru_sum:.1f} km²")
    print(f"NHD source: original HU4 GDB zip, NHDFlowline + NHDPlusFlowlineVAA.TotDASqKm")
    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_table}")
    print(f"Wrote: {md_path}\n")

    if len(dual_txt_nhd):
        s = summarize(dual_txt_nhd, "ratio_chandeg_nhd")
        print("chandeg.con / NHD TotDASqKm (all gages with both):")
        print(f"  n={s['n']}  median ratio={s['median_ratio']:.3f}  P10–P90={s['p10_ratio']:.3f}–{s['p90_ratio']:.3f}")
        print(f"  median |log(TxtInOut/NHD)|={s['median_abs_log_err']:.3f}")
    if len(triple):
        s = summarize(triple, "ratio_chandeg_usgs", ref="usgs_da_km2")
        print("\nchandeg.con / USGS DA (gages with USGS metadata):")
        print(f"  n={s['n']}  median ratio={s['median_ratio']:.3f}  P10–P90={s['p10_ratio']:.3f}–{s['p90_ratio']:.3f}")
        s2 = summarize(triple, "ratio_nhd_usgs")
        print("\nNHD TotDASqKm / USGS DA:")
        print(f"  n={s2['n']}  median ratio={s2['median_ratio']:.3f}  P10–P90={s2['p10_ratio']:.3f}–{s2['p90_ratio']:.3f}")

    # Worst |log| txt vs nhd
    dual = dual_txt_nhd.copy()
    dual["abs_log_err"] = np.abs(
        np.log(dual["txtinout_chandeg_area_km2"].astype(float))
        - np.log(dual["nhd_totdasqkm_km2"].astype(float))
    )
    print("\nLargest |log(chandeg/NHD)| (top 8):")
    for _, r in dual.nlargest(8, "abs_log_err").iterrows():
        print(
            f"  {r['site_no']} gis={int(r['gis_channel'])}  "
            f"chandeg={r['txtinout_chandeg_area_km2']:.1f}  NHD={r['nhd_totdasqkm_km2']:.1f}  "
            f"USGS={r['usgs_da_km2'] or '—'}  ratio={r['ratio_chandeg_nhd']:.3f}"
        )

    print("\nBest |log(chandeg/NHD)| (top 5 among ratio 0.5–2.0):")
    good = dual[(dual["ratio_chandeg_nhd"] >= 0.5) & (dual["ratio_chandeg_nhd"] <= 2.0)].nsmallest(5, "abs_log_err")
    for _, r in good.iterrows():
        print(
            f"  {r['site_no']}  chandeg={r['txtinout_chandeg_area_km2']:.1f}  NHD={r['nhd_totdasqkm_km2']:.1f}  "
            f"ratio={r['ratio_chandeg_nhd']:.3f}"
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare gage drainage area across delineation methods for ONE watershed:
NWIS reported (ground truth) vs each SWAT+ model's executable channel area (chandeg.con),
for any set of sibling models (e.g. NHDPlus-HR vs TauDEM) in the same site directory.

Gage->channel assignment is GEOMETRIC and identical across models (nearest channel within
SNAP_TOL_M, tie-break highest strmOrder then distance, never reads NWIS area), so the
comparison is fair and non-circular and does NOT depend on the shared streamflow_data.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from compare_peace_drainage_area_txtinout_vs_nhd import parse_chandeg  # noqa: E402
from streamflow_drainage_area import load_station_nwis_da_km2  # noqa: E402
from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402

ALBERS = "EPSG:5070"
SNAP_TOL_M = 500.0


def geometric_assign(gages_5070, rivs_5070):
    """For each gage, pick nearest channel within SNAP_TOL_M; tie-break highest strmOrder,
    then nearest. Returns dict site_no -> (Channel, areac_km2, snap_dist_m, strmOrder)."""
    out = {}
    has_ord = "strmOrder" in rivs_5070.columns
    for _, g in gages_5070.iterrows():
        d = rivs_5070.geometry.distance(g.geometry)
        band = rivs_5070[d <= SNAP_TOL_M].copy()
        band["_d"] = d[d <= SNAP_TOL_M]
        if band.empty:
            i = d.idxmin()
            row = rivs_5070.loc[i]
            out[g.site_no] = (int(row["Channel"]), float(row["AreaC"]) / 100.0, float(d.loc[i]),
                              int(row["strmOrder"]) if has_ord else None)
            continue
        if has_ord:
            band = band.sort_values(["strmOrder", "_d"], ascending=[False, True])
        else:
            band = band.sort_values("_d")
        row = band.iloc[0]
        out[g.site_no] = (int(row["Channel"]), float(row["AreaC"]) / 100.0, float(row["_d"]),
                          int(row["strmOrder"]) if has_ord else None)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site-dir", required=True)
    p.add_argument("--vpuid", required=True)
    p.add_argument("--models", required=True,
                   help="comma list of label:MODEL_NAME, e.g. NHD:SWAT_MODEL_Web_Application,TauDEM:SWAT_MODEL_TauDEM_auto")
    args = p.parse_args()
    site = Path(args.site_dir)
    models = [(s.split(":")[0], s.split(":")[1]) for s in args.models.split(",")]

    # gage points (geometry only — model-independent) from any model's streamflow_data
    # (per-MODEL_NAME), falling back to the legacy site-level dir.
    _stn = site / models[0][1] / "streamflow_data" / "stations.shp"
    if not _stn.is_file():
        _stn = site / "streamflow_data" / "stations.shp"
    gages = gpd.read_file(_stn)[["site_no", "geometry"]]
    gages["site_no"] = gages["site_no"].astype(str).str.zfill(8)
    gages_5070 = gages.to_crs(ALBERS)

    meta_csv = Path(SWATGenXPaths.streamflow_vpuid_path) / args.vpuid / f"meta_{args.vpuid}.csv"

    rows = []
    per_model = {}
    for label, mname in models:
        rivs = gpd.read_file(site / mname / "Watershed" / "Shapes" / "rivs1.shp").to_crs(ALBERS)
        chandeg = parse_chandeg(site / mname / "Scenarios" / "Default" / "TxtInOut")
        gis_area = chandeg.set_index("gis_id")["area_km2"].to_dict()
        per_model[label] = (geometric_assign(gages_5070, rivs), gis_area)

    for _, g in gages.iterrows():
        s = g.site_no
        nwis, src = load_station_nwis_da_km2(s, meta_csv)  # real NWIS only; None if missing
        rec = {"site_no": s, "nwis_km2": round(nwis, 2) if nwis else None, "nwis_src": src}
        for label, mname in models:
            assign, gis_area = per_model[label]
            ch, areac, dist, order = assign[s]
            swat = gis_area.get(ch, areac)  # chandeg area for that gis channel
            rec[f"{label}_ch"] = ch
            rec[f"{label}_km2"] = round(swat, 2)
            rec[f"{label}/NWIS"] = round(swat / nwis, 3) if nwis else None
            rec[f"{label}_snap_m"] = round(dist, 0)
        rows.append(rec)

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\nNWIS source meta:", meta_csv)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Collect Phase B TauDEM variant metrics into one table.

For each SWAT_MODEL_pb_* variant under the Oklawaha S site (plus the NHDPlus-HR reference),
read build_timing.json + delineation shape counts (subbasins / LSUs / channels) and total
subbasin area (km^2), and print a comparison table vs the NHDPlus-HR reference.
"""
from __future__ import annotations

import json
import os
import sys

SITE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0308/huc12/030801020804"
WBD_TRUTH_KM2 = 53.37  # Oklawaha S basin area (WBD)
REF_NAME = "SWAT_MODEL_Web_Application"  # NHDPlus-HR reference


def _count(shp):
    try:
        import geopandas as gpd
        return len(gpd.read_file(shp))
    except Exception:
        return None


def _area_km2(shp):
    try:
        import geopandas as gpd
        g = gpd.read_file(shp)
        return round(float(g.geometry.area.sum()) / 1.0e6, 2)
    except Exception:
        return None


def metrics(model_dir):
    sh = os.path.join(model_dir, "Watershed", "Shapes")
    out = {
        "subs": _count(os.path.join(sh, "subs1.shp")),
        "lsus": _count(os.path.join(sh, "lsus1.shp")),
        "rivs": _count(os.path.join(sh, "rivs1.shp")),
        "area_km2": _area_km2(os.path.join(sh, "subs1.shp")),
    }
    bt = os.path.join(model_dir, "build_timing.json")
    if os.path.isfile(bt):
        with open(bt) as fh:
            t = json.load(fh)
        out["built"] = t.get("built")
        out["sec"] = t.get("total_build_seconds")
        out["dem_m"] = t.get("dem_resolution")
        out["stream"] = t.get("stream_threshold_cells")
        out["channel"] = t.get("channel_threshold_cells")
        out["burn"] = t.get("burn_flowline_types") or ("full" if t.get("burn_streams") else "none")
        out["lakes"] = (f">={t.get('lake_min_area_km2')}km2" if t.get("use_lakes") else "none")
    return out


def main():
    variants = sorted(
        d for d in os.listdir(SITE)
        if d.startswith("SWAT_MODEL_pb_") and os.path.isdir(os.path.join(SITE, d))
    )
    rows = []
    ref = metrics(os.path.join(SITE, REF_NAME))
    rows.append(("NHDPlus-HR(ref)", ref))
    for v in variants:
        rows.append((v.replace("SWAT_MODEL_", ""), metrics(os.path.join(SITE, v))))

    hdr = f"{'variant':<20}{'dem':>4}{'strm':>7}{'chan':>6}{'burn':>14}{'lakes':>10}{'subs':>6}{'lsus':>6}{'rivs':>6}{'area_km2':>10}{'sec':>7}{'built':>7}"
    print(hdr)
    print("-" * len(hdr))
    for name, m in rows:
        print(f"{name:<20}{str(m.get('dem_m','')):>4}{str(m.get('stream','')):>7}{str(m.get('channel','')):>6}"
              f"{str(m.get('burn','')):>14}{str(m.get('lakes','')):>10}{str(m.get('subs','')):>6}{str(m.get('lsus','')):>6}"
              f"{str(m.get('rivs','')):>6}{str(m.get('area_km2','')):>10}{str(m.get('sec','')):>7}{str(m.get('built','')):>7}")
    print(f"\nReference NHDPlus-HR: subs/lsus/rivs above; WBD basin truth = {WBD_TRUTH_KM2} km^2")


if __name__ == "__main__":
    sys.exit(main())

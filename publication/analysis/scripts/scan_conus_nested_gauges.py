#!/usr/bin/env python3
"""Scan CONUS for USGS outlets whose SWAT+ model would contain MANY usable nested gauges.

When SWATGenX builds a model for an outlet station, the calibration gauges are the USGS stations
inside the outlet's upstream basin. That basin (HUC12 list) and each station's data quality are
already precomputed in the per-VPUID meta files — so we can predict the calibration-gauge count for
every station in the US *without building a single model*:

  nested_usable(X) = | { Y usable : Y.first_huc in X.list_of_huc12s, Y != X } |

This lets us purpose-pick multi-gauge basins (e.g. 8-20 nested gauges at buildable size) for the
MMPSO-vs-single head-to-heads instead of hunting through accidental admin models.

Read-only. No deps beyond stdlib. Output: ranked CSV + console top list.

Validation (2026-06-14): the count is an UPPER BOUND on gauges that actually score in calibration.
Checked vs known models: 14161500 predicted 3 (basin=1 HUC12, a co-located cluster) but only 1 scored;
14015000 predicted 7 (basin=4) but 3 scored. Build-time attrition (LSU spatial-join, v3 channel
assignment, NWIS overlap in the cal window) realizes roughly 45-65%. Filter to basin_huc12s >= ~2x
nested (gauges spread along the network, not a single-HUC12 cluster) for reliable candidates — those
realize the most. So a predicted-18 well-spread basin should yield ~10-14 actually-scored gauges.
"""
import ast
import csv
import glob
import os

META_DIR = "/data/SWATGenXApp/GenXAppData/USGS/streamflow_stations/VPUID"
OUT = "/data/SWATGenXApp/codes/publication/analysis/qa/conus_nested_gauges.csv"

# "usable data" = will actually score in calibration: not blacklisted, complete-ish record, low gaps.
MIN_DAYS = 1825      # >= ~5 years of daily values
MAX_GAP_PCT = 20.0


def _num(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def load_vpuid(path):
    """Return list of station dicts for one VPUID meta file."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            site = str(r.get("site_no") or "").strip()
            if not site:
                continue
            try:
                hucs = ast.literal_eval(r.get("list_of_huc12s") or "[]")
                hucs = [str(h) for h in hucs] if isinstance(hucs, (list, tuple)) else []
            except (ValueError, SyntaxError):
                hucs = []
            blacklisted = str(r.get("blacklisted") or "").strip().lower() in ("true", "1")
            usable = (
                not blacklisted
                and _num(r.get("number_of_streamflow_data")) >= MIN_DAYS
                and _num(r.get("GAP_percent"), 100.0) <= MAX_GAP_PCT
            )
            rows.append({
                "site_no": site,
                "first_huc": str(r.get("first_huc") or "").strip(),
                "huc_list": set(hucs),
                "n_huc12": len(hucs),
                "drainage_km2": _num(r.get("drainage_area_sqkm")),
                "usable": usable,
            })
    return rows


def main():
    candidates = []
    vpuids = sorted(d for d in os.listdir(META_DIR) if os.path.isdir(os.path.join(META_DIR, d)))
    for vp in vpuids:
        metas = glob.glob(os.path.join(META_DIR, vp, "meta_*.csv"))
        if not metas:
            continue
        stations = load_vpuid(metas[0])
        usable = [s for s in stations if s["usable"]]
        if len(usable) < 2:
            continue
        # location-HUC12 -> usable stations there (a gauge counts as nested if its first_huc is in
        # the outlet's basin HUC12 set).
        by_loc = {}
        for s in usable:
            by_loc.setdefault(s["first_huc"], []).append(s["site_no"])
        for x in usable:
            nested = set()
            for h in x["huc_list"]:
                for sn in by_loc.get(h, ()):  # usable stations located in HUC12 h
                    nested.add(sn)
            nested.discard(x["site_no"])
            if len(nested) >= 4:  # keep multi-gauge outlets only
                candidates.append({
                    "site_no": x["site_no"], "vpuid": vp,
                    "nested_usable_gauges": len(nested),
                    "basin_huc12s": x["n_huc12"],
                    "drainage_km2": round(x["drainage_km2"], 1),
                })

    candidates.sort(key=lambda c: (-c["nested_usable_gauges"], c["drainage_km2"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["site_no", "vpuid", "nested_usable_gauges", "basin_huc12s", "drainage_km2"])
        w.writeheader()
        w.writerows(candidates)

    print(f"wrote {OUT} ({len(candidates)} multi-gauge outlets, nested>=4)")
    print("\n=== top 25 by nested usable gauges ===")
    print(f"{'site_no':>12} {'vpuid':>5} {'nested':>6} {'huc12s':>6} {'drainage_km2':>12}")
    for c in candidates[:25]:
        print(f"{c['site_no']:>12} {c['vpuid']:>5} {c['nested_usable_gauges']:>6} {c['basin_huc12s']:>6} {c['drainage_km2']:>12.0f}")
    # a "buildable sweet spot" view: medium basins, 8-20 nested gauges
    print("\n=== sweet spot: 8-20 nested gauges, basin <= 120 HUC12s (buildable, multi-gauge) ===")
    sweet = [c for c in candidates if 8 <= c["nested_usable_gauges"] <= 20 and c["basin_huc12s"] <= 120]
    sweet.sort(key=lambda c: (c["basin_huc12s"],))
    for c in sweet[:20]:
        print(f"{c['site_no']:>12} {c['vpuid']:>5} {c['nested_usable_gauges']:>6} {c['basin_huc12s']:>6} {c['drainage_km2']:>12.0f}")


if __name__ == "__main__":
    main()

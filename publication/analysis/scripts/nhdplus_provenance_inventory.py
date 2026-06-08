#!/usr/bin/env python3
"""CONUS-scale provenance/version inventory of the local NHDPlus HR source data.

For every HU4 geodatabase zip under <NHDPlusHR>/zipped/, record the version/vintage
and source-resolution provenance that NHDPlus HR carries in its own tables, so the
dataset can be version-controlled and updated precisely when USGS republishes a VPU:

  - VPU id + vintage date parsed from the zip filename (USGS publication date),
  - WBDHU4 loaddate / states / name / area,
  - reach count and reach density (reaches per km^2) as a resolution proxy,
  - the distribution of NHDSourceCitation.SourceScaleDenominator (the in-data field
    that records the source map scale, e.g. 24000 = 1:24,000), which varies by VPU
    because each state steward supplies hydrography at different source scales.

Reach COUNT is read cheaply via OGR GetFeatureCount; total reach length (a more
precise density) is computed only when --with-length is given (slower: iterates).

Outputs a CSV + JSON under publication/analysis/qa/nhdplus-provenance/.

Usage:
  python nhdplus_provenance_inventory.py [--with-length] [--only 0310,0308,0712]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import fiona

ZIPPED = Path("/data/SWATGenXApp/GenXAppData/NHDPlusHR/zipped")
OUTDIR = Path("/data/SWATGenXApp/codes/publication/analysis/qa/nhdplus-provenance")
FNAME_RE = re.compile(r"NHDPLUS_H_(\d{4})_HU4_?(\d{8})?_GDB\.zip", re.IGNORECASE)
# flowline-relevant source scales; tiny denominators (1,3,15,...) are GNIS/point
# sentinels, not map scales, so we report them separately under "other".
MIN_REAL_SCALE = 1000


def ci(props, key):
    kl = key.lower()
    for k, v in props.items():
        if k.lower() == kl:
            return v
    return None


def inventory_one(zip_path: Path, with_length: bool) -> dict | None:
    m = FNAME_RE.match(zip_path.name)
    if not m:
        return None
    vpu, vintage = m.group(1), m.group(2)
    gdb = zip_path.name[:-4] + ".gdb"
    base = f"/vsizip/{zip_path}/{gdb}"
    rec = {
        "vpu": vpu,
        "vintage_filename": vintage,           # USGS publication date (YYYYMMDD) or None
        "vintage_in_filename": bool(vintage),   # flags our naming gaps for version control
        "zip": zip_path.name,
    }
    # WBDHU4: area / states / name / loaddate
    with fiona.open(base, layer="WBDHU4") as w:
        p = next(iter(w))["properties"]
        area = ci(p, "areasqkm")
        rec.update(states=ci(p, "states"), name=ci(p, "name"),
                   area_km2=round(area, 1) if area else None,
                   wbd_loaddate=str(ci(p, "loaddate")) if ci(p, "loaddate") else None,
                   wbd_metasourceid=ci(p, "metasourceid"))
    # reach count (cheap) + optional total length
    with fiona.open(base, layer="NHDFlowline") as fl:
        rec["reach_count"] = len(fl)
        if with_length:
            tot = 0.0
            for feat in fl:
                tot += ci(feat["properties"], "LengthKM") or 0.0
            rec["total_len_km"] = round(tot, 1)
            rec["density_km_per_km2"] = round(tot / area, 3) if area else None
    rec["reaches_per_km2"] = round(rec["reach_count"] / area, 3) if area else None
    # source scale distribution
    real, other = Counter(), Counter()
    with fiona.open(base, layer="NHDSourceCitation") as sc:
        for feat in sc:
            d = ci(feat["properties"], "SourceScaleDenominator")
            if d in (None, 0, -1):
                continue
            (real if d >= MIN_REAL_SCALE else other)[int(d)] += 1
    rec["source_scales"] = dict(sorted(real.items()))
    rec["source_scales_finest"] = min(real) if real else None
    rec["source_scales_sub1000"] = dict(sorted(other.items()))
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--with-length", action="store_true",
                    help="also compute total reach length / density (slower)")
    ap.add_argument("--only", default=None, help="comma-separated VPUs to scan")
    args = ap.parse_args(argv)

    only = set(args.only.split(",")) if args.only else None
    zips = sorted(ZIPPED.glob("NHDPLUS_H_*_HU4*_GDB.zip"))
    OUTDIR.mkdir(parents=True, exist_ok=True)

    records, errors = [], []
    for z in zips:
        m = FNAME_RE.match(z.name)
        if not m or (only and m.group(1) not in only):
            continue
        try:
            rec = inventory_one(z, args.with_length)
            if rec:
                records.append(rec)
                print(f"VPU {rec['vpu']} {rec['states']}: vintage={rec['vintage_filename']} "
                      f"reaches={rec['reach_count']:,} ({rec['reaches_per_km2']}/km2) "
                      f"scales={rec['source_scales']} finest=1:{rec['source_scales_finest']}",
                      flush=True)
        except Exception as e:  # noqa
            errors.append({"zip": z.name, "error": str(e)})
            print(f"ERR {z.name}: {e}", file=sys.stderr, flush=True)

    records.sort(key=lambda r: r["vpu"])
    summary = {
        "n_vpu_local": len(records),
        "n_missing_filename_vintage": sum(1 for r in records if not r["vintage_in_filename"]),
        "vintages_present": sorted({r["vintage_filename"] for r in records if r["vintage_filename"]}),
        "finest_source_scale_overall": min((r["source_scales_finest"] for r in records
                                            if r["source_scales_finest"]), default=None),
    }
    (OUTDIR / "nhdplus_hr_inventory.json").write_text(
        json.dumps({"summary": summary, "records": records, "errors": errors}, indent=2))
    # CSV
    cols = ["vpu", "states", "name", "vintage_filename", "vintage_in_filename",
            "wbd_loaddate", "area_km2", "reach_count", "reaches_per_km2",
            "total_len_km", "density_km_per_km2", "source_scales_finest", "source_scales"]
    lines = [",".join(cols)]
    for r in records:
        row = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, dict):
                v = "|".join(f"{k}:{n}" for k, n in v.items())
            row.append(f"\"{v}\"" if ("," in str(v)) else str(v))
        lines.append(",".join(row))
    (OUTDIR / "nhdplus_hr_inventory.csv").write_text("\n".join(lines) + "\n")

    print(f"\n=== SUMMARY ===\n{json.dumps(summary, indent=2)}")
    print(f"wrote {OUTDIR}/nhdplus_hr_inventory.{{json,csv}}  ({len(records)} VPUs, {len(errors)} errors)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

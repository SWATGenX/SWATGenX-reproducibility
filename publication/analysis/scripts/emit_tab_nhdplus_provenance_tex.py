#!/usr/bin/env python3
"""Emit the per-model NHDPlus HR provenance supplementary table (LaTeX + CSV).

Reads provenance.json from each catalog model directory (written by
SWATGenX.model_provenance) and renders a compact table of per-model hydrography
resolution/vintage, for the manuscript supplement (label tab:nhdplus-provenance).

Output:
  publication/tables/generated/tab-nhdplus-provenance.tex
  publication/tables/generated/tab-nhdplus-provenance.csv
"""
from __future__ import annotations

import json
import os

BASE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID"
OUT_TEX = "/data/SWATGenXApp/codes/publication/tables/generated/tab-nhdplus-provenance.tex"
OUT_CSV = "/data/SWATGenXApp/codes/publication/tables/generated/tab-nhdplus-provenance.csv"

# (tier label, workspace model id)---the eight catalog Model IDs.
ROSTER = [
    ("S---Oklawaha", "0308/huc12/030801020804"),
    ("M---Upper San Pedro", "1505/huc12/09471300"),
    ("L---Peace River", "0310/huc8/03100101"),
    ("X20---Little Kanawha", "0503/huc12/03152000"),
    ("X40---Verdigris", "1107/huc12/07174000"),
    ("X60---Upper Gila", "1506/huc8/15060105"),
    ("Cal---Florida basin", "0310/huc12/02297600"),
    ("Cal---Illinois basin", "0712/huc12/05536265"),
]


def vintage_str(h: dict) -> str:
    v = h.get("vpu_publication_vintage")
    if v and len(v) >= 7:
        return v[:7]                         # USGS publication date YYYY-MM (from gdb CreaDate)
    if v and len(v) == 8:
        return f"{v[:4]}-{v[4:6]}"
    return "n/a"


def main() -> int:
    rows = []
    for label, mid in ROSTER:
        pj = os.path.join(BASE, mid, "SWAT_MODEL_Web_Application", "provenance.json")
        d = json.load(open(pj))
        h = d["data_sources"]["hydrography"]
        sc = h.get("finest_source_scale_denominator")
        rows.append({
            "label": label,
            "vpu": h.get("vpuid"),
            "states": h.get("states") or "",
            "vintage": vintage_str(h),
            "finest": f"1:{sc:,}" if sc else "n/a",
            "density": h.get("vpu_reaches_per_km2"),
            "delin": "NHDPlus HR" if d["delineation"]["method"] in ("existing", "nhd") else d["delineation"]["method"],
        })

    # LaTeX tabular
    L = [r"\begin{tabular}{@{}p{3.1cm}p{1.0cm}p{2.0cm}p{1.7cm}p{1.6cm}p{1.7cm}@{}}",
         r"\toprule",
         r"Model (tier) & VPU & States & NHDPlus vintage & Finest source scale & Reach density (km\textsuperscript{-2}) \\",
         r"\midrule"]
    for r in rows:
        L.append(f"{r['label']} & \\texttt{{{r['vpu']}}} & {r['states']} & {r['vintage']} & "
                 f"{r['finest']} & {r['density']} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    os.makedirs(os.path.dirname(OUT_TEX), exist_ok=True)
    open(OUT_TEX, "w").write("\n".join(L) + "\n")

    # CSV
    cols = ["label", "vpu", "states", "vintage", "finest", "density", "delin"]
    csv = [",".join(cols)]
    for r in rows:
        csv.append(",".join(f"\"{r[c]}\"" if "," in str(r[c]) else str(r[c]) for c in cols))
    open(OUT_CSV, "w").write("\n".join(csv) + "\n")
    print(f"wrote {OUT_TEX} and {OUT_CSV} ({len(rows)} models)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

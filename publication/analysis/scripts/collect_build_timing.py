#!/usr/bin/env python3
"""Collect model creation wall-clocks for the NHD-vs-TauDEM build-time comparison on Peace.

Reads each model's build_timing.json (written by run_taudem_variant_model.py) and recovers the
QSWAT+ per-stage breakdown (runTauDEM / finishDelineation / HRU phase / total delineation) from
the matching run log, then reports a side-by-side table and writes a JSON for the website/paper.

Run AFTER run_peace_timed_builds.sh finishes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SITE = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101")
OUT = Path("/data/SWATGenXApp/codes/publication/analysis/qa/taudem-vs-nhd/peace_build_timing.json")

# model dir -> run log
MODELS = [
    ("SWAT_MODEL_NHD_timed", "/tmp/peace_timed_nhd.log"),
    ("SWAT_MODEL_TauDEM_split_s5000c1000_clip", "/tmp/peace_timed_taudem_s5000c1000.log"),
    ("SWAT_MODEL_TauDEM_split_s2500c500_clip", "/tmp/peace_timed_taudem_s2500c500.log"),
    ("SWAT_MODEL_TauDEM_split_s1250c250_clip", "/tmp/peace_timed_taudem_s1250c250.log"),
]

STAGE_PATTERNS = {
    "tauDEMSeconds": re.compile(r"runTauDEM finished in\s+(.+)$"),
    "finishDelineationSeconds": re.compile(r"finishDelineation finished in\s+(.+)$"),
    "delineationSeconds": re.compile(r"QSWAT\+ delineation \(.*?\) finished in\s+(.+)$"),
    "hruSeconds": re.compile(r"HRU phase finished in\s+(.+)$"),
}


def _parse_elapsed(text: str) -> float | None:
    """'12m 30s' / '1h 02m 03s' / '45.0s' -> seconds."""
    text = text.strip()
    h = re.search(r"(\d+)\s*h", text)
    m = re.search(r"(\d+)\s*m", text)
    s = re.search(r"([\d.]+)\s*s", text)
    if not (h or m or s):
        return None
    return (int(h.group(1)) * 3600 if h else 0) + (int(m.group(1)) * 60 if m else 0) + (float(s.group(1)) if s else 0)


def _stages_from_log(log_path: str) -> dict:
    p = Path(log_path)
    if not p.is_file():
        return {}
    txt = p.read_text(errors="ignore")
    out = {}
    for key, pat in STAGE_PATTERNS.items():
        last = None
        for mm in pat.finditer(txt):
            last = mm.group(1)
        if last:
            out[key] = round(_parse_elapsed(last) or 0, 1)
    return out


def _count_rows(path: Path) -> int | None:
    if not path.is_file():
        return None
    return max(0, sum(1 for i, ln in enumerate(open(path, errors="ignore")) if i >= 2 and ln.strip()))


def main() -> None:
    rows = []
    for model_name, log in MODELS:
        base = SITE / model_name
        timing_p = base / "build_timing.json"
        rec = {"model": model_name, "log": log}
        if timing_p.is_file():
            rec.update(json.loads(timing_p.read_text()))
        else:
            rec["built"] = None
            rec["note"] = "build_timing.json not found (build may not have finished or failed)"
        rec["stages"] = _stages_from_log(log)
        txt = base / "Scenarios" / "Default" / "TxtInOut"
        rec["channels"] = _count_rows(txt / "chandeg.con")
        rec["hrus"] = _count_rows(txt / "hru-data.hru")
        rec["reservoirs"] = _count_rows(txt / "reservoir.con") or 0
        rec["lakesWired"] = (rec["reservoirs"] or 0) > 0
        rows.append(rec)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"basin": "Peace HUC8 03100101", "models": rows}, indent=2) + "\n")

    print(f"{'MODEL':<42} {'build_min':>9} {'taudem':>7} {'finDel':>7} {'HRU':>7} {'chan':>6} {'res':>4} {'lakes':>5}")
    for r in rows:
        st = r.get("stages", {})
        print(f"{r['model']:<42} "
              f"{(r.get('total_build_minutes') or 0):>9} "
              f"{(st.get('tauDEMSeconds') or 0)/60:>7.1f} "
              f"{(st.get('finishDelineationSeconds') or 0)/60:>7.1f} "
              f"{(st.get('hruSeconds') or 0)/60:>7.1f} "
              f"{str(r.get('channels')):>6} {str(r.get('reservoirs')):>4} "
              f"{'yes' if r.get('lakesWired') else 'no':>5}")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

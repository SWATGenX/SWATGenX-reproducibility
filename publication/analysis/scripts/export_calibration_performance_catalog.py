#!/usr/bin/env python3
"""Calibration Performance Evaluation — assemble the per-model dataset and the deep-dive page catalog.

For every calibrated admin model, joins the calibration RESULT (cal/val NSE, PSO convergence, cost)
with the gage→channel DELINEATION-QUALITY predictors (assignment_class, swat/nhd DA ratio, DA error,
gage-to-reach distance_m, basin wetness, model size, delineation source). The central question of the
study is whether achievable NSE is governed by delineation quality + basin hydrology rather than
calibration effort.

Outputs:
  - publication/analysis/qa/calibration_performance_eval.csv         (tidy, one row per model — the paper table)
  - web_application/frontend/src/data/swatPlusCalibrationPerformanceCatalog.json   (deep-dive page data)

Run as www-data (reads www-data-owned model dirs):
  sudo -n -u www-data /data/SWATGenXApp/codes/.venv/bin/python \
      publication/analysis/scripts/export_calibration_performance_catalog.py
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
WEBAPP = REPO / "web_application"
sys.path.insert(0, str(WEBAPP))

MODEL = "SWAT_MODEL_Web_Application"
OUT_CSV = REPO / "publication/analysis/qa/calibration_performance_eval.csv"
OUT_JSON = WEBAPP / "frontend/src/data/swatPlusCalibrationPerformanceCatalog.json"
FAILURE_TAXONOMY = REPO / "publication/analysis/qa/calibration_failure_taxonomy.csv"


def _count_lines(path: str):
    try:
        with open(path) as f:
            return sum(1 for ln in f if ln.strip())
    except OSError:
        return None


def _assignment_row(sd: str, site: str):
    """(row, matched) for the target gage from stations_assignment_v3.csv. matched=False when the
    file is absent (legacy model) or the target site has no row."""
    f = os.path.join(sd, "stations_assignment_v3.csv")
    if not os.path.exists(f):
        return {}, False
    try:
        rows = list(csv.DictReader(open(f)))
    except OSError:
        return {}, False
    site8 = str(site).zfill(8)
    for r in rows:
        if str(r.get("site_no", "")).zfill(8) == site8:
            return r, True
    return {}, False


def _delineation_tier(has_v3, assignment_class, ratio, eligible, zero_flow):
    """Independent (predictor-side) tier for grouping. Ephemeral is a separate basin axis."""
    if zero_flow is not None and zero_flow >= 0.1:
        return "ephemeral_basin"
    if not has_v3:
        return "legacy_unassigned"
    cls = (assignment_class or "").lower()
    elig = str(eligible).lower() in ("true", "1", "yes")
    ratio_off = (ratio is not None and abs(ratio - 1.0) > 0.15)
    if ("clean" in cls) and elig and not ratio_off:
        return "clean_assigned"
    return "review_or_offset"


def _distance_m_from_readme(sd: str, site: str):
    """Parse the gage-to-reach distance_m from the streamflow_data/README.md markdown table."""
    f = os.path.join(sd, "README.md")
    if not os.path.exists(f):
        return None
    site8 = str(site).zfill(8)
    try:
        for ln in open(f):
            if "|" not in ln:
                continue
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if not cells:
                continue
            if str(cells[0]).zfill(8) == site8 or cells[0] == str(site):
                # header order: site_no, usgs_da_km2, ..., distance_m, mapping_method, ...
                for c in cells:
                    if re.fullmatch(r"\d+(\.\d+)?", c) and float(c) > 50:  # distance heuristic; refined below
                        pass
                # robust: find the column index by header
        # re-parse with header awareness
        lines = [l for l in open(f) if "|" in l]
        hdr = None
        for l in lines:
            cells = [c.strip().lower() for c in l.strip().strip("|").split("|")]
            if "site_no" in cells and "distance_m" in cells:
                hdr = cells
                break
        if hdr is None:
            return None
        di = hdr.index("distance_m")
        si = hdr.index("site_no")
        for l in lines:
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cells) <= max(di, si):
                continue
            if str(cells[si]).zfill(8) == site8 or cells[si] == str(site):
                try:
                    return float(cells[di])
                except ValueError:
                    return None
    except OSError:
        return None
    return None


def _wetness(sd: str, site: str):
    """Zero-flow fraction of the target gage's observed daily flow in 2016-2022 (-99 -> missing)."""
    import pandas as pd
    for f in glob.glob(os.path.join(sd, f"*_{site}.csv")):
        try:
            df = pd.read_csv(f, parse_dates=["date"])
            df["date"] = pd.to_datetime(df["date"])
            v = pd.to_numeric(df["streamflow"], errors="coerce").where(lambda x: x != -99)
            w = df[(df.date >= "2016-01-01") & (df.date <= "2022-12-31")]
            vv = v[w.index].dropna()
            if len(vv) == 0:
                return None
            return round(int((vv == 0).sum()) / len(vv), 3)
        except Exception:
            return None
    return None


def _delineation_source(root: str):
    p = os.path.join(root, MODEL, "provenance.json")
    try:
        d = json.load(open(p))
        for k in ("delineation_method", "delineation_source", "delineation"):
            if d.get(k):
                return str(d[k])
        if d.get("taudem") or d.get("force_taudem_only"):
            return "TauDEM"
        return "NHDPlus-HR"
    except Exception:
        return None


def _plateau(global_best):
    """First iteration index within 0.01 of the final (minimum) global-best objective; and the
    init->final improvement. global_best is the negated NSE-sum, minimized."""
    gb = [x for x in (global_best or []) if x is not None]
    if not gb:
        return None, None, None
    best = min(gb)
    plateau = next((i for i, v in enumerate(gb) if abs(v - best) <= 0.01), len(gb) - 1)
    return plateau, round(gb[0], 3), round(best, 3)


def main():
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.user_model_stats import scan_user_models_inventory, _model_overall_nse
        from app.calibration_artifacts import read_central_performance, resolve_global_best_convergence, read_settings_snapshot
        from app.calibration_runtime import estimate_calibration_wall_hours

        base = os.path.join(app.config["USER_PATH"], "admin", "SWATplus_by_VPUID")
        models = [m for m in scan_user_models_inventory(base) if m.get("calibrated")]

        rows = []
        for m in models:
            site, vp, lvl = m["site"], m["vpuid"], m["level"]
            root = os.path.join(base, vp, lvl, site)
            tio = os.path.join(root, MODEL, "Scenarios/Default/TxtInOut")
            sd = os.path.join(root, MODEL, "streamflow_data")

            cal_nse, val_nse = _model_overall_nse(root)
            perf = read_central_performance(root) or {}
            a, has_v3 = _assignment_row(sd, site)
            try:
                usgs_da = float(a.get("usgs_da_km2")) if a.get("usgs_da_km2") not in (None, "") else None
            except ValueError:
                usgs_da = None
            try:
                swat_da = float(a.get("swat_da_km2")) if a.get("swat_da_km2") not in (None, "") else None
            except ValueError:
                swat_da = None
            try:
                swat_nhd_ratio = float(a.get("swat_nhd_ratio")) if a.get("swat_nhd_ratio") not in (None, "") else None
            except ValueError:
                swat_nhd_ratio = None
            da_err = (round(100.0 * (swat_da - usgs_da) / usgs_da, 1)
                      if (usgs_da and swat_da and usgs_da > 0) else None)

            conv = resolve_global_best_convergence(root, "Default", MODEL) or {}
            gb_series = conv.get("global_best") or []
            actual_iters = len([x for x in gb_series if x is not None]) or None
            plateau, init_obj, final_obj = _plateau(gb_series)
            wet = _wetness(sd, site)
            tier = _delineation_tier(has_v3, a.get("assignment_class"), swat_nhd_ratio,
                                     a.get("calibration_eligible"), wet)
            snap = read_settings_snapshot(root, "Default") or {}
            hru = _count_lines(os.path.join(tio, "hru.con"))
            ch = _count_lines(os.path.join(tio, "chandeg.con"))
            iters = snap.get("max_iterations")
            pool = snap.get("cal_pool_size")
            est_hours = None
            try:
                if hru and ch:
                    est_hours = round(estimate_calibration_wall_hours(
                        hru, ch, cal_years=int(snap.get("cal_end_year", 2022)) - int(snap.get("cal_start_year", 2016)) + 1,
                        pool=int(pool or 16), iters=int(iters or 20), concurrent=16, val_runs=5, model_id=site), 2)
            except Exception:
                est_hours = None

            rows.append({
                "site": site, "vpuid": vp, "level": lvl,
                "cal_nse": cal_nse, "val_nse": val_nse,
                "tier": tier,
                "has_v3_assignment": has_v3,
                "assignment_class": a.get("assignment_class"),
                "calibration_eligible": a.get("calibration_eligible"),
                "mapping_method": a.get("mapping_method"),
                "swat_nhd_ratio": swat_nhd_ratio,
                "da_error_pct": da_err,
                "distance_m": _distance_m_from_readme(sd, site),
                "zero_flow_frac": wet,
                "hru": hru, "channels": ch,
                "delineation_source": _delineation_source(root),
                "pso_pool": pool, "pso_iters_requested": iters, "actual_iters": actual_iters,
                "plateau_iter": plateau, "init_objective": init_obj, "final_objective": final_obj,
                "est_wall_hours": est_hours,
                "convergence": gb_series or None,
            })

        # ---- paper CSV (drop the heavy convergence array) ----
        OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
        flat_cols = [k for k in rows[0].keys() if k != "convergence"] if rows else []
        with open(OUT_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=flat_cols)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k) for k in flat_cols})

        # ---- failure taxonomy ----
        failures = []
        if FAILURE_TAXONOMY.exists():
            failures = list(csv.DictReader(open(FAILURE_TAXONOMY)))

        # ---- tier-based summary (the headline result: delineation tier predicts calibratability) ----
        import statistics as _st
        TIER_ORDER = ["clean_assigned", "review_or_offset", "legacy_unassigned", "ephemeral_basin"]

        def _stat(vals):
            v = [x for x in vals if isinstance(x, (int, float))]
            if not v:
                return {"n": 0, "median_cal_nse": None, "min": None, "max": None}
            return {"n": len(v), "median_cal_nse": round(_st.median(v), 3),
                    "min": round(min(v), 3), "max": round(max(v), 3)}

        tier_summary = []
        for t in TIER_ORDER:
            grp = [r for r in rows if r["tier"] == t]
            cals = [r["cal_nse"] for r in grp]
            s = _stat(cals)
            s["tier"] = t
            s["good_rate"] = (round(sum(1 for c in cals if isinstance(c, (int, float)) and c >= 0.5)
                                    / max(1, s["n"]), 2) if s["n"] else None)
            tier_summary.append(s)
        print("\n=== TIER SUMMARY (median cal NSE | good-rate >=0.5) ===")
        for s in tier_summary:
            print(f"  {s['tier']:<18} n={s['n']:>2} median={s['median_cal_nse']} "
                  f"range=[{s['min']},{s['max']}] good_rate={s['good_rate']}")

        # ---- catalog JSON for the page ----
        scored = [r for r in rows if isinstance(r["cal_nse"], (int, float))]
        good = [r for r in scored if r["cal_nse"] >= 0.5]
        catalog = {
            "meta": {"models_calibrated": len(rows), "models_scored": len(scored),
                     "good_threshold": 0.5, "good_count": len(good)},
            "tier_summary": tier_summary,
            "models": [{k: r[k] for k in flat_cols} for r in rows],
            "convergence": {r["site"]: r["convergence"] for r in rows if r.get("convergence")},
            "failures": failures,
        }
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        json.dump(catalog, open(OUT_JSON, "w"), indent=2)
        print(f"[ok] wrote {OUT_CSV} ({len(rows)} models, {len(scored)} scored, {len(good)} >=0.5)")
        print(f"[ok] wrote {OUT_JSON}")


if __name__ == "__main__":
    main()

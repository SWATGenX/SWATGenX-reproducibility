#!/usr/bin/env python3
"""Peace HUC8 — initial (uncalibrated) SWAT+ sim vs observed across the calibration-usable gages,
NHDPlus-HR vs TauDEM+lakes, with per-gage channel cross-validation.

Narrative this serves: the small-model counterexample (Silver Springs) showed that when the
dominant driver is exogenous to the surface model, no delineation can reproduce the gage — so
station selection comes first. Here we (1) select usable gages: keep the calibration-ready
assignment classes and drop gages whose observed flow is tidal (negative/bidirectional) or
spring-dominated (very low coefficient of variation); then (2) for each model, print ALL channels,
cross-validate which channel best matches each gage (monthly timing correlation among channels
near the gage), and (3) report how many gages "align" (monthly r > 0.5) for each delineation.

Both models run uncalibrated over a 7-year window with a 2-year warmup (``--full``), or a short
test window (default) to validate the pipeline first.

Usage:
  # quick pipeline test (2022-2024, 1-yr warmup):
  python compare_peace_initial_sim_multistation.py --taudem-model SWAT_MODEL_TauDEM_split_s2500c500_clip
  # full comparison (2018-2024, 2-yr warmup):
  python compare_peace_initial_sim_multistation.py --full --taudem-model <working_taudem_model>
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

REPO = Path("/data/SWATGenXApp/codes")
sys.path.insert(0, str(REPO / "ModelProcessing"))
# ModelProcessing imports are done lazily inside the SWAT+-running functions: importing the
# package initializes a www-data-owned log file, which would break the read-only --select-only
# path when run as the vahid user.

SWATPLUS = REPO / "bin" / "swatplus"
SITE = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0310/huc8/03100101")
CATALOG = REPO / "web_application/frontend/src/data/stationAssignmentPageCatalog.json"
OUT = Path(os.environ.get("CMP_OUT_DIR", "/tmp/peace_multistation"))
CMS_PER_CFS = 1.0 / 35.3147
ALBERS = "EPSG:5070"

USABLE_CLASSES = {"tributary_clean", "mainstem_clean", "mainstem_known_nhd_offset"}
# Station-selection screens (the Silver Springs lesson): drop exogenous-driver gages.
MIN_OBS_COVERAGE = 0.90      # fraction of eval-window days with a valid observation
MIN_CV = 0.30                # below this the flow is too stable to be surface runoff (spring-fed)
ALIGN_MONTHLY_R = 0.50       # a gage "aligns" if its best channel tracks observed seasonality
SNAP_BUFFER_M = 750.0        # candidate channels within this distance of the gage point


def eval_window(full: bool):
    if full:
        return 2018, 2024, 2, "2020-01-01", "2024-12-31"   # 7 yr sim, 2 yr warmup
    return 2022, 2024, 1, "2023-01-01", "2024-12-31"        # short test


def station_classes() -> dict:
    """site_no -> assignment_class, from the station-assignment catalog."""
    d = json.loads(CATALOG.read_text())
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("stations"), list):
                for s in o["stations"]:
                    sid = str(s.get("siteNo") or s.get("usgsSiteNo") or s.get("site_no") or "").strip().zfill(8)
                    cl = s.get("assignmentClass") or s.get("assignment_class")
                    if sid and cl:
                        out[sid] = cl
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(d)
    return out


def observed_for(site: str, sf_dir: Path, ev_start: str, ev_end: str):
    """Return (obs_df[date,obs_cms], stats) for a gage, or (None, reason)."""
    cands = list(sf_dir.glob(f"*_{site}.csv"))
    if not cands:
        return None, "no_obs_csv"
    o = pd.read_csv(cands[0], parse_dates=["date"]).rename(columns={"streamflow": "cfs"})
    # -99 / -999 / -9999 are missing-data sentinels in these CSVs (not tidal flow); mask them.
    o["cfs"] = o["cfs"].where(o["cfs"] > -99)
    win = o[(o.date >= ev_start) & (o.date <= ev_end)].copy()
    n_days = (pd.Timestamp(ev_end) - pd.Timestamp(ev_start)).days + 1
    valid = win[win["cfs"].notna()]
    cov = len(valid) / max(n_days, 1)
    if valid.empty:
        return None, "no_obs_in_window"
    mean_cfs = float(valid["cfs"].mean())
    cv = float(valid["cfs"].std() / mean_cfs) if mean_cfs > 0 else -1.0
    win["obs_cms"] = win["cfs"] * CMS_PER_CFS
    return win[["date", "obs_cms"]], {"coverage": round(cov, 2), "mean_cfs": round(mean_cfs, 1), "cv": round(cv, 3)}


def select_usable_gages(nhd_model: str, ev_start: str, ev_end: str) -> pd.DataFrame:
    """Apply station selection: usable class + screen tidal/spring/coverage. Read-only."""
    classes = station_classes()
    sf = SITE / nhd_model / "streamflow_data"
    st = gpd.read_file(sf / "stations.shp")
    st["site_no"] = st["site_no"].astype(str).str.zfill(8)
    rows = []
    for _, r in st.iterrows():
        site = r["site_no"]
        cl = classes.get(site, "unknown")
        rec = {"site_no": site, "assignment_class": cl, "geometry": r.geometry,
               "assigned_channel": int(r["channel"]) if pd.notna(r.get("channel")) else None}
        if cl not in USABLE_CLASSES:
            rec["usable"] = False; rec["drop_reason"] = f"class:{cl}"
            rows.append(rec); continue
        obs, stats = observed_for(site, sf, ev_start, ev_end)
        if obs is None:
            rec["usable"] = False; rec["drop_reason"] = stats
            rows.append(rec); continue
        rec.update(stats)
        if stats["mean_cfs"] <= 0:
            rec["usable"] = False; rec["drop_reason"] = "tidal_or_negative_mean"
        elif stats["coverage"] < MIN_OBS_COVERAGE:
            rec["usable"] = False; rec["drop_reason"] = f"coverage<{MIN_OBS_COVERAGE}"
        elif stats["cv"] < MIN_CV:
            rec["usable"] = False; rec["drop_reason"] = f"spring_fed_cv<{MIN_CV}"
        else:
            rec["usable"] = True; rec["drop_reason"] = None
        rows.append(rec)
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=st.crs)


def run_all_channels(model: str, y0: int, y1: int, nyskip: int, ev_start: str, ev_end: str) -> pd.DataFrame:
    """Run model (default params), print ALL channels, return date/unit/flo_out over eval window."""
    from ModelProcessing.print_prt import update_time, nyskip_define, update_print_prt_file, set_output_format_flags
    from ModelProcessing.channel_sd_output import load_channel_sd_day

    src = SITE / model / "Scenarios" / "Default" / "TxtInOut"
    run = Path("/tmp") / f"peace_ms_{model}"
    if run.exists():
        shutil.rmtree(run)
    shutil.copytree(src, run)
    update_time(str(run), y0, y1)
    nyskip_define(str(run), nyskip)
    update_print_prt_file(str(run), daily_flow_printing=True, hru_printing=False,
                          basin_wb_printing=False, channel_sd_daily_only=True)
    set_output_format_flags(str(run), csvout=False, dbout=False, cdfout=True)
    (run / "print_filter.prt").unlink(missing_ok=True)
    for n in ("channel_sd_day.nc", "simulation.out"):
        p = run / n
        if p.exists():
            p.unlink()
    env = os.environ.copy(); env["SWATPLUS_NC_DEFLATE"] = "0"
    print(f"[{model}] running SWAT+ {y0}-{y1} (all channels) ...", flush=True)
    r = subprocess.run([str(SWATPLUS)], cwd=str(run), env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=4 * 3600)
    if not (run / "channel_sd_day.nc").is_file():
        raise RuntimeError(f"[{model}] no channel_sd_day.nc (exit {r.returncode}): {r.stderr[-300:]}")
    df = load_channel_sd_day(str(run), cha_path=str(run / "channel-lte.cha"))
    df["date"] = pd.to_datetime(df.yr.astype(str) + "-" + df.mon.astype(str).str.zfill(2) + "-" + df.day.astype(str).str.zfill(2))
    df = df[(df.date >= ev_start) & (df.date <= ev_end)][["date", "unit", "flo_out"]]
    print(f"[{model}] {df['unit'].nunique()} channels x {df['date'].nunique()} days", flush=True)
    shutil.rmtree(run)
    return df


def crossvalidate_model(model: str, usable: gpd.GeoDataFrame, df_all: pd.DataFrame,
                        nhd_model: str, ev_start: str, ev_end: str) -> list:
    """For each usable gage, pick the best channel near it (monthly r) and score alignment."""
    from ModelProcessing.channel_mapping import gis_channel_to_swat_unit_map_from_channel_lte

    cha = SITE / model / "Scenarios" / "Default" / "TxtInOut" / "channel-lte.cha"
    gmap = gis_channel_to_swat_unit_map_from_channel_lte(str(cha))
    riv = gpd.read_file(SITE / model / "Watershed" / "Shapes" / "rivs1.shp").to_crs(ALBERS)
    sf = SITE / nhd_model / "streamflow_data"
    gages_5070 = usable.to_crs(ALBERS)
    # pivot sim to date x unit once
    pivot = df_all.pivot_table(index="date", columns="unit", values="flo_out", aggfunc="mean")
    pivot_m = pivot.resample("MS").mean()
    results = []
    for _, g in gages_5070.iterrows():
        site = g["site_no"]
        obs, _ = observed_for(site, sf, ev_start, ev_end)
        if obs is None:
            continue
        obs_m = obs.set_index("date")["obs_cms"].resample("MS").mean()
        d = riv.geometry.distance(g.geometry)
        cand = riv[d <= SNAP_BUFFER_M]
        if cand.empty:
            cand = riv.iloc[[int(d.idxmin())]]
        best = None
        for _, ch in cand.iterrows():
            gis = int(ch["Channel"]); unit = gmap.get(gis)
            if unit is None or unit not in pivot_m.columns:
                continue
            sm = pivot_m[unit]
            j = pd.concat([obs_m, sm.rename("sim")], axis=1).dropna()
            if len(j) < 6 or j["sim"].std() == 0:
                continue
            r = float(j["obs_cms"].corr(j["sim"]))
            da = float(ch["AreaC"]) / 100.0 if "AreaC" in ch else None
            cand_rec = {"gisChannel": gis, "daKm2": round(da, 2) if da else None,
                        "monthlyR": round(r, 3), "meanCms": round(float(sm.mean()), 4)}
            if best is None or (cand_rec["monthlyR"] or -9) > (best["monthlyR"] or -9):
                best = cand_rec
        results.append({
            "site_no": site,
            "assignment_class": g["assignment_class"],
            "best": best,
            "aligned": bool(best and best["monthlyR"] is not None and best["monthlyR"] >= ALIGN_MONTHLY_R),
        })
    return results


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nhd-model", default="SWAT_MODEL_Web_Application")
    ap.add_argument("--taudem-model", default=None, help="working TauDEM+lakes model name")
    ap.add_argument("--full", action="store_true", help="7-yr/2-yr-warmup window (default: short test)")
    ap.add_argument("--select-only", action="store_true", help="run station selection only (no SWAT+)")
    ap.add_argument("--out", default=None, help="output directory (overrides CMP_OUT_DIR / default)")
    args = ap.parse_args()
    y0, y1, nyskip, ev_start, ev_end = eval_window(args.full)
    out_dir = Path(args.out) if args.out else OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    usable = select_usable_gages(args.nhd_model, ev_start, ev_end)
    keep = usable[usable["usable"]]
    print(f"=== station selection ({ev_start}..{ev_end}) ===")
    print(f"  total gages: {len(usable)} | usable: {len(keep)}")
    drop = usable[~usable["usable"]]["drop_reason"].value_counts()
    for k, v in drop.items():
        print(f"   dropped {v}: {k}")
    usable.drop(columns="geometry").to_csv(out_dir / "station_selection.csv", index=False)

    if args.select_only or not args.taudem_model:
        print("\n(select-only or no --taudem-model: stopping before SWAT+ runs)")
        return

    models = {"nhd": args.nhd_model, "taudem": args.taudem_model}
    summary = {}
    per_gage = {}
    for key, model in models.items():
        df_all = run_all_channels(model, y0, y1, nyskip, ev_start, ev_end)
        res = crossvalidate_model(model, keep, df_all, args.nhd_model, ev_start, ev_end)
        n_aligned = sum(1 for r in res if r["aligned"])
        summary[key] = {"model": model, "nScored": len(res), "nAligned": n_aligned,
                        "fracAligned": round(n_aligned / max(len(res), 1), 3)}
        per_gage[key] = res
        print(f"== {key} ({model}): aligned {n_aligned}/{len(res)} (monthly r >= {ALIGN_MONTHLY_R})")

    payload = {
        "basin": "Peace HUC8 03100101",
        "period": {"simStart": y0, "simEnd": y1, "warmupYears": nyskip, "evalStart": ev_start, "evalEnd": ev_end},
        "selection": {"usableClasses": sorted(USABLE_CLASSES), "minCv": MIN_CV,
                      "minCoverage": MIN_OBS_COVERAGE, "alignMonthlyR": ALIGN_MONTHLY_R,
                      "nUsable": int(len(keep))},
        "summary": summary,
        "perGage": per_gage,
    }
    (out_dir / "peace_multistation_metrics.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {out_dir/'peace_multistation_metrics.json'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Initial (uncalibrated) SWAT+ simulation: NHDPlus-HR vs TauDEM+lakes on Oklawaha S, with
ALL channels printed so the gage->channel assignment can be cross-validated (rather than
trusting the single stations.shp pick).

Both models run with DEFAULT parameters over the calibration period (2022-2024, 1-yr warmup ->
evaluate 2023-2024). channel_sd daily output is written for EVERY channel (no print_filter).
For each model we then rank all channels against observed USGS daily flow at gage 02239501 by
timing correlation (monthly Pearson r) and report, side by side: the stations.shp-assigned
channel, the basin outlet (max cumulative DA from chandeg.con), and the best-correlated channel.

Reuses production helpers (update_time/nyskip_define/update_print_prt_file) and the bin/swatplus
wrapper (invoked from bin/, never copied). Outputs to publication/analysis/qa/taudem-vs-nhd/.
"""
from __future__ import annotations

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
from ModelProcessing.channel_sd_output import load_channel_sd_day  # noqa: E402
from ModelProcessing.channel_mapping import gis_channel_to_swat_unit_map_from_channel_lte  # noqa: E402
from ModelProcessing.print_prt import update_time, nyskip_define, update_print_prt_file, set_output_format_flags  # noqa: E402
from ModelProcessing.performance_metrics import nse as calc_nse, kge as calc_kge, pbias as calc_pbias  # noqa: E402

SWATPLUS = REPO / "bin" / "swatplus"
SITE = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0308/huc12_outlet/030801020804")
OUT = Path(os.environ.get("CMP_OUT_DIR", "/tmp/taudem_init_sim"))
GAGE = "02239501"
CMS_PER_CFS = 1.0 / 35.3147
SIM_Y0, SIM_Y1 = 2022, 2024
NYSKIP = 1
EVAL_START = f"{SIM_Y0 + NYSKIP}-01-01"   # 2023-01-01
EVAL_END = f"{SIM_Y1}-12-31"

MODELS = [
    {"key": "nhd", "label": "NHDPlus HR", "model": "SWAT_MODEL_Web_Application"},
    {"key": "taudem", "label": "TauDEM + lakes", "model": "SWAT_MODEL_TauDEM_split_s500c100_clip"},
]


def gage_channel(model_name: str) -> int:
    st = gpd.read_file(SITE / model_name / "streamflow_data" / "stations.shp")
    st["site_no"] = st["site_no"].astype(str).str.zfill(8)
    return int(st[st["site_no"] == GAGE].iloc[0]["channel"])


def chandeg_da_map(model_name: str) -> dict:
    """gis channel -> cumulative drainage area (km2) from chandeg.con (area is hectares)."""
    p = SITE / model_name / "Scenarios" / "Default" / "TxtInOut" / "chandeg.con"
    df = pd.read_csv(p, sep=r"\s+", skiprows=1)
    return {int(g): float(a) / 100.0 for g, a in zip(df["gis_id"], df["area"])}


def strm_order_map(model_name: str) -> dict:
    riv = gpd.read_file(SITE / model_name / "Watershed" / "Shapes" / "rivs1.shp")
    if "strmOrder" not in riv.columns:
        return {}
    return {int(c): int(o) for c, o in zip(riv["Channel"], riv["strmOrder"])}


def run_all_channels(m: dict) -> pd.DataFrame:
    """Run the model (default params) and return daily flo_out for ALL channels over the
    evaluation window: columns date, unit, flo_out."""
    src = SITE / m["model"] / "Scenarios" / "Default" / "TxtInOut"
    run = Path("/tmp") / f"cmp_init_{m['key']}"
    if run.exists():
        shutil.rmtree(run)
    shutil.copytree(src, run)

    update_time(str(run), SIM_Y0, SIM_Y1)
    nyskip_define(str(run), NYSKIP)
    update_print_prt_file(str(run), daily_flow_printing=True, hru_printing=False,
                          basin_wb_printing=False, channel_sd_daily_only=True)
    set_output_format_flags(str(run), csvout=False, dbout=False, cdfout=True)
    (run / "print_filter.prt").unlink(missing_ok=True)   # NO filter -> all channels
    for n in ("channel_sd_day.nc", "simulation.out"):
        p = run / n
        if p.exists():
            p.unlink()

    env = os.environ.copy()
    env["SWATPLUS_NC_DEFLATE"] = "0"
    print(f"[{m['key']}] running SWAT+ {SIM_Y0}-{SIM_Y1}, all channels ...", flush=True)
    r = subprocess.run([str(SWATPLUS)], cwd=str(run), env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=5400)
    if not (run / "channel_sd_day.nc").is_file():
        raise RuntimeError(f"[{m['key']}] no channel_sd_day.nc (exit {r.returncode}): {r.stderr[-300:]}")

    df = load_channel_sd_day(str(run), cha_path=str(run / "channel-lte.cha"))
    df["date"] = pd.to_datetime(
        df.yr.astype(str) + "-" + df.mon.astype(str).str.zfill(2) + "-" + df.day.astype(str).str.zfill(2)
    )
    df = df[(df.date >= EVAL_START) & (df.date <= EVAL_END)][["date", "unit", "flo_out"]].copy()
    n_ch = df["unit"].nunique()
    print(f"[{m['key']}] {n_ch} channels x {df['date'].nunique()} days", flush=True)
    shutil.rmtree(run)
    return df


def observed_cms() -> pd.DataFrame:
    csv = next((SITE / "SWAT_MODEL_Web_Application" / "streamflow_data").glob(f"*_{GAGE}.csv"))
    o = pd.read_csv(csv, parse_dates=["date"]).rename(columns={"streamflow": "obs_cfs"})
    o["obs_cms"] = o["obs_cfs"] * CMS_PER_CFS
    o = o[(o.date >= EVAL_START) & (o.date <= EVAL_END)]
    return o[["date", "obs_cms"]]


def crossvalidate(df_all: pd.DataFrame, obs: pd.DataFrame, unit_to_gis: dict,
                  da_map: dict, order_map: dict) -> list:
    """Rank every channel against observed by monthly timing correlation."""
    obs_i = obs.set_index("date")["obs_cms"]
    obs_m = obs_i.resample("MS").mean()
    rows = []
    for unit, g in df_all.groupby("unit"):
        s = g.set_index("date")["flo_out"]
        j = pd.concat([obs_i, s.rename("sim")], axis=1).dropna()
        if len(j) < 60:
            continue
        sim_m = s.resample("MS").mean()
        jm = pd.concat([obs_m, sim_m.rename("sim")], axis=1).dropna()
        gis = unit_to_gis.get(int(unit), int(unit))
        rows.append({
            "unit": int(unit),
            "gisChannel": int(gis),
            "daKm2": round(da_map.get(gis), 2) if da_map.get(gis) is not None else None,
            "strmOrder": order_map.get(gis),
            "meanCms": round(float(s.mean()), 4),
            "dailyR": round(float(j["obs_cms"].corr(j["sim"])), 3) if j["sim"].std() > 0 else None,
            "monthlyR": round(float(jm["obs_cms"].corr(jm["sim"])), 3) if len(jm) > 2 and jm["sim"].std() > 0 else None,
            "nse": round(float(calc_nse(j["obs_cms"].to_numpy(), j["sim"].to_numpy())), 2),
            "pbiasPct": round(float(calc_pbias(j["obs_cms"].to_numpy(), j["sim"].to_numpy())), 1),
            "kge": round(float(calc_kge(j["obs_cms"].to_numpy(), j["sim"].to_numpy())), 3),
        })
    rows.sort(key=lambda r: (r["monthlyR"] if r["monthlyR"] is not None else -9), reverse=True)
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obs = observed_cms()
    obs_mean = float(obs["obs_cms"].mean())

    per_model = {}
    series = obs.copy()
    for m in MODELS:
        df_all = run_all_channels(m)
        gmap = gis_channel_to_swat_unit_map_from_channel_lte(
            str(SITE / m["model"] / "Scenarios" / "Default" / "TxtInOut" / "channel-lte.cha"))
        unit_to_gis = {u: g for g, u in gmap.items()}
        da_map = chandeg_da_map(m["model"])
        order_map = strm_order_map(m["model"])
        ranked = crossvalidate(df_all, obs, unit_to_gis, da_map, order_map)

        assigned_gis = gage_channel(m["model"])
        outlet_gis = max(da_map, key=da_map.get)
        by_gis = {r["gisChannel"]: r for r in ranked}
        best = ranked[0] if ranked else None

        per_model[m["key"]] = {
            "label": m["label"],
            "model": m["model"],
            "nChannels": len(ranked),
            "assigned": by_gis.get(assigned_gis),
            "outlet": by_gis.get(outlet_gis),
            "bestCorrelated": best,
            "topChannels": ranked[:12],
        }

        # series for the hydrograph: outlet flow (the defensible cross-validated channel) +
        # the stations.shp-assigned flow, per model.
        for tag, gis in (("outlet", outlet_gis), ("assigned", assigned_gis)):
            u = gmap.get(gis)
            s = df_all[df_all.unit == u][["date", "flo_out"]].rename(columns={"flo_out": f"{m['key']}_{tag}_cms"})
            series = series.merge(s, on="date", how="left")

    series = series.sort_values("date")
    series.to_csv(OUT / "initial_sim_series.csv", index=False)

    payload = {
        "gage": GAGE,
        "gageName": "Oklawaha River mainstem (USGS 02239501)",
        "period": {"simStart": SIM_Y0, "simEnd": SIM_Y1, "warmupYears": NYSKIP,
                   "evalStart": EVAL_START, "evalEnd": EVAL_END},
        "units": "m3/s",
        "observedMeanCms": round(obs_mean, 2),
        "method": ("All channels printed (no print_filter); each model's channels ranked against "
                   "observed by monthly timing correlation. Reported: stations.shp-assigned channel, "
                   "basin outlet (max chandeg DA), and best-correlated channel."),
        "caveat": ("Uncalibrated default-parameter run. Gage 02239501 drains far more than this 53 km² "
                   "model, so even the outlet undersimulates the observed mean; absolute scores are not a "
                   "delineation verdict — the assignment cross-validation is the comparable signal."),
        "models": per_model,
    }
    with open(OUT / "initial_sim_metrics.json", "w") as fh:
        json.dump(payload, fh, indent=2)

    print(f"\nobserved mean = {obs_mean:.2f} cms")
    for k, v in per_model.items():
        a, o_, b = v["assigned"], v["outlet"], v["bestCorrelated"]
        print(f"== {v['label']}: {v['nChannels']} channels")
        print(f"   assigned  ch{a['gisChannel']} DA={a['daKm2']} ord={a['strmOrder']} mean={a['meanCms']} monthlyR={a['monthlyR']} NSE={a['nse']}")
        print(f"   outlet    ch{o_['gisChannel']} DA={o_['daKm2']} ord={o_['strmOrder']} mean={o_['meanCms']} monthlyR={o_['monthlyR']} NSE={o_['nse']}")
        print(f"   best-corr ch{b['gisChannel']} DA={b['daKm2']} ord={b['strmOrder']} mean={b['meanCms']} monthlyR={b['monthlyR']} NSE={b['nse']}")
    print(f"\nwrote {OUT/'initial_sim_metrics.json'} and initial_sim_series.csv")


if __name__ == "__main__":
    main()

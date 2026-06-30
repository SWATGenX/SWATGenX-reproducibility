"""Phase 1 validation: SWAT+-driven transient MF6 heads vs observed Wellogic wells.

The observations are static depth-to-water snapshots (one per well; obs_head = land
surface - 0.3048*SWL, matching MODGenX). We compare them against the SWAT+-driven
transient simulated head at each well cell, aggregated to the **average annual** head
(and the full-period mean), to answer "how does avg-annual simulated compare to observed".

Reads the 1096-day .hds written by swatmf_phase1_driver.py (no re-run needed).
"""
import os
import glob
import json
import numpy as np
import pandas as pd
import flopy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
MF_SRC = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_250m"
WORK = "/data/SWATGenXApp/codes/_temp/swatmf-coupling/mf6_transient_04124500"
DATE0 = pd.Timestamp("2022-01-01")          # period 1 = first transient day; period 0 = spin-up
DRY = 1e29


def metrics(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    nse = 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)
    rmse = float(np.sqrt(np.mean((o - s) ** 2)))
    pbias = 100.0 * np.sum(s - o) / np.sum(o)
    r = float(np.corrcoef(o, s)[0, 1])
    sd = (np.std(s) / np.std(o)) if np.std(o) else np.nan
    bd = (s.mean() / o.mean()) if o.mean() else np.nan
    kge = 1 - np.sqrt((r - 1) ** 2 + (sd - 1) ** 2 + (bd - 1) ** 2)
    return dict(n=int(len(o)), NSE=round(float(nse), 3), RMSE=round(rmse, 2),
                PBIAS=round(float(pbias), 2), R2=round(r * r, 3), KGE=round(float(kge), 3),
                MAE=round(float(np.mean(np.abs(o - s))), 2))


def sim_topmost(h3d, idom, i, j):
    """Simulated head at the topmost active, wet cell of column (i,j) — mirrors MODGenX."""
    for k in range(h3d.shape[0]):
        if idom[k, i, j] != 0 and abs(h3d[k, i, j]) < DRY:
            return float(h3d[k, i, j])
    return np.nan


def main():
    obs = pd.read_csv(os.path.join(MF_SRC, "obs_vs_sim.csv"))
    # data-quality gate (same as mf6_builder.obs_vs_sim): drop impossible obs heads.
    # land surface in this basin is ~200-260 m; obs<150 m => corrupt Wellogic SWL.
    n0 = len(obs)
    obs = obs[(obs["obs_head_m"] > 150) & (obs["obs_head_m"] < 400)].copy()
    n_bad = n0 - len(obs)

    sim = flopy.mf6.MFSimulation.load(sim_ws=WORK, exe_name="/data/SWATGenXApp/codes/bin/mf6",
                                      verbosity_level=0)
    gwf = sim.get_model()
    idom = gwf.dis.idomain.array
    hf = flopy.utils.HeadFile(glob.glob(os.path.join(WORK, "*.hds"))[0])
    times = np.asarray(hf.get_times())
    # period 0 (totim=1) is steady spin-up; transient days start at totim=2 -> DATE0
    dates = DATE0 + pd.to_timedelta(times - 2.0, unit="D")
    years = dates.year

    # accumulate per-well simulated head per timestep
    rows = obs[["row", "col"]].astype(int).to_numpy()
    nwell = len(obs)
    sim_ts = np.full((len(times), nwell), np.nan)
    for t, tt in enumerate(times):
        h3d = hf.get_data(totim=tt)
        for w, (i, j) in enumerate(rows):
            sim_ts[t, w] = sim_topmost(h3d, idom, i, j)

    transient = times >= 2.0
    obs["sim_mean_m"] = np.nanmean(sim_ts[transient], axis=0)           # full-period mean
    # average-annual: mean within each calendar year, then mean across years
    ann = {}
    for y in sorted(set(years[transient])):
        msk = transient & (years == y)
        obs[f"sim_{y}_m"] = np.nanmean(sim_ts[msk], axis=0)
        ann[y] = obs[f"sim_{y}_m"].to_numpy()
    obs["sim_avgann_m"] = np.nanmean(np.vstack(list(ann.values())), axis=0)

    g = obs.dropna(subset=["sim_avgann_m"]).copy()
    m_avgann = metrics(g["obs_head_m"], g["sim_avgann_m"])
    m_byyear = {int(y): metrics(g["obs_head_m"], g[f"sim_{y}_m"]) for y in sorted(ann)}
    # steady baseline fit (MODGenX's own sim_head_m) for an apples-to-apples reference:
    # isolates "is the misfit a coupling artifact?" from "is the uncalibrated model high?"
    m_steady = metrics(g["obs_head_m"], g["sim_head_m"])
    # interannual signal at the wells: spread of basin-mean sim head across years
    ann_means = [float(g[f"sim_{y}_m"].mean()) for y in sorted(ann)]
    interann = round(max(ann_means) - min(ann_means), 3)

    res = dict(model="04124500", n_obs_total=int(n0), n_bad_dropped=int(n_bad),
               n_used=int(len(g)), window=f"{dates.min().date()}..{dates.max().date()}",
               avg_annual=m_avgann, by_year=m_byyear, steady_baseline=m_steady,
               interannual_wellmean_spread_m=interann,
               note="uncalibrated model; avg-annual fit ~ steady baseline -> misfit is a "
                    "calibration gap, not a coupling artifact. Calibration is a separate step.")
    with open(os.path.join(HERE, "phase1_validation.json"), "w") as f:
        json.dump(res, f, indent=2)
    g.to_csv(os.path.join(HERE, "phase1_validation_wells.csv"), index=False)

    # ---- figure: obs vs avg-annual sim scatter + per-year metric bars ----
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.7), gridspec_kw=dict(width_ratios=[1.05, 1]))
    o, s = g["obs_head_m"], g["sim_avgann_m"]
    lo, hi = min(o.min(), s.min()) - 3, max(o.max(), s.max()) + 3
    ax[0].plot([lo, hi], [lo, hi], "k--", lw=1, label="1:1")
    ax[0].scatter(o, g["sim_head_m"], s=14, alpha=0.30, edgecolor="none", color="0.55",
                  label="steady baseline")
    ax[0].scatter(o, s, s=16, alpha=0.6, edgecolor="none", color="#08519c",
                  label="avg-annual transient")
    ax[0].set_xlim(lo, hi); ax[0].set_ylim(lo, hi); ax[0].set_aspect("equal")
    ax[0].set_xlabel("Observed head (m)"); ax[0].set_ylabel("Simulated head (m)")
    ax[0].set_title("Average-annual simulated vs observed\n(04124500, transient SWAT+ recharge)",
                    fontsize=10)
    txt = (f"avg-annual transient\nn = {m_avgann['n']}\nNSE = {m_avgann['NSE']}\n"
           f"KGE = {m_avgann['KGE']}\nRMSE = {m_avgann['RMSE']} m\n"
           f"PBIAS = {m_avgann['PBIAS']} %\nR² = {m_avgann['R2']}\n"
           f"(steady: NSE {m_steady['NSE']}, RMSE {m_steady['RMSE']} m)")
    ax[0].text(0.04, 0.96, txt, transform=ax[0].transAxes, va="top", fontsize=8.5,
               bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
    ax[0].legend(loc="lower right", frameon=False, fontsize=8)
    ax[0].grid(alpha=0.25, lw=0.5)

    yrs = sorted(m_byyear)
    xb = np.arange(len(yrs))
    ax[1].bar(xb - 0.2, [m_byyear[y]["NSE"] for y in yrs], 0.4, label="NSE", color="#3182bd")
    ax[1].bar(xb + 0.2, [m_byyear[y]["KGE"] for y in yrs], 0.4, label="KGE", color="#e6550d")
    ax[1].set_xticks(xb); ax[1].set_xticklabels(yrs)
    ax[1].axhline(0, color="0.5", lw=0.8)
    ax[1].set_ylabel("score"); ax[1].set_title("Annual fit stability", fontsize=10)
    ax[1].legend(frameon=False, fontsize=8); ax[1].grid(alpha=0.25, lw=0.5, axis="y")
    fig.tight_layout()
    out = os.path.join(HERE, "phase1_validation.png")
    fig.savefig(out, dpi=200)
    print("wrote", out)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()

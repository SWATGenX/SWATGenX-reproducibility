#!/usr/bin/env python3
"""PFAS uncertainty-analysis figures + metrics for the Rogue manuscript.

Consumes the AWS ensemble output (publication .../figures/ua_results/):
  ensemble_params.csv : member, soil_scale, koc_scale, kl, lm, percop
  ensemble_conc.csv   : member, <channel cols...>  (flow-weighted ng/L per reach)

Produces, mirroring the prior Water Research PFAS paper's uncertainty treatment:
  fig5_calibration_uncertainty.{pdf,png} : (a) obs-vs-modeled with 5-95 predictive
        bars, calibration vs validation stations, log-NSE/RMSE/PBIAS/P-/R-factor;
        (b) rank-ordered station ribbon (observed inside the 95% envelope).
  fig6_param_sensitivity.{pdf,png}        : standardized parameter influence on the
        station-mean in-stream PFOS (Spearman) + sampled prior ranges.
  fig7_spatial_uncertainty.{pdf,png}      : per-reach relative uncertainty (5-95
        width / median), batlow choropleth.
  ua_metrics.txt / ua_param_table.tex     : numbers + LaTeX table for the manuscript.

Spatial cal/val split: a fixed-seed 60/40 hold-out of the EGLE station channels.
The "calibrated" member is the ensemble member minimising calibration log-RMSE;
its validation metrics are an out-of-sample check. P-factor / R-factor quantify
the predictive envelope exactly as the streamflow calibration page reports them.
"""
import os, csv, math, statistics, random
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, TwoSlopeNorm
import geopandas as gpd
import pandas as pd
from matplotlib_scalebar.scalebar import ScaleBar
try:
    from cmcrameri import cm as cmc
    SEQ = cmc.batlow            # perceptually-uniform, colour-blind-safe sequential
    DIV = cmc.vik               # perceptually-uniform diverging (for ratio fields)
except Exception:
    SEQ = plt.cm.viridis; DIV = plt.cm.RdBu_r

plt.rcParams.update({"font.size": 8, "font.family": "sans-serif", "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight"})

HERE = os.path.dirname(os.path.abspath(__file__))
UA   = os.path.join(HERE, "ua_results")
SHP  = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/SWAT_MODEL_Web_Application/Watershed/Shapes"
ASSIGN = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/SWAT_MODEL_Web_Application/pfas_data/pfas_stations_assignment.csv"
CRS = 32616
PARAMS = ["soil_scale", "koc_scale", "kl", "lm", "percop"]
PLAB = {"soil_scale": "Soil loading", "koc_scale": r"In-stream $K_{oc}$",
        "kl": r"Langmuir $K_L$", "lm": r"Langmuir $\Gamma_{\max}$", "percop": "Runoff/perc. partition"}
PRANGE = {"soil_scale": (0.05, 0.22), "koc_scale": (0.50, 2.00), "kl": (0.07, 0.27),
          "lm": (1500.0, 3500.0), "percop": (0.10, 0.40)}

# ---------------------------------------------------------------- load ensemble
def load_ensemble():
    par = pd.read_csv(os.path.join(UA, "ensemble_params.csv"))
    conc = pd.read_csv(os.path.join(UA, "ensemble_conc.csv"))
    conc_chan_cols = [c for c in conc.columns if c != "member"]
    return par, conc, conc_chan_cols

def load_stations():
    st = pd.read_csv(ASSIGN)
    st = st[st["max_water_ngL"].astype(float) > 0].copy()
    st["channel"] = st["channel"].astype(int)
    st["obs"] = st["max_water_ngL"].astype(float)
    # AGGREGATE PER REACH: station-MAXIMUM observed (the source-relevant representative
    # value -- a reach hosting a source-proximal station should carry that signal, not
    # have it diluted by tributary-mouth stations snapped to the same reach; also the
    # quantity regulatory exceedance turns on). Consistent with the fig3 scatter.
    st = st.sort_values("obs", ascending=False).drop_duplicates("channel")
    st = st[["site_id", "channel", "obs", "lat", "lon"]].reset_index(drop=True)
    # tag stream order + the deterministic calibrated (soil_scale=0.11) central estimate
    rivs = gpd.read_file(f"{SHP}/rivs1.shp")
    so = dict(zip(rivs["Channel"], rivs["strmOrder"]))
    st["strmorder"] = st["channel"].map(so).fillna(1).astype(int)
    st["mainstem"] = st["strmorder"] >= 4          # the calibrated Rogue mainstem
    det = pd.read_csv(os.path.join(HERE, "channel_pfos.csv"))
    st["det"] = st["channel"].map(dict(zip(det["Channel"], det["pfos_ngL"])))
    return st

# ---------------------------------------------------------------- metrics
def logmetrics(obs, mod):
    o = np.log10(np.asarray(obs, float)); m = np.log10(np.asarray(mod, float))
    sse = np.sum((o - m) ** 2); sst = np.sum((o - o.mean()) ** 2)
    nse = 1 - sse / sst if sst > 0 else float("nan")
    rmse = math.sqrt(sse / len(o))
    pbias = 100 * (np.sum(mod) - np.sum(obs)) / np.sum(obs)
    return nse, rmse, pbias

def pr_factor(obs, lo, hi, obs_all):
    inside = np.sum((np.asarray(obs) >= np.asarray(lo)) & (np.asarray(obs) <= np.asarray(hi)))
    pf = inside / len(obs)
    sigma = statistics.pstdev(obs_all) if len(obs_all) > 1 else 1.0
    rf = float(np.mean(np.asarray(hi) - np.asarray(lo))) / sigma if sigma > 0 else float("nan")
    return pf, rf

def main():
    par, conc, chan_cols = load_ensemble()
    st = load_stations()

    # per-station ensemble matrix: rows=members, cols=stations (channels present in conc)
    have = [c for c in st["channel"] if str(c) in conc.columns]
    st = st[st["channel"].isin(have)].reset_index(drop=True)
    M = conc[[str(c) for c in st["channel"]]].apply(pd.to_numeric, errors="coerce").values  # members x stations
    obs = st["obs"].values
    cen = st["det"].values            # deterministic calibrated (soil_scale=0.11) central estimate
    main = st["mainstem"].values
    nmemb = M.shape[0]

    # predictive envelope per station (5-95% across the LHS ensemble)
    lo = np.nanpercentile(M, 5, axis=0); hi = np.nanpercentile(M, 95, axis=0)
    med = np.nanpercentile(M, 50, axis=0)

    # The CENTRAL run is the deterministic calibration (single global soil-loading
    # parameter); the ensemble supplies the predictive ENVELOPE and the sensitivity.
    # Honest spatial split for an out-of-sample check (one global parameter -> cal and
    # val metrics should be consistent, i.e. it generalises rather than overfits).
    rnd = random.Random(7); idx = list(range(len(st))); rnd.shuffle(idx)
    ncal = int(round(0.6 * len(idx)))
    cal, val = sorted(idx[:ncal]), sorted(idx[ncal:])

    def block(sel):
        ok = [i for i in sel if np.isfinite(cen[i]) and cen[i] > 0]
        nse, rmse, pb = logmetrics(obs[ok], cen[ok])
        pf, rf = pr_factor(obs[ok], lo[ok], hi[ok], obs[ok])
        return dict(n=len(ok), nse=nse, rmse=rmse, pbias=pb, pf=pf, rf=rf)

    allidx = list(range(len(st)))
    rows = {
        "all":         block(allidx),
        "mainstem":    block([i for i in allidx if main[i]]),
        "tributary":   block([i for i in allidx if not main[i]]),
        "calibration": block(cal),
        "validation":  block(val),
    }

    with open(os.path.join(UA, "ua_metrics.txt"), "w") as f:
        f.write(f"ensemble members = {nmemb}; central = deterministic soil_scale=0.11\n")
        for k in ["all", "mainstem", "tributary", "calibration", "validation"]:
            r = rows[k]
            f.write(f"{k:12s} n={r['n']:2d}  log-NSE={r['nse']:+.2f}  log-RMSE={r['rmse']:.2f} dex  "
                    f"PBIAS={r['pbias']:+.0f}%  P-factor={r['pf']:.2f}  R-factor={r['rf']:.2f}\n")
    print(open(os.path.join(UA, "ua_metrics.txt")).read())
    modbest = cen   # central estimate used in the scatter

    # ---- LaTeX parameter table (prior range + calibrated value + Spearman influence)
    # station-mean modeled conc per member for sensitivity
    smean = np.nanmean(M, axis=1)
    def spearman(x, y):
        xr = pd.Series(x).rank().values; yr = pd.Series(y).rank().values
        return float(np.corrcoef(xr, yr)[0, 1])
    infl = {p: spearman(par[p].values, smean) for p in PARAMS}
    CAL = {"soil_scale": 0.11, "koc_scale": 1.0, "kl": 0.137, "lm": 2500.0, "percop": 0.20}
    with open(os.path.join(UA, "ua_param_table.tex"), "w") as f:
        f.write("\\begin{tabular}{lccc}\n\\hline\n")
        f.write("Parameter & Prior range & Calibrated & Spearman $\\rho$ \\\\\n\\hline\n")
        nm = {"soil_scale": "Soil-loading multiplier", "koc_scale": "In-stream $K_{oc}$ multiplier",
              "kl": "Langmuir affinity $K_L$", "lm": "Langmuir max $\\Gamma_{\\max}$",
              "percop": "Runoff/percolation partition"}
        for p in PARAMS:
            a, b = PRANGE[p]
            f.write(f"{nm[p]} & [{a:g}, {b:g}] & {CAL[p]:g} & {infl[p]:+.2f} \\\\\n")
        f.write("\\hline\n\\end{tabular}\n")

    # ============================================================ FIG 5
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5), gridspec_kw={"width_ratios": [1, 1.25]})
    ax = axes[0]
    allmod = modbest[np.isfinite(modbest) & (modbest > 0)]
    lim = [0.8, max(obs.max(), np.nanmax(hi)) * 1.4]
    # central = deterministic calibration; bars = 5-95% ensemble envelope.
    # split mainstem (calibration target, near the source) vs tributary stations.
    for sel, mk, fc, lbl in [(main, "o", "#2563eb", "mainstem (order $\\geq$4)"),
                             (~main, "s", "#ea580c", "tributary (order $\\leq$3)")]:
        g = np.where(sel)[0]
        ax.errorbar(obs[g], modbest[g],
                    yerr=[np.clip(modbest[g] - lo[g], 0, None), np.clip(hi[g] - modbest[g], 0, None)],
                    fmt=mk, ms=5, mfc=fc, mec="k", mew=0.3, ecolor="#9ca3af", elinewidth=0.7,
                    capsize=1.5, alpha=0.9, label=lbl, zorder=3)
    ax.plot(lim, lim, "k-", lw=0.8, label="1:1")
    ax.plot(lim, [2 * x for x in lim], "k--", lw=0.5, alpha=0.6)
    ax.plot(lim, [0.5 * x for x in lim], "k--", lw=0.5, alpha=0.6, label=r"$\times$2")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Observed PFOS (ng L$^{-1}$)"); ax.set_ylabel("Modeled PFOS (ng L$^{-1}$)")
    a, m = rows["all"], rows["mainstem"]
    ax.text(0.04, 0.96,
            f"All ($n$={a['n']}): log-RMSE={a['rmse']:.2f} dex, P={a['pf']:.2f}\n"
            f"Mainstem ($n$={m['n']}): log-RMSE={m['rmse']:.2f} dex, P={m['pf']:.2f}",
            transform=ax.transAxes, va="top", fontsize=6.3,
            bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
    ax.legend(loc="lower right", fontsize=5.8, ncol=1)
    ax.text(0.0, 1.02, "(a)", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom")
    ax.tick_params(labelsize=7)

    # (b) rank-ordered coverage -- DISCRETE (no connecting line: the x-axis is an
    # arbitrary ordering, so a line would imply false continuity / spurious V-spikes).
    ax = axes[1]
    order = np.argsort(obs)
    x = np.arange(len(order))
    # 5-95% envelope as discrete vertical bars
    ax.vlines(x, lo[order], hi[order], color="#93c5fd", lw=3.2, alpha=0.9,
              label="5–95% predictive envelope", zorder=1)
    ax.plot(x, med[order], "D", ms=3.2, mfc="#1d4ed8", mec="#1d4ed8",
            label="ensemble median", zorder=2, ls="none")
    ax.plot(x, obs[order], "o", ms=4.5, mfc="#111827", mec="white", mew=0.4,
            label="observed (EGLE)", zorder=3, ls="none")
    ax.set_yscale("log")
    ax.set_xlabel("EGLE reach (rank-ordered by observed PFOS)")
    ax.set_ylabel("In-stream PFOS (ng L$^{-1}$)")
    a = rows["all"]
    ax.text(0.03, 0.97, f"P-factor={a['pf']:.2f}  R-factor={a['rf']:.2f}  ($n$={a['n']} reaches)",
            transform=ax.transAxes, va="top", fontsize=6.5,
            bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
    ax.legend(loc="lower right", fontsize=6)
    ax.text(0.0, 1.02, "(b)", transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom")
    ax.tick_params(labelsize=7)
    fig.savefig(os.path.join(HERE, "fig5_calibration_uncertainty.pdf"))
    fig.savefig(os.path.join(HERE, "fig5_calibration_uncertainty.png"), dpi=600)
    plt.close(fig); print("fig5 done")

    # ============================================================ FIG 6 sensitivity
    fig, ax = plt.subplots(figsize=(3.8, 2.8))
    order_p = sorted(PARAMS, key=lambda p: abs(infl[p]))
    vals = [infl[p] for p in order_p]
    # blue = positive rho, orange = negative (orange, not red, to avoid a "bad" read)
    cols = ["#2563eb" if v >= 0 else "#ea580c" for v in vals]
    for gx in [-0.75, -0.5, -0.25, 0.25, 0.5, 0.75]:
        ax.axvline(gx, color="#e5e7eb", lw=0.5, zorder=0)
    ax.barh([PLAB[p] for p in order_p], vals, height=0.6, color=cols, edgecolor="k", linewidth=0.4, zorder=2)
    ax.axvline(0, color="k", lw=0.7)
    ax.set_xlabel(r"Spearman $\rho$ with reach-mean in-stream PFOS")
    ax.set_xlim(-1, 1)
    leg6 = [Line2D([0], [0], color="#2563eb", lw=6, label=r"positive $\rho$"),
            Line2D([0], [0], color="#ea580c", lw=6, label=r"negative $\rho$")]
    ax.legend(handles=leg6, loc="lower right", fontsize=6.5, frameon=True, handlelength=1.2)
    ax.tick_params(labelsize=7)
    fig.savefig(os.path.join(HERE, "fig6_param_sensitivity.pdf"))
    fig.savefig(os.path.join(HERE, "fig6_param_sensitivity.png"), dpi=600)
    plt.close(fig); print("fig6 done")

    # ============================================================ FIG 7 spatial uncertainty
    rivs = gpd.read_file(f"{SHP}/rivs1.shp").to_crs(CRS)
    bnd = gpd.read_file(f"{SHP}/watershed_boundary.shp").to_crs(CRS)
    # per-reach relative uncertainty across all members
    rel = {}
    for c in chan_cols:
        col = pd.to_numeric(conc[c], errors="coerce").values
        col = col[np.isfinite(col) & (col > 0)]
        if len(col) >= 5:
            m = np.median(col)
            rel[int(c)] = (np.percentile(col, 95) - np.percentile(col, 5)) / m if m > 0 else np.nan
    rivs["reluncs"] = rivs["Channel"].map(rel)
    fig, ax = plt.subplots(figsize=(3.6, 4.3))
    bnd.plot(ax=ax, facecolor="#f8fafc", edgecolor="#9ca3af", lw=0.6, zorder=1)
    # reaches with no routed PFAS / too few finite members = NOT evaluated (light grey, thin)
    rivs.plot(ax=ax, color="#e5e7eb", lw=0.3, zorder=2)
    r = rivs.dropna(subset=["reluncs"])
    # relative predictive width is a MAGNITUDE (low->high); a sequential ramp is honest --
    # the diverging-at-1.0 centre implied a physical neutral point that does not exist.
    vmin = float(np.nanpercentile(r["reluncs"], 5))
    vmax = float(np.nanpercentile(r["reluncs"], 95))
    norm = Normalize(vmin=vmin, vmax=vmax)
    r.plot(ax=ax, column="reluncs", cmap=SEQ, norm=norm,
           lw=1.1 + 0.6 * (r["strmOrder"].fillna(1) - r["strmOrder"].min()), zorder=3)
    gst = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st["lon"], st["lat"]), crs=4326).to_crs(CRS)
    # white halo under the dark ring so stations stay legible over coloured reaches
    gst.plot(ax=ax, marker="o", color="none", markersize=15, edgecolor="white", linewidth=1.7, zorder=4.5)
    gst.plot(ax=ax, marker="o", color="none", markersize=11, edgecolor="#111827", linewidth=0.7, zorder=5)
    ax.set_axis_off()
    ax.add_artist(ScaleBar(1, location="lower left", frameon=False, border_pad=0.8,
                           length_fraction=0.25, font_properties={"size": 7}))
    ax.annotate("", xy=(0.90, 0.88), xytext=(0.90, 0.795), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.3))
    ax.text(0.90, 0.888, "N", transform=ax.transAxes, ha="center", va="bottom", fontsize=9, fontweight="bold")
    sm = ScalarMappable(norm=norm, cmap=SEQ); sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02, shrink=0.6)
    cb.set_label("Relative predictive width (5–95)/median", fontsize=7.5); cb.ax.tick_params(labelsize=7)
    leg = [Line2D([0],[0], color="#e5e7eb", lw=2, label="not evaluated (no PFAS routed)"),
           Line2D([0],[0], marker="o", color="w", mfc="none", mec="#111827", ms=7, label="EGLE station")]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.01),
              fontsize=6.3, frameon=False, ncol=1)
    ax.text(0.01, 0.01, "Streams: NHDPlus HR · UTM 16N (EPSG:32616)", transform=ax.transAxes,
            fontsize=5.5, color="#6b7280", va="bottom", ha="left")
    fig.savefig(os.path.join(HERE, "fig7_spatial_uncertainty.pdf"))
    fig.savefig(os.path.join(HERE, "fig7_spatial_uncertainty.png"), dpi=600)
    plt.close(fig); print("fig7 done")

if __name__ == "__main__":
    main()

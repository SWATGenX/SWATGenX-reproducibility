"""Supplementary figures for the coupled SWAT+/MODFLOW-6 PFAS manuscript.

Each figure is a guarded function: if an input is missing it prints a warning and skips that
figure rather than crashing the whole run, so a partial data set still yields a partial SI.

Data sources (all repo-local or pre-extracted; nothing is read live from /data/.../Users here):
  _si_cache/si_mf6_grid.npz   water-table heads, recharge, SFR cells, georeferenced centroids
  _si_cache/si_gw_obs.npz     modeled GW-PFOS plume, observed cells, source cells, per-reach SFT
  _si_cache/rogue_pp_vals.npy 243 calibrated pilot-point log10 K-multipliers
  ../pest/rogue/obs_wells.csv  5,383 head observation cells (row, col, head)
  ../pest/rogue/interp_W.npz   pilot-point basis matrix (-> 243 pilot-point locations)
  /tmp/mf6_headcal.npz         head obs vs sim (5,383)
  /tmp/gw_val.npz              GW-PFOS obs vs modeled, prescribed/predicted flag
  /tmp/joint_calibration.npz   joint SW+GW mainstem fit (obs, sw_only, joint, sw_part, gw_part)
  Paper A channel_pfos.csv / hru_soil_pfas.csv (companion surface-water engine study)

If _si_cache/ is empty, regenerate it with:
  sudo -n -u www-data /data/SWATGenXApp/codes/.venv/bin/python paper/_extract_si_data.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from scipy.optimize import nnls

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
CACHE = os.path.join(HERE, "_si_cache")
PEST = os.path.join(HERE, "..", "pest", "rogue")
PAPER_A = "/data/SWATGenXApp/codes/publication/swatplus-pfas-fate-transport/figures"
os.makedirs(FIG, exist_ok=True)


def _save(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}")


def _need(path):
    if not os.path.exists(path):
        print(f"  SKIP: missing {path}")
        return False
    return True


# ---------------------------------------------------------------- existing S-figures (S4, S5)
def head_fig():
    """Head calibration scatter (existing S4)."""
    f = "/tmp/mf6_headcal.npz"
    if not _need(f):
        return
    d = np.load(f)
    o, s = d["obs"], d["sim"]
    nse = 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)
    rmse = np.sqrt(np.mean((o - s) ** 2))
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot(o, s, ".", ms=2, alpha=0.25, color="tab:blue")
    lim = [o.min() - 5, o.max() + 5]
    ax.plot(lim, lim, "k-", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("observed water-table head (m)"); ax.set_ylabel("modeled head (m)")
    ax.set_title(f"MODFLOW-6 head calibration\n$n$={len(o)}, NSE={nse:.2f}, RMSE={rmse:.1f} m "
                 f"(obs range {o.min():.0f}-{o.max():.0f} m)", fontsize=10)
    ax.grid(alpha=0.3)
    _save(fig, "si_head_calibration.png")


def gw_fig():
    """Honest GW-PFOS validation: prescribed vs predicted (existing S5)."""
    f = "/tmp/gw_val.npz"
    if not _need(f):
        return
    d = np.load(f)
    o, m, issrc = d["obs"], d["mod"], d["is_src"]
    fig, ax = plt.subplots(figsize=(6, 5.5))
    pred = ~issrc
    k = pred & (o > 0) & (m > 0)
    above = k & (o > 50)
    ax.loglog(o[k & ~above], m[k & ~above], "o", ms=5, alpha=0.4, color="lightsteelblue",
              label="predicted, obs<50 ng/L (background-dominated)")
    ax.loglog(o[above], m[above], "o", ms=6, alpha=0.7, color="tab:red",
              label="predicted, obs>50 ng/L (above background)")
    ax.loglog(o[issrc & (o > 0) & (m > 0)], m[issrc & (o > 0) & (m > 0)], "s", ms=7,
              color="k", label="prescribed source cells (CNC = data)")
    lim = [1, 2e6]
    ax.plot(lim, lim, "k-", lw=1)
    ax.plot(lim, [x * 10 for x in lim], "k--", lw=0.6); ax.plot(lim, [x / 10 for x in lim], "k--", lw=0.6)
    lo, lm = np.log10(o[above]), np.log10(m[above])
    rmse = np.sqrt(np.mean((lo - lm) ** 2)); w10 = np.mean(np.abs(lo - lm) < 1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("observed groundwater PFOS (ng/L)"); ax.set_ylabel("modeled (ng/L)")
    ax.set_title(f"GW PFOS validation, prescribed vs predicted\nabove-background predicted: "
                 f"log-RMSE {rmse:.2f} dex, {100*w10:.0f}% within 10x", fontsize=10)
    ax.legend(fontsize=7, loc="lower right"); ax.grid(alpha=0.3, which="both")
    _save(fig, "si_gw_validation.png")


# ---------------------------------------------------------------- S6: in-stream longitudinal profile
def instream_profile_fig():
    """In-stream PFOS along the mainstem: observed vs SW-only vs joint, ordered upstream->downstream."""
    f = "/tmp/joint_calibration.npz"
    if not _need(f):
        return
    d = np.load(f)
    ch = d["channel"]; obs = d["obs"]; sw = d["sw_only"]; joint = d["joint"]
    swp = d["sw_part"]; gwp = d["gw_part"]
    stations = ["RR-0600", "RR-0300", "RR-0200", "RR-0060", "RR-0050", "RR-0010", "RR-0020"]
    x = np.arange(len(ch))
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(x, swp, width=0.55, color="tab:orange", alpha=0.55, label="surface-water contribution (joint)")
    ax.bar(x, gwp, width=0.55, bottom=swp, color="tab:green", alpha=0.6,
           label="groundwater contribution (joint)")
    ax.plot(x, obs, "ks-", lw=2, ms=7, label="observed grab samples")
    ax.plot(x, sw, "o--", color="tab:orange", lw=1.4, label="surface-water model alone")
    ax.plot(x, joint, "^-", color="tab:blue", lw=1.6, label="joint SW+GW fit")
    ax.set_xticks(x); ax.set_xticklabels(stations, rotation=30, fontsize=8)
    ax.set_xlabel("mainstem monitoring station (upstream -> downstream)")
    ax.set_ylabel("in-stream PFOS (ng/L)")
    ax.set_title("Longitudinal in-stream PFOS along the Rogue mainstem", fontsize=11)
    ax.legend(fontsize=7.5, loc="upper left"); ax.grid(alpha=0.3, axis="y")
    _save(fig, "si_instream_profile.png")


# ---------------------------------------------------------------- S7: per-reach SW residuals (20 reaches)
def perreach_residual_fig():
    """Per-reach observed vs modeled in-stream PFOS and log-residuals across all 20 gauged reaches."""
    # Paper A per-reach table values (observed, modeled, 5/95 envelope), with mainstem/tributary class.
    reach = [2, 1, 10, 15, 18, 11, 26, 290, 519, 449, 348, 488, 224, 321, 195, 157, 96, 112, 235, 81]
    cls = list("MMMMMMM") + list("T" * 13)
    obs = [27.0, 19.0, 9.6, 7.2, 6.8, 6.7, 6.3, 24.0, 14.0, 6.0, 4.7, 4.6, 3.8, 3.6, 3.4, 3.3, 2.6, 2.5, 1.9, 1.5]
    mod = [15.4, 14.7, 12.4, 9.2, 7.7, 11.2, 6.2, 5.4, 9.7, 0.8, 50.8, 0.1, 25.3, 7.6, 20.7, 1.2, 13.9, 32.8, 14.8, 21.9]
    obs = np.array(obs); mod = np.array(mod)
    res = np.log10(np.clip(mod, 1e-3, None)) - np.log10(obs)
    order = np.argsort(res)
    fig, ax = plt.subplots(figsize=(8, 5))
    y = np.arange(len(reach))
    colors = ["tab:blue" if cls[i] == "M" else "tab:gray" for i in order]
    ax.barh(y, res[order], color=colors, alpha=0.8)
    ax.axvline(0, color="k", lw=1)
    ax.axvline(1, color="k", ls="--", lw=0.6); ax.axvline(-1, color="k", ls="--", lw=0.6)
    ax.set_yticks(y)
    ax.set_yticklabels([f"ch {reach[i]} ({cls[i]})" for i in order], fontsize=7.5)
    ax.set_xlabel("log$_{10}$(modeled / observed)  [dex]")
    ax.set_title("Per-reach surface-water PFOS residuals, all 20 gauged reaches\n"
                 "(blue = source-bearing mainstem, gray = tributary; dashed = factor of 10)",
                 fontsize=10)
    ax.grid(alpha=0.3, axis="x")
    import matplotlib.patches as mp
    ax.legend(handles=[mp.Patch(color="tab:blue", label="mainstem (M)"),
                       mp.Patch(color="tab:gray", label="tributary (T)")], fontsize=8, loc="lower right")
    _save(fig, "si_perreach_residual.png")


# ---------------------------------------------------------------- S8: whole-network longitudinal profile
def network_longitudinal_fig():
    """Modeled in-stream PFOS for every channel (Paper A) sorted by concentration, with the 20
    observed reaches overlaid -- shows the model's full concentration field, not just gauged points."""
    f = os.path.join(PAPER_A, "channel_pfos.csv")
    if not _need(f):
        return
    import csv
    chan, val = [], []
    with open(f) as fh:
        r = csv.DictReader(fh)
        for row in r:
            chan.append(int(row["Channel"])); val.append(float(row["pfos_ngL"]))
    chan = np.array(chan); val = np.array(val)
    obs_ch = {2: 27.0, 1: 19.0, 10: 9.6, 15: 7.2, 18: 6.8, 11: 6.7, 26: 6.3, 290: 24.0, 519: 14.0,
              449: 6.0, 348: 4.7, 488: 4.6, 224: 3.8, 321: 3.6, 195: 3.4, 157: 3.3, 96: 2.6,
              112: 2.5, 235: 1.9, 81: 1.5}
    order = np.argsort(val)
    rank = np.argsort(order)
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.plot(np.arange(len(val)), np.sort(val), "-", color="tab:blue", lw=1.4,
            label=f"modeled, all {len(val)} channels (sorted)")
    for ch, o in obs_ch.items():
        idx = np.where(chan == ch)[0]
        if len(idx):
            ax.plot(rank[idx[0]], o, "o", color="tab:red", ms=5, alpha=0.8)
    ax.plot([], [], "o", color="tab:red", ms=5, label="observed (20 gauged reaches)")
    ax.set_xlabel("channel rank (low -> high modeled PFOS)")
    ax.set_ylabel("in-stream PFOS (ng/L)")
    ax.set_yscale("log")
    ax.set_title("Modeled in-stream PFOS across the full Rogue channel network\n"
                 "with the 20 observed reaches overlaid", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")
    _save(fig, "si_network_longitudinal.png")


# ---------------------------------------------------------------- S9: soil three-phase partitioning
def soil_partition_fig():
    """Per-HRU soil-PFAS initialization (Paper A): distribution of the initial soil PFOS pool and
    the Freundlich parameters that set the aqueous/solid partitioning the engine then evolves."""
    f = os.path.join(PAPER_A, "hru_soil_pfas.csv")
    if not _need(f):
        return
    import csv
    pool, kf, nf = [], [], []
    with open(f) as fh:
        r = csv.DictReader(fh)
        for row in r:
            pool.append(float(row["sol_pfas_ugha"])); kf.append(float(row["kf"])); nf.append(float(row["nf"]))
    pool = np.array(pool) / 1e6  # ug/ha -> kg/ha (readable)
    kf = np.array(kf); nf = np.array(nf)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.4))
    axs[0].hist(pool[pool > 0], bins=40, color="tab:blue", alpha=0.8)
    axs[0].set_xlabel("initial soil PFOS pool (kg ha$^{-1}$)")
    axs[0].set_ylabel("number of HRUs")
    axs[0].set_title(f"(a) soil PFOS loading\n{len(pool)} HRUs", fontsize=9)
    axs[1].hist(kf, bins=40, color="tab:green", alpha=0.8)
    axs[1].set_xlabel("Freundlich $k_f$ (L kg$^{-1}$)"); axs[1].set_title("(b) sorption strength", fontsize=9)
    axs[2].hist(nf, bins=30, color="tab:orange", alpha=0.8)
    axs[2].set_xlabel("Freundlich exponent $n$"); axs[2].set_title("(c) isotherm nonlinearity", fontsize=9)
    for a in axs:
        a.grid(alpha=0.3, axis="y")
    fig.suptitle("Surface-water leg: per-HRU soil three-phase partitioning inputs", fontsize=10)
    fig.tight_layout()
    _save(fig, "si_soil_partition.png")


# ---------------------------------------------------------------- S10: water-table map
def watertable_map_fig():
    """Simulated water-table elevation across the active MODFLOW-6 domain, with the SFR network."""
    f = os.path.join(CACHE, "si_mf6_grid.npz")
    if not _need(f):
        return
    d = np.load(f)
    wt = d["wt"]; sfr = d["sfr_cells"]
    fig, ax = plt.subplots(figsize=(6.2, 7))
    im = ax.imshow(wt, cmap="terrain", origin="upper")
    ax.plot(sfr[:, 1], sfr[:, 0], ".", color="navy", ms=1.2, alpha=0.6)
    cb = fig.colorbar(im, ax=ax, shrink=0.7); cb.set_label("water-table elevation (m)")
    ax.set_xlabel("grid column"); ax.set_ylabel("grid row")
    ax.set_title("Simulated water table, calibrated Rogue MODFLOW-6 flow field\n"
                 "(SFR stream network in dark blue)", fontsize=10)
    _save(fig, "si_watertable_map.png")


# ---------------------------------------------------------------- S11: head residual histogram
def head_residual_hist_fig():
    """Distribution of head-calibration residuals (modeled - observed) over the 5,383 wells."""
    f = "/tmp/mf6_headcal.npz"
    if not _need(f):
        return
    d = np.load(f)
    res = d["sim"] - d["obs"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(res, bins=60, color="tab:blue", alpha=0.8)
    ax.axvline(0, color="k", lw=1)
    ax.axvline(res.mean(), color="tab:red", ls="--", lw=1.2, label=f"mean bias {res.mean():+.2f} m")
    ax.set_xlabel("head residual, modeled - observed (m)")
    ax.set_ylabel("number of wells")
    ax.set_title(f"Head-calibration residuals ($n$={len(res)})\n"
                 f"RMSE {np.sqrt(np.mean(res**2)):.1f} m, "
                 f"{100*np.mean(np.abs(res)<5):.0f}% within 5 m", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
    _save(fig, "si_head_residual_hist.png")


# NOTE: a standalone recharge-field map was considered but the calibrated recharge applied to the
# Rogue MODFLOW-6 model is spatially uniform (a single SWAT+ water-balance rate of ~310 mm/yr scaled
# by one calibrated multiplier), so a map of it is a flat panel and carries no information. The value
# is reported in the text instead. The extraction keeps the rch array in the cache for completeness.


# ---------------------------------------------------------------- S12: pilot points + head obs
def pilotpoint_map_fig():
    """The 243 pilot points that parameterize the hydraulic-conductivity field and the 5,383 head
    observation cells that constrain them, over the active domain."""
    fg = os.path.join(CACHE, "si_mf6_grid.npz")
    fw = os.path.join(PEST, "interp_W.npz")
    fo = os.path.join(PEST, "obs_wells.csv")
    fp = os.path.join(CACHE, "rogue_pp_vals.npy")
    if not (_need(fg) and _need(fw) and _need(fo)):
        return
    d = np.load(fg); idom = d["idom"]
    W = np.load(fw)
    ncol = int(W["ncol"])
    act = W["act_lin"]; Wm = W["W"]
    pp_lin = act[np.argmax(Wm, axis=0)]
    pp_row = pp_lin // ncol; pp_col = pp_lin % ncol
    import csv
    orow, ocol = [], []
    with open(fo) as fh:
        for row in csv.DictReader(fh):
            orow.append(int(row["row"])); ocol.append(int(row["col"]))
    active = (idom != 0).any(axis=0).astype(float)
    fig, ax = plt.subplots(figsize=(6.2, 7))
    ax.imshow(np.where(active > 0, 1, np.nan), cmap="Greys", origin="upper", alpha=0.25, vmin=0, vmax=2)
    ax.plot(ocol, orow, ".", color="tab:blue", ms=2, alpha=0.35, label=f"head observations ($n$={len(orow)})")
    if os.path.exists(fp):
        ppv = np.load(fp)
        sc = ax.scatter(pp_col, pp_row, c=ppv, cmap="RdBu_r", s=22, edgecolor="k", lw=0.3,
                        vmin=-0.8, vmax=0.8, label=f"pilot points ($n$={len(pp_row)})", zorder=3)
        cb = fig.colorbar(sc, ax=ax, shrink=0.6); cb.set_label("calibrated log$_{10}$ $K$ multiplier")
    else:
        ax.scatter(pp_col, pp_row, c="tab:red", s=20, edgecolor="k", lw=0.3,
                   label=f"pilot points ($n$={len(pp_row)})", zorder=3)
    ax.set_xlabel("grid column"); ax.set_ylabel("grid row")
    ax.set_title("Pilot-point parameterization and head observations\n"
                 "(pilot points coloured by calibrated conductivity multiplier)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    _save(fig, "si_pilotpoints_map.png")


# ---------------------------------------------------------------- S14: GW plume plan view + obs
def plume_map_fig():
    """Modeled groundwater PFOS plume (plan view, depth-maximum) with the 73 observation cells and
    the prescribed House Street source overlaid on the same logarithmic colour scale."""
    f = os.path.join(CACHE, "si_gw_obs.npz")
    if not _need(f):
        return
    d = np.load(f)
    cmax = d["cmax"]; orow = d["obs_row"]; ocol = d["obs_col"]; oval = d["obs_val"]
    srow = d["src_row"]; scol = d["src_col"]
    plume = np.where(cmax > 1, cmax, np.nan)
    norm = LogNorm(vmin=10, vmax=1e5)
    fig, ax = plt.subplots(figsize=(6.4, 7))
    im = ax.imshow(plume, cmap="magma", origin="upper", norm=norm)
    ax.scatter(ocol, orow, c=np.clip(oval, 10, 1e5), cmap="magma", norm=norm,
               s=34, edgecolor="white", lw=0.6, label=f"observed cells ($n$={len(orow)})")
    ax.plot(scol, srow, "s", color="cyan", ms=9, mec="k", mew=0.8, label="prescribed source (House St.)")
    cb = fig.colorbar(im, ax=ax, shrink=0.7); cb.set_label("groundwater PFOS (ng/L)")
    ax.set_xlabel("grid column"); ax.set_ylabel("grid row")
    ax.set_title("Modeled groundwater PFOS plume with observations\n"
                 "(filled field = model, ringed dots = observations, same scale)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    _save(fig, "si_plume_map.png")


# ---------------------------------------------------------------- S15: SFT discharged-load network
def sft_network_fig():
    """Groundwater-discharged PFOS routed by the SFT package into the stream network: each reach cell
    coloured by the SFT in-stream concentration (the groundwater contribution before surface dilution)."""
    fg = os.path.join(CACHE, "si_mf6_grid.npz")
    fo = os.path.join(CACHE, "si_gw_obs.npz")
    if not (_need(fg) and _need(fo)):
        return
    d = np.load(fg); sfr = d["sfr_cells"]
    dd = np.load(fo); reach_c = dd["reach_c"]
    n = min(len(sfr), len(reach_c))
    sfr = sfr[:n]; reach_c = reach_c[:n]
    pos = reach_c > 0.01
    fig, ax = plt.subplots(figsize=(6.4, 7))
    ax.plot(sfr[:, 1], sfr[:, 0], ".", color="lightgray", ms=2, label="reaches with no GW PFOS")
    sc = ax.scatter(sfr[pos, 1], sfr[pos, 0], c=np.clip(reach_c[pos], 0.1, None),
                    cmap="viridis", norm=LogNorm(vmin=0.1, vmax=max(1.0, reach_c.max())),
                    s=10, label=f"reaches receiving GW PFOS ($n$={int(pos.sum())})")
    cb = fig.colorbar(sc, ax=ax, shrink=0.7); cb.set_label("SFT in-stream PFOS (ng/L)")
    ax.invert_yaxis()  # row 0 at top, to match the imshow-based domain maps
    ax.set_xlabel("grid column"); ax.set_ylabel("grid row")
    ax.set_title(f"Groundwater-discharged PFOS routed into the stream network\n"
                 f"({int(pos.sum())} of {len(reach_c)} reaches receive groundwater PFOS)", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    _save(fig, "si_sft_network.png")


# ---------------------------------------------------------------- S16: joint-fit LOO + objective
def joint_diagnostics_fig():
    """Joint-calibration diagnostics: leave-one-out cross-validation of the joint vs surface-only fit,
    and the NNLS objective surface in the (L, g) plane with the 95% confidence region."""
    f = "/tmp/joint_calibration.npz"
    if not _need(f):
        return
    d = np.load(f)
    obs = d["obs"]; sw_only = d["sw_only"]; gw_unit = d["gw_unit"]
    L0 = 0.11
    A = sw_only / L0   # SW contribution per unit loading
    B = gw_unit        # GW contribution per unit effectiveness
    n = len(obs)

    # ---- leave-one-out: held-out absolute error, surface-only (g=0) vs joint (L,g) ----
    loo_sw, loo_joint = [], []
    for i in range(n):
        mask = np.arange(n) != i
        # surface-only: fit L alone (g=0)
        Ls, _ = nnls(A[mask][:, None], obs[mask])
        loo_sw.append(abs(Ls[0] * A[i] - obs[i]))
        # joint: fit (L,g)
        coef, _ = nnls(np.c_[A[mask], B[mask]], obs[mask])
        loo_joint.append(abs(coef @ np.array([A[i], B[i]]) - obs[i]))
    loo_sw = np.array(loo_sw); loo_joint = np.array(loo_joint)

    # ---- objective surface over (L,g) ----
    Lg = np.linspace(0.0, 0.16, 120)
    gg = np.linspace(0.0, 0.16, 120)
    LL, GG = np.meshgrid(Lg, gg)
    SSE = np.zeros_like(LL)
    for a, b, y in zip(A, B, obs):
        SSE += (a * LL + b * GG - y) ** 2
    Lhat, ghat = float(d["L"]), float(d["g"])
    sse_min = SSE.min()
    # 95% confidence region for 2 params: SSE <= SSEmin * (1 + p/(n-p) * F)
    p, dof = 2, n - 2
    from scipy.stats import f as fdist
    thresh = sse_min * (1 + p / dof * fdist.ppf(0.95, p, dof))

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
    # panel a: LOO
    x = np.arange(n)
    w = 0.38
    axs[0].bar(x - w / 2, loo_sw, w, color="tab:orange", alpha=0.8, label="surface-only ($g$=0)")
    axs[0].bar(x + w / 2, loo_joint, w, color="tab:blue", alpha=0.8, label="joint SW+GW")
    axs[0].set_xticks(x); axs[0].set_xticklabels([f"ch{c}" for c in d["channel"]], fontsize=8, rotation=30)
    axs[0].set_ylabel("held-out absolute error (ng/L)")
    axs[0].set_title(f"(a) leave-one-out cross-validation\nmean absolute error (MAE) "
                     f"{loo_sw.mean():.1f} -> {loo_joint.mean():.1f} ng/L "
                     f"(RMSE {np.sqrt((loo_sw**2).mean()):.1f} -> {np.sqrt((loo_joint**2).mean()):.1f})",
                     fontsize=8.5)
    axs[0].legend(fontsize=8); axs[0].grid(alpha=0.3, axis="y")
    # panel b: objective surface
    cs = axs[1].contourf(LL, GG, np.log10(SSE), levels=25, cmap="viridis")
    axs[1].contour(LL, GG, SSE, levels=[thresh], colors="white", linewidths=1.6, linestyles="--")
    axs[1].plot(Lhat, ghat, "*", color="red", ms=16, label=f"joint optimum\n($L$={Lhat:.3f}, $g$={ghat:.3f})")
    axs[1].axhline(0, color="w", lw=0.6, alpha=0.5)
    axs[1].set_xlabel("surface soil-loading $L$"); axs[1].set_ylabel("groundwater effectiveness $g$")
    fig.colorbar(cs, ax=axs[1], shrink=0.8).set_label("log$_{10}$ SSE")
    axs[1].set_title("(b) NNLS objective surface\n(white dashed = 95% confidence region)", fontsize=9.5)
    axs[1].legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    _save(fig, "si_joint_diagnostics.png")


if __name__ == "__main__":
    figs = [head_fig, gw_fig, instream_profile_fig, perreach_residual_fig, network_longitudinal_fig,
            soil_partition_fig, watertable_map_fig, head_residual_hist_fig,
            pilotpoint_map_fig, plume_map_fig, sft_network_fig, joint_diagnostics_fig]
    for fn in figs:
        print(fn.__name__)
        try:
            fn()
        except Exception as e:
            print(f"  ERROR {fn.__name__}: {e}")

#!/usr/bin/env python3
"""Re-plot the Morris sensitivity ensemble figures (Fig 6 daily; Suppl. monthly)
directly from the saved per-member ensemble .npz files, with NO on-figure title
(Elsevier artwork rule: title belongs in the caption). Panels carry a letter
only. Band/median/best/observed are computed from the 999 members.

Outputs (overwrites the previously stacked, titled versions):
  publication/figures/final/fig-sensitivity-ensemble-controlled-basins-daily.png
  publication/figures/supplement/fig-sensitivity-ensemble-controlled-basins-monthly.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
USERS = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID")
FINAL = REPO / "publication/figures/final"
SUPP = REPO / "publication/figures/supplement"

BASINS = [
    {"letter": "a", "site": "02297600", "vpuid": "0310", "ch": "2"},
    {"letter": "b", "site": "05536265", "vpuid": "0712", "ch": "25"},
]


def _ens_dir(b):
    return (USERS / b["vpuid"] / "usgs_station" / b["site"]
            / "calibration_artifacts/Default_initialized"
            / "figures_SWAT_MODEL_Web_Application/SF/sensitivity")  # fallback
def _ens_npz_dir(b):
    return (USERS / b["vpuid"] / "usgs_station" / b["site"]
            / "calibration_artifacts/Default_initialized/sensitivity/ensemble")


def _nse(obs, sim):
    m = np.isfinite(obs) & np.isfinite(sim)
    if m.sum() < 2:
        return -np.inf
    o, s = obs[m], sim[m]
    denom = np.sum((o - o.mean()) ** 2)
    return 1 - np.sum((o - s) ** 2) / denom if denom > 0 else -np.inf


def _load(b, freq):
    files = sorted(_ens_npz_dir(b).glob(f"m*_s{b['ch']}.npz"))
    if not files:
        raise FileNotFoundError(_ens_npz_dir(b))
    sims, obs_ref, x = [], None, None
    for f in files:
        z = np.load(f, allow_pickle=True)
        if freq == "daily":
            sims.append(z["sim"])
            if obs_ref is None:
                obs_ref = z["obs"]
                x = z["date_ns"].astype("datetime64[ns]")
        else:
            sims.append(z["monthly_sim"])
            if obs_ref is None:
                obs_ref = z["monthly_obs"]
                yr, mon = z["monthly_yr"], z["monthly_mon"]
                x = np.array([np.datetime64(f"{int(y):04d}-{int(m):02d}-15") for y, m in zip(yr, mon)])
    sims = np.vstack(sims)
    return x, obs_ref, sims, len(files)


def _pr_factors(obs, lo, hi, band_sims):
    m = np.isfinite(obs)
    inside = (obs[m] >= lo[m]) & (obs[m] <= hi[m])
    pfac = inside.mean() if m.sum() else np.nan
    sd = np.nanstd(obs[m])
    rfac = np.mean((hi[m] - lo[m])) / sd if sd > 0 else np.nan
    return pfac, rfac


def render(freq: str, out: Path) -> None:
    fig, axes = plt.subplots(len(BASINS), 1, figsize=(11, 6.2), constrained_layout=True)
    for ax, b in zip(axes, BASINS):
        x, obs, sims, n = _load(b, freq)
        lo = np.nanpercentile(sims, 2.5, axis=0)
        hi = np.nanpercentile(sims, 97.5, axis=0)
        med = np.nanmedian(sims, axis=0)
        best = sims[int(np.argmax([_nse(obs, s) for s in sims]))]
        pfac, rfac = _pr_factors(obs, lo, hi, sims)
        ax.fill_between(x, lo, hi, color="#9ec9e2", alpha=0.6,
                        label=f"95% pred. uncertainty (2.5--97.5%)")
        ax.plot(x, med, "--", color="0.45", lw=0.9, label="Ensemble median")
        ax.plot(x, obs, color="#1f3b73", lw=0.8, label="Observed")
        ax.plot(x, best, color="#b3271e", lw=0.8, label="Best parameter set")
        ax.set_ylabel("Daily streamflow (cfs)" if freq == "daily" else "Monthly streamflow (cfs)")
        ax.set_title(f"({b['letter']})", loc="left", fontsize=11, pad=4)
        ax.annotate(f"P-factor {pfac:.2f}   R-factor {rfac:.2f}   (n={n})",
                    xy=(0.01, 0.97), xycoords="axes fraction", va="top", ha="left",
                    fontsize=8, color="0.25")
        ax.margins(x=0.01)
        if b["letter"] == "a":
            ax.legend(loc="upper right", fontsize=8, framealpha=0.9, ncol=2)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out}")


def main() -> None:
    render("daily", FINAL / "fig-sensitivity-ensemble-controlled-basins-daily.png")
    render("monthly", SUPP / "fig-sensitivity-ensemble-controlled-basins-monthly.png")


if __name__ == "__main__":
    main()

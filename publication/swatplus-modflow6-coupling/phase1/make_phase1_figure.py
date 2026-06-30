"""Phase 1 coupling figure: SWAT+ daily percolation -> MF6 transient groundwater head."""
import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
ts = pd.read_csv(os.path.join(HERE, "phase1_timeseries.csv"), parse_dates=["date"])
res = json.load(open(os.path.join(HERE, "phase1_result.json")))
base = res["steady_baseline_mean_head_m"]

# 30-day rolling perc to expose the seasonal signal under daily noise
ts["perc_30d"] = ts["basin_perc_mm"].rolling(30, center=True, min_periods=1).mean()

fig, ax = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True,
                       gridspec_kw=dict(height_ratios=[1, 1.25], hspace=0.12))

ax[0].fill_between(ts["date"], 0, ts["basin_perc_mm"], color="#9ecae1", lw=0, alpha=0.7,
                   label="daily")
ax[0].plot(ts["date"], ts["perc_30d"], color="#08519c", lw=1.6, label="30-day mean")
ax[0].set_ylabel("Basin percolation\n(mm day$^{-1}$)")
ax[0].legend(loc="upper right", frameon=False, fontsize=8, ncol=2)
ax[0].set_title("SWAT+ → MODFLOW 6 one-way coupling (04124500): "
                "daily recharge drives groundwater head", fontsize=11)
ax[0].margins(x=0.01)

ax[1].axhline(base, color="0.4", ls="--", lw=1.2, label=f"steady baseline ({base:.2f} m)")
ax[1].plot(ts["date"], ts["gw_mean_head_m"], color="#a63603", lw=1.3,
           label="SWAT+-driven transient")
ax[1].set_ylabel("Domain-mean\ngroundwater head (m)")
ax[1].set_xlabel("Date")
ax[1].legend(loc="upper left", frameon=False, fontsize=8)
ax[1].xaxis.set_major_formatter(DateFormatter("%Y-%m"))
ax[1].margins(x=0.01)
for a in ax:
    a.grid(alpha=0.25, lw=0.5)

cap = (f"All {res['nper']}/{res['n_periods']} daily steps converged. "
       f"Head range {res['transient_mean_head_min']:.2f}–{res['transient_mean_head_max']:.2f} m "
       f"(Δ≈{res['transient_mean_head_max']-res['transient_mean_head_min']:.2f} m) about the "
       f"{base:.2f} m steady baseline.")
fig.text(0.5, 0.005, cap, ha="center", fontsize=7.5, color="0.3")
fig.subplots_adjust(left=0.11, right=0.98, top=0.93, bottom=0.10)
out = os.path.join(HERE, "phase1_coupling.png")
fig.savefig(out, dpi=200)
print("wrote", out)

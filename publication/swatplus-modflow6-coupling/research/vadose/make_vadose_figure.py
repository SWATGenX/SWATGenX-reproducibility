"""Vadose travel-time figure: PFOS vs PFOA arrival distributions + AWI impact +
air-water-interface sensitivity to grain size.  No embedded title (caption only).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

theta = 0.18; por = 0.38; Sw = theta/por; rho_b = 1.6
q = 0.139
COMP = {"PFOS": dict(Kd=2.0, Kaw_cm=0.060, c="#b2182b"),
        "PFOA": dict(Kd=0.33, Kaw_cm=0.015, c="#2166ac")}

def R(p, d50, awi=True):
    A = 6*(1-por)*(1-Sw)/d50
    return 1 + (rho_b/theta)*p["Kd"] + ((A/theta)*p["Kaw_cm"]*10 if awi else 0)

dtw = np.load("/tmp/mf6_engine_test/dtw_grid.npy")
L = dtw[np.isfinite(dtw)]; L = L[(L > 0) & (L < 300)]

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

# (a) travel-time distributions, with vs without AWI, d50 = 0.5 mm
d50a = 0.5
bins = np.logspace(0, 4, 40)
for name, p in COMP.items():
    tau = L*theta*R(p, d50a, True)/q
    ax[0].hist(tau, bins=bins, color=p["c"], alpha=0.55, label=f"{name} (with AWI)")
    taun = L*theta*R(p, d50a, False)/q
    ax[0].hist(taun, bins=bins, color=p["c"], histtype="step", lw=1.5, ls="--",
               label=f"{name} (no AWI)")
ax[0].set_xscale("log"); ax[0].set_xlabel("vadose travel time to water table (yr)")
ax[0].set_ylabel("number of grid cells")
ax[0].axvspan(1, 54, color="grey", alpha=0.12)   # 1970-2024 simulation window
ax[0].text(7, ax[0].get_ylim()[1]*0.9, "sim\nwindow", fontsize=7, ha="center")
ax[0].legend(fontsize=7.5, loc="upper right")
ax[0].text(0.02, 0.97, "(a)", transform=ax[0].transAxes, fontweight="bold", va="top")

# (b) AWI retardation multiplier vs grain size (why AWI matters in fine media)
d50s = np.logspace(-1.3, 0.5, 60)   # 0.05 - 3 mm
for name, p in COMP.items():
    mult = [R(p, d, True)/R(p, d, False) for d in d50s]
    ax[1].plot(d50s, mult, color=p["c"], lw=2, label=name)
ax[1].axhspan(1.5, 5, color="green", alpha=0.10)   # Guo 2020 literature range
ax[1].text(0.06, 4.3, "Guo 2020\nAWI 1.5-5x", fontsize=7, color="green")
ax[1].set_xscale("log"); ax[1].set_xlabel("median grain diameter d50 (mm)")
ax[1].set_ylabel("AWI retardation multiplier  R / R(no AWI)")
ax[1].axvline(0.2, color="grey", ls=":", lw=1); ax[1].text(0.21, ax[1].get_ylim()[1]*0.5, "silt/\nfine sand", fontsize=7)
ax[1].legend(fontsize=8)
ax[1].text(0.02, 0.97, "(b)", transform=ax[1].transAxes, fontweight="bold", va="top")

fig.tight_layout()
fig.savefig("vadose_travel_time.png", dpi=300, bbox_inches="tight")
print("wrote vadose_travel_time.png")

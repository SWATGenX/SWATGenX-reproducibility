"""Analyze the OAT hydraulic sensitivity sweep and make the tornado figure.
Reads /tmp/oat_results.csv; reports which hydraulic parameters dominate the
SW<->GW mass exchange and the mass-exchange + mass-balance ranges. No title.
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("/tmp/oat_results.csv")
base = df[df.param == "base"].iloc[0]
LAB = {"Kh": "aquifer K$_h$", "Kv": "aquifer K$_v$", "recharge": "recharge",
       "sfrk": "streambed K", "SY": "specific yield", "disp": "dispersivity"}
QOIS = [("sfr_gain_m3", "groundwater discharge to stream (baseflow, m$^3$)"),
        ("pfhxa_disch_kg", "PFHxA mass discharged to stream (kg)")]
params = [p for p in df.param.unique() if p != "base"]

print("=== base ===")
print(f"  recharge {base.recharge_m:.3g} m | baseflow {base.sfr_gain_m3:.3g} m3 | "
      f"PFHxA discharged {base.pfhxa_disch_kg:.3g} kg | mass-bal {base.massbal_pct:.2g}%\n")

# OAT swing per parameter for each QoI: (Q at x2 - Q at x0.5) / Q_base
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for k, (q, qlab) in enumerate(QOIS):
    swing = {}
    for p in params:
        sub = df[df.param == p]
        try:
            lo = sub[sub.factor == 0.5][q].values[0]
            hi = sub[sub.factor == 2.0][q].values[0]
            swing[p] = (hi - lo) / base[q] * 100.0
        except Exception:
            swing[p] = np.nan
    order = sorted(swing, key=lambda p: abs(swing[p]))
    vals = [swing[p] for p in order]
    cols = ["#b2182b" if v >= 0 else "#2166ac" for v in vals]
    ax[k].barh(range(len(order)), vals, color=cols)
    ax[k].set_yticks(range(len(order))); ax[k].set_yticklabels([LAB.get(p, p) for p in order], fontsize=9)
    ax[k].axvline(0, color="k", lw=0.6)
    ax[k].set_xlabel("change from base, x0.5->x2 (%)")
    ax[k].text(0.02, 0.97, f"({'ab'[k]}) {qlab}", transform=ax[k].transAxes, va="top",
               fontsize=8.5, fontweight="bold")
    print(f"=== {q}: dominant hydraulic controls (|swing %|) ===")
    for p in reversed(order):
        print(f"   {LAB.get(p,p):16s} {swing[p]:+6.0f}%")
    print()

fig.tight_layout()
fig.savefig("oat_hydraulic_tornado.png", dpi=300, bbox_inches="tight")
print("wrote oat_hydraulic_tornado.png")

# mass-exchange + mass-balance ranges across the whole sweep
print("=== ranges across the OAT sweep ===")
for q, lab in [("recharge_m", "recharge (m)"), ("sfr_gain_m3", "baseflow (m3)"),
               ("sfr_loss_m3", "seepage (m3)"), ("pfhxa_disch_kg", "PFHxA discharged (kg)"),
               ("massbal_pct", "transport mass-balance (%)")]:
    v = df[q].astype(float)
    print(f"   {lab:26s} {v.min():.3g} .. {v.max():.3g}  (base {base[q]:.3g})")

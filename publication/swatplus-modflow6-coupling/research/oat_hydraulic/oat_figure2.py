"""OAT hydraulic sensitivity figure + ranking from the converged runs.
For each hydraulic parameter, the % change (from base) in the SW<->GW mass
exchange (baseflow) and PFHxA discharge, using whichever perturbation converged.
Four extreme cases (Kh x2, Kv x0.5, recharge x2, streambed-K x0.5) hit MODFLOW
non-convergence at high flow velocity -- a robustness finding, flagged here.
No embedded title (caption only).
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("/tmp/oat_results.csv")
base = df[df.param == "base"].iloc[0]
LAB = {"Kh":"aquifer K$_h$","sfrk":"streambed K","recharge":"recharge",
       "Kv":"aquifer K$_v$","SY":"specific yield","disp":"dispersivity"}
NONCONV = {"Kh":"2.0","Kv":"0.5","recharge":"2.0","sfrk":"0.5"}  # broke convergence

rows = []
for p in [x for x in df.param.unique() if x != "base"]:
    sub = df[(df.param == p) & df.sfr_gain_m3.notna()]
    if sub.empty:
        continue
    # use the converged factor with the largest |deviation|
    sub = sub.assign(dq=(sub.pfhxa_disch_kg-base.pfhxa_disch_kg)/base.pfhxa_disch_kg*100,
                     dbf=(sub.sfr_gain_m3-base.sfr_gain_m3)/base.sfr_gain_m3*100)
    r = sub.iloc[sub.dq.abs().argmax()]
    rows.append((p, r.factor, r.dq, r.dbf))
rows.sort(key=lambda x: abs(x[2]))

fig, ax = plt.subplots(figsize=(8, 4.2))
y = np.arange(len(rows))
ax.barh(y-0.2, [r[3] for r in rows], 0.38, color="#5b8fb0", label="baseflow (SW$\\leftrightarrow$GW water)")
ax.barh(y+0.2, [r[2] for r in rows], 0.38, color="#b2603a", label="PFHxA discharge to stream")
ax.axvline(0, color="k", lw=0.6)
labs = []
for p,f,dq,dbf in rows:
    tag = f"{LAB.get(p,p)}  ($\\times${f:g}"
    tag += f"; $\\times${NONCONV[p]} diverged)" if p in NONCONV else ")"
    labs.append(tag)
ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=9)
ax.set_xlabel("change from base (%)")
ax.legend(fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig("/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/oat_hydraulic/oat_tornado.png",
            dpi=300, bbox_inches="tight")
print("wrote oat_tornado.png\n")

print("=== ranking (|% change in PFHxA discharge|) ===")
for p,f,dq,dbf in reversed(rows):
    print(f"  {LAB.get(p,p):16s} x{f:<4g}  discharge {dq:+6.1f}%   baseflow {dbf:+6.1f}%")
print("\n=== ranges across converged runs ===")
v=df[df.sfr_gain_m3.notna()]
print(f"  baseflow (SFR gain): {v.sfr_gain_m3.min()/1e6:.1f}-{v.sfr_gain_m3.max()/1e6:.1f} Mm3")
print(f"  PFHxA discharge:     {v.pfhxa_disch_kg.min():.2f}-{v.pfhxa_disch_kg.max():.2f} kg")
print(f"  recharge:            {v.recharge_m.min():.0f}-{v.recharge_m.max():.0f} m")
print(f"  mass-balance |disc|: <= {v.massbal_pct.abs().max():.2f} %")

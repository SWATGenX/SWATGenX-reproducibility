"""Sobol total-order indices for the in-stream PFOS prediction at two mainstem
locations, from a random-forest surrogate on the 380-run Morris ensemble.
Shows the lower mainstem is groundwater-pathway controlled and the mid mainstem
surface-pathway controlled.  No embedded title (caption only).
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from SALib.sample import sobol as ssamp
from SALib.analyze import sobol as sanal

HERE = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/sa"
PARAMS = [("soil_scale",0.05,0.22),("koc_scale",0.50,2.00),("kl",0.07,0.27),("lm",1500.,3500.),
          ("percop",0.10,0.40),("kh",-0.80,0.80),("kv",-0.80,0.80),("rch",-0.30,0.48),
          ("ghb",-2.00,0.50),("drn",-2.00,0.50),("pump",-1.70,0.00),("sfrk",-1.50,1.00),
          ("t_kf",-3.00,-1.30),("t_n",0.60,1.00),("t_alh",1.00,50.0),("t_ath",0.10,5.00),
          ("t_cap",4.00,6.00),("t_bg",5.00,20.0)]
NAMES = [p[0] for p in PARAMS]
PROB = {"num_vars": 18, "names": NAMES, "bounds": [[p[1], p[2]] for p in PARAMS]}
LABEL = {"sfrk": "streambed K", "kh": "aquifer Kh", "t_cap": "source magnitude",
         "soil_scale": "soil PFAS", "kl": "AWI K$_L$", "lm": "AWI $\\Gamma_{max}$",
         "kv": "aquifer Kv", "rch": "recharge", "koc_scale": "soil K$_{oc}$"}

X = pd.read_csv(f"{HERE}/results/morris_samples.csv")[NAMES].values
Yall = pd.read_csv(f"{HERE}/results/morris_Y.csv")
ST = {}
for qoi in ["instream_lower", "instream_mid"]:
    y = Yall[qoi].values; m = np.isfinite(y) & np.isfinite(X).all(axis=1)
    rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=3, random_state=0)
    rf.fit(X[m], np.log10(np.clip(y[m], 1e-3, None)))
    Si = sanal.analyze(PROB, rf.predict(ssamp.sample(PROB, 2048)), print_to_console=False)
    ST[qoi] = Si["ST"]

fig, ax = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
for k, (qoi, sub) in enumerate(zip(["instream_lower", "instream_mid"],
                                   ["lower mainstem (GW-dominated)", "mid mainstem (surface-dominated)"])):
    st = ST[qoi]; idx = np.argsort(st)[::-1][:6][::-1]
    labs = [LABEL.get(NAMES[i], NAMES[i]) for i in idx]
    cols = ["#b2182b" if NAMES[i] in ("sfrk","kh","kv","t_cap","t_kf","t_n","ghb","drn") else "#2166ac" for i in idx]
    ax[k].barh(range(len(idx)), st[idx], color=cols)
    ax[k].set_yticks(range(len(idx))); ax[k].set_yticklabels(labs, fontsize=9)
    ax[k].set_xlabel("Sobol total-order index $S_T$"); ax[k].set_xlim(0, 1)
    ax[k].text(0.02, 0.97, f"({'ab'[k]}) {sub}", transform=ax[k].transAxes, va="top", fontsize=9, fontweight="bold")
from matplotlib.patches import Patch
ax[1].legend(handles=[Patch(color="#b2182b", label="groundwater pathway"),
                      Patch(color="#2166ac", label="surface pathway")], fontsize=8, loc="lower right")
fig.tight_layout()
fig.savefig(f"{HERE}/results/sobol_instream.png", dpi=300, bbox_inches="tight")
print("wrote sobol_instream.png")

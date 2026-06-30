"""Variance-based Sobol indices for the coupled SWAT+/MODFLOW6 PFAS model,
computed on a random-forest surrogate fit to the existing 380-run Morris
ensemble (no new MF6 runs).  Refines the Morris screening into first- and
total-order variance shares for the in-stream PFOS prediction.
"""
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze

HERE = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/sa"
PARAMS = [("soil_scale",0.05,0.22),("koc_scale",0.50,2.00),("kl",0.07,0.27),
          ("lm",1500.,3500.),("percop",0.10,0.40),("kh",-0.80,0.80),("kv",-0.80,0.80),
          ("rch",-0.30,0.48),("ghb",-2.00,0.50),("drn",-2.00,0.50),("pump",-1.70,0.00),
          ("sfrk",-1.50,1.00),("t_kf",-3.00,-1.30),("t_n",0.60,1.00),("t_alh",1.00,50.0),
          ("t_ath",0.10,5.00),("t_cap",4.00,6.00),("t_bg",5.00,20.0)]
NAMES = [p[0] for p in PARAMS]
PROBLEM = {"num_vars": 18, "names": NAMES, "bounds": [[p[1], p[2]] for p in PARAMS]}

X = pd.read_csv(f"{HERE}/results/morris_samples.csv")[NAMES].values
Yall = pd.read_csv(f"{HERE}/results/morris_Y.csv")

for qoi in ["instream_lower", "instream_mid"]:
    y = Yall[qoi].values
    m = np.isfinite(y) & np.isfinite(X).all(axis=1)
    Xf, yf = X[m], np.log10(np.clip(y[m], 1e-3, None))     # log10 conc
    rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=3, random_state=0)
    r2 = cross_val_score(rf, Xf, yf, cv=5, scoring="r2").mean()
    rf.fit(Xf, yf)
    XS = sobol_sample.sample(PROBLEM, 2048)
    YS = rf.predict(XS)
    Si = sobol_analyze.analyze(PROBLEM, YS, print_to_console=False)
    print(f"\n=== Sobol for {qoi}  (surrogate CV R^2 = {r2:.2f}, n={m.sum()}) ===")
    order = np.argsort(Si["ST"])[::-1]
    print(f"  {'param':10s}  ST     S1")
    for i in order[:8]:
        print(f"  {NAMES[i]:10s}  {Si['ST'][i]:.2f}   {Si['S1'][i]:.2f}")
    top = [NAMES[i] for i in order[:4]]
    print(f"  -> top controls on {qoi}: {', '.join(top)}")

#!/usr/bin/env python3
"""Robust Morris elementary-effects analysis tolerant of failed runs.

SALib's analyzer needs intact trajectories (it reshapes to ntraj x (D+1)); a single
failed model run (NaN) forces dropping the whole 19-point trajectory. Instead we
compute the elementary effects step-by-step on the unit hypercube and skip only the
individual EEs whose endpoints include a NaN -- salvaging every other effect. Writes
morris_indices_<qoi>.csv (param, mu_star, mu_star_conf, sigma) for make_morris_figure.py.
"""
import os, sys, csv
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coupled_morris import PARAMS, NAMES, PROBLEM

RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "results")
LO = np.array([p[1] for p in PARAMS]); HI = np.array([p[2] for p in PARAMS])
D = len(PARAMS); TS = D + 1

def main():
    X = np.loadtxt(os.path.join(RES, "morris_samples.csv"), delimiter=",", skiprows=1)
    Yr = list(csv.DictReader(open(os.path.join(RES, "morris_Y.csv"))))
    qois = list(Yr[0].keys())
    Y = {k: np.array([float(r[k]) if r[k] not in ("", "nan") else np.nan for r in Yr]) for k in qois}
    # PFOS concentration QoIs span orders of magnitude -> analyse in log10 space (the
    # paper's metric); baseflow is a normal-range flux -> keep linear.
    LOGQOI = {"instream_lower", "instream_mid", "gw_plume"}
    for k in qois:
        if k in LOGQOI:
            Y[k] = np.log10(np.clip(Y[k], 1e-6, None))
    Xn = (X - LO) / (HI - LO)                       # unit hypercube
    ntraj = X.shape[0] // TS
    rng = np.random.default_rng(7)

    for qoi in qois:
        y = Y[qoi]
        ee = {j: [] for j in range(D)}              # param index -> list of elementary effects
        for t in range(ntraj):
            s = t * TS
            for k in range(TS - 1):
                a, b = s + k, s + k + 1
                dx = Xn[b] - Xn[a]
                j = int(np.argmax(np.abs(dx)))      # the one param that changed
                if abs(dx[j]) < 1e-9:               # degenerate (shouldn't happen)
                    continue
                if np.isnan(y[a]) or np.isnan(y[b]):
                    continue                         # skip EEs touching a failed run
                ee[j].append((y[b] - y[a]) / dx[j])
        rows = []
        for j in range(D):
            e = np.array(ee[j])
            if len(e) == 0:
                rows.append((NAMES[j], 0.0, 0.0, 0.0, 0)); continue
            mu_star = float(np.mean(np.abs(e)))
            sigma = float(np.std(e, ddof=1)) if len(e) > 1 else 0.0
            # bootstrap 95% CI on mu*
            if len(e) > 2:
                boots = [np.mean(np.abs(rng.choice(e, len(e)))) for _ in range(2000)]
                conf = float(1.96 * np.std(boots))
            else:
                conf = 0.0
            rows.append((NAMES[j], mu_star, conf, sigma, len(e)))
        rows.sort(key=lambda r: -r[1])
        out = os.path.join(RES, f"morris_indices_{qoi}.csv")
        with open(out, "w") as f:
            f.write("param,mu_star,mu_star_conf,sigma,n_ee\n")
            for nm, ms, mc, sg, ne in rows:
                f.write(f"{nm},{ms:.6g},{mc:.6g},{sg:.6g},{ne}\n")
        top = [r[0] for r in rows[:5]]
        nee = int(np.median([r[4] for r in rows]))
        print(f"{qoi:16s} median EEs/param={nee:2d}  top5={top}")

if __name__ == "__main__":
    main()

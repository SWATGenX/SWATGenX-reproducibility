"""Self-contained MF6 static-head calibration driver (runs on EC2).

Calibrates the 3-layer Wellogic MF6 model bundled at ./model against obs_vs_sim.csv with
scipy differential_evolution (workers = all cores). 7 params: log10 multipliers on upper-/
lower-drift Kh and Kv, recharge multiplier, log10 drain- and river-conductance multipliers.
Objective = -NSE of topmost-active simulated head vs observed head (1-99 pctile trim).
Writes calibration_result.json.
"""
import os
import glob
import json
import shutil

import numpy as np
import pandas as pd
import flopy
from scipy.optimize import differential_evolution

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "model")
EXE = os.path.join(HERE, "bin", "mf6")
WORK = os.environ.get("CAL_WORK", "/mnt/cal_work")
NPROC = int(os.environ.get("CAL_NPROC", str(max(1, (os.cpu_count() or 2) - 2))))
OBS = pd.read_csv(os.path.join(M, "obs_vs_sim.csv"))
OBS = OBS[(OBS.obs_head_m > 150) & (OBS.obs_head_m < 500)].reset_index(drop=True)

SPEC = [("kh1", -1, 1, "p"), ("kh2", -1, 1, "p"), ("kv1", -1, 1, "p"), ("kv2", -1, 1, "p"),
        ("rch", 0.3, 2.0, "l"), ("drn", -2, 1, "p"), ("riv", -1, 1, "p"), ("ghb", -2, 2, "p")]
BOUNDS = [(s[1], s[2]) for s in SPEC]


def _mults(x):
    return {n: (10.0 ** v if k == "p" else float(v)) for (n, _, _, k), v in zip(SPEC, x)}


def _sim_topmost(h, idom, i, j, dry=1e29):
    for L in range(h.shape[0]):
        if idom[L, i, j] != 0 and abs(h[L, i, j]) < dry:
            return float(h[L, i, j])
    return np.nan


def _metrics(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    nse = 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)
    rmse = float(np.sqrt(np.mean((o - s) ** 2)))
    pbias = 100.0 * np.sum(s - o) / np.sum(o)
    r = float(np.corrcoef(o, s)[0, 1]); sd = np.std(s) / np.std(o); bd = s.mean() / o.mean()
    kge = 1 - np.sqrt((r - 1) ** 2 + (sd - 1) ** 2 + (bd - 1) ** 2)
    return dict(n=int(len(o)), NSE=round(float(nse), 4), RMSE=round(rmse, 3),
                PBIAS=round(float(pbias), 3), R2=round(r * r, 4), KGE=round(float(kge), 4))


def score(x, keep=False):
    m = _mults(x)
    ws = os.path.join(WORK, f"de_{os.getpid()}_{abs(hash(tuple(np.round(x, 6)))) % 10_000_000}")
    shutil.rmtree(ws, ignore_errors=True)
    try:
        sim = flopy.mf6.MFSimulation.load(sim_ws=M, exe_name=EXE, verbosity_level=0)
        sim.set_sim_path(ws)
        g = sim.get_model(); idom = g.dis.idomain.array
        k = g.npf.k.array.copy(); k33 = g.npf.k33.array.copy()
        k[0] *= m["kh1"]; k[1] *= m["kh2"]; k33[0] *= m["kv1"]; k33[1] *= m["kv2"]
        g.npf.k.set_data(k); g.npf.k33.set_data(k33)
        r = g.get_package("rcha_0") or g.get_package("rcha")
        r.recharge.set_data({0: r.recharge.get_data()[0] * m["rch"]})
        for pk, fac in (("drn_0", "drn"), ("riv_0", "riv"), ("ghb_bnd", "ghb")):
            p = g.get_package(pk)
            if p is None:
                continue
            spd = p.stress_period_data.get_data(0).copy()
            spd["cond"] = spd["cond"] * m[fac]
            p.stress_period_data.set_data({0: spd})
        sim.write_simulation(silent=True)
        ok, _ = sim.run_simulation(silent=True)
        if not ok:
            return 1e6
        h = flopy.utils.HeadFile(glob.glob(ws + "/*.hds")[0]).get_data()
        s = np.array([_sim_topmost(h, idom, int(rr.row), int(rr.col)) for rr in OBS.itertuples()])
        o = OBS.obs_head_m.to_numpy(); mm = np.isfinite(s) & np.isfinite(o)
        o, s = o[mm], s[mm]
        lo, hi = np.percentile(o, [1, 99]); ls, hs = np.percentile(s, [1, 99])
        kk = (o >= lo) & (o <= hi) & (s >= ls) & (s <= hs)
        met = _metrics(o[kk], s[kk])
        return met if keep else -met["NSE"]
    except Exception:
        return 1e6
    finally:
        if not keep:
            shutil.rmtree(ws, ignore_errors=True)


def main():
    os.makedirs(WORK, exist_ok=True)
    base = score([0, 0, 0, 0, 1.0, 0, 0, 0], keep=True)   # all multipliers = 1 (8 params)
    print(f"[cal] baseline {base}  nproc={NPROC}", flush=True)
    res = differential_evolution(score, BOUNDS, maxiter=40, popsize=15, tol=1e-4,
                                 mutation=(0.3, 1.0), recombination=0.8, seed=1,
                                 workers=NPROC, polish=False, disp=True, updating="deferred")
    met = score(res.x, keep=True)
    out = dict(baseline=base, calibrated=met,
               best_params={k: round(v, 5) for k, v in _mults(res.x).items()},
               raw_x=[round(float(v), 5) for v in res.x])
    with open(os.path.join(HERE, "calibration_result.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"[cal] DONE baseline NSE {base['NSE']} -> calibrated NSE {met['NSE']}", flush=True)
    print(json.dumps(out, indent=2), flush=True)


if __name__ == "__main__":
    main()

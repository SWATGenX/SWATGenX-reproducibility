"""Static-head calibration of the new 3-layer Wellogic MF6 model (04124500).

Parameters (7): log10 multipliers on upper-/lower-drift Kh and Kv, recharge multiplier,
and log10 multipliers on the surface-seepage drain conductance and the river conductance.
Objective = -NSE of topmost-active simulated head vs observed Wellogic heads (1-99 pctile
trim). Optimised with scipy differential_evolution (parallel). MF6 steady solve ~1-2 s.
"""
import os
import sys
import glob
import json
import shutil

import numpy as np
import pandas as pd
import flopy
from scipy.optimize import differential_evolution

sys.path.insert(0, "/data/SWATGenXApp/codes/MODGenX")
import mf6_head_calibration as C   # _sim_topmost, _metrics

M = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_250m"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
WORK = "/tmp/wlcal_de"
OBS = pd.read_csv(os.path.join(M, "obs_vs_sim.csv"))
OBS = OBS[(OBS.obs_head_m > 150) & (OBS.obs_head_m < 500)].reset_index(drop=True)

# name, lo, hi, kind  (pow10 -> multiplier 10**x)
SPEC = [("kh1", -1, 1, "p"), ("kh2", -1, 1, "p"), ("kv1", -1, 1, "p"), ("kv2", -1, 1, "p"),
        ("rch", 0.3, 2.0, "l"), ("drn", -2, 1, "p"), ("riv", -1, 1, "p")]
BOUNDS = [(s[1], s[2]) for s in SPEC]


def _mults(x):
    return {n: (10.0 ** v if k == "p" else float(v)) for (n, _, _, k), v in zip(SPEC, x)}


def score(x, tag=None, keep=False):
    m = _mults(x)
    # unique workspace per eval (parallel DE workers must not share a directory)
    tag = tag or f"de_{os.getpid()}_{abs(hash(tuple(np.round(x, 6)))) % 10_000_000}"
    ws = os.path.join(WORK, tag)
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
        for pk, fac in (("drn_0", "drn"), ("riv_0", "riv")):
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
        s = np.array([C._sim_topmost(h, idom, int(rr.row), int(rr.col)) for rr in OBS.itertuples()])
        o = OBS.obs_head_m.to_numpy(); mm = np.isfinite(s) & np.isfinite(o)
        o, s = o[mm], s[mm]
        lo, hi = np.percentile(o, [1, 99]); ls, hs = np.percentile(s, [1, 99])
        kk = (o >= lo) & (o <= hi) & (s >= ls) & (s <= hs)
        met = C._metrics(o[kk], s[kk])
        if keep:
            return met
        return -met["NSE"]
    except Exception:
        return 1e6
    finally:
        if not keep:
            shutil.rmtree(ws, ignore_errors=True)


def main():
    os.makedirs(WORK, exist_ok=True)
    base = score([0, 0, 0, 0, 1.0, 0, 0], tag="base", keep=True)
    print("BASELINE (uncalibrated):", base, flush=True)
    res = differential_evolution(score, BOUNDS, maxiter=18, popsize=12, tol=1e-3,
                                 mutation=(0.4, 1.0), recombination=0.8, seed=1,
                                 workers=8, polish=False, disp=True, updating="deferred")
    best = _mults(res.x)
    met = score(res.x, tag="best", keep=True)
    out = dict(baseline=base, calibrated=met,
               best_params={k: round(v, 4) for k, v in best.items()})
    with open(os.path.join(os.path.dirname(__file__), "calibration_result_04124500.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("CALIBRATED:", met, flush=True)
    print("BEST PARAMS:", out["best_params"], flush=True)


if __name__ == "__main__":
    main()

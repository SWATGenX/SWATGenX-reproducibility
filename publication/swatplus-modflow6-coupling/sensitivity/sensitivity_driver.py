#!/usr/bin/env python3
"""MODGenX convergence sensitivity sweep (runs on EC2).

Takes the smallest hard MODFLOW model (041000130106) and sweeps the factors suspected
to control convergence + fit, each as an independent MF6 run, in parallel:

  island_removal : keep all active cells  vs  keep only the largest connected component
                   (the suspected root cause: disconnected active islands mound)
  lake_pkg       : DRN (one-way, wet/dry discontinuity) vs GHB (smooth two-way)
  cond_cap       : lake conductance cap {1e3,1e4,1e5,1e6, none}
  under_relax    : DBD under-relaxation on/off
  outer_dvclose  : head-change tolerance {1cm, 5cm}

Records per run: converged?, outer iterations, mass-balance %, and obs-vs-sim NSE/RMSE
against the same wells (obs_vs_sim.csv shipped with the model). Output: results.csv.
"""
import os, glob, shutil, itertools, csv, re
import numpy as np, pandas as pd, flopy
from scipy import ndimage
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "model")                 # base MF6 model (GHB lakes)
EXE  = os.path.join(HERE, "bin", "mf6")
WORK = os.environ.get("SENS_WORK", "/mnt/sens_work")
OBS  = pd.read_csv(os.path.join(BASE, "obs_vs_sim.csv"))   # row, col, obs_head_m
NPROC = int(os.environ.get("SENS_NPROC", str(max(1, (os.cpu_count() or 2) - 2))))

FACTORS = dict(
    island=["keep_all", "largest_component"],
    lake=["drn", "ghb"],
    cap=[1e3, 1e4, 1e5, 1e6, 1e30],
    relax=["dbd", "none"],
    dvclose=[1e-2, 5e-2],
)

def metrics(o, s):
    o, s = np.asarray(o, float), np.asarray(s, float)
    nse = 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)
    rmse = float(np.sqrt(np.mean((o - s) ** 2)))
    return round(float(nse), 3), round(rmse, 2)

def sim_at(h, idom, i, j):
    for k in range(h.shape[0]):
        if (k >= idom.shape[0] or idom[k, i, j] != 0) and abs(h[k, i, j]) < 1e6:
            return float(h[k, i, j])
    return np.nan

def largest_component(idomain):
    """Set all but the largest connected active component to inactive (per the full 3D
    active footprint, projected: keep cells whose column belongs to the biggest 2D blob)."""
    act2d = (idomain != 0).any(axis=0).astype(int)
    lab, n = ndimage.label(act2d)
    if n <= 1:
        return idomain, 0
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    keep = sizes.argmax()
    drop_mask = (lab != keep) & (act2d == 1)
    out = idomain.copy()
    out[:, drop_mask] = 0
    return out, int(drop_mask.sum())

def run_one(combo):
    island, lake, cap, relax, dvclose = combo
    tag = f"{island}_{lake}_cap{cap:.0e}_{relax}_dv{dvclose:.0e}"
    ws = os.path.join(WORK, tag)
    try:
        shutil.rmtree(ws, ignore_errors=True)
        sim = flopy.mf6.MFSimulation.load(sim_ws=BASE, exe_name=EXE, verbosity_level=0)
        sim.set_sim_path(ws)
        gwf = sim.get_model()
        # base lake cells live in the GHB package (model on disk is GHB)
        ghb = gwf.get_package("GHB_0")
        lake_spd = ghb.stress_period_data.get_data(0)
        cells = [tuple(r["cellid"]) for r in lake_spd]
        bhead = [float(r["bhead"]) for r in lake_spd]
        cond = [min(float(r["cond"]), cap) for r in lake_spd]
        gwf.remove_package("GHB_0")

        # idomain pruning
        idom = gwf.dis.idomain.array.copy()
        ndrop = 0
        if island == "largest_component":
            idom, ndrop = largest_component(idom)
            gwf.dis.idomain = idom
            # pruning inactivates cells -> re-filter EVERY existing list boundary to active
            # cells (MF6 rejects boundaries on inactive cells).
            for pk, flds in [("RIV_0", ["stage", "cond", "rbot"]), ("WEL_0", ["q"]),
                             ("CHD_0", ["head"])]:
                p = gwf.get_package(pk)
                if p is None:
                    continue
                spd = p.stress_period_data.get_data(0)
                kept = [[tuple(r["cellid"])] + [float(r[f]) for f in flds]
                        for r in spd if idom[tuple(r["cellid"])] != 0]
                p.stress_period_data.set_data({0: kept if kept else None})

        def cell_active(c):
            return idom[c[0], c[1], c[2]] != 0
        lk = [(c, b, co) for c, b, co in zip(cells, bhead, cond) if cell_active(c)]
        if lake == "ghb":
            flopy.mf6.ModflowGwfghb(gwf, stress_period_data=[[c, b, co] for c, b, co in lk])
        else:
            flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=[[c, b, co] for c, b, co in lk])

        # solver
        ims = [p for p in sim.sim_package_list if "Ims" in type(p).__name__][0]
        ims.outer_dvclose.set_data(dvclose); ims.inner_dvclose.set_data(dvclose / 10)
        ims.outer_maximum.set_data(500)
        ims.under_relaxation.set_data("dbd" if relax == "dbd" else "none")

        sim.write_simulation(silent=True)
        ok, _ = sim.run_simulation(silent=True)
        lstf = [f for f in os.listdir(ws) if f.endswith(".lst") and "sim" not in f]
        mb, nouter, nse, rmse = None, None, None, None
        if lstf:
            txt = open(os.path.join(ws, lstf[0])).read()
            d = re.findall(r"PERCENT DISCREPANCY\s*=\s*([-\d.]+)", txt)
            mb = float(d[-1]) if d else None
        hf = glob.glob(os.path.join(ws, "*.hds"))
        if ok and hf:
            h = flopy.utils.HeadFile(hf[0]).get_data()
            s = [sim_at(h, idom, int(r.row), int(r.col)) for r in OBS.itertuples()]
            s = np.array(s); m = np.isfinite(s)
            if m.sum() >= 3:
                nse, rmse = metrics(OBS.obs_head_m[m], s[m])
        shutil.rmtree(ws, ignore_errors=True)
        return dict(island=island, lake=lake, cap=cap, relax=relax, dvclose=dvclose,
                    islands_dropped=ndrop, converged=bool(ok), mass_balance=mb, nse=nse, rmse=rmse)
    except Exception as e:
        shutil.rmtree(ws, ignore_errors=True)
        return dict(island=island, lake=lake, cap=cap, relax=relax, dvclose=dvclose,
                    converged=False, error=str(e)[:120])

def main():
    os.makedirs(WORK, exist_ok=True)
    combos = list(itertools.product(*FACTORS.values()))
    print(f"[sens] {len(combos)} combinations, nproc={NPROC}", flush=True)
    with Pool(NPROC) as pool:
        rows = pool.map(run_one, combos)
    keys = ["island", "lake", "cap", "relax", "dvclose", "islands_dropped",
            "converged", "mass_balance", "nse", "rmse", "error"]
    with open(os.path.join(HERE, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})
    nconv = sum(1 for r in rows if r.get("converged"))
    print(f"[sens] done: {nconv}/{len(rows)} converged. results.csv written.", flush=True)

if __name__ == "__main__":
    main()

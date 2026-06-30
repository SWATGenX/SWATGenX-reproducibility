"""Freeze the calibrated steady-state GWF model.

Takes the PEST++ ies posterior (control.3.par.csv), picks the realization at the observed
baseflow (~0.63 m3/s gaining, head-positive), applies its parameters (pilot-point K + globals
+ pump + per-order channel incision) to the as-built MF6 model, and writes a persistent
calibrated model dir (MODFLOW_wl_cal). This is the flow field Phase 3 (PFAS-GWT) runs on.
"""
import os
import sys
import glob
import shutil
import numpy as np
import pandas as pd
import flopy

PEST = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/pest"
SRC = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_250m"
CAL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_cal"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
W = np.load(f"{PEST}/interp_W.npz"); WMAT, ACT_LIN, NROW, NCOL = W["W"], W["act_lin"], int(W["nrow"]), int(W["ncol"])
RR = np.load(f"{PEST}/riv_cell_group.npz"); RIV_ROW, RIV_COL, RIV_GRP = RR["riv_row"], RR["riv_col"], RR["riv_grp"]
OBS = pd.read_csv(f"{PEST}/obs_wells.csv")


def pick_realization():
    sim = pd.read_csv(f"{PEST}/aws_results/control.3.obs.csv", index_col=0)
    bf = sim["baseflow"]
    cand = bf[(bf > -9000)]
    real = (cand - 0.63).abs().idxmin()
    par = pd.read_csv(f"{PEST}/aws_results/control.3.par.csv", index_col=0).loc[real]
    return real, par, float(bf.loc[real])


def apply_and_save(par):
    shutil.rmtree(CAL, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=SRC, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(CAL)
    g = sim.get_model(); idom = g.dis.idomain.array; top = g.dis.top.array; botm = g.dis.botm.array
    nlay = botm.shape[0]
    pp = par[[c for c in par.index if c.startswith("pp_")]].to_numpy(float)
    khmult = np.ones(NROW * NCOL); khmult[ACT_LIN] = np.exp((WMAT @ pp) * np.log(10.0))
    khmult = khmult.reshape(NROW, NCOL)
    k = g.npf.k.array.copy(); k33 = g.npf.k33.array.copy(); kvm = 10.0 ** float(par["kv"])
    for L in (0, 1):
        k[L] *= khmult; k33[L] *= khmult * kvm
    g.npf.k.set_data(k); g.npf.k33.set_data(k33)
    r = g.get_package("rcha_0"); r.recharge.set_data({0: r.recharge.get_data()[0] * float(par["rch"])})
    w = g.get_package("wel_0")
    if w is not None:
        sp = w.stress_period_data.get_data(0).copy(); sp["q"] *= 10.0 ** float(par["pump"]); w.stress_period_data.set_data({0: sp})
    for pk, nm in (("drn_0", "drn"), ("riv_0", "riv"), ("ghb_bnd", "ghb")):
        p = g.get_package(pk)
        if p is None:
            continue
        sp = p.stress_period_data.get_data(0).copy(); sp["cond"] *= 10.0 ** float(par[nm]); p.stress_period_data.set_data({0: sp})
    # per-order incision
    st = par[[c for c in par.index if c.startswith("st_g")]].to_numpy(float)
    off = {(int(i), int(j)): st[gp] for i, j, gp in zip(RIV_ROW, RIV_COL, RIV_GRP)}
    rp = g.get_package("riv_0"); sp = rp.stress_period_data.get_data(0).copy()
    for row in sp:
        i, j = int(row["cellid"][1]), int(row["cellid"][2]); o = off.get((i, j), 0.0)
        rb = top[i, j] - o - 2.0; L = 0
        for c in range(nlay):
            if idom[c, i, j] == 0:
                continue
            L = c
            if rb >= botm[c, i, j]:
                break
        rb = max(rb, float(botm[L, i, j]) + 0.2); ct = top[i, j] if L == 0 else botm[L - 1, i, j]
        row["cellid"] = (L, i, j); row["rbot"] = rb; row["stage"] = min(max(top[i, j] - o, rb + 0.2), ct - 0.1)
    rp.stress_period_data.set_data({0: sp})
    sim.write_simulation(silent=True)
    ok, _ = sim.run_simulation(silent=True)
    return ok, g


def main():
    real, par, bf = pick_realization()
    print(f"calibrated realization {real}: baseflow {bf:.3f} m3/s")
    ok, g = apply_and_save(par)
    par.to_csv(f"{CAL}/calibrated_params.csv")
    print(f"calibrated GWF written to {CAL}; converged={ok}")
    if ok:
        idom = g.dis.idomain.array
        h = flopy.utils.HeadFile(glob.glob(f"{CAL}/*.hds")[0]).get_data()
        s = []
        for o in OBS.itertuples():
            for L in range(h.shape[0]):
                if idom[L, int(o.row), int(o.col)] != 0 and abs(h[L, int(o.row), int(o.col)]) < 1e29:
                    s.append(h[L, int(o.row), int(o.col)]); break
            else:
                s.append(np.nan)
        s = np.array(s); oh = OBS.obs_head_m.to_numpy(); m = np.isfinite(s)
        nse = 1 - np.sum((oh[m] - s[m]) ** 2) / np.sum((oh[m] - oh[m].mean()) ** 2)
        print(f"  head NSE {nse:.3f}, RMSE {np.sqrt(np.mean((oh[m]-s[m])**2)):.2f} m")


if __name__ == "__main__":
    main()

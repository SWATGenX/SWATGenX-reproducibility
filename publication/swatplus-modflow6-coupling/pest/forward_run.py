"""PEST++ forward model for the 04124500 MF6 static-head + baseflow calibration.

Reads the parameter file written by PEST (params.dat: pilot-point log10-Kh-multipliers
pp_0001.. plus global multipliers kv/rch/drn/riv/ghb), builds a smooth Kh-multiplier field
by kernel-interpolating the pilot points onto the grid (weights W precomputed in setup),
applies it to a pristine copy of the MF6 model, runs MF6, and writes the observations PEST
reads (obs.dat): simulated head at each Wellogic well + the net GW->stream baseflow (m3/s).

Pilot points + kriging-style interpolation replace blocky zonal multipliers; the baseflow
observation adds the flux constraint that head-only calibration lacks.
"""
import os
import glob
import shutil

import numpy as np
import pandas as pd
import flopy

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "model")                 # pristine MF6 model
EXE = os.path.join(HERE, "bin", "mf6")
W = np.load(os.path.join(HERE, "interp_W.npz"))        # cell<-pp kernel weights + active mask
WMAT, ACT_LIN, NROW, NCOL = W["W"], W["act_lin"], int(W["nrow"]), int(W["ncol"])
OBS = pd.read_csv(os.path.join(HERE, "obs_wells.csv")) # row,col,obs_head_m
RR = np.load(os.path.join(HERE, "riv_cell_group.npz")) # per-RIV-cell stream-order group
RIV_ROW, RIV_COL, RIV_GRP = RR["riv_row"], RR["riv_col"], RR["riv_grp"]
WORK = os.environ.get("FR_WORK", os.path.join(HERE, "_run"))


def _sim_topmost(h, idom, i, j, dry=1e29):
    for L in range(h.shape[0]):
        if idom[L, i, j] != 0 and abs(h[L, i, j]) < dry:
            return float(h[L, i, j])
    return np.nan


def riv_baseflow(head, idom, riv_spd):
    """Net GW->stream baseflow (m3/s, positive = gaining)."""
    q = 0.0
    for r in riv_spd:
        k, i, j = r["cellid"]
        if idom[k, i, j] == 0:
            continue
        h = head[k, i, j]
        if abs(h) > 1e29:
            continue
        q += float(r["cond"]) * (float(r["stage"]) - max(h, float(r["rbot"])))  # >0 into aquifer
    return -q / 86400.0                                # flip sign: + = GW->stream


def main():
    p = pd.read_csv(os.path.join(HERE, "params.dat"), sep=r"\s+", header=None,
                    names=["name", "val"]).set_index("name")["val"]
    pp = p[[n for n in p.index if n.startswith("pp_")]].to_numpy(float)   # log10 Kh-mult at points
    # kernel-interpolate pilot points -> per-cell Kh multiplier (log space -> exp)
    cell_logmult = WMAT @ pp                            # (nactive,)
    khmult = np.ones(NROW * NCOL)
    khmult[ACT_LIN] = np.exp(cell_logmult * np.log(10.0))
    khmult = khmult.reshape(NROW, NCOL)

    shutil.rmtree(WORK, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=TEMPLATE, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(WORK)
    g = sim.get_model(); idom = g.dis.idomain.array
    riv_spd = g.get_package("riv_0").stress_period_data.get_data(0)

    k = g.npf.k.array.copy(); k33 = g.npf.k33.array.copy()
    kvm = 10.0 ** float(p["kv"])
    for L in (0, 1):                                   # both drift layers share the pp field
        k[L] *= khmult; k33[L] *= khmult * kvm
    g.npf.k.set_data(k); g.npf.k33.set_data(k33)
    r = g.get_package("rcha_0") or g.get_package("rcha")
    r.recharge.set_data({0: r.recharge.get_data()[0] * float(p["rch"])})
    # pumping: WEL q is built from PMP_CPCITY (pump CAPACITY); scale to actual long-term
    # average withdrawal (a major sink ~half the baseflow -- capacity overestimates it).
    wel = g.get_package("wel_0")
    if wel is not None and "pump" in p.index:
        spd_w = wel.stress_period_data.get_data(0).copy()
        spd_w["q"] = spd_w["q"] * (10.0 ** float(p["pump"]))
        wel.stress_period_data.set_data({0: spd_w})
    for pk, nm in (("drn_0", "drn"), ("riv_0", "riv"), ("ghb_bnd", "ghb")):
        pk_o = g.get_package(pk)
        if pk_o is None:
            continue
        spd = pk_o.stress_period_data.get_data(0).copy()
        spd["cond"] = spd["cond"] * (10.0 ** float(p[nm]))
        pk_o.stress_period_data.set_data({0: spd})

    # per-reach channel incision: stage = top - st_offset[reach], rbot = stage - 2 (the missing
    # degree of freedom -- streams at 250 m sit below the cell-mean surface so they can gain).
    st = p[[n for n in p.index if n.startswith("st_g")]].to_numpy(float)  # metres, by order group
    top = g.dis.top.array
    botm = g.dis.botm.array                           # (nlay,nrow,ncol)
    nlay = botm.shape[0]
    off = {(int(i), int(j)): st[gp] for i, j, gp in zip(RIV_ROW, RIV_COL, RIV_GRP)}
    rp = g.get_package("riv_0")
    spd = rp.stress_period_data.get_data(0).copy()
    for row in spd:
        i, j = int(row["cellid"][1]), int(row["cellid"][2])
        o = off.get((i, j), 0.0)
        rb = float(top[i, j]) - o - 2.0               # incised channel bottom
        # place the RIV in the active layer that CONTAINS rb (so deep incision puts the
        # stream in layer 1/2 -- where its bottom is above that cell's bottom -- instead of
        # being clamped into the thin layer 0; this lets a reach incise below the water table
        # and actually gain).
        L = 0
        for cand in range(nlay):
            if idom[cand, i, j] == 0:
                continue
            L = cand
            if rb >= float(botm[cand, i, j]):         # rb sits within this layer
                break
        rb = max(rb, float(botm[L, i, j]) + 0.2)
        cell_top = float(top[i, j]) if L == 0 else float(botm[L - 1, i, j])
        row["cellid"] = (L, i, j)
        row["rbot"] = rb
        row["stage"] = min(max(float(top[i, j]) - o, rb + 0.2), cell_top - 0.1)
    rp.stress_period_data.set_data({0: spd})

    sim.write_simulation(silent=True)
    ok, _ = sim.run_simulation(silent=True)
    sim_head = np.full(len(OBS), -9999.0)
    bf = -9999.0
    if ok:
        h = flopy.utils.HeadFile(glob.glob(os.path.join(WORK, "*.hds"))[0]).get_data()
        sim_head = np.array([_sim_topmost(h, idom, int(o.row), int(o.col)) for o in OBS.itertuples()])
        sim_head = np.where(np.isfinite(sim_head), sim_head, -9999.0)
        bf = riv_baseflow(h, idom, spd)            # modified RIV (calibrated stage + cond)

    with open(os.path.join(HERE, "obs.dat"), "w") as f:
        for i, v in enumerate(sim_head):
            f.write(f"h_{i:04d} {v:.4f}\n")
        f.write(f"baseflow {bf:.5f}\n")
    shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()

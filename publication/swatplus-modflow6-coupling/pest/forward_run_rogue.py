"""PEST++ forward model for the Rogue (04118500) SFR-based MF6 head + baseflow calibration.

Reads params.dat (pilot-point log10 Kh multipliers + globals kv/rch/drn/ghb/pump/sfrk), applies the
continuous-bedrock conditioning + the parameters to a pristine copy of the SFR model, runs MF6, and
writes obs.dat (simulated head at each obs cell + the net GW->stream baseflow from the SFR budget).
"""
import os
import glob
import shutil
import numpy as np
import pandas as pd
import flopy

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "model")
EXE = os.path.join(HERE, "bin", "mf6")
W = np.load(os.path.join(HERE, "interp_W.npz"))
WMAT, ACT_LIN, NROW, NCOL = W["W"], W["act_lin"], int(W["nrow"]), int(W["ncol"])
OBS = pd.read_csv(os.path.join(HERE, "obs_wells.csv"))
WORK = os.environ.get("FR_WORK", os.path.join(HERE, "_run"))
BEDROCK_THICK = 20.0


def _sim_topmost(h, idom, i, j, dry=1e29):
    for L in range(h.shape[0]):
        if idom[L, i, j] != 0 and abs(h[L, i, j]) < dry:
            return float(h[L, i, j])
    return np.nan


def sfr_baseflow(ws):
    cbc = flopy.utils.CellBudgetFile(glob.glob(os.path.join(ws, "*.sfr.cbc"))[0])
    rec = cbc.get_data(text="GWF")[-1]
    q = rec["q"] if rec.dtype.names else np.array([r[2] for r in rec])
    return float(np.sum(q)) / 86400.0


def main():
    p = pd.read_csv(os.path.join(HERE, "params.dat"), sep=r"\s+", header=None,
                    names=["name", "val"]).set_index("name")["val"]
    pp = p[[n for n in p.index if n.startswith("pp_")]].to_numpy(float)
    khmult = np.ones(NROW * NCOL)
    khmult[ACT_LIN] = np.exp((WMAT @ pp) * np.log(10.0))
    khmult = khmult.reshape(NROW, NCOL)

    shutil.rmtree(WORK, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=TEMPLATE, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(WORK)
    g = sim.get_model()
    dis = g.dis; idom = dis.idomain.array.copy(); botm = dis.botm.array.copy()
    # continuous bedrock conditioning (layer 2 active under every active column)
    idom[2] = np.where(idom[1] != 0, 1, idom[2])
    botm[2] = np.where(idom[1] != 0, botm[1] - BEDROCK_THICK, botm[2])
    dis.idomain.set_data(idom); dis.botm.set_data(botm)

    k = g.npf.k.array.copy(); k33 = g.npf.k33.array.copy()
    kvm = 10.0 ** float(p["kv"])
    for Ly in (0, 1):
        k[Ly] *= khmult; k33[Ly] *= khmult * kvm
    g.npf.k.set_data(k); g.npf.k33.set_data(k33)
    r = g.get_package("rcha_0"); r.recharge.set_data({0: r.recharge.get_data()[0] * (10.0 ** float(p["rch"]))})
    wel = g.get_package("wel_0")
    if wel is not None:
        sp = wel.stress_period_data.get_data(0).copy(); sp["q"] *= 10.0 ** float(p["pump"])
        wel.stress_period_data.set_data({0: sp})
    for pk, nm in (("drn_0", "drn"), ("ghb_bnd", "ghb")):
        pkg = g.get_package(pk)
        if pkg is not None:
            sp = pkg.stress_period_data.get_data(0).copy(); sp["cond"] *= 10.0 ** float(p[nm])
            pkg.stress_period_data.set_data({0: sp})
    sfr = g.get_package("sfr_0")
    pdd = sfr.packagedata.get_data().copy(); pdd["rhk"] *= 10.0 ** float(p["sfrk"])
    sfr.packagedata.set_data(pdd)

    sim.write_simulation(silent=True)
    ok, _ = sim.run_simulation(silent=True)
    sim_head = np.full(len(OBS), -9999.0); bf = -9999.0
    if ok:
        h = flopy.utils.HeadFile(glob.glob(os.path.join(WORK, "*.hds"))[0]).get_data()
        sim_head = np.array([_sim_topmost(h, idom, int(o.row), int(o.col)) for o in OBS.itertuples()])
        sim_head = np.where(np.isfinite(sim_head), sim_head, -9999.0)
        try:
            bf = sfr_baseflow(WORK)
        except Exception:
            bf = -9999.0
    with open(os.path.join(HERE, "obs.dat"), "w") as f:
        for i, v in enumerate(sim_head):
            f.write(f"h_{i:04d} {v:.4f}\n")
        f.write(f"baseflow {bf:.5f}\n")
    shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    main()

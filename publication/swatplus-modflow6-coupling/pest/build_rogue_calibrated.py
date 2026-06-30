"""Apply the PEST++ posterior to build the calibrated Rogue SFR GWF (MODFLOW_sfr_cal).

Picks the head+baseflow-matched realization from the ies posterior (control.3.par.csv) and applies
its parameters (pilot-point Kh + globals kv/rch/drn/ghb/pump/sfrk) + continuous-bedrock conditioning
to the as-built MODFLOW_sfr, writing the calibrated flow field the Rogue GW-PFAS transport runs on.
"""
import os
import glob
import shutil
import numpy as np
import pandas as pd
import flopy

HERE = os.path.dirname(os.path.abspath(__file__))
RDIR = os.path.join(HERE, "rogue")
ROGUE = os.environ.get(
    "SWATGENX_ROGUE_DIR",
    "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500",
)
SRC = f"{ROGUE}/MODFLOW_sfr"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
REAL = "8"             # posterior realization: head NSE 0.909, baseflow 5.46 m3/s
BEDROCK_THICK = 20.0
W = np.load(f"{RDIR}/interp_W.npz")
WMAT, ACT_LIN, NROW, NCOL = W["W"], W["act_lin"], int(W["nrow"]), int(W["ncol"])
OBS = pd.read_csv(f"{RDIR}/obs_wells.csv")


def main():
    par = pd.read_csv(f"{RDIR}/control.3.par.csv", index_col=0).loc[REAL]
    pp = par[[c for c in par.index if c.startswith("pp_")]].to_numpy(float)
    khmult = np.ones(NROW * NCOL); khmult[ACT_LIN] = np.exp((WMAT @ pp) * np.log(10.0))
    khmult = khmult.reshape(NROW, NCOL)

    shutil.rmtree(CAL, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=SRC, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(CAL)
    g = sim.get_model()
    dis = g.dis; idom = dis.idomain.array.copy(); botm = dis.botm.array.copy()
    idom[2] = np.where(idom[1] != 0, 1, idom[2])
    botm[2] = np.where(idom[1] != 0, botm[1] - BEDROCK_THICK, botm[2])
    dis.idomain.set_data(idom); dis.botm.set_data(botm)
    k = g.npf.k.array.copy(); k33 = g.npf.k33.array.copy(); kvm = 10.0 ** float(par["kv"])
    for L in (0, 1):
        k[L] *= khmult; k33[L] *= khmult * kvm
    g.npf.k.set_data(k); g.npf.k33.set_data(k33)
    r = g.get_package("rcha_0"); r.recharge.set_data({0: r.recharge.get_data()[0] * 10.0 ** float(par["rch"])})
    w = g.get_package("wel_0")
    if w is not None:
        sp = w.stress_period_data.get_data(0).copy(); sp["q"] *= 10.0 ** float(par["pump"])
        w.stress_period_data.set_data({0: sp})
    for pk, nm in (("drn_0", "drn"), ("ghb_bnd", "ghb")):
        p = g.get_package(pk)
        if p is not None:
            sp = p.stress_period_data.get_data(0).copy(); sp["cond"] *= 10.0 ** float(par[nm])
            p.stress_period_data.set_data({0: sp})
    sfr = g.get_package("sfr_0"); pdd = sfr.packagedata.get_data().copy()
    pdd["rhk"] *= 10.0 ** float(par["sfrk"]); sfr.packagedata.set_data(pdd)
    sim.write_simulation(silent=True)
    ok, _ = sim.run_simulation(silent=True)
    par.to_csv(f"{CAL}/calibrated_params.csv")
    # report
    cbc = flopy.utils.CellBudgetFile(glob.glob(f"{CAL}/*.sfr.cbc")[0])
    rec = cbc.get_data(text="GWF")[-1]
    q = rec["q"] if rec.dtype.names else np.array([rr[2] for rr in rec])
    bf = float(np.sum(q)) / 86400.0
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
    print(f"calibrated Rogue GWF (real {REAL}): converged={ok}, baseflow={bf:+.3f} m3/s, "
          f"head NSE={nse:.3f}, RMSE={np.sqrt(np.mean((oh[m]-s[m])**2)):.2f} m -> {CAL}")


if __name__ == "__main__":
    main()

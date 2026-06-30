"""Condition + calibrate the Rogue (04118500) SFR-based MF6 flow field for the integrated paper.

The automated MODGenX build produced a complete Rogue MF6+SFR model (1506 reaches, 24887 cells)
but it did not converge as-built: (i) raw Wellogic WEL uses pump CAPACITY, which over-pumps a
heavily-developed (Grand Rapids) basin; (ii) the seepage drain over-drains; (iii) the bedrock
layer was patchy (1433/11727 columns), oscillating the steady-state Newton solve. We apply the
generalization recipe established here:
  - continuous bedrock layer (active under every column, uniform 20 m)  [now also in build code]
  - WEL scaled to a fraction of pump capacity (actual long-term withdrawal << capacity)
  - softened seepage-drain conductance
then sweep the SFR streambed K to match the observed gaining baseflow (USGS 04118500: mean flow
7.51 m3/s, Lyne-Hollick BFI 0.74 -> baseflow ~5.56 m3/s). Writes MODFLOW_sfr_cal, the flow field
the Rogue GW-PFAS transport runs on.
"""
import os
import glob
import shutil
import re
import numpy as np
import flopy

M = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
SRC = f"{M}/MODFLOW_sfr"
CAL = f"{M}/MODFLOW_sfr_cal"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
BASEFLOW_TARGET = 5.56          # m3/s gaining (USGS 04118500, BFI 0.74)
WEL_SCALE = 0.15               # actual withdrawal ~15% of Wellogic pump capacity
DRN_SCALE = 0.05               # softened seepage drain
GHB_SCALE = 0.1               # near-no-flow watershed-divide perimeter (a topographic divide IS
                              # a groundwater flow divide; a leaky GHB exports baseflow out the sides)
BED_K = 0.5                   # streambed K (baseflow saturates in bed_k -> recharge is the lever)
BEDROCK_THICK = 20.0
# baseflow is supply-limited (recharge), not streambed-limited: sweep the recharge multiplier.
# (RCHAx1.8/GHBx0.1 -> 5.76; x1.4 -> 4.23; observed target 5.56 m3/s.)


def sfr_baseflow(ws, name):
    cbc = flopy.utils.CellBudgetFile(glob.glob(f"{ws}/*.sfr.cbc")[0])
    rec = cbc.get_data(text="GWF")[-1]
    q = rec["q"] if rec.dtype.names else np.array([r[2] for r in rec])
    return float(np.sum(q)) / 86400.0          # + = GW->stream (gaining)


def build(rch_mult):
    shutil.rmtree(CAL, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=SRC, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(CAL)
    g = sim.get_model()
    dis = g.dis; idom = dis.idomain.array.copy(); botm = dis.botm.array.copy()
    # continuous bedrock: layer 2 active under every active column, uniform thickness
    idom[2] = np.where(idom[1] != 0, 1, idom[2])
    botm[2] = np.where(idom[1] != 0, botm[1] - BEDROCK_THICK, botm[2])
    dis.idomain.set_data(idom); dis.botm.set_data(botm)
    # pumping realism + softened drain + near-no-flow divide perimeter
    w = g.get_package("wel_0"); sp = w.stress_period_data.get_data(0).copy()
    sp["q"] *= WEL_SCALE; w.stress_period_data.set_data({0: sp})
    d = g.get_package("drn_0"); sp = d.stress_period_data.get_data(0).copy()
    sp["cond"] *= DRN_SCALE; d.stress_period_data.set_data({0: sp})
    gh = g.get_package("ghb_bnd"); sp = gh.stress_period_data.get_data(0).copy()
    sp["cond"] *= GHB_SCALE; gh.stress_period_data.set_data({0: sp})
    sfr = g.get_package("sfr_0"); pd_ = sfr.packagedata.get_data().copy()
    pd_["rhk"] = BED_K; sfr.packagedata.set_data(pd_)
    # recharge multiplier = the baseflow lever (supply-limited)
    r = g.get_package("rcha_0"); r.recharge.set_data({0: r.recharge.get_data()[0] * rch_mult})
    sim.write_simulation(silent=True)
    ok, _ = sim.run_simulation(silent=True)
    return ok, g.name


def head_nse(ws):
    f = glob.glob(f"{SRC}/obs_vs_sim.csv")
    if not f:
        return None
    import pandas as pd
    obs = pd.read_csv(f[0])
    if "obs_head_m" not in obs.columns:
        return None
    h = flopy.utils.HeadFile(glob.glob(f"{ws}/*.hds")[0]).get_data()
    g = flopy.mf6.MFSimulation.load(sim_ws=ws, verbosity_level=0).get_model()
    idom = g.dis.idomain.array; s = []
    for o in obs.itertuples():
        for L in range(h.shape[0]):
            if idom[L, int(o.row), int(o.col)] != 0 and abs(h[L, int(o.row), int(o.col)]) < 1e29:
                s.append(h[L, int(o.row), int(o.col)]); break
        else:
            s.append(np.nan)
    s = np.array(s); oh = obs.obs_head_m.to_numpy(); m = np.isfinite(s)
    return 1 - np.sum((oh[m] - s[m]) ** 2) / np.sum((oh[m] - oh[m].mean()) ** 2)


def main():
    best = None
    for rch in (1.0, 1.4, 1.7, 2.0):
        ok, name = build(rch)
        if not ok:
            print(f"rch x{rch}: did NOT converge"); continue
        bf = sfr_baseflow(CAL, name); nse = head_nse(CAL)
        print(f"rch x{rch}: converged baseflow={bf:+.3f} m3/s (target {BASEFLOW_TARGET}) "
              f"head_NSE={nse if nse is None else round(nse, 3)}")
        if best is None or abs(bf - BASEFLOW_TARGET) < abs(best[1] - BASEFLOW_TARGET):
            best = (rch, bf)
    if best is None:
        print("Rogue SFR never converged"); return
    rch, bf = best
    print(f"\nselected rch x{rch} (baseflow {bf:+.3f} m3/s); final MODFLOW_sfr_cal")
    ok, name = build(rch)
    np.savez(f"{M}/rogue_sfr_meta.npz", rch_mult=rch, baseflow=bf, bed_k=BED_K,
             wel_scale=WEL_SCALE, drn_scale=DRN_SCALE, ghb_scale=GHB_SCALE)
    print(f"final: converged={ok}, baseflow={sfr_baseflow(CAL, name):+.3f} m3/s")


if __name__ == "__main__":
    main()

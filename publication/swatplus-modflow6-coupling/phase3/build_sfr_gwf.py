"""Replace RIV with SFR on the calibrated steady-state GWF (04124500).

Takes the calibrated flow field (MODFLOW_wl_cal -- calibrated K/recharge/GHB/pump), removes the
RIV package, and attaches a topologically-connected SFR network built from the SWAT+ channel
graph (sfr_builder). SFR routes streamflow through the reach network and exchanges with GW
head-dependently -- unlike RIV it can carry solute downstream (via SFT in Phase 3).

A short 1-parameter search on the streambed K (rhk) restores the observed gaining baseflow
(~0.63 m3/s); the calibrated aquifer K field is reused unchanged. Writes MODFLOW_wl_cal_sfr,
the flow field the SFR-based Phase 3 PFAS transport runs on.
"""
import os
import sys
import glob
import shutil
import numpy as np
import flopy

sys.path.insert(0, "/data/SWATGenXApp/codes/MODGenX")
from MODGenX.sfr_builder import build_sfr_network

MODEL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500"
CAL = f"{MODEL}/MODFLOW_wl_cal"
SFR = f"{MODEL}/MODFLOW_wl_cal_sfr"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
RIVS = glob.glob(f"{MODEL}/SWAT_MODEL_Web_Application/Watershed/Shapes/rivs1.shp")[0]
GRID = f"{MODEL}/MODFLOW_wl_250m/Grids_MODFLOW.geojson"
BASEFLOW_TARGET = 0.63          # m3/s gaining (USGS 04124500)
import pandas as pd
OBS = pd.read_csv("/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/pest/obs_wells.csv")


def sfr_baseflow(ws, name):
    """Net GW->stream flux (m3/s, + = gaining) from the SFR budget GWF term."""
    cbc = flopy.utils.CellBudgetFile(f"{ws}/{name}.sfr.cbc")
    rec = cbc.get_data(text="GWF")[-1]
    # SFR 'GWF' term: q is flow from GWF into the reach; sum>0 = net gaining
    q = np.array([r[2] for r in rec]) if rec.dtype.names is None else rec["q"]
    return float(np.sum(q)) / 86400.0


def head_nse(ws, name):
    h = flopy.utils.HeadFile(glob.glob(f"{ws}/*.hds")[0]).get_data()
    g = flopy.mf6.MFSimulation.load(sim_ws=ws, verbosity_level=0).get_model()
    idom = g.dis.idomain.array
    s = []
    for o in OBS.itertuples():
        for L in range(h.shape[0]):
            if idom[L, int(o.row), int(o.col)] != 0 and abs(h[L, int(o.row), int(o.col)]) < 1e29:
                s.append(h[L, int(o.row), int(o.col)]); break
        else:
            s.append(np.nan)
    s = np.array(s); oh = OBS.obs_head_m.to_numpy(); m = np.isfinite(s)
    return 1 - np.sum((oh[m] - s[m]) ** 2) / np.sum((oh[m] - oh[m].mean()) ** 2), \
        np.sqrt(np.mean((oh[m] - s[m]) ** 2))


def build(bed_k, inflow=0.0):
    shutil.rmtree(SFR, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(SFR)
    g = sim.get_model()
    g.remove_package("riv_0")                                  # drop RIV
    net = build_sfr_network(RIVS, GRID, g.dis.top.array, g.dis.idomain.array,
                            epsg=26990, bed_k=bed_k)
    per = {}
    if inflow and net["head_reaches"]:
        per = {0: [[h, "inflow", inflow / len(net["head_reaches"])] for h in net["head_reaches"]]}
    flopy.mf6.ModflowGwfsfr(
        g, save_flows=True, length_conversion=1.0, time_conversion=86400.0,
        nreaches=net["nreaches"], packagedata=net["packagedata"],
        connectiondata=net["connectiondata"], perioddata=per or None, pname="sfr_0",
        budget_filerecord=f"{g.name}.sfr.cbc", stage_filerecord=f"{g.name}.sfr.stage")
    sim.write_simulation(silent=True)
    ok, _ = sim.run_simulation(silent=True)
    return ok, g.name, net


def main():
    name = None; net = None
    # 1-parameter search on streambed K to hit the observed gaining baseflow
    best = None
    for bed_k in (0.05, 0.2, 0.5, 1.0, 2.0):
        ok, name, net = build(bed_k)
        if not ok:
            print(f"bed_k={bed_k}: did NOT converge"); continue
        bf = sfr_baseflow(SFR, name)
        nse, rmse = head_nse(SFR, name)
        print(f"bed_k={bed_k:>4}: converged  baseflow={bf:+.3f} m3/s  head NSE={nse:.3f} RMSE={rmse:.2f}")
        if best is None or abs(bf - BASEFLOW_TARGET) < abs(best[1] - BASEFLOW_TARGET):
            best = (bed_k, bf, nse, rmse)
    if best is None:
        print("SFR never converged"); return
    bk, bf, nse, rmse = best
    print(f"\nselected bed_k={bk} (baseflow {bf:+.3f} m3/s vs target {BASEFLOW_TARGET}); "
          f"rebuilding final SFR GWF")
    ok, name, net = build(bk)
    print(f"final MODFLOW_wl_cal_sfr: converged={ok}, {net['nreaches']} reaches, "
          f"baseflow={sfr_baseflow(SFR, name):+.3f} m3/s, head NSE={head_nse(SFR, name)[0]:.3f}")
    np.savez(f"{MODEL}/sfr_network.npz", reach_cells=net["reach_cells"],
             head_reaches=np.array(net["head_reaches"]), reach_channel=net["reach_channel"],
             bed_k=bk)


if __name__ == "__main__":
    main()

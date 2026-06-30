#!/usr/bin/env python3
"""Test the hypothesis: the Rogue convergence failure is a STARTING-HEAD bug, not bad
layers/K. Rebuild the MF6 model with strt = land surface (top) -- guaranteeing no cell
starts dry -- and a robust MF6 Newton config, COLD start (no NWT heads). If it converges
mass-balanced, the fix is identified and is generator-side (MODGenX).
"""
import os, warnings, numpy as np, flopy
warnings.filterwarnings("ignore")
NWT_WS = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/MODFLOW_250m"
WS = "/data/SWATGenXApp/codes/_temp/swatplus-mf6-spike/rogue_fix"
BIN = "/data/SWATGenXApp/codes/_temp/swatplus-mf6-spike/bin"
NAME = "rogue"

def spd(rec, fields, idomain):
    return [[(int(r["k"]), int(r["i"]), int(r["j"]))] + [float(r[f]) for f in fields]
            for r in rec if idomain[int(r["k"]), int(r["i"]), int(r["j"])] != 0]

nwt = flopy.modflow.Modflow.load("MODFLOW_250m.nam", model_ws=NWT_WS, version="mfnwt",
                                 check=False, forgive=True, verbose=False)
dis, bas, upw = nwt.dis, nwt.bas6, nwt.get_package("UPW")
ib = bas.ibound.array
idomain = np.where(ib != 0, 1, 0)
laytyp = list(upw.laytyp.array); layvka = list(upw.layvka.array)
hk, vka = upw.hk.array, upw.vka.array
k33 = np.where(np.array(layvka)[:, None, None] == 0, vka, hk * vka)

# THE FIX: start every cell at land surface (top broadcast down the column). For an
# unconfined/Newton model this is the robust choice -- heads drain DOWN to the water
# table (stable), vs starting dry (head < bottom) which forces rewetting (unstable).
top = dis.top.array
strt = np.broadcast_to(top, (dis.nlay, dis.nrow, dis.ncol)).copy()

sim = flopy.mf6.MFSimulation(sim_name=NAME, sim_ws=WS, exe_name=os.path.join(BIN, "mf6"))
flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="days")
flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                     outer_maximum=500, inner_maximum=200, outer_dvclose=1e-2, inner_dvclose=1e-3,
                     under_relaxation="DBD", under_relaxation_theta=0.9,
                     backtracking_number=20, backtracking_tolerance=1.05,
                     backtracking_reduction_factor=0.2, backtracking_residual_limit=100.0)
gwf = flopy.mf6.ModflowGwf(sim, modelname=NAME, save_flows=True, newtonoptions="NEWTON UNDER_RELAXATION")
flopy.mf6.ModflowGwfdis(gwf, nlay=dis.nlay, nrow=dis.nrow, ncol=dis.ncol,
                        delr=dis.delr.array, delc=dis.delc.array,
                        top=top, botm=dis.botm.array, idomain=idomain, length_units="meters")
flopy.mf6.ModflowGwfic(gwf, strt=strt)                       # <-- the fix
flopy.mf6.ModflowGwfnpf(gwf, k=hk, k33=k33, icelltype=laytyp, save_specific_discharge=True)
flopy.mf6.ModflowGwfsto(gwf, steady_state={0: True}, iconvert=laytyp)
chd = [[(int(k), int(i), int(j)), float(bas.strt.array[k, i, j])] for k, i, j in np.argwhere(ib < 0)]
if chd:
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd)
flopy.mf6.ModflowGwfrcha(gwf, recharge=nwt.rch.rech.array[0])
flopy.mf6.ModflowGwfriv(gwf, stress_period_data=spd(nwt.riv.stress_period_data[0], ["stage", "cond", "rbot"], idomain))
flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=spd(nwt.drn.stress_period_data[0], ["elev", "cond"], idomain))
w = nwt.get_package("WEL")
if w and len(w.stress_period_data[0]):
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data=spd(w.stress_period_data[0], ["flux"], idomain))
flopy.mf6.ModflowGwfoc(gwf, head_filerecord=f"{NAME}.hds", budget_filerecord=f"{NAME}.cbc",
                       saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")])
sim.write_simulation(silent=True)
ok, _ = sim.run_simulation(silent=True)
print("COLD-START (strt=top) converged:", ok)
if ok:
    h = flopy.utils.HeadFile(os.path.join(WS, f"{NAME}.hds")).get_data()
    a = h[(idomain != 0) & (np.abs(h) < 1e6)]
    print(f"head range: {a.min():.1f} - {a.max():.1f} m  mean {a.mean():.1f}")
    # mass balance from listing
    import re
    lst = open(os.path.join(WS, f"{NAME}.lst")).read()
    disc = re.findall(r"PERCENT DISCREPANCY\s*=\s*([-\d.]+)", lst)
    print("final mass-balance discrepancy:", disc[-1] if disc else "n/a", "%")

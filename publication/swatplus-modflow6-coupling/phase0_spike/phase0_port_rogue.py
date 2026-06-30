#!/usr/bin/env python3
"""Phase-0: port the real Rogue MODGenX MODFLOW-NWT model to MODFLOW 6 and validate.

Loads the deployed NWT model (6-layer, 165x124, RCH/RIV/DRN/WEL, NEWTON), rebuilds an
equivalent MF6 GWF model package-by-package via FloPy, runs both, and cross-checks the
simulated heads on active cells. This proves the NWT->MF6 port (the contained ~130-line
MODGenXCore change Phase 1 needs) on a real, validated grid before any coupling code.
"""
import os, warnings, numpy as np, flopy
warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
NWT_WS = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/MODFLOW_250m"
MF6_WS = os.path.join(HERE, "rogue_mf6")
# official MF6 6.7.0 binaries (mf6 + libmf6.so), fetched via flopy get-modflow
BIN = "/data/SWATGenXApp/codes/_temp/swatplus-mf6-spike/bin"
NAME = "rogue"

def spd_to_mf6(rec, fields, idomain=None):
    """NWT stress_period_data recarray -> MF6 list of [(k,i,j), *vals].

    MF6 rejects boundaries on inactive (idomain==0) cells, which MODFLOW-NWT silently
    ignored; drop those so the port is faithful to what NWT actually simulated.
    """
    out, dropped = [], 0
    for r in rec:
        k, i, j = int(r["k"]), int(r["i"]), int(r["j"])
        if idomain is not None and idomain[k, i, j] == 0:
            dropped += 1
            continue
        out.append([(k, i, j)] + [float(r[f]) for f in fields])
    if dropped:
        print(f"[port]   dropped {dropped} boundary cells on inactive cells")
    return out

def port():
    nwt = flopy.modflow.Modflow.load("MODFLOW_250m.nam", model_ws=NWT_WS, version="mfnwt",
                                     check=False, forgive=True, verbose=False)
    dis, bas, upw = nwt.dis, nwt.bas6, nwt.get_package("UPW")
    ibound = bas.ibound.array
    idomain = np.where(ibound != 0, 1, 0)
    chd_cells = np.argwhere(ibound < 0)            # constant-head cells -> CHD
    laytyp = list(upw.laytyp.array)
    layvka = list(upw.layvka.array)
    # vka is vertical K when layvka==0, else a ratio of hk -> convert to K33
    hk, vka = upw.hk.array, upw.vka.array
    k33 = np.where(np.array(layvka)[:, None, None] == 0, vka, hk * vka)

    # Start MF6 from the NWT solution heads: this stiff auto-generated model only barely
    # solves in NWT and MF6-Newton diverges from a cold start, so a port is validated by
    # confirming the NWT solution is a (near-)fixed point of the MF6 packages.
    nwt_hds = flopy.utils.HeadFile(os.path.join(NWT_WS, "MODFLOW_250m.hds")).get_data()
    botm = dis.botm.array
    strt0 = np.where((nwt_hds > -1e29) & (nwt_hds < 1e6), nwt_hds, dis.top.array)
    strt0 = np.maximum(strt0, botm + 0.1)            # keep starting head above cell bottom

    sim = flopy.mf6.MFSimulation(sim_name=NAME, sim_ws=MF6_WS, exe_name=os.path.join(BIN, "mf6"))
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="days")
    flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                         outer_maximum=500, inner_maximum=200,
                         outer_dvclose=1e-2, inner_dvclose=1e-3,
                         under_relaxation="DBD", under_relaxation_theta=0.9,
                         under_relaxation_kappa=0.0001, under_relaxation_gamma=0.0,
                         backtracking_number=20, backtracking_tolerance=1.05,
                         backtracking_reduction_factor=0.2, backtracking_residual_limit=100.0)
    gwf = flopy.mf6.ModflowGwf(sim, modelname=NAME, save_flows=True,
                               newtonoptions="NEWTON UNDER_RELAXATION")
    flopy.mf6.ModflowGwfdis(gwf, nlay=dis.nlay, nrow=dis.nrow, ncol=dis.ncol,
                            delr=dis.delr.array, delc=dis.delc.array,
                            top=dis.top.array, botm=dis.botm.array, idomain=idomain,
                            length_units="meters")
    flopy.mf6.ModflowGwfic(gwf, strt=strt0)
    flopy.mf6.ModflowGwfnpf(gwf, k=hk, k33=k33, icelltype=laytyp, save_specific_discharge=True)
    flopy.mf6.ModflowGwfsto(gwf, steady_state={0: True}, iconvert=laytyp)
    if len(chd_cells):
        chd = [[(int(k), int(i), int(j)), float(bas.strt.array[k, i, j])] for k, i, j in chd_cells]
        flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd)
        print(f"[port] CHD cells: {len(chd)}")
    # array recharge (RCHA) — the form the SWAT+ coupler will SET each day
    flopy.mf6.ModflowGwfrcha(gwf, recharge=nwt.rch.rech.array[0])
    riv = nwt.get_package("RIV"); drn = nwt.get_package("DRN"); wel = nwt.get_package("WEL")
    print("[port] RIV fields:", riv.stress_period_data.dtype.names)
    flopy.mf6.ModflowGwfriv(gwf, stress_period_data=spd_to_mf6(riv.stress_period_data[0], ["stage", "cond", "rbot"], idomain))
    flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=spd_to_mf6(drn.stress_period_data[0], ["elev", "cond"], idomain))
    if wel is not None and wel.stress_period_data[0] is not None and len(wel.stress_period_data[0]):
        flopy.mf6.ModflowGwfwel(gwf, stress_period_data=spd_to_mf6(wel.stress_period_data[0], ["flux"], idomain))
    flopy.mf6.ModflowGwfoc(gwf, head_filerecord=f"{NAME}.hds", budget_filerecord=f"{NAME}.cbc",
                           saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")])
    sim.write_simulation(silent=True)
    print("[port] MF6 model written to", MF6_WS)
    ok, buff = sim.run_simulation(silent=True)
    print("[port] MF6 run converged:", ok)
    return nwt, idomain

def compare(nwt, idomain):
    # NWT heads (already computed in the deployed model dir)
    nwt_hds = flopy.utils.HeadFile(os.path.join(NWT_WS, "MODFLOW_250m.hds")).get_data()
    mf6_hds = flopy.utils.HeadFile(os.path.join(MF6_WS, f"{NAME}.hds")).get_data()
    m = (idomain != 0) & (np.abs(nwt_hds) < 1e6) & (np.abs(mf6_hds) < 1e6)
    d = mf6_hds[m] - nwt_hds[m]
    print(f"\n[compare] active cells: {m.sum()}")
    print(f"[compare] head diff (MF6 - NWT): mean={d.mean():+.3f}  rms={np.sqrt((d**2).mean()):.3f}  "
          f"p50={np.percentile(np.abs(d),50):.3f}  p95={np.percentile(np.abs(d),95):.3f}  max|d|={np.abs(d).max():.3f} m")
    within1 = (np.abs(d) <= 1.0).mean() * 100
    print(f"[compare] {within1:.1f}% of cells within 1 m of NWT")

if __name__ == "__main__":
    nwt, idomain = port()
    compare(nwt, idomain)

"""SWAT+ <-> MODFLOW 6 coupling, Phase 3 (SFR/SFT): PFAS fate & transport with IN-STREAM routing.

Builds on the SFR-based calibrated flow field (MODFLOW_wl_cal_sfr). A GWT model with Freundlich
PFAS sorption is coupled to it; the SFR streamflow-transport package (SFT) routes any PFAS that
discharges from groundwater into a stream reach DOWNSTREAM through the connected channel network
to the outlet. This is what RIV could not do: RIV is a per-cell head-dependent leak with no
routing, so GW-discharged PFAS just vanished from the model. SFR+SFT closes the loop -- the
groundwater PFAS pathway now feeds the in-stream PFAS load that the SWAT+ channel PFAS module
(engine side) carries.

Outputs: the aquifer plume (as in the RIV Phase 3) + the per-reach in-stream PFAS concentration
routed to the outlet -- the new capability.
"""
import os
import glob
import shutil
import numpy as np
import flopy

CAL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_cal_sfr"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
WS = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_sfr_pfas"
MODEL_DIR = os.path.dirname(CAL)

POROSITY = 0.30
BULK_DENSITY = 1800.0
KF = 0.005                      # Freundlich (R~10.6 at 100 ng/L; see phase3_pfas_gwt.py note)
FREUND_N = 0.8
ALH, ATH = 10.0, 1.0
DIFFC = 1e-10
SOURCE_CONC = 100.0
C_BACKGROUND = 0.1              # ambient PFAS; removes the Freundlich C^(n-1) singularity
NYEARS = 40
PERLEN = 365.25


def build(name, sorbing, ws):
    shutil.rmtree(ws, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(ws)
    gwf = sim.get_model()
    gwfname = gwf.name
    dis = gwf.dis
    nlay, nrow, ncol = dis.nlay.array, dis.nrow.array, dis.ncol.array
    idom = dis.idomain.array
    top = dis.top.array
    sfr = gwf.get_package("sfr_0")
    nreaches = sfr.nreaches.array

    ats_period = [(i, PERLEN / 6.0, 1.0, PERLEN, 2.0, 4.0) for i in range(NYEARS)]
    tdis = flopy.mf6.ModflowTdis(sim, nper=NYEARS, time_units="days",
                                 perioddata=[(PERLEN, 6, 1.2) for _ in range(NYEARS)])
    flopy.mf6.ModflowUtlats(tdis, maxats=len(ats_period), perioddata=ats_period,
                            filename=f"{name}.ats")
    gwf.sto.steady_state.set_data({0: True})

    # PFAS source at the upgradient (highest-head) active cell, layer 0
    h = flopy.utils.HeadFile(glob.glob(f"{CAL}/*.hds")[0]).get_data()
    htop = np.where(idom[0] != 0, h[0], np.nan)
    si, sj = np.unravel_index(np.nanargmax(htop), htop.shape)
    src_cell = (0, int(si), int(sj))

    gwt = flopy.mf6.ModflowGwt(sim, modelname=name, save_flows=True)
    flopy.mf6.ModflowGwtdis(gwt, nlay=nlay, nrow=nrow, ncol=ncol,
                            delr=dis.delr.array, delc=dis.delc.array,
                            top=top, botm=dis.botm.array, idomain=idom, length_units="meters")
    flopy.mf6.ModflowGwtic(gwt, strt=C_BACKGROUND if sorbing else 0.0)
    flopy.mf6.ModflowGwtadv(gwt, scheme="tvd")
    flopy.mf6.ModflowGwtdsp(gwt, alh=ALH, ath1=ATH, diffc=DIFFC)
    if sorbing:
        flopy.mf6.ModflowGwtmst(gwt, porosity=POROSITY, sorption="freundlich",
                                bulk_density=BULK_DENSITY, distcoef=KF, sp2=FREUND_N)
    else:
        flopy.mf6.ModflowGwtmst(gwt, porosity=POROSITY)
    flopy.mf6.ModflowGwtcnc(gwt, stress_period_data={0: [[src_cell, SOURCE_CONC]]}, pname="cnc_site")
    flopy.mf6.ModflowGwtssm(gwt, sources=[[]])           # GHB/DRN/WEL/RCHA: clean inflow
    # SFT: streamflow transport on the SFR network. Reaches start clean (strt 0); solute enters
    # each reach with the groundwater it gains (concentration from FMI) and routes downstream.
    sft_pkg = [[r, 0.0] for r in range(nreaches)]
    flopy.mf6.ModflowGwtsft(gwt, flow_package_name="sfr_0", save_flows=True,
                            print_concentration=True, packagedata=sft_pkg,
                            concentration_filerecord=f"{name}.sft.ucn",
                            budget_filerecord=f"{name}.sft.cbc", pname="sft_0")
    flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord=f"{name}.ucn",
                           saverecord=[("CONCENTRATION", "LAST")])
    flopy.mf6.ModflowGwfgwt(sim, exgtype="GWF6-GWT6", exgmnamea=gwfname, exgmnameb=name,
                            filename=f"{name}.gwfgwt")
    ims_t = flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                                 outer_dvclose=1e-4, inner_dvclose=1e-5,
                                 outer_maximum=200, inner_maximum=300, filename=f"{name}.ims")
    sim.register_ims_package(ims_t, [name])
    sim.write_simulation(silent=True)
    return sim, src_cell, idom, nreaches


def main():
    net = np.load(f"{MODEL_DIR}/sfr_network.npz")
    rc = net["reach_cells"]
    out = {}
    src = None
    for name, sorbing, ws in [("pfas", True, WS), ("consv", False, WS + "_consv")]:
        sim, src, idom, nreaches = build(name, sorbing, ws)
        ok, buff = sim.run_simulation(silent=True)
        print(f"SFR+SFT {name}: converged={ok}  (source {src}, {nreaches} reaches)")
        if not ok:
            print("\n".join(buff[-15:])); return
        c = flopy.utils.HeadFile(glob.glob(f"{ws}/{name}.ucn")[0], text="CONCENTRATION").get_data()
        ct = np.where(idom != 0, c, np.nan)
        plume = np.nanmax(np.where(ct > 0.1, ct, np.nan), axis=0)
        sft = flopy.utils.HeadFile(glob.glob(f"{ws}/{name}.sft.ucn")[0], text="CONCENTRATION")
        reach_c = sft.get_data(totim=sft.get_times()[-1]).ravel()
        out[f"{name}_plume"] = plume
        out[f"{name}_reach"] = reach_c
        print(f"  aquifer plume >1 ng/L: {int(np.nansum(plume > 1))} cells; max {np.nanmax(ct):.1f} ng/L")
        print(f"  in-stream: reaches >0.5 ng/L = {int(np.sum(reach_c > 0.5))} of {nreaches}; "
              f"max reach conc {reach_c.max():.3f} ng/L")
    np.savez(f"{MODEL_DIR}/phase3_sfr_plumes.npz", src=np.array(src), reach_cells=rc, **out)
    print(f"wrote {MODEL_DIR}/phase3_sfr_plumes.npz")


if __name__ == "__main__":
    main()

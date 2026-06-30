"""SWAT+ <-> MODFLOW 6 coupling, Phase 3: PFAS fate & transport in groundwater (GWT).

Couples a MODFLOW 6 GWT (groundwater transport) model to the calibrated steady-state GWF
flow field (MODFLOW_wl_cal) via the GWF6-GWT6 exchange. A PFAS source (a contaminated-site
constant-concentration cell + diffuse PFAS in recharge) migrates downgradient and discharges
to the streams -- the groundwater leg of the PFAS pathway. PFAS sorption is FREUNDLICH (the
PFAS-standard isotherm; MST sorption='freundlich'), so the plume is retarded vs a conservative
tracer -- demonstrating PFAS persistence/retardation, the differentiator over a frozen RT3D.

Builds two GWT models on the same flow field for comparison:
  pfas   : Freundlich-sorbed (PFOS-like Kf/n)
  consv  : conservative (no sorption) reference
Outputs the plume rasters + a source->stream breakthrough.

Units: lengths m, time days, concentration ng/L (mass-consistent; recharge/source in ng/L).
"""
import os
import glob
import shutil
import numpy as np
import flopy

CAL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_cal"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
WS = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_pfas"

# --- PFAS / aquifer transport parameters ---
POROSITY = 0.30
BULK_DENSITY = 1800.0          # kg/m3
# Freundlich for PFOS in a sandy aquifer. sorbed = Kf * C^n (MF6 MST units: bulk_density
# kg/m3, conc ng/L). Kf=0.005 / n=0.8 gives a retardation factor R = 1 + (rho_b/theta)*Kf*n*
# C^(n-1) ~= 10.6 at C=100 ng/L -- the literature PFOS range for low-foc sand (R~5-10;
# Li et al. 2019). (Kf=0.05 over-retards to R~96, a 1-cell plume; lowered for unit
# consistency + a realistic, visibly-retarded plume vs the conservative tracer.)
KF = 0.005
FREUND_N = 0.8
ALH, ATH = 10.0, 1.0           # dispersivity (m), regional 250 m grid
DIFFC = 1e-10                  # m2/s ~ negligible
SOURCE_CONC = 100.0            # ng/L at the contaminated-site source cell
C_BACKGROUND = 0.1             # ng/L ambient PFAS (ubiquitous atmospheric/diffuse deposition).
                               # Physically real AND removes the Freundlich C^(n-1) retardation
                               # singularity at C->0 that otherwise stalls the transport solver.
NYEARS = 40
PERLEN = 365.25


def build(name, sorbing, ws, src_cell=None):
    shutil.rmtree(ws, ignore_errors=True)
    # load calibrated GWF, retarget into the coupled sim workspace
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(ws)
    gwf = sim.get_model()
    gwfname = gwf.name
    dis = gwf.dis
    nlay, nrow, ncol = dis.nlay.array, dis.nrow.array, dis.ncol.array
    idom = dis.idomain.array
    top = dis.top.array

    # transient TDIS (steady flow, transient transport); GWF stays steady across periods.
    # ATS (adaptive time stepping): the Freundlich isotherm (n<1) makes the sorption
    # retardation term ~C^(n-1) stiff as C->0 at the spreading plume front -- the transport
    # solver hits a convergence wall mid-run. ATS lets MF6 cut dt on a failed step and
    # recover (dtfailadj=4) instead of aborting, then grow it back (dtadj=2).
    ats_period = [(i, PERLEN / 6.0, 1.0, PERLEN, 2.0, 4.0) for i in range(NYEARS)]
    tdis = flopy.mf6.ModflowTdis(sim, nper=NYEARS, time_units="days",
                                 perioddata=[(PERLEN, 6, 1.2) for _ in range(NYEARS)])
    flopy.mf6.ModflowUtlats(tdis, maxats=len(ats_period), perioddata=ats_period,
                            filename=f"{name}.ats")
    gwf.sto.steady_state.set_data({0: True})

    # contaminated-site source cell: an upgradient active cell (high head, layer 0)
    if src_cell is None:
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
    # SSM (required when GWF has boundary packages): boundary inflows (recharge, losing
    # streams) enter at concentration 0 (clean); outflows (gaining streams, wells, drains)
    # carry the cell concentration -> this is the GW->stream PFAS discharge pathway.
    flopy.mf6.ModflowGwtssm(gwt, sources=[[]])
    flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord=f"{name}.ucn",
                           saverecord=[("CONCENTRATION", "ALL")])  # ALL times -> breakthrough
    flopy.mf6.ModflowGwfgwt(sim, exgtype="GWF6-GWT6", exgmnamea=gwfname, exgmnameb=name,
                            filename=f"{name}.gwfgwt")
    ims_t = flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                                 outer_dvclose=1e-4, inner_dvclose=1e-5,
                                 outer_maximum=200, inner_maximum=300,
                                 filename=f"{name}.ims")
    sim.register_ims_package(ims_t, [name])
    sim.write_simulation(silent=True)
    return sim, src_cell, (nlay, nrow, ncol), idom


def _riv_cells():
    """(row, col) of the GWF RIV cells -- the GW->stream discharge faces."""
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0)
    spd = sim.get_model().get_package("riv_0").stress_period_data.get_data(0)
    return np.array([(int(r["cellid"][1]), int(r["cellid"][2])) for r in spd])


def main():
    out, bt = {}, {}
    src = None
    rivc = _riv_cells()
    bcell = None
    for name, sorb, ws in [("pfas", True, WS), ("consv", False, WS + "_consv")]:
        sim, src, shape, idom = build(name, sorb, ws, src_cell=src)
        ok, buff = sim.run_simulation(silent=True)
        print(f"{name}: converged={ok}  (source cell {src}, ws {os.path.basename(ws)})")
        if not ok:
            print("\n".join(buff[-12:])); return
        hf = flopy.utils.HeadFile(glob.glob(f"{ws}/{name}.ucn")[0], text="CONCENTRATION")
        times = np.array(hf.get_times())
        c = hf.get_data(totim=times[-1])                       # final concentration field
        ct = np.where(idom != 0, c, np.nan)
        out[name] = np.nanmax(np.where(ct > 0.1, ct, np.nan), axis=0)
        # breakthrough: the RIV cell the conservative plume reaches strongest -> fix that
        # same cell for both models so the curves are comparable (PFAS arrives later/lower)
        cmax = np.nanmax(ct, axis=0)
        if bcell is None and name == "pfas":
            pass                                               # set from consv below; reuse on next pass
        if name == "consv":
            riv_final = np.array([cmax[i, j] for i, j in rivc])
            bcell = tuple(rivc[int(np.nanargmax(riv_final))])
        # collect the time series at every stored time at the (eventual) breakthrough cell
        series = []
        for t in times:
            cc = np.where(idom != 0, hf.get_data(totim=t), np.nan)
            series.append(np.nanmax(cc[:, :, :], axis=0))      # max over depth -> 2d per time
        bt[name] = (times, np.array(series))                   # (nt,), (nt,nrow,ncol)
        print(f"  max conc {np.nanmax(ct):.1f} ng/L, cells >1 ng/L {int(np.nansum(ct > 1.0))}")
    # extract the breakthrough series at the shared discharge cell
    bi, bj = bcell
    pf_t, pf_s = bt["pfas"]; cv_t, cv_s = bt["consv"]
    npz = os.path.join(os.path.dirname(WS), "phase3_plumes.npz")  # www-data-writable model dir
    np.savez(npz, pfas=out["pfas"], consv=out["consv"], src=np.array(src),
             bcell=np.array(bcell),
             pf_t=pf_t / 365.25, pf_bt=pf_s[:, bi, bj],
             cv_t=cv_t / 365.25, cv_bt=cv_s[:, bi, bj])
    print(f"wrote {npz}  (breakthrough cell row,col={bcell})")


if __name__ == "__main__":
    main()

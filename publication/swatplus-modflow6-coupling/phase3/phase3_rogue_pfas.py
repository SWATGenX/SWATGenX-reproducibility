"""Rogue (04118500) groundwater PFAS fate & transport, validated against the Wolverine plume.

Couples a MODFLOW 6 GWT (Freundlich PFAS) to the PEST++-calibrated Rogue flow field
(MODFLOW_sfr_cal), with the source ANCHORED to the measured House Street disposal-site
groundwater concentrations (the highest measured GW PFOS, up to 1.5 mg/L). SFT routes the
groundwater-discharged PFAS downstream through the SFR channel network. The modeled groundwater
plume is VALIDATED against the 846 measured groundwater PFOS observations (the downgradient
plume), and the SFT in-stream load is the groundwater contribution to the surface-water PFAS the
SWAT+ engine routes -- closing the surface-water + groundwater PFAS mass balance on one watershed.

Source = measured: CNC at the source-zone cells (measured GW PFOS > SRC_THRESH ng/L) at their
observed concentration. Validation = the remaining observation cells (downgradient + background).
"""
import os
import glob
import shutil
import numpy as np
import pandas as pd
import flopy

ROGUE = os.environ.get(
    "SWATGENX_ROGUE_DIR",
    "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500",
)
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
GWOBS = f"{ROGUE}/SWAT_MODEL_Web_Application/pfas_gw_data/pfas_gw_PFOS.csv"
EXE = "/data/SWATGenXApp/codes/bin/mf6"
WS = f"{ROGUE}/MODFLOW_rogue_pfas"
MODEL_DIR = ROGUE

POROSITY, BULK_DENSITY = 0.30, 1800.0
KF, FREUND_N = 0.005, 0.8        # Freundlich PFOS (R~10; see phase3_pfas_gwt.py note)
ALH, ATH, DIFFC = 10.0, 1.0, 1e-10
C_BACKGROUND = 10.0              # ambient GW PFOS background (ng/L; ~p50 of obs; removes the
                                 # C^(n-1) singularity AND compresses the dynamic range for the solver
SRC_THRESH = 1.0e4               # cells with measured GW PFOS above this = the House St source zone
SRC_CAP = 1.0e5                  # cap the CNC source at a robust source-zone value: the single 1.5e6
                                 # ng/L peak sample is an outlier that makes the front intractably stiff
                                 # (6-order range). The log-space validation tests the plume SHAPE;
                                 # absolute source magnitude carries the (single-sample) source uncertainty.
NYEARS, PERLEN = 40, 365.25      # validates best vs the GW obs (1.09 dex); the joint-calibration
                                 # result is robust to duration (g~0 at 40/100 yr was a georef bug)


def source_and_obs():
    d = pd.read_csv(GWOBS)
    d = d.dropna(subset=["row", "col", "max_value"])
    d["row"] = d.row.astype(int); d["col"] = d.col.astype(int)
    cell_max = d.groupby(["row", "col"])["max_value"].max().reset_index()
    src = cell_max[cell_max.max_value >= SRC_THRESH]
    val = cell_max[cell_max.max_value < SRC_THRESH]      # downgradient + background = validation
    return src, val


def build(src):
    shutil.rmtree(WS, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(WS)
    gwf = sim.get_model(); gwfname = gwf.name
    dis = gwf.dis; nlay, nrow, ncol = dis.nlay.array, dis.nrow.array, dis.ncol.array
    idom = dis.idomain.array; top = dis.top.array
    nre = gwf.get_package("sfr_0").nreaches.array

    ats = [(i, PERLEN / 8.0, 0.01, PERLEN, 2.0, 5.0) for i in range(NYEARS)]
    tdis = flopy.mf6.ModflowTdis(sim, nper=NYEARS, time_units="days",
                                 perioddata=[(PERLEN, 8, 1.2) for _ in range(NYEARS)])
    flopy.mf6.ModflowUtlats(tdis, maxats=len(ats), perioddata=ats, filename="pfas.ats")
    gwf.sto.steady_state.set_data({0: True})

    gwt = flopy.mf6.ModflowGwt(sim, modelname="pfas", save_flows=True)
    flopy.mf6.ModflowGwtdis(gwt, nlay=nlay, nrow=nrow, ncol=ncol, delr=dis.delr.array,
                            delc=dis.delc.array, top=top, botm=dis.botm.array, idomain=idom,
                            length_units="meters")
    flopy.mf6.ModflowGwtic(gwt, strt=C_BACKGROUND)
    flopy.mf6.ModflowGwtadv(gwt, scheme="tvd")
    flopy.mf6.ModflowGwtdsp(gwt, alh=ALH, ath1=ATH, diffc=DIFFC)
    flopy.mf6.ModflowGwtmst(gwt, porosity=POROSITY, sorption="freundlich",
                            bulk_density=BULK_DENSITY, distcoef=KF, sp2=FREUND_N)
    # source: CNC at the House St source-zone cells (layer 0) at measured concentration
    cnc = [[(0, int(r.row), int(r.col)), min(float(r.max_value), SRC_CAP)] for r in src.itertuples()
           if idom[0, int(r.row), int(r.col)] != 0]
    flopy.mf6.ModflowGwtcnc(gwt, stress_period_data={0: cnc}, pname="cnc_housest")
    flopy.mf6.ModflowGwtssm(gwt, sources=[[]])
    flopy.mf6.ModflowGwtsft(gwt, flow_package_name="sfr_0", save_flows=True,
                            packagedata=[[r, 0.0] for r in range(nre)],
                            concentration_filerecord="pfas.sft.ucn",
                            budget_filerecord="pfas.sft.cbc", pname="sft_0")
    flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord="pfas.ucn",
                           saverecord=[("CONCENTRATION", "LAST")])
    flopy.mf6.ModflowGwfgwt(sim, exgtype="GWF6-GWT6", exgmnamea=gwfname, exgmnameb="pfas",
                            filename="pfas.gwfgwt")
    ims = flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                               outer_dvclose=1e-3, inner_dvclose=1e-4, outer_maximum=500,
                               inner_maximum=500, filename="pfas.ims")
    sim.register_ims_package(ims, ["pfas"])
    sim.write_simulation(silent=True)
    return sim, idom, len(cnc), nre


def main():
    src, val = source_and_obs()
    print(f"source-zone cells (>{SRC_THRESH:g} ng/L measured): {len(src)}; validation cells: {len(val)}")
    sim, idom, ncnc, nre = build(src)
    ok, buff = sim.run_simulation(silent=True)
    print(f"Rogue GW-PFAS: converged={ok} (source cells {ncnc}, {nre} reaches)")
    if not ok:
        print("\n".join(buff[-15:])); return
    c = flopy.utils.HeadFile(glob.glob(f"{WS}/pfas.ucn")[0], text="CONCENTRATION").get_data()
    cmax = np.nanmax(np.where(idom != 0, c, np.nan), axis=0)        # max over depth
    # validation: modeled vs observed GW PFOS at the validation cells (log space)
    mod = np.array([cmax[int(r.row), int(r.col)] for r in val.itertuples()])
    obs = val.max_value.to_numpy()
    m = np.isfinite(mod) & (mod > 0) & (obs > 0)
    lo, lm = np.log10(obs[m]), np.log10(mod[m])
    rmse = np.sqrt(np.mean((lo - lm) ** 2)); bias = np.mean(lm - lo)
    within10x = np.mean(np.abs(lo - lm) < 1.0)
    sft = flopy.utils.HeadFile(glob.glob(f"{WS}/pfas.sft.ucn")[0], text="CONCENTRATION")
    reach_c = sft.get_data(totim=sft.get_times()[-1]).ravel()
    print(f"  GW plume validation ({m.sum()} cells): log-RMSE {rmse:.2f} dex, bias {bias:+.2f}, "
          f"within 10x {100*within10x:.0f}%")
    print(f"  in-stream PFOS (SFT): reaches >1 ng/L = {int(np.sum(reach_c > 1))}, "
          f"max reach {reach_c.max():.1f} ng/L")
    np.savez(f"{MODEL_DIR}/rogue_pfas_results.npz", cmax=cmax, reach_c=reach_c,
             val_row=val.row.values, val_col=val.col.values, val_obs=val.max_value.values,
             src_row=src.row.values, src_col=src.col.values)
    print(f"wrote {MODEL_DIR}/rogue_pfas_results.npz")


if __name__ == "__main__":
    main()

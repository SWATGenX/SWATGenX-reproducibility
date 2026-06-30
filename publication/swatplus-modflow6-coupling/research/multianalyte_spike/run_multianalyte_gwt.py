"""Multi-analyte Rogue GW-PFAS transport (lean-5) -> modeled in-stream GW fingerprint.

For each of PFOS, PFOA, PFHxS, PFBS, PFHxA: build a MF6 GWT (Freundlich, compound-specific Kf/n
from compound_params_lean5.csv) on the PEST++-calibrated Rogue flow field, source ANCHORED to that
analyte's measured plume (pfas_gw_<analyte>.csv, >SRC_THRESH), SFT routes the GW-discharged load to
the channel network. Saves per-analyte plume validation + per-reach in-stream concentration. The
assembled per-reach 5-analyte composition is the MODELED GW fingerprint to compare against the
observed plume end-member and the observed in-stream gradient (instream_snapped.csv).

Extends phase3/phase3_rogue_pfas.py to multiple analytes. Run from repo root with .venv python.
"""
import os, glob, shutil, numpy as np, pandas as pd, flopy

ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL   = f"{ROGUE}/MODFLOW_sfr_cal"
EXE   = "/data/SWATGenXApp/codes/bin/mf6"
GWDIR = f"{ROGUE}/SWAT_MODEL_Web_Application/pfas_gw_data"
OUT   = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"

POROSITY, BULK_DENSITY = 0.30, 1800.0
ALH, ATH, DIFFC = 10.0, 1.0, 1e-10
SRC_THRESH, SRC_CAP = 1.0e4, 1.0e5
NYEARS, PERLEN = 40, 365.25
LEAN5 = ["PFOS", "PFOA", "PFHxS", "PFBS", "PFHxA"]

params = pd.read_csv(f"{OUT}/compound_params_lean5.csv").set_index("analyte")


def load_cell(analyte):
    d = pd.read_csv(f"{GWDIR}/pfas_gw_{analyte}.csv").dropna(subset=["row", "col", "max_value"])
    d["row"] = d.row.astype(int); d["col"] = d.col.astype(int)
    return d.groupby(["row", "col"]).max_value.max().reset_index().rename(columns={"max_value": analyte})


def joint_sources():
    """Fingerprint-PRESERVING source: source zone defined by PFOS>=SRC_THRESH; at each source cell
    scale ALL analytes by the same factor s=min(1, SRC_CAP/PFOS) so PFOS<=cap AND the measured
    cross-analyte composition (the plume fingerprint) is preserved. Returns per-analyte source dict."""
    cells = load_cell("PFOS")
    for a in LEAN5:
        if a != "PFOS":
            cells = cells.merge(load_cell(a), on=["row", "col"], how="outer")
    cells = cells[cells.PFOS.notna() & (cells.PFOS >= SRC_THRESH)].copy()
    cells["scale"] = (SRC_CAP / cells.PFOS).clip(upper=1.0)
    src = {}
    for a in LEAN5:
        sa = cells[["row", "col", a, "scale"]].dropna(subset=[a]).copy()
        sa["max_value"] = sa[a] * sa["scale"]
        src[a] = sa[["row", "col", "max_value"]]
    return src


def obs_cells(analyte):
    cell = load_cell(analyte).rename(columns={analyte: "max_value"})
    pfos = load_cell("PFOS")[["row", "col", "PFOS"]]
    cell = cell.merge(pfos, on=["row", "col"], how="left")
    return cell[(cell.PFOS.isna()) | (cell.PFOS < SRC_THRESH)][["row", "col", "max_value"]]


def build(analyte, src, ws):
    Kf = float(params.loc[analyte, "Kf"]); nF = float(params.loc[analyte, "n"])
    bg = 1.0  # ambient background ng/L (compress dynamic range / remove C^(n-1) singularity)
    shutil.rmtree(ws, ignore_errors=True)
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, exe_name=EXE, verbosity_level=0)
    sim.set_sim_path(ws)
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
    flopy.mf6.ModflowGwtic(gwt, strt=bg)
    flopy.mf6.ModflowGwtadv(gwt, scheme="tvd")
    flopy.mf6.ModflowGwtdsp(gwt, alh=ALH, ath1=ATH, diffc=DIFFC)
    flopy.mf6.ModflowGwtmst(gwt, porosity=POROSITY, sorption="freundlich",
                            bulk_density=BULK_DENSITY, distcoef=Kf, sp2=nF)
    cnc = [[(0, int(r.row), int(r.col)), min(float(r.max_value), SRC_CAP)] for r in src.itertuples()
           if idom[0, int(r.row), int(r.col)] != 0]
    flopy.mf6.ModflowGwtcnc(gwt, stress_period_data={0: cnc}, pname="cnc")
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
    summary, reach_tab = [], {}
    SRC = joint_sources()   # fingerprint-preserving per-analyte source
    for a in LEAN5:
        src, val = SRC[a], obs_cells(a)
        ws = f"/tmp/rogue_pfas_{a}"
        sim, idom, ncnc, nre = build(a, src, ws)
        ok, buff = sim.run_simulation(silent=True)
        if not ok:
            print(f"[{a}] FAILED to converge (src cells {ncnc})"); print("\n".join(buff[-8:])); continue
        c = flopy.utils.HeadFile(glob.glob(f"{ws}/pfas.ucn")[0], text="CONCENTRATION").get_data()
        cmax = np.nanmax(np.where(idom != 0, c, np.nan), axis=0)
        np.savez(f"{OUT}/cmax_{a}.npz", cmax=cmax)   # modeled aquifer conc (max over depth) for porewater/plume validation
        mod = np.array([cmax[int(r.row), int(r.col)] for r in val.itertuples()]); obs = val.max_value.to_numpy()
        m = np.isfinite(mod) & (mod > 0) & (obs > 0)
        lo, lm = np.log10(obs[m]), np.log10(mod[m])
        rmse = float(np.sqrt(np.mean((lo - lm) ** 2))); w10 = float(np.mean(np.abs(lo - lm) < 1.0))
        sft = flopy.utils.HeadFile(glob.glob(f"{ws}/pfas.sft.ucn")[0], text="CONCENTRATION")
        reach_c = sft.get_data(totim=sft.get_times()[-1]).ravel()
        reach_tab[a] = reach_c
        summary.append(dict(analyte=a, Kf=float(params.loc[a, "Kf"]), n=float(params.loc[a, "n"]),
                            src_cells=ncnc, val_cells=int(m.sum()), plume_logRMSE=round(rmse, 2),
                            within10x=round(100 * w10, 0), reach_gt1=int((reach_c > 1).sum()),
                            reach_max=round(float(reach_c.max()), 1)))
        print(f"[{a}] Kf={params.loc[a,'Kf']:.5f} n={params.loc[a,'n']:.2f} | plume {m.sum()} cells "
              f"log-RMSE {rmse:.2f} within10x {100*w10:.0f}% | SFT reaches>1ng/L={int((reach_c>1).sum())} "
              f"max {reach_c.max():.1f}", flush=True)
    pd.DataFrame(summary).to_csv(f"{OUT}/multianalyte_gwt_summary.csv", index=False)
    if reach_tab:
        rt = pd.DataFrame(reach_tab); rt.insert(0, "reach", range(len(rt)))
        rt.to_csv(f"{OUT}/multianalyte_reach_conc.csv", index=False)
    print("DONE -> multianalyte_gwt_summary.csv + multianalyte_reach_conc.csv", flush=True)


if __name__ == "__main__":
    main()

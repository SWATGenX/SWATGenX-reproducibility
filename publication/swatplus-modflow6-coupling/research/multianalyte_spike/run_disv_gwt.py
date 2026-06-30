"""DISV multi-analyte GWT (Phase 3 stage 5): run PFAS transport on the refined DISV flow field
and re-check the porewater >50 ng/L bias.

Reuses the structured builder's source/obs/params helpers (run_multianalyte_gwt) but builds the
GWT on the DISV grid built by build_disv_model.py (GWF at /tmp/rogue_disv_gwf). The CNC source is
REFINED: each structured source (row,col) maps to ALL DISV sub-cells covering it (disv_map.npz),
so the source zone is now resolved at ~31 m instead of 250 m -- the lever for the >50 ng/L bias.

Per-analyte: build GWT(DISV)+exchange on a fresh copy of the DISV GWF, run, take cmax over depth
(ncpl), aggregate back to the structured (row,col) by max for apples-to-apples porewater validation,
save cmax_disv_<analyte>.npz. Run from repo root with .venv python.
"""
import os, sys, glob, shutil, numpy as np, pandas as pd, flopy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_multianalyte_gwt as S   # joint_sources, obs_cells, params, LEAN5, constants

EXE = "/data/SWATGenXApp/codes/bin/mf6"
OUT = S.OUT
WS_GWF = "/tmp/rogue_disv_gwf"
GRIDPROPS = f"{OUT}/disv_gridprops.npy"
NYEARS, PERLEN = S.NYEARS, S.PERLEN


def main():
    gp = np.load(GRIDPROPS, allow_pickle=True).item()
    ncpl = int(gp["ncpl"]); ndlay = int(gp["nlay"])
    m = np.load(f"{OUT}/disv_map.npz")
    mr, mc, idom_d = m["mr"], m["mc"], m["idom_d"]          # parent (row,col) + idomain per DISV cell
    # inverse map: structured (row,col) -> list of DISV cells
    from collections import defaultdict
    inv = defaultdict(list)
    for i in range(ncpl):
        inv[(int(mr[i]), int(mc[i]))].append(i)

    SRC = S.joint_sources()
    summary = []
    for a in (sys.argv[1:] or ["PFOS"]):
        src, val = SRC[a], S.obs_cells(a)
        Kf = float(S.params.loc[a, "Kf"]); nF = float(S.params.loc[a, "n"]); bg = 1.0
        ws = f"/tmp/rogue_disv_{a}"
        shutil.rmtree(ws, ignore_errors=True)
        sim = flopy.mf6.MFSimulation.load(sim_ws=WS_GWF, exe_name=EXE, verbosity_level=0)
        sim.set_sim_path(ws)
        gwf = sim.get_model(); gwfname = gwf.name
        gwf.sto.steady_state.set_data({0: True})
        # 40-year transient TDIS with ATS (mirror the structured run)
        sim.remove_package("tdis")
        ats = [(i, PERLEN / 8.0, 0.01, PERLEN, 2.0, 5.0) for i in range(NYEARS)]
        tdis = flopy.mf6.ModflowTdis(sim, nper=NYEARS, time_units="days",
                                     perioddata=[(PERLEN, 8, 1.2) for _ in range(NYEARS)])
        flopy.mf6.ModflowUtlats(tdis, maxats=len(ats), perioddata=ats, filename="pfas.ats")
        nre = gwf.get_package("sfr_0").nreaches.array
        gwt = flopy.mf6.ModflowGwt(sim, modelname="pfas", save_flows=True)
        flopy.mf6.ModflowGwtdisv(gwt, nlay=ndlay, ncpl=ncpl, nvert=int(gp["nvert"]),
                                 top=np.asarray(gp["top"], float), botm=np.asarray(gp["botm"], float),
                                 vertices=gp["vertices"], cell2d=gp["cell2d"], idomain=idom_d,
                                 length_units="meters")
        flopy.mf6.ModflowGwtic(gwt, strt=bg)
        flopy.mf6.ModflowGwtadv(gwt, scheme="tvd")
        flopy.mf6.ModflowGwtdsp(gwt, alh=S.ALH, ath1=S.ATH, diffc=S.DIFFC)
        flopy.mf6.ModflowGwtmst(gwt, porosity=S.POROSITY, sorption="freundlich",
                                bulk_density=S.BULK_DENSITY, distcoef=Kf, sp2=nF)
        # REFINED source: spread each structured source cell onto its DISV sub-cells (layer 0, top active)
        cnc = []
        for r in src.itertuples():
            val_c = min(float(r.max_value), S.SRC_CAP)
            for ic in inv.get((int(r.row), int(r.col)), []):
                if idom_d[0, ic] != 0:
                    cnc.append([(0, ic), val_c])
        flopy.mf6.ModflowGwtcnc(gwt, stress_period_data={0: cnc}, pname="cnc")
        flopy.mf6.ModflowGwtssm(gwt, sources=[[]])
        flopy.mf6.ModflowGwtsft(gwt, flow_package_name="sfr_0", save_flows=True,
                                packagedata=[[rr, 0.0] for rr in range(nre)],
                                concentration_filerecord="pfas.sft.ucn", pname="sft_0")
        flopy.mf6.ModflowGwtoc(gwt, concentration_filerecord="pfas.ucn",
                               saverecord=[("CONCENTRATION", "LAST")])
        flopy.mf6.ModflowGwfgwt(sim, exgtype="GWF6-GWT6", exgmnamea=gwfname, exgmnameb="pfas",
                                filename="pfas.gwfgwt")
        ims = flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                                   outer_dvclose=1e-3, inner_dvclose=1e-4, outer_maximum=500,
                                   inner_maximum=500, filename="pfas.ims")
        sim.register_ims_package(ims, ["pfas"])
        sim.write_simulation(silent=True)
        ok, buff = sim.run_simulation(silent=True)
        if not ok:
            print(f"[{a}] DISV GWT FAILED (src cells {len(cnc)})"); print("\n".join(buff[-10:])); continue
        c = flopy.utils.HeadFile(glob.glob(f"{ws}/pfas.ucn")[0], text="CONCENTRATION").get_data()
        c = np.squeeze(np.asarray(c))                      # DISV get_data may be (nlay,1,ncpl)
        if c.ndim == 1: c = c[None, :]
        cmax_cell = np.nanmax(np.where(idom_d != 0, c, np.nan), axis=0)   # (ncpl,)
        # aggregate DISV cells back to structured (row,col) by max for porewater comparison
        nrow = int(mr.max()) + 1; ncol = int(mc.max()) + 1
        cmax = np.full((nrow, ncol), np.nan)
        for (r, cc), cells in inv.items():
            vals = [cmax_cell[i] for i in cells if np.isfinite(cmax_cell[i])]
            if vals: cmax[r, cc] = np.nanmax(vals)
        np.savez(f"{OUT}/cmax_disv_{a}.npz", cmax=cmax)
        mod = np.array([cmax[int(r.row), int(r.col)] for r in val.itertuples()]); obs = val.max_value.to_numpy()
        ok2 = np.isfinite(mod) & (mod > 0) & (obs > 0)
        lo, lm = np.log10(obs[ok2]), np.log10(mod[ok2])
        rmse = float(np.sqrt(np.mean((lo - lm) ** 2))); w10 = float(np.mean(np.abs(lo - lm) < 1.0))
        summary.append(dict(analyte=a, src_cells=len(cnc), val_cells=int(ok2.sum()),
                            plume_logRMSE=round(rmse, 2), within10x=round(100 * w10, 0)))
        print(f"[{a}] DISV plume {ok2.sum()} cells log-RMSE {rmse:.2f} within10x {100*w10:.0f}% "
              f"(src {len(cnc)} DISV cells)", flush=True)
    pd.DataFrame(summary).to_csv(f"{OUT}/disv_gwt_summary.csv", index=False)
    print("DONE -> disv_gwt_summary.csv + cmax_disv_*.npz", flush=True)


if __name__ == "__main__":
    main()

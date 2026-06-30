"""DISV refinement of the calibrated Rogue GWF (+GWT) model (Phase 3, stages 2-5).

Stage 2: resample the structured calibrated model's arrays (top/botm/k/k33/idomain/sy/ss/strt/
         recharge) onto the quadtree DISV grid built in stage 1 (disv_gridprops.npy, ncpl 28,239).
Stage 3: rebuild GWF on DISV -- NPF, RCHA, STO, IC, GHB/DRN/WEL, SFR (reaches remapped to DISV
         cells), IMS, OC. Flow-first so we can verify convergence + the gaining baseflow before
         adding transport.
Stage 5 (--gwt): add the multi-analyte GWT (ADV/DSP/MST-Freundlich/CNC source/SFT/exchange) and run.

Mapping is by nearest structured-cell centre (KDTree) in the shared LOCAL coordinate frame --
the gridgen DISV vertices are in the same local frame as the structured modelgrid, so refined
DISV cells inherit their parent structured cell's calibrated properties.

Run from repo root with .venv python:  python build_disv_model.py [--gwt]
"""
import os, sys, glob, shutil, numpy as np, pandas as pd, flopy
from scipy.spatial import cKDTree

ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL   = f"{ROGUE}/MODFLOW_sfr_cal"
EXE   = "/data/SWATGenXApp/codes/bin/mf6"
OUT   = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
GRIDPROPS = f"{OUT}/disv_gridprops.npy"
WS_GWF = "/tmp/rogue_disv_gwf"


def disv_centroids(gp):
    """Polygon centroids of each DISV cell2d entry, in the grid's local frame."""
    verts = {int(v[0]): (float(v[1]), float(v[2])) for v in gp["vertices"]}
    xc = np.zeros(gp["ncpl"]); yc = np.zeros(gp["ncpl"])
    for row in gp["cell2d"]:
        ic = int(row[0]); xc[ic] = float(row[1]); yc[ic] = float(row[2])  # cell2d carries (icpl, xc, yc, nv, v...)
    return xc, yc


def main(with_gwt=False):
    print("== Stage 2: load structured calibrated model + DISV grid ==", flush=True)
    sim0 = flopy.mf6.MFSimulation.load(sim_ws=CAL, exe_name=EXE, verbosity_level=0)
    gwf0 = sim0.get_model(); g0 = gwf0.modelgrid
    nlay, nrow, ncol = gwf0.dis.nlay.array, gwf0.dis.nrow.array, gwf0.dis.ncol.array
    k0   = gwf0.npf.k.array;   k330 = gwf0.npf.k33.array
    idom0 = gwf0.dis.idomain.array
    sy0  = gwf0.sto.sy.array;  ss0 = gwf0.sto.ss.array
    strt0 = gwf0.ic.strt.array
    # structured cell centres (local frame), row-major flatten matches (r,c)
    xcc = g0.xcellcenters.ravel(); ycc = g0.ycellcenters.ravel()
    rr, cc = np.meshgrid(np.arange(nrow), np.arange(ncol), indexing="ij")
    rr = rr.ravel(); cc = cc.ravel()
    tree = cKDTree(np.c_[xcc, ycc])

    gp = np.load(GRIDPROPS, allow_pickle=True).item()
    ncpl = int(gp["ncpl"]); ndlay = int(gp["nlay"])
    xc, yc = disv_centroids(gp)
    # map each DISV cell -> nearest structured (row,col)
    _, idx = tree.query(np.c_[xc, yc])
    mr = rr[idx]; mc = cc[idx]                      # parent structured row/col per DISV cell
    print(f"   structured {nlay}x{nrow}x{ncol}={nlay*nrow*ncol}  ->  DISV {ndlay}x{ncpl}", flush=True)

    # resample arrays onto DISV (nlay, ncpl)
    def resamp(arr):
        return np.stack([arr[L][mr, mc] for L in range(ndlay)], axis=0)
    k_d   = resamp(k0);   k33_d = resamp(k330)
    sy_d  = resamp(sy0);  ss_d  = resamp(ss0)
    strt_d = resamp(strt0)
    idom_d = resamp(idom0).astype(int)
    top_d = np.asarray(gp["top"], dtype=float)
    botm_d = np.asarray(gp["botm"], dtype=float)
    # recharge (structured RCHA -> top-cell array); squeeze to (nrow, ncol)
    rcharr = np.asarray(gwf0.get_package("rcha_0").recharge.array, dtype=float)
    while rcharr.ndim > 2:
        rcharr = rcharr[0]
    if rcharr.shape != (nrow, ncol):
        rcharr = rcharr.reshape(nrow, ncol)
    rch_d = rcharr[mr, mc]

    print("== Stage 3: build DISV GWF ==", flush=True)
    shutil.rmtree(WS_GWF, ignore_errors=True); os.makedirs(WS_GWF, exist_ok=True)
    sim = flopy.mf6.MFSimulation(sim_name="rogue_disv", sim_ws=WS_GWF, exe_name=EXE)
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="days")
    ims = flopy.mf6.ModflowIms(sim, complexity="COMPLEX", linear_acceleration="BICGSTAB",
                               outer_dvclose=1e-3, inner_dvclose=1e-4,
                               outer_maximum=500, inner_maximum=500)
    gwf = flopy.mf6.ModflowGwf(sim, modelname="modflow_sfr", save_flows=True, newtonoptions="NEWTON")
    flopy.mf6.ModflowGwfdisv(gwf, nlay=ndlay, ncpl=ncpl, nvert=int(gp["nvert"]),
                             top=top_d, botm=botm_d, vertices=gp["vertices"], cell2d=gp["cell2d"],
                             idomain=idom_d, length_units="meters")
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=1, k=k_d, k33=k33_d, save_specific_discharge=True)
    flopy.mf6.ModflowGwfic(gwf, strt=strt_d)
    flopy.mf6.ModflowGwfsto(gwf, iconvert=1, sy=sy_d, ss=ss_d, steady_state={0: True})
    flopy.mf6.ModflowGwfrcha(gwf, recharge=rch_d)

    # boundary packages: remap (lay,row,col) -> (lay, icpl) by nearest DISV cell to the structured centre
    dtree = cKDTree(np.c_[xc, yc])
    def cell_of(r, c):
        x = g0.xcellcenters[r, c]; y = g0.ycellcenters[r, c]
        return int(dtree.query([x, y])[1])
    for pkgname, cls in [("ghb_bnd", flopy.mf6.ModflowGwfghb), ("drn_0", flopy.mf6.ModflowGwfdrn),
                         ("wel_0", flopy.mf6.ModflowGwfwel)]:
        p0 = gwf0.get_package(pkgname)
        if p0 is None: continue
        spd0 = p0.stress_period_data.get_data(0)
        rows = []
        for rec in spd0:
            lay, r, c = rec[0]
            ic = cell_of(r, c)
            if idom_d[lay, ic] <= 0: continue
            rows.append([(lay, ic)] + list(rec)[1:])
        cls(gwf, stress_period_data={0: rows}, pname=pkgname)
        print(f"   {pkgname}: {len(rows)} entries remapped", flush=True)

    # SFR: remap each reach cellid to its DISV cell; keep connectiondata + perioddata as-is
    sfr0 = gwf0.get_package("sfr_0")
    pd0 = sfr0.packagedata.get_data()
    newpd = []
    for rec in pd0:
        rec = list(rec)
        lay, r, c = rec[1]
        rec[1] = (lay, cell_of(r, c))
        newpd.append(tuple(rec))
    cd0 = sfr0.connectiondata.get_data()
    prd0 = sfr0.perioddata.get_data()
    nreaches = sfr0.nreaches.array
    flopy.mf6.ModflowGwfsfr(gwf, nreaches=nreaches, packagedata=newpd, connectiondata=cd0,
                            perioddata=prd0, save_flows=True, pname="sfr_0",
                            budget_filerecord="modflow_sfr.sfr.cbc")
    flopy.mf6.ModflowGwfoc(gwf, head_filerecord="modflow_sfr.hds",
                           budget_filerecord="modflow_sfr.cbc",
                           saverecord=[("HEAD", "LAST"), ("BUDGET", "LAST")])
    sim.write_simulation(silent=True)
    print("   wrote DISV GWF; running flow ...", flush=True)
    ok, buff = sim.run_simulation(silent=True)
    if not ok:
        print("FLOW FAILED to converge:"); print("\n".join(buff[-15:])); return False
    # baseflow = sum of negative SFR GWF exchange (aquifer -> stream)
    try:
        cbc = flopy.utils.CellBudgetFile(f"{WS_GWF}/modflow_sfr.sfr.cbc")
        gwf_rec = cbc.get_data(text="GWF")[-1]
        q = np.array([r[2] for r in gwf_rec])
        gaining = -q[q < 0].sum()
        print(f"   FLOW OK. SFR gaining baseflow ~ {gaining:.3g} m3/d  ({gaining/86400:.3f} m3/s)", flush=True)
    except Exception as e:
        print("   FLOW OK (baseflow parse failed:", e, ")", flush=True)
    np.savez(f"{OUT}/disv_map.npz", mr=mr, mc=mc, idom_d=idom_d)
    print("== DISV GWF done -> /tmp/rogue_disv_gwf ; map saved disv_map.npz ==", flush=True)
    return True


if __name__ == "__main__":
    main(with_gwt="--gwt" in sys.argv)

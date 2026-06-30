"""Build the PEST++ pilot-point + baseflow calibration for 04124500.

- copies the MF6 model + mf6 binary into ./model, ./bin
- places pilot points on a coarse grid over the active domain
- precomputes the cell<-pilotpoint kernel-interpolation matrix W (smooth, kriging-like)
- writes obs_wells.csv (510 Wellogic heads) and the baseflow target
- builds params.dat + the PEST template/instruction files
- assembles control.pst via pyEMU: pilot-point log10-Kh-multipliers + globals
  (kv/rch/drn/riv/ghb), Tikhonov regularization toward the prior (multiplier 1), and
  observations = 510 heads + 1 net GW->stream baseflow (strongly weighted = the flux constraint)
"""
import os
import shutil
import numpy as np
import pandas as pd
import flopy
import pyemu

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_M = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_250m"
MF6 = "/data/SWATGenXApp/codes/bin/mf6"
PP_SPACING = 5            # pilot point every 5 cells (~1.25 km)
BASEFLOW_TARGET = 0.63    # m3/s gaining = observed USGS baseflow (22.4 cfs, BFI 0.62, full
                          # 158 km2 gauge = the model domain; streamflow file is in CFS)
HEAD_SIGMA = 5.0          # m
BASEFLOW_W = 12.0         # rebalanced: ~comparable to the head group at the start (was 40,
                          # which dominated phi and dragged heads down chasing an
                          # then-unreachable baseflow; now the per-reach stage offset makes
                          # baseflow achievable so it need not dominate)
STAGE_INIT = 3.0          # initial channel incision (m below cell-mean land surface)
STAGE_MAX = 12.0          # max incision


def main():
    os.makedirs(os.path.join(HERE, "model"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "bin"), exist_ok=True)
    for ext in ("nam tdis ims dis ic npf sto ghb riv drn wel chd rcha oc").split():
        for f in __import__("glob").glob(f"{SRC_M}/*.{ext}"):
            shutil.copy(f, os.path.join(HERE, "model", os.path.basename(f)))
    shutil.copy(f"{SRC_M}/mfsim.nam", os.path.join(HERE, "model"))
    shutil.copy(MF6, os.path.join(HERE, "bin", "mf6")); os.chmod(os.path.join(HERE, "bin", "mf6"), 0o755)

    sim = flopy.mf6.MFSimulation.load(sim_ws=os.path.join(HERE, "model"), exe_name=MF6, verbosity_level=0)
    g = sim.get_model(); mg = g.modelgrid; idom = g.dis.idomain.array
    nrow, ncol = idom.shape[1], idom.shape[2]
    act2d = idom[0] != 0
    xc, yc = mg.xcellcenters, mg.ycellcenters
    # local coords are fine (kernel uses distances); use grid index coords for stability
    II, JJ = np.meshgrid(np.arange(nrow), np.arange(ncol), indexing="ij")
    act_lin = np.where(act2d.ravel())[0]
    cx, cy = II.ravel()[act_lin].astype(float), JJ.ravel()[act_lin].astype(float)

    # pilot points: coarse grid, keep those inside the active domain
    pr, pc = np.meshgrid(np.arange(PP_SPACING // 2, nrow, PP_SPACING),
                         np.arange(PP_SPACING // 2, ncol, PP_SPACING), indexing="ij")
    pr, pc = pr.ravel(), pc.ravel()
    keep = act2d[pr, pc]
    pr, pc = pr[keep].astype(float), pc[keep].astype(float)
    npp = len(pr)

    # smooth kernel interpolation weights W (nactive x npp), Gaussian, row-normalized
    L = PP_SPACING * 1.3
    d2 = (cx[:, None] - pr[None, :]) ** 2 + (cy[:, None] - pc[None, :]) ** 2
    Wk = np.exp(-d2 / (2 * L * L))
    Wk /= Wk.sum(axis=1, keepdims=True)
    np.savez(os.path.join(HERE, "interp_W.npz"), W=Wk, act_lin=act_lin, nrow=nrow, ncol=ncol)
    print(f"pilot points: {npp}; active cells: {len(act_lin)}; W {Wk.shape}")

    # observation wells
    obs = pd.read_csv(f"{SRC_M}/obs_vs_sim.csv")
    obs = obs[(obs.obs_head_m > 150) & (obs.obs_head_m < 500)].reset_index(drop=True)
    obs[["row", "col", "obs_head_m"]].to_csv(os.path.join(HERE, "obs_wells.csv"), index=False)
    nh = len(obs)

    # RIV cell -> STREAM-ORDER group (one channel-incision param per stream order, not per
    # reach -- per-reach is over-parameterized/unidentifiable; incision scales with stream size)
    import geopandas as gpd
    riv_spd = g.get_package("riv_0").stress_period_data.get_data(0)
    grid = gpd.read_parquet(f"{SRC_M}/Grids_MODFLOW_centroids.parquet").to_crs(26990)
    gi = grid.set_index(["row", "col"]); gx2 = gi.geometry.x; gy2 = gi.geometry.y
    rivs = gpd.read_file(f"{SRC_M}/../SWAT_MODEL_Web_Application/Watershed/Shapes/rivs1.shp").to_crs(26990)
    rcells = [(int(r["cellid"][1]), int(r["cellid"][2])) for r in riv_spd if idom[tuple(r["cellid"])] != 0]
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy([gx2.loc[c] for c in rcells],
                                                       [gy2.loc[c] for c in rcells]), crs=26990)
    jn = gpd.sjoin_nearest(pts, rivs[["strmOrder", "geometry"]], how="left")
    jn = jn[~jn.index.duplicated(keep="first")]
    cell_ord = np.array([int(o) if pd.notna(o) else 2 for o in jn["strmOrder"].to_numpy()])
    orders = sorted(set(cell_ord.tolist()))                      # e.g. [2, 3, 4]
    ord2grp = {o: k for k, o in enumerate(orders)}
    ngrp = len(orders)
    riv_row = np.array([c[0] for c in rcells]); riv_col = np.array([c[1] for c in rcells])
    riv_grp = np.array([ord2grp[o] for o in cell_ord])
    np.savez(os.path.join(HERE, "riv_cell_group.npz"), riv_row=riv_row, riv_col=riv_col,
             riv_grp=riv_grp, orders=np.array(orders))
    print(f"RIV cells: {len(rcells)} -> {ngrp} stream-order groups {orders} (one incision param each)")

    # parameter list + template
    pnames = ([f"pp_{i:04d}" for i in range(npp)] + ["kv", "rch", "drn", "riv", "ghb", "pump"]
              + [f"st_g{k}" for k in range(ngrp)])
    pinit = {**{f"pp_{i:04d}": 0.0 for i in range(npp)},
             "kv": 0.0, "rch": 0.0, "drn": 0.0, "riv": 0.0, "ghb": 0.0,
             "pump": np.log10(0.15),                  # actual withdrawal ~15% of pump capacity (init)
             **{f"st_g{k}": STAGE_INIT for k in range(ngrp)}}   # rch/kv/.. log10; st_g = metres/order
    with open(os.path.join(HERE, "params.dat"), "w") as f:
        for n in pnames:
            f.write(f"{n} {pinit[n]:.6e}\n")
    with open(os.path.join(HERE, "params.dat.tpl"), "w") as f:
        f.write("ptf ~\n")
        for n in pnames:
            f.write(f"{n} ~{n:^16}~\n")
    # instruction file for obs.dat
    with open(os.path.join(HERE, "obs.dat.ins"), "w") as f:
        f.write("pif @\n")
        for i in range(nh):
            f.write(f"l1 w !h_{i:04d}!\n")
        f.write("l1 w !baseflow!\n")

    # build Pst
    pst = pyemu.Pst.from_io_files(os.path.join(HERE, "params.dat.tpl"), os.path.join(HERE, "params.dat"),
                                  os.path.join(HERE, "obs.dat.ins"), os.path.join(HERE, "obs.dat"),
                                  pst_path=".")
    par = pst.parameter_data
    par["partrans"] = "none"; par["parchglim"] = "relative"
    for n in pnames:
        par.loc[n, "parval1"] = pinit[n]
        if n.startswith("st_"):
            lo, hi = 0.0, STAGE_MAX                 # channel incision in metres
        elif n == "rch":
            lo, hi = np.log10(0.3), np.log10(2.0)
        elif n == "ghb":
            lo, hi = -2.0, 2.0
        elif n == "drn":
            lo, hi = -2.0, 1.0
        elif n == "pump":
            lo, hi = np.log10(0.02), 0.0            # actual withdrawal = 2%-100% of pump capacity
        else:
            lo, hi = -0.8, 0.8
        par.loc[n, "parlbnd"] = lo; par.loc[n, "parubnd"] = hi
    par["pargp"] = (["kh"] * npp + ["kv", "rch", "drn", "riv", "ghb", "pump"] + ["stage"] * ngrp)

    obsd = pst.observation_data
    obsd["weight"] = 0.0
    for i in range(nh):
        obsd.loc[f"h_{i:04d}", "obsval"] = float(obs.obs_head_m[i])
        obsd.loc[f"h_{i:04d}", "weight"] = 1.0 / HEAD_SIGMA
    obsd.loc["baseflow", "obsval"] = BASEFLOW_TARGET
    obsd.loc["baseflow", "weight"] = BASEFLOW_W
    obsd["obgnme"] = ["head"] * nh + ["baseflow"]

    pst.model_command = ["python3 forward_run.py"]
    pst.control_data.noptmax = 0           # set by run script (ies)
    # Tikhonov: prefer-value regularization toward the prior (multiplier 1 -> log10 = 0)
    pyemu.helpers.zero_order_tikhonov(pst, par_groups=["kh", "stage"])  # regularize K + incision toward prior
    pst.write(os.path.join(HERE, "control.pst"))
    print(f"wrote control.pst: {pst.npar} params ({npp} pilot pts), {pst.nobs} obs "
          f"({nh} heads + baseflow target {BASEFLOW_TARGET} m3/s)")


if __name__ == "__main__":
    main()

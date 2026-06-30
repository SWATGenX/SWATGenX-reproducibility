"""Build the PEST++ pilot-point + baseflow calibration for the Rogue (04118500), SFR model.

Adapts the 04124500 RIV setup to the SFR-based Rogue flow model. Differences:
  - template model = MODFLOW_sfr (the as-built; forward_run applies the continuous-bedrock
    conditioning + all calibration multipliers from priors).
  - head obs are generated here from the Wellogic static water levels (head = top - 0.3048*SWL),
    deduplicated to one observation per MODFLOW cell (median), inside the watershed.
  - SFR (not RIV): the stream baseflow lever is a streambed-K multiplier `sfrk`, not per-reach
    channel incision; the GW<->stream baseflow is read from the SFR budget GWF term.
  - globals: kv, rch (recharge), drn (seepage), ghb (divide perimeter), pump (well withdrawal),
    sfrk (streambed K). pilot points = log10 Kh multipliers over the active domain.
Baseflow target = 5.56 m3/s gaining (USGS 04118500, BFI 0.74).
"""
import os
import shutil
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import flopy
import pyemu

HERE = os.path.dirname(os.path.abspath(__file__))
ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
SRC_M = f"{ROGUE}/MODFLOW_sfr"
FGB = "/data/SWATGenXApp/codes/MODGenX"  # config path for the wellogic fgb
WELLOGIC = "/data/SWATGenXApp/GenXAppData/wellogic_wells/Wellogic_Wells_26990.fgb"
MF6 = "/data/SWATGenXApp/codes/bin/mf6"
OUTDIR = os.path.join(HERE, "rogue")
PP_SPACING = 7            # pilot point every 7 cells (~1.75 km) over the bigger Rogue domain
BASEFLOW_TARGET = 5.56    # m3/s gaining (USGS 04118500, BFI 0.74)
HEAD_SIGMA = 5.0
BASEFLOW_W = 12.0


def gen_head_obs(g, modflow_dir):
    """Wellogic SWL -> one head obs per active MODFLOW cell (median over wells in the cell)."""
    top = g.dis.top.array; idom = g.dis.idomain.array
    cen = gpd.read_parquet(os.path.join(modflow_dir, "Grids_MODFLOW_centroids.parquet")).to_crs(26990)
    b = cen.total_bounds
    w = gpd.read_file(WELLOGIC, bbox=tuple(b))
    w = w[(w.SWL > 0) & (w.SWL < 1000)].copy()
    j = gpd.sjoin_nearest(w.to_crs(26990), cen[["row", "col", "geometry"]], how="left",
                          distance_col="d")
    j = j[j.d < 250.0]
    j["row"] = j.row.astype(int); j["col"] = j.col.astype(int)
    rows = []
    for (r, c), grp in j.groupby(["row", "col"]):
        if idom[0, r, c] == 0:
            continue
        head = float(top[r, c]) - 0.3048 * float(grp.SWL.median())
        if 150 < head < 500:
            rows.append((r, c, round(head, 2)))
    return pd.DataFrame(rows, columns=["row", "col", "obs_head_m"])


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(os.path.join(OUTDIR, "model"), exist_ok=True)
    os.makedirs(os.path.join(OUTDIR, "bin"), exist_ok=True)
    for ext in "nam tdis ims dis ic npf sto ghb sfr drn wel rcha oc".split():
        for f in glob.glob(f"{SRC_M}/*.{ext}"):
            shutil.copy(f, os.path.join(OUTDIR, "model", os.path.basename(f)))
    for f in glob.glob(f"{SRC_M}/*.sfr.*"):  # sfr cbc/stage filerecords referenced by name
        pass
    shutil.copy(f"{SRC_M}/mfsim.nam", os.path.join(OUTDIR, "model"))
    shutil.copy(MF6, os.path.join(OUTDIR, "bin", "mf6")); os.chmod(os.path.join(OUTDIR, "bin", "mf6"), 0o755)
    shutil.copy(f"{SRC_M}/Grids_MODFLOW_centroids.parquet", os.path.join(OUTDIR, "model"))

    sim = flopy.mf6.MFSimulation.load(sim_ws=os.path.join(OUTDIR, "model"), exe_name=MF6, verbosity_level=0)
    g = sim.get_model(); idom = g.dis.idomain.array
    nrow, ncol = idom.shape[1], idom.shape[2]
    act2d = idom[0] != 0

    obs = gen_head_obs(g, os.path.join(OUTDIR, "model"))
    obs.to_csv(os.path.join(OUTDIR, "obs_wells.csv"), index=False)
    nh = len(obs)
    print(f"head observations (one per cell): {nh}")

    # pilot points on a coarse grid, inside the active domain
    pr, pc = np.meshgrid(np.arange(PP_SPACING // 2, nrow, PP_SPACING),
                         np.arange(PP_SPACING // 2, ncol, PP_SPACING), indexing="ij")
    pr, pc = pr.ravel(), pc.ravel()
    keep = act2d[pr, pc]
    pr, pc = pr[keep].astype(float), pc[keep].astype(float)
    npp = len(pr)
    II, JJ = np.meshgrid(np.arange(nrow), np.arange(ncol), indexing="ij")
    act_lin = np.where(act2d.ravel())[0]
    cx, cy = II.ravel()[act_lin].astype(float), JJ.ravel()[act_lin].astype(float)
    L = PP_SPACING * 1.3
    d2 = (cx[:, None] - pr[None, :]) ** 2 + (cy[:, None] - pc[None, :]) ** 2
    Wk = np.exp(-d2 / (2 * L * L)); Wk /= Wk.sum(axis=1, keepdims=True)
    np.savez(os.path.join(OUTDIR, "interp_W.npz"), W=Wk, act_lin=act_lin, nrow=nrow, ncol=ncol)
    print(f"pilot points: {npp}; active cells: {len(act_lin)}")

    pnames = ([f"pp_{i:04d}" for i in range(npp)] + ["kv", "rch", "drn", "ghb", "pump", "sfrk"])
    pinit = {**{f"pp_{i:04d}": 0.0 for i in range(npp)},
             "kv": 0.0, "rch": np.log10(1.7), "drn": np.log10(0.05), "ghb": np.log10(0.1),
             "pump": np.log10(0.15), "sfrk": np.log10(0.5)}
    with open(os.path.join(OUTDIR, "params.dat"), "w") as f:
        for n in pnames:
            f.write(f"{n} {pinit[n]:.6e}\n")
    with open(os.path.join(OUTDIR, "params.dat.tpl"), "w") as f:
        f.write("ptf ~\n")
        for n in pnames:
            f.write(f"{n} ~{n:^16}~\n")
    with open(os.path.join(OUTDIR, "obs.dat.ins"), "w") as f:
        f.write("pif @\n")
        for i in range(nh):
            f.write(f"l1 w !h_{i:04d}!\n")
        f.write("l1 w !baseflow!\n")
    # a placeholder obs.dat so pyEMU can read template/instruction pairs
    with open(os.path.join(OUTDIR, "obs.dat"), "w") as f:
        for i in range(nh):
            f.write(f"h_{i:04d} 0.0\n")
        f.write("baseflow 0.0\n")

    pst = pyemu.Pst.from_io_files(os.path.join(OUTDIR, "params.dat.tpl"), os.path.join(OUTDIR, "params.dat"),
                                  os.path.join(OUTDIR, "obs.dat.ins"), os.path.join(OUTDIR, "obs.dat"),
                                  pst_path=".")
    par = pst.parameter_data
    par["partrans"] = "none"; par["parchglim"] = "relative"
    for n in pnames:
        par.loc[n, "parval1"] = pinit[n]
        if n == "rch":
            lo, hi = np.log10(0.5), np.log10(3.0)
        elif n == "ghb":
            lo, hi = -2.0, 0.5
        elif n == "drn":
            lo, hi = -2.0, 0.5
        elif n == "pump":
            lo, hi = np.log10(0.02), 0.0
        elif n == "sfrk":
            lo, hi = -1.5, 1.0
        else:
            lo, hi = -0.8, 0.8
        par.loc[n, "parlbnd"] = lo; par.loc[n, "parubnd"] = hi
    par["pargp"] = ["kh"] * npp + ["kv", "rch", "drn", "ghb", "pump", "sfrk"]

    obsd = pst.observation_data
    obsd["weight"] = 0.0
    for i in range(nh):
        obsd.loc[f"h_{i:04d}", "obsval"] = float(obs.obs_head_m[i])
        obsd.loc[f"h_{i:04d}", "weight"] = 1.0 / HEAD_SIGMA
    obsd.loc["baseflow", "obsval"] = BASEFLOW_TARGET
    obsd.loc["baseflow", "weight"] = BASEFLOW_W
    obsd["obgnme"] = ["head"] * nh + ["baseflow"]

    pst.model_command = ["python3 forward_run_rogue.py"]
    pst.control_data.noptmax = 0
    pyemu.helpers.zero_order_tikhonov(pst, par_groups=["kh"])
    pst.write(os.path.join(OUTDIR, "control.pst"))
    print(f"wrote control.pst: {pst.npar} params ({npp} pilot pts), {pst.nobs} obs "
          f"({nh} heads + baseflow {BASEFLOW_TARGET} m3/s)")


if __name__ == "__main__":
    main()

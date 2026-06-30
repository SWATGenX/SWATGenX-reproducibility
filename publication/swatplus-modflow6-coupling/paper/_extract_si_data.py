"""Extract MODFLOW-6 grid + groundwater-PFAS arrays from the www-data-owned Rogue model into a
repo-local cache (paper/_si_cache/), so make_si_figures.py can build the SI figures without
touching /data/.../Users at figure time.

Run as the model owner:
    sudo -n -u www-data /data/SWATGenXApp/codes/.venv/bin/python paper/_extract_si_data.py

Writes:
    _si_cache/si_mf6_grid.npz  -- nrow/ncol/idomain, water-table heads, recharge field,
                                  SFR reach cells, georeferenced cell centroids.
    _si_cache/si_gw_obs.npz    -- modeled plume (cmax), 846->73 observed GW-PFOS cells,
                                  prescribed source cells, per-reach SFT in-stream concentration.
    _si_cache/rogue_pp_vals.npy -- the 243 calibrated pilot-point log10 K-multipliers.

Everything else the SI needs (head obs/sim, pilot-point geometry, joint calibration, Paper-A
in-stream/soil CSVs) is already repo-local and is read directly by make_si_figures.py.
"""
import os
import glob
import numpy as np
import pandas as pd

R = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{R}/MODFLOW_sfr_cal"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_si_cache")
os.makedirs(OUT, exist_ok=True)


def grid():
    import flopy
    import geopandas as gpd
    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0)
    gwf = sim.get_model()
    dis = gwf.dis
    nlay, nrow, ncol = int(dis.nlay.array), int(dis.nrow.array), int(dis.ncol.array)
    idom = dis.idomain.array
    top = dis.top.array
    hds = flopy.utils.HeadFile(glob.glob(f"{CAL}/*.hds")[0]).get_data()
    wt = np.full((nrow, ncol), np.nan)
    for r in range(nrow):
        for c in range(ncol):
            for l in range(nlay):
                if idom[l, r, c] != 0 and hds[l, r, c] > -1e29:
                    wt[r, c] = hds[l, r, c]
                    break
    rch = np.array([])
    for nm in ("rch", "rcha", "rcha_0"):
        p = gwf.get_package(nm)
        if p is not None:
            arr = p.recharge.array
            rch = (np.array(arr[0]) if getattr(arr, "ndim", 2) == 3 else np.array(arr)).reshape(nrow, ncol)
            break
    sfr = gwf.get_package("sfr_0")
    pdata = sfr.packagedata.get_data()
    sfr_cells = np.array([[int(c[1]), int(c[2])] for c in pdata["cellid"]])
    cen = gpd.read_parquet(f"{R}/MODFLOW_sfr/Grids_MODFLOW_centroids.parquet").to_crs("EPSG:26990")
    cx = np.full((nrow, ncol), np.nan); cy = np.full((nrow, ncol), np.nan)
    for _, row in cen.iterrows():
        rr, cc = int(row["row"]), int(row["col"])
        if 0 <= rr < nrow and 0 <= cc < ncol:
            cx[rr, cc] = row.geometry.x; cy[rr, cc] = row.geometry.y
    np.savez(f"{OUT}/si_mf6_grid.npz", nrow=nrow, ncol=ncol, idom=idom.astype(np.int8),
             top=top, wt=wt, rch=rch, sfr_cells=sfr_cells, cx=cx, cy=cy)
    print(f"grid: wt finite {int(np.isfinite(wt).sum())}, rch {rch.size}, sfr {len(sfr_cells)}")


def gwpfas():
    d = pd.read_csv(f"{R}/SWAT_MODEL_Web_Application/pfas_gw_data/pfas_gw_PFOS.csv")
    d = d.dropna(subset=["row", "col", "max_value"])
    d["row"] = d.row.astype(int); d["col"] = d.col.astype(int)
    cm = d.groupby(["row", "col"])["max_value"].max().reset_index()
    res = np.load(f"{R}/rogue_pfas_results.npz")
    np.savez(f"{OUT}/si_gw_obs.npz", obs_row=cm.row.values, obs_col=cm.col.values,
             obs_val=cm.max_value.values, cmax=res["cmax"], reach_c=res["reach_c"],
             src_row=res["src_row"], src_col=res["src_col"])
    print(f"gwpfas: {len(cm)} obs cells, {len(res['src_row'])} source cells")


def ppvals():
    cp = pd.read_csv(f"{CAL}/calibrated_params.csv")
    pp = cp[cp.iloc[:, 0].astype(str).str.startswith("pp_")].iloc[:, 1].to_numpy(float)
    np.save(f"{OUT}/rogue_pp_vals.npy", pp)
    print(f"ppvals: {len(pp)} pilot points")


if __name__ == "__main__":
    for fn in (grid, gwpfas, ppvals):
        try:
            fn()
        except Exception as e:
            print(f"WARN {fn.__name__} failed: {e}")

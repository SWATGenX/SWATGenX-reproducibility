"""Area-weighted SWAT+ HRU -> MF6 recharge-cell map for the daily coupler (M2).

Output: mf6_recharge.map, read by mf6_coupler.f90.  Each line links one HRU's
overlap with one MF6 top-layer cell:
    rcha_idx  hru  weight
where rcha_idx = row*NCOL + col (0-based, row-major -- matches the BMI RECHARGE
array of shape (NROW*NCOL,)) and weight = overlap_area / cell_area.

The coupler then forms, each day, the MF6 recharge RATE (m/day):
    RECHARGE[rcha_idx] = sum_HRU( sepbtm(hru)/1000 * weight )

Header line: N_ENTRIES  N_RECHARGE(=NROW*NCOL)  NCOL  NHRU_MAX
"""
import sys
import numpy as np
import geopandas as gpd

R = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
GRID = f"{R}/MODFLOW_sfr/Grids_MODFLOW/Grids_MODFLOW.shp"
HRU = f"{R}/SWAT_MODEL_Web_Application/Watershed/Shapes/hrus2.shp"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mf6_engine_test/mf6_recharge.map"

grid = gpd.read_file(GRID)
NROW, NCOL = int(grid["row"].max()) + 1, int(grid["col"].max()) + 1
grid["cell_area"] = grid.geometry.area
print(f"grid {NROW}x{NCOL} = {NROW*NCOL} cells (crs {grid.crs})")

hru = gpd.read_file(HRU).to_crs(grid.crs)[["HRUS", "geometry"]].rename(columns={"HRUS": "hru"})
hru["hru"] = hru["hru"].astype(int)
print(f"HRUs: {len(hru)}  id range {hru['hru'].min()}..{hru['hru'].max()}")

print("intersecting HRUs x grid (spatial-indexed overlay)...")
inter = gpd.overlay(hru, grid[["row", "col", "cell_area", "geometry"]], how="intersection",
                    keep_geom_type=True)
inter["overlap"] = inter.geometry.area
inter = inter[inter["overlap"] > 1.0]                       # drop slivers < 1 m^2
inter["weight"] = inter["overlap"] / inter["cell_area"]
inter["rcha_idx"] = inter["row"].astype(int) * NCOL + inter["col"].astype(int)

# diagnostics: cell coverage + HRU coverage
cov = inter.groupby(["row", "col"])["weight"].sum()
print(f"map entries {len(inter)} | cells covered {len(cov)} | "
      f"mean cell coverage {cov.mean():.2f} (1.0=fully tiled by HRUs)")

m = inter[["rcha_idx", "hru", "weight"]].sort_values(["rcha_idx", "hru"])
with open(OUT, "w") as f:
    f.write(f"{len(m)} {NROW*NCOL} {NCOL} {int(hru['hru'].max())}\n")
    for idx, h, w in m.itertuples(index=False):
        f.write(f"{int(idx)} {int(h)} {w:.6e}\n")
print(f"wrote {OUT}  ({len(m)} entries)")

# total area sanity: sum(overlap) ~ HRU area within domain
print(f"total overlap area {inter['overlap'].sum()/1e6:.1f} km^2")

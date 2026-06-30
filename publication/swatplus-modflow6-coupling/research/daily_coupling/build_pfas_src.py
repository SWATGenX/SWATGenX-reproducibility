"""Add a GWT SRC (mass-source) package to the daily PFAS transport model and
write the HRU->cell PFAS-leaching map (M4b, PFAS down-coupling).

The SWAT+ coupler sets, each transport step, a per-cell PFAS mass loading rate
from the soil-profile leaching flux hpfasb_d%perc (kg/ha/day):

    SRC_rate[cell] = sum_HRU( perc[kg/ha] * overlap_area[ha] ) * 1e9   (ug/day)

(GWT concentration unit = ng/L, length = m, so the GWT internal mass unit is
ng/L*m^3 = ug; 1 kg = 1e9 ug.)  This replaces the prescribed CNC plume's source
with a land-derived PFAS source.  The vadose UZF/UZT lag is a later refinement.

Outputs: a daily GWT model with an SRC package (rate 0, overwritten via BMI) and
pfas_leach.map (src_index, hru, overlap_ha).  Usage:
    python build_pfas_src.py <gwt_ws> <out_ws> <map_out>
"""
import sys
import numpy as np
import geopandas as gpd
import flopy

gwt_ws = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mf6_daily_gwt"
out_ws = sys.argv[2] if len(sys.argv) > 2 else "/tmp/mf6_daily_gwt_src"
map_out = sys.argv[3] if len(sys.argv) > 3 else "/tmp/mf6_engine_test/pfas_leach.map"

R = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
GRID = f"{R}/MODFLOW_sfr/Grids_MODFLOW/Grids_MODFLOW.shp"
HRU = f"{R}/SWAT_MODEL_Web_Application/Watershed/Shapes/hrus2.shp"

# --- HRU x grid overlap (area-weighted), same geometry as the recharge map ---
grid = gpd.read_file(GRID)
NCOL = int(grid["col"].max()) + 1
hru = gpd.read_file(HRU).to_crs(grid.crs)[["HRUS", "geometry"]].rename(columns={"HRUS": "hru"})
hru["hru"] = hru["hru"].astype(int)
inter = gpd.overlay(hru, grid[["row", "col", "geometry"]], how="intersection", keep_geom_type=True)
inter["overlap_ha"] = inter.geometry.area / 1e4
inter = inter[inter["overlap_ha"] > 1e-4]
inter["row"] = inter["row"].astype(int)
inter["col"] = inter["col"].astype(int)

# --- load GWT model first (need idomain to place SRC at the top ACTIVE layer;
#     layer 1 is inactive at some cells, where a layer-1 source would error) ---
sim = flopy.mf6.MFSimulation.load(sim_ws=gwt_ws, verbosity_level=0)
gwt = sim.get_model("pfas")
idomain = gwt.dis.idomain.array          # (nlay, nrow, ncol)
nlay = idomain.shape[0]

def top_active_layer(r, c):
    for k in range(nlay):
        if idomain[k, r, c] > 0:
            return k
    return -1

# --- SRC cells = unique HRU-overlap cells with an active GWT column ---
uc = inter[["row", "col"]].drop_duplicates().sort_values(["row", "col"]).reset_index(drop=True)
rows = []
for r, c in zip(uc["row"], uc["col"]):
    k = top_active_layer(r, c)
    if k >= 0:
        rows.append((r, c, k))
cells = {(r, c): (i, k) for i, (r, c, k) in enumerate(rows)}
cell_index = {(r, c): i for (r, c), (i, k) in cells.items()}
print(f"SRC cells: {len(rows)} active (of {len(uc)} overlap cells; "
      f"{len(uc) - len(rows)} dropped as fully inactive)")

spd = [[(int(k), int(r), int(c)), 0.0] for (r, c, k) in rows]
flopy.mf6.ModflowGwtsrc(gwt, maxbound=len(spd), stress_period_data={0: spd},
                        pname="src_pfas", save_flows=True)
sim.set_sim_path(out_ws)
sim.write_simulation()
print(f"wrote daily GWT+SRC model -> {out_ws}")

# --- leach map: src_index (0-based into SRC list) , hru , overlap_ha ---
m = []
for r, c, h, ov in zip(inter["row"], inter["col"], inter["hru"], inter["overlap_ha"]):
    si = cell_index.get((r, c))
    if si is not None:                  # skip links to dropped (inactive) cells
        m.append((si, int(h), float(ov)))
m.sort()
with open(map_out, "w") as f:
    f.write(f"{len(m)} {len(rows)}\n")
    for si, h, ov in m:
        f.write(f"{si} {h} {ov:.6e}\n")
print(f"wrote {map_out}: {len(m)} HRU-cell leaching links over {len(cells)} SRC cells")

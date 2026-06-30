"""DISV stage 1: build a quadtree-refined grid for the Rogue GW model, refined in the
source->discharge corridor (where the porewater/in-stream validation shows the 250 m structured grid
under-delivers GW PFAS by smearing the steep plume gradient). Coarse 250 m elsewhere, ~62.5 m in the
discharge corridor, ~31 m at the source zones. Writes disv_gridprops.npy for stage 2 (resample inputs).
Run: .venv/bin/python build_disv_grid.py
"""
import flopy, numpy as np, pandas as pd, os, shutil
from flopy.utils.gridgen import Gridgen
from shapely.geometry import Point
from shapely.ops import unary_union

ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
GRIDGEN = "/data/SWATGenXApp/codes/bin/gridgen"

sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0)
gwf = sim.get_model(); mg = gwf.modelgrid; nlay = gwf.dis.nlay.array
base = mg.nrow * mg.ncol


def loc(cells):  # (row,col) -> local model (x,y)
    return [(float(mg.xcellcenters[r, c]), float(mg.ycellcenters[r, c])) for r, c in cells]


def polys(geom):  # -> list of shapely Polygons (flopy ingests shapely directly)
    return [geom] if geom.geom_type == "Polygon" else list(geom.geoms)


src = pd.read_csv(f"{ROGUE}/SWAT_MODEL_Web_Application/pfas_gw_data/pfas_gw_PFOS.csv")
srccells = src[src.max_value >= 1e4][["row", "col"]].drop_duplicates().astype(int).values.tolist()
r2c = pd.read_csv(f"{OUT}/reach_to_channel.csv")
corridor_ch = [556, 308, 261, 225, 189, 6, 5, 4, 3, 2, 1, 10, 11, 15, 18, 26]
corr = r2c[r2c.Channel.isin(corridor_ch)][["row", "col"]].astype(int).values.tolist()

corr_poly = unary_union([Point(xy).buffer(375) for xy in loc(corr)])
src_poly = unary_union([Point(xy).buffer(375) for xy in loc(srccells)])
print(f"corridor: {len(corr)} reach cells + {len(srccells)} source cells; "
      f"{len(polys(corr_poly))} corridor polygon(s)")

ws = "/tmp/gridgen_rogue"; shutil.rmtree(ws, ignore_errors=True); os.makedirs(ws)
g = Gridgen(mg, model_ws=ws, exe_name=GRIDGEN, surface_interpolation="replicate")
g.add_refinement_features(polys(corr_poly), "polygon", 2, range(nlay))   # 250 -> 62.5 m
g.add_refinement_features(polys(src_poly), "polygon", 2, range(nlay))    # 250 -> 62.5 m (source; was lvl3/31 m -- coarsened to ease the transport Courant cost)
g.build(verbose=False)
gp = g.get_gridprops_disv()
print(f"\nDISV grid: ncpl={gp['ncpl']} (base {base}) = {gp['ncpl']/base:.2f}x | nvert={gp['nvert']}")
print(f"min cell ~{250/2**3:.0f} m (source) / {250/2**2:.0f} m (corridor); {250:.0f} m elsewhere")
np.save(f"{OUT}/disv_gridprops.npy", gp, allow_pickle=True)
# also keep the gridgen object's disv export for the SFR/coupling rebuild in stage 2
print("STAGE 1 DONE -> disv_gridprops.npy")

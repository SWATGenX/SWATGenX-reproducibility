#!/usr/bin/env python3
"""Precompute the STATIC groundwater georeferencing for the coupled Morris SA:
the SFR-reach -> SWAT+ channel map, the channel downstream topology, drainage areas,
and the observation-cell list. None of these depend on the sampled parameters, so we
build them ONCE and the per-sample GW evaluation just reads cbc fluxes + ucn conc and
aggregates -- no per-run geopandas. Reuses joint_sw_gw_calibration georeferencing.
"""
import glob, numpy as np, pandas as pd, geopandas as gpd, flopy
ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
RIVS = glob.glob(f"{ROGUE}/SWAT_MODEL_Web_Application/Watershed/Shapes/rivs1.shp")[0]
OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/sa/static_gw.npz"

g = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0).get_model()
rc = np.array([[int(c[1]), int(c[2])] for c in g.get_package("sfr_0").packagedata.get_data()["cellid"]])
print("SFR reaches:", len(rc))
# reach cell -> georeferenced point -> nearest rivs channel
cen = gpd.read_parquet(f"{ROGUE}/MODFLOW_sfr/Grids_MODFLOW_centroids.parquet").to_crs("EPSG:26990")
ci = cen.set_index(["row", "col"]).geometry
pts = gpd.GeoDataFrame(geometry=[ci.loc[(r, c)] for r, c in rc], crs="EPSG:26990")
rivs = gpd.read_file(RIVS).to_crs("EPSG:26990")
j = gpd.sjoin_nearest(pts, rivs[["Channel", "geometry"]], how="left")
j = j[~j.index.duplicated(keep="first")]
reach_channel = j["Channel"].astype(int).to_numpy()
# channel downstream topology + drainage area
ch = rivs["Channel"].astype(int).to_numpy(); chr_ = rivs["ChannelR"].astype(int).to_numpy()
area = rivs["AreaC"].astype(float).to_numpy()
# observation cells (predicted, non-source) for the GW plume QoI
d = np.load("/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/paper/_si_cache/si_gw_obs.npz")
obs_rc = np.c_[d['obs_row'], d['obs_col']].astype(int); obs_val = d['obs_val']
src_rc = set(map(tuple, np.c_[d['src_row'], d['src_col']].astype(int)))
np.savez(OUT, reach_rc=rc, reach_channel=reach_channel, ch=ch, chr=chr_, area=area,
         obs_rc=obs_rc, obs_val=obs_val, src_rc=np.array(list(src_rc)),
         mainstem=np.array([26,18,15,11,10,1,2]), mean_q=7.51)
print("wrote", OUT, "| mainstem reaches mapped:",
      sum(int(c) in set(reach_channel.tolist()) for c in [26,18,15,11,10,1,2]))

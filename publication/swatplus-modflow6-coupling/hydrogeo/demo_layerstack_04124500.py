import sys, numpy as np, pandas as pd, geopandas as gpd, time
sys.path.insert(0, 'MODGenX'); import hydrogeo_layers as H
B = '${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500'
M = f'{B}/MODFLOW_250m'
SWAT_DEM = f'{B}/SWAT_MODEL_Web_Application/Watershed/Rasters/DEM/dem.tif'
FGB = '/data/SWATGenXApp/GenXAppData/wellogic_wells/Wellogic_Wells_26990.fgb'

gr = gpd.read_file(f'{M}/Grids_MODFLOW/Grids_MODFLOW.shp')
cen = gr.geometry.centroid; gr['gx'] = cen.x; gr['gy'] = cen.y
gx = gr.groupby('col')['gx'].mean().sort_index().to_numpy()
gy = np.sort(gr.groupby('row')['gy'].mean().to_numpy())
bbox = (gx.min(), gy.min(), gx.max(), gy.max())

# 1. top from SWAT DEM
top = H.swat_dem_to_grid(SWAT_DEM, gx, gy)
print('TOP from SWAT DEM: pctiles', np.round(np.nanpercentile(top, [5, 50, 95]), 1), '(model was ~234m)')

# 2. wells from FGB (fast) + cure
t = time.time(); wells = H.read_wells_bbox(FGB, bbox, pad=2500)
print(f'FGB read {len(wells)} wells in {time.time()-t:.2f}s')
df, qa = H.cure_wells(wells)

# 3. krige the needed surfaces onto the grid (rows north-up to match top)
def K(col, logt):
    m = df[col].notna()
    fld, se, cv = H.krige_surface(df['x'][m], df['y'][m], df[col][m], gx, gy,
                                  log_transform=logt, name=col)
    return fld[::-1, :], cv          # flip rows: krige y-ascending -> north-up
surf = {}
df['depth_to_bottom'] = df[['BOTAQ', 'WELL_DEPTH']].max(axis=1)
for col, logt in [('AQ_THK_1', False), ('depth_to_bottom', False), ('SWL', False),
                  ('H_COND_1', True), ('H_COND_2', True), ('V_COND_1', True), ('V_COND_2', True)]:
    surf[col], cv = K(col, logt)
surf['SWL_depth'] = surf.pop('SWL')

# 4. assemble stack
botm, kh, kv, info = H.build_layer_stack(top, surf)
print('STACK:', info)
print('  layer bottoms mean:', [round(float(np.nanmean(b)), 1) for b in botm])
print('  K horiz mean (m/d):', [round(float(np.nanmean(k)), 2) for k in kh])
wt = top - surf['SWL_depth']
print(f'  water-table elev mean {np.nanmean(wt):.1f}m  vs model bottom {np.nanmean(botm[-1]):.1f}m')
print(f'  WT inside domain: {info["wt_inside_domain_frac"]*100:.1f}% of cells (target ~100%)')

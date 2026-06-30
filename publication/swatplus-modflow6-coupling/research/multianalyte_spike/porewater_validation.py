"""POREWATER discharge validation — the direct test of the groundwater->stream pathway.

Compares the MODELED aquifer PFAS concentration at the streambed discharge cell (per-analyte GWT,
cmax_<analyte>.npz from run_multianalyte_gwt.py) against the MEASURED EGLE streambed PORE WATER
(source mi_egle_nk_porewater, 43 sites on the lower-mainstem reaches). This validates the pathway at
the discharge interface itself — not via the aquifer plume far away. Per-analyte log-space skill +
the modeled-vs-observed discharging-GW fingerprint.
"""
import sqlite3, numpy as np, pandas as pd, geopandas as gpd, flopy
from shapely.geometry import Point
ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
LEAN5 = ["PFOS", "PFOA", "PFHxS", "PFBS", "PFHxA"]

# --- georeferenced MODFLOW grid (the MF6 DIS is in LOCAL coords; use the grid shapefile for row/col) ---
GRID = f"{ROGUE}/MODFLOW_sfr/Grids_MODFLOW/Grids_MODFLOW.shp"
grid = gpd.read_file(GRID)  # EPSG:26990, fields row/col (0-based)

# --- measured porewater (site x analyte, max ng/L) + coords ---
c = sqlite3.connect("/data/SWATGenXApp/codes/web_application/instance/site.db")
o = pd.read_sql("""select o.site_id,o.analyte,o.max_value,o.n_detect,s.lat,s.lon
 from pfas_observation o join pfas_station s on o.site_id=s.site_id
 where o.source_id='mi_egle_nk_porewater'""", c)
sites = o[["site_id", "lat", "lon"]].drop_duplicates().reset_index(drop=True)
g = gpd.GeoDataFrame(sites, geometry=[Point(xy) for xy in zip(sites.lon, sites.lat)],
                     crs=4326).to_crs(grid.crs)
j = gpd.sjoin_nearest(g, grid[["row", "col", "geometry"]], how="left", distance_col="d")
rc = {r.site_id: (int(r.row), int(r["col"])) if pd.notna(r.row) else (None, None)
      for _, r in j.iterrows()}

val = o.pivot_table(index="site_id", columns="analyte", values="max_value", aggfunc="max")

print("=== POREWATER discharge validation: modeled aquifer conc vs measured streambed porewater ===")
print(f"porewater sites: {len(sites)} | mapped to grid cells: {sum(1 for v in rc.values() if v[0] is not None)}\n")
rows = []
mod_fp, obs_fp = {}, {}
for a in LEAN5:
    try:
        cmax = np.load(f"{OUT}/cmax_{a}.npz")["cmax"]
    except FileNotFoundError:
        print(f"  {a}: cmax grid not found (run_multianalyte_gwt.py still running?)"); continue
    pairs = []
    for sid, (rw, cl) in rc.items():
        if rw is None or sid not in val.index:
            continue
        obs = val.loc[sid, a] if a in val.columns else np.nan
        if pd.isna(obs):
            continue
        mod = cmax[rw, cl]
        if np.isfinite(mod):
            pairs.append((obs, mod))
            mod_fp[a] = mod_fp.get(a, 0) + (mod if np.isfinite(mod) else 0)
            obs_fp[a] = obs_fp.get(a, 0) + (obs if obs > 0 else 0)
    if not pairs:
        continue
    obs_a = np.array([p[0] for p in pairs]); mod_a = np.array([p[1] for p in pairs])
    m = (obs_a > 0) & (mod_a > 0)
    if m.sum() >= 3:
        lo, lm = np.log10(obs_a[m]), np.log10(mod_a[m])
        rmse = float(np.sqrt(np.mean((lo - lm) ** 2))); bias = float(np.mean(lm - lo))
        w10 = float(np.mean(np.abs(lo - lm) < 1.0))
        rows.append((a, int(m.sum()), round(rmse, 2), round(bias, 2), round(100 * w10)))
print(f"{'analyte':8s} {'n':>4s} {'logRMSE':>8s} {'bias':>6s} {'within10x%':>10s}")
for a, n, rm, bi, w in rows:
    print(f"{a:8s} {n:4d} {rm:8.2f} {bi:6.2f} {w:10d}")

# discharging-GW fingerprint: modeled vs observed porewater composition
tot_m = sum(mod_fp.get(a, 0) for a in LEAN5); tot_o = sum(obs_fp.get(a, 0) for a in LEAN5)
if tot_m > 0 and tot_o > 0:
    print("\n=== discharging-GW fingerprint: modeled vs observed porewater composition ===")
    print(f"{'analyte':8s} {'observed':>9s} {'modeled':>9s}")
    l1 = 0
    for a in LEAN5:
        of = obs_fp.get(a, 0) / tot_o; mf = mod_fp.get(a, 0) / tot_m; l1 += abs(of - mf)
        print(f"{a:8s} {of:9.3f} {mf:9.3f}")
    print(f"L1 distance = {l1:.3f}")
pd.DataFrame(rows, columns=["analyte", "n", "logRMSE", "bias", "within10x_pct"]).to_csv(
    f"{OUT}/porewater_validation.csv", index=False)
print("\nsaved porewater_validation.csv")

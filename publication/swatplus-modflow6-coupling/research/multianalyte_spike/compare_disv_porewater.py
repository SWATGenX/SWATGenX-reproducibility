"""Stage-5 success test: does DISV refinement close the porewater >50 ng/L bias?

Range-stratified porewater validation (modeled aquifer conc at the streambed discharge cell vs
measured EGLE streambed porewater), computed for BOTH the structured grid (cmax_<analyte>.npz) and
the DISV grid (cmax_disv_<analyte>.npz), pooled across the LEAN-5 analytes and binned by observed
concentration. The structured baseline had bias -1.43 dex / 27% within 10x in the >50 ng/L band;
this reports whether DISV moves it toward zero.
"""
import os, sqlite3, numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import Point

ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
LEAN5 = ["PFOS", "PFOA", "PFHxS", "PFBS", "PFHxA"]
# fair comparison: only analytes with BOTH a structured and a DISV cmax (handles partial sets)
COMMON = [a for a in LEAN5 if os.path.exists(f"{OUT}/cmax_{a}.npz") and os.path.exists(f"{OUT}/cmax_disv_{a}.npz")]
BANDS = [("MDL-10", 0, 10), ("10-50", 10, 50), (">50", 50, np.inf)]

grid = gpd.read_file(f"{ROGUE}/MODFLOW_sfr/Grids_MODFLOW/Grids_MODFLOW.shp")
c = sqlite3.connect("/data/SWATGenXApp/codes/web_application/instance/site.db")
o = pd.read_sql("""select o.site_id,o.analyte,o.max_value,s.lat,s.lon
 from pfas_observation o join pfas_station s on o.site_id=s.site_id
 where o.source_id='mi_egle_nk_porewater'""", c)
sites = o[["site_id", "lat", "lon"]].drop_duplicates().reset_index(drop=True)
g = gpd.GeoDataFrame(sites, geometry=[Point(xy) for xy in zip(sites.lon, sites.lat)],
                     crs=4326).to_crs(grid.crs)
j = gpd.sjoin_nearest(g, grid[["row", "col", "geometry"]], how="left", distance_col="d")
rc = {r.site_id: (int(r.row), int(r["col"])) if pd.notna(r.row) else (None, None) for _, r in j.iterrows()}
val = o.pivot_table(index="site_id", columns="analyte", values="max_value", aggfunc="max")


def pairs_for(tag):
    """pooled (obs, mod) pairs across analytes for a cmax set ('' = structured, 'disv_' = DISV)."""
    obs_all, mod_all = [], []
    for a in COMMON:
        try:
            cmax = np.load(f"{OUT}/cmax_{tag}{a}.npz")["cmax"]
        except FileNotFoundError:
            continue
        for sid, (rw, cl) in rc.items():
            if rw is None or sid not in val.index or a not in val.columns:
                continue
            obs = val.loc[sid, a]
            if pd.isna(obs) or obs <= 0:
                continue
            mod = cmax[rw, cl]
            if np.isfinite(mod) and mod > 0:
                obs_all.append(float(obs)); mod_all.append(float(mod))
    return np.array(obs_all), np.array(mod_all)


def stratify(obs, mod):
    rows = []
    for name, lo, hi in BANDS:
        m = (obs >= lo) & (obs < hi)
        if m.sum() == 0:
            rows.append((name, 0, np.nan, np.nan, np.nan)); continue
        lO, lM = np.log10(obs[m]), np.log10(mod[m])
        rows.append((name, int(m.sum()), float(np.mean(lM - lO)),
                     float(np.sqrt(np.mean((lM - lO) ** 2))), float(np.mean(np.abs(lM - lO) < 1.0))))
    return rows


print("=== Porewater validation: structured grid vs DISV-refined grid (pooled LEAN-5) ===\n")
out = []
for tag, label in [("", "structured(250m)"), ("disv_", "DISV(31-62m corridor)")]:
    obs, mod = pairs_for(tag)
    if len(obs) == 0:
        print(f"{label}: no cmax files yet"); continue
    print(f"--- {label}: {len(obs)} pairs ---")
    print(f"{'band':8s} {'n':>4s} {'bias_dex':>9s} {'logRMSE':>8s} {'within10x':>9s}")
    for name, n, bias, rmse, w10 in stratify(obs, mod):
        print(f"{name:8s} {n:4d} {bias:9.2f} {rmse:8.2f} {0 if np.isnan(w10) else round(100*w10):9}")
        out.append(dict(grid=label, band=name, n=n, bias_dex=round(bias, 2) if not np.isnan(bias) else None,
                        logRMSE=round(rmse, 2) if not np.isnan(rmse) else None,
                        within10x_pct=None if np.isnan(w10) else round(100 * w10)))
    print()
pd.DataFrame(out).to_csv(f"{OUT}/disv_porewater_comparison.csv", index=False)
print("saved disv_porewater_comparison.csv")
# headline verdict on the >50 band
d = pd.DataFrame(out)
try:
    s = d[(d.grid.str.startswith("structured")) & (d.band == ">50")].bias_dex.iloc[0]
    v = d[(d.grid.str.startswith("DISV")) & (d.band == ">50")].bias_dex.iloc[0]
    print(f"\n>50 ng/L bias:  structured {s:+.2f} dex  ->  DISV {v:+.2f} dex  "
          f"({'CLOSED toward 0' if abs(v) < abs(s) else 'NOT improved'})")
except Exception:
    pass

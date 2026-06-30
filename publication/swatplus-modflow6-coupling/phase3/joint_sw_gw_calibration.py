"""Joint surface-water + groundwater PFAS calibration on the Rogue mainstem.

Resolves the double-counting that an additive two-stage calibration produces. In-stream PFOS at a
mainstem reach is linear in BOTH the surface soil-loading and the groundwater source strength, so
the combined prediction is

    C_i = (L/L0) * C^SW_i  +  g * B_i

where C^SW_i is the surface-water engine's modeled in-stream PFOS at the reference soil-loading L0
(=0.11), L is the (re-)calibrated soil-loading, B_i is the groundwater contribution at reach i (the
cumulative groundwater-discharged PFAS load upstream of i, divided by the streamflow there) at the
reference modeled groundwater source, and g is the calibrated groundwater-source effectiveness.
Fitting (L, g) JOINTLY by non-negative least squares against the observed mainstem PFOS partitions
the signal between the two pathways instead of forcing the soil-loading to absorb the groundwater
contribution -- so the surface and groundwater legs constrain each other against the same data.

g < 1 then has a clean meaning: the fraction of the *modeled* groundwater load that effectively
reaches the stream, i.e. a calibrated (not asserted) measure of interception + the double-counting
already in the surface leg.
"""
import os
import glob
import numpy as np
import pandas as pd
import geopandas as gpd
import flopy
from scipy.optimize import nnls

ROGUE = os.environ.get(
    "SWATGENX_ROGUE_DIR",
    "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500",
)
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
RIVS = glob.glob(f"{ROGUE}/SWAT_MODEL_Web_Application/Watershed/Shapes/rivs1.shp")[0]
MEAN_Q = 7.51            # m3/s at the outlet
L0 = 0.11               # reference surface soil-loading (Paper A)

# Paper A mainstem table (upstream -> downstream): channel, observed, SW-modeled at L0
MAINSTEM = pd.DataFrame({
    "channel": [26, 18, 15, 11, 10, 1, 2],
    "station": ["RR-0600", "RR-0300", "RR-0200", "RR-0060", "RR-0050", "RR-0010", "RR-0020"],
    "obs":     [6.3, 6.8, 7.2, 6.7, 9.6, 19.0, 27.0],
    "sw_mod":  [6.2, 7.7, 9.2, 11.2, 12.4, 14.7, 15.4]})


def gw_load_per_channel():
    """Map the per-reach groundwater PFAS load to SWAT+ channels (snap reach cell -> nearest reach)."""
    cbc = flopy.utils.CellBudgetFile(glob.glob(f"{CAL}/*.sfr.cbc")[0])
    rec = cbc.get_data(text="GWF")[-1]
    qgw = rec["q"] if rec.dtype.names else np.array([r[2] for r in rec])
    g = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0).get_model()
    rc = np.array([[int(c[1]), int(c[2])] for c in g.get_package("sfr_0").packagedata.get_data()["cellid"]])
    res = np.load(f"{ROGUE}/rogue_pfas_results.npz"); cmax = res["cmax"]
    src = set(map(tuple, np.c_[res["src_row"], res["src_col"]]))
    caq = np.array([cmax[r, c] for r, c in rc])
    is_src = np.array([(r, c) in src for r, c in rc])
    load = np.where((qgw > 0) & ~is_src, qgw * caq * 1000.0, 0.0)      # ng/d per reach
    # reach cell -> GEOREFERENCED location from the centroids parquet (the modelgrid has no coord
    # offset set, so mg.xcellcenters are LOCAL, not EPSG:26990 -- using them mis-snaps every reach).
    cen = gpd.read_parquet(f"{ROGUE}/MODFLOW_sfr/Grids_MODFLOW_centroids.parquet").to_crs("EPSG:26990")
    ci = cen.set_index(["row", "col"]).geometry
    geom = [ci.loc[(r, c)] for r, c in rc]
    pts = gpd.GeoDataFrame(geometry=geom, crs="EPSG:26990")
    rivs = gpd.read_file(RIVS).to_crs("EPSG:26990")
    j = gpd.sjoin_nearest(pts, rivs[["Channel", "geometry"]], how="left")
    j = j[~j.index.duplicated(keep="first")]
    ch = j["Channel"].to_numpy()
    out = {}
    for c, l in zip(ch, load):
        out[int(c)] = out.get(int(c), 0.0) + l
    return out, rivs


def cumulative_upstream(rivs, per_ch_load):
    """Cumulative groundwater load reaching each channel: propagate each loaded channel's load
    DOWNSTREAM (channel -> ChannelR -> ... -> outlet), accumulating it into every channel on the
    flow path. So a channel's value is the sum of loads from all channels at or upstream of it."""
    ch = rivs["Channel"].astype(int).to_numpy()
    chr_ = rivs["ChannelR"].astype(int).to_numpy()
    area = dict(zip(ch, rivs["AreaC"].astype(float).to_numpy()))
    nd = {int(c): int(d) for c, d in zip(ch, chr_)}      # channel -> receiving channel
    valid = set(ch.tolist())
    cum = {int(c): 0.0 for c in ch}
    for s, load in per_ch_load.items():
        if load <= 0:
            continue
        cur, seen = int(s), set()
        while cur in valid and cur not in seen:
            cum[cur] += load
            seen.add(cur)
            cur = nd.get(cur, -1)                          # walk downstream
    return cum, area


def main():
    per_ch, rivs = gw_load_per_channel()
    cum, area = cumulative_upstream(rivs, per_ch)
    amax = max(area.values())
    # B_i = cumulative GW load upstream of i (ng/d) / flow_i (L/d)  -> ng/L
    B = []
    for c in MAINSTEM.channel:
        q_i = MEAN_Q * area.get(c, amax) / amax        # m3/s scaled by drainage area
        B.append(cum.get(c, 0.0) / (q_i * 86400.0 * 1000.0))
    MAINSTEM["gw_unit"] = B
    A = (MAINSTEM.sw_mod / L0).to_numpy()              # SW contribution per unit loading
    Bv = MAINSTEM.gw_unit.to_numpy()
    y = MAINSTEM.obs.to_numpy()
    # joint NNLS: y = x0 * A + x1 * B  (x0 = soil-loading L, x1 = GW effectiveness g)
    X = np.c_[A, Bv]
    coef, _ = nnls(X, y)
    L, g = coef
    pred = X @ coef
    sw_part = L * A; gw_part = g * Bv
    rmse_log = np.sqrt(np.mean((np.log10(y) - np.log10(np.clip(pred, 1e-6, None))) ** 2))
    print(f"JOINT FIT: soil-loading L={L:.3f} (was {L0}); GW effectiveness g={g:.4f} "
          f"(=> {100*g:.1f}% of modeled GW load reaches the stream)")
    print(f"mainstem log-RMSE: SW-only(Paper A)=0.15 dex -> joint={rmse_log:.2f} dex")
    print(f"{'ch':>3} {'station':>8} {'obs':>6} {'SW-only':>7} {'joint':>6} {'SWpart':>6} {'GWpart':>6}")
    for i, r in MAINSTEM.iterrows():
        print(f"{r.channel:>3} {r.station:>8} {r.obs:>6.1f} {r.sw_mod:>7.1f} {pred[i]:>6.1f} "
              f"{sw_part[i]:>6.1f} {gw_part[i]:>6.1f}")
    print(f"\nGW contribution share at the lower mainstem (ch2): "
          f"{100*gw_part[-1]/pred[-1]:.0f}% of predicted; at headwaters (ch26): "
          f"{100*gw_part[0]/pred[0]:.0f}%")
    np.savez("/tmp/joint_calibration.npz", L=L, g=g, channel=MAINSTEM.channel.values,
             obs=y, sw_only=MAINSTEM.sw_mod.values, joint=pred, sw_part=sw_part, gw_part=gw_part,
             gw_unit=Bv)
    # figure
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os
    x = np.arange(len(MAINSTEM))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(x, y, "ks-", lw=2, label="observed")
    ax.plot(x, MAINSTEM.sw_mod, "o--", color="tab:orange", label="surface-water model (alone)")
    ax.plot(x, pred, "^-", color="tab:blue", label=f"joint SW+GW fit (L={L:.3f}, g={g:.3f})")
    ax.bar(x, gw_part, width=0.5, color="tab:green", alpha=0.5, label="GW contribution in joint fit")
    ax.set_xticks(x); ax.set_xticklabels(MAINSTEM.station, rotation=30, fontsize=8)
    ax.set_ylabel("in-stream PFOS (ng/L)")
    ax.set_title("Joint SW+GW calibration, Rogue mainstem (upstream → downstream)\n"
                 f"the GW pathway explains the lower-mainstem excess (joint {rmse_log:.2f} vs "
                 f"SW-only 0.15 dex; g={g:.3f})", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    out = os.path.join(os.path.dirname(__file__), "../paper/figures/joint_calibration.png")
    fig.tight_layout(); fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

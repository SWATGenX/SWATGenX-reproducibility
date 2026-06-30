#!/usr/bin/env python3
"""Publication-quality GIS figures for the Rogue River SWAT+ PFAS manuscript.

Stack (per scouting): geopandas + matplotlib (agg, vector PDF) + mapclassify
(NaturalBreaks) + cmcrameri batlow + matplotlib-scalebar; contextily for the
location inset only. Native CRS EPSG:32616 (UTM 16N). Mirrors the prior Water
Research paper's signature multi-panel distributed-variable choropleths.
"""
import os, csv, math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, LogNorm, BoundaryNorm
import geopandas as gpd
import pandas as pd
import mapclassify
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar
try:
    from cmcrameri import cm as cmc
    SEQ = cmc.batlow; SEQR = cmc.batlow_r; DIV = cmc.vik
except Exception:
    SEQ = plt.cm.viridis; SEQR = plt.cm.viridis_r; DIV = plt.cm.RdBu_r

plt.rcParams.update({
    "font.size": 8, "font.family": "sans-serif", "axes.linewidth": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.bbox": "tight",
})

SHP = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/SWAT_MODEL_Web_Application/Watershed/Shapes"
HERE = os.path.dirname(os.path.abspath(__file__))
ASSIGN = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/SWAT_MODEL_Web_Application/pfas_data/pfas_stations_assignment.csv"
CRS = 32616

# ---- load layers ----
rivs = gpd.read_file(f"{SHP}/rivs1.shp").to_crs(CRS)
hrus = gpd.read_file(f"{SHP}/hrus1.shp").to_crs(CRS)
bnd  = gpd.read_file(f"{SHP}/watershed_boundary.shp").to_crs(CRS)
try:
    res = gpd.read_file(f"{SHP}/reservoirs.shp").to_crs(CRS)
except Exception:
    res = None

chan = pd.read_csv(f"{HERE}/channel_pfos.csv")
rivs = rivs.merge(chan, on="Channel", how="left")
soil = pd.read_csv(f"{HERE}/hru_soil_pfas.csv")
hrus["HRU"] = hrus["HRUS"].astype(str).str.extract(r"(\d+)")[0].astype("Int64")
hrus = hrus.merge(soil, on="HRU", how="left")

# stations (obs) + modeled by channel
st = pd.read_csv(ASSIGN)
st = st[st["max_water_ngL"].astype(float) > 0].copy()
modmap = dict(zip(chan["Channel"], chan["pfos_ngL"]))
st["mod"] = st["channel"].map(modmap)
gst = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st["lon"], st["lat"]), crs=4326).to_crs(CRS)
# Wolverine House St source ~ lower Rogue (near RR-0020)
wolv = gpd.GeoDataFrame(geometry=gpd.points_from_xy([-85.5906], [43.0824]), crs=4326).to_crs(CRS)

def north_arrow(ax, x=0.90, y=0.88):
    """Standard north arrow placed INSIDE the map frame: shaft up, 'N' above the tip."""
    ax.annotate("", xy=(x, y), xytext=(x, y - 0.085), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.3))
    ax.text(x, y + 0.008, "N", transform=ax.transAxes, ha="center", va="bottom",
            fontsize=9, fontweight="bold")

def scalebar(ax, length_fraction=0.25):
    """Frameless scale bar inset from the lower-left corner (inside the frame)."""
    ax.add_artist(ScaleBar(1, location="lower left", frameon=False, border_pad=0.8,
                           length_fraction=length_fraction, font_properties={"size": 7}))

def furniture(ax, scale=True, north=True):
    ax.set_axis_off()
    if scale:
        scalebar(ax)
    if north:
        north_arrow(ax)

def _fmt(v):
    """Publication number format: x.x×10^e for large/small, plain otherwise."""
    av = abs(v)
    if av >= 1e4 or (0 < av < 1e-2):
        m, e = f"{v:.1e}".split("e")
        return f"{float(m):.1f}$\\times$10$^{{{int(e)}}}$"
    if av >= 100:
        return f"{v:.0f}"
    if av >= 1:
        return f"{v:.1f}"
    return f"{v:.2f}"

def classified_legend_handles(values, k=5, cat_thresh=8):
    """Square-patch legend handles + a BoundaryNorm.

    Discrete fields (<= cat_thresh unique values, e.g. soil-class k_f / n) are
    rendered CATEGORICALLY (one swatch per value, single-value label) so the
    classifier cannot emit a degenerate '216-216' bin; continuous fields use
    NaturalBreaks intervals with en-dash labels.
    """
    vals = np.asarray(values, float)
    vals = vals[np.isfinite(vals)]
    uniq = np.unique(vals)
    if len(uniq) <= cat_thresh:                      # categorical
        # BoundaryNorm edges = midpoints between sorted unique values
        mids = (uniq[:-1] + uniq[1:]) / 2.0
        span = (uniq[-1] - uniq[0]) or 1.0
        edges = [uniq[0] - 0.01 * span] + list(mids) + [uniq[-1] + 0.01 * span]
        handles = [Patch(facecolor=SEQ(i / max(1, len(uniq) - 1)), edgecolor="none",
                         label=_fmt(v)) for i, v in enumerate(uniq)]
        return edges, handles
    kk = min(k, max(2, len(uniq)))
    nb = mapclassify.NaturalBreaks(vals, k=kk)
    edges = sorted(set([float(vals.min())] + [float(b) for b in nb.bins]))
    handles = []
    for i in range(len(edges) - 1):
        col = SEQ(i / max(1, len(edges) - 2))
        handles.append(Patch(facecolor=col, edgecolor="none",
                              label=f"{_fmt(edges[i])}–{_fmt(edges[i+1])}"))
    return edges, handles

def basemap_inset(ax_main):
    """Michigan locator: labelled basemap (state/cities/Great Lakes) + the basin outlined."""
    try:
        import contextily as cx
        axin = ax_main.inset_axes([0.0, 0.74, 0.34, 0.26])
        b3857 = bnd.to_crs(3857)
        c = b3857.geometry.centroid.iloc[0]
        padx, pady = 3.2e5, 4.2e5   # frame the Michigan Lower Peninsula around the basin
        axin.set_xlim(c.x-padx, c.x+padx); axin.set_ylim(c.y-pady, c.y+pady)
        # Positron WITH labels -> "Michigan", "Grand Rapids", "Lake Michigan" give instant context
        cx.add_basemap(axin, source=cx.providers.CartoDB.Positron, attribution=False)
        b3857.plot(ax=axin, facecolor="none", edgecolor="#dc2626", lw=1.2, zorder=4)
        axin.plot(c.x, c.y, marker="o", ms=4, mfc="#dc2626", mec="k", mew=0.4, zorder=5)
        axin.set_xticks([]); axin.set_yticks([])
        for s in axin.spines.values():
            s.set_linewidth(0.8); s.set_edgecolor("#374151")
    except Exception as e:
        print("inset skipped:", e)

# ===================================================================== FIG 1
def fig_study_area():
    fig, ax = plt.subplots(figsize=(3.5, 4.2))
    bnd.plot(ax=ax, facecolor="#f3f4f6", edgecolor="#374151", lw=0.8, zorder=1)
    # widen the Strahler-order line-width range so the river hierarchy is legible
    lw = 0.3 + 0.5 * (rivs["strmOrder"].fillna(1) - rivs["strmOrder"].min())
    rivs.plot(ax=ax, color="#3b82f6", lw=lw, zorder=2)
    # reservoirs omitted from the overview: the SWAT+ impoundment polygons clutter the
    # source corridor and are not part of this figure's message (network + stations + source).
    gst.plot(ax=ax, marker="o", color="#111827", markersize=14, zorder=5,
             edgecolor="white", linewidth=0.4)
    wolv.plot(ax=ax, marker="*", color="#dc2626", markersize=150, zorder=6,
              edgecolor="k", linewidth=0.5)
    furniture(ax)
    basemap_inset(ax)
    leg = [Line2D([0],[0], marker="*", color="w", mfc="#dc2626", mec="k", ms=12,
                  label="Wolverine / House St. source"),
           Line2D([0],[0], marker="o", color="w", mfc="#111827", mec="w", ms=7,
                  label="EGLE PFOS station ($n$=29)"),
           Line2D([0],[0], color="#3b82f6", lw=1.5, label="Stream network (590 reaches)")]
    # legend OUTSIDE the map frame (below) so it never overlaps the source/stations
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.01),
              fontsize=6.8, frameon=True, framealpha=0.95, borderpad=0.5,
              handletextpad=0.5, ncol=1)
    # source/CRS attribution + neatline (cartographic furniture; no title -> LaTeX caption)
    ax.text(0.01, 0.005, "Streams: NHDPlus HR · Source: EGLE · UTM 16N (EPSG:32616)",
            transform=ax.transAxes, fontsize=5.3, color="#6b7280", va="bottom", ha="left", zorder=10)
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False,
                               ec="#9ca3af", lw=0.6, zorder=20))
    # no embedded title (publication rule): title goes in the LaTeX caption
    fig.savefig(f"{HERE}/fig1_study_area.pdf"); fig.savefig(f"{HERE}/fig1_study_area.png", dpi=600)
    plt.close(fig); print("fig1 done")

# ===================================================================== FIG 2
def fig_instream_pfos():
    fig, ax = plt.subplots(figsize=(3.5, 4.2))
    bnd.plot(ax=ax, facecolor="#f8fafc", edgecolor="#9ca3af", lw=0.6, zorder=1)
    r = rivs.dropna(subset=["pfos_ngL"]).copy()
    pos = r[r["pfos_ngL"] > 0]
    # PFOS spans orders of magnitude and is highly right-skewed (a few hot reaches
    # near the source, most low) -> a LINEAR colorbar renders the whole network navy.
    # Use a LOG normalization to expose the full spatial gradient.
    vmin = max(0.05, float(np.nanpercentile(pos["pfos_ngL"], 5)))
    vmax = float(np.nanpercentile(pos["pfos_ngL"], 99))
    norm = LogNorm(vmin=vmin, vmax=vmax)
    lw = 0.3 + 0.25 * (rivs["strmOrder"].fillna(1) - rivs["strmOrder"].min())
    rivs.plot(ax=ax, color="#e5e7eb", lw=lw*0.6, zorder=2)
    pos.plot(ax=ax, column="pfos_ngL", cmap=SEQ, norm=norm,
             lw=0.4 + 0.35*(pos["strmOrder"].fillna(1)-pos["strmOrder"].min()), zorder=3)
    gst.plot(ax=ax, marker="o", color="none", markersize=11, zorder=5,
             edgecolor="#111827", linewidth=0.6)
    wolv.plot(ax=ax, marker="*", color="#dc2626", markersize=140, zorder=6,
              edgecolor="k", linewidth=0.5)
    furniture(ax)
    sm = ScalarMappable(norm=norm, cmap=SEQ); sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02, shrink=0.6)
    cb.set_label("Modeled in-stream PFOS (ng L$^{-1}$, log scale)", fontsize=7.5)
    cb.ax.tick_params(labelsize=7)
    leg = [Line2D([0],[0], marker="*", color="w", mfc="#dc2626", mec="k", ms=11,
                  label="Wolverine / House St. source"),
           Line2D([0],[0], marker="o", color="w", mfc="none", mec="#111827", ms=7,
                  label="EGLE PFOS station")]
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.01),
              fontsize=6.8, frameon=True, framealpha=0.95, borderpad=0.5, ncol=1)
    # no embedded title (publication rule)
    fig.savefig(f"{HERE}/fig2_instream_pfos.pdf"); fig.savefig(f"{HERE}/fig2_instream_pfos.png", dpi=600)
    plt.close(fig); print("fig2 done")

# ===================================================================== FIG 3
def fig_calibration():
    # AGGREGATE PER REACH: the 29 EGLE stations fall on 20 distinct modeled reaches;
    # several stations share a reach (and therefore one modeled value). Plotting per
    # station produces horizontal banding, so the scatter uses one point per reach with
    # the station-MAXIMUM observed concentration (source-relevant; keeps the source-
    # proximal signal that a mean would dilute). n consistent with the UA (20 reaches).
    s0 = gst.dropna(subset=["mod"]).copy()
    s0 = s0[(s0["max_water_ngL"].astype(float) > 0) & (s0["mod"].astype(float) > 0)]
    n_stations = len(s0)
    agg = s0.groupby("channel").agg(obs=("max_water_ngL", "max"),
                                    mod=("mod", "first")).reset_index()
    obs = agg["obs"].values; mod = agg["mod"].values
    n_reach = len(agg)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.6), gridspec_kw={"width_ratios":[1,1.15]})
    # (a) scatter log-log, one point per reach
    ax = axes[0]
    ax.scatter(obs, mod, s=26, c="#2563eb", edgecolor="k", linewidth=0.3, alpha=0.85, zorder=3)
    lim = [1, max(obs.max(), mod.max())*1.3]
    ax.plot(lim, lim, "k-", lw=0.8, label="1:1")
    ax.plot(lim, [2*x for x in lim], "k--", lw=0.5, alpha=0.6)
    ax.plot(lim, [0.5*x for x in lim], "k--", lw=0.5, alpha=0.6, label="$\\times$2 envelope")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("Observed PFOS (ng L$^{-1}$)"); ax.set_ylabel("Modeled PFOS (ng L$^{-1}$)")
    o, m = np.log10(obs), np.log10(mod)
    nse = 1 - np.sum((o-m)**2)/np.sum((o-o.mean())**2)
    rmse = math.sqrt(np.mean((o-m)**2))
    note = f"$n$={n_reach} reaches\n({n_stations} stations)\nlog-NSE={nse:.2f}\nlog-RMSE={rmse:.2f} dex"
    ax.text(0.05, 0.95, note, transform=ax.transAxes, va="top", fontsize=6.3,
            bbox=dict(boxstyle="round", fc="white", ec="0.7", alpha=0.9))
    ax.legend(loc="lower right", fontsize=6.5)
    ax.text(0.0, 1.02, "(a)", transform=ax.transAxes, fontweight="bold", va="bottom", fontsize=9)
    ax.tick_params(labelsize=7)
    # (b) station map, dots colored by observed
    d = s0
    ax = axes[1]
    bnd.plot(ax=ax, facecolor="#f8fafc", edgecolor="#9ca3af", lw=0.5)
    rivs.plot(ax=ax, color="#cbd5e1", lw=0.4)
    # observed PFOS is strongly right-skewed -> log scale so source-proximal enrichment
    # is visible instead of saturating to one colour (consistent with fig2)
    pos = d["max_water_ngL"].astype(float); pos = pos[pos > 0]
    vmin = max(0.5, float(np.nanpercentile(pos, 5)))
    vmax = float(np.nanpercentile(np.concatenate([obs, mod]), 95))
    norm = LogNorm(vmin=vmin, vmax=vmax)
    d.plot(ax=ax, column="max_water_ngL", cmap=SEQ, norm=norm, markersize=34,
           edgecolor="k", linewidth=0.4, alpha=0.9, zorder=5)
    wolv.plot(ax=ax, marker="*", color="#dc2626", markersize=110, edgecolor="k", linewidth=0.5, zorder=6)
    furniture(ax)
    sm = ScalarMappable(norm=norm, cmap=SEQ); sm.set_array([])
    cb = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02, shrink=0.6)
    cb.set_label("Observed PFOS (ng L$^{-1}$)", fontsize=7.5); cb.ax.tick_params(labelsize=7)
    leg = [Line2D([0],[0], marker="o", color="w", mfc=SEQ(0.5), mec="k", ms=7,
                  label="EGLE station (fill = observed)"),
           Line2D([0],[0], marker="*", color="w", mfc="#dc2626", mec="k", ms=11,
                  label="Wolverine / House St. source")]
    # legend BELOW the frame so it never overlaps the network/stations
    ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.01),
              fontsize=6, frameon=True, framealpha=0.95, borderpad=0.4, ncol=2)
    ax.text(0.0, 1.02, "(b)", transform=ax.transAxes, fontweight="bold", va="bottom", fontsize=9)
    fig.savefig(f"{HERE}/fig3_calibration.pdf"); fig.savefig(f"{HERE}/fig3_calibration.png", dpi=600)
    plt.close(fig); print("fig3 done")

# ===================================================================== FIG 4
def fig_soil_params():
    panels = [("sol_pfas_ugha", "Initial soil PFOS (µg ha$^{-1}$)"),
              ("kf", "Freundlich $k_f$ ((nmol kg$^{-1}$)/(nM)$^{n}$)"),
              ("nf", "Freundlich exponent $n$ (–)")]
    # extra bottom margin holds the per-panel square-patch legends (outside the data)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.4))
    fig.subplots_adjust(bottom=0.26, wspace=0.05, top=0.90)
    for i, (ax, (col, lab)) in enumerate(zip(axes, panels)):
        L = "abc"[i]
        g = hrus.dropna(subset=[col])
        edges, handles = classified_legend_handles(g[col].values, k=5)
        bnorm = BoundaryNorm(edges, ncolors=SEQ.N, clip=True)
        g.plot(ax=ax, column=col, cmap=SEQ, norm=bnorm, edgecolor="none")
        ax.collections[0].set_rasterized(True)
        bnd.plot(ax=ax, facecolor="none", edgecolor="#374151", lw=0.6)
        ax.set_axis_off()
        # ONE shared scalebar + north arrow on panel (a); panels share extent (caption notes it)
        if L == "a":
            scalebar(ax, length_fraction=0.3)
            north_arrow(ax, x=0.88, y=0.86)
        # square-patch legend BELOW the panel, en-dash interval labels, never over the map
        ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.02),
                  fontsize=6.5, frameon=False, handlelength=1.0, handleheight=1.0,
                  labelspacing=0.3, borderpad=0.2, title=None)
        ax.text(0.02, 0.97, f"({L})", transform=ax.transAxes, fontweight="bold", va="top", fontsize=8)
    fig.savefig(f"{HERE}/fig4_soil_params.pdf", dpi=600)
    fig.savefig(f"{HERE}/fig4_soil_params.png", dpi=600)
    plt.close(fig); print("fig4 done")

if __name__ == "__main__":
    fig_study_area()
    fig_instream_pfos()
    fig_calibration()
    fig_soil_params()
    print("ALL FIGURES DONE ->", HERE)

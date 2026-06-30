"""Rogue GW PFAS figure: measured-anchored plume, validation vs 846 obs, SFT in-stream routing."""
import os
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import flopy
from matplotlib_scalebar.scalebar import ScaleBar


def _furniture(ax):
    """Publication GIS furniture: scale bar (grid is in metres) + north arrow (grid is north-up)."""
    ax.add_artist(ScaleBar(1, units="m", location="lower right", box_alpha=0.7,
                           font_properties={"size": 7}))
    ax.annotate("N", xy=(0.95, 0.93), xytext=(0.95, 0.80), xycoords="axes fraction",
                ha="center", va="center", fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.3))


ROGUE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500"
CAL = f"{ROGUE}/MODFLOW_sfr_cal"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rogue_pfas_validation.png")


def main():
    d = np.load(f"{ROGUE}/rogue_pfas_results.npz")
    cmax, reach_c = d["cmax"], d["reach_c"]
    g = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0).get_model()
    mg = g.modelgrid; idom = g.dis.idomain.array[0]; ext = mg.extent
    xc, yc = mg.xcellcenters, mg.ycellcenters
    inactive = np.ma.masked_where(idom != 0, np.ones_like(idom))
    pdd = g.get_package("sfr_0").packagedata.get_data()
    rc = np.array([[int(cid[1]), int(cid[2])] for cid in pdd["cellid"]])
    rx, ry = xc[rc[:, 0], rc[:, 1]], yc[rc[:, 0], rc[:, 1]]
    vr, vco, vo = d["val_row"], d["val_col"], d["val_obs"]
    sr, sco = d["src_row"], d["src_col"]
    mod = np.array([cmax[int(r), int(c)] for r, c in zip(vr, vco)])

    fig = plt.figure(figsize=(16, 5.2))
    # (a) modeled GW plume + obs stations + source
    ax = fig.add_subplot(1, 3, 1)
    ax.imshow(inactive, extent=ext, origin="upper", cmap="Greys", vmin=0, vmax=2, alpha=0.12)
    pm = np.ma.masked_invalid(np.where(cmax > 1, cmax, np.nan))
    im = ax.imshow(pm, extent=ext, origin="upper", norm=LogNorm(vmin=10, vmax=1e5), cmap="turbo")
    ax.scatter(xc[vr, vco], yc[vr, vco], c=vo, norm=LogNorm(vmin=10, vmax=1e5), cmap="turbo",
               s=22, edgecolors="k", linewidths=0.4, label="obs GW PFOS")
    ax.plot(xc[sr, sco], yc[sr, sco], "*", color="white", ms=16, mec="k", label="House St source")
    ax.text(0.02, 0.97, "(a)", transform=ax.transAxes, fontweight="bold", va="top", fontsize=11)
    _furniture(ax)
    ax.set_xticks([]); ax.set_yticks([]); ax.legend(loc="lower left", fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02).set_label("GW PFOS (ng/L)", fontsize=8)
    # source zoom-inset: the near-source plume + obs stations are unresolvable at basin extent
    sx, sy = float(xc[sr, sco].mean()), float(yc[sr, sco].mean()); zh = 2500.0
    axa = ax.inset_axes([0.56, 0.56, 0.42, 0.42])
    axa.imshow(pm, extent=ext, origin="upper", norm=LogNorm(vmin=10, vmax=1e5), cmap="turbo")
    axa.scatter(xc[vr, vco], yc[vr, vco], c=vo, norm=LogNorm(vmin=10, vmax=1e5), cmap="turbo",
                s=34, edgecolors="k", linewidths=0.5)
    axa.plot(xc[sr, sco], yc[sr, sco], "*", color="white", ms=15, mec="k")
    axa.set_xlim(sx - zh, sx + zh); axa.set_ylim(sy - zh, sy + zh)
    axa.set_xticks([]); axa.set_yticks([])
    for s in axa.spines.values(): s.set_edgecolor("#b91c1c"); s.set_linewidth(1.3)
    ax.indicate_inset_zoom(axa, edgecolor="#b91c1c", lw=1.0)

    # (b) modeled vs observed scatter
    ax = fig.add_subplot(1, 3, 2)
    m = (mod > 0) & (vo > 0)
    ax.loglog(vo[m], mod[m], "o", ms=5, alpha=0.6, color="tab:blue")
    lim = [1, 2e5]
    ax.plot(lim, lim, "k-", lw=1)
    ax.plot(lim, [x * 10 for x in lim], "k--", lw=0.6); ax.plot(lim, [x / 10 for x in lim], "k--", lw=0.6)
    lo, lm = np.log10(vo[m]), np.log10(mod[m])
    rmse = np.sqrt(np.mean((lo - lm) ** 2)); w10 = np.mean(np.abs(lo - lm) < 1)
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_xlabel("observed GW PFOS (ng/L)")
    ax.set_ylabel("modeled (ng/L)")
    ax.text(0.02, 0.97, "(b)", transform=ax.transAxes, fontweight="bold", va="top", fontsize=11)
    ax.grid(alpha=0.3, which="both")

    # (c) SFT in-stream PFOS (raw, undiluted by surface flow)
    ax = fig.add_subplot(1, 3, 3)
    ax.imshow(inactive, extent=ext, origin="upper", cmap="Greys", vmin=0, vmax=2, alpha=0.12)
    wet = reach_c > 1
    sc = ax.scatter(rx[wet], ry[wet], c=reach_c[wet], norm=LogNorm(vmin=1, vmax=1e4),
                    cmap="viridis", s=8)
    ax.plot(xc[sr, sco], yc[sr, sco], "*", color="red", ms=14, mec="k")
    ax.text(0.02, 0.97, "(c)", transform=ax.transAxes, fontweight="bold", va="top", fontsize=11)
    _furniture(ax)
    ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02).set_label("in-stream PFOS (ng/L, undiluted)", fontsize=8)
    # source zoom-inset: near-source reaches carry the highest undiluted in-stream PFOS
    axc = ax.inset_axes([0.56, 0.56, 0.42, 0.42])
    axc.imshow(inactive, extent=ext, origin="upper", cmap="Greys", vmin=0, vmax=2, alpha=0.12)
    axc.scatter(rx[wet], ry[wet], c=reach_c[wet], norm=LogNorm(vmin=1, vmax=1e4), cmap="viridis", s=22)
    axc.plot(xc[sr, sco], yc[sr, sco], "*", color="red", ms=14, mec="k")
    axc.set_xlim(sx - zh, sx + zh); axc.set_ylim(sy - zh, sy + zh)
    axc.set_xticks([]); axc.set_yticks([])
    for s in axc.spines.values(): s.set_edgecolor("#b91c1c"); s.set_linewidth(1.3)
    ax.indicate_inset_zoom(axc, edgecolor="#b91c1c", lw=1.0)

    # no embedded title/suptitle (publication rule): description goes in the LaTeX caption
    fig.tight_layout()
    fig.savefig(OUT, dpi=350, bbox_inches="tight")
    print(f"wrote {OUT}  | val log-RMSE {rmse:.2f} dex, {100*w10:.0f}% within 10x")


if __name__ == "__main__":
    main()

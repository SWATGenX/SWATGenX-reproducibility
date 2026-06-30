"""Phase 3 (SFR/SFT) figure: GW PFAS plume + IN-STREAM routing of the discharged solute.

Two panels (conservative tracer vs Freundlich PFAS). Each shows the aquifer plume (faded) and
the SFR reaches coloured by in-stream concentration. The conservative tracer discharges to the
streams and SFT routes it DOWNSTREAM through the connected reach network (the new capability over
RIV); the Freundlich PFAS is retarded in the aquifer and has not reached the streams in 40 yr.
"""
import os
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import flopy

CAL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_cal_sfr"
MODEL_DIR = os.path.dirname(CAL)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "phase3_sfr_instream.png")


def main():
    d = np.load(f"{MODEL_DIR}/phase3_sfr_plumes.npz")
    src, rc = d["src"], d["reach_cells"]
    g = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0).get_model()
    mg = g.modelgrid; idom = g.dis.idomain.array[0]; ext = mg.extent
    xc, yc = mg.xcellcenters, mg.ycellcenters
    inactive = np.ma.masked_where(idom != 0, np.ones_like(idom))
    rx, ry = xc[rc[:, 0], rc[:, 1]], yc[rc[:, 0], rc[:, 1]]

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.0))
    pvmin, pvmax = 0.5, 100.0
    svmin, svmax = 0.1, 2.0
    for ax, (title, plume, reach) in zip(axes, [
            ("(a) Conservative tracer", d["consv_plume"], d["consv_reach"]),
            ("(b) Freundlich-sorbed PFAS", d["pfas_plume"], d["pfas_reach"])]):
        ax.imshow(inactive, extent=ext, origin="upper", cmap="Greys", vmin=0, vmax=2, alpha=0.12)
        pm = np.ma.masked_invalid(plume)
        ax.imshow(pm, extent=ext, origin="upper", norm=LogNorm(vmin=pvmin, vmax=pvmax),
                  cmap="YlOrBr", alpha=0.55)
        # all reaches faint, then in-stream concentration on top
        ax.plot(rx, ry, ".", color="lightsteelblue", ms=2.5, alpha=0.7, zorder=2)
        wet = reach > svmin
        sc = ax.scatter(rx[wet], ry[wet], c=reach[wet], cmap="viridis",
                        norm=LogNorm(vmin=svmin, vmax=svmax), s=26, zorder=3,
                        edgecolors="k", linewidths=0.3)
        ax.plot(xc[src[1], src[2]], yc[src[1], src[2]], "*", color="red", ms=18,
                mec="k", mew=1.2, zorder=4, label="PFAS source")
        ax.set_title(f"{title}  ({int(np.sum(wet))} stream reaches w/ solute)", fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
        if reach.max() > svmin:
            cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02)
            cb.set_label("in-stream conc (ng/L)", fontsize=8)
        ax.legend(loc="lower left", fontsize=8, framealpha=0.9)
    fig.suptitle("Phase 3 (SFR/SFT): groundwater PFAS plume + in-stream routing to the outlet\n"
                 "faded = aquifer plume (ng/L); coloured points = SFT in-stream concentration on "
                 "the connected reach network", fontsize=11, y=1.04)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"wrote {OUT}")
    print(f"conservative in-stream reaches >{svmin}: {int(np.sum(d['consv_reach'] > svmin))}, "
          f"max {d['consv_reach'].max():.2f} ng/L | PFAS: {int(np.sum(d['pfas_reach'] > svmin))}")


if __name__ == "__main__":
    main()

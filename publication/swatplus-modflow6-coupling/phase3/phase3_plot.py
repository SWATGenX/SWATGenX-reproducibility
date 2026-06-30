"""Phase 3 figure: PFAS (Freundlich-sorbed) vs conservative groundwater plume + breakthrough.

Reads phase3_plumes.npz (written next to the model by phase3_pfas_gwt.py) and the calibrated
GWF grid, and draws a 3-panel figure:
  (a) conservative tracer plume after 40 yr  (b) Freundlich-sorbed PFAS plume after 40 yr
  (c) breakthrough at the GW->stream discharge cell -- PFAS arrives later and lower (retardation)
"""
import os
import glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import flopy

CAL = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_cal"
MODEL_DIR = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "phase3_pfas_plume.png")


def main():
    d = np.load(os.path.join(MODEL_DIR, "phase3_plumes.npz"))
    pfas, consv, src, bcell = d["pfas"], d["consv"], d["src"], d["bcell"]

    sim = flopy.mf6.MFSimulation.load(sim_ws=CAL, verbosity_level=0)
    g = sim.get_model(); mg = g.modelgrid; idom = g.dis.idomain.array[0]
    ext = mg.extent
    inactive = np.ma.masked_where(idom != 0, np.ones_like(idom))
    riv = g.get_package("riv_0").stress_period_data.get_data(0)
    rr = np.array([(int(r["cellid"][1]), int(r["cellid"][2])) for r in riv])
    xc, yc = mg.xcellcenters, mg.ycellcenters

    fig = plt.figure(figsize=(15, 5.2))
    vmin, vmax = 0.5, 100.0   # floor above the 0.1 ng/L ambient background (suppresses speckle)
    for k, (title, plume) in enumerate([("(a) Conservative tracer, 40 yr", consv),
                                        ("(b) Freundlich-sorbed PFAS, 40 yr", pfas)]):
        ax = fig.add_subplot(1, 3, k + 1)
        ax.imshow(inactive, extent=ext, origin="upper", cmap="Greys", vmin=0, vmax=2, alpha=0.15)
        pm = np.ma.masked_invalid(plume)
        im = ax.imshow(pm, extent=ext, origin="upper", norm=LogNorm(vmin=vmin, vmax=vmax),
                       cmap="turbo")
        ax.plot(xc[rr[:, 0], rr[:, 1]], yc[rr[:, 0], rr[:, 1]], ".", color="steelblue",
                ms=2, alpha=0.6, label="streams (RIV)")
        ax.plot(xc[src[1], src[2]], yc[src[1], src[2]], "*", color="white", ms=18,
                mec="k", mew=1.2, label="PFAS source")
        ax.plot(xc[bcell[0], bcell[1]], yc[bcell[0], bcell[1]], "v", color="magenta", ms=11,
                mec="k", label="discharge cell")
        ax.set_title(title, fontsize=11)
        ax.set_xticks([]); ax.set_yticks([])
        if k == 0:
            ax.legend(loc="lower left", fontsize=7, framealpha=0.9)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cb.set_label("conc (ng/L)", fontsize=8)

    ax = fig.add_subplot(1, 3, 3)
    ax.plot(d["cv_t"], d["cv_bt"], "-", color="tab:gray", lw=2, label="conservative")
    ax.plot(d["pf_t"], d["pf_bt"], "-", color="tab:red", lw=2, label="PFAS (Freundlich)")
    ax.set_xlabel("years"); ax.set_ylabel("conc at discharge cell (ng/L)")
    ax.set_title("(c) GW→stream breakthrough", fontsize=11)
    ax.grid(alpha=0.3); ax.legend(fontsize=9)

    fig.suptitle("SWAT+ ↔ MODFLOW 6 coupling, Phase 3: PFAS groundwater fate & transport "
                 "(R≈10; sorption retards & delays the plume)", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"wrote {OUT}")
    # summary stats
    print(f"PFAS footprint (>1 ng/L): {int(np.nansum(pfas > 1))} cells; "
          f"conservative: {int(np.nansum(consv > 1))} cells")
    print(f"breakthrough cell (row,col)={tuple(bcell)}; "
          f"PFAS final {d['pf_bt'][-1]:.2f} ng/L vs consv {d['cv_bt'][-1]:.2f} ng/L")


if __name__ == "__main__":
    main()

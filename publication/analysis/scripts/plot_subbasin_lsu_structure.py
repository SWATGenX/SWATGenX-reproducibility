#!/usr/bin/env python3
"""Delineation STRUCTURE figure: NHDPlus HR vs corrected coarse-threshold TauDEM for the
same watershed (Oklawaha S, HUC12 030801020804). Each panel draws BOTH levels of the
SWAT+ spatial hierarchy — subbasins (thick boundary) and landscape units / LSUs (filled,
distinct colors) — plus the channel network, to show that a coarse TauDEM threshold
reproduces the NHDPlus HR structure: few subbasins, many catchment-scale LSUs.

Output: publication/figures/final/fig-subbasin-lsu-structure-S.png
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

# (panel title, MODEL_NAME, subtitle) — counts are read live from the shapefiles.
PANELS = [
    ("NHDPlus HR (production)", "SWAT_MODEL_Web_Application",
     "existing high-resolution network"),
    ("TauDEM — coarse threshold", "SWAT_MODEL_TauDEM_coarse_s15k_c500",
     "stream 15000 / channel 500 cells"),
]


def _read(site, model, name):
    p = Path(site) / model / "Watershed" / "Shapes" / name
    return gpd.read_file(p).to_crs("EPSG:5070") if p.is_file() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", required=True)
    ap.add_argument("--out", default="/data/SWATGenXApp/codes/publication/figures/final/fig-subbasin-lsu-structure-S.png")
    a = ap.parse_args()

    data = []
    for title, model, sub in PANELS:
        data.append({
            "title": title, "sub": sub,
            "subs": _read(a.site_dir, model, "subs1.shp"),
            "lsus": _read(a.site_dir, model, "lsus1.shp"),
            "rivs": _read(a.site_dir, model, "rivs1.shp"),
        })

    bounds = [d["lsus"].total_bounds for d in data if d["lsus"] is not None]
    xmin = min(b[0] for b in bounds); ymin = min(b[1] for b in bounds)
    xmax = max(b[2] for b in bounds); ymax = max(b[3] for b in bounds)

    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    for ax, d in zip(axes, data):
        n_sub = 0 if d["subs"] is None else len(d["subs"])
        n_lsu = 0 if d["lsus"] is None else len(d["lsus"])
        if d["lsus"] is not None:
            # Landscape units filled with categorical colors to expose the catchment-scale division.
            d["lsus"].plot(ax=ax, cmap="tab20", edgecolor="white", linewidth=0.3,
                           alpha=0.85, zorder=1)
        if d["subs"] is not None:
            # Subbasin boundaries — the coarse level — drawn thick on top.
            d["subs"].boundary.plot(ax=ax, color="black", linewidth=1.8, zorder=3)
        if d["rivs"] is not None:
            d["rivs"].plot(ax=ax, color="#0d47a1", linewidth=1.1, zorder=4)
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(d["title"], fontsize=12, fontweight="bold")
        ax.annotate(
            f"{n_sub} subbasin{'s' if n_sub != 1 else ''}  ·  {n_lsu} landscape units (LSUs)\n{d['sub']}",
            xy=(0.5, -0.05), xycoords="axes fraction", ha="center", va="top", fontsize=10,
        )

    # Shared legend explaining the two hierarchy levels.
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [
        Line2D([0], [0], color="black", lw=1.8, label="Subbasin boundary"),
        Patch(facecolor="#7fb3d5", edgecolor="white", label="Landscape unit (LSU)"),
        Line2D([0], [0], color="#0d47a1", lw=1.1, label="Channel network"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=10,
               bbox_to_anchor=(0.5, 0.005))

    fig.suptitle(
        "Same watershed, same SWAT+ hierarchy — NHDPlus HR vs coarse TauDEM "
        "(Oklawaha S, HUC12 030801020804)",
        fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=200, bbox_inches="tight")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()

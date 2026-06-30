#!/usr/bin/env python3
"""Internal test: side-by-side HRU map (hrus2.shp) for NHDPlus-HR vs TauDEM delineation
of the same watershed. Usage:
  .venv/bin/python publication/analysis/scripts/plot_hru_nhd_vs_taudem.py \
    --site-dir ${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0308/huc12_outlet/030801020804 \
    --nhd SWAT_MODEL_Web_Application --taudem SWAT_MODEL_TauDEM_auto --out /tmp/hru_nhd_vs_taudem_S.png
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd


def _load(site_dir, model):
    base = Path(site_dir) / model / "Watershed" / "Shapes"
    hru = gpd.read_file(base / "hrus2.shp")
    rivs = gpd.read_file(base / "rivs1.shp")
    return hru, rivs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site-dir", required=True)
    p.add_argument("--nhd", default="SWAT_MODEL_Web_Application")
    p.add_argument("--taudem", default="SWAT_MODEL_TauDEM_auto")
    p.add_argument("--out", default="/tmp/hru_nhd_vs_taudem_S.png")
    a = p.parse_args()

    nhd_h, nhd_r = _load(a.site_dir, a.nhd)
    tau_h, tau_r = _load(a.site_dir, a.taudem)

    # shared land-use color map so the two panels are directly comparable
    classes = sorted(set(nhd_h["Landuse"].dropna()) | set(tau_h["Landuse"].dropna()))
    cmap = plt.get_cmap("tab20")
    color = {c: cmap(i % 20) for i, c in enumerate(classes)}

    # shared extent (union) so the delineation size difference is visible
    xmin = min(nhd_h.total_bounds[0], tau_h.total_bounds[0])
    ymin = min(nhd_h.total_bounds[1], tau_h.total_bounds[1])
    xmax = max(nhd_h.total_bounds[2], tau_h.total_bounds[2])
    ymax = max(nhd_h.total_bounds[3], tau_h.total_bounds[3])

    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    panels = [
        (axes[0], nhd_h, nhd_r, f"NHDPlus HR\n{len(nhd_h)} HRUs  ·  {len(nhd_r)} channels  ·  "
                                f"{nhd_r['AreaC'].max()/100:.1f} km$^2$"),
        (axes[1], tau_h, tau_r, f"TauDEM (threshold)\n{len(tau_h)} HRUs  ·  {len(tau_r)} channels  ·  "
                                f"{tau_r['AreaC'].max()/100:.1f} km$^2$"),
    ]
    for ax, hru, rivs, title in panels:
        hru["_c"] = hru["Landuse"].map(color)
        hru.plot(ax=ax, color=hru["_c"], edgecolor="white", linewidth=0.15)
        rivs.plot(ax=ax, color="#1565c0", linewidth=0.8)
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal"); ax.set_title(title, fontsize=12)
        ax.set_xticks([]); ax.set_yticks([])

    handles = [plt.Rectangle((0, 0), 1, 1, fc=color[c], ec="white") for c in classes]
    fig.legend(handles, classes, title="Land use", loc="lower center",
               ncol=min(len(classes), 8), fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("HRU delineation comparison — Oklawaha S (HUC12 030801020804)", fontsize=13)
    fig.tight_layout(rect=(0, 0.06, 1, 0.97))
    fig.savefig(a.out, dpi=170, bbox_inches="tight")
    print(f"wrote {a.out}  (NHD {len(nhd_h)} HRUs vs TauDEM {len(tau_h)} HRUs)")


if __name__ == "__main__":
    main()

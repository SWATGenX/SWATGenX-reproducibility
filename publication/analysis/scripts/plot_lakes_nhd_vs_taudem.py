#!/usr/bin/env python3
"""Internal test: lakes + stream network for NHDPlus-HR vs TauDEM models of the same site.
Lake polygons are NHD-derived (shared); the panels differ in how each model's channels
route through the lakes."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd


def _load(site, m):
    base = Path(site) / m / "Watershed" / "Shapes"
    lakes = gpd.read_file(base / "SWAT_plus_lakes.shp").to_crs("EPSG:5070")
    rivs = gpd.read_file(base / "rivs1.shp").to_crs("EPSG:5070")
    subs = None
    sp = base / "SWAT_plus_subbasins.shp"
    if sp.is_file():
        subs = gpd.read_file(sp).to_crs("EPSG:5070")
    return lakes, rivs, subs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site-dir", required=True)
    p.add_argument("--nhd", default="SWAT_MODEL_Web_Application")
    p.add_argument("--taudem", default="SWAT_MODEL_TauDEM_auto")
    p.add_argument("--out", default="/tmp/lakes_nhd_vs_taudem_S.png")
    a = p.parse_args()

    nl, nr, ns = _load(a.site_dir, a.nhd)
    tl, tr, ts = _load(a.site_dir, a.taudem)

    xmin = min(nl.total_bounds[0], tl.total_bounds[0], nr.total_bounds[0], tr.total_bounds[0])
    ymin = min(nl.total_bounds[1], tl.total_bounds[1], nr.total_bounds[1], tr.total_bounds[1])
    xmax = max(nl.total_bounds[2], tl.total_bounds[2], nr.total_bounds[2], tr.total_bounds[2])
    ymax = max(nl.total_bounds[3], tl.total_bounds[3], nr.total_bounds[3], tr.total_bounds[3])

    fig, axes = plt.subplots(1, 2, figsize=(13, 7))
    for ax, lakes, rivs, subs, title in [
        (axes[0], nl, nr, ns, f"NHDPlus HR\n{len(nr)} channels  ·  {len(nl)} lakes ({lakes_area(nl):.2f} km$^2$)"),
        (axes[1], tl, tr, ts, f"TauDEM (threshold)\n{len(tr)} channels  ·  {len(tl)} lakes ({lakes_area(tl):.2f} km$^2$)"),
    ]:
        if subs is not None:
            subs.boundary.plot(ax=ax, color="0.8", linewidth=0.5)
        rivs.plot(ax=ax, color="#1565c0", linewidth=0.9, zorder=2)
        lakes.plot(ax=ax, facecolor="#4aa3df", edgecolor="#0b3d63", linewidth=0.6, alpha=0.85, zorder=3)
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal"); ax.set_title(title, fontsize=12)
        ax.set_xticks([]); ax.set_yticks([])

    fig.suptitle("Lakes + channel routing — Oklawaha S (HUC12 030801020804); lake polygons are NHD-derived (shared)",
                 fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(a.out, dpi=170, bbox_inches="tight")
    print(f"wrote {a.out}")


def lakes_area(g):
    return float(g.to_crs("EPSG:5070").area.sum() / 1e6)


if __name__ == "__main__":
    main()

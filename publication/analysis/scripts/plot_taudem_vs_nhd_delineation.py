#!/usr/bin/env python3
"""Publication figure: NHDPlus HR vs threshold-TauDEM delineation of the same lake-bearing
watershed (Oklawaha S, HUC12 030801020804). Channel network + lakes + subbasin boundary,
three panels, shared extent, annotated with outlet area / channels / lakes wired.
Output: publication/figures/final/fig-taudem-vs-nhd-delineation-S.png
"""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

TRUE_AREA_KM2 = 53.37  # WBD HU12 030801020804 polygon area = true basin drainage area


def _load(site, m):
    base = Path(site) / m / "Watershed" / "Shapes"
    out = {}
    for key, name in [("rivs", "rivs1.shp"), ("lakes", "SWAT_plus_lakes.shp"),
                      ("subs", "SWAT_plus_subbasins.shp")]:
        p = base / name
        out[key] = gpd.read_file(p).to_crs("EPSG:5070") if p.is_file() else None
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--site-dir", required=True)
    p.add_argument("--out", default="/data/SWATGenXApp/codes/publication/figures/final/fig-taudem-vs-nhd-delineation-S.png")
    a = p.parse_args()

    panels = [
        ("NHDPlus HR", "SWAT_MODEL_Web_Application", "52.6", "45", "4 lakes wired (reservoirs)"),
        ("TauDEM — square DEM", "SWAT_MODEL_TauDEM_auto", "67.6", "63", "lakes dropped"),
        ("TauDEM — DEM clipped to basin", "SWAT_MODEL_TauDEM_nolakes_clip", "43.1", "25", "lakes dropped"),
    ]
    data = [(t, _load(a.site_dir, m), area, nch, lk) for t, m, area, nch, lk in panels]

    bounds = [d[1]["rivs"].total_bounds for d in data if d[1]["rivs"] is not None]
    xmin = min(b[0] for b in bounds); ymin = min(b[1] for b in bounds)
    xmax = max(b[2] for b in bounds); ymax = max(b[3] for b in bounds)

    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2))
    for ax, (title, g, area, nch, lk) in zip(axes, data):
        if g["subs"] is not None:
            g["subs"].boundary.plot(ax=ax, color="0.78", linewidth=0.6)
        if g["rivs"] is not None:
            g["rivs"].plot(ax=ax, color="#1565c0", linewidth=1.0, zorder=2)
        if g["lakes"] is not None:
            g["lakes"].plot(ax=ax, facecolor="#4aa3df", edgecolor="#0b3d63",
                            linewidth=0.6, alpha=0.85, zorder=3)
        ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, fontsize=12, fontweight="bold")
        delta = (float(area) - TRUE_AREA_KM2) / TRUE_AREA_KM2 * 100.0
        ax.annotate(
            f"outlet area {area} km$^2$  ({delta:+.0f}% vs true {TRUE_AREA_KM2:.0f})\n"
            f"{nch} channels  ·  {lk}",
            xy=(0.5, -0.06), xycoords="axes fraction", ha="center", va="top", fontsize=10,
        )

    fig.suptitle(
        "NHDPlus HR vs threshold-TauDEM — same lake-bearing watershed (Oklawaha S, HUC12 030801020804)",
        fontsize=13, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.95))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=200, bbox_inches="tight")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()

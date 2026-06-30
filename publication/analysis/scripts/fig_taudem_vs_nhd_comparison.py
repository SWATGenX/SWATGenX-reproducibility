#!/usr/bin/env python3
"""Figures for the TauDEM-vs-NHDPlus-HR page: (1) a two-panel delineation map showing
channels + wired lakes for the NHDPlus-HR and TauDEM+lakes models, and (2) the initial
(uncalibrated) simulated-vs-observed daily hydrograph at gage 02239501.

Reads the sim series/metrics produced by compare_initial_sim_nhd_vs_taudem.py.
Writes PNGs to both publication/figures/final/ and the website public/figures/ dir.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

REPO = Path("/data/SWATGenXApp/codes")
SITE = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0308/huc12_outlet/030801020804")
SIM_DIR = Path("/tmp/taudem_init_sim")
PUB = REPO / "publication/figures/final"
WEB = REPO / "web_application/frontend/public/figures"
ALBERS = "EPSG:5070"

MODELS = [
    {"key": "nhd", "label": "NHDPlus HR", "model": "SWAT_MODEL_Web_Application",
     "subtitle": "52.6 km² · 45 channels · 4 lakes wired"},
    {"key": "taudem", "label": "TauDEM + lakes", "model": "SWAT_MODEL_TauDEM_split_s500c100_clip",
     "subtitle": "43.1 km² · 299 channels · 4 lakes wired (split, 500/100)"},
]
GAGE_LONLAT = (-82.0412, 29.2149764)


def _read_layers(model_name: str):
    base = SITE / model_name / "Watershed" / "Shapes"
    subs = gpd.read_file(base / "subs1.shp").to_crs(ALBERS)
    rivs = gpd.read_file(base / "rivs1.shp").to_crs(ALBERS)
    lakes = None
    lk = base / "SWAT_plus_lakes.shp"
    if lk.is_file():
        lakes = gpd.read_file(lk).to_crs(ALBERS)
    return subs, rivs, lakes


def delineation_map(out_png: Path):
    layers = [(_read_layers(m["model"]), m) for m in MODELS]
    # common extent = union of both subbasin bounds, with margin
    xs0 = min(l[0][0].total_bounds[0] for l in layers)
    ys0 = min(l[0][0].total_bounds[1] for l in layers)
    xs1 = max(l[0][0].total_bounds[2] for l in layers)
    ys1 = max(l[0][0].total_bounds[3] for l in layers)
    mx, my = (xs1 - xs0) * 0.06, (ys1 - ys0) * 0.06

    gage = gpd.GeoSeries(gpd.points_from_xy([GAGE_LONLAT[0]], [GAGE_LONLAT[1]]),
                         crs="EPSG:4326").to_crs(ALBERS)

    fig, axes = plt.subplots(1, 2, figsize=(11, 6.2))
    for ax, ((subs, rivs, lakes), m) in zip(axes, layers):
        subs.plot(ax=ax, facecolor="#eef1f4", edgecolor="#b9c2cc", linewidth=0.5, zorder=1)
        if "strmOrder" in rivs.columns:
            lw = 0.4 + 0.5 * (rivs["strmOrder"] - rivs["strmOrder"].min())
        else:
            lw = 0.8
        rivs.plot(ax=ax, color="#2b6cb0", linewidth=lw, zorder=2)
        if lakes is not None and len(lakes):
            lakes.plot(ax=ax, facecolor="#38b2ac", edgecolor="#1d6f6a", linewidth=0.6, alpha=0.85, zorder=3)
        gage.plot(ax=ax, color="#e53e3e", marker="*", markersize=190,
                  edgecolor="white", linewidth=0.7, zorder=4)
        ax.set_xlim(xs0 - mx, xs1 + mx)
        ax.set_ylim(ys0 - my, ys1 + my)
        ax.set_title(f"{m['label']}\n{m['subtitle']}", fontsize=11, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor("#cbd5e0")

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [
        Line2D([0], [0], color="#2b6cb0", lw=2, label="SWAT+ channels"),
        Patch(facecolor="#38b2ac", edgecolor="#1d6f6a", alpha=0.85, label="Lakes (wired as reservoirs)"),
        Patch(facecolor="#eef1f4", edgecolor="#b9c2cc", label="Subbasins"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#e53e3e", markersize=15,
               markeredgecolor="white", label="USGS gage 02239501"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("Same basin, same 30 m DEM, same NHD lakes — NHDPlus-HR vs threshold-TauDEM delineation",
                 fontsize=12, fontweight="bold", y=0.99)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    for d in (PUB, WEB):
        d.mkdir(parents=True, exist_ok=True)
        fig.savefig(d / out_png.name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote delineation map -> {out_png.name}")


def hydrograph(out_png: Path):
    series = pd.read_csv(SIM_DIR / "initial_sim_series.csv", parse_dates=["date"])
    meta = json.loads((SIM_DIR / "initial_sim_metrics.json").read_text())
    mk = {m["key"]: m for m in MODELS}
    colors = {"nhd": "#2b6cb0", "taudem": "#dd6b20"}

    yr0 = pd.to_datetime(series["date"]).dt.year.min()
    yr1 = pd.to_datetime(series["date"]).dt.year.max()
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.plot(series["date"], series["obs_cms"], color="#1a202c", lw=1.1, label="Observed (USGS)", zorder=3)
    for key in ("nhd", "taudem"):
        col = f"{key}_outlet_cms"   # cross-validated channel = basin outlet (max chandeg DA)
        if col not in series:
            continue
        o = meta["models"][key]["outlet"]
        lbl = (f"{mk[key]['label']} · outlet ch{o['gisChannel']} ({o['daKm2']} km²) — "
               f"NSE {o['nse']:+.1f}, monthly r {o['monthlyR']:+.2f}")
        ax.plot(series["date"], series[col].clip(lower=1e-3), color=colors[key], lw=0.9, alpha=0.9, label=lbl)

    ax.set_yscale("log")
    ax.set_ylabel("Daily streamflow (m³/s, log)", fontsize=10)
    ax.set_title(f"Initial (uncalibrated) SWAT+ simulation vs observed — Oklawaha gage 02239501, {yr0}–{yr1}",
                 fontsize=11.5, fontweight="bold")
    ax.legend(fontsize=9, loc="lower center", ncol=3, framealpha=0.9)
    ax.grid(True, alpha=0.25, which="both")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=0, ha="center")
    ax.margins(x=0.01)
    ax.text(0.01, 0.97, "Gage = Silver River (Silver Springs): observed flow is artesian spring discharge,\n"
                        "not surface runoff (NWIS lists no drainage area; CV 0.22). Both surface delineations\n"
                        "undersimulate ~20× by the same margin — a source/process mismatch, not a delineation one.",
            transform=ax.transAxes, va="top", ha="left", fontsize=8.0, color="#4a5568",
            bbox=dict(boxstyle="round,pad=0.3", fc="#f7fafc", ec="#cbd5e0"))
    fig.tight_layout()
    for d in (PUB, WEB):
        d.mkdir(parents=True, exist_ok=True)
        fig.savefig(d / out_png.name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote hydrograph -> {out_png.name}")


if __name__ == "__main__":
    delineation_map(Path("fig-taudem-vs-nhd-delineation-lakes.png"))
    hydrograph(Path("fig-taudem-vs-nhd-hydrograph.png"))

#!/usr/bin/env python3
"""
Draft static maps for locked evaluation basins (no web basemaps).

Reads `status=locked_from_inventory` rows from tab-model-complexity.csv, resolves
showcase workspace paths (same layout as print_locked_basin_paths.py), loads
SWAT_plus_streams.shp and SWAT_plus_subbasins.shp from Watershed/Shapes/, and
optionally SWAT_plus_lakes.shp when present.

Default outputs are **drafts** under ``publication/figures/drafts/`` (ignored in git).

With ``--final``, writes manuscript-ready maps under ``publication/figures/final/`` using
stem ``fig-example-basin-maps`` (no draft watermark). Default raster dpi is **300** for
``--final`` and **150** for drafts (override with ``--dpi``).

With ``--final --layout combined``, writes a **single-row** manuscript figure: each basin is
**independently zoomed** to its merged vector bounds (panels are not a common geographic
scale). The figure emphasizes SWAT+ structure (subbasins, streams, lakes); quantitative
area and counts belong in **Tab-ModelComplexity**.

Same locked rows and shapefile inputs as drafts.

Writes a sidecar JSON with tier, model_id, state, area_km2, HRU/channel/subbasin/lake
counts from the CSV plus output paths.

Dependencies: geopandas, matplotlib (and a GDAL/fiona stack for shapefile I/O).

Environment (same as print_locked_basin_paths.py):
  USER_PATH, EXAMPLE_MODELS_USERNAME, SWAT_SHOWCASE_MODEL_DIR

Usage (from repo root):
  python3 publication/analysis/scripts/render_example_basin_maps.py
  python3 publication/analysis/scripts/render_example_basin_maps.py --layout combined
  python3 publication/analysis/scripts/render_example_basin_maps.py --out-dir publication/figures/drafts
  python3 publication/analysis/scripts/render_example_basin_maps.py --final --layout combined
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

try:
    import geopandas as gpd
    import matplotlib.pyplot as plt
    from matplotlib import patheffects as pe
except Exception as exc:  # ImportError or binary ABI issues (e.g. NumPy 2 vs old Matplotlib wheels)
    print(
        "ERROR: geopandas/matplotlib failed to import. Use a Python env where "
        "matplotlib, geopandas, and numpy are ABI-compatible (e.g. conda-forge "
        "or a venv with `pip install 'geopandas' 'matplotlib>=3.8'` on NumPy 2).",
        file=sys.stderr,
    )
    print(f"Detail: {exc}", file=sys.stderr)
    raise SystemExit(1) from exc

from _locked_basin_paths import (
    DEFAULT_CSV,
    DEFAULT_MODEL_DIR,
    DEFAULT_USER_PATH,
    DEFAULT_USERNAME,
    OPTIONAL_SHP_LAKES,
    REPO_ROOT,
    load_locked_inventory_rows,
    resolve_workspace_and_shapes_for_row,
)

STREAMS_SHP = "SWAT_plus_streams.shp"
SUBBASINS_SHP = "SWAT_plus_subbasins.shp"
DEFAULT_OUT_DIR = REPO_ROOT / "publication" / "figures" / "drafts"
DEFAULT_FINAL_OUT_DIR = REPO_ROOT / "publication" / "figures" / "final"
TIER_ORDER = {"Small": 0, "Medium": 1, "Large": 2}

# US state postal → full name for journal-style panel titles (final layout).
STATE_FULL_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

# Final-mode symbology (draft uses values inlined in _plot_on_ax).
FINAL_SUB_FACE = "#f6f7fa"
FINAL_SUB_EDGE = "#a8aab0"
FINAL_LAKE_FACE = "#b0d4ef"
FINAL_LAKE_EDGE = "#3d5d78"
FINAL_STREAM_COLOR = "#1c1d22"


def _fmt_cell(v: str | None) -> str:
    s = (v or "").strip()
    return s if s else "—"


def _fmt_float(v: str | None, nd: int = 1) -> str:
    s = (v or "").strip()
    if not s:
        return "—"
    return f"{float(s):.{nd}f}"


def _annotation_lines(row: dict[str, str]) -> list[str]:
    tier = _fmt_cell(row.get("tier"))
    mid = _fmt_cell(row.get("model_id"))
    st = _fmt_cell(row.get("state"))
    area = _fmt_float(row.get("area_km2"), 1)
    hrus = _fmt_cell(row.get("n_hrus"))
    ch = _fmt_cell(row.get("n_channels"))
    sub = _fmt_cell(row.get("n_subbasins"))
    lakes = _fmt_cell(row.get("n_lakes"))
    return [
        f"{tier}  |  {mid}",
        f"state={st}  area_km2={area}",
        f"HRUs={hrus}  channels={ch}  subbasins={sub}  lakes={lakes}",
    ]


def _state_full_name(row: dict[str, str]) -> str:
    abbr = (row.get("state") or "").strip().upper()
    return STATE_FULL_NAME.get(abbr, abbr or "—")


def _panel_title_journal(panel_letter: str, row: dict[str, str]) -> str:
    tier = _fmt_cell(row.get("tier"))
    place = _state_full_name(row)
    return f"({panel_letter}) {tier} — {place}"


def _final_stats_line(row: dict[str, str]) -> str:
    """Single concise line: area | HRUs | channels [| lakes if recorded]."""
    area_s = (row.get("area_km2") or "").strip()
    area = f"{float(area_s):.1f} km²" if area_s else "—"
    hrus = (row.get("n_hrus") or "").strip()
    ch = (row.get("n_channels") or "").strip()
    lakes_raw = (row.get("n_lakes") or "").strip()
    parts = [area, f"{hrus} HRUs" if hrus else "— HRUs", f"{ch} channels" if ch else "— channels"]
    if lakes_raw:
        parts.append(f"{lakes_raw} lakes")
    return " | ".join(parts)


def _stream_lw_alpha_final(row: dict[str, str]) -> tuple[float, float]:
    """Stream weight by channel density; readable on light subbasin fill."""
    raw = (row.get("n_channels") or "").strip()
    n = int(float(raw)) if raw else 0
    if n <= 80:
        lw, alp = 0.48, 0.92
    elif n <= 600:
        lw, alp = 0.38, 0.80
    else:
        lw, alp = 0.28, 0.70
    # Large (Kansas) tier: many channels default to thin/low-alpha; nudge for legibility.
    if (row.get("state") or "").strip().upper() == "KS":
        lw = min(lw * 1.2, 0.42)
        alp = min(alp + 0.12, 0.92)
    return lw, alp


def _meters_per_unit_xy(crs, x: float, y: float) -> tuple[float, float]:
    """Approximate meters per map unit in x (easting) and y (northing) at (x, y)."""
    if crs is None:
        return 1.0, 1.0
    from pyproj import CRS

    c = CRS.from_user_input(crs)
    if c.is_geographic:
        lat_rad = math.radians(y)
        m_lon = 111_320.0 * max(0.15, abs(math.cos(lat_rad)))
        m_lat = 111_320.0
        return m_lon, m_lat
    try:
        ai = c.axis_info[0]
        fac = getattr(ai, "unit_conversion_factor", None)
        if fac is not None and float(fac) > 0:
            f = float(fac)
            return f, f
    except Exception:
        pass
    return 1.0, 1.0


def _nice_scale_bar_km(span_m: float) -> float:
    """Round horizontal scale bar length (km) from map span in meters."""
    target_km = max(0.5, span_m * 0.12 / 1000.0)
    for s in (1, 2, 5, 10, 15, 20, 25, 50, 75, 100, 150, 200):
        if float(s) >= target_km * 0.85:
            return float(s)
    return 200.0


def _read_layers(shapes: Path, workspace: Path | None = None) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame | None]:
    streams_path = shapes / STREAMS_SHP
    sub_path = shapes / SUBBASINS_SHP
    lakes_path = shapes / OPTIONAL_SHP_LAKES
    if not sub_path.is_file() and workspace is not None:
        results = workspace / "Scenarios" / "Default" / "Results"
        sub_path = results / "subs.shp"
        streams_path = results / "rivs.shp"
        lakes_path = None
    if not streams_path.is_file():
        raise FileNotFoundError(f"Missing required shapefile: {streams_path}")
    if not sub_path.is_file():
        raise FileNotFoundError(f"Missing required shapefile: {sub_path}")
    subs = gpd.read_file(sub_path)
    lines = gpd.read_file(streams_path)
    lakes: gpd.GeoDataFrame | None = None
    if lakes_path and Path(lakes_path).is_file():
        lakes = gpd.read_file(lakes_path)
        if lakes is not None and lakes.empty:
            lakes = None
    return subs, lines, lakes


def _load_reprojected_layers(
    shapes: Path,
    workspace: Path | None = None,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame | None]:
    subs, lines, lakes = _read_layers(shapes, workspace=workspace)
    target_crs = subs.crs if subs.crs is not None else None
    if target_crs is not None:
        if lines.crs is not None and lines.crs != target_crs:
            lines = lines.to_crs(target_crs)
        if lakes is not None and lakes.crs is not None and lakes.crs != target_crs:
            lakes = lakes.to_crs(target_crs)
    return subs, lines, lakes


def _merged_bounds(
    subs: gpd.GeoDataFrame,
    lines: gpd.GeoDataFrame,
    lakes: gpd.GeoDataFrame | None,
) -> tuple[float, float, float, float]:
    chunks: list[gpd.GeoDataFrame] = [subs]
    if lakes is not None and not lakes.empty:
        chunks.append(lakes)
    if lines is not None and not lines.empty:
        chunks.append(lines)
    comb = gpd.GeoDataFrame(pd.concat(chunks, ignore_index=True), crs=subs.crs)
    return tuple(comb.total_bounds)


def _draw_layers(
    ax,
    subs: gpd.GeoDataFrame,
    lines: gpd.GeoDataFrame,
    lakes: gpd.GeoDataFrame | None,
    row: dict[str, str],
    *,
    final: bool,
) -> None:
    if final:
        subs.plot(
            ax=ax,
            facecolor=FINAL_SUB_FACE,
            edgecolor=FINAL_SUB_EDGE,
            linewidth=0.15,
            alpha=0.94,
        )
        if lakes is not None and not lakes.empty:
            lakes.plot(
                ax=ax,
                facecolor=FINAL_LAKE_FACE,
                edgecolor=FINAL_LAKE_EDGE,
                linewidth=0.14,
                alpha=0.88,
            )
        slw, salp = _stream_lw_alpha_final(row)
        lines.plot(ax=ax, color=FINAL_STREAM_COLOR, linewidth=slw, alpha=salp)
    else:
        subs.plot(ax=ax, facecolor="#e8e8e8", edgecolor="#555555", linewidth=0.35, alpha=0.9)
        if lakes is not None and not lakes.empty:
            lakes.plot(ax=ax, facecolor="#7eb8da", edgecolor="#2a5a7a", linewidth=0.25, alpha=0.85)
        lines.plot(ax=ax, color="#1a1a1a", linewidth=0.6, alpha=0.95)


def _add_panel_scale_bar(
    ax,
    crs,
    cx: float,
    cy: float,
    *,
    bar_km: float,
) -> None:
    """Horizontal scale bar in data units (same bar_km / crs logic on every panel)."""
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    mpx, _mpy = _meters_per_unit_xy(crs, cx, cy)
    bar_m = bar_km * 1000.0
    dx_data = bar_m / mpx
    xspan = xmax - xmin
    yspan = ymax - ymin
    x0 = xmin + 0.05 * xspan
    y0 = ymin + 0.06 * yspan
    ax.plot(
        [x0, x0 + dx_data],
        [y0, y0],
        color="0.12",
        linewidth=2.0,
        solid_capstyle="butt",
        path_effects=[pe.withStroke(linewidth=3.2, foreground="white")],
    )
    label = f"{int(bar_km)} km" if bar_km >= 1 else f"{bar_km:g} km"
    ax.text(
        x0 + 0.5 * dx_data,
        y0 + 0.03 * yspan,
        label,
        ha="center",
        va="bottom",
        fontsize=7.5,
        color="0.12",
        path_effects=[pe.withStroke(linewidth=2.5, foreground="white")],
    )


def _add_subtle_panel_frame(ax) -> None:
    """Very light rectangle in axes coordinates (axis is off)."""
    ax.add_patch(
        Rectangle(
            (0, 0),
            1,
            1,
            transform=ax.transAxes,
            fill=False,
            edgecolor="0.91",
            linewidth=0.35,
            zorder=100,
            clip_on=False,
        )
    )


def _plot_on_ax(
    ax,
    row: dict[str, str],
    shapes: Path,
    *,
    workspace: Path | None = None,
    final: bool,
    panel_letter: str | None,
    show_final_stats: bool = True,
) -> None:
    subs, lines, lakes = _load_reprojected_layers(shapes, workspace=workspace)
    _draw_layers(ax, subs, lines, lakes, row, final=final)

    ax.set_axis_off()
    ax.set_aspect("equal", adjustable="datalim")

    if final and panel_letter is not None:
        ax.set_title(
            _panel_title_journal(panel_letter, row),
            loc="left",
            fontsize=10,
            color="0.15",
            pad=5,
        )
        if show_final_stats:
            stats = _final_stats_line(row)
            ax.text(
                0.02,
                0.02,
                stats,
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment="bottom",
                color="0.12",
                path_effects=[pe.withStroke(linewidth=2.2, foreground="white")],
            )
    else:
        for i, ln in enumerate(_annotation_lines(row)):
            ax.text(
                0.02,
                0.98 - 0.055 * i,
                ln,
                transform=ax.transAxes,
                fontsize=8,
                verticalalignment="top",
                color="0.1",
                path_effects=[pe.withStroke(linewidth=2.5, foreground="white")],
            )


def _add_final_combined_legend(fig) -> None:
    """Shared legend under combined final figure (vector symbology)."""
    h_sub = Patch(
        facecolor=FINAL_SUB_FACE,
        edgecolor=FINAL_SUB_EDGE,
        linewidth=0.6,
        label="Subbasins",
    )
    slw, salp = _stream_lw_alpha_final({"n_channels": "400"})
    h_line = Line2D(
        [0],
        [0],
        color=FINAL_STREAM_COLOR,
        linewidth=max(1.2, slw * 4),
        alpha=salp,
        label="Stream channels",
    )
    h_lake = Patch(
        facecolor=FINAL_LAKE_FACE,
        edgecolor=FINAL_LAKE_EDGE,
        linewidth=0.5,
        label="Lakes (where present)",
    )
    fig.legend(
        handles=[h_sub, h_line, h_lake],
        loc="lower center",
        ncol=3,
        frameon=True,
        fancybox=False,
        fontsize=9,
        edgecolor="0.75",
        bbox_to_anchor=(0.5, 0.028),
        borderaxespad=0.2,
    )


def _add_final_single_legend(ax) -> None:
    """Compact legend on a single-panel final export."""
    h_sub = Patch(
        facecolor=FINAL_SUB_FACE,
        edgecolor=FINAL_SUB_EDGE,
        linewidth=0.5,
        label="Subbasins",
    )
    slw, salp = _stream_lw_alpha_final({"n_channels": "400"})
    h_line = Line2D(
        [0],
        [0],
        color=FINAL_STREAM_COLOR,
        linewidth=max(1.0, slw * 4),
        alpha=salp,
        label="Streams",
    )
    h_lake = Patch(
        facecolor=FINAL_LAKE_FACE,
        edgecolor=FINAL_LAKE_EDGE,
        linewidth=0.45,
        label="Lakes",
    )
    ax.legend(
        handles=[h_sub, h_line, h_lake],
        loc="lower right",
        fontsize=7,
        frameon=True,
        fancybox=False,
        edgecolor="0.75",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="tab-model-complexity.csv")
    p.add_argument(
        "--user-path",
        type=Path,
        default=Path(os.environ.get("USER_PATH", DEFAULT_USER_PATH)).expanduser(),
    )
    p.add_argument(
        "--username",
        default=(os.environ.get("EXAMPLE_MODELS_USERNAME") or DEFAULT_USERNAME).strip() or DEFAULT_USERNAME,
    )
    p.add_argument(
        "--model-dir",
        default=(os.environ.get("SWAT_SHOWCASE_MODEL_DIR") or DEFAULT_MODEL_DIR).strip() or DEFAULT_MODEL_DIR,
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Output directory (default: drafts/, or final/ when --final)",
    )
    p.add_argument(
        "--final",
        action="store_true",
        help="Manuscript-ready output: figures/final/, stem fig-example-basin-maps, no draft banner",
    )
    p.add_argument(
        "--layout",
        choices=("separate", "combined"),
        default="separate",
        help="separate: one file per basin; combined: single-row multi-panel",
    )
    p.add_argument(
        "--dpi",
        type=int,
        default=None,
        help="Raster dpi (default: 150 for drafts, 300 for --final unless overridden)",
    )
    p.add_argument("--format", dest="img_format", default="png", choices=("png", "pdf"), help="File format")
    args = p.parse_args(argv)
    if args.dpi is None:
        args.dpi = 300 if args.final else 150

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = DEFAULT_FINAL_OUT_DIR if args.final else DEFAULT_OUT_DIR
    out_dir = out_dir.resolve()
    stem = "fig-example-basin-maps" if args.final else "example-basin-map-draft"
    draft_banner = not args.final

    csv_path = args.csv.resolve()
    if not csv_path.is_file():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 1

    user_path = args.user_path.resolve()
    rows = load_locked_inventory_rows(csv_path)
    if not rows:
        print("ERROR: no locked_from_inventory rows in CSV", file=sys.stderr)
        return 1

    rows = sorted(
        rows,
        key=lambda r: TIER_ORDER.get((r.get("tier") or "").strip(), 99),
    )

    out_dir.mkdir(parents=True, exist_ok=True)

    meta_basins: list[dict[str, object]] = []
    final_combined_extent_meta: dict[str, object] = {}

    def row_meta(
        row: dict[str, str],
        rel_path: str,
        *,
        panel_letter: str | None = None,
    ) -> dict[str, object]:
        base: dict[str, object] = {
            "tier": (row.get("tier") or "").strip(),
            "model_id": (row.get("model_id") or "").strip(),
            "state": (row.get("state") or "").strip(),
            "area_km2": (row.get("area_km2") or "").strip(),
            "n_hrus": (row.get("n_hrus") or "").strip(),
            "n_channels": (row.get("n_channels") or "").strip(),
            "n_subbasins": (row.get("n_subbasins") or "").strip(),
            "n_lakes": (row.get("n_lakes") or "").strip(),
        }
        if args.final:
            base["output_image"] = rel_path
            base["stats_line"] = _final_stats_line(row)
            if panel_letter is not None:
                base["panel_title"] = _panel_title_journal(panel_letter, row)
        else:
            base["draft_image"] = rel_path
        return base

    if args.layout == "separate":
        for idx, row in enumerate(rows):
            tier = (row.get("tier") or "basin").strip().replace(" ", "_")
            try:
                _base, shapes, warn = resolve_workspace_and_shapes_for_row(
                    row, user_path, args.username, args.model_dir
                )
            except ValueError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                return 1
            if warn:
                print(f"WARN {warn}", file=sys.stderr)
            fname = f"{stem}-{tier}.{args.img_format}"
            fpath = out_dir / fname
            fig, ax = plt.subplots(1, 1, figsize=(5.5, 5.5))
            fig.patch.set_facecolor("white")
            letter = chr(ord("a") + idx) if args.final else None
            _plot_on_ax(ax, row, shapes, workspace=_base, final=args.final, panel_letter=letter)
            if args.final:
                _add_final_single_legend(ax)
            if draft_banner:
                fig.suptitle(
                    "Draft — example basin map (not final figure)",
                    fontsize=9,
                    color="0.35",
                    y=0.02,
                )
            fig.savefig(fpath, dpi=args.dpi, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            rel = str(fpath.relative_to(REPO_ROOT))
            meta_basins.append(row_meta(row, rel, panel_letter=letter))
    elif args.layout == "combined":
        n = len(rows)
        fig, axes = plt.subplots(1, n, figsize=(5.35 * n, 5.35))
        if n == 1:
            axes = [axes]
        fig.patch.set_facecolor("white")
        if args.final:
            for idx, (ax, row) in enumerate(zip(axes, rows, strict=True)):
                try:
                    _base, shapes, warn = resolve_workspace_and_shapes_for_row(
                        row, user_path, args.username, args.model_dir
                    )
                except ValueError as e:
                    print(f"ERROR: {e}", file=sys.stderr)
                    return 1
                if warn:
                    print(f"WARN {warn}", file=sys.stderr)
                subs, lines, lakes = _load_reprojected_layers(shapes, workspace=_base)
                _draw_layers(ax, subs, lines, lakes, row, final=True)
                bx0, by0, bx1, by1 = _merged_bounds(subs, lines, lakes)
                cx = 0.5 * (bx0 + bx1)
                cy = 0.5 * (by0 + by1)
                zpad = 1.05
                half_w = 0.5 * (bx1 - bx0) * zpad
                half_h = 0.5 * (by1 - by0) * zpad
                # Square data limits around merged-bounds center so equal-aspect panels
                # do not shift content off-center in the subplot box.
                half = max(half_w, half_h, 1e-9)
                ax.set_xlim(cx - half, cx + half)
                ax.set_ylim(cy - half, cy + half)
                ax.set_aspect("equal", adjustable="box")
                ax.set_axis_off()
                letter = chr(ord("a") + idx)
                ax.set_title(
                    _panel_title_journal(letter, row),
                    loc="left",
                    fontsize=10,
                    color="0.15",
                    pad=6,
                )
                _add_subtle_panel_frame(ax)
                mpx, mpy = _meters_per_unit_xy(subs.crs, cx, cy)
                span_d = min(2.0 * half * mpx, 2.0 * half * mpy)
                bar_d = _nice_scale_bar_km(span_d)
                _add_panel_scale_bar(ax, subs.crs, cx, cy, bar_km=bar_d)
            fig.subplots_adjust(bottom=0.125, top=0.9, wspace=0.1)
            _add_final_combined_legend(fig)
            final_combined_extent_meta = {
                "independent_zoom": True,
                "viewport_padding_ratio": 1.05,
                "viewport_square": True,
                "interpretation": (
                    "Each panel is independently zoomed to merged subbasin/stream/lake bounds with a "
                    "square viewport centered on that extent (equal aspect, centered in panel); "
                    "panels are not equal-scale across basins. Footprint area and discretization counts "
                    "for quantitative comparison are in Tab-ModelComplexity."
                ),
            }
        else:
            for idx, (ax, row) in enumerate(zip(axes, rows, strict=True)):
                try:
                    _base, shapes, warn = resolve_workspace_and_shapes_for_row(
                        row, user_path, args.username, args.model_dir
                    )
                except ValueError as e:
                    print(f"ERROR: {e}", file=sys.stderr)
                    return 1
                if warn:
                    print(f"WARN {warn}", file=sys.stderr)
                letter = chr(ord("a") + idx) if args.final else None
                _plot_on_ax(ax, row, shapes, final=args.final, panel_letter=letter, show_final_stats=True)
        if draft_banner:
            fig.suptitle(
                "Draft — example basin maps (not final figure)",
                fontsize=9,
                color="0.35",
                y=0.02,
            )
        fname = f"{stem}-combined-{n}panel.{args.img_format}"
        fpath = out_dir / fname
        pad = (
            0.14
            if args.final and args.layout == "combined"
            else (0.32 if args.final else 0.1)
        )
        fig.savefig(fpath, dpi=args.dpi, bbox_inches="tight", facecolor="white", pad_inches=pad)
        plt.close(fig)
        rel_all = str(fpath.relative_to(REPO_ROOT))
        for idx, row in enumerate(rows):
            letter = chr(ord("a") + idx) if args.final else None
            m = row_meta(row, rel_all, panel_letter=letter)
            m["combined_panel"] = True
            if args.final:
                m["independent_zoom"] = True
            meta_basins.append(m)

    sidecar = {
        "note": (
            "Manuscript Fig-ExampleBasinMaps (reproducible from render_example_basin_maps.py --final)."
            if args.final
            else "Draft outputs for editorial review; not final publication figures."
        ),
        "csv": str(csv_path),
        "layout": args.layout,
        "dpi": args.dpi,
        "final": bool(args.final),
        "basemaps": "none (local vector layers only)",
        "basins": meta_basins,
    }
    if args.final:
        man: dict[str, object] = {
            "model_ids_small_to_large": [(r.get("model_id") or "").strip() for r in rows],
            "panel_titles": [
                _panel_title_journal(chr(ord("a") + i), r) for i, r in enumerate(rows)
            ],
        }
        man.update(final_combined_extent_meta)
        sidecar["manuscript"] = man
    side_path = out_dir / f"{stem}-metadata.json"
    side_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote maps under: {out_dir}")
    print(f"Sidecar metadata: {side_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

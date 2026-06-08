#!/usr/bin/env python3
"""Render platform workflow and architecture diagrams for the manuscript.

Design language (shared across the three schematics):
  * One sans family, a clear size/weight hierarchy, dark-slate ink on white.
  * Each process phase is a *container* that visibly holds its steps, so the
    phase -> steps relationship reads at a glance (not a floating header bar).
  * The pipeline endpoint (the downloadable deliverable / export) is accented.
  * The architecture figure groups every box inside its functional layer, with
    flow arrows living in the gaps between boxes, and a sky -> blue -> indigo
    palette that reads top (user-facing) to bottom (deep backend).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

OUT = Path(__file__).resolve().parents[3] / "publication/figures/final"

# ---- shared ink / neutrals -------------------------------------------------
INK = "#0f172a"
MUTED = "#64748b"
FAINT = "#cbd5e1"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "text.color": INK,
        "figure.dpi": 100,
    }
)


def _round(ax, x, y, w, h, *, edge, face, lw=1.2, r=0.06, alpha=1.0, z=1):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0,rounding_size={r}",
            linewidth=lw, edgecolor=edge, facecolor=face, alpha=alpha, zorder=z,
        )
    )


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.06)
    plt.close(fig)
    print(f"Wrote {path}")


# ---------------------------------------------------------------------------
# Horizontal pipeline: three phase-containers, two steps each, accented endpoint
# ---------------------------------------------------------------------------
def _pipeline(
    steps, phases, *,
    box_edge, box_fill, text_color,
    cont_edge, cont_fills, label_color,
    deliver_edge, deliver_fill, arrow_color,
    title, note, outname,
):
    fig, ax = plt.subplots(figsize=(11.4, 3.5))
    ax.set_xlim(0, 11.4)
    ax.set_ylim(0, 3.55)
    ax.axis("off")

    cont_x = [0.20, 3.93, 7.66]
    cont_w = 3.53
    cont_y, cont_h = 0.52, 2.18
    box_w, box_h, y_box = 1.46, 1.30, 0.72

    # step x positions: two per container
    xs = []
    for cx in cont_x:
        xs.append(cx + 0.20)
        xs.append(cx + 1.87)

    # phase containers + headers (drawn first, behind the steps)
    for k, (cx, plabel) in enumerate(zip(cont_x, phases)):
        _round(ax, cx, cont_y, cont_w, cont_h, edge=cont_edge,
               face=cont_fills[k], lw=1.0, r=0.10, z=1)
        ax.text(cx + cont_w / 2, cont_y + cont_h - 0.24, plabel,
                ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=label_color, zorder=3)

    # step boxes
    for i, (x, label) in enumerate(zip(xs, steps)):
        last = i == len(steps) - 1
        _round(ax, x, y_box, box_w, box_h,
               edge=deliver_edge if last else box_edge,
               face=deliver_fill if last else box_fill,
               lw=1.5, r=0.08, z=4)
        ax.text(x + box_w / 2, y_box + box_h / 2, label,
                ha="center", va="center", fontsize=8.7,
                color="white" if last else text_color,
                fontweight="bold" if last else "normal",
                linespacing=1.3, zorder=5)
        if not last:
            ax.annotate(
                "", xy=(xs[i + 1] - 0.015, y_box + box_h / 2),
                xytext=(x + box_w + 0.015, y_box + box_h / 2),
                arrowprops=dict(arrowstyle="-|>", color=arrow_color,
                                lw=1.7, mutation_scale=15),
                zorder=6,
            )

    # Per Elsevier artwork rules, the title and descriptive note are NOT drawn
    # on the figure; they live in the LaTeX caption. (title/note kept as params
    # for provenance only.)
    _ = (title, note)
    _save(fig, outname)


def fig_workflow() -> None:
    _pipeline(
        steps=[
            "Basin extent\n& outlet selection",
            "NHDPlus HR\npreprocessing",
            "National ancillary\nlayers",
            "QSWAT+ project\nassembly",
            "QA sidecars\n+ manifest",
            "Downloadable\nSWAT+ model",
        ],
        phases=["Domain & hydrography", "Data & assembly", "Audit & handoff"],
        box_edge="#475569", box_fill="#f8fafc", text_color=INK,
        cont_edge="#cbd5e1", cont_fills=("#eef2f7", "#e8edf4", "#e2e8f0"),
        label_color="#334155",
        deliver_edge="#1e3a8a", deliver_fill="#1d4ed8", arrow_color="#475569",
        title="End-to-end SWAT+ model generation",
        note="Long-running generation runs on brokered workers; every step writes inspectable, auditable artifacts.",
        outname="fig-workflow.png",
    )


def fig_nhd_workflow() -> None:
    _pipeline(
        steps=[
            "NHDPlus HR\nvector ingest\n(VPU scope)",
            "UTM projection,\nlength & drop",
            "Remove\ndivergence-2",
            "Drop isolated\n& orphan reaches",
            "One-outlet\nsubbasin partition",
            "Lake linkage\n+ SWAT+ export",
        ],
        phases=["Metric preparation", "Network repair", "Subbasin & export"],
        box_edge="#0f766e", box_fill="#f0fdfa", text_color="#134e4a",
        cont_edge="#99f6e4", cont_fills=("#effdf9", "#e3fbf4", "#d3f7ec"),
        label_color="#0f766e",
        deliver_edge="#115e59", deliver_fill="#0f766e", arrow_color="#0f766e",
        title="NHDPlus HR hydrography preprocessing",
        note="VPU-wide preprocessing precedes the HUC12 (or gage) domain clip.",
        outname="fig-nhd-workflow.png",
    )


# ---------------------------------------------------------------------------
# Architecture: three functional layers, each containing its boxes; top-down flow
# ---------------------------------------------------------------------------
def fig_architecture_layers() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 6.5))
    ax.set_xlim(0, 7.8)
    ax.set_ylim(0, 6.6)
    ax.axis("off")

    groups = {
        "delivery": ("#0ea5e9", "#f0f9ff", "Delivery surface"),
        "async": ("#2563eb", "#eef4ff", "Orchestration"),
        "gen": ("#4338ca", "#eef2ff", "Generation & storage"),
    }

    boxes = [
        ("Browser client", "Watershed Explorer UI", "delivery"),
        ("Flask REST API + auth", "Jobs, sessions, signed artifact URLs", "delivery"),
        ("Celery broker + workers", "Non-blocking model-generation tasks", "async"),
        ("SWATGenX engine + ModelProcessing", "NHD rules, national layers, QSWAT+ assembly", "gen"),
        ("Generated project archive", "Per-basin tree, logs, QA JSON", "gen"),
    ]
    ys = [5.05, 4.05, 2.85, 1.65, 0.65]  # box bottoms, top-down
    box_h = 0.72
    x_box, box_w = 1.45, 6.00
    xc = x_box + box_w / 2

    # group containers (computed from the boxes each holds)
    pad = 0.16
    cont = {
        "delivery": (ys[1] - pad, ys[0] + box_h + pad),
        "async": (ys[2] - pad, ys[2] + box_h + pad),
        "gen": (ys[4] - pad, ys[3] + box_h + pad),
    }
    cont_x, cont_w = 1.15, 6.45
    for key, (y0, y1) in cont.items():
        accent, fill, label = groups[key]
        _round(ax, cont_x, y0, cont_w, y1 - y0, edge=accent, face=fill,
               lw=1.0, r=0.06, alpha=0.9, z=1)
        ax.text(0.58, (y0 + y1) / 2, label, ha="center", va="center",
                rotation=90, fontsize=8.8, fontweight="bold", color=accent, zorder=3)

    # boxes (white body + left accent stripe + title/subtitle)
    for (title, sub, key), yb in zip(boxes, ys):
        accent = groups[key][0]
        _round(ax, x_box, yb, box_w, box_h, edge=FAINT, face="white", lw=1.2, r=0.05, z=4)
        ax.add_patch(Rectangle((x_box + 0.015, yb + 0.05), 0.11, box_h - 0.10,
                               facecolor=accent, edgecolor="none", zorder=5))
        ax.text(x_box + 0.34, yb + box_h * 0.63, title, ha="left", va="center",
                fontsize=9.6, fontweight="bold", color=INK, zorder=6)
        ax.text(x_box + 0.34, yb + box_h * 0.26, sub, ha="left", va="center",
                fontsize=7.7, color=MUTED, zorder=6)

    # downward flow arrows, in the gaps between consecutive boxes
    for i in range(len(boxes) - 1):
        y_tail = ys[i] - 0.005
        y_head = ys[i + 1] + box_h + 0.02
        ax.annotate("", xy=(xc, y_head), xytext=(xc, y_tail),
                    arrowprops=dict(arrowstyle="-|>", color="#475569",
                                    lw=1.5, mutation_scale=13), zorder=7)

    # Title + note intentionally omitted from the figure (Elsevier rule); they
    # belong in the LaTeX caption.
    _save(fig, "fig-architecture-layers.png")


def main() -> None:
    fig_workflow()
    fig_architecture_layers()
    fig_nhd_workflow()


if __name__ == "__main__":
    main()

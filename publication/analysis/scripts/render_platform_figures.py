#!/usr/bin/env python3
"""Render platform workflow and architecture diagrams for the manuscript."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

OUT = Path(__file__).resolve().parents[3] / "publication/figures/final"

# Shared manuscript palette (slate workflow + teal hydrography + blue architecture).
_SLATE_EDGE = "#334155"
_SLATE_FILL = "#f8fafc"
_SLATE_PHASE = ("#f1f5f9", "#e2e8f0", "#cbd5e1")
_SLATE_TEXT = "#0f172a"
_TEAL_EDGE = "#0f766e"
_TEAL_FILL = "#f0fdfa"
_TEAL_PHASE = ("#ecfdf5", "#d1fae5", "#a7f3d0")
_TEAL_TEXT = "#134e4a"
_BLUE_EDGE = "#1e40af"
_BLUE_TIER = ("#eff6ff", "#dbeafe", "#bfdbfe")
_BLUE_LAYER = ("#f8fafc", "#e0f2fe", "#bae6fd", "#7dd3fc", "#38bdf8")
_BLUE_TEXT = "#0f172a"
_MUTED = "#64748b"


def _draw_phase_band(
    ax,
    label: str,
    x0: float,
    span: float,
    y: float,
    height: float,
    *,
    edge: str,
    face: str,
    text_color: str,
) -> None:
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (x0, y),
            span,
            height,
            boxstyle="round,pad=0.02",
            linewidth=0.9,
            edgecolor=edge,
            facecolor=face,
            alpha=0.8,
        )
    )
    ax.text(
        x0 + span / 2,
        y + height / 2,
        label,
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color=text_color,
    )


def _draw_pipeline(
    ax,
    stages: list[str],
    *,
    xs: list[float],
    box_w: float,
    box_h: float,
    y_box: float,
    edge: str,
    face: str,
    arrow_color: str | None = None,
    fontsize: float = 8.5,
) -> None:
    arrow_color = arrow_color or edge
    for i, (x, label) in enumerate(zip(xs, stages)):
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x, y_box),
                box_w,
                box_h,
                boxstyle="round,pad=0.06",
                linewidth=1.3,
                edgecolor=edge,
                facecolor=face,
            )
        )
        ax.text(
            x + box_w / 2,
            y_box + box_h / 2,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            color=_TEAL_TEXT if edge == _TEAL_EDGE else _SLATE_TEXT,
            linespacing=1.15,
        )
        if i < len(stages) - 1:
            ax.annotate(
                "",
                xy=(x + box_w + 0.2, y_box + box_h / 2),
                xytext=(x + box_w + 0.04, y_box + box_h / 2),
                arrowprops=dict(arrowstyle="-|>", color=arrow_color, lw=1.5, mutation_scale=13),
            )


def _save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {path}")


def fig_workflow() -> None:
    fig, ax = plt.subplots(figsize=(11.5, 4.4))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    box_w, box_h = 1.58, 1.2
    y_box = 1.45
    xs = [0.22 + i * 1.84 for i in range(6)]

    for label, x0, color in (
        ("Domain & hydrography", xs[0], _SLATE_PHASE[0]),
        ("Data & assembly", xs[2], _SLATE_PHASE[1]),
        ("Audit & handoff", xs[4], _SLATE_PHASE[2]),
    ):
        _draw_phase_band(
            ax, label, x0 - 0.08, box_w * 2 + 0.26, 3.05, 0.38,
            edge=_SLATE_EDGE, face=color, text_color=_SLATE_TEXT,
        )

    steps = [
        "Basin extent\n& outlet selection",
        "NHDPlus HR\npreprocessing",
        "National ancillary\nlayers",
        "QSWAT+ project\nassembly",
        "QA sidecars\n+ manifest",
        "Downloadable\nSWAT+ archive",
    ]
    _draw_pipeline(
        ax, steps, xs=xs, box_w=box_w, box_h=box_h, y_box=y_box,
        edge=_SLATE_EDGE, face=_SLATE_FILL, fontsize=8.3,
    )
    ax.text(
        5.75, 0.55,
        "Long-running generation runs on brokered workers; outputs remain on disk for SWAT+ Editor handoff.",
        ha="center", fontsize=8, color=_MUTED,
    )
    ax.set_title(
        "SWATGenX end-to-end model-generation workflow (Objective 1)",
        fontsize=10.5, color=_SLATE_TEXT, pad=12,
    )
    _save(fig, "fig-workflow.png")


def fig_architecture_layers() -> None:
    fig, ax = plt.subplots(figsize=(7.8, 5.6))
    ax.set_xlim(0, 7.8)
    ax.set_ylim(0, 5.6)
    ax.axis("off")

    tiers = [
        ("Delivery surface", 4.35, 1.35, _BLUE_TIER[0]),
        ("Async orchestration", 2.85, 0.72, _BLUE_TIER[1]),
        ("Generation & storage", 0.55, 1.95, _BLUE_TIER[2]),
    ]
    for label, y0, height, color in tiers:
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (0.35, y0), 7.1, height,
                boxstyle="round,pad=0.03",
                linewidth=0.8, edgecolor=_BLUE_EDGE, facecolor=color, alpha=0.45,
            )
        )
        ax.text(
            0.08, y0 + height / 2, label,
            ha="left", va="center", fontsize=7.5, fontweight="bold",
            color=_BLUE_EDGE, rotation=90,
        )

    layers = [
        ("Browser client", "Watershed Explorer UI", _BLUE_LAYER[0]),
        ("Flask REST API + auth", "Jobs, sessions, artifact URLs", _BLUE_LAYER[1]),
        ("Celery broker + workers", "Non-blocking model-generation tasks", _BLUE_LAYER[2]),
        ("SWATGenX engine + ModelProcessing", "NHD rules, national layers, QSWAT+ assembly", _BLUE_LAYER[3]),
        ("Generated project archive", "Per-basin tree, logs, QA JSON", _BLUE_LAYER[4]),
    ]
    box_w, box_h = 5.8, 0.58
    x_box = 1.35
    ys = [4.55, 3.65, 2.95, 1.75, 0.75]

    for i, ((title, subtitle, color), y) in enumerate(zip(layers, ys)):
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (x_box, y), box_w, box_h,
                boxstyle="round,pad=0.04",
                linewidth=1.2, edgecolor=_BLUE_EDGE, facecolor=color,
            )
        )
        ax.text(x_box + 0.18, y + box_h * 0.62, title, ha="left", va="center",
                fontsize=9, fontweight="bold", color=_BLUE_TEXT)
        ax.text(x_box + 0.18, y + box_h * 0.28, subtitle, ha="left", va="center",
                fontsize=7.5, color=_MUTED)
        if i < len(layers) - 1:
            ax.annotate(
                "", xy=(x_box + box_w / 2, y - 0.06),
                xytext=(x_box + box_w / 2, y),
                arrowprops=dict(arrowstyle="-|>", color=_BLUE_EDGE, lw=1.4, mutation_scale=12),
            )

    ax.text(
        3.95, 0.18,
        "Interactive requests enqueue work; workers write inspectable artifacts independent of the browser session.",
        ha="center", fontsize=7.8, color=_MUTED,
    )
    ax.set_title(
        "Workflow layers (delivery and reproducibility)",
        fontsize=10.5, color=_SLATE_TEXT, pad=10,
    )
    _save(fig, "fig-architecture-layers.png")


def fig_nhd_workflow() -> None:
    fig, ax = plt.subplots(figsize=(11.5, 4.4))
    ax.set_xlim(0, 11.5)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    box_w, box_h = 1.58, 1.2
    y_box = 1.45
    xs = [0.22 + i * 1.84 for i in range(6)]

    for label, x0, color in (
        ("Metric preparation", xs[0], _TEAL_PHASE[0]),
        ("Network repair", xs[2], _TEAL_PHASE[1]),
        ("Subbasin & export", xs[4], _TEAL_PHASE[2]),
    ):
        _draw_phase_band(
            ax, label, x0 - 0.08, box_w * 2 + 0.26, 3.05, 0.38,
            edge=_TEAL_EDGE, face=color, text_color=_TEAL_TEXT,
        )

    stages = [
        "NHDPlus HR\nvector ingest\n(VPU scope)",
        "UTM projection\nlength & drop",
        "Remove\ndivergence-2",
        "Drop isolated\n& orphan reaches",
        "One-outlet\nsubbasin partition",
        "Lake linkage\n+ SWAT+ export",
    ]
    _draw_pipeline(
        ax,
        stages,
        xs=xs,
        box_w=box_w,
        box_h=box_h,
        y_box=y_box,
        edge=_TEAL_EDGE,
        face=_TEAL_FILL,
        fontsize=8.3,
    )

    ax.text(
        5.75,
        0.55,
        "VPU-wide preprocessing runs before HUC12 (or gage) domain clip.",
        ha="center", fontsize=8, color=_MUTED,
    )
    ax.set_title("NHDPlus HR preprocessing pipeline (Objective 2)", fontsize=10.5, color=_SLATE_TEXT, pad=12)
    _save(fig, "fig-nhd-workflow.png")


def main() -> None:
    fig_workflow()
    fig_architecture_layers()
    fig_nhd_workflow()


if __name__ == "__main__":
    main()

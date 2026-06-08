#!/usr/bin/env python3
"""Render publication figures for Objective 5 runtime benchmark."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = REPO_ROOT / "web_application/frontend/src/data/swatPlusRuntimeBenchmarkCatalog.json"
OUT = REPO_ROOT / "publication/figures/final"


def _read_csv(name: str) -> list[dict]:
    path = REPO_ROOT / "publication/tables" / name
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fig_hru_scaling() -> None:
    rows = _read_csv("tab-runtime-benchmark-hru-scaling.csv")
    hrus = [int(r["hrus"]) for r in rows]
    wall = [float(r["wall_s"]) for r in rows]
    labels = [r["tier"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.scatter(hrus, wall, c="#2563eb", s=60, zorder=3)
    for h, w, t in zip(hrus, wall, labels):
        ax.annotate(t, (h, w), textcoords="offset points", xytext=(4, 4), fontsize=8)
    # Least-squares linear fit computed from the frozen CSV points (the catalog
    # no longer carries the fit constants).
    n = len(hrus)
    mean_x = sum(hrus) / n
    mean_y = sum(wall) / n
    sxx = sum((x - mean_x) ** 2 for x in hrus)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(hrus, wall))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    ss_tot = sum((y - mean_y) ** 2 for y in wall)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(hrus, wall))
    r_squared = 1 - ss_res / ss_tot
    xs = [min(hrus), max(hrus)]
    ys = [slope * x + intercept for x in xs]
    ax.plot(xs, ys, "--", color="#64748b", linewidth=1, label=f"Linear fit ($R^2$={r_squared:.2f})")
    ax.set_xlabel("HRU count")
    ax.set_ylabel("Wall time (s), 365-day filtered run")
    # Title omitted from figure per Elsevier artwork rule (lives in caption).
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    path = OUT / "fig-runtime-benchmark-hru-scaling.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


def fig_print_scope() -> None:
    rows = _read_csv("tab-runtime-benchmark-print-scope.csv")
    tiers = ["S", "M"]  # L full export omitted (disk/time); catalog reports filtered only
    full = []
    filt = []
    for t in tiers:
        full.append(float(next(r["wall_s"] for r in rows if r["tier"] == t and r["print_scope"] == "full_export")))
        filt.append(float(next(r["wall_s"] for r in rows if r["tier"] == t and r["print_scope"] == "calibration_filtered")))
    x = range(len(tiers))
    w = 0.35
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.bar([i - w / 2 for i in x], full, width=w, label="Full export", color="#94a3b8")
    ax.bar([i + w / 2 for i in x], filt, width=w, label="Calibration filtered", color="#2563eb")
    ax.set_xticks(list(x))
    ax.set_xticklabels(tiers)
    ax.set_xlabel("Tier")
    ax.set_ylabel("Wall time (s)")
    # Title omitted from figure per Elsevier artwork rule (lives in caption).
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    path = OUT / "fig-runtime-benchmark-print-scope.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_hru_scaling()
    fig_print_scope()


if __name__ == "__main__":
    main()

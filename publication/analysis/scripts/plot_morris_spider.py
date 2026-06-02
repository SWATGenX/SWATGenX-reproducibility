#!/usr/bin/env python3
"""Publication Morris spider (radar) charts from tab-sensitivity-morris.csv."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = REPO_ROOT / "publication/tables/tab-sensitivity-morris.csv"

# Top-N parameters per controlled basin (compact spider webs).
MORRIS_SPIDER_TOP_N: dict[str, int] = {
    "02297600": 8,
    "05536265": 6,
}


def _rows_for_site(csv_path: Path, site_no: str) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = [
            r for r in csv.DictReader(f)
            if r.get("site_no") == site_no and r.get("status", "").startswith("frozen")
        ]
    rows.sort(key=lambda r: -float(r["mu_star"]))
    return rows


def _polar_spider(
    ax: plt.Axes,
    labels: list[str],
    mu_star: np.ndarray,
    *,
    title: str,
) -> None:
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    angles_closed = np.concatenate([angles, angles[:1]])
    values = np.asarray(mu_star, dtype=float)
    values_closed = np.concatenate([values, values[:1]])

    ax.plot(angles_closed, values_closed, color="#2563eb", linewidth=1.8, marker="o", markersize=4)
    ax.fill(angles_closed, values_closed, color="#2563eb", alpha=0.18)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    label_fs = 7 if n >= 8 else 8
    ax.set_thetagrids(np.degrees(angles), labels, fontsize=label_fs)
    rmax = float(values.max()) * 1.12 if values.size else 1.0
    ax.set_ylim(0, max(rmax, 0.05))
    ax.set_rlabel_position(0)
    ax.tick_params(axis="y", labelsize=6)
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.55)
    ax.set_title(title, fontsize=9, pad=8)


def plot_morris_spider_panel(
    csv_path: Path,
    site_no: str,
    top_n: int,
    output_path: Path,
    *,
    title: str | None = None,
) -> None:
    rows = _rows_for_site(csv_path, site_no)[:top_n]
    if not rows:
        raise SystemExit(f"No Morris rows for site {site_no}")
    labels = [r["parameter"] for r in rows]
    mu_star = np.array([float(r["mu_star"]) for r in rows], dtype=float)
    label = title or f"USGS {site_no} (top {top_n} mu*)"
    fig, ax = plt.subplots(figsize=(4.2, 4.2), subplot_kw={"polar": True})
    _polar_spider(ax, labels, mu_star, title=label)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_morris_spider_dual(
    csv_path: Path,
    output_path: Path,
    top_n_by_site: dict[str, int] | None = None,
) -> None:
    top_n_by_site = top_n_by_site or MORRIS_SPIDER_TOP_N
    sites = list(top_n_by_site.items())
    n = len(sites)
    # Side-by-side polar panels fit one supplement page at \\linewidth; vertical stack overflows.
    fig_w = 4.25 * n + 0.4
    fig, axes = plt.subplots(
        1,
        n,
        figsize=(fig_w, 4.35),
        subplot_kw={"polar": True},
        squeeze=False,
    )
    panel_labels = ("(a)", "(b)")
    for col, (site_no, top_n) in enumerate(sites):
        rows = _rows_for_site(csv_path, site_no)[:top_n]
        labels = [r["parameter"] for r in rows]
        mu_star = np.array([float(r["mu_star"]) for r in rows], dtype=float)
        state = "FL" if site_no.startswith("02") else "IL"
        title = f"{panel_labels[col]} {site_no} ({state}, top {top_n} mu*)"
        _polar_spider(axes[0, col], labels, mu_star, title=title)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.06, wspace=0.42)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    p.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "publication/figures/final/fig-morris-spider-controlled-basins.png",
    )
    p.add_argument("--site-no", type=str, default="", help="Single-basin export")
    p.add_argument("--top-n", type=int, default=8)
    args = p.parse_args()
    if args.site_no:
        plot_morris_spider_panel(args.csv, args.site_no, args.top_n, args.out)
    else:
        plot_morris_spider_dual(args.csv, args.out)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

"""Stack publication figure PNGs vertically at full textwidth."""
from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

PANEL_WIDTH_IN = 7.2
DPI = 300
PANEL_GAP_IN = 0.12


def stack_image_panels(
    panels: list[tuple[str, Path]],
    out_png: Path,
    *,
    panel_width_in: float = PANEL_WIDTH_IN,
    dpi: int = DPI,
    panel_gap_in: float = PANEL_GAP_IN,
) -> None:
    """Stack PNG artifacts top-to-bottom; each panel spans *panel_width_in* at *dpi*."""
    if not panels:
        raise ValueError("panels must be non-empty")
    images = []
    for caption, path in panels:
        if not path.is_file():
            raise FileNotFoundError(path)
        images.append((caption, mpimg.imread(str(path))))

    height_ratios = [img.shape[0] / img.shape[1] for _, img in images]
    fig_h = panel_width_in * sum(height_ratios) + panel_gap_in * (len(images) - 1)
    fig = plt.figure(figsize=(panel_width_in, fig_h), dpi=dpi, facecolor="white")
    gs = GridSpec(
        len(images),
        1,
        figure=fig,
        height_ratios=height_ratios,
        hspace=panel_gap_in / (panel_width_in * max(height_ratios)),
    )
    for ax_idx, (caption, img) in enumerate(images):
        ax = fig.add_subplot(gs[ax_idx])
        ax.imshow(img, aspect="equal", interpolation="lanczos")
        ax.set_axis_off()
        if caption:
            ax.text(
                0.012,
                0.98,
                caption,
                transform=ax.transAxes,
                fontsize=10.5,
                fontweight="bold",
                va="top",
                ha="left",
                color="black",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="0.75", alpha=0.92),
            )
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=dpi, bbox_inches="tight", pad_inches=0.04, facecolor="white")
    plt.close(fig)

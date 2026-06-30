#!/usr/bin/env python3
"""
Assemble 3-panel daily hydrograph figure for calibration proof basin 01567500.

Copies init / calibration-best / verification ensemble PNGs from the admin model tree
into publication/figures/final/fig-cal-proof-01567500-hydrographs-3panel.png.

Usage (from repo root):
  python3 publication/analysis/scripts/assemble_cal_proof_hydrographs.py
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[3]
USER_ROOT = Path("${SWATGENX_USER_PATH}")
FIG_ROOT = (
    USER_ROOT
    / "admin/SWATplus_by_VPUID/0205/usgs_station/01567500/calibration_artifacts/Default_initialized"
    / "figures_SWAT_MODEL_Web_Application/SF"
)
SOURCES = {
    "initialization_pool_best": FIG_ROOT / "calibration/init/daily/7_daily.png",
    "calibration_global_best": FIG_ROOT / "calibration/iter_0024/daily/7_daily.png",
    "verification_global_best": FIG_ROOT / "verification/VerificationEnsemble_daily.png",
}
PANEL_LABELS = ("(a) Init. pool best", "(b) Calibration best", "(c) Verification best")
OUT_PNG = REPO_ROOT / "publication/figures/final/fig-cal-proof-01567500-hydrographs-3panel.png"
OUT_META = REPO_ROOT / "publication/figures/final/fig-cal-proof-01567500-hydrographs-metadata.json"
TARGET_HEIGHT = 900
TARGET_WIDTH_EACH = 1200


def _load_rgb(path: Path) -> Image.Image:
    if not path.is_file():
        raise SystemExit(f"ERROR: missing source figure: {path}")
    return Image.open(path).convert("RGB")


def _resize_to_height(img: Image.Image, height: int) -> Image.Image:
    w, h = img.size
    new_w = max(1, int(w * height / h))
    return img.resize((new_w, height), Image.Resampling.LANCZOS)


def _crop_center_width(img: Image.Image, width: int) -> Image.Image:
    w, h = img.size
    if w <= width:
        pad = Image.new("RGB", (width, h), "white")
        pad.paste(img, ((width - w) // 2, 0))
        return pad
    left = (w - width) // 2
    return img.crop((left, 0, left + width, h))


def _label_panel(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, img.width, 28), fill="white")
    draw.text((8, 6), text, fill="black", font=font)
    return img


def assemble() -> None:
    panels = []
    for key, path in SOURCES.items():
        im = _resize_to_height(_load_rgb(path), TARGET_HEIGHT)
        im = _crop_center_width(im, TARGET_WIDTH_EACH)
        panels.append((key, path, im))

    total_w = TARGET_WIDTH_EACH * len(panels)
    canvas = Image.new("RGB", (total_w, TARGET_HEIGHT), "white")
    x = 0
    for (_, _, im), label in zip(panels, PANEL_LABELS):
        labeled = _label_panel(im.copy(), label)
        canvas.paste(labeled, (x, 0))
        x += TARGET_WIDTH_EACH

    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_PNG, format="PNG", optimize=True)

    meta = {
        "figure_id": "Fig-CalProofHydrograph",
        "model_id": "0205/usgs_station/01567500",
        "site_no": "01567500",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_png": str(OUT_PNG.relative_to(REPO_ROOT)),
        "panels": [
            {"stage": k, "source": str(p)} for k, p, _ in panels
        ],
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_META}")


if __name__ == "__main__":
    assemble()

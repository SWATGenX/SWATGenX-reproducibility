#!/usr/bin/env python3
"""Rebuild the cal/val 3-panel hydrograph figures (Suppl. S3, S4) with NO
on-figure titles. The per-stage daily hydrographs are only available as rendered
PNGs (no underlying time-series files survive), so each source panel's title band
is removed by detecting the top axes spine and cropping above it; the three stage
panels are then stacked with a panel letter only. Stat boxes (NSE/PBIAS) and
legends inside the axes are preserved. Stage labels live in the LaTeX caption.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

USERS = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID")
FINAL = Path(__file__).resolve().parents[3] / "publication/figures/final"

BASINS = [
    {"site": "02297600", "vpuid": "0310", "ch": "2", "cal_iter": "iter_0026"},
    {"site": "05536265", "vpuid": "0712", "ch": "25", "cal_iter": "iter_0026"},
]
SCEN = "Default_calval_split202606"


def _sf(b):
    return (USERS / b["vpuid"] / "usgs_station" / b["site"]
            / f"calibration_artifacts/{SCEN}/figures_SWAT_MODEL_Web_Application/SF")


def _daily(d: Path, ch: str) -> Path:
    exact = d / f"{ch}_daily.png"
    if exact.is_file():
        return exact
    hits = sorted(d.glob(f"{ch}*_daily.png"))
    if hits:
        return hits[-1]
    raise FileNotFoundError(d / f"{ch}*_daily.png")


def _sources(b):
    sf = _sf(b)
    return [
        _daily(sf / "calibration/init/daily", b["ch"]),
        _daily(sf / f"calibration/{b['cal_iter']}/daily", b["ch"]),
        sf / "verification/VerificationEnsemble_daily.png",
    ]


def _crop_title(im: Image.Image) -> Image.Image:
    """Remove the top title band by finding the first long horizontal dark line
    (the top axes spine) within the upper 30% of the image and cropping a small
    margin above it."""
    g = np.asarray(im.convert("L"))
    h, w = g.shape
    dark_frac = (g < 110).sum(axis=1) / w
    top = int(h * 0.30)
    spine = None
    for r in range(top):
        if dark_frac[r] > 0.45:          # continuous spine spans most of the width
            spine = r
            break
    if spine is None:
        return im                         # no clear spine; leave untouched
    cut = max(spine - int(0.012 * h), 0)  # keep a little headroom above the spine
    return im.crop((0, cut, w, h))


def _label(im: Image.Image, text: str) -> Image.Image:
    band = int(im.height * 0.055)
    out = Image.new("RGB", (im.width, im.height + band), "white")
    out.paste(im, (0, band))
    d = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(band * 0.62))
    except Exception:
        font = ImageFont.load_default()
    d.text((int(im.width * 0.01), int(band * 0.18)), text, fill="black", font=font)
    return out


def render(b) -> None:
    panels = []
    for letter, src in zip("abc", _sources(b)):
        if not src.is_file():
            raise FileNotFoundError(src)
        panels.append(_label(_crop_title(Image.open(src).convert("RGB")), f"({letter})"))
    w = min(p.width for p in panels)
    panels = [p.resize((w, int(p.height * w / p.width))) for p in panels]
    total_h = sum(p.height for p in panels)
    canvas = Image.new("RGB", (w, total_h), "white")
    y = 0
    for p in panels:
        canvas.paste(p, (0, y)); y += p.height
    out = FINAL / f"fig-cal-val-{b['site']}-hydrographs-3panel.png"
    canvas.save(out, dpi=(200, 200))
    print(f"Wrote {out} ({canvas.size})")


def main() -> None:
    for b in BASINS:
        render(b)


if __name__ == "__main__":
    main()

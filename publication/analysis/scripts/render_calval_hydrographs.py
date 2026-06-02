#!/usr/bin/env python3
"""Publication-quality 3-panel cal/val daily hydrographs from calibration artifacts.

Stacks initialization, calibration-best, and verification panels **vertically** at
native artifact resolution (300 dpi source PNGs from ModelProcessing) so supplementary
PDFs remain legible at \\textwidth.  Horizontal 3-up composites shrink each panel to
~2 in wide and are unsuitable for print.

Usage (repo root):
  python publication/analysis/scripts/render_calval_hydrographs.py
  python publication/analysis/scripts/render_calval_hydrographs.py --site-no 02297600
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from export_objectives_4_5 import BASINS, BasinExport, _hydro_sources  # noqa: E402
from publication_panel_stack import DPI, PANEL_WIDTH_IN, stack_image_panels  # noqa: E402

STAGE_LABELS = {
    "initialization_pool_best": "Initialization pool best",
    "calibration_global_best": "Calibration global best",
    "verification_global_best": "Verification global best",
}


def _panel_caption(stage: str, b: BasinExport) -> str:
    letter = {"initialization_pool_best": "a", "calibration_global_best": "b", "verification_global_best": "c"}[stage]
    title = STAGE_LABELS[stage]
    if stage == "verification_global_best":
        period = b.ver_period.replace(" to ", "–")
    else:
        period = b.cal_period.replace(" to ", "–")
    return f"({letter}) {title} ({period})"


def render_basin(b: BasinExport) -> None:
    sources = _hydro_sources(b)
    stack_panels: list[tuple[str, Path]] = []
    panel_records: list[tuple[str, str, Path]] = []
    for stage, path in sources.items():
        if not path.is_file():
            raise SystemExit(f"Missing hydrograph source for {b.site_no}: {path}")
        caption = _panel_caption(stage, b)
        stack_panels.append((caption, path))
        panel_records.append((stage, caption, path))

    stack_image_panels(stack_panels, b.out_hydro)

    meta = {
        "figure_id": f"Fig-CalValHydrograph-{b.site_no}",
        "model_id": b.model_id,
        "site_no": b.site_no,
        "layout": "vertical_3panel",
        "panel_width_in": PANEL_WIDTH_IN,
        "dpi": DPI,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "panels": [
            {"stage": stage, "caption": cap, "source": str(path)}
            for stage, cap, path in panel_records
        ],
    }
    b.out_hydro_meta.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {b.out_hydro} ({b.out_hydro.stat().st_size // 1024} KiB)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-no", action="append", help="Limit to one or more USGS site numbers")
    args = parser.parse_args()
    selected = {s.strip() for s in args.site_no} if args.site_no else None
    for basin in BASINS:
        if selected and basin.site_no not in selected:
            continue
        render_basin(basin)


if __name__ == "__main__":
    main()

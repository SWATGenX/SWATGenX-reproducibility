#!/usr/bin/env python3
"""Publication-quality Morris ensemble hydrographs (daily + monthly).

Stacks controlled-basin panels vertically from Default_initialized artifact PNGs.
Horizontal side-by-side composites are illegible at \\textwidth in the PDF.

Usage (repo root):
  python publication/analysis/scripts/render_sensitivity_ensemble_figures.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from export_objectives_4_5 import (  # noqa: E402
    BASINS,
    SENS_ENSEMBLE_COMBINED_DAILY,
    SENS_ENSEMBLE_COMBINED_DAILY_META,
    SENS_ENSEMBLE_COMBINED_MONTHLY,
    _ensemble_figure_src,
)
from publication_panel_stack import stack_image_panels  # noqa: E402

REPO_ROOT = SCRIPT_DIR.parents[2]


def _panel_caption(letter: str, site_no: str, state: str, cal_period: str, frequency: str) -> str:
    # Panel letter only; the descriptive title (gage, state, window) lives in the
    # LaTeX caption per Elsevier artwork rule.
    _ = (site_no, state, cal_period, frequency)
    return f"({letter})"


def render_all(*, copy_per_basin: bool = True) -> None:
    daily_panels: list[tuple[str, Path]] = []
    monthly_panels: list[tuple[str, Path]] = []
    panel_meta: list[dict] = []

    for idx, b in enumerate(BASINS):
        letter = chr(97 + idx)
        daily_src = _ensemble_figure_src(b, "daily")
        monthly_src = _ensemble_figure_src(b, "monthly")
        daily_panels.append(
            (_panel_caption(letter, b.site_no, b.state, b.cal_period, "Daily"), daily_src)
        )
        monthly_panels.append(
            (_panel_caption(letter, b.site_no, b.state, b.cal_period, "Monthly"), monthly_src)
        )
        panel_meta.append(
            {
                "site_no": b.site_no,
                "daily_source": str(daily_src),
                "monthly_source": str(monthly_src),
            }
        )
        if copy_per_basin:
            out_daily = REPO_ROOT / f"publication/figures/final/fig-sensitivity-ensemble-{b.site_no}-daily.png"
            out_monthly = (
                REPO_ROOT / f"publication/figures/supplement/fig-sensitivity-ensemble-{b.site_no}-monthly.png"
            )
            shutil.copy2(daily_src, out_daily)
            shutil.copy2(monthly_src, out_monthly)
            print(f"Wrote {out_daily}")
            print(f"Wrote {out_monthly}")

    stack_image_panels(daily_panels, SENS_ENSEMBLE_COMBINED_DAILY)
    stack_image_panels(monthly_panels, SENS_ENSEMBLE_COMBINED_MONTHLY)
    print(f"Wrote {SENS_ENSEMBLE_COMBINED_DAILY} ({SENS_ENSEMBLE_COMBINED_DAILY.stat().st_size // 1024} KiB)")
    print(f"Wrote {SENS_ENSEMBLE_COMBINED_MONTHLY} ({SENS_ENSEMBLE_COMBINED_MONTHLY.stat().st_size // 1024} KiB)")

    meta = {
        "figure_id": "Fig-SensitivityEnsemble-ControlledBasins-Daily",
        "chart_type": "morris_ensemble_hydrograph",
        "layout": "vertical_2panel",
        "n_morris_samples": 999,
        "panels": panel_meta,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    SENS_ENSEMBLE_COMBINED_DAILY_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-per-basin-copy",
        action="store_true",
        help="Only rebuild combined daily/monthly stacks",
    )
    args = parser.parse_args()
    render_all(copy_per_basin=not args.no_per_basin_copy)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply Morris μ* threshold to bin cal_parms before calibration (publication runs)."""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MP_ROOT = os.path.join(REPO_ROOT, "ModelProcessing")
if MP_ROOT not in sys.path:
    sys.path.insert(0, MP_ROOT)

from ModelProcessing.morris_cal_parms import (  # noqa: E402
    MU_STAR_NEGLIGIBLE,
    apply_morris_cal_parm_reduction,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--site-root", required=True, help="HUC12 model directory")
    p.add_argument("--scenario", default="Default_initialized")
    p.add_argument(
        "--bin-cal",
        default=os.path.join(REPO_ROOT, "bin/cal_parms_SWAT_MODEL_Web_Application.cal"),
    )
    p.add_argument(
        "--min-mu-star",
        type=float,
        default=MU_STAR_NEGLIGIBLE,
        help=f"Keep parameters with mu* >= this (dashboard QC default {MU_STAR_NEGLIGIBLE})",
    )
    p.add_argument("--manifest", default="", help="Optional JSON audit path")
    p.add_argument("--print-count", action="store_true", help="Print active parameter count only")
    args = p.parse_args()

    summary = apply_morris_cal_parm_reduction(
        args.site_root,
        args.bin_cal,
        scenario=args.scenario,
        min_mu_star=args.min_mu_star,
        manifest_path=args.manifest or None,
    )

    if args.print_count:
        print(summary["n_after"])
    else:
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

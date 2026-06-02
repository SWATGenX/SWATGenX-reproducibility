#!/usr/bin/env python3
"""
Read locked evaluation basins from publication/tables/tab-model-complexity.csv
and print resolved admin showcase workspace paths plus expected Watershed/Shapes
vector paths. Read-only; does not modify files or generate figures.

Exit code 0 if every required path exists; 1 if any required path is missing.
SWAT_plus_lakes.shp is optional (reported but not required for success).

Environment:
  USER_PATH              Root containing per-user trees (default: ${SWATGENX_USER_PATH})
  EXAMPLE_MODELS_USERNAME  Showcase username (default: admin)
  SWAT_SHOWCASE_MODEL_DIR  Model folder under site_no (default: SWAT_MODEL_Web_Application)

Usage (from repo root):
  python3 publication/analysis/scripts/print_locked_basin_paths.py
  USER_PATH=/path/to/Users python3 publication/analysis/scripts/print_locked_basin_paths.py
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _locked_basin_paths import (
    DEFAULT_CSV,
    DEFAULT_MODEL_DIR,
    DEFAULT_USER_PATH,
    DEFAULT_USERNAME,
    OPTIONAL_SHP_LAKES,
    REQUIRED_SHP_FOR_PATH_CHECK,
    load_locked_inventory_rows,
    resolve_workspace_and_shapes_for_row,
)

REQUIRED_SHP = REQUIRED_SHP_FOR_PATH_CHECK
OPTIONAL_SHP = OPTIONAL_SHP_LAKES


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help=f"Path to tab-model-complexity.csv (default: {DEFAULT_CSV})",
    )
    p.add_argument(
        "--user-path",
        type=Path,
        default=Path(os.environ.get("USER_PATH", DEFAULT_USER_PATH)).expanduser(),
        help=f"USER_PATH root (default env or {DEFAULT_USER_PATH})",
    )
    p.add_argument(
        "--username",
        default=(os.environ.get("EXAMPLE_MODELS_USERNAME") or DEFAULT_USERNAME).strip() or DEFAULT_USERNAME,
        help=f"Showcase username (default env or {DEFAULT_USERNAME})",
    )
    p.add_argument(
        "--model-dir",
        default=(os.environ.get("SWAT_SHOWCASE_MODEL_DIR") or DEFAULT_MODEL_DIR).strip() or DEFAULT_MODEL_DIR,
        help=f"Workspace folder name under site_no (default env or {DEFAULT_MODEL_DIR})",
    )
    args = p.parse_args(argv)

    csv_path = args.csv.resolve()
    if not csv_path.is_file():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        return 1

    user_path = args.user_path.resolve()
    username = args.username
    model_dir = args.model_dir

    rows = load_locked_inventory_rows(csv_path)
    if not rows:
        print(
            "ERROR: No rows with status=locked_from_inventory in " f"{csv_path}",
            file=sys.stderr,
        )
        return 1

    print(f"CSV: {csv_path}")
    print(f"USER_PATH: {user_path}  (exists: {user_path.is_dir()})")
    print(f"Username: {username}")
    print(f"Model dir: {model_dir}")
    print()

    any_missing = False

    for row in rows:
        tier = (row.get("tier") or "").strip()
        model_id = (row.get("model_id") or "").strip()
        try:
            base, shapes, warn = resolve_workspace_and_shapes_for_row(row, user_path, username, model_dir)
        except ValueError as e:
            print(f"ERROR [{model_id}]: {e}", file=sys.stderr)
            any_missing = True
            continue
        if warn:
            print(f"WARN {warn}", file=sys.stderr)

        print(f"=== {tier or '?'} — {model_id} ===")
        print(f"  workspace_base: {base}")
        print(f"  workspace_exists: {base.is_dir()}")
        if not base.is_dir():
            any_missing = True

        print(f"  Watershed/Shapes: {shapes}")
        print(f"  shapes_dir_exists: {shapes.is_dir()}")
        if not shapes.is_dir():
            any_missing = True

        for name in REQUIRED_SHP:
            shp = shapes / name
            ok = shp.is_file()
            print(f"  {name}: {shp}  exists={ok}")
            if not ok:
                any_missing = True

        lakes = shapes / OPTIONAL_SHP
        lakes_ok = lakes.is_file()
        print(f"  {OPTIONAL_SHP} (optional): {lakes}  exists={lakes_ok}")
        print()

    if any_missing:
        print("RESULT: one or more required paths are missing (exit 1).", file=sys.stderr)
        return 1

    print("RESULT: all required workspace and shapefile paths exist (exit 0).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

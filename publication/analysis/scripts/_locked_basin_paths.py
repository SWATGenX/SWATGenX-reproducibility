"""
Shared path resolution for locked evaluation basins (tab-model-complexity.csv).

Used by print_locked_basin_paths.py and render_example_basin_maps.py.
Read-only helpers; no I/O beyond CSV reads in loaders.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CSV = REPO_ROOT / "publication" / "tables" / "tab-model-complexity.csv"
DEFAULT_USER_PATH = os.environ.get("SWATGENX_USER_PATH", "${SWATGENX_USER_PATH}")
DEFAULT_USERNAME = os.environ.get("SWATGENX_EXAMPLE_USER", "admin")
DEFAULT_MODEL_DIR = "SWAT_MODEL_Web_Application"

REQUIRED_SHP_FOR_PATH_CHECK = (
    "SWAT_plus_streams.shp",
    "SWAT_plus_watersheds.shp",
    "SWAT_plus_subbasins.shp",
)
OPTIONAL_SHP_LAKES = "SWAT_plus_lakes.shp"


def parse_model_id(model_id: str) -> tuple[str, str, str]:
    parts = str(model_id).strip().split("/")
    if len(parts) != 3:
        raise ValueError(f"model_id must be vpuid/level/site_no, got: {model_id!r}")
    vpuid, level, site_no = parts[0], parts[1], parts[2]
    if not vpuid or not level or not site_no:
        raise ValueError(f"Invalid model_id: {model_id!r}")
    return vpuid, level, site_no


def workspace_base(
    user_path: Path,
    username: str,
    vpuid: str,
    level: str,
    site_no: str,
    model_dir: str,
) -> Path:
    return user_path / username / "SWATplus_by_VPUID" / vpuid / level / site_no / model_dir


def shapes_dir(workspace: Path) -> Path:
    return workspace / "Watershed" / "Shapes"


def load_locked_inventory_rows(csv_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("status") or "").strip() != "locked_from_inventory":
                continue
            mid = (row.get("model_id") or "").strip()
            if not mid:
                continue
            rows.append(dict(row))
    return rows


def resolve_workspace_and_shapes_for_row(
    row: dict[str, str],
    user_path: Path,
    username: str,
    model_dir: str,
) -> tuple[Path, Path, str | None]:
    """
    Returns (workspace_base, shapes_dir, warn_message).
    warn_message is set if CSV level != model_id level.
    """
    model_id = (row.get("model_id") or "").strip()
    level_csv = (row.get("level") or "").strip()
    vpuid, level, site_no = parse_model_id(model_id)
    warn = None
    if level_csv and level_csv != level:
        warn = (
            f"[{model_id}]: CSV level={level_csv!r} differs from model_id level={level!r}; using model_id."
        )
    base = workspace_base(user_path, username, vpuid, level, site_no, model_dir)
    return base, shapes_dir(base), warn

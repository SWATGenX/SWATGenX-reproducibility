#!/usr/bin/env python3
"""Export tab-product-metrics.csv and LaTeX from showcase workspaces."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
from _swatgenx_paths import USER_ROOT as USER  # env-overridable: SWATGENX_USER_PATH / SWATGENX_EXAMPLE_USER
CSV_OUT = REPO / "publication/tables/tab-product-metrics.csv"
TEX_OUT = REPO / "publication/tables/generated/tab-product-metrics.tex"

MODELS = [
    ("S", "03080102", "0308/huc12/030801020804", "Oklawaha (FL)"),
    ("M", "09471300", "1505/huc12/09471300", "Upper San Pedro (AZ)"),
    ("L", "03100101", "0310/huc8/03100101", "Peace River HUC-8"),
]


def _dir_size_mb(path: Path) -> float:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total / 1e6


def _layer_ok(base: Path, name: str) -> str:
    shp = base / "Watershed/Shapes" / f"{name}.shp"
    return "yes" if shp.is_file() else "no"


def main() -> None:
    rows = []
    for tier, catalog_id, model_id, label in MODELS:
        vpuid, level, name = model_id.split("/")
        root = USER / vpuid / level / name
        stats_path = root / "channel_processing_stats.json"
        n_channels = n_subs = ""
        if stats_path.is_file():
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
            n_channels = str(stats.get("n_channels", stats.get("channels", "")))
            n_subs = str(stats.get("n_subbasins", stats.get("subbasins", "")))
        size_mb = _dir_size_mb(root) if root.is_dir() else 0.0
        rows.append({
            "row_id": f"PM-{catalog_id}",
            "tier": tier,
            "catalog_model_id": catalog_id,
            "workspace_model_id": model_id,
            "label": label,
            "tree_size_mb": f"{size_mb:.1f}",
            "streams_shp": _layer_ok(root, "SWAT_plus_streams"),
            "subbasins_shp": _layer_ok(root, "SWAT_plus_subbasins"),
            "sqlite_project": "yes" if (root / "SWAT_MODEL_Web_Application").is_dir() else "no",
            "channel_stats_json": "yes" if stats_path.is_file() else "no",
            "n_channels_stats": n_channels,
            "n_subbasins_stats": n_subs,
            "status": "frozen_from_admin_workspace",
        })
    header = list(rows[0].keys())
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    lines = [
        r"\begin{tabular}{@{}lllrrlll@{}}", r"\toprule",
        r"Tier & Model ID & Basin & Size (MB) & Streams & Subbasins & SQLite & QA JSON \\", r"\midrule",
    ]
    for r in rows:
        lines.append(
            f"{r['tier']} & \\texttt{{{r['catalog_model_id']}}} & {r['label']} & {r['tree_size_mb']} & "
            f"{r['streams_shp']} & {r['subbasins_shp']} & {r['sqlite_project']} & {r['channel_stats_json']} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    TEX_OUT.parent.mkdir(parents=True, exist_ok=True)
    TEX_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {CSV_OUT} and {TEX_OUT}")


if __name__ == "__main__":
    main()

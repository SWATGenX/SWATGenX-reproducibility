#!/usr/bin/env python3
"""Merge processing_total seconds from runtime JSONL summaries into tab-runtime.csv."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / "publication/analysis/runtime-runs"
TAB = REPO / "publication/tables/tab-runtime.csv"

MODELS = [
    ("Small", "0308/huc12/030801020804"),
    ("Medium", "1505/huc12/09471300"),
    ("Large", "0310/huc8/03100101"),
]


def _processing_total_sec(summary_md: Path) -> float | None:
    if not summary_md.is_file():
        return None
    text = summary_md.read_text(encoding="utf-8")
    m = re.search(r"processing_total[^\d]*(\d+\.?\d*)\s*s", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"Total processing[^\d]*(\d+\.?\d*)", text, re.I)
    return float(m.group(1)) if m else None


def _find_summary(model_id: str) -> Path | None:
    slug = model_id.replace("/", "_")
    candidates = sorted(RUNS.glob(f"*{slug}*summary.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    candidates = sorted(RUNS.glob("*summary.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    for c in candidates:
        if slug.split("_")[-1] in c.name:
            return c
    return None


def main() -> None:
    git_sha = ""
    try:
        import subprocess
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True,
        ).strip()
    except Exception:
        pass
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for tier, model_id in MODELS:
        summary = _find_summary(model_id)
        sec = _processing_total_sec(summary) if summary else None
        wall_min = f"{sec / 60:.2f}" if sec else ""
        rows.append({
            "tier": tier,
            "model_id": model_id,
            "provisional_inventory_wall_min": "",
            "fresh_rerun_wall_min": wall_min,
            "cpu_count": "10",
            "worker_count": "1",
            "peak_ram_gb": "",
            "git_sha": git_sha,
            "env_id": "instrumented_rerun_20260601",
            "run_datetime": now if wall_min else "",
            "status": "measured_scripted_rerun" if wall_min else "needs_fresh_rerun",
            "notes": f"From {summary.name}" if summary and wall_min else "Run time_locked_model_generation.py",
        })
    header = list(rows[0].keys())
    with TAB.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {TAB}")


if __name__ == "__main__":
    main()

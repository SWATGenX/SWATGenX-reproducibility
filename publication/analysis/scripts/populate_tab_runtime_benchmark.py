#!/usr/bin/env python3
"""Populate tab-runtime.csv from instrumented benchmark run summaries (Objective 3)."""
from __future__ import annotations

import csv
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TAB = REPO / "publication/tables/tab-runtime.csv"
ROSTER = REPO / "publication/tables/tab-model-roster.csv"
RUNS = REPO / "publication/analysis/runtime-runs"
INVENTORY = REPO / "publication/analysis/example-models-inventory.csv"

BENCHMARK_RUNS = {
    "S": "20260601-small-benchmark",
    "M": "20260601-medium-benchmark",
    "L": "20260601-large-benchmark",
}


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True,
        ).strip()
    except Exception:
        return ""


def _core_minutes(summary_md: Path) -> tuple[float | None, str]:
    if not summary_md.is_file():
        return None, ""
    text = summary_md.read_text(encoding="utf-8")
    m = re.search(r"core_processing_time[^\d]*(\d+\.?\d*)\s*s", text, re.I)
    if m:
        return float(m.group(1)) / 60.0, "core_processing_time"
    m = re.search(r"Total processing[^\d]*(\d+\.?\d*)\s*s", text, re.I)
    if m:
        return float(m.group(1)) / 60.0, "processing_total"
    return None, ""


def _inventory_wall(workspace_model_id: str) -> float | None:
    with INVENTORY.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("model_id") == workspace_model_id:
                v = (row.get("generation_wall_min") or "").strip()
                if v:
                    return float(v)
    return None


def main() -> None:
    roster = [
        r for r in csv.DictReader(ROSTER.open(newline="", encoding="utf-8"))
        if r["cohort"] == "benchmark" and r["tier"] in {"S", "M", "L"}
    ]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = _git_sha()
    out = []
    for r in roster:
        tier = r["tier"]
        run_id = BENCHMARK_RUNS[tier]
        summary = RUNS / f"{run_id}-summary.md"
        wall, metric = _core_minutes(summary)
        if wall is not None:
            status = "measured_scripted_rerun"
            env_id = "instrumented_benchmark_20260601"
            note = (
                f"Instrumented warm-cache run {run_id} on {r['workspace_model_id']}; "
                f"{metric} on vmi2525606 (10 vCPU)."
            )
            run_dt = datetime.fromtimestamp(summary.stat().st_mtime, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        else:
            wall = _inventory_wall(r["workspace_model_id"])
            status = "inventory_wall_min_fallback"
            env_id = "production_build_log"
            note = (
                f"Fallback: generation_wall_min from example-models-inventory for "
                f"{r['workspace_model_id']}; instrumented summary missing ({run_id})."
            )
            run_dt = now
        if wall is None:
            raise SystemExit(f"No assembly time for tier {tier} ({r['workspace_model_id']})")
        out.append({
            "tier": tier,
            "catalog_model_id": r["catalog_model_id"],
            "workspace_model_id": r["workspace_model_id"],
            "label": r["label"],
            "fresh_rerun_wall_min": f"{wall:.2f}",
            "cpu_count": "10",
            "worker_count": "1",
            "peak_ram_gb": "",
            "git_sha": sha,
            "env_id": env_id,
            "run_datetime": run_dt,
            "status": status,
            "notes": note,
        })
    header = list(out[0].keys())
    with TAB.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(out)
    print(f"Wrote {TAB}")


if __name__ == "__main__":
    main()

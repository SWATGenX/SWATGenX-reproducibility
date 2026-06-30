#!/usr/bin/env python3
"""Populate tab-runtime.csv with measured production assembly times (Objective 3)."""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TAB = REPO / "publication/tables/tab-runtime.csv"
ROSTER = REPO / "publication/tables/tab-model-roster.csv"
MODEL_TASKS = REPO / "web_application/logs/model_tasks.log"
QSWAT_LOG = REPO / "web_application/logs/runQSWATPlus.log"

# Measured Celery worker job duration (model_tasks.log / SwatShowcaseModel).
CELERY_MEASURED = {
    "S": {
        "site_no": "030801020804",
        "wall_min": 494.0373079776764 / 60.0,
        "run_datetime": "2026-05-14T06:38:28Z",
        "note": (
            "Celery worker job duration for 0308/huc12_outlet/030801020804 on vmi2525606 "
            "(10 vCPU; warm local caches)."
        ),
    },
    "M": {
        "site_no": "09471300",
        "wall_min": 1367.5442879199982 / 60.0,
        "run_datetime": "2026-05-06T22:44:44Z",
        "note": (
            "Celery worker job duration for 1505/usgs_station/09471300 on vmi2525606 "
            "(10 vCPU; warm local caches)."
        ),
    },
}

# L completing Celery pass was incremental (~3.3 min); dominant assembly phase from logs.
L_QSWAT_SITE = "03100101"
L_QSWAT_MAX_MIN = 88.53333333333333
L_RUN_DATETIME = "2026-04-28T06:32:03Z"


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO, text=True,
        ).strip()
    except Exception:
        return ""


def _qswat_max_minutes(site_no: str, username: str = "admin") -> float:
    if not QSWAT_LOG.is_file():
        return 0.0
    lines = QSWAT_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    marker = f"Running QSWATPlus for {site_no} for usename {username}"
    max_sec = 0.0
    i = 0
    while i < len(lines):
        if marker not in lines[i]:
            i += 1
            continue
        j = i + 1
        block_max = 0.0
        while j < len(lines):
            if j > i + 1 and lines[j].startswith("runQSWATPlus: Running QSWATPlus for"):
                break
            m = re.search(r"elapsed (\d+)m (\d+)s", lines[j])
            if m:
                block_max = max(block_max, int(m.group(1)) * 60 + int(m.group(2)))
            if lines[j].startswith("Removed script:") and site_no in lines[j]:
                break
            j += 1
        max_sec = max(max_sec, block_max)
        i = j
    return max_sec / 60.0


def _verify_celery_log(site_no: str) -> None:
    if not MODEL_TASKS.is_file():
        return
    for line in MODEL_TASKS.read_text(encoding="utf-8", errors="replace").splitlines():
        if site_no not in line or "SUCCESS" not in line:
            continue
        try:
            row = json.loads(line.split(" - ", 1)[1])
        except Exception:
            continue
        if row.get("site_no") != site_no:
            continue
        return
    print(f"warning: no SUCCESS model_tasks row for {site_no}", file=sys.stderr)


def main() -> None:
    qswat_l = _qswat_max_minutes(L_QSWAT_SITE)
    if qswat_l <= 0:
        qswat_l = L_QSWAT_MAX_MIN

    roster = [
        r for r in csv.DictReader(ROSTER.open(newline="", encoding="utf-8"))
        if r["cohort"] == "benchmark" and r["tier"] in {"S", "M", "L"}
    ]
    sha = _git_sha()
    out = []
    for r in roster:
        tier = r["tier"]
        if tier in CELERY_MEASURED:
            m = CELERY_MEASURED[tier]
            _verify_celery_log(m["site_no"])
            out.append({
                "tier": tier,
                "catalog_model_id": r["catalog_model_id"],
                "workspace_model_id": r["workspace_model_id"],
                "label": r["label"],
                "fresh_rerun_wall_min": f"{m['wall_min']:.2f}",
                "cpu_count": "10",
                "worker_count": "1",
                "peak_ram_gb": "",
                "git_sha": sha,
                "env_id": "production_celery_vmi2525606",
                "run_datetime": m["run_datetime"],
                "status": "measured_celery_job",
                "notes": m["note"],
            })
        else:
            out.append({
                "tier": tier,
                "catalog_model_id": r["catalog_model_id"],
                "workspace_model_id": r["workspace_model_id"],
                "label": r["label"],
                "fresh_rerun_wall_min": f"{qswat_l:.2f}",
                "cpu_count": "10",
                "worker_count": "1",
                "peak_ram_gb": "",
                "git_sha": sha,
                "env_id": "production_qswat_log_vmi2525606",
                "run_datetime": L_RUN_DATETIME,
                "status": "measured_qswat_assembly_max",
                "notes": (
                    f"Maximum logged QSWAT+ project-assembly wall time for admin "
                    f"0310/huc8/{L_QSWAT_SITE} during Apr 2026 production build "
                    f"(completing Celery pass was warm-cache incremental)."
                ),
            })
    header = list(out[0].keys())
    with TAB.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(out)
    print(f"Wrote {TAB}")


if __name__ == "__main__":
    main()

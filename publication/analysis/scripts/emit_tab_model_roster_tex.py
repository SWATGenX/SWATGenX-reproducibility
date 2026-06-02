#!/usr/bin/env python3
"""Emit compact LaTeX summary table for manuscript model roster (introduction)."""
from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "publication/tables/tab-model-roster.csv"
OUT = REPO / "publication/tables/generated/tab-model-roster.tex"

SUMMARY = (
    (
        "Benchmark S/M/L",
        "03080102, 09471300, 03100101",
        "Humid subtropical; semi-arid SW; humid subtropical (whole HUC8)",
        "Obj.~1--3, 5",
    ),
    (
        "Scaling X20/X40/X60",
        "03152000, 07174000, 15060105",
        "Humid temperate; Great Plains; Pacific maritime",
        "Obj.~5 only",
    ),
    (
        "Cal / sensitivity gages",
        "02297600, 05536265",
        "Humid subtropical; snow-influenced temperate",
        "Obj.~4 only",
    ),
)


def main() -> None:
    # Validate CSV still matches summary IDs (fail fast if roster drifts)
    ids = {r["catalog_model_id"] for r in csv.DictReader(CSV_PATH.open(newline="", encoding="utf-8"))}
    expected = {
        "03080102", "09471300", "03100101",
        "03152000", "07174000", "15060105",
        "02297600", "05536265",
    }
    if ids != expected:
        raise SystemExit(f"tab-model-roster.csv IDs changed; update SUMMARY in emit script. Got: {sorted(ids)}")

    lines = [
        r"\begin{tabular}{@{}p{2.5cm}p{4.2cm}p{4.8cm}p{2.0cm}@{}}",
        r"\toprule",
        r"Evaluation set & Catalog model IDs & Hydroclimate / domain type & Objectives \\",
        r"\midrule",
    ]
    for label, model_ids, hydro, objs in SUMMARY:
        lines.append(f"{label} & \\texttt{{{model_ids}}} & {hydro} & {objs} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(SUMMARY)} summary rows)")


if __name__ == "__main__":
    main()

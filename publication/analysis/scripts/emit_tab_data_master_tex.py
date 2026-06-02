#!/usr/bin/env python3
"""Emit abridged Tab-DataMaster LaTeX for Methods."""
from __future__ import annotations

import csv
from pathlib import Path

from latex_emit_utils import latex_escape

REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "publication/tables/tab-data-master.csv"
OUT = REPO / "publication/tables/generated/tab-data-master-abridged.tex"

KEEP = {
    "DM-01", "DM-02", "DM-03", "DM-04", "DM-05", "DM-06", "DM-07", "DM-08",
}


def main() -> None:
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["row_id"] in KEEP:
                rows.append(row)
    lines = [
        r"\begin{tabular}{@{}llp{5.5cm}@{}}", r"\toprule",
        r"Dataset & Provider & Role in SWATGenX \\", r"\midrule",
    ]
    for r in rows:
        ds = r["dataset_or_layer"].split("(")[0].strip()
        if len(ds) > 48:
            ds = ds[:45] + r"\ldots"
        prov = latex_escape(r["provider"])
        role = latex_escape(r["role_in_swatgenx"])
        if len(role) > 80:
            role = role[:77] + r"\ldots"
        lines.append(f"{ds} & {prov} & {role} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

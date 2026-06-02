#!/usr/bin/env python3
"""Emit abridged Tab-NHDRules LaTeX for Methods."""
from __future__ import annotations

import csv
from pathlib import Path

from latex_emit_utils import latex_escape

REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "publication/tables/tab-nhd-rules.csv"
OUT = REPO / "publication/tables/generated/tab-nhd-rules-abridged.tex"

KEEP = [f"NH-{i:02d}" for i in range(0, 13)]


def main() -> None:
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["rule_id"] in KEEP:
                rows.append(row)
    lines = [
        r"\begin{tabular}{@{}llp{6.8cm}@{}}", r"\toprule",
        r"Rule & Name & Processing action \\", r"\midrule",
    ]
    for r in rows:
        name = latex_escape(r["rule_name"])
        action = latex_escape(r["processing_action"])
        if len(action) > 95:
            action = action[:92] + r"\ldots"
        lines.append(f"{r['rule_id']} & {name} & {action} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

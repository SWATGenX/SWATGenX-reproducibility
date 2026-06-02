#!/usr/bin/env python3
"""Emit abridged Tab-PackageManifest LaTeX for Methods."""
from __future__ import annotations

import csv
from pathlib import Path

from latex_emit_utils import latex_escape

REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "publication/tables/tab-package-manifest.csv"
OUT = REPO / "publication/tables/generated/tab-package-manifest-abridged.tex"

KEEP = {"PKG-01", "PKG-02", "PKG-03", "PKG-04", "PKG-07", "PKG-10", "PKG-12", "PKG-13"}

CLASS_LABEL = {
    "vector_shapefile": "Vector shapefile",
    "weather_text": "Weather text",
    "json_sidecar": "JSON sidecar",
    "swatplus_sqlite_project": "SWAT+ SQLite project",
    "zip_deliverable": "Project archive",
    "project_archive": "Project archive",
}

PURPOSE_OVERRIDE = {
    "PKG-13": "Exported SWAT+ project archive bundle",
}


def display_class(raw: str) -> str:
    return latex_escape(CLASS_LABEL.get(raw, raw.replace("_", " ")))


def main() -> None:
    rows = []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["artifact_id"] in KEEP:
                rows.append(row)
    lines = [
        r"\begin{tabularx}{\textwidth}{@{}lYl@{}}",
        r"\toprule",
        r"Output class & Purpose & Always? \\",
        r"\midrule",
    ]
    for r in rows:
        cls = display_class(r["artifact_class"])
        purpose = latex_escape(PURPOSE_OVERRIDE.get(r["artifact_id"], r["purpose"]))
        if len(purpose) > 72:
            purpose = purpose[:69] + r"\ldots"
        always = latex_escape(r["always_optional"])
        lines.append(f"{cls} & {purpose} & {always} \\\\")
    lines += [r"\bottomrule", r"\end{tabularx}"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

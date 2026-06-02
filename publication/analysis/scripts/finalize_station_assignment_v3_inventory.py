#!/usr/bin/env python3
"""Publish canonical v3 station-assignment inventory CSVs from frozen shadow artifacts.

v3 (NHD-first / SWAT-second) is the production streamflow assignment method. This script
consolidates per-model ``stations_assignment_v3.csv`` from the closed shadow run into
portfolio inventory artifacts. It does not re-run assignment or modify workspaces.

Peace watershed (catalog ``03100101``) is excluded from refresh: existing Peace rows in
the prior inventory detail CSV are preserved unchanged while the user rebuilds that model.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from station_assignment_v3_lib import AssignmentInputs, summarize_assignment_v3  # noqa: E402

QA = REPO / "publication/analysis/qa"
PEACE_CID = "03100101"
ROSTER_CSV = REPO / "publication/tables/tab-model-roster.csv"
SHOWCASE_CSV = REPO / "publication/analysis/example-models-inventory.csv"

def _resolve_shadow_root(suffix: str) -> Path:
    live = QA / f"station-assignment-v3-shadow{suffix}"
    if live.is_dir():
        return live
    archive = QA / "archive"
    if suffix == "-showcase":
        pattern = "station-assignment-v3-shadow-showcase-*"
    else:
        pattern = "station-assignment-v3-shadow-roster-*"
    matches = sorted(archive.glob(pattern))
    if matches:
        return matches[-1]
    return live


SUITES = {
    "roster": {
        "roster": ROSTER_CSV,
        "suffix": "",
        "detail": QA / "station-assignment-v3-inventory-detail.csv",
        "title": "evaluation roster (8 models)",
    },
    "showcase": {
        "roster": SHOWCASE_CSV,
        "suffix": "-showcase",
        "detail": QA / "station-assignment-v3-showcase-inventory-detail.csv",
        "title": "showcase disk inventory (~70 models)",
    },
}


def _catalog_ids_from_roster(path: Path, suite: str) -> list[str]:
    df = pd.read_csv(path, dtype=str)
    if suite == "showcase":
        col = "site_no" if "site_no" in df.columns else "catalog_model_id"
        return [str(x).strip().zfill(8) for x in df[col]]
    return [str(x).strip().zfill(8) for x in df["catalog_model_id"]]


def _inputs_from_detail_row(row: pd.Series) -> AssignmentInputs:
    ws = str(row["workspace_model_id"])
    parts = ws.split("/")
    vpuid = parts[0] if parts else ""
    level = parts[1] if len(parts) > 1 else ""
    name = parts[-1] if parts else ""
    return AssignmentInputs(
        vpuid=vpuid,
        level=level,
        name=name,
        txtinout=Path("."),
        meta_csv=Path("."),
        catalog_model_id=str(row["catalog_model_id"]).zfill(8),
        workspace_model_id=ws,
        label=str(row.get("label") or ws),
    )


def _load_frozen_peace(detail_path: Path) -> pd.DataFrame:
    if not detail_path.is_file():
        return pd.DataFrame()
    df = pd.read_csv(detail_path, dtype={"site_no": str, "catalog_model_id": str})
    df["catalog_model_id"] = df["catalog_model_id"].str.zfill(8)
    return df[df["catalog_model_id"] == PEACE_CID].copy()


def _load_shadow_detail(shadow_root: Path, catalog_id: str) -> pd.DataFrame | None:
    p = shadow_root / catalog_id / "stations_assignment_v3.csv"
    if not p.is_file():
        return None
    df = pd.read_csv(p, dtype={"site_no": str, "catalog_model_id": str})
    df["site_no"] = df["site_no"].str.zfill(8)
    df["catalog_model_id"] = df["catalog_model_id"].str.zfill(8)
    return df


def portfolio_markdown(
    summaries: list[dict],
    skipped: list[str],
    *,
    suite_title: str,
    detail_name: str,
    peace_frozen: bool,
) -> str:
    n_models = len(summaries)
    n_stations = sum(s["n_stations"] for s in summaries)
    n_cal = sum(s["n_calibration_ready"] for s in summaries)
    n_review = sum(s["n_review"] for s in summaries)
    n_exclude = sum(s["n_exclude"] for s in summaries)
    pct_cal = round(100.0 * n_cal / n_stations, 1) if n_stations else 0.0
    has_legacy = summaries and summaries[0].get("n_changed_gis") is not None
    n_changed = sum(s.get("n_changed_gis") or 0 for s in summaries) if has_legacy else None
    n_same = sum(s.get("n_same_gis") or 0 for s in summaries) if has_legacy else None

    lines = [
        f"# Station assignment v3 — portfolio inventory ({suite_title})",
        "",
        "NHD-first reference reach (no SWAT area), SWAT-second map to `chandeg.con`. "
        "**v3 is the production assignment method** used by `fetch_streamflow_for_watershed`.",
        "",
    ]
    if peace_frozen:
        lines.append(
            f"**Peace (`{PEACE_CID}`) rows are frozen** from the prior inventory while that watershed model is rebuilt."
        )
        lines.append("")
    lines.extend(
        [
            "## Portfolio totals",
            "",
            "| Metric | Value |",
            "|--------|------:|",
            f"| Models in roster | {n_models + len(skipped)} |",
            f"| Models in inventory | {n_models} |",
            f"| Models skipped (no shadow artifact) | {len(skipped)} |",
            f"| USGS stations | {n_stations} |",
            f"| Calibration-ready | {n_cal} ({pct_cal}%) |",
            f"| Review class | {n_review} |",
            f"| Exclude / missing | {n_exclude} |",
        ]
    )
    if has_legacy and n_changed is not None:
        pct_unchanged = round(100.0 * n_same / n_stations, 1) if n_stations and n_same is not None else 0.0
        lines.extend(
            [
                f"| Same GIS channel as legacy `stations.shp` | {n_same} ({pct_unchanged}%) |",
                f"| Changed vs legacy GIS channel | {n_changed} ({round(100 - pct_unchanged, 1)}%) |",
            ]
        )
    header = "| Catalog ID | Workspace | Stations | Cal-ready | Review | Exclude |"
    sep = "|------------|-----------|---------:|----------:|-------:|--------:|"
    if has_legacy:
        header += " Legacy unchanged | Legacy changed |"
        sep += "----------------:|---------------:|"
    lines.extend(["", "## Per model", "", header, sep])
    for s in summaries:
        ws = s.get("workspace_model_id", "")
        row = (
            f"| `{s['catalog_model_id']}` | `{ws}` | {s['n_stations']} | "
            f"{s['n_calibration_ready']} | {s['n_review']} | {s['n_exclude']} |"
        )
        if has_legacy:
            row += f" {s.get('n_same_gis', '—')} | {s.get('n_changed_gis', '—')} |"
        lines.append(row)
    if skipped:
        lines.extend(["", "## Skipped", ""])
        for msg in skipped:
            lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            f"Detail: `{detail_name}`",
            "",
            "Shadow per-model artifacts were archived under "
            "`publication/analysis/qa/archive/` (inventory closed 2026-05-31).",
            "",
        ]
    )
    return "\n".join(lines)


def finalize_suite(suite: str, *, freeze_peace: bool) -> None:
    cfg = SUITES[suite]
    suffix = cfg["suffix"]
    shadow_root = _resolve_shadow_root(suffix)
    out_summary = QA / f"station-assignment-v3{suffix}-inventory-summary.csv"
    out_detail = QA / f"station-assignment-v3{suffix}-inventory-detail.csv"
    out_md = QA / f"station-assignment-v3{suffix}-inventory-summary.md"
    prior_detail = cfg["detail"]

    catalog_ids = _catalog_ids_from_roster(cfg["roster"], suite)
    peace_frozen = freeze_peace and PEACE_CID in catalog_ids
    peace_df = _load_frozen_peace(prior_detail) if peace_frozen else pd.DataFrame()

    detail_parts: list[pd.DataFrame] = []
    skipped: list[str] = []
    summaries: list[dict] = []

    for cid in catalog_ids:
        if peace_frozen and cid == PEACE_CID:
            continue
        part = _load_shadow_detail(shadow_root, cid)
        if part is None:
            skipped.append(f"{cid}: no {shadow_root.name}/{cid}/stations_assignment_v3.csv (shadow archive)")
            continue
        detail_parts.append(part)
        summaries.append(summarize_assignment_v3(part, _inputs_from_detail_row(part.iloc[0])))

    if peace_frozen and len(peace_df):
        detail_parts.append(peace_df)
        summaries.append(summarize_assignment_v3(peace_df, _inputs_from_detail_row(peace_df.iloc[0])))
        summaries.sort(key=lambda s: s["catalog_model_id"])

    if not detail_parts:
        raise SystemExit(f"No detail rows for suite={suite}")

    detail_df = pd.concat(detail_parts, ignore_index=True)
    summary_df = pd.DataFrame(summaries)

    portfolio_extra = {
        "suite": suite,
        "inventory_status": "canonical_v3_production",
        "peace_frozen": peace_frozen,
        "n_models_processed": int(len(summary_df)),
        "n_models_skipped": len(skipped),
        "n_models_with_changed_station": int((summary_df["n_changed_gis"] > 0).sum())
        if "n_changed_gis" in summary_df.columns
        else None,
        "n_stations_total": int(summary_df["n_stations"].sum()),
        "n_stations_changed": int(summary_df["n_changed_gis"].sum())
        if "n_changed_gis" in summary_df.columns
        else None,
    }
    (QA / f"station-assignment-v3{suffix}-portfolio-totals.json").write_text(
        json.dumps(portfolio_extra, indent=2),
        encoding="utf-8",
    )

    out_summary.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(out_summary, index=False)
    detail_df.to_csv(out_detail, index=False)
    out_md.write_text(
        portfolio_markdown(
            summaries,
            skipped,
            suite_title=cfg["title"],
            detail_name=out_detail.name,
            peace_frozen=peace_frozen,
        ),
        encoding="utf-8",
    )

    print(f"[{suite}] Wrote {out_summary} ({len(summary_df)} models)")
    print(f"[{suite}] Wrote {out_detail} ({len(detail_df)} rows)")
    print(f"[{suite}] Wrote {out_md}")
    if peace_frozen:
        print(f"[{suite}] Peace ({PEACE_CID}) frozen: {len(peace_df)} station rows unchanged")


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize v3 portfolio inventory from shadow artifacts")
    parser.add_argument(
        "--suite",
        choices=sorted(SUITES),
        action="append",
        help="roster and/or showcase (default: both)",
    )
    parser.add_argument(
        "--no-freeze-peace",
        action="store_true",
        help="Include Peace from shadow artifacts instead of freezing prior inventory rows",
    )
    args = parser.parse_args()
    suites = args.suite or sorted(SUITES)
    freeze_peace = not args.no_freeze_peace
    for suite in suites:
        finalize_suite(suite, freeze_peace=freeze_peace)


if __name__ == "__main__":
    main()

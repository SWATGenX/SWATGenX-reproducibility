#!/usr/bin/env python3
"""Legacy portfolio shadow-run: v3 station assignment vs production stations.shp.

**Closed 2026-05-31.** v3 is production; publish inventory with
``finalize_station_assignment_v3_inventory.py`` instead. Per-model shadow outputs
belong under ``publication/analysis/qa/archive/``.

Does not modify stations.shp.

Suites:
  roster   — publication/tables/tab-model-roster.csv (8 evaluation models)
  showcase — publication/analysis/example-models-inventory.csv (~70 disk-success models)

Outputs (per suite):
  publication/analysis/qa/station-assignment-v3[-showcase]-inventory-summary.csv
  publication/analysis/qa/station-assignment-v3[-showcase]-inventory-detail.csv
  publication/analysis/qa/station-assignment-v3[-showcase]-inventory-summary.md
  publication/analysis/qa/station-assignment-v3-shadow[-showcase]/<catalog_id>/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from compare_peace_drainage_area_txtinout_vs_nhd import load_station_names  # noqa: E402
from run_nhd_preprocessing_qa_benchmark import _find_zip, _vpu_original_cache  # noqa: E402
from station_assignment_v3_lib import (  # noqa: E402
    assign_model_v3,
    domain_huc12s,
    load_nhd_enriched_domain,
    resolve_model_paths,
    write_shadow_products,
)

ROSTER_CSV = REPO / "publication/tables/tab-model-roster.csv"
SHOWCASE_CSV = REPO / "publication/analysis/example-models-inventory.csv"
QA = REPO / "publication/analysis/qa"

SUITES = {
    "roster": {
        "roster": ROSTER_CSV,
        "suffix": "",
        "title": "evaluation roster (8 models)",
    },
    "showcase": {
        "roster": SHOWCASE_CSV,
        "suffix": "-showcase",
        "title": "showcase disk inventory (~70 models)",
    },
}


def _nhd_cache_key(vpuid: str, huc12s: list[str]) -> str:
    return f"{vpuid}:{','.join(sorted(h.zfill(12) for h in huc12s))}"


def roster_from_showcase_inventory(path: Path) -> pd.DataFrame:
    inv = pd.read_csv(path, dtype={"site_no": str, "model_id": str, "vpuid": str})
    rows = []
    for _, r in inv.iterrows():
        site = str(r["site_no"]).strip().zfill(8)
        mid = str(r["model_id"]).strip()
        state = str(r.get("state_abbr") or "").strip()
        kind = str(r.get("model_kind") or "").strip()
        label = f"{mid} ({state or kind or 'showcase'})"
        rows.append(
            {
                "catalog_model_id": site,
                "workspace_model_id": mid,
                "label": label,
                "model_kind": kind,
                "state": state,
            }
        )
    return pd.DataFrame(rows)


def load_roster(path: Path, suite: str) -> pd.DataFrame:
    if suite == "showcase" or path.resolve() == SHOWCASE_CSV.resolve():
        return roster_from_showcase_inventory(path)
    df = pd.read_csv(path, dtype={"catalog_model_id": str})
    if "workspace_model_id" not in df.columns:
        raise SystemExit(f"{path} missing workspace_model_id column")
    return df


def portfolio_markdown(
    summaries: list[dict],
    skipped: list[str],
    *,
    suite_title: str,
    detail_name: str,
    shadow_dir: str,
) -> str:
    n_models = len(summaries)
    n_stations = sum(s["n_stations"] for s in summaries)
    n_same = sum(s["n_same_gis"] for s in summaries)
    n_changed = sum(s["n_changed_gis"] for s in summaries)
    n_cal = sum(s["n_calibration_ready"] for s in summaries)
    n_review = sum(s["n_review"] for s in summaries)
    n_exclude = sum(s["n_exclude"] for s in summaries)
    n_models_affected = sum(1 for s in summaries if s["n_changed_gis"] > 0)
    n_models_unchanged = sum(1 for s in summaries if s["n_changed_gis"] == 0 and s["n_stations"] > 0)
    pct_unchanged = round(100.0 * n_same / n_stations, 1) if n_stations else 0.0
    pct_cal = round(100.0 * n_cal / n_stations, 1) if n_stations else 0.0
    pct_models_affected = round(100.0 * n_models_affected / n_models, 1) if n_models else 0.0

    lines = [
        f"# Station assignment v3 — portfolio shadow run ({suite_title})",
        "",
        "NHD-first reference reach (no SWAT area), SWAT-second map to `chandeg.con`, compared to production `stations.shp`.",
        "**Production assignments were not modified.**",
        "",
        "## Portfolio totals",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Models in roster | {n_models + len(skipped)} |",
        f"| Models processed | {n_models} |",
        f"| Models skipped | {len(skipped)} |",
        f"| **Models with ≥1 changed station** | **{n_models_affected} ({pct_models_affected}%)** |",
        f"| Models with all stations unchanged | {n_models_unchanged} |",
        f"| USGS stations | {n_stations} |",
        f"| Same GIS channel (production = v3) | {n_same} ({pct_unchanged}%) |",
        f"| Changed GIS channel | {n_changed} ({round(100 - pct_unchanged, 1)}%) |",
        f"| Calibration-ready | {n_cal} ({pct_cal}%) |",
        f"| Review class | {n_review} |",
        f"| Exclude / missing | {n_exclude} |",
        "",
        "## Per model",
        "",
        "| Catalog ID | Workspace | Stations | Unchanged | Changed | Cal-ready | Review | Exclude |",
        "|------------|-----------|---------:|----------:|--------:|----------:|-------:|--------:|",
    ]
    for s in summaries:
        ws = s.get("workspace_model_id", "")
        lines.append(
            f"| `{s['catalog_model_id']}` | `{ws}` | {s['n_stations']} | "
            f"{s['n_same_gis']} | {s['n_changed_gis']} | {s['n_calibration_ready']} | "
            f"{s['n_review']} | {s['n_exclude']} |"
        )
    if skipped:
        lines.extend(["", "## Skipped", ""])
        for msg in skipped:
            lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            f"Detail: `{detail_name}`",
            "",
            f"Per-model shadow: `{shadow_dir}/`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shadow v3 station assignment portfolio run")
    parser.add_argument(
        "--suite",
        choices=sorted(SUITES),
        default="roster",
        help="roster = 8 evaluation models; showcase = full example-models-inventory.csv",
    )
    parser.add_argument("--roster", type=Path, help="Override roster/inventory CSV path")
    parser.add_argument("--catalog-id", action="append", help="Run only these catalog model IDs (repeatable)")
    args = parser.parse_args()

    cfg = SUITES[args.suite]
    roster_path = args.roster or cfg["roster"]
    suffix = cfg["suffix"]
    shadow_root = QA / f"station-assignment-v3-shadow{suffix}"
    out_summary = QA / f"station-assignment-v3{suffix}-inventory-summary.csv"
    out_detail = QA / f"station-assignment-v3{suffix}-inventory-detail.csv"
    out_md = QA / f"station-assignment-v3{suffix}-inventory-summary.md"

    roster = load_roster(roster_path, args.suite)
    if args.catalog_id:
        want = {c.zfill(8) for c in args.catalog_id}
        roster = roster[roster["catalog_model_id"].astype(str).str.zfill(8).isin(want)]

    names = load_station_names()
    nhd_cache: dict[str, gpd.GeoDataFrame] = {}
    summaries: list[dict] = []
    detail_parts: list[pd.DataFrame] = []
    skipped: list[str] = []

    print(f"Shadow v3 [{args.suite}] for {len(roster)} models from {roster_path.name}")
    for _, row in roster.iterrows():
        cid = str(row["catalog_model_id"]).strip().zfill(8)
        label = str(row.get("label") or row.get("workspace_model_id") or cid)
        print(f"  {cid} {label}…")
        try:
            paths = resolve_model_paths(row.to_dict())
            if paths is None:
                msg = f"{cid} ({label}): missing stations.shp or chandeg.con"
                print(f"    skip: {msg}")
                skipped.append(msg)
                continue

            try:
                _find_zip(paths.vpuid)
            except FileNotFoundError as exc:
                msg = f"{cid} ({label}): {exc}"
                print(f"    skip: {msg}")
                skipped.append(msg)
                continue

            try:
                huc12s = domain_huc12s(paths)
            except (ValueError, FileNotFoundError) as exc:
                msg = f"{cid} ({label}): domain HUC12 resolution failed — {exc}"
                print(f"    skip: {msg}")
                skipped.append(msg)
                continue

            cache_key = _nhd_cache_key(paths.vpuid, huc12s)
            if cache_key not in nhd_cache:
                print(f"    loading NHD HR ({paths.vpuid}, {len(huc12s)} HUC12s)…")
                try:
                    nhd_cache[cache_key] = load_nhd_enriched_domain(paths.vpuid, huc12s)
                except FileNotFoundError as exc:
                    msg = f"{cid} ({label}): {exc}"
                    print(f"    skip: {msg}")
                    skipped.append(msg)
                    continue

            try:
                detail, summary = assign_model_v3(paths, names=names, flows_gdf=nhd_cache[cache_key])
            except Exception as exc:
                msg = f"{cid} ({label}): assignment failed — {exc}"
                print(f"    skip: {msg}")
                skipped.append(msg)
                continue
            write_shadow_products(detail, summary, shadow_root)
            summaries.append(summary)
            detail_parts.append(detail)
            print(
                f"    {summary['n_stations']} stations, {summary['n_changed_gis']} changed, "
                f"{summary['n_calibration_ready']} cal-ready"
            )
        finally:
            # Full HU4 GDB layers are cached per VPUID in run_nhd_preprocessing_qa_benchmark;
            # drop after each model so a long portfolio run does not retain every VPU in RAM.
            if _vpu_original_cache:
                _vpu_original_cache.clear()
            # Clipped flowline GeoDataFrames also accumulate (large HUC-8 domains); release each step.
            nhd_cache.clear()

    if not summaries:
        raise SystemExit("No models processed.")

    summary_df = pd.DataFrame(summaries)
    detail_df = pd.concat(detail_parts, ignore_index=True)

    n_models_affected = int((summary_df["n_changed_gis"] > 0).sum())
    portfolio_extra = {
        "suite": args.suite,
        "n_models_processed": int(len(summary_df)),
        "n_models_skipped": len(skipped),
        "n_models_with_changed_station": n_models_affected,
        "n_stations_total": int(summary_df["n_stations"].sum()),
        "n_stations_changed": int(summary_df["n_changed_gis"].sum()),
    }
    (QA / f"station-assignment-v3{suffix}-portfolio-totals.json").write_text(
        __import__("json").dumps(portfolio_extra, indent=2),
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
            shadow_dir=shadow_root.name,
        ),
        encoding="utf-8",
    )

    n_st = int(summary_df["n_stations"].sum())
    n_ch = int(summary_df["n_changed_gis"].sum())
    print(f"\nWrote {out_summary}")
    print(f"Wrote {out_detail} ({len(detail_df)} rows)")
    print(f"Wrote {out_md}")
    print(
        f"Portfolio: {len(summaries)} models ({n_models_affected} affected), "
        f"{n_st} stations, {n_ch} changed ({round(100 * n_ch / n_st, 1) if n_st else 0}%)"
    )


if __name__ == "__main__":
    main()

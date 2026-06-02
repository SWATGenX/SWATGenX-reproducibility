#!/usr/bin/env python3
"""Export Objective 5 benchmark tables from swatPlusRuntimeBenchmarkCatalog.json."""
from __future__ import annotations

import csv
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = REPO_ROOT / "web_application/frontend/src/data/swatPlusRuntimeBenchmarkCatalog.json"
TABLES = REPO_ROOT / "publication/tables"


def _scenario(catalog: dict, sid: str) -> dict:
    for s in catalog["scenarios"]:
        if s["id"] == sid:
            return s
    raise KeyError(sid)


def _write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {path} ({len(rows)} rows)")


def export_primary(catalog: dict) -> None:
    scen = _scenario(catalog, "outputFiltering")
    rows = []
    for i, res in enumerate(scen["results"], start=1):
        nc = res["filteredNc"]
        rows.append({
            "row_id": f"RB-{i:02d}",
            "tier": res["tier"],
            "model_id": res["modelId"],
            "label": res["label"],
            "hrus": str(res["hrus"]),
            "channels": str(res.get("channels", "")),
            "wall_s": str(nc["wallS"]),
            "sec_per_day": str(nc["secPerDay"]),
            "peak_rss_kb": str(nc.get("rssKb", "")),
            "status": "frozen_from_runtime_benchmark_catalog",
        })
    _write_csv(
        TABLES / "tab-runtime-benchmark.csv",
        ["row_id", "tier", "model_id", "label", "hrus", "channels", "wall_s", "sec_per_day", "peak_rss_kb", "status"],
        rows,
    )


def export_print_scope(catalog: dict) -> None:
    scen = _scenario(catalog, "outputFiltering")
    rows = []
    rid = 1
    for res in scen["results"]:
        if res.get("skipped"):
            continue
        for profile in ("fullNc", "filteredNc"):
            run = res.get(profile)
            if not run:
                continue
            rows.append({
                "row_id": f"PS-{rid:02d}",
                "tier": res["tier"],
                "model_id": res["modelId"],
                "print_scope": "full_export" if profile == "fullNc" else "calibration_filtered",
                "wall_s": str(run["wallS"]),
                "sec_per_day": str(run["secPerDay"]),
                "channel_sd_mb": f"{run.get('channelSdBytes', 0) / 1e6:.2f}",
                "status": "frozen_from_runtime_benchmark_catalog",
            })
            rid += 1
    _write_csv(
        TABLES / "tab-runtime-benchmark-print-scope.csv",
        ["row_id", "tier", "model_id", "print_scope", "wall_s", "sec_per_day", "channel_sd_mb", "status"],
        rows,
    )


def export_nc_vs_txt(catalog: dict) -> None:
    scen = _scenario(catalog, "ncImplementation")
    rows = []
    rid = 1
    for res in scen["results"]:
        if res.get("skipped"):
            continue
        for fmt in ("nc", "txt"):
            run = res.get(fmt)
            if not run:
                continue
            rows.append({
                "row_id": f"NT-{rid:02d}",
                "tier": res["tier"],
                "model_id": res["modelId"],
                "output_format": fmt.upper(),
                "wall_s": str(run["wallS"]),
                "sec_per_day": str(run["secPerDay"]),
                "total_output_gb": f"{max(run.get('outputNcBytes', 0), run.get('outputTxtBytes', 0)) / 1e9:.2f}",
                "status": "frozen_from_runtime_benchmark_catalog",
            })
            rid += 1
    _write_csv(
        TABLES / "tab-runtime-benchmark-nc-vs-txt.csv",
        ["row_id", "tier", "model_id", "output_format", "wall_s", "sec_per_day", "total_output_gb", "status"],
        rows,
    )


def export_compiler(catalog: dict) -> None:
    scen = _scenario(catalog, "compiler")
    rows = []
    rid = 1
    for res in scen["matrix"]:
        for var in res["variants"]:
            if var.get("wallS") is None:
                continue
            rows.append({
                "row_id": f"CP-{rid:02d}",
                "tier": res["tier"],
                "model_id": res["modelId"],
                "variant_id": var["id"],
                "label": var["label"],
                "production": "yes" if var.get("production") else "no",
                "wall_s": str(var["wallS"]),
                "sec_per_day": str(var["secPerDay"]),
                "vs_ref_pct": str(var.get("vsRefPct", "")),
                "status": "frozen_from_runtime_benchmark_catalog",
            })
            rid += 1
    _write_csv(
        TABLES / "tab-runtime-benchmark-compiler.csv",
        ["row_id", "tier", "model_id", "variant_id", "label", "production", "wall_s", "sec_per_day", "vs_ref_pct", "status"],
        rows,
    )


def export_hru_scaling(catalog: dict) -> None:
    hs = catalog["hruScaling"]
    rows = []
    for i, pt in enumerate(hs["points"], start=1):
        rows.append({
            "row_id": f"HS-{i:02d}",
            "tier": pt["tier"],
            "model_id": pt["modelId"],
            "label": pt["label"],
            "hrus": str(pt["hrus"]),
            "channels": str(pt["channels"]),
            "wall_s": str(pt["wallS"]),
            "sec_per_day": str(pt["secPerDay"]),
            "init_s": str(pt.get("initS", "")),
            "daily_loop_s": str(pt.get("dailyLoopS", "")),
            "status": "frozen_from_runtime_benchmark_catalog",
        })
    _write_csv(
        TABLES / "tab-runtime-benchmark-hru-scaling.csv",
        ["row_id", "tier", "model_id", "label", "hrus", "channels", "wall_s", "sec_per_day", "init_s", "daily_loop_s", "status"],
        rows,
    )


def export_vtune(catalog: dict) -> None:
    hs = catalog["hruScaling"]
    rows = []
    rid = 1
    for prof in hs.get("vtune", {}).get("profiles", []):
        rows.append({
            "row_id": f"VT-{rid:02d}",
            "tier": prof["tier"],
            "model_id": prof["modelId"],
            "sim_window_days": str(prof.get("simWindowDays", "")),
            "hru_control_pct_daily": str(prof.get("hruControlPctDaily", "")),
            "channel_pct_daily": str(prof.get("channelPctDaily", "")),
            "strcmp_pct_daily": str(prof.get("strcmpPctDaily", "")),
            "memset_pct_daily": str(prof.get("memsetPctDaily", "")),
            "init_pct": str(prof.get("initPct", "")),
            "status": "frozen_from_runtime_benchmark_catalog",
        })
        rid += 1
    _write_csv(
        TABLES / "tab-runtime-benchmark-vtune.csv",
        ["row_id", "tier", "model_id", "sim_window_days", "hru_control_pct_daily", "channel_pct_daily", "strcmp_pct_daily", "memset_pct_daily", "init_pct", "status"],
        rows,
    )


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    export_primary(catalog)
    export_print_scope(catalog)
    export_nc_vs_txt(catalog)
    export_compiler(catalog)
    export_hru_scaling(catalog)
    export_vtune(catalog)


if __name__ == "__main__":
    main()

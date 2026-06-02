#!/usr/bin/env python3
"""Export Objective 4 (controlled cal/val/sensitivity basins) and Objective 5 (runtime benchmark).

Prerequisites for Default_calval_split202606 re-export (do not run until both basins finish):
  1. FL 02297600: cal scored 2013-2018, ver scored 2019-2024 (post-calibration holdout)
  2. IL 05536265: cal scored 2020-2024, ver scored 2012-2015 (pre-calibration holdout)
  3. python publication/analysis/scripts/verify_calval_split202606_postrun.py  (exit 0)
  4. Update BASINS below: run_label, cal_period, ver_period, cal_iter, metrics_rows, calval_scenario
  5. Morris sensitivity figures still read from Default_initialized (unchanged)
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
import sys as _sys; _sys.path.insert(0, str(Path(__file__).resolve().parent))
from _swatgenx_paths import USER_PATH as USER_ROOT, EXAMPLE_USER  # env-overridable
CATALOG_JSON = REPO_ROOT / "web_application/frontend/src/data/swatPlusRuntimeBenchmarkCatalog.json"

TAB_METRICS = REPO_ROOT / "publication/tables/tab-metrics.csv"
TAB_MORRIS = REPO_ROOT / "publication/tables/tab-sensitivity-morris.csv"
TAB_ENSEMBLE_METRICS = REPO_ROOT / "publication/tables/tab-sensitivity-ensemble-metrics.csv"
TAB_RUNTIME_BENCH = REPO_ROOT / "publication/tables/tab-runtime-benchmark.csv"
TAB_CAL_SETTINGS = REPO_ROOT / "publication/tables/tab-calibration-run-settings.csv"

METRICS_HEADER = [
    "row_id", "model_id", "site_no", "state", "run_label", "workflow_stage", "scored_period",
    "time_step", "station_id", "nse", "kge", "pbias_pct", "rmse", "rmse_units", "mpe_pct", "status", "notes",
]
MORRIS_HEADER = [
    "rank", "model_id", "site_no", "run_label", "parameter", "mu", "mu_star", "sigma",
    "mu_star_conf", "status",
]


@dataclass(frozen=True)
class BasinExport:
    model_id: str
    site_no: str
    state: str
    vpuid: str
    run_label: str
    gage_channel: str
    cal_period: str
    ver_period: str
    cal_iter: str
    calval_scenario: str
    morris_scenario: str
    cal_settings_row: str
    metrics_rows: tuple[tuple, ...]
    out_hydro: Path
    out_hydro_meta: Path
    morris_spider_top_n: int


MORRIS_SPIDER_COMBINED = REPO_ROOT / "publication/figures/final/fig-morris-spider-controlled-basins.png"
MORRIS_SPIDER_COMBINED_META = REPO_ROOT / "publication/figures/final/fig-morris-spider-controlled-basins-metadata.json"
SENS_ENSEMBLE_COMBINED_DAILY = REPO_ROOT / "publication/figures/final/fig-sensitivity-ensemble-controlled-basins-daily.png"
SENS_ENSEMBLE_COMBINED_DAILY_META = REPO_ROOT / "publication/figures/final/fig-sensitivity-ensemble-controlled-basins-daily-metadata.json"
SENS_ENSEMBLE_COMBINED_MONTHLY = REPO_ROOT / "publication/figures/supplement/fig-sensitivity-ensemble-controlled-basins-monthly.png"


def _art_root(b: BasinExport) -> Path:
    return (
        USER_ROOT
        / f"admin/SWATplus_by_VPUID/{b.vpuid}/huc12/{b.site_no}/calibration_artifacts/{b.calval_scenario}"
    )


def _morris_art_root(b: BasinExport) -> Path:
    return (
        USER_ROOT
        / f"admin/SWATplus_by_VPUID/{b.vpuid}/huc12/{b.site_no}/calibration_artifacts/{b.morris_scenario}"
    )


def _fig_sf(b: BasinExport) -> Path:
    return _art_root(b) / "figures_SWAT_MODEL_Web_Application/SF"


def _daily_hydro_png(daily_dir: Path, channel: str) -> Path:
    exact = daily_dir / f"{channel}_daily.png"
    if exact.is_file():
        return exact
    matches = sorted(daily_dir.glob(f"{channel}*_daily.png"))
    if matches:
        return matches[-1]
    raise FileNotFoundError(daily_dir)


def _hydro_sources(b: BasinExport) -> dict[str, Path]:
    ch = b.gage_channel
    sf = _fig_sf(b)
    return {
        "initialization_pool_best": _daily_hydro_png(sf / "calibration/init/daily", ch),
        "calibration_global_best": _daily_hydro_png(sf / f"calibration/{b.cal_iter}/daily", ch),
        "verification_global_best": sf / "verification/VerificationEnsemble_daily.png",
    }


CALVAL_SCENARIO = "Default_calval_split202606"
MORRIS_SCENARIO = "Default_initialized"

BASINS: tuple[BasinExport, ...] = (
    BasinExport(
        model_id="0310/huc12/02297600",
        site_no="02297600",
        state="FL",
        vpuid="0310",
        run_label="controlled_eval_02297600_split20260601",
        gage_channel="2",
        cal_period="2013-01-01 to 2018-12-31",
        ver_period="2019-01-01 to 2024-12-31",
        cal_iter="iter_0026",
        calval_scenario=CALVAL_SCENARIO,
        morris_scenario=MORRIS_SCENARIO,
        cal_settings_row=(
            "0310/huc12/02297600,02297600,controlled_eval_02297600_split20260601,10,6,36,70,"
            '"SWAT nyskip=3 after START_YEAR=2010","Scored 2013-01-01 to 2018-12-31",'
            '"Scored 2019-01-01 to 2024-12-31 (Ver 2019-2024 nyskip=0)",'
            '"Minimize negative (daily_NSE + monthly_NSE) sum",'
            '"NSE daily+monthly; Morris subset cal_parms; Morris 1000 evals on Default_initialized",'
            "bin/cal_parms_SWAT_MODEL_Web_Application.cal,"
            '"CentralPerformance; figures_* under Default_calval_split202606",completed,'
            '"Default_calval_split202606 cal+ver 2026-06-01; independent 2019-2024 verification."'
        ),
        metrics_rows=(
            ("HM-01", "initialization_pool_best", "Daily", "2", 0.795, 0.680, 28.127, 79.989, 103.906),
            ("HM-02", "initialization_pool_best", "Monthly", "2", 0.843, 0.713, 28.127, 1566.927, 75.263),
            ("HM-03", "calibration_global_best", "Daily", "2", 0.837, 0.816, 9.791, 71.445, 62.743),
            ("HM-04", "calibration_global_best", "Monthly", "2", 0.897, 0.886, 9.791, 1269.113, 44.037),
            ("HM-05", "verification_global_best", "Daily", "2", 0.729, 0.747, 7.480, 64.813, 69.784),
            ("HM-06", "verification_global_best", "Monthly", "2", 0.798, 0.817, 7.480, 1306.850, 56.319),
        ),
        out_hydro=REPO_ROOT / "publication/figures/final/fig-cal-val-02297600-hydrographs-3panel.png",
        out_hydro_meta=REPO_ROOT / "publication/figures/final/fig-cal-val-02297600-hydrographs-metadata.json",
        morris_spider_top_n=8,
    ),
    BasinExport(
        model_id="0712/huc12/05536265",
        site_no="05536265",
        state="IL",
        vpuid="0712",
        run_label="controlled_eval_05536265_split20260601",
        gage_channel="25",
        cal_period="2020-01-01 to 2024-12-31",
        ver_period="2012-01-01 to 2015-12-31",
        cal_iter="iter_0026",
        calval_scenario=CALVAL_SCENARIO,
        morris_scenario=MORRIS_SCENARIO,
        cal_settings_row=(
            "0712/huc12/05536265,05536265,controlled_eval_05536265_split20260601,10,6,48,50,"
            '"SWAT nyskip=2 after START_YEAR=2018","Scored 2020-01-01 to 2024-12-31",'
            '"Scored 2012-01-01 to 2015-12-31 (Ver 2011-2015 nyskip=1)",'
            '"Minimize negative (daily_NSE + monthly_NSE) sum",'
            '"NSE daily+monthly; Morris subset cal_parms; Morris 1000 evals on Default_initialized",'
            "bin/cal_parms_SWAT_MODEL_Web_Application.cal,"
            '"CentralPerformance; figures_* under Default_calval_split202606",completed,'
            '"Default_calval_split202606 cal+ver 2026-06-01; pre-calibration 2012-2015 verification."'
        ),
        metrics_rows=(
            ("HM-07", "initialization_pool_best", "Daily", "25", 0.202, 0.605, 2.856, 12.093, 580.906),
            ("HM-08", "initialization_pool_best", "Monthly", "25", 0.405, 0.610, 2.856, 154.894, 51.674),
            ("HM-09", "calibration_global_best", "Daily", "25", 0.371, 0.548, -7.201, 10.737, 829.705),
            ("HM-10", "calibration_global_best", "Monthly", "25", 0.600, 0.792, -7.201, 126.904, 50.307),
            ("HM-11", "verification_global_best", "Daily", "25", 0.223, 0.442, -21.581, 12.499, 311.362),
            ("HM-12", "verification_global_best", "Monthly", "25", 0.416, 0.659, -21.581, 147.032, 61.500),
        ),
        out_hydro=REPO_ROOT / "publication/figures/final/fig-cal-val-05536265-hydrographs-3panel.png",
        out_hydro_meta=REPO_ROOT / "publication/figures/final/fig-cal-val-05536265-hydrographs-metadata.json",
        morris_spider_top_n=6,
    ),
)


def _metrics_dict(b: BasinExport) -> list[dict[str, str]]:
    rows = []
    for row in b.metrics_rows:
        rid, stage, step, st, nse, kge, pb, rmse, mpe = row
        period = b.cal_period if stage != "verification_global_best" else b.ver_period
        rows.append({
            "row_id": rid,
            "model_id": b.model_id,
            "site_no": b.site_no,
            "state": b.state,
            "run_label": b.run_label,
            "workflow_stage": stage,
            "scored_period": period,
            "time_step": step,
            "station_id": st,
            "nse": f"{nse:.3f}",
            "kge": f"{kge:.3f}",
            "pbias_pct": f"{pb:.3f}",
            "rmse": f"{rmse:.3f}",
            "rmse_units": "cfs",
            "mpe_pct": f"{mpe:.3f}",
            "status": "frozen_from_central_performance",
            "notes": f"CentralPerformance.txt; scenario {b.calval_scenario}; {b.run_label}",
        })
    return rows


def _write_tab_metrics() -> None:
    rows: list[dict[str, str]] = []
    for b in BASINS:
        rows.extend(_metrics_dict(b))
    with TAB_METRICS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=METRICS_HEADER)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {TAB_METRICS} ({len(rows)} rows)")


def _append_morris_for_basin(b: BasinExport, existing: list[dict[str, str]]) -> list[dict[str, str]]:
    src = _morris_art_root(b) / "sensitivity/morris_Si_SWAT_MODEL_Web_Application.csv"
    if not src.is_file():
        print(f"Skip Morris for {b.site_no}: missing {src}")
        return existing
    ranked = list(csv.DictReader(src.open(newline="", encoding="utf-8")))
    ranked.sort(key=lambda r: -float(r["mu_star"]))
    start = len(existing) + 1
    for i, row in enumerate(ranked, start=start):
        existing.append({
            "rank": str(i),
            "model_id": b.model_id,
            "site_no": b.site_no,
            "run_label": b.run_label,
            "parameter": row["names"],
            "mu": row["mu"],
            "mu_star": row["mu_star"],
            "sigma": row["sigma"],
            "mu_star_conf": row["mu_star_conf"],
            "status": "frozen_from_morris_si_csv",
        })
    print(f"Appended Morris for {b.site_no} ({len(ranked)} params)")
    return existing


def _write_tab_morris() -> None:
    rows: list[dict[str, str]] = []
    for b in BASINS:
        rows = _append_morris_for_basin(b, rows)
    with TAB_MORRIS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MORRIS_HEADER)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {TAB_MORRIS} ({len(rows)} rows)")


def _write_tab_runtime_benchmark() -> None:
    catalog = json.loads(CATALOG_JSON.read_text(encoding="utf-8"))
    scenario = next(s for s in catalog["scenarios"] if s["id"] == "outputFiltering")
    header = [
        "row_id", "tier", "model_id", "label", "hrus", "channels", "scenario_id", "print_profile",
        "output_format", "sim_window_days", "sim_year", "wall_s", "sec_per_day", "peak_rss_kb",
        "binary", "catalog_generated_at", "status", "notes",
    ]
    rows = []
    for i, res in enumerate(scenario["results"], start=1):
        nc = res["filteredNc"]
        rows.append({
            "row_id": f"RB-{i:02d}",
            "tier": res["tier"],
            "model_id": res["modelId"],
            "label": res["label"],
            "hrus": str(res["hrus"]),
            "channels": str(res.get("channels", "")),
            "scenario_id": "outputFiltering",
            "print_profile": "filtered_daily_channel_sd_gauges",
            "output_format": "NetCDF",
            "sim_window_days": str(catalog.get("simWindowDays", 365)),
            "sim_year": str(catalog.get("simYear", 2021)),
            "wall_s": str(nc["wallS"]),
            "sec_per_day": str(nc["secPerDay"]),
            "peak_rss_kb": str(nc.get("rssKb", "")),
            "binary": catalog["methodology"]["binary"],
            "catalog_generated_at": catalog.get("generatedAt", ""),
            "status": "frozen_from_runtime_benchmark_catalog",
            "notes": "Calibration-style print_filter profile; see /swat-plus-runtime-benchmark",
        })
    with TAB_RUNTIME_BENCH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {TAB_RUNTIME_BENCH} ({len(rows)} rows)")


def _upsert_cal_settings_rows() -> None:
    """Replace controlled-gage rows for 02297600 / 05536265 with split202606 run settings."""
    keep_labels = {b.run_label for b in BASINS}
    lines = TAB_CAL_SETTINGS.read_text(encoding="utf-8").splitlines()
    header, body = lines[0], lines[1:]
    filtered = [
        row for row in body
        if row.strip() and row.split(",")[1] not in ("02297600", "05536265")
    ]
    filtered.extend(b.cal_settings_row for b in BASINS)
    TAB_CAL_SETTINGS.write_text(header + "\n" + "\n".join(filtered) + "\n", encoding="utf-8")
    print(f"Updated {TAB_CAL_SETTINGS} for sites 02297600, 05536265 ({', '.join(sorted(keep_labels))})")


def _assemble_hydrographs(b: BasinExport) -> None:
    from render_calval_hydrographs import render_basin

    render_basin(b)


def _site_root(b: BasinExport) -> Path:
    return USER_ROOT / EXAMPLE_USER / f"SWATplus_by_VPUID/{b.vpuid}/huc12/{b.site_no}"


def _write_tab_sensitivity_ensemble_metrics() -> None:
    import sys

    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from morris_ensemble_metrics import compute_ensemble_metrics

    header = [
        "row_id", "model_id", "site_no", "state", "run_label", "frequency",
        "n_morris_members", "morris_best_member_index", "p_factor", "r_factor", "best_nse", "status",
    ]
    rows: list[dict[str, str]] = []
    rid = 0
    for b in BASINS:
        root = _site_root(b)
        for freq, monthly in (("Daily", False), ("Monthly", True)):
            rid += 1
            m = compute_ensemble_metrics(root, b.gage_channel, monthly=monthly)
            rows.append({
                "row_id": f"SE-{rid:02d}",
                "model_id": b.model_id,
                "site_no": b.site_no,
                "state": b.state,
                "run_label": b.run_label,
                "frequency": freq,
                "n_morris_members": str(m["n_morris_members"]),
                "morris_best_member_index": str(m["morris_best_member_index"]),
                "p_factor": f"{m['p_factor']:.4f}",
                "r_factor": f"{m['r_factor']:.4f}",
                "best_nse": f"{m['best_nse']:.4f}" if m["best_nse"] is not None else "",
                "status": "frozen_from_morris_ensemble_npz",
            })
    with TAB_ENSEMBLE_METRICS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {TAB_ENSEMBLE_METRICS} ({len(rows)} rows)")


def _ensemble_figure_src(b: BasinExport, frequency: str) -> Path:
    name = "SensitivityEnsemble_monthly.png" if frequency == "monthly" else "SensitivityEnsemble_daily.png"
    return _morris_art_root(b) / "figures_SWAT_MODEL_Web_Application/SF/sensitivity" / name


def _export_sensitivity_ensemble_figures() -> None:
    from render_sensitivity_ensemble_figures import render_all

    render_all()


def _render_morris_spider_figure() -> None:
    import sys

    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from plot_morris_spider import plot_morris_spider_dual

    top_n = {b.site_no: b.morris_spider_top_n for b in BASINS}
    plot_morris_spider_dual(TAB_MORRIS, MORRIS_SPIDER_COMBINED, top_n_by_site=top_n)
    meta = {
        "figure_id": "Fig-MorrisSpider-ControlledBasins",
        "chart_type": "spider_radar",
        "top_n_by_site": top_n,
        "source_csv": str(TAB_MORRIS),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    MORRIS_SPIDER_COMBINED_META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MORRIS_SPIDER_COMBINED}")


def main() -> None:
    _write_tab_metrics()
    _write_tab_morris()
    _write_tab_sensitivity_ensemble_metrics()
    _write_tab_runtime_benchmark()
    _upsert_cal_settings_rows()
    for b in BASINS:
        _assemble_hydrographs(b)
    _export_sensitivity_ensemble_figures()
    _render_morris_spider_figure()


if __name__ == "__main__":
    main()

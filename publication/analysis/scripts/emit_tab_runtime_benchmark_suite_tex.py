#!/usr/bin/env python3
"""Emit LaTeX fragments for Objective 5 benchmark tables."""
from __future__ import annotations

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TABLES = REPO_ROOT / "publication/tables"
OUT = REPO_ROOT / "publication/tables/generated"


def _read(name: str) -> list[dict]:
    with (TABLES / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write(name: str, lines: list[str]) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def _tabular_star(col_spec: str, header: str, body: list[str]) -> list[str]:
    """Full \\textwidth tabular* — consistent font size across tables (no resizebox scaling)."""
    return [
        rf"\begin{{tabular*}}{{\textwidth}}{{@{{\extracolsep{{\fill}}}}{col_spec}@{{}}}}",
        r"\toprule",
        header + r" \\",
        r"\midrule",
        *body,
        r"\bottomrule",
        r"\end{tabular*}",
    ]


def emit_primary() -> None:
    rows = _read("tab-runtime-benchmark.csv")
    body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {r['hrus']} & "
        f"{r['wall_s']} & {r['sec_per_day']} & {r['peak_rss_kb']} \\\\"
        for r in rows
    ]
    _write(
        "tab-runtime-benchmark.tex",
        _tabular_star(
            "llrrrr",
            r"Size class & Model & HRUs & Wall (s) & s/day & Peak RSS (KB)",
            body,
        ),
    )


def emit_print_scope() -> None:
    rows = _read("tab-runtime-benchmark-print-scope.csv")
    scope = {"full_export": "Full export", "calibration_filtered": "Calibration filtered"}
    body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {scope[r['print_scope']]} & "
        f"{r['wall_s']} & {r['sec_per_day']} & {r['channel_sd_mb']} \\\\"
        for r in rows
    ]
    _write(
        "tab-runtime-benchmark-print-scope.tex",
        _tabular_star(
            "lllrrr",
            r"Size class & Model & Print scope & Wall (s) & s/day & channel\_sd (MB)",
            body,
        ),
    )


def emit_nc_vs_txt() -> None:
    rows = _read("tab-runtime-benchmark-nc-vs-txt.csv")
    body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {r['output_format']} & "
        f"{r['wall_s']} & {r['sec_per_day']} & {r['total_output_gb']} \\\\"
        for r in rows
    ]
    _write(
        "tab-runtime-benchmark-nc-vs-txt.tex",
        _tabular_star(
            "lllrrr",
            r"Size class & Model & Format & Wall (s) & s/day & Total output (GB)",
            body,
        ),
    )


def emit_compiler() -> None:
    rows = _read("tab-runtime-benchmark-compiler.csv")
    prod = [r for r in rows if r.get("production") == "yes"]
    prod_body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {r['label']} & {r['wall_s']} & {r['sec_per_day']} \\\\"
        for r in prod
    ]
    _write(
        "tab-runtime-benchmark-compiler-prod.tex",
        _tabular_star(
            "lllrr",
            r"Size class & Model & Build & Wall (s) & s/day",
            prod_body,
        ),
    )

    full_body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {r['label']} & "
        f"{r['wall_s']} & {r['sec_per_day']} & {r['vs_ref_pct']} & "
        f"{'yes' if r.get('production') == 'yes' else ''} \\\\"
        for r in rows
    ]
    _write(
        "tab-runtime-benchmark-compiler-full.tex",
        _tabular_star(
            "lllrrrl",
            r"Size class & Model & Build & Wall (s) & s/day & vs ref (\%) & Prod.",
            full_body,
        ),
    )


def emit_vtune() -> None:
    rows = _read("tab-runtime-benchmark-vtune.csv")
    body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {r['sim_window_days']} & "
        f"{r['hru_control_pct_daily']} & {r['channel_pct_daily']} & {r['strcmp_pct_daily']} & "
        f"{r['memset_pct_daily']} & {r['init_pct']} \\\\"
        for r in rows
    ]
    _write(
        "tab-runtime-benchmark-vtune.tex",
        _tabular_star(
            "llrrrrrr",
            r"Tier & Model & Days & HRU (\%) & Channel (\%) & strcmp (\%) & memset (\%) & Init (\%)",
            body,
        ),
    )


def emit_hru_scaling() -> None:
    rows = _read("tab-runtime-benchmark-hru-scaling.csv")
    body = [
        f"{r['tier']} & \\texttt{{{r['model_id']}}} & {r['hrus']} & {r['channels']} & "
        f"{r['wall_s']} & {r['sec_per_day']} & {r['init_s']} \\\\"
        for r in rows
    ]
    _write(
        "tab-runtime-benchmark-hru-scaling.tex",
        _tabular_star(
            "lllrrrr",
            r"Size class & Model & HRUs & Channels & Wall (s) & s/day & Init (s)",
            body,
        ),
    )


def main() -> None:
    emit_primary()
    emit_print_scope()
    emit_nc_vs_txt()
    emit_compiler()
    emit_vtune()
    emit_hru_scaling()


if __name__ == "__main__":
    main()

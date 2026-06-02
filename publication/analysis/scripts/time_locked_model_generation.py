#!/usr/bin/env python3
"""
Pilot timing for one **inventory-locked** evaluation basin (see
``publication/tables/tab-model-complexity.csv``, ``status=locked_from_inventory``).
Default ``--model-id`` is the Small basin; pass another locked ``vpuid/huc12/site_no``
for Medium or Large. Use ``--rm-site-output`` to delete that site’s existing
``SWATplus_by_VPUID/...`` tree before generation.

Runs SWATGenX model creation with phase-resolved JSONL timing enabled, then
appends flattened rows to a runtime phases CSV (see body) and writes a Markdown
summary. See publication/analysis/runtime-protocol.md.

Environment (typical):
  USER_PATH, EXAMPLE_MODELS_USERNAME, SWAT_SHOWCASE_MODEL_DIR

The process user must be able to write national data caches under
``GenXAppData/`` (NHDPlus HR ``zipped/`` and ``unzipped_*``, gSSURGO VPU
folders, etc.). If another user started a download, fix ownership on those paths
or run as that user.

JSONL and summary default to ``publication/analysis/runtime-runs/`` in the repo;
``sudo -u www-data`` often cannot write there. Use ``--runtime-runs-dir`` (or env
``SWATGENX_RUNTIME_RUNS_DIR``) pointing to a writable directory, for example
``/tmp/swx-runtime-runs``. When that path differs from the default, flattened CSV
rows default to ``<runtime-runs-dir>/tab-runtime-phases-append.csv`` unless you
set ``--runtime-phases-csv``, ``SWATGENX_RUNTIME_PHASES_CSV``, or ``--skip-csv-append``.
``--force`` requires permission to remove prior files for the same ``--run-id`` in
the runs directory.

Usage (from repo root):
  python3 publication/analysis/scripts/time_locked_model_generation.py \\
    --model-id 0308/huc12/02239501 --run-id 20260514-small-pilot-001

Service user (JSONL + CSV under ``/tmp``, optional fresh site tree):

  python3 publication/analysis/scripts/time_locked_model_generation.py \\
    --runtime-runs-dir /tmp/swx-runtime-runs \\
    --model-id 0204/huc12/01451800 --run-id 20260514-medium-pilot-001 \\
    --rm-site-output --force
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_DEFAULT = REPO_ROOT / "publication" / "tables" / "tab-model-complexity.csv"
RUNTIME_CSV = REPO_ROOT / "publication" / "tables" / "tab-runtime-phases.csv"
RUNS_DIR = REPO_ROOT / "publication" / "analysis" / "runtime-runs"

DEFAULT_USER_PATH = "${SWATGENX_USER_PATH}"
DEFAULT_USERNAME = "admin"
DEFAULT_MODEL_DIR = "SWAT_MODEL_Web_Application"
DEFAULT_MODEL_ID = "0308/huc12/02239501"
DEFAULT_RUN_ID = "20260514-small-pilot-001"


def _swat_site_dir(user_path: Path, username: str, vpuid: str, level: str, site_no: str) -> Path:
    return user_path.expanduser().resolve() / username / "SWATplus_by_VPUID" / vpuid / level / site_no


def _clear_prior_run_artifacts(jsonl_path: Path, summary_path: Path) -> int | None:
    """
    Remove prior JSONL/summary for this run_id. Return 1 if removal fails (e.g.
    wrong file owner when switching between login user and www-data).
    """
    for pth in (jsonl_path, summary_path):
        if not pth.is_file():
            continue
        try:
            pth.unlink()
        except PermissionError:
            print(
                f"ERROR: Cannot remove {pth} (permission denied).\n"
                "It was probably created by another OS user. Choose one:\n"
                f"  sudo rm -f {shlex.quote(str(pth))}\n"
                "  — or run this script as that same user — or use a new --run-id without --force.",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(f"ERROR: Cannot remove {pth}: {exc}", file=sys.stderr)
            return 1
    return None


def _runs_dir_from_cli(cli_dir: Path | None) -> Path:
    if cli_dir is not None:
        return cli_dir.expanduser().resolve()
    env = (os.environ.get("SWATGENX_RUNTIME_RUNS_DIR") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return RUNS_DIR.resolve()


def _require_writable_runs_dir(runs_dir: Path) -> int | None:
    runs_dir.mkdir(parents=True, exist_ok=True)
    probe = runs_dir / f".swx_runtime_write_probe_{os.getpid()}"
    try:
        probe.write_text("ok", encoding="utf-8")
    except OSError as exc:
        print(
            f"ERROR: cannot write runtime logs under {runs_dir} ({exc}).\n"
            "Fix directory permissions, run as a user that owns this path, or pass\n"
            "  --runtime-runs-dir /path/to/writable/dir\n"
            "(or set SWATGENX_RUNTIME_RUNS_DIR).",
            file=sys.stderr,
        )
        return 1
    probe.unlink(missing_ok=True)
    return None


def _display_path(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(p.resolve())


def _runtime_phases_csv_target(args: argparse.Namespace, runs_dir: Path) -> Path | None:
    if args.skip_csv_append:
        return None
    if args.runtime_phases_csv is not None:
        return args.runtime_phases_csv.expanduser().resolve()
    env = (os.environ.get("SWATGENX_RUNTIME_PHASES_CSV") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    if runs_dir.resolve() != RUNS_DIR.resolve():
        return (runs_dir / "tab-runtime-phases-append.csv").resolve()
    return RUNTIME_CSV.resolve()


def _require_writable_csv_parent(csv_path: Path) -> int | None:
    parent = csv_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    probe = parent / f".swx_runtime_csv_probe_{os.getpid()}"
    try:
        probe.write_text("ok", encoding="utf-8")
    except OSError as exc:
        print(
            f"ERROR: cannot write runtime phases CSV under {parent} ({exc}).\n"
            "Pass --runtime-phases-csv /path/writable/tab-runtime-phases-append.csv\n"
            "or --skip-csv-append and merge JSONL into the table later.",
            file=sys.stderr,
        )
        return 1
    probe.unlink(missing_ok=True)
    return None


def _parse_model_id(model_id: str) -> tuple[str, str, str]:
    parts = str(model_id).strip().split("/")
    if len(parts) != 3:
        raise ValueError(f"model_id must be vpuid/level/site_no, got {model_id!r}")
    return parts[0], parts[1], parts[2]


def _load_row(csv_path: Path, model_id: str) -> dict[str, str]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row.get("model_id") or "").strip() != model_id:
                continue
            status = (row.get("status") or "").strip()
            if not status.startswith("locked_"):
                continue
            return dict(row)
    raise SystemExit(f"No locked row with model_id={model_id!r} in {csv_path}")


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def _ram_gb_linux() -> str:
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return f"{kb / (1024 * 1024):.2f}"
    except Exception:
        pass
    return ""


def _append_runtime_csv(
    csv_path: Path,
    *,
    rows: list[dict[str, object]],
    git_sha: str,
    environment_id: str,
    hostname: str,
    cpu_count: str,
    ram_gb: str,
    storage_mode: str,
    cache_state: str,
    model_id: str,
    tier: str,
    run_id: str,
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not csv_path.is_file() or csv_path.stat().st_size == 0
    fieldnames = [
        "model_id",
        "tier",
        "run_id",
        "git_sha",
        "environment_id",
        "hostname",
        "cpu_count",
        "ram_gb",
        "storage_mode",
        "cache_state",
        "phase_name",
        "phase_group",
        "include_in_processing_total",
        "elapsed_seconds",
        "start_utc",
        "end_utc",
        "status",
        "notes",
    ]
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        if write_header:
            w.writeheader()
        for rec in rows:
            w.writerow(
                {
                    "model_id": model_id,
                    "tier": tier,
                    "run_id": run_id,
                    "git_sha": git_sha,
                    "environment_id": environment_id,
                    "hostname": hostname,
                    "cpu_count": cpu_count,
                    "ram_gb": ram_gb,
                    "storage_mode": storage_mode,
                    "cache_state": cache_state,
                    "phase_name": rec.get("phase_name", ""),
                    "phase_group": rec.get("phase_group", ""),
                    "include_in_processing_total": "Y"
                    if rec.get("include_in_processing_total")
                    else "N",
                    "elapsed_seconds": rec.get("elapsed_seconds", ""),
                    "start_utc": rec.get("start_utc", ""),
                    "end_utc": rec.get("end_utc", ""),
                    "status": rec.get("status", ""),
                    "notes": (rec.get("notes") or "").replace("\n", " ")[:2000],
                }
            )


def _write_summary(
    path: Path,
    *,
    model_id: str,
    tier: str,
    state: str,
    area: str,
    run_id: str,
    git_sha: str,
    hostname: str,
    cpu_count: str,
    ram_gb: str,
    storage_mode: str,
    cache_state: str,
    phases: list[dict[str, object]],
    core_total: float,
    external_total: float,
) -> None:
    lines = [
        f"# Runtime pilot summary: `{run_id}`",
        "",
        "## Basin",
        "",
        f"- **model_id:** `{model_id}`",
        f"- **tier:** {tier}",
        f"- **state:** {state}",
        f"- **area_km2 (CSV):** {area}",
        "",
        "## Environment",
        "",
        f"- **hostname:** `{hostname}`",
        f"- **cpu_count:** {cpu_count}",
        f"- **ram_gb (approx):** {ram_gb or 'unknown'}",
        f"- **git_sha:** `{git_sha or 'unknown'}`",
        f"- **storage_mode:** {storage_mode}",
        f"- **cache_state:** {cache_state}",
        "",
        "## Per-phase (JSONL merge)",
        "",
        "| phase_name | phase_group | include_core | elapsed_s | status |",
        "|------------|-------------|-------------|----------|--------|",
    ]
    for p in phases:
        inc = "Y" if p.get("include_in_processing_total") else "N"
        lines.append(
            f"| {p.get('phase_name', '')} | {p.get('phase_group', '')} | {inc} | "
            f"{p.get('elapsed_seconds', '')} | {p.get('status', '')} |"
        )
    lines.extend(
        [
            "",
            "## Aggregates (pilot definitions)",
            "",
            f"- **core_processing_time (sum include=Y):** {core_total:.3f} s",
            f"- **external_acquisition_time (sum phase_group=external_acquisition):** {external_total:.3f} s",
            "",
            "## Known limitations",
            "",
            "- Timings are single-host, single-run, and not comparable across tools or deployments.",
            "- `check_configuration` CRS validation is not separately timed from VPU geospatial auto-build sub-phases.",
            "- ZIP packaging for download is not part of this core pipeline hook set (`packaging_zip_report` omitted).",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--csv", type=Path, default=CSV_DEFAULT)
    p.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    p.add_argument("--run-id", default=DEFAULT_RUN_ID)
    p.add_argument(
        "--user-path",
        type=Path,
        default=Path(os.environ.get("USER_PATH", DEFAULT_USER_PATH)).expanduser(),
    )
    p.add_argument(
        "--username",
        default=(os.environ.get("EXAMPLE_MODELS_USERNAME") or DEFAULT_USERNAME).strip() or DEFAULT_USERNAME,
    )
    p.add_argument(
        "--model-dir",
        default=(os.environ.get("SWAT_SHOWCASE_MODEL_DIR") or DEFAULT_MODEL_DIR).strip() or DEFAULT_MODEL_DIR,
    )
    p.add_argument("--ls-resolution", default="250", help="Land/soil grid resolution (default 250)")
    p.add_argument(
        "--storage-mode",
        default="unknown",
        choices=("low_storage_on_demand", "local_cache", "full_local_mirror", "unknown"),
    )
    p.add_argument(
        "--cache-state",
        default="unknown",
        choices=("cold_external", "warm_local", "mixed", "unknown"),
    )
    p.add_argument("--force", action="store_true", help="Remove existing JSONL/summary for this run_id before starting")
    p.add_argument(
        "--rm-site-output",
        action="store_true",
        help="Delete USER_PATH/username/SWATplus_by_VPUID/<vpuid>/huc12/<site> before model generation (fresh SWAT+ tree)",
    )
    p.add_argument(
        "--runtime-runs-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Writable directory for JSONL and summary (default: publication/analysis/runtime-runs "
            "or SWATGENX_RUNTIME_RUNS_DIR). If this is not the default directory, CSV append defaults "
            "to <DIR>/tab-runtime-phases-append.csv unless overridden."
        ),
    )
    p.add_argument(
        "--runtime-phases-csv",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Append flattened rows here (default: publication/tables/tab-runtime-phases.csv, "
            "or <runtime-runs-dir>/tab-runtime-phases-append.csv when runs dir is custom, "
            "or SWATGENX_RUNTIME_PHASES_CSV)"
        ),
    )
    p.add_argument(
        "--skip-csv-append",
        action="store_true",
        help="Only write JSONL + summary; merge into tab-runtime-phases.csv later (for service users without repo write)",
    )
    args = p.parse_args(argv)

    if args.skip_csv_append and args.runtime_phases_csv is not None:
        print("ERROR: use either --skip-csv-append or --runtime-phases-csv, not both", file=sys.stderr)
        return 1

    csv_path = args.csv.resolve()
    row = _load_row(csv_path, args.model_id.strip())
    tier = (row.get("tier") or "").strip()
    state = (row.get("state") or "").strip()
    area = (row.get("area_km2") or "").strip()
    dem_raw = (row.get("dem_resolution_m") or "30").strip()
    try:
        dem_res = str(int(round(float(dem_raw))))
    except ValueError:
        dem_res = "30"

    vpuid, level, station_key = _parse_model_id(args.model_id.strip())
    if level not in {"huc12", "huc8"}:
        print(f"ERROR: pilot supports huc12 or huc8 model_id, got level={level!r}", file=sys.stderr)
        return 1

    site_dir = _swat_site_dir(args.user_path, args.username, vpuid, level, station_key)
    if args.rm_site_output:
        if site_dir.is_dir():
            try:
                shutil.rmtree(site_dir)
            except OSError as exc:
                print(
                    f"ERROR: could not remove {site_dir}: {exc}\n"
                    "Fix permissions or run as the user that owns this path.",
                    file=sys.stderr,
                )
                return 1
            print(f"Removed existing site directory: {site_dir}", flush=True)
        elif site_dir.exists():
            print(f"ERROR: {site_dir} exists but is not a directory; refusing to delete", file=sys.stderr)
            return 1

    runs_dir = _runs_dir_from_cli(args.runtime_runs_dir)
    rc_w = _require_writable_runs_dir(runs_dir)
    if rc_w:
        return rc_w

    jsonl_path = runs_dir / f"{args.run_id}.jsonl"
    summary_path = runs_dir / f"{args.run_id}-summary.md"
    if jsonl_path.exists() and not args.force:
        print(f"ERROR: {jsonl_path} exists (pass --force to replace)", file=sys.stderr)
        return 1
    if args.force:
        rc = _clear_prior_run_artifacts(jsonl_path, summary_path)
        if rc:
            return rc

    phases_csv = _runtime_phases_csv_target(args, runs_dir)
    if phases_csv is not None:
        rc_csvp = _require_writable_csv_parent(phases_csv)
        if rc_csvp:
            return rc_csvp

    os.environ["SWATGENX_RUNTIME_PROFILE"] = "1"
    os.environ["SWATGENX_RUNTIME_JSONL"] = str(jsonl_path.resolve())
    os.environ["SWATGENX_RUNTIME_RUN_ID"] = args.run_id
    os.environ["SWATGENX_RUNTIME_MODEL_ID"] = args.model_id.strip()
    os.environ["SWATGENX_RUNTIME_TIER"] = tier
    os.environ["SWATGENX_RUNTIME_STATE"] = state
    os.environ.setdefault("USER_PATH", str(args.user_path))
    os.environ.setdefault("EXAMPLE_MODELS_USERNAME", args.username)

    sys.path.insert(0, str(REPO_ROOT / "SWATGenX"))
    from SWATGenXCommand import SWATGenXCommand
    from SWATGenXConfigPars import SWATGenXPaths

    station_usgs = station_key
    config = {
        "VPUID": vpuid,
        "LEVEL": level,
        "MAX_AREA": 5000,
        "MIN_AREA": 10,
        "GAP_percent": 10,
        "landuse_product": "NLCD",
        "landuse_epoch": "2021",
        "ls_resolution": args.ls_resolution,
        "dem_resolution": dem_res,
        "station_name": station_usgs,
        "MODEL_NAME": SWATGenXPaths.SWAT_MODEL_NAME,
        "single_model": True,
        "START_YEAR": 2015,
        "END_YEAR": 2022,
        "nyskip": 3,
        "pet": 2,
        "cn": 1,
        "no_value": 1e6,
        "username": args.username,
        "force_rebuild": False,
    }

    git_sha = _git_sha()
    hostname = socket.gethostname()
    cpu_count = str(os.cpu_count() or "")
    ram_gb = _ram_gb_linux()
    environment_id = (os.environ.get("SWATGENX_RUNTIME_ENVIRONMENT_ID") or "").strip()

    print(
        f"Starting pilot run_id={args.run_id} model_id={args.model_id} runtime_runs_dir={runs_dir}",
        flush=True,
    )
    try:
        cmd = SWATGenXCommand(config)
        out = cmd.execute()
    except BaseException as exc:
        print(f"ERROR: model creation failed: {exc}", file=sys.stderr)
        return 1

    if not out:
        print("ERROR: SWATGenXCommand returned empty path", file=sys.stderr)
        return 1

    if not jsonl_path.is_file():
        print("ERROR: expected JSONL log missing after run", file=sys.stderr)
        return 1

    phases: list[dict[str, object]] = []
    with jsonl_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            phases.append(json.loads(line))

    if not phases:
        print("ERROR: JSONL contained no phase rows", file=sys.stderr)
        return 1
    if any(p.get("status") != "ok" for p in phases):
        print("ERROR: one or more phases reported non-ok status; not appending CSV", file=sys.stderr)
        return 1

    core_total = sum(
        float(p.get("elapsed_seconds") or 0)
        for p in phases
        if p.get("include_in_processing_total") is True
    )
    external_total = sum(
        float(p.get("elapsed_seconds") or 0)
        for p in phases
        if (p.get("phase_group") or "") == "external_acquisition"
    )

    if phases_csv is not None:
        try:
            _append_runtime_csv(
                phases_csv,
                rows=phases,
                git_sha=git_sha,
                environment_id=environment_id,
                hostname=hostname,
                cpu_count=cpu_count,
                ram_gb=ram_gb,
                storage_mode=args.storage_mode,
                cache_state=args.cache_state,
                model_id=args.model_id.strip(),
                tier=tier,
                run_id=args.run_id,
            )
        except PermissionError as exc:
            print(
                f"ERROR: cannot append runtime phases CSV ({exc}).\n"
                "Use --runtime-phases-csv /writable/path.csv or --skip-csv-append.",
                file=sys.stderr,
            )
            return 1

    _write_summary(
        summary_path,
        model_id=args.model_id.strip(),
        tier=tier,
        state=state,
        area=area,
        run_id=args.run_id,
        git_sha=git_sha,
        hostname=hostname,
        cpu_count=cpu_count,
        ram_gb=ram_gb,
        storage_mode=args.storage_mode,
        cache_state=args.cache_state,
        phases=phases,
        core_total=core_total,
        external_total=external_total,
    )

    print(f"OK: wrote {_display_path(jsonl_path)}", flush=True)
    if phases_csv is not None:
        print(f"OK: appended rows to {_display_path(phases_csv)}", flush=True)
    else:
        print(
            "OK: skipped CSV append (--skip-csv-append); merge JSONL into publication/tables/tab-runtime-phases.csv when ready",
            flush=True,
        )
    print(f"OK: wrote {_display_path(summary_path)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

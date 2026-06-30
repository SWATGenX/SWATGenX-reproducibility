#!/usr/bin/env python3
"""Generate a TauDEM-delineated SWAT+ model VARIANT in the SAME site directory as the
existing NHDPlus-HR model, differing only by project name (MODEL_NAME).

Standalone (no Flask): builds the same config dict as the web path and calls
SWATGenXCommand directly (pattern from time_locked_model_generation.py), plus the
TauDEM policy keys from web_application/app/utils.py:_apply_web_swatgenx_policy.

MUST run as www-data so it can write the admin model tree:
  sudo -n -u www-data /data/SWATGenXApp/codes/.venv/bin/python \\
    publication/analysis/scripts/run_taudem_variant_model.py \\
    --model-id 0308/huc12_outlet/030801020804 --model-name SWAT_MODEL_TauDEM_auto \\
    --stream 5000 --channel 1000 --snap 900 --ls-resolution 250 --dem-resolution 30
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--model-id", required=True, help="vpuid/level/site_no, e.g. 0308/huc12_outlet/030801020804")
    p.add_argument("--model-name", required=True, help="project folder name (sibling under the site dir)")
    p.add_argument("--delineation", choices=("taudem", "nhd"), default="taudem",
                   help="taudem = DEM threshold-only; nhd = NHDPlus-HR predefined network (TauDEM fallback)")
    p.add_argument("--username", default="admin")
    p.add_argument("--ls-resolution", default="250")
    p.add_argument("--dem-resolution", default="30")
    p.add_argument("--stream", type=int, default=5000, help="TauDEM stream-definition threshold (cells)")
    p.add_argument("--channel", type=int, default=1000, help="TauDEM channel threshold (cells)")
    p.add_argument("--snap", type=int, default=None, help="outlet snap (m); default 900 taudem / 300 nhd")
    p.add_argument("--auto-threshold", action="store_true",
                   help="let core auto-derive thresholds from HUC12 area (ignores --stream/--channel)")
    p.add_argument("--threshold-basis-res", type=float, default=None,
                   help="if set and != --dem-resolution, interpret --stream/--channel as cell counts "
                        "at THIS resolution (m) and rescale to --dem-resolution holding drainage AREA "
                        "constant: cells_target = round(cells_basis * (basis_res/target_res)^2). "
                        "E.g. --threshold-basis-res 30 --dem-resolution 250 maps s15000 -> ~216 cells")
    p.add_argument("--list-huc12s", default=None,
                   help="comma-separated HUC12s for the explorer/HUC12-keyed path; "
                        "default = [site] when the workspace site is a 12-digit HUC12")
    p.add_argument("--use-lakes", action="store_true",
                   help="TauDEM: wire the NHD-derived lakes as reservoirs (sets QSWAT_TAUDEM_USE_LAKES)")
    p.add_argument("--burn-streams", action="store_true",
                   help="TauDEM: burn the NHD stream network into the DEM before delineation (QSWAT+ checkBurn)")
    p.add_argument("--burn-flowline-types", default=None,
                   help="TauDEM selective burn: FType preset (major_rivers | rivers_artificial | all) "
                        "or comma FType codes (e.g. 460,558). Implies --burn-streams; builds a filtered "
                        "SWAT_plus_burn_streams.shp from raw NHD instead of burning the full network")
    p.add_argument("--lake-min-area", type=float, default=None,
                   help="TauDEM lake filter: minimum waterbody area (km^2) to keep as a lake "
                        "(drops small ponds; sets QSWAT_TAUDEM_LAKE_MIN_AREA_KM2)")
    p.add_argument("--lake-types", default=None,
                   help="TauDEM lake filter: FType preset (major_lakes | all) or comma FType codes "
                        "(e.g. 390,436); drops Wetlands/Playa. Sets QSWAT_TAUDEM_LAKE_TYPES")
    p.add_argument("--clip-dem", action="store_true",
                   help="clip the DEM to the basin polygon, not the bbox (SWATGENX_CLIP_DEM_TO_BOUNDARY)")
    p.add_argument("--lake-split", action="store_true",
                   help="force QSWAT+ splitChannelsByLakes instead of addHUCLakes for TauDEM+lakes")
    p.add_argument("--force-rebuild", action="store_true")
    args = p.parse_args(argv)

    parts = args.model_id.strip().split("/")
    if len(parts) != 3:
        print(f"ERROR: --model-id must be vpuid/level/site_no, got {args.model_id!r}", file=sys.stderr)
        return 2
    vpuid, level, site = parts
    force_taudem = args.delineation == "taudem"
    snap = args.snap if args.snap is not None else (900 if force_taudem else 300)

    os.environ.setdefault("USER_PATH", "${SWATGENX_USER_PATH}")
    os.environ.setdefault("EXAMPLE_MODELS_USERNAME", args.username)
    if args.clip_dem:
        os.environ["SWATGENX_CLIP_DEM_TO_BOUNDARY"] = "1"
    if args.lake_split:
        os.environ["SWATGENX_QSWAT_TAUDEM_SPLIT_CHANNELS_BY_LAKES"] = "1"
    sys.path.insert(0, str(REPO_ROOT / "SWATGenX"))
    from SWATGenXCommand import SWATGenXCommand  # noqa: E402

    config = {
        "VPUID": vpuid,
        "LEVEL": level,
        "MAX_AREA": 5000,
        "MIN_AREA": 10,
        "GAP_percent": 10,
        "landuse_product": "NLCD",
        "landuse_epoch": "2021",
        "ls_resolution": args.ls_resolution,
        "dem_resolution": args.dem_resolution,
        "station_name": site,
        "MODEL_NAME": args.model_name,
        "single_model": True,
        "START_YEAR": 2015,
        "END_YEAR": 2022,
        "nyskip": 3,
        "pet": 2,
        "cn": 1,
        "no_value": 1e6,
        "username": args.username,
        "force_rebuild": bool(args.force_rebuild),
        # --- delineation policy (mirrors _apply_web_swatgenx_policy) ---
        "MAX_REACHES": None,
        "DISSOLVE_TINY_WATERSHEDS": False,
        "QSWAT_FORCE_TAUDEM_ONLY": force_taudem,
        "QSWAT_FALLBACK_TAUDEM_DELIN": not force_taudem,
        "QSWAT_TAUDEM_OUTLET_SNAP_M": int(snap),
        "QSWAT_TAUDEM_USE_MANUAL_THRESHOLDS": not args.auto_threshold,
    }
    stream_cells, channel_cells = int(args.stream), int(args.channel)
    if (not args.auto_threshold) and args.threshold_basis_res:
        basis = float(args.threshold_basis_res)
        target = float(args.dem_resolution)
        if basis != target and target > 0:
            # Hold the channel-/stream-initiation drainage AREA constant across DEM resolution:
            # a cell at `target` m covers (target/basis)^2 as much ground as a cell at `basis` m,
            # so the equivalent cell count scales by (basis/target)^2.
            factor = (basis / target) ** 2
            stream_cells = max(1, round(stream_cells * factor))
            channel_cells = max(1, round(channel_cells * factor))
            print(f"[run_taudem_variant] threshold rescale {basis}m->{target}m factor={factor:.4f}: "
                  f"stream {args.stream}->{stream_cells}, channel {args.channel}->{channel_cells}", flush=True)
    if not args.auto_threshold:
        config["QSWAT_TAUDEM_STREAM_THRESHOLD_CELLS"] = stream_cells
        config["QSWAT_TAUDEM_CHANNEL_THRESHOLD_CELLS"] = channel_cells
    if args.use_lakes:
        config["QSWAT_TAUDEM_USE_LAKES"] = True
    if args.burn_streams or args.burn_flowline_types:
        config["QSWAT_TAUDEM_BURN_STREAMS"] = True
    if args.burn_flowline_types:
        config["QSWAT_TAUDEM_BURN_FLOWLINE_TYPES"] = args.burn_flowline_types
    if args.lake_min_area is not None:
        config["QSWAT_TAUDEM_LAKE_MIN_AREA_KM2"] = float(args.lake_min_area)
    if args.lake_types:
        config["QSWAT_TAUDEM_LAKE_TYPES"] = args.lake_types

    # HUC12-keyed workspace (explorer path): pass a preset list_of_huc12s so the command
    # uses the preset branch in handle_huc12() instead of resolving a USGS gage from
    # station_name (which fails for a HUC12 code).
    if args.list_huc12s:
        h12 = [h.strip().zfill(12) for h in args.list_huc12s.split(",") if h.strip()]
    elif level == "huc12" and site.isdigit() and len(site) == 12:
        h12 = [site]
    else:
        h12 = None
    if h12:
        config["list_of_huc12s"] = h12
        config["site_no"] = site

    import time as _time
    import json as _json
    from datetime import datetime as _dt

    print(f"[run_taudem_variant] config: {config}", flush=True)
    _t0 = _time.monotonic()
    _start_iso = _dt.now().isoformat(timespec="seconds")
    out = SWATGenXCommand(config).execute()
    _total_s = round(_time.monotonic() - _t0, 1)
    _end_iso = _dt.now().isoformat(timespec="seconds")
    if not out:
        print("ERROR: SWATGenXCommand returned empty path", file=sys.stderr)
        return 1
    print(f"[run_taudem_variant] DONE returned_path={out}", flush=True)

    # SWATGenXCommand returns the SITE path; the model lives under <site>/<MODEL_NAME>.
    model_dir = Path(out) / args.model_name
    if not model_dir.is_dir():
        model_dir = Path(out)
    txt = model_dir / "Scenarios" / "Default" / "TxtInOut" / "chandeg.con"
    rivs = model_dir / "Watershed" / "Shapes" / "rivs1.shp"
    built = txt.is_file()

    # Persist creation wall-clock so NHD vs TauDEM build time can be compared fairly. Run each
    # build alone (no contention) for the wall-clock to be meaningful; QSWAT+ stage timings
    # (runTauDEM/finishDelineation/HRU) remain in the run log for a finer breakdown.
    timing = {
        "model_name": args.model_name,
        "model_id": args.model_id,
        "username": args.username,
        "delineation": args.delineation,
        "stream_threshold_cells": (None if args.auto_threshold else stream_cells),
        "channel_threshold_cells": (None if args.auto_threshold else channel_cells),
        "threshold_basis_res": args.threshold_basis_res,
        "use_lakes": bool(args.use_lakes),
        "lake_split": bool(args.lake_split),
        "clip_dem": bool(args.clip_dem),
        "burn_streams": bool(args.burn_streams or args.burn_flowline_types),
        "burn_flowline_types": args.burn_flowline_types,
        "lake_min_area_km2": args.lake_min_area,
        "lake_types": args.lake_types,
        "dem_resolution": args.dem_resolution,
        "start": _start_iso,
        "end": _end_iso,
        "total_build_seconds": _total_s,
        "total_build_minutes": round(_total_s / 60.0, 2),
        "built": bool(built),
    }
    try:
        with open(model_dir / "build_timing.json", "w") as _fh:
            _json.dump(timing, _fh, indent=2)
    except OSError as _e:
        print(f"[run_taudem_variant] WARN could not write build_timing.json: {_e}", file=sys.stderr)

    print(f"[run_taudem_variant] model_dir={model_dir}", flush=True)
    print(f"[run_taudem_variant] chandeg.con exists={built} | rivs1.shp exists={rivs.is_file()} "
          f"| build={_total_s}s ({timing['total_build_minutes']} min)", flush=True)
    return 0 if built else 1


if __name__ == "__main__":
    raise SystemExit(main())

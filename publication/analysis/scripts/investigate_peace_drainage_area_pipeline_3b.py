#!/usr/bin/env python3
"""Peace phase 3b: rivs1 / sqlite channel area vs NHD and chandeg (10-gage panel).

Quiet when Watershed/Shapes are missing: writes trace rows with artifact status.
Re-run after restoring Peace ``rivs1.shp`` or project SQLite.

Internal QA only.
"""
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    MODEL_BASE,
    TXTINOUT,
    parse_chandeg,
)
from investigate_peace_drainage_area_pipeline import (  # noqa: E402
    OUT_DIR,
    PANEL,
    README_ASSIGN,
    parse_readme_assignment,
)

TRACE3 = OUT_DIR / "peace-drainage-area-pipeline-trace.csv"
OUT_CSV = OUT_DIR / "peace-drainage-area-pipeline-3b-trace.csv"
OUT_MD = OUT_DIR / "peace-drainage-area-pipeline-3b-trace.md"
REL_TOL = 0.08

SHAPES_DIR = MODEL_BASE / "Watershed" / "Shapes"
RIVS1 = SHAPES_DIR / "rivs1.shp"
SWAT_STREAMS = SHAPES_DIR / "SWAT_plus_streams.shp"
SQLITE = MODEL_BASE / f"{MODEL_BASE.name}.sqlite"


def _ha_to_km2(v) -> float | None:
    if v is None or pd.isna(v):
        return None
    x = float(v)
    if not np.isfinite(x) or x <= 0:
        return None
    return x / 100.0


def _rel_close(a: float | None, b: float | None, tol: float = REL_TOL) -> bool:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return False
    return abs(a - b) / abs(b) <= tol


def _pct_diff(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)) or b == 0:
        return None
    return abs(a - b) / abs(b) * 100.0


def _area_like_columns(columns: list[str]) -> list[str]:
    pat = re.compile(r"area|drain|das|totda|areac", re.I)
    return [c for c in columns if pat.search(c)]


def load_rivs1_by_channel() -> tuple[dict[int, float], str]:
    if not RIVS1.is_file():
        return {}, f"missing: {RIVS1}"
    rivs = gpd.read_file(RIVS1)
    if "Channel" not in rivs.columns:
        return {}, f"rivs1 present but no Channel column: {RIVS1}"
    ac_col = "AreaC" if "AreaC" in rivs.columns else None
    if ac_col is None:
        return {}, f"rivs1 present but no AreaC column: {RIVS1}"
    out: dict[int, float] = {}
    for _, row in rivs.iterrows():
        ch = row.get("Channel")
        if ch is None or pd.isna(ch):
            continue
        km2 = _ha_to_km2(row.get(ac_col))
        if km2 is not None:
            out[int(float(ch))] = km2
    return out, f"ok: {RIVS1} ({len(out)} channels)"


def load_sqlite_areas() -> tuple[dict[int, float], dict[int, float], str]:
    if not SQLITE.is_file():
        return {}, {}, f"missing: {SQLITE}"
    con = sqlite3.connect(SQLITE)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gis_channels'")
    if cur.fetchone() is None:
        con.close()
        return {}, {}, f"sqlite present but no gis_channels: {SQLITE}"
    gis: dict[int, float] = {}
    cur.execute("SELECT id, areac FROM gis_channels")
    for cid, areac in cur.fetchall():
        km2 = _ha_to_km2(areac)
        if km2 is not None and cid is not None:
            gis[int(cid)] = km2
    con_cha: dict[int, float] = {}
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='channel_con'")
    if cur.fetchone():
        cur.execute("SELECT gis_id, area FROM channel_con WHERE gis_id IS NOT NULL")
        for gid, area in cur.fetchall():
            km2 = _ha_to_km2(area)
            if km2 is not None and gid is not None:
                con_cha[int(gid)] = km2
    con.close()
    return gis, con_cha, f"ok: {SQLITE} (gis_channels={len(gis)}, channel_con={len(con_cha)})"


def swat_streams_area_fields() -> tuple[str, str]:
    if not SWAT_STREAMS.is_file():
        return "missing", f"missing: {SWAT_STREAMS}"
    gdf = gpd.read_file(SWAT_STREAMS, rows=1)
    found = _area_like_columns(list(gdf.columns))
    if found:
        return "present_unexpected", ",".join(found)
    return "none_expected", f"ok: no drainage-area fields ({len(gdf.columns)} cols)"


def classify_3b(
    nhd: float | None,
    rivs1: float | None,
    chandeg: float | None,
    rivs1_status: str,
) -> str:
    if not rivs1_status.startswith("ok:"):
        return "artifacts_missing_rerun_when_restored"
    if rivs1 is None or chandeg is None:
        return "insufficient_channel_match"
    if _rel_close(rivs1, chandeg) and nhd is not None and rivs1 > float(nhd) * (1 + REL_TOL):
        return "offset_in_rivs1_before_chandeg_export"
    if _rel_close(rivs1, chandeg):
        return "rivs1_matches_chandeg"
    if rivs1 < chandeg * (1 - REL_TOL):
        return "chandeg_higher_than_rivs1_review_export"
    if rivs1 > chandeg * (1 + REL_TOL):
        return "rivs1_higher_than_chandeg_review"
    return "mixed_review"


def main() -> None:
    panel = pd.read_csv(PANEL, dtype={"usgs_site_no": str})
    panel["usgs_site_no"] = panel["usgs_site_no"].str.zfill(8)

    trace3 = pd.read_csv(TRACE3, dtype={"usgs_site_no": str}) if TRACE3.is_file() else None
    if trace3 is not None:
        trace3["usgs_site_no"] = trace3["usgs_site_no"].str.zfill(8)
        trace3_idx = trace3.set_index("usgs_site_no")
    else:
        trace3_idx = None

    rivs_by_ch, rivs1_status = load_rivs1_by_channel()
    gis_by_id, con_by_gid, sqlite_status = load_sqlite_areas()
    streams_field_status, streams_note = swat_streams_area_fields()
    readme_areas = parse_readme_assignment()
    chandeg = parse_chandeg(TXTINOUT)
    gis_area = chandeg.set_index("gis_id")["area_km2"].to_dict()

    rows = []
    for _, pr in panel.iterrows():
        site = pr["usgs_site_no"]
        role = pr["role"]
        gis_ch = None
        if trace3_idx is not None and site in trace3_idx.index:
            gis_ch = trace3_idx.loc[site, "gis_channel"]
            if isinstance(gis_ch, pd.Series):
                gis_ch = gis_ch.iloc[0]
        nhd_a = gis_g = None
        if trace3_idx is not None and site in trace3_idx.index:
            nhd_a = trace3_idx.loc[site, "stage_a_nhd_totdasqkm_zip"]
            gis_g = trace3_idx.loc[site, "stage_g_streams_pkl_reach_totdasqkm"]
        stage_f = float(gis_area[int(gis_ch)]) if gis_ch is not None and not pd.isna(gis_ch) and int(gis_ch) in gis_area else None
        stage_e_readme = readme_areas.get(site)
        stage_h_rivs1 = rivs_by_ch.get(int(gis_ch)) if gis_ch is not None and not pd.isna(gis_ch) else None
        stage_h_sqlite_gis = gis_by_id.get(int(gis_ch)) if gis_ch is not None and not pd.isna(gis_ch) else None
        stage_h2_sqlite_con = con_by_gid.get(int(gis_ch)) if gis_ch is not None and not pd.isna(gis_ch) else None

        row = {
            "usgs_site_no": site,
            "panel_role": role,
            "gis_channel": int(gis_ch) if gis_ch is not None and not pd.isna(gis_ch) else None,
            "stage_a_nhd_totdasqkm_zip": nhd_a,
            "stage_g_streams_pkl_reach_totdasqkm": gis_g,
            "stage_e_readme_areac_km2": stage_e_readme,
            "stage_h_rivs1_areac_km2": stage_h_rivs1,
            "stage_h_sqlite_gis_channels_areac_km2": stage_h_sqlite_gis,
            "stage_h2_sqlite_channel_con_area_km2": stage_h2_sqlite_con,
            "stage_f_chandeg_km2": stage_f,
            "artifact_rivs1": rivs1_status,
            "artifact_sqlite": sqlite_status,
            "artifact_swat_plus_streams": streams_note,
            "swat_plus_streams_area_fields": streams_field_status,
            "pct_h_vs_a": _pct_diff(stage_h_rivs1, nhd_a),
            "pct_h_vs_g": _pct_diff(stage_h_rivs1, gis_g),
            "pct_h_vs_f": _pct_diff(stage_h_rivs1, stage_f),
            "pct_f_vs_h": _pct_diff(stage_f, stage_h_rivs1),
            "fork_3b": classify_3b(
                float(nhd_a) if nhd_a is not None and np.isfinite(nhd_a) else None,
                stage_h_rivs1,
                stage_f,
                rivs1_status,
            ),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    lines = [
        "# Peace phase 3b — rivs1 / sqlite vs NHD and chandeg",
        "",
        f"**Model base:** `{MODEL_BASE}`",
        "",
        "## Artifact status",
        "",
        f"| Artifact | Status |",
        f"|---|---|",
        f"| `rivs1.shp` | {rivs1_status} |",
        f"| Project SQLite | {sqlite_status} |",
        f"| `SWAT_plus_streams.shp` area fields | {streams_field_status} — {streams_note} |",
        "",
        "When artifacts are missing, `stage_h_*` columns are empty and `fork_3b` is "
        "`artifacts_missing_rerun_when_restored`. Re-run this script after restore.",
        "",
        "## Panel trace",
        "",
        "| Site | Role | NHD A | G pickle | rivs1 H | sqlite | chandeg F | fork_3b |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in df.iterrows():
        h = r.get("stage_h_rivs1_areac_km2")
        sq = r.get("stage_h_sqlite_gis_channels_areac_km2")
        sq_s = f"{sq:.2f}" if h is None and sq is not None and np.isfinite(sq) else (f"{h:.2f}" if h is not None and np.isfinite(h) else "—")
        lines.append(
            f"| {r['usgs_site_no']} | {r['panel_role']} | {r.get('stage_a_nhd_totdasqkm_zip', '—')} | "
            f"{r.get('stage_g_streams_pkl_reach_totdasqkm', '—')} | "
            f"{h if h is not None and np.isfinite(h) else '—'} | {sq_s} | "
            f"{r.get('stage_f_chandeg_km2', '—')} | {r.get('fork_3b', '—')} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation (when rivs1 is restored)",
            "",
            "- **H ≈ F ≈ E and all ≫ A:** offset is in QSWAT/TauDEM channel `AreaC`, not TxtInOut export.",
            "- **H low, F high:** offset introduced during SWAT+ text export.",
            "- **G ≈ A, H high:** supports TauDEM recompute vs NHD VAA (not pre-inflated pickle attribute).",
            "",
            f"Output: `{OUT_CSV.name}`",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if rivs1_status.startswith("ok:"):
        print(f"rivs1 found; wrote {OUT_CSV}")
    else:
        print(f"rivs1 not on disk ({RIVS1}); wrote missing-artifact rows to {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()

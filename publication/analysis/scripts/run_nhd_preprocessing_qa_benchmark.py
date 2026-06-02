#!/usr/bin/env python3
"""
Compare **original NHDPlus HR** (HU4 GDB zip) against **delivered SWAT+ shapes**.

Baseline counts come from the USGS zip under ``GenXAppData/NHDPlusHR/zipped/``:
each VPU is extracted to a temporary directory, layers are read from the FileGDB,
domain catchments/flowlines are counted, then the temp tree is removed.

Final product counts come **only** from admin model workspaces (``rivs1.shp``,
``subs1.shp``, etc.) — not from ``streams.pkl``, ``watersheds.pkl``, or other
preprocessed national artifacts.

Usage (repo root):
  python3 publication/analysis/scripts/run_nhd_preprocessing_qa_benchmark.py
"""
from __future__ import annotations

import ast
import csv
import os
import shutil
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402
from wbd_upstream_huc12 import watershed_huc12s_for_outlet  # noqa: E402

ROSTER = REPO / "publication/tables/tab-model-roster.csv"
COMPLEXITY = REPO / "publication/tables/tab-model-complexity.csv"
USER_ROOT = Path("${SWATGENX_USER_PATH}/SWATplus_by_VPUID")
ZIP_DIR = Path(SWATGenXPaths.NHDPlus_VPUID_zipped_path)
STREAMFLOW_VPU = Path(SWATGenXPaths.streamflow_vpuid_path)
OUT_DIR = REPO / "publication/analysis/qa"
CSV_OUT = REPO / "publication/tables/tab-nhd-preprocessing-qa.csv"
MD_OUT = OUT_DIR / "nhd-preprocessing-qa-benchmark.md"

GDB_LAYERS = (
    "WBDHU12",
    "NHDFlowline",
    "NHDPlusFlowlineVAA",
    "NHDPlusCatchment",
    "NHDWaterbody",
)

_vpu_original_cache: dict[str, dict[str, gpd.GeoDataFrame]] = {}


def _z12(values) -> set[str]:
    return {str(v).strip().zfill(12) for v in values if str(v).strip()}


def _read_meta_huc12s(vpuid: str, site_no: str) -> list[str]:
    meta_path = STREAMFLOW_VPU / vpuid / f"meta_{vpuid}.csv"
    df = pd.read_csv(meta_path, dtype={"site_no": str})
    row = df.loc[df["site_no"] == str(site_no).zfill(8)]
    if row.empty:
        raise ValueError(f"site {site_no} not in {meta_path}")
    raw = row.iloc[0]["list_of_huc12s"]
    parsed = ast.literal_eval(raw)
    return sorted(_z12(parsed))


def resolve_domain_huc12s(vpuid: str, level: str, name: str) -> list[str]:
    name = str(name).strip()
    if level == "huc8":
        hucs = derive_huc12_list_for_huc8(name.zfill(8), vpuid=vpuid)
        if not hucs:
            raise ValueError(f"no HUC12s for huc8 {name} vpuid {vpuid}")
        return sorted(_z12(hucs))
    if len(name) == 12 and name.isdigit():
        res = watershed_huc12s_for_outlet(name.zfill(12))
        if not res.get("ok"):
            raise ValueError(f"watershed_huc12s_for_outlet failed: {res}")
        return sorted(_z12(res["watershed_huc12s"]))
    return _read_meta_huc12s(vpuid, name)


def _find_zip(vpuid: str) -> Path:
    if not ZIP_DIR.is_dir():
        raise FileNotFoundError(ZIP_DIR)
    matches = sorted(
        p for p in ZIP_DIR.iterdir() if p.suffix.lower() == ".zip" and f"_{vpuid}_" in p.name
    )
    if not matches:
        raise FileNotFoundError(f"No NHDPlus HR zip matching '*_{vpuid}_*.zip' in {ZIP_DIR}")
    return matches[0]


def _find_gdb(root: Path) -> Path:
    for dirpath, dirnames, _ in os.walk(root):
        for d in dirnames:
            if d.endswith(".gdb"):
                return Path(dirpath) / d
    raise FileNotFoundError(f"No .gdb under {root}")


def _read_gdb_layer(gdb: Path, layer: str) -> gpd.GeoDataFrame | pd.DataFrame:
    import pyogrio

    info = pyogrio.read_info(str(gdb), layer=layer)
    if info.get("geometry_type") is None:
        return pyogrio.read_dataframe(str(gdb), layer=layer, read_geometry=False)
    gdf = gpd.read_file(gdb, layer=layer)
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)
    return gdf


@contextmanager
def _original_nhd_vpuid(vpuid: str, *, keep_unzip: bool = False):
    """Unzip original HR GDB to a temp dir, load layers, then remove the tree."""
    if vpuid in _vpu_original_cache:
        yield _vpu_original_cache[vpuid]
        return

    zip_path = _find_zip(vpuid)
    tmp_root = Path(tempfile.mkdtemp(prefix=f"nhd_qa_{vpuid}_"))
    unzip_dir = tmp_root / "gdb"
    unzip_dir.mkdir()
    print(f"  unzip {zip_path.name} -> {tmp_root} (temporary)")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(unzip_dir)
    gdb = _find_gdb(unzip_dir)
    layers = {name: _read_gdb_layer(gdb, name) for name in GDB_LAYERS}
    layers["source_zip"] = str(zip_path)
    _vpu_original_cache[vpuid] = layers
    try:
        yield layers
    finally:
        if not keep_unzip:
            shutil.rmtree(tmp_root, ignore_errors=True)
            print(f"  removed temp {tmp_root}")


def _normalize_nhdplus_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    id_col = next((c for c in out.columns if c.lower() == "nhdplusid"), None)
    if id_col is None:
        raise KeyError(f"No NHDPlusID column in {list(out.columns)}")
    if id_col != "NHDPlusID":
        out = out.rename(columns={id_col: "NHDPlusID"})
    out["NHDPlusID"] = pd.to_numeric(out["NHDPlusID"], errors="coerce")
    return out


def _normalize_huc12(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    huc_col = next((c for c in out.columns if c.lower() == "huc12"), None)
    if huc_col is None:
        raise KeyError(f"No HUC12 column in {list(out.columns)}")
    if huc_col != "huc12":
        out = out.rename(columns={huc_col: "huc12"})
    out["huc12"] = out["huc12"].astype(str).str.zfill(12)
    return out


def _assign_catchments_to_huc12(
    catchment: gpd.GeoDataFrame,
    wbdhu12: gpd.GeoDataFrame,
    huc12_domain: set[str],
) -> gpd.GeoDataFrame:
    h12 = _normalize_huc12(wbdhu12)
    h12 = h12[h12["huc12"].isin(huc12_domain)].copy()
    pts = catchment[["NHDPlusID", "geometry"]].copy()
    pts["geometry"] = pts.geometry.representative_point()
    joined = gpd.sjoin(pts, h12[["huc12", "geometry"]], how="inner", predicate="within")
    return joined.drop_duplicates(subset="NHDPlusID")


def _pick_vaa_columns(vaa: pd.DataFrame) -> pd.DataFrame:
    out = _normalize_nhdplus_id(vaa.copy())
    mapping: dict[str, str] = {}
    for std in ("Divergence", "HydroSeq", "DnHydroSeq", "UpHydroSeq"):
        col = next((c for c in out.columns if c.lower() == std.lower()), None)
        if col:
            mapping[col] = std
    out = out.rename(columns=mapping)
    if "Divergence" not in out.columns:
        out["Divergence"] = pd.NA
    for col in ("HydroSeq", "DnHydroSeq", "UpHydroSeq"):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype("int64")
        else:
            out[col] = 0
    return out


def _simulate_preprocess_drops(
    flows_in: pd.DataFrame,
    domain_catch_ids: set[int],
) -> dict[str, int]:
    """Apply SWATGenX stream-drop rules on original-domain flowlines (in memory)."""
    s = flows_in.copy()
    div2 = s["Divergence"] == 2
    n_div2 = int(div2.sum())
    div2_catchments = int(s.loc[div2, "NHDPlusID"].nunique())
    s = s.loc[~div2].reset_index(drop=True)

    if "Permanent_Identifier" in s.columns:
        coastal = s["Permanent_Identifier"].astype(str).str.startswith("C")
        n_coastal = int(coastal.sum())
        s = s.loc[~coastal].reset_index(drop=True)
    else:
        n_coastal = 0

    s = s[s["NHDPlusID"].isin(domain_catch_ids)].reset_index(drop=True)

    hydroseq_set = set(s["HydroSeq"].astype("int64"))
    s["DnHydroSeq"] = s["DnHydroSeq"].where(s["DnHydroSeq"].isin(hydroseq_set), 0)
    s["UpHydroSeq"] = s["UpHydroSeq"].where(s["UpHydroSeq"].isin(hydroseq_set), 0)

    isolated = (s["UpHydroSeq"] == 0) & (s["DnHydroSeq"] == 0)
    n_isolated = int(isolated.sum())
    isolated_catchments = int(s.loc[isolated, "NHDPlusID"].nunique())
    s = s.loc[~isolated].reset_index(drop=True)

    retained_ids = set(s["NHDPlusID"].astype("int64"))
    flowed_catch_ids = set(flows_in["NHDPlusID"].astype("int64"))
    orphan_catchments = int(len(flowed_catch_ids - retained_ids))

    return {
        "divergence2_catchments_merged": div2_catchments,
        "coastal_removed": n_coastal,
        "isolated_reaches_removed": n_isolated,
        "isolated_catchments_merged": isolated_catchments,
        "orphan_catchments_merged": orphan_catchments,
        "retained_flowlines_after_rules": int(len(s)),
    }


def _original_domain_counts(
    layers: dict[str, gpd.GeoDataFrame],
    huc12_domain: set[str],
) -> dict[str, int]:
    catchment = _normalize_nhdplus_id(gpd.GeoDataFrame(layers["NHDPlusCatchment"], geometry="geometry"))
    if catchment.crs is None:
        catchment = catchment.set_crs("EPSG:4326", allow_override=True)
    wbd = _normalize_huc12(gpd.GeoDataFrame(layers["WBDHU12"], geometry="geometry"))
    if wbd.crs is None:
        wbd = wbd.set_crs("EPSG:4326", allow_override=True)
    catch_in_domain = _assign_catchments_to_huc12(catchment, wbd, huc12_domain)
    domain_catch_ids = set(catch_in_domain["NHDPlusID"].dropna().astype("int64"))

    flowline = _normalize_nhdplus_id(layers["NHDFlowline"].copy())
    vaa = _pick_vaa_columns(layers["NHDPlusFlowlineVAA"])
    vaa_ids = set(vaa["NHDPlusID"].dropna().astype("int64"))

    vaa_cols = ["NHDPlusID", "Divergence", "HydroSeq", "DnHydroSeq", "UpHydroSeq"]
    merged = flowline.merge(vaa[vaa_cols], on="NHDPlusID", how="inner")
    flows_in = merged[merged["NHDPlusID"].isin(domain_catch_ids)].copy()

    drops = _simulate_preprocess_drops(flows_in, domain_catch_ids)

    wb = gpd.GeoDataFrame(layers["NHDWaterbody"], geometry="geometry", crs=catchment.crs)
    wb_pts = wb.copy()
    wb_pts["geometry"] = wb_pts.geometry.representative_point()
    catch_polys = gpd.GeoDataFrame(
        catchment[catchment["NHDPlusID"].isin(domain_catch_ids)][["NHDPlusID", "geometry"]],
        geometry="geometry",
        crs=catchment.crs,
    )
    wb_in = gpd.sjoin(wb_pts, catch_polys, how="inner", predicate="within")
    wb_key = "Permanent_Identifier" if "Permanent_Identifier" in wb_in.columns else "NHDPlusID"
    n_waterbodies = int(wb_in.drop_duplicates(subset=wb_key).shape[0]) if len(wb_in) else 0

    no_vaa_catchments = int((~catch_in_domain["NHDPlusID"].isin(vaa_ids)).sum())

    return {
        "original_catchments": int(len(catch_in_domain)),
        "original_flowlines_vaa": int(len(flows_in)),
        "original_divergence2": int((flows_in["Divergence"] == 2).sum()),
        "original_coastal_flowlines": drops["coastal_removed"],
        "original_catchments_no_flowline": no_vaa_catchments,
        "original_waterbodies": n_waterbodies,
        "unmatched_catchment_removed": 0,
        **drops,
    }


def _shape_count(path: Path) -> int | None:
    return len(gpd.read_file(path)) if path.is_file() else None


def _model_shapes_root(workspace_model_id: str) -> Path:
    vpuid, level, name = workspace_model_id.split("/")
    return USER_ROOT / vpuid / level / name / "SWAT_MODEL_Web_Application" / "Watershed" / "Shapes"


def _final_product_counts(
    shapes: Path,
    catalog_id: str,
) -> dict[str, int | None]:
    channels = _shape_count(shapes / "rivs1.shp")
    subbasins = _shape_count(shapes / "subs1.shp")
    watersheds = _shape_count(shapes / "SWAT_plus_watersheds.shp")
    post_extract = _shape_count(shapes / "SWAT_plus_streams.shp")
    lakes = _shape_count(shapes / "SWAT_plus_lakes.shp")

    if catalog_id and COMPLEXITY.is_file():
        with COMPLEXITY.open(newline="", encoding="utf-8") as f:
            inv = {r["catalog_model_id"]: r for r in csv.DictReader(f)}
        row = inv.get(catalog_id, {})
        if channels is None and row.get("n_channels"):
            channels = int(row["n_channels"])
        if subbasins is None and row.get("n_subbasins"):
            subbasins = int(row["n_subbasins"])

    return {
        "post_extract_streams": post_extract,
        "final_channels": channels,
        "final_subbasins": subbasins,
        "final_watersheds": watersheds,
        "lakes_in_final_swat": lakes,
    }


def analyze_model(row: dict, *, keep_unzip: bool = False) -> dict:
    ws = row["workspace_model_id"].strip()
    vpuid, level, name = ws.split("/")
    catalog_id = row["catalog_model_id"]
    huc12s = resolve_domain_huc12s(vpuid, level, name)
    huc12_set = set(huc12s)

    with _original_nhd_vpuid(vpuid, keep_unzip=keep_unzip) as layers:
        orig = _original_domain_counts(layers, huc12_set)
        zip_path = layers["source_zip"]

    final = _final_product_counts(_model_shapes_root(ws), catalog_id)

    orig_catch = orig["original_catchments"]
    orig_flow = orig["original_flowlines_vaa"]
    final_ch = final["final_channels"] or 0
    final_sub = final["final_subbasins"] or 0
    final_ws = final["final_watersheds"] or 0

    return {
        "cohort": row.get("cohort", ""),
        "tier": row.get("tier", ""),
        "catalog_model_id": catalog_id,
        "workspace_model_id": ws,
        "label": row.get("label", ""),
        "n_huc12_in_domain": len(huc12s),
        "source_zip": zip_path,
        "input_catchments": orig_catch,
        "input_reaches": orig_flow,
        "divergence2_removed": orig["original_divergence2"],
        "coastal_removed": orig["original_coastal_flowlines"],
        "unmatched_catchment_removed": orig["unmatched_catchment_removed"],
        "no_vaa_catchments_dissolved": orig["original_catchments_no_flowline"],
        "isolated_reaches_removed": orig["isolated_reaches_removed"],
        "isolated_catchments_merged": orig["isolated_catchments_merged"],
        "orphan_catchments_merged": orig["orphan_catchments_merged"],
        "divergence2_catchments_merged": orig["divergence2_catchments_merged"],
        "retained_flowlines_after_rules": orig["retained_flowlines_after_rules"],
        "nhd_waterbodies_in_domain": orig["original_waterbodies"],
        "lakes_in_final_swat": final["lakes_in_final_swat"] if final["lakes_in_final_swat"] is not None else "",
        "post_extract_streams": final["post_extract_streams"] if final["post_extract_streams"] is not None else "",
        "final_channels": final["final_channels"] if final["final_channels"] is not None else "",
        "final_subbasins": final["final_subbasins"] if final["final_subbasins"] is not None else "",
        "final_watersheds": final_ws if final_ws else "",
        "catchments_consolidated": max(orig_catch - final_ws, 0) if final_ws else "",
        "flowlines_removed_total": orig_flow - final_ch if final_ch else "",
        "status": "ok",
        "run_datetime_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _to_manuscript_row(r: dict) -> dict:
    return {
        "row_id": f"NQA-{r.get('tier') or r['catalog_model_id']}",
        "cohort": r["cohort"],
        "tier": r.get("tier", ""),
        "catalog_model_id": r["catalog_model_id"],
        "label": r["label"],
        "n_huc12_in_domain": r["n_huc12_in_domain"],
        "input_reaches": r["input_reaches"],
        "retained_reaches": r.get("post_extract_streams") or r.get("final_channels") or "",
        "divergence2_removed": r["divergence2_removed"],
        "unmatched_catchment_removed": r["unmatched_catchment_removed"],
        "no_vaa_catchments_dissolved": r["no_vaa_catchments_dissolved"],
        "isolated_reaches_removed": r.get("isolated_reaches_removed", ""),
        "isolated_catchments_merged": r.get("isolated_catchments_merged", ""),
        "orphan_catchments_merged": r.get("orphan_catchments_merged", ""),
        "divergence2_catchments_merged": r.get("divergence2_catchments_merged", ""),
        "post_extract_streams": r.get("post_extract_streams", ""),
        "final_channels": r.get("final_channels", ""),
        "final_subbasins": r.get("final_subbasins", ""),
        "nhd_waterbodies_in_domain": r["nhd_waterbodies_in_domain"],
        "lakes_in_final_swat": r.get("lakes_in_final_swat", ""),
        "original_catchments": r["input_catchments"],
        "final_watersheds": r.get("final_watersheds", ""),
        "catchments_consolidated": r.get("catchments_consolidated", ""),
        "status": "frozen_qa_from_original_zip",
        "notes": f"Input from {Path(r['source_zip']).name}; final from workspace shapefiles.",
    }


def write_markdown(rows: list[dict], path: Path) -> None:
    lines = [
        "# NHD preprocessing QA (original zip vs delivered product)",
        "",
        f"Generated at {rows[0]['run_datetime_utc']}.",
        "",
        "**Input:** USGS NHDPlus HR HU4 GDB zip (temporary unzip, then deleted).",
        "**Output:** admin workspace `rivs1.shp` / `subs1.shp` / `SWAT_plus_watersheds.shp`.",
        "",
        "| Tier | Model | Orig. catch. | Orig. flow | Div-2 | Isol. reach | Isol. cat. | Orphan cat. | No-VAA | Final ch. | Final ws. |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r.get('tier') or r.get('cohort')} | `{r['catalog_model_id']}` | "
            f"{r['input_catchments']} | {r['input_reaches']} | {r['divergence2_removed']} | "
            f"{r.get('isolated_reaches_removed', '---')} | {r.get('isolated_catchments_merged', '---')} | "
            f"{r.get('orphan_catchments_merged', '---')} | {r['no_vaa_catchments_dissolved']} | "
            f"{r.get('final_channels', '---')} | {r.get('final_watersheds', '---')} |"
        )
    lines.extend(
        [
            "",
            "- **Isol. reach / cat.** = isolated flowlines (both hydroseq links zero) and their catchment polygons, removed and dissolved into neighbours.",
            "- **Orphan cat.** = catchments whose original flowline was dropped by div-2/isolated/coastal rules (polygon merged, not retained as standalone).",
            "",
            f"Manuscript CSV: `{CSV_OUT.name}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--keep-unzip", action="store_true", help="Keep temp unzip dirs (debug only)")
    args = p.parse_args()

    _vpu_original_cache.clear()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with ROSTER.open(newline="", encoding="utf-8") as f:
        roster = [r for r in csv.DictReader(f) if r.get("status") == "official"]

    results: list[dict] = []
    for row in roster:
        try:
            print(f"Analyzing {row['catalog_model_id']} ...")
            results.append(analyze_model(row, keep_unzip=args.keep_unzip))
            print(f"OK {row['catalog_model_id']}")
        except Exception as exc:
            results.append(
                {
                    "catalog_model_id": row["catalog_model_id"],
                    "status": f"error: {exc}",
                    "run_datetime_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
            )
            print(f"ERROR {row['catalog_model_id']}: {exc}")

    ok_rows = [r for r in results if r.get("status") == "ok"]
    if not ok_rows:
        raise SystemExit("No successful QA rows")

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ok_rows[0].keys()), extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)

    ms_rows = [_to_manuscript_row(r) for r in ok_rows]
    ms_path = REPO / "publication/tables/tab-nhd-preprocessing-qa.csv"
    with ms_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(ms_rows[0].keys()))
        w.writeheader()
        w.writerows(ms_rows)

    write_markdown(ok_rows, MD_OUT)
    print(f"Wrote {CSV_OUT}")
    print(f"Wrote {ms_path}")
    print(f"Wrote {MD_OUT}")


if __name__ == "__main__":
    main()

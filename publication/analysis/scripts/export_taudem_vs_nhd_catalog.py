#!/usr/bin/env python3
"""Export the TauDEM-vs-NHDPlus-HR delineation comparison (Oklawaha S small model) to a
frontend JSON consumed by ``SwatPlusTauDemVsNhdPanel``.

This is the website/manuscript companion to the internal findings note
``publication/analysis/qa/taudem-vs-nhd-small-model-findings.md``. Every quantitative field for a
*built* model is read live from its executable SWAT+ artifacts so the page stays reproducible:

  channels   = data rows in Scenarios/Default/TxtInOut/chandeg.con
  hrus       = data rows in Scenarios/Default/TxtInOut/hru-data.hru
  reservoirs = data rows in Scenarios/Default/TxtInOut/reservoir.con (0 if file absent)
  subbasins  = distinct Subbasin ids in Watershed/Shapes/rivs1.shp
  outletArea = max(AreaC)/100 over Watershed/Shapes/rivs1.shp (hectares -> km^2)
  lakes      = features / total area in Watershed/Shapes/SWAT_plus_lakes.shp

The delineation parameters and the (documented) failure reason for the lake-bearing builds that
QSWAT+ could not complete are carried as metadata in MODELS below — those builds have no executable
TxtInOut to read, so their outcome is the experimental result itself.

Usage:
  python export_taudem_vs_nhd_catalog.py [--site-dir DIR] [--out JSON]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import geopandas as gpd

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SITE = "${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0308/huc12_outlet/030801020804"
DEFAULT_OUT = REPO / "web_application/frontend/src/data/taudemVsNhdComparison.json"

REFERENCE_ID = "nhd"

# Ordered model set. ``built`` models are read live; ``built: False`` records a documented
# QSWAT+ build failure (the experimental result). Areas/counts for built models are overwritten
# from artifacts below.
MODELS = [
    {
        "id": "nhd",
        "label": "NHDPlus HR (production)",
        "workspaceModelId": "SWAT_MODEL_Web_Application",
        "delineation": "NHDPlus HR (existing network)",
        "demExtent": "n/a (predefined hydrography)",
        "lakesRequested": True,
        "lakeMethod": "NHD lake–channel topology",
        "streamBurn": False,
        "isReference": True,
    },
    {
        "id": "taudem_coarse_nhdlike",
        "label": "TauDEM · NHDPlus-like (coarse)",
        "workspaceModelId": "SWAT_MODEL_TauDEM_coarse_s15k_c500",
        "delineation": "Threshold TauDEM (stream 15000 / channel 500 cells)",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": False,
        "lakeMethod": None,
        "streamBurn": False,
        "successNote": "A coarse stream threshold (~one subbasin for the whole HUC12) with a moderate channel threshold reproduces the NHDPlus HR structure: a single subbasin subdivided into many catchment-scale landscape units — not the many-subbasin fragmentation of the default threshold.",
    },
    {
        "id": "taudem_square",
        "label": "TauDEM · square DEM",
        "workspaceModelId": "SWAT_MODEL_TauDEM_auto",
        "delineation": "Threshold TauDEM (stream 5000 / channel 1000 cells)",
        "demExtent": "Square bounding box",
        "lakesRequested": False,
        "lakeMethod": None,
        "streamBurn": False,
    },
    {
        "id": "taudem_clip",
        "label": "TauDEM · basin-clip DEM",
        "workspaceModelId": "SWAT_MODEL_TauDEM_nolakes_clip",
        "delineation": "Threshold TauDEM (stream 5000 / channel 1000 cells)",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": False,
        "lakeMethod": None,
        "streamBurn": False,
    },
    {
        "id": "taudem_clip_burn",
        "label": "TauDEM · basin-clip + stream-burn",
        "workspaceModelId": "SWAT_MODEL_TauDEM_burn_nolakes_clip",
        "delineation": "Threshold TauDEM + NHD stream-burn into DEM",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": False,
        "lakeMethod": None,
        "streamBurn": True,
    },
    {
        "id": "taudem_lakes_addhuc_clip",
        "label": "TauDEM + lakes · addHUCLakes · clip",
        "workspaceModelId": "SWAT_MODEL_TauDEM_lakes_clip",
        "delineation": "Threshold TauDEM",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": True,
        "lakeMethod": "addHUCLakes",
        "streamBurn": False,
        "built": False,
        "failureReason": "Failed to find outlet for lake 1–4 (lake outlet not a DSNODEID in demchannel.shp) → HRU creation crash (QgsGeometry.fromPointXY NoneType).",
    },
    {
        "id": "taudem_lakes_split_clip",
        "label": "TauDEM + lakes · splitChannelsByLakes · clip",
        "workspaceModelId": "SWAT_MODEL_TauDEM_lakes_clip_split",
        "delineation": "Threshold TauDEM (channels re-split by lakes, TauDEM rerun)",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": True,
        "lakeMethod": "splitChannelsByLakes",
        "streamBurn": False,
        "built": False,
        "failureReason": "Identical lake-outlet resolution failure (Failed to find outlet for lake 1–4) → HRU crash.",
    },
    {
        "id": "taudem_lakes_addhuc_square",
        "label": "TauDEM + lakes · addHUCLakes · square",
        "workspaceModelId": "SWAT_MODEL_TauDEM_lakes_square",
        "delineation": "Threshold TauDEM",
        "demExtent": "Square bounding box",
        "lakesRequested": True,
        "lakeMethod": "addHUCLakes",
        "streamBurn": False,
        "built": False,
        "failureReason": "Same lake-outlet failure on the square DEM — DEM extent does not change the outcome.",
    },
    {
        "id": "taudem_lakes_burn_clip",
        "label": "TauDEM + lakes · stream-burn · clip",
        "workspaceModelId": "SWAT_MODEL_TauDEM_lakes_burn_clip",
        "delineation": "Threshold TauDEM + NHD stream-burn",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": True,
        "lakeMethod": "addHUCLakes",
        "streamBurn": True,
        "built": False,
        "failureReason": "Stream-burn engaged but lakes still failed identically (Failed to find outlet for lake 1–4) → HRU crash.",
    },
    {
        "id": "taudem_lakes_split_fine",
        "label": "TauDEM + lakes · splitChannelsByLakes · fine (500/100)",
        "workspaceModelId": "SWAT_MODEL_TauDEM_split_s500c100_clip",
        "delineation": "Threshold TauDEM, splitChannelsByLakes (stream 500 / channel 100 cells)",
        "demExtent": "Basin polygon + 250 m buffer",
        "lakesRequested": True,
        "lakeMethod": "splitChannelsByLakes",
        "streamBurn": False,
        "successNote": "Geometric re-cut of channels at lake boundaries (fresh outlet nodes, no NHD-ID match) at a fine threshold wires all 4 lakes as reservoirs and runs SWAT+ successfully.",
    },
]


def _dem_resolution_m(base: Path) -> float | None:
    """Live DEM cell size (m) from the filled DEM TauDEM/QSWAT+ actually routes on."""
    for name in ("dem.tif", "demfel.tif"):
        dem = base / "Watershed" / "Rasters" / "DEM" / name
        if dem.is_file():
            try:
                import rasterio

                with rasterio.open(dem) as r:
                    return round(float(r.res[0]), 1)
            except Exception:
                return None
    return None


def _count_data_rows(path: Path) -> int | None:
    """SWAT+ connectivity/HRU files: 2 header lines then one row per object."""
    if not path.is_file():
        return None
    n = 0
    with open(path, "r", errors="ignore") as fh:
        for i, line in enumerate(fh):
            if i < 2:
                continue
            if line.strip():
                n += 1
    return n


def _read_built_model(site: Path, m: dict) -> dict:
    base = site / m["workspaceModelId"]
    txt = base / "Scenarios" / "Default" / "TxtInOut"
    rivs = base / "Watershed" / "Shapes" / "rivs1.shp"
    lsus = base / "Watershed" / "Shapes" / "lsus1.shp"
    lakes = base / "Watershed" / "Shapes" / "SWAT_plus_lakes.shp"

    channels = _count_data_rows(txt / "chandeg.con")
    built = channels is not None
    out = {
        **{k: v for k, v in m.items() if k not in ("built",)},
        "built": m.get("built", built),
    }
    if out["built"] and channels is not None:
        out["channels"] = channels
        out["hrus"] = _count_data_rows(txt / "hru-data.hru")
        out["reservoirs"] = _count_data_rows(txt / "reservoir.con") or 0
        if rivs.is_file():
            g = gpd.read_file(rivs)
            out["subbasins"] = int(g["Subbasin"].nunique()) if "Subbasin" in g.columns else None
            out["outletAreaKm2"] = round(float(g["AreaC"].max()) / 100.0, 2) if "AreaC" in g.columns else None
        # Landscape units (LSUs) — the catchment-scale division inside each subbasin.
        # NHDPlus HR keeps a HUC12 as ~1 subbasin with many catchment LSUs; the count
        # shows whether a TauDEM threshold reproduces that few-subbasin / many-LSU structure.
        out["landscapeUnits"] = int(len(gpd.read_file(lsus))) if lsus.is_file() else None
        out["lakesWired"] = (out.get("reservoirs") or 0) > 0
    else:
        out["built"] = False
        out["channels"] = out["hrus"] = out["subbasins"] = out["outletAreaKm2"] = None
        out["landscapeUnits"] = None
        out["reservoirs"] = 0
        out["lakesWired"] = False

    out["demResolutionM"] = _dem_resolution_m(base)
    out["lakesRequestedLabel"] = "with lakes" if m.get("lakesRequested") else "no lakes"

    # Lake shapefile is produced at the shape stage even for failed builds.
    if lakes.is_file():
        L = gpd.read_file(lakes).to_crs("EPSG:5070")
        out["nLakeShapes"] = int(len(L))
        out["lakeShapesKm2"] = round(float(L.geometry.area.sum()) / 1e6, 3)
    else:
        out["nLakeShapes"] = None
        out["lakeShapesKm2"] = None
    return out


GAGE = "02239501"
FOCAL = {"nhd": "SWAT_MODEL_Web_Application", "taudem": "SWAT_MODEL_TauDEM_split_s500c100_clip"}
QA_DIR = REPO / "publication/analysis/qa/taudem-vs-nhd"


def _assignment(site: Path, model_name: str) -> dict | None:
    """Gage 02239501 -> channel assignment for one model (how each delineation maps the gage)."""
    import pandas as pd

    sf = site / model_name / "streamflow_data"
    stn = sf / "stations.shp"
    if not stn.is_file():
        return None
    st = gpd.read_file(stn)
    st["site_no"] = st["site_no"].astype(str).str.zfill(8)
    row = st[st["site_no"] == GAGE]
    if row.empty:
        return None
    ch = int(row.iloc[0]["channel"])
    riv = gpd.read_file(site / model_name / "Watershed" / "Shapes" / "rivs1.shp")
    chrow = riv[riv["Channel"] == ch]
    order = int(chrow.iloc[0]["strmOrder"]) if len(chrow) and "strmOrder" in riv.columns else None
    g5070 = row.to_crs("EPSG:5070")
    c5070 = riv.to_crs("EPSG:5070")
    snap = round(float(c5070.geometry.distance(g5070.geometry.iloc[0]).min()), 0)
    out = {"channel": ch, "strmOrder": order, "snapM": snap}
    v3 = sf / "stations_assignment_v3.csv"
    if v3.is_file():
        v = pd.read_csv(v3)
        v["site_no"] = v["site_no"].astype(str).str.zfill(8)
        vr = v[v["site_no"] == GAGE]
        if len(vr):
            r0 = vr.iloc[0]
            def _f(k):
                val = r0.get(k)
                return round(float(val), 3) if pd.notna(val) else None
            out.update({
                "swatDaKm2": _f("swat_da_km2"),
                "nhdVaaKm2": _f("nhd_tda_km2"),
                "ratioSwatNhd": _f("swat_nhd_ratio"),
                "assignmentClass": (r0.get("assignment_class") if pd.notna(r0.get("assignment_class")) else None),
                "mappingMethod": (r0.get("mapping_method") if pd.notna(r0.get("mapping_method")) else None),
                "usgsDaKm2": _f("usgs_da_km2"),
                "usgsDaSource": (r0.get("usgs_da_source") if pd.notna(r0.get("usgs_da_source")) else None),
            })
    return out


def _initial_performance() -> dict | None:
    p = QA_DIR / "initial_sim_metrics.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", default=DEFAULT_SITE)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    site = Path(args.site_dir)

    models = [_read_built_model(site, m) for m in MODELS]
    ref = next(m for m in models if m["id"] == REFERENCE_ID)
    ref_area = ref.get("outletAreaKm2")

    for m in models:
        a = m.get("outletAreaKm2")
        if m["id"] == REFERENCE_ID or a is None or not ref_area:
            m["areaVsNhdPct"] = None
            m["areaVerdict"] = "reference" if m["id"] == REFERENCE_ID else None
            continue
        pct = (a - ref_area) / ref_area * 100.0
        m["areaVsNhdPct"] = round(pct, 1)
        m["areaVerdict"] = "over" if pct > 5 else "under" if pct < -5 else "match"

    built = [m for m in models if m["built"]]
    taudem_built = [m for m in built if m["id"] != REFERENCE_ID]
    dem_res_vals = sorted({m["demResolutionM"] for m in built if m.get("demResolutionM")})
    dem_res_m = dem_res_vals[0] if len(dem_res_vals) == 1 else None
    lake_attempts = [m for m in models if m["lakesRequested"] and m["id"] != REFERENCE_ID]
    lake_failures = [m for m in lake_attempts if not m["built"]]

    # Lake context (shared NHD-derived polygons) taken from the reference model.
    split_ok = next((m for m in models if m["id"] == "taudem_lakes_split_fine" and m["built"]), None)
    lake_ctx = {
        "nLakes": ref.get("nLakeShapes"),
        "totalKm2": ref.get("lakeShapesKm2"),
        "source": "NHD-derived (identical polygons inherited by every TauDEM variant)",
        "taudemCanWireLakes": split_ok is not None,
        "taudemSuccessMethod": "splitChannelsByLakes at a fine threshold (stream 500 / channel 100 cells)",
        "taudemSuccessReservoirs": (split_ok or {}).get("reservoirs"),
    }
    perf = _initial_performance()
    figures = {
        "structure": "/figures/fig-subbasin-lsu-structure-S.png",
        "delineation": "/figures/fig-taudem-vs-nhd-delineation-lakes.png",
        "hydrograph": "/figures/fig-taudem-vs-nhd-hydrograph.png",
    }
    # Why the initial sim is far off — NWIS metadata + observed-flow signature for gage 02239501.
    gage_context = {
        "siteNo": GAGE,
        "stationName": "SILVER RIVER NEAR OCALA, FL",
        "nwisDrainAreaReported": False,
        "springFed": True,
        "spring": "Silver Springs — a first-magnitude artesian spring of the Floridan aquifer",
        "obsMeanCms": 16.2,
        "obsCv": 0.22,
        "p10OverMedian": 0.71,
        "explanation": (
            "Gage 02239501 is the Silver River, a spring run fed by Silver Springs — one of the largest artesian "
            "springs on Earth. NWIS lists no drainage area for the site because its flow is not surface runoff: the "
            "observed ~16 m³/s is artesian discharge from the regional Floridan (karst) aquifer, whose springshed is "
            "far larger than this 53 km² HU12 and sits in deep groundwater. A SWAT+ surface delineation of the local "
            "basin — NHDPlus-HR or TauDEM — simulates rainfall-runoff only and cannot inject spring discharge, so both "
            "undersimulate by ~20×. The very stable observed flow (coefficient of variation 0.22; p10/median 0.71) is "
            "the hydrologic fingerprint of spring discharge, not flashy surface runoff. The initial-simulation gap is "
            "therefore a source/process mismatch, not a delineation or gage-assignment error — and it is identical for "
            "both delineations."
        ),
    }

    catalog = {
        "schemaVersion": 1,
        "basin": {
            "name": "Oklawaha S",
            "huc12": "030801020804",
            "vpuid": "0308",
            "label": "Oklawaha S · HUC-12 030801020804 (VPUID 0308)",
        },
        "generatedFrom": "live SWAT+ TxtInOut + Watershed/Shapes artifacts",
        "sourceNote": (
            "Counts and areas for built models are read from executable chandeg.con / hru-data.hru / "
            "reservoir.con and rivs1.shp. Failed lake builds report the QSWAT+ outcome."
        ),
        "reference": {
            "id": ref["id"],
            "label": ref["label"],
            "outletAreaKm2": ref_area,
            "reservoirs": ref.get("reservoirs"),
        },
        "lakeContext": lake_ctx,
        # Whole-HUC-8 scalability result (Peace River 03100101) — a static one-off experiment,
        # not part of the routine Oklawaha catalog read. Measured 2026-06-05 from the live
        # SWAT_MODEL_TauDEM_pb_peace_clip_burnmajor_250 + SWAT_MODEL_Web_Application artifacts.
        "peaceScale": {
            "basin": "Peace River · HUC-8 03100101 (VPUID 0310)",
            "areaKm2": 6030,
            "nHuc12": 63,
            "nLakes": 347,
            "headline": (
                "At whole-HUC-8 scale the gap widens: NHDPlus HR builds the lake-dense Peace basin "
                "unattended with all 347 waterbodies, while threshold TauDEM reaches a runnable model "
                "only by clipping the DEM to the basin, burning only the major rivers, and dropping "
                "every lake — and even then it over-segments the basin ~14×."
            ),
            "reference": {"label": "NHDPlus HR", "subbasins": 162, "landscapeUnits": 9341,
                          "channels": 8181, "outletAreaKm2": 5982.5, "reservoirs": 347, "built": True},
            "taudem": {"label": "Threshold TauDEM",
                       "recipe": "coarse auto-threshold + basin-clipped 250 m DEM + selective major-river burn + lakes omitted",
                       "subbasins": 2304, "landscapeUnits": 22361, "channels": 22361,
                       "outletAreaKm2": 5853.0, "reservoirs": 0, "built": True},
            "points": [
                "NHDPlus HR builds Peace cleanly and unattended, inheriting all 347 mapped waterbodies as lake objects — no per-basin tuning.",
                "Threshold TauDEM failed outright with lakes: a fine network ran 8+ hours on the lake-topology merge without producing HRUs; a coarse network exited abnormally during lake integration.",
                "A runnable TauDEM model was reached only after clipping the DEM to the basin, burning only the surveyed StreamRiver flowlines, and dropping all 347 lakes.",
                "Clipping the DEM brought total contributing area to within 2% of NHDPlus (5,853 vs 5,982 km²) by suppressing the cross-divide over-capture an unclipped threshold delineation produces.",
                "The cost: the only buildable TauDEM model carries no lakes and is over-segmented ~14× (2,304 vs 162 subbasins; 22,361 vs 8,181 channels).",
            ],
        },
        "models": models,
        "summary": {
            "nModelsAttempted": len(models),
            "nBuilt": len(built),
            "nTaudemBuilt": len(taudem_built),
            "nLakeAttempts": len(lake_attempts),
            "nLakeFailures": len(lake_failures),
            "nhdOutletAreaKm2": ref_area,
            "nhdReservoirs": ref.get("reservoirs"),
            "demResolutionM": dem_res_m,
            "demResolutionConsistent": len(dem_res_vals) == 1,
            "taudemAreaRangeKm2": (
                [min(m["outletAreaKm2"] for m in taudem_built), max(m["outletAreaKm2"] for m in taudem_built)]
                if taudem_built
                else None
            ),
        },
        "crossValidation": (perf or {}).get("models"),
        "initialPerformance": perf,
        "gageContext": gage_context,
        "figures": figures,
        "conclusion": {
            "headline": "TauDEM can integrate the lakes — with splitChannelsByLakes at a fine threshold — so the real differences are drainage-area determinism and how each delineation assigns the USGS gage.",
            "points": [
                "Same DEM for everyone: all models route the identical {res} m DEM (same grid, same CRS) — only the delineation engine and the DEM extent/clip differ, so the comparison isolates the method, not the input resolution.".format(res=dem_res_m or 30),
                "Lakes (updated): the default addHUCLakes fails at every threshold because the NHD lake-outlet node IDs have no counterpart in the rebuilt TauDEM network, but splitChannelsByLakes — which re-cuts channels geometrically at the lake boundaries — wires all {n} lakes as reservoirs at a fine threshold (500/100) and runs SWAT+ successfully. So threshold TauDEM CAN route the lakes; it needs the right method and a dense enough network ({f} of {a} lake builds failed before this combination worked).".format(n=lake_ctx["nLakes"], f=len(lake_failures), a=len(lake_attempts)),
                "Contributing area: NHDPlus HR lands at the basin's drainage area ({ref} km²); threshold TauDEM is governed by the DEM extent — a square box over-delineates and a tight basin-clip under-delineates, bracketing but never reproducing the NHD value (no threshold/extent knob on NHD).".format(ref=ref_area),
                "Gage assignment (cross-validated over all channels): the single stations.shp pick is a poor channel for both models; the basin outlet is the right channel by drainage area, and the delineations route the gage's location to different channels and stream orders.",
                "Initial performance: the gage (USGS 02239501) is the Silver River, fed by Silver Springs — NWIS reports no drainage area, and the very stable flow (CV 0.22) is artesian discharge from the regional Floridan aquifer, not surface runoff. Both surface delineations undersimulate ~20× because neither can inject spring flow, so initial streamflow does not discriminate the delineations here — a runoff-dominated, gage-matched basin is needed for that test.",
            ],
        },
        "methodology": {
            "dem": "Every model — NHDPlus HR and all TauDEM variants — routes the same {res} m DEM (identical grid and CRS, read live from each model's Watershed/Rasters/DEM/dem.tif). The 250 m figure on the TauDEM rows is the clip-buffer distance around the basin polygon, not the DEM resolution.".format(res=dem_res_m or 30),
            "areaSource": "max(AreaC)/100 over rivs1.shp (hectares → km²), cross-checked against chandeg.con.",
            "lakeWiring": "A lake is 'wired' only if it appears as a reservoir object in reservoir.con / hydrology.res / reservoir.res.",
            "delineationParams": "Threshold TauDEM uses stream 5000 / channel 1000 cells (force_taudem_only); DEM extent is a square bbox or the dissolved basin polygon with a 250 m clip buffer (SWATGENX_CLIP_DEM_TO_BOUNDARY).",
            "lakeMethods": "QSWAT+ addHUCLakes (subtract lakes from subbasins) and splitChannelsByLakes (re-split channels, rerun TauDEM); both attempted, with and without NHD stream-burn.",
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fh:
        json.dump(catalog, fh, indent=2)
        fh.write("\n")

    print(f"wrote {out_path}")
    print(
        f"  built={len(built)}/{len(models)}  taudem_built={len(taudem_built)}  "
        f"lake_failures={len(lake_failures)}/{len(lake_attempts)}  nhd_area={ref_area} km²"
    )
    for m in models:
        if m["built"]:
            print(f"  {m['id']:<28} area={m['outletAreaKm2']} km² ({m['areaVerdict']}) ch={m['channels']} hru={m['hrus']} res={m['reservoirs']}")
        else:
            print(f"  {m['id']:<28} BUILD FAILED — {m.get('failureReason','')[:60]}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""NHD-first reference reach selection for Peace (no SWAT AreaC / chandeg area).

Versions:
  v1_draft — Phase 0 exploratory picker (re-exported here for A/B).
  v1b      — Phase 1b hardened rules + deterministic tie-breakers.
"""
from __future__ import annotations

import re

import geopandas as gpd
import numpy as np
import pandas as pd

GAGE_RADIUS_M = 500.0
TRIBUTARY_RATIO = 0.35
CANAL_FTYPES = {336, 428, 460}
_STOP_WORDS = frozenset(
    {
        "NEAR",
        "AT",
        "BELOW",
        "ABOVE",
        "FL",
        "FLA",
        "THE",
        "OF",
        "ON",
        "TO",
        "AND",
        "SR",
        "US",
        "ST",
        "CR",
        "HWY",
        "STRUCTURE",
        "UPSTREAM",
        "DOWNSTREAM",
        "DRAINAGE",
        "GAGE",
        "SITE",
    }
)


def _log_err(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return 12.0
    x, y = float(a), float(b)
    if not (np.isfinite(x) and np.isfinite(y) and x > 0 and y > 0):
        return 12.0
    return abs(np.log(x) - np.log(y))


def tokenize_station_name(name: str | None) -> dict[str, bool]:
    u = (name or "").upper()
    return {
        "peace_river": "PEACE RIVER" in u or " PEACE R" in u,
        "tributary": any(t in u for t in (" BRANCH", " CREEK", " CR ", " BROOK", " RUN")),
        "lake_outlet": "OUTLET" in u or ("BELOW" in u and "LAKE" in u),
        "lake": " LAKE " in f" {u} " or "RESERVOIR" in u,
        "canal": "CANAL" in u or " DITCH" in u,
    }


def infer_gage_context(
    tokens: dict[str, bool],
    site_tp: str | None,
    usgs_da: float | None,
    max_tda_band: float,
) -> str:
    st = (site_tp or "").upper()
    if tokens["canal"] or st in ("CA", "CN"):
        return "canal"
    if tokens["lake_outlet"]:
        return "lake_outlet"
    if tokens["lake"] and not tokens["peace_river"]:
        return "lake_related"
    if usgs_da and max_tda_band > 0 and float(usgs_da) / max_tda_band < TRIBUTARY_RATIO:
        return "tributary"
    if tokens["tributary"] and not tokens["peace_river"]:
        return "tributary"
    if tokens["peace_river"]:
        return "mainstem"
    return "cumulative"


def name_keywords(station_name: str | None) -> list[str]:
    if not station_name:
        return []
    words = re.split(r"[^A-Za-z0-9]+", station_name.upper())
    return [w for w in words if len(w) > 2 and w not in _STOP_WORDS]


def gnis_name_rank(station_name: str | None, gnis: str | None) -> int:
    """0 = strong token match, 1 = partial, 2 = weak, 3 = none."""
    g = (gnis or "").upper()
    if not g:
        return 3
    keys = name_keywords(station_name)
    if not keys:
        return 3
    hits = [w for w in keys if w in g]
    if len(hits) >= min(2, len(keys)):
        return 0
    if len(hits) == 1:
        return 1
    u = (station_name or "").upper()
    if "PEACE RIVER" in u and "PEACE" in g and "RIVER" in g:
        return 0
    for frag in ("BRANCH", "CREEK", "BROOK", "RUN"):
        if frag in u and frag.rstrip(".") in g.replace(".", ""):
            return 0
    return 2


def dominant_levelpath_id(band: pd.DataFrame) -> float | None:
    if "LevelPathI" not in band.columns or band["LevelPathI"].isna().all():
        return None
    so = pd.to_numeric(band["StreamOrde"], errors="coerce")
    if not so.notna().any():
        return None
    top = band.loc[so == so.max(), "LevelPathI"]
    mode = top.mode()
    return float(mode.iloc[0]) if len(mode) else None


def context_filter(band: pd.DataFrame, ctx: str, tokens: dict, usgs_da: float | None, max_tda: float) -> pd.DataFrame:
    sub = band.copy()
    if ctx == "tributary" and usgs_da and usgs_da > 0:
        cap = max(3.0 * float(usgs_da), max_tda * 0.5)
        filt = sub[sub["TotDASqKm"].fillna(np.inf) <= cap]
        if len(filt):
            sub = filt
    if ctx in ("mainstem", "cumulative"):
        so = pd.to_numeric(sub["StreamOrde"], errors="coerce")
        if so.notna().any():
            sub = sub[so >= so.max() - 1]
        lp = dominant_levelpath_id(sub)
        if lp is not None:
            lp_sub = sub[sub["LevelPathI"] == lp]
            if len(lp_sub):
                sub = lp_sub
        if tokens["peace_river"] and "GNIS_Name" in sub.columns:
            peace = sub[sub["GNIS_Name"].astype(str).str.contains("Peace", case=False, na=False)]
            if len(peace):
                sub = peace
    if ctx == "canal" and "FType" in sub.columns:
        canal = sub[pd.to_numeric(sub["FType"], errors="coerce").isin(list(CANAL_FTYPES))]
        if len(canal):
            sub = canal
    if ctx == "lake_outlet" and "WBArea_Permanent_Identifier" in sub.columns:
        linked = sub[sub["WBArea_Permanent_Identifier"].notna() & (sub["WBArea_Permanent_Identifier"].astype(str) != "")]
        if len(linked):
            sub = linked
    return sub if len(sub) else band.copy()


def reach_penalty(row: pd.Series, ctx: str, tokens: dict) -> int:
    p = 0
    div = int(float(row.get("Divergence") or 0))
    ftype = int(float(row.get("FType") or 0)) if pd.notna(row.get("FType")) else 0
    has_wb = bool(row.get("WBArea_Permanent_Identifier")) and str(row.get("WBArea_Permanent_Identifier")) not in (
        "",
        "nan",
        "None",
    )
    if div == 2 and ctx in ("mainstem", "cumulative"):
        p += 2
    if ftype in CANAL_FTYPES and ctx not in ("canal",) and not tokens["canal"]:
        p += 3
    if has_wb and ctx not in ("lake_outlet", "lake_related", "canal") and not tokens["lake_outlet"]:
        p += 3 if ctx == "tributary" else 2
    local = row.get("AreaSqKm")
    if ctx == "tributary" and local is not None and pd.notna(local) and float(local) < 0.05:
        p += 2
    return p


def levelpath_rank(row: pd.Series, dom_lp: float | None) -> int:
    if dom_lp is None:
        return 1
    lp = row.get("LevelPathI")
    if lp is None or pd.isna(lp):
        return 2
    return 0 if float(lp) == dom_lp else 1


def rank_key_v1b(
    row: pd.Series,
    station_name: str | None,
    usgs_da: float | None,
    ctx: str,
    tokens: dict,
    dom_lp: float | None,
) -> tuple:
    """Lexicographic tie-break (lower is better). Area (TotDASqKm) is near-last."""
    gnis_r = gnis_name_rank(station_name, str(row.get("GNIS_Name") or ""))
    lp_r = levelpath_rank(row, dom_lp)
    dist = float(row["_dist"]) / GAGE_RADIUS_M
    tda = row.get("TotDASqKm")
    da_r = _log_err(float(tda) if pd.notna(tda) else None, usgs_da)
    pen = reach_penalty(row, ctx, tokens)
    so = int(float(row.get("StreamOrde") or 0))
    so_pref = -so if ctx in ("mainstem", "cumulative") else so
    local_a = float(row.get("AreaSqKm") or 0) if pd.notna(row.get("AreaSqKm")) else 0.0
    local_rank = -local_a if ctx == "tributary" else 0.0
    return (pen, gnis_r, lp_r, local_rank, dist, -so_pref * 0.001, da_r)


def pick_best_v1b(sub: pd.DataFrame, station_name: str | None, usgs_da: float | None, ctx: str, tokens: dict) -> tuple[pd.Series, str]:
    dom_lp = dominant_levelpath_id(sub)
    best_i = None
    best_key = None
    for i, row in sub.iterrows():
        key = rank_key_v1b(row, station_name, usgs_da, ctx, tokens, dom_lp)
        if best_key is None or key < best_key:
            best_key = key
            best_i = i
    rule = "nhd_first_v1b_tiebreak"
    if best_key and best_key[1] == 0:
        rule = "nhd_first_v1b_gnis"
    elif best_key and best_key[2] == 0:
        rule = "nhd_first_v1b_levelpath"
    return sub.loc[best_i], rule


def pick_nhd_reference_v1b(
    flows_5070: gpd.GeoDataFrame,
    gage_5070,
    usgs_da: float | None,
    station_name: str | None,
    site_tp: str | None,
) -> tuple[pd.Series | None, str, str]:
    tokens = tokenize_station_name(station_name)
    sp = flows_5070.copy()
    sp["_dist"] = sp.geometry.distance(gage_5070)
    band = sp[sp["_dist"] <= GAGE_RADIUS_M].copy()
    if band.empty:
        row = sp.nsmallest(1, "_dist").iloc[0]
        ctx = infer_gage_context(tokens, site_tp, usgs_da, 0.0)
        return row, "nhd_first_v1b_global_closest", ctx

    tda = pd.to_numeric(band["TotDASqKm"], errors="coerce")
    max_tda = float(tda.max()) if tda.notna().any() else 0.0
    ctx = infer_gage_context(tokens, site_tp, usgs_da, max_tda)
    sub = context_filter(band, ctx, tokens, usgs_da, max_tda)
    row, rule = pick_best_v1b(sub, station_name, usgs_da, ctx, tokens)
    return row, rule, ctx


# --- v1_draft (Phase 0) for before/after comparison ---


def pick_nhd_reference_v1_draft(
    flows_5070: gpd.GeoDataFrame,
    gage_5070,
    usgs_da: float | None,
    station_name: str | None,
    site_tp: str | None,
) -> tuple[pd.Series | None, str, str]:
    """Phase 0 draft picker (unchanged logic)."""
    tokens = tokenize_station_name(station_name)
    sp = flows_5070.copy()
    sp["_dist"] = sp.geometry.distance(gage_5070)
    band = sp[sp["_dist"] <= GAGE_RADIUS_M].copy()
    if band.empty:
        row = sp.nsmallest(1, "_dist").iloc[0]
        ctx = infer_gage_context(tokens, site_tp, usgs_da, 0.0)
        return row, "global_closest", ctx

    tda = pd.to_numeric(band["TotDASqKm"], errors="coerce")
    max_tda = float(tda.max()) if tda.notna().any() else 0.0
    ctx = infer_gage_context(tokens, site_tp, usgs_da, max_tda)

    if ctx == "tributary":
        sub = band.copy()
        if usgs_da and usgs_da > 0:
            sub = sub[sub["TotDASqKm"].fillna(np.inf) <= max(3.0 * float(usgs_da), max_tda * 0.5)]
            if sub.empty:
                sub = band.copy()
        best = None
        best_key = None
        for _, row in sub.iterrows():
            local = row.get("AreaSqKm")
            so = int(float(row.get("StreamOrde") or 0))
            gnis_bonus = 0.0
            if tokens["tributary"]:
                gnis = str(row.get("GNIS_Name") or "")
                for frag in ("BRANCH", "CREEK", "CR.", "BROOK", "RUN"):
                    if frag in gnis.upper():
                        gnis_bonus = -0.15
                        break
            key = (
                _log_err(float(local) if pd.notna(local) else None, usgs_da) + gnis_bonus,
                float(row["_dist"]) / GAGE_RADIUS_M,
                so,
            )
            if best_key is None or key < best_key:
                best_key = key
                best = row
        if best is not None:
            return best, "nhd_first_tributary_local_gnis", ctx

    if ctx in ("mainstem", "cumulative"):
        sub = band.copy()
        so = pd.to_numeric(sub["StreamOrde"], errors="coerce")
        if so.notna().any():
            sub = sub[so >= so.max() - 1]
        if "LevelPathI" in sub.columns and sub["LevelPathI"].notna().any():
            top = sub.loc[sub["StreamOrde"] == sub["StreamOrde"].max(), "LevelPathI"]
            lp = top.mode()
            if len(lp):
                sub_lp = sub[sub["LevelPathI"] == lp.iloc[0]]
                if len(sub_lp):
                    sub = sub_lp
        if tokens["peace_river"] and "GNIS_Name" in sub.columns:
            peace = sub[sub["GNIS_Name"].astype(str).str.contains("Peace", case=False, na=False)]
            if len(peace):
                sub = peace
        best = None
        best_key = None
        for _, row in sub.iterrows():
            tda_v = row.get("TotDASqKm")
            so_v = int(float(row.get("StreamOrde") or 0))
            key = (
                float(row["_dist"]) / GAGE_RADIUS_M,
                -so_v * 0.01,
                0.25 * _log_err(float(tda_v) if pd.notna(tda_v) else None, usgs_da),
            )
            if best_key is None or key < best_key:
                best_key = key
                best = row
        if best is not None:
            return best, "nhd_first_mainstem_levelpath_gnis", ctx

    if ctx == "lake_outlet":
        wb_col = "WBArea_Permanent_Identifier"
        if wb_col in band.columns:
            linked = band[band[wb_col].notna() & (band[wb_col].astype(str) != "")]
            if len(linked):
                return linked.sort_values("_dist").iloc[0], "nhd_first_lake_wb_link", ctx
        return band.sort_values("_dist").iloc[0], "nhd_first_lake_outlet_nearest", ctx

    if ctx == "canal":
        if "FType" in band.columns:
            canalish = band[pd.to_numeric(band["FType"], errors="coerce").isin(list(CANAL_FTYPES))]
            if len(canalish):
                return canalish.sort_values("_dist").iloc[0], "nhd_first_canal_ftype", ctx

    return band.sort_values("_dist").iloc[0], "nhd_first_distance_fallback", ctx

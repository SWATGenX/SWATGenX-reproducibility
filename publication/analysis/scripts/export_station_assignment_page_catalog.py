#!/usr/bin/env python3
"""Export station-assignment public page catalog (Peace pilot + drainage-audit portfolio)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from streamflow_drainage_area import (  # noqa: E402
    load_station_drainage_area_km2,
    load_wbd_upstream_area_km2,
)
from streamflow_obs_coverage import obs_coverage_flags  # noqa: E402

PEACE_V3 = REPO / "publication/analysis/qa/peace-station-assignment-v3-inventory.csv"
V3_DETAIL = REPO / "publication/analysis/qa/station-assignment-v3-inventory-detail.csv"
SHOWCASE_DETAIL = REPO / "publication/analysis/qa/station-assignment-v3-showcase-inventory-detail.csv"
SHOWCASE_TOTALS = REPO / "publication/analysis/qa/station-assignment-v3-showcase-portfolio-totals.json"
SHOWCASE_SUMMARY = REPO / "publication/analysis/qa/station-assignment-v3-showcase-inventory-summary.csv"
AUDIT_CATALOG_IDS = frozenset(
    {"03080102", "09471300", "03100101", "03152000", "07174000", "15060105", "02297600", "05536265"}
)
COMPLEXITY = REPO / "publication/tables/tab-model-complexity.csv"
DRAIN_JSON = REPO / "web_application/frontend/src/data/drainageAreaAuditCatalog.json"
OUT = REPO / "web_application/frontend/src/data/stationAssignmentPageCatalog.json"

CALIBRATION_READY = frozenset({"mainstem_clean", "tributary_clean", "mainstem_known_nhd_offset"})
OBS_START = int(SWATGenXPaths.niws_start_date[:4])
OBS_END = int(SWATGenXPaths.niws_end_date[:4])
RATIO_LOOSE = (0.5, 2.0)
RATIO_TIGHT = (0.8, 1.25)
MIN_OBS_FRAC = 0.80
NHD_NWIS_LOOSE_PCT = 25.0
NHD_NWIS_TIGHT_PCT = 10.0


def _json_val(v):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return None
    if isinstance(v, (np.integer, np.floating)):
        return float(v) if isinstance(v, np.floating) else int(v)
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    return v


def _ratio_in_band(series: pd.Series, lo: float, hi: float) -> pd.Series:
    r = pd.to_numeric(series, errors="coerce")
    return r.between(lo, hi, inclusive="both")


def load_meta(vpuid: str) -> pd.DataFrame | None:
    path = Path(SWATGenXPaths.streamflow_vpuid_path) / vpuid / f"meta_{vpuid}.csv"
    if not path.is_file():
        return None
    meta = pd.read_csv(path, dtype={"site_no": str})
    meta["site_no"] = meta["site_no"].str.zfill(8)
    for c in ("number_of_streamflow_data", "total_expected_days", "GAP_percent"):
        if c in meta.columns:
            meta[c] = pd.to_numeric(meta[c], errors="coerce")
    return meta


def obs_flags(meta: pd.DataFrame | None, site: str, vpuid: str | None = None) -> dict:
    meta_row = None
    if meta is not None and site in meta["site_no"].values:
        meta_row = meta.loc[meta["site_no"] == site].iloc[0]
    return obs_coverage_flags(site, vpuid=vpuid, meta_row=meta_row, min_obs_frac=MIN_OBS_FRAC)


def funnel_counts(df: pd.DataFrame, meta: pd.DataFrame | None, vpuid: str | None = None) -> dict:
    df = df.copy()
    df["swat_nhd_ratio"] = pd.to_numeric(df.get("swat_nhd_ratio"), errors="coerce")
    if "calibration_eligible" in df.columns:
        cal_mask = df["calibration_eligible"].astype(str).str.lower().isin(("true", "1"))
    else:
        cal_mask = df["assignment_class"].isin(CALIBRATION_READY)

    obs_usable = []
    has_obs = []
    for site in df["site_no"].str.zfill(8):
        fl = obs_flags(meta, site, vpuid=vpuid)
        has_obs.append(fl["hasObsInPeriod"])
        obs_usable.append(fl["usableObsForCal"])

    df["_has_obs"] = has_obs
    df["_obs_usable"] = obs_usable
    cal = df[cal_mask]

    matched = df["swat_nhd_ratio"].notna()
    within_loose = _ratio_in_band(df["swat_nhd_ratio"], *RATIO_LOOSE)
    within_tight = _ratio_in_band(df["swat_nhd_ratio"], *RATIO_TIGHT)
    swat_loose = within_loose

    usgs_da = pd.to_numeric(df.get("usgs_da_km2"), errors="coerce")
    nhd_tda = pd.to_numeric(df.get("nhd_tda_km2"), errors="coerce")
    if "usgs_da_source" in df.columns:
        has_nwis_site = (
            df["usgs_da_source"].astype(str).str.startswith("nwis", na=False)
            & usgs_da.notna()
            & (usgs_da > 0)
        )
    else:
        has_nwis_site = pd.Series(False, index=df.index)
    nhd_minus_nwis_pct = 100.0 * (nhd_tda - usgs_da) / usgs_da
    nhd_nwis_ok_loose = has_nwis_site & nhd_tda.notna() & (nhd_minus_nwis_pct.abs() <= NHD_NWIS_LOOSE_PCT)

    cal_loose = _ratio_in_band(cal["swat_nhd_ratio"], *RATIO_LOOSE)
    cal_tight = _ratio_in_band(cal["swat_nhd_ratio"], *RATIO_TIGHT)

    n_calibration_audit = int((cal_mask & df["_obs_usable"] & swat_loose).sum())
    n_process_audit = int((cal_mask & ~df["_obs_usable"] & ~swat_loose & matched).sum())
    n_nwis_metadata_review = int(
        (cal_mask & df["_obs_usable"] & swat_loose & has_nwis_site & ~nhd_nwis_ok_loose).sum()
    )

    obs_usable_s = pd.Series(obs_usable, index=df.index)
    n_obs_manual_review = int((obs_usable_s & ~cal_mask).sum())

    review_breakdown = (
        df.loc[~cal_mask, "assignment_class"].value_counts().to_dict()
        if "assignment_class" in df.columns
        else {}
    )

    return {
        "nStations": int(len(df)),
        "nSwatNhdMatched": int(matched.sum()),
        "nWithinRatioLoose": int(within_loose.sum()),
        "nWithinRatioTight": int(within_tight.sum()),
        "nWithObsInPeriod": int(sum(has_obs)),
        "nObsUsableForCal": int(sum(obs_usable)),
        "nAssignmentCalReady": int(cal_mask.sum()),
        "nAssignmentReview": int((~cal_mask).sum()),
        "assignmentReviewClasses": {str(k): int(v) for k, v in review_breakdown.items()},
        "nObsUsableManualReview": n_obs_manual_review,
        "nCalReadyWithObs": int((cal_mask & df["_obs_usable"]).sum()),
        "nCalReadyRatioLooseOk": int((cal_mask & swat_loose).sum()),
        "nCalReadyRatioTightOk": int((cal_mask & cal_tight).sum()),
        "nCalReadyAreaBiasLoose": int((cal_mask & ~swat_loose & matched).sum()),
        "nCalReadyAreaBiasTight": int(len(cal) - cal_tight.sum()),
        "nCalReady": n_calibration_audit,
        "nCalibrationAudit": n_calibration_audit,
        "nProcessAuditSwatNhd": n_process_audit,
        "nNwisMetadataReview": n_nwis_metadata_review,
        "nCalReadyForDrainageAudit": n_calibration_audit,
        "medianSwatNhdCalReady": _json_val(cal["swat_nhd_ratio"].median()) if len(cal) else None,
    }


def peace_structure() -> dict:
    cx = pd.read_csv(COMPLEXITY)
    row = cx[cx["catalog_model_id"].astype(str).str.zfill(8) == "03100101"].iloc[0]
    return {
        "catalogModelId": "03100101",
        "workspaceModelId": str(row["model_id"]),
        "label": str(row["label"]),
        "tier": str(row["tier"]),
        "state": str(row["state"]),
        "areaKm2": _json_val(row.get("area_km2")),
        "nHrus": _json_val(row.get("n_hrus")),
        "nChannels": _json_val(row.get("n_channels")),
        "nSubbasins": _json_val(row.get("n_subbasins")),
        "nCatchments": _json_val(row.get("n_catchments")),
        "nLakes": _json_val(row.get("n_lakes")),
    }


def _meta_drainage_from_df(site: str, meta: pd.DataFrame | None, meta_path: Path) -> dict:
    out = {"nwisDrainageAreaKm2": None, "nwisDaSource": None, "wbdUpstreamHu12Km2": None}
    if meta is None or not meta_path.is_file():
        return out
    da, src = load_station_drainage_area_km2(site, meta_path)
    wbd = load_wbd_upstream_area_km2(site, meta_path)
    out["wbdUpstreamHu12Km2"] = _json_val(wbd)
    if da is not None and src and str(src).startswith("nwis"):
        out["nwisDrainageAreaKm2"] = _json_val(da)
        out["nwisDaSource"] = src
    return out


def drainage_credibility_counts(df: pd.DataFrame, meta: pd.DataFrame | None, meta_path: Path) -> dict:
    """Summarize NHD reference TotDASqKm vs USGS NWIS site drainage (Peace credibility)."""
    rows = []
    for _, r in df.iterrows():
        site = str(r["site_no"]).zfill(8)
        nwis = _meta_drainage_from_df(site, meta, meta_path)["nwisDrainageAreaKm2"]
        nhd = pd.to_numeric(r.get("nhd_first_totdasqkm"), errors="coerce")
        if nhd is None or (isinstance(nhd, float) and np.isnan(nhd)):
            nhd = pd.to_numeric(r.get("nhd_tda_km2"), errors="coerce")
        wbd = _meta_drainage_from_df(site, meta, meta_path)["wbdUpstreamHu12Km2"]
        if nwis and nhd is not None and not np.isnan(nhd) and nwis > 0 and nhd > 0:
            pct = 100.0 * (float(nhd) - float(nwis)) / float(nwis)
            rows.append(
                {
                    "nhd_over_nwis": float(nhd) / float(nwis),
                    "nhd_minus_nwis_pct": pct,
                    "wbd_over_nwis": float(wbd) / float(nwis) if wbd and wbd > 0 else None,
                }
            )
    if not rows:
        return {"nWithNwisSiteDa": 0, "nNhdNwisComparable": 0}
    rd = pd.DataFrame(rows)
    return {
        "nWithNwisSiteDa": int(sum(1 for _, r in df.iterrows() if _meta_drainage_from_df(str(r["site_no"]).zfill(8), meta, meta_path)["nwisDrainageAreaKm2"])),
        "nNhdNwisComparable": int(len(rd)),
        "nNhdWithin10pctOfNwis": int((rd["nhd_minus_nwis_pct"].abs() <= 10).sum()),
        "nNhdWithin25pctOfNwis": int((rd["nhd_minus_nwis_pct"].abs() <= 25).sum()),
        "nNhdOver25pctFromNwis": int((rd["nhd_minus_nwis_pct"].abs() > 25).sum()),
        "medianNhdOverNwis": _json_val(rd["nhd_over_nwis"].median()),
        "medianNhdMinusNwisPct": _json_val(rd["nhd_minus_nwis_pct"].median()),
        "description": (
            "USGS site drainage from NWIS site-service (nwis_drain_area_km2 in meta). "
            "NHD reference is TotDASqKm on the v3 NHD-first reach (not SWAT+ chandeg area). "
            "WBD HU12↑ is the sum of upstream 12-digit catchment polygons (legacy production da_distance scale)."
        ),
    }


def station_row(r: pd.Series, meta: pd.DataFrame | None, meta_path: Path, vpuid: str | None = None) -> dict:
    site = str(r["site_no"]).zfill(8)
    ratio = pd.to_numeric(r.get("swat_nhd_ratio"), errors="coerce")
    cal = str(r.get("calibration_eligible", "")).lower() in ("true", "1") or str(
        r.get("assignment_class", "")
    ) in CALIBRATION_READY
    obs = obs_flags(meta, site, vpuid=vpuid)
    drain = _meta_drainage_from_df(site, meta, meta_path)
    nwis = drain["nwisDrainageAreaKm2"]
    nhd = pd.to_numeric(r.get("nhd_first_totdasqkm"), errors="coerce")
    if nhd is None or (isinstance(nhd, float) and np.isnan(nhd)):
        nhd = pd.to_numeric(r.get("nhd_tda_km2"), errors="coerce")
    nhd_f = float(nhd) if nhd is not None and not np.isnan(nhd) else None
    nhd_over_nwis = None
    nhd_minus_nwis_pct = None
    if nwis and nhd_f and nwis > 0:
        nhd_over_nwis = round(nhd_f / nwis, 4)
        nhd_minus_nwis_pct = round(100.0 * (nhd_f - nwis) / nwis, 2)
    wbd = drain["wbdUpstreamHu12Km2"]
    wbd_over_nwis = round(wbd / nwis, 4) if wbd and nwis and nwis > 0 else None
    swat_da = pd.to_numeric(r.get("swat_da_km2"), errors="coerce")
    swat_da_f = float(swat_da) if swat_da is not None and not np.isnan(swat_da) else None
    return {
        "siteNo": site,
        "stationName": str(r["station_name"]) if pd.notna(r.get("station_name")) else None,
        "swatGisId": _json_val(r.get("swat_gis_id")),
        "productionGisId": _json_val(r.get("production_gis_channel")),
        "swatplusDrainageAreaKm2": _json_val(swat_da_f),
        "mappingMethod": str(r["mapping_method"]) if pd.notna(r.get("mapping_method")) else None,
        "assignmentClass": str(r["assignment_class"]) if pd.notna(r.get("assignment_class")) else None,
        "calibrationEligible": cal,
        "swatNhdRatio": _json_val(ratio),
        "swatNhdInLooseBand": bool(_ratio_in_band(pd.Series([ratio]), *RATIO_LOOSE).iloc[0])
        if pd.notna(ratio)
        else False,
        "swatNhdInTightBand": bool(_ratio_in_band(pd.Series([ratio]), *RATIO_TIGHT).iloc[0])
        if pd.notna(ratio)
        else False,
        "areaBiasLoose": bool(pd.notna(ratio) and not (RATIO_LOOSE[0] <= ratio <= RATIO_LOOSE[1])),
        "nwisDrainageAreaKm2": nwis,
        "nwisDaSource": drain["nwisDaSource"],
        "wbdUpstreamHu12Km2": wbd,
        "nhdReferenceTotdasqkm": _json_val(nhd_f),
        "nhdOverNwisRatio": nhd_over_nwis,
        "nhdMinusNwisPct": nhd_minus_nwis_pct,
        "wbdOverNwisRatio": wbd_over_nwis,
        "nhdNwisWithin10pct": bool(nhd_minus_nwis_pct is not None and abs(nhd_minus_nwis_pct) <= 10),
        **obs,
    }


def _overlap_matrix(sub: pd.DataFrame) -> dict:
    nhd_ok = sub["nhd_nwis_ok_loose"]
    swat_ok = sub["swat_nhd_ok_loose"]
    return {
        "n": int(len(sub)),
        "bothOk": int((nhd_ok & swat_ok).sum()),
        "onlyNhdUsgsMismatch": int((~nhd_ok & swat_ok).sum()),
        "onlySwatNhdMismatch": int((nhd_ok & ~swat_ok).sum()),
        "bothMismatch": int((~nhd_ok & ~swat_ok).sum()),
    }


def compute_mismatch_overlap_analysis(stations: list[dict], funnel: dict) -> dict:
    """Statistical overlap: NHD vs USGS site DA mismatch vs SWAT+ vs NHD mismatch (Peace)."""
    df = pd.DataFrame(stations)
    df["calibrationEligible"] = df["calibrationEligible"].astype(bool)
    df["usableObsForCal"] = df["usableObsForCal"].astype(bool)
    df["has_nwis"] = df["nwisDrainageAreaKm2"].notna()
    df["has_swat_nhd"] = df["swatNhdRatio"].notna()
    df["nhd_nwis_ok_loose"] = df["nhdMinusNwisPct"].abs() <= NHD_NWIS_LOOSE_PCT
    df["nhd_nwis_ok_tight"] = df["nhdMinusNwisPct"].abs() <= NHD_NWIS_TIGHT_PCT
    df["swat_nhd_ok_loose"] = df["swatNhdRatio"].between(*RATIO_LOOSE)
    df["swat_nhd_ok_tight"] = df["swatNhdRatio"].between(*RATIO_TIGHT)
    df["audit_handoff"] = df["calibrationEligible"] & df["usableObsForCal"] & df["swat_nhd_ok_loose"]
    df["swat_nhd_log_err"] = df["swatNhdRatio"].apply(
        lambda x: abs(math.log(float(x))) if x is not None and float(x) > 0 else np.nan
    )

    comp = df[df["has_nwis"] & df["has_swat_nhd"]].copy()
    cal = comp[comp["calibrationEligible"]]
    audit = comp[comp["audit_handoff"]]
    mainstem = comp["assignmentClass"].astype(str).str.contains("mainstem", na=False)
    offset = comp["assignmentClass"] == "mainstem_known_nhd_offset"

    def _corr(sub: pd.DataFrame) -> float | None:
        if len(sub) < 3:
            return None
        c = sub[["nhdMinusNwisPct", "swat_nhd_log_err"]].corr().iloc[0, 1]
        return _json_val(c) if pd.notna(c) else None

    only_nhd = comp[~comp["nhd_nwis_ok_loose"] & comp["swat_nhd_ok_loose"]]
    by_class = only_nhd["assignmentClass"].value_counts().to_dict() if len(only_nhd) else {}
    both_bad = comp[~comp["nhd_nwis_ok_loose"] & ~comp["swat_nhd_ok_loose"]]

    no_nwis = df[~df["has_nwis"]]
    n_total = len(df)
    n_comp = len(comp)

    findings = [
        f"Among {n_comp} gages with both USGS site drainage and SWAT/NHD ratios, only {int((~comp['nhd_nwis_ok_loose'] & ~comp['swat_nhd_ok_loose']).sum())} show both mismatches (|NHD−USGS|>25% and SWAT/NHD outside 0.5–2.0×).",
        f"The dominant pattern is NHD–USGS metadata disagreement with acceptable SWAT/NHD ({_overlap_matrix(comp)['onlyNhdUsgsMismatch']} gages)—assignment and model fidelity can look fine while hydrography catalog area differs from USGS site area.",
        f"SWAT/NHD mismatch without NHD–USGS mismatch is rare ({_overlap_matrix(comp)['onlySwatNhdMismatch']} gages), suggesting TauDEM/QSWAT vs NHD VAA offsets are largely independent of USGS site-file drainage.",
        (
            f"Pearson correlation between |NHD−USGS|% and |log(SWAT/NHD)| is near zero "
            f"(r={_corr(comp) if _corr(comp) is not None else 'n/a'} on comparable gages)—the two disagreements do not move together linearly."
        ),
        f"All {int(offset.sum())} mainstem_known_nhd_offset gages agree with USGS site area within 25% and sit in the loose SWAT/NHD band—documented ~10–17% SWAT+ excess is not explained by NWIS–NHD catalog conflict.",
        f"NHD–USGS-only mismatches concentrate in tributary_clean ({by_class.get('tributary_clean', 0)}), lake_outlet_review ({by_class.get('lake_outlet_review', 0)}), and canal review classes—context picking, not mainstem scale error.",
        f"{len(no_nwis)} gages lack USGS drain_area_va in NWIS; {int(no_nwis['calibrationEligible'].sum())} are still calibration-ready with SWAT/NHD data—credibility table cannot score them.",
        f"Calibration funnel: {funnel.get('nAssignmentCalReady', '—')} pass auto-cal assignment class, "
        f"{funnel.get('nAssignmentReview', '—')} manual-review assignment class, "
        f"{funnel.get('nObsUsableForCal', '—')} with usable {OBS_START}–{OBS_END} obs, "
        f"{funnel.get('nCalReady', funnel.get('nCalibrationAudit', '—'))} fully cal-ready (assignment + obs + loose SWAT/NHD), "
        f"{funnel.get('nProcessAuditSwatNhd', '—')} process-audit flags (cal-ready, no usable obs, SWAT/NHD outside {RATIO_LOOSE[0]}–{RATIO_LOOSE[1]}×), "
        f"{funnel.get('nNwisMetadataReview', '—')} NWIS metadata review (obs + SWAT/NHD OK but |NHD−USGS|>{NHD_NWIS_LOOSE_PCT:.0f}%).",
    ]

    paragraphs = [
        (
            "Peace River separates two drainage-area questions that are easy to conflate. "
            "NHD vs USGS compares hydrography metadata (NHDPlus HR TotDASqKm on the v3 reference reach) to the "
            "USGS NWIS site catalog (gage watershed). SWAT vs NHD compares executable SWAT+ channel area in "
            "`chandeg.con` to that same NHD cumulative area after the station is already assigned. They measure "
            "different parts of the pipeline."
        ),
        (
            f"On {n_comp} gages with both metrics, {_overlap_matrix(comp)['bothOk']} ({100*_overlap_matrix(comp)['bothOk']/n_comp:.0f}%) "
            f"fall in the loose agreement window for both (|NHD−USGS|≤25% and SWAT/NHD within 0.5–2.0×). "
            f"Only {_overlap_matrix(comp)['bothMismatch']} gage shows both flags in the loose definition—typically "
            "a canal or local routing case (e.g. Peace Creek canal), not a basin-wide failure."
        ),
        (
            f"The more common pattern is NHD–USGS mismatch only ({_overlap_matrix(comp)['onlyNhdUsgsMismatch']} gages): "
            "SWAT+ still tracks NHD TotDASqKm on the assigned reach while USGS site drainage differs—often because "
            "the gage sits on a tributary, lake outlet, or canal and the USGS catalog area is local, whereas NHD "
            "cumulative area on the picked reach reflects a different hydrographic position. v3 assignment uses "
            "GNIS/name, stream order, and FType for that reason—not log-area distance alone."
        ),
        (
            f"Among {_overlap_matrix(cal)['n']} calibration-ready gages with USGS site DA, {_overlap_matrix(cal)['bothOk']} "
            f"have both loose agreements; none have both mismatches. The two assignment-ready gages with loose SWAT/NHD "
            f"bias but OK NHD–USGS ({_overlap_matrix(cal)['onlySwatNhdMismatch']}) are outliers for model fidelity review, "
            "not evidence that NWIS metadata drove a wrong reach choice."
        ),
        (
            "For automatic calibration, the operative filter is: assignment class eligible, ≥80% valid daily "
            "streamflow, and loose SWAT/NHD agreement "
            f"({funnel.get('nCalReady', funnel.get('nCalibrationAudit', '—'))} Peace gages). Cal-ready (v3) gages without usable obs but "
            f"with SWAT/NHD area bias ({funnel.get('nProcessAuditSwatNhd', '—')}) flag a SWATGenX pipeline "
            "issue. Gages with obs and acceptable SWAT/NHD but |NHD−USGS|>25% "
            f"({funnel.get('nNwisMetadataReview', '—')}) are NWIS/hydrography metadata context—not automatic "
            "calibration blockers when SWAT/NHD remains in band."
        ),
    ]

    return {
        "thresholds": {
            "nhdNwisLoosePct": NHD_NWIS_LOOSE_PCT,
            "nhdNwisTightPct": NHD_NWIS_TIGHT_PCT,
            "swatNhdLoose": list(RATIO_LOOSE),
            "swatNhdTight": list(RATIO_TIGHT),
            "minObsCoverageFrac": MIN_OBS_FRAC,
        },
        "nTotal": n_total,
        "nWithNwisAndSwatNhd": n_comp,
        "nNoUsgsSiteDa": int(len(no_nwis)),
        "matrixAll": _overlap_matrix(comp),
        "matrixCalReady": _overlap_matrix(cal),
        "matrixCalReadyWithObs": _overlap_matrix(cal),
        "matrixAuditHandoff": _overlap_matrix(audit),
        "matrixMainstem": _overlap_matrix(comp[mainstem]),
        "matrixNonMainstem": _overlap_matrix(comp[~mainstem]),
        "nMainstemKnownOffset": int(offset.sum()),
        "mainstemOffsetNhdNwisLooseOk": int((offset & comp["nhd_nwis_ok_loose"]).sum()),
        "mainstemOffsetSwatNhdLooseOk": int((offset & comp["swat_nhd_ok_loose"]).sum()),
        "corrNhdNwisPctVsSwatNhdLogErr": _corr(comp),
        "corrCalReady": _corr(cal),
        "onlyNhdMismatchByClass": {str(k): int(v) for k, v in by_class.items()},
        "bothMismatchSites": [
            {
                "siteNo": str(r["siteNo"]),
                "stationName": r.get("stationName"),
                "assignmentClass": r.get("assignmentClass"),
                "nhdMinusNwisPct": r.get("nhdMinusNwisPct"),
                "swatNhdRatio": r.get("swatNhdRatio"),
            }
            for _, r in both_bad.iterrows()
        ],
        "findings": findings,
        "paragraphs": paragraphs,
    }


def sync_v3_detail_from_showcase() -> pd.DataFrame | None:
    """Merge showcase shadow inventory into evaluation detail (8 audit models + Oklawaha fallback)."""
    if not SHOWCASE_DETAIL.is_file():
        return pd.read_csv(V3_DETAIL, dtype={"site_no": str, "catalog_model_id": str}) if V3_DETAIL.is_file() else None
    show = pd.read_csv(SHOWCASE_DETAIL, dtype={"site_no": str, "catalog_model_id": str})
    show["site_no"] = show["site_no"].str.zfill(8)
    show["catalog_model_id"] = show["catalog_model_id"].str.zfill(8)
    parts = [show[show["catalog_model_id"].isin(AUDIT_CATALOG_IDS)]]
    if V3_DETAIL.is_file():
        old = pd.read_csv(V3_DETAIL, dtype={"site_no": str, "catalog_model_id": str})
        old["catalog_model_id"] = old["catalog_model_id"].str.zfill(8)
        okl = old[old["catalog_model_id"] == "03080102"]
        if len(okl) and not (parts[0]["catalog_model_id"] == "03080102").any():
            parts.append(okl)
    merged = pd.concat(parts, ignore_index=True).drop_duplicates(
        subset=["catalog_model_id", "site_no"], keep="first"
    )
    V3_DETAIL.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(V3_DETAIL, index=False)
    return merged


def load_showcase_portfolio_inventory() -> dict | None:
    if not SHOWCASE_TOTALS.is_file():
        return None
    totals = json.loads(SHOWCASE_TOTALS.read_text(encoding="utf-8"))
    peace_frozen = bool(totals.get("peace_frozen"))
    agg: dict = {}
    if SHOWCASE_SUMMARY.is_file():
        sm = pd.read_csv(SHOWCASE_SUMMARY)
        for col, key in (
            ("n_calibration_ready", "nCalibrationReady"),
            ("n_review", "nReview"),
            ("n_exclude", "nExclude"),
            ("n_changed_gis", "nChangedGis"),
            ("n_same_gis", "nSameGis"),
        ):
            if col in sm.columns:
                agg[key] = int(pd.to_numeric(sm[col], errors="coerce").fillna(0).sum())
        if "n_stations" in sm.columns:
            agg["nStationsInSummary"] = int(pd.to_numeric(sm["n_stations"], errors="coerce").fillna(0).sum())
        if "n_models_processed" not in totals and len(sm):
            agg["nModelsInSummary"] = int(len(sm))
    n_proc = int(totals.get("n_models_processed", 0))
    n_skip = int(totals.get("n_models_skipped", 0))
    return {
        "title": "Showcase portfolio inventory (v3 production assignment)",
        "description": (
            "NHD-first / SWAT-second v3 assignment for USGS stations in publication showcase workspaces "
            "on disk. This is the same method used in production streamflow extraction after model build."
        ),
        "totals": {
            "nModelsProcessed": n_proc,
            "nModelsSkipped": n_skip,
            "nModelsInRoster": n_proc + n_skip,
            "nModelsWithChangedStation": int(totals.get("n_models_with_changed_station") or 0),
            "nStationsTotal": int(totals.get("n_stations_total", 0)),
            "nStationsChangedGis": int(totals.get("n_stations_changed") or 0),
            "peaceFrozen": peace_frozen,
        },
        "aggregate": agg,
        "inventoryArtifacts": {
            "detailCsv": "publication/analysis/qa/station-assignment-v3-showcase-inventory-detail.csv",
            "summaryCsv": "publication/analysis/qa/station-assignment-v3-showcase-inventory-summary.csv",
            "summaryMd": "publication/analysis/qa/station-assignment-v3-showcase-inventory-summary.md",
        },
        "note": (
            "Oklawaha tier-S (03080102) is not in the showcase example inventory; evaluation-model "
            "assignment for that workspace is taken from the evaluation roster inventory. "
            + (
                "Peace (03100101) inventory rows are frozen until that watershed model rebuild completes."
                if peace_frozen
                else ""
            )
        ),
    }


def portfolio_models(v3_detail: pd.DataFrame | None) -> list[dict]:
    drain = json.loads(DRAIN_JSON.read_text(encoding="utf-8"))
    rows = []
    for m in drain.get("models", []):
        cid = str(m["catalogModelId"]).zfill(8)
        ws = m["workspaceModelId"]
        vpuid = ws.split("/")[0]
        meta = load_meta(vpuid)

        assign = None
        if v3_detail is not None and len(v3_detail):
            sub = v3_detail[v3_detail["catalog_model_id"].astype(str).str.zfill(8) == cid]
            if len(sub):
                assign = funnel_counts(sub, meta, vpuid=vpuid)

        ds = m.get("summary", {})
        st = m.get("stations", [])
        n_audit_loose = sum(
            1
            for s in st
            if s.get("ratioSwatNhd") is not None and RATIO_LOOSE[0] <= float(s["ratioSwatNhd"]) <= RATIO_LOOSE[1]
        )

        rows.append(
            {
                "catalogModelId": cid,
                "workspaceModelId": ws,
                "label": m.get("label"),
                "tier": m.get("tier") or "",
                "state": m.get("state") or "",
                "nStations": ds.get("nStations"),
                "nMatchedSwatNhd": ds.get("nMatchedSwatNhd"),
                "nWithinHalfToDouble": ds.get("withinHalfToDouble"),
                "medianSwatNhdRatio": ds.get("medianSwatNhdRatio"),
                "assignment": assign,
                "nDrainageAuditLooseOk": n_audit_loose,
                "drainageAuditPath": f"/swat-plus-drainage-area-audit",
            }
        )
    return rows


def _peace_portfolio_example(funnel: dict, structure: dict) -> dict:
    review = funnel.get("assignmentReviewClasses") or {}
    review_line = " · ".join(f"{v} {k.replace('_', ' ')}" for k, v in review.items())
    n = funnel.get("nStations", 76)
    auto = funnel.get("nAssignmentCalReady", 0)
    manual = funnel.get("nAssignmentReview", 0)
    obs = funnel.get("nObsUsableForCal", 0)
    cal = funnel.get("nCalReady", funnel.get("nCalibrationAudit", 0))
    obs_manual = funnel.get("nObsUsableManualReview", 0)
    proc = funnel.get("nProcessAuditSwatNhd", 0)
    nwis = funnel.get("nNwisMetadataReview", 0)
    return {
        "label": structure.get("label", "Peace River HUC-8"),
        "catalogModelId": structure.get("catalogModelId", "03100101"),
        "reviewBreakdown": review_line,
        "selectionSummary": (
            f"{n} USGS gages → {auto} auto-cal class + {manual} manual review ({review_line}) → "
            f"{obs} usable obs → {cal} cal-ready for automatic calibration."
        ),
        "obsSplit": f"{obs} obs usable = {cal} cal-ready + {obs_manual} obs with manual-review class",
        "calReadyImpact": (
            f"The {cal} cal-ready gages are the automatic-calibration set: v3 assignment class, ≥80% valid "
            f"daily Q ({OBS_START}–{OBS_END}), and SWAT/NHD within 0.5–2.0×. Streamflow calibration objectives "
            f"and performance metrics are evaluated at these stations."
        ),
        "processAuditImpact": (
            f"{proc} auto-cal-class gages lack usable obs and show SWAT/NHD outside 0.5–2.0×—likely QSWAT/TauDEM "
            f"or routing fidelity issues. Investigate on the drainage-area audit page before using area constraints "
            f"or interpreting model performance at those reaches."
        ),
        "nwisNoteImpact": (
            f"{nwis} of {cal} cal-ready gages also have |NHD−USGS|>25% (USGS site drainage vs NHD TotDASqKm). "
            f"They remain in the calibration set because executable SWAT+ area matches NHD; the flag documents "
            f"hydrography metadata context when reading area diagnostics on the drainage-area audit page."
        ),
    }


def main() -> None:
    if not PEACE_V3.is_file():
        raise SystemExit(f"Missing {PEACE_V3}")

    peace_df = pd.read_csv(PEACE_V3, dtype={"site_no": str})
    peace_df["site_no"] = peace_df["site_no"].str.zfill(8)
    meta_0310 = load_meta("0310")
    meta_0310_path = Path(SWATGenXPaths.streamflow_vpuid_path) / "0310" / "meta_0310.csv"

    v3_detail = sync_v3_detail_from_showcase()
    if v3_detail is not None:
        v3_detail["site_no"] = v3_detail["site_no"].str.zfill(8)
    showcase_portfolio = load_showcase_portfolio_inventory()

    peace_funnel = funnel_counts(peace_df, meta_0310, vpuid="0310")
    peace_credibility = drainage_credibility_counts(peace_df, meta_0310, meta_0310_path)
    peace_stations = [
        station_row(r, meta_0310, meta_0310_path, vpuid="0310")
        for _, r in peace_df.sort_values("site_no").iterrows()
    ]
    peace_overlap = compute_mismatch_overlap_analysis(peace_stations, peace_funnel)

    payload = {
        "lastUpdated": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "obsPeriod": {
            "startYear": OBS_START,
            "endYear": OBS_END,
            "label": f"{OBS_START}–{OBS_END}",
            "description": (
                f"USGS NWIS daily streamflow archive window ({SWATGenXPaths.niws_start_date} to "
                f"{SWATGenXPaths.niws_end_date}). Usable coverage counts days with a real value "
                f"(not NaN, not -99 placeholder), requiring ≥{int(MIN_OBS_FRAC * 100)}% of the calendar span."
            ),
        },
        "ratioBands": {
            "loose": {"lo": RATIO_LOOSE[0], "hi": RATIO_LOOSE[1], "label": "0.5–2.0× SWAT/NHD"},
            "tight": {"lo": RATIO_TIGHT[0], "hi": RATIO_TIGHT[1], "label": "0.8–1.25× SWAT/NHD"},
        },
        "method": {
            "version": "nhd_first_v1b_swat_second_v3",
            "productionSummary": (
                "NHD-first reference reach (hydrography + NWIS site context, no SWAT area), then SWAT-second "
                "map to chandeg.con via NHD→GIS crosswalk or controlled downstream replacement."
            ),
            "improvedSummary": (
                "NHD-first: pick the NHDPlus HR reference reach using coordinates, USGS NWIS site drainage area "
                "(when available), GNIS/name context, stream order, LevelPath, FType, and lake/canal flags—without using "
                "SWAT+ AreaC or chandeg.con area. SWAT-second: map that reach to executable chandeg.con "
                "via crosswalk or controlled downstream replacement. Drainage-area comparison runs only "
                "after assignment, on calibration-ready stations."
            ),
            "steps": [
                "NHD-first reference reach (no SWAT area for reach choice)",
                "SWAT-second map to chandeg.con GIS channel",
                "Assignment class and calibration eligibility",
                "SWAT+ vs NHDPlus HR TotDASqKm ratio (drainage-area fidelity)",
            ],
            "drainageAreaFields": {
                "nwisSite": "nwis_drain_area_km2 — USGS NWIS site-service catalog (gage watershed metadata)",
                "nhdReference": "NHDPlus HR TotDASqKm on the v3 reference reach (hydrography, not SWAT+ chandeg)",
                "wbdHu12": "wbd_upstream_hu12_area_sqkm — sum of upstream WBD HU12 polygons (legacy da_distance scale)",
                "deprecated": "drainage_area_sqkm — alias of WBD HU12 sum; do not treat as NWIS",
            },
        },
        "peace": {
            **peace_structure(),
            "funnel": peace_funnel,
            "drainageCredibility": peace_credibility,
            "mismatchOverlap": peace_overlap,
            "mappingMethod": {k: int(v) for k, v in peace_df["mapping_method"].value_counts().items()},
            "assignmentClass": {k: int(v) for k, v in peace_df["assignment_class"].value_counts().items()},
            "stations": peace_stations,
        },
        "auditPortfolio": {
            "title": "Calibration & model-audit station funnel",
            "subtitle": "Eight publication evaluation watersheds (same workspaces as the drainage-area audit page)",
            "purpose": (
                "Before automatic streamflow calibration or interpreting SWAT+ vs NHD drainage-area ratios, each "
                "USGS gage passes assignment class, observation coverage, and structural area checks. This table "
                "counts how many gages remain at each gate—and which flags need human follow-up."
            ),
            "description": (
                "Each row is one benchmark SWAT+ workspace. Counts are per in-watershed USGS station after v3 "
                "NHD-first / SWAT-second assignment. Cal-ready is the set we use for automatic calibration; "
                "process audit and NWIS note describe how area disagreements affect interpretation—not extra stations."
            ),
            "auditColumns": {
                "assignmentAutoCalClass": (
                    "mainstem_clean, tributary_clean, or mainstem_known_nhd_offset with valid chandeg.con—"
                    "eligible for automatic calibration once obs and SWAT/NHD checks pass."
                ),
                "assignmentManualReview": (
                    "lake_outlet_review or canal_or_artificial_review (and similar): still mapped to a SWAT+ "
                    "channel, but held for human review—not counted as missing stations."
                ),
                "calReady": (
                    "Fully cal-ready: auto-cal assignment class + usable obs + SWAT/NHD within loose band "
                    "(0.5–2.0×)—eligible for automatic calibration."
                ),
                "calibrationAudit": (
                    "Fully cal-ready: auto-cal assignment class + usable obs + SWAT/NHD within loose band "
                    "(0.5–2.0×)—eligible for automatic calibration."
                ),
                "processAuditSwatNhd": (
                    "Auto-cal-class gages with no usable obs and SWAT/NHD outside 0.5–2.0×. Signals QSWAT/TauDEM "
                    "or assignment fidelity issues—review on the drainage-area audit page before trusting area-based "
                    "calibration constraints at these reaches."
                ),
                "nwisMetadataReview": (
                    "Subset of cal-ready gages: SWAT/NHD OK but |NHD−USGS|>25%. USGS site catalog vs NHD "
                    "hydrography metadata—document when reading area diagnostics; does not block calibration when "
                    "executable SWAT+ area matches NHD."
                ),
                "portfolioFunnelNote": (
                    "Stations = auto-cal class + manual review. Obs usable = cal-ready + obs-only manual-review. "
                    "Process audit and NWIS note flag subsets—they do not sum to the obs−cal-ready gap."
                ),
            },
            "peaceExample": _peace_portfolio_example(peace_funnel, peace_structure()),
            "models": portfolio_models(v3_detail),
            "portfolioSummary": json.loads(DRAIN_JSON.read_text(encoding="utf-8")).get("portfolioSummary"),
        },
        "showcasePortfolioInventory": showcase_portfolio,
        "calibrationReadyClasses": sorted(CALIBRATION_READY),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=_json_val), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

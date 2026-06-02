#!/usr/bin/env python3
"""Phase 1: Review Peace gages where production NHD pick ≠ NHD-first reference reach.

Does not change production assignment or stations.shp. Uses Phase 0 inventory and
enriched NHD HR only (no QSWAT AreaC / chandeg area for reference-reach choice).

Outputs:
  - peace-station-assignment-phase1-disagreement-review.csv
  - peace-station-assignment-phase1-disagreement-review.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    GAGE_RADIUS_M,
    HUC8,
    STATIONS_SHP,
    VPUID,
)
from inventory_peace_station_assignment_phase0 import (  # noqa: E402
    TRIBUTARY_RATIO,
    load_nhd_enriched_domain,
    tokenize_station_name,
)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

PHASE0_CSV = REPO / "publication/analysis/qa/peace-station-assignment-phase0-inventory.csv"
OUT_DIR = REPO / "publication/analysis/qa"
OUT_CSV = OUT_DIR / "peace-station-assignment-phase1-disagreement-review.csv"
OUT_MD = OUT_DIR / "peace-station-assignment-phase1-disagreement-review.md"

LAKE_NEAR_M = 150.0
CANAL_FTYPES = {336, 428, 460}


def _f(v) -> float | None:
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return None
    return float(v)


def reach_attrs(flows: pd.DataFrame, nhd_id: int | None) -> dict:
    empty = {
        "nhdplusid": nhd_id,
        "gnis_name": "",
        "totdasqkm": None,
        "areasqkm": None,
        "streamorde": None,
        "levelpathi": None,
        "ftype": None,
        "fcode": None,
        "divergence": None,
        "has_wb_link": False,
        "hydroseq": None,
    }
    if nhd_id is None or pd.isna(nhd_id):
        return empty
    sub = flows[flows["NHDPlusID"] == int(nhd_id)]
    if sub.empty:
        return empty
    r = sub.iloc[0]
    wb = r.get("WBArea_Permanent_Identifier")
    has_wb = wb is not None and str(wb).strip() not in ("", "nan", "None")
    return {
        "nhdplusid": int(nhd_id),
        "gnis_name": str(r.get("GNIS_Name") or "").strip(),
        "totdasqkm": _f(r.get("TotDASqKm")),
        "areasqkm": _f(r.get("AreaSqKm")),
        "streamorde": int(_f(r.get("StreamOrde")) or 0) if pd.notna(r.get("StreamOrde")) else None,
        "levelpathi": _f(r.get("LevelPathI")),
        "ftype": int(_f(r.get("FType"))) if pd.notna(r.get("FType")) else None,
        "fcode": int(_f(r.get("FCode"))) if pd.notna(r.get("FCode")) else None,
        "divergence": int(_f(r.get("Divergence"))) if pd.notna(r.get("Divergence")) else None,
        "has_wb_link": has_wb,
        "hydroseq": int(r["HydroSeq"]) if pd.notna(r.get("HydroSeq")) else None,
    }


def gnis_matches_station(station_name: str, gnis: str) -> str:
    """Return match class: strong, partial, none."""
    if not gnis or not station_name:
        return "none"
    u_name = station_name.upper()
    u_gnis = gnis.upper()
    if "PEACE RIVER" in u_name and "PEACE" in u_gnis and "RIVER" in u_gnis:
        return "strong"
    for frag in ("BRANCH", "CREEK", "CR.", "BROOK", "RUN", "CANAL"):
        if frag in u_name and frag.rstrip(".") in u_gnis.replace(".", ""):
            return "strong"
    name_words = [w for w in u_name.replace(",", " ").split() if len(w) > 3 and w not in ("NEAR", "BELOW", "LAKE", "RIVER")]
    hits = sum(1 for w in name_words if w in u_gnis)
    if hits >= 2:
        return "partial"
    if hits == 1:
        return "partial"
    return "none"


def is_mainstem_scale(tda: float | None, usgs_da: float | None, band_max_tda: float) -> bool:
    if tda is None or tda <= 0:
        return False
    if usgs_da and usgs_da > 0:
        if float(usgs_da) / float(tda) < TRIBUTARY_RATIO:
            return False
        if float(tda) > 3.0 * float(usgs_da) and band_max_tda > 0 and float(tda) >= 0.5 * band_max_tda:
            return True
    if band_max_tda > 0 and float(tda) >= 0.85 * band_max_tda:
        return True
    return False


def classify_disagreement(
    row: pd.Series,
    prod: dict,
    first: dict,
    band_max_tda: float,
    band_max_order: int,
) -> tuple[str, str, str]:
    """Return (reason_code, recommended_reference, reviewer_notes)."""
    usgs = _f(row.get("usgs_da_km2"))
    tokens = {
        "peace_river": bool(row.get("name_peace_river")),
        "tributary": bool(row.get("name_tributary")),
        "lake_outlet": bool(row.get("name_lake_outlet")),
        "lake": bool(row.get("name_lake")),
        "canal": bool(row.get("name_canal")),
    }
    ctx = str(row.get("nhd_first_context") or "")
    dist_lake = _f(row.get("dist_to_lake_m"))
    inside_wb = bool(row.get("inside_waterbody"))
    site_tp = str(row.get("site_tp_cd") or "").upper()

    prod_tda = prod["totdasqkm"]
    first_tda = first["totdasqkm"]
    prod_mainstem = is_mainstem_scale(prod_tda, usgs, band_max_tda)
    first_mainstem = is_mainstem_scale(first_tda, usgs, band_max_tda)

    first_gnis_match = gnis_matches_station(str(row.get("station_name") or ""), first["gnis_name"])
    prod_gnis_match = gnis_matches_station(str(row.get("station_name") or ""), prod["gnis_name"])

    no_crosswalk = pd.isna(row.get("nhd_first_gis_via_crosswalk"))

    lake_canal_flag = (
        tokens["lake_outlet"]
        or tokens["canal"]
        or (tokens["lake"] and not tokens["peace_river"])
        or ctx in ("lake_outlet", "lake_related", "canal")
        or site_tp in ("CA", "CN")
        or (
            dist_lake is not None
            and dist_lake <= LAKE_NEAR_M
            and (tokens["lake_outlet"] or tokens["lake"] or ctx.startswith("lake"))
        )
        or (inside_wb and (tokens["lake_outlet"] or tokens["lake"] or ctx.startswith("lake")))
        or prod["ftype"] in CANAL_FTYPES
        or first["ftype"] in CANAL_FTYPES
    )

    prod_on_wrong_scale = bool(
        usgs and prod_tda and prod_tda > 3.0 * usgs and first_tda and first_tda < prod_tda * 0.2
    )

    if tokens["tributary"] or ctx == "tributary":
        if prod_mainstem and not first_mainstem:
            return (
                "production_mainstem_wrong_for_tributary",
                "nhd_first",
                f"Production TDA {prod_tda:.1f} km² vs USGS {usgs:.1f}; NHD-first tributary GNIS match={first_gnis_match}.",
            )
        if prod_on_wrong_scale or (usgs and prod_tda and prod_tda > 3.0 * usgs and first_tda and first_tda <= 3.0 * usgs):
            return (
                "production_mainstem_wrong_for_tributary",
                "nhd_first",
                f"Production TDA {prod_tda:.1f} km² vs USGS {usgs:.1f}; NHD-first {first_tda:.1f} km² ({first['gnis_name']}).",
            )
        if prod_mainstem and first_mainstem:
            return (
                "nhd_first_uncertain",
                "manual_review",
                "Both reaches mainstem-scale; tributary name — verify local branch reach.",
            )

    if tokens["peace_river"] or (ctx in ("mainstem", "cumulative") and not tokens["tributary"]):
        on_mainstem_path = (
            first_mainstem
            or (first_tda and band_max_tda and first_tda >= 0.5 * band_max_tda)
            or first_gnis_match in ("strong", "partial")
        )
        if on_mainstem_path:
            return (
                "nhd_first_mainstem_correct",
                "nhd_first",
                "Peace/mainstem gage: NHD-first keeps level-path Peace reach; SWAT/NHD offset not hidden.",
            )

    if lake_canal_flag:
        if no_crosswalk:
            return (
                "no_valid_reference_reach",
                "manual_review",
                "Lake/canal context and no chandeg crosswalk — SWAT-second mapping required.",
            )
        return (
            "production_lake_or_canal_ambiguous",
            "nhd_first",
            f"Lake/canal context (dist_lake={dist_lake}, ctx={ctx}); production used da_distance.",
        )

    if usgs and prod_tda and first_tda:
        if prod_tda > 5 * usgs and first_tda <= 3 * usgs:
            return (
                "production_mainstem_wrong_for_tributary",
                "nhd_first",
                "Production reach TDA far above USGS DA; NHD-first local/tributary scale.",
            )

    if no_crosswalk:
        return (
            "no_valid_reference_reach",
            "manual_review",
            "NHD-first NHDPlusID has no chandeg crosswalk within 150 m — needs SWAT-second rule.",
        )

    if first_gnis_match == "strong" and prod_gnis_match == "none":
        return (
            "production_mainstem_wrong_for_tributary" if not prod_mainstem else "nhd_first_uncertain",
            "nhd_first",
            f"GNIS aligns with NHD-first ({first['gnis_name'][:40]}), not production.",
        )

    return (
        "nhd_first_uncertain",
        "manual_review",
        f"ctx={ctx}; prod_TDA={prod_tda}; first_TDA={first_tda}; band_max_TDA={band_max_tda:.1f}.",
    )


def prefix_attrs(attrs: dict, prefix: str) -> dict:
    return {f"{prefix}_{k}": v for k, v in attrs.items()}


def main() -> None:
    if not PHASE0_CSV.is_file():
        raise SystemExit(f"Run Phase 0 first: missing {PHASE0_CSV}")

    phase0 = pd.read_csv(PHASE0_CSV, dtype={"usgs_site_no": str})
    phase0["usgs_site_no"] = phase0["usgs_site_no"].str.zfill(8)
    disagree = phase0[~phase0["nhd_production_vs_first_same_id"]].copy()
    if disagree.empty:
        raise SystemExit("No disagreements in Phase 0 inventory.")

    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    print("Loading NHD HR for reach attributes…")
    flows_gdf, _, _ = load_nhd_enriched_domain(huc12s)
    flows = flows_gdf.drop(columns=["geometry"], errors="ignore")

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)
    stations_5070 = stations.to_crs(ALBERS)

    rows = []
    for _, row in disagree.iterrows():
        site = row["usgs_site_no"]
        st = stations_5070[stations_5070["site_no"] == site]
        if st.empty:
            continue
        gage = st.iloc[0].geometry
        sp = flows_gdf.to_crs(ALBERS)
        sp["_dist"] = sp.geometry.distance(gage)
        band = sp[sp["_dist"] <= GAGE_RADIUS_M]
        band_tda = pd.to_numeric(band["TotDASqKm"], errors="coerce")
        band_max_tda = float(band_tda.max()) if band_tda.notna().any() else 0.0
        band_order = pd.to_numeric(band["StreamOrde"], errors="coerce")
        band_max_order = int(band_order.max()) if band_order.notna().any() else 0

        prod = reach_attrs(flows, int(row["production_nhdplusid"]) if pd.notna(row["production_nhdplusid"]) else None)
        first = reach_attrs(flows, int(row["nhd_first_nhdplusid"]) if pd.notna(row["nhd_first_nhdplusid"]) else None)

        reason, ref_pick, notes = classify_disagreement(row, prod, first, band_max_tda, band_max_order)

        rec = {
            "usgs_site_no": site,
            "station_name": row.get("station_name"),
            "site_tp_cd": row.get("site_tp_cd"),
            "usgs_da_km2": row.get("usgs_da_km2"),
            "name_peace_river": row.get("name_peace_river"),
            "name_tributary": row.get("name_tributary"),
            "name_lake_outlet": row.get("name_lake_outlet"),
            "name_lake": row.get("name_lake"),
            "name_canal": row.get("name_canal"),
            "dist_to_lake_m": row.get("dist_to_lake_m"),
            "inside_waterbody": row.get("inside_waterbody"),
            "n_nhd_candidates_500m": row.get("n_nhd_candidates_500m"),
            "band_max_totdasqkm": band_max_tda,
            "band_max_streamorde": band_max_order,
            "nhd_first_context": row.get("nhd_first_context"),
            "nhd_first_pick_rule": row.get("nhd_first_pick_rule"),
            "production_nhd_pick_rule": row.get("production_nhd_pick_rule"),
            "production_gis_channel": row.get("production_gis_channel"),
            "production_nhdplusid": row.get("production_nhdplusid"),
            "nhd_first_nhdplusid": row.get("nhd_first_nhdplusid"),
            "nhd_first_gis_via_crosswalk": row.get("nhd_first_gis_via_crosswalk"),
            "nhd_first_crosswalk_snap_m": row.get("nhd_first_crosswalk_snap_m"),
            "gnis_match_production": gnis_matches_station(str(row.get("station_name") or ""), prod["gnis_name"]),
            "gnis_match_nhd_first": gnis_matches_station(str(row.get("station_name") or ""), first["gnis_name"]),
            "phase1_reason_code": reason,
            "phase1_recommended_reference": ref_pick,
            "phase1_reviewer_notes": notes,
        }
        rec.update(prefix_attrs(prod, "production"))
        rec.update(prefix_attrs(first, "nhd_first"))
        rows.append(rec)

    df = pd.DataFrame(rows).sort_values("usgs_site_no")
    df.to_csv(OUT_CSV, index=False)

    counts = df["phase1_reason_code"].value_counts()
    ref_counts = df["phase1_recommended_reference"].value_counts()

    md = [
        "# Peace Phase 1 — NHD-first disagreement review",
        "",
        f"**Scope:** {len(df)} gages where production `da_distance` NHD pick ≠ draft NHD-first reference reach "
        f"(of {len(phase0)} Peace stations). Production and `stations.shp` unchanged.",
        "",
        "## Reason code summary",
        "",
        "| Reason code | Count | Meaning |",
        "|-------------|------:|---------|",
        "| `production_mainstem_wrong_for_tributary` | "
        f"{counts.get('production_mainstem_wrong_for_tributary', 0)} | Gage is tributary/local scale; production picked mainstem-scale reach |",
        "| `production_lake_or_canal_ambiguous` | "
        f"{counts.get('production_lake_or_canal_ambiguous', 0)} | Lake/canal/outlet structure; production area match unreliable |",
        "| `nhd_first_mainstem_correct` | "
        f"{counts.get('nhd_first_mainstem_correct', 0)} | Mainstem Peace gage; keep NHD-first reach despite SWAT/NHD offset |",
        "| `nhd_first_uncertain` | "
        f"{counts.get('nhd_first_uncertain', 0)} | Draft rules need manual confirmation |",
        "| `no_valid_reference_reach` | "
        f"{counts.get('no_valid_reference_reach', 0)} | No confident reference until SWAT-second / mapping |",
        "",
        "## Recommended reference (preliminary)",
        "",
    ]
    for ref, n in ref_counts.items():
        md.append(f"- **{ref}:** {n}")
    md.extend(
        [
            "",
            "## Anchor cases (locked interpretation)",
            "",
            "| USGS | Reason | Recommendation |",
            "|------|--------|----------------|",
        ]
    )
    for site in ("02294760", "02294650"):
        sub = df[df["usgs_site_no"] == site]
        if not sub.empty:
            r = sub.iloc[0]
            md.append(
                f"| {site} | {r['phase1_reason_code']} | {r['phase1_recommended_reference']} |"
            )

    md.extend(
        [
            "",
            "## Full disagreement table",
            "",
            f"See `{OUT_CSV.name}` for production vs NHD-first attributes (GNIS, TDA, FType, WB link, stream order, LevelPath).",
            "",
            "## Next step (Phase 2)",
            "",
            "1. Harden `pick_nhd_reference_nhd_first` using accepted reason codes.",
            "2. SWAT-second mapping for reaches without chandeg crosswalk.",
            "3. v3 Peace inventory with assignment class + calibration eligibility.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_CSV} ({len(df)} rows)")
    print(f"Wrote {OUT_MD}")
    print("Reason codes:\n", counts.to_string())
    print("Recommended reference:\n", ref_counts.to_string())


if __name__ == "__main__":
    main()

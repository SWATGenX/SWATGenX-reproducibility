#!/usr/bin/env python3
"""Phase 1b: Harden NHD-first reference reach rules; compare v1_draft vs v1b vs production.

No production or stations.shp changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "publication/analysis/scripts"))

from compare_peace_drainage_area_txtinout_vs_nhd import (  # noqa: E402
    ALBERS,
    CONUS_STATIONS_CSV,
    HUC8,
    STATIONS_SHP,
    VPUID,
    load_station_names,
    load_usgs_da_km2,
    pick_nhd_reach,
)
from inventory_peace_station_assignment_phase0 import load_nhd_enriched_domain  # noqa: E402
from peace_nhd_first_pick import pick_nhd_reference_v1_draft, pick_nhd_reference_v1b  # noqa: E402
from peace_nhd_first_pick import tokenize_station_name  # noqa: E402
from review_peace_nhd_first_disagreements_phase1 import (  # noqa: E402
    classify_disagreement,
    gnis_matches_station,
    reach_attrs,
)


def classify_v1b_after_hardening(
    station_name: str,
    v1b_ctx: str,
    v1b_rule: str,
    prod: dict,
    v1b: dict,
    usgs_da: float | None,
    band_max_tda: float,
    pseudo_row: pd.Series,
) -> tuple[str, str, str]:
    """Re-classify former Phase-1 uncertain rows after v1b GNIS/levelpath tie-break."""
    tokens = tokenize_station_name(station_name)
    gnis = gnis_matches_station(station_name, v1b.get("gnis_name"))
    prod_tda = prod.get("totdasqkm")
    v1b_tda = v1b.get("totdasqkm")

    if "gnis" in v1b_rule and gnis == "strong":
        if tokens["peace_river"] or v1b_ctx in ("mainstem", "cumulative"):
            return (
                "nhd_first_mainstem_correct",
                "nhd_first",
                "v1b GNIS/level-path mainstem lock; preserves QSWAT/NHD offset visibility.",
            )
        if v1b_ctx == "tributary" or tokens["tributary"]:
            return (
                "nhd_first_tributary_gnis_locked",
                "nhd_first",
                "v1b GNIS keyword match on tributary reach; production da_distance sibling.",
            )

    if "levelpath" in v1b_rule and v1b_ctx == "tributary":
        if usgs_da and prod_tda and v1b_tda and prod_tda > 2.0 * usgs_da and v1b_tda <= 2.5 * usgs_da:
            return (
                "production_mainstem_wrong_for_tributary",
                "nhd_first",
                f"v1b level-path tributary TDA {v1b_tda:.1f} vs production {prod_tda:.1f} km².",
            )

    return classify_disagreement(pseudo_row, prod, v1b, band_max_tda, 0)
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

PHASE0_CSV = REPO / "publication/analysis/qa/peace-station-assignment-phase0-inventory.csv"
PHASE1_CSV = REPO / "publication/analysis/qa/peace-station-assignment-phase1-disagreement-review.csv"
OUT_DIR = REPO / "publication/analysis/qa"
OUT_CSV = OUT_DIR / "peace-station-assignment-phase1b-comparison.csv"
OUT_MD = OUT_DIR / "peace-station-assignment-phase1b-comparison.md"


def load_conus_index() -> pd.DataFrame | None:
    if not CONUS_STATIONS_CSV.is_file():
        return None
    df = pd.read_csv(CONUS_STATIONS_CSV, dtype={"site_no": str})
    return df.set_index("site_no")


def main() -> None:
    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    names = load_station_names()
    conus_idx = load_conus_index()

    print("Loading NHD HR…")
    flows_gdf, _, _ = load_nhd_enriched_domain(huc12s)
    flows_5070 = flows_gdf.to_crs(ALBERS)
    flows = flows_gdf.drop(columns=["geometry"], errors="ignore")

    stations = gpd.read_file(STATIONS_SHP)
    stations["site_no"] = stations["site_no"].astype(str).str.zfill(8)

    rows = []
    for _, st in stations.iterrows():
        site = st["site_no"]
        nm = names.get(site, "")
        gage = gpd.GeoSeries([st.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        usgs_da, _ = load_usgs_da_km2(site)
        site_tp = None
        if conus_idx is not None and site in conus_idx.index:
            cr = conus_idx.loc[site]
            if isinstance(cr, pd.DataFrame):
                cr = cr.iloc[0]
            site_tp = cr.get("site_tp_cd")

        prod_row, prod_rule, _ = pick_nhd_reach(flows_5070, gage, usgs_da)
        draft_row, draft_rule, draft_ctx = pick_nhd_reference_v1_draft(flows_5070, gage, usgs_da, nm, str(site_tp or ""))
        v1b_row, v1b_rule, v1b_ctx = pick_nhd_reference_v1b(flows_5070, gage, usgs_da, nm, str(site_tp or ""))

        def nid(row):
            if row is None or pd.isna(row.get("NHDPlusID")):
                return None
            return int(row["NHDPlusID"])

        prod_id = nid(prod_row)
        draft_id = nid(draft_row)
        v1b_id = nid(v1b_row)

        rows.append(
            {
                "usgs_site_no": site,
                "station_name": nm,
                "production_nhdplusid": prod_id,
                "v1_draft_nhdplusid": draft_id,
                "v1b_nhdplusid": v1b_id,
                "production_pick_rule": prod_rule,
                "v1_draft_pick_rule": draft_rule,
                "v1b_pick_rule": v1b_rule,
                "v1_draft_context": draft_ctx,
                "v1b_context": v1b_ctx,
                "prod_eq_draft": prod_id == draft_id if prod_id and draft_id else False,
                "prod_eq_v1b": prod_id == v1b_id if prod_id and v1b_id else False,
                "draft_eq_v1b": draft_id == v1b_id if draft_id and v1b_id else False,
                "v1b_changed_from_draft": draft_id != v1b_id if draft_id and v1b_id else False,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    n = len(df)
    prod_eq_draft = int(df["prod_eq_draft"].sum())
    prod_eq_v1b = int(df["prod_eq_v1b"].sum())
    draft_eq_v1b = int(df["draft_eq_v1b"].sum())
    v1b_changed = int(df["v1b_changed_from_draft"].sum())

    disagree_prod_draft = df[~df["prod_eq_draft"]]
    disagree_prod_v1b = df[~df["prod_eq_v1b"]]

    phase1_uncertain_sites = set()
    if PHASE1_CSV.is_file():
        p1 = pd.read_csv(PHASE1_CSV, dtype={"usgs_site_no": str})
        p1["usgs_site_no"] = p1["usgs_site_no"].str.zfill(8)
        phase1_uncertain_sites = set(
            p1.loc[p1["phase1_reason_code"] == "nhd_first_uncertain", "usgs_site_no"]
        )

    review_rows = []
    for site in sorted(phase1_uncertain_sites):
        r = df[df["usgs_site_no"] == site]
        if r.empty:
            continue
        r = r.iloc[0]
        st_row = stations[stations["site_no"] == site].iloc[0]
        gage = gpd.GeoSeries([st_row.geometry], crs=stations.crs).to_crs(ALBERS).iloc[0]
        sp = flows_5070.copy()
        sp["_dist"] = sp.geometry.distance(gage)
        band = sp[sp["_dist"] <= 500]
        band_tda = pd.to_numeric(band["TotDASqKm"], errors="coerce")
        band_max_tda = float(band_tda.max()) if band_tda.notna().any() else 0.0
        band_order = int(pd.to_numeric(band["StreamOrde"], errors="coerce").max())

        prod = reach_attrs(flows, int(r["production_nhdplusid"]) if pd.notna(r["production_nhdplusid"]) else None)
        v1b = reach_attrs(flows, int(r["v1b_nhdplusid"]) if pd.notna(r["v1b_nhdplusid"]) else None)

        p0 = pd.read_csv(PHASE0_CSV, dtype={"usgs_site_no": str})
        p0["usgs_site_no"] = p0["usgs_site_no"].str.zfill(8)
        p0r = p0[p0["usgs_site_no"] == site].iloc[0] if site in set(p0["usgs_site_no"]) else None
        pseudo = p0r if p0r is not None else r
        usgs_da = float(pseudo["usgs_da_km2"]) if pd.notna(pseudo.get("usgs_da_km2")) else None
        reason, ref, notes = classify_v1b_after_hardening(
            r["station_name"],
            r["v1b_context"],
            r["v1b_pick_rule"],
            prod,
            v1b,
            usgs_da,
            band_max_tda,
            pseudo,
        )

        review_rows.append(
            {
                "usgs_site_no": site,
                "station_name": r["station_name"],
                "phase1_was_uncertain": True,
                "production_nhdplusid": r["production_nhdplusid"],
                "v1_draft_nhdplusid": r["v1_draft_nhdplusid"],
                "v1b_nhdplusid": r["v1b_nhdplusid"],
                "v1b_changed_from_draft": r["v1b_changed_from_draft"],
                "v1b_pick_rule": r["v1b_pick_rule"],
                "gnis_match_v1b": gnis_matches_station(r["station_name"], v1b["gnis_name"]),
                "phase1b_reason_code": reason,
                "phase1b_recommended_reference": ref,
                "phase1b_notes": notes,
            }
        )

    review_df = pd.DataFrame(review_rows)
    review_path = OUT_DIR / "peace-station-assignment-phase1b-uncertain-resolved.csv"
    review_df.to_csv(review_path, index=False)

    still_uncertain = 0
    if len(review_df):
        still_uncertain = int((review_df["phase1b_reason_code"] == "nhd_first_uncertain").sum())

    md = [
        "# Peace Phase 1b — NHD-first rule hardening",
        "",
        "Compares **production** (`da_distance`), **v1_draft** (Phase 0), and **v1b** (hardened tie-breakers).",
        "Reference reach selection uses **NHD attributes only** — not QSWAT `AreaC` or `chandeg` area.",
        "",
        "## All 76 stations",
        "",
        f"| Comparison | Same NHDPlusID | Different |",
        f"|------------|---------------:|----------:|",
        f"| Production vs v1_draft | {prod_eq_draft} | {n - prod_eq_draft} |",
        f"| Production vs **v1b** | **{prod_eq_v1b}** | **{n - prod_eq_v1b}** |",
        f"| v1_draft vs v1b | {draft_eq_v1b} | {v1b_changed} changed by v1b |",
        "",
        f"Production vs v1_draft disagreements: **{len(disagree_prod_draft)}** (Phase 0 baseline).",
        f"Production vs v1b disagreements: **{len(disagree_prod_v1b)}**.",
        "",
        "## Phase 1 uncertain cases (14)",
        "",
        f"| Outcome | Count |",
        f"|---------|------:|",
        f"| Was `nhd_first_uncertain` in Phase 1 | {len(phase1_uncertain_sites)} |",
        f"| Still `nhd_first_uncertain` after v1b | {still_uncertain} |",
        f"| Locked tributary via GNIS (`nhd_first_tributary_gnis_locked`) | "
        f"{int((review_df['phase1b_reason_code'] == 'nhd_first_tributary_gnis_locked').sum()) if len(review_df) else 0} |",
        f"| Mainstem GNIS lock | "
        f"{int((review_df['phase1b_reason_code'] == 'nhd_first_mainstem_correct').sum()) if len(review_df) else 0} |",
        f"| Resolved to other reason codes | {len(review_df) - still_uncertain} |",
        "",
        f"Detail: `{review_path.name}`",
        "",
        "## v1b tie-break order (lexicographic)",
        "",
        "1. Penalize divergence / canal FType / lake-interior WB link (unless name/context supports)",
        "2. GNIS keyword match to station name",
        "3. Dominant LevelPath on mainstem context",
        "4. Distance to gage geometry",
        "5. Stream order preference (high on mainstem, low on tributary)",
        "6. `TotDASqKm` vs NWIS DA (last resort only)",
        "",
        "## Changed reference reaches (v1b ≠ v1_draft)",
        "",
    ]
    changed = df[df["v1b_changed_from_draft"]].sort_values("usgs_site_no")
    for _, r in changed.head(20).iterrows():
        md.append(
            f"- **{r['usgs_site_no']}** {str(r['station_name'])[:45]} — "
            f"draft `{r['v1_draft_nhdplusid']}` → v1b `{r['v1b_nhdplusid']}` ({r['v1b_pick_rule']})"
        )
    if len(changed) > 20:
        md.append(f"- … {len(changed) - 20} more in `{OUT_CSV.name}`")

    md.extend(
        [
            "",
            "## Next: Phase 2 SWAT-second mapping",
            "",
            "Map locked v1b `NHDPlusID` → `gis_id` (crosswalk / downstream replacement).",
            "",
            f"Full table: `{OUT_CSV.name}`",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {review_path}")
    print(f"76 stations: prod=v1b {prod_eq_v1b}, prod=draft {prod_eq_draft}, v1b changed from draft {v1b_changed}")
    print(f"Phase1 uncertain: {len(phase1_uncertain_sites)} -> still uncertain {still_uncertain}")


if __name__ == "__main__":
    main()

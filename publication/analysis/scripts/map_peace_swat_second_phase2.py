#!/usr/bin/env python3
"""Phase 2: SWAT-second mapping for locked v1b NHD-first reference reaches (Peace HUC-8).

NHD reference reach is fixed from Phase 1b (no AreaC/chandeg for reach choice).
Maps NHDPlusID → SWAT gis_id via crosswalk and downstream HydroSeq walk.

Does not change production assignment or stations.shp.
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
    HUC8,
    STATIONS_SHP,
    TXTINOUT,
    VPUID,
    load_station_names,
    parse_chandeg,
)
from inventory_peace_station_assignment_phase0 import SNAP_M, load_nhd_enriched_domain  # noqa: E402
from review_peace_nhd_first_disagreements_phase1 import reach_attrs  # noqa: E402
from investigate_peace_drainage_area_upstream import (  # noqa: E402
    parse_chandeg_gis_points,
    snap_gis_to_nhd_orig,
)
from peace_nhd_first_pick import CANAL_FTYPES  # noqa: E402
from taudem_threshold_from_huc8 import derive_huc12_list_for_huc8  # noqa: E402

PHASE1B_CSV = REPO / "publication/analysis/qa/peace-station-assignment-phase1b-comparison.csv"
OUT_DIR = REPO / "publication/analysis/qa"
OUT_CSV = OUT_DIR / "peace-station-assignment-phase2-swat-map.csv"
OUT_MD = OUT_DIR / "peace-station-assignment-phase2-swat-map.md"
MAX_DOWNSTREAM_STEPS = 30
MAINSTEM_OFFSET_RATIO_LO = 1.05
MAINSTEM_OFFSET_RATIO_HI = 1.25


def normalize_reference_class(ctx: str) -> str:
    c = (ctx or "").strip().lower()
    if c in ("mainstem", "cumulative"):
        return "mainstem"
    if c == "tributary":
        return "tributary"
    if c == "lake_outlet":
        return "lake_outlet"
    if c == "canal":
        return "canal"
    if c == "lake_related":
        return "lake_related"
    return c or "review"


def build_hydroseq_maps(flows: pd.DataFrame) -> tuple[dict[int, dict], dict[int, int]]:
    """hs -> row dict; nhd_id -> hydroseq."""
    hs_map: dict[int, dict] = {}
    nhd_to_hs: dict[int, int] = {}
    for _, r in flows.iterrows():
        if pd.isna(r.get("HydroSeq")):
            continue
        hs = int(r["HydroSeq"])
        nid = int(r["NHDPlusID"]) if pd.notna(r.get("NHDPlusID")) else None
        hs_map[hs] = r.to_dict()
        if nid is not None:
            nhd_to_hs[nid] = hs
    return hs_map, nhd_to_hs


def downstream_hydroseq_chain(start_hs: int, hs_map: dict[int, dict], *, max_steps: int) -> list[int]:
    chain = [start_hs]
    cur = start_hs
    for _ in range(max_steps):
        row = hs_map.get(cur)
        if not row:
            break
        dn = row.get("DnHydroSeq")
        if dn is None or pd.isna(dn):
            break
        dn = int(dn)
        if dn == 0 or dn == cur:
            break
        chain.append(dn)
        cur = dn
    return chain


def build_nhd_to_gis(xw: pd.DataFrame, chandeg_gis: set[int]) -> dict[int, list[tuple[int, float]]]:
    out: dict[int, list[tuple[int, float]]] = {}
    for _, r in xw.iterrows():
        nid = r.get("nhdplusid_crosswalk")
        gis = r.get("gis_id")
        if pd.isna(nid) or pd.isna(gis):
            continue
        nid = int(nid)
        gis = int(gis)
        snap = float(r.get("snap_dist_m", 999))
        if snap > SNAP_M:
            continue
        out.setdefault(nid, []).append((gis, snap))
    for nid in out:
        out[nid] = sorted(out[nid], key=lambda t: t[1])
    return out


def pick_gis_for_nhd(
    nhd_id: int,
    nhd_to_gis: dict[int, list[tuple[int, float]]],
    chandeg_gis: set[int],
) -> tuple[int | None, float | None]:
    cands = nhd_to_gis.get(nhd_id, [])
    for gis, snap in cands:
        if gis in chandeg_gis:
            return gis, snap
    return None, None


def map_reference_to_swat(
    ref_nhd: int,
    hs_map: dict[int, dict],
    nhd_to_hs: dict[int, int],
    nhd_to_gis: dict[int, list[tuple[int, float]]],
    chandeg_gis: set[int],
    ref_class: str,
    ref_row: dict,
) -> tuple[int | None, str, int, int | None]:
    """Return (gis_id, mapping_method, downstream_steps, mapped_nhd_id)."""
    gis, _ = pick_gis_for_nhd(ref_nhd, nhd_to_gis, chandeg_gis)
    if gis is not None:
        return gis, "exact_crosswalk", 0, ref_nhd

    start_hs = nhd_to_hs.get(ref_nhd)
    if start_hs is None:
        return None, "missing", 0, None

    chain = downstream_hydroseq_chain(start_hs, hs_map, max_steps=MAX_DOWNSTREAM_STEPS)
    for step, hs in enumerate(chain):
        if step == 0:
            continue
        row = hs_map.get(hs)
        if not row:
            continue
        nid = int(row["NHDPlusID"]) if pd.notna(row.get("NHDPlusID")) else None
        if nid is None:
            continue
        gis, _ = pick_gis_for_nhd(nid, nhd_to_gis, chandeg_gis)
        if gis is not None:
            method = "downstream_replacement"
            if ref_class in ("lake_outlet", "lake_related") or ref_row.get("has_wb_link"):
                method = "lake_outlet_replacement"
            return gis, method, step, nid

    return None, "missing", len(chain) - 1, None


def assignment_class_for_row(
    ref_class: str,
    mapping_method: str,
    chandeg_present: bool,
    ratio: float | None,
    ref_row: dict,
    downstream_steps: int,
) -> str:
    if not chandeg_present or mapping_method == "missing":
        return "exclude_from_auto_calibration" if mapping_method == "missing" else "missing_output_channel"

    ftype = ref_row.get("ftype")
    div = ref_row.get("divergence")

    if ref_class == "canal":
        return "canal_or_artificial_review"

    if ref_class in ("lake_outlet", "lake_related"):
        return "lake_outlet_review"

    if mapping_method == "lake_outlet_replacement":
        return "lake_outlet_review"

    if div == 2 and ref_class == "mainstem":
        return "assignment_ambiguous"

    if downstream_steps > 5:
        return "assignment_ambiguous"

    if ref_class == "mainstem" and ratio is not None:
        if MAINSTEM_OFFSET_RATIO_LO <= ratio <= MAINSTEM_OFFSET_RATIO_HI:
            return "mainstem_known_nhd_offset"
        if 0.5 <= ratio <= 2.0 and mapping_method == "exact_crosswalk":
            return "mainstem_clean"

    if ref_class == "tributary":
        if mapping_method == "exact_crosswalk" and ratio is not None and 0.2 <= ratio <= 5.0:
            return "tributary_clean"
        if mapping_method in ("exact_crosswalk", "downstream_replacement") and downstream_steps <= 3:
            return "tributary_clean"

    if mapping_method == "exact_crosswalk" and ref_class in ("mainstem", "tributary"):
        return f"{ref_class}_clean"

    if ref_class == "canal" or (ftype in CANAL_FTYPES and ref_class not in ("mainstem", "tributary")):
        return "canal_or_artificial_review"

    return "review"


def main() -> None:
    if not PHASE1B_CSV.is_file():
        raise SystemExit(f"Missing {PHASE1B_CSV}; run Phase 1b first.")

    v1b = pd.read_csv(PHASE1B_CSV, dtype={"usgs_site_no": str})
    v1b["usgs_site_no"] = v1b["usgs_site_no"].str.zfill(8)
    names = load_station_names()

    huc12s = derive_huc12_list_for_huc8(HUC8, vpuid=VPUID)
    print("Loading NHD HR + chandeg crosswalk…")
    flows_gdf, _, _ = load_nhd_enriched_domain(huc12s)
    flows = flows_gdf.drop(columns=["geometry"], errors="ignore")
    hs_map, nhd_to_hs = build_hydroseq_maps(flows)

    chandeg_df = parse_chandeg(TXTINOUT)
    chandeg_gis = set(chandeg_df["gis_id"].dropna().astype(int).tolist())
    chandeg_by_gis = chandeg_df.set_index("gis_id")[["lcha", "area_km2", "chandeg_id"]].to_dict("index")

    gis_pts = parse_chandeg_gis_points(TXTINOUT)
    xw = snap_gis_to_nhd_orig(gis_pts, flows_gdf.to_crs("EPSG:5070"))
    if "NHDPlusID" in xw.columns:
        xw = xw.rename(columns={"NHDPlusID": "nhdplusid_crosswalk"})
    xw["nhdplusid_crosswalk"] = pd.to_numeric(xw["nhdplusid_crosswalk"], errors="coerce")
    nhd_to_gis = build_nhd_to_gis(xw, chandeg_gis)

    prod_ch = {}
    if STATIONS_SHP.is_file():
        st = gpd.read_file(STATIONS_SHP)
        st["site_no"] = st["site_no"].astype(str).str.zfill(8)
        prod_ch = st.set_index("site_no")["channel"].to_dict()

    rows = []
    for _, r in v1b.iterrows():
        site = r["usgs_site_no"]
        ref_nhd = int(r["v1b_nhdplusid"]) if pd.notna(r["v1b_nhdplusid"]) else None
        ref_class = normalize_reference_class(r.get("v1b_context"))
        ref_attr = reach_attrs(flows, ref_nhd) if ref_nhd else {}
        nhd_tda = ref_attr.get("totdasqkm")

        gis_id = None
        mapping_method = "missing"
        steps = 0
        mapped_nhd = None
        notes = ""

        if ref_nhd is not None:
            gis_id, mapping_method, steps, mapped_nhd = map_reference_to_swat(
                ref_nhd,
                hs_map,
                nhd_to_hs,
                nhd_to_gis,
                chandeg_gis,
                ref_class,
                ref_attr,
            )

        chandeg_present = gis_id is not None and int(gis_id) in chandeg_by_gis
        swat_da = None
        swat_lcha = None
        if chandeg_present:
            ent = chandeg_by_gis[int(gis_id)]
            swat_da = float(ent["area_km2"])
            swat_lcha = float(ent["lcha"]) if pd.notna(ent.get("lcha")) else None

        ratio = (swat_da / nhd_tda) if swat_da and nhd_tda and nhd_tda > 0 else None

        if mapping_method == "missing":
            notes = "No chandeg GIS channel within downstream HydroSeq walk."
        elif mapping_method == "exact_crosswalk" and mapped_nhd == ref_nhd:
            notes = "Exact NHDPlusID crosswalk to chandeg gis_id."
        elif mapping_method in ("downstream_replacement", "lake_outlet_replacement"):
            notes = f"Mapped at downstream step {steps} to NHD {mapped_nhd} (ref {ref_nhd})."

        aclass = assignment_class_for_row(
            ref_class, mapping_method, chandeg_present, ratio, ref_attr, steps
        )

        prod = prod_ch.get(site)
        prod_note = ""
        if prod is not None and gis_id is not None and int(prod) != int(gis_id):
            prod_note = f" production_gis={int(prod)}"

        rows.append(
            {
                "site_no": site,
                "station_name": r.get("station_name") or names.get(site, ""),
                "v1b_nhdplusid": ref_nhd,
                "v1b_pick_rule": r.get("v1b_pick_rule"),
                "reference_class": ref_class,
                "reference_gnis": ref_attr.get("gnis_name"),
                "reference_ftype": ref_attr.get("ftype"),
                "reference_has_wb_link": ref_attr.get("has_wb_link"),
                "swat_gis_id": int(gis_id) if gis_id is not None else None,
                "swat_lcha": swat_lcha,
                "mapping_method": mapping_method,
                "mapped_nhdplusid": mapped_nhd,
                "replacement_steps_downstream": steps,
                "chandeg_present": chandeg_present,
                "swat_da_km2": swat_da,
                "nhd_tda_km2": nhd_tda,
                "swat_nhd_ratio": ratio,
                "assignment_class": aclass,
                "production_gis_channel": int(prod) if prod is not None and pd.notna(prod) else None,
                "notes": notes + prod_note,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    n = len(df)
    exact = int((df["mapping_method"] == "exact_crosswalk").sum())
    down = int(df["mapping_method"].str.contains("replacement", na=False).sum())
    miss = int((df["mapping_method"] == "missing").sum())
    cls = df["assignment_class"].value_counts()

    md = [
        "# Peace Phase 2 — SWAT-second mapping (v1b reference reaches)",
        "",
        "Maps Phase 1b **NHD-first** `NHDPlusID` → SWAT+ `gis_id` in `chandeg.con`. "
        "Reference reach was **not** chosen using `AreaC` or chandeg area.",
        "",
        "## Mapping summary (76 stations)",
        "",
        f"| Mapping method | Count |",
        f"|----------------|------:|",
        f"| `exact_crosswalk` | {exact} |",
        f"| downstream / lake outlet replacement | {down} |",
        f"| `missing` | {miss} |",
        "",
        "## Assignment class (preliminary)",
        "",
    ]
    for k, v in cls.items():
        md.append(f"- **{k}:** {v}")
    md.extend(
        [
            "",
            "## Anchor checks",
            "",
        ]
    )
    for site in ("02294760", "02294650"):
        sub = df[df["site_no"] == site]
        if not sub.empty:
            s = sub.iloc[0]
            md.append(
                f"- **{site}** — ref `{s['v1b_nhdplusid']}`, GIS **{s['swat_gis_id']}**, "
                f"`{s['mapping_method']}`, class `{s['assignment_class']}`, ratio {s['swat_nhd_ratio']}"
            )

    md.extend(
        [
            "",
            "## Next: v3 inventory",
            "",
            "Merge Phase 1b reference + Phase 2 mapping + drainage-area audit chain for calibration eligibility.",
            "",
            f"Full table: `{OUT_CSV.name}`",
        ]
    )
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"exact={exact} downstream={down} missing={miss}")
    print(cls.to_string())


if __name__ == "__main__":
    main()

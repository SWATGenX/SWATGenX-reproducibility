#!/usr/bin/env python3
"""Compare Peace meta NWIS columns vs live NWIS site API (acceptance after backfill)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))

from SWATGenXConfigPars import SWATGenXPaths  # noqa: E402
from nwis_site_metadata import SQMI_TO_SQKM, fetch_site_drainage_batch, nwis_drain_area_km2  # noqa: E402

V3 = REPO / "publication/analysis/qa/peace-station-assignment-v3-inventory.csv"
META = Path(SWATGenXPaths.streamflow_vpuid_path) / "0310" / "meta_0310.csv"
OUT_CSV = REPO / "publication/analysis/qa/peace-meta-vs-nwis-drainage-area.csv"
OUT_MD = REPO / "publication/analysis/qa/peace-meta-vs-nwis-drainage-area.md"


def main() -> None:
    v3 = pd.read_csv(V3, dtype=str)
    sites = sorted(v3["site_no"].str.zfill(8).unique())
    meta = pd.read_csv(META, dtype={"site_no": str})
    meta["site_no"] = meta["site_no"].str.zfill(8)

    api = fetch_site_drainage_batch(sites)
    rows = []
    for sn in sites:
        m = meta.loc[meta["site_no"] == sn]
        meta_nwis = float(m.iloc[0]["nwis_drain_area_km2"]) if len(m) and pd.notna(m.iloc[0].get("nwis_drain_area_km2")) else None
        meta_wbd = float(m.iloc[0]["wbd_upstream_hu12_area_sqkm"]) if len(m) and pd.notna(m.iloc[0].get("wbd_upstream_hu12_area_sqkm")) else None
        a = api.get(sn, {})
        api_km2 = nwis_drain_area_km2(a.get("drain_area_va"), a.get("contrib_drain_area_va"))
        diff_pct = None
        if meta_nwis and api_km2:
            diff_pct = round(100.0 * (meta_nwis - api_km2) / api_km2, 4)
        rows.append(
            {
                "site_no": sn,
                "meta_nwis_drain_area_km2": meta_nwis,
                "api_nwis_drain_area_km2": round(api_km2, 4) if api_km2 else None,
                "meta_wbd_upstream_hu12_km2": meta_wbd,
                "meta_minus_api_pct": diff_pct,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    both = df.dropna(subset=["meta_nwis_drain_area_km2", "api_nwis_drain_area_km2"])
    within_1 = int((both["meta_minus_api_pct"].abs() <= 1.0).sum()) if len(both) else 0
    OUT_MD.write_text(
        "\n".join(
            [
                "# Peace meta NWIS columns vs live API",
                "",
                f"Stations: {len(sites)}",
                f"Both meta and API NWIS km²: {len(both)}",
                f"Within 1%: {within_1}",
                "",
                f"Table: `{OUT_CSV.name}`",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUT_CSV} — within 1%: {within_1}/{len(both)}")


if __name__ == "__main__":
    main()

"""Load station drainage areas from VPU meta CSV (NWIS site vs WBD HU12 sum)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "SWATGenX"))

from nwis_site_metadata import station_drainage_area_km2  # noqa: E402


def load_station_drainage_area_km2(site_no: str, meta_csv: Path) -> tuple[float | None, str]:
    """Return (km², source_label). Prefers NWIS site catalog; documents WBD when used."""
    if not meta_csv.is_file():
        return None, "none"
    meta = pd.read_csv(meta_csv, dtype={"site_no": str})
    row = meta.loc[meta["site_no"] == str(site_no).zfill(8)]
    if row.empty:
        return None, "none"
    return station_drainage_area_km2(row.iloc[0].to_dict(), for_da_distance=False)


def load_station_nwis_da_km2(site_no: str, meta_csv: Path) -> tuple[float | None, str]:
    """Real USGS NWIS site drainage area only (km², source_label).

    Returns (None, source) when the meta row has no NWIS site area and only a WBD HU12
    fallback exists — so callers never mislabel the WBD polygon area as NWIS.
    """
    da, src = load_station_drainage_area_km2(site_no, meta_csv)
    if da is not None and str(src).startswith("nwis"):
        return da, src
    return None, src


def load_wbd_upstream_area_km2(site_no: str, meta_csv: Path) -> float | None:
    if not meta_csv.is_file():
        return None
    meta = pd.read_csv(meta_csv, dtype={"site_no": str})
    row = meta.loc[meta["site_no"] == str(site_no).zfill(8)]
    if row.empty:
        return None
    r = row.iloc[0]
    for col in ("wbd_upstream_hu12_area_sqkm", "drainage_area_sqkm"):
        if col in r.index and pd.notna(r[col]) and float(r[col]) > 0:
            return float(r[col])
    return None


# Backward-compatible alias (misnamed historically).
def load_usgs_da_km2(site_no: str, meta_csv: Path) -> tuple[float | None, str]:
    return load_station_drainage_area_km2(site_no, meta_csv)

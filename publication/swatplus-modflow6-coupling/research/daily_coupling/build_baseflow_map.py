"""SFR-reach -> SWAT+ channel map for the daily coupler up-direction (M3).

Output: mf6_baseflow.map, read by mf6_coupler.f90.  Each line links one MODFLOW 6
SFR reach to the SWAT+ channel (gis id) it discharges to:
    reach_idx(0-based)  gis_channel
The coupler reads MODFLOW_SFR/SFR_0/GWFLOW (per-reach groundwater<->stream
exchange, m3/day) and aggregates -GWFLOW (baseflow, +ve = aquifer feeds stream)
onto channels by gis id, then adds it to the channel inflow.

Source: reach_to_channel.csv (reach, row, col, Channel, d), built earlier by
matching each SFR reach's GWF cell (Grids_MODFLOW.shp) to the nearest rivs1
SWAT+ channel.  Usage: python build_baseflow_map.py <reach_to_channel.csv> <out>
"""
import sys
import csv

src = sys.argv[1] if len(sys.argv) > 1 else "../multianalyte_spike/reach_to_channel.csv"
out = sys.argv[2] if len(sys.argv) > 2 else "mf6_baseflow.map"
NSFR = 1506   # number of SFR reaches (GWFLOW array size)

rows = list(csv.DictReader(open(src)))
seen = {}
for r in rows:
    rea, ch = int(r["reach"]), int(r["Channel"])
    if 0 <= rea < NSFR and rea not in seen:   # 1 reach -> 1 (nearest) channel
        seen[rea] = ch
m = sorted(seen.items())
with open(out, "w") as f:
    f.write(f"{len(m)} {NSFR}\n")
    for rea, ch in m:
        f.write(f"{rea} {ch}\n")
print(f"wrote {out}: {len(m)} reach->channel links, "
      f"{len(set(seen.values()))} channels receive baseflow")

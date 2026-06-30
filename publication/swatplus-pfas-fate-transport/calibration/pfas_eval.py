#!/usr/bin/env python3
"""PFAS calibration objective for the Rogue: compare modeled in-stream PFOS
concentration at the EGLE station channels to the observed grab-sample values.

Observations are sparse spatial aggregates (max_water_ngL per station), so this
is a SPATIAL calibration -- match the modeled concentration pattern (incl. the
Wolverine downstream gradient) across the ~22 station channels, in log space.

Inputs:
  - pfas_stations_assignment.csv : station -> channel + observed max_water_ngL
  - channel_pfas_day.txt         : modeled daily per-reach PFAS (conc_ngL col)

Modeled representative conc per channel = flow-weighted mean of daily outflow
(total exported mass / total outflow volume), the most grab-sample-comparable
statistic. Reports per-station table + log-space NSE / RMSE / PBIAS + a scatter.
"""
import sys, csv, math
from collections import defaultdict

ASSIGN = sys.argv[1] if len(sys.argv) > 1 else "pfas_stations_assignment.csv"
CHAN   = sys.argv[2] if len(sys.argv) > 2 else "channel_pfas_day.txt"

# ---- observed: station -> (channel, obs_ngL) -------------------------------
obs_by_chan = {}   # channel -> list of (site, obs)
with open(ASSIGN) as f:
    r = csv.DictReader(f)
    for d in r:
        try:
            ch = int(d["channel"]); ob = float(d["max_water_ngL"])
        except (ValueError, KeyError):
            continue
        if ob > 0:
            obs_by_chan.setdefault(ch, []).append((d["site_id"], ob))

# ---- modeled: channel -> flow-weighted mean conc ---------------------------
# channel_pfas_day.txt cols: jday mon day yr unit gis_id name pfas tot_in sol_out
#   sor_out settle resus diffuse bury water benthic conc   (conc is last col)
m_mass = defaultdict(float)   # sum daily exported mass (sol_out+sor_out)
m_vol  = defaultdict(float)   # sum daily outflow volume (m3) = mass/conc*1e9
m_csum = defaultdict(float); m_cn = defaultdict(int)   # arithmetic mean conc
with open(CHAN) as f:
    header = f.readline()
    for line in f:
        p = line.split()
        if len(p) < 18:
            continue
        try:
            unit = int(p[4]); sol = float(p[9]); sor = float(p[10]); conc = float(p[-1])
        except ValueError:
            continue
        if unit not in obs_by_chan:
            continue
        mass = sol + sor
        m_mass[unit] += mass
        if conc > 0:
            m_vol[unit] += mass / conc * 1.0e9
            m_csum[unit] += conc; m_cn[unit] += 1

# ---- per-station comparison ------------------------------------------------
rows = []
for ch in sorted(obs_by_chan):
    fw = (m_mass[ch] / m_vol[ch] * 1.0e9) if m_vol[ch] > 0 else 0.0   # flow-wtd ng/L
    am = (m_csum[ch] / m_cn[ch]) if m_cn[ch] > 0 else 0.0             # arithmetic mean ng/L
    for site, ob in obs_by_chan[ch]:
        rows.append((ch, site, ob, fw, am))

print(f"{'chan':>5} {'site':<22} {'obs_ngL':>8} {'mod_fw':>9} {'mod_mean':>9}")
for ch, site, ob, fw, am in rows:
    print(f"{ch:>5} {site:<22} {ob:>8.2f} {fw:>9.2f} {am:>9.2f}")

# ---- objective metrics (log space; PFAS spans orders of magnitude) ---------
pairs = [(ob, fw) for _, _, ob, fw, _ in rows if ob > 0 and fw > 0]
if pairs:
    o = [math.log10(x[0]) for x in pairs]
    m = [math.log10(x[1]) for x in pairs]
    ob_mean = sum(o) / len(o)
    sse = sum((a - b) ** 2 for a, b in zip(o, m))
    sst = sum((a - ob_mean) ** 2 for a in o)
    nse = 1 - sse / sst if sst > 0 else float("nan")
    rmse = math.sqrt(sse / len(o))                       # log10 units
    obs_lin = [x[0] for x in pairs]; mod_lin = [x[1] for x in pairs]
    pbias = 100 * (sum(mod_lin) - sum(obs_lin)) / sum(obs_lin)
    print(f"\nn_paired={len(pairs)}  log-NSE={nse:.3f}  log-RMSE={rmse:.3f} dex  "
          f"PBIAS={pbias:+.1f}%")
    # objective to MINIMIZE for calibration (lower is better)
    print(f"OBJECTIVE(logRMSE)={rmse:.4f}")
else:
    print("\nno paired obs/model points (model conc all zero at station channels?)")

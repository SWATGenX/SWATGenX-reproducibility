#!/usr/bin/env python3
"""Prepare per-channel calibrated PFOS concentration + per-HRU soil-PFAS params
for the manuscript figures. Writes two CSVs the figure script joins to shapefiles."""
import csv, os, collections, statistics

RUN = "/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/run_rogue"
OUT = os.path.dirname(os.path.abspath(__file__))

# ---- 1. per-channel flow-weighted PFOS conc (ng/L) from channel_pfas_day.txt ----
mass = collections.defaultdict(float); vol = collections.defaultdict(float)
with open(os.path.join(RUN, "channel_pfas_day.txt")) as f:
    f.readline()
    for line in f:
        p = line.split()
        if len(p) < 18:
            continue
        try:
            unit = int(p[4]); sol = float(p[9]); sor = float(p[10]); conc = float(p[-1])
        except ValueError:
            continue
        m = sol + sor
        mass[unit] += m
        if conc > 0:
            vol[unit] += m / conc * 1e9
with open(os.path.join(OUT, "channel_pfos.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Channel", "pfos_ngL"])
    for ch in sorted(mass):
        c = (mass[ch] / vol[ch] * 1e9) if vol[ch] > 0 else 0.0
        w.writerow([ch, round(c, 4)])
print("channel_pfos.csv:", len(mass), "channels")

# ---- 2. per-HRU surface-layer soil PFOS (ug/ha), kf, nf from pfas_hru.ini ----
# format: "hru <id> nly <n>" / num_pconta / d50/layer / then per PFAS: id + n vals
# repeated 4x: sol_pfas, kf, nf, enr
rows = []
with open(os.path.join(RUN, "pfas_hru.ini")) as f:
    lines = [ln.rstrip("\n") for ln in f]
i = 0
# skip 2 title/header lines
while i < len(lines) and not lines[i].startswith("hru "):
    i += 1
while i < len(lines):
    if not lines[i].startswith("hru "):
        i += 1; continue
    parts = lines[i].split()
    hid = int(parts[1]); nly = int(parts[3]); i += 1
    i += 1                       # num_pconta
    i += 1                       # d50/layer
    # PFAS block: sol_pfas, kf, nf, enr (each: id + values)
    def readvals():
        global i
        toks = lines[i].split(); i += 1
        return [float(x) for x in toks[1:]]
    sol = readvals(); kf = readvals(); nf = readvals(); enr = readvals()
    rows.append((hid, sol[0] if sol else 0.0, kf[0] if kf else 0.0, nf[0] if nf else 0.0))
with open(os.path.join(OUT, "hru_soil_pfas.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["HRU", "sol_pfas_ugha", "kf", "nf"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3]])
print("hru_soil_pfas.csv:", len(rows), "HRUs")

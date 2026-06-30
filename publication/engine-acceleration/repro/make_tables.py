#!/usr/bin/env python3
"""Regenerate the paper's scaling tables directly from the measured result CSVs.

This closes the reproducibility loop: clone -> python3 make_tables.py reproduces the
cross-hardware grid (main-paper Table 2 / Supplement S2) and the full-vs-byte-identical
table (Supplement S3) from results/*.csv, with no embedded numbers.
Best-of-two per (rung, threads); speedups are each machine's own t1 -> N.
"""
import csv, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

def best(path):
    b = defaultdict(lambda: 1e9)
    with open(path) as f:
        for r in csv.DictReader(f):
            k = (r["rung"], int(r["threads"]))
            b[k] = min(b[k], float(r["wall_s"]))
    return b

print("=== Cross-hardware scaling (Table 2 / S2) — self-relative t1->N ===")
print(f"{'N':>4} | {'c8a':>16} | {'c8i':>16} | {'c5a':>16}")
boxes = {}
for box in ["c8a", "c8i", "c5a"]:
    p = os.path.join(RES, f"crosshw_{box}.csv")
    boxes[box] = best(p) if os.path.exists(p) else {}
for box in ["c8a", "c8i", "c5a"]:
    d = boxes[box]
    if d:
        print(f"  {box}: stock R0={d[('R0',1)]:.1f}s  R6={d[('R6',1)]:.1f}s  "
              f"serial {d[('R0',1)]/d[('R6',1)]:.2f}x  t1={d[('R6FULL',1)]:.1f}s")
for N in [2, 4, 6, 8, 10, 12, 16, 20, 24]:
    cells = []
    for box in ["c8a", "c8i", "c5a"]:
        d = boxes[box]; key = ("R6FULL", N)
        if d and key in d and d[key] < 1e9:
            t1 = d[("R6FULL", 1)]
            cells.append(f"{t1/d[key]:.2f}x (vs-stk {d[('R0',1)]/d[key]:.2f}x)")
        else:
            cells.append("--")
    print(f"{N:>4} | {cells[0]:>16} | {cells[1]:>16} | {cells[2]:>16}")

fb = os.path.join(RES, "c8a_full_vs_byteid.csv")
if os.path.exists(fb):
    d = best(fb); R0 = d[("R0", 1)]
    print(f"\n=== Full vs byte-identical (Table S3) — c8a, stock R0={R0:.1f}s ===")
    print(f"{'N':>4} | {'full wall':>10} {'full':>7} | {'byteid wall':>11} {'byteid':>7} | {'forfeit':>7}")
    tf, ts = d[("R6FULL", 1)], d[("R6SER", 1)]
    for N in [1, 2, 4, 8, 16]:
        f_, s_ = d[("R6FULL", N)], d[("R6SER", N)]
        print(f"{N:>4} | {f_:>9.1f}s {tf/f_:>6.2f}x | {s_:>10.1f}s {ts/s_:>6.2f}x | {(1-f_/s_)*100:>5.0f}%")

"""Aggregate a finished DISV GWT run's pfas.ucn -> cmax_disv_<analyte>.npz, mapped back to the
structured (row,col) grid by max (apples-to-apples with the structured porewater validation).
Recovers results from completed mf6 runs whose Python post-processing crashed on the array shape.
Usage: python aggregate_disv_cmax.py PFOA PFHxS PFBS PFHxA [PFOS]
"""
import os, sys, glob, numpy as np, flopy
from collections import defaultdict

OUT = "/data/SWATGenXApp/codes/publication/swatplus-modflow6-coupling/research/multianalyte_spike"
m = np.load(f"{OUT}/disv_map.npz")
mr, mc, idom_d = m["mr"], m["mc"], m["idom_d"]
ncpl = idom_d.shape[1]
inv = defaultdict(list)
for i in range(ncpl):
    inv[(int(mr[i]), int(mc[i]))].append(i)
nrow, ncol = int(mr.max()) + 1, int(mc.max()) + 1

for a in (sys.argv[1:] or ["PFOA", "PFHxS", "PFBS", "PFHxA"]):
    ucn = glob.glob(f"/tmp/rogue_disv_{a}/pfas.ucn")
    if not ucn:
        print(f"{a}: no pfas.ucn"); continue
    c = np.squeeze(np.asarray(flopy.utils.HeadFile(ucn[0], text="CONCENTRATION").get_data()))
    if c.ndim == 1:
        c = c[None, :]
    cmax_cell = np.nanmax(np.where(idom_d != 0, c, np.nan), axis=0)   # (ncpl,)
    cmax = np.full((nrow, ncol), np.nan)
    for (r, cc), cells in inv.items():
        vals = [cmax_cell[i] for i in cells if np.isfinite(cmax_cell[i])]
        if vals:
            cmax[r, cc] = max(vals)
    np.savez(f"{OUT}/cmax_disv_{a}.npz", cmax=cmax)
    finite = np.isfinite(cmax)
    print(f"{a}: cmax_disv saved | cells>1ng/L={int(np.nansum(cmax>1))} max={np.nanmax(cmax):.0f} ng/L")
print("DONE")

# MODGenX convergence — root cause + fix (2026-06-21)

The deployed Rogue NWT model (and the failed dashboard order) don't meet solver
tolerance. Diagnosed on the real model:

| Check | Result | Verdict |
|---|---|---|
| Layer geometry | monotonic, thickness 1–8 m, **0 pinch-outs/inversions** | clean |
| K field (UPW) | 2–47 m/d, 23× range, <1 order-of-mag adjacent jumps, no zeros | clean |
| **Starting heads** | **14,442 / 54,910 active cells (26%) start BELOW cell bottom (dry)** | **ROOT CAUSE** |
| Bottom layer | layer 6 entirely inactive (dead) | minor cleanup |

**Root cause: a starting-head bug, not bad data.** In steep terrain MODGenX sets a
regional starting head that falls below the topography-following cell bottoms, so the
Newton solver begins with thousands of dry cells and cannot recover.

**Proven fix** (`phase0_spike/convergence_fix_test.py`): set `strt = top` (land surface,
per cell) + a robust MF6 Newton config (BICGSTAB + DBD under-relaxation + backtracking).
The Rogue then **converges COLD (no NWT heads) at 0.00% mass-balance discrepancy**,
mean head 226.6 m (same physical answer).

**Refactor (decided: MF6 generator + validation):**
1. `strt = top` per cell.
2. Robust MF6 IMS Newton config, baked in.
3. Geometry/conditioning **validation+repair gate** (monotonic layers, min thickness,
   `strt>=botm`, K>0, connected active region, drop dead all-inactive layers) so a
   non-converging model can never silently ship — this also catches genuinely bad-layer
   regions beyond the Rogue.
4. Multi-watershed convergence test harness.

Note: this fixes *convergence* (solver finds a solution). Calibration (gwflow-zone /
MODFLOW, matching observed heads) is the separate downstream step, unchanged.

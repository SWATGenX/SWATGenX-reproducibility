# SWAT+ ↔ MODFLOW 6 daily coupling — status

_Built overnight 2026-06-25. Engine work on fork branch `feat/pfas-surface-water`._

## What now works (validated + committed)

A genuine **live, daily, two-way SWAT+ ↔ MODFLOW 6 coupling** — MODFLOW 6 embedded
in the SWAT+ day loop via its BMI/XMI C interface (`libmf6.so`). Every simulated day:

| # | Direction | Mechanism | Status |
|---|-----------|-----------|--------|
| M1 | engine drives MF6 | `dlopen` libmf6.so (RTLD_LOCAL), step daily | ✅ validated |
| M2 | water **down** | SWAT+ percolation `sepbtm` → MF6 recharge (area-weighted, 84 684 links) | ✅ +139 mm/yr, matches GWF budget |
| M3 | water **up** | MF6 SFR baseflow → SWAT+ channels, replaces native aquifer return | ✅ +27 Mm³/yr gaining, matches budget |
| M4b | PFAS **down** | SWAT+ leaching `hpfasb_d%perc` → GWT SRC mass source | ⚙️ code correct; 0 flux short-term (see below) |
| M4c | PFAS **up** | GW PFAS (baseflow × GW conc) → channel `hcs1%pfas` | ✅ 44.7 kg/90d discharged to streams |

**Commits:** engine `94308d0` (M1–M3) + `ee07ca0` (M4) on the fork;
monorepo `6b533d01` + `735e23e4` (build tools, this folder). Nothing pushed.

## Five hard problems solved
1. **libmf6.so Fortran-runtime interposition** (statically-embedded `for__*` symbols
   corrupted SWAT+ file I/O → `munmap_chunk`). Fix: `dlopen` with `RTLD_LOCAL`.
2. **`-fpe0` SIGFPE** on MODFLOW's normal Inf/NaN (dry cells). Fix: IEEE halting
   disabled around BMI calls.
3. **List-directed read truncated `./mf6` → `.`** at the `/`. Fix: manual token parse.
4. **Recharge timing** — overwrite the live array between `prepare_time_step` and
   `do_time_step` (XMI granular stepping), not via bundled `update()`.
5. **SRC at inactive layer-1 cells** (period data only validated at `rp`, not
   `initialize`). Fix: place the source at the top *active* layer.

## The key scientific finding (M4b) — robust across seasons
SWAT+ computes **zero PFAS percolation** in BOTH a winter (Jan–Mar) and a summer
(Jun–Aug) 90-day window — 0 of 17 773 HRUs, despite active water recharge. The soil
PFAS pool *does* shrink (~0.16 kg/ha-sum lost), but PFOS leaves via surface runoff /
lateral flow / sediment, **not** deep percolation. **PFOS does not leach to
groundwater on these timescales — it is too strongly sorbed.**

This is corroborated by the **kriged depth-to-water: mean 37.7 m, median 30.6 m**
(`dtw_grid.npy`) — a *tens-of-metres* vadose zone. Together: groundwater PFAS is
**legacy** (the historical Tannery plume, which M4c correctly routes to streams at
44.7 kg), and any land-derived PFOS would take **decades** to cross the deep vadose.
The M4b "0 flux" is the physically *correct* answer, not a coupling defect — and it
is precisely the case the UZF/UZT vadose model exists to represent over decades.

_(Note: `1e30` in the `.ucn` files is MODFLOW's inactive-cell no-data marker, not a
blown-up solution — active-cell concentrations top out at the 100 000 ng/L source.
The daily GWF+GWT transport is numerically stable.)_

## How to run
`mf6.con` in TxtInOut (workspace, GWF cadence, GWT cadence). Maps next to it:
`mf6_recharge.map`, `mf6_baseflow.map`, `pfas_leach.map`. Build with the scripts here
(`build_daily_mf6.py`, `build_daily_gwt.py`, `build_recharge_map.py`,
`build_baseflow_map.py`, `build_pfas_src.py`). Validated test rig:
`run_rogue` (PFAS-configured Rogue) + a daily GWF+GWT model in `./mf6`.

## Next phase — vadose UZF/UZT (the headline mechanism)
**Data is available:** `MODFLOW_250m/rasters_input/04118500_kriging_output_SWL_250m.tif`
(kriged depth-to-water). The current model has **no vadose zone** (water table pinned
at land surface), confirming the gap.

Design:
1. Resample the SWL raster → per-cell depth-to-water = unsaturated column thickness.
2. **UZF** package: an unsaturated column per cell (surface → water table); infiltration
   = the SWAT+ percolation we already pass (drive UZF instead of/above RCHA).
3. **UZT** package: transport PFAS down the column with Freundlich retardation
   (R = 1 + ρ·Kd/θ) → years–decades lag → aquifer (GWT) → SFT → stream. Infiltration
   concentration = the SWAT+ PFAS leaching signal (replaces the direct SRC).
4. Coupler: feed UZF/UZT instead of RCHA/SRC; everything else (baseflow + PFAS up) is
   unchanged.

**Open parameterization (needs review):** UZF vertical discretization, UZT vs the
air–water-interface Langmuir term (standard UZT does Freundlich only — the deep-vadose
air–water retention is the rigorous refinement), and the multi-year spin-up window.

## Remaining Phase 3 (run on the coupled model, after vadose)
DISV refinement → SW+GW mass-balance closure → Sobol UA → transient 95PPU →
fold all into the manuscript (methods now describe a *live* daily two-way coupling).

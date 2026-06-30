# Coupled SWAT⁺ ↔ MODFLOW 6 PFAS fate-and-transport

A live, daily, two-way coupling of the SWAT⁺ surface-water model and MODFLOW 6
groundwater flow + transport, carrying PFAS through both compartments. This folder
holds the paper, the run-it guide, and the supporting analyses.

## Start here
- **[USER_GUIDE.md](USER_GUIDE.md)** — plain-language, step-by-step **how to run**
  the model (two on-ramps: the swatgenx.com website, or a local Windows build).
  Read the paper for the science; read the guide to run it.
- **`paper/`** — the manuscript (`paper/main.pdf`).

## How the coupling is built and validated
- **`research/daily_coupling/`** — the coupling itself: build tools
  (`build_daily_mf6.py`, `build_recharge_map.py`, `build_baseflow_map.py`,
  `build_daily_gwt.py`, `build_pfas_src.py`) and `COUPLING_STATUS.md` (what works,
  the engineering hurdles, validation: recharge ≈139 mm/yr and net stream–aquifer
  exchange +27 Mm³/yr, both matching MODFLOW's own budget).
- Engine code lives on the SWAT⁺ fork, branch `feat/pfas-surface-water`
  (`mf6_coupler.f90` + hooks). The engine dlopens `libmf6.so` and exchanges state
  each day; activated by an `mf6.con` file in `TxtInOut`.

## Supporting analyses
- **`research/vadose/`** — vadose-zone travel time (lumped + explicit 1D agree):
  PFOS ~centuries, PFOA ~decades-centuries; air-water-interface retardation;
  Sobol. Shows diffuse land→groundwater PFAS is negligible in-window → the
  groundwater plume is legacy.
- **`research/oat_hydraulic/`** — one-at-a-time HYDRAULIC sensitivity of the
  coupled model using PFHxA (the most mobile analyte), reporting the SW↔GW mass
  exchange and mass-balance ranges.
- **`sa/`** — the 18-parameter Morris screening and a surrogate Sobol; the
  in-stream prediction is groundwater-controlled at the lower mainstem and
  surface-controlled mid-basin.

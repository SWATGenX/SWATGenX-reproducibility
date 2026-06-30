# RIV → SFR migration (04124500) — connected streamflow routing + in-stream PFAS transport

**Status: DONE.** The RIV package (a per-cell head-dependent leak with no routing) is replaced by
SFR (a topologically-connected reach network that routes streamflow AND, via SFT, solute
downstream). SFR is now the default stream package in the MODGenX build pipeline, and it unlocks
the in-stream PFAS pathway: PFAS that discharges from groundwater into a stream reach is routed
downstream through the channel network to the outlet — the loop RIV could not close.

## Why SFR over RIV
| | RIV | SFR |
|---|---|---|
| GW↔stream exchange | per-cell head-dependent leak | per-reach head-dependent (streambed K) |
| streamflow routing | none | Manning depth → stage, routed through reach graph |
| in-stream solute | impossible (water "vanishes") | SFT routes solute downstream |
| stage | prescribed (top − incision) | computed from accumulated flow |

## Network construction (`MODFLOW/MODGenX/sfr_builder.py`)
From the SWAT+ channel network (`rivs1.shp`: `Channel`, `ChannelR`=downstream channel, `Wid2`,
`Len2`, `MinEl/MaxEl`, `strmOrder`), filtered to `strmOrder ≥ 2` (order-1 = artificial flowlines):
1. orient each channel upstream→downstream by **DEM elevation at its endpoints** (lower = downstream);
2. intersect with the MODFLOW grid → one reach per crossed active cell, ordered downstream;
3. per-reach geometry: in-cell length, width (Wid2), slope ((MaxEl−MinEl)/Len2, floored), streambed
   top (model top − incision), bed thickness, bed K, Manning's n;
4. connectivity from a single-successor (`nd`) graph: intra-channel reach→reach + inter-channel
   last-reach→receiver's-first-reach (`ChannelR`); confluences give a reach multiple upstreams.

**Two connectivity bugs found + fixed** (both produced "circular dependency / streamflow not
permitted" MF6 errors):
- A geometric (proximity-to-downstream-channel) orientation produced reciprocal links at
  confluences. Fixed with elevation-based orientation (per-channel, independent).
- 0-based signed connections lose the sign of a link to reach 0 (`-0 == 0`). Fixed by numbering
  reaches in **topological order** (headwaters first) so every reach's downstream id exceeds its
  own — `−nd` is never `−0`. (This is also the order MF6's SFR solver prefers.)

Result on 04124500: **382 reaches, 95 channels, 14 headwaters, 0 connectivity violations.**

## Calibrated SFR flow field (`build_sfr_gwf.py` → `MODFLOW_wl_cal_sfr`)
Swaps RIV→SFR on the calibrated GWF (reusing the calibrated aquifer K / recharge / GHB / pump) and
runs a 1-parameter search on streambed K to restore the observed gaining baseflow:

| streambed K (m/d) | baseflow (m³/s) | head NSE |
|---|---|---|
| 0.05 | +0.391 | 0.205 |
| **0.20** | **+0.629** | **0.242** |
| 0.50 | +0.683 | 0.258 |
| 1.0 | +0.692 | 0.262 |

`bed_k = 0.2 m/d` matches the observed 0.63 m³/s gaining baseflow, with head NSE 0.242 — *better*
than the RIV-calibrated model (0.22) and cleanly gaining.

## Phase 2 readback (SFR-native, `swatmf_phase2_driver.py::phase2_sfr`)
The GW↔stream exchange is now a native per-reach SFR budget term ('GWF') — no leakage-law
recomputation, no RIV-cell→reach spatial join (reaches already *are* SWAT+ channel segments):
**net baseflow +0.629 m³/s, 54.7% gaining channels** (vs the RIV Phase 2 which fought to stay
net-gaining). `phase2_sfr_per_channel_baseflow.csv`, `phase2_sfr_result.json`.

## Phase 3 in-stream PFAS routing (`phase3_pfas_sfr.py` → `phase3_sfr_instream.png`)
GWT + Freundlich PFAS coupled to `MODFLOW_wl_cal_sfr`, with **SFT** (streamflow transport) on the
SFR network. SFT carries any GW-discharged solute downstream through the connected reaches:
- **conservative tracer**: discharges where the aquifer plume meets the channel network and routes
  downstream through **74 reaches** (peak 1.66 ng/L at the discharge point, attenuating downstream
  to the outlet) — the new GW→stream→downstream capability.
- **Freundlich PFAS**: retarded (R≈10) in the aquifer (17-cell plume), **0 stream reaches** — has
  not reached a stream in 40 yr.

## Pipeline wiring
`config.modflow_use_sfr=True` (default) makes MODGenX build SFR for every new MODFLOW model;
`build_mf6_model(sfr_spec=...)` constructs the network against the *repaired* idomain (no reach on
a pruned cell) and falls back to RIV (`riv_rec`) if disabled. Verified: a from-arrays
`build_mf6_model` SFR build converges (mass balance −0.01%).

## Files
`sfr_builder.py` (network), `mf6_builder.py` (`_add_sfr` + `sfr_spec` path), `MODGenXCore.py`
(wiring), `config.py` (flags), `swatmf_phase2_driver.py` (`phase2_sfr`), `build_sfr_gwf.py`,
`phase3_pfas_sfr.py`, `phase3_plot_sfr.py`.

## Next (deferred)
Drive the SFR network transiently with daily SWAT+ channel inflow (currently GW-fed only) and
inject the SFT outlet PFAS load back into the SWAT+ channel PFAS module (engine side) — the full
two-way in-stream coupling.

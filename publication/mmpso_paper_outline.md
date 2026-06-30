# Standalone paper outline — Multi-Memory PSO for high-dimensional multi-gauge SWAT+ calibration

**Status:** scoping (no EC2 spend yet). Read-only census done 2026-06-14. Decision pending: build/run.

## One-line contribution
A multi-memory particle-swarm optimizer (MMPSO) — adapting the platform author's PhD technique
(coupled SW–GW, geological sections; EMS 149 (2022) 105312) to **large, automated, multi-gauge
surface-water SWAT+ calibration** — that escapes the local-optimum plateau where single-objective PSO
stalls, demonstrated at scale on a 76-gauge basin generated end-to-end by SWATGenX.

## Why it's novel / publishable
- Single-objective PSO collapses every gauge's daily+monthly NSE into one scalar and steers the whole
  swarm to one global best. With many gauges a few dominant hydrographs drown out the rest, so the
  swarm fits the big channels and abandons the small ones, then plateaus.
- MMPSO decomposes the objective **per gauge** and gives each particle a memory **per sub-objective**;
  three role sub-swarms (mentor/independent/mentee) + role-based inertia + a stagnation-only budget let
  it keep exploring and break through the plateau.
- The advantage **scales with the number of sub-objectives** — so this is a *high-dimensional
  multi-gauge* calibration method, not just a tweak. SWATGenX's auto-generation makes a 76-gauge basin
  a tractable test bed (most studies can't build one).

## Evidence so far
- **Pilot (14161500, 4 gauges)**: controlled head-to-head, same seed/window/pool/budget. Single-PSO
  plateaued ~iter 17 (−1.7274) and self-terminated; MMPSO escaped to −1.7449 (iter 50). Daily NSE
  0.799→0.812, Monthly 0.928→0.934, PBIAS 5.26%→1.25%, KGE 0.840→0.851. Clear plateau-escape, modest
  NSE delta (basin already well-behaved → only 4 sub-objectives). Data: `publication/analysis/qa/mmpso_headtohead/`.
- The pilot proves the mechanism; the paper needs a **many-gauge** basin to show a *decisive* win.

## Hero dataset — Peace River basin (census 2026-06-14)
- Model: `admin/SWATplus_by_VPUID/0310/huc8/03100101` (Peace–Tampa Bay HUC8). **76 internal USGS
  gauges** in `streamflow_data/`.
- Build variants on disk: `SWAT_MODEL_Web_Application` (~58k HRUs, calibration-pipeline default),
  `SWAT_MODEL_NHD_timed` (~94k HRUs), `SWAT_MODEL_TauDEM_pb_peace_clip_burnmajor_250` (~181k HRUs).
  All have a `Scenarios/Default/TxtInOut`. (`TauDEM_coarse_lakes10_250` is incomplete — hru.con empty.)
- **Usable sub-objectives**: **35 / 76** gauges have ≥365 valid daily values in 2008–2016. Tuning the
  window may raise this. 35 sub-objectives is already a strong stress test (vs 4 in the pilot).

## Experiment design (the paper's core figure)
- One Peace model, two arms, identical seed / pool / iteration budget / cal+val windows:
  **single-objective PSO vs MMPSO (by_gauge)**, run on the same dedicated-EC2 pipeline.
- Report: (1) global-best convergence overlay (plateau vs escape); (2) **per-gauge** cal/val NSE
  distribution — the key claim is MMPSO lifts the *tail* (small/secondary gauges) that single-PSO
  abandons, not just the basin-mean; (3) headline metrics table; (4) spatial map of per-gauge NSE
  improvement. Optionally a 2–3 basin sweep (14161500 + Peace + one mid-size) to show the advantage
  growing with gauge count.

## Caveats / prerequisites (honest)
1. **Compute**: 58–94k-HRU model × pool × budget × 2 arms is a multi-hour EC2 job per arm (per-eval ~minutes).
   Bounded + on credits, but the largest run we've done. Pick the 58k `Web_Application` variant to cap cost.
2. **Calibratability**: confirm the chosen variant runs clean (produces channel_sd_day.nc) and that the
   35 usable gauges map to channels (gage→channel assignment QA). Peace's build history is rocky
   (TauDEM HRU segfaults) — but the NHD/Web_Application variants exist and are large/complete.
3. **Window choice**: pick the cal/val window that maximizes usable gauges (≥35) with a clean common period.
4. **Multi-gauge MMPSO is the regime it's built for**; single-gauge models (most of the uncalibrated
   inventory) won't showcase it — they're not paper material, just dashboard calibrations.

## Decisions for the user
- Target venue: a methods/optimization journal (e.g. *Environmental Modelling & Software*, where the
  PhD MMPSO appeared) vs a hydrology venue. Separate from the C&G SWATGenX platform paper.
- Go/no-go on the Peace head-to-head EC2 run (cost vs the decisive figure it produces).
- Whether to include a basin sweep (advantage vs gauge count) or just Peace + the 14161500 pilot.

## Uncalibrated inventory (from the same census)
111 generated admin models, ~57 uncalibrated (mostly single-gauge). Not paper material; candidates for
routine MMPSO calibration via the dashboard if desired. Junk scratch already cleaned (1.36 GB of
interrupted-run Scenario_ dirs on 02294405 removed 2026-06-14).

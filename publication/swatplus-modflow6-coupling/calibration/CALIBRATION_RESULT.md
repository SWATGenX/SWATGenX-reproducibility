# Static-head calibration — 04124500 (Wellogic MF6 model, GHB boundary)

8-parameter differential-evolution calibration (64-vCPU EC2, 21 min) against 510 observed
Wellogic well heads. Parameters: log10 multipliers on upper/lower-drift Kh+Kv, recharge
multiplier, log10 drain/river/GHB-boundary conductance multipliers. Objective = −NSE
(1–99 pctile trim).

| metric | uncalibrated | **calibrated** |
|---|---|---|
| NSE | −0.47 | **0.52** |
| RMSE | 13.0 m | **7.5 m** |
| PBIAS | +2.2 % | **+0.05 %** |
| KGE | 0.54 | **0.69** |
| R² | 0.515 | 0.533 |

Best multipliers: kh1 0.13, kh2 9.96, kv1 0.80, kv2 0.11, recharge 0.80, drn-cond 9.83,
riv-cond 0.25, **ghb-cond 0.013**.

**Physical reading:** the optimizer drove the GHB perimeter conductance to ×0.013 — i.e. it
pushed the watershed boundary toward **near-no-flow**, independently confirming the boundary
behaves as a groundwater divide (the textbook expectation). It also made the lower drift
much more transmissive (Kh ×10) and the upper drift tighter (Kh ×0.13), with recharge at 80 %
of the SWAT+ estimate. NSE 0.52 / RMSE 7.5 m is a solid regional static-head fit.

Result: `aws_results/calibration_result.json`; figure `calibration_obs_vs_sim_04124500.png`.

# PEST++ ies (pilot points + baseflow) — 04124500 result

pestpp-ies, 120 realizations × 3 iterations, 64-vCPU EC2, **2 min**. 112 pilot-point Kh
multipliers (kriged) + 5 globals (kv/rch/drn/riv/ghb), Tikhonov toward prior. Obs = 534
Wellogic heads (w=1/5) + net GW->stream baseflow (w=40, target +0.63 m3/s gaining).

| calibration | head NSE | net baseflow (target +0.63) |
|---|---|---|
| head-only DE (8 params) | **0.52** | −6.4 m3/s (losing) |
| **joint head + baseflow ies** | **−1.34** | **−1.27 m3/s** (still losing) |

phi: 1.5e5 -> 12,400 (converged, ensemble std tight).

## Finding: the constraint exposed a STRUCTURAL deficiency, not a tuning gap
The ies could not satisfy both objectives — it more than halved the baseflow error
(−6.4 -> −1.3) but degraded the head fit (0.52 -> −1.34) and still never produced a
gaining stream. This is a genuine head/baseflow TENSION:

- river stage is set at land surface (`stage = top`, the 250 m cell-mean DEM);
- the regional water table, fit to the (mostly interfluve) wells, sits below land surface;
- so at the stream cells the table is below the stream -> the reach must LOSE.

To make a reach gain, its water table must be ABOVE the stream. That cannot happen while the
stream is pinned at the cell-mean surface AND the wells pull the table down. Tuning K /
conductance / recharge alone cannot bridge it — the missing degree of freedom is the **river
stage / channel incision**: at 250 m the thalweg sits several metres below the cell-mean
surface, so the stream should be incised, not at `top`.

## Recommendation
1. Set the river stage from the stream-burned DEM (demwStream.tif) or the SWAT+ channel depth
   (Dep2), incising the streams below the cell-mean surface; OR add a per-reach stage-offset as
   a calibration parameter.
2. Rebalance the baseflow weight (w=40 split phi ~50/50 and dragged heads down chasing an
   unachievable target).
3. Re-run the ies. The pilot-point + baseflow machinery itself works and is fast (2 min/64-core).

This is the meaningful-model lesson: head-only calibration is non-unique and gave NSE 0.52
that is physically wrong on flux; the baseflow constraint reveals the model can't be both
head-accurate and gaining until the river geometry is fixed.

---

## Update — per-reach incision + rebalanced weight (run 2 & 3): root cause PINNED

Added 177 per-reach channel-incision parameters (the missing DOF) + rebalanced baseflow
weight (40->12). Two issues surfaced and were fixed for convergence:
- RIV `rbot` incised below the thin layer-0 (~7 m upper drift) bottom -> MF6 rejects. Fixed
  by first clamping to layer 0, then by **placing the RIV in the layer that contains the
  incised bottom** (layer 1/2 for deep reaches).
- Tightened the prior ensemble (STAGE_MAX 12, K +-0.8, par_sigma_range 3) -> 109/109 reals
  converge, phi 2.3e9 -> 5.5e3.

**But the streams still cannot gain**, because of a hard convergence wall:

| run | head NSE | net baseflow (target +0.63) |
|---|---|---|
| head-only DE | 0.52 | -6.4 |
| joint, no incision (w=40) | -1.34 | -1.27 |
| joint, incision clamped to L0 (w=12) | -0.67 | -3.1 |
| forward-run probe, incision >= 8 m | (fails) | non-convergent |

Only **shallow incision (~3 m) converges**; incision deep enough to put the stream below the
~8 m-deep water table (so the reach gains) + the strong riverbed conductance destabilises the
MF6 Newton solve in the thin (~7 m) drift layers, no matter which layer hosts the RIV.

**ROOT CAUSE: the layer geometry is too thin (vertically) to host deeply-incised gaining
streams.** The geometry fix we made earlier deepened the model *bottom* (so heads fit), but
the *upper* layers are still ~7 m thick — too thin for an incised, high-conductance stream to
sit below the water table without drying cells / breaking convergence. Head-only calibration
hid this; the baseflow constraint exposed it.

**Recommended structural fix (user decision):**
1. **Merge the drift into one thick upper layer** (simplest) so incised streams have vertical
   room; then re-run the (working) ies.
2. **Switch RIV -> SFR** (streamflow routing): a proper streambed that handles gaining/losing
   robustly, and it is needed anyway for PFAS in-stream transport (Phase 3).
3. Finer vertical discretisation near the stream network.

The PEST++ pilot-point + baseflow machinery is built, fast (4 min/64-core), gives parameter
uncertainty, and is ready to re-run the moment the geometry hosts gaining streams.

---

## Update 2 — Vahid's three domain fixes (run 4-6): a meaningful model emerges

Three insights from Vahid, each verified, turned the dead-end into a working calibration:
1. **RIV only on real streams (order >= 2)** — order-1 reaches are artificial/ephemeral
   headwater flowlines (121/216; widths to 0.04 m; at the highest elevations p95 424 m).
   Incising them dried cells + broke Newton. Dropping them (config.modflow_min_stream_order=2)
   -> streams can gain + the model converges. Decisive test: order>=2 + 10 m incision gains
   +1.36 m3/s and converges; all-reaches never gained.
2. **Pumping multiplier** — the WEL used PMP_CPCITY (pump CAPACITY = 0.30 m3/s ~ half the
   baseflow) as steady withdrawal. Calibrated actual/capacity = **14.5%**; at 15% + 3 m
   incision baseflow goes -3.9 -> -1.0 m3/s (over-extraction was consuming ~half the baseflow).
3. **Group incision by stream order** (3 params) instead of per-reach (89, unidentifiable +
   fragile). 207 -> 122 params; **108/111 reals converge** (was 56/118).

**Result (pilot points + heads + baseflow, 122 params, ies):** a realization at the baseflow
target has **NSE 0.10, baseflow 0.609 m3/s** (vs observed +0.63) -- head-positive AND correctly
gaining, the first time both hold. Best head NSE 0.26; 17/108 gaining. Fitted: pump 14.5% of
capacity, per-order incision 2.4-2.9 m -- all physically sensible.

**Remaining head/baseflow tension** (best-NSE realizations lean losing; best-baseflow lean to
lower NSE) is now small and reflects the residual RIV structural limit. The robust next step is
**RIV -> SFR** (proper streambed; also needed for Phase-3 PFAS in-stream transport). The model
is now structurally correct (real streams, corrected pumping, deep geometry, GHB boundary,
SWAT recharge) and the calibration finds physically-meaningful parameters.

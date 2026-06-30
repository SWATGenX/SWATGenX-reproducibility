# MF6 static-head calibration — diagnosis (04124500)

**Verdict: the static-head misfit on 04124500 is a model-geometry problem, not a
parameter-calibration problem. A PSO over K/recharge/conductance cannot fix it.** Stopping
before spending AWS compute; this needs a structural decision.

## What I built (reusable, correct)

`MODFLOW/MODGenX/mf6_head_calibration.py` — a clean MF6 port of the archived NWT
`MODFLOW_PSO.py`: kriging-stderr tercile **zones**, per-zone **K multipliers** (Kh/Kv ×2
aquifers ×3 zones) + recharge + river/drain conductance multipliers (15 params), and an
objective = −NSE of topmost-active simulated head vs the 510 observed Wellogic wells
(1–99 pctile trim), exactly matching `read_plot_evaluate`. Single eval ≈ 3 s; verified
working. `zones_04124500.npz` built from the stderr rasters. This is ready to run the
moment the geometry issue below is resolved.

## The evidence (every probe, 04124500, trimmed n≈486)

| configuration | NSE | RMSE (m) | PBIAS (%) |
|---|---|---|---|
| baseline (uncalibrated) | −0.95 | 20.8 | +7.8 |
| all K ×10 | −0.86 | 20.3 | +7.4 |
| all K ×0.1 | −1.01 | 21.4 | +8.2 |
| recharge ×0.5 | −0.88 | 20.4 | +7.5 |
| river+drain cond ×0.1 | −0.96 | 20.8 | +7.8 |
| K ×10 + recharge ×0.5 + cond ×10 | −0.85 | 20.2 | +7.4 |
| blanket drain removed | −1.91 | 25.7 | +10.6 |
| drain elevation −3 m (or lower) | **fails to converge** | | |
| drain set to kriged SWL elevation | **fails to converge** | | |

The objective is locked at NSE ≈ −0.85…−1.0 / PBIAS +7–11 % across the **entire feasible
parameter space**. No combination of the calibratable parameters moves it.

## Root cause (three linked facts)

1. **Blanket drain.** MODGenX puts a DRN on **100 % of active cells** (2895/2895) at
   elevation = land surface − 1 m, with conductance ~70 000 m² d⁻¹. This clamps the
   simulated water table to ~1 m below ground *everywhere* → simulated head ≈ surface−1 m
   regardless of K/recharge. That is why nothing I tune has leverage.
2. **The real water table is deep.** The kriged SWL raster (MODGenX's own data) puts the
   observed water table a median **18 m** and locally **up to 66 m** below ground — a sandy,
   high-relief outwash watershed (Pere Marquette). Observed head spread 187–240 m vs
   simulated 227–248 m: the model is both ~15 m too high and far too flat.
3. **The aquifer is too thin to hold a deep table.** The Wellogic `AQ_THK` kriging gives
   aquifer thicknesses of only ~1–14 m per unit. When the drain is lowered toward the real
   (deep) SWL, the thin cells go dry and the Newton solve diverges. The model geometry
   physically cannot represent a water table 18–66 m deep.

So the blanket drain is masking a geometry deficit: layers too shallow to contain the true
water table, with a surface drain pinning heads near the top so the model still converges.

> Note: 04124500 is the hard case. Two other converged models (04080206, 040900010212) fit
> observed heads at NSE 0.92–0.94 *uncalibrated* with the same structure — their water
> tables are genuinely shallow, so surface−1 m is about right. The defect bites where the
> real table is deep.

## Options (need user steer — structural + affects MODGenX for all models)

A. **Deepen the model geometry.** Extend DIS bottoms to a real depth-to-bedrock (not the
   thin Wellogic productive-aquifer thickness) so the domain can contain an 18–66 m table,
   then drains only on stream cells at incised elevations + calibrate K. Biggest change;
   needs a depth-to-bedrock source.
B. **Drain elevation as the SWL surface + thicker single upper layer.** Set the diffuse
   drain to the kriged SWL elevation and merge the thin upper layers into one thick layer so
   cells don't dry. Uses data already on hand; moderate change to the builder.
C. **Re-target the objective.** If these deep Wellogic wells are screened in deeper/confined
   units, comparing to the topmost (water-table) layer is unfair; score against the well's
   actual screen layer instead. Cheapest to test; may explain part of the bias.
D. **Accept 04124500 as out of scope** for head calibration and demonstrate the (working)
   calibration machinery on a shallow-table model (04080206) where it has leverage.

How was aquifer thickness / model depth handled in your prior NWT calibrations — did those
models use a deeper bottom or a thicker upper layer?

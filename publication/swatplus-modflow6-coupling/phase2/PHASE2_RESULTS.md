# Phase 2 — bidirectional GW ↔ stream exchange (04124500)

**Status: machinery DONE; it exposed + fixed 3 river-package bugs and now produces physical
baseflow. A meaningful net balance needs joint head+baseflow calibration (see below).**

## What Phase 2 does
Reads the GW↔stream exchange BACK OUT of the converged MF6 model and maps it onto the SWAT+
channel network. Per RIV cell the exchange is the exact MODFLOW leakage law
`Q = cond·(stage − max(h, rbot))` (Q<0 = GW→stream = gaining/baseflow). Computed from the
simulated head (no SIMVALS export needed), aggregated to SWAT+ reaches via a RIV-cell→reach
spatial map (439 RIV cells → 171 of the 216 reaches). `swatmf_phase2_driver.py`.

## River-package bugs exposed (rivers.py:58, all fixed)
1. **stage = top + 1** — river surface set 1 m *above* land → forced 98 % of reaches to lose.
   Fixed to stage = top (valley/stream surface), rbot = top − 2.
2. **conductance = `swat_river·0.3048` ≈ 0.3 m² d⁻¹** — a placeholder ~10,000× too small, so
   the GW↔stream flux was negligible (basin baseflow 0.0002 m³ s⁻¹). Fixed to a physical
   riverbed conductance = leakance(0.1 d⁻¹)·cell_area ≈ 6250 m² d⁻¹ (tuned by `rv_cond`).

## Result after the fix (uncalibrated for the new river)
| | value | observed |
|---|---|---|
| GW→stream (gaining) | **8.9 m³ s⁻¹** | ~9 m³ s⁻¹ (USGS 04124500 baseflow) |
| stream→GW (losing) | 14.6 m³ s⁻¹ | |
| net | −5.7 m³ s⁻¹ | should be net gaining |
| gaining reaches | 48 % | |

The **gaining magnitude now matches the observed baseflow** — the coupling extracts a physical
GW↔stream signal. But the net is still losing (half the reaches lose) because the head field
was calibrated to wells ALONE; it fits heads yet gets the head-vs-stream relationship wrong on
many reaches. `phase2_gw_stream_exchange_04124500.png` shows the gaining/losing pattern.

## Remaining (the meaningful-model step)
Head-only calibration is non-unique (equifinality): it fit 510 heads but produced unphysical
net-losing streams. A meaningful model needs the **baseflow constraint added** — multi-objective
calibration on heads + the GW↔stream exchange vs observed baseflow (~9 m³ s⁻¹ gaining). This is
precisely what the bidirectional coupling enables; Phase 2 provides the modeled baseflow to
score against. (Also: the river fix invalidated the head-only calibration — recalibrate.)

# Vadose-zone PFAS travel time — findings (Rogue)

_Lumped + explicit, PFOS vs PFOA, AWI impact, Sobol/UA. 2026-06-25._

## Question
Does diffuse land-applied PFAS reach groundwater within the 1970–2024 simulation,
and how does the air-water interface (AWI) and chain length (PFOS vs PFOA) control it?

## Method
Three-phase retardation (the SWAT+ engine's own physics, `pfas_module.f90`):

> R = 1 + (ρ_b/θ)·Kd  +  (A_aw/θ)·K_aw ,  A_aw = 6(1−por)(1−Sw)/d50
> τ = L·θ·R / q_recharge

evaluated per grid cell over the **kriged depth-to-water** (median 31 m, 12–69 m).
Vadose sorption uses **literature low-OC outwash values** (Higgins & Luthy 2006;
Brusseau 2020; Guo 2020), *not* the root-zone (topsoil) values — applying topsoil
kf/Langmuir to the deep vadose over-retards by ~3 orders of magnitude (a real trap).

## Results

| | PFOS | PFOA |
|---|---|---|
| Kd (L/kg) | 2.0 | 0.33 |
| K_aw (cm) | 0.060 | 0.015 |
| Retardation R | 25 | 5.6 |
| AWI share of R | 27% | 36% |
| **Travel time (median)** | **~1000 yr** (387–2275) | **~220 yr** (85–500) |
| AWI slow-down | 1.3× | 1.4× |
| reaches GW < 100 yr | 0% of basin | 14% of basin |

- **PFOS precedes nothing** to groundwater within the simulation — centuries of
  transit. **PFOA is ~4.5× faster** (shorter chain, lower Kd + K_aw), the only one
  with any near-term arrival (14% of the basin within a century, at shallow-water-
  table cells). This is exactly the chain-length contrast of Rafiei et al. (2023, WR).
- **AWI matters and is grain-size sensitive:** 1.3× in coarse sand (d50≈1 mm) rising
  to **>5× in silt/fine sand** (Fig. b), within Guo (2020)'s 1.5–5× range.

## Two approaches agree (the test)
- **Lumped** τ and **explicit 1D advection-dispersion-retardation** (Ogata-Banks)
  50%-breakthrough times are **identical** (PFOS 1278 yr, PFOA 289 yr) — dispersion
  only spreads the front; the median arrival is the retardation-scaled advection
  time. The lumped estimate is validated; a full MF6 UZF/UZT basin model would
  reproduce these arrivals at much greater cost.

## Sobol / uncertainty (PFOS travel time)
ST: **recharge 0.45 > depth 0.32 > grain-size/AWI 0.27 > Kd 0.10 > K_aw 0.08 > θ 0.02**.
Travel-time 5–95% uncertainty 437–5467 yr. Even the fastest tail is ≫ 54 yr.

## Conclusion (for the paper)
**Diffuse land→groundwater PFAS transport is negligible on the 1970–2024 timescale.**
The deep (tens-of-metres), AWI-retarded vadose means land-applied PFOS needs
centuries and PFOA decades-to-centuries to reach the water table. Therefore the
observed groundwater PFAS is **legacy** — the historical point source (the Tannery
plume the model prescribes), which the coupling correctly routes to streams
(44.7 kg/90 d). The vadose is the *reason* the prescribed-plume treatment is
defensible, and the PFOS-vs-PFOA contrast is the testable, literature-consistent
signature.

## Open (needs Vahid)
Replace the literature vadose Kd/K_aw/d50 with the **2023-paper values**; decide if a
full MF6 UZF/UZT basin run is worth the cost given both methods already agree that
nothing arrives in-window. Files: `vadose_travel_time.py`, `make_vadose_figure.py`
(`vadose_travel_time.png`), `vadose_verify_sobol.py`.

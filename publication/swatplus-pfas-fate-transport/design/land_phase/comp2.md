Clean compile (exit 0, no diagnostics). Both files compile against the engine's real symbols for everything that exists, and against faithful stubs for the new PFAS constituent plumbing (`hcs*%pfas`, `ch_pfas_water/benthic`) that this feature adds — mirroring the existing `%pest` / `ch_water` / `ch_benthic` slots exactly.

DELIVERABLE

Two files written and compile-verified (`gfortran -ffree-form`, exit 0):
- `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_cha.f90` — the in-stream + reservoir PFAS routing routine (SERIAL channel phase).
- `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_cha_module.f90` — companion reach state/output module (the PFAS analogue of `ch_pesticide_module`, plus the in-stream linear-Koc parameter DB `pfas_chadb`).

KEY FINDING — REUSE vs. NEW
Legacy `rtpfas.f` / `lakeqpfas.f` use a LINEAR Koc downstream (no Freundlich/Langmuir in-stream). That makes them a physical SUBSET of the existing SWAT+ `ch_rtpest.f90`: identical settling / resuspension / sediment-water diffusion / burial / advective-in-out machinery, all driven by `frsol = 1/(1+kd*sedcon)`. PFAS just drops the three pesticide-only loss terms (chemical/biological reaction `decay_a/decay_b`, volatilization `aq_volat`, metabolite daughters `num_metab`).

So there are two valid integration paths, and I documented both in the file header:

1. Cleanest (recommended if no separate PFAS columns needed): route each PFAS THROUGH `ch_rtpest` as a pesticide-type constituent. Exact DB mapping (in the `pfas_cha.f90` header table): `chpfas_koc→pestdb%koc` (note `kd = koc*carbon/100`), `chpfas_stl→aq_settle`, `chpfas_rsp→aq_resus`, `chpfas_mix→sd_ch%aq_mix`, `sedpfas_bry→ben_bury`, `sedpfas_act→ben_act_dep`; inflow `varoute(34/35)→hcs1%pest` (combined sol+sorbed, repartitioned daily by frsol/frsrb); storage `chpfas_conc*rchwtr→ch_water%pest`, `sedpfas_conc*bedvol→ch_benthic%pest`; outflow `solpfaso/sorpfaso = frsol/frsrb * hcs2%pest`; and ZERO `decay_a=decay_b=1.`, `aq_volat=0.`, `num_metab=0`.

2. Dedicated (what I shipped): `pfas_cha` — the linear-Koc subset of `ch_rtpest`, wired to dedicated `pfas`-slot constituent containers and named from `pfasdb`, giving distinct PFAS reach output and avoiding koc carbon-scaling coupling.

INTEGRATION DEPENDENCIES (new plumbing this feature must add, mirroring `%pest`):
- `pfas` real-allocatable slot on `hyd_output` (for `hcs1%pfas`/`hcs2%pfas`) and on `constituent_mass` (for `ch_pfas_water`/`ch_pfas_benthic`), dimensioned `npfas`.
- Call site: in `sd_channel_control3.f90`, alongside the `if (cs_db%num_pests > 0) call ch_rtpest` block, add `if (npfas > 0) call pfas_cha` then `obcs(icmd)%hd(1)%pfas = hcs2%pfas`.
- `pfas_chadb(:)` (type `pfas_cha_db`) populated from the PFAS input file with `koc, aq_settle, aq_resus, ben_bury, ben_act_dep`.
- Allocate `chpfas_d/m/y/a(nrch)` and each `%pfas(npfas)`; a `cha_pfas_output(jrch)` writer copying `cha_pesticide_output.f90` verbatim with `chpst_*→chpfas_*` and the header below.

REACH-OUTPUT FIELD LIST (`pfas_cha_processes`, units kg unless noted; column headers from `pfas_cha_header`):
- `tot_in`  — tot_in_kg — total PFAS into reach (= inflow `hcs1%pfas`)
- `sol_out` — sol_out_kg — soluble PFAS out of reach (`frsol*hcs2%pfas`)
- `sor_out` — sor_out_kg — sorbed PFAS out of reach (`frsrb*hcs2%pfas`)
- `settle`  — settle_kg — PFAS settling water→bed
- `resus`   — resuspend_kg — PFAS resuspended bed→water
- `difus`   — diffuse_kg — sediment-water diffusive exchange (signed)
- `bury`    — bury_benth_kg — PFAS buried out of active bed layer
- `water`   — water_stor_kg — PFAS in reach water at end of day
- `benthic` — benthic_kg — PFAS in bed sediment at end of day

(Pesticide's `react`, `metab`, `volat`, `react_bot`, `metab_bot` are intentionally omitted — PFAS is non-degradable/non-volatile.)

Note: the soil `pfas_module%pfas_db` carries no in-stream routing params (by design — those are soil/equilibrium), so I put `koc/aq_settle/aq_resus/ben_bury/ben_act_dep` in the new `pfas_chadb` and kept only the `sol` solubility-cap lookup reaching back into `pfasdb` (via a tiny contained accessor). The serial routine writes shared per-reach state and is correctly NOT reentrant-guarded — that is appropriate for the serial channel phase (the parallel HRU/soil equilibrium lives in `pfas_module%pfas_partition`).
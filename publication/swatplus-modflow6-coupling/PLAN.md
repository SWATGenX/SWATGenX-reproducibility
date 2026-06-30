# Full SWAT+ ↔ MODFLOW 6 coupling — project plan

Status: planning (2026-06-21). Companion feasibility report:
`_temp/modflow6/SWATplus_MF6_coupling_feasibility.md`. MF6 source clone:
`_temp/modflow6`. Memory: `swatplus-mf6-coupling`.

## Source control & MF6 fork

- **MF6 fork:** `rafiei-vahid/modflow6` (private) — forked 2026-06-21, symmetric with the
  `rafiei-vahid/swatplus` fork. We develop against **stock** MF6 (external XMI/BMI API);
  the fork is for **reproducibility** (pin the exact MF6 version the papers build
  against) and **insurance** (patch a BMI/XMI hook only if the Phase-0 spike finds a
  needed array isn't exposed). Make it public at submission for reproducibility.
- **Working clone:** `_temp/modflow6` — `origin` = our fork, `upstream` = MODFLOW-USGS,
  full history (unshallowed) + tags. Currently on `develop` (`6.8.0.dev0`). **Pin to the
  `6.7.0` release tag (latest stable) for the spike and all paper builds** — `git checkout
  6.7.0` — and record the commit here; do not build the papers against a dev snapshot.
- **Coupling code** lives in this SWATGenX repo (`publication/swatplus-modflow6-coupling/`
  + a coupler module under `MODFLOW/`), NOT in the MF6 fork; MF6 source is referenced by
  version, never vendored into SWATGenX.

## 0. Goal

A loosely (sequentially) coupled, daily, bidirectional surface-water–groundwater
model: SWAT+ solves the land/channel surface system and MODFLOW 6 solves the
groundwater system, exchanging **recharge** (SWAT+ → MF6) and **groundwater–stream
exchange / baseflow** (MF6 → SWAT+) each day, with optional **well extraction**.
Built on the automated SWATGenX/MODGenX generation so a coupled model can be
produced for any Michigan-LP location (CONUS later). Final extension: route **PFAS
in groundwater** through MF6 Groundwater Transport (GWT) — the differentiator.

Non-goal (v1): ParFlow-style tight (single-matrix) SW–GW coupling. We do operator-
split loose coupling, with optional iterate-to-convergence only if mass balance
demands it.

## 1. Architecture decision (settled)

**External API coupling via `libmf6.so` + the MODFLOW 6 XMI/BMI interface
(`xmipy` / `modflowapi`). Do NOT embed MF6 source into the SWAT+ executable.**

Rationale: MF6 is an object-oriented multi-model framework (Mf6Core owns the time
loop, each Solution owns its linear system, state lives in a Memory Manager). The
XMI was purpose-built for an external program to own the time loop. Embedding means
re-driving Mf6Core from SWAT+ `main.f90` and inheriting MF6's IDM/Memory-Manager +
ifx/NetCDF build — re-implementing what XMI already exposes. Effort: embed ≈ 6–12
months; external API ≈ 2–4 months.

Coupler process (Python, alongside the SWAT+ run):

```
mf6 = modflowapi/xmipy over libmf6.so
mf6.initialize()                       # TDIS configured DAILY from the start
for day in simulation:
    swatplus.run_day()                 # land phase -> per-HRU percolation, channel state
    recharge_cells = map_HRU_to_cells(swatplus.perc)     # SET
    mf6.set_value('<MODEL>/RCHA/RECHARGE', recharge_cells)
    mf6.set_value('<MODEL>/WEL-1/BOUND', well_rates)      # optional
    mf6.prepare_time_step(dt); mf6.do_time_step(); mf6.finalize_time_step()
    gw_stream_flux = mf6.get_value('<MODEL>/RIV-1/SIMVALS')  # GET (or SFR GWFLOW)
    swatplus.add_baseflow_to_channels(gw_stream_flux)    # before channel routing
mf6.finalize()
```

Note: MF6 ignores the `dt` argument after init — TDIS **must** be daily from the
start. Resolve every variable address with `get_var_address(...)` (never hand-build
mempath strings). Per-day handshake variables (verified in MF6 source):

| Direction | Quantity | MF6 variable |
|---|---|---|
| SET SWAT+→MF6 | recharge | RCH `RECHARGE` (array) / `BOUND` (list) |
| SET SWAT+→MF6 | well extraction | WEL `BOUND` / `Q` |
| GET MF6→SWAT+ | GW↔stream flux (baseflow) | RIV/DRN `SIMVALS`, or SFR `GWFLOW` |
| GET MF6→SWAT+ | heads | Solution `X` |

## 2. The spatial mapping objects (the user's mental model)

1. **HRU → DHRU.** SWAT+ HRUs are lumped, non-spatial. Disaggregate into geo-located
   "disaggregated HRU" polygons so recharge has a real location. **(net-new; the main
   novel mapping object)**
2. **DHRU → MF6 cell.** Polygon × grid intersection → area-weighted fractions that
   spread each DHRU's deep percolation across overlapping cells.
3. **River → cell.** SWAT+ channel × grid intersection → which cells exchange with
   each channel (RIV/DRN, or SFR reaches).
4. **Lake → cell.** Reservoir/lake × grid intersection → LAK or DRN cells.
5. **Well → cell.** Pumping points → WEL cells.

Reuse: SWAT+gwflow (already in our `swatplus_perf` build, 18 `gwflow_*.f90`) carries
exactly this map family in-memory (`hru_cells`/`cell_hrus`/`hru_cells_fract`,
`gw_chan_info`, the `groundwater_ss` flux enumeration, recharge-delay, Darcy
GW↔channel). MODGenX already builds the grid + river/lake/well maps (for NWT). The
**new** piece is the vector DHRU map + the *daily* SWAT+-percolation handoff
(MODGenX today injects a single static annual recharge raster).

## 3. Phased roadmap

### Phase 0 — De-risking spike (~1–2 weeks)
- [x] `pip install xmipy modflowapi`; official MF6 **6.7.0** `libmf6.so` via flopy
  `get-modflow`. Smoke-tested.
- [x] **API handshake PROVEN** (`phase0_spike/`, `SPIKE_RESULTS.md`): a minimal MF6
  model driven via xmipy — SET `RCHA_0/RECHARGE`, step, GET `RIV_0/SIMVALS` + heads;
  raising recharge raised heads + GW→stream baseflow. Addresses, sign convention
  (negative RIV = aquifer→river baseflow), and the BICGSTAB-for-NEWTON gotcha recorded.
- [x] **Ported the real Rogue NWT model to MF6** (`phase0_port_rogue.py`): all packages
  translate; MF6 **converges** on the 60k-cell grid (NWT didn't), median head agreement
  1.05 m vs the non-converged NWT reference. Drove the full model via xmipy
  (`spike2_rogue_api.py`): SET recharge ×1.5 → mean head 226.6→228.9 m — **handshake
  PROVEN AT SCALE**. Key timing fact: SET *after* `prepare_time_step`.
- **Phase 0 COMPLETE.** (Side finding: the MODGenX model conditioning is poor — same
  convergence warning as the dashboard order — worth fixing in MODGenX independently.)

### Phase 1 — MVP: one-way SWAT+ → MF6 flow coupling — **COMPLETE** (see `phase1/PHASE1_RESULTS.md`)
- [x] Port `MODGenXCore.create_modflow_model` NWT → MF6 (`mf6_builder.py`,
  convergence-by-construction). Structured raster grid (DIS) for v1.
- [x] Build the **vector HRU → cell** area-weighted map (`swatmf_coupling.build_hru_cell_map`;
  for SWAT+ the HRU polygons are geo-located so HRU→DHRU disaggregation is unnecessary).
- [x] Aggregate **daily SWAT+ percolation** (`hru_wb_day.nc` `perc`) onto grid cells via a
  sparse area-weighted matrix-multiply, replacing the static `Recharge_250m.tif`.
- [x] Configure TDIS daily; SET recharge per day via the MF6 BMI/XMI API (`modflowapi`,
  in-place `RCHA/RECHARGE` pointer write); run MF6 stepwise. *No return path yet.*
- [x] Deliverable: SWAT+-driven **transient** MF6 heads on 04124500 — 1096/1096 daily
  steps converged, head swings ±0.16 m about the 232.41 m steady baseline tracking the
  seasonal recharge signal (`swatmf_phase1_driver.py`, `phase1_coupling.png`).
  *Remaining: HOB validation against observed Wellogic wells over the transient window.*

### Phase 2 — Bidirectional GW ↔ river return (~1–2 months)
- After each `do_time_step`, GET `SIMVALS` (RIV/DRN) or `GWFLOW` (SFR); feed baseflow
  back into SWAT+ channel routing at the per-day hook (after land phase, before
  routing).
- Decide **RIV vs SFR** for streams here (SFR enables SFT-routed in-stream solute,
  needed for PFAS in Phase 3; RIV is simpler).
- Measure loose-coupling drift on gaining/losing reaches; add iterate-to-convergence
  only if mass balance demands it.
- Deliverable: closed daily SW↔GW water balance; baseflow signature in the channel
  hydrograph; re-validated streamflow at Rockford.

### Phase 3 — PFAS-GWT add-on (~1–2 months)
- FloPy `flopy.mf6` generates the GWF + GWT + exchange stack (supported).
- Wire SWAT+ PFAS leaching (`pfas_lch.f90` daily `perc` mass + aqueous `cw`) into
  **SRC** (mass-preserving) or **SSM** (concentration-preserving) at recharge cells.
- **FMI** couples GWT advection to the GWF flow field; **MST** handles sorption.
- Sorption: MST supports **Linear / Freundlich / Langmuir** natively. Use **Freundlich**
  (PFAS standard) per congener. Air-water-interface sorption is vadose-only (absent
  below the water table), so the saturated-zone isotherm is physically complete, not
  an approximation. Keep the three-phase soil equilibrium in SWAT+ (land limb).
- Return dissolved PFAS to streams via **SFT/MVT** (requires SFR from Phase 2).
- Constraints: MST = one isotherm/model; GWT = single-solute/model → stack a GWT per
  congener (start with terminal PFOS, mixtures later). Optional **IST** for back-
  diffusion tailing (a further differentiator).
- Deliverable: integrated SW–GW PFAS fate-transport on the Rogue; GW PFAS plume +
  GW→stream PFAS return — the contribution that overcomes the 2023 RT3D gap (RT3D ran
  but no contaminant was transported in groundwater).

## 4. Validation strategy
- Phase 1/2: MF6 heads vs NWT baseline + EGLE Wellogic observation wells (HOB);
  streamflow at USGS 04118500; daily SW↔GW water-balance closure.
- Phase 3: GW PFAS vs any available groundwater PFAS samples near the Wolverine
  corridor; in-stream PFAS with vs without the GW return term (attribution).

## 5. Risks (from the adversarial review)
- `xmipy`/`modflowapi` not yet in our venv — thin ctypes wrappers over the proven C
  ABI; smoke-test in Phase 0.
- MODGenX recharge is static/one-way today — the daily SWAT+→RCH map is net-new.
- MF6 ≠ byte-identical to the validated NWT calibration record → re-validate.
- BMI grid metadata is partial for unstructured DISV/DISU (full only for DIS) — keep
  the structured grid for v1; revisit unstructured/XT3D later.
- Units glue (daily HRU perc mass → cell recharge → SSM conc / SRC mass-rate) is a
  likely mass-balance error source; SRC preserves mass, SSM preserves concentration —
  pick per goal.
- Coverage is Michigan-LP only (K/SWL/AQ_THK kriged from EGLE Wellogic). CONUS needs
  national well data + a national recharge source.

## 6. Prior art to cite / differentiate
- Bailey et al. SWAT-MODFLOW (NWT, embedded), Hydrological Processes 2016.
- SWAT+gwflow (native grid GW in SWAT+), Bailey et al. 2020.
- "SWAT+MODFLOW: a new hydrologic model", GMD 18:5681 (2025) — closest prior art
  (multi-layer, daily fractional-area coupling) **but MODFLOW-NWT and no contaminant
  transport**. Our edge = MF6 (GWT/GWE/PRT, unstructured, XT3D) + automated national
  generation + **PFAS in groundwater**.
- Rafiei & Nejadhashemi 2023 (SWAT-MODFLOW-RT3D, Water Research 240:120073) — the
  framework existed but no PFAS was transported in groundwater; Phase 3 overcomes it.

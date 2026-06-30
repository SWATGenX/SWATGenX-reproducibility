All symbols verified. I have everything needed. Producing the decision-grade build manifest.

---

# PFAS SURFACE-WATER BUILD MANIFEST — SWAT+ engine

Engine root: `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine`
Verified against the live tree: anchors, symbols, CMake glob, and the target model all confirmed below.

---

## 1. FILE MANIFEST

### 1A. New files — already delivered (compile-verified), drop into `src/`
| File | Purpose |
|---|---|
| `src/pfas_module.f90` | Container types (`pfas_db`, `pfas_soil*`) + solver (`pfas_partition`, `pfas_awi`); module-level `npfas`, `pfas_num`, `pfas_flag`, `pfasdb`, `pfas_soil_hru`. |
| `src/pfas_read.f90` | **Combined** reader: `pfas.dat` DB + `pfas_hru.ini` per-HRU pools + allocation. (This is `subroutine pfas_read`.) |
| `src/pfas_output_module.f90` | Per-HRU/per-PFAS daily land-loss accumulators `hpfasb_d(j)%{surq,latq,perc,sed}`. |
| `src/pfas_lch.f90` | Land-phase leach/runoff/lateral routine (`subroutine pfas_lch`). |
| `src/pfas_sed.f90` | Sediment-bound erosion loading (`subroutine pfas_sed`). |
| `src/pfas_cha_module.f90` | Reach state/output + in-stream `pfas_chadb` (linear-Koc params) + `chpfas_{d,m,y,a}`. |
| `src/pfas_cha.f90` | Serial in-stream PFAS routing (`subroutine pfas_cha`). |

### 1B. New files — STILL TO WRITE (the integration map assumes these but they were not delivered)
| File | Purpose | Status |
|---|---|---|
| `src/pfas_output.f90` (or fold into output flush) | Daily/monthly HRU + channel PFAS **file writers** (headers + `write` of `hpfasb_d` / `chpfas_*`). | **MISSING** — accumulators exist, no writer. Minimal smoke test can skip this (see §3). |

> **NAMING RECONCILIATION (decision needed):** the integration map (Component 4) calls for four separate readers — `pfas_parm_read`, `pfas_hru_read`, `pfas_init` — but Component 1 shipped a **single** `pfas_read.f90` doing DB + per-HRU read + allocation in one pass. **Recommendation: use the delivered single `pfas_read` and call it once from `proc_read.f90`** (not the 3-call split). This is simpler and already end-to-end tested. The §2 diffs below are written for the **single-reader** path. If you prefer the map's split, that is a rewrite, not an integration pass.

### 1C. Existing files to MODIFY
| File | Change |
|---|---|
| `src/input_file_module.f90` | Add `pfas = "pfas.dat"` near L180 (in `in_parmdb`) and `pfas_soil = "pfas_hru.ini"` near L230. (Cosmetic — `pfas_read` currently hardcodes filenames; only needed if you route through the slots.) |
| `src/maximum_data_module.f90` | Add `integer :: pfasparm = 0` to `db_max` (~L25) if `pfas_read` is changed to set `db_mx%pfasparm` (currently it does **not**). |
| `src/proc_read.f90` | Add `pfas_read` to `external` (L5–16); add `call pfas_read` after `call cs_hru_read` (L42). |
| `src/hru_module.f90` | None (symbols `surfq`, `sedyld`, `enratio`, `hru%area_ha` all exist). |
| `src/hru_control.f90` | `external :: pfas_lch, pfas_sed`; `use pfas_module`; after `call pest_soil_tot` (L521) add `if (npfas>0) call pfas_lch`; inside the `precip_eff>0` block after `pest_pesty` (L526) add `if (npfas>0 .and. sedyld(j)>0.) call pfas_sed`. |
| `src/hydrograph_module.f90` | Add `real, dimension(:), allocatable :: pfas` to type `hyd_output` (L31–50), so `hcs1%pfas`/`hcs2%pfas` exist. |
| `src/constituent_mass_module.f90` | Add `real, dimension(:), allocatable :: pfas` to type `constituent_mass` (~L80); declare `ch_pfas_water(:)`, `ch_pfas_benthic(:)` (mirror `ch_water`/`ch_benthic` at L115–117). **`pfas_cha` already `use`s these — they MUST be added or `pfas_cha` will not link.** |
| `src/sd_channel_control3.f90` | `external :: pfas_cha`; `use pfas_module, only: npfas`; after the L168–171 `ch_rtpest` block add `if (npfas>0) then; call pfas_cha; obcs(icmd)%hd(1)%pfas = hcs2%pfas; end if`; replicate at the L365 set block. |
| `src/proc_open.f90` (or wherever channel/HRU output units open) | Allocate `chpfas_{d,m,y,a}(sp_ob%chandeg)` and `%pfas(npfas)`; allocate `hpfasb_d(sp_ob%hru)` and `%{surq,latq,perc,sed}(npfas)`; allocate `ch_pfas_water/benthic(nrch)%pfas(npfas)` and `hcs1/hcs2%pfas(npfas)`. **This allocation site is the single biggest missing piece** — see Open Questions Q1. |

---

## 2. COMPILE ORDER / CMAKE

**CMake: NO edit required.** Confirmed `CMakeLists.txt:159` is `file(GLOB sources src/*.f90)` → every `src/pfas_*.f90` is picked up. Fortran module deps are resolved by the build system's dependency scanner; no manual ordering needed. **You must re-run `cmake` configure** (the glob is captured at configure time) after adding files — a bare `make` will not see new files.

Module-dependency order (for reference / if anyone ever pins an explicit list):
```
pfas_module ─┬─> pfas_read           (use pfas_module, hydrograph_module, soil_module, maximum_data_module, input_file_module)
             ├─> pfas_output_module
             ├─> pfas_lch            (use hru_module, soil_module, pfas_module, pfas_output_module)
             ├─> pfas_sed            (use hru_module, pfas_module, pfas_output_module)
             └─> pfas_cha_module ──> pfas_cha   (use ...pfas_cha_module, pfas_module, hydrograph_module, constituent_mass_module)
```
Hard requirement: `pfas_module` and `pfas_output_module` and `pfas_cha_module` compile before the routines that `use` them — GLOB handles this automatically.

---

## 3. SMOKE-TEST PLAN

### 3.0 Path correction (important)
The TxtInOut is one directory deeper than the prompt states. **Actual path:**
```
${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0410/huc12_outlet/041000130106/SWAT_MODEL_Web_Application/Scenarios/Default/TxtInOut
```
Confirmed contents: `file.cio`, `hru-data.hru` (16,755 HRUs), `pesticide.pes`, `soils.sol`, **empty `constituents.cs`**, 1-year sim (2024, 366 days). 16k HRUs is heavy for a smoke test — see Q4.

### 3.1 Compile (serial / stock, per develop-on-serial rule)
`ifx` is on PATH for this engine (build dir `build/ifx-release_o2` exists). Develop-on-serial = **no OpenMP flag**, single-thread, stock optimization:
```bash
cd /data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine
cmake -S . -B build/pfas-serial -DCMAKE_Fortran_COMPILER=ifx \
      -DCMAKE_Fortran_FLAGS="-O2"        # NO -qopenmp  (serial)
cmake --build build/pfas-serial -j
```
Gfortran fallback if ifx unavailable: `-ffree-form` is irrelevant (engine is free-form `.f90`); use `gfortran -O2 -ffree-line-length-none`. (Per MEMORY: gfortran can fail on large models — so a large-model crash here is a real bug, but for *compile-only* gfortran is fine.)

### 3.2 Minimal single-PFAS (PFOS) input set
Work in a **copy** of Default so the no-PFAS baseline is preserved:
```bash
cp -r .../Scenarios/Default .../Scenarios/PFAS_smoke
```
Add three files to `.../PFAS_smoke/TxtInOut`:

**`pfas.dat`** (DB, terminator-stopped):
```
pfas.dat: PFAS compound database (smoke)
 id  name        mw        sol      kl       lm        percop
  1  PFOS    0.50013    680.0    0.0456   3.05e-6   0.50
  0  END     0.0        0.0      0.0      0.0       0.0
```

**`constituents.cs`** — append PFAS block (file is currently empty; must also carry the pest/salt/cs preamble the reader expects — match `constit_db_read` format). Minimum: a `num_cs`/pest header consistent with the existing parser plus:
```
1
PFOS
```

**`pfas_hru.ini`** — one record set per HRU in HRU order (title + header, then per HRU: name line, `num_pconta`, per-layer `sol_d50`, then PFOS quad sol_pfas/kf/nf/enr). Use the `pfasid<=0` sentinel for the vast majority of HRUs and seed **one** HRU with non-zero PFOS mass (e.g. `1000.0` µg/ha) to exercise the solver. (Generating 16k records by hand is impractical — script it; see Q4 for the small-model alternative.)

### 3.3 Run
```bash
cd .../Scenarios/PFAS_smoke/TxtInOut
/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/build/pfas-serial/<exe>
```

### 3.4 Acceptance checks
1. **Compiles** — `cmake --build` exit 0, zero unresolved symbols (esp. `hcs1%pfas`, `ch_pfas_water` — the §1C plumbing). 
2. **Runs** — process exits 0 on the seeded model; `simulation.out`/log clean; no NaN in PFAS output.
3. **Per-HRU mass balance closes** — for the seeded HRU, per day:
   `Σ_layers Δsol_pfas == surq + latq + perc + sed` (within ~1e-7 rel, the solver's validated residual). Instrument by summing `hpfasb_d(j)%{surq,latq,perc,sed}` against the pool decrement. Solver itself is validated to 5.4e-8 mass-balance residual.
4. **One-thread byte-identity for non-PFAS output** — diff every **non-PFAS** output file (flow, sediment, nutrients, pesticide) between the `PFAS_smoke` run and the original `Default` (no-PFAS) run, both **serial**. Must be **byte-identical**. This is the regression gate: PFAS must be purely additive. Drive it:
```bash
for f in channel_sd_day.txt hru_wb_day.txt ...; do
  cmp .../Default/.../$f .../PFAS_smoke/.../$f && echo "IDENTICAL $f"; done
```
   Any non-PFAS diff ⇒ a write leaked into shared state (most likely an over-allocation or a mis-indexed `obcs` write).

---

## 4. OPEN QUESTIONS / RISKS for the integration pass

**Q1 — Allocation home is unspecified and is the critical gap.** `pfas_cha` `use`s `hcs1%pfas`, `hcs2%pfas`, `ch_pfas_water`, `ch_pfas_benthic`, and `pfas_chadb`; `pfas_lch`/`pfas_sed` write `hpfasb_d(j)%...`. **None of these are allocated anywhere in the delivered code.** You must add an init block (after `pfas_read`, before time loop) that sizes `hpfasb_d(sp_ob%hru)`, `chpfas_*(nrch)`, `ch_pfas_water/benthic(nrch)`, `hcs1/hcs2%pfas`, and **populates `pfas_chadb`** (its source file is undefined — `pfas.dat` carries no koc/settle/resus/bury params; see Q2). Without this, the link fails or runs un-allocated.

**Q2 — In-stream params have no input file.** `pfas_chadb` needs `koc, aq_settle, aq_resus, ben_bury, ben_act_dep` per reach, but `pfas.dat` (soil/equilibrium params only) doesn't carry them and no reader populates `pfas_chadb`. Decide: extend `pfas.dat` with a channel block, add a new `pfas_cha.dat`, or hardcode defaults for the smoke test. The cleaner Path-1 alternative (route PFAS through `ch_rtpest` as a pesticide-type constituent) sidesteps this entirely — reconsider before committing to the dedicated `pfas_cha`.

**Q3 — `constituents.cs` is empty in the target model**, and the registration crosswalk (`constit_db_read` PFAS block from the map) was **not** implemented — `pfas_read` sets `npfas` directly from `pfas.dat`. So `npfas` is driven by `pfas.dat` presence, **not** by `constituents.cs`. Confirm which is authoritative; the map and Component 1 disagree. Recommendation: let `pfas_read` own `npfas` (already tested), skip the `constit_db_read` edit, drop the `constituents.cs` PFAS lines from the smoke set.

**Q4 — 16,755-HRU target is poorly suited to a smoke test.** Hand/scripted generation of a 16k-record `pfas_hru.ini` plus a full 366-day run is slow and noisy for a first byte-identity gate. **Strongly recommend running the smoke test on an S-tier model first** (a few HRUs), then promote to `041000130106` for scale. If `041000130106` is mandatory, script the `.ini` with all-sentinel HRUs + one seeded HRU.

**Q5 — `db_mx%pfasparm` / `input_file_module` slots are referenced by the map but unused by delivered code.** `pfas_read` hardcodes `"pfas.dat"`/`"pfas_hru.ini"` and does a no-op on `db_mx%pestparm`. The `input_file_module` and `maximum_data_module` edits in §1C are **optional** for function — only do them if you want the slot-based path. Don't let the map's diffs imply they're load-bearing.

**Q6 — Output writers are missing (`pfas_output.f90`).** Accumulators are populated but never written to a file. Mass-balance acceptance check #3 therefore needs **temporary instrumentation** (a debug write of `hpfasb_d`), or you implement the writer first. The byte-identity check #4 does not need it.

**Q7 — `enratio` threadprivacy (only matters once you go parallel).** `pfas_sed` reads global `enratio` as fallback. Serial smoke test is unaffected. For the OpenMP land phase, `enratio` must already be `threadprivate` (inherited from the pesticide path) — verify before enabling `-qopenmp`, do not add a new global.

**Q8 — Reader format coupling.** `pfas_read`'s `pfas_hru.ini` parser expects an exact record cadence (name line / num_pconta / d50 / per-PFAS quads) in strict HRU order. A malformed or short file silently truncates (EOF `exit`) leaving later HRUs at zero — no error raised. The SWATGenX emitter must match this cadence exactly; mismatches will look like "PFAS silently inactive," not a crash.
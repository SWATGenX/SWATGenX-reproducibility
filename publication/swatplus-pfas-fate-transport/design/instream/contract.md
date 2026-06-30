I now have everything I need. Note the key field shapes: `hpfasb_d(j)%surq/latq/perc/sed` are `dimension(:)` indexed by PFAS (not `%pfas(ipf)%surq` like pesticides — PFAS flips the indexing). The deferred draft references some names that don't exist (`pfasdb%sol` exists; `pfas_chadb`/`chpfas_d` exist in draft module; `ch_pfas_water`/`ch_pfas_benthic` are referenced via constituent_mass_module but the draft adds them there). Let me confirm the deferred draft's storage choice vs. the contract (contract says add `%pfas` to constituent_mass and store pools as `ch_pfas_water`).

The contract is explicit: add `%pfas` allocatable to the constituent_mass type, and pools dimensioned channel×npfas. The deferred draft stores pools in dedicated `ch_pfas_water`/`ch_pfas_benthic` arrays (referenced from constituent_mass_module) — these need to be added there. Let me verify cnv_kg and finalize. I have all I need to produce the brief.

# PFAS IN-STREAM TRANSPORT — IMPLEMENTATION BRIEF

Full in-stream PFAS fate-and-transport for modern free-form SWAT+, mirroring the SWAT+ pesticide channel model (`ch_rtpest.f90`) and the legacy `rtpfas.f`. Linear-Koc soluble/sorbed split + settle + resuspend + diffuse + bury + advective in/out. PFAS drops the three pesticide-only terms (no reaction `decay_a/decay_b`, no volatilization, no metabolite daughters), keeping everything else.

Files reviewed: `ch_rtpest.f90`, `ch_pesticide_module.f90`, `constituent_mass_module.f90`, `hydrograph_module.f90`, `sd_channel_control3.f90`, `rtpfas.f`, `hru_hyds.f90`, `pfas_module.f90`, `pfas_output_module.f90`, and the two deferred drafts. The deferred drafts are ~90% correct and mostly compilable; this brief fixes the integration gaps (the `%pfas` hydrograph slot, the `ch_pfas_water/benthic` declarations, the HRU index-order mismatch, and the missing allocation/output/command wiring).

---

## 1. DATA-STRUCTURE ADDITIONS

### 1a. `%pfas` slot on the constituent-mass hydrograph type

`hcs1/hcs2/hcs3`, `obcs%hin/%hd`, `ch_water/ch_benthic` are all `type (constituent_mass)`. Add a `pfas` vector alongside `pest/path/hmet/salt/cs`. This is the slot carried into/out of `pfas_cha` (mirrors `%pest`).

In `constituent_mass_module.f90`, edit `type constituent_mass` (currently lines 79–90):

```fortran
      ! constituent mass - soil, plant, aquifer, and channels
      type constituent_mass
        real, dimension (:), allocatable :: pest        !pesticide (kg/ha)
        real, dimension (:), allocatable :: path        !pathogen (cfu)
        real, dimension (:), allocatable :: hmet        !heavy metal (kg/ha)
        real, dimension (:), allocatable :: salt        !salt ion mass (kg/ha)
        real, dimension (:), allocatable :: salt_min    !salt mineral hydrographs
        real, dimension (:), allocatable :: saltc       !salt ion concentrations (mg/L)
        real, dimension (:), allocatable :: cs          !constituent mass (kg/ha)
        real, dimension (:), allocatable :: csc         !constituent concentration (mg/L)
        real, dimension (:), allocatable :: cs_sorb     !sorbed constituent mass (kg/ha)
        real, dimension (:), allocatable :: csc_sorb    !sorbed constituent concentration (mg/kg)
        real, dimension (:), allocatable :: pfas        !PFAS mass (kg) - sol+sorbed combined, repartitioned by frsol each day
      end type constituent_mass
```

The three operator helpers in this module (`hydcsout_add`, `hydcsout_mult_const`, `hydcsout_conc_mass`) build `constituent_mass` results by allocating each vector to its `cs_db%num_*` count. PFAS count lives in `pfas_module%npfas` (not in `cs_db`). To keep this module free of a `use pfas_module` cycle, **guard PFAS by allocation status** in each of the three functions — add after the existing `cs` block in all three:

```fortran
        if (allocated(hydcs1%pfas)) then
          allocate (hydcs3%pfas(size(hydcs1%pfas)), source = 0.)
          do ipf = 1, size(hydcs1%pfas)
            hydcs3%pfas(ipf) = hydcs2%pfas(ipf) + hydcs1%pfas(ipf)   ! _add
          end do
        end if
```
(declare `integer :: ipf = 0` in each; for `_mult_const` use `const * hydcs1%pfas(ipf)`; for `hydcsout_conc_mass` use `vol_m3 * hydcs1%pfas(ipf) / 1000.`). These operators run only in serial routing here, so the `size()` guard is race-free.

### 1b. Per-channel PFAS water + benthic pools

The contract wants pools dimensioned channel × npfas. Reuse `type (constituent_mass)` (it now has `%pfas`) so allocation/zeroing matches `ch_water/ch_benthic`. Add to `constituent_mass_module.f90` next to the channel storage block (after line 118):

```fortran
      ! storing water and benthic PFAS in channel (dimensioned by channel; %pfas by npfas)
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_water
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_benthic
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_water_init
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_benthic_init
```

These are the names the deferred `pfas_cha.f90` already `use`s from `constituent_mass_module`. Declaring them here satisfies that `use`.

### 1c. `pfas_cha_module` — transport params + daily output

The deferred `pfas_cha_module.f90` is **correct as-is** and should be shipped. Public surface:

```fortran
      !! per-PFAS in-stream routing parameters (extends pfasdb; from pfas-channel input)
      type pfas_cha_db
        character(len=16) :: name = ""    !          |PFAS compound name
        real :: koc       = 0.            !m^3/g     |linear water-sediment partition (Koc)
        real :: aq_settle = 0.            !m/day     |settling velocity of sorbed PFAS
        real :: aq_resus  = 0.            !m/day     |resuspension velocity of bed PFAS
        real :: ben_bury  = 0.            !m/day     |burial velocity in bed sediment
        real :: ben_act_dep = 0.          !m         |active bed-sediment layer depth
      end type pfas_cha_db
      type (pfas_cha_db), dimension(:), allocatable, save :: pfas_chadb   ! by PFAS (npfas)

      type pfas_cha_processes      ! daily reach PFAS balance (kg)
        real :: tot_in=0., sol_out=0., sor_out=0., settle=0., resus=0.,   &
                difus=0., bury=0., water=0., benthic=0.
      end type pfas_cha_processes
      type pfas_cha_output
        type (pfas_cha_processes), dimension(:), allocatable :: pfas
      end type pfas_cha_output
      type (pfas_cha_output), dimension(:), allocatable, save :: chpfas_d, chpfas_m, chpfas_y, chpfas_a
      type (pfas_cha_output) :: chpfas, chpfasz
```
Plus `frsol`/`frsrb` module reals, `chpfas_hdr`, and the `+ / //` operators — all present and mirroring `ch_pesticide_module` exactly. **One addition needed**: a separate per-channel active-bed parameters store is *not* required because `pfas_chadb` is by-PFAS while bed depth/bd vary by channel via `sd_ch(jrch)%ch_bd` (already used). Keep the active bed depth as a per-PFAS scalar `ben_act_dep` (matches `rtpfas.f` `sedpfas_act` and pesticide `ben_act_dep`).

### 1d. Initial-bed-concentration input (matches `rtpfas.f` `sedpfas_conc`/`chpfas_conc`)

Add an initializer type to `constituent_mass_module.f90` mirroring `cs_water_init_concentrations` (used by `pest_water_ini`):

```fortran
      !initial PFAS water-benthic concentrations for channels
      type pfas_water_init_concentrations
        character (len=16) :: name = ""               !! PFAS name
        real, dimension (:), allocatable :: water     !! mg/L (g/m3)  |initial water-column PFAS conc
        real, dimension (:), allocatable :: benthic   !! mg/kg or kg  |initial bed-sediment PFAS conc
      end type pfas_water_init_concentrations
      type (pfas_water_init_concentrations), dimension(:), allocatable :: pfas_water_ini
```

---

## 2. ALGORITHM SPEC — `pfas_cha`

The deferred `pfas_cha.f90` is **correct and ready to ship** with two fixes (noted below). Per-day, per-channel `jrch`, loop `ipf = 1..npfas`, `jpf = pfas_num(ipf)`:

| Step | Equation (mirrors `ch_rtpest` / `rtpfas.f`) |
|---|---|
| depth | `depth = rcurv%dep`; floor `0.01` m |
| inflow vol | `wtrin = ht1%flo + ch_stor(jrch)%flo` (m³) |
| PFAS in | `pfin = hcs1%pfas(ipf)` (kg, sol+sorbed combined) |
| reach mass | `chpfmass = pfin + ch_pfas_water(jrch)%pfas(ipf)` |
| bed mass | `sedpfmass = ch_pfas_benthic(jrch)%pfas(ipf)` |
| trace skip | if `chpfmass+sedpfmass < 1.e-12` → zero pools, `cycle` |
| **if `wtrin/86400 > 1.e-9`:** | |
| sed conc | `sedcon = ht1%sed / wtrin * 1.e6` (g/m³) |
| kd | `kd = pfas_chadb(jpf)%koc * sd_ch(jrch)%carbon / 100.` |
| soluble frac | `frsol = 1./(1.+kd*sedcon)` if `kd>0` else `1.`; `frsrb = 1.-frsol` |
| benthic partition | `por = 1. - sd_ch(jrch)%ch_bd/2.65`; `fd2 = 1./(por+kd)` |
| flow duration | `tday = rttime/24.`; cap `1.0` |
| settle | `settle = aq_settle*frsrb*chpfmass*tday/depth`; cap at `frsrb*chpfmass`; `chpfmass-=settle`; `sedpfmass+=settle` |
| resuspend | `resus = aq_resus*sedpfmass*tday/depth`; cap at `sedpfmass`; `sedpfmass-=resus`; `chpfmass+=resus` |
| diffuse | `difus = aq_mix*(fd2*sedpfmass - frsol*chpfmass)*tday/depth`; signed transfer water↔bed with cap on the donor pool |
| bury | `bury = ben_bury*sedpfmass/ben_act_dep`; cap at `sedpfmass`; `sedpfmass-=bury` |
| solubility cap | `solmax = pfasdb(jpf)%sol * wtrin`; if exceeded, shift excess soluble mass to bed |
| **else (negligible flow):** | `sedpfmass += chpfmass; chpfmass = 0.` |
| (no benthic reaction) | OMITTED — PFAS non-degradable |
| store water | if `wtrin>1.e-6`: `hcs1%pfas(ipf)=chpfmass` else `sedpfmass+=chpfmass; chpfmass=0.` |
| store bed | `ch_pfas_benthic(jrch)%pfas(ipf) = sedpfmass` |
| outflow split | `rto_out = min(1., ht2%flo/(1.e-6+ht2%flo+ch_stor(jrch)%flo))`; `hcs2%pfas(ipf)=rto_out*chpfmass`; `ch_pfas_water(jrch)%pfas(ipf)=(1.-rto_out)*chpfmass` |
| daily output | `tot_in=pfin`; `sol_out=frsol*hcs2%pfas`; `sor_out=frsrb*hcs2%pfas`; `water`/`benthic` from pools (settle/resus/difus/bury already stored in `chpfas_d` during the steps) |

**Two fixes to the deferred draft:**
1. The solubility call uses an internal `pfasdb_sol(idb)` `contains` function reading `pfasdb(idb)%sol`. That works, but cleaner to drop the contained function and `use pfas_module, only : pfasdb` directly: `solmax = pfasdb(jpf)%sol * wtrin`. (Draft's `pfasdb_sol(jpf)` already passes `jpf`, so behavior is identical — keep whichever; both compile.)
2. The draft writes `settle/resus/difus/bury` straight into `chpfas_d(jrch)%pfas(ipf)%...` as the working scalars. That is fine and matches the spec (those ARE the daily totals), but ensure `chpfas_d(jrch) = chpfasz` zeroing at the top **happens before** the `cycle` guard (draft does this correctly at line 86).

Also switch the fixed-form continuations (`&` in column 6, `1` style) — the draft has `&` continuations in column-6/`     &` legacy style; in free-form `.f90` use trailing `&` only. Reformat the `chpfas_d(jrch)%pfas(ipf)%settle = pfas_chadb(jpf)%aq_settle *  &` lines to free-form (drop the leading `     &` on the continued line).

---

## 3. INTEGRATION MAP

### 3a. `sd_channel_control3.f90` — three insertion points (mirror the `%pest` hooks)

**(i) module use** — add after line 18:
```fortran
      use pfas_cha_module
      use pfas_module, only : npfas
```

**(ii) call site** — right after the pesticide block (after line 172, the `obcs(icmd)%hd(1)%pest = hcs2%pest` line), insert the PFAS analogue. `hcs1` is already set to `obcs(icmd)%hin(1)` at line 155, so `hcs1%pfas` carries the inbound PFAS load:
```fortran
      !! route PFAS (linear-Koc in-stream: settle/resus/diffuse/bury)
      if (npfas > 0) then
        call pfas_cha
        obcs(icmd)%hd(1)%pfas = hcs2%pfas
      end if
```

**(iii) output mapping** — after the pesticide output loop (after line 460), add:
```fortran
      !! set PFAS channel output variables
      do ipf = 1, npfas
        chpfas_d(isdch)%pfas(ipf)%tot_in  = obcs(icmd)%hin(1)%pfas(ipf)
        chpfas_d(isdch)%pfas(ipf)%sol_out = frsol * obcs(icmd)%hd(1)%pfas(ipf)
        chpfas_d(isdch)%pfas(ipf)%sor_out = frsrb * obcs(icmd)%hd(1)%pfas(ipf)
        chpfas_d(isdch)%pfas(ipf)%settle  = chpfas%pfas(ipf)%settle
        chpfas_d(isdch)%pfas(ipf)%resus   = chpfas%pfas(ipf)%resus
        chpfas_d(isdch)%pfas(ipf)%difus   = chpfas%pfas(ipf)%difus
        chpfas_d(isdch)%pfas(ipf)%bury    = chpfas%pfas(ipf)%bury
        chpfas_d(isdch)%pfas(ipf)%water   = ch_pfas_water(ich)%pfas(ipf)
        chpfas_d(isdch)%pfas(ipf)%benthic = ch_pfas_benthic(ich)%pfas(ipf)
      end do
```
(declare `integer :: ipf = 0` in the subroutine. NOTE: since `pfas_cha` already populates `chpfas_d(jrch)` directly, this block is redundant with the routine and can be omitted — prefer letting `pfas_cha` own `chpfas_d` and dropping this loop, exactly as the draft does. Pesticides use the loop because `ch_rtpest` stages into module-global `chpst` not `chpst_d`. The PFAS routine stages straight into `chpfas_d`, so **omit this loop**.)

### 3b. HRU→channel coupling (`hru_hyds.f90`) — mirror the pesticide load path

The pesticide surface+sediment load enters `obcs(icmd)%hd(3)%pest` at line 92, lateral at `hd(4)`, perc at `hd(2)`, and `hd(1)` is summed at lines 172–175. Add the PFAS analogues. **Critical index-order difference**: PFAS HRU output is `hpfasb_d(j)%surq(ipf)` (vector indexed by PFAS), NOT `hpfasb_d(j)%pfas(ipf)%surq` like pesticides. Add `use pfas_module, only: npfas` and `use pfas_output_module, only: hpfasb_d`.

After the pesticide surface block (after line 93):
```fortran
      do ipf = 1, npfas       ! surface runoff + sediment-sorbed PFAS -> hd(3)
        obcs(icmd)%hd(3)%pfas(ipf) = (hpfasb_d(j)%surq(ipf) + hpfasb_d(j)%sed(ipf)) * cnv_kg
      end do
```
After the perc block (after line 109):
```fortran
      do ipf = 1, npfas       ! leached PFAS -> hd(2) (recharge)
        obcs(icmd)%hd(2)%pfas(ipf) = hpfasb_d(j)%perc(ipf) * cnv_kg
      end do
```
After the lateral block (after line 127):
```fortran
      do ipf = 1, npfas       ! lateral-flow PFAS -> hd(4)
        obcs(icmd)%hd(4)%pfas(ipf) = hpfasb_d(j)%latq(ipf) * cnv_kg
      end do
```
After the `hd(1)` pest sum (after line 175):
```fortran
      do ipf = 1, npfas       ! total inbound = surface + lateral (perc goes to recharge)
        obcs(icmd)%hd(1)%pfas(ipf) = obcs(icmd)%hd(3)%pfas(ipf) + obcs(icmd)%hd(4)%pfas(ipf)
      end do
```
(`cnv_kg = hru(j)%area_ha` converts kg/ha → kg, matching the salt/cs lines; `hpfasb_d` units are kg/ha per `pfas_output_module`. Declare `integer :: ipf = 0`.)

### 3c. Allocation / init site

PFAS hydrograph vectors and channel pools must be allocated wherever the pesticide equivalents are. The pesticide path allocates `%pest` inside the constituent-hydrograph allocator and `ch_water/ch_benthic` in the constituent-channel allocator (search `allocate (obcs(...)%hd(...)%pest` and `allocate (ch_water` in `cs_allocate*.f90` / `hyd_read_obj*` / the constituent setup). Add a parallel PFAS allocation guarded by `if (npfas > 0)`:

- For every place that allocates `obcs(i)%hin/%hd/%hin_sur/...(k)%pest(cs_db%num_pests)`, also allocate `...%pfas(npfas)`.
- Allocate `hcs1%pfas(npfas)`, `hcs2%pfas(npfas)`, `hcs3%pfas(npfas)`, `hin_csz%pfas(npfas)`.
- Allocate `ch_pfas_water(sp_ob%chandeg)`, `ch_pfas_benthic(...)` and each `%pfas(npfas)`, initialized from `pfas_water_ini` (water-column → `ch_pfas_water%pfas = conc*ch_stor%flo`; benthic → `ch_pfas_benthic%pfas = conc*bedvol`, `bedvol = chw*chl*ben_act_dep*1000`, matching `rtpfas.f` lines 99/124).
- Allocate `chpfas_d/m/y/a(nch)` and each `%pfas(npfas)`; set `chpfasz`, `chpfas` with `%pfas(npfas)`.
- Allocate `pfas_chadb(npfas)` and populate from the PFAS-channel input file (read alongside `pfas_read.f90`).

The cleanest home is a new `pfas_cha_allocate` (called from the same init point as the pesticide channel allocate, e.g. after `pfas_read`) plus the per-`obcs` `%pfas` allocation folded into the existing constituent allocator loop guarded by `npfas>0`.

### 3d. Command order

Within `sd_channel_control3`: `ch_rtmusk` (flow) → `ch_rtpest` → **`pfas_cha`** → `ch_rtpath` → salt/cs. PFAS slots immediately after pesticides since it shares the identical `hcs1→call→hcs2→obcs%hd` contract and depends on the same post-Muskingum `ht1/ht2/ch_stor/rcurv/rttime` state. No dependency on watqual/nutrient steps.

---

## 4. INTERFACE SUMMARY (for downstream agents)

**New / extended public names:**

| Name | Module | Shape | Meaning |
|---|---|---|---|
| `constituent_mass%pfas` | `constituent_mass_module` | `real(:)` by npfas | PFAS mass (kg), sol+sorbed combined; carried by `hcs1/hcs2/hcs3`, `obcs%hin(k)`, `obcs%hd(k)`, `hin_csz` |
| `ch_pfas_water(:)` | `constituent_mass_module` | `constituent_mass` by channel; `%pfas(npfas)` | reach water-column PFAS pool (kg) |
| `ch_pfas_benthic(:)` | `constituent_mass_module` | by channel; `%pfas(npfas)` | reach bed-sediment PFAS pool (kg) |
| `ch_pfas_water_init`, `ch_pfas_benthic_init` | `constituent_mass_module` | same | initial-condition copies |
| `pfas_water_ini(:)` | `constituent_mass_module` | by PFAS; `%water(:)`,`%benthic(:)` | initial reach conc input |
| `pfas_chadb(:)` | `pfas_cha_module` | `pfas_cha_db` by npfas | per-PFAS Koc, aq_settle, aq_resus, ben_bury, ben_act_dep |
| `chpfas_d/m/y/a(:)` | `pfas_cha_module` | `pfas_cha_output` by channel; `%pfas(npfas)` | daily/mon/yr/avg reach PFAS balance (kg) |
| `chpfas`, `chpfasz` | `pfas_cha_module` | scalar `pfas_cha_output` | working / zero accumulators |
| `frsol`, `frsrb` | `pfas_cha_module` | `real` | reach soluble/sorbed fractions (set by `pfas_cha`, read by output) |
| `pfas_cha` | (subroutine) | `call pfas_cha` | the in-stream routine; reads `hcs1%pfas`, writes `hcs2%pfas`, `ch_pfas_water/benthic`, `chpfas_d` |
| `chpfas_hdr` | `pfas_cha_module` | header type | output column headers |

**`pfas_cha` contract** (no args; uses module state):
- IN: `hcs1%pfas(ipf)` (kg inbound), `ht1%flo`, `ht1%sed`, `ht2%flo`, `ch_stor(jrch)%flo`, `rcurv%dep`, `rttime`, `sd_ch(jrch)%{carbon,ch_bd,aq_mix(ipf)}`, `pfas_chadb(jpf)%*`, `pfasdb(jpf)%sol`, `ch_pfas_water/benthic(jrch)%pfas(ipf)`.
- OUT: `hcs2%pfas(ipf)` (kg outflow), `ch_pfas_water/benthic(jrch)%pfas(ipf)` (updated pools), `chpfas_d(jrch)%pfas(ipf)%*` (daily kg balance), `frsol`/`frsrb`.

**Per-PFAS indexing convention (important):** PFAS HRU outputs use `hpfasb_d(j)%surq(ipf)` (vector-by-PFAS), the **inverse** of pesticide `hpestb_d(j)%pest(ipf)%surq`. The channel side `chpfas_d(jrch)%pfas(ipf)%settle` matches the pesticide convention (`output%pfas(ipf)%field`). Downstream output-writers must respect both orderings.

**Status of deferred drafts:** `pfas_cha_module.f90` — ship as-is. `pfas_cha.f90` — ship after (a) free-form continuation cleanup, (b) confirming `pfasdb%sol` solubility call, (c) the `chpfas_d(jrch)=chpfasz` zeroing precedes the trace-mass `cycle` (already correct). Both reference `ch_pfas_water/ch_pfas_benthic` from `constituent_mass_module` and `pfas_chadb/chpfas*` from `pfas_cha_module` — those declarations (§1a–1c) are the missing glue. Remaining un-drafted work is purely the **allocation/init wiring (§3c)** and the **HRU-load + command hooks (§3a–3b)**, all of which are mechanical mirrors of existing pesticide/salt code.
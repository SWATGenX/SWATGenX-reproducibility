I now have everything verified against the live source. One important discrepancy to flag: the deferred `pfas_cha.f90` line 215 writes `hcs1%pfas(ipf) = chpfmass` (staging back into the *inbound* hydrograph), which is then read nowhere downstream — but the contract brief said this line should be a no-op `chpfmass = chpfmass`. I'll note this in RISKS. I have what I need to produce the manifest.

# PFAS IN-STREAM TRANSPORT — BUILD MANIFEST

Verified against live source at `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine`. GLOB build confirmed (`CMakeLists.txt:159 file(GLOB sources src/*.f90)`), `main.f90` generated from `main.f90.in` (`CMakeLists.txt:140-148`). All field shapes, line numbers, and the pesticide templates below are confirmed present.

---

## 1. FILE MANIFEST

### NEW files to add (move from `deferred_instream/` into `src/`, after the diffs in §2 are applied to their dependencies)
| File | Status | Action |
|---|---|---|
| `src/pfas_cha_module.f90` | deferred draft = ship as-is | `git mv deferred_instream/pfas_cha_module.f90 src/` |
| `src/pfas_cha.f90` | deferred draft, **2 fixes** (free-form continuations + line-215 no-op) | fix then `mv` to `src/` |
| `src/pfas_cha_read.f90` | deferred draft (reader+allocator) = ship as-is; **needs call wired into main.f90.in** | `mv` to `src/` |
| `src/cha_pfas_output.f90` | **does not exist yet** — must be authored (full text in the REACH OUTPUT contract section) | write new |

### EXISTING files to MODIFY (exact diffs in §2)
| File | Change | Why |
|---|---|---|
| `src/constituent_mass_module.f90` | add `%pfas` to `type constituent_mass` (after line 89); add `ch_pfas_water/benthic[_init]` + `pfas_water_init_concentrations`/`pfas_water_ini` (after line 118); add PFAS guard block to the 3 operator helpers (`hydcsout_add` 603-634, `hydcsout_mult_const` 636-668, `hydcsout_conc_mass` 670-703) | the `%pfas` hydrograph slot + channel pools + init-conc input. Operators must propagate `%pfas` or routed-sum hydrograph adds silently drop PFAS |
| `src/sd_channel_control3.f90` | add `use pfas_cha_module` + `use pfas_module, only: npfas` (after line 21); add `call pfas_cha` + `obcs(icmd)%hd(1)%pfas = hcs2%pfas` after line 171 | the call site (command order = right after `ch_rtpest`) |
| `src/hru_hyds.f90` | add `use pfas_module, only: npfas` + `use pfas_output_module, only: hpfasb_d` (after line 17); `integer :: ipf=0` (after line 33); 4 load blocks after lines 92, 109, 127, 174 | %pfas-in-hydrograph allocation source: fills `obcs%hd(1..4)%pfas` from `hpfasb_d` (flipped indexing) |
| `src/main.f90.in` | add `pfas_cha_read` to `external` list (line 13/14); `call pfas_cha_read` after `call pfas_read` (line 75); add `cha_pfas_output` call inside command (already routed via `command.f90`) | wire reader/allocator into init sequence |
| `src/command.f90` | add `cha_pfas_output` to external list (line 34) + `use pfas_module, only: npfas`; `if (npfas>0) call cha_pfas_output(jrch)` after line 570 | reach-output dispatch |
| `src/header_pest.f90` | add `use pfas_module` + `use pfas_cha_module`; add `CHANNEL_PFAS` open block (units 7100-7107) guarded `sp_ob%chandeg>0 .and. npfas>0` | open the 8 output files + write headers |

---

## 2. EXACT DIFFS INTO SHARED FILES

### 2a. `constituent_mass_module.f90`

**(i) `%pfas` slot** — after line 89 (`csc_sorb`), before `end type constituent_mass` (line 90):
```fortran
        real, dimension (:), allocatable :: pfas        !PFAS mass (kg) - sol+sorbed combined, repartitioned each day by frsol
```

**(ii) channel pools + init-conc type** — after line 118 (`ch_benthic_init`):
```fortran
      ! storing water and benthic PFAS in channel (dimensioned by channel; %pfas by npfas)
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_water
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_benthic
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_water_init
      type (constituent_mass), dimension (:), allocatable :: ch_pfas_benthic_init

      !initial PFAS water-benthic concentrations for channels
      type pfas_water_init_concentrations
        character (len=16) :: name = ""
        real, dimension (:), allocatable :: water     !! ng/L  |initial water-column PFAS conc
        real, dimension (:), allocatable :: benthic   !! ng/g  |initial bed-sediment PFAS conc
      end type pfas_water_init_concentrations
      type (pfas_water_init_concentrations), dimension(:), allocatable :: pfas_water_ini
```

**(iii) operator propagation** — REQUIRED, not optional. `hcs3 = hcs1 + hcs2` and `const * hcs1` are used in the routing/recall path; if `%pfas` isn't carried, inflow summation zeroes PFAS. Add a `size()`-guarded block to each of the three functions (cannot use `cs_db%num_*`; PFAS count lives in `pfas_module`, and a `use pfas_module` here would risk a module cycle — guard by allocation status instead). Declare `integer :: ipf = 0` in each, and:

In `hydcsout_add` (after the `cs` loop, before `return` at line 632/633):
```fortran
        if (allocated(hydcs1%pfas)) then
          allocate (hydcs3%pfas(size(hydcs1%pfas)), source = 0.)
          do ipf = 1, size(hydcs1%pfas)
            hydcs3%pfas(ipf) = hydcs2%pfas(ipf) + hydcs1%pfas(ipf)
          end do
        end if
```
In `hydcsout_mult_const` (after `cs` loop, before line 667): same, with `hydcs2%pfas(ipf) = const * hydcs1%pfas(ipf)`.
In `hydcsout_conc_mass` (after `cs` loop, before line 702): same, with `hydcs2%pfas(ipf) = vol_m3 * hydcs1%pfas(ipf) / 1000.`.

> Note: the `+` operator (`hydcsout_add`) is invoked on `obcs(icmd)%hd(:) = hin_csz` style zeroing and inflow accumulation. The `allocated()` guard makes these safe before `pfas_cha_read` runs and harmless when `npfas==0`.

### 2b. `sd_channel_control3.f90`

Use-block (after line 21, `use maximum_data_module`):
```fortran
      use pfas_cha_module
      use pfas_module, only : npfas
```
Call site — after line 171 (`obcs(icmd)%hd(1)%pest = hcs2%pest`); `hcs1` is already `obcs(icmd)%hin(1)` from line 155:
```fortran
      !! route PFAS (linear-Koc in-stream: settle/resus/diffuse/bury)
      if (npfas > 0) then
        call pfas_cha
        obcs(icmd)%hd(1)%pfas = hcs2%pfas
      end if
```
**Do NOT add a separate output-mapping loop** like the pesticide block at lines 446-460. `pfas_cha` already populates `chpfas_d(jrch)` directly (unlike `ch_rtpest`, which stages into module-global `chpst` requiring the 446-460 copy). Adding the loop would double-write.

### 2c. `hru_hyds.f90`

Use-block (after line 17, `use output_ls_pesticide_module`):
```fortran
      use pfas_module, only : npfas
      use pfas_output_module, only : hpfasb_d
```
Counter (after line 33, `integer :: ics = 0`):
```fortran
      integer :: ipf = 0             !none          |counter for PFAS compounds
```
Surface (3) — after line 92 (pest loop body). **Flipped indexing: `hpfasb_d(j)%surq(ipf)`, NOT `%pest(ipf)%surq`:**
```fortran
      do ipf = 1, npfas
        obcs(icmd)%hd(3)%pfas(ipf) = (hpfasb_d(j)%surq(ipf) + hpfasb_d(j)%sed(ipf)) * cnv_kg
      end do
```
Recharge (2) — after line 109:
```fortran
      do ipf = 1, npfas
        obcs(icmd)%hd(2)%pfas(ipf) = hpfasb_d(j)%perc(ipf) * cnv_kg
      end do
```
Lateral (4) — after line 127:
```fortran
      do ipf = 1, npfas
        obcs(icmd)%hd(4)%pfas(ipf) = hpfasb_d(j)%latq(ipf) * cnv_kg
      end do
```
Total (1) — after line 174 (the pest `hd(1)` sum). `hpfasb_d` has **no tileq field**, so omit `hd(5)`:
```fortran
      do ipf = 1, npfas
        obcs(icmd)%hd(1)%pfas(ipf) = obcs(icmd)%hd(3)%pfas(ipf) + obcs(icmd)%hd(4)%pfas(ipf)
      end do
```
`cnv_kg = hru(j)%area_ha` (line 43) converts kg/ha→kg. `hpfasb_d%{surq,latq,perc,sed}` are kg/ha (confirmed `pfas_output_module.f90:25-28`). Recharge (`hd(2)`) intentionally NOT in the `hd(1)` channel total (matches pesticide; perc→aquifer).

### 2d. `main.f90.in`

External list — append to line 14:
```fortran
      external :: ..., pfas_read, pfas_output, pfas_cha_read
```
Call — after line 75 (`call pfas_read`), and after `proc_cha` (line 77, which runs `sd_channel_read`) so `sp_ob%chandeg`/`sd_ch`/`ch_stor` exist. The reader needs `obcs` allocated (from `hyd_connect`) AND channel geometry. Safest placement: immediately after `call proc_cha` (line 77):
```fortran
      call pfas_cha_read
```
> Verify ordering: `pfas_read`(75) → `proc_cha`(77, builds channels/obcs geometry) → `pfas_cha_read`. If `obcs` is allocated earlier in `hyd_connect` (line 12 external), this is satisfied. The reader is `allocated()`-guarded per-object, so it is safe regardless.

### 2e. `command.f90`

External list (line 34): add `cha_pfas_output`. Add `use pfas_module, only : npfas`. After line 570 (`call cha_pesticide_output (jrch)`):
```fortran
            if (npfas > 0) call cha_pfas_output (jrch)
```

### 2f. `header_pest.f90`

Add `use pfas_module, only : npfas` and `use pfas_cha_module` to the use-block (after line 11). After the CHANNEL_PESTICIDE ave-annual block (after line ~136), add the `CHANNEL_PFAS` block using units **7100-7103 (txt)** / **7104-7107 (csv)** (clear of pesticide 2808-2815, salt/cs 28xx), guarded `if (sp_ob%chandeg > 0 .and. npfas > 0)`, header = `chpfas_hdr`, registering each file into unit 9000 as `CHANNEL_PFAS`. Pattern is a verbatim mirror of lines 80-137.

---

## 3. COMPILE-ORDER NOTES

- **GLOB is automatic**: `file(GLOB sources src/*.f90)` (CMakeLists.txt:159) picks up `src/pfas_cha*.f90` and `src/cha_pfas_output.f90` with **zero CMakeLists edits** — but GLOB is evaluated at configure time, so a **fresh `cmake -B build` (re-configure) is required** after `mv`-ing new files in; an incremental `make` alone will not see them.
- **Module dependency DAG** (ifx resolves order from `use` automatically; listed for review):
  - `pfas_module` (exists) ← independent
  - `pfas_output_module` (exists) ← independent
  - `constituent_mass_module` (edited) ← independent of PFAS modules (uses `allocated()` guard, no `use pfas_module` — this avoids a cycle since `pfas_cha.f90` does `use constituent_mass_module, only: ch_pfas_water/benthic`).
  - `pfas_cha_module` (new) ← independent (only `implicit none` + own types).
  - `pfas_cha.f90` (new) ← `use`s `pfas_cha_module`, `pfas_module`, `constituent_mass_module`, `channel_module`, `sd_channel_module`, `hydrograph_module`. All pre-exist. `rcurv` in `sd_channel_module`, `rttime` in `channel_module` — both confirmed.
  - `pfas_cha_read.f90` (new) ← `pfas_module`, `pfas_cha_module`, `constituent_mass_module`, `hydrograph_module`, `sd_channel_module`.
  - `cha_pfas_output.f90` (new) ← `pfas_cha_module`, `pfas_module`, `time_module`, `basin_module`, `hydrograph_module`.
- **No new circular dependency** introduced: the only back-edge would be `constituent_mass_module → pfas_module`, which the `allocated()`/`size()` guard deliberately avoids.
- **Build command** (per MEMORY ifx+NetCDF recipe): pin `-DCMAKE_Fortran_COMPILER=ifx` and `PKG_CONFIG_PATH=deps/netcdf-ifx/lib/pkgconfig`; do NOT cp+reconfigure an existing build dir.

---

## 4. SMOKE-TEST PLAN (Rogue model)

1. **Build serial debug first** (catches the index-flip + allocation bugs that `-O` hides): `cmake -B build_dbg -DCMAKE_BUILD_TYPE=Debug -DCMAKE_Fortran_COMPILER=ifx` (debug flags include `-check bounds`, CMakeLists.txt:53). Confirm clean compile of all 4 new files + 6 edited.
2. **Run on Rogue with existing land-phase PFAS inputs** (the model already exercises `pfas_read`/`pfas_lch`/`pfas_sed` → `hpfasb_d`). Two cases:
   - **(a) no `pfas_cha.dat`**: confirms `pfas_cha_read` defaults path (PFOS-like Koc, clean reach) and that HRU loads still route. Model must complete a full serial run with no segfault.
   - **(b) with `pfas_cha.dat`** + nonzero initial reach/benthic conc: exercises the init-from-concentration path and bed pools.
3. **Confirm reach PFOS concentrations appear**: `channel_pfas_day.txt` exists, has the 20-column header, and `tot_conc_ngL` (col 20) is nonzero on channels downstream of PFAS HRUs. Cross-reference the channels carrying the **31 EGLE PFOS stations** (snap each station to its `jrch`; the calibration matcher uses the same `channel_sd_day` → `jrch` join).
4. **In-stream mass balance** — the conservation check (no reaction/volat/decay for PFAS, so it must close exactly):
   - Per channel-day: `tot_in + resus_in + difus_in == sol_out + sor_out + settle + bury + Δwater + Δbenthic`.
   - **Soluble + sorbed + benthic conserved**: sum `water + benthic` pools + cumulative `sol_out+sor_out+bury` across all reaches against cumulative HRU input. Burial is the only permanent sink; everything else must balance to FP tolerance.
5. **Serial-only**: run single-thread (`OMP_NUM_THREADS=1` / non-OpenMP binary). `pfas_cha` is serial-channel-phase and writes shared `ch_pfas_water/benthic` + `chpfas_d` — do not test under the parallel engine yet.

---

## 5. RISKS FOR THE INTEGRATION PASS

1. **`pfas_cha.f90` line 215 — `hcs1%pfas(ipf) = chpfmass`**: the deferred draft writes the post-process water mass back into the **inbound** hydrograph `hcs1`. Nothing reads `hcs1%pfas` after `pfas_cha` returns (the outflow is `hcs2%pfas`, set at line 225 from `chpfmass`), so this is currently a harmless dead write — BUT it mutates `hcs1`, and if any later refactor reuses `hcs1` post-call it will read corrupted PFAS. The contract brief explicitly calls for this to be a no-op (`chpfmass = chpfmass`). **Recommend: change line 215 to `chpfmass = chpfmass` (or delete the `if (wtrin>1.e-6)` staging block)** to match the contract and avoid the latent aliasing bug.

2. **`%pfas`-in-hydrograph allocation lifecycle** — the highest-risk area. `hru_hyds` and `sd_channel_control3` reference `obcs(icmd)%hd(k)%pfas(ipf)` and `hcs1/hcs2%pfas(ipf)` with **no `allocated()` guard**. Every one of these vectors MUST be allocated by `pfas_cha_read` before the first time step, OR the run segfaults on the first `%pfas(ipf)`. Specifically verify the reader allocates: `hcs1/hcs2/hcs3%pfas`, `hin_csz%pfas`, AND every `obcs(iob)%{hin,hin_sur,hin_lat,hin_til,hin_aqu,hd}(:)%pfas` under the `obcs_alloc(iob)==1` guard. The daily zeroing `obcs(icmd)%hd(:) = hin_csz` (control3 line 67) relies on `hin_csz%pfas` being allocated — if it isn't, the operator-`=` (intrinsic, component-wise) on an unallocated `%pfas` is a no-op and the `hd%pfas` stays stale/garbage. **Confirm `hin_csz%pfas(npfas)` is allocated and zeroed.**

3. **`obcs` existence gate** — `obcs`/`obcs_alloc` are only allocated when `cs_db%num_tot > 0` (per the deferred reader's own integration note). A Rogue model with **only** PFAS and zero pesticides/salts/cs would have `obcs` unallocated → the HRU load path `obcs(icmd)%hd(3)%pfas` segfaults. Verify the Rogue model has `cs_db%num_tot>0`, OR bump `num_tot` when `npfas>0` (contract §3c). The `allocated()` guards in the reader prevent a crash *in the reader*, but the **load path in hru_hyds has no such guard**.

4. **Operator `%pfas` propagation (§2a iii) is load-bearing, not cosmetic** — if skipped, `hcs3 = hcs1 + hcs2` inflow summation and any `const *` scaling silently drop PFAS mass (mass-balance test #4 fails). The `allocated()` guard is mandatory because these operators run before `pfas_cha_read` (e.g. on zero-hydrograph init) and when `npfas==0`.

5. **`sd_ch(jrch)%aq_mix(ipf)` indexing** — `pfas_cha` line 168 reads `sd_ch(jrch)%aq_mix(ipf)`. Confirm `aq_mix` is allocated to at least `npfas` (it is sized for pesticides). If `aq_mix` is pesticide-dimensioned and `npfas > num_pests`, this is an out-of-bounds read. **Verify `sd_ch%aq_mix` allocation covers `npfas`**, or add a PFAS-specific mix array.

6. **Output unit collision** — units 7100-7107 are assumed free. Grep the tree for `7100`-`7107` before wiring `header_pest.f90` to confirm no other writer claims them.

7. **`cha_pfas_output.f90` field-order coupling** — the `100 format` writes `chpfas_d(j)%pfas(ipf)` as a whole derived type; Fortran emits components in declaration order. If the 3 `conc_*` fields are added to `pfas_cha_processes` anywhere but **last**, columns silently misalign against the header. Keep `conc_sol/conc_sor/conc_tot` as the final 3 fields, and extend all 3 operator functions in `pfas_cha_module` to carry them (else monthly/annual averaging drops concentration).

8. **`pfas_qout%vol` allocation** — the concentration writer needs `pfas_qout%vol(sp_ob%chandeg)` allocated in `pfas_cha_read` and the one-line `pfas_qout%vol(jrch) = ...` added to `pfas_cha`. Easy to forget; without it the writer reads an unallocated array.
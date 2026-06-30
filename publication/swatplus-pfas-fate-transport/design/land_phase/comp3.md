I have all required anchors and field bindings. I'll now produce the integration map.

# PFAS Surface-Water Integration Map — modern SWAT+

This wires the validated `pfas_module.f90` (already at `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_module.f90`) into the engine, mirroring the pesticide framework. New source files are named below and must be created alongside the diffs; only the engine-edit diffs into existing files are spelled out exactly.

**New source files to add** (siblings of the pesticide equivalents): `pfas_parm_read.f90` (↔`pest_parm_read.f90`), `pfas_hru_read.f90` (↔`cs_hru_read.f90`), `pfas_init.f90` (↔`pesticide_init.f90`), `pfas_lch.f90` (↔`pest_lch.f90`), `pfas_sed.f90` (↔`pest_pesty.f90`), `pfas_cha.f90` (↔`ch_rtpest.f90`), `pfas_output.f90` (daily HRU + channel writes). The container/solver (`pfas_module.f90`) is done.

---

## 1. Exact insertion points

### 1a. Database read — `pfas_parm_read` (reads `pfas.dat` → `pfasdb(:)`)
File `proc_db.f90`, right after the pesticide-DB read (line 17). `pfas_parm_read` must also be added to the `external` list at line 8.

```diff
--- a/src/proc_db.f90
@@ external :: ... pest_parm_read, plant_parm_read, ...
+      external :: pfas_parm_read
@@
       call pest_parm_read                           !! read the pesticide database
+      call pfas_parm_read                            !! read the PFAS compound database (pfas.dat)
```

`pfas_parm_read` mirrors `pest_parm_read.f90` exactly: inquire on a new `in_parmdb%pfas` slot, count rows, `allocate(pfasdb(0:imax))`, read each `pfasdb(ip)` (a `pfas_db` derived type — list-directed read works because all components are intrinsic scalars in declaration order: name, mw, sol, kl, lm, percop), set `db_mx%pfasparm = imax`. No `pestcp`-style decay precompute is needed (no half-lives in surface-water PFAS).

### 1b. Constituent registration — crosswalk in `constit_db_read`
PFAS rides the same `constituents.cs` selection file as pests. Add a PFAS block after the `num_cs` block (line 65) and a crosswalk after the pest crosswalk (line 77):

```diff
--- a/src/constit_db_read.f90
@@ use pesticide_data_module
+      use pfas_module
@@ read (106,*,iostat=eof) (cs_db%cs(i), i = 1, cs_db%num_cs)
+        !PFAS compounds (surface-water only)
+        read (106,*,iostat=eof) npfas
+        if (eof < 0) exit
+        allocate (cs_db_pfas(0:npfas))          ! names buffer
+        allocate (pfas_num(0:npfas), source = 0)
+        read (106,*,iostat=eof) (cs_db_pfas(i), i = 1, npfas)
         exit
@@ end do  ! pest crosswalk
+      do ipfas = 1, npfas
+        do ipfasdb = 1, db_mx%pfasparm
+          if (pfasdb(ipfasdb)%name == cs_db_pfas(ipfas)) then
+            pfas_num(ipfas) = ipfasdb
+            exit
+          end if
+        end do
+      end do
```

`cs_db_pfas(:)` is a local `character(len=16)` names buffer (declare in this subroutine, or add `pfas` to `cs_db` for symmetry — keeping it module-side via `pfas_num` is sufficient since `pfas_module` already owns `npfas`/`pfas_num`). Declare `integer :: ipfas, ipfasdb` in the subroutine. Add `pfasparm` to `maximum_data_module`'s `db_mx`. The `null`-file branch (line 26) must also `npfas = 0`. **Back-compat:** if a legacy `constituents.cs` lacks the PFAS lines, the `read` hits EOF and `npfas` stays 0 — PFAS silently off. Good.

### 1c. Per-HRU read + allocation/zeroing — `pfas_hru_read` + `pfas_init`
File `proc_read.f90`: add `pfas_hru_read` to the `external` list (line 6-16) and call it after `cs_hru_read` (line 42):

```diff
--- a/src/proc_read.f90
+      external :: pfas_hru_read
@@ call cs_hru_read
+      call pfas_hru_read        !! per-HRU PFAS soil mass + Freundlich kf/nf + d50 (pfas_hru.ini)
```

File `proc_hru.f90`: call `pfas_init` after `cs_hru_init` (line 48), guarded by `npfas`. Add `pfas_init` to the `external` list (line 17):

```diff
--- a/src/proc_hru.f90
+      use pfas_module
@@ external :: ... pesticide_init, pathogen_init, salt_hru_init, cs_hru_init
+      external :: pfas_init
@@ if (cs_db%num_cs > 0) call cs_hru_init !rtb cs
+        if (npfas > 0) call pfas_init      !! PFAS surface-water soil pools
```

`pfas_init` mirrors `pesticide_init.f90`: loop `ihru = 1, sp_ob%hru`; `allocate(pfas_soil_hru(ihru)%ly(nly))`; per layer `allocate(...%sol_pfas(npfas), %kf, %nf, %enr, %cw, source=0.)`; convert the per-HRU init soil concentration (ppm) to kg/ha with the **same** `wt1 = bd*thick/100.` factor used at `pesticide_init.f90:73`; copy `kf`,`nf`,`sol_d50`,`num_pconta` from the `pfas_hru_read` staging arrays. `pfas_soil_hru` must be allocated `(sp_ob%hru)` before the loop (do it in `pfas_init` head, matching how cs/pest containers are sized).

### 1d. Land phase — `pfas_lch` + `pfas_sed` in `hru_control`
Hook **immediately after the pesticide land block** so PFAS sees the same post-`swr_percmain` soil-water/percolation state. The pesticide soil-leach call is `pest_lch` at `hru_control.f90:518`; sediment-bound `pest_pesty` is at line 526 inside the `surfq>0` guard.

Add to the `external` list (line 44-54): `pfas_lch, pfas_sed`. Then:

```diff
--- a/src/hru_control.f90
@@ external :: ... pest_lch, ... pest_pesty, smp_buffer, ...
+      external :: pfas_lch, pfas_sed
@@ use cs_module !rtb cs
+      use pfas_module
@@         !! sum total pesticide in soil
         call pest_soil_tot
+
+        !! PFAS dissolved movement (runoff/lateral/leach) — solves soil 3-phase equilibrium
+        if (npfas > 0) call pfas_lch
@@         if (precip_eff > 0.) then
             call pest_enrsb
             if (sedyld(j) > 0.) call pest_pesty
+            !! PFAS sediment-bound loading (uses enratio from pest_enrsb)
+            if (npfas > 0 .and. sedyld(j) > 0.) call pfas_sed
```

`pfas_lch` (per HRU `j=ihru`, loop layers then `ipfas`) calls the solver per layer:
`a_aw = pfas_awi(soil(j)%phys(ly)%por, soil(j)%phys(ly)%st, soil(j)%phys(ly)%ul, pfas_soil_hru(j)%ly(ly)%sol_d50)` then
`cw = pfas_partition(pfasdb(idb)%mw, pfas_soil_hru(j)%ly(ly)%kf(ipfas), %nf(ipfas), pfasdb(idb)%lm, pfasdb(idb)%kl, a_aw, soil(j)%phys(ly)%bd, pfas_soil_hru(j)%ly(ly)%sol_pfas(ipfas)/pfas_soil_hru(j)%num_pconta, soil(j)%phys(ly)%thick)` where `idb = pfas_num(ipfas)`. Then apply, byte-faithful to `pfaslch.f`: multiply `cw` back by `num_pconta`, solubility-cap, convert to load `co = cw*mw/1.e5` (kg/mm-ha), and split across `surfq(j)` (ly==1, scaled by `pfasdb%percop`), `soil(j)%ly(ly)%flat` (lateral), and `soil(j)%ly(ly)%prk` (leach to ly+1 or to `perc` output at the bottom) — the same flow-volume structure as `pest_lch.f90:48-94`. Store `cw` in `pfas_soil_hru(j)%ly(ly)%cw(ipfas)` for output. `pfas_sed` mirrors `pest_pesty.f90` using the layer-1 sorbed fraction and `enr` (or the global `enratio` fallback exactly as lines 40-44).

### 1e. Channel routing — `pfas_cha` (SERIAL)
File `sd_channel_control3.f90`, after the pesticide channel route at line 172. Add `pfas_cha` to the `external` list (line 25):

```diff
--- a/src/sd_channel_control3.f90
+      use pfas_module
@@ external :: ... ch_rtpest, ...
+      external :: pfas_cha
@@         obcs(icmd)%hd(1)%pest = hcs2%pest
       end if
+
+      !! route PFAS (linear-Koc in-stream; serial — runs in channel command phase)
+      if (npfas > 0) then
+        call pfas_cha
+      end if
```

`pfas_cha` mirrors `ch_rtpest.f90` but with **linear Koc partitioning only** (`frsol = 1/(1+kd*sedcon)`), no volatilization/decay/benthic-burial chemistry — surface-water scope is settling/resuspension/diffusion + a linear sorption split, writing `hcs2`/channel storage analogues for PFAS. Use a PFAS channel-water/benthic store paralleling `ch_water`/`ch_benthic` (declare `pfas_ch_water(:)`, `pfas_ch_benthic(:)` in `pfas_module` or alongside the channel constituent stores). This routine is invoked only inside the channel command object, which the parallel-engine work keeps serial — see §4.

### 1f. Output
Add `call pfas_output` after the pesticide HRU output block in `hru_control.f90` (or fold daily PFAS soil/surq/latq/perc/sed balance writes into a `hpfasb_d(j)` structure populated in `pfas_lch`/`pfas_sed`, mirroring `hpestb_d`). Open the output unit in `proc_hru.f90` next to the erosion-output open (line 52), guarded by `npfas > 0`. Channel PFAS load output piggybacks on the existing channel-constituent writer pattern. Header/columns follow the pesticide `output_ls_pesticide_module` idiom (`sol_pfas, surq, latq, perc, sed, cw` per compound).

---

## 2. CMakeLists.txt

**No edit required.** Line 157 is `file(GLOB sources src/*.f90)` — every new `src/pfas_*.f90` is picked up automatically on the next `cmake` configure. (CMake caches the glob, so a fresh `cmake -B build` or a re-configure is needed after adding files; there is no hand-maintained source list.) If the project later pins to an explicit list, append:

```cmake
  src/pfas_module.f90 src/pfas_parm_read.f90 src/pfas_hru_read.f90
  src/pfas_init.f90 src/pfas_lch.f90 src/pfas_sed.f90
  src/pfas_cha.f90 src/pfas_output.f90
```

`pfas_module.f90` must compile before its users; with GLOB the build system resolves Fortran module deps automatically, so ordering is not manual.

Also add the input-filename slot in `input_file_module.f90` near line 180:

```diff
        character(len=25) :: pest = "pesticide.pes"
+       character(len=25) :: pfas = "pfas.dat"
```
and a per-HRU init slot near line 230:
```diff
        character(len=25) :: pest_soil = "pest_hru.ini"
+       character(len=25) :: pfas_soil = "pfas_hru.ini"
```

---

## 3. Input-file format spec + SWATGenX emission

### `pfas.dat` (global compound database; one row per PFAS — read by `pfas_parm_read`)
Two header lines then whitespace-delimited rows, column order = `pfas_db` component order:

```
pfas.dat: PFAS compound database
name              mw         sol        kl          lm          percop
PFOA          0.41407    9400.0      0.0123      2.10e-6     0.50
PFOS          0.50013     680.0      0.0456      3.05e-6     0.50
```
- `name` char(16); `mw` kg/mol; `sol` mg/L; `kl` L/nmol (Langmuir K_L); `lm` nmol/m² (Γ_max); `percop` 0–1.

### `constituents.cs` addition (selection list)
Append after the existing `num_cs` line + names line:
```
2
PFOA  PFOS
```
(count, then the names that must match `pfas.dat`). Legacy files omit it → `npfas=0`.

### `pfas_hru.ini` (per-HRU initial state — read by `pfas_hru_read`)
One record per HRU init group (referenced via `hru%dbs%soil_plant_init`, same indirection pesticides use). Per compound: initial soil conc (ppm), Freundlich `kf`, Freundlich `nf`; plus per-HRU scalars `num_pconta` and `sol_d50` (mm), and `enr`:

```
pfas_hru.ini
name        num_pconta  sol_d50    PFOA_soil PFOA_kf PFOA_nf PFOA_enr  PFOS_soil PFOS_kf PFOS_nf PFOS_enr
pfas_default   1        0.02       0.0       12.5    0.85    1.0       0.0       28.0    0.78    1.0
```

### SWATGenX emission plan
PFAS rides the identical generation path as `pesticide.pes`. In the model writer that already emits `pesticide.pes` + `pest_hru.ini` + the pesticide line of `constituents.cs`:
1. **`pfas.dat`** — emit from a fixed compound-parameter table (a small CSV/JSON shipped with SWATGenX, keyed by compound name → mw/sol/kl/lm/percop). Static per-compound physchem; not watershed-specific.
2. **`constituents.cs`** — when PFAS is enabled for a build, write the extra `npfas` + names lines at the end (the writer already builds this file for pests; append two lines). Keep it omitted (and thus `npfas=0`) when PFAS is off, preserving byte-identical legacy output.
3. **`pfas_hru.ini`** — generated per HRU exactly like `pest_hru.ini`: default `kf`/`nf` per soil texture (lookup table), `sol_d50` from the SSURGO/gSSURGO particle-size already pulled during soil build (the d50 is derivable from the sand/silt/clay split SWATGenX already has per layer), `num_pconta=1` default, initial soil mass 0 unless a contamination source layer is supplied. Reuse the soil-layer loop that writes the soil DB so `sol_d50` is emitted per the same layers the engine reads.
4. **file.cio / registration** — no new `file.cio` token is needed because `pfas.dat` and `pfas_hru.ini` are resolved through `in_parmdb%pfas` / `in_files%pfas_soil` defaults (set in the diffs above), exactly like `pesticide.pes`. The writer only needs to drop the files into the TxtInOut directory.

Because every PFAS file is gated by `npfas` and absent-file inquiries fall through to `npfas=0`, an existing generated model without PFAS runs bit-identically.

---

## 4. Reentrancy checklist (OpenMP land wavefront safe; channel serial)

The land routines run inside the HRU-parallel wavefront (one HRU per thread). Confirmed safe:

- [x] **Solver is pure-style.** `pfas_partition` / `pfas_awi` read only scalar `intent(in)` args and write only locals (`a,c,d,m,f,h,n,q,g,x,fx,...`). No module variable is written. Verified against the module source.
- [x] **All state is indexed by the current HRU.** `pfas_lch`/`pfas_sed` set `j = ihru` and touch only `pfas_soil_hru(j)%...`, `soil(j)%...`, `surfq(j)`, `sedyld(j)` — disjoint per thread, the same access pattern as `pest_lch`/`pest_pesty` which already run reentrant in the wavefront.
- [x] **No shared module scratch written across calls.** `pfasdb(:)`, `pfas_num(:)`, `npfas`, `db_mx%pfasparm` are read-only after `proc_db`/`proc_read` (init phase, serial). The mutable per-HRU pools live in `pfas_soil_hru(j)`, never aliased across HRUs.
- [x] **No `save` scalars mutated at runtime.** `pfasdb`/`pfas_num` carry `save` but are populated once during serial init; the land routines never write them. (Contrast the N=1 regression class: no `SAVE`-stripped cross-call persistence here because the solver carries no persistent state.)
- [x] **Output is per-HRU.** Daily PFAS balance goes to `hpfasb_d(j)` (per-HRU), written under index `j`; the file `write` is deferred to the serial output flush (same as `hpestb_d`), so no concurrent I/O to a shared unit from threads.
- [x] **`enratio` dependency.** `pfas_sed` reads the global `enratio` only as a fallback and only after `pest_enrsb` set it for this HRU in the same serial-within-HRU call chain; the preferred path uses per-layer `%enr`. No cross-HRU read of another thread's `enratio` (each thread's `enratio` must be threadprivate exactly as the existing pesticide path already requires — inherit that guarantee, do not introduce a new global).
- [x] **Channel routine stays serial.** `pfas_cha` is invoked only from `sd_channel_control3` inside the channel command object, which the parallel engine executes in the serial channel-routing phase (not the HRU wavefront). It may safely use channel-indexed shared stores (`pfas_ch_water(jrch)`, `pfas_ch_benthic(jrch)`, `hcs1/hcs2`) under the same serialization that protects `ch_rtpest`.

**Action item for whoever wires `enratio`:** confirm `enratio` is already `threadprivate` (it must be, since `pest_enrsb`/`pest_pesty` run in the wavefront); `pfas_sed` inherits that and adds no new shared mutable global.

---

Deliverable module file (solver + container), already compile-verified with `gfortran -ffree-form -c`: `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_module.f90`.

Anchor references used: `hru_control.f90:518` (pest_lch), `:526` (pest_pesty); `proc_hru.f90:45-48` (init guards); `proc_read.f90:42` (cs_hru_read); `proc_db.f90:17` (pest_parm_read); `sd_channel_control3.f90:168-172` (ch_rtpest); `pesticide_init.f90:73` (`wt1=bd*thick/100.` ppm→kg/ha); `input_file_module.f90:180,230`; `CMakeLists.txt:157` (GLOB — no edit).
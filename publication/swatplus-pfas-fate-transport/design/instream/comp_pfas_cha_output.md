I have everything I need. There's no `pco%pfas` print flag yet — I'll add one to the output module spec and gate on it, mirroring `pco%pest`. The concentration target is what calibrates against EGLE PFOS stations: `conc = mass_out / flow_out`. PFAS in water at ng/L, so kg/m³ × 1e12 = ng/L (1 kg = 1e9 µg... let me get this exactly: 1 kg/m³ = 1e6 mg / 1000 L = 1000 mg/L = 1e6 µg/L = 1e9 ng/L). So `ng/L = kg_per_m3 * 1e9`.

Now I'll write the deliverable: the reach PFAS output writer with concentration, plus the output-module accumulator additions and the column spec.

The pesticide `cha_pesticide_output` only writes a single mass column. For PFAS calibration against EGLE we need the **concentration** (load/flow) plus the flux columns. I'll extend the writer to emit the full balance from `chpfas_d` and compute soluble/sorbed/total concentration in ng/L from outflow mass and outflow volume.

Here is the deliverable.

---

# REACH PFAS OUTPUT — `cha_pfas_output.f90` + module/header additions + column spec

## 1. Output-module additions (append to `pfas_cha_module.f90`)

The contract's `pfas_cha_module` carries the mass-balance accumulators (`chpfas_d/m/y/a`, `chpfas_hdr`, the `+ / // /` operators) — those ship as-is. The writer additionally needs (a) **concentration** fields on the daily record (mass alone doesn't calibrate against EGLE — they report ng/L), and (b) a **print flag** since `basin_module` has no `pco%pfas`. Add the following to `pfas_cha_module` (a self-contained `pfas_outflow` carrier for the per-step outflow volume, the three concentration fields appended to `pfas_cha_processes`, and a header) — these are additive and don't disturb the operator functions if you extend each operator with the three new fields:

```fortran
      !! ---- ADD these three fields to type pfas_cha_processes (after %benthic) ----
      !! (and extend chpfas_add / chpfas_div / chpfas_ave with them, same idiom)
      !   real :: conc_sol = 0.   !ng/L |soluble PFAS concentration in reach outflow
      !   real :: conc_sor = 0.   !ng/L |sorbed  PFAS concentration in reach outflow
      !   real :: conc_tot = 0.   !ng/L |total   PFAS concentration in reach outflow

      !! per-reach outflow water volume (m3) for the day, set by pfas_cha so the
      !! writer can form concentration = mass_out / volume_out without re-reading
      !! the hydrograph (which the channel command has already advanced).
      type pfas_outflow_vol
        real, dimension(:), allocatable :: vol   !m3 |reach outflow volume, by channel
      end type pfas_outflow_vol
      type (pfas_outflow_vol), save :: pfas_qout

      !! print flag (basin_module has no pco%pfas); read alongside other pco codes
      type pfas_print_codes
        character(len=1) :: d = "n"
        character(len=1) :: m = "n"
        character(len=1) :: y = "n"
        character(len=1) :: a = "n"
      end type pfas_print_codes
      type (pfas_print_codes), save :: pco_pfas
```

**Two-line change in `pfas_cha`** (the routine from the prior brief): after computing `rto_out` and `hcs2%pfas(ipf)`, record the outflow volume once per channel:

```fortran
        pfas_qout%vol(jrch) = rto_out * (ht2%flo + ch_stor(jrch)%flo)   ! m3 actually leaving
```
(allocate `pfas_qout%vol(sp_ob%chandeg)` next to `chpfas_d` in `pfas_cha_allocate`.)

Extend the three operator functions and the `pfas_cha_processes` type with `conc_sol/conc_sor/conc_tot` so monthly/annual averaging carries concentration too (averaged by `//` like the mass terms — a flow-weighted average is more correct but the pesticide template uses simple period averaging, so we match it for consistency; the **daily** file is the calibration target and is exact).

## 2. The writer — `cha_pfas_output.f90`

Mirrors `cha_pesticide_output.f90` exactly (same `m += d`, end-of-month/year roll-up, `// const` averaging, `pco%csvout` branch, `ch_pfasbz` zeroing). Differences: loops `npfas` (not `cs_db%num_pests`), names from `pfasdb`, writes the **full balance + 3 concentrations**, computes concentration from `chpfas_d` outflow mass and `pfas_qout%vol`.

```fortran
      subroutine cha_pfas_output (jrch)

!!    ~ ~ ~ PURPOSE ~ ~ ~
!!    Per-channel in-stream PFAS output (daily / monthly / yearly / ave-annual).
!!    Mirrors cha_pesticide_output.f90.  Writes the full reach PFAS balance
!!    (kg: tot_in, sol_out, sor_out, settle, resus, diffuse, bury, water,
!!    benthic) PLUS soluble / sorbed / total outflow CONCENTRATION in ng/L.
!!    The concentration (load / flow) at each channel is the quantity
!!    calibrated against the EGLE PFOS monitoring stations.
!!
!!    Units: pools/fluxes in kg; concentration = mass_out[kg] / vol_out[m3]
!!           * 1.e9  ->  ng/L   (1 kg/m3 = 1.e9 ng/L).

      use pfas_cha_module
      use pfas_module, only : npfas, pfas_num, pfasdb
      use time_module
      use basin_module
      use hydrograph_module, only : sp_ob1, ob

      implicit none

      integer, intent (in) :: jrch
      integer :: ipf = 0                 !none |sequential PFAS counter
      integer :: jpf = 0                 !none |PFAS index in pfasdb
      integer :: j = 0
      integer :: iob = 0
      real :: const = 0.
      real :: volout = 0.                !m3   |reach outflow volume for the day
      real :: cfac = 0.                  !     |kg/m3 -> ng/L conversion (1.e9)

      j = jrch
      iob = sp_ob1%chandeg + j - 1
      cfac = 1.e9
      volout = pfas_qout%vol(j)

      !! derive daily outflow concentrations (ng/L) before the m/y/a roll-up
      do ipf = 1, npfas
        if (volout > 1.e-6) then
          chpfas_d(j)%pfas(ipf)%conc_sol = chpfas_d(j)%pfas(ipf)%sol_out / volout * cfac
          chpfas_d(j)%pfas(ipf)%conc_sor = chpfas_d(j)%pfas(ipf)%sor_out / volout * cfac
          chpfas_d(j)%pfas(ipf)%conc_tot = (chpfas_d(j)%pfas(ipf)%sol_out +              &
                                            chpfas_d(j)%pfas(ipf)%sor_out) / volout * cfac
        else
          chpfas_d(j)%pfas(ipf)%conc_sol = 0.
          chpfas_d(j)%pfas(ipf)%conc_sor = 0.
          chpfas_d(j)%pfas(ipf)%conc_tot = 0.
        end if
      end do

      !! print balance for each PFAS compound
      do ipf = 1, npfas
        jpf = pfas_num(ipf)

        chpfas_m(j)%pfas(ipf) = chpfas_m(j)%pfas(ipf) + chpfas_d(j)%pfas(ipf)

        !! daily print
        if (pco%day_print == "y" .and. pco%int_day_cur == pco%int_day) then
          if (pco_pfas%d == "y") then
            write (7100,100) time%day, time%mo, time%day_mo, time%yrc, j, ob(iob)%gis_id, &
              ob(iob)%name, pfasdb(jpf)%name, chpfas_d(j)%pfas(ipf)
            if (pco%csvout == "y") then
              write (7104,'(*(G0.6,:","))') time%day, time%mo, time%day_mo, time%yrc, j,  &
                ob(iob)%gis_id, ob(iob)%name, pfasdb(jpf)%name, chpfas_d(j)%pfas(ipf)
            end if
          end if
        end if

        !! check end of month
        if (time%end_mo == 1) then
          chpfas_y(j)%pfas(ipf) = chpfas_y(j)%pfas(ipf) + chpfas_m(j)%pfas(ipf)
          const = float (ndays(time%mo + 1) - ndays(time%mo))
          chpfas_m(j)%pfas(ipf) = chpfas_m(j)%pfas(ipf) // const

          if (pco_pfas%m == "y") then
            write (7101,100) time%day, time%mo, time%day_mo, time%yrc, j, ob(iob)%gis_id, &
              ob(iob)%name, pfasdb(jpf)%name, chpfas_m(j)%pfas(ipf)
            if (pco%csvout == "y") then
              write (7105,'(*(G0.6,:","))') time%day, time%mo, time%day_mo, time%yrc, j,  &
                ob(iob)%gis_id, ob(iob)%name, pfasdb(jpf)%name, chpfas_m(j)%pfas(ipf)
            end if
          end if
          chpfas_m(j)%pfas(ipf) = ch_pfasbz
        end if

        !! check end of year
        if (time%end_yr == 1) then
          chpfas_a(j)%pfas(ipf) = chpfas_a(j)%pfas(ipf) + chpfas_y(j)%pfas(ipf)
          const = time%day_end_yr
          chpfas_y(j)%pfas(ipf) = chpfas_y(j)%pfas(ipf) // const

          if (pco_pfas%y == "y") then
            write (7102,100) time%day, time%mo, time%day_mo, time%yrc, j, ob(iob)%gis_id, &
              ob(iob)%name, pfasdb(jpf)%name, chpfas_y(j)%pfas(ipf)
            if (pco%csvout == "y") then
              write (7106,'(*(G0.6,:","))') time%day, time%mo, time%day_mo, time%yrc, j,  &
                ob(iob)%gis_id, ob(iob)%name, pfasdb(jpf)%name, chpfas_y(j)%pfas(ipf)
            end if
          end if
        end if

        !! average annual print
        if (time%end_sim == 1 .and. pco_pfas%a == "y") then
          chpfas_a(j)%pfas(ipf) = chpfas_a(j)%pfas(ipf) / time%yrs_prt
          chpfas_a(j)%pfas(ipf) = chpfas_a(j)%pfas(ipf) // time%yrs_prt
          write (7103,100) time%day, time%mo, time%day_mo, time%yrc, j, ob(iob)%gis_id,   &
            ob(iob)%name, pfasdb(jpf)%name, chpfas_a(j)%pfas(ipf)
          if (pco%csvout == "y") then
            write (7107,'(*(G0.6,:","))') time%day, time%mo, time%day_mo, time%yrc, j,    &
              ob(iob)%gis_id, ob(iob)%name, pfasdb(jpf)%name, chpfas_a(j)%pfas(ipf)
          end if
          chpfas_a(j)%pfas(ipf) = ch_pfasbz
        end if

      end do    ! PFAS loop

      return

!!    4 time ints, unit, gis_id, name(16), pfas-name(16), then 12 reals:
!!    9 balance(kg) + 3 conc(ng/L)
100   format (4i6,2i8,2x,a16,2x,a16,12e14.5)

      end subroutine cha_pfas_output
```

Note the `chpfas_d(j)%pfas(ipf)` derived-type write: the `100` format consumes the 12 reals of `pfas_cha_processes` **in declaration order** — so the type's field order must be `tot_in, sol_out, sor_out, settle, resus, difus, bury, water, benthic, conc_sol, conc_sor, conc_tot`. (Fortran writes a derived type by listing components in order; keep the three `conc_*` fields **last** in the type so the column order matches the header below.)

## 3. Header extension (`pfas_cha_header` in `pfas_cha_module`)

Append the three concentration columns to `chpfas_hdr` (after `benthic`), so header order matches the record write:

```fortran
          character(len=15) :: conc_sol = "sol_conc_ngL "
          character(len=15) :: conc_sor = "sor_conc_ngL "
          character(len=15) :: conc_tot = "tot_conc_ngL "
```

## 4. File-open plumbing (add to `header_pest.f90`, guarded by `pco_pfas`)

Mirror the `CHANNEL_PEST` block. Units **7100–7107** (txt 7100-7103, csv 7104-7107) — pick any free block; pesticide uses 2808-2815, salt/cs use 28xx, so 7100+ is clear. Add after the channel-pest block:

```fortran
     if (sp_ob%chandeg > 0 .and. npfas > 0) then
       if (pco_pfas%d == "y") then
         call open_output_file(7100, "channel_pfas_day.txt", 800)
         write (7100,*) bsn%name, prog
         write (9000,*) "CHANNEL_PFAS              channel_pfas_day.txt"
         write (7100,*) chpfas_hdr
         if (pco%csvout == "y") then
           call open_output_file(7104, "channel_pfas_day.csv", 800)
           write (7104,*) bsn%name, prog
           write (7104,'(*(G0.6,:","))') chpfas_hdr
           write (9000,*) "CHANNEL_PFAS              channel_pfas_day.csv"
         end if
       end if
       ! ... mon (7101/7105), yr (7102/7106), aa (7103/7107) blocks, identical pattern
     end if
```
(`use pfas_module, only : npfas` and `use pfas_cha_module` at the top of `header_pest.f90`.)

## 5. Command wiring (`command.f90`)

Mirror line 570. After the `call cha_pesticide_output (jrch)` call, add:
```fortran
            if (npfas > 0) call cha_pfas_output (jrch)
```
and add `cha_pfas_output` to the `command.f90` import list at line 34, plus `use pfas_module, only : npfas`.

## 6. OUTPUT-FILE COLUMN SPEC

Files (one row per channel × PFAS compound × timestep): `channel_pfas_day.txt/.csv`, `channel_pfas_mon.*`, `channel_pfas_yr.*`, `channel_pfas_aa.*`.

| # | Column | Units | Source |
|---|--------|-------|--------|
| 1 | jday | day-of-year | `time%day` |
| 2 | mon | month | `time%mo` |
| 3 | day | day-of-month | `time%day_mo` |
| 4 | yr | calendar yr | `time%yrc` |
| 5 | unit | channel id | `jrch` |
| 6 | gis_id | GIS id | `ob(iob)%gis_id` |
| 7 | name | channel name | `ob(iob)%name` |
| 8 | pfas | compound name | `pfasdb(jpf)%name` |
| 9 | tot_in_kg | kg | PFAS into reach (inflow load) |
| 10 | sol_out_kg | kg | soluble PFAS leaving reach |
| 11 | sor_out_kg | kg | sorbed PFAS leaving reach |
| 12 | settle_kg | kg | settled water→bed |
| 13 | resuspend_kg | kg | resuspended bed→water |
| 14 | diffuse_kg | kg | net sediment↔water diffusion (signed) |
| 15 | bury_benth_kg | kg | buried out of active bed layer |
| 16 | water_stor_kg | kg | water-column pool end-of-day |
| 17 | benthic_kg | kg | bed-sediment pool end-of-day |
| 18 | **sol_conc_ngL** | **ng/L** | `sol_out_kg / vol_out_m3 * 1e9` |
| 19 | **sor_conc_ngL** | **ng/L** | `sor_out_kg / vol_out_m3 * 1e9` |
| 20 | **tot_conc_ngL** | **ng/L** | `(sol_out+sor_out) / vol_out_m3 * 1e9` — **the EGLE-station calibration target** |

**Calibration note:** the EGLE PFOS surface-water observations are total (unfiltered) concentrations in ng/L, so column 20 (`tot_conc_ngL`) on the **daily** file is the calibration variable; pair it with the observed station by matching the station's snapped channel `jrch` and the observation date, exactly as the streamflow calibrator matches `channel_sd_day` discharge. Columns 9–17 are the closed daily mass balance (`tot_in + resus + diffuse_in == sol_out + sor_out + settle + bury + Δwater + Δbenthic`) for QA.

---

## Concentration-unit derivation (load-bearing)

`1 kg/m³ = 1e6 mg / 1e3 L = 1e3 mg/L = 1e6 µg/L = 1e9 ng/L`, so `conc_ngL = mass_kg / vol_m3 * 1.e9`. `vol_out` is the actual water leaving the reach that day, `rto_out * (ht2%flo + ch_stor%flo)` (m³), captured in `pfas_qout%vol(jrch)` inside `pfas_cha`.

## Files / status

- `cha_pfas_output.f90` — **new, full source above**; ship as-is.
- `pfas_cha_module.f90` (deferred draft, `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/deferred_instream/pfas_cha_module.f90`) — **extend**: add `conc_sol/conc_sor/conc_tot` to `pfas_cha_processes` (last 3 fields, after `%benthic`) + the matching 3 lines in `chpfas_add/_div/_ave` + the 3 header fields in `pfas_cha_header`; add `pfas_outflow_vol`/`pfas_qout`, `pfas_print_codes`/`pco_pfas`.
- `pfas_cha.f90` (deferred draft) — **one added line**: `pfas_qout%vol(jrch) = rto_out*(ht2%flo+ch_stor(jrch)%flo)` after `hcs2%pfas` is set.
- `header_pest.f90` — add the `CHANNEL_PFAS` open block (§4), units 7100–7107.
- `command.f90` — add `cha_pfas_output` import + `if (npfas>0) call cha_pfas_output(jrch)` after the pesticide-output call.
- `pfas_cha_allocate` (the init routine from the prior brief) — also `allocate (pfas_qout%vol(sp_ob%chandeg), source=0.)`.
- Input reader for `pco_pfas` (the `d/m/y/a` flags) — add to wherever `print.prt` constituent flags are parsed (alongside `pco%pest`); default `"n"`.

**Indexing reminder for downstream writers:** channel-side PFAS uses the pesticide convention `chpfas_d(jrch)%pfas(ipf)%field` (per-PFAS record-of-fluxes), the **inverse** of the HRU side `hpfasb_d(j)%surq(ipf)` (vector-by-PFAS). The writer above respects the channel convention.
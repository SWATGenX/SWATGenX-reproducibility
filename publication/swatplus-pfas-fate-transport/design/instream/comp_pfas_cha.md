`rcurv` lives in `sd_channel_module` and `rttime` in `channel_module` — both already `use`d in the draft. The draft is correct; I just need to clean the fixed-form continuations to free-form and keep the contract-bound names. Here is the final compilable routine.

```fortran
      subroutine pfas_cha

!!     ~ ~ ~ PURPOSE ~ ~ ~
!!     In-stream PFAS fate-and-transport for modern (free-form) SWAT+ --
!!     SERIAL channel phase.  Computes the daily reach PFAS balance
!!     (soluble + sorbed) using a LINEAR-Koc partition and benthic exchange.
!!
!!     Faithful clone of the SWAT+ pesticide in-stream routine ch_rtpest.f90
!!     (linear-Koc subset) wired to the pfas_module / pfas_cha_module
!!     containers.  Ported from the SWAT2012 PFAS implementation
!!     (Vahid Rafiei): rtpfas.f -- a renamed clone of the pesticide
!!     instream model with a LINEAR Koc partition.  The physics is identical
!!     to ch_rtpest: settling, resuspension, sediment-water diffusion, and
!!     burial, all driven by frsol = 1/(1+kd*sedcon).  PFAS therefore DROPS
!!     the three pesticide-only loss terms (no chemical/biological reaction
!!     decay_a/decay_b, no volatilization aq_volat, no metabolite daughters)
!!     and keeps everything else.
!!
!!     legacy rtpfas variable        this routine / SWAT+ field
!!     --------------------------    ----------------------------------------
!!     chpfas_koc(jrch)  (m3/g)      pfas_chadb(jpf)%koc * carbon/100  (= kd)
!!     chpfas_stl(jrch)  (m/day)     pfas_chadb(jpf)%aq_settle
!!     chpfas_rsp(jrch)  (m/day)     pfas_chadb(jpf)%aq_resus
!!     chpfas_mix(jrch)  (m/day)     sd_ch(jrch)%aq_mix(ipf)
!!     sedpfas_bry(jrch) (m/day)     pfas_chadb(jpf)%ben_bury
!!     sedpfas_act(jrch) (m)         pfas_chadb(jpf)%ben_act_dep
!!     varoute(34/35,:)  (PFAS mass) hcs1%pfas(ipf)  (sol+sorbed combined,
!!                                   repartitioned each day by frsol/frsrb)
!!     chpfas_conc*rchwtr            ch_pfas_water(jrch)%pfas(ipf)    (kg)
!!     sedpfas_conc*bedvol           ch_pfas_benthic(jrch)%pfas(ipf) (kg)
!!     solpfaso / sorpfaso           frsol*hcs2%pfas / frsrb*hcs2%pfas
!!
!!     ~ ~ ~ REENTRANCY ~ ~ ~
!!     This is the SERIAL channel phase.  It writes shared per-reach state
!!     (ch_pfas_water/benthic, chpfas_d) and is NOT called from the parallel
!!     land phase, so no OpenMP guard is needed here.
!!    ~ ~ ~ ~ ~ ~ END SPECIFICATIONS ~ ~ ~ ~ ~ ~

      use channel_data_module
      use channel_module
      use sd_channel_module
      use pfas_cha_module
      use pfas_module, only : npfas, pfas_num, pfasdb
      use hydrograph_module, only : jrch, ht1, ht2, ch_stor, hcs1, hcs2
      use constituent_mass_module, only : ch_pfas_water, ch_pfas_benthic

      implicit none

      integer :: ipf = 0        !none          |PFAS counter - sequential
      integer :: jpf = 0        !none          |PFAS counter from data base
      real :: pfin = 0.         !kg            |total PFAS transported into reach during time step
      real :: kd = 0.           !(mg/kg)/(mg/L)|koc * carbon
      real :: depth = 0.        !m             |depth of water in reach
      real :: chpfmass = 0.     !kg            |mass of PFAS in reach water column
      real :: sedpfmass = 0.    !kg            |mass of PFAS in bed sediment
      real :: fd2 = 0.          !none          |benthic sorbed/total partition factor
      real :: solmax = 0.       !kg            |max soluble PFAS at solubility limit
      real :: sedcon = 0.       !g/m^3         |sediment concentration
      real :: tday = 0.         !none          |flow duration (fraction of 24 hr)
      real :: por = 0.          !none          |porosity of bottom sediments
      real :: rto_out = 0.      !none          |ratio of outflow to (outflow + storage)
      real :: wtrin = 0.        !m^3 H2O       |volume of water entering+stored in reach

      !! zero daily outputs for this reach
      chpfas_d(jrch) = chpfasz

      !! initialize depth of water for PFAS calculations
      depth = rcurv%dep
      if (depth < 0.01) then
        depth = .01
      endif

      do ipf = 1, npfas
        jpf = pfas_num(ipf)

        !! volume of water entering reach and stored in reach
        wtrin = ht1%flo + ch_stor(jrch)%flo

        !! PFAS transported into reach during day (kg; sol+sorbed combined)
        pfin = hcs1%pfas(ipf)

        !! calculate mass of PFAS in reach water column
        chpfmass = pfin + ch_pfas_water(jrch)%pfas(ipf)

        !! calculate mass of PFAS in bed sediment
        sedpfmass = ch_pfas_benthic(jrch)%pfas(ipf)

        if (chpfmass + sedpfmass < 1.e-12) then
          ch_pfas_water(jrch)%pfas(ipf) = 0.
          ch_pfas_benthic(jrch)%pfas(ipf) = 0.
        end if
        if (chpfmass + sedpfmass < 1.e-12) cycle

        !!in-stream processes
        if (wtrin / 86400. > 1.e-9) then
          !! calculate sediment concentration (g/m^3)
          sedcon = ht1%sed / wtrin * 1.e6

          !! set kd (linear Koc * organic carbon fraction)
          kd = pfas_chadb(jpf)%koc * sd_ch(jrch)%carbon / 100.

          !! calculate fraction of soluble and sorbed PFAS
          if (kd > 0.) then
            frsol = 1. / (1. + kd * sedcon)
          else
            frsol = 1.
          end if
          frsrb = 1. - frsol

          !! ASSUME DENSITY=2.65E6; KD2=KD1 (benthic partition)
          por = 1. - sd_ch(jrch)%ch_bd / 2.65
          fd2 = 1. / (por + kd)

          !! calculate flow duration
          tday = rttime / 24.0
          if (tday > 1.0) tday = 1.0

          !! -----------------------------------------------------------
          !! NOTE: pesticide reaction (decay_a) and volatilization
          !! (aq_volat) terms of ch_rtpest are intentionally OMITTED --
          !! PFAS are non-volatile and non-degradable in this model.
          !! -----------------------------------------------------------

          !! calculate amount of PFAS removed from reach by settling
          chpfas_d(jrch)%pfas(ipf)%settle = pfas_chadb(jpf)%aq_settle *    &
                              frsrb * chpfmass * tday / depth
          if (chpfas_d(jrch)%pfas(ipf)%settle > frsrb * chpfmass) then
            chpfas_d(jrch)%pfas(ipf)%settle = frsrb * chpfmass
            chpfmass = chpfmass - chpfas_d(jrch)%pfas(ipf)%settle
          else
            chpfmass = chpfmass - chpfas_d(jrch)%pfas(ipf)%settle
          end if
          sedpfmass = sedpfmass + chpfas_d(jrch)%pfas(ipf)%settle

          !! calculate resuspension of PFAS in reach
          chpfas_d(jrch)%pfas(ipf)%resus = pfas_chadb(jpf)%aq_resus *      &
                              sedpfmass * tday / depth
          if (chpfas_d(jrch)%pfas(ipf)%resus > sedpfmass) then
            chpfas_d(jrch)%pfas(ipf)%resus = sedpfmass
            sedpfmass = 0.
          else
            sedpfmass = sedpfmass - chpfas_d(jrch)%pfas(ipf)%resus
          end if
          chpfmass = chpfmass + chpfas_d(jrch)%pfas(ipf)%resus

          !! calculate diffusion of PFAS between reach water and sediment
          chpfas_d(jrch)%pfas(ipf)%difus = sd_ch(jrch)%aq_mix(ipf) *       &
                              (fd2 * sedpfmass - frsol * chpfmass) * tday / depth
          if (chpfas_d(jrch)%pfas(ipf)%difus > 0.) then
            if (chpfas_d(jrch)%pfas(ipf)%difus > sedpfmass) then
              chpfas_d(jrch)%pfas(ipf)%difus = sedpfmass
              sedpfmass = 0.
            else
              sedpfmass = sedpfmass - Abs(chpfas_d(jrch)%pfas(ipf)%difus)
            end if
            chpfmass = chpfmass + Abs(chpfas_d(jrch)%pfas(ipf)%difus)
          else
            if (Abs(chpfas_d(jrch)%pfas(ipf)%difus) > chpfmass) then
              chpfas_d(jrch)%pfas(ipf)%difus = -chpfmass
              chpfmass = 0.
            else
              chpfmass = chpfmass - Abs(chpfas_d(jrch)%pfas(ipf)%difus)
            end if
            sedpfmass = sedpfmass + Abs(chpfas_d(jrch)%pfas(ipf)%difus)
          end if

          !! calculate removal of PFAS from active sediment layer by burial
          chpfas_d(jrch)%pfas(ipf)%bury = pfas_chadb(jpf)%ben_bury *       &
                              sedpfmass / pfas_chadb(jpf)%ben_act_dep
          if (chpfas_d(jrch)%pfas(ipf)%bury > sedpfmass) then
            chpfas_d(jrch)%pfas(ipf)%bury = sedpfmass
            sedpfmass = 0.
          else
            sedpfmass = sedpfmass - chpfas_d(jrch)%pfas(ipf)%bury
          end if

          !! verify that water concentration is at or below solubility
          solmax = pfasdb(jpf)%sol * wtrin
          if (solmax < chpfmass * frsol) then
            sedpfmass = sedpfmass + (chpfmass * frsol - solmax)
            chpfmass = chpfmass - (chpfmass * frsol - solmax)
          end if

        else
          !!insignificant flow -- all PFAS settles to bed
          sedpfmass = sedpfmass + chpfmass
          chpfmass = 0.
        end if

        !! benthic reaction term OMITTED for PFAS (non-degradable)

        !! set new water-column mass (in + store) after processes
        if (wtrin > 1.e-6) then
          chpfmass = chpfmass
        else
          sedpfmass = sedpfmass + chpfmass
          chpfmass = 0.
        end if
        ch_pfas_benthic(jrch)%pfas(ipf) = sedpfmass

        !! calculate outflow and storage in water column
        rto_out = ht2%flo / (1.e-6 + ht2%flo + ch_stor(jrch)%flo)
        rto_out = Min (1., rto_out)
        hcs2%pfas(ipf) = rto_out * chpfmass
        ch_pfas_water(jrch)%pfas(ipf) = (1. - rto_out) * chpfmass

        !! -----------------------------------------------------------
        !! daily reach PFAS output (kg); soluble/sorbed split of outflow
        !! -----------------------------------------------------------
        chpfas_d(jrch)%pfas(ipf)%tot_in  = pfin
        chpfas_d(jrch)%pfas(ipf)%sol_out = frsol * hcs2%pfas(ipf)
        chpfas_d(jrch)%pfas(ipf)%sor_out = frsrb * hcs2%pfas(ipf)
        chpfas_d(jrch)%pfas(ipf)%water   = ch_pfas_water(jrch)%pfas(ipf)
        chpfas_d(jrch)%pfas(ipf)%benthic = ch_pfas_benthic(jrch)%pfas(ipf)

      end do

      return
      end subroutine pfas_cha
```

---

DELIVERABLE: `pfas_cha.f90` (full text above — write it to `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_cha.f90`).

This is a faithful clone of `ch_rtpest.f90` adapted to the PFAS pools/params per the contract. Key points and the fixes applied versus the deferred draft at `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/deferred_instream/pfas_cha.f90`:

1. **Free-form continuations.** The deferred draft used legacy fixed-form continuation markers (`     &` in column 6 on the continued line, e.g. lines 147/158/169/190). Those are illegal in a free-form `.f90` and would fail to compile. Replaced every one with a clean free-form trailing `&` (continued line indented, no leading `&`). This was the only compile-blocking defect.

2. **Solubility call.** Dropped the contained `pfasdb_sol(idb)` helper function and instead `use pfas_module, only : ... pfasdb` directly, calling `pfasdb(jpf)%sol` inline (matches `ch_rtpest`'s `pestdb(jpst)%solub` idiom; behaviorally identical to the draft, fewer moving parts). Confirmed `pfasdb(:)%sol` exists in `pfas_module`.

3. **Water-column store line.** The pesticide template assigns `hcs1%pest(ipest) = chpstmass` to stage the post-process mass back; here the outflow split (`hcs2%pfas` / `ch_pfas_water`) is computed directly from `chpfmass` at the bottom, so the staging line is a no-op (`chpfmass = chpfmass`) kept only to preserve the structural mirror with `ch_rtpest`. The `else` branch (insignificant flow → all mass to bed) is retained exactly.

Contract-bound names all honored: reads `hcs1%pfas(ipf)`, writes `hcs2%pfas(ipf)`, updates `ch_pfas_water(jrch)%pfas(ipf)` / `ch_pfas_benthic(jrch)%pfas(ipf)`, accumulates `chpfas_d(jrch)%pfas(ipf)%{settle,resus,difus,bury,tot_in,sol_out,sor_out,water,benthic}`, sets module `frsol`/`frsrb`. Loop is over `npfas` with `jpf = pfas_num(ipf)`. Physics = linear-Koc soluble/sorbed split (`frsol=1/(1+kd*sedcon)`, `kd=koc*carbon/100`), settling, resuspension, signed water↔bed diffusion (`fd2`), burial, solubility cap, advective in/out via `rto_out`; pesticide-only reaction/volatilization/metabolite terms omitted (PFAS non-degradable, non-volatile).

Module-state dependencies verified present: `rcurv` (in `sd_channel_module`), `rttime` (in `channel_module`), both already `use`d. `pfas_chadb`, `chpfas_d`, `chpfasz`, `frsol`, `frsrb` come from `pfas_cha_module` (ship as-is per brief). `ch_pfas_water`/`ch_pfas_benthic` and the `%pfas` slot on `constituent_mass` are the §1a–1b declarations the integration brief adds to `constituent_mass_module.f90`.
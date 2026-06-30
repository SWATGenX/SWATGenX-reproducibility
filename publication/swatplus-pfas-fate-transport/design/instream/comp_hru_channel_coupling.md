I now have everything. The deferred `pfas_cha.f90` consumes `hcs1%pfas(ipf)` as the inbound load — so my deliverable is the HRU→channel coupling that fills `obcs(icmd)%hd(1..5)%pfas(ipf)` from `hpfasb_d(j)%{surq,latq,perc,sed}(ipf)`, mirroring the pesticide lines (91-175) but with PFAS's flipped indexing. Here is the deliverable.

---

# HRU→CHANNEL PFAS LOAD COUPLING — deliverable

## Where it goes and why

The land phase writes per-HRU PFAS losses into `hpfasb_d(j)%{surq,latq,perc,sed}(ipf)` in **kg/ha** (vector indexed by PFAS — the inverse of pesticide's `hpestb_d(j)%pest(ipf)%surq`). `hru_hyds` is the single place SWAT+ converts every land-phase loss to a **kg** mass on the outgoing hydrograph `obcs(icmd)%hd(k)%<const>(i)`, using `cnv_kg = hru(j)%area_ha`. Routing then carries `obcs(icmd)%hin(1) → hcs1` into `pfas_cha`, which reads exactly `hcs1%pfas(ipf)`. So the coupling is four blocks inside `hru_hyds`, slotted right after each existing pesticide block, plus the use-statements:

| hydrograph | PFAS land losses delivered | matches pesticide line |
|---|---|---|
| `hd(3)` surface | `surq + sed` (runoff + sediment-sorbed) | 91-93 |
| `hd(2)` recharge | `perc` (leached out profile bottom) | 108-110 |
| `hd(4)` lateral | `latq` | 126-128 |
| `hd(1)` total | `hd(3)+hd(4)+hd(5)` | 172-175 |

Tile (`hd(5)`) has no PFAS source term (`pfas_output_module` has no `tileq`), so `hd(5)%pfas` stays zero (from `hin_csz` re-init at line 54-58) and the `hd(1)` sum still adds it harmlessly. PFAS is guarded by `npfas > 0` rather than `cs_db%num_*` because PFAS count lives in `pfas_module`, not `cs_db`.

The PFAS hydrograph vectors are zeroed each day by the existing `obcs(icmd)%hd(k) = hin_csz` block (lines 54-58), provided `hin_csz%pfas(npfas)` is allocated at init (brief §3c) — so no extra zeroing is needed here, matching pest/salt/cs which rely on the same re-init.

## Diff into `hru_hyds.f90`

**1. Use statements** — add after line 17 (`use output_ls_pesticide_module`):

```fortran
      use pfas_module, only : npfas
      use pfas_output_module, only : hpfasb_d
```

**2. Counter declaration** — add after line 33 (`integer :: ics = 0`):

```fortran
      integer :: ipf = 0             !none          |counter for PFAS compounds
```

**3. Surface runoff hydrograph (3)** — insert after line 93 (after the `ipest`/`hd(3)%pest` loop):

```fortran
      do ipf = 1, npfas   !PFAS: surface-runoff dissolved + sediment-sorbed -> kg
        obcs(icmd)%hd(3)%pfas(ipf) = (hpfasb_d(j)%surq(ipf) + hpfasb_d(j)%sed(ipf)) * cnv_kg
      end do
```

**4. Recharge hydrograph (2)** — insert after line 110 (after the `hd(2)%pest` loop):

```fortran
      do ipf = 1, npfas   !PFAS: leached below profile -> recharge load (kg)
        obcs(icmd)%hd(2)%pfas(ipf) = hpfasb_d(j)%perc(ipf) * cnv_kg
      end do
```

**5. Lateral soil flow hydrograph (4)** — insert after line 128 (after the `hd(4)%pest` loop):

```fortran
      do ipf = 1, npfas   !PFAS: lateral subsurface flow load (kg)
        obcs(icmd)%hd(4)%pfas(ipf) = hpfasb_d(j)%latq(ipf) * cnv_kg
      end do
```

**6. Total outflow hydrograph (1)** — insert after line 175 (after the `hd(1)%pest` sum loop):

```fortran
      do ipf = 1, npfas   !PFAS total = surface (runoff+sed) + lateral + tile(=0)
        obcs(icmd)%hd(1)%pfas(ipf) = obcs(icmd)%hd(3)%pfas(ipf) + obcs(icmd)%hd(4)%pfas(ipf) +   &
                                                                  obcs(icmd)%hd(5)%pfas(ipf)
      end do
```

## Notes / contract points

- **Units**: `hpfasb_d` fields are kg/ha; `cnv_kg = hru(j)%area_ha` (line 43) converts to **kg**, identical to the pest/salt/cs lines. `pfas_cha` consumes `hcs1%pfas` as kg. Consistent end-to-end.
- **Index order**: PFAS uses `hpfasb_d(j)%surq(ipf)` (loss-field is the derived-type member, PFAS index is the array subscript) — the *flip* of pesticide `hpestb_d(j)%pest(ipf)%surq`. The diffs above already respect this; the channel side `obcs(...)%hd(k)%pfas(ipf)` follows the constituent-vector convention (subscript = PFAS), matching `hcs1%pfas(ipf)` in `pfas_cha`.
- **`hd(5)` tile**: left at zero (no land-phase tile-PFAS term). Including it in the `hd(1)` sum is correct and future-proof: if a `hpfasb_d%tileq` term is ever added, only an `hd(5)` block need be inserted, exactly mirroring `hd(5)%pest` (line 143-145).
- **Recharge (`hd(2)`) is intentionally NOT in the `hd(1)` total** — matches pesticides (perc goes to the aquifer recharge path, not the channel inflow), and matches the brief §3a which keeps `hd(1) = hd(3)+hd(4)` for the channel-delivered load.
- **No new zeroing**: relies on lines 54-58 re-initializing `obcs(icmd)%hd(1..5) = hin_csz` each HRU-day. This requires `hin_csz%pfas(npfas)` and each `obcs(...)%hd(k)%pfas(npfas)` allocated at startup (brief §3c, `pfas_cha_allocate`). Without that allocation these diffs will segfault on the first `%pfas(ipf)` reference — the allocation wiring is the prerequisite, exactly as for pest/salt/cs.

## Relevant file paths

- Edited routine: `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/hru_hyds.f90`
- Consumer (reads `hcs1%pfas`): `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/deferred_instream/pfas_cha.f90` (lines 101, 215)
- Source land-phase losses: `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_output_module.f90` (`hpfasb_d`)
- Counts/crosswalk: `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/pfas_module.f90` (`npfas`, `pfas_num`)
- Slot to be added (`%pfas` on constituent_mass): `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/src/constituent_mass_module.f90` (brief §1a — prerequisite)
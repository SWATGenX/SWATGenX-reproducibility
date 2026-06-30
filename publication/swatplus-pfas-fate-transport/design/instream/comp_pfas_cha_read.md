Compiles clean. The deliverable is complete. Here is the summary.

---

## Deliverable

**File written:** `/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/engine/deferred_instream/pfas_cha_read.f90`

A combined reader + allocator (the PFAS analogue of `pest_cha_res_read.f90` + the pesticide channel-pool block of `sd_channel_read.f90` + the `%pest` hydrograph allocation of `hyd_read_connect.f90`/`hyd_connect.f90`). Syntax-verified with gfortran against stub modules matching the real type/interface contract — compiles clean. It is a no-op when `npfas <= 0`, and routes with built-in PFOS-like defaults when `pfas_cha.dat` is absent.

### What it does (in order)
1. **`pfas_chadb(1:npfas)`** — allocated and seeded with PFOS-like defaults (`koc=1.e-5 m^3/g`, `aq_settle=1.0`, `aq_resus=0.05`, `ben_bury=0.001 m/day`, `ben_act_dep=0.1 m`).
2. **`pfas_water_ini(1:npfas)`** — allocated (`%water(1)`, `%benthic(1)`), default 0.
3. **Reads `pfas_cha.dat`** (if present) overriding params + initial conc per compound; trailing `water_ppt`/`benthic_ppt` columns are optional (list-directed read leaves them 0).
4. **Per-channel pools** `ch_pfas_water/benthic(0:chandeg)%pfas(npfas)` + `_init` copies, and **daily/monthly/yearly/avg** `chpfas_d/m/y/a(0:chandeg)%pfas(npfas)` (zeroed via `ch_pfasbz`), plus scalar `chpfas`/`chpfasz`. Initial pools are computed from the read concentrations: water `= ng/L * 1.e-9 * ch_stor%flo`; benthic `= ng/g * 1.e-12 * active-bed sediment mass`, where `bedmass = chw * (chl*1000) * ben_act_dep * (ch_bd*1000) * (1-porosity)` and `porosity = 1 - ch_bd/2.65` (mirrors `rtpfas.f` bed-volume init).
5. **`%pfas` hydrograph slots** on `hcs1/hcs2/hcs3`, `hin_csz`, and every `obcs(iob)%{hin,hin_sur,hin_lat,hin_til,hin_aqu}(1)%pfas` + all `obcs(iob)%hd(:)%pfas`, looping all objects under the `obcs_alloc(iob)==1` guard, each `allocated()`-guarded for safety.

### Input-file format — `pfas_cha.dat`
Two header lines, then one record per PFAS compound. List-directed (free) columns; a record with `id<=0` ends the list. `id` maps to the database compound via `pfas_num`.

```
PFAS in-stream (channel) transport parameters
 id  name              koc      settle   resus    bury     act_dep  water_ppt  benthic_ppt
  1  PFOS            1.0e-5     1.00     0.050    0.0010    0.10       0.0        0.0
  2  PFOA            5.0e-6     0.50     0.050    0.0010    0.10       0.0        0.0
  0  end
```

| col | name | units | target |
|---|---|---|---|
| id | sequential PFAS index (1..npfas); `<=0` ends list | - | crosswalk |
| name | compound name (informational) | a16 | `pfas_chadb%name` |
| koc | linear water-sediment partition | m³/g | `pfas_chadb%koc` |
| settle | settling velocity of sorbed PFAS | m/day | `pfas_chadb%aq_settle` |
| resus | resuspension velocity | m/day | `pfas_chadb%aq_resus` |
| bury | burial velocity in bed sediment | m/day | `pfas_chadb%ben_bury` |
| act_dep | active bed-sediment layer depth | m | `pfas_chadb%ben_act_dep` |
| water_ppt | *(optional)* initial reach water-column conc | ng/L | `pfas_water_ini%water` |
| benthic_ppt | *(optional)* initial bed-sediment conc | ng/g | `pfas_water_ini%benthic` |

Trailing `water_ppt`/`benthic_ppt` may be omitted (reach starts PFAS-free). If the whole file is absent, every compound gets the PFOS-like defaults and a clean reach, so a model with no `pfas_cha.dat` still routes HRU PFAS loads through `pfas_cha`.

### Integration notes for the parent/caller (not yet wired here)
- **Call site:** invoke `call pfas_cha_read` once during init, **after** `pfas_read` (sets `npfas`/`pfasdb`/`pfas_num`), `sd_channel_read` (sets `sp_ob%chandeg`/`sd_ch` geometry + `ch_stor`), and `hyd_read_connect` (allocates `obcs`/`obcs_alloc`). Mirror where `pest_cha_res_read` is called.
- **`obcs` dependency:** `obcs`/`obcs_alloc` are only allocated when `cs_db%num_tot > 0` (see `hyd_read_connect.f90:80`). For PFAS HRU loads to reach channels via `obcs(icmd)%hd(1)%pfas`, `obcs` must exist when `npfas>0`. The brief's §3c plan is to bump `cs_db%num_tot` when PFAS is active; this reader is `allocated()`-guarded so it is safe either way, but the load path (§3b) requires `obcs` present.
- **Type additions still required** (per the brief §1a–1d, not part of this reader file): `constituent_mass%pfas`; `ch_pfas_water/ch_pfas_benthic[_init]`; `pfas_water_init_concentrations` + `pfas_water_ini` — all in `constituent_mass_module.f90`. The reader `use`s exactly these names. The `pfas_cha_module` names (`pfas_chadb`, `chpfas_d/m/y/a`, `chpfas`, `chpfasz`, `ch_pfasbz`) already exist in the deferred `pfas_cha_module.f90`.
- **No `db_mx` field used** — the reader stores no record-max in `db_mx` (`pfas_chadb` is sized by `npfas`, not a file count). If a count is wanted in the input summary, add a `db_mx%pfas_cha` integer and assign `imax` (a one-line addition is flagged in a comment in the file).
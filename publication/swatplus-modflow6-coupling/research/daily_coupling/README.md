# Daily two-way SWAT+ ↔ MODFLOW 6 coupling — build tools

These scripts prepare the inputs for the live daily two-way flow coupling
implemented in the SWAT+ engine (`mf6_coupler.f90`, fork branch
`feat/pfas-surface-water`). The engine embeds MODFLOW 6 via its BMI/XMI C
interface (`libmf6.so`, `dlopen`ed with `RTLD_LOCAL`) and exchanges state every
simulated day:

- **down** — SWAT+ soil-profile percolation (`sepbtm`, mm/d) → MF6 recharge,
  area-weighted onto the MODFLOW grid, overwritten between `prepare_time_step`
  and `do_time_step`.
- **up** — MF6 SFR per-reach groundwater↔stream exchange (`GWFLOW`) → aggregated
  to SWAT+ channels and added to the channel inflow, replacing the native SWAT+
  aquifer return (no double counting).

## Activation

Place an `mf6.con` file in the SWAT+ `TxtInOut`:

```
./mf6     # workspace holding mfsim.nam (relative to TxtInOut)
1         # GWF (flow) step cadence, days
30        # GWT (transport) step cadence, days
```

Coupling is a no-op when `mf6.con` is absent, so existing models are unaffected.

## Workflow

1. **`build_daily_mf6.py <nper_days> <out_ws>`** — regenerate the calibrated MF6
   flow model with daily stress periods + transient storage (one MF6 stress
   period per SWAT+ day). Writes to `TxtInOut/mf6/`.

2. **`build_recharge_map.py <out>`** — area-weighted HRU → MF6-cell map
   (`mf6_recharge.map`) from `Grids_MODFLOW.shp ∩ hrus2.shp`. Index =
   `row*NCOL+col` (matches the BMI `RECHARGE` array); weight = overlap/cell area.

3. **`build_baseflow_map.py <reach_to_channel.csv> <out>`** — SFR reach → SWAT+
   channel (gis id) map (`mf6_baseflow.map`).

Put `mf6_recharge.map` and `mf6_baseflow.map` next to `mf6.con` in `TxtInOut`.

## Validation (Rogue, USGS 04118500)

- Net groundwater→stream exchange **+27 Mm³/yr gaining**, matching MODFLOW's own
  GWF volumetric budget exactly.
- Recharge **~139 mm/yr** basin-average (daily-varying with SWAT+ hydrology).
- SFR sign: `GWFLOW > 0` = stream loses to aquifer; `< 0` = aquifer feeds stream
  (baseflow), so baseflow-into-channel = `-GWFLOW`.

Paths in the scripts are currently hard-coded to the Rogue model; parameterize
before reuse on other watersheds.

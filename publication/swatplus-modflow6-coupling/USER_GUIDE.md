# Running the coupled SWAT⁺ ↔ MODFLOW 6 PFAS model — a plain-language guide

This guide tells you, step by step, **how to run** the coupled surface-water /
groundwater PFAS model. It assumes no programming background. For the *science*
(why the model works, where the data come from), see the paper; for *how to run
it*, everything you need is here.

There are **two ways** to get a working model. Pick one:

- **A — The easy way (no installation):** generate the model on the SWATGenX
  website. Best if you are in the United States and want results without setting
  up software.
- **B — The full way (on your own computer):** download the code and an example
  model and run it on your Windows desktop. Best if you want to change the model,
  run many scenarios, or work offline.

> **About the figures.** The data-flow diagram (`figures/guide_workflow.png`) and
> the file templates and real output snippets below are included and complete.
> The interface screenshots *(Figure A1–A4 of the swatgenx.com pages, Figure B1 of
> the compile step)* are website/desktop captures to be added by a person; each
> step text tells you exactly what you should see, so you can follow it without
> them. Drop the captures into `figures/` with those names when available.

**What the model represents** *(see `figures/conceptual_model.png`)* — PFAS is
partitioned in the soil profile (aqueous / solid / air–water interface), routed to
streams with runoff, lateral flow, and sediment, and — new in this work — carried
to groundwater and back through the daily two-way SWAT⁺↔MODFLOW 6 coupling
(recharge down, baseflow up), a retardation-lagged vadose pathway, the legacy
groundwater plume, and groundwater PFAS discharge to streams.

**How the pieces fit together** *(see `figures/guide_workflow.png`)* — the engine
reads your `TxtInOut` files, runs the SWAT⁺ land phase, sends recharge and leached
PFAS **down** to MODFLOW 6, gets baseflow and discharged PFAS **back up** into the
streams, and writes the surface, groundwater, and exchange outputs:

```
 TxtInOut --read--> SWAT+ land phase --DOWN: recharge + PFAS--> MODFLOW 6
                          ^                                        |
                          +---------- UP: baseflow + PFAS ---------+
   outputs: pfas_hru_aa.txt . channel_pfas_day.txt . mf6/pfas.ucn . mf6/pfas.lst
```

---

## A. The easy way — build it on swatgenx.com

1. Go to **https://swatgenx.com** and create a free account *(Figure A1)*.
2. On the map, **find your watershed** by its USGS streamgage number or by
   clicking the stream network *(Figure A2)*.
3. Choose what to build:
   - **SWAT⁺ (surface water)** — available for the **entire continental US**.
   - **SWAT⁺ + MODFLOW 6 (surface water + groundwater)** — currently available
     for the **Michigan Lower Peninsula** only. **More states are coming soon.**
   - Turn on the **PFAS** option if you want PFAS fate and transport *(Figure A3)*.
4. Click **Build**. When it finishes you get a download link and an online
   dashboard with the results *(Figure A4)*.
5. Download the model folder. Inside it is a folder called **`TxtInOut`** — this
   is the model. You can stop here (use the website results), or run it yourself
   with the engine in Section B.5.

That's it. If MODFLOW 6 is not yet available for your state, you can still build
SWAT⁺ everywhere and add groundwater later.

---

## B. The full way — run it on your Windows desktop

### B.1 Get the code
1. Install **Git for Windows** (https://git-scm.com) — accept the defaults.
2. Open **Git Bash** (Start menu → "Git Bash").
3. Copy the code to your computer:
   ```
   git clone https://github.com/rafiei-vahid/swatplus.git
   cd swatplus
   git checkout feat/pfas-surface-water
   ```
   This gives you the SWAT⁺ engine **with the PFAS and MODFLOW 6 coupling built
   in**.

### B.2 Get an example model
Download the **example Rogue River PFAS model** from the link on the paper's
data page and unzip it. You will get a `TxtInOut` folder full of text files —
that *is* the model.

### B.3 Compile the engine (Windows)
You need the **Intel Fortran compiler (ifx)**, which is free in the *Intel oneAPI
HPC Toolkit* (https://www.intel.com/oneapi). Install it, then:
1. Open the **"Intel oneAPI command prompt"** (Start menu).
2. Go to the code folder and build:
   ```
   cd swatplus
   cmake -B build -S . -DCMAKE_Fortran_COMPILER=ifx
   cmake --build build
   ```
3. You now have **`swatplus.exe`** in the `build` folder *(Figure B1)*. Copy it
   into your `TxtInOut` folder.

> If you only want surface-water SWAT⁺ (no MODFLOW 6), that's all. The groundwater
> coupling switches on only when the control file in Section B.4 is present.

### B.4 Tell the engine to use MODFLOW 6
The engine runs MODFLOW 6 **only if it finds a small text file named `mf6.con`**
in your `TxtInOut` folder. No file = plain SWAT⁺ (nothing changes). With the
file = live daily two-way coupling.

**Where does the MODFLOW 6 model live?** In a **sub-folder of `TxtInOut`** — by
convention `TxtInOut/mf6/` — that contains the MODFLOW 6 files (`mfsim.nam`, the
`.dis`, `.npf`, `.sfr`, etc.). The engine loads the MODFLOW 6 library
(`libmf6.so` / `libmf6.dll`) and drives it from this folder.

**`mf6.con` — copy this template** (lines after `!` are ignored):
```
./mf6        ! 1: folder (inside TxtInOut) holding mfsim.nam
1            ! 2: groundwater FLOW step, in days (1 = daily)
30           ! 3: groundwater TRANSPORT step, in days (30 = monthly)
1.0          ! 4: (optional) recharge multiplier for calibration
             ! 5: (optional) full path to libmf6 if not on the default search path
```

Two small **map files** also go in `TxtInOut` (the website and the example model
already include them; you only make them yourself for a brand-new watershed):

| File | What it does |
|---|---|
| `mf6_recharge.map` | links each SWAT⁺ field (HRU) to the MODFLOW cells under it, so percolation becomes groundwater recharge |
| `mf6_baseflow.map` | links each MODFLOW stream reach to its SWAT⁺ channel, so groundwater discharge returns to the right stream |
| `pfas_leach.map` | (PFAS only) links fields to cells so soil-leached PFAS becomes a groundwater source |

### B.5 Run it
From the Intel oneAPI command prompt, inside `TxtInOut`:
```
swatplus.exe
```
You will see the day-by-day progress, and — if `mf6.con` is present — a line
`MF6 COUPLER: active`, then at the end a summary of the water and PFAS exchanged
between surface water and groundwater *(Figure B2)*.

---

## Turning PFAS on

PFAS is controlled by **two files in `TxtInOut`** (already present in the example
and the website models):

- **`pfas.dat`** — the list of PFAS compounds and their chemistry. No file = no
  PFAS.
- **`pfas_hru.ini`** — the starting amount of PFAS in each field's soil, plus its
  soil-sorption numbers.

### `pfas.dat` — one row per compound
```
 id  name      mw        sol      kl       lm       percop
  1  PFOS    0.50013   680.0    0.137   2500.0    0.20
  0  END     0.0       0.0      0.0      0.0       0.0
```

### `pfas_hru.ini` — starting soil PFAS and sorption, per field
```
hru 1 nly 4                                    <- field 1 has 4 soil layers
1                                              <- number of PFAS in this field
0.0400 0.0600 0.0600 0.0500                    <- grain size d50 (mm), per layer
1 1.536e+07 5.610e+06 6.591e+06 1.107e+07      <- PFAS id + starting soil PFAS per layer
1 450.2 227.8 227.8 365.7                      <- Freundlich kf per layer
1 0.4300 0.3800 0.3800 0.4500                  <- Freundlich n per layer
1 1.0                                          <- enrichment ratio (sediment)
```

---

## The PFAS parameters added to SWAT⁺

These are every input the PFAS module adds, mirroring the parameter list in the
2023 *Water Research* paper's supplementary material. The three-phase soil model
(aqueous / solid / air–water interface) uses them all.

| Parameter | File | Units | Meaning |
|---|---|---|---|
| `mw` | pfas.dat | kg mol⁻¹ | molecular weight of the compound |
| `sol` | pfas.dat | mg L⁻¹ | maximum aqueous solubility |
| `kl` | pfas.dat | L nmol⁻¹ | Langmuir constant for **air–water interface** sorption (K_L) |
| `lm` | pfas.dat | nmol m⁻² | Langmuir maximum surface coverage at the air–water interface (Γ_max) |
| `percop` | pfas.dat | – (0–1) | how PFAS splits between percolation and runoff water |
| `sol_pfas` | pfas_hru.ini | kg ha⁻¹ | starting PFAS mass in each soil layer |
| `kf` | pfas_hru.ini | (nmol kg⁻¹)/(nM)ⁿ | **Freundlich** solid-phase sorption coefficient |
| `nf` (`n`) | pfas_hru.ini | – | Freundlich exponent (sorption non-linearity) |
| `d50` | pfas_hru.ini | mm | median grain diameter (sets the air–water interfacial area) |
| `enr` | pfas_hru.ini | – | enrichment ratio for PFAS leaving on eroded sediment |

The **air–water interfacial area** itself is computed, not entered:
`A_aw = 6 (1 − porosity)(1 − saturation) / d50`. This is why `d50` and soil
moisture matter — drier, finer soils hold more PFAS at air–water interfaces.

---

## Reading the output

After a run, these files appear in `TxtInOut`. Plain-language meaning:

### Surface water (the land and streams)
| File | What's in it |
|---|---|
| `pfas_hru_aa.txt` | per-field PFAS budget: `init_kgha` and `final_kgha` (soil PFAS start/end), and where it went — `surq_kgha` (surface runoff), `latq_kgha` (lateral flow), `perc_kgha` (**leached down toward groundwater**), `sed_kgha` (on eroded sediment), `resid_kgha` (left in soil). |
| `channel_pfas_day.txt` | daily PFAS concentration and load in each stream channel — the in-stream signal you compare to monitoring data. |
| `pfas_cha_balance.out` | a mass-balance check for the in-stream PFAS (in vs out vs stored). |

### Groundwater and the vadose (unsaturated) zone — MODFLOW 6 side
Inside `TxtInOut/mf6/`:
| File | What's in it |
|---|---|
| `pfas.ucn` | groundwater PFAS **concentration** in every aquifer cell, over time (open with a viewer or Python/flopy). |
| `pfas.lst` | the transport **mass budget**: how much PFAS entered (recharge/source), left (to streams), and is stored — including the **percent discrepancy** (should be near zero). |
| `MODFLOW_sfr.lst` | the groundwater **flow** budget, including the stream–aquifer exchange (recharge in, baseflow out). |

> Note on the vadose zone: in the standard setup PFAS reaches groundwater as a
> recharge source, and the deep unsaturated travel time is handled analytically
> (it is *long* — centuries for PFOS, much faster for short-chain PFAS like
> PFHxA). An explicit unsaturated-zone (UZF/UZT) build is an optional refinement.

### Surface ↔ groundwater interaction (the coupling itself)
The engine prints a summary at the end of the run (and you can save the screen
output to a file). It reports, over the whole run:
- **recharge** delivered from the land to groundwater,
- the **stream–aquifer exchange** — *gaining* (groundwater feeding streams,
  i.e. baseflow) and *losing* (streams leaking to the aquifer),
- **PFAS loaded** to the aquifer from the land, and
- **PFAS discharged** from groundwater back into the streams.

Those last two numbers **are the surface-water/groundwater PFAS exchange** — the
quantity this coupled model exists to compute. A real run ends like this:

```
 MF6 COUPLER summary over 91 coupled days:
   recharge (sum of daily basin depths) =   5.2015E+01 m
   SFR exchange: gaining   2.9579E+07  losing  -2.6348E+07 m3
   PFAS discharged to stream =   1.4780E+00 kg
 Execution successfully completed
```
(*gaining* = groundwater feeding streams; *losing* = streams leaking down; the
PFAS line is the groundwater contribution to the in-stream signal.)

And `pfas_hru_aa.txt` looks like this — each row is one field, columns are where
its soil PFAS went over the run:
```
hru  pfas  init_kgha    final_kgha   surq_kgha    latq_kgha    perc_kgha    sed_kgha     resid_kgha
  1     1  4.24941E-03  4.24941E-03  1.53459E-09  8.44545E-17  0.00000E+00  0.00000E+00  3.28058E-10
```
(here `perc_kgha`=0 means this PFAS did not leach to groundwater over the run — a
real result for strongly-sorbing PFOS on a short run; mobile compounds like PFHxA
show non-zero leaching.) The MODFLOW transport budget `mf6/pfas.lst` should report
`PERCENT DISCREPANCY` near `0.00` — that's your mass-balance check.

---

## File schemas — everything we add to `TxtInOut`

Beyond the standard SWAT⁺ and MODFLOW 6 files, the PFAS and coupling modules add
the files below. All are plain text, whitespace-delimited, free-format. Grouped as
**input**, **coupler**, and **output**.

### Input files (you provide)

**`pfas.dat`** — compounds; one row each, ended by `id=0` (`END`); two header lines.

| Field | Units | Meaning |
|---|---|---|
| `id` | – | compound number (1,2,…; 0 ends the list) |
| `name` | text(16) | compound name |
| `mw` | kg mol⁻¹ | molecular weight |
| `sol` | mg L⁻¹ | maximum aqueous solubility |
| `kl` | L nmol⁻¹ | Langmuir K_L (air–water interface) |
| `lm` | nmol m⁻² | Langmuir Γmax (air–water interface) |
| `percop` | – (0–1) | percolation/runoff split of mobile PFAS |

**`pfas_hru.ini`** — starting soil PFAS + sorption, one block per HRU (HRU order):
```
hru <id> nly <nlayers>            header for this HRU
<num_pconta>                      number of PFAS in this HRU
<d50_L1> <d50_L2> ...             grain size d50 per layer (mm)
<pid> <solpfas_L1> ...            starting soil PFAS per layer (kg/ha)  [1 line/PFAS]
<pid> <kf_L1> ...                 Freundlich kf per layer               [1 line/PFAS]
<pid> <nf_L1> ...                 Freundlich n  per layer               [1 line/PFAS]
<pid> <enr>                       sediment enrichment ratio             [1 line/PFAS]
```

**`pfas_calib.dat`** *(optional)* — one line `soil_scale koc_scale` (e.g. `0.11 1.0`);
missing → both 1.0. `soil_scale` scales the soil PFAS pool, `koc_scale` the in-stream sorption.

**`pfas_cha.dat`** *(optional)* — per-compound in-stream parameters; missing → defaults.
Columns: `id`, `name`(16), `koc` (m³ g⁻¹), `settle` (m d⁻¹), `resus` (m d⁻¹), `bury` (m d⁻¹), `act_dep` (m).

### Coupler files (link SWAT⁺ ↔ MODFLOW 6)

**`mf6.con`** — turns on MODFLOW 6; one value per line, `!` comments ignored:

| Line | Required | Meaning |
|---|---|---|
| 1 | yes | MODFLOW 6 folder, relative to `TxtInOut` (e.g. `./mf6`) |
| 2 | yes | groundwater FLOW step, days (1 = daily) |
| 3 | yes | groundwater TRANSPORT step, days (30 = monthly) |
| 4 | no | recharge multiplier (default 1.0) |
| 5 | no | full path to `libmf6` (default: system search path) |

The three **map** files (first line = header counts; each later line = one link):

| File | Header line | Each row |
|---|---|---|
| `mf6_recharge.map` | `N_ENTRIES N_CELLS NCOL N_HRU` | `cell_index hru weight` |
| `mf6_baseflow.map` | `N_LINKS N_REACHES` | `reach_index gis_channel` |
| `pfas_leach.map` | `N_ENTRIES N_SRCCELLS` | `src_index hru overlap_ha` |

- `cell_index = row*NCOL + col` (0-based, row-major, into MODFLOW's recharge array); `weight` = HRU–cell overlap ÷ cell area.
- `reach_index` = 0-based MODFLOW SFR reach; `gis_channel` = SWAT⁺ channel GIS id it discharges to.
- `src_index` = 0-based entry in the groundwater PFAS source list; `overlap_ha` = HRU–cell overlap (ha).

### Output files (the model writes)

| File | Columns / contents |
|---|---|
| `pfas_hru_aa.txt` | per-HRU soil-PFAS budget: `hru pfas init_kgha final_kgha surq_kgha latq_kgha perc_kgha sed_kgha resid_kgha` (kg ha⁻¹) |
| `pfas_balance.out` | basin land-phase PFAS mass balance (kg): per compound `init/final/surq/latq/perc/sed_kg` + max per-HRU closure residual |
| `channel_pfas_day.txt` | daily in-stream PFAS per channel: `jday mon day yr unit gis_id name pfas` then mass terms (kg) `tot_in sol_out sor_out settle resus diffuse bury water benthic` + `conc_ngL` (ng L⁻¹) |
| `pfas_cha_balance.out` | in-stream PFAS mass balance (cumulative kg): reach-days, point-source input, reach inflow/outflow, burial |

The MODFLOW 6 side (`mf6/pfas.ucn`, `mf6/pfas.lst`, `mf6/MODFLOW_sfr.lst`) uses
*standard* MODFLOW 6 formats and is not re-documented here.

## Quick troubleshooting
- **Nothing about MODFLOW in the output?** `mf6.con` is missing or misspelled, or
  it's not in `TxtInOut`. The engine silently runs plain SWAT⁺ without it.
- **No PFAS numbers?** `pfas.dat` is missing, or has no compound rows before `END`.
- **The model stops while reading a MODFLOW file?** A path in `mf6.con` is wrong,
  or the `mf6/` folder doesn't contain a valid `mfsim.nam`.
- **Big "percent discrepancy" in `pfas.lst`?** The transport step (line 3 of
  `mf6.con`) may be too long; reduce it.

---

*This guide covers how to run the model. The scientific basis, parameter sources,
and validation are in the accompanying paper.*

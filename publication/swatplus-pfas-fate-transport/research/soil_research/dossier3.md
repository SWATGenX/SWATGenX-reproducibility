There's also a directly relevant new USGS product (ACS PFAS background in soil). I have enough. Here is the deliverable.

---

# STREAM 3 DOSSIER — Biosolids Land-Application & Atmospheric Deposition as Initial-Soil-PFAS Loading Terms for SWAT+

Scope: the two **diffuse** soil-loading pathways (vs. point/contaminated sites covered elsewhere). For each I give the dataset, coverage, access method, the actual concentration/rate values, an automatability rating for "can SWATGenX pull it programmatically for any HUC," and the per-HRU translation. I distinguish **direct soil-concentration data** (ug/kg you can assign straight to an HRU) from **source/loading data** (you get a mass-loading rate and must run a simple accumulation model to get ug/kg).

A key framing point: **neither pathway has a national, gridded, ready-made soil-PFAS-concentration raster.** Biosolids gives you *where* sludge is applied + *how much* (a loading proxy); deposition gives you a *flux* (ng/m²/yr). Both feed an accumulation/mass-balance model to produce per-HRU initial ug/kg. The only thing close to a turnkey national soil-concentration surface is the **USGS anthropogenic-background soil PFAS** product (Stream-3-adjacent, listed at the end) — it implicitly bakes in both diffuse pathways and is the single most automatable layer.

---

## PART A — BIOSOLIDS LAND APPLICATION

### A.1 Datasets — WHERE biosolids are applied + HOW MUCH (source/loading data)

| Dataset | What it gives | Coverage | Access | Spatial granularity | Automatability |
|---|---|---|---|---|---|
| **EPA ECHO — Biosolids Annual Report download** (NeT-Biosolids / NETBIO, 2017–2024) | Per-facility annual **dry metric tons generated** and **dry metric tons land-applied** (plus tons to landfill/incineration/surface disposal); management practice code | National (all NPDES biosolids reporters, electronic since 31 Mar 2018) | Bulk CSV from `echo.epa.gov/tools/data-downloads` (Biosolids Annual Report file); also Biosolids Annual Report Search UI + ECHO REST web services | **Facility level** (treatment plant), with city/state/ZIP/county. NOT the application field. | **HIGH** for the tonnage; **LOW–MED** for spatially placing the application |
| **EPA ECHO — ICIS-NPDES Biosolids facility download** (5 CSVs: permits, violations, inspections, enforcement) | Permit + compliance metadata, facility city/state/ZIP/county | National | Same ECHO Data Downloads page; documented at `echo.epa.gov/tools/data-downloads/biosolids-download-summary` | Facility level. **No coordinates, no application-site locations, no application rates** | HIGH to pull, but it does **not** contain loading amounts — use the Annual Report file instead |
| **State biosolids land-application permits / site GIS** (e.g. MI EGLE, WI DNR, TX TCEQ NETBIO, OH, VA, WA) | Permitted application **field locations** (sometimes polygons/coordinates), approved agronomic rates | Per-state only; schemas differ | State open-data / ArcGIS REST portals; varies wildly | **Field level** where it exists | **LOW** nationally (per-state custom ingestion, like your MI EGLE PFAS pull). Good for high-value states, not CONUS-automatable |

**Critical gap (be explicit):** The federal data tells you a plant land-applied *X dry tons*, but **not the field it went to**. There is no national field-boundary layer for biosolids application. So national automation requires a **disaggregation rule**: distribute each facility's land-applied tonnage onto agricultural land within a service radius of the plant. Practical recipe:
- Take facility ZIP/county centroid (Annual Report) → buffer (literature median haul distance ~20–50 km, often county-bounded).
- Intersect buffer with **cropland/pasture** from the **USDA Cropland Data Layer (CDL, 30 m, national, annual, automatable WMS/download)** — biosolids go to ag land, not forest/urban.
- Allocate the dry-ton load proportionally to ag area within the buffer that overlaps each HRU.

This makes biosolids automatable for any HUC at a **statistical/expected-loading** resolution, which is the honest resolution of the federal data — not field-exact.

### A.2 PFAS concentrations IN biosolids (ng/g dry weight) — the source term

You need a concentration to multiply by the applied mass. Use these national values:

| Source | PFOS (ng/g dw) | PFOA (ng/g dw) | Notes |
|---|---|---|---|
| **EPA National Sewage Sludge Survey-era synthesis** (national mean) | mean ~**402** | mean **34 ± 22** | Other 10 PFAS each mean ~2–21 ng/g; basis for national load estimates |
| **EPA 2025 Draft Sewage Sludge Risk Assessment (PFOA/PFOS)** | modeled at **1 ppb = 1 ng/g** each | 1 ng/g | EPA explicitly calls 1 ng/g the **low end**; results **scale linearly** with concentration — convenient for parameterization |
| **Global/US literature range (biosolids)** | total PFAS **2.1 – 500,000 ng/g**; typical individual 0.6–84 ng/g; total ΣPFAS often ~70–340 ng/g | — | Use as uncertainty bounds |
| **MI EGLE regulatory threshold** | **100 ng/g** PFOS/PFOA = "industrially impacted," land-application banned | 100 | Useful upper-bound flag for routine (non-industrial) biosolids |

**Recommended default for SWATGenX:** ΣPFAS ~200–340 ng/g; PFOS ~100–400 ng/g, PFOA ~20–35 ng/g for typical municipal biosolids, with the 1 ng/g (EPA low) and 100+ ng/g (industrial) as scenario bounds.

### A.3 Soil concentrations OBSERVED after application (direct ug/kg — for validation/back-calibration)

| Study/site | Soil PFOS after application | Context |
|---|---|---|
| **Sepulvado et al. 2011** (Illinois reclamation, 32 yr consecutive application) | up to **483 ng/g (= 483 ug/kg)** PFOS | high cumulative loading endmember |
| **10 NE US farms (Sci. Reports 2025)** | mean ~**4.1 ug/kg** (ND to several ug/kg) | typical agronomic-rate farms |
| Class-B long-term studies | ND → low-single-digit to tens of ug/kg | most surface soil 96–97% mass unaccounted (leaching/runoff/plant) |

These let you **calibrate the accumulation model**: typical agronomic application → low single-digit ug/kg; decades of heavy reclamation loading → hundreds of ug/kg. This brackets Vahid's Huron-River biosolids field range (4–40 ug/kg PFOS) — consistent with agronomic-rate fields, on the higher side.

### A.4 Application-rate → soil-concentration translation (the per-HRU model)

Use a **mixing/mass-balance into the plow layer** (the same logic EPA's draft risk assessment uses — it scales linearly):

```
C_soil (ug/kg) = (C_bio (ng/g) × M_app (kg biosolids dry / m²)) 
                 / (ρ_bulk (kg/m³) × d_mix (m))                × accumulation_factor
```
- EPA modeling anchors: **10 and 50 dry t/ha/yr**, over **1 to 40 yr** (cumulative = rate × years × retention).
- d_mix ≈ 0.20 m tillage layer; ρ_bulk ≈ 1300 kg/m³ → soil mass ≈ 260 kg/m² in plow layer.
- Single 10 t/ha (=1 kg/m²) application of 300 ng/g biosolids → ~1.15 ug/kg increment; 40 yr → tens to ~hundreds ug/kg (matches Sepulvado), before accounting for the ~96% non-retention loss.
- Apply a **retention factor** (surface-soil retention ~ a few % to tens %; PFOS retained more than short-chain PFCAs) calibrated to the A.3 observed values.

**Per-HRU assignment:** flag HRU as biosolids-receiving if its land use ∈ {cropland, pasture} (CDL) **and** it falls in a facility service buffer; assign initial ug/kg = mass-balance result using the facility's reported land-applied tonnage allocated to that HRU's ag area. Non-ag HRUs get 0 from this pathway.

### A.5 Biosolids automatability verdict
- **Tonnage + management practice:** HIGH (national CSV/API, any HUC).
- **Concentration source term:** HIGH (literature constants, scenario-parameterized).
- **Spatial placement to HRU:** MEDIUM — requires the CDL + service-buffer disaggregation heuristic; not field-exact but fully scriptable and defensible. State field-polygon layers are LOW (per-state, optional enrichment for priority states like MI/WI/TX).

---

## PART B — ATMOSPHERIC DEPOSITION

### B.1 Datasets — deposition flux (loading data, ng/m²/yr)

| Dataset/source | What it gives | Coverage | Access | Automatability |
|---|---|---|---|---|
| **NADP-NTN PFAS (Wisconsin intensive study, Atmos. Env. 2022)** | Wet-deposition flux: **1.3–47.4 ng/m²/day (median 5.7)**; rain ΣPFAS 0.7–6.1 ng/L (median 1.5); PFCAs ~83% of mass | Measured at 8 WI NTN sites; **not yet a national PFAS product** | Paper values; NADP network (`nadp.slh.wisc.edu`) — PFAS not a routine national NADP analyte yet | **LOW** as data (point studies). Use as a **flux constant**, not a queryable layer |
| **Wilmington NC (ES&T Letters 2021)** | Annual flux **30 ug/m²/yr wet + 1.4 ug/m²/yr dry** (6 PFAS); dry 0.3–29 ng/m²/day | Single site (point-source-influenced, high end) | Paper | LOW; treat as elevated/near-source endmember |
| **Regional CMAQ-type deposition predictions (Sci. Total Environ. 2023, S0048969723048817)** | Modeled regional-scale PFAS atmospheric deposition + ambient air | Regional (grid model) | Paywalled paper; method = chemical transport model (CMAQ/CAMx class) | **LOW–MED**: a *method*, not a downloadable national raster. Could be reproduced but heavy |
| **NADP nitrogen/sulfur/mercury gridded deposition** | National gridded deposition surfaces (the analog product) | National | NADP downloads | HIGH — but **PFAS layer does not exist** yet; cited only as the template |

**Critical gap (be explicit):** There is **no published national gridded PFAS atmospheric-deposition raster** you can pull per HUC. What exists is a small set of measured fluxes converging on the same order of magnitude.

### B.2 Defensible national deposition values to use as a constant background term

- **Wet deposition (rural/background):** median ~**5.7 ng/m²/day ≈ ~2,000 ng/m²/yr ≈ ~2 ug/m²/yr** ΣPFAS (Wisconsin NTN). Range ~0.5–17 ug/m²/yr.
- **Dry deposition:** ~5–50% of wet in background settings (Wilmington dry ≈ 5% of wet).
- **Near-source/urban-industrial:** up to ~30 ug/m²/yr (Wilmington wet) — apply as an urban multiplier.
- Speciation: PFCAs (PFOA, PFBA, PFHxA, short-chains) dominate (~83% of deposited mass); PFOS a smaller fraction. This is the **opposite** of biosolids (PFOS-dominant) — keep species-resolved if the engine supports it.

### B.3 Deposition → per-HRU initial soil concentration

Deposition is a **diffuse background everywhere** (the term that fills HRUs with no point/biosolids source). Same plow-layer mixing:

```
C_soil (ug/kg) = (F_dep (ug/m²/yr) × T_accum (yr) × f_retained) 
                 / (ρ_bulk × d_mix)        [soil mass per m² ≈ 260 kg in 0.2 m]
```
- Background F_dep ≈ 2 ug/m²/yr ΣPFAS, accumulated over a deposition era (~50–70 yr since PFAS production ramp, ~1950s–present, peak ~1970s–2000s).
- Example: 2 ug/m²/yr × 60 yr × retention ~0.5 ÷ 260 kg/m² ≈ **0.23 ug/kg** ΣPFAS background in the plow layer. This lands squarely in Vahid's Huron-River "background-by-land-use urban 0.2–30 ug/kg" low end — internally consistent and a good sanity check.
- **Spatial modulation (automatable):** scale F_dep by an **urban/precipitation proxy** per HRU — use NLCD impervious/developed fraction (national, automatable) × PRISM precipitation (you already ingest PRISM). Wet deposition tracks rainfall; urban areas see higher flux. This turns a single constant into a per-HRU surface without a PFAS-specific raster.

### B.4 Deposition automatability verdict
- **As a uniform/precip-scaled background constant:** HIGH — one literature-anchored flux × your existing PRISM + NLCD layers, computable for any HUC.
- **As a measured/gridded national layer:** does not exist (LOW). Do not promise one; use the constant-with-proxy approach and cite the NADP-WI and Wilmington fluxes as the empirical anchor + uncertainty band.

---

## PART C — The one near-turnkey national SOIL-CONCENTRATION product (use as default/validation)

This is the single most automatable layer and it implicitly integrates **both** diffuse pathways — strongly recommend it as SWATGenX's default background initialization:

| Product | What it is | Coverage | Access | Automatability |
|---|---|---|---|---|
| **USGS — Anthropogenic Background PFAS in Soil** (ES&T 2025, `acs.est.5c16810`; USGS data release) | Modeled **background soil PFAS concentrations** (direct ug/kg-class), related to land use/lithology | Reported for regions, expanding (NE US shallow-soil predictions; CONUS methodology) | USGS data releases / data.usgs.gov; ScienceBase rasters | **MED–HIGH** (USGS rasters, scriptable; check CONUS coverage extent) |
| **USGS — National groundwater PFAS prediction (Science 2024, `ado6638`)** | 1×1 km CONUS XGBoost PFAS-occurrence raster; predictors include land use, septic N-loading, distance-to-source | **National, 1 km** | data.gov / data.usgs.gov / GAMA dashboard; full rasters + model object + code released | **HIGH** — fully downloadable national rasters; a deposition/source proxy even though it's groundwater-targeted |

The USGS soil-background product gives you a **direct ug/kg** value to drop into HRUs as the diffuse baseline (deposition + diffuse biosolids/urban), onto which you add the **explicit** biosolids (Part A) and contaminated-site (other stream) increments. That is the cleanest national architecture.

---

## Recommended SWATGenX initialization architecture (synthesis)

Per HRU initial soil PFAS (ug/kg) = **max or sum** of:
1. **Background** = USGS anthropogenic-background soil raster (HIGH automatability) — OR, where unavailable, the deposition mass-balance (~0.2–1 ug/kg ΣPFAS, precip/NLCD-scaled).
2. **Biosolids increment** (ag HRUs only) = ECHO Biosolids Annual Report land-applied tonnage → CDL service-buffer disaggregation → plow-layer mass balance with C_bio ~200–400 ng/g PFOS. (MED automatability.)
3. **Point/contaminated-site increment** = (other stream — PPC/AFFF/WWTP).

Freundlich kf/n: keep Li et al. 2019 per-soil-group values keyed to **gSSURGO soil group**, which SWATGenX already resolves per HRU — that part is already national and automatable.

**Honest bottom line on Stream 3:** Biosolids = automatable *loading* (federal tonnage, HIGH) but only statistical *placement* (MED, needs CDL buffering — no national field map). Atmospheric deposition = automatable only as a *literature-anchored, precip/urban-scaled constant* (~2 ug/m²/yr ΣPFAS background; no national gridded PFAS deposition raster exists). The genuinely turnkey national soil-*concentration* layer is the **USGS anthropogenic-background soil PFAS** product, which should be SWATGenX's diffuse default.

Sources:
- [ECHO Biosolids data download summary](https://echo.epa.gov/tools/data-downloads/biosolids-download-summary) · [ECHO Data Downloads](https://echo.epa.gov/tools/data-downloads) · [Biosolids Annual Report search help](https://echo.epa.gov/help/facility-search/biosolids-annual-report-search-results-help)
- [EPA Draft Sewage Sludge Risk Assessment FAQ (PFOA/PFOS)](https://www.epa.gov/biosolids/frequent-questions-and-answers-draft-sewage-sludge-risk-assessment-pfoa-and-pfos) · [EPA Sewage Sludge Surveys](https://epa.gov/biosolids/sewage-sludge-surveys)
- [ITRC Biosolids & PFAS Fact Sheet (2022)](https://pfas-1.itrcweb.org/wp-content/uploads/2022/10/Biosolids_PFAS_Fact_Sheet_102022_508.pdf) · [ITRC 2.6 PFAS Releases](https://pfas-1.itrcweb.org/2-6-pfas-releases-to-the-environment/)
- [PFAS in soils, 10 NE US farms (Sci. Reports 2025)](https://www.nature.com/articles/s41598-025-90184-z) · [Incidence of PFAS, long-term Class B biosolids (Sepulvado-class)](https://www.sciencedirect.com/science/article/abs/pii/S004896972103521X) · [PFAS in soil/groundwater after historical land application](https://www.sciencedirect.com/science/article/abs/pii/S004313542101229X)
- [NADP-NTN PFAS precipitation deposition, Wisconsin (Atmos. Env. 2022)](https://www.sciencedirect.com/science/article/abs/pii/S1352231022004332) · [Atmospheric deposition flux, Wilmington NC (ES&T Letters 2021)](https://pubs.acs.org/doi/abs/10.1021/acs.estlett.1c00251) · [Regional PFAS deposition predictions (STOTEN 2023)](https://www.sciencedirect.com/science/article/pii/S0048969723048817)
- [USGS national groundwater PFAS prediction, 1 km CONUS (data.gov)](https://catalog.data.gov/dataset/predictions-of-pfas-occurrence-in-groundwater-at-the-depth-of-drinking-water-supplies-in-t) · [Science 2024 paper](https://www.science.org/doi/10.1126/science.ado6638) · [USGS anthropogenic-background PFAS in soil (ES&T 2025)](https://pubs.acs.org/doi/10.1021/acs.est.5c16810)
- [Managing PFAS in Sewage Sludge review (PMC 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12387247/)
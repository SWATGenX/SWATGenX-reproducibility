I have sufficient material to compile the dossier. Let me synthesize.

---

# STREAM 4 DOSSIER — Source-Location Datasets → Soil-PFAS Hotspots (National, Automatable)

**Scope:** National source-location inventories that flag ELEVATED-soil-PFAS zones, programmatic access for any HUC, and — the critical gap — how to translate a source location into an initial soil concentration (ug/kg) + contaminated-site ratio. None of these are direct soil-concentration data; they are **proxies** requiring a concentration model. I pair them at the end with the one national *direct* soil-concentration product (USGS background) that anchors the low end.

## Key framing for the SWATGenX pipeline

A source location gives you **WHERE** elevated soil exists, not **HOW MUCH**. The translation has two parts:
1. **A buffer/footprint** around the point (how far does elevated soil extend) — literature supports ~0.5–1 mile for a presumptive zone (Salvatore used a uniform **1-mile buffer**), but actual soil enrichment is concentrated within the source pad (tens-to-hundreds of meters) and decays sharply.
2. **A concentration multiplier by source type** — this is what Rafiei's Huron model encoded implicitly (PPC 100–4000, biosolids 4–40, urban 0.2–30 ug/kg PFOS). To go national, you map each source-type to a soil-PFOS range and a "contaminated-site ratio" = source-zone conc / background conc.

Recommended source-type → initial soil PFOS (ug/kg) crosswalk synthesized from the literature below (use as SWATGenX default lookup, overridable):

| Source class (national layer) | Soil PFOS, source zone (ug/kg) | Ratio vs background | Footprint to apply |
|---|---|---|---|
| AFFF fire-training area (DoD / FAA Part 139 / industrial FTA) | 100–4,000 (total PFAS to ~530 in some FTAs; PFOS dominant) | 100–10,000× | source pad + ~100–300 m |
| PFAS manufacturer / fluorochemical industrial (TRI PFAS, FRS) | 50–4,000 (PPC-class) | 100–10,000× | facility footprint + ~0.5 mi |
| WWTP / biosolids land-application field | 4–40 (mean ~4.1; single-app up to ~30) | 10–100× | applied fields polygon |
| Landfill / waste transfer (TRI land releases) | 5–50 | 10–100× | cell + leachate downgradient |
| Urban / developed background (land-use class) | 0.2–30 | 1–30× | NLCD developed classes |
| Rural / undeveloped anthropogenic background | ~0.1–2 (USGS national) | 1× (baseline) | everywhere (floor) |

---

## STREAM 4 datasets — access, coverage, automatability

### 1. EPA PFAS Analytic Tools (hosted on ECHO)
- **What:** 12 consolidated national-scale layers including "Facilities Handling PFAS" (this is the ~120k FRS-derived facility set), CWA PFAS effluent dischargers, TRI PFAS, spills, federally-owned PFAS-investigation sites, waste transfers, and PFAS detections in environmental media.
- **Access:** UI at `https://echo.epa.gov/trends/pfas-tools`; underlying systems are programmatic. The "Facilities Handling PFAS" layer is FRS-backed → bulk CSV per state at `https://www.epa.gov/frs/epa-frs-facilities-state-single-file-csv-download`. ECHO Web Services (`echo.epa.gov/tools/web-services`) + ECHO map services give REST query by lat/long bbox. Metadata catalog: `https://echo.epa.gov/system/files/PFAS_Analytic_Tools_Metadata_2024-06-10.pdf`.
- **Coverage:** National (all states + DC).
- **Automatability:** HIGH for the FRS facility layer (per-state CSV, joinable to any HUC by point-in-polygon) and ECHO web services; MEDIUM for the bespoke PFAS-tool layers (some are download-on-click, not a clean REST endpoint).
- **Soil-conc translation:** None published in the tool itself — it is pure source location. It tells you facility TYPE (NAICS/SIC industry code), which is the lever: map fluorochemical/metal-plating/textile NAICS → industrial PPC range (50–4,000 ug/kg), others → lower.

### 2. EPA TRI — PFAS releases (Envirofacts REST API)
- **What:** 172 PFAS added to TRI by 2020 NDAA; reported releases (incl. **releases to land** — landfills, land treatment/application, surface impoundments) at ~21k facilities, reporting year 2020+.
- **Access:** **Envirofacts Data Service REST API — free, no auth, JSON/CSV/Parquet** (`https://www.epa.gov/enviro/envirofacts-data-service-api`). Query pattern: `https://data.epa.gov/efservice/<table>/<col>/<value>/rows/<start>:<end>`. TRI tables queryable; chemical metadata includes PFAS category flag. TRI Explorer PFAS list: `https://enviro.epa.gov/triexplorer/tri_text.list_chemical_pfas`.
- **Coverage:** National.
- **Automatability:** VERY HIGH — best programmatic story of the whole set (clean REST API, queryable by state/county/CAS, geocoded facilities).
- **Soil-conc translation:** TRI reports **release mass (lbs/yr) to land**, not soil concentration. This is actually richer than a point — you can convert land-release mass to an initial soil concentration with a simple mixing model: `C_soil (ug/kg) = released_mass × fraction_retained / (area × depth × bulk_density)`. That gives a physically-grounded per-facility number instead of a lookup. High value, but needs the mixing-model assumptions (retention fraction, mixing depth ~10–30 cm, bulk density ~1.3 g/cm³).

### 3. Salvatore et al. 2022 — Presumptive PFAS contamination (57,412 sites)
- **What:** 57,412 locations: 49,145 industrial facilities + 4,255 WWTPs + 3,493 current/former military sites + 519 major airports. Single integrated national map.
- **Method (translation-relevant):** **1-mile buffer** around each source = "presumptive contamination zone." NOTE: presumptive = proximity-based, **no measured concentration thresholds** assigned per site. So it gives footprint geometry + source class, not ug/kg.
- **Access:** Published in EST Letters (`https://pubs.acs.org/doi/10.1021/acs.estlett.2c00502`); public map at PFAS Project Lab (pfasproject.com); dataset also surfaced via PFAS-Central data hub (`https://pfascentral.org/data-hub/`). Underlying inputs are the same EPA TRI/FRS/DoD/FAA layers, so it is partly reproducible from primary sources.
- **Coverage:** National (50 states + DC).
- **Automatability:** MEDIUM — the published dataset is a one-time supplement (download + cache, not a live API); re-running their method from TRI/FRS/DoD/FAA primary layers is fully automatable and keeps it current.
- **Soil-conc translation:** Use their **source-class taxonomy** to drive the crosswalk table above; apply their 1-mile presumptive buffer for the "elevated zone" mask, but apply a sharper internal decay for the actual ug/kg (source pad high, edge → background).

### 4. DoD / military AFFF sites (+ EWG military map)
- **What:** DoD installations with known/suspected AFFF use; >300 bases with drinking-water PFAS; EWG mapped 206 military sites with measured contamination (`https://www.ewg.org/research/mapping-pfas-chemical-contamination-206-us-military-sites`).
- **Access:** DoD publishes installation PFAS-assessment lists (PDF/spreadsheet, periodic); EWG map is curated (scrape/download, not API). Locations also embedded in Salvatore military layer + EPA federal-sites layer.
- **Coverage:** National.
- **Automatability:** MEDIUM (DoD lists are tabular but irregular release cadence; geocoding to HUC is straightforward).
- **Soil-conc translation:** Strongest literature here. Fire-training areas are the dominant soil source on bases. Measured FTA soil totals: 3.4–531.7 ug/kg total PFAS (one FTA); to ~560 ng/g at another; sediments near Barksdale AFB up to 31.4 ng/g. PFAS persists at FTAs for ~century timescales. **Use AFFF-FTA = 100–4,000 ug/kg PFOS source-zone (top of the contaminated-site band), decaying to background within a few hundred meters.** This is the closest national analogue to Rafiei's PPC 100–4,000 ug/kg.

### 5. FAA Part 139 certificated airports (AFFF fire-training)
- **What:** ~500+ Part 139 airports historically required to use AFFF for fire suppression/training → airport fire-training areas are PFAS soil hotspots; this is Salvatore's 519-airport layer.
- **Access:** FAA publishes the Part 139 certificated-airport list (downloadable; `faa.gov`); also derivable from the NPIAS / airport facility data. Geocoded.
- **Coverage:** National.
- **Automatability:** HIGH (stable FAA list, clean geocoding).
- **Soil-conc translation:** Same AFFF/FTA basis as DoD (100–4,000 ug/kg in FTA, lower airfield-wide). Apply at airport-property polygon, concentrated at the ARFF/fire-training pad.

### 6. EWG PFAS contamination map (general)
- **What:** Curated national map of detections (water-centric, plus military/industrial). Useful for QC/cross-check, not as the primary soil driver.
- **Access:** `ewg.org` interactive map — scrape/manual download, no public API.
- **Coverage:** National.
- **Automatability:** LOW–MEDIUM (curated HTML; no clean endpoint).
- **Soil-conc translation:** Mostly water (ng/L), not soil. Use only as a hotspot cross-validation layer.

---

## The anchor you also need: national DIRECT soil-concentration product

To turn ratios into absolute ug/kg you need a **background floor**. The new national product:

- **USGS — Predicted anthropogenic background PFAS in soil, CONUS** (Env. Sci. Technol. 2025, `acs.est.5c16810`; "Predictions of Anthropogenic Background PFAS Concentrations in Soil and Relation to Bedrock Lithology and Groundwater Quality"). National modeled soil-PFAS surface tied to land use / bedrock lithology. USGS New England soil-PFAS prediction is the regional precursor. These ship as USGS data releases (ScienceBase, DOI-cited, downloadable rasters/tables) — the authoritative, automatable **background term** that every non-source HRU gets, and the denominator for your contaminated-site ratio. (Could not fetch the ACS full text — 403; pull the values + ScienceBase DOI from the USGS Science Data Catalog entry, which is open.)
- Biosolids/WWTP-applied-soil literature anchors that middle band: mean ~4.1 ug/kg after long-term Class B application, up to ~30 ug/kg single application; biosolids themselves 12–1,310 ug/kg.

---

## Bottom line for the SWATGenX pipeline

1. **Best programmatic spine:** EPA Envirofacts REST API (TRI, no auth, JSON/Parquet, queryable by state/county/CAS) + EPA FRS per-state CSV (the ~120k "Facilities Handling PFAS"). These two give you geocoded, NAICS-typed source points for any HUC, fully automatably. FAA Part 139 list adds airports cleanly.
2. **Footprint mask:** Salvatore 1-mile presumptive buffer for the "could-be-elevated" envelope; apply a sharper internal decay so only the source pad gets the top-band concentration.
3. **Concentration model (the real deliverable to build):** source-type → soil-PFOS lookup (table above), with TRI land-release mass converted to ug/kg via a soil-mixing model where mass data exist. Multiply background (USGS national soil product) by a source-class **contaminated-site ratio** (10–100× WWTP/biosolids/landfill; 100–10,000× AFFF-FTA/industrial PPC).
4. **Background floor everywhere:** USGS CONUS soil-PFAS prediction (ScienceBase data release) = the baseline every HRU starts from; developed NLCD classes get the 0.2–30 ug/kg urban bump even with no point source.
5. **Freundlich kf/n:** still from Li et al. 2019 per USDA soil group — join on gSSURGO (already in the SWATGenX stack), so this stays automatable.

**Automatability ranking:** TRI/Envirofacts (VERY HIGH) > FAA Part 139, FRS Facilities-Handling-PFAS, USGS soil-background (HIGH) > DoD lists, Salvatore dataset (MEDIUM) > EWG map (LOW).

**Key gap to flag:** no national dataset gives measured soil ug/kg at source locations — every Stream-4 layer is a proxy. The defensible, automatable path is source-class ratio × USGS national background floor, with TRI land-release mass→concentration mixing model where mass is reported.

Sources:
- [EPA PFAS Analytic Tools (ECHO)](https://echo.epa.gov/trends/pfas-tools) · [Metadata 2024](https://echo.epa.gov/system/files/PFAS_Analytic_Tools_Metadata_2024-06-10.pdf) · [FRS state CSV download](https://www.epa.gov/frs/epa-frs-facilities-state-single-file-csv-download)
- [EPA Envirofacts Data Service API](https://www.epa.gov/enviro/envirofacts-data-service-api) · [TRI PFAS chemical list](https://enviro.epa.gov/triexplorer/tri_text.list_chemical_pfas)
- [Salvatore et al. 2022, EST Letters](https://pubs.acs.org/doi/10.1021/acs.estlett.2c00502) · [PDF](https://www.akaction.org/wp-content/uploads/Salvatore-et-al_2022_Presumptive-Contamination-of-PFAS_ESTLetters-1.pdf) · [PFAS Central Data Hub](https://pfascentral.org/data-hub/)
- [EWG 206 military sites map](https://www.ewg.org/research/mapping-pfas-chemical-contamination-206-us-military-sites)
- [Centurial Persistence at Military Fire Training Sites, EST 2023](https://pubs.acs.org/doi/full/10.1021/acs.est.3c00675) · [Barksdale AFB sediment/water](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8917801/)
- [USGS national soil-background PFAS prediction, EST 2025](https://pubs.acs.org/doi/10.1021/acs.est.5c16810) · [USGS PFAS interagency workshop](https://pubs.usgs.gov/publication/ofr20251044/full)
- [PFAS in soil after biosolids land application](https://www.sciencedirect.com/science/article/abs/pii/S004313542101229X) · [Long-term Class B biosolids soil incidence](https://www.sciencedirect.com/science/article/abs/pii/S004896972103521X)
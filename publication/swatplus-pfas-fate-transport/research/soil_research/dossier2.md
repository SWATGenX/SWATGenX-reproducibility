I have comprehensive coverage. I have the key national/regional measured-soil datasets, the authoritative compilations with concrete ug/kg numbers, DOIs, and access methods. Compiling the dossier.

---

# STREAM 2 — MEASURED SOIL PFAS CONCENTRATION DATA (direct µg/kg)

Datasets reporting *measured* soil/sediment PFAS concentrations (or model-predicted concentrations derived from measurements) usable to assign per-HRU initial soil PFAS in SWATGenX. Distinguished from Stream 1 source-location proxies. PFOS/PFOA emphasized because those are what the SWAT+ PFAS engine and the Huron-River precedent track.

## A. Top-tier: directly usable, concrete µg/kg, programmatic access

### Table A1 — National / multi-state MEASURED soil datasets

| Dataset | Coverage | PFOS / PFOA soil conc. (µg/kg = ng/g) | Access / DOI | Automatability (per-HUC pull) |
|---|---|---|---|---|
| **Brusseau et al. 2020 compilation** "PFAS concentrations in soils: Background vs Contaminated" | Global, but US-heavy; **>30,000 samples / >2,500 sites**; classed as background / primary-source / secondary-source(biosolids) | **Background:** PFOS 0.003–162, PFOA 0.01–123.6; **median-of-max ≈ 2.7 each**. Primary-source (fire-training/AFFF, manufacturing) and biosolids sites orders of magnitude higher (PFOS into 10²–10³+). | Open-access PMC: PMC7654437. Tabular SI (Excel) of curated values. | **High as a lookup table** (one-time ingest of SI → background-by-class table). **Not** spatial/queryable per HUC by itself — use as the concentration-model parameter source. |
| **USGS predicted background soil PFAS — ME/VT/NH** (Smalling/Romanok et al., EST 2025, "Predictions of Anthropogenic Background PFAS in Soil…") | 3 states, **continuous prediction raster** (interpolated from field samples) | Reported as: ~73% of soils exceed NH PFOS soil-remediation standard, ~41% exceed PFOA std. Underlying field set (see A2): PFOS ND–5.4, PFOA ND–5.3; detected medians PFOS 0.37–0.94, PFOA 0.17–0.76. Predictor = **low soil pH** (most important), bedrock calcite, OC, atmospheric deposition. | **Data + model archive DOI 10.5066/P1K5IUJ6** (ScienceBase). Rasters downloadable. | **High within ME/VT/NH** — clip raster by HUC polygon, area-weight to HRU. The *method* (pH/lithology regression) is the template for a national background layer. |

### Table A2 — State / regional MEASURED soil field datasets (high-quality background, downloadable)

| Dataset | Coverage | n / media | PFOS / PFOA (µg/kg) | Access / DOI | Automatability |
|---|---|---|---|---|---|
| **USGS NH statewide shallow-soil survey, 2021** | New Hampshire, equal-area random grid, undisturbed land (forest/shrub/grass/wetland/barren), 500 m buffer from known sources | 100 sites shallow + 50 deeper + 6 full profiles to 36 in.; **36 PFAS** + TOPA, TOC, pH, moisture | PFAS detected at **every** site; NH detected medians ≈ PFOS 0.94, PFOA 0.76; max ≈ 5.4 / 5.3 | **DOI 10.5066/P9KG38B5**, ScienceBase. **Excel** (study data, QA/QC, data dictionary, soil descriptions) + JSON/ATOM/ISO. | **High** — clean CSV/XLSX with coordinates → point-in-HUC join; **ideal background/land-cover calibration set**. |
| **USGS NH confirmatory shallow-soil sampling, 2022** | NH | Confirmatory resample | Same magnitude band | **ScienceBase 63fe454c… / DOI 10.5066** (item page lists files) | High (same structure as above). |
| **Maine DEP / DACF PFAS soil investigation** | Maine statewide, **biosolids/sludge-impacted farm fields** (155 farms; 66 exceed conservative soil guideline) | Soil + groundwater + produce | Background study + impacted-field values (impacted ≫ background; many exceed agronomic soil screening levels). Maine background medians PFOS 0.37, PFOA 0.17. | **Maine PFAS Investigation Map** (ArcGIS web map; DEP results layer). Status report PDF (maine.gov/ifw). | **Medium** — ArcGIS REST endpoint behind the map is scriptable per-bbox/HUC, but schema is messy and many values are in PDFs. Best for the *biosolids/agricultural-impacted* class. |
| **MN PCA "PFAS ambient background concentrations"** (tdr-g1-25) | Minnesota statewide, urban vs non-urban | Background threshold values (BTVs) | Establishes urban vs non-urban BTVs; PFOS and PFDA statistically higher in urban (α=0.05). Numeric BTVs in the TDR. | PDF on pca.state.mn.us (binary, parse manually). | **Low-Medium** — values are in a report, not an API; one-time manual extraction → urban/non-urban background table. |

## B. SOURCE-LOCATION / LANDSCAPE PROXY data (NOT direct µg/kg — needs a concentration model)

These do **not** give soil concentration; they flag where soil is *likely* elevated. They belong to Stream 1 but are listed so they are not mistaken for measured data.

| Dataset | Coverage | What it gives | Access / DOI | Use |
|---|---|---|---|---|
| **USGS PFAS Reconnaissance Landscape Data** | **National** (US + PR + USVI) | EPA PFAS-facility counts, fire-affected/burn areas, land-cover within 5 km / 50 km buffers around tapwater sites. **No soil concentrations.** | **DOI 10.5066/P9JF1EXH**, ScienceBase, **two CSVs**. | Proxy weights for a national source-overlay; pair with a concentration model. |
| **USGS groundwater PFAS prediction (CONUS)** (Science 2024, ado6638) | **Conterminous US**, drinking-water-depth GW | Predicted GW PFAS occurrence rasters (not soil). | **DOI 10.5066/P93RXTKJ** + GAMA model archive. | Indirect: GW prediction correlates with source loading; a covariate, not soil conc. |

## C. Concentration-model parameters (the bridge from proxies → µg/kg)

For HRUs flagged only by source-location proxies (Stream 1), assign µg/kg using the **Brusseau 2020 class statistics** (Table A1) as the literature-anchored ranges, which align with the author's Huron-River PFOS bands and extend them nationally:

| Class | PFOS soil (µg/kg) | PFOA soil (µg/kg) | Source anchor |
|---|---|---|---|
| Remote / forest background | <0.1–0.5 | <0.1–0.4 | NH/ME field medians; global median ≈1.03 ng/g PFOS |
| Agricultural background | ~0.2–3 | ~0.1–2 | NH survey, MN non-urban BTV |
| Urban / suburban background | ~0.5–30 | ~0.3–10 | MN urban BTV; Huron urban 0.2–30 |
| Biosolids-applied fields (secondary source) | ~4–40+ | ~2–40 | Brusseau secondary; Huron biosolids 4–40 |
| Primary source (AFFF/fire-training, manufacturing — PPC) | ~100–4000 (up to 10²–10³⁴ tail) | ~50–1000+ | Brusseau primary; Huron PPC 100–4000 |

Freundlich kf/n per soil group: retain **Li et al. 2019** (as in the Huron paper); pair with USGS sorption-coefficient/soil-property releases (gNATSGO / STATSGO on ScienceBase, DOI 10.5066/... item 5fd7c19c) already used in SWATGenX for soil grouping.

## Recommended SWATGenX ingestion priority

1. **USGS NH statewide soil survey (10.5066/P9KG38B5)** + **Brusseau 2020 SI (PMC7654437)** — clean tabular, becomes the *background-by-land-cover concentration table* (one-time ingest, no per-HUC API needed). **Best automatability + best scientific anchor.**
2. **USGS ME/VT/NH predicted-background raster (10.5066/P1K5IUJ6)** — only spatially-continuous *measured-derived* soil PFAS layer; directly clip-by-HUC where it has coverage, and adopt its **pH/lithology regression as the national-background method** (the path to CONUS).
3. **Maine DEP ArcGIS REST** — scriptable per-HUC pull for the *biosolids/agricultural-impacted* high-concentration class.
4. National proxies (**10.5066/P9JF1EXH** landscape data) → feed the Table-C concentration model for any HUC outside the measured-data footprint.

**Key gap:** No single *queryable national MEASURED soil PFAS µg/kg* layer exists yet (the USGS 2024 Interagency Workshop, OFR 2025-1044, explicitly names the data-poor US interior as the priority). For CONUS coverage today, SWATGenX must combine measured tables (background-by-class) + the ME/VT/NH-style pH/lithology background model + source-location proxies, exactly the hybrid in Tables A–C.

Sources:
- [USGS NH statewide soil survey — ScienceBase 61f43d6c (DOI 10.5066/P9KG38B5)](https://www.sciencebase.gov/catalog/item/61f43d6cd34e622189bbb0c4)
- [USGS NH confirmatory soil sampling 2022 — ScienceBase 63fe454c](https://www.sciencebase.gov/catalog/item/63fe454cd34e176a2a34abc0)
- [Predictions of Anthropogenic Background PFAS in Soil — EST 2025 (data DOI 10.5066/P1K5IUJ6)](https://pubs.acs.org/doi/10.1021/acs.est.5c16810)
- [USGS news: predicts PFAS in shallow soils, northern New England](https://www.usgs.gov/centers/new-england-water-science-center/news/usgs-predicts-pfas-shallow-soils-throughout-northern)
- [Brusseau et al. 2020, background vs contaminated soils — PMC7654437](https://pmc.ncbi.nlm.nih.gov/articles/PMC7654437/)
- [ITRC media-specific occurrence (soil ranges, BTVs)](https://pfas-1.itrcweb.org/6-media-specific-occurrence/)
- [MN PCA PFAS ambient background concentrations (TDR-G1-25)](https://www.pca.state.mn.us/sites/default/files/tdr-g1-25.pdf)
- [USGS PFAS Reconnaissance Landscape Data — ScienceBase (DOI 10.5066/P9JF1EXH)](https://www.sciencebase.gov/catalog/item/63c6fdcad34e92aad3d120fe)
- [Maine status of PFAS soil & groundwater investigation 2025](https://www.maine.gov/ifw/docs/PFAS%20Soil%20and%20Groundwater%20Investigation%20Report%202025%20FINAL.pdf)
- [USGS 2024 PFAS Interagency Workshop — OFR 2025-1044](https://pubs.usgs.gov/publication/ofr20251044/full)
- [USGS CONUS groundwater PFAS prediction — Science 2024 (data DOI 10.5066/P93RXTKJ)](https://www.science.org/doi/10.1126/science.ado6638)
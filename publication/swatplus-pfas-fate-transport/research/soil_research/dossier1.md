I now have the complete ground-truth method including Table 1 (the canonical source-to-concentration lookup). I have everything needed for STREAM 1. The supplementary text I read does not contain the Li et al. 2019 numeric kf/n by soil group (those live in Table S1/S2 figures not in the txt), but the paper cites the source precisely. Here is the deliverable.

---

# DOSSIER — STREAM 1: The Water Research Paper's Initial-Soil-PFAS Method (Ground Truth)

**Source:** Rafiei, V. & Nejadhashemi, A.P. (2023). *Watershed Scale PFAS Fate and Transport Model for Source Identification and Management Implications.* Water Research (Elsevier, S0043135423005092). SMR-W = SWAT-MODFLOW-RT3D. Huron River watershed, SE Michigan, 2,292 km², 189 subbasins, **9,451 HRUs**.

This is the template the national pipeline must generalize. The whole approach is: **assign each HRU a representative initial PFOS soil concentration (ug/kg) by a land-use / source-overlay classification, then let calibration tune within those ranges.** PFOS only (as a long-chain proxy). Three years warm-up (1999–2001 stated as "1999-2021 warm-up"; actually first 3 yrs) lets the soil profile reach dynamic equilibrium.

## 1. Source categories and assigned initial soil PFOS concentration (ug/kg)

This is **Table 1** of the paper — the canonical lookup. Concentrations are *ranges*; calibration (MMPSO, 54 soil-concentration parameters) selects the operative value within each range.

| Category | # HRUs | Total area (ha) | % watershed | **Representative PFOS soil conc. (ug/kg)** | Concentration source cited |
|---|---|---|---|---|---|
| **PPC sites** (Potential PFAS Contamination — confirmed + suspected) | 148 | 176 | 0.08 | **100 – 4000** | LimnoTech (2021) site soil reports; Adamson et al. (2021); Brusseau et al. (2020) |
| **Biosolids sites** (agricultural HRUs receiving biosolids) | 160 | 1,540 | 0.67 | **4 – 40** | Pepper et al. (2021); Johnson (2022) |
| **Urban** (background, indirect) | 2,791 | 72,537 | 31.65 | **0.2 – 30** (text) / 0.2 – 30 (Table 1) | Xiao et al. (2015) — surficial soil, US metro |
| **Pasture** | 1,865 | 22,316 | 9.74 | **0.2 – 8** | (background-by-land-use) |
| **Agriculture** (non-biosolids) | 498 | 29,869 | 13.03 | **0.2 – 8** | (background-by-land-use) |
| **Natural lands** (forest, wetland) | 4,024 | 102,760 | 44.83 | **0.005 – 0.01** | Rankin et al. (2016) — surficial soil, no apparent human presence |

Note the body text quotes urban as "0.20 to 40.00 ug/kg" while Table 1 lists "0.2 to 30" — a minor internal inconsistency; Table 1 is the authoritative machine-readable version. PPC body text range = 100–4000 ug/kg, consistent with Table 1.

Biosolids note: PFOS in MI biosolids statewide ranges **<0.97 to 2150 ug/kg** (EGLE 2022a), application rates **6,725–26,900 kg/ha**. The Wixom outlier (~2,150 ug/kg) was excluded (land application ceased 2018). They settled on **6,725–13,450 kg/ha/year** at **6.0–24.0 ug/kg** PFOS for the representative biosolids application.

## 2. How each HRU got its value (the assignment logic)

HRUs = homogeneous land use × soil × topography units within subbasins. Classification into the 3 conceptual groups + 6 reporting categories:

1. **PPC sites — site overlay.** HRUs were selected whose location coincides with confirmed/suspected PFAS sites (Figure 2 point layer). To bound load, each PPC HRU was **size-clamped to 0.5–1.3 ha** (per Adamson et al. 2021 AFFF-site characterization). 148 sites → 176 ha total. This is a **spatial intersection of HRU polygons with a point/site layer**, not distance-weighted.
2. **Biosolids sites — site overlay on agricultural HRUs.** Agricultural HRUs intersecting biosolids permitting/compliance locations (EGLE MiWaters). Size-clamped to **10–100 ha** (min/max farmland size in watershed). 160 sites → 1,540 ha (2.8% of ag+pasture). Implemented as an actual **biosolids application event** in selected croplands (not just an initial concentration — see engine task list).
3. **Background by land use — lookup table.** Every remaining HRU got its initial PFOS by a **land-use class → concentration-range lookup** (urban / pasture / agriculture / natural). No site overlay, no distance. These represent indirect impact (wind erosion, wet deposition, irrigation).

There is **no distance-decay function** in the initial-condition assignment. Distance/overlay is binary (HRU is or isn't a site). Spatial gradients emerge from transport, not from the IC.

## 3. Freundlich kf and n by soil group (Li et al. 2019)

The Freundlich isotherm `Cs = kf · C^n` governs water-solid adsorption (Eq. 2). Csolid in M/M, kf in (M/M)/(M/L³)^n, n dimensionless.

- **Source:** **Li, F., Fang, X., Zhou, Z., Liao, X., Zou, J., Yuan, B., Sun, W., 2019. Adsorption of perfluorinated acids onto soils: Kinetics, isotherms, and influences of soil properties. Science of The Total Environment 649, 504–514. https://doi.org/10.1016/J.SCITOTENV.2018.08.209** — this paper measured/validated kf and n for PFOS across **six soils** of distinct physicochemical properties.
- **How the paper mapped them:** The Huron NRCS/gSSURGO soil database had **18 soil profiles, up to 4 layers each, ~1500 mm to A-horizon depth**. They examined each soil layer's **organic carbon** (Figure S1.a) and **texture** (Table S1), then **classified each layer into one of the six Li et al. (2019) soil groups** whose properties most closely resemble it. Each group carries its Li-derived kf and n (supplementary Table S2). Figures S1.c/S1.d show the resulting spatial average initial kf and n across the watershed.
- **Calibration handling:** kf was allowed to vary **±30% of the Li-derived initial value**, with **54 kf calibration parameters** (mirroring the 54 soil-concentration parameters, across the 9 calibration regions × 5 land uses, applied to surface / bottom / profile-average layers).

**Numeric kf/n per soil group are NOT in the supplementary .txt I was given** (Tables S1/S2 are referenced as figures/tables not present in the plain-text supplement). To populate them you must pull the actual values from **Li et al. 2019, STOTEN 649:504-514** (the six-soil isotherm table) — that paper is the authoritative numeric source and must be obtained directly. The pipeline implication: kf/n is **not assigned from a PFAS dataset at all — it is derived from soil texture + organic carbon** (which SWATGenX already has nationally via gSSURGO), by analogy-matching to the Li et al. six reference soils.

## 4. Every data source cited for the soil-PFAS inputs (with enough detail to find)

### Source-LOCATION layers (proxies → imply elevated soil; need a concentration model)
| Source | What it provides | Access (as cited) | Coverage |
|---|---|---|---|
| **EGLE Michigan PFAS Sites** (2022d) | Confirmed PFAS sites (GW well exceeds MI 7 cleanup criteria) | https://gis-egle.hub.arcgis.com/datasets/michigan-pfas-sites/ | Michigan |
| **USEPA PFAS Analytic Tools / ECHO** (2021) | Facilities in industries that may handle PFAS (148 in watershed: chem mfg, metal coating, plastics, airports…) → suspected sites | https://echo.epa.gov/trends/pfas-tools | **National** |
| **EGLE MiWaters** (2022c) | Biosolids permitting & compliance reports (>160 application sites) | https://miwaters.deq.state.mi.us/nsite/map/ | Michigan |
| **EGLE PFAS surface water sampling** (2022b) | River/SW PFAS sample points (ArcGIS Hub) | https://gis-egle.hub.arcgis.com/datasets/egle::pfas-surface-water-sampling/ | Michigan |
| **EGLE PFAS public water supply sampling** (2022e) | PWS PFAS (hexbins — coords withheld for privacy → unusable for siting) | https://gis-egle.hub.arcgis.com/datasets/egle::public-water-supply-sampling-hexbins/ | Michigan |
| **EGLE WWTP/IPP effluent & biosolids field reports** (2021a, 2021b, 2020) | WWTP effluent PFOS conc + flow (Table 2); biosolids PFOS | Statewide WWTP & biosolids PFAS field reports summary | Michigan |
| **EGLE Huron River investigation** (2019) | Watershed-specific PFAS occurrence/source narrative | https://www.michigan.gov/pfasresponse/investigations/lakes-and-streams/huron-river | Local |

### Soil-CONCENTRATION literature (direct ug/kg ranges → the lookup values)
| Source | Provides | Value used |
|---|---|---|
| **LimnoTech (2021)**, *PFAS Investigation Phase 1 Report, Willow Run Airport (YIP)* | Site soil-sample PFOS reports | Anchors PPC 100–4000 ug/kg |
| **Adamson, D.T. et al. (2021/2022)**, Environmental Advances 7:100167, *Characterization of relevant site-specific PFAS fate and transport processes at multiple AFFF sites* | AFFF-site soil characterization + site-size bounds | PPC range + 0.5–1.3 ha clamp |
| **Brusseau, M.L., Anderson, R.H., Guo, B. (2020)**, STOTEN 740:140017, *PFAS concentrations in soils: Background levels versus contaminated sites* | Background vs contaminated soil PFAS national synthesis | Supports PPC + background split |
| **Xiao, F., Simcik, M.F., Halbach, T.R., Gulliver, J.S. (2015)**, Water Research 72:64-74, *PFOS and PFOA in soils and groundwater of a US metropolitan area* | Urban surficial soil PFOS | Urban 0.2–30(40) ug/kg |
| **Rankin, K., Mabury, S.A. et al. (2016)**, Chemosphere 161:333-341, *A North American and global survey of perfluoroalkyl substances in surface soils* | Background surface soil in areas with no apparent human presence | Natural lands 0.005–0.01 ug/kg |
| **Pepper, I.L. et al. (2021)**, STOTEN 793:148449, *Incidence of PFAS in soil following long-term application of Class B biosolids* | Biosolids-amended soil PFOS | Biosolids 4–40 ug/kg |
| **Johnson, G.R. (2022)**, Water Research 211:118035, *PFAS in soil and groundwater following historical land application of biosolids* | Biosolids-amended soil/GW | Biosolids 4–40 ug/kg |
| **Li, F. et al. (2019)**, STOTEN 649:504-514 | Freundlich kf, n for PFOS in 6 soils | kf/n by soil group |

### NRCS soils (the kf/n driver — already national in SWATGenX)
- **NRCS gSSURGO** (2021), *Gridded Soil Survey Geographic*, http://datagateway.nrcs.usda.gov/ — organic carbon + texture per layer → six-group classification → kf/n. **National coverage.**

### In-stream/lake initial PFOS (Table 3, not soil but completes the IC picture)
Initial PFOS in river/lake water = 2.1 ug/l (EGLE 2022b); initial PFOS in sediment = 710 ug/kg (Balgooyen & Remucal 2022); kd = 0.00015 m³/g (Mussabek et al. 2019).

## 5. Enrichment / contaminated-site-ratio handling

There is **no multiplicative enrichment ratio** applied to soil concentrations. The handling is:
- **Range + calibration, not a fixed enrichment factor.** Each category is a *range*; MMPSO picks the operative concentration within it (the actual calibrated values reported: PPC 3,700 ug/kg and urban 40 ug/kg in the heavily-urbanized sub-watershed; biosolids 4 ug/kg in the agriculture-dominated sub-watershed). So "enrichment" is expressed as the gap between the natural-lands floor (0.005–0.01) and PPC ceiling (4000) — a ~10⁵–10⁶× span across categories.
- **Area clamping** is the load-control analog of enrichment: PPC HRUs clamped 0.5–1.3 ha, biosolids 10–100 ha, so a hot concentration is confined to a realistic footprint.
- **WWTP point-source decay:** Wixom WWTP daily PFOS load **divided by 10 after 2019** (90% IPP-driven reduction); loads = median effluent conc × flow (Table 2).
- **Biosolids as a flux, not just an IC:** biosolids enter as an annual application **event** (6,725–13,450 kg/ha/yr × 6–24 ug/kg), calibrated 200–400 mg/ha/year application range — i.e. ongoing loading, distinct from a one-time initial concentration.

---

## Implications for the national pipeline (concise)

- **Two data classes confirmed:** (a) **direct soil-concentration** = literature ranges keyed to land use/source type (Brusseau 2020, Xiao 2015, Rankin 2016, Pepper 2021, Johnson 2022, Adamson 2021 + local site reports like LimnoTech); (b) **source-location proxies** = point/polygon layers (EPA ECHO/PFAS Analytic Tools = the ONLY national one cited; EGLE = MI-only) that must be intersected with HRUs then assigned a concentration *range* from class (a).
- **The single national source the paper itself used = EPA PFAS Analytic Tools / ECHO** (facilities that may handle PFAS). Everything else (EGLE sites, MiWaters biosolids, WWTP reports) is Michigan-specific and has a **state-by-state analog problem** for CONUS automation.
- **kf/n needs no PFAS dataset** — it is fully derivable from gSSURGO (organic carbon + texture) by matching to the 6 Li et al. 2019 reference soils. SWATGenX already ingests gSSURGO nationally, so kf/n initialization is the most automatable piece. **Action: extract the 6-soil kf/n table from Li et al. 2019 STOTEN 649:504-514 directly — it is not in the provided supplement.**
- **The assignment is a per-HRU land-use lookup + binary site overlay + area clamp**, then ranges → calibration. No distance decay, no enrichment multiplier. A national pipeline can replicate this exactly: classify HRU → assign concentration range → overlay national source layer (ECHO + biosolids + AFFF/MIL inventories) → clamp footprint → hand ranges to calibration.

Paper PDF: `/data/SWATGenXApp/codes/_temp/swat-modflow-pfas-paper/Water_research_PFAS_Fate_and_Transport_manuscript.pdf` (Table 1 p.31-equiv, Methods §2.5–2.6 pp.8-11). Supplement: `/data/SWATGenXApp/codes/_temp/swat-modflow-pfas-paper/Supplementary_Materials_v3.txt` (Tables S1/S2 with numeric kf/n are referenced but NOT present in this plain-text file).
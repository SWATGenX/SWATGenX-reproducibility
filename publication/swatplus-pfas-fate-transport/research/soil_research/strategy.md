I'll synthesize this now. The four dossiers are comprehensive and self-consistent. Let me produce the decision-grade strategy directly.

---

# SOIL-PFAS INITIALIZATION STRATEGY for the SWATGenX Pipeline

**Scope:** Per-HRU, per-soil-layer initial soil PFOS (ug/kg) + Freundlich kf/n for any CONUS watershed, generalizing the Huron-River method (Rafiei & Nejadhashemi 2023, *Water Research*) to national automatable data. Honest framing up front: **no national queryable measured-soil-PFAS layer exists** (Dossier 2 §C; Dossier 4 key gap; USGS OFR 2025-1044 names the data-poor interior as the priority). The defensible architecture is therefore exactly the paper's: **classify HRU → assign a literature-anchored concentration RANGE → overlay national source layers → clamp footprint → hand ranges to MMPSO calibration.** kf/n is the one piece that needs no PFAS data at all.

---

## 1. TIERED DATA STRATEGY (land/source category → best national dataset → defensible ug/kg)

The architecture is **layered, not exclusive** (Dossier 3 synthesis): every HRU gets a **background floor**, then **additive increments** for biosolids and source-proximity. Within each category, the value is a *range* handed to calibration, never a fixed number (Dossier 1 §1, §5).

### Tier 0 — Background floor (every HRU, national)
| Best dataset | Automatability | Value (PFOS ug/kg) | Citation |
|---|---|---|---|
| **USGS Anthropogenic-Background PFAS in Soil** (EST 2025, `acs.est.5c16810`; ScienceBase data release) — modeled soil-PFAS surface tied to land use + bedrock lithology + pH | MED–HIGH (USGS rasters, clip-by-HUC where covered; CONUS extent must be verified) | direct ug/kg; NE-US field anchor PFOS detected-median **0.37–0.94**, max ~5.4 | Dossier 2 Table A1; Dossier 3 Part C; Dossier 4 anchor |
| **Fallback where raster absent:** deposition mass-balance, precip/NLCD-scaled | HIGH (uses PRISM + NLCD you already ingest) | ~**0.2–1** ΣPFAS (≈0.23 worked example) | Dossier 3 §B.3 |

### Tier 1 — Background-by-land-use (the paper's lookup, nationalized)
Anchored to **Brusseau et al. 2020** (PMC7654437, >30k samples) + USGS NH survey (DOI 10.5066/P9KG38B5) + MN PCA urban/non-urban BTVs:

| Category | PFOS soil (ug/kg) | Citation |
|---|---|---|
| **Forest / remote / natural** | **0.005–0.5** (paper used 0.005–0.01; field medians push to ~0.5) | Rankin 2016; NH/ME field medians (Dossier 2 Table C) |
| **Agricultural (non-biosolids) / pasture** | **0.2–8** (paper); 0.2–3 from NH/MN | Dossier 1 Table 1; Dossier 2 Table C |
| **Urban / developed background** | **0.2–30** (Table 1 authoritative; body text says 40) | Xiao 2015; MN urban BTV (Dossier 1 §1; Dossier 2 Table C) |

Land-use class from **NLCD** (national, automatable) — developed classes → urban; CDL cropland/pasture → ag.

### Tier 2 — Biosolids fields (additive, ag HRUs only)
| Best dataset | Automatability | Value | Citation |
|---|---|---|---|
| **EPA ECHO Biosolids Annual Report** (NETBIO, CSV/REST) — dry-tons land-applied per facility | HIGH for tonnage; MED for placement (no national field map → CDL service-buffer disaggregation) | soil **4–40 ug/kg** PFOS (paper); validated by 10-NE-farms mean ~4.1, Sepulvado endmember 483 | Dossier 3 Part A; Dossier 1 Table 1 |
| Biosolids source term | — | C_bio **100–400 ng/g** PFOS typical municipal (EPA NSSS mean ~402); 1 ng/g EPA low / 100 ng/g MI "industrial" bounds | Dossier 3 §A.2 |

### Tier 3 — Contaminated-site / AFFF / industrial (additive, source overlay) — "PPC"
| Best NATIONAL dataset | Automatability | Value (PFOS ug/kg) | Citation |
|---|---|---|---|
| **EPA Envirofacts TRI REST API** (172 PFAS, releases-to-land, geocoded, no auth) | **VERY HIGH** | source-zone **50–4,000**; or compute from land-release mass via mixing model | Dossier 4 §2 |
| **EPA FRS "Facilities Handling PFAS"** (per-state CSV, NAICS-typed, ~120k) — the ONE national layer the paper itself used (via PFAS Analytic Tools/ECHO) | HIGH | **100–4,000** for fluorochem/metal-plating NAICS | Dossier 1 §4; Dossier 4 §1 |
| **FAA Part 139 airports** (~500+, AFFF fire-training) | HIGH | FTA **100–4,000** | Dossier 4 §5 |
| **DoD AFFF installations** / EWG 206 military | MED | FTA **100–4,000** (measured FTA totals 3.4–531.7); centurial persistence | Dossier 4 §4 |
| **Salvatore 2022** (57,412 presumptive sites; 1-mile buffer) — footprint mask + source taxonomy | MED (cached supplement; reproducible from TRI/FRS/DoD/FAA) | provides geometry + class, not ug/kg | Dossier 4 §3 |

This reproduces the paper's PPC **100–4,000 ug/kg** (Dossier 1 Table 1) nationally.

---

## 2. PER-HRU ASSIGNMENT ALGORITHM (generalization of the Huron method)

The paper's logic is **binary site overlay + land-use lookup + area clamp + ranges→calibration; NO distance decay, NO multiplicative enrichment factor** (Dossier 1 §2, §5). Generalized:

```
For each HRU h (polygon) with land-use LU, soil S, in subbasin:

  # --- Tier 0: background floor (always) ---
  C_bg = USGS_background_raster.clip(h).area_weighted_mean()
         if raster covers h
         else deposition_massbalance(PRISM_precip[h], NLCD_dev_frac[h])   # ~0.2–1 ug/kg

  # --- Tier 1: land-use floor (take the higher of bg and LU floor) ---
  C_lu = LANDUSE_LOOKUP[classify_NLCD_CDL(LU)]      # forest / ag / urban range (low end)
  C0   = max(C_bg, C_lu.low)

  # --- Tier 2: biosolids increment (ag HRUs only) ---
  if LU in {cropland, pasture} and h ∈ facility_service_buffer(ECHO_NETBIO):
      C_bio_inc = plow_layer_massbalance(
                     tonnage_allocated_to_h_by_ag_area,   # CDL disaggregation
                     C_bio=100..400 ng/g, d_mix=0.20 m, ρ=1300 kg/m³, retention_f)
      C0 += C_bio_inc
      tag h = "biosolids"; clamp_area(h, 10..100 ha)      # paper's farmland clamp

  # --- Tier 3: contaminated-site overlay (binary intersection) ---
  if h intersects PPC_layer (TRI∪FRS-PFAS∪FAA139∪DoD, NAICS-typed):
      C0 = PPC_RANGE_by_class[class]      # 100–4000; OVERRIDE, not add (it dominates)
      tag h = "PPC"; clamp_area(h, 0.5..1.3 ha)           # paper's AFFF clamp

  # --- emit RANGE to calibration, per soil layer ---
  assign_initial_PFOS(h, layer) = depth_profile(C0_range)  # surface > bottom
```

**Contaminated-site ratio (the explicit generalization the paper left implicit):** the paper has no enrichment multiplier — "enrichment" is the ~10⁵–10⁶× gap between the natural floor (0.005) and PPC ceiling (4,000) plus area-clamping (Dossier 1 §5). For the national pipeline make the ratio **explicit and source-class-keyed** (Dossier 4 crosswalk), applied as `C_zone = ratio × C_background_floor` ONLY where you lack an absolute literature range, otherwise use the absolute range directly:

| Source class | ratio vs background | absolute PFOS (ug/kg) |
|---|---|---|
| AFFF FTA / fluorochem industrial | 100–10,000× | 100–4,000 |
| WWTP / biosolids / landfill | 10–100× | 4–50 |
| Urban developed | 1–30× | 0.2–30 |
| Rural background | 1× (baseline) | 0.1–2 |

**Footprint handling:** keep the paper's **binary overlay + area clamp** as the default (most defensible, matches ground truth). Salvatore's 1-mile buffer is the *candidate-zone mask*; apply the hot concentration only to the source-pad-clamped HRU area, not the whole mile (Dossier 4 §3, framing). No distance-decay function in the IC — gradients emerge from transport (Dossier 1 §2).

**Depth profile:** surface layer gets the assigned C0; deeper layers attenuate (paper applied surface/bottom/profile-average parameters across 4 layers to ~1500 mm; Dossier 1 §3). First cut: surface = C0, each deeper layer × 0.3–0.5, calibration-tunable.

---

## 3. FREUNDLICH kf/n ASSIGNMENT (no PFAS data needed — gSSURGO-driven)

`Cs = kf · C^n` (Eq. 2). This is the **most automatable piece** — derived entirely from soil texture + organic carbon, which SWATGenX already ingests nationally via gSSURGO (Dossier 1 §3, bottom line).

**Method (exact paper procedure, Dossier 1 §3):**
1. For each HRU soil layer, pull **organic carbon + texture** from gSSURGO (already per-HRU in the stack).
2. **Classify the layer into one of the six Li et al. 2019 reference soils** whose OC + texture most closely match (analogy-matching, nearest-neighbor on OC and clay/sand fraction).
3. Assign that reference soil's **kf and n** (PFOS isotherm values).
4. Calibration: allow kf to vary **±30%** of the Li-derived value; 54 kf parameters mirroring the 54 concentration parameters across calibration regions × land uses × layers.

**CRITICAL ACTION / GAP:** the numeric six-soil kf/n table is **NOT in the supplied supplement** (Tables S1/S2 are figures, absent from the plain-text). You MUST extract the six (kf, n) pairs directly from **Li, F. et al. 2019, STOTEN 649:504–514, https://doi.org/10.1016/j.scitotenv.2018.08.209** (the isotherm table). Until obtained, seed with a literature placeholder (PFOS log-Koc-derived kf ordered by OC) and flag as provisional. This is the single hard blocker for kf/n and it is a one-paper fetch, not a data-pipeline problem.

---

## 4. AUTOMATABILITY VERDICT per dataset + GAPS

| Dataset | API/Download/GIS | National? | Verdict |
|---|---|---|---|
| **gSSURGO** (kf/n + soil layers) | already ingested | Yes | **TURNKEY** — already in SWATGenX |
| **EPA Envirofacts TRI** (PFAS land releases) | REST, no auth, JSON/Parquet, by state/county/CAS | Yes | **VERY HIGH** — best programmatic spine (Dossier 4 §2) |
| **EPA FRS Facilities-Handling-PFAS** | per-state CSV, point-in-poly | Yes | **HIGH** — the one national source the paper used (Dossier 1 §4) |
| **FAA Part 139 airports** | stable list, geocoded | Yes | **HIGH** (Dossier 4 §5) |
| **NLCD / CDL** (land-use classify + biosolids placement) | WMS/download | Yes | **HIGH** — already used |
| **ECHO Biosolids Annual Report** (tonnage) | CSV/REST | Yes | **HIGH for tonnage; MED for placement** — no national field map → CDL service-buffer heuristic (Dossier 3 §A.1) |
| **USGS Background-Soil raster** | ScienceBase raster | Partial CONUS (verify extent) | **MED–HIGH** — clip-by-HUC; the only direct-ug/kg national-ish surface (Dossier 3 §C) |
| **USGS ME/VT/NH predicted-background** (DOI 10.5066/P1K5IUJ6) | ScienceBase raster | 3 states | HIGH in-footprint; **method = national template** (pH/lithology regression) |
| **USGS NH survey** (DOI 10.5066/P9KG38B5) + **Brusseau SI** (PMC7654437) | XLSX/CSV | regional / compilation | **HIGH as lookup-table ingest** (becomes background-by-class table) |
| **DoD AFFF lists / EWG** | irregular tabular / scrape | Yes | **MED** |
| **Salvatore 2022** | cached supplement; reproducible from primaries | Yes | **MED** |
| **State PFAS/biosolids GIS** (MI EGLE, ME DEP, WI, TX) | per-state ArcGIS REST | per-state only | **LOW nationally** — optional enrichment for priority states; the state-by-state analog problem (Dossier 1 implications) |
| **Atmospheric deposition** | point studies only | No gridded product | **LOW as data; HIGH as precip/NLCD-scaled constant** (~2 ug/m²/yr ΣPFAS) (Dossier 3 §B) |

**Honest GAPS (where we fall back to literature ranges + calibration):**
1. **No national measured-soil-ug/kg layer** — the core gap. Mitigated by class-lookup + USGS background raster + ranges→MMPSO (this IS the paper's design, so it's defensible, not a workaround).
2. **No national biosolids field-boundary map** — placement is statistical (CDL service-buffer), not field-exact. Honest resolution of the federal data.
3. **No national gridded PFAS deposition** — use literature-anchored constant × PRISM/NLCD proxy.
4. **Li et al. 2019 numeric kf/n** — not in supplement; one-paper fetch required.
5. **State source layers don't generalize** — beyond EPA national layers, per-state ingestion is bespoke (you already have the MI EGLE pattern).

---

## 5. MINIMAL FIRST-CUT RECIPE to seed the Huron model (041000130106) NOW

The Huron is the paper's own watershed, so this is also a **validation harness** — your seeded values should reproduce Table 1 within calibration bands.

**Do now (all national/automatable, no new data engineering):**
1. **kf/n from gSSURGO** for every HRU layer via the six-soil Li analogy-match. *Blocker:* fetch the six (kf,n) pairs from Li et al. 2019 STOTEN 649:504–514 first; until then use a provisional OC-ordered placeholder. — *This is the only piece needing an external fetch.*
2. **Tier 0+1 background-by-land-use** from NLCD/CDL already in the model: forest 0.005–0.5, ag/pasture 0.2–8, urban 0.2–30 ug/kg PFOS. Pure lookup, zero new data.
3. **Tier 3 PPC overlay** by intersecting HRUs with **EPA FRS Facilities-Handling-PFAS (MI CSV)** + **FAA Part 139** + **TRI land-release (Envirofacts, MI)**; assign 100–4,000 ug/kg, clamp 0.5–1.3 ha. (For exact paper reproduction you can also drop in the MI EGLE sites layer you already ingest — Dossier 1 §4.)
4. **Tier 2 biosolids** — flag ag HRUs in ECHO NETBIO service buffers (MI facilities); assign 4–40 ug/kg, clamp 10–100 ha. Quick approximation acceptable; the paper's biosolids were MiWaters-specific (state data you have).
5. **Emit RANGES, not point values** — hand the per-category ranges + ±30% kf to MMPSO (54 conc + 54 kf params across 9 regions × 5 land uses). The calibration picks operative values (paper got PPC 3,700, urban 40, biosolids 4 ug/kg).
6. **Validate:** confirm seeded category ranges reproduce Table 1; the worked deposition sanity-check (~0.23 ug/kg) should land in the urban-background low end.

**Defer:**
- USGS background raster clip (verify CONUS coverage first; Huron is fine on land-use lookup for v1).
- TRI land-release **mass→concentration mixing model** (use the simpler class-lookup range first).
- National biosolids CDL-disaggregation engine (use MI MiWaters / simple buffer for Huron v1).
- Atmospheric deposition as an explicit term (it's already implicitly in the urban-background floor for v1).
- State-by-state source ingestion beyond MI.
- PFOA / multi-species (paper is PFOS-only as long-chain proxy — keep it that way for v1; revisit when the engine confirms species-resolved support, relevant because deposition is PFCA-dominated vs biosolids PFOS-dominated, Dossier 3 §B.2).

**Net:** v1 Huron can be seeded today with **zero new national datasets** beyond what SWATGenX already has (gSSURGO, NLCD/CDL, PRISM) + free EPA Envirofacts/FRS/FAA pulls + the MI state layers you already ingest — the only true external dependency is the Li et al. 2019 kf/n table.

**Key file references:** Paper PDF `/data/SWATGenXApp/codes/_temp/swat-modflow-pfas-paper/Water_research_PFAS_Fate_and_Transport_manuscript.pdf` (Table 1, Methods §2.5–2.6); supplement `/data/SWATGenXApp/codes/_temp/swat-modflow-pfas-paper/Supplementary_Materials_v3.txt` (Tables S1/S2 kf/n referenced but ABSENT — must fetch Li et al. 2019 directly).
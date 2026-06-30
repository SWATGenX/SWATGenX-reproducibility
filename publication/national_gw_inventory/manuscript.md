# A national inventory of groundwater well & lithology data for the conterminous United States

*Single data paper (consolidated; supersedes `paper1_vision_draft.md`). Target: Earth System Science
Data (ESSD) → fallback Scientific Data. Status: empirical sections populated with measured findings
through 2026-06-23. `[TODO]` = gap. Living evidence: `documents/national-groundwater-modflow-db.md`
(scorecard) + `pdf_extraction_demo/` (pilots) + `GenXAppData/state_well_records/_inventory/`.*

## Abstract (draft)

Process-based and coupled surface-water/groundwater models need a 3-D picture of the subsurface that,
across most of the United States, exists only as water-well **driller's logs** held in fragmented,
largely non-machine-readable state archives. We build a national inventory of groundwater well and
**lithology** data from primary state regulatory sources, harmonized to a single canonical schema (the
Michigan *Wellogic* template). We (1) compile an availability **census** — of ~13.4M wells across 48
CONUS states, only **8 states (~3.2M wells)** expose lithology in machine-readable form (REST/inline/bulk,
plus state viewers that prove to render *structured HTML* tables), **26 states (~7.7M)** carry lithology
only in scanned PDF logs, and **14 (~2.5M)** publish none; (2) deliver a **harmonized digital lithology
database** (≈9.6M depth-resolved intervals once Michigan is folded in), the only such primary-source,
MODFLOW-aligned compilation we are aware of; and (3) show the scanned remainder is cheaply and reliably
recoverable. Using a **stream-and-discard calibration sampler** that routes each log to a cheap text-only
LLM (born-digital) or a vision-language model (raster scan), we characterize **seven independent states**:
85–100% of wells carry a retrievable log, extraction succeeds faithfully without fabricating absent data,
and the metered cost is **$0.0002–0.0004 per log** (Gemini 2.5 flash-lite). Critically, the fraction
needing a vision model spans **33–100% by state**, anti-correlated with e-permitting adoption — so the
national recovery cost is low (**≈$2k**) and dominated by the legacy-archive states. We argue the
bottleneck is neither data nor feasibility but the **absence of a harmonized, maintained layer**, and we
describe a use-sustained path that keeps it current.

## 1. Introduction `[TODO expand]`
- The subsurface-data gap for national/coupled groundwater modeling; every regional model re-digitizes
  its basin's driller logs by hand.
- Contribution: census + harmonized digital inventory + PDF-recovery feasibility + use-sustained path.
- **Complementary to USGWD** (Lin et al. 2024, *Scientific Data*): USGWD harmonizes **14.26M** well
  records (1763–2023) to a data standard of location, purpose, status, **well depth, screen depth/length,
  and well capacity** — but by design carries **no lithology and no water levels** (verified against the
  full text: "static water"/"water level" = 0; lithology is not an attribute). USGWD is the national
  well-*location* layer; this inventory is the *subsurface-structure-and-hydraulics* layer (depth-resolved
  lithology + SWL + pump-test ingredients) that USGWD omits. The two **compose** — not a negative example
  but the complementary half a MODFLOW-ready picture needs.

### 1.1 How continental models represent the subsurface today — and why it is a gap
If primary driller-log lithology is so sparse, how are CONUS-scale subsurface models and geologic maps
built? Not from it. Continental hydrologic platforms take one of two routes, **neither using harmonized
well logs**. (1) *Conceptual collapse* — operational water-balance models, the NOAA **National Water
Model** (WRF-Hydro; Gochis et al. 2020) and the USGS **National Hydrologic Model** (PRMS; Regan et al.
2018), resolve only a ~2 m soil column and abstract everything beneath into lumped, calibrated "bucket"
reservoirs with no geologic structure. (2) *Generalized, map-derived inputs* — physically based models
parameterize the subsurface from a small, shared set of products derived from geologic **maps**, not
boreholes. The flagship integrated model, **ParFlow-CONUS**, resolves the entire deep subsurface as one
(CONUS1: 5 layers, 102 m; Maxwell et al. 2015) to six (CONUS2: 10 layers, 392 m; Yang et al. 2023) broad
units, with conductivity assigned from the global **GLHYMPS** permeability map (Gleeson et al. 2014 —
itself derived from the GLiM lithology map, Hartmann & Moosdorf 2012), soils from SSURGO, and
depth-to-bedrock from Shangguan et al. (2017). Its developers state plainly that the model is "limited
not by computational expense but by data availability, with a lack of detailed depth-to-bedrock and
aquifer thickness estimates at meaningful resolution," and is better viewed as a "shallow aquifer storage
model" (O'Neill et al. 2021). The same few generalized products recur field-wide: GLHYMPS in the de Graaf
et al. (2017) global groundwater model, exponential depth-decay of K in Fan et al. (2013, whose >1M well
records only *validate* water-table depth), Pelletier et al. (2016) regolith thickness, and soil-only
layers that stop at ~2 m (SoilGrids, Hengl et al. 2017; POLARIS, Chaney et al. 2019). The lithology beneath
these permeability products is itself a coarse, surface, polygon map: the global GLiM (Hartmann & Moosdorf
2012) descends from continental compilations such as the **262,111-polygon North American lithological map**
of Moosdorf et al. (2010), whose authors showed that map **resolution and source alone** shift modeled
continental fluxes by roughly −59% to +38% — generalization with a *measured* cost.

National geologic products are no better as a 3-D lithology source. The seamless USGS **State Geologic Map
Compilation** (Horton et al. 2017) is a *surface* polygon geodatabase — interpreted single-horizon geology,
not depth-resolved stratigraphy. USGS **3-D geologic framework models** do resolve depth but are regional:
an inventory found 38 models covering ~49% of the CONUS at a **~4,170 km² median footprint** (USGS 2023),
decentralized and poorly catalogued. The one effort to mine bulk driller's records at scale — **Bayless et
al. (2017)**, ~14 million standardized logs — is confined to the glaciated 24 states and outputs *derived*
hydrogeologic-property grids (deposit thickness, conductivity), **not** a harmonized primary-source
lithology layer. At the opposite extreme, federal/research effort yields *exquisite* per-borehole records —
full drilling, construction, geophysical, and lithologic logs, even **NMR-*measured* hydraulic
conductivity** — but only at a handful of research wells (e.g., USGS Data Series 1058, two boreholes at
Idaho National Laboratory, Twining et al. 2017; the DOE East River watershed SFA, four boreholes with
NMR-derived K, Uhlemann et al. 2020), not a population. Continental subsurface data thus splits between
coarse-everywhere maps and exquisite-nowhere research holes; the scalable middle — millions of driller's
logs — is what remains unharmonized. Thus,
mirroring USGWD on the well-location side (Lin et al. 2024), every prior subsurface
compilation is generalized, regional, or property-derived: a harmonized, CONUS-wide, primary driller-log
*lithology* layer — the input these models actually lack — does not exist. That absence, not a
computational or feasibility barrier, is the gap this inventory fills.

## 2. Methods

### 2.1 Harvest — and the heterogeneity it exposes
State sources are ArcGIS REST (most), Socrata, bulk file, or by-request. A registry-driven harvester
(`national_gw_inventory/download_state_well_records.py`) paginates each REST layer to FlatGeobuf. Real
heterogeneity encountered, each a methods lesson:
- **Pagination is not universal.** Several servers (e.g. MS) reject `resultOffset` ("Pagination is not
  supported"), silently yielding zero. Fallback: enumerate object IDs (`returnIdsOnly`) then fetch in
  `objectIds` batches (`download_arcgis_objectids.py`) — recovered MS's 181,279 wells.
- **Viewer vs direct PDF — and viewers that hide *structured* data.** Several states expose a log URL
  that is an HTML viewer rather than a file. Hopping each viewer to its per-well report is decisive:
  two (**OK**, **IA**) turned out to render a **server-side HTML lithology table** that parses directly to
  the canonical schema — no vision model needed (OK: OWRB `printreport.php`, 243,801 wells; a single
  http→https redirect was the only obstacle) — while others (**NY, UT, ID**) resolve to scanned PDFs.
  The lesson: an HTML-viewer URL is not evidence of "PDF-only"; it must be dereferenced before
  classifying a state. Direct PDF/image states (OR vault, KS Azure blob, NV/SD/FL/WI) skip the hop.
- **Network/jurisdiction blocks.** Datacenter-IP 403 (TN, NH) and DNS blocks (PA) require a different network.
- **Scope:** the inventory is **CONUS-only**; non-contiguous states (AK, HI) are excluded by design.

### 2.2 Harmonization to the Wellogic schema
Each state's native lithology is mapped to one canonical interval schema
(`source_id | state | well_id | seq | top_ft | bottom_ft | thickness_ft | description (verbatim) |
normalized`). Adapters handle separate interval tables (MI/MT/AL), wide inline columns
(MO `FORM_1..10` + `FROM_1..10`, un-pivoted to long), and multi-CSV bulk (CA: freeform/quickpick/
uscs/generalized, freeform-priority union by well). Code: `national_gw_inventory/build_inventory.py`.

### 2.3 Lithology-term normalization
Verbatim driller text → controlled vocabulary via a rule-based keyword map (start point; the labor
core). Verbatim descriptions are always retained, so the vocabulary is refinable post hoc. Evidence
that it needs regional terms: Plains/Southwest "Caliche" and mixed "Sand & Gravel Clay Mixed" currently
fall to `other` (~19–27% of intervals). `[TODO: expand vocab; report before/after]`

### 2.4 PDF triage and extraction — a sampling, not a full-pass, design
We deliberately do **not** run a full PDF pass per state. Instead a per-state **calibration sampler**
(`national_gw_inventory/pdf_extraction/sample_state_pdfs.py`) draws a small date-stratified sample of a
state's driller-log PDFs and, for each, **streams-and-discards**: fetch → classify → extract → delete
(no PDF is retained, so the multi-hundred-GB national archive never materializes). Classification routes
each log two ways: born-digital (embedded text layer, via `pdftotext`) → a cheap **text-only LLM** (no
image tokens); raster scan → a **vision-language model** (the only thing that reads handwriting). The
sampler emits a one-row **calibration card** per state — has-PDF %, LLM/VLM split, extraction quality,
and metered `$/log` — which is what lets each state be costed *before* committing to expand it, and
quantifies how much of the corpus genuinely needs a VLM versus a cheap LLM. Scanned logs are extracted
with Gemini 2.5 (native PDF input, forced JSON schema: intervals + verbatim description + normalized
class + total depth + SWL + legibility + self-confidence); token usage is metered for true cost
(`pdf_extraction/extract_lithology_llm.py`). A local open VLM (Qwen2.5-VL) was evaluated for sovereignty
but trailed on handwriting; given trivial API cost, the hosted model is used.

This OCR-free, VLM-based approach rests on a method base that matured only recently (2023–2025). Frontier
multimodal LLMs — Gemini 1.5/2.5 (Gemini Team 2024), GPT-4o (OpenAI 2024), Qwen2.5-VL (Bai et al. 2025),
InternVL (Chen et al. 2024) — now read text-rich and handwritten document images directly, as quantified
by OCR/document benchmarks (OCRBench, Liu et al. 2023/2024; OCRBench v2, Liu et al. 2025) and OCR-free
document models (mPLUG-DocOwl 1.5, Hu et al. 2024). Crucially for *handwritten* driller's logs, recent
work shows zero-/few-shot multimodal-LLM transcription of historical handwriting at usable accuracy —
~5–7% character error rate, below dedicated HTR systems (Humphries et al. 2024) — and of handwritten
forms into structured fields (Crosilla et al. 2025; Greif et al. 2025). The broader "documents → structured
database" paradigm is likewise established in adjacent domains: scientific-literature extraction (Dagdelen
et al. 2024; ChatExtract, Polak & Morgan 2023), clinical-note IE (Hu et al. 2024), and specimen-label
digitisation. **Yet the well-record domain is near-virgin.** Even within geoscience, LLMs have so far been
applied to *born-digital* report text — knowledge-graph and question-answering extraction (Ge et al.
2026) — and to *generating* geological cross-sections from sparse borehole data (Li & Shi 2025), while
the one paper operating on borehole lithology itself (GEOBERTje, Vandelaer et al. 2024) merely
*classifies already-transcribed* descriptions. None recovers structured lithology from scanned,
handwritten driller's logs. End-to-end VLM recovery of a depth-resolved lithology layer from scanned U.S.
logs at scale is, to our knowledge, new, and is what makes Phase-2 feasible now in a way it was not three
years ago.

## 3. Results

### 3.1 Availability census (Table 1)
| Category | States | Wells | Extraction needed |
|---|---|---:|---|
| A — machine-readable lithology (REST/inline/bulk/structured-HTML) | 8 (MI, MT, AL, MO, CA, KY, IA, **OK**) | ~3.2M | none |
| B — PDF-only lithology | 26 (KS, WA, OR, WI, TX, FL, NV, SD, ID, NY, UT, …) | ~7.7M | yes (VLM ± LLM) |
| C — no digital lithology / no public DB | 14 | ~2.5M | n/a |

Reclassification is bidirectional and must be evidence-based, not assumed from the access method:
- **OK B→A**: its OWRB map viewer dereferences to a *server-side HTML lithology table* (`printreport.php`,
  243,801 wells, depth-resolved material/from/to) that parses straight to the canonical schema — no PDF,
  no vision model. IA resolved the same way. An HTML-viewer URL is therefore **not** evidence of PDF-only.
- **KS A→B**: its `GEOLOGICAL_FORMATION` column is 100% empty and the ORDS detail page has no lithology
  table — lithology survives only in its scanned blob PDFs. A structured-looking column is **not** evidence
  of machine-readable lithology.
- **Scope**: CONUS-only; AK/HI excluded by design.

### 3.2 Harmonized digital inventory (Table 2)
Built to date (Michigan still ingesting): **3,863,128 intervals across 4 states.**
| State | source | intervals | wells | % classified |
|---|---|---:|---:|---:|
| MT | GWIC | 1,539,984 | 244,277 | 100% |
| CA | OSWCR (4-CSV union) | 1,334,875 | 104,618 | 100% |
| MO | DNR WIMS (un-pivoted) | 946,944 | 185,687 | 100% |
| AL | NGWMN | 41,325 | 40,486 | 2% (sparse source) |
| MI | Wellogic | 5,771,062 (pending) | ~ | — |
| **Total (w/ MI)** | | **≈9.6M** | | |

### 3.3 PDF corpus characterization — the LLM/VLM split (Table 3)
A per-state **calibration sampler** (§2.4) draws a date-stratified sample (n=15–20), streams-and-discards
each log, and routes it text-layer→LLM vs raster→VLM. Seven states measured live:

| State (source) | has-PDF | text-layer % (LLM) | raster scan % (VLM) | avg intervals/log |
|---|---:|---:|---:|---:|
| ID (Laserfiche) | 93% | 0% | 100% | 15.2 |
| SD (DANR images) | 100% | 0% | 100% | 12.6 |
| OR (OWRD vault) | 100% | 10% | 90% | 3.7 |
| NV (NDWR images) | 95% | 11% | 89% | 6.3 |
| KS (KGS blob) | 85% | 29% | 71% | 12.5 |
| WI (DNR ReportViewer) | 100% | 65% | 35% | 3.2 |
| FL (SJRWMD DOCLINK) | 90% | 67% | 33% | 3.1 |

Two findings: (i) **85–100% of wells carry a retrievable log** — the data exists; (ii) the **VLM share
spans 33–100%**, sharply **anti-correlated with e-permitting era** — legacy paper-archive states (ID, SD,
OR, NV) are ~90–100% scans, while recent e-permitting states (WI, FL) are ~two-thirds born-digital and
need only the cheap LLM route. This split is what sets per-state cost; it must be *measured*, not assumed.
(Limitations: n=15–20 per state; these seven have a direct/derefable PDF URL — viewer-hop and no-URL
states await per-state resolvers.)

### 3.4 Extraction cost (Table 4) — measured, seven states
Metered token cost, Gemini 2.5 flash-lite (the routed default; flash is reserved for low-legibility
re-runs at ~4×):

| State | success | blended $/log | $/1k logs |
|---|---:|---:|---:|
| OR | 20/20 | $0.000167 | $0.17 |
| WI | 20/20 | $0.000196 | $0.20 |
| FL | 18/18 | $0.000201 | $0.20 |
| NV | 19/19 | $0.000221 | $0.22 |
| KS | 17/17 | $0.000364 | $0.36 |
| SD | 20/20 | $0.000400 | $0.40 |
| ID | 14/14 | $0.000409 | $0.41 |

Extraction is faithful across all seven — driller shorthand transcribed verbatim (incl. misspellings),
`poor`/`partial` legibility flags on illegible scans, and **empty arrays rather than fabricated intervals**
on blank logs. Per-log cost scales with VLM share and log depth: the deepest, most scan-heavy states
(ID, SD) top out at ~$0.41/1k; LLM-routed e-permitting states (OR, WI, FL) run ~$0.17–0.20/1k.
**National projection:** ~7.7M PDF-only wells × ~90% retrievable × ~$0.0003 blended ≈ **≈$2.0k** at
flash-lite (born-digital share routed near-free via `pdftotext`+LLM; raster remainder to the VLM). The
API is the cheap part — the binding constraints are wall-clock (politely fetching millions of small
gov-hosted files) and normalization-vocab QA, **not** dollars or storage (stream-and-discard avoids the
~700 GB archive entirely). KS note: a fraction of blobs are GIF (need image-mime handling); "Caliche"
still exposes the regional-vocab gap (§2.3).

## 4. Discussion `[TODO expand]`
- **Why sparse:** no federal mandate (well construction is a *state* permitting byproduct; USGS does
  geologic mapping/monitoring, not driller-log custody); lithology is a paper artifact; governance
  fragmentation; no adopted schema. The one federal attempt (NGDS) proved feasibility but decayed on
  funding — *sustainability*, not capability, is the failure mode. `[verify NGDS + cite]`
- **Use-sustained model:** a layer kept current because it feeds an operational modeling platform.
- **Proof of utility:** a non-MI state through the existing MODGenX→MODFLOW-6 pipeline `[insert]` — and,
  more broadly, a harmonized driller-log lithology layer is exactly the input the continental models of
  §1.1 currently approximate with GLHYMPS-class generalized geology, so it offers a path to replace those
  coarse deep-K units with observation-based stratigraphy where log density allows.
- **Limitations / honesty:** publish tiers AND exclusions (PDF-only, section-center geometry, sparse
  sources like AL); the unevenness is a finding, not a defect.

### 4.1 Known gaps and shortcomings — a living inventory, not a closed product
We treat this as an ongoing compilation and catalogue its current holes so users can judge fitness and
later versions can close them:
- **Lithology coverage is incomplete.** Queryable lithology exists for 8 states; 26 are PDF-only
  (extraction in progress, 7 states calibrated) and 14 publish none. Large states (TX, WA, OH) and the
  viewer-hop/403 states (NY, UT, TN, NH, VT, VA, ME) are not yet harvested.
- **Hydraulic ingredients are present but uneven** (audit: `publication/national_gw_inventory/
  hydraulic_coverage.md`, regenerated by `national_gw_inventory/audit_hydraulic_coverage.py`). Static
  water level and total depth form a broad backbone (SWL in ~20 states, frequently 80–100% populated;
  depth widely 90–100%). But the pump-test fields needed to *derive* conductivity are scarce: **direct
  specific capacity exists in only ~2 states (NV, WI), drawdown in ~3 (AZ, NV, WI), and measured
  transmissivity essentially nowhere (NV alone).** A national derived-K layer is therefore feasible only
  where yield+drawdown (or specific capacity) co-occur — a minority of states; elsewhere K must fall back
  to lithology-facies estimates (still anchored to observed logs, unlike GLHYMPS map polygons, §1.1).
  Screened-interval and aquifer-name fields are likewise sparse, so aquifer thickness will mostly come
  from the lithology log rather than a column.
- **The audit is a lower bound:** field-name matching can miss oddly-named columns; population is a
  1500-row sample; CA/MI/MN are stored outside the `*_wells.fgb` convention and audited separately —
  MI/Wellogic is the only source already carrying H_COND/V_COND/AQ_THK.
- **Other documented holes:** normalization leaves ~8–27% of intervals as `other` (regional vocab);
  geometry is PLSS section-center for some states; provenance/vintage varies; PDF extraction is validated
  at n=15–20 per state, not whole-corpus. None is fatal — each is an improvable, documented gap. The
  contribution is the harmonized framework plus an honest map of what is and is not yet covered.

## 5. Data & code availability
Harvest/harmonization/extraction: `national_gw_inventory/`. Census + scorecard:
`documents/national-groundwater-modflow-db.md`. Demo + pilots: `publication/national_gw_inventory/`.
Inventory output: `GenXAppData/state_well_records/_inventory/`. `[DOI host TBD: Zenodo/HydroShare]`

## References `[TODO]`

*Inventory / precedent*
- Lin, C.-Y., Miller, A., Waqar, M., Marston, L.T. (2024). A database of groundwater wells in the United
  States (USGWD). *Scientific Data* 11:335. DOI 10.1038/s41597-024-03186-3 — 14,260,752 records,
  1763–2023; attributes = location/purpose/status/well-depth/screen-depth+length/well-capacity;
  **no lithology, no water levels**. The complementary well-location layer; also a model for the
  Data-Descriptor genre/format we target. *(full text verified, PDF on file)*
- Bayless, E.R., et al. (2017). Maps and grids of hydrogeologic information created from standardized
  water-well drillers' records of the glaciated United States. *USGS SIR 2015–5105.*
  https://doi.org/10.3133/sir20155105 — closest prior art (≈14M logs); **regional (24 states) +
  property-derived, not a lithology layer.**
- NGDS / AASG — feasibility-proven, sustainability-failed precedent. `[cite]`
- USGS RASA / NGWMN / NWIS GWSI — federal monitoring/framework scope. `[cite]`
- Wellogic (Michigan EGLE) schema. `[cite]`

*Continental subsurface representation (related work, §1.1)*
- Maxwell, R.M., Condon, L.E., Kollet, S.J. (2015). A high-resolution simulation of groundwater and
  surface water over most of the continental US (ParFlow v3). *Geosci. Model Dev.* 8, 923–937.
  https://doi.org/10.5194/gmd-8-923-2015
- O'Neill, M.M.F., Tijerina, D.T., Condon, L.E., Maxwell, R.M. (2021). Assessment of the ParFlow–CLM
  CONUS 1.0 integrated hydrologic model. *Geosci. Model Dev.* 14, 7223–7254.
  https://doi.org/10.5194/gmd-14-7223-2021
- Yang, C., et al. (2023). A high-resolution, 3D groundwater-surface water simulation of the contiguous
  US: ParFlow CONUS 2.0. *J. Hydrol.* 626, 130294. https://doi.org/10.1016/j.jhydrol.2023.130294
- Gleeson, T., Moosdorf, N., Hartmann, J., van Beek, L.P.H. (2014). A glimpse beneath earth's surface:
  GLHYMPS of permeability and porosity. *Geophys. Res. Lett.* 41, 3891–3898.
  https://doi.org/10.1002/2014GL059856
- Huscroft, J., Gleeson, T., Hartmann, J., Börker, J. (2018). GLHYMPS 2.0. *Geophys. Res. Lett.* 45,
  1897–1904. https://doi.org/10.1002/2017GL075860
- Hartmann, J., Moosdorf, N. (2012). The new global lithological map database GLiM. *Geochem. Geophys.
  Geosyst.* 13, Q12004. https://doi.org/10.1029/2012GC004370
- Moosdorf, N., Hartmann, J., Dürr, H.H. (2010). Lithological composition of the North American continent
  and implications of lithological map resolution for dissolved silica flux modeling. *Geochem. Geophys.
  Geosyst.* 11, Q11003. DOI 10.1029/2010GC003259 — 262,111-polygon N. American surface-lithology map
  (GLiM lineage); shows map resolution/source alone shift modeled fluxes −59% to +38%. *(full text on file)*
- Twining, B.V., et al. (2017). Drilling, Construction, Geophysical Log Data, and Lithologic Log for
  Boreholes USGS 142 and USGS 142A, Idaho National Laboratory, Idaho. *USGS Data Series 1058* (DOE/ID-22243)
  — federal per-borehole gold standard (n=2); the exquisite-but-sparse end of the data spectrum. *(on file)*
- Uhlemann, S., Carr, B., Dafflon, B., Williams, K. (2020). Geophysical borehole logging data of wells
  ER-GLS1, ER-GUM1, ER-PLM7, ER-PLM8 at the East River Watershed, Colorado. ESS-DIVE / OSTI,
  DOI 10.15485/1650355 — 4 DOE research boreholes (Mancos shale) with gamma/resistivity/NMR-**measured**
  hydraulic conductivity; the research end where K is *measured* (vs our specific-capacity-derived K at scale).
- Pelletier, J.D., et al. (2016). A gridded global data set of soil, intact regolith, and sedimentary
  deposit thicknesses. *J. Adv. Model. Earth Syst.* 8, 41–65. https://doi.org/10.1002/2015MS000526
- Shangguan, W., Hengl, T., Mendes de Jesus, J., Yuan, H., Dai, Y. (2017). Mapping the global depth to
  bedrock for land surface modeling. *J. Adv. Model. Earth Syst.* 9, 65–88.
  https://doi.org/10.1002/2016MS000686
- Hengl, T., et al. (2017). SoilGrids250m: global gridded soil information. *PLoS ONE* 12, e0169748.
  https://doi.org/10.1371/journal.pone.0169748
- Chaney, N.W., et al. (2019). POLARIS soil properties: 30-m maps over the CONUS. *Water Resour. Res.*
  55, 2916–2938. https://doi.org/10.1029/2018WR022797
- Chaney, N.W., Metcalfe, P., Wood, E.F. (2016). HydroBlocks: a field-scale resolving land surface model.
  *Hydrol. Process.* 30, 3543–3559. https://doi.org/10.1002/hyp.10891
- Fan, Y., Li, H., Miguez-Macho, G. (2013). Global patterns of groundwater table depth. *Science* 339,
  940–943. https://doi.org/10.1126/science.1229881
- de Graaf, I.E.M., et al. (2017). A global-scale two-layer transient groundwater model. *Adv. Water
  Resour.* 102, 53–67. https://doi.org/10.1016/j.advwatres.2017.01.011
- Horton, J.D., San Juan, C.A., Stoeser, D.B. (2017). The State Geologic Map Compilation (SGMC)
  geodatabase of the conterminous United States. *USGS Data Series 1052.*
  https://doi.org/10.3133/ds1052
- U.S. Geological Survey (2023). An inventory of three-dimensional geologic models—USGS, 2004–22. *USGS
  Data Report 1183.* https://pubs.usgs.gov/publication/dr1183
- Regan, R.S., et al. (2018). Description of the National Hydrologic Model for use with PRMS. *USGS
  Techniques and Methods 6-B9.* https://pubs.usgs.gov/publication/tm6B9
- Gochis, D.J., et al. (2020). The WRF-Hydro Modeling System Technical Description (NOAA National Water
  Model). *NCAR Technical Note.* `[pin NWM/WRF-Hydro version to the release cited]`

*VLM/LLM document extraction — the method base (§2.4); all 2023+, arXiv-verified*
- Gemini Team, Google (2024). Gemini 1.5: Unlocking multimodal understanding across millions of tokens
  of context. arXiv:2403.05530
- OpenAI (2024). GPT-4o System Card. arXiv:2410.21276
- Bai, S., et al. (2025). Qwen2.5-VL Technical Report. arXiv:2502.13923 — flags structured invoice/form/
  table extraction.
- Chen, Z., et al. (2024). InternVL: Scaling up Vision Foundation Models. arXiv:2312.14238 (CVPR 2024)
- Liu, Y., et al. (2023/2024). OCRBench: On the Hidden Mystery of OCR in Large Multimodal Models.
  arXiv:2305.07895; DOI 10.1007/s11432-024-4235-6
- Liu, Y., et al. (2025). OCRBench v2. arXiv:2501.00321
- Hu, A., et al. (2024). mPLUG-DocOwl 1.5: Unified Structure Learning for OCR-free Document Understanding.
  arXiv:2403.12895 (Findings of EMNLP 2024)
- Humphries, M., et al. (2024). Unlocking the Archives: LLMs Achieve SOTA on Transcription of Handwritten
  Historical Documents. arXiv:2411.03340 — CER ~5–7%, beats Transkribus.
- Crosilla, L., Klic, L., Colavizza, G. (2025). Benchmarking Large Language Models for Handwritten Text
  Recognition. arXiv:2503.15195 — zero-shot HTR with Claude/Gemini/GPT-4o.
- Greif, et al. (2025). Multimodal LLMs for OCR, OCR Post-Correction, and NER in Historical Documents.
  arXiv:2504.00414
- Dagdelen, J., et al. (2024). Structured information extraction from scientific text with large language
  models. *Nature Communications* 15:1418. DOI 10.1038/s41467-024-45563-x
- Polak, M.P., Morgan, D. (2023). Extracting Accurate Materials Data from Research Papers with
  Conversational LLMs and Prompt Engineering (ChatExtract). arXiv:2303.05352
- Hu, Y., et al. (2024). Information Extraction from Clinical Notes: Are We Ready to Switch to LLMs?
  arXiv:2411.10020
- **Vandelaer, et al. (2024). Classification of geological borehole descriptions using a domain adapted
  large language model (GEOBERTje). arXiv:2407.10991** — the closest prior art: *classification* of
  already-transcribed borehole text, NOT scanned-log extraction → defines the whitespace this paper fills.
- Ge, Q., Li, P., Li, J., Sun, H., Liu, Z. (2026). Leveraging large language models for automated
  knowledge extraction from geological reports. *Journal of Rock Mechanics and Geotechnical Engineering*
  (in press). DOI 10.1016/j.jrmge.2025.12.038 — benchmarks 8 LLMs for knowledge-graph/QA extraction from
  born-digital geological *text*; not scanned logs, not a lithology DB. *(full text verified, PDF on file)*
- Li, H., Shi, C. (2025). Few-shot learning of geological cross-sections from sparse data using large
  language model. *Geodata and AI* 2, 100010. DOI 10.1016/j.geoai.2025.100010 (open access) — LLM
  *generates* 2-D cross-sections from sparse boreholes; a modeling task, not record→database extraction.
  *(full text verified, PDF on file)*
- `[VERIFY-BEFORE-CITE — still unresolved 2026 IDs from lit search: VAREX arXiv:2603.15118; "From
  Handwriting to Structured Data" arXiv:2604.16504. Do not cite until independently confirmed.]`

# Literature-review source notes (verified from full-text PDFs)

PDFs in this folder are publisher copies (Elsevier) provided for reading — **gitignored, not committed**.
These notes record what was verified from the full text, for citation provenance.

## Ge, Q., Li, P., Li, J., Sun, H., Liu, Z. (2026)
"Leveraging large language models for automated knowledge extraction from geological reports."
*Journal of Rock Mechanics and Geotechnical Engineering* (in-press pre-proof).
**DOI: 10.1016/j.jrmge.2025.12.038** · PII S1674-7755(26)00121-6 · Received 2025-08-04, accepted 2025-12-03.
- **What it does:** benchmarks 8 LLMs (DeepSeek-V3/R1, GPT-4/4o/3.5, Llama-3.1, Qwen2.5-72B) on
  **knowledge-graph construction + question-answering** from *unstructured geological report text*, with
  ICL / CoT / knowledge-injection prompting + RAG. DeepSeek-V3 best at KG, DeepSeek-R1 best at QA.
- **Relation to our paper:** adjacent (LLMs structuring geological text) but operates on **born-digital
  text**, produces **KG/QA**, not a depth-resolved lithology database, and never touches scanned or
  handwritten driller's logs. Reinforces — does not scoop — our whitespace.

## Li, H., Shi, C. (2025)
"Few-shot learning of geological cross-sections from sparse data using large language model."
*Geodata and AI* 2 (2025) 100010. **DOI: 10.1016/j.geoai.2025.100010** · open access (CC BY) ·
Received 2024-10-02, accepted 2025-02-12. Nanyang Technological University, Singapore.
- **What it does:** few-shot / in-context LLM to **generate** 2-D geological cross-sections from sparse
  site-investigation (borehole) data; CoT + self-consistency prompting; two real-world examples.
- **Relation to our paper:** a **modeling/inference** task (produce cross-sections), not record→database
  extraction. Adjacent, not overlapping.

## Lin, C.-Y., Miller, A., Waqar, M., Marston, L.T. (2024)  — USGWD (the key contrast paper)
"A database of groundwater wells in the United States." *Scientific Data* 11:335.
**DOI: 10.1038/s41597-024-03186-3** · Virginia Tech (Marston lab) · open access.
- **What it is:** the United States Groundwater Well Database — **14,260,752** well records (1763–2023)
  compiled from state + federal agencies, harmonized to a new data standard, validated by state
  authorities, released as tabular + geospatial points. A *Data Descriptor* (our exact target genre).
- **Data-standard attributes (verified from full text):** Well ID, Well ID (State), Longitude, Latitude,
  County, flags, **Well Depth (ft), Screen Depth (ft), Length of Screen (ft), Well Capacity**, well
  purpose/use, operational status, Flag Duplicate.
- **What it LACKS (our differentiator, verified):** **no lithology** (not an attribute), **no water
  levels / SWL** ("static water"/"water level" = 0 occurrences), no specific capacity, no transmissivity,
  no casing/construction stratigraphy. It has screen depth + capacity but not the SWL/drawdown needed to
  derive K.
- **Positioning:** USGWD = national well-*location/use/depth/capacity* layer (primary-source, validated —
  NOT a third-party junk aggregation; the earlier "negative example" framing was imprecise). Ours = the
  *subsurface-structure + hydraulics* layer (depth-resolved lithology + SWL + pump-test ingredients) it
  omits. **Complementary, not competing.** Their Table S4 (state→attribute crosswalk) and per-state counts
  (Fig 1) are a useful cross-check for our harvest coverage.

## Moosdorf, N., Hartmann, J., Dürr, H.H. (2010) — N. American lithology map (§1.1)
"Lithological composition of the North American continent and implications of lithological map resolution
for dissolved silica flux modeling." *Geochem. Geophys. Geosyst.* 11, Q11003. **DOI 10.1029/2010GC003259**.
- **What it is:** a 262,111-polygon **surface** lithological map of North America (62.8% sediments, 14.8%
  plutonics, 13.3% metamorphics, 7.2% volcanics), compared to global lithological maps. GLiM lineage
  (Moosdorf & Hartmann also authored GLiM 2012 → feeds GLHYMPS → ParFlow-CONUS).
- **Why it matters for us:** quantifies that **map resolution + source alone shift modeled fluxes −59% to
  +38%**, and that same-named lithology classes differ across datasets. Direct evidence that the generalized
  surface-polygon lithology underpinning continental models carries a measured cost — the corrective is
  depth-resolved, observation-based well-log lithology (ours).

## Twining, B.V., et al. (2017) — USGS Data Series 1058 (DOE/ID-22243)
"Drilling, Construction, Geophysical Log Data, and Lithologic Log for Boreholes USGS 142 and USGS 142A,
Idaho National Laboratory, Idaho." *USGS Data Series 1058.*
- **What it is:** the federal gold standard for a *single borehole* — full drilling/construction/geophysical
  + lithologic logs — but for **two** research/monitoring wells at INL.
- **Why it matters:** the *exquisite-but-sparse* end of the spectrum. Federal subsurface data = coarse
  geologic maps (everywhere) ↔ research boreholes like this (perfect, almost nowhere); the abundant
  middle (driller's logs) is unharmonized = our niche. Useful rhetorical bookend; narrow as a source.

## Uhlemann, S., Carr, B., Dafflon, B., Williams, K. (2020) — East River borehole geophysics (§1.1)
"Geophysical borehole logging data of wells ER-GLS1, ER-GUM1, ER-PLM7, ER-PLM8 at the East River
Watershed, Colorado." ESS-DIVE / OSTI. **DOI 10.15485/1650355** · OSTI 1650355.
- **What it is:** 4 DOE research boreholes (Mancos shale, Upper Colorado / Watershed Function SFA) with
  full geophysical suite — natural+spectral gamma (Th/K/U), magnetic susceptibility, fluid temp/EC, EM
  resistivity — and **NMR-derived water content + hydraulic conductivity (measured K)**. CSV per borehole.
- **Why it matters:** a second "exquisite-but-sparse" example (with DS1058). Sharpens the hydraulics
  point: **measured K** (NMR/pump tests) exists only at a few research wells; our specific-capacity-derived
  K is the scalable alternative across millions of driller's logs.

## Colorado data landscape (provenance for CO classification, 2026-06-24)
- **CGS Aquifer Studies** (cologeosurvey AGOL → cgsarcimage.mines.edu): per-county aquifer FRAMEWORK
  models, **only 4 counties** (Chaffee, Douglas, Mesa, Park). Wells carry hydraulic ingredients
  (static level, screen TPERF/BPERF, yield, depth) + a single aquifer/unit code — NOT a multi-interval
  lithology log.
- **CO DWR Well Permit viewer** (maps.dnrgis.state.co.us/dwr): has a **Geophysical Log** layer (GR/RES/SP
  curves — a different modality, not lithology), Water Level, Transmissivity contours, and **Well
  Application / Final Permit** layers = the well construction reports where the actual driller's lithology
  lives (likely scanned). → CO lithology target = DWR construction reports (PDF, to confirm).

## Synthesis (for §2.4 novelty)
Three geoscience LLM works bracket but do not occupy our niche: Ge et al. 2026 (text → KG/QA),
Li & Shi 2025 (sparse data → cross-section modeling), GEOBERTje / Vandelaer et al. 2024 (classify
already-transcribed borehole text). **None recovers structured lithology from scanned, handwritten
driller's logs at scale** — that is this paper's contribution.

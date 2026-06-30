# Publication plan — national groundwater (well-lithology) inventory

**Scope of this folder.** Publication drafts + audit/figure code for the national groundwater
inventory live here (`publication/national_gw_inventory/`). The *inventory-completion* code
(harvesters, the PDF-extraction pipeline) lives in `national_gw_inventory/`. Project framing,
quality rubric, and the source scorecard: `documents/national-groundwater-modflow-db.md`.

## ONE paper (decided 2026-06-23) — the national inventory

**Working title:** *"A national inventory of groundwater well & lithology data for the conterminous
United States."*

- **Target:** Earth System Science Data (ESSD) → fallback *Scientific Data*.
- **Type:** data paper / descriptor. The "why sparse / use-sustained" narrative is the **intro +
  discussion**, NOT a separate paper. Vision-only paper dropped.
- **Novelty hinge vs USGWD (Lin et al. 2024):** USGWD = third-party aggregation, depth/capacity only,
  no lithology, no SWL, static. Ours = **lithology-bearing + SWL + primary-source + quality-graded**,
  plus an explicit accounting of what is and isn't recoverable.
- **What the paper delivers, in build order:**
  1. **The availability census** (Table 1: 8 digital / 26 PDF-only / 14 none; ~13.4M wells) — the map
     of where US groundwater lithology actually lives.
  2. **The harmonized digital inventory** (the 8 digital-lithology states → one Wellogic-schema DB) —
     the concrete, usable deliverable, buildable now without extraction.
  3. **The PDF-only triage** (Table 2): for the 26 PDF states, estimate the three buckets —
     **(a)** text-layer logs extractable with a cheap text LLM, **(b)** raster scans needing a VLM,
     **(c)** logs that need no processing (no lithology / non-log / duplicate). This bounds the job.
  4. **Extraction feasibility + cost** (measured: $0.0002–0.0009/log, no hallucination) → the path to
     fold the recoverable PDF lithology into the inventory.
  5. **Proof of utility:** a non-MI state run through the existing MODGenX→MF6 pipeline.
- **Discussion framing:** structural sparseness (federalism, NGDS feasibility-but-not-sustainability,
  USGS scope), and the use-sustained maintenance model.
- **Status:** harvest done (28 states, ~7.98M wells); lithology MI(5.77M)/MT(1.54M)/AL landing;
  building the harmonized digital inventory next.

*(`paper1_vision_draft.md` is superseded — its census/PDF/cost sections migrate into this single paper.)*

## Phase-2 PDF extraction — feasibility demo (this folder)

Goal: show, on **10 real Oregon driller's-log PDFs**, how confidently an LLM extracts the lithology
log (depth intervals + normalized class) + construction, and at what **measured** per-PDF cost.

- **Source:** OWRD "vault" scanned water-well reports (direct `application/pdf`), pulled via the OR
  `well_log_url`. 10 logs across 9 counties, 40–600 ft. Files in `pdf_extraction_demo/pdfs/`.
- **Pipeline:** `national_gw_inventory/pdf_extraction/extract_lithology_llm.py` — Gemini native PDF
  input + forced JSON response schema (depth intervals, verbatim description, normalized class from a
  25-term vocab, total depth, SWL, water-bearing zones, legibility, self-confidence). Token usage
  captured → real cost.
- **Models compared:** gemini-2.5-flash-lite / flash / pro (reusing the Ask SWATGenX key).
- **Results + cost:** see `RESULTS_AND_COST.md` (filled from the demo run).
- **Manual check:** the source PDFs sit beside the extracted JSON so each interval can be verified by
  eye against the scan.

## Open decisions / next
- Run the published-models survey (Table 2 evidence) — *gated on user go.*
- Pick the canonical lithology controlled vocabulary (start from Wellogic `PRIM_LITH`/`LITH_MOD`).
- Author list, data-availability/DOI host (HydroShare? Zenodo?), licensing.
- Phase-2 scope: which PDF-only states first (bounded by the models survey).

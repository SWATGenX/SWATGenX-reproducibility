# National PFAS Inventory (PDF/VLM-harvested)

Structuring PFAS measurement data that is trapped in agency **PDF reports** and missing from every
open structured database (WQP / EPA PFAS Analytic Tools / state feeds). Two products:

1. **Depth-resolved SOIL PFAS (vadose profiles)** — a national first. Concentration vs soil depth,
   the data layer needed to drive SWAT+↔MODFLOW6 land→vadose→groundwater PFAS transport. Lives in its
   own inventory DB (mirrors the groundwater inventory model).
2. **Ambient-water PFAS** from agency PDFs that WQP misses → loaded into the production `site.db`
   PFAS map layer (`pfas_station`/`pfas_observation`).

## Data locations (outside the repo; data dir)
- Raw PDFs + extracted CSVs: `/data/SWATGenXApp/GenXAppData/pfas_discovery/`
- Soil inventory DB: `/data/SWATGenXApp/GenXAppData/pfas_discovery/pfas_soil_inventory.db`
  (`pfas_soil_profile`, `soil_source`)

## Canonical soil schema
`pfas_soil_profile(source_id, site_id, boring_id, lat, lon, state, sample_date, depth_top_cm,
 depth_bottom_cm, horizon, ph, toc, moisture_pct, method[direct|TOPA], analyte, value, units,
 qa_flag, mdl, rl, retrieved_at)` — depth-resolved AND vadose-ready (pH/TOC/moisture for Freundlich sorption).

## Method (proven 2026-06-29)
PDF page → `pdftoppm` png 200dpi → **Gemini 2.5-flash vision** → JSON (temp 0). `pdftotext` FAILS on
stacked tables — VLM required even for text-native. Three-gate QA: value-accuracy vs Claude-vision
ground truth, block-recall re-extraction, controlled-vocabulary station-ID reconciliation. Cost ~$0.13
for the pilot corpus.

## Status (2026-06-29)
- SOIL: USGS NH 2021 (ground truth, 2,510 rows/100 sites/50 profiles + pH/TOC) + Kirtland AFB RI (28 rows). 51 multi-depth profiles.
- WATER: NC DEQ ALMP-EC 2023 in prod site.db (18 stations / 146 obs; not in WQP).
- Hard rule: NO overlap with `wqp` (=EPA PFAS Analytic Tools) or `mi_egle`. Public sources only; never private residential wells.

## Next
Scale soil via NYSDEC DECdocs + EPA SEMS + more DoD RIs (Gemini, $100 budget). Add HUC8/12 spatial join. NC PWS drinking water.

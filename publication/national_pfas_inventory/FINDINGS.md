# National Soil-PFAS Inventory — Running Findings Log

Foundation notes accumulated **as we harvest** (methods, sources, decisions, scientific findings).
Publication is the **last** stage (Vahid's explicit go required); this file is the evidence base we
build toward it. Append-only; newest section at top of each list.

---

## Goal
Harvest as much publicly-available PFAS data as possible — **focus: depth-resolved SOIL profiles**
(vadose-zone, ng/g by depth) — record it, build the inventory DB, and (eventually) publish.
Soil-by-depth PFAS is absent from every open structured database → a **national first**.

## Scientific findings (the "why this matters")
- **Chain-length-dependent vertical mobility (vadose signal), observed in real harvested data.**
  Cannon AFB AFFF source zone: PFOS retained near surface (610 ng/g at top → ND with depth) while
  **PFOA leaches deeper** (6 → 22 → 64 ng/g, *increasing* with depth). This is exactly the
  land→vadose→groundwater fractionation that the SWAT+↔MF6 PFAS coupling must reproduce — and it is
  invisible in any aggregated/ambient database. Depth resolution is the whole point.
- pH/TOC/moisture (captured where reported, e.g. USGS-NH) give per-horizon Freundlich Kf/n context for
  sorption — the inventory is *vadose-ready*, not just a measurement dump.

## Method (proven, evolving)
- PDF page → `pdftoppm` PNG @200 dpi → **Gemini 2.5-flash vision** → JSON (temp 0,
  `response_mime_type=application/json`). `pdftotext` FAILS on stacked multi-line tables (20/46 cells)
  → **VLM required even for text-native PDFs**.
- `locate_soil_pages()` pre-filters pages by (PFAS analyte ∧ soil units ∧ depth/SOIL keyword) before
  rendering — caps cost. MAXPAGES=30/report.
- Normalization: depth ft×30.48 / in×2.54 → cm; mg/kg×1000 → ng/g; ng/g ≡ µg/kg.
- **QA gates:** (1) value-accuracy vs Claude-vision ground truth; (2) block-recall re-extraction of
  low-yield pages (Gemini high-precision but can miss a block at page splits — missed the Cane Creek
  hotspot once); (3) controlled-vocabulary station-ID reconciliation (difflib); (4) depth-unit sanity;
  (5) **analyte-name normalization** (full names → canonical abbrevs; case typos PFTEDA→PFTeDA) — TODO.
- Cost: trivial (~$0.13 for pilot corpus; budget $100).

## Scope decision (2026-06-30): SOIL-ONLY — confirmed
The RI/SI reports we harvest are groundwater-heavy (more MW groundwater than soil), and the extractor
**deliberately discards** groundwater/surface-water/sediment (prompt: "SOIL only — SKIP…"). Considered
adding a medium-aware pass (groundwater → a new `pfas_gw_sample` table; ~$5, additive since site-RI MW
data isn't in `wqp`). **Vahid's call: stay soil-only** — keep the depth-resolved vadose differentiator
sharp; groundwater is already well-covered by `wqp`. Do not re-litigate.

## Hard constraints
- **NO overlap** with what's already in prod `site.db`: `wqp` (44,168 obs = EPA PFAS Analytic Tools
  ambient feed) and ALL `mi_egle_*` (Michigan incl. Wolverine/North Kent). Dedup spatially + by source.
- **Public/publishable sources only — NEVER private/residential drinking-water wells.** Soil borings
  yes; residential DW no (even at sites flagged ResidentialWellsSampled=Yes).

---

## Source veins & search depth (the harvest map)

### Confirmed-contaminated-site registries (HIGH-PRECISION SEEDS — every entry has a report)
- **EGLE MPART "Sites and Areas of Interest"** — **387 confirmed Michigan PFAS sites** pulled +
  saved (`pfas_discovery/mi_egle_mpart_confirmed_sites.json`). Types: 118 landfill, 90 industrial,
  29 plating, 22 wastewater, 18 airport, 17 military, 15 fire, 13 paper, +tanneries/dry-cleaners.
  Each has a doc-portal link (RIDE `egle.state.mi.us/RIDE` or MiEnviro `mienviro.michigan.gov`).
  - *Portal note:* MiEnviro is a JS SPA; document API (`{NCoreUrl}ss/documentcontentarchives` POST +
    `DownloadDocumentArchive/{id}`) is CORS/auth-gated — not trivially scriptable. michigan.gov/pfasresponse
    site pages are also JS (no inline PDF hrefs). → harvest MI reports via search/EPA-SEMS instead of
    portal-walking. Registry still valuable as the authoritative confirmed-site seed list.
  - Additive: only North Kent of the 387 overlaps existing `mi_egle` feeds; other 386 soil reports new.
- **EPA federal confirmed-site list** (PFAS Analytic Tools site registry / SEMS) — TODO enumerate as
  the federal analogue. (Its *measurement* feed = `wqp`, excluded; the *site list* as a seed is additive.)

### AFFF military bases (name-driven, seeded from our 948 `pfas_site` installations)
- Works via mirrors: 6/24 marquee bases found accessible (Wayback aec.army.mil, MT DEQ, home.army.mil)
  → Cavazos, Malmstrom, Ft Harrison, Moore, Chaffee, Meade. Most .mil are Akamai/bot-blocked.
- Manual-download (pinned, .mil-blocked): Camp Lejeune (NAVFAC M67001_008778.pdf), Fort Detrick
  (aec.army.mil/Portals/115/PFAS/Fort_Detrick_PFAS_PA_SI.pdf), NAS Patuxent.

### State env-agency document repositories (fetchable; deep-search in progress)
NM HWB (hwbdocs.env.nm.gov), MT DEQ, AK DEC, WA Ecology, NH DES/ME DEP, NY DEC (DECdocs / Socrata
`data.ny.gov/resource/c6ci-rzpg`), CA Geotracker (`geotracker.waterboards.ca.gov/.../deliverable_documents`),
PA/AZ/CO, EPA SEMS (`semspub.epa.gov/work/<region>/<id>.pdf`). USGS ScienceBase for additive ground truth.

---

## Discovery round 1 (2026-06-29) — fan-out workflow `wf_dd328101-410`
12 parallel veins, URL-verified (curl). **110 candidates → 78 worklist (accessible ∧ soil-depth
confirmed) + 30 deferred**, 16 jurisdictions. `pfas_discovery/soil_report_worklist.json`.
- By host: AK DOT&PF airports via Wayback (13) · MI EGLE michigan.gov (9) · WA Ecology (7) ·
  CA GeoTracker (7) · Army AEC/NAVFAC via Wayback (7+2) · MT DEQ (5) · NY DEC (4) · EPA SEMS (3) ·
  AZ ADEQ Luke AFB (3) · NM HWB/env (5) · NH DES (2) · USGS ScienceBase (2) · ME/MN/peer-reviewed.
- Marquee AFFF bases now reachable via Wayback mirrors: Patuxent, Fentress, **Fort Detrick**, Bragg,
  Meade, Sill, Carson, Bliss, Aberdeen (the .mil-blocked manual list is largely solved via web.archive.org).
- Largest single-site sets: FTWHH RI (MT, 304 MB), Saint-Gobain Merrimack NH SI (245 MB),
  Santa Maria Airport CA (104 MB).
- Deferred 30: scanned/needs-OCR (Paine Field FTP, Cedar Springs MI), summary/desktop reports w/o
  depth tables, EPA SEMS legacy 5YR/proposed-plans w/ incidental PFAS, NAVFAC curl -k workplans.

### CA GeoTracker EDF county exports — NON-DEPTH soil (deferred for the vadose product)
The `data_download/edf_by_county/<County>EDF.zip` files are tab-delimited analytical deliverables
(23 cols: COUNTY, GLOBAL_ID, FIELD_PT_NAME, LOGDATE, SAMPID, MATRIX, PARLABEL, PARVAL, PARVQ, UNITS…).
**Merced probe:** 1.42 M total rows → **475 SOIL PFAS rows** (matrix SO/SX/SL in UG/KG, NG/G, NG/KG),
34 analytes, 4 sites. **BUT no depth column and no lat/lon** — depth + coords live in CA's separate
geology/GEO_XY EDF deliverable, not this export. So CA EDF = breadth (soil-surface PFAS concentrations),
NOT depth-resolved. Decision: defer; if we want breadth, parse all 5 counties (~2–3k soil PFAS rows)
and geo-join GLOBAL_ID→GeoTracker site coords. Keeps the headline inventory depth-resolved.

## Inventory state (update each harvest round)

### 2026-06-29 (round 1 — 78-report worklist harvest, parallel VLM)
- `extract_worklist.py` (10-worker thread pool, dedup-by-URL, idempotent): **69 reports loaded, 0
  failed, $3.83 Gemini spend**. Inventory jumped to **15,676 soil rows · 94 multi-depth profiles ·
  83 sources · 17 states**.
- Biggest yields: North Pole Refinery AK **1,802** · FTWHH RI MT (304 MB) **999** · Plattsburgh NY
  **687** · Cannon Phase-1 NM **617** · Lapeer biosolids MI **504** · Fairchild RI WA **417/130** ·
  Swamp Creek Paine WA **410** · Port Huron biosolids MI **311** · Spokane WA **305** · Gabreski +
  Statewide-bg NY **288/285** · Wixom MI **288** · King Salmon AK **270** · Cordova AK **256** ·
  Saint-Gobain supp NH **256** · Gaylord MI **269** · Bethel AK **234** · Great Falls MT **227** ·
  Patuxent MD **216+103** · Vandenberg CA **176** · ME background **174** · Luke AZ **164** · USAFA
  CO **128** · Meade MD **119** · Detrick MD **105** · Carson CO **103** · Sill OK **93** · Bragg NC **76**.
- **Marquee AFFF bases harvested via Wayback** (the .mil-block is solved): Detrick, Meade, Patuxent,
  Aberdeen, Bragg, Sill, Carson — all Army AEC / Navy NAVFAC mirrors.
- **LESSON — locate recall gap:** `locate_soil_pages` (pdftotext heuristic) yields 0 on scanned/
  no-text PDFs (`pages=[]`, "Syntax Error: optional content group") and misses tables on some text
  PDFs (Fairbanks found 1 of 177 pp). → `recover_lowyield.py` renders EVERY page (cap 160) and
  Gemini-extracts, loading only if it beats the existing count. Recovery + round-2 discovery running.
- **QA gate 5 built:** `normalize_analytes.py` — 273 raw analyte strings → canonical abbreviations
  (`analyte_canon` column, raw preserved); isomer prefixes L-/Br-/n- kept distinct to avoid
  double-counting linear+branched vs reported totals; FTS/FTCA family + full-name + case folding.

### 2026-06-29 — post-round-1 QA + state of inventory
**TOTAL: 15,676 rows · 83 sources · 17 states · 74 canonical analytes · 94 multi-depth profiles ·
67% of rows carry an explicit depth.**
- By state: NH 2,859 · AK 2,852 · MT 1,607 · MI 1,549 · WA 1,521 · NY 1,334 · NM 1,067 · TX 765 ·
  MD 567 · AR 522 · CA 263 · CO 231 · ME 174 · AZ 164 · OK 93 · NC 76 · VA 32.
- Depth coverage: 0–30 cm 7,341 · 30–100 cm 751 · 100–300 cm 941 · >300 cm 1,499.
- Analyte normalization (gate 5) DONE: 273 raw strings → 74 canonical (`analyte_canon`, raw preserved);
  15,658/15,676 mapped (99.9%); only true aggregates ("Total PFAS") left NULL. Top: PFOS 2,795 ·
  PFOA 2,196 · PFBS 1,563 · PFHxS 946 · PFNA 912 · …incl. F-53B (9Cl-PF3ONS/11Cl-PF3OUdS 137 each),
  HFPO-DA 234, ADONA 156, FOSAAs, FTS/FTCA families.
- **QA flag (TODO, Gemini-independent): depth-sanity pass.** Deepest parsed depth = 30,449 cm (304 m)
  — implausible for soil (real AFFF borings ~≤12 m). Some >300 cm rows are parse errors (value/sample-id
  leaked into depth, or ft↔cm slip). Add a sanity gate: flag/null depths beyond ~30 m; spot-check the
  >300 cm bucket.

### Depth-sanity QA (gate 6) DONE — `depth_qa` column added
Discriminator = interval SPAN, not absolute depth (deep arid-vadose cores are REAL: King Salmon AK
soil borings to ~26 m, Luke AFB AZ subsurface soil to 321 ft — premium deep-vadose data). Soil
samples are thin intervals; well screens span tens-hundreds of ft.
- **10,359 clean depth-resolved soil rows** (`depth_qa` NULL) · 133 flagged `span_large`
  (>300 cm interval = monitoring-well screen / composite mis-as-soil, e.g. FTWHH-MW19 15–999 ft) ·
  40 flagged `depth_implausible` · 5,144 no-depth (surface/composite). Flagged, NOT deleted
  (provenance preserved; exclude flagged rows from depth-profile analyses).
- Vadose science note: the clean deep cores (AK/AZ/WA arid + cold deep unsaturated zones) are exactly
  what the SWAT+↔MF6 deep-vadose coupling needs — concentration vs depth through thick unsaturated zones.

### BLOCKER (2026-06-29): Gemini monthly spend cap re-hit
After the round-1 worklist run ($3.83 Gemini), the project tripped its **monthly spending cap**
(429 RESOURCE_EXHAUSTED, "exceeded its monthly spending cap" — shared cap with the /ask site
assistant). Round-1's 15,676 rows landed BEFORE the cap (late reports had strong yields → not
truncated). The recovery pass returned 0/$0 entirely because of the cap, NOT a code/data bug — those
~16 reports + recovery are re-runnable once the cap lifts. **`gem()` now fails fast on the cap**
(SpendCapExceeded) so runs abort cleanly instead of silently zero-yielding thousands of pages, with
exponential backoff for transient 429s. Fix = raise cap at https://ai.studio/spend.

### Round-2 discovery DONE — ready to extract when cap lifts
`pfas-soil-discovery-round2` → `soil_report_worklist2.json`: **26 verified reports + 29 deferred**
across 15 states. EPA SEMS, more DoD (Fort Hood/Bliss, Patrick AFB, NRL, Webster Field, NAS Oceana,
JBLM), NASA JPL, NY BCP sites (DecDocs), MN 3M settlement, VT/IA/RI/NH. `extract_worklist.py` now
takes a worklist path arg: `python extract_worklist.py <wl2.json>`.

### 2026-06-29 (round 0 — pilot + first DoD batch)
- DB `pfas_discovery/pfas_soil_inventory.db` (`pfas_soil_profile`, `soil_source`): **2,806 soil rows,
  53 multi-depth profiles**.
  - usgs_nh_2021_soil 2,510 (NH, ground truth, w/ pH/TOC) · dod_af_jbsa_randolph_si 256 (TX) ·
    dod_af_kirtland_ri 28 (NM) · nmed_cannon_ft008_rfi_2026 12 (NM).
  - cannon_si_tables & holloman_phase1 → 0 rows so far (page-location miss; revisit).
- WATER (prod site.db, additive to wqp): nc_deq_almp 18 stations / 146 obs (NC ALMP-EC 2023).
- Gemini spend to date: ~$0.13 of $100.

---

## Open threads / TODO
- 10-report Gemini batch `bmq9mu3il` finishing → inspect the two 0-row reports' page location.
- Discovery fan-out workflow `wf_dd328101-410` → produces `pfas_discovery/soil_report_worklist.json`.
- Generalize `run_soil_batch.py` to consume the worklist.
- Analyte-name normalization pass (5th QA gate).
- HUC8/12 spatial join for NC water stations (NULL).
- Enumerate EPA federal confirmed-site registry as a seed.

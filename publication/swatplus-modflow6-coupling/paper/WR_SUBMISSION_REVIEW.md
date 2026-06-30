# Water Research submission review & checklist
Manuscript: *An automated, public-data SWAT⁺/MODFLOW 6 model for PFAS fate and transport through both surface water and groundwater.*
Compiled 2026-06-27 from a 4-agent review (science · WR compliance · figure-technical · GIS/cartography).

Legend: **P0** submission blocker · **P1** must-fix · **P2** should-fix · **P3** nice-to-have.

---

## A. Science / manuscript (consistency & framing)

- [ ] **P0 — Reconcile "18 parameters" vs the 13-row Morris table.** Text says 18 (`results.tex:223`, `discussion.tex:82`, `supplementary.tex:337`; the 380=20×19 arithmetic confirms 18), but `si_morris_table.tex` shows 13 rows. Either label the table "13 of 18 screened shown" or fix the count. A reviewer will count rows.
- [ ] **P0 — Stop crediting "846 groundwater observations at 1.1 dex".** The metric is over **65 predicted cells** (846 obs → 73 cells → 65 predicted). Fix `conclusions.tex:12-13` and the highlight to say "65 predicted cells (from 846 observations)". The results section already polices this conflation (`results.tex:47-48`), so it's self-inflicted.
- [ ] **P1 — Make the abstract + Highlight 5 carry the body's honesty on the joint calibration** (effective n≈2; "observation-consistent", "plausibly first-order"). Body is exemplary (`results.tex:160-170`); front matter oversells.
- [ ] **P1 — Elevate the fit-free multi-analyte fingerprint decomposition into the abstract** as the primary GW-attribution evidence (currently absent from the abstract; it's the best defense against the small-n critique), and add the **PFOS-only-transport caveat** next to every "both compartments" claim.
- [ ] **P1 — Verify the "≈150 m DEM bias"** (`methods-modflow-generation.tex:43`) — exceeds the basin's ~125 m total head range; reads as a unit error (1.5 m? 15 m?). Correct or explain.
- [ ] **P2 — Add the fitted delivery scalar *g* to the abstract** so "source prescribed, not fitted" isn't read as "nothing fitted to in-stream data".
- [ ] **P2 — Vadose simplification:** add one sentence noting the legacy-source timescale argument is conditional on the (weakly-identified) sorption parameters, and that prescribing the source sidesteps (not resolves) the land→vadose→aquifer flux.
- [ ] **P2 — Consider reordering Results** so the model-free fingerprint precedes the joint calibration (detect → quantify).
- [ ] **P3 — minor:** define "dex = log₁₀ unit" on first use; trim the discussion's re-derivation of the *L*-drop argument (already in results); introduce or drop "RT3D" in the conceptual-figure caption; reconcile "1.4 dex" vs "1.37 dex"; clarify 590 vs 273 channels.

## B. Water Research compliance

- [ ] **P0 — Keywords: 9 → ≤7** (`keywords.tex`). Drop e.g. "Freundlich sorption" + "reproducible modeling".
- [ ] **P0 — Word count ≤ 8,000 incl. references.** Currently ~9,700 incl. refs (body 8,612). Trim ~700–1,700 words, mostly Results (2,522) and Introduction (1,628).
- [ ] **P1 — Bibliography style apalike → Elsevier Harvard** (`elsarticle-harv`) in `main.tex`. Tolerated at first submission, required by proof.
- [ ] **P2 — Suggested reviewers:** prepare 3–5 non-conflicted names for Editorial Manager.
- [ ] **P2 — Zenodo:** publish on acceptance; confirm final license (MIT code + CC-BY-4.0 data).
- [ ] **P3 — Separate figure files** (Figure_1…), each ≥300 dpi / vector, at upload. Optional: shorten the long title.
- Compliant already: abstract 248 w; all 5 highlights ≤82 chars; graphical abstract 1328×531 px; CRediT; competing-interest; data-availability; genAI declaration; ORCID; line numbers; double spacing; cover letter.

## C. Figures — hard-rule blockers & technical

- [ ] **P0 — Remove 4 embedded descriptive titles** in `make_ua_figures.py` (project hard rule: no title on figure, caption only):
  - `:192` `"(a) Deterministic calibration + 5–95% envelope"` → bare `(a)`
  - `:215` `"(b) Predictive uncertainty across reaches"` → bare `(b)`
  - `:233` `"Parameter influence (LHS ensemble)"` → delete (single panel)
  - `:276` `"Per-reach PFOS predictive uncertainty"` → delete (single panel)
  - Move the wording into the LaTeX captions.
- [ ] **P1 — fig3(a):** fix `(a)` tag vs metrics-box overlap. **fig3(b):** move legend out of the map frame (use the below-axis pattern from fig1/2).
- [ ] **P1 — Re-copy regenerated PDFs into `paper/figures/`** — those are stale (Jun 23) and still carry the title-bearing versions. Easy way to ship the wrong figure.
- [ ] **P2 — fig6:** add a legend for blue = +ρ / orange = −ρ. **fig4:** enlarge 5.6 pt legend labels (≥6.5 pt). **graphical_abstract:** regenerate PNG at ≥300 dpi (currently 100; PDF is fine). **conceptual_model:** plan as full-page/landscape (dense nodes + tiny key won't survive column width).
- [ ] **P3 — fig2:** raise vmin / darken basemap so pale low-PFOS reaches don't wash out. **fig7:** thicken reach lines for single-column legibility.
- Good foundations: every body figure is vector PDF, `pdf.fonttype=42` (editable text), colourblind-safe `cmcrameri` batlow/vik, all colorbars carry units, fig4 rasterizes polygons + keeps vector text.

## D. GIS / cartography (high-quality map work — the priority)

Foundations are solid: **EPSG:32616 (UTM 16N)** true-scale, valid scale bars (dx=1 m), batlow/vik colourmaps, NaturalBreaks. Upgrades:

- [ ] **P1 — fig1 study-area locator + context (highest perceived-quality lever):** replace the crude red-dot inset with a **Michigan state outline (TIGER, EPSG:5070) + labeled basin polygon + Grand Rapids reference + neatline**; add a muted basemap under the network (`cx.add_basemap(ax, crs=32616)`, alpha≈0.5); widen the Strahler line-width range; **label the USGS 04118500 gauge + the Rogue mainstem**; add a source/CRS footnote.
- [ ] **P1 — Fix skewed map colorbars:** **fig3(b)** → `LogNorm` (right-skewed; currently all navy, gradient invisible — same fix already used in fig2). **fig7** → reconsider diverging `vik` centered at an arbitrary 1.0 ratio; prefer **sequential batlow** with much thicker evaluated reaches and lighter "not-evaluated" greys so the signal reads.
- [ ] **P2 — Coordinate furniture on all maps:** sparse UTM graticule or corner coordinate labels, neatline/frame, and a "Streams: NHDPlus HR; UTM 16N (EPSG:32616)" footnote — cheap signal of georeferencing rigor.
- [ ] **P2 — fig3(b) point occlusion** near the source cluster: smaller markers + alpha or leader lines; white halo on EGLE station markers in fig7.
- [ ] **P3 — Consistent insets** across fig1/fig3/fig7 (all or none).

---

## Suggested execution order
1. **Figures P0/P1** (title removal + GIS upgrades to fig1/fig3b/fig7) — regenerate, **re-copy PDFs into `paper/figures/`**, recompile.
2. **Science P0** (Morris count, 846→65) + **WR P0** (keywords, word count, bib style).
3. **P1/P2 polish**, then recompile and send `main.pdf`.

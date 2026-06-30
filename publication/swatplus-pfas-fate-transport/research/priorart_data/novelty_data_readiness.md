I have everything I need from the three dossiers. These are synthesis outputs, not research tasks — I'll write them directly.

---

# OUTPUT A — DEFENSIBLE NOVELTY / POSITIONING

## (1) Ranked closest prior models + how we differ

**1. Rafiei & Nejadhashemi 2023, *Water Research* (SMR-W: SWAT-MODFLOW-RT3D) — SAME WATERSHED, our own predecessor.** Closest in subject (Huron PFOS/PFOA, process-based, sediment pathway, ~22 kg/yr PFOS discharge). DIFFER: SWAT+ engine (not classic SWAT-MODFLOW-RT3D); ~3,119 reaches / 72,475 HRUs vs ~189 reaches (~16×); automated/reproducible generation (SWATGenX) vs bespoke; focus on post-source-control recovery trajectory vs source-ID. This cannot scoop us (we own it) but it forecloses "first Huron PFAS model" and forces the delta to be explicit and demonstrated (must show resolution changes the science — e.g., addresses the PFOA underestimation the 2023 paper admitted).

**2. Saló et al. 2025, *Env. Modelling & Software* (point-source pollutants in SWAT+; Arnold + Čerkasova co-authors).** Closest on METHOD — calibrated, in-stream, process-based micropollutant transport built on SWAT+ routines, validated against observed in-river concentrations. DIFFER: pharmaceuticals (ciprofloxacin/venlafaxine), which DEGRADE in-stream, vs PFAS which are conservative and sediment/biosolids-partitioned — genuinely different process content; coarse Catalan basins vs NHDPlus-HR; no sediment-legacy/post-source-control dynamics. This kills any "first organic micropollutant / first point-source pollutant in SWAT+" claim. Must be cited head-on as the antecedent we extend to PFAS.

**3. Shanghai coupled hydrological-multimedia model 2024, *J. Hydrology*.** Closest NON-SWAT competitor — process-based, river-network, water+sediment, PFOS/PFOA, observation-backed, 1990–2022. DIFFER: lumped river-network multimedia/segment-box formulation with no HRU land-phase generation; urban; far coarser segment count (VERIFY < 3,119). Blocks "first process-based / river-network / coupled hydrology+sediment PFAS watershed model." Our claim must carry the "high-resolution, HRU-distributed, NHDPlus-HR-resolved" qualifier.

**4. Raschke et al. 2022, *JEE* 148(9) (SWAT+MODFLOW+WASP, Huron).** Same watershed, same lineage, classic resolution. DIFFER: same axes as #1. Usable as SUPPORT (it names the resolution/extent gap). Cannot scoop us.

**5. Lindim et al. STREAM-EU 2015–2016 (Delft3D-WAQ + E-HYPE; Danube/Europe).** Continental process-based PFOS/PFOA. DIFFER: continental subbasin resolution; its own PFOA validation never reached NSE>0 — the canonical "large but coarse and poorly-constrained" foil. Supports both our resolution claim and our validation-density claim.

**6. Endicott et al. 2025, IEAM (Kent Lake sediment→biota).** Not a watershed model — a two-lake empirical study. DIFFER: empirical, two lakes, no network routing. BUT it already asserts "sediment is an ongoing PFAS source to the food web" qualitatively — so it owns the *mechanism claim*. We must reframe to *quantifying, spatially distributing, and routing* that flux network-wide. Position as validation source, not competitor.

**7. MITRE WaterSHEDs (NHDPlus HR + PFAS, Upper Colorado).** DIFFER: vulnerability/screening index, NOT process-based fate-and-transport (no mass balance/routing). Blocks unqualified "first PFAS model on NHDPlus HR" — always say "process-based fate-and-transport on NHDPlus HR."

## (2) Single strongest defensible novelty sentence

> **"We present the first high-resolution, fully-distributed (HRU- and reach-resolved) process-based PFAS surface-water fate-and-transport model — implemented in SWAT+ on the NHDPlus High Resolution network (3,119 reaches / 72,475 HRUs) — calibrated against a 128-station observed PFOS field and validated against an independent multi-year post-source-control decline trajectory."**

Every qualifier is load-bearing: "high-resolution / HRU-distributed" survives Shanghai and STREAM-EU; "SWAT+ ... PFAS" survives Saló (pharmaceuticals) and the never-PFAS HSPF/INCA engines; "process-based fate-and-transport ... NHDPlus HR" survives MITRE; the resolution numbers survive Rafiei 2023.

## (3) Fallback framings (if a "first" is contested)

- **F1 (engine + substance):** "first PFAS — conservative, sediment/biosolids-partitioned — fate-and-transport implementation in SWAT+," extending the Saló et al. point-source framework to a non-degrading, sediment-coupled contaminant class.
- **F2 (quantified resolution delta, scoop-proof):** "a ~16× reach-resolution successor (189 → 3,119 reaches) to the prior SWAT-MODFLOW-RT3D Huron PFAS model, demonstrating that NHDPlus-HR resolution resolves source localization and sediment dynamics the coarse model could not." Unassailable because we own both endpoints.
- **F3 (validation density):** "the first distributed process-based PFAS model calibrated AND validated against multi-station observed in-stream PFAS and a documented post-treatment decline transient" — leans on STREAM-EU's PFOA validation failure and the box models' non-validation against distributed in-stream data.

## (4) Must-cite prior-art list

1. Rafiei & Nejadhashemi 2023, *Water Research* 240:119437 (DOI 10.1016/j.watres.2023.119437) — predecessor/baseline.
2. Saló et al. 2025, *Env. Modelling & Software* (S1364815225003159) — SWAT+ point-source method antecedent; **cite head-on**.
3. Raschke, Nejadhashemi & Rafiei 2022, *JEE* 148(9), both companion papers (DOIs ...0002033 and ...0002034) — gap-definition.
4. Zhang/Babbar-Sebens et al. 2025, *JEE* 151(11) (DOI 10.1061/JOEEDU.EEENG-8137) — most recent field review; **READ FULL TEXT FIRST** (most load-bearing unread doc; check its reference list for any missed competitor).
5. Shanghai 2024, *J. Hydrology* (S0022169424019887) — closest non-SWAT competitor; **read in full, VERIFY segment count**.
6. Lindim et al. STREAM-EU trio (*Chemosphere* S0045653515301387; *Environ. Pollut.* S0269749115300440; *Water Research* S0043135416305280).
7. Endicott et al. 2025, IEAM 21(4):810 (DOI 10.1093/inteam/vjaf010) — sediment-legacy mechanism owner + our sediment validation source.
8. Zhang et al. 2024 *Env. Sci. Ecotechnol.* (10.1016/j.ese.2024.100473) — Singapore 3D receiving-water branch.
9. Zhu et al. 2024 *Water Research* (10.1016/j.watres.2024.121675) — Elbe fugacity foil (same target journal).
10. MITRE WaterSHEDs (USGS data release) — NHDPlus-HR + PFAS screening precedent.
11. Bailey et al. 2020 gwflow (*Hydrology* 7(4):75) — SWAT+ has constituent scaffold, PFAS unimplemented (handle Bailey-IP attribution carefully).

## (5) SCOOP RISK (address head-on)

**PRIMARY — SERDP/GSI/MSU-IWR group (Newell, Panday, Nejadhashemi). Grade: MODERATE-to-HIGH on TIMING, LOW on existing prior art.** This is our former group; it has the Huron data, SERDP funding, co-author overlap, and an *active* "distributed watershed-scale PFAS model" program (currently SWAT-MODFLOW-WASP + ML/GNN — no public SWAT+ or NHDPlus-HR mention yet). Nothing they have *published* equals our model, but they are the one party positioned to publish a SWAT+ PFAS model concurrently. MITIGATION: prioritize preprint/submission; state the SWAT+ / NHDPlus-HR / 3,119-reach / automation differentiators crisply so a near-simultaneous paper cannot blur the line; monitor *JEE* and *Remediation Journal*.

**SECONDARY — method overlap, Saló et al. 2025 (Grade: MODERATE).** Anticipates the generic SWAT+ point-source mechanism. Not a contaminant/watershed scoop, but a reviewer will surface it. MITIGATION: cite explicitly as the antecedent we extend to PFAS; never claim "first micropollutant in SWAT+."

**RESIDUAL — the unread 2025 ASCE review may already cite a competitor we missed (Grade: unquantified until read).** MITIGATION: pull the PDF and read its reference list end-to-end before finalizing any "first."

---

# OUTPUT B — DATA-READINESS ASSESSMENT

Holdings: 128 EGLE Huron surface-water stations (218 records, the same data as the live sample-level feed — no hidden denser layer). Zero sediment, zero fish, zero in-house USGS PFAS records.

## (i) Calibrate FLOW — **YES.**
6 nested USGS daily-discharge gauges (04172000 Hamburg 308 mi² → 04174500 Ann Arbor 729 mi²; 04174518 Malletts Creek 10.9 mi²) spanning headwater tributaries to outlet, with long decadal records. Ideal for spatially distributed multi-gauge calibration. PREP: none required. Minor: Norton Creek (the principal PFAS-source corridor below Wixom WWTP) is ungauged for discharge — consider a synthetic flow estimate, optional.

## (ii) Calibrate/validate spatial in-stream PFOS — **YES.**
128 EGLE stations across 48 waterbodies is exceptional single-watershed spatial density; this is a spatially-rich snapshot calibration. PREP: **re-ingest the sample-level EGLE REST feed** (`.../EGLE/PfasOpenData/MapServer/0`) to replace the aggregated 10-analyte table — recovers full collection dates, MDL/RL/flags, and the richer analyte set (notably 6:2 FTS, which Endicott shows co-dominant). Clean the `H20` matrix typo on ingest. Zero new fieldwork.

## (iii) Validate temporal trend / post-source-control decline — **PARTIAL (lean YES).**
~10 stations have ≥4 repeats, and they sit exactly where the science is: the Wixom/Norton Creek/Kent Lake source corridor carries clean publicly-documented decline curves (HR-0690: 1,400→6 ng/L PFOS 2018→2020; NC-0010: 5,600→12 ng/L; NC-0030 spanning 2018→2022; HR-0700 a low unimpacted control; 470581 a dense bi-monthly low series). Median per-station depth is thin (~1.7 samples/station). PREP: full sample-level time-series pull (same as ii). FRAME HONESTLY as "spatially-rich snapshot calibration + a small number of multi-year decline series for transient validation" — not dense per-station hydrograph calibration.

## (iv) Validate the SEDIMENT-LEGACY centerpiece — **NO, currently (convertible to PARTIAL/YES with one data action).**
We hold zero sediment PFAS records. The entire centerpiece rests on the **paywalled Endicott et al. 2025** Kent Lake sediment study (ng/g, core counts, Kd/Koc, BSAFs all behind OUP paywall). Without it the sediment-legacy claim is asserted, not demonstrated — and a reviewer in this watershed will catch it. PREP (binding constraint, priority order): (1) **obtain Endicott 2025 full text + SI** via institutional access or author request to Douglas Endicott — extract sediment concentrations, locations/counts, Kd/Koc, BSAFs as both parameters and validation targets (fastest, highest-value); (2) file an EGLE/MPART data request for Kent/Proud Lake sediment + fish from the 2018–2021 investigation (water-only ArcGIS feed confirms these aren't public); (3) ingest the open **Ecology Center / Wu et al. 2023 *Chemosphere* SI** (per-site Huron fish fillet PFOS/ΣPFAS) for an independent bioaccumulation validation layer. **If only one thing happens before submission, secure the Endicott 2025 sediment dataset.**

## SCOPE RECOMMENDATION

- **Domain:** Resolve the HUC8-label discrepancy FIRST — EGLE's Huron feed is HUC8 **04090005**, not 04100013 (which is Clinton/Lake St. Clair). Confirm what the domain polygon actually carries and standardize before any "we cover HUC8 X" sentence; a reviewer here will check. Build at **full HUC8** (the spatial PFOS and flow data support whole-basin calibration), but **anchor the deep validation in the data-rich Wixom–Norton Creek–Kent Lake source sub-basin** where the decline curves, the Endicott sediment, and the fish advisories all concentrate. Full domain for the distributed model; sub-basin for the load-bearing temporal/sediment evidence.
- **Analytes:** Lead **PFOS-primary** — it is where the data density, the decline signal, the advisory, and the sediment/biota dominance all align. Add **6:2 FTS as a secondary** (Endicott shows it co-dominant in sediment and biota, and it's recoverable from the sample-level feed). Treat PFOA and short-chains as exploratory/diagnostic only — coverage is thinner and STREAM-EU's PFOA validation failure is a cautionary precedent. Do NOT promise a multi-analyte validated model.
- **Sediment-legacy claim — framing:** As of TODAY it must be framed as **conditional / future-work-leaning**, because we hold zero sediment data. It converts to a **deliverable RESULT only after Endicott 2025 SI is secured** (parameters + validation targets). Recommended manuscript posture until then: present the high-resolution distributed PFOS calibration + spatial field + post-treatment decline as the firm results; present sediment-legacy quantification/routing as the centerpiece **contingent on the Endicott ingest** — and reframe its novelty as *quantifying, spatially distributing, and routing* the legacy flux network-wide (Endicott already owns the qualitative "sediment is a source" claim, so we cannot claim discovery of the mechanism).

**One-line readiness verdict:** Flow and spatial-PFOS calibration are ready now; temporal decline validation is ready at ~10 corridor stations after a sample-level re-ingest; the sediment-legacy centerpiece is NOT deliverable until the Endicott 2025 sediment dataset is in hand — that single ingest is the difference between a validated paper and an unsupported one.
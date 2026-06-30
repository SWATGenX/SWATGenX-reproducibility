I have full coverage. The MITRE WaterSHEDs model is a useful contrast (NHDPlus HR but vulnerability-scoring, not process-based F&T). Writing the dossier now.

---

# STREAM 1A DOSSIER — SWAT/SWAT+-based PFAS watershed models (novelty threat assessment)

**Bottom line up front:** Your core novelty largely survives. As of June 2026, there is **no published, calibrated, high-resolution, process-based PFAS surface-water fate-and-transport model in SWAT+** anywhere — not for the Huron, not elsewhere. Every direct prior-art SWAT PFAS effort is either (a) the legacy **classic-SWAT + MODFLOW + RT3D/WASP** coupling at ~189 reaches (your own lineage and one sibling), or (b) **SWAT+ pollutant-transport machinery that has never been applied to PFAS**. The two real threats are timing/scooping risks, not existing equivalents: the SERDP/GSI–Nejadhashemi group could publish a SWAT+ PFAS model before you, and a Spanish SWAT+ group has already built (for pharmaceuticals, not PFAS) the generic "point-source pollutant in SWAT+" framework that partly anticipates your *method*. Details and grading below.

---

## TIER 1 — DIRECT PRIOR ART (highest novelty threat)

### 1. Rafiei & Nejadhashemi (2023) — your own predecessor [SUPPORTS / defines the baseline you must exceed]
- **Citation:** Rafiei, V., Nejadhashemi, A.P., et al. "Watershed scale PFAS fate and transport model for source identification and management implications." *Water Research*, vol. 240, 119437 (2023, online May 2023). DOI: 10.1016/j.watres.2023.119437. PubMed 37235893; ScienceDirect S0043135423005092.
- **Model:** "SMR-W" = SWAT (classic) + MODFLOW + **RT3D** reactive transport (Bailey/Wible SWAT-MODFLOW-RT3D lineage). Watershed: **Huron River, SE Michigan** — the *same* watershed you are re-doing.
- **Processes:** PFOS (primary) and PFOA fate/transport via surface runoff, soil lateral flow, sediment-bound transport, groundwater leaching; point + nonpoint sources; biosolids application; ~22 kg/yr PFOS total mass discharge. Reported result: model captured PFOS trends but **underestimated PFOA** ("lack of information from diffusive sources and historical loads").
- **Resolution (your key lever):** classic-SWAT subbasin delineation, **~189 reaches** (per your prompt). This is ~16× coarser than your 3,119 NHDPlus HR reaches.
- **What it did NOT do that you do:** NHDPlus HR reach network; ~3,119 reaches / 72,475 HRUs; SWAT+ (not classic SWAT); automated/reproducible model generation; post-source-control (post-2018 plume/sediment) dynamics.
- **Threat grade: LOW-to-MODERATE.** This is the paper you are explicitly building on, so it cannot "scoop" you — but it *constrains your novelty claim*: you cannot claim "first process-based PFAS model of the Huron." Your honest claim is "first **high-resolution, SWAT+, NHDPlus-HR** process-based PFAS model" and "an order-of-magnitude resolution increase over the prior Huron model, resolving sources/sediment dynamics the 189-reach model could not." Reviewers will demand you show the resolution actually *changes the science* (e.g., resolves the PFOA underestimation, localizes sources). Make that the spine of the contribution.

### 2. Raschke, Nejadhashemi, Rafiei, Fernandez, Shabani & Li (2022) — the SWAT+MODFLOW+WASP Huron sibling [THREATENS the "Huron + integrated model" framing]
- **Citation:** Raschke, A., Nejadhashemi, A.P., Rafiei, V., Fernandez, N., Shabani, A., Li, S.-G. "Opportunities and Challenges of Integrated Large-Scale PFAS Modeling: A Case Study for PFAS Modeling at a Watershed Scale." *J. Environmental Engineering* 148(9), 2022. DOI: 10.1061/(ASCE)EE.1943-7870.0002034. (Companion review: Raschke, Nejadhashemi & Rafiei, "Overview of Modeling, Applications, and Knowledge Gaps for Integrated Large-Scale PFAS Modeling," *JEE* 148(9), DOI .../0002033, 2022.)
- **Model:** SWAT + MODFLOW + **WASP** (streamflow water-quality engine), Huron River. Classic SWAT resolution. PFOS/PFOA. Same watershed, overlapping author team (you are a co-author).
- **What it did NOT do:** SWAT+, NHDPlus HR, high resolution, automation. The companion 2022 review's own stated gap: existing models are "simple… simulating small and isolated systems" — i.e., the *field itself* (including this group) flags low resolution / small extent as the open problem. **Quote that gap; it is your justification.**
- **Threat grade: LOW (and usable AS support).** Same-group prior art you co-authored; it establishes the lineage and, helpfully, names the resolution/extent gap you fill. Cite both 2022 JEE papers as the gap-definition.

### 3. Saló, Estrada, Llorente, Garcia, **Čerkasova, Arnold**, Acuña (2025) — point-source pollutants IN SWAT+ [THREATENS your METHOD novelty, not your PFAS/Huron novelty]
- **Citation:** Saló, J., Estrada, L., Llorente, O., Garcia, X., Čerkasova, N., Arnold, J.G., Acuña, V. "Integrated modeling of the generation, attenuation, and transport of point-source pollutants at the watershed-scale using SWAT+." *Environmental Modelling & Software*, 2025. ScienceDirect S1364815225003159; preprint SSRN 5191943.
- **Model:** Three-part framework: (1) WWTP generation/removal model; (2) **in-stream attenuation + transport of point-source pollutants built on SWAT+ routines**; (3) `pySWATPlus` Python coupling/calibration library. Applied to **ciprofloxacin and venlafaxine** (pharmaceuticals — NOT PFAS) in 3 Catalan River Basin District basins, NE Spain. **Calibrated against observed in-river concentrations.**
- **Why it matters:** This is the closest existing thing to "doing a dissolved organic micropollutant in SWAT+ as a process-based, calibrated, in-stream transport model." It demonstrates the *generic capability* you rely on. Crucially it has **Jeff Arnold and Natalja Čerkasova (SWAT+ core development team)** as co-authors — so the SWAT+ establishment is actively moving into exactly this space.
- **What it did NOT do that you do:** PFAS (they did pharmaceuticals — different sorption/persistence/sediment behavior; PFAS are far more conservative and sediment/biosolids-coupled); high-resolution NHDPlus HR reach network; sediment-bound and post-source-control dynamics; Huron/US setting. Their pollutants degrade in-stream; PFOS does not — your sediment-exchange and source-control story is genuinely different process content.
- **Threat grade: MODERATE.** It weakens any claim of the form "first to transport an organic micropollutant in SWAT+" or "first SWAT+ point-source pollutant framework." **Do not make those claims.** Reframe to substance- and resolution-specific novelty: "first **PFAS** (conservative, sediment/biosolids-partitioned) fate-and-transport implementation in SWAT+, at NHDPlus-HR resolution, with post-source-control sediment dynamics." Cite Saló et al. 2025 explicitly as the methodological antecedent you extend to PFAS — pre-empting the reviewer who finds it.

---

## TIER 2 — ADJACENT / ENABLING WORK (context, mild threat)

### 4. SERDP/GSI "Tier-2" coupled effort (Newell, Panday, Nejadhashemi) — the SCOOP RISK [THREATENS via future publication]
- **Evidence:** Newell (GSI Environmental) + Panday + Nejadhashemi collaborate on PFAS fate/transport with SERDP/GSI support. Newell & Panday 2024 — "Modeling and evaluation of PFOS retention in the unsaturated zone above the water table" (MODFLOW-USG/vadose). Newell 2025, *Remediation Journal*: "Exploration of PFAS Mass Discharge in Stormwater Versus Groundwater" (DOI 10.1002/rem.70052) and "A Long Way to Go: Challenges and Strategies for Managing PFAS in Groundwater" (10.1002/rem.70028). MSU IWR (Nejadhashemi, Director) lists an active **"distributed, watershed-scale PFAS model"** program using **SWAT–MODFLOW–WASP** frameworks plus ML/Graph Neural Nets — *no public mention yet of SWAT+ or NHDPlus HR.*
- **What's published so far:** vadose-zone/groundwater retention and stormwater-vs-groundwater mass-discharge framing. **No published SWAT+ PFAS watershed model from this group as of June 2026.**
- **Threat grade: MODERATE-to-HIGH on TIMING, LOW on existing prior art.** Nothing they have *published* equals your model, but this is the one group with the funding, the Huron data, and the co-author overlap (your former group) to publish a SWAT+ PFAS model concurrently. **Mitigation: priority — get to preprint/submission fast, and state your specific differentiators (SWAT+, NHDPlus HR 3,119 reaches/72,475 HRUs, automation) crisply so a near-simultaneous paper cannot blur the distinction.** Monitor *J. Environmental Engineering* and *Remediation Journal* for this group.

### 5. ASCE 2025 review — "Advances and Research Gaps for PFAS Modeling in Watersheds and Receiving Waters" [SUPPORTS — cite as your gap statement]
- **Citation:** *J. Environmental Engineering* 151(11), 2025, Forum paper. DOI 10.1061/JOEEDU.EEENG-8137. (Gated; ASCE library.)
- **Use:** A 2025 field-wide review explicitly framing watershed/receiving-water PFAS modeling as having open **research gaps**. This is your authoritative, current "the field needs X" citation. Get the full text (library/ILL) to harvest the exact gap language on spatial resolution and process representation — it will be your strongest single justification sentence. **Threat grade: NONE (pure support), HIGH VALUE.**

### 6. SWAT+ gwflow / salt / selenium constituent modules (Bailey et al.) [ENABLING context]
- gwflow physically-based distributed GW module (Bailey et al., *Hydrology* 7(4):75, 2020) now ships with QSWAT+; salt (SO4/Ca/Mg/Na/K/Cl/CO3/HCO3) and selenium constituent transport exist. **No PFAS constituent module exists.** Establishes that SWAT+ has a constituent-transport scaffold but that **PFAS is unimplemented** — supports your "we implement PFAS in SWAT+" novelty. Note the Bailey-IP sensitivity (your memory: gwflow/Bailey) — if you use gwflow, handle attribution carefully. **Threat grade: NONE; supports.**

---

## TIER 3 — NON-SWAT process-based PFAS watershed models (define the broader competitive frontier; minor threat to "high-resolution process-based" superlatives)

- **Shanghai coupled multimedia model** — *Journal of Hydrology*, Dec 2024 (S0022169424019887). **SWMM**-based (not SWAT) urban river-network multimedia PFAS model; PFOA/PFOS in water + sediment, 1990–2022 trends. Process-based, river-network, water+sediment — but urban SWMM, different platform, different region. **Threat grade: LOW** (different engine; but blocks a naked "first process-based watershed PFAS model" claim — qualify with "SWAT+/NHDPlus-HR" or "in the US"). 
- **MITRE WaterSHEDs** (USGS-hosted output, Upper Colorado) — uses **NHDPlus High Resolution** for PFAS *stream-vulnerability scoring* at hex tessellations. **Not process-based fate-and-transport** (no mass balance/routing); it's a screening/vulnerability index. **Threat grade: LOW**, but note it: someone has paired "NHDPlus HR + PFAS," so claim novelty as "**process-based fate-and-transport** on NHDPlus HR," not merely "NHDPlus HR + PFAS."
- Distributed physically-based hydrogeochemical PFAS models in the broader literature (soil/vadose/river/lake) reinforce the 2022 review's "small isolated systems" characterization — your extent + resolution is the differentiator.

---

## NOVELTY VERDICT — what survives, what to drop

**SURVIVES (defensible, specific claims):**
1. **First high-resolution PFAS surface-water fate-and-transport model in SWAT+** (no published SWAT+ PFAS model exists; Saló 2025 did pharmaceuticals, not PFAS).
2. **First PFAS watershed model built on the NHDPlus HR reach network at process-based F&T fidelity** — 3,119 reaches / 72,475 HRUs (MITRE used NHDPlus HR only for vulnerability scoring, not F&T).
3. **~16× resolution increase over the prior Huron model** (3,119 vs ~189 reaches) — provided you *demonstrate it changes results* (source localization; the PFOA underestimation the 2023 model admitted).
4. **Automated/reproducible model generation** (SWATGenX pipeline) for a contaminant model — genuinely absent from all prior PFAS work, all of which were bespoke.
5. **Post-source-control sediment dynamics** — a process-content differentiator vs. the degradable pharmaceuticals in Saló 2025 and a temporal differentiator vs. the 2022–2023 Huron models.

**DROP / DO NOT CLAIM (will be falsified):**
- ✗ "First process-based PFAS model of the Huron" — Rafiei 2023 and Raschke 2022 own that.
- ✗ "First to transport an organic micropollutant / point-source pollutant in SWAT+" — Saló et al. 2025 (with Arnold & Čerkasova) did that for pharmaceuticals.
- ✗ "First PFAS watershed model on NHDPlus HR" (unqualified) — MITRE WaterSHEDs pairs PFAS + NHDPlus HR. Always qualify with "process-based fate-and-transport."
- ✗ "First process-based watershed PFAS model" (unqualified) — Shanghai 2024 (SWMM) exists.

**TWO LIVE RISKS to manage:**
- **Scoop risk (MODERATE-HIGH):** the SERDP/GSI/MSU-IWR group (Newell/Panday/Nejadhashemi) has the data + funding + Huron focus to publish a SWAT+ PFAS model concurrently. Prioritize submission; monitor *JEE* and *Remediation Journal*.
- **Method-overlap risk (MODERATE):** Saló et al. 2025 anticipates the *generic mechanism*. Cite it head-on as the antecedent you extend to PFAS at high resolution; do not let a reviewer surface it.

**OBSERVED-DATA NOTE (flagged for Stream-2 follow-up):** Stream 1A surfaced concrete calibration/validation targets for the Huron — Michigan EGLE's "Investigation of the Occurrence and Source(s) of PFAS in the Huron River Watershed," HRWC monitoring, and your own existing PFAS observation store (your memory: Michigan EGLE 2,439 stations loaded; WQP 44k obs). The 2023 model already calibrated PFOS to ~22 kg/yr discharge in this exact watershed, which confirms a usable observed baseline exists. Confirm spatial/temporal coverage adequacy in the dedicated data-availability stream.

### Sources
- [Rafiei & Nejadhashemi 2023, Water Research — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0043135423005092) · [PubMed 37235893](https://pubmed.ncbi.nlm.nih.gov/37235893/)
- [Raschke et al. 2022, JEE 148(9) "Opportunities and Challenges" (case study)](https://ascelibrary.com/doi/10.1061/(ASCE)EE.1943-7870.0002034) · [companion "Overview… Knowledge Gaps" 0002033](https://ascelibrary.org/doi/10.1061/%28ASCE%29EE.1943-7870.0002033) · [USQ repository record](https://research.usq.edu.au/item/z0299/overview-of-modeling-applications-and-knowledge-gaps-for-integrated-large-scale-pfas-modeling)
- [Saló, Estrada, Llorente, Garcia, Čerkasova, Arnold, Acuña 2025, Env. Modelling & Software — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1364815225003159) · [SSRN preprint 5191943](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5191943)
- [ASCE 2025 review "Advances and Research Gaps for PFAS Modeling in Watersheds and Receiving Waters," JEE 151(11)](https://ascelibrary.org/doi/10.1061/JOEEDU.EEENG-8137)
- [Newell 2025, Remediation Journal — Stormwater vs Groundwater PFAS mass discharge](https://onlinelibrary.wiley.com/doi/10.1002/rem.70052) · [Newell 2025 "A Long Way to Go"](https://onlinelibrary.wiley.com/doi/10.1002/rem.70028)
- [MSU IWR — PFAS Fate and Transport Modeling program](https://www.canr.msu.edu/iwr/Research/pfas-fate-and-transport-modeling)
- [SWAT-MODFLOW-RT3D model library (USF/Bailey-Wible)](https://www.usf.edu/engineering/cee/faculty-projects/gaim-wbmp/model-library/swat-modflow-rt3d.aspx) · [gwflow module for SWAT+ (Bailey et al.)](https://swat.tamu.edu/software/plus/gwflow/) · [Bailey et al. 2020, Hydrology 7(4):75](https://www.mdpi.com/2306-5338/7/4/75)
- [Shanghai coupled hydrological multimedia PFAS model 2024, J. Hydrology](https://www.sciencedirect.com/science/article/abs/pii/S0022169424019887)
- [MITRE WaterSHEDs PFAS vulnerability (NHDPlus HR), USGS data release](https://www.usgs.gov/data/mitre-watersheds-pfas-vulnerability-model-output-upper-colorado-river-basin-1-km-9-km-and-100)
This is a synthesis task with all inputs provided. No tools needed. Producing the package directly.

---

# PAPER-READY JUSTIFICATION PACKAGE
## High-Resolution Process-Based PFAS Surface-Water Fate-and-Transport Model — Huron River Watershed (HUC8 04100013)

---

## 1. MOTIVATION / JUSTIFICATION NARRATIVE (Introduction-ready)

Per- and polyfluoroalkyl substances (PFAS) in surface waters have, over 2024–2026, crossed from an "emerging contaminant of interest" into a regime of enforceable numeric limits — and it is precisely in that regime that predictive, source-resolved watershed modeling becomes a decision tool rather than an academic exercise. In April 2024 the U.S. EPA finalized the first National Primary Drinking Water Regulation for PFAS, setting legally enforceable Maximum Contaminant Levels of 4.0 ng/L for PFOA and PFOS individually (with 10 ng/L limits for PFHxS, PFNA, and HFPO-DA and a Hazard Index for mixtures), and reaffirmed the PFOA/PFOS MCLs in its 2025 reconsideration (Fed. Reg. 2024-07773; EPA 2025). A 4 ng/L threshold sits at the analytical detection floor, which means the *source waters feeding intakes* must be characterized at trace levels — a watershed-loading question, not a treatment-plant question alone. In parallel, EPA's 2024 designation of PFOA and PFOS as CERCLA hazardous substances (Fed. Reg. 2024-08547) imposes strict, joint-and-several liability whose allocation is fundamentally a fate-and-transport attribution problem: which release reached which receptor, by which pathway, in what proportion. And under Clean Water Act §303(d), any PFAS impairment listing triggers a Total Maximum Daily Load — by statutory definition a load-allocation calculation across point and nonpoint sources. Michigan's surface-water program already operationalizes this with in-stream numeric Rule 57 values (PFOS 12 ng/L, PFOA 11 ng/L), the cleanest regulatory hook of all: a model that predicts reach-resolved in-stream concentration outputs the *same quantity the regulation constrains* (Dossier 1, §1).

These regulatory drivers expose four capabilities that monitoring, by construction, cannot supply, and a fifth that defines the scientific problem. First, **source attribution**: a grab sample integrates surface runoff, lateral flow, groundwater discharge, and sediment-bound transport, each with distinct spatial origins; only a model that separately routes each pathway can disaggregate an observed concentration back to contributing sources — the basis for CERCLA "polluter-pays" allocation and cleanup prioritization (Rafiei & Nejadhashemi 2023; Dossier 1, §2). Second, **prediction in ungauged reaches**: PFAS monitoring is structurally sparse — EPA's National Rivers and Streams Assessment is a probability-based survey of a few thousand sites nationally, not a reach census, and the global synthesis of >45,000 samples shows monitoring systematically *underestimates* true burden because only a limited PFAS suite is quantified (Ackerman Grunfeld et al. 2024). A calibrated process model is the only mechanism that yields a mass-conserving concentration at every one of the watershed's reaches (Dossier 1, §3). Third, **counterfactual evaluation**: management decisions are prospective and interventional ("remove the Wixom source," "change biosolids application," "impose a wasteload allocation"), and an intervention acts on a *pathway*, not on a concentration — so counterfactual validity requires a model that encodes the correct causal pathways, which a purely statistical concentration model lacks (Dossier 1, §4; Dossier 2, §b).

The fifth driver is the scientific centerpiece and the most compelling single argument, because it is a published, watershed-specific observation that static, steady-state, or source-control-only reasoning cannot explain. After granular-activated-carbon source control at the upstream Wixom WWTP discharger, Huron/Kent Lake water-column PFOS fell roughly 99% — yet fish-tissue PFOS plateaued *above* the consumption-advisory threshold rather than continuing to decline, with partition coefficients, bioaccumulation factors, and water–sediment–biota patterns consistent with contaminated sediment acting as an ongoing secondary internal source (Endicott et al. 2025, *IEAM* 21(4):810). A plateau-above-threshold despite ~99% external-source removal is the signature of a slowly releasing internal reservoir whose desorption/resuspension timescale outlasts the intervention — a phenomenon that equilibrium or source-inventory accounting cannot reproduce, and that only a time-dependent model with an explicit sediment compartment and sediment–water exchange kinetics can simulate, attribute, and use to forecast recovery time. This is consequential now precisely because Michigan lowered its fish PFOS "Do Not Eat" threshold from 300 to 50 ppb, expanding statewide advisory waterbodies from ~92 to ~188 (Dossier 1, §5; Dossier 4, Obj. 1). The thesis follows directly: monitoring *documented* the plateau but cannot project it forward; a dynamic, sediment-coupled, reach-resolved transport model is required to mechanistically test it, quantify the sediment inventory's contribution, and forecast how long it will sustain exceedance.

**Reviewer-proof framing line (for the Introduction's closing):** *Enforceable in-stream limits and a TMDL apparatus that is, by definition, a load calculation, together convert PFAS management from monitoring to prediction — and a source-resolved, reach-resolved, sediment-coupled process model is the only tool whose native output is the quantity these regulations constrain, at the reaches and under the interventions managers must act on.*

---

## 2. RESOLUTION-ADVANTAGE SUBSECTION (defensible, with honest caveats)

**Heading: Why reach-scale resolution is a methodological advance, not cosmetic refinement.**

The model resolves the Huron (HUC8 04100013) into **3,119 NHDPlus HR channels and 72,475 HRUs**, an ~16.5× increase in stream-network resolution over the authors' prior distributed model of the same watershed (~189 reaches; Rafiei & Nejadhashemi 2023). Three pillars make this consequential, each anchored in established discretization-sensitivity and drainage-area-transfer literature.

**(a) PFOS belongs to the resolution-sensitive constituent class.** The watershed-subdivision literature is unambiguous that streamflow is largely *insensitive* to subbasin count, but sediment- and particulate-associated constituents are strongly sensitive: Jha et al. (2004, *JAWRA* 40:811–825) show that stabilizing sediment loads requires subbasin drainage areas below ~3% of total watershed area (~2% for nitrate, ~5% for phosphorus), and FitzHugh & Mackay (2000, *J. Hydrol.* 236:35–53) show sediment response to coarsening is *biased*, not merely noisy, through a nonlinear source-area relationship. Because PFOS partitions strongly to organic carbon and sediment, it is governed by the same physics that makes sediment the resolution-sensitive class — so the applicable discretization standard is the ~2–5% sediment/nutrient standard, which a 189-reach delineation cannot meet and a 3,119-reach delineation can (Dossier 3, §1).

**(b) The resolution gain is inherited from the input hydrography and restores deleted headwaters.** NHDPlus HR is built on 1:24,000-scale (or better) hydrography plus the 1/3-arc-second 3DEP DEM, versus NHDPlus V2's 1:100,000-scale basis (Moore et al. 2019, *JAWRA* 55:874–898). Medium-resolution networks do not merely lump headwaters — they *omit* them, and first-order streams are the most frequent tributary type and disproportionate sites of in-stream processing owing to high benthic-area-to-volume ratios (Alexander et al. 2007, *JAWRA* 43:41–59). The finer network restores these reaches as explicit modeling units, so the advance is data-supported, not an arbitrary modeling choice (Dossier 3, §2).

**(c) The methodological centerpiece — closest-drainage-area observation-to-channel assignment.** Every PFAS field measurement sits at a real upstream drainage area; assigning it to a model channel introduces a *representativeness error* proportional to the mismatch between the sample's true upstream area and the assigned channel's upstream area. Drainage-area-ratio transfer theory establishes that this error grows monotonically as the area ratio departs from unity, with reliable transfer commonly bounded to a 0.5–1.5 ratio (Asquith et al. 2006, USGS SIR 2006-5286), and Farmer (2018, *J. Hydrol.* 561:872–885) shows explicitly that higher network resolution reduces this representativeness error. At 189 reaches a station is forced onto a coarse aggregate integrating tributaries it never saw; at 3,119 reaches the nearest channel by drainage area is a far tighter match, pulling the assignment ratio toward unity so that the model's reach concentration is compared against an observation that genuinely represents that reach (Dossier 3, §3; Dossier 4, Obj. 3b). This sharpens both calibration targets and source attribution — and, where PFOS loads and the sediment-legacy inventory implicated at Kent Lake are spatially concentrated (the documented norm: ~80% of diffuse load from ~20% of area, Djodjic & Markensten 2018), the finer network resolves contributing reaches that a coarse model would dilution-bias into invisibility (Dossier 3, §4).

**Honest costs and how we mitigate them (state proactively):**

- *Over-parameterization / equifinality.* SWAT+ does not assign independent parameters per reach — transport parameters are class-based (land use, soil, source type), so going 189→3,119 reaches increases the *spatial resolution of prediction* far faster than the *dimension of the calibration vector*. We further constrain the calibration to physically grouped parameters and use global (Morris) sensitivity screening to fix non-influential parameters before fitting — the recognized antidote to equifinality (Dossier 3, §6.1; Dossier 4, Obj. 3a, Obj. 5).
- *Forcing-resolution mismatch.* We do not claim sub-reach certainty in meteorology or PFAS source inventories. The resolution gain we claim is in *network geometry and observation assignment* — quantities genuinely supplied at high resolution by NHDPlus HR + 3DEP — and we treat the coarser forcings as the limiting resolution for source-attribution confidence (Dossier 3, §6.2; Dossier 4, Obj. 3c).
- *Diminishing returns / convergence.* We are not over-resolving past convergence; the Jha et al. ~2–5% thresholds place the 189-reach model on the *non-converged* side and the 3,119-reach model on the converged side. (The airtight demonstration is a subbasin-sensitivity sweep showing load metrics stabilize at our resolution while 189 has not.)
- *Compute cost.* Acknowledged and tractable via parallelization/cloud calibration; an engineering cost, not a scientific barrier, justified by the reach-scale decisions (4 ng/L MCL, 50 ppb advisory) the model informs.

**Caveat on the DAR argument itself (do not overclaim):** the drainage-area-ratio validity bands were derived for transferring *flow* between hydrologically similar catchments, whereas we use closest-drainage-area as a *station-to-reach snapping criterion*. We cite DAR theory as the conceptual scale of acceptable mismatch and the principle that representativeness error grows with area-ratio departure — not as a numerically transferable validity band (Dossier 3, §3 caveat).

**The single highest-payoff figure to harden this section** (recommended, currently a mechanistic rather than measured claim): for the actual Huron PFAS stations, plot the histogram of |log(DAR)| = |log(A_station / A_assigned_reach)| under the 189-reach vs 3,119-reach networks and report the fraction of stations inside the 0.5–1.5 band under each. This converts the strongest mechanistic claim into a measured, reviewer-proof number specific to the data (Dossier 3, §3; Dossier 2, "evidence worth generating").

---

## 3. CONTRIBUTION / NOVELTY STATEMENT (4 sentences)

We present a process-based PFAS surface-water fate-and-transport model of the Huron River watershed built in SWAT+ from NHDPlus HR hydrography, resolving the network into 3,119 channels and 72,475 HRUs — an ~16.5× increase in reach resolution over the prior distributed model of the same watershed (Rafiei & Nejadhashemi 2023) — which for the first time allows each PFAS observation to be assigned to its hydrologically correct channel by closest drainage area rather than to a coarse aggregated subbasin. Unlike that earlier source-apportionment effort, conducted before regulatory source control, this model targets the *post-control regime* in which water-column PFOS has fallen ~99% while fish-tissue PFOS has plateaued above advisory — a decoupling attributed to sediment legacy as a secondary internal source (Endicott et al. 2025) — and uses that divergence as a demanding dynamic validation of the model's water–sediment–biota partitioning that fitting a single concentration series could not provide. Against machine-learning and monitoring alternatives, the contribution is one of *capability rather than goodness-of-fit*: ML occurrence models (e.g., Tokranov et al. 2024) are non-causal and cannot represent the source-control or sediment-remediation interventions that are the regulator's actual levers, and monitoring records the integrated present but cannot attribute, forecast, or evaluate counterfactuals — so we position the process model as the causal/forecasting tier these tools structurally cannot reach, complementary to ML's national occurrence-triage strength. The work is timely because it serves the post-2024 landscape of enforceable 4.0 ng/L PFOA/PFOS MCLs and Michigan's 300→50 ppb fish-tissue threshold, which shift the management question from detection to forecasting and reach-scale intervention design.

---

## 4. CLAIM LEDGER — strongest defensible vs. weaker/hedge

**Deploy as STRONG (main text, reviewer-proof on cited evidence):**
- Monitoring cannot attribute, forecast, or evaluate counterfactuals; the Kent Lake water-down/fish-plateau divergence is the empirical proof case (Endicott et al. 2025). *[Dossier 1 §5; Dossier 2 §a; Dossier 4 Obj.1]*
- A ~99% water-column drop with a fish-tissue plateau is the signature of a slow-release internal sediment source that only a dynamic, sediment-coupled model can simulate. *[Dossier 1 §5]*
- ML predicts occurrence but is non-causal and cannot simulate interventions; counterfactuals require explicit cause-effect structure (Prosperi et al. 2020; Tokranov et al. 2024 as exemplar). *[Dossier 2 §b; Dossier 4 Obj.2]*
- Steady-state/mass-balance screening tools assume away the exact non-steady sediment-legacy dynamics that define the Huron problem. *[Dossier 2 §c]*
- 16.5× finer network → each observation maps to the *right* reach by drainage area; self-evident from reach counts and grounded in representativeness-error theory (Farmer 2018). *[Dossier 2 §d; Dossier 3 §3; Dossier 4 Obj.3b]*
- PFOS is sediment-/OC-associated and therefore belongs to the resolution-*sensitive* constituent class; the applicable discretization standard is sediment's ~2–5% subbasin-area threshold, which 189 reaches fail and 3,119 meet (Jha et al. 2004; FitzHugh & Mackay 2000). *[Dossier 3 §1]*
- The resolution gain is inherited from NHDPlus HR (1:24k vs 1:100k) and restores omitted headwater reaches that dominate loading/processing (Moore et al. 2019; Alexander et al. 2007). *[Dossier 3 §2]*
- Higher reach count refines geometry, not the calibration-vector dimension (class-based parameters) — the over-parameterization charge largely dissolves. *[Dossier 3 §6.1; Dossier 4 Obj.3a]*
- The 2025 ASCE review names spatial resolution, sediment-as-secondary-source, and data sparsity as recognized open gaps — the group's own peer-reviewed framing of the frontier. *[Dossier 2 §d]*
- Enforceable numeric limits (4 ng/L MCL; 11–12 ng/L Rule 57; Michigan 300→50 ppb fish) are reach-scale, in-stream quantities a process model natively outputs. *[Dossier 1 §1; Dossier 4 Obj.1,4]*

**Deploy as MODERATE / Discussion (sound but needs care or added evidence):**
- "Coarse models bias peaks and sediment-water partitioning" — mechanistically sound but a *measured* claim only with a side-by-side 189-vs-3,119 comparison. *[Dossier 2 §d; Dossier 3 §1]*
- "More reaches → better calibration" — reframe strictly as *more observation-to-reach matches at correct support*, not automatic accuracy (more reaches also means more parameters if not class-controlled). *[Dossier 2 §d; Dossier 3 §3.4]*
- In-stream processing fidelity (residence time, sorption/resuspension) improves with finer reaches — structurally true but hard to *prove improved* without reach-scale process data; present as a structural capability, not a demonstrated accuracy gain. *[Dossier 3 §5]*
- National scalability / automated NHDPlus HR→SWAT+ pipeline — real but the *weakest scientific* novelty; frame as reproducibility/transferability in the Discussion, not a core advance, since HR-based SWAT+ generation is increasingly common. *[Dossier 4 Obj.4 #5]*

**HEDGE or AVOID (rhetorically tempting, attackable as worded):**
- Do NOT claim the process model is more accurate than ML at pure interpolation/goodness-of-fit — frame the contrast as *capability* (mechanism, mass balance, counterfactuals), not fit. *[Dossier 2 §b; Dossier 4 Obj.2]*
- Do NOT claim the model *replaces* monitoring — it is the inference/forecasting layer on top of monitoring. *[Dossier 1 §4; Dossier 4 Obj.1]*
- Do NOT state a single "monitoring covers <1% of reaches" percentage — cite the *structural* reason (NRSA is a statistical survey, not a reach census; sampling cannot scale to stream-miles). *[Dossier 1 §3]*
- Do NOT present the sediment-legacy mechanism as a closed mass balance — it is Endicott et al.'s lines-of-evidence inference; frame as the observation our model is positioned to mechanistically *test and quantify* (this turns the weakness into the contribution). *[Dossier 1 §5 honest note; Dossier 4 Obj.5]*
- Do NOT imply the 4 ng/L MCL governs all PFAS — it is PFOA/PFOS only; PFHxS/PFNA/HFPO-DA are 10 ng/L + Hazard Index. If the model addresses only PFOS, say so. *[Dossier 4 corrections]*
- Do NOT claim equifinality is *eliminated* — claim it is *managed* (Morris screening + class-based parameters + uncertainty bands); claiming elimination is a red flag. *[Dossier 4 Obj.3, Obj.5]*
- Do NOT assert DAR numeric validity bands transfer directly to station-snapping — use them as conceptual scale only. *[Dossier 3 §3 caveat]*
- Frame the TMDL hook as "a mechanism now being activated, Michigan as exemplar," not as nationwide PFAS 303(d) practice. *[Dossier 1 §1 caveat]*

---

## 5. KEY CITATIONS TO OBTAIN / VERIFY (by argument)

**A. Regulatory need (Dossier 1 §1, Dossier 4 Obj.1,4) — VERIFIED this session:**
- EPA (2024). PFAS National Primary Drinking Water Regulation. *Fed. Reg.* 2024-07773; 89 FR 32532; PFOA/PFOS MCL = 4.0 ng/L. **[VERIFY current status sentence — 2025 reconsideration extended some deadlines but retained PFOA/PFOS MCLs.]**
- EPA (2024). Designation of PFOA/PFOS as CERCLA Hazardous Substances. *Fed. Reg.* 2024-08547 (eff. Jul 8 2024; reaffirmed Sep 2025).
- Michigan EGLE (2022/2023). Rule 57 surface-water values: PFOS 12 ng/L, PFOA 11 ng/L.
- Michigan fish PFOS Do-Not-Eat 300→50 ppb; limited-consumption ~9→1.5 ppb; advisories ~92→188 (eff. 2025). **[Cite precisely; distinguish the two thresholds.]**
- EPA. CWA §303(d)/TMDL overview; National Rivers and Streams Assessment (statistical-survey framing).

**B. The need for process modeling / source apportionment (Dossier 1 §2–4, Dossier 2):**
- Rafiei & Nejadhashemi (2023). Watershed-scale PFAS fate-and-transport model… *Water Research* 240:120073. PMID 37235893. **[Headline prior work; VERIFY reach denominator = 189 is subbasins/reaches not HRUs, and the ~22 kg/yr PFOS figure, before printing the 16.5× ratio.]**
- Ackerman Grunfeld et al. (2024). Underestimated burden of PFAS in global surface/groundwaters. *Nature Geoscience* 17:340. **[VERIFIED]**
- ES&T Letters (2024). PFAS River Export Analysis… Catchment-Scale Mass Loading Data. *Environ. Sci. Technol. Lett.* **[Independent group framing the gap — strong; verify author list/pagination.]**
- Newell et al. (2025). PFAS mass discharge stormwater vs groundwater. *Remediation Journal.* **[Verify.]**

**C. Vs alternatives — ML & screening (Dossier 2 §b–c, Dossier 4 Obj.2):**
- Tokranov et al. (2024). Predictions of groundwater PFAS occurrence… *Science* 386(6722):eado6638. **[VERIFIED — ML occurrence exemplar.]**
- Prosperi et al. (2020). Causal inference and counterfactual prediction in ML… *Nat. Mach. Intell.* 2:369–375. **[Non-causal ML anchor.]**
- FOCUS (2025). Hydrology-informed geospatial PFAS mapping. arXiv:2502.14894.
- European interpretable-ML PFAS surface-water hazard model (2025). *Environment International* S0160412025002557. **[Verify pagination/authors — publisher 403 this session.]**
- Guo et al. (2020). PFAS vadose-zone screening model. *Adv. Water Resour.* 145:103730. **[Steady-state/screening exemplar.]**

**D. The sediment-legacy centerpiece (Dossier 1 §5, Dossier 3 §4, Dossier 4 Obj.1,5):**
- Endicott, D.D., Silva-Wilkinson, R., McCauley, D., Armstrong, B. (2025). PFAS in sediment: a source of PFAS to the food web? *Integ. Environ. Assess. Manag.* 21(4):810–822. PMID 39903053. **[VERIFIED — the load-bearing observation.]**

**E. Resolution / discretization sensitivity (Dossier 3 §1–2, Dossier 4 Obj.3) — STANDARD, verify in ref manager:**
- Jha, Gassman, Secchi, Gu & Arnold (2004). Watershed subdivision effect on SWAT flow/sediment/nutrients. *JAWRA* 40(3):811–825. **[Strongest anchor — ~3% sediment / ~2% N / ~5% P thresholds.]**
- FitzHugh & Mackay (2000). *J. Hydrology* 236:35–53 (+ 2001, *J. Soil Water Conserv.* 56:137–143).
- Arabi, Govindaraju & Hantush (2006). Subbasin-area threshold corroboration ~2–4%. **[Verify full citation.]**
- Moore, McKay, Rea, Bondelid, Price, Dewald & Johnston (2019). The Road to NHDPlus. *JAWRA* 55(3):874–898.
- USGS (2025). User's Guide for NHDPlus HR. SIR 2025-5031.
- Alexander, Boyer, Smith, Schwarz & Moore (2007). Role of headwater streams in downstream water quality. *JAWRA* 43(1):41–59.

**F. Drainage-area-ratio / representativeness error (Dossier 3 §3) — the novelty hook:**
- Farmer (2018). High-spatial-resolution streamflow estimation… NHD + USGS. *J. Hydrology* 561:872–885. **[Direct "higher resolution reduces representativeness error" citation.]**
- Asquith, Roussel & Vrabel (2006). Statewide drainage-area-ratio analysis. USGS SIR 2006-5286. (+ Stuckey 2006 SIR 2006-5130; Ries & Friesz 2000.)

**G. Critical source areas / hotspot dilution (Dossier 3 §4):**
- Djodjic & Markensten (2018). Critical source areas for erosion and P at high resolution. *Ambio* 48(10):1129–1142.

**H. Method-defensibility / uncertainty (Dossier 4 Obj.3,5) — STANDARD, add from ref manager:**
- Morris (1991). Factorial sampling for preliminary computational experiments. *Technometrics.* (Elementary-effects SA.)
- Saltelli et al. (global sensitivity analysis); Beven & Binley (GLUE / equifinality); Abbaspour et al. (P-factor/R-factor, SWAT-CUP); Vrugt (DREAM) if formal Bayesian UA is performed.

**I. Prediction-in-ungauged-basins framing (Dossier 1 §3):**
- Sivapalan et al. (2003). IAHS Decade on Predictions in Ungauged Basins. *Hydrol. Sci. J.* 48(6):857–880. **[From domain knowledge — verify before final inclusion.]**

**J. Recognized-gap framing — the group's own reviews (Dossier 2 §d):**
- Nejadhashemi group (2025). Advances and Research Gaps for PFAS Modeling in Watersheds and Receiving Waters. *J. Environ. Eng. (ASCE)* 151(11), JOEEDU.EEENG-8137. **[Verify pagination/author order — snippet-confirmed only.]**
- Niu/Nejadhashemi group (2022). Opportunities and Challenges of Integrated Large-Scale PFAS Modeling. *J. Environ. Eng. (ASCE)* 148(9):05022004. **[Verify.]**

**Highest-priority pre-submission verifications:** (1) the 189-reach denominator in Rafiei & Nejadhashemi 2023 — the 16.5× headline ratio must match the prior paper's reported discretization exactly; (2) current EPA MCL deadline status (actively moving in 2025); (3) full-text pagination/author order for the two ASCE reviews and the *Environment International* ML paper (publisher 403 this session); (4) Sivapalan 2003 and Arabi 2006 against the reference manager.

---

**Honest bottom-line on what is strong vs. thin:** The package's spine — Sections 1 (regulatory need), the sediment-legacy centerpiece (Dossier 1 §5 / Dossier 4 Obj.1), the vs-monitoring and vs-ML capability arguments, and the resolution→constituent-sensitivity logic (Dossier 3 §1–2) — is reviewer-proof on cited evidence. The novel centerpiece — closest-drainage-area observation-to-reach assignment (Dossier 3 §3) — is strong *in principle* but currently mechanistic; it becomes airtight only with the |log(DAR)| histogram on the actual Huron stations and a subbasin-sensitivity convergence sweep. The thinnest claims are in-stream processing fidelity (structural, unproven without reach-scale process data) and national-scalability novelty (engineering, not science) — both belong in the Discussion, hedged as written above.
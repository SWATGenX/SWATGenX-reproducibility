I have enough material. The task list is unrelated to this research deliverable, so I'll ignore it. Compiling the dossier now.

---

# STREAM 1 — THE NEED: Why process-based PFAS surface-water fate-and-transport modeling is necessary

A citation-anchored affirmative case. Claims are graded **[STRONG]** (defensible to a skeptical reviewer), **[MODERATE]** (well-supported but with caveats), or **[WEAKER]** (rhetorically useful, flag as motivation not proof).

---

## 1. Regulatory drivers create direct demand for predictive load/concentration models

**[STRONG]** The 2024–2026 regulatory wave converted PFAS from an "emerging contaminant of interest" into an enforceable-numeric-limit problem, which is precisely the regime where predictive watershed models become decision tools rather than academic exercises.

- **Federal MCLs (enforceable).** EPA's final National Primary Drinking Water Regulation (promulgated April 10, 2024; effective June 25, 2024) set legally enforceable MCLs of **4.0 ng/L for PFOA and PFOS individually**, 10 ng/L for PFHxS, PFNA, and HFPO-DA, and a Hazard Index of 1 for mixtures, with compliance required by **2029** (the deadline was extended to 2031 for PFOA/PFOS in the 2025 reconsideration, but EPA explicitly **retained the 4 ng/L PFOA/PFOS MCLs**) (Federal Register, 2024-07773, *PFAS National Primary Drinking Water Regulation*; EPA news release, "EPA Announces It Will Keep Maximum Contaminant Levels for PFOA, PFOS," 2025). A 4 ng/L threshold sits at the analytical detection floor — meaning *source waters feeding intakes* must be characterized at trace levels, which is a watershed-loading question, not a treatment-plant question alone.

- **CERCLA hazardous-substance designation.** EPA designated PFOA and PFOS (plus salts and isomers) as hazardous substances under CERCLA §102(a), effective July 8, 2024 — the first-ever use of §102(a) to list substances not already regulated under another statute (Federal Register 2024-08547, May 8, 2024; Pillsbury *PFAS Observer*, 2024; Bergeson & Campbell, 2024). EPA reaffirmed the designation September 17, 2025. This imposes **strict, joint-and-several liability** on potentially responsible parties (owners/operators, transporters, arrangers). Liability allocation under CERCLA is fundamentally a *fate-and-transport attribution problem*: which release reached which receptor, by which pathway, in what proportion. (Tie to §2 below.)

- **CWA §303(d) / TMDL machinery.** Section 303(d) requires states to list waters not meeting water quality standards and to develop a Total Maximum Daily Load — a quantified pollutant cap allocated across point and nonpoint sources — for each listed pollutant (EPA, "Overview of Identifying and Restoring Impaired Waters under §303(d)"). **A TMDL is, by statutory definition, a loading calculation** (load + wasteload + margin of safety), so any PFAS 303(d) listing creates direct demand for a load-estimation model capable of allocating among sources. **[MODERATE caveat:** PFAS 303(d) listings are still nascent nationally; cite this as a *mechanism that is being activated*, not yet a widespread fait accompli. Michigan's surface-water program is a leading example.]

- **State water-quality standards (the binding numbers in surface water).** Michigan EGLE has derived Part 4 Rule 57 Water Quality Values for five PFAS, with PFOS and PFOA Rule 57 drinking-water-source values of **12 ng/L (PFOS) and 11 ng/L (PFOA)** (EGLE, "EGLE establishes new surface water values," 2022/2023). These are *in-stream* numeric targets — exactly the quantity a surface-water fate-and-transport model predicts at each reach. This is the cleanest regulatory hook for our paper: a model that predicts reach-resolved in-stream concentration outputs the same quantity the regulation constrains.

> **Reviewer-proof framing:** "Enforceable numeric limits (4 ng/L MCL; 11–12 ng/L Rule 57 in-stream values) and a TMDL apparatus that is, by definition, a load-allocation calculation, together convert PFAS management from monitoring to *prediction* — and predictive, source-resolved, reach-resolved concentration is the native output of a process-based surface-water model."

---

## 2. Source identification & apportionment for liability, cleanup prioritization, and "polluter-pays"

**[STRONG]** Monitoring tells you *where* contamination is; only a transport model tells you *where it came from and in what proportion* — the question CERCLA liability and remediation prioritization actually turn on.

- The directly analogous prior work establishes the precedent: a distributed watershed PFAS fate-and-transport model reproduced spatiotemporal PFOS concentrations across the Huron River and **apportioned loads among point and nonpoint sources**, finding surface runoff from urban/industrial areas and biosolids-applied sites to be dominant pathways (Rafiei & Nejadhashemi, 2023, *Water Research*, "Watershed scale PFAS fate and transport model for source identification and management implications," PMID 37235893; total Huron PFOS mass discharge ≈ **22 kg/yr**). This is the canonical citation for "process-based modeling enables source apportionment."

- The mechanistic point that makes apportionment defensible: PFOS/PFOA reach streams by **multiple competing pathways** — surface runoff, lateral flow, leaching to groundwater discharge, and sediment-bound transport — each with different spatial origins (Rafiei & Nejadhashemi, 2023). A grab sample at a reach integrates all of them; only a model that *separately routes each pathway* can disaggregate a measured concentration back to contributing sources. This is the formal basis for "polluter-pays" attribution and for ranking cleanup sites by predicted downstream load reduction.

- Corroborating independent literature: Newell et al. (2025, *Remediation Journal*) on PFAS mass discharge in stormwater vs. groundwater, and the ES&T Letters analysis (2024) arguing the field urgently needs **catchment-scale mass-loading data** rather than concentration snapshots ("PFAS River Export Analysis Highlights the Urgent Need for Catchment-Scale Mass Loading Data," *Environ. Sci. Technol. Lett.*). The latter is a strong reviewer-facing citation: an independent group explicitly framing the gap our model fills.

> **Our high-resolution leverage here:** with **3,119 reaches** vs. ~189 in the prior model, apportionment can be resolved to *individual tributaries and outfall-receiving channels*, not coarse aggregated subbasins — sharpening which PRP/outfall maps to which downstream exceedance. (This is Stream-3 territory but worth signaling.)

---

## 3. Prediction in UNGAUGED reaches — monitoring covers a vanishing fraction of stream miles

**[STRONG]** This is the single most defensible "need" argument, because the arithmetic is stark and uncontested.

- PFAS monitoring is spatially sparse by construction. EPA's National Rivers and Streams Assessment is a *probability-based survey of a few thousand sites nationally every four years* — it estimates national condition statistically, it does **not** characterize specific reaches (EPA, *National Rivers and Streams Assessment*). For a given watershed, observed PFAS data exist at a handful of accessible points; the **3,119 reaches** in our Huron model vastly exceed any feasible sampling campaign.

- The global synthesis quantifies how thin and biased the data are: Ackerman Grunfeld et al. (2024, *Nature Geoscience*, "Underestimated burden of per- and polyfluoroalkyl substances in global surface waters and groundwaters") compiled **>45,000 samples worldwide** and found that **a substantial fraction exceed drinking-water guidance values**, while emphasizing that monitoring *systematically underestimates* true burden because only a limited PFAS suite is quantified. Two usable arguments: (a) even the world's aggregated dataset is small and exceedances are common; (b) measured concentrations are lower bounds, so models calibrated to them must reason about unmeasured reaches and unmeasured compounds.

- The modeling implication is the classic *prediction-in-ungauged-basins (PUB)* problem (Sivapalan et al., 2003, *Hydrol. Sci. J.*, IAHS PUB Decade) transferred to water quality: a physically-based, spatially-distributed model is the only tool that produces a concentration/load estimate at **every** reach, including the >99% never sampled. A statistical/interpolation model cannot honor mass conservation across confluences; a process model can.

> **Reviewer-proof framing:** "Direct measurement will never scale to stream-mile coverage; a calibrated process model is the only mechanism that yields a mass-conserving concentration at every one of the 3,119 reaches, transforming a few dozen observations into watershed-complete, decision-ready coverage."

---

## 4. Scenario / counterfactual testing that monitoring alone cannot answer

**[STRONG]** Monitoring is retrospective and observational; management decisions are prospective and interventional. Only a mechanistic model answers "what if."

- Concrete, regulation-relevant counterfactuals a process model uniquely supports: *remove or treat the Wixom WWTP source* (the actual Huron intervention — a granular-activated-carbon system at the upstream industrial discharger drove the ~99% water-column PFOS decline; Endicott et al., 2025); *change biosolids land-application practice*; *site a new discharge*; *impose a TMDL wasteload allocation and predict resulting in-stream concentration vs. the 11–12 ng/L Rule 57 target.* None of these is observable by sampling — they are forward simulations of an unrealized state.

- The Rafiei & Nejadhashemi (2023) model was explicitly built "for source identification **and management implications**," i.e., to support exactly these scenario runs — the affirmative precedent that watershed PFAS models are used as decision/counterfactual engines, not just reproducers of past data.

- The deeper methodological point (defensible): counterfactual validity requires that the model encode the *correct causal pathways* (runoff vs. sediment vs. groundwater), because an intervention acts on a pathway, not on a concentration. A purely statistical concentration model has no pathway to perturb. This is the strongest theoretical justification for *process-based* over data-driven approaches.

---

## 5. The sediment-legacy problem — why a *dynamic* transport model is needed to explain the fish-tissue plateau

**[STRONG]** This is the paper's scientific centerpiece and the most compelling single argument, because there is a published, watershed-specific observation that *static / steady-state / source-control-only reasoning cannot explain.*

- The observation: after source control at the upstream discharger, Huron/Kent Lake **water-column PFOS fell ~99%**, yet **fish-tissue PFOS plateaued above the consumption-advisory threshold** rather than continuing to decline (Endicott, Silva-Wilkinson, McCauley & Armstrong, 2025, *Integrated Environmental Assessment and Management* 21(4):810–822, "Per- and polyfluoroalkyl substances (PFAS) in sediment: a source of PFAS to the food web?", PMID 39903053). Partition coefficients, bioaccumulation factors, and water–sediment–biota PFAS patterns (including 6:2 FTS corroboration) are **consistent with contaminated sediment acting as an ongoing internal secondary source**.

- Why this *demands* a dynamic transport model: a plateau-above-threshold despite ~99% external-source removal is the signature of a **slowly-releasing internal reservoir** (sediment desorption/resuspension) whose timescale exceeds the source-control intervention. Equilibrium or source-inventory accounting predicts continued decline; only a **time-dependent model with an explicit sediment compartment, sorption/desorption kinetics, and sediment–water exchange** reproduces a decoupling of water-column and fish-tissue trajectories. The Rafiei & Nejadhashemi (2023) model already identified **sediment transport as a notable PFOS release pathway** — establishing that the SWAT+/erosion-coupled framework carries the sediment process needed to represent this legacy term.

- Regulatory urgency that makes the plateau consequential: Michigan **lowered the PFOS fish "Do Not Eat" threshold from 300 ppb to 50 ppb** (and the limited-consumption threshold from 9 to 1.5 ppb), which **expanded statewide Do-Not-Eat advisory waterbodies from ~92 to ~188** (EHN, 2024; Great Lakes PFAS Action Network; Bridge Michigan, 2025). So the very legacy term that explains the plateau now governs whether a waterbody trips a far stricter advisory — raising the bar a fate-and-transport model must clear.

> **Reviewer-proof framing (the thesis sentence):** "A ~99% water-column PFOS reduction that nonetheless leaves fish tissue plateaued above advisory is, by construction, evidence of an internal sediment source whose release kinetics outlast source control — a phenomenon that *monitoring documents but cannot project forward, and that only a dynamic, sediment-coupled, reach-resolved transport model can simulate, attribute, and use to forecast recovery time.*"

---

## Synthesis: the five drivers compose into one argument

| # | Driver | What monitoring gives | What only a process model gives | Strength |
|---|--------|----------------------|--------------------------------|----------|
| 1 | Enforceable limits (4 ng/L MCL; 11–12 ng/L Rule 57; TMDL = a load calc) | Pass/fail at sampled points | Reach-resolved predicted concentration vs. the numeric target; load allocation | STRONG |
| 2 | CERCLA liability / polluter-pays | Where contamination is | Which source, which pathway, what fraction | STRONG |
| 3 | Ungauged reaches (NRSA = thousands of sites nationally; our model = 3,119 reaches) | A few dozen observations | Mass-conserving estimate at *every* reach | STRONG |
| 4 | Scenario/counterfactual (remove Wixom source, change biosolids, impose WLA) | The observed past only | Forward simulation of unrealized interventions | STRONG |
| 5 | Sediment legacy / fish-tissue plateau | Documents the plateau | Explains and forecasts it via dynamic sediment–water exchange | STRONG |

**Honest weak points to pre-empt:** (a) PFAS-specific 303(d)/TMDL listings are still emerging — frame §1's TMDL hook as *a mechanism now being activated*, with Michigan as the leading exemplar, not as nationwide practice. (b) "Monitoring covers <1% of reaches" is rhetorically powerful but cite the *structural* reason (NRSA is a statistical survey, not reach census; sampling cannot scale to stream-miles) rather than a single contested percentage. (c) The sediment-legacy causal claim is *Endicott et al.'s* (lines-of-evidence, not a closed mass balance) — present it as the observation our model is positioned to *mechanistically test and quantify*, which turns a possible weakness into the paper's contribution.

---

### Key references (real, verified this session)
- Ackerman Grunfeld, D., Gilbert, D., Hou, J., Jones, A.M., Lee, M.J., Kibbey, T.C.G., O'Carroll, D.M. (2024). Underestimated burden of PFAS in global surface waters and groundwaters. *Nature Geoscience* 17:340. https://www.nature.com/articles/s41561-024-01402-8
- Endicott, D., Silva-Wilkinson, McCauley, Armstrong (2025). PFAS in sediment: a source of PFAS to the food web? *Integr. Environ. Assess. Manag.* 21(4):810–822. PMID 39903053. https://pubmed.ncbi.nlm.nih.gov/39903053/
- Rafiei, V. & Nejadhashemi, A.P. (2023). Watershed scale PFAS fate and transport model for source identification and management implications. *Water Research*. PMID 37235893. https://pubmed.ncbi.nlm.nih.gov/37235893/
- EPA (2024). PFAS National Primary Drinking Water Regulation. *Fed. Reg.* 2024-07773. https://www.federalregister.gov/documents/2024/04/26/2024-07773/pfas-national-primary-drinking-water-regulation
- EPA (2024). Designation of PFOA and PFOS as CERCLA Hazardous Substances. *Fed. Reg.* 2024-08547. https://www.federalregister.gov/documents/2024/05/08/2024-08547/
- EPA. Overview of Identifying and Restoring Impaired Waters under §303(d) of the CWA. https://www.epa.gov/tmdl
- EPA. National Rivers and Streams Assessment. https://riverstreamassessment.epa.gov/webreport/
- Michigan EGLE. New surface water values for PFAS (Rule 57: PFOS 12 ng/L, PFOA 11 ng/L). https://www.michigan.gov/egle/newsroom/mi-environment/2023/10/25/
- ES&T Letters (2024). PFAS River Export Analysis Highlights the Urgent Need for Catchment-Scale Mass Loading Data. https://pubs.acs.org/doi/10.1021/acs.estlett.4c00017
- Michigan PFOS fish "Do Not Eat" threshold 300→50 ppb; advisories ~92→188 waterbodies. EHN (2024); Bridge Michigan (2025); Great Lakes PFAS Action Network. https://www.ehn.org/michigan-expands-do-not-eat-fish-warnings-as-pfas-levels-prompt-tighter-safety-standards
- Sivapalan, M. et al. (2003). IAHS Decade on Predictions in Ungauged Basins (PUB). *Hydrol. Sci. J.* 48(6):857–880. [prediction-in-ungauged-reaches framing; from domain knowledge, verify before final inclusion]
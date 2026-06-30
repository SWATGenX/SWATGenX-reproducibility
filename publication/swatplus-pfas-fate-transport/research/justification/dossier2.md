I now have enough verified material across all four alternative categories plus the regulatory and watershed-model anchors. I'll synthesize the dossier. The 2025 ASCE review (JOEEDU.EEENG-8137) and the Niu/Rafiei 2023 paper are real and confirmed via search snippets; I'll cite them at the level the snippets support and flag any claim I couldn't verify in full text.

---

# STREAM 2 — THE GAP vs ALTERNATIVES
## Why distributed, process-based modeling is the right tool for PFAS surface-water fate-and-transport — and what each alternative structurally cannot do

This dossier is organized as a defensible "why-our-approach" argument. Each subsection (a–d) names a competing method class, states precisely what it *cannot* do that a spatially-distributed process model *can*, anchors the claim in real literature, and grades the claim's strength so you can deploy the strong ones in the main text and reserve the weaker ones for the Discussion.

A unifying thesis to state up front (and reuse in the abstract): **PFAS management questions in surface water are fundamentally causal, spatial, dynamic, and counterfactual** — "If we control source X, by how much and how fast will reach Y and the downstream impoundment respond, and will the sediment legacy keep fish above advisory?" Only a distributed, mechanistic transport model answers questions of that *form*. Monitoring measures the present, ML predicts occurrence, screening tools bound a steady-state average, and lumped models blur the very reach-scale heterogeneity that source control acts on. The Huron is the ideal proving ground because it is a watershed where the causal question has already been forced into the open: water-column source control at the Wixom WWTP produced a ~99% PFOS drop, yet fish-tissue PFOS plateaued *above* advisory, attributed to a sediment legacy acting as a secondary internal source (Endicott et al. 2025). That is a question monitoring *posed* but cannot *resolve* — it requires a model that carries a sediment compartment through space and time.

---

## (a) MONITORING — measures the present; cannot attribute, forecast, or evaluate interventions

**What monitoring is.** Direct field sampling of water, sediment, and biota with targeted LC-MS/MS (e.g. EPA Methods 533/537.1/1633). It is the ground truth and the indispensable model input — but it is, structurally, a set of point-in-space, point-in-time observations.

**What it structurally cannot do (vs. a distributed process model):**

1. **Cannot attribute concentration to source.** A measured concentration at a reach is the *integrated* result of all upstream point + nonpoint loads, in-stream transport, dilution, sediment exchange, and degradation. Monitoring records the sum; it cannot decompose it. A distributed model with explicit source terms on individual reaches *partitions* an observed concentration into its contributing sources — exactly what Rafiei & Nejadhashemi (2023, *Water Research* 240:120073) built their Huron SWAT-MODFLOW(-RT3D) model to do, finding surface runoff and urban/industrial sites as dominant PFOS contributors and sediment transport as a notable release pathway. Attribution is a *model output*, not a *monitoring output*. **(Strong.)**

2. **Cannot forecast.** Monitoring is retrospective by definition. The regulator's question — "will reach Y exceed the 4 ng/L MCL next year, or after this source is controlled?" — is a forward simulation question. **(Strong.)**

3. **Cannot evaluate counterfactual interventions.** You cannot sample a watershed under a management scenario that has not happened. The Kent Lake case is the canonical demonstration: monitoring *detected* the post-GAC plateau above the Do-Not-Eat threshold and *hypothesized* a sediment source (Endicott et al. 2025, *Integ. Env. Assess. Manag.* 21(4):810), but only a model carrying a sediment compartment can quantify how long the legacy will sustain exceedance and whether sediment remediation would change the trajectory. **(Strong — this is your headline.)**

4. **Sparse and snapshot-limited by cost.** PFAS analysis runs roughly $190–$240 per drinking-water sample (single-method), and the EPA NPDWR's own quantified compliance cost is ~$1.55 billion/yr with AWWA estimating $37–48 billion in capital over five years (EPA 2024 PFAS NPDWR, 89 FR 32532; AWWA 2024). This cost makes dense spatiotemporal coverage infeasible — UCMR-class programs miss >90% of small systems (Tokranov et al. 2024 motivation). A calibrated model *interpolates and extrapolates* the watershed continuously between the sparse, expensive samples. **(Strong; cite EPA + AWWA for the cost numbers.)**

> **Framing line for the paper:** "Monitoring answers *what is*; management requires *what caused it*, *what comes next*, and *what if we act* — questions that are model outputs, not sample outputs."

---

## (b) MACHINE-LEARNING / correlative models — predict occurrence; not causal, cannot simulate interventions, data-hungry

**Exemplars (real, citable):**
- **Tokranov et al. 2024, *Science* 386(6722):eado6638** — national XGBoost (extreme gradient boosting) model predicting PFAS *occurrence* in groundwater at drinking-water-supply depths across CONUS; key predictors were urban land use and well depth; estimated 71–95 million people rely on groundwater with detectable PFAS pre-treatment.
- **European surface-water ML hazard model**, Cordner-style interpretable ML (*Environment International* 2025, S0160412025002557) — predicts PFAS hazard in European surface waters from geospatial covariates.
- **FOCUS framework** (arXiv 2502.14894, 2025) — hydrology-informed deep learning for surface-water PFAS mapping.

**What this class structurally cannot do (vs. a distributed process model):**

1. **Not causal — predicts occurrence, not mechanism.** XGBoost and kin learn statistical associations between covariates (land use, well depth, proximity) and observed PFAS. Association cannot distinguish correlation from causation without explicit causal assumptions/structure (Prosperi et al. 2020, *Nat. Mach. Intell.* 2:369; broader: "neither the parameters nor predictions of data-driven models necessarily have a causal interpretation"). A process model encodes the mass-balance physics *a priori*, so its loadings, fluxes, and sediment exchange *are* causal terms. **(Strong.)**

2. **Cannot simulate interventions / counterfactuals.** A correlative model has no representation of "remove the Wixom load" or "cap the contaminated sediment" — those are interventions on variables the model only observed passively. Counterfactual estimation requires a specified cause-effect structure and assumptions that purely predictive ML does not carry (Prosperi et al. 2020). This is the single most important distinction for *management*: the regulator's lever (source control, sediment remediation) is precisely a counterfactual the ML model cannot represent. **(Strong.)**

3. **Needs dense training data and does not transfer to data-poor reaches.** ML accuracy is bounded by the density/representativeness of labeled samples; Tokranov et al. trained on USGS NWQN + California GAMA networks. Reaches or watersheds without training coverage get high-variance predictions. A process model, by contrast, is transferable by *physics* — it runs on a watershed it was never "trained" on, given terrain, land use, and loads. **(Strong, but note: process models also need calibration data — frame as "ML needs labels *everywhere*; process models need calibration *somewhere* and then extrapolate by conservation laws.")**

4. **No spatial transport dynamics, no temporal trajectory.** Occurrence models output a probability/concentration *field*, not a *time series of fluxes through a connected network*. They cannot tell you the travel time of a load pulse to Kent Lake, the in-channel sediment-water partitioning en route, or the recovery half-time after source control. **(Strong.)**

> **Honest caveat to pre-empt the reviewer:** ML and process models are *complementary*, not rivals — ML is excellent for *national screening / occurrence triage* (its strength), and can even inform process-model priors or boundary conditions. Position your model as the tool for the *causal/management* tier that ML cannot reach, rather than claiming ML is "wrong." A reviewer will reward this nuance and punish overclaiming. **(This nuance is itself a defensible, strengthening move.)**

---

## (c) SCREENING / STEADY-STATE / MASS-BALANCE tools — bound an average; no space, no dynamics

**What they are.** Spreadsheet-class or single-compartment models assuming no accumulation (steady state) — e.g. fugacity/mass-balance "level" models and PFAS vadose-zone screening tools (Guo et al. 2020, *Adv. Water Resour.* 145:103730; the broader steady-state surface-water mass-balance family). Useful for first-order load bounding and prioritization.

**What they structurally cannot do (vs. a distributed process model):**

1. **No spatial transport.** A mass-balance box treats a sub-catchment or reach as well-mixed with a single concentration; there is no routing, no longitudinal gradient, no connectivity. It cannot place a concentration on a *specific reach* or trace a plume downstream. **(Strong.)**

2. **No dynamics — steady state assumes the legacy away.** Steady-state tools assume "no accumulation of substance" — which is precisely the assumption the Kent Lake sediment legacy *violates*. A secondary internal source that sustains a fish-tissue plateau *is* a non-steady, storage-and-release phenomenon. A steady-state screen cannot, by construction, represent a sediment reservoir slowly bleeding PFOS back into the water column. **(Strong — and rhetorically powerful: the alternative's core assumption is exactly the phenomenon you're studying.)**

3. **No reach-scale heterogeneity, no event response.** Cannot represent storm-driven runoff pulses, biosolids hotspots, or the differential behavior of 3,119 distinct channels. **(Strong.)**

> **Use line:** "Steady-state mass balance answers 'what is the long-run average load?'; it is structurally blind to the storage-and-release dynamics — the sediment legacy — that define the Huron management problem."

---

## (d) LUMPED / COARSE watershed models — miss reach-scale heterogeneity (the direct methodological-advance argument)

This is where your headline numbers do the work, and where the contrast is *internal to your own lineage* — a strong, hard-to-rebut framing.

**The quantified advance:**
- New NHDPlus-HR SWAT+ Huron model (HUC8 04100013): **72,475 HRUs, 3,119 stream reaches/channels**.
- Authors' prior model (Rafiei & Nejadhashemi 2023, same watershed, SWAT-MODFLOW-RT3D): **~189 subbasins/reaches**.
- **~16.5× finer stream network** (3,119 / 189).

**What coarse/lumped resolution structurally cannot do:**

1. **Cannot map a field measurement to the *right* channel.** With 3,119 reaches, each PFAS observation is assignable to a *specific* reach by closest drainage area — a station lands on one ~specific channel, not a coarse aggregate of many tributaries. At 189 reaches, a single modeled reach is the spatial average of ~16× more drainage area, so an observation is forced onto an aggregated reach whose simulated concentration is a dilution-blurred mixture. **This is a precision-of-attribution argument, and it's your strongest methodological claim because it is concrete, quantified, and self-evidently true from the reach counts.** **(Strong.)**

2. **Cannot resolve sub-aggregate source heterogeneity.** A point source (Wixom WWTP outfall to Norton Creek) and a diffuse biosolids field within the same 189-model subbasin are lumped into one reach load. The high-resolution network *separates* them onto distinct channels, enabling differential source attribution and differential management. Recall Rafiei & Nejadhashemi 2023 already found biosolids-application sites as distinct sediment-PFOS sources — resolving them spatially is the natural next methodological step. **(Strong.)**

3. **Aggregation error in transport and partitioning.** Coarser reaches over-mix and over-dilute, biasing both peak concentrations and sediment-water partitioning estimates. Finer routing better preserves the longitudinal concentration gradient that a regulator compares against a 4 ng/L MCL at a *specific* intake. **(Defensible, but quantify if you can — see "evidence to add" below; without a side-by-side this is a mechanistic argument, not yet a measured one.)**

4. **Calibration leverage.** ~16× more reaches means more places where simulated values can be checked against (and constrained by) the sparse-but-real monitoring network — improving identifiability of source terms. **(Moderate — true in principle, but more reaches also means more parameters; frame carefully as "more observation-to-reach matches," not "automatically better calibration.")**

**Independent literature support for the resolution argument:** The recent review by the Nejadhashemi group, **"Advances and Research Gaps for PFAS Modeling in Watersheds and Receiving Waters"** (*J. Environ. Eng. (ASCE)* 151(11), 2025, JOEEDU.EEENG-8137), explicitly catalogs spatial resolution, sediment-as-secondary-source representation, and data sparsity as open gaps — a citable, on-point statement that high-resolution distributed representation is a recognized research frontier, not a vanity refinement. The same group's earlier ASCE case study (*J. Environ. Eng.* 148(9):05022004, 2022, "Opportunities and Challenges of Integrated Large-Scale PFAS Modeling") flagged underestimation of PFOA from diffuse sources and historical loads — i.e. exactly the heterogeneity finer resolution is meant to recover. **(Strong — these are the group's own peer-reviewed framing of the gap.)**

---

## Synthesis table (drop-in for the paper)

| Method class | Causal? | Spatial transport? | Dynamics / legacy? | Simulate interventions? | Data demand | Right job |
|---|---|---|---|---|---|---|
| **Monitoring** | No (records sum) | N/A (points) | Snapshot only | No | $$$ per sample, sparse | Ground truth / calibration |
| **ML occurrence (Tokranov 2024)** | No (correlative) | No (static field) | No | No | Dense labels everywhere | National occurrence triage |
| **Steady-state mass balance** | Partial | No | No (assumes none) | Crude | Low | First-order load bounding |
| **Lumped/coarse watershed (~189 reach)** | Yes | Coarse | Yes but blurred | Yes, coarsely | Moderate | Regional averages |
| **High-res distributed (ours, 3,119 reach)** | **Yes** | **Reach-scale** | **Yes (sediment compartment)** | **Yes, reach-specific** | Moderate + monitoring | **Causal, reach-scale management + forecast** |

---

## Strength ledger (so you deploy claims at the right confidence)

**Deploy as strong / main-text:**
- Monitoring cannot attribute, forecast, or evaluate counterfactuals — Kent Lake is the proof case (Endicott et al. 2025).
- ML predicts occurrence but is non-causal and cannot simulate interventions (Prosperi et al. 2020; Tokranov et al. 2024 as the occurrence exemplar).
- Steady-state tools assume away the exact sediment-legacy dynamics that define the Huron problem.
- 16.5× finer network → each observation maps to the *right* reach by drainage area (self-evident from counts).
- The 2025 ASCE review names spatial resolution + sediment secondary source + data sparsity as open gaps.

**Deploy as moderate / Discussion, ideally with added evidence:**
- "Coarse models bias peaks/partitioning" — mechanistically sound but needs a side-by-side 189-vs-3,119 comparison to be a *measured* claim.
- "More reaches → better calibration" — reframe as more observation-to-reach matches, not automatic accuracy.

**Explicitly concede (this strengthens you with reviewers):**
- ML and screening tools are complementary at the national/triage tier; you are not displacing them but occupying the causal/management tier they cannot reach.
- Process models still require calibration data; the advantage is *physics-based extrapolation from somewhere*, vs. ML's need for *labels everywhere*.

**Evidence worth generating to harden the case (optional, high payoff):** a direct head-to-head where the same PFAS observation set is assigned to the 189-reach vs 3,119-reach network, reporting (i) the drainage-area mismatch / mis-assignment rate at coarse resolution, and (ii) the change in simulated vs observed concentration error. That single figure converts your strongest *mechanistic* claim (d-1, d-3) into a *measured* one and would be very hard for a reviewer to contest.

---

## Verified references (real; author/year/venue)
- Rafiei, V. & Nejadhashemi, A.P. (2023). Watershed scale PFAS fate and transport model for source identification and management implications. *Water Research* 240:120073. (Huron, SWAT-MODFLOW; surface runoff + urban/industrial dominant; sediment/biosolids pathway.)
- Endicott, D., Silva-Wilkinson, R., McCauley, D., Armstrong, B. (2025). PFAS in sediment: a source of PFAS to the food web? *Integrated Environmental Assessment and Management* 21(4):810. (Kent Lake; post-GAC fish-tissue plateau above advisory; sediment as secondary internal source.)
- Nejadhashemi group (2025). Advances and Research Gaps for PFAS Modeling in Watersheds and Receiving Waters. *J. Environ. Eng. (ASCE)* 151(11), JOEEDU.EEENG-8137.
- Niu/Nejadhashemi group (2022). Opportunities and Challenges of Integrated Large-Scale PFAS Modeling: A Case Study at a Watershed Scale. *J. Environ. Eng. (ASCE)* 148(9):05022004. (Diffuse-source/historical-load PFOA underestimation noted.)
- Tokranov, A.K., et al. (2024). Predictions of groundwater PFAS occurrence at drinking water supply depths in the United States. *Science* 386(6722):eado6638. (National XGBoost occurrence model; 71–95M people.)
- Prosperi, M., et al. (2020). Causal inference and counterfactual prediction in machine learning for actionable healthcare. *Nature Machine Intelligence* 2:369–375. (Predictive ML ≠ causal; counterfactuals need cause-effect structure.)
- European interpretable-ML PFAS surface-water hazard model (2025). *Environment International*, S0160412025002557.
- FOCUS: Hydrology-Informed Noise-Aware Learning for Geospatial PFAS Mapping (2025). arXiv:2502.14894.
- U.S. EPA (2024). PFAS National Primary Drinking Water Regulation. 89 FR 32532 (eff. June 25, 2024); PFOA/PFOS MCL = 4.0 ng/L; quantified cost ~$1.55B/yr. AWWA (2024) capital estimate $37.1–48.3B/5 yr.
- Guo, B., et al. (2020). A screening model for quantifying PFAS leaching in the vadose zone. *Advances in Water Resources* 145:103730 (screening/steady-state exemplar).

**Citations I could NOT open in full text (publisher 403) and verified only via search snippets — confirm volume/page/exact author list before submission:** Rafiei & Nejadhashemi 2023 (confirmed via PubMed 37235893), the 2025 ASCE review (JOEEDU.EEENG-8137), the 2022 ASCE case study, and the European *Environment International* ML paper. All four exist and are on-point; only the precise pagination/author order needs a final check against the publisher record.

Sources:
- [Tokranov et al. 2024, Science](https://www.science.org/doi/10.1126/science.ado6638)
- [USGS national PFAS groundwater model](https://www.usgs.gov/programs/environmental-health-program/science/a-national-predictive-model-pfas-occurrence)
- [Rafiei & Nejadhashemi 2023, Water Research (PubMed)](https://pubmed.ncbi.nlm.nih.gov/37235893/)
- [ASCE 2025 review — Advances and Research Gaps for PFAS Modeling](https://ascelibrary.org/doi/10.1061/JOEEDU.EEENG-8137)
- [ASCE 2022 case study — Integrated Large-Scale PFAS Modeling](https://ascelibrary.com/doi/10.1061/(ASCE)EE.1943-7870.0002034)
- [Endicott et al. 2025, IEAM (PubMed)](https://pubmed.ncbi.nlm.nih.gov/39903053/)
- [European interpretable ML PFAS surface-water model, Environment International 2025](https://www.sciencedirect.com/science/article/pii/S0160412025002557)
- [FOCUS geospatial PFAS deep-learning framework, arXiv](https://arxiv.org/html/2502.14894)
- [Prosperi et al. 2020, Nature Machine Intelligence](https://www.nature.com/articles/s42256-020-0197-y)
- [Guo et al. 2020 PFAS vadose-zone screening model, Adv. Water Resour.](https://www.sciencedirect.com/science/article/abs/pii/S0309170821002529)
- [EPA PFAS NPDWR Federal Register 2024](https://www.federalregister.gov/documents/2024/04/26/2024-07773/pfas-national-primary-drinking-water-regulation)
- [AWWA 2024 national PFAS cost estimate](https://www.asdwa.org/2024/08/02/awwa-releases-updated-national-pfas-cost-estimate/)
- [Michigan PFAS Response — Huron River Watershed](https://www.michigan.gov/pfasresponse/investigations/lakes-and-streams/huron-river)
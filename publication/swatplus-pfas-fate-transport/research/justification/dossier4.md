All four load-bearing facts are verified against real, citable sources. The prior model is Rafiei & Nejadhashemi (2023), *Water Research* — confirmed, with the ~22 kg/yr PFOS calibration discharge and SWAT-MODFLOW-RT3D structure. Michigan's 300→50 ppb Do-Not-Eat change confirmed (effective 2025). I now have everything needed to write the dossier.

---

# STREAM 4 — Reviewer Defense & Positioning Dossier

**Manuscript:** High-resolution, process-based PFAS surface-water fate-and-transport model of the Huron River watershed (HUC8 04100013), SWAT+ from NHDPlus HR (72,475 HRUs; 3,119 reaches).

A note on citation confidence is included with each. **[VERIFIED]** = confirmed this session against a primary/authoritative source; **[GROUNDED]** = supplied in the brief and internally consistent; **[STANDARD]** = well-established methods literature the reviewer will recognize but which you should confirm against your reference manager before submission.

---

## OBJECTION 1 — "Why model at all? Why not just monitor?"

**Rebuttal (strong).** Monitoring and modeling answer different questions, and the Huron case is the textbook demonstration that monitoring alone is insufficient for management. Endicott et al. (2025) showed that after the Wixom WWTP source control (GAC installation), Kent Lake **water-column PFOS fell ~99%, yet fish-tissue PFOS plateaued above the consumption-advisory threshold** — the monitoring data revealed the plateau but could not explain it, attribute it, or forecast it. The mechanistic inference (sediment legacy acting as a secondary internal source via partition coefficients and bioaccumulation factors) is fundamentally a *modeling* conclusion built on top of monitoring. A process model is required to (a) **forecast** how long the sediment reservoir will sustain exceedances, (b) **attribute** residual loading between remaining external sources and internal recycling, and (c) **evaluate counterfactual interventions** (e.g., dredging vs. monitored natural recovery) that cannot be observed because they have not happened. **[VERIFIED: Endicott et al. 2025, *Integ. Environ. Assess. Manag.* 21(4):810]**

**Three supporting arguments:**
- **Spatial extrapolation.** PFAS monitoring is sparse and station-bound; a watershed with 3,119 reaches cannot be characterized by a handful of sampling points. A calibrated process model is the only defensible way to assign concentrations to *un-monitored* reaches — exactly the reaches a manager needs for permitting and advisory decisions.
- **Regulatory forcing now demands prediction, not just detection.** The EPA finalized **enforceable MCLs of 4.0 ng/L for PFOA and PFOS** (Federal Register, Apr 26 2024; effective Jun 25 2024), with compliance monitoring by 2027 and treatment by 2029. Utilities and states must now *predict* where exceedances will occur and *plan* interventions on a fixed timeline — a forecasting task monitoring cannot perform. **[VERIFIED]**
- **Source-control sufficiency is now a quantitative question.** Michigan's lowering of the Do-Not-Eat fish PFOS threshold from 300→50 ppb (effective 2025) more than doubled advisory waterbodies (92→188). Whether a given source control will bring a waterbody *under* a moving threshold is a model question, not a monitoring one. **[VERIFIED]**

*Honest framing for the paper:* do not claim the model replaces monitoring. Claim the model is the **inference and forecasting layer** that converts monitoring into decisions — and that the Huron's fish-tissue plateau is the empirical proof monitoring alone left a gap.

---

## OBJECTION 2 — "Why process-based instead of cheaper machine learning?"

**Rebuttal (strong, but be disciplined).** ML/geostatistical PFAS models (e.g., the hydrology-informed geospatial PFAS mapping work, arXiv 2502.14894, "FOCUS"; and the broader national PFAS-occurrence ML literature) are excellent at **interpolating occurrence under stationary conditions**, but they are structurally unable to do the three things this paper is about:

1. **Counterfactual / intervention simulation.** ML predicts under the *observed* regime. The entire management question post-2024 is the *un-observed* regime (after source control, after threshold change, after sediment intervention). The Huron has already moved out-of-sample — water-column PFOS dropped ~99% while fish tissue did not track it. An ML model trained on pre-control data cannot reproduce a 99% drop with a non-tracking fish response; a process model with explicit water–sediment–biota partitioning can, because **partition coefficients and bioaccumulation factors are mechanistic, not learned correlations** (Endicott et al. 2025). **[VERIFIED]**
2. **Mass conservation and attribution.** Source identification ("how much of reach X comes from source Y") requires a mass-balanced transport model. This is precisely what Rafiei & Nejadhashemi (2023) used the distributed model for (apportioning ~22 kg/yr PFOS across point and non-point sources). ML gives a concentration field, not a defensible mass-discharge attribution. **[VERIFIED: Rafiei & Nejadhashemi 2023, *Water Research*]**
3. **Data scarcity favors mechanism.** PFAS observations are sparse (the brief itself notes sparse PFAS data). ML's accuracy degrades with sparse, spatially clustered labels; process models inject physical constraints (flow continuity, advection-dispersion, sorption) that act as strong priors and let you predict where you have *no* labels. This is the standard argument for physics-based over data-driven models in data-poor regimes. **[STANDARD]**

*Honest framing:* concede ML's strengths explicitly (cheaper, good for occurrence screening and prioritizing where to sample) and position the two as **complementary** — ML for occurrence triage, process model for fate/forecast/intervention. Do **not** claim the process model is more accurate at pure interpolation; that is a weak and attackable claim. Frame the contrast as *capability* (mechanism, counterfactuals, mass balance), not raw goodness-of-fit.

---

## OBJECTION 3 — "Is the high resolution justified, or just more parameters and compute?" (over-parameterization / equifinality / input-resolution mismatch)

This is the **most dangerous objection** because it has real technical teeth. Split it into three sub-claims and answer each honestly; one of your claims here is strong and two need care.

**3a. Resolution buys observation fidelity, NOT more free parameters (STRONG — lead with this).**
The decisive point: **higher reach count does not necessarily mean more *calibrated* parameters.** SWAT+ PFAS/transport parameters are typically assigned by class (land use, soil, source type), not per-reach. Going from ~189 reaches (Rafiei & Nejadhashemi 2023) to 3,119 reaches (~16.5×) increases *spatial discretization*, not the *dimension of the calibration vector*, if parameters remain class-based. So the over-parameterization charge largely dissolves: you are refining geometry, not adding degrees of freedom. **[GROUNDED + STANDARD]** — *State this explicitly in the paper; it is your single best defense and reviewers often assume the opposite.*

**3b. Resolution's concrete payoff is correct observation-to-reach assignment (STRONG, and it's your novelty hook).**
With 3,119 reaches, each PFAS field measurement is assigned to the **specific channel matching by closest drainage area** — a station maps to one near-correct reach rather than being averaged into a coarse aggregated subbasin. At 189 reaches, a single reach can span many kilometers and aggregate hydrologically distinct sources; a measured concentration gets attributed to a spatial unit ~16.5× too coarse, biasing both calibration targets and source attribution. This is a **measurable, defensible methodological gain**: it reduces *representativeness error* (the mismatch between the support of an observation and the support of the model unit), a well-recognized error class in spatial environmental modeling. The reviewer accepts this because it is a fidelity argument, not a free-parameter argument. **[GROUNDED]**

**3c. Input-data resolution mismatch (the honest weakness — disclose, don't hide).**
A sharp reviewer will say: "Your *forcing* data (precipitation, PFAS source inventories, atmospheric deposition) are coarser than your 3,119-reach network, so the extra reaches are spurious precision." **You must concede the asymmetry and bound it:**
- The defensible position: high reach resolution is justified **where the controlling heterogeneity is itself fine-scale** — i.e., the *stream network topology and drainage-area structure* (from NHDPlus HR), which genuinely is high-resolution and is what governs routing and observation assignment. Resolution of the *network* is data-supported even if some *forcings* are coarse.
- Where forcings are coarse (e.g., meteorology), the fine network does not invent information — it routes the same forcing through a more accurate channel geometry. That is a *geometric* refinement, legitimately supported by the HR hydrography.
- **Recommended explicit caveat sentence:** *"High channel resolution is warranted by the resolution of the NHDPlus HR hydrography and the drainage-area structure that governs routing and observation-to-reach assignment; it does not presuppose equally fine resolution in meteorological or source-inventory forcings, and we treat those as the limiting resolution for source-attribution confidence."*

**On equifinality specifically:** acknowledge it head-on and show you control for it — multi-objective calibration, parameter identifiability analysis, and (the brief notes Morris SA capability) **global sensitivity analysis to fix non-influential parameters before calibration.** Equifinality is managed, not eliminated; claiming you eliminated it is a red flag. **[STANDARD — GLUE/Beven; Morris 1991]**

---

## OBJECTION 4 — "What is actually new versus your own 2023 Water Research paper?" (the delta)

This is the objection most likely to come from an editor (self-citation / incremental-advance concern). You need a crisp, enumerated delta. Five distinct, defensible advances:

| # | Delta | 2023 (Rafiei & Nejadhashemi) | This paper | Strength |
|---|---|---|---|---|
| 1 | **Stream-network resolution** | ~189 subbasins/reaches | 3,119 reaches (~16.5×) in SWAT+ on NHDPlus HR; 72,475 HRUs | Strong [GROUNDED] |
| 2 | **Observation-to-reach assignment** | coarse aggregated reach | each measurement → specific reach by closest drainage area | Strong [GROUNDED] |
| 3 | **Post-source-control regime + sediment legacy** | pre/early-control source apportionment (~22 kg/yr) | the *new* dynamics: water-column ~99% drop vs. fish-tissue plateau, sediment as secondary internal source | Strong [VERIFIED via Endicott 2025] |
| 4 | **Enforceable-MCL relevance** | pre-regulation (advisory-era) | 4.0 ng/L enforceable MCL (2024) + Michigan 50 ppb fish threshold (2025) | Strong [VERIFIED] |
| 5 | **Modeling platform + national scalability** | SWAT-MODFLOW-RT3D, bespoke | SWAT+ generated by an automated NHDPlus HR → model pipeline, reproducible for any CONUS HUC | Moderate [GROUNDED] |

**The two strongest deltas to foreground** are #3 (you are modeling a *scientifically new phenomenon* — the decoupling of water and fish trajectories that did not exist in the 2023 data) and #1+#2 together (a genuine methodological step-change in resolution with a concrete payoff). Delta #4 makes it timely. Delta #5 is your scalability/product story but is the weakest *scientific* novelty — frame it as enabling reproducibility/transferability, not as the core advance, or a reviewer will call it engineering.

*Caution on #5:* a SWAT-platform reviewer may note that NHDPlus HR-based SWAT+ generation is increasingly common. Position your contribution as the **first application of an automated high-resolution SWAT+ pipeline to PFAS fate-and-transport**, not as inventing HR-based model generation.

---

## OBJECTION 5 — "Calibration/validation defensibility with sparse PFAS data"

This is where many PFAS-modeling papers are legitimately weak; pre-empt it with a concrete protocol rather than a defense.

**Rebuttal components (all STANDARD practice the reviewer expects to see):**
1. **Reduce the calibration dimension before fitting.** Use global sensitivity analysis (Morris screening; Sobol if affordable) to identify the few influential parameters; fix the rest at literature values. With sparse data this is the single most important defensibility move — it directly answers the equifinality/over-parameterization charge from Objection 3. **[STANDARD: Morris 1991, *Technometrics*; Saltelli et al.]**
2. **Use the right targets at the right support.** Calibrate to the observations *at the specific reaches they belong to* — this is exactly what the high resolution enables (Objection 3b). Coarse models force you to calibrate against spatially mismatched targets, which is itself a hidden error you avoid.
3. **Multi-line-of-evidence constraints, not just concentration time series.** Constrain with (a) calibrated total mass discharge (the 2023 paper's ~22 kg/yr provides a *prior* mass-balance anchor — a legitimate use of your own earlier work), (b) water/sediment/biota partitioning consistency (Endicott's measured partition coefficients and BAFs as independent constraints), and (c) the *direction and magnitude* of the post-control change (the ~99% water-column drop is a strong dynamic constraint that a sediment-legacy model must reproduce). Reproducing the **water-down/fish-plateau divergence** is a far more demanding and convincing validation than fitting a single concentration series. **[VERIFIED via Endicott 2025; GROUNDED via 2023]**
4. **Honest uncertainty reporting.** Report parameter and predictive uncertainty (GLUE or formal Bayesian/DREAM if feasible; at minimum P-factor / R-factor bands). State that PFAS data sparsity makes this an *uncertainty-bounded* fate model, not a point-predictive one. **[STANDARD: Beven & Binley GLUE; Abbaspour P-factor/R-factor]**
5. **Spatial/temporal holdout.** Where data permit, hold out reaches or a post-control time window for validation. The post-source-control period is a natural validation experiment: calibrate on the pre/early-control regime, validate against the documented plateau dynamics.

*Honest framing:* explicitly state the data-sparsity limitation. Reviewers punish overclaiming far more than they punish a candidly bounded model. The defensible claim is: *"We do not claim a fully identified parameter set; we claim a sensitivity-reduced, mass-balance-anchored, partition-constrained model whose predictive uncertainty we quantify and whose key validation is reproducing the observed post-control water–fish decoupling."*

---

## STRONGEST CANDIDATE SENTENCES FOR THE CONTRIBUTION/NOVELTY STATEMENT

Pick 3–4. These are written to be defensible as worded.

> **(1) — Resolution + assignment, the methodological core.**
> "We present a process-based PFAS surface-water fate-and-transport model of the Huron River watershed built in SWAT+ from NHDPlus HR hydrography, resolving the stream network into 3,119 channels and 72,475 HRUs — an ~16.5× increase in reach resolution over the prior distributed model of the same watershed (Rafiei & Nejadhashemi, 2023) — which for the first time allows each PFAS field observation to be assigned to its hydrologically correct channel by closest drainage area rather than to a coarse aggregated subbasin."

> **(2) — The new phenomenon (your strongest scientific hook).**
> "Unlike earlier source-apportionment efforts conducted before regulatory source control, our model targets the post-control regime in which water-column PFOS has fallen by roughly 99% while fish-tissue PFOS has plateaued above the consumption-advisory threshold — a decoupling attributed to sediment legacy acting as a secondary internal source (Endicott et al., 2025) — and we use that divergence as the primary dynamic validation of the model's water–sediment–biota partitioning."

> **(3) — Regulatory timeliness.**
> "This work directly serves the post-2024 regulatory landscape, in which the U.S. EPA has finalized enforceable drinking-water MCLs of 4.0 ng/L for PFOA and PFOS (2024) and Michigan has lowered its fish-tissue PFOS 'Do-Not-Eat' threshold from 300 to 50 ppb (2025), shifting the management question from detection to forecasting and intervention design — tasks that monitoring and data-driven occurrence models cannot perform."

> **(4) — Scalability/reproducibility (use only if you want the product angle; keep it modest).**
> "Because the model is generated by an automated NHDPlus HR → SWAT+ pipeline, the approach is reproducible and transferable to any watershed in the conterminous United States, providing a template for high-resolution, process-based PFAS assessment at national scale."

**Recommendation:** lead the abstract/contribution paragraph with **(2)** (new science) and **(1)** (new method), support with **(3)** (timeliness). Use **(4)** sparingly and only in the discussion/implications — it is the weakest as *scientific* novelty and the easiest for a reviewer to dismiss as engineering.

---

## CORRECTIONS / CAUTIONS ON THE GROUNDING FACTS (flag before submission)

- The EPA 2024 rule sets PFOA/PFOS at **4.0 ng/L**, but also sets **PFHxS, PFNA, and HFPO-DA (GenX) at 10 ng/L individually plus a Hazard Index for mixtures.** If your model addresses only PFOS, say so; do not imply the 4 ng/L number governs all PFAS. **[VERIFIED]** *(Note: in 2025 EPA proposed extending compliance deadlines and revisiting the non-PFOA/PFOS limits; the 4 ng/L PFOA/PFOS MCLs were retained. Confirm the current status sentence at submission, as this is actively moving.)*
- Michigan 300→50 ppb is the **Do-Not-Eat** trigger; the same revision also lowered the limited-consumption threshold (≈9→1.5 ppb). Cite precisely.
- Rafiei & Nejadhashemi (2023) reach count: the brief says "~189 subbasins/reaches." Confirm whether 189 is subbasins, reaches, or HRUs in that paper before printing the exact 16.5× ratio — the ratio is your headline number and must match the prior paper's reported discretization exactly. **[GROUNDED — verify the denominator in your own 2023 paper]**

---

## SOURCES (verified this session)

- Endicott et al. (2025), "Per- and polyfluoroalkyl substances (PFAS) in sediment: a source of PFAS to the food web?" *Integrated Environmental Assessment and Management* 21(4):810 — [PubMed](https://pubmed.ncbi.nlm.nih.gov/39903053/) | [Oxford Academic](https://academic.oup.com/ieam/article-abstract/21/4/810/7998487)
- EPA PFAS National Primary Drinking Water Regulation, final rule, 4.0 ng/L PFOA/PFOS — [Federal Register, Apr 26 2024](https://www.federalregister.gov/documents/2024/04/26/2024-07773/pfas-national-primary-drinking-water-regulation) | [EPA retains MCLs](https://www.epa.gov/newsreleases/epa-announces-it-will-keep-maximum-contaminant-levels-pfoa-pfos)
- Rafiei & Nejadhashemi (2023), watershed-scale PFAS fate-and-transport model (SWAT-MODFLOW-RT3D), Huron River, ~22 kg/yr PFOS — *Water Research* — [PubMed](https://pubmed.ncbi.nlm.nih.gov/37235893/) | [ResearchGate](https://www.researchgate.net/publication/370819004_Watershed_Scale_PFAS_Fate_and_Transport_Model_for_Source_Identification_and_Management_Implications)
- Michigan PFOS fish Do-Not-Eat threshold 300→50 ppb (2025), advisories 92→188 — [Bridge Michigan](https://bridgemi.com/michigan-environment-watch/new-pfas-guidelines-spark-more-do-not-eat-warnings-michigan-fish/) | [Huron River Watershed Council](https://www.hrwc.org/updated-michigan-eat-safe-fish-guides-offer-more-protective-advice-to-anglers/) | [Great Lakes PFAS Action Network](https://www.glpan.org/michigans-new-pfos-fish-consumption-guidelines-mark-major-step-forward)
- Michigan EGLE Huron River PFAS investigation (Wixom WWTP / Kent Lake context) — [michigan.gov/pfasresponse](https://www.michigan.gov/pfasresponse/investigations/lakes-and-streams/huron-river)
- ML PFAS mapping comparison point (FOCUS, hydrology-informed geospatial PFAS) — [arXiv 2502.14894](https://arxiv.org/pdf/2502.14894)

**Methods citations to add from your reference manager (not searched this session, [STANDARD]):** Morris (1991) *Technometrics* (elementary-effects SA); Saltelli et al. (global SA); Beven & Binley (GLUE / equifinality); Abbaspour et al. (P-factor/R-factor, SWAT-CUP); Vrugt (DREAM) if you do formal Bayesian uncertainty.
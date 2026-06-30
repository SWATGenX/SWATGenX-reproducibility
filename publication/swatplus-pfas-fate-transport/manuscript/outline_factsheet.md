I have the full justification dossier. Producing the structured brief.

---

# MANUSCRIPT BRIEF — PFAS SWAT+ Model of the Huron River Watershed (HUC8 04100013)

## PART 1 — TITLE & ABSTRACT

### Title (two options)

**Option A (recommended — capability-forward, sediment hook):**
A high-resolution, process-based PFAS fate-and-transport model of the Huron River watershed (SWAT+): reach-resolved surface-water transport for the post-source-control, sediment-legacy regime.

**Option B (resolution-forward, methods hook):**
Reach-scale PFAS surface-water modeling from NHDPlus HR: a process-based SWAT+ fate-and-transport framework for the Huron River watershed.

### Abstract (≈225 words; no citations; structured problem → approach → novelty → scope)

Per- and polyfluoroalkyl substances (PFAS) in surface waters have entered a regime of enforceable numeric limits—a 2024 U.S. drinking-water Maximum Contaminant Level of 4 ng/L for PFOA and PFOS, a CERCLA hazardous-substance designation, and Michigan in-stream Rule 57 values—shifting the management question from detection toward reach-scale prediction, source attribution, and counterfactual forecasting. These are tasks that monitoring and statistical occurrence models, by construction, cannot supply. The need is sharpened in the Huron River watershed (southeastern Michigan), where, following upstream source control, water-column PFOS fell by roughly 99% while fish-tissue PFOS plateaued above consumption-advisory thresholds—a divergence attributed to contaminated sediment acting as a secondary internal source. We present a process-based PFAS surface-water fate-and-transport model of this watershed, generated in SWAT+ by the SWATGenX platform from NHDPlus HR hydrography, 3DEP elevation, gSSURGO soils, and gridded land-use and climate forcings. The model resolves the network into 3,119 channels and 72,475 hydrologic response units—an order-of-magnitude increase in reach resolution over the prior distributed model of the same watershed—allowing each PFAS observation to be assigned to its hydrologically correct channel by closest drainage area. The PFAS engine ports a soil three-phase equilibrium formulation into the modern SWAT+ constituent host, routing PFAS through surface runoff, lateral flow, leaching, and sediment-bound pathways. We describe the model generation, the PFAS process formulation, the soil-PFAS initialization, and the observation-to-channel assignment, and we lay out the calibration and validation design; flow and PFAS calibration results are forthcoming.

---

## PART 2 — SECTION OUTLINE (with intents)

### 1. Introduction
Establish that enforceable 2024–2025 PFAS regulation (4 ng/L MCL, CERCLA designation, Michigan Rule 57, 300→50 ppb fish advisory) converts PFAS management from monitoring into reach-scale prediction. State the four capabilities monitoring cannot supply (source attribution, ungauged-reach prediction, counterfactual evaluation) and the scientific centerpiece (water-column ~99% drop vs. fish-tissue plateau → sediment legacy). Close on the thesis line: only a dynamic, sediment-coupled, reach-resolved process model natively outputs the quantity these regulations constrain, at the reaches and interventions managers must act on.

#### 1.1 Regulatory and management drivers
The enforceable-limits landscape and why each (MCL, CERCLA, TMDL/§303(d), Rule 57) is a load- or in-stream-concentration problem.

#### 1.2 Why monitoring and machine learning are insufficient
Frame as *capability not goodness-of-fit*: ML predicts occurrence but is non-causal; monitoring is structurally sparse and records only the integrated present. The process model is the causal/forecasting tier, complementary to ML's occurrence-triage strength.

#### 1.3 The Huron sediment-legacy problem and prior work
The Endicott et al. 2025 plateau-above-threshold observation; position this paper as the follow-up to Rafiei & Nejadhashemi (2023) on the same watershed, now targeting the *post-control regime*.

#### 1.4 Objectives and scope
PFOS-only v1; reach-resolved land-phase + in-stream framework; explicit statement that results/calibration are forthcoming (in the scaffold phase).

### 2. Study Area
Describe the Huron River watershed (HUC8 04100013, SE Michigan): physiography, land use (forest/ag/urban gradient), the regulated/contaminated context (Tribar/Wixom source history, Kent Lake), and why it is a decisive PFAS test bed.

### 3. Methods

#### 3.1 Model generation and resolution
SWATGenX pipeline: NHDPlus HR hydrography + 1/3 arc-second 3DEP DEM + gSSURGO soils + NLCD/CDL land use (250 m) + PRISM climate. Report the discretization (72,475 HRUs; 3,119 channels; ~3,430 routing units; ~90 reservoirs) and the resolution advance over the 2023 model, with the constituent-sensitivity and headwater-restoration justifications and the honest equifinality/forcing caveats.

#### 3.2 PFAS process model and engine
The ported soil three-phase equilibrium on the SWAT+ pesticide-constituent host: per-layer governing equation F(Cw)=0 (air–water Langmuir + aqueous + Freundlich solid − total mass), solved by bracket → bisection → Improved-Halley; double-precision re-implementation and its validation. Land-phase routing to runoff/lateral/leaching/sediment-bound; HRU-parallel land phase + serial routing (byte-identical, race-free); mass-balance closure; linear-Koc in-stream transport.

#### 3.3 Soil-PFAS initialization
Freundlich kf, exponent n, and d50 assigned per soil layer by matching gSSURGO organic carbon + texture to the nearest of six reference soils (S1–S6). Initial PFOS by land use (Table-1 ranges) plus national source overlays (EPA TRI/FRS, FAA Part 139 airports, DoD AFFF). Concentrations emitted as ranges handed to calibration.

#### 3.4 Observation-to-channel assignment
PFAS ambient stations (Michigan EGLE + USEPA/WQP) snapped to nearest channel by planar distance in EPSG:5070, drainage-area-aware. Report the test-subwatershed demonstration (58 EGLE stations, median snap 3.9 m) and the representativeness-error rationale (DAR theory as conceptual scale).

#### 3.5 Calibration and validation design
Morris global sensitivity screening → class-based parameter grouping → PSO/MMPSO calibration on the SWATGenX platform. State the dynamic validation strategy against the post-control water-column drop and the fish-tissue plateau as a demanding test of water–sediment partitioning; P-factor/R-factor uncertainty reporting; equifinality *managed* not eliminated.

### 4. Results *(SCAFFOLD — placeholders pending calibration)*
List to be filled:
- **Fig. R1** — Model domain map: 3,119-channel network, HRUs, PFAS station locations.
- **Fig. R2** — Observation-to-channel assignment: |log(DAR)| histogram, 189-reach vs 3,119-reach network; fraction of stations within the 0.5–1.5 band. *(The single highest-payoff figure.)*
- **Table R1** — Morris sensitivity ranking of PFAS transport parameters.
- **Fig. R3** — Flow calibration/validation hydrographs at gauged outlets; NSE/KGE/PBIAS table (**Table R2**).
- **Fig. R4** — Simulated vs. observed in-stream PFOS at assigned reaches; calibration metrics + P-factor/R-factor (**Table R3**).
- **Fig. R5** — Land-phase PFAS mass-balance partition (runoff/lateral/leach/sediment-bound) by land use.
- **Fig. R6** — Spatial reach-resolved PFOS concentration map vs. Rule 57 / MCL thresholds.
- **Fig. R7** — Sediment-legacy scenario: water-column recovery trajectory with/without a sediment internal source (the centerpiece forecast).

### 5. Discussion
Source attribution and CERCLA allocation use; prediction in ungauged reaches; counterfactual/intervention design (source control, sediment remediation); the sediment-legacy mechanism as the observation the model is positioned to *test and quantify*; national scalability/transferability of the NHDPlus HR→SWAT+ pipeline (framed as reproducibility, not core novelty); limitations (PFOS-only, forcing resolution, in-stream process data).

### 6. Conclusions
Restate the capability contribution, the resolution-plus-assignment methodological advance, and the timeliness for the post-2024 enforceable-limit landscape.

---

## PART 3 — CONSOLIDATED FACT-SHEET (use verbatim; preserve [VERIFY] flags)

**Model identity & discretization**
- Watershed: Huron River, HUC8 **04100013**, southeastern Michigan.
- Generator: **SWATGenX** platform → **SWAT+**.
- Inputs: **NHDPlus HR** hydrography; **1/3 arc-second 3DEP** DEM; **gSSURGO** soils; **NLCD/CDL** land use (**250 m**); **PRISM** climate.
- **72,475 HRUs**; **3,119 stream reaches/channels**; **~3,430 routing units**; **~90 reservoirs**.
- Performance: peak RAM **~2.85 GB**; **~13 min per simulated-year**, serial.
- Resolution advance: **~16.5×** more reaches than the 2023 model's **~189 subbasins/reaches** **[VERIFY the 189 against Rafiei & Nejadhashemi 2023 before printing the 16.5× ratio]**.

**PFAS engine**
- Ported from the SWAT-MODFLOW-RT3D PFAS model (Rafiei & Nejadhashemi 2023) onto the SWAT+ **pesticide-constituent host**.
- Per-layer soil equilibrium solves aqueous conc Cw of **F(Cw) = air–water Langmuir term [Γ_max·KL] + aqueous term + Freundlich solid term [kf·Cw^n] − total mass = 0**, via **bracket → bisection → Improved-Halley**.
- Re-implemented in **double precision**; validated to **1.7×10⁻⁷ worst-case relative error** vs. a 40-digit reference across **29,160 cases** (original real(16) quad unnecessary).
- Land phase routes PFAS to **surface runoff / lateral flow / leaching / sediment-bound** (Freundlich solid × sediment yield × enrichment).
- **HRU-parallel land phase + serial routing (byte-identical mode)** → race-free in-stream water quality.
- Land-phase mass balance closes to **~1×10⁻⁵ relative**.
- In-stream routing: **linear-Koc** transport (NOT Freundlich/Langmuir downstream), matching the source model.
- **Reach concentrations are a RESULT pending the in-stream module + calibration.**

**Soil-PFAS initialization**
- Per-layer Freundlich **kf**, exponent **n**, median grain diameter **d50** assigned by matching gSSURGO organic carbon + texture to nearest of **six reference soils S1–S6** (**kf 126–450, n 0.33–0.53, d50 0.04–0.10 mm**; from Li et al. 2019).
- Initial soil PFOS by land use: **forest 0.005–0.01; ag/pasture 0.2–8; urban 0.2–30 µg/kg**.
- National source overlays: **EPA TRI/FRS** PFAS facilities, **FAA Part 139** airports, **DoD AFFF** → **100–4000 µg/kg**.
- Concentrations emitted as **RANGES** handed to calibration.
- **PFOS-only v1**: mw **0.50013 kg/mol**; sol **680 mg/L**; **KL = 0.137 L/nmol [VERIFY against paper]**; **Γ_max = 2500 nmol/m² [VERIFY]**.

**Observation-to-channel assignment**
- PFAS ambient stations: **Michigan EGLE** surface-water program + **USEPA/WQP**.
- Snapped to nearest SWAT+ channel reach by **planar distance in EPSG:5070** (drainage-area-aware).
- Demonstrated: **58 EGLE stations** in the test sub-watershed, **median snap 3.9 m**. HUC8 set is larger.

**Regulatory anchors (motivation)**
- EPA **MCL = 4 ng/L** PFOA/PFOS (2024) **[VERIFY current deadline status; 2025 reconsideration retained PFOA/PFOS MCLs]**.
- **CERCLA** hazardous-substance designation (2024).
- Michigan **Rule 57**: PFOS **12 ng/L** / PFOA **11 ng/L** in-stream.
- Michigan fish PFOS Do-Not-Eat threshold **300 → 50 ppb**.

**Scientific centerpiece**
- Post-source-control (Tribar/Wixom): Huron water-column PFOS fell **~99%**, but fish-tissue PFOS **plateaued above advisory**, attributed to **sediment legacy** as a secondary internal source (**Endicott et al. 2025**).

### NOVELTY / CONTRIBUTION STATEMENT (use as the canonical 4–5 sentence block)

We present a process-based PFAS surface-water fate-and-transport model of the Huron River watershed built in SWAT+ from NHDPlus HR hydrography, resolving the network into 3,119 channels and 72,475 HRUs—an ~16.5× increase in reach resolution over the prior distributed model of the same watershed (Rafiei & Nejadhashemi 2023)—which for the first time allows each PFAS observation to be assigned to its hydrologically correct channel by closest drainage area rather than to a coarse aggregated subbasin. Unlike that earlier source-apportionment effort, conducted before regulatory source control, this model targets the post-control regime in which water-column PFOS has fallen ~99% while fish-tissue PFOS has plateaued above advisory—a decoupling attributed to sediment legacy as a secondary internal source—and is positioned to use that divergence as a demanding dynamic test of water–sediment–biota partitioning that fitting a single concentration series could not provide. Against machine-learning and monitoring alternatives, the contribution is one of capability rather than goodness-of-fit: ML occurrence models are non-causal and cannot represent the source-control or sediment-remediation interventions that are the regulator's actual levers, and monitoring records the integrated present but cannot attribute, forecast, or evaluate counterfactuals. We therefore position the process model as the causal/forecasting tier these tools structurally cannot reach, complementary to ML's national occurrence-triage strength. The work is timely because it serves the post-2024 landscape of enforceable 4 ng/L PFOA/PFOS MCLs and Michigan's 300→50 ppb fish-tissue threshold, which shift the management question from detection to forecasting and reach-scale intervention design.

---

## PART 4 — NOTATION & VOICE CONVENTIONS

**PFAS vs. PFOS.** Use **PFAS** for the contaminant class, the regulatory landscape, and the general motivation. Use **PFOS** wherever the statement is specific to the modeled constituent—the engine is **PFOS-only v1**. Never let a PFOS result imply a class-wide claim. State explicitly in the Introduction and Methods that v1 simulates PFOS only; note that the 4 ng/L MCL is **PFOA/PFOS-specific** (PFHxS/PFNA/HFPO-DA are 10 ng/L + Hazard Index) so the regulatory framing is not overgeneralized.

**Units.** Water-column / in-stream concentrations in **ng/L** (regulatory units: MCL 4 ng/L, Rule 57 11–12 ng/L). Soil / solid-phase PFOS in **µg/kg**. Fish tissue in **ppb**. Internal model quantities keep their native units: KL in **L/nmol**, Γ_max in **nmol/m²**, kf dimensionless-style as given, d50 in **mm**, mw in **kg/mol**, solubility in **mg/L**. Do not silently convert between ng/L and µg/L—keep regulatory comparisons in ng/L.

**Referring to the 2023 paper.** Cite as **Rafiei & Nejadhashemi (2023)**, *Water Research* 240:120073. Frame it as **"our prior distributed model of the same watershed"** / **"the earlier source-apportionment effort."** Two load-bearing distinctions to make every time it is contrasted: (1) it was the **SWAT-MODFLOW-RT3D** model at **~189 reaches**; this is the **SWAT+** port at 3,119; (2) it was built **before** regulatory source control, whereas this targets the **post-control regime**. The PFAS soil-equilibrium physics is **ported from**, not reinvented relative to, that work.

**The 16.5× framing.** Always state it as **network/reach resolution**: "~16.5× increase in **stream-network resolution** / **reach count**." Never as "16.5× more accurate" or "16.5× higher resolution" unqualified. The resolution gain is in **network geometry and observation assignment** (supplied by NHDPlus HR), **not** in forcing or parameter dimensionality—say so proactively. The 16.5× number is **gated on [VERIFY]** of the 189 denominator; until verified, write "approximately an order of magnitude" as the safe fallback.

**Claim discipline (apply the claim ledger).** Frame the contrast with ML and monitoring as **capability, not goodness-of-fit**. Equifinality is **managed** (Morris screening + class-based parameters + uncertainty bands), **never eliminated**. The sediment legacy is the observation the model is **positioned to test and quantify**—stated as such, never as a closed mass balance the model has already proven. DAR theory is cited as **conceptual scale only**, not a numerically transferable validity band. National scalability lives in the **Discussion** as reproducibility/transferability, not as core novelty. Reach concentrations and all calibration metrics are **RESULTS pending calibration**—the Results section is a labeled scaffold.

**Voice.** Scholarly, citation-anchored, declarative. Hedge claims that are mechanistic-but-unmeasured ("is positioned to," "we expect," "structurally") distinctly from claims that are evidence-backed ("falls ~99%," "validated to 1.7×10⁻⁷"). Mark every unverified number inline with **[VERIFY]**.

---

**Authoritative source:** `/data/SWATGenXApp/codes/publication/pfas-huron-swatplus/research/justification/justification.md` (read in full for citations, the resolution-advantage argument, and the claim ledger that governs Part 4's claim discipline).
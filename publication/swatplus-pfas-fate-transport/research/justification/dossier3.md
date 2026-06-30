I have all the evidence I need. Compiling the dossier now.

---

# STREAM 3 — THE RESOLUTION ADVANTAGE: A citation-anchored dossier

**Thesis the manuscript should defend:** moving from a ~189-reach watershed model (Rafiei & Nejadhashemi 2023) to a 3,119-reach NHDPlus HR SWAT+ model (a ~16.5× finer stream network) is not cosmetic refinement — it materially improves (i) measurement-to-channel assignment, (ii) reach-scale PFAS load and concentration prediction, and (iii) the spatial localization of sources and sediment-legacy hotspots. Below, each pillar is graded **STRONG** (reviewer will accept on cited evidence), **DEFENSIBLE** (well-supported but argue carefully), or **WEAKER / CAVEAT** (flag honestly, pre-empt the critique).

---

## 1. Why stream-network resolution governs water-quality prediction (the foundational literature) — STRONG

The discretization-sensitivity literature is unambiguous that **streamflow is relatively insensitive** to subbasin number, but **sediment- and nutrient-bound constituents are strongly sensitive**. This is the central asymmetry to lead with, because PFAS (especially PFOS, the Huron problem) partitions to organic carbon and sediment and therefore behaves like the *sensitive* class, not the insensitive (streamflow) class.

- **Jha, Gassman, Secchi, Gu & Arnold (2004),** *J. American Water Resources Association* 40(3):811–825. The canonical subdivision-sensitivity study. Findings to cite verbatim: streamflow is essentially insensitive to subbasin count, but to stabilize **sediment** loads the subbasin drainage area should be **< ~3% of total watershed area**, **nitrate ~2%**, and **phosphorus ~5%**. This paper gives you a *quantitative target*: for a HUC8 like 04100013, a coarse 189-reach model has mean subbasin area far above these thresholds; 3,119 reaches drives mean per-reach area well below them. This is your single strongest, most-cited anchor.
- **FitzHugh & Mackay (2000),** *J. Hydrology* 236:35–53, and **(2001)** *J. Soil & Water Conservation* 56:137–143. Showed sediment generation is sensitive to HRU/subbasin area through a *nonlinear* source-area relationship, while streamflow is nearly invariant. Establishes that the sediment/particulate response to coarsening is biased, not just noisy — coarse partitioning systematically mis-estimates source-limited sediment yield.
- **Arabi, Govindaraju & Hantush (2006)** corroborate the ~2–4% subbasin-area threshold for representing sediment and BMP effects (cite alongside Jha et al. for a convergent independent number).

**Argument for the manuscript:** PFOS in the Huron is sediment-/OC-associated; it is governed by the same partitioning physics that makes sediment and particulate P the *resolution-sensitive* constituents. Therefore the discretization standard the model must meet is the sediment/nutrient standard (~2–5% subbasin area), not the lax streamflow standard. The 189-reach model cannot meet it; the 3,119-reach model can.

---

## 2. NHDPlus HR vs medium-resolution NHD — the source of the resolution gain — STRONG

- **Moore, McKay, Rea, Bondelid, Price, Dewald & Johnston (2019),** *JAWRA* 55(3):874–898, "The Road to NHDPlus." Authoritative description of the NHDPlus lineage. **NHDPlus V2 is built on medium-resolution (1:100,000-scale) NHD; NHDPlus HR is built on high-resolution (1:24,000-scale or better) NHD plus the 1/3-arc-second 3DEP DEM and the full WBD.** This is the documented basis for the order-of-magnitude jump in mapped channel density.
- **USGS NHDPlus HR User's Guide** (SIR 2025-5031; and the earlier release) — cite for the formal statement that NHDPlus HR "provides much greater spatial detail than NHDPlusV2."
- **Headwater under-mapping:** medium-resolution networks systematically *omit* small/first-order channels. **Alexander, Boyer, Smith, Schwarz & Moore (2007),** *JAWRA* 43(1):41–59, quantify why this matters: first-order (headwater) streams are the most frequent tributary type, contribute ~65% of nitrogen flux in second-order streams (≈40% even in navigable waters), and are *disproportionate sites of in-stream processing* (denitrification, here read as in-channel sorption/settling for PFOS) because of their high benthic-area-to-volume ratio. Resolving these reaches is exactly what HR (and your 3,119 channels) does and medium-resolution (189-reach) cannot.

**Argument:** the resolution advance is *inherited from the input hydrography*, not an arbitrary modeling choice. Coarse medium-resolution networks don't merely lump — they *delete* the headwater reaches where a large share of source loading and in-stream attenuation occurs. The HR-derived 3,119-reach network restores those reaches as explicit modeling units.

---

## 3. The measurement-to-channel assignment argument (the methodological centerpiece) — STRONG-to-DEFENSIBLE

This is your most novel and defensible methodological claim, and it ties directly to the drainage-area-ratio (DAR) literature.

**The DAR / representativeness-error logic:**
- The **drainage-area ratio method** (USGS standard practice; e.g., **Asquith, Roussel & Vrabel 2006**, USGS SIR 2006-5286; **Ries & Friesz 2000**; **Stuckey 2006**, USGS SIR 2006-5130) transfers a streamflow/observation from a reference point to a target reach by scaling on the **ratio of drainage areas**, and is reliable only when that ratio is near 1 — commonly accepted within **0.5–1.5**, with some regions tolerating ~0.33–3. The transfer error grows monotonically as the drainage-area ratio departs from 1.
- **Farmer (2018),** *J. Hydrology* 561:872–885 ("High-spatial-resolution streamflow estimation … using NHD and USGS streamflow") makes the explicit case that **higher network resolution reduces the representativeness error** of assigning gauge information to ungauged reaches, because finer networks place a candidate reach whose drainage area is closer to the observation point.

**Apply this to PFAS field stations:** every PFAS grab sample sits at a real-world drainage area. Assigning it to a model channel introduces a *representativeness error* proportional to the mismatch between the sample's true upstream area and the model channel's upstream area. With 189 reaches, the nearest available channel can differ from the sample's true drainage area by a large factor (the sample is forced onto a coarse, aggregated reach that integrates tributaries the sample never saw). With 3,119 reaches, the nearest channel by drainage area is a *much tighter* match — the DAR is driven close to 1 — so the concentration/load the model attributes to that reach is being compared against an observation that actually represents that reach.

**Quantify it for the manuscript (defensible, do this calculation):**
- Mean reach-incremental drainage area scales ~inversely with reach count: going 189 → 3,119 reduces mean per-reach catchment area by **~16.5×**, i.e., the granularity of *available* drainage-area "bins" a station can be matched to is ~16.5× finer.
- This shrinks the **worst-case drainage-area mismatch** when snapping a station to its closest-DA channel by roughly the same factor, pulling the median assignment DAR from a regime where coarse-model snaps routinely fall outside the 0.5–1.5 "reliable" band into one where they sit comfortably inside it.
- **Recommended figure:** for your actual Huron PFAS stations, plot the histogram of |log(DAR)| = |log(A_station / A_assigned_reach)| under the 189-reach vs 3,119-reach networks, and report the fraction of stations that fall within the 0.5–1.5 DAR band in each case. This converts the abstract resolution claim into a measured, reviewer-proof number specific to your data. (This is the single most persuasive figure you can produce for Stream 3.)

**Honest caveat (state it):** the DAR literature is about transferring *flow* between hydrologically similar catchments; you are using DAR as a *station-to-reach snapping criterion*, which is a related but not identical use. Frame it as "closest-drainage-area assignment minimizes representativeness error," cite Farmer (2018) and the DAR sources as the principle, and don't overclaim that DAR validity bands transfer numerically — use them as the conceptual scale of acceptable mismatch.

---

## 4. Source localization & critical-source-area / sediment-legacy resolution — STRONG (and directly on-point for the Endicott sediment story)

This pillar connects resolution to the *management* payload of the paper: localizing the sediment-legacy secondary source.

- **The 80:20 concentration of loads.** Across NPS-modeling studies a small fraction of area produces most of the load — Djodjic & Markensten (2018), *Ambio* 48:1129–1142 confirm **~80% of diffuse P loss from ~20% of area**; SWAT critical-source-area studies report cases like **26% of area generating 50% of sediment load**. When loads are this spatially concentrated, **coarse reaches blur the hotspot**: a 189-reach model averages the high-loading sub-area into a large channel and *dilutes* the signal, whereas 3,119 reaches isolate the contributing reach. Djodjic & Markensten's high-resolution (2 m) modeling explicitly shows fine resolution resolves source areas as small as ~0.5 ha that coarse regional models miss.
- **Endicott et al. (2025),** *Integrated Environmental Assessment and Management* 21(4):810– (Kent Lake / Huron). Your grounding fact: after ~99% water-column source control (GAC at the Wixom WWTP / Norton Creek source), **fish-tissue PFOS plateaued above the advisory**, consistent with **contaminated sediment acting as an ongoing secondary internal source**. The management question this raises — *which reaches hold the legacy sediment inventory that keeps re-supplying the water column* — is inherently a reach-localization problem. A 16.5×-finer network is what lets the model carry reach-specific sediment-PFOS storage and resolve where the internal source is, rather than smearing it across a ~189-reach aggregation that spans the very source/impoundment gradient at issue.
- **Regulatory stakes that justify the resolution cost (frame, don't overclaim as resolution evidence):** EPA's 2024 final PFOA/PFOS MCLs at **4 ng/L**, and Michigan's tightening of the fish PFOS Do-Not-Eat threshold from **300 → 50 ppb**, mean management decisions now turn on *which specific reach/segment* exceeds thresholds — a reach-scale question that a coarse network cannot answer at the granularity regulators act on.

**Argument:** when loads and legacy inventories are spatially concentrated (the documented norm), prediction error and source mislocation in coarse models is not random — it is a *dilution bias* that hides hotspots. Fine resolution is the corrective, and the Endicott sediment-legacy finding is precisely the kind of localized internal source that demands it.

---

## 5. In-stream processing fidelity — DEFENSIBLE

Finer reaches improve the representation of **in-channel residence time and reach-scale biogeochemical/partitioning processing**, which matters because PFOS is reactive with sediment/OC in-channel (sorption, settling, resuspension), not conservative.

- **Alexander et al. (2007)** (above): low-order streams disproportionately process solutes due to high benthic-area:volume ratios; lumping them away removes that processing surface.
- General stream-network-density literature (e.g., the Mid-Atlantic potential-stream-density and headwater-network work, *PNAS/PMC* sources) shows network density controls water residence-time distribution — a first-order control on how long PFAS is exposed to sediment exchange in transit.

**Caveat:** this is mechanistically sound but harder to *prove improved* without reach-scale process data; present it as a structural advantage (the model can now represent reach-specific residence time and sediment exchange) rather than a demonstrated accuracy gain, unless you have observations to back it.

---

## 6. Honest costs, limits, and pre-emptive rebuttals (include this — reviewers will probe it)

State these proactively; each has a clean rebuttal.

1. **Over-parameterization / equifinality.** More reaches and HRUs = more free parameters and a higher-dimensional, equifinal solution space (the spatial-discretization/equifinality literature: Beven's equifinality thesis; the *J. Hydrology* discretization-and-extreme-runoff and a-priori-discretization-error work; the lumped-vs-distributed regionalization studies showing parameters absorb noise to compensate for missing spatial detail).
   - **Rebuttal:** SWAT+/SWAT does **not** assign independent parameters per reach; parameters are tied to soil/land-use/HRU classes and regionalized cal_parms, so reach count grows the *spatial resolution of prediction* far faster than it grows the *calibrated parameter dimension*. Constrain calibration to physically grouped parameters (standard practice) to keep dimensionality bounded — explicitly cite that controlling which parameters are calibrated is the recognized antidote to equifinality.
2. **Input/forcing uncertainty may dominate at fine scale.** At very fine reach scale, errors in DEM-derived delineation, soils (gSSURGO), and especially PFAS source inputs can exceed the resolution gain.
   - **Rebuttal:** the resolution gain we *claim* is in **assignment and localization** (Sections 3–4), which depends on network geometry (well-constrained from HR hydrography + 3DEP), not on the most uncertain forcings. We do not claim sub-reach forcing certainty; we claim correct station-to-reach matching and hotspot isolation.
3. **Diminishing returns / convergence.** Outputs converge as subbasins increase; beyond a point, more reaches add compute without accuracy.
   - **Rebuttal:** the convergence thresholds (Jha 2004: ~2–5% area) are exactly where the **189-reach model sits on the wrong side and the 3,119-reach model sits safely on the converged side.** We are not over-resolving past convergence; we are *reaching* convergence that the prior model never did. (If you want to be airtight, run a subdivision-sensitivity sweep showing your load metrics stabilize at your resolution — the strongest possible reviewer answer.)
4. **Compute cost.** Finer networks raise runtime/calibration cost (directly relevant to your PSO/cloud calibration work).
   - **Rebuttal:** acknowledge and quantify; note this is a tractable engineering cost (parallelization, cloud), not a scientific barrier, and is justified by the regulatory-scale (4 ng/L, 50 ppb) decisions the model informs.

---

## 7. One-paragraph version for the manuscript (drop-in)

> Streamflow predictions in distributed watershed models are largely insensitive to stream-network resolution, but sediment- and particulate-associated constituents are not: Jha et al. (2004, *JAWRA* 40:811–825) and FitzHugh & Mackay (2000, *J. Hydrol.* 236:35–53) show that stabilizing sediment and nutrient loads requires subbasin drainage areas below roughly 2–5% of total watershed area, a threshold a coarse ~189-reach delineation cannot meet. Because PFOS partitions strongly to organic carbon and sediment, it belongs to this resolution-sensitive class. Our NHDPlus HR-derived SWAT+ model (Moore et al. 2019, *JAWRA* 55:874–898) resolves the Huron (HUC8 04100013) into 3,119 channels — ~16.5× finer than the authors' prior 189-reach SWAT-MODFLOW-RT3D model (Rafiei & Nejadhashemi 2023) — which (i) drives mean reach catchment area below the Jha et al. convergence thresholds, (ii) restores the headwater reaches that medium-resolution hydrography omits yet that dominate loading and in-stream processing (Alexander et al. 2007, *JAWRA* 43:41–59), and (iii) lets each PFAS measurement be assigned to the channel of closest drainage area, minimizing the representativeness error that drainage-area-ratio transfer theory predicts grows as the area ratio departs from unity (Farmer 2018, *J. Hydrol.* 561:872–885; Asquith et al. 2006). Where PFOS loads and the sediment legacy implicated as a secondary internal source in Kent Lake (Endicott et al. 2025, *IEAM* 21:810) are spatially concentrated, this finer network resolves the contributing reaches that a coarse model would dilute — a precision now made consequential by enforceable reach-scale standards (EPA 4 ng/L MCL; Michigan 50 ppb fish PFOS advisory).

---

## Reference list (verified authors/years/journals)

- Jha, M., Gassman, P.W., Secchi, S., Gu, R., Arnold, J. (2004). Effect of watershed subdivision on SWAT flow, sediment, and nutrient predictions. *JAWRA* 40(3):811–825. **[STRONG anchor — ~3% sediment / ~2% nitrate / ~5% P subbasin-area thresholds]**
- FitzHugh, T.W., Mackay, D.S. (2000). Impacts of input parameter spatial aggregation on an agricultural NPS pollution model. *J. Hydrology* 236:35–53. (companion: 2001, *J. Soil Water Conserv.* 56:137–143)
- Arabi, M., Govindaraju, R.S., Hantush, M.M. (2006). [subbasin-area threshold corroboration ~2–4%].
- Moore, R.B., et al. (2019). The Road to NHDPlus — Advancements in Digital Stream Networks. *JAWRA* 55(3):874–898.
- USGS (2025). User's Guide for NHDPlus HR. SIR 2025-5031.
- Alexander, R.B., Boyer, E.W., Smith, R.A., Schwarz, G.E., Moore, R.B. (2007). The role of headwater streams in downstream water quality. *JAWRA* 43(1):41–59.
- Farmer, W.H. (2018). High-spatial-resolution streamflow estimation at ungauged sites using NHD and USGS data. *J. Hydrology* 561:872–885.
- Asquith, R.W., Roussel, M.C., Vrabel, J. (2006). Statewide analysis of the drainage-area ratio method. USGS SIR 2006-5286. (+ Stuckey 2006, SIR 2006-5130; Ries & Friesz 2000 for DAR practice)
- Djodjic, F., Markensten, H. (2018). From single fields to river basins: critical source areas for erosion and P at high resolution. *Ambio* 48(10):1129–1142.
- Endicott, D.D., et al. (2025). PFAS in sediment: a source of PFAS to the food web? (Kent Lake / Huron). *Integrated Environmental Assessment and Management* 21(4):810–.
- Rafiei, V., Nejadhashemi, A.P., et al. (2023). [Huron SWAT-MODFLOW-RT3D PFAS model, ~189 reaches]. *Water Research*.

**Grading summary:** Sections 1, 2, 4 are STRONG and reviewer-proof on cited evidence. Section 3 (the DAR measurement-to-channel argument) is your novel centerpiece — STRONG in principle but should be backed by the actual |log(DAR)| histogram on your Huron stations to be airtight, and framed carefully since DAR's numeric validity bands were derived for flow transfer, not station snapping. Section 5 (in-stream processing) is DEFENSIBLE structural argument, weaker on direct proof. Section 6 costs/limits must be included to pre-empt the over-parameterization/diminishing-returns critique; the cleanest single defense is a subbasin-sensitivity sweep showing your load metrics have converged at 3,119 reaches while 189 has not.

Sources:
- https://onlinelibrary.wiley.com/doi/10.1111/1752-1688.12389
- https://pubs.usgs.gov/publication/sir20255031
- https://www.sciencedirect.com/science/article/abs/pii/S0022169418306796
- https://pmc.ncbi.nlm.nih.gov/articles/PMC3307624/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6722166/
- https://academic.oup.com/ieam/article-abstract/21/4/810/7998487
- https://www.sciencedirect.com/science/article/abs/pii/S0043135423005092
- https://www.researchgate.net/publication/227624631
- https://www.sciencedirect.com/science/article/abs/pii/S0022169410004865
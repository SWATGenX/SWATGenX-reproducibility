I have sufficient material to deliver the dossier. The reach count for Rafiei 2023 is given in the user's context (~189 reaches). I have characterized all the major competitors and both review papers. Compiling the deliverable now.

---

# STREAM 1B DOSSIER — Non-SWAT process-based watershed/catchment PFAS models + the modeling-landscape reviews

Scope: distributed/process-based PFAS surface-water and catchment fate-and-transport models built on engines OTHER than SWAT (HSPF, INCA, MIKE, Delft3D/Sobek, HYPE, fugacity-multimedia, river-network routing), plus the named PFAS-modeling review papers and their explicit open gaps. Graded by threat (🔴 high / 🟡 moderate / 🟢 low) to the two paper claims: (C1) NOVELTY vs other process-based watershed PFAS models, and (C2) sufficiency of OBSERVED data to calibrate/validate.

A blunt caveat up front: nearly all primary publisher pages (ScienceDirect, ACS, ASCE, ResearchGate) returned HTTP 403 to automated fetch. The numbers below come from search-snippet abstracts, PMC/PubMed mirrors, and university repositories. Items flagged "VERIFY" need a human to open the PDF before they go in the manuscript — I do not want you citing a reach count I could only read in a snippet.

---

## PART 1 — THE TWO REVIEW PAPERS (your white-space source)

These are the Nejadhashemi-group ASCE reviews. Critically, **your co-author lineage owns both reviews** (Raschke, Nejadhashemi, Rafiei) — so the "open gaps" they name are gaps you are entitled to cite as the field's own framing, and your new paper is the natural answer to them.

### Review #1 (the 2022 pair — overview + case study)
Two companion papers, *Journal of Environmental Engineering* (ASCE), Vol. 148(9), Sept 2022:

1. **Raschke, A., Nejadhashemi, A.P., Rafiei, V. (2022).** "Overview of Modeling, Applications, and Knowledge Gaps for Integrated Large-Scale PFAS Modeling." *J. Environ. Eng.* 148(9). DOI: 10.1061/(ASCE)EE.1943-7870.0002033.
2. **(same authors) (2022).** "Opportunities and Challenges of Integrated Large-Scale PFAS Modeling: A Case Study for PFAS Modeling at a Watershed Scale." *J. Environ. Eng.* 148(9). DOI: 10.1061/(ASCE)EE.1943-7870.0002034.

Named gaps extracted (overview paper abstract):
- Existing PFAS models show "**simplicity**" and "**most simulating small and isolated systems**" — i.e., the field lacked large, integrated, spatially-complex models. (Strong support for C1.)
- Gaps identified per environmental compartment: **surface water, vadose zone, groundwater, streamflow, plant uptake, aquatic-organism bioaccumulation** — each flagged as under-modeled.
- The case-study paper integrated **SWAT (surface) + MODFLOW (groundwater) + WASP (streamflow)** and explicitly framed itself as assessing the "capabilities and shortcomings of widely used models." This is the direct intellectual predecessor of Rafiei & Nejadhashemi 2023.

Grade: 🟢🟢 SUPPORTS. The field's own 2022 review says existing models are simple and small/isolated. A 72,475-HRU / 3,119-reach model is the antithesis.

### Review #2 (the 2025 review — the one you MUST cite and rebut/align with)
**"Advances and Research Gaps for PFAS Modeling in Watersheds and Receiving Waters."** *Journal of Environmental Engineering* (ASCE), **Vol. 151(11), Nov 2025.** DOI: **10.1061/JOEEDU.EEENG-8137**.
(Authorship not confirmed from snippet — VERIFY, but almost certainly the same MSU/Nejadhashemi lineage given venue + topic.)

This is the most recent and most threatening-to-overlook review. It explicitly synthesizes PFAS F&T across **surface water, vadose zone, groundwater, streamflow, plant uptake, aquatic organisms** and "identifies knowledge gaps in modeling for each environmental area." You cannot publish without engaging it. Two strategic implications:
- It is your single best citation for "no high-resolution, fully-distributed, observation-calibrated process-based surface-water PFAS model yet exists." VERIFY that it actually says this — read it first.
- If this 2025 review already cites a newer competitor model you haven't found, that is your highest-priority blind spot. Open it and read its reference list end-to-end. 🟡 (unquantified risk until read.)

ACTION: A human must download both 2025 review PDF and its full reference list. This is the single most load-bearing unread document in this dossier.

---

## PART 2 — THE COMPETITIVE LANDSCAPE (non-SWAT process-based PFAS surface-water models)

Ordered roughly by threat to your novelty claim.

### 🔴 / 🟡 #1 — Shanghai river-network coupled hydrological-multimedia PFAS model (2024) — YOUR CLOSEST NON-SWAT COMPETITOR
"**A coupled hydrological multimedia model used to simulate PFASs transport and fate in the river network of megacity Shanghai.**" *Journal of Hydrology*, 2024. ScienceDirect PII S0022169424019887. (Authors/exact DOI VERIFY — 403-blocked.)
- Couples hydrology + multimedia transport over a **river network**; simulates **PFOA and PFOS**, 1990–2022; combines **field measurements + discharge estimation + model simulation** (so it IS calibrated/validated against observations).
- This is the one paper that overlaps your framing most: "process-based + river network + observation-backed + PFOS/PFOA." 
- Why it likely does NOT defeat you (VERIFY all three): (a) it appears to be a **coupled hydrological-multimedia / segment-box** formulation, not a high-resolution HRU+reach distributed F&T model; no HRU concept; resolution (segment count) not surfaced in snippets and is almost certainly far below 3,119 reaches; (b) urban river-network, not a NHDPlus-HR-resolved mixed-use watershed; (c) multimedia mass-balance emphasis (concentration reconstruction) vs your process-resolved runoff/lateral-flow/sediment partitioning.
- THREAT: It blunts a naked "first process-based river-network PFAS model" claim. Your defensible claim becomes "first **high-resolution, HRU-distributed, NHDPlus-HR-resolved** process-based PFAS surface-water model," with Shanghai cited as the coarser river-network precedent. ACTION: read this paper in full before finalizing any "first/highest-resolution" wording.

### 🟡 #2 — STREAM-EU (Delft3D-WAQ + E-HYPE), Danube and Europe-wide PFOS/PFOA
- **Lindim, C., van Gils, J., Cousins, I.T. (2016).** "A large-scale model for simulating the fate & transport of organic contaminants in river basins." *Chemosphere* (ScienceDirect PII S0045653515301387). The STREAM-EU model: dynamic mass-balance, **process-based, spatially-and-temporally resolved**, simulates surface water + groundwater + snow + soil + sediment; built in **open-source Delft3D-WAQ** and paired with the **E-HYPE** European hydrology model.
- **Lindim, C., Cousins, I.T., van Gils, J. (2015/2016).** "Estimating emissions of PFOS and PFOA to the Danube River catchment and evaluating them using a catchment-scale chemical transport and fate model." *Environmental Pollution* (PII S0269749115300440). Calibrated emissions; only the combined population+wealth+WWTP estimate achieved **NSE > 0 for PFOS; no positive NSE for PFOA.**
- **Lindim, C., van Gils, J., Cousins, I.T. (2016).** "Europe-wide estuarine export and surface water concentrations of PFOS and PFOA." *Water Research* (PII S0043135416305280). Predicted PFOS 6 ng/L (Thames)–125 ng/L (Rhône); PFOA 6 (Thames)–90 (Dnieper).
- Why it does NOT defeat you: continental/basin-scale, **coarse spatial resolution** (E-HYPE subbasins, hundreds-of-km river basins), and its OWN validation was weak (PFOA NSE never positive). This is the canonical "large-scale but coarse and poorly-constrained" precedent — exactly the simplicity-gap the 2022 review names. Strong CONTRAST citation.
- THREAT to C1: low-moderate (different resolution class). To C2: actually SUPPORTS you — STREAM-EU's failure to validate PFOA is evidence that observed-data sufficiency + fine resolution is the unmet need you fill.

### 🟡 #3 — Singapore reservoir 3D hydrodynamic + water-quality PFAS model (2024)
**Zhang, J., et al. (2024).** "Characterizing PFASs in aquatic ecosystems with 3D hydrodynamic and water quality models." *Environmental Science and Ecotechnology*. DOI: **10.1016/j.ese.2024.100473** (open access, PMC11381888).
- Six-model chain: Sobek rainfall-runoff + emission + Sobek-FLOW (1D) + **Delft3D-FLOW (3D hydrodynamic)** + Sobek-WAQ/ECO + **Delft3D-ECO (3D water quality)**. Process-based (advection-diffusion, adsorption/desorption, sedimentation, degradation). Total PFAS, PFOA, PFOS.
- Resolution: **2,500 curvilinear grid cells** (hydrodynamic), aggregated 4×4 for WQ, 4 water-column + 1 sediment layer. Calibrated 2009–2010, validated 2013–2014; **9 sampling stations** (5 tributaries + 4 reservoir); relative deviations <40%.
- Why it does NOT defeat you: this is a **reservoir/water-body 3D model**, not a watershed-scale land-phase + river-network F&T model. No HRU land-phase PFAS generation; it imports loads. Different problem class.
- THREAT: low. Cite as the "in-waterbody receiving-water 3D" branch — complements rather than competes.

### 🟢 #4 — Fugacity / numerical multimedia "box" models (NOT distributed; your easy contrast set)
These are regional multimedia mass-balance / fugacity models — explicitly the "simple, isolated-system" class the 2022 review criticizes. They are NOT spatially-distributed process-based hydrologic models. Use them as the foil.
- **Zhu, X., Li, H., Luo, Y., Li, Y., Zhang, J., Wang, Z., Yang, W., Li, R. (2024).** "Evaluation and prediction of anthropogenic impacts on long-term multimedia fate and health risks of PFOS and PFOA in the Elbe River Basin." ***Water Research***. DOI: **10.1016/j.watres.2024.121675.** **Multimedia fugacity model** (confirmed via PubMed 38692258), 2010–2021, no distributed reach routing. Note: this is in the SAME journal you likely target — must cite.
- **Pearl River basin (2022)** — "A regional numerical environmental multimedia modeling approach to assess spatial Eco-Environmental exposure risk of PFOS in the Pearl River basin." (PubMed 35121494). Multimedia, gridded-but-coarse.
- **Bohai Rim (2018)** — "Dynamic multimedia fate simulation of PFOS from 1981 to 2050 in the urbanizing Bohai Rim of China." (PubMed 29291523). Level-IV fugacity, regional.
- **Armitage et al. / global-scale PFO-A/S box models (2006–2009)** and **Pistocchi & Loos (2009)** "A Map of European Emissions and Concentrations of PFOS and PFOA," *Environ. Sci. Technol.* DOI 10.1021/es901246d — GIS regression/mass-balance, continental, coarse. The original "map, not a process model" reference.
- THREAT: low — all box/fugacity, none HRU-distributed. Collectively they ARE your novelty argument (the field defaulted to box models because distributed PFAS F&T was hard).

### 🟢 #5 — Lake Ekoln / Stockholm PFAS transport (2024)
"Modelling PFAS transport in Lake Ekoln: Implications for drinking water safety in the Stockholm region." *J. Hazardous Materials*, 2024 (PII S026974912402298X). Lake/receiving-water transport, S-HYPE-region context (S-HYPE = ~37,000 Swedish subbasins, but applied here to a lake, not a distributed PFAS land-phase model). Receiving-water focus. THREAT: low.

### 🟢 #6 — HSPF / INCA for PFAS — NO PUBLISHED PFAS APPLICATION FOUND
Despite HSPF and INCA being the canonical non-SWAT process-based catchment WQ engines, **I found no peer-reviewed HSPF-PFAS or INCA-PFAS surface-water fate-transport model (2018–2026).** INCA hits are all INCA-P (phosphorus); HSPF hits are sediment/nutrient. This is itself a finding: the obvious alternative engines have NOT been turned to PFAS. SUPPORTS C1. (Mild caveat: absence-of-evidence; a human should do one more targeted INCA-PFAS / HSPF-PFAS literature pass to be safe before claiming it in print.)

### 🟢 #7 — USGS efforts are STATISTICAL/ML, not process-based F&T
USGS PFAS work (PFAS Integrated Science Team; NWQN 23 surface-water sites sampling from Feb 2023; the FY24 **national groundwater PFAS occurrence predictive model**, samples 2019–2022, 24 analytes; *Science* 2024 "Predictions of groundwater PFAS occurrence at drinking water supply depths," DOI 10.1126/science.ado6638) are **monitoring + machine-learning occurrence/logistic models**, NOT process-based watershed F&T. THREAT to C1: low (different method class). VALUE: USGS NWQN/monitoring is a potential OBSERVED-DATA source for C2.

### Context-only (not direct competitors)
- arXiv 2503.10285 "Unifying monitoring and modelling of water concentration levels in surface waters" (2025) — statistical/data-fusion, not process-based.
- ESTL 2024 "PFAS River Export Analysis Highlights the Urgent Need for Catchment-Scale Mass Loading Data" (DOI 10.1021/acs.estlett.4c00017, 403-blocked) — argues catchment-scale PFAS **mass-loading data are scarce**. Double-edged: SUPPORTS your novelty (no one has the loads) but FLAGS your C2 risk (observed mass-load data hard to get). Read it.
- Newell et al. 2025, *Remediation Journal*, "Exploration of PFAS Mass Discharge in Stormwater Versus Groundwater" (DOI 10.1002/rem.70052) — conceptual/regulatory.

---

## PART 3 — EXPLICIT WHITE SPACE (how to position)

Synthesizing the landscape, here is what NO published model appears to have done simultaneously — your defensible novelty vector:

1. **Resolution.** Every non-SWAT process-based PFAS model is coarse: STREAM-EU = continental subbasins; Shanghai = river-network segments; Singapore = 2,500-cell reservoir grid; all box/fugacity models = regional compartments. **None is HRU-distributed at ~72,475 HRU / 3,119 NHDPlus-HR reaches.** This is your sharpest, most quantitative novelty axis. Frame as "highest-resolution process-based watershed PFAS surface-water model to date" (after VERIFYing Shanghai's segment count is lower).
2. **Engine.** The non-SWAT engines (HSPF, INCA) have **never been applied to PFAS**; the SWAT-family PFAS work is only Rafiei & Nejadhashemi 2023 and its 2022 precedent. You extend SWAT→SWAT+ (a different, more modern engine) for PFAS for the first time.
3. **Self-consistency vs your own predecessor.** Rafiei & Nejadhashemi 2023 (same Huron River, ~189 reaches, SWAT-MODFLOW-RT3D, PFOS, ~22 kg/yr discharge) is your baseline. The new work is a **~16× reach-resolution increase (189 → 3,119)** on the identical watershed in SWAT+ — a clean, quantified "high-resolution successor" story that no reviewer can dispute because you own both.
4. **Validation density.** STREAM-EU could not even reach NSE>0 for PFOA; the box models do not validate against distributed in-stream observations. If your observed-PFAS network is dense enough to calibrate AND validate at multiple in-network stations, that is a genuine first for a distributed model.

Recommended one-line claim (conservative, defensible): *"the first high-resolution, fully-distributed (HRU- and reach-resolved) process-based PFAS surface-water fate-and-transport model calibrated and validated against observed in-stream PFAS, advancing beyond coarse continental (STREAM-EU), urban river-network (Shanghai), receiving-water 3D (Singapore reservoir), and regional fugacity/multimedia (Elbe, Pearl, Bohai) approaches."* — but only after reading the 2025 ASCE review and the Shanghai paper.

---

## PART 4 — THREATS / HONEST RISK REGISTER

| Threat | Grade | Why | Mitigation |
|---|---|---|---|
| 2025 ASCE review (JOEEDU.EEENG-8137) may already cite a newer competitor you missed | 🔴 | Unread; most recent; same lineage | Human must read full PDF + reference list FIRST |
| Shanghai river-network model (2024) | 🟡→🔴 if high-res | Closest "process-based + river-network + observed PFOS/PFOA" overlap | Read full text; confirm segment count ≪ 3,119 and box-multimedia formulation; downgrade your claim to "HRU-distributed / highest-resolution" |
| C2 — observed PFAS load/concentration data scarcity | 🟡 | ESTL 2024 explicitly flags catchment mass-loading data gap; STREAM-EU couldn't validate PFOA | Inventory your Huron observed-PFAS stations/samples NOW; if PFOA/short-chain coverage is thin, scope claims to PFOS or compounds you can actually validate |
| "First/only" wording | 🟡 | Box/fugacity + STREAM-EU + Shanghai all predate you | Never say "first watershed PFAS model" (that's R&N 2023); say "first high-resolution HRU-distributed" |
| HSPF/INCA-PFAS absence is absence-of-evidence | 🟢 | One more targeted lit pass needed | Quick human search "HSPF PFAS" / "INCA PFAS" / "MIKE SHE PFAS" before printing the claim |

## Key citations to pull (for the human, in priority order)
1. ASCE *JEE* 151(11) 2025, DOI 10.1061/JOEEDU.EEENG-8137 — the gap review. **Read first.**
2. *J. Hydrology* 2024, Shanghai river-network PFAS, PII S0022169424019887 — closest competitor.
3. Lindim et al. STREAM-EU trio: *Chemosphere* (S0045653515301387), *Environ. Pollut.* (S0269749115300440), *Water Research* (S0043135416305280).
4. Zhu et al. 2024 *Water Research* 10.1016/j.watres.2024.121675 (Elbe fugacity).
5. Zhang et al. 2024 *Environ. Sci. Ecotechnol.* 10.1016/j.ese.2024.100473 (Singapore 3D).
6. Raschke, Nejadhashemi, Rafiei 2022 *JEE* 148(9), DOIs 10.1061/(ASCE)EE.1943-7870.0002033 and .0002034 (your own framing).
7. Pistocchi & Loos 2009 *ES&T* 10.1021/es901246d (European map, the box-model foil).
8. ESTL 2024 10.1021/acs.estlett.4c00017 (catchment mass-loading-data gap — relevant to C2).

Bottom line: your NOVELTY claim is defensible on the **resolution + engine + validation-density** axes, with the field's own 2022/2025 reviews naming the exact "simple/coarse/isolated" gap you fill. The two must-read-before-publishing items are the **2025 ASCE review** and the **2024 Shanghai paper** — both could force you to narrow "first" to "first high-resolution HRU-distributed," which is still a strong, clean claim. The main honest vulnerability is C2 (observed PFAS data sufficiency, esp. for compounds beyond PFOS), independently corroborated by STREAM-EU's PFOA validation failure and the ESTL 2024 mass-loading-data-gap paper.
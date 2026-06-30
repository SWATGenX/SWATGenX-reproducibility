# Upgrade plan — coupled SWAT+ ↔ MODFLOW 6 PFAS paper (Rogue River)

**Goal:** turn the central finding from *observation-consistent* (a lumped scalar `g` fit on ~2
effective reaches, leaning on a weak 1.4-dex aquifer validation) into a **robust, source-resolved
attribution** that a Water Research reviewer accepts. Not in a rush — gate each phase on results.

**Target venue:** Water Research (per `paper/MERGE_PLAN.md`).

---

## 1. The root problem (one sentence)
The groundwater attribution is non-identifiable on the present data: a single analyte (PFOS), a single
prescribed source, a 250 m grid (Péclet ~25, numerical dispersion dominates), and a 2-parameter joint
fit on 7 spatially-autocorrelated mainstem reaches (effective n≈2). The paper itself states it cannot
separate groundwater discharge from any co-located unmodeled term — so the headline claim rests on the
weakest leg.

## 2. The reframe (the new scientific spine)
**Multi-analyte source apportionment.** Different PFAS compounds fractionate differently between the
surface-runoff/sediment pathway and the groundwater pathway (chain length controls Freundlich `Kf`:
short chains are groundwater-mobile, long chains sorb to soil/sediment). The two pathways therefore
carry **distinct, independent fingerprints**. Fitting many analytes jointly — shared hydrology (one
flow field, one set of SFR discharge fluxes), compound-specific transport — does three things the
current single-analyte fit cannot:

1. **Raises degrees of freedom ~50×** — from 7 PFOS reaches to ~52 stations × ~8 analytes.
2. **Identifies the groundwater term by fingerprint, not by a residual** — killing the paper's biggest
   caveat ("cannot distinguish GW discharge from a co-located surface source"): a surface point source
   has a different analyte ratio than the Wolverine groundwater plume.
3. **Makes it a Water Research paper** — source apportionment by chemical fingerprint is exactly that
   journal's wheelhouse, not "we fit a scalar."

**Data confirms this is feasible (verified in `site.db`, Rogue bounding box 43.0–43.5N, -85.8 to -85.35W):**
- Surface water: 52 stations; well-detected analytes PFBS(83), PFBA(82), PFHpA(70), PFOA(68),
  PFOS(64), PFHxA(64), PFHxS(63), PFPeA(61) detects — both mobile and sorptive ends present.
- Groundwater: 893 wells; PFBS(1513), PFOA(1400), PFHxS(1243), PFOS(1169), PFHxA(1068), PFNA(396)
  detects; Wolverine source signature (PFOS max 1.5×10⁶, PFHxS 6.2×10⁴, PFBS 3.1×10⁴ ng/L).
- Source facilities in-box: 46 manufacturing + 17 wastewater → candidate additional sources.

---

## 3. Modeling upgrades (priority tiers)

### TIER 1 — make the attribution robust (load-bearing)

**T1.1 Multi-analyte apportionment** *(centerpiece; data ready)*
- Model ≥5 analytes across the mobility spectrum: mobile {PFBS, PFBA, PFHxA, PFPeA} + sorptive
  {PFOS, PFOA, PFHxS}. Compound-specific Freundlich `Kf`/`n` and `Koc` from literature
  (Li 2019 set; see memory `pfas-soil-data-init`), per-analyte source signature from the well plume.
- Surface engine + MF6 GWT run per species on the SAME calibrated flow field; SFT routes each.
- New estimator: joint apportionment of (surface loading, groundwater interception) fit across
  analytes × reaches in linear concentration space, with fingerprint separation of GW vs. surface
  sources. Report per-analyte and pooled.
- **Robustness gain: highest.** Identifiability + DoF. **Effort: medium.** **Risk: low–med** (needs
  analytes to fractionate distinguishably — data suggests they do).
- *Gate G1:* if the GW fingerprint separates cleanly, the spine is set and T1.2 becomes refinement
  rather than load-bearing.

**T1.2 Local grid refinement at the Wolverine corridor** *(makes `g` physical)*
- MODFLOW 6 LGR or a DISV quadtree refined to ~25–50 m in the source-to-river corridor; coarse
  elsewhere. Kills Péclet-25 numerical dispersion, resolves the plume gradient and the
  discharge-to-stream geometry the 250 m cell smears.
- Converts `g` from a lumped fudge factor toward a **physical interception fraction** — ideally the
  coupled model predicts the in-stream GW load with no fitted `g`.
- **Robustness gain: high** (sharpens the GWT validation, currently 1.4 dex above background).
  **Effort: high** (generator emits refined grid; re-calibrate flow; convergence). **Risk: med.**

**T1.3 Multiple / identified source zones** — RESOLVED 2026-06-24: the Tannery is ALREADY a prescribed
source. Diagnostic of `pfas_gw_PFOS.csv` shows the 8 GWT source cells split 6 House Street + **2
Tannery (cells 135/136,83 carrying the 1.5M & 830k ng/L peaks — the strongest source in the model)**.
So the lower-mainstem porewater under-prediction (−0.5 to −1 dex) is NOT a missing-source problem — the
discharge zones (ch 1/2 outlet) sit ~2.6 km downstream of both source clusters and the plume decays
over that distance. **→ This is a TRANSPORT/RESOLUTION problem; the fix is T1.2 DISV, not a new source.**
T1.3 deprioritized (no redundant Tannery source needed). Other documented sites (Wolven-Jewell, NE
Gravel) remain optional but the porewater diagnostic says transport, not source count, is the lever.

### TIER 2 — strengthen the supporting calibration

**T2.1 Flow calibration beyond one baseflow number.** Hydrograph separation → seasonal/multiple
baseflow targets; reduce RMSE (5.6 m). Promote head obs-vs-sim to a **main-text figure** (currently
SI only). Effort: med.

**T2.2 Transport on transient flow (or a documented sensitivity).** Retire — or quantify the
irrelevance of — the steady-flow simplification for the time-aggregated plume. Effort: med–high; lower
priority.

**T2.3 Mass-balance closure as a number.** Compute and report the SW↔GW PFAS budget closure (%); the
manuscript currently asserts "continuous mass balance" rhetorically ~6×. Effort: low.

### TIER 3 — external validity (decide after Tier 1)

**T3.1 Second contaminated watershed** with plume data, to back the "reproducible at archive scale"
claim with N=2. Effort: high. Defer; revisit once Rogue is robust.

**T3.2 Sobol on the scoped parameters.** Morris already flags the cluster (source, aquifer K, `Kf`/`n`,
streambed conductance); variance decomposition on those handful. Effort: med. After Tier 1.

---

## 4. Paper upgrades (follow from the new results)
- **New narrative spine:** multi-analyte source apportionment with a physically-resolved (LGR)
  groundwater pathway → robust, fingerprint-based attribution. Demote the lumped-`g` framing.
- **Abstract → ~250 words** (currently 523; WR limit). **Highlights → ≤85 char × 5** (currently
  200–300 each). Consolidate the "first … to our knowledge" claim (×5 → 1–2).
- **Figures:** add coupling schematic (doubles as WR graphical abstract); promote head-calibration to
  main text; **new apportionment/fingerprint figure** (the centerpiece); LGR plume.
- Report mass-balance closure number; reframe `g` as interception fraction post-LGR.

---

## 5. Sequencing & gates
1. **Spike (½ day):** pull the Rogue multi-analyte surface + GW tables, plot the analyte-ratio
   fingerprints (surface stations vs. plume wells). Confirm separability. → decide T1.1 scope.
2. **T1.3** (cheap) → **T1.1** (core). *Gate G1:* clean fingerprint separation?
   - Yes → spine set; T1.2 is refinement.
   - No → T1.2 (LGR) + T1.3 become load-bearing; reassess.
3. **T1.2 LGR** → sharpen GWT + make `g` physical.
4. **T2.1 / T2.3** firm up support. Reassess T2.2 / T3.1 / T3.2 against the story.
5. Rewrite paper around the robust result.

## 6. Decisions (locked 2026-06-24)
- **Analyte set = lean 5:** PFOS, PFOA, PFHxS, PFBS, PFHxA (sorptive↔mobile span, strong detects in
  both compartments).
- **Refinement = DISV quadtree** (T1.2). More general/reusable for the national archive than LGR;
  bigger MODGenX change — the generator must emit an unstructured quadtree grid + re-plumb flow
  calibration on it. Consistent with the archive-scale ambition.
- **Scope = N=1 RIGOROUS (Rogue only)** — revised 2026-06-24 after the spike. The 2nd basin is
  unsupported by current data (only the Rogue has a multi-analyte GW plume in `site.db`; a 2nd basin
  needs a PFAS-ingestion sub-project first). Decision: one basin done bulletproof (multi-analyte +
  DISV + full validation); "archive-scale" stays a methods claim backed by the automated pipeline.
  T3.1 (2nd basin) dropped from this paper. DISV therefore only needs to refine the Rogue source
  corridor (lower effort than basin-agnostic).

## 7. Implications of the locked decisions
- **2nd-basin selection is now a gating task** (do it in the spike): query `site.db` for watersheds
  near a USGS gauge that have (a) a documented PFAS source (`pfas_site`), (b) a dense groundwater PFAS
  plume (multi-analyte wells), and (c) multi-analyte in-stream stations. Shortlist 2–3, pick one.
  Michigan has the most candidates (EGLE coverage), but a second-state basin would strengthen the
  generality claim more.
- **DISV is the long pole.** Sequence it so T1.1 (multi-analyte on the existing 250 m grid) proves the
  fingerprint first (Gate G1) *before* sinking effort into the DISV generator — if the fingerprint
  doesn't separate on the coarse grid, DISV won't save it.
- **Both basins get the full chain** (multi-analyte + DISV + validation), so Tier 2 (flow-cal upgrade,
  mass-balance closure) must run per basin.

## 7b. Lessons from prior WR PFAS reviews + EGLE site data (2026-06-24)

**From a Water Research PFAS review (ms 2024WR037707) — what WR reviewers demand:**
1. **Field-data validation + literature cross-check of mechanisms** (AE pt1, R2 C1/C2). → our
   observed multi-analyte fingerprint + EGLE corroboration answer this. **Cite the chromatographic-
   separation literature that underpins the fingerprint** (short-chain PFAS migrate faster than
   long-chain): Bigler et al. 2024 (ES&T, depth-discrete center-of-mass ∝ molar volume/chain length),
   Brusseau et al. 2020, Schaefer et al. 2022/2023, Dauchy et al. 2019, Stults et al. 2024. This makes
   the fingerprint reframe *grounded science*, not a clever trick.
2. **Global SA is effectively mandatory** (AE pt3, R3 C1 cites Saltelli 2010/2019 "why SAs are
   false"). We have Morris ✓; do Sobol on the scoped params (T3.2). Avoid OAT — the Freundlich/Langmuir
   nonlinearity makes OAT "controversial."
3. **Physically justify every simplification** (AE pt4, R3 C2): dimensionality, steady-flow-for-
   transient, structured-vs-refined grid, preferential flow.
4. Cite the Guo/Brusseau (Arizona) vadose PFAS lineage (Zeng & Guo 2021/2023; Guo 2022) the surface
   engine builds on.

**From the EGLE RRT presentation (2021) — site facts that change the model:**
- **MULTIPLE named sources, not one:** House Street Disposal Area, the **Tannery (Rockford, directly on
  the Rogue)**, Wolven-Jewell gravel-pit source area, North Kent Landfill, Northeast Gravel site
  (+109 dump sites; leather scraps along the Rogue). Model currently uses House Street only.
- **The Tannery sits on the Rogue at Rockford = the lower-mainstem reaches (ch1,2,10)** where the
  fingerprint found high f_gw but the single-source model under-credited it → **the missing Tannery
  source likely closes that model–data gap.** Promotes T1.3 to necessary, with named sources.
- House St is **on a groundwater divide; "Rogue River encircles the area"**, flow in multiple
  directions toward the river — independent confirmation of the GW→stream pathway.
- Geology: surficial clay over sand to 175 ft, first impacted aquifer ~60 ft; **paleo-drainage
  channels route flow to the river** (preferential paths the 250 m grid can't resolve → justifies DISV).
- DW well peak 96,000 ppt (House St); EGLE CSM built from Lidar + Wellogic well logs + soil survey —
  same data lineage as our automated pipeline.

**Net effect on priorities:** (a) add named multi-sources (T1.3) — likely reconciles model with the
observed fingerprint at the lower mainstem; (b) frame the fingerprint with the chromatographic-
separation literature; (c) keep SA strong (Morris→Sobol); (d) DISV justified by paleochannels +
the Tannery's near-river discharge geometry.

## 7c. REDESIGN from the EGLE North Kent multi-media data (2026-06-24)

New public data ingested (`ingest_egle_north_kent.py`): soil (706 sites, PFOS→220,000 µg/kg),
porewater (43 sites, multi-analyte), EGLE groundwater (67 wells incl. North Kent Landfill), Wolverine
surface water (50), foam. This changes the paper's validation architecture from "one weak leg" to a
**full causal-chain validation of the groundwater pathway**:

1. **Source — aquifer plume:** Wolverine (893) + EGLE (67) monitoring wells, 5-analyte.
2. **Discharge interface — POREWATER (NEW, the missing link):** 43 streambed porewater sites, ALL
   within 100 m of a channel, 42 within 300 m of the mainstem, on channels 1/2/11/15 (the high-f_gw
   reaches). Multi-analyte (PFOS 37/43 det, PFOA/PFBS/PFHxS/PFHxA). This is the measured concentration
   of groundwater AS IT DISCHARGES to the stream — retires the "attribution rests on the weak 1.4-dex
   aquifer validation" caveat by validating the pathway at the discharge point itself.
3. **Receiving water — in-stream multi-analyte fingerprint** (EMMA, already validated).
4. **Surface source — measured soil** (706 sites, on ch 9/10/11 = Tannery/Rockford corridor) replaces
   the free-fitted soil-loading scalar AND resolves the GW-vs-Tannery-surface ambiguity (divergent vs
   shared signatures between soil and porewater).

**Model-accuracy re-examination:** (a) GW plume validation on the expanded Wolverine+EGLE 5-analyte
set; (b) POREWATER discharge validation (modeled aquifer conc at streambed discharge cells vs measured
porewater, per analyte) — NEW; (c) surface soil constraint (modeled vs measured source-zone soil);
(d) transient flow recalibration vs the 2019–2024 dated water-table elevations (retires single-baseflow
weakness); (e) fingerprint EMMA refreshed with expanded surface water. Status: starting with (b).

## 7d. Conclusion-phase + spin-up design (Vahid brainstorm, 2026-06-24/25)

Four reviewer-grade items raised by Vahid; all to be addressed before the accuracy claims are final.

**(i) Report LOAD (mass flux), not just concentration.** Concentration is intensive; the conserved,
mass-balancing quantity is load = C × Q. The coupled model already routes MASS (SFT), so:
- GW-discharged load per reach = (SFR gaining flux, m³/d) × (discharge conc, ng/L), pulled from the
  SFT mass budget (`pfas.sft.cbc`), NOT reconstructed from mismatched tables.
- In-stream observed load = C_obs × Q (gauge 04118500; drainage-scaled elsewhere) → compare load↔load.
- **Basin mass-balance closure %** (Σ source inputs = outlet export + storage Δ) — quantifies the
  "continuous mass balance" the paper asserts but never computed. PREREQUISITE: fix the SFR-reach→
  rivs1-channel index (authoritative = SFR packagedata cellid; has bitten Test 2 + the load calc).

**(ii) Range-stratified error + MDL-aware.** log-RMSE is range-blind: a ×4 miss at 1 ng/L (near the
~2 ng/L MDL = measurement noise) ≠ ×4 at 10→40 ng/L (a real miss). Report skill by concentration band
and treat near-MDL points separately; load-space reporting (i) auto-down-weights low-flow/low-conc noise.

**(iii) Data-uncertainty floor.** PFAS obs carry MDL censoring, lab/field variability, and (worst for
surface water) temporal representativeness (a grab sample is one instant). Quantify where data allows
(replicate spread, MDL bands, temporal range at multi-sample sites); this sets the floor below which
"model error" is meaningless.

**(iv) Formal UA capstone → model-confidence statement.** Morris (done) → Sobol on scoped params →
posterior-predictive uncertainty → a stated confidence envelope per prediction, against the (iii) floor.
The honest conclusion is a confidence statement, not a point estimate (answers the WR Saltelli demand).

**Derived-source transient spin-up (replaces the prescribed static plume).** VERIFIED 2026-06-24:
SWAT+ runs ANY period via the wgn weather generator — not bounded by PRISM 2000–2024 (test: 1970–1972
ran clean, no measured weather) [[swatplus-wgen-out-of-range]]. So: run the SWAT+ PFAS engine
**1970→2024** with the measured source-zone soil (220,000 µg/kg) as the initial condition; **wgn drives
1970–1999 spin-up** (equilibration only — NO observations there to match, so a weather generator is the
*correct* choice, not a fallback; real daily weather would add false precision), **real PRISM drives
2000–2024**. The engine then DERIVES the time-varying vadose→groundwater PFAS leaching flux as the GWT
source — the mechanistic "continuous land→vadose→aquifer mass balance," and the answer to "is the source
still being fed?" (PFOS leaches for decades). What matters in spin-up = the PFAS loading history
(disposal ~1958–1970 + soil IC), not the weather realization.

## 8. Immediate next step — the spike (½–1 day)
1. Pull Rogue multi-analyte surface + GW tables (lean-5), plot analyte-ratio fingerprints
   (surface stations vs. plume wells). **Confirm separability (Gate G1 dry-run).**
2. Run the 2nd-basin selection query; shortlist candidates with the (source + plume + in-stream) triad.
3. Report both → lock 2nd basin + confirm T1.1 scope, then build.

I have sufficient evidence to assemble the dossier. The Shanghai model is the key competitor (coupled hydrology + sediment multimedia), but it is a lumped river-network multimedia-box model, not an HRU-resolved process-based watershed model — preserving our high-resolution novelty. Compiling the deliverable now.

---

# STREAM 2 DOSSIER — Huron PFAS Observational-Data Inventory & Novelty Assessment

**Scope:** What observed PFAS/flow data exist for the Huron River (SE Michigan) beyond the 128 EGLE surface-water stations already ingested, whether they suffice to calibrate/validate a high-resolution SWAT+ PFAS model, and how the paper's novelty survives the competing process-based watershed PFAS models. Grading: 🟢 supports the paper, 🟡 mixed/manageable, 🔴 threatens the paper.

A reconciliation note up front, because it matters for the whole inventory: the prompt cites the model domain as **HUC8 04100013**, but EGLE's authoritative surface-water PFAS feed labels the SE-Michigan Huron River basin as **HUC8 04090005** (04100013 in the national WBD is the Clinton/Lake St. Clair area). The USGS gauges resolve to mixed HUC strings too (e.g., Hamburg → `041000130112`). The team should explicitly confirm which HUC8 string its domain polygon carries and standardize labeling before any "we cover HUC8 X" claim goes in the manuscript — a reviewer in this exact watershed will check. I queried EGLE on `Watershed='Huron'` (HUC8 04090005) and it returns precisely the 128 stations / 218 records the team already holds, so the datasets are the same basin regardless of the code.

---

## A. EGLE Huron surface-water PFAS — full time-series depth 🟢 (with a real caveat)

**Source:** EGLE PFAS Surface Water Sampling feed (MPART). Live REST endpoint:
`https://gisagoegle.state.mi.us/arcgis/rest/services/EGLE/PfasOpenData/MapServer/0` — bulk CSV/GeoJSON/Shapefile/GDB download via the EGLE hub item `391cca4f364845829abcd5a92093c631`. Statewide count today: **4,053 sample-level records.** Schema is **sample-level, not aggregated** — one row per `LabSampleId` × `CollectionDate`, with `Longitude/Latitude`, `Waterbody`, `LocationCode`, `Matrix`, `CollectionDate`, and ~40 analyte columns each carrying value + `Flag` + `Mdl` + `Rl` (method detection / reporting limits). Analytes include PFOS, PFOA, the C4–C14 carboxylates/sulfonates **plus 6:2 FTS, 8:2 FTS, FOSAs, GenX, ADONA, F-53B** — i.e., richer than the 10 analytes the team's aggregated table carries.

**Huron-basin contents (queried live):** **218 surface-water records across 128 distinct `LocationCode` stations**, 48 waterbodies. Year distribution: 2001(1), **2018(80), 2019(38), 2020(48)**, 2021(6), 2022(15), 2023(6), **2024(22)**, 2025(2). Matrix is **100% water** (`Water`/`H2O`/`H20` — all the same; note the dirty `H20` typo to clean on ingest). Top waterbodies by sample count: Huron River (70), Norton Creek (20), South Ore Creek (12), Regan Drain (11), Honey Creek (9), Willow Run (9), Pettibone Creek (7).

**The caveat is confirmed and it is real:** mean ≈1.7 samples/station; only **10 stations have ≥4 repeats.** This feed *is* the team's already-ingested data — there is **no hidden denser EGLE surface-water layer** to mine. So spatial coverage is excellent, per-station temporal depth is thin in the median.

**BUT** — and this materially upgrades the verdict — the densest stations sit exactly where the science is, and they carry a clean **multi-year decline curve** (the post-treatment recovery signal):

- **NC-0010 (Norton Creek):** 2018-07-24 **5,600** → 1,500 (Aug) → 0.52 (Sep) → 88 (Oct) → 13 (2019-04) → 12.2 (2020-08) → 1.21 (2020-09) ng/L PFOS.
- **NC-0030 (Norton Creek):** 1,900 (2018-08) → 75 → 13 → 8.28 → **6.8 (2022-08)** — spans 2018→2022.
- **HR-0690 (Huron R. below Norton):** 1,400 (2018-07) → 480 → 21 → 2.9 → 6.13 (2020-08).
- **HR-0700 (Huron R.):** stable low ~1–2.6 ng/L across 2018–2020 (a useful unimpacted control reach).
- **RG-0005 (Regan Drain):** five samples within 2020-08→2020-10 (within-event replication).
- **470581 (South Ore Creek):** 10 samples across 2021-05→2022-11 — a dense bi-monthly series at low concentration.

**Verdict:** **Supports temporal-trend validation 🟢** at the source reaches (Norton Creek/Wixom/Kent Lake corridor) — the 1,400→6 ng/L Huron-River and 5,600→12 ng/L Norton-Creek declines after the Wixom WWTP granular-activated-carbon installation are a genuine, publicly documented, model-testable transient. **Supports broad spatial PFOS calibration 🟢** (128 stations is exceptional spatial density for a single watershed). **Does not support dense per-station hydrograph-style temporal calibration 🟡** outside the ~10 repeat stations. The honest framing for the manuscript: *spatially rich snapshot calibration + a small number of multi-year decline series for transient validation.* Note EGLE corroborates these declines in its Aug-2020 update (1,400→6.1 ppt main stem; Norton Creek −99.8%, 5,600→12.2 ppt) and a later WRD report.

---

## B. Fish-tissue PFAS — validates the sediment-legacy story 🟢 (strong, and NOT yet held)

Three independent fish datasets exist; the team holds none of them. This is the most valuable un-ingested asset.

1. **MDHHS Eat Safe Fish / "Do Not Eat" program (2017–present) 🟢.** PFOS in Kent Lake fillets in 2017 triggered the **Aug 2018 "Do Not Eat" advisory** (Kent Lake, Hubbell/Mill Pond, then extended to the Huron R. at N. Wixom Rd and Norton Creek). Michigan tightened its "Do Not Eat" PFOS fillet threshold from **300 → 50 ppb** in 2023. MDHHS/EGLE Fish Contaminant Monitoring Program fillet data are obtainable (some via the state; raw fillet ppb often requires a data request). **Verdict: supports sediment-legacy validation** — fillet PFOS is the standing-stock endpoint a sediment-source model predicts via a BAF.

2. **Ecology Center 2023 "100-fish" community study 🟢 — peer-reviewed and the best-documented.** Anglers hand-caught **100 fish, 12 species, 15 sites** across the Huron + Rouge; tested for **40 PFAS**; **every fish had ≥1 PFAS**, fillet ΣPFAS **11–133 ppb**. Published as **Wu, Schwartz, et al., *Chemosphere* 2023** ("From watersheds to dinner plates: Evaluating PFAS exposure through fish consumption in Southeast Michigan," `S0045653523027248`, DOI 10.1016/j.chemosphere.2023.140802). Per-fish, per-site, per-analyte data are in SI — directly ingestible. **Verdict: supports sediment-legacy + spatial bioaccumulation validation** (independent of state advisory data).

3. **Endicott et al. 2025 biota (see C)** — benthos, forage fish, predator fish whole-body composites from Kent Lake + reference lake, 2021. **Verdict: the cleanest sediment→biota dataset for BSAF validation.**

**Net:** fish tissue is plentiful, partly peer-reviewed, and currently **un-held — this is a fillable gap, not a wall.**

---

## C. Sediment PFAS — the centerpiece compartment 🟢🔴 (the make-or-break dataset)

**Endicott, Silva-Wilkinson, McCauley & Armstrong (2025)** — *"Per- and polyfluoroalkyl substances (PFAS) in sediment: a source of PFAS to the food web?"*, **Integrated Environmental Assessment and Management 21(4):810–822, July 2025, DOI 10.1093/inteam/vjaf010** (PubMed 39903053). PFAS sampled in **water, sediment, and biota from Kent Lake + a reference lake, 2021**; biota as whole-body composites; **PFOS and 6:2 FTS dominant** in both sediment and biota. Critically, the paper reports **partition coefficients AND bioaccumulation factors**, and concludes sediment is an **ongoing source to the food web** — i.e., it independently asserts the exact legacy-sediment mechanism this SWAT+ paper is built around, and hands over the sediment–water Kd/Koc and BSAF parameters the fate model needs to parameterize and to validate against.

**Two-sided grade:**
- 🟢 **Supports sediment-legacy validation + parameterization** — there is a real, recent, peer-reviewed Kent Lake sediment PFAS dataset with partition coefficients. This is rare for any watershed and is the strongest possible external corroboration of the paper's thesis.
- 🔴 **Threatens the narrative on two fronts the team must pre-empt:** (i) the numeric sediment concentrations (ng/g dw), core counts, and Kd/BSAF values are **paywalled** — I could not extract them via WebFetch (OUP 403/paywall). The team must obtain the full text and SI (institutional access or author request to Endicott) before claiming sediment calibration; right now the team holds **zero sediment PFAS records.** (ii) Endicott 2025 already publishes the sediment-source conclusion qualitatively — so the SWAT+ paper's novelty cannot be "sediment is a legacy source" (Endicott owns that claim). It must be **"a spatially distributed, process-based, HRU-resolved model that *quantifies and routes* that legacy flux across the whole network and reproduces both the spatial PFOS field and the post-treatment decline."** Position Endicott as the validating data source, not a scoop.

---

## D. USGS Huron PFAS 🟡 (mostly a non-source — useful to state explicitly)

I queried the USGS/NWIS **Water Quality Portal** for PFOS (Perfluorooctanesulfonate) in HUC8 04090005: **0 results, 0 stations.** USGS is **not** a meaningful PFAS *concentration* provider for this watershed — the Huron PFAS record is overwhelmingly EGLE + MDHHS + the academic studies above. The only USGS PFAS-adjacent work is a **2019 POCIS passive-sampler pilot** (4 sites, 28-day deployment, Sept 26–Oct 24 2019) reported in the EGLE/USGS source-investigation work — useful as qualitative corroboration, not as calibration targets. **Verdict: do not rely on USGS for PFAS; state plainly that EGLE is the authoritative surface-water source.** (Low threat — but a reviewer may ask "why no USGS PFAS?" and the answer is simply that USGS has not sampled PFAS here.)

---

## E. Flow gauges — hydrology calibration 🟢 (strong)

USGS streamflow is robust and dense for this basin. Active daily-discharge (param 00060) gauges in/around the Huron domain, queried live from NWIS:

| Gauge | Name | Drainage area (mi²) | Role |
|---|---|---|---|
| **04172000** | Huron R. near Hamburg | 308 | Upper main stem (above Kent Lake corridor) |
| **04173000** | Huron R. near Dexter | 522 | Mid main stem |
| **04173500** | Mill Creek near Dexter | 128 | Major tributary |
| **04174040** | Huron R. at Zeeb Rd at Scio | 700 | Lower main stem |
| **04174500** | Huron R. at Ann Arbor | 729 | Outlet-region anchor (long record) |
| **04174518** | Malletts Creek at Ann Arbor | 10.9 | Small urban tributary (nested) |

That is a **nested multi-scale set (10.9 → 729 mi²)** spanning headwater tributaries to the outlet — ideal for spatially distributed flow calibration and the kind of multi-gauge validation a high-resolution model warrants. The Ann Arbor (04174500) and Hamburg (04172000) records are long (decadal+), and Wall Street/Ann Arbor is the standard reference gauge. **Verdict: fully supports flow/hydrology calibration 🟢** — no gap here. Note: the principal PFAS source (Wixom WWTP/Norton Creek) sits **upstream of Hamburg**, so flow at Hamburg + the Norton Creek confluence frames the PFAS mass-balance corridor; consider whether a gauge or a synthetic flow estimate is needed on Norton Creek itself (currently ungauged for discharge — minor gap).

---

## NOVELTY DEFENSE — competing process-based watershed PFAS models

| Model / study | Watershed | Type & resolution | Sediment? | Calibrated to obs? | Threat |
|---|---|---|---|---|---|
| **Rafiei & Nejadhashemi 2023**, *Water Research* (S0043135423005092; PubMed 37235893) — **SMR-W (SWAT-MODFLOW-RT3D)** | **Huron (same)** | Process-based, **~189 reaches** | Yes (sediment transport pathway) | Yes (flow NSE>0.6; PFOS) | 🟡 **Predecessor, same watershed/team** — novelty must be explicit delta |
| **This paper** | Huron | **SWAT+, 3,119 reaches / 72,475 HRUs** | Sediment legacy = centerpiece | EGLE 128 stns + decline series + Endicott sediment | — |
| **Shanghai river-network model**, *J. Hydrology* 2024 (S0022169424019887) | Shanghai | Coupled hydrology + **multimedia box** model; PFOA/PFOS in water+sediment; 1990–2022 | Yes (water+sediment) | Yes (field-measured) | 🟡 **Closest external competitor** — but lumped river-network multimedia boxes, **not HRU-resolved upland fate**; urban, not legacy-recovery |
| **Zhang, Babbar-Sebens, Ahmadisharaf & Imen 2025**, *J. Env. Eng.* 151(11) (JOEEDU.EEENG-8137) — **review, not a model** | n/a | Review of watershed/receiving-water PFAS models | — | — | 🟢 **Helps us** — names the gaps (high-resolution, sediment legacy, episodic events, calibration data) we fill; cite as the gap statement |
| EPA TMDL Modeling Toolbox; "Opportunities & Challenges" case study, *J. Env. Eng.* 148(9) 2022 | various | Screening/integrated, coarse | Partial | Limited | 🟢 Lower-resolution; supports our resolution claim |

**Where novelty is genuinely safe (lead with these):**
1. **Resolution leap is real and quantified:** 3,119 reaches / 72,475 HRUs vs the predecessor's ~189 reaches — a **~16× reach-density** increase in the *same* watershed. No published process-based watershed PFAS model approaches this HRU/reach count.
2. **SWAT+ (vs legacy SWAT-MODFLOW-RT3D):** modern restructured engine, channel-resolved routing — a different modeling platform, not a re-run.
3. **Legacy-sediment quantification + transient recovery:** reproducing the 2018→2020/2022 post-treatment decline as a model-validated transient, with sediment flux routed network-wide, is not done elsewhere. Shanghai is steady-state urban loading; Endicott is a two-lake empirical study; Rafiei 2023 was source-ID, not recovery-trajectory.

**Where novelty is exposed (defend explicitly):**
- 🔴 **"Sediment is a legacy PFAS source"** is *already claimed* by Endicott 2025 (empirically) and Rafiei 2023 (modeled). The paper cannot claim to discover this. Reframe novelty as *quantification, spatial distribution, and network routing of that flux at high resolution, validated against independent sediment+fish data.*
- 🟡 **Same watershed + same lead author as the 2023 predecessor.** Reviewers will probe "what's new vs your own prior work." The delta must be explicit in the intro: platform (SWAT+ vs SWAT-MODFLOW-RT3D), resolution (16×), compartment focus (legacy sediment recovery vs source ID), and validation breadth (adds Endicott sediment + Ecology Center/MDHHS fish).
- 🟡 The Shanghai 2024 model means "first coupled hydrology+sediment PFAS watershed model" is **false** — do not claim it. Claim "first **high-resolution, HRU-distributed, process-based** PFAS surface-water/sediment model" and cite Shanghai as the (lumped, urban) contrast.

---

## SUFFICIENCY VERDICT (per objective)

- **Flow calibration:** 🟢 sufficient now — 6 nested USGS gauges, no action needed (optionally add a Norton Creek flow estimate).
- **Spatial PFOS calibration:** 🟢 sufficient — 128 EGLE stations already held; consider re-ingesting the *sample-level* feed to recover full dates + 40 analytes (6:2 FTS especially, given Endicott shows it co-dominant).
- **Temporal-trend validation:** 🟢/🟡 sufficient at ~10 repeat stations (the Norton/Huron decline curves); thin elsewhere — frame honestly.
- **Sediment-legacy validation:** 🔴→🟢 **conditional** — the data EXISTS (Endicott 2025 Kent Lake sediment + Kd/BSAF) but is **not yet held and is paywalled.** This is the binding constraint.

---

## THE SINGLE BIGGEST DATA GAP — and how to fill it

**The gap: in-house sediment PFAS data is zero.** The paper's centerpiece compartment (legacy sediment as an ongoing PFOS source) currently rests entirely on the *paywalled* Endicott et al. 2025 Kent Lake study, of which the team holds none of the numeric sediment concentrations, core/station counts, or the sediment–water partition coefficients (Kd/Koc) and BSAFs that the fate model must both ingest as parameters and validate against. Without it, the sediment-legacy claim is asserted, not demonstrated — and a reviewer in this watershed will catch it immediately.

**How to fill it (in priority order):**
1. **Obtain Endicott et al. 2025 full text + SI** (IEAM, DOI 10.1093/inteam/vjaf010) via institutional access or a direct request to the corresponding author (Douglas Endicott). Extract sediment ng/g, sample locations/counts, Kd/Koc, and BSAFs — these become both calibration parameters and validation targets. **Fastest, highest-value step.**
2. **File an EGLE/MPART data request** for any Kent Lake / Proud Lake sediment + fish PFAS collected under the 2018–2021 Huron investigation (the EGLE work explicitly planned sediment + macroinvertebrate + fish collection from Kent and Proud Lakes). Some may not be in the public ArcGIS feed (which is water-only — confirmed: matrix is 100% water statewide).
3. **Ingest the Ecology Center 2023 *Chemosphere* SI** (Wu et al., DOI 10.1016/j.chemosphere.2023.140802) for per-site Huron fish fillet PFOS/ΣPFAS as an independent bioaccumulation validation layer — open and immediately usable.
4. **Re-ingest the sample-level EGLE surface-water feed** (REST endpoint above) to replace the team's aggregated table with full date/value/analyte rows — recovers the decline-curve time series and 6:2 FTS, at zero new fieldwork.

If only one thing happens before submission: **secure the Endicott 2025 sediment dataset.** It is the difference between a validated sediment-legacy paper and an unsupported one.

---

**Sources:**
- [EGLE Huron River PFAS investigation page](https://www.michigan.gov/pfasresponse/investigations/lakes-and-streams/huron-river) · [EGLE PFAS Surface Water Sampling dataset (ArcGIS hub)](https://gis-egle.hub.arcgis.com/datasets/egle::pfas-surface-water-sampling) · REST: `https://gisagoegle.state.mi.us/arcgis/rest/services/EGLE/PfasOpenData/MapServer/0`
- [EGLE: PFAS drop after upstream treatment](https://origin-sl.michigan.gov/egle/0,9429,7-135-3308-542999--,00.html) · [EGLE WRD-20/020 Huron source investigation (PDF)](https://www.michigan.gov/-/media/Project/Websites/PFAS-Response/Watersheds/Huron-River/Investigation_of_the_Occurrence_and_Sources_of_PFAS_in_the_Huron_River_Watershed_Using_Pol.pdf)
- [Endicott et al. 2025, IEAM (Kent Lake sediment)](https://academic.oup.com/ieam/article-abstract/21/4/810/7998487) · [PubMed 39903053](https://pubmed.ncbi.nlm.nih.gov/39903053/) — DOI 10.1093/inteam/vjaf010
- [MDHHS Huron "Do Not Eat" advisory](https://michigan.gov/mdhhs/0,5885,7-339-73970_71692_71696-475982--,00.html) · [2023 Eat Safe Fish guides](https://www.michigan.gov/pfasresponse/about/news/2023/08/11/eat-safe-fish-2023)
- [Ecology Center 100-fish study](https://www.ecocenter.org/anglers-find-forever-chemicals-every-fish-tested-huron-and-rouge-rivers) · [Wu et al. 2023, Chemosphere](https://www.sciencedirect.com/science/article/abs/pii/S0045653523027248)
- [Rafiei & Nejadhashemi 2023, Water Research (SMR-W)](https://www.sciencedirect.com/science/article/abs/pii/S0043135423005092) · [PubMed 37235893](https://pubmed.ncbi.nlm.nih.gov/37235893/)
- [Shanghai coupled hydrological-multimedia PFAS model, J. Hydrology 2024](https://www.sciencedirect.com/science/article/abs/pii/S0022169424019887)
- [Zhang et al. 2025 review, J. Env. Eng.](https://ascelibrary.org/doi/10.1061/JOEEDU.EEENG-8137) · [Integrated large-scale PFAS modeling case study, J. Env. Eng. 2022](https://ascelibrary.com/doi/10.1061/(ASCE)EE.1943-7870.0002034)
- USGS NWIS gauges (live): 04172000, 04173000, 04173500, 04174040, 04174500, 04174518 via `https://waterservices.usgs.gov/nwis/site/` · USGS Water Quality Portal (0 PFOS in HUC 04090005): `https://www.waterqualitydata.us/`
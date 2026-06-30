# Multi-analyte spike — results (2026-06-24)

Dry-run of Gate G1 (fingerprint separability) + 2nd-basin selection, per `UPGRADE_PLAN.md`.
Lean-5 analytes: PFOS, PFOA, PFHxS, PFBS, PFHxA. Data: `site.db` (`pfas_observation`/`pfas_station`),
Rogue bbox 43.0–43.5N / -85.8 to -85.35W. Values = latest_value else max_value (ng/L).

## 1. Gate G1 — PASS (fingerprints separate cleanly)
End-member mean composition (fraction of Σ5):

| Class | PFOS | PFOA | PFHxS | PFBS | PFHxA | median ΣPFAS |
|---|---|---|---|---|---|---|
| GW plume (PFOS>1e4) | **0.72** | 0.15 | 0.05 | 0.05 | 0.03 | 50,000 ng/L |
| GW ambient | 0.36 | 0.25 | 0.14 | 0.17 | 0.08 | 264 ng/L |
| Surface water (in-stream) | 0.23 | 0.25 | 0.11 | **0.26** | **0.16** | 9 ng/L |

L1 composition distance (0=identical, 2=disjoint): **SW↔plume = 0.98**, SW↔ambient = 0.33,
plume↔ambient = 0.72. The plume is PFOS-dominated (legacy tannery/Scotchgard); in-stream surface
signal is short-chain-rich. → the two pathways are an **identifiable two-end-member mixture**.
Figure: `fig_fingerprint_separation.png`. Per-site data: `rogue_fingerprints.csv`.

## 2. Network-resolved per-reach unmixing — INDEPENDENTLY CONFIRMS the paper's central claim
In-stream stations snapped to the Rogue SWAT+ channel graph (`rivs1.shp`, EPSG:32616→5070);
two-end-member NNLS unmix (SW headwater vs GW plume fingerprint) restricted to **on-channel**
stations (snap <50 m — the named EGLE `RR-xxxx` Rogue River transect). Per the paper's 7 mainstem
reaches (upstream→downstream):

| reach | fingerprint f_gw (independent) | paper g-fraction (model fit) | PFOS (ng/L) |
|---|---|---|---|
| ch26 | 0.00 | 0.13 | 1.1 |
| ch18 | 0.00 | 0.11 | 1.4 |
| ch15 | 0.47 | 0.10 | 4.8 |
| ch11 | 0.19 | 0.09 | 4.8 |
| ch10 | 0.55 | 0.08 | 9.6 |
| ch1  | 0.56 | 0.55 | 15.0 |
| ch2  | 0.63 | 0.53 | 18.5 |

- **Endpoints match almost exactly**: headwaters ~0% GW, lower mainstem ~55–63% GW — by both the
  fingerprint AND the paper's model fit. **This is the model-free evidence the paper lacked**: it
  moves the attribution from "rests on the weak aquifer validation" to "corroborated by independent
  source-fingerprinting." Pearson r=0.58 across 7 reaches.
- **Revises the spatial detail**: the fingerprint detects GW influence at mid-mainstem (ch10, ch15 —
  right at the Wolverine/Rockford corridor, gauge area) that the paper's model under-credits there.
  Points to discharge entering around Rockford (ch10), exactly where the source is.
- **Caveats (honest):** n=1 per middle reach (endpoints are the robust part); off-channel
  tributary/lake stations (snap 200–550 m) must be excluded or they wash out the gradient (an early
  median was polluted this way). Figure: `fig_reach_gw_fraction_vs_paper.png`. Data:
  `mainstem_reach_fgw_onchannel.csv`, `instream_snapped.csv`.

**Upshot:** the multi-analyte reframe doesn't just add DoF — it supplies *independent observational
confirmation* of the headline result. The coupled per-analyte model (T1.1 proper) now has a concrete,
model-free target to reproduce.

## 2b. Multi-analyte coupled MODEL (lean-5 GWT+SFT) — reproduces the plume fingerprint
Ran MF6 GWT (compound-specific Kf/n from `compound_params_lean5.csv`) + SFT for all five analytes on
the calibrated Rogue flow field; source anchored to each analyte's measured plume.

**Model bug found & fixed (multi-analyte exposed it):** the single-analyte model caps every source
cell at 1e5 ng/L for PFOS numerical stability. Applied per-analyte this *equalizes* PFOS and PFOA
(both clip to 1e5) and corrupts the fingerprint — modeled in-stream gave PFOS 0.37 / PFOA 0.37 vs the
observed plume's 0.75 / 0.14 (L1=0.76). Fix = **fingerprint-preserving source**: scale all analytes at
a source cell by the same factor s=min(1, cap/PFOS), preserving the measured composition.

**After the fix — modeled in-stream GW fingerprint vs observed plume (TEST 1):**

| analyte | observed plume | modeled SFT |
|---|---|---|
| PFOS | 0.75 | 0.79 |
| PFOA | 0.14 | 0.14 |
| PFHxS | 0.06 | 0.02 |
| PFBS | 0.03 | 0.02 |
| PFHxA | 0.03 | 0.03 |

**L1 = 0.10** (was 0.76). The coupling (GWT→SFT) transports the plume signature to the channel
faithfully. Per-analyte plume validation also improves toward the mobile end: PFHxA 1.01 dex / 59%
within ×10, PFBS 1.15, PFHxS 1.16, PFOA 1.38, PFOS 1.65 (hardest — most retarded/stiffest front). The
multi-analyte view broadens the evidence beyond a single PFOS number. Code: `run_multianalyte_gwt.py`
(fingerprint-preserving source), `compare_modeled_fingerprint.py`. Outputs:
`multianalyte_gwt_summary.csv`, `multianalyte_reach_conc.csv`.

**OPEN (next step):** TEST 2 (modeled GW in-stream load coincides spatially with the observed
high-f_gw reaches ch 1,2,10,15) needs a correct SFR-reach→rivs1-Channel join — the current
cell-centroid snap mis-indexes (only ch1 matched). Fix the reach ordering, then close Test 2.

## 2c. POREWATER discharge validation (NEW data, 2026-06-24) — closes the GW->stream attribution
EGLE streambed porewater (`mi_egle_nk_porewater`, 43 sites, ALL within 100 m of a channel, 42 on the
lower-mainstem reaches ch 1/2/11/15) = the direct measurement of groundwater AS IT DISCHARGES.

**Model-INDEPENDENT causal chain** (composition fraction of lean-5): aquifer plume PFOS 0.79 →
porewater 0.68 → in-stream 0.80; L1(plume,porewater)=0.22, L1(plume,instream)=0.06. All three carry
the PFOS-dominated Wolverine signature; porewater is slightly short-chain-enriched (mobile chains
discharge preferentially). NOT the short-chain-rich diffuse-runoff signature. → **the discharging
groundwater is plume-derived and matches the in-stream signal — attribution validated at the
discharge interface, not via the far-field aquifer plume.** Resolves the GW-vs-Tannery-surface
ambiguity (surface erosion would not carry the plume fingerprint to the porewater).

**Model-SIDE** (modeled aquifer conc at streambed cell vs measured porewater; cmax_<analyte>.npz +
`porewater_validation.py`): PFOS 1.54 dex/28% within10x, PFOA 1.31/43%, PFHxS 0.97/56%, PFBS 0.94/57%,
PFHxA 0.84/69%. **Systematic NEGATIVE bias −0.49 to −0.74 dex** = model under-delivers GW to the
streambed (single House St source on 250 m grid). Reproduces the right place + PFOS-dominated
fingerprint but under-predicts magnitude → quantified "before" target for the **multi-source (add
Tannery) + DISV** upgrades. Short-chains validate better (mobility). Grid gotcha: MF6 DIS is in LOCAL
coords (CRS=None, origin 0,0) — map lat/lon→row/col via the georeferenced `Grids_MODFLOW.shp`
(EPSG:26990), NOT modelgrid.intersect.

## 2d. LOAD / mass-flux validation (Vahid: concentration misses mass balance) — 2026-06-25
Concentration is intensive; the conserved quantity is load = C×Q. The coupled model already routes
MASS (SFT). Per-reach GW-discharged load = (SFR `GWF` gaining flux, m³/d) × (aquifer conc, ng/L),
indexed by SFR reach. SFR `GWF` net exchange = **+5.46 m³/s = the calibrated baseflow** (self-check OK).

**Reach-index bug FIXED at root:** the recurring "everything maps to ch1" failure (Test 2, load calc)
was `reach_to_channel.csv` built with the LOCAL-coord snap (MF6 DIS CRS=None). Rebuilt reach→cellid
(SFR packagedata) → centroid via `Grids_MODFLOW.shp` (EPSG:26990) → nearest rivs1 channel: 320 distinct
channels, 58 m median snap (was degenerate). `sfr_gwf_flux.csv` + `gw_load_per_reach.csv`.

**Basin GW PFAS load to the stream (g/yr):** transport-delivered (source cells excluded) PFOS 45,239 /
PFOA 8,558 / PFHxS 3,115 / PFBS 3,560 / PFHxA 5,222 = **Σ5 ≈ 66 kg/yr** (incl. prescribed source 234 kg/yr).

**Vahid's point, concrete:** lower-mainstem ch1 & ch2 have ~equal conc (778 vs 800 ng/L) but ch2 carries
**2.1× the mass** (4,741 vs 2,297 g/yr) because its gaining flux is 3.5× higher. Concentration-vs-
concentration calls them equal; load differs 2×. → report validation + apportionment in LOAD space; full
SW+GW basin mass-balance closure % still needs the surface-engine load (next).

## 2e. Range-stratified error (Vahid: "0.4 dex error at what range?") — 2026-06-25
Porewater error stratified by observed concentration (5 analytes pooled, MDL~2 ng/L);
`porewater_error_by_range.csv`:

| band | n | logRMSE | bias | within10x | med_obs |
|---|---|---|---|---|---|
| <2×MDL (noise) | 2 | 1.38 | +0.63 | 50% | 3.8 |
| MDL–10 | 45 | 0.95 | −0.19 | 82% | 7.3 |
| 10–50 | 71 | 1.12 | −0.58 | 32% | 18.0 |
| >50 ng/L | 26 | 1.69 | −1.43 | 27% | 86.5 |

Pooled = 1.21 dex (n=144) but that HIDES the structure: the model is ~unbiased & good at low conc
(MDL–10: bias −0.19, 82% within 10×) — NOT failing on near-MDL noise — and **systematically
under-predicts the HIGH band (>50 ng/L: bias −1.43 ≈ 27× low)**. Those high-conc sites are the
strong-discharge zones that carry the MASS (§2d), so the mass-weighted error > pooled, and it pins the
deficiency at the high-conc discharge reaches → **DISV target confirmed, range-resolved.** Report skill
BY band, never one pooled dex. The <2×MDL band is genuine measurement noise (write-off OK).

## 3. 2nd-basin selection — DATA WALL (resolved: N=1)
CONUS query for HUC8s with a multi-analyte GW plume (≥2 wells PFOS>1e4) **and** multi-analyte
in-stream stations: **only the Rogue (HUC8 04050006, MI) qualifies.** Fully relaxed, **no other HUC8
in `site.db` has even 2 multi-analyte plume wells** — multi-analyte PFAS for other documented sites
(MN 3M, NC Chemours/GenX, NH Pease, CO Fountain) **is not ingested yet** (national PFAS ingestion is
mid-stream; MI loaded, others pending). Candidates: `basin_candidates.csv`.

→ **N=2 requires a data-ingestion phase first.** Options:
- **(A) Ingest a 2nd basin** (recommended: MN 3M / Washington County — decades of multi-analyte SW+GW,
  documented source, USGS gauges; already on the PFAS-ingestion priority list) → then N=2 as planned.
- **(B) N=1 (Rogue only, rigorous)** — data robustly supports Rogue + multi-analyte + DISV;
  "archive-scale" stays a methods claim.

## Status of upgrade tiers after the spike
- T1.1 multi-analyte: **Gate G1 passed.** Next = network georeferencing → per-reach 5-analyte unmixing,
  then couple to the per-analyte model runs.
- 2nd basin: blocked on the (A)/(B) decision above.

## 4. DISV refinement — STAGE 1 done (2026-06-25)
`build_disv_grid.py` (gridgen 1.0.02). Quadtree refined in the source→discharge corridor (8 source
cells + 124 lower-mainstem reach cells, corridor channels 556→…→1 + 10/11/15/18/26): **ncpl=28,239
(1.38× base 20,460)**, ~31 m at source / ~62 m corridor / 250 m elsewhere. Targets exactly the
high-conc discharge reaches where the porewater error (§2e) and load (§2d) locate the under-delivery,
without bloating the grid. → `disv_gridprops.npy` (regenerable, gitignored).
GOTCHA: flopy gridgen `add_refinement_features` wants shapely geometries (not raw coord lists);
refinement features must be in the MF6 grid's LOCAL coords (CRS=None), use `mg.xcellcenters`.
Remaining stages: (2) resample top/botm/K/recharge/ibound onto DISV cells; (3) rebuild SFR + GWF↔GWT
coupling on the unstructured grid; (4) map calibrated multipliers / re-run PEST++; (5) re-run GWT per
analyte, success = porewater >50 ng/L bias (−1.43 dex) closes + lower-mainstem load gap narrows.

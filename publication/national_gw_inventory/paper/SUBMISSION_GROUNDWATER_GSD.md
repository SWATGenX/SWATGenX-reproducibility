# Submission tracker — Groundwater for Sustainable Development (GSD)

Target: **Groundwater for Sustainable Development** (Elsevier). **Subscription route = free** (APC only if you
opt into Open Access — *decline OA at the licensing step*). Hybrid confirmed from the guide-for-authors PDF.
Submit via Elsevier **Editorial Manager** ("Submit your paper" on the journal page).

## Manuscript checklist — DONE (in `main.tex`, compiles clean ~28 pp)
- [x] Reframed for sustainability + **global transferability** (abstract, intro, "Transferability beyond the US" subsection, cover letter) — clears GSD's international-relevance gate
- [x] Abstract ≤250 words (224), standalone, no refs
- [x] **Highlights** ×5, each ≤85 chars (in doc + `highlights.txt`)
- [x] **Graphical abstract** (`figures/graphical_abstract.{pdf,tiff}`, Elsevier aspect ratio)
- [x] Keywords (7)
- [x] **CRediT** · **Competing interests** (discloses SWATGenX/explorer) · **Funding** (none) ·
      **Declaration of generative-AI use** · **Data-availability statement** (frozen Zenodo + method code + secondary live-explorer)
- [x] Dataset citation in `references.bib` (`rafiei2026data`)
- [x] Metric conversion note (1 ft = 0.3048 m); line numbers; double spacing; tables as text; vector figures
- [x] Census reconciled (8 → 17 free machine-readable states; ~3.7M wells moved VLM→free)

## At-acceptance (user)
- [ ] Activate the **Zenodo DOI** (publish the unpublished draft, id 20837659) and fill it into the data-availability statement + `rafiei2026data`
- [ ] On the Wiley/Elsevier licensing step choose **subscription (CTA), not Open Access**
- [ ] Provide ORCID 0009-0009-8309-1895 (have it); optionally suggest reviewers

## Free-harvest completion (the "all free data" build) — running, checkpointed
Rate-limited by source servers, not us. All resume automatically.

| State | Source | ETA from 2026-06-25 03:00 | output |
|---|---|---|---|
| VT | structured grid | ~5 h | `VT/VT_lithology.parquet` |
| KY | KGS | ~few h | `KY/KY_lithology.parquet` |
| OK | HTML scrape | ~11 h | `OK/OK_lithology.parquet` |
| MA | born-digital text | ~24–33 h (hydraulics already done, 212k) | `MA/MA_lithology.parquet` |
| WI | born-digital triage | ~28 h | `WI/WI_digital_intervals.parquet` |
| NM | structured API (1.5/s) | ~44 h | `NM/NM_lithology.parquet` |

**On completion, rebuild (one shot):**
1. `python national_gw_inventory/package_release.py` → refreshes `_inventory/release_v1/gw_{lithology,hydraulics}_v1.parquet`
   (harvested wells grow ~3.0M → ~4.0M; +OK/WI/VT/NM/MA/KY)
2. `python national_gw_inventory/make_completeness_figure.py` (+ send)
3. Update the paper's harvested-count numbers (currently ~3M wells / 20M intervals → final).
4. Re-upload the refreshed parquets to the Zenodo draft (`python national_gw_inventory/zenodo_upload.py` updates the draft; do NOT `--publish` until acceptance).

## Fallbacks
If GSD desk-rejects on scope: **Hydrogeology Journal** (Springer, genuinely free hybrid) or **Groundwater** (NGWA — verify its non-OA author fee first).

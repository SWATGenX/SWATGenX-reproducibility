# Editorial Manager submission guide — Geodata and AI (Elsevier)

Walk the 8 "Submission tasks" in order. Copy-paste blocks below. (Abstract field allows up to 350 words;
ours is 248.)

---

## Task 1 — Article type  ✅
**Research article.**

## Task 2 — Upload submission files  ✅
Uploaded from the package: `manuscript.pdf`, `supplement.pdf`, `highlights.docx`, `cover_letter.docx`
(or .pdf), `graphical_abstract.tiff`, and the figure files `Fig1_spectrum` … `Fig6_hydraulic`.
(Optionally upload the editable source: `main.tex`, `references.bib`, `preamble-common.tex`, the figures.)

## Task 3 — Title, abstract, keywords  ← you are here

**Title** (already auto-filled, correct):
A national inventory of well lithology and hydraulics for the conterminous United States, with a vision-language method for reading scanned driller's logs

**Abstract** — paste this (plain text; if the Greek κ does not paste cleanly, replace "κ" with "kappa"):

> Sustainable groundwater management requires a three-dimensional picture of the subsurface, yet across much of the world that information exists only as water-well driller's logs in fragmented, partly-digitized government archives — a barrier most acute where agency-scale digitization is unaffordable. Using the United States as a demonstration, we (i) compile an availability census of the ~13.4 million wells in the 48 conterminous states, classifying each by how its lithology is published: a first-pass audit finds machine-readable lithology in 8 states (~3.2M wells), but systematic probing raises this to 17 states (~7.0M); 13 states (~4M) publish it only as scanned images, and 18 (~2.4M) publish no digital lithology (the wells are registered, the logs are not); (ii) from the machine-readable states we harmonize the ~3.4 million wells carrying a log into an open inventory of nearly 24 million depth-resolved intervals, plus structured hydraulics for ~2.8 million wells, all from public endpoints, no privileged access; and (iii) introduce a reproducible, cost-bounded method that recovers lithology from scanned logs using vision-language models. Validated against a state agency's hand-transcriptions, the method reproduces material class at 91.5% accuracy (Cohen's κ = 0.90) and the coarse/fine texture that groundwater models consume at 96.0% (κ = 0.92), at roughly 1,000 tokens per log. We report cost in tokens, a provider-independent unit, and quantify what each state does and does not expose. Because the method transfers to any jurisdiction with scanned well records, it offers a low-cost path to the subsurface data groundwater management needs; data and method are released openly.

**Keywords** — paste (semicolon-separated):

> groundwater; driller's logs; lithology; vision-language models; data harmonization; geo-database; hydrogeology

(7 keywords; meets the ≥3 minimum. "vision-language models" and "geo-database" align with the journal.)

## Task 4 — Author details
- Name: **Vahid Rafiei** — set as **corresponding author** (sole author).
- ORCID: **0009-0009-8309-1895**
- Affiliation: **Independent Researcher** (no institution); Country: **United States**.
- Email: **vahidr32@gmail.com**

## Task 5 — Open access decision  ⚠️ read this
Geodata and AI is **gold open access — there is NO subscription route**, so the article *will* be open
access. This is the OPPOSITE of the hybrid-journal advice (don't look for a "decline OA / subscription"
option — there isn't one). **The APC (US$2,100) is WAIVED for submissions received before 31 August 2026
that are accepted after review**, so you should owe **nothing**.
- Choose open access / accept the gold-OA terms; the waiver applies automatically to a pre-cutoff submission.
- **License choice:** CC-BY is the standard OA license. If you'd rather limit commercial reuse of the
  *article text*, pick **CC-BY-NC-ND**. (This is the article license only — it does NOT govern the dataset.
  Keep the *data* license decision separate on Zenodo; per our earlier discussion, license the frozen v1
  snapshot openly but keep the maintained dataset + pipeline proprietary.)

## Task 6 — Classifications
Pick the closest from the journal's list — aim for: groundwater / hydrogeology / subsurface; machine
learning or artificial intelligence / foundation or vision-language models; and geospatial data / databases.

## Task 7 — Additional information (declarations etc.)
All of these are already written in the manuscript (end matter) — re-enter in the form if asked:
- **Competing interests:** "The author develops and maintains SWATGenX, which hosts an optional interactive
  viewer of the inventory; no other competing interests."
- **Funding:** none ("This research did not receive any specific grant…").
- **Data availability:** frozen inventory + method code deposited on **Zenodo** with a citable DOI
  (activate it now and paste the real DOI — see below); interactive viewer at swatgenx.com is secondary.
- **Generative-AI declaration:** an LLM assisted writing/editing; the vision-language models are a *research
  method*, declared separately. (Note: gen-AI artwork is not used; the graphical abstract is matplotlib.)
- **CRediT:** Vahid Rafiei — all roles (sole author).
- **Suggested reviewers (optional):** add 3–4 names in groundwater data systems / AI document extraction if you have them.

## Task 8 — Review and submit
- Confirm files attached: manuscript, supplement, highlights, graphical abstract, cover letter (+ source if uploaded).
- **Before submitting: activate the Zenodo DOI**, then make sure the manuscript's Data-availability statement
  and the `rafiei2026data` reference carry the *real* DOI (the source currently has a placeholder
  `10.5281/zenodo.0000000`). If you can't re-upload the PDF, note the DOI in the cover-letter / comments field.
- Submit. (Submitting before 31 Aug 2026 secures the APC waiver.)

---
### One optional pre-flight (recommended)
A one-line email to the editors confirming groundwater driller's-log data is in scope (the journal's listed
scope skews geotechnical/mining). Not required to submit, but cheap insurance against a scope desk-reject.

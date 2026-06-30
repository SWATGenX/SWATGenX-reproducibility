# Water Research — submission compliance checklist

Tracked against the WR *Guide for Authors* (ISSN 0043-1354). Status: ✅ done · ⚠️ partial/verify · ⬜ TODO.

## Article type & length
- ✅ **Research Paper** (original research, in-depth evaluation) — correct type.
- ⚠️ **Total length ≤ 8000 words incl. references** — verify final word count (currently ~manuscript + 35pp PDF; tables/figures count toward presentation, not the word cap). Trim if over.
- ✅ Not multi-part; not a case study sold as one.

## Title page
- ⚠️ **Title** concise, avoid abbreviations — current title is long/descriptive; consider shortening.
- ✅ Author + affiliation (Vahid Rafiei, Independent Researcher, ORCID) — provide full postal address + email + corresponding-author flag at submission (in the EM system).

## Abstract / keywords / highlights / graphical abstract
- ✅ **Abstract ≤ 250 words** — cut from 545 → ~245; stands alone; no references; includes lineage + porewater.
- ✅ **Keywords** 1–7, English — present (SWAT+, MODFLOW 6, PFAS, …).
- ✅ **Highlights** 3–5 bullets, **each ≤ 85 chars** — rewritten, all 70–82 chars; submit as a separate file with "highlights" in the filename.
- ⬜ **Graphical abstract** (encouraged) — none yet; the coupling schematic (recharge↓ / baseflow+PFAS↑) would serve; 531×1328 px, TIFF/EPS/PDF.

## Structure
- ✅ Numbered sections (Intro, Methods, Results, Discussion, Conclusions) — LaTeX auto-numbers; abstract not numbered.
- ⚠️ Cross-reference by number (not "the text") — using \ref; verify no "see text" phrasing.
- ✅ Introduction states objectives; Methods reproducible; Discussion doesn't repeat results; standalone Conclusions.

## Declarations (mandatory)
- ✅ **CRediT authorship contribution statement** — added.
- ✅ **Declaration of competing interest** — present (none).
- ✅ **Funding** — present (no specific grant).
- ✅ **Declaration of generative AI use** — added (new section before references, per the required template).
- ✅ Acknowledgements — separate section before references.

## Figures / tables / maps
- ✅ Tables use booktabs (no vertical rules / shading) — WR-compliant; captions present; notes below.
- ⚠️ Figures: cite all in text ✅; **supply as separate files at submission**, ≥300 dpi (photos) / vector for line art; logical names (Figure_1…). One PNG figure (`rogue_pfas_validation.png`) — confirm ≥300 dpi.
- ✅ **Jurisdictional map note** added to the study-area figure caption ("Map lines delineate study areas…").
- ⬜ Add a porewater + load/mass-balance figure (new results currently text-only).

## References
- ⚠️ **Style**: WR final style is numbered [n] in order of appearance; current is author-year (apalike). Acceptable at submission ("any consistent style"), **converted at proof**. Keep consistent.
- ✅ **SWATGenX cited** — added `Rafiei2026SWATGenX` (C&G, submitted) and cited in Introduction + Availability (answers "cite the SWATGenX API/platform").
- ✅ Software cited (Zenodo archive) with DOI; ✅ MODFLOW 6 / PEST++ cited.
- ⚠️ Add [dataset] tags for the public PFAS inventories (EGLE/ECHO) in the reference list if listed as data references.

## Data / software / reproducibility (Option A — encouraged)
- ✅ **Zenodo archive** created (DRAFT, DOI 10.5281/zenodo.20838389, 47.5 MB) — models + code + flow field + scripts. **NOT yet published** (goes live on acceptance).
- ⚠️ **License** — Zenodo + repo LICENSE is a PLACEHOLDER; **choose a license before publishing** (e.g., MIT for code / CC-BY-4.0 for data).
- ✅ Development repo cited: github.com/rafiei-vahid/swatplus (engine + coupling).
- ✅ SWATGenX framed as model-generation source, not a platform pitch.

## Submission files (Editorial Manager)
- ⬜ Cover letter (note: no pre-submission inquiry; WR doesn't do them).
- ⬜ Highlights as separate editable file.
- ⬜ Declaration of competing interest as .doc/.docx (declarations tool output).
- ⬜ Graphical abstract file (optional).
- ✅ Manuscript source = .tex (editable) — WR accepts LaTeX.
- ⚠️ Remove `\linenumbers` from main.tex (WR adds line numbers automatically) — optional.

## Outstanding science items (not GfA, but for a strong submission)
- ⬜ DISV refinement result (stages 2–5) → close the high-conc discharge under-prediction.
- ⬜ Formal uncertainty analysis (Sobol) → model-confidence statement.
- ⬜ Full SW+GW mass-balance closure % (needs surface-engine load).

---
## Phase 4 packaging status (2026-06-26)

✅ **License** — MIT (code) + CC-BY-4.0 (data) applied to `reproducibility/LICENSE`.
✅ **Cover letter** — `cover_letter.pdf` (+ .tex).
✅ **Highlights** — separate file `highlights.txt`.
✅ **Competing interest** — separate file `declaration_competing_interest.txt`.
✅ **[dataset] tags** — USGS NWIS, NHDPlus HR, EPA ECHO, Michigan EGLE added to
   `references.bib` and cited in the availability section.
✅ **Sobol** — variance-based surrogate Sobol done (results + discussion).
✅ **Vadose travel-time** — done (discussion); explicit UZF/UZT noted as future work.
✅ **Conceptual model** — Figure 1 (Methods).
✅ **OAT hydraulic sensitivity** — SI subsection si:oat + figure.
☑️ **Word count** — ~8,360-word body; author elected to leave as-is (WR soft target).
⬜ **Deferred (future work, framed as such in Discussion):** DISV grid refinement,
   full SW+GW mass-balance closure %, explicit UZF/UZT vadose model.
🔜 **At submission:** separate figure files ≥300 dpi; numbered-reference style is a
   proof-stage conversion; Zenodo record published on acceptance.

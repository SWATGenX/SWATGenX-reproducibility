# SWATGenX manuscript (scaffold)

Primary journal: **JAWRA** (*Journal of the American Water Resources Association*, Wiley)—SWAT+ was introduced there (Bieger et al., 2017).

Backup: **ASCE** *Journal of Water Resources Planning and Management*.

Fast / open-access fallback: **Water** (MDPI)—use if timeline or OA requirements dominate cost.

## Contents

| Path | Purpose |
|------|---------|
| [journal-notes.md](journal-notes.md) | Frozen Wiley/JAWRA submission notes (fill when verified). |
| [evidence-matrix.md](evidence-matrix.md) | Claim → evidence (figure, table, repo path, citation). |
| [manuscript/main.tex](manuscript/main.tex) | Main manuscript (`article` + lineno + doublespace). |
| [manuscript/supplement.tex](manuscript/supplement.tex) | Standalone supplementary PDF (manifest, extended runtime tables, cal/val figures). |
| [manuscript/sections/](manuscript/sections/) | Section bodies (`\input` from `main.tex` or `supplement.tex`). |
| [bib/references.bib](bib/references.bib) | BibTeX database. |
| [figures/](figures/) | Figure PDFs/PNGs (add assets here). |
| [tables/](tables/) | Table sources or exported TeX snippets. |
| [analysis/evaluation-protocol.md](analysis/evaluation-protocol.md) | Pre-specified basins, metrics, periods (no results prose yet). |
| [analysis/cal-val-sensitivity-basin-02297600.md](analysis/cal-val-sensitivity-basin-02297600.md) | **Objective 4** — controlled cal/val/sensitivity basin. |
| [analysis/runtime-benchmark-objective.md](analysis/runtime-benchmark-objective.md) | **Objective 5** — SWAT+ simulation runtime benchmark (public page). |
| [supplement/](supplement/) | Supplementary artifact lifecycle table (inputs, caches, generated products, qualitative storage/compute classes). |
| [source-bank/](source-bank/) | Controlled reuse of legacy docs: [source-bank/document-inventory.md](source-bank/document-inventory.md), extraction notes, [rejected-or-stale-claims.md](source-bank/rejected-or-stale-claims.md). |
| [submission/cover-letter.md](submission/cover-letter.md) | Cover letter template. |

## Thesis (manuscript spine)

SWATGenX reduces the **reproducibility and scalability bottleneck** in SWAT+ preparation by automating **high-resolution** watershed model generation from **U.S. national datasets**, with **NHDPlus HR** as the hydrographic backbone—framed as **water-resources modeling infrastructure**, not a web-app paper.

## Compile (local)

From repository root:

```bash
bash publication/manuscript/build_pdfs.sh
```

Or manually from `publication/manuscript/`:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
pdflatex supplement && pdflatex supplement
pdflatex main && pdflatex supplement
```

Outputs: **`main.pdf`** (manuscript) and **`supplement.pdf`** (supplementary material).
Cross-references between the two use the `xr` package (`\externaldocument`).

Adjust `\bibliographystyle{...}` if JAWRA author notes require a different style.

## Repo sources (drafting later)

Methods text: [documents/NHDPlus_HR_SWATPlus_Methods.md](../documents/NHDPlus_HR_SWATPlus_Methods.md). Platform overview: [web_application/frontend/src/pages/PlatformOverview.js](../web_application/frontend/src/pages/PlatformOverview.js). Architecture: [architecture.md](../architecture.md), [readme.md](../readme.md).

**Do not** paste illustrative bibliometric year tables from internal research memos into the manuscript unless replaced by a reproducible query bundle under `publication/bibliometrics/` (not part of this scaffold).

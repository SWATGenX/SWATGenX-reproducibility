# Publication supplement — artifact lifecycle

This folder holds **supplementary** materials that document how major SWATGenX **inputs**, **intermediate artifacts**, **generated products**, and **pipeline steps where retention and provenance matter** are handled in the workflow. It is intended for a **data / reproducibility supplement** (or internal reviewer appendix), **not** as a substitute for Methods prose or the Data Availability statement in the manuscript.

## Contents

| File | Purpose |
|------|---------|
| [`tab-artifact-lifecycle.csv`](tab-artifact-lifecycle.csv) | Canonical, machine-readable table (one row per artifact or component class). |
| [`artifact-lifecycle-table.md`](artifact-lifecycle-table.md) | Human-readable mirror of the same rows with short narrative context. |
| [`tab-repro-file-manifest.csv`](tab-repro-file-manifest.csv) | File-level reproducibility manifest for Supplementary Table S1 (tables, scripts, figures). |

## How to use

- **Authors:** Update the CSV when the pipeline, data contracts, or archival policy change; keep `status` honest (`verified` / `partial` / `needs_audit`).
- **Manuscript:** Supplementary Table S1 is emitted from `tab-repro-file-manifest.csv` via `publication/analysis/scripts/emit_tab_repro_manifest_tex.py` and included in the manuscript appendix; the main text cites Supplementary Table S1 without listing individual repository paths.
- **Readers:** Treat `lifecycle`, `storage_implication`, and `cpu_ram_implication` as **qualitative design classes**, not measured benchmarks.

## Scope and non-claims

- **Tone** — workflow transparency, **artifact provenance**, and **storage-aware reproducibility**; not infrastructure marketing or optimization claims.
- **No universal performance claim** — elapsed time and working-set behavior depend on deployment, model extent, and how archives are stored and read.
- **No “fastest workflow” language** — entries describe **where data live** and **how they are produced or cached**, not competitive speed.
- **No secrets** — do not paste private host paths, credentials, tokens, or deployment-only configuration into these tables. Use repository-relative paths and public product names in `evidence_source`.
- **No invented byte sizes** — storage columns stay qualitative unless a separate measurement note exists.

## Related manuscript materials (read-only pointers)

- Data Availability draft: `publication/manuscript/sections/data-availability.tex`
- Data master contract: `publication/tables/tab-data-master.csv`, `publication/tables/table-specifications.md`
- NHDPlus HR methods narrative: `documents/NHDPlus_HR_SWATPlus_Methods.md`
- Locked evaluation examples: `publication/analysis/evaluation-protocol.md`, `publication/tables/tab-model-complexity.csv`

# Public release manifest

Defines what ships to the **public reproducibility mirror**
(`github.com/SWATGenX/SWATGenX-reproducibility`) versus what stays internal. The
source of truth is the private monorepo `rafiei-vahid/SWATGenX`; the public mirror is
a cleaned subset of `publication/`, published the same way as the API examples bundle
(`scripts/publish_public_swatgenx_api.sh` is the reference pattern).

## INCLUDE (ships public)

```
publication/manuscript/**            # .tex, build_pdfs.sh  (PDFs optional)
publication/manuscript/final         # symlink -> ../figures/final
publication/bib/references.bib
publication/tables/*.csv             # source tables
publication/tables/generated/*.tex   # committed LaTeX fragments
publication/figures/final/**         # publication figures (+ metadata json)
publication/figures/supplement/**
publication/figures/figure-specifications.md
publication/analysis/scripts/*.py    # emitters, renderers, exporters, shared libs
publication/analysis/scripts/*.sh
publication/analysis/scripts/README.md
publication/analysis/*.md            # evaluation-protocol, objective specs
publication/analysis/qa/             # FINAL audit outputs only (see EXCLUDE for scratch)
publication/supplement/**            # repro manifest, artifact lifecycle
publication/README.md
publication/REPRODUCIBILITY.md
publication/requirements.txt
publication/RELEASE_MANIFEST.md
publication/evidence-matrix.md
```

## EXCLUDE (internal only — never push public)

```
publication/analysis/_archive/**     # QA scratch + one-off ops scripts
publication/analysis/logs/**         # raw calibration/validation run logs (6.9M; untracked)
publication/analysis/runtime-runs/** # raw timing JSONL (mostly gitignored)
publication/figures/drafts/**        # draft figure iterations
publication/journal-notes.md         # submission portal URLs / APF notes
publication/manuscript/PRESUBMISSION_REVIEW.md  # internal self-review (kept private)
publication/submission/**            # cover letter drafts
publication/review/**                # internal TODO/audit snapshots
publication/source-bank/**           # legacy-document reuse triage
**/*.aux **/*.log **/*.bbl **/*.out  # LaTeX byproducts
```

## REDACT before publishing (path scrub)

A few committed data files embed the internal absolute path
`${SWATGENX_USER_PATH}/...` in non-essential cells (artifact-status columns,
figure-metadata JSON). The manuscript does not depend on these strings. At publish
time, scrub them to a placeholder, e.g.:

```bash
grep -rlI '${SWATGENX_USER_PATH}' <staged-public-tree> \
  | xargs sed -i 's#${SWATGENX_USER_PATH}[A-Za-z0-9_]*#${SWATGENX_USER_PATH}#g'
```

Scripts themselves are already parameterized via `SWATGENX_USER_PATH` /
`SWATGENX_EXAMPLE_USER` (see `analysis/scripts/_swatgenx_paths.py`).

## Heavy artifacts → SWATGenX website (not GitHub)

SWAT+ model packages (TxtInOut, shapefiles, project SQLite; 100 MB+ each) are not
stored in git. They are downloadable as project ZIPs from the SWATGenX example-models
portal <https://www.swatgenx.com/example-models> (per-model case-study pages for the
benchmark domains), which the Data Availability Statement cites as the model source.

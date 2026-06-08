# Reproducibility

This directory reproduces the tables, figures, and PDFs of the SWATGenX manuscript.
Three layers, in increasing data requirements:

| Layer | Needs | Reproduces |
|-------|-------|-----------|
| **A. Document build** | LaTeX + the committed `tables/generated/*.tex` and `figures/final/*.png` | `manuscript/main.pdf`, `supplement.pdf` |
| **B. Table/figure regeneration** | Python env (`requirements.txt`) + committed source data (`tables/*.csv`, frontend `*.json`) | the `tables/generated/*.tex` fragments and catalog-driven figures |
| **C. Full regeneration** | the SWAT+ model workspaces + national source datasets | the source CSVs/JSON themselves (drainage audit, metrics, runtime) |

Most readers only need **A** and **B**, which run entirely from committed data.

## 1. Environment

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r publication/requirements.txt        # Python 3.10
# Document build also needs: TeX Live (pdflatex, bibtex) and poppler-utils (optional, for PDF rasterization)
```

## 2. Configuration (layer C only)

Scripts that read the example model workspaces resolve their location from
environment variables (default = the internal deployment). Override to point at
your own `SWATplus_by_VPUID` tree:

```bash
export SWATGENX_USER_PATH=/path/to/Users     # parent of <user>/SWATplus_by_VPUID
export SWATGENX_EXAMPLE_USER=admin           # account holding the evaluation models
```

## 3. Build

```bash
# Layer B: regenerate all LaTeX table fragments from source CSV/JSON
bash publication/build_all.sh                # runs emit_tab_*.py then builds the PDFs

# Layer A only (PDFs from existing fragments/figures):
bash publication/manuscript/build_pdfs.sh    # -> main.pdf, supplement.pdf
```

## 4. Data sources (layer C)

- **National datasets** (obtain from the responsible agencies; see `tables/tab-data-master.csv`):
  NHDPlus HR, WBD, PRISM, NLCD, gSSURGO/SSURGO, NSRDB, USGS NWIS.
- **SWAT+ model packages** (the eight evaluation Model IDs in `tables/tab-model-roster.csv`).
  These executable project trees are large (100 MB+ each) and are **not** stored in this
  repo; download them from the SWATGenX example-models portal and unzip them into the
  workspace tree the layer-C scripts expect.

  **Get the model(s) from the SWATGenX website:**
  1. Open the example-models portal: <https://www.swatgenx.com/example-models>.
  2. Find the Model ID you need (filter/sort by state, HRUs, streams, or USGS gauges) and
     click **Download ZIP**. (Benchmark domains also have per-model case-study pages, e.g.
     Peace River HUC-8 at <https://www.swatgenx.com/swat-plus-modeling/florida/03100101>.)
  3. Unzip into your workspace tree at the path matching `workspace_model_id` in
     `tables/tab-model-roster.csv`:
     ```
     $SWATGENX_USER_PATH/$SWATGENX_EXAMPLE_USER/SWATplus_by_VPUID/<vpuid>/<level>/<name>/
     ```
     e.g. tier-S Oklawaha `0308/huc12/030801020804` unzips to
     `…/SWATplus_by_VPUID/0308/huc12/030801020804/`.
  4. Re-run the layer-C scripts (drainage audit, metrics, runtime); they resolve the model
     from `$SWATGENX_USER_PATH` (Section 2).

  **Evaluation Model IDs** (`catalog_model_id`): benchmarks `03080102` (S), `09471300` (M),
  `03100101` (L, HUC-8), and the simulation scaling ladder `03152000` (X20), `07174000`
  (X40), `15060105` (X60, HUC-8); plus the two controlled calibration/validation basins
  `02297600` (FL) and `05536265` (IL). Any model can also be regenerated from scratch with
  the SWATGenX platform.

## 5. Manifests

- `supplement/tab-repro-file-manifest.csv` — file-level reproducibility manifest (Supplementary Table S1).
- `RELEASE_MANIFEST.md` — what ships to the public reproducibility mirror vs stays internal.
- `analysis/evaluation-protocol.md` — frozen basins, metrics, and periods.

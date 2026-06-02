# Manuscript QA artifacts (internal)

Run NHD preprocessing impact benchmark for all official evaluation models:

```bash
python3 publication/analysis/scripts/run_nhd_preprocessing_qa_benchmark.py
```

Outputs:

- `publication/tables/tab-nhd-preprocessing-qa.csv` — frozen counters (manuscript source)
- `publication/analysis/qa/nhd-preprocessing-qa-benchmark.md` — human-readable summary

Emit LaTeX (S/M/L table for Results):

```bash
python3 publication/analysis/scripts/emit_tab_nhd_preprocessing_qa_tex.py
```

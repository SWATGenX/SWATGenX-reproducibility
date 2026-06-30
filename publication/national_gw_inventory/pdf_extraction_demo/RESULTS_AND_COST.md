# PDF lithology extraction — demo results, cost, and local-vs-API analysis

Feasibility demo for Phase-2 of the national groundwater inventory: extract the lithology log +
construction from scanned driller's-log PDFs. 10 real Oregon (OWRD) water-well reports, 9 counties.
Pipeline: `national_gw_inventory/pdf_extraction/extract_lithology_llm.py` (Gemini native PDF input,
forced JSON schema, measured token usage). PDFs + per-log JSON live beside this file for manual check.

## 1. Extraction quality (gemini-2.5-flash)

10/10 succeeded; all `legibility=clear`, self-confidence 0.9–1.0. Spot-checked against the scans:

- **Faithful transcription** incl. driller shorthand ("Sand f-m tan w/wood", "Gravel f-c w/sandy clay
  tan") and even misspellings preserved verbatim ("Plumice" = pumice).
- **No hallucination:** the one log with a blank materials column returned an **empty** lithology
  array (conf 1.0) rather than inventing intervals — the key trust signal.
- **Soft spot = normalization, not extraction:** mixed rows ("Clay & Gravel") fall to `other`. The
  verbatim `description` is correct, so it's recoverable by improving the controlled vocab — the
  extraction itself is sound.

## 2. Cost (measured token usage, USD)

| Model | per PDF | per 1k | per 1M | quality |
|---|---|---|---|---|
| **gemini-2.5-flash** | **$0.00091** | $0.91 | ~$906 | 10/10, high fidelity |
| **gemini-2.5-flash-lite** | **$0.00020** | $0.20 | ~$201 | 9/10 (1 = Google 503, not model); comparable content |

Transient `503`s appeared on flash-lite during testing (Google-side availability, now retried with
backoff). Flash was rock-solid. **Flash-lite is ~4.5× cheaper and looks good enough** — flash is the
safe fallback for low-legibility logs.

> ⚠️ Earlier a `requests` error leaked the API key via a `?key=` URL into a /tmp log — scrubbed, and
> the script now sends the key in the `x-goog-api-key` header so it can't recur.

## 3. The corpus splits two ways (measured on 60 OR logs)

| Type | Share (OR) | Path | Cost |
|---|---|---|---|
| Digital-native (embedded text layer) | **~13%** | `pdftotext` + parse, fully local | **free** |
| Raster scan (often handwritten) | **~87%** | needs a vision model (OCR fails on handwriting) | API or local VLM |

So a `pdftotext`-first pass skims off the free fraction; the **majority genuinely needs a VLM.**

## 4. National cost (PDF-only universe ≈ 8.6M wells; ~2.2M already have queryable lithology)

Apply per-PDF cost to the ~87% raster share (~7.5M) + free local parse for the ~13%:

| Model | raster-only (~7.5M) | note |
|---|---|---|
| flash-lite | **~$1.5k** (1-page) → ~$3–4k (multi-page) | recommended default |
| flash | **~$6.8k** → ~$10k | fallback for hard logs |

**Not $100** — that buys ~110k PDFs (one mid state). But low single-digit $k for a national lithology
layer is still the headline. The API is the *cheap* part; real costs are PDF fetch/storage at 8.6M
scale, low-confidence re-runs, and **human QA on the normalization vocab**.

## 5. Local model? (answering directly)

- **Not yet tried, and this server can't:** no GPU (10 CPU / 16 GB free), no VLM runtime. A 7B VLM on
  CPU is impractical at 8.6M scale; `tesseract` isn't even installed (and plain OCR fails on handwriting).
- **What local would take:** a (rented) GPU running an open VLM — Qwen2.5-VL (7B/72B), InternVL2.5,
  MiniCPM-V, or Llama-3.2-Vision. One pass ≈ a few hundred GPU-hours ≈ $250–950 rental + engineering.
- **Cost verdict:** local does **not** beat flash-lite on price (flash-lite ≈ $1.5–4k national is
  already trivial). Local wins on **data sovereignty** (no third-party upload), **unlimited re-runs**,
  and **paper reproducibility** (method not locked to a proprietary API).
- **Accuracy verdict (the real unknown):** open VLMs are competitive with Gemini-flash on *clean*
  documents, but the **handwritten older logs** are exactly where a frontier model likely still leads.
  That gap is what a benchmark must measure — head-to-head on the same scans vs manual ground truth.

**Recommendation:** hybrid — (1) `pdftotext` for the free ~13%; (2) Gemini **flash-lite** for the
raster ~87% (cheap, reliable, available now); (3) build a local-VLM benchmark to run on a rented GPU,
and adopt local only if it matches accuracy *and* sovereignty/re-run needs justify the engineering.

## Next steps
- Build the local-VLM benchmark harness (Qwen2.5-VL via vLLM) — ready to run on a GPU box.
- Measure the text-layer fraction across more states (sizes the free vs paid split nationally).
- Refine the lithology controlled vocab (fix the mixed-row → `other` cases) + a manual-QA sample protocol.

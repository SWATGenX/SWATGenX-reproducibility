# SWAT+ engine acceleration — manuscript scaffold

**Working title:** *Accelerating a very large SWAT+ model without changing the science:
a reproducible profiling-to-parallelization methodology.*

**Primary venue:** **Geoscientific Model Development (GMD)** — "development and technical
paper" type (reproducible model performance + open code). Backup: *Environmental Modelling
& Software (EMS)*. Fast/short option: *SoftwareX*.

This is a **separate, self-contained** paper from the in-review C&G/JAWRA model-generation
paper (which lives at the `publication/` top level). Nothing here touches that submission.

## Delineation from the C&G paper (avoid double-publishing)
The C&G paper's **Objective 5** already reports the **runtime benchmark** and the **output
I/O work** (NetCDF backend, filtered print). In *this* paper those are **prior work /
background**, cited, not re-claimed. The **novel core here** is:

1. A **systematic acceleration methodology**: profile (Intel VTune) → classify bottlenecks
   → fix by class → validate correctness rigorously → re-measure.
2. A **bottleneck taxonomy of SWAT+ at scale**, and the headline finding that the dominant
   cost is **overhead, not hydrology** (string name-matching, per-object whole-array
   zeroing, derived-type struct copies, and a serial routing critical path).
3. A **shared-memory OpenMP parallelization that respects the routing DAG** (level
   wavefront over `cmd_order`), with reentrancy via threadprivate "current-object" state.
4. A **correctness framework**: byte-parity vs the production binary + **thread-count
   invariance** (run-to-run identity across thread counts) as an automatable race detector.
5. The **architectural-limit result**: where SWAT+'s daily step is critical-path-bound, and
   that much of the cost is removable *without* parallelism.

## Validation model
**Peace River HUC-8 (03100101)** — 57,998 HRUs / 8,182 channels, built by SWATGenX at 500 m.
Toolchain: **ifx `-O3 -ipo`** (gfortran fails on large models). OpenMP via `-fiopenmp`.

## Contents
| Path | Purpose |
|------|---------|
| [outline.md](outline.md) | Section outline + abstract draft + benchmark evidence table. |
| analysis/ | Benchmark tables + VTune profiles (the real measured data). |
| manuscript/ | `main.tex` (drafted later). |
| figures/ , bib/ | Assets; reuse `../bib/references.bib` where possible. |

## Source data already in hand (the analysis backbone)
- `swatplus_perf/MULTICPU_MILESTONES.md` — running engineering log of every milestone.
- `swatplus_perf/benchmark-results/` — thread-scaling runs.
- VTune hotspots/source-line profiles (regenerable; commands in `analysis/`).
- Fork `rafiei-vahid/swatplus`, branch `exp/openmp-hru-20260616` — the full commit history
  is the reproducible record of each optimization.

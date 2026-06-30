# swatplus-engine-acceleration

Reproducibility package for:

> **Accelerating a Regional Hyper-Resolution SWAT+ Model Without Changing the Science:
> a Reproducible Profiling-to-Parallelization Methodology and a Routing-Aware Shared-Memory Wavefront**
> V. Rafiei (submitted to *Computers & Geosciences*).

This repository contains everything needed to reproduce the benchmarks in the paper: the
benchmark model, the build recipe for the optimized/parallel SWAT+ engine, the timing harness,
the measured results, and the figure-generation script.

**You do not need AWS.** The paper's timings were collected on dedicated AWS instances only to
get quiet, uncontended hardware, but the benchmark itself is hardware-agnostic — run
`bench_scaling.sh` on any machine and you get *that machine's* scaling curve. The provisioning
scripts we used are in [`aws/`](aws/) purely as a convenience; they are not part of the
reproduction path.

## What's here

| Path | What it is |
|------|------------|
| [`BUILD.md`](BUILD.md) | Exact engine fork + per-optimization commits + the `ifx` build recipe |
| [`peace-river-03100101-model.7z`](peace-river-03100101-model.7z) | The benchmark model (Peace River, HUC-8 03100101; 57,998 HRUs / 8,181 channels). Unpack with `7z x`. |
| `bench_scaling.sh` | Cross-hardware scaling sweep: stock + final engine, `N = 1…24` threads, best of two |
| `bench_full.sh` | Full study: serial ladder + text/NetCDF I/O + thread-count byte-identity sweep |
| `make_figures.py` | Regenerates the paper figures from `results/*.csv` into `figures/` |
| `results/*.csv` | The measured wall times behind the paper's tables and figures |
| `aws/` | *Optional.* The scripts we used to provision dedicated cloud instances |

## The engine (built from commits, not shipped as a binary)

Every optimization is a single commit in the engine fork, so the cumulative ladder is auditable
commit by commit. See [`BUILD.md`](BUILD.md). The benchmark binaries are **not** committed here —
they are reproducible from those commits with `ifx`, and binaries are compiler/CPU-specific.

## Quick start

```bash
# 1. unpack the model
7z x peace-river-03100101-model.7z

# 2. build the engine binaries (see BUILD.md) and place them in ./bins/:
#    r0_<commit>  (stock)   r6_<commit>  (final serial)   r6clean (final, OpenMP)

# 3. run the scaling sweep on YOUR machine
bash bench_scaling.sh            # writes results.csv

# 4. regenerate the figures
python3 make_figures.py          # writes figures/Figure_*.png
```

## A note on the numbers

Absolute wall times and speedups are **hardware-specific** — they depend on CPU
microarchitecture, core count, memory bandwidth, and compiler version. The paper reports three
dedicated-instance microarchitectures (AMD EPYC "Turin", Intel Xeon "Granite Rapids", AMD EPYC
"Rome"); your machine will differ. The *shape* of the result — a wide, abundantly parallel land
phase followed by a memory-bound, serially-bounded routing tail — is the portable finding.

## License

The benchmark harness and scripts here are released under the MIT License. The SWAT+ engine
itself is governed by the upstream `swat-model/swatplus` license.

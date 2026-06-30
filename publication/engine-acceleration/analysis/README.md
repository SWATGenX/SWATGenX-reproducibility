# Analysis backbone — engine acceleration

Real measured data + how to regenerate it. Nothing here is hand-typed results.

## Sources (in the repo)
- `swatplus_perf/MULTICPU_MILESTONES.md` — chronological engineering log of every
  optimization + result (the narrative spine).
- `swatplus_perf/benchmark-results/omp-threads-*` — thread-scaling runs (wall time per N).
- Fork `rafiei-vahid/swatplus` @ `exp/openmp-hru-20260616` — commit history = reproducible
  record (each optimization is one commit with its validation in the message).

## How to regenerate
- Scaling: `swatplus_perf/scripts/bench_omp_threads.sh` (env BENCH_THREADS / BENCH_YEARS).
  For publication curves use a dedicated many-core box + best-of-N (the shared 10-core
  production box is contention-limited above ~4 threads).
- VTune profile (per-routine + source-line): build with `-O3 -ipo -g`, then
  `vtune -collect hotspots -r <out> -- ./swatplus`; report with
  `vtune -report hotspots -r <out> -group-by source-line`.
- Correctness: `scripts/parity_openmp_vs_prod.sh` (byte-parity vs production binary) and
  thread-count invariance (run N=4 twice + N=1-vs-N=4, byte-diff sorted output).

## Model
Peace River HUC-8 (03100101): 57,998 HRUs / 8,182 channels, 500 m, ifx -O3 -ipo.

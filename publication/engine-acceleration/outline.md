# Outline + abstract draft — SWAT+ engine acceleration

> Status: scaffold. Numbers below are measured but **preliminary** — the shared 10-core
> production box (which also runs the live site) is contention-limited at high thread
> counts. Final scaling curves to be measured on a **dedicated many-core box** (AWS, up to
> ~60 threads), best-of-N timing. All optimizations are validated **output-identical**
> (byte-parity) or **model-equivalent** (documented).

## Abstract (draft)
Process-based watershed models such as SWAT+ are increasingly run at continental, hyper-
resolution scale, where a single simulation of a large basin becomes the practical
bottleneck. We present a reproducible methodology for accelerating the SWAT+ engine on a
large basin (Peace River, 57,998 HRUs / 8,182 channels) **without altering model results**.
Intel VTune profiling shows that the dominant costs at scale are **overhead, not hydrology**:
O(N²) string name-matching at startup, per-object whole-array re-zeroing, derived-type
struct copies, and a serial routing critical path. We remove these by class — algorithmic
fixes (contributed upstream), output filtering and a NetCDF backend [prior work], and a
shared-memory OpenMP parallelization that respects the routing directed-acyclic graph
(a level wavefront over `cmd_order`, made reentrant by privatizing the engine's
"current-object" state). Correctness is enforced by **thread-count invariance** — repeated
runs across thread counts must be bit-identical — which doubles as an automatable data-race
detector. [Result sentence: cumulative speedup X×; parallel speedup Y× bounded by the serial
main-stem critical path.] We characterize where SWAT+'s daily step is parallelizable and
where it is architecturally serial, and release all code and benchmarks.

## Section outline
1. **Introduction** — hyper-resolution SWAT+; the single-run wall; why "speed without
   changing the science"; contributions.
2. **Background / prior optimizations** (cite C&G paper) — NetCDF output, filtered print,
   the two output-identical startup/reset fixes (upstream PRs #219 hru_read O(1), #220
   varinit per-row reset). Framed as context, not re-claimed.
3. **Methodology** — the loop: profile (VTune) → classify → fix → validate → re-measure.
   Validation framework: byte-parity vs production; thread-count invariance as race detector.
4. **Bottleneck taxonomy** — "overhead, not science": measured CPU split; the hotspot list.
5. **Parallelization** — routing DAG → `cmd_order` levels → OpenMP wavefront; reentrancy via
   threadprivate current-object state; the SAVE-locals Fortran hazard; one parallel region
   per day; the 1-thread = original-order = byte-identical guarantee.
6. **Targeted hotspot removal** — e.g. `ch_temp` LSU re-zeroing (O(N_lsu·N_channels) →
   O(ru_count·N_channels)); redundant struct copies. Each is a methodology data point.
7. **Results** — scaling curves (dedicated box); cumulative vs incremental speedup;
   correctness evidence; the critical-path ceiling and its cause.
8. **Discussion / limits** — Amdahl on an irregular routing network; what is and isn't
   parallelizable in SWAT+; portability; reproducibility.
9. **Conclusions.**

## Measured evidence (preliminary, Peace River, ifx -O3 -ipo, shared 10-core box)
| Stage | N=1 | N=2 | N=4 | N=8 | Notes |
|-------|----:|----:|----:|----:|-------|
| Full-DAG wave, per-level fork | 669.9 | 577 (1.16×) | 484 (1.38×) | 578 (1.16×) | regressed at 8 (fork overhead) |
| + single parallel region/day | 630.4 | 541.6 (1.16×) | 461.9 (1.36×) | 401.6 (1.57×) | best-of-3; regression gone |
| + ch_temp LSU-zeroing fix | 554.9 | 343.7 (1.61×) | **226.1 (2.45×)** | 391.5† | single runs; †N=8 contention-limited |

† N=8 on this box oversubscribes 10 cores under live-site load; single-run, not best-of-3.
Re-measure on a dedicated box for the publication curve.

**Headline so far:** removing one redundant per-channel array reset (`ch_temp`, the single
hottest line in the engine at ~731 s / ~97% of the routine) **halved the 4-thread wall
(462→226 s) and lifted 4-thread scaling from 1.36× to 2.45×** — because the cut was on the
serial critical path, shrinking the serial fraction. Output byte-identical.

## VTune bottleneck snapshot (8 threads, 180-day window)
- CPU split: ~73% effective, ~25% spin (idle at barriers), ~2% overhead.
- Dominant routine pre-fix: `ch_temp` ~750 s (mostly one full-array reset line) ≫
  `hru_control` ~29 s. Channel routing is the serial main stem.
- Earlier (`-ipo` lump): the channel phase was ~7× the HRU land phase.

## To do before drafting prose
- [ ] Clean best-of-N scaling on a dedicated many-core box (AWS), threads 1..32/60.
- [ ] Continue hotspot removal (next after ch_temp); re-profile each time.
- [ ] Quantify cumulative speedup vs stock upstream (end-to-end, incl. prior I/O work).
- [ ] Long-period model-equivalence check (the ~0.5% channel-constituent residual).
- [ ] Figure set: scaling curve, VTune before/after, the cmd_order level histogram (265).

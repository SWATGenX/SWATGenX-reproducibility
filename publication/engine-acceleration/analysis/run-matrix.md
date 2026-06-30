# Benchmark run matrix — cumulative optimization ladder

**Goal.** A single, internally consistent ladder on **one model, one box, one protocol**, so the
final engine can be compared to the stock engine with each optimization *class* isolated.
Every rung is measured **on this 57,998-HRU (500 m) Peace model** — including NetCDF and the
print filter, whose C&G numbers were on the 94k-HRU (250 m) model and do **not** transfer.

**Model.** Peace River HUC-8 03100101, 57,998 HRUs / 8,182 channels, 1 simulated year.
**Toolchain.** ifx `-O3 -ipo`; OpenMP `-fiopenmp`. **Box.** one dedicated AWS instance
(c8a.8xlarge, AMD Turin, 32 physical cores — the cross-hardware scaling champion), thread-pinned
(`OMP_PROC_BIND=close OMP_PLACES=cores`). **Repetitions.** best-of-3, least-contended.
**Deliverable held constant.** time to produce the calibration-relevant output (channel_sd daily).

## Rung → commit map (fork `rafiei-vahid/swatplus`)

| Rung | Label | Group | Commit | Binary status |
|-----:|-------|-------|--------|---------------|
| R0 | Stock engine (upstream, default print) | baseline | `934549c` | **build** |
| R1 | + NetCDF backend (`cdfout=y`) | I/O *(technique: C&G)* | `a117136` (+`768f1d1` ifx-link fix) | **build** |
| R2 | + channel_sd print filter | I/O *(technique: C&G)* | `a6b1a2a` | **build** |
| R3 | + hru_read O(1) name index | serial / startup | `87abf8e` | **build** |
| R4 | + varinit per-row reset (kill O(N²)/day memset) | serial / per-step | `247e95b` | have (`g247e95b`) |
| R5a | OpenMP machinery present, pre-channel-fix | (control, N=1) | `0d6e5f6` | have (`g0d6e5f6`) |
| R5b | + drop redundant inflow struct copy | serial / channel | `91922e3` | have (`g91922e3`) |
| R5c | + ch_temp LSU-zeroing scope fix | serial / channel | `6d41300` | have (`g6d41300`) |
| R6 | + narrow-level fusion (final engine) | parallel | `22e17a3` / `34f5c02` | have (`g22e17a3`,`g34f5c02`) |

**Why R5a is a control.** R4→R5a adds the reentrancy refactor + wavefront machinery but no
new serial math; at **N=1** it should be time-neutral vs R4 (validates the "1-thread = original
path" claim). R5b/R5c then isolate the channel serial fixes **at N=1**, separating their serial
benefit from their parallel benefit.

## Build list (4 binaries to add)
`934549c`, `a117136`, `a6b1a2a`, `87abf8e`. **Risk:** the ifx/NetCDF link fix (`768f1d1`) and
build-shadowing fixes post-date the stock/NetCDF/filter commits, so those may not build cleanly
with the current toolchain. Mitigation: cherry-pick only the *build* fix onto each old commit
for compilation (no behavior change), or build in a worktree and document any backport. Build in
a git **worktree** so the shared checkout/branch is untouched (multi-agent git safety).

## Timing matrix

| Rung | N=1 | N=2 | N=4 | N=8 | N=16 |
|------|:---:|:---:|:---:|:---:|:----:|
| R0 stock | ✓×3 | — | — | — | — |
| R1 +NetCDF | ✓×3 | — | — | — | — |
| R2 +filter | ✓×3 | — | — | — | — |
| R3 +hru_read | ✓×3 | — | — | — | — |
| R4 +varinit | ✓×3 | — | — | — | — |
| R5a control | ✓×3 | — | — | — | — |
| R5b +struct | ✓×3 | — | — | — | — |
| R5c +ch_temp | ✓×3 | — | — | — | — |
| R6 final | ✓×3 | ✓×3 | ✓×3 | ✓×3 | ✓×3 |

- **N=1 column = the serial ladder** (the "free win for every user" story; Group A + I/O).
- **R6 row across N = the parallel scaling** (Group B).
- Cross-hardware curves (c8a/c8i/c5a) already measured for R6 — reuse as the portability figure.

## VTune capture points (hotspots, 180-day window)
1. **R0 stock @ N=1** — shows channel routing + the to-be-removed overhead dominating.
2. **R6 final @ N=1** — shows the serial hotspots gone (ch_temp collapsed), pre-parallel.
3. **R6 final @ N=8** — shows the bottleneck migrated to barrier spin / serial main stem.
Triptych figure = the bottleneck *migrating* across the campaign.

## Outputs
- `analysis/ladder-times.csv` — rung, threads, rep, wall_s (raw), + best-of-3 summary.
- `analysis/vtune-{stock,final-n1,final-n8}/` — hotspots exports.
- Headline numbers for the paper: (i) cumulative serial factor R0→R6@N=1; (ii) parallel factor
  R6@N=1→R6@N=8; (iii) total R0→R6@N=8.

## Protocol notes
- Same `file.cio`, same weather window, same `print.prt` deliverable (channel_sd daily) for R3+;
  R0/R1 use stock default print (the honest "what users run today" baseline), R2 introduces the
  filter — so R1→R2 is the isolated print-filter contribution.
- Pin clock behavior: report CPU model + base clock from `/proc/cpuinfo`; note turbo for ratios.
- One box, sequential runs, nothing else on it (no contention).

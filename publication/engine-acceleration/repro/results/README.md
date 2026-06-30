# Measured results

Wall-clock times (seconds) behind the paper's tables and figures. Each row is one timed run;
take the best of the repeated `rep` values per `(rung, threads)` as the engine does no useful
work between reps. All runs: one simulated year, daily `channel_sd` output, thread-pinned.

| File | Machine | Contents |
|------|---------|----------|
| `crosshw_c8a.csv` | AWS c8a.8xlarge — AMD EPYC "Turin", 32 vCPU | Stock `R0` + final serial `R6` anchors + full-wavefront `R6FULL` at `N = 1…24` |
| `crosshw_c8i.csv` | AWS c8i.8xlarge — Intel Xeon "Granite Rapids", 32 vCPU | same protocol |
| `crosshw_c5a.csv` | AWS c5a.8xlarge — AMD EPYC "Rome", 32 vCPU | same protocol |
| `c8a_ladder_io_byteid.csv` | AWS c8a | Serial ladder (R0→R6), text-vs-NetCDF I/O, and the full-vs-byte-identical (routing-serial) scaling sub-study |

Columns: `rung,threads,rep,wall_s`. Rung names: `R0` stock; `R3…R5c` serial-optimization rungs;
`R6` final serial; `R6FULL` final OpenMP (full wavefront); `R6SER` final OpenMP with
`SWATPLUS_ROUTING_SERIAL=1` (byte-identical).

# Building the engine binaries

The optimized/parallel SWAT+ engine is maintained as a fork of `swat-model/swatplus`, with each
optimization isolated as a single commit so the cumulative ladder in the paper is auditable. The
benchmark binaries are rebuilt from these commits rather than shipped, because they are specific
to the compiler and CPU.

## Engine fork

```
https://github.com/rafiei-vahid/swatplus
```

## The cumulative ladder (commit per optimization)

| Rung | Commit  | Optimization (class) |
|------|---------|----------------------|
| R0   | `768f1d1` | Stock engine baseline (with the NetCDF/print-filter I/O backend available) |
| R3   | `87abf8e` | `hru_read` O(1) name index — startup (serial) |
| R4   | `247e95b` | `varinit` per-row reset — per-step (serial) |
| R5b  | `91922e3` | Drop redundant inflow-hydrograph struct copy — channel (serial) |
| R5c  | `6d41300` | `ch_temp` reset scope — channel (serial) |
| R6   | `34f5c02` | Narrow-level fusion (final). Build **serial** for the ladder, **OpenMP** for scaling. |

## Toolchain

The engine builds with the Intel oneAPI Fortran compiler (`ifx`). `gfortran` fails to produce a
working binary at this model size, so `ifx` is the reference toolchain.

```bash
# serial / ladder binaries:
ifx -O3 -ipo -recursive -init=zero -init=arrays -free -fpe0  ...

# OpenMP (final parallel engine, "r6clean"):
ifx -O3 -ipo -recursive -init=zero -init=arrays -free -fpe0 -fiopenmp  ...   # -DSWATPLUS_OPENMP=ON
```

The repository's CMake build is the supported path. Two build gotchas that cost real time:

- **Pin the compiler and NetCDF explicitly** on a fresh CMake configure:
  `-DCMAKE_Fortran_COMPILER=ifx` **and** `PKG_CONFIG_PATH=<deps>/netcdf-ifx/lib/pkgconfig`.
  Otherwise CMake picks up `gfortran`/system NetCDF and the `.mod` files clash.
- Source the Intel `setvars.sh` **without** `set -u`.

## The two engine modes

`r6clean` is one binary with two runtime modes, selected by an environment variable:

- **Full wavefront** (default): land phase *and* routing run in parallel. Bit-exact for flow,
  sediment, and dissolved species; the in-stream particulate constituents carry a compiler-induced
  ordering sensitivity at `N>1` (see the paper, §Correctness).
- **Byte-identical** (`SWATPLUS_ROUTING_SERIAL=1`): land phase parallel, routing serial.
  Thread-count-invariant for all constituents, at a measured cost in parallel speedup.

```bash
OMP_NUM_THREADS=8 ./bins/r6clean                          # full wavefront
OMP_NUM_THREADS=8 SWATPLUS_ROUTING_SERIAL=1 ./bins/r6clean # byte-identical
```

## Runtime libraries

The `ifx` binaries link the Intel runtime (`libiomp5`, `libimf`, …) and NetCDF
(`libnetcdf.so.19`, `libnetcdff.so.7`, `libhdf5`). On a stock Ubuntu host:

```bash
sudo apt-get install -y libnetcdf19 libhdf5-103 libcurl4
```

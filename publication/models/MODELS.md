# Evaluation SWAT+ model bundles (paper 1)

The eight evaluation SWAT+ models analysed in the manuscript are distributed as
**input-only ZIP bundles attached to the GitHub Release [`models-v1.0`]**, so this
repository is permanently independent of the SWATGenX web server (whose hosted
example-model versions evolve over time). Each bundle is the SWAT+ project
(`SWAT_MODEL_Web_Application/`, the `TxtInOut` inputs + `Watershed/Shapes`) with the
regenerable simulation outputs (`.nc`, `*_day/_mon/_yr/_aa.txt`, `*.out` diagnostics)
stripped — sufficient to run the model and to verify every reported structural metric.

Download all eight: `bash fetch_models.sh` (see also `MANIFEST.csv`).

## Provenance note (Peace River HUC-8)

The reported Peace River model is the **94,303-HRU, 30 m** version (tier L). The version
currently served by the live portal has since been regenerated at coarser resolution
(fewer HRUs); the bundle here is the exact reported build, frozen from the original
project, so the repository reproduces the manuscript rather than the evolving live model.

## Verification — reported vs. bundled

Structural metrics are reported for the three showcase tiers (S/M/L) and match the
bundles exactly. The scaling-ladder (X20/X40/X60) and calibration basins are documented
here for completeness.

| Tier | Model | HUC/Gauge | HRUs (reported) | HRUs (bundle) | Channels (bundle) |
|------|-------|-----------|-----------------|---------------|-------------------|
| S    | Oklawaha (FL)        | 030801020804 | 473    | 473    | 45    |
| M    | Upper San Pedro (AZ) | 09471300     | 11,284 | 11,284 | 1,371 |
| L    | Peace River HUC-8 (FL) | 03100101   | 94,303 | 94,303 | 8,181 |
| X20  | Little Kanawaha (WV) | 03152000     | —      | 19,530 | 1,615 |
| X40  | Verdigris River (KS) | 07174000     | —      | 36,833 | 2,329 |
| X60  | Upper Gila HUC-8 (AZ) | 15060105    | —      | 51,685 | 17,296 |
| cal  | Florida controlled basin  | 02297600 | —    | 778    | 37    |
| cal  | Illinois controlled basin | 05536265 | —    | 1,573  | 206   |

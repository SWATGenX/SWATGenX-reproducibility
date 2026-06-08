# Peace HUC8 (03100101) — threshold-TauDEM buildability (negative result)

NHDPlus-HR conditioning builds the Peace River HUC8 cleanly and runs (production
`SWAT_MODEL_Web_Application`, 347 NHD waterbodies wired as lakes). Threshold-based TauDEM
via QSWAT+ did **not** yield a runnable Peace model across the settings exercised:

| Delineation setting | Lakes | Subbasins (approx) | Outcome |
|---|---|---|---|
| Fine: stream 1250 / 2500 / 5000, channel 250 / 500 / 1000 (`splitChannelsByLakes`, clip) | yes | hundreds | **Hang** — QSWAT+ lake-topology merge ran >8 h (8.8 h observed) without producing HRUs |
| Coarse auto: stream ≈106,347 / channel ≈10,635 (one subbasin per HUC12) | yes | ~63 | **Segfault (exit 139)** in QSWAT+ lake-topology integration (`QSWATTopology._LAKEOUT`); SWATGenX auto-retried with lakes skipped |
| Coarse: stream 30,000 / channel 3,000, no lakes | no | ~220 | Delineation OK; QSWAT+ ran **76 min then segfault (exit 139)** during HRU construction — `HRU2 shapefile does not exist` → `RuntimeError: SWATGenX failed for huc8 03100101` |

**Reading:** the coarse threshold *does* remove the fine-threshold lake-merge stall (the build
reaches delineation/HRU for the first time), but QSWAT+ still cannot complete the Peace HUC8 —
segfaulting at lake-topology (with lakes) or HRU construction (without). So the difference between
the two delineations on a large, lake-dense basin is not merely fewer calibration-usable gages: the
threshold alternative did not converge on a buildable model at all, whereas the NHDPlus-HR
conditioned network — surveyed, lake-aware topology supplied to QSWAT+ rather than reconstructed
from flow accumulation — builds and runs unattended.

**Provenance:** failure tracebacks in `web_application/logs/celery-worker-error.log` (search
`03100101`). Build ordered via `/api/model-settings-huc8` (admin), `qswat_force_taudem_only=true`,
custom `model_name`. Failed experiment dirs cleaned up; production NHDPlus model + `SWAT_MODEL_NHD_timed`
(build-timing) retained. Documented in `sections/methods-delineation-comparison.tex`
(§ Station selection and the watershed-scale comparison).

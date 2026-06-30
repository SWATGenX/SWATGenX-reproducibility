#!/usr/bin/env bash
# Phase B — Oklawaha S TauDEM variant matrix (selective burn / lake filter / DEM resolution).
# Reference: NHDPlus-HR build SWAT_MODEL_Web_Application (3 subs / 53 LSU / 45 rivs, basin 53.37 km^2).
# Coarse proven threshold s15000/c500 @30m; rescaled to drainage-area-equivalent at 250m
# via --threshold-basis-res 30 (s15000 -> ~216 cells, c500 -> ~7 cells).
#
# Run as the normal user (each build self-elevates to www-data via the allowlisted
# passwordless sudo on the .venv python), sequentially (clean per-build wall-clock):
#   bash publication/analysis/scripts/run_taudem_phaseb_oklawaha.sh
#
# Each build writes build_timing.json in its model dir; the collector reads metrics after.
set -u

PY="sudo -n -u www-data /data/SWATGenXApp/codes/.venv/bin/python"
RUN=/data/SWATGenXApp/codes/publication/analysis/scripts/run_taudem_variant_model.py
MODEL_ID=0308/huc12_outlet/030801020804
QA=/data/SWATGenXApp/codes/publication/analysis/qa
COMMON="--model-id $MODEL_ID --delineation taudem --snap 900 --ls-resolution 250 --force-rebuild"
# Per-build wall-clock guard: Oklawaha coarse builds run ~3 min; 20 min is a generous ceiling.
GUARD="timeout -s KILL 1200"

run_variant () {
  local name="$1"; shift
  local log="$QA/phaseb_${name}.log"
  echo "=== [$(date +%H:%M:%S)] building $name ===" | tee -a "$QA/phaseb_oklawaha_driver.log"
  $GUARD $PY "$RUN" $COMMON --model-name "SWAT_MODEL_$name" "$@" > "$log" 2>&1
  local rc=$?
  echo "    [$(date +%H:%M:%S)] $name exit=$rc (log: $log)" | tee -a "$QA/phaseb_oklawaha_driver.log"
}

echo "##### Phase B Oklawaha matrix start $(date) #####" | tee "$QA/phaseb_oklawaha_driver.log"

# --- DEM 30 m (proven coarse threshold) ---
run_variant pb_base30        --stream 15000 --channel 500
run_variant pb_burnall30     --stream 15000 --channel 500 --burn-flowline-types all
run_variant pb_burnmajor30   --stream 15000 --channel 500 --burn-flowline-types major_rivers
run_variant pb_burnmajorlk30 --stream 15000 --channel 500 --burn-flowline-types major_rivers --use-lakes --lake-min-area 1.0

# --- DEM 250 m (area-equivalent thresholds via basis-res rescale) ---
run_variant pb_base250        --dem-resolution 250 --threshold-basis-res 30 --stream 15000 --channel 500
run_variant pb_burnall250     --dem-resolution 250 --threshold-basis-res 30 --stream 15000 --channel 500 --burn-flowline-types all
run_variant pb_burnmajor250   --dem-resolution 250 --threshold-basis-res 30 --stream 15000 --channel 500 --burn-flowline-types major_rivers
run_variant pb_burnmajorlk250 --dem-resolution 250 --threshold-basis-res 30 --stream 15000 --channel 500 --burn-flowline-types major_rivers --use-lakes --lake-min-area 1.0

echo "##### Phase B Oklawaha matrix done $(date) #####" | tee -a "$QA/phaseb_oklawaha_driver.log"

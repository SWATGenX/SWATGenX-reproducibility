#!/usr/bin/env bash
set -u
PY="sudo -n -u www-data /data/SWATGenXApp/codes/.venv/bin/python"
RUN=/data/SWATGenXApp/codes/publication/analysis/scripts/run_taudem_variant_model.py
QA=/data/SWATGenXApp/codes/publication/analysis/qa
COMMON="--model-id 0308/huc12/030801020804 --delineation taudem --snap 900 --ls-resolution 250 --force-rebuild --clip-dem --burn-flowline-types major_rivers"
run () { local n="$1"; shift; echo "=== [$(date +%H:%M:%S)] $n ===" | tee -a "$QA/phaseb_clip_driver.log"
  timeout -s KILL 1200 $PY "$RUN" $COMMON --model-name "SWAT_MODEL_$n" "$@" > "$QA/phaseb_${n}.log" 2>&1
  echo "    [$(date +%H:%M:%S)] $n exit=$? " | tee -a "$QA/phaseb_clip_driver.log"; }
echo "##### clip matrix start $(date) #####" | tee "$QA/phaseb_clip_driver.log"
run pb_burnmajorclip30  --stream 15000 --channel 500
run pb_burnmajorclip250 --dem-resolution 250 --threshold-basis-res 30 --stream 15000 --channel 500
echo "##### clip matrix done $(date) #####" | tee -a "$QA/phaseb_clip_driver.log"

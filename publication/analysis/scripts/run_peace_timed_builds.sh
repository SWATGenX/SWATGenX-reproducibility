#!/bin/bash
# Sequential, timed NHD-vs-TauDEM model builds for Peace HUC8 03100101 (admin user).
# Each build runs ALONE (no contention) so build_timing.json wall-clocks are comparable.
# NHD uses its native predefined-network delineation; TauDEM uses splitChannelsByLakes + clip
# at three thresholds. Run in the background; emails are sent separately on completion.
set -u
RUNNER=/data/SWATGenXApp/codes/publication/analysis/scripts/run_taudem_variant_model.py
PY=/data/SWATGenXApp/codes/.venv/bin/python
BASE="sudo -n -u www-data $PY $RUNNER --model-id 0310/huc8/03100101 --username admin"
LOGDIR=/tmp
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

echo "===== PEACE TIMED BUILDS START $(stamp) ====="

echo "----- [1/4] NHD (native NHDPlus-HR delineation) $(stamp) -----"
$BASE --delineation nhd --model-name SWAT_MODEL_NHD_timed \
  > $LOGDIR/peace_timed_nhd.log 2>&1
echo "[1/4] NHD exit=$? $(stamp)"

echo "----- [2/4] TauDEM split 5000/1000 $(stamp) -----"
$BASE --delineation taudem --use-lakes --lake-split --clip-dem --stream 5000 --channel 1000 \
  --model-name SWAT_MODEL_TauDEM_split_s5000c1000_clip \
  > $LOGDIR/peace_timed_taudem_s5000c1000.log 2>&1
echo "[2/4] TauDEM 5000/1000 exit=$? $(stamp)"

echo "----- [3/4] TauDEM split 2500/500 $(stamp) -----"
$BASE --delineation taudem --use-lakes --lake-split --clip-dem --stream 2500 --channel 500 \
  --model-name SWAT_MODEL_TauDEM_split_s2500c500_clip \
  > $LOGDIR/peace_timed_taudem_s2500c500.log 2>&1
echo "[3/4] TauDEM 2500/500 exit=$? $(stamp)"

echo "----- [4/4] TauDEM split 1250/250 $(stamp) -----"
$BASE --delineation taudem --use-lakes --lake-split --clip-dem --stream 1250 --channel 250 \
  --model-name SWAT_MODEL_TauDEM_split_s1250c250_clip \
  > $LOGDIR/peace_timed_taudem_s1250c250.log 2>&1
echo "[4/4] TauDEM 1250/250 exit=$? $(stamp)"

echo "===== PEACE TIMED BUILDS DONE $(stamp) ====="

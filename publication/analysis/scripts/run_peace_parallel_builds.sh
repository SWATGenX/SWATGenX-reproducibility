#!/bin/bash
# Parallel, capped TauDEM+lakes builds for Peace HUC8 03100101 (admin user).
# NHD baseline already built earlier (101.3 min, ran alone). Here the three TauDEM
# thresholds run CONCURRENTLY, each capped at 12 h via `timeout`. Fine threshold is
# launched first (CPU priority), coarse last. A detached www-data monitor emails an
# hourly status report (see peace_build_monitor.py).
#
# NOTE: because the three run concurrently, their wall-clocks are NOT directly
# comparable to each other or to the NHD baseline. The goal is a SUCCESSFUL
# TauDEM+lakes build per threshold, not fair timing.
set -u
RUNNER=/data/SWATGenXApp/codes/publication/analysis/scripts/run_taudem_variant_model.py
MONITOR=/data/SWATGenXApp/codes/publication/analysis/scripts/peace_build_monitor.py
PY=/data/SWATGenXApp/codes/.venv/bin/python
MID=0310/huc8/03100101
LOGDIR=/tmp
CAP=12h
COMMON="--model-id $MID --username admin --delineation taudem --use-lakes --lake-split --clip-dem"
stamp() { date '+%Y-%m-%d %H:%M:%S'; }

launch() {  # key stream channel name
  local key=$1 stream=$2 channel=$3 name=$4
  local log=$LOGDIR/peace_par_taudem_$key.log
  : > "$log"
  timeout "$CAP" sudo -n -u www-data "$PY" "$RUNNER" $COMMON \
      --stream "$stream" --channel "$channel" --model-name "$name" \
      >> "$log" 2>&1 &
  echo $! > "$LOGDIR/peace_par_$key.pid"
  echo "[$(stamp)] launched $key (thr $stream/$channel) timeout=$CAP pid=$! -> $log"
}

echo "===== PEACE PARALLEL BUILDS START $(stamp) ====="
# fine first (best chance of threading lakes), then medium, then coarse
launch s1250c250  1250 250  SWAT_MODEL_TauDEM_split_s1250c250_clip
sleep 8
launch s2500c500  2500 500  SWAT_MODEL_TauDEM_split_s2500c500_clip
sleep 8
launch s5000c1000 5000 1000 SWAT_MODEL_TauDEM_split_s5000c1000_clip

START=$(date +%s)
echo "$START" > "$LOGDIR/peace_par_start.epoch"

# detached www-data hourly emailer (survives this shell); runs as www-data so it can
# read the SMTP password and signal the www-data build processes at the cap.
setsid sudo -n -u www-data "$PY" "$MONITOR" "$START" \
    > "$LOGDIR/peace_par_monitor.log" 2>&1 < /dev/null &
echo $! > "$LOGDIR/peace_par_monitor.pid"
echo "[$(stamp)] monitor launched pid=$(cat "$LOGDIR/peace_par_monitor.pid") -> $LOGDIR/peace_par_monitor.log"
echo "===== ALL LAUNCHED $(stamp) (cap $CAP; hourly emails to vahidr32@gmail.com) ====="

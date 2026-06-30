#!/usr/bin/env bash
# PFAS calibration grid search for the Rogue: vary soil_scale (and optionally
# koc_scale) in pfas_calib.dat, run the engine, evaluate vs EGLE, record the
# log-RMSE objective. In-stream conc scales ~linearly with soil_scale, so a
# short grid bracketing the analytic estimate (baseline_ratio^-1) converges fast.
set -uo pipefail
RUN=/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/run_rogue
ASSIGN=${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0405/usgs_station/04118500/SWAT_MODEL_Web_Application/pfas_data/pfas_stations_assignment.csv
EVAL=/data/SWATGenXApp/codes/_temp/pfas-swatplus-port/pfas_calib/pfas_eval.py
PY=/data/SWATGenXApp/codes/.venv/bin/python
cd "$RUN"
source /opt/intel/oneapi/setvars.sh >/dev/null 2>&1 || true

# args: list of "soil_scale:koc_scale" trials (koc default 1.0)
TRIALS=("$@")
[ ${#TRIALS[@]} -eq 0 ] && TRIALS=("0.06:1.0" "0.08:1.0" "0.11:1.0" "0.15:1.0")

echo "trial          obj(logRMSE)   PBIAS%"
best_obj=99 ; best=""
for t in "${TRIALS[@]}"; do
  ss="${t%%:*}" ; kc="${t##*:}"
  printf '%s %s\n' "$ss" "$kc" > pfas_calib.dat
  rm -f success.fin
  ./swatplus_pfas > /dev/null 2>&1
  out=$("$PY" "$EVAL" "$ASSIGN" channel_pfas_day.txt 2>/dev/null)
  obj=$(echo "$out" | grep OBJECTIVE | cut -d= -f2)
  pb=$(echo "$out"  | grep -oE 'PBIAS=[+-][0-9.]+' | cut -d= -f2)
  printf "ss=%-5s kc=%-4s   %-12s   %s\n" "$ss" "$kc" "${obj:-NA}" "${pb:-NA}"
  if [ -n "${obj:-}" ] && awk "BEGIN{exit !($obj < $best_obj)}"; then best_obj="$obj"; best="$t"; fi
done
echo "BEST: $best  obj=$best_obj"

#!/usr/bin/env bash
# Cross-hardware scaling of the FINAL engine (r6clean, commit 34f5c02). One consistent protocol:
# full-wavefront, 1 simulated year, filtered channel_sd daily output, best of 2, thread-pinned.
# Same grid on every box so the curves are directly comparable. Also pins R0 stock + R6 serial
# anchors for the stock-baseline total on each machine.
set -uo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
export LD_LIBRARY_PATH="$B/libs"
M="$B/run"
RES="$B/results.csv"; LOG="$B/bench.log"
echo "rung,threads,rep,wall_s" > "$RES"; : > "$LOG"
echo "[stage] $(date) cores=$(nproc)" | tee -a "$LOG"
rm -rf "$M"; cp -r "$B/model" "$M"; cd "$M"
cat > time.sim <<'TS'
time.sim: ladder
day_start  yrc_start   day_end   yrc_end      step
       1      2011       366      2011         0
TS
python3 - <<'PY'
t=open('print.prt').read().splitlines()
for i,l in enumerate(t):
    if l.split()[:1]==['nyskip']:
        p=t[i+1].split(); p[0]='0'; t[i+1]='           '.join(p); break
open('print.prt','w').write('\n'.join(t)+'\n')
PY
run3(){ local exe="$1" N="$2" tag="$3" rep w t0 t1
  for rep in 1 2; do
    rm -f ./*_day.txt ./*_mon.txt ./*_yr.txt ./*_aa.txt ./*.nc 2>/dev/null
    t0=$(date +%s.%N)
    OMP_NUM_THREADS="$N" OMP_PROC_BIND=close OMP_PLACES=cores OMP_STACKSIZE=512M "$exe" >/dev/null 2>>"$LOG"
    t1=$(date +%s.%N); w=$(awk "BEGIN{print $t1-$t0}")
    echo "$tag,$N,$rep,$w" >> "$RES"; echo "[$(date +%H:%M:%S)] $tag N=$N rep=$rep ${w}s" | tee -a "$LOG"
  done
}
# stock + serial anchors (for stock-baseline total on this machine)
run3 "$B/bins/r0_768f1d1" 1 R0
run3 "$B/bins/r6_34f5c02" 1 R6
# full-wavefront scaling grid (final engine)
for n in 1 2 4 6 8 10 12 16 20 24; do
  [ "$n" -le "$(nproc)" ] && run3 "$B/bins/r6clean" "$n" R6FULL
done
echo "CROSSHW_DONE $(date)" | tee -a "$LOG"

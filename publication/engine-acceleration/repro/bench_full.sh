#!/usr/bin/env bash
# Remote cumulative-ladder timing on a dedicated box. Self-contained (bundle libs only).
# Serial ladder (R0->R6 @ N=1) + final-engine scaling (R6 @ N=2..16) + NetCDF I/O sub-study.
# 1 simulated year, best of 3, same output config across engine rungs (text, channel_sd daily).
set -uo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
export LD_LIBRARY_PATH="$B/libs"
M="$B/run"
RES="$B/results.csv"
LOG="$B/bench.log"
echo "rung,threads,rep,wall_s" > "$RES"
: > "$LOG"

echo "[stage] $(date)  cores=$(nproc)" | tee -a "$LOG"
rm -rf "$M"; cp -r "$B/model" "$M"; cd "$M"

# 1 simulated year
cat > time.sim <<'EOF'
time.sim: ladder
day_start  yrc_start   day_end   yrc_end      step
       1      2011       366      2011         0
EOF
# nyskip=0 so the year emits output (matches a real run's I/O)
python3 - <<'PY'
import re
t=open('print.prt').read().splitlines()
for i,l in enumerate(t):
    if l.split()[:1]==['nyskip'] and i+1<len(t):
        p=t[i+1].split(); p[0]='0'; t[i+1]='           '.join(p); break
open('print.prt','w').write('\n'.join(t)+'\n')
PY
set_cdf(){ python3 -c "import re,sys;t=open('print.prt').read();t=re.sub(r'(csvout\s+dbout\s+cdfout\s*\n\s*\S+\s+\S+\s+)\S+',r'\1$1',t);open('print.prt','w').write(t)"; }

run3(){ local exe="$1" N="$2" tag="$3" envp="${4:-}" rep w t0 t1
  for rep in 1 2; do
    rm -f ./*_day.txt ./*_mon.txt ./*_yr.txt ./*_aa.txt ./*.nc 2>/dev/null   # keep disk clean
    t0=$(date +%s.%N)
    OMP_NUM_THREADS="$N" OMP_PROC_BIND=close OMP_PLACES=cores OMP_STACKSIZE=512M env $envp "$exe" >/dev/null 2>>"$LOG"
    t1=$(date +%s.%N)
    w=$(awk "BEGIN{print $t1-$t0}")
    echo "$tag,$N,$rep,$w" >> "$RES"
    echo "[$(date +%H:%M:%S)] $tag N=$N rep=$rep ${w}s" | tee -a "$LOG"
  done
}

# --- Anchors only (compute ladder R3/R4/R5b/R5c reused from the prior run; here we just pin
#     R0 stock + R6 reference on THIS box for same-box consistency with the scaling below) ---
set_cdf n
run3 "$B/bins/r0_768f1d1" 1 R0
run3 "$B/bins/r6_34f5c02" 1 R6

# --- I/O sub-study: text vs NetCDF (N=1) ---
set_cdf n; run3 "$B/bins/r0_768f1d1" 1 IO_text
set_cdf y; run3 "$B/bins/r0_768f1d1" 1 IO_netcdf
set_cdf n

# --- FULL wavefront vs byte-identical (routing-serial) scaling. SAME clean binary (r6clean);
#     SWATPLUS_ROUTING_SERIAL=1 forces the byte-identical mode. R6FULL = full wavefront,
#     R6SER = byte-identical (HRU-parallel, routing-serial). For the speedup configurator. ---
set_cdf n
for n in 1 2 4 8 16; do run3 "$B/bins/r6clean" "$n" R6FULL; done
for n in 1 2 4 8 16; do run3 "$B/bins/r6clean" "$n" R6SER "SWATPLUS_ROUTING_SERIAL=1"; done

# --- PRINT-FILTER sub-study (N=1, text). "heavy" = realistic full reporting (ALL objects MONTHLY
#     + channel_sd daily); "filter" = channel_sd daily only. Ratio = print-filter factor F.
#     Monthly-not-daily keeps output small (no disk blow-up). ---
set_cdf n
setprint(){ python3 - "$1" <<'PY'
import sys; mode=sys.argv[1]
t=open('print.prt').read().splitlines(); out=[]; insec=False
for l in t:
    s=l.split()
    if s[:1]==['objects']: insec=True; out.append(l); continue
    if insec and len(s)>=5 and s[1] in ('y','n') and s[2] in ('y','n'):
        nm=s[0]
        if mode=='heavy':
            out.append('%-22s y    n    n    n'%nm if nm=='channel_sd' else '%-22s n    y    n    n'%nm)
        else:  # filter: only channel_sd daily
            out.append('%-22s y    n    n    n'%nm if nm=='channel_sd' else '%-22s n    n    n    n'%nm)
    else:
        out.append(l)
open('print.prt','w').write('\n'.join(out)+'\n')
PY
}
setprint heavy ; run3 "$B/bins/r6clean" 1 PRINT_full   "SWATPLUS_ROUTING_SERIAL=1"
setprint filter; run3 "$B/bins/r6clean" 1 PRINT_filter "SWATPLUS_ROUTING_SERIAL=1"
set_cdf n

echo "BENCH_DONE $(date)" | tee -a "$LOG"

# --- BYTE-IDENTITY sweep with the FIXED final engine (1 sim-yr, channel_sd monthly, N up to 32) ---
echo "[byteid] start $(date)" | tee -a "$LOG"
set_cdf n
python3 -c "import re;p=\"$M/print.prt\";t=open(p).read();t=re.sub(r\"^channel_sd\\s+\\S+\\s+\\S+\\s+\\S+\\s+\\S+\",\"channel_sd    n    y    n    n\",t,flags=re.M);open(p,\"w\").write(t)"
for n in 1 8; do
  rm -f "$M/channel_sd_mon.txt"
  ( cd "$M" && OMP_NUM_THREADS="$n" OMP_PROC_BIND=close OMP_PLACES=cores OMP_STACKSIZE=512M "$B/bins/r6clean" >/dev/null 2>>"$LOG" )
  cp -f "$M/channel_sd_mon.txt" "$B/byteid_n${n}.txt" 2>/dev/null
  echo "[byteid] N=$n done $(date +%H:%M:%S)" | tee -a "$LOG"
done
echo "BYTEID_DONE $(date)" | tee -a "$LOG"

# --- FALLBACK byte-identity sweep (HRU-parallel + routing-serial): confirm race-free on AWS too.
#     Expect byteid_fb_n{N} all identical to byteid_fb_n1 (down to FP-reorder ~1e-7). ---
echo "[byteid-fb] start $(date)" | tee -a "$LOG"
for n in 1 4 8 16; do
  rm -f "$M/channel_sd_mon.txt"
  ( cd "$M" && OMP_NUM_THREADS="$n" OMP_PROC_BIND=close OMP_PLACES=cores OMP_STACKSIZE=512M env SWATPLUS_ROUTING_SERIAL=1 "$B/bins/r6clean" >/dev/null 2>>"$LOG" )
  cp -f "$M/channel_sd_mon.txt" "$B/byteid_fb_n${n}.txt" 2>/dev/null
  echo "[byteid-fb] N=$n done $(date +%H:%M:%S)" | tee -a "$LOG"
done
echo "BYTEID_FB_DONE $(date)" | tee -a "$LOG"

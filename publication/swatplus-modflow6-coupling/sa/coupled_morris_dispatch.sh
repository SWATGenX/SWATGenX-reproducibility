#!/usr/bin/env bash
# Dispatch the coupled SWAT+ <-> MODFLOW 6 Morris SA to an EC2 spot box.
# Compute on EC2; this server only orchestrates (build -> launch -> scp -> run ->
# fetch -> terminate via trap). Reuses the cloud-calibration AWS assets.
#   SA_R=20 SA_NPROC=48 INSTANCE_TYPE=c7i.16xlarge bash coupled_morris_dispatch.sh
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODES="${CODES:-/data/SWATGenXApp/codes}"

P="--profile ${AWS_PROFILE_NAME:-swatgenx} --region ${AWS_REGION_NAME:-us-east-1}"
REGION="${AWS_REGION_NAME:-us-east-1}"
PEM="${PEM:-$CODES/ssl_certificate/swatgenx-cal.pem}"
AMI="${AMI:-ami-02013f5b15758f4d4}"
SG="${SG:-sg-0501c61574388c6cc}"
KEY="${KEY:-swatgenx-cal}"
INSTANCE_TYPE="${INSTANCE_TYPE:-c7i.16xlarge}"   # 64 vCPU / 128 GiB
INSTANCE_TYPES="${INSTANCE_TYPES:-${INSTANCE_TYPE} c7a.16xlarge c6i.16xlarge m7i.16xlarge c6a.16xlarge}"
USE_SPOT="${USE_SPOT:-1}"; KEEP_INSTANCE="${KEEP_INSTANCE:-0}"
MAX_WAIT_S="${MAX_WAIT_S:-1800}"; WAIT_INTERVAL="${WAIT_INTERVAL:-30}"; SPOT_FALLBACK_S="${SPOT_FALLBACK_S:-240}"

SA_R="${SA_R:-20}"; SA_NPROC="${SA_NPROC:-48}"; SA_LEVELS="${SA_LEVELS:-4}"; SA_SEED="${SA_SEED:-20260623}"
SA_GW_NYEARS="${SA_GW_NYEARS:-40}"
RUN_LABEL="${RUN_LABEL:-swatgenx-coupled-morris}"
BUNDLE="${BUNDLE:-/tmp/coupled-sa-bundle-$$.tar.gz}"
OUTDIR="${OUTDIR:-$HERE/results}"; mkdir -p "$OUTDIR"
chmod 600 "$PEM" 2>/dev/null || true

echo "[0/6] building coupled-SA bundle ..."
bash "$HERE/build_coupled_bundle.sh" "$BUNDLE" || { echo "[dispatch] bundle build failed" >&2; exit 1; }

MARKET=()
[ "$USE_SPOT" = "1" ] && MARKET=(--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time}')
launch_once(){
  local tags="{Key=Name,Value=$RUN_LABEL},{Key=Project,Value=SWATGenX},{Key=Purpose,Value=coupled-morris-sa},{Key=LaunchedBy,Value=coupled-morris-dispatch}"
  aws $P ec2 run-instances --image-id "$AMI" --instance-type "$1" --key-name "$KEY" \
    --security-group-ids "$SG" --count 1 --monitoring 'Enabled=true' "${MARKET[@]}" \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=150,VolumeType=gp3,Throughput=750,Iops=8000}' \
    --tag-specifications "ResourceType=instance,Tags=[$tags]" \
    --query "Instances[0].InstanceId" --output text 2>/tmp/coupled-sa-launch.err
}
echo "[1/6] launching spot [$INSTANCE_TYPES] in $REGION ..."
IID=""; t_start=$(date +%s); attempts=0
while :; do
  for ITYPE in $INSTANCE_TYPES; do
    attempts=$((attempts+1)); IID=$(launch_once "$ITYPE")
    if [ -n "$IID" ] && [ "$IID" != "None" ]; then INSTANCE_TYPE="$ITYPE"; echo "[1/6] launched $ITYPE instance=$IID (try $attempts)"; break 2; fi
    err=$(tr '\n' ' ' < /tmp/coupled-sa-launch.err 2>/dev/null)
    echo "$err" | grep -qE "Insufficient|capacity|SpotMax|VcpuLimit|InstanceLimit|RequestLimit" && { echo "[1/6] $ITYPE no capacity"; continue; }
    echo "$err" | grep -qE "Unauthorized|not authorized|AccessDenied" && { echo "[1/6] $ITYPE IAM-denied, skip"; continue; }
    echo "[dispatch] launch error ($ITYPE): $err" >&2
  done
  [ -n "$IID" ] && [ "$IID" != "None" ] && break
  elapsed=$(( $(date +%s) - t_start ))
  if [ "${#MARKET[@]}" -gt 0 ] && [ "$elapsed" -ge "$SPOT_FALLBACK_S" ]; then echo "[1/6] spot unavailable ${elapsed}s -> on-demand"; MARKET=(); continue; fi
  [ "$elapsed" -ge "$MAX_WAIT_S" ] && { echo "[dispatch] no capacity after ${elapsed}s" >&2; exit 1; }
  echo "[1/6] waiting ${WAIT_INTERVAL}s ..."; sleep "$WAIT_INTERVAL"
done
BOX_LAUNCHED_AT=$(date +%s)
cleanup(){
  if [ "$KEEP_INSTANCE" = "1" ]; then echo "[keep] leaving $IID running. Terminate: aws $P ec2 terminate-instances --instance-ids $IID"; return 0; fi
  [ -n "${IID:-}" ] && { echo "[cleanup] terminating $IID"; aws $P ec2 terminate-instances --instance-ids "$IID" >/dev/null 2>&1; } || true
}
trap cleanup EXIT
aws $P ec2 wait instance-running --instance-ids "$IID"
IP=$(aws $P ec2 describe-instances --instance-ids "$IID" --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "[2/6] IP=$IP type=$INSTANCE_TYPE"
echo "[console] ssh -i $PEM ubuntu@$IP   then: tail -f /home/ubuntu/coupled_sa/results/run.log"

echo "[3/6] waiting for sshd ..."
up=0
for i in $(seq 1 45); do
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$PEM" ubuntu@"$IP" "echo ok" 2>/dev/null | grep -q ok && { up=1; echo "[3/6] ssh up (${i}x8s)"; break; }
  sleep 8
done
[ "$up" = 1 ] || { echo "[dispatch] ssh never came up" >&2; exit 1; }

echo "[4/6] uploading bundle ($(du -h "$BUNDLE" | cut -f1)) ..."
scp -o StrictHostKeyChecking=no -i "$PEM" "$BUNDLE" ubuntu@"$IP":/tmp/coupled-sa-bundle.tar.gz

echo "[5/6] provisioning + running Morris (R=$SA_R nproc=$SA_NPROC) ..."
REMOTE=$(cat <<REMOTE_EOF
set -e
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq >/dev/null 2>&1 || true
sudo apt-get install -y -qq libnetcdf19 python3-pip python3-venv >/dev/null 2>&1 || true
sudo mkdir -p /mnt/sa_work && sudo chown ubuntu:ubuntu /mnt/sa_work
cd /home/ubuntu && rm -rf coupled_sa && tar -xzf /tmp/coupled-sa-bundle.tar.gz
cd /home/ubuntu/coupled_sa && mkdir -p results
python3 -m venv /home/ubuntu/saenv
/home/ubuntu/saenv/bin/pip install -q --upgrade pip >/dev/null 2>&1
/home/ubuntu/saenv/bin/pip install -q numpy scipy flopy SALib >/dev/null 2>&1
chmod +x sw_model/swatplus_pfas bin/mf6
export SW_MODEL=/home/ubuntu/coupled_sa/sw_model
export SW_BIN=/home/ubuntu/coupled_sa/sw_model/swatplus_pfas
export SW_LD=/home/ubuntu/coupled_sa/libs
export GW_CAL=/home/ubuntu/coupled_sa/gw_model
export GW_MF6=/home/ubuntu/coupled_sa/bin/mf6
export STATIC_NPZ=/home/ubuntu/coupled_sa/static_gw.npz
export SA_WORK=/mnt/sa_work
export SA_OUT=/home/ubuntu/coupled_sa/results
export SA_R=$SA_R SA_NPROC=$SA_NPROC SA_LEVELS=$SA_LEVELS SA_SEED=$SA_SEED SA_GW_NYEARS=$SA_GW_NYEARS
export LD_LIBRARY_PATH=/home/ubuntu/coupled_sa/libs:\${LD_LIBRARY_PATH:-}
echo "[box] self-test (dry-run, imports/paths/SALib) ..."
SA_DRYRUN=1 SA_R=2 SA_OUT=/tmp/st /home/ubuntu/saenv/bin/python coupled_morris.py >/tmp/selftest.log 2>&1 \
  && echo "[box] self-test OK" || { echo "[box] SELF-TEST FAILED:"; tail -25 /tmp/selftest.log; exit 1; }
echo "[box] cpus=\$(nproc) starting Morris at \$(date -u +%H:%M:%S)"
nohup /home/ubuntu/saenv/bin/python coupled_morris.py > results/run.log 2>&1 &
echo \$! > results/run.pid
# stream until the driver writes its DONE line (or dies)
while kill -0 \$(cat results/run.pid) 2>/dev/null; do tail -n 2 results/run.log; sleep 30; done
echo "[box] driver exited; tail:"; tail -n 8 results/run.log
REMOTE_EOF
)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -i "$PEM" ubuntu@"$IP" "$REMOTE" 2>&1 | tee "$OUTDIR/coupled-morris-run.log"

echo "[6/6] fetching Morris results -> $OUTDIR ..."
for f in morris_samples.csv morris_Y.csv morris_summary.json run.log \
         morris_indices_instream_lower.csv morris_indices_instream_mid.csv \
         morris_indices_gw_plume.csv morris_indices_baseflow.csv; do
  scp -o StrictHostKeyChecking=no -i "$PEM" ubuntu@"$IP":/home/ubuntu/coupled_sa/results/$f "$OUTDIR/$f" 2>/dev/null || echo "  (missing $f)"
done
WALL=$(( $(date +%s) - BOX_LAUNCHED_AT ))
echo "==================================================================="
echo "[ok] coupled Morris done. dispatch wall: ${WALL}s ($((WALL/60))m)"
echo "[ok] instance: $([ "$KEEP_INSTANCE" = 1 ] && echo "KEPT $IID" || echo "terminating via trap")"

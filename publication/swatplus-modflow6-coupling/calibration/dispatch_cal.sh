#!/usr/bin/env bash
# Dispatch the MF6 static-head calibration (differential evolution) to an EC2 spot box.
# Reuses the validated cloud assets. Compute on EC2; the server only orchestrates.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODES="${CODES:-/data/SWATGenXApp/codes}"

P="--profile ${AWS_PROFILE_NAME:-swatgenx} --region ${AWS_REGION_NAME:-us-east-1}"
PEM="${PEM:-$CODES/ssl_certificate/swatgenx-cal.pem}"
AMI="${AMI:-ami-02013f5b15758f4d4}"; SG="${SG:-sg-0501c61574388c6cc}"; KEY="${KEY:-swatgenx-cal}"
INSTANCE_TYPE="${INSTANCE_TYPE:-c7i.16xlarge}"          # 64 vCPU
USE_SPOT="${USE_SPOT:-1}"
SRC="${SRC:-${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_250m}"
BUNDLE="/tmp/cal-bundle-$$.tar.gz"
OUT="$HERE/aws_results"; mkdir -p "$OUT"
chmod 600 "$PEM" 2>/dev/null || true

echo "[0/5] staging bundle ..."
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/cal/model" "$STAGE/cal/bin"
for ext in nam tdis ims dis ic npf sto ghb riv drn wel chd rcha oc; do
  cp "$SRC"/*.$ext "$STAGE/cal/model/" 2>/dev/null || true
done
cp "$SRC"/mfsim.nam "$STAGE/cal/model/"
cp "$SRC"/obs_vs_sim.csv "$STAGE/cal/model/"
cp "$CODES/bin/mf6" "$STAGE/cal/bin/mf6"; chmod +x "$STAGE/cal/bin/mf6"
cp "$HERE/calibrate_wl_ec2.py" "$STAGE/cal/"
tar -czf "$BUNDLE" -C "$STAGE" cal
echo "[0/5] bundle $(du -h "$BUNDLE" | cut -f1) ($(ls "$STAGE/cal/model" | wc -l) model files)"

MARKET=(); [ "$USE_SPOT" = 1 ] && MARKET=(--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time}')
echo "[1/5] launching $INSTANCE_TYPE spot ..."
IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY" \
  --security-group-ids "$SG" --count 1 --monitoring 'Enabled=true' "${MARKET[@]}" \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=swatgenx-mf6-cal},{Key=Project,Value=SWATGenX}]' \
  --query "Instances[0].InstanceId" --output text 2>/tmp/cal-launch.err)
if [ -z "$IID" ] || [ "$IID" = None ]; then
  echo "[1/5] spot failed ($(cat /tmp/cal-launch.err)); on-demand"; MARKET=()
  IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY" \
    --security-group-ids "$SG" --count 1 --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3}' \
    --query "Instances[0].InstanceId" --output text)
fi
echo "[1/5] instance=$IID"; BOX_AT=$(date +%s)
cleanup(){ [ -n "${IID:-}" ] && { echo "[cleanup] terminating $IID"; aws $P ec2 terminate-instances --instance-ids "$IID" >/dev/null 2>&1; }; }
trap 'cleanup; rm -rf "$STAGE"' EXIT

aws $P ec2 wait instance-running --instance-ids "$IID"
IP=$(aws $P ec2 describe-instances --instance-ids "$IID" --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "[2/5] IP=$IP"
up=0; for i in $(seq 1 45); do ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$PEM" ubuntu@"$IP" "echo ok" 2>/dev/null | grep -q ok && { up=1; break; }; sleep 8; done
[ "$up" = 1 ] || { echo "ssh never came up" >&2; exit 1; }

echo "[3/5] upload + provision ..."
scp -o StrictHostKeyChecking=no -i "$PEM" "$BUNDLE" ubuntu@"$IP":/tmp/cal.tar.gz
REMOTE='set -e
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq >/dev/null 2>&1 || true
sudo apt-get install -y -qq python3-pip >/dev/null 2>&1 || true
pip3 install -q flopy numpy pandas scipy >/dev/null 2>&1
sudo mkdir -p /mnt/cal_work && sudo chown ubuntu:ubuntu /mnt/cal_work
cd /home/ubuntu && rm -rf cal && tar -xzf /tmp/cal.tar.gz && cd cal
export CAL_WORK=/mnt/cal_work CAL_NPROC=$(nproc)
echo "[box] cpus=$(nproc) starting calibration"
python3 calibrate_wl_ec2.py'
echo "[4/5] running calibration ..."
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -i "$PEM" ubuntu@"$IP" "$REMOTE" 2>&1 | tee "$OUT/run.log"

echo "[5/5] fetching result ..."
scp -o StrictHostKeyChecking=no -i "$PEM" ubuntu@"$IP":/home/ubuntu/cal/calibration_result.json "$OUT/calibration_result.json" 2>/dev/null || echo "  (no result.json)"
WALL=$(( $(date +%s) - BOX_AT ))
echo "[ok] done. wall=${WALL}s ($((WALL/60))m). -> $OUT/calibration_result.json"

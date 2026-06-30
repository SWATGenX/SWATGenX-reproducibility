#!/usr/bin/env bash
# Dispatch the MODGenX convergence sensitivity sweep to an EC2 spot box.
# Reuses the validated cloud-calibration AWS assets. Compute on EC2; server orchestrates.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODES="${CODES:-/data/SWATGenXApp/codes}"

P="--profile ${AWS_PROFILE_NAME:-swatgenx} --region ${AWS_REGION_NAME:-us-east-1}"
REGION="${AWS_REGION_NAME:-us-east-1}"
PEM="${PEM:-$CODES/ssl_certificate/swatgenx-cal.pem}"
AMI="${AMI:-ami-02013f5b15758f4d4}"; SG="${SG:-sg-0501c61574388c6cc}"; KEY="${KEY:-swatgenx-cal}"
INSTANCE_TYPE="${INSTANCE_TYPE:-c7i.4xlarge}"            # 16 vCPU plenty for ~80 small runs
USE_SPOT="${USE_SPOT:-1}"
# source model: the smallest hard model (041000130106), regenerated with GHB lakes
SRC="${SRC:-${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0410/huc12_outlet/041000130106/MODFLOW_250m}"
BUNDLE="/tmp/modgenx-sens-bundle-$$.tar.gz"
OUT="$HERE/results"; mkdir -p "$OUT"
chmod 600 "$PEM" 2>/dev/null || true

# ---- 1. stage bundle: MF6 input files + obs csv + mf6 binary + driver ----
echo "[0/5] staging bundle ..."
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/sens/model" "$STAGE/sens/bin"
# MF6 input files only (skip outputs/rasters/cruft); keep obs_vs_sim.csv for scoring
for ext in nam tdis ims dis ic npf sto ghb riv drn wel chd rcha oc; do
  cp "$SRC"/*.$ext "$STAGE/sens/model/" 2>/dev/null || true
done
cp "$SRC"/mfsim.nam "$STAGE/sens/model/" 2>/dev/null || true
cp "$SRC"/obs_vs_sim.csv "$STAGE/sens/model/"
cp "$CODES/bin/mf6" "$STAGE/sens/bin/mf6"; chmod +x "$STAGE/sens/bin/mf6"
cp "$HERE/sensitivity_driver.py" "$STAGE/sens/"
tar -czf "$BUNDLE" -C "$STAGE" sens
echo "[0/5] bundle $(du -h "$BUNDLE" | cut -f1)  ($(ls "$STAGE/sens/model" | wc -l) model files)"

# ---- 2. launch spot ----
MARKET=(); [ "$USE_SPOT" = 1 ] && MARKET=(--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time}')
echo "[1/5] launching $INSTANCE_TYPE spot in $REGION ..."
IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY" \
  --security-group-ids "$SG" --count 1 --monitoring 'Enabled=true' "${MARKET[@]}" \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=swatgenx-modgenx-sens},{Key=Project,Value=SWATGenX},{Key=Purpose,Value=modgenx-sensitivity}]' \
  --query "Instances[0].InstanceId" --output text 2>/tmp/sens-launch.err)
if [ -z "$IID" ] || [ "$IID" = None ]; then
  echo "[1/5] spot failed ($(cat /tmp/sens-launch.err)); trying on-demand"; MARKET=()
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

echo "[3/5] uploading + provisioning ..."
scp -o StrictHostKeyChecking=no -i "$PEM" "$BUNDLE" ubuntu@"$IP":/tmp/sens.tar.gz
REMOTE='set -e
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq >/dev/null 2>&1 || true
sudo apt-get install -y -qq python3-pip >/dev/null 2>&1 || true
pip3 install -q flopy numpy pandas scipy >/dev/null 2>&1
sudo mkdir -p /mnt/sens_work && sudo chown ubuntu:ubuntu /mnt/sens_work
cd /home/ubuntu && rm -rf sens && tar -xzf /tmp/sens.tar.gz
cd /home/ubuntu/sens
export SENS_WORK=/mnt/sens_work SENS_NPROC=$(nproc)
echo "[box] cpus=$(nproc) starting sweep"
python3 sensitivity_driver.py'
echo "[4/5] running sweep ..."
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -i "$PEM" ubuntu@"$IP" "$REMOTE" 2>&1 | tee "$OUT/run.log"

echo "[5/5] fetching results ..."
scp -o StrictHostKeyChecking=no -i "$PEM" ubuntu@"$IP":/home/ubuntu/sens/results.csv "$OUT/results.csv" 2>/dev/null || echo "  (no results.csv)"
WALL=$(( $(date +%s) - BOX_AT ))
echo "[ok] done. wall=${WALL}s ($((WALL/60))m). results -> $OUT/results.csv"

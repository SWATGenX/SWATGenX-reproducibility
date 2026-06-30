#!/usr/bin/env bash
# Dispatch the PEST++ ies (pilot points + baseflow) calibration to an EC2 spot/on-demand box.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; CODES="${CODES:-/data/SWATGenXApp/codes}"
P="--profile ${AWS_PROFILE_NAME:-swatgenx} --region ${AWS_REGION_NAME:-us-east-1}"
PEM="${PEM:-$CODES/ssl_certificate/swatgenx-cal.pem}"
AMI="${AMI:-ami-02013f5b15758f4d4}"; SG="${SG:-sg-0501c61574388c6cc}"; KEY="${KEY:-swatgenx-cal}"
INSTANCE_TYPE="${INSTANCE_TYPE:-c7i.16xlarge}"; USE_SPOT="${USE_SPOT:-1}"
SRC_M="${SWATGENX_USER_PATH}/SWATplus_by_VPUID/0406/usgs_station/04124500/MODFLOW_wl_250m"
BUNDLE="/tmp/pest-bundle-$$.tar.gz"; OUT="$HERE/aws_results"; mkdir -p "$OUT"; chmod 600 "$PEM" 2>/dev/null||true
echo "[0/5] staging ..."; STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/pest/model" "$STAGE/pest/bin"
for ext in nam tdis ims dis ic npf sto ghb riv drn wel chd rcha oc; do cp "$SRC_M"/*.$ext "$STAGE/pest/model/" 2>/dev/null||true; done
cp "$SRC_M"/mfsim.nam "$STAGE/pest/model/"
cp "$CODES/bin/mf6" "$STAGE/pest/bin/mf6"; cp "$HERE/bin/pestpp-ies" "$STAGE/pest/bin/"; chmod +x "$STAGE/pest/bin/"*
cp "$HERE"/{forward_run.py,control.pst,params.dat,params.dat.tpl,obs.dat.ins,interp_W.npz,obs_wells.csv,riv_cell_group.npz} "$STAGE/pest/"
tar -czf "$BUNDLE" -C "$STAGE" pest; echo "[0/5] bundle $(du -h "$BUNDLE"|cut -f1)"
MARKET=(); [ "$USE_SPOT" = 1 ] && MARKET=(--instance-market-options 'MarketType=spot,SpotOptions={SpotInstanceType=one-time}')
echo "[1/5] launching $INSTANCE_TYPE ..."
IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY" \
  --security-group-ids "$SG" --count 1 "${MARKET[@]}" \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=swatgenx-pestpp-ies},{Key=Project,Value=SWATGenX}]' \
  --query "Instances[0].InstanceId" --output text 2>/tmp/pest-launch.err)
if [ -z "$IID" ]||[ "$IID" = None ]; then echo "spot failed ($(cat /tmp/pest-launch.err)); on-demand"; \
  IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$INSTANCE_TYPE" --key-name "$KEY" --security-group-ids "$SG" --count 1 --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3}' --query "Instances[0].InstanceId" --output text); fi
echo "[1/5] instance=$IID"; BOX_AT=$(date +%s)
cleanup(){ [ -n "${IID:-}" ]&&{ echo "[cleanup] terminating $IID"; aws $P ec2 terminate-instances --instance-ids "$IID" >/dev/null 2>&1; }; }
trap 'cleanup; rm -rf "$STAGE"' EXIT
aws $P ec2 wait instance-running --instance-ids "$IID"
IP=$(aws $P ec2 describe-instances --instance-ids "$IID" --query "Reservations[0].Instances[0].PublicIpAddress" --output text); echo "[2/5] IP=$IP"
up=0; for i in $(seq 1 45); do ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$PEM" ubuntu@"$IP" "echo ok" 2>/dev/null|grep -q ok&&{ up=1; break; }; sleep 8; done
[ "$up" = 1 ]||{ echo "ssh down" >&2; exit 1; }
echo "[3/5] upload+provision ..."; scp -o StrictHostKeyChecking=no -i "$PEM" "$BUNDLE" ubuntu@"$IP":/tmp/pest.tar.gz
REMOTE='set -e; export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq >/dev/null 2>&1||true; sudo apt-get install -y -qq python3-pip >/dev/null 2>&1||true
pip3 install -q flopy numpy pandas scipy >/dev/null 2>&1
cd /home/ubuntu && rm -rf pest && tar -xzf /tmp/pest.tar.gz && cd pest && chmod +x bin/*
NAG=$(($(nproc)-2)); echo "[box] cpus=$(nproc) agents=$NAG"
sudo mkdir -p /mnt/ag && sudo chown ubuntu:ubuntu /mnt/ag
for i in $(seq 1 $NAG); do d=/mnt/ag/a$i; mkdir -p $d; ln -s /home/ubuntu/pest/model $d/model; ln -s /home/ubuntu/pest/bin $d/bin
  cp forward_run.py control.pst params.dat params.dat.tpl obs.dat.ins interp_W.npz obs_wells.csv riv_cell_group.npz $d/; done
./bin/pestpp-ies control.pst /h :4004 > master.log 2>&1 & MPID=$!; sleep 8
for i in $(seq 1 $NAG); do (cd /mnt/ag/a$i && FR_WORK=/mnt/ag/a$i/_run ./bin/pestpp-ies control.pst /h localhost:4004 >/dev/null 2>&1) & done
wait $MPID; echo "[box] done"; tail -20 master.log'
echo "[4/5] running pestpp-ies ..."; ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -i "$PEM" ubuntu@"$IP" "$REMOTE" 2>&1|tee "$OUT/run.log"
echo "[5/5] fetching ..."; for f in control.phi.actual.csv control.3.par.csv control.3.obs.csv control.2.par.csv master.log; do
  scp -o StrictHostKeyChecking=no -i "$PEM" ubuntu@"$IP":/home/ubuntu/pest/$f "$OUT/" 2>/dev/null||true; done
WALL=$(( $(date +%s)-BOX_AT )); echo "[ok] wall=${WALL}s ($((WALL/60))m) -> $OUT/"

#!/usr/bin/env bash
# Provision ONE dedicated c8a.8xlarge (on-demand), ship the bench bundle, run the cumulative-ladder
# timing campaign (nohup on the box, survives ssh drops). Prints instance id + IP, then the launcher
# exits — poll/fetch with aws_ladder_fetch.sh. Terminate with aws_ladder_term.sh.
set -uo pipefail
P="--profile swatgenx --region us-east-1"
PEM=/data/SWATGenXApp/codes/ssl_certificate/swatgenx-cal.pem
AMI=ami-02013f5b15758f4d4
SG=sg-0501c61574388c6cc
KEY=swatgenx-cal
TYPE=c8a.8xlarge
BUNDLE=/tmp/aws-bench/bench-bundle.tar.gz
STATE=/tmp/aws-bench/instance.env
chmod 600 "$PEM" 2>/dev/null || true

echo "[1/5] launching on-demand $TYPE ..."
IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$TYPE" --key-name "$KEY" \
  --security-group-ids "$SG" --count 1 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=swatgenx-engine-ladder}]' \
  --query "Instances[0].InstanceId" --output text) || { echo "RUN-INSTANCES FAILED"; exit 1; }
echo "  instance=$IID"
echo "IID=$IID" > "$STATE"

echo "[2/5] waiting for running + public IP ..."
aws $P ec2 wait instance-running --instance-ids "$IID"
IP=$(aws $P ec2 describe-instances --instance-ids "$IID" --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "  ip=$IP"; echo "IP=$IP" >> "$STATE"

echo "[3/5] waiting for ssh ..."
up=0
for i in $(seq 1 40); do
  if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$PEM" ubuntu@"$IP" "echo ok" 2>/dev/null | grep -q ok; then up=1; echo "  ssh up after $((i*8))s"; break; fi
  sleep 8
done
[ "$up" = 1 ] || { echo "SSH NEVER CAME UP"; exit 1; }

echo "[4/5] shipping bundle ($(du -h "$BUNDLE"|cut -f1)) ..."
scp -o StrictHostKeyChecking=no -i "$PEM" "$BUNDLE" ubuntu@"$IP":/tmp/bench-bundle.tar.gz

echo "[5/5] extracting + launching ladder (nohup) ..."
ssh -o StrictHostKeyChecking=no -i "$PEM" ubuntu@"$IP" '
  set -e
  sudo apt-get update -qq >/dev/null 2>&1 || true
  command -v python3 >/dev/null || sudo apt-get install -y -qq python3 >/dev/null 2>&1
  # NetCDF C runtime (libnetcdf.so.19) — the ifx binaries link it; not in the bundle.
  sudo apt-get install -y -qq libnetcdf19 libhdf5-103 libcurl4 >/dev/null 2>&1 || true
  cd /home/ubuntu && rm -rf bundle && tar -xzf /tmp/bench-bundle.tar.gz
  chmod +x bundle/bench_remote.sh bundle/bins/*
  nohup bash bundle/bench_remote.sh > /home/ubuntu/ladder.out 2>&1 &
  sleep 2; echo "  remote bench launched, log: /home/ubuntu/bundle/bench.log"
'
echo "=== LAUNCHED: $IID @ $IP ==="
echo "poll: bash $(dirname "$0")/aws_ladder_fetch.sh"

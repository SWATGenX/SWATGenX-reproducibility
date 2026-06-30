#!/usr/bin/env bash
# Launch ONE instance of a given type, ship bundle, run bench_crosshw.sh (nohup).
set -uo pipefail
TYPE="$1"; NAME="$2"
P="--profile swatgenx --region us-east-1"
PEM=/data/SWATGenXApp/codes/ssl_certificate/swatgenx-cal.pem
AMI=ami-02013f5b15758f4d4; SG=sg-0501c61574388c6cc; KEY=swatgenx-cal
BUNDLE=/tmp/aws-bench/bench-bundle.tar.gz
STATE=/tmp/aws-bench/crosshw_${NAME}.env
chmod 600 "$PEM" 2>/dev/null || true
echo "[$NAME] launching $TYPE ..."
IID=$(aws $P ec2 run-instances --image-id "$AMI" --instance-type "$TYPE" --key-name "$KEY" \
  --security-group-ids "$SG" --count 1 \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=swatgenx-crosshw-$NAME}]" \
  --query "Instances[0].InstanceId" --output text) || { echo "[$NAME] RUN FAILED"; exit 1; }
echo "IID=$IID" > "$STATE"; echo "TYPE=$TYPE" >> "$STATE"; echo "NAME=$NAME" >> "$STATE"
aws $P ec2 wait instance-running --instance-ids "$IID"
IP=$(aws $P ec2 describe-instances --instance-ids "$IID" --query "Reservations[0].Instances[0].PublicIpAddress" --output text)
echo "IP=$IP" >> "$STATE"; echo "[$NAME] $IID @ $IP"
for i in $(seq 1 45); do
  ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i "$PEM" ubuntu@"$IP" "echo ok" 2>/dev/null | grep -q ok && { echo "[$NAME] ssh up"; break; }
  sleep 8
done
scp -o StrictHostKeyChecking=no -i "$PEM" "$BUNDLE" ubuntu@"$IP":/tmp/bench-bundle.tar.gz
ssh -o StrictHostKeyChecking=no -i "$PEM" ubuntu@"$IP" '
  sudo apt-get update -qq >/dev/null 2>&1 || true
  sudo apt-get install -y -qq libnetcdf19 libhdf5-103 libcurl4 python3 >/dev/null 2>&1 || true
  cd /home/ubuntu && rm -rf bundle && tar -xzf /tmp/bench-bundle.tar.gz
  chmod +x bundle/bench_crosshw.sh bundle/bins/*
  nohup bash bundle/bench_crosshw.sh > /home/ubuntu/crosshw.out 2>&1 &
  sleep 2; echo "  launched"
'
echo "[$NAME] === LAUNCHED $TYPE: $IID @ $IP ==="

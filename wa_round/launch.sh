#!/bin/bash
# Run the pipeline for one design on the cluster (Mac can be closed afterwards).
#   ./launch.sh DESIGN                         full run: s1 -> gate -> s2 -> s3
#   ./launch.sh DESIGN --only s1               one stage only
#   ./launch.sh DESIGN --from s3               resume from a stage (uses files already in /work/pipe/DESIGN)
#   ./launch.sh DESIGN --only s3 --src /work/rw/builds/rw-xxx    card-test an existing build
# DESIGN must have designs/DESIGN.env. Watch: kubectl -n hls4ml-nrp logs -f job/pipe-DESIGN
set -e
cd "$(dirname "$0")"
D=$1; shift || true
[ -n "$D" ] && [ -f "designs/$D.env" ] || { echo "usage: $0 DESIGN [--from sN] [--only sN] [--src DIR]  (needs designs/DESIGN.env)"; exit 1; }
FROM=s1; ONLY=; SRC=
while [ $# -gt 0 ]; do
  case $1 in --from) FROM=$2; shift 2;; --only) ONLY=$2; shift 2;; --src) SRC=$2; shift 2;; *) echo "unknown option $1"; exit 1;; esac
done
CLK=3.333; SLR=SLR2; STOP_ON_RISK=0; MODEL_PATH=; DATA_DIR=/work/rw/data
source "designs/$D.env"
MODEL_PATH=${MODEL_PATH:-/work/rw/models/$MODEL.h5}
DIR=${SRC:-/work/pipe/$D}
mkdir -p "rendered/$D"
for s in s1 s2 s3; do
  sed -e "s|__NAME__|$D|g" -e "s|__MODEL__|$MODEL|g" -e "s|__RF__|$RF|g" -e "s|__PREC__|$PREC|g" \
      -e "s|__STRAT__|$STRAT|g" -e "s|__CLK__|$CLK|g" -e "s|__SLR__|$SLR|g" -e "s|__DIR__|$DIR|g" -e "s|__MODEL_PATH__|$MODEL_PATH|g" -e "s|__DATA_DIR__|$DATA_DIR|g" \
      "job-$s-TEMPLATE.yaml" > "rendered/$D/$s.yaml"
done
sed -e "s|__NAME__|$D|g" -e "s|__FROM__|$FROM|g" -e "s|__ONLY__|$ONLY|g" -e "s|__STOP_ON_RISK__|$STOP_ON_RISK|g" \
    job-pipe-TEMPLATE.yaml > "rendered/$D/pipe.yaml"
kubectl -n hls4ml-nrp delete job "pipe-$D" --ignore-not-found --wait=true
kubectl -n hls4ml-nrp delete configmap "pipe-$D-jobs" --ignore-not-found
kubectl -n hls4ml-nrp create configmap "pipe-$D-jobs" --from-file="rendered/$D/s1.yaml" --from-file="rendered/$D/s2.yaml" --from-file="rendered/$D/s3.yaml"
kubectl apply -f "rendered/$D/pipe.yaml"
echo "launched pipe-$D (from=$FROM only=${ONLY:-none})"
echo "watch: kubectl -n hls4ml-nrp logs -f job/pipe-$D"

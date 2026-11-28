#!/bin/bash
# Run the pipeline for one design on the cluster (the Mac can be closed afterwards). Uses the namespace of your current
# kubectl context:  kubectl config set-context --current --namespace=<your-namespace>
#   ./launch.sh DESIGN                 full run: s1 -> gate -> s2 -> s3 (s3 only if CARD=1)
#   ./launch.sh DESIGN --only s1       one stage only
#   ./launch.sh DESIGN --from s2       resume from a stage (uses files already in /work/pipe/DESIGN)
#   ./launch.sh DESIGN --adopt         pick up stage Jobs that already ran (e.g. after a lost controller) instead of rerunning them
# DESIGN must have designs/DESIGN.env. Watch: kubectl logs -f job/pipe-DESIGN
set -e
cd "$(dirname "$0")"
D=$1; shift || true
[ -n "$D" ] && [ -f "designs/$D.env" ] || { echo "usage: $0 DESIGN [--from sN] [--only sN]  (needs designs/DESIGN.env)"; exit 1; }
FROM=s1; ONLY=; SRC=; ADOPT=0
while [ $# -gt 0 ]; do
  case $1 in --from) FROM=$2; shift 2;; --only) ONLY=$2; shift 2;; --src) SRC=$2; shift 2;; --adopt) ADOPT=1; shift;; *) echo "unknown option $1"; exit 1;; esac
done
# defaults = the U55C study setup; designs/*.env override what differs
CLK=3.333; SLR=SLR2; STOP_ON_RISK=0; MODEL_PATH=; DATA_DIR=/work/rw/data
BOARD=alveo-u55c; SLR_DSP=2879; VITIS=/tools/Xilinx/Vitis/2024.2/settings64.sh; HLS4ML=wheel
PLATFORMS=/opt/xilinx/platforms; S1_MEM=6Gi; CARD=1
source "designs/$D.env"
MODEL_PATH=${MODEL_PATH:-/work/rw/models/$MODEL.h5}
DIR=${SRC:-/work/pipe/$D}
mkdir -p "rendered/$D"
render() {  # template out s1_mem
  sed -e "s|__NAME__|$D|g" -e "s|__MODEL__|$MODEL|g" -e "s|__RF__|$RF|g" -e "s|__PREC__|$PREC|g" \
      -e "s|__STRAT__|$STRAT|g" -e "s|__CLK__|$CLK|g" -e "s|__SLR__|$SLR|g" -e "s|__DIR__|$DIR|g" \
      -e "s|__MODEL_PATH__|$MODEL_PATH|g" -e "s|__DATA_DIR__|$DATA_DIR|g" -e "s|__BOARD__|$BOARD|g" \
      -e "s|__SLR_DSP__|$SLR_DSP|g" -e "s|__VITIS__|$VITIS|g" -e "s|__HLS4ML__|$HLS4ML|g" \
      -e "s|__PLATFORMS__|$PLATFORMS|g" -e "s|__S1_MEM__|$3|g" "$1" > "$2"
}
render job-s1-TEMPLATE.yaml rendered/$D/s1.yaml $S1_MEM
render job-s1-TEMPLATE.yaml rendered/$D/s1big.yaml 16Gi      # used only if s1 is OOMKilled (pre-registered retry)
render job-s2-TEMPLATE.yaml rendered/$D/s2.yaml $S1_MEM
render job-s3-TEMPLATE.yaml rendered/$D/s3.yaml $S1_MEM
sed -e "s|__NAME__|$D|g" -e "s|__FROM__|$FROM|g" -e "s|__ONLY__|$ONLY|g" -e "s|__STOP_ON_RISK__|$STOP_ON_RISK|g" \
    -e "s|__CARD__|$CARD|g" -e "s|__RUN__|$(date +%s)|g" -e "s|__ADOPT__|$ADOPT|g" job-pipe-TEMPLATE.yaml > "rendered/$D/pipe.yaml"
if grep -l "__[A-Z0-9_]*__" rendered/$D/*.yaml; then echo "unfilled placeholder above"; exit 1; fi
kubectl delete job "pipe-$D" --ignore-not-found --wait=true
kubectl delete configmap "pipe-$D-jobs" --ignore-not-found
kubectl create configmap "pipe-$D-jobs" --from-file=rendered/$D/s1.yaml --from-file=rendered/$D/s1big.yaml \
  --from-file=rendered/$D/s2.yaml --from-file=rendered/$D/s3.yaml
kubectl apply -f "rendered/$D/pipe.yaml"
echo "launched pipe-$D (from=$FROM only=${ONLY:-none})   watch: kubectl logs -f job/pipe-$D"

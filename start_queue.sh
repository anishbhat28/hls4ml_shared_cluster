#!/bin/bash
# Start the build queue ON THE CLUSTER (your Mac can be closed afterwards).
#   ./start_queue.sh queue-main 5 job-rw-jet-*.yaml job-rw-big-r4-*.yaml ...
# Watch:  kubectl -n hls4ml-nrp logs -f job/queue-main
# Stop:   kubectl -n hls4ml-nrp delete job queue-main   (running builds keep running)
set -e
QN=$1; N=$2; shift 2
[ -n "$QN" ] && [ -n "$N" ] && [ $# -gt 0 ] || { echo "usage: $0 QUEUE_NAME N job-files..."; exit 1; }
kubectl apply -f queue-rbac.yaml
kubectl -n hls4ml-nrp delete job "$QN" --ignore-not-found
kubectl -n hls4ml-nrp delete configmap "$QN-jobs" --ignore-not-found
args=(); order=""
for f in "$@"; do args+=(--from-file="$f"); order="$order $(basename "$f")"; done
kubectl -n hls4ml-nrp create configmap "$QN-jobs" "${args[@]}"
sed -e "s|__QN__|$QN|g" -e "s|__N__|$N|g" -e "s|__ORDER__|$order|g" job-queue-TEMPLATE.yaml | kubectl apply -f -
echo "queue $QN started with N=$N and $# job files"

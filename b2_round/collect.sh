#!/bin/bash
# Copy the batch-2 build folders from /work/pipe (logs, reports, result.json; no xclbins or bundles) to ./results/
# and build results/results.csv.
set -e
cd "$(dirname "$0")"
DESIGNS=$(ls designs | sed 's/\.env$//')
kubectl delete pod pipe-peek --ignore-not-found --wait=true >/dev/null
kubectl apply -f pod-pipe-peek.yaml >/dev/null
kubectl wait --for=condition=Ready pod/pipe-peek --timeout=5m >/dev/null
EXIST=$(kubectl exec pipe-peek -- sh -c "cd /work/pipe && for d in $DESIGNS; do [ -d \$d ] && echo \$d; done")
kubectl exec pipe-peek -- tar czf - --exclude='*.xclbin' --exclude='bundle.tgz' --exclude='prj_sources.tgz' -C /work/pipe $EXIST > pipe.tgz
gzip -t pipe.tgz
rm -rf results && mkdir results && tar xzf pipe.tgz -C results && rm pipe.tgz
kubectl delete pod pipe-peek --wait=false >/dev/null
python3 aggregate.py results > results/results.csv
echo "saved $(echo $EXIST | wc -w) designs to results/"
python3 -c "
import csv
for r in csv.DictReader(open('results/results.csv')):
    print(f\"{r['design']:30s} {r['outcome']:12s} gate={str(r.get('gate_verdict'))[:4]:5s} clk={r.get('kernel_clock_mhz') or '':6s} exact={r.get('bitexact_vs_csim') or ''}\")"

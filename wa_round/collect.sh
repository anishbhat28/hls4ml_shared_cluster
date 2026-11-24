#!/bin/bash
# Copy /work/pipe (logs, reports, result.json; no xclbins or bundles) to ./results/ and build results.csv.
set -e
cd "$(dirname "$0")"
kubectl apply -f pod-pipe-peek.yaml >/dev/null
kubectl -n hls4ml-nrp wait --for=condition=Ready pod/pipe-peek --timeout=5m >/dev/null
kubectl -n hls4ml-nrp exec pipe-peek -- tar czf - --exclude='*.xclbin' --exclude='bundle.tgz' --exclude='prj_sources.tgz' \
  -C /work pipe > pipe.tgz
gzip -t pipe.tgz
rm -rf results && mkdir results && tar xzf pipe.tgz -C results --strip-components=1 && rm pipe.tgz
kubectl -n hls4ml-nrp delete pod pipe-peek --wait=false >/dev/null
python3 aggregate.py results > results/results.csv
echo "saved $(ls results | grep -vc results.csv) designs to results/"; column -s, -t < results/results.csv | cut -c1-200

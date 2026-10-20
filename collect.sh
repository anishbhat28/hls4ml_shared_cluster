#!/bin/bash
# Run on your Mac after jobs finish (before deleting any of them). Safe to rerun.
# 1. Logs and pod records (start/finish times, node, OOMKilled reason) for every rw-* job.
# 2. The measurement files each build wrote on /work (stages, memory/CPU samples, reports, C-sim outputs),
#    copied to results/work_rw.tgz. The xclbins stay on the cluster.
NS=hls4ml-nrp
mkdir -p results
kubectl -n $NS get jobs | grep -E '^(NAME|rw-|queue)' | tee results/jobs.txt
for n in $(kubectl -n $NS get jobs -o name | sed 's|job.batch/||' | grep '^rw-'); do
  kubectl -n $NS logs job/$n > results/$n.log 2>&1 || true
  kubectl -n $NS get job $n -o json > results/$n.job.json
  kubectl -n $NS get pods -l job-name=$n -o json > results/$n.pod.json
  echo "saved $n"
done

kubectl -n $NS delete pod rw-peek --ignore-not-found >/dev/null
kubectl apply -f pod-rw-peek.yaml >/dev/null
kubectl -n $NS wait --for=condition=Ready pod/rw-peek --timeout=10m
# stream the archive straight to the Mac (kubectl cp can silently truncate large files), then verify it
for try in 1 2 3; do
  kubectl -n $NS exec rw-peek -- sh -c 'cd /work/rw && L=""; for f in builds data/X_stress.npy HLS4ML_COMMIT csimcheck*.json card_results_*.csv card_xbutil_*.txt; do [ -e "$f" ] && L="$L $f"; done; tar czf - --exclude="*.xclbin" --exclude="prj_sources.tgz" $L' > results/work_rw.tgz
  if gzip -t results/work_rw.tgz 2>/dev/null; then echo "work_rw.tgz OK ($(ls -lh results/work_rw.tgz | awk '{print $5}'))"; break; fi
  echo "archive incomplete, retrying ($try)"
done
kubectl -n $NS delete pod rw-peek --wait=false >/dev/null
gzip -t results/work_rw.tgz || echo "WARNING: work_rw.tgz is still incomplete - tell Claude"
echo "done: zip the results folder and send it"

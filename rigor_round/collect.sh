#!/bin/bash
# Run on your Mac after ALL rg- jobs (including rg-card) have finished, before deleting any of them. Safe to rerun.
NS=hls4ml-nrp
mkdir -p results_rg
kubectl -n $NS get jobs | grep -E '^(NAME|rg-)' | tee results_rg/jobs.txt
for n in $(kubectl -n $NS get jobs -o name | sed 's|job.batch/||' | grep '^rg-'); do
  kubectl -n $NS logs job/$n > results_rg/$n.log 2>&1 || true
  kubectl -n $NS get job $n -o json > results_rg/$n.job.json
  kubectl -n $NS get pods -l job-name=$n -o json > results_rg/$n.pod.json   # includes the exact image digest (imageID)
  echo "saved $n"
done
kubectl -n $NS delete pod rg-peek --ignore-not-found >/dev/null
kubectl apply -f pod-rg-peek.yaml >/dev/null
kubectl -n $NS wait --for=condition=Ready pod/rg-peek --timeout=10m
for try in 1 2 3; do
  kubectl -n $NS exec rg-peek -- sh -c 'cd /work/rw && L=$(ls -d builds/rg-* card_results_rg.csv card_xbutil_rg_* 2>/dev/null); tar czf - --exclude="*.xclbin" --exclude="prj_sources.tgz" $L' > results_rg/work_rg.tgz
  if gzip -t results_rg/work_rg.tgz 2>/dev/null; then echo "work_rg.tgz OK ($(ls -lh results_rg/work_rg.tgz | awk '{print $5}'))"; break; fi
  echo "archive incomplete, retrying ($try)"
done
kubectl -n $NS delete pod rg-peek --wait=false >/dev/null
gzip -t results_rg/work_rg.tgz || echo "WARNING: work_rg.tgz is still incomplete"
echo "== libudev stub used per build (every line should say with-udev-stub)"
grep -H '^udev wrapper:' results_rg/rg-*.log | sed 's#results_rg/##' | tee results_rg/udev_wrapper_check.txt
bad=$(grep -L '^udev wrapper: with-udev-stub' $(ls results_rg/rg-*.log | grep -v rg-card) 2>/dev/null)
[ -z "$bad" ] && echo "stub check OK" || echo "WARNING: no with-udev-stub line in: $bad"
echo "done: zip results_rg and send it"

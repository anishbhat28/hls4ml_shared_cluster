#!/bin/bash
# wa-hls4ml round. Run on your Mac from this folder.
#   ./launch_wa.sh prep     build the 12 models + inputs into /work/wa (a few minutes)
#   ./launch_wa.sh batch1   start the first 6 pipelines (s1 -> gate -> s2 -> s3, on the cluster; Mac can close)
#   ./launch_wa.sh batch2   start the other 6 (after batch1's links have finished, to keep <= 6 links at once)
#   ./launch_wa.sh status   one line per design
set -e
cd "$(dirname "$0")"
NS=hls4ml-nrp
B1="wa-anomaly-r1-p16-lat wa-automlp-r1-p16-res wa-cookie-r128-p8-lat wa-jet-r128-p8-lat wa-particle-r1-p8-res wa-quarks-r1-p16-lat"
B2="wa-anomaly-r1024-p16-res wa-automlp-r1024-p16-lat wa-cookie-r128-p8-res wa-jet-r1024-p16-res wa-particle-r1-p2-res wa-quarks-r128-p16-lat"
case "$1" in
  prep)
    kubectl -n $NS delete configmap wa-prep --ignore-not-found >/dev/null
    kubectl -n $NS create configmap wa-prep --from-file=wa_sample.json --from-file=prep_wa.py --from-file=sample_wa.py
    kubectl -n $NS delete job wa-prep --ignore-not-found --wait=true >/dev/null
    kubectl apply -f job-wa-prep.yaml
    echo "watch: kubectl -n $NS logs -f job/wa-prep" ;;
  batch1) for d in $B1; do ./launch.sh $d; done ;;
  batch2) for d in $B2; do ./launch.sh $d; done ;;
  status)
    for d in $B1 $B2; do
      j=$(kubectl -n $NS get jobs -l design=$d --no-headers 2>/dev/null | awk '{print $1":"$2}' | tr '\n' ' ')
      echo "$d  ${j:-not started}"
    done ;;
  *) echo "usage: ./launch_wa.sh prep|batch1|batch2|status"; exit 1 ;;
esac

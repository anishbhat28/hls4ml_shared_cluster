#!/bin/bash
# Batch 2. Run on your Mac from this folder, with your namespace as the current kubectl context.
#   ./launch_b2.sh prep     build the 12 new random-sample models + inputs into /work/wa2 (a few minutes)
#   ./launch_b2.sh smoke    stage 1 only, one design per new toolchain (hls4ml main, Vitis 2023.2, 2025.2, U250 branch)
#   ./launch_b2.sh g1       6 random-sample designs (full pipeline)
#   ./launch_b2.sh g2       the other 6 random-sample designs
#   ./launch_b2.sh g3       hls4ml main x3 + Vitis 2023.2 x3
#   ./launch_b2.sh g4       Vitis 2025.2 x3 + U250 x3
#   ./launch_b2.sh status   one line per design
# Start the next group when the previous group's links have finished, so at most 6 links run at once.
set -e
cd "$(dirname "$0")"
G1="wa-anomaly-r1024-p8-res wa-automlp-r128-p16-lat wa-cookie-r128-p16-lat wa-jet-r1-p2-lat wa-particle-r128-p2-lat wa-quarks-r128-p16-res"
G2="wa-anomaly-r128-p2-res wa-automlp-r1024-p2-res wa-cookie-r1-p8-res wa-jet-r1024-p2-lat wa-particle-r1024-p2-res wa-quarks-r1024-p2-res"
G3="hm-jet-r4-p16-res hm-jet-r4-p16-lat hm-wa-quarks-r1-p16-lat v23-jet-r4-p16-res v23-jet-r4-p16-lat v23-wa-quarks-r1-p16-lat"
G4="v25-jet-r4-p16-res v25-jet-r4-p16-lat v25-wa-quarks-r1-p16-lat u250-jet-r4-p16-res u250-big-r4-w8-res u250-wa-quarks-r1-p16-lat"
SMOKE="hm-wa-quarks-r1-p16-lat v23-wa-quarks-r1-p16-lat v25-wa-quarks-r1-p16-lat u250-wa-quarks-r1-p16-lat"
case "$1" in
  prep)
    kubectl delete configmap b2-prep --ignore-not-found >/dev/null
    kubectl create configmap b2-prep --from-file=wa_sample_b2.json --from-file=prep_wa.py --from-file=sample_b2.py
    kubectl delete job b2-prep --ignore-not-found --wait=true >/dev/null
    kubectl apply -f job-b2-prep.yaml
    echo "watch: kubectl logs -f job/b2-prep" ;;
  smoke) for d in $SMOKE; do ./launch.sh $d --only s1; done ;;
  g1) for d in $G1; do ./launch.sh $d; done ;;
  g2) for d in $G2; do ./launch.sh $d; done ;;
  g3) for d in $G3; do ./launch.sh $d; done ;;
  g4) for d in $G4; do ./launch.sh $d; done ;;
  status)
    for d in $G1 $G2 $G3 $G4; do
      j=$(kubectl get jobs -l design=$d --no-headers 2>/dev/null | awk '{print $1":"$2}' | tr '\n' ' ')
      last=$(kubectl logs job/pipe-$d --tail=1 2>/dev/null | cut -c1-90)
      printf "%-28s %-40s %s\n" "$d" "${j:-not started}" "$last"
    done ;;
  *) echo "usage: ./launch_b2.sh prep|smoke|g1|g2|g3|g4|status"; exit 1 ;;
esac

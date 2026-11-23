#!/bin/bash
# Run on your Mac, from this folder.
#   ./launch.sh phase1   -> the 10 jobs that start now (r1-r3, t1, q1-q4, p1-p2)
#   ./launch.sh t2       -> start ONLY after rg-t1 has finished (same node; keeps t1 and t2 alone on cpu03)
#   ./launch.sh card     -> after every build has finished: validate all new bitstreams on a U55C (~3 min)
set -e
NS=hls4ml-nrp
# every rg- job and the card job must be pinned to one vivado-vitis digest (./pin_image.sh)
unpinned=$(grep -L 'image: gitlab-registry.nrp-nautilus.io/nrp/coder-images/vivado-vitis@sha256:[0-9a-f]\{64\}' jobs/*.yaml rg-card.yaml || true)
[ -z "$unpinned" ] || { echo "not pinned to a digest: $unpinned -> run ./pin_image.sh first"; exit 1; }
[ "$(grep -ho 'vivado-vitis@sha256:[0-9a-f]\{64\}' jobs/*.yaml rg-card.yaml | sort -u | wc -l)" -eq 1 ] || { echo "jobs are pinned to different digests -> rerun ./pin_image.sh"; exit 1; }
mkdir -p results_rg/node_snapshots
snap() { for n in "$@"; do kubectl describe node $n > results_rg/node_snapshots/$(date +%Y%m%dT%H%M)_$n.txt 2>&1 || true; done; }
case "$1" in
  phase1)
    git -C .. rev-parse HEAD 2>/dev/null > results_rg/repo_commit_at_launch.txt || true
    snap nautilus-it-gpu08.fullerton.edu chi-dgx-node02.csuchico.edu nautilus-it-cpu03.fullerton.edu
    # the four-way and the pair must start together: apply them back to back
    for f in jobs/rg-q*.yaml jobs/rg-p*.yaml jobs/rg-t1-*.yaml jobs/rg-r*.yaml; do kubectl apply -f $f; done ;;
  t2)
    s=$(kubectl -n $NS get job rg-t1-big-r4-w8-res -o jsonpath='{.status.conditions[0].type}' 2>/dev/null)
    [ "$s" = "Complete" ] || [ "$s" = "Failed" ] || { echo "rg-t1 has not finished yet (status: ${s:-running}); wait."; exit 1; }
    snap nautilus-it-cpu03.fullerton.edu
    kubectl apply -f jobs/rg-t2-noslr-jet-r1-p16-lat.yaml ;;
  card)
    kubectl apply -f rg-card.yaml ;;
  *) echo "usage: ./launch.sh phase1|t2|card"; exit 1 ;;
esac
kubectl -n $NS get pods -o wide | grep -E '^(NAME|rg-)'

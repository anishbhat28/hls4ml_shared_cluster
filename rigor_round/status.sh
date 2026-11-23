#!/bin/bash
# Quick look: which rg- jobs are running/done, on which node, and their current stage.
NS=hls4ml-nrp
kubectl -n $NS get pods -o wide | grep -E '^(NAME|rg-)'
for p in $(kubectl -n $NS get pods -o name | grep 'pod/rg-' | grep -v card); do
  echo "$p: $(kubectl -n $NS logs $p 2>/dev/null | grep -E '##### STAGE|RESULT' | tail -1)"
done

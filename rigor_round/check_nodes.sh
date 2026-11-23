#!/bin/bash
# Run on your Mac BEFORE launching. Shows whether the three pinned nodes exist, are schedulable,
# and how much CPU/memory is already requested on them.
for n in nautilus-it-gpu08.fullerton.edu chi-dgx-node02.csuchico.edu nautilus-it-cpu03.fullerton.edu; do
  echo "=================== $n"
  kubectl get node $n -o custom-columns=STATUS:.status.conditions[-1].type,UNSCHEDULABLE:.spec.unschedulable,TAINTS:.spec.taints[*].key 2>&1
  kubectl describe node $n 2>/dev/null | sed -n '/^Allocatable:/,/^System Info/p' | grep -E 'cpu|memory' | head -2
  kubectl describe node $n 2>/dev/null | sed -n '/Allocated resources/,/Events/p' | grep -E '^\s+(cpu|memory)'
done
echo
echo "Needed free: gpu08 32 CPU + 160Gi (4 builds at once); chi-dgx-node02 16 CPU + 80Gi (2 at once); cpu03 8 CPU + 40Gi."

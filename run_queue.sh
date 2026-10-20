#!/bin/bash
# Submit build jobs with at most N rw-* jobs active (pending or running) at once.
#   caffeinate -i ./run_queue.sh 4 job-rw-jet-*.yaml job-rw-big-r4-*.yaml
# Keep the Mac awake while it runs (caffeinate), or run it inside tmux/screen.
N=$1; shift
active() {
  kubectl -n hls4ml-nrp get jobs -o jsonpath='{range .items[*]}{.metadata.name} {.status.active}{"\n"}{end}' \
    | awk '$1 ~ /^rw-/ && $2 >= 1' | wc -l
}
for f in "$@"; do
  name=$(awk '/^  name:/{print $2; exit}' "$f")
  if kubectl -n hls4ml-nrp get job "$name" >/dev/null 2>&1; then echo "skip $name (exists)"; continue; fi
  while [ "$(active)" -ge "$N" ]; do sleep 300; done
  kubectl apply -f "$f" && echo "$(date '+%a %H:%M') started $name"
  sleep 30
done
echo "all submitted"

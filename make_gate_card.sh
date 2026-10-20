#!/usr/bin/env bash
# Make card-validation Jobs for the gate-round builds (rw-g-*) from the run-week card job.
#   ga: pinned to k8s-stratix-10-02 (run-week session A host)
#   gb: any other U55C host (run-week session B rule)
# Output: job-rw-card-ga.json, job-rw-card-gb.json. Run from ~/hls4ml-paper/runweek.
set -euo pipefail
SRC=job-rw-card.yaml
HOST_A=k8s-stratix-10-02.sdsc.optiputer.net
[ -f "$SRC" ] || { echo "run this in ~/hls4ml-paper/runweek ($SRC not found)"; exit 1; }
grep -q '/work/rw/builds/\*/' "$SRC" || { echo "loop line '/work/rw/builds/*/' not found in $SRC"; exit 1; }

for T in ga gb; do
  sed -e "s/__TAG__/$T/g" -e 's#/work/rw/builds/\*/#/work/rw/builds/rw-g-*/#g' "$SRC" > "/tmp/card-$T.yaml"
  grep -q '__TAG__' "/tmp/card-$T.yaml" && { echo "unreplaced __TAG__"; exit 1; }
  kubectl create --dry-run=client -o json -f "/tmp/card-$T.yaml" > "/tmp/card-$T.json"
done

HOST_A="$HOST_A" python3 - <<'PY'
import json, os
host = os.environ['HOST_A']
for tag, op in (('ga', 'In'), ('gb', 'NotIn')):
    j = json.load(open(f'/tmp/card-{tag}.json'))
    spec = j['spec']['template']['spec']
    spec['affinity'] = {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [
        {'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': op, 'values': [host]}]}]}}}
    c = spec['containers'][0]
    script = c['args'][0] if c.get('args') else ''
    assert '/work/rw/builds/rw-g-*/' in script, 'loop not restricted'
    assert f'card_results_{{TAG}}' in script or 'card_results_' in script
    tagenv = [e.get('value') for e in c.get('env', []) if e.get('name') == 'TAG']
    assert tagenv == [tag], f'TAG env is {tagenv}'
    assert tag in j['metadata']['name'], j['metadata']['name']
    out = f'job-rw-card-{tag}.json'
    json.dump(j, open(out, 'w'), indent=1)
    print(out, 'name=', j['metadata']['name'], 'TAG=', tag, 'affinity', op, host,
          'resources=', c.get('resources', {}).get('requests'))
PY

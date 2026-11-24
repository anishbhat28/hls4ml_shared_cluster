import csv, json, sys, glob, os
rows = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*', 'result.json'))):
    r = json.load(open(f))
    g = r.pop('gate', None) or {}
    gp = os.path.join(os.path.dirname(f), 'gate.json')
    if not g and os.path.exists(gp):
        g = json.load(open(gp))
    for k in ('verdict', 'dsp', 'lut', 'ff'):
        r[f'gate_{k}'] = g.get(k)
    rows.append(r)
keys = ['design', 'outcome', 'gate_verdict', 'gate_dsp', 'gate_lut', 'gate_ff', 'kernel_clock_mhz', 'bitexact_vs_csim',
        'hw_accuracy', 'keras_accuracy', 'test_hw_vs_keras_argmax_agree', 'max_abs_diff_vs_keras', 'inferences_per_s',
        'latency_1_us', 'load_s', 'node']
keys += [k for r in rows for k in r if k not in keys]
keys = list(dict.fromkeys(keys))
w = csv.DictWriter(sys.stdout, fieldnames=keys, lineterminator='\n')
w.writeheader(); w.writerows(rows)

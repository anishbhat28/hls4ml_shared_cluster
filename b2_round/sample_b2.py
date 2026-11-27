"""Draw batch 2 of the wa-hls4ml exemplar sample. Same frame and exclusions as sample_wa.py (batch 1);
the 12 batch-1 designs are excluded (decided before drawing); new seed. Deterministic.
usage: python3 sample_b2.py exemplar_models.json wa_sample.json   -> wa_sample_b2.json"""
import json, random, re, hashlib, sys
raw = open(sys.argv[1], 'rb').read(); d = json.loads(raw)
b1 = {o['name'] for o in json.load(open(sys.argv[2]))['sample']}
frame = {}
for s in d:
    fam = s['meta_data']['model_name'].split('_')[0]
    if any(l['class_name'] not in ('InputLayer', 'Dense', 'Activation') for l in s['model_config']):
        continue                                    # excludes Bipc (Add layers)
    m = s['hls_config']['Model']
    frame.setdefault((fam, m['Precision'].replace(' ', ''), int(m['ReuseFactor']), m['Strategy']), s)
def name(k):
    fam, prec, rf, strat = k; b = re.match(r'fixed<(\d+),(\d+)>', prec).groups()
    return f"wa-{fam.lower()}-r{rf}-p{b[0]}-{'lat' if strat == 'Latency' else 'res'}"
SEED = 20261126
rng = random.Random(SEED); fams = sorted({k[0] for k in frame}); pick = []
for f in fams:
    pick += rng.sample(sorted(k for k in frame if k[0] == f and name(k) not in b1), 2)
out = []
for k in pick:
    s = frame[k]; fam, prec, rf, strat = k; b = re.match(r'fixed<(\d+),(\d+)>', prec).groups()
    out.append({'name': name(k), 'family': fam, 'precision': f'ap_fixed<{b[0]},{b[1]}>', 'reuse_factor': rf, 'strategy': strat,
                'n_in': s['model_config'][0]['input_shape'][0][1],
                'layers': [{'class': l['class_name'], 'units': l.get('neurons'), 'activation': l.get('activation'),
                            'use_bias': l.get('use_bias', True)} for l in s['model_config'][1:]],
                'params': sum(l.get('parameters', 0) for l in s['model_config']),
                'wa_uuid': s['meta_data']['uuid'], 'wa_model_name': s['meta_data']['model_name']})
json.dump({'seed': SEED, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'frame_size': len(frame),
           'excluded': 'Bipc (residual Add layers); the 12 batch-1 designs', 'families': fams, 'sample': out},
          open('wa_sample_b2.json', 'w'), indent=1)
for o in out: print(o['name'])

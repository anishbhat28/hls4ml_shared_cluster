"""Draw the wa-hls4ml exemplar sample for the shared-cluster paper. Deterministic: run it again to get the same list.
Frame: the wa-hls4ml exemplar test set (887 samples, 7 scientific models). The part/clock/Vivado-version replicas are
irrelevant here (every design is rebuilt for the U55C with VitisUnified at 3.333 ns), so the frame is the distinct
(model, precision, reuse factor, strategy) combinations.
Exclusion (decided before drawing): models whose topology is not sequential (Bipc: residual Add layers whose inputs
cannot be recovered from the flat layer list). No other exclusion: designs that do not fit the SLR or never finish HLS
are outcomes, not exclusions.
Design: stratified, 2 configurations per remaining model, drawn uniformly without replacement, seed below.
"""
import json, random, re, sys, hashlib
SEED = 20261124
src = sys.argv[1]
raw = open(src, 'rb').read()
d = json.loads(raw)
frame = {}
for s in d:
    fam = s['meta_data']['model_name'].split('_')[0]
    if any(l['class_name'] not in ('InputLayer', 'Dense', 'Activation') for l in s['model_config']):
        continue                                    # excludes Bipc (Add layers)
    m = s['hls_config']['Model']
    key = (fam, m['Precision'].replace(' ', ''), int(m['ReuseFactor']), m['Strategy'])
    frame.setdefault(key, s)                        # one representative per combination (architecture identical)
fams = sorted({k[0] for k in frame})
rng = random.Random(SEED)
pick = []
for f in fams:
    keys = sorted(k for k in frame if k[0] == f)
    pick += rng.sample(keys, 2)
out = []
for fam, prec, rf, strat in pick:
    s = frame[(fam, prec, rf, strat)]
    layers = [{'class': l['class_name'], 'units': l.get('neurons'), 'activation': l.get('activation'),
               'use_bias': l.get('use_bias', True)} for l in s['model_config'][1:]]
    bits = re.match(r'fixed<(\d+),(\d+)>', prec).groups()
    name = f"wa-{fam.lower()}-r{rf}-p{bits[0]}-{'lat' if strat == 'Latency' else 'res'}"
    out.append({'name': name, 'family': fam, 'precision': f'ap_fixed<{bits[0]},{bits[1]}>', 'reuse_factor': rf,
                'strategy': strat, 'n_in': s['model_config'][0]['input_shape'][0][1], 'layers': layers,
                'params': sum(l.get('parameters', 0) for l in s['model_config']),
                'wa_uuid': s['meta_data']['uuid'], 'wa_model_name': s['meta_data']['model_name']})
json.dump({'seed': SEED, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'frame_size': len(frame),
           'families': fams, 'excluded_families': ['Bipc'], 'sample': out}, open('wa_sample.json', 'w'), indent=1)
print(f"frame {len(frame)} combinations in {len(fams)} models; sha256 {hashlib.sha256(raw).hexdigest()[:16]}…")
for o in out:
    print(f"{o['name']:28s} in={o['n_in']:4d} params={o['params']:5d} {o['precision']:15s} RF={o['reuse_factor']:<5d} {o['strategy']}")

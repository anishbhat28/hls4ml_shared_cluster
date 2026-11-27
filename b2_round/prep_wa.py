"""Build the sampled wa-hls4ml models (fixed-seed random weights) and their inputs into /work/wa. Runs in job-wa-prep."""
import json, os, sys, hashlib
import numpy as np, keras

S = json.load(open(sys.argv[1]))
root = sys.argv[2] if len(sys.argv) > 2 else '/work/wa'
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
man = {'seed': S['seed'], 'keras': keras.__version__, 'designs': {}}
for i, d in enumerate(S['sample']):
    seed = S['seed'] + i
    keras.utils.set_random_seed(seed)
    layers, k = [keras.Input((d['n_in'],))], 0
    for l in d['layers']:
        if l['class'] == 'Dense':
            layers.append(keras.layers.Dense(
                l['units'], use_bias=l['use_bias'],
                kernel_initializer=keras.initializers.GlorotUniform(seed=seed * 100 + k),
                bias_initializer=keras.initializers.RandomNormal(0.0, 0.1, seed=seed * 100 + 50 + k)))
            k += 1
        elif l['class'] == 'Activation':
            layers.append(keras.layers.Activation(l['activation']))
        else:
            raise ValueError(l)
    m = keras.Sequential(layers, name=d['name'].replace('-', '_'))
    os.makedirs(f"{root}/models", exist_ok=True)
    mp = f"{root}/models/{d['name']}.h5"
    m.save(mp)
    rng = np.random.default_rng(seed)
    n = d['n_in']
    X_test = rng.normal(0.0, 1.0, (2000, n)).astype(np.float32)
    special = np.array([np.inf, -np.inf, np.nan], dtype=np.float32)
    X_stress = np.concatenate([
        np.zeros((10, n), np.float32),                                   # all zero
        (rng.normal(0.0, 1.0, (400, n)) * 50).astype(np.float32),        # far outside the fixed-point range
        rng.uniform(-1000, 1000, (80, n)).astype(np.float32),            # very large values
        np.repeat(special, 10).reshape(30, 1) * np.ones((30, n), np.float32),   # +Inf / -Inf / NaN rows
    ])
    dd = f"{root}/data/{d['name']}"
    os.makedirs(dd, exist_ok=True)
    np.save(f"{dd}/X_test.npy", X_test); np.save(f"{dd}/X_stress.npy", X_stress)
    man['designs'][d['name']] = {'seed': seed, 'model_sha256': sha(mp), 'x_test_sha256': sha(f"{dd}/X_test.npy"),
                                 'x_stress_sha256': sha(f"{dd}/X_stress.npy"), 'params': int(m.count_params()),
                                 'params_wa': d['params']}
    print(d['name'], m.count_params(), 'params (wa-hls4ml:', d['params'], ')')
json.dump(man, open(f"{root}/manifest.json", 'w'), indent=1)
print('wrote', root)

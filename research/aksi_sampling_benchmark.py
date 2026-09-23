import numpy as np

RNG = np.random.default_rng(42)

def make_trace(T=1000, dims=4):
    x = np.zeros((T, dims))
    n_changes = RNG.integers(8, 25)
    points = sorted(RNG.choice(np.arange(20, T-20), size=n_changes, replace=False))
    state = np.zeros(dims)
    cur = 0
    for p in points + [T]:
        state = state + RNG.normal(0, 1, dims)
        x[cur:p] = state
        cur = p
    x += RNG.normal(0, 0.03, x.shape)
    x[:, 0] += np.cumsum(RNG.normal(0, 0.01, T))
    return x

def uniform_sample(x, k):
    return np.unique(np.linspace(0, len(x)-1, k).round().astype(int))

def adaptive_sample(x, threshold=0.4):
    sm = np.vstack([x[0], (x[:-2] + x[1:-1] + x[2:]) / 3, x[-1]])
    delta = np.linalg.norm(np.diff(sm, axis=0), axis=1)
    idx = [0]
    idx.extend(i for i, v in enumerate(delta, start=1) if v >= threshold)
    idx.append(len(x)-1)
    return np.unique(idx)

def reconstruct(x, idx):
    grid = np.arange(len(x))
    return np.column_stack([
        np.interp(grid, idx, x[idx, d]) for d in range(x.shape[1])
    ])

def rmse(a, b):
    return float(np.sqrt(np.mean((a-b)**2)))

uniform_errors, adaptive_errors, adaptive_counts = [], [], []
for _ in range(500):
    x = make_trace()
    iu = uniform_sample(x, 40)
    ia = adaptive_sample(x, 0.4)
    uniform_errors.append(rmse(x, reconstruct(x, iu)))
    adaptive_errors.append(rmse(x, reconstruct(x, ia)))
    adaptive_counts.append(len(ia))

print("uniform_mean_rmse", np.mean(uniform_errors))
print("adaptive_mean_rmse", np.mean(adaptive_errors))
print("adaptive_mean_samples", np.mean(adaptive_counts))
print("adaptive_beats_uniform", np.mean(np.array(adaptive_errors) < np.array(uniform_errors)))

"""
Apples-to-apples representation benchmark on the hex8 atlas.
Trains 6 methods on the SAME frozen X.npy (1191x739), each -> 256-d, and runs
every one through the SAME frozen eval_harness. Adds corruption-robustness,
2-seed stability (Procrustes), and CKA vs the shipped e1.

Methods: PCA · AE · VAE · MAE(denoising) · Contrastive(SCARF+view-mask InfoNCE)
         · Hybrid(PCA-160 + contrastive-96)   [+ shipped e1 as a reference row]
Output: embedding/benchmark_results.json
"""
import json, time
from pathlib import Path
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from sklearn.decomposition import PCA
from scipy.spatial.distance import cdist

HERE = Path(__file__).parent
torch.set_num_threads(8)
from eval_harness import evaluate, procrustes_corr

X = np.load(HERE / "X.npy").astype(np.float32)
n, d = X.shape
DIM = 256
Xt = torch.tensor(X)
meta = json.load(open(HERE / "meta.json"))
views = meta["views"]
vgroups = {}
for i, c in enumerate(meta["cols"]):
    vgroups.setdefault(views[c], []).append(i)
MASKABLE = [v for v in ("WHO", "WHAT", "FLOW", "PRICE", "WHERE") if v in vgroups]
SEEDS = [0, 1]
print(f"X {X.shape} -> {DIM}d | views {meta['view_counts']}", flush=True)


def enc_mlp(dim, hidden=512, p=0.1):
    return nn.Sequential(nn.Linear(d, hidden), nn.LayerNorm(hidden), nn.GELU(),
                         nn.Dropout(p), nn.Linear(hidden, dim))


# ---------------- trainers: each returns (Z[n,DIM], encode_fn(Xnp)->Z) ----------------
def train_pca(seed):
    pca = PCA(n_components=DIM, random_state=seed).fit(X)
    return pca.transform(X).astype(np.float32), lambda A: pca.transform(A).astype(np.float32)


def _torch_train(seed, step_fn, epochs, lr=1e-3, batch=256, extra=None):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    enc = enc_mlp(DIM); dec = nn.Sequential(nn.Linear(DIM, 512), nn.GELU(), nn.Linear(512, d))
    mods = nn.ModuleList([enc, dec]);
    if extra is not None: mods.append(extra)
    opt = torch.optim.AdamW(mods.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    for ep in range(epochs):
        perm = torch.randperm(n)
        for s in range(0, n, batch):
            idx = perm[s:s + batch]; x = Xt[idx]
            loss = step_fn(x, idx, enc, dec, extra, rng)
            opt.zero_grad(); loss.backward(); opt.step()
        sched.step()
    enc.eval()
    with torch.no_grad():
        encode = lambda A: enc(torch.tensor(np.asarray(A, np.float32))).detach().numpy()
        return enc(Xt).detach().numpy().astype(np.float32), encode


def train_ae(seed):
    def step(x, idx, enc, dec, extra, rng):
        return F.mse_loss(dec(enc(x)), x)
    return _torch_train(seed, step, epochs=400)


def train_vae(seed, beta=0.001):
    mu = nn.Linear(DIM, DIM); lv = nn.Linear(DIM, DIM)
    head = nn.ModuleList([mu, lv])
    def step(x, idx, enc, dec, extra, rng):
        h = enc(x); m, v = extra[0](h), extra[1](h)
        z = m + torch.randn_like(m) * torch.exp(0.5 * v)
        kl = -0.5 * torch.mean(1 + v - m.pow(2) - v.exp())
        return F.mse_loss(dec(z), x) + beta * kl
    return _torch_train(seed, step, epochs=400, extra=head)


def train_mae(seed, mask=0.3):
    def step(x, idx, enc, dec, extra, rng):
        m = torch.tensor(rng.random(x.shape) < mask)
        xm = torch.where(m, torch.zeros_like(x), x)   # mask -> 0
        return F.mse_loss(dec(enc(xm)), x)            # reconstruct FULL from masked
    return _torch_train(seed, step, epochs=400)


def train_contrastive(seed, mask=0.3, tau=0.5, vmp=0.5, lam=1.0, dim=DIM, epochs=700):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    enc = enc_mlp(dim); proj = nn.Linear(dim, 128); dec = nn.Sequential(nn.Linear(dim, 512), nn.GELU(), nn.Linear(512, d))
    mods = nn.ModuleList([enc, proj, dec])
    opt = torch.optim.AdamW(mods.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    def nce(p1, p2):
        lg = p1 @ p2.T / tau; lb = torch.arange(len(p1))
        return 0.5 * (F.cross_entropy(lg, lb) + F.cross_entropy(lg.T, lb))
    for ep in range(epochs):
        perm = torch.randperm(n)
        for s in range(0, n, 256):
            idx = perm[s:s + 256]; x = Xt[idx]
            m = torch.tensor(rng.random((len(idx), d)) < mask)
            donor = Xt[torch.randint(0, n, (len(idx),))]
            xc = torch.where(m, donor, x)
            if rng.random() < vmp:
                v = MASKABLE[rng.integers(len(MASKABLE))]
                xc[:, vgroups[v]] = 0.0; m[:, vgroups[v]] = True
            p1 = F.normalize(proj(enc(x)), dim=-1)
            zc = enc(xc); p2 = F.normalize(proj(zc), dim=-1)
            loss = nce(p1, p2) + lam * F.mse_loss(dec(zc)[m], x[m])
            opt.zero_grad(); loss.backward(); opt.step()
        sched.step()
    enc.eval()
    with torch.no_grad():
        encode = lambda A: enc(torch.tensor(np.asarray(A, np.float32))).detach().numpy()
        return enc(Xt).detach().numpy().astype(np.float32), encode


def train_hybrid(seed):
    pca160 = PCA(n_components=160, random_state=seed).fit(X)
    Zc, enc_c = train_contrastive(seed, dim=256, epochs=700)
    pca96 = PCA(n_components=96, random_state=seed).fit(Zc)
    def encode(A):
        a = np.asarray(A, np.float32)
        return np.concatenate([pca160.transform(a), pca96.transform(enc_c(a))], 1).astype(np.float32)
    Z = np.concatenate([pca160.transform(X), pca96.transform(Zc)], 1).astype(np.float32)
    return Z, encode


# ---------------- extra metrics ----------------
def corrupt(seed=7, frac=0.3):
    rng = np.random.default_rng(seed); Xc = X.copy()
    m = rng.random(X.shape) < frac
    donor = X[rng.integers(0, n, n)]
    Xc[m] = donor[m]; return Xc

def nn_overlap(Za, Zb, k=10):
    Da = cdist(Za, Za); np.fill_diagonal(Da, np.inf)
    Db = cdist(Zb, Zb); np.fill_diagonal(Db, np.inf)
    na = np.argsort(Da, 1)[:, :k]; nb = np.argsort(Db, 1)[:, :k]
    return float(np.mean([len(set(a) & set(b)) / k for a, b in zip(na, nb)]))

def robustness(encode_fn, Z_clean):
    return nn_overlap(Z_clean, encode_fn(corrupt()))

def cka(A, B):
    A = A - A.mean(0); B = B - B.mean(0)
    return float(np.linalg.norm(A.T @ B) ** 2 /
                 (np.linalg.norm(A.T @ A) * np.linalg.norm(B.T @ B) + 1e-12))


# ---------------- run ----------------
TRAINERS = {"PCA": train_pca, "AE": train_ae, "VAE": train_vae,
            "MAE": train_mae, "Contrastive": train_contrastive, "Hybrid": train_hybrid}

# shipped e1 reference (aligned to labels order)
import pandas as pd
lab = pd.read_parquet(HERE / "labels.parquet")
e1p = pd.read_parquet(HERE.parent / "hex/hex8_embedding_plexis_e1_256d.parquet").set_index("hex8_id")
e1_ship = e1p.reindex(lab["hex8_id"]).to_numpy(np.float32)

results = {}
t0 = time.time()
for name, fn in TRAINERS.items():
    ts = time.time()
    Zs = {}
    for sd in SEEDS:
        Zs[sd] = fn(sd)
    Z0, enc0 = Zs[0]; Z1, _ = Zs[1]
    ev = evaluate(Z0, fast=False, X_raw=X)
    ev["stability_procrustes"] = procrustes_corr(Z0, Z1)
    ev["corruption_robust"] = robustness(enc0, Z0)
    ev["cka_vs_shipped_e1"] = cka(Z0, e1_ship)
    results[name] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in ev.items()}
    print(f"[{name}] {round(time.time()-ts)}s  twin={ev['twin_hitrate']} od={ev['probe_od_r2']:.3f} "
          f"adq={ev['probe_adq_r2']:.3f} robust={ev['corruption_robust']:.3f} "
          f"stab={ev['stability_procrustes']:.3f} negctrl={ev['negctrl_r2']:.3f}", flush=True)

# shipped e1 row (no retrain; stability from its frozen eval)
ev = evaluate(e1_ship, fast=False, X_raw=X)
ev["stability_procrustes"] = 0.987   # from eval_final_plexis_e1.json
ev["corruption_robust"] = None       # encoder not reloaded here
ev["cka_vs_shipped_e1"] = 1.0
results["e1 (shipped)"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in ev.items()}

out = {"generated_s": round(time.time() - t0), "n": n, "d": d, "dim": DIM,
       "seeds": SEEDS, "methods": results}
json.dump(out, open(HERE / "benchmark_results.json", "w"), indent=1)
print(f"\nDONE in {out['generated_s']}s -> embedding/benchmark_results.json", flush=True)

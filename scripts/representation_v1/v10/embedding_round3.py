#!/usr/bin/env python3
"""
Embedding Round 3 — XGBoost-derived + modern alternatives
Run on server.

Methods:
  1. XGBoost leaf embedding + PCA-64 (NEW) — XGBoost finds splits, PCA compresses
  2. XGBoost prediction distillation + encoder-64 (NEW) — neural encoder mimics XGBoost
  3. XGBoost predictions as direct embedding (24-dim) — simplest
  4. Barlow Twins self-supervised (NEW)
  5. VAE-64 (NEW)

All evaluated identically to previous rounds: kNN PA, Cat R², AMI,
structural twins. Compared to existing GCN-64 and PCA-128 baselines.
"""
import numpy as np
import pandas as pd
import json, os, time, warnings
warnings.filterwarnings("ignore")

from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_mutual_info_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = "/home/azureuser/digital-atlas-sgp"
HEX_RAW = f"{ROOT}/data/hex_v10/hex_features_v10.parquet"
HEX_NORM = f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet"
OUT_DIR = f"{ROOT}/data/hex_v10/embeddings"
os.makedirs(OUT_DIR, exist_ok=True)

SEED = 42
EMBED_DIM = 64

ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
BK_COLS = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

def load_data():
    log("Loading data...")
    raw = pd.read_parquet(HEX_RAW)
    norm = pd.read_parquet(HEX_NORM)
    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]
    X = norm[feat_cols].to_numpy(dtype=np.float32)
    stds = X.std(axis=0); keep = stds > 1e-9; X = X[:, keep]
    cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and c not in {"pc_cat_hhi","pc_cat_entropy"}])
    Y = raw[cat_cols].to_numpy(dtype=np.float32)
    pas = raw["parent_pa"].to_numpy(dtype=str)
    hex_ids = raw["hex_id"].to_numpy(dtype=str)
    active = raw["pc_total"].to_numpy() > 0
    idx = np.arange(len(X))
    tr, te = train_test_split(idx, test_size=0.2, random_state=SEED)
    tr, vl = train_test_split(tr, test_size=0.125, random_state=SEED)
    return {"X": X, "Y": Y, "cat_cols": cat_cols, "pas": pas, "hex_ids": hex_ids,
            "active": active, "tr": tr, "vl": vl, "te": te, "raw": raw}

def evaluate(Z, data, name):
    pas, active, Y = data["pas"], data["active"], data["Y"]
    tr, te = data["tr"], data["te"]
    r = {"method": name, "dims": Z.shape[1]}
    # kNN
    Za = Z[active]; pa_a = pas[active]
    n = np.linalg.norm(Za, axis=1, keepdims=True); n[n<1e-9]=1; Zn = Za/n
    sims = Zn @ Zn.T; np.fill_diagonal(sims, -1)
    c = t = 0
    for i in range(len(Za)):
        top5 = np.argsort(-sims[i])[:5]
        c += sum(1 for j in top5 if pa_a[j] == pa_a[i]); t += 5
    r["knn_pa"] = round(c/t, 4)
    # Cat R²
    r2s = []
    for j in range(Y.shape[1]):
        m = Ridge(alpha=1.0).fit(Z[tr], Y[tr, j])
        p = m.predict(Z[te]); y = Y[te, j]
        ss_res = ((y-p)**2).sum(); ss_tot = ((y-y.mean())**2).sum()
        r2s.append(1 - ss_res/(ss_tot+1e-9))
    r["cat_r2"] = round(float(np.mean(r2s)), 4)
    # AMI
    km = KMeans(8, random_state=SEED, n_init=10).fit(Z[active])
    pu = list(set(pa_a)); pn = np.array([pu.index(p) for p in pa_a])
    r["ami"] = round(float(adjusted_mutual_info_score(pn, km.labels_)), 4)
    return r


# =====================================================================
# 1. XGBoost LEAF EMBEDDING + PCA
# =====================================================================
def method_xgb_leaves(data):
    log("\n=== XGBoost leaf embedding + PCA-64 ===")
    X = data["X"]; Y = data["Y"]; tr = data["tr"]
    n_cats = Y.shape[1]

    # Train XGBoost per category on TRAIN set to avoid leakage
    all_leaves = []
    for j in range(n_cats):
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1,
                              subsample=0.8, random_state=SEED, n_jobs=-1, verbosity=0)
        model.fit(X[tr], np.log1p(Y[tr, j]))
        # apply() returns leaf index for each sample for each tree → [n, n_estimators]
        leaves = model.apply(X)  # shape [n_samples, n_trees]
        all_leaves.append(leaves)

    # Stack leaf indices: [n_samples, n_cats * n_trees] = [7318, 2400]
    leaf_matrix = np.hstack(all_leaves).astype(np.float32)
    log(f"  leaf matrix: {leaf_matrix.shape}")

    # Standardize then PCA-64
    # (treat leaf indices as ordinal features; PCA on them finds dense projections)
    leaf_matrix = (leaf_matrix - leaf_matrix.mean(axis=0)) / (leaf_matrix.std(axis=0) + 1e-9)
    Z = PCA(n_components=EMBED_DIM, random_state=SEED).fit_transform(leaf_matrix)
    log(f"  embedding: {Z.shape}")

    r = evaluate(Z, data, "xgb_leaves_pca_64")
    pd.DataFrame(Z, columns=[f"x{i}" for i in range(EMBED_DIM)]).to_parquet(
        f"{OUT_DIR}/xgb_leaves_pca_64.parquet", index=False)
    return Z, r


# =====================================================================
# 2. XGBoost PREDICTION DISTILLATION → NEURAL ENCODER (64-dim)
# =====================================================================
class DistillEncoder(nn.Module):
    def __init__(self, in_dim, embed_dim=64, out_dim=24):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(in_dim, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(),
            nn.Linear(64, embed_dim),
        )
        self.dec = nn.Sequential(
            nn.Linear(embed_dim, 64), nn.ReLU(),
            nn.Linear(64, out_dim),
        )
    def forward(self, x):
        z = self.enc(x)
        y = self.dec(z)
        return y, z

def method_xgb_distillation(data):
    log("\n=== XGBoost distillation → Encoder-64 ===")
    X = data["X"]; Y = data["Y"]; tr = data["tr"]

    # First: train XGBoost per category, collect predictions for ALL samples
    log("  Training XGBoost teacher...")
    n_cats = Y.shape[1]
    preds = np.zeros_like(Y)
    for j in range(n_cats):
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1,
                              subsample=0.8, random_state=SEED, n_jobs=-1, verbosity=0)
        model.fit(X[tr], np.log1p(Y[tr, j]))
        preds[:, j] = model.predict(X)  # log-scale predictions

    # Train neural encoder to map X → XGBoost predictions (supervised by XGBoost's outputs)
    log("  Distilling into 64-dim encoder...")
    model = DistillEncoder(X.shape[1], EMBED_DIM, n_cats)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=10, factor=0.5)

    X_t = torch.tensor(X, dtype=torch.float32)
    Y_t = torch.tensor(preds, dtype=torch.float32)  # XGBoost predictions as targets
    ds = TensorDataset(X_t[tr], Y_t[tr])
    dl = DataLoader(ds, batch_size=256, shuffle=True)
    Xv = X_t[data["vl"]]; Yv = Y_t[data["vl"]]

    best_vl = float("inf"); wait = 0; best_st = None
    for ep in range(200):
        model.train()
        for xb, yb in dl:
            y_pred, _ = model(xb)
            loss = nn.MSELoss()(y_pred, yb)
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            vl_pred, _ = model(Xv)
            vl_loss = nn.MSELoss()(vl_pred, Yv).item()
        sch.step(vl_loss)
        if vl_loss < best_vl:
            best_vl = vl_loss; wait = 0
            best_st = {k:v.clone() for k,v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= 30: break
    model.load_state_dict(best_st)
    model.eval()
    with torch.no_grad():
        _, Z = model(X_t)
        Z = Z.numpy()

    r = evaluate(Z, data, "xgb_distill_64")
    pd.DataFrame(Z, columns=[f"x{i}" for i in range(EMBED_DIM)]).to_parquet(
        f"{OUT_DIR}/xgb_distill_64.parquet", index=False)
    return Z, r


# =====================================================================
# 3. XGBoost PREDICTIONS as direct embedding (24-dim)
# =====================================================================
def method_xgb_preds(data):
    log("\n=== XGBoost predictions as direct embedding (24-dim) ===")
    X = data["X"]; Y = data["Y"]; tr = data["tr"]
    n_cats = Y.shape[1]
    Z = np.zeros_like(Y, dtype=np.float32)
    for j in range(n_cats):
        model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1,
                              subsample=0.8, random_state=SEED, n_jobs=-1, verbosity=0)
        model.fit(X[tr], np.log1p(Y[tr, j]))
        Z[:, j] = model.predict(X)
    r = evaluate(Z, data, "xgb_preds_24")
    pd.DataFrame(Z, columns=[f"x{i}" for i in range(n_cats)]).to_parquet(
        f"{OUT_DIR}/xgb_preds_24.parquet", index=False)
    return Z, r


# =====================================================================
# 4. BARLOW TWINS SELF-SUPERVISED (NEW)
# =====================================================================
class BarlowEncoder(nn.Module):
    def __init__(self, in_dim, embed_dim=64):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(in_dim, 256), nn.BatchNorm1d(256), nn.ReLU(),
            nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(),
            nn.Linear(128, embed_dim),
        )
        self.proj = nn.Sequential(
            nn.Linear(embed_dim, 128), nn.BatchNorm1d(128), nn.ReLU(),
            nn.Linear(128, embed_dim),
        )
    def forward(self, x):
        z = self.enc(x)
        p = self.proj(z)
        return z, p

def barlow_loss(p1, p2, lambda_off=5e-3):
    # batch-norm style
    n, d = p1.shape
    p1_n = (p1 - p1.mean(0)) / (p1.std(0) + 1e-9)
    p2_n = (p2 - p2.mean(0)) / (p2.std(0) + 1e-9)
    C = (p1_n.T @ p2_n) / n
    on_diag = ((torch.diagonal(C) - 1) ** 2).sum()
    off_diag = (C ** 2).sum() - (torch.diagonal(C) ** 2).sum()
    return on_diag + lambda_off * off_diag

def method_barlow(data):
    log("\n=== Barlow Twins self-supervised ===")
    X = data["X"]; tr = data["tr"]
    model = BarlowEncoder(X.shape[1], EMBED_DIM)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    X_t = torch.tensor(X, dtype=torch.float32)
    ds = TensorDataset(X_t[tr]); dl = DataLoader(ds, batch_size=256, shuffle=True)

    def augment(b):
        # noise + feature dropout
        v1 = b + torch.randn_like(b) * 0.1
        v1 = v1 * (torch.rand_like(b) > 0.15).float()
        v2 = b + torch.randn_like(b) * 0.1
        v2 = v2 * (torch.rand_like(b) > 0.15).float()
        return v1, v2

    for ep in range(100):
        model.train()
        tot = 0; nb = 0
        for (b,) in dl:
            v1, v2 = augment(b)
            _, p1 = model(v1); _, p2 = model(v2)
            loss = barlow_loss(p1, p2)
            opt.zero_grad(); loss.backward(); opt.step()
            tot += loss.item(); nb += 1
        if ep % 20 == 0:
            log(f"  Epoch {ep}: loss={tot/nb:.4f}")

    model.eval()
    with torch.no_grad():
        Z, _ = model(X_t); Z = Z.numpy()
    r = evaluate(Z, data, "barlow_64")
    pd.DataFrame(Z, columns=[f"b{i}" for i in range(EMBED_DIM)]).to_parquet(
        f"{OUT_DIR}/barlow_64.parquet", index=False)
    return Z, r


# =====================================================================
# 5. VAE-64
# =====================================================================
class VAE(nn.Module):
    def __init__(self, in_dim, embed_dim=64):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(in_dim, 128), nn.BatchNorm1d(128), nn.ReLU(),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(),
        )
        self.mu = nn.Linear(64, embed_dim)
        self.logvar = nn.Linear(64, embed_dim)
        self.dec = nn.Sequential(
            nn.Linear(embed_dim, 64), nn.BatchNorm1d(64), nn.ReLU(),
            nn.Linear(64, 128), nn.BatchNorm1d(128), nn.ReLU(),
            nn.Linear(128, in_dim),
        )
    def encode(self, x):
        h = self.enc(x); return self.mu(h), self.logvar(h)
    def forward(self, x):
        mu, logvar = self.encode(x)
        std = torch.exp(0.5 * logvar)
        z = mu + std * torch.randn_like(std)
        return self.dec(z), mu, logvar, z

def method_vae(data):
    log("\n=== VAE-64 ===")
    X = data["X"]; tr = data["tr"]
    model = VAE(X.shape[1], EMBED_DIM)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    X_t = torch.tensor(X, dtype=torch.float32)
    ds = TensorDataset(X_t[tr]); dl = DataLoader(ds, batch_size=256, shuffle=True)
    Xv = X_t[data["vl"]]

    best_vl = float("inf"); wait = 0; best_st = None
    for ep in range(200):
        model.train()
        for (b,) in dl:
            recon, mu, logvar, z = model(b)
            rec_loss = nn.MSELoss(reduction="sum")(recon, b) / b.size(0)
            kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp()) / b.size(0)
            loss = rec_loss + 0.001 * kl
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            r2, m2, l2, _ = model(Xv)
            vl = nn.MSELoss(reduction="sum")(r2, Xv).item() / Xv.size(0)
        if vl < best_vl:
            best_vl = vl; wait = 0
            best_st = {k:v.clone() for k,v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= 30: break

    model.load_state_dict(best_st)
    model.eval()
    with torch.no_grad():
        mu, _ = model.encode(X_t); Z = mu.numpy()
    r = evaluate(Z, data, "vae_64")
    pd.DataFrame(Z, columns=[f"v{i}" for i in range(EMBED_DIM)]).to_parquet(
        f"{OUT_DIR}/vae_64.parquet", index=False)
    return Z, r


# =====================================================================
# MAIN
# =====================================================================
def main():
    t0 = time.time()
    log("="*60)
    log("EMBEDDING ROUND 3 — XGBoost + modern alternatives")
    log("="*60)
    data = load_data()

    results = []
    _, r1 = method_xgb_leaves(data); results.append(r1)
    log(f"  → kNN={r1['knn_pa']}, CatR²={r1['cat_r2']}, AMI={r1['ami']}")
    _, r2 = method_xgb_distillation(data); results.append(r2)
    log(f"  → kNN={r2['knn_pa']}, CatR²={r2['cat_r2']}, AMI={r2['ami']}")
    _, r3 = method_xgb_preds(data); results.append(r3)
    log(f"  → kNN={r3['knn_pa']}, CatR²={r3['cat_r2']}, AMI={r3['ami']}")
    _, r4 = method_barlow(data); results.append(r4)
    log(f"  → kNN={r4['knn_pa']}, CatR²={r4['cat_r2']}, AMI={r4['ami']}")
    _, r5 = method_vae(data); results.append(r5)
    log(f"  → kNN={r5['knn_pa']}, CatR²={r5['cat_r2']}, AMI={r5['ami']}")

    log("\n" + "="*70)
    log(f"{'Method':<25} {'Dims':>5} {'kNN PA':>8} {'Cat R²':>8} {'AMI':>6}")
    log("-"*70)
    # Previous results for context
    priors = [
        ("raw_features", 460, 0.374, 0.896, 0.225),
        ("gcn_masked_64", 64, 0.430, 0.649, None),
        ("pca_128", 128, 0.359, 0.746, 0.265),
        ("pca_64", 64, 0.349, 0.690, 0.265),
        ("contrastive_64", 64, 0.340, 0.520, 0.222),
        ("ae_64", 64, 0.314, 0.579, 0.192),
    ]
    for name, dims, knn, cat, ami in priors:
        ami_str = f"{ami:.3f}" if ami else "—"
        log(f"  {name:<23} {dims:>5} {knn:>8.3f} {cat:>8.3f} {ami_str:>6}")
    log("  " + "-"*67)
    for r in sorted(results, key=lambda x: -x["knn_pa"]):
        log(f"  {r['method']:<23} {r['dims']:>5} {r['knn_pa']:>8.3f} {r['cat_r2']:>8.3f} {r['ami']:>6.3f}")

    with open(f"{ROOT}/data/hex_v10/embedding_round3.json", "w") as f:
        json.dump(results, f, indent=2)
    log(f"\nTotal time: {time.time()-t0:.0f}s")

if __name__ == "__main__":
    main()

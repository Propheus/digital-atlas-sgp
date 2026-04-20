#!/usr/bin/env python3
"""
Build three non-GCN baselines as fixed 64-d embeddings:

  1. Node2Vec-64   — random walks on influence graph + skip-gram (graph-only, no features)
  2. UMAP-64       — nonlinear manifold learning on 391 raw features (features-only)
  3. Transformer-64 — masked-feature modeling with self-attention (features-only, attention-based)

Each saved to data/hex_v10/baselines/{method}_64.parquet
for the continuous engine to load as fixed baselines.
"""
import os, sys, time, random

import numpy as np
import pandas as pd
import scipy.sparse as sp
import torch
import torch.nn as nn

ROOT = "/home/azureuser/digital-atlas-sgp"
OUT = f"{ROOT}/data/hex_v10/baselines"
os.makedirs(OUT, exist_ok=True)

SEED = 42


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ============================================================
# Shared data loader
# ============================================================
def load():
    raw = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
    norm = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet")
    adj = sp.load_npz(f"{ROOT}/data/hex_v10/hex_influence_graph.npz").tocsr()
    ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
    BK = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}
    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK]
    X = norm[feat_cols].to_numpy(np.float32)
    # drop zero-std columns
    keep = X.std(axis=0) > 1e-9
    X = X[:, keep]
    return raw, X, adj


# ============================================================
# 1. NODE2VEC — graph random walks + skip-gram
# ============================================================
def build_node2vec(raw, adj, dim=64, walk_len=80, n_walks=10, window=10, epochs=5):
    log("=" * 60)
    log("BUILDING NODE2VEC-64")
    log("=" * 60)
    from gensim.models import Word2Vec

    n = adj.shape[0]
    neighbors = [adj[i].indices.tolist() for i in range(n)]
    rng = random.Random(SEED)

    log(f"  Generating {n_walks} walks of length {walk_len} per node ({n} nodes)...")
    walks = []
    for r in range(n_walks):
        nodes = list(range(n))
        rng.shuffle(nodes)
        for i in nodes:
            walk = [str(i)]
            cur = i
            for _ in range(walk_len - 1):
                nbrs = neighbors[cur]
                if not nbrs:
                    break
                cur = rng.choice(nbrs)
                walk.append(str(cur))
            walks.append(walk)
    log(f"  Generated {len(walks)} walks")

    log(f"  Training skip-gram (dim={dim}, window={window}, epochs={epochs})...")
    model = Word2Vec(walks, vector_size=dim, window=window, min_count=0, sg=1,
                     workers=4, epochs=epochs, seed=SEED)

    Z = np.zeros((n, dim), dtype=np.float32)
    for i in range(n):
        if str(i) in model.wv:
            Z[i] = model.wv[str(i)]

    df = pd.DataFrame(Z, columns=[f"n{i}" for i in range(dim)])
    df.insert(0, "hex_id", raw["hex_id"].values)
    out = f"{OUT}/node2vec_64.parquet"
    df.to_parquet(out, index=False)
    log(f"  Saved: {out} ({os.path.getsize(out)/1024:.0f} KB)")
    return Z


# ============================================================
# 2. UMAP — nonlinear manifold learning on raw features
# ============================================================
def build_umap(raw, X, dim=64):
    log("=" * 60)
    log("BUILDING UMAP-64")
    log("=" * 60)
    import umap

    log(f"  Fitting UMAP (dim={dim}, n_neighbors=30, metric=cosine)...")
    reducer = umap.UMAP(
        n_components=dim,
        n_neighbors=30,
        min_dist=0.1,
        metric="cosine",
        random_state=SEED,
        verbose=False,
    )
    Z = reducer.fit_transform(X).astype(np.float32)
    log(f"  Output shape: {Z.shape}")

    df = pd.DataFrame(Z, columns=[f"u{i}" for i in range(dim)])
    df.insert(0, "hex_id", raw["hex_id"].values)
    out = f"{OUT}/umap_64.parquet"
    df.to_parquet(out, index=False)
    log(f"  Saved: {out} ({os.path.getsize(out)/1024:.0f} KB)")
    return Z


# ============================================================
# 3. TRANSFORMER — masked-feature modeling with self-attention
# ============================================================
class FeatureTransformer(nn.Module):
    """
    Each feature is a token; value embedding + feature-id (positional) embedding.
    Randomly mask 15% of features, train to reconstruct masked values.
    CLS token output = 64-d embedding.
    """
    def __init__(self, n_features, d_model=32, nhead=2, nlayers=2, out_dim=64):
        super().__init__()
        self.value_embed = nn.Linear(1, d_model)
        self.feat_embed = nn.Embedding(n_features, d_model)
        self.cls = nn.Parameter(torch.randn(1, 1, d_model))
        self.mask_tok = nn.Parameter(torch.randn(1, 1, d_model))
        layer = nn.TransformerEncoderLayer(
            d_model, nhead, dim_feedforward=64,
            batch_first=True, dropout=0.1,
        )
        self.encoder = nn.TransformerEncoder(layer, nlayers)
        self.recon = nn.Linear(d_model, 1)
        self.proj = nn.Linear(d_model, out_dim)
        self.n_features = n_features

    def forward(self, x, mask):
        B = x.size(0)
        feat_ids = torch.arange(self.n_features, device=x.device).unsqueeze(0).expand(B, -1)
        feat_embs = self.feat_embed(feat_ids)
        val_embs = self.value_embed(x.unsqueeze(-1))
        toks = feat_embs + val_embs
        mask_exp = mask.unsqueeze(-1).expand_as(toks)
        toks = torch.where(mask_exp, self.mask_tok.expand(B, self.n_features, -1), toks)
        cls = self.cls.expand(B, -1, -1)
        toks = torch.cat([cls, toks], dim=1)
        out = self.encoder(toks)
        cls_out = out[:, 0]
        emb = self.proj(cls_out)
        recon = self.recon(out[:, 1:]).squeeze(-1)
        return emb, recon


def build_transformer(raw, X, dim=64, epochs=40, batch_size=256, mask_rate=0.15):
    log("=" * 60)
    log("BUILDING TRANSFORMER-64 (masked-feature modeling)")
    log("=" * 60)

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"  Device: {device}")

    n, n_feat = X.shape
    Xt = torch.tensor(X, dtype=torch.float32).to(device)

    model = FeatureTransformer(n_feat, d_model=32, nhead=2, nlayers=2, out_dim=dim).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)

    log(f"  Training {epochs} epochs, batch_size={batch_size}, mask_rate={mask_rate}")
    log(f"  Params: ~{sum(p.numel() for p in model.parameters())/1000:.0f}K")
    rng = np.random.default_rng(SEED)
    t0 = time.time()
    for ep in range(epochs):
        model.train()
        perm = rng.permutation(n)
        total_loss = 0.0; nb = 0
        for i in range(0, n, batch_size):
            idx = perm[i:i+batch_size]
            xb = Xt[idx]
            mask = torch.tensor(rng.random((len(idx), n_feat)) < mask_rate,
                                 dtype=torch.bool).to(device)
            _, recon = model(xb, mask)
            loss = ((recon - xb) ** 2 * mask.float()).sum() / (mask.float().sum() + 1e-9)
            opt.zero_grad(); loss.backward(); opt.step()
            total_loss += loss.item(); nb += 1
        if (ep + 1) % 5 == 0 or ep == 0:
            log(f"    ep {ep+1:>3}/{epochs}  loss={total_loss/nb:.4f}  "
                f"t={time.time()-t0:.0f}s")

    # Extract embeddings
    log("  Extracting embeddings (no mask, deterministic)...")
    model.eval()
    Z = np.zeros((n, dim), dtype=np.float32)
    with torch.no_grad():
        for i in range(0, n, batch_size):
            xb = Xt[i:i+batch_size]
            mask_false = torch.zeros(xb.size(0), n_feat, dtype=torch.bool).to(device)
            emb, _ = model(xb, mask_false)
            Z[i:i+batch_size] = emb.cpu().numpy()

    df = pd.DataFrame(Z, columns=[f"t{i}" for i in range(dim)])
    df.insert(0, "hex_id", raw["hex_id"].values)
    out = f"{OUT}/transformer_64.parquet"
    df.to_parquet(out, index=False)
    log(f"  Saved: {out} ({os.path.getsize(out)/1024:.0f} KB)")
    return Z


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", nargs="+",
                    default=["node2vec", "umap", "transformer"],
                    choices=["node2vec", "umap", "transformer"])
    args = ap.parse_args()

    log("Loading shared data...")
    raw, X, adj = load()
    log(f"  Raw feature matrix: {X.shape}  Graph: {adj.shape} nnz={adj.nnz}")

    for m in args.methods:
        try:
            if m == "node2vec":
                build_node2vec(raw, adj)
            elif m == "umap":
                build_umap(raw, X)
            elif m == "transformer":
                build_transformer(raw, X)
        except Exception as e:
            log(f"ERROR in {m}: {e}")
            import traceback; traceback.print_exc()

    log("\nDone. Baselines:")
    for f in os.listdir(OUT):
        log(f"  {f}  ({os.path.getsize(OUT+'/'+f)/1024:.0f} KB)")

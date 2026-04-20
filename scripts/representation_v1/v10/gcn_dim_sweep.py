#!/usr/bin/env python3
"""
Train GCN at multiple embedding dimensions (32, 128, 256) and compare vs GCN-64.

Re-uses the architecture from gcn_masked_hex.py but parameterizes gcn_dim.
Outputs: embeddings + kNN-PA + category R² for each.
"""
import os, sys, json, time, argparse
# Import the training pipeline from gcn_masked_hex
sys.path.insert(0, "/home/azureuser/digital-atlas-sgp")

import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
import scipy.sparse as sp

ROOT = "/home/azureuser/digital-atlas-sgp"
RESULTS = f"{ROOT}/data/hex_v10/gcn_results"
os.makedirs(RESULTS, exist_ok=True)

ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
BK_COLS = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}
SEED = 42


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def load_data():
    log("Loading data...")
    raw = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
    norm = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet")

    cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and
                       c not in {"pc_cat_hhi","pc_cat_entropy"}])
    target = raw[cat_cols].to_numpy(np.float32)
    target_log = np.log1p(target)

    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]
    context_cols = [c for c in feat_cols if not c.startswith("pc_")]
    context = norm[context_cols].to_numpy(np.float32)
    stds = context.std(axis=0); keep = stds > 1e-9
    context = context[:, keep]

    # Graph
    adj = sp.load_npz(f"{ROOT}/data/hex_v10/hex_influence_graph.npz")
    coo = adj.tocoo()
    r, c, w = coo.row, coo.col, coo.data
    sp_mask = w == 1.0
    tr_mask = w == 2.0
    n = len(raw)
    self_loops = np.stack([np.arange(n), np.arange(n)])
    spatial_ei = torch.tensor(
        np.concatenate([np.stack([r[sp_mask], c[sp_mask]]), self_loops], axis=1),
        dtype=torch.long)
    transit_ei = torch.tensor(
        np.concatenate([np.stack([r[tr_mask], c[tr_mask]]), self_loops], axis=1),
        dtype=torch.long)

    log(f"  hexes={n} context_dim={context.shape[1]} cats={len(cat_cols)}")
    log(f"  spatial edges={spatial_ei.shape[1]} transit edges={transit_ei.shape[1]}")
    return raw, context, target_log, target, cat_cols, spatial_ei, transit_ei


try:
    from torch_geometric.nn import GCNConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False


class DualGCN(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        if HAS_PYG:
            self.spa = GCNConv(in_dim, out_dim)
            self.tra = GCNConv(in_dim, out_dim)
        else:
            self.spa = nn.Linear(in_dim, out_dim)
            self.tra = nn.Linear(in_dim, out_dim)
        self.fuse = nn.Linear(2 * out_dim, out_dim)

    def forward(self, x, sp_ei, tr_ei):
        if HAS_PYG:
            hs = F.relu(self.spa(x, sp_ei))
            ht = F.relu(self.tra(x, tr_ei))
        else:
            hs = F.relu(self.spa(x))
            ht = F.relu(self.tra(x))
        return F.relu(self.fuse(torch.cat([hs, ht], dim=-1)))


class Model(nn.Module):
    def __init__(self, ctx_dim, tgt_dim, gcn_dim, hidden=128):
        super().__init__()
        self.ctx = nn.Sequential(
            nn.Linear(ctx_dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, hidden), nn.BatchNorm1d(hidden), nn.ReLU(),
        )
        self.tgt = nn.Sequential(
            nn.Linear(tgt_dim, hidden // 2), nn.ReLU(),
            nn.Linear(hidden // 2, hidden // 2),
        )
        self.mask_tok = nn.Parameter(torch.randn(hidden // 2))
        fus = hidden + hidden // 2
        self.gcn = DualGCN(fus, gcn_dim)
        self.head = nn.Sequential(
            nn.Linear(gcn_dim + fus, hidden), nn.BatchNorm1d(hidden), nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, hidden // 2), nn.ReLU(),
            nn.Linear(hidden // 2, tgt_dim),
        )
        self.gcn_dim = gcn_dim

    def encode(self, ctx, vis_tgt, mask, sp_ei, tr_ei):
        """Return the GCN embedding only (no prediction)."""
        c = self.ctx(ctx)
        # apply mask: where mask is True, replace with mask_tok
        t = self.tgt(vis_tgt)
        fus = torch.cat([c, t], dim=-1)
        h = self.gcn(fus, sp_ei, tr_ei)
        return h

    def forward(self, ctx, vis_tgt, mask, sp_ei, tr_ei):
        c = self.ctx(ctx)
        t = self.tgt(vis_tgt)
        fus = torch.cat([c, t], dim=-1)
        h = self.gcn(fus, sp_ei, tr_ei)
        out = self.head(torch.cat([h, fus], dim=-1))
        return out, h


def train_eval(gcn_dim, epochs=100, mask_rate=0.3):
    log(f"\n{'='*60}\nTRAINING GCN with gcn_dim={gcn_dim}\n{'='*60}")
    raw, context, target_log, target, cat_cols, sp_ei, tr_ei = load_data()

    torch.manual_seed(SEED)
    np.random.seed(SEED)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"  Device: {device}")

    ctx = torch.tensor(context, dtype=torch.float32).to(device)
    tgt = torch.tensor(target_log, dtype=torch.float32).to(device)
    sp_ei = sp_ei.to(device); tr_ei = tr_ei.to(device)

    n_cats = target_log.shape[1]
    model = Model(ctx.shape[1], n_cats, gcn_dim=gcn_dim).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-5)

    # 5-fold CV
    kf = KFold(n_splits=5, shuffle=True, random_state=SEED)
    all_pred = np.zeros_like(target_log)
    all_emb = np.zeros((len(context), gcn_dim), dtype=np.float32)
    rng = np.random.default_rng(SEED)

    for fold, (tr_idx, va_idx) in enumerate(kf.split(np.arange(len(context)))):
        log(f"  Fold {fold+1}/5 ...")
        # Fresh model per fold
        torch.manual_seed(SEED + fold)
        model = Model(ctx.shape[1], n_cats, gcn_dim=gcn_dim).to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-5)

        tr_mask = np.zeros(len(context), dtype=bool); tr_mask[tr_idx] = True

        for ep in range(epochs):
            model.train()
            # sample masks (for training hexes only; eval hexes get fixed mask)
            mask = torch.tensor(
                rng.random((len(context), n_cats)) < mask_rate,
                dtype=torch.bool).to(device)
            vis_tgt = tgt * (~mask).float()

            out, _ = model(ctx, vis_tgt, mask, sp_ei, tr_ei)
            # loss only on training indices, only on masked positions
            loss_mask = mask.float() * torch.tensor(tr_mask, dtype=torch.float32).to(device).unsqueeze(1)
            loss = ((out - tgt) ** 2 * loss_mask).sum() / (loss_mask.sum() + 1e-9)

            opt.zero_grad(); loss.backward(); opt.step()

        # Eval on val: with 30% mask, predict masked, also extract embedding
        model.eval()
        with torch.no_grad():
            mask = torch.tensor(
                rng.random((len(context), n_cats)) < mask_rate,
                dtype=torch.bool).to(device)
            vis_tgt = tgt * (~mask).float()
            out, emb = model(ctx, vis_tgt, mask, sp_ei, tr_ei)
            all_pred[va_idx] = out[va_idx].cpu().numpy()
            all_emb[va_idx] = emb[va_idx].cpu().numpy()

    # Metrics
    # Category R² (on masked positions - we test on all now for simplicity)
    from sklearn.metrics import r2_score
    per_cat_r2 = []
    for j in range(n_cats):
        r = r2_score(target_log[:, j], all_pred[:, j])
        per_cat_r2.append(r)
    mean_r2 = float(np.mean(per_cat_r2))

    # kNN-PA @10
    Z = all_emb
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
    S = Zn @ Zn.T
    np.fill_diagonal(S, -np.inf)
    nn = np.argpartition(-S, 10, axis=1)[:, :10]
    pa = np.asarray(raw["parent_pa"].astype(str).values)
    knn_pa = float((pa[nn] == pa[:, None]).mean())

    log(f"  DIM={gcn_dim}  kNN-PA@10={knn_pa:.3f}  cat_R²={mean_r2:.3f}")

    # Save embedding
    emb_df = pd.DataFrame(Z, columns=[f"g{i}" for i in range(gcn_dim)])
    emb_df.insert(0, "hex_id", raw["hex_id"].values)
    emb_df.to_parquet(f"{RESULTS}/gcn_embedding_{gcn_dim}.parquet", index=False)
    log(f"  Saved: {RESULTS}/gcn_embedding_{gcn_dim}.parquet")

    return {"dims": gcn_dim, "knn_pa": knn_pa, "cat_r2_mean": mean_r2}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dims", type=int, nargs="+", default=[32, 128, 256])
    ap.add_argument("--epochs", type=int, default=100)
    args = ap.parse_args()

    results = []
    for d in args.dims:
        results.append(train_eval(d, epochs=args.epochs))

    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"{'DIM':<6} {'kNN-PA':<10} {'cat_R²':<10}")
    for r in results:
        log(f"{r['dims']:<6} {r['knn_pa']:<10.3f} {r['cat_r2_mean']:<10.3f}")

    out = f"{RESULTS}/gcn_dim_sweep.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    log(f"\nSaved: {out}")

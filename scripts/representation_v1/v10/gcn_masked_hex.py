#!/usr/bin/env python3
"""
GCN-MLP Masked Category Predictor — Hex v10

Adapted from atlas_model.py (subzone, 332 nodes, R²=0.597) to
hex v10 (7,318 nodes, 460 features, influence graph with 47K edges).

Architecture:
  Context encoder: physical features (non-commerce) → MLP → 128-dim
  Target encoder: 24 category counts (with masking) → MLP → 64-dim
  Learnable mask token for masked category positions
  Dual GCN: spatial edges + transit edges (from hex_influence_graph.npz)
  Prediction head: graph output + skip connection → predict 24 counts

Training: mask 30% of categories per hex per epoch, predict masked from
context + visible categories + graph neighborhood.

Run ON SERVER: python3 gcn_masked_hex.py
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np
import json, os, time, sys
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
import scipy.sparse as sp

# Try torch_geometric, fall back to manual if not installed
try:
    from torch_geometric.nn import GCNConv
    HAS_PYG = True
except ImportError:
    HAS_PYG = False
    print("torch_geometric not available, using manual GCN")

ROOT = "/home/azureuser/digital-atlas-sgp"
HEX_RAW = f"{ROOT}/data/hex_v10/hex_features_v10.parquet"
HEX_NORM = f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet"
GRAPH_PATH = f"{ROOT}/data/hex_v10/hex_influence_graph.npz"
RESULTS = f"{ROOT}/data/hex_v10/gcn_results"
os.makedirs(RESULTS, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

# ============================================================
# DATA
# ============================================================
ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
BK_COLS = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}

def load_data():
    log("Loading hex v10 data...")
    raw = pd.read_parquet(HEX_RAW)
    norm = pd.read_parquet(HEX_NORM)

    # Target: 24 category counts (raw, not normalized)
    cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and
                       c not in {"pc_cat_hhi","pc_cat_entropy"}])
    target = raw[cat_cols].to_numpy(dtype=np.float32)
    target_log = np.log1p(target)

    # Context: everything EXCEPT place_composition (pc_*) — no leakage
    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]
    context_cols = [c for c in feat_cols if not c.startswith("pc_")]
    context = norm[context_cols].to_numpy(dtype=np.float32)

    # Remove constant columns from context
    stds = context.std(axis=0)
    keep = stds > 1e-9
    context = context[:, keep]
    context_cols_kept = [c for c, k in zip(context_cols, keep) if k]

    # Load influence graph
    log("Loading influence graph...")
    adj = sp.load_npz(GRAPH_PATH)

    # Build edge_index from sparse matrix
    # The graph has spatial (weight=1) and transit (weight=2) edges
    coo = adj.tocoo()
    rows, cols, weights = coo.row, coo.col, coo.data

    # Split into spatial and transit edges
    spatial_mask = weights == 1.0
    transit_mask = weights == 2.0

    spatial_edges = np.stack([rows[spatial_mask], cols[spatial_mask]])
    transit_edges = np.stack([rows[transit_mask], cols[transit_mask]])

    # Add self-loops
    n = len(raw)
    self_loops = np.stack([np.arange(n), np.arange(n)])
    spatial_edges = np.concatenate([spatial_edges, self_loops], axis=1)
    transit_edges = np.concatenate([transit_edges, self_loops], axis=1)

    spatial_ei = torch.tensor(spatial_edges, dtype=torch.long)
    transit_ei = torch.tensor(transit_edges, dtype=torch.long)

    # Active hexes (for evaluation — only hexes with places)
    active = raw["pc_total"].to_numpy() > 0
    pas = raw["parent_pa"].to_numpy(dtype=str)
    hex_ids = raw["hex_id"].to_numpy(dtype=str)

    log(f"  Nodes: {n}")
    log(f"  Context features: {context.shape[1]} (non-commerce)")
    log(f"  Target categories: {len(cat_cols)}")
    log(f"  Spatial edges: {spatial_edges.shape[1]}")
    log(f"  Transit edges: {transit_edges.shape[1]}")
    log(f"  Active hexes: {active.sum()}")

    return {
        "context": torch.tensor(context, dtype=torch.float32),
        "target": torch.tensor(target, dtype=torch.float32),
        "target_log": torch.tensor(target_log, dtype=torch.float32),
        "spatial_ei": spatial_ei,
        "transit_ei": transit_ei,
        "n_nodes": n,
        "cat_cols": cat_cols,
        "context_cols": context_cols_kept,
        "active": active,
        "pas": pas,
        "hex_ids": hex_ids,
    }

# ============================================================
# MODEL — Manual GCN (no torch_geometric dependency)
# ============================================================
class ManualGCNLayer(nn.Module):
    """Simple GCN layer: H' = D^{-1/2} A D^{-1/2} H W"""
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim)

    def forward(self, x, edge_index):
        # Build adjacency and degree
        n = x.size(0)
        row, col = edge_index[0], edge_index[1]
        # Aggregate: for each node, sum neighbor features
        out = torch.zeros(n, x.size(1), device=x.device)
        out.index_add_(0, row, x[col])
        # Degree normalization
        deg = torch.zeros(n, device=x.device)
        deg.index_add_(0, row, torch.ones(row.size(0), device=x.device))
        deg = deg.clamp(min=1).unsqueeze(1)
        out = out / deg
        return self.linear(out)

class HexCompositionPredictor(nn.Module):
    def __init__(self, context_dim, target_dim, hidden_dim=128, gcn_dim=64):
        super().__init__()
        self.target_dim = target_dim

        # Context encoder
        self.context_encoder = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # Target encoder (masked categories)
        self.target_encoder = nn.Sequential(
            nn.Linear(target_dim, hidden_dim // 2),
            nn.ReLU(),
        )

        # Learnable mask token
        self.mask_token = nn.Parameter(torch.randn(1, target_dim) * 0.01)

        # Fusion dim
        fusion_dim = hidden_dim + hidden_dim // 2  # 192

        # GCN layers — spatial
        GCN = GCNConv if HAS_PYG else ManualGCNLayer
        self.gcn_s1 = GCN(fusion_dim, gcn_dim)
        self.gcn_s2 = GCN(gcn_dim, gcn_dim)

        # GCN layers — transit
        self.gcn_t1 = GCN(fusion_dim, gcn_dim)
        self.gcn_t2 = GCN(gcn_dim, gcn_dim)

        # Learned graph fusion weight
        self.graph_alpha = nn.Parameter(torch.tensor(0.5))

        # Prediction head
        self.pred_head = nn.Sequential(
            nn.Linear(gcn_dim + fusion_dim, hidden_dim),  # skip connection
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, target_dim),
        )

    def forward(self, context, target_log, mask, spatial_ei, transit_ei):
        # Encode context
        ctx = self.context_encoder(context)

        # Mask target
        masked = target_log.clone()
        mask_f = mask.float()
        masked = masked * (1 - mask_f) + self.mask_token.expand_as(masked) * mask_f

        # Encode masked target
        tgt = self.target_encoder(masked)

        # Fuse
        fused = torch.cat([ctx, tgt], dim=-1)

        # Spatial GCN
        hs = F.relu(self.gcn_s1(fused, spatial_ei))
        hs = F.dropout(hs, p=0.1, training=self.training)
        hs = self.gcn_s2(hs, spatial_ei)

        # Transit GCN
        ht = F.relu(self.gcn_t1(fused, transit_ei))
        ht = F.dropout(ht, p=0.1, training=self.training)
        ht = self.gcn_t2(ht, transit_ei)

        # Weighted fusion
        alpha = torch.sigmoid(self.graph_alpha)
        hg = alpha * hs + (1 - alpha) * ht

        # Skip + predict
        out = torch.cat([hg, fused], dim=-1)
        return self.pred_head(out)

    def get_embedding(self, context, target_log, spatial_ei, transit_ei):
        """Extract the bottleneck embedding (no masking)."""
        self.eval()
        with torch.no_grad():
            ctx = self.context_encoder(context)
            tgt = self.target_encoder(target_log)
            fused = torch.cat([ctx, tgt], dim=-1)
            hs = F.relu(self.gcn_s1(fused, spatial_ei))
            hs = self.gcn_s2(hs, spatial_ei)
            ht = F.relu(self.gcn_t1(fused, transit_ei))
            ht = self.gcn_t2(ht, transit_ei)
            alpha = torch.sigmoid(self.graph_alpha)
            hg = alpha * hs + (1 - alpha) * ht
            return hg  # gcn_dim (64) dimensional embedding

# ============================================================
# TRAINING
# ============================================================
def create_mask(n, d, ratio=0.3):
    mask = torch.zeros(n, d, dtype=torch.bool)
    for i in range(n):
        k = max(1, int(d * ratio))
        idx = torch.randperm(d)[:k]
        mask[i, idx] = True
    return mask

def train_fold(data, train_idx, val_idx, fold, epochs=500, lr=1e-3):
    ctx = data["context"]; tgt_log = data["target_log"]
    sei = data["spatial_ei"]; tei = data["transit_ei"]
    n = data["n_nodes"]; d = tgt_log.size(1)

    model = HexCompositionPredictor(ctx.size(1), d, hidden_dim=128, gcn_dim=64)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    best_val = float("inf"); best_st = None; wait = 0

    for ep in range(epochs):
        model.train()
        mask = create_mask(n, d, 0.3)
        pred = model(ctx, tgt_log, mask, sei, tei)

        # Loss on masked positions of train nodes
        tr_mask = mask[train_idx]
        tr_pred = pred[train_idx]; tr_true = tgt_log[train_idx]
        loss_m = F.mse_loss(tr_pred[tr_mask], tr_true[tr_mask])
        loss_u = F.mse_loss(tr_pred[~tr_mask], tr_true[~tr_mask])
        loss = loss_m + 0.1 * loss_u

        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step(); sch.step()

        if ep % 20 == 0:
            model.eval()
            with torch.no_grad():
                vm = create_mask(n, d, 0.3)
                vp = model(ctx, tgt_log, vm, sei, tei)
                vl = F.mse_loss(vp[val_idx][vm[val_idx]], tgt_log[val_idx][vm[val_idx]]).item()
            if vl < best_val:
                best_val = vl; wait = 0
                best_st = {k:v.clone() for k,v in model.state_dict().items()}
            else:
                wait += 1
                if wait >= 5: break  # patience = 5 * 20 = 100 epochs
            if ep % 100 == 0:
                log(f"  F{fold} E{ep}: train={loss.item():.4f} val={vl:.4f} best={best_val:.4f}")

    model.load_state_dict(best_st)
    return model, best_val

def evaluate_fold(model, data, val_idx):
    model.eval()
    with torch.no_grad():
        no_mask = torch.zeros(data["n_nodes"], data["target_log"].size(1), dtype=torch.bool)
        pred_log = model(data["context"], data["target_log"], no_mask,
                         data["spatial_ei"], data["transit_ei"])
        pred = torch.expm1(pred_log).clamp(min=0).numpy()
        true = data["target"].numpy()

        vp = pred[val_idx]; vt = true[val_idx]
        r2s = []
        for j in range(vt.shape[1]):
            ss_res = ((vt[:,j] - vp[:,j])**2).sum()
            ss_tot = ((vt[:,j] - vt[:,j].mean())**2).sum()
            r2s.append(1 - ss_res / max(ss_tot, 1e-8))
        mae = np.mean(np.abs(vp - vt))
    return np.array(r2s), mae, pred

# ============================================================
# MAIN
# ============================================================
def main():
    t0 = time.time()
    log("="*60)
    log("GCN MASKED CATEGORY PREDICTOR — HEX V10")
    log("="*60)

    data = load_data()
    n = data["n_nodes"]; d = data["target_log"].size(1)

    # 5-fold CV (not 10 — faster with 7K nodes)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    fold_r2s = []; fold_maes = []
    all_pred = np.zeros_like(data["target"].numpy())

    for fold, (tr, va) in enumerate(kf.split(np.arange(n))):
        log(f"\n--- Fold {fold+1}/5 (train={len(tr)}, val={len(va)}) ---")
        tr_t = torch.tensor(tr, dtype=torch.long)
        va_t = torch.tensor(va, dtype=torch.long)

        model, vl = train_fold(data, tr_t, va_t, fold+1, epochs=500)
        r2s, mae, pred = evaluate_fold(model, data, va_t)

        fold_r2s.append(r2s)
        fold_maes.append(mae)
        all_pred[va] = pred[va]

        log(f"  Fold {fold+1}: R2={np.mean(r2s):.3f} MAE={mae:.2f}")

    # Aggregate
    mean_r2 = np.mean([np.mean(r) for r in fold_r2s])
    mean_mae = np.mean(fold_maes)
    cat_r2s = np.mean(fold_r2s, axis=0)

    log(f"\n{'='*60}")
    log(f"RESULTS: Mean R2={mean_r2:.3f}  MAE={mean_mae:.2f}")
    log(f"{'='*60}")

    cat_cols = data["cat_cols"]
    log(f"\n{'Category':<35} R2")
    log("-"*45)
    for i, c in enumerate(cat_cols):
        log(f"  {c:<33} {cat_r2s[i]:.3f}")

    # Train final model on all data
    log("\nTraining final model on all data...")
    all_idx = torch.arange(n)
    final_model, _ = train_fold(data, all_idx, all_idx, 0, epochs=600)

    # Extract embedding
    log("Extracting GCN embeddings...")
    emb = final_model.get_embedding(data["context"], data["target_log"],
                                     data["spatial_ei"], data["transit_ei"])
    emb_np = emb.numpy()

    # Save embedding
    raw = pd.read_parquet(HEX_RAW)
    emb_df = pd.DataFrame({
        "hex_id": raw["hex_id"],
        "lat": raw["lat"], "lng": raw["lng"],
        "parent_subzone": raw["parent_subzone"],
        "parent_pa": raw["parent_pa"],
    })
    for i in range(emb_np.shape[1]):
        emb_df[f"g{i}"] = emb_np[:, i]
    emb_df.to_parquet(f"{RESULTS}/gcn_embedding_64.parquet", index=False)
    log(f"Wrote gcn_embedding_64.parquet ({emb_df.shape})")

    # Evaluate embedding with kNN
    active = data["active"]; pas = data["pas"]
    Za = emb_np[active]
    pa_a = pas[active]
    norms = np.linalg.norm(Za, axis=1, keepdims=True); norms[norms<1e-9]=1
    Zn = Za/norms; sims = Zn@Zn.T; np.fill_diagonal(sims,-1)
    c=t=0
    for i in range(len(Za)):
        top5 = np.argsort(-sims[i])[:5]; c+=sum(1 for j in top5 if pa_a[j]==pa_a[i]); t+=5
    knn_pa = c/t
    log(f"\nGCN embedding kNN PA accuracy: {knn_pa:.3f}")
    log(f"(Compare: raw features=0.374, PCA-128=0.359)")

    # Save results
    report = {
        "method": "gcn_masked_hex_v10",
        "n_nodes": n,
        "context_dim": int(data["context"].size(1)),
        "target_dim": d,
        "embedding_dim": emb_np.shape[1],
        "mean_r2": round(float(mean_r2), 4),
        "mean_mae": round(float(mean_mae), 4),
        "knn_pa_accuracy": round(float(knn_pa), 4),
        "per_category_r2": {c: round(float(r), 4) for c, r in zip(cat_cols, cat_r2s)},
        "comparison": {
            "subzone_gcn_v1": 0.597,
            "subzone_xgb_v5": 0.110,
            "hex_v10_this": round(float(mean_r2), 4),
        },
        "time_seconds": round(time.time() - t0),
    }
    with open(f"{RESULTS}/gcn_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Save model
    torch.save(final_model.state_dict(), f"{RESULTS}/gcn_model.pt")

    log(f"\nTotal time: {time.time()-t0:.0f}s")
    log("DONE.")

if __name__ == "__main__":
    main()

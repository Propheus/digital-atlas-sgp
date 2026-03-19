#!/usr/bin/env python3
"""
Digital Atlas SGP - Urban Composition Predictor
Masked Category Prediction with GCN-MLP
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
import pandas as pd
import numpy as np
import json, os, time, sys
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

FINAL = "/home/azureuser/digital-atlas-sgp/final"
GRAPHS = "/home/azureuser/digital-atlas-sgp/graphs"
RESULTS_DIR = "/home/azureuser/digital-atlas-sgp/model_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

# ============================================================
# DATA LOADING
# ============================================================
def load_data():
    log("Loading data...")

    sf = pd.read_parquet(FINAL + "/subzone_features_raw.parquet")
    log("  Subzone features: %d x %d" % sf.shape)

    # Identify feature blocks
    all_cols = sf.select_dtypes(include=[np.number]).columns.tolist()

    # TARGET: 24 category count columns
    target_cols = sorted([c for c in all_cols if c.startswith("cat_") and not c.endswith("_pct")])
    log("  Target cols (categories): %d" % len(target_cols))

    # CONTEXT: everything else numeric (excluding target)
    context_cols = [c for c in all_cols if c not in target_cols]
    log("  Context cols: %d" % len(context_cols))

    # Fill NaN
    sf[all_cols] = sf[all_cols].fillna(0)

    # Normalize context features
    context_scaler = StandardScaler()
    context_data = context_scaler.fit_transform(sf[context_cols].values)

    # Target: raw counts (we predict counts, not normalized)
    target_data = sf[target_cols].values.astype(np.float32)

    # Log-transform targets (counts are skewed)
    target_log = np.log1p(target_data)

    # Load adjacency graph
    with open(GRAPHS + "/subzone_adjacency.json") as f:
        adj_graph = json.load(f)

    # Load transit graph
    with open(GRAPHS + "/transit_connectivity.json") as f:
        transit_graph = json.load(f)

    # Build node index: subzone_code -> index
    subzone_codes = sf["subzone_code"].tolist()
    code_to_idx = {code: i for i, code in enumerate(subzone_codes)}
    n_nodes = len(subzone_codes)

    # Build adjacency edge_index
    adj_edges = []
    for e in adj_graph["edges"]:
        src = code_to_idx.get(e["source"])
        tgt = code_to_idx.get(e["target"])
        if src is not None and tgt is not None:
            adj_edges.append([src, tgt])
            adj_edges.append([tgt, src])  # undirected

    # Build transit edge_index
    transit_edges = []
    for e in transit_graph["edges"]:
        src = code_to_idx.get(e["source"])
        tgt = code_to_idx.get(e["target"])
        if src is not None and tgt is not None:
            transit_edges.append([src, tgt])
            transit_edges.append([tgt, src])

    # Add self-loops
    self_loops = [[i, i] for i in range(n_nodes)]

    adj_edge_index = torch.tensor(adj_edges + self_loops, dtype=torch.long).t().contiguous()
    transit_edge_index = torch.tensor(transit_edges + self_loops, dtype=torch.long).t().contiguous()

    log("  Adjacency edges: %d" % (len(adj_edges) // 2))
    log("  Transit edges: %d" % (len(transit_edges) // 2))

    data = {
        "context": torch.tensor(context_data, dtype=torch.float32),
        "target": torch.tensor(target_data, dtype=torch.float32),
        "target_log": torch.tensor(target_log, dtype=torch.float32),
        "adj_edge_index": adj_edge_index,
        "transit_edge_index": transit_edge_index,
        "n_nodes": n_nodes,
        "target_cols": target_cols,
        "context_cols": context_cols,
        "subzone_codes": subzone_codes,
        "subzone_names": sf["subzone_name"].tolist(),
        "context_scaler": context_scaler,
    }

    return data


# ============================================================
# MODEL
# ============================================================
class UrbanCompositionPredictor(nn.Module):
    def __init__(self, context_dim, target_dim, hidden_dim=64, gcn_dim=64):
        super().__init__()

        self.target_dim = target_dim

        # Context encoder
        self.context_encoder = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )

        # Target encoder (for visible/unmasked targets)
        self.target_encoder = nn.Sequential(
            nn.Linear(target_dim, hidden_dim // 2),
            nn.ReLU(),
        )

        # Mask token embedding (learnable)
        self.mask_token = nn.Parameter(torch.randn(1, target_dim) * 0.01)

        # GCN layers (spatial adjacency)
        fusion_dim = hidden_dim + hidden_dim // 2
        self.gcn1 = GCNConv(fusion_dim, gcn_dim)
        self.gcn2 = GCNConv(gcn_dim, gcn_dim)

        # Transit GCN layers
        self.transit_gcn1 = GCNConv(fusion_dim, gcn_dim)
        self.transit_gcn2 = GCNConv(gcn_dim, gcn_dim)

        # Graph fusion
        self.graph_alpha = nn.Parameter(torch.tensor(0.5))

        # Final prediction head
        self.prediction_head = nn.Sequential(
            nn.Linear(gcn_dim + fusion_dim, hidden_dim),  # skip connection
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, target_dim),
        )

    def forward(self, context, target_log, mask, adj_edge_index, transit_edge_index):
        # Encode context
        ctx_emb = self.context_encoder(context)  # [N, hidden]

        # Apply mask to target: masked positions get mask_token
        masked_target = target_log.clone()
        mask_expanded = mask.float()
        masked_target = masked_target * (1 - mask_expanded) + self.mask_token.expand(target_log.size(0), -1) * mask_expanded

        # Encode masked target
        tgt_emb = self.target_encoder(masked_target)  # [N, hidden//2]

        # Fuse
        fused = torch.cat([ctx_emb, tgt_emb], dim=-1)  # [N, hidden + hidden//2]

        # GCN on spatial graph
        h_spatial = F.relu(self.gcn1(fused, adj_edge_index))
        h_spatial = F.dropout(h_spatial, p=0.1, training=self.training)
        h_spatial = self.gcn2(h_spatial, adj_edge_index)

        # GCN on transit graph
        h_transit = F.relu(self.transit_gcn1(fused, transit_edge_index))
        h_transit = F.dropout(h_transit, p=0.1, training=self.training)
        h_transit = self.transit_gcn2(h_transit, transit_edge_index)

        # Weighted combination
        alpha = torch.sigmoid(self.graph_alpha)
        h_graph = alpha * h_spatial + (1 - alpha) * h_transit

        # Skip connection + prediction
        combined = torch.cat([h_graph, fused], dim=-1)
        output = self.prediction_head(combined)

        return output


# ============================================================
# TRAINING
# ============================================================
def create_mask(n_nodes, target_dim, mask_ratio=0.3):
    """Random mask: for each node, mask mask_ratio of target dims"""
    mask = torch.zeros(n_nodes, target_dim, dtype=torch.bool)
    for i in range(n_nodes):
        n_mask = max(1, int(target_dim * mask_ratio))
        indices = torch.randperm(target_dim)[:n_mask]
        mask[i, indices] = True
    return mask


def train_fold(data, train_idx, val_idx, fold, epochs=800, lr=1e-3):
    """Train one fold"""
    context = data["context"]
    target_log = data["target_log"]
    target_raw = data["target"]
    adj_ei = data["adj_edge_index"]
    transit_ei = data["transit_edge_index"]
    n_nodes = data["n_nodes"]
    target_dim = target_log.size(1)
    context_dim = context.size(1)

    model = UrbanCompositionPredictor(
        context_dim=context_dim,
        target_dim=target_dim,
        hidden_dim=64,
        gcn_dim=64,
    )

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float("inf")
    best_state = None
    patience = 80
    no_improve = 0

    train_losses = []
    val_losses = []

    for epoch in range(epochs):
        model.train()

        # Random mask each epoch
        mask = create_mask(n_nodes, target_dim, mask_ratio=0.3)

        # Forward
        pred = model(context, target_log, mask, adj_ei, transit_ei)

        # Loss on masked positions (train nodes only)
        train_mask = mask[train_idx]
        train_pred = pred[train_idx]
        train_true = target_log[train_idx]

        masked_loss = F.mse_loss(
            train_pred[train_mask],
            train_true[train_mask]
        )

        # Small regularization on unmasked
        unmasked_loss = F.mse_loss(
            train_pred[~train_mask],
            train_true[~train_mask]
        )

        loss = masked_loss + 0.1 * unmasked_loss

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        train_losses.append(loss.item())

        # Validation
        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                val_mask = create_mask(n_nodes, target_dim, mask_ratio=0.3)
                val_pred = model(context, target_log, val_mask, adj_ei, transit_ei)

                val_pred_nodes = val_pred[val_idx]
                val_true_nodes = target_log[val_idx]
                val_mask_nodes = val_mask[val_idx]

                val_loss = F.mse_loss(
                    val_pred_nodes[val_mask_nodes],
                    val_true_nodes[val_mask_nodes]
                ).item()

                val_losses.append(val_loss)

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_state = {k: v.clone() for k, v in model.state_dict().items()}
                    no_improve = 0
                else:
                    no_improve += 1

                if epoch % 100 == 0:
                    log("  Fold %d Epoch %d: train=%.4f val=%.4f best=%.4f" % (fold, epoch, loss.item(), val_loss, best_val_loss))

                if no_improve >= patience // 10:
                    log("  Fold %d: early stop at epoch %d" % (fold, epoch))
                    break

    # Load best model
    model.load_state_dict(best_state)
    model.eval()

    return model, best_val_loss, train_losses, val_losses


def evaluate_fold(model, data, val_idx):
    """Evaluate: predict all categories (no mask) and compare"""
    model.eval()
    with torch.no_grad():
        # No masking — predict everything
        no_mask = torch.zeros(data["n_nodes"], data["target_log"].size(1), dtype=torch.bool)
        pred_log = model(data["context"], data["target_log"], no_mask,
                         data["adj_edge_index"], data["transit_edge_index"])

        # Convert back from log space
        pred_counts = torch.expm1(pred_log).clamp(min=0)
        true_counts = data["target"]

        # Metrics on validation nodes
        val_pred = pred_counts[val_idx].numpy()
        val_true = true_counts[val_idx].numpy()

        # MAE per category
        mae_per_cat = np.mean(np.abs(val_pred - val_true), axis=0)

        # Overall MAE
        overall_mae = np.mean(np.abs(val_pred - val_true))

        # MAPE (where true > 0)
        mask = val_true > 0
        mape = np.mean(np.abs(val_pred[mask] - val_true[mask]) / val_true[mask]) * 100 if mask.sum() > 0 else float("inf")

        # R2 per category
        r2_per_cat = []
        for j in range(val_true.shape[1]):
            ss_res = np.sum((val_true[:, j] - val_pred[:, j]) ** 2)
            ss_tot = np.sum((val_true[:, j] - np.mean(val_true[:, j])) ** 2)
            r2 = 1 - ss_res / max(ss_tot, 1e-8)
            r2_per_cat.append(r2)

    return {
        "mae_per_cat": mae_per_cat,
        "overall_mae": overall_mae,
        "mape": mape,
        "r2_per_cat": np.array(r2_per_cat),
        "val_pred": val_pred,
        "val_true": val_true,
    }


# ============================================================
# MAIN: K-FOLD CROSS VALIDATION
# ============================================================
def main():
    log("=" * 60)
    log("DIGITAL ATLAS SGP - MODEL TRAINING")
    log("=" * 60)

    data = load_data()

    n_nodes = data["n_nodes"]
    target_cols = data["target_cols"]
    n_folds = 10
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

    fold_results = []
    all_predictions = np.zeros_like(data["target"].numpy())
    all_mask = np.zeros(n_nodes, dtype=bool)

    log("\nStarting %d-fold cross-validation..." % n_folds)
    log("  Nodes: %d, Context: %d, Target: %d" % (n_nodes, data["context"].size(1), data["target_log"].size(1)))

    indices = np.arange(n_nodes)

    for fold, (train_idx, val_idx) in enumerate(kf.split(indices)):
        log("\n--- Fold %d/%d (train=%d, val=%d) ---" % (fold + 1, n_folds, len(train_idx), len(val_idx)))

        train_idx_t = torch.tensor(train_idx, dtype=torch.long)
        val_idx_t = torch.tensor(val_idx, dtype=torch.long)

        model, val_loss, train_losses, val_losses = train_fold(
            data, train_idx_t, val_idx_t, fold + 1, epochs=800
        )

        metrics = evaluate_fold(model, data, val_idx_t)

        fold_results.append({
            "fold": fold + 1,
            "val_loss": val_loss,
            "overall_mae": float(metrics["overall_mae"]),
            "mape": float(metrics["mape"]),
            "r2_per_cat": metrics["r2_per_cat"].tolist(),
            "mae_per_cat": metrics["mae_per_cat"].tolist(),
        })

        # Store predictions for validation nodes
        all_predictions[val_idx] = metrics["val_pred"]
        all_mask[val_idx] = True

        log("  Fold %d: MAE=%.2f, MAPE=%.1f%%, R2_mean=%.3f" % (
            fold + 1, metrics["overall_mae"], metrics["mape"], np.mean(metrics["r2_per_cat"])))

    # ============================================================
    # AGGREGATE RESULTS
    # ============================================================
    log("\n" + "=" * 60)
    log("CROSS-VALIDATION RESULTS")
    log("=" * 60)

    all_maes = [r["overall_mae"] for r in fold_results]
    all_mapes = [r["mape"] for r in fold_results]
    all_r2s = [np.mean(r["r2_per_cat"]) for r in fold_results]

    log("  Mean MAE:  %.3f +/- %.3f" % (np.mean(all_maes), np.std(all_maes)))
    log("  Mean MAPE: %.1f%% +/- %.1f%%" % (np.mean(all_mapes), np.std(all_mapes)))
    log("  Mean R2:   %.3f +/- %.3f" % (np.mean(all_r2s), np.std(all_r2s)))

    # Per-category results
    cat_maes = np.mean([r["mae_per_cat"] for r in fold_results], axis=0)
    cat_r2s = np.mean([r["r2_per_cat"] for r in fold_results], axis=0)

    log("\nPer-category performance:")
    log("  %-45s  MAE     R2" % "Category")
    log("  " + "-" * 65)
    for i, col in enumerate(target_cols):
        log("  %-45s %6.2f  %6.3f" % (col, cat_maes[i], cat_r2s[i]))

    # ============================================================
    # TRAIN FINAL MODEL ON ALL DATA
    # ============================================================
    log("\n" + "=" * 60)
    log("TRAINING FINAL MODEL (all data)")
    log("=" * 60)

    all_idx = torch.arange(n_nodes)
    final_model, _, _, _ = train_fold(data, all_idx, all_idx, fold=0, epochs=1000, lr=1e-3)

    # Full prediction (no mask)
    final_model.eval()
    with torch.no_grad():
        no_mask = torch.zeros(n_nodes, len(target_cols), dtype=torch.bool)
        pred_log = final_model(data["context"], data["target_log"], no_mask,
                               data["adj_edge_index"], data["transit_edge_index"])
        final_pred = torch.expm1(pred_log).clamp(min=0).numpy()

    final_true = data["target"].numpy()

    # ============================================================
    # GAP ANALYSIS
    # ============================================================
    log("\n" + "=" * 60)
    log("GAP ANALYSIS")
    log("=" * 60)

    gaps = final_pred - final_true
    gap_scores = gaps / np.maximum(final_pred, 1)

    gap_df = pd.DataFrame(gap_scores, columns=[c.replace("cat_", "gap_") for c in target_cols])
    gap_df["subzone_code"] = data["subzone_codes"]
    gap_df["subzone_name"] = data["subzone_names"]

    # Also add raw prediction and actual
    pred_df = pd.DataFrame(final_pred, columns=[c.replace("cat_", "pred_") for c in target_cols])
    actual_df = pd.DataFrame(final_true, columns=[c.replace("cat_", "actual_") for c in target_cols])

    result_df = pd.concat([
        gap_df[["subzone_code", "subzone_name"]],
        actual_df, pred_df, gap_df.drop(columns=["subzone_code", "subzone_name"])
    ], axis=1)

    result_df.to_parquet(RESULTS_DIR + "/gap_analysis.parquet", index=False)
    result_df.to_csv(RESULTS_DIR + "/gap_analysis.csv", index=False)

    # Top gaps per category
    log("\nTop 5 opportunity gaps per category:")
    for col in target_cols:
        gap_col = col.replace("cat_", "gap_")
        pred_col = col.replace("cat_", "pred_")
        actual_col = col.replace("cat_", "actual_")
        top = result_df.nlargest(5, gap_col)
        log("\n  %s:" % col)
        for _, row in top.iterrows():
            log("    %s: predicted=%.0f actual=%.0f gap=%.2f" % (
                row["subzone_name"], row[pred_col], row[actual_col], row[gap_col]))

    # ============================================================
    # SAVE EVERYTHING
    # ============================================================
    log("\n" + "=" * 60)
    log("SAVING RESULTS")
    log("=" * 60)

    # Save model
    torch.save(final_model.state_dict(), RESULTS_DIR + "/model_weights.pt")

    # Save CV results
    cv_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "n_folds": n_folds,
        "n_nodes": n_nodes,
        "context_dim": int(data["context"].size(1)),
        "target_dim": len(target_cols),
        "target_cols": target_cols,
        "mean_mae": float(np.mean(all_maes)),
        "std_mae": float(np.std(all_maes)),
        "mean_mape": float(np.mean(all_mapes)),
        "mean_r2": float(np.mean(all_r2s)),
        "per_category_mae": {col: float(mae) for col, mae in zip(target_cols, cat_maes)},
        "per_category_r2": {col: float(r2) for col, r2 in zip(target_cols, cat_r2s)},
        "fold_results": fold_results,
    }

    with open(RESULTS_DIR + "/cv_report.json", "w") as f:
        json.dump(cv_report, f, indent=2)

    # ============================================================
    # VALIDATION TESTS
    # ============================================================
    log("\n" + "=" * 60)
    log("MODEL VALIDATION TESTS")
    log("=" * 60)

    tests = []

    # Test 1: Model beats naive baseline (predict mean)
    naive_pred = np.mean(final_true, axis=0, keepdims=True).repeat(n_nodes, axis=0)
    naive_mae = np.mean(np.abs(naive_pred - final_true))
    model_mae = np.mean(np.abs(final_pred - final_true))
    tests.append(("Model beats naive mean baseline", model_mae < naive_mae,
                   "model=%.2f naive=%.2f" % (model_mae, naive_mae)))

    # Test 2: Mean R2 > 0 (better than just predicting mean)
    tests.append(("Mean CV R2 > 0", np.mean(all_r2s) > 0, "R2=%.3f" % np.mean(all_r2s)))

    # Test 3: Mean R2 > 0.3 (reasonable fit)
    tests.append(("Mean CV R2 > 0.3", np.mean(all_r2s) > 0.3, "R2=%.3f" % np.mean(all_r2s)))

    # Test 4: No negative R2 categories (model doesn't hurt)
    neg_r2 = sum(1 for r in cat_r2s if r < 0)
    tests.append(("No categories with negative R2", neg_r2 == 0,
                   "%d negative" % neg_r2))

    # Test 5: Predictions are non-negative
    tests.append(("All predictions non-negative", (final_pred >= 0).all(), ""))

    # Test 6: Predictions are reasonable (not absurdly large)
    max_pred = final_pred.max()
    max_true = final_true.max()
    tests.append(("Max prediction < 5x max actual", max_pred < 5 * max_true,
                   "max_pred=%.0f max_actual=%.0f" % (max_pred, max_true)))

    # Test 7: Gap scores are bounded
    tests.append(("Gap scores in [-5, 5]", np.abs(gap_scores).max() < 5,
                   "max_gap=%.2f" % np.abs(gap_scores).max()))

    # Test 8: Cross-validation stability
    mae_cv = np.std(all_maes) / np.mean(all_maes)
    tests.append(("CV stability (MAE CV < 0.5)", mae_cv < 0.5,
                   "CV=%.3f" % mae_cv))

    all_pass = True
    for name, passed, detail in tests:
        status = "PASS" if passed else "FAIL"
        log("  [%s] %s %s" % (status, name, detail))
        if not passed:
            all_pass = False

    log("\n  OVERALL: %s" % ("ALL PASSED" if all_pass else "SOME FAILED"))

    # Save test results
    test_report = {
        "tests": [{"name": n, "passed": p, "detail": d} for n, p, d in tests],
        "all_passed": all_pass,
    }
    with open(RESULTS_DIR + "/validation_tests.json", "w") as f:
        json.dump(test_report, f, indent=2)

    log("\nSaved to %s:" % RESULTS_DIR)
    for f in sorted(os.listdir(RESULTS_DIR)):
        log("  %s: %.1f KB" % (f, os.path.getsize(os.path.join(RESULTS_DIR, f)) / 1024))

    log("\nDONE.")


if __name__ == "__main__":
    main()

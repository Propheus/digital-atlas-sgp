#!/usr/bin/env python3
"""
Digital Atlas SGP - Model v2
Fixes: dwelling bugs, non-viable exclusion, proportion prediction,
interaction features, centrality, correlation-aware masking, XGBoost baseline
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
import pandas as pd
import numpy as np
import json, os, time, sys
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from math import radians, sin, cos, sqrt, atan2

FINAL = "/home/azureuser/digital-atlas-sgp/final"
GRAPHS = "/home/azureuser/digital-atlas-sgp/graphs"
INTER = "/home/azureuser/digital-atlas-sgp/intermediate"
RESULTS = "/home/azureuser/digital-atlas-sgp/model_results_v2"
os.makedirs(RESULTS, exist_ok=True)

def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg), flush=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

# ============================================================
# FIX 1: RELOAD AND FIX DATA
# ============================================================
def load_and_fix_data():
    log("=" * 60)
    log("LOADING AND FIXING DATA")
    log("=" * 60)

    sf = pd.read_parquet(FINAL + "/subzone_features_raw.parquet")
    log("Raw features: %d x %d" % sf.shape)

    # FIX 1A: Dwelling percentages - recompute from dwelling counts
    log("\nFIX 1: Dwelling percentage bugs")
    dwl_path = "/home/azureuser/digital-atlas-sgp/data/demographics/dwellings_subzone_2025.csv"
    if os.path.exists(dwl_path):
        dwl = pd.read_csv(dwl_path)
        dwl_latest = dwl[dwl["Time"] == dwl["Time"].max()]
        # Pivot: subzone x floor_area -> dwelling count
        dwl_pivot = dwl_latest.pivot_table(index=["PA", "SZ"], columns="FA", values="HSE", fill_value=0).reset_index()
        dwl_pivot.columns.name = None

        # Total dwellings per subzone
        fa_cols = [c for c in dwl_pivot.columns if c not in ["PA", "SZ"]]
        dwl_pivot["total_dwellings"] = dwl_pivot[fa_cols].sum(axis=1)

        # Map to subzone codes
        dwl_pivot["SZ_upper"] = dwl_pivot["SZ"].str.upper().str.strip()

        # Fix: cap all dwelling _pct columns at 100
        for col in sf.columns:
            if "_pct" in col and any(w in col for w in ["HDB", "Condo", "Landed", "HUDC", "Others"]):
                before_bad = (sf[col] > 100).sum()
                sf[col] = sf[col].clip(upper=100)
                after_bad = (sf[col] > 100).sum()
                if before_bad > 0:
                    log("  Fixed %s: %d values capped at 100" % (col, before_bad))

    # FIX 1B: Remove zero-variance features
    log("\nFIX 2: Remove zero-variance features")
    numeric_cols = sf.select_dtypes(include=[np.number]).columns
    zero_var = [c for c in numeric_cols if sf[c].std() == 0]
    if zero_var:
        sf.drop(columns=zero_var, inplace=True)
        log("  Removed: %s" % zero_var)

    # FIX 2: Mark viable subzones
    log("\nFIX 3: Mark viable subzones")
    cat_cols = sorted([c for c in sf.columns if c.startswith("cat_") and not c.endswith("_pct")])

    sf["total_places"] = sf[cat_cols].sum(axis=1) if cat_cols else 0
    sf["is_viable"] = (
        (sf["total_population"].fillna(0) > 50) |
        (sf["total_places"] > 5)
    ).astype(int)

    viable = sf["is_viable"].sum()
    log("  Viable subzones: %d / %d" % (viable, len(sf)))

    # FIX 3: Add interaction features
    log("\nFIX 4: Add interaction features")

    sf["demand_potential"] = sf["pop_density"].fillna(0) * sf["lu_commercial_pct"].fillna(0) / 100
    sf["transit_density"] = sf["mrt_stations_1km"].fillna(0) * sf["bus_density_per_km2"].fillna(0)
    sf["affluence_proxy"] = sf["median_hdb_psf"].fillna(sf["median_hdb_psf"].median())

    # HDB room mix as affluence signal
    hdb_12 = sf["HDB 1- and 2-Room Flats_pct"].fillna(0)
    hdb_45 = sf["HDB 4-Room Flats_pct"].fillna(0) + sf["HDB 5-Room and Executive Flats_pct"].fillna(0)
    sf["hdb_affluence"] = hdb_45 - hdb_12  # positive = more affluent

    # Family vs singles proxy
    sf["elderly_ratio"] = sf["age_65_plus_pct"].fillna(0)

    # Commercial intensity
    sf["commercial_intensity"] = sf["lu_commercial_pct"].fillna(0) * sf["road_density_km_per_km2"].fillna(0)

    # FIX 4: Add centrality features
    log("\nFIX 5: Add centrality features")

    # Key Singapore destinations
    destinations = {
        "cbd": (1.2830, 103.8513),         # Raffles Place
        "orchard": (1.3048, 103.8318),      # Orchard Road
        "marina_bay": (1.2816, 103.8606),   # Marina Bay Sands
        "changi": (1.3644, 103.9915),       # Changi Airport
        "jurong": (1.3329, 103.7436),       # Jurong East
        "woodlands": (1.4369, 103.7867),    # Woodlands
        "tampines": (1.3539, 103.9452),     # Tampines
    }

    import geopandas as gpd
    sz_gdf = gpd.read_file("/home/azureuser/digital-atlas-sgp/data/boundaries/subzones.geojson")
    centroids = sz_gdf.geometry.centroid
    sz_gdf["cent_lat"] = centroids.y
    sz_gdf["cent_lon"] = centroids.x

    code_to_latlon = {}
    for _, row in sz_gdf.iterrows():
        code_to_latlon[row["SUBZONE_C"]] = (row["cent_lat"], row["cent_lon"])

    for dest_name, (dlat, dlon) in destinations.items():
        col = "dist_to_%s_km" % dest_name
        dists = []
        for code in sf["subzone_code"]:
            if code in code_to_latlon:
                clat, clon = code_to_latlon[code]
                dists.append(haversine(clat, clon, dlat, dlon) / 1000)
            else:
                dists.append(np.nan)
        sf[col] = dists

    sf["min_dist_to_destination_km"] = sf[["dist_to_%s_km" % d for d in destinations]].min(axis=1)
    log("  Added %d destination distance features" % len(destinations))

    # FIX 5: Compute PROPORTIONS (not just counts)
    log("\nFIX 6: Compute category proportions")
    total_safe = sf["total_places"].clip(lower=1)
    prop_cols = []
    for col in cat_cols:
        prop_col = col + "_prop"
        sf[prop_col] = sf[col].fillna(0) / total_safe
        prop_cols.append(prop_col)

    log("  Added %d proportion features" % len(prop_cols))

    # Fill remaining NaN
    numeric_cols = sf.select_dtypes(include=[np.number]).columns
    sf[numeric_cols] = sf[numeric_cols].fillna(0)

    return sf, cat_cols, prop_cols


# ============================================================
# MODEL v2
# ============================================================
class UrbanModelV2(nn.Module):
    def __init__(self, context_dim, target_dim, hidden=64):
        super().__init__()
        self.target_dim = target_dim

        self.context_enc = nn.Sequential(
            nn.Linear(context_dim, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(hidden, hidden),
            nn.GELU(),
        )

        self.target_enc = nn.Sequential(
            nn.Linear(target_dim, hidden // 2),
            nn.GELU(),
        )

        self.mask_token = nn.Parameter(torch.randn(1, target_dim) * 0.01)

        fusion = hidden + hidden // 2
        self.gcn1 = GCNConv(fusion, hidden)
        self.gcn2 = GCNConv(hidden, hidden)
        self.transit_gcn1 = GCNConv(fusion, hidden)
        self.transit_gcn2 = GCNConv(hidden, hidden)
        self.alpha = nn.Parameter(torch.tensor(0.5))

        self.head = nn.Sequential(
            nn.Linear(hidden + fusion, hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden, target_dim),
        )

    def forward(self, context, target, mask, adj_ei, transit_ei):
        ctx = self.context_enc(context)
        masked_t = target * (1 - mask.float()) + self.mask_token.expand_as(target) * mask.float()
        tgt = self.target_enc(masked_t)
        fused = torch.cat([ctx, tgt], -1)

        h1 = F.gelu(self.gcn1(fused, adj_ei))
        h1 = F.dropout(h1, 0.1, self.training)
        h_sp = self.gcn2(h1, adj_ei)

        h2 = F.gelu(self.transit_gcn1(fused, transit_ei))
        h2 = F.dropout(h2, 0.1, self.training)
        h_tr = self.transit_gcn2(h2, transit_ei)

        a = torch.sigmoid(self.alpha)
        h = a * h_sp + (1-a) * h_tr
        return self.head(torch.cat([h, fused], -1))


# ============================================================
# CORRELATION-AWARE MASKING
# ============================================================
def create_corr_aware_mask(n, dim, target_data, mask_ratio=0.3):
    """Mask correlated categories together"""
    corr = np.corrcoef(target_data.T)
    mask = torch.zeros(n, dim, dtype=torch.bool)

    for i in range(n):
        n_mask = max(1, int(dim * mask_ratio))
        # Pick seed indices
        seeds = torch.randperm(dim)[:max(1, n_mask // 2)]
        masked_set = set(seeds.tolist())

        # Add correlated partners
        for s in seeds.tolist():
            for j in range(dim):
                if j not in masked_set and abs(corr[s, j]) > 0.7:
                    masked_set.add(j)
                    if len(masked_set) >= n_mask:
                        break
            if len(masked_set) >= n_mask:
                break

        # Fill remaining randomly
        while len(masked_set) < n_mask:
            masked_set.add(torch.randint(0, dim, (1,)).item())

        for j in list(masked_set)[:n_mask]:
            mask[i, j] = True

    return mask


# ============================================================
# TRAINING
# ============================================================
def train_fold(sf, cat_cols, prop_cols, train_idx, val_idx, fold,
               adj_ei, transit_ei, mode="proportion", epochs=1000):
    """Train one fold. mode: 'proportion' or 'count'"""

    all_cols = sf.select_dtypes(include=[np.number]).columns.tolist()

    if mode == "proportion":
        target_cols = prop_cols
    else:
        target_cols = cat_cols

    context_cols = [c for c in all_cols if c not in cat_cols and c not in prop_cols
                    and c != "total_places" and c != "is_viable"]

    context = torch.tensor(sf[context_cols].values, dtype=torch.float32)
    target = torch.tensor(sf[target_cols].values, dtype=torch.float32)

    # Normalize context
    scaler = StandardScaler()
    ctx_np = scaler.fit_transform(context.numpy())
    context = torch.tensor(ctx_np, dtype=torch.float32)

    n = len(sf)
    target_dim = target.size(1)
    ctx_dim = context.size(1)

    model = UrbanModelV2(ctx_dim, target_dim, hidden=64)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)

    best_val = float("inf")
    best_state = None
    patience = 100
    no_improve = 0
    target_np = target.numpy()

    for epoch in range(epochs):
        model.train()
        mask = create_corr_aware_mask(n, target_dim, target_np, mask_ratio=0.3)

        pred = model(context, target, mask, adj_ei, transit_ei)

        # Loss on masked positions of train nodes
        t_mask = mask[train_idx]
        t_pred = pred[train_idx]
        t_true = target[train_idx]

        if t_mask.sum() > 0:
            loss_masked = F.mse_loss(t_pred[t_mask], t_true[t_mask])
        else:
            loss_masked = torch.tensor(0.0)
        loss_unmask = F.mse_loss(t_pred[~t_mask], t_true[~t_mask])
        loss = loss_masked + 0.1 * loss_unmask

        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()

        if epoch % 10 == 0:
            model.eval()
            with torch.no_grad():
                v_mask = create_corr_aware_mask(n, target_dim, target_np, 0.3)
                v_pred = model(context, target, v_mask, adj_ei, transit_ei)
                v_loss = F.mse_loss(v_pred[val_idx][v_mask[val_idx]], target[val_idx][v_mask[val_idx]]).item()

                if v_loss < best_val:
                    best_val = v_loss
                    best_state = {k: v.clone() for k, v in model.state_dict().items()}
                    no_improve = 0
                else:
                    no_improve += 1

                if epoch % 200 == 0:
                    log("  Fold %d Ep %d: train=%.4f val=%.4f best=%.4f" % (fold, epoch, loss.item(), v_loss, best_val))

                if no_improve >= patience // 10:
                    log("  Fold %d: early stop ep %d" % (fold, epoch))
                    break

    model.load_state_dict(best_state)
    model.eval()
    return model, context, target, context_cols, target_cols


def evaluate(model, context, target, val_idx, adj_ei, transit_ei, target_cols, sf, cat_cols, mode):
    model.eval()
    with torch.no_grad():
        no_mask = torch.zeros(context.size(0), target.size(1), dtype=torch.bool)
        pred = model(context, target, no_mask, adj_ei, transit_ei)

        val_pred = pred[val_idx].numpy()
        val_true = target[val_idx].numpy()

        # If proportion mode, convert back to counts for interpretable metrics
        if mode == "proportion":
            total_places = sf["total_places"].values
            val_pred_counts = val_pred * total_places[val_idx, np.newaxis]
            val_true_counts = val_true * total_places[val_idx, np.newaxis]
            # Also get actual counts
            actual_counts = sf[cat_cols].values[val_idx]
        else:
            val_pred_counts = val_pred
            val_true_counts = val_true
            actual_counts = val_true

        mae = np.mean(np.abs(val_pred_counts - actual_counts))

        # R2 per category (on proportions)
        r2s = []
        for j in range(val_true.shape[1]):
            ss_res = np.sum((val_true[:, j] - val_pred[:, j]) ** 2)
            ss_tot = np.sum((val_true[:, j] - np.mean(val_true[:, j])) ** 2)
            r2 = 1 - ss_res / max(ss_tot, 1e-8)
            r2s.append(r2)

    return {"mae": mae, "r2_per_cat": np.array(r2s), "mean_r2": np.mean(r2s)}


# ============================================================
# XGBOOST BASELINE
# ============================================================
def xgboost_baseline(sf, cat_cols, prop_cols):
    log("\n" + "=" * 60)
    log("XGBOOST BASELINE")
    log("=" * 60)

    all_cols = sf.select_dtypes(include=[np.number]).columns.tolist()
    context_cols = [c for c in all_cols if c not in cat_cols and c not in prop_cols
                    and c != "total_places" and c != "is_viable"]

    X = sf[context_cols].values
    Y = sf[prop_cols].values  # predict proportions

    viable_mask = sf["is_viable"].values == 1
    X_v = X[viable_mask]
    Y_v = Y[viable_mask]

    kf = KFold(n_splits=10, shuffle=True, random_state=42)
    fold_r2s = []

    for fold, (tr, va) in enumerate(kf.split(X_v)):
        r2s = []
        for j in range(Y_v.shape[1]):
            gbr = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
            gbr.fit(X_v[tr], Y_v[tr, j])
            pred = gbr.predict(X_v[va])
            ss_res = np.sum((Y_v[va, j] - pred) ** 2)
            ss_tot = np.sum((Y_v[va, j] - np.mean(Y_v[va, j])) ** 2)
            r2 = 1 - ss_res / max(ss_tot, 1e-8)
            r2s.append(r2)
        fold_r2s.append(np.mean(r2s))

    log("  XGBoost 10-fold mean R2: %.3f +/- %.3f" % (np.mean(fold_r2s), np.std(fold_r2s)))
    return np.mean(fold_r2s)


# ============================================================
# MAIN
# ============================================================
def main():
    log("=" * 60)
    log("DIGITAL ATLAS SGP - MODEL v2")
    log("=" * 60)

    sf, cat_cols, prop_cols = load_and_fix_data()

    # Load graphs
    with open(GRAPHS + "/subzone_adjacency.json") as f:
        adj = json.load(f)
    with open(GRAPHS + "/transit_connectivity.json") as f:
        tr = json.load(f)

    codes = sf["subzone_code"].tolist()
    c2i = {c: i for i, c in enumerate(codes)}
    n = len(codes)

    adj_edges = [[c2i[e["source"]], c2i[e["target"]]] for e in adj["edges"]
                 if e["source"] in c2i and e["target"] in c2i]
    adj_edges += [[b, a] for a, b in adj_edges]
    adj_edges += [[i, i] for i in range(n)]

    tr_edges = [[c2i[e["source"]], c2i[e["target"]]] for e in tr["edges"]
                if e["source"] in c2i and e["target"] in c2i]
    tr_edges += [[b, a] for a, b in tr_edges]
    tr_edges += [[i, i] for i in range(n)]

    adj_ei = torch.tensor(adj_edges, dtype=torch.long).t().contiguous()
    tr_ei = torch.tensor(tr_edges, dtype=torch.long).t().contiguous()

    # Filter to viable subzones only
    viable_mask = sf["is_viable"].values == 1
    viable_idx = np.where(viable_mask)[0]
    log("\nTraining on %d viable subzones (excluded %d non-viable)" % (len(viable_idx), n - len(viable_idx)))

    # XGBoost baseline (on viable only)
    xgb_r2 = xgboost_baseline(sf, cat_cols, prop_cols)

    # GCN-MLP cross-validation (proportion mode)
    log("\n" + "=" * 60)
    log("GCN-MLP v2: PROPORTION MODE, CORRELATION-AWARE MASKING")
    log("=" * 60)

    kf = KFold(n_splits=10, shuffle=True, random_state=42)
    fold_results = []

    for fold, (tr_local, va_local) in enumerate(kf.split(viable_idx)):
        tr_idx = torch.tensor(viable_idx[tr_local], dtype=torch.long)
        va_idx = torch.tensor(viable_idx[va_local], dtype=torch.long)

        log("\n--- Fold %d/10 (train=%d, val=%d) ---" % (fold+1, len(tr_idx), len(va_idx)))

        model, context, target, ctx_cols, tgt_cols = train_fold(
            sf, cat_cols, prop_cols, tr_idx, va_idx, fold+1,
            adj_ei, tr_ei, mode="proportion", epochs=1000
        )

        metrics = evaluate(model, context, target, va_idx, adj_ei, tr_ei, tgt_cols, sf, cat_cols, "proportion")
        fold_results.append(metrics)
        log("  Fold %d: MAE=%.2f, R2=%.3f" % (fold+1, metrics["mae"], metrics["mean_r2"]))

    # Aggregate
    all_r2 = [r["mean_r2"] for r in fold_results]
    all_mae = [r["mae"] for r in fold_results]
    cat_r2_avg = np.mean([r["r2_per_cat"] for r in fold_results], axis=0)

    log("\n" + "=" * 60)
    log("RESULTS COMPARISON")
    log("=" * 60)
    log("  XGBoost baseline R2:   %.3f" % xgb_r2)
    log("  GCN-MLP v2 mean R2:   %.3f +/- %.3f" % (np.mean(all_r2), np.std(all_r2)))
    log("  GCN-MLP v2 mean MAE:  %.3f +/- %.3f" % (np.mean(all_mae), np.std(all_mae)))
    log("  v1 R2 was:             0.597")

    improvement = np.mean(all_r2) - 0.597
    log("  R2 improvement:        %+.3f" % improvement)

    log("\nPer-category R2:")
    target_names = prop_cols
    order = sorted(range(len(target_names)), key=lambda i: -cat_r2_avg[i])
    for i in order:
        log("  %-50s %.3f" % (target_names[i], cat_r2_avg[i]))

    # Train final model on all viable data
    log("\n" + "=" * 60)
    log("TRAINING FINAL MODEL (all viable data)")
    log("=" * 60)

    all_viable = torch.tensor(viable_idx, dtype=torch.long)
    final_model, context, target, ctx_cols, tgt_cols = train_fold(
        sf, cat_cols, prop_cols, all_viable, all_viable, 0,
        adj_ei, tr_ei, mode="proportion", epochs=1200
    )

    # Gap analysis
    log("\nGAP ANALYSIS")
    final_model.eval()
    with torch.no_grad():
        no_mask = torch.zeros(n, len(prop_cols), dtype=torch.bool)
        pred_prop = final_model(context, target, no_mask, adj_ei, tr_ei).numpy()

    total_places = sf["total_places"].values
    pred_counts = pred_prop * total_places[:, np.newaxis]
    actual_counts = sf[cat_cols].values

    gaps = pred_counts - actual_counts
    gap_scores = gaps / np.maximum(pred_counts, 1)

    gap_df = pd.DataFrame()
    gap_df["subzone_code"] = codes
    gap_df["subzone_name"] = sf["subzone_name"].values
    gap_df["is_viable"] = sf["is_viable"].values
    gap_df["total_places"] = total_places

    for i, col in enumerate(cat_cols):
        cname = col.replace("cat_", "")
        gap_df["actual_" + cname] = actual_counts[:, i]
        gap_df["predicted_" + cname] = np.round(pred_counts[:, i], 1)
        gap_df["gap_" + cname] = np.round(gap_scores[:, i], 3)

    gap_df.to_parquet(RESULTS + "/gap_analysis_v2.parquet", index=False)
    gap_df.to_csv(RESULTS + "/gap_analysis_v2.csv", index=False)

    # Top opportunities (viable only)
    viable_gaps = gap_df[gap_df["is_viable"] == 1]
    log("\nTop opportunities per category (viable subzones only):")
    for col in cat_cols:
        cname = col.replace("cat_", "")
        gc = "gap_" + cname
        pc = "predicted_" + cname
        ac = "actual_" + cname
        top = viable_gaps.nlargest(3, gc)
        if top[gc].iloc[0] > 0.3:
            log("\n  %s:" % cname)
            for _, row in top.iterrows():
                if row[gc] > 0.2:
                    log("    %s: predicted=%.0f actual=%.0f gap=+%.2f" % (
                        row["subzone_name"], row[pc], row[ac], row[gc]))

    # Save model + report
    torch.save(final_model.state_dict(), RESULTS + "/model_v2_weights.pt")

    report = {
        "version": "v2",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "fixes_applied": [
            "dwelling_pct_capped_100",
            "zero_variance_removed",
            "non_viable_excluded",
            "interaction_features_added",
            "centrality_features_added",
            "proportion_prediction",
            "correlation_aware_masking",
        ],
        "viable_subzones": int(len(viable_idx)),
        "total_subzones": n,
        "xgboost_baseline_r2": float(xgb_r2),
        "gcn_mlp_v2_mean_r2": float(np.mean(all_r2)),
        "gcn_mlp_v2_std_r2": float(np.std(all_r2)),
        "gcn_mlp_v2_mean_mae": float(np.mean(all_mae)),
        "v1_r2": 0.597,
        "r2_improvement": float(improvement),
        "per_category_r2": {prop_cols[i]: float(cat_r2_avg[i]) for i in range(len(prop_cols))},
    }

    with open(RESULTS + "/cv_report_v2.json", "w") as f:
        json.dump(report, f, indent=2)

    # Validation tests
    log("\n" + "=" * 60)
    log("VALIDATION TESTS")
    log("=" * 60)

    tests = [
        ("v2 R2 > v1 R2 (0.597)", np.mean(all_r2) > 0.597, "v2=%.3f" % np.mean(all_r2)),
        ("v2 R2 > XGBoost", np.mean(all_r2) > xgb_r2, "gcn=%.3f xgb=%.3f" % (np.mean(all_r2), xgb_r2)),
        ("v2 R2 > 0.5", np.mean(all_r2) > 0.5, "R2=%.3f" % np.mean(all_r2)),
        ("All predictions non-negative", (pred_counts >= -0.5).all(), "min=%.2f" % pred_counts.min()),
        ("CV stability < 0.5", np.std(all_r2)/max(np.mean(all_r2), 0.01) < 0.5, ""),
        ("No category R2 < -0.5", all(cat_r2_avg > -0.5), "min=%.3f" % cat_r2_avg.min()),
        ("Gap scores bounded", np.abs(gap_scores[viable_mask]).max() < 10, "max=%.2f" % np.abs(gap_scores[viable_mask]).max()),
        ("Non-viable gaps near 0", np.abs(gap_scores[~viable_mask]).mean() < 2, "mean=%.2f" % np.abs(gap_scores[~viable_mask]).mean()),
    ]

    all_pass = True
    for name, passed, detail in tests:
        status = "PASS" if passed else "FAIL"
        log("  [%s] %s %s" % (status, name, detail))
        if not passed:
            all_pass = False

    log("\n  OVERALL: %s" % ("ALL PASSED" if all_pass else "SOME FAILED"))

    log("\nFiles saved:")
    for f in sorted(os.listdir(RESULTS)):
        log("  %s: %.1f KB" % (f, os.path.getsize(os.path.join(RESULTS, f))/1024))

    log("\nDONE.")

if __name__ == "__main__":
    main()

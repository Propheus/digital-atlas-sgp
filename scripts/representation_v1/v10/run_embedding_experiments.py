"""
Urban Region Embedding — Full Experimental Ladder
Run ON SERVER: python3 run_embedding_experiments.py

Methods (each adds ONE innovation):
  0. Raw features (460-dim) — baseline
  1. PCA-32 — linear compression
  2. Standard AE-32 — non-linear compression
  3. Masked AE-32 — random 30% feature masking (VIME-style)
  4. Multi-View MAE-32 — thematic face masking
  5. MV-MAE-32 + Multi-task — per-face decoders + category head

Evaluation (identical across ALL methods):
  T1: kNN PA accuracy (k=5)
  T2: Category count prediction R² (Ridge, 80/20 split)
  T3: Cross-view R² (infrastructure → commerce, methods 4-5 only)
  T4: Cluster AMI (k=8 vs PA labels)
  T5: Structural twin check (Sentosa→MBS, Bedok→heartlands)

Output:
  /home/azureuser/digital-atlas-sgp/data/hex_v10/embedding_experiments.json
  /home/azureuser/digital-atlas-sgp/data/hex_v10/embeddings/*.parquet
"""
import json
import os
import time
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_mutual_info_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = "/home/azureuser/digital-atlas-sgp"
HEX_PATH = f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet"
HEX_RAW = f"{ROOT}/data/hex_v10/hex_features_v10.parquet"
OUT_DIR = f"{ROOT}/data/hex_v10/embeddings"
OUT_JSON = f"{ROOT}/data/hex_v10/embedding_experiments.json"

os.makedirs(OUT_DIR, exist_ok=True)

EMBED_DIM = 32
SEED = 42
DEVICE = "cpu"

# =====================================================================
# DATA LOADING + FACE DEFINITIONS
# =====================================================================

ID_COLS = {"hex_id", "lat", "lng", "area_km2", "parent_subzone",
           "parent_subzone_name", "parent_pa", "parent_region"}
BK_COLS = {"subzone_pop_total", "subzone_res_floor_area", "residential_floor_weight"}

# Face definitions (column name prefixes/exact names → face label)
def assign_face(c):
    if c.startswith("bldg_") or c in {"avg_floors", "max_floors", "avg_height", "max_height",
                                       "hdb_blocks", "total_floor_area_sqm",
                                       "residential_floor_area_sqm", "commercial_floor_area_sqm"}:
        return "built"
    if c in {"population", "children_count", "elderly_count", "working_age_count",
             "walking_dependent_count", "population_nonresident", "population_total",
             "tourist_draw_est", "daytime_ratio"}:
        return "people"
    if c in {"mrt_stations", "lrt_stations", "bus_stops", "mrt_daily_taps", "bus_daily_taps",
             "transit_daily_taps", "mrt_hex_rings", "carpark_count", "carpark_lots",
             "taxi_snapshot", "pcn_segments"} or c.startswith("road_cat_") or c.startswith("sig_") or \
       c.startswith("ped_") or c.startswith("hex_") or c == "bicycle_signal" or \
       "walkability" in c or c == "amenity_types_nearby" or \
       (c.startswith("walk_") and not c.startswith("walking")) or \
       (c.startswith("dist_") and c.endswith("_m")):
        return "access"
    if c.startswith("lu_") or c == "avg_gpr" or c.startswith("gap_") or c == "ura_development_gap":
        return "zoning"
    if c.startswith("pc_"):
        return "commerce"
    if c.startswith("mg_"):
        return "spatial"
    if c.startswith("sp_") or c.startswith("tr_"):
        return "influence"
    if c in {"hawker_centres", "chas_clinics", "preschools_gov", "hotels", "tourist_attractions",
             "sfa_eating_establishments", "silver_zones", "school_zones", "park_facilities",
             "formal_schools", "schools_primary", "schools_secondary", "supermarkets", "parks_nature"}:
        return "access"  # government amenities → access face
    return "other"


def load_data():
    print("Loading data...")
    norm = pd.read_parquet(HEX_PATH)
    raw = pd.read_parquet(HEX_RAW)
    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]

    X = norm[feat_cols].to_numpy(dtype=np.float32)
    # remove constant columns
    stds = X.std(axis=0)
    keep = stds > 1e-9
    X = X[:, keep]
    feat_kept = [c for c, k in zip(feat_cols, keep) if k]

    # Face indices
    faces = {}
    for i, c in enumerate(feat_kept):
        f = assign_face(c)
        faces.setdefault(f, []).append(i)

    # Labels for evaluation
    pas = raw["parent_pa"].to_numpy(dtype=str)
    hex_ids = raw["hex_id"].to_numpy(dtype=str)
    active = raw["pc_total"].to_numpy() > 0

    # Category counts for Task 2 (from raw features)
    cat_cols = [c for c in raw.columns if c.startswith("pc_cat_") and
                c not in {"pc_cat_hhi", "pc_cat_entropy"}]
    Y_cats = raw[cat_cols].to_numpy(dtype=np.float32)

    # Train/val/test split
    np.random.seed(SEED)
    idx = np.arange(len(X))
    train_idx, test_idx = train_test_split(idx, test_size=0.2, random_state=SEED)
    train_idx, val_idx = train_test_split(train_idx, test_size=0.125, random_state=SEED)

    print(f"  Features: {X.shape[1]}  Faces: {sorted(faces.keys())}")
    for f, idxs in sorted(faces.items()):
        print(f"    {f:<12} {len(idxs):>4} dims")
    print(f"  Train: {len(train_idx)}  Val: {len(val_idx)}  Test: {len(test_idx)}")

    return {
        "X": X, "feat_kept": feat_kept, "faces": faces,
        "pas": pas, "hex_ids": hex_ids, "active": active,
        "Y_cats": Y_cats, "cat_cols": cat_cols,
        "train_idx": train_idx, "val_idx": val_idx, "test_idx": test_idx,
    }


# =====================================================================
# EVALUATION (shared across all methods)
# =====================================================================

def evaluate(Z, data, method_name):
    """Evaluate a 32-dim (or any-dim) embedding on all 5 tasks."""
    pas = data["pas"]
    active = data["active"]
    Y_cats = data["Y_cats"]
    train_idx = data["train_idx"]
    test_idx = data["test_idx"]
    hex_ids = data["hex_ids"]

    results = {"method": method_name, "dims": Z.shape[1]}

    # T1: kNN PA accuracy
    Za = Z[active]
    pa_a = pas[active]
    norms = np.linalg.norm(Za, axis=1, keepdims=True)
    norms[norms < 1e-9] = 1
    Zn = Za / norms
    sims = Zn @ Zn.T
    np.fill_diagonal(sims, -1)
    correct = total = 0
    for i in range(len(Za)):
        top5 = np.argsort(-sims[i])[:5]
        correct += sum(1 for j in top5 if pa_a[j] == pa_a[i])
        total += 5
    results["t1_knn_pa"] = round(correct / total, 4)

    # T2: Category count prediction
    X_tr, X_te = Z[train_idx], Z[test_idx]
    Y_tr, Y_te = Y_cats[train_idx], Y_cats[test_idx]
    r2s = []
    for j in range(Y_cats.shape[1]):
        model = Ridge(alpha=1.0)
        model.fit(X_tr, Y_tr[:, j])
        pred = model.predict(X_te)
        ss_res = ((Y_te[:, j] - pred) ** 2).sum()
        ss_tot = ((Y_te[:, j] - Y_te[:, j].mean()) ** 2).sum()
        r2 = 1 - ss_res / (ss_tot + 1e-9)
        r2s.append(r2)
    results["t2_cat_r2_mean"] = round(float(np.mean(r2s)), 4)
    results["t2_cat_r2_std"] = round(float(np.std(r2s)), 4)

    # T4: Cluster AMI
    km = KMeans(n_clusters=8, random_state=SEED, n_init=10).fit(Z[active])
    cluster_labels = km.labels_
    # PA → numeric label
    pa_unique = list(set(pa_a))
    pa_num = np.array([pa_unique.index(p) for p in pa_a])
    ami = adjusted_mutual_info_score(pa_num, cluster_labels)
    results["t4_cluster_ami"] = round(float(ami), 4)

    # T5: Structural twins
    raw_df = pd.read_parquet(HEX_RAW)
    # Sentosa
    sentosa_hex = raw_df[raw_df["parent_subzone"] == "SISZ01"].nlargest(1, "pc_total")["hex_id"].iloc[0]
    si = np.where(hex_ids == sentosa_hex)[0]
    if len(si):
        si = si[0]
        s = Z @ Z[si] / (np.linalg.norm(Z, axis=1) * np.linalg.norm(Z[si]) + 1e-9)
        top10 = np.argsort(-s)[1:11]
        top_pas = [pas[j] for j in top10]
        results["t5_sentosa_mbs"] = "DOWNTOWN CORE" in top_pas
        results["t5_sentosa_top"] = top_pas[:5]

    # Bedok
    bedok_hex = raw_df[(raw_df["parent_pa"] == "BEDOK") & (raw_df["hdb_blocks"] > 10)].nlargest(1, "population")["hex_id"].iloc[0]
    bi = np.where(hex_ids == bedok_hex)[0]
    if len(bi):
        bi = bi[0]
        s = Z @ Z[bi] / (np.linalg.norm(Z, axis=1) * np.linalg.norm(Z[bi]) + 1e-9)
        top10 = np.argsort(-s)[1:11]
        top_pas = [pas[j] for j in top10]
        unique_pas = len(set(top_pas))
        results["t5_bedok_unique_pas"] = unique_pas
        results["t5_bedok_top"] = top_pas[:5]

    return results


# =====================================================================
# METHOD 0: RAW FEATURES
# =====================================================================

def method_raw(data):
    print("\n=== Method 0: Raw Features ===")
    Z = data["X"]
    results = evaluate(Z, data, "raw_features")
    results["dims"] = Z.shape[1]
    return Z, results


# =====================================================================
# METHOD 1: PCA
# =====================================================================

def method_pca(data):
    print("\n=== Method 1: PCA-32 ===")
    pca = PCA(n_components=EMBED_DIM, random_state=SEED)
    Z = pca.fit_transform(data["X"])
    results = evaluate(Z, data, "pca_32")
    results["explained_var"] = round(float(pca.explained_variance_ratio_.sum()), 4)
    return Z, results


# =====================================================================
# METHOD 2: STANDARD AE
# =====================================================================

class StandardAE(nn.Module):
    def __init__(self, input_dim, embed_dim=32):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, embed_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(embed_dim, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, input_dim),
        )

    def forward(self, x):
        z = self.encoder(x)
        recon = self.decoder(z)
        return recon, z


def train_ae(model, X_train, X_val, epochs=500, lr=1e-3, patience=50, mask_rate=0.0, face_mask_fn=None):
    """Generic AE trainer with optional masking."""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=20, factor=0.5)

    X_tr = torch.tensor(X_train, dtype=torch.float32)
    X_vl = torch.tensor(X_val, dtype=torch.float32)
    train_ds = TensorDataset(X_tr)
    train_dl = DataLoader(train_ds, batch_size=256, shuffle=True)

    best_val = float("inf")
    patience_counter = 0
    best_state = None

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for (batch,) in train_dl:
            # Apply masking
            if face_mask_fn is not None:
                masked_batch = face_mask_fn(batch)
            elif mask_rate > 0:
                mask = (torch.rand_like(batch) > mask_rate).float()
                masked_batch = batch * mask
            else:
                masked_batch = batch

            recon, z = model(masked_batch)
            loss = nn.MSELoss()(recon, batch)  # reconstruct ORIGINAL from masked
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(batch)

        # Validation
        model.eval()
        with torch.no_grad():
            recon_val, _ = model(X_vl)
            val_loss = nn.MSELoss()(recon_val, X_vl).item()

        scheduler.step(val_loss)

        if val_loss < best_val:
            best_val = val_loss
            patience_counter = 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    model.load_state_dict(best_state)
    return model, best_val


def method_standard_ae(data):
    print("\n=== Method 2: Standard AE-32 ===")
    X = data["X"]
    model = StandardAE(X.shape[1], EMBED_DIM)
    model, val_loss = train_ae(model, X[data["train_idx"]], X[data["val_idx"]])
    model.eval()
    with torch.no_grad():
        _, Z = model(torch.tensor(X, dtype=torch.float32))
        Z = Z.numpy()
    results = evaluate(Z, data, "ae_32")
    results["val_loss"] = round(val_loss, 6)
    # Reconstruction R²
    with torch.no_grad():
        recon, _ = model(torch.tensor(X, dtype=torch.float32))
        recon = recon.numpy()
    ss_res = ((X - recon) ** 2).sum()
    ss_tot = ((X - X.mean(axis=0)) ** 2).sum()
    results["recon_r2"] = round(float(1 - ss_res / ss_tot), 4)
    pd.DataFrame(Z, columns=[f"e{i}" for i in range(EMBED_DIM)]).to_parquet(f"{OUT_DIR}/ae_32.parquet", index=False)
    return Z, results


# =====================================================================
# METHOD 3: MASKED AE (random 30% feature masking)
# =====================================================================

def method_masked_ae(data):
    print("\n=== Method 3: Masked AE-32 (random 30%) ===")
    X = data["X"]
    model = StandardAE(X.shape[1], EMBED_DIM)
    model, val_loss = train_ae(model, X[data["train_idx"]], X[data["val_idx"]], mask_rate=0.3)
    model.eval()
    with torch.no_grad():
        _, Z = model(torch.tensor(X, dtype=torch.float32))
        Z = Z.numpy()
    results = evaluate(Z, data, "masked_ae_32")
    results["val_loss"] = round(val_loss, 6)
    with torch.no_grad():
        recon, _ = model(torch.tensor(X, dtype=torch.float32))
        recon = recon.numpy()
    ss_res = ((X - recon) ** 2).sum()
    ss_tot = ((X - X.mean(axis=0)) ** 2).sum()
    results["recon_r2"] = round(float(1 - ss_res / ss_tot), 4)
    pd.DataFrame(Z, columns=[f"e{i}" for i in range(EMBED_DIM)]).to_parquet(f"{OUT_DIR}/masked_ae_32.parquet", index=False)
    return Z, results


# =====================================================================
# METHOD 4: MULTI-VIEW MAE (thematic face masking)
# =====================================================================

def method_mv_mae(data):
    print("\n=== Method 4: Multi-View MAE-32 ===")
    X = data["X"]
    faces = data["faces"]
    face_names = sorted(faces.keys())

    def face_mask_fn(batch):
        """Randomly mask 1-2 entire faces."""
        masked = batch.clone()
        n_mask = np.random.randint(1, min(3, len(face_names)))
        to_mask = np.random.choice(face_names, n_mask, replace=False)
        for f in to_mask:
            for idx in faces[f]:
                masked[:, idx] = 0
        return masked

    model = StandardAE(X.shape[1], EMBED_DIM)
    model, val_loss = train_ae(model, X[data["train_idx"]], X[data["val_idx"]], face_mask_fn=face_mask_fn)
    model.eval()
    with torch.no_grad():
        _, Z = model(torch.tensor(X, dtype=torch.float32))
        Z = Z.numpy()
    results = evaluate(Z, data, "mv_mae_32")
    results["val_loss"] = round(val_loss, 6)

    # Reconstruction R²
    with torch.no_grad():
        recon, _ = model(torch.tensor(X, dtype=torch.float32))
        recon = recon.numpy()
    ss_res = ((X - recon) ** 2).sum()
    ss_tot = ((X - X.mean(axis=0)) ** 2).sum()
    results["recon_r2"] = round(float(1 - ss_res / ss_tot), 4)

    # T3: Cross-view prediction (infrastructure → commerce)
    infra_faces = ["built", "people", "access", "zoning"]
    infra_idx = []
    for f in infra_faces:
        infra_idx.extend(faces.get(f, []))
    commerce_faces = ["commerce", "spatial"]
    commerce_idx = []
    for f in commerce_faces:
        commerce_idx.extend(faces.get(f, []))

    X_infra_only = np.zeros_like(X)
    for i in infra_idx:
        X_infra_only[:, i] = X[:, i]
    # Also include influence features that are about physical infrastructure
    for i in faces.get("influence", []):
        X_infra_only[:, i] = X[:, i]

    with torch.no_grad():
        recon_from_infra, _ = model(torch.tensor(X_infra_only, dtype=torch.float32))
        recon_from_infra = recon_from_infra.numpy()

    # R² on commerce features only
    actual_commerce = X[:, commerce_idx]
    pred_commerce = recon_from_infra[:, commerce_idx]
    ss_res_cv = ((actual_commerce - pred_commerce) ** 2).sum()
    ss_tot_cv = ((actual_commerce - actual_commerce.mean(axis=0)) ** 2).sum()
    results["t3_cross_view_r2"] = round(float(1 - ss_res_cv / ss_tot_cv), 4)

    pd.DataFrame(Z, columns=[f"e{i}" for i in range(EMBED_DIM)]).to_parquet(f"{OUT_DIR}/mv_mae_32.parquet", index=False)
    return Z, results, model


# =====================================================================
# METHOD 5: MV-MAE + MULTI-TASK
# =====================================================================

class MultiTaskAE(nn.Module):
    def __init__(self, input_dim, embed_dim, faces, n_cats=24):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, embed_dim),
        )
        # Per-face decoders
        self.decoders = nn.ModuleDict()
        for face_name, face_idx in faces.items():
            n = len(face_idx)
            self.decoders[face_name] = nn.Sequential(
                nn.Linear(embed_dim, 64), nn.ReLU(), nn.Dropout(0.2),
                nn.Linear(64, n),
            )
        # Category distribution head
        self.cat_head = nn.Sequential(
            nn.Linear(embed_dim, 32), nn.ReLU(),
            nn.Linear(32, n_cats), nn.Softmax(dim=1),
        )
        self.faces = faces

    def forward(self, x):
        z = self.encoder(x)
        recons = {}
        for face_name, decoder in self.decoders.items():
            recons[face_name] = decoder(z)
        cat_pred = self.cat_head(z)
        return recons, cat_pred, z


def method_mv_mae_mt(data):
    print("\n=== Method 5: MV-MAE-32 + Multi-task ===")
    X = data["X"]
    faces = data["faces"]
    face_names = sorted(faces.keys())

    # Category distribution target (from raw pc_pct_cat_* columns)
    raw = pd.read_parquet(HEX_RAW)
    cat_pct_cols = sorted([c for c in raw.columns if c.startswith("pc_pct_cat_")])[:24]
    Y_cat_dist = raw[cat_pct_cols].to_numpy(dtype=np.float32)
    # Normalize to sum=1
    row_sums = Y_cat_dist.sum(axis=1, keepdims=True)
    row_sums[row_sums < 1e-9] = 1
    Y_cat_dist = Y_cat_dist / row_sums

    model = MultiTaskAE(X.shape[1], EMBED_DIM, faces, n_cats=len(cat_pct_cols))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=20, factor=0.5)

    X_tr = torch.tensor(X[data["train_idx"]], dtype=torch.float32)
    X_vl = torch.tensor(X[data["val_idx"]], dtype=torch.float32)
    Y_tr = torch.tensor(Y_cat_dist[data["train_idx"]], dtype=torch.float32)
    Y_vl = torch.tensor(Y_cat_dist[data["val_idx"]], dtype=torch.float32)

    train_ds = TensorDataset(X_tr, Y_tr)
    train_dl = DataLoader(train_ds, batch_size=256, shuffle=True)

    best_val = float("inf")
    patience_counter = 0
    best_state = None

    for epoch in range(500):
        model.train()
        for batch_x, batch_y in train_dl:
            # Face masking
            masked = batch_x.clone()
            n_mask = np.random.randint(1, min(3, len(face_names)))
            to_mask = np.random.choice(face_names, n_mask, replace=False)
            for f in to_mask:
                for idx in faces[f]:
                    masked[:, idx] = 0

            recons, cat_pred, z = model(masked)

            # Per-face reconstruction loss (against ORIGINAL)
            loss = 0
            for face_name, face_idx in faces.items():
                target = batch_x[:, face_idx]
                loss += nn.MSELoss()(recons[face_name], target)

            # Category distribution loss
            cat_loss = nn.KLDivLoss(reduction="batchmean")(
                torch.log(cat_pred + 1e-9), batch_y
            )
            loss += 0.5 * cat_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            recons_v, cat_v, _ = model(X_vl)
            val_loss = sum(
                nn.MSELoss()(recons_v[f], X_vl[:, faces[f]]).item()
                for f in faces
            )
        scheduler.step(val_loss)

        if val_loss < best_val:
            best_val = val_loss
            patience_counter = 0
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= 50:
                break

    model.load_state_dict(best_state)
    model.eval()

    with torch.no_grad():
        X_t = torch.tensor(X, dtype=torch.float32)
        _, _, Z = model(X_t)
        Z = Z.numpy()

    results = evaluate(Z, data, "mv_mae_mt_32")
    results["val_loss"] = round(best_val, 6)

    # Reconstruction R² (full)
    with torch.no_grad():
        recons, _, _ = model(X_t)
    recon_full = np.zeros_like(X)
    for face_name, face_idx in faces.items():
        recon_full[:, face_idx] = recons[face_name].numpy()
    ss_res = ((X - recon_full) ** 2).sum()
    ss_tot = ((X - X.mean(axis=0)) ** 2).sum()
    results["recon_r2"] = round(float(1 - ss_res / ss_tot), 4)

    # Cross-view (infrastructure → commerce)
    infra_faces = ["built", "people", "access", "zoning", "influence"]
    commerce_faces = ["commerce", "spatial"]
    X_infra = np.zeros_like(X)
    for f in infra_faces:
        for i in faces.get(f, []):
            X_infra[:, i] = X[:, i]
    with torch.no_grad():
        recons_cv, _, _ = model(torch.tensor(X_infra, dtype=torch.float32))
    commerce_idx = []
    for f in commerce_faces:
        commerce_idx.extend(faces.get(f, []))
    actual = X[:, commerce_idx]
    predicted = np.concatenate([recons_cv[f].numpy() for f in commerce_faces], axis=1)
    ss_res_cv = ((actual - predicted) ** 2).sum()
    ss_tot_cv = ((actual - actual.mean(axis=0)) ** 2).sum()
    results["t3_cross_view_r2"] = round(float(1 - ss_res_cv / ss_tot_cv), 4)

    pd.DataFrame(Z, columns=[f"e{i}" for i in range(EMBED_DIM)]).to_parquet(f"{OUT_DIR}/mv_mae_mt_32.parquet", index=False)
    return Z, results


# =====================================================================
# MAIN
# =====================================================================

def main():
    t0 = time.time()
    data = load_data()
    all_results = []

    # Method 0: Raw
    _, r0 = method_raw(data)
    all_results.append(r0)
    print(f"  kNN={r0['t1_knn_pa']}  CatR2={r0['t2_cat_r2_mean']}  AMI={r0['t4_cluster_ami']}")

    # Method 1: PCA
    Z1, r1 = method_pca(data)
    all_results.append(r1)
    print(f"  kNN={r1['t1_knn_pa']}  CatR2={r1['t2_cat_r2_mean']}  AMI={r1['t4_cluster_ami']}  ExpVar={r1['explained_var']}")
    pd.DataFrame(Z1, columns=[f"e{i}" for i in range(EMBED_DIM)]).to_parquet(f"{OUT_DIR}/pca_32.parquet", index=False)

    # Method 2: Standard AE
    Z2, r2 = method_standard_ae(data)
    all_results.append(r2)
    print(f"  kNN={r2['t1_knn_pa']}  CatR2={r2['t2_cat_r2_mean']}  AMI={r2['t4_cluster_ami']}  ReconR2={r2['recon_r2']}")

    # Method 3: Masked AE
    Z3, r3 = method_masked_ae(data)
    all_results.append(r3)
    print(f"  kNN={r3['t1_knn_pa']}  CatR2={r3['t2_cat_r2_mean']}  AMI={r3['t4_cluster_ami']}  ReconR2={r3['recon_r2']}")

    # Method 4: MV-MAE
    Z4, r4, mv_model = method_mv_mae(data)
    all_results.append(r4)
    print(f"  kNN={r4['t1_knn_pa']}  CatR2={r4['t2_cat_r2_mean']}  AMI={r4['t4_cluster_ami']}  ReconR2={r4['recon_r2']}  CrossView={r4['t3_cross_view_r2']}")

    # Method 5: MV-MAE + MT
    Z5, r5 = method_mv_mae_mt(data)
    all_results.append(r5)
    print(f"  kNN={r5['t1_knn_pa']}  CatR2={r5['t2_cat_r2_mean']}  AMI={r5['t4_cluster_ami']}  ReconR2={r5['recon_r2']}  CrossView={r5['t3_cross_view_r2']}")

    # Summary table
    print("\n" + "=" * 90)
    print(f"{'Method':<25} {'Dims':>5} {'kNN PA':>8} {'Cat R²':>8} {'Recon R²':>9} {'CrossView':>10} {'AMI':>6} {'MBS?':>5}")
    print("-" * 90)
    for r in all_results:
        mbs = "✓" if r.get("t5_sentosa_mbs") else ("✗" if "t5_sentosa_mbs" in r else "—")
        print(f"{r['method']:<25} {r['dims']:>5} {r['t1_knn_pa']:>8.3f} {r['t2_cat_r2_mean']:>8.3f} "
              f"{r.get('recon_r2', 'N/A'):>9} {r.get('t3_cross_view_r2', 'N/A'):>10} "
              f"{r['t4_cluster_ami']:>6.3f} {mbs:>5}")

    with open(OUT_JSON, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nWrote {OUT_JSON}")
    print(f"Total time: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

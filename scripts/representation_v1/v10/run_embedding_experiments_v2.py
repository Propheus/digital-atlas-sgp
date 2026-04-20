"""
Urban Region Embedding — Experiment Round 2
Run ON SERVER: python3 run_embedding_experiments_v2.py

Round 1 finding: 32-dim bottleneck too aggressive. PCA beats neural methods.
Round 2 tests:
  6. PCA-64 — is 32 too small?
  7. PCA-128 — how much does more capacity help?
  8. AE-64 — non-linear at 64 dims
  9. AE-128 — non-linear at 128 dims
  10. MV-MAE-64 — thematic masking at 64
  11. Contrastive (SimCLR-style) — 32-dim, similarity-optimized
  12. Contrastive-64 — same at 64 dims
  13. Raw features + UMAP-32 — non-linear manifold baseline

Also re-evaluate: raw features at 460 dims as the absolute ceiling.
"""
import json, os, time, warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_mutual_info_score
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = "/home/azureuser/digital-atlas-sgp"
HEX_NORM = f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet"
HEX_RAW = f"{ROOT}/data/hex_v10/hex_features_v10.parquet"
OUT_DIR = f"{ROOT}/data/hex_v10/embeddings"
OUT_JSON = f"{ROOT}/data/hex_v10/embedding_experiments_v2.json"
os.makedirs(OUT_DIR, exist_ok=True)
SEED = 42
DEVICE = "cpu"

ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
BK_COLS = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}

def assign_face(c):
    if c.startswith("bldg_") or c in {"avg_floors","max_floors","avg_height","max_height","hdb_blocks","total_floor_area_sqm","residential_floor_area_sqm","commercial_floor_area_sqm"}: return "built"
    if c in {"population","children_count","elderly_count","working_age_count","walking_dependent_count","population_nonresident","population_total","tourist_draw_est","daytime_ratio"}: return "people"
    if c.startswith("road_cat_") or c.startswith("sig_") or c.startswith("ped_") or c.startswith("hex_") or c=="bicycle_signal" or "walkability" in c or c=="amenity_types_nearby" or (c.startswith("walk_") and not c.startswith("walking")) or (c.startswith("dist_") and c.endswith("_m")) or c in {"mrt_stations","lrt_stations","bus_stops","mrt_daily_taps","bus_daily_taps","transit_daily_taps","mrt_hex_rings","carpark_count","carpark_lots","taxi_snapshot","pcn_segments","hawker_centres","chas_clinics","preschools_gov","hotels","tourist_attractions","sfa_eating_establishments","silver_zones","school_zones","park_facilities","formal_schools","schools_primary","schools_secondary","supermarkets","parks_nature"}: return "access"
    if c.startswith("lu_") or c=="avg_gpr" or c.startswith("gap_") or c=="ura_development_gap": return "zoning"
    if c.startswith("pc_"): return "commerce"
    if c.startswith("mg_"): return "spatial"
    if c.startswith("sp_") or c.startswith("tr_"): return "influence"
    return "other"

def load_data():
    print("Loading...")
    norm = pd.read_parquet(HEX_NORM)
    raw = pd.read_parquet(HEX_RAW)
    feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK_COLS]
    X = norm[feat_cols].to_numpy(dtype=np.float32)
    stds = X.std(axis=0); keep = stds > 1e-9; X = X[:, keep]
    feat_kept = [c for c, k in zip(feat_cols, keep) if k]
    faces = {}
    for i, c in enumerate(feat_kept):
        f = assign_face(c); faces.setdefault(f, []).append(i)
    pas = raw["parent_pa"].to_numpy(dtype=str)
    hex_ids = raw["hex_id"].to_numpy(dtype=str)
    active = raw["pc_total"].to_numpy() > 0
    cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and c not in {"pc_cat_hhi","pc_cat_entropy"}])
    Y_cats = raw[cat_cols].to_numpy(dtype=np.float32)
    idx = np.arange(len(X))
    train_idx, test_idx = train_test_split(idx, test_size=0.2, random_state=SEED)
    train_idx, val_idx = train_test_split(train_idx, test_size=0.125, random_state=SEED)
    print(f"  {X.shape[1]} features, {len(train_idx)} train, {len(val_idx)} val, {len(test_idx)} test")
    return {"X": X, "feat_kept": feat_kept, "faces": faces, "pas": pas, "hex_ids": hex_ids,
            "active": active, "Y_cats": Y_cats, "cat_cols": cat_cols,
            "train_idx": train_idx, "val_idx": val_idx, "test_idx": test_idx}

def evaluate(Z, data, name):
    pas, active, Y_cats = data["pas"], data["active"], data["Y_cats"]
    train_idx, test_idx, hex_ids = data["train_idx"], data["test_idx"], data["hex_ids"]
    r = {"method": name, "dims": Z.shape[1]}
    # T1: kNN PA
    Za = Z[active]; pa_a = pas[active]
    norms = np.linalg.norm(Za, axis=1, keepdims=True); norms[norms<1e-9]=1
    Zn = Za/norms; sims = Zn@Zn.T; np.fill_diagonal(sims,-1)
    c=t=0
    for i in range(len(Za)):
        top5 = np.argsort(-sims[i])[:5]; c+=sum(1 for j in top5 if pa_a[j]==pa_a[i]); t+=5
    r["t1_knn_pa"] = round(c/t, 4)
    # T2: Cat R²
    r2s = []
    for j in range(Y_cats.shape[1]):
        m = Ridge(alpha=1.0).fit(Z[train_idx], Y_cats[train_idx, j])
        pred = m.predict(Z[test_idx]); y = Y_cats[test_idx, j]
        ss_res = ((y-pred)**2).sum(); ss_tot = ((y-y.mean())**2).sum()
        r2s.append(1 - ss_res/(ss_tot+1e-9))
    r["t2_cat_r2"] = round(float(np.mean(r2s)), 4)
    # T4: AMI
    km = KMeans(8, random_state=SEED, n_init=10).fit(Z[active])
    pa_u = list(set(pa_a)); pa_n = np.array([pa_u.index(p) for p in pa_a])
    r["t4_ami"] = round(float(adjusted_mutual_info_score(pa_n, km.labels_)), 4)
    # T5: Sentosa→MBS
    raw_df = pd.read_parquet(HEX_RAW)
    sh = raw_df[raw_df["parent_subzone"]=="SISZ01"].nlargest(1,"pc_total")["hex_id"].iloc[0]
    si = np.where(hex_ids==sh)[0]
    if len(si):
        si=si[0]; s=Z@Z[si]/(np.linalg.norm(Z,axis=1)*np.linalg.norm(Z[si])+1e-9)
        r["t5_mbs"] = "DOWNTOWN CORE" in [pas[j] for j in np.argsort(-s)[1:11]]
    return r

# ============= AE ARCHITECTURE =============
class AE(nn.Module):
    def __init__(self, d_in, d_emb):
        super().__init__()
        h1 = min(256, max(d_emb*4, 128))
        h2 = min(128, max(d_emb*2, 64))
        self.enc = nn.Sequential(
            nn.Linear(d_in, h1), nn.BatchNorm1d(h1), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(h1, h2), nn.BatchNorm1d(h2), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(h2, d_emb))
        self.dec = nn.Sequential(
            nn.Linear(d_emb, h2), nn.BatchNorm1d(h2), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(h2, h1), nn.BatchNorm1d(h1), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(h1, d_in))
    def forward(self, x):
        z = self.enc(x); return self.dec(z), z
    def encode(self, x):
        return self.enc(x)

def train_ae(model, X_tr, X_vl, epochs=500, lr=1e-3, mask_rate=0.0, face_mask_fn=None):
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=20, factor=0.5)
    Xt = torch.tensor(X_tr, dtype=torch.float32); Xv = torch.tensor(X_vl, dtype=torch.float32)
    dl = DataLoader(TensorDataset(Xt), batch_size=256, shuffle=True)
    best_val=float("inf"); wait=0; best_st=None
    for ep in range(epochs):
        model.train()
        for (b,) in dl:
            if face_mask_fn: mb = face_mask_fn(b)
            elif mask_rate > 0: mb = b * (torch.rand_like(b) > mask_rate).float()
            else: mb = b
            rec, z = model(mb); loss = nn.MSELoss()(rec, b)
            opt.zero_grad(); loss.backward(); opt.step()
        model.eval()
        with torch.no_grad():
            vl = nn.MSELoss()(model(Xv)[0], Xv).item()
        sch.step(vl)
        if vl < best_val: best_val=vl; wait=0; best_st={k:v.clone() for k,v in model.state_dict().items()}
        else:
            wait+=1
            if wait>=50: break
    model.load_state_dict(best_st)
    return model, best_val

# ============= CONTRASTIVE (SimCLR-style) =============
class ProjectionHead(nn.Module):
    def __init__(self, d_emb):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_emb, d_emb), nn.ReLU(), nn.Linear(d_emb, d_emb))
    def forward(self, x): return self.net(x)

def augment(batch, noise_std=0.1, drop_rate=0.15):
    """Two augmented views: noise injection + random feature dropout."""
    v1 = batch + torch.randn_like(batch) * noise_std
    mask1 = (torch.rand_like(batch) > drop_rate).float()
    v1 = v1 * mask1
    v2 = batch + torch.randn_like(batch) * noise_std
    mask2 = (torch.rand_like(batch) > drop_rate).float()
    v2 = v2 * mask2
    return v1, v2

def nt_xent_loss(z1, z2, temperature=0.5):
    """Normalized temperature-scaled cross-entropy loss."""
    z1 = nn.functional.normalize(z1, dim=1)
    z2 = nn.functional.normalize(z2, dim=1)
    N = z1.size(0)
    z = torch.cat([z1, z2], dim=0)
    sim = z @ z.T / temperature
    # Mask self-similarities
    mask = torch.eye(2*N, dtype=torch.bool)
    sim.masked_fill_(mask, -1e9)
    # Positive pairs: (i, i+N) and (i+N, i)
    labels = torch.cat([torch.arange(N, 2*N), torch.arange(0, N)])
    loss = nn.CrossEntropyLoss()(sim, labels)
    return loss

def train_contrastive(encoder, proj_head, X_tr, X_vl, epochs=500, lr=1e-3):
    params = list(encoder.parameters()) + list(proj_head.parameters())
    opt = torch.optim.Adam(params, lr=lr, weight_decay=1e-4)
    sch = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, patience=20, factor=0.5)
    Xt = torch.tensor(X_tr, dtype=torch.float32)
    Xv = torch.tensor(X_vl, dtype=torch.float32)
    dl = DataLoader(TensorDataset(Xt), batch_size=256, shuffle=True)
    best_val=float("inf"); wait=0; best_st=None
    for ep in range(epochs):
        encoder.train(); proj_head.train()
        for (b,) in dl:
            v1, v2 = augment(b)
            z1 = proj_head(encoder(v1))
            z2 = proj_head(encoder(v2))
            loss = nt_xent_loss(z1, z2)
            opt.zero_grad(); loss.backward(); opt.step()
        encoder.eval(); proj_head.eval()
        with torch.no_grad():
            v1v, v2v = augment(Xv, noise_std=0.05, drop_rate=0.1)
            vl = nt_xent_loss(proj_head(encoder(v1v)), proj_head(encoder(v2v))).item()
        sch.step(vl)
        if vl < best_val:
            best_val=vl; wait=0
            best_st = {k:v.clone() for k,v in encoder.state_dict().items()}
        else:
            wait+=1
            if wait>=50: break
    encoder.load_state_dict(best_st)
    return encoder, best_val

# ============= MAIN =============
def main():
    t0 = time.time()
    data = load_data()
    X = data["X"]; d = X.shape[1]
    tr, vl, te = data["train_idx"], data["val_idx"], data["test_idx"]
    faces = data["faces"]; face_names = sorted(faces.keys())
    results = []

    # Load round 1 results for comparison
    r1_path = f"{ROOT}/data/hex_v10/embedding_experiments.json"
    if os.path.exists(r1_path):
        with open(r1_path) as f:
            r1 = json.load(f)
        results.extend(r1)
        print(f"Loaded {len(r1)} round 1 results")

    # --- 6. PCA-64 ---
    print("\n=== PCA-64 ===")
    Z = PCA(64, random_state=SEED).fit_transform(X)
    r = evaluate(Z, data, "pca_64")
    r["explained_var"] = round(float(PCA(64, random_state=SEED).fit(X).explained_variance_ratio_.sum()), 4)
    results.append(r); print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  AMI={r['t4_ami']}")
    pd.DataFrame(Z).to_parquet(f"{OUT_DIR}/pca_64.parquet", index=False)

    # --- 7. PCA-128 ---
    print("\n=== PCA-128 ===")
    Z = PCA(128, random_state=SEED).fit_transform(X)
    r = evaluate(Z, data, "pca_128")
    r["explained_var"] = round(float(PCA(128, random_state=SEED).fit(X).explained_variance_ratio_.sum()), 4)
    results.append(r); print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  AMI={r['t4_ami']}")

    # --- 8. AE-64 ---
    print("\n=== AE-64 ===")
    model = AE(d, 64)
    model, vl_loss = train_ae(model, X[tr], X[vl])
    model.eval()
    with torch.no_grad(): Z = model.encode(torch.tensor(X, dtype=torch.float32)).numpy()
    r = evaluate(Z, data, "ae_64"); results.append(r)
    with torch.no_grad():
        rec = model(torch.tensor(X, dtype=torch.float32))[0].numpy()
    r["recon_r2"] = round(float(1 - ((X-rec)**2).sum() / ((X-X.mean(0))**2).sum()), 4)
    print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  ReconR2={r['recon_r2']}")
    pd.DataFrame(Z).to_parquet(f"{OUT_DIR}/ae_64.parquet", index=False)

    # --- 9. AE-128 ---
    print("\n=== AE-128 ===")
    model = AE(d, 128)
    model, vl_loss = train_ae(model, X[tr], X[vl])
    model.eval()
    with torch.no_grad(): Z = model.encode(torch.tensor(X, dtype=torch.float32)).numpy()
    r = evaluate(Z, data, "ae_128"); results.append(r)
    with torch.no_grad():
        rec = model(torch.tensor(X, dtype=torch.float32))[0].numpy()
    r["recon_r2"] = round(float(1 - ((X-rec)**2).sum() / ((X-X.mean(0))**2).sum()), 4)
    print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  ReconR2={r['recon_r2']}")

    # --- 10. MV-MAE-64 ---
    print("\n=== MV-MAE-64 ===")
    def face_mask_fn(batch):
        masked = batch.clone()
        nm = np.random.randint(1, min(3, len(face_names)))
        for f in np.random.choice(face_names, nm, replace=False):
            for idx in faces[f]: masked[:, idx] = 0
        return masked
    model = AE(d, 64)
    model, vl_loss = train_ae(model, X[tr], X[vl], face_mask_fn=face_mask_fn)
    model.eval()
    with torch.no_grad(): Z = model.encode(torch.tensor(X, dtype=torch.float32)).numpy()
    r = evaluate(Z, data, "mv_mae_64"); results.append(r)
    with torch.no_grad():
        rec = model(torch.tensor(X, dtype=torch.float32))[0].numpy()
    r["recon_r2"] = round(float(1 - ((X-rec)**2).sum() / ((X-X.mean(0))**2).sum()), 4)
    # Cross-view
    infra_faces = ["built","people","access","zoning","influence"]
    commerce_faces = ["commerce","spatial"]
    X_infra = np.zeros_like(X)
    for f in infra_faces:
        for i in faces.get(f,[]): X_infra[:,i] = X[:,i]
    with torch.no_grad():
        rec_cv = model(torch.tensor(X_infra, dtype=torch.float32))[0].numpy()
    cidx = [];
    for f in commerce_faces: cidx.extend(faces.get(f,[]))
    act = X[:,cidx]; pred = rec_cv[:,cidx]
    r["t3_cross_view"] = round(float(1-((act-pred)**2).sum()/((act-act.mean(0))**2).sum()), 4)
    print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  ReconR2={r['recon_r2']}  CV={r['t3_cross_view']}")
    pd.DataFrame(Z).to_parquet(f"{OUT_DIR}/mv_mae_64.parquet", index=False)

    # --- 11. Contrastive-32 ---
    print("\n=== Contrastive-32 (SimCLR) ===")
    enc = nn.Sequential(
        nn.Linear(d, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.2),
        nn.Linear(64, 32))
    proj = ProjectionHead(32)
    enc, vl_loss = train_contrastive(enc, proj, X[tr], X[vl])
    enc.eval()
    with torch.no_grad(): Z = enc(torch.tensor(X, dtype=torch.float32)).numpy()
    r = evaluate(Z, data, "contrastive_32"); results.append(r)
    print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  AMI={r['t4_ami']}")
    pd.DataFrame(Z).to_parquet(f"{OUT_DIR}/contrastive_32.parquet", index=False)

    # --- 12. Contrastive-64 ---
    print("\n=== Contrastive-64 ===")
    enc = nn.Sequential(
        nn.Linear(d, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.2),
        nn.Linear(128, 64))
    proj = ProjectionHead(64)
    enc, vl_loss = train_contrastive(enc, proj, X[tr], X[vl])
    enc.eval()
    with torch.no_grad(): Z = enc(torch.tensor(X, dtype=torch.float32)).numpy()
    r = evaluate(Z, data, "contrastive_64"); results.append(r)
    print(f"  kNN={r['t1_knn_pa']}  CatR2={r['t2_cat_r2']}  AMI={r['t4_ami']}")
    pd.DataFrame(Z).to_parquet(f"{OUT_DIR}/contrastive_64.parquet", index=False)

    # --- Summary ---
    print("\n" + "="*95)
    print(f"{'Method':<25} {'Dims':>5} {'kNN PA':>8} {'Cat R²':>8} {'Recon R²':>9} {'CrossView':>10} {'AMI':>6} {'MBS':>4}")
    print("-"*95)
    for r in results:
        mbs = "✓" if r.get("t5_mbs") else ("✗" if "t5_mbs" in r else "—")
        cv = r.get("t3_cross_view", r.get("t3_cross_view_r2", "—"))
        rc = r.get("recon_r2", "—")
        knn = r.get("t1_knn_pa", 0)
        cat = r.get("t2_cat_r2", r.get("t2_cat_r2_mean", 0))
        ami = r.get("t4_ami", r.get("t4_cluster_ami", 0))
        print(f"{r['method']:<25} {r['dims']:>5} {knn:>8.3f} {cat:>8.3f} {str(rc):>9} {str(cv):>10} {ami:>6.3f} {mbs:>4}")

    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nWrote {OUT_JSON} ({time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main()

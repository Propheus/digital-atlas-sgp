#!/usr/bin/env python3
"""
Validate GCN-64 embedding quality and interpret what it encodes.

Three tests:
  1. Landmark similarity: pick 12 known SGP landmarks, find top-5 similar hexes,
     verify the results match urban intuition (CBD finds CBD, heartland finds heartland).
  2. Dimension interpretability: correlate each of 64 dims with 391 raw features,
     identify the dominant theme per dim.
  3. Cluster semantics: k-means k=10, characterize each cluster.
  4. Comparative sanity: GCN-64 vs PCA-128 vs raw-features on the same landmarks.
"""
import json
import time
import numpy as np
import pandas as pd
import h3

ROOT = "/home/azureuser/digital-atlas-sgp"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# ============================================================
# LOAD
# ============================================================
log("Loading data...")
gcn = pd.read_parquet(f"{ROOT}/data/hex_v10/gcn_results/gcn_embedding_64.parquet")
raw = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
norm = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet")
pca = pd.read_parquet(f"{ROOT}/data/hex_v10/embeddings/hex_embedding_128.parquet")

log(f"  GCN-64: {gcn.shape}")
log(f"  Raw features: {raw.shape}")
log(f"  PCA-128: {pca.shape}")

# Align all to canonical hex order
canonical = raw[["hex_id", "lat", "lng", "parent_subzone",
                 "parent_subzone_name", "parent_pa"]].copy()
gcn = gcn.set_index("hex_id")
G = gcn.loc[canonical["hex_id"].tolist(), [f"g{i}" for i in range(64)]].to_numpy(np.float32)

ID_COLS = {"hex_id", "lat", "lng", "area_km2", "parent_subzone",
           "parent_subzone_name", "parent_pa", "parent_region"}
feat_cols = [c for c in norm.columns if c not in ID_COLS]
F = norm[feat_cols].to_numpy(np.float32)

pca = pca.set_index("hex_id")
pca_cols = [c for c in pca.columns if c.startswith("pc_") or c.startswith("emb")]
if not pca_cols:
    pca_cols = [c for c in pca.columns if c not in ID_COLS][:128]
P = pca.loc[canonical["hex_id"].tolist(), pca_cols].to_numpy(np.float32)

log(f"  Aligned: GCN {G.shape}, Features {F.shape}, PCA {P.shape}")


# ============================================================
# HELPER: cosine top-k
# ============================================================
def norm_rows(M):
    n = np.linalg.norm(M, axis=1, keepdims=True) + 1e-9
    return M / n


Gn = norm_rows(G)
Fn = norm_rows(F)
Pn = norm_rows(P)


def top_k(Zn, idx, k=5):
    sims = Zn @ Zn[idx]
    sims[idx] = -np.inf
    top = np.argsort(-sims)[:k]
    return top, sims[top]


# ============================================================
# TEST 1: LANDMARK SIMILARITY
# ============================================================
log("\n" + "=" * 70)
log("TEST 1 — Landmark similarity (top-5 by cosine)")
log("=" * 70)

LANDMARKS = {
    "Raffles Place (CBD core)":       (1.2841, 103.8515),
    "Orchard Road (retail spine)":    (1.3048, 103.8318),
    "Tiong Bahru (heritage cafe)":    (1.2852, 103.8306),
    "Marina Bay Sands (tourism)":     (1.2838, 103.8591),
    "Changi Airport T3":              (1.3554, 103.9840),
    "Sentosa RWS (island resort)":    (1.2541, 103.8231),
    "Tampines Hub (heartland)":       (1.3549, 103.9442),
    "Jurong East (regional centre)":  (1.3331, 103.7428),
    "Tuas (heavy industry)":          (1.3240, 103.6360),
    "Bedok HDB (mature estate)":      (1.3236, 103.9273),
    "NUS Kent Ridge (university)":    (1.2966, 103.7764),
    "Woodlands (N suburban)":         (1.4382, 103.7883),
}

hid_to_idx = {h: i for i, h in enumerate(canonical["hex_id"].tolist())}

landmark_table = []
for name, (lat, lng) in LANDMARKS.items():
    hid = h3.latlng_to_cell(lat, lng, 9)
    if hid not in hid_to_idx:
        log(f"\n{name}: hex {hid} NOT in canonical 7318")
        continue
    idx = hid_to_idx[hid]
    pa = canonical.iloc[idx]["parent_pa"]
    sz = canonical.iloc[idx]["parent_subzone_name"]
    log(f"\n{name}  [{sz} / {pa}]")

    for zname, Zn in [("GCN-64", Gn), ("PCA-128", Pn), ("Raw-460", Fn)]:
        top, sims = top_k(Zn, idx, k=5)
        nbrs = []
        for ti, s in zip(top, sims):
            nbr_sz = canonical.iloc[ti]["parent_subzone_name"]
            nbr_pa = canonical.iloc[ti]["parent_pa"]
            nbrs.append(f"{nbr_sz[:14]:14} ({nbr_pa[:10]}) {s:.2f}")
        log(f"  {zname:<8} → {' | '.join(nbrs)}")

    # For the table
    top, sims = top_k(Gn, idx, k=5)
    landmark_table.append({
        "landmark": name,
        "query_pa": pa,
        "top5_pas": [canonical.iloc[t]["parent_pa"] for t in top],
        "top5_same_pa_count": sum(1 for t in top
                                   if canonical.iloc[t]["parent_pa"] == pa),
    })


# ============================================================
# TEST 2: DIMENSION INTERPRETABILITY
# ============================================================
log("\n\n" + "=" * 70)
log("TEST 2 — Dimension interpretability")
log("=" * 70)
log("For each GCN dim, find the top-3 raw features it correlates with.")

# Pearson correlation of each embedding dim with each feature
# G: [N, 64], F: [N, 391]
G_centered = G - G.mean(axis=0, keepdims=True)
G_std = G.std(axis=0, keepdims=True) + 1e-9
G_norm = G_centered / G_std

F_centered = F - F.mean(axis=0, keepdims=True)
F_std = F.std(axis=0, keepdims=True) + 1e-9
F_norm = F_centered / F_std

# Correlation matrix: [64, 391]
n = G.shape[0]
C = (G_norm.T @ F_norm) / n  # Pearson

dim_themes = {}
log(f"\n{'Dim':<4} {'Top-3 most correlated features':<70}")
log("-" * 80)
for d in range(64):
    # Top 3 absolute correlations
    abs_c = np.abs(C[d])
    top3 = np.argsort(-abs_c)[:3]
    parts = []
    for t in top3:
        sign = "+" if C[d, t] > 0 else "-"
        parts.append(f"{sign}{feat_cols[t]}({abs_c[t]:.2f})")
    dim_themes[d] = parts
    log(f"g{d:<3} {' '.join(parts):<70}")


# ============================================================
# TEST 3: CLUSTER SEMANTICS
# ============================================================
log("\n\n" + "=" * 70)
log("TEST 3 — K-means cluster semantics (k=10)")
log("=" * 70)

from sklearn.cluster import KMeans
km = KMeans(n_clusters=10, random_state=42, n_init=10).fit(G)
labels = km.labels_

log(f"\n{'Cluster':<8} {'Size':<6} {'Dominant PAs':<35} {'Top features':<60}")
log("-" * 110)

for c in range(10):
    mask = labels == c
    sz = mask.sum()

    # Dominant parent PAs
    pas = canonical.loc[mask, "parent_pa"].value_counts().head(3)
    pa_str = ", ".join([f"{p}({n})" for p, n in pas.items()])

    # Feature signature: which features are high in this cluster vs baseline
    cluster_mean = F[mask].mean(axis=0)
    baseline_mean = F.mean(axis=0)
    diff = cluster_mean - baseline_mean
    top_pos = np.argsort(-diff)[:3]
    feat_str = ", ".join([f"{feat_cols[t]}(+{diff[t]:.1f})" for t in top_pos])

    log(f"{c:<8} {sz:<6} {pa_str[:35]:<35} {feat_str[:60]}")


# ============================================================
# TEST 4: QUANTITATIVE COMPARISON
# ============================================================
log("\n\n" + "=" * 70)
log("TEST 4 — Quantitative similarity quality")
log("=" * 70)

pa_labels = np.asarray(canonical["parent_pa"].astype(str).values)


def knn_agreement(Zn, labels, k=10):
    S = Zn @ Zn.T
    np.fill_diagonal(S, -np.inf)
    nn = np.argpartition(-S, k, axis=1)[:, :k]
    return (labels[nn] == labels[:, None]).mean()


log("\nkNN @ k=10 agreement on parent-PA (all 7,318 hexes):")
for name, Zn in [("GCN-64", Gn), ("PCA-128", Pn), ("Raw-460", Fn)]:
    acc = knn_agreement(Zn, pa_labels)
    log(f"  {name:<10} {acc:.3f}")


# ============================================================
# SAVE REPORT
# ============================================================
out = f"{ROOT}/data/hex_v10/gcn_results/gcn_validation_report.json"
report = {
    "landmarks": landmark_table,
    "dimension_themes": {f"g{d}": parts for d, parts in dim_themes.items()},
    "cluster_sizes": [int((labels == c).sum()) for c in range(10)],
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
}
with open(out, "w") as f:
    json.dump(report, f, indent=2)
log(f"\nSaved: {out}")

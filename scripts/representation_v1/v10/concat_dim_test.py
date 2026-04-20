#!/usr/bin/env python3
"""Quick test: does concatenating existing embeddings (= more dims) improve similarity?"""
import pandas as pd
import numpy as np
import time

ROOT = "/home/azureuser/digital-atlas-sgp"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


raw = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
norm = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10_normalized.parquet")
gcn = pd.read_parquet(f"{ROOT}/data/hex_v10/gcn_results/gcn_embedding_64.parquet")
pca128 = pd.read_parquet(f"{ROOT}/data/hex_v10/embeddings/hex_embedding_128.parquet")
barlow = pd.read_parquet(f"{ROOT}/data/hex_v10/embeddings/barlow_64.parquet")
vae = pd.read_parquet(f"{ROOT}/data/hex_v10/embeddings/vae_64.parquet")

hex_order = raw["hex_id"].tolist()

def align(df, ncols):
    # If hex_id column exists, index by it; else assume row order matches
    if "hex_id" in df.columns:
        df = df.set_index("hex_id")
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return df.loc[hex_order, num_cols[:ncols]].to_numpy(np.float32)
    else:
        # No hex_id — assume rows align with canonical order
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return df[num_cols[:ncols]].to_numpy(np.float32)

G = align(gcn, 64)
P = align(pca128, 128)
B = align(barlow, 64)
V = align(vae, 64)

ID_COLS = {"hex_id","lat","lng","area_km2","parent_subzone","parent_subzone_name","parent_pa","parent_region"}
BK = {"subzone_pop_total","subzone_res_floor_area","residential_floor_weight"}
feat_cols = [c for c in norm.columns if c not in ID_COLS and c not in BK]
R = norm[feat_cols].to_numpy(np.float32)

pa = np.asarray(raw["parent_pa"].astype(str).values)


def knn_pa(Z, k=10):
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
    S = Zn @ Zn.T
    np.fill_diagonal(S, -np.inf)
    nn = np.argpartition(-S, k, axis=1)[:, :k]
    return (pa[nn] == pa[:, None]).mean()


def z_standardize(Z):
    """Zero mean, unit variance per dim."""
    return (Z - Z.mean(axis=0)) / (Z.std(axis=0) + 1e-9)


# Before concatenation, z-standardize each piece so they contribute equally
Gz, Pz, Bz, Vz, Rz = map(z_standardize, [G, P, B, V, R])

log("\n=== SINGLE EMBEDDINGS ===")
for n, Z in [("GCN-64", Gz), ("PCA-128", Pz), ("Barlow-64", Bz), ("VAE-64", Vz), ("Raw-460", Rz)]:
    log(f"  {n:<15} dims={Z.shape[1]:<4} kNN-PA={knn_pa(Z):.3f}")

log("\n=== CONCATENATIONS ===")
configs = [
    ("GCN-64 ⊕ PCA-128", np.hstack([Gz, Pz])),
    ("GCN-64 ⊕ Barlow-64", np.hstack([Gz, Bz])),
    ("GCN-64 ⊕ VAE-64", np.hstack([Gz, Vz])),
    ("GCN-64 ⊕ Raw-460", np.hstack([Gz, Rz])),
    ("GCN-64 ⊕ PCA-128 ⊕ Barlow-64", np.hstack([Gz, Pz, Bz])),
    ("All (GCN+PCA+Barlow+VAE+Raw)", np.hstack([Gz, Pz, Bz, Vz, Rz])),
]
for n, Z in configs:
    log(f"  {n:<45} dims={Z.shape[1]:<4} kNN-PA={knn_pa(Z):.3f}")

log("\n=== SCALED CONCATS (GCN weighted 2x) ===")
# Sometimes the richer signal should dominate
configs2 = [
    ("2×GCN-64 ⊕ PCA-128", np.hstack([2*Gz, Pz])),
    ("3×GCN-64 ⊕ Raw-460", np.hstack([3*Gz, Rz])),
]
for n, Z in configs2:
    log(f"  {n:<45} dims={Z.shape[1]:<4} kNN-PA={knn_pa(Z):.3f}")

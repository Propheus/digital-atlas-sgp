"""
SGP Factor Decomposition pipeline.

Reads data/hex_v10/hex_features_v10_normalized.parquet (7318 hexes x 460 numeric features,
already z-scored), reduces to 2D via PCA -> UMAP, clusters via HDBSCAN (k-means fallback),
computes stability (mean ARI across 5 bootstrap resamples), and emits:

  data/factor_atlas/embedding.json       per-hex {hex_id,x,y,cluster,parent_subzone,...}
  data/factor_atlas/cluster_summary.json per-cluster {n, top_features[], centroid}
  data/factor_atlas/preview.png          matplotlib preview for eyeballing

Run:
  python3 scripts/build_factor_embedding.py
  python3 scripts/build_factor_embedding.py --feature-set base --k 5
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, silhouette_score

META_COLS = {"hex_id", "lat", "lng", "area_km2",
             "parent_subzone", "parent_subzone_name",
             "parent_pa", "parent_region"}

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "factor_atlas"


def load_features(feature_set: str) -> pd.DataFrame:
    fname = {
        "normalized": "hex_features_v10_normalized.parquet",
        "base": "hex_features_v10_base.parquet",
        "merged": "hex_features_v10_merged.parquet",
    }[feature_set]
    df = pd.read_parquet(ROOT / "data" / "hex_v10" / fname)
    # base parquet isn't z-scored; standardize if needed
    num_cols = [c for c in df.columns if c not in META_COLS and df[c].dtype != "object"]
    X = df[num_cols].to_numpy(dtype=np.float32)
    # impute NaNs with column mean before any standardization
    if np.isnan(X).any():
        col_mean = np.nanmean(X, axis=0)
        col_mean = np.where(np.isnan(col_mean), 0.0, col_mean)
        idx = np.where(np.isnan(X))
        X[idx] = np.take(col_mean, idx[1])
    if feature_set == "base":
        from sklearn.preprocessing import StandardScaler
        X = StandardScaler().fit_transform(X).astype(np.float32)
    return df, X, num_cols


def reduce_pca_umap(X: np.ndarray, *, pca_dim: int, n_neighbors: int, min_dist: float, seed: int):
    import umap
    pca = PCA(n_components=min(pca_dim, X.shape[1]), random_state=seed)
    Xp = pca.fit_transform(X)
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        metric="euclidean",
        random_state=seed,
        n_jobs=1,
    )
    Xe = reducer.fit_transform(Xp)
    return Xe.astype(np.float32), pca.explained_variance_ratio_.sum()


def cluster(Xe: np.ndarray, *, method: str, k: int, min_cluster_size: int, seed: int):
    if method == "hdbscan":
        import hdbscan
        labels = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size, min_samples=10
        ).fit_predict(Xe)
        # HDBSCAN may emit -1 (noise); push to nearest cluster centroid
        if (labels == -1).any() and (labels != -1).any():
            from sklearn.metrics import pairwise_distances_argmin
            centroids = np.vstack([Xe[labels == c].mean(0) for c in sorted(set(labels) - {-1})])
            cmap = sorted(set(labels) - {-1})
            noise = labels == -1
            nearest = pairwise_distances_argmin(Xe[noise], centroids)
            labels = labels.copy()
            labels[noise] = [cmap[i] for i in nearest]
        return labels
    if method == "kmeans":
        return KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(Xe)
    raise ValueError(method)


def stability_ari(X: np.ndarray, base_labels: np.ndarray, *, method: str, k: int,
                  min_cluster_size: int, pca_dim: int, n_neighbors: int, min_dist: float,
                  n_bootstraps: int = 5, sample_frac: float = 0.85, seed: int = 42) -> float:
    import umap
    rng = np.random.default_rng(seed)
    aris = []
    for i in range(n_bootstraps):
        idx = rng.choice(X.shape[0], size=int(X.shape[0] * sample_frac), replace=False)
        Xs = X[idx]
        Xp = PCA(n_components=min(pca_dim, Xs.shape[1]), random_state=seed + i).fit_transform(Xs)
        Xe = umap.UMAP(n_components=2, n_neighbors=n_neighbors, min_dist=min_dist,
                       random_state=seed + i, n_jobs=1).fit_transform(Xp)
        labels = cluster(Xe.astype(np.float32), method=method, k=k,
                         min_cluster_size=min_cluster_size, seed=seed + i)
        aris.append(adjusted_rand_score(base_labels[idx], labels))
    return float(np.mean(aris))


def cluster_summaries(df: pd.DataFrame, X: np.ndarray, feature_names: list[str],
                      labels: np.ndarray, top_k: int = 8) -> list[dict]:
    summaries = []
    global_mean = X.mean(0)
    for cid in sorted(set(labels)):
        mask = labels == cid
        n = int(mask.sum())
        # since features are z-scored, cluster mean IS the z-score vs global
        zmean = X[mask].mean(0) - global_mean  # robust even if not perfectly z-scored
        top_pos = np.argsort(-zmean)[:top_k]
        top_neg = np.argsort(zmean)[:top_k]
        # geographic centroid
        sub_df = df.loc[mask]
        summaries.append({
            "cluster": int(cid),
            "n": n,
            "share": round(n / len(df), 3),
            "centroid_lat": float(sub_df["lat"].mean()),
            "centroid_lng": float(sub_df["lng"].mean()),
            "top_positive_features": [
                {"name": feature_names[i], "z": float(round(zmean[i], 3))} for i in top_pos
            ],
            "top_negative_features": [
                {"name": feature_names[i], "z": float(round(zmean[i], 3))} for i in top_neg
            ],
            "top_subzones": (
                sub_df.groupby("parent_subzone_name").size().sort_values(ascending=False).head(8).to_dict()
            ),
            "top_regions": (
                sub_df.groupby("parent_region").size().sort_values(ascending=False).to_dict()
            ),
        })
    return summaries


def save_preview(df: pd.DataFrame, Xe: np.ndarray, labels: np.ndarray, out: Path,
                 title: str):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor="#0a1f1c")
    palette = ["#7af5c5", "#f4cf9d", "#9bd1ff", "#c4f560", "#ff8fa3",
               "#b794f4", "#fce38a", "#5eead4"]
    for ax in axes:
        ax.set_facecolor("#0a1f1c")
        for spine in ax.spines.values():
            spine.set_color("#1f3a35")
        ax.tick_params(colors="#7af5c5")
    # latent
    for cid in sorted(set(labels)):
        m = labels == cid
        c = palette[cid % len(palette)] if cid >= 0 else "#3a5a55"
        axes[0].scatter(Xe[m, 0], Xe[m, 1], s=4, c=c, alpha=0.85, linewidths=0)
    axes[0].set_title(f"UMAP latent — {title}", color="#e0f5ec")
    # geographic
    for cid in sorted(set(labels)):
        m = labels == cid
        c = palette[cid % len(palette)] if cid >= 0 else "#3a5a55"
        axes[1].scatter(df.loc[m, "lng"], df.loc[m, "lat"], s=6, c=c, alpha=0.9, linewidths=0)
    axes[1].set_title("Geographic projection (SGP)", color="#e0f5ec")
    axes[1].set_aspect("equal")
    fig.tight_layout()
    fig.savefig(out, dpi=140, facecolor="#0a1f1c")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature-set", choices=["normalized", "base", "merged"], default="normalized")
    ap.add_argument("--pca-dim", type=int, default=40)
    ap.add_argument("--n-neighbors", type=int, default=30)
    ap.add_argument("--min-dist", type=float, default=0.1)
    ap.add_argument("--method", choices=["hdbscan", "kmeans"], default="hdbscan")
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--min-cluster-size", type=int, default=180)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--bootstraps", type=int, default=5)
    ap.add_argument("--skip-stability", action="store_true")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[1/5] loading feature set: {args.feature_set}")
    df, X, feature_names = load_features(args.feature_set)
    print(f"      shape {X.shape}")

    print(f"[2/5] PCA({args.pca_dim}) -> UMAP(n={args.n_neighbors}, d={args.min_dist})")
    Xe, var = reduce_pca_umap(
        X, pca_dim=args.pca_dim, n_neighbors=args.n_neighbors,
        min_dist=args.min_dist, seed=args.seed,
    )
    print(f"      PCA variance retained: {var:.3f}")

    print(f"[3/5] cluster method={args.method}")
    labels = cluster(Xe, method=args.method, k=args.k,
                     min_cluster_size=args.min_cluster_size, seed=args.seed)
    n_clusters = len(set(labels))
    sil = float(silhouette_score(Xe, labels)) if n_clusters > 1 else 0.0
    print(f"      {n_clusters} clusters, silhouette {sil:.3f}")
    print(f"      sizes: {dict(zip(*np.unique(labels, return_counts=True)))}")

    if args.skip_stability:
        stab = None
    else:
        print(f"[4/5] stability ({args.bootstraps} bootstraps)")
        stab = stability_ari(
            X, labels, method=args.method, k=args.k,
            min_cluster_size=args.min_cluster_size, pca_dim=args.pca_dim,
            n_neighbors=args.n_neighbors, min_dist=args.min_dist,
            n_bootstraps=args.bootstraps, seed=args.seed,
        )
        print(f"      mean ARI: {stab:.3f}")

    print("[5/5] writing artifacts")
    embedding = [
        {
            "hex_id": row.hex_id,
            "x": float(round(Xe[i, 0], 4)),
            "y": float(round(Xe[i, 1], 4)),
            "lat": float(round(row.lat, 6)),
            "lng": float(round(row.lng, 6)),
            "cluster": int(labels[i]),
            "subzone": row.parent_subzone_name,
            "region": row.parent_region,
        }
        for i, row in enumerate(df.itertuples(index=False))
    ]
    (OUT_DIR / "embedding.json").write_text(json.dumps(embedding, separators=(",", ":")))

    summary = {
        "feature_set": args.feature_set,
        "n_hexes": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "pca_dim": args.pca_dim,
        "pca_variance_retained": round(float(var), 4),
        "umap_n_neighbors": args.n_neighbors,
        "umap_min_dist": args.min_dist,
        "method": args.method,
        "n_clusters": int(n_clusters),
        "silhouette": round(sil, 4),
        "stability_ari": (None if stab is None else round(stab, 4)),
        "seed": args.seed,
        "clusters": cluster_summaries(df, X, feature_names, labels),
    }
    (OUT_DIR / "cluster_summary.json").write_text(json.dumps(summary, indent=2, default=str))

    save_preview(df, Xe, labels, OUT_DIR / "preview.png",
                 title=f"{args.feature_set} | {n_clusters} clusters | sil={sil:.2f}"
                       + (f" | stab={stab:.2f}" if stab is not None else ""))
    print(f"      -> {OUT_DIR}")


if __name__ == "__main__":
    main()

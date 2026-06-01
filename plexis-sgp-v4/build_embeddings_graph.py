"""
Plexis SGP v4 — Stage 28: Graph-based embeddings (preserves PCA).

Three new graph-based embeddings, alongside the existing PCA ones:

  PLACE2VEC 64d      gensim Word2Vec skip-gram on place co-occurrence
                     (each hex9 = a sentence of its places, shuffled across
                     epochs). Captures co-location semantics.
  HEX_NODE2VEC 64d   gensim Word2Vec on random walks over H3 grid adjacency.
                     Captures pure topology.
  HEX_GCN 64d        2-hop normalized-adjacency message passing on hex_all
                     features, then PCA-64. Captures graph-smoothed feature
                     similarity.

Plus combined ensembles that mix graph + PCA dims:

  PLACE_SUPER 128d   concat[place2vec_64d, what_pca_64d]
  HEX_SUPER  128d    concat[hex_node2vec_64d, hex_gcn_64d]
  PLACE_MEGA 256d    concat[place2vec, what_pca, hex_gcn(of place's hex), hex_where_pca]

Outputs (new files; existing PCA embeddings untouched):
  hex/hex9_embedding_node2vec_64d.parquet
  hex/hex9_embedding_gcn_64d.parquet
  hex/hex9_embedding_super_128d.parquet
  places/place_embedding_place2vec_64d.parquet
  places/place_embedding_super_128d.parquet
  places/place_embedding_mega_256d.parquet
"""
import json, time, random
from pathlib import Path
import numpy as np
import pandas as pd
import h3
from gensim.models import Word2Vec
from scipy.sparse import csr_matrix, eye, diags
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent
SEED = 42
np.random.seed(SEED); random.seed(SEED)


def place2vec(places, n_epochs=10, vector_size=64):
    """Word2Vec on hex-based place co-occurrence."""
    print("\n=== PLACE2VEC ===")
    places = places[places["hex9_id"].notna()].copy()
    place_by_hex = places.groupby("hex9_id")["id"].apply(list).reset_index()
    place_by_hex = place_by_hex[place_by_hex["id"].apply(len) >= 2]
    print(f"  hexes with ≥2 places: {len(place_by_hex)}")

    # Shuffled sentences across epochs
    sentences = []
    for epoch in range(n_epochs):
        for places_in_hex in place_by_hex["id"]:
            shuffled = list(places_in_hex)
            random.shuffle(shuffled)
            sentences.append(shuffled)
    print(f"  total sentences (across {n_epochs} epochs): {len(sentences):,}")

    print("  training Word2Vec (skip-gram, neg=10)...")
    model = Word2Vec(
        sentences=sentences,
        vector_size=vector_size,
        window=5,
        min_count=1,
        sg=1,            # skip-gram
        negative=10,
        epochs=5,
        workers=8,
        seed=SEED,
    )
    print(f"  vocab size: {len(model.wv):,}")

    # Build embedding matrix in places' order
    rows = []
    for pid in places["id"]:
        if pid in model.wv:
            rows.append(model.wv[pid])
        else:
            rows.append(np.zeros(vector_size, dtype=np.float32))
    arr = np.array(rows, dtype=np.float32)
    df = pd.DataFrame(arr, columns=[f"d{i}" for i in range(vector_size)])
    df.insert(0, "id", places["id"].values)
    return df


def hex_node2vec(h9_ids, walks_per_node=30, walk_length=30, vector_size=64):
    """Random walks on H3 grid_ring(k=1) adjacency, then Word2Vec."""
    print("\n=== HEX_NODE2VEC ===")
    cell_set = set(h9_ids)
    print(f"  hex9 count: {len(h9_ids):,}")

    # Pre-compute neighbors
    print("  building adjacency (H3 grid_ring k=1)...")
    nbr_map = {}
    for c in h9_ids:
        try:
            nbrs = [n for n in h3.grid_ring(c, 1) if n in cell_set]
        except Exception:
            nbrs = []
        nbr_map[c] = nbrs

    # Random walks
    print(f"  generating walks ({walks_per_node} per node × length {walk_length})...")
    walks = []
    for c in h9_ids:
        for _ in range(walks_per_node):
            walk = [c]
            cur = c
            for _ in range(walk_length - 1):
                nbrs = nbr_map.get(cur, [])
                if not nbrs: break
                cur = random.choice(nbrs)
                walk.append(cur)
            walks.append(walk)
    print(f"  total walks: {len(walks):,}")

    print("  training Word2Vec on walks...")
    model = Word2Vec(
        sentences=walks, vector_size=vector_size, window=5, min_count=1,
        sg=1, negative=10, epochs=5, workers=8, seed=SEED,
    )
    rows = [model.wv[c] if c in model.wv else np.zeros(vector_size, dtype=np.float32) for c in h9_ids]
    arr = np.array(rows, dtype=np.float32)
    df = pd.DataFrame(arr, columns=[f"d{i}" for i in range(vector_size)])
    df.insert(0, "hex9_id", h9_ids)
    return df


def hex_gcn(h9_df, vector_size=64):
    """2-hop GCN-style message passing over hex_all_features, then PCA-64.

    Implementation: Graph G with edges = H3 grid_ring(1).
    A_sym = D^-0.5 (A + I) D^-0.5
    H = A_sym @ A_sym @ X     (2-hop smoothed features)
    Embedding = PCA-64(H)
    """
    print("\n=== HEX_GCN ===")
    h9_ids = h9_df["hex9_id"].tolist()
    cell_to_idx = {c: i for i, c in enumerate(h9_ids)}
    n = len(h9_ids)

    # Build sparse adjacency
    print("  building sparse adjacency...")
    rows, cols = [], []
    for i, c in enumerate(h9_ids):
        for nb in h3.grid_ring(c, 1):
            j = cell_to_idx.get(nb)
            if j is not None:
                rows.append(i); cols.append(j)
    data = np.ones(len(rows), dtype=np.float32)
    A = csr_matrix((data, (rows, cols)), shape=(n, n))
    A = A + eye(n, dtype=np.float32)  # self-loops
    deg = np.array(A.sum(axis=1)).flatten()
    d_inv_sqrt = 1.0 / np.sqrt(np.maximum(deg, 1e-9))
    D = diags(d_inv_sqrt, format="csr")
    A_sym = D @ A @ D
    print(f"  A_sym: {A_sym.shape}, nnz {A_sym.nnz:,}")

    # Feature matrix (numeric only, no IDs/labels)
    drop_cols = ["hex9_id","parent_hex8","parent_subzone","parent_subzone_name","parent_pa",
                 "parent_region","lat","lng","pc_dominant_category","archetype_label",
                 "pc2_dominant_category"]
    feat_cols = [c for c in h9_df.columns
                 if c not in drop_cols and pd.api.types.is_numeric_dtype(h9_df[c])]
    X_raw = h9_df[feat_cols].fillna(0).values.astype(np.float32)
    X = StandardScaler().fit_transform(X_raw).astype(np.float32)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    print(f"  feature matrix: {X.shape}")

    print("  2-hop message passing...")
    H = A_sym @ X
    H = A_sym @ H

    print("  PCA-64...")
    pca = PCA(n_components=min(64, H.shape[1]), random_state=SEED)
    emb = pca.fit_transform(H).astype(np.float32)
    if emb.shape[1] < 64:
        emb = np.pad(emb, ((0,0),(0,64-emb.shape[1])))
    var = pca.explained_variance_ratio_.sum()
    print(f"    explained variance: {var:.3f}")

    df = pd.DataFrame(emb, columns=[f"d{i}" for i in range(64)])
    df.insert(0, "hex9_id", h9_ids)
    return df, var


def main():
    t0 = time.time()
    print("Loading inputs...")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
    place_what_pca = pd.read_parquet(ROOT / "places/place_embedding_what_64d.parquet")
    hex_where_pca = pd.read_parquet(ROOT / "hex/hex9_embedding_where_64d.parquet")
    print(f"  places: {len(places):,}, hex9: {len(h9):,}")

    # === PLACE2VEC ===
    p2v = place2vec(places, n_epochs=10, vector_size=64)
    p2v.to_parquet(ROOT / "places/place_embedding_place2vec_64d.parquet", index=False)
    print(f"  place_embedding_place2vec_64d: {p2v.shape}")

    # === HEX_NODE2VEC ===
    hn2v = hex_node2vec(h9["hex9_id"].tolist(), walks_per_node=30, walk_length=30, vector_size=64)
    hn2v.to_parquet(ROOT / "hex/hex9_embedding_node2vec_64d.parquet", index=False)
    print(f"  hex9_embedding_node2vec_64d: {hn2v.shape}")

    # === HEX_GCN ===
    hgcn, gcn_var = hex_gcn(h9, vector_size=64)
    hgcn.to_parquet(ROOT / "hex/hex9_embedding_gcn_64d.parquet", index=False)
    print(f"  hex9_embedding_gcn_64d: {hgcn.shape}")

    # === HEX_SUPER 128d (node2vec ⊕ gcn) ===
    print("\n=== HEX_SUPER 128d ===")
    hs = hn2v.merge(hgcn, on="hex9_id", suffixes=("_n2v","_gcn"))
    cols = ([f"d{i}_n2v" for i in range(64)] + [f"d{i}_gcn" for i in range(64)])
    super_arr = hs[cols].values.astype(np.float32)
    hex_super = pd.DataFrame(super_arr, columns=[f"d{i}" for i in range(128)])
    hex_super.insert(0, "hex9_id", hs["hex9_id"].values)
    hex_super.to_parquet(ROOT / "hex/hex9_embedding_super_128d.parquet", index=False)
    print(f"  hex9_embedding_super_128d: {hex_super.shape}")

    # === PLACE_SUPER 128d (place2vec ⊕ what_pca) ===
    print("\n=== PLACE_SUPER 128d ===")
    ps = p2v.merge(place_what_pca, on="id", suffixes=("_p2v","_what"))
    cols = ([f"d{i}_p2v" for i in range(64)] + [f"d{i}_what" for i in range(64)])
    super_arr = ps[cols].values.astype(np.float32)
    place_super = pd.DataFrame(super_arr, columns=[f"d{i}" for i in range(128)])
    place_super.insert(0, "id", ps["id"].values)
    place_super.to_parquet(ROOT / "places/place_embedding_super_128d.parquet", index=False)
    print(f"  place_embedding_super_128d: {place_super.shape}")

    # === PLACE_MEGA 256d (place2vec ⊕ what_pca ⊕ hex_gcn ⊕ hex_where_pca) ===
    print("\n=== PLACE_MEGA 256d ===")
    places_h = places[["id","hex9_id"]]
    pm = ps.merge(places_h, on="id")
    pm = pm.merge(hgcn.rename(columns={f"d{i}": f"d{i}_gcn" for i in range(64)}), on="hex9_id", how="left")
    pm = pm.merge(hex_where_pca.rename(columns={f"d{i}": f"d{i}_where" for i in range(64)}), on="hex9_id", how="left")
    fill_cols = [f"d{i}_gcn" for i in range(64)] + [f"d{i}_where" for i in range(64)]
    for c in fill_cols: pm[c] = pm[c].fillna(0)
    cols = ([f"d{i}_p2v" for i in range(64)] + [f"d{i}_what" for i in range(64)]
            + [f"d{i}_gcn" for i in range(64)] + [f"d{i}_where" for i in range(64)])
    mega_arr = pm[cols].values.astype(np.float32)
    place_mega = pd.DataFrame(mega_arr, columns=[f"d{i}" for i in range(256)])
    place_mega.insert(0, "id", pm["id"].values)
    place_mega.to_parquet(ROOT / "places/place_embedding_mega_256d.parquet", index=False)
    print(f"  place_embedding_mega_256d: {place_mega.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "method": {
            "place2vec":     "Word2Vec skip-gram on hex co-occurrence (10 epochs × shuffled)",
            "hex_node2vec":  "Word2Vec skip-gram on H3 grid_ring random walks (30×30)",
            "hex_gcn":       "2-hop A_sym @ A_sym @ X then PCA-64",
            "place_super":   "concat[place2vec_64, what_pca_64]",
            "hex_super":     "concat[node2vec_64, gcn_64]",
            "place_mega":    "concat[place2vec_64, what_pca_64, hex_gcn_64, hex_where_pca_64]",
        },
        "shapes": {
            "place_p2v_64":   list(p2v.shape),
            "hex_n2v_64":     list(hn2v.shape),
            "hex_gcn_64":     list(hgcn.shape),
            "hex_super_128":  list(hex_super.shape),
            "place_super_128": list(place_super.shape),
            "place_mega_256": list(place_mega.shape),
        },
        "hex_gcn_explained_variance": gcn_var,
    }
    with open(ROOT / "hex/embeddings_graph_report.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

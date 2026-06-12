"""
Plexis SGP v4 — Stage 27: Place + Hex embeddings.

Three embedding artifacts, all PCA-based (deterministic, reproducible):

  WHERE_AM_I (64d) — per-hex9 embedding from hex_all_features (558 cols).
                     This captures the *location context* of any place.
  WHAT_AM_I  (64d) — per-place embedding from intrinsic place features:
                     plexis_category one-hot, pc2_category one-hot,
                     brand_norm one-hot (top 50 + other), rating,
                     reviews_count, magnet_strength, etc.
  COMBINED  (128d) — concat[what, where] per place; per hex9 = where ⊕ mean(what).

Outputs:
  hex/hex9_embedding_where_64d.parquet         hex9_id + d0..d63
  places/place_embedding_what_64d.parquet      id + d0..d63
  places/place_embedding_combined_128d.parquet id + d0..d127
  hex/hex9_embedding_combined_128d.parquet     hex9_id + d0..d127
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent
SEED = 42


def fit_pca_64(arr, name):
    print(f"  fitting PCA-64 on {name}: shape {arr.shape}")
    scaler = StandardScaler(with_mean=True, with_std=True)
    arr_s = scaler.fit_transform(arr)
    arr_s = np.nan_to_num(arr_s, nan=0.0, posinf=0.0, neginf=0.0)
    n_comp = min(64, arr_s.shape[1], arr_s.shape[0])
    pca = PCA(n_components=n_comp, random_state=SEED)
    emb = pca.fit_transform(arr_s)
    if emb.shape[1] < 64:
        emb = np.pad(emb, ((0, 0), (0, 64 - emb.shape[1])))
    var_explained = pca.explained_variance_ratio_.sum()
    print(f"    explained variance: {var_explained:.3f}")
    return emb.astype(np.float32), float(var_explained)


def main():
    t0 = time.time()

    # ============== WHERE_AM_I: hex9 embedding ==============
    print("\n=== WHERE_AM_I (hex9 embedding 64d) ===")
    h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
    # Drop key + non-numeric cols
    drop_cols = ["hex9_id","parent_hex8","parent_subzone","parent_subzone_name","parent_pa",
                 "parent_region","lat","lng","pc_dominant_category","archetype_label",
                 "pc2_dominant_category"]
    feat_cols = [c for c in h9.columns if c not in drop_cols]
    feat_cols = [c for c in feat_cols if pd.api.types.is_numeric_dtype(h9[c])]
    X = h9[feat_cols].fillna(0).values.astype(float)
    where_emb, var_w = fit_pca_64(X, "hex9_all_features")
    where_df = pd.DataFrame(where_emb, columns=[f"d{i}" for i in range(64)])
    where_df.insert(0, "hex9_id", h9["hex9_id"].values)
    where_df.to_parquet(ROOT / "hex/hex9_embedding_where_64d.parquet", index=False)
    print(f"  hex9_embedding_where_64d: {where_df.shape}")

    # ============== WHAT_AM_I: per-place embedding ==============
    print("\n=== WHAT_AM_I (place embedding 64d) ===")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")

    # Add pc2 category
    pc2_cats = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
    # Re-derive pc2_category from raw primary_category (re-use map from build_place_composition_v2)
    from build_place_composition_v2 import CAT_MAP
    places["pc2_category"] = places["primary_category"].map(CAT_MAP).fillna("unmapped")

    # Build feature matrix
    print("  building place feature matrix...")
    # 1. plexis_category one-hot (24)
    plexis_oh = pd.get_dummies(places["plexis_category"], prefix="plx").astype(np.float32)
    # 2. pc2_category one-hot (~55)
    pc2_oh = pd.get_dummies(places["pc2_category"], prefix="pc2").astype(np.float32)
    # 3. Top 50 brands one-hot + 'other'
    top_brands = places["brand_norm"].dropna().value_counts().head(50).index.tolist()
    brand_col = places["brand_norm"].where(places["brand_norm"].isin(top_brands), other="OTHER")
    brand_col = brand_col.fillna("NONE")
    brand_oh = pd.get_dummies(brand_col, prefix="brnd").astype(np.float32)
    # 4. Numeric features
    num = pd.DataFrame({
        "rating":           places["rating"].fillna(0).values.astype(np.float32),
        "reviews_log":      np.log1p(places["reviews_count"].fillna(0).values).astype(np.float32),
        "has_rating":       places["has_rating"].fillna(False).astype(np.float32).values,
        "is_magnet":        places["is_magnet"].fillna(False).astype(np.float32).values,
        "is_long_tail":     places["is_long_tail"].fillna(False).astype(np.float32).values,
        "magnet_strength":  places["magnet_strength"].fillna(0).values.astype(np.float32),
        "qualpctl_in_cat":  places["review_quality_pctl_in_cat"].fillna(0.5).values.astype(np.float32),
    })
    feat = pd.concat([plexis_oh, pc2_oh, brand_oh, num], axis=1)
    print(f"  place feature matrix: {feat.shape}")
    X = feat.values.astype(float)
    what_emb, var_what = fit_pca_64(X, "place_features")
    what_df = pd.DataFrame(what_emb, columns=[f"d{i}" for i in range(64)])
    what_df.insert(0, "id", places["id"].values)
    what_df.to_parquet(ROOT / "places/place_embedding_what_64d.parquet", index=False)
    print(f"  place_embedding_what_64d: {what_df.shape}")

    # ============== COMBINED 128d per place ==============
    print("\n=== COMBINED 128d per place ===")
    # For each place, look up its hex's where embedding
    places_hex = places[["id","hex9_id"]].copy()
    place_where = places_hex.merge(where_df, on="hex9_id", how="left")
    # Some places may have hex9_ids not in universe → fill with 0
    where_cols = [f"d{i}" for i in range(64)]
    for c in where_cols:
        place_where[c] = place_where[c].fillna(0)

    # Concat
    what_arr = what_emb.astype(np.float32)
    where_arr = place_where[where_cols].values.astype(np.float32)
    combined_arr = np.hstack([what_arr, where_arr])  # 128d
    combined_df = pd.DataFrame(combined_arr, columns=[f"d{i}" for i in range(128)])
    combined_df.insert(0, "id", places["id"].values)
    combined_df.to_parquet(ROOT / "places/place_embedding_combined_128d.parquet", index=False)
    print(f"  place_embedding_combined_128d: {combined_df.shape}")

    # ============== COMBINED 128d per hex ==============
    print("\n=== COMBINED 128d per hex9 ===")
    # Per hex: where + mean(what of places in hex)
    place_what_with_hex = pd.DataFrame(what_emb, columns=where_cols).assign(hex9_id=places["hex9_id"].values)
    hex_what_mean = place_what_with_hex.groupby("hex9_id")[where_cols].mean().reset_index()
    # Merge with where + reindex to full universe
    h9_full = h9[["hex9_id"]].merge(hex_what_mean, on="hex9_id", how="left")
    h9_full = h9_full.merge(where_df, on="hex9_id", how="left", suffixes=("_what","_where"))
    for c in where_cols:
        h9_full[f"{c}_what"] = h9_full[f"{c}_what"].fillna(0)
        h9_full[f"{c}_where"] = h9_full[f"{c}_where"].fillna(0)

    what_part = h9_full[[f"{c}_what" for c in where_cols]].values
    where_part = h9_full[[f"{c}_where" for c in where_cols]].values
    hex_combined = np.hstack([what_part, where_part]).astype(np.float32)
    hex_comb_df = pd.DataFrame(hex_combined, columns=[f"d{i}" for i in range(128)])
    hex_comb_df.insert(0, "hex9_id", h9_full["hex9_id"].values)
    hex_comb_df.to_parquet(ROOT / "hex/hex9_embedding_combined_128d.parquet", index=False)
    print(f"  hex9_embedding_combined_128d: {hex_comb_df.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "where_input_features": len(feat_cols),
        "where_explained_variance": var_w,
        "what_input_features": int(feat.shape[1]),
        "what_explained_variance": var_what,
        "shapes": {
            "hex9_where_64d":          list(where_df.shape),
            "place_what_64d":          list(what_df.shape),
            "place_combined_128d":     list(combined_df.shape),
            "hex9_combined_128d":      list(hex_comb_df.shape),
        },
    }
    with open(ROOT / "hex/embeddings_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

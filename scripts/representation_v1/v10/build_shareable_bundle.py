"""Build the definitive shareable bundle: GCN-64 embedding + XGBoost-24 predictions."""
import pandas as pd
import os

ROOT = "/home/azureuser/digital-atlas-sgp"
raw = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
gcn_emb = pd.read_parquet(f"{ROOT}/data/hex_v10/gcn_results/gcn_embedding_64.parquet")
xgb_preds = pd.read_parquet(f"{ROOT}/data/hex_v10/embeddings/xgb_preds_24.parquet")

bundle = pd.DataFrame({
    "hex_id": raw["hex_id"],
    "lat": raw["lat"],
    "lng": raw["lng"],
    "parent_subzone": raw["parent_subzone"],
    "parent_pa": raw["parent_pa"],
})

# 64-dim GCN embedding (similarity representation)
for i in range(64):
    col = f"g{i}"
    bundle[col] = gcn_emb[col].values

# 24-dim XGBoost predicted category counts (gap analysis)
cat_cols = sorted([c for c in raw.columns if c.startswith("pc_cat_") and c not in {"pc_cat_hhi", "pc_cat_entropy"}])
for i, c in enumerate(cat_cols):
    clean = c.replace("pc_cat_", "pred_")
    bundle[clean] = xgb_preds[f"x{i}"].values

out_path = f"{ROOT}/data/hex_v10/hex_shareable_bundle.parquet"
bundle.to_parquet(out_path, index=False)
print(f"Bundle shape: {bundle.shape}")
print(f"Columns: 5 identity + 64 GCN embedding + 24 XGBoost predictions = 93")
print(f"Parquet size: {os.path.getsize(out_path)/1024/1024:.1f} MB")

# Also save as CSV for easy sharing
csv_path = f"{ROOT}/data/hex_v10/hex_shareable_bundle.csv"
bundle.to_csv(csv_path, index=False)
print(f"CSV size: {os.path.getsize(csv_path)/1024/1024:.1f} MB")

print("\nSample row:")
print(bundle.iloc[0])

"""Validate place2vec on server."""
import pandas as pd
import numpy as np
import json

ROOT = "/home/azureuser/digital-atlas-sgp"
pv = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors.parquet")
pvn = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors_normalized.parquet")
hex_df = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")

vec_cols = [c for c in pv.columns if c.startswith("v")]
V = pvn[vec_cols].to_numpy()
norms = np.linalg.norm(V, axis=1, keepdims=True)
norms[norms < 1e-9] = 1
Vn = V / norms

print(f"Place vectors: {pv.shape[0]:,} x {len(vec_cols)}-dim")

# TEST 1: Within-brand similarity
print("\n=== TEST 1: Within-brand similarity ===")
for brand_name in ["Starbucks", "FairPrice", "7-Eleven", "McDonald's", "Toast Box", "Ya Kun Kaya Toast"]:
    bp = pv[pv["brand"] == brand_name]
    if len(bp) < 5:
        continue
    indices = bp.index[:min(50, len(bp))].tolist()
    vecs = Vn[indices]
    pair_sims = vecs @ vecs.T
    np.fill_diagonal(pair_sims, 0)
    n = len(indices)
    mean_sim = pair_sims.sum() / (n * (n - 1))
    print(f"  {brand_name:<20} ({len(bp):>3} locs): within-brand sim = {mean_sim:.3f}")

# TEST 2: Within vs cross category
print("\n=== TEST 2: Within vs cross category ===")
np.random.seed(42)
for cat in ["Cafe & Coffee", "Restaurant", "Shopping & Retail", "Bar & Nightlife", "Health & Medical", "Education"]:
    ci = pv[pv["main_category"] == cat].index[:100].tolist()
    oi = pv[pv["main_category"] != cat].sample(min(100, len(pv) - len(ci)), random_state=42).index.tolist()
    if len(ci) < 20:
        continue
    cv = Vn[ci]
    ov = Vn[oi]
    within = float((cv @ cv.T).mean())
    across = float((cv @ ov.T).mean())
    print(f"  {cat:<25} within={within:.3f}  across={across:.3f}  ratio={within/(across+1e-9):.1f}x")

# TEST 3: Starbucks CBD vs Starbucks HDB
print("\n=== TEST 3: Same brand, different context ===")
hex_pa = dict(zip(hex_df["hex_id"], hex_df["parent_pa"]))

with open(f"{ROOT}/data/hex_v10/place2vec_catalog.json") as f:
    catalog = json.load(f)
dim_names = catalog["dim_names"]

sb = pv[pv["name"].str.contains("Starbucks", case=False, na=False)].copy()
sb["pa"] = sb["hex_id"].map(hex_pa)
cbd_sb = sb[sb["pa"].isin(["DOWNTOWN CORE", "ORCHARD"])]
hdb_sb = sb[sb["pa"].isin(["BEDOK", "TAMPINES", "WOODLANDS", "YISHUN"])]

if len(cbd_sb) > 0 and len(hdb_sb) > 0:
    i1 = cbd_sb.index[0]
    i2 = hdb_sb.index[0]
    v1_raw = pv.loc[i1, vec_cols].values.astype(float)
    v2_raw = pv.loc[i2, vec_cols].values.astype(float)
    cos = float(np.dot(Vn[i1], Vn[i2]))
    diff = v1_raw - v2_raw
    print(f"  CBD: {pv.loc[i1, 'name'][:40]} ({cbd_sb.loc[i1, 'pa']})")
    print(f"  HDB: {pv.loc[i2, 'name'][:40]} ({hdb_sb.loc[i2, 'pa']})")
    print(f"  Cosine: {cos:.3f}")
    print(f"  Top differences:")
    top_diff = np.argsort(-np.abs(diff))[:10]
    for d in top_diff:
        name = dim_names[d] if d < len(dim_names) else f"v{d}"
        print(f"    {name:<30} CBD={v1_raw[d]:>8.3f}  HDB={v2_raw[d]:>8.3f}  diff={diff[d]:>+8.3f}")

# TEST 4: Place-pool per hex → hex similarity
print("\n=== TEST 4: Hex place-pool similarity ===")
hex_pool = pvn.groupby(pv["hex_id"])[vec_cols].mean()
print(f"  Hex pools: {hex_pool.shape}")

pool_v = hex_pool.values
pool_norms = np.linalg.norm(pool_v, axis=1, keepdims=True)
pool_norms[pool_norms < 1e-9] = 1
pool_n = pool_v / pool_norms

# Orchard vs others
orchard_hex = hex_df[hex_df["parent_pa"] == "ORCHARD"].nlargest(1, "pc_total")["hex_id"].iloc[0]
if orchard_hex in hex_pool.index:
    oi = list(hex_pool.index).index(orchard_hex)
    sims = pool_n @ pool_n[oi]
    order = np.argsort(-sims)
    print(f"  Orchard ({orchard_hex[:15]}) nearest by place-pool:")
    for j in order[1:8]:
        hid = hex_pool.index[j]
        pa = hex_pa.get(hid, "?")
        pc = int(hex_df[hex_df["hex_id"] == hid]["pc_total"].iloc[0]) if hid in hex_df["hex_id"].values else 0
        print(f"    pa={pa:<22} places={pc:>5}  sim={sims[j]:.3f}")

# Sentosa
sentosa_hex = hex_df[hex_df["parent_subzone"] == "SISZ01"].nlargest(1, "pc_total")["hex_id"].iloc[0]
if sentosa_hex in hex_pool.index:
    si = list(hex_pool.index).index(sentosa_hex)
    sims_s = pool_n @ pool_n[si]
    order_s = np.argsort(-sims_s)
    print(f"\n  Sentosa ({sentosa_hex[:15]}) nearest by place-pool:")
    for j in order_s[1:8]:
        hid = hex_pool.index[j]
        pa = hex_pa.get(hid, "?")
        pc = int(hex_df[hex_df["hex_id"] == hid]["pc_total"].iloc[0]) if hid in hex_df["hex_id"].values else 0
        print(f"    pa={pa:<22} places={pc:>5}  sim={sims_s[j]:.3f}")

# Bedok HDB
bedok_hex = hex_df[(hex_df["parent_pa"] == "BEDOK") & (hex_df["hdb_blocks"] > 10)].nlargest(1, "population")["hex_id"].iloc[0]
if bedok_hex in hex_pool.index:
    bi = list(hex_pool.index).index(bedok_hex)
    sims_b = pool_n @ pool_n[bi]
    order_b = np.argsort(-sims_b)
    print(f"\n  Bedok HDB ({bedok_hex[:15]}) nearest by place-pool:")
    for j in order_b[1:8]:
        hid = hex_pool.index[j]
        pa = hex_pa.get(hid, "?")
        pc = int(hex_df[hex_df["hex_id"] == hid]["pc_total"].iloc[0]) if hid in hex_df["hex_id"].values else 0
        print(f"    pa={pa:<22} places={pc:>5}  sim={sims_b[j]:.3f}")

print("\nDone.")

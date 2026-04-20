"""Hawker center analysis in Place2Vec. Run on server."""
import pandas as pd
import numpy as np

ROOT = "/home/azureuser/digital-atlas-sgp"
pv = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors_v2.parquet")
pvn = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors_v2_normalized.parquet")
hex_df = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
hex_pa = dict(zip(hex_df["hex_id"], hex_df["parent_pa"]))

vec_cols = [c for c in pvn.columns if c.startswith("v")]
V = pvn[vec_cols].to_numpy().astype("float32")
norms = np.linalg.norm(V, axis=1, keepdims=True)
norms[norms < 1e-9] = 1
Vn = V / norms

print("=" * 60)
print("HAWKER CENTERS IN PLACE2VEC")
print("=" * 60)

hawker = pv[pv["main_category"] == "Hawker & Street Food"]
print(f"\nHawker places: {len(hawker):,}")
print(f"  with micrograph: {int(hawker['has_micrograph'].sum()):,}")
print(f"  branded: {int(hawker['is_branded'].sum()):,}")
print(f"  in hexes: {hawker['hex_id'].nunique()}")
print(f"  tiers: {dict(hawker['price_tier'].value_counts())}")

# Context comparison
print("\n--- Hawkers by urban context ---")
hawker_pa = hawker["hex_id"].map(hex_pa)
ctxs = {
    "CBD/Tourist": ["DOWNTOWN CORE", "OUTRAM", "ROCHOR", "SINGAPORE RIVER", "MUSEUM"],
    "HDB Heartland": ["BEDOK", "TAMPINES", "YISHUN", "JURONG WEST", "HOUGANG", "WOODLANDS", "TOA PAYOH"],
    "Industrial": ["TUAS", "SUNGEI KADUT", "PIONEER", "BOON LAY"],
}
for label, pas in ctxs.items():
    sub = hawker[hawker_pa.isin(pas)]
    if len(sub) < 5:
        continue
    idx = sub.index[:50].tolist()
    vecs = Vn[idx]
    within = float((vecs @ vecs.T).mean())
    print(f"  {label:<20} {len(sub):>5} hawkers  within-sim={within:.3f}")

cbd_idx = hawker[hawker_pa.isin(ctxs["CBD/Tourist"])].index[:50].tolist()
hdb_idx = hawker[hawker_pa.isin(ctxs["HDB Heartland"])].index[:50].tolist()
if cbd_idx and hdb_idx:
    cross = float((Vn[cbd_idx] @ Vn[hdb_idx].T).mean())
    print(f"  CBD vs HDB hawker cross-sim: {cross:.3f}")

# Famous centres
print("\n--- Famous hawker centres (by PA match) ---")
famous = [
    ("Chinatown/Maxwell area", "OUTRAM"),
    ("Lau Pa Sat / CBD", "DOWNTOWN CORE"),
    ("Old Airport Rd / Geylang", "GEYLANG"),
    ("Bedok area", "BEDOK"),
    ("Tampines area", "TAMPINES"),
    ("Toa Payoh area", "TOA PAYOH"),
    ("Ang Mo Kio area", "ANG MO KIO"),
]
for name, pa in famous:
    stalls = hawker[hawker_pa == pa]
    if len(stalls) < 3:
        continue
    idx = stalls.index[:30].tolist()
    vecs = Vn[idx]
    within = float((vecs @ vecs.T).mean())
    all_hawk_idx = hawker.index[:300].tolist()
    all_mean = Vn[all_hawk_idx].mean(axis=0)
    all_mean /= np.linalg.norm(all_mean) + 1e-9
    c_mean = vecs.mean(axis=0)
    c_mean /= np.linalg.norm(c_mean) + 1e-9
    dist = float(np.dot(c_mean, all_mean))
    print(f"  {name:<25} {len(stalls):>4} stalls  within={within:.3f}  vs-avg={dist:.3f}")

# Cross-category neighbors
print("\n--- Chinatown hawker -> non-hawker neighbors ---")
ct_hawk = hawker[hawker_pa == "OUTRAM"]
if len(ct_hawk):
    qi = ct_hawk.index[0]
    sims = Vn @ Vn[qi]
    order = np.argsort(-sims)
    print(f"  Query: {pv.iloc[qi]['name'][:50]}")
    count = 0
    for j in order[1:]:
        if pv.iloc[j]["main_category"] != "Hawker & Street Food":
            r = pv.iloc[j]
            pa = hex_pa.get(r["hex_id"], "")
            print(f"    {r['name'][:35]:<35} {r['main_category']:<22} pa={pa:<16} sim={sims[j]:.3f}")
            count += 1
            if count >= 8:
                break

print("\n--- Bedok hawker -> non-hawker neighbors ---")
bd_hawk = hawker[hawker_pa == "BEDOK"]
if len(bd_hawk):
    qi = bd_hawk.index[0]
    sims = Vn @ Vn[qi]
    order = np.argsort(-sims)
    print(f"  Query: {pv.iloc[qi]['name'][:50]}")
    count = 0
    for j in order[1:]:
        if pv.iloc[j]["main_category"] != "Hawker & Street Food":
            r = pv.iloc[j]
            pa = hex_pa.get(r["hex_id"], "")
            print(f"    {r['name'][:35]:<35} {r['main_category']:<22} pa={pa:<16} sim={sims[j]:.3f}")
            count += 1
            if count >= 8:
                break

# Hex-level hawker signal
print("\n--- Hex-level hawker signal ---")
hex_wh = hex_df[hex_df["hawker_centres"] > 0]
hex_nh = hex_df[(hex_df["hawker_centres"] == 0) & (hex_df["pc_total"] > 10)]
for c in ["pc_cat_hawker_street_food", "sfa_eating_establishments", "population", "hdb_blocks", "walkability_score"]:
    w = hex_wh[c].mean()
    n = hex_nh[c].mean()
    print(f"  {c:<30}  hawker_hex={w:>8.1f}  no_hawker={n:>8.1f}  ratio={w / (n + 0.001):.1f}x")

# Hawker micrograph profile
print("\n--- Hawker micrograph profile ---")
hawk_mg = hawker[hawker["has_micrograph"] == 1]
if len(hawk_mg) > 10:
    raw = pv.loc[hawk_mg.index[:500], vec_cols].astype(float)
    print(f"  {len(hawk_mg):,} hawkers with micrograph")
    print(f"  T1 transit:       {raw['v0'].mean():.3f}")
    print(f"  T2 competitor:    {raw['v1'].mean():.3f}")
    print(f"  T3 complementary: {raw['v2'].mean():.3f}")
    print(f"  T4 demand:        {raw['v3'].mean():.3f}")
    print(f"  anchor_count:     {raw['v4'].mean():.1f}")
    print(f"  comp_pressure:    {raw['v5'].mean():.3f}")

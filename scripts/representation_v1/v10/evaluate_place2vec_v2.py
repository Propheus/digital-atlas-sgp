"""Place2Vec v2 evaluation — context-only vectors. Run on server."""
import json, time
import numpy as np
import pandas as pd
from collections import Counter

ROOT = "/home/azureuser/digital-atlas-sgp"
t0 = time.time()
pv = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors_v2.parquet")
pvn = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors_v2_normalized.parquet")
hex_df = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")
hex_pa = dict(zip(hex_df["hex_id"], hex_df["parent_pa"]))

vec_cols = [c for c in pvn.columns if c.startswith("v")]
V = pvn[vec_cols].to_numpy().astype("float32")
norms = np.linalg.norm(V, axis=1, keepdims=True); norms[norms<1e-9]=1
Vn = V / norms
cats = pv["main_category"].to_numpy(dtype=str)
tiers = pv["price_tier"].to_numpy(dtype=str)
results = {"version": "v2", "design": "context-only, no category/tier one-hot", "vec_dim": len(vec_cols), "n_places": len(pv)}

print(f"Place vectors v2: {pv.shape[0]:,} x {len(vec_cols)}-dim")

# 1. CROSS-CATEGORY SIMILARITY (the key test)
print("\n1. Cross-category similarity in same hex...")
# For hexes with both cafes and restaurants, measure similarity
cross_cat = []
for hid in pv["hex_id"].value_counts().head(100).index:
    hp = pv[pv["hex_id"] == hid]
    cafe_idx = hp[hp["main_category"] == "Cafe & Coffee"].index.tolist()
    rest_idx = hp[hp["main_category"] == "Restaurant"].index.tolist()
    if len(cafe_idx) >= 3 and len(rest_idx) >= 3:
        cv = Vn[cafe_idx[:10]]
        rv = Vn[rest_idx[:10]]
        cross = float((cv @ rv.T).mean())
        within_c = float((cv @ cv.T).mean())
        within_r = float((rv @ rv.T).mean())
        cross_cat.append({"hex": hid, "cross_cafe_rest": cross, "within_cafe": within_c, "within_rest": within_r})
if cross_cat:
    mean_cross = np.mean([x["cross_cafe_rest"] for x in cross_cat])
    mean_within = np.mean([(x["within_cafe"] + x["within_rest"]) / 2 for x in cross_cat])
    print(f"  Same-hex cafe vs restaurant: {mean_cross:.3f}")
    print(f"  Same-hex within-category:    {mean_within:.3f}")
    print(f"  Cross/within ratio: {mean_cross/mean_within:.2f} (target: close to 1.0)")
    results["cross_category_same_hex"] = {"cross": round(mean_cross, 3), "within": round(mean_within, 3)}

# 2. SAME BRAND DIFFERENT CONTEXT
print("\n2. Same brand, different context...")
brand_spread = {}
for brand in ["Starbucks", "FairPrice", "McDonald's", "7-Eleven", "Watsons"]:
    bp = pv[pv["brand"] == brand]
    if len(bp) < 10: continue
    bp_pa = bp["hex_id"].map(hex_pa)
    cbd_idx = bp[bp_pa.isin(["DOWNTOWN CORE", "ORCHARD", "SINGAPORE RIVER"])].index[:20].tolist()
    hdb_idx = bp[bp_pa.isin(["BEDOK", "TAMPINES", "WOODLANDS", "YISHUN", "JURONG WEST"])].index[:20].tolist()
    if len(cbd_idx) < 3 or len(hdb_idx) < 3: continue
    cv = Vn[cbd_idx]; hv = Vn[hdb_idx]
    within_cbd = float((cv @ cv.T).mean())
    within_hdb = float((hv @ hv.T).mean())
    cross = float((cv @ hv.T).mean())
    brand_spread[brand] = {"within_cbd": round(within_cbd, 3), "within_hdb": round(within_hdb, 3), "cross_cbd_hdb": round(cross, 3)}
    print(f"  {brand:<15} CBD_within={within_cbd:.3f}  HDB_within={within_hdb:.3f}  CBD_vs_HDB={cross:.3f}")
results["brand_context_spread"] = brand_spread

# 3. kNN CATEGORY PREDICTION (should be LOWER than v1's 99.5%)
print("\n3. kNN category prediction (should be lower than v1)...")
np.random.seed(42)
sample_idx = np.random.choice(len(pv), min(5000, len(pv)), replace=False)
sv = Vn[sample_idx]; sc = cats[sample_idx]; st = tiers[sample_idx]
sm = sv @ sv.T; np.fill_diagonal(sm, -1)
c1 = c5 = 0
for i in range(len(sample_idx)):
    top5 = np.argsort(-sm[i])[:5]
    if sc[top5[0]] == sc[i]: c1 += 1
    if sc[i] in sc[top5]: c5 += 1
cat_k1 = c1/len(sample_idx); cat_k5 = c5/len(sample_idx)
print(f"  k=1 accuracy: {cat_k1:.1%} (v1 was 99.5%)")
print(f"  k=5 hit rate: {cat_k5:.1%} (v1 was 99.8%)")
results["knn_category"] = {"k1": round(cat_k1, 3), "k5": round(cat_k5, 3)}

# 4. kNN TIER PREDICTION
t1 = ta = nt = 0
for i in range(len(sample_idx)):
    if not st[i]: continue
    nt += 1
    top1_tier = st[np.argsort(-sm[i])[0]]
    if top1_tier == st[i]: t1 += 1
    tier_ord = {"Luxury":0,"Premium":1,"Mid":2,"Value":3,"Budget":4}
    if top1_tier and abs(tier_ord.get(top1_tier,2)-tier_ord.get(st[i],2)) <= 1: ta += 1
print(f"  Tier k=1 exact: {t1/nt:.1%}   adjacent: {ta/nt:.1%}")
results["knn_tier"] = {"exact": round(t1/nt, 3), "adjacent": round(ta/nt, 3)}

# 5. HEX PLACE-POOL
print("\n5. Hex place-pool kNN PA accuracy...")
hex_pool = pvn.groupby(pv["hex_id"])[vec_cols].mean()
hp_v = hex_pool.values
hp_n = np.linalg.norm(hp_v, axis=1, keepdims=True); hp_n[hp_n<1e-9]=1
hp_vn = hp_v / hp_n
hp_ids = hex_pool.index.values
hp_pa = np.array([hex_pa.get(h, "") for h in hp_ids])
active = hp_pa != ""
hpv = hp_vn[active]; hpl = hp_pa[active]
hsm = hpv @ hpv.T; np.fill_diagonal(hsm, -1)
hc = ht = 0
for i in range(len(hpv)):
    top5 = np.argsort(-hsm[i])[:5]
    hc += sum(1 for j in top5 if hpl[j] == hpl[i])
    ht += 5
pool_acc = hc/ht
print(f"  Pool kNN PA accuracy: {pool_acc:.3f}")
results["hex_pool_knn"] = round(pool_acc, 3)

# 6. NAMED EXAMPLES (the real test)
print("\n6. Named examples — cross-category neighbors...")
for qname, qfilter in [
    ("Starbucks ION Orchard", pv[(pv["name"].str.contains("Starbucks", case=False, na=False)) & (pv["hex_id"].map(hex_pa) == "ORCHARD")]),
    ("McDonald's Bedok", pv[(pv["name"].str.contains("McDonald", case=False, na=False)) & (pv["hex_id"].map(hex_pa) == "BEDOK")]),
    ("Hawker in Chinatown", pv[(pv["main_category"] == "Hawker & Street Food") & (pv["hex_id"].map(hex_pa) == "OUTRAM")]),
]:
    if len(qfilter) == 0: continue
    qi = qfilter.index[0]
    sims_q = Vn @ Vn[qi]
    order = np.argsort(-sims_q)[1:8]
    print(f"\n  {qname} ({pv.iloc[qi]['main_category']}, {hex_pa.get(pv.iloc[qi]['hex_id'],'')})")
    for j in order:
        r = pv.iloc[j]
        print(f"    {r['name'][:35]:<35} {r['main_category']:<22} tier={r['price_tier']:<8} pa={hex_pa.get(r['hex_id'],''):<18} sim={sims_q[j]:.3f}")
    results.setdefault("named_examples", {})[qname] = [
        {"name": pv.iloc[j]["name"][:40], "cat": pv.iloc[j]["main_category"], "tier": pv.iloc[j]["price_tier"],
         "pa": hex_pa.get(pv.iloc[j]["hex_id"], ""), "sim": round(float(sims_q[j]), 3)} for j in order
    ]

with open(f"{ROOT}/data/hex_v10/place2vec_v2_evaluation.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print(f"\n{'='*60}")
print(f"v2 SUMMARY: {len(vec_cols)}-dim context-only vectors")
print(f"  Cross-cat same-hex similarity: {results.get('cross_category_same_hex',{}).get('cross','?')}")
print(f"  Category kNN k=1: {cat_k1:.1%} (v1: 99.5%)")
print(f"  Hex pool kNN PA:  {pool_acc:.3f}")
print(f"  Time: {time.time()-t0:.0f}s")

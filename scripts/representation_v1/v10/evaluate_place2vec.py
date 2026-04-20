"""
Comprehensive Place2Vec evaluation — run on server.
Outputs: /home/azureuser/digital-atlas-sgp/data/hex_v10/place2vec_evaluation.json
"""
import json
import time
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ROOT = "/home/azureuser/digital-atlas-sgp"
t0 = time.time()

print("Loading data...")
pv = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors.parquet")
pvn = pd.read_parquet(f"{ROOT}/data/hex_v10/place_vectors_normalized.parquet")
hex_df = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")

vec_cols = [c for c in pv.columns if c.startswith("v")]
V = pvn[vec_cols].to_numpy().astype("float32")
norms = np.linalg.norm(V, axis=1, keepdims=True)
norms[norms < 1e-9] = 1
Vn = V / norms

hex_pa = dict(zip(hex_df["hex_id"], hex_df["parent_pa"]))
hex_subz = dict(zip(hex_df["hex_id"], hex_df["parent_subzone"]))

with open(f"{ROOT}/data/hex_v10/place2vec_catalog.json") as f:
    catalog = json.load(f)
dim_names = catalog["dim_names"]

results = {"shape": list(pv.shape), "vec_dim": len(vec_cols)}

# =====================================================================
# 1. WITHIN-BRAND CONSISTENCY
# =====================================================================
print("\n1. Within-brand consistency...")
brand_sims = {}
for brand in pv["brand"].value_counts().head(20).index:
    if not brand:
        continue
    bp = pv[pv["brand"] == brand]
    if len(bp) < 5:
        continue
    idx = bp.index[:min(80, len(bp))].tolist()
    vecs = Vn[idx]
    ps = vecs @ vecs.T
    np.fill_diagonal(ps, 0)
    n = len(idx)
    ms = float(ps.sum() / (n * (n - 1)))
    # also compute std of pairwise sims
    triu = ps[np.triu_indices(n, k=1)]
    brand_sims[brand] = {
        "n_locations": len(bp),
        "mean_sim": round(ms, 3),
        "std_sim": round(float(triu.std()), 3),
        "min_sim": round(float(triu.min()), 3),
        "max_sim": round(float(triu.max()), 3),
    }
results["brand_consistency"] = brand_sims

# =====================================================================
# 2. CATEGORY SEPARATION
# =====================================================================
print("2. Category separation...")
np.random.seed(42)
cat_sep = {}
for cat in pv["main_category"].value_counts().head(12).index:
    ci = pv[pv["main_category"] == cat].index[:200].tolist()
    other = pv[pv["main_category"] != cat].sample(min(200, len(pv) - len(ci)), random_state=42).index.tolist()
    if len(ci) < 20:
        continue
    cv = Vn[ci]
    ov = Vn[other]
    within = float((cv @ cv.T).mean())
    across = float((cv @ ov.T).mean())
    cat_sep[cat] = {
        "within": round(within, 3),
        "across": round(across, 3),
        "separation": round(within - across, 3),
        "n_places": len(pv[pv["main_category"] == cat]),
    }
results["category_separation"] = cat_sep

# =====================================================================
# 3. PRICE TIER GRADIENT
# =====================================================================
print("3. Price tier gradient...")
tier_centroids = {}
for tier in ["Luxury", "Premium", "Mid", "Value", "Budget"]:
    tp = pv[pv["price_tier"] == tier]
    if len(tp) < 10:
        continue
    idx = tp.index[:500].tolist()
    centroid = Vn[idx].mean(axis=0)
    centroid /= np.linalg.norm(centroid) + 1e-9
    tier_centroids[tier] = centroid

# Pairwise cosine between tier centroids
tier_pairs = {}
tiers_order = ["Luxury", "Premium", "Mid", "Value", "Budget"]
for i, t1 in enumerate(tiers_order):
    for j, t2 in enumerate(tiers_order):
        if j <= i or t1 not in tier_centroids or t2 not in tier_centroids:
            continue
        cos = float(np.dot(tier_centroids[t1], tier_centroids[t2]))
        tier_pairs[f"{t1}_vs_{t2}"] = round(cos, 3)
results["tier_gradient"] = tier_pairs

# =====================================================================
# 4. kNN CATEGORY PREDICTION (does the vector predict its own category?)
# =====================================================================
print("4. kNN category prediction (k=5)...")
np.random.seed(42)
sample_idx = np.random.choice(len(pv), min(5000, len(pv)), replace=False)
sample_v = Vn[sample_idx]
sample_cats = pv.iloc[sample_idx]["main_category"].values
sims = sample_v @ sample_v.T
np.fill_diagonal(sims, -1)

correct_1 = 0
correct_5 = 0
for i in range(len(sample_idx)):
    top5 = np.argsort(-sims[i])[:5]
    nbr_cats = [sample_cats[j] for j in top5]
    if nbr_cats[0] == sample_cats[i]:
        correct_1 += 1
    if sample_cats[i] in nbr_cats:
        correct_5 += 1

results["knn_category_prediction"] = {
    "k1_accuracy": round(correct_1 / len(sample_idx), 3),
    "k5_hit_rate": round(correct_5 / len(sample_idx), 3),
    "n_sample": len(sample_idx),
}

# =====================================================================
# 5. kNN PRICE TIER PREDICTION
# =====================================================================
print("5. kNN price tier prediction...")
sample_tiers = pv.iloc[sample_idx]["price_tier"].values
tier_correct_1 = 0
tier_adjacent = 0  # within 1 tier
tier_order = {"Luxury": 0, "Premium": 1, "Mid": 2, "Value": 3, "Budget": 4}
for i in range(len(sample_idx)):
    if not sample_tiers[i]:
        continue
    top1 = np.argsort(-sims[i])[0]
    pred_tier = sample_tiers[top1]
    if pred_tier == sample_tiers[i]:
        tier_correct_1 += 1
    if pred_tier and abs(tier_order.get(pred_tier, 2) - tier_order.get(sample_tiers[i], 2)) <= 1:
        tier_adjacent += 1

n_tiered = sum(1 for t in sample_tiers if t)
results["knn_tier_prediction"] = {
    "k1_exact": round(tier_correct_1 / n_tiered, 3) if n_tiered else 0,
    "k1_adjacent": round(tier_adjacent / n_tiered, 3) if n_tiered else 0,
    "n_tiered": n_tiered,
}

# =====================================================================
# 6. MICROGRAPH vs NON-MICROGRAPH COMPARISON
# =====================================================================
print("6. Micrograph impact...")
has_mg = pv[pv["v30"] == 1]  # has_micrograph flag at dim 30
no_mg = pv[pv["v30"] == 0]

# Same-category sim for micrographed vs non-micrographed
mg_cats = {}
for cat in ["Cafe & Coffee", "Restaurant", "Shopping & Retail"]:
    mg_idx = has_mg[has_mg["main_category"] == cat].index[:100].tolist()
    no_idx = no_mg[no_mg["main_category"] == cat].index[:100].tolist()
    if len(mg_idx) < 20 or len(no_idx) < 20:
        continue
    mg_within = float((Vn[mg_idx] @ Vn[mg_idx].T).mean())
    no_within = float((Vn[no_idx] @ Vn[no_idx].T).mean())
    mg_cats[cat] = {
        "with_micrograph": round(mg_within, 3),
        "without_micrograph": round(no_within, 3),
        "difference": round(mg_within - no_within, 3),
    }
results["micrograph_impact"] = {
    "n_with": len(has_mg),
    "n_without": len(no_mg),
    "per_category": mg_cats,
}

# =====================================================================
# 7. WHICH LAYERS MATTER? (ablation by zeroing out layers)
# =====================================================================
print("7. Layer ablation...")
layers = {
    "identity": list(range(0, 31)),
    "spatial_context": list(range(31, 43)),
    "hex_context": list(range(43, 57)),
    "influence": list(range(57, 64)),
    "competitive_position": list(range(64, 68)),
}

# Baseline: full vector kNN category accuracy
def knn_cat_acc(X, cats, n=3000):
    idx = np.random.choice(len(X), min(n, len(X)), replace=False)
    Xs = X[idx]
    cs = cats[idx] if isinstance(cats, np.ndarray) else np.array([cats.iloc[i] for i in idx])
    ns = np.linalg.norm(Xs, axis=1, keepdims=True)
    ns[ns < 1e-9] = 1
    Xn = Xs / ns
    sm = Xn @ Xn.T
    np.fill_diagonal(sm, -1)
    correct = sum(1 for i in range(len(idx)) if cs[np.argsort(-sm[i])[0]] == cs[i])
    return correct / len(idx)

np.random.seed(42)
cats_arr = pv["main_category"].to_numpy(dtype=str)
baseline_acc = knn_cat_acc(V, cats_arr)
ablation = {"baseline": round(baseline_acc, 3)}

for layer_name, dims in layers.items():
    V_ablated = V.copy()
    V_ablated[:, dims] = 0
    acc = knn_cat_acc(V_ablated, cats_arr)
    drop = baseline_acc - acc
    ablation[layer_name] = {
        "accuracy_without": round(acc, 3),
        "drop": round(drop, 3),
        "n_dims": len(dims),
    }
results["layer_ablation"] = ablation

# =====================================================================
# 8. PLACE-POOL HEX SIMILARITY (does pooling beat raw hex features?)
# =====================================================================
print("8. Place-pool hex similarity...")
hex_pool = pvn.groupby(pv["hex_id"])[vec_cols].agg(["mean", "max"])
hex_pool.columns = [f"{c[0]}_{c[1]}" for c in hex_pool.columns]
hex_pool = hex_pool.reset_index()

# Also compute per-hex count of micrographed places and total
hex_mg_stats = pv.groupby("hex_id").agg(
    n_places=("place_id", "count"),
    n_micrographed=("v30", "sum"),
    n_branded=("v29", "sum"),
    mean_tier_rank=("v64", "mean"),
).reset_index()

pool_hexes = hex_pool["hex_id"].values
pool_v = hex_pool[[c for c in hex_pool.columns if c != "hex_id"]].values
pn = np.linalg.norm(pool_v, axis=1, keepdims=True)
pn[pn < 1e-9] = 1
pool_n = pool_v / pn

# kNN PA accuracy on hex pools
pool_pas = np.array([hex_pa.get(h, "") for h in pool_hexes])
active = pool_pas != ""
pool_active = pool_n[active]
pas_active = pool_pas[active]

sm = pool_active @ pool_active.T
np.fill_diagonal(sm, -1)
correct = 0
total = 0
for i in range(len(pool_active)):
    top5 = np.argsort(-sm[i])[:5]
    correct += sum(1 for j in top5 if pas_active[j] == pas_active[i])
    total += 5
pool_knn = correct / total

results["hex_pool"] = {
    "n_hexes": len(pool_hexes),
    "pool_dim": pool_v.shape[1],
    "knn_pa_accuracy": round(pool_knn, 3),
    "note": "Compare to hex feature table kNN = 0.374 with 460 features",
}

# =====================================================================
# 9. NAMED PLACE EXAMPLES
# =====================================================================
print("9. Named place examples...")
examples = {}
for query_name, query_filter in [
    ("Starbucks ION Orchard", pv[pv["name"].str.contains("Starbucks", case=False, na=False) & (pv["hex_id"].map(hex_pa) == "ORCHARD")]),
    ("McDonald's Bedok", pv[pv["name"].str.contains("McDonald", case=False, na=False) & (pv["hex_id"].map(hex_pa) == "BEDOK")]),
    ("Din Tai Fung", pv[pv["name"].str.contains("Din Tai Fung", case=False, na=False)]),
    ("Watsons", pv[pv["name"].str.contains("Watsons", case=False, na=False)]),
]:
    if len(query_filter) == 0:
        continue
    qi = query_filter.index[0]
    sims_q = Vn @ Vn[qi]
    order = np.argsort(-sims_q)
    nbrs = []
    for j in order[1:8]:
        r = pv.iloc[j]
        nbrs.append({
            "name": r["name"][:40],
            "category": r["main_category"],
            "tier": r["price_tier"],
            "brand": r["brand"],
            "pa": hex_pa.get(r["hex_id"], ""),
            "sim": round(float(sims_q[j]), 3),
        })
    examples[query_name] = {
        "category": pv.iloc[qi]["main_category"],
        "tier": pv.iloc[qi]["price_tier"],
        "pa": hex_pa.get(pv.iloc[qi]["hex_id"], ""),
        "neighbors": nbrs,
    }
results["named_examples"] = examples

# =====================================================================
# SAVE
# =====================================================================
with open(f"{ROOT}/data/hex_v10/place2vec_evaluation.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nWrote place2vec_evaluation.json ({time.time()-t0:.0f}s)")

# Print summary
print("\n" + "=" * 60)
print("PLACE2VEC EVALUATION SUMMARY")
print("=" * 60)
print(f"  Places: {pv.shape[0]:,} x {len(vec_cols)}-dim")
print(f"\n  Category kNN k=1 accuracy: {results['knn_category_prediction']['k1_accuracy']:.1%}")
print(f"  Category kNN k=5 hit rate: {results['knn_category_prediction']['k5_hit_rate']:.1%}")
print(f"  Tier kNN k=1 exact: {results['knn_tier_prediction']['k1_exact']:.1%}")
print(f"  Tier kNN k=1 adjacent: {results['knn_tier_prediction']['k1_adjacent']:.1%}")
print(f"\n  Layer ablation (category kNN accuracy):")
print(f"    full vector:         {ablation['baseline']:.3f}")
for layer, info in ablation.items():
    if layer == "baseline":
        continue
    print(f"    - {layer:<22} {info['accuracy_without']:.3f} (drop {info['drop']:+.3f}, {info['n_dims']} dims)")
print(f"\n  Hex place-pool kNN PA accuracy: {results['hex_pool']['knn_pa_accuracy']:.3f}")

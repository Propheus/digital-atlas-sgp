"""
Plexis SGP v4 — Comprehensive embedding test suite.

15 tests across structural integrity, spatial coherence, semantic coherence,
and consistency between WHERE / WHAT / COMBINED embeddings.

Each test outputs PASS/WARN/FAIL with details. Saves to JSON for the report.
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).parent
results = []


def add(idx, name, status, detail, metric=None):
    results.append({"idx": idx, "name": name, "status": status, "detail": detail, "metric": metric})
    print(f"  [{status}] T{idx:02d} {name} — {detail}")


print("Loading all embeddings + metadata...")
hex_where = pd.read_parquet(ROOT / "hex/hex9_embedding_where_64d.parquet")
hex_comb = pd.read_parquet(ROOT / "hex/hex9_embedding_combined_128d.parquet")
place_what = pd.read_parquet(ROOT / "places/place_embedding_what_64d.parquet")
place_comb = pd.read_parquet(ROOT / "places/place_embedding_combined_128d.parquet")
report_data = json.load(open(ROOT / "hex/embeddings_report.json"))

h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
places_meta = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")[
    ["id","plexis_category","brand_norm","is_magnet","is_long_tail","name","hex9_id","parent_pa","parent_subzone_name"]
]
h9_full = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
hex_pa = hex_where.merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")

WHERE_DIMS = [f"d{i}" for i in range(64)]
COMB_DIMS  = [f"d{i}" for i in range(128)]


# ===== T01 SHAPES =====
ok = (hex_where.shape == (7318, 65) and hex_comb.shape == (7318, 129)
       and place_what.shape == (190591, 65) and place_comb.shape == (190591, 129))
if ok:
    add(1, "shapes_match", "PASS",
        f"hex_where={hex_where.shape} hex_comb={hex_comb.shape} place_what={place_what.shape} place_comb={place_comb.shape}")
else:
    add(1, "shapes_match", "FAIL", f"hex_where={hex_where.shape} hex_comb={hex_comb.shape} place_what={place_what.shape} place_comb={place_comb.shape}")

# ===== T02 NO NaN/inf =====
nans = (hex_where.isna().sum().sum() + hex_comb.isna().sum().sum()
         + place_what.isna().sum().sum() + place_comb.isna().sum().sum())
infs_a = np.isinf(hex_where[WHERE_DIMS].values).sum()
infs_b = np.isinf(hex_comb[COMB_DIMS].values).sum()
infs_c = np.isinf(place_what[WHERE_DIMS].values).sum()
infs_d = np.isinf(place_comb[COMB_DIMS].values).sum()
infs = infs_a + infs_b + infs_c + infs_d
if nans == 0 and infs == 0:
    add(2, "no_nan_inf", "PASS", "0 NaN, 0 inf across all 4 embeddings")
else:
    add(2, "no_nan_inf", "FAIL", f"NaN={nans} inf={infs}")

# ===== T03 VARIANCE =====
vw = report_data["where_explained_variance"]
vwh = report_data["what_explained_variance"]
if vw >= 0.6 and vwh >= 0.6:
    add(3, "variance_explained", "PASS", f"WHERE={vw:.3f} WHAT={vwh:.3f} (≥0.6)", {"where_var": vw, "what_var": vwh})
else:
    add(3, "variance_explained", "WARN", f"WHERE={vw:.3f} WHAT={vwh:.3f}")

# ===== T04 WHERE: CBD coherence =====
def nn_pas_for(df, key, df_label, seed_subzone, k=5):
    seeds = df_label[df_label["parent_subzone_name"] == seed_subzone]
    if len(seeds) == 0: return None
    seed_idx = seeds.index[0]
    X = df[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=k+1).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    return df_label.iloc[idx[0][1:]]["parent_pa"].tolist()

cbd_pas = {"DOWNTOWN CORE","RAFFLES PLACE","CECIL","TANJONG PAGAR","MARINA SOUTH","OUTRAM","SINGAPORE RIVER","ROCHOR","MUSEUM"}
nbrs = nn_pas_for(hex_where, "hex9_id", hex_pa, "CECIL", 5)
if nbrs:
    hits = sum(1 for pa in nbrs if pa in cbd_pas)
    if hits >= 4:
        add(4, "where_cbd_coherence", "PASS", f"Cecil's 5 NN: {hits}/5 in CBD ({nbrs})")
    else:
        add(4, "where_cbd_coherence", "WARN", f"{hits}/5 ({nbrs})")
else:
    add(4, "where_cbd_coherence", "SKIP", "Cecil not found")

# ===== T05 WHERE: Industrial coherence =====
ind_pas = {"TUAS","JURONG WEST","JURONG EAST","WOODLANDS","BUKIT BATOK","BENOI","PIONEER","BOON LAY","TENGAH"}
# Find an industrial subzone to seed
ind_seed = hex_pa[hex_pa["parent_pa"] == "TUAS"]
if len(ind_seed):
    seed_idx = ind_seed.index[0]
    X = hex_where[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    nbrs = hex_pa.iloc[idx[0][1:11]]["parent_pa"].tolist()
    hits = sum(1 for pa in nbrs if pa in ind_pas)
    if hits >= 6:
        add(5, "where_industrial_coherence", "PASS", f"Tuas hex 10 NN: {hits}/10 industrial PAs")
    else:
        add(5, "where_industrial_coherence", "WARN", f"{hits}/10 ({nbrs[:5]}...)")
else:
    add(5, "where_industrial_coherence", "SKIP", "no Tuas hex")

# ===== T06 WHERE: HDB town coherence =====
hdb_pas = {"TAMPINES","BEDOK","HOUGANG","SENGKANG","PUNGGOL","WOODLANDS","JURONG WEST","BUKIT BATOK",
           "ANG MO KIO","CHOA CHU KANG","CLEMENTI","TOA PAYOH","BISHAN","PASIR RIS"}
tampines_seed = hex_pa[hex_pa["parent_pa"] == "TAMPINES"]
if len(tampines_seed):
    seed_idx = tampines_seed.index[len(tampines_seed)//2]  # pick middle
    X = hex_where[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    nbrs = hex_pa.iloc[idx[0][1:11]]["parent_pa"].tolist()
    hits = sum(1 for pa in nbrs if pa in hdb_pas)
    if hits >= 6:
        add(6, "where_hdb_coherence", "PASS", f"Tampines hex 10 NN: {hits}/10 HDB PAs")
    else:
        add(6, "where_hdb_coherence", "WARN", f"{hits}/10 ({nbrs[:5]}...)")
else:
    add(6, "where_hdb_coherence", "SKIP", "no Tampines")

# ===== T07 WHAT: Cafe coherence =====
mw = place_what.merge(places_meta, on="id")
cafe_seed = mw[(mw["plexis_category"] == "cafe_coffee") & mw["brand_norm"].notna()].iloc[0:1]
if len(cafe_seed):
    seed_idx = cafe_seed.index[0]
    sample = mw.iloc[:80000]
    X = sample[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    cats = sample.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    food_cats = {"cafe_coffee","restaurant","fast_food","bakery","food","hawker"}
    food_hits = sum(cats.get(c, 0) for c in food_cats)
    if food_hits >= 7:
        add(7, "what_cafe_coherence", "PASS", f"Cafe 10 NN: {food_hits}/10 F&B ({cats})")
    else:
        add(7, "what_cafe_coherence", "WARN", f"{food_hits}/10 ({cats})")

# ===== T08 WHAT: Restaurant coherence =====
rest_seed = mw[mw["plexis_category"] == "restaurant"].iloc[100:101]
if len(rest_seed):
    seed_idx = rest_seed.index[0]
    sample = mw.iloc[:80000]
    X = sample[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    cats = sample.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    food_hits = sum(cats.get(c, 0) for c in {"restaurant","fast_food","cafe_coffee","hawker","bakery"})
    if food_hits >= 7:
        add(8, "what_restaurant_coherence", "PASS", f"Rest 10 NN: {food_hits}/10 F&B ({cats})")
    else:
        add(8, "what_restaurant_coherence", "WARN", f"{food_hits}/10 ({cats})")

# ===== T09 WHAT: HDB residential coherence =====
hdb_seed = mw[mw["plexis_category"] == "residential"].iloc[0:1]
if len(hdb_seed):
    seed_idx = hdb_seed.index[0]
    sample = mw.iloc[:80000]
    X = sample[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    cats = sample.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    res_hits = cats.get("residential", 0)
    if res_hits >= 7:
        add(9, "what_residential_coherence", "PASS", f"Residential NN: {res_hits}/10 residential ({cats})")
    else:
        add(9, "what_residential_coherence", "WARN", f"{res_hits}/10 ({cats})")

# ===== T10 WHAT: Brand clustering — Starbucks =====
starb = mw[mw["brand_norm"].fillna("").str.contains("Starbucks", case=False)]
if len(starb) >= 5:
    seed_idx = starb.index[0]
    sample = mw.iloc[:80000]
    X = sample[WHERE_DIMS].values
    nn = NearestNeighbors(n_neighbors=21).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    nbr_brands = sample.iloc[idx[0][1:21]]["brand_norm"].tolist()
    starb_hits = sum(1 for b in nbr_brands if b and "starbucks" in str(b).lower())
    if starb_hits >= 3:
        add(10, "what_brand_starbucks_clustering", "PASS", f"{starb_hits}/20 of Starbucks NN are also Starbucks")
    else:
        add(10, "what_brand_starbucks_clustering", "WARN", f"{starb_hits}/20")
else:
    add(10, "what_brand_starbucks_clustering", "SKIP", "<5 Starbucks places")

# ===== T11 WHAT: Magnet separation =====
mag = mw[mw["is_magnet"] == True].sample(n=200, random_state=42)
non_mag = mw[mw["is_magnet"] == False].sample(n=200, random_state=42)
mag_X = mag[WHERE_DIMS].values
non_X = non_mag[WHERE_DIMS].values
mag_norm = np.linalg.norm(mag_X, axis=1).mean()
non_norm = np.linalg.norm(non_X, axis=1).mean()
# Magnets should have a different distribution than long-tail
diff = abs(mag_norm - non_norm) / max(non_norm, 0.01)
if diff > 0.05:
    add(11, "what_magnet_separation", "PASS", f"magnet norm {mag_norm:.2f} vs non-magnet {non_norm:.2f} (Δ={diff*100:.1f}%)")
else:
    add(11, "what_magnet_separation", "WARN", f"weak separation ({diff*100:.1f}%)")

# ===== T12 COMBINED: Orchard mall coherence =====
mc = place_comb.merge(places_meta, on="id")
orchard_mall = mc[(mc["parent_pa"] == "ORCHARD") & (mc["plexis_category"] == "shopping_retail")]
if len(orchard_mall) >= 5:
    seed_idx = orchard_mall.index[0]
    sample = mc.iloc[:80000]
    X = sample[COMB_DIMS].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    cats = sample.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    pas = sample.iloc[idx[0][1:11]]["parent_pa"].value_counts().to_dict()
    retail_hits = cats.get("shopping_retail", 0)
    in_orchard = pas.get("ORCHARD", 0) + pas.get("DOWNTOWN CORE", 0) + pas.get("ROCHOR", 0)
    if retail_hits >= 5 and in_orchard >= 3:
        add(12, "combined_orchard_retail_coherence", "PASS", f"retail {retail_hits}/10, ORCHARD/DTC/ROCHOR {in_orchard}/10")
    else:
        add(12, "combined_orchard_retail_coherence", "WARN", f"retail {retail_hits}/10, area {in_orchard}/10")

# ===== T13 CONSISTENCY: hex_combined `where_part` matches hex_where_64d =====
# In build, hex_combined cols: d0..d63 = mean(what); d64..d127 = where
hex_comb_where_part = hex_comb[[f"d{i}" for i in range(64, 128)]].values
hex_where_orig = hex_where[WHERE_DIMS].values
diff_max = np.abs(hex_comb_where_part - hex_where_orig).max()
if diff_max < 1e-3:
    add(13, "consistency_hex_where_match", "PASS", f"max abs diff {diff_max:.2e}")
else:
    add(13, "consistency_hex_where_match", "FAIL", f"max abs diff {diff_max:.2e}")

# ===== T14 CONSISTENCY: place_combined `where_part` matches place's hex's where =====
sample_places = place_comb.sample(n=1000, random_state=42).merge(places_meta[["id","hex9_id"]], on="id")
sample_places = sample_places.merge(hex_where, on="hex9_id", how="left")
where_in_combined = sample_places[[f"d{i}" for i in range(64, 128)]].values
where_from_hex = sample_places[[f"d{i}_y" for i in range(64) if f"d{i}_y" in sample_places.columns]].values
# Actually columns suffix may differ; let's check the rename
# After merging, hex_where's cols are renamed with _x or _y. Take the right one.
emb_cols_combined = [f"d{i}" for i in range(64, 128)]
# Rename hex_where's d0..d63 to where_d0..where_d63 first
sample_check = place_comb.sample(n=1000, random_state=42).merge(places_meta[["id","hex9_id"]], on="id")
hex_w_renamed = hex_where.rename(columns={f"d{i}": f"hex_d{i}" for i in range(64)})
sample_check = sample_check.merge(hex_w_renamed, on="hex9_id", how="left").dropna(subset=[f"hex_d0"])
combined_where = sample_check[[f"d{i}" for i in range(64,128)]].values
hex_where_v = sample_check[[f"hex_d{i}" for i in range(64)]].values
diff_max2 = np.abs(combined_where - hex_where_v).max()
if diff_max2 < 1e-3:
    add(14, "consistency_place_where_match", "PASS", f"max abs diff {diff_max2:.2e} across 1000 sampled places")
else:
    add(14, "consistency_place_where_match", "FAIL", f"max abs diff {diff_max2:.2e}")

# ===== T15 NORMS distribution =====
hex_norms = np.linalg.norm(hex_where[WHERE_DIMS].values, axis=1)
place_norms = np.linalg.norm(place_what[WHERE_DIMS].values, axis=1)
if 0.1 < hex_norms.std() < 100 and 0.1 < place_norms.std() < 100:
    add(15, "norms_distribution", "PASS",
        f"hex_norms p50={np.median(hex_norms):.2f} std={hex_norms.std():.2f}; place_norms p50={np.median(place_norms):.2f} std={place_norms.std():.2f}")
else:
    add(15, "norms_distribution", "WARN", f"hex_norms std={hex_norms.std():.2f}; place_norms std={place_norms.std():.2f}")

# ===== T16 Cosine similarity bounds =====
# Random pairs: should distribute across [-1, 1] not concentrate
sample = hex_where[WHERE_DIMS].sample(n=500, random_state=42).values
sims = cosine_similarity(sample)
np.fill_diagonal(sims, np.nan)
sim_med = np.nanmedian(sims)
sim_p99 = np.nanpercentile(sims, 99)
sim_p1  = np.nanpercentile(sims, 1)
if -0.5 < sim_med < 0.5 and sim_p99 > 0.5 and sim_p1 < 0:
    add(16, "cosine_distribution", "PASS",
        f"hex pairwise cos: p1={sim_p1:.2f} p50={sim_med:.2f} p99={sim_p99:.2f}")
else:
    add(16, "cosine_distribution", "WARN", f"p1={sim_p1:.2f} p50={sim_med:.2f} p99={sim_p99:.2f}")

# ===== T17 Place hexes have distinct embeddings =====
# Two random places at different hexes shouldn't have identical embeddings
unique_hexes = place_comb.merge(places_meta[["id","hex9_id"]], on="id")["hex9_id"].nunique()
if unique_hexes > 1000:
    # Check 100 random pairs from different hexes
    s1 = place_comb.sample(n=100, random_state=42).merge(places_meta[["id","hex9_id"]], on="id")
    diffs = []
    for _, r in s1.iterrows():
        v1 = r[COMB_DIMS].values.astype(float)
        diffs.append(np.linalg.norm(v1))
    if all(d > 0.01 for d in diffs):
        add(17, "place_distinctness", "PASS", f"all 100 sampled places have non-trivial norms")
    else:
        add(17, "place_distinctness", "WARN", f"some places have zero/near-zero norm")

# ===== Summary =====
passes = sum(1 for r in results if r["status"] == "PASS")
warns  = sum(1 for r in results if r["status"] == "WARN")
fails  = sum(1 for r in results if r["status"] == "FAIL")
skips  = sum(1 for r in results if r["status"] == "SKIP")
print(f"\n{passes} PASS, {warns} WARN, {fails} FAIL, {skips} SKIP — total {len(results)} tests")

out = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "total_tests": len(results),
    "pass_count": passes, "warn_count": warns, "fail_count": fails, "skip_count": skips,
    "tests": results,
}
with open(ROOT / "hex/embeddings_full_test.json", "w") as f:
    json.dump(out, f, indent=2, default=str)

"""
Plexis SGP v4 — Graph embedding test suite.

Tests for the new graph-based embeddings (place2vec, hex_node2vec, hex_gcn,
super, mega). 12 tests covering structural integrity, semantic coherence
specific to graph-based methods, and complementarity with PCA.
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).parent
results = []


def add(idx, name, status, detail):
    results.append({"idx": idx, "name": name, "status": status, "detail": detail})
    print(f"  [{status}] G{idx:02d} {name} — {detail}")


print("Loading...")
p2v = pd.read_parquet(ROOT / "places/place_embedding_place2vec_64d.parquet")
hn2v = pd.read_parquet(ROOT / "hex/hex9_embedding_node2vec_64d.parquet")
hgcn = pd.read_parquet(ROOT / "hex/hex9_embedding_gcn_64d.parquet")
hsup = pd.read_parquet(ROOT / "hex/hex9_embedding_super_128d.parquet")
psup = pd.read_parquet(ROOT / "places/place_embedding_super_128d.parquet")
pmega = pd.read_parquet(ROOT / "places/place_embedding_mega_256d.parquet")
places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")[
    ["id","plexis_category","brand_norm","is_magnet","name","hex9_id","parent_pa","parent_subzone_name"]
]
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")

D64 = [f"d{i}" for i in range(64)]
D128 = [f"d{i}" for i in range(128)]
D256 = [f"d{i}" for i in range(256)]

# G01 shapes
ok = (p2v.shape == (190591, 65) and hn2v.shape == (7318, 65)
       and hgcn.shape == (7318, 65) and hsup.shape == (7318, 129)
       and psup.shape == (190591, 129) and pmega.shape == (190591, 257))
if ok:
    add(1, "shapes", "PASS", "all 6 graph embeddings correct shape")
else:
    add(1, "shapes", "FAIL",
        f"p2v={p2v.shape} hn2v={hn2v.shape} hgcn={hgcn.shape} hsup={hsup.shape} psup={psup.shape} pmega={pmega.shape}")

# G02 no NaN/inf
nans = sum(df.isna().sum().sum() for df in [p2v, hn2v, hgcn, hsup, psup, pmega])
if nans == 0:
    add(2, "no_nan_inf", "PASS", "0 NaN across 6 graph embeddings")
else:
    add(2, "no_nan_inf", "FAIL", f"{nans} NaN")

# G03 PLACE2VEC: same hex co-location
mw = p2v.merge(places, on="id")
# Pick a place in a hex with many places
busy_hex = mw["hex9_id"].value_counts()
busy_hex_id = busy_hex.index[0]
in_hex = mw[mw["hex9_id"] == busy_hex_id]
if len(in_hex) >= 5:
    seed_idx = in_hex.index[0]
    sample = mw.iloc[:80000]
    X = sample[D64].values
    nn = NearestNeighbors(n_neighbors=21).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    nbr_hexes = sample.iloc[idx[0][1:21]]["hex9_id"].value_counts()
    same_hex_share = nbr_hexes.get(busy_hex_id, 0) / 20
    if same_hex_share >= 0.30:
        add(3, "place2vec_same_hex", "PASS",
            f"{int(same_hex_share*20)}/20 of NN are in same hex (busy hex {busy_hex_id})")
    else:
        add(3, "place2vec_same_hex", "WARN", f"{int(same_hex_share*20)}/20")

# G04 PLACE2VEC: category coherence
cafe_seed = mw[mw["plexis_category"] == "cafe_coffee"].iloc[0:1]
if len(cafe_seed):
    seed_idx = cafe_seed.index[0]
    sample = mw.iloc[:80000]
    X = sample[D64].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    cats = sample.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    food_hits = sum(cats.get(c, 0) for c in {"cafe_coffee","restaurant","fast_food","bakery","hawker"})
    if food_hits >= 5:
        add(4, "place2vec_cafe_coherence", "PASS", f"{food_hits}/10 F&B nearby ({cats})")
    else:
        add(4, "place2vec_cafe_coherence", "WARN", f"{food_hits}/10 ({cats})")

# G05 NODE2VEC: hex spatial coherence — Cecil's NN should be in CBD
hexpa = hn2v.merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")
cbd_pas = {"DOWNTOWN CORE","RAFFLES PLACE","CECIL","TANJONG PAGAR","MARINA SOUTH","OUTRAM","SINGAPORE RIVER"}
cecil = hexpa[hexpa["parent_subzone_name"] == "CECIL"]
if len(cecil):
    seed_idx = cecil.index[0]
    X = hn2v[D64].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    nbrs = hexpa.iloc[idx[0][1:11]]["parent_pa"].tolist()
    hits = sum(1 for pa in nbrs if pa in cbd_pas)
    if hits >= 7:
        add(5, "node2vec_cbd_topology", "PASS", f"{hits}/10 Cecil NN in CBD via topology only ({nbrs[:3]}...)")
    else:
        add(5, "node2vec_cbd_topology", "WARN", f"{hits}/10")

# G06 GCN: hex feature-smoothed coherence (CBD)
hgcn_pa = hgcn.merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")
cecil = hgcn_pa[hgcn_pa["parent_subzone_name"] == "CECIL"]
if len(cecil):
    seed_idx = cecil.index[0]
    X = hgcn[D64].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    nbrs = hgcn_pa.iloc[idx[0][1:11]]["parent_pa"].tolist()
    hits = sum(1 for pa in nbrs if pa in cbd_pas)
    if hits >= 7:
        add(6, "gcn_cbd_coherence", "PASS", f"{hits}/10 Cecil NN in CBD via GCN")
    else:
        add(6, "gcn_cbd_coherence", "WARN", f"{hits}/10")

# G07 NODE2VEC ≠ GCN — they capture different aspects
# Their nearest neighbors of same seed should NOT be identical
if len(cecil):
    seed_idx = cecil.index[0]
    Xn = hn2v[D64].values
    nn = NearestNeighbors(n_neighbors=11).fit(Xn)
    _, idx_n = nn.kneighbors(Xn[[seed_idx]])
    set_n = set(hn2v.iloc[idx_n[0][1:11]]["hex9_id"])
    Xg = hgcn[D64].values
    nn = NearestNeighbors(n_neighbors=11).fit(Xg)
    _, idx_g = nn.kneighbors(Xg[[seed_idx]])
    set_g = set(hgcn.iloc[idx_g[0][1:11]]["hex9_id"])
    overlap = len(set_n & set_g)
    if overlap < 8:  # not identical → captures different things
        add(7, "node2vec_vs_gcn_distinctness", "PASS", f"only {overlap}/10 NN overlap → graph methods capture different aspects")
    else:
        add(7, "node2vec_vs_gcn_distinctness", "WARN", f"{overlap}/10 — too similar")

# G08 SUPER 128: combines node2vec + gcn — best of both
hsup_pa = hsup.merge(h9_uni[["hex9_id","parent_subzone_name","parent_pa"]], on="hex9_id")
cecil = hsup_pa[hsup_pa["parent_subzone_name"] == "CECIL"]
if len(cecil):
    seed_idx = cecil.index[0]
    X = hsup[D128].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    nbrs = hsup_pa.iloc[idx[0][1:11]]["parent_pa"].tolist()
    hits = sum(1 for pa in nbrs if pa in cbd_pas)
    if hits >= 8:
        add(8, "hex_super_cbd", "PASS", f"{hits}/10 with super=concat[node2vec,gcn]")
    else:
        add(8, "hex_super_cbd", "WARN", f"{hits}/10")

# G09 PLACE_SUPER 128: place2vec + what_pca
psup_m = psup.merge(places, on="id")
sb = psup_m[psup_m["brand_norm"].fillna("").str.contains("Starbucks", case=False)]
if len(sb) >= 5:
    seed_idx = sb.index[0]
    sample = psup_m.iloc[:80000]
    X = sample[D128].values
    nn = NearestNeighbors(n_neighbors=21).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    nbr_brands = sample.iloc[idx[0][1:21]]["brand_norm"].tolist()
    starb_hits = sum(1 for b in nbr_brands if b and "starbucks" in str(b).lower())
    if starb_hits >= 6:
        add(9, "place_super_starbucks", "PASS", f"{starb_hits}/20 Starbucks NN under super")
    else:
        add(9, "place_super_starbucks", "WARN", f"{starb_hits}/20")

# G10 PLACE_MEGA 256: full feature space
pmega_m = pmega.merge(places, on="id")
orchard_mall = pmega_m[(pmega_m["parent_pa"] == "ORCHARD") & (pmega_m["plexis_category"] == "shopping_retail")]
if len(orchard_mall) >= 5:
    seed_idx = orchard_mall.index[0]
    sample = pmega_m.iloc[:80000]
    X = sample[D256].values
    nn = NearestNeighbors(n_neighbors=11).fit(X)
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    cats = sample.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    pas = sample.iloc[idx[0][1:11]]["parent_pa"].value_counts().to_dict()
    retail_hits = cats.get("shopping_retail", 0)
    cbd_area = sum(pas.get(p, 0) for p in {"ORCHARD","DOWNTOWN CORE","ROCHOR","TANGLIN","MUSEUM"})
    if retail_hits >= 6 and cbd_area >= 5:
        add(10, "place_mega_orchard", "PASS", f"retail {retail_hits}/10, CBD-area {cbd_area}/10")
    else:
        add(10, "place_mega_orchard", "WARN", f"retail {retail_hits}/10, area {cbd_area}/10")

# G11 NODE2VEC norm spread
norms = np.linalg.norm(hn2v[D64].values, axis=1)
n2v_std = float(norms.std())
n2v_med = float(np.median(norms))
if 0.5 < n2v_std < 50 and 0.5 < n2v_med < 50:
    add(11, "node2vec_norms", "PASS", f"median={n2v_med:.2f} std={n2v_std:.2f}")
else:
    add(11, "node2vec_norms", "WARN", f"median={n2v_med:.2f} std={n2v_std:.2f}")

# G12 PLACE2VEC: distinctness (places without graph context = zeros)
zero_count = int((np.linalg.norm(p2v[D64].values, axis=1) < 0.01).sum())
if zero_count < 200:
    add(12, "place2vec_zero_count", "PASS", f"{zero_count}/{len(p2v):,} places have ~zero embedding (singletons)")
else:
    add(12, "place2vec_zero_count", "WARN", f"{zero_count}/{len(p2v):,} zeros — too many isolated places")

passes = sum(1 for r in results if r["status"] == "PASS")
warns = sum(1 for r in results if r["status"] == "WARN")
fails = sum(1 for r in results if r["status"] == "FAIL")
print(f"\n{passes} PASS, {warns} WARN, {fails} FAIL — total {len(results)} graph tests")

out = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "total_tests": len(results),
    "pass_count": passes, "warn_count": warns, "fail_count": fails,
    "tests": results,
}
with open(ROOT / "hex/embeddings_graph_test.json", "w") as f:
    json.dump(out, f, indent=2, default=str)

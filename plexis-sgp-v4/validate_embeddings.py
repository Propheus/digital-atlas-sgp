"""
Plexis SGP v4 — embeddings validator.

E1 shapes correct (7318 × 65 for hex; 190591 × 65/129 for place)
E2 no NaN/inf in any embedding
E3 hex nearest-neighbor sanity: top-5 NN of a CBD hex should be CBD/Marina hexes
E4 place nearest-neighbor sanity: NN of a Starbucks should be other cafes/F&B
E5 variance explained ≥ 0.6 for both 64d embeddings
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).parent
report = {"checks": []}


def add(name, status, detail=""):
    report["checks"].append({"check": name, "status": status, "detail": detail})
    print(f"  [{status}] {name} — {detail}")


print("Loading...")
hex_where = pd.read_parquet(ROOT / "hex/hex9_embedding_where_64d.parquet")
place_what = pd.read_parquet(ROOT / "places/place_embedding_what_64d.parquet")
place_comb = pd.read_parquet(ROOT / "places/place_embedding_combined_128d.parquet")
hex_comb = pd.read_parquet(ROOT / "hex/hex9_embedding_combined_128d.parquet")
report_data = json.load(open(ROOT / "hex/embeddings_report.json"))

# E1 shapes
ok = (hex_where.shape == (7318, 65) and hex_comb.shape == (7318, 129)
       and place_what.shape[1] == 65 and place_comb.shape[1] == 129
       and place_what.shape[0] == 190591)
if ok:
    add("E1_shapes", "PASS", f"hex_where={hex_where.shape} hex_comb={hex_comb.shape} place_what={place_what.shape} place_comb={place_comb.shape}")
else:
    add("E1_shapes", "FAIL", f"hex_where={hex_where.shape} hex_comb={hex_comb.shape} place_what={place_what.shape} place_comb={place_comb.shape}")

# E2 no NaN/inf
nan_count = (hex_where.isna().sum().sum() + place_what.isna().sum().sum()
              + place_comb.isna().sum().sum() + hex_comb.isna().sum().sum())
inf_count = (np.isinf(hex_where.select_dtypes(np.float32).values).sum()
              + np.isinf(place_what.select_dtypes(np.float32).values).sum()
              + np.isinf(place_comb.select_dtypes(np.float32).values).sum()
              + np.isinf(hex_comb.select_dtypes(np.float32).values).sum())
if nan_count == 0 and inf_count == 0:
    add("E2_no_nan_inf", "PASS", "all embeddings clean")
else:
    add("E2_no_nan_inf", "FAIL", f"NaN={nan_count} inf={inf_count}")

# E3 hex NN sanity for a CBD hex (Cecil) → top-5 NN should be CBD/Marina
h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
hex_pa = hex_where.merge(h9_uni[["hex9_id","parent_pa","parent_subzone_name"]], on="hex9_id")
# Find a Cecil hex
cecil = hex_pa[hex_pa["parent_subzone_name"] == "CECIL"]
if len(cecil):
    seed_idx = cecil.index[0]
    X = hex_where.iloc[:, 1:].values
    nn = NearestNeighbors(n_neighbors=6).fit(X)
    _, idx = nn.kneighbors(X[[seed_idx]])
    top5_pas = hex_pa.iloc[idx[0][1:]]["parent_pa"].tolist()
    cbd_pas = {"DOWNTOWN CORE","RAFFLES PLACE","CECIL","TANJONG PAGAR","MARINA SOUTH","OUTRAM","SINGAPORE RIVER"}
    hits = sum(1 for pa in top5_pas if pa in cbd_pas)
    if hits >= 3:
        add("E3_cbd_hex_nn", "PASS", f"NN of Cecil hex: {hits}/5 in CBD ({top5_pas})")
    else:
        add("E3_cbd_hex_nn", "WARN", f"{hits}/5 ({top5_pas})")
else:
    add("E3_cbd_hex_nn", "WARN", "no Cecil hex found")

# E4 place NN sanity: a coffee place's NN should be other cafes/F&B
places_meta = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")[["id","plexis_category","name"]]
mw = place_what.merge(places_meta, on="id")
seed_pl = mw[mw["plexis_category"] == "cafe_coffee"].iloc[0:1]
if len(seed_pl):
    seed_idx = seed_pl.index[0]
    X = mw.iloc[:, 1:65].values  # 64d cols
    nn = NearestNeighbors(n_neighbors=11).fit(X[:50000])  # sample for speed
    _, idx = nn.kneighbors(X[seed_idx:seed_idx+1])
    top10_cats = mw.iloc[idx[0][1:11]]["plexis_category"].value_counts().to_dict()
    food_cats = {"cafe_coffee","restaurant","fast_food","bakery","food","hawker"}
    food_hits = sum(top10_cats.get(c, 0) for c in food_cats)
    if food_hits >= 5:
        add("E4_cafe_place_nn", "PASS", f"NN of cafe: {food_hits}/10 are F&B ({top10_cats})")
    else:
        add("E4_cafe_place_nn", "WARN", f"{food_hits}/10 ({top10_cats})")
else:
    add("E4_cafe_place_nn", "WARN", "no cafe place found")

# E5 variance explained
var_w = report_data["where_explained_variance"]
var_what = report_data["what_explained_variance"]
if var_w >= 0.6 and var_what >= 0.6:
    add("E5_variance_explained", "PASS", f"where={var_w:.2f} what={var_what:.2f}")
else:
    add("E5_variance_explained", "WARN", f"where={var_w:.2f} what={var_what:.2f}")

passes = sum(1 for c in report["checks"] if c["status"] == "PASS")
print(f"\n{passes}/{len(report['checks'])} checks passed")

report["generated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
with open(ROOT / "hex/embeddings_validation.json", "w") as f:
    json.dump(report, f, indent=2)

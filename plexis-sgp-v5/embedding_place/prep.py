"""
Plexis-P1 — feature prep for the per-place embedding (PLACE_EMBEDDING_DESIGN.md).

HARD RULE: no rating / review signals anywhere. Excluded everywhere:
rating, has_rating, reviews_count, has_reviews, review_bucket,
review_quality_pctl_in_cat, magnet_strength, is_magnet, is_long_tail,
pmg_competitor_rating_avg.

Outputs (embedding_place/):
  X_A.npy          essence + micrograph  (tower A inputs — THE place)
  X_B.npy          context: frozen hex8 plexis-e1 PCA-64 + 400 m category mix
  ids.parquet      id, hex8_id, plexis_category, brand_norm, lat, lng, chain flags
  chain_pairs.npz  train pair pool (row indices) + holdout outlet indices
  archetypes.json  4 hand-picked anchors chosen BEFORE training
  meta.json        column lists, denylist, counts
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.decomposition import PCA

ROOT = Path(__file__).parent.parent
OUT = Path(__file__).parent
SEED = 42

FORBIDDEN = ["rating", "has_rating", "reviews_count", "has_reviews",
             "review_bucket", "review_quality_pctl_in_cat", "magnet_strength",
             "is_magnet", "is_long_tail", "pmg_competitor_rating_avg"]

# unmanned / utility / pseudo-chain brands — never chain-sibling positives
DENY_RE = re.compile(
    r"charging|charge\+|locker|vending|ijooz|axs|popstation|parking|recharge"
    r"|bluesg|atm\b", re.I)
DENY_EXACT = {"DBS", "POSB", "UOB", "OCBC", "Citibank", "HSBC",
              "Standard Chartered", "Maybank", "DHL Express Service Point",
              "Marina Bay Sands", "SAM Machine", "Pick Locker",
              "SPX Express Locker", "LHN Parking", "SP Mobility Charging"}


def main():
    rng = np.random.default_rng(SEED)
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
    pm = pd.read_parquet(ROOT / "places/sgp_places_micrograph.parquet")
    df = pl.merge(pm, on="id", how="left").reset_index(drop=True)
    n = len(df)
    print(f"places: {n}")
    assert not any(c in FORBIDDEN for c in []), "sanity"

    # ---------------- ESSENCE ----------------
    cat_oh = pd.get_dummies(df["plexis_category"], prefix="cat").astype(np.float32)
    top_prim = df["primary_category"].value_counts().head(60).index
    prim = df["primary_category"].where(df["primary_category"].isin(top_prim), "other")
    prim_oh = pd.get_dummies(prim, prefix="prim").astype(np.float32)

    brand = df["brand_norm"].fillna("")
    bsize = brand.map(brand.value_counts())
    is_chain = ((brand != "") & (bsize >= 2)).astype(np.float32)
    size_bucket = pd.cut(bsize.fillna(0), bins=[-1, 1, 4, 19, 10**9],
                         labels=["indep", "small", "mid", "big"])
    size_oh = pd.get_dummies(size_bucket, prefix="bsz").astype(np.float32)

    # ---------------- MICROGRAPH ----------------
    pmg_cols = [c for c in pm.columns if c.startswith("pmg_")
                and c not in FORBIDDEN]
    M = df[pmg_cols].astype(float)
    nan_ind = M.isna().astype(np.float32)
    nan_ind.columns = [c + "_nan" for c in pmg_cols]
    Mt = M.copy()
    for c in pmg_cols:
        v = Mt[c]
        if v.min() >= 0 and v.skew() > 2:
            Mt[c] = np.log1p(v)
        mu, sd = Mt[c].mean(), Mt[c].std()
        Mt[c] = ((Mt[c] - mu) / (sd if sd > 0 else 1)).fillna(0)
    # keep only indicator cols that vary
    nan_ind = nan_ind.loc[:, nan_ind.std() > 0]

    X_A = pd.concat([cat_oh, prim_oh, size_oh,
                     pd.DataFrame({"is_chain": is_chain}),
                     Mt.astype(np.float32), nan_ind], axis=1)
    a_cols = list(X_A.columns)
    assert not any(any(f in c for f in ("rating", "review", "magnet"))
                   for c in a_cols), "FORBIDDEN signal leaked into X_A"

    # ---------------- CONTEXT (tower B) ----------------
    E = pd.read_parquet(ROOT / "hex/hex8_embedding_plexis_e1_256d.parquet") \
        .set_index("hex8_id")
    pca = PCA(n_components=64, random_state=SEED)
    E64 = pd.DataFrame(pca.fit_transform(E.to_numpy()), index=E.index,
                       columns=[f"hexe1_{i}" for i in range(64)])
    print(f"hex-e1 PCA-64 var explained: {pca.explained_variance_ratio_.sum():.3f}")
    hexctx = df["hex8_id"].map(E64.to_dict("index"))
    hex_missing = hexctx.isna()
    Hx = pd.DataFrame(list(hexctx.fillna(
        {i: dict.fromkeys(E64.columns, 0.0) for i in df.index[hex_missing]})),
        index=df.index).astype(np.float32)
    Hx = (Hx - Hx.mean()) / Hx.std().replace(0, 1)

    # 400 m neighbour category mix (equirectangular metres)
    lat0 = np.deg2rad(df["latitude"].mean())
    xy = np.c_[df["longitude"].to_numpy() * 111320 * np.cos(lat0),
               df["latitude"].to_numpy() * 110540]
    tree = cKDTree(xy)
    cats = df["plexis_category"].astype("category")
    cat_codes = cats.cat.codes.to_numpy()
    k = len(cats.cat.categories)
    mix = np.zeros((n, k), dtype=np.float32)
    neigh = tree.query_ball_point(xy, r=400, workers=-1)
    for i, idxs in enumerate(neigh):
        np.add.at(mix[i], cat_codes[idxs], 1)
        mix[i, cat_codes[i]] -= 1            # exclude self
    mix = np.log1p(mix)
    mix = (mix - mix.mean(0)) / np.where(mix.std(0) > 0, mix.std(0), 1)

    X_B = np.concatenate([Hx.to_numpy(np.float32),
                          mix.astype(np.float32),
                          hex_missing.to_numpy(np.float32)[:, None]], axis=1)
    b_cols = list(Hx.columns) + [f"mix_{c}" for c in cats.cat.categories] + ["hex_missing"]

    # ---------------- chain pairs + holdout ----------------
    deny = brand.str.contains(DENY_RE) | brand.isin(DENY_EXACT)
    eligible = (brand != "") & (~deny) & (bsize >= 5)
    print(f"chain-eligible outlets: {int(eligible.sum())} "
          f"({brand[eligible].nunique()} brands; denied {int((deny & (brand != '')).sum())} outlets)")

    holdout_idx, pair_rows = [], []
    for b, g in df[eligible].groupby(brand[eligible]):
        idx = g.index.to_numpy()
        rng.shuffle(idx)
        if len(idx) >= 10:                    # exam chains: hide 20%
            n_hold = max(2, int(0.2 * len(idx)))
            holdout_idx.extend(idx[:n_hold])
            idx = idx[n_hold:]
        # training pair pool (capped at sample time, not here)
        if len(idx) >= 2:
            for _ in range(min(200, 3 * len(idx))):
                i, j = rng.choice(idx, 2, replace=False)
                pair_rows.append((i, j))
    pairs = np.array(pair_rows, dtype=np.int64)
    holdout = np.array(sorted(set(holdout_idx)), dtype=np.int64)
    print(f"chain train pairs: {len(pairs)} | exam holdout outlets: {len(holdout)}")

    # ---------------- archetypes (picked BEFORE training) ----------------
    def pick(mask, label):
        cand = df[mask].sort_values("id")
        if not len(cand):
            print(f"  archetype MISS: {label}")
            return None
        r = cand.iloc[0]
        print(f"  archetype {label}: {r['name']} ({r['parent_subzone_name']})")
        return {"label": label, "id": r["id"], "row": int(r.name),
                "name": r["name"], "subzone": r["parent_subzone_name"]}

    arch = [a for a in [
        pick(brand.eq("Ya Kun Kaya Toast"), "yakun_kopi_chain"),
        pick(df["plexis_category"].eq("health_medical")
             & df["name"].str.contains("clinic", case=False, na=False)
             & df["parent_pa"].isin(["TOA PAYOH", "ANG MO KIO", "BEDOK"]),
             "heartland_clinic"),
        pick(df["plexis_category"].eq("bar_nightlife")
             & df["parent_subzone_name"].str.contains("DUXTON|TANJONG PAGAR|CHINATOWN",
                                                      na=False), "shophouse_bar"),
        pick(df["plexis_category"].isin(["hawker", "restaurant"])
             & df["name"].str.contains("canteen", case=False, na=False)
             & df["parent_pa"].isin(["TUAS", "JURONG WEST", "PIONEER"]),
             "industrial_canteen"),
    ] if a]

    # ---------------- save ----------------
    np.save(OUT / "X_A.npy", X_A.to_numpy(np.float32))
    np.save(OUT / "X_B.npy", X_B)
    df[["id", "hex8_id", "plexis_category", "brand_norm", "latitude",
        "longitude", "parent_subzone_name", "rating"]].to_parquet(OUT / "ids.parquet")
    # NOTE: 'rating' rides along in ids.parquet ONLY for exam check 7
    # (the forbidden-probe audit) — it never enters X_A / X_B / training.
    np.savez(OUT / "chain_pairs.npz", pairs=pairs, holdout=holdout)
    json.dump(arch, open(OUT / "archetypes.json", "w"), indent=1)
    json.dump({"n": n, "dA": len(a_cols), "dB": len(b_cols),
               "a_cols": a_cols, "b_cols": b_cols,
               "forbidden": FORBIDDEN,
               "deny_exact": sorted(DENY_EXACT), "deny_regex": DENY_RE.pattern,
               "n_chain_pairs": int(len(pairs)), "n_holdout": int(len(holdout))},
              open(OUT / "meta.json", "w"), indent=1)
    print(f"X_A {X_A.shape} | X_B {X_B.shape} — prep done")


if __name__ == "__main__":
    main()

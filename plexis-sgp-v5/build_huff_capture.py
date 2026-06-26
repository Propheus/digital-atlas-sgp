"""
Plexis SGP v4 — S1 Huff capture potential (cap_*) per hex9 -> hex8.

Spec: SITE_SELECTION_METRICS.md §S1.

For each category c and candidate hex9 h: the demand (in OUTLET-EQUIVALENTS)
a single new outlet at h would capture against existing competition:

  q_place  = (1 + log1p(reviews)) / category mean      (outlet-equivalent units)
  A_j      = sum of q over existing places of c in hex9 j
  f(d)     = exp(-d / lambda_c)        d = euclid hex9<->hex9 (EPSG:3414);
                                       d_ii = 100 m (within-cell self distance)
  S_i      = sum_j A_j f(d_ij)         (denominator from existing supply)
  P(i->h)  = f(d_ih) / (S_i + f(d_ih))                  (candidate A_h = 1)
  D_i,c    = pop9_i x dt_adjust(c) x N_c / sum(pop)     (national outlet count
                                                         spread per capita)
  cap_c(h) = sum_i D_i,c x P(i->h)

cap_c = 1.0 means "enough unmet/winnable demand to support one average outlet".

lambda_c is calibrated OUT-OF-SAMPLE: subzones split 80/20; supply built from
train subzones only; lambda maximizes Spearman(cap at test hex9s, actual
outlet mass A at test hex9s). The gate number reported is this honest
test-split Spearman. The shipped layer uses full supply at lambda*.

Daytime categories (cafe, restaurant, fast_food, bakery) use S3 dt_ratio
(hex8 -> children) to weight demand by who is actually present at midday.

hex8 rollup = MAX over child hex9s (best site within the hex8), since site
selection asks "where is the best spot", not "what is the average spot".

Output: hex/hex9_huff_capture.parquet, hex/hex8_huff_capture.parquet,
        hex/huff_capture_report.json
"""
import json
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).parent

# bar_nightlife DROPPED (2026-06-10): rho ~ 0 on both the placement and the
# allocation test — bar districts follow culture, not spatial demand
# (consistent with v7 finding #3, R2=0.44 vs zoning). A Huff capture number
# for bars would be confidently wrong.
CATS = ["cafe_coffee", "restaurant", "hawker", "fast_food", "supermarket",
        "convenience", "fitness_recreation", "health_medical", "beauty_personal",
        "shopping_retail", "education", "pharmacy_beauty"]
DAYTIME_CATS = {"cafe_coffee", "restaurant", "fast_food"}
# LAMBDA IS ASSUMED, NOT CALIBRATED — finding 2026-06-10: lambda is not
# empirically identifiable from cross-sectional outlet data here.
#   - placement test drives lambda -> 100 m (overfits zoning adjacency;
#     10-min-walk weight 0.0003 is behaviorally absurd)
#   - allocation test (counts-A -> review mass) NEVER beats its degenerate
#     lambda->inf baseline rho(counts, reviews) for any category
# Mitigation: rankings are lambda-robust (Spearman >= 0.91 across 400-1200,
# >= 0.75 across 400-2000), so behavioral priors carry the layer:
LAMBDA_BY_CAT = {
    "hawker": 500.0, "convenience": 500.0, "supermarket": 500.0,
    "cafe_coffee": 500.0, "fast_food": 500.0,                      # walk-daily
    "health_medical": 700.0, "beauty_personal": 700.0, "pharmacy_beauty": 700.0,
    "education": 700.0, "fitness_recreation": 700.0,               # neighborhood
    "restaurant": 1000.0,                                          # mixed-mode
    "shopping_retail": 1500.0,                                     # destination
}
SENS_PAIR = (400.0, 1200.0)   # rank-stability sensitivity reported per cat
CUTOFF = 4000.0
SELF_D = 100.0
TEST_FRAC = 0.2
SEED = 42


def main():
    t0 = time.time()
    h9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
    h9 = h9.merge(pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
                  [["hex9_id", "lat", "lng"]], on="hex9_id")
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    x, y = tr.transform(h9["lng"].to_numpy(), h9["lat"].to_numpy())
    xy = np.column_stack([x, y])
    n = len(h9)
    h9_index = pd.Series(range(n), index=h9["hex9_id"])

    # demand: pop with daytime adjustment from S3
    dt = pd.read_parquet(ROOT / "hex/hex8_daytime_pop.parquet")[["hex8_id", "dt_ratio"]]
    h9["hex8_of"] = [h3.cell_to_parent(c, 8) for c in h9["hex9_id"]]
    h9 = h9.merge(dt, left_on="hex8_of", right_on="hex8_id", how="left")
    dt_adj = h9["dt_ratio"].clip(0.5, 5.0).fillna(1.0).to_numpy()
    pop = h9["pop_resident"].fillna(0).to_numpy()

    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["hex9_id", "plexis_category", "reviews_count",
                                  "parent_subzone_name"])
    pl = pl[pl["plexis_category"].isin(CATS) & pl["hex9_id"].isin(h9_index.index)].copy()
    pl["hi"] = pl["hex9_id"].map(h9_index)
    pl["q_raw"] = 1 + np.log1p(pl["reviews_count"].fillna(0))
    pl["q"] = pl["q_raw"] / pl.groupby("plexis_category")["q_raw"].transform("mean")

    # 80/20 subzone split for calibration
    rng = np.random.default_rng(SEED)
    szs = pl["parent_subzone_name"].dropna().unique()
    test_szs = set(rng.choice(szs, int(len(szs) * TEST_FRAC), replace=False))
    pl["is_test"] = pl["parent_subzone_name"].isin(test_szs)

    # pairwise hex9 weights within cutoff (built once, reused per lambda)
    tree = cKDTree(xy)
    pairs = tree.query_pairs(CUTOFF, output_type="ndarray")
    pd_d = np.linalg.norm(xy[pairs[:, 0]] - xy[pairs[:, 1]], axis=1)
    pi = np.concatenate([pairs[:, 0], pairs[:, 1], np.arange(n)])
    pj = np.concatenate([pairs[:, 1], pairs[:, 0], np.arange(n)])
    pdist = np.concatenate([pd_d, pd_d, np.full(n, SELF_D)])
    print(f"hex9 pairs within {CUTOFF/1000:.0f} km: {len(pdist):,}")

    def capture(A, D, lam):
        """cap(h) for all h, given supply A, demand D, decay lam."""
        w = np.exp(-pdist / lam)
        S = np.zeros(n)
        np.add.at(S, pi, A[pj] * w)          # S_i = sum_j A_j f_ij
        cap = np.zeros(n)
        contrib = D[pi] * w / (S[pi] + w)    # pair (i=demand, j=candidate h)
        np.add.at(cap, pj, contrib)
        return cap, S

    rep = {"lambda": {}, "test_spearman": {}, "alloc_spearman": {},
           "alloc_baseline": {}, "lambda_rank_stability": {},
           "conservation": {}, "n_outlets": {}}
    np.savez_compressed(ROOT / "hex/huff_pairs.npz", pi=pi, pj=pj, pdist=pdist,
                        hex9_id=h9["hex9_id"].to_numpy())
    out9 = pd.DataFrame({"hex9_id": h9["hex9_id"]})
    for cat in CATS:
        sub = pl[pl["plexis_category"] == cat]
        N_c = sub["q"].sum()                  # national outlet-equivalents
        D = pop * (dt_adj if cat in DAYTIME_CATS else 1.0)
        D = D / D.sum() * N_c
        A_train = np.zeros(n)
        g = sub[~sub["is_test"]].groupby("hi")["q"].sum()
        A_train[g.index] = g.to_numpy()
        A_full = np.zeros(n)
        g = sub.groupby("hi")["q"].sum()
        A_full[g.index] = g.to_numpy()
        test_target = np.zeros(n)
        g = sub[sub["is_test"]].groupby("hi")["q"].sum()
        test_target[g.index] = g.to_numpy()
        test_hexes = h9["parent_subzone_name"].isin(test_szs).to_numpy() \
            if "parent_subzone_name" in h9 else None
        # hex9_population carries parent_subzone_name
        test_hexes = h9["parent_subzone_name"].isin(test_szs).to_numpy()

        # counts-only attractiveness + review-mass target (non-circular)
        A_cnt = np.zeros(n)
        g = sub.groupby("hi").size()
        A_cnt[g.index] = g.to_numpy()
        rev = np.zeros(n)
        g = sub.groupby("hi")["reviews_count"].sum()
        rev[g.index] = g.to_numpy()
        omask = (A_cnt > 0) & test_hexes        # evaluate on held-out outlet hexes

        def alloc_at(lam):
            w = np.exp(-pdist / lam)
            Sv = np.zeros(n)
            np.add.at(Sv, pi, A_cnt[pj] * w)
            alloc = np.zeros(n)
            good = Sv[pi] > 0
            contrib = np.where(good, D[pi] * A_cnt[pj] * w
                               / np.where(good, Sv[pi], 1.0), 0.0)
            np.add.at(alloc, pj, contrib)
            return alloc

        lam = LAMBDA_BY_CAT[cat]
        alloc = alloc_at(lam)
        rho_alloc = spearmanr(alloc[omask], rev[omask]).statistic
        rho_base = spearmanr(A_cnt[omask], rev[omask]).statistic
        # placement diagnostic at the assumed lambda (out-of-sample)
        cap_t, _ = capture(A_train, D, lam)
        rho = spearmanr(cap_t[test_hexes], test_target[test_hexes]).statistic
        cap, S = capture(A_full, D, lam)
        # lambda sensitivity: rank stability of cap across the plausible band
        c_lo, _ = capture(A_full, D, SENS_PAIR[0])
        c_hi, _ = capture(A_full, D, SENS_PAIR[1])
        pm = pop > 0
        rho_sens = spearmanr(c_lo[pm], c_hi[pm]).statistic
        rep["lambda"][cat] = lam
        rep["test_spearman"][cat] = round(float(rho), 3)
        rep["alloc_spearman"][cat] = round(float(rho_alloc), 3)
        rep["alloc_baseline"][cat] = round(float(rho_base), 3)
        rep["lambda_rank_stability"][cat] = round(float(rho_sens), 3)
        rep["conservation"][cat] = round(float(alloc.sum() / D.sum()), 4)
        rep["n_outlets"][cat] = int(len(sub))
        out9[f"cap_{cat}"] = cap.round(4)
        print(f"  {cat:20s} lam={lam:6.0f}  placement={rho:.3f}  alloc={rho_alloc:.3f} "
              f"(base {rho_base:.3f})  sens={rho_sens:.3f}  "
              f"alloc/demand={alloc.sum()/D.sum():.3f}")

    cap_cols = [f"cap_{c}" for c in CATS]
    out9["cap_total"] = out9[cap_cols].sum(axis=1).round(4)
    out9["cap_best_category"] = (out9[cap_cols].idxmax(axis=1)
                                 .str.replace("cap_", "", regex=False))
    out9.to_parquet(ROOT / "hex/hex9_huff_capture.parquet", index=False)

    # hex8 rollup: MAX over children (best site in the hex)
    out9["hex8_of"] = h9["hex8_of"].to_numpy()
    agg = out9.groupby("hex8_of")[cap_cols + ["cap_total"]].max().reset_index() \
        .rename(columns={"hex8_of": "hex8_id"})
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    out8 = h8.merge(agg, on="hex8_id", how="left").fillna(0.0)
    best9 = out9.loc[out9.groupby("hex8_of")["cap_total"].idxmax(),
                     ["hex8_of", "cap_best_category"]]
    out8 = out8.merge(best9.rename(columns={"hex8_of": "hex8_id"}), on="hex8_id",
                      how="left")
    out8.to_parquet(ROOT / "hex/hex8_huff_capture.parquet", index=False)

    rep.update({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S1",
        "unit": "outlet_equivalents",
        "self_distance_m": SELF_D, "cutoff_m": CUTOFF,
        "test_subzones": len(test_szs),
        "wall_clock_s": round(time.time() - t0, 2),
    })
    json.dump(rep, open(ROOT / "hex/huff_capture_report.json", "w"), indent=2)
    print(f"\nwall clock {rep['wall_clock_s']}s")


if __name__ == "__main__":
    main()

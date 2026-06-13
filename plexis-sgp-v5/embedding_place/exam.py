"""
Plexis-P1 — the LOCKED 9-check exam (PLACE_EMBEDDING_DESIGN.md).
Thresholds are fixed by the design doc; the exam, not the loss, decides.

Usage: python3 exam.py Z_seed0.npy [Z_seed1.npy Z_seed2.npy] [--subset subset_idx.npy]
Writes exam_<stem>.json next to the first Z.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

OUT = Path(__file__).parent

THRESH = {  # locked
    "chain_retrieval": 0.70, "cat_knn": 0.80, "beyond_cat_ratio": 0.70,
    "geo_leak_rho": 0.45, "samehex_spread": 0.50,
    "probe_anchors_r2": 0.50, "probe_mrt_r2": 0.60,
    "forbidden_rating_r2": 0.15, "procrustes": 0.95,
}


def knn(Z, q_idx, k, exclude_self=True, chunk=2000):
    out = np.empty((len(q_idx), k), dtype=np.int64)
    for s in range(0, len(q_idx), chunk):
        d = cdist(Z[q_idx[s:s + chunk]], Z)
        if exclude_self:
            d[np.arange(d.shape[0]), q_idx[s:s + chunk]] = np.inf
        out[s:s + chunk] = np.argsort(d, axis=1)[:, :k]
    return out


def procrustes_sim(A, B):
    A = A - A.mean(0); B = B - B.mean(0)
    A /= np.linalg.norm(A); B /= np.linalg.norm(B)
    s = np.linalg.svd(A.T @ B, compute_uv=False).sum()
    return float(s)  # in [0,1]; 1 = identical up to rotation/scale


def main():
    z_paths = [a for a in sys.argv[1:] if a.endswith(".npy") and "subset" not in a]
    sub_path = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--subset"), None)
    Zs = [np.load(p) for p in z_paths]
    Z = Zs[0]

    ids = pd.read_parquet(OUT / "ids.parquet").reset_index(drop=True)
    cp = np.load(OUT / "chain_pairs.npz")
    arch = json.load(open(OUT / "archetypes.json"))

    if sub_path:  # map global row indices into subset space
        sub = np.load(sub_path)
        pos = {g: i for i, g in enumerate(sub)}
        ids = ids.iloc[sub].reset_index(drop=True)
        holdout = np.array([pos[h] for h in cp["holdout"] if h in pos])
        arch = [dict(a, row=pos[a["row"]]) for a in arch if a["row"] in pos]
    else:
        holdout = cp["holdout"]
    assert len(Z) == len(ids), f"Z {len(Z)} vs ids {len(ids)}"
    n = len(Z)
    rng = np.random.default_rng(0)
    res = {}

    # 1 chain retrieval: held-out outlet finds a sibling in top-10
    brands = ids["brand_norm"].fillna("")
    hit = 0
    nn10 = knn(Z, holdout, 10)
    for r, h in enumerate(holdout):
        hit += brands.iloc[nn10[r]].eq(brands.iloc[h]).any()
    res["1_chain_retrieval"] = {"score": round(hit / max(1, len(holdout)), 3),
                                "n": int(len(holdout)),
                                "pass": hit / max(1, len(holdout)) >= THRESH["chain_retrieval"]}

    # 2 category kNN majority (5k sample)
    q = rng.choice(n, min(5000, n), replace=False)
    nn = knn(Z, q, 10)
    cats = ids["plexis_category"].to_numpy()
    maj = np.array([pd.Series(cats[nn[i]]).mode()[0] == cats[qi]
                    for i, qi in enumerate(q)])
    res["2_cat_knn"] = {"score": round(float(maj.mean()), 3),
                       "pass": maj.mean() >= THRESH["cat_knn"]}

    # 3 beyond-category: within cafes, neighbours closer on micrograph z than random
    XA = np.load(OUT / "X_A.npy")
    if sub_path:
        XA = XA[np.load(sub_path)]
    meta = json.load(open(OUT / "meta.json"))
    pmg_i = [i for i, c in enumerate(meta["a_cols"])
             if c in ("pmg_anchor_strength_sum", "pmg_complement_diversity")]
    cafe = np.where(cats == "cafe_coffee")[0]
    qc = rng.choice(cafe, min(800, len(cafe)), replace=False)
    d = cdist(Z[qc], Z[cafe]); d[np.arange(len(qc)), np.searchsorted(cafe, qc)] = np.inf
    nbr = cafe[np.argmin(d, axis=1)]
    d_nbr = np.abs(XA[np.ix_(qc, pmg_i)] - XA[np.ix_(nbr, pmg_i)]).mean()
    rnd = rng.choice(cafe, (len(qc), 2))
    d_rnd = np.abs(XA[np.ix_(rnd[:, 0], pmg_i)] - XA[np.ix_(rnd[:, 1], pmg_i)]).mean()
    ratio = float(d_nbr / d_rnd)
    res["3_beyond_cat"] = {"ratio": round(ratio, 3),
                           "pass": ratio <= THRESH["beyond_cat_ratio"]}

    # 4 geography leak
    lat0 = np.deg2rad(ids["latitude"].mean())
    xy = np.c_[ids["longitude"] * 111320 * np.cos(lat0), ids["latitude"] * 110540]
    ii = rng.integers(0, n, 100000); jj = rng.integers(0, n, 100000)
    ok = ii != jj; ii, jj = ii[ok], jj[ok]
    dz = np.linalg.norm(Z[ii] - Z[jj], axis=1)
    dm = np.linalg.norm(xy[ii] - xy[jj], axis=1)
    rho = float(spearmanr(dz, dm).statistic)
    res["4_geo_leak"] = {"rho": round(rho, 3), "pass": rho <= THRESH["geo_leak_rho"]}

    # 5 same-hex spread
    gmean = float(dz.mean())
    hx = ids.groupby("hex8_id").indices
    sd = [np.linalg.norm(Z[v[:30]][:, None] - Z[v[:30]][None], axis=2)
          [np.triu_indices(min(30, len(v)), 1)].mean()
          for v in hx.values() if len(v) >= 5]
    spread = float(np.mean(sd) / gmean)
    res["5_samehex_spread"] = {"ratio": round(spread, 3),
                               "pass": spread >= THRESH["samehex_spread"]}

    # 6 probes (standardized Z + RidgeCV — the e1 lesson)
    def probe(y, name, bar):
        m = ~np.isnan(y)
        Xtr, Xte, ytr, yte = train_test_split(Z[m], y[m], test_size=0.2, random_state=0)
        sc = StandardScaler().fit(Xtr)
        r = RidgeCV(alphas=np.logspace(-2, 4, 13)).fit(sc.transform(Xtr), ytr)
        r2 = float(r.score(sc.transform(Xte), yte))
        return {"r2": round(r2, 3), "pass": (r2 >= bar)}

    res["6a_probe_anchors"] = probe(XA[:, meta["a_cols"].index("pmg_anchors_400m")],
                                    "anchors", THRESH["probe_anchors_r2"])
    res["6b_probe_mrt"] = probe(XA[:, meta["a_cols"].index("pmg_walk_dist_mrt_m")],
                                "mrt", THRESH["probe_mrt_r2"])

    # 7 forbidden probe: rating must be UNpredictable (audit of the no-rating rule)
    rt = ids["rating"].to_numpy(float)
    p7 = probe(rt, "rating", -1)
    res["7_forbidden_rating"] = {"r2": p7["r2"],
                                 "pass": p7["r2"] <= THRESH["forbidden_rating_r2"]}

    # 8 seed stability
    if len(Zs) >= 2:
        sims = [procrustes_sim(Zs[0], Zb) for Zb in Zs[1:]]
        res["8_stability"] = {"procrustes": [round(s, 3) for s in sims],
                              "pass": min(sims) >= THRESH["procrustes"]}
    else:
        res["8_stability"] = {"procrustes": None, "pass": None}

    # 9 archetypes — top-5 printed + heuristic (>=3/5 same category)
    arch_out = []
    for a in arch:
        nn5 = knn(Z, np.array([a["row"]]), 5)[0]
        same = int((cats[nn5] == cats[a["row"]]).sum())
        arch_out.append({"label": a["label"], "anchor": a["name"],
                         "neighbours": [f"{ids['id'].iloc[i]}|{cats[i]}|{ids['parent_subzone_name'].iloc[i]}"
                                        for i in nn5],
                         "same_cat": same, "pass": same >= 3})
    res["9_archetypes"] = {"detail": arch_out,
                           "pass": all(a["pass"] for a in arch_out)}

    res["VERDICT"] = bool(all(v["pass"] for k, v in res.items()
                              if isinstance(v, dict) and v.get("pass") is not None))
    npfix = lambda o: o.item() if hasattr(o, "item") else str(o)  # noqa: E731
    out = OUT / f"exam_{Path(z_paths[0]).stem}.json"
    json.dump(res, open(out, "w"), indent=1, default=npfix)
    print(json.dumps({k: (v if k == "VERDICT" else
                          {kk: vv for kk, vv in v.items() if kk != "detail"})
                      for k, v in res.items()}, indent=1, default=npfix))
    print("exam ->", out)


if __name__ == "__main__":
    main()

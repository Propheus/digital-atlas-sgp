"""
Plexis-E v1 — eval harness (EMBEDDING_V5_DESIGN.md checks, machine-checkable set).

evaluate(Z, fast=True)  -> quick in-loop metrics (twins, probes, ARI, dist band)
evaluate(Z, fast=False) -> + negative control, zone silhouette, per-hex coherence

All probes use PA-blocked GroupKFold (spatial autocorrelation guard).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.linear_model import RidgeCV
from sklearn.metrics import adjusted_rand_score, r2_score, silhouette_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

# probes must be SCALE-INVARIANT across candidate embeddings: standardize Z
# and let RidgeCV pick alpha — raw-scale ridge silently under-regularizes
# large-scale embeddings (PCA) vs unit-scale ones (fixed 2026-06-11)


def _ridge_probe(Z, y, groups, gkf):
    Zs = StandardScaler().fit_transform(Z)
    preds, trues = [], []
    for tr, te in gkf.split(Zs, y, groups):
        r = RidgeCV(alphas=np.logspace(-2, 4, 13)).fit(Zs[tr], y[tr])
        preds.append(r.predict(Zs[te])); trues.append(y[te])
    return float(r2_score(np.concatenate(trues), np.concatenate(preds)))

HERE = Path(__file__).parent
L = pd.read_parquet(HERE / "labels.parquet")
META = json.load(open(HERE / "meta.json"))

MATURE = {"TOA PAYOH", "ANG MO KIO", "BEDOK", "QUEENSTOWN", "BUKIT MERAH",
          "CLEMENTI", "HOUGANG", "TAMPINES", "YISHUN", "WOODLANDS", "JURONG WEST",
          "BUKIT BATOK", "SERANGOON", "GEYLANG", "KALLANG", "TOA PAYOH"}
CBD_SZ = {"CECIL", "RAFFLES PLACE", "ANSON", "TANJONG PAGAR", "CLIFFORD PIER",
          "PHILLIP", "MAXWELL", "CENTRAL SUBZONE", "CITY HALL", "BAYFRONT SUBZONE",
          "MARINA CENTRE", "CHINATOWN", "BUGIS"}
NEWTOWN = {"PUNGGOL", "SENGKANG", "TENGAH", "SEMBAWANG"}


def _pick(subzone_contains, by="pop_resident"):
    s = L[L["parent_subzone_name"].str.contains(subzone_contains, na=False)]
    return None if not len(s) else int(s[by].idxmax())


TWINS = [  # (anchor picker, expectation fn over top-5 neighbor label rows, name)
    (lambda: _pick("TOA PAYOH CENTRAL"),
     lambda nb: (nb["parent_pa"].str.upper().isin(MATURE)).sum() >= 3, "toa_payoh_mature"),
    # hex8 grain absorbs tiny CBD subzones (no CECIL at this grain) — Central
    # Subzone is the canonical CBD anchor
    (lambda: _pick("CENTRAL SUBZONE", by="tgt_od_throughput"),
     lambda nb: nb["parent_subzone_name"].str.upper().isin(CBD_SZ).sum() >= 3, "cbd_core"),
    (lambda: _pick("MATILDA"),
     lambda nb: nb["parent_pa"].str.upper().isin(NEWTOWN).sum() >= 3, "matilda_newtown"),
    (lambda: _pick("TUAS", by="pop_resident"),
     lambda nb: (nb["zone_type_broad"] == "industrial").sum() >= 3, "tuas_industrial"),
    (lambda: _pick("YISHUN CENTRAL"),
     lambda nb: nb["parent_pa"].str.upper().isin(MATURE | NEWTOWN).sum() >= 3,
     "yishun_heartland"),
]
CONTRASTS = [("TUAS VIEW", "BOULEVARD"), ("LIM CHU KANG", "CECIL")]


def evaluate(Z, fast=True, X_raw=None):
    Z = np.asarray(Z, dtype=np.float64)
    D = cdist(Z, Z)
    np.fill_diagonal(D, np.inf)
    res = {}

    # twins
    hits = []
    for pick, expect, name in TWINS:
        i = pick()
        if i is None:
            continue
        nb = L.iloc[np.argsort(D[i])[:5]]
        hits.append(bool(expect(nb)))
        res[f"twin_{name}"] = bool(expect(nb))
    res["twin_hitrate"] = float(np.mean(hits))

    # contrasts: pair distance percentile
    flat = D[np.isfinite(D)]
    cperc = []
    for a, b in CONTRASTS:
        ia, ib = _pick(a), _pick(b)
        if ia is None or ib is None:
            continue
        cperc.append(float((flat < D[ia, ib]).mean()))
    res["contrast_pct_min"] = float(min(cperc)) if cperc else None

    # PA-blocked probes
    groups = L["parent_pa"].fillna("NA")
    gkf = GroupKFold(n_splits=5)
    for tname, tcol in [("hdb_psm", "tgt_hdb_psm"), ("od", "tgt_od_throughput"),
                        ("adq", "tgt_adq_default")]:
        y = L[tcol].to_numpy(dtype=float)
        m = np.isfinite(y) & (y != 0)
        if tcol == "tgt_od_throughput":
            y = np.log1p(np.abs(y)) * np.sign(y)
        res[f"probe_{tname}_r2"] = _ridge_probe(Z[m], y[m], groups[m], gkf)

    # zone classification probe + archetype-style recovery (ARI vs zone)
    zlab = L["zone_type_broad"].fillna("unknown")
    keep = zlab.isin(zlab.value_counts()[zlab.value_counts() > 20].index)
    km = KMeans(n_clusters=int(zlab[keep].nunique()), n_init=4,
                random_state=0).fit(Z[keep.to_numpy()])
    res["zone_ari"] = float(adjusted_rand_score(zlab[keep], km.labels_))

    if not fast:
        # distance sanity band vs raw features
        if X_raw is not None:
            Dr = cdist(X_raw, X_raw)
            iu = np.triu_indices(len(Z), 1)
            from scipy.stats import spearmanr
            sub = np.random.default_rng(0).choice(len(iu[0]), 200_000, replace=False)
            res["dist_rankcorr_raw"] = float(spearmanr(
                D[iu][sub], Dr[iu][sub]).statistic)
        # negative control: permuted target must fail
        rng = np.random.default_rng(1)
        yperm = rng.permutation(L["tgt_hdb_psm"].fillna(0).to_numpy())
        m = yperm != 0
        res["negctrl_r2"] = _ridge_probe(Z[m], yperm[m], groups[m], gkf)
        # zone silhouette + per-hex neighbor coherence
        res["zone_silhouette"] = float(silhouette_score(Z[keep.to_numpy()],
                                                        zlab[keep]))
        nb5 = np.argsort(D, axis=1)[:, :5]
        same = (zlab.to_numpy()[nb5] == zlab.to_numpy()[:, None]).sum(1)
        res["perhex_zone_coherence_pass"] = float((same >= 3).mean())
        # locality: parent PA share in top-50 vs base rate
        nb50 = np.argsort(D, axis=1)[:, :50]
        pa = L["parent_pa"].to_numpy()
        pa_share = (pa[nb50] == pa[:, None]).mean(1)
        res["locality_pa_share_top50"] = float(pa_share.mean())
    return res


def procrustes_corr(Z1, Z2):
    from scipy.spatial import procrustes
    _, _, disparity = procrustes(Z1, Z2)
    return float(1 - disparity)


if __name__ == "__main__":
    import sys
    Z = np.load(sys.argv[1])
    X = np.load(HERE / "X.npy")
    print(json.dumps(evaluate(Z, fast=False, X_raw=X), indent=1))

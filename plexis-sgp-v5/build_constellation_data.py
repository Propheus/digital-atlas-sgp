"""
Plexis Constellation — precompute app data from the plexis-p1 embedding.
Spec: docs/PLACE_GRAPH_APP_SPEC.md. Emits to apps/place-graph/public/data/.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
APP = ROOT.parent / "apps/place-graph/public/data"
(APP / "nn").mkdir(parents=True, exist_ok=True)
SEED = 42
K = 12
SHARDS = 128

CAT_COLOR = {  # travel-lens-compatible loud palette
    "restaurant": "#f97316", "hawker": "#fb923c", "fast_food": "#fdba74",
    "cafe_coffee": "#fcd34d", "bakery": "#fde68a", "bar_nightlife": "#c084fc",
    "entertainment_culture": "#a78bfa", "shopping_retail": "#38bdf8",
    "supermarket": "#7dd3fc", "convenience": "#bae6fd",
    "beauty_personal": "#f472b6", "services": "#94a3b8",
    "health_medical": "#34d399", "fitness_recreation": "#6ee7b7",
    "education": "#fb7185", "hotel_hospitality": "#fbbf24",
    "business_office": "#818cf8", "transport_parking": "#64748b",
    "industrial_mfg": "#a8a29e", "park_open": "#4ade80",
    "government_public": "#5eead4", "religious_worship": "#d4d4d8",
    "residential": "#fda4af", "transportation": "#64748b",
    "other_uncategorized": "#475569",
}


def main():
    E = pd.read_parquet(ROOT / "places/place_embedding_plexis_p1_64d.parquet")
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["id", "name", "plexis_category", "brand_norm",
                                  "latitude", "longitude", "parent_region",
                                  "parent_pa"])
    df = E[["id"]].merge(pl, on="id", how="left")
    Z = E.drop(columns=["id"]).to_numpy(np.float32)
    n = len(df)
    print(f"{n} places, Z {Z.shape}")

    # ---- UMAP 2D ----
    import umap
    um = umap.UMAP(n_components=2, n_neighbors=30, min_dist=0.08,
                   metric="cosine", random_state=SEED, verbose=True)
    XY = um.fit_transform(Z).astype(np.float32)
    XY -= XY.min(0); XY *= 1000.0 / XY.max()
    XY.astype(np.float32).tofile(APP / "galaxy_xy.bin")
    print("umap done")

    # ---- clusters + honest heuristic names ----
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=48, random_state=SEED, n_init=4).fit(Z)
    cl = km.labels_.astype(np.uint16)
    clusters = []
    for c in range(48):
        m = cl == c
        sub = df[m]
        cat_share = sub["plexis_category"].value_counts(normalize=True)
        top_cat, share = cat_share.index[0], cat_share.iloc[0]
        reg = sub["parent_pa"].value_counts(normalize=True)
        qual = (reg.index[0].title() if len(reg) and reg.iloc[0] >= 0.25
                else ("islandwide"))
        cat2 = f" + {cat_share.index[1].replace('_', ' ')}" \
            if share < 0.5 and len(cat_share) > 1 else ""
        brands = [b for b in sub["brand_norm"].dropna().value_counts().head(3).index
                  if b]
        clusters.append({
            "name": f"{top_cat.replace('_', ' ')}{cat2} · {qual}",
            "cx": float(XY[m, 0].mean()), "cy": float(XY[m, 1].mean()),
            "size": int(m.sum()), "top_cat": top_cat,
            "brands": brands})
    print("clusters named")

    # ---- kNN-12 shards (cosine on unit vectors = dot product) ----
    nn_idx = np.empty((n, K), dtype=np.int32)
    nn_sim = np.empty((n, K), dtype=np.float32)
    B = 2048
    for s in range(0, n, B):
        sims = Z[s:s + B] @ Z.T
        sims[np.arange(sims.shape[0]), np.arange(s, min(s + B, n))] = -2
        part = np.argpartition(-sims, K, axis=1)[:, :K]
        order = np.argsort(-np.take_along_axis(sims, part, 1), axis=1)
        nn_idx[s:s + B] = np.take_along_axis(part, order, 1)
        nn_sim[s:s + B] = np.take_along_axis(
            np.take_along_axis(sims, part, 1), order, 1)
        if (s // B) % 20 == 0:
            print(f"knn {s}/{n}", flush=True)
    for sh in range(SHARDS):
        rows = np.arange(sh, n, SHARDS)
        json.dump({int(r): [[int(i), int(round(max(0, sm) * 1000))]
                            for i, sm in zip(nn_idx[r], nn_sim[r])]
                   for r in rows},
                  open(APP / f"nn/s{sh}.json", "w"))
    print("knn shards done")

    # ---- arrays + meta ----
    cats = df["plexis_category"].astype("category")
    json.dump({   # no "id": app never uses it; saves ~3 MB on the wire
        "name": df["name"].fillna("").str.slice(0, 48).tolist(),
        "cat": cats.cat.codes.astype(int).tolist(),
        "lat": np.round(df["latitude"].to_numpy(float), 5).tolist(),
        "lng": np.round(df["longitude"].to_numpy(float), 5).tolist(),
        "cluster": cl.astype(int).tolist(),
    }, open(APP / "arrays.json", "w"))
    json.dump({
        "n": n, "k": K, "shards": SHARDS,
        "cats": list(cats.cat.categories),
        "cat_colors": [CAT_COLOR.get(c, "#64748b") for c in cats.cat.categories],
        "clusters": clusters,
        "src": "plexis-p1 64d place embedding (no rating signals; 9/9 locked exam) — UMAP n30/d0.08 cosine; KMeans-48",
    }, open(APP / "meta.json", "w"))
    sizes = {p.name: round(p.stat().st_size / 1e6, 1)
             for p in APP.glob("*.json")} | {"galaxy_xy.bin": round(
                 (APP / "galaxy_xy.bin").stat().st_size / 1e6, 1)}
    print("done:", sizes)


if __name__ == "__main__":
    main()

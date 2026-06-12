"""
Plexis SGP v4 — S6 Co-location lift matrix (colo_*) per hex9 -> hex8.

Spec: SITE_SELECTION_METRICS.md §S6.

Empirical synergy weights learned from 190K places:

  count_B(x) = number of B-places within 400 m of location x (self excluded)
  lift(A,B)  = mean(count_B over A-places) / mean(count_B over ALL places)

COUNT-based, not presence-based: a v1 used binary presence-within-400m and
saturated — P(office within 400 m of any urban place) ~ 1, capping lift at ~1
for every common category (cafe->office read 1.006). Counts don't saturate.
The denominator is the category-blind base over actual place locations, so
lift isolates "B concentrates near A beyond generic commercial clustering".
Bootstrap CI (200 resamples of the A-set); lifts whose 95% CI includes 1.0,
or with < MIN_SUPPORT A-places, are zeroed in the fit scores.

  colo_fit_c(hex9) = sum_B log(lift(c,B)) * share_B(hex9)
      share_B = count_B within 400 m of centroid / total places within 400 m

SHARE-weighted (mix-match), not presence-weighted: a v1 used binary partner
presence and collapsed into amenity-type breadth — r=0.95 with walk_score_avg,
duplicating walkability. Shares measure whether the surrounding COMPOSITION
matches what category c empirically thrives in, independent of volume
(share-fit max |r| vs walkability/pc_total = 0.35). hex8 rollup = MAX over
children (best site).

Output: catalog/colo_lift_matrix.parquet (24x24 + CI),
        hex/hex9_colo_fit.parquet, hex/hex8_colo_fit.parquet,
        hex/colo_lift_report.json
"""
import json
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent

RADIUS = 400.0
MIN_SUPPORT = 200
N_BOOT = 200
SEED = 11
FIT_CATS = ["cafe_coffee", "restaurant", "hawker", "fast_food", "supermarket",
            "convenience", "fitness_recreation", "health_medical",
            "beauty_personal", "shopping_retail", "education"]


def main():
    t0 = time.time()
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["latitude", "longitude", "plexis_category",
                                  "hex9_id"])
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    x, y = tr.transform(pl["longitude"].to_numpy(), pl["latitude"].to_numpy())
    xy = np.column_stack([x, y])
    cats = sorted(pl["plexis_category"].dropna().unique())
    n_pl = len(pl)

    # count of each category within 400 m of every place (self excluded)
    print(f"count matrix: {n_pl:,} places x {len(cats)} categories")
    present = np.zeros((n_pl, len(cats)), dtype=np.float32)
    cat_codes = pl["plexis_category"].to_numpy()
    for bi, b in enumerate(cats):
        own = cat_codes == b
        cnt = cKDTree(xy[own]).query_ball_point(xy, RADIUS, return_length=True,
                                                workers=-1).astype(np.float32)
        cnt[own] -= 1.0                               # don't count yourself
        present[:, bi] = cnt

    base = present.mean(axis=0)                       # category-blind base counts
    rng = np.random.default_rng(SEED)
    lift = np.full((len(cats), len(cats)), np.nan)
    lo_ci = np.full_like(lift, np.nan)
    hi_ci = np.full_like(lift, np.nan)
    for ai, a in enumerate(cats):
        rows = np.where(cat_codes == a)[0]
        if len(rows) < MIN_SUPPORT:
            continue
        pa = present[rows].mean(axis=0)
        lift[ai] = pa / np.maximum(base, 1e-9)
        boots = np.empty((N_BOOT, len(cats)))
        for r in range(N_BOOT):
            samp = rng.choice(rows, len(rows), replace=True)
            boots[r] = present[samp].mean(axis=0) / np.maximum(base, 1e-9)
        lo_ci[ai] = np.percentile(boots, 2.5, axis=0)
        hi_ci[ai] = np.percentile(boots, 97.5, axis=0)

    sig = (lo_ci > 1.0) | (hi_ci < 1.0)               # CI excludes 1
    mat = pd.DataFrame(lift, index=cats, columns=cats)
    out_rows = []
    for ai, a in enumerate(cats):
        for bi, b in enumerate(cats):
            if np.isfinite(lift[ai, bi]):
                out_rows.append({"cat_a": a, "cat_b": b, "lift": lift[ai, bi],
                                 "ci_lo": lo_ci[ai, bi], "ci_hi": hi_ci[ai, bi],
                                 "significant": bool(sig[ai, bi])})
    pd.DataFrame(out_rows).to_parquet(ROOT / "catalog/colo_lift_matrix.parquet",
                                      index=False)

    # ---- per-hex9 fit scores ------------------------------------------------
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")[["hex9_id", "lat", "lng"]]
    hx, hy = tr.transform(h9["lng"].to_numpy(), h9["lat"].to_numpy())
    hxy = np.column_stack([hx, hy])
    cnt_h = np.zeros((len(h9), len(cats)), dtype=np.float32)
    for bi, b in enumerate(cats):
        cnt_h[:, bi] = cKDTree(xy[cat_codes == b]).query_ball_point(
            hxy, RADIUS, return_length=True, workers=-1)
    share_h = cnt_h / np.maximum(cnt_h.sum(axis=1), 1.0)[:, None]

    out9 = pd.DataFrame({"hex9_id": h9["hex9_id"]})
    for c in FIT_CATS:
        ai = cats.index(c)
        wvec = np.where(sig[ai] & np.isfinite(lift[ai]) & (lift[ai] > 0),
                        np.log(np.maximum(lift[ai], 1e-6)), 0.0)
        wvec[ai] = 0.0                                # own-category excluded
        out9[f"colo_fit_{c}"] = (share_h @ wvec).round(4)
    out9.to_parquet(ROOT / "hex/hex9_colo_fit.parquet", index=False)

    out9["hex8_of"] = [h3.cell_to_parent(c, 8) for c in out9["hex9_id"]]
    fit_cols = [f"colo_fit_{c}" for c in FIT_CATS]
    out8 = out9.groupby("hex8_of")[fit_cols].max().reset_index() \
        .rename(columns={"hex8_of": "hex8_id"})
    out8.to_parquet(ROOT / "hex/hex8_colo_fit.parquet", index=False)

    key_pairs = {f"{a}->{b}": round(float(mat.loc[a, b]), 3)
                 for a, b in [("cafe_coffee", "business_office"),
                              ("bar_nightlife", "bar_nightlife"),
                              ("fitness_recreation", "residential"),
                              ("supermarket", "supermarket"),
                              ("hawker", "business_office")]}
    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S6",
        "radius_m": RADIUS, "min_support": MIN_SUPPORT, "n_boot": N_BOOT,
        "categories": len(cats),
        "pairs_total": int(np.isfinite(lift).sum()),
        "pairs_significant": int(sig[np.isfinite(lift)].sum()),
        "cats_below_support": [c for c in cats
                               if (cat_codes == c).sum() < MIN_SUPPORT],
        "key_pairs": key_pairs,
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/colo_lift_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()

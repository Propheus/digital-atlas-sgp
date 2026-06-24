"""
Plexis-E v1 — feature prep for the hex8 embedding (EMBEDDING_V5_DESIGN.md).

From hex8_all_features (1191 x 801) builds the training matrix:
  - numeric cols only; identity/bookkeeping excluded
  - OPPORTUNITY view (cap_*, colo_fit_*, roi_*) excluded from INPUT (model
    outputs; also probe-adjacent)
  - probe targets excluded from input: hdb_resale_4r_median_psm, od_throughput,
    adq_default (+ archetype/zone labels used for recovery checks)
  - per-column transform: log1p for skewed non-negative cols, then z-score
  - NaN -> 0 AFTER z, with per-family NaN indicator channels appended
  - every input col assigned a VIEW (WHO/WHERE/WHAT/FLOW/PRICE) for view-masking

Outputs: embedding/X.npy, embedding/meta.json (cols, views, targets, labels)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent
OUT = Path(__file__).parent

EXCLUDE_EXACT = {"hex8_id", "lat", "lng", "n_children", "n_children_wk",
                 "n_children_tr", "hdb_resale_4r_median_psm", "od_throughput",
                 "adq_default", "ca_footfall", "industrial_adjacency_score",
                 "format_fit_score", "vis_exit_footfall"}
# nous V4 embedding-leak fix: derived footfall + rent are NOT inputs (they correlate with
# the held-out price/connectivity probes -> inflate recovery). Folded DOMAIN-PACK hero scores
# (re_/risk_/insurance_/utility_/mobility_/retail_) are downstream MODEL OUTPUTS -- same class
# as cap_/roi_/colo_fit_. Original urbanism indices (walkability_score, vibrancy_index, ...)
# are STRUCTURAL inputs and are kept.
EXCLUDE_PREFIX = ("cap_", "colo_fit_", "roi_", "parent_", "zone_type",
                  "archetype", "pop_callout", "adq_primary", "adq_worst_factor",
                  "mrt_reach_mode", "dominant_use", "pc_dominant",
                  "best_max", "rent_", "vis_exit_station",
                  "pipe_mrt_name", "cap_best", "dt_class",
                  "re_", "risk_", "insurance_", "utility_", "mobility_",
                  "retail_", "format_fit", "transport_subtype")

VIEWS = [
    ("WHO", ("pop_", "nvp_", "female_pop_share", "pr_share", "low_income_share",
             "dt_", "walking_dependent", "vulnerability", "access_vuln",
             "crowd_", "nonres_share", "n_dwell", "hdb_pop")),
    ("FLOW", ("od_", "bus_taps", "daily_", "gtfs_", "iso_", "labor_", "time_to_",
              "n_dest", "pct_dest", "mrt_reach", "peak_wait", "crowding",
              "n_lines", "n_stations", "ca_", "commercial_activity")),
    ("PRICE", ("rent_", "hdb_resale", "nl_", "sat_", "gap_")),
    ("WHAT", ("pc_", "pc2_", "mg_", "biz_", "osm_", "pmg_", "coworking",
              "wet_market", "petrol", "condo_", "hawker", "chas", "preschool",
              "school", "tourist", "silver", "poi_", "in_", "primary_")),
    # WHERE = fallback: land use, buildings, roads, walk, transit infra, etc.
]


def assign_view(col):
    for v, prefixes in VIEWS:
        if col.startswith(prefixes):
            return v
    return "WHERE"


def main():
    df = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    df = df.set_index("hex8_id")

    num = df.select_dtypes(include=[np.number])
    cols = [c for c in num.columns
            if c not in EXCLUDE_EXACT and not c.startswith(EXCLUDE_PREFIX)]
    X = num[cols].copy()

    # NaN indicators per family BEFORE imputation
    nan_fams = {"adq_": "nanind_adq", "min15_": "nanind_min15",
                "time_to_": "nanind_time", "rent_": "nanind_rent",
                "dt_ratio": "nanind_dt"}
    indicators = {}
    for pref, name in nan_fams.items():
        fam = [c for c in cols if c.startswith(pref)]
        if fam:
            indicators[name] = X[fam].isna().all(axis=1).astype(float)

    # transforms
    stats = {}
    for c in cols:
        v = X[c].astype(float)
        if v.min() >= 0 and v.skew() > 2:
            v = np.log1p(v)
        mu, sd = v.mean(), v.std()
        X[c] = ((v - mu) / (sd if sd > 1e-9 else 1.0)).clip(-6, 6)
        stats[c] = {"mu": float(mu), "sd": float(sd)}
    X = X.fillna(0.0)
    for name, ind in indicators.items():
        X[name] = ind

    views = {c: assign_view(c) for c in X.columns}
    for n in indicators:
        views[n] = "MASKCH"

    # labels + probe targets (kept OUT of X)
    labels = pd.DataFrame({
        "hex8_id": df.index,
        "parent_pa": df["parent_pa"].values,
        "parent_subzone_name": df["parent_subzone_name"].values,
        "zone_type_broad": df["zone_type_broad"].values
        if "zone_type_broad" in df else "unknown",
        "pop_resident": df["pop_resident"].values,
        "tgt_hdb_psm": df["hdb_resale_4r_median_psm"].values,
        "tgt_od_throughput": df["od_throughput"].values,
        "tgt_adq_default": df["adq_default"].values,
    })

    np.save(OUT / "X.npy", X.to_numpy(dtype=np.float32))
    labels.to_parquet(OUT / "labels.parquet", index=False)
    from collections import Counter
    meta = {"n": len(X), "d": X.shape[1], "cols": list(X.columns),
            "views": views, "view_counts": dict(Counter(views.values()))}
    json.dump(meta, open(OUT / "meta.json", "w"))
    print(f"X: {X.shape} | views: {meta['view_counts']}")


if __name__ == "__main__":
    main()

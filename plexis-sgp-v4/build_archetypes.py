"""
Plexis SGP v4 — Stage 15: hex archetypes via k-means clustering.

K-means on a curated feature subset (population + land-use + transit + activity
+ pricing) to produce K=8 archetypes per hex9 + per subzone.

Output cols:
  archetype_id    integer 0..K-1
  archetype_label human-readable string
  archetype_dist  distance to assigned cluster centroid (normalized)

Outputs:
  hex/hex9_archetypes.parquet
  hex/subzone_archetypes.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).parent

K = 8  # number of archetypes
SEED = 42

# Curated feature set for clustering — the dimensions we want archetypes to span
FEATURES = [
    "pop_resident","pop_nonresident",
    "lu_residential_share","lu_commercial_share","lu_industrial_share","lu_park_share",
    "bld_total_count","bld_footprint_share",
    "transit_score","walkability_score",
    "pc_total","pc_magnets","pc_cat_business_office","pc_cat_shopping_retail",
    "pc_cat_residential","pc_cat_industrial_mfg","pc_cat_hawker",
    "nl_2024","nl_commercial_indicator",
    "hdb_resale_4r_median_psm","hdb_resale_in_town",
    "school_count_total","primary_schools_within_1km",
    "pull_cbd","pull_mall","pull_mrt_interchange",
    "vibrancy_index","commercial_intensity","family_index","density_pressure",
]


def label_archetypes(centers, feature_names):
    """Auto-label clusters by checking which named axes dominate each centroid.
    Centers are in standardized (z-score) space; >1 means strongly above mean."""
    # Map a 'theme' to a list of features that signal it
    THEMES = [
        ("CBD_office",         ["pc_cat_business_office","pull_cbd","commercial_intensity","nl_2024"]),
        ("Retail_hub",         ["pc_cat_shopping_retail","pc_magnets","pull_mall","commercial_intensity"]),
        ("Industrial",         ["lu_industrial_share","pc_cat_industrial_mfg"]),
        ("Green_open",         ["lu_park_share"]),
        ("Mature_HDB",         ["hdb_resale_4r_median_psm","hdb_resale_in_town","pop_resident"]),
        ("Family_residential", ["pc_cat_residential","primary_schools_within_1km","family_index"]),
        ("Transit_hub",        ["transit_score","pull_mrt_interchange"]),
        ("Mixed_use_vibrant",  ["vibrancy_index","pc_total","walkability_score"]),
        ("Low_density_outer",  []),  # fallback for sparse clusters
    ]
    feat_idx = {f: i for i, f in enumerate(feature_names)}

    raw_labels = []
    for i, c in enumerate(centers):
        # Score each theme = mean z-score of its features (only those present)
        best_theme, best_score = None, -np.inf
        for theme, feats in THEMES:
            present = [f for f in feats if f in feat_idx]
            if not present:
                # fallback theme (Low_density_outer): pick if all centers are negative
                score = -c.max()
            else:
                score = np.mean([c[feat_idx[f]] for f in present])
            if score > best_score:
                best_score = score
                best_theme = theme
        raw_labels.append(best_theme)

    # Disambiguate duplicates
    seen = {}
    final = []
    for l in raw_labels:
        seen[l] = seen.get(l, 0) + 1
        final.append(f"{l}_{seen[l]}" if seen[l] > 1 else l)
    return final


def cluster_scale(scale, key):
    print(f"\n--- {scale.upper()} ---")
    df = pd.read_parquet(ROOT / f"hex/{scale}_all_features.parquet")
    feats = [f for f in FEATURES if f in df.columns]
    print(f"  features used: {len(feats)}/{len(FEATURES)}")

    X = df[feats].fillna(0).values.astype(float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    km = KMeans(n_clusters=K, random_state=SEED, n_init=10)
    labels = km.fit_predict(Xs)
    centers = km.cluster_centers_
    inertias = ((Xs - centers[labels]) ** 2).sum(axis=1)

    arch_labels = label_archetypes(centers, feats)
    label_map = dict(enumerate(arch_labels))
    out = pd.DataFrame({
        key: df[key],
        "archetype_id": labels.astype(int),
        "archetype_label": [label_map[l] for l in labels],
        "archetype_dist": np.sqrt(inertias).round(3),
    })
    out.to_parquet(ROOT / f"hex/{scale}_archetypes.parquet", index=False)
    print(f"  {scale}_archetypes: {out.shape}")
    print(f"  archetype counts: {out['archetype_label'].value_counts().to_dict()}")
    return arch_labels


def main():
    t0 = time.time()
    h9_labels = cluster_scale("hex9", "hex9_id")
    sz_labels = cluster_scale("subzone", "subzone_c")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "k": K,
        "hex9_archetype_labels": h9_labels,
        "subzone_archetype_labels": sz_labels,
    }
    with open(ROOT / "hex/archetypes_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

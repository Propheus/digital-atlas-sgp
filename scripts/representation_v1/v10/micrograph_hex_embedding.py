#!/usr/bin/env python3
"""
Build a place-origin hex embedding from raw per-place micrographs.

Motivation:
  hex_features_v10 already has 156 `mg_*` aggregate features per hex (pct_dense,
  mean anchor_count, cv_transit, ...). These collapse away the RICH structure
  in each place's micrograph: weighted anchor-type composition, tier×decay
  structure, gap-tier signature. This script builds a per-place vector from
  that structure and pools per H3-9 hex.

Per-place vector (≈56-d):
  4   context_vector (transit, competitor, complementary, demand)
  3   competitive_pressure, demand_diversity, walkability_index/100
  3   log1p(anchor_count), log1p(competitor_count), log1p(fnb_density)
  4   tier distribution (normalized_weight sum per tier 1..4)
  15  anchor-type distribution (normalized_weight sum per top-15 types)
  4   density_band one-hot (hyperdense, dense, moderate, sparse)
  1   has_gaps flag
  4   gap_tiers one-hot (which tiers are flagged)
  12  category one-hot
  ---
  50 features

Pooling per hex:
  - mean pool (unweighted average across places in hex)
  - result: 7318 hexes × 50 features

Evaluation vs GCN-64:
  - kNN-PA agreement @ k=10 (same split as GCN)
  - cosine similarity correlation (is it capturing different signal?)
  - concat GCN-64 ⊕ place-50 → 114-d, test kNN-PA
"""
import json
import os
import time
from collections import Counter

import numpy as np
import pandas as pd
import h3

ROOT = "/home/azureuser/digital-atlas-sgp"
MG_DIR = f"{ROOT}/micrograph_output"
OUT_DIR = f"{ROOT}/data/hex_v10/micrograph_embedding"
os.makedirs(OUT_DIR, exist_ok=True)

CATEGORIES = [
    "bakery_pastry", "bar_nightlife", "beauty_personal_care", "cafe",
    "convenience_daily_needs", "education", "fast_food_qsr",
    "fitness_recreation", "hawker", "health_medical", "restaurant",
    "shopping_retail",
]
DENSITY_BANDS = ["hyperdense", "dense", "moderate", "sparse"]


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def discover_anchor_types():
    """Scan all micrographs to find top-15 most common anchor types (pads if fewer)."""
    log("Scanning anchor-type vocabulary across all 12 categories...")
    type_counts = Counter()
    for cat in CATEGORIES:
        path = f"{MG_DIR}/{cat}_micrographs.jsonl"
        with open(path) as f:
            for line in f:
                rec = json.loads(line)
                for a in rec.get("anchors", []):
                    t = a.get("anchor_type")
                    if t:
                        type_counts[t] += 1
    top = [t for t, _ in type_counts.most_common(15)]
    log(f"  Found {len(type_counts)} unique anchor types; using all {len(top)}: {top}")
    return top


def per_place_vector(rec, cat_idx, anchor_type_vocab, vec_size):
    """Return vec_size-d feature vector for one place."""
    v = np.zeros(vec_size, dtype=np.float32)
    n_types = len(anchor_type_vocab)
    # Offsets (dynamic based on vocab size)
    OFF_DB = 14 + n_types                    # density_band start
    OFF_HASGAPS = OFF_DB + 4                 # 1 slot
    OFF_GAPTIERS = OFF_HASGAPS + 1           # 4 slots
    OFF_CAT = OFF_GAPTIERS + 4               # 12 slots

    # 0:4 context_vector
    cv = rec.get("context_vector", {}) or {}
    v[0] = cv.get("transit", 0.0)
    v[1] = cv.get("competitor", 0.0)
    v[2] = cv.get("complementary", 0.0)
    v[3] = cv.get("demand", 0.0)

    # 4:7 quality scalars
    v[4] = rec.get("competitive_pressure", 0.0) or 0.0
    v[5] = rec.get("demand_diversity", 0.0) or 0.0
    v[6] = (rec.get("walkability_index", 0.0) or 0.0) / 100.0

    # 7:10 log counts
    v[7] = np.log1p(rec.get("anchor_count", 0) or 0)
    v[8] = np.log1p(rec.get("competitor_count", 0) or 0)
    v[9] = np.log1p(rec.get("fnb_density", 0) or 0)

    # 10:14 tier distribution (sum normalized_weight per tier)
    # 14:29 anchor-type distribution (sum normalized_weight per top-15 type)
    type_to_idx = {t: i for i, t in enumerate(anchor_type_vocab)}
    for a in rec.get("anchors", []):
        tier = a.get("tier")
        w = a.get("normalized_weight", 0.0) or 0.0
        if tier in (1, 2, 3, 4):
            v[10 + tier - 1] += w
        t = a.get("anchor_type")
        if t in type_to_idx:
            v[14 + type_to_idx[t]] += w

    # density_band one-hot
    db = rec.get("density_band")
    if db in DENSITY_BANDS:
        v[OFF_DB + DENSITY_BANDS.index(db)] = 1.0

    # has_gaps
    v[OFF_HASGAPS] = 1.0 if rec.get("has_gaps") else 0.0

    # gap_tiers one-hot
    for gt in rec.get("gap_tiers", []) or []:
        if gt in (1, 2, 3, 4):
            v[OFF_GAPTIERS + gt - 1] = 1.0

    # category one-hot
    v[OFF_CAT + cat_idx] = 1.0

    return v


def main():
    t0 = time.time()
    anchor_type_vocab = discover_anchor_types()
    n_types = len(anchor_type_vocab)
    VEC_SIZE = 14 + n_types + 4 + 1 + 4 + 12  # = 35 + n_types
    log(f"  Per-place vector size: {VEC_SIZE}")

    # Collect per-place vectors tagged with hex_id
    log("\nBuilding per-place vectors and mapping to H3-9 hexes...")
    place_rows = []
    for cat_idx, cat in enumerate(CATEGORIES):
        path = f"{MG_DIR}/{cat}_micrographs.jsonl"
        n = 0
        with open(path) as f:
            for line in f:
                rec = json.loads(line)
                lat, lng = rec.get("latitude"), rec.get("longitude")
                if lat is None or lng is None:
                    continue
                hex_id = h3.latlng_to_cell(lat, lng, 9)
                v = per_place_vector(rec, cat_idx, anchor_type_vocab, VEC_SIZE)
                place_rows.append((hex_id, v))
                n += 1
        log(f"  {cat:<25} {n:>6} places")

    log(f"\nTotal places with valid coordinates: {len(place_rows)}")

    # Pool per hex
    log("\nPooling per hex (mean)...")
    hex_vecs = {}
    hex_counts = {}
    for hid, v in place_rows:
        if hid not in hex_vecs:
            hex_vecs[hid] = np.zeros(VEC_SIZE, dtype=np.float64)
            hex_counts[hid] = 0
        hex_vecs[hid] += v
        hex_counts[hid] += 1
    for hid in hex_vecs:
        hex_vecs[hid] /= hex_counts[hid]
    log(f"  Hexes with places: {len(hex_vecs)}")

    # Align to canonical hex order (7,318 hexes from hex_features_v10)
    canonical = pd.read_parquet(f"{ROOT}/data/hex_v10/hex_features_v10.parquet")[
        ["hex_id", "parent_pa", "parent_subzone"]
    ]
    n_hex = len(canonical)
    X = np.zeros((n_hex, VEC_SIZE), dtype=np.float32)
    has_places = np.zeros(n_hex, dtype=bool)
    for i, hid in enumerate(canonical["hex_id"].tolist()):
        if hid in hex_vecs:
            X[i] = hex_vecs[hid]
            has_places[i] = True
    log(f"  Canonical hexes with ≥1 place-with-micrograph: "
        f"{has_places.sum()}/{n_hex} ({100*has_places.sum()/n_hex:.1f}%)")

    # Save
    col_names = (
        ["mp_cv_transit", "mp_cv_competitor", "mp_cv_complementary", "mp_cv_demand",
         "mp_comp_pressure", "mp_demand_diversity", "mp_walkability",
         "mp_log_anchor_count", "mp_log_competitor_count", "mp_log_fnb_density"]
        + [f"mp_tier{i}_weight" for i in range(1, 5)]
        + [f"mp_anchor_{t}" for t in anchor_type_vocab]
        + [f"mp_db_{b}" for b in DENSITY_BANDS]
        + ["mp_has_gaps"]
        + [f"mp_gap_tier{i}" for i in range(1, 5)]
        + [f"mp_cat_{c}" for c in CATEGORIES]
    )
    assert len(col_names) == VEC_SIZE, f"Expected {VEC_SIZE} columns, got {len(col_names)}"

    out = pd.DataFrame(X, columns=col_names)
    out.insert(0, "hex_id", canonical["hex_id"].values)
    out.insert(1, "parent_pa", canonical["parent_pa"].values)
    out.insert(2, "parent_subzone", canonical["parent_subzone"].values)
    out.insert(3, "has_place_micrographs", has_places)
    out_path = f"{OUT_DIR}/hex_place_embedding_{VEC_SIZE}.parquet"
    out.to_parquet(out_path, index=False)
    log(f"\nSaved: {out_path} ({os.path.getsize(out_path)/1024:.0f} KB)")

    # ============================================================
    # Evaluation: kNN-PA agreement vs GCN-64
    # ============================================================
    log("\n" + "=" * 60)
    log("EVALUATION: kNN-PA agreement")
    log("=" * 60)

    # Load GCN-64 for comparison
    gcn = pd.read_parquet(f"{ROOT}/data/hex_v10/gcn_results/gcn_embedding_64.parquet")
    gcn_emb = gcn[[f"g{i}" for i in range(64)]].to_numpy(dtype=np.float32)
    # Align to canonical
    gcn = gcn.set_index("hex_id")
    gcn_emb = gcn.loc[canonical["hex_id"].tolist(), [f"g{i}" for i in range(64)]].to_numpy(np.float32)

    pa_labels = np.asarray(canonical["parent_pa"].astype(str).values)
    sz_labels = np.asarray(canonical["parent_subzone"].astype(str).values)

    def knn_agreement(Z, labels, k=10, mask=None):
        """For each hex with mask=True, find k nearest (excl self) by cosine,
           return fraction that share the same label."""
        idx = np.where(mask)[0] if mask is not None else np.arange(len(Z))
        Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
        S = Zn @ Zn.T
        np.fill_diagonal(S, -np.inf)
        # Restrict to mask for both query and neighbors
        if mask is not None:
            S = S[np.ix_(idx, idx)]
            labs = labels[idx]
        else:
            labs = labels
        nn = np.argsort(-S, axis=1)[:, :k]
        agree = (labs[nn] == labs[:, None]).mean()
        return agree

    # Use only hexes that have micrographs for a FAIR comparison on place-only embedding
    for name, Z in [
        ("GCN-64 (region)", gcn_emb),
        (f"Place-{VEC_SIZE} (place-origin pool)", X),
        (f"Concat GCN-64 ⊕ Place-{VEC_SIZE} ({64+VEC_SIZE}-d)", np.hstack([gcn_emb, X])),
    ]:
        # Full set
        pa_full = knn_agreement(Z, pa_labels, k=10)
        # Only hexes with places (fair for place-50)
        pa_mask = knn_agreement(Z, pa_labels, k=10, mask=has_places)
        sz_mask = knn_agreement(Z, sz_labels, k=10, mask=has_places)
        log(f"\n  {name}")
        log(f"    kNN-PA @10 (all 7318):           {pa_full:.3f}")
        log(f"    kNN-PA @10 (only with places):   {pa_mask:.3f}")
        log(f"    kNN-Subzone @10 (only w/ places): {sz_mask:.3f}")

    # Cosine sim correlation between GCN and Place embeddings
    log("\n\nCOMPLEMENTARITY: how different are the two embeddings?")
    # Pairwise cosine on subset of 1000 hexes for speed
    rng = np.random.default_rng(42)
    samp = rng.choice(np.where(has_places)[0], size=min(1000, has_places.sum()), replace=False)
    def cos_mat(Z, ix):
        Zn = Z[ix] / (np.linalg.norm(Z[ix], axis=1, keepdims=True) + 1e-9)
        return Zn @ Zn.T
    gcn_sim = cos_mat(gcn_emb, samp)
    place_sim = cos_mat(X, samp)
    iu = np.triu_indices_from(gcn_sim, k=1)
    corr = np.corrcoef(gcn_sim[iu], place_sim[iu])[0, 1]
    log(f"  Pearson correlation of pairwise cosine sims: {corr:.3f}")
    log(f"  (if >0.9: redundant signal; if <0.7: complementary)")

    log(f"\nTime: {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

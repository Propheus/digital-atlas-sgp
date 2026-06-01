"""
Plexis SGP v4 — JSON catalog (app-consumption friendly).

Wraps the existing catalog/dataset_catalog.parquet + feature_catalog.parquet
plus an embeddings catalog into clean JSON files that apps can fetch directly.

Outputs:
  catalog/dataset_catalog.json
  catalog/feature_catalog.json
  catalog/embedding_catalog.json
  catalog/atlas_manifest.json   — one-stop summary linking everything
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
CAT = ROOT / "catalog"

# === Datasets ===
ds = pd.read_parquet(CAT / "dataset_catalog.parquet")
fc = pd.read_parquet(CAT / "feature_catalog.parquet")

# Convert to JSON
ds_records = ds.fillna("").to_dict(orient="records")
for r in ds_records:
    for k in ("size_bytes","n_rows","n_cols"):
        if k in r and r[k] != "":
            try: r[k] = int(r[k])
            except: pass

(CAT / "dataset_catalog.json").write_text(
    json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "n_datasets": len(ds_records),
                "datasets": ds_records}, indent=2, default=str))

fc_records = fc.fillna("").to_dict(orient="records")
for r in fc_records:
    for k in ("n_unique","null_pct","min","max","mean","median"):
        if k in r and r[k] != "":
            try: r[k] = float(r[k])
            except: pass

(CAT / "feature_catalog.json").write_text(
    json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "n_features": len(fc_records),
                "scales": {s: int((fc["scale"]==s).sum()) for s in fc["scale"].dropna().unique()},
                "features": fc_records}, indent=2, default=str))

# === Embedding catalog ===
EMBEDDINGS = [
    # Hex
    {"name":"hex9_embedding_where_64d", "scale":"hex9", "dim":64, "method":"PCA",
     "input":"hex_all_features (545 numeric cols)", "var_explained":0.843,
     "purpose":"location-context embedding from feature compression",
     "path":"hex/hex9_embedding_where_64d.parquet", "key":"hex9_id"},
    {"name":"hex9_embedding_node2vec_64d", "scale":"hex9", "dim":64, "method":"Node2Vec (Word2Vec on H3 grid_ring random walks)",
     "input":"H3 grid_ring(1) adjacency, 30 walks × length 30",
     "purpose":"pure-topology hex embedding",
     "path":"hex/hex9_embedding_node2vec_64d.parquet", "key":"hex9_id"},
    {"name":"hex9_embedding_gcn_64d", "scale":"hex9", "dim":64, "method":"2-hop GCN (A_sym × A_sym × X) + PCA-64",
     "input":"hex_all_features over A_sym normalized adjacency", "var_explained":0.966,
     "purpose":"graph-smoothed feature similarity",
     "path":"hex/hex9_embedding_gcn_64d.parquet", "key":"hex9_id"},
    {"name":"hex9_embedding_combined_128d", "scale":"hex9", "dim":128, "method":"PCA concat",
     "input":"WHERE_64d + mean(place_what_64d in hex)",
     "purpose":"PCA-based combined hex embedding",
     "path":"hex/hex9_embedding_combined_128d.parquet", "key":"hex9_id"},
    {"name":"hex9_embedding_super_128d", "scale":"hex9", "dim":128, "method":"concat[node2vec, gcn]",
     "input":"hex_node2vec_64 + hex_gcn_64",
     "purpose":"graph ensemble — topology + feature smoothing",
     "path":"hex/hex9_embedding_super_128d.parquet", "key":"hex9_id"},
    # Place
    {"name":"place_embedding_what_64d", "scale":"place", "dim":64, "method":"PCA",
     "input":"137 place features (cat one-hot + brand + numeric)", "var_explained":0.710,
     "purpose":"intrinsic place identity (PCA)",
     "path":"places/place_embedding_what_64d.parquet", "key":"id"},
    {"name":"place_embedding_place2vec_64d", "scale":"place", "dim":64, "method":"Word2Vec skip-gram",
     "input":"hex co-occurrence sentences (10 epochs of shuffled places per hex)",
     "purpose":"co-location semantics via graph context",
     "path":"places/place_embedding_place2vec_64d.parquet", "key":"id"},
    {"name":"place_embedding_combined_128d", "scale":"place", "dim":128, "method":"PCA concat",
     "input":"place_what_64d + place's hex's where_64d",
     "purpose":"PCA-based combined place embedding",
     "path":"places/place_embedding_combined_128d.parquet", "key":"id"},
    {"name":"place_embedding_super_128d", "scale":"place", "dim":128, "method":"concat[place2vec, what_pca]",
     "input":"place2vec_64 + place_what_64",
     "purpose":"graph + identity ensemble",
     "path":"places/place_embedding_super_128d.parquet", "key":"id"},
    {"name":"place_embedding_mega_256d", "scale":"place", "dim":256, "method":"concat[place2vec, what_pca, hex_gcn, hex_where]",
     "input":"all 4 64d embeddings",
     "purpose":"full-ensemble (graph + identity + location-context)",
     "path":"places/place_embedding_mega_256d.parquet", "key":"id"},
]

(CAT / "embedding_catalog.json").write_text(
    json.dumps({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "n_embeddings": len(EMBEDDINGS),
                "embeddings": EMBEDDINGS}, indent=2))

# === Atlas manifest — top-level summary ===
checkpoints = sorted(ROOT.glob("CHECKPOINT_v*.json"))
latest = json.load(open(checkpoints[-1])) if checkpoints else {}

manifest = {
    "atlas_name": "Plexis SGP",
    "version": "4.8.0",
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "scales": {
        "hex9": {"resolution": "H3 res-9 (~174m edge, ~0.105 km²)", "n_cells": 7318},
        "hex8": {"resolution": "H3 res-8 (~461m edge, ~0.737 km²)", "n_cells": 1191},
        "subzone": {"resolution": "URA Master Plan 2019 subzone", "n_cells": 326},
        "place": {"resolution": "individual venue/POI", "n_places": 190591},
    },
    "primary_keys": {
        "hex9": "hex9_id (H3 cell index)",
        "hex8": "hex8_id (H3 cell index)",
        "subzone": "subzone_c (URA code, e.g. AMSZ01)",
        "place": "id (12-char unique place ID)",
    },
    "master_bundles": {
        "hex9_all_features": {"path": "hex/hex9_all_features.parquet", "shape": [7318, 558]},
        "hex8_all_features": {"path": "hex/hex8_all_features.parquet", "shape": [1191, 548]},
        "subzone_all_features": {"path": "hex/subzone_all_features.parquet", "shape": [326, 388]},
        "places_final": {"path": "places/sgp_places_final.parquet", "shape": [190591, 27]},
        "places_micrograph": {"path": "places/sgp_places_micrograph.parquet", "shape": [190591, 19]},
    },
    "catalogs": {
        "datasets": "catalog/dataset_catalog.json",
        "features": "catalog/feature_catalog.json",
        "embeddings": "catalog/embedding_catalog.json",
        "report_html": "PLEXIS_v4_FINAL_REPORT.html",
    },
    "embedding_count": len(EMBEDDINGS),
    "feature_count": len(fc_records),
    "dataset_count": len(ds_records),
    "pipeline_stages": 47,
}

(CAT / "atlas_manifest.json").write_text(json.dumps(manifest, indent=2))

print(f"\n=== Catalogs written to {CAT}/ ===")
for f in sorted(CAT.glob("*.json")):
    print(f"  {f.name}  ({f.stat().st_size:,} bytes)")

# Plexis SGP v4.7.0 — Deployment Manifest

**Deployed location:** `atlas-deploy:/home/azureuser/plexis-sgp-v4/` (propheus-deploy-server)
**Total size:** 362 MB · **Versioned via:** `CHECKPOINT_v4.7.0.{json,md}`

## Layout for app integration

```
/home/azureuser/plexis-sgp-v4/
├── hex/                            # 107 parquets, all hex-scale features
│   ├── hex9_all_features.parquet   # 7,318 × 558 — primary master bundle
│   ├── hex8_all_features.parquet   # 1,191 × 548
│   ├── subzone_all_features.parquet # 326 × 388
│   ├── hex9_embedding_where_64d.parquet     # 7,318 × 65
│   ├── hex9_embedding_combined_128d.parquet # 7,318 × 129
│   └── …                           # per-layer parquets if you need lean joins
├── places/
│   ├── sgp_places_final.parquet            # 190,591 places × 27 cols
│   ├── sgp_places_micrograph.parquet       # 190,591 × 19 (per-place context)
│   ├── place_embedding_what_64d.parquet    # 190,591 × 65
│   └── place_embedding_combined_128d.parquet # 190,591 × 129
├── CHECKPOINT_v4.7.0.json          # canonical manifest
├── PLEXIS_v4_FINAL_REPORT.html     # full feature catalog (open in browser)
└── build_*.py / validate_*.py      # 50 build + validate scripts (for reproducibility only;
                                    # apps should read the parquets, not re-run these)
```

## Primary tables apps should join on

| Key | Joins between |
|---|---|
| `hex9_id` | every hex9_*.parquet, every place's `hex9_id` |
| `hex8_id` | every hex8_*.parquet |
| `subzone_c` | every subzone_*.parquet |
| `id` | every per-place parquet (sgp_places_final, micrograph, embeddings) |

## Common app queries

```python
import pandas as pd
ROOT = "/home/azureuser/plexis-sgp-v4"

# 1. Pull a hex's full feature vector
h = pd.read_parquet(f"{ROOT}/hex/hex9_all_features.parquet").query(f"hex9_id == '{cell}'")

# 2. Find similar hexes (semantic + spatial)
from sklearn.neighbors import NearestNeighbors
emb = pd.read_parquet(f"{ROOT}/hex/hex9_embedding_combined_128d.parquet")
nn = NearestNeighbors(n_neighbors=10).fit(emb.iloc[:, 1:].values)

# 3. Pull a place's full context
p = pd.read_parquet(f"{ROOT}/places/sgp_places_final.parquet").query(f"id == '{place_id}'")
mg = pd.read_parquet(f"{ROOT}/places/sgp_places_micrograph.parquet").query(f"id == '{place_id}'")

# 4. Find similar places (combined what + where)
emb = pd.read_parquet(f"{ROOT}/places/place_embedding_combined_128d.parquet")
```

## Schemas

- **Coordinates:** all geo cols are EPSG:4326 (lat/lng); for metric distance use EPSG:3414
- **H3:** hex9 = res 9 (~174m edge), hex8 = res 8 (~461m edge)
- **Subzone:** URA Master Plan 2019 codes (e.g., `AMSZ01` = Ang Mo Kio Town Centre)

## Performance hints

- All parquets are < 100 MB each → memory-map fine
- For random-access lookups, set `hex9_id` / `id` as the index after reading
- Embeddings: combined 128d = 60 MB → fits in RAM trivially
- For nearest-neighbor at scale, use `sklearn.NearestNeighbors` (CPU) or `faiss` (GPU/AVX2)

## Re-deploy from atlas-1

```bash
# On atlas-1 (compute side), publish a new version:
ssh atlas-1 "cd /home/azureuser/plexis-sgp-v4 && python3 publish_checkpoint.py"
ssh atlas-1 "cd /home/azureuser && tar -czf plexis-backups/plexis-sgp-vX.Y.Z.tar.gz \
    --exclude='plexis-sgp-v4/cache' --exclude='__pycache__' plexis-sgp-v4"

# Stream to atlas-deploy:
ssh atlas-1 "cat /home/azureuser/plexis-backups/plexis-sgp-vX.Y.Z.tar.gz" | \
ssh atlas-deploy "cat > /home/azureuser/plexis-sgp-vX.Y.Z.tar.gz && \
                  cd /home/azureuser && tar -xzf plexis-sgp-vX.Y.Z.tar.gz && \
                  rm plexis-sgp-vX.Y.Z.tar.gz"
```

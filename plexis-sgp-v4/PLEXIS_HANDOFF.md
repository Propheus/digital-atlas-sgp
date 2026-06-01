# Plexis SGP v4.8.0 — Handoff / Continuity Brief

**Read this first** if you're picking up the project in a new session. Everything you need to be productive is here.

---

## 1. What Plexis SGP is

A multi-resolution Singapore digital atlas at three spatial scales (hex9 / hex8 / subzone) plus a per-place layer (190K places). Built in 47 reproducible pipeline stages over 11 versions (v4.0.0 → v4.8.0).

Master state at v4.8.0:
- **7,318 hex9 cells** × **558 features** (master bundle `hex/hex9_all_features.parquet`)
- **1,191 hex8 cells** × **548 features**
- **326 subzones** × **388 features**
- **190,591 places** × **27 base cols + 19 micrograph cols**
- **10 embeddings** (5 hex + 5 place; 5 PCA + 5 graph-based)
- **34 datasets** documented in `catalog/`
- **2,189 features** in `catalog/feature_catalog.json`
- **120+ validator checks**, ~96% PASS, 0 FAIL

---

## 2. Where everything lives

### Three servers

| Alias | What | Path |
|---|---|---|
| **atlas-1** (compute) | Source-of-truth for builds. All `build_*.py`, raw data inputs, all parquets. | `/home/azureuser/plexis-sgp-v4/` |
| **atlas-deploy** (deployment) | App-ready mirror. Apps read parquets directly from here. | `/home/azureuser/plexis-sgp-v4/` |
| **rwm-server** (public web) | Public nginx serving the HTML report. | `/var/www/digital-atlas/PLEXIS_v4_FULL_REPORT.html` |

SSH from local:
```bash
ssh atlas-1
ssh atlas-deploy
ssh rwm-server
```

### Local mirror

`/Users/sumanth/propheus-projs/da-sgp/digital-atlas-sgp/`
- `plexis-sgp-v4/` — local copy (some master parquets stale; use atlas-1 or atlas-deploy as source of truth)
- `plexis-backups/` — versioned tar.gz (v4.0.0 → v4.3.0 only — newer ones live on atlas-1)
- `data/` — 2.3 GB of raw inputs (roads.geojson 220 MB, GTFS 320 MB, hex_v10 v3 atlas, etc.)
- `merlion/` + `merlion-app/` — engine source

### Raw data root (on atlas-1)

`/home/azureuser/digital-atlas-sgp/data/`
- `roads/roads.geojson` — 550K-edge OSM road network (used as pedestrian graph)
- `gtfs/singapore-gtfs/` — 8M+ stop_times rows
- `transit/`, `transit_updated/`, `amenities_updated/`, `housing/`, `property/`, `buildings/`, `satellite/`, `osm_pois/`, …
- `hex_v10/` — the prior v3 atlas with embedding zoo (gcn, ae, mae, contrastive, vae, etc.)

---

## 3. How to continue work

### Open the report
```
https://sgp-sim.alchemy-propheus.ai/PLEXIS_v4_FULL_REPORT.html
```
Or local file: `plexis-sgp-v4/PLEXIS_v4_FULL_REPORT.html` (608 KB, fully self-contained).

### Pick up any layer
```python
import pandas as pd, json
ROOT = "/home/azureuser/plexis-sgp-v4"  # on atlas-1 or atlas-deploy

# 1. Atlas summary
manifest = json.load(open(f"{ROOT}/catalog/atlas_manifest.json"))

# 2. Master bundle — every hex9 with 558 features
h9 = pd.read_parquet(f"{ROOT}/hex/hex9_all_features.parquet")

# 3. Places with category + brand + magnet status
places = pd.read_parquet(f"{ROOT}/places/sgp_places_final.parquet")

# 4. Per-place network-walking-distance micrograph
mg = pd.read_parquet(f"{ROOT}/places/sgp_places_micrograph.parquet")

# 5. Embeddings (10 files)
hex_where = pd.read_parquet(f"{ROOT}/hex/hex9_embedding_where_64d.parquet")          # PCA hex 64d
hex_node2vec = pd.read_parquet(f"{ROOT}/hex/hex9_embedding_node2vec_64d.parquet")    # graph topology
hex_gcn = pd.read_parquet(f"{ROOT}/hex/hex9_embedding_gcn_64d.parquet")              # graph-smoothed
hex_super = pd.read_parquet(f"{ROOT}/hex/hex9_embedding_super_128d.parquet")         # graph ensemble
place_what = pd.read_parquet(f"{ROOT}/places/place_embedding_what_64d.parquet")      # PCA place 64d
place_2vec = pd.read_parquet(f"{ROOT}/places/place_embedding_place2vec_64d.parquet") # Word2Vec
place_mega = pd.read_parquet(f"{ROOT}/places/place_embedding_mega_256d.parquet")     # full ensemble
```

### Run the full pipeline (atlas-1)
```bash
cd /home/azureuser/plexis-sgp-v4
python3 run_pipeline.py             # all 47 stages from raw data
python3 run_pipeline.py --from 25   # resume from a stage
python3 run_pipeline.py --only 28   # run just one stage
```

### Re-publish a new version
```bash
# 1. Bump version in publish_checkpoint.py
ssh atlas-1 "sed -i 's/VERSION = \"4.8.0\"/VERSION = \"4.9.0\"/' /home/azureuser/plexis-sgp-v4/publish_checkpoint.py"

# 2. Generate checkpoint + tar
ssh atlas-1 "cd /home/azureuser/plexis-sgp-v4 && python3 publish_checkpoint.py && cd /home/azureuser && tar -czf plexis-backups/plexis-sgp-v4.9.0.tar.gz --exclude='plexis-sgp-v4/cache' --exclude='__pycache__' plexis-sgp-v4"

# 3. Stream to atlas-deploy
ssh atlas-1 "cat /home/azureuser/plexis-backups/plexis-sgp-v4.9.0.tar.gz" | ssh atlas-deploy "cat > /home/azureuser/plexis-sgp-v4.9.0.tar.gz && cd /home/azureuser && rm -rf plexis-sgp-v4 && tar -xzf plexis-sgp-v4.9.0.tar.gz && rm plexis-sgp-v4.9.0.tar.gz"
```

---

## 4. Key facts apps must know

### Primary keys
- `hex9_id` — H3 cell index (hex9 scale)
- `hex8_id` — H3 cell index (hex8 scale)
- `subzone_c` — URA Master Plan code (e.g. `AMSZ01`)
- `id` — 12-char place ID (e.g. `c5Wl6sW53JSX`)

### Coordinate systems
- All lat/lng = **EPSG:4326**
- For metric distance (m) = **EPSG:3414** (SVY21)

### Hex resolutions
- hex9 = res 9 (~174m edge, ~0.105 km²)
- hex8 = res 8 (~461m edge, ~0.737 km²)
- A hex8 contains ~7 hex9; `parent_hex8 = h3.cell_to_parent(hex9, 8)`

### Catalogs (apps bootstrap from these)
- `catalog/atlas_manifest.json` — top-level summary
- `catalog/dataset_catalog.json` — 34 datasets with paths + shapes + join keys
- `catalog/feature_catalog.json` — 2,189 features with descriptions + stats
- `catalog/embedding_catalog.json` — 10 embeddings with method + dim + purpose

---

## 5. Layer families (high-level)

| Family | Source | Stage | Cols at hex9 |
|---|---|---|---|
| Population | SingStat dasymetric (HDB units + area) | 3 | 9 |
| Land use | URA Master Plan 2019 (14 buckets) | 4 | 18 |
| Buildings | Overture + HDB authoritative | 2c | 28 |
| Roads | OSM (550K edges, motorway/trunk excluded for ped) | 6/6c | 5 |
| Transit | data.gov.sg + GTFS | 5/5c/23 | 18 |
| Walkability | OSM ped infra | 7w | 11 |
| Satellite | VIIRS night lights + WorldPop | 5b | 8 |
| **Place composition** | 190K places, 24 plexis cats | 7 | 33 |
| **Place comp V2** | 55 finer pc2_* cats | 24 | 59 |
| **HDB resale** | 227K txns 2017–2026, town-broadcast | 7p | 9 |
| **Schools** | 337 MOE, 1km/2km catchments | 7s | 12 |
| **Amenities extra** | tourist+hawker+CHAS+preschool+silver | 9 | 12 |
| **Spatial rings** | k=1 + k=2 grid_ring averages | 10 | 18 |
| **Pop-weighted** | k=1+k=2 with neighbor_pop weighting | 21 | 125 |
| **Composites** | vibrancy, livability, family, density, etc. | 11 | 6 |
| **Demand pull** | gravity to CBD/mall/hospital/MRT/school/airport | 12 | 7 |
| **Synergy** | 8 cross-feature interactions | 13 | 8 |
| **Saturation/gap** | 9 categories per 1k residents + gap | 14 | 18 |
| **Archetypes** | k-means K=8 (CBD_office, Family_residential, …) | 15 | 3 |
| **Influence** | gravity-decay outbound + inbound + net | 16 | 3 |
| **Micrograph rollup** | per-place mg → hex (mg_<cat>_pressure/support/anchor) | 17 | 75 |
| **Walk scores** | exp(-d/400m) per amenity | 18 | 10 |
| **OSM POIs** | amenities/leisure/shops/tourism counts | 19 | 4 |
| **Land cover** | ESA WorldCover 2021 (built/tree/water/grass) | 20 | 6 |
| **Traffic signals** | LTA 44,917 signals (overhead/ground/ped/RAG/...) | 22 | 9 |
| **GTFS multi-window** | am/midday/pm/night headways + departures | 23 | 12 |
| **LTA PV taps** | 73M weekday tap-ins by window | 25 | 13 |
| **LTA dynamic** | 2,592 carparks + 56,785 speed bands | 26 | 6 |

---

## 6. Embedding architecture

```
hex9 (5 embeddings):
  where_64d         PCA(545 hex features) → 84.3% var          [PCA-based]
  node2vec_64d      Word2Vec on H3 grid_ring random walks      [graph]
  gcn_64d           A_sym × A_sym × X then PCA-64 → 96.6% var  [graph]
  combined_128d     PCA-style concat                            [PCA-based]
  super_128d        concat[node2vec, gcn]                       [graph]

place (5 embeddings):
  what_64d          PCA(137 place features) → 71.0% var         [PCA-based]
  place2vec_64d     Word2Vec on hex co-occurrence sentences     [graph]
  combined_128d     PCA-style concat with hex's where           [PCA-based]
  super_128d        concat[place2vec, what_pca]                 [graph + PCA]
  mega_256d         concat[place2vec, what, hex_gcn, hex_where] [full ensemble]
```

Test results: 17/17 PCA tests PASS · 8/12 graph tests PASS (4 WARNs are informative — place2vec captures co-location, not category, by design).

---

## 7. Apps using or could use this atlas

### Currently consumes v4 atlas (deployed at `atlas-deploy:/home/azureuser/plexis-sgp-v4/`)
None yet wired (atlas was just deployed). Apps would need to be updated.

### Existing apps on atlas-deploy (running, not yet using v4 atlas)
- **atlas-sgp-demo** (port 27090) — static HTML/JS demo
- **atlas-nyc-demo** (port 29090) — same shape, NYC version
- **hex-adequacy-app** (port 16087) — React + Python backend
- **place-lens** (port 29091) — Streamlit dashboard
- **report-ingestion** (port 8080) — FastAPI service

### Existing on atlas-1 (Merlion)
- **merlion-api** (port 18700) — FastAPI orchestrator
- **merlion-ui** (port 18701) — Next.js frontend
- 3-layer engine: Intent (rule-based + Claude Sonnet) → Use Cases → Models (stubbed in v0.1)
- Source: `/home/azureuser/digital-atlas-sgp/merlion/` + `merlion-app/`

---

## 8. Skipped / blocked layers (not in atlas)

| Family | Why skipped | What's needed to add |
|---|---|---|
| Private resale prices | `private_resi_transactions.csv` mislabelled — content is HDB, not URA | Scrape URA private resale data |
| MRT time-of-day taps | PT_CODE for trains is slash-separated at interchanges (NS1/EW24/CC22). Splitting evenly drops accuracy. | Build a proper interchange-aware code resolver |
| Some legacy v3 cols | ~50 v3-specific column splits and deprecated features | Probably not worth chasing |

---

## 9. Versioned tar backups

| Version | atlas-1 | local |
|---|---|---|
| v4.0.0 | `plexis-backups/plexis-sgp-v4.0.0.tar.gz` (87 MB) | ✓ |
| v4.0.1 | (90 MB) | ✓ |
| v4.0.2 | (90 MB) | ✓ |
| v4.1.0 | (100 MB) | ✓ |
| v4.2.0 | (102 MB) | ✓ |
| v4.3.0 | (103 MB) | ✓ |
| v4.4.0 | (106 MB) | — |
| v4.5.0 | (107 MB) | — |
| v4.6.0 | (107 MB) | — |
| v4.7.0 | (205 MB — added PCA embeddings) | — |
| v4.8.0 | (525 MB — added graph embeddings) | — |

---

## 10. Quick "where to find X"

| Need | File |
|---|---|
| Full feature list | `catalog/feature_catalog.json` (2,189 features) |
| All datasets | `catalog/dataset_catalog.json` (34 datasets) |
| All embeddings | `catalog/embedding_catalog.json` (10 embeddings) |
| Atlas summary | `catalog/atlas_manifest.json` |
| Tabbed report | `PLEXIS_v4_FULL_REPORT.html` (608 KB) |
| Pipeline run log | `logs/pipeline_run.json` |
| Latest version manifest | `CHECKPOINT_v4.8.0.json` |
| Build scripts | `build_*.py` (50 files) |
| Validators | `validate_*.py` (15 files) + `test_*.py` (2 files) |
| Run pipeline | `run_pipeline.py` (47 stages) |
| Deployment guide for apps | `DEPLOYMENT.md` |
| This handoff brief | `PLEXIS_HANDOFF.md` |

---

## 11. Common follow-up tasks (with recipes)

### "Find similar places" service
```python
import pandas as pd
from sklearn.neighbors import NearestNeighbors
mega = pd.read_parquet("places/place_embedding_mega_256d.parquet")
nn = NearestNeighbors(n_neighbors=20).fit(mega.iloc[:,1:].values)
# Now: nn.kneighbors(query_vec)
```

### "Hex similarity / clustering"
```python
super_emb = pd.read_parquet("hex/hex9_embedding_super_128d.parquet")
# super_128d = concat[node2vec, gcn] — pure graph signal
```

### "Per-place full context"
```python
place_id = "c5Wl6sW53JSX"
place = pd.read_parquet("places/sgp_places_final.parquet").query(f"id == '{place_id}'")
mg    = pd.read_parquet("places/sgp_places_micrograph.parquet").query(f"id == '{place_id}'")
hex_id = place.iloc[0]['hex9_id']
hex_features = pd.read_parquet("hex/hex9_all_features.parquet").query(f"hex9_id == '{hex_id}'")
```

### "Filter places in a subzone with high commercial intensity"
```python
h9 = pd.read_parquet("hex/hex9_all_features.parquet")
hot_subzones = h9.query("commercial_intensity > 0.5")["parent_subzone"].unique()
hot_places = pd.read_parquet("places/sgp_places_final.parquet").query(
    "parent_subzone_c.isin(@hot_subzones)"
)
```

---

## 12. If something's wrong

- Pipeline broken → check `logs/pipeline_run.json` on atlas-1 for stage status
- Validator FAIL → see `hex/<layer>_validation.json` files for details
- Embedding off → re-run `test_embeddings_full.py` and `test_graph_embeddings.py`
- Stale parquet → re-run the layer's `build_*.py` then `build_all_features.py` to refresh master bundle

---

**Atlas state at handoff: v4.8.0 · 47 stages · 10 embeddings · 558 hex9 cols · 190K places · 0 FAIL validators · deployed on atlas-1 + atlas-deploy · public report at https://sgp-sim.alchemy-propheus.ai/PLEXIS_v4_FULL_REPORT.html**

# Plexis — SGP Urban Knowledge Graph + Embeddings

## Quick start

```python
import numpy as np
import pandas as pd

# Load embeddings
emb = np.load("plexis_v6_embeddings.npz", allow_pickle=True)
place_ids   = emb['place_ids']        # (174,711,) string IDs
place_emb   = emb['place_embeds']     # (174,711, 256) full embedding
place_comm  = emb['place_commercial'] # (174,711, 128) commercial head only
hex8_ids    = emb['hex8_ids']         # (1,191,) H3 res-8 IDs
hex8_emb    = emb['hex8_embeds']      # (1,191, 256) full embedding

# Load features (for combining with embeddings)
pl = pd.read_parquet("../places_consolidated/sgp_places_featured.parquet")  # 174,711 × 114
h8 = pd.read_parquet("../hex_v10/hex8_final.parquet")                       # 1,191 × 637
h9 = pd.read_parquet("../hex_v10/hex9_final.parquet")                       # 7,318 × 612

# Load graph
trips = pd.read_parquet("plexis_triplets_v2.parquet")  # 1,485,547 edges × 39 relations

# Similarity search
from sklearn.metrics.pairwise import cosine_similarity
pid_idx = {pid: i for i, pid in enumerate(place_ids)}
target = pid_idx["some_place_id"]
sims = cosine_similarity(place_emb[target:target+1], place_emb)[0]
top10 = np.argsort(-sims)[1:11]  # skip self
```

---

## What's in this directory

| File | Size | Contents |
|---|---|---|
| `plexis_v6_embeddings.npz` | 240 MB | **Production embeddings** — 256d per node (v6, GAT-R-GCN) |
| `plexis_v6_model.pt` | 1.5 MB | Trained PyTorch model weights |
| `plexis_v6_best.pt` | 1.5 MB | Best checkpoint (early stopping) |
| `plexis_triplets_v2.parquet` | 12 MB | Graph: 1,485,547 edges, 39 relation types |
| `plexis_triplets.parquet` | 12 MB | Graph v1: 1,452,579 edges, 21 relations (original) |
| `plexis_summary.json` | 1 KB | Graph v1 metadata |

---

## Embedding specification

### Arrays in `plexis_v6_embeddings.npz`

| Key | Shape | Type | Description |
|---|---|---|---|
| `place_ids` | (174,711,) | string | Place IDs matching sgp_places_featured.parquet |
| `place_embeds` | (174,711, 256) | float32 | Full embedding (128d spatial + 128d commercial) |
| `place_commercial` | (174,711, 128) | float32 | Commercial head only — use for category-aware search |
| `hex8_ids` | (1,191,) | string | H3 res-8 hex IDs matching hex8_final.parquet |
| `hex8_embeds` | (1,191, 256) | float32 | Full hex-8 embedding |

### Embedding structure

```
256d full embedding = [spatial_128d | commercial_128d]

spatial_128d  → encodes WHERE: walkability, population, ecosystem, transit reach
commercial_128d → encodes WHAT: category, competition, demand match, synergy
```

Use `place_embeds` (256d) for general similarity. Use `place_commercial` (128d) for same-category retrieval.

### How to join with features

```python
# Place embedding → feature lookup
pid_to_idx = {pid: i for i, pid in enumerate(place_ids)}
pid = "some_place_id"
embedding = place_emb[pid_to_idx[pid]]     # 256d
features = pl[pl['place_id'] == pid].iloc[0]  # 114 features

# Hex embedding → feature lookup
h8_to_idx = {hid: i for i, hid in enumerate(hex8_ids)}
hid = "886520d907fffff"
embedding = hex8_emb[h8_to_idx[hid]]       # 256d
features = h8.loc[hid]                      # 637 features

# Place → its hex embedding (cross-entity)
place_hex = pl[pl['place_id'] == pid].iloc[0]['h3_res8']
hex_embedding = hex8_emb[h8_to_idx[place_hex]]
```

---

## How it was built

### Model: GAT-R-GCN v6

```
Architecture:
  Input: 64d PCA (32d place features + 32d hex features, raw, no transform)
  4 × GAT-R-GCN layers (4-head attention, 192d hidden)
  Spatial head: 128d
  Commercial head: 128d
  Category classifier: 128d → 24 classes
  Feature regressor: 192d → 15 targets
  Total parameters: 364,711

Training:
  200 epochs, cosine annealing LR (0.001 → 0.00001)
  Early stopping (patience=30, best at loss=0.3739)
  Loss: 0.10×link + 0.15×contrastive + 0.35×category + 0.40×regression
  15 regression targets:
    competitors_200m, anchor_score, demand_context_score, transit_score,
    survivability_index, complementary_diversity, total_places_300m,
    pull_office, pull_residential, pull_transit, nwalk_mrt_score,
    nwalk_bus_score, catchment_pop, catchment_elderly, context_score
```

### Graph: Plexis v2

```
Nodes: 195,756 (174K places + 7.3K hex-9 + 1.2K hex-8 + 326 subzones + 5.4K transit + amenities)
Edges: 1,485,547
Relation types: 39 (8 families)

Edge families:
  Commercial (941K):  COMPETES_WITH, SYNERGIZES_WITH, SUBSTITUTES_FOR, EXIT_FRONTAGE, VOID_DECK_OF
  Hierarchy (364K):   LOCATED_IN, IS_A, PARENT_OF, PART_OF
  Anchor (121K):      ANCHORED_BY, WALK_CATCHMENT, SERVES
  Spatial (28K):      ADJACENT_TO, N/S/E/W_OF, ROAD_CONNECTED, COASTAL
  Structure (11K):    SAME_CLUSTER, LU_TRANSITION, DEVELOPMENT_FRONT
  Gradient (9K):      COMMERCIAL/HEIGHT/DENSITY/PRICE gradients
  Transit (6K):       CONNECTS_TO, FEEDS_INTO, SAME_CORRIDOR, EXPRESSWAY
  Supply (5K):        UNDERSUPPLIED, OVERSUPPLIED, DEMAND_LEAKS_TO, COMPARABLE_TO
```

### Feature input

```
Place features (114d, from sgp_places_featured.parquet):
  Competition: competitors_200m/500m, nearest_competitor, market_share, substitution_risk
  Complementary: diversity, total_300m, fnb/retail, score
  Anchor: 14 types (MRT, bus, hawker, clinic, park, hotel, school, library, sports...)
  Demand: 6 pulls + total_pop + demand_context
  Synergy: 10 target-category-only scores
  Transit: network walk, GTFS headway, transit_score
  Supply-demand: saturation, demand_match, survivability_index

Hex-8 features (637d, from hex8_final.parquet):
  Demographics (18), dwelling types (12), built environment (16), land use (12),
  transit (18), GTFS (8), walkability (26), amenities (16), place composition (79),
  demand pull (12), synergy (20), saturation (13), satellite (12),
  archetypes (15), micrograph (156), spatial context (123), LTA dynamic (10), property (2)

Both compressed to 32d via PCA (no transform — raw features proven better than log).
```

---

## Accuracy (v6 production)

### Category classification: 78.1%
The 128d commercial embedding alone predicts which of 24 business categories a place belongs to.

### R² — what the 256d embedding captures

| Feature | R² | Source level | What it means |
|---|---|---|---|
| pull_residential | 0.938 | Place | 94% of residential demand captured |
| walkability | 0.921 | Hex | 92% of walkability encoded |
| pull_residential | 0.920 | Hex | 92% at neighborhood level too |
| anchor_score | 0.909 | Place | 91% of anchor proximity |
| demand_context | 0.907 | Place | 91% of demand quality |
| ecosystem | 0.854 | Hex | 85% of daily-needs completeness |
| pull_office | 0.844 | Place | 84% of office demand |
| population | 0.834 | Hex | 83% of population density |
| competitors | 0.803 | Place | 80% of competitive landscape |
| context_score | 0.784 | Place | 78% of overall context quality |
| diversity | 0.777 | Place | 78% of commercial diversity |
| pull_office | 0.720 | Hex | 72% at neighborhood level |
| transit_taps | 0.697 | Hex | 70% of transit usage |
| nwalk_mrt | 0.679 | Place | 68% of MRT network walk |
| transit_score | 0.671 | Place | 67% of transit access |
| survivability | 0.513 | Place | 51% of viability (hardest — supply-side) |

### Other metrics
- P@5 same-category retrieval: 0.104
- Link prediction Hits@10: 8.7%
- Archetype NMI: 0.389

---

## Common operations

### Find similar places
```python
target_idx = pid_to_idx["some_place_id"]
sims = cosine_similarity(place_emb[target_idx:target_idx+1], place_emb)[0]
top = np.argsort(-sims)[1:11]
for i in top:
    print(f"sim={sims[i]:.3f}  {place_ids[i]}")
```

### Find similar neighborhoods
```python
target_idx = h8_to_idx["886520d907fffff"]
sims = cosine_similarity(hex8_emb[target_idx:target_idx+1], hex8_emb)[0]
```

### Brand expansion (find hex matching brand profile but brand absent)
```python
brand_places = pl[pl['name'].str.contains("Starbucks", case=False)]
brand_idx = [pid_to_idx[p] for p in brand_places['place_id'] if p in pid_to_idx]
centroid = place_emb[brand_idx].mean(axis=0, keepdims=True)
hex_sims = cosine_similarity(centroid, hex8_emb)[0]
# Filter out hexes where brand already exists
brand_hexes = set(brand_places['h3_res8'])
candidates = [(hex8_ids[i], hex_sims[i]) for i in np.argsort(-hex_sims) if hex8_ids[i] not in brand_hexes]
```

### Same-category retrieval (use commercial head)
```python
sims = cosine_similarity(place_comm[target_idx:target_idx+1], place_comm)[0]
```

### Anomaly detection (place vs hex mismatch)
```python
place_hex = pl.iloc[0]['h3_res8']
sim = cosine_similarity(place_emb[0:1], hex8_emb[h8_to_idx[place_hex]:h8_to_idx[place_hex]+1])[0][0]
# Low sim = structural misfit
```

### Graph traversal (edges from a node)
```python
node = "some_place_id"
edges = trips[(trips['head'] == node) | (trips['tail'] == node)]
by_type = edges.groupby('relation').size()
```

---

## Data sources (20)

The embeddings encode information from:
Overture Maps (175K places), Overture Buildings (377K), LTA stations (275), LTA bus stops (5,177),
LTA ridership (12.3M taps/day), GTFS 2026 (231K trips), OSM roads (551K segments),
SingStat population (5.98M), HDB resale (227K transactions), URA Master Plan (113K parcels),
VIIRS nightlights, WorldPop, WorldCover, LTA DataMall live API (taxi, carpark, speed, bus routes),
government amenity datasets (hawkers, clinics, parks, schools, hotels), OSM POIs (52K).

---

## Version history

| Version | Embed dim | Category acc | Best hex R² | Best place R² | Key change |
|---|---|---|---|---|---|
| v1 | 128d | N/A | walk 0.88 | anchor 0.71 | Baseline |
| v2 | 128d | N/A | walk 0.88 | anchor 0.71 | + edge weights + contrastive |
| v3 | 128d | 69.8% | walk 0.88 | anchor 0.91 | + multi-task (classification + regression) |
| v4 | 128d | 69.1% | res_pull 0.89 | anchor 0.91 | + spatial edges (39 relations) |
| v5 | 128d | 63.3% | walk 0.90 | anchor 0.88 | Loss rebalance (didn't help) |
| **v6** | **256d** | **78.1%** | **walk 0.92** | **res_pull 0.94** | **GAT + 256d + 15 targets + 200 epochs** |

---

*Plexis v6 — Production — 2026-04-21*

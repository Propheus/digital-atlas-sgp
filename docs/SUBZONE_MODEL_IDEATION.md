# Digital Atlas SGP — Subzone Structure Model Ideation

**Date:** 2026-03-26
**Status:** Ideation — not yet implemented

---

## Core Idea

Build a **learned representation (embedding) of every subzone** in Singapore that captures its full commercial DNA — demographics, infrastructure, place composition, micrograph structure, and market positioning. Like Word2Vec for neighborhoods.

**Goal:** A 32-64 dimensional vector per subzone that enables:
- **Compare** subzones ("ORSZ02 is similar to DTSZ01")
- **Predict** what would work ("this subzone needs a premium cafe")
- **Simulate** changes ("what happens if a mall opens here")
- **Cluster** into archetypes ("CBD", "heartland hub", "industrial zone", "bedroom community")

---

## Three Layers of Structure

### Layer 1: Region Structure (the subzone itself)

| Signal | Data Source | What It Captures |
|---|---|---|
| Population density | Census 2011-2025 | Residential demand |
| Age distribution | Census by age band | Youth vs elderly demand profiles |
| Dwelling type | HDB / condo / landed | Income proxy, lifestyle |
| HDB resale price | 227K transactions | Purchasing power |
| Land use mix | URA master plan (113K parcels) | Zoning entropy — pure residential vs mixed-use |
| Transit score | MRT + bus + ridership | Accessibility / pass-through traffic |
| Road density | 551K road segments | Car accessibility |
| Building density | 126K footprints | Built-up intensity |
| Amenity mix | Schools, hawkers, clinics, parks | Public infrastructure quality |

### Layer 2: Place Structure (commercial ecosystem)

| Signal | Data Source | What It Captures |
|---|---|---|
| Place count by category | 174K places × 24 categories | Commercial composition |
| Place count by sub-type | 3,034 place types | Fine-grained commercial mix |
| Price tier distribution | Luxury/Premium/Mid/Value/Budget | Market positioning |
| Brand density | 1,753 brands × locations | Chain penetration vs independent |
| Category concentration | Herfindahl index | Specialization vs diversity |
| Co-location patterns | PMI pairs | What goes together |
| Vacancy signals | ACRA cessations by area | Business health |
| Survival rates | ACRA registration dates | Location viability |

### Layer 3: Micrograph Structure (spatial relationships)

| Signal | Data Source | What It Captures |
|---|---|---|
| Context vectors | 42K micrographs | What drives each place (transit/competitor/complementary/demand) |
| Anchor network | Avg anchors per place, tier distribution | Commercial fabric connectivity |
| Competitive pressure | T2 density per place | Saturation level |
| Complementary density | T3 density per place | Synergy potential |
| Transit dependency | T1 weight in context vector | MRT-driven vs walk-in economy |
| Demand diversity | T4 variety | Demand source breadth |
| Walk-time distribution | Avg walk time to anchors | Pedestrian accessibility |
| Density band | Hyperdense / dense / moderate / sparse | Urban intensity class |

---

## Model Architecture Options

### Option A: Autoencoder (unsupervised)

```
Raw features (350 dims) → Encoder (350 → 128 → 64 → 32) → Latent embedding (32 dims)
                        → Decoder (32 → 64 → 128 → 350) → Reconstruction
```

- Feature vector = 202 existing features + ~150 new micrograph/tier/ACRA features
- Bottleneck forces learning what matters
- Simple, fast to train on 328 subzones

### Option B: Contrastive Embedding (semi-supervised)

- Positive pairs: Same planning area, similar category distributions
- Negative pairs: Different region, very different profiles
- Loss: Contrastive (SimCLR-style) on feature vectors
- Gives more meaningful similarity comparisons

### Option C: Graph Neural Network (structural)

- Nodes = 328 subzones
- Edges = adjacency (shared boundary) + transit connectivity (MRT links)
- Node features = 350-dim feature vector
- Edge features = travel time, shared transit lines
- GNN (GraphSAGE) learns embeddings capturing neighborhood context
- "Subzone next to Orchard inherits premium signal"

### Option D: Multi-Modal Transformer (ambitious)

| Modality | Input | Encoder |
|---|---|---|
| Demographics | Population table (age × gender × dwelling) | MLP |
| Places | Bag of (category, type, brand, tier) tuples | Set transformer |
| Micrographs | Bag of context vectors | Mean pooling + MLP |
| Transit | Graph of connected stations + ridership | Graph encoder |
| Land use | Spatial grid of zoning codes | CNN |
| Time series | Population trend 2011-2025 | 1D convolution |

Cross-attention → fused 128-dim embedding.

---

## Recommended Approach: A + B Hybrid

**Phase 1:** Expand feature matrix 202 → ~350 features:
- Micrograph aggregates (mean context vector, anchor counts, competitive pressure per category)
- Price tier distribution (% luxury/premium/mid/value/budget per subzone)
- ACRA survival rates (avg business age, churn rate)
- Category Herfindahl index, brand penetration rate

**Phase 2:** Train autoencoder (350 → 64 → 32) for base embeddings.

**Phase 3:** Fine-tune with contrastive pairs.

**Phase 4:** Use embeddings for downstream tasks.

---

## What This Unlocks

### Gap Analyzer
- Embedding predicts "expected" place counts per category per tier
- Gap = expected - actual
- "BMSZ01 embedding is similar to AMSZ01 but has 40% fewer cafes → opportunity"

### What-If Simulator
- Recompute feature vector with proposed change
- Project through encoder → new embedding
- "After adding 3 premium cafes, this subzone moves toward Orchard → signals premium viability"

### Data Explorer
- 328 subzones in 2D (UMAP of embeddings)
- Color by archetype cluster (CBD, heartland, industrial, suburban, tourist)
- Click to see full profile, drag to compare

### Comp Set Generator
- "Find 10 most similar subzones to ORSZ02 for benchmarking"
- Also works at place level: "Find 10 locations similar to Starbucks ION Orchard"

---

## Data Available for Building This

| Data | Records | Status |
|---|---|---|
| Places (consolidated v2) | 174,711 | Ready |
| Subzone features (202 dims) | 332 | Ready |
| Micrographs (12 categories) | 42,603 | Ready (needs rebuild on 174K) |
| ACRA business registry | 2,076,437 | On server, not integrated |
| HDB resale prices | 227,207 | On server, not aggregated |
| Private property transactions | 287,196 | On server, not aggregated |
| Population time series (2011-2025) | 315K+ rows | On server |
| Co-location PMI graph | Ready | Ready |
| Subzone adjacency graph | Ready | Ready |
| Transit connectivity graph | Ready | Ready |

---

## Open Questions

1. **Subzone-level vs place-level?** Subzone (328 embeddings) is faster, powers Gap Analyzer. Place-level (174K embeddings) is richer, powers site selection. Or both?
2. **How to handle temporal?** Population trends 2011-2025 are available. Include as time-series features or just use latest snapshot?
3. **Footfall integration?** If we get LTA ridership data, it becomes a powerful signal. Design the model to accommodate it later.
4. **Transfer to other cities?** If the model architecture is city-agnostic, it could be applied to NYC (already have data), Chicago, LA, SF.

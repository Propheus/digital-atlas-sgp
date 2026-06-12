# Urban Knowledge Graph Layer — Ideation
## Adding structured relationships to the SGP Digital Atlas

**Date:** 2026-04-21  
**Status:** Ideation — no code  
**Inspiration:** UUKG (NeurIPS 2023) — Unified Urban Knowledge Graph  
**Core thesis:** Flat features answer WHAT. The graph answers WHY and WHAT IF.

---

## 1. Why a Graph Layer

The atlas today is a spreadsheet. Every entity has a row, every feature a column. Powerful for querying, blind to connections.

When you ask "why is this cafe successful?", the feature vector says "high pull_office, low competition, near MRT." But it can't say "this cafe succeeds because the MRT exit funnels 50K people past it daily, 15 office towers within 300m generate lunch demand, and the hawker centre across the street creates a food-destination cluster that draws people who then discover the cafe."

That's a graph story — a chain of typed relationships that explains causality, not just correlation.

---

## 2. What UUKG Does (and its limits)

**UUKG** (NeurIPS 2023, HKUST): Encodes urban entities (POIs, roads, junctions, administrative areas) as nodes with spatial/hierarchical relations as edges. Trains TransE/RotH embeddings. Concatenates with task features for downstream prediction (traffic flow, crime).

**What's good:**
- Graph structure captures information that flat features miss
- Multi-scale entity hierarchy (borough → area → POI)
- Embeddings transfer across tasks (one KG, multiple downstream uses)
- Reusable schema across cities (NYC + Chicago use identical schema)

**What's limited:**
- Topology only, no features on nodes (our 114-feature place vector is orders of magnitude richer)
- 13 relation types are all spatial/administrative — no commercial relations (no "competes with", "synergizes with", "generates demand for")
- Embeddings concatenated with features (crude fusion)
- No temporal knowledge in the graph
- No commercial intelligence (traffic + crime, nothing about viability or competition)

---

## 3. Our Graph: ~200K Entities, ~25 Relation Types, ~2-5M Edges

### Entities (already exist — just need to become graph nodes)

| Entity type | Count | Feature dimensions | Source |
|---|---|---|---|
| **Place** | 174,711 | 114 | sgp_places_featured.parquet |
| **Hex-9** | 7,318 | 603 | hex9_final.parquet |
| **Hex-8** | 1,191 | 628 | hex8_final.parquet |
| **Subzone** | 326 | ~449 | subzone_features_full.json |
| **MRT Station** | 231 | ridership, line, interchange | train_stations_mar2026 |
| **Bus Stop** | 5,172 | routes, headway, taps | bus_stops_mar2026 + GTFS |
| **Hawker Centre** | 129 | capacity proxy | hawker_centres.geojson |
| **School** | ~336 | level, catchment | schools data |
| **HDB Block** | 10,431 | floors, units, age | sgp_buildings_fused |
| **Park** | 449 | area, type | parks_nature_reserves |
| **Total** | **~200K** | | |

### Relation types (25 — UUKG's 13 + 12 commercial)

#### Structural (6 types, UUKG-equivalent)

| Relation | From → To | Count est. | What it encodes |
|---|---|---|---|
| `LOCATED_IN` | Place → Hex-9 | 174K | Place containment in hex |
| `PARENT_OF` | Hex-8 → Hex-9 | 7.3K | H3 hierarchy |
| `PART_OF` | Hex-9 → Subzone | 7.3K | Planning alignment |
| `ADJACENT_TO` | Hex-9 ↔ Hex-9 | ~44K | k=1 ring neighbors (6 per hex) |
| `ADJACENT_TO` | Hex-8 ↔ Hex-8 | ~7K | Neighborhood adjacency |
| `SERVES` | MRT/Bus → Hex-9 | ~7K | Transit coverage of hex |

#### Transit network (3 types)

| Relation | From → To | Count est. | What it encodes |
|---|---|---|---|
| `CONNECTS_TO` | MRT ↔ MRT | ~500 | Rail network topology (from rail_lines.geojson) |
| `FEEDS_INTO` | Bus Stop → MRT | ~2K | Feeder bus stops within 300m of MRT |
| `OD_FLOW` | MRT → MRT | ~10K | Actual commute flow (from od_train_202512.zip, top-k per station) |

`OD_FLOW` is gold that UUKG doesn't have. It encodes WHERE people actually GO — "Jurong East connects to Raffles Place" becomes a structural fact the embedding learns.

#### Commercial (8 types — our unique contribution)

| Relation | From → To | Count est. | What it encodes |
|---|---|---|---|
| `COMPETES_WITH` | Place ↔ Place | ~500K | Same category within 500m (from competitors_500m) |
| `SYNERGIZES_WITH` | Place ↔ Place | ~200K | Known synergy pairs within 300m (cafe↔office, gym↔juice bar) |
| `SUBSTITUTES_FOR` | Place → Place | ~100K | Cross-category competition (hawker substitutes for restaurant) |
| `ANCHORED_BY` | Place → Anchor | ~300K | Place benefits from MRT exit, hawker centre, mall, etc. |
| `DEMANDS` | Hex → Category | ~15K | Hex has demand for this category (demand_match > 0.5) |
| `OVERSUPPLIED` | Hex → Category | ~5K | Saturation > 2.0 |
| `UNDERSUPPLIED` | Hex → Category | ~3K | Saturation < 0.5, gap > 0 |
| `COMPARABLE_TO` | Hex ↔ Hex | ~12K | Same archetype + similar feature profile (top-10 per hex) |

#### Demand flow (3 types)

| Relation | From → To | Count est. | What it encodes |
|---|---|---|---|
| `RESIDENTIAL_DEMAND_TO` | Hex (residential) → Hex (commercial) | ~10K | Net demand flow direction (from pull scores) |
| `WORKER_INFLOW` | Hex (residential) → Hex (CBD/industrial) | ~5K | Commute pattern (daytime_intensity > 2) |
| `TOURIST_FLOW` | Hotel hex → Attraction hex | ~2K | Tourist movement (from pull_hotel) |

#### Temporal (edge attributes, not separate types)

Rather than separate AM/PM/night relation types, encode time as edge attributes:
- `CONNECTS_TO` with `{headway_am: 5, headway_pm: 6, headway_night: 15}`
- `OD_FLOW` with `{am_trips: 5000, pm_trips: 3000}`
- `COMPETES_WITH` with `{overlap_hours: "lunch_only"}` vs `{overlap_hours: "all_day"}`

**Total: ~25 relation types, ~2-5M edges.**

---

## 4. What the Graph Enables That Flat Features Can't

### Multi-hop reasoning

"Why is this hex undersupplied for cafes?"

**Flat features:** `saturation_cafe = 0.3, gap_cafe = +15`. Tells you WHAT but not WHY.

**Graph path:** `This_Hex ←[ADJACENT_TO]— MRT_Station ←[OD_FLOW, 50K trips]— CBD_Hex ←[WORKER_INFLOW]— This_Hex`. The workers commute OUT to CBD for coffee. The demand exists but leaks through the transit connection. The fix isn't "open more cafes here" — it's "open a cafe AT the MRT station to intercept commuters."

That reasoning is impossible from a feature vector. It requires traversing the graph.

### Structural similarity beyond feature similarity

Two hexes with identical features (same population, same places) but different graph positions. One is a hub (3 MRT lines, surrounded by commercial hexes). The other is a leaf (end of bus route, surrounded by forest). Their embeddings should differ because their structural roles differ.

### Demand attribution

Currently synergy scores say "this cafe benefits from office pull." But HOW MUCH from which source? The graph attributes:

```
This cafe's demand:
  40% ← Office towers (via SYNERGIZES_WITH, 15 edges)
  25% ← MRT commuters (via ANCHORED_BY MRT, OD_FLOW 50K)
  20% ← Residential (via RESIDENTIAL_DEMAND_TO, 3 hex edges)
  15% ← Hotel tourists (via TOURIST_FLOW, 2 hotel edges)
```

This is demand decomposition through graph attention — weight incoming edges by their contribution.

### Counterfactual reasoning ("what if")

**Remove an edge:** "What if this MRT station closes?" → Recompute embeddings without `CONNECTS_TO` and `FEEDS_INTO` edges. Every place `ANCHORED_BY` that station sees its embedding shift. Most-affected places = most dependent on that edge.

**Add an edge:** "What if we build a new MRT station here?" → Add `CONNECTS_TO` edges. Recompute. Which hexes shift from `UNDERSUPPLIED` to balanced? Which places gain new `ANCHORED_BY` edges?

This is scenario simulation that the current engine can't do.

### Transfer learning across cities

SGP and HKG share the same relation schema (COMPETES_WITH, SYNERGIZES_WITH, ANCHORED_BY, etc.). An R-GCN trained on SGP can be fine-tuned for HKG with minimal data. Structural patterns ("cafes near transit with office synergy perform well") transfer. Specific entities differ but relational patterns are universal.

This is the "universal" in universal representation — not universal features (every city has different demographics) but universal structure (competition, synergy, demand flow work the same way everywhere).

---

## 5. Embedding Architecture

### Option A: Two-tower (UUKG approach, simple)
```
Tower 1: Feature encoder (MLP on 114/603/628-d → 64d)
Tower 2: KG encoder (R-GCN on graph structure → 64d)
Fusion: concatenate → 128d final embedding
```
Simple but the two towers don't communicate.

### Option B: Feature-initialized R-GCN (recommended)
```
Initialize node embeddings with feature vectors
R-GCN message passing over typed edges (3-4 layers)
Output: 128d embedding encoding BOTH features and structure
```
Better: features inform message passing. A place with high `competitors_200m` sends different messages along `COMPETES_WITH` edges than one with low competition.

### Option C: Heterogeneous Graph Transformer (best, expensive)
```
Multi-head attention over typed edges
Feature vectors as node inputs
Edge attributes (distance, headway, flow volume) as attention bias
Output: 128d embedding with interpretable attention weights
```
Attention weights are interpretable: "this place's embedding is 40% from MRT anchor, 30% from office synergy, 20% from residential demand, 10% from competitors."

---

## 6. How This Changes Merlion / Nous

### Today (flat features)
- Receives query → runs model on feature vectors → returns ranked hexes
- No explanation of WHY a hex ranks high
- No way to simulate changes
- No cross-entity reasoning

### With graph layer
- Receives query → traverses graph → returns ranked hexes WITH explanation paths
- "This hex ranks #1 because: 3 MRT connections bring 150K daily commuters, 8 office towers generate lunch demand, but only 2 cafes exist (gap=15)"
- Scenario: "add a station" → modify graph → rerank → show delta
- Cross-city: "find a hex in HKG with same graph structure as Toa Payoh"

---

## 7. How This Changes the MoE Corpus

Instead of generating entity descriptions from flat features, generate from graph traversal:

> "This cafe (entity) LOCATED_IN Toa Payoh Central (hex-8) which is ADJACENT_TO Novena (hex-8). It SYNERGIZES_WITH 15 office buildings within 300m and COMPETES_WITH 9 other cafes. The hex SERVES_DEMAND_OF 32K residents. The nearest transit stop FEEDS_INTO NSL which CONNECTS_TO Raffles Place via OD_FLOW of 50K daily trips..."

The KG provides structured reasoning paths that the MoE can learn from. Grounded spatial reasoning, not free-form description.

---

## 8. Universal Schema (Cross-City)

If we define this schema once:

```
Entities: Place, Hex, Subzone, Region, TransitStop, Road, Building, Amenity
Relations: LOCATED_IN, ADJACENT_TO, COMPETES_WITH, SYNERGIZES_WITH,
           SERVES, ANCHORED_BY, FEEDS_INTO, SUBSTITUTES_FOR,
           COMPARABLE_TO, DEMANDS, OVERSUPPLIED, UNDERSUPPLIED,
           OD_FLOW, RESIDENTIAL_DEMAND_TO, WORKER_INFLOW, TOURIST_FLOW,
           CONNECTS_TO, PARENT_OF, PART_OF
```

...and implement for SGP, the same schema works for:
- **HKG** (already have 147K places × 142 features, TPU boundaries, MTR network)
- **NYC/Chicago** (have in atlas datarepo: 6,809 tracts, 520K places)
- **Jakarta, Dubai, Bangalore** (planned digital atlases)

One graph schema. Multiple city instantiations. Transferable embeddings. That's the universal representation.

---

## 9. Construction Effort

| Step | Effort | Output |
|---|---|---|
| Emit structural triplets (LOCATED_IN, PARENT_OF, ADJACENT_TO, PART_OF) | 2 hours | ~230K edges |
| Emit transit triplets (SERVES, CONNECTS_TO, FEEDS_INTO) | 2 hours | ~10K edges |
| Emit OD_FLOW from od_train matrix | 3 hours | ~10K weighted edges |
| Emit commercial triplets (COMPETES_WITH, SYNERGIZES_WITH, etc.) | 4 hours | ~1M edges from KD-tree results |
| Emit demand/supply triplets (DEMANDS, OVERSUPPLIED, UNDERSUPPLIED) | 2 hours | ~23K edges |
| Emit flow triplets (RESIDENTIAL_DEMAND_TO, WORKER_INFLOW) | 2 hours | ~17K edges |
| Emit COMPARABLE_TO from archetype similarity | 2 hours | ~12K edges |
| Train R-GCN (4 layers, 128d) | 4-8 hours on atlas-1 | 200K × 128d embeddings |
| Integration into Merlion | 2-3 days | Graph-aware handlers |
| **Total** | **~5 days** | **~200K nodes, ~1.3M edges, 128d universal embeddings** |

---

## 10. What NOT to Adopt from UUKG

1. **TransE/RotH** — too simple for our feature-rich graph. Use R-GCN or heterogeneous graph transformer.
2. **Concatenation for fusion** — use attention-based or shared bottleneck.
3. **Their task set** — traffic + crime are academic. Keep our commercial use cases (site selection, gap analysis, etc.).
4. **Feature-free nodes** — UUKG nodes have no features. Ours have 114-628 features each. Initialize embeddings from features.
5. **Their scale** — 236K entities for NYC. We have 200K for SGP alone with richer features.

---

## 11. Architecture Decision: Parallel Layer, Not Replacement

Build the graph as a parallel layer alongside the flat feature stack:

```
┌─────────────────────────────────────┐
│  FLAT FEATURES (current)            │
│  DuckDB queries, <7ms               │
│  Direct: "show me hexes with X"     │
│  ↓                                  │
│  Answers: WHAT                      │
└─────────────────────────────────────┘
        +
┌─────────────────────────────────────┐
│  GRAPH LAYER (new)                  │
│  R-GCN embeddings, graph traversal  │
│  Paths: "why does this hex rank #1" │
│  ↓                                  │
│  Answers: WHY and WHAT IF           │
└─────────────────────────────────────┘
        =
┌─────────────────────────────────────┐
│  COMBINED (product)                 │
│  Feature queries + graph reasoning  │
│  Explainable, simulatable, portable │
└─────────────────────────────────────┘
```

The flat features are fast, validated, and work for DuckDB queries. The graph adds:
1. **Explanation generation** — graph paths explain WHY
2. **Scenario simulation** — edge modification simulates WHAT IF
3. **Universal embeddings** — R-GCN embeddings as a new feature column on every entity
4. **Cross-city transfer** — the schema (not the data) is the portable asset

---

## 12. Comparison: UUKG vs Our Proposed Graph

| Dimension | UUKG | Ours |
|---|---|---|
| Entities | 236K (NYC) | 200K (SGP) |
| Entity types | 8 | 10 |
| Node features | None | 114-628 per node |
| Relation types | 13 (spatial/admin only) | 25 (+ commercial + demand flow) |
| Edges | 930K | 1.3-5M |
| Edge attributes | None | Distance, headway, flow volume, time |
| Embedding model | TransE/RotH | R-GCN or HGT (feature-initialized) |
| Fusion method | Concatenation | Attention-based or integrated |
| Downstream tasks | Traffic, crime | Site selection, gaps, archetypes, comparable, whitespace, 15-min city |
| Commercial relations | None | COMPETES_WITH, SYNERGIZES_WITH, DEMANDS, OVERSUPPLIED, etc. |
| Temporal | Static graph + separate .dyna files | Edge attributes (AM/PM/night) |
| Cities | NYC, Chicago | SGP (+ HKG, NYC, Chicago via same schema) |
| Cross-city transfer | Same schema, no feature transfer | Same schema + transferable structural patterns |

---

*Ideation v1.0 — 2026-04-21*  
*Inspired by UUKG (NeurIPS 2023). Extended with commercial relations, feature-rich nodes, and demand flow edges that the academic work lacks.*  
*Next: emit triplets from existing data, train R-GCN, integrate into Nous/Merlion.*

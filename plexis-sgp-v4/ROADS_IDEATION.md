# Plexis SGP v4 — Road Network: Hex Representation Ideation

**Date:** 2026-04-25
**Status:** Pre-implementation — design choices to make before building
**Source data:** `data/roads/roads.geojson` (550,991 OSM segments, already topologized with `u`/`v` node IDs)

---

## 1. What roads encode (and why this is hard)

A hex is a 2D area; a road network is a 1D graph embedded in that area. There is no single number that captures it. Different downstream questions need different summaries:

| Question downstream | What it needs from roads |
|---|---|
| "Is this hex easy to walk in?" | Sidewalk density, footway %, crossings, pedestrian-accessible % of edges |
| "Is this hex easy to drive in?" | Lane-km of motor-traffic roads, max road class, expressway proximity |
| "How is this hex connected to the rest of SGP?" | Edge degree, node degree, link to expressway, betweenness centrality |
| "What's the urban form?" (Jacobs / mixed-use signal) | Block size, intersection density, % small blocks, gridiness |
| "Where is congestion likely?" | Lane-km × adjacent population × dominant_use, bottleneck nodes |
| "How permeable is this hex for transit?" | Road class diversity, % of roads transit-routes use, signalized intersection density |

**Implication:** roads should produce *several* feature families, not one composite. Each downstream consumer picks what it needs.

---

## 2. The OSM raw data we already have

```
550,991 segments, schema:
  u, v, key, osmid    — graph topology (start node, end node, parallel-edge key)
  name                — road name
  highway             — road class (footway, service, residential, motorway, etc.)
  length              — meters
  oneway              — bool
  lanes               — string (NULL on 68% — sparse)
  maxspeed            — string (NULL on 80% — sparse)
  bridge, tunnel      — flags
```

**Class distribution:**
```
237,627  footway          (43%)  ← pedestrian-only, dominant by count
161,181  service          (29%)  ← driveways, parking aisles, alleys
 57,910  residential      (11%)  ← residential streets
 27,169  cycleway          (5%)
 12,219  primary           (2%)
 11,789  tertiary          (2%)
  9,705  secondary         (2%)
  8,668  unclassified
  5,206  path
  3,877  steps             ← pedestrian only, often inside HDB
  2,873  primary_link
  1,907  trunk
  1,485  motorway_link
  1,458  pedestrian        ← fully pedestrianized streets
  1,405  corridor          ← inside-building corridors
    462  motorway          (0.08%)  ← expressways, AYE/PIE/CTE/ECP
```

Three observations:
1. **Pedestrian infra dominates** (43% footway + 5% cycleway + 0.7% steps + 0.3% pedestrian). Treat walkability as the primary lens.
2. **Expressways are tiny but matter disproportionately** (462 motorway segments = 0.08% but they shape regional connectivity).
3. **Lane/maxspeed sparsity** means we can't reliably compute "vehicle capacity" on most segments. We have to use class-based defaults (e.g. residential=2 lanes default).

---

## 3. Proposed feature families per hex

I'd group features into **6 pillars**. Each is independent so we can ship in any order; each has its own validator.

### Pillar A — Length and density (the basics)

Per hex:
- `road_length_total_m` — clipped to hex polygon
- `road_density_km_per_km2` — total length / hex area
- `road_pedestrian_length_m` — sum of footway + path + cycleway + pedestrian + steps
- `road_vehicular_length_m` — sum of motorway + trunk + primary + secondary + tertiary + residential + service (excludes pedestrian)
- `road_walkable_share` — pedestrian / total (0 = car-only, 1 = ped-only)

Cost: medium (need to clip 550K linestrings to 7,318 hex polygons in EPSG:3414).

### Pillar B — Class composition (typology)

Length per class as fraction of total:
- `road_pct_motorway`, `road_pct_trunk`, `road_pct_primary`, `road_pct_secondary`, `road_pct_tertiary`, `road_pct_residential`, `road_pct_service`, `road_pct_footway`, `road_pct_cycleway`
- `road_class_entropy` — Shannon entropy across classes (high = mixed network, low = monoculture)
- `road_max_class` — categorical: highest road class present (motorway > trunk > primary > … > footway)

Cost: low (once Pillar A is done, just rebucket).

### Pillar C — Topology (graph metrics)

This is the new value proposition. The graph already has `u`/`v` node IDs; we can build a NetworkX (or pandas-edgelist) graph and compute per-hex metrics:

- `road_node_count` — number of OSM nodes inside the hex
- `road_edge_count` — number of edges with at least one endpoint inside
- `intersection_count` — nodes with degree ≥ 3 (vehicle network only — exclude footway-only nodes)
- `intersection_density_per_km2`
- `road_avg_degree` — mean node degree
- `road_dead_ends` — degree-1 nodes inside the hex (cul-de-sacs, end of dead-end driveways)
- `block_count_estimate` — face count of the planar graph clipped to hex (small blocks = walkable urban form per Jacobs)
- `avg_block_size_m2`

**Why this matters:** Jacobs' core finding (already in our paper-replication suite) is that small blocks + high intersection density predict commercial vitality. We want this signal.

Cost: high (planar face computation is expensive; could use a simpler proxy like 1/intersection_density × road_length_per_km2).

### Pillar D — Expressway and arterial proximity

- `dist_motorway_m` — distance from hex centroid to nearest motorway segment
- `dist_motorway_link_m` — distance to nearest expressway entrance/exit
- `motorway_within_500m` — bool (severance / noise penalty)
- `near_expressway_exit` — bool (commercial accessibility bonus)
- `arterial_pct` — share of road length that is primary or trunk

This captures the dual nature of expressways: closer = more accessible by car, but also more severed for pedestrians (expressways are walls).

Cost: low (point-to-line distance via STRtree).

### Pillar E — Walkability infrastructure

- `pedestrian_path_density_km_per_km2` — footway + path + steps + cycleway
- `cycleway_length_m`
- `pcn_length_m` — Park Connector Network (separate file, already counted in Stage 4 as `park_connector_segments`)
- `signalized_crossing_count` — from `data/transit/traffic_signals.geojson` (44,922 signals, includes `ped_*` types)
- `pedestrian_island_score` — does the road network have continuous footway connections, or is it interrupted? (computed as: footway_length / vehicular_length, or as a connectivity ratio)

Cost: low–medium.

### Pillar F — Capacity and traffic load

For vehicular roads only, infer:
- `lane_km` — sum of length × lanes (default lanes per class: motorway=4, trunk=3, primary=3, secondary=2, residential=2, service=1)
- `lane_km_per_km2`
- `bridge_length_m`, `tunnel_length_m` — infrastructure cost / severance
- `oneway_pct` — fraction of vehicular length that is one-way (CBD signal — gridded streets)

If we have time-series traffic data later (LTA speed bands, jam factor):
- `dyn_avg_speed_kmh`, `dyn_jam_pct`, `dyn_pct_jammed` (already exists in V3 atlas — can copy or rebuild)

Cost: low for static; medium for dynamic.

---

## 4. Decision points (need your call)

### 4.1 Topology depth — how far do we go?

| Tier | What it adds | Compute cost | Use cases unlocked |
|---|---|---|---|
| **T1: lengths only** | Pillars A + B + Eβ | 5 min | density, class mix, basic walkability |
| **T2: + topology lite** | + node count, intersection count, avg degree | 15 min | Jacobs intelligence at hex level |
| **T3: + planar faces** | + block_count, avg_block_size | 1–3 hours | full Jacobs replication, urban morphology |
| **T4: + global graph metrics** | + betweenness centrality, accessibility scores | several hours | network-position features for similarity |

T1 is the floor; T3+ is research-grade. **My recommendation: T2 by default, escalate to T3 only if Stage 18 (Plexis-Graph) needs it.**

### 4.2 Pedestrian vs vehicular as separate networks?

Two networks live in this dataset:
- **Pedestrian graph:** footway + path + cycleway + steps + pedestrian + corridor + roads with sidewalks
- **Vehicle graph:** motorway through residential, no footway/path

V3 atlas built two networks (`network walk` vs `network drive`). We have three options:

| Option | Description | Cost | Result |
|---|---|---|---|
| **A. Combined graph** | Treat all edges as walkable (most pedestrians can use service roads / quiet residentials) | 1× | One topology pillar, simpler |
| **B. Two graphs (clean split)** | Pedestrian = ped-only edges; Vehicle = motor-only edges | 2× | Cleaner per-mode metrics, doubles the table |
| **C. Three graphs** | + Active mobility (cycleway + PCN + low-speed roads) for the bicycle network | 3× | Most accurate but most complex |

**Recommendation:** Option B. Pedestrian-vs-vehicle distinction is fundamental enough that downstream (transit access, walkability, congestion) all need it. Active mobility can derive from the combined later if needed.

### 4.3 Severance — do we model it?

Expressways are physical barriers. A hex 200 m from an expressway might be poorly walkable to its mirror hex on the other side, even though their centroid distance is 200 m. Two ways to capture:

- **Implicit:** `dist_motorway_m` + `motorway_within_500m` (Pillar D) lets downstream models learn the severance penalty.
- **Explicit:** compute `severed_from_neighbours` — number of adjacent hex-9s where the network walk distance is > 2× euclidean (means a barrier between).

Explicit severance is a Stage-9-ish feature (it depends on the walk-graph being built). I'd defer.

### 4.4 What about the road network at hex-8?

Roads aggregate cleanly hex-9 → hex-8 by SUM (lengths) and re-derivation (topology metrics shouldn't be summed; they should be re-computed on the hex-8's clipped subgraph). Standard Plexis aggregation rules from §10 of methodology apply:

- `road_length_total_m` — SUM of children
- `intersection_count` — SUM of children
- `road_pct_*` — re-derive from summed lengths (NOT pop-weighted)
- `road_max_class` — MAX (highest class wins)
- `road_class_entropy` — re-derive from re-summed lengths
- `dist_motorway_m` — MIN of children
- `block_count` — re-compute (because blocks straddle hex boundaries)

### 4.5 Should we use the existing V3 walkability features?

V3 atlas already has 26 walkability columns (`walk_*` Euclidean + `nwalk_*` network) per hex. Two paths:

- **Re-derive in Plexis v4** — full ownership, slower (build the walk-graph + compute distances for 7K hexes × 9 amenity types = ~63K shortest paths)
- **Borrow V3 directly** — copy the relevant columns from `data/hex_v10/hex9_final.parquet`; mark them as "borrowed in v4.0, will re-derive in v4.1"

V3's walkability is good (R²=0.88+ in Plexis-Embed). Borrowing it gets us 85% of the value at 5% of the cost. **Recommendation: borrow for v4.0, mark for re-derivation later.**

---

## 5. Suggested staging

| Stage in Plexis | Builds | What's in scope | Wall-clock target |
|---|---|---|---|
| **6a** Roads basic | Pillars A + B | length, density, class composition | 10–15 min |
| **6b** Topology lite | Pillar C (T2 tier) | nodes, intersections, degree | 15–30 min |
| **6c** Walkability infra | Pillars D + E | expressway proximity, ped paths, signalized crossings | 15 min |
| **6d** Vehicle graph | Pillar F static | lane-km, oneway, bridge/tunnel | 10 min |
| (Future) **6e** Walk-graph distances | re-derive `nwalk_*_m` to 9 amenity types | 9 amenities × 7,318 hexes shortest paths | 60–120 min |

Each stage produces its own parquet (`hex9_roads_basic.parquet`, etc.) and validator. They join on `hex9_id`.

The whole road layer adds **~25 columns at hex-9 minimum (T1)**, **~45 at T2**, up to **~80 at full T3 + walkability re-derive**.

---

## 6. Concrete schema proposal (T2, my recommended floor)

```
hex9_roads.parquet  (7,318 × ~45)

  hex9_id

  -- Pillar A: lengths --
  road_length_total_m
  road_pedestrian_length_m
  road_vehicular_length_m
  road_density_km_per_km2
  road_walkable_share

  -- Pillar B: class composition --
  road_pct_motorway, road_pct_trunk, road_pct_primary,
  road_pct_secondary, road_pct_tertiary, road_pct_residential,
  road_pct_service, road_pct_footway, road_pct_cycleway,
  road_pct_other
  road_class_entropy
  road_max_class                          (categorical)

  -- Pillar C: topology lite --
  road_node_count
  road_edge_count
  road_intersection_count
  road_intersection_density_per_km2
  road_avg_node_degree
  road_dead_ends_count

  -- Pillar D: expressway proximity --
  dist_motorway_m
  dist_motorway_link_m
  motorway_within_500m                    (bool)

  -- Pillar E: walkability infra --
  pedestrian_path_density_km_per_km2
  cycleway_length_m
  signalized_crossing_count               (from traffic_signals.geojson)

  -- Pillar F: vehicle capacity --
  lane_km
  lane_km_per_km2
  bridge_length_m
  tunnel_length_m
  oneway_pct
```

---

## 7. What this enables downstream

| Use case | Roads features used |
|---|---|
| Site selection: where to put a cafe | road_pedestrian_length_m, intersection_density, road_class_entropy, dist_motorway_m (negative — too noisy) |
| Walkability score per hex | road_walkable_share, pedestrian_path_density, signalized_crossing_count, motorway_within_500m (penalty) |
| Congestion prediction | lane_km, road_max_class, oneway_pct, intersection_density (model congestion = capacity vs demand) |
| Jacobs vitality replication | small `avg_block_size_m2` × `road_intersection_density` × `road_class_entropy` → predicts place_count |
| Plexis-Graph "ROAD_CONNECTED" relation | u/v nodes shared between hexes (existing in V3, ports cleanly) |
| Severance ("WALK_CATCHMENT" relation) | nwalk distances (deferred to walk-graph stage) |

---

## 8. Recommendation summary

**Build T2 + Pillars A/B/C/D/E now (Stages 6a–c).** Defer T3 (planar faces) and the full walk-graph distance re-derivation to a later sub-stage that bundles into Stage 9 (demand pull).

**Borrow V3 walkability columns** (`nwalk_*_m`) directly — mark them as "borrowed" in the schema, plan a re-derivation pass later if the rest of v4 outgrows V3.

Estimated v4 effort to ship Stage 6 a/b/c: **~1 hour wall-clock on atlas-1**, ~45 hex columns added, fits in our existing pipeline runner.

---

## 9. Motorway / highway detection in detail

A single `dist_motorway_m` collapses three different things into one number. Better to split:

### 9.1 Three relationships a hex can have to a major road

```
   Through       Adjacent       Severed-by-near
                                                
  ╔══════╗      ╔══════╗       ╔══════╗
  ║      ║   ▶▶▶║▶▶▶▶▶▶║▶▶▶ ▶▶▶║▶▶▶▶▶▶║▶▶▶
  ║▶▶▶▶▶▶║▶     ║      ║       ║      ║
  ╚══════╝      ╚══════╝       ╚══════╝
                                  ▲
                                 100m gap
```

- **Through** — segment polygon-intersects the hex. Highest impact: severance + noise + accessibility from on-ramps.
- **Adjacent** — segment touches hex boundary (e.g. expressway running along the edge). Severance penalty without through-traffic mess.
- **Severed-by-near** — segment is < 200 m from hex centroid but doesn't enter. Major barrier between this hex and its neighbour on the other side.

We should encode all three. None alone tells the full story.

### 9.2 Proposed motorway/arterial features (per hierarchy class)

For each road class in {motorway, trunk, primary}:

| Feature | Meaning |
|---|---|
| `road_{class}_in_hex_m` | length of class segments INSIDE the hex (= "through") |
| `road_{class}_on_boundary_m` | length running along the hex polygon boundary (= "adjacent") — proxy: segments within 30 m of hex border that don't penetrate |
| `dist_{class}_m` | shortest distance from hex centroid to nearest segment of class |
| `{class}_within_200m` | bool — barrier-near flag |
| `{class}_within_500m` | bool — accessibility flag |

Plus aggregate signals:
- `dist_expressway_m` = min over {motorway, trunk, motorway_link, trunk_link}
- `expressway_severance_score` ∈ [0, 1] — composite: high if through OR within 200m, low otherwise
- `dist_expressway_exit_m` — distance to nearest motorway_link / trunk_link (= on-ramp/off-ramp = car accessibility)
- `near_expressway_exit_400m` — bool (commercial accessibility bonus, used by McDonald's, Shell, FairPrice for drive-through siting)

### 9.3 Why expressway exit matters separately

In SGP a motorway segment passing through a hex is mostly bad (severance, noise, no pedestrian access). But the *exit* is the opposite — it's where you actually get on/off the expressway. A petrol station / fast food / supermarket benefits from being within 400 m of an exit. The 1,485 motorway_link + 797 trunk_link segments encode exits.

`dist_expressway_m` and `dist_expressway_exit_m` are two different signals. We need both.

### 9.4 Named expressway flag (optional)

The 462 motorway segments belong to ~10 named expressways: AYE, ECP, PIE, KPE, CTE, BKE, SLE, TPE, MCE, KJE, AHE. We could emit `near_expressway_PIE = bool` etc. so a downstream model knows "PIE corridor" structure. **Cost: trivial.** **Value: medium** — only matters for SGP-specific narrative analytics. Defer unless asked.

### 9.5 Hierarchical "max class through" feature

A single categorical that summarises road exposure:

```
road_max_class_through  ∈ {motorway, trunk, primary, secondary, tertiary, residential, service, footway, none}
```

Set to the highest class that intersects the hex polygon. Cheap; useful as a quick filter (e.g., "all hexes with motorway running through" = severance candidates).

---

## 10. Parking — what we have and what to feature

Parking is an underrated signal: it predicts car-dependency, retail viability (mall vs HDB centre), and commercial intensity. Inventory:

### 10.1 Available data

| Source | Records | Granularity | Use |
|---|---|---|---|
| **OSM `amenity=parking`** | 3,156 polygons + points | per-lot | Static — best for inventory |
| **OSM `amenity=parking_entrance`** | 1,908 points | entrance | Counts capture access points |
| **OSM `amenity=parking_space`** | 779 polygons | individual stall | Edge cases (street-level stalls) |
| **OSM `amenity=bicycle_parking`** | 646 points | bike-rack | Active mobility signal |
| **HDB `hdb_property_info.csv`** | **1,114 blocks** with `multistorey_carpark=Y` | per-block flag | HDB MSCP detection (authoritative) |
| **`hdb_property_info.csv`** | **3,109 blocks** with `miscellaneous=Y` (often surface carparks) | per-block flag | Surface lot detection |
| **LTA carpark snapshot (live)** | 5 carparks (Suntec etc.) — only LTA-managed ones | timestamped availability | Too sparse for static features; useful only for dynamic |
| **`carpark_availability.json` (data.gov.sg)** | LTA odata, 5 records | live availability | Same — too narrow |
| **HDB carpark dataset (data.gov.sg)** | ~2,000 HDB carparks (separate dataset, NOT yet on atlas-1) | per-carpark with capacity | Would need download |

### 10.2 Two-tier parking strategy

**Tier 1 — Static inventory (ship now):**

For each hex compute from OSM + HDB:

| Feature | Source | Meaning |
|---|---|---|
| `parking_lot_count` | OSM amenity=parking polygons + points in hex | Number of distinct lots |
| `parking_lot_area_m2` | OSM polygon area | Total parking footprint |
| `parking_entrance_count` | OSM parking_entrance | Access points (predicts car-traffic generators) |
| `parking_space_count` | OSM parking_space stalls | Estimated stall count (sparse, mostly underestimates) |
| `bicycle_parking_count` | OSM bicycle_parking | Active mobility signal |
| `hdb_mscp_count` | HDB authoritative `multistorey_carpark=Y` | Multi-storey HDB carparks (authoritative) |
| `hdb_surface_carpark_count` | HDB authoritative `miscellaneous=Y` (with regex filter on street name to exclude non-parking misc) | Surface HDB lots |
| `parking_density_per_km2` | derived | density |
| `parking_footprint_share` | parking_area / hex_area | fraction of hex devoted to parking |
| `is_parking_dominant` | bool — `parking_footprint_share` > 0.15 | flag for "parking heavy" hexes |

Ten columns total. ~5 min to build.

**Tier 2 — Capacity estimation (later):**

OSM rarely reports capacity. We can ESTIMATE:
- HDB MSCP block: typical 200–400 lots → use 300 as default
- HDB surface block: typical 50–100 → use 75
- OSM parking polygon: 25 m² per stall → derive `est_stalls = area_m2 / 25`

This gives `parking_estimated_capacity` per hex. Useful but lossy — flag it as estimated.

**Tier 3 — Dynamic load (Stage 14c, later):**

When live LTA carpark API returns to working state (currently sparse), compute `dyn_carpark_utilization_pct` per hex per timestamp. V3 atlas had this; can port.

### 10.3 What parking features unlock

| Use case | Parking feature |
|---|---|
| Car-dependent retail siting (FairPrice, IKEA, Decathlon) | high `parking_footprint_share`, `near_expressway_exit_400m` |
| HDB-anchored convenience | `hdb_mscp_count > 0`, `hdb_surface_carpark_count > 0` |
| Walkability penalty | high `parking_footprint_share` predicts low `road_walkable_share` |
| Footfall proxy for mall hexes | `parking_lot_count + parking_entrance_count` high → mall |
| Active mobility / bike-friendliness | `bicycle_parking_count` |
| Severance / land-use waste flag | `is_parking_dominant=True` |

### 10.4 Schema add-on

```
hex9_parking.parquet  (7,318 × ~12)
  hex9_id
  parking_lot_count, parking_lot_area_m2,
  parking_entrance_count, parking_space_count,
  bicycle_parking_count,
  hdb_mscp_count, hdb_surface_carpark_count,
  parking_density_per_km2, parking_footprint_share,
  is_parking_dominant,
  parking_estimated_capacity      (optional, Tier 2)
```

Could also fold these into the buildings table since some are already there (`bldg_transport_count` includes carparks). My preference: keep parking as its own pillar so we can tune/ablate independently.

---

## 11. Updated staging recommendation

| Stage | Builds | Wall-clock | Cols added |
|---|---|---|---|
| **6a** Roads basic | Pillars A + B | 10–15 min | ~15 |
| **6b** Topology lite | Pillar C (T2) | 15–30 min | ~6 |
| **6c** Highway+motorway proximity | §9 features (through/adjacent/severance/exits) | 10–15 min | ~10 |
| **6d** Walkability infra | Pillar E (signalized crossings, ped paths) | 10–15 min | ~6 |
| **6e** Parking | §10 Tier 1 | 5–10 min | ~10 |
| **6f** Vehicle capacity | Pillar F static (lane-km, oneway, bridge) | 10 min | ~6 |
| (Future) **6g** Walk-graph distances | nwalk_*_m to 9 amenities | 60–120 min | ~26 (borrow V3 first) |

**Total at floor (6a-6e + 6f static): ~53 columns, ~70 min wall-clock.**

The hex profile then has 5+1=6 layers ≈ 130 cols total:
- Identity (8) · Population (11) · Land use (21) · Buildings (39) · Roads + parking (53)

---

## 11b. Graph-theory features per hex

A road network is fundamentally a graph G=(V,E). Each hex contains a subgraph G_h (nodes + edges that fall inside). We can compute features at three scales:

### 11b.1 Local subgraph metrics (cheap, ship in 6b)

For G_h restricted to vehicle edges (motorway through residential, exclude footway):

| Feature | Formula | Captures |
|---|---|---|
| `road_node_count` | \|V(G_h)\| | Network density of nodes |
| `road_edge_count` | \|E(G_h)\| | Network density of edges |
| `road_intersection_count` | nodes with deg ≥ 3 | True intersections (excl. mid-segment nodes and dead ends) |
| `road_intersection_density_per_km2` | derived | Density-normalized |
| `road_avg_node_degree` | mean(deg(v)) for v ∈ V(G_h) | Network connectivity |
| `road_dead_end_count` | nodes with deg = 1 | Cul-de-sacs (HDB-estate signal) |
| `road_3way_count` | nodes with deg = 3 | T-junctions |
| `road_4way_count` | nodes with deg = 4 | Crossroads (Manhattan-grid signal) |
| `road_5plus_way_count` | nodes with deg ≥ 5 | Roundabouts / multi-arm junctions |
| `road_gridiness_score` | 4way_count / (3way + 4way + 5plus) | 1 = Manhattan grid; 0 = organic / radial / dendritic |
| `road_internal_components` | number of connected components in G_h | 1 = fully linked, >1 = fragmented (severance) |
| `road_local_clustering_coeff` | mean local clustering | Cul-de-sac estates have low; downtown gridded streets have low; suburban looped streets have higher |

Cost: O(\|V_h\| + \|E_h\|) per hex. For 7,318 hexes × ~40 nodes avg = trivial. **Ship in 6b.**

### 11b.2 Planar-face metrics (moderate, optional T3)

Roads define planar faces = city blocks. The dual graph encodes morphology:

| Feature | Captures |
|---|---|
| `road_block_count` | Number of blocks fully inside hex |
| `road_avg_block_area_m2` | Small = walkable / Jacobs; large = superblock / suburban |
| `road_block_size_cv` | Coefficient of variation; uniform = planned, varied = organic |
| `road_avg_block_perimeter_m` | Shape regularity proxy |

Cost: requires Shapely `polygonize` on the edge set per hex. Doable but heavier. **Defer to v4.1 unless block_count proves load-bearing.**

### 11b.3 Global centrality (expensive, ship in 6g)

A hex isn't just defined by what's inside it. It's also defined by its position in the SGP-wide network. Compute centrality on the full SGP road graph, then aggregate per hex.

Tractability: SGP full road graph has ~213K nodes (V3 atlas number). Full betweenness centrality is O(V·E) = ~10⁹ ops, several hours. We make it tractable by:

- **Restrict to major-road subgraph**: motorway + trunk + primary + secondary = ~36K segments, ~30K nodes. Betweenness is now ~10⁸ ops, **minutes**.
- **Sample-based approximation**: for full graph, sample 500 source-target pairs (gives unbiased estimate); ~30 minutes.

Per-hex aggregations:

| Feature | What | Cost |
|---|---|---|
| `centr_betweenness_mean` | mean of node betweenness for nodes in hex | computed once, joined |
| `centr_betweenness_max` | max — does a critical bottleneck node sit here? | trivial |
| `centr_closeness_mean` | how reachable is this hex from anywhere on SGP road graph? | one-shot Dijkstra-based |
| `centr_closeness_max` | best-positioned node in this hex | trivial |
| `centr_pagerank_mean` | random-walk importance | iterative, fast |
| `centr_eigenvector_mean` | dominant-eigenvector importance | iterative, fast |
| `centr_bridge_count` | number of bridges (edges whose removal disconnects the graph) inside hex | O(V+E), one-shot |

Why these matter:
- **Betweenness max** flags critical bottlenecks. Knowing "this hex sits on a critical link" predicts congestion vulnerability.
- **Closeness mean** ranks hexes by accessibility-by-road. Drive-thru retail wants high closeness.
- **PageRank mean** captures network-position quality (reachable from many origins).
- **Bridge count** identifies severance liabilities (edges that, if removed, fragment the network).

### 11b.4 Spectral features (skip for now)

Spectral-graph features (algebraic connectivity, spectral radius) are theoretically beautiful but yield little interpretable signal at hex scale. **Skip in v4; revisit if needed.**

### 11b.5 Implementation plan

**Stage 6b — local topology (cheap, do now):**
- Build vehicle-only subgraph from u/v columns of OSM
- For each hex: subset nodes by point-in-hex, edges by both-endpoints-in-hex (or majority-in-hex)
- Compute the 12 local features above

**Stage 6g — global centrality (medium, run once):**
- Build major-road subgraph (~36K segments, ~30K nodes)
- Compute node betweenness, closeness, pagerank, eigenvector centrality
- Identify bridges (Tarjan's bridge algorithm)
- Aggregate per hex (mean + max)
- Use NetworkX (CPU only, ~5–15 min on atlas-1)

**Stage 6g.2 — sample-based full-graph betweenness (optional):**
- If 6g signal proves weak, run k=500 source-pair sampled betweenness on full 213K-node graph
- ~30 min on atlas-1

---

## 12. Open questions (updated)

1. **T2 topology** ~confirmed, you happy?
2. **Two-network split** (pedestrian vs vehicle)? My lean: yes (Option B).
3. **Hierarchical motorway features (§9)** — through/adjacent/severance/exit as four separate flags, or one composite? My lean: keep all four — composites lose information.
4. **Borrow V3 walkability for now**, defer re-derivation? My lean: yes.
5. **Parking Tier 1 only** (static OSM + HDB) for now, defer capacity estimation and dynamic? My lean: yes.
6. **Include `near_expressway_exit_400m` as a separate flag from `dist_expressway_m`?** My lean: yes — different downstream use cases.
7. **Named expressway flags (PIE, ECP, AYE, …)?** My lean: defer unless explicitly needed.

Once you confirm, I'll write the builders + validators for stages 6a–6e.

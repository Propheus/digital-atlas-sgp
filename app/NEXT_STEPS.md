# SGP Atlas App — Next Steps

## What's Done
- Data composer: `compose_data.py` generates frontend-ready JSONs (9.5 MB)
- Subzone profiles (332 zones with 100+ metrics each)
- Places slim (66,851 places as compact tuples)
- Category stats, brand registry, co-location data
- Transit overlays (MRT stations, bus stops, hawker centres)

## What's Needed: Micrograph Pipeline

The NYC app's power comes from **per-place micro-graphs** — not just choropleth maps.
Each cafe/QSR/grocery has:
1. Tier classification (T1-T4 based on brand, rating, reviews)
2. OSM walk-routing to nearby places (Dijkstra on road network)
3. Context vector: transit, competitor, complementary, demand
4. Anchor detection: which major places (MRT, malls, schools) are nearby
5. Derived scores: location quality, competitive pressure, demand diversity

### Build Order
1. **Category taxonomy for SGP** — map 165 place_types to micrograph categories
2. **Tier classification** — T1 (premium brands), T2 (known chains), T3 (rated independents), T4 (others)
3. **OSM network snap** — snap all 66K places to road network (we have 551K edges)
4. **Anchor detection** — MRT stations, shopping malls, HDB blocks as anchors
5. **Micro-graph builder** — for each place, compute star-graph to nearby competitors + anchors
6. **Context vectors** — transit/competitor/complementary/demand per place
7. **Gap scores** — per-place opportunity scoring

### Which Categories First
Start with what matters most in SGP:
1. **Cafe & Coffee** (3,303 places) — direct comparison to NYC cafe pipeline
2. **Hawker & Street Food** (3,168) — SGP-specific, high impact
3. **Restaurant** (5,656) — largest F&B category
4. **Shopping & Retail** (12,280) — largest overall
5. **Beauty & Personal Care** (3,967) — high brand density

### Reuse from NYC
The `data-composer/src/` modules are mostly reusable:
- `spatial/index.py` — cKDTree spatial queries (generic)
- `graph/edge_classifier.py` — edge type/weight computation (generic)
- `graph/micro_graph.py` — star-graph builder (generic)
- `ingest/category_taxonomy.py` — needs SGP-specific version
- `cafe/config.py` — needs SGP brands/tiers
- `cafe/snap.py` — OSM snapping (needs SGP road network)

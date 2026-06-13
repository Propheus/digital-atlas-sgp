# Plexis Constellation — place-graph app (sketch)

2026-06-12. Standalone React app over the plexis-p1 place embedding
(190,591 places × 64d, 9/9 exam). Sibling app to SG Pulse; same travel-lens
theme, Propheus logo, fully static.

## Two modes (v0)

**GALAXY** — the whole city's commercial DNA in one picture.
UMAP-2D of all 190K embeddings rendered as a deck.gl point cloud.
Color by category; clusters labeled with honest heuristic names
("cafes · Orchard & malls", "industrial canteens"). Search any venue → camera
flies to it in *function space*. Toggle "color by region" to SHOW the
geo-leak result visually (function space ≠ geography).

**CONSTELLATION** — click any point (or search) → force-directed star:
the venue at centre, its 12 nearest functional siblings, edge thickness =
similarity. Click a sibling → re-centre (walk the graph). Right panel =
Mapbox map with the same nodes pinned + arcs, always in sync: function-space
left, geo-space right. Every panel carries ATLAS provenance footers.

v1 later: Brand DNA (chain centroid → next-outlet ghosts), Cast-this-corner
(context tower on an empty location → which archetypes fit).

## Data contracts (apps/place-graph/public/data/, all precomputed)

| File | Contents |
|---|---|
| `arrays.json` | parallel arrays over embedding row order: id[], name[], cat[] (uint8 code), lat[], lng[], cluster[] (uint16) |
| `galaxy_xy.bin` | Float32 x,y per point (UMAP coords, normalized to [0,1000]) |
| `meta.json` | category names/colors, cluster table (name, cx, cy, size, top brands), counts, extents |
| `nn/s<0..127>.json` | kNN-12 shards: rowIdx -> [[nbrRowIdx, sim*1000], ...], shard = idx % 128 |

Builder: `plexis-sgp-v5/build_constellation_data.py` (UMAP n_neighbors=30,
min_dist=0.08; KMeans k=48 clusters named by dominant category + dominant
region/context, no LLM in v0).

## Deploy

azold `/home/azureuser/place-graph/`, screen `place-graph`,
python http.server **16096** → http://10.0.2.25:16096
Verification: playwright probe against the DEPLOYED URL (house rule).

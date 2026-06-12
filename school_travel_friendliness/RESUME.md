# ASTS Friendliness — resume notes

Replicating *Land* 2024, 13(8), 1319 (Active School Travel Space friendliness,
Lanzhou) for Singapore's 179 MOE primary schools.

## State (paused)
- **01 schools** ✅ `data/primary_schools.geojson` — 179 primary schools.
- **02 walk network** ✅ `data/sg_walk.graphml` — 170,121 nodes / 463,880 edges (osmnx walk, SVY21).
- **03 space syntax** ⏸ restarted but STOPPED mid-run. Fix applied: build cityseer
  topology via `io.nx_from_generic_geopandas(edges)` (the old `io.nx_from_osm_nx`
  threw `KeyError` on a dangling node key after graphml round-trip). Just re-run.
- **04 catchments** ⏸ STOPPED mid-run (179× networkx ego_graph @1km on 170k-node graph — slow).
- **05–08** not yet run.

## To resume
```bash
cd school_travel_friendliness/scripts
python3 03_space_syntax.py   # produces data/syntax_nodes.gpkg  (heavy: cityseer on full net)
python3 04_catchments.py     # produces data/catchments.gpkg     (slow: per-school ego_graph)
python3 05_index_components.py
python3 06_friendliness.py
python3 07_geodetector.py
python3 08_report.py         # writes REPORT.md
```

## Open items / TODO before trusting numbers
- **05 column auto-discovery**: verify the cityseer angular column picked for
  `integration` (harmonic closeness @800) and `choice` (betweenness @800) after 03
  runs — print the columns and confirm names match.
- **Perf**: 04 is slow. Options — precompute nearest nodes once (done), or cap radius,
  or vectorize with `nx.single_source_dijkstra_path_length` cutoff (same thing).
  Consider running 03 + 04 overnight / in background.
- **Phase 2 (not started)**: street-view experiential dimension (green-view index,
  sky/enclosure, sidewalk ratio) via Google Street View / Mapillary + semantic
  segmentation. Phase 1 = network structure + objective proxies only.

## Design invariants (do not break)
- Index components and Geographic Detector drivers must stay DISJOINT (no transport/pop
  in the index) or the q-statistic is circular.
- Catchment = 1 km NETWORK distance (MOE priority band), not Euclidean buffer.
- Sanity check: mature estates (Toa Payoh/Bishan) high, peripheral (Lim Chu Kang) low.

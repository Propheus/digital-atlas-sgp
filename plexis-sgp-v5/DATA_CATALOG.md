# Digital Atlas — Data Catalog (Plexis **v5.2.0**)

A mathematical representation of Singapore at three spatial scales plus a per-place
layer. **Population 6,036,900** (SingStat Jun-2024). Updated 2026-06-11.

| Scale | Rows | Cols | Master file |
|---|---|---|---|
| **hex9** (H3 res-9, ~0.10 km²) | 7,318 | **583** | `hex/hex9_all_features.parquet` |
| **hex8** (H3 res-8, ~0.74 km²) | 1,191 | **801** | `hex/hex8_all_features.parquet` |
| **subzone** (URA Master Plan) | 326 | **389** | `hex/subzone_all_features.parquet` |
| **place** (POI) | 190,591 | 27 + 19 mg | `places/sgp_places_final.parquet` |

**New in v5.1.0 — S10 context pack** (16 hex8 cols, gated 4/4): URA conserved
buildings/shophouse clusters (`cons_*`), HDB carpark capacity (`carpark_*`, 696K lots),
polyclinics, wet markets, petrol stations, coworking venues, condo projects
(`condo_*`), `female_pop_share` (subzone-broadcast), BTO pipeline
(`bto_uc_units_town` + FAR-headroom-allocated `bto_pipeline_est`, FY2024 91,941 units).
Sources + point files in `nous_export/` (also delivered to the nous gap analyzer).

**New in v5.0.0 (= v4.10.0 content, released as V5) — site-selection layers S1–S9** (85 hex8 cols, 24 hex9 cols; every
layer validation-gated, see `SITE_SELECTION_VALIDATION.md`): `dt_*` daytime population,
`iso_*` walk/transit isochrone catchments (+ cached 1191×7318 transit minute matrix),
`cap_*` Huff capture potential (11 categories, hex9+hex8), `biz_*` ACRA formation/churn
(offline OneMap postal dump), `colo_*` co-location lift (+ 24×24 matrix in
`catalog/colo_lift_matrix.parquet`), `labor_*` labor-shed, `vis_*` MRT-exit footfall +
traffic exposure, `rent_*`/`roi_*` URA resi rent surface, `pipe_*` future rail (MP19
delta, 37 stations) + FAR-headroom dev capacity. Explorer manifest now 43 metrics in
11 categories incl. Opportunity/Catchment/Business/Future; `breathing_idx` redefined
to the AM-directional form (old form was direction-blind).

Join keys: `hex9_id` / `hex8_id` (H3), `subzone_c` (e.g. `AMSZ01`), `id` (place). Coords EPSG:4326; metric EPSG:3414.

---

## 1. Where everything lives

| What | Location |
|---|---|
| **Authoritative atlas (v5.0.0)** | `azold-test-server:/home/azureuser/da-sgp/v5/` (v4/ frozen at v4.9.0+S-layers) |
| Master tables (3 scales) | `v4/hex/{hex9,hex8,subzone}_all_features.parquet` |
| Per-layer parquets (~90 files) | `v4/hex/{scale}_<layer>.parquet` |
| Per-place tables | `v4/places/` (`sgp_places_final.parquet`, `sgp_places_micrograph.parquet`) |
| Place PCA embeddings | `v4/places/place_embedding_{what_64d,combined_128d}.parquet` |
| Hex PCA embeddings | `v4/hex/hex9_embedding_{where_64d,combined_128d}.parquet` |
| GNN embeddings (v3 128d, v6 256d) | `v4/plexis_gnn/plexis_v{3,6}_embeddings.npz` |
| OD raw + flow matrix | `v4/data/lta_od/` (CSVs + `hex8_od_matrix.parquet`) |
| NVIDIA personas (raw 148k) | `v4/data/nvidia_personas/train-0000{0,1}-of-00002.parquet` |
| Dorm sources (MOM/DASL) | `v4/data/external/mom/` |
| Machine catalogs | `v5/catalog/{dataset_catalog,feature_catalog}.{md,parquet,json}` (**2,518 features, 48 datasets, 100% described** — 1,347 curated + 1,171 pattern-derived; `desc_source` column tells which) |
| Build/validate scripts | `v4/build_*.py`, `validate_*.py`, `run_pipeline.py` |
| Version checkpoints | `v4/CHECKPOINT_v4.*.{json,md}` |
| Explorer app export | `v4/explorer_export/` → `explorer-app/public/data/` |
| **Git repo** | `github.com/Propheus/digital-atlas-sgp` → `plexis-sgp-v5/`, `explorer-app/` (LFS for parquet/geojson/csv) |
| **Canonical build host** | `atlas-1` / `atlas-deploy` (10.2.2.x) — has the 5 *graph* embeddings; **currently network-unreachable** |
| Explorer UI (dev) | `http://localhost:16070` (Vite) |

---

## 2. Layer families

Counts = columns in the master at each scale. Each family also has a standalone
`hex/{scale}_<file>.parquet`. ✓ = present, — = not at that scale.

| Family | h9 | h8 | sz | Source | Layer file | Sample cols |
|---|---|---|---|---|---|---|
| **Population & demographics** | 18 | 18 | 14 | SingStat dasymetric (HDB units+area), non-resident allocation, **MOM dorm placement**, WorldPop | `{scale}_population.parquet` | `pop_resident`, `pop_nonresident`, `pop_dorm`, `nonres_share`, `pop_65plus` |
| **Land use** | 18 | 18 | 18 | URA Master Plan 2019 (14 buckets) | `{scale}_land_use.parquet` | `lu_residential_pct`, `lu_commercial_pct`, `lu_total_m2`, `dominant_use` |
| **Buildings** | 14 | 14 | 13 | Overture + HDB authoritative | `{scale}_buildings_clean.parquet` | `bldg_count`, `bldg_density_per_km2`, `bldg_footprint_m2`, est-FAR |
| **Roads & traffic** | 6 | 7 | 7 | OSM (550K edges) + LTA 44,917 signals | `{scale}_roads_clean.parquet`, `_traffic_signals.parquet` | `road_length_total_m`, `road_density_km_per_km2`, centrality |
| **Transit & GTFS** | 52 | 52 | 37 | data.gov.sg + GTFS (8M stop_times), multi-window headways | `{scale}_transit_clean.parquet`, `_gtfs_windows.parquet` | `mrt_station_count`, `bus_stop_count`, `daily_bus_taps`, `gtfs_headway_am_min` |
| **Walkability** | 32 | 27 | 12 | OSM pedestrian infra + amenity walk-distance | `{scale}_walkability.parquet`, `_walk_scores.parquet` | `walkability_score`, `road_walkable_share`, `ped_path_length_m` |
| **Satellite night lights** | 25 | 25 | 15 | VIIRS 2022/2024 + WorldPop | `{scale}_satellite.parquet` | `nl_2024`, `nl_change_pct`, `nl_commercial_indicator`, `nl_growth_corridor` |
| **Land cover** | 6 | 6 | 6 | ESA WorldCover 2021 | `{scale}_landcover.parquet` | `wc_built_share`, `wc_tree_share`, `wc_water_share` |
| **Place composition (24 cat)** | 84 | 84 | 32 | 190K places, 24 Plexis categories | `{scale}_place_composition.parquet` | `pc_total`, `pc_magnets`, `pc_diversity`, `pc_cat_restaurant` |
| **Place composition V2 (55 cat)** | 51 | 51 | 51 | finer 55-category taxonomy | `{scale}_place_composition_v2.parquet` | `pc2_total`, `pc2_cat_food_hawker_count`, `pc2_cat_health_clinic_count` |
| **Per-place micrograph rollup** | 65 | 65 | 65 | per-place pressure/support/anchor → hex | `{scale}_micrograph_rollup.parquet` | `mg_cafe_coffee_pressure_400m`, `mg_*_support_400m`, `mg_*_anchor_strength` |
| **Amenities & schools** | 26 | 26 | 26 | 337 MOE schools + CHAS/hawker/preschool/tourist/silver | `{scale}_schools.parquet`, `_amenities_extra.parquet` | `school_count_total`, `chas_clinic_count`, `hawker_centre_count` |
| **HDB resale prices** | 9 | 9 | 9 | 227K txns 2017–2026 (town-broadcast) | `{scale}_hdb_resale.parquet` | `hdb_resale_4r_median_psm`, `hdb_resale_txns_12m` |
| **Demand pull (gravity)** | 14 | 14 | 6 | distance-decay to CBD/mall/hospital/MRT/school/airport | `{scale}_demand_pull.parquet` | `pull_cbd`, `pull_mall`, `pull_hospital`, `pull_mrt_interchange` |
| **Composite indices** | 22 | 22 | 6 | derived rollups | `{scale}_composites.parquet` | `vibrancy_index`, `livability_index`, `commercial_intensity`, `density_pressure` |
| **Synergy interactions** | 4 | 4 | 4 | cross-feature products | `{scale}_synergy.parquet` | `syn_pop_x_transit`, `syn_density_x_amenities` |
| **Saturation / gap** | 9 | 9 | 9 | actual vs expected per category /1k residents | `{scale}_saturation_gap.parquet` | `gap_cafe_coffee`, `gap_restaurant`, `gap_hawker` |
| **Spatial rings (k1/k2)** | ✓ | ✓ | — | 1- & 2-ring neighbor aggregates | `{scale}_spatial_rings.parquet` | `ring1_pop_resident`, `ring2_nl_2024` |
| **Pop-weighted neighborhood** | 32 | 32 | — | Σ neighbor_pop·feature / Σ pop | `{scale}_pop_weighted.parquet` | `pw1_pc_cat_business_office`, `max2_commercial_intensity` |
| **LTA dynamic** | ✓ | ✓ | ✓ | 73M tap-ins, 2,592 carparks, speed bands | `{scale}_lta_pv.parquet`, `_lta_dynamic.parquet` | `daily_train_taps`, carpark, speed |
| **OSM POIs** | ✓ | ✓ | ✓ | amenities/leisure/shops/tourism counts | `{scale}_osm_pois.parquet` | osm counts |
| **Archetypes** | 3 | — | 3 | k-means K=8 | `{scale}_archetypes.parquet` | `archetype_id`, `archetype_label` |
| **Influence** | ✓ | — | — | gravity-decay outbound/inbound/net (hex9 only) | `hex9_influence.parquet` | `interface`, `gradient_position`, `net_demand_flow` |

---

## 3. New in v4.9.0 (hex8-only unless noted)

| Layer | Cols | Where | Notes |
|---|---|---|---|
| **Dorm placement** (all scales) | `pop_dorm` | `{scale}_population.parquet` | 439,198 migrant-worker dorm pop at real MOM dorm hexes; subset of non-resident. Source `data/external/mom/`. |
| **OD mobility flows** | 13 (`od_*`) | `hex8_od_features.parquet` + full matrix `data/lta_od/hex8_od_matrix.parquet` | LTA DataMall PV-by-OD bus+train (Apr-2026 weekday); 100% mapped. `od_throughput`, `od_net_flow`, `od_dest_entropy`, `od_self_containment`, `od_am_pm_out_ratio`. |
| **Commercial activity** | 6 (`ca_*` + `commercial_activity_index`) | `hex8_commercial_activity.parquet` | Footfall-weighted (NL+spend+taps+places+OD). Distinct from `commercial_intensity` (corr 0.84). |
| **NVIDIA personas** | 33 (`nvp_*`) | `hex8_personas_nv.parquet` | nvidia/Nemotron-Personas-Singapore (148k, **PA-resolution broadcast**). age/sex/edu/occupation/industry distributions + `nvp_affluence_idx`, `nvp_low_n`. Raw in `data/nvidia_personas/`. |
| **Emergent** (derived in explorer) | `breathing_idx`, `latent_demand` | explorer export only | breathing = z(OD inflow)−z(resident); latent_demand = z(activity)−z(supply). |

---

## 4. Embeddings

| Embedding | Dim | Where | Method |
|---|---|---|---|
| **hex8 `plexis-e1`** ⭐ | 256 | `hex/hex8_embedding_plexis_e1_256d.parquet` | **HYBRID 160 PCA + 96 contrastive** (SCARF + view-masking) over the full v5.2 master — the primary hex8 SIMILARITY space, 13-check-gated (see `embedding/PLEXIS_E1_REPORT.md`). Use for twins/clustering/site matching; use raw features for ceiling prediction tasks |
| hex9 `where` | 64 | `hex/hex9_embedding_where_64d.parquet` | PCA of 545 hex features (84% var) |
| hex9 `combined` | 128 | `hex/hex9_embedding_combined_128d.parquet` | PCA concat |
| place `what` | 64 | `places/place_embedding_what_64d.parquet` | PCA of place features |
| place `combined` | 128 | `places/place_embedding_combined_128d.parquet` | PCA concat |
| GNN v3 | 128 | `plexis_gnn/plexis_v3_embeddings.npz` | two-head R-GCN (place/hex9/hex8) |
| GNN v6 | 256 | `plexis_gnn/plexis_v6_embeddings.npz` | GAT-R-GCN 4-layer (place/hex8) |

> The 5 **graph** embeddings (node2vec/gcn/super/place2vec/mega) exist only on the canonical `atlas-1` host (unreachable) and were intentionally not deployed here.

---

## 5. What the Explorer surfaces

`explorer-app` (`localhost:16070`) exposes **28 colorable hex8 metrics in 7 categories** (Population, Mobility, Commercial, Places, Living, People, Emergent) + ~50 detail fields. Map masked to **550 displayable hex8 / 244 subzones** (residential + industrial; airport, water-catchment, nature, islands, future excluded via `zone_type_broad`). Manifest: `explorer-app/public/data/layers.json`.

---

## 6. Load recipe

```python
import pandas as pd
ROOT = "/home/azureuser/da-sgp/v5"
h8 = pd.read_parquet(f"{ROOT}/hex/hex8_all_features.parquet")     # 1191 × 687
h9 = pd.read_parquet(f"{ROOT}/hex/hex9_all_features.parquet")     # 7318 × 583 (cap_*/colo_* at fine grain)
od = pd.read_parquet(f"{ROOT}/data/lta_od/hex8_od_matrix.parquet") # origin→dest flows
tmin = "hex/hex8_hex9_transit_min.npz"                             # 1191×7318 transit minutes (S2b/S5)
lift = pd.read_parquet(f"{ROOT}/catalog/colo_lift_matrix.parquet") # 24×24 co-location lifts
feat = pd.read_parquet(f"{ROOT}/catalog/feature_catalog.parquet")  # 2,518 descriptions (100%)
```

Full machine-readable feature list with stats + descriptions: `catalog/feature_catalog.parquet` (2,518 rows, every row described — `desc_source` ∈ curated|pattern; JSON twin for apps). Dataset-level index: `catalog/dataset_catalog.md` (48 datasets). Validation evidence per site-selection layer (S1–S10): `SITE_SELECTION_VALIDATION.md` + `logs/validate_*.json`.

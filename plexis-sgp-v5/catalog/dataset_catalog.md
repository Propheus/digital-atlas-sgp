# Plexis SGP v4 — Dataset Catalog

**Generated:** 2026-06-11 04:15 · **Datasets:** 50 (50 existing)

## scale = `hex9`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `hex/hex9_all_features.parquet` | 7,318 × 583 | `hex9_id` | `all` | MASTER — all standalone layers joined per hex-9 |
| `hex/hex9_buildings.parquet` | 7,318 × 39 | `hex9_id` | `2` | Buildings (counts, classes, floors, HDB) per hex-9 |
| `hex/hex9_buildings_clean.parquet` | 7,318 × 20 | `hex9_id` | `2c` | Buildings clean (clipped, est-FAR, HDB age) per hex-9 |
| `hex/hex9_built_environment_features.parquet` | 7,318 × 41 | `hex9_id` | `24` | BUNDLE — buildings + land_use per hex-9 |
| `hex/hex9_colo_fit.parquet` | 7,318 × 12 | `hex9_id` | `S6` | S6 co-location mix-match fit per hex-9 (colo_fit_*) |
| `hex/hex9_huff_capture.parquet` | 7,318 × 14 | `hex9_id` | `S1` | S1 Huff capture potential per hex-9 (cap_*, 11 categories, outlet-equivalents) |
| `hex/hex9_land_use.parquet` | 7,318 × 22 | `hex9_id` | `4` | URA land-use 14-bucket shares per hex-9 |
| `hex/hex9_mobility_features.parquet` | 7,318 × 53 | `hex9_id` | `56` | BUNDLE — roads + transit + walkability per hex-9 |
| `hex/hex9_population.parquet` | 7,318 × 15 | `hex9_id` | `3+3b` | Population (residents + non-residents) per hex-9 |
| `hex/hex9_roads_clean.parquet` | 7,318 × 18 | `hex9_id` | `6+6c` | Roads + parking + centrality (clean) per hex-9 |
| `hex/hex9_satellite.parquet` | 7,318 × 11 | `hex9_id` | `5b` | VIIRS night lights + WorldPop per hex-9 |
| `hex/hex9_transit_clean.parquet` | 7,318 × 19 | `hex9_id` | `5+5c` | Transit (MRT/LRT/bus/GTFS/ridership) per hex-9 |
| `hex/hex9_universe.parquet` | 7,318 × 8 | `hex9_id` | `0` | Hex-9 cell universe (7,318 cells across SGP) |
| `hex/hex9_walkability.parquet` | 7,318 × 27 | `hex9_id` | `7w` | Walkability composite + amenity walk distances per hex-9 |

## scale = `hex8`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `hex/hex8_acra_biz.parquet` | 1,191 × 11 | `hex8_id` | `S4` | S4 ACRA business formation & churn (biz_*; 1.95M entities geocoded via offline OneMap dump) |
| `hex/hex8_all_features.parquet` | 1,191 × 801 | `hex8_id` | `all` | MASTER — all standalone layers joined per hex-8 |
| `hex/hex8_buildings_clean.parquet` | 1,191 × 19 | `hex8_id` | `2c` | Buildings clean aggregated to hex-8 |
| `hex/hex8_built_environment_features.parquet` | 1,191 × 40 | `hex8_id` | `24` | BUNDLE — buildings + land_use aggregated to hex-8 |
| `hex/hex8_colo_fit.parquet` | 1,191 × 12 | `hex8_id` | `S6` | S6 co-location fit rolled to hex-8 (MAX over children) |
| `hex/hex8_context_pack.parquet` | 1,191 × 17 | `hex8_id` | `S10` | S10 context pack: conservation/shophouse, carpark capacity, polyclinics, wet markets, petrol, coworking, condos, female share, BTO pipeline |
| `hex/hex8_daytime_pop.parquet` | 1,191 × 9 | `hex8_id` | `S3` | S3 daytime population from LTA OD AM window (dt_*) |
| `hex/hex8_huff_capture.parquet` | 1,191 × 14 | `hex8_id` | `S1` | S1 Huff capture rolled to hex-8 (MAX over children = best site) |
| `hex/hex8_iso_transit.parquet` | 1,191 × 5 | `hex8_id` | `S2b` | S2b 15-min weekday-AM transit reach (iso_transit15_*; GTFS route-dir-stop graph) |
| `hex/hex8_iso_walk.parquet` | 1,191 × 17 | `hex8_id` | `S2a` | S2a 10-min walk isochrone catchments (iso_walk10_*; node-field demand, activity origins) |
| `hex/hex8_labor_shed.parquet` | 1,191 × 6 | `hex8_id` | `S5` | S5 labor pool / jobs reach within 30/45-min transit (labor_*) |
| `hex/hex8_land_use.parquet` | 1,191 × 22 | `hex8_id` | `4agg` | URA land-use aggregated to hex-8 (area-weighted) |
| `hex/hex8_mobility_features.parquet` | 1,191 × 50 | `hex8_id` | `56` | BUNDLE — roads + transit + walkability aggregated to hex-8 |
| `hex/hex8_mobility_pack.parquet` | 1,191 × 99 | `hex8_id` | `S11` | S11 mobility pack: travel-time anchors, destination reach, MRT effective-reach, waits/crowding, adequacy v3 (adq_*), 15-min city, pop pass-type splits, vulnerability, linkways/cycling |
| `hex/hex8_pipeline.parquet` | 1,191 × 6 | `hex8_id` | `S9` | S9 future rail (MP19 delta, 37 stations) + FAR-headroom dev capacity (pipe_*) |
| `hex/hex8_population.parquet` | 1,191 × 18 | `hex8_id` | `3agg` | Population aggregated to hex-8 |
| `hex/hex8_rent_surface.parquet` | 1,191 × 9 | `hex8_id` | `S8` | S8 URA resi rent surface + capture-per-rent ROI (rent_*, roi_*) |
| `hex/hex8_roads_clean.parquet` | 1,191 × 18 | `hex8_id` | `6c` | Roads + parking + centrality aggregated to hex-8 |
| `hex/hex8_satellite.parquet` | 1,191 × 9 | `hex8_id` | `5b` | VIIRS + WorldPop aggregated to hex-8 |
| `hex/hex8_transit_clean.parquet` | 1,191 × 18 | `hex8_id` | `5c` | Transit aggregated to hex-8 |
| `hex/hex8_universe.parquet` | 1,191 × 7 | `hex8_id` | `0` | Hex-8 cell universe (1,191 cells) |
| `hex/hex8_visibility.parquet` | 1,191 × 7 | `hex8_id` | `S7` | S7 MRT-exit footfall + traffic exposure (vis_*) |
| `hex/hex8_walkability.parquet` | 1,191 × 21 | `hex8_id` | `7w` | Walkability aggregated to hex-8 |

## scale = `subzone`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `hex/subzone_all_features.parquet` | 326 × 389 | `subzone_c` | `all` | MASTER — all standalone layers joined per subzone |
| `hex/subzone_buildings_clean.parquet` | 270 × 17 | `subzone_c` | `2c` | Buildings clean aggregated to subzone |
| `hex/subzone_built_environment_features.parquet` | 270 × 38 | `subzone_c` | `24` | BUNDLE — buildings + land_use aggregated to subzone |
| `hex/subzone_land_use.parquet` | 326 × 22 | `subzone_c` | `4agg` | URA land-use aggregated to subzone (area-weighted) |
| `hex/subzone_mobility_features.parquet` | 270 × 38 | `subzone_c` | `56` | BUNDLE — roads + transit + walkability aggregated to subzone |
| `hex/subzone_population.parquet` | 326 × 12 | `subzone_c` | `3agg` | Population aggregated to subzone |
| `hex/subzone_roads_clean.parquet` | 270 × 18 | `subzone_c` | `6c` | Roads + parking + centrality aggregated to subzone |
| `hex/subzone_satellite.parquet` | 326 × 9 | `subzone_c` | `5b` | VIIRS + WorldPop aggregated to subzone |
| `hex/subzone_transit_clean.parquet` | 270 × 14 | `subzone_c` | `5c` | Transit aggregated to subzone |
| `hex/subzone_walkability.parquet` | 270 × 8 | `subzone_c` | `7w` | Walkability aggregated to subzone |

## scale = `place`

| Dataset | Rows × Cols | Join key | Owner | Description |
|---|---|---|---|---|
| `places/sgp_places_final.parquet` | 190,591 × 27 | `hex9_id` | `1` | Stage-1 deliverable: 190,591 places × 27 cols (geo + cat + brand + quality) |
| `places/sgp_places_micrograph.parquet` | 190,591 × 20 | `id` | `10p` | Per-place micrograph (pmg_*): 400/800m competitors, complements, anchors, transit walk context — the per-venue site fingerprint |

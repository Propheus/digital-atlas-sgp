# Plexis — Feature Catalog (authoritative, detailed)

**Date:** 2026-04-23
**Source:** live parquets on atlas-1 (2026-04-20 build)
**Per-column stats** (dtype, null %, min/p50/p90/max) computed from the actual tables.
**Units** inferred from naming convention + dtype (see §0.2).
**Source stage** references `PLEXIS_METHODOLOGY.md` §5.

---

## 0. How to read this catalog

### 0.1 Table shape

| Table | Rows | Cols | File |
|---|---|---|---|
| hex9_final | 7,318 | 613 | `data/hex_v10/hex9_final.parquet` |
| hex8_final | 1,191 | 638 | `data/hex_v10/hex8_final.parquet` |
| places_featured | 174,711 | 114 | `data/places_consolidated/sgp_places_featured.parquet` |

### 0.2 Units convention

| Suffix / prefix | Units | Example |
|---|---|---|
| `_m` | meters | `dist_mrt_m`, `walk_mrt_m` |
| `_km`, `_km2` | km / km² | `area_km2` |
| `_pct`, `pct_*`, `_share` | fraction [0,1] | `pct_elderly`, `lu_residential_pct` |
| `_score`, `idx_*` | score [0,1] | `anchor_score`, `idx_vitality` |
| `_pctl` | percentile [0,100] | `pull_office_pctl` |
| `_count`, `_segments` | integer count | `bldg_count` |
| `_taps` | daily transit taps | `transit_daily_taps` |
| `gtfs_headway_*` | minutes | `gtfs_headway_am_min` |
| `saturation_*` | actual/expected ratio | `saturation_cafe` |
| `gap_*` | count deficit | `gap_restaurant` |
| `pull_*` | distance-decay weighted | `pull_office` |
| `synergy_*` | cat_count × pull | `synergy_cafe_office` |
| `sp_*` | spatial ring agg | `sp_max_population` |
| `tr_*` | transit ring agg | `tr_max_pc_total` |
| `nl_*` | VIIRS radiance | `nl_2024` |
| `ghsl_*` | GHSL built-up index | `ghsl_built_change` |
| `wc_*` | WorldCover share [0,1] | `wc_tree_cover_pct` |
| `wp_*` | WorldPop growth | `wp_pop_growth_pct` |
| `dyn_*` | live LTA | `dyn_avg_speed`, `dyn_pct_jammed` |

### 0.3 Null-policy convention

- **0%** — always populated (mandatory features)
- **< 5%** — edge hexes (coast, border, military). Zero-fill safe.
- **< 30%** — uneven coverage (legacy v9 copy-through for 1,421 new hexes; persona subzone limits).
- **>= 30%** — conditional feature (e.g., `saturation_cafe` only where `pop_total > 500`).

Mask companion: `hex_features_v10_mask.parquet` carries per-feature presence bits.

---

## 1. hex9_final.parquet — 7,318 rows × 613 cols

### identity — Identity / location metadata  (8 cols · Stage 0)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `area_km2` | float64 | km² | 0.0 | 0.1053 | 0.1053 | 0.1053 | 0.1053 |  |
| `hex_id` | str | string | 0.0 | — | — | — | — |  |
| `lat` | float64 | degrees EPSG:4326 | 0.0 | 1.16 | 1.35 | 1.42 | 1.47 |  |
| `lng` | float64 | degrees EPSG:4326 | 0.0 | 103.60 | 103.81 | 104.00 | 104.09 |  |
| `parent_pa` | str | string | 0.0 | — | — | — | — |  |
| `parent_region` | str | string | 0.0 | — | — | — | — |  |
| `parent_subzone` | str | string | 0.0 | — | — | — | — |  |
| `parent_subzone_name` | str | string | 0.0 | — | — | — | — |  |

### demographics — Population & age structure  (13 cols · Stage 3)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `children_count` | float64 | persons | 0.0 | 0 | 0 | 309.80 | 2,272 | 73.38% zero |
| `daytime_intensity` | float64 | fraction [0,1] | 0.0 | 0 | 1.14 | 100 | 100 |  |
| `daytime_ratio` | float64 | fraction [0,1] | 0.0 | 0 | 1.05 | 999 | 999 |  |
| `elderly_count` | float64 | persons | 0.0 | 0 | 0 | 447.44 | 2,740 | 73.26% zero |
| `nonresident_share` | float64 | fraction [0,1] | 0.0 | 0 | 0.128 | 1 | 1 |  |
| `population` | float64 | persons | 0.0 | 0 | 0 | 2,466 | 10,878 | 73.04% zero |
| `population_nonresident` | float64 | persons | 0.0 | 0 | 56.82 | 687.07 | 11,680 |  |
| `population_total` | float64 | persons | 0.0 | 0 | 62.89 | 3,202 | 13,033 |  |
| `residential_floor_weight` | float64 | — | 0.0 | 0 | 0 | 0.125 | 1 | 54.06% zero |
| `subzone_pop_total` | int64 | — | 0.0 | 0 | 0 | 31,530 | 127,080 | 53.38% zero |
| `subzone_res_floor_area` | float64 | — | 0.0 | 0 | 239,901 | 1,682,815 | 7,147,112 |  |
| `walking_dependent_count` | float64 | persons | 0.0 | 0 | 0 | 799.19 | 3,426 | 73.12% zero |
| `working_age_count` | float64 | persons | 0.0 | 0 | 0 | 1,661 | 7,452 | 73.04% zero |

### buildings — Built environment / physical form  (20 cols · Stage 2)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `avg_floors` | float64 | floors | 0.0 | 0 | 0 | 10.14 | 60 | 67.26% zero |
| `avg_height` | float64 | meters | 0.0 | 0 | 0 | 0 | 182 | 96.02% zero |
| `bldg_commercial` | float64 | — | 0.0 | 0 | 0 | 0 | 87 | 91.36% zero |
| `bldg_count` | float64 | count | 0.0 | 0 | 17 | 79 | 518 |  |
| `bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 6,056 | 39,159 | 353,933 |  |
| `bldg_hdb_residential` | float64 | — | 0.0 | 0 | 0 | 6 | 109 | 84.18% zero |
| `bldg_industrial` | float64 | — | 0.0 | 0 | 0 | 1 | 69 | 87.96% zero |
| `bldg_institutional` | float64 | — | 0.0 | 0 | 0 | 0 | 21 | 93.09% zero |
| `bldg_other` | float64 | — | 0.0 | 0 | 0 | 1 | 26 | 89.53% zero |
| `bldg_private_residential` | float64 | — | 0.0 | 0 | 0 | 9 | 454 | 75.05% zero |
| `bldg_religious` | float64 | — | 0.0 | 0 | 0 | 0 | 14 | 97.5% zero |
| `bldg_residential` | float64 | — | 0.0 | 0 | 0 | 18 | 454 | 72.0% zero |
| `bldg_transport` | float64 | — | 0.0 | 0 | 0 | 0 | 6 | 94.15% zero |
| `bldg_unclassified` | float64 | — | 0.0 | 0 | 14 | 64 | 418 |  |
| `commercial_floor_area_sqm` | float64 | m² | 0.0 | 0 | 0 | 24,294 | 1,050,112 | 76.77% zero |
| `hdb_blocks` | float64 | — | 0.0 | 0 | 0 | 6 | 109 | 84.18% zero |
| `max_floors` | float64 | floors | 0.0 | 0 | 0 | 16 | 70 | 67.26% zero |
| `max_height` | float64 | meters | 0.0 | 0 | 0 | 0 | 245 | 96.02% zero |
| `residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 0 | 148,973 | 898,919 | 72.03% zero |
| `total_floor_area_sqm` | float64 | m² | 0.0 | 0 | 13,881 | 208,138 | 1,071,301 |  |

### land_use — URA / zoning land use  (12 cols · Stage 4)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `avg_gpr` | float64 | GPR | 0.0 | 0 | 0 | 2.80 | 21.96 | 50.26% zero |
| `lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.8336 | 1 | 74.0% zero |
| `lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.002412 | 0.9317 | 89.23% zero |
| `lu_entropy` | float64 | nats | 0.0 | 0 | 0.5011 | 1.24 | 1.83 |  |
| `lu_institutional_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.1008 | 1 | 76.76% zero |
| `lu_mixed_use_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 1 | 98.1% zero |
| `lu_open_space_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.001328 | 0.9772 | 1 |  |
| `lu_other_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 1 | 1 | 65.41% zero |
| `lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.6374 | 1 | 67.76% zero |
| `lu_total_sqm` | float64 | m² | 0.0 | 0.02469 | 119,084 | 119,233 | 130,807 |  |
| `lu_transport_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.09267 | 0.3668 | 1 |  |
| `lu_utility_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.2027 | 1 | 61.9% zero |

### transit — Transit network + ridership  (17 cols · Stage 5)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `bus_daily_taps` | float64 | — | 0.0 | 0 | 0 | 2,477 | 107,657 | 68.11% zero |
| `bus_services_count` | float64 | count | 0.0 | 0 | 0.1429 | 3 | 11.29 |  |
| `bus_stops` | float64 | count | 0.0 | 0 | 0 | 3 | 13 | 69.77% zero |
| `bus_taps_am_peak` | float64 | — | 0.0 | 0 | 0 | 550.95 | 23,950 | 68.11% zero |
| `bus_taps_pm_peak` | float64 | — | 0.0 | 0 | 0 | 711.73 | 30,939 | 68.11% zero |
| `lrt_stations` | float64 | count | 0.0 | 0 | 0 | 0 | 1 | 99.4% zero |
| `mrt_daily_taps` | float64 | — | 0.0 | 0 | 0 | 0 | 168,480 | 98.35% zero |
| `mrt_hex_rings` | float64 | — | 0.0 | 0 | 5 | 19 | 20 |  |
| `mrt_stations` | float64 | count | 0.0 | 0 | 0 | 0 | 3 | 97.72% zero |
| `mrt_taps_am_peak` | float64 | — | 0.0 | 0 | 0 | 0 | 40,745 | 98.35% zero |
| `mrt_taps_night` | float64 | — | 0.0 | 0 | 0 | 0 | 22,400 | 98.35% zero |
| `mrt_taps_offpeak` | float64 | — | 0.0 | 0 | 0 | 0 | 50,080 | 98.35% zero |
| `mrt_taps_pm_peak` | float64 | — | 0.0 | 0 | 0 | 0 | 55,255 | 98.35% zero |
| `taps_per_capita_resident` | float64 | taps/person/day | 0.0 | 0 | 0 | 124.30 | 168,480 | 67.79% zero |
| `taps_per_capita_total` | float64 | taps/person/day | 0.0 | 0 | 0 | 4.48 | 37,935 | 67.79% zero |
| `transit_daily_taps` | float64 | daily taps | 0.0 | 0 | 0 | 2,686 | 198,622 | 67.79% zero |
| `transit_peak_ratio` | float64 | — | 0.0 | 0.5367 | 0.5367 | 0.5367 | 0.5367 |  |

### gtfs — GTFS schedule-derived frequency  (8 cols · Stage 5)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gtfs_daily_departures` | float64 | count/day | 0.0 | 0 | 0 | 57.57 | 485.05 | 69.58% zero |
| `gtfs_frequency_score` | float64 | score [0,1] | 0.0 | 0.002479 | 0.002479 | 0.02732 | 0.7372 |  |
| `gtfs_headway_am_min` | float64 | minutes | 0.0 | 3.05 | 60 | 60 | 60 |  |
| `gtfs_headway_night_min` | float64 | minutes | 0.0 | 7.15 | 60 | 60 | 60 |  |
| `gtfs_headway_offpeak_min` | float64 | minutes | 0.0 | 3.11 | 60 | 60 | 60 |  |
| `gtfs_headway_pm_min` | float64 | minutes | 0.0 | 3.10 | 60 | 60 | 60 |  |
| `gtfs_routes_served` | float64 | count | 0.0 | 0 | 0 | 7 | 50 | 69.58% zero |
| `gtfs_stops_with_service` | float64 | — | 0.0 | 0 | 0 | 3 | 12 | 69.58% zero |

### walk_euclid — Walkability scores (Euclidean)  (16 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `walk_bus_m` | float64 | meters | 0.0 | 5.32 | 464.26 | 5,063 | 13,781 |  |
| `walk_bus_score` | float64 | score [0,1] | 0.0 | 3.302e-08 | 0.5597 | 0.9 | 0.9934 |  |
| `walk_clinic_m` | float64 | meters | 0.0 | 1.44 | 1,339 | 7,147 | 14,169 |  |
| `walk_clinic_score` | float64 | score [0,1] | 0.0 | 2.033e-08 | 0.1875 | 0.764 | 0.9982 |  |
| `walk_hawker_m` | float64 | meters | 0.0 | 17.86 | 2,292 | 8,770 | 16,807 |  |
| `walk_hawker_score` | float64 | score [0,1] | 0.0 | 7.517e-10 | 0.05699 | 0.5108 | 0.9779 |  |
| `walk_mrt_m` | float64 | meters | 0.0 | 10.21 | 1,752 | 8,094 | 14,183 |  |
| `walk_mrt_score` | float64 | score [0,1] | 0.0 | 0 | 0 | 0.5388 | 0.98 | 71.44% zero |
| `walk_park_m` | float64 | meters | 0.0 | 17.26 | 1,354 | 7,279 | 16,209 |  |
| `walk_park_score` | float64 | score [0,1] | 0.0 | 1.587e-09 | 0.1841 | 0.6935 | 0.9787 |  |
| `walk_school_m` | float64 | meters | 0.0 | 0 | 700 | 7,456 | 15,929 |  |
| `walk_scorert_score` | float64 | score [0,1] | 0.0 | 1.997e-08 | 0.1119 | 0.6145 | 0.9873 |  |
| `walk_super_m` | float64 | meters | 0.0 | 6.21 | 1,232 | 6,393 | 14,368 |  |
| `walk_super_score` | float64 | score [0,1] | 0.0 | 1.585e-08 | 0.2144 | 0.7103 | 0.9923 |  |
| `walkability_score` | float64 | score [0,1] | 0.0 | 2.054e-08 | 0.2077 | 0.6036 | 0.8911 |  |
| `walkability_score_v2` | float64 | — | 0.0 | 0 | 0.4786 | 37 | 79 |  |

### walk_network — Walkability scores (network graph)  (13 cols · Stage 6+8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `nwalk_bus_m` | float64 | meters | 8.53 | 0 | 537.32 | 3,264 | 4,987 |  |
| `nwalk_bus_score` | float64 | score [0,1] | 0.0 | 0 | 0.4504 | 0.8736 | 1 |  |
| `nwalk_clinic_m` | float64 | meters | 22.14 | 0 | 1,412 | 3,898 | 4,981 |  |
| `nwalk_clinic_score` | float64 | score [0,1] | 0.0 | 0 | 0.06514 | 0.6378 | 1 |  |
| `nwalk_hawker_m` | float64 | meters | 34.22 | 0 | 1,794 | 3,981 | 5,000 |  |
| `nwalk_hawker_score` | float64 | score [0,1] | 0.0 | 0 | 0.02383 | 0.3644 | 1 |  |
| `nwalk_mrt_m` | float64 | meters | 31.02 | 0 | 1,600 | 3,923 | 4,999 |  |
| `nwalk_mrt_score` | float64 | score [0,1] | 0.0 | 0 | 0.03301 | 0.4675 | 1 |  |
| `nwalk_park_m` | float64 | meters | 22.26 | 0 | 1,423 | 3,806 | 4,994 |  |
| `nwalk_park_score` | float64 | score [0,1] | 0.0 | 0 | 0.07532 | 0.6434 | 1 |  |
| `nwalk_super_m` | float64 | meters | 21.4 | 0 | 1,369 | 4,041 | 4,998 |  |
| `nwalk_super_score` | float64 | score [0,1] | 0.0 | 0 | 0.07764 | 0.5658 | 1 |  |
| `nwalkability_composite` | float64 | — | 0.0 | 0 | 0.1667 | 0.5185 | 0.8316 |  |

### distance_amenity — Distance-to-amenity (meters, Euclidean)  (8 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `dist_bus_m` | float64 | meters | 0.0 | 5 | 464 | 5,057 | 13,757 |  |
| `dist_clinic_m` | float64 | meters | 0.0 | 1 | 1,339 | 7,143 | 14,144 |  |
| `dist_hawker_m` | float64 | meters | 0.0 | 17 | 2,292 | 8,764 | 16,777 |  |
| `dist_mrt_m` | float64 | meters | 0.0 | 16 | 1,752 | 8,086 | 14,163 |  |
| `dist_nearest_mrt_m` | float64 | meters | 0.0 | 0 | 875 | 6,137 | 14,163 |  |
| `dist_park_m` | float64 | meters | 0.0 | 9 | 1,364 | 7,250 | 16,175 |  |
| `dist_school_m` | float64 | meters | 0.0 | 0 | 700 | 7,456 | 15,929 |  |
| `dist_super_m` | float64 | meters | 0.0 | 6 | 1,230 | 6,385 | 14,343 |  |

### place_composition — Place composition (cat shares/counts)  (79 cols · Stage 7)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `pc_branded_count` | float64 | count | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_branded_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_cat_automotive` | float64 | — | 0.0 | 0 | 0 | 1 | 196 | 84.33% zero |
| `pc_cat_bakery___pastry` | float64 | — | 0.0 | 0 | 0 | 1 | 28 | 88.17% zero |
| `pc_cat_bakery_pastry` | int64 | — | 0.0 | 0 | 0 | 1 | 28 | 88.17% zero |
| `pc_cat_bar___nightlife` | float64 | — | 0.0 | 0 | 0 | 1 | 67 | 85.32% zero |
| `pc_cat_bar_nightlife` | int64 | — | 0.0 | 0 | 0 | 1 | 67 | 85.32% zero |
| `pc_cat_beauty___personal_care` | float64 | — | 0.0 | 0 | 0 | 3 | 209 | 79.16% zero |
| `pc_cat_beauty_personal_care` | int64 | — | 0.0 | 0 | 0 | 3 | 209 | 79.16% zero |
| `pc_cat_business` | float64 | — | 0.0 | 0 | 0 | 3 | 384 | 74.2% zero |
| `pc_cat_cafe___coffee` | float64 | — | 0.0 | 0 | 0 | 2 | 68 | 80.13% zero |
| `pc_cat_cafe_coffee` | int64 | — | 0.0 | 0 | 0 | 2 | 68 | 80.13% zero |
| `pc_cat_civic___government` | float64 | — | 0.0 | 0 | 0 | 1 | 16 | 77.48% zero |
| `pc_cat_civic_government` | int64 | — | 0.0 | 0 | 0 | 1 | 16 | 77.48% zero |
| `pc_cat_convenience___daily_needs` | float64 | — | 0.0 | 0 | 0 | 2 | 34 | 78.72% zero |
| `pc_cat_convenience_daily_needs` | int64 | — | 0.0 | 0 | 0 | 2 | 34 | 78.72% zero |
| `pc_cat_culture___entertainment` | float64 | — | 0.0 | 0 | 0 | 1 | 33 | 84.63% zero |
| `pc_cat_culture_entertainment` | int64 | — | 0.0 | 0 | 0 | 1 | 33 | 84.63% zero |
| `pc_cat_education` | float64 | — | 0.0 | 0 | 0 | 4 | 91 | 74.01% zero |
| `pc_cat_entropy` | float64 | nats | 46.24 | 0 | 1.75 | 2.54 | 2.89 |  |
| `pc_cat_fast_food___qsr` | float64 | — | 0.0 | 0 | 0 | 1 | 39 | 89.01% zero |
| `pc_cat_fast_food_qsr` | int64 | — | 0.0 | 0 | 0 | 1 | 39 | 89.01% zero |
| `pc_cat_fitness___recreation` | float64 | — | 0.0 | 0 | 0 | 3 | 62 | 73.35% zero |
| `pc_cat_fitness_recreation` | int64 | — | 0.0 | 0 | 0 | 3 | 62 | 73.35% zero |
| `pc_cat_general` | float64 | — | 0.0 | 0 | 0 | 1 | 13 | 82.71% zero |
| `pc_cat_hawker___street_food` | float64 | — | 0.0 | 0 | 0 | 1 | 88 | 86.43% zero |
| `pc_cat_hawker_street_food` | int64 | — | 0.0 | 0 | 0 | 1 | 88 | 86.43% zero |
| `pc_cat_health___medical` | float64 | — | 0.0 | 0 | 0 | 2 | 255 | 82.09% zero |
| `pc_cat_health_medical` | int64 | — | 0.0 | 0 | 0 | 2 | 255 | 82.09% zero |
| `pc_cat_hhi` | float64 | — | 0.0 | 0 | 0.0916 | 0.5556 | 1 |  |
| `pc_cat_hospitality` | float64 | — | 0.0 | 0 | 0 | 1 | 40 | 87.0% zero |
| `pc_cat_ngo` | float64 | — | 0.0 | 0 | 0 | 0 | 9 | 91.3% zero |
| `pc_cat_office___workspace` | float64 | — | 0.0 | 0 | 0 | 1 | 27 | 85.42% zero |
| `pc_cat_office_workspace` | int64 | — | 0.0 | 0 | 0 | 1 | 27 | 85.42% zero |
| `pc_cat_religious` | float64 | — | 0.0 | 0 | 0 | 1 | 32 | 89.33% zero |
| `pc_cat_residential` | float64 | — | 0.0 | 0 | 0 | 1 | 19 | 82.8% zero |
| `pc_cat_restaurant` | float64 | — | 0.0 | 0 | 0 | 5 | 243 | 74.19% zero |
| `pc_cat_services` | float64 | — | 0.0 | 0 | 0 | 4 | 288 | 69.73% zero |
| `pc_cat_shopping___retail` | float64 | — | 0.0 | 0 | 0 | 7 | 376 | 67.29% zero |
| `pc_cat_shopping_retail` | int64 | — | 0.0 | 0 | 0 | 7 | 376 | 67.29% zero |
| `pc_cat_transport` | float64 | — | 0.0 | 0 | 0 | 2 | 38 | 76.1% zero |
| `pc_pct_cat_automotive` | float64 | — | 0.0 | 0 | 0 | 0.0303 | 1 | 84.33% zero |
| `pc_pct_cat_bakery_pastry` | float64 | — | 0.0 | 0 | 0 | 0.01163 | 1 | 88.17% zero |
| `pc_pct_cat_bar_nightlife` | float64 | — | 0.0 | 0 | 0 | 0.02381 | 1 | 85.32% zero |
| `pc_pct_cat_beauty_personal_care` | float64 | — | 0.0 | 0 | 0 | 0.07572 | 1 | 79.16% zero |
| `pc_pct_cat_business` | float64 | — | 0.0 | 0 | 0 | 0.1622 | 1 | 74.2% zero |
| `pc_pct_cat_cafe_coffee` | float64 | — | 0.0 | 0 | 0 | 0.05263 | 1 | 80.13% zero |
| `pc_pct_cat_civic_government` | float64 | — | 0.0 | 0 | 0 | 0.07143 | 1 | 77.48% zero |
| `pc_pct_cat_convenience_daily_needs` | float64 | — | 0.0 | 0 | 0 | 0.0625 | 1 | 78.72% zero |
| `pc_pct_cat_culture_entertainment` | float64 | — | 0.0 | 0 | 0 | 0.02664 | 1 | 84.63% zero |
| `pc_pct_cat_education` | float64 | — | 0.0 | 0 | 0 | 0.1228 | 1 | 74.01% zero |
| `pc_pct_cat_fast_food_qsr` | float64 | — | 0.0 | 0 | 0 | 0.008742 | 0.5 | 89.01% zero |
| `pc_pct_cat_fitness_recreation` | float64 | — | 0.0 | 0 | 0 | 0.1087 | 1 | 73.35% zero |
| `pc_pct_cat_general` | float64 | — | 0.0 | 0 | 0 | 0.02857 | 1 | 82.71% zero |
| `pc_pct_cat_hawker_street_food` | float64 | — | 0.0 | 0 | 0 | 0.02532 | 1 | 86.43% zero |
| `pc_pct_cat_health_medical` | float64 | — | 0.0 | 0 | 0 | 0.04762 | 1 | 82.09% zero |
| `pc_pct_cat_hospitality` | float64 | — | 0.0 | 0 | 0 | 0.01726 | 1 | 87.0% zero |
| `pc_pct_cat_ngo` | float64 | — | 0.0 | 0 | 0 | 0 | 1 | 91.3% zero |
| `pc_pct_cat_office_workspace` | float64 | — | 0.0 | 0 | 0 | 0.02941 | 1 | 85.42% zero |
| `pc_pct_cat_religious` | float64 | — | 0.0 | 0 | 0 | 0.005155 | 1 | 89.33% zero |
| `pc_pct_cat_residential` | float64 | — | 0.0 | 0 | 0 | 0.04348 | 1 | 82.8% zero |
| `pc_pct_cat_restaurant` | float64 | — | 0.0 | 0 | 0 | 0.1273 | 1 | 74.19% zero |
| `pc_pct_cat_services` | float64 | — | 0.0 | 0 | 0 | 0.1435 | 1 | 69.73% zero |
| `pc_pct_cat_shopping_retail` | float64 | — | 0.0 | 0 | 0 | 0.2 | 1 | 67.29% zero |
| `pc_pct_cat_transport` | float64 | — | 0.0 | 0 | 0 | 0.07273 | 1 | 76.1% zero |
| `pc_pct_tier_budget` | float64 | — | 0.0 | 0 | 0 | 0.102 | 1 | 72.25% zero |
| `pc_pct_tier_luxury` | float64 | — | 0.0 | 0 | 0 | 0 | 1 | 94.7% zero |
| `pc_pct_tier_mid` | float64 | — | 0.0 | 0 | 0 | 0.75 | 1 | 53.06% zero |
| `pc_pct_tier_premium` | float64 | — | 0.0 | 0 | 0 | 0.1111 | 1 | 72.88% zero |
| `pc_pct_tier_value` | float64 | — | 0.0 | 0 | 0 | 0.5 | 1 | 55.03% zero |
| `pc_seg_entropy` | float64 | — | 0.0 | 0 | 0 | 2.83 | 3.56 | 54.3% zero |
| `pc_tier_budget` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_tier_luxury` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_tier_mid` | float64 | — | 0.0 | 0 | 0 | 0 | 1 | 99.55% zero |
| `pc_tier_premium` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_tier_value` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_total` | float64 | — | 0.0 | 0 | 1 | 51 | 1,356 |  |
| `pc_unique_brands` | int64 | — | 0.0 | 0 | 0 | 3 | 194 | 77.51% zero |
| `pc_unique_place_types` | int64 | — | 0.0 | 0 | 1 | 34 | 288 |  |

### demand_pull — Demand pull (distance-decay weighted)  (14 cols · Stage 9)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `pull_hawker` | float64 | pull units | 0.0 | 0 | 0 | 0.3929 | 3.13 | 80.83% zero |
| `pull_hawker_pctl` | float64 | percentile [0,100] | 0.0 | 0.4042 | 0.4042 | 0.9 | 1 |  |
| `pull_hotel` | float64 | pull units | 0.0 | 0 | 0 | 0.2778 | 39.67 | 87.11% zero |
| `pull_hotel_pctl` | float64 | percentile [0,100] | 0.0 | 0.4356 | 0.4356 | 0.9 | 1 |  |
| `pull_office` | float64 | pull units | 0.0 | 0 | 1.34 | 33.11 | 960.47 |  |
| `pull_office_pctl` | float64 | percentile [0,100] | 0.0 | 0.1578 | 0.5001 | 0.9 | 1 |  |
| `pull_residential` | float64 | pull units | 0.0 | 0 | 0 | 15,068 | 39,036 | 52.81% zero |
| `pull_residential_pctl` | float64 | percentile [0,100] | 0.0 | 0.2641 | 0.2641 | 0.9 | 1 |  |
| `pull_school` | float64 | pull units | 0.0 | 0 | 0 | 1.23 | 3.95 | 70.52% zero |
| `pull_school_pctl` | float64 | percentile [0,100] | 0.0 | 0.3527 | 0.3527 | 0.9 | 1 |  |
| `pull_total_pop` | float64 | pull units | 0.0 | 0 | 1,130 | 19,321 | 44,684 |  |
| `pull_total_pop_pctl` | float64 | percentile [0,100] | 0.0 | 0.1178 | 0.5001 | 0.9 | 1 |  |
| `pull_transit` | float64 | pull units | 0.0 | 0 | 631.88 | 29,776 | 223,618 |  |
| `pull_transit_pctl` | float64 | percentile [0,100] | 0.0 | 0.1759 | 0.5001 | 0.9 | 1 |  |

### synergy — Synergy (category × pull)  (23 cols · Stage 10)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `synergy_cafe_office` | float64 | synergy units | 0.0 | 0 | 0 | 33.82 | 59,460 | 80.34% zero |
| `synergy_cafe_office_pctl` | float64 | percentile [0,100] | 0.0 | 0.4017 | 0.4017 | 0.9 | 1 |  |
| `synergy_conv_transit` | float64 | synergy units | 0.0 | 0 | 0 | 51,672 | 6,612,730 | 78.93% zero |
| `synergy_conv_transit_pctl` | float64 | percentile [0,100] | 0.0 | 0.3947 | 0.3947 | 0.9 | 1 |  |
| `synergy_education` | float64 | synergy units | 0.0 | 0 | 0 | 3.69 | 95.57 | 79.19% zero |
| `synergy_education_pctl` | float64 | percentile [0,100] | 0.0 | 0.396 | 0.396 | 0.9 | 1 |  |
| `synergy_financial` | float64 | synergy units | 0.0 | 0 | 0 | 78.27 | 335,772 | 74.2% zero |
| `synergy_financial_pctl` | float64 | percentile [0,100] | 0.0 | 0.3711 | 0.3711 | 0.9 | 1 |  |
| `synergy_grocery_residential` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 134,984 | 94.53% zero |
| `synergy_grocery_residential_pctl` | float64 | percentile [0,100] | 0.0 | 0.4727 | 0.4727 | 0.4727 | 1 |  |
| `synergy_grocery_totalpop` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 155,073 | 94.29% zero |
| `synergy_health` | float64 | synergy units | 0.0 | 0 | 0 | 23,286 | 1,844,028 | 82.93% zero |
| `synergy_health_pctl` | float64 | percentile [0,100] | 0.0 | 0.4147 | 0.4147 | 0.9 | 1 |  |
| `synergy_health_totalpop` | float64 | synergy units | 0.0 | 0 | 0 | 32,093 | 3,445,009 | 82.11% zero |
| `synergy_lifestyle` | float64 | synergy units | 0.0 | 0 | 0 | 28,664 | 669,198 | 75.42% zero |
| `synergy_lifestyle_pctl` | float64 | percentile [0,100] | 0.0 | 0.3772 | 0.3772 | 0.9 | 1 |  |
| `synergy_lifestyle_totalpop` | float64 | synergy units | 0.0 | 0 | 0 | 39,647 | 801,392 | 73.74% zero |
| `synergy_morning` | float64 | synergy units | 0.0 | 0 | 0 | 10,884 | 3,695,349 | 88.21% zero |
| `synergy_morning_pctl` | float64 | percentile [0,100] | 0.0 | 0.4411 | 0.4411 | 0.9 | 1 |  |
| `synergy_nightlife` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 2,204 | 94.66% zero |
| `synergy_nightlife_pctl` | float64 | percentile [0,100] | 0.0 | 0.4734 | 0.4734 | 0.4734 | 1 |  |
| `synergy_rest_hotel` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 6,844 | 92.33% zero |
| `synergy_rest_hotel_pctl` | float64 | percentile [0,100] | 0.0 | 0.4617 | 0.4617 | 0.4617 | 1 |  |

### micrograph — Micrograph per-category context  (156 cols · Stage 13)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `mg_bake_anchor_count` | float64 | context | 0.0 | 0 | 0 | 19 | 25 | 87.82% zero |
| `mg_bake_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01147 | 0.09695 | 88.36% zero |
| `mg_bake_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.03892 | 0.2921 | 88.36% zero |
| `mg_bake_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1334 | 0.6445 | 87.84% zero |
| `mg_bake_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08532 | 0.8908 | 87.82% zero |
| `mg_bake_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6396 | 0.8128 | 87.99% zero |
| `mg_bake_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.53 | 1.79 | 87.82% zero |
| `mg_bake_n` | int64 | context | 0.0 | 0 | 0 | 1 | 31 | 87.82% zero |
| `mg_bake_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 96.72% zero |
| `mg_bake_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 99.18% zero |
| `mg_bake_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 94.7% zero |
| `mg_bake_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 95.27% zero |
| `mg_bake_walkability` | float64 | context | 0.0 | 0 | 0 | 43.34 | 283.60 | 87.82% zero |
| `mg_bar_anchor_count` | float64 | context | 0.0 | 0 | 0 | 19 | 25 | 85.32% zero |
| `mg_bar_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0125 | 1 | 86.61% zero |
| `mg_bar_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.04703 | 1 | 86.61% zero |
| `mg_bar_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.135 | 0.8359 | 85.64% zero |
| `mg_bar_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.09103 | 1.00 | 85.35% zero |
| `mg_bar_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6492 | 0.8959 | 86.44% zero |
| `mg_bar_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.56 | 1.79 | 85.41% zero |
| `mg_bar_n` | int64 | context | 0.0 | 0 | 0 | 1 | 69 | 85.27% zero |
| `mg_bar_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 96.91% zero |
| `mg_bar_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 99.08% zero |
| `mg_bar_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 95.26% zero |
| `mg_bar_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 91.9% zero |
| `mg_bar_walkability` | float64 | context | 0.0 | 0 | 0 | 83.88 | 411.20 | 85.32% zero |
| `mg_beau_anchor_count` | float64 | context | 0.0 | 0 | 0 | 17 | 17 | 79.63% zero |
| `mg_beau_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0216 | 0.2088 | 80.2% zero |
| `mg_beau_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1686 | 0.5867 | 80.2% zero |
| `mg_beau_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `mg_beau_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.1012 | 1.00 | 79.63% zero |
| `mg_beau_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.7322 | 0.9857 | 80.12% zero |
| `mg_beau_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.63 | 1.79 | 79.64% zero |
| `mg_beau_n` | int64 | context | 0.0 | 0 | 0 | 3 | 199 | 79.63% zero |
| `mg_beau_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 94.79% zero |
| `mg_beau_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.92% zero |
| `mg_beau_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 90.57% zero |
| `mg_beau_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.2261 | 1 | 89.19% zero |
| `mg_beau_walkability` | float64 | context | 0.0 | 0 | 0 | 102.02 | 337.80 | 79.63% zero |
| `mg_cafe_anchor_count` | float64 | context | 0.0 | 0 | 0 | 25 | 25 | 80.3% zero |
| `mg_cafe_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01744 | 0.2815 | 80.91% zero |
| `mg_cafe_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.132 | 0.4013 | 80.91% zero |
| `mg_cafe_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1358 | 0.7218 | 80.45% zero |
| `mg_cafe_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08808 | 1.00 | 80.3% zero |
| `mg_cafe_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6416 | 0.956 | 81.05% zero |
| `mg_cafe_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.59 | 1.79 | 80.35% zero |
| `mg_cafe_n` | int64 | context | 0.0 | 0 | 0 | 2 | 71 | 80.28% zero |
| `mg_cafe_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 95.01% zero |
| `mg_cafe_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.85% zero |
| `mg_cafe_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 91.3% zero |
| `mg_cafe_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 90.09% zero |
| `mg_cafe_walkability` | float64 | context | 0.0 | 0 | 0 | 94.54 | 400.80 | 80.3% zero |
| `mg_conv_anchor_count` | float64 | context | 0.0 | 0 | 0 | 17 | 17 | 78.42% zero |
| `mg_conv_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0206 | 0.191 | 78.9% zero |
| `mg_conv_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1596 | 0.5646 | 78.9% zero |
| `mg_conv_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `mg_conv_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.1025 | 1.00 | 78.42% zero |
| `mg_conv_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.7433 | 0.9421 | 78.97% zero |
| `mg_conv_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.64 | 1.79 | 78.44% zero |
| `mg_conv_n` | int64 | context | 0.0 | 0 | 0 | 3 | 39 | 78.42% zero |
| `mg_conv_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 95.2% zero |
| `mg_conv_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 99.02% zero |
| `mg_conv_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 90.43% zero |
| `mg_conv_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.5 | 1 | 88.1% zero |
| `mg_conv_walkability` | float64 | context | 0.0 | 0 | 0 | 113.35 | 383.80 | 78.42% zero |
| `mg_educ_anchor_count` | float64 | context | 0.0 | 0 | 0 | 25 | 25 | 75.25% zero |
| `mg_educ_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.02018 | 0.6296 | 75.76% zero |
| `mg_educ_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1602 | 0.6296 | 75.76% zero |
| `mg_educ_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1037 | 0.4827 | 75.88% zero |
| `mg_educ_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.0931 | 1.00 | 75.25% zero |
| `mg_educ_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6682 | 0.8906 | 76.11% zero |
| `mg_educ_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.68 | 1.79 | 75.31% zero |
| `mg_educ_n` | int64 | context | 0.0 | 0 | 0 | 4 | 76 | 75.24% zero |
| `mg_educ_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 95.35% zero |
| `mg_educ_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.92% zero |
| `mg_educ_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.1111 | 1 | 89.59% zero |
| `mg_educ_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 1 | 1 | 83.16% zero |
| `mg_educ_walkability` | float64 | context | 0.0 | 0 | 0 | 161.13 | 412.50 | 75.25% zero |
| `mg_fast_anchor_count` | float64 | context | 0.0 | 0 | 0 | 21 | 25 | 88.33% zero |
| `mg_fast_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0129 | 0.092 | 88.67% zero |
| `mg_fast_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.06708 | 0.371 | 88.67% zero |
| `mg_fast_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1268 | 0.7366 | 88.36% zero |
| `mg_fast_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08078 | 1 | 88.33% zero |
| `mg_fast_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6161 | 0.8862 | 88.59% zero |
| `mg_fast_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.40 | 1.79 | 88.34% zero |
| `mg_fast_n` | int64 | context | 0.0 | 0 | 0 | 1 | 36 | 88.33% zero |
| `mg_fast_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 96.53% zero |
| `mg_fast_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 99.07% zero |
| `mg_fast_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 94.51% zero |
| `mg_fast_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 96.27% zero |
| `mg_fast_walkability` | float64 | context | 0.0 | 0 | 0 | 30.19 | 277.10 | 88.33% zero |
| `mg_fitn_anchor_count` | float64 | context | 0.0 | 0 | 0 | 24 | 25 | 81.44% zero |
| `mg_fitn_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0153 | 0.4679 | 82.03% zero |
| `mg_fitn_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1056 | 0.8888 | 82.03% zero |
| `mg_fitn_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.119 | 0.5802 | 81.88% zero |
| `mg_fitn_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.09304 | 1 | 81.44% zero |
| `mg_fitn_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.671 | 0.8739 | 82.41% zero |
| `mg_fitn_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.56 | 1.79 | 81.51% zero |
| `mg_fitn_n` | int64 | context | 0.0 | 0 | 0 | 1 | 38 | 81.44% zero |
| `mg_fitn_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 96.41% zero |
| `mg_fitn_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 99.08% zero |
| `mg_fitn_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 93.22% zero |
| `mg_fitn_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.5 | 1 | 89.18% zero |
| `mg_fitn_walkability` | float64 | context | 0.0 | 0 | 0 | 141.91 | 445.60 | 81.44% zero |
| `mg_hawk_anchor_count` | float64 | context | 0.0 | 0 | 0 | 24 | 25 | 85.98% zero |
| `mg_hawk_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0147 | 0.078 | 86.51% zero |
| `mg_hawk_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1007 | 0.2841 | 86.51% zero |
| `mg_hawk_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1331 | 0.6986 | 86.03% zero |
| `mg_hawk_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08347 | 0.939 | 85.98% zero |
| `mg_hawk_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6234 | 0.8698 | 86.21% zero |
| `mg_hawk_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.56 | 1.79 | 85.98% zero |
| `mg_hawk_n` | int64 | context | 0.0 | 0 | 0 | 1 | 87 | 85.98% zero |
| `mg_hawk_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 96.38% zero |
| `mg_hawk_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 99.21% zero |
| `mg_hawk_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 93.18% zero |
| `mg_hawk_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 94.82% zero |
| `mg_hawk_walkability` | float64 | context | 0.0 | 0 | 0 | 47.17 | 289.80 | 85.98% zero |
| `mg_heal_anchor_count` | float64 | context | 0.0 | 0 | 0 | 18.67 | 25 | 84.16% zero |
| `mg_heal_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01766 | 0.0804 | 84.75% zero |
| `mg_heal_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1271 | 0.4771 | 84.75% zero |
| `mg_heal_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.02362 | 0.203 | 86.12% zero |
| `mg_heal_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.095 | 1.00 | 84.16% zero |
| `mg_heal_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.7022 | 0.9072 | 84.41% zero |
| `mg_heal_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.56 | 1.79 | 84.18% zero |
| `mg_heal_n` | int64 | context | 0.0 | 0 | 0 | 2 | 196 | 84.16% zero |
| `mg_heal_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 95.56% zero |
| `mg_heal_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.92% zero |
| `mg_heal_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 92.1% zero |
| `mg_heal_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 93.43% zero |
| `mg_heal_walkability` | float64 | context | 0.0 | 0 | 0 | 93.61 | 428.30 | 84.16% zero |
| `mg_rest_anchor_count` | float64 | context | 0.0 | 0 | 0 | 25 | 25 | 75.57% zero |
| `mg_rest_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01999 | 0.5098 | 76.25% zero |
| `mg_rest_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.158 | 0.7652 | 76.25% zero |
| `mg_rest_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1338 | 0.6216 | 75.87% zero |
| `mg_rest_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08983 | 1.00 | 75.57% zero |
| `mg_rest_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6379 | 0.9373 | 76.93% zero |
| `mg_rest_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.65 | 1.79 | 75.68% zero |
| `mg_rest_n` | int64 | context | 0.0 | 0 | 0 | 4 | 200 | 75.55% zero |
| `mg_rest_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 94.48% zero |
| `mg_rest_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.85% zero |
| `mg_rest_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.1699 | 1 | 88.95% zero |
| `mg_rest_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 1 | 1 | 86.1% zero |
| `mg_rest_walkability` | float64 | context | 0.0 | 0 | 0 | 119.42 | 399.70 | 75.57% zero |
| `mg_shop_anchor_count` | float64 | context | 0.0 | 0 | 0 | 25 | 25 | 68.87% zero |
| `mg_shop_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.02146 | 0.7822 | 69.31% zero |
| `mg_shop_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1705 | 0.9274 | 69.31% zero |
| `mg_shop_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1191 | 0.4176 | 69.91% zero |
| `mg_shop_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.09836 | 1.00 | 68.87% zero |
| `mg_shop_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6533 | 0.9397 | 71.32% zero |
| `mg_shop_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.68 | 1.79 | 68.93% zero |
| `mg_shop_n` | int64 | context | 0.0 | 0 | 0 | 5 | 254 | 68.83% zero |
| `mg_shop_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 93.96% zero |
| `mg_shop_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.8% zero |
| `mg_shop_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.3 | 1 | 87.59% zero |
| `mg_shop_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 1 | 1 | 78.45% zero |
| `mg_shop_walkability` | float64 | context | 0.0 | 0 | 0 | 169.47 | 423.40 | 68.87% zero |

### saturation_gap — Supply-demand saturation + gaps  (14 cols · Stage 11 / 14b)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gap_cafe` | float64 | count deficit | 73.01 | -67.32 | 0.3679 | 2.02 | 6.05 |  |
| `gap_commercial` | float64 | count deficit | 0.0 | -0.3643 | 0 | 0.007056 | 1 | 84.27% zero |
| `gap_convenience` | float64 | count deficit | 73.01 | -33.34 | 0.4361 | 2.42 | 8.52 |  |
| `gap_fnb` | float64 | count deficit | 73.01 | -357.41 | 1.46 | 8.96 | 28.44 |  |
| `gap_health` | float64 | count deficit | 73.01 | -253.71 | 0.3646 | 1.91 | 6.23 |  |
| `gap_industrial` | float64 | count deficit | 0.0 | -0.2297 | 0 | 0.8229 | 1 | 70.8% zero |
| `gap_residential` | float64 | count deficit | 0.0 | -0.3401 | 0 | 0.5409 | 1 | 66.51% zero |
| `gap_restaurant` | float64 | count deficit | 73.01 | -241.89 | 0.7208 | 4.16 | 12.18 |  |
| `saturation_cafe` | float64 | ratio | 73.01 | 0 | 0.5011 | 5 | 5 |  |
| `saturation_convenience` | float64 | ratio | 73.01 | 0 | 0.6004 | 4.21 | 5 |  |
| `saturation_fnb` | float64 | ratio | 73.01 | 0 | 0.6239 | 5 | 5 |  |
| `saturation_health` | float64 | ratio | 73.01 | 0 | 0.4467 | 5 | 5 |  |
| `saturation_restaurant` | float64 | ratio | 73.01 | 0 | 0.5846 | 5 | 5 |  |
| `ura_development_gap` | float64 | — | 0.0 | -3.36 | 0.05451 | 0.6902 | 1 |  |

### spatial_rings — Spatial neighborhood rings  (61 cols · Stage 12)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `sp_max_avg_gpr` | float64 | ring agg | 0.0 | 0 | 1.87 | 3.73 | 14.70 |  |
| `sp_max_bldg_count` | float64 | ring agg | 0.0 | 0 | 36 | 84 | 350 |  |
| `sp_max_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 35,268 | 60,553 | 213,913 |  |
| `sp_max_bus_stops` | float64 | ring agg | 0.0 | 0 | 1 | 4 | 13 |  |
| `sp_max_children_count` | float64 | ring agg | 0.0 | 0 | 0 | 407.79 | 1,743 | 61.37% zero |
| `sp_max_distance_rings` | float64 | ring agg | 0.0 | 1 | 4 | 5 | 5 |  |
| `sp_max_elderly_count` | float64 | ring agg | 0.0 | 0 | 0 | 598.55 | 1,921 | 60.88% zero |
| `sp_max_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 0 | 14 | 27 | 69.34% zero |
| `sp_max_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.7502 | 1 | 64.53% zero |
| `sp_max_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.4295 | 0.9317 | 59.14% zero |
| `sp_max_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.4675 | 1 | 60.48% zero |
| `sp_max_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 4.85 | 15.93 | 16.95 |  |
| `sp_max_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.3998 | 0.8511 | 1.00 |  |
| `sp_max_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0 | 0.2148 | 1 | 50.05% zero |
| `sp_max_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.121 | 0.3013 | 1.00 |  |
| `sp_max_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0 | 0.3034 | 1 | 63.08% zero |
| `sp_max_mrt_stations` | float64 | ring agg | 0.0 | 0 | 0 | 1 | 3 | 76.97% zero |
| `sp_max_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 0 | 4 | 65 | 54.52% zero |
| `sp_max_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 3 | 24 | 68 |  |
| `sp_max_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 2 | 29 | 91 |  |
| `sp_max_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 2.07 | 2.53 | 2.75 |  |
| `sp_max_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 1 | 19 | 88 |  |
| `sp_max_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 2 | 24 | 255 |  |
| `sp_max_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 0 | 6 | 27 | 52.56% zero |
| `sp_max_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 7 | 99 | 243 |  |
| `sp_max_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 12 | 117 | 376 |  |
| `sp_max_pc_total` | float64 | ring agg | 0.0 | 0 | 102 | 554 | 1,356 |  |
| `sp_max_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 3 | 82 | 194 |  |
| `sp_max_population` | float64 | ring agg | 0.0 | 0 | 0 | 3,252 | 10,175 | 60.88% zero |
| `sp_max_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 0 | 167,896 | 548,349 | 57.64% zero |
| `sp_max_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 0 | 1,046 | 3,173 | 60.88% zero |
| `sp_pw_avg_gpr` | float64 | ring agg | 0.0 | 0 | 1.79 | 2.86 | 13.32 |  |
| `sp_pw_bldg_count` | float64 | ring agg | 0.0 | 0 | 45.02 | 83.06 | 211.55 |  |
| `sp_pw_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 30,215 | 42,074 | 106,220 |  |
| `sp_pw_bus_stops` | float64 | ring agg | 0.0 | 0 | 1.50 | 2.43 | 4.70 |  |
| `sp_pw_children_count` | float64 | ring agg | 0.0 | 0 | 37.58 | 394.97 | 995.35 |  |
| `sp_pw_elderly_count` | float64 | ring agg | 0.0 | 0 | 60.82 | 545.74 | 1,057 |  |
| `sp_pw_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 0.3599 | 10.91 | 19.71 |  |
| `sp_pw_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.06355 | 0.7152 | 1 |  |
| `sp_pw_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.01355 | 0.1443 | 0.5764 |  |
| `sp_pw_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.12 | 0.4704 | 0.7274 |  |
| `sp_pw_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 4.83 | 11.37 | 14.79 |  |
| `sp_pw_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.4562 | 0.5854 | 0.9147 |  |
| `sp_pw_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.04365 | 0.1691 | 0.6536 |  |
| `sp_pw_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.1802 | 0.2981 | 0.8889 |  |
| `sp_pw_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0.0272 | 0.1548 | 0.7 |  |
| `sp_pw_mrt_stations` | float64 | ring agg | 0.0 | 0 | 0.01818 | 0.3153 | 1.16 |  |
| `sp_pw_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 0.4817 | 2.14 | 28.92 |  |
| `sp_pw_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 1.68 | 7.44 | 38.43 |  |
| `sp_pw_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 1.66 | 11.34 | 44.42 |  |
| `sp_pw_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 1.91 | 2.37 | 2.50 |  |
| `sp_pw_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 1.19 | 8.24 | 26.42 |  |
| `sp_pw_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 1.02 | 8.12 | 97.05 |  |
| `sp_pw_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 0.5351 | 2.95 | 12.62 |  |
| `sp_pw_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 4.26 | 27.13 | 133.29 |  |
| `sp_pw_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 5.77 | 41.41 | 186.36 |  |
| `sp_pw_pc_total` | float64 | ring agg | 0.0 | 0 | 44.87 | 203.26 | 838.56 |  |
| `sp_pw_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 2.38 | 20.71 | 78.46 |  |
| `sp_pw_population` | float64 | ring agg | 0.0 | 0 | 313.67 | 2,960 | 5,513 |  |
| `sp_pw_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 29,258 | 153,951 | 264,448 |  |
| `sp_pw_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 99.17 | 935.03 | 1,743 |  |

### transit_rings — Transit-graph rings  (62 cols · Stage 12)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `tr_max_avg_gpr` | float64 | ring agg | 0.0 | 0 | 3.41 | 8.54 | 14.70 |  |
| `tr_max_bldg_count` | float64 | ring agg | 0.0 | 0 | 28 | 48 | 284 |  |
| `tr_max_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 43,504 | 67,527 | 81,558 |  |
| `tr_max_bus_stops` | float64 | ring agg | 0.0 | 0 | 2 | 6 | 13 |  |
| `tr_max_children_count` | float64 | ring agg | 0.0 | 0 | 18.98 | 407.79 | 1,096 |  |
| `tr_max_elderly_count` | float64 | ring agg | 0.0 | 0 | 34.80 | 858.87 | 1,921 |  |
| `tr_max_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 1 | 12 | 20 |  |
| `tr_max_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.6363 | 0.7155 | 72.19% zero |
| `tr_max_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.3255 | 0.5088 | 0.9317 |  |
| `tr_max_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.04318 | 0.3072 | 0.6585 |  |
| `tr_max_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 15.11 | 16.24 | 16.95 |  |
| `tr_max_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.3957 | 0.4808 | 0.8941 |  |
| `tr_max_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.1627 | 0.2607 | 0.3318 |  |
| `tr_max_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.1542 | 0.1983 | 0.3886 |  |
| `tr_max_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0.2094 | 0.3681 | 0.4488 |  |
| `tr_max_mrt_stations` | float64 | ring agg | 0.0 | 0 | 1 | 2 | 2 |  |
| `tr_max_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 2 | 27 | 29 |  |
| `tr_max_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 17 | 51.90 | 68 |  |
| `tr_max_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 28 | 38 | 55 |  |
| `tr_max_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 2.25 | 2.53 | 2.57 |  |
| `tr_max_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 9 | 19 | 47 |  |
| `tr_max_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 19 | 74 | 134 |  |
| `tr_max_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 2 | 24 | 26 |  |
| `tr_max_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 104 | 172 | 219 |  |
| `tr_max_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 112 | 146 | 376 |  |
| `tr_max_pc_total` | float64 | ring agg | 0.0 | 0 | 462 | 1,278 | 1,356 |  |
| `tr_max_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 75 | 143 | 194 |  |
| `tr_max_population` | float64 | ring agg | 0.0 | 0 | 164.51 | 4,141 | 8,832 |  |
| `tr_max_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 41,158 | 215,459 | 548,349 |  |
| `tr_max_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 53.78 | 1,267 | 3,017 |  |
| `tr_nearest_station_rings` | float64 | ring agg | 0.0 | 0 | 5 | 24 | 999 |  |
| `tr_pw_avg_gpr` | float64 | ring agg | 0.0 | 0 | 2.70 | 3.65 | 5.53 |  |
| `tr_pw_bldg_count` | float64 | ring agg | 0.0 | 0 | 50.08 | 89.05 | 102.26 |  |
| `tr_pw_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 35,096 | 45,303 | 47,492 |  |
| `tr_pw_bus_stops` | float64 | ring agg | 0.0 | 0 | 2.36 | 2.62 | 3.14 |  |
| `tr_pw_children_count` | float64 | ring agg | 0.0 | 0 | 254.01 | 421.11 | 776.49 |  |
| `tr_pw_elderly_count` | float64 | ring agg | 0.0 | 0 | 403.99 | 616.35 | 687.25 |  |
| `tr_pw_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 7.57 | 11.78 | 15.43 |  |
| `tr_pw_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.1026 | 0.4609 | 0.7455 |  |
| `tr_pw_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.09993 | 0.2384 | 0.3317 |  |
| `tr_pw_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.3475 | 0.4806 | 0.5185 |  |
| `tr_pw_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 10.35 | 12.45 | 13.86 |  |
| `tr_pw_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.4923 | 0.5382 | 0.5705 |  |
| `tr_pw_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.1237 | 0.1502 | 0.1894 |  |
| `tr_pw_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.2324 | 0.2533 | 0.2834 |  |
| `tr_pw_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0.1326 | 0.172 | 0.236 |  |
| `tr_pw_mrt_stations` | float64 | ring agg | 0.0 | 0 | 0.2292 | 0.4059 | 0.4919 |  |
| `tr_pw_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 0.9423 | 11.22 | 19.09 |  |
| `tr_pw_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 5.77 | 16.94 | 24.74 |  |
| `tr_pw_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 9.18 | 17.26 | 22.38 |  |
| `tr_pw_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 2.33 | 2.37 | 2.45 |  |
| `tr_pw_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 5.97 | 10.00 | 12.84 |  |
| `tr_pw_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 6.72 | 27.76 | 37.99 |  |
| `tr_pw_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 1.63 | 4.38 | 5.40 |  |
| `tr_pw_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 19.54 | 65.42 | 95.79 |  |
| `tr_pw_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 26.97 | 82.18 | 101.65 |  |
| `tr_pw_pc_total` | float64 | ring agg | 0.0 | 0 | 143.89 | 432.01 | 582.31 |  |
| `tr_pw_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 16.35 | 31.34 | 40.63 |  |
| `tr_pw_population` | float64 | ring agg | 0.0 | 0 | 2,074 | 3,388 | 4,380 |  |
| `tr_pw_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 114,747 | 165,807 | 218,823 |  |
| `tr_pw_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 673.24 | 1,061 | 1,335 |  |
| `tr_reachable_hexes` | float64 | ring agg | 0.0 | 0 | 191 | 423 | 628 |  |

### influence — Influence (cross-scale, no leakage)  (3 cols · Stage 14)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gradient_position` | float64 | unitless | 0.0 | -4.82 | -0.1384 | 1.18 | 34.68 |  |
| `interface_score` | float64 | score [0,1] | 0.0 | 0 | 0.1667 | 0.6667 | 1 |  |
| `net_demand_flow` | float64 | fraction [0,1] | 0.0 | -0.9423 | 0 | 0.3669 | 0.9921 |  |

### amenities — Amenity counts at hex  (19 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `amenity_types_nearby` | float64 | count | 0.0 | 0 | 1 | 6 | 6 |  |
| `chas_clinics` | int64 | count | 0.0 | 0 | 0 | 0 | 12 | 91.3% zero |
| `clinics` | float64 | count | 0.0 | 0 | 0 | 0 | 12 | 91.3% zero |
| `formal_schools` | int64 | count | 0.0 | 0 | 0 | 0 | 3 | 95.93% zero |
| `hawker_centres` | float64 | count | 0.0 | 0 | 0 | 0 | 2 | 98.36% zero |
| `hotels` | float64 | count | 0.0 | 0 | 0 | 0 | 23 | 97.76% zero |
| `park_facilities` | int64 | count | 0.0 | 0 | 0 | 2 | 90 | 86.23% zero |
| `parks` | float64 | count | 0.0 | 0 | 0 | 0 | 6 | 94.97% zero |
| `parks_nature` | int64 | count | 0.0 | 0 | 0 | 0 | 5 | 94.85% zero |
| `preschools_gov` | int64 | count | 0.0 | 0 | 0 | 1 | 14 | 84.48% zero |
| `school_zones` | int64 | count | 0.0 | 0 | 0 | 0 | 2 | 97.25% zero |
| `schools_primary` | int64 | count | 0.0 | 0 | 0 | 0 | 2 | 97.61% zero |
| `schools_secondary` | int64 | count | 0.0 | 0 | 0 | 0 | 2 | 97.92% zero |
| `sfa_eating_count` | float64 | count | 0.0 | 0 | 0 | 12 | 244 | 72.41% zero |
| `sfa_eating_establishments` | int64 | count | 0.0 | 0 | 0 | 12 | 244 | 72.41% zero |
| `silver_zones` | int64 | count | 0.0 | 0 | 0 | 0 | 1 | 99.43% zero |
| `supermarkets` | float64 | count | 0.0 | 0 | 0 | 0 | 5 | 94.27% zero |
| `tourist_attractions` | float64 | count | 0.0 | 0 | 0 | 0 | 5 | 98.95% zero |
| `tourist_draw_est` | int64 | count | 0.0 | 0 | 0 | 60 | 3,485 | 71.21% zero |

### roads_signals — Roads + signals + pedestrian  (16 cols · Stage 6)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `bicycle_signal` | float64 | — | 0.0 | 0 | 0 | 0 | 4 | 99.78% zero |
| `ped_countdown` | float64 | count | 0.0 | 0 | 0 | 0 | 17 | 95.34% zero |
| `ped_crossings_total` | float64 | count | 0.0 | 0 | 0 | 8 | 48 | 75.4% zero |
| `ped_elderly` | float64 | count | 0.0 | 0 | 0 | 0 | 10 | 98.88% zero |
| `ped_standard` | float64 | count | 0.0 | 0 | 0 | 7 | 33 | 76.09% zero |
| `road_cat_arterial` | float64 | count/km | 0.0 | 0 | 0 | 0 | 26 | 97.2% zero |
| `road_cat_expressway` | float64 | count/km | 0.0 | 0 | 0 | 0 | 21 | 93.13% zero |
| `road_cat_major_arterial` | float64 | count/km | 0.0 | 0 | 0 | 0 | 53 | 91.75% zero |
| `road_cat_minor_arterial` | float64 | count/km | 0.0 | 0 | 0 | 0 | 25 | 92.43% zero |
| `road_cat_slip` | float64 | count/km | 0.0 | 0 | 0 | 0 | 32 | 92.53% zero |
| `road_cat_small` | float64 | count/km | 0.0 | 0 | 0 | 0 | 48 | 92.63% zero |
| `sig_beacon` | float64 | count | 0.0 | 0 | 0 | 4 | 20 | 82.52% zero |
| `sig_filter_arrow` | float64 | count | 0.0 | 0 | 0 | 0 | 22 | 90.42% zero |
| `sig_ground` | float64 | count | 0.0 | 0 | 0 | 10 | 51 | 74.88% zero |
| `sig_overhead` | float64 | count | 0.0 | 0 | 0 | 3 | 14 | 77.28% zero |
| `sig_rag` | float64 | count | 0.0 | 0 | 0 | 0 | 21 | 93.25% zero |

### satellite — Satellite (VIIRS / GHSL / WorldPop / WorldCover)  (23 cols · Stage 5b)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `ghsl_built_change` | float64 | built-up idx | 100.0 | — | — | — | — |  |
| `ghsl_built_growth_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_est_floors` | float64 | floors | 100.0 | — | — | — | — |  |
| `ghsl_height` | float64 | meters | 100.0 | — | — | — | — |  |
| `ghsl_is_highrise` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_is_new_dev` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_is_urban` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_is_urban_centre` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_smod` | float64 | built-up idx | 100.0 | — | — | — | — |  |
| `nl_2022` | float64 | radiance | 1.3 | 2.08 | 38.56 | 80.98 | 476.73 |  |
| `nl_2024` | float64 | radiance | 2.43 | 1.75 | 41.42 | 89.80 | 468.06 |  |
| `nl_change_pct` | float64 | fraction [0,1] | 1.68 | -68.20 | 1.89 | 29.47 | 1,067 |  |
| `nl_commercial_indicator` | float64 | radiance | 0.0 | -0.8336 | 0.03183 | 0.1569 | 0.9891 |  |
| `nl_decline_zone` | int64 | radiance | 0.0 | 0 | 0 | 0 | 1 | 91.76% zero |
| `nl_growth_corridor` | int64 | radiance | 0.0 | 0 | 0 | 1 | 1 | 84.07% zero |
| `nl_per_capita` | float64 | radiance | 0.0 | 0 | 0 | 294.60 | 3,291 | 52.84% zero |
| `wc_class` | float64 | fraction [0,1] | 0.0 | 10 | 50 | 80 | 95 |  |
| `wc_is_built` | int64 | fraction [0,1] | 0.0 | 0 | 0 | 1 | 1 | 63.57% zero |
| `wc_is_tree` | int64 | fraction [0,1] | 0.0 | 0 | 0 | 1 | 1 | 70.5% zero |
| `wc_is_water` | int64 | fraction [0,1] | 0.0 | 0 | 0 | 1 | 1 | 80.73% zero |
| `worldpop_2020` | float64 | — | 64.44 | 0.7738 | 113.39 | 230.29 | 844.45 |  |
| `worldpop_2025` | float64 | — | 64.44 | 0.7738 | 113.39 | 230.29 | 844.45 |  |
| `wp_pop_growth_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |

### property — Property  (1 cols · Stage 17)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `hdb_median_psf` | float64 | SGD/sqft | 0.0 | 0 | 0 | 685.44 | 923.86 | 61.77% zero |

### osm_poi — OSM POI  (4 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `osm_amenities` | float64 | count | 0.0 | 0 | 0 | 11 | 229 | 62.75% zero |
| `osm_leisure` | float64 | count | 0.0 | 0 | 0 | 6 | 68 | 68.94% zero |
| `osm_shops` | float64 | count | 0.0 | 0 | 0 | 1 | 161 | 84.49% zero |
| `osm_tourism` | float64 | count | 0.0 | 0 | 0 | 1 | 73 | 89.74% zero |

### dynamic_lta — Dynamic LTA (live)  (18 cols · Stage 14c)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `carpark_count` | int64 | count | 0.0 | 0 | 0 | 1 | 16 | 85.9% zero |
| `carpark_lots` | int64 | count | 0.0 | 0 | 0 | 177.30 | 3,054 | 86.1% zero |
| `dyn_avg_speed` | float64 | km/h | 0.0 | 0 | 4.01 | 10.60 | 79.72 |  |
| `dyn_car_dependency` | float64 | — | 0.0 | 0 | 0 | 14.29 | 25 | 72.72% zero |
| `dyn_carpark_available` | float64 | — | 0.0 | 0 | 0 | 269.14 | 1,663 | 72.72% zero |
| `dyn_carpark_count` | float64 | count | 0.0 | 0 | 0 | 1.29 | 6.86 | 72.53% zero |
| `dyn_carpark_per_1000pop` | float64 | — | 0.0 | 0 | 0 | 15.38 | 21,294 | 72.72% zero |
| `dyn_pct_jammed` | float64 | fraction [0,1] | 0.0 | 0 | 1.24 | 5.67 | 22.23 |  |
| `dyn_taxi_count` | float64 | count | 0.0 | 0 | 0 | 1.43 | 21 | 63.64% zero |
| `dyn_taxi_density` | float64 | — | 0.0 | 0 | 0 | 1.71 | 25.10 | 63.64% zero |
| `dyn_traffic_segs` | float64 | — | 0.0 | 0 | 3 | 20 | 44 |  |
| `hex_avg_speed_kmh` | float64 | km/h | 0.0 | 0 | 0 | 38.30 | 75 | 80.61% zero |
| `hex_flow_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 20 | 100 | 87.93% zero |
| `hex_flow_segments` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 2 | 49 | 87.93% zero |
| `hex_jam_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 5.90 | 100 | 89.76% zero |
| `hex_jam_segments` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 1 | 36 | 89.76% zero |
| `hex_seg_count` | float64 | count | 0.0 | 0 | 0 | 8 | 98 | 80.61% zero |
| `taxi_snapshot` | int64 | — | 0.0 | 0 | 0 | 0 | 13 | 94.98% zero |

### infra_misc — Park connectors + F&B roll-up + density  (5 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `fnb_total` | float64 | count | 0.0 | 0 | 0 | 10 | 360 | F&B roll-up (hawker + restaurant + cafe + fast food + bakery) |
| `park_connector_segments` | float64 | count | 0.0 | 0 | 0 | 0 | 18 | 94.77% zero |
| `pcn_segments` | int64 | count | 0.0 | 0 | 0 | 0 | 18 | 94.6% zero |
| `places_per_1000_resident` | float64 | per-capita density | 0.0 | 0 | 5.42 | 9,000 | 1,356,000 | inflated in near-zero-resident industrial hexes |
| `places_per_1000_total` | float64 | per-capita density | 0.0 | 0 | 3.77 | 579.63 | 117,000 | uses pop_total |

---

## 2. hex8_final.parquet — 1,191 rows × 638 cols

### identity — Identity / location metadata  (8 cols · Stage 0)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `area_km2` | float64 | km² | 0.0 | 0.8356 | 0.8375 | 0.8384 | 0.8389 |  |
| `hex8_id` | str | string | 0.0 | — | — | — | — |  |
| `lat` | float64 | degrees EPSG:4326 | 0.0 | 1.16 | 1.35 | 1.42 | 1.47 |  |
| `lng` | float64 | degrees EPSG:4326 | 0.0 | 103.60 | 103.81 | 104.01 | 104.09 |  |
| `n_children` | int64 | — | 0.0 | 1 | 7 | 7 | 7 |  |
| `parent_pa` | str | string | 0.0 | — | — | — | — |  |
| `parent_region` | str | string | 0.0 | — | — | — | — |  |
| `parent_subzone` | str | string | 0.0 | — | — | — | — |  |

### demographics — Population & age structure  (22 cols · Stage 3)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `children_count` | float64 | persons | 0.0 | 0 | 0 | 1,875 | 7,241 | 65.58% zero |
| `daytime_intensity` | float64 | fraction [0,1] | 0.0 | 0 | 1.27 | 100 | 100 |  |
| `daytime_ratio` | float64 | fraction [0,1] | 0.0 | 0 | 1.19 | 713.57 | 999 |  |
| `dependency_ratio` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.5358 | 13.50 | 65.24% zero |
| `elderly_count` | float64 | persons | 0.0 | 0 | 0 | 2,847 | 7,561 | 65.32% zero |
| `nonresident_share` | float64 | fraction [0,1] | 0.0 | 0 | 0.2147 | 1 | 1 |  |
| `pct_children` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.1501 | 0.2929 | 65.58% zero |
| `pct_elderly` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.2232 | 0.931 | 65.32% zero |
| `pct_elderly_total` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.1611 | 0.3009 | 65.32% zero |
| `pct_nonresident` | float64 | fraction [0,1] | 0.0 | 0 | 0.2147 | 1 | 1 |  |
| `pop_commercial_correlation` | float64 | persons | 0.0 | -0.918 | 0 | 0.6065 | 1 | 65.74% zero |
| `pop_concentration` | float64 | persons | 0.0 | 0 | 0 | 0.7134 | 0.8571 | 65.41% zero |
| `pop_density` | float64 | persons | 0.0 | 0 | 0 | 17,549 | 50,576 | 65.24% zero |
| `pop_density_total` | float64 | persons | 0.0 | 0 | 630.43 | 22,596 | 57,841 |  |
| `population` | float64 | persons | 0.0 | 0 | 0 | 14,695 | 42,391 | 65.24% zero |
| `population_nonresident` | float64 | persons | 0.0 | 0 | 454.18 | 4,229 | 18,559 |  |
| `population_total` | float64 | persons | 0.0 | 0 | 528.30 | 18,926 | 48,430 |  |
| `residential_floor_weight` | float64 | — | 0.0 | 0 | 0.01299 | 0.1694 | 0.869 |  |
| `subzone_pop_total` | float64 | — | 0.0 | 0 | 0 | 175,400 | 889,560 | 50.38% zero |
| `subzone_res_floor_area` | float64 | — | 0.0 | 0 | 234,561 | 1,761,181 | 7,147,112 |  |
| `walking_dependent_count` | float64 | persons | 0.0 | 0 | 0 | 4,802 | 12,450 | 65.24% zero |
| `working_age_count` | float64 | persons | 0.0 | 0 | 0 | 9,869 | 30,626 | 65.24% zero |

### buildings — Built environment / physical form  (21 cols · Stage 2)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `avg_floors` | float64 | floors | 0.0 | 0 | 0 | 11.14 | 40 | 54.66% zero |
| `avg_height` | float64 | meters | 0.0 | 0 | 0 | 0.3095 | 126.27 | 89.17% zero |
| `bldg_commercial` | float64 | — | 0.0 | 0 | 0 | 4 | 165 | 74.22% zero |
| `bldg_count` | float64 | count | 0.0 | 0 | 120 | 489 | 1,797 |  |
| `bldg_density` | float64 | — | 0.0 | 0 | 143.26 | 583.41 | 2,148 |  |
| `bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 48,806 | 235,036 | 456,952 |  |
| `bldg_hdb_residential` | float64 | — | 0.0 | 0 | 0 | 37 | 130 | 76.07% zero |
| `bldg_industrial` | float64 | — | 0.0 | 0 | 0 | 9 | 126 | 68.43% zero |
| `bldg_institutional` | float64 | — | 0.0 | 0 | 0 | 3 | 36 | 78.34% zero |
| `bldg_other` | float64 | — | 0.0 | 0 | 0 | 4 | 34 | 68.09% zero |
| `bldg_private_residential` | float64 | — | 0.0 | 0 | 0 | 79 | 969 | 63.98% zero |
| `bldg_religious` | float64 | — | 0.0 | 0 | 0 | 1 | 17 | 89.67% zero |
| `bldg_residential` | float64 | — | 0.0 | 0 | 0 | 23.27 | 345.33 | 63.06% zero |
| `bldg_transport` | float64 | — | 0.0 | 0 | 0 | 2 | 14 | 78.25% zero |
| `bldg_unclassified` | float64 | — | 0.0 | 0 | 104 | 379 | 1,581 |  |
| `commercial_floor_area_sqm` | float64 | m² | 0.0 | 0 | 0 | 176,595 | 1,073,373 | 52.14% zero |
| `hdb_blocks` | float64 | — | 0.0 | 0 | 0 | 37 | 130 | 76.07% zero |
| `max_floors` | float64 | floors | 0.0 | 0 | 0 | 25 | 70 | 54.07% zero |
| `max_height` | float64 | meters | 0.0 | 0 | 0 | 5 | 245 | 87.83% zero |
| `residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 0 | 839,740 | 2,128,494 | 63.06% zero |
| `total_floor_area_sqm` | float64 | m² | 0.0 | 0 | 111,243 | 1,245,484 | 2,383,582 |  |

### land_use — URA / zoning land use  (14 cols · Stage 4)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `avg_gpr` | float64 | GPR | 0.0 | 0 | 0.8293 | 2.81 | 14.01 |  |
| `dominant_use` | str | categorical | 0.0 | — | — | — | — |  |
| `lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.8164 | 1 | 65.16% zero |
| `lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.04285 | 0.5234 | 74.06% zero |
| `lu_entropy` | float64 | nats | 0.0 | 0 | 0.4326 | 1.13 | 1.64 |  |
| `lu_fragmentation` | float64 | count | 0.0 | 0 | 1 | 3 | 5 |  |
| `lu_institutional_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.09492 | 0.9183 | 65.91% zero |
| `lu_mixed_use_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0.4621 | 96.47% zero |
| `lu_open_space_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.03219 | 0.8947 | 1 |  |
| `lu_other_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.002482 | 0.9338 | 1 |  |
| `lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.627 | 0.8612 | 63.48% zero |
| `lu_total_sqm` | float64 | m² | 0.0 | 0.02469 | 119,023 | 119,226 | 122,567 |  |
| `lu_transport_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.1021 | 0.3195 | 1 |  |
| `lu_utility_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.003987 | 0.2066 | 1 |  |

### transit — Transit network + ridership  (18 cols · Stage 5)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `bus_daily_taps` | float64 | — | 0.0 | 0 | 0 | 19,436 | 156,751 | 50.46% zero |
| `bus_services_count` | float64 | count | 0.0 | 0 | 0 | 20 | 79 | 54.24% zero |
| `bus_stops` | float64 | count | 0.0 | 0 | 0 | 14 | 31 | 53.32% zero |
| `bus_taps_am_peak` | float64 | — | 0.0 | 0 | 0 | 4,324 | 34,871 | 50.46% zero |
| `bus_taps_pm_peak` | float64 | — | 0.0 | 0 | 0 | 5,586 | 45,047 | 50.46% zero |
| `lrt_stations` | float64 | count | 0.0 | 0 | 0 | 0 | 3 | 97.98% zero |
| `mrt_daily_taps` | float64 | — | 0.0 | 0 | 0 | 0 | 197,223 | 90.85% zero |
| `mrt_hex_rings` | float64 | — | 0.0 | 0.104 | 6 | 20 | 20 |  |
| `mrt_stations` | float64 | count | 0.0 | 0 | 0 | 1 | 5 | 87.99% zero |
| `mrt_taps_am_peak` | float64 | — | 0.0 | 0 | 0 | 0 | 47,697 | 90.85% zero |
| `mrt_taps_night` | float64 | — | 0.0 | 0 | 0 | 0 | 26,221 | 90.85% zero |
| `mrt_taps_offpeak` | float64 | — | 0.0 | 0 | 0 | 0 | 58,623 | 90.85% zero |
| `mrt_taps_pm_peak` | float64 | — | 0.0 | 0 | 0 | 0 | 64,682 | 90.85% zero |
| `taps_per_capita_resident` | float64 | taps/person/day | 0.0 | 0 | 0.06149 | 679 | 86,404 |  |
| `taps_per_capita_total` | float64 | taps/person/day | 0.0 | 0 | 0.03535 | 7.39 | 16,916 |  |
| `transit_daily_taps` | float64 | daily taps | 0.0 | 0 | 2 | 25,258 | 221,777 |  |
| `transit_mode_count` | int64 | count | 0.0 | 0 | 0 | 2 | 3 | 53.06% zero |
| `transit_peak_ratio` | float64 | — | 0.0 | 0.5367 | 0.5367 | 0.5367 | 0.5367 |  |

### gtfs — GTFS schedule-derived frequency  (8 cols · Stage 5)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gtfs_daily_departures` | float64 | count/day | 0.0 | 0 | 0 | 348.95 | 1,054 | 53.57% zero |
| `gtfs_frequency_score` | float64 | score [0,1] | 0.0 | 0.002479 | 0.002479 | 0.1312 | 0.7372 |  |
| `gtfs_headway_am_min` | float64 | minutes | 0.0 | 3.05 | 60 | 60 | 60 |  |
| `gtfs_headway_night_min` | float64 | minutes | 0.0 | 7.15 | 60 | 60 | 60 |  |
| `gtfs_headway_offpeak_min` | float64 | minutes | 0.0 | 3.11 | 60 | 60 | 60 |  |
| `gtfs_headway_pm_min` | float64 | minutes | 0.0 | 3.10 | 60 | 60 | 60 |  |
| `gtfs_routes_served` | float64 | count | 0.0 | 0 | 0 | 12 | 50 | 53.57% zero |
| `gtfs_stops_with_service` | float64 | — | 0.0 | 0 | 0 | 15 | 32 | 53.57% zero |

### walk_euclid — Walkability scores (Euclidean)  (16 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `walk_bus_m` | float64 | meters | 0.0 | 5.32 | 282.22 | 5,689 | 13,418 |  |
| `walk_bus_score` | float64 | score [0,1] | 0.0 | 4.251e-08 | 0.5294 | 0.8753 | 0.9805 |  |
| `walk_clinic_m` | float64 | meters | 0.0 | 1.44 | 1,319 | 7,415 | 13,828 |  |
| `walk_clinic_score` | float64 | score [0,1] | 0.0 | 2.574e-08 | 0.1351 | 0.7782 | 0.8957 |  |
| `walk_hawker_m` | float64 | meters | 0.0 | 17.86 | 2,265 | 9,463 | 16,523 |  |
| `walk_hawker_score` | float64 | score [0,1] | 0.0 | 9.322e-10 | 0.03996 | 0.5348 | 0.9263 |  |
| `walk_mrt_m` | float64 | meters | 0.0 | 10.21 | 1,720 | 8,483 | 13,813 |  |
| `walk_mrt_score` | float64 | score [0,1] | 0.0 | 0 | 0 | 0.5024 | 0.8562 | 64.06% zero |
| `walk_park_m` | float64 | meters | 0.0 | 17.26 | 1,214 | 8,135 | 15,928 |  |
| `walk_park_score` | float64 | score [0,1] | 0.0 | 1.96e-09 | 0.1571 | 0.6611 | 0.9428 |  |
| `walk_school_m` | float64 | meters | 0.0 | 0 | 700 | 7,615 | 15,244 |  |
| `walk_scorert_score` | float64 | score [0,1] | 0.0 | 2.584e-08 | 0.08153 | 0.6091 | 0.9054 |  |
| `walk_super_m` | float64 | meters | 0.0 | 6.21 | 1,171 | 6,770 | 14,020 |  |
| `walk_super_score` | float64 | score [0,1] | 0.0 | 2.016e-08 | 0.1738 | 0.7122 | 0.9199 |  |
| `walkability_score` | float64 | score [0,1] | 0.0 | 2.639e-08 | 0.1782 | 0.6085 | 0.8136 |  |
| `walkability_score_v2` | float64 | — | 0.0 | 0 | 1.14 | 38.44 | 71.68 |  |

### walk_network — Walkability scores (network graph)  (13 cols · Stage 6+8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `nwalk_bus_m` | float64 | meters | 10.5 | 0 | 577.19 | 3,264 | 4,862 |  |
| `nwalk_bus_score` | float64 | score [0,1] | 0.0 | 0 | 0.3736 | 0.8541 | 1 |  |
| `nwalk_clinic_m` | float64 | meters | 24.1 | 0 | 1,632 | 3,969 | 4,992 |  |
| `nwalk_clinic_score` | float64 | score [0,1] | 0.0 | 0 | 0.04804 | 0.615 | 1 |  |
| `nwalk_hawker_m` | float64 | meters | 36.94 | 110.30 | 1,836 | 4,014 | 4,970 |  |
| `nwalk_hawker_score` | float64 | score [0,1] | 0.0 | 0 | 0.01768 | 0.325 | 0.8712 |  |
| `nwalk_mrt_m` | float64 | meters | 34.51 | 0 | 1,698 | 4,054 | 4,974 |  |
| `nwalk_mrt_score` | float64 | score [0,1] | 0.0 | 0 | 0.02424 | 0.4501 | 1 |  |
| `nwalk_park_m` | float64 | meters | 24.52 | 0 | 1,506 | 3,806 | 4,982 |  |
| `nwalk_park_score` | float64 | score [0,1] | 0.0 | 0 | 0.05641 | 0.597 | 1 |  |
| `nwalk_super_m` | float64 | meters | 24.1 | 0 | 1,498 | 4,162 | 4,985 |  |
| `nwalk_super_score` | float64 | score [0,1] | 0.0 | 0 | 0.05289 | 0.5307 | 1 |  |
| `nwalkability_composite` | float64 | — | 0.0 | 0 | 0.1425 | 0.51 | 0.8045 |  |

### distance_amenity — Distance-to-amenity (meters, Euclidean)  (8 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `dist_bus_m` | float64 | meters | 0.0 | 5 | 282 | 5,688 | 13,394 |  |
| `dist_clinic_m` | float64 | meters | 0.0 | 1 | 1,317 | 7,402 | 13,803 |  |
| `dist_hawker_m` | float64 | meters | 0.0 | 17 | 2,265 | 9,447 | 16,523 |  |
| `dist_mrt_m` | float64 | meters | 0.0 | 16 | 1,739 | 8,460 | 13,793 |  |
| `dist_nearest_mrt_m` | float64 | meters | 0.0 | 0 | 875 | 6,124 | 13,793 |  |
| `dist_park_m` | float64 | meters | 0.0 | 9 | 1,223 | 8,135 | 15,908 |  |
| `dist_school_m` | float64 | meters | 0.0 | 0 | 700 | 7,615 | 15,244 |  |
| `dist_super_m` | float64 | meters | 0.0 | 6 | 1,170 | 6,758 | 13,996 |  |

### place_composition — Place composition (cat shares/counts)  (79 cols · Stage 7)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `pc_branded_count` | float64 | count | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_branded_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_cat_automotive` | float64 | — | 0.0 | 0 | 0 | 8 | 334 | 63.98% zero |
| `pc_cat_bakery___pastry` | float64 | — | 0.0 | 0 | 0 | 6 | 73 | 71.03% zero |
| `pc_cat_bakery_pastry` | float64 | — | 0.0 | 0 | 0 | 6 | 73 | 71.03% zero |
| `pc_cat_bar___nightlife` | float64 | — | 0.0 | 0 | 0 | 5 | 269 | 62.47% zero |
| `pc_cat_bar_nightlife` | float64 | — | 0.0 | 0 | 0 | 5 | 269 | 62.47% zero |
| `pc_cat_beauty___personal_care` | float64 | — | 0.0 | 0 | 0 | 26 | 683 | 64.4% zero |
| `pc_cat_beauty_personal_care` | float64 | — | 0.0 | 0 | 0 | 26 | 683 | 64.4% zero |
| `pc_cat_business` | float64 | — | 0.0 | 0 | 0 | 26 | 955 | 53.4% zero |
| `pc_cat_cafe___coffee` | float64 | — | 0.0 | 0 | 0 | 15 | 259 | 60.03% zero |
| `pc_cat_cafe_coffee` | float64 | — | 0.0 | 0 | 0 | 15 | 259 | 60.03% zero |
| `pc_cat_civic___government` | float64 | — | 0.0 | 0 | 0 | 8 | 44 | 53.06% zero |
| `pc_cat_civic_government` | float64 | — | 0.0 | 0 | 0 | 8 | 44 | 53.06% zero |
| `pc_cat_convenience___daily_needs` | float64 | — | 0.0 | 0 | 0 | 18 | 103 | 60.96% zero |
| `pc_cat_convenience_daily_needs` | float64 | — | 0.0 | 0 | 0 | 18 | 103 | 60.96% zero |
| `pc_cat_culture___entertainment` | float64 | — | 0.0 | 0 | 0 | 5 | 132 | 61.29% zero |
| `pc_cat_culture_entertainment` | float64 | — | 0.0 | 0 | 0 | 5 | 132 | 61.29% zero |
| `pc_cat_education` | float64 | — | 0.0 | 0 | 0 | 29 | 204 | 60.03% zero |
| `pc_cat_entropy` | float64 | nats | 0.0 | 0 | 1.56 | 15.33 | 18.17 |  |
| `pc_cat_fast_food___qsr` | float64 | — | 0.0 | 0 | 0 | 7 | 80 | 70.53% zero |
| `pc_cat_fast_food_qsr` | float64 | — | 0.0 | 0 | 0 | 7 | 80 | 70.53% zero |
| `pc_cat_fitness___recreation` | float64 | — | 0.0 | 0 | 0 | 16 | 144 | 53.82% zero |
| `pc_cat_fitness_recreation` | float64 | — | 0.0 | 0 | 0 | 16 | 144 | 53.82% zero |
| `pc_cat_general` | float64 | — | 0.0 | 0 | 0 | 5 | 39 | 56.76% zero |
| `pc_cat_hawker___street_food` | float64 | — | 0.0 | 0 | 0 | 16 | 271 | 68.01% zero |
| `pc_cat_hawker_street_food` | float64 | — | 0.0 | 0 | 0 | 16 | 271 | 68.01% zero |
| `pc_cat_health___medical` | float64 | — | 0.0 | 0 | 0 | 19 | 581 | 65.91% zero |
| `pc_cat_health_medical` | float64 | — | 0.0 | 0 | 0 | 19 | 581 | 65.91% zero |
| `pc_cat_hhi` | float64 | — | 0.0 | 0 | 1 | 2.71 | 6.36 |  |
| `pc_cat_hospitality` | float64 | — | 0.0 | 0 | 0 | 5 | 96 | 67.51% zero |
| `pc_cat_ngo` | float64 | — | 0.0 | 0 | 0 | 3 | 22 | 74.14% zero |
| `pc_cat_office___workspace` | float64 | — | 0.0 | 0 | 0 | 7 | 80 | 64.57% zero |
| `pc_cat_office_workspace` | float64 | — | 0.0 | 0 | 0 | 7 | 80 | 64.57% zero |
| `pc_cat_religious` | float64 | — | 0.0 | 0 | 0 | 5 | 64 | 71.87% zero |
| `pc_cat_residential` | float64 | — | 0.0 | 0 | 0 | 7 | 69 | 66.25% zero |
| `pc_cat_restaurant` | float64 | — | 0.0 | 0 | 0 | 38 | 1,209 | 55.08% zero |
| `pc_cat_services` | float64 | — | 0.0 | 0 | 0 | 26 | 619 | 51.47% zero |
| `pc_cat_shopping___retail` | float64 | — | 0.0 | 0 | 0 | 54 | 1,339 | 50.88% zero |
| `pc_cat_shopping_retail` | float64 | — | 0.0 | 0 | 0 | 54 | 1,339 | 50.88% zero |
| `pc_cat_transport` | float64 | — | 0.0 | 0 | 0 | 11 | 84 | 53.74% zero |
| `pc_pct_cat_automotive` | float64 | — | 0.0 | 0 | 0 | 0.03571 | 0.3333 | 65.99% zero |
| `pc_pct_cat_bakery_pastry` | float64 | — | 0.0 | 0 | 0 | 0.02041 | 0.1667 | 72.96% zero |
| `pc_pct_cat_bar_nightlife` | float64 | — | 0.0 | 0 | 0 | 0.03089 | 0.5 | 65.49% zero |
| `pc_pct_cat_beauty_personal_care` | float64 | — | 0.0 | 0 | 0 | 0.08247 | 0.272 | 65.99% zero |
| `pc_pct_cat_business` | float64 | — | 0.0 | 0 | 0 | 0.1429 | 0.7964 | 55.67% zero |
| `pc_pct_cat_cafe_coffee` | float64 | — | 0.0 | 0 | 0 | 0.05211 | 0.1786 | 62.38% zero |
| `pc_pct_cat_civic_government` | float64 | — | 0.0 | 0 | 0 | 0.08392 | 1 | 56.09% zero |
| `pc_pct_cat_convenience_daily_needs` | float64 | — | 0.0 | 0 | 0 | 0.06673 | 0.2857 | 62.89% zero |
| `pc_pct_cat_culture_entertainment` | float64 | — | 0.0 | 0 | 0 | 0.03921 | 0.7659 | 65.32% zero |
| `pc_pct_cat_education` | float64 | — | 0.0 | 0 | 0 | 0.1164 | 1 | 61.29% zero |
| `pc_pct_cat_fast_food_qsr` | float64 | — | 0.0 | 0 | 0 | 0.0191 | 0.3333 | 72.96% zero |
| `pc_pct_cat_fitness_recreation` | float64 | — | 0.0 | 0 | 0 | 0.104 | 0.5 | 55.08% zero |
| `pc_pct_cat_general` | float64 | — | 0.0 | 0 | 0 | 0.0381 | 0.5382 | 59.78% zero |
| `pc_pct_cat_hawker_street_food` | float64 | — | 0.0 | 0 | 0 | 0.04564 | 0.3992 | 70.19% zero |
| `pc_pct_cat_health_medical` | float64 | — | 0.0 | 0 | 0 | 0.05213 | 0.6956 | 67.51% zero |
| `pc_pct_cat_hospitality` | float64 | — | 0.0 | 0 | 0 | 0.03232 | 0.5246 | 69.02% zero |
| `pc_pct_cat_ngo` | float64 | — | 0.0 | 0 | 0 | 0.01372 | 0.5 | 76.74% zero |
| `pc_pct_cat_office_workspace` | float64 | — | 0.0 | 0 | 0 | 0.03571 | 0.5 | 67.34% zero |
| `pc_pct_cat_religious` | float64 | — | 0.0 | 0 | 0 | 0.01956 | 0.2695 | 73.22% zero |
| `pc_pct_cat_residential` | float64 | — | 0.0 | 0 | 0 | 0.06563 | 0.5088 | 67.34% zero |
| `pc_pct_cat_restaurant` | float64 | — | 0.0 | 0 | 0 | 0.1129 | 0.7143 | 57.09% zero |
| `pc_pct_cat_services` | float64 | — | 0.0 | 0 | 0 | 0.125 | 1 | 53.15% zero |
| `pc_pct_cat_shopping_retail` | float64 | — | 0.0 | 0 | 0 | 0.158 | 0.5 | 52.64% zero |
| `pc_pct_cat_transport` | float64 | — | 0.0 | 0 | 0 | 0.07901 | 0.5556 | 56.42% zero |
| `pc_pct_tier_budget` | float64 | — | 0.0 | 0 | 0 | 0.107 | 0.5 | 51.81% zero |
| `pc_pct_tier_luxury` | float64 | — | 0.0 | 0 | 0 | 0.003938 | 0.2778 | 84.97% zero |
| `pc_pct_tier_mid` | float64 | — | 0.0 | 0 | 0.2092 | 0.5986 | 1 |  |
| `pc_pct_tier_premium` | float64 | — | 0.0 | 0 | 0 | 0.1079 | 0.6364 | 56.51% zero |
| `pc_pct_tier_value` | float64 | — | 0.0 | 0 | 0.1429 | 0.4275 | 1 |  |
| `pc_seg_entropy` | float64 | — | 0.0 | 0 | 0.2879 | 2.79 | 3.27 |  |
| `pc_tier_budget` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_tier_luxury` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_tier_mid` | float64 | — | 0.0 | 0 | 0 | 0 | 2 | 97.4% zero |
| `pc_tier_premium` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_tier_value` | float64 | — | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `pc_total` | float64 | — | 0.0 | 0 | 8 | 374 | 5,693 |  |
| `pc_unique_brands` | float64 | — | 0.0 | 0 | 0 | 24 | 542 | 60.12% zero |
| `pc_unique_place_types` | float64 | — | 0.0 | 0 | 7 | 224 | 1,439 |  |

### demand_pull — Demand pull (distance-decay weighted)  (14 cols · Stage 9)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `pull_hawker` | float64 | pull units | 0.0 | 0 | 0 | 1.06 | 6.58 | 54.83% zero |
| `pull_hawker_pctl` | float64 | percentile [0,100] | 0.0 | 0.2746 | 0.2746 | 0.9001 | 1 |  |
| `pull_hotel` | float64 | pull units | 0.0 | 0 | 0 | 1.54 | 79.27 | 65.32% zero |
| `pull_hotel_pctl` | float64 | percentile [0,100] | 0.0 | 0.327 | 0.327 | 0.9001 | 1 |  |
| `pull_office` | float64 | pull units | 0.0 | 0 | 7.44 | 100.59 | 1,488 |  |
| `pull_office_pctl` | float64 | percentile [0,100] | 0.0 | 0.07976 | 0.5004 | 0.9001 | 1 |  |
| `pull_residential` | float64 | pull units | 0.0 | 0 | 1,064 | 49,479 | 112,709 |  |
| `pull_residential_pctl` | float64 | percentile [0,100] | 0.0 | 0.1965 | 0.5004 | 0.9001 | 1 |  |
| `pull_school` | float64 | pull units | 0.0 | 0 | 0 | 4.06 | 8.92 | 51.39% zero |
| `pull_school_pctl` | float64 | percentile [0,100] | 0.0 | 0.2573 | 0.2573 | 0.9001 | 1 |  |
| `pull_total_pop` | float64 | pull units | 0.0 | 0 | 6,359 | 65,439 | 132,279 |  |
| `pull_total_pop_pctl` | float64 | percentile [0,100] | 0.0 | 0.0508 | 0.5004 | 0.9001 | 1 |  |
| `pull_transit` | float64 | pull units | 0.0 | 0 | 3,212 | 69,593 | 299,630 |  |
| `pull_transit_pctl` | float64 | percentile [0,100] | 0.0 | 0.1066 | 0.5004 | 0.9001 | 1 |  |

### synergy — Synergy (category × pull)  (23 cols · Stage 10)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `synergy_cafe_office` | float64 | synergy units | 0.0 | 0 | 0 | 1,078 | 385,419 | 60.2% zero |
| `synergy_cafe_office_pctl` | float64 | percentile [0,100] | 0.0 | 0.3014 | 0.3014 | 0.9001 | 1 |  |
| `synergy_conv_transit` | float64 | synergy units | 0.0 | 0 | 0 | 1,274,593 | 19,337,505 | 61.38% zero |
| `synergy_conv_transit_pctl` | float64 | percentile [0,100] | 0.0 | 0.3073 | 0.3073 | 0.9001 | 1 |  |
| `synergy_education` | float64 | synergy units | 0.0 | 0 | 0 | 109.22 | 980.75 | 64.32% zero |
| `synergy_education_pctl` | float64 | percentile [0,100] | 0.0 | 0.322 | 0.322 | 0.9001 | 1 |  |
| `synergy_financial` | float64 | synergy units | 0.0 | 0 | 0 | 2,330 | 1,421,141 | 53.4% zero |
| `synergy_financial_pctl` | float64 | percentile [0,100] | 0.0 | 0.2674 | 0.2674 | 0.9001 | 1 |  |
| `synergy_grocery_residential` | float64 | synergy units | 0.0 | 0 | 0 | 72,428 | 435,944 | 78.42% zero |
| `synergy_grocery_residential_pctl` | float64 | percentile [0,100] | 0.0 | 0.3925 | 0.3925 | 0.9001 | 1 |  |
| `synergy_grocery_totalpop` | float64 | synergy units | 0.0 | 0 | 0 | 101,438 | 509,993 | 78.0% zero |
| `synergy_health` | float64 | synergy units | 0.0 | 0 | 0 | 874,864 | 15,786,755 | 67.59% zero |
| `synergy_health_pctl` | float64 | percentile [0,100] | 0.0 | 0.3384 | 0.3384 | 0.9001 | 1 |  |
| `synergy_health_totalpop` | float64 | synergy units | 0.0 | 0 | 0 | 1,177,517 | 24,661,567 | 65.91% zero |
| `synergy_lifestyle` | float64 | synergy units | 0.0 | 0 | 0 | 763,155 | 4,075,432 | 57.51% zero |
| `synergy_lifestyle_pctl` | float64 | percentile [0,100] | 0.0 | 0.288 | 0.288 | 0.9001 | 1 |  |
| `synergy_lifestyle_totalpop` | float64 | synergy units | 0.0 | 0 | 0 | 961,541 | 5,038,470 | 53.99% zero |
| `synergy_morning` | float64 | synergy units | 0.0 | 0 | 0 | 396,759 | 18,456,308 | 71.03% zero |
| `synergy_morning_pctl` | float64 | percentile [0,100] | 0.0 | 0.3556 | 0.3556 | 0.9001 | 1 |  |
| `synergy_nightlife` | float64 | synergy units | 0.0 | 0 | 0 | 3.74 | 16,330 | 78.93% zero |
| `synergy_nightlife_pctl` | float64 | percentile [0,100] | 0.0 | 0.395 | 0.395 | 0.9001 | 1 |  |
| `synergy_rest_hotel` | float64 | synergy units | 0.0 | 0 | 0 | 24.22 | 73,392 | 75.73% zero |
| `synergy_rest_hotel_pctl` | float64 | percentile [0,100] | 0.0 | 0.3791 | 0.3791 | 0.9001 | 1 |  |

### micrograph — Micrograph per-category context  (156 cols · Stage 13)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `mg_bake_anchor_count` | float64 | context | 0.0 | 0 | 0 | 13.25 | 25.00 | 72.88% zero |
| `mg_bake_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.009011 | 0.0307 | 74.9% zero |
| `mg_bake_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.04658 | 0.1425 | 74.9% zero |
| `mg_bake_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.08975 | 0.24 | 72.96% zero |
| `mg_bake_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.05911 | 0.2158 | 72.88% zero |
| `mg_bake_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.4055 | 0.772 | 73.47% zero |
| `mg_bake_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 0.9818 | 1.79 | 72.88% zero |
| `mg_bake_n` | float64 | context | 0.0 | 0 | 0 | 7 | 88 | 71.03% zero |
| `mg_bake_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 90.76% zero |
| `mg_bake_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 97.98% zero |
| `mg_bake_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.2194 | 1 | 82.45% zero |
| `mg_bake_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.1936 | 1 | 82.54% zero |
| `mg_bake_walkability` | float64 | context | 0.0 | 0 | 0 | 55.40 | 250.60 | 72.88% zero |
| `mg_bar_anchor_count` | float64 | context | 0.0 | 0 | 0 | 12.34 | 25.00 | 65.99% zero |
| `mg_bar_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.009567 | 0.1429 | 71.03% zero |
| `mg_bar_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.04117 | 0.2715 | 71.03% zero |
| `mg_bar_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.09051 | 0.3402 | 67.76% zero |
| `mg_bar_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.07007 | 0.5 | 66.16% zero |
| `mg_bar_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.3902 | 0.7731 | 69.44% zero |
| `mg_bar_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 0.9308 | 1.79 | 66.41% zero |
| `mg_bar_n` | float64 | context | 0.0 | 0 | 0 | 5 | 271 | 62.64% zero |
| `mg_bar_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 0.9754 | 92.11% zero |
| `mg_bar_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 0.9484 | 97.98% zero |
| `mg_bar_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.1429 | 1 | 84.72% zero |
| `mg_bar_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.2857 | 1 | 73.72% zero |
| `mg_bar_walkability` | float64 | context | 0.0 | 0 | 0 | 65.94 | 266.80 | 65.99% zero |
| `mg_beau_anchor_count` | float64 | context | 0.0 | 0 | 0 | 15.36 | 17.00 | 66.16% zero |
| `mg_beau_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01983 | 0.1919 | 68.93% zero |
| `mg_beau_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1525 | 0.2903 | 68.93% zero |
| `mg_beau_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `mg_beau_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.09758 | 0.7618 | 66.16% zero |
| `mg_beau_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6814 | 0.8608 | 67.67% zero |
| `mg_beau_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.50 | 1.79 | 66.25% zero |
| `mg_beau_n` | float64 | context | 0.0 | 0 | 0 | 25 | 598 | 64.48% zero |
| `mg_beau_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.05671 | 0.9944 | 88.16% zero |
| `mg_beau_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 97.57% zero |
| `mg_beau_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.3705 | 1 | 78.25% zero |
| `mg_beau_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.4476 | 1 | 72.04% zero |
| `mg_beau_walkability` | float64 | context | 0.0 | 0 | 0 | 91.70 | 239.20 | 66.16% zero |
| `mg_cafe_anchor_count` | float64 | context | 0.0 | 0 | 0 | 19.50 | 25.00 | 62.89% zero |
| `mg_cafe_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01397 | 0.05507 | 65.41% zero |
| `mg_cafe_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1044 | 0.2148 | 65.41% zero |
| `mg_cafe_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1126 | 0.2944 | 63.64% zero |
| `mg_cafe_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.07787 | 0.3607 | 62.89% zero |
| `mg_cafe_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.5054 | 0.7811 | 65.24% zero |
| `mg_cafe_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.27 | 1.79 | 63.14% zero |
| `mg_cafe_n` | float64 | context | 0.0 | 0 | 0 | 15 | 273 | 60.29% zero |
| `mg_cafe_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.06267 | 1 | 87.99% zero |
| `mg_cafe_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 0.981 | 97.48% zero |
| `mg_cafe_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.316 | 1 | 77.67% zero |
| `mg_cafe_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.3765 | 1 | 70.03% zero |
| `mg_cafe_walkability` | float64 | context | 0.0 | 0 | 0 | 77.83 | 201.80 | 62.89% zero |
| `mg_conv_anchor_count` | float64 | context | 0.0 | 0 | 0 | 14.99 | 17.00 | 62.8% zero |
| `mg_conv_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01865 | 0.09874 | 65.24% zero |
| `mg_conv_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.144 | 0.2145 | 65.24% zero |
| `mg_conv_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `mg_conv_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.0964 | 0.8673 | 62.8% zero |
| `mg_conv_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6622 | 0.8644 | 64.23% zero |
| `mg_conv_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.47 | 1.79 | 62.89% zero |
| `mg_conv_n` | float64 | context | 0.0 | 0 | 0 | 19 | 106 | 60.87% zero |
| `mg_conv_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.0593 | 1 | 88.08% zero |
| `mg_conv_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 97.9% zero |
| `mg_conv_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.3752 | 1 | 77.75% zero |
| `mg_conv_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.4576 | 1 | 68.35% zero |
| `mg_conv_walkability` | float64 | context | 0.0 | 0 | 0 | 95.89 | 195.30 | 62.8% zero |
| `mg_educ_anchor_count` | float64 | context | 0.0 | 0 | 0 | 23.42 | 25.00 | 62.97% zero |
| `mg_educ_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01935 | 0.3693 | 65.49% zero |
| `mg_educ_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1535 | 0.4941 | 65.49% zero |
| `mg_educ_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.09395 | 0.157 | 65.16% zero |
| `mg_educ_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.09209 | 0.8524 | 62.97% zero |
| `mg_educ_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6427 | 0.8678 | 65.41% zero |
| `mg_educ_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.57 | 1.79 | 63.22% zero |
| `mg_educ_n` | float64 | context | 0.0 | 0 | 0 | 25 | 147 | 61.63% zero |
| `mg_educ_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.05157 | 1 | 88.41% zero |
| `mg_educ_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 0.8825 | 97.73% zero |
| `mg_educ_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.3261 | 1 | 77.08% zero |
| `mg_educ_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.6265 | 1 | 66.5% zero |
| `mg_educ_walkability` | float64 | context | 0.0 | 0 | 0 | 142.69 | 312.05 | 62.97% zero |
| `mg_fast_anchor_count` | float64 | context | 0.0 | 0 | 0 | 12.61 | 25.00 | 72.04% zero |
| `mg_fast_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.008718 | 0.03366 | 73.55% zero |
| `mg_fast_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.06432 | 0.1792 | 73.55% zero |
| `mg_fast_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.07379 | 0.3034 | 72.21% zero |
| `mg_fast_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.04812 | 0.1763 | 72.04% zero |
| `mg_fast_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.3334 | 0.7768 | 72.71% zero |
| `mg_fast_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 0.8578 | 1.79 | 72.12% zero |
| `mg_fast_n` | float64 | context | 0.0 | 0 | 0 | 7 | 90 | 69.27% zero |
| `mg_fast_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 90.26% zero |
| `mg_fast_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 97.73% zero |
| `mg_fast_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.249 | 1 | 81.78% zero |
| `mg_fast_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.1429 | 1 | 84.89% zero |
| `mg_fast_walkability` | float64 | context | 0.0 | 0 | 0 | 39.40 | 212.90 | 72.04% zero |
| `mg_fitn_anchor_count` | float64 | context | 0.0 | 0 | 0 | 18 | 25.00 | 65.41% zero |
| `mg_fitn_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0131 | 0.09607 | 68.09% zero |
| `mg_fitn_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.0882 | 0.5629 | 68.09% zero |
| `mg_fitn_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.09565 | 0.1825 | 67.0% zero |
| `mg_fitn_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08274 | 0.7109 | 65.41% zero |
| `mg_fitn_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.533 | 0.8128 | 68.01% zero |
| `mg_fitn_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.26 | 1.79 | 65.66% zero |
| `mg_fitn_n` | float64 | context | 0.0 | 0 | 0 | 10 | 101 | 63.22% zero |
| `mg_fitn_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 90.93% zero |
| `mg_fitn_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 97.98% zero |
| `mg_fitn_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.2491 | 1 | 80.27% zero |
| `mg_fitn_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.4506 | 1 | 70.95% zero |
| `mg_fitn_walkability` | float64 | context | 0.0 | 0 | 0 | 116.87 | 260.50 | 65.41% zero |
| `mg_hawk_anchor_count` | float64 | context | 0.0 | 0 | 0 | 16.43 | 25.00 | 69.52% zero |
| `mg_hawk_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01207 | 0.02617 | 71.62% zero |
| `mg_hawk_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.09036 | 0.182 | 71.62% zero |
| `mg_hawk_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.09464 | 0.2919 | 69.69% zero |
| `mg_hawk_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.06217 | 0.6779 | 69.52% zero |
| `mg_hawk_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.4322 | 0.7742 | 70.28% zero |
| `mg_hawk_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.08 | 1.79 | 69.52% zero |
| `mg_hawk_n` | float64 | context | 0.0 | 0 | 0 | 16 | 273 | 67.17% zero |
| `mg_hawk_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.02219 | 0.9955 | 89.42% zero |
| `mg_hawk_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 98.07% zero |
| `mg_hawk_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.2948 | 1 | 80.27% zero |
| `mg_hawk_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.2153 | 1 | 81.53% zero |
| `mg_hawk_walkability` | float64 | context | 0.0 | 0 | 0 | 52.56 | 267.08 | 69.52% zero |
| `mg_heal_anchor_count` | float64 | context | 0.0 | 0 | 0 | 14.57 | 24.79 | 70.53% zero |
| `mg_heal_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.01397 | 0.04019 | 73.22% zero |
| `mg_heal_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1048 | 0.1716 | 73.22% zero |
| `mg_heal_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.02952 | 0.1028 | 75.31% zero |
| `mg_heal_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.07909 | 0.5 | 70.53% zero |
| `mg_heal_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.553 | 0.8697 | 71.37% zero |
| `mg_heal_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.23 | 1.79 | 70.61% zero |
| `mg_heal_n` | float64 | context | 0.0 | 0 | 0 | 14 | 414 | 68.85% zero |
| `mg_heal_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.0481 | 1 | 88.83% zero |
| `mg_heal_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 1 | 97.57% zero |
| `mg_heal_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.3038 | 1 | 79.76% zero |
| `mg_heal_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.2641 | 1 | 77.58% zero |
| `mg_heal_walkability` | float64 | context | 0.0 | 0 | 0 | 89.15 | 205.04 | 70.53% zero |
| `mg_rest_anchor_count` | float64 | context | 0.0 | 0 | 0 | 21.89 | 25.00 | 58.19% zero |
| `mg_rest_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.0181 | 0.1333 | 61.13% zero |
| `mg_rest_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1385 | 0.344 | 61.13% zero |
| `mg_rest_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1221 | 0.3413 | 59.61% zero |
| `mg_rest_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.08585 | 0.8015 | 58.19% zero |
| `mg_rest_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.5689 | 0.7721 | 61.21% zero |
| `mg_rest_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.45 | 1.79 | 58.52% zero |
| `mg_rest_n` | float64 | context | 0.0 | 0 | 0 | 29 | 979 | 56.0% zero |
| `mg_rest_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.07099 | 1 | 87.49% zero |
| `mg_rest_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 0.9403 | 97.4% zero |
| `mg_rest_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.381 | 1 | 74.64% zero |
| `mg_rest_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.4948 | 1 | 64.23% zero |
| `mg_rest_walkability` | float64 | context | 0.0 | 0 | 0 | 89.96 | 275.30 | 58.19% zero |
| `mg_shop_anchor_count` | float64 | context | 0.0 | 0 | 0 | 24.36 | 25.00 | 53.9% zero |
| `mg_shop_comp_pressure` | float64 | context | 0.0 | 0 | 0 | 0.02076 | 0.2087 | 55.92% zero |
| `mg_shop_cv_competitor` | float64 | context | 0.0 | 0 | 0 | 0.1624 | 0.5541 | 55.92% zero |
| `mg_shop_cv_complementary` | float64 | context | 0.0 | 0 | 0 | 0.1108 | 0.2247 | 56.84% zero |
| `mg_shop_cv_demand` | float64 | context | 0.0 | 0 | 0 | 0.1008 | 0.47 | 53.9% zero |
| `mg_shop_cv_transit` | float64 | context | 0.0 | 0 | 0 | 0.6359 | 0.7826 | 58.1% zero |
| `mg_shop_demand_diversity` | float64 | context | 0.0 | 0 | 0 | 1.59 | 1.79 | 54.07% zero |
| `mg_shop_n` | float64 | context | 0.0 | 0 | 0 | 44 | 943 | 52.06% zero |
| `mg_shop_pct_dense` | float64 | context | 0.0 | 0 | 0 | 0.07557 | 0.9793 | 86.99% zero |
| `mg_shop_pct_hyperdense` | float64 | context | 0.0 | 0 | 0 | 0 | 0.9854 | 97.4% zero |
| `mg_shop_pct_moderate` | float64 | context | 0.0 | 0 | 0 | 0.3728 | 1 | 74.14% zero |
| `mg_shop_pct_sparse` | float64 | context | 0.0 | 0 | 0 | 0.6896 | 1 | 57.85% zero |
| `mg_shop_walkability` | float64 | context | 0.0 | 0 | 0 | 136.63 | 265.30 | 53.9% zero |

### saturation_gap — Supply-demand saturation + gaps  (14 cols · Stage 11 / 14b)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gap_cafe` | float64 | count deficit | 49.62 | -253.62 | 0.4528 | 5.59 | 23.69 |  |
| `gap_commercial` | float64 | count deficit | 0.0 | -0.1556 | 0 | 0.04403 | 0.6858 | 66.75% zero |
| `gap_convenience` | float64 | count deficit | 49.62 | -93.23 | 0.6199 | 6.27 | 22.71 |  |
| `gap_fnb` | float64 | count deficit | 49.62 | -1,856 | 2.02 | 25.51 | 107.89 |  |
| `gap_health` | float64 | count deficit | 49.62 | -576.80 | 0.4497 | 4.37 | 16.97 |  |
| `gap_industrial` | float64 | count deficit | 0.0 | -0.02649 | 0 | 0.8019 | 1 | 56.84% zero |
| `gap_residential` | float64 | count deficit | 0.0 | -0.09928 | 0 | 0.5143 | 0.8254 | 60.29% zero |
| `gap_restaurant` | float64 | count deficit | 49.62 | -1,196 | 1.06 | 14.42 | 61.15 |  |
| `saturation_cafe` | float64 | ratio | 49.62 | 0 | 0.697 | 4.32 | 5 |  |
| `saturation_convenience` | float64 | ratio | 49.62 | 0 | 0.7265 | 3.03 | 5 |  |
| `saturation_fnb` | float64 | ratio | 49.62 | 0 | 0.7451 | 4.44 | 5 |  |
| `saturation_health` | float64 | ratio | 49.62 | 0 | 0.5798 | 3.99 | 5 |  |
| `saturation_restaurant` | float64 | ratio | 49.62 | 0 | 0.7048 | 5 | 5 |  |
| `ura_development_gap` | float64 | — | 0.0 | -0.4849 | 0.1657 | 0.6319 | 1 |  |

### spatial_rings — Spatial neighborhood rings  (61 cols · Stage 12)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `sp_max_avg_gpr` | float64 | ring agg | 0.0 | 0 | 2.04 | 4.04 | 14.70 |  |
| `sp_max_bldg_count` | float64 | ring agg | 0.0 | 0 | 45 | 105 | 350 |  |
| `sp_max_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 38,603 | 65,311 | 213,913 |  |
| `sp_max_bus_stops` | float64 | ring agg | 0.0 | 0 | 2 | 4 | 13 |  |
| `sp_max_children_count` | float64 | ring agg | 0.0 | 0 | 0 | 550.67 | 1,743 | 55.67% zero |
| `sp_max_distance_rings` | float64 | ring agg | 0.0 | 1 | 5 | 5 | 5 |  |
| `sp_max_elderly_count` | float64 | ring agg | 0.0 | 0 | 0 | 847.72 | 1,921 | 55.42% zero |
| `sp_max_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 0 | 17 | 27 | 64.15% zero |
| `sp_max_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.805 | 1 | 56.93% zero |
| `sp_max_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.487 | 0.9317 | 52.39% zero |
| `sp_max_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.5735 | 1 | 55.33% zero |
| `sp_max_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 5.85 | 16 | 16.95 |  |
| `sp_max_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.4526 | 0.8941 | 1.00 |  |
| `sp_max_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.006541 | 0.2607 | 1 |  |
| `sp_max_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.1436 | 0.4231 | 1.00 |  |
| `sp_max_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0 | 0.351 | 1 | 57.77% zero |
| `sp_max_mrt_stations` | float64 | ring agg | 0.0 | 0 | 0 | 1 | 3 | 70.95% zero |
| `sp_max_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 1 | 6 | 65 |  |
| `sp_max_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 4 | 28 | 68 |  |
| `sp_max_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 2 | 32 | 91 |  |
| `sp_max_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 2.15 | 2.56 | 2.75 |  |
| `sp_max_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 2 | 33 | 88 |  |
| `sp_max_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 2 | 25 | 255 |  |
| `sp_max_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 1 | 8 | 27 |  |
| `sp_max_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 10 | 104 | 243 |  |
| `sp_max_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 13 | 131 | 376 |  |
| `sp_max_pc_total` | float64 | ring agg | 0.0 | 0 | 100 | 554 | 1,356 |  |
| `sp_max_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 4 | 89 | 194 |  |
| `sp_max_population` | float64 | ring agg | 0.0 | 0 | 0 | 4,322 | 10,175 | 55.42% zero |
| `sp_max_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 0 | 227,504 | 548,349 | 51.81% zero |
| `sp_max_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 0 | 1,322 | 3,173 | 55.42% zero |
| `sp_pw_avg_gpr` | float64 | ring agg | 0.0 | 0 | 1.46 | 2.82 | 11.89 |  |
| `sp_pw_bldg_count` | float64 | ring agg | 0.0 | 0 | 289.13 | 544.53 | 1,329 |  |
| `sp_pw_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 190,783 | 286,492 | 493,545 |  |
| `sp_pw_bus_stops` | float64 | ring agg | 0.0 | 0 | 7.25 | 16.68 | 30.20 |  |
| `sp_pw_children_count` | float64 | ring agg | 0.0 | 0 | 92.45 | 2,508 | 6,209 |  |
| `sp_pw_elderly_count` | float64 | ring agg | 0.0 | 0 | 135.72 | 3,626 | 6,551 |  |
| `sp_pw_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 0.5341 | 69.58 | 126.64 |  |
| `sp_pw_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.06694 | 0.727 | 1 |  |
| `sp_pw_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.008757 | 0.1403 | 0.5079 |  |
| `sp_pw_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.06976 | 0.4563 | 0.6849 |  |
| `sp_pw_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 3.41 | 11.23 | 14.56 |  |
| `sp_pw_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.4322 | 0.5768 | 0.8188 |  |
| `sp_pw_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.02688 | 0.1635 | 0.5919 |  |
| `sp_pw_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.1644 | 0.2875 | 0.7424 |  |
| `sp_pw_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0.01481 | 0.1445 | 0.5 |  |
| `sp_pw_mrt_stations` | float64 | ring agg | 0.0 | 0 | 0.08785 | 1.93 | 5.18 |  |
| `sp_pw_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 2.46 | 13.67 | 192.96 |  |
| `sp_pw_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 7.62 | 46.68 | 248.16 |  |
| `sp_pw_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 4.79 | 72.73 | 212.94 |  |
| `sp_pw_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 11.11 | 16.45 | 17.34 |  |
| `sp_pw_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 4.18 | 52.29 | 142.63 |  |
| `sp_pw_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 2.93 | 53.52 | 585.16 |  |
| `sp_pw_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 2.87 | 18.94 | 69.81 |  |
| `sp_pw_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 21.01 | 169.69 | 869.11 |  |
| `sp_pw_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 29.51 | 256.23 | 1,214 |  |
| `sp_pw_pc_total` | float64 | ring agg | 0.0 | 0 | 208.91 | 1,294 | 5,397 |  |
| `sp_pw_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 9.60 | 125.72 | 495.06 |  |
| `sp_pw_population` | float64 | ring agg | 0.0 | 0 | 729.20 | 18,680 | 34,922 |  |
| `sp_pw_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 108,180 | 1,002,905 | 1,734,093 |  |
| `sp_pw_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 220.11 | 6,051 | 11,026 |  |

### transit_rings — Transit-graph rings  (62 cols · Stage 12)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `tr_max_avg_gpr` | float64 | ring agg | 0.0 | 0 | 3.41 | 14.70 | 14.70 |  |
| `tr_max_bldg_count` | float64 | ring agg | 0.0 | 0 | 28 | 58 | 284 |  |
| `tr_max_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 43,504 | 67,656 | 81,558 |  |
| `tr_max_bus_stops` | float64 | ring agg | 0.0 | 0 | 2 | 6 | 13 |  |
| `tr_max_children_count` | float64 | ring agg | 0.0 | 0 | 18.98 | 407.79 | 1,096 |  |
| `tr_max_elderly_count` | float64 | ring agg | 0.0 | 0 | 34.80 | 858.87 | 1,921 |  |
| `tr_max_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 2 | 14 | 20 |  |
| `tr_max_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.6779 | 0.7155 | 68.93% zero |
| `tr_max_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.3255 | 0.5226 | 0.9317 |  |
| `tr_max_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.05816 | 0.3214 | 0.6585 |  |
| `tr_max_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 15.61 | 16.27 | 16.95 |  |
| `tr_max_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.3998 | 0.4808 | 0.8941 |  |
| `tr_max_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.1855 | 0.2607 | 0.3318 |  |
| `tr_max_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.1632 | 0.1983 | 0.3886 |  |
| `tr_max_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0.2749 | 0.3836 | 0.4488 |  |
| `tr_max_mrt_stations` | float64 | ring agg | 0.0 | 0 | 1 | 2 | 2 |  |
| `tr_max_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 3 | 27 | 29 |  |
| `tr_max_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 17 | 68 | 68 |  |
| `tr_max_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 29 | 38 | 55 |  |
| `tr_max_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 2.26 | 2.53 | 2.57 |  |
| `tr_max_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 9 | 33 | 47 |  |
| `tr_max_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 20 | 74 | 134 |  |
| `tr_max_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 2 | 24 | 26 |  |
| `tr_max_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 104 | 172 | 219 |  |
| `tr_max_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 113 | 152 | 376 |  |
| `tr_max_pc_total` | float64 | ring agg | 0.0 | 0 | 462 | 1,356 | 1,356 |  |
| `tr_max_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 78 | 143 | 194 |  |
| `tr_max_population` | float64 | ring agg | 0.0 | 0 | 164.51 | 4,141 | 8,832 |  |
| `tr_max_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 41,158 | 227,504 | 548,349 |  |
| `tr_max_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 53.78 | 1,267 | 3,017 |  |
| `tr_nearest_station_rings` | float64 | ring agg | 0.0 | 0 | 5 | 25 | 999 |  |
| `tr_pw_avg_gpr` | float64 | ring agg | 0.0 | 0 | 2.70 | 3.67 | 5.53 |  |
| `tr_pw_bldg_count` | float64 | ring agg | 0.0 | 0 | 323.02 | 608.40 | 703.29 |  |
| `tr_pw_bldg_footprint_sqm` | float64 | m² | 0.0 | 0 | 233,601 | 313,155 | 332,445 |  |
| `tr_pw_bus_stops` | float64 | ring agg | 0.0 | 0 | 15.49 | 17.98 | 21.79 |  |
| `tr_pw_children_count` | float64 | ring agg | 0.0 | 0 | 1,470 | 2,948 | 5,390 |  |
| `tr_pw_elderly_count` | float64 | ring agg | 0.0 | 0 | 2,301 | 4,040 | 4,807 |  |
| `tr_pw_hdb_blocks` | float64 | ring agg | 0.0 | 0 | 41.87 | 76.72 | 107.17 |  |
| `tr_pw_lu_business_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.1026 | 0.4609 | 0.7378 |  |
| `tr_pw_lu_commercial_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.09864 | 0.2314 | 0.3317 |  |
| `tr_pw_lu_residential_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0.3378 | 0.4806 | 0.5128 |  |
| `tr_pw_mg_mean_anchor_count` | float64 | ring agg | 0.0 | 0 | 10.33 | 12.38 | 13.86 |  |
| `tr_pw_mg_mean_competitor` | float64 | ring agg | 0.0 | 0 | 0.492 | 0.5324 | 0.5698 |  |
| `tr_pw_mg_mean_complementary` | float64 | ring agg | 0.0 | 0 | 0.1211 | 0.1491 | 0.1886 |  |
| `tr_pw_mg_mean_demand` | float64 | ring agg | 0.0 | 0 | 0.2222 | 0.2533 | 0.2814 |  |
| `tr_pw_mg_mean_transit` | float64 | ring agg | 0.0 | 0 | 0.1325 | 0.172 | 0.236 |  |
| `tr_pw_mrt_stations` | float64 | ring agg | 0.0 | 0 | 1.40 | 2.60 | 3.44 |  |
| `tr_pw_pc_cat_bar_nightlife` | float64 | ring agg | 0.0 | 0 | 6.20 | 57.03 | 133.64 |  |
| `tr_pw_pc_cat_cafe_coffee` | float64 | ring agg | 0.0 | 0 | 35.53 | 97.27 | 173.21 |  |
| `tr_pw_pc_cat_education` | float64 | ring agg | 0.0 | 0 | 55.31 | 100.24 | 156.64 |  |
| `tr_pw_pc_cat_entropy` | float64 | ring agg | 0.0 | 0 | 16.03 | 16.57 | 17.16 |  |
| `tr_pw_pc_cat_hawker_street_food` | float64 | ring agg | 0.0 | 0 | 39.04 | 61.59 | 89.70 |  |
| `tr_pw_pc_cat_health_medical` | float64 | ring agg | 0.0 | 0 | 44.28 | 172.76 | 265.95 |  |
| `tr_pw_pc_cat_office_workspace` | float64 | ring agg | 0.0 | 0 | 8.48 | 29.46 | 37.43 |  |
| `tr_pw_pc_cat_restaurant` | float64 | ring agg | 0.0 | 0 | 117.63 | 363.15 | 670.54 |  |
| `tr_pw_pc_cat_shopping_retail` | float64 | ring agg | 0.0 | 0 | 175.51 | 497.01 | 711.55 |  |
| `tr_pw_pc_total` | float64 | ring agg | 0.0 | 0 | 933.99 | 2,444 | 4,076 |  |
| `tr_pw_pc_unique_brands` | float64 | ring agg | 0.0 | 0 | 102.65 | 188.58 | 269.45 |  |
| `tr_pw_population` | float64 | ring agg | 0.0 | 0 | 11,713 | 22,356 | 30,413 |  |
| `tr_pw_residential_floor_area_sqm` | float64 | m² | 0.0 | 0 | 672,952 | 1,134,716 | 1,518,027 |  |
| `tr_pw_walking_dependent_count` | float64 | ring agg | 0.0 | 0 | 3,779 | 7,081 | 9,266 |  |
| `tr_reachable_hexes` | float64 | ring agg | 0.0 | 0 | 184 | 410.85 | 625.71 |  |

### composites — Composite indices  (8 cols · Stage 16)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `idx_accessibility` | float64 | score [0,1] | 34.51 | 0.05144 | 0.4831 | 0.6851 | 0.9045 |  |
| `idx_competition` | float64 | score [0,1] | 0.0 | 0 | 0.0001329 | 0.01124 | 1 |  |
| `idx_demand` | float64 | score [0,1] | 0.0 | 0 | 0.01671 | 0.2676 | 0.6223 |  |
| `idx_growth_potential` | float64 | score [0,1] | 2.27 | 0.05244 | 0.3989 | 0.4824 | 0.7 |  |
| `idx_redevelopment_pressure` | float64 | score [0,1] | 0.0 | 0.02325 | 0.4 | 0.4141 | 0.8192 |  |
| `idx_residential_quality` | float64 | score [0,1] | 0.0 | 0 | 0.2 | 0.5268 | 0.7925 |  |
| `idx_urban_intensity` | float64 | score [0,1] | 0.0 | 0 | 0.02353 | 0.2315 | 0.7127 |  |
| `idx_vitality` | float64 | score [0,1] | 0.0 | 0 | 0.01816 | 0.2356 | 0.8523 |  |

### proxies — Proxies  (4 cols · Stage 16)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `proxy_daytime_pop` | float64 | proxy | 0.0 | 0 | 20 | 1,490 | 16,794 |  |
| `proxy_footfall` | float64 | proxy | 0.0 | 0 | 0.03421 | 0.1909 | 0.6278 |  |
| `proxy_night_economy` | float64 | proxy | 0.0 | 0 | 0 | 25 | 1,037 | 57.09% zero |
| `proxy_tourism` | float64 | proxy | 0.0 | 0 | 0 | 6.63 | 396.58 | 64.74% zero |

### influence — Influence (cross-scale, no leakage)  (6 cols · Stage 14)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `ecosystem_completeness` | float64 | unitless | 0.0 | 0 | 0.1429 | 0.8571 | 1 |  |
| `gradient_position` | float64 | unitless | 0.0 | -3.90 | -0.3836 | 1.19 | 23.36 |  |
| `interface_score` | float64 | score [0,1] | 0.0 | 0 | 0.1667 | 0.6667 | 1 |  |
| `net_demand_flow` | float64 | fraction [0,1] | 0.0 | -0.8393 | 8.13e-05 | 0.3879 | 0.9851 |  |
| `place_clustering` | float64 | unitless | 0.0 | 0 | 0.4085 | 0.7685 | 0.8571 |  |
| `self_containment` | float64 | unitless | 0.0 | 0 | 0 | 0.75 | 1 | 65.66% zero |

### archetype — Archetype / character  (3 cols · Stage 19)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `archetype` | str | categorical | 0.0 | — | — | — | — |  |
| `archetype_confidence` | float64 | score [0,1] | 0.0 | 0 | 0.8763 | 0.9301 | 0.968 |  |
| `archetype_id` | int32 | categorical | 0.0 | 0 | 4 | 6 | 6 |  |

### amenities — Amenity counts at hex  (19 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `amenity_types_nearby` | float64 | count | 0.0 | 0 | 0.8571 | 5.41 | 6.00 |  |
| `chas_clinics` | float64 | count | 0.0 | 0 | 0 | 4 | 20 | 76.74% zero |
| `clinics` | float64 | count | 0.0 | 0 | 0 | 4 | 20 | 76.74% zero |
| `formal_schools` | float64 | count | 0.0 | 0 | 0 | 1 | 5 | 84.72% zero |
| `hawker_centres` | float64 | count | 0.0 | 0 | 0 | 0 | 6 | 91.77% zero |
| `hotels` | float64 | count | 0.0 | 0 | 0 | 0 | 43 | 93.12% zero |
| `park_facilities` | float64 | count | 0.0 | 0 | 0 | 15 | 133 | 67.59% zero |
| `parks` | float64 | count | 0.0 | 0 | 0 | 1 | 9 | 80.52% zero |
| `parks_nature` | float64 | count | 0.0 | 0 | 0 | 1 | 9 | 80.35% zero |
| `preschools_gov` | float64 | count | 0.0 | 0 | 0 | 8 | 26 | 70.45% zero |
| `school_zones` | float64 | count | 0.0 | 0 | 0 | 1 | 4 | 86.99% zero |
| `schools_primary` | float64 | count | 0.0 | 0 | 0 | 1 | 3 | 87.83% zero |
| `schools_secondary` | float64 | count | 0.0 | 0 | 0 | 0 | 3 | 90.43% zero |
| `sfa_eating_count` | float64 | count | 0.0 | 0 | 0 | 88 | 911 | 52.14% zero |
| `sfa_eating_establishments` | float64 | count | 0.0 | 0 | 0 | 89 | 922 | 52.23% zero |
| `silver_zones` | float64 | count | 0.0 | 0 | 0 | 0 | 2 | 96.81% zero |
| `supermarkets` | float64 | count | 0.0 | 0 | 0 | 2 | 7 | 78.0% zero |
| `tourist_attractions` | float64 | count | 0.0 | 0 | 0 | 0 | 16 | 96.31% zero |
| `tourist_draw_est` | float64 | count | 0.0 | 0 | 5 | 350 | 13,330 |  |

### roads_signals — Roads + signals + pedestrian  (16 cols · Stage 6)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `bicycle_signal` | float64 | — | 0.0 | 0 | 0 | 0 | 4 | 98.91% zero |
| `ped_countdown` | float64 | count | 0.0 | 0 | 0 | 4 | 34 | 84.72% zero |
| `ped_crossings_total` | float64 | count | 0.0 | 0 | 0 | 42 | 122 | 56.0% zero |
| `ped_elderly` | float64 | count | 0.0 | 0 | 0 | 0 | 12 | 95.13% zero |
| `ped_standard` | float64 | count | 0.0 | 0 | 0 | 35 | 104 | 56.34% zero |
| `road_cat_arterial` | float64 | count/km | 0.0 | 0 | 0 | 0 | 59 | 92.7% zero |
| `road_cat_expressway` | float64 | count/km | 0.0 | 0 | 0 | 10 | 40 | 84.38% zero |
| `road_cat_major_arterial` | float64 | count/km | 0.0 | 0 | 0 | 10 | 129 | 82.12% zero |
| `road_cat_minor_arterial` | float64 | count/km | 0.0 | 0 | 0 | 5 | 79 | 86.31% zero |
| `road_cat_slip` | float64 | count/km | 0.0 | 0 | 0 | 6 | 48 | 79.76% zero |
| `road_cat_small` | float64 | count/km | 0.0 | 0 | 0 | 4 | 154 | 87.15% zero |
| `sig_beacon` | float64 | count | 0.0 | 0 | 0 | 16 | 65 | 61.38% zero |
| `sig_filter_arrow` | float64 | count | 0.0 | 0 | 0 | 9 | 47 | 71.54% zero |
| `sig_ground` | float64 | count | 0.0 | 0 | 0 | 51 | 133 | 55.67% zero |
| `sig_overhead` | float64 | count | 0.0 | 0 | 0 | 16 | 34 | 56.84% zero |
| `sig_rag` | float64 | count | 0.0 | 0 | 0 | 6 | 35 | 75.31% zero |

### satellite — Satellite (VIIRS / GHSL / WorldPop / WorldCover)  (16 cols · Stage 5b)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `ghsl_built_change` | float64 | built-up idx | 100.0 | — | — | — | — |  |
| `ghsl_built_growth_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_est_floors` | float64 | floors | 100.0 | — | — | — | — |  |
| `ghsl_height` | float64 | meters | 100.0 | — | — | — | — |  |
| `ghsl_is_highrise` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `ghsl_is_new_dev` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `nl_2022` | float64 | radiance | 1.01 | 1.86 | 33.65 | 78.88 | 406.04 |  |
| `nl_2024` | float64 | radiance | 2.85 | 1.98 | 36.05 | 88.30 | 372.34 |  |
| `nl_change_pct` | float64 | fraction [0,1] | 2.27 | -62.39 | 1.39 | 28.68 | 745.23 |  |
| `nl_commercial_indicator` | float64 | radiance | 0.0 | -0.8213 | 0.01839 | 0.1715 | 0.9633 |  |
| `nl_decline_zone` | int64 | radiance | 0.0 | 0 | 0 | 0 | 1 | 90.18% zero |
| `nl_growth_corridor` | int64 | radiance | 0.0 | 0 | 0 | 1 | 1 | 84.55% zero |
| `nl_per_capita` | float64 | radiance | 0.0 | 0 | 2.91 | 72.55 | 1,377 |  |
| `worldpop_2020` | float64 | — | 68.6 | 0.7822 | 115.27 | 229.86 | 729.77 |  |
| `worldpop_2025` | float64 | — | 68.6 | 0.7822 | 115.27 | 229.86 | 729.77 |  |
| `wp_pop_growth_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |

### property — Property  (2 cols · Stage 17)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `hdb_median_psf` | float64 | SGD/sqft | 0.0 | 0 | 0 | 641.27 | 923.86 | 68.09% zero |
| `hdb_pop_share` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 0.7049 | 0.8712 | 76.07% zero |

### osm_poi — OSM POI  (4 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `osm_amenities` | float64 | count | 0.0 | 0 | 1 | 72 | 937 |  |
| `osm_leisure` | float64 | count | 0.0 | 0 | 0 | 36 | 141 | 54.91% zero |
| `osm_shops` | float64 | count | 0.0 | 0 | 0 | 15 | 331 | 65.24% zero |
| `osm_tourism` | float64 | count | 0.0 | 0 | 0 | 4 | 182 | 72.71% zero |

### dynamic_lta — Dynamic LTA (live)  (18 cols · Stage 14c)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `carpark_count` | float64 | count | 0.0 | 0 | 0 | 8 | 45 | 75.9% zero |
| `carpark_lots` | float64 | count | 0.0 | 0 | 0 | 1,374 | 7,896 | 75.99% zero |
| `dyn_avg_speed` | float64 | km/h | 0.0 | 0 | 24.50 | 68.10 | 534.50 |  |
| `dyn_car_dependency` | float64 | — | 0.0 | 0 | 0 | 90.20 | 100 | 75.9% zero |
| `dyn_carpark_available` | float64 | — | 0.0 | 0 | 0 | 1,688 | 11,644 | 75.9% zero |
| `dyn_carpark_count` | float64 | count | 0.0 | 0 | 0 | 8 | 48 | 75.73% zero |
| `dyn_carpark_per_1000pop` | float64 | — | 0.0 | 0 | 0 | 99.75 | 149,057 | 75.9% zero |
| `dyn_pct_jammed` | float64 | fraction [0,1] | 0.0 | 0 | 2.60 | 37.10 | 100 |  |
| `dyn_taxi_count` | float64 | count | 0.0 | 0 | 0 | 9 | 147 | 67.76% zero |
| `dyn_taxi_density` | float64 | — | 0.0 | 0 | 0 | 10.74 | 175.72 | 67.76% zero |
| `dyn_traffic_segs` | float64 | — | 0.0 | 0 | 11 | 133 | 308 |  |
| `hex_avg_speed_kmh` | float64 | km/h | 0.0 | 0 | 0 | 30.27 | 70 | 72.38% zero |
| `hex_flow_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 24.07 | 100 | 76.15% zero |
| `hex_flow_segments` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 15 | 67 | 74.98% zero |
| `hex_jam_pct` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 14.26 | 74.49 | 81.61% zero |
| `hex_jam_segments` | float64 | fraction [0,1] | 0.0 | 0 | 0 | 6 | 109 | 80.69% zero |
| `hex_seg_count` | float64 | count | 0.0 | 0 | 0 | 44 | 272 | 71.2% zero |
| `taxi_snapshot` | float64 | — | 0.0 | 0 | 0 | 1 | 14 | 80.94% zero |

### infra_misc — Park connectors + F&B roll-up + density  (5 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `fnb_total` | float64 | count | 0.0 | 0 | 0 | 82 | 1,883 | 51.55% zero — F&B total roll-up |
| `park_connector_segments` | float64 | count | 0.0 | 0 | 0 | 2 | 38 | 83.71% zero |
| `pcn_segments` | float64 | count | 0.0 | 0 | 0 | 2 | 37 | 82.62% zero |
| `places_per_1000_resident` | float64 | per-capita density | 0.0 | 0 | 28.29 | 24,000 | 1,214,000 | inflated in near-zero-resident industrial hexes |
| `places_per_1000_total` | float64 | per-capita density | 0.0 | 0 | 11.83 | 1,000 | 89,000 | uses pop_total |

---

## 3. places_featured.parquet — 174,711 rows × 114 cols

### identity — Identity / location metadata  (13 cols · Stage 0)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `address` | str | string | 0.0 | — | — | — | — |  |
| `brand_name` | str | string | 0.0 | — | — | — | — |  |
| `confidence` | float64 | score [0,1] | 0.0 | 0.5185 | 0.9389 | 0.9765 | 1 |  |
| `h3_res8` | str | — | 0.0 | — | — | — | — |  |
| `h3_res9` | str | — | 0.0 | — | — | — | — |  |
| `is_branded` | int64 | 0/1 | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `latitude` | float64 | degrees EPSG:4326 | 0.0 | 1.20 | 1.33 | 1.42 | 1.47 |  |
| `longitude` | float64 | degrees EPSG:4326 | 0.0 | 103.60 | 103.85 | 103.91 | 104.05 |  |
| `main_category` | str | categorical | 0.0 | — | — | — | — |  |
| `name` | str | string | 0.0 | — | — | — | — |  |
| `place_id` | str | string | 0.0 | — | — | — | — |  |
| `place_type` | str | categorical | 0.0 | — | — | — | — |  |
| `price_tier` | str | categorical | 0.0 | — | — | — | — |  |

### buildings — Built environment / physical form  (8 cols · Stage 2)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `bld_avg_floors` | float64 | varies | 0.0 | 0 | 5.77 | 13.83 | 60 |  |
| `bld_bldg_count` | float64 | count | 0.0 | 0 | 46 | 177 | 518 |  |
| `bld_hdb_blocks` | float64 | varies | 0.0 | 0 | 0 | 13 | 109 | 56.22% zero |
| `bld_lu_business` | float64 | varies | 0.0 | 0 | 0 | 0.6241 | 1 | 71.68% zero |
| `bld_lu_commercial` | float64 | varies | 0.0 | 0 | 0.035 | 0.4843 | 0.9317 |  |
| `bld_lu_entropy` | float64 | varies | 0.0 | 0 | 1.12 | 1.44 | 1.83 |  |
| `bld_lu_residential` | float64 | varies | 0.0 | 0 | 0.1682 | 0.6658 | 1 |  |
| `bld_max_floors` | float64 | varies | 0.0 | 0 | 12 | 36 | 70 |  |

### transit — Transit network + ridership  (2 cols · Stage 5)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `transit_daily_taps` | float64 | daily taps | 0.0 | 0 | 1,597 | 46,613 | 198,622 |  |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.586e-55 | 0.4736 | 0.7785 | 1 |  |

### gtfs — GTFS schedule-derived frequency  (2 cols · Stage 5)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gtfs_headway_am_min` | float64 | minutes | 0.0 | 3.05 | 39.60 | 60 | 99,999 |  |
| `gtfs_routes_served` | float64 | count | 0.0 | 0 | 6 | 17 | 50 |  |

### walk_network — Walkability scores (network graph)  (4 cols · Stage 6+8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `nwalk_bus_m` | float64 | meters | 0.0 | 0 | 192.92 | 512.40 | 99,999 |  |
| `nwalk_bus_score` | float64 | score [0,1] | 0.0 | 0 | 0.7857 | 0.9461 | 1 |  |
| `nwalk_mrt_m` | float64 | meters | 0.0 | 0 | 658.39 | 2,096 | 99,999 |  |
| `nwalk_mrt_score` | float64 | score [0,1] | 0.0 | 0 | 0.4591 | 0.8377 | 99,999 |  |

### demand_pull — Demand pull (distance-decay weighted)  (7 cols · Stage 9)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `pull_hawker` | float64 | pull units | 0.0 | 0 | 0.1968 | 1.31 | 3.13 |  |
| `pull_hotel` | float64 | pull units | 0.0 | 0 | 0 | 21.65 | 39.67 | 51.94% zero |
| `pull_office` | float64 | pull units | 0.0 | 0 | 45.27 | 344.33 | 960.47 |  |
| `pull_residential` | float64 | pull units | 0.0 | 0 | 7,344 | 21,693 | 39,036 |  |
| `pull_school` | float64 | pull units | 0.0 | 0 | 0.4735 | 1.88 | 3.95 |  |
| `pull_total_pop` | float64 | pull units | 0.0 | 0 | 12,090 | 25,649 | 44,684 |  |
| `pull_transit` | float64 | pull units | 0.0 | 0 | 29,672 | 108,132 | 223,618 |  |

### synergy — Synergy (category × pull)  (10 cols · Stage 10)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `synergy_cafe_office` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 960.47 | 96.35% zero |
| `synergy_convenience_transit` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 223,618 | 96.64% zero |
| `synergy_education` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 3.95 | 95.27% zero |
| `synergy_financial` | float64 | synergy units | 0.0 | 0 | 0 | 96.62 | 960.47 | 81.39% zero |
| `synergy_grocery_residential` | float64 | synergy units | 0.0 | 0 | 0 | 7,084 | 39,036 | 82.47% zero |
| `synergy_health_cluster` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 39,036 | 95.65% zero |
| `synergy_lifestyle` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 39,036 | 96.6% zero |
| `synergy_morning` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 194,492 | 98.67% zero |
| `synergy_nightlife` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 39.67 | 98.74% zero |
| `synergy_restaurant_hotel` | float64 | synergy units | 0.0 | 0 | 0 | 0 | 39.67 | 92.88% zero |

### saturation_gap — Supply-demand saturation + gaps  (3 cols · Stage 11 / 14b)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `gap_fill_score` | float64 | score [0,1] | 0.0 | 0 | 0.5 | 0.5 | 1 |  |
| `gap_own_category` | float64 | count deficit | 69.6 | -1,856 | -46.72 | 4.69 | 107.89 |  |
| `saturation_own_category` | float64 | ratio | 69.6 | 0 | 3.69 | 5 | 5 |  |

### composites — Composite indices  (5 cols · Stage 16)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `idx_accessibility` | float64 | score [0,1] | 0.0 | 0 | 0.6679 | 0.742 | 0.9045 |  |
| `idx_demand` | float64 | score [0,1] | 0.0 | 0 | 0.2768 | 0.4698 | 0.6223 |  |
| `idx_growth_potential` | float64 | score [0,1] | 0.0 | 0 | 0.296 | 0.4456 | 0.7 |  |
| `idx_urban_intensity` | float64 | score [0,1] | 0.0 | 0 | 0.235 | 0.4389 | 0.7127 |  |
| `idx_vitality` | float64 | score [0,1] | 0.0 | 0 | 0.2661 | 0.6696 | 0.8523 |  |

### archetype — Archetype / character  (9 cols · Stage 19)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `char_archetype` | str | signal | 0.0 | — | — | — | — |  |
| `char_ecosystem` | float64 | signal | 0.0 | 0 | 0.8571 | 1 | 1 |  |
| `char_gradient` | float64 | signal | 0.0 | -3.90 | 0.5354 | 3.85 | 23.36 |  |
| `char_hdb_psf` | float64 | signal | 0.0 | 0 | 576.33 | 753.88 | 923.86 |  |
| `char_hdb_share` | float64 | fraction [0,1] | 0.0 | 0 | 0.4996 | 0.8088 | 0.8712 |  |
| `char_interface` | float64 | signal | 0.0 | 0 | 0.1667 | 0.8333 | 1 |  |
| `char_nonres_share` | float64 | fraction [0,1] | 0.0 | 0 | 0.3439 | 0.9798 | 1 |  |
| `char_pct_elderly` | float64 | signal | 0.0 | 0 | 0.2064 | 0.257 | 0.931 |  |
| `char_pop_density` | float64 | signal | 0.0 | 0 | 9,412 | 26,324 | 50,576 |  |

### amenities — Amenity counts at hex  (29 cols · Stage 8)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `anchor_bus_200m` | int64 | score | 0.0 | 0 | 2 | 4 | 13 |  |
| `anchor_bus_dist_m` | float64 | meters | 0.0 | 0.445 | 109.79 | 258.14 | 12,103 |  |
| `anchor_clinic_500m` | int64 | score | 0.0 | 0 | 4 | 12 | 24 |  |
| `anchor_clinic_dist_m` | float64 | meters | 0.0 | 0.004684 | 195.98 | 802.21 | 15,880 |  |
| `anchor_community_500m` | int64 | score | 0.0 | 0 | 1 | 3 | 9 |  |
| `anchor_community_dist_m` | float64 | meters | 0.0 | 0.1927 | 471.25 | 1,464 | 15,066 |  |
| `anchor_hawker_300m` | int64 | score | 0.0 | 0 | 0 | 1 | 3 | 77.92% zero |
| `anchor_hawker_dist_m` | float64 | meters | 0.0 | 0.08242 | 713.96 | 1,894 | 17,222 |  |
| `anchor_hotel_300m` | int64 | score | 0.0 | 0 | 0 | 8 | 41 | 67.94% zero |
| `anchor_hotel_dist_m` | float64 | meters | 0.0 | 0.001352 | 963.38 | 4,474 | 13,929 |  |
| `anchor_library_500m` | int64 | score | 0.0 | 0 | 0 | 1 | 5 | 79.59% zero |
| `anchor_library_dist_m` | float64 | meters | 0.0 | 0.4757 | 1,022 | 2,358 | 15,558 |  |
| `anchor_mrt_300m` | int64 | score | 0.0 | 0 | 0 | 1 | 6 | 64.86% zero |
| `anchor_mrt_dist_m` | float64 | meters | 0.0 | 0.7914 | 424.86 | 1,394 | 14,478 |  |
| `anchor_park_500m` | int64 | score | 0.0 | 0 | 0 | 3 | 11 | 50.17% zero |
| `anchor_park_dist_m` | float64 | meters | 0.0 | 0.6645 | 501.80 | 1,395 | 14,201 |  |
| `anchor_school_500m` | int64 | score | 0.0 | 0 | 0 | 0 | 0 | 100.0% zero |
| `anchor_school_dist_m` | float64 | meters | 0.0 | 99,999 | 99,999 | 99,999 | 99,999 |  |
| `anchor_score` | float64 | score [0,1] | 0.0 | 8.17e-07 | 0.5555 | 0.7128 | 0.8156 |  |
| `anchor_sports_500m` | int64 | score | 0.0 | 0 | 6 | 22 | 151 |  |
| `anchor_sports_dist_m` | float64 | meters | 0.0 | 0.2961 | 213.01 | 752.48 | 14,238 |  |
| `anchor_supermarket_300m` | int64 | score | 0.0 | 0 | 1 | 3 | 7 |  |
| `anchor_supermarket_dist_m` | float64 | meters | 0.0 | 0.003905 | 278.43 | 809.51 | 15,527 |  |
| `anchor_tourist_500m` | int64 | score | 0.0 | 0 | 0 | 5 | 21 | 74.76% zero |
| `anchor_tourist_dist_m` | float64 | meters | 0.0 | 0.5478 | 1,599 | 4,508 | 14,560 |  |
| `anchor_university_500m` | int64 | score | 0.0 | 0 | 0 | 1 | 17 | 81.89% zero |
| `anchor_university_dist_m` | float64 | meters | 0.0 | 1.20 | 1,126 | 2,887 | 15,997 |  |
| `anchor_worship_300m` | int64 | score | 0.0 | 0 | 0 | 3 | 11 | 56.21% zero |
| `anchor_worship_dist_m` | float64 | meters | 0.0 | 4.421e-11 | 342.77 | 1,053 | 14,424 |  |

### satellite — Satellite (VIIRS / GHSL / WorldPop / WorldCover)  (2 cols · Stage 5b)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `nl_commercial` | float64 | radiance | 0.0 | -0.8336 | 0.0336 | 0.2395 | 0.771 |  |
| `nl_radiance` | float64 | radiance | 0.0 | 0 | 75.04 | 151.31 | 372.34 |  |

### competition — Competition (place-level)  (5 cols · Stage 17)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `competitors_200m` | int32 | — | 0.0 | 0 | 15 | 136 | 597 |  |
| `competitors_500m` | int32 | — | 0.0 | 0 | 48 | 434 | 1,527 |  |
| `market_share_proxy` | float64 | score [0,1] | 0.0 | 0.0006545 | 0.02041 | 0.1429 | 1 |  |
| `nearest_competitor_m` | float64 | meters | 0.0 | 0 | 18.10 | 159.92 | 7,844 |  |
| `substitution_risk` | float64 | — | 0.0 | 0 | 0 | 24 | 1,046 | 80.03% zero |

### complementary — Complementary (place-level)  (5 cols · Stage 17)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `complementary_diversity` | int32 | — | 0.0 | 0 | 22 | 24 | 24 |  |
| `complementary_fnb_300m` | int32 | — | 0.0 | 0 | 66 | 454 | 948 |  |
| `complementary_retail_300m` | int32 | — | 0.0 | 0 | 62 | 267 | 1,141 |  |
| `complementary_score` | float64 | score [0,1] | 0.0 | 0 | 1 | 1 | 1 |  |
| `total_places_300m` | int32 | — | 0.0 | 0 | 309 | 1,609 | 3,305 |  |

### catchment — Catchment (place-level)  (5 cols · Stage 17)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `catchment_daytime` | float64 | — | 0.0 | 0 | 1.77 | 100 | 100 |  |
| `catchment_elderly` | float64 | — | 0.0 | 0 | 93.38 | 900.62 | 2,740 |  |
| `catchment_nonres_share` | float64 | fraction [0,1] | 0.0 | 0 | 0.4354 | 1 | 1 |  |
| `catchment_nonresident` | float64 | — | 0.0 | 0 | 589.26 | 1,491 | 11,680 |  |
| `catchment_pop` | float64 | — | 0.0 | 0 | 1,552 | 5,137 | 13,033 |  |

### supply_demand_fit — Supply-demand fit (place-level)  (4 cols · Stage 17)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `context_score` | float64 | score [0,1] | 0.0 | 0.05121 | 0.6157 | 0.7162 | 0.9289 |  |
| `demand_context_score` | float64 | score [0,1] | 0.0 | 0 | 0.1659 | 0.3061 | 0.4704 |  |
| `demand_match` | float64 | score [0,1] | 0.0 | 0 | 0.05561 | 0.4065 | 1 |  |
| `survivability_index` | float64 | score [0,1] | 0.0 | 0 | 0 | 0.06898 | 0.5911 | 64.04% zero |

### provenance — Source tracking  (1 cols · Stage 1)

| Column | dtype | units | null % | min | p50 | p90 | max | notes |
|---|---|---|---|---|---|---|---|---|
| `source` | str | string | 0.0 | — | — | — | — | origin dataset: `overture`, `osm`, `sfa`, `manual` |

---

## 4. Stage-to-pillar mapping

| Stage | Pillar(s) produced |
|---|---|
| 0 Universe | identity |
| 2 Buildings | buildings |
| 3 Population | demographics |
| 4 Land use | land_use |
| 5 Transit | transit + gtfs |
| 5b Satellite (opt) | satellite (VIIRS/GHSL/WorldPop/WorldCover) |
| 6 Walk graph | walk_network + roads_signals |
| 7 Place composition | place_composition |
| 8 Amenities | amenities + distance_amenity + walk_euclid + osm_poi |
| 9 Demand pull | demand_pull |
| 10 Synergy | synergy |
| 11 Saturation | saturation_gap |
| 12 Spatial rings | spatial_rings + transit_rings |
| 13 Micrograph | micrograph |
| 14 Influence | influence |
| 14b Development gap | saturation_gap (ura_*) |
| 14c Dynamic LTA (opt) | dynamic_lta |
| 15 Merge+normalize | (all, normalized copies) |
| 16 Composites | composites + proxies |
| 17 Place enrichment | competition + complementary + catchment + supply-demand fit (place only) |
| 19 Archetype | archetype (k-means) |

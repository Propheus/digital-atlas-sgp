# Plexis SGP v4 — Feature Catalog

**Generated:** 2026-06-11 04:15 · **Features:** 2,735

## `catalog/colo_lift_matrix.parquet`

_6 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `cat_a` | object | category | 0.0 | 24 unique · `bakery` | Anchor category A (lift = how much B over-concentrates near A) |
| `cat_b` | object | category | 0.0 | 24 unique · `bakery` | Partner category B |
| `ci_hi` | float64 | ratio | 0.0 | 0.2051 → 4.899 (median 1.044) | Bootstrap 95% CI upper |
| `ci_lo` | float64 | ratio | 0.0 | 0.1896 → 4.27 (median 0.9821) | Bootstrap 95% CI lower (200 resamples of the A-set) |
| `lift` | float64 | ratio | 0.0 | 0.1974 → 4.591 (median 1.008) | mean count of B within 400 m of A-places ÷ category-blind base over all places. >1 = B seeks A (bar→bar 3.0); <1 = avoidance (industrial→residential 0.50) |
| `significant` | bool | bool | 0.0 | 0 → 1 (median 1) | CI excludes 1.0 — only these pairs enter colo_fit scores |

## `hex/hex8_acra_biz.parquet`

_11 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `biz_company_share` | float64 | ratio | 47.1 | 0 → 1 (median 0.6667) | 'Local Company' share of live entities (formality mix) |
| `biz_dead_share` | float64 | ratio | 44.6 | 0 → 1 (median 0.7006) | Deregistered / total ever — LIFETIME mortality (no cessation dates in ACRA). NaN where no entities |
| `biz_density_per_km2` | float64 | count/km2 | 0.0 | 0 → 6.594e+04 (median 2.7) | Live entities per km² |
| `biz_formation_5y` | float64 | count | 0.0 | 0 → 3.074e+04 (median 0) | Entities issued in the last 5 years (any status) |
| `biz_live_count` | float64 | count | 0.0 | 0 → 4.86e+04 (median 2) | ACRA live ('Registered') entities at building-precise postals (offline OneMap dump, 94.2% coverage) |
| `biz_live_robust` | float64 | count | 0.0 | 0 → 1.047e+04 (median 2) | Live count with per-postal contribution winsorized at 100 — registered-agent buildings (Paya Lebar Sq 19K/postal) damped |
| `biz_median_age_yrs` | float64 | years | 47.1 | 0.3915 → 63.19 (median 7.918) | Median age of live entities |
| `biz_per_address` | float64 | count/address | 47.1 | 1 → 746.1 (median 6.211) | Live entities per unique postal — high = corporate-secretary building (City Hall 109–131) |
| `biz_recent_dead_share` | float64 | ratio | 49.7 | 0 → 1 (median 0.3589) | Dead share among 2018+ cohort (closer to churn). NaN where no 2018+ entities |
| `biz_total_ever` | float64 | count | 0.0 | 0 → 1.287e+05 (median 6) | All entities ever registered (live + dead) |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |

## `hex/hex8_all_features.parquet`

_801 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `access_vuln_penalty` | float64 | points | 0.0 | 0 → 0.25 (median 0) | Access-vulnerability penalty |
| `access_vuln_share` | float64 | ratio | 0.0 | 0 → 1 (median 0) | Access-vulnerable share |
| `accessibility_composite` | float64 | 0-1 | 0.0 | 0 → 0.957 (median 0.287) | Composite access score across transit + walk + road reach |
| `adq_availability_v2` | float64 | 0-100 | 41.7 | 0.0606 → 1 (median 0.3862) | Transit availability composite |
| `adq_core` | float64 | 0-100 | 41.7 | 0.1839 → 1 (median 0.5583) | Adequacy core (pre-vulnerability) |
| `adq_core_elderly` | float64 | 0-100 | 41.7 | 0.1634 → 1 (median 0.4936) | Adequacy core, elderly |
| `adq_core_family` | float64 | 0-100 | 41.7 | 0.1967 → 1 (median 0.5692) | Adequacy core, family |
| `adq_core_workers` | float64 | 0-100 | 41.7 | 0.1938 → 1 (median 0.6252) | Adequacy core, workers |
| `adq_default` | float64 | 0-100 | 41.7 | 0.0677 → 1 (median 0.5035) | Transport adequacy v3 (default profile, 0-100) |
| `adq_default_elderly` | float64 | 0-100 | 41.7 | 0.0677 → 1 (median 0.5633) | Adequacy, elderly profile |
| `adq_default_family` | float64 | 0-100 | 41.7 | 0.0606 → 1 (median 0.5571) | Adequacy, family profile |
| `adq_default_workers` | float64 | 0-100 | 41.7 | 0.0606 → 1 (median 0.4479) | Adequacy, workers profile |
| `adq_f_accessibility` | float64 | 0-100 | 41.7 | 0.2829 → 1 (median 0.607) | Adequacy v3 factor score: composite access (mobility-v2 model) |
| `adq_f_children_gap` | float64 | 0-100 | 41.7 | 0 → 0.9322 (median 0.1256) | Adequacy v3 factor score: child-population service gap (mobility-v2 model) |
| `adq_f_connectivity` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.6469) | Adequacy v3 factor score: network connectivity (mobility-v2 model) |
| `adq_f_distance` | float64 | 0-100 | 41.7 | 0.004667 → 1 (median 0.248) | Adequacy v3 factor score: distance to transit (mobility-v2 model) |
| `adq_f_dorm_gap` | float64 | 0-100 | 41.7 | 0 → 1 (median 0) | Adequacy v3 factor score: dorm-worker service gap (mobility-v2 model) |
| `adq_f_elderly_gap` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.0948) | Adequacy v3 factor score: elderly service gap (mobility-v2 model) |
| `adq_f_fdw_gap` | float64 | 0-100 | 41.7 | 0 → 0.7624 (median 0) | Adequacy v3 factor score: FDW service gap (mobility-v2 model) |
| `adq_f_last_mile` | float64 | 0-100 | 41.7 | 0.1719 → 1 (median 0.6926) | Adequacy v3 factor score: last-mile friction (mobility-v2 model) |
| `adq_f_line_pressure` | float64 | 0-100 | 41.7 | 0 → 1 (median 0) | Adequacy v3 factor score: line crowding pressure (mobility-v2 model) |
| `adq_f_low_frequency` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.6627) | Adequacy v3 factor score: service frequency shortfall (mobility-v2 model) |
| `adq_f_low_income_gap` | float64 | 0-100 | 41.7 | 0 → 0.5804 (median 0.2188) | Adequacy v3 factor score: low-income service gap (mobility-v2 model) |
| `adq_f_reach_gap` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.2084) | Adequacy v3 factor score: destination reach shortfall (mobility-v2 model) |
| `adq_gap_core` | float64 | 0-100 | 41.7 | 0.1614 → 0.95 (median 0.5126) | Adequacy gap (core) |
| `adq_gap_default` | float64 | 0-100 | 41.7 | 0.1409 → 0.965 (median 0.4769) | Adequacy gap (default profile) |
| `adq_gap_equity_max` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.3882) | Worst per-profile equity gap |
| `adq_primary_factor` | object | category | 55.7 | 6 unique · `reach` | Primary driving factor (default profile) |
| `adq_primary_gap_reason` | object | category | 0.0 | 11 unique · `walk_unfriendly` | Primary gap explanation tag |
| `adq_v2` | float64 | 0-100 | 41.7 | 0.0677 → 1 (median 0.5387) | Adequacy v2 (availability-floored legacy) |
| `adq_worst_factor` | object | category | 0.0 | 10 unique · `f_accessibility` | Name of the worst adequacy factor |
| `adq_worst_factor_value` | float64 | 0-100 | 41.7 | 0.1084 → 1 (median 0.8477) | Score of the worst adequacy factor |
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 11.03 (median 0.5845) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `biz_company_share` | float64 | ratio | 47.1 | 0 → 1 (median 0.6667) | 'Local Company' share of live entities (formality mix) |
| `biz_dead_share` | float64 | ratio | 44.6 | 0 → 1 (median 0.7006) | Deregistered / total ever — LIFETIME mortality (no cessation dates in ACRA). NaN where no entities |
| `biz_density_per_km2` | float64 | count/km2 | 0.0 | 0 → 6.594e+04 (median 2.7) | Live entities per km² |
| `biz_formation_5y` | float64 | count | 0.0 | 0 → 3.074e+04 (median 0) | Entities issued in the last 5 years (any status) |
| `biz_live_count` | float64 | count | 0.0 | 0 → 4.86e+04 (median 2) | ACRA live ('Registered') entities at building-precise postals (offline OneMap dump, 94.2% coverage) |
| `biz_live_robust` | float64 | count | 0.0 | 0 → 1.047e+04 (median 2) | Live count with per-postal contribution winsorized at 100 — registered-agent buildings (Paya Lebar Sq 19K/postal) damped |
| `biz_median_age_yrs` | float64 | years | 47.1 | 0.3915 → 63.19 (median 7.918) | Median age of live entities |
| `biz_per_address` | float64 | count/address | 47.1 | 1 → 746.1 (median 6.211) | Live entities per unique postal — high = corporate-secretary building (City Hall 109–131) |
| `biz_recent_dead_share` | float64 | ratio | 49.7 | 0 → 1 (median 0.3589) | Dead share among 2018+ cohort (closer to churn). NaN where no 2018+ entities |
| `biz_total_ever` | float64 | count | 0.0 | 0 → 1.287e+05 (median 6) | All entities ever registered (live + dead) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 191 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1968 (median 136) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 2670 (median 184.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 4.288e+05 (median 4.936e+04) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.5818 (median 0.067) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 165 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 45 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1084 (median 0) | Residential buildings |
| `bridge_length_m` | float64 | m | 0.0 | 0 → 1.07e+04 (median 89.88) | Bridge segment length |
| `bto_pipeline_est` | float64 | units | 0.0 | 0 → 3431 (median 0) | Town under-construction units allocated within town by FAR headroom share — MODELED estate-growth estimate |
| `bto_uc_units_town` | float64 | units | 0.0 | 0 → 1.148e+04 (median 0) | FY2024 HDB units under construction in the hex's town (town-broadcast; Kallang/Whampoa 11.5K, Tengah 11.1K top) |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 20.36 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Bus stops in hex |
| `bus_stops_in_400m` | int64 | count | 0.0 | 0 → 18 (median 0) | Bus stops within 400 m of centroid |
| `bus_stops_in_800m` | int64 | count | 0.0 | 0 → 59 (median 2) | Bus stops within 800 m |
| `bus_taps_in_am` | int64 |  | 0.0 | 0 → 1.863e+05 (median 0) | Daily bus tap-ins in the am time window (LTA PV) |
| `bus_taps_in_midday` | int64 |  | 0.0 | 0 → 1.582e+05 (median 0) | Daily bus tap-ins in the midday time window (LTA PV) |
| `bus_taps_in_night` | int64 |  | 0.0 | 0 → 7.79e+04 (median 0) | Daily bus tap-ins in the night time window (LTA PV) |
| `bus_taps_in_offpeak` | int64 |  | 0.0 | 0 → 6e+05 (median 0) | Daily bus tap-ins in the offpeak time window (LTA PV) |
| `bus_taps_in_pm` | int64 |  | 0.0 | 0 → 2.371e+05 (median 0) | Daily bus tap-ins in the pm time window (LTA PV) |
| `bus_taps_in_total` | int64 |  | 0.0 | 0 → 1.25e+06 (median 0) | Daily bus tap-ins in the total time window (LTA PV) |
| `bus_taps_out_am` | int64 |  | 0.0 | 0 → 2.221e+05 (median 0) | Daily bus tap-outs in the am time window (LTA PV) |
| `bus_taps_out_midday` | int64 |  | 0.0 | 0 → 1.918e+05 (median 0) | Daily bus tap-outs in the midday time window (LTA PV) |
| `bus_taps_out_night` | int64 |  | 0.0 | 0 → 5.752e+04 (median 0) | Daily bus tap-outs in the night time window (LTA PV) |
| `bus_taps_out_offpeak` | int64 |  | 0.0 | 0 → 5.563e+05 (median 0) | Daily bus tap-outs in the offpeak time window (LTA PV) |
| `bus_taps_out_pm` | int64 |  | 0.0 | 0 → 1.855e+05 (median 0) | Daily bus tap-outs in the pm time window (LTA PV) |
| `bus_taps_out_total` | int64 |  | 0.0 | 0 → 1.184e+06 (median 0) | Daily bus tap-outs in the total time window (LTA PV) |
| `ca_footfall` | float64 |  | 0.0 | 0 → 1 (median 0) | Commercial-activity component: footfall |
| `ca_nl` | float64 |  | 0.0 | 0 → 1 (median 0.2993) | Commercial-activity component: nl |
| `ca_places` | float64 |  | 0.0 | 0 → 1 (median 0.0023) | Commercial-activity component: places |
| `ca_spend` | float64 |  | 0.0 | 0 → 1 (median 0.1726) | Commercial-activity component: spend |
| `ca_taps` | float64 |  | 0.0 | 0 → 1 (median 0) | Commercial-activity component: taps |
| `cap_beauty_personal` | float64 | outlet-equivalents | 0.0 | 0 → 3.906 (median 0.3123) | Huff capture for a NEW beauty_personal outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_best_category` | object | category | 0.0 | 11 unique · `cafe_coffee` | Category with the highest capture at this hex |
| `cap_cafe_coffee` | float64 | outlet-equivalents | 0.0 | 0 → 3.905 (median 0.2361) | Huff capture for a NEW cafe_coffee outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_convenience` | float64 | outlet-equivalents | 0.0 | 0 → 2.902 (median 0.1662) | Huff capture for a NEW convenience outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_education` | float64 | outlet-equivalents | 0.0 | 0 → 2.473 (median 0.2423) | Huff capture for a NEW education outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fast_food` | float64 | outlet-equivalents | 0.0 | 0 → 2.063 (median 0.1607) | Huff capture for a NEW fast_food outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fitness_recreation` | float64 | outlet-equivalents | 0.0 | 0 → 3.482 (median 0.2053) | Huff capture for a NEW fitness_recreation outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_hawker` | float64 | outlet-equivalents | 0.0 | 0 → 4.939 (median 0.1847) | Huff capture for a NEW hawker outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_health_medical` | float64 | outlet-equivalents | 0.0 | 0 → 4.321 (median 0.2502) | Huff capture for a NEW health_medical outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_restaurant` | float64 | outlet-equivalents | 0.0 | 0 → 3.857 (median 0.3747) | Huff capture for a NEW restaurant outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_shopping_retail` | float64 | outlet-equivalents | 0.0 | 0 → 4.058 (median 0.4394) | Huff capture for a NEW shopping_retail outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_supermarket` | float64 | outlet-equivalents | 0.0 | 0 → 3.31 (median 0.1391) | Huff capture for a NEW supermarket outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_total` | float64 | outlet-equivalents | 0.0 | 0 → 36.82 (median 2.758) | Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83) |
| `carpark_capacity_lots` | float64 | lots | 0.0 | 0 → 1.367e+04 (median 0) | Summed car-lot CAPACITY (live availability total_lots, lot type C; 696K national) |
| `carpark_count_avail` | int64 |  | 0.0 | 0 → 45 (median 0) | carpark count avail (see layer docs) |
| `carpark_count_hdb` | float64 | count | 0.0 | 0 → 26 (median 0) | HDB carparks in hex (HDB Carpark Information) |
| `carpark_lots_avail` | int64 |  | 0.0 | 0 → 9318 (median 0) | carpark lots avail (see layer docs) |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 0) | Tarjan bridge endpoints (network cut points) |
| `chas_clinic_count` | int64 |  | 0.0 | 0 → 20 (median 0) | chas clinic count (see layer docs) |
| `chas_clinics_within_500m` | int64 |  | 0.0 | 0 → 120 (median 0) | Count of chas clinics within 500m |
| `colo_fit_beauty_personal` | float64 | log-lift | 0.0 | -0.4176 → 0.5449 (median 0.2206) | Co-location mix-match for beauty_personal: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_cafe_coffee` | float64 | log-lift | 0.0 | -0.3487 → 0.1852 (median 0.0906) | Co-location mix-match for cafe_coffee: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_convenience` | float64 | log-lift | 0.0 | -0.5409 → 0.2072 (median 0) | Co-location mix-match for convenience: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_education` | float64 | log-lift | 0.0 | -0.5588 → 0.225 (median 0) | Co-location mix-match for education: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fast_food` | float64 | log-lift | 0.0 | -0.7358 → 0.2334 (median 0) | Co-location mix-match for fast_food: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fitness_recreation` | float64 | log-lift | 0.0 | -0.5761 → 0.1972 (median 0) | Co-location mix-match for fitness_recreation: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_hawker` | float64 | log-lift | 0.0 | -0.5998 → 0.2785 (median 0) | Co-location mix-match for hawker: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_health_medical` | float64 | log-lift | 0.0 | -0.5084 → 0.2515 (median 0.1073) | Co-location mix-match for health_medical: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_restaurant` | float64 | log-lift | 0.0 | -0.1131 → 0.5658 (median 0.2243) | Co-location mix-match for restaurant: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_shopping_retail` | float64 | log-lift | 0.0 | 0 → 0.416 (median 0.1618) | Co-location mix-match for shopping_retail: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_supermarket` | float64 | log-lift | 0.0 | -0.364 → 0.1704 (median 0) | Co-location mix-match for supermarket: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `commercial_activity_index` | float64 | 0-1 | 0.0 | 0 → 0.9549 (median 0.1314) | Footfall-weighted economic activity: night lights + spend proxy + transit taps + place density + OD throughput (distinct from supply-only commercial_intensity, corr 0.84) |
| `commercial_intensity` | float64 | 0-1 | 0.0 | 0 → 0.998 (median 0.06) | Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `condo_project_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Private strata projects with transactions in hex (URA, 2,384) |
| `condo_txn_units` | float64 | units | 0.0 | 0 → 1624 (median 0) | Units TRANSACTED across those projects — private-housing density weight, NOT stock |
| `cons_bldg_count` | float64 | count | 0.0 | 0 → 1351 (median 0) | URA conserved buildings in hex (MP2019 SDCP layer, 7,235 islandwide) — shophouse/heritage density |
| `cons_cluster_flag` | bool | bool | 0.0 | 0 → 1 (median 0) | >=20 conserved buildings — heritage shophouse cluster (Chinatown, Little India, Jalan Besar belt) |
| `coworking_count` | float64 | count | 0.0 | 0 → 20 (median 0) | Coworking venues (places name-match, 171 islandwide; 40% CBD-core) |
| `crowd_equity_penalty` | float64 | points | 0.0 | 0 → 0.2338 (median 0) | Crowding equity penalty |
| `crowd_sensitive_share` | float64 | ratio | 0.0 | 0 → 0.55 (median 0) | Crowding-sensitive share |
| `crowding_load_factor` | float64 | index | 0.0 | 0 → 0.9931 (median 0) | Peak load factor on serving lines |
| `cycling_path_len_m` | float64 | m | 0.0 | 0 → 1.048e+04 (median 0) | Cycling-path length in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.187e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.476e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `density_pressure` | float64 | 0-1 | 0.0 | 0 → 0.778 (median 0.021) | Composite: population + buildings + low road space |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.336e+04 (median 281.7) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.372e+04 (median 1503) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.376e+04 (median 1731) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.373e+04 (median 1655) | Centroid distance to nearest MRT/LRT station |
| `dist_petrol_m` | float64 | m | 0.0 | 2.5 → 1.407e+04 (median 2030) | Distance to nearest petrol station |
| `dist_polyclinic_m` | float64 | m | 0.0 | 103.9 → 1.668e+04 (median 3757) | Centroid distance to nearest polyclinic — public primary-care competition signal |
| `dist_to_nearest_lrt_m` | float64 | m | 0.0 | 65.08 → 2.421e+04 (median 8450) | Distance to nearest LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.599e+04 (median 915.2) | Walk distance to nearest clinic |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.596e+04 (median 385.1) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.599e+04 (median 1046) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.054e+04 (median 1037) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.581e+04 (median 610.4) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.79e+04 (median 857.1) | Walk distance to nearest supermarket |
| `dist_wet_market_m` | float64 | m | 0.0 | 37.6 → 1.794e+04 (median 4601) | Distance to nearest wet market — morning-circuit / grocery-substitution signal |
| `dominant_use` | object | categorical | 0.0 | 11 unique · `transport` | Bucket with highest area share |
| `dt_class` | object | category | 0.0 | 4 unique · `no_data` | job_center (>1.5) / balanced / bedroom (<0.67) / no_data |
| `dt_clipped` | bool | bool | 0.0 | 0 → 1 (median 0) | True if pop+net was clipped at 0 (12 hexes) |
| `dt_inflow_am_persons` | float64 | persons/day | 0.0 | 0 → 9.1e+04 (median 0) | AM-window inbound persons (mode-share adjusted) |
| `dt_net_am_persons` | float64 | persons/day | 0.0 | -1.887e+04 → 8.724e+04 (median 0) | AM net inflow (in − out). THE directional day-night signal; basis of redefined breathing_idx |
| `dt_outflow_am_persons` | float64 | persons/day | 0.0 | 0 → 4.993e+04 (median 0) | AM-window outbound persons (mode-share adjusted) |
| `dt_pop` | float64 | persons | 0.0 | 0 → 8.788e+04 (median 16.79) | Commuter daytime headcount: pop_resident − AM transit out + AM in (0.62 PT mode share, /22 weekdays). Clipped ≥0. |
| `dt_pop_unadj` | float64 | persons | 0.0 | 0 → 5.473e+04 (median 13.01) | Daytime pop, transit-observed only (no mode-share scale-up) |
| `dt_ratio` | float64 | ratio | 59.1 | 0 → 138.8 (median 0.99) | dt_pop / pop_resident; NaN where pop<50 & no OD (no-data, NOT 0) |
| `dyn_avg_speed_kmh` | float64 |  | 0.0 | 0 → 61.06 (median 15.08) | dyn avg speed kmh (see layer docs) |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 3.686 (median 0.2114) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 2.716e+06 (median 1.558e+05) | Sum of footprint × est_floors per building |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `family_index` | float64 | 0-1 | 0.0 | 0 → 0.934 (median 0.103) | Composite: children + schools + preschools + family amenities |
| `female_pop_share` | float64 | ratio | 57.1 | 0.2381 → 0.6471 (median 0.5182) | Female share of resident pop (SingStat 2025, subzone-broadcast). NaN = zero-population subzone; tiny subzones can skew genuinely |
| `gap_bakery` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for bakery: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_beauty_personal` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for beauty personal: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_cafe_coffee` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for cafe coffee: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_fast_food` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for fast food: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_fitness_recreation` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for fitness recreation: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_hawker` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for hawker: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_health_medical` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for health medical: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_restaurant` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for restaurant: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_supermarket` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for supermarket: actual minus expected per-1k supply (positive = oversupplied) |
| `gtfs_daily_departures` | int64 |  | 0.0 | 0 → 2.416e+04 (median 0) | GTFS-derived transit service metric: daily departures (weekday schedule) |
| `gtfs_dep_am` | int64 |  | 0.0 | 0 → 2567 (median 0) | GTFS-derived transit service metric: dep am (weekday schedule) |
| `gtfs_dep_midday` | int64 |  | 0.0 | 0 → 3796 (median 0) | GTFS-derived transit service metric: dep midday (weekday schedule) |
| `gtfs_dep_night` | int64 |  | 0.0 | 0 → 3390 (median 0) | GTFS-derived transit service metric: dep night (weekday schedule) |
| `gtfs_dep_pm` | int64 |  | 0.0 | 0 → 2612 (median 0) | GTFS-derived transit service metric: dep pm (weekday schedule) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `gtfs_headway_midday_min` | float64 |  | 0.0 | 0.1 → 999 (median 999) | GTFS-derived transit service metric: headway midday min (weekday schedule) |
| `gtfs_headway_night_min` | float64 |  | 0.0 | 0.3 → 999 (median 999) | GTFS-derived transit service metric: headway night min (weekday schedule) |
| `gtfs_headway_pm_min` | float64 |  | 0.0 | 0.1 → 999 (median 999) | GTFS-derived transit service metric: headway pm min (weekday schedule) |
| `gtfs_routes_served` | int64 |  | 0.0 | 0 → 291 (median 0) | GTFS-derived transit service metric: routes served (weekday schedule) |
| `gtfs_stops_with_service` | int64 |  | 0.0 | 0 → 31 (median 0) | GTFS-derived transit service metric: stops with service (weekday schedule) |
| `hawker_centre_count` | int64 |  | 0.0 | 0 → 6 (median 0) | hawker centre count (see layer docs) |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 63.75 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 147 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.319e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 23 (median 0) | Authoritative HDB multi-storey carparks |
| `hdb_resale_12m_median_price` | float64 |  | 0.0 | 0 → 9.8e+05 (median 0) | hdb resale 12m median price (see layer docs) |
| `hdb_resale_4r_median_price` | float64 |  | 0.0 | 0 → 8.35e+05 (median 0) | hdb resale 4r median price (see layer docs) |
| `hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | hdb resale 4r median psm (see layer docs) |
| `hdb_resale_avg_lease_remaining_yrs` | float64 |  | 0.0 | 0 → 89.87 (median 0) | hdb resale avg lease remaining yrs (see layer docs) |
| `hdb_resale_in_town` | int64 |  | 0.0 | 0 → 1 (median 0) | hdb resale in town (see layer docs) |
| `hdb_resale_median_price` | float64 |  | 0.0 | 0 → 7.6e+05 (median 0) | hdb resale median price (see layer docs) |
| `hdb_resale_median_psm` | float64 |  | 0.0 | 0 → 7629 (median 0) | hdb resale median psm (see layer docs) |
| `hdb_resale_txns_12m` | float64 |  | 0.0 | 0 → 1948 (median 0) | hdb resale txns 12m (see layer docs) |
| `hdb_resale_txns_total` | float64 |  | 0.0 | 0 → 1.852e+04 (median 0) | hdb resale txns total (see layer docs) |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `in_primary_school_zone` | int64 | bool | 0.0 | 0 → 1 (median 0) | Cell intersects a primary-school zone |
| `in_silver_zone` | int64 | bool | 0.0 | 0 → 1 (median 0) | Cell intersects an elderly-priority Silver Zone |
| `industrial_adjacency_score` | float64 | index | 0.0 | 0 → 1 (median 0) | Adjacency to industrial estates (guard signal) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `iso_euclid800_pop` | float64 | persons | 0.0 | 0 → 9.396e+04 (median 16.02) | Euclid-800m baseline pop on the same node field |
| `iso_reached_node_n` | float64 | count | 0.0 | 0 → 1018 (median 48) | Walk-graph nodes reached within budget (QA) |
| `iso_severance_ratio` | float64 | ratio | 56.2 | 0 → 0.77 (median 0.219) | network pop / euclid pop. Ideal grid ≈0.55 (detour²); low = barriers. NaN where euclid pop < 200 |
| `iso_snap_dist_m` | float64 | m | 0.0 | 1.634 → 1.019e+04 (median 55.99) | Activity-origin snap distance to walk graph (QA) |
| `iso_transit15_hex9_n` | int64 | count | 0.0 | 1 → 111 (median 23) | hex9 cells reached in 15 min |
| `iso_transit15_places` | float64 | count | 0.0 | 0 → 2.192e+04 (median 114) | Places (hex9 pc_total) within the 15-min transit reach |
| `iso_transit15_pop` | float64 | persons | 0.0 | 0 → 3.121e+05 (median 23) | Population reachable door-to-door in 15 min weekday-AM transit (GTFS route-dir-stop graph + walk arms) |
| `iso_transit15_stops_used` | int64 | count | 0.0 | 0 → 272 (median 4) | Transit stops reachable within 15 min (network-access measure) |
| `iso_walk10_competitors_cafe_coffee` | float64 | count | 0.0 | 0 → 217 (median 0) | Existing cafe_coffee outlets inside the 800 m walk catchment |
| `iso_walk10_competitors_fitness_recreation` | float64 | count | 0.0 | 0 → 95 (median 0) | Existing fitness_recreation outlets inside the 800 m walk catchment |
| `iso_walk10_competitors_restaurant` | float64 | count | 0.0 | 0 → 513 (median 0) | Existing restaurant outlets inside the 800 m walk catchment |
| `iso_walk10_competitors_supermarket` | float64 | count | 0.0 | 0 → 44 (median 0) | Existing supermarket outlets inside the 800 m walk catchment |
| `iso_walk10_magnets` | float64 | count | 0.0 | 0 → 953 (median 0) | Magnet anchors reached within the walk catchment |
| `iso_walk10_places` | float64 | count | 0.0 | 0 → 4508 (median 11) | Exact place points reached within 800 m network walk |
| `iso_walk10_pop` | float64 | persons | 0.0 | 0 → 3.534e+04 (median 2.649) | Population within 800 m NETWORK walk of hex activity centroid (node-field demand, k=4 multi-source Dijkstra) |
| `iso_walk10_spend` | float64 | persons-weighted | 0.0 | 0 → 9745 (median 0.762) | iso pop × PA affluence index — catchment spending proxy |
| `iso_walk10_unserved_pop_cafe_coffee` | float64 | persons | 0.0 | 0 → 817.8 (median 0) | Catchment residents with NO cafe_coffee within 800 m euclid of home — network-precise underserved demand |
| `iso_walk10_unserved_pop_fitness_recreation` | float64 | persons | 0.0 | 0 → 395.6 (median 0) | Catchment residents with NO fitness_recreation within 800 m euclid of home — network-precise underserved demand |
| `iso_walk10_unserved_pop_restaurant` | float64 | persons | 0.0 | 0 → 226.7 (median 0) | Catchment residents with NO restaurant within 800 m euclid of home — network-precise underserved demand |
| `iso_walk10_unserved_pop_supermarket` | float64 | persons | 0.0 | 0 → 2316 (median 0) | Catchment residents with NO supermarket within 800 m euclid of home — network-precise underserved demand |
| `jam_pct` | float64 |  | 0.0 | 0 → 62.79 (median 1.79) | jam pct (see layer docs) |
| `jobs_reach_45m` | float64 | jobs | 0.0 | 0 → 1.799e+06 (median 1.122e+05) | Job proxy (office+industrial+services places, scaled 2.4M) within 45 min |
| `labor_accessibility_pct` | float64 | ratio | 0.0 | 0 → 0.749 (median 0.0502) | labor_pool_45m / national working-age pop |
| `labor_jobs_balance_45m` | float64 | ratio | 0.0 | 0 → 8.504e+04 (median 0.951) | jobs_reach / labor_pool — divergence flags job-rich/transit-poor (Jurong Island, Tuas) |
| `labor_pool_30m` | float64 | persons | 0.0 | 0 → 8.228e+05 (median 2.039e+04) | Working-age pop reaching this hex within 30-min weekday-AM transit |
| `labor_pool_45m` | float64 | persons | 0.0 | 0 → 2.116e+06 (median 1.419e+05) | Working-age pop within 45-min transit (CBD 1.68M = 59.6% of workforce; Tuas p0) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 22.81) | Lane-km per km² (lane count × length / area) |
| `last_mile_friction` | float64 | index | 0.0 | 0.1719 → 1 (median 0.8333) | Last-mile friction composite |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.47 (median 1.349) | Hex centroid latitude |
| `linkway_len_m` | float64 | m | 0.0 | 0 → 4705 (median 0) | Covered-linkway length in hex (7,012-segment LTA layer) — sheltered-walk density |
| `linkway_per_road_km` | float64 | m/km | 20.2 | 0 → 65.59 (median 0) | Covered-linkway metres per road km — shelter coverage ratio |
| `livability_index` | float64 | 0-1 | 0.0 | 0.063 → 0.972 (median 0.378) | Composite: walkability + green + amenities + transit |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `low_income_share` | float64 | ratio | 65.2 | 0 → 0.2998 (median 0.1687) | Low-income share of residents (level deduped vs pop_hdb; share is the signal) |
| `lrt_stations` | float64 | count | 0.0 | 0 → 3 (median 0) | LRT stations in hex |
| `lrt_stations_in_500m` | int64 | count | 0.0 | 0 → 3 (median 0) | LRT stations within 500 m |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.523 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4744 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7291 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.09 (median 0.6931) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2884 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3002 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0346) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 2096 (median 30) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9368 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 8.596e+05 (median 8.331e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1035) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9207 (median 0.0005) | Water body share |
| `max1_chas_clinic_count` | float64 |  | 0.0 | 0 → 20 (median 0) | Max over ring-1 neighbours of: chas clinic count (see layer docs) |
| `max1_commercial_intensity` | float64 |  | 0.0 | 0 → 0.998 (median 0.095) | Max over ring-1 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `max1_density_pressure` | float64 |  | 0.0 | 0 → 0.778 (median 0.137) | Max over ring-1 neighbours of: Composite: population + buildings + low road space |
| `max1_family_index` | float64 |  | 0.0 | 0 → 0.934 (median 0.252) | Max over ring-1 neighbours of: Composite: children + schools + preschools + family amenities |
| `max1_hawker_centre_count` | float64 |  | 0.0 | 0 → 6 (median 0) | Max over ring-1 neighbours of: hawker centre count (see layer docs) |
| `max1_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | Max over ring-1 neighbours of: hdb resale 4r median psm (see layer docs) |
| `max1_nl_2024` | float64 |  | 0.0 | 0 → 161.4 (median 60.46) | Max over ring-1 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `max1_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 158.6 (median 44.37) | Max over ring-1 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `max1_pc_cat_business_office` | float64 |  | 0.0 | 0 → 867 (median 9) | Max over ring-1 neighbours of: Place count in cell: business office category (24-cat taxonomy) |
| `max1_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 213 (median 2) | Max over ring-1 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `max1_pc_cat_education` | float64 |  | 0.0 | 0 → 169 (median 2) | Max over ring-1 neighbours of: Place count in cell: education category (24-cat taxonomy) |
| `max1_pc_cat_hawker` | float64 |  | 0.0 | 0 → 246 (median 1) | Max over ring-1 neighbours of: Place count in cell: hawker category (24-cat taxonomy) |
| `max1_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 424 (median 1) | Max over ring-1 neighbours of: Place count in cell: health medical category (24-cat taxonomy) |
| `max1_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 419 (median 8) | Max over ring-1 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `max1_pc_cat_residential` | float64 |  | 0.0 | 0 → 149 (median 2) | Max over ring-1 neighbours of: Place count in cell: residential category (24-cat taxonomy) |
| `max1_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 534 (median 4) | Max over ring-1 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) |
| `max1_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 742 (median 5) | Max over ring-1 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `max1_pc_magnets` | float64 |  | 0.0 | 0 → 980 (median 6) | Max over ring-1 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `max1_pc_total` | float64 |  | 0.0 | 0 → 4929 (median 130) | Max over ring-1 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `max1_pc_unique_brands` | float64 |  | 0.0 | 0 → 125 (median 5) | Max over ring-1 neighbours of: Distinct retail/F&B brands present — chain richness |
| `max1_preschools_within_400m` | float64 |  | 0.0 | 0 → 104 (median 0) | Max over ring-1 neighbours of: Count of preschools within 400m |
| `max1_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 6.71 (median 0) | Max over ring-1 neighbours of: Count of primary schools within 1km |
| `max1_pull_cbd` | float64 |  | 0.0 | 0 → 0.969 (median 0.08) | Max over ring-1 neighbours of: Gravity pull toward cbd (distance-decayed attraction) |
| `max1_pull_mall` | float64 |  | 0.0 | 0 → 0.952 (median 0.051) | Max over ring-1 neighbours of: Gravity pull toward mall (distance-decayed attraction) |
| `max1_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.976 (median 0.058) | Max over ring-1 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `max1_tourist_attraction_count` | float64 |  | 0.0 | 0 → 16 (median 0) | Max over ring-1 neighbours of: tourist attraction count (see layer docs) |
| `max1_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.54) | Max over ring-1 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `max1_vibrancy_index` | float64 |  | 0.0 | 0 → 0.988 (median 0.212) | Max over ring-1 neighbours of: Composite: places + magnets + reviews + transit + night lights |
| `max1_walkability_score` | float64 |  | 0.0 | 0 → 0.922 (median 0.465) | Max over ring-1 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `max1_wc_built_share` | float64 |  | 0.0 | 0 → 0.964 (median 0.608) | Max over ring-1 neighbours of: ESA WorldCover land-cover share: built share |
| `max1_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.455) | Max over ring-1 neighbours of: ESA WorldCover land-cover share: tree share |
| `max2_chas_clinic_count` | float64 |  | 0.0 | 0 → 20 (median 2) | Max over ring-2 neighbours of: chas clinic count (see layer docs) |
| `max2_commercial_intensity` | float64 |  | 0.0 | 0 → 0.998 (median 0.152) | Max over ring-2 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `max2_density_pressure` | float64 |  | 0.0 | 0 → 0.778 (median 0.295) | Max over ring-2 neighbours of: Composite: population + buildings + low road space |
| `max2_family_index` | float64 |  | 0.0 | 0 → 0.934 (median 0.389) | Max over ring-2 neighbours of: Composite: children + schools + preschools + family amenities |
| `max2_hawker_centre_count` | float64 |  | 0.0 | 0 → 6 (median 0) | Max over ring-2 neighbours of: hawker centre count (see layer docs) |
| `max2_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 4521) | Max over ring-2 neighbours of: hdb resale 4r median psm (see layer docs) |
| `max2_nl_2024` | float64 |  | 0.0 | 0 → 161.4 (median 67.96) | Max over ring-2 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `max2_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 158.6 (median 57.09) | Max over ring-2 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `max2_pc_cat_business_office` | float64 |  | 0.0 | 0 → 867 (median 22) | Max over ring-2 neighbours of: Place count in cell: business office category (24-cat taxonomy) |
| `max2_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 213 (median 9) | Max over ring-2 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `max2_pc_cat_education` | float64 |  | 0.0 | 0 → 169 (median 14) | Max over ring-2 neighbours of: Place count in cell: education category (24-cat taxonomy) |
| `max2_pc_cat_hawker` | float64 |  | 0.0 | 0 → 246 (median 10) | Max over ring-2 neighbours of: Place count in cell: hawker category (24-cat taxonomy) |
| `max2_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 424 (median 6) | Max over ring-2 neighbours of: Place count in cell: health medical category (24-cat taxonomy) |
| `max2_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 419 (median 25) | Max over ring-2 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `max2_pc_cat_residential` | float64 |  | 0.0 | 0 → 149 (median 19) | Max over ring-2 neighbours of: Place count in cell: residential category (24-cat taxonomy) |
| `max2_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 534 (median 13) | Max over ring-2 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) |
| `max2_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 742 (median 18) | Max over ring-2 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `max2_pc_magnets` | float64 |  | 0.0 | 0 → 980 (median 23) | Max over ring-2 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `max2_pc_total` | float64 |  | 0.0 | 0 → 4929 (median 265) | Max over ring-2 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `max2_pc_unique_brands` | float64 |  | 0.0 | 0 → 125 (median 18) | Max over ring-2 neighbours of: Distinct retail/F&B brands present — chain richness |
| `max2_preschools_within_400m` | float64 |  | 0.0 | 0 → 104 (median 16) | Max over ring-2 neighbours of: Count of preschools within 400m |
| `max2_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 6.71 (median 1) | Max over ring-2 neighbours of: Count of primary schools within 1km |
| `max2_pull_cbd` | float64 |  | 0.0 | 0 → 0.969 (median 0.095) | Max over ring-2 neighbours of: Gravity pull toward cbd (distance-decayed attraction) |
| `max2_pull_mall` | float64 |  | 0.0 | 0 → 0.952 (median 0.062) | Max over ring-2 neighbours of: Gravity pull toward mall (distance-decayed attraction) |
| `max2_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.976 (median 0.085) | Max over ring-2 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `max2_tourist_attraction_count` | float64 |  | 0.0 | 0 → 16 (median 0) | Max over ring-2 neighbours of: tourist attraction count (see layer docs) |
| `max2_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.849) | Max over ring-2 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `max2_vibrancy_index` | float64 |  | 0.0 | 0 → 0.988 (median 0.286) | Max over ring-2 neighbours of: Composite: places + magnets + reviews + transit + night lights |
| `max2_walkability_score` | float64 |  | 0.0 | 0 → 0.922 (median 0.601) | Max over ring-2 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `max2_wc_built_share` | float64 |  | 0.0 | 0 → 0.964 (median 0.771) | Max over ring-2 neighbours of: ESA WorldCover land-cover share: built share |
| `max2_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.607) | Max over ring-2 neighbours of: ESA WorldCover land-cover share: tree share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 1) | Max GPR within hex |
| `mg_avg_anchor_strength` | float64 |  | 0.0 | 0 → 650 (median 0) | Magnet model: strength of the biggest avg anchor place nearby |
| `mg_avg_competitors_400m` | float64 | count | 0.0 | 0 → 90.98 (median 0.455) | Magnet model: mean same-category competitor count within 400 m across categories |
| `mg_avg_walk_dist_mrt_m` | float64 | m | 0.0 | 0 → 9999 (median 1553) | Magnet model: mean walk distance to MRT across category micrographs |
| `mg_bakery_anchor_strength` | float64 |  | 0.0 | 0 → 1225 (median 0) | Magnet model: strength of the biggest bakery anchor place nearby |
| `mg_bakery_pressure_400m` | float64 |  | 0.0 | 0 → 37.96 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bakery |
| `mg_bakery_support_400m` | float64 |  | 0.0 | 0 → 180.4 (median 0) | Magnet model: complementary-category support density within 400 m for bakery (demand context, not supply) |
| `mg_bar_nightlife_anchor_strength` | float64 |  | 0.0 | 0 → 216.8 (median 0) | Magnet model: strength of the biggest bar nightlife anchor place nearby |
| `mg_bar_nightlife_pressure_400m` | float64 |  | 0.0 | 0 → 21.54 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bar nightlife |
| `mg_bar_nightlife_support_400m` | float64 |  | 0.0 | 0 → 92.09 (median 0) | Magnet model: complementary-category support density within 400 m for bar nightlife (demand context, not supply) |
| `mg_beauty_personal_anchor_strength` | float64 |  | 0.0 | 0 → 928 (median 0) | Magnet model: strength of the biggest beauty personal anchor place nearby |
| `mg_beauty_personal_pressure_400m` | float64 |  | 0.0 | 0 → 84.19 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for beauty personal |
| `mg_beauty_personal_support_400m` | float64 |  | 0.0 | 0 → 174.5 (median 0) | Magnet model: complementary-category support density within 400 m for beauty personal (demand context, not supply) |
| `mg_business_office_anchor_strength` | float64 |  | 0.0 | 0 → 287.6 (median 0) | Magnet model: strength of the biggest business office anchor place nearby |
| `mg_business_office_pressure_400m` | float64 |  | 0.0 | 0 → 201.8 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for business office |
| `mg_business_office_support_400m` | float64 |  | 0.0 | 0 → 257.6 (median 0) | Magnet model: complementary-category support density within 400 m for business office (demand context, not supply) |
| `mg_cafe_coffee_anchor_strength` | float64 |  | 0.0 | 0 → 1172 (median 0) | Magnet model: strength of the biggest cafe coffee anchor place nearby |
| `mg_cafe_coffee_pressure_400m` | float64 |  | 0.0 | 0 → 34.92 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for cafe coffee |
| `mg_cafe_coffee_support_400m` | float64 |  | 0.0 | 0 → 162.2 (median 0) | Magnet model: complementary-category support density within 400 m for cafe coffee (demand context, not supply) |
| `mg_convenience_anchor_strength` | float64 |  | 0.0 | 0 → 64.15 (median 0) | Magnet model: strength of the biggest convenience anchor place nearby |
| `mg_convenience_pressure_400m` | float64 |  | 0.0 | 0 → 26.56 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for convenience |
| `mg_convenience_support_400m` | float64 |  | 0.0 | 0 → 23.65 (median 0) | Magnet model: complementary-category support density within 400 m for convenience (demand context, not supply) |
| `mg_education_anchor_strength` | float64 |  | 0.0 | 0 → 39.43 (median 0) | Magnet model: strength of the biggest education anchor place nearby |
| `mg_education_pressure_400m` | float64 |  | 0.0 | 0 → 57.68 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for education |
| `mg_education_support_400m` | float64 |  | 0.0 | 0 → 28.74 (median 0) | Magnet model: complementary-category support density within 400 m for education (demand context, not supply) |
| `mg_entertainment_culture_anchor_strength` | float64 |  | 0.0 | 0 → 1069 (median 0) | Magnet model: strength of the biggest entertainment culture anchor place nearby |
| `mg_entertainment_culture_pressure_400m` | float64 |  | 0.0 | 0 → 17.23 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for entertainment culture |
| `mg_entertainment_culture_support_400m` | float64 |  | 0.0 | 0 → 101.9 (median 0) | Magnet model: complementary-category support density within 400 m for entertainment culture (demand context, not supply) |
| `mg_fast_food_anchor_strength` | float64 |  | 0.0 | 0 → 1103 (median 0) | Magnet model: strength of the biggest fast food anchor place nearby |
| `mg_fast_food_pressure_400m` | float64 |  | 0.0 | 0 → 88 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fast food |
| `mg_fast_food_support_400m` | float64 |  | 0.0 | 0 → 127.7 (median 0) | Magnet model: complementary-category support density within 400 m for fast food (demand context, not supply) |
| `mg_fitness_recreation_anchor_strength` | float64 |  | 0.0 | 0 → 847.9 (median 0) | Magnet model: strength of the biggest fitness recreation anchor place nearby |
| `mg_fitness_recreation_pressure_400m` | float64 |  | 0.0 | 0 → 21.19 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fitness recreation |
| `mg_fitness_recreation_support_400m` | float64 |  | 0.0 | 0 → 121.3 (median 0) | Magnet model: complementary-category support density within 400 m for fitness recreation (demand context, not supply) |
| `mg_government_public_anchor_strength` | float64 |  | 0.0 | 0 → 62.72 (median 0) | Magnet model: strength of the biggest government public anchor place nearby |
| `mg_government_public_pressure_400m` | float64 |  | 0.0 | 0 → 11.87 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for government public |
| `mg_government_public_support_400m` | float64 |  | 0.0 | 0 → 173.8 (median 0) | Magnet model: complementary-category support density within 400 m for government public (demand context, not supply) |
| `mg_hawker_anchor_strength` | float64 |  | 0.0 | 0 → 67.72 (median 0) | Magnet model: strength of the biggest hawker anchor place nearby |
| `mg_hawker_pressure_400m` | float64 |  | 0.0 | 0 → 107.3 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hawker |
| `mg_hawker_support_400m` | float64 |  | 0.0 | 0 → 32 (median 0) | Magnet model: complementary-category support density within 400 m for hawker (demand context, not supply) |
| `mg_health_medical_anchor_strength` | float64 |  | 0.0 | 0 → 56.69 (median 0) | Magnet model: strength of the biggest health medical anchor place nearby |
| `mg_health_medical_pressure_400m` | float64 |  | 0.0 | 0 → 142 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for health medical |
| `mg_health_medical_support_400m` | float64 |  | 0.0 | 0 → 127.9 (median 0) | Magnet model: complementary-category support density within 400 m for health medical (demand context, not supply) |
| `mg_hotel_hospitality_anchor_strength` | float64 |  | 0.0 | 0 → 953.7 (median 0) | Magnet model: strength of the biggest hotel hospitality anchor place nearby |
| `mg_hotel_hospitality_pressure_400m` | float64 |  | 0.0 | 0 → 56.39 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hotel hospitality |
| `mg_hotel_hospitality_support_400m` | float64 |  | 0.0 | 0 → 105.4 (median 0) | Magnet model: complementary-category support density within 400 m for hotel hospitality (demand context, not supply) |
| `mg_industrial_mfg_anchor_strength` | float64 |  | 0.0 | 0 → 250.2 (median 0) | Magnet model: strength of the biggest industrial mfg anchor place nearby |
| `mg_industrial_mfg_pressure_400m` | float64 |  | 0.0 | 0 → 113.6 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for industrial mfg |
| `mg_industrial_mfg_support_400m` | float64 |  | 0.0 | 0 → 321.8 (median 0) | Magnet model: complementary-category support density within 400 m for industrial mfg (demand context, not supply) |
| `mg_other_uncategorized_anchor_strength` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: strength of the biggest other uncategorized anchor place nearby |
| `mg_other_uncategorized_pressure_400m` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for other uncategorized |
| `mg_other_uncategorized_support_400m` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: complementary-category support density within 400 m for other uncategorized (demand context, not supply) |
| `mg_park_open_anchor_strength` | float64 |  | 0.0 | 0 → 27.71 (median 0) | Magnet model: strength of the biggest park open anchor place nearby |
| `mg_park_open_pressure_400m` | float64 |  | 0.0 | 0 → 8.292 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for park open |
| `mg_park_open_support_400m` | float64 |  | 0.0 | 0 → 68.38 (median 0) | Magnet model: complementary-category support density within 400 m for park open (demand context, not supply) |
| `mg_religious_worship_anchor_strength` | float64 |  | 0.0 | 0 → 22.52 (median 0) | Magnet model: strength of the biggest religious worship anchor place nearby |
| `mg_religious_worship_pressure_400m` | float64 |  | 0.0 | 0 → 17.25 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for religious worship |
| `mg_religious_worship_support_400m` | float64 |  | 0.0 | 0 → 25.25 (median 0) | Magnet model: complementary-category support density within 400 m for religious worship (demand context, not supply) |
| `mg_residential_anchor_strength` | float64 |  | 0.0 | 0 → 597.7 (median 0) | Magnet model: strength of the biggest residential anchor place nearby |
| `mg_residential_pressure_400m` | float64 |  | 0.0 | 0 → 18.82 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for residential |
| `mg_residential_support_400m` | float64 |  | 0.0 | 0 → 37.04 (median 0) | Magnet model: complementary-category support density within 400 m for residential (demand context, not supply) |
| `mg_restaurant_anchor_strength` | float64 |  | 0.0 | 0 → 1113 (median 0) | Magnet model: strength of the biggest restaurant anchor place nearby |
| `mg_restaurant_pressure_400m` | float64 |  | 0.0 | 0 → 136.6 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for restaurant |
| `mg_restaurant_support_400m` | float64 |  | 0.0 | 0 → 106.8 (median 0) | Magnet model: complementary-category support density within 400 m for restaurant (demand context, not supply) |
| `mg_services_anchor_strength` | float64 |  | 0.0 | 0 → 1053 (median 0) | Magnet model: strength of the biggest services anchor place nearby |
| `mg_services_pressure_400m` | float64 |  | 0.0 | 0 → 139.7 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for services |
| `mg_services_support_400m` | float64 |  | 0.0 | 0 → 223.3 (median 0) | Magnet model: complementary-category support density within 400 m for services (demand context, not supply) |
| `mg_shopping_retail_anchor_strength` | float64 |  | 0.0 | 0 → 1165 (median 0) | Magnet model: strength of the biggest shopping retail anchor place nearby |
| `mg_shopping_retail_pressure_400m` | float64 |  | 0.0 | 0 → 117.4 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for shopping retail |
| `mg_shopping_retail_support_400m` | float64 |  | 0.0 | 0 → 151.3 (median 0) | Magnet model: complementary-category support density within 400 m for shopping retail (demand context, not supply) |
| `mg_supermarket_anchor_strength` | float64 |  | 0.0 | 0 → 42.41 (median 0) | Magnet model: strength of the biggest supermarket anchor place nearby |
| `mg_supermarket_pressure_400m` | float64 |  | 0.0 | 0 → 32.13 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for supermarket |
| `mg_supermarket_support_400m` | float64 |  | 0.0 | 0 → 128.3 (median 0) | Magnet model: complementary-category support density within 400 m for supermarket (demand context, not supply) |
| `mg_transportation_anchor_strength` | float64 |  | 0.0 | 0 → 999.8 (median 0) | Magnet model: strength of the biggest transportation anchor place nearby |
| `mg_transportation_pressure_400m` | float64 |  | 0.0 | 0 → 18.13 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for transportation |
| `mg_transportation_support_400m` | float64 |  | 0.0 | 0 → 215.9 (median 0) | Magnet model: complementary-category support density within 400 m for transportation (demand context, not supply) |
| `min15_count_essentials` | int64 | count | 0.0 | 0 → 283 (median 2) | Essential amenities within 15 min |
| `min15_count_health` | int64 | count | 0.0 | 0 → 814 (median 1) | Health amenities within 15 min |
| `min15_count_retail` | int64 | count | 0.0 | 0 → 6070 (median 24) | Retail within 15 min |
| `min15_count_school` | int64 | count | 0.0 | 0 → 651 (median 1) | Schools within 15 min |
| `min15_essentials` | float64 | 0-100 | 0.0 | 0 → 100 (median 24.7) | 15-min subscore: daily essentials |
| `min15_health` | float64 | 0-100 | 0.0 | 0 → 100 (median 36.9) | 15-min subscore: health |
| `min15_nearest_super_m` | float64 | m | 0.0 | 6 → 1.437e+04 (median 1473) | Nearest supermarket |
| `min15_retail` | float64 | 0-100 | 0.0 | 0 → 100 (median 89.8) | 15-min subscore: retail |
| `min15_school` | float64 | 0-100 | 0.0 | 0 → 100 (median 17.8) | 15-min subscore: schools |
| `min15_score` | float64 | 0-100 | 0.0 | 0 → 100 (median 37.1) | 15-minute-city score (calibrated: Toa Payoh 100 / Lim Chu Kang 13) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 21 (median 0) | MRT exits in hex |
| `mrt_reach_bus_min` | float64 | min | 58.4 | 4.6 → 40.7 (median 11.8) | Feeder-bus leg of MRT reach |
| `mrt_reach_bus_wait_min` | float64 | min | 58.4 | 0.1 → 15 (median 1.1) | Feeder wait of MRT reach |
| `mrt_reach_crowd` | float64 | index | 0.0 | 0 → 0.9931 (median 0.3361) | Crowding multiplier on the reach path |
| `mrt_reach_index` | float64 | 0-1 | 0.0 | 0 → 1 (median 0.3788) | Composite MRT reach quality |
| `mrt_reach_mode` | object | category | 0.0 | 3 unique · `walk` | Reach mode: walk / feeder / poor |
| `mrt_reach_n_feeders` | int64 | count | 0.0 | 0 → 36 (median 0) | Feeder bus services to nearest MRT |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 5 (median 0) | MRT/LRT stations in hex |
| `mrt_stations_in_1km` | int64 | count | 0.0 | 0 → 12 (median 0) | MRT stations within 1 km |
| `mrt_stations_in_500m` | int64 | count | 0.0 | 0 → 5 (median 0) | MRT stations within 500 m |
| `multimodal_score` | float64 | 0-1 | 0.0 | 0 → 0.7522 (median 0) | Multi-modal option richness |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `n_dest_reachable` | int64 | count | 0.0 | 0 → 17 (median 0) | Key destinations reachable by transit (mobility-v2) |
| `n_dest_within_45min` | int64 | count | 0.0 | 0 → 17 (median 0) | Key destinations within 45-min transit |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 979 (median 0) | Number of buildings with floors ≥ 10 |
| `n_lines_to_cbd` | int64 | count | 0.0 | 0 → 5 (median 0) | Distinct rail lines connecting toward the CBD |
| `n_stations_walking` | int64 | count | 0.0 | 0 → 9 (median 0) | Stations within walking reach |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `nearest_chas_clinic_dist_m` | float64 |  | 0.0 | 1.4 → 1.379e+04 (median 1316) | Distance to nearest chas clinic |
| `nearest_hawker_centre_dist_m` | float64 |  | 0.0 | 17.8 → 1.647e+04 (median 2261) | Distance to nearest hawker centre |
| `nearest_mrt_st_peak_taps` | float64 | taps | 0.0 | 0 → 3.862e+05 (median 4.601e+04) | Peak taps at the nearest MRT station |
| `nearest_preschool_dist_m` | float64 |  | 0.0 | 1.3 → 1.572e+04 (median 1332) | Distance to nearest preschool |
| `nearest_primary_school_dist_m` | float64 |  | 0.0 | 9.5 → 1.602e+04 (median 2178) | Distance to nearest primary school |
| `nearest_school_dist_m` | float64 |  | 0.0 | 4.5 → 1.563e+04 (median 2065) | Distance to nearest school |
| `nearest_tourist_dist_m` | float64 |  | 0.0 | 12.7 → 1.518e+04 (median 3232) | Distance to nearest tourist |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 3.077 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 2.682 → 161.4 (median 49.34) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 107.9 (median 4.208) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 2.682 → 158.6 (median 29.56) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 0.8876 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1825) | Non-resident share of total pop |
| `nvp_affluence_idx` | float64 |  | 0.0 | 0 → 0.6667 (median 0.2137) | NVIDIA Nemotron persona distribution: affluence idx (PA-resolution broadcast) |
| `nvp_ind_construction` | float64 |  | 0.0 | 0 → 0.5 (median 0.0279) | NVIDIA Nemotron persona distribution: ind construction (PA-resolution broadcast) |
| `nvp_ind_finance` | float64 |  | 0.0 | 0 → 0.2143 (median 0.0529) | NVIDIA Nemotron persona distribution: ind finance (PA-resolution broadcast) |
| `nvp_ind_food_accom` | float64 |  | 0.0 | 0 → 0.07143 (median 0.0197) | NVIDIA Nemotron persona distribution: ind food accom (PA-resolution broadcast) |
| `nvp_ind_health` | float64 |  | 0.0 | 0 → 1 (median 0.0382) | NVIDIA Nemotron persona distribution: ind health (PA-resolution broadcast) |
| `nvp_ind_infocomm` | float64 |  | 0.0 | 0 → 0.07143 (median 0.0331) | NVIDIA Nemotron persona distribution: ind infocomm (PA-resolution broadcast) |
| `nvp_ind_manufacturing` | float64 |  | 0.0 | 0 → 0.3571 (median 0.0449) | NVIDIA Nemotron persona distribution: ind manufacturing (PA-resolution broadcast) |
| `nvp_ind_prof_services` | float64 |  | 0.0 | 0 → 0.1053 (median 0.047) | NVIDIA Nemotron persona distribution: ind prof services (PA-resolution broadcast) |
| `nvp_ind_public_edu` | float64 |  | 0.0 | 0 → 0.1429 (median 0) | NVIDIA Nemotron persona distribution: ind public edu (PA-resolution broadcast) |
| `nvp_ind_retail` | float64 |  | 0.0 | 0 → 0.25 (median 0.0728) | NVIDIA Nemotron persona distribution: ind retail (PA-resolution broadcast) |
| `nvp_ind_transport` | float64 |  | 0.0 | 0 → 0.25 (median 0.0333) | NVIDIA Nemotron persona distribution: ind transport (PA-resolution broadcast) |
| `nvp_low_n` | float64 |  | 0.0 | 0 → 1 (median 0) | NVIDIA Nemotron persona distribution: low n (PA-resolution broadcast) |
| `nvp_median_age` | float64 |  | 0.0 | 0 → 90 (median 46) | NVIDIA Nemotron persona distribution: median age (PA-resolution broadcast) |
| `nvp_occ_assoc_prof` | float64 |  | 0.0 | 0 → 0.5 (median 0.1531) | NVIDIA Nemotron persona distribution: occ assoc prof (PA-resolution broadcast) |
| `nvp_occ_clerical` | float64 |  | 0.0 | 0 → 0.07143 (median 0.0333) | NVIDIA Nemotron persona distribution: occ clerical (PA-resolution broadcast) |
| `nvp_occ_homemaker` | float64 |  | 0.0 | 0 → 0.25 (median 0.1071) | NVIDIA Nemotron persona distribution: occ homemaker (PA-resolution broadcast) |
| `nvp_occ_manager` | float64 |  | 0.0 | 0 → 0.2143 (median 0.0946) | NVIDIA Nemotron persona distribution: occ manager (PA-resolution broadcast) |
| `nvp_occ_manual` | float64 |  | 0.0 | 0 → 0.5 (median 0.0443) | NVIDIA Nemotron persona distribution: occ manual (PA-resolution broadcast) |
| `nvp_occ_professional` | float64 |  | 0.0 | 0 → 1 (median 0.1337) | NVIDIA Nemotron persona distribution: occ professional (PA-resolution broadcast) |
| `nvp_occ_retired` | float64 |  | 0.0 | 0 → 1 (median 0.1456) | NVIDIA Nemotron persona distribution: occ retired (PA-resolution broadcast) |
| `nvp_occ_service_sales` | float64 |  | 0.0 | 0 → 0.1429 (median 0.0175) | NVIDIA Nemotron persona distribution: occ service sales (PA-resolution broadcast) |
| `nvp_occ_student` | float64 |  | 0.0 | 0 → 0.1429 (median 0.0182) | NVIDIA Nemotron persona distribution: occ student (PA-resolution broadcast) |
| `nvp_occ_unemployed` | float64 |  | 0.0 | 0 → 0.1333 (median 0.0167) | NVIDIA Nemotron persona distribution: occ unemployed (PA-resolution broadcast) |
| `nvp_pct_age_18_34` | float64 |  | 0.0 | 0 → 0.5 (median 0.2472) | NVIDIA Nemotron persona distribution: pct age 18 34 (PA-resolution broadcast) |
| `nvp_pct_age_35_54` | float64 |  | 0.0 | 0 → 1 (median 0.3441) | NVIDIA Nemotron persona distribution: pct age 35 54 (PA-resolution broadcast) |
| `nvp_pct_age_55plus` | float64 |  | 0.0 | 0 → 1 (median 0.3399) | NVIDIA Nemotron persona distribution: pct age 55plus (PA-resolution broadcast) |
| `nvp_pct_female` | float64 |  | 0.0 | 0 → 1 (median 0.5011) | NVIDIA Nemotron persona distribution: pct female (PA-resolution broadcast) |
| `nvp_pct_married` | float64 |  | 0.0 | 0 → 1 (median 0.6029) | NVIDIA Nemotron persona distribution: pct married (PA-resolution broadcast) |
| `nvp_pct_poly` | float64 |  | 0.0 | 0 → 1 (median 0.0879) | NVIDIA Nemotron persona distribution: pct poly (PA-resolution broadcast) |
| `nvp_pct_secondary_below` | float64 |  | 0.0 | 0 → 1 (median 0.2962) | NVIDIA Nemotron persona distribution: pct secondary below (PA-resolution broadcast) |
| `nvp_pct_single` | float64 |  | 0.0 | 0 → 0.5 (median 0.2759) | NVIDIA Nemotron persona distribution: pct single (PA-resolution broadcast) |
| `nvp_pct_univ` | float64 |  | 0.0 | 0 → 1 (median 0.3143) | NVIDIA Nemotron persona distribution: pct univ (PA-resolution broadcast) |
| `nvp_persona_n` | float64 |  | 0.0 | 0 → 1.04e+04 (median 28) | NVIDIA Nemotron persona distribution: persona n (PA-resolution broadcast) |
| `od_am_pm_out_ratio` | float64 |  | 0.0 | -0.9981 → 0.6117 (median 0) | LTA origin-destination flow metric: am pm out ratio (weekday monthly, bus+train) |
| `od_dest_entropy` | float64 |  | 0.0 | 0 → 4.644 (median 0) | LTA origin-destination flow metric: dest entropy (weekday monthly, bus+train) |
| `od_in_am` | float64 |  | 0.0 | 0 → 1.241e+06 (median 0) | LTA origin-destination flow metric: in am (weekday monthly, bus+train) |
| `od_in_pm` | float64 |  | 0.0 | 0 → 8.394e+05 (median 0) | LTA origin-destination flow metric: in pm (weekday monthly, bus+train) |
| `od_in_trips` | float64 |  | 0.0 | 0 → 2.989e+06 (median 0) | LTA origin-destination flow metric: in trips (weekday monthly, bus+train) |
| `od_n_dest_hex` | float64 |  | 0.0 | 0 → 327 (median 0) | LTA origin-destination flow metric: n dest hex (weekday monthly, bus+train) |
| `od_net_flow` | float64 |  | 0.0 | -2.279e+05 → 1.85e+05 (median 0) | LTA origin-destination flow metric: net flow (weekday monthly, bus+train) |
| `od_out_am` | float64 |  | 0.0 | 0 → 6.81e+05 (median 0) | LTA origin-destination flow metric: out am (weekday monthly, bus+train) |
| `od_out_pm` | float64 |  | 0.0 | 0 → 1.106e+06 (median 0) | LTA origin-destination flow metric: out pm (weekday monthly, bus+train) |
| `od_out_trips` | float64 |  | 0.0 | 0 → 2.935e+06 (median 0) | LTA origin-destination flow metric: out trips (weekday monthly, bus+train) |
| `od_self_containment` | float64 |  | 0.0 | 0 → 0.1757 (median 0) | LTA origin-destination flow metric: self containment (weekday monthly, bus+train) |
| `od_self_trips` | float64 |  | 0.0 | 0 → 1.497e+05 (median 0) | LTA origin-destination flow metric: self trips (weekday monthly, bus+train) |
| `od_throughput` | float64 |  | 0.0 | 0 → 5.924e+06 (median 0) | LTA origin-destination flow metric: throughput (weekday monthly, bus+train) |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1692) | Fraction of vehicular length that's one-way |
| `osm_amenities_count` | int64 | count | 0.0 | 0 → 940 (median 1) | OSM amenity-tagged POIs in cell (independent ground truth) |
| `osm_leisure_count` | int64 | count | 0.0 | 0 → 147 (median 0) | OSM leisure-tagged POIs in cell |
| `osm_shops_count` | int64 | count | 0.0 | 0 → 310 (median 0) | OSM shop-tagged POIs in cell — independent retail frontage |
| `osm_tourism_count` | int64 | count | 0.0 | 0 → 183 (median 0) | OSM tourism-tagged POIs in cell |
| `parent_pa` | object | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | object | string | 0.0 | 270 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | object | string | 0.0 | 270 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 28 (median 0) | OSM amenity=parking points |
| `pc2_branded_count` | int64 |  | 0.0 | 0 → 221 (median 0) | Fine-taxonomy place metric: branded count |
| `pc2_cat_biz_office_count` | int64 |  | 0.0 | 0 → 209 (median 0) | Place count in cell: biz office (55-cat fine taxonomy) |
| `pc2_cat_civic_community_count` | int64 |  | 0.0 | 0 → 9 (median 0) | Place count in cell: civic community (55-cat fine taxonomy) |
| `pc2_cat_civic_government_count` | int64 |  | 0.0 | 0 → 35 (median 0) | Place count in cell: civic government (55-cat fine taxonomy) |
| `pc2_cat_civic_nonprofit_count` | int64 |  | 0.0 | 0 → 52 (median 0) | Place count in cell: civic nonprofit (55-cat fine taxonomy) |
| `pc2_cat_civic_religious_count` | int64 |  | 0.0 | 0 → 37 (median 0) | Place count in cell: civic religious (55-cat fine taxonomy) |
| `pc2_cat_edu_preschool_count` | int64 |  | 0.0 | 0 → 35 (median 0) | Place count in cell: edu preschool (55-cat fine taxonomy) |
| `pc2_cat_edu_primary_secondary_count` | int64 |  | 0.0 | 0 → 60 (median 0) | Place count in cell: edu primary secondary (55-cat fine taxonomy) |
| `pc2_cat_edu_specialty_count` | int64 |  | 0.0 | 0 → 12 (median 0) | Place count in cell: edu specialty (55-cat fine taxonomy) |
| `pc2_cat_edu_tertiary_count` | int64 |  | 0.0 | 0 → 19 (median 0) | Place count in cell: edu tertiary (55-cat fine taxonomy) |
| `pc2_cat_edu_tuition_count` | int64 |  | 0.0 | 0 → 129 (median 0) | Place count in cell: edu tuition (55-cat fine taxonomy) |
| `pc2_cat_food_bakery_count` | int64 |  | 0.0 | 0 → 36 (median 0) | Place count in cell: food bakery (55-cat fine taxonomy) |
| `pc2_cat_food_bar_count` | int64 |  | 0.0 | 0 → 79 (median 0) | Place count in cell: food bar (55-cat fine taxonomy) |
| `pc2_cat_food_cafe_count` | int64 |  | 0.0 | 0 → 152 (median 0) | Place count in cell: food cafe (55-cat fine taxonomy) |
| `pc2_cat_food_caterer_count` | int64 |  | 0.0 | 0 → 17 (median 0) | Place count in cell: food caterer (55-cat fine taxonomy) |
| `pc2_cat_food_dessert_count` | int64 |  | 0.0 | 0 → 66 (median 0) | Place count in cell: food dessert (55-cat fine taxonomy) |
| `pc2_cat_food_fast_food_count` | int64 |  | 0.0 | 0 → 18 (median 0) | Place count in cell: food fast food (55-cat fine taxonomy) |
| `pc2_cat_food_hawker_count` | int64 |  | 0.0 | 0 → 246 (median 0) | Place count in cell: food hawker (55-cat fine taxonomy) |
| `pc2_cat_food_restaurant_count` | int64 |  | 0.0 | 0 → 503 (median 0) | Place count in cell: food restaurant (55-cat fine taxonomy) |
| `pc2_cat_health_clinic_count` | int64 |  | 0.0 | 0 → 133 (median 0) | Place count in cell: health clinic (55-cat fine taxonomy) |
| `pc2_cat_health_hospital_count` | int64 |  | 0.0 | 0 → 46 (median 0) | Place count in cell: health hospital (55-cat fine taxonomy) |
| `pc2_cat_health_pharmacy_count` | int64 |  | 0.0 | 0 → 32 (median 0) | Place count in cell: health pharmacy (55-cat fine taxonomy) |
| `pc2_cat_health_specialist_count` | int64 |  | 0.0 | 0 → 183 (median 0) | Place count in cell: health specialist (55-cat fine taxonomy) |
| `pc2_cat_health_tcm_count` | int64 |  | 0.0 | 0 → 16 (median 0) | Place count in cell: health tcm (55-cat fine taxonomy) |
| `pc2_cat_leisure_entertainment_count` | int64 |  | 0.0 | 0 → 32 (median 0) | Place count in cell: leisure entertainment (55-cat fine taxonomy) |
| `pc2_cat_leisure_park_count` | int64 |  | 0.0 | 0 → 28 (median 0) | Place count in cell: leisure park (55-cat fine taxonomy) |
| `pc2_cat_leisure_tourist_count` | int64 |  | 0.0 | 0 → 50 (median 0) | Place count in cell: leisure tourist (55-cat fine taxonomy) |
| `pc2_cat_other_count` | int64 |  | 0.0 | 0 → 926 (median 4) | Place count in cell: other (55-cat fine taxonomy) |
| `pc2_cat_res_aged_care_count` | int64 |  | 0.0 | 0 → 8 (median 0) | Place count in cell: res aged care (55-cat fine taxonomy) |
| `pc2_cat_res_hdb_count` | int64 |  | 0.0 | 0 → 90 (median 0) | Place count in cell: res hdb (55-cat fine taxonomy) |
| `pc2_cat_res_private_count` | int64 |  | 0.0 | 0 → 103 (median 0) | Place count in cell: res private (55-cat fine taxonomy) |
| `pc2_cat_retail_apparel_count` | int64 |  | 0.0 | 0 → 265 (median 0) | Place count in cell: retail apparel (55-cat fine taxonomy) |
| `pc2_cat_retail_convenience_count` | int64 |  | 0.0 | 0 → 64 (median 0) | Place count in cell: retail convenience (55-cat fine taxonomy) |
| `pc2_cat_retail_electronics_count` | int64 |  | 0.0 | 0 → 87 (median 0) | Place count in cell: retail electronics (55-cat fine taxonomy) |
| `pc2_cat_retail_furniture_home_count` | int64 |  | 0.0 | 0 → 85 (median 0) | Place count in cell: retail furniture home (55-cat fine taxonomy) |
| `pc2_cat_retail_general_count` | int64 |  | 0.0 | 0 → 94 (median 0) | Place count in cell: retail general (55-cat fine taxonomy) |
| `pc2_cat_retail_jewelry_cosmetics_count` | int64 |  | 0.0 | 0 → 265 (median 0) | Place count in cell: retail jewelry cosmetics (55-cat fine taxonomy) |
| `pc2_cat_retail_mall_count` | int64 |  | 0.0 | 0 → 31 (median 0) | Place count in cell: retail mall (55-cat fine taxonomy) |
| `pc2_cat_retail_supermarket_count` | int64 |  | 0.0 | 0 → 55 (median 0) | Place count in cell: retail supermarket (55-cat fine taxonomy) |
| `pc2_cat_service_automotive_count` | int64 |  | 0.0 | 0 → 234 (median 0) | Place count in cell: service automotive (55-cat fine taxonomy) |
| `pc2_cat_service_beauty_count` | int64 |  | 0.0 | 0 → 324 (median 0) | Place count in cell: service beauty (55-cat fine taxonomy) |
| `pc2_cat_service_cleaning_repair_count` | int64 |  | 0.0 | 0 → 29 (median 0) | Place count in cell: service cleaning repair (55-cat fine taxonomy) |
| `pc2_cat_service_consulting_count` | int64 |  | 0.0 | 0 → 637 (median 0) | Place count in cell: service consulting (55-cat fine taxonomy) |
| `pc2_cat_service_fitness_count` | int64 |  | 0.0 | 0 → 86 (median 0) | Place count in cell: service fitness (55-cat fine taxonomy) |
| `pc2_cat_service_legal_finance_count` | int64 |  | 0.0 | 0 → 378 (median 0) | Place count in cell: service legal finance (55-cat fine taxonomy) |
| `pc2_cat_service_logistics_count` | int64 |  | 0.0 | 0 → 312 (median 0) | Place count in cell: service logistics (55-cat fine taxonomy) |
| `pc2_cat_service_other_count` | int64 |  | 0.0 | 0 → 304 (median 0) | Place count in cell: service other (55-cat fine taxonomy) |
| `pc2_cat_service_pet_count` | int64 |  | 0.0 | 0 → 9 (median 0) | Place count in cell: service pet (55-cat fine taxonomy) |
| `pc2_cat_service_real_estate_count` | int64 |  | 0.0 | 0 → 113 (median 0) | Place count in cell: service real estate (55-cat fine taxonomy) |
| `pc2_cat_transport_air_count` | int64 |  | 0.0 | 0 → 7 (median 0) | Place count in cell: transport air (55-cat fine taxonomy) |
| `pc2_cat_transport_bus_count` | int64 |  | 0.0 | 0 → 42 (median 0) | Place count in cell: transport bus (55-cat fine taxonomy) |
| `pc2_cat_transport_ev_count` | int64 |  | 0.0 | 0 → 23 (median 0) | Place count in cell: transport ev (55-cat fine taxonomy) |
| `pc2_cat_transport_mrt_count` | int64 |  | 0.0 | 0 → 10 (median 0) | Place count in cell: transport mrt (55-cat fine taxonomy) |
| `pc2_cat_transport_other_count` | int64 |  | 0.0 | 0 → 6 (median 0) | Place count in cell: transport other (55-cat fine taxonomy) |
| `pc2_cat_transport_parking_count` | int64 |  | 0.0 | 0 → 39 (median 0) | Place count in cell: transport parking (55-cat fine taxonomy) |
| `pc2_cat_unmapped_count` | int64 |  | 0.0 | 0 → 62 (median 0) | Place count in cell: unmapped (55-cat fine taxonomy) |
| `pc2_dominant_category` | object |  | 0.0 | 30 unique · `none` | Fine-taxonomy place metric: dominant category |
| `pc2_total` | int64 |  | 0.0 | 0 → 4929 (median 10) | Fine-taxonomy place metric: total |
| `pc2_unbranded_count` | int64 |  | 0.0 | 0 → 4752 (median 10) | Fine-taxonomy place metric: unbranded count |
| `pc_avg_rating` | float64 | stars | 0.0 | 0 → 5 (median 4.24) | Mean rating of rated places — quality proxy |
| `pc_cat_bakery` | float64 |  | 0.0 | 0 → 39 (median 0) | Place count in cell: bakery category (24-cat taxonomy) |
| `pc_cat_bar_nightlife` | float64 |  | 0.0 | 0 → 88 (median 0) | Place count in cell: bar nightlife category (24-cat taxonomy) |
| `pc_cat_beauty_personal` | float64 |  | 0.0 | 0 → 351 (median 0) | Place count in cell: beauty personal category (24-cat taxonomy) |
| `pc_cat_business_office` | float64 |  | 0.0 | 0 → 867 (median 0) | Place count in cell: business office category (24-cat taxonomy) |
| `pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 213 (median 0) | Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pc_cat_convenience` | float64 |  | 0.0 | 0 → 83 (median 0) | Place count in cell: convenience category (24-cat taxonomy) |
| `pc_cat_education` | float64 |  | 0.0 | 0 → 169 (median 0) | Place count in cell: education category (24-cat taxonomy) |
| `pc_cat_entertainment_culture` | float64 |  | 0.0 | 0 → 88 (median 0) | Place count in cell: entertainment culture category (24-cat taxonomy) |
| `pc_cat_fast_food` | float64 |  | 0.0 | 0 → 18 (median 0) | Place count in cell: fast food category (24-cat taxonomy) |
| `pc_cat_fitness_recreation` | float64 |  | 0.0 | 0 → 89 (median 0) | Place count in cell: fitness recreation category (24-cat taxonomy) |
| `pc_cat_government_public` | float64 |  | 0.0 | 0 → 41 (median 0) | Place count in cell: government public category (24-cat taxonomy) |
| `pc_cat_hawker` | float64 |  | 0.0 | 0 → 246 (median 0) | Place count in cell: hawker category (24-cat taxonomy) |
| `pc_cat_health_medical` | float64 |  | 0.0 | 0 → 424 (median 0) | Place count in cell: health medical category (24-cat taxonomy) |
| `pc_cat_hotel_hospitality` | float64 |  | 0.0 | 0 → 64 (median 0) | Place count in cell: hotel hospitality category (24-cat taxonomy) |
| `pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 419 (median 1) | Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pc_cat_other_uncategorized` | float64 |  | 0.0 | 0 → 521 (median 2) | Place count in cell: other uncategorized category (24-cat taxonomy) |
| `pc_cat_park_open` | float64 |  | 0.0 | 0 → 36 (median 0) | Place count in cell: park open category (24-cat taxonomy) |
| `pc_cat_religious_worship` | float64 |  | 0.0 | 0 → 44 (median 0) | Place count in cell: religious worship category (24-cat taxonomy) |
| `pc_cat_residential` | float64 |  | 0.0 | 0 → 149 (median 0) | Place count in cell: residential category (24-cat taxonomy) |
| `pc_cat_restaurant` | float64 |  | 0.0 | 0 → 534 (median 0) | Place count in cell: restaurant category (24-cat taxonomy) |
| `pc_cat_services` | float64 |  | 0.0 | 0 → 777 (median 0) | Place count in cell: services category (24-cat taxonomy) |
| `pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 742 (median 0) | Place count in cell: shopping retail category (24-cat taxonomy) |
| `pc_cat_supermarket` | float64 |  | 0.0 | 0 → 68 (median 0) | Place count in cell: supermarket category (24-cat taxonomy) |
| `pc_cat_transportation` | float64 |  | 0.0 | 0 → 143 (median 1) | Place count in cell: transportation category (24-cat taxonomy) |
| `pc_diversity` | float64 | 0-1 | 0.0 | 0 → 2.909 (median 1.427) | Category entropy of the place mix — high = mixed-use |
| `pc_dominant_category` | object | category | 0.0 | 22 unique · `none` | Most common place category in cell |
| `pc_long_tail` | float64 | count | 0.0 | 0 → 2392 (median 6) | Places with few/no reviews — independent long-tail share base |
| `pc_magnets` | float64 | count | 0.0 | 0 → 980 (median 0) | High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pc_total` | float64 | count | 0.0 | 0 → 4929 (median 10) | Total mapped places (POIs) in cell — overall point-of-interest density |
| `pc_total_reviews` | float64 | count | 0.0 | 0 → 8.951e+05 (median 238) | Sum of review counts — popularity/footfall proxy |
| `pc_unique_brands` | float64 | count | 0.0 | 0 → 125 (median 0) | Distinct retail/F&B brands present — chain richness |
| `pc_with_rating` | float64 | count | 0.0 | 0 → 3078 (median 5) | Places carrying a Google rating |
| `pct_dest_within_45min` | float64 | ratio | 0.0 | 0 → 100 (median 0) | Share of key destinations within 45 min |
| `pct_dest_within_60min` | float64 | ratio | 0.0 | 0 → 100 (median 0) | Share of key destinations within 60 min |
| `peak_wait_bus_only_min` | float64 | min | 58.9 | 1.5 → 30 (median 7) | Peak wait, bus only |
| `peak_wait_min` | float64 | min | 56.1 | 1.275 → 12.5 (median 2.8) | Expected peak-hour wait (best mode) |
| `peak_wait_mrt_only_min` | float64 | min | 73.5 | 2.5 → 5 (median 2.5) | Peak wait, MRT only |
| `ped_countdown` | int64 |  | 0.0 | 0 → 34 (median 0) | Road-network metric: ped countdown |
| `ped_greenman_count` | int64 | count | 0.0 | 0 → 12 (median 0) | Green Man+ (extended-time) crossings |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 74.58 (median 6.807) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 5.482e+04 (median 4281) | Footway + path + cycleway + steps length |
| `petrol_station_count` | float64 | count | 0.0 | 0 → 4 (median 0) | Fuel stations in hex (OSM, 201 islandwide) |
| `pipe_dev_capacity_com` | float64 | FAR-units | 0.0 | 0 → 1.781 (median 0) | FAR headroom × (commercial + mixed) zoning share |
| `pipe_dev_capacity_res` | float64 | FAR-units | 0.0 | 0 → 1.793 (median 0) | FAR headroom (avg_gpr − est_built_far)⁺ × residential zoning share. Matilda 0.50 / Bidadari 0.34 / built-out Toa Payoh Ctrl 0 |
| `pipe_mrt_dist_m` | float64 | m | 0.0 | 11.4 → 1.535e+04 (median 4403) | Distance to nearest future rail station |
| `pipe_mrt_name` | object | string | 0.0 | 35 unique · `JURONG PIER` | Nearest future station name |
| `pipe_new_mrt_within_800m` | bool | bool | 0.0 | 0 → 1 (median 0) | Future rail station (MP2019 minus existing Mar-2026; 37 stations: full JRL + Keppel CCL6) within 800 m |
| `polyclinic_count` | float64 | count | 0.0 | 0 → 1 (median 0) | Public polyclinics in hex (27 islandwide) |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 7274 (median 0.1151) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 2.692e+04 (median 1.372) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 7709 (median 0.1071) | Population age 65+ |
| `pop_dorm` | float64 | persons | 0.0 | 0 → 3.095e+04 (median 0) | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 3.484e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 9707 (median 1.609) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 3.339e+04 (median 448.8) | Non-residents (FW + EP + MDW) |
| `pop_nr_ep` | float64 | persons | 0.0 | 0 → 1.749e+04 (median 0) | Employment-pass holders |
| `pop_nr_fdw` | float64 | persons | 0.0 | 0 → 4192 (median 0) | Foreign domestic workers |
| `pop_nr_sp` | float64 | persons | 0.0 | 0 → 7115 (median 0) | S-pass holders |
| `pop_nr_wp_other` | float64 | persons | 0.0 | 0 → 9062 (median 0) | Other work-permit holders (non-dorm) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 3.813e+04 (median 2.017) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 4.21e+04 (median 603.1) | Total population (residents + non-residents) |
| `pr_share` | float64 | ratio | 65.2 | 0.1286 → 0.1286 (median 0.1286) | PR share of resident population (citizen/PR ratio signal; levels deduped away) |
| `preschool_count` | int64 |  | 0.0 | 0 → 26 (median 0) | preschool count (see layer docs) |
| `preschools_within_400m` | int64 |  | 0.0 | 0 → 104 (median 0) | Count of preschools within 400m |
| `primary_school_zone_count` | int64 | count | 0.0 | 0 → 9 (median 0) | Primary-school zones overlapping cell |
| `primary_schools_within_1km` | float64 |  | 0.0 | 0 → 6.71 (median 0) | Count of primary schools within 1km |
| `primary_schools_within_2km` | float64 |  | 0.0 | 0 → 18 (median 0) | Count of primary schools within 2km |
| `pull_airport` | float64 |  | 0.0 | 0.001 → 0.998 (median 0.224) | Gravity pull toward airport (distance-decayed attraction) |
| `pull_cbd` | float64 |  | 0.0 | 0 → 0.969 (median 0.068) | Gravity pull toward cbd (distance-decayed attraction) |
| `pull_composite` | float64 |  | 0.0 | 0.001 → 0.755 (median 0.128) | Gravity pull toward composite (distance-decayed attraction) |
| `pull_hospital` | float64 |  | 0.0 | 0 → 0.979 (median 0.071) | Gravity pull toward hospital (distance-decayed attraction) |
| `pull_mall` | float64 |  | 0.0 | 0 → 0.952 (median 0.039) | Gravity pull toward mall (distance-decayed attraction) |
| `pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.976 (median 0.041) | Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pull_school_premium` | float64 |  | 0.0 | 0 → 0.975 (median 0.094) | Gravity pull toward school premium (distance-decayed attraction) |
| `pw1_chas_clinic_count` | float64 |  | 0.0 | 0 → 14.28 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: chas clinic count (see layer docs) |
| `pw1_commercial_intensity` | float64 |  | 0.0 | 0 → 0.839 (median 0.039) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `pw1_density_pressure` | float64 |  | 0.0 | 0 → 0.767 (median 0.021) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: population + buildings + low road space |
| `pw1_family_index` | float64 |  | 0.0 | 0 → 0.876 (median 0.141) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: children + schools + preschools + family amenities |
| `pw1_hawker_centre_count` | float64 |  | 0.0 | 0 → 4.125 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: hawker centre count (see layer docs) |
| `pw1_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 8851 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: hdb resale 4r median psm (see layer docs) |
| `pw1_nl_2024` | float64 |  | 0.0 | 0 → 158.6 (median 31.24) | Proximity-weighted (distance-decayed) ring-1 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `pw1_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 158.5 (median 17.37) | Proximity-weighted (distance-decayed) ring-1 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `pw1_pc_cat_business_office` | float64 |  | 0.0 | 0 → 709 (median 1.201) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: business office category (24-cat taxonomy) |
| `pw1_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 160.7 (median 0.206) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pw1_pc_cat_education` | float64 |  | 0.0 | 0 → 111.1 (median 0.345) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: education category (24-cat taxonomy) |
| `pw1_pc_cat_hawker` | float64 |  | 0.0 | 0 → 171.2 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: hawker category (24-cat taxonomy) |
| `pw1_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 144.6 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: health medical category (24-cat taxonomy) |
| `pw1_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 246.2 (median 0.926) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pw1_pc_cat_residential` | float64 |  | 0.0 | 0 → 125.9 (median 0.523) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: residential category (24-cat taxonomy) |
| `pw1_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 395.5 (median 0.986) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) |
| `pw1_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 255.5 (median 0.579) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `pw1_pc_magnets` | float64 |  | 0.0 | 0 → 739.4 (median 2) | Proximity-weighted (distance-decayed) ring-1 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pw1_pc_total` | float64 |  | 0.0 | 0 → 3862 (median 25.32) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `pw1_pc_unique_brands` | float64 |  | 0.0 | 0 → 74.35 (median 0.867) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Distinct retail/F&B brands present — chain richness |
| `pw1_preschools_within_400m` | float64 |  | 0.0 | 0 → 70.56 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of preschools within 400m |
| `pw1_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 5.408 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of primary schools within 1km |
| `pw1_pull_cbd` | float64 |  | 0.0 | 0 → 0.942 (median 0.047) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward cbd (distance-decayed attraction) |
| `pw1_pull_mall` | float64 |  | 0.0 | 0 → 0.901 (median 0.038) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mall (distance-decayed attraction) |
| `pw1_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.903 (median 0.033) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pw1_tourist_attraction_count` | float64 |  | 0.0 | 0 → 9.488 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: tourist attraction count (see layer docs) |
| `pw1_transit_score` | float64 |  | 0.0 | 0 → 0.976 (median 0.386) | Proximity-weighted (distance-decayed) ring-1 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `pw1_vibrancy_index` | float64 |  | 0.0 | 0 → 0.891 (median 0.137) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: places + magnets + reviews + transit + night lights |
| `pw1_walkability_score` | float64 |  | 0.0 | 0 → 0.892 (median 0.255) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `pw1_wc_built_share` | float64 |  | 0.0 | 0 → 0.909 (median 0.211) | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: built share |
| `pw1_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.16) | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: tree share |
| `pw2_chas_clinic_count` | float64 |  | 0.0 | 0 → 10.44 (median 0.53) | Proximity-weighted ring-2 aggregate of: chas clinic count (see layer docs) |
| `pw2_commercial_intensity` | float64 |  | 0.0 | 0 → 0.769 (median 0.077) | Proximity-weighted ring-2 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `pw2_density_pressure` | float64 |  | 0.0 | 0 → 0.72 (median 0.143) | Proximity-weighted ring-2 aggregate of: Composite: population + buildings + low road space |
| `pw2_family_index` | float64 |  | 0.0 | 0 → 0.851 (median 0.314) | Proximity-weighted ring-2 aggregate of: Composite: children + schools + preschools + family amenities |
| `pw2_hawker_centre_count` | float64 |  | 0.0 | 0 → 2.591 (median 0) | Proximity-weighted ring-2 aggregate of: hawker centre count (see layer docs) |
| `pw2_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 8537 (median 3947) | Proximity-weighted ring-2 aggregate of: hdb resale 4r median psm (see layer docs) |
| `pw2_nl_2024` | float64 |  | 0.0 | 0 → 158.6 (median 46.27) | Proximity-weighted ring-2 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `pw2_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 158.5 (median 19.5) | Proximity-weighted ring-2 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `pw2_pc_cat_business_office` | float64 |  | 0.0 | 0 → 547.5 (median 5.797) | Proximity-weighted ring-2 aggregate of: Place count in cell: business office category (24-cat taxonomy) |
| `pw2_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 133.7 (median 4.277) | Proximity-weighted ring-2 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pw2_pc_cat_education` | float64 |  | 0.0 | 0 → 95.91 (median 7.335) | Proximity-weighted ring-2 aggregate of: Place count in cell: education category (24-cat taxonomy) |
| `pw2_pc_cat_hawker` | float64 |  | 0.0 | 0 → 112 (median 3.275) | Proximity-weighted ring-2 aggregate of: Place count in cell: hawker category (24-cat taxonomy) |
| `pw2_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 124.4 (median 2.998) | Proximity-weighted ring-2 aggregate of: Place count in cell: health medical category (24-cat taxonomy) |
| `pw2_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 202.8 (median 5.048) | Proximity-weighted ring-2 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pw2_pc_cat_residential` | float64 |  | 0.0 | 0 → 118.7 (median 12.68) | Proximity-weighted ring-2 aggregate of: Place count in cell: residential category (24-cat taxonomy) |
| `pw2_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 317.1 (median 6.057) | Proximity-weighted ring-2 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) |
| `pw2_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 224.1 (median 6.522) | Proximity-weighted ring-2 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `pw2_pc_magnets` | float64 |  | 0.0 | 0 → 612 (median 11.59) | Proximity-weighted ring-2 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pw2_pc_total` | float64 |  | 0.0 | 0 → 3057 (median 148.2) | Proximity-weighted ring-2 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `pw2_pc_unique_brands` | float64 |  | 0.0 | 0 → 70.05 (median 8.154) | Proximity-weighted ring-2 aggregate of: Distinct retail/F&B brands present — chain richness |
| `pw2_preschools_within_400m` | float64 |  | 0.0 | 0 → 70.7 (median 10.12) | Proximity-weighted ring-2 aggregate of: Count of preschools within 400m |
| `pw2_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 5.557 (median 0.624) | Proximity-weighted ring-2 aggregate of: Count of primary schools within 1km |
| `pw2_pull_cbd` | float64 |  | 0.0 | 0 → 0.923 (median 0.062) | Proximity-weighted ring-2 aggregate of: Gravity pull toward cbd (distance-decayed attraction) |
| `pw2_pull_mall` | float64 |  | 0.0 | 0 → 0.794 (median 0.053) | Proximity-weighted ring-2 aggregate of: Gravity pull toward mall (distance-decayed attraction) |
| `pw2_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.825 (median 0.059) | Proximity-weighted ring-2 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pw2_tourist_attraction_count` | float64 |  | 0.0 | 0 → 7.5 (median 0) | Proximity-weighted ring-2 aggregate of: tourist attraction count (see layer docs) |
| `pw2_transit_score` | float64 |  | 0.0 | 0 → 0.963 (median 0.603) | Proximity-weighted ring-2 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `pw2_vibrancy_index` | float64 |  | 0.0 | 0 → 0.831 (median 0.221) | Proximity-weighted ring-2 aggregate of: Composite: places + magnets + reviews + transit + night lights |
| `pw2_walkability_score` | float64 |  | 0.0 | 0 → 0.846 (median 0.501) | Proximity-weighted ring-2 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `pw2_wc_built_share` | float64 |  | 0.0 | 0 → 0.883 (median 0.456) | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: built share |
| `pw2_wc_tree_share` | float64 |  | 0.0 | 0 → 0.988 (median 0.182) | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: tree share |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 7810 (median 0) | Rail line length through hex (above + underground) |
| `rent_resi_n_obs` | int64 | count | 0.0 | 0 → 5 (median 1) | Projects within 2.5 km supporting the estimate |
| `rent_resi_psf_med` | float64 | $psf/month | 47.5 | 2.02 → 8.174 (median 4.412) | URA private-resi median rent (913 projects, last 4 quarters, IDW k=5 ≤2.5 km). COMMERCIAL rent not openly available. NaN = no observation in range |
| `rent_resolution` | object | category | 0.0 | 3 unique · `none` | local (≤800 m) / idw / none |
| `ring1_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 8833 (median 0) | Sum over H3 ring-1 neighbours (~±1 km) of: hdb resale 4r median psm (see layer docs) |
| `ring1_nl_2024` | float64 |  | 0.0 | 0 → 158.6 (median 50.01) | Sum over H3 ring-1 neighbours (~±1 km) of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `ring1_pc_magnets` | float64 |  | 0.0 | 0 → 452.5 (median 2) | Sum over H3 ring-1 neighbours (~±1 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `ring1_pc_total` | float64 |  | 0.0 | 0 → 2340 (median 40.83) | Sum over H3 ring-1 neighbours (~±1 km) of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `ring1_pop_nonresident` | float64 |  | 0.0 | 0 → 1.5e+04 (median 1017) | Sum over H3 ring-1 neighbours (~±1 km) of: Non-residents (FW + EP + MDW) |
| `ring1_pop_resident` | float64 |  | 0.0 | 0 → 3.232e+04 (median 51.41) | Sum over H3 ring-1 neighbours (~±1 km) of: Resident population (citizens + PRs) |
| `ring1_school_count_total` | float64 |  | 0.0 | 0 → 16 (median 0) | Sum over H3 ring-1 neighbours (~±1 km) of: school count total (see layer docs) |
| `ring1_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.54) | Sum over H3 ring-1 neighbours (~±1 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `ring1_walkability_score` | float64 |  | 0.0 | 0 → 0.864 (median 0.24) | Sum over H3 ring-1 neighbours (~±1 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `ring2_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 7560 (median 873.8) | Sum over H3 ring-2 neighbours (~±2 km) of: hdb resale 4r median psm (see layer docs) |
| `ring2_nl_2024` | float64 |  | 0.0 | 0 → 158.6 (median 50.08) | Sum over H3 ring-2 neighbours (~±2 km) of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `ring2_pc_magnets` | float64 |  | 0.0 | 0 → 291 (median 4.583) | Sum over H3 ring-2 neighbours (~±2 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `ring2_pc_total` | float64 |  | 0.0 | 0 → 1608 (median 76.17) | Sum over H3 ring-2 neighbours (~±2 km) of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `ring2_pop_nonresident` | float64 |  | 0.0 | 0 → 9341 (median 1240) | Sum over H3 ring-2 neighbours (~±2 km) of: Non-residents (FW + EP + MDW) |
| `ring2_pop_resident` | float64 |  | 0.0 | 0 → 2.14e+04 (median 807.6) | Sum over H3 ring-2 neighbours (~±2 km) of: Resident population (citizens + PRs) |
| `ring2_school_count_total` | float64 |  | 0.0 | 0 → 20 (median 0) | Sum over H3 ring-2 neighbours (~±2 km) of: school count total (see layer docs) |
| `ring2_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.849) | Sum over H3 ring-2 neighbours (~±2 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `ring2_walkability_score` | float64 |  | 0.0 | 0 → 0.808 (median 0.278) | Sum over H3 ring-2 neighbours (~±2 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 112.5 (median 22.68) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 523 (median 73) | Road-network metric: road intersection count total |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 709.6 (median 99.05) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 8.288e+04 (median 1.671e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3055) | Pedestrian-only roads as fraction of total |
| `roi_cap_per_rent_cafe_coffee` | float64 | ratio | 47.5 | 0.0019 → 1.126 (median 0.219) | cap_cafe_coffee / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_restaurant` | float64 | ratio | 47.5 | 0.0012 → 1.148 (median 0.2529) | cap_restaurant / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_shopping_retail` | float64 | ratio | 47.5 | 0.0023 → 1.208 (median 0.2573) | cap_shopping_retail / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_supermarket` | float64 | ratio | 47.5 | 0.0005 → 0.9638 (median 0.1866) | cap_supermarket / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_total` | float64 | ratio | 47.5 | 0.0302 → 10.96 (median 2.277) | cap_total / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `sat_bakery_per_1k` | float64 |  | 0.0 | 0 → 38.86 (median 0) | Supply saturation: bakery outlets per 1,000 residents |
| `sat_beauty_personal_per_1k` | float64 |  | 0.0 | 0 → 80.04 (median 0) | Supply saturation: beauty personal outlets per 1,000 residents |
| `sat_cafe_coffee_per_1k` | float64 |  | 0.0 | 0 → 105.5 (median 0) | Supply saturation: cafe coffee outlets per 1,000 residents |
| `sat_fast_food_per_1k` | float64 |  | 0.0 | 0 → 22.39 (median 0) | Supply saturation: fast food outlets per 1,000 residents |
| `sat_fitness_recreation_per_1k` | float64 |  | 0.0 | 0 → 23.4 (median 0) | Supply saturation: fitness recreation outlets per 1,000 residents |
| `sat_hawker_per_1k` | float64 |  | 0.0 | 0 → 75.8 (median 0) | Supply saturation: hawker outlets per 1,000 residents |
| `sat_health_medical_per_1k` | float64 |  | 0.0 | 0 → 87.65 (median 0) | Supply saturation: health medical outlets per 1,000 residents |
| `sat_restaurant_per_1k` | float64 |  | 0.0 | 0 → 172 (median 0) | Supply saturation: restaurant outlets per 1,000 residents |
| `sat_supermarket_per_1k` | float64 |  | 0.0 | 0 → 36.19 (median 0) | Supply saturation: supermarket outlets per 1,000 residents |
| `school_count_jc` | int64 |  | 0.0 | 0 → 1 (median 0) | school count jc (see layer docs) |
| `school_count_mixed` | int64 |  | 0.0 | 0 → 0 (median 0) | school count mixed (see layer docs) |
| `school_count_premium` | int64 |  | 0.0 | 0 → 3 (median 0) | school count premium (see layer docs) |
| `school_count_primary` | int64 |  | 0.0 | 0 → 4 (median 0) | school count primary (see layer docs) |
| `school_count_secondary` | int64 |  | 0.0 | 0 → 3 (median 0) | school count secondary (see layer docs) |
| `school_count_total` | int64 |  | 0.0 | 0 → 6 (median 0) | school count total (see layer docs) |
| `sig_beacon` | int64 |  | 0.0 | 0 → 65 (median 0) | Road-network metric: sig beacon |
| `sig_bicycle` | int64 |  | 0.0 | 0 → 4 (median 0) | Road-network metric: sig bicycle |
| `sig_filter_arrow` | int64 |  | 0.0 | 0 → 47 (median 0) | Road-network metric: sig filter arrow |
| `sig_ground` | int64 |  | 0.0 | 0 → 133 (median 0) | Road-network metric: sig ground |
| `sig_overhead` | int64 |  | 0.0 | 0 → 34 (median 0) | Road-network metric: sig overhead |
| `sig_pedestrian` | int64 |  | 0.0 | 0 → 122 (median 0) | Road-network metric: sig pedestrian |
| `sig_rag` | int64 |  | 0.0 | 0 → 35 (median 0) | Road-network metric: sig rag |
| `sig_total` | int64 |  | 0.0 | 0 → 365 (median 0) | Road-network metric: sig total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |
| `silver_zone_count` | int64 |  | 0.0 | 0 → 7 (median 0) | silver zone count (see layer docs) |
| `speed_band_avg` | float64 |  | 0.0 | 0 → 6.7 (median 1.77) | speed band avg (see layer docs) |
| `speed_band_count` | int64 |  | 0.0 | 0 → 330 (median 12) | speed band count (see layer docs) |
| `syn_density_x_amenities` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: density x amenities (cross-feature product) |
| `syn_far_x_transit` | float64 |  | 0.0 | 0 → 0 (median 0) | Synergy interaction term: far x transit (cross-feature product) |
| `syn_office_x_transit` | float64 |  | 0.0 | 0 → 0.988 (median 0) | Synergy interaction term: office x transit (cross-feature product) |
| `syn_pop_x_transit` | float64 |  | 0.0 | 0 → 0.959 (median 0) | Synergy interaction term: pop x transit (cross-feature product) |
| `syn_pop_x_walk` | float64 |  | 0.0 | 0 → 0.866 (median 0) | Synergy interaction term: pop x walk (cross-feature product) |
| `syn_premium_school_x_4r` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: premium school x 4r (cross-feature product) |
| `syn_residential_x_school` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: residential x school (cross-feature product) |
| `syn_retail_x_anchors` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: retail x anchors (cross-feature product) |
| `time_to_cbd_min` | float64 | min | 63.6 | 6.577 → 66.29 (median 39.45) | Door-to-door transit travel time to CBD (Raffles Place) (mobility-v2 reach model) |
| `time_to_cgh_min` | float64 | min | 63.6 | 4.786 → 97.79 (median 59.77) | Door-to-door transit travel time to CGH (mobility-v2 reach model) |
| `time_to_changi_business_min` | float64 | min | 63.6 | 4.786 → 97.79 (median 59.77) | Door-to-door transit travel time to Changi Business Park (mobility-v2 reach model) |
| `time_to_jurong_east_min` | float64 | min | 63.6 | 5.44 → 78.54 (median 39.52) | Door-to-door transit travel time to Jurong East (mobility-v2 reach model) |
| `time_to_kkh_min` | float64 | min | 63.6 | 4.123 → 71.79 (median 36.99) | Door-to-door transit travel time to KKH (mobility-v2 reach model) |
| `time_to_ntu_min` | float64 | min | 63.6 | 5.464 → 88.54 (median 50.65) | Door-to-door transit travel time to NTU (mobility-v2 reach model) |
| `time_to_nus_min` | float64 | min | 63.6 | 7.21 → 77.54 (median 41.53) | Door-to-door transit travel time to NUS (mobility-v2 reach model) |
| `time_to_one_north_min` | float64 | min | 63.6 | 5.178 → 75.04 (median 39.15) | Door-to-door transit travel time to one-north (mobility-v2 reach model) |
| `time_to_orchard_min` | float64 | min | 63.6 | 5.996 → 75.29 (median 38.45) | Door-to-door transit travel time to Orchard (mobility-v2 reach model) |
| `time_to_sgh_min` | float64 | min | 63.6 | 6.197 → 61.29 (median 38.49) | Door-to-door transit travel time to SGH (mobility-v2 reach model) |
| `time_to_tampines_hub_min` | float64 | min | 63.6 | 4.588 → 96.29 (median 56.85) | Door-to-door transit travel time to Tampines Hub (mobility-v2 reach model) |
| `time_to_ttsh_min` | float64 | min | 63.6 | 2.449 → 75.79 (median 40.17) | Door-to-door transit travel time to TTSH (mobility-v2 reach model) |
| `tourist_attraction_count` | int64 |  | 0.0 | 0 → 16 (median 0) | tourist attraction count (see layer docs) |
| `transit_mode_count` | int64 | count | 0.0 | 0 → 3 (median 0) | Distinct transit modes serving hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 4.345e-08 → 0.9879 (median 0.3623) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `vibrancy_index` | float64 | 0-1 | 0.0 | 0 → 0.988 (median 0.134) | Composite: places + magnets + reviews + transit + night lights |
| `vis_corner_premium` | float64 | count | 0.0 | 0 → 323 (median 0) | Signalized crossings × main-road presence |
| `vis_dist_exit_origin_m` | float64 | m | 0.0 | 9.6 → 1.404e+04 (median 2062) | Activity origin → nearest exit distance |
| `vis_exit_footfall` | float64 | taps/day | 0.0 | 0 → 4.085e+04 (median 0) | Weekday taps at nearest MRT/LRT exit ≤400 m, split per exit from per-station PV. Few-exit busy stations beat 13-exit Orchard |
| `vis_exit_station` | object | string | 86.9 | 138 unique · `KRANJI MRT STATION` | Name of that nearest station |
| `vis_main_road_m` | float64 | m | 0.0 | 0 → 8095 (median 0) | LTA speed-band cat A/B segment length in hex |
| `vis_traffic_pass_proxy` | float64 | index | 0.0 | 0 → 839.5 (median 0) | Σ road-category weights over speed-band segments — drive-past exposure |
| `vulnerability_penalty` | float64 | points | 0.0 | 0 → 0 (median 0) | Adequacy penalty from vulnerability double-threshold |
| `vulnerability_share` | float64 | ratio | 0.0 | 0 → 0.55 (median 0) | Vulnerable-population share (adequacy v3 multiplier input) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 1.148e+04 (median 29) | Place count within 400m walk |
| `walk_bus_score` | float64 |  | 0.0 | 0 → 0.987 (median 0.494) | Walk-access score to nearest bus (distance-decayed) |
| `walk_clinic_score` | float64 |  | 0.0 | 0 → 0.996 (median 0.101) | Walk-access score to nearest clinic (distance-decayed) |
| `walk_convenience_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest convenience (distance-decayed) |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 2499 (median 1) | Food places within 400m walk |
| `walk_food_score` | float64 |  | 0.0 | 0 → 0.995 (median 0.382) | Walk-access score to nearest food (distance-decayed) |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 630 (median 0) | Hawkers within 400m walk |
| `walk_hawker_score` | float64 |  | 0.0 | 0 → 0.995 (median 0.073) | Walk-access score to nearest hawker (distance-decayed) |
| `walk_mrt_score` | float64 |  | 0.0 | 0 → 1 (median 0.016) | Walk-access score to nearest mrt (distance-decayed) |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 30 (median 0) | Parks within 400m walk |
| `walk_park_score` | float64 |  | 0.0 | 0 → 1 (median 0.075) | Walk-access score to nearest park (distance-decayed) |
| `walk_school_score` | float64 |  | 0.0 | 0 → 0.995 (median 0.217) | Walk-access score to nearest school (distance-decayed) |
| `walk_score_avg` | float64 | 0-1 | 0.0 | 0 → 0.848 (median 0.226) | Mean of the 9 amenity walk-access scores |
| `walk_supermarket_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.117) | Walk-access score to nearest supermarket (distance-decayed) |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9217 (median 0.1915) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `walking_dependent_count` | float64 | persons | 0.0 | 0 → 1.245e+04 (median 0) | Walking-dependent residents (no car/PT-captive) |
| `wc_built_share` | float64 |  | 0.0 | 0 → 0.964 (median 0.25) | ESA WorldCover land-cover share: built share |
| `wc_dominant_class` | int64 |  | 0.0 | 10 → 95 (median 50) | ESA WorldCover land-cover share: dominant class |
| `wc_grass_share` | float64 |  | 0.0 | 0 → 0.73 (median 0.034) | ESA WorldCover land-cover share: grass share |
| `wc_other_share` | float64 |  | 0.0 | 0 → 0.747 (median 0.008) | ESA WorldCover land-cover share: other share |
| `wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.188) | ESA WorldCover land-cover share: tree share |
| `wc_water_share` | float64 |  | 0.0 | 0 → 1 (median 0.058) | ESA WorldCover land-cover share: water share |
| `wet_market_count` | float64 | count | 0.0 | 0 → 5 (median 0) | NEA market & food centres flagged as wet markets (63 of 129) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 9.262e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |
| `zone_type` | object | category | 0.0 | 11 unique · `unknown` | URA zone type of the hex (PA→SZ→hex8 propagated) |
| `zone_type_broad` | object | category | 0.0 | 7 unique · `unknown` | Broad zone class (residential/industrial/airport/nature/islands/future) — the NA-masking rule |

## `hex/hex8_buildings_clean.parquet`

_19 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `best_max_floors` | float64 | floors | 52.3 | 1 → 70 (median 25) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 191 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1968 (median 136) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 2670 (median 184.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 4.288e+05 (median 4.936e+04) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.5818 (median 0.067) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 165 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 45 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1084 (median 0) | Residential buildings |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 3.686 (median 0.2114) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 2.716e+06 (median 1.558e+05) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 76.0 | 8.062 → 63.75 (median 45.48) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 147 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.319e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 76.0 | 12 → 50 (median 40) | Max HDB floor count |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 979 (median 0) | Number of buildings with floors ≥ 10 |

## `hex/hex8_built_environment_features.parquet`

_40 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 13.05 (median 1) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 191 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1968 (median 136) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 2670 (median 184.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 4.288e+05 (median 4.936e+04) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.5818 (median 0.067) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 165 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 45 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1084 (median 0) | Residential buildings |
| `dominant_use` | object | categorical | 0.0 | 11 unique · `transport` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 3.686 (median 0.2114) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 2.716e+06 (median 1.558e+05) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 63.75 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 147 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.319e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.5231 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4369 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.729 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0 → 1.726 (median 0.449) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3256 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2079 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0354) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 2096 (median 30) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9368 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 8.596e+05 (median 8.331e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0957) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9207 (median 0.0005) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 1) | Max GPR within hex |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 979 (median 0) | Number of buildings with floors ≥ 10 |

## `hex/hex8_colo_fit.parquet`

_12 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `colo_fit_beauty_personal` | float64 | log-lift | 0.0 | -0.4176 → 0.5449 (median 0.2206) | Co-location mix-match for beauty_personal: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_cafe_coffee` | float64 | log-lift | 0.0 | -0.3487 → 0.1852 (median 0.0906) | Co-location mix-match for cafe_coffee: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_convenience` | float64 | log-lift | 0.0 | -0.5409 → 0.2072 (median 0) | Co-location mix-match for convenience: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_education` | float64 | log-lift | 0.0 | -0.5588 → 0.225 (median 0) | Co-location mix-match for education: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fast_food` | float64 | log-lift | 0.0 | -0.7358 → 0.2334 (median 0) | Co-location mix-match for fast_food: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fitness_recreation` | float64 | log-lift | 0.0 | -0.5761 → 0.1972 (median 0) | Co-location mix-match for fitness_recreation: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_hawker` | float64 | log-lift | 0.0 | -0.5998 → 0.2785 (median 0) | Co-location mix-match for hawker: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_health_medical` | float64 | log-lift | 0.0 | -0.5084 → 0.2515 (median 0.1073) | Co-location mix-match for health_medical: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_restaurant` | float64 | log-lift | 0.0 | -0.1131 → 0.5658 (median 0.2243) | Co-location mix-match for restaurant: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_shopping_retail` | float64 | log-lift | 0.0 | 0 → 0.416 (median 0.1618) | Co-location mix-match for shopping_retail: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_supermarket` | float64 | log-lift | 0.0 | -0.364 → 0.1704 (median 0) | Co-location mix-match for supermarket: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |

## `hex/hex8_context_pack.parquet`

_17 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bto_pipeline_est` | float64 | units | 0.0 | 0 → 3431 (median 0) | Town under-construction units allocated within town by FAR headroom share — MODELED estate-growth estimate |
| `bto_uc_units_town` | float64 | units | 0.0 | 0 → 1.148e+04 (median 0) | FY2024 HDB units under construction in the hex's town (town-broadcast; Kallang/Whampoa 11.5K, Tengah 11.1K top) |
| `carpark_capacity_lots` | float64 | lots | 0.0 | 0 → 1.367e+04 (median 0) | Summed car-lot CAPACITY (live availability total_lots, lot type C; 696K national) |
| `carpark_count_hdb` | float64 | count | 0.0 | 0 → 26 (median 0) | HDB carparks in hex (HDB Carpark Information) |
| `condo_project_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Private strata projects with transactions in hex (URA, 2,384) |
| `condo_txn_units` | float64 | units | 0.0 | 0 → 1624 (median 0) | Units TRANSACTED across those projects — private-housing density weight, NOT stock |
| `cons_bldg_count` | float64 | count | 0.0 | 0 → 1351 (median 0) | URA conserved buildings in hex (MP2019 SDCP layer, 7,235 islandwide) — shophouse/heritage density |
| `cons_cluster_flag` | bool | bool | 0.0 | 0 → 1 (median 0) | >=20 conserved buildings — heritage shophouse cluster (Chinatown, Little India, Jalan Besar belt) |
| `coworking_count` | float64 | count | 0.0 | 0 → 20 (median 0) | Coworking venues (places name-match, 171 islandwide; 40% CBD-core) |
| `dist_petrol_m` | float64 | m | 0.0 | 2.5 → 1.407e+04 (median 2030) | Distance to nearest petrol station |
| `dist_polyclinic_m` | float64 | m | 0.0 | 103.9 → 1.668e+04 (median 3757) | Centroid distance to nearest polyclinic — public primary-care competition signal |
| `dist_wet_market_m` | float64 | m | 0.0 | 37.6 → 1.794e+04 (median 4601) | Distance to nearest wet market — morning-circuit / grocery-substitution signal |
| `female_pop_share` | float64 | ratio | 57.1 | 0.2381 → 0.6471 (median 0.5182) | Female share of resident pop (SingStat 2025, subzone-broadcast). NaN = zero-population subzone; tiny subzones can skew genuinely |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `petrol_station_count` | float64 | count | 0.0 | 0 → 4 (median 0) | Fuel stations in hex (OSM, 201 islandwide) |
| `polyclinic_count` | float64 | count | 0.0 | 0 → 1 (median 0) | Public polyclinics in hex (27 islandwide) |
| `wet_market_count` | float64 | count | 0.0 | 0 → 5 (median 0) | NEA market & food centres flagged as wet markets (63 of 129) |

## `hex/hex8_daytime_pop.parquet`

_9 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `dt_class` | object | category | 0.0 | 4 unique · `no_data` | job_center (>1.5) / balanced / bedroom (<0.67) / no_data |
| `dt_clipped` | bool | bool | 0.0 | 0 → 1 (median 0) | True if pop+net was clipped at 0 (12 hexes) |
| `dt_inflow_am_persons` | float64 | persons/day | 0.0 | 0 → 9.1e+04 (median 0) | AM-window inbound persons (mode-share adjusted) |
| `dt_net_am_persons` | float64 | persons/day | 0.0 | -1.887e+04 → 8.724e+04 (median 0) | AM net inflow (in − out). THE directional day-night signal; basis of redefined breathing_idx |
| `dt_outflow_am_persons` | float64 | persons/day | 0.0 | 0 → 4.993e+04 (median 0) | AM-window outbound persons (mode-share adjusted) |
| `dt_pop` | float64 | persons | 0.0 | 0 → 8.788e+04 (median 16.79) | Commuter daytime headcount: pop_resident − AM transit out + AM in (0.62 PT mode share, /22 weekdays). Clipped ≥0. |
| `dt_pop_unadj` | float64 | persons | 0.0 | 0 → 5.473e+04 (median 13.01) | Daytime pop, transit-observed only (no mode-share scale-up) |
| `dt_ratio` | float64 | ratio | 59.1 | 0 → 138.8 (median 0.99) | dt_pop / pop_resident; NaN where pop<50 & no OD (no-data, NOT 0) |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |

## `hex/hex8_huff_capture.parquet`

_14 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `cap_beauty_personal` | float64 | outlet-equivalents | 0.0 | 0 → 3.906 (median 0.3123) | Huff capture for a NEW beauty_personal outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_best_category` | object | category | 0.0 | 11 unique · `cafe_coffee` | Category with the highest capture at this hex |
| `cap_cafe_coffee` | float64 | outlet-equivalents | 0.0 | 0 → 3.905 (median 0.2361) | Huff capture for a NEW cafe_coffee outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_convenience` | float64 | outlet-equivalents | 0.0 | 0 → 2.902 (median 0.1662) | Huff capture for a NEW convenience outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_education` | float64 | outlet-equivalents | 0.0 | 0 → 2.473 (median 0.2423) | Huff capture for a NEW education outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fast_food` | float64 | outlet-equivalents | 0.0 | 0 → 2.063 (median 0.1607) | Huff capture for a NEW fast_food outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fitness_recreation` | float64 | outlet-equivalents | 0.0 | 0 → 3.482 (median 0.2053) | Huff capture for a NEW fitness_recreation outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_hawker` | float64 | outlet-equivalents | 0.0 | 0 → 4.939 (median 0.1847) | Huff capture for a NEW hawker outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_health_medical` | float64 | outlet-equivalents | 0.0 | 0 → 4.321 (median 0.2502) | Huff capture for a NEW health_medical outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_restaurant` | float64 | outlet-equivalents | 0.0 | 0 → 3.857 (median 0.3747) | Huff capture for a NEW restaurant outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_shopping_retail` | float64 | outlet-equivalents | 0.0 | 0 → 4.058 (median 0.4394) | Huff capture for a NEW shopping_retail outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_supermarket` | float64 | outlet-equivalents | 0.0 | 0 → 3.31 (median 0.1391) | Huff capture for a NEW supermarket outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_total` | float64 | outlet-equivalents | 0.0 | 0 → 36.82 (median 2.758) | Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83) |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |

## `hex/hex8_iso_transit.parquet`

_5 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `iso_transit15_hex9_n` | int64 | count | 0.0 | 1 → 111 (median 23) | hex9 cells reached in 15 min |
| `iso_transit15_places` | float64 | count | 0.0 | 0 → 2.192e+04 (median 114) | Places (hex9 pc_total) within the 15-min transit reach |
| `iso_transit15_pop` | float64 | persons | 0.0 | 0 → 3.121e+05 (median 23) | Population reachable door-to-door in 15 min weekday-AM transit (GTFS route-dir-stop graph + walk arms) |
| `iso_transit15_stops_used` | int64 | count | 0.0 | 0 → 272 (median 4) | Transit stops reachable within 15 min (network-access measure) |

## `hex/hex8_iso_walk.parquet`

_17 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `iso_euclid800_pop` | float64 | persons | 0.0 | 0 → 9.396e+04 (median 16.02) | Euclid-800m baseline pop on the same node field |
| `iso_reached_node_n` | float64 | count | 0.0 | 0 → 1018 (median 48) | Walk-graph nodes reached within budget (QA) |
| `iso_severance_ratio` | float64 | ratio | 56.2 | 0 → 0.77 (median 0.219) | network pop / euclid pop. Ideal grid ≈0.55 (detour²); low = barriers. NaN where euclid pop < 200 |
| `iso_snap_dist_m` | float64 | m | 0.0 | 1.634 → 1.019e+04 (median 55.99) | Activity-origin snap distance to walk graph (QA) |
| `iso_walk10_competitors_cafe_coffee` | float64 | count | 0.0 | 0 → 217 (median 0) | Existing cafe_coffee outlets inside the 800 m walk catchment |
| `iso_walk10_competitors_fitness_recreation` | float64 | count | 0.0 | 0 → 95 (median 0) | Existing fitness_recreation outlets inside the 800 m walk catchment |
| `iso_walk10_competitors_restaurant` | float64 | count | 0.0 | 0 → 513 (median 0) | Existing restaurant outlets inside the 800 m walk catchment |
| `iso_walk10_competitors_supermarket` | float64 | count | 0.0 | 0 → 44 (median 0) | Existing supermarket outlets inside the 800 m walk catchment |
| `iso_walk10_magnets` | float64 | count | 0.0 | 0 → 953 (median 0) | Magnet anchors reached within the walk catchment |
| `iso_walk10_places` | float64 | count | 0.0 | 0 → 4508 (median 11) | Exact place points reached within 800 m network walk |
| `iso_walk10_pop` | float64 | persons | 0.0 | 0 → 3.534e+04 (median 2.649) | Population within 800 m NETWORK walk of hex activity centroid (node-field demand, k=4 multi-source Dijkstra) |
| `iso_walk10_spend` | float64 | persons-weighted | 0.0 | 0 → 9745 (median 0.762) | iso pop × PA affluence index — catchment spending proxy |
| `iso_walk10_unserved_pop_cafe_coffee` | float64 | persons | 0.0 | 0 → 817.8 (median 0) | Catchment residents with NO cafe_coffee within 800 m euclid of home — network-precise underserved demand |
| `iso_walk10_unserved_pop_fitness_recreation` | float64 | persons | 0.0 | 0 → 395.6 (median 0) | Catchment residents with NO fitness_recreation within 800 m euclid of home — network-precise underserved demand |
| `iso_walk10_unserved_pop_restaurant` | float64 | persons | 0.0 | 0 → 226.7 (median 0) | Catchment residents with NO restaurant within 800 m euclid of home — network-precise underserved demand |
| `iso_walk10_unserved_pop_supermarket` | float64 | persons | 0.0 | 0 → 2316 (median 0) | Catchment residents with NO supermarket within 800 m euclid of home — network-precise underserved demand |

## `hex/hex8_labor_shed.parquet`

_6 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `jobs_reach_45m` | float64 | jobs | 0.0 | 0 → 1.799e+06 (median 1.122e+05) | Job proxy (office+industrial+services places, scaled 2.4M) within 45 min |
| `labor_accessibility_pct` | float64 | ratio | 0.0 | 0 → 0.749 (median 0.0502) | labor_pool_45m / national working-age pop |
| `labor_jobs_balance_45m` | float64 | ratio | 0.0 | 0 → 8.504e+04 (median 0.951) | jobs_reach / labor_pool — divergence flags job-rich/transit-poor (Jurong Island, Tuas) |
| `labor_pool_30m` | float64 | persons | 0.0 | 0 → 8.228e+05 (median 2.039e+04) | Working-age pop reaching this hex within 30-min weekday-AM transit |
| `labor_pool_45m` | float64 | persons | 0.0 | 0 → 2.116e+06 (median 1.419e+05) | Working-age pop within 45-min transit (CBD 1.68M = 59.6% of workforce; Tuas p0) |

## `hex/hex8_land_use.parquet`

_22 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 11.03 (median 0.5845) | Area-weighted Gross Plot Ratio |
| `dominant_use` | object | categorical | 0.0 | 11 unique · `transport` | Bucket with highest area share |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.523 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4744 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7291 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.09 (median 0.6931) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2884 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3002 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0346) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 2096 (median 30) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9368 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 8.596e+05 (median 8.331e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1035) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9207 (median 0.0005) | Water body share |
| `max_gpr` | float64 | ratio | 45.0 | 1 → 25 (median 2.8) | Max GPR within hex |

## `hex/hex8_mobility_features.parquet`

_50 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 1.07e+04 (median 89.88) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 20.36 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 0) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.187e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.476e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.336e+04 (median 281.7) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.372e+04 (median 1503) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.376e+04 (median 1731) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.373e+04 (median 1655) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.599e+04 (median 915.2) | Walk distance to nearest clinic |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.596e+04 (median 385.1) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.599e+04 (median 1046) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.054e+04 (median 1037) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.581e+04 (median 610.4) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.79e+04 (median 857.1) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 23 (median 0) | Authoritative HDB multi-storey carparks |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 22.81) | Lane-km per km² (lane count × length / area) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 21 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 5 (median 0) | MRT/LRT stations in hex |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `n_children_tr` | int64 | count | 0.0 | 1 → 7 (median 7) | hex9 children with transit data (bookkeeping) |
| `n_children_wk` | int64 | count | 0.0 | 1 → 7 (median 7) | hex9 children with walk data (bookkeeping) |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1692) | Fraction of vehicular length that's one-way |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 28 (median 0) | OSM amenity=parking points |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 74.58 (median 6.807) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 5.482e+04 (median 4281) | Footway + path + cycleway + steps length |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 7810 (median 0) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 112.5 (median 22.68) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 523 (median 73) | Road-network metric: road intersection count total |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 709.6 (median 99.05) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 8.288e+04 (median 1.671e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3055) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 4.345e-08 → 0.9879 (median 0.3623) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 1.148e+04 (median 29) | Place count within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 2499 (median 1) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 630 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 30 (median 0) | Parks within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9217 (median 0.1915) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/hex8_mobility_pack.parquet`

_99 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `access_vuln_penalty` | float64 | points | 41.7 | 0 → 0.25 (median 0) | Access-vulnerability penalty |
| `access_vuln_share` | float64 | ratio | 41.7 | 0 → 1 (median 0.0799) | Access-vulnerable share |
| `adq_availability_v2` | float64 | 0-100 | 41.7 | 0.0606 → 1 (median 0.3862) | Transit availability composite |
| `adq_core` | float64 | 0-100 | 41.7 | 0.1839 → 1 (median 0.5583) | Adequacy core (pre-vulnerability) |
| `adq_core_elderly` | float64 | 0-100 | 41.7 | 0.1634 → 1 (median 0.4936) | Adequacy core, elderly |
| `adq_core_family` | float64 | 0-100 | 41.7 | 0.1967 → 1 (median 0.5692) | Adequacy core, family |
| `adq_core_workers` | float64 | 0-100 | 41.7 | 0.1938 → 1 (median 0.6252) | Adequacy core, workers |
| `adq_default` | float64 | 0-100 | 41.7 | 0.0677 → 1 (median 0.5035) | Transport adequacy v3 (default profile, 0-100) |
| `adq_default_elderly` | float64 | 0-100 | 41.7 | 0.0677 → 1 (median 0.5633) | Adequacy, elderly profile |
| `adq_default_family` | float64 | 0-100 | 41.7 | 0.0606 → 1 (median 0.5571) | Adequacy, family profile |
| `adq_default_workers` | float64 | 0-100 | 41.7 | 0.0606 → 1 (median 0.4479) | Adequacy, workers profile |
| `adq_f_accessibility` | float64 | 0-100 | 41.7 | 0.2829 → 1 (median 0.607) | Adequacy v3 factor score: composite access (mobility-v2 model) |
| `adq_f_children_gap` | float64 | 0-100 | 41.7 | 0 → 0.9322 (median 0.1256) | Adequacy v3 factor score: child-population service gap (mobility-v2 model) |
| `adq_f_connectivity` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.6469) | Adequacy v3 factor score: network connectivity (mobility-v2 model) |
| `adq_f_distance` | float64 | 0-100 | 41.7 | 0.004667 → 1 (median 0.248) | Adequacy v3 factor score: distance to transit (mobility-v2 model) |
| `adq_f_dorm_gap` | float64 | 0-100 | 41.7 | 0 → 1 (median 0) | Adequacy v3 factor score: dorm-worker service gap (mobility-v2 model) |
| `adq_f_elderly_gap` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.0948) | Adequacy v3 factor score: elderly service gap (mobility-v2 model) |
| `adq_f_fdw_gap` | float64 | 0-100 | 41.7 | 0 → 0.7624 (median 0) | Adequacy v3 factor score: FDW service gap (mobility-v2 model) |
| `adq_f_last_mile` | float64 | 0-100 | 41.7 | 0.1719 → 1 (median 0.6926) | Adequacy v3 factor score: last-mile friction (mobility-v2 model) |
| `adq_f_line_pressure` | float64 | 0-100 | 41.7 | 0 → 1 (median 0) | Adequacy v3 factor score: line crowding pressure (mobility-v2 model) |
| `adq_f_low_frequency` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.6627) | Adequacy v3 factor score: service frequency shortfall (mobility-v2 model) |
| `adq_f_low_income_gap` | float64 | 0-100 | 41.7 | 0 → 0.5804 (median 0.2188) | Adequacy v3 factor score: low-income service gap (mobility-v2 model) |
| `adq_f_reach_gap` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.2084) | Adequacy v3 factor score: destination reach shortfall (mobility-v2 model) |
| `adq_gap_core` | float64 | 0-100 | 41.7 | 0.1614 → 0.95 (median 0.5126) | Adequacy gap (core) |
| `adq_gap_default` | float64 | 0-100 | 41.7 | 0.1409 → 0.965 (median 0.4769) | Adequacy gap (default profile) |
| `adq_gap_equity_max` | float64 | 0-100 | 41.7 | 0 → 1 (median 0.3882) | Worst per-profile equity gap |
| `adq_primary_factor` | object | category | 55.7 | 6 unique · `reach` | Primary driving factor (default profile) |
| `adq_primary_gap_reason` | object | category | 0.0 | 11 unique · `walk_unfriendly` | Primary gap explanation tag |
| `adq_v2` | float64 | 0-100 | 41.7 | 0.0677 → 1 (median 0.5387) | Adequacy v2 (availability-floored legacy) |
| `adq_worst_factor` | object | category | 0.0 | 10 unique · `f_accessibility` | Name of the worst adequacy factor |
| `adq_worst_factor_value` | float64 | 0-100 | 41.7 | 0.1084 → 1 (median 0.8477) | Score of the worst adequacy factor |
| `bus_stops_in_400m` | int64 | count | 0.0 | 0 → 18 (median 0) | Bus stops within 400 m of centroid |
| `bus_stops_in_800m` | int64 | count | 0.0 | 0 → 59 (median 2) | Bus stops within 800 m |
| `crowd_equity_penalty` | float64 | points | 41.7 | 0 → 0.2338 (median 0) | Crowding equity penalty |
| `crowd_sensitive_share` | float64 | ratio | 41.7 | 0 → 0.55 (median 0.2681) | Crowding-sensitive share |
| `crowding_load_factor` | float64 | index | 0.0 | 0 → 0.9931 (median 0) | Peak load factor on serving lines |
| `cycling_path_len_m` | float64 | m | 0.0 | 0 → 1.048e+04 (median 0) | Cycling-path length in hex |
| `dist_to_nearest_lrt_m` | float64 | m | 0.0 | 65.08 → 2.421e+04 (median 8450) | Distance to nearest LRT station |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `industrial_adjacency_score` | float64 | index | 0.0 | 0 → 1 (median 0) | Adjacency to industrial estates (guard signal) |
| `last_mile_friction` | float64 | index | 0.0 | 0.1719 → 1 (median 0.8333) | Last-mile friction composite |
| `linkway_len_m` | float64 | m | 0.0 | 0 → 4705 (median 0) | Covered-linkway length in hex (7,012-segment LTA layer) — sheltered-walk density |
| `linkway_per_road_km` | float64 | m/km | 20.2 | 0 → 65.59 (median 0) | Covered-linkway metres per road km — shelter coverage ratio |
| `low_income_share` | float64 | ratio | 65.2 | 0 → 0.2998 (median 0.1687) | Low-income share of residents (level deduped vs pop_hdb; share is the signal) |
| `lrt_stations` | float64 | count | 0.0 | 0 → 3 (median 0) | LRT stations in hex |
| `lrt_stations_in_500m` | int64 | count | 0.0 | 0 → 3 (median 0) | LRT stations within 500 m |
| `min15_count_essentials` | int64 | count | 0.0 | 0 → 283 (median 2) | Essential amenities within 15 min |
| `min15_count_health` | int64 | count | 0.0 | 0 → 814 (median 1) | Health amenities within 15 min |
| `min15_count_retail` | int64 | count | 0.0 | 0 → 6070 (median 24) | Retail within 15 min |
| `min15_count_school` | int64 | count | 0.0 | 0 → 651 (median 1) | Schools within 15 min |
| `min15_essentials` | float64 | 0-100 | 0.0 | 0 → 100 (median 24.7) | 15-min subscore: daily essentials |
| `min15_health` | float64 | 0-100 | 0.0 | 0 → 100 (median 36.9) | 15-min subscore: health |
| `min15_nearest_super_m` | float64 | m | 0.0 | 6 → 1.437e+04 (median 1473) | Nearest supermarket |
| `min15_retail` | float64 | 0-100 | 0.0 | 0 → 100 (median 89.8) | 15-min subscore: retail |
| `min15_school` | float64 | 0-100 | 0.0 | 0 → 100 (median 17.8) | 15-min subscore: schools |
| `min15_score` | float64 | 0-100 | 0.0 | 0 → 100 (median 37.1) | 15-minute-city score (calibrated: Toa Payoh 100 / Lim Chu Kang 13) |
| `mrt_reach_bus_min` | float64 | min | 58.4 | 4.6 → 40.7 (median 11.8) | Feeder-bus leg of MRT reach |
| `mrt_reach_bus_wait_min` | float64 | min | 58.4 | 0.1 → 15 (median 1.1) | Feeder wait of MRT reach |
| `mrt_reach_crowd` | float64 | index | 0.0 | 0 → 0.9931 (median 0.3361) | Crowding multiplier on the reach path |
| `mrt_reach_index` | float64 | 0-1 | 0.0 | 0 → 1 (median 0.3788) | Composite MRT reach quality |
| `mrt_reach_mode` | object | category | 0.0 | 3 unique · `walk` | Reach mode: walk / feeder / poor |
| `mrt_reach_n_feeders` | int64 | count | 0.0 | 0 → 36 (median 0) | Feeder bus services to nearest MRT |
| `mrt_stations_in_1km` | int64 | count | 0.0 | 0 → 12 (median 0) | MRT stations within 1 km |
| `mrt_stations_in_500m` | int64 | count | 0.0 | 0 → 5 (median 0) | MRT stations within 500 m |
| `multimodal_score` | float64 | 0-1 | 0.0 | 0 → 0.7522 (median 0) | Multi-modal option richness |
| `n_dest_reachable` | int64 | count | 0.0 | 0 → 17 (median 0) | Key destinations reachable by transit (mobility-v2) |
| `n_dest_within_45min` | int64 | count | 0.0 | 0 → 17 (median 0) | Key destinations within 45-min transit |
| `n_lines_to_cbd` | int64 | count | 0.0 | 0 → 5 (median 0) | Distinct rail lines connecting toward the CBD |
| `n_stations_walking` | int64 | count | 0.0 | 0 → 9 (median 0) | Stations within walking reach |
| `nearest_mrt_st_peak_taps` | float64 | taps | 0.0 | 0 → 3.862e+05 (median 4.601e+04) | Peak taps at the nearest MRT station |
| `pct_dest_within_45min` | float64 | ratio | 0.0 | 0 → 100 (median 0) | Share of key destinations within 45 min |
| `pct_dest_within_60min` | float64 | ratio | 0.0 | 0 → 100 (median 0) | Share of key destinations within 60 min |
| `peak_wait_bus_only_min` | float64 | min | 58.9 | 1.5 → 30 (median 7) | Peak wait, bus only |
| `peak_wait_min` | float64 | min | 56.1 | 1.275 → 12.5 (median 2.8) | Expected peak-hour wait (best mode) |
| `peak_wait_mrt_only_min` | float64 | min | 73.5 | 2.5 → 5 (median 2.5) | Peak wait, MRT only |
| `ped_greenman_count` | int64 | count | 0.0 | 0 → 12 (median 0) | Green Man+ (extended-time) crossings |
| `pop_nr_ep` | float64 | persons | 0.0 | 0 → 1.749e+04 (median 0) | Employment-pass holders |
| `pop_nr_fdw` | float64 | persons | 0.0 | 0 → 4192 (median 0) | Foreign domestic workers |
| `pop_nr_sp` | float64 | persons | 0.0 | 0 → 7115 (median 0) | S-pass holders |
| `pop_nr_wp_other` | float64 | persons | 0.0 | 0 → 9062 (median 0) | Other work-permit holders (non-dorm) |
| `pr_share` | float64 | ratio | 65.2 | 0.1286 → 0.1286 (median 0.1286) | PR share of resident population (citizen/PR ratio signal; levels deduped away) |
| `time_to_cbd_min` | float64 | min | 63.6 | 6.577 → 66.29 (median 39.45) | Door-to-door transit travel time to CBD (Raffles Place) (mobility-v2 reach model) |
| `time_to_cgh_min` | float64 | min | 63.6 | 4.786 → 97.79 (median 59.77) | Door-to-door transit travel time to CGH (mobility-v2 reach model) |
| `time_to_changi_business_min` | float64 | min | 63.6 | 4.786 → 97.79 (median 59.77) | Door-to-door transit travel time to Changi Business Park (mobility-v2 reach model) |
| `time_to_jurong_east_min` | float64 | min | 63.6 | 5.44 → 78.54 (median 39.52) | Door-to-door transit travel time to Jurong East (mobility-v2 reach model) |
| `time_to_kkh_min` | float64 | min | 63.6 | 4.123 → 71.79 (median 36.99) | Door-to-door transit travel time to KKH (mobility-v2 reach model) |
| `time_to_ntu_min` | float64 | min | 63.6 | 5.464 → 88.54 (median 50.65) | Door-to-door transit travel time to NTU (mobility-v2 reach model) |
| `time_to_nus_min` | float64 | min | 63.6 | 7.21 → 77.54 (median 41.53) | Door-to-door transit travel time to NUS (mobility-v2 reach model) |
| `time_to_one_north_min` | float64 | min | 63.6 | 5.178 → 75.04 (median 39.15) | Door-to-door transit travel time to one-north (mobility-v2 reach model) |
| `time_to_orchard_min` | float64 | min | 63.6 | 5.996 → 75.29 (median 38.45) | Door-to-door transit travel time to Orchard (mobility-v2 reach model) |
| `time_to_sgh_min` | float64 | min | 63.6 | 6.197 → 61.29 (median 38.49) | Door-to-door transit travel time to SGH (mobility-v2 reach model) |
| `time_to_tampines_hub_min` | float64 | min | 63.6 | 4.588 → 96.29 (median 56.85) | Door-to-door transit travel time to Tampines Hub (mobility-v2 reach model) |
| `time_to_ttsh_min` | float64 | min | 63.6 | 2.449 → 75.79 (median 40.17) | Door-to-door transit travel time to TTSH (mobility-v2 reach model) |
| `transit_mode_count` | int64 | count | 0.0 | 0 → 3 (median 0) | Distinct transit modes serving hex |
| `vulnerability_penalty` | float64 | points | 41.7 | 0 → 0 (median 0) | Adequacy penalty from vulnerability double-threshold |
| `vulnerability_share` | float64 | ratio | 41.7 | 0 → 0.55 (median 0.2651) | Vulnerable-population share (adequacy v3 multiplier input) |
| `walking_dependent_count` | float64 | persons | 0.0 | 0 → 1.245e+04 (median 0) | Walking-dependent residents (no car/PT-captive) |
| `zone_type` | object | category | 0.0 | 11 unique · `unknown` | URA zone type of the hex (PA→SZ→hex8 propagated) |
| `zone_type_broad` | object | category | 0.0 | 7 unique · `unknown` | Broad zone class (residential/industrial/airport/nature/islands/future) — the NA-masking rule |

## `hex/hex8_pipeline.parquet`

_6 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `pipe_dev_capacity_com` | float64 | FAR-units | 0.0 | 0 → 1.781 (median 0) | FAR headroom × (commercial + mixed) zoning share |
| `pipe_dev_capacity_res` | float64 | FAR-units | 0.0 | 0 → 1.793 (median 0) | FAR headroom (avg_gpr − est_built_far)⁺ × residential zoning share. Matilda 0.50 / Bidadari 0.34 / built-out Toa Payoh Ctrl 0 |
| `pipe_mrt_dist_m` | float64 | m | 0.0 | 11.4 → 1.535e+04 (median 4403) | Distance to nearest future rail station |
| `pipe_mrt_name` | object | string | 0.0 | 35 unique · `JURONG PIER` | Nearest future station name |
| `pipe_new_mrt_within_800m` | bool | bool | 0.0 | 0 → 1 (median 0) | Future rail station (MP2019 minus existing Mar-2026; 37 stations: full JRL + Keppel CCL6) within 800 m |

## `hex/hex8_population.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.47 (median 1.349) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1825) | Non-resident share of total pop |
| `parent_pa` | object | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | object | string | 0.0 | 270 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | object | string | 0.0 | 270 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 7274 (median 0.1151) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 2.692e+04 (median 1.372) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 7709 (median 0.1071) | Population age 65+ |
| `pop_dorm` | float64 | persons | 0.0 | 0 → 3.095e+04 (median 0) | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 3.484e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 9707 (median 1.609) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 3.339e+04 (median 448.8) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 3.813e+04 (median 2.017) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 4.21e+04 (median 603.1) | Total population (residents + non-residents) |

## `hex/hex8_rent_surface.parquet`

_9 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `rent_resi_n_obs` | int64 | count | 0.0 | 0 → 5 (median 1) | Projects within 2.5 km supporting the estimate |
| `rent_resi_psf_med` | float64 | $psf/month | 47.5 | 2.02 → 8.174 (median 4.412) | URA private-resi median rent (913 projects, last 4 quarters, IDW k=5 ≤2.5 km). COMMERCIAL rent not openly available. NaN = no observation in range |
| `rent_resolution` | object | category | 0.0 | 3 unique · `none` | local (≤800 m) / idw / none |
| `roi_cap_per_rent_cafe_coffee` | float64 | ratio | 47.5 | 0.0019 → 1.126 (median 0.219) | cap_cafe_coffee / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_restaurant` | float64 | ratio | 47.5 | 0.0012 → 1.148 (median 0.2529) | cap_restaurant / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_shopping_retail` | float64 | ratio | 47.5 | 0.0023 → 1.208 (median 0.2573) | cap_shopping_retail / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_supermarket` | float64 | ratio | 47.5 | 0.0005 → 0.9638 (median 0.1866) | cap_supermarket / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |
| `roi_cap_per_rent_total` | float64 | ratio | 47.5 | 0.0302 → 10.96 (median 2.277) | cap_total / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent |

## `hex/hex8_roads_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 1.07e+04 (median 89.88) | Bridge segment length |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 0) | Tarjan bridge endpoints (network cut points) |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.372e+04 (median 1503) | Centroid distance to nearest motorway/trunk segment |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 23 (median 0) | Authoritative HDB multi-storey carparks |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 22.81) | Lane-km per km² (lane count × length / area) |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1692) | Fraction of vehicular length that's one-way |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 28 (median 0) | OSM amenity=parking points |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 112.5 (median 22.68) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 523 (median 73) | Road-network metric: road intersection count total |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 709.6 (median 99.05) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 8.288e+04 (median 1.671e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.3055) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |

## `hex/hex8_satellite.parquet`

_9 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 3.077 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 2.682 → 161.4 (median 49.34) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 107.9 (median 4.208) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 2.682 → 158.6 (median 29.56) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 0.8876 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 9.262e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex8_transit_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 20.36 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Bus stops in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.187e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.476e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.336e+04 (median 281.7) | Centroid distance to nearest bus stop |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.376e+04 (median 1731) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.373e+04 (median 1655) | Centroid distance to nearest MRT/LRT station |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 21 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 5 (median 0) | MRT/LRT stations in hex |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 7810 (median 0) | Rail line length through hex (above + underground) |
| `transit_score` | float64 | score [0,1] | 0.0 | 4.345e-08 → 0.9879 (median 0.3623) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |

## `hex/hex8_universe.parquet`

_7 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.47 (median 1.349) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `parent_pa` | object | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | object | string | 0.0 | 270 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | object | string | 0.0 | 270 unique · `TUAS VIEW EXTENSION` | URA subzone full name |

## `hex/hex8_visibility.parquet`

_7 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `vis_corner_premium` | float64 | count | 0.0 | 0 → 323 (median 0) | Signalized crossings × main-road presence |
| `vis_dist_exit_origin_m` | float64 | m | 0.0 | 9.6 → 1.404e+04 (median 2062) | Activity origin → nearest exit distance |
| `vis_exit_footfall` | float64 | taps/day | 0.0 | 0 → 4.085e+04 (median 0) | Weekday taps at nearest MRT/LRT exit ≤400 m, split per exit from per-station PV. Few-exit busy stations beat 13-exit Orchard |
| `vis_exit_station` | object | string | 86.9 | 138 unique · `KRANJI MRT STATION` | Name of that nearest station |
| `vis_main_road_m` | float64 | m | 0.0 | 0 → 8095 (median 0) | LTA speed-band cat A/B segment length in hex |
| `vis_traffic_pass_proxy` | float64 | index | 0.0 | 0 → 839.5 (median 0) | Σ road-category weights over speed-band segments — drive-past exposure |

## `hex/hex8_walkability.parquet`

_21 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.599e+04 (median 915.2) | Walk distance to nearest clinic |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.596e+04 (median 385.1) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.599e+04 (median 1046) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.054e+04 (median 1037) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.581e+04 (median 610.4) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.79e+04 (median 857.1) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `hex8_id` | object | string | 0.0 | 1191 unique · `886520c001fffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `n_children` | int64 | persons | 0.0 | 1 → 7 (median 7) | Child count used as dasymetric denominator (bookkeeping) |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 1) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 74.58 (median 6.807) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 5.482e+04 (median 4281) | Footway + path + cycleway + steps length |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 711.6 (median 110.2) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2303) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 365 (median 0) | LTA traffic signals in hex |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 1.148e+04 (median 29) | Place count within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 2499 (median 1) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 630 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 30 (median 0) | Parks within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9217 (median 0.1915) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/hex9_all_features.parquet`

_583 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `accessibility_composite` | float64 | 0-1 | 0.0 | 0 → 0.975 (median 0.1145) | Composite access score across transit + walk + road reach |
| `archetype_dist` | float64 | z | 0.0 | 0.081 → 28.45 (median 1.371) | Distance to archetype centroid (typicality) |
| `archetype_id` | int64 | id | 0.0 | 0 → 7 (median 5) | k-means (K=8) urban archetype cluster id |
| `archetype_label` | object | category | 0.0 | 8 unique · `CBD_office` | Human label of the archetype cluster |
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 21.96 (median 0) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 541 (median 20) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5152 (median 190.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 1.213e+05 (median 6765) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0644) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 71 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 27 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 474 (median 0) | Residential buildings |
| `bridge_length_m` | float64 | m | 0.0 | 0 → 4369 (median 0) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 50 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 13 (median 0) | Bus stops in hex |
| `bus_taps_in_am` | int64 |  | 0.0 | 0 → 1.781e+05 (median 0) | Daily bus tap-ins in the am time window (LTA PV) |
| `bus_taps_in_midday` | int64 |  | 0.0 | 0 → 1.304e+05 (median 0) | Daily bus tap-ins in the midday time window (LTA PV) |
| `bus_taps_in_night` | int64 |  | 0.0 | 0 → 7.445e+04 (median 0) | Daily bus tap-ins in the night time window (LTA PV) |
| `bus_taps_in_offpeak` | int64 |  | 0.0 | 0 → 5.562e+05 (median 0) | Daily bus tap-ins in the offpeak time window (LTA PV) |
| `bus_taps_in_pm` | int64 |  | 0.0 | 0 → 2.24e+05 (median 0) | Daily bus tap-ins in the pm time window (LTA PV) |
| `bus_taps_in_total` | int64 |  | 0.0 | 0 → 1.161e+06 (median 0) | Daily bus tap-ins in the total time window (LTA PV) |
| `bus_taps_out_am` | int64 |  | 0.0 | 0 → 1.851e+05 (median 0) | Daily bus tap-outs in the am time window (LTA PV) |
| `bus_taps_out_midday` | int64 |  | 0.0 | 0 → 1.533e+05 (median 0) | Daily bus tap-outs in the midday time window (LTA PV) |
| `bus_taps_out_night` | int64 |  | 0.0 | 0 → 4.164e+04 (median 0) | Daily bus tap-outs in the night time window (LTA PV) |
| `bus_taps_out_offpeak` | int64 |  | 0.0 | 0 → 4.636e+05 (median 0) | Daily bus tap-outs in the offpeak time window (LTA PV) |
| `bus_taps_out_pm` | int64 |  | 0.0 | 0 → 1.787e+05 (median 0) | Daily bus tap-outs in the pm time window (LTA PV) |
| `bus_taps_out_total` | int64 |  | 0.0 | 0 → 9.825e+05 (median 0) | Daily bus tap-outs in the total time window (LTA PV) |
| `cap_beauty_personal` | float64 | outlet-equivalents | 0.0 | 0 → 3.906 (median 0.3291) | Huff capture for a NEW beauty_personal outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_best_category` | object | category | 0.0 | 11 unique · `cafe_coffee` | Category with the highest capture at this hex |
| `cap_cafe_coffee` | float64 | outlet-equivalents | 0.0 | 0 → 3.905 (median 0.2431) | Huff capture for a NEW cafe_coffee outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_convenience` | float64 | outlet-equivalents | 0.0 | 0 → 2.902 (median 0.1769) | Huff capture for a NEW convenience outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_education` | float64 | outlet-equivalents | 0.0 | 0 → 2.473 (median 0.2614) | Huff capture for a NEW education outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fast_food` | float64 | outlet-equivalents | 0.0 | 0 → 2.063 (median 0.1865) | Huff capture for a NEW fast_food outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fitness_recreation` | float64 | outlet-equivalents | 0.0 | 0 → 3.482 (median 0.2521) | Huff capture for a NEW fitness_recreation outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_hawker` | float64 | outlet-equivalents | 0.0 | 0 → 4.939 (median 0.2019) | Huff capture for a NEW hawker outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_health_medical` | float64 | outlet-equivalents | 0.0 | 0 → 4.321 (median 0.2753) | Huff capture for a NEW health_medical outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_restaurant` | float64 | outlet-equivalents | 0.0 | 0 → 3.857 (median 0.4208) | Huff capture for a NEW restaurant outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_shopping_retail` | float64 | outlet-equivalents | 0.0 | 0 → 4.058 (median 0.4699) | Huff capture for a NEW shopping_retail outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_supermarket` | float64 | outlet-equivalents | 0.0 | 0 → 3.31 (median 0.1648) | Huff capture for a NEW supermarket outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_total` | float64 | outlet-equivalents | 0.0 | 0 → 36.82 (median 3.219) | Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83) |
| `carpark_count_avail` | int64 |  | 0.0 | 0 → 16 (median 0) | carpark count avail (see layer docs) |
| `carpark_lots_avail` | int64 |  | 0.0 | 0 → 3336 (median 0) | carpark lots avail (see layer docs) |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Tarjan bridge endpoints (network cut points) |
| `chas_clinic_count` | int64 |  | 0.0 | 0 → 12 (median 0) | chas clinic count (see layer docs) |
| `chas_clinics_within_500m` | int64 |  | 0.0 | 0 → 22 (median 0) | Count of chas clinics within 500m |
| `colo_fit_beauty_personal` | float64 | log-lift | 0.0 | -0.4176 → 0.5449 (median 0.1032) | Co-location mix-match for beauty_personal: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_cafe_coffee` | float64 | log-lift | 0.0 | -0.3487 → 0.1852 (median 0.0111) | Co-location mix-match for cafe_coffee: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_convenience` | float64 | log-lift | 0.0 | -0.5409 → 0.2072 (median -0.0929) | Co-location mix-match for convenience: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_education` | float64 | log-lift | 0.0 | -0.5588 → 0.225 (median -0.1164) | Co-location mix-match for education: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fast_food` | float64 | log-lift | 0.0 | -0.7358 → 0.2334 (median 0) | Co-location mix-match for fast_food: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fitness_recreation` | float64 | log-lift | 0.0 | -0.5761 → 0.1972 (median -0.0661) | Co-location mix-match for fitness_recreation: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_hawker` | float64 | log-lift | 0.0 | -0.5998 → 0.2785 (median -0.0473) | Co-location mix-match for hawker: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_health_medical` | float64 | log-lift | 0.0 | -0.5084 → 0.2515 (median 0) | Co-location mix-match for health_medical: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_restaurant` | float64 | log-lift | 0.0 | -0.1131 → 0.5658 (median 0.161) | Co-location mix-match for restaurant: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_shopping_retail` | float64 | log-lift | 0.0 | -0.0564 → 0.416 (median 0.1229) | Co-location mix-match for shopping_retail: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_supermarket` | float64 | log-lift | 0.0 | -0.364 → 0.1704 (median -0.0443) | Co-location mix-match for supermarket: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `commercial_intensity` | float64 | 0-1 | 0.0 | 0 → 1 (median 0.046) | Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.042e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.212e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `density_pressure` | float64 | 0-1 | 0.0 | 0 → 0.809 (median 0.02) | Composite: population + buildings + low road space |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.373e+04 (median 463.5) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.409e+04 (median 1463) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.413e+04 (median 1762) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.409e+04 (median 1657) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.639e+04 (median 1102) | Walk distance to nearest clinic |
| `dist_walk_convenience_m` | float64 | m | 0.0 | 3.638 → 1.41e+04 (median 755.2) | Walk distance to nearest convenience store |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.636e+04 (median 645) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.638e+04 (median 1202) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.091e+04 (median 1222) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.625e+04 (median 845.2) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.834e+04 (median 1055) | Walk distance to nearest supermarket |
| `dominant_use` | object | categorical | 0.0 | 14 unique · `transport` | Bucket with highest area share |
| `dyn_avg_speed_kmh` | float64 |  | 0.0 | 0 → 74 (median 0) | dyn avg speed kmh (see layer docs) |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 10.03 (median 0.2165) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.053e+06 (median 2.273e+04) | Sum of footprint × est_floors per building |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `family_index` | float64 | 0-1 | 0.0 | 0 → 0.974 (median 0.127) | Composite: children + schools + preschools + family amenities |
| `gap_bakery` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for bakery: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_beauty_personal` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for beauty personal: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_cafe_coffee` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for cafe coffee: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_fast_food` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for fast food: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_fitness_recreation` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for fitness recreation: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_hawker` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for hawker: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_health_medical` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for health medical: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_restaurant` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for restaurant: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_supermarket` | float64 |  | 0.0 | -1 → 1 (median 1) | Saturation gap for supermarket: actual minus expected per-1k supply (positive = oversupplied) |
| `gtfs_daily_departures` | int64 |  | 0.0 | 0 → 1.067e+04 (median 0) | GTFS-derived transit service metric: daily departures (weekday schedule) |
| `gtfs_dep_am` | int64 |  | 0.0 | 0 → 1229 (median 0) | GTFS-derived transit service metric: dep am (weekday schedule) |
| `gtfs_dep_midday` | int64 |  | 0.0 | 0 → 1739 (median 0) | GTFS-derived transit service metric: dep midday (weekday schedule) |
| `gtfs_dep_night` | int64 |  | 0.0 | 0 → 1383 (median 0) | GTFS-derived transit service metric: dep night (weekday schedule) |
| `gtfs_dep_pm` | int64 |  | 0.0 | 0 → 1173 (median 0) | GTFS-derived transit service metric: dep pm (weekday schedule) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `gtfs_headway_midday_min` | float64 |  | 0.0 | 0.1 → 999 (median 999) | GTFS-derived transit service metric: headway midday min (weekday schedule) |
| `gtfs_headway_night_min` | float64 |  | 0.0 | 0.3 → 999 (median 999) | GTFS-derived transit service metric: headway night min (weekday schedule) |
| `gtfs_headway_pm_min` | float64 |  | 0.0 | 0.1 → 999 (median 999) | GTFS-derived transit service metric: headway pm min (weekday schedule) |
| `gtfs_routes_served` | int64 |  | 0.0 | 0 → 94 (median 0) | GTFS-derived transit service metric: routes served (weekday schedule) |
| `gtfs_stops_with_service` | int64 |  | 0.0 | 0 → 12 (median 0) | GTFS-derived transit service metric: stops with service (weekday schedule) |
| `hawker_centre_count` | int64 |  | 0.0 | 0 → 2 (median 0) | hawker centre count (see layer docs) |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 65 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.055e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 7 (median 0) | Authoritative HDB multi-storey carparks |
| `hdb_resale_12m_median_price` | float64 |  | 0.0 | 0 → 9.8e+05 (median 0) | hdb resale 12m median price (see layer docs) |
| `hdb_resale_4r_median_price` | float64 |  | 0.0 | 0 → 8.35e+05 (median 0) | hdb resale 4r median price (see layer docs) |
| `hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | hdb resale 4r median psm (see layer docs) |
| `hdb_resale_avg_lease_remaining_yrs` | float64 |  | 0.0 | 0 → 89.87 (median 0) | hdb resale avg lease remaining yrs (see layer docs) |
| `hdb_resale_in_town` | int64 |  | 0.0 | 0 → 1 (median 0) | hdb resale in town (see layer docs) |
| `hdb_resale_median_price` | float64 |  | 0.0 | 0 → 7.6e+05 (median 0) | hdb resale median price (see layer docs) |
| `hdb_resale_median_psm` | float64 |  | 0.0 | 0 → 7629 (median 0) | hdb resale median psm (see layer docs) |
| `hdb_resale_txns_12m` | float64 |  | 0.0 | 0 → 1948 (median 0) | hdb resale txns 12m (see layer docs) |
| `hdb_resale_txns_total` | float64 |  | 0.0 | 0 → 1.852e+04 (median 0) | hdb resale txns total (see layer docs) |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `in_primary_school_zone` | int64 | bool | 0.0 | 0 → 1 (median 0) | Cell intersects a primary-school zone |
| `in_silver_zone` | int64 | bool | 0.0 | 0 → 1 (median 0) | Cell intersects an elderly-priority Silver Zone |
| `inbound_influence` | float64 | index | 0.0 | 0 → 1 (median 0.102) | Gravity-decayed influence neighbours exert on the cell (hex9 influence model) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `jam_pct` | float64 |  | 0.0 | 0 → 100 (median 0) | jam pct (see layer docs) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 147.7 (median 17.13) | Lane-km per km² (lane count × length / area) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.472 (median 1.352) | Hex centroid latitude |
| `livability_index` | float64 | 0-1 | 0.0 | 0.027 → 0.977 (median 0.382) | Composite: walkability + green + amenities + transit |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8105 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9317 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.084 (median 0.514) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8857 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8988 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6274 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0026) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 533 (median 5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 1.308e+05 (median 1.191e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Water body share |
| `max1_chas_clinic_count` | float64 |  | 0.0 | 0 → 12 (median 0) | Max over ring-1 neighbours of: chas clinic count (see layer docs) |
| `max1_commercial_intensity` | float64 |  | 0.0 | 0 → 1 (median 0.074) | Max over ring-1 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `max1_density_pressure` | float64 |  | 0.0 | 0 → 0.809 (median 0.092) | Max over ring-1 neighbours of: Composite: population + buildings + low road space |
| `max1_family_index` | float64 |  | 0.0 | 0 → 0.974 (median 0.2555) | Max over ring-1 neighbours of: Composite: children + schools + preschools + family amenities |
| `max1_hawker_centre_count` | float64 |  | 0.0 | 0 → 2 (median 0) | Max over ring-1 neighbours of: hawker centre count (see layer docs) |
| `max1_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | Max over ring-1 neighbours of: hdb resale 4r median psm (see layer docs) |
| `max1_nl_2024` | float64 |  | 0.0 | 0 → 179.5 (median 57.09) | Max over ring-1 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `max1_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 167.3 (median 41.1) | Max over ring-1 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `max1_pc_cat_business_office` | float64 |  | 0.0 | 0 → 368 (median 1) | Max over ring-1 neighbours of: Place count in cell: business office category (24-cat taxonomy) |
| `max1_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 49 (median 0) | Max over ring-1 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `max1_pc_cat_education` | float64 |  | 0.0 | 0 → 75 (median 0) | Max over ring-1 neighbours of: Place count in cell: education category (24-cat taxonomy) |
| `max1_pc_cat_hawker` | float64 |  | 0.0 | 0 → 96 (median 0) | Max over ring-1 neighbours of: Place count in cell: hawker category (24-cat taxonomy) |
| `max1_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 196 (median 0) | Max over ring-1 neighbours of: Place count in cell: health medical category (24-cat taxonomy) |
| `max1_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 142 (median 1) | Max over ring-1 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `max1_pc_cat_residential` | float64 |  | 0.0 | 0 → 30 (median 0) | Max over ring-1 neighbours of: Place count in cell: residential category (24-cat taxonomy) |
| `max1_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 88 (median 0) | Max over ring-1 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) |
| `max1_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 229 (median 0) | Max over ring-1 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `max1_pc_magnets` | float64 |  | 0.0 | 0 → 266 (median 1) | Max over ring-1 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `max1_pc_total` | float64 |  | 0.0 | 0 → 1215 (median 11) | Max over ring-1 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `max1_pc_unique_brands` | float64 |  | 0.0 | 0 → 96 (median 0) | Max over ring-1 neighbours of: Distinct retail/F&B brands present — chain richness |
| `max1_preschools_within_400m` | float64 |  | 0.0 | 0 → 25 (median 0) | Max over ring-1 neighbours of: Count of preschools within 400m |
| `max1_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 9 (median 0) | Max over ring-1 neighbours of: Count of primary schools within 1km |
| `max1_pull_cbd` | float64 |  | 0.0 | 0 → 1 (median 0.079) | Max over ring-1 neighbours of: Gravity pull toward cbd (distance-decayed attraction) |
| `max1_pull_mall` | float64 |  | 0.0 | 0 → 1 (median 0.051) | Max over ring-1 neighbours of: Gravity pull toward mall (distance-decayed attraction) |
| `max1_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 1 (median 0.059) | Max over ring-1 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `max1_tourist_attraction_count` | float64 |  | 0.0 | 0 → 5 (median 0) | Max over ring-1 neighbours of: tourist attraction count (see layer docs) |
| `max1_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.406) | Max over ring-1 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `max1_vibrancy_index` | float64 |  | 0.0 | 0 → 0.99 (median 0.162) | Max over ring-1 neighbours of: Composite: places + magnets + reviews + transit + night lights |
| `max1_walkability_score` | float64 |  | 0.0 | 0 → 0.959 (median 0.485) | Max over ring-1 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `max1_wc_built_share` | float64 |  | 0.0 | 0 → 1 (median 0.696) | Max over ring-1 neighbours of: ESA WorldCover land-cover share: built share |
| `max1_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.497) | Max over ring-1 neighbours of: ESA WorldCover land-cover share: tree share |
| `max2_chas_clinic_count` | float64 |  | 0.0 | 0 → 12 (median 0) | Max over ring-2 neighbours of: chas clinic count (see layer docs) |
| `max2_commercial_intensity` | float64 |  | 0.0 | 0 → 1 (median 0.097) | Max over ring-2 neighbours of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `max2_density_pressure` | float64 |  | 0.0 | 0 → 0.809 (median 0.181) | Max over ring-2 neighbours of: Composite: population + buildings + low road space |
| `max2_family_index` | float64 |  | 0.0 | 0 → 0.974 (median 0.331) | Max over ring-2 neighbours of: Composite: children + schools + preschools + family amenities |
| `max2_hawker_centre_count` | float64 |  | 0.0 | 0 → 2 (median 0) | Max over ring-2 neighbours of: hawker centre count (see layer docs) |
| `max2_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | Max over ring-2 neighbours of: hdb resale 4r median psm (see layer docs) |
| `max2_nl_2024` | float64 |  | 0.0 | 0 → 179.5 (median 61.32) | Max over ring-2 neighbours of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `max2_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 167.3 (median 47.93) | Max over ring-2 neighbours of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `max2_pc_cat_business_office` | float64 |  | 0.0 | 0 → 368 (median 2) | Max over ring-2 neighbours of: Place count in cell: business office category (24-cat taxonomy) |
| `max2_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 49 (median 1) | Max over ring-2 neighbours of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `max2_pc_cat_education` | float64 |  | 0.0 | 0 → 75 (median 1) | Max over ring-2 neighbours of: Place count in cell: education category (24-cat taxonomy) |
| `max2_pc_cat_hawker` | float64 |  | 0.0 | 0 → 96 (median 0) | Max over ring-2 neighbours of: Place count in cell: hawker category (24-cat taxonomy) |
| `max2_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 196 (median 0) | Max over ring-2 neighbours of: Place count in cell: health medical category (24-cat taxonomy) |
| `max2_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 142 (median 2) | Max over ring-2 neighbours of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `max2_pc_cat_residential` | float64 |  | 0.0 | 0 → 30 (median 1) | Max over ring-2 neighbours of: Place count in cell: residential category (24-cat taxonomy) |
| `max2_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 88 (median 1) | Max over ring-2 neighbours of: Place count in cell: restaurant category (24-cat taxonomy) |
| `max2_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 229 (median 1) | Max over ring-2 neighbours of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `max2_pc_magnets` | float64 |  | 0.0 | 0 → 266 (median 2) | Max over ring-2 neighbours of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `max2_pc_total` | float64 |  | 0.0 | 0 → 1215 (median 27) | Max over ring-2 neighbours of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `max2_pc_unique_brands` | float64 |  | 0.0 | 0 → 96 (median 1) | Max over ring-2 neighbours of: Distinct retail/F&B brands present — chain richness |
| `max2_preschools_within_400m` | float64 |  | 0.0 | 0 → 25 (median 0) | Max over ring-2 neighbours of: Count of preschools within 400m |
| `max2_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 9 (median 0) | Max over ring-2 neighbours of: Count of primary schools within 1km |
| `max2_pull_cbd` | float64 |  | 0.0 | 0 → 1 (median 0.085) | Max over ring-2 neighbours of: Gravity pull toward cbd (distance-decayed attraction) |
| `max2_pull_mall` | float64 |  | 0.0 | 0 → 1 (median 0.0555) | Max over ring-2 neighbours of: Gravity pull toward mall (distance-decayed attraction) |
| `max2_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 1 (median 0.067) | Max over ring-2 neighbours of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `max2_tourist_attraction_count` | float64 |  | 0.0 | 0 → 5 (median 0) | Max over ring-2 neighbours of: tourist attraction count (see layer docs) |
| `max2_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.481) | Max over ring-2 neighbours of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `max2_vibrancy_index` | float64 |  | 0.0 | 0 → 0.99 (median 0.201) | Max over ring-2 neighbours of: Composite: places + magnets + reviews + transit + night lights |
| `max2_walkability_score` | float64 |  | 0.0 | 0 → 0.959 (median 0.631) | Max over ring-2 neighbours of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `max2_wc_built_share` | float64 |  | 0.0 | 0 → 1 (median 0.855) | Max over ring-2 neighbours of: ESA WorldCover land-cover share: built share |
| `max2_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.703) | Max over ring-2 neighbours of: ESA WorldCover land-cover share: tree share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 0) | Max GPR within hex |
| `mg_avg_anchor_strength` | float64 |  | 0.0 | 0 → 765.4 (median 0) | Magnet model: strength of the biggest avg anchor place nearby |
| `mg_avg_competitors_400m` | float64 | count | 0.0 | 0 → 181.7 (median 0) | Magnet model: mean same-category competitor count within 400 m across categories |
| `mg_avg_walk_dist_mrt_m` | float64 | m | 0.0 | 0 → 9999 (median 701.1) | Magnet model: mean walk distance to MRT across category micrographs |
| `mg_bakery_anchor_strength` | float64 |  | 0.0 | 0 → 1564 (median 0) | Magnet model: strength of the biggest bakery anchor place nearby |
| `mg_bakery_pressure_400m` | float64 |  | 0.0 | 0 → 50.94 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bakery |
| `mg_bakery_support_400m` | float64 |  | 0.0 | 0 → 241 (median 0) | Magnet model: complementary-category support density within 400 m for bakery (demand context, not supply) |
| `mg_bar_nightlife_anchor_strength` | float64 |  | 0.0 | 0 → 319.2 (median 0) | Magnet model: strength of the biggest bar nightlife anchor place nearby |
| `mg_bar_nightlife_pressure_400m` | float64 |  | 0.0 | 0 → 28.48 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bar nightlife |
| `mg_bar_nightlife_support_400m` | float64 |  | 0.0 | 0 → 144 (median 0) | Magnet model: complementary-category support density within 400 m for bar nightlife (demand context, not supply) |
| `mg_beauty_personal_anchor_strength` | float64 |  | 0.0 | 0 → 1060 (median 0) | Magnet model: strength of the biggest beauty personal anchor place nearby |
| `mg_beauty_personal_pressure_400m` | float64 |  | 0.0 | 0 → 105.9 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for beauty personal |
| `mg_beauty_personal_support_400m` | float64 |  | 0.0 | 0 → 210.9 (median 0) | Magnet model: complementary-category support density within 400 m for beauty personal (demand context, not supply) |
| `mg_business_office_anchor_strength` | float64 |  | 0.0 | 0 → 378.7 (median 0) | Magnet model: strength of the biggest business office anchor place nearby |
| `mg_business_office_pressure_400m` | float64 |  | 0.0 | 0 → 347.5 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for business office |
| `mg_business_office_support_400m` | float64 |  | 0.0 | 0 → 367.9 (median 0) | Magnet model: complementary-category support density within 400 m for business office (demand context, not supply) |
| `mg_cafe_coffee_anchor_strength` | float64 |  | 0.0 | 0 → 1305 (median 0) | Magnet model: strength of the biggest cafe coffee anchor place nearby |
| `mg_cafe_coffee_pressure_400m` | float64 |  | 0.0 | 0 → 56.31 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for cafe coffee |
| `mg_cafe_coffee_support_400m` | float64 |  | 0.0 | 0 → 234.8 (median 0) | Magnet model: complementary-category support density within 400 m for cafe coffee (demand context, not supply) |
| `mg_convenience_anchor_strength` | float64 |  | 0.0 | 0 → 85.8 (median 0) | Magnet model: strength of the biggest convenience anchor place nearby |
| `mg_convenience_pressure_400m` | float64 |  | 0.0 | 0 → 36.35 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for convenience |
| `mg_convenience_support_400m` | float64 |  | 0.0 | 0 → 47.5 (median 0) | Magnet model: complementary-category support density within 400 m for convenience (demand context, not supply) |
| `mg_education_anchor_strength` | float64 |  | 0.0 | 0 → 47.17 (median 0) | Magnet model: strength of the biggest education anchor place nearby |
| `mg_education_pressure_400m` | float64 |  | 0.0 | 0 → 72 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for education |
| `mg_education_support_400m` | float64 |  | 0.0 | 0 → 54.2 (median 0) | Magnet model: complementary-category support density within 400 m for education (demand context, not supply) |
| `mg_entertainment_culture_anchor_strength` | float64 |  | 0.0 | 0 → 1661 (median 0) | Magnet model: strength of the biggest entertainment culture anchor place nearby |
| `mg_entertainment_culture_pressure_400m` | float64 |  | 0.0 | 0 → 20.38 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for entertainment culture |
| `mg_entertainment_culture_support_400m` | float64 |  | 0.0 | 0 → 136.8 (median 0) | Magnet model: complementary-category support density within 400 m for entertainment culture (demand context, not supply) |
| `mg_fast_food_anchor_strength` | float64 |  | 0.0 | 0 → 1197 (median 0) | Magnet model: strength of the biggest fast food anchor place nearby |
| `mg_fast_food_pressure_400m` | float64 |  | 0.0 | 0 → 114.5 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fast food |
| `mg_fast_food_support_400m` | float64 |  | 0.0 | 0 → 188 (median 0) | Magnet model: complementary-category support density within 400 m for fast food (demand context, not supply) |
| `mg_fitness_recreation_anchor_strength` | float64 |  | 0.0 | 0 → 1147 (median 0) | Magnet model: strength of the biggest fitness recreation anchor place nearby |
| `mg_fitness_recreation_pressure_400m` | float64 |  | 0.0 | 0 → 26.62 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fitness recreation |
| `mg_fitness_recreation_support_400m` | float64 |  | 0.0 | 0 → 156 (median 0) | Magnet model: complementary-category support density within 400 m for fitness recreation (demand context, not supply) |
| `mg_government_public_anchor_strength` | float64 |  | 0.0 | 0 → 73.3 (median 0) | Magnet model: strength of the biggest government public anchor place nearby |
| `mg_government_public_pressure_400m` | float64 |  | 0.0 | 0 → 19.83 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for government public |
| `mg_government_public_support_400m` | float64 |  | 0.0 | 0 → 276.2 (median 0) | Magnet model: complementary-category support density within 400 m for government public (demand context, not supply) |
| `mg_hawker_anchor_strength` | float64 |  | 0.0 | 0 → 88.85 (median 0) | Magnet model: strength of the biggest hawker anchor place nearby |
| `mg_hawker_pressure_400m` | float64 |  | 0.0 | 0 → 122.9 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hawker |
| `mg_hawker_support_400m` | float64 |  | 0.0 | 0 → 59.17 (median 0) | Magnet model: complementary-category support density within 400 m for hawker (demand context, not supply) |
| `mg_health_medical_anchor_strength` | float64 |  | 0.0 | 0 → 92.73 (median 0) | Magnet model: strength of the biggest health medical anchor place nearby |
| `mg_health_medical_pressure_400m` | float64 |  | 0.0 | 0 → 198.3 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for health medical |
| `mg_health_medical_support_400m` | float64 |  | 0.0 | 0 → 224 (median 0) | Magnet model: complementary-category support density within 400 m for health medical (demand context, not supply) |
| `mg_hotel_hospitality_anchor_strength` | float64 |  | 0.0 | 0 → 2007 (median 0) | Magnet model: strength of the biggest hotel hospitality anchor place nearby |
| `mg_hotel_hospitality_pressure_400m` | float64 |  | 0.0 | 0 → 56.39 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hotel hospitality |
| `mg_hotel_hospitality_support_400m` | float64 |  | 0.0 | 0 → 133.8 (median 0) | Magnet model: complementary-category support density within 400 m for hotel hospitality (demand context, not supply) |
| `mg_industrial_mfg_anchor_strength` | float64 |  | 0.0 | 0 → 321.7 (median 0) | Magnet model: strength of the biggest industrial mfg anchor place nearby |
| `mg_industrial_mfg_pressure_400m` | float64 |  | 0.0 | 0 → 137.2 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for industrial mfg |
| `mg_industrial_mfg_support_400m` | float64 |  | 0.0 | 0 → 616.6 (median 0) | Magnet model: complementary-category support density within 400 m for industrial mfg (demand context, not supply) |
| `mg_other_uncategorized_anchor_strength` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: strength of the biggest other uncategorized anchor place nearby |
| `mg_other_uncategorized_pressure_400m` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for other uncategorized |
| `mg_other_uncategorized_support_400m` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: complementary-category support density within 400 m for other uncategorized (demand context, not supply) |
| `mg_park_open_anchor_strength` | float64 |  | 0.0 | 0 → 28.69 (median 0) | Magnet model: strength of the biggest park open anchor place nearby |
| `mg_park_open_pressure_400m` | float64 |  | 0.0 | 0 → 11.18 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for park open |
| `mg_park_open_support_400m` | float64 |  | 0.0 | 0 → 109 (median 0) | Magnet model: complementary-category support density within 400 m for park open (demand context, not supply) |
| `mg_religious_worship_anchor_strength` | float64 |  | 0.0 | 0 → 27.93 (median 0) | Magnet model: strength of the biggest religious worship anchor place nearby |
| `mg_religious_worship_pressure_400m` | float64 |  | 0.0 | 0 → 24.54 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for religious worship |
| `mg_religious_worship_support_400m` | float64 |  | 0.0 | 0 → 34 (median 0) | Magnet model: complementary-category support density within 400 m for religious worship (demand context, not supply) |
| `mg_residential_anchor_strength` | float64 |  | 0.0 | 0 → 1145 (median 0) | Magnet model: strength of the biggest residential anchor place nearby |
| `mg_residential_pressure_400m` | float64 |  | 0.0 | 0 → 28 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for residential |
| `mg_residential_support_400m` | float64 |  | 0.0 | 0 → 60 (median 0) | Magnet model: complementary-category support density within 400 m for residential (demand context, not supply) |
| `mg_restaurant_anchor_strength` | float64 |  | 0.0 | 0 → 1238 (median 0) | Magnet model: strength of the biggest restaurant anchor place nearby |
| `mg_restaurant_pressure_400m` | float64 |  | 0.0 | 0 → 161 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for restaurant |
| `mg_restaurant_support_400m` | float64 |  | 0.0 | 0 → 132.6 (median 0) | Magnet model: complementary-category support density within 400 m for restaurant (demand context, not supply) |
| `mg_services_anchor_strength` | float64 |  | 0.0 | 0 → 1294 (median 0) | Magnet model: strength of the biggest services anchor place nearby |
| `mg_services_pressure_400m` | float64 |  | 0.0 | 0 → 241.9 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for services |
| `mg_services_support_400m` | float64 |  | 0.0 | 0 → 347.1 (median 0) | Magnet model: complementary-category support density within 400 m for services (demand context, not supply) |
| `mg_shopping_retail_anchor_strength` | float64 |  | 0.0 | 0 → 1292 (median 0) | Magnet model: strength of the biggest shopping retail anchor place nearby |
| `mg_shopping_retail_pressure_400m` | float64 |  | 0.0 | 0 → 143.3 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for shopping retail |
| `mg_shopping_retail_support_400m` | float64 |  | 0.0 | 0 → 200.7 (median 0) | Magnet model: complementary-category support density within 400 m for shopping retail (demand context, not supply) |
| `mg_supermarket_anchor_strength` | float64 |  | 0.0 | 0 → 42.41 (median 0) | Magnet model: strength of the biggest supermarket anchor place nearby |
| `mg_supermarket_pressure_400m` | float64 |  | 0.0 | 0 → 46.5 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for supermarket |
| `mg_supermarket_support_400m` | float64 |  | 0.0 | 0 → 186 (median 0) | Magnet model: complementary-category support density within 400 m for supermarket (demand context, not supply) |
| `mg_transportation_anchor_strength` | float64 |  | 0.0 | 0 → 1239 (median 0) | Magnet model: strength of the biggest transportation anchor place nearby |
| `mg_transportation_pressure_400m` | float64 |  | 0.0 | 0 → 25.89 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for transportation |
| `mg_transportation_support_400m` | float64 |  | 0.0 | 0 → 297.6 (median 0) | Magnet model: complementary-category support density within 400 m for transportation (demand context, not supply) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 10 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 3 (median 0) | MRT/LRT stations in hex |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 474 (median 0) | Number of buildings with floors ≥ 10 |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `nearest_chas_clinic_dist_m` | float64 |  | 0.0 | 1.4 → 1.413e+04 (median 1336) | Distance to nearest chas clinic |
| `nearest_hawker_centre_dist_m` | float64 |  | 0.0 | 17.8 → 1.675e+04 (median 2288) | Distance to nearest hawker centre |
| `nearest_preschool_dist_m` | float64 |  | 0.0 | 1.3 → 1.6e+04 (median 1303) | Distance to nearest preschool |
| `nearest_primary_school_dist_m` | float64 |  | 0.0 | 9.5 → 1.629e+04 (median 2064) | Distance to nearest primary school |
| `nearest_school_dist_m` | float64 |  | 0.0 | 4.5 → 1.59e+04 (median 1905) | Distance to nearest school |
| `nearest_tourist_dist_m` | float64 |  | 0.0 | 12.7 → 1.55e+04 (median 3315) | Distance to nearest tourist |
| `net_influence` | float64 | index | 0.0 | 0 → 1 (median 0.567) | Outbound minus inbound influence (hex9 influence model) |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 48.49) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 4.41) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 167.3 (median 28.12) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 2.997 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1602) | Non-resident share of total pop |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0407) | Fraction of vehicular length that's one-way |
| `osm_amenities_count` | int64 | count | 0.0 | 0 → 229 (median 0) | OSM amenity-tagged POIs in cell (independent ground truth) |
| `osm_leisure_count` | int64 | count | 0.0 | 0 → 68 (median 0) | OSM leisure-tagged POIs in cell |
| `osm_shops_count` | int64 | count | 0.0 | 0 → 161 (median 0) | OSM shop-tagged POIs in cell — independent retail frontage |
| `osm_tourism_count` | int64 | count | 0.0 | 0 → 73 (median 0) | OSM tourism-tagged POIs in cell |
| `outbound_influence` | float64 | index | 0.0 | 0 → 1 (median 0.4335) | Gravity-decayed influence the cell exerts on neighbours (hex9 influence model) |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_pa` | object | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | object | string | 0.0 | 326 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 15 (median 0) | OSM amenity=parking points |
| `pc2_branded_count` | int64 |  | 0.0 | 0 → 123 (median 0) | Fine-taxonomy place metric: branded count |
| `pc2_cat_biz_office_count` | int64 |  | 0.0 | 0 → 109 (median 0) | Place count in cell: biz office (55-cat fine taxonomy) |
| `pc2_cat_civic_community_count` | int64 |  | 0.0 | 0 → 7 (median 0) | Place count in cell: civic community (55-cat fine taxonomy) |
| `pc2_cat_civic_government_count` | int64 |  | 0.0 | 0 → 23 (median 0) | Place count in cell: civic government (55-cat fine taxonomy) |
| `pc2_cat_civic_nonprofit_count` | int64 |  | 0.0 | 0 → 20 (median 0) | Place count in cell: civic nonprofit (55-cat fine taxonomy) |
| `pc2_cat_civic_religious_count` | int64 |  | 0.0 | 0 → 18 (median 0) | Place count in cell: civic religious (55-cat fine taxonomy) |
| `pc2_cat_edu_preschool_count` | int64 |  | 0.0 | 0 → 14 (median 0) | Place count in cell: edu preschool (55-cat fine taxonomy) |
| `pc2_cat_edu_primary_secondary_count` | int64 |  | 0.0 | 0 → 23 (median 0) | Place count in cell: edu primary secondary (55-cat fine taxonomy) |
| `pc2_cat_edu_specialty_count` | int64 |  | 0.0 | 0 → 5 (median 0) | Place count in cell: edu specialty (55-cat fine taxonomy) |
| `pc2_cat_edu_tertiary_count` | int64 |  | 0.0 | 0 → 15 (median 0) | Place count in cell: edu tertiary (55-cat fine taxonomy) |
| `pc2_cat_edu_tuition_count` | int64 |  | 0.0 | 0 → 59 (median 0) | Place count in cell: edu tuition (55-cat fine taxonomy) |
| `pc2_cat_food_bakery_count` | int64 |  | 0.0 | 0 → 20 (median 0) | Place count in cell: food bakery (55-cat fine taxonomy) |
| `pc2_cat_food_bar_count` | int64 |  | 0.0 | 0 → 20 (median 0) | Place count in cell: food bar (55-cat fine taxonomy) |
| `pc2_cat_food_cafe_count` | int64 |  | 0.0 | 0 → 39 (median 0) | Place count in cell: food cafe (55-cat fine taxonomy) |
| `pc2_cat_food_caterer_count` | int64 |  | 0.0 | 0 → 14 (median 0) | Place count in cell: food caterer (55-cat fine taxonomy) |
| `pc2_cat_food_dessert_count` | int64 |  | 0.0 | 0 → 26 (median 0) | Place count in cell: food dessert (55-cat fine taxonomy) |
| `pc2_cat_food_fast_food_count` | int64 |  | 0.0 | 0 → 12 (median 0) | Place count in cell: food fast food (55-cat fine taxonomy) |
| `pc2_cat_food_hawker_count` | int64 |  | 0.0 | 0 → 95 (median 0) | Place count in cell: food hawker (55-cat fine taxonomy) |
| `pc2_cat_food_restaurant_count` | int64 |  | 0.0 | 0 → 84 (median 0) | Place count in cell: food restaurant (55-cat fine taxonomy) |
| `pc2_cat_health_clinic_count` | int64 |  | 0.0 | 0 → 61 (median 0) | Place count in cell: health clinic (55-cat fine taxonomy) |
| `pc2_cat_health_hospital_count` | int64 |  | 0.0 | 0 → 25 (median 0) | Place count in cell: health hospital (55-cat fine taxonomy) |
| `pc2_cat_health_pharmacy_count` | int64 |  | 0.0 | 0 → 11 (median 0) | Place count in cell: health pharmacy (55-cat fine taxonomy) |
| `pc2_cat_health_specialist_count` | int64 |  | 0.0 | 0 → 81 (median 0) | Place count in cell: health specialist (55-cat fine taxonomy) |
| `pc2_cat_health_tcm_count` | int64 |  | 0.0 | 0 → 8 (median 0) | Place count in cell: health tcm (55-cat fine taxonomy) |
| `pc2_cat_leisure_entertainment_count` | int64 |  | 0.0 | 0 → 13 (median 0) | Place count in cell: leisure entertainment (55-cat fine taxonomy) |
| `pc2_cat_leisure_park_count` | int64 |  | 0.0 | 0 → 17 (median 0) | Place count in cell: leisure park (55-cat fine taxonomy) |
| `pc2_cat_leisure_tourist_count` | int64 |  | 0.0 | 0 → 17 (median 0) | Place count in cell: leisure tourist (55-cat fine taxonomy) |
| `pc2_cat_other_count` | int64 |  | 0.0 | 0 → 241 (median 0) | Place count in cell: other (55-cat fine taxonomy) |
| `pc2_cat_res_aged_care_count` | int64 |  | 0.0 | 0 → 4 (median 0) | Place count in cell: res aged care (55-cat fine taxonomy) |
| `pc2_cat_res_hdb_count` | int64 |  | 0.0 | 0 → 26 (median 0) | Place count in cell: res hdb (55-cat fine taxonomy) |
| `pc2_cat_res_private_count` | int64 |  | 0.0 | 0 → 25 (median 0) | Place count in cell: res private (55-cat fine taxonomy) |
| `pc2_cat_retail_apparel_count` | int64 |  | 0.0 | 0 → 75 (median 0) | Place count in cell: retail apparel (55-cat fine taxonomy) |
| `pc2_cat_retail_convenience_count` | int64 |  | 0.0 | 0 → 29 (median 0) | Place count in cell: retail convenience (55-cat fine taxonomy) |
| `pc2_cat_retail_electronics_count` | int64 |  | 0.0 | 0 → 52 (median 0) | Place count in cell: retail electronics (55-cat fine taxonomy) |
| `pc2_cat_retail_furniture_home_count` | int64 |  | 0.0 | 0 → 44 (median 0) | Place count in cell: retail furniture home (55-cat fine taxonomy) |
| `pc2_cat_retail_general_count` | int64 |  | 0.0 | 0 → 31 (median 0) | Place count in cell: retail general (55-cat fine taxonomy) |
| `pc2_cat_retail_jewelry_cosmetics_count` | int64 |  | 0.0 | 0 → 90 (median 0) | Place count in cell: retail jewelry cosmetics (55-cat fine taxonomy) |
| `pc2_cat_retail_mall_count` | int64 |  | 0.0 | 0 → 14 (median 0) | Place count in cell: retail mall (55-cat fine taxonomy) |
| `pc2_cat_retail_supermarket_count` | int64 |  | 0.0 | 0 → 16 (median 0) | Place count in cell: retail supermarket (55-cat fine taxonomy) |
| `pc2_cat_service_automotive_count` | int64 |  | 0.0 | 0 → 143 (median 0) | Place count in cell: service automotive (55-cat fine taxonomy) |
| `pc2_cat_service_beauty_count` | int64 |  | 0.0 | 0 → 96 (median 0) | Place count in cell: service beauty (55-cat fine taxonomy) |
| `pc2_cat_service_cleaning_repair_count` | int64 |  | 0.0 | 0 → 11 (median 0) | Place count in cell: service cleaning repair (55-cat fine taxonomy) |
| `pc2_cat_service_consulting_count` | int64 |  | 0.0 | 0 → 225 (median 0) | Place count in cell: service consulting (55-cat fine taxonomy) |
| `pc2_cat_service_fitness_count` | int64 |  | 0.0 | 0 → 35 (median 0) | Place count in cell: service fitness (55-cat fine taxonomy) |
| `pc2_cat_service_legal_finance_count` | int64 |  | 0.0 | 0 → 200 (median 0) | Place count in cell: service legal finance (55-cat fine taxonomy) |
| `pc2_cat_service_logistics_count` | int64 |  | 0.0 | 0 → 116 (median 0) | Place count in cell: service logistics (55-cat fine taxonomy) |
| `pc2_cat_service_other_count` | int64 |  | 0.0 | 0 → 105 (median 0) | Place count in cell: service other (55-cat fine taxonomy) |
| `pc2_cat_service_pet_count` | int64 |  | 0.0 | 0 → 7 (median 0) | Place count in cell: service pet (55-cat fine taxonomy) |
| `pc2_cat_service_real_estate_count` | int64 |  | 0.0 | 0 → 106 (median 0) | Place count in cell: service real estate (55-cat fine taxonomy) |
| `pc2_cat_transport_air_count` | int64 |  | 0.0 | 0 → 5 (median 0) | Place count in cell: transport air (55-cat fine taxonomy) |
| `pc2_cat_transport_bus_count` | int64 |  | 0.0 | 0 → 16 (median 0) | Place count in cell: transport bus (55-cat fine taxonomy) |
| `pc2_cat_transport_ev_count` | int64 |  | 0.0 | 0 → 8 (median 0) | Place count in cell: transport ev (55-cat fine taxonomy) |
| `pc2_cat_transport_mrt_count` | int64 |  | 0.0 | 0 → 5 (median 0) | Place count in cell: transport mrt (55-cat fine taxonomy) |
| `pc2_cat_transport_other_count` | int64 |  | 0.0 | 0 → 3 (median 0) | Place count in cell: transport other (55-cat fine taxonomy) |
| `pc2_cat_transport_parking_count` | int64 |  | 0.0 | 0 → 10 (median 0) | Place count in cell: transport parking (55-cat fine taxonomy) |
| `pc2_cat_unmapped_count` | int64 |  | 0.0 | 0 → 51 (median 0) | Place count in cell: unmapped (55-cat fine taxonomy) |
| `pc2_dominant_category` | object |  | 0.0 | 48 unique · `none` | Fine-taxonomy place metric: dominant category |
| `pc2_total` | int64 |  | 0.0 | 0 → 1215 (median 1) | Fine-taxonomy place metric: total |
| `pc2_unbranded_count` | int64 |  | 0.0 | 0 → 1189 (median 1) | Fine-taxonomy place metric: unbranded count |
| `pc_avg_rating` | float64 | stars | 0.0 | 0 → 5 (median 3.4) | Mean rating of rated places — quality proxy |
| `pc_cat_bakery` | float64 |  | 0.0 | 0 → 22 (median 0) | Place count in cell: bakery category (24-cat taxonomy) |
| `pc_cat_bar_nightlife` | float64 |  | 0.0 | 0 → 25 (median 0) | Place count in cell: bar nightlife category (24-cat taxonomy) |
| `pc_cat_beauty_personal` | float64 |  | 0.0 | 0 → 104 (median 0) | Place count in cell: beauty personal category (24-cat taxonomy) |
| `pc_cat_business_office` | float64 |  | 0.0 | 0 → 368 (median 0) | Place count in cell: business office category (24-cat taxonomy) |
| `pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 49 (median 0) | Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pc_cat_convenience` | float64 |  | 0.0 | 0 → 33 (median 0) | Place count in cell: convenience category (24-cat taxonomy) |
| `pc_cat_education` | float64 |  | 0.0 | 0 → 75 (median 0) | Place count in cell: education category (24-cat taxonomy) |
| `pc_cat_entertainment_culture` | float64 |  | 0.0 | 0 → 22 (median 0) | Place count in cell: entertainment culture category (24-cat taxonomy) |
| `pc_cat_fast_food` | float64 |  | 0.0 | 0 → 12 (median 0) | Place count in cell: fast food category (24-cat taxonomy) |
| `pc_cat_fitness_recreation` | float64 |  | 0.0 | 0 → 40 (median 0) | Place count in cell: fitness recreation category (24-cat taxonomy) |
| `pc_cat_government_public` | float64 |  | 0.0 | 0 → 28 (median 0) | Place count in cell: government public category (24-cat taxonomy) |
| `pc_cat_hawker` | float64 |  | 0.0 | 0 → 96 (median 0) | Place count in cell: hawker category (24-cat taxonomy) |
| `pc_cat_health_medical` | float64 |  | 0.0 | 0 → 196 (median 0) | Place count in cell: health medical category (24-cat taxonomy) |
| `pc_cat_hotel_hospitality` | float64 |  | 0.0 | 0 → 51 (median 0) | Place count in cell: hotel hospitality category (24-cat taxonomy) |
| `pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 142 (median 0) | Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pc_cat_other_uncategorized` | float64 |  | 0.0 | 0 → 134 (median 0) | Place count in cell: other uncategorized category (24-cat taxonomy) |
| `pc_cat_park_open` | float64 |  | 0.0 | 0 → 17 (median 0) | Place count in cell: park open category (24-cat taxonomy) |
| `pc_cat_religious_worship` | float64 |  | 0.0 | 0 → 24 (median 0) | Place count in cell: religious worship category (24-cat taxonomy) |
| `pc_cat_residential` | float64 |  | 0.0 | 0 → 30 (median 0) | Place count in cell: residential category (24-cat taxonomy) |
| `pc_cat_restaurant` | float64 |  | 0.0 | 0 → 88 (median 0) | Place count in cell: restaurant category (24-cat taxonomy) |
| `pc_cat_services` | float64 |  | 0.0 | 0 → 259 (median 0) | Place count in cell: services category (24-cat taxonomy) |
| `pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 229 (median 0) | Place count in cell: shopping retail category (24-cat taxonomy) |
| `pc_cat_supermarket` | float64 |  | 0.0 | 0 → 18 (median 0) | Place count in cell: supermarket category (24-cat taxonomy) |
| `pc_cat_transportation` | float64 |  | 0.0 | 0 → 29 (median 0) | Place count in cell: transportation category (24-cat taxonomy) |
| `pc_diversity` | float64 | 0-1 | 0.0 | 0 → 2.925 (median 0) | Category entropy of the place mix — high = mixed-use |
| `pc_dominant_category` | object | category | 0.0 | 24 unique · `none` | Most common place category in cell |
| `pc_long_tail` | float64 | count | 0.0 | 0 → 725 (median 1) | Places with few/no reviews — independent long-tail share base |
| `pc_magnets` | float64 | count | 0.0 | 0 → 266 (median 0) | High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pc_total` | float64 | count | 0.0 | 0 → 1215 (median 1) | Total mapped places (POIs) in cell — overall point-of-interest density |
| `pc_total_reviews` | float64 | count | 0.0 | 0 → 3.406e+05 (median 2) | Sum of review counts — popularity/footfall proxy |
| `pc_unique_brands` | float64 | count | 0.0 | 0 → 96 (median 0) | Distinct retail/F&B brands present — chain richness |
| `pc_with_rating` | float64 | count | 0.0 | 0 → 704 (median 1) | Places carrying a Google rating |
| `ped_countdown` | int64 |  | 0.0 | 0 → 17 (median 0) | Road-network metric: ped countdown |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 228.6 (median 6.367) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 2.4e+04 (median 668.6) | Footway + path + cycleway + steps length |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1721 (median 0) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 9727 (median 0.0659) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2092 (median 0.0027) | Population age 65+ |
| `pop_dorm` | float64 | persons | 0.0 | 0 → 2.978e+04 (median 0) | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.26e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 2049 (median 0.0252) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 3.034e+04 (median 45.77) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.322e+04 (median 0.0968) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 3.105e+04 (median 104.5) | Total population (residents + non-residents) |
| `preschool_count` | int64 |  | 0.0 | 0 → 14 (median 0) | preschool count (see layer docs) |
| `preschools_within_400m` | int64 |  | 0.0 | 0 → 25 (median 0) | Count of preschools within 400m |
| `primary_school_zone_count` | int64 | count | 0.0 | 0 → 3 (median 0) | Primary-school zones overlapping cell |
| `primary_schools_within_1km` | int64 |  | 0.0 | 0 → 9 (median 0) | Count of primary schools within 1km |
| `primary_schools_within_2km` | int64 |  | 0.0 | 0 → 19 (median 0) | Count of primary schools within 2km |
| `pull_airport` | float64 |  | 0.0 | 0 → 1 (median 0.226) | Gravity pull toward airport (distance-decayed attraction) |
| `pull_cbd` | float64 |  | 0.0 | 0 → 1 (median 0.0745) | Gravity pull toward cbd (distance-decayed attraction) |
| `pull_composite` | float64 |  | 0.0 | 0 → 0.762 (median 0.133) | Gravity pull toward composite (distance-decayed attraction) |
| `pull_hospital` | float64 |  | 0.0 | 0 → 1 (median 0.08) | Gravity pull toward hospital (distance-decayed attraction) |
| `pull_mall` | float64 |  | 0.0 | 0 → 1 (median 0.047) | Gravity pull toward mall (distance-decayed attraction) |
| `pull_mrt_interchange` | float64 |  | 0.0 | 0 → 1 (median 0.052) | Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pull_school_premium` | float64 |  | 0.0 | 0 → 1 (median 0.115) | Gravity pull toward school premium (distance-decayed attraction) |
| `pw1_chas_clinic_count` | float64 |  | 0.0 | 0 → 4.642 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: chas clinic count (see layer docs) |
| `pw1_commercial_intensity` | float64 |  | 0.0 | 0 → 0.9 (median 0.013) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `pw1_density_pressure` | float64 |  | 0.0 | 0 → 0.729 (median 0.001) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: population + buildings + low road space |
| `pw1_family_index` | float64 |  | 0.0 | 0 → 0.925 (median 0.05) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: children + schools + preschools + family amenities |
| `pw1_hawker_centre_count` | float64 |  | 0.0 | 0 → 1.758 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: hawker centre count (see layer docs) |
| `pw1_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: hdb resale 4r median psm (see layer docs) |
| `pw1_nl_2024` | float64 |  | 0.0 | 0 → 167.3 (median 13.86) | Proximity-weighted (distance-decayed) ring-1 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `pw1_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 163.2 (median 13.23) | Proximity-weighted (distance-decayed) ring-1 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `pw1_pc_cat_business_office` | float64 |  | 0.0 | 0 → 184.4 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: business office category (24-cat taxonomy) |
| `pw1_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 31.69 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pw1_pc_cat_education` | float64 |  | 0.0 | 0 → 42.5 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: education category (24-cat taxonomy) |
| `pw1_pc_cat_hawker` | float64 |  | 0.0 | 0 → 55.38 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: hawker category (24-cat taxonomy) |
| `pw1_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 60.02 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: health medical category (24-cat taxonomy) |
| `pw1_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 94.9 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pw1_pc_cat_residential` | float64 |  | 0.0 | 0 → 25.56 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: residential category (24-cat taxonomy) |
| `pw1_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 78.65 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) |
| `pw1_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 98.08 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `pw1_pc_magnets` | float64 |  | 0.0 | 0 → 147.9 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pw1_pc_total` | float64 |  | 0.0 | 0 → 796.2 (median 0.2485) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `pw1_pc_unique_brands` | float64 |  | 0.0 | 0 → 50.73 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Distinct retail/F&B brands present — chain richness |
| `pw1_preschools_within_400m` | float64 |  | 0.0 | 0 → 17.72 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of preschools within 400m |
| `pw1_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 7.369 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Count of primary schools within 1km |
| `pw1_pull_cbd` | float64 |  | 0.0 | 0 → 0.985 (median 0.036) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward cbd (distance-decayed attraction) |
| `pw1_pull_mall` | float64 |  | 0.0 | 0 → 0.971 (median 0.022) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mall (distance-decayed attraction) |
| `pw1_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.984 (median 0.018) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pw1_tourist_attraction_count` | float64 |  | 0.0 | 0 → 3.437 (median 0) | Proximity-weighted (distance-decayed) ring-1 aggregate of: tourist attraction count (see layer docs) |
| `pw1_transit_score` | float64 |  | 0.0 | 0 → 0.962 (median 0.184) | Proximity-weighted (distance-decayed) ring-1 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `pw1_vibrancy_index` | float64 |  | 0.0 | 0 → 0.963 (median 0.067) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite: places + magnets + reviews + transit + night lights |
| `pw1_walkability_score` | float64 |  | 0.0 | 0 → 0.934 (median 0.093) | Proximity-weighted (distance-decayed) ring-1 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `pw1_wc_built_share` | float64 |  | 0.0 | 0 → 0.991 (median 0.0575) | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: built share |
| `pw1_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.0965) | Proximity-weighted (distance-decayed) ring-1 aggregate of: ESA WorldCover land-cover share: tree share |
| `pw2_chas_clinic_count` | float64 |  | 0.0 | 0 → 4.189 (median 0) | Proximity-weighted ring-2 aggregate of: chas clinic count (see layer docs) |
| `pw2_commercial_intensity` | float64 |  | 0.0 | 0 → 0.876 (median 0.027) | Proximity-weighted ring-2 aggregate of: Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `pw2_density_pressure` | float64 |  | 0.0 | 0 → 0.722 (median 0.014) | Proximity-weighted ring-2 aggregate of: Composite: population + buildings + low road space |
| `pw2_family_index` | float64 |  | 0.0 | 0 → 0.917 (median 0.13) | Proximity-weighted ring-2 aggregate of: Composite: children + schools + preschools + family amenities |
| `pw2_hawker_centre_count` | float64 |  | 0.0 | 0 → 1.541 (median 0) | Proximity-weighted ring-2 aggregate of: hawker centre count (see layer docs) |
| `pw2_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9020 (median 0) | Proximity-weighted ring-2 aggregate of: hdb resale 4r median psm (see layer docs) |
| `pw2_nl_2024` | float64 |  | 0.0 | 0 → 165.7 (median 28.62) | Proximity-weighted ring-2 aggregate of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `pw2_nl_commercial_indicator` | float64 |  | 0.0 | 0 → 158.5 (median 13.85) | Proximity-weighted ring-2 aggregate of: nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `pw2_pc_cat_business_office` | float64 |  | 0.0 | 0 → 184.8 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: business office category (24-cat taxonomy) |
| `pw2_pc_cat_cafe_coffee` | float64 |  | 0.0 | 0 → 27.3 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pw2_pc_cat_education` | float64 |  | 0.0 | 0 → 37.2 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: education category (24-cat taxonomy) |
| `pw2_pc_cat_hawker` | float64 |  | 0.0 | 0 → 47.01 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: hawker category (24-cat taxonomy) |
| `pw2_pc_cat_health_medical` | float64 |  | 0.0 | 0 → 39.06 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: health medical category (24-cat taxonomy) |
| `pw2_pc_cat_industrial_mfg` | float64 |  | 0.0 | 0 → 81.45 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pw2_pc_cat_residential` | float64 |  | 0.0 | 0 → 24.03 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: residential category (24-cat taxonomy) |
| `pw2_pc_cat_restaurant` | float64 |  | 0.0 | 0 → 66.61 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: restaurant category (24-cat taxonomy) |
| `pw2_pc_cat_shopping_retail` | float64 |  | 0.0 | 0 → 72.75 (median 0) | Proximity-weighted ring-2 aggregate of: Place count in cell: shopping retail category (24-cat taxonomy) |
| `pw2_pc_magnets` | float64 |  | 0.0 | 0 → 127.9 (median 0) | Proximity-weighted ring-2 aggregate of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pw2_pc_total` | float64 |  | 0.0 | 0 → 734.1 (median 2.083) | Proximity-weighted ring-2 aggregate of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `pw2_pc_unique_brands` | float64 |  | 0.0 | 0 → 40.12 (median 0) | Proximity-weighted ring-2 aggregate of: Distinct retail/F&B brands present — chain richness |
| `pw2_preschools_within_400m` | float64 |  | 0.0 | 0 → 16.68 (median 0) | Proximity-weighted ring-2 aggregate of: Count of preschools within 400m |
| `pw2_primary_schools_within_1km` | float64 |  | 0.0 | 0 → 7.053 (median 0) | Proximity-weighted ring-2 aggregate of: Count of primary schools within 1km |
| `pw2_pull_cbd` | float64 |  | 0.0 | 0 → 0.973 (median 0.047) | Proximity-weighted ring-2 aggregate of: Gravity pull toward cbd (distance-decayed attraction) |
| `pw2_pull_mall` | float64 |  | 0.0 | 0 → 0.945 (median 0.039) | Proximity-weighted ring-2 aggregate of: Gravity pull toward mall (distance-decayed attraction) |
| `pw2_pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.968 (median 0.035) | Proximity-weighted ring-2 aggregate of: Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pw2_tourist_attraction_count` | float64 |  | 0.0 | 0 → 2.487 (median 0) | Proximity-weighted ring-2 aggregate of: tourist attraction count (see layer docs) |
| `pw2_transit_score` | float64 |  | 0.0 | 0 → 0.925 (median 0.291) | Proximity-weighted ring-2 aggregate of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `pw2_vibrancy_index` | float64 |  | 0.0 | 0 → 0.947 (median 0.1065) | Proximity-weighted ring-2 aggregate of: Composite: places + magnets + reviews + transit + night lights |
| `pw2_walkability_score` | float64 |  | 0.0 | 0 → 0.928 (median 0.241) | Proximity-weighted ring-2 aggregate of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `pw2_wc_built_share` | float64 |  | 0.0 | 0 → 0.978 (median 0.2025) | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: built share |
| `pw2_wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.133) | Proximity-weighted ring-2 aggregate of: ESA WorldCover land-cover share: tree share |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 3704 (median 0) | Rail line length through hex (above + underground) |
| `ring1_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 0) | Sum over H3 ring-1 neighbours (~±1 km) of: hdb resale 4r median psm (see layer docs) |
| `ring1_nl_2024` | float64 |  | 0.0 | 0 → 160.4 (median 50.02) | Sum over H3 ring-1 neighbours (~±1 km) of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `ring1_pc_magnets` | float64 |  | 0.0 | 0 → 139 (median 0.167) | Sum over H3 ring-1 neighbours (~±1 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `ring1_pc_total` | float64 |  | 0.0 | 0 → 812.2 (median 3.5) | Sum over H3 ring-1 neighbours (~±1 km) of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `ring1_pop_nonresident` | float64 |  | 0.0 | 0 → 5940 (median 130.6) | Sum over H3 ring-1 neighbours (~±1 km) of: Non-residents (FW + EP + MDW) |
| `ring1_pop_resident` | float64 |  | 0.0 | 0 → 6592 (median 1.001) | Sum over H3 ring-1 neighbours (~±1 km) of: Resident population (citizens + PRs) |
| `ring1_school_count_total` | float64 |  | 0.0 | 0 → 6 (median 0) | Sum over H3 ring-1 neighbours (~±1 km) of: school count total (see layer docs) |
| `ring1_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.406) | Sum over H3 ring-1 neighbours (~±1 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `ring1_walkability_score` | float64 |  | 0.0 | 0 → 0.934 (median 0.261) | Sum over H3 ring-1 neighbours (~±1 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `ring2_hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 8833 (median 0) | Sum over H3 ring-2 neighbours (~±2 km) of: hdb resale 4r median psm (see layer docs) |
| `ring2_nl_2024` | float64 |  | 0.0 | 0 → 158.6 (median 50.32) | Sum over H3 ring-2 neighbours (~±2 km) of: VIIRS night light radiance 2024 (subzone-broadcast) |
| `ring2_pc_magnets` | float64 |  | 0.0 | 0 → 80.92 (median 0.25) | Sum over H3 ring-2 neighbours (~±2 km) of: High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `ring2_pc_total` | float64 |  | 0.0 | 0 → 509.9 (median 6.417) | Sum over H3 ring-2 neighbours (~±2 km) of: Total mapped places (POIs) in cell — overall point-of-interest density |
| `ring2_pop_nonresident` | float64 |  | 0.0 | 0 → 4971 (median 166) | Sum over H3 ring-2 neighbours (~±2 km) of: Non-residents (FW + EP + MDW) |
| `ring2_pop_resident` | float64 |  | 0.0 | 0 → 5622 (median 4.455) | Sum over H3 ring-2 neighbours (~±2 km) of: Resident population (citizens + PRs) |
| `ring2_school_count_total` | float64 |  | 0.0 | 0 → 9 (median 0) | Sum over H3 ring-2 neighbours (~±2 km) of: school count total (see layer docs) |
| `ring2_transit_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.481) | Sum over H3 ring-2 neighbours (~±2 km) of: 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `ring2_walkability_score` | float64 |  | 0.0 | 0 → 0.916 (median 0.277) | Sum over H3 ring-2 neighbours (~±2 km) of: Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 271 (median 27.54) | Road km per km² |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 2.846e+04 (median 2892) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `sat_bakery_per_1k` | float64 |  | 0.0 | 0 → 66.69 (median 0) | Supply saturation: bakery outlets per 1,000 residents |
| `sat_beauty_personal_per_1k` | float64 |  | 0.0 | 0 → 196.4 (median 0) | Supply saturation: beauty personal outlets per 1,000 residents |
| `sat_cafe_coffee_per_1k` | float64 |  | 0.0 | 0 → 169.8 (median 0) | Supply saturation: cafe coffee outlets per 1,000 residents |
| `sat_fast_food_per_1k` | float64 |  | 0.0 | 0 → 53.54 (median 0) | Supply saturation: fast food outlets per 1,000 residents |
| `sat_fitness_recreation_per_1k` | float64 |  | 0.0 | 0 → 59.54 (median 0) | Supply saturation: fitness recreation outlets per 1,000 residents |
| `sat_hawker_per_1k` | float64 |  | 0.0 | 0 → 127.3 (median 0) | Supply saturation: hawker outlets per 1,000 residents |
| `sat_health_medical_per_1k` | float64 |  | 0.0 | 0 → 174.3 (median 0) | Supply saturation: health medical outlets per 1,000 residents |
| `sat_restaurant_per_1k` | float64 |  | 0.0 | 0 → 329.3 (median 0) | Supply saturation: restaurant outlets per 1,000 residents |
| `sat_supermarket_per_1k` | float64 |  | 0.0 | 0 → 49.01 (median 0) | Supply saturation: supermarket outlets per 1,000 residents |
| `school_count_jc` | int64 |  | 0.0 | 0 → 1 (median 0) | school count jc (see layer docs) |
| `school_count_mixed` | int64 |  | 0.0 | 0 → 0 (median 0) | school count mixed (see layer docs) |
| `school_count_premium` | int64 |  | 0.0 | 0 → 2 (median 0) | school count premium (see layer docs) |
| `school_count_primary` | int64 |  | 0.0 | 0 → 2 (median 0) | school count primary (see layer docs) |
| `school_count_secondary` | int64 |  | 0.0 | 0 → 2 (median 0) | school count secondary (see layer docs) |
| `school_count_total` | int64 |  | 0.0 | 0 → 3 (median 0) | school count total (see layer docs) |
| `sig_beacon` | int64 |  | 0.0 | 0 → 20 (median 0) | Road-network metric: sig beacon |
| `sig_bicycle` | int64 |  | 0.0 | 0 → 4 (median 0) | Road-network metric: sig bicycle |
| `sig_filter_arrow` | int64 |  | 0.0 | 0 → 22 (median 0) | Road-network metric: sig filter arrow |
| `sig_ground` | int64 |  | 0.0 | 0 → 51 (median 0) | Road-network metric: sig ground |
| `sig_overhead` | int64 |  | 0.0 | 0 → 14 (median 0) | Road-network metric: sig overhead |
| `sig_pedestrian` | int64 |  | 0.0 | 0 → 48 (median 0) | Road-network metric: sig pedestrian |
| `sig_rag` | int64 |  | 0.0 | 0 → 24 (median 0) | Road-network metric: sig rag |
| `sig_total` | int64 |  | 0.0 | 0 → 143 (median 0) | Road-network metric: sig total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |
| `silver_zone_count` | int64 |  | 0.0 | 0 → 2 (median 0) | silver zone count (see layer docs) |
| `speed_band_avg` | float64 |  | 0.0 | 0 → 8 (median 0) | speed band avg (see layer docs) |
| `speed_band_count` | int64 |  | 0.0 | 0 → 119 (median 0) | speed band count (see layer docs) |
| `syn_density_x_amenities` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: density x amenities (cross-feature product) |
| `syn_far_x_transit` | float64 |  | 0.0 | 0 → 0 (median 0) | Synergy interaction term: far x transit (cross-feature product) |
| `syn_office_x_transit` | float64 |  | 0.0 | 0 → 0.987 (median 0) | Synergy interaction term: office x transit (cross-feature product) |
| `syn_pop_x_transit` | float64 |  | 0.0 | 0 → 0.984 (median 0) | Synergy interaction term: pop x transit (cross-feature product) |
| `syn_pop_x_walk` | float64 |  | 0.0 | 0 → 0.93 (median 0) | Synergy interaction term: pop x walk (cross-feature product) |
| `syn_premium_school_x_4r` | float64 |  | 0.0 | 0 → 0 (median 0) | Synergy interaction term: premium school x 4r (cross-feature product) |
| `syn_residential_x_school` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: residential x school (cross-feature product) |
| `syn_retail_x_anchors` | float64 |  | 0.0 | 0 → 1 (median 0) | Synergy interaction term: retail x anchors (cross-feature product) |
| `tourist_attraction_count` | int64 |  | 0.0 | 0 → 5 (median 0) | tourist attraction count (see layer docs) |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.754e-08 → 0.9879 (median 0.3227) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `vibrancy_index` | float64 | 0-1 | 0.0 | 0 → 0.99 (median 0.124) | Composite: places + magnets + reviews + transit + night lights |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 2111 (median 5) | Place count within 400m walk |
| `walk_bus_score` | float64 |  | 0.0 | 0 → 0.987 (median 0.314) | Walk-access score to nearest bus (distance-decayed) |
| `walk_clinic_400m` | int64 | count | 0.0 | 0 → 321 (median 0) | Clinics within 400m walk |
| `walk_clinic_score` | float64 |  | 0.0 | 0 → 0.996 (median 0.064) | Walk-access score to nearest clinic (distance-decayed) |
| `walk_convenience_400m` | int64 | count | 0.0 | 0 → 58 (median 0) | Convenience stores within 400m walk |
| `walk_convenience_score` | float64 |  | 0.0 | 0 → 0.991 (median 0.151) | Walk-access score to nearest convenience (distance-decayed) |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 491 (median 0) | Food places within 400m walk |
| `walk_food_score` | float64 |  | 0.0 | 0 → 0.995 (median 0.199) | Walk-access score to nearest food (distance-decayed) |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 160 (median 0) | Hawkers within 400m walk |
| `walk_hawker_score` | float64 |  | 0.0 | 0 → 0.995 (median 0.0495) | Walk-access score to nearest hawker (distance-decayed) |
| `walk_mrt_score` | float64 |  | 0.0 | 0 → 1 (median 0.016) | Walk-access score to nearest mrt (distance-decayed) |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 10 (median 0) | Parks within 400m walk |
| `walk_park_score` | float64 |  | 0.0 | 0 → 1 (median 0.047) | Walk-access score to nearest park (distance-decayed) |
| `walk_school_400m` | int64 | count | 0.0 | 0 → 131 (median 0) | Schools within 400m walk |
| `walk_school_score` | float64 |  | 0.0 | 0 → 0.995 (median 0.121) | Walk-access score to nearest school (distance-decayed) |
| `walk_score_avg` | float64 | 0-1 | 0.0 | 0 → 0.933 (median 0.165) | Mean of the 9 amenity walk-access scores |
| `walk_supermarket_400m` | int64 | count | 0.0 | 0 → 42 (median 0) | Supermarkets within 400m walk |
| `walk_supermarket_score` | float64 |  | 0.0 | 0 → 0.988 (median 0.072) | Walk-access score to nearest supermarket (distance-decayed) |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9587 (median 0.2351) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `wc_built_share` | float64 |  | 0.0 | 0 → 1 (median 0.252) | ESA WorldCover land-cover share: built share |
| `wc_dominant_class` | int64 |  | 0.0 | 10 → 95 (median 50) | ESA WorldCover land-cover share: dominant class |
| `wc_grass_share` | float64 |  | 0.0 | 0 → 1 (median 0.015) | ESA WorldCover land-cover share: grass share |
| `wc_other_share` | float64 |  | 0.0 | 0 → 1 (median 0.001) | ESA WorldCover land-cover share: other share |
| `wc_tree_share` | float64 |  | 0.0 | 0 → 1 (median 0.169) | ESA WorldCover land-cover share: tree share |
| `wc_water_share` | float64 |  | 0.0 | 0 → 1 (median 0) | ESA WorldCover land-cover share: water share |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.645e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex9_buildings.parquet`

_39 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_floors` | Float64 | floors | 67.3 | 0.5 → 60 (median 6.5) | Mean building floors in cell |
| `avg_height` | float64 | m | 91.4 | 0 → 182 (median 0) | Mean building height in cell |
| `best_avg_floors` | Float64 | floors | 66.4 | 0.5 → 60 (median 13) | Avg floor count |
| `best_max_floors` | Float64 | floors | 66.4 | 1 → 70 (median 18) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_area_m2` | float64 |  | 0.0 | 0 → 6.799e+04 (median 0) | bldg commercial area m2 (see layer docs) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_commercial_share` | float64 |  | 0.0 | 0 → 1 (median 0) | bldg commercial share (see layer docs) |
| `bldg_count` | float64 | count | 0.0 | 0 → 518 (median 17) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 4933 (median 161.9) | Buildings per km² |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 3.371 (median 0.0577) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_area_m2` | float64 |  | 0.0 | 0 → 1.822e+05 (median 0) | bldg industrial area m2 (see layer docs) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 69 (median 0) | Industrial buildings |
| `bldg_industrial_share` | float64 |  | 0.0 | 0 → 1 (median 0) | bldg industrial share (see layer docs) |
| `bldg_institutional_area_m2` | float64 |  | 0.0 | 0 → 7.197e+04 (median 0) | bldg institutional area m2 (see layer docs) |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 21 (median 0) | Institutional buildings |
| `bldg_other_area_m2` | float64 |  | 0.0 | 0 → 2.019e+04 (median 0) | bldg other area m2 (see layer docs) |
| `bldg_other_count` | float64 |  | 0.0 | 0 → 26 (median 0) | bldg other count (see layer docs) |
| `bldg_religious_area_m2` | float64 |  | 0.0 | 0 → 1.075e+04 (median 0) | bldg religious area m2 (see layer docs) |
| `bldg_religious_count` | float64 |  | 0.0 | 0 → 14 (median 0) | bldg religious count (see layer docs) |
| `bldg_residential_area_m2` | float64 |  | 0.0 | 0 → 7.518e+04 (median 0) | bldg residential area m2 (see layer docs) |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 454 (median 0) | Residential buildings |
| `bldg_residential_share` | float64 |  | 0.0 | 0 → 1 (median 0) | bldg residential share (see layer docs) |
| `bldg_total_area_m2` | float64 | m² | 0.0 | 0 → 3.539e+05 (median 6056) | Total building footprint area |
| `bldg_transport_area_m2` | float64 |  | 0.0 | 0 → 8.474e+04 (median 0) | bldg transport area m2 (see layer docs) |
| `bldg_transport_count` | float64 |  | 0.0 | 0 → 6 (median 0) | bldg transport count (see layer docs) |
| `bldg_unclassified_area_m2` | float64 |  | 0.0 | 0 → 3.539e+05 (median 2308) | bldg unclassified area m2 (see layer docs) |
| `bldg_unclassified_count` | float64 |  | 0.0 | 0 → 418 (median 14) | bldg unclassified count (see layer docs) |
| `hdb_avg_floors` | float64 | floors | 83.8 | 3 → 45 (median 21) | Avg HDB floor count |
| `hdb_avg_year` | float64 | year | 83.8 | 1937 → 2024 (median 1981) | Avg HDB completion year |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.07e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 83.8 | 3 → 50 (median 27) | Max HDB floor count |
| `hdb_min_year` | float64 | year | 83.8 | 1937 → 2024 (median 1976) | Earliest HDB completion year |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | boolean | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.472 (median 1.352) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `max_floors` | Float64 | floors | 67.3 | 1 → 70 (median 12) | Tallest building floors in cell |
| `max_height` | float64 | m | 91.4 | 0 → 245 (median 0) | Tallest building height in cell |

## `hex/hex9_buildings_clean.parquet`

_20 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `best_max_floors` | float64 | floors | 63.6 | 1 → 70 (median 16.5) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 541 (median 20) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5152 (median 190.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 1.213e+05 (median 6765) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0644) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 71 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 27 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 474 (median 0) | Residential buildings |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 10.03 (median 0.2165) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.053e+06 (median 2.273e+04) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 83.8 | 2 → 65 (median 44.97) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.055e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 83.8 | 3 → 50 (median 27) | Max HDB floor count |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 474 (median 0) | Number of buildings with floors ≥ 10 |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |

## `hex/hex9_built_environment_features.parquet`

_41 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 21.96 (median 0) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 0) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 87 (median 0) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 541 (median 20) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5152 (median 190.5) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 1.213e+05 (median 6765) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0644) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 71 (median 0) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 27 (median 0) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 474 (median 0) | Residential buildings |
| `dominant_use` | object | categorical | 0.0 | 14 unique · `transport` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 10.03 (median 0.2165) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.053e+06 (median 2.273e+04) | Sum of footprint × est_floors per building |
| `hdb_avg_age_years` | float64 | years | 0.0 | 0 → 65 (median 0) | Avg years since HDB completion (year_completed filtered ≥1960) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 110 (median 0) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 1.055e+04 (median 0) | Total dwelling units across HDB blocks |
| `hdb_max_floors` | float64 | floors | 0.0 | 0 → 50 (median 0) | Max HDB floor count |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_highrise` | bool | bool | 0.0 | 0 → 1 (median 0) | True if max_floors >= 10 |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8105 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9317 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.084 (median 0.514) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8857 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8988 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6274 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0026) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 533 (median 5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 1.308e+05 (median 1.191e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 0) | Max GPR within hex |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 474 (median 0) | Number of buildings with floors ≥ 10 |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |

## `hex/hex9_colo_fit.parquet`

_12 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `colo_fit_beauty_personal` | float64 | log-lift | 0.0 | -0.4176 → 0.5449 (median 0.1032) | Co-location mix-match for beauty_personal: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_cafe_coffee` | float64 | log-lift | 0.0 | -0.3487 → 0.1852 (median 0.0111) | Co-location mix-match for cafe_coffee: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_convenience` | float64 | log-lift | 0.0 | -0.5409 → 0.2072 (median -0.0929) | Co-location mix-match for convenience: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_education` | float64 | log-lift | 0.0 | -0.5588 → 0.225 (median -0.1164) | Co-location mix-match for education: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fast_food` | float64 | log-lift | 0.0 | -0.7358 → 0.2334 (median 0) | Co-location mix-match for fast_food: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_fitness_recreation` | float64 | log-lift | 0.0 | -0.5761 → 0.1972 (median -0.0661) | Co-location mix-match for fitness_recreation: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_hawker` | float64 | log-lift | 0.0 | -0.5998 → 0.2785 (median -0.0473) | Co-location mix-match for hawker: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_health_medical` | float64 | log-lift | 0.0 | -0.5084 → 0.2515 (median 0) | Co-location mix-match for health_medical: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_restaurant` | float64 | log-lift | 0.0 | -0.1131 → 0.5658 (median 0.161) | Co-location mix-match for restaurant: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_shopping_retail` | float64 | log-lift | 0.0 | -0.0564 → 0.416 (median 0.1229) | Co-location mix-match for shopping_retail: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `colo_fit_supermarket` | float64 | log-lift | 0.0 | -0.364 → 0.1704 (median -0.0443) | Co-location mix-match for supermarket: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only) |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |

## `hex/hex9_huff_capture.parquet`

_14 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `cap_beauty_personal` | float64 | outlet-equivalents | 0.0 | 0 → 3.906 (median 0.3291) | Huff capture for a NEW beauty_personal outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_best_category` | object | category | 0.0 | 11 unique · `cafe_coffee` | Category with the highest capture at this hex |
| `cap_cafe_coffee` | float64 | outlet-equivalents | 0.0 | 0 → 3.905 (median 0.2431) | Huff capture for a NEW cafe_coffee outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_convenience` | float64 | outlet-equivalents | 0.0 | 0 → 2.902 (median 0.1769) | Huff capture for a NEW convenience outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_education` | float64 | outlet-equivalents | 0.0 | 0 → 2.473 (median 0.2614) | Huff capture for a NEW education outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fast_food` | float64 | outlet-equivalents | 0.0 | 0 → 2.063 (median 0.1865) | Huff capture for a NEW fast_food outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_fitness_recreation` | float64 | outlet-equivalents | 0.0 | 0 → 3.482 (median 0.2521) | Huff capture for a NEW fitness_recreation outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_hawker` | float64 | outlet-equivalents | 0.0 | 0 → 4.939 (median 0.2019) | Huff capture for a NEW hawker outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_health_medical` | float64 | outlet-equivalents | 0.0 | 0 → 4.321 (median 0.2753) | Huff capture for a NEW health_medical outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_restaurant` | float64 | outlet-equivalents | 0.0 | 0 → 3.857 (median 0.4208) | Huff capture for a NEW restaurant outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_shopping_retail` | float64 | outlet-equivalents | 0.0 | 0 → 4.058 (median 0.4699) | Huff capture for a NEW shopping_retail outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_supermarket` | float64 | outlet-equivalents | 0.0 | 0 → 3.31 (median 0.1648) | Huff capture for a NEW supermarket outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet) |
| `cap_total` | float64 | outlet-equivalents | 0.0 | 0 → 36.82 (median 3.219) | Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83) |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |

## `hex/hex9_land_use.parquet`

_22 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 52.8 | 0.9014 → 21.96 (median 2.5) | Area-weighted Gross Plot Ratio |
| `dominant_use` | object | categorical | 0.0 | 14 unique · `transport` | Bucket with highest area share |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8105 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9317 (median 0) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | -0 → 2.084 (median 0.514) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8857 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8988 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6274 (median 0) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0026) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 1 → 533 (median 5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 0.02469 → 1.308e+05 (median 1.191e+05) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | Water body share |
| `max_gpr` | float64 | ratio | 52.8 | 1 → 25 (median 2.5) | Max GPR within hex |

## `hex/hex9_mobility_features.parquet`

_53 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 4369 (median 0) | Bridge segment length |
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 50 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 13 (median 0) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.042e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.212e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.373e+04 (median 463.5) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.409e+04 (median 1463) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.413e+04 (median 1762) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.409e+04 (median 1657) | Centroid distance to nearest MRT/LRT station |
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.639e+04 (median 1102) | Walk distance to nearest clinic |
| `dist_walk_convenience_m` | float64 | m | 0.0 | 3.638 → 1.41e+04 (median 755.2) | Walk distance to nearest convenience store |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.636e+04 (median 645) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.638e+04 (median 1202) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.091e+04 (median 1222) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.625e+04 (median 845.2) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.834e+04 (median 1055) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 7 (median 0) | Authoritative HDB multi-storey carparks |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 147.7 (median 17.13) | Lane-km per km² (lane count × length / area) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 10 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 3 (median 0) | MRT/LRT stations in hex |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0407) | Fraction of vehicular length that's one-way |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 15 (median 0) | OSM amenity=parking points |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 228.6 (median 6.367) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 2.4e+04 (median 668.6) | Footway + path + cycleway + steps length |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 3704 (median 0) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 271 (median 27.54) | Road km per km² |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 2.846e+04 (median 2892) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.754e-08 → 0.9879 (median 0.3227) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 2111 (median 5) | Place count within 400m walk |
| `walk_clinic_400m` | int64 | count | 0.0 | 0 → 321 (median 0) | Clinics within 400m walk |
| `walk_convenience_400m` | int64 | count | 0.0 | 0 → 58 (median 0) | Convenience stores within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 491 (median 0) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 160 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 10 (median 0) | Parks within 400m walk |
| `walk_school_400m` | int64 | count | 0.0 | 0 → 131 (median 0) | Schools within 400m walk |
| `walk_supermarket_400m` | int64 | count | 0.0 | 0 → 42 (median 0) | Supermarkets within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9587 (median 0.2351) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/hex9_population.parquet`

_15 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1602) | Non-resident share of total pop |
| `parent_pa` | object | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone_name` | object | string | 0.0 | 326 unique · `TUAS VIEW EXTENSION` | URA subzone full name |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1721 (median 0) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 9727 (median 0.0659) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2092 (median 0.0027) | Population age 65+ |
| `pop_dorm` | float64 | persons | 0.0 | 0 → 2.978e+04 (median 0) | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.26e+04 (median 0) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 2049 (median 0.0252) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 3.034e+04 (median 45.77) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.322e+04 (median 0.0968) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 3.105e+04 (median 104.5) | Total population (residents + non-residents) |

## `hex/hex9_roads_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 4369 (median 0) | Bridge segment length |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 31 (median 0) | Tarjan bridge endpoints (network cut points) |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 1.409e+04 (median 1463) | Centroid distance to nearest motorway/trunk segment |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 7 (median 0) | Authoritative HDB multi-storey carparks |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 147.7 (median 17.13) | Lane-km per km² (lane count × length / area) |
| `near_expressway_exit_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if motorway_link/trunk_link < 400m (drive-thru flag) |
| `oneway_pct` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.0407) | Fraction of vehicular length that's one-way |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 15 (median 0) | OSM amenity=parking points |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 271 (median 27.54) | Road km per km² |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 2.846e+04 (median 2892) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 13 unique · `none` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |

## `hex/hex9_satellite.parquet`

_11 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 46.03) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 48.49) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 4.41) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 167.3 (median 28.12) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 2.997 (median 0) | nl_2024 / pop_resident (commercial vs residential signal) |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.645e+04 (median 0) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/hex9_transit_clean.parquet`

_19 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bus_routes_per_stop_max` | float64 | count | 0.0 | 0 → 50 (median 0) | Max # routes serving a stop in hex (GTFS) |
| `bus_routes_per_stop_mean` | float64 | count | 0.0 | 0 → 50 (median 0) | Mean routes/stop in hex |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 13 (median 0) | Bus stops in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 1.042e+05 (median 0) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 2.212e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 1.373e+04 (median 463.5) | Centroid distance to nearest bus stop |
| `dist_mrt_exit_m` | float64 | m | 0.0 | 7.807 → 1.413e+04 (median 1762) | Centroid distance to nearest MRT exit |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 1.409e+04 (median 1657) | Centroid distance to nearest MRT/LRT station |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1389 → 999 (median 999) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `is_mrt_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | True if any station has ≥2 lines (slash-PT_CODE) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 10 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 3 (median 0) | MRT/LRT stations in hex |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 3704 (median 0) | Rail line length through hex (above + underground) |
| `transit_score` | float64 | score [0,1] | 0.0 | 2.754e-08 → 0.9879 (median 0.3227) | 0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m)) |

## `hex/hex9_universe.parquet`

_8 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `lat` | float64 | degrees | 0.0 | 1.159 → 1.472 (median 1.352) | Hex centroid latitude |
| `lng` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Hex centroid longitude |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_pa` | object | string | 0.0 | 55 unique · `TUAS` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `WEST REGION` | URA region (5 regions) |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `parent_subzone_name` | object | string | 0.0 | 326 unique · `TUAS VIEW EXTENSION` | URA subzone full name |

## `hex/hex9_walkability.parquet`

_27 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `dist_walk_clinic_m` | float64 | m | 0.0 | 1.673 → 1.639e+04 (median 1102) | Walk distance to nearest clinic |
| `dist_walk_convenience_m` | float64 | m | 0.0 | 3.638 → 1.41e+04 (median 755.2) | Walk distance to nearest convenience store |
| `dist_walk_food_m` | float64 | m | 0.0 | 1.963 → 1.636e+04 (median 645) | Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food |
| `dist_walk_hawker_m` | float64 | m | 0.0 | 1.963 → 1.638e+04 (median 1202) | Walk distance to nearest hawker (Euclidean × 1.3 detour) |
| `dist_walk_park_m` | float64 | m | 0.0 | 0 → 2.091e+04 (median 1222) | Walk distance to nearest park |
| `dist_walk_school_m` | float64 | m | 0.0 | 2.142 → 1.625e+04 (median 845.2) | Walk distance to nearest school |
| `dist_walk_supermarket_m` | float64 | m | 0.0 | 4.861 → 1.834e+04 (median 1055) | Walk distance to nearest supermarket |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `hex9_id` | object | string | 0.0 | 7318 unique · `896520c0007ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `near_bus_300m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if bus < 300m |
| `near_mrt_400m` | bool | bool | 0.0 | 0 → 1 (median 0) | True if MRT < 400m |
| `parent_hex8` | object | string | 0.0 | 1191 unique · `886520c001fffff` | hex-9's parent hex-8 |
| `parent_subzone` | object | string | 0.0 | 326 unique · `TSSZ06` | URA subzone parent (max-overlap) |
| `ped_path_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 228.6 (median 6.367) | Pedestrian-network density |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 2.4e+04 (median 668.6) | Footway + path + cycleway + steps length |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1248 (median 114.3) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2475) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 143 (median 0) | LTA traffic signals in hex |
| `walk_amenities_400m` | int64 | count | 0.0 | 0 → 2111 (median 5) | Place count within 400m walk |
| `walk_clinic_400m` | int64 | count | 0.0 | 0 → 321 (median 0) | Clinics within 400m walk |
| `walk_convenience_400m` | int64 | count | 0.0 | 0 → 58 (median 0) | Convenience stores within 400m walk |
| `walk_food_400m` | int64 | count | 0.0 | 0 → 491 (median 0) | Food places within 400m walk |
| `walk_hawker_400m` | int64 | count | 0.0 | 0 → 160 (median 0) | Hawkers within 400m walk |
| `walk_park_400m` | int64 | count | 0.0 | 0 → 10 (median 0) | Parks within 400m walk |
| `walk_school_400m` | int64 | count | 0.0 | 0 → 131 (median 0) | Schools within 400m walk |
| `walk_supermarket_400m` | int64 | count | 0.0 | 0 → 42 (median 0) | Supermarkets within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9587 (median 0.2351) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/subzone_all_features.parquet`

_389 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `accessibility_composite` | float64 | 0-1 | 0.0 | 0 → 0.893 (median 0.2845) | Composite access score across transit + walk + road reach |
| `archetype_dist` | float64 | z | 0.0 | 0.69 → 11.94 (median 2.313) | Distance to archetype centroid (typicality) |
| `archetype_id` | int64 | id | 0.0 | 0 → 7 (median 3) | k-means (K=8) urban archetype cluster id |
| `archetype_label` | object | category | 0.0 | 8 unique · `Mature_HDB` | Human label of the archetype cluster |
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 14.7 (median 2.513) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 30) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 205 (median 2) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 0 → 1.313e+04 (median 480.5) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0 → 5030 (median 375.8) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 0 → 3.748e+06 (median 2.278e+05) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.1835) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 647 (median 1) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 88 (median 1) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1998 (median 78) | Residential buildings |
| `bridge_length_m` | float64 | m | 0.0 | 0 → 7.355e+04 (median 2034) | Bridge segment length |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 104 (median 14) | Bus stops in hex |
| `bus_taps_in_am` | int64 |  | 0.0 | 0 → 4.356e+05 (median 2.063e+04) | Daily bus tap-ins in the am time window (LTA PV) |
| `bus_taps_in_midday` | int64 |  | 0.0 | 0 → 3.893e+05 (median 1.857e+04) | Daily bus tap-ins in the midday time window (LTA PV) |
| `bus_taps_in_night` | int64 |  | 0.0 | 0 → 1.317e+05 (median 4135) | Daily bus tap-ins in the night time window (LTA PV) |
| `bus_taps_in_offpeak` | int64 |  | 0.0 | 0 → 1.29e+06 (median 5.811e+04) | Daily bus tap-ins in the offpeak time window (LTA PV) |
| `bus_taps_in_pm` | int64 |  | 0.0 | 0 → 4.534e+05 (median 2.243e+04) | Daily bus tap-ins in the pm time window (LTA PV) |
| `bus_taps_in_total` | int64 |  | 0.0 | 0 → 2.7e+06 (median 1.272e+05) | Daily bus tap-ins in the total time window (LTA PV) |
| `bus_taps_out_am` | int64 |  | 0.0 | 0 → 4.797e+05 (median 2.363e+04) | Daily bus tap-outs in the am time window (LTA PV) |
| `bus_taps_out_midday` | int64 |  | 0.0 | 0 → 4.046e+05 (median 1.859e+04) | Daily bus tap-outs in the midday time window (LTA PV) |
| `bus_taps_out_night` | int64 |  | 0.0 | 0 → 1.192e+05 (median 5538) | Daily bus tap-outs in the night time window (LTA PV) |
| `bus_taps_out_offpeak` | int64 |  | 0.0 | 0 → 1.244e+06 (median 5.965e+04) | Daily bus tap-outs in the offpeak time window (LTA PV) |
| `bus_taps_out_pm` | int64 |  | 0.0 | 0 → 4.389e+05 (median 2.017e+04) | Daily bus tap-outs in the pm time window (LTA PV) |
| `bus_taps_out_total` | int64 |  | 0.0 | 0 → 2.686e+06 (median 1.289e+05) | Daily bus tap-outs in the total time window (LTA PV) |
| `carpark_count_avail` | int64 |  | 0.0 | 0 → 74 (median 3) | carpark count avail (see layer docs) |
| `carpark_lots_avail` | int64 |  | 0.0 | 0 → 1.45e+04 (median 383.5) | carpark lots avail (see layer docs) |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0.0161) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 4) | Tarjan bridge endpoints (network cut points) |
| `chas_clinic_count` | int64 |  | 0.0 | 0 → 42 (median 2) | chas clinic count (see layer docs) |
| `chas_clinics_within_500m` | int64 |  | 0.0 | 0 → 266 (median 14) | Count of chas clinics within 500m |
| `commercial_intensity` | float64 | 0-1 | 0.0 | 0.002 → 0.86 (median 0.119) | Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 2.076e+05 (median 9208) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 3.573e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `density_pressure` | float64 | 0-1 | 0.0 | 0 → 0.73 (median 0.0945) | Composite: population + buildings + low road space |
| `dist_bus_m` | float64 | m | 0.0 | 0 → 9542 (median 35.1) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0 → 9553 (median 31.3) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 9633 (median 97.94) | Centroid distance to nearest MRT/LRT station |
| `dominant_use` | object | categorical | 0.0 | 13 unique · `mixed_use` | Bucket with highest area share |
| `dyn_avg_speed_kmh` | float64 |  | 0.0 | 0 → 53.14 (median 27.56) | dyn avg speed kmh (see layer docs) |
| `est_built_far` | float64 | ratio | 0.0 | 0 → 7.347 (median 1.069) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 0 → 1.054e+07 (median 1.494e+06) | Sum of footprint × est_floors per building |
| `expressway_in_subzone` | object | bool | 17.2 | 2 unique · `True` | An expressway segment crosses the subzone |
| `expressway_severance` | object | bool | 17.2 | 2 unique · `False` | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `family_index` | float64 | 0-1 | 0.0 | 0 → 0.934 (median 0.3575) | Composite: children + schools + preschools + family amenities |
| `gap_bakery` | float64 |  | 0.0 | -1 → 1 (median 0.902) | Saturation gap for bakery: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_beauty_personal` | float64 |  | 0.0 | -1 → 1 (median 0.921) | Saturation gap for beauty personal: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_cafe_coffee` | float64 |  | 0.0 | -1 → 1 (median 0.904) | Saturation gap for cafe coffee: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_fast_food` | float64 |  | 0.0 | -1 → 1 (median 0.951) | Saturation gap for fast food: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_fitness_recreation` | float64 |  | 0.0 | -1 → 1 (median 0.8245) | Saturation gap for fitness recreation: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_hawker` | float64 |  | 0.0 | -1 → 1 (median 0.907) | Saturation gap for hawker: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_health_medical` | float64 |  | 0.0 | -1 → 1 (median 0.913) | Saturation gap for health medical: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_restaurant` | float64 |  | 0.0 | -1 → 1 (median 0.9355) | Saturation gap for restaurant: actual minus expected per-1k supply (positive = oversupplied) |
| `gap_supermarket` | float64 |  | 0.0 | -1 → 1 (median 0.8985) | Saturation gap for supermarket: actual minus expected per-1k supply (positive = oversupplied) |
| `gtfs_daily_departures` | int64 |  | 0.0 | 0 → 6.882e+04 (median 5972) | GTFS-derived transit service metric: daily departures (weekday schedule) |
| `gtfs_dep_am` | int64 |  | 0.0 | 0 → 7713 (median 689) | GTFS-derived transit service metric: dep am (weekday schedule) |
| `gtfs_dep_midday` | int64 |  | 0.0 | 0 → 1.122e+04 (median 1004) | GTFS-derived transit service metric: dep midday (weekday schedule) |
| `gtfs_dep_night` | int64 |  | 0.0 | 0 → 8405 (median 668.5) | GTFS-derived transit service metric: dep night (weekday schedule) |
| `gtfs_dep_pm` | int64 |  | 0.0 | 0 → 7682 (median 684.5) | GTFS-derived transit service metric: dep pm (weekday schedule) |
| `gtfs_headway_am_min` | float64 | min | 0.0 | 0.1 → 999 (median 1.1) | Best AM-peak headway (lowest minutes between buses) at any stop in hex |
| `gtfs_headway_midday_min` | float64 |  | 0.0 | 0.1 → 999 (median 1.2) | GTFS-derived transit service metric: headway midday min (weekday schedule) |
| `gtfs_headway_night_min` | float64 |  | 0.0 | 0.3 → 999 (median 3.3) | GTFS-derived transit service metric: headway night min (weekday schedule) |
| `gtfs_headway_pm_min` | float64 |  | 0.0 | 0.1 → 999 (median 1.2) | GTFS-derived transit service metric: headway pm min (weekday schedule) |
| `gtfs_routes_served` | int64 |  | 0.0 | 0 → 560 (median 61) | GTFS-derived transit service metric: routes served (weekday schedule) |
| `gtfs_stops_with_service` | int64 |  | 0.0 | 0 → 88 (median 14) | GTFS-derived transit service metric: stops with service (weekday schedule) |
| `has_interchange` | object | bool | 17.2 | 2 unique · `False` | Subzone contains an interchange station |
| `has_mrt` | object | bool | 17.2 | 2 unique · `False` | Subzone contains at least one MRT/LRT station |
| `hawker_centre_count` | int64 |  | 0.0 | 0 → 5 (median 0) | hawker centre count (see layer docs) |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 416 (median 11) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 3.249e+04 (median 922.6) | Total dwelling units across HDB blocks |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 42 (median 1) | Authoritative HDB multi-storey carparks |
| `hdb_resale_12m_median_price` | float64 |  | 0.0 | 0 → 9.8e+05 (median 5.989e+05) | hdb resale 12m median price (see layer docs) |
| `hdb_resale_4r_median_price` | float64 |  | 0.0 | 0 → 8.35e+05 (median 5e+05) | hdb resale 4r median price (see layer docs) |
| `hdb_resale_4r_median_psm` | float64 |  | 0.0 | 0 → 9175 (median 5167) | hdb resale 4r median psm (see layer docs) |
| `hdb_resale_avg_lease_remaining_yrs` | float64 |  | 0.0 | 0 → 89.87 (median 68.16) | hdb resale avg lease remaining yrs (see layer docs) |
| `hdb_resale_in_town` | int64 |  | 0.0 | 0 → 1 (median 1) | hdb resale in town (see layer docs) |
| `hdb_resale_median_price` | float64 |  | 0.0 | 0 → 7.6e+05 (median 4.88e+05) | hdb resale median price (see layer docs) |
| `hdb_resale_median_psm` | float64 |  | 0.0 | 0 → 7629 (median 5166) | hdb resale median psm (see layer docs) |
| `hdb_resale_txns_12m` | float64 |  | 0.0 | 0 → 1948 (median 806) | hdb resale txns 12m (see layer docs) |
| `hdb_resale_txns_total` | float64 |  | 0.0 | 0 → 1.852e+04 (median 6927) | hdb resale txns total (see layer docs) |
| `in_primary_school_zone` | int64 | bool | 0.0 | 0 → 1 (median 0) | Cell intersects a primary-school zone |
| `in_silver_zone` | int64 | bool | 0.0 | 0 → 1 (median 0) | Cell intersects an elderly-priority Silver Zone |
| `jam_pct` | float64 |  | 0.0 | 0 → 60.72 (median 19.9) | jam pct (see layer docs) |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 50.21) | Lane-km per km² (lane count × length / area) |
| `livability_index` | float64 | 0-1 | 0.0 | 0.045 → 0.956 (median 0.7315) | Composite: walkability + green + amenities + transit |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6194 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9114 (median 0.0125) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6369 (median 0.0008) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.79 (median 0.0212) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0.021 → 2.115 (median 1.424) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.371 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1804 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9115 (median 0.0138) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3615 (median 0.009) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9969 (median 0.0483) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 22 → 7026 (median 227.5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9576 (median 0.0127) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8106 (median 0.3315) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 1.19e+05 → 6.798e+07 (median 1.294e+06) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8373 (median 0.1926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7739 (median 0.0027) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7043 (median 0.012) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 3.5) | Max GPR within hex |
| `max_transit_score` | float64 | 0-1 | 0.0 | 0 → 0.9879 (median 0.7723) | Best hex8 transit score within subzone |
| `mg_avg_anchor_strength` | float64 |  | 0.0 | 0 → 632.8 (median 12.86) | Magnet model: strength of the biggest avg anchor place nearby |
| `mg_avg_competitors_400m` | float64 | count | 0.0 | 0 → 124.4 (median 6.066) | Magnet model: mean same-category competitor count within 400 m across categories |
| `mg_avg_walk_dist_mrt_m` | float64 | m | 0.0 | 143 → 9999 (median 1193) | Magnet model: mean walk distance to MRT across category micrographs |
| `mg_bakery_anchor_strength` | float64 |  | 0.0 | 0 → 1304 (median 14.25) | Magnet model: strength of the biggest bakery anchor place nearby |
| `mg_bakery_pressure_400m` | float64 |  | 0.0 | 0 → 41.33 (median 2.667) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bakery |
| `mg_bakery_support_400m` | float64 |  | 0.0 | 0 → 212.4 (median 9.333) | Magnet model: complementary-category support density within 400 m for bakery (demand context, not supply) |
| `mg_bar_nightlife_anchor_strength` | float64 |  | 0.0 | 0 → 246.5 (median 0) | Magnet model: strength of the biggest bar nightlife anchor place nearby |
| `mg_bar_nightlife_pressure_400m` | float64 |  | 0.0 | 0 → 27.03 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for bar nightlife |
| `mg_bar_nightlife_support_400m` | float64 |  | 0.0 | 0 → 106.2 (median 0) | Magnet model: complementary-category support density within 400 m for bar nightlife (demand context, not supply) |
| `mg_beauty_personal_anchor_strength` | float64 |  | 0.0 | 0 → 913.2 (median 17.04) | Magnet model: strength of the biggest beauty personal anchor place nearby |
| `mg_beauty_personal_pressure_400m` | float64 |  | 0.0 | 0 → 105.9 (median 2.966) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for beauty personal |
| `mg_beauty_personal_support_400m` | float64 |  | 0.0 | 0 → 199.4 (median 8.265) | Magnet model: complementary-category support density within 400 m for beauty personal (demand context, not supply) |
| `mg_business_office_anchor_strength` | float64 |  | 0.0 | 0 → 372 (median 7.261) | Magnet model: strength of the biggest business office anchor place nearby |
| `mg_business_office_pressure_400m` | float64 |  | 0.0 | 0 → 249.5 (median 3.893) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for business office |
| `mg_business_office_support_400m` | float64 |  | 0.0 | 0 → 310.4 (median 11.46) | Magnet model: complementary-category support density within 400 m for business office (demand context, not supply) |
| `mg_cafe_coffee_anchor_strength` | float64 |  | 0.0 | 0 → 1119 (median 28.54) | Magnet model: strength of the biggest cafe coffee anchor place nearby |
| `mg_cafe_coffee_pressure_400m` | float64 |  | 0.0 | 0 → 38.07 (median 3.257) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for cafe coffee |
| `mg_cafe_coffee_support_400m` | float64 |  | 0.0 | 0 → 178.3 (median 11.29) | Magnet model: complementary-category support density within 400 m for cafe coffee (demand context, not supply) |
| `mg_convenience_anchor_strength` | float64 |  | 0.0 | 0 → 81.3 (median 7.303) | Magnet model: strength of the biggest convenience anchor place nearby |
| `mg_convenience_pressure_400m` | float64 |  | 0.0 | 0 → 32.29 (median 3.309) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for convenience |
| `mg_convenience_support_400m` | float64 |  | 0.0 | 0 → 29.96 (median 6.694) | Magnet model: complementary-category support density within 400 m for convenience (demand context, not supply) |
| `mg_education_anchor_strength` | float64 |  | 0.0 | 0 → 39.43 (median 0.426) | Magnet model: strength of the biggest education anchor place nearby |
| `mg_education_pressure_400m` | float64 |  | 0.0 | 0 → 56.51 (median 2.5) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for education |
| `mg_education_support_400m` | float64 |  | 0.0 | 0 → 43.8 (median 4.798) | Magnet model: complementary-category support density within 400 m for education (demand context, not supply) |
| `mg_entertainment_culture_anchor_strength` | float64 |  | 0.0 | 0 → 1044 (median 2.511) | Magnet model: strength of the biggest entertainment culture anchor place nearby |
| `mg_entertainment_culture_pressure_400m` | float64 |  | 0.0 | 0 → 20.38 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for entertainment culture |
| `mg_entertainment_culture_support_400m` | float64 |  | 0.0 | 0 → 113 (median 0.429) | Magnet model: complementary-category support density within 400 m for entertainment culture (demand context, not supply) |
| `mg_fast_food_anchor_strength` | float64 |  | 0.0 | 0 → 1152 (median 7.787) | Magnet model: strength of the biggest fast food anchor place nearby |
| `mg_fast_food_pressure_400m` | float64 |  | 0.0 | 0 → 112.5 (median 4.5) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fast food |
| `mg_fast_food_support_400m` | float64 |  | 0.0 | 0 → 144.5 (median 6.75) | Magnet model: complementary-category support density within 400 m for fast food (demand context, not supply) |
| `mg_fitness_recreation_anchor_strength` | float64 |  | 0.0 | 0 → 921.3 (median 10.9) | Magnet model: strength of the biggest fitness recreation anchor place nearby |
| `mg_fitness_recreation_pressure_400m` | float64 |  | 0.0 | 0 → 25.75 (median 0.667) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for fitness recreation |
| `mg_fitness_recreation_support_400m` | float64 |  | 0.0 | 0 → 153.8 (median 6) | Magnet model: complementary-category support density within 400 m for fitness recreation (demand context, not supply) |
| `mg_government_public_anchor_strength` | float64 |  | 0.0 | 0 → 70.12 (median 1.726) | Magnet model: strength of the biggest government public anchor place nearby |
| `mg_government_public_pressure_400m` | float64 |  | 0.0 | 0 → 11.63 (median 0.25) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for government public |
| `mg_government_public_support_400m` | float64 |  | 0.0 | 0 → 194.2 (median 5.062) | Magnet model: complementary-category support density within 400 m for government public (demand context, not supply) |
| `mg_hawker_anchor_strength` | float64 |  | 0.0 | 0 → 69.59 (median 2.913) | Magnet model: strength of the biggest hawker anchor place nearby |
| `mg_hawker_pressure_400m` | float64 |  | 0.0 | 0 → 122.9 (median 7.752) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hawker |
| `mg_hawker_support_400m` | float64 |  | 0.0 | 0 → 42.13 (median 6.986) | Magnet model: complementary-category support density within 400 m for hawker (demand context, not supply) |
| `mg_health_medical_anchor_strength` | float64 |  | 0.0 | 0 → 78.53 (median 4.726) | Magnet model: strength of the biggest health medical anchor place nearby |
| `mg_health_medical_pressure_400m` | float64 |  | 0.0 | 0 → 136.2 (median 2.151) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for health medical |
| `mg_health_medical_support_400m` | float64 |  | 0.0 | 0 → 157.5 (median 6.455) | Magnet model: complementary-category support density within 400 m for health medical (demand context, not supply) |
| `mg_hotel_hospitality_anchor_strength` | float64 |  | 0.0 | 0 → 1054 (median 0) | Magnet model: strength of the biggest hotel hospitality anchor place nearby |
| `mg_hotel_hospitality_pressure_400m` | float64 |  | 0.0 | 0 → 42.37 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for hotel hospitality |
| `mg_hotel_hospitality_support_400m` | float64 |  | 0.0 | 0 → 120.8 (median 0) | Magnet model: complementary-category support density within 400 m for hotel hospitality (demand context, not supply) |
| `mg_industrial_mfg_anchor_strength` | float64 |  | 0.0 | 0 → 217.8 (median 5.143) | Magnet model: strength of the biggest industrial mfg anchor place nearby |
| `mg_industrial_mfg_pressure_400m` | float64 |  | 0.0 | 0 → 82.28 (median 2.458) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for industrial mfg |
| `mg_industrial_mfg_support_400m` | float64 |  | 0.0 | 0 → 439 (median 6.428) | Magnet model: complementary-category support density within 400 m for industrial mfg (demand context, not supply) |
| `mg_other_uncategorized_anchor_strength` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: strength of the biggest other uncategorized anchor place nearby |
| `mg_other_uncategorized_pressure_400m` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for other uncategorized |
| `mg_other_uncategorized_support_400m` | float64 |  | 0.0 | 0 → 0 (median 0) | Magnet model: complementary-category support density within 400 m for other uncategorized (demand context, not supply) |
| `mg_park_open_anchor_strength` | float64 |  | 0.0 | 0 → 13.26 (median 0.22) | Magnet model: strength of the biggest park open anchor place nearby |
| `mg_park_open_pressure_400m` | float64 |  | 0.0 | 0 → 7.364 (median 0.718) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for park open |
| `mg_park_open_support_400m` | float64 |  | 0.0 | 0 → 81.5 (median 3.778) | Magnet model: complementary-category support density within 400 m for park open (demand context, not supply) |
| `mg_religious_worship_anchor_strength` | float64 |  | 0.0 | 0 → 23.57 (median 0) | Magnet model: strength of the biggest religious worship anchor place nearby |
| `mg_religious_worship_pressure_400m` | float64 |  | 0.0 | 0 → 13.7 (median 0) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for religious worship |
| `mg_religious_worship_support_400m` | float64 |  | 0.0 | 0 → 19.4 (median 1) | Magnet model: complementary-category support density within 400 m for religious worship (demand context, not supply) |
| `mg_residential_anchor_strength` | float64 |  | 0.0 | 0 → 748.8 (median 8.324) | Magnet model: strength of the biggest residential anchor place nearby |
| `mg_residential_pressure_400m` | float64 |  | 0.0 | 0 → 16.49 (median 3.232) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for residential |
| `mg_residential_support_400m` | float64 |  | 0.0 | 0 → 48.67 (median 4.186) | Magnet model: complementary-category support density within 400 m for residential (demand context, not supply) |
| `mg_restaurant_anchor_strength` | float64 |  | 0.0 | 0 → 1059 (median 24.71) | Magnet model: strength of the biggest restaurant anchor place nearby |
| `mg_restaurant_pressure_400m` | float64 |  | 0.0 | 0 → 144.5 (median 11.18) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for restaurant |
| `mg_restaurant_support_400m` | float64 |  | 0.0 | 0 → 108.8 (median 4.976) | Magnet model: complementary-category support density within 400 m for restaurant (demand context, not supply) |
| `mg_services_anchor_strength` | float64 |  | 0.0 | 0 → 1057 (median 20.72) | Magnet model: strength of the biggest services anchor place nearby |
| `mg_services_pressure_400m` | float64 |  | 0.0 | 0 → 187.3 (median 3.329) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for services |
| `mg_services_support_400m` | float64 |  | 0.0 | 0 → 266.5 (median 10.22) | Magnet model: complementary-category support density within 400 m for services (demand context, not supply) |
| `mg_shopping_retail_anchor_strength` | float64 |  | 0.0 | 0 → 1176 (median 24.73) | Magnet model: strength of the biggest shopping retail anchor place nearby |
| `mg_shopping_retail_pressure_400m` | float64 |  | 0.0 | 0 → 115.8 (median 6.051) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for shopping retail |
| `mg_shopping_retail_support_400m` | float64 |  | 0.0 | 0 → 186.2 (median 9.305) | Magnet model: complementary-category support density within 400 m for shopping retail (demand context, not supply) |
| `mg_supermarket_anchor_strength` | float64 |  | 0.0 | 0 → 25.93 (median 0) | Magnet model: strength of the biggest supermarket anchor place nearby |
| `mg_supermarket_pressure_400m` | float64 |  | 0.0 | 0 → 39.07 (median 3) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for supermarket |
| `mg_supermarket_support_400m` | float64 |  | 0.0 | 0 → 169 (median 9.29) | Magnet model: complementary-category support density within 400 m for supermarket (demand context, not supply) |
| `mg_transportation_anchor_strength` | float64 |  | 0.0 | 0 → 962.6 (median 12.68) | Magnet model: strength of the biggest transportation anchor place nearby |
| `mg_transportation_pressure_400m` | float64 |  | 0.0 | 0 → 23.16 (median 2.814) | Magnet model: 400 m distance-decayed SAME-category competitive pressure for transportation |
| `mg_transportation_support_400m` | float64 |  | 0.0 | 0 → 248.5 (median 6.724) | Magnet model: complementary-category support density within 400 m for transportation (demand context, not supply) |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 33 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 6 (median 0) | MRT/LRT stations in hex |
| `n_hex8` | float64 | count | 0.0 | 0 → 121 (median 1.5) | Number of hex8 children (bookkeeping) |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 1865 (median 65) | Number of buildings with floors ≥ 10 |
| `n_interchanges` | float64 | count | 0.0 | 0 → 2 (median 0) | Interchange stations in subzone |
| `nearest_chas_clinic_dist_m` | float64 |  | 0.0 | 1.4 → 9742 (median 140.2) | Distance to nearest chas clinic |
| `nearest_hawker_centre_dist_m` | float64 |  | 0.0 | 17.8 → 9842 (median 423.9) | Distance to nearest hawker centre |
| `nearest_preschool_dist_m` | float64 |  | 0.0 | 1.3 → 9696 (median 92.65) | Distance to nearest preschool |
| `nearest_primary_school_dist_m` | float64 |  | 0.0 | 9.5 → 1.126e+04 (median 367.9) | Distance to nearest primary school |
| `nearest_school_dist_m` | float64 |  | 0.0 | 4.5 → 1.055e+04 (median 285.1) | Distance to nearest school |
| `nearest_tourist_dist_m` | float64 |  | 0.0 | 12.7 → 9975 (median 1294) | Distance to nearest tourist |
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 58.86) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 63.89) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 8.999) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 165 (median 30.88) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 1.61 (median 0.0463) | nl_2024 / pop_resident (commercial vs residential signal) |
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2863) | Non-resident share of total pop |
| `osm_amenities_count` | int64 | count | 0.0 | 0 → 745 (median 57) | OSM amenity-tagged POIs in cell (independent ground truth) |
| `osm_leisure_count` | int64 | count | 0.0 | 0 → 407 (median 23) | OSM leisure-tagged POIs in cell |
| `osm_shops_count` | int64 | count | 0.0 | 0 → 301 (median 10) | OSM shop-tagged POIs in cell — independent retail frontage |
| `osm_tourism_count` | int64 | count | 0.0 | 0 → 342 (median 1) | OSM tourism-tagged POIs in cell |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 61 (median 6) | OSM amenity=parking points |
| `pc2_branded_count` | int64 |  | 0.0 | 0 → 405 (median 26.5) | Fine-taxonomy place metric: branded count |
| `pc2_cat_biz_office_count` | int64 |  | 0.0 | 0 → 224 (median 4) | Place count in cell: biz office (55-cat fine taxonomy) |
| `pc2_cat_civic_community_count` | int64 |  | 0.0 | 0 → 16 (median 1) | Place count in cell: civic community (55-cat fine taxonomy) |
| `pc2_cat_civic_government_count` | int64 |  | 0.0 | 0 → 35 (median 2) | Place count in cell: civic government (55-cat fine taxonomy) |
| `pc2_cat_civic_nonprofit_count` | int64 |  | 0.0 | 0 → 136 (median 4.5) | Place count in cell: civic nonprofit (55-cat fine taxonomy) |
| `pc2_cat_civic_religious_count` | int64 |  | 0.0 | 0 → 91 (median 2) | Place count in cell: civic religious (55-cat fine taxonomy) |
| `pc2_cat_edu_preschool_count` | int64 |  | 0.0 | 0 → 82 (median 4) | Place count in cell: edu preschool (55-cat fine taxonomy) |
| `pc2_cat_edu_primary_secondary_count` | int64 |  | 0.0 | 0 → 96 (median 2) | Place count in cell: edu primary secondary (55-cat fine taxonomy) |
| `pc2_cat_edu_specialty_count` | int64 |  | 0.0 | 0 → 12 (median 0) | Place count in cell: edu specialty (55-cat fine taxonomy) |
| `pc2_cat_edu_tertiary_count` | int64 |  | 0.0 | 0 → 30 (median 0) | Place count in cell: edu tertiary (55-cat fine taxonomy) |
| `pc2_cat_edu_tuition_count` | int64 |  | 0.0 | 0 → 138 (median 9) | Place count in cell: edu tuition (55-cat fine taxonomy) |
| `pc2_cat_food_bakery_count` | int64 |  | 0.0 | 0 → 56 (median 3) | Place count in cell: food bakery (55-cat fine taxonomy) |
| `pc2_cat_food_bar_count` | int64 |  | 0.0 | 0 → 63 (median 1) | Place count in cell: food bar (55-cat fine taxonomy) |
| `pc2_cat_food_cafe_count` | int64 |  | 0.0 | 0 → 115 (median 10) | Place count in cell: food cafe (55-cat fine taxonomy) |
| `pc2_cat_food_caterer_count` | int64 |  | 0.0 | 0 → 21 (median 0) | Place count in cell: food caterer (55-cat fine taxonomy) |
| `pc2_cat_food_dessert_count` | int64 |  | 0.0 | 0 → 57 (median 3) | Place count in cell: food dessert (55-cat fine taxonomy) |
| `pc2_cat_food_fast_food_count` | int64 |  | 0.0 | 0 → 27 (median 1) | Place count in cell: food fast food (55-cat fine taxonomy) |
| `pc2_cat_food_hawker_count` | int64 |  | 0.0 | 0 → 201 (median 10) | Place count in cell: food hawker (55-cat fine taxonomy) |
| `pc2_cat_food_restaurant_count` | int64 |  | 0.0 | 0 → 400 (median 16.5) | Place count in cell: food restaurant (55-cat fine taxonomy) |
| `pc2_cat_health_clinic_count` | int64 |  | 0.0 | 0 → 110 (median 4) | Place count in cell: health clinic (55-cat fine taxonomy) |
| `pc2_cat_health_hospital_count` | int64 |  | 0.0 | 0 → 50 (median 0) | Place count in cell: health hospital (55-cat fine taxonomy) |
| `pc2_cat_health_pharmacy_count` | int64 |  | 0.0 | 0 → 26 (median 1) | Place count in cell: health pharmacy (55-cat fine taxonomy) |
| `pc2_cat_health_specialist_count` | int64 |  | 0.0 | 0 → 148 (median 2.5) | Place count in cell: health specialist (55-cat fine taxonomy) |
| `pc2_cat_health_tcm_count` | int64 |  | 0.0 | 0 → 16 (median 0) | Place count in cell: health tcm (55-cat fine taxonomy) |
| `pc2_cat_leisure_entertainment_count` | int64 |  | 0.0 | 0 → 25 (median 1) | Place count in cell: leisure entertainment (55-cat fine taxonomy) |
| `pc2_cat_leisure_park_count` | int64 |  | 0.0 | 0 → 80 (median 9) | Place count in cell: leisure park (55-cat fine taxonomy) |
| `pc2_cat_leisure_tourist_count` | int64 |  | 0.0 | 0 → 62 (median 1) | Place count in cell: leisure tourist (55-cat fine taxonomy) |
| `pc2_cat_other_count` | int64 |  | 0.0 | 0 → 1114 (median 81) | Place count in cell: other (55-cat fine taxonomy) |
| `pc2_cat_res_aged_care_count` | int64 |  | 0.0 | 0 → 12 (median 0) | Place count in cell: res aged care (55-cat fine taxonomy) |
| `pc2_cat_res_hdb_count` | int64 |  | 0.0 | 0 → 204 (median 4) | Place count in cell: res hdb (55-cat fine taxonomy) |
| `pc2_cat_res_private_count` | int64 |  | 0.0 | 0 → 197 (median 7) | Place count in cell: res private (55-cat fine taxonomy) |
| `pc2_cat_retail_apparel_count` | int64 |  | 0.0 | 0 → 199 (median 2) | Place count in cell: retail apparel (55-cat fine taxonomy) |
| `pc2_cat_retail_convenience_count` | int64 |  | 0.0 | 0 → 136 (median 11) | Place count in cell: retail convenience (55-cat fine taxonomy) |
| `pc2_cat_retail_electronics_count` | int64 |  | 0.0 | 0 → 67 (median 1) | Place count in cell: retail electronics (55-cat fine taxonomy) |
| `pc2_cat_retail_furniture_home_count` | int64 |  | 0.0 | 0 → 151 (median 4) | Place count in cell: retail furniture home (55-cat fine taxonomy) |
| `pc2_cat_retail_general_count` | int64 |  | 0.0 | 0 → 119 (median 8) | Place count in cell: retail general (55-cat fine taxonomy) |
| `pc2_cat_retail_jewelry_cosmetics_count` | int64 |  | 0.0 | 0 → 203 (median 1) | Place count in cell: retail jewelry cosmetics (55-cat fine taxonomy) |
| `pc2_cat_retail_mall_count` | int64 |  | 0.0 | 0 → 23 (median 1) | Place count in cell: retail mall (55-cat fine taxonomy) |
| `pc2_cat_retail_supermarket_count` | int64 |  | 0.0 | 0 → 55 (median 4) | Place count in cell: retail supermarket (55-cat fine taxonomy) |
| `pc2_cat_service_automotive_count` | int64 |  | 0.0 | 0 → 508 (median 2) | Place count in cell: service automotive (55-cat fine taxonomy) |
| `pc2_cat_service_beauty_count` | int64 |  | 0.0 | 0 → 265 (median 11) | Place count in cell: service beauty (55-cat fine taxonomy) |
| `pc2_cat_service_cleaning_repair_count` | int64 |  | 0.0 | 0 → 66 (median 2) | Place count in cell: service cleaning repair (55-cat fine taxonomy) |
| `pc2_cat_service_consulting_count` | int64 |  | 0.0 | 0 → 751 (median 14) | Place count in cell: service consulting (55-cat fine taxonomy) |
| `pc2_cat_service_fitness_count` | int64 |  | 0.0 | 0 → 65 (median 7) | Place count in cell: service fitness (55-cat fine taxonomy) |
| `pc2_cat_service_legal_finance_count` | int64 |  | 0.0 | 0 → 230 (median 2) | Place count in cell: service legal finance (55-cat fine taxonomy) |
| `pc2_cat_service_logistics_count` | int64 |  | 0.0 | 0 → 573 (median 11) | Place count in cell: service logistics (55-cat fine taxonomy) |
| `pc2_cat_service_other_count` | int64 |  | 0.0 | 0 → 584 (median 9) | Place count in cell: service other (55-cat fine taxonomy) |
| `pc2_cat_service_pet_count` | int64 |  | 0.0 | 0 → 13 (median 0) | Place count in cell: service pet (55-cat fine taxonomy) |
| `pc2_cat_service_real_estate_count` | int64 |  | 0.0 | 0 → 112 (median 1) | Place count in cell: service real estate (55-cat fine taxonomy) |
| `pc2_cat_transport_air_count` | int64 |  | 0.0 | 0 → 26 (median 0) | Place count in cell: transport air (55-cat fine taxonomy) |
| `pc2_cat_transport_bus_count` | int64 |  | 0.0 | 0 → 62 (median 9) | Place count in cell: transport bus (55-cat fine taxonomy) |
| `pc2_cat_transport_ev_count` | int64 |  | 0.0 | 0 → 58 (median 5) | Place count in cell: transport ev (55-cat fine taxonomy) |
| `pc2_cat_transport_mrt_count` | int64 |  | 0.0 | 0 → 11 (median 1) | Place count in cell: transport mrt (55-cat fine taxonomy) |
| `pc2_cat_transport_other_count` | int64 |  | 0.0 | 0 → 13 (median 0) | Place count in cell: transport other (55-cat fine taxonomy) |
| `pc2_cat_transport_parking_count` | int64 |  | 0.0 | 0 → 64 (median 6) | Place count in cell: transport parking (55-cat fine taxonomy) |
| `pc2_cat_unmapped_count` | int64 |  | 0.0 | 0 → 84 (median 0.5) | Place count in cell: unmapped (55-cat fine taxonomy) |
| `pc2_dominant_category` | object |  | 0.0 | 13 unique · `other` | Fine-taxonomy place metric: dominant category |
| `pc2_total` | int64 |  | 0.0 | 1 → 4639 (median 418) | Fine-taxonomy place metric: total |
| `pc2_unbranded_count` | int64 |  | 0.0 | 1 → 4571 (median 393) | Fine-taxonomy place metric: unbranded count |
| `pc_avg_rating` | float64 | stars | 0.0 | 0 → 4.87 (median 4.42) | Mean rating of rated places — quality proxy |
| `pc_cat_bakery` | int64 |  | 0.0 | 0 → 59 (median 3) | Place count in cell: bakery category (24-cat taxonomy) |
| `pc_cat_bar_nightlife` | int64 |  | 0.0 | 0 → 69 (median 1) | Place count in cell: bar nightlife category (24-cat taxonomy) |
| `pc_cat_beauty_personal` | int64 |  | 0.0 | 0 → 289 (median 11.5) | Place count in cell: beauty personal category (24-cat taxonomy) |
| `pc_cat_business_office` | int64 |  | 0.0 | 0 → 1144 (median 22) | Place count in cell: business office category (24-cat taxonomy) |
| `pc_cat_cafe_coffee` | int64 |  | 0.0 | 0 → 164 (median 13) | Place count in cell: cafe coffee category (24-cat taxonomy) |
| `pc_cat_convenience` | int64 |  | 0.0 | 0 → 144 (median 12) | Place count in cell: convenience category (24-cat taxonomy) |
| `pc_cat_education` | int64 |  | 0.0 | 0 → 263 (median 22.5) | Place count in cell: education category (24-cat taxonomy) |
| `pc_cat_entertainment_culture` | int64 |  | 0.0 | 0 → 75 (median 2) | Place count in cell: entertainment culture category (24-cat taxonomy) |
| `pc_cat_fast_food` | int64 |  | 0.0 | 0 → 27 (median 1) | Place count in cell: fast food category (24-cat taxonomy) |
| `pc_cat_fitness_recreation` | int64 |  | 0.0 | 0 → 68 (median 7) | Place count in cell: fitness recreation category (24-cat taxonomy) |
| `pc_cat_government_public` | int64 |  | 0.0 | 0 → 49 (median 4) | Place count in cell: government public category (24-cat taxonomy) |
| `pc_cat_hawker` | int64 |  | 0.0 | 0 → 201 (median 10) | Place count in cell: hawker category (24-cat taxonomy) |
| `pc_cat_health_medical` | int64 |  | 0.0 | 0 → 347 (median 10) | Place count in cell: health medical category (24-cat taxonomy) |
| `pc_cat_hotel_hospitality` | int64 |  | 0.0 | 0 → 87 (median 1) | Place count in cell: hotel hospitality category (24-cat taxonomy) |
| `pc_cat_industrial_mfg` | int64 |  | 0.0 | 0 → 873 (median 16) | Place count in cell: industrial mfg category (24-cat taxonomy) |
| `pc_cat_other_uncategorized` | int64 |  | 0.0 | 0 → 466 (median 36.5) | Place count in cell: other uncategorized category (24-cat taxonomy) |
| `pc_cat_park_open` | int64 |  | 0.0 | 0 → 88 (median 10) | Place count in cell: park open category (24-cat taxonomy) |
| `pc_cat_religious_worship` | int64 |  | 0.0 | 0 → 111 (median 2) | Place count in cell: religious worship category (24-cat taxonomy) |
| `pc_cat_residential` | int64 |  | 0.0 | 0 → 514 (median 24.5) | Place count in cell: residential category (24-cat taxonomy) |
| `pc_cat_restaurant` | int64 |  | 0.0 | 0 → 428 (median 18) | Place count in cell: restaurant category (24-cat taxonomy) |
| `pc_cat_services` | int64 |  | 0.0 | 0 → 1032 (median 31.5) | Place count in cell: services category (24-cat taxonomy) |
| `pc_cat_shopping_retail` | int64 |  | 0.0 | 0 → 572 (median 22) | Place count in cell: shopping retail category (24-cat taxonomy) |
| `pc_cat_supermarket` | int64 |  | 0.0 | 0 → 60 (median 5) | Place count in cell: supermarket category (24-cat taxonomy) |
| `pc_cat_transportation` | int64 |  | 0.0 | 0 → 239 (median 30) | Place count in cell: transportation category (24-cat taxonomy) |
| `pc_diversity` | float64 | 0-1 | 0.0 | -0 → 2.897 (median 2.632) | Category entropy of the place mix — high = mixed-use |
| `pc_dominant_category` | object | category | 0.0 | 15 unique · `beauty_personal` | Most common place category in cell |
| `pc_long_tail` | int64 | count | 0.0 | 1 → 2962 (median 235) | Places with few/no reviews — independent long-tail share base |
| `pc_magnets` | int64 | count | 0.0 | 0 → 747 (median 34.5) | High-draw anchor places (malls, hubs, 30+ review demand magnets) |
| `pc_total` | int64 | count | 0.0 | 1 → 4639 (median 418) | Total mapped places (POIs) in cell — overall point-of-interest density |
| `pc_total_reviews` | int64 | count | 0.0 | 0 → 6.093e+05 (median 2.445e+04) | Sum of review counts — popularity/footfall proxy |
| `pc_unique_brands` | int64 | count | 0.0 | 0 → 159 (median 20) | Distinct retail/F&B brands present — chain richness |
| `pc_with_rating` | int64 | count | 0.0 | 0 → 2345 (median 242) | Places carrying a Google rating |
| `ped_countdown` | int64 |  | 0.0 | 0 → 64 (median 0) | Road-network metric: ped countdown |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 3.072e+05 (median 3.284e+04) | Footway + path + cycleway + steps length |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1.531e+04 (median 755) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 8.245e+04 (median 3544) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2.643e+04 (median 1079) | Population age 65+ |
| `pop_dorm` | float64 | persons | 0.0 | 0 → 4.271e+04 (median 0) | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.125e+05 (median 2053) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.5671) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 3.042e+04 (median 1215) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 7.171e+04 (median 3213) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.242e+05 (median 5404) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 1.399e+05 (median 1.267e+04) | Total population (residents + non-residents) |
| `preschool_count` | int64 |  | 0.0 | 0 → 68 (median 4) | preschool count (see layer docs) |
| `preschools_within_400m` | int64 |  | 0.0 | 0 → 289 (median 18) | Count of preschools within 400m |
| `primary_school_zone_count` | int64 | count | 0.0 | 0 → 17 (median 0) | Primary-school zones overlapping cell |
| `primary_schools_within_1km` | float64 |  | 0.0 | 0 → 6.18 (median 1.06) | Count of primary schools within 1km |
| `primary_schools_within_2km` | float64 |  | 0.0 | 0 → 17.82 (median 5) | Count of primary schools within 2km |
| `pull_airport` | float64 |  | 0.0 | 0.014 → 0.949 (median 0.2795) | Gravity pull toward airport (distance-decayed attraction) |
| `pull_cbd` | float64 |  | 0.0 | 0.009 → 1 (median 0.186) | Gravity pull toward cbd (distance-decayed attraction) |
| `pull_composite` | float64 |  | 0.0 | 0.005 → 0.762 (median 0.2555) | Gravity pull toward composite (distance-decayed attraction) |
| `pull_hospital` | float64 |  | 0.0 | 0.004 → 0.986 (median 0.2185) | Gravity pull toward hospital (distance-decayed attraction) |
| `pull_mall` | float64 |  | 0.0 | 0.001 → 0.995 (median 0.119) | Gravity pull toward mall (distance-decayed attraction) |
| `pull_mrt_interchange` | float64 |  | 0.0 | 0 → 0.976 (median 0.1515) | Gravity pull toward mrt interchange (distance-decayed attraction) |
| `pull_school_premium` | float64 |  | 0.0 | 0.003 → 0.961 (median 0.378) | Gravity pull toward school premium (distance-decayed attraction) |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 2.05e+04 (median 1344) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 264.1 (median 48.75) | Road km per km² |
| `road_intersection_count_total` | float64 |  | 0.0 | 0 → 5204 (median 350.5) | Road-network metric: road intersection count total |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1538 (median 255.7) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 1.062e+06 (median 6.254e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 17.2 | 8 unique · `motorway` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.7701 (median 0.4667) | Pedestrian-only roads as fraction of total |
| `sat_bakery_per_1k` | float64 |  | 0.0 | 0 → 39.18 (median 0.282) | Supply saturation: bakery outlets per 1,000 residents |
| `sat_beauty_personal_per_1k` | float64 |  | 0.0 | 0 → 265.8 (median 1.044) | Supply saturation: beauty personal outlets per 1,000 residents |
| `sat_cafe_coffee_per_1k` | float64 |  | 0.0 | 0 → 171.7 (median 1.067) | Supply saturation: cafe coffee outlets per 1,000 residents |
| `sat_fast_food_per_1k` | float64 |  | 0.0 | 0 → 34.52 (median 0.0805) | Supply saturation: fast food outlets per 1,000 residents |
| `sat_fitness_recreation_per_1k` | float64 |  | 0.0 | 0 → 54.05 (median 0.6465) | Supply saturation: fitness recreation outlets per 1,000 residents |
| `sat_hawker_per_1k` | float64 |  | 0.0 | 0 → 187.6 (median 0.805) | Supply saturation: hawker outlets per 1,000 residents |
| `sat_health_medical_per_1k` | float64 |  | 0.0 | 0 → 194.5 (median 0.931) | Supply saturation: health medical outlets per 1,000 residents |
| `sat_restaurant_per_1k` | float64 |  | 0.0 | 0 → 399.7 (median 1.496) | Supply saturation: restaurant outlets per 1,000 residents |
| `sat_supermarket_per_1k` | float64 |  | 0.0 | 0 → 73.27 (median 0.4445) | Supply saturation: supermarket outlets per 1,000 residents |
| `school_count_jc` | int64 |  | 0.0 | 0 → 2 (median 0) | school count jc (see layer docs) |
| `school_count_mixed` | int64 |  | 0.0 | 0 → 0 (median 0) | school count mixed (see layer docs) |
| `school_count_premium` | int64 |  | 0.0 | 0 → 3 (median 0) | school count premium (see layer docs) |
| `school_count_primary` | int64 |  | 0.0 | 0 → 6 (median 0) | school count primary (see layer docs) |
| `school_count_secondary` | int64 |  | 0.0 | 0 → 5 (median 0) | school count secondary (see layer docs) |
| `school_count_total` | int64 |  | 0.0 | 0 → 12 (median 0) | school count total (see layer docs) |
| `sig_beacon` | int64 |  | 0.0 | 0 → 124 (median 12) | Road-network metric: sig beacon |
| `sig_bicycle` | int64 |  | 0.0 | 0 → 6 (median 0) | Road-network metric: sig bicycle |
| `sig_filter_arrow` | int64 |  | 0.0 | 0 → 81 (median 4) | Road-network metric: sig filter arrow |
| `sig_ground` | int64 |  | 0.0 | 0 → 356 (median 41.5) | Road-network metric: sig ground |
| `sig_overhead` | int64 |  | 0.0 | 0 → 82 (median 11) | Road-network metric: sig overhead |
| `sig_pedestrian` | int64 |  | 0.0 | 0 → 266 (median 31.5) | Road-network metric: sig pedestrian |
| `sig_rag` | int64 |  | 0.0 | 0 → 64 (median 3) | Road-network metric: sig rag |
| `sig_total` | int64 |  | 0.0 | 0 → 905 (median 104.5) | Road-network metric: sig total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 104) | LTA traffic signals in hex |
| `silver_zone_count` | int64 |  | 0.0 | 0 → 11 (median 0) | silver zone count (see layer docs) |
| `speed_band_avg` | float64 |  | 0.0 | 0 → 5.92 (median 3.315) | speed band avg (see layer docs) |
| `speed_band_count` | int64 |  | 0.0 | 0 → 1127 (median 132.5) | speed band count (see layer docs) |
| `subzone_area_km2` | float64 | km2 | 0.0 | 0 → 68.55 (median 1.231) | Subzone polygon area |
| `subzone_area_m2` | float64 | m2 | 0.0 | 0 → 6.855e+07 (median 1.231e+06) | Subzone polygon area |
| `subzone_c` | object | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |
| `syn_density_x_amenities` | float64 |  | 0.0 | 0 → 1 (median 0.012) | Synergy interaction term: density x amenities (cross-feature product) |
| `syn_far_x_transit` | float64 |  | 0.0 | 0 → 0 (median 0) | Synergy interaction term: far x transit (cross-feature product) |
| `syn_office_x_transit` | float64 |  | 0.0 | 0 → 0 (median 0) | Synergy interaction term: office x transit (cross-feature product) |
| `syn_pop_x_transit` | float64 |  | 0.0 | 0 → 0 (median 0) | Synergy interaction term: pop x transit (cross-feature product) |
| `syn_pop_x_walk` | float64 |  | 0.0 | 0 → 0.785 (median 0.024) | Synergy interaction term: pop x walk (cross-feature product) |
| `syn_premium_school_x_4r` | float64 |  | 0.0 | 0 → 0.818 (median 0) | Synergy interaction term: premium school x 4r (cross-feature product) |
| `syn_residential_x_school` | float64 |  | 0.0 | 0 → 0.731 (median 0.017) | Synergy interaction term: residential x school (cross-feature product) |
| `syn_retail_x_anchors` | float64 |  | 0.0 | 0 → 1 (median 0.005) | Synergy interaction term: retail x anchors (cross-feature product) |
| `tourist_attraction_count` | int64 |  | 0.0 | 0 → 15 (median 0) | tourist attraction count (see layer docs) |
| `vibrancy_index` | float64 | 0-1 | 0.0 | 0.005 → 0.97 (median 0.1625) | Composite: places + magnets + reviews + transit + night lights |
| `walk_amenities_400m` | float64 | count | 0.0 | 0 → 1.562e+04 (median 974.5) | Place count within 400m walk |
| `walk_bus_score` | float64 |  | 0.0 | 0 → 0.987 (median 0.8785) | Walk-access score to nearest bus (distance-decayed) |
| `walk_clinic_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest clinic (distance-decayed) |
| `walk_convenience_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest convenience (distance-decayed) |
| `walk_food_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest food (distance-decayed) |
| `walk_hawker_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest hawker (distance-decayed) |
| `walk_mrt_score` | float64 |  | 0.0 | 0 → 1 (median 0.5125) | Walk-access score to nearest mrt (distance-decayed) |
| `walk_park_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest park (distance-decayed) |
| `walk_school_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest school (distance-decayed) |
| `walk_score_avg` | float64 | 0-1 | 0.0 | 0 → 0.22 (median 0.157) | Mean of the 9 amenity walk-access scores |
| `walk_supermarket_score` | float64 |  | 0.0 | 0 → 0 (median 0) | Walk-access score to nearest supermarket (distance-decayed) |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0 → 0.9132 (median 0.5462) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |
| `wc_built_share` | float64 |  | 0.0 | 0 → 0.966 (median 0.64) | ESA WorldCover land-cover share: built share |
| `wc_dominant_class` | int64 |  | 0.0 | 10 → 80 (median 50) | ESA WorldCover land-cover share: dominant class |
| `wc_grass_share` | float64 |  | 0.0 | 0 → 0.437 (median 0.036) | ESA WorldCover land-cover share: grass share |
| `wc_other_share` | float64 |  | 0.0 | 0 → 0.286 (median 0.008) | ESA WorldCover land-cover share: other share |
| `wc_tree_share` | float64 |  | 0.0 | 0.019 → 0.884 (median 0.218) | ESA WorldCover land-cover share: tree share |
| `wc_water_share` | float64 |  | 0.0 | 0 → 0.864 (median 0.001) | ESA WorldCover land-cover share: water share |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.618e+05 (median 1.504e+04) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/subzone_buildings_clean.parquet`

_17 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `best_max_floors` | float64 | floors | 3.0 | 1 → 70 (median 38) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 205 (median 3) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 1 → 1.313e+04 (median 621) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0.6206 → 5030 (median 433.3) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 102.1 → 3.748e+06 (median 2.705e+05) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 6.339e-05 → 1 (median 0.2178) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 647 (median 3) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 88 (median 2) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1998 (median 109.5) | Residential buildings |
| `est_built_far` | float64 | ratio | 0.0 | 0.0001902 → 7.347 (median 1.254) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 306.4 → 1.054e+07 (median 1.743e+06) | Sum of footprint × est_floors per building |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 416 (median 27) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 3.249e+04 (median 2366) | Total dwelling units across HDB blocks |
| `n_hex8` | int64 | count | 0.0 | 1 → 121 (median 2) | Number of hex8 children (bookkeeping) |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 1865 (median 90) | Number of buildings with floors ≥ 10 |
| `subzone_area_m2` | float64 | m2 | 0.0 | 2.36e+05 → 6.855e+07 (median 1.46e+06) | Subzone polygon area |
| `subzone_c` | object | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_built_environment_features.parquet`

_38 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 12.96 (median 2.61) | Area-weighted Gross Plot Ratio |
| `best_max_floors` | float64 | floors | 0.0 | 0 → 70 (median 36) | Max floor count (Overture or HDB authoritative) |
| `bldg_commercial_count` | float64 | count | 0.0 | 0 → 205 (median 3) | Commercial buildings |
| `bldg_count` | float64 | count | 0.0 | 1 → 1.313e+04 (median 621) | Building footprints in hex (Overture + HDB + OSM) |
| `bldg_density_per_km2` | float64 | count/km² | 0.0 | 0.6206 → 5030 (median 433.3) | Buildings per km² |
| `bldg_footprint_m2` | float64 | m² | 0.0 | 102.1 → 3.748e+06 (median 2.705e+05) | Total clipped building footprint area in hex |
| `bldg_footprint_share` | float64 | ratio [0,1] | 0.0 | 6.339e-05 → 1 (median 0.2178) | Footprint as fraction of hex area (clipped, ≤1) |
| `bldg_industrial_count` | float64 | count | 0.0 | 0 → 647 (median 3) | Industrial buildings |
| `bldg_institutional_count` | float64 | count | 0.0 | 0 → 88 (median 2) | Institutional buildings |
| `bldg_residential_count` | float64 | count | 0.0 | 0 → 1998 (median 109.5) | Residential buildings |
| `dominant_use` | object | categorical | 0.0 | 11 unique · `residential` | Bucket with highest area share |
| `est_built_far` | float64 | ratio | 0.0 | 0.0001902 → 7.347 (median 1.254) | Estimated built-up FAR = total floor area / hex area |
| `est_total_floor_area_m2` | float64 | m² | 0.0 | 306.4 → 1.054e+07 (median 1.743e+06) | Sum of footprint × est_floors per building |
| `hdb_block_count` | float64 | count | 0.0 | 0 → 416 (median 27) | HDB blocks (authoritative) |
| `hdb_dwelling_units` | float64 | count | 0.0 | 0 → 3.249e+04 (median 2366) | Total dwelling units across HDB blocks |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3942 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9423 (median 0.0208) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.4369 (median 0.0006) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.637 (median 0.0232) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0.009144 → 1.726 (median 0.9879) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.2255 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1651 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8335 (median 0.0133) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1856 (median 0.0087) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9591 (median 0.0561) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 22 → 8931 (median 287.5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.863 (median 0.0165) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8108 (median 0.3333) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 4.709e+05 → 6.869e+07 (median 1.667e+06) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8517 (median 0.1831) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.5228 (median 0.0031) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.5622 (median 0.0144) | Water body share |
| `max_gpr` | float64 | ratio | 0.0 | 0 → 25 (median 3.2) | Max GPR within hex |
| `n_hex8` | int64 | count | 0.0 | 1 → 121 (median 2) | Number of hex8 children (bookkeeping) |
| `n_highrise_bldgs` | float64 | count | 0.0 | 0 → 1865 (median 90) | Number of buildings with floors ≥ 10 |
| `subzone_area_m2` | float64 | m2 | 0.0 | 2.36e+05 → 6.855e+07 (median 1.46e+06) | Subzone polygon area |
| `subzone_c` | object | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_land_use.parquet`

_22 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `avg_gpr` | float64 | ratio | 0.0 | 0 → 14.7 (median 2.513) | Area-weighted Gross Plot Ratio |
| `dominant_use` | object | categorical | 0.0 | 13 unique · `mixed_use` | Bucket with highest area share |
| `lu_business_park_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6194 (median 0) | Business park share |
| `lu_business_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9114 (median 0.0125) | Land area share zoned business (industrial) |
| `lu_commercial_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.6369 (median 0.0008) | Land area share zoned commercial |
| `lu_educational_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.79 (median 0.0212) | Educational institution share |
| `lu_entropy` | float64 | nats | 0.0 | 0.021 → 2.115 (median 1.424) | Shannon entropy across 14 LU buckets |
| `lu_health_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.371 (median 0) | Health & medical share |
| `lu_hotel_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.1804 (median 0) | Hotel zone share |
| `lu_institutional_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9115 (median 0.0138) | Civic/community/place-of-worship |
| `lu_mixed_use_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.3615 (median 0.009) | Mixed-use zone share (residential + commercial) |
| `lu_open_space_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9969 (median 0.0483) | Park / open space share |
| `lu_other_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0 (median 0) | Other / unmapped |
| `lu_parcel_count` | int64 | count | 0.0 | 22 → 7026 (median 227.5) | URA parcels intersecting hex |
| `lu_reserve_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.9576 (median 0.0127) | Reserve site share |
| `lu_residential_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8106 (median 0.3315) | Land area share zoned residential |
| `lu_total_m2` | float64 | m² | 0.0 | 1.19e+05 → 6.798e+07 (median 1.294e+06) | Total land area covered by URA parcels in hex |
| `lu_transport_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.8373 (median 0.1926) | Transport infra share |
| `lu_utility_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7739 (median 0.0027) | Utility infra share |
| `lu_water_pct` | float64 | ratio [0,1] | 0.0 | 0 → 0.7043 (median 0.012) | Water body share |
| `max_gpr` | float64 | ratio | 3.1 | 1 → 25 (median 3.5) | Max GPR within hex |
| `subzone_c` | object | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |

## `hex/subzone_mobility_features.parquet`

_38 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 7.355e+04 (median 2636) | Bridge segment length |
| `bus_stop_count` | float64 | count | 0.0 | 0 → 104 (median 16) | Bus stops in hex |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0.0193) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 5) | Tarjan bridge endpoints (network cut points) |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 2.076e+05 (median 1.428e+04) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 3.573e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 9542 (median 42.01) | Centroid distance to nearest bus stop |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 9553 (median 77.23) | Centroid distance to nearest motorway/trunk segment |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 9633 (median 150.6) | Centroid distance to nearest MRT/LRT station |
| `expressway_in_subzone` | bool | bool | 0.0 | 0 → 1 (median 1) | An expressway segment crosses the subzone |
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `has_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | Subzone contains an interchange station |
| `has_mrt` | bool | bool | 0.0 | 0 → 1 (median 0) | Subzone contains at least one MRT/LRT station |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 42 (median 2.5) | Authoritative HDB multi-storey carparks |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 54.64) | Lane-km per km² (lane count × length / area) |
| `max_transit_score` | float64 | 0-1 | 0.0 | 6.178e-06 → 0.9879 (median 0.8407) | Best hex8 transit score within subzone |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 33 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 6 (median 0) | MRT/LRT stations in hex |
| `n_hex8` | int64 | count | 0.0 | 1 → 121 (median 2) | Number of hex8 children (bookkeeping) |
| `n_hex8_tr` | int64 | count | 0.0 | 1 → 121 (median 2) | hex8 children with transit data (bookkeeping) |
| `n_hex8_wk` | int64 | count | 0.0 | 1 → 121 (median 2) | hex8 children with walkability data (bookkeeping) |
| `n_interchanges` | int64 | count | 0.0 | 0 → 2 (median 0) | Interchange stations in subzone |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 61 (median 8) | OSM amenity=parking points |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 3.072e+05 (median 3.666e+04) | Footway + path + cycleway + steps length |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 2.05e+04 (median 1732) | Rail line length through hex (above + underground) |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 264.1 (median 56.98) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 5204 (median 394.5) | Road-network metric: road intersection count total |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1538 (median 305.1) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 1.062e+06 (median 7.348e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 8 unique · `motorway` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.7701 (median 0.4958) | Pedestrian-only roads as fraction of total |
| `road_walkable_share_wk` | float64 |  | 0.0 | 0 → 0.8394 (median 0.479) | Road-network metric: road walkable share wk |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 143.5) | LTA traffic signals in hex |
| `signalized_crossing_count_wk` | float64 | count | 0.0 | 0 → 968 (median 143.5) | Signalized pedestrian crossings (walk-layer copy) |
| `subzone_area_km2` | float64 | km2 | 0.0 | 0.236 → 68.55 (median 1.46) | Subzone polygon area |
| `subzone_c` | object | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |
| `walk_amenities_400m` | int64 | count | 0.0 | 4 → 1.562e+04 (median 1230) | Place count within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0.0001536 → 0.9132 (median 0.6135) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `hex/subzone_population.parquet`

_12 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `nonres_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.2863) | Non-resident share of total pop |
| `pop_0_14` | float64 | persons | 0.0 | 0 → 1.531e+04 (median 755) | Population age 0-14 |
| `pop_15_64` | float64 | persons | 0.0 | 0 → 8.245e+04 (median 3544) | Population age 15-64 |
| `pop_65plus` | float64 | persons | 0.0 | 0 → 2.643e+04 (median 1079) | Population age 65+ |
| `pop_dorm` | float64 | persons | 0.0 | 0 → 4.271e+04 (median 0) | Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident |
| `pop_hdb` | float64 | persons | 0.0 | 0 → 1.125e+05 (median 2053) | Residents in HDB flats |
| `pop_hdb_share` | float64 | ratio [0,1] | 0.0 | 0 → 1 (median 0.5671) | HDB share of resident pop |
| `pop_non_hdb` | float64 | persons | 0.0 | 0 → 3.042e+04 (median 1215) | Residents in non-HDB housing |
| `pop_nonresident` | float64 | persons | 0.0 | 0 → 7.171e+04 (median 3213) | Non-residents (FW + EP + MDW) |
| `pop_resident` | float64 | persons | 0.0 | 0 → 1.242e+05 (median 5404) | Resident population (citizens + PRs) |
| `pop_total_all` | float64 | persons | 0.0 | 0 → 1.399e+05 (median 1.267e+04) | Total population (residents + non-residents) |
| `subzone_c` | object | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |

## `hex/subzone_roads_clean.parquet`

_18 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bridge_length_m` | float64 | m | 0.0 | 0 → 7.355e+04 (median 2636) | Bridge segment length |
| `centr_betweenness_max` | float64 | ratio | 0.0 | 0 → 0.108 (median 0.0193) | Max betweenness centrality of major-road nodes |
| `centr_bridge_count` | float64 | count | 0.0 | 0 → 64 (median 5) | Tarjan bridge endpoints (network cut points) |
| `dist_expressway_m` | float64 | m | 0.0 | 0.00143 → 9553 (median 77.23) | Centroid distance to nearest motorway/trunk segment |
| `expressway_in_subzone` | bool | bool | 0.0 | 0 → 1 (median 1) | An expressway segment crosses the subzone |
| `hdb_mscp_count` | float64 | count | 0.0 | 0 → 42 (median 2.5) | Authoritative HDB multi-storey carparks |
| `lane_km_per_km2` | float64 | km/km² | 0.0 | 0 → 97.19 (median 54.64) | Lane-km per km² (lane count × length / area) |
| `n_hex8` | int64 | count | 0.0 | 1 → 121 (median 2) | Number of hex8 children (bookkeeping) |
| `parking_lot_count` | float64 | count | 0.0 | 0 → 61 (median 8) | OSM amenity=parking points |
| `road_density_km_per_km2` | float64 | km/km² | 0.0 | 0 → 264.1 (median 56.98) | Road km per km² |
| `road_intersection_count_total` | int64 |  | 0.0 | 0 → 5204 (median 394.5) | Road-network metric: road intersection count total |
| `road_intersection_density_per_km2` | float64 | count/km² | 0.0 | 0 → 1538 (median 305.1) | Vehicle-network nodes with deg ≥ 3 per km² (Jacobs) |
| `road_length_total_m` | float64 | m | 0.0 | 0 → 1.062e+06 (median 7.348e+04) | Total OSM road length clipped to hex |
| `road_max_class_through` | object | categorical | 0.0 | 8 unique · `motorway` | Highest road class running through hex |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.7701 (median 0.4958) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 143.5) | LTA traffic signals in hex |
| `subzone_area_km2` | float64 | km2 | 0.0 | 0.236 → 68.55 (median 1.46) | Subzone polygon area |
| `subzone_c` | object | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_satellite.parquet`

_9 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `nl_2022` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 153.6 (median 58.86) | VIIRS night light radiance 2022 (subzone-broadcast) |
| `nl_2024` | float64 | nanoWatts/cm²/sr | 0.0 | 0 → 179.5 (median 63.89) | VIIRS night light radiance 2024 (subzone-broadcast) |
| `nl_change_pct` | float64 | % | 0.0 | -28.01 → 120.4 (median 8.999) | VIIRS 2022→2024 brightness change |
| `nl_commercial_indicator` | float64 | composite | 0.0 | 0 → 165 (median 30.88) | nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce) |
| `nl_decline_zone` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light declined ≥ 20% |
| `nl_growth_corridor` | bool | bool | 0.0 | 0 → 1 (median 0) | True if night light grew ≥ 20% |
| `nl_per_capita` | float64 | radiance/person | 0.0 | 0 → 1.61 (median 0.0463) | nl_2024 / pop_resident (commercial vs residential signal) |
| `subzone_c` | object | string | 0.0 | 326 unique · `AMSZ01` | URA subzone code |
| `wp_pop` | float64 | persons | 0.0 | 0 → 1.618e+05 (median 1.504e+04) | WorldPop count per hex (single snapshot — only one valid TIF available) |

## `hex/subzone_transit_clean.parquet`

_14 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `bus_stop_count` | float64 | count | 0.0 | 0 → 104 (median 16) | Bus stops in hex |
| `daily_bus_taps` | float64 | taps/day | 0.0 | 0 → 2.076e+05 (median 1.428e+04) | Daily bus taps (Dec 2025 LTA monthly / 31) |
| `daily_train_taps` | float64 | taps/day | 0.0 | 0 → 3.573e+05 (median 0) | Daily MRT/LRT taps (Jan 2026 LTA monthly / 31) |
| `dist_bus_m` | float64 | m | 0.0 | 5.326 → 9542 (median 42.01) | Centroid distance to nearest bus stop |
| `dist_mrt_m` | float64 | m | 0.0 | 0 → 9633 (median 150.6) | Centroid distance to nearest MRT/LRT station |
| `has_interchange` | bool | bool | 0.0 | 0 → 1 (median 0) | Subzone contains an interchange station |
| `has_mrt` | bool | bool | 0.0 | 0 → 1 (median 0) | Subzone contains at least one MRT/LRT station |
| `max_transit_score` | float64 | 0-1 | 0.0 | 6.178e-06 → 0.9879 (median 0.8407) | Best hex8 transit score within subzone |
| `mrt_exit_count` | float64 | count | 0.0 | 0 → 33 (median 0) | MRT exits in hex |
| `mrt_station_count` | float64 | count | 0.0 | 0 → 6 (median 0) | MRT/LRT stations in hex |
| `n_hex8` | int64 | count | 0.0 | 1 → 121 (median 2) | Number of hex8 children (bookkeeping) |
| `n_interchanges` | int64 | count | 0.0 | 0 → 2 (median 0) | Interchange stations in subzone |
| `rail_line_through_m` | float64 | m | 0.0 | 0 → 2.05e+04 (median 1732) | Rail line length through hex (above + underground) |
| `subzone_c` | object | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |

## `hex/subzone_walkability.parquet`

_8 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `expressway_severance` | bool | bool | 0.0 | 0 → 1 (median 0) | Expressway < 200m AND no exit < 400m (barrier without benefit) |
| `n_hex8` | int64 | count | 0.0 | 1 → 121 (median 2) | Number of hex8 children (bookkeeping) |
| `ped_path_length_m` | float64 | m | 0.0 | 0 → 3.072e+05 (median 3.666e+04) | Footway + path + cycleway + steps length |
| `road_walkable_share` | float64 | ratio [0,1] | 0.0 | 0 → 0.8394 (median 0.479) | Pedestrian-only roads as fraction of total |
| `signalized_crossing_count` | float64 | count | 0.0 | 0 → 968 (median 143.5) | LTA traffic signals in hex |
| `subzone_c` | object | string | 0.0 | 270 unique · `AMSZ02` | URA subzone code |
| `walk_amenities_400m` | int64 | count | 0.0 | 4 → 1.562e+04 (median 1230) | Place count within 400m walk |
| `walkability_score` | float64 | score [0,1] | 0.0 | 0.0001536 → 0.9132 (median 0.6135) | Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15) |

## `places/sgp_places_final.parquet`

_27 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `brand` | object | string | 0.0 | 251 unique · `` | Raw brand string of the place (pre-normalisation) |
| `brand_norm` | object | string | 92.1 | 268 unique · `Marina Bay Sands` | Normalized brand name |
| `brand_source` | object | categorical | 92.1 | 2 unique · `scrape` | scrape | name_pattern |
| `has_rating` | bool | bool | 0.0 | 0 → 1 (median 1) | Place carries a Google rating |
| `has_reviews` | bool | bool | 0.0 | 0 → 1 (median 1) | Place carries at least one review |
| `hdb_town` | object |  | 47.5 | 27 unique · `BUKIT BATOK` | hdb town (see layer docs) |
| `hex8_id` | object | string | 0.0 | 911 unique · `886520c95bfffff` | H3 resolution-8 cell ID (~0.737 km², 461m edge) |
| `hex9_id` | object | string | 0.0 | 4224 unique · `896520c95a7ffff` | H3 resolution-9 cell ID (~0.105 km², 174m edge) |
| `id` | object | string | 0.0 | 190591 unique · `c5Wl6sW53JSX` | Place ID (string hash) |
| `in_sgp` | bool | bool | 0.0 | 1 → 1 (median 1) | Place lies within Singapore boundary (QA flag) |
| `is_long_tail` | bool | bool | 0.0 | 0 → 1 (median 1) | reviews < 5 OR no rating |
| `is_magnet` | bool | bool | 0.0 | 0 → 1 (median 0) | rating ≥ 4 AND reviews ≥ 100 |
| `latitude` | float64 | degrees | 0.0 | 1.16 → 1.471 (median 1.331) | Place latitude (WGS84) |
| `longitude` | float64 | degrees | 0.0 | 103.6 → 104.1 (median 103.8) | Place longitude (WGS84) |
| `magnet_strength` | float64 | ratio | 42.6 | 0.6931 → 55.06 (median 12.67) | rating × log(reviews+1) |
| `name` | object | string | 0.0 | 175228 unique · `Golden Hill Landscape Pte. Ltd.` | Place name |
| `parent_pa` | object | string | 0.0 | 55 unique · `LIM CHU KANG` | URA planning area name (one of 55) |
| `parent_region` | object | string | 0.0 | 5 unique · `NORTH REGION` | URA region (5 regions) |
| `parent_subzone_c` | object | string | 0.0 | 331 unique · `LKSZ01` | URA subzone code of parent |
| `parent_subzone_name` | object | string | 0.0 | 331 unique · `LIM CHU KANG` | URA subzone full name |
| `parent_subzone_source` | object | category | 0.0 | 90 unique · `contains` | How the place→subzone attach was resolved (bookkeeping) |
| `plexis_category` | object | categorical | 0.0 | 24 unique · `services` | Resolved 24-category Plexis taxonomy |
| `primary_category` | object | string | 0.0 | 166 unique · `Landscape Design` | Original Google Maps category |
| `rating` | float64 | stars | 42.6 | 1 → 5 (median 4.5) | Google Maps rating (0–5) |
| `review_bucket` | object | category | 0.0 | 5 unique · `1-9` | Review-volume tier of the place |
| `review_quality_pctl_in_cat` | float64 | ratio [0,1] | 42.6 | 0.0006369 → 1 (median 0.4997) | magnet_strength percentile within category |
| `reviews_count` | int64 | count | 0.0 | 0 → 1.109e+05 (median 2) | Google Maps reviews count |

## `places/sgp_places_micrograph.parquet`

_20 columns_

| Column | dtype | Units | Null % | Range / sample | Description |
|---|---|---|---|---|---|
| `id` | object | string | 0.0 | 190591 unique · `c5Wl6sW53JSX` | Place ID (string hash) |
| `pmg_anchor_strength_sum` | float32 | index | 0.0 | 0 → 2111 (median 9.921) | Summed anchor strength in the place's neighbourhood |
| `pmg_anchors_400m` | int32 | count | 0.0 | 0 → 78 (median 0) | Magnet/anchor places within 400 m |
| `pmg_anchors_800m` | int32 | count | 0.0 | 0 → 260 (median 1) | Magnet/anchor places within 800 m |
| `pmg_closest_anchor_m` | float32 | m | 0.0 | 1.208 → 9999 (median 561.8) | Distance to the nearest anchor place |
| `pmg_closest_competitor_m` | float32 | m | 0.0 | 0.505 → 9999 (median 93.02) | Distance to the nearest same-category place |
| `pmg_competitor_rating_avg` | float32 | stars | 0.0 | 0 → 5 (median 4.371) | Mean rating of nearby competitors — incumbent quality bar |
| `pmg_competitors_400m` | int32 | count | 0.0 | 0 → 476 (median 6) | SAME-category places within 400 m of this place |
| `pmg_competitors_800m` | int32 | count | 0.0 | 0 → 1381 (median 22) | SAME-category places within 800 m |
| `pmg_complement_categories_present` | int32 | count | 0.0 | 0 → 5 (median 3) | Distinct complementary categories present within 400 m |
| `pmg_complement_diversity` | float32 | 0-1 | 0.0 | 0 → 1.587 (median 0.698) | Entropy of the complementary mix around the place |
| `pmg_complements_400m` | int32 | count | 0.0 | 0 → 814 (median 9) | Complementary-category places within 400 m (demand context) |
| `pmg_complements_800m` | int32 | count | 0.0 | 0 → 2362 (median 41) | Complementary-category places within 800 m |
| `pmg_hex_transit_score` | float64 | 0-1 | 0.0 | 0 → 0.988 (median 0.716) | Transit score of the place's hex (context copy) |
| `pmg_hex_walk_score` | float64 | 0-1 | 0.0 | 0 → 0.959 (median 0.793) | Walkability score of the place's hex (context copy) |
| `pmg_near_bus_300m` | int8 | bool | 0.0 | 0 → 1 (median 0) | Bus stop within 300 m of the place |
| `pmg_near_mrt_400m` | int8 | bool | 0.0 | 0 → 1 (median 0) | MRT within 400 m of the place |
| `pmg_snap_delta_m` | float32 | m | 0.0 | 0.025 → 1.019e+04 (median 27.77) | Geocode-to-network snap distance (QA) |
| `pmg_walk_dist_bus_m` | float32 | m | 0.0 | 0.111 → 9999 (median 318.1) | Walk distance to nearest bus stop |
| `pmg_walk_dist_mrt_m` | float32 | m | 0.0 | 0.609 → 9999 (median 918.4) | Walk distance from the place to nearest MRT/LRT |

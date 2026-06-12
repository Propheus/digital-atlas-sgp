"""
Plexis SGP v4 — feature + dataset catalog generator.

Walks every .parquet under hex/ and places/, emits:
  catalog/dataset_catalog.parquet  + .md   — one row per dataset
  catalog/feature_catalog.parquet  + .md   — one row per (dataset, column)

Each feature row: dataset, scale, column, dtype, null_pct, sample, units, source, notes.
Curated descriptions in DESCRIPTIONS dict; everything else auto-discovered.
"""
import json, time, re
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
CAT = ROOT / "catalog"
CAT.mkdir(exist_ok=True)


# ===== Curated metadata for individual columns (extends what auto-discovery gives) =====
# (column_name) → dict(description, units, source_stage, derivation)
DESCRIPTIONS = {
    # Identity
    "hex9_id": dict(description="H3 resolution-9 cell ID (~0.105 km², 174m edge)", units="string", source_stage="0"),
    "hex8_id": dict(description="H3 resolution-8 cell ID (~0.737 km², 461m edge)", units="string", source_stage="0"),
    "subzone_c": dict(description="URA subzone code", units="string", source_stage="0"),
    "parent_hex8": dict(description="hex-9's parent hex-8", units="string", source_stage="0"),
    "parent_subzone": dict(description="URA subzone parent (max-overlap)", units="string", source_stage="0"),
    "parent_subzone_name": dict(description="URA subzone full name", units="string", source_stage="0"),
    "parent_pa": dict(description="URA planning area name (one of 55)", units="string", source_stage="0c"),
    "parent_region": dict(description="URA region (5 regions)", units="string", source_stage="0c"),
    "lat": dict(description="Hex centroid latitude", units="degrees", source_stage="0"),
    "lng": dict(description="Hex centroid longitude", units="degrees", source_stage="0"),

    # Population
    "pop_resident": dict(description="Resident population (citizens + PRs)", units="persons", source_stage="3", derivation="SingStat 2025 dasymetric via HDB units + non-HDB area"),
    "pop_hdb": dict(description="Residents in HDB flats", units="persons", source_stage="3"),
    "pop_non_hdb": dict(description="Residents in non-HDB housing", units="persons", source_stage="3"),
    "pop_nonresident": dict(description="Non-residents (FW + EP + MDW)", units="persons", source_stage="3b", derivation="V3 hex-8 anchor split to hex-9 by land-use weight"),
    "pop_total_all": dict(description="Total population (residents + non-residents)", units="persons", source_stage="3+3b"),
    "pop_0_14": dict(description="Population age 0-14", units="persons", source_stage="3"),
    "pop_15_64": dict(description="Population age 15-64", units="persons", source_stage="3"),
    "pop_65plus": dict(description="Population age 65+", units="persons", source_stage="3"),
    "pop_hdb_share": dict(description="HDB share of resident pop", units="ratio [0,1]", source_stage="3"),
    "nonres_share": dict(description="Non-resident share of total pop", units="ratio [0,1]", source_stage="3b"),

    # Land use
    "lu_residential_pct": dict(description="Land area share zoned residential", units="ratio [0,1]", source_stage="4"),
    "lu_commercial_pct": dict(description="Land area share zoned commercial", units="ratio [0,1]", source_stage="4"),
    "lu_business_pct": dict(description="Land area share zoned business (industrial)", units="ratio [0,1]", source_stage="4"),
    "lu_business_park_pct": dict(description="Business park share", units="ratio [0,1]", source_stage="4"),
    "lu_hotel_pct": dict(description="Hotel zone share", units="ratio [0,1]", source_stage="4"),
    "lu_open_space_pct": dict(description="Park / open space share", units="ratio [0,1]", source_stage="4"),
    "lu_transport_pct": dict(description="Transport infra share", units="ratio [0,1]", source_stage="4"),
    "lu_mixed_use_pct": dict(description="Mixed-use zone share (residential + commercial)", units="ratio [0,1]", source_stage="4"),
    "lu_educational_pct": dict(description="Educational institution share", units="ratio [0,1]", source_stage="4"),
    "lu_health_pct": dict(description="Health & medical share", units="ratio [0,1]", source_stage="4"),
    "lu_institutional_pct": dict(description="Civic/community/place-of-worship", units="ratio [0,1]", source_stage="4"),
    "lu_utility_pct": dict(description="Utility infra share", units="ratio [0,1]", source_stage="4"),
    "lu_water_pct": dict(description="Water body share", units="ratio [0,1]", source_stage="4"),
    "lu_reserve_pct": dict(description="Reserve site share", units="ratio [0,1]", source_stage="4"),
    "lu_other_pct": dict(description="Other / unmapped", units="ratio [0,1]", source_stage="4"),
    "lu_total_m2": dict(description="Total land area covered by URA parcels in hex", units="m²", source_stage="4"),
    "lu_entropy": dict(description="Shannon entropy across 14 LU buckets", units="nats", source_stage="4"),
    "dominant_use": dict(description="Bucket with highest area share", units="categorical", source_stage="4"),
    "avg_gpr": dict(description="Area-weighted Gross Plot Ratio", units="ratio", source_stage="4"),
    "max_gpr": dict(description="Max GPR within hex", units="ratio", source_stage="4"),
    "lu_parcel_count": dict(description="URA parcels intersecting hex", units="count", source_stage="4"),

    # Buildings
    "bldg_count": dict(description="Building footprints in hex (Overture + HDB + OSM)", units="count", source_stage="2"),
    "bldg_density_per_km2": dict(description="Buildings per km²", units="count/km²", source_stage="2"),
    "bldg_total_area_m2": dict(description="Total building footprint area", units="m²", source_stage="2"),
    "bldg_footprint_share": dict(description="Fraction of hex covered by buildings", units="ratio [0,1]", source_stage="2"),
    "bldg_residential_count": dict(description="Residential buildings", units="count", source_stage="2"),
    "bldg_commercial_count": dict(description="Commercial buildings", units="count", source_stage="2"),
    "bldg_industrial_count": dict(description="Industrial buildings", units="count", source_stage="2"),
    "bldg_institutional_count": dict(description="Institutional buildings", units="count", source_stage="2"),
    "best_max_floors": dict(description="Max floor count (Overture or HDB authoritative)", units="floors", source_stage="2"),
    "best_avg_floors": dict(description="Avg floor count", units="floors", source_stage="2"),
    "is_highrise": dict(description="True if max_floors >= 10", units="bool", source_stage="2"),
    "hdb_block_count": dict(description="HDB blocks (authoritative)", units="count", source_stage="2"),
    "hdb_dwelling_units": dict(description="Total dwelling units across HDB blocks", units="count", source_stage="2"),
    "hdb_max_floors": dict(description="Max HDB floor count", units="floors", source_stage="2"),
    "hdb_avg_floors": dict(description="Avg HDB floor count", units="floors", source_stage="2"),
    "hdb_min_year": dict(description="Earliest HDB completion year", units="year", source_stage="2"),
    "hdb_avg_year": dict(description="Avg HDB completion year", units="year", source_stage="2"),

    # Buildings v2 (clean)
    "bldg_footprint_m2": dict(description="Total clipped building footprint area in hex", units="m²", source_stage="2c", derivation="sum of building polygon × hex polygon intersection areas"),
    "bldg_footprint_share": dict(description="Footprint as fraction of hex area (clipped, ≤1)", units="ratio [0,1]", source_stage="2c"),
    "n_highrise_bldgs": dict(description="Number of buildings with floors ≥ 10", units="count", source_stage="2c"),
    "est_total_floor_area_m2": dict(description="Sum of footprint × est_floors per building", units="m²", source_stage="2c", derivation="floors from Overture or class default (HDB 14, residential 12, commercial 6, industrial 2)"),
    "est_built_far": dict(description="Estimated built-up FAR = total floor area / hex area", units="ratio", source_stage="2c"),
    "hdb_avg_age_years": dict(description="Avg years since HDB completion (year_completed filtered ≥1960)", units="years", source_stage="2c"),

    # Roads / parking / centrality (stage 6)
    "road_length_total_m": dict(description="Total OSM road length clipped to hex", units="m", source_stage="6"),
    "road_density_km_per_km2": dict(description="Road km per km²", units="km/km²", source_stage="6"),
    "road_walkable_share": dict(description="Pedestrian-only roads as fraction of total", units="ratio [0,1]", source_stage="6"),
    "road_max_class_through": dict(description="Highest road class running through hex", units="categorical", source_stage="6"),
    "road_intersection_density_per_km2": dict(description="Vehicle-network nodes with deg ≥ 3 per km² (Jacobs)", units="count/km²", source_stage="6"),
    "dist_expressway_m": dict(description="Centroid distance to nearest motorway/trunk segment", units="m", source_stage="6"),
    "near_expressway_exit_400m": dict(description="True if motorway_link/trunk_link < 400m (drive-thru flag)", units="bool", source_stage="6"),
    "lane_km_per_km2": dict(description="Lane-km per km² (lane count × length / area)", units="km/km²", source_stage="6"),
    "oneway_pct": dict(description="Fraction of vehicular length that's one-way", units="ratio [0,1]", source_stage="6"),
    "bridge_length_m": dict(description="Bridge segment length", units="m", source_stage="6"),
    "signalized_crossing_count": dict(description="LTA traffic signals in hex", units="count", source_stage="6"),
    "parking_lot_count": dict(description="OSM amenity=parking points", units="count", source_stage="6"),
    "hdb_mscp_count": dict(description="Authoritative HDB multi-storey carparks", units="count", source_stage="6"),
    "centr_betweenness_max": dict(description="Max betweenness centrality of major-road nodes", units="ratio", source_stage="6g"),
    "centr_bridge_count": dict(description="Tarjan bridge endpoints (network cut points)", units="count", source_stage="6g"),

    # Transit (stage 5)
    "mrt_station_count": dict(description="MRT/LRT stations in hex", units="count", source_stage="5"),
    "mrt_exit_count": dict(description="MRT exits in hex", units="count", source_stage="5"),
    "bus_stop_count": dict(description="Bus stops in hex", units="count", source_stage="5"),
    "dist_mrt_m": dict(description="Centroid distance to nearest MRT/LRT station", units="m", source_stage="5"),
    "dist_mrt_exit_m": dict(description="Centroid distance to nearest MRT exit", units="m", source_stage="5"),
    "dist_bus_m": dict(description="Centroid distance to nearest bus stop", units="m", source_stage="5"),
    "near_mrt_400m": dict(description="True if MRT < 400m", units="bool", source_stage="5"),
    "near_bus_300m": dict(description="True if bus < 300m", units="bool", source_stage="5"),
    "rail_line_through_m": dict(description="Rail line length through hex (above + underground)", units="m", source_stage="5"),
    "daily_train_taps": dict(description="Daily MRT/LRT taps (Jan 2026 LTA monthly / 31)", units="taps/day", source_stage="5"),
    "daily_bus_taps": dict(description="Daily bus taps (Dec 2025 LTA monthly / 31)", units="taps/day", source_stage="5"),
    "bus_routes_per_stop_max": dict(description="Max # routes serving a stop in hex (GTFS)", units="count", source_stage="5"),
    "bus_routes_per_stop_mean": dict(description="Mean routes/stop in hex", units="count", source_stage="5"),
    "gtfs_headway_am_min": dict(description="Best AM-peak headway (lowest minutes between buses) at any stop in hex", units="min", source_stage="5"),
    "is_mrt_interchange": dict(description="True if any station has ≥2 lines (slash-PT_CODE)", units="bool", source_stage="5"),
    "transit_score": dict(description="0.6×MRT_decay + 0.4×bus_decay (decay = exp(-d/800m))", units="score [0,1]", source_stage="5"),

    # Walkability (stage 7w)
    "ped_path_length_m": dict(description="Footway + path + cycleway + steps length", units="m", source_stage="7w"),
    "ped_path_density_km_per_km2": dict(description="Pedestrian-network density", units="km/km²", source_stage="7w"),
    "dist_walk_hawker_m": dict(description="Walk distance to nearest hawker (Euclidean × 1.3 detour)", units="m", source_stage="7w"),
    "dist_walk_clinic_m": dict(description="Walk distance to nearest clinic", units="m", source_stage="7w"),
    "dist_walk_supermarket_m": dict(description="Walk distance to nearest supermarket", units="m", source_stage="7w"),
    "dist_walk_park_m": dict(description="Walk distance to nearest park", units="m", source_stage="7w"),
    "dist_walk_school_m": dict(description="Walk distance to nearest school", units="m", source_stage="7w"),
    "dist_walk_food_m": dict(description="Walk distance to nearest restaurant/cafe/hawker/bakery/fast-food", units="m", source_stage="7w"),
    "dist_walk_convenience_m": dict(description="Walk distance to nearest convenience store", units="m", source_stage="7w"),
    "walk_amenities_400m": dict(description="Place count within 400m walk", units="count", source_stage="7w"),
    "walk_food_400m": dict(description="Food places within 400m walk", units="count", source_stage="7w"),
    "walk_hawker_400m": dict(description="Hawkers within 400m walk", units="count", source_stage="7w"),
    "walk_clinic_400m": dict(description="Clinics within 400m walk", units="count", source_stage="7w"),
    "walk_supermarket_400m": dict(description="Supermarkets within 400m walk", units="count", source_stage="7w"),
    "walk_park_400m": dict(description="Parks within 400m walk", units="count", source_stage="7w"),
    "walk_school_400m": dict(description="Schools within 400m walk", units="count", source_stage="7w"),
    "walk_convenience_400m": dict(description="Convenience stores within 400m walk", units="count", source_stage="7w"),
    "expressway_severance": dict(description="Expressway < 200m AND no exit < 400m (barrier without benefit)", units="bool", source_stage="7w"),
    "walkability_score": dict(description="Composite (ped infra 0.55 + amenities 0.15 + transit 0.15 - severance 0.15)", units="score [0,1]", source_stage="7w"),

    # Places
    "id": dict(description="Place ID (string hash)", units="string", source_stage="1"),
    "name": dict(description="Place name", units="string", source_stage="1"),
    "primary_category": dict(description="Original Google Maps category", units="string", source_stage="1"),
    "plexis_category": dict(description="Resolved 24-category Plexis taxonomy", units="categorical", source_stage="1b"),
    "brand_norm": dict(description="Normalized brand name", units="string", source_stage="1c"),
    "brand_source": dict(description="scrape | name_pattern", units="categorical", source_stage="1c"),
    "rating": dict(description="Google Maps rating (0–5)", units="stars", source_stage="1"),
    "reviews_count": dict(description="Google Maps reviews count", units="count", source_stage="1"),
    "magnet_strength": dict(description="rating × log(reviews+1)", units="ratio", source_stage="1d"),
    "is_magnet": dict(description="rating ≥ 4 AND reviews ≥ 100", units="bool", source_stage="1d"),
    "is_long_tail": dict(description="reviews < 5 OR no rating", units="bool", source_stage="1d"),
    "review_quality_pctl_in_cat": dict(description="magnet_strength percentile within category", units="ratio [0,1]", source_stage="1d"),

    # Satellite
    "nl_2022": dict(description="VIIRS night light radiance 2022 (subzone-broadcast)", units="nanoWatts/cm²/sr", source_stage="5b"),
    "nl_2024": dict(description="VIIRS night light radiance 2024 (subzone-broadcast)", units="nanoWatts/cm²/sr", source_stage="5b"),
    "nl_change_pct": dict(description="VIIRS 2022→2024 brightness change", units="%", source_stage="5b"),
    "nl_growth_corridor": dict(description="True if night light grew ≥ 20%", units="bool", source_stage="5b"),
    "nl_decline_zone": dict(description="True if night light declined ≥ 20%", units="bool", source_stage="5b"),
    "nl_per_capita": dict(description="nl_2024 / pop_resident (commercial vs residential signal)", units="radiance/person", source_stage="5b"),
    "nl_commercial_indicator": dict(description="nl_2024 weighted by 1/(1+pop/1000) — high when bright but pop-poor (commerce)", units="composite", source_stage="5b"),
    "wp_pop": dict(description="WorldPop count per hex (single snapshot — only one valid TIF available)", units="persons", source_stage="5b"),
}

# ===== Site-selection layers S1-S9 (v5.0.0; gates in SITE_SELECTION_VALIDATION.md) =====
DESCRIPTIONS.update({
    # S3 daytime population
    "dt_pop": dict(description="Commuter daytime headcount: pop_resident − AM transit out + AM in (0.62 PT mode share, /22 weekdays). Clipped ≥0.", units="persons", source_stage="S3"),
    "dt_pop_unadj": dict(description="Daytime pop, transit-observed only (no mode-share scale-up)", units="persons", source_stage="S3"),
    "dt_ratio": dict(description="dt_pop / pop_resident; NaN where pop<50 & no OD (no-data, NOT 0)", units="ratio", source_stage="S3"),
    "dt_inflow_am_persons": dict(description="AM-window inbound persons (mode-share adjusted)", units="persons/day", source_stage="S3"),
    "dt_outflow_am_persons": dict(description="AM-window outbound persons (mode-share adjusted)", units="persons/day", source_stage="S3"),
    "dt_net_am_persons": dict(description="AM net inflow (in − out). THE directional day-night signal; basis of redefined breathing_idx", units="persons/day", source_stage="S3"),
    "dt_clipped": dict(description="True if pop+net was clipped at 0 (12 hexes)", units="bool", source_stage="S3"),
    "dt_class": dict(description="job_center (>1.5) / balanced / bedroom (<0.67) / no_data", units="category", source_stage="S3"),
    # S2a walk isochrones
    "iso_walk10_pop": dict(description="Population within 800 m NETWORK walk of hex activity centroid (node-field demand, k=4 multi-source Dijkstra)", units="persons", source_stage="S2a"),
    "iso_walk10_spend": dict(description="iso pop × PA affluence index — catchment spending proxy", units="persons-weighted", source_stage="S2a"),
    "iso_reached_node_n": dict(description="Walk-graph nodes reached within budget (QA)", units="count", source_stage="S2a"),
    "iso_walk10_places": dict(description="Exact place points reached within 800 m network walk", units="count", source_stage="S2a"),
    "iso_walk10_magnets": dict(description="Magnet anchors reached within the walk catchment", units="count", source_stage="S2a"),
    "iso_euclid800_pop": dict(description="Euclid-800m baseline pop on the same node field", units="persons", source_stage="S2a"),
    "iso_severance_ratio": dict(description="network pop / euclid pop. Ideal grid ≈0.55 (detour²); low = barriers. NaN where euclid pop < 200", units="ratio", source_stage="S2a"),
    "iso_snap_dist_m": dict(description="Activity-origin snap distance to walk graph (QA)", units="m", source_stage="S2a"),
    # S2b transit isochrones
    "iso_transit15_pop": dict(description="Population reachable door-to-door in 15 min weekday-AM transit (GTFS route-dir-stop graph + walk arms)", units="persons", source_stage="S2b"),
    "iso_transit15_places": dict(description="Places (hex9 pc_total) within the 15-min transit reach", units="count", source_stage="S2b"),
    "iso_transit15_hex9_n": dict(description="hex9 cells reached in 15 min", units="count", source_stage="S2b"),
    "iso_transit15_stops_used": dict(description="Transit stops reachable within 15 min (network-access measure)", units="count", source_stage="S2b"),
    # S1 Huff capture
    "cap_total": dict(description="Sum of per-category Huff capture: demand (outlet-equivalents) a NEW outlet at the best hex9 in this hex would win vs existing competition. λ ASSUMED (500/700/1000/1500m priors; not identifiable from data — rankings λ-robust ρ≥0.83)", units="outlet-equivalents", source_stage="S1"),
    "cap_best_category": dict(description="Category with the highest capture at this hex", units="category", source_stage="S1"),
    # S4 ACRA
    "biz_live_count": dict(description="ACRA live ('Registered') entities at building-precise postals (offline OneMap dump, 94.2% coverage)", units="count", source_stage="S4"),
    "biz_live_robust": dict(description="Live count with per-postal contribution winsorized at 100 — registered-agent buildings (Paya Lebar Sq 19K/postal) damped", units="count", source_stage="S4"),
    "biz_total_ever": dict(description="All entities ever registered (live + dead)", units="count", source_stage="S4"),
    "biz_formation_5y": dict(description="Entities issued in the last 5 years (any status)", units="count", source_stage="S4"),
    "biz_dead_share": dict(description="Deregistered / total ever — LIFETIME mortality (no cessation dates in ACRA). NaN where no entities", units="ratio", source_stage="S4"),
    "biz_recent_dead_share": dict(description="Dead share among 2018+ cohort (closer to churn). NaN where no 2018+ entities", units="ratio", source_stage="S4"),
    "biz_median_age_yrs": dict(description="Median age of live entities", units="years", source_stage="S4"),
    "biz_per_address": dict(description="Live entities per unique postal — high = corporate-secretary building (City Hall 109–131)", units="count/address", source_stage="S4"),
    "biz_company_share": dict(description="'Local Company' share of live entities (formality mix)", units="ratio", source_stage="S4"),
    "biz_density_per_km2": dict(description="Live entities per km²", units="count/km2", source_stage="S4"),
    # S5 labor shed
    "labor_pool_30m": dict(description="Working-age pop reaching this hex within 30-min weekday-AM transit", units="persons", source_stage="S5"),
    "labor_pool_45m": dict(description="Working-age pop within 45-min transit (CBD 1.68M = 59.6% of workforce; Tuas p0)", units="persons", source_stage="S5"),
    "jobs_reach_45m": dict(description="Job proxy (office+industrial+services places, scaled 2.4M) within 45 min", units="jobs", source_stage="S5"),
    "labor_accessibility_pct": dict(description="labor_pool_45m / national working-age pop", units="ratio", source_stage="S5"),
    "labor_jobs_balance_45m": dict(description="jobs_reach / labor_pool — divergence flags job-rich/transit-poor (Jurong Island, Tuas)", units="ratio", source_stage="S5"),
    # S7 visibility
    "vis_exit_footfall": dict(description="Weekday taps at nearest MRT/LRT exit ≤400 m, split per exit from per-station PV. Few-exit busy stations beat 13-exit Orchard", units="taps/day", source_stage="S7"),
    "vis_exit_station": dict(description="Name of that nearest station", units="string", source_stage="S7"),
    "vis_dist_exit_origin_m": dict(description="Activity origin → nearest exit distance", units="m", source_stage="S7"),
    "vis_main_road_m": dict(description="LTA speed-band cat A/B segment length in hex", units="m", source_stage="S7"),
    "vis_traffic_pass_proxy": dict(description="Σ road-category weights over speed-band segments — drive-past exposure", units="index", source_stage="S7"),
    "vis_corner_premium": dict(description="Signalized crossings × main-road presence", units="count", source_stage="S7"),
    # S8 rent
    "rent_resi_psf_med": dict(description="URA private-resi median rent (913 projects, last 4 quarters, IDW k=5 ≤2.5 km). COMMERCIAL rent not openly available. NaN = no observation in range", units="$psf/month", source_stage="S8"),
    "rent_resi_n_obs": dict(description="Projects within 2.5 km supporting the estimate", units="count", source_stage="S8"),
    "rent_resolution": dict(description="local (≤800 m) / idw / none", units="category", source_stage="S8"),
    # S9 pipeline
    "pipe_new_mrt_within_800m": dict(description="Future rail station (MP2019 minus existing Mar-2026; 37 stations: full JRL + Keppel CCL6) within 800 m", units="bool", source_stage="S9"),
    "pipe_mrt_name": dict(description="Nearest future station name", units="string", source_stage="S9"),
    "pipe_mrt_dist_m": dict(description="Distance to nearest future rail station", units="m", source_stage="S9"),
    "pipe_dev_capacity_res": dict(description="FAR headroom (avg_gpr − est_built_far)⁺ × residential zoning share. Matilda 0.50 / Bidadari 0.34 / built-out Toa Payoh Ctrl 0", units="FAR-units", source_stage="S9"),
    "pipe_dev_capacity_com": dict(description="FAR headroom × (commercial + mixed) zoning share", units="FAR-units", source_stage="S9"),
})
DESCRIPTIONS.update({
    "cat_a": dict(description="Anchor category A (lift = how much B over-concentrates near A)", units="category", source_stage="S6"),
    "cat_b": dict(description="Partner category B", units="category", source_stage="S6"),
    "lift": dict(description="mean count of B within 400 m of A-places ÷ category-blind base over all places. >1 = B seeks A (bar→bar 3.0); <1 = avoidance (industrial→residential 0.50)", units="ratio", source_stage="S6"),
    "ci_lo": dict(description="Bootstrap 95% CI lower (200 resamples of the A-set)", units="ratio", source_stage="S6"),
    "ci_hi": dict(description="Bootstrap 95% CI upper", units="ratio", source_stage="S6"),
    "significant": dict(description="CI excludes 1.0 — only these pairs enter colo_fit scores", units="bool", source_stage="S6"),
})
DESCRIPTIONS.update({
    # S10 context pack (integrated nous external sources)
    "cons_bldg_count": dict(description="URA conserved buildings in hex (MP2019 SDCP layer, 7,235 islandwide) — shophouse/heritage density", units="count", source_stage="S10"),
    "cons_cluster_flag": dict(description=">=20 conserved buildings — heritage shophouse cluster (Chinatown, Little India, Jalan Besar belt)", units="bool", source_stage="S10"),
    "carpark_count_hdb": dict(description="HDB carparks in hex (HDB Carpark Information)", units="count", source_stage="S10"),
    "carpark_capacity_lots": dict(description="Summed car-lot CAPACITY (live availability total_lots, lot type C; 696K national)", units="lots", source_stage="S10"),
    "polyclinic_count": dict(description="Public polyclinics in hex (27 islandwide)", units="count", source_stage="S10"),
    "dist_polyclinic_m": dict(description="Centroid distance to nearest polyclinic — public primary-care competition signal", units="m", source_stage="S10"),
    "wet_market_count": dict(description="NEA market & food centres flagged as wet markets (63 of 129)", units="count", source_stage="S10"),
    "dist_wet_market_m": dict(description="Distance to nearest wet market — morning-circuit / grocery-substitution signal", units="m", source_stage="S10"),
    "petrol_station_count": dict(description="Fuel stations in hex (OSM, 201 islandwide)", units="count", source_stage="S10"),
    "dist_petrol_m": dict(description="Distance to nearest petrol station", units="m", source_stage="S10"),
    "coworking_count": dict(description="Coworking venues (places name-match, 171 islandwide; 40% CBD-core)", units="count", source_stage="S10"),
    "condo_project_count": dict(description="Private strata projects with transactions in hex (URA, 2,384)", units="count", source_stage="S10"),
    "condo_txn_units": dict(description="Units TRANSACTED across those projects — private-housing density weight, NOT stock", units="units", source_stage="S10"),
    "female_pop_share": dict(description="Female share of resident pop (SingStat 2025, subzone-broadcast). NaN = zero-population subzone; tiny subzones can skew genuinely", units="ratio", source_stage="S10"),
    "bto_uc_units_town": dict(description="FY2024 HDB units under construction in the hex's town (town-broadcast; Kallang/Whampoa 11.5K, Tengah 11.1K top)", units="units", source_stage="S10"),
    "bto_pipeline_est": dict(description="Town under-construction units allocated within town by FAR headroom share — MODELED estate-growth estimate", units="units", source_stage="S10"),
})
_SS_CATS = ["cafe_coffee", "restaurant", "hawker", "fast_food", "supermarket",
            "convenience", "fitness_recreation", "health_medical",
            "beauty_personal", "shopping_retail", "education"]
for _c in _SS_CATS:
    DESCRIPTIONS[f"cap_{_c}"] = dict(
        description=f"Huff capture for a NEW {_c} outlet (outlet-equivalents vs existing competition; 1.0 = supports one average outlet)",
        units="outlet-equivalents", source_stage="S1")
    DESCRIPTIONS[f"colo_fit_{_c}"] = dict(
        description=f"Co-location mix-match for {_c}: Σ log lift(c,B) × share of B in the 400 m place mix (count-based lift, bootstrap-significant pairs only)",
        units="log-lift", source_stage="S6")
for _c in ["cafe_coffee", "supermarket", "restaurant", "fitness_recreation"]:
    DESCRIPTIONS[f"iso_walk10_unserved_pop_{_c}"] = dict(
        description=f"Catchment residents with NO {_c} within 800 m euclid of home — network-precise underserved demand",
        units="persons", source_stage="S2a")
    DESCRIPTIONS[f"iso_walk10_competitors_{_c}"] = dict(
        description=f"Existing {_c} outlets inside the 800 m walk catchment",
        units="count", source_stage="S2a")
for _c in ["total", "cafe_coffee", "supermarket", "restaurant", "shopping_retail"]:
    DESCRIPTIONS[f"roi_cap_per_rent_{_c}"] = dict(
        description=f"cap_{_c} / rent_resi_psf_med — opportunity per occupancy-cost proxy (rank heuristic). NaN where no rent",
        units="ratio", source_stage="S8")


DESCRIPTIONS.update({
    "pop_dorm": dict(description="Migrant-worker dormitory population at real MOM dorm locations (439,198 national, DASL H2-2024); subset of non-resident", units="persons", source_stage="3c"),
    "n_children": dict(description="Child count used as dasymetric denominator (bookkeeping)", units="persons", source_stage="3"),
    "pc_total": dict(description="Total mapped places (POIs) in cell — overall point-of-interest density", units="count", source_stage="1"),
    "pc_unique_brands": dict(description="Distinct retail/F&B brands present — chain richness", units="count", source_stage="1"),
    "pc_magnets": dict(description="High-draw anchor places (malls, hubs, 30+ review demand magnets)", units="count", source_stage="1"),
    "pc_long_tail": dict(description="Places with few/no reviews — independent long-tail share base", units="count", source_stage="1"),
    "pc_with_rating": dict(description="Places carrying a Google rating", units="count", source_stage="1"),
    "pc_total_reviews": dict(description="Sum of review counts — popularity/footfall proxy", units="count", source_stage="1"),
    "pc_avg_rating": dict(description="Mean rating of rated places — quality proxy", units="stars", source_stage="1"),
    "pc_diversity": dict(description="Category entropy of the place mix — high = mixed-use", units="0-1", source_stage="1"),
    "pc_dominant_category": dict(description="Most common place category in cell", units="category", source_stage="1"),
    "primary_school_zone_count": dict(description="Primary-school zones overlapping cell", units="count", source_stage="8"),
    "in_primary_school_zone": dict(description="Cell intersects a primary-school zone", units="bool", source_stage="8"),
    "in_silver_zone": dict(description="Cell intersects an elderly-priority Silver Zone", units="bool", source_stage="8"),
    "vibrancy_index": dict(description="Composite: places + magnets + reviews + transit + night lights", units="0-1", source_stage="12"),
    "livability_index": dict(description="Composite: walkability + green + amenities + transit", units="0-1", source_stage="12"),
    "commercial_intensity": dict(description="Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share", units="0-1", source_stage="12"),
    "family_index": dict(description="Composite: children + schools + preschools + family amenities", units="0-1", source_stage="12"),
    "density_pressure": dict(description="Composite: population + buildings + low road space", units="0-1", source_stage="12"),
    "accessibility_composite": dict(description="Composite access score across transit + walk + road reach", units="0-1", source_stage="12"),
    "mg_avg_competitors_400m": dict(description="Magnet model: mean same-category competitor count within 400 m across categories", units="count", source_stage="10"),
    "mg_avg_walk_dist_mrt_m": dict(description="Magnet model: mean walk distance to MRT across category micrographs", units="m", source_stage="10"),
    "walk_score_avg": dict(description="Mean of the 9 amenity walk-access scores", units="0-1", source_stage="7w"),
    "osm_amenities_count": dict(description="OSM amenity-tagged POIs in cell (independent ground truth)", units="count", source_stage="osm"),
    "osm_leisure_count": dict(description="OSM leisure-tagged POIs in cell", units="count", source_stage="osm"),
    "osm_shops_count": dict(description="OSM shop-tagged POIs in cell — independent retail frontage", units="count", source_stage="osm"),
    "osm_tourism_count": dict(description="OSM tourism-tagged POIs in cell", units="count", source_stage="osm"),
    "commercial_activity_index": dict(description="Footfall-weighted economic activity: night lights + spend proxy + transit taps + place density + OD throughput (distinct from supply-only commercial_intensity, corr 0.84)", units="0-1", source_stage="13"),
    # subzone-scale + bookkeeping one-offs
    "n_hex8": dict(description="Number of hex8 children (bookkeeping)", units="count", source_stage="0"),
    "n_hex8_tr": dict(description="hex8 children with transit data (bookkeeping)", units="count", source_stage="5c"),
    "n_hex8_wk": dict(description="hex8 children with walkability data (bookkeeping)", units="count", source_stage="7w"),
    "n_children_wk": dict(description="hex9 children with walk data (bookkeeping)", units="count", source_stage="7w"),
    "subzone_area_m2": dict(description="Subzone polygon area", units="m2", source_stage="0"),
    "subzone_area_km2": dict(description="Subzone polygon area", units="km2", source_stage="0"),
    "has_mrt": dict(description="Subzone contains at least one MRT/LRT station", units="bool", source_stage="5"),
    "has_interchange": dict(description="Subzone contains an interchange station", units="bool", source_stage="5"),
    "n_interchanges": dict(description="Interchange stations in subzone", units="count", source_stage="5"),
    "max_transit_score": dict(description="Best hex8 transit score within subzone", units="0-1", source_stage="5c"),
    "expressway_in_subzone": dict(description="An expressway segment crosses the subzone", units="bool", source_stage="6"),
    "archetype_id": dict(description="k-means (K=8) urban archetype cluster id", units="id", source_stage="11"),
    "archetype_label": dict(description="Human label of the archetype cluster", units="category", source_stage="11"),
    "archetype_dist": dict(description="Distance to archetype centroid (typicality)", units="z", source_stage="11"),
    "has_rating": dict(description="Place carries a Google rating", units="bool", source_stage="1"),
    "has_reviews": dict(description="Place carries at least one review", units="bool", source_stage="1"),
    "review_bucket": dict(description="Review-volume tier of the place", units="category", source_stage="1"),
    "parent_subzone_c": dict(description="URA subzone code of parent", units="string", source_stage="0"),
    "parent_subzone_source": dict(description="How the place→subzone attach was resolved (bookkeeping)", units="category", source_stage="1"),
    "signalized_crossing_count_wk": dict(description="Signalized pedestrian crossings (walk-layer copy)", units="count", source_stage="6"),
    "avg_floors": dict(description="Mean building floors in cell", units="floors", source_stage="2"),
    "avg_height": dict(description="Mean building height in cell", units="m", source_stage="2"),
    "outbound_influence": dict(description="Gravity-decayed influence the cell exerts on neighbours (hex9 influence model)", units="index", source_stage="9"),
    "net_influence": dict(description="Outbound minus inbound influence (hex9 influence model)", units="index", source_stage="9"),
    "inbound_influence": dict(description="Gravity-decayed influence neighbours exert on the cell (hex9 influence model)", units="index", source_stage="9"),
    "brand": dict(description="Raw brand string of the place (pre-normalisation)", units="string", source_stage="1"),
    "in_sgp": dict(description="Place lies within Singapore boundary (QA flag)", units="bool", source_stage="1"),
    "latitude": dict(description="Place latitude (WGS84)", units="degrees", source_stage="1"),
    "longitude": dict(description="Place longitude (WGS84)", units="degrees", source_stage="1"),
    "max_floors": dict(description="Tallest building floors in cell", units="floors", source_stage="2"),
    "max_height": dict(description="Tallest building height in cell", units="m", source_stage="2"),
    "n_children_tr": dict(description="hex9 children with transit data (bookkeeping)", units="count", source_stage="5c"),
})

# ===== Pattern-derived descriptions (fallback when no curated entry) =====
# Covers the big templatable families (mg_/pc_/pc2_/nvp_/aggregates/...) that
# were previously blank auto-rows. Tagged desc_source="pattern" vs "curated".

_AGG = {"ring1_": "Sum over H3 ring-1 neighbours (~±1 km) of: ",
        "ring2_": "Sum over H3 ring-2 neighbours (~±2 km) of: ",
        "pw1_": "Proximity-weighted (distance-decayed) ring-1 aggregate of: ",
        "pw2_": "Proximity-weighted ring-2 aggregate of: ",
        "max1_": "Max over ring-1 neighbours of: ",
        "max2_": "Max over ring-2 neighbours of: "}


def _cat_label(c):
    return c.replace("_", " ")


def derive_description(col):
    import re as _re
    for p, lead in _AGG.items():
        if col.startswith(p):
            base = col[len(p):]
            inner = (DESCRIPTIONS.get(base, {}).get("description")
                     or derive_description(base) or _cat_label(base))
            return lead + inner.rstrip(".")
    m = _re.match(r"pc_cat_(\w+)$", col)
    if m:
        return f"Place count in cell: {_cat_label(m.group(1))} category (24-cat taxonomy)"
    m = _re.match(r"pc_pct_cat_(\w+)$", col)
    if m:
        return f"Share of cell's places that are {_cat_label(m.group(1))}"
    m = _re.match(r"pc2_cat_(\w+)_count$", col)
    if m:
        return f"Place count in cell: {_cat_label(m.group(1))} (55-cat fine taxonomy)"
    m = _re.match(r"pc2_(\w+)$", col)
    if m:
        return f"Fine-taxonomy place metric: {_cat_label(m.group(1))}"
    m = _re.match(r"mg_(\w+)_pressure_400m$", col)
    if m:
        return f"Magnet model: 400 m distance-decayed SAME-category competitive pressure for {_cat_label(m.group(1))}"
    m = _re.match(r"mg_(\w+)_support_400m$", col)
    if m:
        return f"Magnet model: complementary-category support density within 400 m for {_cat_label(m.group(1))} (demand context, not supply)"
    m = _re.match(r"mg_(\w+)_anchor_strength$", col)
    if m:
        return f"Magnet model: strength of the biggest {_cat_label(m.group(1))} anchor place nearby"
    m = _re.match(r"nvp_(\w+)$", col)
    if m:
        return f"NVIDIA Nemotron persona distribution: {_cat_label(m.group(1))} (PA-resolution broadcast)"
    m = _re.match(r"sat_(\w+)_per_1k$", col)
    if m:
        return f"Supply saturation: {_cat_label(m.group(1))} outlets per 1,000 residents"
    m = _re.match(r"gap_(\w+)$", col)
    if m:
        return f"Saturation gap for {_cat_label(m.group(1))}: actual minus expected per-1k supply (positive = oversupplied)"
    m = _re.match(r"bus_taps_(in|out)_(\w+)$", col)
    if m:
        return f"Daily bus tap-{'ins' if m.group(1)=='in' else 'outs'} in the {m.group(2)} time window (LTA PV)"
    m = _re.match(r"gtfs_(\w+)$", col)
    if m:
        return f"GTFS-derived transit service metric: {_cat_label(m.group(1))} (weekday schedule)"
    m = _re.match(r"od_(\w+)$", col)
    if m:
        return f"LTA origin-destination flow metric: {_cat_label(m.group(1))} (weekday monthly, bus+train)"
    m = _re.match(r"walk_(\w+)_score$", col)
    if m:
        return f"Walk-access score to nearest {_cat_label(m.group(1))} (distance-decayed)"
    m = _re.match(r"dist_walk_(\w+)_m$", col)
    if m:
        return f"Network walk distance to nearest {_cat_label(m.group(1))}"
    m = _re.match(r"nearest_(\w+)_dist_m$", col)
    if m:
        return f"Distance to nearest {_cat_label(m.group(1))}"
    m = _re.match(r"(\w+)_within_(\d+k?m)$", col)
    if m:
        return f"Count of {_cat_label(m.group(1))} within {m.group(2)}"
    m = _re.match(r"pull_(\w+)$", col)
    if m:
        return f"Gravity pull toward {_cat_label(m.group(1))} (distance-decayed attraction)"
    m = _re.match(r"syn_(\w+)$", col)
    if m:
        return f"Synergy interaction term: {_cat_label(m.group(1))} (cross-feature product)"
    m = _re.match(r"(road|lane|ped|sig|centr)_(\w+)$", col)
    if m:
        return f"Road-network metric: {_cat_label(col)}"
    m = _re.match(r"(wc|sat|nl|ca)_(\w+)$", col)
    if m:
        fam = {"wc": "ESA WorldCover land-cover share",
               "nl": "VIIRS night-light metric",
               "ca": "Commercial-activity component",
               "sat": "Satellite-derived metric"}[m.group(1)]
        return f"{fam}: {_cat_label(m.group(2))}"
    m = _re.match(r"(bldg|hdb|lu|school|preschool|hawker|chas|silver|tourist|carpark|speed|jam|dyn|est)_(\w+)$", col)
    if m:
        return f"{_cat_label(col)} (see layer docs)"
    return ""


# ===== Datasets to catalog =====
DATASETS = [
    # (file, scale, description, owner_stage)
    ("hex/hex9_universe.parquet",        "hex9",   "Hex-9 cell universe (7,318 cells across SGP)", "0"),
    ("hex/hex8_universe.parquet",        "hex8",   "Hex-8 cell universe (1,191 cells)", "0"),
    ("hex/hex9_population.parquet",      "hex9",   "Population (residents + non-residents) per hex-9", "3+3b"),
    ("hex/hex9_land_use.parquet",        "hex9",   "URA land-use 14-bucket shares per hex-9", "4"),
    ("hex/hex9_buildings.parquet",       "hex9",   "Buildings (counts, classes, floors, HDB) per hex-9", "2"),
    ("hex/hex9_roads_clean.parquet",     "hex9",   "Roads + parking + centrality (clean) per hex-9", "6+6c"),
    ("hex/hex8_roads_clean.parquet",     "hex8",   "Roads + parking + centrality aggregated to hex-8", "6c"),
    ("hex/subzone_roads_clean.parquet",  "subzone","Roads + parking + centrality aggregated to subzone", "6c"),
    ("hex/hex9_transit_clean.parquet",   "hex9",   "Transit (MRT/LRT/bus/GTFS/ridership) per hex-9", "5+5c"),
    ("hex/hex8_transit_clean.parquet",   "hex8",   "Transit aggregated to hex-8", "5c"),
    ("hex/subzone_transit_clean.parquet","subzone","Transit aggregated to subzone", "5c"),
    ("hex/hex9_walkability.parquet",     "hex9",   "Walkability composite + amenity walk distances per hex-9", "7w"),
    ("hex/hex8_walkability.parquet",     "hex8",   "Walkability aggregated to hex-8", "7w"),
    ("hex/subzone_walkability.parquet",  "subzone","Walkability aggregated to subzone", "7w"),
    ("hex/hex9_mobility_features.parquet",   "hex9",   "BUNDLE — roads + transit + walkability per hex-9", "56"),
    ("hex/hex8_mobility_features.parquet",   "hex8",   "BUNDLE — roads + transit + walkability aggregated to hex-8", "56"),
    ("hex/subzone_mobility_features.parquet","subzone","BUNDLE — roads + transit + walkability aggregated to subzone", "56"),
    ("hex/hex9_buildings_clean.parquet",     "hex9",   "Buildings clean (clipped, est-FAR, HDB age) per hex-9", "2c"),
    ("hex/hex8_buildings_clean.parquet",     "hex8",   "Buildings clean aggregated to hex-8", "2c"),
    ("hex/subzone_buildings_clean.parquet",  "subzone","Buildings clean aggregated to subzone", "2c"),
    ("hex/hex9_built_environment_features.parquet",   "hex9",   "BUNDLE — buildings + land_use per hex-9", "24"),
    ("hex/hex8_built_environment_features.parquet",   "hex8",   "BUNDLE — buildings + land_use aggregated to hex-8", "24"),
    ("hex/subzone_built_environment_features.parquet","subzone","BUNDLE — buildings + land_use aggregated to subzone", "24"),
    # Standalone gap-fillers
    ("hex/hex8_population.parquet",      "hex8",   "Population aggregated to hex-8", "3agg"),
    ("hex/subzone_population.parquet",   "subzone","Population aggregated to subzone", "3agg"),
    ("hex/hex8_land_use.parquet",        "hex8",   "URA land-use aggregated to hex-8 (area-weighted)", "4agg"),
    ("hex/subzone_land_use.parquet",     "subzone","URA land-use aggregated to subzone (area-weighted)", "4agg"),
    # Satellite (Stage 5b)
    ("hex/hex9_satellite.parquet",       "hex9",   "VIIRS night lights + WorldPop per hex-9", "5b"),
    ("hex/hex8_satellite.parquet",       "hex8",   "VIIRS + WorldPop aggregated to hex-8", "5b"),
    ("hex/subzone_satellite.parquet",    "subzone","VIIRS + WorldPop aggregated to subzone", "5b"),
    # Site-selection layers S1-S9 (v5.0.0)
    ("hex/hex8_daytime_pop.parquet",     "hex8",   "S3 daytime population from LTA OD AM window (dt_*)", "S3"),
    ("hex/hex8_iso_walk.parquet",        "hex8",   "S2a 10-min walk isochrone catchments (iso_walk10_*; node-field demand, activity origins)", "S2a"),
    ("hex/hex8_iso_transit.parquet",     "hex8",   "S2b 15-min weekday-AM transit reach (iso_transit15_*; GTFS route-dir-stop graph)", "S2b"),
    ("hex/hex9_huff_capture.parquet",    "hex9",   "S1 Huff capture potential per hex-9 (cap_*, 11 categories, outlet-equivalents)", "S1"),
    ("hex/hex8_huff_capture.parquet",    "hex8",   "S1 Huff capture rolled to hex-8 (MAX over children = best site)", "S1"),
    ("hex/hex8_acra_biz.parquet",        "hex8",   "S4 ACRA business formation & churn (biz_*; 1.95M entities geocoded via offline OneMap dump)", "S4"),
    ("hex/hex9_colo_fit.parquet",        "hex9",   "S6 co-location mix-match fit per hex-9 (colo_fit_*)", "S6"),
    ("hex/hex8_colo_fit.parquet",        "hex8",   "S6 co-location fit rolled to hex-8 (MAX over children)", "S6"),
    ("catalog/colo_lift_matrix.parquet", "matrix", "S6 24×24 count-based co-location lift matrix with bootstrap CIs", "S6"),
    ("hex/hex8_labor_shed.parquet",      "hex8",   "S5 labor pool / jobs reach within 30/45-min transit (labor_*)", "S5"),
    ("hex/hex8_visibility.parquet",      "hex8",   "S7 MRT-exit footfall + traffic exposure (vis_*)", "S7"),
    ("hex/hex8_rent_surface.parquet",    "hex8",   "S8 URA resi rent surface + capture-per-rent ROI (rent_*, roi_*)", "S8"),
    ("hex/hex8_pipeline.parquet",        "hex8",   "S9 future rail (MP19 delta, 37 stations) + FAR-headroom dev capacity (pipe_*)", "S9"),
    ("hex/hex8_context_pack.parquet",    "hex8",   "S10 context pack: conservation/shophouse, carpark capacity, polyclinics, wet markets, petrol, coworking, condos, female share, BTO pipeline", "S10"),
    # Master bundles
    ("hex/hex9_all_features.parquet",    "hex9",   "MASTER — all standalone layers joined per hex-9", "all"),
    ("hex/hex8_all_features.parquet",    "hex8",   "MASTER — all standalone layers joined per hex-8", "all"),
    ("hex/subzone_all_features.parquet", "subzone","MASTER — all standalone layers joined per subzone", "all"),
    ("places/sgp_places_final.parquet",  "place",  "Stage-1 deliverable: 190,591 places × 27 cols (geo + cat + brand + quality)", "1"),
]


def main():
    t0 = time.time()
    print(f"Building catalogs into {CAT}/")

    feature_rows = []
    dataset_rows = []

    for path_rel, scale, desc, owner in DATASETS:
        path = ROOT / path_rel
        if not path.exists():
            print(f"  MISSING: {path_rel}")
            dataset_rows.append({
                "dataset": path_rel, "scale": scale, "description": desc,
                "owner_stage": owner, "exists": False, "n_rows": 0, "n_cols": 0, "size_bytes": 0,
            })
            continue
        df = pd.read_parquet(path)
        size = path.stat().st_size
        join_key = next((c for c in ["hex9_id", "hex8_id", "subzone_c", "id"] if c in df.columns), None)
        dataset_rows.append({
            "dataset": path_rel,
            "scale": scale,
            "description": desc,
            "owner_stage": owner,
            "exists": True,
            "n_rows": int(len(df)),
            "n_cols": int(len(df.columns)),
            "size_bytes": int(size),
            "join_key": join_key,
        })
        for col in df.columns:
            s = df[col]
            row = {
                "dataset": path_rel,
                "scale": scale,
                "column": col,
                "dtype": str(s.dtype),
                "null_pct": round(100 * s.isna().mean(), 2),
            }
            # Curated metadata first; pattern-derived fallback for families
            curated = DESCRIPTIONS.get(col, {})
            desc = curated.get("description", "")
            if desc:
                row["desc_source"] = "curated"
            else:
                desc = derive_description(col)
                row["desc_source"] = "pattern" if desc else "none"
            row["description"] = desc
            row["units"] = curated.get("units", "")
            row["source_stage"] = curated.get("source_stage", owner)
            row["derivation"] = curated.get("derivation", "")
            # Add quick stats
            if pd.api.types.is_numeric_dtype(s):
                vals = s.dropna()
                if len(vals):
                    row["min"] = float(vals.min())
                    row["max"] = float(vals.max())
                    row["mean"] = round(float(vals.mean()), 4)
                    row["median"] = round(float(vals.median()), 4)
            elif pd.api.types.is_bool_dtype(s):
                row["true_pct"] = round(100 * s.sum() / len(s), 2)
            else:
                # categorical / string
                row["n_unique"] = int(s.nunique())
                samp = s.dropna().head(1)
                row["sample"] = str(samp.iloc[0])[:80] if len(samp) else ""
            feature_rows.append(row)
        print(f"  {path_rel}: {len(df):,} × {len(df.columns)} cols  ({len(df.columns)} cataloged)")

    # === Save ===
    df_ds = pd.DataFrame(dataset_rows)
    df_feat = pd.DataFrame(feature_rows)

    df_ds.to_parquet(CAT / "dataset_catalog.parquet", index=False)
    df_feat.to_parquet(CAT / "feature_catalog.parquet", index=False)

    # Markdown rendering
    write_dataset_md(df_ds)
    write_feature_md(df_feat)

    # Summary
    print(f"\n=== Catalog summary ===")
    print(f"  Datasets cataloged: {len(df_ds):,}  (existing: {df_ds['exists'].sum()})")
    print(f"  Features cataloged: {len(df_feat):,}")
    print(f"  Curated descriptions matched: {(df_feat['description'] != '').sum()}/{len(df_feat)}")
    print(f"\nOutputs:")
    print(f"  {CAT}/dataset_catalog.parquet")
    print(f"  {CAT}/dataset_catalog.md")
    print(f"  {CAT}/feature_catalog.parquet")
    print(f"  {CAT}/feature_catalog.md")
    print(f"  Wall clock: {time.time()-t0:.1f}s")


def write_dataset_md(df):
    lines = ["# Plexis SGP v4 — Dataset Catalog", ""]
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M')} · **Datasets:** {len(df):,} ({df['exists'].sum()} existing)")
    lines.append("")
    by_scale = df.groupby("scale")
    for scale in ["hex9", "hex8", "subzone", "place"]:
        if scale not in by_scale.groups:
            continue
        sub = by_scale.get_group(scale).sort_values("dataset")
        lines.append(f"## scale = `{scale}`")
        lines.append("")
        lines.append("| Dataset | Rows × Cols | Join key | Owner | Description |")
        lines.append("|---|---|---|---|---|")
        for _, r in sub.iterrows():
            tag = "" if r["exists"] else " ❌MISSING"
            lines.append(f"| `{r['dataset']}`{tag} | {r['n_rows']:,} × {r['n_cols']} | `{r.get('join_key','—')}` | `{r['owner_stage']}` | {r['description']} |")
        lines.append("")
    (CAT / "dataset_catalog.md").write_text("\n".join(lines))


def write_feature_md(df):
    lines = ["# Plexis SGP v4 — Feature Catalog", ""]
    lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M')} · **Features:** {len(df):,}")
    lines.append("")
    # Group by dataset, sort by column
    for dataset, sub in df.groupby("dataset"):
        sub = sub.sort_values("column")
        lines.append(f"## `{dataset}`")
        lines.append("")
        lines.append(f"_{len(sub)} columns_")
        lines.append("")
        lines.append("| Column | dtype | Units | Null % | Range / sample | Description |")
        lines.append("|---|---|---|---|---|---|")
        for _, r in sub.iterrows():
            stats = ""
            if "min" in r and pd.notna(r["min"]):
                stats = f"{r['min']:.4g} → {r['max']:.4g} (median {r['median']:.4g})"
            elif "n_unique" in r and pd.notna(r["n_unique"]):
                stats = f"{int(r['n_unique'])} unique · `{r.get('sample','')}`"
            elif "true_pct" in r and pd.notna(r["true_pct"]):
                stats = f"{r['true_pct']:.1f}% True"
            desc = r["description"] or ""
            units = r["units"] or ""
            lines.append(f"| `{r['column']}` | {r['dtype']} | {units} | {r['null_pct']:.1f} | {stats} | {desc} |")
        lines.append("")
    (CAT / "feature_catalog.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()

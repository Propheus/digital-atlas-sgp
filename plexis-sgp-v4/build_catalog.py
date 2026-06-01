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
            # Add curated metadata if available
            curated = DESCRIPTIONS.get(col, {})
            row["description"] = curated.get("description", "")
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

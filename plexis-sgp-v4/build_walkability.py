"""
Plexis SGP v4 — Walkability per hex.

Combines pedestrian infrastructure with amenity walk-distance to produce a
single composite walkability score per hex.

Inputs (already in v4):
  hex/hex9_roads_raw.parquet       — has per-class lengths (footway, path, cycleway, steps)
  hex/hex9_roads_clean.parquet     — intersection density, signalized crossings, expressway flags
  hex/hex9_transit_clean.parquet   — near_mrt/bus flags
  places/sgp_places_final.parquet  — 190K places with hex9_id and plexis_category

External (atlas-1):
  data/amenities/parks_nature_reserves.geojson   — 450 parks (use polygons)
  data/amenities/park_connector.geojson          — 883 PCN segments

Output:
  hex/hex9_walkability.parquet  (~14 cols)
  hex/hex8_walkability.parquet
  hex/subzone_walkability.parquet
"""
import json, os, time
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
import h3

ROOT = Path(__file__).parent

def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError

DATA = _resolve_data_root()
PARKS_GEO = DATA / "amenities/parks_nature_reserves.geojson"
PCN_GEO = DATA / "amenities/park_connector.geojson"

OUT_H9 = ROOT / "hex/hex9_walkability.parquet"
OUT_H8 = ROOT / "hex/hex8_walkability.parquet"
OUT_SZ = ROOT / "hex/subzone_walkability.parquet"
REPORT = ROOT / "hex/walkability_report.json"

HEX_AREA_KM2 = 0.105
DETOUR = 1.3   # Euclidean × 1.3 ≈ network walk distance in dense urban grid


def main():
    t0 = time.time()
    print("Loading inputs...")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    rd_raw = pd.read_parquet(ROOT / "hex/hex9_roads_raw.parquet")
    rd_clean = pd.read_parquet(ROOT / "hex/hex9_roads_clean.parquet")
    tr_clean = pd.read_parquet(ROOT / "hex/hex9_transit_clean.parquet")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
    print(f"  h9 {len(h9):,}  rd_raw {rd_raw.shape}  places {places.shape}")

    # === Hex centroids in 3414 ===
    print("\n  Building hex centroids (3414)...")
    hex_polys = []
    for hid in h9["hex9_id"]:
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hid)]
        hex_polys.append(Polygon(ring))
    h9_gdf = gpd.GeoDataFrame({"hex9_id": h9["hex9_id"]}, geometry=hex_polys, crs=4326).to_crs(3414)
    h9_cent = h9_gdf.geometry.centroid

    # === Pedestrian infrastructure (from raw roads) ===
    print("  Pedestrian path lengths (footway + path + cycleway + steps)...")
    ped_cols = ["road_footway_length_m", "road_path_length_m",
                 "road_cycleway_length_m", "road_steps_length_m"]
    available = [c for c in ped_cols if c in rd_raw.columns]
    rd_raw["ped_path_length_m"] = rd_raw[available].sum(axis=1)
    print(f"    used cols: {available}")

    # === Places by category to walkable points ===
    print("\n  Building amenity point sets from places...")
    AMENITY_GROUPS = {
        "hawker":      ["hawker"],
        "clinic":      ["health_medical"],
        "supermarket": ["supermarket"],
        "school":      ["education"],
        "food":        ["restaurant", "cafe_coffee", "hawker", "bakery", "fast_food"],
        "convenience": ["convenience"],
    }
    amenity_geoms = {}
    for group, cats in AMENITY_GROUPS.items():
        sub = places[places["plexis_category"].isin(cats)].dropna(subset=["latitude", "longitude"])
        if len(sub) == 0:
            amenity_geoms[group] = []
            continue
        gdf = gpd.GeoDataFrame(sub[["id"]],
                                 geometry=gpd.points_from_xy(sub["longitude"], sub["latitude"]),
                                 crs=4326).to_crs(3414)
        amenity_geoms[group] = list(gdf.geometry.values)
        print(f"    {group}: {len(amenity_geoms[group]):,} points")

    # Parks from polygons
    print("  Park polygons from amenities/parks_nature_reserves.geojson...")
    parks = gpd.read_file(PARKS_GEO).to_crs(3414)
    amenity_geoms["park"] = list(parks.geometry.values)
    print(f"    park: {len(amenity_geoms['park']):,} polygons")

    # === Per-hex distance to nearest amenity ===
    print("\n  Computing nearest-amenity distances...")
    def nearest_dist(centroids, target_geoms):
        if not target_geoms:
            return [np.nan] * len(centroids)
        tree = STRtree(target_geoms)
        out = []
        for c in centroids:
            idx = tree.nearest(c)
            d = c.distance(target_geoms[idx])
            out.append(d * DETOUR)  # apply Euclidean→network detour factor
        return out

    walk_dists = {}
    for group, geoms in amenity_geoms.items():
        col = f"dist_walk_{group}_m"
        walk_dists[col] = nearest_dist(h9_cent.values, geoms)
        print(f"    dist_walk_{group}_m: median {np.median([d for d in walk_dists[col] if not np.isnan(d)]):.0f}m")

    # === Amenity count within 400m walk (= 308m euclidean with 1.3 detour) ===
    print("\n  Counting amenities within 400m walk-distance...")
    EUCLID_THRESHOLD = 400 / DETOUR  # ~308m
    counts = {}
    for group, geoms in amenity_geoms.items():
        if not geoms:
            counts[f"walk_{group}_400m"] = [0] * len(h9_cent)
            continue
        tree = STRtree(geoms)
        col_counts = []
        for c in h9_cent.values:
            buf = c.buffer(EUCLID_THRESHOLD)
            idxs = tree.query(buf)
            n = sum(1 for i in idxs if c.distance(geoms[i]) <= EUCLID_THRESHOLD)
            col_counts.append(n)
        counts[f"walk_{group}_400m"] = col_counts

    # Total amenity count (any place within 400m)
    print("  Total places within 400m walk...")
    place_pts = places.dropna(subset=["latitude", "longitude"])
    place_geoms = list(gpd.GeoDataFrame(geometry=gpd.points_from_xy(
        place_pts["longitude"], place_pts["latitude"]), crs=4326).to_crs(3414).geometry.values)
    place_tree = STRtree(place_geoms)
    walk_total = []
    for c in h9_cent.values:
        buf = c.buffer(EUCLID_THRESHOLD)
        idxs = place_tree.query(buf)
        n = sum(1 for i in idxs if c.distance(place_geoms[i]) <= EUCLID_THRESHOLD)
        walk_total.append(n)

    # === Build output ===
    print("\n  Assembling walkability table...")
    out = h9[["hex9_id", "parent_hex8", "parent_subzone"]].copy()
    out = out.merge(rd_raw[["hex9_id", "ped_path_length_m"]], on="hex9_id", how="left")
    out["ped_path_length_m"] = out["ped_path_length_m"].fillna(0)
    out["ped_path_density_km_per_km2"] = out["ped_path_length_m"] / 1000 / HEX_AREA_KM2
    # Pull from clean roads
    out = out.merge(rd_clean[["hex9_id", "road_walkable_share", "road_intersection_density_per_km2",
                               "signalized_crossing_count", "dist_expressway_m",
                               "near_expressway_exit_400m"]], on="hex9_id", how="left")
    out = out.merge(tr_clean[["hex9_id", "near_mrt_400m", "near_bus_300m"]], on="hex9_id", how="left")
    # Walk distances
    h9_dists = pd.DataFrame({"hex9_id": h9["hex9_id"]})
    for col, vals in walk_dists.items():
        h9_dists[col] = vals
    out = out.merge(h9_dists, on="hex9_id", how="left")
    # Walk counts
    h9_counts = pd.DataFrame({"hex9_id": h9["hex9_id"]})
    for col, vals in counts.items():
        h9_counts[col] = vals
    h9_counts["walk_amenities_400m"] = walk_total
    out = out.merge(h9_counts, on="hex9_id", how="left")

    # Severance: expressway near but no exit
    out["expressway_severance"] = (out["dist_expressway_m"] < 200) & (~out["near_expressway_exit_400m"])

    # Composite walkability score (0-1)
    # Components:
    #  +0.20 ped_path_density (normalized 0 → 1 at 30 km/km²)
    #  +0.20 road_walkable_share
    #  +0.15 intersection density (normalized 0 → 1 at 200 / km²)
    #  +0.15 signalized_crossings (normalized 0 → 1 at 5 crossings)
    #  +0.10 walk_food_400m count (normalized 0 → 1 at 30 food places)
    #  +0.10 near_mrt_400m
    #  +0.05 near_bus_300m
    #  +0.05 walk_amenities_400m count (normalized 0 → 1 at 100)
    #  -0.15 expressway_severance penalty (binary)

    def n01(v, denom): return np.clip(v / denom, 0, 1)
    score = (
        0.20 * n01(out["ped_path_density_km_per_km2"], 30)
        + 0.20 * out["road_walkable_share"].fillna(0)
        + 0.15 * n01(out["road_intersection_density_per_km2"], 200)
        + 0.15 * n01(out["signalized_crossing_count"], 5)
        + 0.10 * n01(out["walk_food_400m"], 30)
        + 0.10 * out["near_mrt_400m"].astype(int)
        + 0.05 * out["near_bus_300m"].astype(int)
        + 0.05 * n01(out["walk_amenities_400m"], 100)
        - 0.15 * out["expressway_severance"].astype(int)
    )
    out["walkability_score"] = score.clip(0, 1)

    # Reorder
    out = out[[
        "hex9_id", "parent_hex8", "parent_subzone",
        # infrastructure
        "ped_path_length_m", "ped_path_density_km_per_km2",
        "road_walkable_share", "road_intersection_density_per_km2",
        "signalized_crossing_count",
        # transit access
        "near_mrt_400m", "near_bus_300m",
        # amenity walk distances
        "dist_walk_hawker_m", "dist_walk_clinic_m", "dist_walk_supermarket_m",
        "dist_walk_park_m", "dist_walk_school_m",
        "dist_walk_food_m", "dist_walk_convenience_m",
        # amenity counts within 400m walk
        "walk_amenities_400m", "walk_food_400m", "walk_hawker_400m",
        "walk_clinic_400m", "walk_supermarket_400m",
        "walk_park_400m", "walk_school_400m", "walk_convenience_400m",
        # severance
        "expressway_severance",
        # composite
        "walkability_score",
    ]]

    out.to_parquet(OUT_H9, index=False)
    print(f"\n  hex9_walkability: {out.shape}")

    # === Aggregate to hex-8 ===
    print("\n  Aggregating to hex-8...")
    h8 = out.groupby("parent_hex8").agg(
        n_children=("hex9_id", "count"),
        ped_path_length_m=("ped_path_length_m", "sum"),
        ped_path_density_km_per_km2=("ped_path_density_km_per_km2", "mean"),
        road_walkable_share=("road_walkable_share", "mean"),
        road_intersection_density_per_km2=("road_intersection_density_per_km2", "mean"),
        signalized_crossing_count=("signalized_crossing_count", "sum"),
        near_mrt_400m=("near_mrt_400m", "any"),
        near_bus_300m=("near_bus_300m", "any"),
        dist_walk_hawker_m=("dist_walk_hawker_m", "min"),
        dist_walk_clinic_m=("dist_walk_clinic_m", "min"),
        dist_walk_supermarket_m=("dist_walk_supermarket_m", "min"),
        dist_walk_park_m=("dist_walk_park_m", "min"),
        dist_walk_school_m=("dist_walk_school_m", "min"),
        dist_walk_food_m=("dist_walk_food_m", "min"),
        walk_amenities_400m=("walk_amenities_400m", "sum"),
        walk_food_400m=("walk_food_400m", "sum"),
        walk_hawker_400m=("walk_hawker_400m", "sum"),
        walk_park_400m=("walk_park_400m", "sum"),
        expressway_severance=("expressway_severance", "any"),
        walkability_score=("walkability_score", "mean"),
    ).reset_index().rename(columns={"parent_hex8": "hex8_id"})
    h8.to_parquet(OUT_H8, index=False)
    print(f"  hex8_walkability: {h8.shape}")

    # === Subzone aggregation ===
    print("  Aggregating to subzone...")
    h8_univ = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h8_with_sz = h8.merge(h8_univ[["hex8_id", "parent_subzone"]], on="hex8_id", how="left")
    sz = h8_with_sz.groupby("parent_subzone").agg(
        n_hex8=("hex8_id", "count"),
        ped_path_length_m=("ped_path_length_m", "sum"),
        road_walkable_share=("road_walkable_share", "mean"),
        signalized_crossing_count=("signalized_crossing_count", "sum"),
        walk_amenities_400m=("walk_amenities_400m", "sum"),
        walkability_score=("walkability_score", "mean"),
        expressway_severance=("expressway_severance", "any"),
    ).reset_index().rename(columns={"parent_subzone": "subzone_c"})
    sz.to_parquet(OUT_SZ, index=False)
    print(f"  subzone_walkability: {sz.shape}")

    # Top hexes
    h9_lookup = h9[["hex9_id", "parent_subzone_name", "parent_pa"]].rename(
        columns={"parent_subzone_name": "subz", "parent_pa": "pa"})
    top = out.nlargest(10, "walkability_score").merge(h9_lookup, on="hex9_id")
    print(f"\n=== Top 10 hexes by walkability_score ===")
    for _, r in top.iterrows():
        print(f"  score={r['walkability_score']:.3f}  ped/km²={r['ped_path_density_km_per_km2']:>5.1f}  "
              f"food400m={int(r['walk_food_400m']):>3}  "
              f"intxn={r['road_intersection_density_per_km2']:>5.0f}  "
              f"{str(r['subz']):<20} ({r['pa']})")

    bot = out[out["ped_path_length_m"] > 0].nsmallest(5, "walkability_score").merge(h9_lookup, on="hex9_id")
    print(f"\n=== Bottom 5 (least walkable, but with some ped infra) ===")
    for _, r in bot.iterrows():
        print(f"  score={r['walkability_score']:.3f}  severance={r['expressway_severance']}  "
              f"{str(r['subz']):<20} ({r['pa']})")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {"hex9": list(out.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
        "totals": {
            "hexes_with_ped_path": int((out["ped_path_length_m"] > 0).sum()),
            "median_walkability_score": float(out["walkability_score"].median()),
            "max_walkability_score": float(out["walkability_score"].max()),
            "hexes_with_severance": int(out["expressway_severance"].sum()),
        },
    }
    with open(REPORT, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

"""
Plexis SGP v4 — master pipeline runner.

Runs all stages end-to-end with timing + pass/fail tracking.
Designed to run on atlas-1 (or anywhere with source data accessible).

Usage:
    python3 run_pipeline.py            # full pipeline
    python3 run_pipeline.py --from 3   # resume from stage 3
    python3 run_pipeline.py --only 3   # only run stage 3
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent

STAGES = [
    # (id, label, script, validator)
    ("0",   "Hex universe (hex-9 + hex-8 from subzones)",   "build_hex_universe.py",     "validate_coverage.py"),
    ("0b",  "Post-sweep (close coverage gaps to 100%)",    "post_sweep.py",             "validate_coverage.py"),
    ("0c",  "Admin boundaries (PA, regions, HDB towns)",   "build_admin_boundaries.py", "validate_admin.py"),
    ("1a",  "Place geo-attach (hex + admin parents)",      "enrich_places.py",          None),
    ("1b1", "Category map (deterministic 166→24)",         "apply_category_map.py",     None),
    ("1b2", "Heuristic classifier (residue patterns)",     "apply_heuristics.py",       None),
    ("1bf", "Finalize categories (mark unresolved)",       "finalize_categories.py",    None),
    ("1c",  "Brand normalization + name detection",         "apply_brands.py",           None),
    ("1d",  "Quality / review signals",                    "apply_quality.py",          None),
    ("2",   "Buildings (Overture + HDB authoritative)",    "build_buildings.py",        "validate_buildings.py"),
    ("2c",  "Buildings clean (proper clipping + FAR + age)", "build_buildings_clean.py",  "validate_buildings_clean.py"),
    ("3",   "Population dasymetric (HDB units + area)",    "build_population.py",       "validate_population.py"),
    ("4",   "Land use (URA Master Plan → 14 buckets)",     "build_land_use.py",         "validate_land_use.py"),
    ("3b",  "Non-resident allocation (1.77M + V3 anchor)", "build_non_residents.py",    "validate_non_residents.py"),
    ("6",   "Roads + Parking (lengths, topology, motorway, lots, MSCPs)", "build_roads.py", "validate_roads.py"),
    ("6g",  "Road centrality (betweenness, closeness, PageRank, bridges)", "build_road_centrality.py", "validate_road_centrality.py"),
    ("6c",  "Roads cleanup → hex9/hex8/subzone (18 cols each)", "build_roads_clean.py",      None),
    ("5",   "Transit (MRT/LRT/bus/exits/rail/ridership)",  "build_transit.py",          "validate_transit.py"),
    ("5c",  "Transit cleanup → hex9/hex8/subzone",         "build_transit_clean.py",    None),
    ("7w",  "Walkability (ped infra + amenity walk-distance + composite)", "build_walkability.py",      None),
    ("56",  "mobility_features bundle (roads+parking+centrality+transit+walkability)", "build_mobility_features.py", None),
    ("24",  "built_environment_features bundle (buildings + land_use)", "build_built_environment_features.py", None),
    ("5b",  "Satellite (VIIRS night lights + WorldPop)",    "build_satellite.py",        "validate_satellite.py"),
    ("7",   "Place composition (190K places → hex/subzone)", "build_place_composition.py", "validate_place_composition.py"),
    ("7p",  "HDB resale prices (227K txns → hex/subzone)",   "build_hdb_resale.py",        "validate_hdb_resale.py"),
    ("7s",  "Schools (337 MOE schools + 211 catchment zones)", "build_schools.py",          "validate_schools.py"),
    ("9",   "Amenities extra (tourist + hawker + CHAS + preschool + silver)", "build_amenities_extra.py", "validate_amenities_extra.py"),
    ("10",  "Spatial rings (1-ring neighborhood context)",  "build_spatial_rings.py",     None),
    ("11",  "Composite indices (vibrancy, livability, family, ...)", "build_composites.py", "validate_composites.py"),
    ("12",  "Demand pull (gravity model, 6 destination types)", "build_demand_pull.py", "validate_demand_pull.py"),
    ("13",  "Synergy interactions (cross-feature products)",  "build_synergy.py",       None),
    ("14",  "Saturation / gap (supply-vs-demand by category)", "build_saturation_gap.py", None),
    ("15",  "Archetypes (k-means clustering, K=8)",           "build_archetypes.py",     None),
    ("16",  "Influence graph (gravity-decay outbound + inbound)", "build_influence.py",  None),
    ("17",  "Micrograph hex rollup (per-cat pressure/support/anchor)", "build_micrograph_hex_rollup.py", None),
    ("18",  "Walk scores (exp-decay per-amenity)",            "build_walk_scores.py",   None),
    ("19",  "OSM POI counts (amenities/leisure/shops/tourism)", "build_osm_pois.py",      None),
    ("20",  "ESA WorldCover landcover (built/tree/water/grass)", "build_landcover.py",     None),
    ("21",  "Pop-weighted spatial features (ring1+ring2, pw+max)", "build_pop_weighted.py", None),
    ("22",  "Traffic signals + ped crossings (LTA 44K signals)",  "build_traffic_signals.py", None),
    ("23",  "GTFS multi-window headways (am/midday/pm/night)",   "build_gtfs_windows.py",  None),
    ("24",  "Place composition V2 (55 finer categories)",        "build_place_composition_v2.py", None),
    ("25",  "LTA Datamall PV (bus + train time-of-day taps)",    "build_lta_pv.py",        None),
    ("26",  "LTA Datamall dynamic (carparks + speed bands)",     "build_lta_dynamic.py",   None),
    ("27",  "Embeddings: WHERE_AM_I 64d + WHAT_AM_I 64d + COMBINED 128d", "build_embeddings.py", "validate_embeddings.py"),
    ("8",   "Per-place micrograph (network walking distance)", "build_place_micrograph.py",  "validate_place_micrograph.py"),
    ("3agg", "Population aggregate hex9→hex8+subzone",       "build_population_aggregate.py", None),
    ("4agg", "Land use aggregate hex9→hex8+subzone",         "build_land_use_aggregate.py", None),
    ("all", "all_features MASTER bundle per scale",          "build_all_features.py",      None),
    ("cat", "Catalog: dataset_catalog + feature_catalog (parquet + md)", "build_catalog.py",          None),
]


def run(script):
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, str(ROOT / script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    dt = time.time() - t0
    return proc.returncode, dt, proc.stdout, proc.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", default=None,
                    help="Stage id to start from (e.g. 1a)")
    ap.add_argument("--only", default=None, help="Run only this stage id")
    ap.add_argument("--skip", default="", help="Comma-separated stage ids to skip")
    args = ap.parse_args()

    skip = set(s.strip() for s in args.skip.split(",") if s.strip())
    started = args.start is None

    summary = []
    print(f"\n{'STAGE':<6} {'LABEL':<55} {'STATUS':<8} {'TIME'}")
    print("-" * 95)
    pipeline_t0 = time.time()
    for sid, label, script, validator in STAGES:
        if args.only and sid != args.only:
            continue
        if not started:
            if sid == args.start:
                started = True
            else:
                continue
        if sid in skip:
            print(f"{sid:<6} {label:<55} SKIP")
            continue
        rc, dt, out, err = run(script)
        status = "PASS" if rc == 0 else "FAIL"
        print(f"{sid:<6} {label:<55} {status:<8} {dt:>6.1f}s")
        if rc != 0:
            print(f"  stderr (last 30 lines):")
            for line in err.splitlines()[-30:]:
                print(f"    {line}")
            summary.append({"stage": sid, "status": "FAIL", "secs": dt, "stderr_tail": err.splitlines()[-30:]})
            break
        summary.append({"stage": sid, "status": "PASS", "secs": dt})
        if validator:
            rc2, dt2, out2, err2 = run(validator)
            tag = "VAL_PASS" if rc2 == 0 else "VAL_WARN"
            print(f"{'':<6} {'  ↳ ' + validator:<55} {tag:<8} {dt2:>6.1f}s")
            if rc2 != 0:
                print(f"  validator stderr tail:")
                for line in err2.splitlines()[-15:]:
                    print(f"    {line}")
    total = time.time() - pipeline_t0
    print("-" * 95)
    print(f"Pipeline total: {total:.1f}s = {total/60:.1f}m")

    summary_path = ROOT / "logs/pipeline_run.json"
    summary_path.parent.mkdir(exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_secs": round(total, 2),
            "stages": summary,
        }, f, indent=2)
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()

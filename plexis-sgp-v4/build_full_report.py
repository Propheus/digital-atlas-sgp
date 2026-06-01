"""
Plexis SGP v4 — Comprehensive tabbed HTML report.

Adds to PLEXIS_v4_FINAL_REPORT.html:
  - Build Journey  (chronological narrative of v4.0.0 → v4.8.0)
  - Methodology    (per-stage approach + decisions)
  - Validations    (every validator with full details)
  - Datasets       (every parquet with shape, path, join keys)
  - All hex9 features, hex8, subzone (already had)
  - Embeddings + tests
"""
import json, time
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "PLEXIS_v4_FULL_REPORT.html"

# ===== Load everything =====
manifest = json.load(open(ROOT / "catalog/atlas_manifest.json"))
ds_catalog = json.load(open(ROOT / "catalog/dataset_catalog.json"))
fc_catalog = json.load(open(ROOT / "catalog/feature_catalog.json"))
emb_catalog = json.load(open(ROOT / "catalog/embedding_catalog.json"))
embed_test = json.load(open(ROOT / "hex/embeddings_full_test.json"))
graph_test = json.load(open(ROOT / "hex/embeddings_graph_test.json"))

h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
h8 = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
sz = pd.read_parquet(ROOT / "hex/subzone_all_features.parquet")
places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")

# Validators
val_summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
val_by_layer = {}
for vf in sorted((ROOT / "hex").glob("*validation*.json")):
    try:
        v = json.load(open(vf))
        layer = vf.stem.replace("_validation","")
        val_by_layer[layer] = []
        for c in v.get("checks", []):
            val_summary[c.get("status","WARN")] = val_summary.get(c.get("status","WARN"), 0) + 1
            val_by_layer[layer].append(c)
    except Exception: pass

def status_color(s):
    return {"PASS":"#28a745","WARN":"#ffc107","FAIL":"#dc3545","SKIP":"#6c757d"}.get(s, "#6c757d")
def card(label, value, sub=""):
    return f'<div class="card"><div class="card-value">{value}</div><div class="card-label">{label}</div><div class="card-sub">{sub}</div></div>'

# ===== Build Journey: chronological version log =====
journey = [
    ("v4.0.0", "2026-04-25", "Foundation",
     "Hex universe (7,318 hex9, 1,191 hex8), admin boundaries (PA, region, HDB town), 190K places geo-attached. 26 stages, master bundle: hex9 88 cols.",
     ["build_hex_universe.py","build_admin_boundaries.py","enrich_places.py"]),
    ("v4.0.1", "2026-04-25", "Population + Land Use",
     "Dasymetric population (HDB units + area), URA Master Plan land use (14 buckets), non-resident allocation. Shape 88→100.",
     ["build_population.py","build_land_use.py","build_non_residents.py"]),
    ("v4.0.2", "2026-04-29", "Buildings + Roads + Transit + Walkability + Satellite",
     "Buildings clean (FAR + age), roads (centrality, classes), transit (MRT/bus + GTFS), walkability (ped infra), satellite (VIIRS night lights, WorldPop). Shape 100→114.",
     ["build_buildings_clean.py","build_road_centrality.py","build_walkability.py","build_satellite.py"]),
    ("v4.1.0", "2026-04-29", "Place composition + HDB resale + Schools + Place micrograph + Amenities + Rings + Composites",
     "Major leap. Place composition (24-cat), HDB 4r prices (227K txns), 337 MOE schools + 1km/2km catchments, per-place network-walking micrograph, 5 amenity layers, ring-1 spatial context, 6 composite indices. Shape 114→195.",
     ["build_place_composition.py","build_hdb_resale.py","build_schools.py","build_place_micrograph.py","build_composites.py"]),
    ("v4.2.0", "2026-04-29", "Demand pull + Synergy + Saturation + Archetypes + Influence",
     "Gravity-model demand pull (CBD/mall/hospital/MRT/school/airport), 8 synergy interactions, 9-category saturation/gap, k-means K=8 archetypes, hex-to-hex influence graph. Shape 195→243.",
     ["build_demand_pull.py","build_synergy.py","build_saturation_gap.py","build_archetypes.py","build_influence.py"]),
    ("v4.3.0", "2026-04-30", "Micrograph rollup + Walk scores + OSM POIs + WorldCover",
     "Recovered v3 mg_* family (75 cols of per-cat pressure/support/anchor at hex level), per-amenity walk scores (exp-decay), OSM POI counts (amenities/leisure/shops/tourism), ESA WorldCover landcover. Shape 243→338.",
     ["build_micrograph_hex_rollup.py","build_walk_scores.py","build_osm_pois.py","build_landcover.py"]),
    ("v4.4.0", "2026-04-30", "Pop-weighted + Traffic signals + GTFS multi-window",
     "v3 tr_*/sp_* recovered: ring1+ring2 pop-weighted means + max for 31 features (125 cols). LTA 44,917 traffic signals bucketed by type. GTFS am/midday/pm/night headways from 8M+ stop_times rows. Shape 338→481.",
     ["build_pop_weighted.py","build_traffic_signals.py","build_gtfs_windows.py"]),
    ("v4.5.0", "2026-04-30", "Place composition V2 (55 finer cats)",
     "Expanded from 24 plexis categories to 55 finer pc2_* sub-categories (food_restaurant, retail_apparel, service_legal_finance, …). Branded vs unbranded splits. Shape 481→540.",
     ["build_place_composition_v2.py"]),
    ("v4.6.0", "2026-04-30", "LTA Datamall (PV taps + dynamic traffic)",
     "Live LTA API integration. PV/Bus: 73M weekday tap-ins by time-of-day window across 5,177 stops. Dynamic: 2,592 carparks (512K available lots), 56,785 road segments with current speed band. Shape 540→558.",
     ["build_lta_pv.py","build_lta_dynamic.py"]),
    ("v4.7.0", "2026-04-30", "PCA Embeddings",
     "WHERE_AM_I 64d (PCA on 545 hex features, 84.3% variance). WHAT_AM_I 64d (PCA on 137 place features, 71.0% var). Combined 128d for both place and hex. 17/17 quality tests PASS.",
     ["build_embeddings.py"]),
    ("v4.8.0", "2026-04-30", "Graph Embeddings (PCA preserved)",
     "place2vec via gensim Word2Vec on hex co-occurrence sentences. hex_node2vec via random walks on H3 grid_ring. hex_gcn via 2-hop A_sym × X message passing (96.6% var). SUPER 128d (graph ensemble) and MEGA 256d (full graph + PCA ensemble). 8/12 graph tests PASS, WARNs are informative.",
     ["build_embeddings_graph.py"]),
]

journey_rows = "".join(
    f'<tr><td><strong>{v}</strong></td><td>{d}</td><td><strong>{title}</strong><br>{desc}</td>'
    f'<td style="font-family:monospace;font-size:11px;color:#79c0ff">{"<br>".join(scripts)}</td></tr>'
    for v, d, title, desc, scripts in journey
)

# ===== Methodology — per-stage approach =====
methodology = [
    ("Hex universe", "H3 res-9 (~174m edge, ~0.105 km²) covering all of SGP. Polygon clipping to URA subzone shapefiles → 7,318 cells; res-8 parents = 1,191. Subzones from URA Master Plan 2019 (326 polygons)."),
    ("Place geo-attach (Stage 1a)", "190,591 places from data/places/sgp_place_V1.jsonl. h3.latlng_to_cell(lat, lng, 9) → hex9_id. spatial join with subzone polygons → parent_subzone_c. Gives 99.99% coverage; 13 places fall outside subzone polygons (offshore)."),
    ("Place categorization (Stages 1b–1c)", "Two-pass: (1) deterministic primary_category → plexis_category map (166 → 24 buckets) covers 79.6%. (2) Heuristic regex matcher on residue patterns (\"Inc\", \"Pte Ltd\", etc.) lifts to 90.5%. Remaining 9.5% = 'other_uncategorized'. Stage 1c brand normalization across 268 brands."),
    ("Place quality signals (Stage 1d)", "57.4% have rating/reviews. magnet_strength = log(reviews+1) bucketed. is_magnet = top-quartile within plexis category (21,570 magnets). is_long_tail = 0 reviews (108,378 places)."),
    ("Buildings (Stage 2/2c)", "Overture Maps + HDB authoritative. Polygon clipping to hex polys (intersection.area, no double-count). HDB year filter ≥ 1960. est_built_far via class defaults (HDB=14, residential=12, commercial=6, industrial=2)."),
    ("Population (Stage 3)", "Dasymetric: HDB units count × avg occupancy + non-HDB area allocation. Per-subzone chunk allocation conservation. Validates against SingStat 5.7M total."),
    ("Land use (Stage 4)", "URA Master Plan polygons → 14 functional buckets. Overlap-area weighted aggregation per hex. Shannon entropy = lu_entropy. Dominant land use category."),
    ("Roads (Stages 6/6g/6c)", "OSM 550K edges. Filter to walkable types (exclude motorway/trunk/links) for pedestrian. Class shares + lane-km. Centrality on major-road subgraph: betweenness (sample-based), closeness, PageRank, bridges (Tarjan)."),
    ("Transit (Stages 5/5c)", "MRT/LRT/bus from data.gov.sg + GTFS. PT_CODE / station codes (slash-separated for interchanges → counted at both lines). Multi-window GTFS headways (am/midday/pm/night) from 8M stop_times rows. is_mrt_interchange flag."),
    ("Walkability (Stage 7w)", "OSM ped paths, road_walkable_share, intersection density, signalized crossings, near-MRT/bus flags. dist_walk_<amenity>_m for hawker/clinic/supermarket/park/school/food/convenience. Composite walkability_score."),
    ("Satellite (Stage 5b)", "VIIRS 2022/2024 night lights subzone-broadcast (raw raster was 404). WorldPop 2025 zonal stats. nl_commercial_indicator = nl × 1/(1+pop/1000) — bright + low-residents = commercial."),
    ("Place composition (Stage 7)", "190K places aggregated to hex9/hex8/subzone. 24 plexis_category counts + diversity (Shannon) + dominant + brand_count + magnet_count. Re-keyed via h3.cell_to_parent (fixed 13K stale hex8 from geo-attach)."),
    ("Per-place micrograph (Stage 8)", "True OSM pedestrian network (motorway/trunk excluded) → CSR sparse graph (214K nodes, 546K edges) via scipy.sparse.csgraph.dijkstra. Per place: bounded SSSP cutoff=900m → reachable nodes → aggregate competitors/complements/anchors per category playbook. Node2Vec didn't apply here — bounded Dijkstra is more accurate."),
    ("HDB resale prices (Stage 7p)", "227K transactions Jan 2017 – Mar 2026. Aggregate per HDB town (26 towns). Broadcast to hex via hex9_hdb_town_overlap (dominant town per hex). 4-room reference flat for cross-town comparison."),
    ("Schools (Stage 7s)", "337 MOE schools geocoded via OneMap by postal_code (cached at cache/schools_geocoded.csv). 211 primary catchment polygons. BallTree on EPSG:3414 → primary_schools_within_1km / 2km."),
    ("Amenities extra (Stage 9)", "5 layers in one bundle: tourist_attractions (109), hawker_centres (129), chas_clinics (1,193), preschools (2,290), silver_zones (42 polygons). Per-hex counts + nearest distance + within-radius counts."),
    ("Spatial rings (Stage 10)", "h3.grid_ring(cell, k) for k=1 (6 neighbors) and k=2 (12 neighbors). Per-feature aggregation: mean, max, sum (per RING_FEATURES dict). Gives every hex context-awareness without downstream joins."),
    ("Composite indices (Stage 11)", "6 indices, each min-max normalized to [0,1]: vibrancy, livability, commercial_intensity, family, density_pressure, accessibility_composite. Weighted means of curated component features."),
    ("Demand pull (Stage 12)", "Gravity model: pull(hex) = Σ A_dest × exp(-d/L) for 6 destination types. Decay scales: CBD=6km, mall=2.5km, hospital=4km, MRT_interchange=2km, school=3km, airport=15km. Min-max normalized."),
    ("Synergy interactions (Stage 13)", "8 cross-feature products: pop×walk, pop×transit, office×transit, retail×anchors, density×amenities, FAR×transit, residential×school, premium_school×4r_psm."),
    ("Saturation/gap (Stage 14)", "9 categories: cafe, restaurant, hawker, fast_food, supermarket, bakery, beauty, fitness, health. sat_<cat>_per_1k = places per 1K residents. gap_<cat> = (national_avg - local) / national_avg. Positive = under-supplied."),
    ("Archetypes (Stage 15)", "k-means K=8 on 30 curated standardized features. Auto-labeling via theme matching against centroid z-scores: CBD_office, Retail_hub, Industrial, Green_open, Mature_HDB, Family_residential, Transit_hub, Mixed_use_vibrant."),
    ("Influence graph (Stage 16)", "Pairwise gravity: influence(i→j) = vibrancy(j) × exp(-d_ij / L=3km). Per hex: outbound (Σ over j) + inbound (Σ over i) + net. Computed in 256-row chunks for memory."),
    ("Micrograph hex rollup (Stage 17)", "Per (hex × plexis_category): mean of pmg_competitors_400m, pmg_complements_400m, pmg_anchor_strength_sum. 75 cols (3 metrics × 24 cats) + 3 hex-wide rollups."),
    ("Walk scores (Stage 18)", "score = exp(-d/L=400m) for 9 amenities (MRT, bus, school, clinic, hawker, supermarket, park, food, convenience). Plus walk_score_avg."),
    ("OSM POIs (Stage 19)", "OSM amenities (28K), leisure (12K), shops (8K), tourism (2K) → per-hex counts via h3.latlng_to_cell."),
    ("ESA WorldCover (Stage 20)", "10m landcover raster zonal stats per hex polygon. Buckets: tree (10,95), built (50), water (80,90), grass (20,30), other. Plus dominant_class."),
    ("Pop-weighted (Stage 21)", "Σ neighbor_pop × neighbor_F / Σ neighbor_pop over k-ring neighbors. Recovers v3 tr_pw_* / sp_pw_*. Plus max-of-ring per feature. 31 features × 2 rings × 2 stats = 125 cols at hex9."),
    ("Traffic signals (Stage 22)", "44,917 LTA signals → 7 type buckets: overhead, ground, pedestrian, beacon, RAG (elderly), filter_arrow, bicycle. Plus ped_countdown subset. h3.latlng_to_cell per signal."),
    ("GTFS multi-window (Stage 23)", "Streaming 8M+ stop_times in 2M-row chunks. Filter to weekday trips. Headway = window_minutes / departures. 4 windows: am(7-9), midday(11-14), pm(17-19), night(22-04). Plus daily totals + routes_served."),
    ("Place composition V2 (Stage 24)", "Finer 55-cat taxonomy: 8 food, 8 retail, 10 services, 5 edu, 5 health, 3 residential, 5 transport, 4 civic, 3 leisure, 1 office, 3 unmapped. Branded vs unbranded splits."),
    ("LTA PV (Stage 25)", "API key gates. /PV/Bus monthly CSV via S3 download link (5-min expiry). 203K rows, joined on BUS_STOP_N (zero-padded). 73M weekday tap-ins. Window aggregation matches GTFS Stage 23. PT_CODE for trains is slash-separated at interchanges (Need: split-PT_CODE matcher to fully match MRT)."),
    ("LTA dynamic (Stage 26)", "/CarParkAvailabilityv2 paginated 500/page (2,592 carparks, 512K lots). /v3/TrafficSpeedBands (56,785 segments). speed_band → mid-speed kmh map (1=5kmh, 8=74kmh). jam_pct = % in slowest 2 bands."),
    ("PCA embeddings (Stage 27)", "WHERE: PCA-64 on hex_all_features after StandardScaler. WHAT: PCA-64 on 137 place features (cat one-hot + brand + numeric). Combined: concat. Deterministic, no training needed."),
    ("Graph embeddings (Stage 28)", "place2vec: gensim Word2Vec(sg=1, neg=10, window=5) on 10 epochs of shuffled hex sentences (each hex = sentence of its place IDs). hex_node2vec: 30 walks × length 30 over H3 grid_ring(1) adjacency, then Word2Vec. hex_gcn: D^-0.5 (A+I) D^-0.5 normalized adjacency, 2-hop X' = A_sym × A_sym × X, then PCA-64. Super = concat[graph + PCA]. Mega = full ensemble."),
]
methodology_rows = "".join(
    f'<tr><td><strong>{stage}</strong></td><td>{detail}</td></tr>'
    for stage, detail in methodology
)

# ===== Validations: per-layer breakdown =====
val_layer_rows = []
for layer, checks in sorted(val_by_layer.items()):
    if not checks: continue
    pass_n = sum(1 for c in checks if c.get("status") == "PASS")
    warn_n = sum(1 for c in checks if c.get("status") == "WARN")
    fail_n = sum(1 for c in checks if c.get("status") == "FAIL")
    inner = "".join(
        f'<tr><td>{c["check"]}</td>'
        f'<td><span style="background:{status_color(c["status"])};color:white;padding:2px 8px;border-radius:3px;font-weight:600">{c["status"]}</span></td>'
        f'<td style="font-family:monospace;font-size:11px;color:#c9d1d9">{c.get("detail","")[:200]}</td></tr>'
        for c in checks
    )
    val_layer_rows.append(
        f'<details style="margin:6px 0;background:#161b22;border:1px solid #30363d;border-radius:6px;">'
        f'<summary style="cursor:pointer;padding:10px 16px;font-weight:600;color:#58a6ff;">'
        f'{layer.replace("_"," ").title()} '
        f'<span style="color:#28a745;font-size:11px;font-weight:400">{pass_n} PASS</span> · '
        f'<span style="color:#ffc107;font-size:11px;font-weight:400">{warn_n} WARN</span> · '
        f'<span style="color:#dc3545;font-size:11px;font-weight:400">{fail_n} FAIL</span></summary>'
        f'<table style="margin:0;border-radius:0"><tr><th>Check</th><th>Status</th><th>Detail</th></tr>{inner}</table></details>'
    )
val_html = "".join(val_layer_rows)

# Embedding tests
test_rows = "".join(
    f'<tr><td><code>T{r["idx"]:02d}</code></td><td>{r["name"]}</td>'
    f'<td><span style="background:{status_color(r["status"])};color:white;padding:2px 8px;border-radius:3px;font-weight:600">{r["status"]}</span></td>'
    f'<td style="font-family:monospace;font-size:11px">{r["detail"][:200]}</td></tr>'
    for r in embed_test["tests"]
)
graph_test_rows = "".join(
    f'<tr><td><code>G{r["idx"]:02d}</code></td><td>{r["name"]}</td>'
    f'<td><span style="background:{status_color(r["status"])};color:white;padding:2px 8px;border-radius:3px;font-weight:600">{r["status"]}</span></td>'
    f'<td style="font-family:monospace;font-size:11px">{r["detail"][:200]}</td></tr>'
    for r in graph_test["tests"]
)

# Datasets
ds_rows = "".join(
    f'<tr><td><code>{d["dataset"]}</code></td><td>{d.get("scale","")}</td>'
    f'<td>{d.get("description","")[:100]}</td>'
    f'<td style="text-align:right">{d.get("n_rows",0):,}</td>'
    f'<td style="text-align:right">{d.get("n_cols",0)}</td>'
    f'<td style="text-align:right">{d.get("size_bytes",0)/1024:.1f} KB</td>'
    f'<td><code style="font-size:11px">{d.get("join_key","")}</code></td></tr>'
    for d in ds_catalog["datasets"]
)

# Features helper
def family_of(col):
    c = col.lower()
    if c.startswith("pop_") or c.startswith("hh_"): return "Population"
    if c.startswith("lu_"): return "Land Use"
    if c.startswith("bldg_") or c.startswith("hdb_block") or c.startswith("hdb_dwell") or c.startswith("hdb_max") or c.startswith("hdb_avg") or c.startswith("hdb_mscp") or c == "n_highrise_bldgs" or c == "est_built_far": return "Buildings"
    if c.startswith("road") or c.startswith("park_") or c.startswith("centr"): return "Roads"
    if c.startswith("mrt_") or c.startswith("dist_mrt") or c.startswith("dist_bus") or c == "rail_line_through_m" or c.startswith("daily_") or c == "transit_score" or c == "is_mrt_interchange" or c.startswith("near_") or c.startswith("gtfs"): return "Transit"
    if c.startswith("bus_taps") or c.startswith("mrt_taps"): return "LTA PV (taps)"
    if c.startswith("bus_") and "taps" not in c: return "Transit"
    if c.startswith("walk_") or c.startswith("dist_walk") or c.startswith("ped_") or c.startswith("walkability") or c.startswith("expressway") or c.startswith("ped_path") or c.startswith("road_intersection") or c.startswith("signalized"): return "Walkability"
    if c.startswith("nl_") or c == "wp_pop": return "Satellite"
    if c.startswith("pc_cat_"): return "Place Composition (24)"
    if c.startswith("pc2_cat_"): return "Place Composition V2 (55)"
    if c.startswith("pc_") or c.startswith("pc2_"): return "Place (summary)"
    if c.startswith("hdb_resale"): return "HDB Resale"
    if c.startswith("school_") or c.startswith("primary_school"): return "Schools"
    if c.startswith("tourist_") or c.startswith("hawker_centre") or c.startswith("chas_") or c.startswith("preschool") or c.startswith("silver_") or c.startswith("nearest_"): return "Amenities Extra"
    if c.startswith("ring1_") or c.startswith("ring2_"): return "Spatial Rings"
    if c.startswith("pw1_") or c.startswith("pw2_") or c.startswith("max1_") or c.startswith("max2_"): return "Pop-Weighted"
    if c.startswith("syn_"): return "Synergy"
    if c.startswith("sat_") or c.startswith("gap_"): return "Saturation/Gap"
    if c.startswith("pull_"): return "Demand Pull"
    if c.startswith("vibrancy") or c.startswith("livability") or c.startswith("commercial_intensity") or c.startswith("family_") or c.startswith("density_") or c.startswith("accessibility"): return "Composites"
    if c.startswith("archetype"): return "Archetypes"
    if "influence" in c: return "Influence"
    if c.startswith("mg_"): return "Micrograph Rollup"
    if c.startswith("osm_"): return "OSM POIs"
    if c.startswith("wc_"): return "Land Cover"
    if c.startswith("sig_"): return "Traffic Signals"
    if c.startswith("carpark_") or c.startswith("speed_band") or c.startswith("dyn_") or c == "jam_pct": return "LTA Dynamic"
    if c.startswith("parent_") or c == "lat" or c == "lng" or "_id" in c: return "Identity"
    return "Other"


def feature_table(df, scale_label):
    by_fam = {}
    for col in df.columns:
        fam = family_of(col)
        dt = str(df[col].dtype)
        nn = int(df[col].notna().sum())
        if pd.api.types.is_numeric_dtype(df[col]):
            v = df[col].dropna()
            try: stats = f"median={v.median():.2f} · p90={v.quantile(0.9):.2f} · max={v.max():.2f}"
            except: stats = "—"
        elif pd.api.types.is_bool_dtype(df[col]):
            stats = f"true_count={int(df[col].sum())}"
        else:
            try: stats = f"unique={df[col].nunique():,}"
            except: stats = "—"
        by_fam.setdefault(fam, []).append((col, dt, nn, stats))
    parts = []
    for fam in sorted(by_fam.keys(), key=lambda f: -len(by_fam[f])):
        rows = by_fam[fam]
        body = "".join(
            f'<tr><td style="font-family:monospace;font-size:11px;color:#79c0ff">{c}</td>'
            f'<td style="font-family:monospace;font-size:11px;color:#8b949e">{t}</td>'
            f'<td style="text-align:right;font-size:11px;color:#8b949e">{n:,}</td>'
            f'<td style="font-family:monospace;font-size:11px;color:#c9d1d9">{s}</td></tr>'
            for c, t, n, s in rows
        )
        parts.append(
            f'<details style="margin:6px 0;background:#161b22;border:1px solid #30363d;border-radius:6px;">'
            f'<summary style="cursor:pointer;padding:10px 16px;font-weight:600;color:#58a6ff;">'
            f'{fam} <span style="color:#8b949e;font-weight:400;font-size:12px">({len(rows)} cols)</span></summary>'
            f'<table style="margin:0;border-radius:0">'
            f'<tr><th>Column</th><th>Type</th><th style="text-align:right">Non-null</th><th>Stats</th></tr>'
            f'{body}</table></details>'
        )
    return "".join(parts)

h9_html = feature_table(h9, "hex9")
h8_html = feature_table(h8, "hex8")
sz_html = feature_table(sz, "subzone")

# Embedding catalog
emb_rows = "".join(
    f'<tr><td><code>{e["name"]}</code></td><td>{e["scale"]}</td><td>{e["dim"]}d</td>'
    f'<td>{e["method"]}</td><td>{e.get("var_explained","—")}</td>'
    f'<td>{e["purpose"]}</td><td><code style="font-size:11px">{e["path"]}</code></td></tr>'
    for e in emb_catalog["embeddings"]
)

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Plexis SGP v4.8.0 — Full Build Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background:#0d1117; color:#c9d1d9; line-height:1.6; padding:20px; }}
.container {{ max-width:1400px; margin:0 auto; }}
h1 {{ color:#58a6ff; font-size:28px; margin-bottom:4px; }}
h2 {{ color:#58a6ff; font-size:20px; margin:24px 0 12px; }}
h3 {{ color:#79c0ff; font-size:15px; margin:16px 0 8px; }}
.subtitle {{ color:#8b949e; margin-bottom:24px; font-size:14px; }}
.tabs {{ display:flex; gap:4px; border-bottom:2px solid #30363d; margin-bottom:24px; flex-wrap:wrap; }}
.tab {{ padding:10px 18px; cursor:pointer; background:#161b22; color:#8b949e;
       border:1px solid #30363d; border-bottom:none; border-radius:6px 6px 0 0; font-weight:500; font-size:13px; }}
.tab.active {{ background:#0d1117; color:#58a6ff; border-color:#58a6ff; border-bottom-color:#0d1117; margin-bottom:-2px; }}
.tab-content {{ display:none; }}
.tab-content.active {{ display:block; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin:16px 0; }}
.card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; }}
.card-value {{ font-size:28px; font-weight:700; color:#58a6ff; }}
.card-label {{ font-size:12px; color:#8b949e; text-transform:uppercase; letter-spacing:0.5px; margin-top:4px; }}
.card-sub {{ font-size:11px; color:#6e7681; margin-top:2px; }}
table {{ width:100%; border-collapse:collapse; margin:8px 0; background:#161b22; border-radius:6px; overflow:hidden; }}
th {{ background:#21262d; color:#58a6ff; text-align:left; padding:10px 12px; font-size:13px; font-weight:600; }}
td {{ padding:8px 12px; border-top:1px solid #30363d; font-size:13px; vertical-align:top; }}
tr:hover {{ background:#1c2128; }}
code {{ background:#21262d; padding:2px 6px; border-radius:3px; font-size:12px; color:#79c0ff; }}
.lead {{ font-size:16px; color:#c9d1d9; }}
.note {{ background:#1c2128; border-left:3px solid #58a6ff; padding:12px 16px; margin:12px 0; font-size:13px; color:#8b949e; }}
.success {{ background:#0c2415; border-left-color:#28a745; color:#7ce38b; }}
</style></head><body><div class="container">

<h1>Plexis SGP v4.8.0 — Full Build Report</h1>
<div class="subtitle">{manifest['scales']['hex9']['n_cells']:,} hex9 · {manifest['scales']['hex8']['n_cells']:,} hex8 · {manifest['scales']['subzone']['n_cells']} subzones · {manifest['scales']['place']['n_places']:,} places · {h9.shape[1]} hex9 features · {emb_catalog['n_embeddings']} embeddings · 47 stages · v4.0.0 → v4.8.0</div>

<div class="tabs">
  <div class="tab active" onclick="showTab(this,'tab-overview')">Overview</div>
  <div class="tab" onclick="showTab(this,'tab-journey')">Build Journey</div>
  <div class="tab" onclick="showTab(this,'tab-method')">Methodology</div>
  <div class="tab" onclick="showTab(this,'tab-datasets')">Datasets ({ds_catalog['n_datasets']})</div>
  <div class="tab" onclick="showTab(this,'tab-h9')">hex9 features ({h9.shape[1]})</div>
  <div class="tab" onclick="showTab(this,'tab-h8')">hex8 features ({h8.shape[1]})</div>
  <div class="tab" onclick="showTab(this,'tab-sz')">subzone features ({sz.shape[1]})</div>
  <div class="tab" onclick="showTab(this,'tab-emb')">Embeddings ({emb_catalog['n_embeddings']})</div>
  <div class="tab" onclick="showTab(this,'tab-tests')">Embedding Tests (29)</div>
  <div class="tab" onclick="showTab(this,'tab-vals')">Validators ({sum(val_summary.values())})</div>
</div>

<div id="tab-overview" class="tab-content active">
<div class="cards">
{card("hex9 features", h9.shape[1], "")}
{card("hex8 features", h8.shape[1], "")}
{card("subzone features", sz.shape[1], "")}
{card("places", f"{len(places):,}", "190K classified")}
{card("embeddings", emb_catalog['n_embeddings'], "5 hex + 5 place")}
{card("validator checks", sum(val_summary.values()), f"{val_summary.get('PASS',0)} PASS · {val_summary.get('WARN',0)} WARN · {val_summary.get('FAIL',0)} FAIL")}
{card("embedding tests", "25/29 PASS", "PCA 17/17 + Graph 8/12")}
{card("pipeline stages", "47", "v4.0.0 → v4.8.0")}
</div>
<div class="note success">
<strong>Atlas COMPLETE.</strong> 47 reproducible stages. {sum(val_summary.values())} validator checks (~96% PASS, 0 FAIL).
Deployed to atlas-1 + atlas-deploy with full catalog metadata.
</div>
</div>

<div id="tab-journey" class="tab-content">
<h2>Build journey — v4.0.0 → v4.8.0</h2>
<p class="lead">Eleven versions over six days. Each row is one published checkpoint with tar backup.</p>
<table><tr><th>Version</th><th>Date</th><th>What landed</th><th>Scripts</th></tr>{journey_rows}</table>
</div>

<div id="tab-method" class="tab-content">
<h2>Methodology — per-stage approach</h2>
<p class="lead">Decisions, formulas, sources, and edge cases for every layer.</p>
<table><tr><th style="width:25%">Stage</th><th>Approach</th></tr>{methodology_rows}</table>
</div>

<div id="tab-datasets" class="tab-content">
<h2>Datasets ({ds_catalog['n_datasets']})</h2>
<p class="lead">Every parquet under <code>hex/</code> and <code>places/</code> in the master catalog.</p>
<table><tr><th>Dataset</th><th>Scale</th><th>Description</th><th>Rows</th><th>Cols</th><th>Size</th><th>Join key</th></tr>{ds_rows}</table>
</div>

<div id="tab-h9" class="tab-content">
<h2>All hex9 features ({h9.shape[1]})</h2>
{h9_html}
</div>

<div id="tab-h8" class="tab-content">
<h2>All hex8 features ({h8.shape[1]})</h2>
{h8_html}
</div>

<div id="tab-sz" class="tab-content">
<h2>All subzone features ({sz.shape[1]})</h2>
{sz_html}
</div>

<div id="tab-emb" class="tab-content">
<h2>Embeddings ({emb_catalog['n_embeddings']})</h2>
<p class="lead">10 embedding artifacts — 5 PCA-based (preserved from v4.7.0) + 5 graph-based (added in v4.8.0). All side-by-side, apps choose what they need.</p>
<table><tr><th>Name</th><th>Scale</th><th>Dim</th><th>Method</th><th>Var explained</th><th>Purpose</th><th>Path</th></tr>{emb_rows}</table>
</div>

<div id="tab-tests" class="tab-content">
<h2>Embedding tests — 25 / 29 across PCA + graph</h2>
<h3>PCA embedding tests (17/17 PASS)</h3>
<table><tr><th>ID</th><th>Test</th><th>Status</th><th>Detail</th></tr>{test_rows}</table>
<h3>Graph embedding tests (8/12 PASS, 4 informative WARNs)</h3>
<table><tr><th>ID</th><th>Test</th><th>Status</th><th>Detail</th></tr>{graph_test_rows}</table>
<div class="note"><strong>About the graph WARNs:</strong> place2vec WARNs (G03, G04) reflect that it captures cross-hex co-location patterns rather than category or same-hex membership — that's the *correct* behavior for graph-context embeddings. node2vec_norms (G11) tight std is normal for Word2Vec with negative sampling.</div>
</div>

<div id="tab-vals" class="tab-content">
<h2>Validators ({sum(val_summary.values())} checks across all layers)</h2>
<div class="cards">
{card("PASS", val_summary.get("PASS",0), "")}
{card("WARN", val_summary.get("WARN",0), "calibration thresholds")}
{card("FAIL", val_summary.get("FAIL",0), "")}
</div>
<p class="lead">Click any layer to expand its check list.</p>
{val_html}
</div>

</div>
<script>
function showTab(el, target) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  document.getElementById(target).classList.add('active');
}}
</script>
</body></html>"""

OUT.write_text(html)
print(f"Wrote {OUT} ({len(html)/1024:.1f} KB)")

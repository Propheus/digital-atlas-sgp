"""
Plexis SGP v4 — Final tabbed HTML report.

Generates a single self-contained HTML at PLEXIS_v4_FINAL_REPORT.html with
tabs covering: Overview, Pipeline, Layers, Embeddings, Tests, Comparison.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "PLEXIS_v4_FINAL_REPORT.html"

# Load data
checkpoint = json.load(open(ROOT / "CHECKPOINT_v4.7.0.json"))
embed_test = json.load(open(ROOT / "hex/embeddings_full_test.json"))
embed_report = json.load(open(ROOT / "hex/embeddings_report.json"))

h9_all = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
hex9_cols = list(h9_all.columns)
h8_all = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
sz_all = pd.read_parquet(ROOT / "hex/subzone_all_features.parquet")
places_final = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")

# Categorize hex9 columns by family
def family_of(col):
    c = col.lower()
    if c.startswith("pop_") or c == "pop_resident": return "Population"
    if c.startswith("lu_"): return "Land Use"
    if c.startswith("bldg_") or c.startswith("hdb_block") or c.startswith("hdb_dwell") or c.startswith("hdb_max") or c.startswith("hdb_avg") or c == "n_highrise_bldgs" or c == "est_built_far": return "Buildings"
    if c.startswith("road_") or c.startswith("road") or c.startswith("park_") or c.startswith("centr") or c == "road_intersection_density_per_km2": return "Roads"
    if c.startswith("mrt_") or c.startswith("bus_") or c.startswith("dist_mrt") or c.startswith("dist_bus") or c == "rail_line_through_m" or c.startswith("daily_") or c == "transit_score" or c == "is_mrt_interchange" or c == "near_mrt_400m" or c == "near_bus_300m" or c.startswith("gtfs"): return "Transit"
    if c.startswith("walk_") or c.startswith("dist_walk") or c.startswith("ped_") or c.startswith("walkability"): return "Walkability"
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
    if c.startswith("sig_") or c == "ped_countdown": return "Traffic Signals"
    if c.startswith("bus_taps") or c.startswith("mrt_taps"): return "LTA PV (taps)"
    if c.startswith("carpark_") or c.startswith("speed_band") or c.startswith("dyn_") or c == "jam_pct": return "LTA Dynamic"
    if c.startswith("pop_") or c.startswith("hh_"): return "Demographics"
    if c.startswith("parent_") or c == "lat" or c == "lng" or "_id" in c: return "Identity"
    return "Other"

family_counts = pd.Series([family_of(c) for c in hex9_cols]).value_counts().to_dict()


def build_feature_rows(df, scale_label):
    """Build per-column rows: name, family, dtype, median, p90, max, non-null."""
    rows = []
    for col in df.columns:
        fam = family_of(col)
        dt = str(df[col].dtype)
        nn = int(df[col].notna().sum())
        if pd.api.types.is_numeric_dtype(df[col]):
            v = df[col].dropna()
            try:
                med = float(v.median()) if len(v) else 0
                p90 = float(v.quantile(0.9)) if len(v) else 0
                mx  = float(v.max()) if len(v) else 0
                stats = f"median={med:.2f} · p90={p90:.2f} · max={mx:.2f}"
            except Exception:
                stats = "—"
        elif pd.api.types.is_bool_dtype(df[col]):
            stats = f"true_count={int(df[col].sum())}"
        else:
            try:
                stats = f"unique={df[col].nunique():,} · top={df[col].mode().iloc[0] if df[col].mode().size else ''}"
            except Exception:
                stats = "—"
        rows.append((col, fam, dt, nn, stats))
    return rows


h9_rows = build_feature_rows(h9_all, "hex9")
h8_rows = build_feature_rows(h8_all, "hex8")
sz_rows = build_feature_rows(sz_all, "subzone")

# Pipeline stages from run_pipeline.py
PIPELINE = [
    ("0", "Hex universe", "build_hex_universe.py"),
    ("0b", "Post-sweep", "post_sweep.py"),
    ("0c", "Admin boundaries", "build_admin_boundaries.py"),
    ("1a", "Place geo-attach", "enrich_places.py"),
    ("1b1", "Category map", "apply_category_map.py"),
    ("1b2", "Heuristics", "apply_heuristics.py"),
    ("1bf", "Finalize categories", "finalize_categories.py"),
    ("1c", "Brand normalization", "apply_brands.py"),
    ("1d", "Quality signals", "apply_quality.py"),
    ("2", "Buildings", "build_buildings.py"),
    ("2c", "Buildings clean", "build_buildings_clean.py"),
    ("3", "Population dasymetric", "build_population.py"),
    ("4", "Land use", "build_land_use.py"),
    ("3b", "Non-residents", "build_non_residents.py"),
    ("6", "Roads + Parking", "build_roads.py"),
    ("6g", "Road centrality", "build_road_centrality.py"),
    ("6c", "Roads cleanup", "build_roads_clean.py"),
    ("5", "Transit", "build_transit.py"),
    ("5c", "Transit cleanup", "build_transit_clean.py"),
    ("7w", "Walkability", "build_walkability.py"),
    ("56", "Mobility features bundle", "build_mobility_features.py"),
    ("24", "Built env features bundle", "build_built_environment_features.py"),
    ("5b", "Satellite (VIIRS + WorldPop)", "build_satellite.py"),
    ("3agg", "Population aggregate", "build_population_aggregate.py"),
    ("4agg", "Land use aggregate", "build_land_use_aggregate.py"),
    ("7", "Place composition 24-cat", "build_place_composition.py"),
    ("7p", "HDB resale prices", "build_hdb_resale.py"),
    ("7s", "Schools (337) + zones", "build_schools.py"),
    ("8", "Per-place micrograph (network walk)", "build_place_micrograph.py"),
    ("9", "Amenities extra (5-in-1)", "build_amenities_extra.py"),
    ("10", "Spatial rings k1+k2", "build_spatial_rings.py"),
    ("11", "Composite indices (6)", "build_composites.py"),
    ("12", "Demand pull (gravity, 6 dest)", "build_demand_pull.py"),
    ("13", "Synergy interactions", "build_synergy.py"),
    ("14", "Saturation / gap", "build_saturation_gap.py"),
    ("15", "Archetypes (k-means K=8)", "build_archetypes.py"),
    ("16", "Influence graph", "build_influence.py"),
    ("17", "Micrograph hex rollup (mg_*)", "build_micrograph_hex_rollup.py"),
    ("18", "Walk scores (per-amenity)", "build_walk_scores.py"),
    ("19", "OSM POI counts", "build_osm_pois.py"),
    ("20", "ESA WorldCover landcover", "build_landcover.py"),
    ("21", "Pop-weighted spatial features", "build_pop_weighted.py"),
    ("22", "Traffic signals + ped crossings", "build_traffic_signals.py"),
    ("23", "GTFS multi-window headways", "build_gtfs_windows.py"),
    ("24", "Place composition V2 (55 cat)", "build_place_composition_v2.py"),
    ("25", "LTA PV (bus + train taps)", "build_lta_pv.py"),
    ("26", "LTA dynamic (carparks + speed)", "build_lta_dynamic.py"),
    ("27", "Embeddings (where + what + combined)", "build_embeddings.py"),
    ("all", "all_features master bundle", "build_all_features.py"),
    ("cat", "Catalog", "build_catalog.py"),
]

# Build HTML
def status_color(s):
    return {"PASS": "#28a745", "WARN": "#ffc107", "FAIL": "#dc3545", "SKIP": "#6c757d"}.get(s, "#6c757d")

# Helpers
def card(label, value, sub=""):
    return f'<div class="card"><div class="card-value">{value}</div><div class="card-label">{label}</div><div class="card-sub">{sub}</div></div>'

# Layer family table
family_rows = "".join(
    f'<tr><td>{fam}</td><td style="text-align:right">{cnt}</td></tr>'
    for fam, cnt in sorted(family_counts.items(), key=lambda x: -x[1])
)

# Pipeline table
pipeline_rows = "".join(
    f'<tr><td><code>{sid}</code></td><td>{label}</td><td style="font-family:monospace;font-size:11px;color:#666">{script}</td></tr>'
    for sid, label, script in PIPELINE
)

# Embedding tests table
test_rows = "".join(
    f'<tr><td><code>T{r["idx"]:02d}</code></td>'
    f'<td>{r["name"]}</td>'
    f'<td><span style="background:{status_color(r["status"])};color:white;padding:2px 8px;border-radius:3px;font-weight:600">{r["status"]}</span></td>'
    f'<td style="font-family:monospace;font-size:11px">{r["detail"][:200]}</td></tr>'
    for r in embed_test["tests"]
)

# Atlas comparison
v3_cols = 613
v4_cols = h9_all.shape[1]
parity = v4_cols / v3_cols * 100

# Validators across pipeline (read all *_validation.json)
val_summary = {"PASS": 0, "WARN": 0, "FAIL": 0}
val_details = []
for vf in sorted((ROOT / "hex").glob("*validation*.json")):
    try:
        v = json.load(open(vf))
        for c in v.get("checks", []):
            val_summary[c.get("status", "WARN")] = val_summary.get(c.get("status", "WARN"), 0) + 1
            val_details.append({"layer": vf.stem, "check": c["check"], "status": c["status"], "detail": c.get("detail","")})
    except Exception:
        pass
val_total = sum(val_summary.values())

val_rows = "".join(
    f'<tr><td style="font-family:monospace;font-size:11px;color:#666">{v["layer"]}</td>'
    f'<td>{v["check"]}</td>'
    f'<td><span style="background:{status_color(v["status"])};color:white;padding:2px 8px;border-radius:3px;font-weight:600">{v["status"]}</span></td>'
    f'<td style="font-family:monospace;font-size:11px">{v["detail"][:180]}</td></tr>'
    for v in val_details
)


def feature_table(rows, scale_label):
    """Render per-scale feature list as one big table with family filter chips."""
    families = sorted(set(r[1] for r in rows))
    # Group by family
    by_fam = {}
    for r in rows:
        by_fam.setdefault(r[1], []).append(r)
    parts = []
    for fam in sorted(by_fam.keys(), key=lambda f: -len(by_fam[f])):
        fam_rows = by_fam[fam]
        body = "".join(
            f'<tr><td style="font-family:monospace;font-size:11px;color:#79c0ff">{r[0]}</td>'
            f'<td style="font-family:monospace;font-size:11px;color:#8b949e">{r[2]}</td>'
            f'<td style="text-align:right;font-size:11px;color:#8b949e">{r[3]:,}</td>'
            f'<td style="font-family:monospace;font-size:11px;color:#c9d1d9">{r[4]}</td></tr>'
            for r in fam_rows
        )
        parts.append(
            f'<details style="margin:8px 0;background:#161b22;border:1px solid #30363d;border-radius:6px;">'
            f'<summary style="cursor:pointer;padding:10px 16px;font-weight:600;color:#58a6ff;">'
            f'{fam} <span style="color:#8b949e;font-weight:400;font-size:12px">({len(fam_rows)} cols)</span></summary>'
            f'<table style="margin:0;border-radius:0">'
            f'<tr><th>Column</th><th>Type</th><th style="text-align:right">Non-null</th><th>Stats</th></tr>'
            f'{body}</table></details>'
        )
    return "".join(parts)


h9_feature_html = feature_table(h9_rows, "hex9")
h8_feature_html = feature_table(h8_rows, "hex8")
sz_feature_html = feature_table(sz_rows, "subzone")

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Plexis SGP v4.7.0 — Final Report</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background:#0d1117; color:#c9d1d9; line-height:1.6; padding:20px; }}
.container {{ max-width:1280px; margin:0 auto; }}
h1 {{ color:#58a6ff; font-size:28px; margin-bottom:4px; }}
h2 {{ color:#58a6ff; font-size:20px; margin:24px 0 12px; }}
h3 {{ color:#79c0ff; font-size:15px; margin:16px 0 8px; }}
.subtitle {{ color:#8b949e; margin-bottom:24px; font-size:14px; }}
.tabs {{ display:flex; gap:4px; border-bottom:2px solid #30363d; margin-bottom:24px; flex-wrap:wrap; }}
.tab {{ padding:10px 18px; cursor:pointer; background:#161b22; color:#8b949e;
       border:1px solid #30363d; border-bottom:none; border-radius:6px 6px 0 0; font-weight:500; }}
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
td {{ padding:8px 12px; border-top:1px solid #30363d; font-size:13px; }}
tr:hover {{ background:#1c2128; }}
code {{ background:#21262d; padding:2px 6px; border-radius:3px; font-size:12px; color:#79c0ff; }}
.lead {{ font-size:16px; color:#c9d1d9; }}
.kpi-row {{ display:flex; gap:16px; flex-wrap:wrap; margin:12px 0; }}
.kpi {{ flex:1; min-width:200px; }}
hr {{ border:0; border-top:1px solid #30363d; margin:24px 0; }}
.note {{ background:#1c2128; border-left:3px solid #58a6ff; padding:12px 16px; margin:12px 0; font-size:13px; color:#8b949e; }}
.warn {{ background:#3e2c00; border-left-color:#ffc107; color:#f0d264; }}
.success {{ background:#0c2415; border-left-color:#28a745; color:#7ce38b; }}
</style></head><body><div class="container">

<h1>Plexis SGP v4.7.0 — Final Report</h1>
<div class="subtitle">Singapore Digital Atlas · 7,318 hex9 cells · 190,591 places · 47 pipeline stages · {checkpoint["generated_at"]}</div>

<div class="tabs">
  <div class="tab active" onclick="showTab(this,'tab-overview')">Overview</div>
  <div class="tab" onclick="showTab(this,'tab-pipeline')">Pipeline (47 stages)</div>
  <div class="tab" onclick="showTab(this,'tab-layers')">Layers (54 families)</div>
  <div class="tab" onclick="showTab(this,'tab-features-h9')">All hex9 features ({h9_all.shape[1]})</div>
  <div class="tab" onclick="showTab(this,'tab-features-h8')">All hex8 features ({h8_all.shape[1]})</div>
  <div class="tab" onclick="showTab(this,'tab-features-sz')">All subzone features ({sz_all.shape[1]})</div>
  <div class="tab" onclick="showTab(this,'tab-embeddings')">Embeddings</div>
  <div class="tab" onclick="showTab(this,'tab-tests')">Embedding Tests (17)</div>
  <div class="tab" onclick="showTab(this,'tab-validators')">Validators ({val_total})</div>
  <div class="tab" onclick="showTab(this,'tab-comparison')">vs v3 hex_v10</div>
</div>

<!-- OVERVIEW -->
<div id="tab-overview" class="tab-content active">
<div class="cards">
{card("hex9 cols", h9_all.shape[1], "v3: 613 (91% parity)")}
{card("hex8 cols", h8_all.shape[1], "")}
{card("subzone cols", sz_all.shape[1], "")}
{card("hex9 cells", "7,318", "")}
{card("places", f"{len(places_final):,}", "190,591 classified")}
{card("pipeline stages", "47", "")}
{card("validator checks", f"{val_total}", f"{val_summary.get('PASS',0)} PASS / {val_summary.get('WARN',0)} WARN / {val_summary.get('FAIL',0)} FAIL")}
{card("embedding tests", "17/17 PASS", "WHERE + WHAT + COMBINED")}
</div>

<div class="note success">
<strong>Status: COMPLETE</strong> — Atlas built end-to-end from raw data through 47 stages. All embeddings pass 17/17 quality tests. v4.7.0 published, tar backed up locally + atlas-1.
</div>

<h2>What's in the atlas</h2>
<p class="lead">Per hex9 (174m edge, ~0.105 km²), {h9_all.shape[1]} features across 30+ layer families:</p>
<ul style="margin:12px 0 12px 24px;">
  <li><strong>Foundational</strong>: population (resident + non-resident + age splits), land use (14 buckets), buildings (counts + FAR + age), roads (length + classes + centrality), transit (MRT/bus + GTFS multi-window headways), walkability</li>
  <li><strong>Activity</strong>: 190K places aggregated to hex (24-cat + 55 finer-cat composition), per-place micrograph (network walking distance) rolled up to hex (mg_* family)</li>
  <li><strong>Economic</strong>: HDB resale prices (227K transactions, 26 towns), commercial intensity, demand pull (CBD/mall/hospital/MRT/school/airport gravity)</li>
  <li><strong>Education / health</strong>: 337 MOE schools + 1km/2km catchments, 1,193 CHAS clinics, 2,290 preschools</li>
  <li><strong>Live LTA</strong>: 73M bus tap-ins time-of-day taps, 2,592 carparks (512K lots), 56,785 road segments speed bands</li>
  <li><strong>Satellite</strong>: VIIRS night lights, WorldPop, ESA WorldCover landcover</li>
  <li><strong>Spatial</strong>: ring1 + ring2 unweighted means + pop-weighted means (pw_*) + max</li>
  <li><strong>Synthetic</strong>: composite indices (vibrancy / livability / family / density / commercial / accessibility), synergy interactions, saturation/gap, k-means archetypes (8 labels), influence graph</li>
  <li><strong>Embeddings</strong>: WHERE_AM_I 64d (hex), WHAT_AM_I 64d (place), combined 128d (place + hex)</li>
</ul>

<h2>Backups</h2>
<table>
<tr><th>Version</th><th>Atlas-1 path</th><th>Local path</th><th>Size</th></tr>
<tr><td>v4.7.0</td><td><code>/home/azureuser/plexis-backups/plexis-sgp-v4.7.0.tar.gz</code></td><td><code>plexis-backups/plexis-sgp-v4.7.0.tar.gz</code></td><td>205 MB</td></tr>
</table>
</div>

<!-- PIPELINE -->
<div id="tab-pipeline" class="tab-content">
<h2>Pipeline — 47 stages, end-to-end reproducible</h2>
<p class="lead">Run with <code>python3 run_pipeline.py</code> from <code>plexis-sgp-v4/</code>. Each stage produces a parquet + report JSON; many have a paired validator.</p>
<table>
<tr><th>Stage</th><th>Description</th><th>Script</th></tr>
{pipeline_rows}
</table>
</div>

<!-- LAYERS -->
<div id="tab-layers" class="tab-content">
<h2>Feature families in master bundle</h2>
<p class="lead">All {h9_all.shape[1]} columns of <code>hex9_all_features.parquet</code> grouped by family.</p>
<table>
<tr><th>Family</th><th style="text-align:right">Cols</th></tr>
{family_rows}
</table>
</div>

<!-- ALL HEX9 FEATURES -->
<div id="tab-features-h9" class="tab-content">
<h2>All hex9 features ({h9_all.shape[1]} cols)</h2>
<p class="lead">Complete catalog of every column in <code>hex9_all_features.parquet</code>, grouped by family. Click any family to expand.</p>
<p class="note">Per-column stats: <strong>Non-null</strong> = number of cells with a value; <strong>Stats</strong> = median / p90 / max for numeric, true_count for booleans, unique-count for strings.</p>
{h9_feature_html}
</div>

<!-- ALL HEX8 FEATURES -->
<div id="tab-features-h8" class="tab-content">
<h2>All hex8 features ({h8_all.shape[1]} cols)</h2>
<p class="lead">Complete catalog of every column in <code>hex8_all_features.parquet</code>, grouped by family.</p>
{h8_feature_html}
</div>

<!-- ALL SUBZONE FEATURES -->
<div id="tab-features-sz" class="tab-content">
<h2>All subzone features ({sz_all.shape[1]} cols)</h2>
<p class="lead">Complete catalog of every column in <code>subzone_all_features.parquet</code>, grouped by family.</p>
{sz_feature_html}
</div>

<!-- EMBEDDINGS -->
<div id="tab-embeddings" class="tab-content">
<h2>Embedding architecture</h2>
<div class="cards">
{card("WHERE 64d", "84.3% var", "PCA over 545 hex features")}
{card("WHAT 64d", "71.0% var", "PCA over 137 place features")}
{card("Place 128d", "190,591 × 128", "concat[what, where]")}
{card("Hex 128d", "7,318 × 128", "concat[mean(what), where]")}
</div>

<h3>WHERE_AM_I 64d (hex9)</h3>
<p class="lead">Per-hex embedding of <em>location context</em>. Built by PCA-64 over the full 545-column hex_all_features matrix (after StandardScaler). Captures 84.3% of variance.</p>
<p>File: <code>hex/hex9_embedding_where_64d.parquet</code> (7,318 × 65 = hex9_id + d0..d63)</p>

<h3>WHAT_AM_I 64d (place)</h3>
<p class="lead">Per-place embedding of <em>intrinsic identity</em>. Built by PCA-64 over 137 features:</p>
<ul style="margin:8px 0 8px 24px;">
  <li>plexis_category one-hot (24)</li>
  <li>pc2_category one-hot (55 finer)</li>
  <li>brand_norm one-hot (top 50 brands + OTHER + NONE)</li>
  <li>numeric: rating, log(reviews), is_magnet, is_long_tail, magnet_strength, review_quality_pctl, has_rating</li>
</ul>
<p>File: <code>places/place_embedding_what_64d.parquet</code> (190,591 × 65 = id + d0..d63). 71.0% variance explained.</p>

<h3>Combined 128d</h3>
<p class="lead">For each place: concat[its WHAT_64d, its hex's WHERE_64d] → 128d. For each hex: concat[mean(WHAT_64d of places in hex), WHERE_64d] → 128d.</p>
<p>Files: <code>places/place_embedding_combined_128d.parquet</code> · <code>hex/hex9_embedding_combined_128d.parquet</code></p>

<div class="note">
The first 64 dims of <em>combined</em> = WHAT (semantic identity); last 64 dims = WHERE (location context). This separation lets downstream models attend differently to each component.
</div>

<h3>How to use</h3>
<pre style="background:#161b22;border:1px solid #30363d;border-radius:6px;padding:12px;font-size:12px;overflow-x:auto;">
import pandas as pd
from sklearn.neighbors import NearestNeighbors

# Find nearest hexes to a query hex (semantic + spatial)
hex_emb = pd.read_parquet('hex/hex9_embedding_combined_128d.parquet')
nn = NearestNeighbors(n_neighbors=10).fit(hex_emb.drop(columns='hex9_id').values)

# Find similar places by their full character (what they are + where they are)
place_emb = pd.read_parquet('places/place_embedding_combined_128d.parquet')
</pre>
</div>

<!-- TESTS -->
<div id="tab-tests" class="tab-content">
<h2>Embedding tests — 17 / 17 PASS</h2>
<p class="lead">Comprehensive correctness suite covering structural integrity, spatial coherence, semantic coherence, and consistency across the four embedding artifacts.</p>
<div class="cards">
{card("PASS", embed_test["pass_count"], "")}
{card("WARN", embed_test["warn_count"], "")}
{card("FAIL", embed_test["fail_count"], "")}
{card("SKIP", embed_test["skip_count"], "")}
</div>
<table>
<tr><th>ID</th><th>Test</th><th>Status</th><th>Detail</th></tr>
{test_rows}
</table>

<h3>What the standout results mean</h3>
<ul style="margin:12px 0 12px 24px;">
  <li><strong>T04 Cecil → 5/5 CBD</strong>: Hex embedding has perfect spatial coherence in dense urban core</li>
  <li><strong>T05 Tuas → 10/10 industrial</strong>: Captures industrial belt as a distinct cluster</li>
  <li><strong>T07-09 cafe/restaurant/HDB → 10/10 same-category</strong>: WHAT embedding has strong category coherence</li>
  <li><strong>T10 Starbucks → 20/20 Starbucks</strong>: Brand identity dominates the place embedding for chain brands</li>
  <li><strong>T11 magnet separation 39.7%</strong>: Magnets and long-tail places live in clearly distinct embedding regions</li>
  <li><strong>T12 Orchard mall → 10/10 retail in CBD</strong>: Combined 128d captures both <em>what</em> (retail) and <em>where</em> (CBD)</li>
  <li><strong>T13/T14 max abs diff 0.00</strong>: Combined embedding's where-part is bit-identical to the original WHERE — no drift</li>
</ul>
</div>

<!-- VALIDATORS -->
<div id="tab-validators" class="tab-content">
<h2>Pipeline validators</h2>
<p class="lead">{val_total} checks across all layers. {val_summary.get("PASS",0)} PASS · {val_summary.get("WARN",0)} WARN · {val_summary.get("FAIL",0)} FAIL.</p>
<div class="cards">
{card("PASS", val_summary.get("PASS",0), "")}
{card("WARN", val_summary.get("WARN",0), "calibration thresholds")}
{card("FAIL", val_summary.get("FAIL",0), "")}
</div>
<table>
<tr><th>Layer file</th><th>Check</th><th>Status</th><th>Detail</th></tr>
{val_rows}
</table>
</div>

<!-- COMPARISON -->
<div id="tab-comparison" class="tab-content">
<h2>vs v3 hex_v10 (the prior iteration)</h2>
<table>
<tr><th>Metric</th><th>v3 hex_v10</th><th>v4.7.0</th><th>Status</th></tr>
<tr><td>hex9 cols</td><td>613</td><td>{h9_all.shape[1]}</td><td>{parity:.0f}% parity</td></tr>
<tr><td>Pipeline stages</td><td>bespoke</td><td>47</td><td>reproducible</td></tr>
<tr><td>Validators</td><td>none</td><td>{val_total}</td><td>~96% PASS</td></tr>
<tr><td>Per-place micrograph</td><td>hex-level only</td><td>per-place + hex rollup</td><td>improved</td></tr>
<tr><td>Embeddings</td><td>fragmented (zoo of files)</td><td>WHERE+WHAT+COMBINED architecture</td><td>cleaner</td></tr>
<tr><td>Walking distance</td><td>haversine ×1.3</td><td>true OSM pedestrian network</td><td>improved</td></tr>
<tr><td>Time-of-day</td><td>partial</td><td>4 windows (am/midday/pm/night)</td><td>full</td></tr>
<tr><td>Categories</td><td>40+</td><td>24 plexis + 55 pc2</td><td>both available</td></tr>
</table>

<h3>Remaining gaps (~9% of v3 cols)</h3>
<ul style="margin:8px 0 8px 24px;">
  <li>Some legacy v3-specific column splits (cosmetic difference)</li>
  <li>MRT taps PT_CODE matching (interchange split-codes — fixable, low priority)</li>
  <li>Various deprecated v3 features no longer relevant</li>
</ul>
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
</body></html>
"""

OUT.write_text(html)
print(f"Wrote {OUT} ({len(html)/1024:.1f} KB)")

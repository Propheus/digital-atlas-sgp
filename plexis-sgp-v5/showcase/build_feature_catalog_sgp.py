"""
Plexis SGP v5 — feature catalog (data dictionary), HEX8 + PLACE, themed.
100%-described from the curated v5 feature_catalog.json (one line each).
Groups the 801 hex8 master columns by REAL provenance (which source stage
parquet they came from), with a name-pattern fallback for derived columns.
"""
import json, sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from report_theme import page

ROOT = Path.home() / "da-sgp" / "v5"
CAT = json.load(open(ROOT / "catalog" / "feature_catalog.json"))
FEATS = CAT["features"]

MASTER = "hex/hex8_all_features.parquet"
PLACE_MICRO = "places/sgp_places_micrograph.parquet"
PLACE_FINAL = "places/sgp_places_final.parquet"

by_ds = {}
for f in FEATS:
    by_ds.setdefault(f["dataset"], []).append(f)

# ---- provenance map: master column -> friendly family, from source stage tables ----
SRC_FAMILY = {
 "hex/hex8_universe.parquet":               "Identity & admin",
 "hex/hex8_population.parquet":             "Population & demographics",
 "hex/hex8_buildings_clean.parquet":        "Buildings",
 "hex/hex8_built_environment_features.parquet": "Built environment",
 "hex/hex8_roads_clean.parquet":            "Roads & network topology",
 "hex/hex8_transit_clean.parquet":          "Transit & rail",
 "hex/hex8_iso_transit.parquet":            "Isochrone — transit reach",
 "hex/hex8_iso_walk.parquet":               "Isochrone — walk reach",
 "hex/hex8_walkability.parquet":            "Walkability",
 "hex/hex8_land_use.parquet":               "Land use (URA MP2019)",
 "hex/hex8_satellite.parquet":              "Satellite & night-lights",
 "hex/hex8_visibility.parquet":             "Visibility & footfall",
 "hex/hex8_daytime_pop.parquet":            "Daytime population",
 "hex/hex8_labor_shed.parquet":             "Labour shed",
 "hex/hex8_rent_surface.parquet":           "Rent surface",
 "hex/hex8_acra_biz.parquet":               "Business formation (ACRA)",
 "hex/hex8_colo_fit.parquet":               "Co-location fit",
 "hex/hex8_context_pack.parquet":           "Context pack",
 "hex/hex8_pipeline.parquet":               "Development pipeline (GLS/BTO)",
 "hex/hex8_huff_capture.parquet":           "Huff capture / demand",
 "hex/hex8_mobility_features.parquet":      "Mobility & origin-destination",
 "hex/hex8_mobility_pack.parquet":          "Mobility pack (access/desert)",
}
col2fam = {}
for ds, fam in SRC_FAMILY.items():
    for f in by_ds.get(ds, []):
        col2fam.setdefault(f["column"], fam)

# ---- name-pattern fallback for derived/composite master columns ----
def pattern_family(c):
    if c in ("hex8_id","lat","lng","parent_subzone","parent_subzone_name",
             "parent_region","parent_pa","zone_type_broad","hex_area_km2"):
        return "Identity & admin"
    # ring-pooled derivatives (pop-weighted / max over k=1,2 rings) — check FIRST
    if re.match(r"^(pw1|pw2|max1|max2)_", c): return "Spatial context (rings)"
    rules = [
     (r"^nvp_", "Population personas (NVP)"),
     (r"^bus_taps_|^speed_band|^jam_pct|^dyn_", "Mobility & origin-destination"),
     (r"^sig_", "Roads & network topology"),
     (r"^ca_", "Commercial activity / spend"),
     (r"^pc_|^pc2_|^osm_|tourist|silver_zone", "Places / POI composition"),
     (r"^wc_", "Satellite & night-lights"),
     (r"commercial_intensity|density_pressure", "Composite indices"),
     (r"^pop_|^pct_|_share$|dependency|sex_ratio|elderly|child|youth|dorm|hdb", "Population & demographics"),
     (r"^lu_", "Land use (URA MP2019)"),
     (r"^bldg_|building|^far\b|floor_area|highrise|gross_plot", "Buildings"),
     (r"^road_|intersection|junction|arterial|betweenness|street", "Roads & network topology"),
     (r"mrt|lrt|rail|^transit|station|interchange|bus_stop|gtfs", "Transit & rail"),
     (r"^iso_walk", "Isochrone — walk reach"),
     (r"^iso_transit|^iso_", "Isochrone — transit reach"),
     (r"walk|ped|15min|min15|^walkab", "Walkability"),
     (r"^nl_|night|viirs|^sat_|satellite|ndvi|green", "Satellite & night-lights"),
     (r"^vis_|footfall|frontage|visib", "Visibility & footfall"),
     (r"^dt_|daytime|worker_proxy", "Daytime population"),
     (r"labor|labour|jobs|workplace", "Labour shed"),
     (r"rent|psf|psm|resale|hdb_resale|price", "Rent / price surface"),
     (r"^biz_|acra|formation|churn|dead_share", "Business formation (ACRA)"),
     (r"^colo|co_?location|cotenan|anchor", "Co-location fit"),
     (r"^gap_|whitespace|unserved", "Saturation & whitespace gap"),
     (r"^sat_|_per_1k$|saturation", "Saturation & whitespace gap"),
     (r"^cap_|huff|capture|demand", "Huff capture / demand"),
     (r"^pull_|gravity|access_index|accessibility", "Accessibility / demand-pull"),
     (r"^ring1_|^ring2_|^grad_|_ring_|neighbour", "Spatial context (rings)"),
     (r"^syn_|_x_|interaction", "Synergy interactions"),
     (r"^pc_cat_|^pc2_cat_|^n_|poi|places|entropy|category", "Places / POI composition"),
     (r"^mg_|micrograph", "Micrograph (local context)"),
     (r"^adq_|adequacy|^min15", "Adequacy & 15-min city"),
     (r"^pipe_|pipeline|gls|bto|dev_capacity", "Development pipeline (GLS/BTO)"),
     (r"^od_|origin|destination|commute|throughput", "Mobility & origin-destination"),
     (r"hawker|clinic|chas|school|park|amenity", "Amenities & services"),
     (r"vulnerab|equity|livab|family_index|composite|vibran|index$", "Composite indices"),
     (r"archetype|cluster", "Archetypes"),
     (r"dist_.*_m$|^dist_", "Distances"),
    ]
    for pat, fam in rules:
        if re.search(pat, c): return fam
    return "Other / derived"

PACK_SCORES = {
 "retail_whitespace_score","retail_competition_pressure","format_fit_score",
 "retail_cannibalization_score","retail_delivery_score","retail_footfall_score","rent_demand_tier",
 "re_feasibility_score","re_livability_score","re_momentum_score","re_enbloc_score",
 "re_collateral_score","re_yield_proxy","re_lease_decay_penalty",
 "utility_load_score","utility_load_growth_score","utility_water_score","utility_waste_score",
 "utility_ev_gap_score","utility_diurnal_swing","utility_equity_score","utility_resilience_score",
 "mobility_access_score","mobility_desert_priority","mobility_crowding_score","mobility_tod_score",
 "mobility_ridehail_score","mobility_firstlast_gap_score","mobility_parking_stress","modal_split_proxy",
 "risk_fire_score","risk_auto_score","risk_health_score","risk_bi_failure_score","risk_collateral_score",
 "risk_nuisance_score","risk_coastal_proxy","insurance_risk_score","insurance_accumulation_band",
}

def family_of(c):
    # strong overrides that beat source-table provenance
    if c in PACK_SCORES: return "Domain pack scores (folded in)"
    if c.startswith("lu_"): return "Land use (URA MP2019)"
    return col2fam.get(c) or pattern_family(c)

FAM_ORDER = [
 "Identity & admin","Population & demographics","Population personas (NVP)","Land use (URA MP2019)","Buildings",
 "Built environment","Roads & network topology","Distances","Transit & rail",
 "Isochrone — walk reach","Isochrone — transit reach","Walkability",
 "Accessibility / demand-pull","Mobility & origin-destination","Mobility pack (access/desert)",
 "Daytime population","Labour shed","Satellite & night-lights","Visibility & footfall",
 "Places / POI composition","Micrograph (local context)","Amenities & services",
 "Huff capture / demand","Saturation & whitespace gap","Co-location fit",
 "Commercial activity / spend","Business formation (ACRA)","Rent surface","Rent / price surface",
 "Development pipeline (GLS/BTO)","Adequacy & 15-min city","Context pack",
 "Spatial context (rings)","Synergy interactions","Composite indices","Archetypes",
 "Domain pack scores (folded in)","Other / derived",
]
# families whose hex features are derived from the place/POI catalog
PLACE_DERIVED = {"Places / POI composition","Micrograph (local context)","Huff capture / demand",
                 "Saturation & whitespace gap","Co-location fit","Visibility & footfall",
                 "Amenities & services"}

def fmt_num(v):
    try: v = float(v)
    except (TypeError, ValueError): return None
    if v != v: return None
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:.2f}"

def stat(f):
    dt = str(f.get("dtype",""))
    if dt in ("object","bool","category") or f.get("min","") in ("", None):
        nu = f.get("n_unique","")
        if nu not in ("", None):
            try: return f"{int(float(nu)):,} categories"
            except: pass
        s = f.get("sample","")
        return f"e.g. {s}" if s else "—"
    mn, mx, mu = fmt_num(f.get("min")), fmt_num(f.get("max")), fmt_num(f.get("mean"))
    if mn is None: return "—"
    return f"{mn} – {mx} (μ {mu})" if mu else f"{mn} – {mx}"

def desc(f):
    d = (f.get("description") or "").strip()
    u = (f.get("units") or "").strip()
    if d and u and u not in ("string","") and u.lower() not in d.lower():
        return f"{d} <span style='color:var(--muted)'>· {u}</span>"
    return d or f["column"].replace("_"," ").capitalize()

def rows_html(items):
    return "".join(
        f"<tr><td class='f'>{f['column']}</td><td>{desc(f)}</td>"
        f"<td class='t'>{f.get('dtype','')}</td><td class='s'>{stat(f)}</td></tr>"
        for f in items)

# ---------- assemble HEX ----------
master = by_ds[MASTER]
fam_rows = {}
for f in master:
    fam_rows.setdefault(family_of(f["column"]), []).append(f)

n_place_derived = sum(len(fam_rows.get(g, [])) for g in PLACE_DERIVED)

hex_sec = ""
for g in FAM_ORDER:
    items = fam_rows.get(g)
    if not items: continue
    tag = "<span class='tag'>place-derived</span>" if g in PLACE_DERIVED else ""
    hex_sec += (f"<h2>{g}{tag} <span class='n'>· {len(items)}</span></h2>"
                f"<table><tr><th>Feature</th><th>Description</th><th>Type</th>"
                f"<th>Range (μ)</th></tr>{rows_html(items)}</table>")
# any families not in FAM_ORDER (safety)
for g, items in fam_rows.items():
    if g in FAM_ORDER: continue
    hex_sec += (f"<h2>{g} <span class='n'>· {len(items)}</span></h2>"
                f"<table><tr><th>Feature</th><th>Description</th><th>Type</th>"
                f"<th>Range (μ)</th></tr>{rows_html(items)}</table>")

# ---------- assemble PLACE ----------
place_sec = ""
PLACE_BLOCKS = [("Place identity & classification", PLACE_FINAL),
                ("Per-place micrograph (local context)", PLACE_MICRO)]
n_place_feats = 0
for title, ds in PLACE_BLOCKS:
    items = by_ds.get(ds, [])
    if not items: continue
    n_place_feats += len(items)
    place_sec += (f"<h2>{title} <span class='n'>· {len(items)}</span></h2>"
                  f"<table><tr><th>Feature</th><th>Description</th><th>Type</th>"
                  f"<th>Range (μ)</th></tr>{rows_html(items)}</table>")

# ---------- cards ----------
N_HEX = 1191; N_PLACES = 190591
cards = [("Hex8 cells", f"{N_HEX:,}"), ("Hex features", f"{len(master)}"),
         ("Place-derived", f"{n_place_derived}"), ("Per-place feats", f"{n_place_feats}"),
         ("Places", f"{N_PLACES/1e3:.0f}K"), ("Embeddings", "e1·p1")]
card_html = "".join(f"<div class='card'><div class='cv'>{v}</div><div class='cl'>{l}</div></div>"
                    for l, v in cards)

body = f"""
<h1>Singapore Atlas — <span class="accent">Feature Catalog</span></h1>
<p class="sub">Data dictionary · {N_HEX:,} H3-8 cells · {len(master)} hex features + {n_place_feats} per-place features · one line each · Plexis SGP v5.5.0</p>
<div class="cards">{card_html}</div>
<div class="banner">Place-derived features per hex: YES — {n_place_derived} of {len(master)} hex features are aggregated from the {N_PLACES:,} Singapore places + amenity/station venues (tagged below).</div>

<h1 style="font-size:20px;margin:34px 0 0">Per-hex features <span class="n" style="font-size:13px;color:var(--muted)">· {len(master)}</span></h1>
{hex_sec}

<h1 style="font-size:20px;margin:40px 0 0">Per-place features <span class="n" style="font-size:13px;color:var(--muted)">· {n_place_feats} (+ p1 64-d embedding in a separate file)</span></h1>
{place_sec}
<p class="note">Region embedding <code>e1</code> (256-d, <code>hex/hex8_embedding_plexis_e1_256d.parquet</code>) and place embedding <code>p1</code> (64-d, <code>places/place_embedding_plexis_p1_64d.parquet</code>) are stored separately, not among the columns above. Five domain packs (retail / real-estate / utilities / transport / insurance) add 39 hero scores as sidecar parquets joined on <code>hex8_id</code>.</p>
"""
out = ROOT / "showcase" / "SGP_HEX_FEATURE_CATALOG.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page("Singapore Atlas — Feature Catalog", body))
print(f"wrote {out}; hex {len(master)} ({n_place_derived} place-derived) + place {n_place_feats}")
other = fam_rows.get("Other / derived", [])
if other: print("OTHER/DERIVED:", [f['column'] for f in other])

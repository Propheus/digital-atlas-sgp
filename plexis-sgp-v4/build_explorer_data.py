"""Export hex8 + subzone GeoJSON + layer manifest for the Explorer app."""
import json, numpy as np, pandas as pd, h3
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "explorer_export"; OUT.mkdir(exist_ok=True)

# ---- colorable metrics: id -> (column, label, group, unit, scale_lo, scale_hi, reverse, desc) ----
METRICS = [
 ("pop_total","pop_total_all","Total population","Population","ppl",0,None,0,
  "Resident + non-resident headcount per hex8. Calibrated to SingStat Jun-2024 (6.04M nationally)."),
 ("nonres_share","nonres_share","Non-resident share","Population","frac",0,1,0,
  "Fraction of population that is non-resident (work-permit, dorm, FDW, students). High in industrial/CBD."),
 ("pop_dorm","pop_dorm","Dorm workers","Population","ppl",0,None,0,
  "Migrant-worker dormitory population placed at real MOM dorm locations (439,198 nationally, DASL H2-2024)."),
 ("nl_2024","nl_2024","Night lights 2024","Night lights","rad",0,None,0,
  "VIIRS night-light radiance 2024 — proxy for built/economic intensity."),
 ("nl_change","nl_change_pct","Night-light growth","Night lights","%",-50,50,0,
  "% change in night lights 2022->2024. Positive = brightening (growth corridor)."),
 ("commercial_activity","commercial_activity_index","Commercial activity","Commercial","0-1",0,1,0,
  "NEW footfall-weighted economic-activity index: night lights + spend proxy + transit taps + place density + OD throughput. Distinct from supply-only commercial_intensity (corr 0.84)."),
 ("commercial_intensity","commercial_intensity","Commercial intensity (supply)","Commercial","0-1",0,1,0,
  "Supply/morphology composite: commercial place mix + commercial night-light + commercial land-use share."),
 ("od_throughput","od_throughput","OD throughput","Mobility (OD)","trips/mo",0,None,0,
  "Total transit journeys originating + terminating in this hex (LTA DataMall OD, Apr-2026 weekday monthly). Bus+train, 100% mapped."),
 ("od_net","od_net_flow","OD net flow (in-out)","Mobility (OD)","trips/mo",None,None,0,
  "Inbound minus outbound journeys. Positive = net destination (job/retail magnet); negative = net origin (residential)."),
 ("breathing","breathing_idx","Day-night breathing","Emergent","z",None,None,0,
  "EMERGENT: z(OD inflow) - z(resident pop). High = fills by day, empties at night (job center). Low = empties by day (bedroom community)."),
 ("latent_demand","latent_demand","Latent retail demand","Emergent","z",None,None,0,
  "EMERGENT: z(commercial activity) - z(commercial supply). High = high footfall but under-built retail (opportunity)."),
 ("transit","transit_score","Transit access","Mobility","0-1",0,1,0,
  "Composite transit accessibility (MRT/LRT/bus proximity + frequency)."),
 ("walkability","walkability_score","Walkability","Mobility","0-1",0,1,0,
  "Pedestrian-infrastructure + amenity walk-distance composite."),
 ("vibrancy","vibrancy_index","Vibrancy","Composites","0-1",0,1,0,
  "Places + magnets + reviews + transit + night lights."),
 ("livability","livability_index","Livability","Composites","0-1",0,1,0,
  "Walkability + green + amenities + transit (note: stale vs current parks layer)."),
 ("density","density_pressure","Density pressure","Composites","0-1",0,1,0,
  "Population + buildings + low road space."),
 ("affluence","nvp_affluence_idx","Persona affluence","Personas","0-1",0,1,0,
  "NVIDIA Nemotron persona affluence proxy (university + professional/manager + finance/infocomm). PA-resolution broadcast."),
 ("median_age","nvp_median_age","Persona median age","Personas","yrs",20,70,0,
  "Median age of adult personas in this planning area (NVIDIA Nemotron, PA-resolution)."),
 ("pct_univ","nvp_pct_univ","% university-educated","Personas","frac",0,1,0,
  "Share of personas with a university degree (PA-resolution)."),
 ("hdb_resale","hdb_resale_4r_median_psm","HDB resale 4-room $/sqm","Housing","$/m2",0,None,0,
  "Median 4-room HDB resale price per sqm (227k transactions, town-broadcast)."),
 # --- Places (POI composition; ~0.74 km2 per hex8) ---
 ("place_density","pc_total","Place density","Places","places",0,None,0,
  "Total mapped places (POIs) per hex8 (~0.74 km2) — overall point-of-interest density."),
 ("place_diversity","pc_diversity","Place-mix diversity","Places","0-1",0,1,0,
  "Category diversity (entropy) of the place mix. High = mixed-use; low = monofunctional."),
 ("magnets","pc_magnets","Magnet anchors","Places","count",0,None,0,
  "High-draw anchor places (malls, hubs, major attractions; 30+ review demand magnets)."),
 ("brands","pc_unique_brands","Unique brands","Places","count",0,None,0,
  "Distinct retail/F&B brands present — chain/commercial richness."),
 ("avg_rating","pc_avg_rating","Avg place rating","Places","stars",2.5,5,0,
  "Mean rating of rated places — quality proxy."),
 ("reviews","pc_total_reviews","Total reviews","Places","count",0,None,0,
  "Sum of place review counts — popularity / footfall proxy."),
 ("fnb","pc_cat_restaurant","F&B (restaurants)","Places","count",0,None,0,
  "Restaurant place count (see hawker/cafe/fast-food in the detail panel)."),
 ("retail","pc_cat_shopping_retail","Retail shops","Places","count",0,None,0,
  "Shopping / retail place count."),
 # --- Site-selection layers (S1-S9, gated; SITE_SELECTION_VALIDATION.md) ---
 ("cap_total","cap_total","Capture potential (all)","Opportunity","outlet-eq",0,None,0,
  "S1 Huff model: demand (outlet-equivalents) a NEW outlet at the best spot in this hex would capture across 11 categories, net of existing competition. 1.0 = supports one average outlet."),
 ("cap_supermarket","cap_supermarket","Supermarket capture","Opportunity","outlet-eq",0,None,0,
  "Competition-adjusted demand winnable by a new supermarket. Yunnan (the known FairPrice desert) ranks p96."),
 ("cap_cafe","cap_cafe_coffee","Cafe capture","Opportunity","outlet-eq",0,None,0,
  "Competition-adjusted demand winnable by a new cafe. Saturated Orchard ranks p03 — the inversion is the point."),
 ("roi_rent","roi_cap_per_rent_total","Capture per rent (ROI)","Opportunity","ratio",0,None,0,
  "cap_total / residential rent $psf — opportunity per occupancy-cost proxy. Gray where no rent observation within 2.5 km."),
 ("unserved_sm","iso_walk10_unserved_pop_supermarket","Unserved pop (supermarket)","Opportunity","ppl",0,None,0,
  "Residents reachable in a 10-min walk who have NO supermarket within 800 m of home. Most novel column in the atlas (max |r|=0.14 vs all prior features)."),
 ("iso_walk_pop","iso_walk10_pop","10-min walk catchment","Catchment","ppl",0,None,0,
  "Population within an 800 m NETWORK walk of the hex activity centre (node-field demand, k=4 multi-source). Severance-aware, unlike rings."),
 ("iso_transit_pop","iso_transit15_pop","15-min transit reach","Catchment","ppl",0,None,0,
  "Population reachable door-to-door in 15 min by weekday-AM transit (GTFS graph + walk arms). Interchange towns peak ~250K."),
 ("dt_pop","dt_pop","Daytime population","Catchment","ppl",0,None,0,
  "Commuter daytime headcount: residents - AM out + AM in (OD-based, 0.62 PT mode share)."),
 ("labor45","labor_pool_45m","Labor pool (45-min)","Catchment","ppl",0,None,0,
  "Working-age population that can reach this hex within 45-min transit. CBD = 1.68M (59.6% of workforce); Tuas = p0."),
 ("biz_live","biz_live_robust","Live businesses (robust)","Business","count",0,None,0,
  "ACRA live entities, per-postal contribution capped at 100 (registered-agent buildings winsorized). 94% of 2.07M entities geocoded."),
 ("biz_mort","biz_recent_dead_share","Business mortality (2018+)","Business","frac",0,1,0,
  "Share of 2018+ registered entities now deregistered — churn-risk signal. Gray where no entities."),
 ("rent","rent_resi_psf_med","Resi rent $psf/mo","Business","$psf",None,None,0,
  "URA private rental medians (913 projects, last 4 quarters, IDW 2.5 km). Commercial rent not openly available — this is the spatial price surface."),
 ("exit_footfall","vis_exit_footfall","MRT exit footfall","Business","taps/day",0,None,0,
  "Weekday taps at the nearest station exit (<=400 m), split per exit from per-station PV. Few-exit busy stations (Punggol, Novena) legitimately beat 13-exit Orchard."),
 ("pipe_mrt","pipe_mrt_dist_m","Future MRT distance","Future","m",None,None,1,
  "Distance to the nearest FUTURE rail station (MP2019 minus existing Mar-2026: 37 stations — full JRL + Keppel CCL6). Reversed: closer = brighter."),
 ("pipe_cap","pipe_dev_capacity_res","Dev capacity (FAR headroom)","Future","FAR-units",0,None,0,
  "(allowed GPR - built FAR) x residential zoning share. Matilda 0.50 / Bidadari 0.34; built-out Toa Payoh Central = 0."),
]
# broad detail props (union with metric cols), grouped for the panel
DETAIL = {
 "Identity": ["parent_pa","parent_subzone_name","parent_region","archetype_label"],
 "Population": ["pop_total_all","pop_resident","pop_nonresident","pop_dorm","nonres_share","pop_65plus","pop_0_14"],
 "Mobility (OD)": ["od_throughput","od_in_trips","od_out_trips","od_net_flow","od_self_containment","od_dest_entropy","od_am_pm_out_ratio"],
 "Transit & walk": ["transit_score","walkability_score","daily_bus_taps","daily_train_taps"],
 "Commercial": ["commercial_activity_index","commercial_intensity","ca_footfall","ca_taps","ca_places","nl_2024","nl_change_pct","nl_commercial_indicator"],
 "Places": ["pc_total","pc_diversity","pc_dominant_category","pc_magnets","pc_unique_brands","pc_avg_rating","pc_total_reviews","pc_cat_restaurant","pc_cat_cafe_coffee","pc_cat_hawker","pc_cat_fast_food","pc_cat_shopping_retail","pc_cat_supermarket","pc_cat_convenience","pc_cat_health_medical","pc_cat_education","pc_cat_park_open","pc_cat_business_office","pc_cat_fitness_recreation","pc_cat_beauty_personal"],
 "Composites": ["vibrancy_index","livability_index","family_index","density_pressure","commercial_intensity"],
 "Personas (NVIDIA, PA-level)": ["nvp_median_age","nvp_affluence_idx","nvp_pct_univ","nvp_pct_age_55plus","nvp_occ_professional","nvp_occ_manual","nvp_ind_finance","nvp_ind_manufacturing","nvp_persona_n","nvp_low_n"],
 "Housing": ["hdb_resale_4r_median_psm"],
 "Emergent": ["breathing_idx","latent_demand"],
 "Opportunity (S1 capture)": ["cap_total","cap_best_category","cap_supermarket",
    "cap_cafe_coffee","cap_restaurant","cap_hawker","cap_convenience",
    "cap_health_medical","cap_fitness_recreation","cap_shopping_retail",
    "roi_cap_per_rent_total","roi_cap_per_rent_supermarket"],
 "Catchment (S2/S3/S5)": ["iso_walk10_pop","iso_walk10_spend","iso_walk10_places",
    "iso_walk10_magnets","iso_severance_ratio",
    "iso_walk10_unserved_pop_supermarket","iso_walk10_unserved_pop_cafe_coffee",
    "iso_transit15_pop","iso_transit15_places","dt_pop","dt_ratio","dt_class",
    "labor_pool_45m","labor_pool_30m","jobs_reach_45m","labor_jobs_balance_45m"],
 "Business (S4 ACRA)": ["biz_live_count","biz_live_robust","biz_formation_5y",
    "biz_dead_share","biz_recent_dead_share","biz_median_age_yrs",
    "biz_per_address","biz_company_share"],
 "Site factors (S6-S9)": ["colo_fit_cafe_coffee","colo_fit_supermarket",
    "colo_fit_restaurant","vis_exit_footfall","vis_exit_station",
    "vis_traffic_pass_proxy","vis_corner_premium","rent_resi_psf_med",
    "rent_resolution","pipe_new_mrt_within_800m","pipe_mrt_name",
    "pipe_mrt_dist_m","pipe_dev_capacity_res","pipe_dev_capacity_com"],
 "Context (S10)": ["cons_bldg_count","cons_cluster_flag","carpark_capacity_lots",
    "dist_polyclinic_m","dist_wet_market_m","wet_market_count",
    "petrol_station_count","coworking_count","condo_project_count",
    "female_pop_share","bto_uc_units_town","bto_pipeline_est"],
}


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    return (s - s.mean()) / (s.std() + 1e-9)


def export_hex8():
    df = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    active = (df.get("pop_total_all", 0) > 50) | (df.get("od_throughput", 0) > 0)
    # AMENDED 2026-06-10 (S3 validation): the old z(od_in_trips)-z(pop) form
    # was direction-blind — full-day in~=out (rho .996), so it collapsed to
    # throughput-vs-pop (rho .999) and scored interchange town centres
    # (Yishun Central, Woodgrove) as job centers. AM-directional form:
    df["breathing_idx"] = np.where(active, z(df["dt_net_am_persons"]), np.nan).round(3)
    df["latent_demand"] = np.where(active, z(df["commercial_activity_index"]) - z(df["commercial_intensity"]), np.nan).round(3)

    allprops = sorted(set(c for cols in DETAIL.values() for c in cols) | {m[1] for m in METRICS})
    allprops = [c for c in allprops if c in df.columns]
    feats = []
    for _, r in df.iterrows():
        try:
            bnd = h3.cell_to_boundary(r["hex8_id"])  # [(lat,lng),...]
        except Exception:
            continue
        ring = [[lng, lat] for lat, lng in bnd] + [[bnd[0][1], bnd[0][0]]]
        props = {"hex8_id": r["hex8_id"]}
        for c in allprops:
            v = r[c]
            if isinstance(v, (np.integer,)): v = int(v)
            elif isinstance(v, (np.floating,)): v = None if pd.isna(v) else round(float(v), 4)
            elif isinstance(v, (np.bool_, bool)): v = bool(v)
            elif pd.isna(v): v = None
            props[c] = v
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": "Polygon", "coordinates": [ring]}})
    fc = {"type": "FeatureCollection", "features": feats}
    json.dump(fc, open(OUT / "hex8_explore.geojson", "w"))
    print(f"hex8_explore.geojson: {len(feats)} features, {len(allprops)} props")
    return df


def export_subzone():
    try:
        gj = json.load(open(ROOT / "boundaries/subzones.geojson"))
    except FileNotFoundError:
        print("no subzones.geojson; skipping"); return
    sz = pd.read_parquet(ROOT / "hex/subzone_all_features.parquet").set_index("subzone_c")
    keep = [c for c in sz.columns if c in {x for cols in DETAIL.values() for x in cols} or c in {m[1] for m in METRICS}]
    n = 0
    for f in gj["features"]:
        p = f["properties"]
        code = p.get("subzone_c") or p.get("SUBZONE_C") or p.get("name")
        if code in sz.index:
            row = sz.loc[code]
            for c in keep:
                v = row[c]
                p[c] = None if pd.isna(v) else (int(v) if isinstance(v, np.integer) else round(float(v), 4) if isinstance(v, np.floating) else v)
            n += 1
    json.dump(gj, open(OUT / "subzone_explore.geojson", "w"))
    print(f"subzone_explore.geojson: {n} matched")


def export_manifest(df):
    metrics = []
    for mid, col, label, group, unit, lo, hi, rev, desc in METRICS:
        if col not in df.columns: continue
        s = pd.to_numeric(df[col], errors="coerce")
        d_lo = float(np.nanpercentile(s, 2)) if lo is None else lo
        d_hi = float(np.nanpercentile(s, 98)) if hi is None else hi
        metrics.append({"id": mid, "col": col, "label": label, "group": group,
                        "unit": unit, "domain": [round(d_lo,3), round(d_hi,3)],
                        "reverse": bool(rev), "desc": desc})
    # group order = category pill order in the app; "Composites"/"Personas"/
    # legacy group names are normalized the way the deployed manifest does
    RENAME = {"Night lights": "Commercial", "Mobility (OD)": "Mobility",
              "Composites": "Living", "Personas": "People", "Housing": "Living"}
    for m in metrics:
        m["group"] = RENAME.get(m["group"], m["group"])
    cats = list(dict.fromkeys(m["group"] for m in metrics))
    json.dump({"metrics": metrics, "detail_groups": DETAIL, "categories": cats},
              open(OUT / "layers.json", "w"), indent=2)
    print(f"layers.json: {len(metrics)} metrics, categories: {cats}")


if __name__ == "__main__":
    d = export_hex8()
    export_subzone()
    export_manifest(d)
    print("done ->", OUT)

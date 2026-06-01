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
]
# broad detail props (union with metric cols), grouped for the panel
DETAIL = {
 "Identity": ["parent_pa","parent_subzone_name","parent_region","archetype_label"],
 "Population": ["pop_total_all","pop_resident","pop_nonresident","pop_dorm","nonres_share","pop_65plus","pop_0_14"],
 "Mobility (OD)": ["od_throughput","od_in_trips","od_out_trips","od_net_flow","od_self_containment","od_dest_entropy","od_am_pm_out_ratio"],
 "Transit & walk": ["transit_score","walkability_score","daily_bus_taps","daily_train_taps"],
 "Commercial": ["commercial_activity_index","commercial_intensity","ca_footfall","ca_taps","ca_places","nl_2024","nl_change_pct","nl_commercial_indicator"],
 "Places": ["pc_total","pc_magnets","pc_cat_business_office","pc_cat_shopping_retail","pc_cat_restaurant","pc_cat_cafe_coffee"],
 "Composites": ["vibrancy_index","livability_index","family_index","density_pressure","commercial_intensity"],
 "Personas (NVIDIA, PA-level)": ["nvp_median_age","nvp_affluence_idx","nvp_pct_univ","nvp_pct_age_55plus","nvp_occ_professional","nvp_occ_manual","nvp_ind_finance","nvp_ind_manufacturing","nvp_persona_n","nvp_low_n"],
 "Housing": ["hdb_resale_4r_median_psm"],
 "Emergent": ["breathing_idx","latent_demand"],
}


def z(s):
    s = pd.to_numeric(s, errors="coerce")
    return (s - s.mean()) / (s.std() + 1e-9)


def export_hex8():
    df = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet")
    active = (df.get("pop_total_all", 0) > 50) | (df.get("od_throughput", 0) > 0)
    df["breathing_idx"] = np.where(active, z(df["od_in_trips"]) - z(df["pop_resident"]), np.nan).round(3)
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
    json.dump({"metrics": metrics, "detail_groups": DETAIL}, open(OUT / "layers.json", "w"), indent=2)
    print(f"layers.json: {len(metrics)} metrics")


if __name__ == "__main__":
    d = export_hex8()
    export_subzone()
    export_manifest(d)
    print("done ->", OUT)

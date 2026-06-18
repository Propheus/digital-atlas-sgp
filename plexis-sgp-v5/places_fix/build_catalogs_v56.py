"""
Plexis SGP v5.6.1 — (re)generate the three catalogs into catalog/:
  DATA_CATALOG          dataset/layer inventory (json + md)
  FEATURE_CATALOG       every column across the masters + places (json + md + parquet)
  PLACES_CATEGORY_CATALOG  the 26-category taxonomy + brand/flag stats (json + md)
Reads the LIVE v5.6.1 parquets; reuses curated descriptions from the existing
feature_catalog.parquet where column names still match.
"""
import json, time, glob, os
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/azureuser/da-sgp/v5")
CAT = ROOT / "catalog"
TS = time.strftime("%Y-%m-%dT%H:%M:%S")
VER = json.load(open(CAT / "atlas_manifest.json")).get("version", "5.6.1")

# ---------- dataset descriptions ----------
DS_DESC = {
 "hex8_all_features": "Master hex8 feature bundle (product scale, ~0.74 km²) — every feature per cell",
 "hex9_all_features": "Master hex9 feature bundle (~0.10 km²; fine, not used in products)",
 "subzone_all_features": "Master subzone feature bundle (URA MP2019)",
 "hex8_place_composition": "Per-hex place counts by category (pc_cat_*) + diversity/magnets",
 "hex8_huff_capture": "Huff capturable demand per category (cap_*)",
 "hex8_pop_weighted": "Pop-weighted ring poolings (pw1/pw2/max1/max2)",
 "hex8_mobility_pack": "Travel-times to anchors + access/desert mobility metrics",
 "sgp_places_final": "All Singapore places (cleaned, canonical) — name/category/brand/flags",
 "sgp_places_micrograph": "Per-venue local-context micrograph (pmg_*)",
 "hex8_embedding_plexis_e1_256d": "Hex region embedding e1 (256-d, hybrid)",
 "place_embedding_plexis_p1_64d": "Place embedding p1 (64-d, contrastive)",
}
def scale_of(name):
    for s in ("hex9","hex8","subzone"):
        if name.startswith(s): return s
    if "place" in name or name.startswith("sgp_places"): return "place"
    return "other"

# ============ A. DATA CATALOG ============
rows = []
for f in sorted(glob.glob(str(ROOT/"hex"/"*.parquet")) + glob.glob(str(ROOT/"places"/"*.parquet"))
                + glob.glob(str(CAT/"*.parquet"))):
    name = Path(f).stem
    try:
        import pyarrow.parquet as pq
        md = pq.ParquetFile(f).metadata
        nr, nc = md.num_rows, md.num_columns
    except Exception:
        d = pd.read_parquet(f); nr, nc = d.shape
    rows.append({"dataset": name, "scale": scale_of(name),
                 "path": os.path.relpath(f, ROOT), "rows": int(nr), "cols": int(nc),
                 "size_mb": round(os.path.getsize(f)/1e6, 2),
                 "description": DS_DESC.get(name, "")})
data_cat = {"atlas": "Plexis SGP", "version": VER, "generated_at": TS,
            "n_datasets": len(rows), "datasets": rows}
json.dump(data_cat, open(CAT/"DATA_CATALOG.json","w"), indent=1)
with open(CAT/"DATA_CATALOG.md","w") as fh:
    fh.write(f"# Plexis SGP — Data Catalog (v{VER})\n\n*{len(rows)} datasets · generated {TS}*\n\n")
    fh.write("| Dataset | Scale | Rows | Cols | Size MB | Description |\n|---|---|--:|--:|--:|---|\n")
    for r in rows:
        fh.write(f"| `{r['dataset']}` | {r['scale']} | {r['rows']:,} | {r['cols']} | {r['size_mb']} | {r['description']} |\n")
print(f"DATA_CATALOG: {len(rows)} datasets", flush=True)

# ============ B. FEATURE CATALOG (refresh) ============
# reuse curated descriptions from the existing catalog
old = pd.read_parquet(CAT/"feature_catalog.parquet") if (CAT/"feature_catalog.parquet").exists() else pd.DataFrame(columns=["column","description","units","derivation"])
desc_map = dict(zip(old["column"], old["description"]))
unit_map = dict(zip(old["column"], old.get("units", pd.Series(dtype=str))))

CURATED_NEW = {
 "is_storefront": "True = manned commercial premise; False = unmanned (ATM/vending/locker) or pure transit infra",
 "host_venue": "Venue this place sits inside (co-located tenant), else empty",
 "operator": "Food-court / coffeeshop operator above the stall (parent_brand)",
 "parent_brand": "Operator brand for stalls inside a food court / coffeeshop",
 "is_duplicate": "True = a duplicate/alias of canonical_id (filter out for supply counts)",
 "canonical_id": "The canonical place id this row maps to",
 "zero_reviews": "True if reviews_count == 0 (new/unlisted vs no-traffic — ambiguous)",
 "is_phantom_suspect": "Duplicate with 0 reviews — likely phantom/alias",
 "pc_cat_financial_services": "Count of financial venues in cell (ATM/bank/insurance/remittance)",
 "pc_cat_automated_kiosk": "Count of unmanned automated points (vending/locker/AXS) in cell",
 "brand_norm": "Canonical chain brand (null = independent or unresolved)",
 "brand_source": "How brand was resolved (scrape / dict / llm)",
}
def describe(col):
    if col in desc_map and isinstance(desc_map[col], str) and desc_map[col].strip(): return desc_map[col]
    if col in CURATED_NEW: return CURATED_NEW[col]
    if col.startswith("pc_cat_"): return f"Count of {col[7:]} places in cell"
    if col.startswith("cap_"): return f"Huff capturable demand for {col[4:]} (review-free)"
    if col.startswith("gap_"): return f"Demand-vs-supply whitespace for {col[4:]}"
    return col.replace("_"," ").capitalize()

def col_stats(s):
    num = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
    r = {"dtype": str(s.dtype), "null_pct": round(float(s.isna().mean()*100),2)}
    if num:
        r.update(min=round(float(s.min()),4) if s.notna().any() else "",
                 max=round(float(s.max()),4) if s.notna().any() else "",
                 mean=round(float(s.mean()),4) if s.notna().any() else "",
                 n_unique="", sample="")
    else:
        r.update(min="",max="",mean="", n_unique=int(s.nunique()),
                 sample=str(s.dropna().iloc[0])[:40] if s.notna().any() else "")
    return r

SCAN = {"hex8_all_features":"hex8","hex9_all_features":"hex9","subzone_all_features":"subzone",
        "sgp_places_final":"place","sgp_places_micrograph":"place"}
feat_rows = []
for ds, scale in SCAN.items():
    sub = "places" if scale=="place" else "hex"
    df = pd.read_parquet(ROOT/sub/f"{ds}.parquet")
    for c in df.columns:
        st = col_stats(df[c])
        feat_rows.append({"dataset": f"{sub}/{ds}.parquet", "scale": scale, "column": c,
                          "description": describe(c), "units": unit_map.get(c,"") or "", **st})
fc = pd.DataFrame(feat_rows)
for c in ["min","max","mean","n_unique","sample","units"]:
    fc[c] = fc[c].astype(str).replace("nan","")
fc.to_parquet(CAT/"feature_catalog.parquet", index=False)
json.dump({"atlas":"Plexis SGP","version":VER,"generated_at":TS,"n_features":len(fc),
           "scales":{s:int((fc.scale==s).sum()) for s in fc.scale.unique()},
           "features": fc.fillna("").to_dict("records")},
          open(CAT/"feature_catalog.json","w"), indent=1, default=str)
with open(CAT/"FEATURE_CATALOG.md","w") as fh:
    fh.write(f"# Plexis SGP — Feature Catalog (v{VER})\n\n*{len(fc)} columns across {len(SCAN)} master datasets · {TS}*\n\n")
    for ds in SCAN:
        g = fc[fc.dataset.str.contains(ds)]
        fh.write(f"\n## {ds} ({len(g)} cols)\n\n| Column | Description | Type | Range/μ or sample |\n|---|---|---|---|\n")
        for _,r in g.iterrows():
            rng = f"{r['min']}–{r['max']} (μ {r['mean']})" if r['min']!="" else (f"e.g. {r['sample']}" if r['sample'] else f"{r['n_unique']} unique")
            fh.write(f"| `{r['column']}` | {r['description']} | {r['dtype']} | {rng} |\n")
print(f"FEATURE_CATALOG: {len(fc)} columns", flush=True)

# ============ C. PLACES + CATEGORY CATALOG ============
p = pd.read_parquet(ROOT/"places/sgp_places_final.parquet")
N = len(p)
CAT_DESC = {
 "cafe_coffee":"Cafés, coffee shops, bubble tea, dessert, juice bars",
 "restaurant":"Full-service & casual restaurants, eateries, caterers",
 "fast_food":"Quick-service / fast-food outlets",
 "hawker":"Hawker stalls & centres, food courts, kopitiams",
 "bakery":"Bakeries, cake & bread shops",
 "bar_nightlife":"Bars, pubs, lounges, nightclubs",
 "convenience":"Convenience & provision stores (7-Eleven, Cheers, mama shops)",
 "supermarket":"Supermarkets, grocery, wet markets, specialty food",
 "shopping_retail":"Apparel, electronics, furniture, books, malls & general retail",
 "health_medical":"Clinics, hospitals, dental, TCM, pharmacy, physio, vet",
 "beauty_personal":"Hair / nail / beauty salons, spa, massage, tailor",
 "fitness_recreation":"Gyms & sports facilities",
 "education":"Schools, tuition, preschools, universities, studios",
 "services":"Professional & personal services (legal, repair, courier, agencies)",
 "business_office":"Corporate offices, coworking, trading, media, IT",
 "hotel_hospitality":"Hotels, resorts, hostels",
 "entertainment_culture":"Museums, galleries, cinemas, attractions, event venues",
 "transportation":"Bus/MRT stops, taxi stands, parking, petrol, airport",
 "government_public":"Govt offices, post, police, fire, library, community clubs",
 "religious_worship":"Churches, temples, mosques, cemeteries",
 "industrial_mfg":"Manufacturers, wholesale, logistics, construction, car dealers",
 "residential":"HDB, condos, apartments",
 "park_open":"Parks, playgrounds, gardens, nature",
 "financial_services":"ATMs, banks, financial services, insurance, money transfer (NEW v5.6)",
 "automated_kiosk":"Unmanned automated points: vending, self-service kiosks, parcel lockers (NEW v5.6)",
 "other_uncategorized":"Unclassified residue (genuinely ambiguous names)",
}
cat_rows = []
for c, n in p["plexis_category"].value_counts().items():
    sub = p[p["plexis_category"]==c]
    top = sub["brand_norm"].dropna().value_counts().head(4).index.tolist()
    cat_rows.append({"category": c, "count": int(n), "pct": round(100*n/N,1),
                     "description": CAT_DESC.get(c,""),
                     "is_storefront_pct": round(100*sub["is_storefront"].mean(),1) if "is_storefront" in sub else None,
                     "branded_pct": round(100*sub["brand_norm"].notna().mean(),1),
                     "top_brands": top})
pcat = {"atlas":"Plexis SGP","version":VER,"generated_at":TS,
        "n_places": N, "n_categories": p["plexis_category"].nunique(),
        "canonical_places": int((~p["is_duplicate"]).sum()) if "is_duplicate" in p else N,
        "brand_coverage_pct": round(100*p["brand_norm"].notna().mean(),1),
        "duplicates_flagged": int(p["is_duplicate"].sum()) if "is_duplicate" in p else 0,
        "flags": {
          "is_storefront":"manned commercial premise (count supply with is_storefront & not is_duplicate)",
          "host_venue":"venue a co-located tenant sits inside",
          "operator/parent_brand":"food-court / coffeeshop operator",
          "is_duplicate / canonical_id":"de-duplication (filter is_duplicate==False)",
          "zero_reviews":"reviews_count == 0",
        },
        "categories": cat_rows}
json.dump(pcat, open(CAT/"PLACES_CATEGORY_CATALOG.json","w"), indent=1)
with open(CAT/"PLACES_CATEGORY_CATALOG.md","w") as fh:
    fh.write(f"# Plexis SGP — Places & Category Catalog (v{VER})\n\n")
    fh.write(f"*{N:,} places · {p['plexis_category'].nunique()} categories · "
             f"{pcat['canonical_places']:,} canonical · brand coverage {pcat['brand_coverage_pct']}% · {TS}*\n\n")
    fh.write("## Categories\n\n| Category | Count | % | Storefront % | Branded % | Top brands | Description |\n|---|--:|--:|--:|--:|---|---|\n")
    for r in cat_rows:
        fh.write(f"| `{r['category']}` | {r['count']:,} | {r['pct']} | {r['is_storefront_pct']} | "
                 f"{r['branded_pct']} | {', '.join(r['top_brands'])} | {r['description']} |\n")
    fh.write("\n## Place flags\n\n")
    for k,v in pcat["flags"].items(): fh.write(f"- **`{k}`** — {v}\n")
print(f"PLACES_CATEGORY_CATALOG: {len(cat_rows)} categories", flush=True)

print(f"\nWrote to {CAT}/ :")
for f in ["DATA_CATALOG","FEATURE_CATALOG","PLACES_CATEGORY_CATALOG"]:
    for ext in (".json",".md"):
        pth = CAT/f"{f}{ext}"
        if pth.exists(): print(f"  {pth.name}  ({pth.stat().st_size/1024:.0f} KB)")
print(f"  feature_catalog.json / .parquet refreshed ({len(fc)} features)")

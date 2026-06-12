"""One-off schema inspection for scenario_sim data prep. Run on rwm-server."""
import json, os
import pandas as pd

BASE = "/home/azureuser/digital-atlas-sgp"

def hdr(title):
    print(f"\n=== {title} ===")

# -------- subzones --------
with open(f"{BASE}/data/boundaries/subzones.geojson") as f:
    sz = json.load(f)
hdr("subzones.geojson")
print(f"features: {len(sz['features'])}")
print(f"props: {list(sz['features'][0]['properties'].keys())}")
print(f"example: {sz['features'][0]['properties']}")

# -------- population --------
p = pd.read_csv(f"{BASE}/data/demographics/pop_age_sex_tod_2025.csv", nrows=5)
hdr("pop_age_sex_tod_2025.csv")
print(f"cols: {list(p.columns)}")
print(p.head(5).to_string())

# -------- dwellings --------
d = pd.read_csv(f"{BASE}/data/demographics/dwellings_subzone_2025.csv", nrows=5)
hdr("dwellings_subzone_2025.csv")
print(f"cols: {list(d.columns)}")
print(d.head(5).to_string())

# -------- V8 subzone table --------
v8 = pd.read_parquet(f"{BASE}/model/v8_subzone_table.parquet")
hdr("v8_subzone_table.parquet")
print(f"shape: {v8.shape}")
print(f"first 60 cols: {list(v8.columns)[:60]}")

# -------- personas --------
pers = pd.read_parquet(f"{BASE}/data/personas/persona_features_by_subzone.parquet")
hdr("persona_features_by_subzone.parquet")
print(f"shape: {pers.shape}")
print(f"cols: {list(pers.columns)}")
print(pers.head(2).to_string())

# -------- chas clinics --------
with open(f"{BASE}/data/amenities_updated/chas_clinics.geojson") as f:
    c = json.load(f)
hdr(f"chas_clinics.geojson ({len(c['features'])} features)")
print(f"props: {list(c['features'][0]['properties'].keys())}")
print(f"example: {c['features'][0]['properties']}")

# -------- train stations --------
with open(f"{BASE}/data/transit_updated/train_stations_mar2026.geojson") as f:
    t = json.load(f)
hdr(f"train_stations_mar2026.geojson ({len(t['features'])} features)")
print(f"props: {list(t['features'][0]['properties'].keys())}")
print(f"example: {t['features'][0]['properties']}")

# -------- rail lines --------
rl_path = f"{BASE}/data/transit/rail_lines.geojson"
if os.path.exists(rl_path):
    with open(rl_path) as f:
        r = json.load(f)
    hdr(f"rail_lines.geojson ({len(r['features'])} features)")
    print(f"props: {list(r['features'][0]['properties'].keys())}")
    print(f"example: {r['features'][0]['properties']}")

# -------- sample place + grocery brand scan --------
hdr("sgp_places_v2.jsonl — first record keys + grocery brand scan")
first = None
brand_counts = {}
cat_counts = {}
with open(f"{BASE}/data/places_consolidated/sgp_places_v2.jsonl") as f:
    for i, line in enumerate(f):
        rec = json.loads(line)
        if i == 0:
            first = rec
        b = rec.get("brand")
        cat = rec.get("main_category", "") or ""
        sub = rec.get("sub_category", "") or ""
        blob = (cat + " " + sub).lower()
        if b and ("grocer" in blob or "supermarket" in blob or "convenience" in blob):
            brand_counts[b] = brand_counts.get(b, 0) + 1
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

print(f"first record keys: {list(first.keys())}")
print(f"first record: {first}")
print(f"\ntop grocery/supermarket/convenience brands:")
for b, n in sorted(brand_counts.items(), key=lambda x: -x[1])[:25]:
    print(f"  {n:4d}  {b}")
print(f"\ncategories hitting that filter:")
for c, n in sorted(cat_counts.items(), key=lambda x: -x[1])[:15]:
    print(f"  {n:4d}  {c}")

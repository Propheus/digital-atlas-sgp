"""Step 5 — friendliness INDEX components per catchment (route environment quality).

Strictly DISJOINT from the Geographic Detector drivers. All OSM-sourced layers
clipped/counted within each catchment corridor.
  integration   angular harmonic closeness @800 (mean of nodes in catchment)
  choice        angular betweenness @800
  crossing_dens OSM crossings per km of network          (safety)
  signal_dens   OSM traffic signals per km of network     (safety)
  green_pct     OSM park/green area / catchment area       (greenery)
  footpath_dens walk-network length per km2                (provision)
"""
import time
import geopandas as gpd
import pandas as pd
from common import ART, DATA, SVY21

t0 = time.time()
catch = gpd.read_file(ART["catchments"]).to_crs(SVY21)
syn = gpd.read_file(ART["syntax_nodes"]).to_crs(SVY21)

def pick(cols, *musts):
    for c in cols:
        cl = c.lower()
        if all(m in cl for m in musts):
            return c
    return None

clo = pick(syn.columns, "harmonic", "800") or pick(syn.columns, "closeness", "800") or pick(syn.columns, "density", "800")
btw = pick(syn.columns, "betweenness", "800")
print("space-syntax cols -> integration:", clo, "| choice:", btw, flush=True)
syn = syn.rename(columns={clo: "integration", btw: "choice"})[["integration", "choice", "geometry"]]

cross = gpd.read_file(ART["crossings"]).to_crs(SVY21)
sig = gpd.read_file(ART["signals"]).to_crs(SVY21)
parks = gpd.read_file(ART["parks"]).to_crs(SVY21)

rows = []
for _, c in catch.iterrows():
    poly = c.geometry
    net_km = max(c["net_length_m"] / 1000.0, 0.1)
    area_km2 = max(c["catch_area_m2"] / 1e6, 1e-4)
    syn_in = gpd.clip(syn, poly)
    integ = float(syn_in["integration"].mean()) if len(syn_in) else 0.0
    choi = float(syn_in["choice"].mean()) if len(syn_in) else 0.0
    n_cross = int(cross.sindex.query(poly, predicate="intersects").size)
    n_sig = int(sig.sindex.query(poly, predicate="intersects").size)
    park_area = gpd.clip(parks, poly).area.sum()
    rows.append({
        "school_id": int(c["school_id"]), "name": c["name"], "zone": c["zone"],
        "subzone_c": c.get("subzone_c"),
        "integration": integ, "choice": choi,
        "crossing_dens": n_cross / net_km,
        "signal_dens": n_sig / net_km,
        "green_pct": park_area / c["catch_area_m2"],
        "footpath_dens": (c["net_length_m"] / 1000.0) / area_km2,
    })

df = pd.DataFrame(rows)
df.to_csv(DATA / "index_components.csv", index=False)
print(f"saved {len(df)} rows -> index_components.csv ({time.time()-t0:.0f}s)", flush=True)
print(df.drop(columns=["school_id", "name", "zone", "subzone_c"]).describe().round(3).to_string())

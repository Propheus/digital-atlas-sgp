"""Step 5 — friendliness INDEX components per catchment (route environment quality).

DEPENDENT-VARIABLE set only. Kept strictly DISJOINT from the Geographic Detector
drivers (pop density, transport convenience, catchment size, school centrality)
so the q-statistic in step 7 is not circular.

Components (all oriented "higher = friendlier"):
  integration   space syntax: mean angular harmonic closeness @800m (reachability)
  choice        space syntax: mean angular betweenness @800m (through-movement)
  crossing_dens controlled road-crossings per km of network (safety)
  signal_dens   traffic signals per km of network (safety)
  green_pct     park/reserve area as fraction of catchment (greenery/comfort)
  pcn_dens      park-connector length per km2 (greenery/comfort)
  footpath_dens LTA footpath length per km2 (pedestrian provision)
"""
import time
import geopandas as gpd
import pandas as pd
from common import SRC, ART, DATA, SVY21

t0 = time.time()
catch = gpd.read_file(ART["catchments"]).to_crs(SVY21)
syn = gpd.read_file(ART["syntax_nodes"]).to_crs(SVY21)

# auto-discover cityseer angular columns (names vary by version)
def pick(cols, *musts):
    for c in cols:
        cl = c.lower()
        if all(m in cl for m in musts):
            return c
    return None

clo = pick(syn.columns, "harmonic", "800") or pick(syn.columns, "harmonic", "800")
btw = pick(syn.columns, "betweenness", "800")
# simplest-path angular columns may carry no 'harmonic'; fall back to any closeness@800
if clo is None:
    clo = pick(syn.columns, "closeness", "800") or pick(syn.columns, "density", "800")
print("space-syntax cols ->  integration:", clo, "| choice:", btw, flush=True)
syn = syn.rename(columns={clo: "integration", btw: "choice"})[["integration", "choice", "geometry"]]

def load(key):
    return gpd.read_file(SRC[key]).to_crs(SVY21)

print("loading layers...", flush=True)
foot = load("footpath"); cross = load("crossing"); sig = load("signals")
parks = load("parks"); pcn = load("pcn")
print(f"  loaded ({time.time()-t0:.0f}s)", flush=True)

rows = []
for _, c in catch.iterrows():
    poly = c.geometry
    sub = gpd.GeoDataFrame(geometry=[poly], crs=SVY21)
    net_km = max(c["net_length_m"] / 1000.0, 0.1)
    area_km2 = max(c["catch_area_m2"] / 1e6, 1e-4)

    syn_in = gpd.clip(syn, poly)
    integ = float(syn_in["integration"].mean()) if len(syn_in) else 0.0
    choi = float(syn_in["choice"].mean()) if len(syn_in) else 0.0

    n_cross = int(cross.sindex.query(poly, predicate="intersects").size)
    n_sig = int(sig.sindex.query(poly, predicate="intersects").size)
    foot_len = gpd.clip(foot, poly).length.sum()
    pcn_len = gpd.clip(pcn, poly).length.sum()
    park_area = gpd.clip(parks, poly).area.sum()

    rows.append({
        "school_id": int(c["school_id"]), "name": c["name"], "zone": c["zone"],
        "integration": integ,
        "choice": choi,
        "crossing_dens": n_cross / net_km,
        "signal_dens": n_sig / net_km,
        "green_pct": park_area / c["catch_area_m2"],
        "pcn_dens": (pcn_len / 1000.0) / area_km2,
        "footpath_dens": (foot_len / 1000.0) / area_km2,
    })

df = pd.DataFrame(rows)
df.to_csv(DATA / "index_components.csv", index=False)
print(f"saved {len(df)} rows -> index_components.csv  ({time.time()-t0:.0f}s)", flush=True)
print(df.drop(columns=["school_id", "name", "zone"]).describe().round(3).to_string())

"""Step 7 — drivers + Geographic Detector (factor + interaction).

DRIVERS (independent vars, DISJOINT from the friendliness index):
  pop_density     area-weighted residential density over the catchment
  transport_conv  bus-stop density + MRT proximity (z-combined)  -> "transport convenience"
  catch_size      catchment area (km2)                            -> "school-district size"
  school_central  angular closeness @1600 at school's nearest network node -> "school centrality"

Geographic Detector q-statistic (Wang & Xu):
  q = 1 - (sum_h N_h * var_h) / (N * var_total)   in [0,1]; higher = stronger control.
Drivers stratified into 5 quantile classes (reported). Interaction detector overlays
two drivers' strata and compares q(A∩B) to q(A), q(B).
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from itertools import combinations
from common import SRC, ART, OUT, SVY21

N_STRATA = 5
idx = pd.read_csv(ART["index"])
catch = gpd.read_file(ART["catchments"]).to_crs(SVY21)
sch = gpd.read_file(ART["schools"]).to_crs(SVY21)
syn = gpd.read_file(ART["syntax_nodes"]).to_crs(SVY21)

# --- pop density: area-weighted over catchment ---
sz = gpd.read_file(SRC["schools"].parents[2] / "app/public/subzones.geojson").to_crs(SVY21)
sz = sz[["pop_density", "geometry"]]
def wpop(poly):
    inter = gpd.clip(sz, poly)
    if not len(inter):
        return 0.0
    a = inter.area
    return float((inter["pop_density"] * a).sum() / a.sum()) if a.sum() else 0.0

# --- transport convenience: bus density + MRT proximity ---
bus = gpd.read_file(SRC["bus"]).to_crs(SVY21)
mrt = gpd.read_file(SRC["mrt"]).to_crs(SVY21)
mrt_pts = mrt.geometry.centroid

# --- school centrality: angular closeness @1600 at nearest node ---
cen_col = [c for c in syn.columns if "harmonic" in c.lower() and "1600" in c]
cen_col = cen_col[0] if cen_col else [c for c in syn.columns if "closeness" in c.lower() and "1600" in c][0]
syn_c = syn[[cen_col, "geometry"]].rename(columns={cen_col: "central"})
sch_central = gpd.sjoin_nearest(sch[["school_id", "geometry"]], syn_c, how="left")
sch_central = sch_central.groupby("school_id")["central"].mean()

rows = []
for _, c in catch.iterrows():
    poly = c.geometry
    area_km2 = c["catch_area_m2"] / 1e6
    n_bus = int(bus.sindex.query(poly, predicate="intersects").size)
    sp = sch[sch["school_id"] == c["school_id"]].geometry.iloc[0]
    mrt_dist = float(mrt_pts.distance(sp).min())
    rows.append({
        "school_id": int(c["school_id"]),
        "pop_density": wpop(poly),
        "bus_dens": n_bus / max(area_km2, 1e-4),
        "mrt_dist_m": mrt_dist,
        "catch_size": area_km2,
        "school_central": float(sch_central.get(c["school_id"], np.nan)),
    })
drv = pd.DataFrame(rows)
# transport convenience = z(bus density) + z(-mrt distance)
z = lambda s: (s - s.mean()) / s.std(ddof=0)
drv["transport_conv"] = z(drv["bus_dens"]) + z(-drv["mrt_dist_m"])

m = idx.merge(drv, on="school_id")
DRIVERS = ["pop_density", "transport_conv", "catch_size", "school_central"]
LABEL = {"pop_density": "Population density", "transport_conv": "Transport convenience",
         "catch_size": "School-district size", "school_central": "School centrality"}

def stratify(s):
    try:
        return pd.qcut(s.rank(method="first"), N_STRATA, labels=False)
    except ValueError:
        return pd.cut(s, N_STRATA, labels=False)

def q_stat(y, strata):
    y = np.asarray(y, float); tot = y.var() * len(y)
    if tot == 0:
        return 0.0
    within = sum(((strata == h).sum()) * y[strata == h].var() for h in np.unique(strata))
    return 1 - within / tot

y = m["friendliness"].values
strata = {d: stratify(m[d]).values for d in DRIVERS}

# direction of effect: corr sign
single = []
for d in DRIVERS:
    q = q_stat(y, strata[d])
    sign = "+" if np.corrcoef(m[d], y)[0, 1] >= 0 else "-"
    single.append({"driver": LABEL[d], "q": round(q, 4), "effect": sign})
single = pd.DataFrame(single).sort_values("q", ascending=False)

print(f"=== Geographic Detector — single factor (n={len(m)}, {N_STRATA} strata) ===")
print(single.to_string(index=False))

inter = []
for a, b in combinations(DRIVERS, 2):
    qa, qb = q_stat(y, strata[a]), q_stat(y, strata[b])
    comb = strata[a] * N_STRATA + strata[b]
    qab = q_stat(y, comb)
    if qab > qa + qb: kind = "nonlinear-enhance"
    elif qab > max(qa, qb): kind = "bi-enhance"
    elif qab < min(qa, qb): kind = "weaken"
    else: kind = "independent"
    inter.append({"pair": f"{LABEL[a]} ∩ {LABEL[b]}", "q_ab": round(qab, 4),
                  "max_single": round(max(qa, qb), 4), "interaction": kind})
inter = pd.DataFrame(inter).sort_values("q_ab", ascending=False)
print("\n=== Interaction detector ===")
print(inter.to_string(index=False))

single.to_csv(ART["geodetector"], index=False)
inter.to_csv(OUT / "geodetector_interaction.csv", index=False)
m.to_csv(OUT / "schools_index_drivers.csv", index=False)
print(f"\nsaved -> {ART['geodetector'].name}, geodetector_interaction.csv, schools_index_drivers.csv")

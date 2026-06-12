"""Step 7 — drivers + Geographic Detector (factor + interaction).

Drivers (DISJOINT from the index):
  pop_density     area-weighted residential density over catchment (v4 subzone data)
  transport_conv  OSM bus-stop density + MRT proximity (z-combined)
  catch_size      catchment area km2
  school_central  angular closeness @1600 at nearest network node
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

# subzone density from v4: pop_total_all / polygon area
sz = gpd.read_file(SRC["subzones"]).to_crs(SVY21)
sz["subzone_c"] = sz["SUBZONE_C"]
pop = pd.read_parquet(SRC["subzone_pop"])[["subzone_c", "pop_total_all"]]
sz = sz.merge(pop, on="subzone_c", how="left")
sz["dens"] = sz["pop_total_all"].fillna(0) / (sz.geometry.area / 1e6).clip(lower=1e-4)
sz = sz[["dens", "geometry"]]

def wpop(poly):
    inter = gpd.clip(sz, poly)
    if not len(inter):
        return 0.0
    a = inter.area
    return float((inter["dens"] * a).sum() / a.sum()) if a.sum() else 0.0

bus = gpd.read_file(ART["bus"]).to_crs(SVY21)
mrt = gpd.read_file(ART["mrt"]).to_crs(SVY21)
mrt_pts = mrt.geometry

cen = [c for c in syn.columns if "harmonic" in c.lower() and "1600" in c]
cen = cen[0] if cen else [c for c in syn.columns if "closeness" in c.lower() and "1600" in c][0]
syn_c = syn[[cen, "geometry"]].rename(columns={cen: "central"})
sch_central = gpd.sjoin_nearest(sch[["school_id", "geometry"]], syn_c, how="left").groupby("school_id")["central"].mean()

rows = []
for _, c in catch.iterrows():
    poly = c.geometry
    area_km2 = c["catch_area_m2"] / 1e6
    n_bus = int(bus.sindex.query(poly, predicate="intersects").size)
    sp = sch[sch["school_id"] == c["school_id"]].geometry.iloc[0]
    rows.append({"school_id": int(c["school_id"]), "pop_density": wpop(poly),
                 "bus_dens": n_bus / max(area_km2, 1e-4),
                 "mrt_dist_m": float(mrt_pts.distance(sp).min()) if len(mrt_pts) else np.nan,
                 "catch_size": area_km2,
                 "school_central": float(sch_central.get(c["school_id"], np.nan))})
drv = pd.DataFrame(rows)
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
    qab = q_stat(y, strata[a] * N_STRATA + strata[b])
    kind = ("nonlinear-enhance" if qab > qa + qb else "bi-enhance" if qab > max(qa, qb)
            else "weaken" if qab < min(qa, qb) else "independent")
    inter.append({"pair": f"{LABEL[a]} ∩ {LABEL[b]}", "q_ab": round(qab, 4),
                  "max_single": round(max(qa, qb), 4), "interaction": kind})
inter = pd.DataFrame(inter).sort_values("q_ab", ascending=False)
print("\n=== Interaction detector ===")
print(inter.to_string(index=False))

single.to_csv(ART["geodetector"], index=False)
inter.to_csv(OUT / "geodetector_interaction.csv", index=False)
m.to_csv(OUT / "schools_index_drivers.csv", index=False)
print(f"\nsaved -> {ART['geodetector'].name}, geodetector_interaction.csv, schools_index_drivers.csv")

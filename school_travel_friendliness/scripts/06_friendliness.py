"""Step 6 — entropy-weighted friendliness composite (the paper's index).

Entropy weight method (objective weighting, as in the paper):
  1. min-max normalise each indicator (all positively oriented)
  2. p_ij = r_ij / sum_i r_ij
  3. entropy  e_j = -1/ln(n) * sum_i p_ij ln p_ij
  4. divergence d_j = 1 - e_j ; weight w_j = d_j / sum d_j
  5. friendliness = sum_j w_j r_ij  -> scaled 0-100
Classified into Low / Medium / High by tertiles (paper's friendliness levels).
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from common import DATA, ART, OUT, SVY21, WGS84

EPS = 1e-6
df = pd.read_csv(DATA / "index_components.csv")
COMP = ["integration", "choice", "crossing_dens", "signal_dens",
        "green_pct", "pcn_dens", "footpath_dens"]

X = df[COMP].astype(float).values
# min-max normalise (shift to (0,1] to keep entropy defined)
mn, mx = X.min(0), X.max(0)
R = (X - mn) / np.where(mx - mn == 0, 1, mx - mn)
R = R * (1 - EPS) + EPS

n = R.shape[0]
P = R / R.sum(0, keepdims=True)
e = -(P * np.log(P)).sum(0) / np.log(n)
d = 1 - e
w = d / d.sum()

friend = (R * w).sum(1)
df["friendliness"] = 100 * (friend - friend.min()) / (friend.max() - friend.min())
df["level"] = pd.qcut(df["friendliness"], 3, labels=["Low", "Medium", "High"])

weights = pd.Series(w, index=COMP).sort_values(ascending=False)
print("=== entropy weights ===")
print((weights.round(4)).to_string())
print(f"\nlow/med/high split: {df['level'].value_counts().reindex(['Low','Medium','High']).to_dict()}")

print("\n=== TOP 8 friendliest ===")
print(df.sort_values("friendliness", ascending=False).head(8)[["name", "zone", "friendliness"]].to_string(index=False))
print("\n=== BOTTOM 8 ===")
print(df.sort_values("friendliness").head(8)[["name", "zone", "friendliness"]].to_string(index=False))

print("\n=== mean friendliness by region (core-periphery check) ===")
print(df.groupby("zone")["friendliness"].agg(["mean", "count"]).round(1).to_string())

# sanity anchors
for kw in ["TOA PAYOH", "BISHAN", "LIM CHU KANG", "MARSILING", "WOODLANDS"]:
    hit = df[df["name"].str.contains(kw)]
    if len(hit):
        print(f"  anchor {kw:14s}: {hit['friendliness'].mean():.1f}")

df.to_csv(ART["index"], index=False)

# join geometry for the GeoJSON deliverable (school points, WGS84)
sch = gpd.read_file(ART["schools"]).to_crs(WGS84)[["school_id", "geometry"]]
g = sch.merge(df, on="school_id")
gpd.GeoDataFrame(g, crs=WGS84).to_file(ART["index_gj"], driver="GeoJSON")
print(f"\nsaved -> {ART['index'].name}, {ART['index_gj'].name}")

"""Step 6 — entropy-weighted friendliness composite (the paper's index)."""
import numpy as np
import pandas as pd
import geopandas as gpd
from common import DATA, ART, WGS84

EPS = 1e-6
df = pd.read_csv(DATA / "index_components.csv")
COMP = ["integration", "choice", "crossing_dens", "signal_dens", "green_pct", "footpath_dens"]

X = df[COMP].astype(float).values
mn, mx = X.min(0), X.max(0)
R = (X - mn) / np.where(mx - mn == 0, 1, mx - mn)
R = R * (1 - EPS) + EPS
n = R.shape[0]
P = R / R.sum(0, keepdims=True)
e = -(P * np.log(P)).sum(0) / np.log(n)
w = (1 - e) / (1 - e).sum()

friend = (R * w).sum(1)
df["friendliness"] = 100 * (friend - friend.min()) / (friend.max() - friend.min())
df["level"] = pd.qcut(df["friendliness"], 3, labels=["Low", "Medium", "High"])

print("=== entropy weights ===")
print(pd.Series(w, index=COMP).sort_values(ascending=False).round(4).to_string())
print(f"\nlevels: {df['level'].value_counts().reindex(['Low','Medium','High']).to_dict()}")
print("\n=== TOP 8 ===")
print(df.sort_values("friendliness", ascending=False).head(8)[["name", "zone", "friendliness"]].to_string(index=False))
print("\n=== BOTTOM 8 ===")
print(df.sort_values("friendliness").head(8)[["name", "zone", "friendliness"]].to_string(index=False))
print("\n=== mean by region (core-periphery) ===")
print(df.groupby("zone")["friendliness"].agg(["mean", "count"]).round(1).to_string())
for kw in ["TOA PAYOH", "BISHAN", "LIM CHU KANG", "MARSILING", "WOODLANDS", "PUNGGOL"]:
    hit = df[df["name"].str.contains(kw, case=False)]
    if len(hit):
        print(f"  anchor {kw:13s}: {hit['friendliness'].mean():.1f} (n={len(hit)})")

df.to_csv(ART["index"], index=False)
sch = gpd.read_file(ART["schools"]).to_crs(WGS84)[["school_id", "geometry"]]
gpd.GeoDataFrame(sch.merge(df, on="school_id"), crs=WGS84).to_file(ART["index_gj"], driver="GeoJSON")
print(f"\nsaved -> {ART['index'].name}, {ART['index_gj'].name}")

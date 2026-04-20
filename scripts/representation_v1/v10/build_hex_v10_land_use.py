"""
Hex v10 — land use / GPR per hex from URA master plan parcels.

Input:
    data/land_use/master_plan_land_use.geojson  (113,212 parcels)
    data/hex_v10/hex_universe.parquet

Output:
    data/hex_v10/hex_land_use.parquet

For each hex we compute area-weighted shares of each LU bucket, a land-use
entropy (Shannon), and a GPR that is area-weighted across "buildable" parcels
(residential, commercial, business, hotel, institutional). Parcels with non-
numeric GPR ('LND' landed properties → 1.4; 'EVA' / 'NA' → excluded from GPR
calc, not counted in denominator).

Procedure:
    1. Read parcels in 4326, keep only useful columns.
    2. Collapse 30+ LU_DESC classes to 9 buckets: residential, commercial,
       business, mixed_use, institutional, open_space, transport, utility, other.
    3. Clean GPR: numeric pass-through, 'LND' → 1.4, anything else → NaN.
    4. Build hex polygon GeoDataFrame from h3.cell_to_boundary.
    5. Project both to EPSG:3414 (SVY21) for proper area math in metres.
    6. Spatial overlay (intersection) between hexes and parcels.
    7. Per-hex aggregate: area-weighted shares + Shannon entropy + GPR.
"""
from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "land_use" / "master_plan_land_use.geojson"
UNI = ROOT / "data" / "hex_v10" / "hex_universe.parquet"
OUT = ROOT / "data" / "hex_v10" / "hex_land_use.parquet"

# LU_DESC → bucket mapping.
LU_BUCKET = {
    # residential
    "RESIDENTIAL": "residential",
    "RESIDENTIAL WITH COMMERCIAL AT 1ST STOREY": "residential",
    "RESIDENTIAL / INSTITUTION": "residential",
    # commercial
    "COMMERCIAL": "commercial",
    "COMMERCIAL & RESIDENTIAL": "commercial",
    "COMMERCIAL / INSTITUTION": "commercial",
    "HOTEL": "commercial",
    # business (B1/B2/biz park = offices + light industry)
    "BUSINESS 1": "business",
    "BUSINESS 2": "business",
    "BUSINESS PARK": "business",
    "BUSINESS 1 - WHITE": "business",
    "BUSINESS 2 - WHITE": "business",
    "BUSINESS PARK - WHITE": "business",
    # mixed use
    "WHITE": "mixed_use",
    # institutional
    "CIVIC & COMMUNITY INSTITUTION": "institutional",
    "EDUCATIONAL INSTITUTION": "institutional",
    "HEALTH & MEDICAL CARE": "institutional",
    "PLACE OF WORSHIP": "institutional",
    # open space / nature
    "PARK": "open_space",
    "OPEN SPACE": "open_space",
    "SPORTS & RECREATION": "open_space",
    "BEACH AREA": "open_space",
    "AGRICULTURE": "open_space",
    # transport
    "ROAD": "transport",
    "TRANSPORT FACILITIES": "transport",
    "MASS RAPID TRANSIT": "transport",
    "PORT / AIRPORT": "transport",
    # utility / other
    "UTILITY": "utility",
    "WATERBODY": "utility",
    "CEMETERY": "other",
    "RESERVE SITE": "other",
    "SPECIAL USE": "other",
}

BUCKETS = [
    "residential", "commercial", "business", "mixed_use",
    "institutional", "open_space", "transport", "utility", "other",
]

# Classes that contribute to the GPR computation (buildable land).
GPR_BUCKETS = {"residential", "commercial", "business", "mixed_use", "institutional"}

# SVY21 projected CRS — proper for Singapore areas in metres
SVY21 = "EPSG:3414"


def clean_gpr(raw) -> float:
    if raw is None:
        return float("nan")
    s = str(raw).strip()
    if s == "LND":
        return 1.4  # landed typical
    try:
        return float(s)
    except ValueError:
        return float("nan")


def main() -> None:
    print(f"Loading URA parcels: {SRC}")
    g = gpd.read_file(SRC)
    print(f"  {len(g):,} parcels")

    # Attach bucket + cleaned GPR
    g["lu_bucket"] = g["LU_DESC"].map(LU_BUCKET).fillna("other")
    g["gpr_num"] = g["GPR"].map(clean_gpr)

    # Project to SVY21 (metres)
    g = g.to_crs(SVY21)
    # Recompute area in sqm after projection
    g["area_sqm"] = g.geometry.area
    # drop zero-area edge cases
    g = g[g["area_sqm"] > 0].reset_index(drop=True)

    # Build hex polygon GeoDataFrame
    print("Building hex polygons...")
    uni = pd.read_parquet(UNI)
    hex_polys = []
    for hid in uni["hex_id"]:
        # h3.cell_to_boundary returns list[(lat,lng)] in h3 4.x
        boundary = h3.cell_to_boundary(hid)
        # shapely wants (x=lng, y=lat)
        poly = Polygon([(lng, lat) for lat, lng in boundary])
        hex_polys.append(poly)
    hex_gdf = gpd.GeoDataFrame(uni[["hex_id"]].copy(), geometry=hex_polys, crs="EPSG:4326").to_crs(SVY21)
    hex_gdf["hex_area_sqm"] = hex_gdf.geometry.area
    print(f"  built {len(hex_gdf):,} hex polygons (mean area {hex_gdf['hex_area_sqm'].mean():,.0f} sqm)")

    # Spatial overlay — intersection between parcels and hexes
    print("Running spatial overlay (parcels x hexes)...")
    inter = gpd.overlay(
        g[["lu_bucket", "gpr_num", "geometry"]],
        hex_gdf[["hex_id", "geometry"]],
        how="intersection",
        keep_geom_type=True,
    )
    inter["inter_area_sqm"] = inter.geometry.area
    print(f"  intersection rows: {len(inter):,}")

    # Aggregate per (hex_id, bucket): total intersection area
    pivot = inter.pivot_table(
        index="hex_id", columns="lu_bucket", values="inter_area_sqm",
        aggfunc="sum", fill_value=0.0,
    )
    # Ensure all expected buckets are present as columns
    for b in BUCKETS:
        if b not in pivot.columns:
            pivot[b] = 0.0
    pivot = pivot[BUCKETS]

    # Per-hex total measured land area (may be < hex_area_sqm if the hex overlaps sea)
    pivot["lu_total_sqm"] = pivot[BUCKETS].sum(axis=1)

    # Shares and entropy
    with np.errstate(invalid="ignore", divide="ignore"):
        for b in BUCKETS:
            pivot[f"lu_{b}_pct"] = np.where(
                pivot["lu_total_sqm"] > 0,
                pivot[b] / pivot["lu_total_sqm"],
                0.0,
            )
    # Shannon entropy across the 9 buckets (nats)
    def _entropy(row: pd.Series) -> float:
        p = row[[f"lu_{b}_pct" for b in BUCKETS]].to_numpy()
        p = p[p > 0]
        if p.size == 0:
            return 0.0
        return float(-(p * np.log(p)).sum())
    pivot["lu_entropy"] = pivot.apply(_entropy, axis=1)

    # GPR: area-weighted average over parcels with numeric GPR in GPR_BUCKETS
    gpr_rows = inter[inter["lu_bucket"].isin(GPR_BUCKETS) & inter["gpr_num"].notna()].copy()
    gpr_rows["weighted_gpr"] = gpr_rows["gpr_num"] * gpr_rows["inter_area_sqm"]
    gpr_agg = gpr_rows.groupby("hex_id").agg(
        weighted_gpr_sum=("weighted_gpr", "sum"),
        gpr_area_sum=("inter_area_sqm", "sum"),
    )
    gpr_agg["avg_gpr"] = gpr_agg["weighted_gpr_sum"] / gpr_agg["gpr_area_sum"]
    pivot = pivot.join(gpr_agg[["avg_gpr"]], how="left")

    # Final frame
    out = pivot.reset_index()
    # left-join to full universe so every hex has a row
    out = uni[["hex_id"]].merge(out, on="hex_id", how="left")
    # fill shares with 0 where we have no land-use data; avg_gpr stays NaN
    for c in [f"lu_{b}_pct" for b in BUCKETS] + BUCKETS + ["lu_total_sqm", "lu_entropy"]:
        out[c] = out[c].fillna(0.0)

    # Keep only final feature columns — drop raw bucket sums (we have pcts)
    keep = (
        ["hex_id"]
        + [f"lu_{b}_pct" for b in BUCKETS]
        + ["lu_total_sqm", "lu_entropy", "avg_gpr"]
    )
    out = out[keep]

    print(f"Output shape: {out.shape}")
    print(f"Hexes with any land-use measured: {(out['lu_total_sqm']>0).sum():,}")
    print(f"Hexes with avg_gpr defined: {out['avg_gpr'].notna().sum():,}")

    # Within-subzone std check — should be >0
    check = uni[["hex_id", "parent_subzone"]].merge(out[["hex_id", "avg_gpr", "lu_residential_pct"]], on="hex_id")
    s_gpr = check.groupby("parent_subzone")["avg_gpr"].std().dropna()
    s_res = check.groupby("parent_subzone")["lu_residential_pct"].std().dropna()
    print(f"Within-subzone std of avg_gpr: median={s_gpr.median():.4f}  max={s_gpr.max():.4f}")
    print(f"Within-subzone std of lu_residential_pct: median={s_res.median():.4f}  max={s_res.max():.4f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

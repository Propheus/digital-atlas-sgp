"""
Plexis SGP v4 — Stage 4: land use features per hex-9.

Inputs:
  data/land_use/master_plan_land_use.geojson  (113,212 parcels, 33 LU types)
  hex/hex9_universe.parquet                   (7,318 hexes)

Method:
  1. Map URA's 33 LU_DESC values into 12 Plexis buckets:
       residential / commercial / mixed_use / business / business_park / hotel /
       institutional / educational / health / open_space / transport / utility / water / other
  2. For each hex, intersect with land-use parcels in EPSG:3414 (meters).
  3. Compute per-hex:
       lu_<bucket>_pct  — area share, sums to 1 (over land in the hex)
       lu_entropy       — Shannon entropy over non-zero buckets (nats)
       dominant_use     — bucket with max share
       avg_gpr          — area-weighted Gross Plot Ratio (numeric GPRs only)
       max_gpr          — max numeric GPR in hex
       lu_parcel_count  — number of distinct parcels intersecting the hex

Outputs:
  hex/hex9_land_use.parquet
  hex/land_use_report.json
"""
import json, time, os
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists():
            return c
    raise FileNotFoundError("No data root found")


DATA = _resolve_data_root()
LU_GEO = DATA / "land_use/master_plan_land_use.geojson"
HEX9 = ROOT / "hex/hex9_universe.parquet"
OUT_PQ = ROOT / "hex/hex9_land_use.parquet"
REPORT = ROOT / "hex/land_use_report.json"

# 33 URA LU_DESC -> 14 Plexis buckets
LU_MAP = {
    "RESIDENTIAL": "residential",
    "RESIDENTIAL WITH COMMERCIAL AT 1ST STOREY": "mixed_use",
    "RESIDENTIAL / INSTITUTION": "mixed_use",
    "COMMERCIAL & RESIDENTIAL": "mixed_use",
    "COMMERCIAL": "commercial",
    "COMMERCIAL / INSTITUTION": "commercial",
    "HOTEL": "hotel",
    "BUSINESS 1": "business",
    "BUSINESS 2": "business",
    "BUSINESS 1 - WHITE": "business",
    "BUSINESS 2 - WHITE": "business",
    "WHITE": "business",
    "BUSINESS PARK": "business_park",
    "BUSINESS PARK - WHITE": "business_park",
    "EDUCATIONAL INSTITUTION": "educational",
    "HEALTH & MEDICAL CARE": "health",
    "PLACE OF WORSHIP": "institutional",
    "CIVIC & COMMUNITY INSTITUTION": "institutional",
    "SPECIAL USE": "institutional",
    "PARK": "open_space",
    "OPEN SPACE": "open_space",
    "BEACH AREA": "open_space",
    "SPORTS & RECREATION": "open_space",
    "CEMETERY": "open_space",
    "AGRICULTURE": "open_space",
    "ROAD": "transport",
    "MASS RAPID TRANSIT": "transport",
    "LIGHT RAPID TRANSIT": "transport",
    "TRANSPORT FACILITIES": "transport",
    "PORT / AIRPORT": "transport",
    "UTILITY": "utility",
    "WATERBODY": "water",
    "RESERVE SITE": "reserve",
}

BUCKETS = [
    "residential", "mixed_use", "commercial", "hotel",
    "business", "business_park", "educational", "health",
    "institutional", "open_space", "transport", "utility",
    "water", "reserve",
]


def parse_gpr(g):
    """URA GPR field is mixed (numeric like '1.4' or codes like 'EVA','LND','NA','SDP'). Return float or NaN."""
    if g is None:
        return np.nan
    s = str(g).strip()
    try:
        return float(s)
    except Exception:
        return np.nan


def main():
    t0 = time.time()
    print(f"Loading inputs (this may take ~60s for 113K parcels)...")
    lu = gpd.read_file(LU_GEO).to_crs(4326)
    print(f"  parcels: {len(lu):,}  cols: {list(lu.columns)[:8]}")
    h9 = pd.read_parquet(HEX9)
    print(f"  hex-9 rows: {len(h9):,}")

    # Map LU buckets + parse GPR
    lu["lu_bucket"] = lu["LU_DESC"].map(LU_MAP).fillna("other")
    lu["gpr_num"] = lu["GPR"].apply(parse_gpr)
    print(f"  LU bucket distribution:")
    for b, c in lu["lu_bucket"].value_counts().items():
        print(f"    {b:18s}  {c:>7,}")
    print(f"  Numeric GPR rows: {lu['gpr_num'].notna().sum():,} / {len(lu):,}")

    # Project to metric
    print(f"\n  Projecting to EPSG:3414...")
    lu_3414 = lu.to_crs(3414)
    lu_3414["parcel_area_m2"] = lu_3414.geometry.area

    # Build hex-9 polygons in 3414
    print(f"  Building hex-9 polygons (3414)...")
    hex_polys_4326 = []
    for hid in h9["hex9_id"]:
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hid)]
        hex_polys_4326.append(Polygon(ring))
    h9_gdf = gpd.GeoDataFrame({"hex9_id": h9["hex9_id"]}, geometry=hex_polys_4326, crs=4326).to_crs(3414)

    # Spatial overlay (hex × parcel) — use sjoin for candidate pairs, then compute precise intersections
    print(f"  Spatial join (sjoin)...")
    cand = gpd.sjoin(h9_gdf, lu_3414, how="inner", predicate="intersects")
    print(f"    candidate hex×parcel pairs: {len(cand):,}")

    # Compute precise intersection area per pair
    print(f"  Computing precise intersection areas...")
    # Merge geometries back to compute intersection
    lu_indexed = lu_3414[["geometry", "lu_bucket", "gpr_num", "parcel_area_m2"]].reset_index(drop=False).rename(columns={"index": "parcel_idx"})
    cand2 = cand.reset_index().rename(columns={"index": "h_idx"})
    # Build parcel geom lookup
    parcel_geom = dict(zip(lu_indexed["parcel_idx"], lu_indexed["geometry"]))
    hex_geom_by_idx = dict(zip(h9_gdf.index, h9_gdf.geometry))
    rows = []
    for _, r in cand2.iterrows():
        hg = hex_geom_by_idx.get(r["h_idx"])
        pg = parcel_geom.get(r["index_right"])
        if hg is None or pg is None:
            continue
        try:
            inter = hg.intersection(pg).area
        except Exception:
            inter = 0
        if inter > 0:
            rows.append({
                "hex9_id": r["hex9_id"],
                "lu_bucket": r["lu_bucket"],
                "gpr_num": r["gpr_num"],
                "inter_m2": inter,
            })
        if len(rows) % 50000 == 0 and len(rows) > 0:
            print(f"    ...{len(rows):,} rows")
    df = pd.DataFrame(rows)
    print(f"  intersection rows (>0 area): {len(df):,}")

    # Per-hex aggregation
    print(f"\n  Aggregating per hex...")
    bucket_areas = df.pivot_table(
        index="hex9_id", columns="lu_bucket", values="inter_m2", aggfunc="sum", fill_value=0
    ).reset_index()
    # Ensure all bucket cols exist
    for b in BUCKETS + ["other"]:
        if b not in bucket_areas.columns:
            bucket_areas[b] = 0
    cols_order = ["hex9_id"] + BUCKETS + ["other"]
    bucket_areas = bucket_areas[cols_order]
    # Total land area in hex (sum of all parcel intersections)
    bucket_areas["lu_total_m2"] = bucket_areas[BUCKETS + ["other"]].sum(axis=1)

    # Convert to shares (handle empty hexes)
    for b in BUCKETS + ["other"]:
        bucket_areas[f"lu_{b}_pct"] = np.where(
            bucket_areas["lu_total_m2"] > 0,
            bucket_areas[b] / bucket_areas["lu_total_m2"],
            0,
        )

    # Entropy + dominant_use
    share_cols = [f"lu_{b}_pct" for b in BUCKETS + ["other"]]
    shares = bucket_areas[share_cols].values
    # entropy: -sum(p*log(p)) only over non-zero p
    eps = 1e-12
    shares_safe = np.clip(shares, eps, 1.0)
    entropy = -np.sum(shares * np.log(shares_safe), axis=1)
    bucket_areas["lu_entropy"] = entropy
    # dominant_use
    dominant_idx = np.argmax(shares, axis=1)
    bucket_names = [b for b in BUCKETS + ["other"]]
    bucket_areas["dominant_use"] = [bucket_names[i] if shares[r, i] > 0 else None
                                      for r, i in enumerate(dominant_idx)]

    # GPR aggregates
    print(f"  Computing GPR aggregates...")
    df_gpr = df.dropna(subset=["gpr_num"])
    gpr_agg = df_gpr.groupby("hex9_id").apply(
        lambda g: pd.Series({
            "avg_gpr": np.average(g["gpr_num"], weights=g["inter_m2"]) if len(g) else np.nan,
            "max_gpr": g["gpr_num"].max() if len(g) else np.nan,
        })
    ).reset_index()
    bucket_areas = bucket_areas.merge(gpr_agg, on="hex9_id", how="left")

    # Parcel count per hex
    parcel_counts = df.groupby("hex9_id").size().reset_index(name="lu_parcel_count")
    bucket_areas = bucket_areas.merge(parcel_counts, on="hex9_id", how="left")
    bucket_areas["lu_parcel_count"] = bucket_areas["lu_parcel_count"].fillna(0).astype(int)

    # Join to all hexes
    out = h9[["hex9_id"]].merge(bucket_areas, on="hex9_id", how="left")
    # Empty hexes: 0 area, 0 entropy, null dominant_use, 0 parcels
    for c in BUCKETS + ["other"]:
        out[c] = out[c].fillna(0)
        out[f"lu_{c}_pct"] = out[f"lu_{c}_pct"].fillna(0)
    out["lu_total_m2"] = out["lu_total_m2"].fillna(0)
    out["lu_entropy"] = out["lu_entropy"].fillna(0)
    out["lu_parcel_count"] = out["lu_parcel_count"].fillna(0).astype(int)
    # avg_gpr / max_gpr stay NaN where unknown

    # Drop the raw m² columns to keep table lean (keep only shares + diagnostics)
    out = out.drop(columns=BUCKETS + ["other"])

    out.to_parquet(OUT_PQ, index=False)

    # Summary stats
    total_parcel_area = lu_3414["parcel_area_m2"].sum() / 1e6
    total_hex_lu_area = out["lu_total_m2"].sum() / 1e6
    print(f"\n=== Summary ===")
    print(f"  Total URA parcel area: {total_parcel_area:.2f} km²")
    print(f"  Total hex-LU intersected area: {total_hex_lu_area:.2f} km²")
    print(f"  Hexes with land use data: {(out['lu_total_m2'] > 0).sum():,} / {len(out):,}")
    print(f"\n=== Dominant use distribution ===")
    for u, c in out["dominant_use"].value_counts(dropna=False).items():
        print(f"  {str(u):20s}  {c:>5,} hexes  ({100*c/len(out):.1f}%)")

    # Top dense hexes per bucket sanity check
    print(f"\n=== Top-3 hexes by share ===")
    for b in ["commercial", "residential", "business_park", "hotel"]:
        top = out.nlargest(3, f"lu_{b}_pct").merge(h9[["hex9_id", "parent_subzone_name", "parent_pa"]], on="hex9_id")
        print(f"  {b}:")
        for _, r in top.iterrows():
            print(f"    {r[f'lu_{b}_pct']*100:5.1f}%  {r['hex9_id']}  {str(r['parent_subzone_name']):25s} ({r['parent_pa']})")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "parcels_input": len(lu),
        "hex_count": len(out),
        "hexes_with_lu_data": int((out["lu_total_m2"] > 0).sum()),
        "buckets": BUCKETS + ["other"],
        "ura_parcel_area_km2": round(total_parcel_area, 2),
        "hex_lu_intersected_area_km2": round(total_hex_lu_area, 2),
        "dominant_use_distribution": {str(k): int(v) for k, v in out["dominant_use"].value_counts(dropna=False).items()},
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")
    print(f"Output: {OUT_PQ}")


if __name__ == "__main__":
    main()

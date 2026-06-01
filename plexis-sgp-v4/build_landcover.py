"""
Plexis SGP v4 — Stage 20: ESA WorldCover landcover per hex.

Recovers the v3 `wc_*` family using zonal stats on
data/satellite/sgp_clips/sgp_worldcover_2021.tif.

WorldCover classes (10m raster):
  10 Tree cover, 20 Shrubland, 30 Grassland, 40 Cropland, 50 Built-up,
  60 Bare, 70 Snow, 80 Water, 90 Wetland, 95 Mangroves, 100 Moss/Lichen.

Per-hex features:
  wc_built_share, wc_tree_share, wc_water_share, wc_grass_share, wc_other_share
  wc_dominant_class (int)

Outputs:
  hex/hex9_landcover.parquet
  hex/hex8_landcover.parquet
  hex/subzone_landcover.parquet
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import h3
import rasterio
from rasterstats import zonal_stats

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
WC_TIF = DATA / "satellite/sgp_clips/sgp_worldcover_2021.tif"

# Buckets
BUCKETS = {
    "wc_tree_share":  [10, 95],
    "wc_built_share": [50],
    "wc_water_share": [80, 90],
    "wc_grass_share": [20, 30],
}


def hex_polys_4326(hex_ids):
    out = []
    for hid in hex_ids:
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hid)]
        out.append(Polygon(ring))
    return out


def main():
    t0 = time.time()
    print(f"Loading hex universe...")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    print(f"  {len(h9)} hex9")

    print(f"Building polygons + computing zonal stats from {WC_TIF.name}...")
    polys = hex_polys_4326(h9["hex9_id"].tolist())
    # zonal_stats with categorical=True returns dict of class → pixel count
    stats = zonal_stats(polys, str(WC_TIF), categorical=True, all_touched=False)
    print(f"  zonal stats done")

    rows = []
    for hid, s in zip(h9["hex9_id"], stats):
        s = s or {}
        total = sum(s.values()) or 1
        row = {"hex9_id": hid}
        for col, classes in BUCKETS.items():
            row[col] = sum(s.get(c, 0) for c in classes) / total
        # other = whatever's left
        accounted = sum(row[col] for col in BUCKETS)
        row["wc_other_share"] = max(0, 1 - accounted)
        # dominant class (mode)
        row["wc_dominant_class"] = int(max(s, key=s.get)) if s else 0
        rows.append(row)
    out_h9 = pd.DataFrame(rows)
    for c in out_h9.columns:
        if c.endswith("_share"): out_h9[c] = out_h9[c].round(3)

    out_h9 = h9[["hex9_id"]].merge(out_h9, on="hex9_id", how="left")
    out_h9.to_parquet(ROOT / "hex/hex9_landcover.parquet", index=False)
    print(f"  hex9_landcover: {out_h9.shape}")
    print(f"  built_share median {out_h9['wc_built_share'].median():.3f}")
    print(f"  tree_share median {out_h9['wc_tree_share'].median():.3f}")
    print(f"  water_share median {out_h9['wc_water_share'].median():.3f}")

    # === Aggregate to hex8 (mean of constituent hex9 shares) ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h9wp = out_h9.merge(h9[["hex9_id","parent_hex8"]], on="hex9_id")
    share_cols = [c for c in out_h9.columns if c.endswith("_share")]
    h8_agg = h9wp.groupby("parent_hex8")[share_cols].mean().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    out_h8 = h8_uni.merge(h8_agg, on="hex8_id", how="left")
    # dominant class via mode
    h8_dom = h9wp.groupby("parent_hex8")["wc_dominant_class"].agg(lambda x: x.mode().iloc[0]).reset_index().rename(columns={"parent_hex8":"hex8_id"})
    out_h8 = out_h8.merge(h8_dom, on="hex8_id", how="left")
    for c in share_cols: out_h8[c] = out_h8[c].fillna(0).round(3)
    out_h8["wc_dominant_class"] = out_h8["wc_dominant_class"].fillna(0).astype(int)
    out_h8.to_parquet(ROOT / "hex/hex8_landcover.parquet", index=False)
    print(f"  hex8_landcover: {out_h8.shape}")

    # === SUBZONE ===
    print("\n--- SUBZONE ---")
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    h9wsz = out_h9.merge(h9[["hex9_id","parent_subzone"]], on="hex9_id")
    sz_agg = h9wsz.groupby("parent_subzone")[share_cols].mean().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    out_sz = sz_lu.merge(sz_agg, on="subzone_c", how="left")
    sz_dom = h9wsz.groupby("parent_subzone")["wc_dominant_class"].agg(lambda x: x.mode().iloc[0]).reset_index().rename(columns={"parent_subzone":"subzone_c"})
    out_sz = out_sz.merge(sz_dom, on="subzone_c", how="left")
    for c in share_cols: out_sz[c] = out_sz[c].fillna(0).round(3)
    out_sz["wc_dominant_class"] = out_sz["wc_dominant_class"].fillna(0).astype(int)
    out_sz.to_parquet(ROOT / "hex/subzone_landcover.parquet", index=False)
    print(f"  subzone_landcover: {out_sz.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {"hex9": list(out_h9.shape), "hex8": list(out_h8.shape), "subzone": list(out_sz.shape)},
    }
    with open(ROOT / "hex/landcover_report.json", "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()

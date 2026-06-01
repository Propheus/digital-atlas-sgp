"""
Plexis SGP v4 — Stage 5b: satellite features per hex.

Inputs (atlas-1):
  data/satellite/ghsl/ghsl_built_2010_sgp.tif    GHSL built-up surface 2010
  data/satellite/ghsl/ghsl_built_2020_sgp.tif    GHSL built-up surface 2020
  data/satellite/ghsl/ghsl_built_2025_sgp.tif    GHSL built-up surface 2025
  data/satellite/ghsl/ghsl_height_sgp.tif        GHSL building height 2018 (meters)
  data/satellite/worldpop_pop_2020.tif           WorldPop 2020 pop count per ~93m pixel
  data/satellite/worldpop_pop_2025.tif           WorldPop 2025 pop count
  data/satellite/night_light_temporal.json       VIIRS night lights pre-aggregated by subzone (2022, 2024)

Method:
  - GHSL + WorldPop: rasterstats zonal stats (mean for built/height, sum for pop)
  - VIIRS: broadcast subzone-level stats (no raster available)
  - Compute derived metrics: change %, growth flags, commercial indicator

Outputs:
  hex/hex9_satellite.parquet     (~13 cols)
  hex/hex8_satellite.parquet
  hex/subzone_satellite.parquet
"""
import json, os, time
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
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
    raise FileNotFoundError

DATA = _resolve_data_root()
GHSL_2010 = DATA / "satellite/ghsl/ghsl_built_2010_sgp.tif"
GHSL_2020 = DATA / "satellite/ghsl/ghsl_built_2020_sgp.tif"
GHSL_2025 = DATA / "satellite/ghsl/ghsl_built_2025_sgp.tif"
GHSL_HEIGHT = DATA / "satellite/ghsl/ghsl_height_sgp.tif"
WP_2020 = DATA / "satellite/worldpop_pop_2020.tif"
WP_2025 = DATA / "satellite/worldpop_pop_2025.tif"
NL_JSON = DATA / "satellite/night_light_temporal.json"


def hex_polys_4326(hex_ids):
    out = []
    for hid in hex_ids:
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hid)]
        out.append(Polygon(ring))
    return out


def zstats(raster_path, polys, stats="mean", nodata_override=None):
    """Run zonal stats. Returns list of dicts. Treat negative WorldPop nodata properly."""
    with rasterio.open(raster_path) as src:
        nodata = nodata_override if nodata_override is not None else src.nodata
    return zonal_stats(polys, str(raster_path), stats=stats, nodata=nodata, all_touched=True)


def main():
    t0 = time.time()
    print("Loading hex universe...")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    polys9 = hex_polys_4326(h9["hex9_id"].tolist())
    print(f"  hex-9 cells: {len(polys9):,}")

    out = h9[["hex9_id", "parent_hex8", "parent_subzone"]].copy()

    # === GHSL skipped: source tiles cover SE Asia north of SGP (R7_C29 doesn't include SGP land) ===
    # V3 atlas had the same issue. We rely on our own buildings layer for built-area + height.
    print("\n  Skipping GHSL (source tiles don't cover SGP land — known issue from V3)")

    # === WorldPop (sum per hex; nodata=-99999) ===
    # NOTE: worldpop_pop_2020.tif and 2025.tif are identical bytes — only one snapshot available.
    # We surface a single wp_pop column (not a temporal delta).
    print("  WorldPop zonal stats (single snapshot — 2020/2025 files are identical)...")
    st = zstats(WP_2025, polys9, stats="sum")
    out["wp_pop"] = [s["sum"] if s and s["sum"] is not None else 0 for s in st]
    out["wp_pop"] = out["wp_pop"].clip(lower=0)
    print(f"    wp_pop sum: {out['wp_pop'].sum():,.0f}")

    # === VIIRS night lights (subzone-level broadcast) ===
    print("  VIIRS night lights (broadcasting from subzone JSON)...")
    with open(NL_JSON) as f:
        nl = json.load(f)
    yearly = nl.get("yearly_stats", {})
    nl_2022 = {sz: v["mean"] for sz, v in yearly.get("2022", {}).items()}
    nl_2024 = {sz: v["mean"] for sz, v in yearly.get("2024", {}).items()}
    out["nl_2022"] = out["parent_subzone"].map(nl_2022).fillna(0)
    out["nl_2024"] = out["parent_subzone"].map(nl_2024).fillna(0)
    out["nl_change_pct"] = np.where(
        out["nl_2022"] > 0.1,
        (out["nl_2024"] - out["nl_2022"]) / out["nl_2022"] * 100,
        0,
    )

    # nl_commercial_indicator: high radiance per resident → likely commercial
    # We use pop_resident from population layer if it's loadable
    pop_path = ROOT / "hex/hex9_population.parquet"
    if pop_path.exists():
        pop = pd.read_parquet(pop_path)[["hex9_id", "pop_resident"]]
        out = out.merge(pop, on="hex9_id", how="left")
        out["pop_resident"] = out["pop_resident"].fillna(0)
        out["nl_per_capita"] = np.where(
            out["pop_resident"] > 50,
            out["nl_2024"] / out["pop_resident"],
            0,
        )
        # commercial indicator: nl_radiance × (1 - residential signal). Resident-poor + nl-bright = commercial.
        out["nl_commercial_indicator"] = np.where(
            out["pop_resident"] > 0,
            out["nl_2024"] * (1 / (1 + out["pop_resident"] / 1000)),
            out["nl_2024"],
        )
        out = out.drop(columns=["pop_resident"])
    else:
        out["nl_per_capita"] = 0
        out["nl_commercial_indicator"] = out["nl_2024"]

    # Growth corridor / decline zone flags
    out["nl_growth_corridor"] = out["nl_change_pct"] >= 20
    out["nl_decline_zone"] = out["nl_change_pct"] <= -20

    # === Reorder + persist ===
    keep = [
        "hex9_id", "parent_hex8", "parent_subzone",
        # VIIRS night lights (subzone-broadcast — VIIRS raster TIF was a 404; pre-aggregated subzone JSON only)
        "nl_2022", "nl_2024", "nl_change_pct",
        "nl_growth_corridor", "nl_decline_zone",
        "nl_per_capita", "nl_commercial_indicator",
        # WorldPop (zonal-stat, hex-level)
        "wp_pop",
    ]
    out = out[keep]
    for c in out.columns:
        if c in ("hex9_id", "parent_hex8", "parent_subzone"): continue
        if out[c].dtype == bool: out[c] = out[c].fillna(False)
        elif out[c].dtype.kind in "if": out[c] = out[c].fillna(0)

    out.to_parquet(ROOT / "hex/hex9_satellite.parquet", index=False)
    print(f"\n  hex9_satellite: {out.shape}")

    # === Aggregate to hex-8 ===
    print("\n  Aggregating to hex-8...")
    h8_univ = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    agg_h8 = out.groupby("parent_hex8").agg(
        nl_2022=("nl_2022", "mean"),
        nl_2024=("nl_2024", "mean"),
        nl_change_pct=("nl_change_pct", "mean"),
        nl_growth_corridor=("nl_growth_corridor", "any"),
        nl_decline_zone=("nl_decline_zone", "any"),
        nl_per_capita=("nl_per_capita", "mean"),
        nl_commercial_indicator=("nl_commercial_indicator", "mean"),
        wp_pop=("wp_pop", "sum"),
    ).reset_index().rename(columns={"parent_hex8": "hex8_id"})
    h8 = h8_univ[["hex8_id"]].merge(agg_h8, on="hex8_id", how="left")
    h8.to_parquet(ROOT / "hex/hex8_satellite.parquet", index=False)
    print(f"  hex8_satellite: {h8.shape}")

    # === Aggregate to subzone ===
    print("  Aggregating to subzone...")
    sz = out.groupby("parent_subzone").agg(
        nl_2022=("nl_2022", "first"),
        nl_2024=("nl_2024", "first"),
        nl_change_pct=("nl_change_pct", "first"),
        nl_growth_corridor=("nl_growth_corridor", "any"),
        nl_decline_zone=("nl_decline_zone", "any"),
        nl_per_capita=("nl_per_capita", "mean"),
        nl_commercial_indicator=("nl_commercial_indicator", "mean"),
        wp_pop=("wp_pop", "sum"),
    ).reset_index().rename(columns={"parent_subzone": "subzone_c"})
    sz.to_parquet(ROOT / "hex/subzone_satellite.parquet", index=False)
    print(f"  subzone_satellite: {sz.shape}")

    # Top hexes by nl_2024 (sanity — should be CBD / Orchard)
    h9_lookup = h9[["hex9_id", "parent_subzone_name", "parent_pa"]]
    top = out.drop_duplicates("parent_subzone").nlargest(10, "nl_2024").merge(h9_lookup, on="hex9_id")
    print(f"\n=== Top 10 SUBZONES by nl_2024 (night light brightness) ===")
    for _, r in top.iterrows():
        print(f"  nl={r['nl_2024']:.1f}  Δ%={r['nl_change_pct']:>+6.1f}  comm_ind={r['nl_commercial_indicator']:.2f}  "
              f"{str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    print(f"\n=== Top 10 SUBZONES by nl_change_pct (growth corridors) ===")
    top2 = out.drop_duplicates("parent_subzone").nlargest(10, "nl_change_pct").merge(h9_lookup, on="hex9_id")
    for _, r in top2.iterrows():
        print(f"  Δ%={r['nl_change_pct']:>+6.1f}  nl22→24: {r['nl_2022']:.0f}→{r['nl_2024']:.0f}  "
              f"{str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    print(f"\n=== Top 10 hexes by WorldPop pop count ===")
    top3 = out.nlargest(10, "wp_pop").merge(h9_lookup, on="hex9_id")
    for _, r in top3.iterrows():
        print(f"  pop={r['wp_pop']:>5.0f}  "
              f"{str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "shapes": {"hex9": list(out.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
        "totals": {
            "median_nl_2024": float(out["nl_2024"].median()),
            "max_nl_2024": float(out["nl_2024"].max()),
            "growth_corridor_hexes": int(out["nl_growth_corridor"].sum()),
            "decline_zone_hexes": int(out["nl_decline_zone"].sum()),
            "wp_pop_total": int(out["wp_pop"].sum()),
        },
    }
    with open(ROOT / "hex/satellite_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

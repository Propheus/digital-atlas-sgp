"""
Plexis SGP v4 — Stage 3: population dasymetric allocation to hex-9.

Architecture: do ALL allocation at (hex, subzone) chunk level, then sum to hex.
This guarantees per-subzone totals, HDB/non-HDB totals, AND age sums all match
by construction.

Chunk rule:
  HDB chunk pop       = sz.pop_hdb × (dwelling_units_in_chunk / sz_total_units)
  non-HDB chunk pop   = sz.pop_non_hdb × (chunk_area / sz_buildable_area)
  chunk age pop_X     = (chunk_pop_hdb + chunk_pop_non_hdb) × sz_age_share_X

Where `sz_buildable_area` = hex-subzone-intersection area (proxy for residential potential).

Outputs:
  hex/hex9_population.parquet
  hex/population_report.json
"""
import json, time
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree
import os
import h3

ROOT = Path(__file__).parent


def _resolve_data_root():
    """Source-data root. Env override > atlas-1 path > local repo path."""
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [
        Path("/home/azureuser/digital-atlas-sgp/data"),
        ROOT.parent / "data",
    ]:
        if c.exists():
            return c
    raise FileNotFoundError("No data root found; set PLEXIS_DATA_ROOT")


DATA = _resolve_data_root()
POP_CSV = DATA / "demographics/pop_age_sex_tod_2025.csv"
HDB_GEO = DATA / "housing/hdb_existing_buildings.geojson"
HDB_INFO = DATA / "housing/hdb_property_info.csv"
SUBZONES = ROOT / "boundaries/subzones.geojson"
HEX9 = ROOT / "hex/hex9_universe.parquet"
OVERLAP_PQ = ROOT / "hex/hex9_subzone_overlap.parquet"

OUT_PQ = ROOT / "hex/hex9_population.parquet"
REPORT = ROOT / "hex/population_report.json"

HDB_TOD = {
    "HDB 1- and 2-Room Flats", "HDB 3-Room Flats", "HDB 4-Room Flats",
    "HDB 5-Room and Executive Flats", "HUDC Flats (excluding those privatised)",
}


def normalize_name(s):
    if s is None: return None
    return " ".join(str(s).upper().replace("-", " ").split())


def ag_to_bucket(ag):
    if ag == "85_and_over":
        return "65plus"
    try:
        lo = int(str(ag).split("_")[0])
    except Exception:
        return "unk"
    if lo < 15: return "0_14"
    if lo < 65: return "15_64"
    return "65plus"


def main():
    t0 = time.time()
    print("Loading...")
    pop = pd.read_csv(POP_CSV)
    hdb_geo = gpd.read_file(HDB_GEO).to_crs(4326)
    hdb_info = pd.read_csv(HDB_INFO)
    sz_gdf = gpd.read_file(SUBZONES).to_crs(4326)
    h9 = pd.read_parquet(HEX9)
    overlap = pd.read_parquet(OVERLAP_PQ)
    print(f"  pop rows: {len(pop):,}  hdb_blocks: {len(hdb_geo):,}  hex-9: {len(h9):,}  overlap rows: {len(overlap):,}")

    # --- Subzone pop totals ---
    pop = pop[pop["Time"] == 2025].copy()
    pop["is_hdb"] = pop["TOD"].isin(HDB_TOD)
    pop["SZ_norm"] = pop["SZ"].apply(normalize_name)
    pop["age_bucket"] = pop["AG"].apply(ag_to_bucket)

    sz_pop = pop.groupby("SZ_norm").agg(
        pop_total=("Pop", "sum"),
        pop_hdb=("Pop", lambda s: s[pop.loc[s.index, "is_hdb"]].sum()),
    ).reset_index()
    sz_pop["pop_non_hdb"] = sz_pop["pop_total"] - sz_pop["pop_hdb"]

    sz_age = pop.pivot_table(index="SZ_norm", columns="age_bucket", values="Pop", aggfunc="sum", fill_value=0).reset_index()
    for c in ["0_14", "15_64", "65plus"]:
        if c not in sz_age.columns:
            sz_age[c] = 0
    sz_pop = sz_pop.merge(sz_age[["SZ_norm", "0_14", "15_64", "65plus"]], on="SZ_norm", how="left")
    sz_pop["age_share_014"] = np.where(sz_pop["pop_total"] > 0, sz_pop["0_14"] / sz_pop["pop_total"], 0)
    sz_pop["age_share_1564"] = np.where(sz_pop["pop_total"] > 0, sz_pop["15_64"] / sz_pop["pop_total"], 0)
    sz_pop["age_share_65plus"] = np.where(sz_pop["pop_total"] > 0, sz_pop["65plus"] / sz_pop["pop_total"], 0)
    print(f"  SGP pop total: {sz_pop['pop_total'].sum():,}  HDB: {sz_pop['pop_hdb'].sum():,}  non-HDB: {sz_pop['pop_non_hdb'].sum():,}")

    # --- HDB blocks → (subzone, hex) with dwelling units ---
    sz_3414 = sz_gdf.to_crs(3414)
    hdb_3414 = hdb_geo.to_crs(3414)
    hdb_3414["centroid"] = hdb_3414.geometry.centroid
    tree = STRtree(sz_3414.geometry.values)
    sz_names_arr = list(sz_3414["SUBZONE_N"])

    def subzone_of(pt):
        for i in tree.query(pt):
            if sz_3414.geometry.iloc[i].contains(pt):
                return sz_names_arr[i]
        dists = sz_3414.geometry.distance(pt)
        return sz_names_arr[dists.idxmin()]

    print("  Linking HDB blocks to subzones...")
    hdb_3414["subzone_name"] = hdb_3414["centroid"].apply(subzone_of)
    hdb_3414["SZ_norm"] = hdb_3414["subzone_name"].apply(normalize_name)
    # hex-9 via centroid lat/lng
    cent_4326 = hdb_geo.geometry.centroid
    hdb_3414["hex9_id"] = [h3.latlng_to_cell(c.y, c.x, 9) for c in cent_4326]

    hdb_info["blk_no_n"] = hdb_info["blk_no"].astype(str).str.upper().str.strip()
    hdb_3414["BLK_NO_N"] = hdb_3414["BLK_NO"].astype(str).str.upper().str.strip()
    info_units = hdb_info.groupby("blk_no_n")["total_dwelling_units"].sum().to_dict()
    geo_counts = hdb_3414["BLK_NO_N"].value_counts().to_dict()
    def units_for(blk):
        total = info_units.get(blk, 0)
        n = geo_counts.get(blk, 1)
        return total / n if n else 0
    hdb_3414["dwelling_units"] = hdb_3414["BLK_NO_N"].apply(units_for)
    print(f"  Total dwelling units matched: {hdb_3414['dwelling_units'].sum():,.0f}")

    # HDB chunks: (subzone_name, hex9_id) -> dwelling_units
    hdb_chunks = hdb_3414.groupby(["SZ_norm", "hex9_id"]).agg(
        units=("dwelling_units", "sum"),
    ).reset_index()
    # Subzone HDB total units
    sz_units = hdb_3414.groupby("SZ_norm")["dwelling_units"].sum().to_dict()

    # --- Non-HDB chunks: hex × subzone intersection area ---
    print("  Computing hex-subzone intersection areas (3414)...")
    sz_code_to_name = dict(zip(sz_gdf["SUBZONE_C"], sz_gdf["SUBZONE_N"]))
    overlap["subzone_name"] = overlap["subzone_c"].map(sz_code_to_name)
    overlap["SZ_norm"] = overlap["subzone_name"].apply(normalize_name)

    def hex_poly_3414(hex_id):
        ring = [(lng, lat) for lat, lng in h3.cell_to_boundary(hex_id)]
        return gpd.GeoSeries([Polygon(ring)], crs=4326).to_crs(3414).iloc[0]

    hex_ids = overlap["hex9_id"].unique()
    hex_poly_cache = {h: hex_poly_3414(h) for h in hex_ids}
    sz_poly_cache = dict(zip(sz_3414["SUBZONE_N"], sz_3414.geometry.values))

    def inter_area(row):
        hp_ = hex_poly_cache.get(row["hex9_id"])
        sp = sz_poly_cache.get(row["subzone_name"])
        if hp_ is None or sp is None:
            return 0
        try:
            return hp_.intersection(sp).area
        except Exception:
            return 0
    overlap["inter_m2"] = overlap.apply(inter_area, axis=1)
    # sz total area
    sz_total_area = overlap.groupby("SZ_norm")["inter_m2"].sum().to_dict()

    # --- Merge HDB + non-HDB + age at chunk level, then sum to hex ---
    # Build chunk table: (SZ_norm, hex9_id)
    # Union of HDB chunks (has units) and overlap (has area). Some chunks exist
    # in one but not the other; that's fine — the one without just gets 0 for
    # that component.
    hdb_c = hdb_chunks.rename(columns={"units": "chunk_units"})
    non_c = overlap[["SZ_norm", "hex9_id", "inter_m2"]].rename(columns={"inter_m2": "chunk_area_m2"})
    chunks = non_c.merge(hdb_c, on=["SZ_norm", "hex9_id"], how="outer")
    chunks["chunk_units"] = chunks["chunk_units"].fillna(0)
    chunks["chunk_area_m2"] = chunks["chunk_area_m2"].fillna(0)

    # Attach subzone-level pop and totals
    chunks = chunks.merge(
        sz_pop[["SZ_norm", "pop_hdb", "pop_non_hdb", "age_share_014", "age_share_1564", "age_share_65plus"]],
        on="SZ_norm", how="left",
    )
    chunks["sz_units"] = chunks["SZ_norm"].map(sz_units).fillna(0)
    chunks["sz_area_m2"] = chunks["SZ_norm"].map(sz_total_area).fillna(0)

    # Allocate
    chunks["chunk_pop_hdb"] = np.where(
        chunks["sz_units"] > 0,
        chunks["pop_hdb"].fillna(0) * chunks["chunk_units"] / chunks["sz_units"],
        0,
    )
    chunks["chunk_pop_non_hdb"] = np.where(
        chunks["sz_area_m2"] > 0,
        chunks["pop_non_hdb"].fillna(0) * chunks["chunk_area_m2"] / chunks["sz_area_m2"],
        0,
    )
    chunks["chunk_pop_total"] = chunks["chunk_pop_hdb"] + chunks["chunk_pop_non_hdb"]

    # Age allocated per-chunk using that subzone's age mix
    chunks["chunk_pop_014"] = chunks["chunk_pop_total"] * chunks["age_share_014"].fillna(0)
    chunks["chunk_pop_1564"] = chunks["chunk_pop_total"] * chunks["age_share_1564"].fillna(0)
    chunks["chunk_pop_65plus"] = chunks["chunk_pop_total"] * chunks["age_share_65plus"].fillna(0)

    # Aggregate to hex
    hp = chunks.groupby("hex9_id").agg(
        pop_total=("chunk_pop_total", "sum"),
        pop_hdb=("chunk_pop_hdb", "sum"),
        pop_non_hdb=("chunk_pop_non_hdb", "sum"),
        pop_0_14=("chunk_pop_014", "sum"),
        pop_15_64=("chunk_pop_1564", "sum"),
        pop_65plus=("chunk_pop_65plus", "sum"),
    ).reset_index()
    hp["pop_hdb_share"] = np.where(hp["pop_total"] > 0, hp["pop_hdb"] / hp["pop_total"], 0)

    # Join to universe (fills 0 for any hex with no chunk)
    hp = h9[["hex9_id", "parent_subzone_name", "parent_pa", "parent_region"]].merge(hp, on="hex9_id", how="left")
    for c in ["pop_total", "pop_hdb", "pop_non_hdb", "pop_0_14", "pop_15_64", "pop_65plus", "pop_hdb_share"]:
        hp[c] = hp[c].fillna(0)

    hp.to_parquet(OUT_PQ, index=False)

    # --- Report ---
    total_expected = sz_pop["pop_total"].sum()
    total_alloc = hp["pop_total"].sum()
    age_sum_max_err = (hp["pop_0_14"] + hp["pop_15_64"] + hp["pop_65plus"] - hp["pop_total"]).abs().max()
    print(f"\n=== Allocation summary ===")
    print(f"  Expected total: {total_expected:,}")
    print(f"  Allocated:      {total_alloc:,.0f}")
    print(f"  Drift:          {(total_alloc-total_expected):+.1f} ({100*(total_alloc-total_expected)/total_expected:+.4f}%)")
    print(f"  HDB allocated:  {hp['pop_hdb'].sum():,.0f} / {sz_pop['pop_hdb'].sum():,}")
    print(f"  Non-HDB:        {hp['pop_non_hdb'].sum():,.0f} / {sz_pop['pop_non_hdb'].sum():,}")
    print(f"  Max age-sum discrepancy: {age_sum_max_err:.6f}")

    # Top 10 sanity
    top = hp.nlargest(10, "pop_total")
    print(f"\n=== Top 10 most-populated hex-9 ===")
    for _, r in top.iterrows():
        print(f"  {r['pop_total']:>8,.0f}  {r['hex9_id']}  {str(r['parent_subzone_name']):25s}  ({r['parent_pa']})")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hex9_count": len(hp),
        "sgp_pop_expected": int(total_expected),
        "sgp_pop_allocated": float(total_alloc),
        "drift_pct": round(100 * (total_alloc - total_expected) / total_expected, 6),
        "pop_hdb_allocated": float(hp["pop_hdb"].sum()),
        "pop_non_hdb_allocated": float(hp["pop_non_hdb"].sum()),
        "hexes_with_population": int((hp["pop_total"] > 0).sum()),
        "age_sum_max_discrepancy": float(age_sum_max_err),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()

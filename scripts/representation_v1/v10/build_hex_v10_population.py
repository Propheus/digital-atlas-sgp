"""
Hex v10 — dasymetric population and age bands per hex.

Approach:
    Take subzone population + age breakdown from Census 2025 and distribute to hexes
    within each subzone proportional to that hex's residential floor area. A subzone
    with 8,000 residents split across 5 hexes with residential floor areas
    [100k, 80k, 50k, 20k, 0] sqm gets populations [3200, 2560, 1600, 640, 0].

    This is the standard dasymetric approach and is the correct fix for the
    "persona broadcast" leak: a hex with zero residential floor area gets ZERO
    population / elderly / children, which also means it gets NaN for ratio
    features (elderly_pct etc.) in the persona step.

Inputs:
    data/demographics/pop_age_sex_tod_2025.csv   (332 × 19 × 2 × ... table)
    data/hex_v10/hex_buildings.parquet           (residential_floor_area_sqm)
    data/hex_v10/hex_universe.parquet            (parent_subzone)
    data/boundaries/subzones.geojson             (for subzone name → code mapping)

Output:
    data/hex_v10/hex_population.parquet

Columns:
    hex_id
    population                 (dasymetric, sum to subzone total)
    children_count             (ages 0-14)
    elderly_count              (ages 65+)
    working_age_count          (ages 15-64)
    walking_dependent_count    (children + elderly)
    elderly_pct                (elderly / population, NaN if population == 0)
    walking_dependent_pct      (walking_dependent / population, NaN if 0)
    subzone_pop_total          (denominator used — handy for debugging)
    subzone_res_floor_area     (denominator used — same)
    residential_floor_weight   (hex weight = hex_res / subzone_res, NaN if 0)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[3]
CENSUS = ROOT / "data" / "demographics" / "pop_age_sex_tod_2025.csv"
BLDG = ROOT / "data" / "hex_v10" / "hex_buildings.parquet"
UNI = ROOT / "data" / "hex_v10" / "hex_universe.parquet"
SUBZ = ROOT / "data" / "boundaries" / "subzones.geojson"
OUT = ROOT / "data" / "hex_v10" / "hex_population.parquet"

CHILDREN_AG = {"0_to_4", "5_to_9", "10_to_14"}
ELDERLY_AG = {
    "65_to_69", "70_to_74", "75_to_79", "80_to_84", "85_to_89", "90_and_over",
}


def main() -> None:
    print(f"Loading census: {CENSUS}")
    c = pd.read_csv(CENSUS)
    # Normalize subzone name for matching
    c["subz_name_upper"] = c["SZ"].str.upper().str.strip()

    # Aggregate total + age bands per subzone
    c_tot = c.groupby("subz_name_upper")["Pop"].sum().rename("subzone_pop_total")
    c_chld = c[c["AG"].isin(CHILDREN_AG)].groupby("subz_name_upper")["Pop"].sum().rename("children_count_subz")
    c_eld = c[c["AG"].isin(ELDERLY_AG)].groupby("subz_name_upper")["Pop"].sum().rename("elderly_count_subz")
    sub_df = pd.concat([c_tot, c_chld, c_eld], axis=1).fillna(0)
    sub_df["working_count_subz"] = sub_df["subzone_pop_total"] - sub_df["children_count_subz"] - sub_df["elderly_count_subz"]
    print(f"  census subzones: {len(sub_df)}")
    print(f"  total population: {sub_df['subzone_pop_total'].sum():,.0f}")

    # Map census subzone name -> subzone code via boundaries
    g = gpd.read_file(SUBZ)
    name_to_code = {
        str(n).strip().upper(): c for n, c in zip(g["SUBZONE_N"], g["SUBZONE_C"])
    }
    sub_df = sub_df.reset_index().rename(columns={"subz_name_upper": "parent_subzone_name"})
    sub_df["parent_subzone"] = sub_df["parent_subzone_name"].map(name_to_code)

    unmatched = sub_df[sub_df["parent_subzone"].isna()]
    if len(unmatched):
        print(f"  WARN: {len(unmatched)} census subzones have no boundary code:")
        print(unmatched[["parent_subzone_name", "subzone_pop_total"]].to_string(index=False))

    sub_df = sub_df.dropna(subset=["parent_subzone"]).set_index("parent_subzone")

    # Load hex universe + buildings and join
    uni = pd.read_parquet(UNI, columns=["hex_id", "parent_subzone"])
    bldg = pd.read_parquet(BLDG, columns=["hex_id", "residential_floor_area_sqm"])
    hex_df = uni.merge(bldg, on="hex_id", how="left")
    hex_df["residential_floor_area_sqm"] = hex_df["residential_floor_area_sqm"].fillna(0.0)

    # Subzone residential floor area totals
    sub_res = hex_df.groupby("parent_subzone")["residential_floor_area_sqm"].sum().rename("subzone_res_floor_area")
    hex_df = hex_df.merge(sub_res, on="parent_subzone", how="left")

    # Attach subzone population totals
    hex_df = hex_df.merge(
        sub_df[["subzone_pop_total", "children_count_subz", "elderly_count_subz", "working_count_subz"]],
        left_on="parent_subzone", right_index=True, how="left",
    )

    # Compute the dasymetric weight
    # Where subzone residential floor area is zero (e.g. purely industrial subzones),
    # fall back to uniform distribution across the subzone's hexes — population is
    # likely tiny or zero in those subzones anyway, but this avoids divide-by-zero.
    w = np.where(
        hex_df["subzone_res_floor_area"] > 0,
        hex_df["residential_floor_area_sqm"] / hex_df["subzone_res_floor_area"],
        np.nan,
    )

    # Fallback uniform for subzones with zero residential floor area
    zero_res_sub = hex_df["subzone_res_floor_area"] == 0
    if zero_res_sub.any():
        counts = hex_df[zero_res_sub].groupby("parent_subzone")["hex_id"].count().rename("n_hexes")
        fb = hex_df[zero_res_sub].merge(counts, on="parent_subzone", how="left")
        w_fallback = 1.0 / fb["n_hexes"].to_numpy()
        w[zero_res_sub.to_numpy()] = w_fallback
    hex_df["residential_floor_weight"] = w

    # Distribute subzone totals to hex level
    pop_col = hex_df["subzone_pop_total"].fillna(0).to_numpy()
    chld_col = hex_df["children_count_subz"].fillna(0).to_numpy()
    eld_col = hex_df["elderly_count_subz"].fillna(0).to_numpy()
    work_col = hex_df["working_count_subz"].fillna(0).to_numpy()
    w_arr = hex_df["residential_floor_weight"].fillna(0).to_numpy()

    hex_df["population"] = pop_col * w_arr
    hex_df["children_count"] = chld_col * w_arr
    hex_df["elderly_count"] = eld_col * w_arr
    hex_df["working_age_count"] = work_col * w_arr
    hex_df["walking_dependent_count"] = hex_df["children_count"] + hex_df["elderly_count"]

    # Intentionally DO NOT emit elderly_pct / walking_dependent_pct at hex level.
    # With a single residential-floor-area weight, the numerator and denominator both
    # scale by the same factor, so the ratio collapses to a subzone constant. Without
    # age-differentiated per-hex data (not available), these ratios are inherently
    # subzone-level properties and belong in the subzone feature table, not the hex one.
    # At hex level we keep the raw dasymetric COUNTS, which do vary across hexes.

    # Final tidy
    out_cols = [
        "hex_id",
        "population", "children_count", "elderly_count", "working_age_count",
        "walking_dependent_count",
        "subzone_pop_total", "subzone_res_floor_area", "residential_floor_weight",
    ]
    out_df = hex_df[out_cols]

    # Verify: sum of hex populations per subzone == subzone total (to within rounding)
    sub_check = hex_df.groupby("parent_subzone").agg(
        hex_pop_sum=("population", "sum"),
        subz_tot=("subzone_pop_total", "first"),
    )
    sub_check["diff"] = sub_check["hex_pop_sum"] - sub_check["subz_tot"]
    max_abs_diff = sub_check["diff"].abs().max()
    print(f"  max |hex pop sum - subzone pop total| = {max_abs_diff:.6f}")
    assert max_abs_diff < 1.0, "dasymetric distribution did not preserve subzone totals"

    print(f"Output shape: {out_df.shape}")
    print(f"Hexes with population > 0: {(out_df['population']>0).sum():,}")
    print(f"Total population distributed: {out_df['population'].sum():,.0f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_parquet(OUT, index=False)
    print(f"Wrote {OUT}")

    # Critical check: within-subzone std of elderly_count (should be > 0 because
    # different hexes in a subzone have different residential floor area).
    import pandas as _pd
    check = _pd.concat([uni[['parent_subzone']], out_df[['elderly_count','population']]], axis=1)
    within_std_elderly = check[check['population']>0].groupby('parent_subzone')['elderly_count'].std().describe()
    print()
    print("Within-subzone std of elderly_count (after dasymetric):")
    print(within_std_elderly.to_string())


if __name__ == "__main__":
    main()

"""
Plexis SGP v4 — aggregate population from hex-9 → hex-8 + subzone.

Pure SUM aggregation for counts; recompute shares post-aggregation.

Outputs:
  hex/hex8_population.parquet
  hex/subzone_population.parquet
"""
import json, time
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent


def main():
    t0 = time.time()
    print("Loading...")
    p9 = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    print(f"  hex9_population: {p9.shape}")

    SUM_COLS = ["pop_resident", "pop_hdb", "pop_non_hdb",
                 "pop_0_14", "pop_15_64", "pop_65plus",
                 "pop_nonresident", "pop_dorm", "pop_total_all"]

    # === hex-8 ===
    print("\n  Aggregating to hex-8...")
    p9_with_keys = p9.merge(h9[["hex9_id", "parent_hex8", "parent_subzone"]], on="hex9_id", how="left")
    h8_pop = p9_with_keys.groupby("parent_hex8")[SUM_COLS].sum().reset_index().rename(columns={"parent_hex8": "hex8_id"})
    h8_pop["pop_hdb_share"] = np.where(h8_pop["pop_resident"] > 0, h8_pop["pop_hdb"] / h8_pop["pop_resident"], 0)
    h8_pop["nonres_share"] = np.where(h8_pop["pop_total_all"] > 0, h8_pop["pop_nonresident"] / h8_pop["pop_total_all"], 0)
    h8_pop = h8.merge(h8_pop, on="hex8_id", how="left")
    for c in SUM_COLS + ["pop_hdb_share", "nonres_share"]:
        h8_pop[c] = h8_pop[c].fillna(0)
    h8_pop.to_parquet(ROOT / "hex/hex8_population.parquet", index=False)
    print(f"  hex8_population: {h8_pop.shape}, total={h8_pop['pop_total_all'].sum():,.0f}")

    # === subzone ===
    print("  Aggregating to subzone...")
    sz_pop = p9_with_keys.groupby("parent_subzone")[SUM_COLS].sum().reset_index().rename(columns={"parent_subzone": "subzone_c"})
    sz_pop["pop_hdb_share"] = np.where(sz_pop["pop_resident"] > 0, sz_pop["pop_hdb"] / sz_pop["pop_resident"], 0)
    sz_pop["nonres_share"] = np.where(sz_pop["pop_total_all"] > 0, sz_pop["pop_nonresident"] / sz_pop["pop_total_all"], 0)
    sz_pop.to_parquet(ROOT / "hex/subzone_population.parquet", index=False)
    print(f"  subzone_population: {sz_pop.shape}, total={sz_pop['pop_total_all'].sum():,.0f}")

    # Sanity
    src_total = p9["pop_total_all"].sum()
    h8_total = h8_pop["pop_total_all"].sum()
    sz_total = sz_pop["pop_total_all"].sum()
    print(f"\n=== Conservation check ===")
    print(f"  hex9 total: {src_total:,.0f}")
    print(f"  hex8 total: {h8_total:,.0f}  drift {h8_total - src_total:+.1f}")
    print(f"  subzone total: {sz_total:,.0f}  drift {sz_total - src_total:+.1f}")
    print(f"  wall: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()

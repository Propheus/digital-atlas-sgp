"""
Plexis SGP v4 — Stage 3b: non-resident population allocation.

Approach: borrow V3 hex-8 non-resident totals (1,770,000 calibrated to industrial
dorms + worker inflow patterns), then project to hex-9 children proportional to
land-use weight (favour business zones, then private residential, then mixed).

Why borrow V3: SingStat publishes non-resident totals only at the national level;
V3 manually integrated dormitory locations + LTA daytime intensity to produce a
realistic hex-8 allocation. Re-deriving from scratch without dormitory point data
gives misleading "top hexes" (everywhere with private housing). V3 is the
authoritative subzone-level baseline.

If V3 hex-8 allocation is missing on the host, fall back to a pure URA-based model.
"""
import json, time, os
from pathlib import Path
import pandas as pd
import numpy as np
import h3

ROOT = Path(__file__).parent

V3_HEX8 = Path("/home/azureuser/digital-atlas-sgp/data/hex_v10/hex8_final.parquet")
NATIONAL_NONRES_TOTAL = 1_769_520  # SingStat 2025

OUT_PQ = ROOT / "hex/hex9_population.parquet"
REPORT = ROOT / "hex/non_resident_report.json"


def load_v3_hex8_nonres():
    if not V3_HEX8.exists():
        return None
    v3 = pd.read_parquet(V3_HEX8, columns=["hex8_id", "population_nonresident"])
    v3 = v3.rename(columns={"population_nonresident": "nonres_h8"})
    return v3


def main():
    t0 = time.time()
    print("Loading inputs...")
    pop = pd.read_parquet(ROOT / "hex/hex9_population.parquet")
    lu = pd.read_parquet(ROOT / "hex/hex9_land_use.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    print(f"  hex9: {len(h9):,}  pop_resident total: {pop['pop_total'].sum():,.0f}")

    df = h9[["hex9_id"]].merge(pop, on="hex9_id", how="left").merge(
        lu[["hex9_id", "lu_total_m2", "lu_business_pct", "lu_business_park_pct",
            "lu_residential_pct", "lu_mixed_use_pct", "lu_hotel_pct"]],
        on="hex9_id", how="left",
    )
    # parent_hex8 from H3
    df["parent_hex8"] = df["hex9_id"].apply(lambda c: h3.cell_to_parent(c, 8))

    # Build per-hex9 weight: prefer business + business_park; then mixed_use × hotel; then residential as MDW proxy
    df["w_business"] = (df["lu_business_pct"].fillna(0) + df["lu_business_park_pct"].fillna(0)) * df["lu_total_m2"].fillna(0)
    df["w_mixed_hotel"] = (df["lu_mixed_use_pct"].fillna(0) + df["lu_hotel_pct"].fillna(0)) * df["lu_total_m2"].fillna(0)
    df["w_residential"] = df["lu_residential_pct"].fillna(0) * df["lu_total_m2"].fillna(0)

    # Composite weight, biased toward business/dormitory + transient hotel + small share to residential (MDW)
    df["w_total"] = (
        4.0 * df["w_business"]
        + 1.5 * df["w_mixed_hotel"]
        + 0.5 * df["w_residential"]
        + 0.1   # tiny ε so totally-empty parent hex-8s get equal split among children
    )

    v3 = load_v3_hex8_nonres()
    if v3 is None:
        print("  V3 hex-8 reference not found — using URA-only fallback")
        # Pure URA fallback: distribute total nationally proportional to weight
        df["pop_nonresident"] = NATIONAL_NONRES_TOTAL * df["w_total"] / df["w_total"].sum()
        method = "ura_fallback"
    else:
        print(f"  V3 hex-8 reference loaded: {len(v3):,} hex-8 cells, total={v3['nonres_h8'].sum():,.0f}")
        # For each parent hex-8, split V3's total across our hex-9 children proportional to w_total
        df = df.merge(v3, left_on="parent_hex8", right_on="hex8_id", how="left")
        df["nonres_h8"] = df["nonres_h8"].fillna(0)
        # parent weight sum
        parent_w = df.groupby("parent_hex8")["w_total"].sum().rename("parent_w")
        df = df.merge(parent_w, left_on="parent_hex8", right_index=True, how="left")
        df["pop_nonresident"] = np.where(
            df["parent_w"] > 0,
            df["nonres_h8"] * df["w_total"] / df["parent_w"],
            0,
        )
        method = "v3_hex8_anchored_url_split"

    # Calibrate to exact national total
    cur_sum = df["pop_nonresident"].sum()
    if cur_sum > 0:
        df["pop_nonresident"] = df["pop_nonresident"] * (NATIONAL_NONRES_TOTAL / cur_sum)

    print(f"\n  allocation (post-calibration):")
    print(f"    pop_resident:     {df['pop_total'].sum():>10,.0f}")
    print(f"    pop_nonresident:  {df['pop_nonresident'].sum():>10,.0f}")
    print(f"    pop_total_all:    {df['pop_total'].sum() + df['pop_nonresident'].sum():>10,.0f}")

    # Persist: rename pop_total → pop_resident and add pop_total_all
    out = pop.merge(df[["hex9_id", "pop_nonresident"]], on="hex9_id", how="left")
    out["pop_nonresident"] = out["pop_nonresident"].fillna(0)
    out = out.rename(columns={"pop_total": "pop_resident"})
    out["pop_total_all"] = out["pop_resident"] + out["pop_nonresident"]
    out["nonres_share"] = np.where(
        out["pop_total_all"] > 0,
        out["pop_nonresident"] / out["pop_total_all"],
        0,
    )
    out.to_parquet(OUT_PQ, index=False)

    # Top hexes
    h9_lookup = h9[["hex9_id", "parent_subzone_name", "parent_pa"]].rename(
        columns={"parent_subzone_name": "subzone_label", "parent_pa": "pa_label"}
    )
    top = out.nlargest(20, "pop_nonresident").merge(h9_lookup, on="hex9_id")
    print(f"\n=== Top 20 hexes by non-resident population ===")
    print(f"  {'hex9_id':<18} {'nonres':>8} {'res':>7} {'nr%':>5}  subzone")
    for _, r in top.iterrows():
        print(f"  {r['hex9_id']:<18} {r['pop_nonresident']:>8,.0f} {r['pop_resident']:>7,.0f}"
              f"   {r['nonres_share']*100:>4.0f}%  {str(r['subzone_label']):<28} ({r['pa_label']})")

    # Validation
    drift_pct = (df["pop_nonresident"].sum() - NATIONAL_NONRES_TOTAL) / NATIONAL_NONRES_TOTAL
    print(f"\n=== Validation ===")
    print(f"  Allocated non-residents: {df['pop_nonresident'].sum():,.0f}")
    print(f"  Expected:                {NATIONAL_NONRES_TOTAL:,}")
    print(f"  Drift:                   {drift_pct*100:+.4f}%")
    print(f"  Total population (res + nonres): {out['pop_total_all'].sum():,.0f}")
    print(f"  Hexes with non-residents: {(out['pop_nonresident'] > 0).sum():,}")
    print(f"  Method:                  {method}")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "method": method,
        "national_resident_total": int(out["pop_resident"].sum()),
        "national_nonresident_total": float(out["pop_nonresident"].sum()),
        "national_total": float(out["pop_total_all"].sum()),
        "drift_pct": round(drift_pct * 100, 6),
        "hexes_with_nonres": int((out["pop_nonresident"] > 0).sum()),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")
    print(f"Output: {OUT_PQ}")


if __name__ == "__main__":
    main()

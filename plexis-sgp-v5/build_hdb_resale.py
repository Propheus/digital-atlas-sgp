"""
Plexis SGP v4 — Stage 7p: HDB resale prices per scale.

Aggregates 227K HDB resale transactions (Jan 2017 → Mar 2026) at HDB-town
level, then broadcasts to each hex/subzone via dominant HDB-town overlap.

Outputs:
  hex/hex9_hdb_resale.parquet
  hex/hex8_hdb_resale.parquet
  hex/subzone_hdb_resale.parquet
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
RESALE_CSV = DATA / "property/hdb_resale_prices.csv"


def parse_lease_remaining(s):
    """'61 years 04 months' → 61.33; NaN if unparseable."""
    if pd.isna(s): return np.nan
    s = str(s).lower().strip()
    yrs = mons = 0
    parts = s.split()
    for i, p in enumerate(parts):
        if p.startswith("year") and i > 0:
            try: yrs = int(parts[i-1])
            except: pass
        elif p.startswith("month") and i > 0:
            try: mons = int(parts[i-1])
            except: pass
    return yrs + mons / 12.0 if (yrs or mons) else np.nan


def town_aggregates(df):
    """Per-town aggregations. df has month, town, flat_type, floor_area_sqm, resale_price, lease_remaining_yrs."""
    df = df.copy()
    df["price_psm"] = df["resale_price"] / df["floor_area_sqm"]
    cutoff_12m = df["month"].max() - pd.DateOffset(months=12)
    df["is_12m"] = df["month"] >= cutoff_12m

    rows = []
    for town, g in df.groupby("town"):
        all_p = g
        last12 = g[g["is_12m"]]
        flat4 = g[g["flat_type"] == "4 ROOM"]
        rows.append({
            "town": town,
            "hdb_resale_txns_total": len(all_p),
            "hdb_resale_txns_12m": len(last12),
            "hdb_resale_median_price": float(all_p["resale_price"].median()),
            "hdb_resale_median_psm": float(all_p["price_psm"].median()),
            "hdb_resale_4r_median_price": float(flat4["resale_price"].median()) if len(flat4) else 0.0,
            "hdb_resale_4r_median_psm": float(flat4["price_psm"].median()) if len(flat4) else 0.0,
            "hdb_resale_12m_median_price": float(last12["resale_price"].median()) if len(last12) else 0.0,
            "hdb_resale_avg_lease_remaining_yrs": float(all_p["lease_remaining_yrs"].mean()),
        })
    return pd.DataFrame(rows)


def dominant_town(overlap, key_col):
    """For each hex/subzone, pick the HDB town with max overlap."""
    return (overlap.sort_values("overlap_deg2", ascending=False)
                   .drop_duplicates(key_col)
                   .reset_index(drop=True))


def main():
    t0 = time.time()
    print(f"Loading {RESALE_CSV.name}...")
    df = pd.read_csv(RESALE_CSV, dtype={"block": str})
    df["month"] = pd.to_datetime(df["month"])
    df["lease_remaining_yrs"] = df["remaining_lease"].apply(parse_lease_remaining)
    print(f"  {len(df):,} txns, {df['month'].min().date()} → {df['month'].max().date()}, {df['town'].nunique()} towns")

    print("Computing per-town aggregates...")
    town_df = town_aggregates(df)
    print(f"  {len(town_df)} towns")
    print("\n=== Median 4-room price by town (top 10 / bottom 10) ===")
    sorted_towns = town_df.sort_values("hdb_resale_4r_median_price", ascending=False)
    print(sorted_towns[["town","hdb_resale_4r_median_price","hdb_resale_4r_median_psm","hdb_resale_txns_total"]].head(10).to_string(index=False))
    print("...")
    print(sorted_towns[["town","hdb_resale_4r_median_price","hdb_resale_4r_median_psm","hdb_resale_txns_total"]].tail(10).to_string(index=False))

    metric_cols = [c for c in town_df.columns if c != "town"]

    # === HEX-9 ===
    print("\n--- HEX-9 ---")
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h9_ov = pd.read_parquet(ROOT / "hex/hex9_hdb_town_overlap.parquet")
    h9_dom = dominant_town(h9_ov, "hex9_id")[["hex9_id","hdb_town"]]
    h9 = h9_uni[["hex9_id"]].merge(h9_dom, on="hex9_id", how="left")
    h9 = h9.merge(town_df, left_on="hdb_town", right_on="town", how="left")
    h9["hdb_resale_in_town"] = h9["hdb_town"].notna().astype(int)
    h9 = h9.drop(columns=["town"])
    for c in metric_cols:
        h9[c] = h9[c].fillna(0)
    h9 = h9[["hex9_id","hdb_resale_in_town"] + metric_cols]
    h9.to_parquet(ROOT / "hex/hex9_hdb_resale.parquet", index=False)
    print(f"  hex9_hdb_resale: {h9.shape}, hexes_in_hdb_town: {int(h9['hdb_resale_in_town'].sum())}")

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    h8_ov = pd.read_parquet(ROOT / "hex/hex8_hdb_town_overlap.parquet")
    h8_dom = dominant_town(h8_ov, "hex8_id")[["hex8_id","hdb_town"]]
    h8 = h8_uni[["hex8_id"]].merge(h8_dom, on="hex8_id", how="left")
    h8 = h8.merge(town_df, left_on="hdb_town", right_on="town", how="left")
    h8["hdb_resale_in_town"] = h8["hdb_town"].notna().astype(int)
    h8 = h8.drop(columns=["town"])
    for c in metric_cols:
        h8[c] = h8[c].fillna(0)
    h8 = h8[["hex8_id","hdb_resale_in_town"] + metric_cols]
    h8.to_parquet(ROOT / "hex/hex8_hdb_resale.parquet", index=False)
    print(f"  hex8_hdb_resale: {h8.shape}, hexes_in_hdb_town: {int(h8['hdb_resale_in_town'].sum())}")

    # === SUBZONE === (derive dominant town per subzone via hex9 overlaps)
    print("\n--- SUBZONE ---")
    h9_with_sz = h9_uni[["hex9_id","parent_subzone"]].merge(h9_dom, on="hex9_id", how="inner")
    sz_dom = (h9_with_sz.groupby(["parent_subzone","hdb_town"]).size()
              .reset_index(name="n").sort_values("n", ascending=False)
              .drop_duplicates("parent_subzone")
              .rename(columns={"parent_subzone":"subzone_c"}))
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz = sz_lu.merge(sz_dom[["subzone_c","hdb_town"]], on="subzone_c", how="left")
    sz = sz.merge(town_df, left_on="hdb_town", right_on="town", how="left")
    sz["hdb_resale_in_town"] = sz["hdb_town"].notna().astype(int)
    sz = sz.drop(columns=["town"])
    for c in metric_cols:
        sz[c] = sz[c].fillna(0)
    sz = sz[["subzone_c","hdb_resale_in_town"] + metric_cols]
    sz.to_parquet(ROOT / "hex/subzone_hdb_resale.parquet", index=False)
    print(f"  subzone_hdb_resale: {sz.shape}, subzones_in_hdb_town: {int(sz['hdb_resale_in_town'].sum())}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_txns": len(df),
        "month_range": [str(df["month"].min().date()), str(df["month"].max().date())],
        "towns": int(df["town"].nunique()),
        "shapes": {"hex9": list(h9.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
        "national_median_price": float(df["resale_price"].median()),
        "national_median_psm":   float((df["resale_price"]/df["floor_area_sqm"]).median()),
    }
    with open(ROOT / "hex/hdb_resale_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

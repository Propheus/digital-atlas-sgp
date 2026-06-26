"""
Plexis SGP v4 — Stage 7: place_composition per scale.

Aggregates the 190,591 classified places (places/sgp_places_final.parquet) into
hex9 / hex8 / subzone with category counts + diversity + magnet/long-tail signals.

Outputs:
  hex/hex9_place_composition.parquet
  hex/hex8_place_composition.parquet
  hex/subzone_place_composition.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent

CATS = [
    "bakery","bar_nightlife","beauty_personal","business_office","cafe_coffee",
    "convenience","education","entertainment_culture","fast_food","fitness_recreation",
    "government_public","hawker","health_medical","hotel_hospitality","industrial_mfg",
    "other_uncategorized","park_open","religious_worship","residential","restaurant",
    "services","shopping_retail","supermarket","transportation",
    "financial_services","automated_kiosk","pharmacy_beauty",
]
CAT_COLS = [f"pc_cat_{c}" for c in CATS]


def shannon_vec(arr, totals):
    """Row-wise Shannon entropy of category mix. arr: NxK counts. totals: N totals."""
    safe = np.where(totals == 0, 1, totals).reshape(-1, 1)
    p = arr / safe
    log_p = np.where(p > 0, np.log(p), 0)
    h = -(p * log_p).sum(axis=1)
    h[totals == 0] = 0
    return h


def aggregate(places, key_col):
    g = places.groupby(key_col)

    cat_cnt = pd.crosstab(places[key_col], places["plexis_category"]).reindex(columns=CATS, fill_value=0)
    cat_cnt.columns = CAT_COLS
    cat_cnt = cat_cnt.reset_index()

    summ = g.agg(
        pc_total=("id", "count"),
        pc_unique_brands=("brand_norm", lambda s: s.dropna().nunique()),
        pc_magnets=("is_magnet", "sum"),
        pc_long_tail=("is_long_tail", "sum"),
        pc_with_rating=("has_rating", "sum"),
        pc_total_reviews=("reviews_count", "sum"),
    ).reset_index()

    rated = places[places["has_rating"] & (places["reviews_count"] > 0)].copy()
    rated["_w"] = rated["rating"] * rated["reviews_count"]
    wr = rated.groupby(key_col).agg(_num=("_w", "sum"), _den=("reviews_count", "sum")).reset_index()
    wr["pc_avg_rating"] = (wr["_num"] / wr["_den"]).round(2)
    wr = wr[[key_col, "pc_avg_rating"]]

    out = summ.merge(wr, on=key_col, how="left")
    out["pc_avg_rating"] = out["pc_avg_rating"].fillna(0.0)
    out = out.merge(cat_cnt, on=key_col, how="left")

    arr = out[CAT_COLS].values.astype(float)
    totals = out["pc_total"].values.astype(float)
    out["pc_diversity"] = np.round(shannon_vec(arr, totals), 3)

    dom_idx = arr.argmax(axis=1)
    dom = np.array(CATS)[dom_idx]
    dom[totals == 0] = "none"
    out["pc_dominant_category"] = dom

    return out


def fill_zeros(df, key_col):
    fill_num = ["pc_total","pc_unique_brands","pc_magnets","pc_long_tail",
                "pc_with_rating","pc_total_reviews","pc_avg_rating","pc_diversity"] + CAT_COLS
    for c in fill_num:
        if c in df.columns:
            df[c] = df[c].fillna(0)
    df["pc_dominant_category"] = df["pc_dominant_category"].fillna("none")
    return df


def main():
    t0 = time.time()
    print("Loading places...")
    places = pd.read_parquet(ROOT / "places/sgp_places_final.parquet")
    print(f"  {len(places):,} places")

    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    sz_uni = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()

    # Re-key both hex8 and subzone from the hex9 universe so all 3 scales line
    # up exactly. Reasons:
    #   - 331 vs 326 subzone codes drift between places and v4 universe
    #   - 13,343 places have stale hex8_id that disagrees with h3.cell_to_parent;
    #     the universe.parent_hex8 is canonical-correct.
    places = places.drop(columns=["hex8_id"]).merge(
        h9_uni[["hex9_id", "parent_hex8", "parent_subzone"]].rename(
            columns={"parent_hex8": "hex8_id", "parent_subzone": "subzone_c_v4"}),
        on="hex9_id", how="left",
    )
    print(f"  places re-keyed via hex9_universe "
          f"(hex8 null: {places['hex8_id'].isna().sum()}, "
          f"subzone null: {places['subzone_c_v4'].isna().sum()})")

    # === HEX-9 ===
    print("\n--- HEX-9 ---")
    h9 = aggregate(places, "hex9_id")
    h9 = h9_uni[["hex9_id"]].merge(h9, on="hex9_id", how="left")
    h9 = fill_zeros(h9, "hex9_id")
    h9.to_parquet(ROOT / "hex/hex9_place_composition.parquet", index=False)
    print(f"  hex9_place_composition: {h9.shape}")

    # === HEX-8 ===
    print("\n--- HEX-8 ---")
    h8 = aggregate(places, "hex8_id")
    h8 = h8_uni[["hex8_id"]].merge(h8, on="hex8_id", how="left")
    h8 = fill_zeros(h8, "hex8_id")
    h8.to_parquet(ROOT / "hex/hex8_place_composition.parquet", index=False)
    print(f"  hex8_place_composition: {h8.shape}")

    # === SUBZONE === (use hex9-derived subzone, not places' parent_subzone_c)
    print("\n--- SUBZONE ---")
    sz_places = places.dropna(subset=["subzone_c_v4"])
    sz = aggregate(sz_places, "subzone_c_v4").rename(columns={"subzone_c_v4": "subzone_c"})
    sz = sz_uni.merge(sz, on="subzone_c", how="left")
    sz = fill_zeros(sz, "subzone_c")
    sz.to_parquet(ROOT / "hex/subzone_place_composition.parquet", index=False)
    print(f"  subzone_place_composition: {sz.shape}")

    # Top hex9 by pc_total
    h9_lookup = h9_uni[["hex9_id","parent_pa","parent_subzone_name"]]
    top = h9.nlargest(10, "pc_total").merge(h9_lookup, on="hex9_id")
    print(f"\n=== Top 10 hex9 by pc_total ===")
    for _, r in top.iterrows():
        print(f"  pc={r['pc_total']:>4.0f}  div={r['pc_diversity']:.2f}  dom={r['pc_dominant_category']:<22}  "
              f"{str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    print(f"\n=== Top 10 hex9 by pc_magnets ===")
    top2 = h9.nlargest(10, "pc_magnets").merge(h9_lookup, on="hex9_id")
    for _, r in top2.iterrows():
        print(f"  mag={r['pc_magnets']:>3.0f}  pc_total={r['pc_total']:>3.0f}  "
              f"{str(r['parent_subzone_name']):<25} ({r['parent_pa']})")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_places": len(places),
        "shapes": {"hex9": list(h9.shape), "hex8": list(h8.shape), "subzone": list(sz.shape)},
        "totals": {
            "places_in_hex9_universe": int(h9["pc_total"].sum()),
            "places_in_hex8_universe": int(h8["pc_total"].sum()),
            "places_in_subzone_universe": int(sz["pc_total"].sum()),
            "hex9_with_places": int((h9["pc_total"] > 0).sum()),
            "hex8_with_places": int((h8["pc_total"] > 0).sum()),
            "subzone_with_places": int((sz["pc_total"] > 0).sum()),
        },
    }
    with open(ROOT / "hex/place_composition_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

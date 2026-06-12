"""
Plexis SGP v4 — Stage 12: demand pull (gravity-model accessibility).

For each hex, compute Σ A_d · exp(-d/L) over six destination types:
  pull_cbd                CBD office cluster (DOWNTOWN CORE / RAFFLES PLACE / CECIL / TANJONG PAGAR / MARINA SOUTH)
  pull_mall               top retail magnets
  pull_hospital           top healthcare magnets
  pull_mrt_interchange    rail interchange stations
  pull_school_premium     SAP / Gifted / IP schools
  pull_airport            Changi airport
  pull_composite          mean of the six (each min-max normalized first)

Distances are Euclidean in EPSG:3414 (meters). Decay scale L is type-specific
(CBD pull is regional, mall pull is local).

Outputs:
  hex/hex9_demand_pull.parquet
  hex/hex8_demand_pull.parquet
  hex/subzone_demand_pull.parquet
"""
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import h3

ROOT = Path(__file__).parent

DECAY = {
    "pull_cbd":             6000.0,
    "pull_mall":            2500.0,
    "pull_hospital":        4000.0,
    "pull_mrt_interchange": 2000.0,
    "pull_school_premium":  3000.0,
    "pull_airport":        15000.0,
}

CBD_PAS = {"DOWNTOWN CORE","RAFFLES PLACE","CECIL","TANJONG PAGAR",
           "MARINA SOUTH","MARINA EAST","SINGAPORE RIVER"}
AIRPORT_PAS = {"CHANGI","CHANGI BAY","CHANGI POINT"}


def gravity_pull(origin_xy, dest_xy, dest_weights, L):
    """For each origin, return Σ w_i exp(-d_i / L) over destinations."""
    if len(dest_xy) == 0:
        return np.zeros(len(origin_xy))
    pull = np.zeros(len(origin_xy))
    # Process in chunks to keep memory bounded
    CHUNK = 256
    for s in range(0, len(dest_xy), CHUNK):
        e = min(s + CHUNK, len(dest_xy))
        dx = origin_xy[:, 0:1] - dest_xy[s:e, 0]
        dy = origin_xy[:, 1:2] - dest_xy[s:e, 1]
        d = np.sqrt(dx * dx + dy * dy)
        decay = np.exp(-d / L)
        pull += (decay * dest_weights[s:e][None, :]).sum(axis=1)
    return pull


def minmax01(v):
    v = np.asarray(v, dtype=float)
    lo, hi = np.nanmin(v), np.nanmax(v)
    if hi <= lo: return np.zeros_like(v)
    return ((v - lo) / (hi - lo)).clip(0, 1)


def main():
    t0 = time.time()
    print("Loading inputs...")
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    h9 = pd.read_parquet(ROOT / "hex/hex9_all_features.parquet")
    n = len(h9)
    print(f"  hex9: {n:,}, all_features cols: {len(h9.columns)}")

    # Origin centroids in EPSG:3414
    cents = np.array([h3.cell_to_latlng(c) for c in h9["hex9_id"]])
    g = gpd.GeoDataFrame(geometry=gpd.points_from_xy(cents[:, 1], cents[:, 0]),
                         crs="EPSG:4326").to_crs(3414)
    origin_xy = np.column_stack([g.geometry.x.values, g.geometry.y.values])

    out = pd.DataFrame({"hex9_id": h9["hex9_id"].values})

    # === 1. CBD pull ===
    print("\nComputing pull_cbd...")
    in_cbd = h9["parent_pa"].isin(CBD_PAS) & (h9.get("pc_cat_business_office", 0) > 0)
    idx = np.where(in_cbd.values)[0]
    if len(idx) == 0:
        print("  no CBD destinations found; check parent_pa values")
        out["pull_cbd_raw"] = 0.0
    else:
        w = h9.loc[in_cbd, "pc_cat_business_office"].values.astype(float)
        out["pull_cbd_raw"] = gravity_pull(origin_xy, origin_xy[idx], w, DECAY["pull_cbd"])
        print(f"  destinations: {len(idx)} CBD office hexes, total weight {w.sum():.0f}")

    # === 2. Mall pull ===
    print("Computing pull_mall...")
    score = h9.get("pc_cat_shopping_retail", 0) * (h9.get("pc_magnets", 0) + 1)
    thr = score.quantile(0.95) if (score > 0).any() else 0
    mall_mask = score >= thr if thr > 0 else pd.Series([False] * n)
    idx = np.where(mall_mask.values)[0]
    w = score[mall_mask].values.astype(float)
    out["pull_mall_raw"] = gravity_pull(origin_xy, origin_xy[idx], w, DECAY["pull_mall"])
    print(f"  destinations: {len(idx)} mall hexes (≥p95)")

    # === 3. Hospital pull ===
    print("Computing pull_hospital...")
    score = h9.get("pc_cat_health_medical", 0) * (h9.get("pc_magnets", 0) + 1)
    thr = score.quantile(0.95) if (score > 0).any() else 0
    hosp_mask = score >= thr if thr > 0 else pd.Series([False] * n)
    idx = np.where(hosp_mask.values)[0]
    w = score[hosp_mask].values.astype(float)
    out["pull_hospital_raw"] = gravity_pull(origin_xy, origin_xy[idx], w, DECAY["pull_hospital"])
    print(f"  destinations: {len(idx)} hospital-cluster hexes")

    # === 4. MRT interchange pull ===
    print("Computing pull_mrt_interchange...")
    intch = h9.get("is_mrt_interchange", False).fillna(False).astype(bool)
    idx = np.where(intch.values)[0]
    w = np.ones(intch.sum(), dtype=float)
    out["pull_mrt_interchange_raw"] = gravity_pull(origin_xy, origin_xy[idx], w, DECAY["pull_mrt_interchange"])
    print(f"  destinations: {len(idx)} interchange hexes")

    # === 5. Premium school pull ===
    print("Computing pull_school_premium...")
    sch = h9.get("school_count_premium", 0)
    sch_mask = sch > 0
    idx = np.where(sch_mask.values)[0]
    w = sch[sch_mask].values.astype(float)
    out["pull_school_premium_raw"] = gravity_pull(origin_xy, origin_xy[idx], w, DECAY["pull_school_premium"])
    print(f"  destinations: {len(idx)} premium-school hexes (total {int(w.sum())} schools)")

    # === 6. Airport pull ===
    print("Computing pull_airport...")
    air_mask = h9["parent_pa"].isin(AIRPORT_PAS)
    idx = np.where(air_mask.values)[0]
    w = np.ones(air_mask.sum(), dtype=float)
    out["pull_airport_raw"] = gravity_pull(origin_xy, origin_xy[idx], w, DECAY["pull_airport"])
    print(f"  destinations: {len(idx)} Changi-area hexes")

    # === Normalize each pull to 0..1 ===
    print("\nNormalizing each pull to [0,1]...")
    for col in ["pull_cbd","pull_mall","pull_hospital","pull_mrt_interchange",
                "pull_school_premium","pull_airport"]:
        out[col] = minmax01(out[f"{col}_raw"]).round(3)
    out = out.drop(columns=[c for c in out.columns if c.endswith("_raw")])

    # Composite (mean of the six)
    pull_cols = [c for c in out.columns if c.startswith("pull_")]
    out["pull_composite"] = out[pull_cols].mean(axis=1).round(3)

    out.to_parquet(ROOT / "hex/hex9_demand_pull.parquet", index=False)
    print(f"\n  hex9_demand_pull: {out.shape}")

    # === Aggregate to hex8 + subzone (mean of constituent hex9 pulls) ===
    print("\n--- HEX-8 ---")
    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h9wp = out.merge(h9_uni[["hex9_id","parent_hex8"]], on="hex9_id")
    pull_all = pull_cols + ["pull_composite"]
    h8_agg = h9wp.groupby("parent_hex8")[pull_all].mean().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_agg, on="hex8_id", how="left")
    for c in pull_all: h8_out[c] = h8_out[c].fillna(0).round(3)
    h8_out.to_parquet(ROOT / "hex/hex8_demand_pull.parquet", index=False)
    print(f"  hex8_demand_pull: {h8_out.shape}")

    print("\n--- SUBZONE ---")
    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    h9wsz = out.merge(h9_uni[["hex9_id","parent_subzone"]], on="hex9_id")
    sz_agg = h9wsz.groupby("parent_subzone")[pull_all].mean().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_agg, on="subzone_c", how="left")
    for c in pull_all: sz_out[c] = sz_out[c].fillna(0).round(3)
    sz_out.to_parquet(ROOT / "hex/subzone_demand_pull.parquet", index=False)
    print(f"  subzone_demand_pull: {sz_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "decay_scales_m": DECAY,
        "shapes": {"hex9": list(out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
        "destination_counts": {
            "cbd": int(in_cbd.sum()), "mall": int(mall_mask.sum()),
            "hospital": int(hosp_mask.sum()), "mrt_interchange": int(intch.sum()),
            "school_premium": int(sch_mask.sum()), "airport": int(air_mask.sum()),
        },
    }
    with open(ROOT / "hex/demand_pull_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

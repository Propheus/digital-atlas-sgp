"""
Plexis SGP v4 — Stage 26: LTA Datamall dynamic features (carparks + speed bands).

Live data (snapshot at run time):
  /CarParkAvailability/v2  — every public carpark with available_lots, agency
  /v3/Traffic/SpeedBands   — every road link with speed_band (1=<10kmh ... 8=>=70kmh)

Per-hex columns:
  carpark_count_avail              # of carparks with availability
  carpark_lots_avail               total available lots
  speed_band_count                 # of road segments touching hex
  speed_band_avg                   mean speed band (1..8)
  jam_pct                          % of segments in slowest 2 bands
  dyn_avg_speed_kmh                approx avg speed (mid-of-band)

Outputs:
  hex/hex9_lta_dynamic.parquet
  hex/hex8_lta_dynamic.parquet
  hex/subzone_lta_dynamic.parquet
"""
import json, os, time
from pathlib import Path
import numpy as np
import pandas as pd
import h3
import requests

ROOT = Path(__file__).parent
LTA_KEY = os.environ.get("LTA_KEY", "")
H = {"AccountKey": LTA_KEY, "accept": "application/json"}

# Speed band → mid-speed kmh (LTA spec)
SPEED_MID = {1: 5, 2: 14, 3: 24, 4: 34, 5: 44, 6: 54, 7: 64, 8: 74}


def fetch_paged(endpoint, max_records=200_000):
    """Paginate through LTA OData endpoint (500/page)."""
    url = f"https://datamall2.mytransport.sg/ltaodataservice/{endpoint}"
    out = []
    skip = 0
    while True:
        r = requests.get(url, headers=H, params={"$skip": skip}, timeout=30)
        if r.status_code != 200:
            print(f"  status {r.status_code} on skip={skip}")
            break
        v = r.json().get("value", [])
        if not v: break
        out.extend(v)
        if len(v) < 500: break
        skip += 500
        if len(out) >= max_records: break
    return out


def main():
    t0 = time.time()

    # === CARPARKS ===
    print("Fetching CarParkAvailability/v2...")
    cp = fetch_paged("CarParkAvailabilityv2")
    print(f"  {len(cp)} carparks")
    cp_df = pd.DataFrame(cp)
    if len(cp_df):
        cp_df = cp_df[cp_df["Location"].astype(str).str.contains(" ")]
        cp_df["lat"] = cp_df["Location"].astype(str).str.split().str[0].astype(float)
        cp_df["lng"] = cp_df["Location"].astype(str).str.split().str[1].astype(float)
        cp_df["AvailableLots"] = pd.to_numeric(cp_df["AvailableLots"], errors="coerce").fillna(0).astype(int)
        cp_df["hex9_id"] = [h3.latlng_to_cell(la, lo, 9) for la, lo in zip(cp_df["lat"], cp_df["lng"])]
        cp_hex = cp_df.groupby("hex9_id").agg(
            carpark_count_avail=("CarParkID","count"),
            carpark_lots_avail=("AvailableLots","sum"),
        ).reset_index()
    else:
        cp_hex = pd.DataFrame({"hex9_id": [], "carpark_count_avail": [], "carpark_lots_avail": []})

    # === SPEED BANDS ===
    print("Fetching Traffic/SpeedBands...")
    sb = fetch_paged("v3/TrafficSpeedBands")
    print(f"  {len(sb)} road segments")
    sb_df = pd.DataFrame(sb)
    if len(sb_df):
        # Use midpoint of segment as hex assignment (StartLat/Lng + EndLat/Lng)
        for c in ["StartLat","StartLon","EndLat","EndLon","SpeedBand"]:
            sb_df[c] = pd.to_numeric(sb_df[c], errors="coerce")
        sb_df = sb_df.dropna(subset=["StartLat","StartLon","EndLat","EndLon","SpeedBand"])
        sb_df["mid_lat"] = (sb_df["StartLat"] + sb_df["EndLat"]) / 2
        sb_df["mid_lng"] = (sb_df["StartLon"] + sb_df["EndLon"]) / 2
        sb_df["hex9_id"] = [h3.latlng_to_cell(la, lo, 9) for la, lo in zip(sb_df["mid_lat"], sb_df["mid_lng"])]
        sb_df["mid_speed_kmh"] = sb_df["SpeedBand"].astype(int).map(SPEED_MID).fillna(0)
        sb_hex = sb_df.groupby("hex9_id").agg(
            speed_band_count=("SpeedBand","count"),
            speed_band_avg=("SpeedBand","mean"),
            jam_pct=("SpeedBand", lambda x: (x <= 2).mean() * 100),
            dyn_avg_speed_kmh=("mid_speed_kmh","mean"),
        ).reset_index()
    else:
        sb_hex = pd.DataFrame({"hex9_id":[], "speed_band_count":[], "speed_band_avg":[], "jam_pct":[], "dyn_avg_speed_kmh":[]})

    # === Merge ===
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    out = h9_uni[["hex9_id"]].copy()
    out = out.merge(cp_hex, on="hex9_id", how="left").merge(sb_hex, on="hex9_id", how="left")

    int_cols = ["carpark_count_avail","carpark_lots_avail","speed_band_count"]
    for c in int_cols:
        out[c] = out[c].fillna(0).astype(int)
    for c in ["speed_band_avg","jam_pct","dyn_avg_speed_kmh"]:
        out[c] = out[c].fillna(0).round(2)

    out.to_parquet(ROOT / "hex/hex9_lta_dynamic.parquet", index=False)
    print(f"\n  hex9_lta_dynamic: {out.shape}")

    # Aggregate
    h9wp = out.merge(h9_uni[["hex9_id","parent_hex8","parent_subzone"]], on="hex9_id")

    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h8_sum = h9wp.groupby("parent_hex8")[["carpark_count_avail","carpark_lots_avail","speed_band_count"]].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_mean = h9wp.groupby("parent_hex8")[["speed_band_avg","jam_pct","dyn_avg_speed_kmh"]].mean().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_sum, on="hex8_id", how="left").merge(h8_mean, on="hex8_id", how="left")
    for c in int_cols: h8_out[c] = h8_out[c].fillna(0).astype(int)
    for c in ["speed_band_avg","jam_pct","dyn_avg_speed_kmh"]: h8_out[c] = h8_out[c].fillna(0).round(2)
    h8_out.to_parquet(ROOT / "hex/hex8_lta_dynamic.parquet", index=False)
    print(f"  hex8_lta_dynamic: {h8_out.shape}")

    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz_sum = h9wp.groupby("parent_subzone")[["carpark_count_avail","carpark_lots_avail","speed_band_count"]].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_mean = h9wp.groupby("parent_subzone")[["speed_band_avg","jam_pct","dyn_avg_speed_kmh"]].mean().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_sum, on="subzone_c", how="left").merge(sz_mean, on="subzone_c", how="left")
    for c in int_cols: sz_out[c] = sz_out[c].fillna(0).astype(int)
    for c in ["speed_band_avg","jam_pct","dyn_avg_speed_kmh"]: sz_out[c] = sz_out[c].fillna(0).round(2)
    sz_out.to_parquet(ROOT / "hex/subzone_lta_dynamic.parquet", index=False)
    print(f"  subzone_lta_dynamic: {sz_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "carparks_fetched": len(cp_df),
        "speed_segments_fetched": len(sb_df) if len(sb_df) else 0,
        "shapes": {"hex9": list(out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
        "totals": {
            "carpark_count_avail_total": int(out["carpark_count_avail"].sum()),
            "carpark_lots_avail_total": int(out["carpark_lots_avail"].sum()),
            "speed_band_count_total": int(out["speed_band_count"].sum()),
        },
    }
    with open(ROOT / "hex/lta_dynamic_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

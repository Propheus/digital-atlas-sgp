"""
Plexis SGP v4 — OD (origin-destination) flow layer at hex8.

Source: LTA DataMall Passenger Volume by OD (Bus Stops + Train Stations),
month 2026-04. Bus stops -> lat/lng via DataMall BusStops API; train station
codes -> lat/lng via cheeaun/sgraildata sg-rail.geojson (handles interchange
codes like NS25/EW13 by exploding station_codes). Stops -> hex8 (H3 res 8).

Stores combined bus+train flows for:  weekday all-day, AM peak (7-9h),
PM peak (17-19h).

Outputs:
  data/lta_od/hex8_od_matrix.parquet   sparse origin_hex8 x dest_hex8 flows
  hex/hex8_od_features.parquet         per-hex8 summary -> merged into master

Reads LTA key from env LTA_KEY (not committed). Trips are MONTHLY totals.
"""
import os, time, json, math, re
from pathlib import Path
import numpy as np
import pandas as pd
import h3
import requests

ROOT = Path(__file__).parent
OD = ROOT / "data/lta_od"
KEY = os.environ["LTA_KEY"]
AM = {7, 8, 9}
PM = {17, 18, 19}


def bus_stop_hex8():
    """Pull all bus stops from DataMall, map BusStopCode -> hex8."""
    base = "https://datamall2.mytransport.sg/ltaodataservice/BusStops"
    rows, skip = [], 0
    while True:
        r = requests.get(base, headers={"AccountKey": KEY}, params={"$skip": skip}, timeout=30)
        v = r.json().get("value", [])
        if not v:
            break
        rows.extend(v); skip += 500
    bs = pd.DataFrame(rows)
    bs["hex8"] = [h3.latlng_to_cell(float(la), float(lo), 8)
                  for la, lo in zip(bs["Latitude"], bs["Longitude"])]
    print(f"  bus stops: {len(bs):,} -> {bs['hex8'].nunique()} hex8")
    return dict(zip(bs["BusStopCode"].astype(str), bs["hex8"]))


def train_code_hex8():
    """Explode sg-rail station_codes -> hex8 (each code component of an
    interchange maps to that station's hex8)."""
    gj = json.load(open(OD / "sg-rail.geojson"))
    m = {}
    for f in gj["features"]:
        if f["geometry"]["type"] != "Point":
            continue
        codes = f["properties"].get("station_codes")
        if not codes:
            continue
        lng, lat = f["geometry"]["coordinates"][:2]
        hx = h3.latlng_to_cell(float(lat), float(lng), 8)
        # sg-rail joins interchange codes with '-' (e.g. NS1-EW24); OD uses '/'
        for c in re.split(r"[-/ ]+", str(codes)):
            if c:
                m[c] = hx
    print(f"  train codes resolved: {len(m):,}")
    return m


def resolve_train(code, tmap):
    """OD train code may be 'NS25/EW13'; resolve via any component."""
    if code in tmap:
        return tmap[code]
    for c in re.split(r"[-/ ]+", str(code)):
        if c in tmap:
            return tmap[c]
    return None


def map_od(csv, omap, is_train, tmap=None):
    df = pd.read_csv(csv, dtype={"ORIGIN_PT_CODE": str, "DESTINATION_PT_CODE": str})
    df = df[df["DAY_TYPE"] == "WEEKDAY"].copy()
    if is_train:
        codes = pd.unique(pd.concat([df["ORIGIN_PT_CODE"], df["DESTINATION_PT_CODE"]]))
        lut = {c: resolve_train(c, tmap) for c in codes}
        df["o_hex"] = df["ORIGIN_PT_CODE"].map(lut)
        df["d_hex"] = df["DESTINATION_PT_CODE"].map(lut)
    else:
        df["o_hex"] = df["ORIGIN_PT_CODE"].map(omap)
        df["d_hex"] = df["DESTINATION_PT_CODE"].map(omap)
    tot = df["TOTAL_TRIPS"].sum()
    ok = df.dropna(subset=["o_hex", "d_hex"])
    mapped = ok["TOTAL_TRIPS"].sum()
    print(f"  {csv.name}: {len(df):,} weekday rows | trips {tot:,.0f} | mapped "
          f"{mapped:,.0f} ({100*mapped/tot:.1f}%)")
    ok = ok.copy()
    ok["peak"] = np.where(ok["TIME_PER_HOUR"].isin(AM), "am",
                  np.where(ok["TIME_PER_HOUR"].isin(PM), "pm", "off"))
    return ok[["o_hex", "d_hex", "TIME_PER_HOUR", "peak", "TOTAL_TRIPS"]]


def main():
    t0 = time.time()
    omap = bus_stop_hex8()
    tmap = train_code_hex8()
    bus = map_od(OD / "origin_destination_bus_202604.csv", omap, False)
    trn = map_od(OD / "origin_destination_train_202604.csv", None, True, tmap)
    flows = pd.concat([bus, trn], ignore_index=True)

    # --- sparse matrix: weekday all-day + AM + PM ---
    def agg(sub):
        return sub.groupby(["o_hex", "d_hex"])["TOTAL_TRIPS"].sum()
    wd = agg(flows).rename("trips_wd")
    am = agg(flows[flows["peak"] == "am"]).rename("trips_am")
    pm = agg(flows[flows["peak"] == "pm"]).rename("trips_pm")
    mat = pd.concat([wd, am, pm], axis=1).fillna(0).reset_index()
    mat.columns = ["origin_hex8", "dest_hex8", "trips_wd", "trips_am", "trips_pm"]
    mat.to_parquet(OD / "hex8_od_matrix.parquet", index=False)
    print(f"  od matrix: {len(mat):,} hex8->hex8 pairs")

    # --- per-hex8 features (restricted to hex8 universe) ---
    uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")["hex8_id"]
    self_mask = mat["origin_hex8"] == mat["dest_hex8"]
    out = mat.groupby("origin_hex8").agg(
        od_out_trips=("trips_wd", "sum"),
        od_out_am=("trips_am", "sum"),
        od_out_pm=("trips_pm", "sum"),
        od_n_dest_hex=("dest_hex8", "nunique"),
    )
    inn = mat.groupby("dest_hex8").agg(
        od_in_trips=("trips_wd", "sum"),
        od_in_am=("trips_am", "sum"),
        od_in_pm=("trips_pm", "sum"),
    )
    selft = mat[self_mask].groupby("origin_hex8")["trips_wd"].sum().rename("od_self_trips")

    # destination entropy (outbound diversity), excluding self
    ext = mat[~self_mask]
    def entropy(g):
        p = g.values.astype(float); s = p.sum()
        if s <= 0: return 0.0
        p = p / s
        return float(-(p * np.log(p + 1e-12)).sum())
    ent = ext.groupby("origin_hex8")["trips_wd"].apply(entropy).rename("od_dest_entropy")

    f = pd.DataFrame({"hex8_id": uni}).set_index("hex8_id")
    for s in [out, inn, selft, ent]:
        f = f.join(s)
    f = f.fillna(0.0)
    f["od_throughput"] = f["od_out_trips"] + f["od_in_trips"]
    f["od_net_flow"] = f["od_in_trips"] - f["od_out_trips"]
    denom = (f["od_out_trips"] + f["od_self_trips"]).replace(0, np.nan)
    f["od_self_containment"] = (f["od_self_trips"] / denom).fillna(0.0)
    # AM origin-heavy vs PM (commuter residential signal): >0 => more AM departures
    f["od_am_pm_out_ratio"] = (f["od_out_am"] - f["od_out_pm"]) / (f["od_out_am"] + f["od_out_pm"]).replace(0, np.nan)
    f["od_am_pm_out_ratio"] = f["od_am_pm_out_ratio"].fillna(0.0)
    for c in f.columns:
        f[c] = f[c].round(4)
    f = f.reset_index()
    f.to_parquet(ROOT / "hex/hex8_od_features.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "month": "2026-04", "trip_basis": "monthly_weekday_totals",
        "matrix_pairs": int(len(mat)),
        "hex8_with_od": int((f["od_throughput"] > 0).sum()),
        "total_trips_mapped_wd": float(mat["trips_wd"].sum()),
        "feature_cols": [c for c in f.columns if c != "hex8_id"],
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/od_features_report.json", "w"), indent=2)
    print("\n" + json.dumps(rep, indent=2))
    print("\nTop hex8 by throughput:")
    print(f.nlargest(6, "od_throughput")[["hex8_id","od_out_trips","od_in_trips","od_self_containment","od_dest_entropy"]].to_string(index=False))


if __name__ == "__main__":
    main()

"""
Plexis SGP v4 — Stage 25: LTA Datamall passenger volume (time-of-day taps).

Pulls /PV/Bus and /PV/Train from LTA Datamall, downloads + parses the CSVs,
sums tap-in/tap-out by stop/station × time-of-day window, and aggregates
to hex9 / hex8 / subzone via stop/station coords.

Time windows match Stage 23 (GTFS):
  am:     hours 7-8
  midday: 11-13
  pm:     17-18
  night:  22-23, 0-3
  offpeak (rest)

For each hex / scale we produce:
  bus_taps_in_<window>, bus_taps_out_<window>
  mrt_taps_in_<window>, mrt_taps_out_<window>
  bus_taps_in_total, bus_taps_out_total
  mrt_taps_in_total, mrt_taps_out_total

= 4 windows × 4 (bus/mrt × in/out) + 4 totals = 20 cols.

Outputs:
  hex/hex9_lta_pv.parquet
  hex/hex8_lta_pv.parquet
  hex/subzone_lta_pv.parquet
"""
import io, json, os, time, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import h3
import requests

ROOT = Path(__file__).parent

LTA_KEY = os.environ.get("LTA_KEY", "")
H = {"AccountKey": LTA_KEY, "accept": "application/json"}

# Most recent month (LTA publishes ~2 months back; try Feb→Jan→Dec)
TRY_MONTHS = ["202602","202601","202512","202511","202510"]

WINDOWS = {
    "am":     (7, 9),
    "midday": (11, 14),
    "pm":     (17, 19),
    "night":  (22, 28),  # 22 wraps to 04
}


def _resolve_data_root():
    if os.environ.get("PLEXIS_DATA_ROOT"):
        return Path(os.environ["PLEXIS_DATA_ROOT"])
    for c in [Path("/home/azureuser/digital-atlas-sgp/data"), ROOT.parent / "data"]:
        if c.exists(): return c
    raise FileNotFoundError("data root not found")


DATA = _resolve_data_root()
CACHE = ROOT / "cache/lta_pv"
CACHE.mkdir(parents=True, exist_ok=True)


def fetch_pv(kind):
    """Get the PV/Bus or PV/Train CSV. Returns DataFrame or None."""
    cache_csv = CACHE / f"pv_{kind}.csv"
    if cache_csv.exists():
        print(f"  cache hit: {cache_csv}")
        return pd.read_csv(cache_csv)
    for date in TRY_MONTHS:
        endpoint = f"PV/{kind}"
        url = f"https://datamall2.mytransport.sg/ltaodataservice/{endpoint}"
        print(f"  trying date={date}...")
        r = requests.get(url, headers=H, params={"Date": date}, timeout=20)
        if r.status_code != 200: continue
        v = r.json().get("value", [])
        if not v: continue
        link = v[0].get("Link")
        if not link: continue
        # Download zip
        z = requests.get(link, timeout=60)
        if z.status_code != 200: continue
        try:
            zf = zipfile.ZipFile(io.BytesIO(z.content))
            csv_name = next(n for n in zf.namelist() if n.endswith(".csv"))
            df = pd.read_csv(zf.open(csv_name))
            print(f"  fetched {kind} {date}: {len(df):,} rows")
            df.to_csv(cache_csv, index=False)
            return df
        except Exception as e:
            print(f"  parse failed: {e}")
            continue
    return None


def window_for_hour(h):
    h = int(h)
    for name, (lo, hi) in WINDOWS.items():
        # night wraps
        if name == "night":
            if h >= lo or h < (hi - 24): return name
        else:
            if lo <= h < hi: return name
    return "offpeak"


def aggregate_pv(df, code_col):
    """Sum tap volumes by code × window × in/out for WEEKDAY only."""
    df = df[df["DAY_TYPE"] == "WEEKDAY"].copy()
    df = df.dropna(subset=["TIME_PER_HOUR", code_col, "TOTAL_TAP_IN_VOLUME", "TOTAL_TAP_OUT_VOLUME"])
    df["window"] = df["TIME_PER_HOUR"].apply(window_for_hour)
    grp = df.groupby([code_col, "window"]).agg(
        in_v=("TOTAL_TAP_IN_VOLUME", "sum"),
        out_v=("TOTAL_TAP_OUT_VOLUME", "sum"),
    ).reset_index()
    return grp


def main():
    t0 = time.time()
    print("Fetching PV/Bus...")
    pv_bus = fetch_pv("Bus")
    print("Fetching PV/Train...")
    pv_train = fetch_pv("Train")

    # === BUS aggregation ===
    if pv_bus is not None:
        # Schema: YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, PT_CODE, TOTAL_TAP_IN_VOLUME, TOTAL_TAP_OUT_VOLUME
        agg = aggregate_pv(pv_bus, "PT_CODE")
        # Coord lookup
        bus = gpd.read_file(DATA / "transit_updated/bus_stops_mar2026.geojson")
        # PT_CODE in PV is int, BUS_STOP_N in geojson is zero-padded 5-digit string. Normalize both.
        bus["BUS_STOP_N"] = bus["BUS_STOP_N"].astype(str).str.lstrip("0")
        agg["PT_CODE"] = agg["PT_CODE"].astype(int).astype(str)
        m = agg.merge(bus[["BUS_STOP_N", "geometry"]], left_on="PT_CODE", right_on="BUS_STOP_N", how="inner")
        # Convert to lat/lng
        m["lat"] = m["geometry"].apply(lambda p: p.y if p else np.nan)
        m["lng"] = m["geometry"].apply(lambda p: p.x if p else np.nan)
        m = m.dropna(subset=["lat","lng"])
        m["hex9_id"] = [h3.latlng_to_cell(la, lo, 9) for la, lo in zip(m["lat"], m["lng"])]
        bus_hex = m.groupby(["hex9_id","window"]).agg(in_v=("in_v","sum"), out_v=("out_v","sum")).reset_index()
        # Pivot wide
        bus_wide = bus_hex.pivot(index="hex9_id", columns="window", values=["in_v","out_v"]).reset_index()
        bus_wide.columns = ["hex9_id"] + [f"bus_taps_{flow}_{w}" for flow, w in bus_wide.columns[1:]]
        bus_wide = bus_wide.rename(columns=lambda c: c.replace("in_v_","in_").replace("out_v_","out_"))
        print(f"  bus_hex stops: {m['PT_CODE'].nunique()}, hexes: {bus_wide['hex9_id'].nunique()}")
    else:
        print("  bus PV unavailable; skipping")
        bus_wide = pd.DataFrame({"hex9_id": []})

    # === TRAIN aggregation === (use mrt_lrt_stations name → coord)
    if pv_train is not None:
        # PT_CODE for trains looks like "NS1", "EW2", etc. We need coords.
        # Try mrt_station_names.geojson which has station-code attributes
        mrt = gpd.read_file(DATA / "transit/mrt_station_names.geojson")
        # ATTACHEMEN holds station_code in many tagged stations
        mrt = mrt[mrt.geometry.notna()].copy()
        mrt["centroid"] = mrt.geometry.centroid
        # Try various code columns
        code_col = None
        for c in ["STN_NO_DE","STATION_CODE","ATTACHEMEN","STN_NAM_DE"]:
            if c in mrt.columns:
                code_col = c
                break
        if code_col:
            mrt["pt_code"] = mrt[code_col].astype(str).str.strip().str.upper()
            mrt["lat"] = mrt["centroid"].apply(lambda p: p.y if p else np.nan)
            mrt["lng"] = mrt["centroid"].apply(lambda p: p.x if p else np.nan)
            mrt_codes = mrt[["pt_code","lat","lng"]].dropna().drop_duplicates("pt_code")
        else:
            mrt_codes = pd.DataFrame()

        agg = aggregate_pv(pv_train, "PT_CODE")
        agg["PT_CODE"] = agg["PT_CODE"].astype(str).str.strip().str.upper()

        # Stations like "NS1/EW24/CC22" (interchanges). Split on / and match each.
        rows = []
        for _, r in agg.iterrows():
            for code in str(r["PT_CODE"]).split("/"):
                rows.append({"pt_code": code.strip(), "window": r["window"],
                             "in_v": r["in_v"]/len(r["PT_CODE"].split("/")),  # split evenly
                             "out_v": r["out_v"]/len(r["PT_CODE"].split("/"))})
        agg_split = pd.DataFrame(rows)
        if len(mrt_codes):
            m = agg_split.merge(mrt_codes, on="pt_code", how="inner")
            m["hex9_id"] = [h3.latlng_to_cell(la, lo, 9) for la, lo in zip(m["lat"], m["lng"])]
            mrt_hex = m.groupby(["hex9_id","window"]).agg(in_v=("in_v","sum"), out_v=("out_v","sum")).reset_index()
            mrt_wide = mrt_hex.pivot(index="hex9_id", columns="window", values=["in_v","out_v"]).reset_index()
            mrt_wide.columns = ["hex9_id"] + [f"mrt_taps_{flow}_{w}" for flow, w in mrt_wide.columns[1:]]
            mrt_wide = mrt_wide.rename(columns=lambda c: c.replace("in_v_","in_").replace("out_v_","out_"))
            print(f"  mrt matched: {m['pt_code'].nunique()} of {agg_split['pt_code'].nunique()} codes; hexes: {mrt_wide['hex9_id'].nunique()}")
        else:
            mrt_wide = pd.DataFrame({"hex9_id": []})
    else:
        print("  train PV unavailable; skipping")
        mrt_wide = pd.DataFrame({"hex9_id": []})

    # === Merge into hex universe ===
    h9_uni = pd.read_parquet(ROOT / "hex/hex9_universe.parquet")
    out = h9_uni[["hex9_id"]].copy()
    if not bus_wide.empty:
        out = out.merge(bus_wide, on="hex9_id", how="left")
    if not mrt_wide.empty:
        out = out.merge(mrt_wide, on="hex9_id", how="left")

    int_cols = [c for c in out.columns if c != "hex9_id"]
    for c in int_cols:
        out[c] = out[c].fillna(0).round().astype(int)

    # Add totals
    for prefix in ("bus_taps_in_","bus_taps_out_","mrt_taps_in_","mrt_taps_out_"):
        cols = [c for c in out.columns if c.startswith(prefix)]
        if cols: out[f"{prefix}total"] = out[cols].sum(axis=1)

    out.to_parquet(ROOT / "hex/hex9_lta_pv.parquet", index=False)
    print(f"\n  hex9_lta_pv: {out.shape}")

    # === Aggregate to hex8 + subzone ===
    h9wp = out.merge(h9_uni[["hex9_id","parent_hex8","parent_subzone"]], on="hex9_id")
    sum_cols = [c for c in out.columns if c != "hex9_id"]

    h8_uni = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    h8_agg = h9wp.groupby("parent_hex8")[sum_cols].sum().reset_index().rename(columns={"parent_hex8":"hex8_id"})
    h8_out = h8_uni.merge(h8_agg, on="hex8_id", how="left")
    for c in sum_cols: h8_out[c] = h8_out[c].fillna(0).astype(int)
    h8_out.to_parquet(ROOT / "hex/hex8_lta_pv.parquet", index=False)
    print(f"  hex8_lta_pv: {h8_out.shape}")

    sz_lu = pd.read_parquet(ROOT / "hex/subzone_land_use.parquet")[["subzone_c"]].drop_duplicates()
    sz_agg = h9wp.groupby("parent_subzone")[sum_cols].sum().reset_index().rename(columns={"parent_subzone":"subzone_c"})
    sz_out = sz_lu.merge(sz_agg, on="subzone_c", how="left")
    for c in sum_cols: sz_out[c] = sz_out[c].fillna(0).astype(int)
    sz_out.to_parquet(ROOT / "hex/subzone_lta_pv.parquet", index=False)
    print(f"  subzone_lta_pv: {sz_out.shape}")

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "wall_clock_s": round(time.time() - t0, 2),
        "input_pv_bus_rows": int(len(pv_bus)) if pv_bus is not None else 0,
        "input_pv_train_rows": int(len(pv_train)) if pv_train is not None else 0,
        "shapes": {"hex9": list(out.shape), "hex8": list(h8_out.shape), "subzone": list(sz_out.shape)},
        "totals": {c: int(out[c].sum()) for c in out.columns if c.endswith("_total")},
    }
    with open(ROOT / "hex/lta_pv_report.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n{json.dumps(summary, indent=2)}")


if __name__ == "__main__":
    main()

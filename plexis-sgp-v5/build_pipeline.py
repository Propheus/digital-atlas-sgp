"""
Plexis SGP v4 — S9 Future supply pipeline (pipe_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S9 — AMENDED 2026-06-10 after source audit:
  - HDB "Public Housing Under-Construction" geojson on data.gov.sg is STALE
    (2018 vintage) — dropped.
  - Project-level BTO locations are no longer openly published; only national
    totals exist (FY2024: 31,452 units awarded) — recorded as context.
What ships:
  pipe_new_mrt_within_800m  future rail station within 800 m of hex activity
                            origin. Future = MP2019 rail-station polygons
                            (257) with no existing Mar-2026 station within
                            400 m of their centroid (CRL, JRL remainder,
                            TEL/DTL extensions — committed lines as of MP19).
  pipe_mrt_name             nearest such future station name
  pipe_mrt_dist_m           distance to it
  pipe_dev_capacity_res     FAR headroom x residential zoning share:
                            (avg_gpr - est_built_far, clipped >= 0) x
                            lu_residential_pct. A v1 used footprint-share
                            (zoned minus ground coverage) and inverted the
                            archetypes — HDB towers cover little GROUND, so
                            built-out Toa Payoh read as 'capacity' while
                            mostly-built Tengah read as none. FAR headroom
                            ranks growth areas correctly (Matilda 0.51,
                            Bidadari 0.34, Toa Payoh Central 0.00).
  pipe_dev_capacity_com     same headroom x (commercial + mixed) share

Output: hex/hex8_pipeline.parquet + hex/pipeline_report.json
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent
HEX8_M2 = 737_327.6
FUTURE_MATCH_M = 400.0
NEAR_M = 800.0


def centroids(path, name_key):
    d = json.load(open(path))
    rows = []
    for f in d["features"]:
        geom = shapely.geometry.shape(f["geometry"])
        c = geom.centroid
        rows.append((f["properties"].get(name_key), c.x, c.y))
    return pd.DataFrame(rows, columns=["name", "lng", "lat"])


def main():
    t0 = time.time()
    tr = Transformer.from_crs(4326, 3414, always_xy=True)

    mp19 = centroids(ROOT.parent / "data/external/d_8d886e3a83934d7447acdf5bc6959999.geojson",
                     "NAME")
    exist = centroids(ROOT.parent / "data/transit_updated/train_stations_mar2026.geojson",
                      "STN_NAM_DE")
    mxy = np.column_stack(tr.transform(mp19["lng"], mp19["lat"]))
    exy = np.column_stack(tr.transform(exist["lng"], exist["lat"]))
    d_min, _ = cKDTree(exy).query(mxy)
    mp19["name"] = mp19["name"].fillna("UNNAMED")
    future = mp19[d_min > FUTURE_MATCH_M].reset_index(drop=True)
    print(f"MP19 stations: {len(mp19)}, existing: {len(exist)}, "
          f"future: {len(future)}")
    print("  future names sample:", ", ".join(future["name"].head(12)))

    # hex8 activity origins
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["hex8_id", "latitude", "longitude"])
    act = pl.groupby("hex8_id")[["longitude", "latitude"]].mean()
    h8 = h8.set_index("hex8_id")
    h8["o_lng"] = act["longitude"].reindex(h8.index).fillna(h8["lng"])
    h8["o_lat"] = act["latitude"].reindex(h8.index).fillna(h8["lat"])
    h8 = h8.reset_index()
    oxy = np.column_stack(tr.transform(h8["o_lng"], h8["o_lat"]))
    fxy = np.column_stack(tr.transform(future["lng"], future["lat"]))
    fd, fk = cKDTree(fxy).query(oxy)
    h8["pipe_mrt_dist_m"] = fd.round(1)
    h8["pipe_mrt_name"] = future["name"].to_numpy()[fk]
    h8["pipe_new_mrt_within_800m"] = fd <= NEAR_M

    # development capacity = FAR headroom x zoned share
    m = pd.read_parquet(ROOT / "hex/hex8_all_features.parquet",
                        columns=["hex8_id", "lu_residential_pct",
                                 "lu_commercial_pct", "lu_mixed_use_pct",
                                 "avg_gpr", "est_built_far"])
    headroom = (m["avg_gpr"].fillna(0) - m["est_built_far"].fillna(0)).clip(lower=0)
    m["pipe_dev_capacity_res"] = (headroom
                                  * m["lu_residential_pct"].fillna(0)).round(4)
    com = m["lu_commercial_pct"].fillna(0) + m["lu_mixed_use_pct"].fillna(0)
    m["pipe_dev_capacity_com"] = (headroom * com).round(4)

    out = h8[["hex8_id", "pipe_new_mrt_within_800m", "pipe_mrt_name",
              "pipe_mrt_dist_m"]].merge(
        m[["hex8_id", "pipe_dev_capacity_res", "pipe_dev_capacity_com"]],
        on="hex8_id", how="left")
    out.to_parquet(ROOT / "hex/hex8_pipeline.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S9 (amended scope)",
        "future_stations": int(len(future)),
        "hex_near_future_mrt": int(out["pipe_new_mrt_within_800m"].sum()),
        "national_bto_context": "FY2024 awarded 31,452 units (no open locations)",
        "dropped": "HDB under-construction geojson (2018-stale)",
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/pipeline_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()

"""
Plexis SGP v5 — S10 Context pack (heritage / carparks / health / daily-needs /
growth) per hex8.

Integrates the externally-sourced nous feature pack (build_nous_features.py)
as a first-class atlas layer, so the live hex8 view carries these columns.

  cons_bldg_count          URA conserved buildings in hex (MP19 SDCP layer)
  cons_cluster_flag        >= 20 conserved buildings (shophouse cluster)
  carpark_count_hdb        HDB carparks in hex
  carpark_capacity_lots    summed car lots (live-availability total_lots, C)
  polyclinic_count         polyclinics in hex
  dist_polyclinic_m        centroid distance to nearest polyclinic
  wet_market_count         NEA market & food centres flagged as markets
  dist_wet_market_m        distance to nearest wet market
  petrol_station_count     OSM fuel stations in hex
  dist_petrol_m            distance to nearest station
  coworking_count          coworking venues (places name-match)
  condo_project_count      URA strata projects in hex
  condo_txn_units          units transacted (volume weight, NOT stock)
  female_pop_share         subzone-broadcast (SingStat 2025) — NaN if no match
  bto_uc_units_town        FY-latest under-construction units of the hex's
                           HDB town (town-broadcast; 0 = no HDB town match)
  bto_pipeline_est         town units allocated within town by FAR headroom
                           (pipe_dev_capacity_res share) — modeled, labeled

Output: hex/hex8_context_pack.parquet + hex/context_pack_report.json
"""
import json
import re
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent
PACK = ROOT / "nous_export"

# HDB town -> URA planning area (broadcast key). Identity unless noted.
TOWN_TO_PA = {
    "Kallang/Whampoa": "KALLANG", "Central Area": "DOWNTOWN CORE",
    "Choa Chu Kang": "CHOA CHU KANG", "Ang Mo Kio": "ANG MO KIO",
}


def to3414(lng, lat):
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    x, y = tr.transform(np.asarray(lng), np.asarray(lat))
    return np.column_stack([x, y])


def count_and_dist(h8, oxy, pts_lng, pts_lat, weights=None):
    """points -> (count per hex, weight sum per hex, centroid dist to nearest)"""
    hexes = pd.Series([h3.latlng_to_cell(la, lo, 8)
                       for la, lo in zip(pts_lat, pts_lng)])
    cnt = hexes.value_counts()
    wsum = None
    if weights is not None:
        wsum = pd.Series(np.asarray(weights)).groupby(hexes).sum()
    pxy = to3414(pts_lng, pts_lat)
    d, _ = cKDTree(pxy).query(oxy)
    return cnt, wsum, d


def main():
    t0 = time.time()
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    oxy = to3414(h8["lng"], h8["lat"])
    out = h8[["hex8_id"]].copy()
    idx = out.set_index("hex8_id").index

    # conservation (already hex-keyed)
    sh = pd.read_parquet(PACK / "hex8_shophouse_density.parquet").set_index("hex8_id")
    out["cons_bldg_count"] = sh["conserved_bldg_count"].reindex(idx).fillna(0).to_numpy()
    out["cons_cluster_flag"] = sh["is_conservation_cluster"].reindex(idx).fillna(False).to_numpy()

    # carparks
    cp = pd.read_parquet(PACK / "carparks.parquet")
    cnt, lots, _ = count_and_dist(h8, oxy, cp["lon"], cp["lat"],
                                  cp["total_lots"].fillna(0))
    out["carpark_count_hdb"] = cnt.reindex(idx).fillna(0).to_numpy()
    out["carpark_capacity_lots"] = lots.reindex(idx).fillna(0).to_numpy()

    # polyclinics
    pc = pd.read_csv(PACK / "polyclinics.csv")
    cnt, _, d = count_and_dist(h8, oxy, pc["lon"], pc["lat"])
    out["polyclinic_count"] = cnt.reindex(idx).fillna(0).to_numpy()
    out["dist_polyclinic_m"] = d.round(1)

    # wet markets (markets only)
    wm = pd.read_csv(PACK / "wet_markets.csv")
    wm = wm[wm["is_wet_market"]]
    cnt, _, d = count_and_dist(h8, oxy, wm["lon"], wm["lat"])
    out["wet_market_count"] = cnt.reindex(idx).fillna(0).to_numpy()
    out["dist_wet_market_m"] = d.round(1)

    # petrol
    pf = pd.read_csv(PACK / "petrol_stations.csv")
    cnt, _, d = count_and_dist(h8, oxy, pf["lon"], pf["lat"])
    out["petrol_station_count"] = cnt.reindex(idx).fillna(0).to_numpy()
    out["dist_petrol_m"] = d.round(1)

    # coworking
    cw = pd.read_csv(PACK / "coworking_spaces.csv")
    cnt, _, _ = count_and_dist(h8, oxy, cw["lon"], cw["lat"])
    out["coworking_count"] = cnt.reindex(idx).fillna(0).to_numpy()

    # condos
    cd = pd.read_parquet(PACK / "condo_projects.parquet")
    cnt, units, _ = count_and_dist(h8, oxy, cd["lon"], cd["lat"], cd["units_sold"])
    out["condo_project_count"] = cnt.reindex(idx).fillna(0).to_numpy()
    out["condo_txn_units"] = units.reindex(idx).fillna(0).to_numpy()

    # female pop share (subzone broadcast)
    fs = pd.read_csv(PACK / "female_pop_share.csv")
    fs["key"] = fs["subzone"].str.upper().str.strip()
    h8n = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    key = h8n["parent_subzone_name"].str.upper().str.strip()
    out["female_pop_share"] = key.map(fs.set_index("key")["female_pop_share"]).round(4)

    # BTO pipeline (town broadcast + headroom-weighted allocation)
    ct = pd.read_csv(PACK / "hdb_completion_by_town.csv")
    fy = ct["financial_year"].max()
    uc = ct[(ct["financial_year"] == fy) & (ct["status"] == "Under Construction")] \
        .groupby("town_or_estate")["no_of_units"].sum()
    uc.index = [TOWN_TO_PA.get(t, t.upper()) for t in uc.index]
    pa = h8n["parent_pa"].str.upper()
    out["bto_uc_units_town"] = pa.map(uc).fillna(0).to_numpy()
    cap = pd.read_parquet(ROOT / "hex/hex8_pipeline.parquet") \
        .set_index("hex8_id")["pipe_dev_capacity_res"].reindex(idx).fillna(0).to_numpy()
    alloc = np.zeros(len(out))
    df = pd.DataFrame({"pa": pa.to_numpy(), "cap": cap, "units": out["bto_uc_units_town"]})
    for p, sub in df.groupby("pa"):
        tot = sub["cap"].sum()
        if sub["units"].iloc[0] > 0 and tot > 0:
            alloc[sub.index] = sub["units"].iloc[0] * sub["cap"] / tot
    out["bto_pipeline_est"] = alloc.round(1)

    for c in out.columns:
        if out[c].dtype == float and c != "female_pop_share":
            out[c] = out[c].round(2)
    out.to_parquet(ROOT / "hex/hex8_context_pack.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "S10 context pack (nous external sources integrated)",
        "sources": "build_nous_features.py pack (see nous_export/README.md)",
        "fy_pipeline": int(fy),
        "national": {
            "conserved_bldgs": float(out["cons_bldg_count"].sum()),
            "carpark_lots": float(out["carpark_capacity_lots"].sum()),
            "wet_markets": float(out["wet_market_count"].sum()),
            "petrol": float(out["petrol_station_count"].sum()),
            "coworking": float(out["coworking_count"].sum()),
            "condo_projects": float(out["condo_project_count"].sum()),
            "bto_alloc_units": float(out["bto_pipeline_est"].sum()),
        },
        "female_share_match": float(out["female_pop_share"].notna().mean()),
        "cols": [c for c in out.columns if c != "hex8_id"],
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/context_pack_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()

"""
Plexis SGP v4 — S4 Business formation & churn (biz_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S4.

Geocoding: NOT via the OneMap API — live API now requires an auth token and
throttles unauthenticated calls to ~18/min (and returns HTTP-200 error bodies
that look like not-found). Instead uses the offline OneMap dump
`xkjyeah/singapore-postal-codes` (141,726 building records, updated 2026-04)
downloaded to data/external/sg_postal_buildings.json. SG postal codes are
building-precise, so postal -> lat/lng -> H3 is exact.

Per hex8 from 2.07M ACRA entities:
  biz_live_count        entities with status 'Registered'
  biz_density_per_km2   live per km2
  biz_formation_5y      entities issued in the last 5 years (any status)
  biz_dead_share        deregistered+other-dead / total ever (LIFETIME — no
                        cessation date exists in the file, documented limit)
  biz_recent_dead_share dead share among the 2018+ issue cohort
  biz_median_age_yrs    median age of LIVE entities
  biz_company_share     'Local Company' share of live (formality mix)
  biz_live_robust       live count with per-postal contribution capped at 100
                        — registered-agent buildings (Paya Lebar Square 19K,
                        the ACRA building 14K, SBF Center 8.7K) are paper
                        addresses, not local business activity
  biz_per_address       live entities per unique postal (high = corporate-
                        secretary building — a signal in its own right)

Output: hex/hex8_acra_biz.parquet + hex/acra_biz_report.json
"""
import json
import time
from pathlib import Path

import h3
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
TODAY = pd.Timestamp("2026-06-10")
HEX8_KM2 = 0.737


def main():
    t0 = time.time()
    print("Loading postal dump...")
    dump = json.load(open(ROOT.parent / "data/external/sg_postal_buildings.json"))
    pc = pd.DataFrame([(d["POSTAL"], float(d["LATITUDE"]), float(d["LONGITUDE"]))
                       for d in dump], columns=["postal", "lat", "lng"])
    pc = pc[pc["postal"].str.match(r"^\d{6}$")].groupby("postal").first()
    print(f"  {len(pc):,} unique postals")

    print("Loading ACRA...")
    a = pd.read_csv(ROOT.parent / "data/business/acra_entities.csv",
                    usecols=["uen_status_desc", "entity_type_desc",
                             "uen_issue_date", "reg_postal_code"],
                    dtype=str)
    a["postal"] = a["reg_postal_code"].str.zfill(6)
    a = a[a["postal"].str.match(r"^\d{6}$", na=False)]
    a = a.join(pc, on="postal")
    matched = a["lat"].notna()
    cover = matched.mean()
    print(f"  geocoded {matched.sum():,}/{len(a):,} ({cover:.2%})")
    a = a[matched].copy()

    a["issue"] = pd.to_datetime(a["uen_issue_date"], errors="coerce")
    a["live"] = a["uen_status_desc"] == "Registered"
    a["recent"] = a["issue"] >= TODAY - pd.DateOffset(years=5)
    a["cohort18"] = a["issue"] >= "2018-01-01"
    a["age_yrs"] = (TODAY - a["issue"]).dt.days / 365.25
    a["is_company"] = a["entity_type_desc"] == "Local Company"

    # postal -> hex8 (vectorized over unique coords)
    upc = a[["postal", "lat", "lng"]].drop_duplicates("postal")
    upc["hex8_id"] = [h3.latlng_to_cell(la, ln, 8)
                      for la, ln in zip(upc["lat"], upc["lng"])]
    a = a.merge(upc[["postal", "hex8_id"]], on="postal")

    POSTAL_CAP = 100
    per_postal = a[a["live"]].groupby(["hex8_id", "postal"]).size()
    robust = per_postal.clip(upper=POSTAL_CAP).groupby("hex8_id").sum()
    per_addr = per_postal.groupby("hex8_id").mean()

    g = a.groupby("hex8_id")
    out = pd.DataFrame({
        "biz_live_robust": robust,
        "biz_per_address": per_addr,
        "biz_live_count": g["live"].sum(),
        "biz_total_ever": g.size(),
        "biz_formation_5y": g["recent"].sum(),
        "biz_dead_share": 1 - g["live"].mean(),
        "biz_recent_dead_share": 1 - a[a["cohort18"]].groupby("hex8_id")["live"].mean(),
        "biz_median_age_yrs": a[a["live"]].groupby("hex8_id")["age_yrs"].median(),
        "biz_company_share": a[a["live"]].groupby("hex8_id")["is_company"].mean(),
    }).reset_index()
    out["biz_density_per_km2"] = (out["biz_live_count"] / HEX8_KM2).round(1)

    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")[["hex8_id"]]
    in_univ = out["hex8_id"].isin(set(h8["hex8_id"]))
    print(f"  hex8 cells with entities: {len(out):,} ({in_univ.sum()} in universe)")
    out = h8.merge(out, on="hex8_id", how="left")
    cnt_cols = ["biz_live_count", "biz_total_ever", "biz_formation_5y",
                "biz_density_per_km2", "biz_live_robust"]
    out[cnt_cols] = out[cnt_cols].fillna(0)
    for c in out.columns:
        if out[c].dtype == float:
            out[c] = out[c].round(4)
    out.to_parquet(ROOT / "hex/hex8_acra_biz.parquet", index=False)

    top = out.nlargest(10, "biz_live_count")
    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S4",
        "geocode_source": "xkjyeah/singapore-postal-codes (OneMap dump 2026-04)",
        "geocode_coverage": round(float(cover), 4),
        "entities_geocoded": int(matched.sum()),
        "national_live": int(a["live"].sum()),
        "national_dead_share": round(float(1 - a["live"].mean()), 4),
        "top_hex_share_raw": round(float(top["biz_live_count"].max()
                                         / a["live"].sum()), 4),
        "top_hex_share_robust": round(float(out["biz_live_robust"].max()
                                            / out["biz_live_robust"].sum()), 4),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/acra_biz_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()

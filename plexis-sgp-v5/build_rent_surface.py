"""
Plexis SGP v4 — S8 Rent surface (rent_*) per hex8.

Spec: SITE_SELECTION_METRICS.md §S8 — AMENDED 2026-06-10: the URA Data
Service has NO commercial (office/retail) rental endpoints (probed:
PMI_Comm_*, all "Invalid service"), and the quarterly office/retail median
tables are URA-SPACE/Realis-only. What IS available with the access key:
PMI_Resi_Rental_Median — 917 private-resi projects with SVY21 coords and
quarterly median $psf/mo. Shipped layer = RESIDENTIAL rent surface:
a real spatial price signal (catchment purchasing power, occupancy-cost
proxy), honestly labeled. Commercial rent stays an open Tier-2 gap.

  rent_resi_psf_med   median of project medians, last 4 available quarters,
                      IDW (k=5, p=2, max 2.5 km) onto hex8 activity points
  rent_resi_n_obs     supporting project count within 2.5 km
  rent_resolution     'local' (nearest project <= 800 m), 'idw' (<= 2.5 km),
                      'none'
  roi_cap_per_rent_*  S1 capture / rent — rank heuristic for cafe,
                      supermarket, restaurant, shopping_retail + total

Source: data/external/ura_rental_median.json (fetched 2026-06-10).
Output: hex/hex8_rent_surface.parquet + hex/rent_surface_report.json
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).parent
K_IDW, P_IDW = 5, 2.0
MAX_D = 2500.0
LOCAL_D = 800.0
ROI_CATS = ["cafe_coffee", "supermarket", "restaurant", "shopping_retail"]


def main():
    t0 = time.time()
    raw = json.load(open(ROOT.parent / "data/external/ura_rental_median.json"))
    rows = []
    for proj in raw["Result"]:
        med = proj.get("rentalMedian") or []
        if not med or "x" not in proj:
            continue
        qs = sorted(med, key=lambda m: m["refPeriod"])[-4:]   # last 4 quarters
        rows.append({
            "project": proj["project"],
            "x": float(proj["x"]), "y": float(proj["y"]),
            "rent_psf": float(np.median([m["median"] for m in qs])),
            "last_q": qs[-1]["refPeriod"],
            "district": qs[-1].get("district"),
        })
    pr = pd.DataFrame(rows)
    print(f"projects with rent: {len(pr)} | latest quarter span: "
          f"{pr['last_q'].min()}..{pr['last_q'].max()}")

    # hex8 activity origins (same definition as S2) — rent at the likely site
    h8 = pd.read_parquet(ROOT / "hex/hex8_universe.parquet")
    pl = pd.read_parquet(ROOT / "places/sgp_places_final.parquet",
                         columns=["hex8_id", "latitude", "longitude"])
    act = pl.groupby("hex8_id")[["longitude", "latitude"]].mean()
    h8 = h8.set_index("hex8_id")
    h8["o_lng"] = act["longitude"].reindex(h8.index).fillna(h8["lng"])
    h8["o_lat"] = act["latitude"].reindex(h8.index).fillna(h8["lat"])
    h8 = h8.reset_index()
    tr = Transformer.from_crs(4326, 3414, always_xy=True)
    ox, oy = tr.transform(h8["o_lng"].to_numpy(), h8["o_lat"].to_numpy())
    oxy = np.column_stack([ox, oy])

    tree = cKDTree(pr[["x", "y"]].to_numpy())
    d, k = tree.query(oxy, k=K_IDW)
    w = 1.0 / np.maximum(d, 50.0) ** P_IDW
    w[d > MAX_D] = 0.0
    vals = pr["rent_psf"].to_numpy()[k]
    wsum = w.sum(axis=1)
    rent = np.where(wsum > 0, (w * vals).sum(axis=1) / np.maximum(wsum, 1e-12),
                    np.nan)
    n_obs = (d <= MAX_D).sum(axis=1)
    res = np.where(d[:, 0] <= LOCAL_D, "local",
                   np.where(wsum > 0, "idw", "none"))

    out = pd.DataFrame({
        "hex8_id": h8["hex8_id"],
        "rent_resi_psf_med": np.round(rent, 3),
        "rent_resi_n_obs": n_obs,
        "rent_resolution": res,
    })
    cap = pd.read_parquet(ROOT / "hex/hex8_huff_capture.parquet")
    out = out.merge(cap[["hex8_id", "cap_total"]
                        + [f"cap_{c}" for c in ROI_CATS]], on="hex8_id", how="left")
    for c in ROI_CATS + ["total"]:
        col = f"cap_{c}"
        out[f"roi_cap_per_rent_{c}"] = (out[col]
                                        / out["rent_resi_psf_med"]).round(4)
    out = out.drop(columns=["cap_total"] + [f"cap_{c}" for c in ROI_CATS])
    out.to_parquet(ROOT / "hex/hex8_rent_surface.parquet", index=False)

    rep = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "spec": "SITE_SELECTION_METRICS.md S8 (amended: resi-only)",
        "projects": int(len(pr)),
        "coverage": {r: int((res == r).sum()) for r in ["local", "idw", "none"]},
        "rent_range_psf": [float(np.nanmin(rent)), float(np.nanmax(rent))],
        "commercial_rent": "NOT AVAILABLE via URA API/data.gov.sg — Realis only",
        "wall_clock_s": round(time.time() - t0, 2),
    }
    json.dump(rep, open(ROOT / "hex/rent_surface_report.json", "w"), indent=2)
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()

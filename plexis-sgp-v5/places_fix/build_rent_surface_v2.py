"""
Plexis SGP v5.7 — residential rent surface at hex9 + hex8 (extends the hex8-only S8).
URA PMI_Resi_Rental_Median (913 private-resi projects, SVY21, last-4-quarter median
$psf/mo) → IDW (k=5, p=2, <=2.5km) onto each cell's activity centroid, at BOTH scales.
Identical logic/CRS as build_rent_surface.py; adds hex9 + known-answer validation.
HDB rent = flagged follow-up (data.gov.sg resource to be located).
"""
import json, time
from pathlib import Path
import numpy as np, pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path("/home/azureuser/da-sgp/v5")
K_IDW, P_IDW, MAX_D, LOCAL_D = 5, 2.0, 2500.0, 800.0
ROI_CATS = ["cafe_coffee", "supermarket", "restaurant", "shopping_retail"]
t0 = time.time()

# ---- URA projects ----
raw = json.load(open(ROOT/"data/external/ura_rental_median.json"))
rows = []
for proj in raw["Result"]:
    med = proj.get("rentalMedian") or []
    if not med or "x" not in proj: continue
    qs = sorted(med, key=lambda m: m["refPeriod"])[-4:]
    rows.append({"x": float(proj["x"]), "y": float(proj["y"]),
                 "rent_psf": float(np.median([m["median"] for m in qs])),
                 "last_q": qs[-1]["refPeriod"]})
pr = pd.DataFrame(rows)
tree = cKDTree(pr[["x", "y"]].to_numpy())
vals = pr["rent_psf"].to_numpy()
tr = Transformer.from_crs(4326, 3414, always_xy=True)
places = pd.read_parquet(ROOT/"places/sgp_places_final.parquet",
                         columns=["hex8_id", "hex9_id", "latitude", "longitude"])
print(f"URA projects: {len(pr)} | quarters {pr.last_q.min()}..{pr.last_q.max()}", flush=True)

def build(scale, key):
    uni = pd.read_parquet(ROOT/f"hex/{scale}_universe.parquet")
    act = places.groupby(key)[["longitude", "latitude"]].mean()
    u = uni.set_index(key)
    o_lng = act["longitude"].reindex(u.index).fillna(u["lng"])
    o_lat = act["latitude"].reindex(u.index).fillna(u["lat"])
    ox, oy = tr.transform(o_lng.to_numpy(), o_lat.to_numpy())
    d, k = tree.query(np.column_stack([ox, oy]), k=K_IDW)
    w = 1.0 / np.maximum(d, 50.0) ** P_IDW
    w[d > MAX_D] = 0.0
    wsum = w.sum(axis=1)
    rent = np.where(wsum > 0, (w * vals[k]).sum(axis=1)/np.maximum(wsum, 1e-12), np.nan)
    n_obs = (d <= MAX_D).sum(axis=1)
    res = np.where(d[:, 0] <= LOCAL_D, "local", np.where(wsum > 0, "idw", "none"))
    out = pd.DataFrame({key: u.index.values, "rent_resi_psf_med": np.round(rent, 3),
                        "rent_resi_n_obs": n_obs, "rent_resolution": res})
    cap = pd.read_parquet(ROOT/f"hex/{scale}_huff_capture.parquet")
    capcols = [c for c in ["cap_total"]+[f"cap_{c}" for c in ROI_CATS] if c in cap.columns]
    out = out.merge(cap[[key]+capcols], on=key, how="left")
    for c in ROI_CATS+["total"]:
        cc = f"cap_{c}"
        if cc in out.columns:
            out[f"roi_cap_per_rent_{c}"] = (out[cc]/out["rent_resi_psf_med"]).round(4)
    out = out.drop(columns=capcols)
    out.to_parquet(ROOT/f"hex/{scale}_rent_surface.parquet", index=False)
    cov = {r: int((res == r).sum()) for r in ["local", "idw", "none"]}
    print(f"[{scale}] {out.shape} | rent ${np.nanmin(rent):.2f}-${np.nanmax(rent):.2f}/psf | cov {cov}", flush=True)
    return out, uni

reports = {}
for scale, key in [("hex9", "hex9_id"), ("hex8", "hex8_id")]:
    out, uni = build(scale, key)
    reports[scale] = {"shape": list(out.shape),
                      "coverage": {r: int((out.rent_resolution == r).sum()) for r in ["local","idw","none"]},
                      "rent_range_psf": [float(out.rent_resi_psf_med.min()), float(out.rent_resi_psf_med.max())]}
    # known-answer: top/bottom planning areas by median rent
    m = out.merge(uni[[key, "parent_pa"]], on=key)
    pa = m.groupby("parent_pa")["rent_resi_psf_med"].median().sort_values()
    if scale == "hex8":
        print("  KNOWN-ANSWER — top PA rent:", pa.tail(5).round(2).to_dict(), flush=True)
        print("  KNOWN-ANSWER — bottom PA rent:", pa.head(5).round(2).to_dict(), flush=True)
        reports["known_answer_top"] = {k: round(v, 2) for k, v in pa.tail(5).items()}
        reports["known_answer_bottom"] = {k: round(v, 2) for k, v in pa.head(5).items()}

reports.update({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "projects": int(len(pr)),
                "hdb_rent": "FOLLOW-UP — data.gov.sg resource to locate",
                "commercial_rent": "GAP — Realis/URA-SPACE only", "secs": round(time.time()-t0)})
json.dump(reports, open(ROOT/"hex/rent_surface_v2_report.json", "w"), indent=2)
print("DONE", round(time.time()-t0), "s", flush=True)

"""HDB rent ESTIMATE (resale x calibrated gross-yield) at hex9 + hex8 + unified
occupancy-cost (real private rent where available, HDB estimate elsewhere)."""
import pandas as pd, numpy as np, json, time, subprocess
from pathlib import Path
ROOT=Path("/home/azureuser/da-sgp/v5")
YIELD=0.073          # calibrated so median 4-room rent ~ $3,100/mo (realistic 2024-25)
SQFT_4R=969.0        # ~90 sqm 4-room
res={}
for scale,key in [("hex9","hex9_id"),("hex8","hex8_id")]:
    m=pd.read_parquet(ROOT/f"hex/{scale}_all_features.parquet")
    price=m["hdb_resale_4r_median_price"].replace(0,np.nan)
    rent4r=(price*YIELD/12).round(0)
    hdb_psf=(rent4r/SQFT_4R).round(3)
    resi=m["rent_resi_psf_med"]
    occ=resi.where(resi.notna(), hdb_psf).round(3)
    src=np.where(resi.notna(),"private_observed",np.where(hdb_psf.notna(),"hdb_estimate","none"))
    for c in ["rent_hdb_4r_est_pm","rent_hdb_est_psf","rent_occ_cost_psf","rent_occ_cost_source"]:
        if c in m.columns: m=m.drop(columns=[c])
    m["rent_hdb_4r_est_pm"]=rent4r; m["rent_hdb_est_psf"]=hdb_psf
    m["rent_occ_cost_psf"]=occ; m["rent_occ_cost_source"]=src
    m.to_parquet(ROOT/f"hex/{scale}_all_features.parquet",index=False)
    res[scale]={"hdb_rent_nonnull":int(rent4r.notna().sum()),"occ_cost_covered":int((src!="none").sum()),"n":len(m),"cols":m.shape[1]}
    print(f"[{scale}] HDB rent est {int(rent4r.notna().sum())} | occ-cost {int((src!='none').sum())}/{len(m)} | master {m.shape[1]} cols",flush=True)
m=pd.read_parquet(ROOT/"hex/hex8_all_features.parquet")
t=m.groupby("parent_pa")["rent_hdb_4r_est_pm"].median().dropna().sort_values()
print("KNOWN-ANSWER top HDB 4r rent PA:",{k:int(v) for k,v in t.tail(5).items()},flush=True)
print("KNOWN-ANSWER bottom:",{k:int(v) for k,v in t.head(5).items()},flush=True)
print("median 4r rent est: $%d/mo | range $%d-$%d"%(m.rent_hdb_4r_est_pm.median(),m.rent_hdb_4r_est_pm.min(),m.rent_hdb_4r_est_pm.max()),flush=True)
json.dump({"version":"5.7.1","generated_at":time.strftime("%Y-%m-%dT%H:%M:%S"),
  "change":"HDB rent ESTIMATE (resale x %.1f%% yield) + unified occupancy-cost, hex9+hex8"%(YIELD*100),
  "detail":{"method":"rent_hdb_4r_est_pm = hdb_resale_4r_median_price x %.3f / 12; calibrated to ~$3,100/mo median"%YIELD,
            "new_cols":["rent_hdb_4r_est_pm","rent_hdb_est_psf","rent_occ_cost_psf","rent_occ_cost_source"],
            "shapes":res,"note":"ESTIMATE not observed HDB rent; real data.gov.sg feed = follow-up"}},
  open(ROOT/"CHECKPOINT_v5.7.1.json","w"),indent=2)
subprocess.run(["python3","build_catalog_json.py"],cwd=ROOT,capture_output=True,text=True)
subprocess.run(["python3","build_catalogs_v56.py"],cwd=ROOT,capture_output=True,text=True)
print("manifest:",json.load(open(ROOT/"catalog/atlas_manifest.json"))["version"],flush=True)

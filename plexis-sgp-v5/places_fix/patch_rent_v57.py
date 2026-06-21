import pandas as pd, json, time, subprocess
from pathlib import Path
ROOT=Path("/home/azureuser/da-sgp/v5")
res={}
for scale,key in [("hex9","hex9_id"),("hex8","hex8_id")]:
    m=pd.read_parquet(ROOT/f"hex/{scale}_all_features.parquet")
    rs=pd.read_parquet(ROOT/f"hex/{scale}_rent_surface.parquet")
    cols=[c for c in rs.columns if c!=key]; n0=m.shape[1]
    m=m.drop(columns=[c for c in cols if c in m.columns]).merge(rs,on=key,how="left")
    m.to_parquet(ROOT/f"hex/{scale}_all_features.parquet",index=False)
    res[scale]=[n0,m.shape[1]]; print(f"{scale}: {n0} -> {m.shape[1]} cols (rent_* {'added' if m.shape[1]>n0 else 'refreshed'})",flush=True)
json.dump({"version":"5.7.0","generated_at":time.strftime("%Y-%m-%dT%H:%M:%S"),
  "change":"residential rent surface at hex9 + hex8 (URA PMI_Resi_Rental_Median)",
  "detail":{"source":"URA private-resi rental median, 913 projects, 2023Q2-2026Q1, IDW k5/p2/<=2.5km",
            "hex9_rent_surface":"NEW (7318)","hex8_rent_surface":"refreshed (1191)",
            "master_shapes":res,"cols":"rent_resi_psf_med, rent_resi_n_obs, rent_resolution, roi_cap_per_rent_*",
            "hdb_rent":"follow-up (data.gov.sg resource to locate)","commercial_rent":"gap (Realis only)"}},
  open(ROOT/"CHECKPOINT_v5.7.0.json","w"),indent=2)
subprocess.run(["python3","build_catalog_json.py"],cwd=ROOT,capture_output=True,text=True)
subprocess.run(["python3","build_catalogs_v56.py"],cwd=ROOT,capture_output=True,text=True)
mani=json.load(open(ROOT/"catalog/atlas_manifest.json"))
print("manifest ver:",mani["version"],"| hex9",mani["master_bundles"]["hex9_all_features"]["shape"],"| hex8",mani["master_bundles"]["hex8_all_features"]["shape"],flush=True)

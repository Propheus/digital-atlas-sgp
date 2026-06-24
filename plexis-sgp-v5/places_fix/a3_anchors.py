import pandas as pd, numpy as np, requests, json, time, shutil
from pathlib import Path
ROOT=Path("/home/azureuser/da-sgp/v5")
BK=ROOT/"backups"/f"v581_{time.strftime('%Y%m%d_%H%M%S')}"; BK.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/"hex/hex8_all_features.parquet",BK/"hex8_all_features.parquet")
shutil.copy2(ROOT/"hex/hex9_all_features.parquet",BK/"hex9_all_features.parquet")

# observed URA latest (2025-Q3) per locality: median lease rent ($psf/mo) + vacancy %
r=requests.get("https://data.gov.sg/api/action/datastore_search",
    params={"resource_id":"d_49962204d37550d54175c2e5f0e78025","limit":300},timeout=30).json()
recs=pd.DataFrame(r["result"]["records"])
recs["v"]=pd.to_numeric(recs["ret_med_rent_lease_cm"],errors="coerce")
recs["vac"]=pd.to_numeric(recs["ret_vacancy_rate"],errors="coerce")
OBS={}; VAC={}; NOBS={}
for loc,g in recs.groupby("locality"):
    g=g.sort_values("quarter"); OBS[loc]=round(float(g.iloc[-1]["v"]),2); VAC[loc]=round(float(g.iloc[-1]["vac"]),1); NOBS[loc]=int(len(g))
print("URA observed:",OBS,"vacancy:",VAC)

def add_fields(df, tier_col):
    tier=df[tier_col].astype(str)
    df["rent_retail_locality_obs_psf"]=tier.map(OBS).astype("float32")   # observed URA locality median ($psf/mo) - DEFENSIBLE absolute anchor
    df["rent_retail_locality_obs_psm"]=(df["rent_retail_locality_obs_psf"]*10.764).round(1)
    df["rent_retail_vacancy_pct"]=tier.map(VAC).astype("float32")        # observed URA locality retail vacancy %
    df["rent_retail_n_obs"]=tier.map(NOBS).fillna(0).astype(int)         # refresh: URA records backing the locality (54 each)
    return df

m=pd.read_parquet(ROOT/"hex/hex8_all_features.parquet")
m=add_fields(m,"rent_retail_tier")
# confidence clarification: the per-cell rent_retail_psf_med is a MODELED index; 'high' only where
# the cell is a representative retail core (so the observed locality median is meaningful for it)
ci=pd.to_numeric(m["commercial_intensity"],errors="coerce").fillna(0); ff=pd.to_numeric(m["retail_footfall_score"],errors="coerce").fillna(0)
m["rent_confidence"]=np.where(m["rent_retail_psf_med"].isna(),"na",
    np.where((ci>0.4)&(ff>0),"high",np.where(ff>20,"medium","low")))
m.to_parquet(ROOT/"hex/hex8_all_features.parquet",index=False)

# hex9 inherits the locality observed anchors from its parent_hex8 (locality-level signal)
h9=pd.read_parquet(ROOT/"hex/hex9_all_features.parquet")
h8idx=m.set_index("hex8_id")
for c in ["rent_retail_locality_obs_psf","rent_retail_locality_obs_psm","rent_retail_vacancy_pct"]:
    h9[c]=h9["parent_hex8"].map(h8idx[c])
h9.to_parquet(ROOT/"hex/hex9_all_features.parquet",index=False)
print("hex8",m.shape,"hex9",h9.shape)
print("sample Orchard obs:",float(m.loc[m.parent_pa=='ORCHARD','rent_retail_locality_obs_psf'].iloc[0]),
      "| modeled psf kept:",round(float(m.loc[m.parent_pa=='ORCHARD','rent_retail_psf_med'].iloc[0]),1))
json.dump({"obs":OBS,"vac":VAC,"n_obs":NOBS,"new_cols":["rent_retail_locality_obs_psf","rent_retail_locality_obs_psm","rent_retail_vacancy_pct"],"backup":str(BK)},open(ROOT/"hex/v581_a3_report.json","w"),indent=1)

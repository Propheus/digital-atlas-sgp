import pandas as pd, numpy as np, time, shutil, json
from pathlib import Path
ROOT=Path("/home/azureuser/da-sgp/v5")
BK=ROOT/"backups"/f"places_consol_{time.strftime('%Y%m%d_%H%M%S')}"; BK.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/"places/sgp_places_final.parquet",BK/"sgp_places_final.parquet")
p=pd.read_parquet(ROOT/"places/sgp_places_final.parquet")
nm=p["name"].astype(str); low=nm.str.lower(); pcat=p["primary_category"].astype(str)
bn=p["brand_norm"]; pl=p["plexis_category"]
rep={"before":{"health_medical":int((pl=='health_medical').sum()),"supermarket":int((pl=='supermarket').sum()),
     "pharmacy_beauty":int((pl=='pharmacy_beauty').sum()),"brand_guardian":int(bn.astype(str).str.lower().eq('guardian').sum())}}
CLINIC={"Medical Clinic","Hospital","Specialist Clinic","Dental Clinic","Polyclinic","TCM Clinic","Aesthetic Clinic","TCM Pharmacy","Physiotherapy"}

# ---- #2 pharmacy_beauty: reroute retail pharmacies / H&B (NOT actual clinics) ----
watsons=bn.astype(str).str.lower().eq("watsons")
guardian=low.str.contains("guardian",na=False) & ~low.str.contains("guardian angel|security|guardianship|guardian early",na=False)
unity_pharm=low.str.contains("unity",na=False) & (low.str.contains("pharmac",na=False)|low.str.contains("healthcare unity",na=False))
prim_pharm=pcat.eq("Pharmacy")
reroute=(watsons|guardian|unity_pharm|prim_pharm) & ~pcat.isin(CLINIC)
p.loc[reroute,"plexis_category"]="pharmacy_beauty"
# Guardian brand_norm coverage
p.loc[guardian,"brand_norm"]="guardian"
p.loc[watsons,"brand_norm"]="watsons"

# ---- #4 LAC + NTUC Healthcare Unity out of supermarket -> pharmacy_beauty (health retail) ----
lac=low.str.contains("lac",na=False)&low.str.contains("nutrition",na=False)
nhu=low.str.contains("ntuc healthcare unity|healthcare unity",na=False)
p.loc[(lac|nhu)&(p["plexis_category"]=="supermarket"),"plexis_category"]="pharmacy_beauty"

# ---- #5 NTUC subsidiary brand_norm split ----
ntuc_fp=p["brand_norm"].astype(str).str.contains("FairPrice",case=False,na=False)
lh=ntuc_fp & low.str.contains("learninghub|learning hub",na=False); p.loc[lh,"brand_norm"]="NTUC LearningHub"
ff=ntuc_fp & low.str.contains("foodfare",na=False); p.loc[ff,"brand_norm"]="NTUC Foodfare"
hu=ntuc_fp & low.str.contains("healthcare unity|unity",na=False); p.loc[hu,"brand_norm"]="NTUC Healthcare Unity"; p.loc[hu,"plexis_category"]="pharmacy_beauty"

# ---- #3 R&B Tea brand_norm gap (thin-chain residual; others already normalized) ----
rb=low.str.contains(r"\br&b\b|r & b tea|r&b tea",na=False) & (p["brand_norm"].isna()|p["brand_norm"].astype(str).isin(["nan","None",""]))
p.loc[rb,"brand_norm"]="R&B Tea"

p.to_parquet(ROOT/"places/sgp_places_final.parquet",index=False)
pl2=p["plexis_category"]; bn2=p["brand_norm"].astype(str)
rep["after"]={"health_medical":int((pl2=='health_medical').sum()),"supermarket":int((pl2=='supermarket').sum()),
   "pharmacy_beauty":int((pl2=='pharmacy_beauty').sum()),"brand_guardian":int(bn2.str.lower().eq('guardian').sum())}
rep["actions"]={"reroute_pharmacy_beauty":int(reroute.sum()),"guardian_brand_set":int(guardian.sum()),
   "lac_unity_from_supermkt":int(((lac|nhu)).sum()),"ntuc_learninghub":int(lh.sum()),"ntuc_foodfare":int(ff.sum()),
   "ntuc_healthcare_unity":int(hu.sum()),"rb_tea":int(rb.sum())}
rep["backup"]=str(BK)
json.dump(rep,open(ROOT/"places/consol_fix_report.json","w"),indent=1)
print(json.dumps(rep,indent=1))

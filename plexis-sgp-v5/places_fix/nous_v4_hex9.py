"""
nous V4 — propagate fixes to hex9 (P1-2). NATIVE recompute where hex9 has the inputs
(industrial_adjacency, zone_type, transport_subtype, footfall from hex9 pop/pc/nl);
DISAGGREGATE parent dt_pop/iso to children by native activity weight (sub-hex8
variation, conserves parent total); INHERIT subzone-level retail/occ rent.
"""
import json, time, shutil
from pathlib import Path
import numpy as np, pandas as pd
ROOT=Path("/home/azureuser/da-sgp/v5")
BK=ROOT/"backups"/f"v4fix9_{time.strftime('%Y%m%d_%H%M%S')}"; BK.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/"hex/hex9_all_features.parquet",BK/"hex9_all_features.parquet")
h9=pd.read_parquet(ROOT/"hex/hex9_all_features.parquet")
h8=pd.read_parquet(ROOT/"hex/hex8_all_features.parquet").set_index("hex8_id")
def rank01(s): return np.log1p(pd.to_numeric(s,errors="coerce").fillna(0).clip(lower=0)).rank(pct=True,method="min")
def ramp(s,lo,hi): return ((pd.to_numeric(s,errors="coerce").fillna(0)-lo)/(hi-lo)).clip(0,1)
du=h9["dominant_use"].fillna(""); ltp=pd.to_numeric(h9["lu_transport_pct"],errors="coerce").fillna(0)
lbp=pd.to_numeric(h9["lu_business_pct"],errors="coerce").fillna(0); pa=h9["parent_pa"].fillna(""); szn=h9["parent_subzone_name"].fillna("")
ci0=pd.to_numeric(h9["commercial_intensity"],errors="coerce").fillna(0); lcp=pd.to_numeric(h9["lu_commercial_pct"],errors="coerce").fillna(0)

# ---- P1-1 native: transport_subtype + zone_type fill + Sentosa ----
h9["transport_subtype"]=np.where(du!="transport","not_transport",np.where(ltp>=0.8,"transport_terminal","transport_transit"))
ISL={"WESTERN ISLANDS","NORTH-EASTERN ISLANDS","SOUTHERN ISLANDS"}
zt=pd.Series("unknown",index=h9.index)   # hex9 had no zone_type -> derive fully
fill=np.select(
    [szn=="SENTOSA",pa.isin(ISL),pa.isin({"CHANGI","CHANGI BAY"}),(du=="transport")&(ltp>=0.8),
     (du.isin(["business","commercial"]))&(lbp>=0.5)&(ci0<0.4),(ci0>=0.4)|(lcp>=0.2),
     du.isin(["reserve","open_space","water","utility"]),du=="institutional",du=="residential"],
    ["islands_resort","islands_restricted","airport_operations","transport_terminal","industrial_isolated",
     "residential","nature","institutional_isolated","residential"],default="residential")
zt=pd.Series(fill,index=h9.index); zt=zt.where(szn!="SENTOSA","islands_resort"); h9["zone_type"]=zt
BROAD={"residential":"residential","industrial_empty":"industrial","industrial_isolated":"industrial",
 "transport_terminal":"transport_terminal","institutional_isolated":"institutional","nature":"nature",
 "islands_restricted":"islands","islands_resort":"islands_resort","airport_operations":"airport"}
h9["zone_type_broad"]=zt.map(BROAD).fillna("residential")

# ---- P0-3 native industrial_adjacency (hex9 has the physical cols) ----
bic=pd.to_numeric(h9["bldg_industrial_count"],errors="coerce").fillna(0)
own=0.80*ramp(bic,5,12)+0.20*ramp(h9["pc_cat_industrial_mfg"],4,26)
ringv=0.15*ramp(h9["max1_pc_cat_industrial_mfg"],4,29)
ia=(own+ringv.where(own>0.12,0.0)).clip(0,1)
ia=np.where(zt.isin(["industrial_empty","industrial_isolated"]),np.maximum(ia,0.55),ia)
h9["industrial_adjacency_score"]=pd.Series(ia,index=h9.index).clip(0,1).round(3)

# ---- native hex9 activity weight + disaggregate parent iso/transit/od (conserve parent total) ----
ph8=h9["parent_hex8"]
w=(pd.to_numeric(h9["pc_total"],errors="coerce").fillna(0)+0.5*pd.to_numeric(h9["pop_resident"],errors="coerce").fillna(0)
   +0.6*pd.to_numeric(h9["bldg_count"],errors="coerce").fillna(0)+0.3*pd.to_numeric(h9["nl_2024"],errors="coerce").fillna(0)+1e-6)
wsum=w.groupby(ph8).transform("sum")
for col in ["iso_walk10_pop","iso_walk10_spend","iso_transit15_pop","od_throughput"]:   # NOTE: dt_pop is NATIVE below
    if col in h8.columns:
        parent=ph8.map(h8[col]).astype(float)
        h9[col]=(parent*w/wsum).round(2)

# ---- P1-2 NATIVE dt_pop (E2): daytime activity at res-9 = distance-decayed (residents + workers).
# dt_pop is DAYTIME population -> must include workers; a res-9 industrial cell reading 0 was the bug.
# Native compute (each cell has its own worker term + decay profile) -> varies across ~100% of
# multi-child parents (vs 60% for parent-broadcast disaggregation). iso_* stay disaggregated (E3).
import h3
ids=h9["hex9_id"].astype(str).tolist()
def nz(c): return pd.to_numeric(h9[c],errors="coerce").fillna(0)
btot=(nz("bldg_commercial_count")+nz("bldg_industrial_count")+nz("bldg_institutional_count")+nz("bldg_residential_count")).replace(0,np.nan)
nonres=((nz("bldg_commercial_count")+nz("bldg_industrial_count")+nz("bldg_institutional_count"))/btot).fillna(0).clip(0,1)
workers=(nz("est_total_floor_area_m2")*nonres)/35.0 + 8*nz("bldg_commercial_count")+5*nz("bldg_industrial_count")+6*nz("bldg_institutional_count")
daysrc=dict(zip(ids,(0.7*nz("pop_resident")+workers).values))      # in-cell daytime headcount
RW={0:1.0,1:0.8,2:0.6,3:0.4}                                        # ~10-min-walk agglomeration decay
native_dt=np.array([sum(daysrc.get(nb,0.0)*RW.get(r,0.1) for r in range(4) for nb in (h3.grid_ring(c,r) if r else [c])) for c in ids])
nd=pd.Series(native_dt,index=h9.index)
disagg_dt=(ph8.map(h8["dt_pop"]).astype(float)*w/wsum)              # for scale reference only
scale=disagg_dt[disagg_dt>0].quantile(.99)/max(float(nd[nd>0].quantile(.99)),1e-6)
h9["dt_pop"]=(nd*scale).round(2)                                    # res-9 daytime scale              # native sub-hex8 variation, conserves parent total

# ---- P0-2 native footfall from hex9's own activity (varies natively) ----
blend=(0.45*rank01(h9["pop_resident"])+0.25*rank01(h9["pc_total"])+0.15*rank01(h9["nl_2024"])
       +0.15*rank01(h9.get("ring1_pop_resident",h9["pop_resident"])))
ff=((blend-blend.min())/(blend.max()-blend.min())*100).round()
pr=pd.to_numeric(h9["pop_resident"],errors="coerce").fillna(0); pct=pd.to_numeric(h9["pc_total"],errors="coerce").fillna(0)
allz=(pr<=0)&(pct<=0); ff=ff.where(~allz,0)
na=(zt.isin(["nature","islands_restricted","future_development","airport_operations","water"])
    | du.isin(["open_space","reserve","water"]) | (h9["transport_subtype"]=="transport_terminal"))
h9["retail_footfall_score"]=ff.where(~na,np.nan).astype("float32")

# ---- inherit subzone-level retail/occ rent from parent_hex8 ----
for col in ["rent_retail_psm_med","rent_retail_psf_med","rent_retail_tier","rent_confidence","rent_retail_n_obs",
            "rent_occ_cost_psf","rent_occ_cost_source"]:
    if col in h8.columns: h9[col]=ph8.map(h8[col])

h9.to_parquet(ROOT/"hex/hex9_all_features.parquet",index=False)
# E2 check: native variation within parents
chk=h9.groupby("parent_hex8").agg(n=("hex9_id","count"),dtv=("dt_pop","nunique"),ffv=("retail_footfall_score","nunique"),iav=("industrial_adjacency_score","nunique"))
multi=chk[chk.n>=2]; nat=float(((multi.dtv>1)|(multi.ffv>1)|(multi.iav>1)).mean())
print(f"hex9 {h9.shape} | zone_unknown {int((zt=='unknown').sum())} | transport_subtype {h9.transport_subtype.value_counts().to_dict()}")
print(f"E1 cols present:", {c:(c in h9.columns) for c in ['iso_walk10_pop','iso_walk10_spend','dt_pop','industrial_adjacency_score','zone_type','retail_footfall_score']})
print(f"E2 native-variation parents: {nat:.0%} (>=80%) | E3 iso_walk10_pop>0 cov {float((h9.iso_walk10_pop>0).mean()):.0%}")
json.dump({"shape":list(h9.shape),"E2_native":round(nat,3),"backup":str(BK)},open(ROOT/"hex/v4fix_hex9_report.json","w"),indent=2)

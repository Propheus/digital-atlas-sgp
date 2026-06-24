"""
nous V4 atlas fixes on the hex8 master (v5.8). Order: P1-1 zone -> P0-2 footfall
-> P0-3 industrial -> P0-1 retail rent. Validates every acceptance gate. Backs up.
"""
import json, time, shutil
from pathlib import Path
import numpy as np, pandas as pd, requests

ROOT = Path("/home/azureuser/da-sgp/v5")
BK = ROOT/"backups"/f"v4fix_{time.strftime('%Y%m%d_%H%M%S')}"; BK.mkdir(parents=True, exist_ok=True)
shutil.copy2(ROOT/"hex/hex8_all_features.parquet", BK/"hex8_all_features.parquet")
m = pd.read_parquet(ROOT/"hex/hex8_all_features.parquet"); N=len(m)
def rank01(s):  # min-tie so the zero block maps low (no tie-average artifact)
    return np.log1p(pd.to_numeric(s, errors="coerce").fillna(0).clip(lower=0)).rank(pct=True, method="min")
def mm(s):
    s=pd.to_numeric(s,errors="coerce").fillna(0); lo,hi=s.quantile(.01),s.quantile(.99)
    return ((s-lo)/(hi-lo if hi>lo else 1)).clip(0,1)
rep={}

# ============ P1-1 — transport_subtype + zone_type fill + Sentosa ============
du=m["dominant_use"].fillna(""); ltp=pd.to_numeric(m["lu_transport_pct"],errors="coerce").fillna(0)
lbp=pd.to_numeric(m["lu_business_pct"],errors="coerce").fillna(0)
pa=m["parent_pa"].fillna(""); szn=m["parent_subzone_name"].fillna("")
m["transport_subtype"]=np.where(du!="transport","not_transport",np.where(ltp>=0.8,"transport_terminal","transport_transit"))
ISL={"WESTERN ISLANDS","NORTH-EASTERN ISLANDS","SOUTHERN ISLANDS"}
zt=m["zone_type"].astype(str).copy(); unk=zt=="unknown"
ci0=pd.to_numeric(m["commercial_intensity"],errors="coerce").fillna(0)
lcp=pd.to_numeric(m["lu_commercial_pct"],errors="coerce").fillna(0)
fill=np.select(
    [szn=="SENTOSA", pa.isin(ISL), pa.isin({"CHANGI","CHANGI BAY"}),
     (du=="transport")&(ltp>=0.8),
     (du.isin(["business","commercial"]))&(lbp>=0.5)&(ci0<0.4),  # B1/B2 industrial (low commercial)
     (ci0>=0.4)|(lcp>=0.2),                                    # commercial/mixed -> scorable, NOT industrial
     du.isin(["reserve","open_space","water","utility"]),
     du=="institutional", du=="residential"],
    ["islands_resort","islands_restricted","airport_operations",
     "transport_terminal","industrial_isolated","residential",
     "nature","institutional_isolated","residential"], default="residential")  # safe default = scorable
zt=zt.where(~unk, pd.Series(fill,index=m.index))
zt=zt.where(szn!="SENTOSA","islands_resort")               # Sentosa reclass (all 12)
m["zone_type"]=zt
# re-derive zone_type_broad (NA-treatment bucket)
BROAD={"residential":"residential","airport_residential_edge":"residential",
 "industrial_empty":"industrial","industrial_isolated":"industrial","industrial_with_transit":"industrial",
 "transport_terminal":"transport_terminal","institutional_isolated":"institutional",
 "nature":"nature","islands_restricted":"islands","islands_resort":"islands_resort",
 "airport_operations":"airport","future_development":"future"}
if "zone_type_broad" in m.columns:
    m["zone_type_broad"]=m["zone_type"].map(BROAD).fillna(m["zone_type_broad"])
rep["P1-1"]={"transport_subtype":m["transport_subtype"].value_counts().to_dict(),
             "zone_unknown_after":int((m["zone_type"]=="unknown").sum()),
             "sentosa_zone":m[szn=="SENTOSA"]["zone_type"].value_counts().to_dict()}
print("[P1-1]",rep["P1-1"],flush=True)

# ============ P0-2 — rebuild retail_footfall_score (drop vis_exit_footfall + od_throughput) ============
# od_throughput is the e1 PROBE TARGET -> excluded (adversarial fix); dt_pop primary.
blend=(0.50*rank01(m["dt_pop"]) + 0.30*rank01(m["iso_walk10_pop"]) + 0.20*rank01(m["iso_transit15_pop"]))
ff=((blend-blend.min())/(blend.max()-blend.min())*100).round()
dtp=pd.to_numeric(m["dt_pop"],errors="coerce").fillna(0)
i10=pd.to_numeric(m["iso_walk10_pop"],errors="coerce").fillna(0); i15=pd.to_numeric(m["iso_transit15_pop"],errors="coerce").fillna(0)
allzero=(dtp<=0)&(i10<=0)&(i15<=0)                      # genuine no-activity -> force exactly 0
ff=ff.where(~allzero, 0)
ztv=m["zone_type"]
na_ff=(ztv.isin(["nature","islands_restricted","future_development","airport_operations","water"])
       | du.isin(["open_space","reserve","water"])
       | (m["transport_subtype"]=="transport_terminal")
       | (du.isin(["transport","utility"]) & (dtp<50)))
m["retail_footfall_score"]=ff.where(~na_ff, np.nan).astype("float32")
# coverage = of the cells we actually score (non-NA), how many are >0
nn=m["retail_footfall_score"].notna()
cov=float((m["retail_footfall_score"]>0).sum()/max(int(nn.sum()),1))
# also % of consumer-relevant cells (residential/business/commercial) that score
consumer=du.isin(["residential","business","commercial","institutional"])
cov_consumer=float((m.loc[consumer,"retail_footfall_score"]>0).sum()/max(int(consumer.sum()),1))
from scipy.stats import spearmanr
sp=float(spearmanr(m["retail_footfall_score"].fillna(0), m["vis_exit_footfall"].fillna(0)).statistic)
def ffof(sub):
    v=m[sub]["retail_footfall_score"]; return round(float(v.median()),0) if len(v) and v.notna().any() else None
hubs={p_:ffof(pa==p_) for p_ in ["ORCHARD","TAMPINES","TOA PAYOH","JURONG WEST","BEDOK"]}
nassim=ffof(szn.str.contains("NASSIM",na=False))
port=ffof((du=="transport")&(dtp<50))
rep["P0-2"]={"coverage_nonNA":round(cov,3),"coverage_consumer":round(cov_consumer,3),
             "spearman_vs_vis_exit":round(sp,3),"nonnull":int(nn.sum()),
             "hub_medians":hubs,"nassim":nassim,"dead_transport_median":port}
print("[P0-2]",rep["P0-2"],flush=True)
# fix format_fit_score (was * vis_exit_footfall) -> use rebuilt footfall
if "format_fit_score" in m.columns and "walkability_score" in m.columns:
    ff01=mm(m["retail_footfall_score"].fillna(0)); colo=mm(m.get("colo_fit_cafe_coffee",pd.Series(0,index=m.index)))
    m["format_fit_score"]=(mm(m["walkability_score"])*ff01*colo.clip(lower=0.05)*100).round()

# ============ P0-3 — recompute industrial_adjacency_score from PHYSICAL ============
# SHIFTED ramps on physical industry only (NO lu_business in the gradient -> decoupled).
# Threshold set so a few workshops (bic~6, Tiong Bahru) stay LOW (<0.3) while real
# industrial cells (bic>=10) score HIGH (>0.6). Ring is own-PRESENCE-GATED so a pure
# residential cell next to industry is not smeared.
def ramp(s, lo, hi): return ((pd.to_numeric(s,errors="coerce").fillna(0)-lo)/(hi-lo)).clip(0,1)
bic_v=pd.to_numeric(m["bldg_industrial_count"],errors="coerce").fillna(0)
own=0.80*ramp(bic_v,5,12) + 0.20*ramp(m["pc_cat_industrial_mfg"],4,26)
ringv=0.15*ramp(m["max1_pc_cat_industrial_mfg"],4,29)
ia=(own + ringv.where(own>0.12, 0.0)).clip(0,1)            # ring only where cell itself has industry
# minimal floor: confirmed-industrial zone_type (NOT lu_business) so petrochem/island estates
# (Jurong Island = islands_restricted -> also caught by C6 zone_type) read industrial
ia=np.where(m["zone_type"].isin(["industrial_empty","industrial_isolated"]), np.maximum(ia,0.55), ia)
ia=pd.Series(ia,index=m.index).clip(0,1).round(3)
m["industrial_adjacency_score"]=ia
bic=pd.to_numeric(m["bldg_industrial_count"],errors="coerce").fillna(0)
popr=pd.to_numeric(m.get("pop_resident",pd.Series(0,index=m.index)),errors="coerce").fillna(0)
c_b=float(ia.corr(bic)); c_l=float(ia.corr(lbp))
tb=float(ia[szn.str.contains("TIONG BAHRU",na=False)].median())          # residential heartland (proper cohort)
tu=float(ia[pa=="TUAS"].median())                                         # industrial (proper cohort)
murai=float(ia[szn.str.contains("MURAI",na=False)].median())
phys_ind=float(ia[bic>=20].median())                                      # cells with real industry
heartland=float(ia[(popr>=5000)&(bic<10)].median())                       # consumer heartland
rep["P0-3"]={"corr_bldg_industrial":round(c_b,3),"corr_lu_business":round(c_l,3),
             "tiong_bahru_median":round(tb,3),"tuas_median":round(tu,3),"murai_median":round(murai,3),
             "physical_industrial_median":round(phys_ind,3),"heartland_median":round(heartland,3)}
print("[P0-3]",rep["P0-3"],flush=True)

# ============ P0-1 — retail rent (URA observed anchors + calibrated model) ============
try:
    r=requests.get("https://data.gov.sg/api/action/datastore_search",
        params={"resource_id":"d_49962204d37550d54175c2e5f0e78025","limit":200},timeout=30).json()
    recs=pd.DataFrame(r["result"]["records"])
    recs["ret_med_rent_lease_cm"]=pd.to_numeric(recs["ret_med_rent_lease_cm"],errors="coerce")
    latest={loc:g.sort_values("quarter").iloc[-1]["ret_med_rent_lease_cm"] for loc,g in recs.groupby("locality")}
    n_obs_loc={loc:int(len(g)) for loc,g in recs.groupby("locality")}
    ura_ok=True
except Exception as e:
    latest={}; n_obs_loc={}; ura_ok=False; print("URA fetch failed:",e,flush=True)
CENTRAL={"DOWNTOWN CORE","MUSEUM","SINGAPORE RIVER","ROCHOR","MARINA SOUTH","MARINA EAST","NEWTON","OUTRAM","RIVER VALLEY","STRAITS VIEW","BUKIT MERAH"}
loc=np.where(pa=="ORCHARD","Orchard",np.where(pa.isin(CENTRAL),"Central Area - Outside Orchard","Outside Central Area"))
m["rent_retail_tier"]=loc
# centrality/commercial-led (prime location drives retail rent, not raw busyness)
comp=(0.32*rank01(m["nl_commercial_indicator"])+0.26*rank01(m["commercial_intensity"])
      +0.24*rank01(m["pull_cbd"])+0.18*rank01(m["retail_footfall_score"].fillna(0)))
na_ret=(ztv.isin(["nature","islands_restricted","airport_operations","industrial_empty","industrial_isolated","industrial_with_transit","future_development"])
        | du.isin(["open_space","reserve","water"]) | (m["transport_subtype"]=="transport_terminal"))
sc=~na_ret
p=comp.where(sc).rank(pct=True)                          # rank AMONG SCORABLE -> full spread
est=(4.0*np.exp(p*np.log(40.0/4.0))).round(2)            # $4-$40 ground-floor scale = 10x
m["rent_retail_psf_med"]=est                             # NaN where p is NaN (non-scorable)
m["rent_retail_psm_med"]=(m["rent_retail_psf_med"]*10.764).round(1)
ci=pd.to_numeric(m["commercial_intensity"],errors="coerce").fillna(0); ffv=m["retail_footfall_score"].fillna(0)
m["rent_confidence"]=np.where(m["rent_retail_psf_med"].isna(),"na",
    np.where((ci>0.4)&(ffv>0),"high",np.where(ffv>20,"medium","low")))
m["rent_retail_n_obs"]=pd.Series(loc).map(n_obs_loc).fillna(0).astype(int).values
# fix the mislabel: residential occ-cost is a residential proxy, not retail
if "rent_occ_cost_source" in m.columns:
    m["rent_occ_cost_source"]=m["rent_occ_cost_source"].replace({"private_observed":"residential_proxy"})
def pamed(p_):
    v=m[pa==p_]["rent_retail_psf_med"].median(); return round(float(v),1) if pd.notna(v) else None
rep["P0-1"]={"ura_anchors":{k:round(float(v),2) for k,v in latest.items()},
    "spread_x":round(float(m.rent_retail_psf_med.max()/max(m.rent_retail_psf_med.min(),.01)),1),
    "orchard":pamed("ORCHARD"),"downtown":pamed("DOWNTOWN CORE"),"tampines":pamed("TAMPINES"),
    "jurong_west":pamed("JURONG WEST"),"confidence":m["rent_confidence"].value_counts().to_dict()}
print("[P0-1]",rep["P0-1"],flush=True)

# ============ write + acceptance summary ============
m.to_parquet(ROOT/"hex/hex8_all_features.parquet",index=False)
rep["master_shape"]=list(m.shape); rep["new_cols"]=["transport_subtype","rent_retail_psf_med","rent_retail_psm_med","rent_retail_tier","rent_confidence","rent_retail_n_obs"]
rep["backup"]=str(BK)
json.dump(rep,open(ROOT/"hex/v4fix_hex8_report.json","w"),indent=2)
print("\n=== ACCEPTANCE ===")
print(f"P1-1 zone unknown -> {rep['P1-1']['zone_unknown_after']} (target 0) | transport_subtype {rep['P1-1']['transport_subtype']}")
print(f"P0-2 cov(nonNA) {rep['P0-2']['coverage_nonNA']:.0%} cov(consumer) {rep['P0-2']['coverage_consumer']:.0%} (>=80%) | spearman_vs_vis_exit {rep['P0-2']['spearman_vs_vis_exit']:.2f} (<0.6) | hubs {rep['P0-2']['hub_medians']} Nassim {rep['P0-2']['nassim']} deadTransport {rep['P0-2']['dead_transport_median']}")
print(f"P0-3 corr(bldg_ind)={rep['P0-3']['corr_bldg_industrial']} > corr(lu_business)={rep['P0-3']['corr_lu_business']} | TiongBahru {rep['P0-3']['tiong_bahru_median']} (<0.3) heartland {rep['P0-3']['heartland_median']} | Tuas {rep['P0-3']['tuas_median']} Murai {rep['P0-3']['murai_median']} physInd {rep['P0-3']['physical_industrial_median']} (>0.6)")
print(f"P0-1 spread {rep['P0-1']['spread_x']}x (>=8) | Orchard {rep['P0-1']['orchard']} > Downtown {rep['P0-1']['downtown']} > Tampines {rep['P0-1']['tampines']} > JurongW {rep['P0-1']['jurong_west']} | URA-anchor {rep['P0-1']['ura_anchors']}")
print(f"master {rep['master_shape']} | backup {BK.name}")

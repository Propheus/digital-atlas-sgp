#!/usr/bin/env python3
"""
Plexis-Mind — atlas_tools.py: the callable tool/verifier layer over the live Plexis atlas.

ONE module, THREE consumers:
  • tool-calling   — the agent calls these functions for fresh, exact SGP facts
  • distillation   — verify() rejection-samples teacher reasoning (keep only correct chains)
  • GRPO           — verify() is the reward oracle

Loads the atlas parquets once; every tool returns exact current values (update parquets -> fresh).

Tools: resolve_entity, get_metric, compare, rank, filter_entities, aggregate, od, similar,
       places, catalog.   Verifier: verify(model_answer, gold_answer).
"""
import re, math, functools
ATLAS="/home/azureuser/da-sgp/v4"

# ---- metric registry (col or derived) -> (label, unit, normalized?) ----------------
def _f(): pass
DERIVED={"elder_share":("pop_65plus","pop_resident"),"child_share":("pop_0_14","pop_resident"),
         "pop_density":("pop_resident","subzone_area_km2"),"dorm_density":("pop_dorm","subzone_area_km2")}
ALIASES={"density":"pop_density","population":"pop_resident","elderly":"elder_share",
         "walkability":"walkability_score","vibrancy":"vibrancy_index","cafes":"food_cafe","clinics":"health_clinic"}

@functools.lru_cache(maxsize=1)
def _load():
    import pandas as pd
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
        ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    for c in("name","pa","region"): sz[c]=sz[c].astype("string").str.title()
    a=sz.subzone_area_km2.clip(lower=0.01); p=sz.pop_resident.clip(lower=1)
    sz["elder_share"]=sz.pop_65plus/p; sz["child_share"]=sz.pop_0_14/p
    sz["pop_density"]=sz.pop_resident/a; sz["dorm_density"]=sz.pop_dorm/a
    sz=sz.set_index("name",drop=False)
    # OD aggregated to subzone
    us=pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet").set_index("hex8_id")["parent_subzone_name"]
    od=pd.read_parquet(f"{ATLAS}/data/lta_od/hex8_od_matrix.parquet")
    od["o"]=od.origin_hex8.map(us).str.title(); od["d"]=od.dest_hex8.map(us).str.title()
    g=od.dropna(subset=["o","d"]).groupby(["o","d"],as_index=False).trips_wd.sum()
    return sz,g

def _col(metric):
    metric=ALIASES.get(metric,metric)
    sz,_=_load()
    if metric in sz.columns: return metric
    pc=f"pc2_cat_{metric}_count"
    if pc in sz.columns: return pc
    return None

# ---------------------------------------------------------------- TOOLS
def resolve_entity(name):
    sz,_=_load(); t=str(name).title()
    if t in sz.index:
        r=sz.loc[t]; return {"found":True,"entity":t,"scale":"subzone","pa":r["pa"],"region":r["region"]}
    pa=sz[sz.pa==t]
    if len(pa): return {"found":True,"entity":t,"scale":"pa","region":pa.iloc[0]["region"]}
    return {"found":False,"entity":name,"note":"not a subzone/planning-area in the atlas"}

def get_metric(entity, metric):
    sz,_=_load(); c=_col(metric); t=str(entity).title()
    if c is None: return {"error":"metric_not_tracked","metric":metric}
    if t not in sz.index: return {"error":"entity_not_found","entity":entity}
    v=sz.loc[t,c]
    return {"entity":t,"metric":metric,"value":(None if v!=v else round(float(v),4))}

def compare(entities, metric):
    c=_col(metric);
    if c is None: return {"error":"metric_not_tracked","metric":metric}
    sz,_=_load(); out=[]
    for e in entities:
        t=str(e).title()
        if t in sz.index and sz.loc[t,c]==sz.loc[t,c]: out.append({"entity":t,"value":round(float(sz.loc[t,c]),4)})
    out.sort(key=lambda x:-x["value"]); return {"metric":metric,"ranked":out}

def rank(metric, scope=None, n=5, direction="desc", min_pop=2000):
    c=_col(metric)
    if c is None: return {"error":"metric_not_tracked","metric":metric}
    sz,_=_load(); df=sz[sz.pop_resident>=min_pop].dropna(subset=[c])
    if scope: df=df[(df.region==str(scope).title())|(df.pa==str(scope).title())]
    df=df.sort_values(c,ascending=(direction=="asc")).head(n)
    return {"metric":metric,"scope":scope,"results":[{"entity":r["name"],"value":round(float(r[c]),4)} for _,r in df.iterrows()]}

def filter_entities(metric, op, threshold, scope=None, min_pop=2000):
    c=_col(metric)
    if c is None: return {"error":"metric_not_tracked","metric":metric}
    sz,_=_load(); df=sz[sz.pop_resident>=min_pop].dropna(subset=[c])
    if scope: df=df[(df.region==str(scope).title())|(df.pa==str(scope).title())]
    m={">":df[c]>threshold,">=":df[c]>=threshold,"<":df[c]<threshold,"<=":df[c]<=threshold}[op]
    q=df[m]; return {"metric":metric,"op":op,"threshold":threshold,"count":int(len(q)),
                     "entities":list(q.sort_values(c,ascending=(op in("<","<=")))["name"].head(30))}

def aggregate(parent, metric, agg="sum"):
    c=_col(metric)
    if c is None: return {"error":"metric_not_tracked","metric":metric}
    sz,_=_load(); t=str(parent).title()
    sub=sz[(sz.pa==t)|(sz.region==t)]
    if not len(sub): return {"error":"parent_not_found","parent":parent}
    v=getattr(sub[c],agg)(); return {"parent":t,"metric":metric,"agg":agg,"value":round(float(v),4),"n_children":int(len(sub))}

def od(origin, kind="top_dest", n=5):
    _,g=_load(); o=str(origin).title()
    out=g[g.o==o]
    if not len(out): return {"error":"origin_not_found","origin":origin}
    tot=out.trips_wd.sum(); self_=out[out.d==o].trips_wd.sum()
    if kind=="self_containment": return {"origin":o,"self_containment_pct":round(100*self_/max(tot,1),1)}
    if kind=="net_flow":
        inn=g[g.d==o].trips_wd.sum(); return {"origin":o,"inflow":int(inn),"outflow":int(tot),"net":int(inn-tot),
            "role":"importer" if inn>tot*1.05 else "exporter" if inn<tot*0.95 else "balanced"}
    dests=out[out.d!=o].sort_values("trips_wd",ascending=False).head(n)
    return {"origin":o,"top_destinations":[{"dest":r.d,"trips":int(r.trips_wd)} for r in dests.itertuples()]}

def od_between(a, b):
    _,g=_load(); A,B=str(a).title(),str(b).title()
    ab=g[(g.o==A)&(g.d==B)].trips_wd.sum(); ba=g[(g.o==B)&(g.d==A)].trips_wd.sum()
    return {"a":A,"b":B,"a_to_b":int(ab),"b_to_a":int(ba),
            "dominant":A+"->"+B if ab>=ba else B+"->"+A,"ratio":round(max(ab,ba)/max(min(ab,ba),1),2)}

def places(entity, category=None):
    sz,_=_load(); t=str(entity).title()
    if t not in sz.index: return {"error":"entity_not_found"}
    if category:
        c=_col(category) or f"pc2_cat_{category}_count"
        if c not in sz.columns: return {"error":"category_not_tracked","category":category}
        return {"entity":t,"category":category,"count":int(sz.loc[t,c])}
    return {"entity":t,"total_places":int(sz.loc[t,"pc_total"]),
            "dominant":str(sz.loc[t,"pc2_dominant_category"]).replace("_"," ") if "pc2_dominant_category" in sz.columns else None}

def catalog(what="metrics"):
    sz,_=_load()
    if what=="categories": return {"categories":[c.replace("pc2_cat_","").replace("_count","") for c in sz.columns if c.startswith("pc2_cat_")]}
    base=[k for k in DERIVED]+["pop_resident","walkability_score","vibrancy_index","commercial_intensity",
          "bus_stop_count","mrt_station_count","hawker_centre_count","school_count_total","pc_total","nonres_share"]
    return {"metrics":base}

# ---------------------------------------------------------------- VERIFIER (distillation + GRPO)
_NUM=re.compile(r'-?\$?\d[\d,]*\.?\d*%?')
def _nums(s):
    out=[]
    for t in _NUM.findall(s or ""):
        try: out.append(float(t.replace(",","").replace("$","").replace("%","")))
        except: pass
    return out
def _ents(s):  # crude proper-noun grab for entity overlap
    return set(re.findall(r'[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*', s or ""))

def verify(model_answer, gold_answer, kind=""):
    """True if the model's answer matches the deterministic gold. Numeric tolerance + entity overlap.
    Abstention: gold declines -> model must also decline (not emit a fabricated number)."""
    g=_nums(gold_answer); m=_nums(model_answer)
    decline=any(w in (gold_answer or "").lower() for w in ("doesn't","does not","not track","not include","no data","not a subzone","cannot"))
    if kind.startswith("abstain") or decline:
        md=any(w in (model_answer or "").lower() for w in ("doesn't","does not","not track","not include","no data","can't","cannot","unable","not a subzone","i don't have"))
        return md and not m   # declined AND didn't fabricate a number
    if g:  # numeric gold: every gold key number must appear in model answer (within tolerance)
        ok=all(any(abs(a-x)<=max(0.03*abs(x),0.5) for x in m) for a in g)
        return ok
    # non-numeric (e.g. membership/category): require entity overlap
    ge,me=_ents(gold_answer),_ents(model_answer)
    return len(ge & me)>0 if ge else (model_answer or "").strip().lower() in (gold_answer or "").strip().lower() or False

if __name__=="__main__":
    # smoke test
    print("resolve:", resolve_entity("Tampines East"))
    print("resolve fake:", resolve_entity("Manhattan"))
    print("get_metric:", get_metric("Tampines East","elder_share"))
    print("not tracked:", get_metric("Tampines East","crime_rate"))
    print("compare:", compare(["Toa Payoh Central","Bishan East"],"pop_density"))
    print("rank:", rank("elder_share",n=3))
    print("od:", od("Tampines East","top_dest",3))
    print("od net:", od("Tampines East","net_flow"))
    print("filter:", {k:v for k,v in filter_entities("elder_share",">",0.25).items() if k!="entities"})
    print("aggregate:", aggregate("Tampines","bus_stop_count"))
    print("verify num ok:", verify("about 28,140 people/km²","28140 per km²"))
    print("verify num bad:", verify("around 5,000","28140"))
    print("verify abstain ok:", verify("The atlas doesn't track crime rate.","the atlas does not include crime rate",kind="abstain_metric"))
    print("verify abstain bad:", verify("The crime rate is 42.","the atlas does not include crime rate",kind="abstain_metric"))

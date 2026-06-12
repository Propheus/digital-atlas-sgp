#!/usr/bin/env python3
"""
Plexis-Mind — DIVERSE + ABSTENTION generator (the kinds the v2 grind couldn't add).

Five families, all deterministic answers + reasoning traces:
  abstain   — out-of-atlas questions -> honest "the atlas doesn't cover that" (ANTI-HALLUCINATION)
  why       — explain a high/low composite by its actually-high/low component features (grounded association)
  multirank — order 3-4 named entities by a metric (multi-entity reasoning)
  threshold — filter+enumerate: "which subzones have <metric> above X" / "how many have no MRT"
  concept   — definitional: "what does commuter self-containment mean"

Abstention negatives are verified against the REAL vocabulary (326 subzones, 55 categories) so
they are true negatives, not accidental false-negatives.

Usage: python3 generate_reasoning_v3.py --dry-run | --pilot 60 --out-dir raw/v3_pilot | --out-dir raw/v3
"""
import argparse, json, os, sys, time, random, urllib.request, socket
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
random.seed(91); socket.setdefaulttimeout(150)
ATLAS="/home/azureuser/da-sgp/v4"
KEY=open(os.path.expanduser("~/notes/openrouter-llm-build-key.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
MIN_POP=2000

def f0(v):return f"{round(v):,}"
def f3(v):return f"{v:.3f}"
def fp(v):return f"{v:.0%}"
MET={  # metric -> (label, fmt)
 "pop_resident":("resident population",f0),"elder_share":("share of residents 65+",fp),
 "child_share":("share of residents 0–14",fp),"pop_density":("population density per km²",f0),
 "walkability_score":("walkability score",f3),"vibrancy_index":("vibrancy index",f3),
 "commercial_intensity":("commercial intensity",f3),"bus_stop_count":("number of bus stops",f0),
 "mrt_station_count":("number of MRT/LRT stations",f0),"hawker_centre_count":("number of hawker centres",f0),
 "school_count_total":("number of schools",f0),"pc_total":("total places",f0),
 "nonres_share":("non-resident share",fp),"hdb_share":("HDB-housing share",fp),
}
COMPOSITES={
 "vibrancy_index":("vibrancy",["pc_total","pc_diversity","mrt_station_count","bus_stop_count","daily_bus_taps","walk_amenities_400m"]),
 "livability_index":("livability",["walkability_score","walk_amenities_400m","mrt_station_count","school_count_total","hawker_centre_count"]),
 "commercial_intensity":("commercial intensity",["pc_total","bldg_commercial_count","daily_bus_taps","mrt_station_count"]),
 "family_index":("family-friendliness",["school_count_total","pop_hdb_share","hawker_centre_count","walk_amenities_400m"]),
 "density_pressure":("density pressure",["pop_density","bus_stop_count","nonres_share"]),
}
COMP_LABEL={"pc_total":"total places","pc_diversity":"place diversity","mrt_station_count":"MRT/LRT stations",
 "bus_stop_count":"bus stops","daily_bus_taps":"daily bus taps","walk_amenities_400m":"amenities within 400m",
 "walkability_score":"walkability","school_count_total":"schools","hawker_centre_count":"hawker centres",
 "bldg_commercial_count":"commercial buildings","pop_hdb_share":"HDB share","pop_density":"population density",
 "nonres_share":"non-resident share"}
# verified NOT in the atlas
UNTRACKED_CATS=["casinos","embassies","prisons","stadiums","golf courses","theme parks","observatories",
 "cemeteries","lighthouses","vineyards","nightclubs","military camps"]
OOS_METRICS=["crime rate","air-quality (PSI) reading","GDP","unemployment rate","average household income",
 "annual rainfall","average temperature","broadband speed","COE price","electricity consumption",
 "literacy rate","voter turnout"]
NON_SGP=["Manhattan","Shibuya","Bandra","Soho","Kowloon","Brooklyn","Montmartre","Sentul","Chelsea","Roppongi",
 "Mission District","Camden","Andheri","Gangnam","Georgetown (Penang)"]
CONCEPTS={
 "commuter self-containment":"the share of weekday trips that start AND end within the same subzone — high means people live and work locally; low means most residents commute out.",
 "non-resident share":"the fraction of a subzone's population who are not residents (e.g. workers, students, dormitory residents) rather than registered residents.",
 "vibrancy index":"a 0–1 composite of how active/lively an area is, blending place density & diversity, transit, and footfall.",
 "land-use entropy":"a measure (in nats) of how MIXED an area's land uses are — higher means a more even mix of residential, commercial, etc.; lower means dominated by one use.",
 "night-light radiance":"satellite-measured brightness at night, used as a proxy for built-up economic activity.",
 "walkability score":"a 0–1 composite of pedestrian infrastructure, nearby amenities, and transit access.",
 "gross plot ratio (GPR)":"the ratio of a building's total floor area to its land area — a proxy for how intensely a plot is developed.",
}

def load():
    import pandas as pd, numpy as np
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
        ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    for c in("name","pa","region"): sz[c]=sz[c].astype("string").str.title()
    a=sz.subzone_area_km2.clip(lower=0.01); p=sz.pop_resident.clip(lower=1)
    sz["elder_share"]=sz.pop_65plus/p; sz["child_share"]=sz.pop_0_14/p
    sz["pop_density"]=sz.pop_resident/a; sz["hdb_share"]=sz.get("pop_hdb_share",0)
    return sz.set_index("name",drop=False)

def build(caps):
    import pandas as pd, numpy as np
    sz=load(); F=[]
    res=sz[sz.pop_resident>=MIN_POP]; names=list(res["name"]); nameset=set(sz["name"])

    # ---------- ABSTENTION ----------
    for cat in UNTRACKED_CATS:
        for n in random.sample(names,min(caps["abstain_cat"]//len(UNTRACKED_CATS),len(names))):
            F.append(dict(category="reasoning",kind="abstain_category",scale="subzone",entity=n,
                stmt=f"ABSTAIN: The Singapore atlas does NOT track '{cat}' as a place category (it has 55 categories such "
                     f"as cafés, clinics, hawker eateries, supermarkets, schools). A question about {cat} in {n} cannot be "
                     f"answered from it — the correct response is to say the atlas doesn't track {cat}, NOT to invent a number.",
                prov=dict(kind="untracked_category",cat=cat,entity=n)))
    for m in OOS_METRICS:
        for n in random.sample(names,min(caps["abstain_metric"]//len(OOS_METRICS),len(names))):
            F.append(dict(category="reasoning",kind="abstain_metric",scale="subzone",entity=n,
                stmt=f"ABSTAIN: The atlas does NOT include '{m}' data (it covers population, land use, buildings, transit, "
                     f"places, walkability, night-lights, HDB resale, commuter flows). {m} for {n} is out of scope — decline "
                     f"honestly and say it isn't in the atlas, do not fabricate a value.",
                prov=dict(kind="oos_metric",metric=m,entity=n)))
    for nm in NON_SGP*max(1,caps["abstain_place"]//(2*len(NON_SGP))):
        F.append(dict(category="reasoning",kind="abstain_place",scale="subzone",entity=nm,
            stmt=f"ABSTAIN: '{nm}' is NOT a subzone or area in the Singapore atlas (which has 326 named subzones across 5 "
                 f"regions). Any question treating {nm} as a Singapore subzone should be declined — it is not one.",
            prov=dict(kind="fake_place",name=nm)))

    # ---------- WHY (composite explanation) ----------
    compcols={k:[c for c in v[1] if c in res.columns] for k,v in COMPOSITES.items()}
    Z={}
    for k,cols in compcols.items():
        for c in cols:
            if c not in Z: Z[c]=(res[c]-res[c].mean())/(res[c].std(ddof=0)+1e-9)
    for comp,(clabel,_) in COMPOSITES.items():
        if comp not in res.columns: continue
        cols=compcols[comp]; q1,q2=res[comp].quantile([0.34,0.66])
        for _,r in res.iterrows():
            val=r[comp]
            high = val>=q2; low = val<=q1
            if not (high or low): continue
            zc=sorted(cols,key=lambda c: Z[c].get(r["name"],0), reverse=high)[:3]
            drivers="; ".join(f"{COMP_LABEL.get(c,c)} ({MET.get(c,(c,f0))[1](r[c]) if c in MET else (f3(r[c]) if r[c]<10 else f0(r[c]))})" for c in zc)
            F.append(dict(category="reasoning",kind="why_composite",scale="subzone",entity=r["name"],
                stmt=f"ASSOCIATION (not proven cause): {r['name']} has a {'HIGH' if high else 'LOW'} {clabel} score "
                     f"({f3(val)}). Among its components it is correspondingly {'high' if high else 'low'} on: {drivers}. "
                     f"These features are what the {clabel} index is built from, so they explain the score.",
                prov=dict(composite=comp,entity=r["name"],drivers=zc,high=bool(high))))

    # ---------- MULTI-ENTITY RANKING ----------
    metcols=[m for m in MET if m in res.columns]; seen=set(); tries=0
    while len([x for x in F if x["kind"]=="multirank"])<caps["multirank"] and tries<caps["multirank"]*4:
        tries+=1; k=random.choice([3,3,4]); pick=tuple(sorted(random.sample(names,k))); m=random.choice(metcols)
        key=(pick,m)
        if key in seen: continue
        seen.add(key); lab,f=MET[m]
        sub=res.loc[list(pick)].dropna(subset=[m])
        if len(sub)<k: continue
        order=sub.sort_values(m,ascending=False)
        items="; ".join(f"{i+1}. {nm} ({f(v)})" for i,(nm,v) in enumerate(zip(order["name"],order[m])))
        F.append(dict(category="reasoning",kind="multirank",scale="subzone",entity=order.iloc[0]["name"],
            stmt=f"RANKING: ordering {', '.join(pick)} by {lab} (highest first): {items}.",
            prov=dict(entities=list(pick),metric=m)))

    # ---------- THRESHOLD / LIST ----------
    for m in metcols:
        lab,f=MET[m]; sub=res.dropna(subset=[m])
        for qq in (0.75,0.85,0.92,0.95):
            thr=sub[m].quantile(qq)
            for hi in (True,False):
                qual=sub[sub[m]>=thr] if hi else sub[sub[m]<=thr]
                if not (3<=len(qual)<=60): continue
                lst=", ".join(qual.sort_values(m,ascending=not hi)["name"].head(12))
                more=f" (and {len(qual)-12} more)" if len(qual)>12 else ""
                F.append(dict(category="reasoning",kind="threshold_list",scale="subzone",entity=qual.iloc[0]["name"],
                    stmt=f"FILTER: {len(qual)} subzones have {lab} {'at or above' if hi else 'at or below'} {f(thr)}: {lst}{more}.",
                    prov=dict(metric=m,thr=float(thr),above=hi,n=len(qual))))
        # count-with-none
        if m in("mrt_station_count","hawker_centre_count"):
            none=int((sub[m]==0).sum())
            F.append(dict(category="reasoning",kind="threshold_count",scale="subzone",entity="Singapore",
                stmt=f"COUNT: of {len(sub)} residential subzones, {none} have no {lab.replace('number of ','')} at all (count 0).",
                prov=dict(metric=m,zero_count=none)))

    # ---------- CONCEPTUAL ----------
    for term,defn in CONCEPTS.items():
        for _ in range(max(1,caps["concept"]//len(CONCEPTS))):
            F.append(dict(category="reasoning",kind="concept",scale="general",entity=term,
                stmt=f"DEFINITION: '{term}' in the Singapore atlas means: {defn}",
                prov=dict(term=term)))

    random.shuffle(F)
    for i,x in enumerate(F): x["fid"]=i
    return F

SYS=("You convert Singapore atlas items into natural Q&A for a spatial-reasoning model. For EACH item "
 "write ONE question a user would ask and a correct answer. CRITICAL RULES: (1) For ABSTAIN items, the "
 "question should naively ask for the out-of-scope thing, and the ANSWER must HONESTLY decline — say the "
 "atlas doesn't track/include it — and NOT invent any number. This teaches the model to refuse gracefully. "
 "(2) For WHY items, the reasoning must cite the named component features as the explanation; keep the "
 "'association not proven cause' nuance. (3) For RANKING/FILTER, preserve the exact order/list/values. "
 "(4) 'reasoning' = the explicit steps. (5) Vary phrasing. Return a JSON array: "
 "{\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch,model,retries=3):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"ITEMS:\n{txt}"}],"temperature":0.7,"max_tokens":300*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-reasoning-v3","Connection":"close"})
    for a in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=60) as r:d=json.loads(r.read())
            c=d["choices"][0]["message"]["content"];u=d.get("usage",{})
            s=c.find("[");e=c.rfind("]");return (json.loads(c[s:e+1]) if s>=0 else json.loads(c)),u
        except Exception as ex:
            if a==retries-1:return {"error":str(ex)},{}
            time.sleep(1.5*(a+1))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--batch",type=int,default=8);ap.add_argument("--concurrency",type=int,default=12)
    ap.add_argument("--model",default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out-dir",default="raw/v3");ap.add_argument("--shard-size",type=int,default=10000)
    ap.add_argument("--dry-run",action="store_true");ap.add_argument("--pilot",type=int,default=0)
    ap.add_argument("--abstain-cat",type=int,default=4000);ap.add_argument("--abstain-metric",type=int,default=3000)
    ap.add_argument("--abstain-place",type=int,default=900);ap.add_argument("--multirank",type=int,default=16000)
    ap.add_argument("--concept",type=int,default=350)
    args=ap.parse_args()
    caps=dict(abstain_cat=args.abstain_cat,abstain_metric=args.abstain_metric,abstain_place=args.abstain_place,
              multirank=args.multirank,concept=args.concept)
    FA=build(caps)
    from collections import Counter
    c=Counter(f["kind"] for f in FA)
    print(f"[facts] total={len(FA):,}",file=sys.stderr)
    for k,v in sorted(c.items(),key=lambda x:-x[1]): print(f"   {k:20s} {v:,}",file=sys.stderr)
    print(f"[est] ~${len(FA)*70/1e6*0.0983+len(FA)*110/1e6*0.1966:.2f}",file=sys.stderr)
    if args.dry_run:
        for f in FA[:16]: print("  •",f["stmt"][:140],file=sys.stderr)
        return
    if args.pilot: FA=FA[:args.pilot]
    by={f["fid"]:f for f in FA};B=[FA[i:i+args.batch] for i in range(0,len(FA),args.batch)]
    os.makedirs(args.out_dir,exist_ok=True)
    tin=tout=ok=bad=0;sh=0;w=0;t0=time.time();out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
    it=iter(B); fmap={}
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for _ in range(args.concurrency*2):
            b=next(it,None)
            if b is None: break
            fmap[ex.submit(call,b,args.model)]=b
        while fmap:
            done,_=wait(list(fmap),timeout=120,return_when=FIRST_COMPLETED)
            if not done: print(f"  …(waiting) ok={ok:,} {time.time()-t0:.0f}s",file=sys.stderr); continue
            for fut in done:
                b=fmap.pop(fut)
                try: arr,u=fut.result()
                except Exception: arr,u={"error":1},{}
                tin+=u.get("prompt_tokens",0);tout+=u.get("completion_tokens",0)
                if isinstance(arr,dict): bad+=len(b)
                else:
                    for o in arr:
                        if not isinstance(o,dict): bad+=1; continue
                        f=by.get(o.get("fid")); q=str(o.get("question","")).strip(); a=str(o.get("answer","")).strip()
                        if not f or not q or not a: bad+=1; continue
                        rec=dict(category="reasoning",kind=f["kind"],scale=f["scale"],entity=f["entity"],
                            question=q,reasoning=str(o.get("reasoning","")).strip(),answer=a,fact=f["stmt"],provenance=f["prov"])
                        out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                        if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
                nb=next(it,None)
                if nb is not None: fmap[ex.submit(call,nb,args.model)]=nb
            if (ok+bad)%2000<args.batch*args.concurrency:
                out.flush();print(f"  …ok={ok:,} bad={bad} ${tin/1e6*0.0983+tout/1e6*0.1966:.2f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,4),shards=sh+1)))
    print(f"[done] ok={ok:,} bad={bad} ${cost:.2f} {time.time()-t0:.0f}s",file=sys.stderr)

if __name__=="__main__":main()

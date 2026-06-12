#!/usr/bin/env python3
"""
Plexis-Mind — CASUAL v2: rich, human, life-spectrum questions (not just transport/counts).
Covers food, housing/affordability, family-friendliness, vibe (quiet vs lively), shopping,
healthcare, schools, green space, demographics, AND connectivity — plus natural comparisons
and "is X good for families/foodies/young profs?" character questions. All grounded in the atlas.

Usage: python3 generate_casual_v2.py --dry-run | --pilot 50 --out-dir casual/pilot | --n 50000 --out-dir casual/full
"""
import argparse, json, os, sys, time, random, urllib.request, socket
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
random.seed(303); socket.setdefaulttimeout(120)
KEY=open(os.path.expanduser("~/notes/openrouter-llm-build-key.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"; MODEL="deepseek/deepseek-v4-flash"
ATLAS="/home/azureuser/da-sgp/v4"

def fN(v):return f"{round(v):,}"
def fp(v):return f"{round(100*v)}%"
def fd(v):return f"${round(v):,}/m²"
# single-entity life dimensions: col/derived -> (casual label, formatter)
DIMS={
 "pop_resident":("residents",fN),"elder_share":("share of seniors (65+)",fp),
 "child_share":("share of young kids (0–14)",fp),"hdb_share":("share living in HDB flats",fp),
 "hdb_resale_4r_median_psm":("typical 4-room HDB resale price",fd),
 "food_total":("eateries (cafes, restaurants, hawker, etc.)",fN),"cafe":("cafes",fN),
 "restaurant":("restaurants",fN),"hawker":("hawker/food spots",fN),
 "supermarket":("supermarkets",fN),"mall":("shopping malls",fN),"convenience":("convenience stores",fN),
 "clinic":("clinics",fN),"preschool":("preschools",fN),"school_count_total":("schools",fN),
 "gym":("gyms",fN),"park":("parks",fN),"mrt_station_count":("MRT/LRT stations",fN),
 "bus_stop_count":("bus stops",fN),"walkability_score":("walkability (0–1)",lambda v:f"{v:.2f}"),
}
PC={"cafe":"food_cafe","restaurant":"food_restaurant","hawker":"food_hawker","supermarket":"retail_supermarket",
    "mall":"retail_mall","convenience":"retail_convenience","clinic":"health_clinic","preschool":"edu_preschool",
    "gym":"service_fitness","park":"leisure_park"}

def load():
    import pandas as pd
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    sz["name"]=sz["name"].astype("string").str.title(); sz["pa"]=sz["pa"].astype("string").str.title()
    p=sz.pop_resident.clip(lower=1)
    sz["elder_share"]=sz.pop_65plus/p; sz["child_share"]=sz.pop_0_14/p; sz["hdb_share"]=sz.get("pop_hdb_share",0)
    for k,c in PC.items(): sz[k]=sz.get(f"pc2_cat_{c}_count",0)
    sz["food_total"]=sum(sz.get(f"pc2_cat_food_{x}_count",0) for x in ["cafe","restaurant","hawker","bakery","dessert","fast_food","bar"])
    sz["hdb_resale_4r_median_psm"]=sz["hdb_resale_4r_median_psm"].replace(0,float("nan"))
    return sz[sz.pop_resident>=2000].copy()

def terc(sz,col):
    s=sz[col].dropna();
    if len(s)<10: return None
    lo,hi=s.quantile([0.34,0.66]); return lo,hi

def build():
    import pandas as pd, numpy as np
    sz=load(); F=[]; names=list(sz["name"]); idx=sz.set_index("name")
    T={c:terc(sz,c) for c in ["vibrancy_index","family_index","hdb_resale_4r_median_psm","food_total","elder_share","walkability_score","park"]}
    def lvl(name,col,hi_lbl,mid_lbl,lo_lbl):
        v=idx.loc[name,col]; t=T.get(col)
        if pd.isna(v) or not t: return None
        return hi_lbl if v>=t[1] else (lo_lbl if v<=t[0] else mid_lbl)

    # ---- character + suitability (the "what's it like / good for X" questions) ----
    for n in names:
        r=idx.loc[n]
        vibe=lvl(n,"vibrancy_index","lively and buzzing","moderately active","quiet and residential")
        afford=lvl(n,"hdb_resale_4r_median_psm","on the pricier side","mid-range","relatively affordable")
        fam=lvl(n,"family_index","quite family-friendly","okay for families","less geared to families")
        food=lvl(n,"food_total","a great food scene","a decent food scene","limited dining options")
        dom=str(r.get("dominant_use","")).replace("_"," ")
        mrt="has an MRT/LRT station" if r["mrt_station_count"]>0 else "has no MRT (bus only)"
        old="skews older" if r["elder_share"]>=(T["elder_share"][1] if T["elder_share"] else 1) else ("has many young families" if r["child_share"]>r["elder_share"] else "has a mixed age profile")
        parts=[x for x in [vibe,afford,food] if x]
        if parts:
            F.append(dict(kind="char_vibe",entity=n,stmt=f"{n} ({r['pa']}) is {', '.join(parts)}; it {mrt}, is mostly {dom}, and {old}."))
        if fam: F.append(dict(kind="suit_family",entity=n,stmt=f"{n} is {fam} — {int(r['school_count_total'])} schools, {int(r['preschool'])} preschools, {int(r['park'])} parks, and {fp(r['hdb_share'])} live in HDB."))
        if food: F.append(dict(kind="suit_food",entity=n,stmt=f"{n} has {food}: {int(r['food_total'])} eateries including {int(r['cafe'])} cafes, {int(r['restaurant'])} restaurants and {int(r['hawker'])} hawker/food spots."))
        if afford: F.append(dict(kind="suit_afford",entity=n,stmt=f"{n} is {afford} for housing: {fp(r['hdb_share'])} in HDB"+(f", 4-room resale around {fd(r['hdb_resale_4r_median_psm'])}" if pd.notna(r['hdb_resale_4r_median_psm']) else "")+"."))

    # ---- single-dimension life facts (broad — all dims per area) ----
    dimcols=[d for d in DIMS if d in sz.columns]
    SHARE_DIM={"hdb_resale_4r_median_psm","walkability_score","elder_share","child_share","hdb_share"}
    for n in names:
        r=idx.loc[n]
        for d in dimcols:
            lab,f=DIMS[d]; v=r[d]
            if pd.isna(v): continue
            F.append(dict(kind=f"dim_{d}",entity=n,
                stmt=(f"{n}: {lab} is {f(v)}." if d in SHARE_DIM else f"{n} has {f(v)} {lab}.")))

    # ---- casual comparisons (volume driver) — grammatical predicates; numbers only where meaningful ----
    # (col, predicate, show_numbers)
    cmp_dims=[("food_total","has more places to eat",True),("hdb_resale_4r_median_psm","is pricier for housing",True),
              ("family_index","is more family-friendly",False),("vibrancy_index","is livelier",False),
              ("park","has more parks",True),("mrt_station_count","has better MRT/LRT access",True),
              ("pop_resident","is bigger",True),("walkability_score","is more walkable",False),
              ("mall","has more shopping malls",True),("hawker","has more hawker food",True),
              ("elder_share","has an older crowd",False)]
    for _ in range(38000):
        a,b=random.sample(names,2); col,phr,shownum=random.choice(cmp_dims)
        va,vb=idx.loc[a,col],idx.loc[b,col]
        if pd.isna(va) or pd.isna(vb) or va==vb or max(va,vb)==0: continue
        hi=a if va>vb else b
        if shownum: nums=f" ({DIMS.get(col,(col,fN))[1](max(va,vb))} vs {DIMS.get(col,(col,fN))[1](min(va,vb))})"
        elif col=="elder_share": nums=f" ({fp(max(va,vb))} vs {fp(min(va,vb))})"
        else: nums=""
        F.append(dict(kind=f"cmp_{col}",entity=hi,stmt=f"Between {a} and {b}, {hi} {phr}{nums}."))

    random.shuffle(F)
    for i,f in enumerate(F): f["fid"]=i; f["category"]="places" if f["kind"].startswith(("dim_","suit_food","cmp_food","cmp_mall","cmp_hawker")) else "factual"
    return F

SYS=("You turn a Singapore neighbourhood FACT into a SHORT, CASUAL question-and-answer, like a "
 "resident or someone deciding where to live — NOT an analyst. RULES: (1) QUESTION: 4-14 words, natural "
 "and conversational (e.g. 'What's Tampines like?', 'Is Bishan good for families?', 'Cheaper to live in "
 "Yishun or Sengkang?', 'Good food around Clementi?', 'Is Punggol quiet?'). No jargon, no 'subzone', no "
 "'according to the atlas'. (2) ANSWER: 1 short, friendly, helpful sentence using ONLY the fact (light "
 "rounding ok). Natural tone ('Yeah, pretty family-friendly — lots of schools and parks.'). (3) NO reasoning. "
 "Vary the framing. Return a JSON array, one per fact: {\"fid\":int,\"question\":str,\"answer\":str}. JSON only.")

def call(batch, retries=3):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":MODEL,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"FACTS:\n{txt}"}],"temperature":0.85,"max_tokens":130*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-casual2","Connection":"close"})
    for a in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:d=json.loads(r.read())
            c=d["choices"][0]["message"]["content"];u=d.get("usage",{})
            s=c.find("[");e=c.rfind("]");return (json.loads(c[s:e+1]) if s>=0 else json.loads(c)),u
        except Exception as ex:
            if a==retries-1:return {"error":1},{}
            time.sleep(1.5*(a+1))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-dir",default="casual/full");ap.add_argument("--n",type=int,default=0)
    ap.add_argument("--pilot",type=int,default=0);ap.add_argument("--batch",type=int,default=12)
    ap.add_argument("--concurrency",type=int,default=14);ap.add_argument("--shard-size",type=int,default=10000)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    F=build()
    from collections import Counter
    print(f"[facts] total={len(F):,}  {dict(Counter(f['kind'].split('_')[0] for f in F))}",file=sys.stderr)
    if args.dry_run:
        for f in F[:14]: print("  •",f["stmt"][:150],file=sys.stderr)
        return
    if args.pilot: F=F[:args.pilot]
    elif args.n: F=F[:args.n]
    by={f["fid"]:f for f in F}; B=[F[i:i+args.batch] for i in range(0,len(F),args.batch)]
    os.makedirs(args.out_dir,exist_ok=True)
    tin=tout=ok=bad=0;sh=0;w=0;t0=time.time();out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
    it=iter(B); fmap={}
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for _ in range(args.concurrency*2):
            b=next(it,None)
            if b is None: break
            fmap[ex.submit(call,b)]=b
        while fmap:
            done,_=wait(list(fmap),timeout=120,return_when=FIRST_COMPLETED)
            if not done: print(f"  …ok={ok}",file=sys.stderr); continue
            for fut in done:
                b=fmap.pop(fut)
                try: arr,u=fut.result()
                except Exception: arr,u={"error":1},{}
                tin+=u.get("prompt_tokens",0);tout+=u.get("completion_tokens",0)
                if isinstance(arr,dict): bad+=len(b)
                else:
                    for o in arr:
                        if not isinstance(o,dict): bad+=1;continue
                        f=by.get(o.get("fid")); q=str(o.get("question","")).strip(); a=str(o.get("answer","")).strip()
                        if not f or len(q)<4 or len(a)<1: bad+=1;continue
                        rec=dict(category=f["category"],kind="casual_"+f["kind"],scale="subzone",entity=f["entity"],
                                 question=q,reasoning="",answer=a,fact=f["stmt"],register="casual")
                        out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                        if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
                nb=next(it,None)
                if nb is not None: fmap[ex.submit(call,nb)]=nb
            if (ok+bad)%3000<args.batch*args.concurrency:
                print(f"  ok={ok} bad={bad} ${tin/1e6*0.0983+tout/1e6*0.1966:.2f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,3))))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""
Plexis-Mind — PLACES Q&A generator (190K POIs: density, mix, counts, existence, brands).

Families (deterministic answers, LLM only phrases):
  count    — "how many cafes in X" (pc2_cat_*_count)
  existence— "is there a hospital in X" (count>0 / ==0, honest)
  mix      — dominant category, diversity, total places, food-vs-retail balance
  brand    — Singapore-level brand facts (n_locations, top PA, region concentration)
  topn     — which area has the most {cat} (per-capita AND raw)
  compare  — more {cat} in X or Y

Subzone/PA only (uniquely named). Counts framed "in the atlas" (POI snapshot).

Usage: python3 generate_places.py --dry-run | --pilot 60 --out-dir raw/pilot | --out-dir raw/full
"""
import argparse, json, os, sys, time, random, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
random.seed(13)
ATLAS="/home/azureuser/da-sgp/v4"
KEY=open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
MIN_POP=2000

# curated user-facing categories: pc2 col-stem -> plural label
CATS={
 "food_cafe":"cafés","food_restaurant":"restaurants","food_hawker":"hawker-style eateries",
 "food_bar":"bars","food_bakery":"bakeries","food_dessert":"dessert shops","food_fast_food":"fast-food outlets",
 # NB: food_hawker = hawker-style EATERIES (POI count), not gazetted hawker centres (that's hawker_centre_count)
 "health_clinic":"clinics","health_hospital":"hospitals","health_pharmacy":"pharmacies","health_tcm":"TCM halls",
 "retail_supermarket":"supermarkets","retail_mall":"shopping malls","retail_convenience":"convenience stores",
 "retail_apparel":"apparel shops","retail_electronics":"electronics shops",
 "edu_preschool":"preschools","edu_primary_secondary":"primary/secondary schools","edu_tuition":"tuition centres",
 "service_fitness":"gyms/fitness studios","service_beauty":"beauty/salon services","service_automotive":"automotive services",
 "service_pet":"pet services","civic_religious":"places of worship","leisure_park":"parks","res_aged_care":"aged-care facilities",
}
def col(stem): return f"pc2_cat_{stem}_count"

def load():
    import pandas as pd
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
        ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    for c in("name","pa","region"): sz[c]=sz[c].astype("string").str.title()
    # PA aggregation (sum counts)
    countcols=[col(s) for s in CATS if col(s) in sz.columns]+["pc_total","pc_magnets","pop_resident","subzone_area_km2"]
    pa=sz.groupby("pa")[countcols].sum().reset_index()
    pr=sz[["pa","region"]].drop_duplicates("pa"); pa=pa.merge(pr,on="pa")
    pa["name"]=pa["pa"]
    # dominant + diversity recompute at PA from counts
    catcols=[col(s) for s in CATS if col(s) in sz.columns]
    pa["pc_dominant_category"]=pa[catcols].idxmax(axis=1).str.replace("pc2_cat_","").str.replace("_count","")
    sz["pc_dominant_category"]=sz.get("pc2_dominant_category",sz.get("pc_dominant_category"))
    br=pd.read_parquet(f"{ATLAS}/places/brand_rollup.parquet")
    return sz, pa, br

def F(**k): return k
def build(sz, pa, br):
    facts=[]
    def entphrase(r,scale): return f"the subzone {r['name']} ({r['pa']}, {r['region']})" if scale=="subzone" else f"the {r['name']} planning area ({r['region']})"
    for df,scale,word in [(sz,"subzone","subzone"),(pa,"pa","planning area")]:
        a=df["subzone_area_km2"].clip(lower=0.01); p=df["pop_resident"].clip(lower=1)
        # --- counts + existence ---
        for stem,label in CATS.items():
            c=col(stem)
            if c not in df.columns: continue
            for _,r in df.iterrows():
                n=int(r[c])
                if n>0:
                    facts.append(F(category="places",kind=f"count_{stem}",scale=scale,entity=r["name"],
                        stmt=f"In the atlas, {entphrase(r,scale)} has {n} {label}.",
                        prov=dict(file=f"{scale}_place_composition_v2",key=r.get('subzone_c',r['name']),col=c,value=n)))
                elif random.random()<0.12:  # sample the zeros for honest existence
                    facts.append(F(category="places",kind=f"exist_{stem}",scale=scale,entity=r["name"],
                        stmt=f"In the atlas, {entphrase(r,scale)} has no {label} (count 0).",
                        prov=dict(file=f"{scale}_place_composition_v2",key=r.get('subzone_c',r['name']),col=c,value=0)))
        # --- mix: dominant, diversity, total ---
        for _,r in df.iterrows():
            dom=str(r.get("pc_dominant_category","")).replace("_"," ")
            if dom and dom!="None" and not any(w in dom for w in ("other","unmapped","unknown")):
                facts.append(F(category="places",kind="mix_dominant",scale=scale,entity=r["name"],
                    stmt=f"In the atlas, the most common place category in {entphrase(r,scale)} is {dom}, "
                         f"out of {int(r['pc_total'])} total places.",
                    prov=dict(col="pc_dominant_category",key=r.get('subzone_c',r['name']))))
            # food vs retail balance
            food=sum(int(r[col(s)]) for s in CATS if s.startswith("food_") and col(s) in df.columns)
            retail=sum(int(r[col(s)]) for s in CATS if s.startswith("retail_") and col(s) in df.columns)
            if food+retail>=10:
                more="food & beverage" if food>=retail else "retail"
                facts.append(F(category="places",kind="mix_food_retail",scale=scale,entity=r["name"],
                    stmt=f"In {entphrase(r,scale)}, {more} places outnumber the other: {food} F&B vs {retail} retail outlets.",
                    prov=dict(key=r.get('subzone_c',r['name']),food=food,retail=retail)))
        # --- top-N per category (raw + per-capita) ---
        for stem,label in CATS.items():
            c=col(stem)
            if c not in df.columns: continue
            sub=df[df[c]>0].copy()
            if len(sub)<6: continue
            top=sub.nlargest(5,c)
            items="; ".join(f"{i+1}. {x['name']} ({int(x[c])})" for i,(_,x) in enumerate(top.iterrows()))
            facts.append(F(category="places",kind=f"topn_count_{stem}",scale=scale,entity=top.iloc[0]["name"],
                stmt=f"The {word}s with the most {label} (by count) are: {items}.",
                prov=dict(col=c,rank="max_count")))
            subp=sub[sub.pop_resident>=MIN_POP].copy()
            if len(subp)>=6:
                subp["per10k"]=subp[c]/subp.pop_resident*1e4
                topp=subp.nlargest(5,"per10k")
                itemsp="; ".join(f"{i+1}. {x['name']} ({x['per10k']:.1f})" for i,(_,x) in enumerate(topp.iterrows()))
                facts.append(F(category="places",kind=f"topn_per10k_{stem}",scale=scale,entity=topp.iloc[0]["name"],
                    stmt=f"The {word}s with the most {label} per 10,000 residents (≥{MIN_POP:,} residents) are: {itemsp}.",
                    prov=dict(col=c,rank="max_per10k")))
        # --- comparisons (sampled) ---
        names=list(df.index)
        for _ in range(400 if scale=="subzone" else 120):
            stem=random.choice([s for s in CATS if col(s) in df.columns]); c=col(stem)
            a_,b_=random.sample(names,2); A=df.loc[a_]; B=df.loc[b_]
            va,vb=int(A[c]),int(B[c])
            if va==vb: continue
            hi,lo=(A,B) if va>vb else (B,A)
            facts.append(F(category="places",kind=f"cmp_{stem}",scale=scale,entity=hi["name"],
                stmt=f"In the atlas, {hi['name']} has more {CATS[stem]} ({max(va,vb)}) than {lo['name']} ({min(va,vb)}).",
                prov=dict(col=c,a=A['name'],b=B['name'])))
    # --- brand facts (Singapore-level) ---
    for _,r in br.nlargest(120,"n_locations").iterrows():
        facts.append(F(category="places",kind="brand_count",scale="singapore",entity=r["brand_norm"],
            stmt=f"The brand {r['brand_norm']} ({r['primary_category']}) has {int(r['n_locations'])} locations across Singapore; "
                 f"its top planning area is {str(r['top_pa']).title()}.",
            prov=dict(brand=r["brand_norm"],n=int(r["n_locations"]),top_pa=r["top_pa"])))
    random.shuffle(facts)
    for i,f in enumerate(facts): f["fid"]=i
    return facts

SYS=("You convert Singapore atlas FACTS about PLACES (POIs) into natural Q&A for a spatial model. "
 "For EACH fact write ONE question a user would ask and a correct concise answer. RULES: (1) Use ONLY "
 "the fact — never add/alter a number, place, brand, or category; for list facts preserve exact order/values. "
 "(2) 'reasoning' = one short sentence citing the count/category used. (3) Keep the 'in the atlas' framing for "
 "counts (it is a POI snapshot). (4) Vary phrasing. Return a JSON array: "
 "{\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch,model,retries=4):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"FACTS:\n{txt}"}],"temperature":0.7,"max_tokens":220*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-places"})
    for a in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=180) as r:d=json.loads(r.read())
            c=d["choices"][0]["message"]["content"];u=d.get("usage",{})
            s=c.find("[");e=c.rfind("]");return (json.loads(c[s:e+1]) if s>=0 else json.loads(c)),u
        except Exception as ex:
            if a==retries-1:return {"error":str(ex)},{}
            time.sleep(2*(a+1))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--batch",type=int,default=10);ap.add_argument("--concurrency",type=int,default=12)
    ap.add_argument("--model",default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out-dir",default="raw/full");ap.add_argument("--shard-size",type=int,default=5000)
    ap.add_argument("--dry-run",action="store_true");ap.add_argument("--pilot",type=int,default=0)
    args=ap.parse_args()
    sz,pa,br=load(); FA=build(sz,pa,br)
    from collections import Counter
    c=Counter(f["kind"].split("_")[0]+":"+f["scale"] for f in FA)
    print(f"[facts] total={len(FA):,}",file=sys.stderr)
    for k,v in sorted(c.items()): print(f"   {k:18s} {v:,}",file=sys.stderr)
    print(f"[est] ~${len(FA)*60/1e6*0.0983+len(FA)*60/1e6*0.1966:.2f}",file=sys.stderr)
    if args.dry_run:
        for f in FA[:16]: print("  •",f["stmt"][:150],file=sys.stderr)
        return
    if args.pilot: FA=FA[:args.pilot]
    by={f["fid"]:f for f in FA};B=[FA[i:i+args.batch] for i in range(0,len(FA),args.batch)]
    os.makedirs(args.out_dir,exist_ok=True)
    tin=tout=ok=bad=0;sh=0;w=0;t0=time.time();out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs={ex.submit(call,b,args.model):b for b in B}
        for fut in as_completed(futs):
            arr,u=fut.result();tin+=u.get("prompt_tokens",0);tout+=u.get("completion_tokens",0)
            if isinstance(arr,dict):bad+=len(futs[fut]);continue
            for o in arr:
                f=by.get(o.get("fid"))
                if not f or not o.get("question") or not o.get("answer"):bad+=1;continue
                rec=dict(category="places",kind=f["kind"],scale=f["scale"],entity=f["entity"],
                    question=o["question"].strip(),reasoning=o.get("reasoning","").strip(),
                    answer=o["answer"].strip(),fact=f["stmt"],provenance=f["prov"])
                out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
            if (ok+bad)%3000<args.batch:print(f"  …ok={ok:,} ${tin/1e6*0.0983+tout/1e6*0.1966:.3f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,4),shards=sh+1)))
    print(f"[done] ok={ok:,} bad={bad} ${cost:.3f} {time.time()-t0:.0f}s",file=sys.stderr)

if __name__=="__main__":main()

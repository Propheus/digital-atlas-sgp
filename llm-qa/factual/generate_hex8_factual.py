#!/usr/bin/env python3
"""
Plexis-Mind — hex8 FACTUAL generator, keyed by LANDMARK (fixes the name-collision blocker).

Problem solved: 91% of hex8 share a parent-subzone name, so name-keyed hex8 facts were
contradictory. Fix: label each hex8 by its most-reviewed prominent place (unique), and require
that landmark to clear a prominence bar (reviews>=20 or is_magnet) — which also masks out
water/empty/industrial-dead cells automatically. Each hex8 fact is then keyed by a UNIQUE
"area around {landmark}" phrase → no contradictions, and naturally human-readable.

Families: attr (per metric) · compare (same-PA, landmark-vs-landmark).

Usage: python3 generate_hex8_factual.py --dry-run | --pilot 50 --out-dir raw/hex8_pilot | --out-dir raw/hex8
"""
import argparse, json, os, sys, time, random, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
random.seed(23)
ATLAS="/home/azureuser/da-sgp/v4"
KEY=open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
MIN_REVIEWS=20   # landmark prominence bar (also acts as active-area mask)

def f0(v):return f"{round(v):,}"
def f2(v):return f"{v:.2f}"
def f3(v):return f"{v:.3f}"
def fp(v):return f"{v:.0%}"
# col -> (label, formatter, unit)
MET={
 "pop_resident":("resident population",f0,"people"),
 "pop_65plus":("residents aged 65+",f0,"people"),
 "pop_dorm":("migrant-worker dorm population",f0,"people"),
 "nonres_share":("non-resident share",fp,""),
 "bldg_count":("building count",f0,"buildings"),
 "mrt_station_count":("MRT/LRT stations",f0,"stations"),
 "bus_stop_count":("bus stops",f0,"stops"),
 "dist_mrt_m":("distance to nearest MRT/LRT",f0,"m"),
 "walkability_score":("walkability score (0–1)",f3,""),
 "vibrancy_index":("vibrancy index (0–1)",f3,""),
 "commercial_intensity":("commercial intensity (0–1)",f3,""),
 "commercial_activity_index":("commercial activity index",f3,""),
 "nl_2024":("night-light radiance (2024)",f2,""),
 "school_count_total":("schools",f0,"schools"),
 "pc_total":("total places (POIs)",f0,"places"),
 "od_throughput":("commuter throughput (monthly weekday)",f0,"trips"),
 "od_self_containment":("commuter self-containment",fp,""),
 "hdb_resale_4r_median_psm":("median 4-room HDB resale ($/m², proxy)",f0,"$/m²"),
 "daily_bus_taps":("daily bus taps",f0,"taps/day"),
}

def landmarks():
    import pandas as pd
    p=pd.read_parquet(f"{ATLAS}/places/sgp_places_final.parquet")
    p=p[p.name.notna() & (p.name.str.len()>2)].copy()
    p["score"]=p.reviews_count.fillna(0)*(1+p.is_magnet.fillna(False).astype(int))
    best=p.sort_values("score",ascending=False).drop_duplicates("hex8_id")
    best=best[(best.reviews_count.fillna(0)>=MIN_REVIEWS) | (best.is_magnet.fillna(False))]
    return best.set_index("hex8_id")[["name","reviews_count"]]

def load():
    import pandas as pd
    h8=pd.read_parquet(f"{ATLAS}/hex/hex8_all_features.parquet")
    u=pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet")[["hex8_id","parent_subzone_name","parent_pa","parent_region"]]
    h8=h8.drop(columns=[c for c in("parent_subzone_name","parent_pa","parent_region")if c in h8.columns]).merge(u,on="hex8_id")
    lm=landmarks()
    h8=h8.merge(lm,left_on="hex8_id",right_index=True,how="inner")  # only hex8 with a prominent landmark
    for c in("parent_subzone_name","parent_pa","parent_region"): h8[c]=h8[c].astype("string").str.title()
    h8["lm"]=h8["name"].str.strip()
    if "hdb_resale_4r_median_psm" in h8.columns:
        h8["hdb_resale_4r_median_psm"]=h8["hdb_resale_4r_median_psm"].replace(0,float("nan"))  # 0 = no HDB, not "cheap"
    return h8

def area(r): return f"the area around {r['lm']} (in {r['parent_subzone_name']}, {r['parent_pa']})"
def build():
    import pandas as pd
    h8=load(); facts=[]
    print(f"[landmarks] {len(h8)} hex8 with a prominent landmark (of 1191)",file=sys.stderr)
    cols=[c for c in MET if c in h8.columns]
    # attribute facts
    for _,r in h8.iterrows():
        for c in cols:
            v=r[c]
            if pd.isna(v): continue
            lab,f,unit=MET[c]; us=f" {unit}" if unit else ""
            facts.append(dict(category="factual",kind=f"hex8_attr_{c}",scale="hex8",entity=r["lm"],
                stmt=f"In the atlas, {area(r)} has a {lab} of {f(v)}{us}.",
                prov=dict(file="hex8_all_features.parquet",key=r["hex8_id"],col=c,value=float(v))))
    # comparisons: landmark vs landmark within same PA (now unique names)
    for pa,sub in h8.groupby("parent_pa"):
        if len(sub)<2: continue
        idx=list(sub.index)
        for c in cols:
            lab,f,unit=MET[c]
            pairs=random.sample([(a,b) for i,a in enumerate(idx) for b in idx[i+1:]], min(3,len(idx)*(len(idx)-1)//2))
            for a,b in pairs:
                A,B=sub.loc[a],sub.loc[b]
                if pd.isna(A[c]) or pd.isna(B[c]) or A[c]==B[c]: continue
                hi,lo=(A,B) if A[c]>B[c] else (B,A)
                facts.append(dict(category="factual",kind=f"hex8_cmp_{c}",scale="hex8",entity=hi["lm"],
                    stmt=f"In {pa}, the area around {hi['lm']} has a higher {lab} ({f(hi[c])}) than the area around {lo['lm']} ({f(lo[c])}).",
                    prov=dict(col=c,a=A["hex8_id"],b=B["hex8_id"])))
    random.shuffle(facts)
    for i,x in enumerate(facts): x["fid"]=i
    return facts

SYS=("You convert Singapore atlas FACTS about small localities (each identified by a nearby "
 "landmark) into natural Q&A for a spatial model. For EACH fact write ONE question and a concise "
 "correct answer. RULES: (1) Use ONLY the fact — keep the landmark name and the exact value; never "
 "invent. (2) Refer to the place by its landmark (e.g. 'the area around X'). (3) 'reasoning' = one "
 "short sentence citing the value. (4) Keep 'in the atlas' framing. (5) Vary phrasing. Return a JSON "
 "array: {\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch,model,retries=4):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"FACTS:\n{txt}"}],"temperature":0.7,"max_tokens":210*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-hex8"})
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
    ap.add_argument("--out-dir",default="raw/hex8");ap.add_argument("--shard-size",type=int,default=5000)
    ap.add_argument("--dry-run",action="store_true");ap.add_argument("--pilot",type=int,default=0)
    args=ap.parse_args()
    FA=build()
    from collections import Counter
    c=Counter(("cmp" if "cmp" in f["kind"] else "attr") for f in FA)
    print(f"[facts] total={len(FA):,}  {dict(c)}",file=sys.stderr)
    print(f"[est] ~${len(FA)*60/1e6*0.0983+len(FA)*55/1e6*0.1966:.2f}",file=sys.stderr)
    if args.dry_run:
        for f in FA[:14]: print("  •",f["stmt"][:150],file=sys.stderr)
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
                rec=dict(category="factual",kind=f["kind"],scale="hex8",entity=f["entity"],
                    question=o["question"].strip(),reasoning=o.get("reasoning","").strip(),
                    answer=o["answer"].strip(),fact=f["stmt"],provenance=f["prov"])
                out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
            if (ok+bad)%3000<args.batch:print(f"  …ok={ok:,} ${tin/1e6*0.0983+tout/1e6*0.1966:.3f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,4),shards=sh+1)))
    print(f"[done] ok={ok:,} bad={bad} ${cost:.3f} {time.time()-t0:.0f}s",file=sys.stderr)

if __name__=="__main__":main()

#!/usr/bin/env python3
"""
EXHAUSTIVE Factual Q&A generator for the SGP spatial-reasoning LLM.

Covers all of SGP: every entity at subzone / planning-area / region / hex8 scale,
across a curated headline metric registry, in several fact TYPES:
  membership | attribute | superlative | rank_percentile | comparison | profile

Principle (docs/SGP_LLM_QA_STRATEGY.md): Python computes the ground-truth answer
deterministically; DeepSeek-v4-flash only PHRASES Q + concise answer + 1-line reasoning.
The model never invents a number. Every pair ships provenance for QC recompute.

Usage:
  python3 generate_factual_v2.py --dry-run                       # count facts only
  python3 generate_factual_v2.py --scales subzone,pa,region --pilot 60   # quality pilot
  python3 generate_factual_v2.py --scales subzone,pa,region,hex8 \
      --batch 10 --concurrency 10 --shard-size 5000 --out-dir raw/full
"""
import argparse, json, os, sys, time, random, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
random.seed(42)

ATLAS = "/home/azureuser/da-sgp/v4"
KEY = open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# col -> (label, unit_suffix, decimals, kind)  kind: num | ratio | cat | dist
REG = {
 "pop_resident":("resident population","people",0,"num"),
 "pop_0_14":("number of residents aged 0–14","people",0,"num"),
 "pop_15_64":("number of working-age residents (15–64)","people",0,"num"),
 "pop_65plus":("number of residents aged 65 and above","people",0,"num"),
 "pop_dorm":("migrant-worker dormitory population","people",0,"num"),
 "pop_nonresident":("non-resident population","people",0,"num"),
 "nonres_share":("non-resident share of population","",2,"ratio"),
 "pop_hdb_share":("share of residents living in HDB flats","",2,"ratio"),
 "lu_residential_pct":("residential land-use share","",2,"ratio"),
 "lu_commercial_pct":("commercial land-use share","",2,"ratio"),
 "lu_entropy":("land-use mix (entropy)","nats",2,"num"),
 "dominant_use":("dominant land use","",0,"cat"),
 "avg_gpr":("average gross plot ratio","",2,"num"),
 "max_gpr":("maximum gross plot ratio","",2,"num"),
 "bldg_count":("number of buildings","buildings",0,"num"),
 "bldg_residential_count":("number of residential buildings","buildings",0,"num"),
 "bldg_commercial_count":("number of commercial buildings","buildings",0,"num"),
 "bldg_industrial_count":("number of industrial buildings","buildings",0,"num"),
 "road_density_km_per_km2":("road density","km/km²",2,"num"),
 "road_walkable_share":("pedestrian-only road share","",2,"ratio"),
 "dist_expressway_m":("distance to the nearest expressway","m",0,"dist"),
 "mrt_station_count":("number of MRT/LRT stations","stations",0,"num"),
 "bus_stop_count":("number of bus stops","stops",0,"num"),
 "dist_mrt_m":("distance to the nearest MRT/LRT station","m",0,"dist"),
 "dist_bus_m":("distance to the nearest bus stop","m",0,"dist"),
 "daily_train_taps":("daily MRT/LRT taps","taps/day",0,"num"),
 "daily_bus_taps":("daily bus taps","taps/day",0,"num"),
 "walkability_score":("walkability score (0–1)","",3,"num"),
 "walk_amenities_400m":("number of amenities within a 400 m walk","places",0,"num"),
 "ped_path_length_m":("pedestrian path length","m",0,"num"),
 "hawker_centre_count":("number of hawker centres","centres",0,"num"),
 "school_count_total":("number of schools","schools",0,"num"),
 "chas_clinic_count":("number of CHAS clinics","clinics",0,"num"),
 "preschool_count":("number of preschools","preschools",0,"num"),
 "tourist_attraction_count":("number of tourist attractions","attractions",0,"num"),
 "vibrancy_index":("vibrancy index (0–1)","",3,"num"),
 "livability_index":("livability index (0–1)","",3,"num"),
 "commercial_intensity":("commercial intensity (0–1)","",3,"num"),
 "commercial_activity_index":("commercial activity index","",3,"num"),
 "nl_2024":("night-light radiance (2024)","",2,"num"),
 "nl_change_pct":("night-light change 2022→2024","%",1,"num"),
 "hdb_resale_4r_median_psm":("median 4-room HDB resale price","$/m²",0,"num"),
 "od_throughput":("commuter throughput (origin–destination)","trips/day",0,"num"),
 "od_self_containment":("commuter self-containment ratio","",2,"ratio"),
 "od_net_flow":("net commuter flow","trips/day",0,"num"),
 "pc_total":("total number of places (POIs)","places",0,"num"),
 "pc_magnets":("number of demand-magnet places","places",0,"num"),
 "pc_diversity":("place-category diversity","",3,"num"),
 "archetype_label":("urban archetype","",0,"cat"),
}
SCALE_WORD = {"subzone":"subzone","pa":"planning area","region":"region","hex8":"locality"}

def fmt(v, dec, kind):
    if kind=="ratio": return f"{v:.{dec}f}"
    if dec==0: return f"{round(v):,}"
    return f"{v:.{dec}f}"

def unit_str(unit, kind):
    if not unit or kind=="ratio": return ""
    if unit in ("%",): return "%"
    return f" {unit}"

# ---------------------------------------------------------------- entity loaders
def load_entities(scale):
    import pandas as pd
    if scale=="subzone":
        df = pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
        u = pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
            ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
        u.columns=["subzone_c","name","pa","region"]
        df = df.merge(u,on="subzone_c",how="left")
        df["key"]=df["subzone_c"]
    elif scale=="hex8":
        df = pd.read_parquet(f"{ATLAS}/hex/hex8_all_features.parquet")
        ucols=["hex8_id","parent_subzone_name","parent_pa","parent_region","lat","lng"]
        u = pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet")[ucols]
        df = df.drop(columns=[c for c in ucols if c!="hex8_id" and c in df.columns])
        df = df.merge(u,on="hex8_id",how="left")
        df["name"]=df["parent_subzone_name"]; df["pa"]=df["parent_pa"]; df["region"]=df["parent_region"]
        df["key"]=df["hex8_id"]
    elif scale in ("pa","region"):
        h8 = pd.read_parquet(f"{ATLAS}/hex/hex8_all_features.parquet")
        u = pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet")[["hex8_id","parent_pa","parent_region"]]
        h8 = h8.drop(columns=[c for c in ("parent_pa","parent_region") if c in h8.columns])
        h8 = h8.merge(u,on="hex8_id",how="left")
        gcol = "parent_pa" if scale=="pa" else "parent_region"
        agg = {}
        for c,(lab,un,dec,kind) in REG.items():
            if c not in h8.columns or kind in ("cat",): continue
            agg[c] = "mean" if kind in ("ratio","num") and ("score" in c or "index" in c or "share" in c or "_pct" in c or kind=="ratio" or "density" in c or "gpr" in c or "entropy" in c or "diversity" in c or c.startswith("dist_") or c.endswith("_psm") or c.startswith("nl_")) else "sum"
        df = h8.groupby(gcol).agg(agg).reset_index()
        df["name"]=df[gcol]; df["region"]=df[gcol] if scale=="region" else None; df["pa"]=df[gcol] if scale=="pa" else None
        df["key"]=df[gcol]
        # region for PA
        if scale=="pa":
            pr = h8[["parent_pa","parent_region"]].drop_duplicates("parent_pa").set_index("parent_pa")["parent_region"]
            df["region"]=df["parent_pa"].map(pr)
    for col in ("name","pa","region"):
        if col in df.columns:
            df[col]=df[col].astype("string").str.title()
    return df

# ---------------------------------------------------------------- fact builders
def ent_phrase(scale, r):
    w = SCALE_WORD[scale]
    if scale=="subzone": return f"the subzone {r['name']} ({r['pa']}, {r['region']})"
    if scale=="pa":      return f"the {r['name']} planning area ({r['region']})"
    if scale=="region":  return f"the {r['name']} of Singapore"
    if scale=="hex8":    return f"the locality around {r['name']} (lat {r['lat']:.3f}, lng {r['lng']:.3f}), in {r['pa']}"

def metrics_for(df):
    return [c for c in REG if c in df.columns]

def build_facts(scales, caps):
    import pandas as pd
    facts=[]
    cache={}
    for scale in scales:
        df = load_entities(scale); cache[scale]=df
        cols = metrics_for(df)
        wlabel = SCALE_WORD[scale]
        # --- membership (admin scales + hex8) ---
        if scale in ("subzone","hex8","pa"):
            for _,r in df.iterrows():
                if scale=="pa":
                    stmt=f"The {r['name']} planning area is in the {r['region']} of Singapore."
                    col="parent_region"
                else:
                    stmt=f"{ent_phrase(scale,r).capitalize()} is in the {r['pa']} planning area, {r['region']}."
                    col="parent_pa"
                facts.append(dict(kind=f"membership_{scale}",scale=scale,entity=r["name"],
                    stmt=stmt,prov=dict(file=f"{scale}_all_features.parquet",key=r["key"],col=col)))
        # --- attribute ---
        for _,r in df.iterrows():
            for c in cols:
                lab,un,dec,kind = REG[c]
                v=r[c]
                if pd.isna(v): continue
                if kind=="cat":
                    val=str(v).replace("_"," ")
                    stmt=f"According to the Singapore atlas, {ent_phrase(scale,r)} has a {lab} of {val}."
                else:
                    stmt=f"According to the Singapore atlas, {ent_phrase(scale,r)} has a {lab} of {fmt(v,dec,kind)}{unit_str(un,kind)}."
                facts.append(dict(kind=f"attr_{c}",scale=scale,entity=r["name"],
                    stmt=stmt,prov=dict(file=f"{scale}_all_features.parquet",key=r["key"],col=c,
                                        value=(None if kind=="cat" else float(v)))))
        # --- superlative + rank within scopes ---
        scope_cols = {"subzone":["__all__","region","pa"],"hex8":["__all__","region","pa"],
                      "pa":["__all__","region"],"region":["__all__"]}[scale]
        for c in cols:
            lab,un,dec,kind = REG[c]
            if kind=="cat": continue
            for sc in scope_cols:
                if sc=="__all__":
                    groups=[("Singapore",df)]
                else:
                    groups=[(g,sub) for g,sub in df.groupby(sc) if len(sub)>=3 and g and str(g)!="None"]
                for gname,sub in groups:
                    sub2=sub.dropna(subset=[c])
                    if len(sub2)<3: continue
                    top=sub2.loc[sub2[c].idxmax()]; bot=sub2.loc[sub2[c].idxmin()]
                    scope_txt = f"in {gname}" if sc=="__all__" else (f"in the {gname} planning area" if sc=="pa" else f"in {gname}")
                    unit=unit_str(un,kind)
                    facts.append(dict(kind=f"max_{c}",scale=scale,entity=top["name"],
                        stmt=f"Among {wlabel}s {scope_txt}, {top['name']} has the highest {lab} ({fmt(top[c],dec,kind)}{unit}).",
                        prov=dict(file=f"{scale}_all_features.parquet",key=top["key"],col=c,scope=str(gname),rank="max")))
                    facts.append(dict(kind=f"min_{c}",scale=scale,entity=bot["name"],
                        stmt=f"Among {wlabel}s {scope_txt}, {bot['name']} has the lowest {lab} ({fmt(bot[c],dec,kind)}{unit}).",
                        prov=dict(file=f"{scale}_all_features.parquet",key=bot["key"],col=c,scope=str(gname),rank="min")))
        # --- comparison (same parent, sampled) ---
        if scale in ("subzone","hex8"):
            par = "pa" if scale=="subzone" else "pa"
            for c in cols:
                lab,un,dec,kind=REG[c]
                if kind=="cat": continue
                for g,sub in df.groupby(par):
                    sub=sub.dropna(subset=[c])
                    if len(sub)<2 or not g or str(g)=="None": continue
                    pairs=list(zip(sub.itertuples(),list(sub.itertuples())[1:]))
                    random.shuffle(pairs); pairs=pairs[:caps["cmp_per_group"]]
                    for a,b in pairs:
                        va=getattr(a,c); vb=getattr(b,c)
                        hi,lo=(a,b) if va>=vb else (b,a)
                        facts.append(dict(kind=f"cmp_{c}",scale=scale,entity=getattr(hi,"name"),
                            stmt=f"Comparing {wlabel}s in {str(g).title()}: {getattr(hi,'name')} has a higher {lab} "
                                 f"({fmt(max(va,vb),dec,kind)}{unit_str(un,kind)}) than {getattr(lo,'name')} "
                                 f"({fmt(min(va,vb),dec,kind)}{unit_str(un,kind)}).",
                            prov=dict(file=f"{scale}_all_features.parquet",col=c,a=getattr(a,'key'),b=getattr(b,'key'))))
        # --- multi-metric profile (subzone/pa) ---
        if scale in ("subzone","pa"):
            prof=[m for m in ["pop_resident","dominant_use","walkability_score","mrt_station_count","hawker_centre_count","vibrancy_index"] if m in df.columns]
            for _,r in df.iterrows():
                parts=[]
                for c in prof:
                    lab,un,dec,kind=REG[c]
                    if pd.isna(r[c]): continue
                    parts.append(f"{lab} {('of '+str(r[c]).replace('_',' ')) if kind=='cat' else '= '+fmt(r[c],dec,kind)+unit_str(un,kind)}")
                if len(parts)>=3:
                    facts.append(dict(kind="profile",scale=scale,entity=r["name"],
                        stmt=f"Profile of {ent_phrase(scale,r)}: " + "; ".join(parts) + ".",
                        prov=dict(file=f"{scale}_all_features.parquet",key=r["key"],cols=prof)))
    random.shuffle(facts)
    for i,f in enumerate(facts): f["fid"]=i
    return facts

# ---------------------------------------------------------------- phrasing
SYS=("You convert Singapore atlas FACTS into natural-language training Q&A for a spatial-"
 "reasoning model. For EACH fact write ONE question a real user would ask and a concise, "
 "correct answer. RULES: (1) Use ONLY the information in the fact — never add a number, "
 "place, or claim not present. (2) Answer must be directly supported by the fact. "
 "(3) 'reasoning' = one short sentence naming the value/relationship used. (4) Vary phrasing; "
 "some direct, some conversational; for comparison facts ask which is higher/lower. Return a "
 "JSON array, one object per fact: {\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch, model, retries=4):
    facts_txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"FACTS:\n{facts_txt}"}],
        "temperature":0.7,"max_tokens":200*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"sgp-llm-qa-factual"})
    for a in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=180) as r: d=json.loads(r.read())
            txt=d["choices"][0]["message"]["content"]; usage=d.get("usage",{})
            s=txt.find("["); e=txt.rfind("]")
            return (json.loads(txt[s:e+1]) if s>=0 else json.loads(txt)), usage
        except Exception as ex:
            if a==retries-1: return {"error":str(ex)}, {}
            time.sleep(2*(a+1))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scales",default="subzone,pa,region,hex8")
    ap.add_argument("--batch",type=int,default=10)
    ap.add_argument("--concurrency",type=int,default=10)
    ap.add_argument("--model",default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out-dir",default="raw/full")
    ap.add_argument("--shard-size",type=int,default=5000)
    ap.add_argument("--cmp-per-group",type=int,default=4)
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--pilot",type=int,default=0)
    args=ap.parse_args()

    scales=[s.strip() for s in args.scales.split(",")]
    facts=build_facts(scales, dict(cmp_per_group=args.cmp_per_group))
    from collections import Counter
    grp=Counter(("_".join(f["kind"].split("_")[:1]))+":"+f["scale"] for f in facts)
    print(f"[facts] total={len(facts):,}",file=sys.stderr)
    for k,v in sorted(grp.items()): print(f"   {k:28s} {v:,}",file=sys.stderr)
    est_in=len(facts)*55; est_out=len(facts)*60
    print(f"[est cost] ~${est_in/1e6*0.0983+est_out/1e6*0.1966:.2f} for {len(facts):,} pairs",file=sys.stderr)
    if args.dry_run: return
    if args.pilot: facts=facts[:args.pilot]

    by={f["fid"]:f for f in facts}
    batches=[facts[i:i+args.batch] for i in range(0,len(facts),args.batch)]
    os.makedirs(args.out_dir,exist_ok=True)
    tin=tout=ok=bad=0; t0=time.time(); shard=0; written=0
    out=open(f"{args.out_dir}/shard_{shard:03d}.jsonl","w")
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs={ex.submit(call,b,args.model):b for b in batches}
        for fut in as_completed(futs):
            arr,usage=fut.result()
            tin+=usage.get("prompt_tokens",0); tout+=usage.get("completion_tokens",0)
            if isinstance(arr,dict): bad+=len(futs[fut]); continue
            for o in arr:
                f=by.get(o.get("fid"))
                if not f or not o.get("question") or not o.get("answer"): bad+=1; continue
                rec=dict(category="factual",kind=f["kind"],scale=f["scale"],entity=f["entity"],
                    question=o["question"].strip(),reasoning=o.get("reasoning","").strip(),
                    answer=o["answer"].strip(),fact=f["stmt"],provenance=f["prov"])
                out.write(json.dumps(rec,ensure_ascii=False)+"\n"); ok+=1; written+=1
                if written>=args.shard_size:
                    out.close(); shard+=1; written=0; out=open(f"{args.out_dir}/shard_{shard:03d}.jsonl","w")
            if (ok+bad)%2000<args.batch:
                c=tin/1e6*0.0983+tout/1e6*0.1966
                print(f"  …ok={ok:,} bad={bad} cost=${c:.3f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close()
    cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,prompt_tok=tin,compl_tok=tout,cost_usd=round(cost,4),
        shards=shard+1,out_dir=args.out_dir)))
    print(f"[done] ok={ok:,} bad={bad} cost=${cost:.3f} {time.time()-t0:.0f}s -> {args.out_dir}",file=sys.stderr)

if __name__=="__main__": main()

#!/usr/bin/env python3
"""
Plexis-Mind — REASONING Q&A generator (makes the model think, not just recall).

Four families, all with deterministic Python answers + multi-step reasoning traces:
  topn   — "which N areas have the most/least X" (NORMALIZED: share/density/per-capita)
  compare— "X vs Y on metric" (which higher, by how much, ratio)
  odflow — "where do weekday commuters from X go / self-containment / net flow" (OD matrix)
  rank   — "where does X rank on metric" (#k of N, percentile)

Discipline baked in:
  * concentration questions ALWAYS use normalized measures, never raw counts
  * affluence = PA-resolution proxy (education/occupation/housing), nvp_low_n excluded
  * OD is weekday, all-commuter aggregate (NOT dorm-tagged) — stated in reasoning
The LLM only PHRASES; it must preserve rankings/values exactly.

Usage:
  python3 generate_reasoning.py --dry-run
  python3 generate_reasoning.py --pilot 60 --out-dir raw/pilot
  python3 generate_reasoning.py --families topn,compare,odflow,rank --out-dir raw/full
"""
import argparse, json, os, sys, time, random, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
random.seed(7)
ATLAS="/home/azureuser/da-sgp/v4"
KEY=open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
MIN_POP=2000   # denominator floor for share/per-capita metrics
def ordinal(n):
    return f"{n}{'th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"

# ---- normalized stat metrics at SUBZONE: col-or-derived -> (label, kind, better, fmt)
def fmt_pct(v): return f"{100*v:.1f}%"
def fmt_num(v): return f"{v:,.0f}"
def fmt_d2(v):  return f"{v:.2f}"
def fmt_d3(v):  return f"{v:.3f}"
SUB_METRICS={
 "elder_share":   ("share of residents aged 65+","share","high",fmt_pct),
 "child_share":   ("share of residents aged 0–14","share","high",fmt_pct),
 "nonres_share":  ("non-resident share of population","share","high",fmt_pct),
 "hdb_share":     ("share of residents in HDB flats","share","high",fmt_pct),
 "private_proxy": ("share of residents NOT in HDB (private-housing proxy)","share","high",fmt_pct),
 "pop_density":   ("resident population density (per km²)","density","high",fmt_num),
 "dorm_density":  ("migrant-worker dorm density (per km²)","density","high",fmt_num),
 "place_density": ("place (POI) density (per km²)","density","high",fmt_num),
 "busstop_density":("bus-stop density (per km²)","density","high",fmt_d2),
 "hawker_per_100k":("hawker centres per 100k residents","per-capita","high",fmt_d2),
 "school_per_100k":("schools per 100k residents","per-capita","high",fmt_d2),
 "walkability_score":("walkability score (0–1)","index","high",fmt_d3),
 "vibrancy_index":("vibrancy index (0–1)","index","high",fmt_d3),
 "commercial_intensity":("commercial intensity (0–1)","index","high",fmt_d3),
 "hdb_resale_4r_median_psm":("median 4-room HDB resale price ($/m², wealth proxy)","proxy","high",fmt_num),
}
PA_METRICS={  # personas = PA resolution; exclude nvp_low_n
 "nvp_affluence_idx":("affluence proxy index (education+occupation+housing)","proxy","high",fmt_d3),
 "nvp_pct_univ":("share of adults university-educated","share","high",fmt_pct),
 "nvp_occ_professional":("share in professional occupations","share","high",fmt_pct),
 "nvp_median_age":("median resident age","raw","high",fmt_d2),
 "nvp_pct_age_55plus":("share of adults aged 55+","share","high",fmt_pct),
}

def load():
    import pandas as pd, numpy as np
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
        ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    for c in ("name","pa","region"): sz[c]=sz[c].astype("string").str.title()
    a=sz["subzone_area_km2"].clip(lower=0.01); p=sz["pop_resident"].clip(lower=1)
    sz["elder_share"]=sz.pop_65plus/p; sz["child_share"]=sz.pop_0_14/p
    sz["hdb_share"]=sz.get("pop_hdb_share",0); sz["private_proxy"]=1-sz.get("pop_hdb_share",0)
    sz["pop_density"]=sz.pop_resident/a; sz["dorm_density"]=sz.pop_dorm/a
    sz["place_density"]=sz.get("pc_total",0)/a; sz["busstop_density"]=sz.bus_stop_count/a
    sz["hdb_resale_4r_median_psm"]=sz["hdb_resale_4r_median_psm"].replace(0,float("nan"))  # 0 = no HDB, not "cheap"
    sz["hawker_per_100k"]=sz.hawker_centre_count/p*1e5; sz["school_per_100k"]=sz.school_count_total/p*1e5
    # PA personas (pop-weighted from hex8), low_n excluded
    h8=pd.read_parquet(f"{ATLAS}/hex/hex8_all_features.parquet")
    u8=pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet")[["hex8_id","parent_pa","parent_region"]]
    h8=h8.drop(columns=[c for c in("parent_pa","parent_region")if c in h8.columns]).merge(u8,on="hex8_id")
    good=h8[h8.get("nvp_low_n",1)==0] if "nvp_low_n" in h8.columns else h8
    rows=[]
    for pa,d in good.groupby("parent_pa"):
        w=d.pop_resident.clip(lower=0); sw=max(w.sum(),1); rec={"pa":str(pa).title(),"region":str(d.parent_region.iloc[0]).title()}
        for c in PA_METRICS:
            if c in d.columns: rec[c]=float((d[c]*w).sum()/sw)
        rows.append(rec)
    pa=pd.DataFrame(rows)
    # OD aggregated hex8 -> subzone (weekday)
    m=u8.set_index("hex8_id")["parent_pa"]  # placeholder; need subzone name
    us=pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet").set_index("hex8_id")["parent_subzone_name"]
    od=pd.read_parquet(f"{ATLAS}/data/lta_od/hex8_od_matrix.parquet")
    od["o"]=od.origin_hex8.map(us).str.title(); od["d"]=od.dest_hex8.map(us).str.title()
    od=od.dropna(subset=["o","d"])
    g=od.groupby(["o","d"],as_index=False).agg(trips=("trips_wd","sum"),am=("trips_am","sum"),pm=("trips_pm","sum"))
    return sz,pa,g

# ---------------- fact builders -----------------
def topn_facts(df, metrics, scale_word, n=5):
    facts=[]
    for col,(label,kind,better,f) in metrics.items():
        if col not in df.columns: continue
        sub=df.dropna(subset=[col]).copy()
        if kind in("share","per-capita","density","index","proxy") and "pop_resident" in sub.columns:
            sub=sub[sub.pop_resident>=MIN_POP]
        if len(sub)<8: continue
        for hi,word in [(True,"highest"),(False,"lowest")]:
            top=sub.sort_values(col,ascending=not hi).head(n)
            if top[col].nunique()<=1: continue   # skip degenerate all-equal ties (e.g. lowest dorm density = all 0)
            items="; ".join(f"{i+1}. {r['name'] if 'name' in r else r['pa']} ({f(r[col])})" for i,(_,r) in enumerate(top.iterrows()))
            method=("ranked by "+label+ (f", among {scale_word}s with ≥{MIN_POP:,} residents" if kind in('share','per-capita','density','index','proxy') else ""))
            facts.append(dict(category="reasoning",kind=f"top{n}_{word}_{col}",scale=scale_word,
                entity=top.iloc[0]['name' if 'name' in top.columns else 'pa'],
                stmt=f"The {n} {scale_word}s in Singapore with the {word} {label} are: {items}. (Method: {method}.)",
                prov=dict(col=col,rank=word,n=n,method=method)))
    return facts

def compare_facts(df, metrics, scale_word, anchors, n_pairs=600):
    facts=[]; rows=df.dropna(subset=["name"]) if "name" in df.columns else df
    ids=list(rows.index)
    pairs=set()
    # anchored pairs (e.g. Tampines East vs others) + random region pairs
    namecol="name" if "name" in df.columns else "pa"
    for a in anchors:
        ar=rows[rows[namecol].str.contains(a,case=False,na=False)]
        if len(ar)==0: continue
        ai=ar.index[0]
        for bi in random.sample(ids,min(20,len(ids))):
            if bi!=ai: pairs.add(tuple(sorted((ai,bi))))
    while len(pairs)<n_pairs and len(ids)>1:
        a,b=random.sample(ids,2); pairs.add(tuple(sorted((a,b))))
    for ai,bi in list(pairs)[:n_pairs]:
        A=rows.loc[ai]; B=rows.loc[bi]; col=random.choice([c for c in metrics if c in df.columns])
        label,kind,better,f=metrics[col]
        if kind in("share","per-capita","density","index","proxy") and min(A.get("pop_resident",1e9),B.get("pop_resident",1e9))<MIN_POP: continue
        va,vb=A[col],B[col]
        if va!=va or vb!=vb: continue
        hi,lo=(A,B) if va>=vb else (B,A); hv,lv=max(va,vb),min(va,vb)
        ratio=hv/lv if lv else float('inf')
        show_ratio = kind in ("share","density","per-capita","proxy","index") and ratio<50 and lv
        facts.append(dict(category="reasoning",kind=f"cmp_{col}",scale=scale_word,entity=hi[namecol],
            stmt=f"Comparing {A[namecol]} and {B[namecol]} on {label}: {hi[namecol]} is higher ({f(hv)}) "
                 f"than {lo[namecol]} ({f(lv)})"+(f", about {ratio:.1f}× as much" if show_ratio else "")+".",
            prov=dict(col=col,a=A[namecol],b=B[namecol],va=float(va),vb=float(vb))))
    return facts

def odflow_facts(g, n=5):
    import pandas as pd
    facts=[]
    out=g.groupby("o").trips.sum(); inn=g.groupby("d").trips.sum()
    self_=g[g.o==g.d].set_index("o").trips
    am=g.groupby("o").am.sum(); pm=g.groupby("o").pm.sum()
    origins=[o for o in out.index if out[o]>=500]
    for o in origins:
        dests=g[(g.o==o)&(g.d!=o)].sort_values("trips",ascending=False).head(n)
        if len(dests)<3: continue
        items="; ".join(f"{i+1}. {r.d} ({int(r.trips):,})" for i,r in enumerate(dests.itertuples()))
        facts.append(dict(category="patterns",kind="od_top_dest",scale="subzone",entity=o,
            stmt=f"By total weekday trips over a month (LTA OD, Apr 2026), the top {n} destinations for "
                 f"commuters travelling from {o} are: {items}. (All commuters — not dorm-specific.)",
            prov=dict(origin=o,kind="od_top_dest")))
        sc=100*self_.get(o,0)/max(out.get(o,1),1)
        facts.append(dict(category="patterns",kind="od_self_containment",scale="subzone",entity=o,
            stmt=f"{o} has a commuter self-containment of {sc:.0f}% — that share of weekday trips starting there also end within {o} (LTA OD, monthly).",
            prov=dict(origin=o,self_pct=round(sc,1))))
        net=inn.get(o,0)-out.get(o,0); tot=inn.get(o,0)+out.get(o,0); rr=net/max(tot,1)
        if abs(rr)<0.05:
            stmt=(f"{o} has roughly balanced commuter flow: ~{int(inn.get(o,0)):,} monthly weekday trips arrive "
                  f"vs ~{int(out.get(o,0)):,} that leave (net {int(net):+,}, within 5% — neither a strong origin nor destination).")
            role="balanced"
        else:
            role="net importer of commuters (a job/destination hub)" if net>0 else "net exporter of commuters (a residential/origin area)"
            stmt=(f"{o} is a {role}: ~{int(inn.get(o,0)):,} monthly weekday trips arrive vs "
                  f"~{int(out.get(o,0)):,} that leave (net {int(net):+,}, {abs(rr)*100:.0f}% imbalance).")
        facts.append(dict(category="patterns",kind="od_net_flow",scale="subzone",entity=o,stmt=stmt,
            prov=dict(origin=o,inflow=int(inn.get(o,0)),outflow=int(out.get(o,0)),role=role)))
    return facts

def rank_facts(df, metrics, scale_word):
    facts=[]; namecol="name" if "name" in df.columns else "pa"
    for col,(label,kind,better,f) in metrics.items():
        if col not in df.columns: continue
        sub=df.dropna(subset=[col]).copy()
        if kind in("share","per-capita","density","index","proxy") and "pop_resident" in sub.columns: sub=sub[sub.pop_resident>=MIN_POP]
        if len(sub)<10: continue
        sub=sub.sort_values(col,ascending=False).reset_index(drop=True); N=len(sub)
        for k in random.sample(range(N),min(40,N)):
            r=sub.iloc[k]; rank=k+1
            pctile=round(100*(N-rank)/(N-1)) if N>1 else 100   # higher value -> higher percentile
            band=("near the top" if pctile>=90 else "the upper range" if pctile>=60 else
                  "mid-range" if pctile>40 else "the lower range" if pctile>10 else "near the bottom")
            facts.append(dict(category="reasoning",kind=f"rank_{col}",scale=scale_word,entity=r[namecol],
                stmt=f"Ranked by {label} (highest first), {r[namecol]} is #{rank} of {N} {scale_word}s "
                     f"({f(r[col])}) — the {ordinal(pctile)} percentile, {band}.",
                prov=dict(col=col,rank=rank,of=N,value=float(r[col]),pctile=pctile)))
    return facts

def build(families):
    sz,pa,g=load()
    F=[]
    if "topn" in families:   F+=topn_facts(sz,SUB_METRICS,"subzone")+topn_facts(pa,PA_METRICS,"planning area")
    if "compare" in families:F+=compare_facts(sz,SUB_METRICS,"subzone",anchors=["Tampines East","Toa Payoh","Bishan","Jurong"])+compare_facts(pa,PA_METRICS,"planning area",anchors=["Tampines","Bedok"],n_pairs=200)
    if "odflow" in families: F+=odflow_facts(g)
    if "rank" in families:   F+=rank_facts(sz,SUB_METRICS,"subzone")+rank_facts(pa,PA_METRICS,"planning area")
    random.shuffle(F)
    for i,f in enumerate(F): f["fid"]=i
    return F

# ---------------- phrasing -----------------
SYS=("You convert Singapore atlas FACTS into natural-language training Q&A for a spatial-"
 "REASONING model. For EACH fact write ONE question a real user/analyst would ask and a "
 "correct answer. RULES: (1) Use ONLY the fact — never add/alter a number, name, rank, or "
 "ordering. For list facts, PRESERVE the exact ranking and values. (2) 'reasoning' = 1–2 short "
 "sentences showing HOW the answer follows (the comparison, the normalization, the ranking, "
 "the flow) — this teaches reasoning, so make it explicit. (3) Keep any caveat the fact states "
 "(e.g. 'proxy', 'weekday', 'not dorm-specific'). (4) Vary phrasing. Return a JSON array, one "
 "object per fact: {\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch,model,retries=4):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"FACTS:\n{txt}"}],"temperature":0.7,"max_tokens":260*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-reasoning"})
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
    ap.add_argument("--families",default="topn,compare,odflow,rank")
    ap.add_argument("--batch",type=int,default=8); ap.add_argument("--concurrency",type=int,default=12)
    ap.add_argument("--model",default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out-dir",default="raw/full"); ap.add_argument("--shard-size",type=int,default=5000)
    ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--pilot",type=int,default=0)
    args=ap.parse_args()
    fams=[x.strip() for x in args.families.split(",")]
    F=build(fams)
    from collections import Counter
    c=Counter(f["kind"].split("_")[0]+":"+f["category"] for f in F)
    print(f"[facts] total={len(F):,}",file=sys.stderr)
    for k,v in sorted(c.items()): print(f"   {k:22s} {v:,}",file=sys.stderr)
    print(f"[est] ~${len(F)*70/1e6*0.0983+len(F)*90/1e6*0.1966:.2f}",file=sys.stderr)
    if args.dry_run:
        for f in F[:14]: print("  •",f["stmt"][:150],file=sys.stderr)
        return
    if args.pilot: F=F[:args.pilot]
    by={f["fid"]:f for f in F}; B=[F[i:i+args.batch] for i in range(0,len(F),args.batch)]
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
                rec=dict(category=f["category"],kind=f["kind"],scale=f["scale"],entity=f["entity"],
                    question=o["question"].strip(),reasoning=o.get("reasoning","").strip(),
                    answer=o["answer"].strip(),fact=f["stmt"],provenance=f["prov"])
                out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
            if (ok+bad)%2000<args.batch:print(f"  …ok={ok:,} bad={bad} ${tin/1e6*0.0983+tout/1e6*0.1966:.3f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,4),shards=sh+1,out_dir=args.out_dir)))
    print(f"[done] ok={ok:,} bad={bad} ${cost:.3f} {time.time()-t0:.0f}s",file=sys.stderr)

if __name__=="__main__":main()

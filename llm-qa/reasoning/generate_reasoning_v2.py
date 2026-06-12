#!/usr/bin/env python3
"""
Plexis-Mind — STRONG REASONING generator (multi-hop / multi-constraint / OD / analogy).

Goes beyond single-cell lookups. Every answer is computed deterministically in Python; the
LLM emits an explicit multi-STEP reasoning chain. Families:

  od_flow      — directed corridor volume A->B (weekday/month)
  od_asym      — A->B vs B->A: which direction dominates, by how much (2-step compare)
  od_share     — what share of trips leaving A go to its single busiest destination
  od_toporigin — which areas send the most commuters to destination X (reverse lookup)
  filt_super   — superlative UNDER constraints ("among East subzones >20k residents, highest walkability")
  multihop     — subzone -> parent PA/region aggregate; share-of-parent
  quant_delta  — how many more / combined total / fraction (arithmetic over 2-3 entities)
  synthesis    — 2-metric reasoning ("densest among the transit-poor")
  similar      — most/least similar subzone by z-scored profile (+ why), cosine
  hex8_multi   — landmark-vs-landmark multi-metric comparison

Usage: python3 generate_reasoning_v2.py --dry-run | --pilot 60 --out-dir raw/v2_pilot | --out-dir raw/v2
"""
import argparse, json, os, sys, time, random, urllib.request, socket
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
random.seed(71)
socket.setdefaulttimeout(150)   # backstop so no urlopen can hang the worker forever
ATLAS="/home/azureuser/da-sgp/v4"
KEY=open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
MIN_POP=2000

def f0(v):return f"{round(v):,}"
def f2(v):return f"{v:.2f}"
def f3(v):return f"{v:.3f}"
def fp(v):return f"{v:.0%}"
# metric -> (label, formatter, kind) kind: share|density|percap|index|raw|count
MET={
 "pop_resident":("resident population",f0,"raw"),"pop_65plus":("residents aged 65+",f0,"count"),
 "elder_share":("share of residents 65+",fp,"share"),"child_share":("share of residents 0–14",fp,"share"),
 "nonres_share":("non-resident share",fp,"share"),"hdb_share":("HDB-housing share",fp,"share"),
 "pop_density":("population density (per km²)",f0,"density"),"dorm_density":("dorm density (per km²)",f0,"density"),
 "bus_stop_count":("bus stops",f0,"count"),"mrt_station_count":("MRT/LRT stations",f0,"count"),
 "dist_mrt_m":("distance to nearest MRT (m)",f0,"raw"),"walkability_score":("walkability score",f3,"index"),
 "vibrancy_index":("vibrancy index",f3,"index"),"commercial_intensity":("commercial intensity",f3,"index"),
 "hawker_centre_count":("hawker centres",f0,"count"),"school_count_total":("schools",f0,"count"),
 "pc_total":("total places",f0,"count"),"hdb_resale_4r_median_psm":("median 4-rm HDB resale ($/m²)",f0,"raw"),
}
PLACECATS={"food_cafe":"cafés","food_restaurant":"restaurants","food_hawker":"hawker eateries",
 "health_clinic":"clinics","retail_supermarket":"supermarkets","retail_mall":"malls","edu_preschool":"preschools",
 "service_fitness":"gyms","food_bar":"bars"}

def load():
    import pandas as pd, numpy as np
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
        ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    for c in("name","pa","region"): sz[c]=sz[c].astype("string").str.title()
    a=sz.subzone_area_km2.clip(lower=0.01); p=sz.pop_resident.clip(lower=1)
    sz["elder_share"]=sz.pop_65plus/p; sz["child_share"]=sz.pop_0_14/p
    sz["hdb_share"]=sz.get("pop_hdb_share",0); sz["pop_density"]=sz.pop_resident/a; sz["dorm_density"]=sz.pop_dorm/a
    sz["hdb_resale_4r_median_psm"]=sz["hdb_resale_4r_median_psm"].replace(0,np.nan)
    sz=sz.set_index("name",drop=False)
    # OD directed at subzone
    us=pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet").set_index("hex8_id")["parent_subzone_name"]
    od=pd.read_parquet(f"{ATLAS}/data/lta_od/hex8_od_matrix.parquet")
    od["o"]=od.origin_hex8.map(us).str.title(); od["d"]=od.dest_hex8.map(us).str.title()
    g=od.dropna(subset=["o","d"]).groupby(["o","d"],as_index=False).trips_wd.sum()
    # similarity matrix (z-scored headline metrics)
    feats=["pop_density","elder_share","child_share","nonres_share","hdb_share","walkability_score",
           "vibrancy_index","commercial_intensity","bus_stop_count","mrt_station_count","pc_total"]
    M=sz[sz.pop_resident>=MIN_POP][["name"]+feats].dropna()
    X=(M[feats]-M[feats].mean())/M[feats].std(ddof=0)
    Xn=X.values/ (np.linalg.norm(X.values,axis=1,keepdims=True)+1e-9)
    sim=Xn@Xn.T
    simnames=list(M["name"])
    return sz,g,sim,simnames,feats

def build(caps):
    import pandas as pd, numpy as np
    sz,g,sim,simnames,feats=load(); F=[]
    res=sz[sz.pop_resident>=MIN_POP]
    metcols=[m for m in MET if m in sz.columns]
    def step(*s): return " ".join(s)

    # ---------- OD families ----------
    gx=g[g.o!=g.d]
    flowpairs=gx[gx.trips_wd>=200]
    for r in flowpairs.sample(min(caps["od_flow"],len(flowpairs)),random_state=1).itertuples():
        F.append(dict(category="reasoning",kind="od_flow",scale="subzone",entity=r.o,
            stmt=f"OD FACT (LTA, weekday-monthly): {int(r.trips_wd):,} commuter trips travel from {r.o} to {r.d}.",
            prov=dict(o=r.o,d=r.d,trips=int(r.trips_wd))))
    # asymmetry
    piv={(o,d):t for o,d,t in zip(g.o,g.d,g.trips_wd)}
    seen=set(); asym=[]
    for (o,d),t in piv.items():
        if o>=d or (d,o) not in piv: continue
        t2=piv[(d,o)];
        if max(t,t2)<300: continue
        asym.append((o,d,t,t2))
    random.shuffle(asym)
    for o,d,t,t2 in asym[:caps["od_asym"]]:
        hi,lo,ht,lt=(o,d,t,t2) if t>=t2 else (d,o,t2,t)
        ratio=ht/max(lt,1)
        F.append(dict(category="reasoning",kind="od_asym",scale="subzone",entity=hi,
            stmt=f"OD ASYMMETRY: {int(t):,} weekday trips go {o}->{d}, while {int(t2):,} go {d}->{o}. "
                 f"The dominant direction is {hi}->{lo} (about {ratio:.1f}x the reverse).",
            prov=dict(o=o,d=d,ab=int(t),ba=int(t2))))
    # share-to-top + top-origins
    out=g.groupby("o").trips_wd.sum()
    for o in list(out.index):
        sub=g[(g.o==o)&(g.d!=o)].sort_values("trips_wd",ascending=False)
        if len(sub)<2 or out[o]<500: continue
        top=sub.iloc[0]; sh=top.trips_wd/max(out[o]-piv.get((o,o),0),1)
        F.append(dict(category="reasoning",kind="od_share",scale="subzone",entity=o,
            stmt=f"Of all weekday commuter trips LEAVING {o} for other subzones ({int(out[o]-piv.get((o,o),0)):,} total), "
                 f"the single largest flow is to {top.d} ({int(top.trips_wd):,} trips) = {sh:.0%} of outbound trips.",
            prov=dict(o=o,top=top.d,share=round(float(sh),3))))
    inn=g[g.o!=g.d].groupby("d")
    for d,sub in inn:
        sub=sub.sort_values("trips_wd",ascending=False)
        if sub.trips_wd.iloc[0]<500: continue
        top=sub.head(5)
        items="; ".join(f"{i+1}. {r.o} ({int(r.trips_wd):,})" for i,r in enumerate(top.itertuples()))
        F.append(dict(category="reasoning",kind="od_toporigin",scale="subzone",entity=top.iloc[0].o,
            stmt=f"The subzones sending the MOST weekday commuters INTO {d} are: {items}.",
            prov=dict(d=d,rank="top_origins")))

    # ---------- filtered superlative (multi-constraint) — ENUMERATE distinct ----------
    regions=list(res.region.dropna().unique())
    for reg in regions:
        for m in metcols:
            lab,f,kind=MET[m]
            for popmin in (10000,20000,30000):
                sub=res[(res.region==reg)&(res.pop_resident>=popmin)].dropna(subset=[m])
                if len(sub)<4: continue
                for hi in (True,False):
                    pick=sub.loc[sub[m].idxmax() if hi else sub[m].idxmin()]
                    F.append(dict(category="reasoning",kind="filt_super",scale="subzone",entity=pick["name"],
                        stmt=f"CONSTRAINED QUERY: among subzones in {reg} with at least {popmin:,} residents "
                             f"({len(sub)} qualify), the one with the {'highest' if hi else 'lowest'} {lab} is "
                             f"{pick['name']} ({f(pick[m])}). Method: filter by region+population, then rank by {lab}.",
                        prov=dict(metric=m,region=reg,popmin=popmin,n=len(sub))))
                # top-3 listing variant
                t3=sub.nlargest(3,m)
                if len(t3)==3:
                    items="; ".join(f"{i+1}. {r['name']} ({f(r[m])})" for i,(_,r) in enumerate(t3.iterrows()))
                    F.append(dict(category="reasoning",kind="filt_super_top3",scale="subzone",entity=t3.iloc[0]["name"],
                        stmt=f"CONSTRAINED RANKING: among subzones in {reg} with ≥{popmin:,} residents, the top 3 by {lab} are: {items}.",
                        prov=dict(metric=m,region=reg,popmin=popmin,rank="top3")))

    # ---------- multi-hop containment ----------
    pa_ag=res.groupby("pa").agg({**{c:'sum' for c in ['pop_resident','bus_stop_count','mrt_station_count','hawker_centre_count','school_count_total','pc_total','pop_65plus'] if c in res.columns}})
    reg_ag=res.groupby("region").agg({c:'sum' for c in ['pop_resident','pop_65plus','pc_total'] if c in res.columns})
    hopcols=[c for c in ['bus_stop_count','mrt_station_count','hawker_centre_count','school_count_total','pc_total'] if c in res.columns]
    for _,r in res.iterrows():
      for c in hopcols:                     # every subzone × every hop metric (distinct)
        lab=MET.get(c,(c.replace('_',' '),f0,'count'))[0]
        tot=pa_ag.loc[r['pa'],c] if r['pa'] in pa_ag.index else None
        if tot is None or tot<=0: continue
        F.append(dict(category="reasoning",kind="multihop_pa",scale="subzone",entity=r['name'],
            stmt=f"MULTI-HOP: {r['name']} sits in the {r['pa']} planning area. Across ALL subzones in {r['pa']}, "
                 f"there are {int(tot):,} {lab} in total (sum over its subzones).",
            prov=dict(subzone=r['name'],pa=r['pa'],col=c,total=int(tot))))
      if True:
        # share of region
        if r['region'] in reg_ag.index and 'pop_resident' in reg_ag.columns and reg_ag.loc[r['region'],'pop_resident']>0:
            shr=r['pop_resident']/reg_ag.loc[r['region'],'pop_resident']
            F.append(dict(category="reasoning",kind="multihop_share",scale="subzone",entity=r['name'],
                stmt=f"MULTI-HOP SHARE: {r['name']} has {r['pop_resident']:,.0f} residents; its region ({r['region']}) "
                     f"has {reg_ag.loc[r['region'],'pop_resident']:,.0f}. So {r['name']} holds {shr:.1%} of {r['region']}'s residents.",
                prov=dict(subzone=r['name'],region=r['region'],share=round(float(shr),4))))

    # ---------- quantitative delta (distinct via seen-set) ----------
    names=list(res["name"]); qseen=set(); qatt=0; qn=0
    while qn<caps["quant"] and qatt<caps["quant"]*4:
        qatt+=1
        kind=random.choice(["diff_place","combine_pop","diff_metric"])
        if kind=="diff_place":
            stem=random.choice(list(PLACECATS)); col=f"pc2_cat_{stem}_count"
            if col not in res.columns: continue
            A,B=random.sample(names,2); key=("dp",stem,*sorted((A,B)))
            if key in qseen: continue
            va,vb=int(res.loc[A,col]),int(res.loc[B,col])
            if va==vb: continue
            qseen.add(key); hi,lo=((A,va),(B,vb)) if va>vb else ((B,vb),(A,va)); qn+=1
            F.append(dict(category="reasoning",kind="quant_diff_place",scale="subzone",entity=hi[0],
                stmt=f"ARITHMETIC: {A} has {va} {PLACECATS[stem]} and {B} has {vb}. {hi[0]} has {hi[1]-lo[1]} more ({hi[1]}-{lo[1]}) than {lo[0]}.",
                prov=dict(a=A,b=B,col=col,diff=abs(va-vb))))
        elif kind=="combine_pop":
            k=random.choice([2,3]); pick=random.sample(names,k); key=("cp",*sorted(pick))
            if key in qseen: continue
            qseen.add(key); vals=[int(res.loc[n,"pop_resident"]) for n in pick]; tot=sum(vals); qn+=1
            terms=" + ".join(f"{v:,}" for v in vals)
            F.append(dict(category="reasoning",kind="quant_combine_pop",scale="subzone",entity=pick[0],
                stmt=f"ARITHMETIC: combined resident population of {', '.join(pick)} is {terms} = {tot:,}.",
                prov=dict(subzones=pick,total=tot)))
        else:
            m=random.choice([x for x in metcols if MET[x][2] in ('count','raw','density')]); lab,f,_=MET[m]
            A,B=random.sample(names,2); key=("dm",m,*sorted((A,B)))
            if key in qseen: continue
            va,vb=res.loc[A,m],res.loc[B,m]
            if pd.isna(va) or pd.isna(vb) or va==vb: continue
            qseen.add(key); qn+=1
            F.append(dict(category="reasoning",kind="quant_diff_metric",scale="subzone",entity=A,
                stmt=f"ARITHMETIC: {A}'s {lab} is {f(va)} and {B}'s is {f(vb)}; the difference is {f(abs(va-vb))}.",
                prov=dict(a=A,b=B,metric=m,diff=float(abs(va-vb)))))

    # ---------- 2-metric synthesis — ENUMERATE distinct ordered metric pairs ----------
    for m1 in metcols:
        for m2 in metcols:
            if m1==m2: continue
            l1,f1,_=MET[m1]; l2,f2,_=MET[m2]
            sub=res.dropna(subset=[m1,m2])
            if len(sub)<10: continue
            thr=sub[m2].median(); lowm2=sub[sub[m2]<=thr]
            if len(lowm2)<4: continue
            pick=lowm2.loc[lowm2[m1].idxmax()]
            F.append(dict(category="reasoning",kind="synthesis",scale="subzone",entity=pick["name"],
                stmt=f"TWO-CONDITION: among subzones with below-median {l2} (≤{f2(thr)}), the one with the highest {l1} "
                     f"is {pick['name']} ({l1} {f1(pick[m1])}, {l2} {f2(pick[m2])}). Step 1: filter to low-{l2}. Step 2: take the max {l1}.",
                prov=dict(m1=m1,m2=m2,pick=pick["name"])))

    # ---------- similarity (analogy) ----------
    import numpy as np
    idx={n:i for i,n in enumerate(simnames)}
    for n in simnames:
        i=idx[n]; order=np.argsort(-sim[i])
        nn=[simnames[j] for j in order if simnames[j]!=n][:3]
        far=simnames[order[-1]]
        # why: top contributing shared features
        F.append(dict(category="reasoning",kind="similar",scale="subzone",entity=n,
            stmt=f"PROFILE SIMILARITY: by a z-scored profile over {len(feats)} features (density, age mix, housing, "
                 f"walkability, transit, places), the subzones most similar to {n} are: {', '.join(nn)}. "
                 f"The least similar is {far}.",
            prov=dict(subzone=n,similar=nn,least=far)))

    # ---------- hex8 landmark multi-metric (loaded lazily) ----------
    if caps["hex8"]>0:
        F+=hex8_facts(caps["hex8"])

    random.shuffle(F)
    for i,x in enumerate(F): x["fid"]=i
    return F

def hex8_facts(cap):
    import pandas as pd, numpy as np
    p=pd.read_parquet(f"{ATLAS}/places/sgp_places_final.parquet")
    p=p[p.name.notna()&(p.name.str.len()>2)].copy(); p["sc"]=p.reviews_count.fillna(0)*(1+p.is_magnet.fillna(False).astype(int))
    lm=p.sort_values("sc",ascending=False).drop_duplicates("hex8_id")
    lm=lm[(lm.reviews_count.fillna(0)>=20)|(lm.is_magnet.fillna(False))].set_index("hex8_id")["name"]
    h8=pd.read_parquet(f"{ATLAS}/hex/hex8_all_features.parquet")
    u=pd.read_parquet(f"{ATLAS}/hex/hex8_universe.parquet")[["hex8_id","parent_pa","parent_region"]]
    h8=h8.drop(columns=[c for c in("parent_pa","parent_region")if c in h8.columns]).merge(u,on="hex8_id")
    h8=h8.reset_index(drop=True)
    h8=h8[h8.hex8_id.isin(lm.index)].copy(); h8["lm"]=h8.hex8_id.map(lm)
    h8["parent_pa"]=h8.parent_pa.astype("string").str.title()
    h8["parent_region"]=h8.parent_region.astype("string").str.title()
    mets=[c for c in ["walkability_score","vibrancy_index","commercial_activity_index","pop_resident","bus_stop_count","nl_2024","od_throughput","pc_total"] if c in h8.columns]
    fmt={"walkability_score":f3,"vibrancy_index":f3,"commercial_activity_index":f3,"nl_2024":f2}
    rng=random.Random(99); F=[]; seen=set()
    pools=[]
    for gkind,gcol in (("pa","parent_pa"),("region","parent_region")):
        for gname,sub in h8.groupby(gcol):
            if len(sub)>=2: pools.append((gkind,str(gname),sub))
    attempts=0
    while len(F)<cap and attempts<cap*12:
        attempts+=1
        gkind,gname,sub=rng.choice(pools); m=rng.choice(mets)
        a,b=rng.sample(list(sub.index),2)
        key=(min(a,b),max(a,b),m)
        if key in seen: continue
        A,B=sub.loc[a],sub.loc[b]; va,vb=A[m],B[m]
        if pd.isna(va) or pd.isna(vb) or va==vb: continue
        seen.add(key); ff=fmt.get(m,f0); hi,lo=(A,B) if va>vb else (B,A); lab=m.replace("_"," ")
        scope=f"In {gname}" if gkind=="pa" else f"In the {gname}"
        F.append(dict(category="reasoning",kind="hex8_multi",scale="hex8",entity=hi["lm"],
            stmt=f"{scope}, the area around {hi['lm']} has a higher {lab} ({ff(max(va,vb))}) "
                 f"than the area around {lo['lm']} ({ff(min(va,vb))}).",
            prov=dict(scope=gname,metric=m,a=A['lm'],b=B['lm'])))
    return F

SYS=("You convert Singapore atlas REASONING items into natural Q&A for a strong spatial-reasoning "
 "model. For EACH item write ONE question an analyst would ask and a correct answer. CRITICAL: "
 "(1) Use ONLY the numbers/names in the item — never invent; preserve list order. (2) 'reasoning' MUST "
 "show the explicit STEPS (the filter, the two-direction compare, the parent aggregation, the arithmetic, "
 "the ranking) — this is a reasoning model, make the chain visible. (3) For OD items keep 'weekday' framing. "
 "(4) Phrase the QUESTION to require the reasoning (state the constraints/the two entities), not just ask for "
 "a number. (5) Vary phrasing. Return a JSON array: {\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch,model,retries=3):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"ITEMS:\n{txt}"}],"temperature":0.7,"max_tokens":300*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-reasoning-v2","Connection":"close"})
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
    ap.add_argument("--batch",type=int,default=8);ap.add_argument("--concurrency",type=int,default=16)
    ap.add_argument("--model",default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out-dir",default="raw/v2");ap.add_argument("--shard-size",type=int,default=10000)
    ap.add_argument("--dry-run",action="store_true");ap.add_argument("--pilot",type=int,default=0)
    ap.add_argument("--key-file",default="~/notes/openrouter-kosha.txt")
    ap.add_argument("--resume",action="store_true")
    # volume caps per family (tune to hit ~200k)
    ap.add_argument("--od-flow",type=int,default=19000);ap.add_argument("--od-asym",type=int,default=13000)
    ap.add_argument("--filt-super",type=int,default=0);ap.add_argument("--multihop",type=int,default=0)
    ap.add_argument("--quant",type=int,default=88000);ap.add_argument("--synth",type=int,default=0)
    ap.add_argument("--hex8",type=int,default=105000)
    args=ap.parse_args()
    caps=dict(od_flow=args.od_flow,od_asym=args.od_asym,filt_super=args.filt_super,multihop=args.multihop,
              quant=args.quant,synth=args.synth,hex8=args.hex8)
    FA=build(caps)
    from collections import Counter
    c=Counter(f["kind"] for f in FA)
    print(f"[facts] total={len(FA):,}",file=sys.stderr)
    for k,v in sorted(c.items(),key=lambda x:-x[1]): print(f"   {k:18s} {v:,}",file=sys.stderr)
    print(f"[est] ~${len(FA)*70/1e6*0.0983+len(FA)*110/1e6*0.1966:.2f}",file=sys.stderr)
    if args.dry_run:
        for f in FA[:14]: print("  •",f["stmt"][:150],file=sys.stderr)
        return
    if args.pilot: FA=FA[:args.pilot]
    globals()["KEY"]=open(os.path.expanduser(args.key_file)).read().strip()  # allow key switch
    os.makedirs(args.out_dir,exist_ok=True)
    sh=0
    if args.resume:
        import glob
        done=set(); existing=sorted(glob.glob(f"{args.out_dir}/shard_*.jsonl"))
        for p in existing:
            for l in open(p):
                try: done.add(json.loads(l)["fact"])
                except: pass
        before=len(FA); FA=[f for f in FA if f["stmt"] not in done]
        sh=len(existing)   # append as new shards, don't touch existing
        print(f"[resume] {len(done):,} already done; {len(FA):,} remaining (of {before:,}); new shards start at {sh}",file=sys.stderr)
    by={f["fid"]:f for f in FA};B=[FA[i:i+args.batch] for i in range(0,len(FA),args.batch)]
    tin=tout=ok=bad=0;w=0;t0=time.time();out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
    # SLIDING WINDOW: keep ~2x concurrency in flight; one stuck call ties up 1 slot, never a whole wave
    it=iter(B); fmap={}
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for _ in range(args.concurrency*2):
            b=next(it,None)
            if b is None: break
            fmap[ex.submit(call,b,args.model)]=b
        while fmap:
            done,_=wait(list(fmap),timeout=120,return_when=FIRST_COMPLETED)
            if not done:  # nothing finished in 120s — keep waiting, but log liveness
                print(f"  …(waiting) ok={ok:,} inflight={len(fmap)} {time.time()-t0:.0f}s",file=sys.stderr); continue
            for fut in done:
                b=fmap.pop(fut)
                try: arr,u=fut.result()
                except Exception: arr,u={"error":"fut"},{}
                tin+=u.get("prompt_tokens",0);tout+=u.get("completion_tokens",0)
                if isinstance(arr,dict): bad+=len(b)
                else:
                    for o in arr:
                        if not isinstance(o,dict): bad+=1; continue
                        f=by.get(o.get("fid"))
                        q=str(o.get("question","")).strip(); a=str(o.get("answer","")).strip()
                        if not f or not q or not a:bad+=1;continue
                        rec=dict(category="reasoning",kind=f["kind"],scale=f["scale"],entity=f["entity"],
                            question=q,reasoning=str(o.get("reasoning","")).strip(),
                            answer=a,fact=f["stmt"],provenance=f["prov"])
                        out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                        if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
                nb=next(it,None)
                if nb is not None: fmap[ex.submit(call,nb,args.model)]=nb
            if (ok+bad)%2000<args.batch*args.concurrency:
                out.flush();print(f"  …ok={ok:,} bad={bad} inflight={len(fmap)} ${tin/1e6*0.0983+tout/1e6*0.1966:.2f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,4),shards=sh+1)))
    print(f"[done] ok={ok:,} bad={bad} ${cost:.2f} {time.time()-t0:.0f}s",file=sys.stderr)

if __name__=="__main__":main()

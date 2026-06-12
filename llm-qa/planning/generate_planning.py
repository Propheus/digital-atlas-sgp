#!/usr/bin/env python3
"""
Plexis-Mind — PLANNING Q&A generator (counterfactual / what-if reasoning).

CARDINAL RULE: there is no ground truth for "open an MRT line" in a static atlas, so we
NEVER fabricate a magnitude. Three grounded tiers (docs/SGP_LLM_QA_STRATEGY.md §Planning):
  observed  — Tier 1, REAL: night-light 2022->2024 change (what actually grew/declined)
  mrt_gap   — Tier 2, ANALOG estimate: underserved area vs a comparable connected area;
              projection is directional + explicitly labelled a model estimate under assumptions
  supply_gap— Tier 2, GROUNDED: measured per-1k supply vs the national median -> add-capacity logic
  scenario  — Tier 3, CHAIN: assumption -> inference -> caveat (teaches the reasoning structure)

"Train the chain, not the digit." Every answer cites real current data, states assumptions,
gives a directional/analog conclusion, and carries an estimate caveat.

Usage: python3 generate_planning.py --dry-run | --pilot 40 --out-dir raw/pilot | --out-dir raw/full
"""
import argparse, json, os, sys, time, random, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
random.seed(31)
ATLAS="/home/azureuser/da-sgp/v4"
KEY=open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"

GAPS={"cafe_coffee":"cafés","restaurant":"restaurants","hawker":"hawker food","supermarket":"supermarkets",
      "bakery":"bakeries","beauty_personal":"beauty/personal services","fitness_recreation":"gyms & recreation",
      "health_medical":"clinics & medical"}

def load():
    import pandas as pd
    sz=pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    un=pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
        ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]].drop_duplicates("parent_subzone")
    un.columns=["subzone_c","name","pa","region"]; sz=sz.merge(un,on="subzone_c")
    for c in("name","pa","region"): sz[c]=sz[c].astype("string").str.title()
    return sz

def build():
    import pandas as pd, numpy as np
    sz=load(); F=[]
    res=sz[sz.pop_resident>=5000].copy()   # planning is about inhabited areas
    # ---- Tier 1: observed night-light change (REAL) ----
    ch=res.dropna(subset=["nl_change_pct"])
    top=ch.nlargest(8,"nl_change_pct"); bot=ch.nsmallest(8,"nl_change_pct")
    F.append(dict(category="planning",kind="observed_growth_top",scale="subzone",entity=top.iloc[0]["name"],
        stmt="REAL OBSERVED CHANGE (night-light radiance is a proxy for built-up economic activity). "
             "From 2022 to 2024, the residential subzones with the LARGEST growth were: "
             +"; ".join(f"{r.name} (+{r.nl_change_pct:.0f}%)" for r in top.itertuples())+".",
        prov=dict(col="nl_change_pct",rank="max")))
    F.append(dict(category="planning",kind="observed_growth_bottom",scale="subzone",entity=bot.iloc[0]["name"],
        stmt="REAL OBSERVED CHANGE. From 2022 to 2024, the residential subzones with the LARGEST DECLINE "
             "in night-light activity were: "+"; ".join(f"{r.name} ({r.nl_change_pct:+.0f}%)" for r in bot.itertuples())+".",
        prov=dict(col="nl_change_pct",rank="min")))
    for _,r in ch.iterrows():   # every residential subzone gets its observed-change fact
        d="grew" if r.nl_change_pct>=0 else "declined"
        F.append(dict(category="planning",kind="observed_growth_sz",scale="subzone",entity=r["name"],
            stmt=f"REAL OBSERVED CHANGE: between 2022 and 2024, night-light activity in {r['name']} ({r['pa']}) "
                 f"{d} by {abs(r.nl_change_pct):.0f}% — a measured signal of {'rising' if r.nl_change_pct>=0 else 'softening'} "
                 f"local economic activity (not a forecast).",
            prov=dict(col="nl_change_pct",key=r["subzone_c"],value=float(r.nl_change_pct))))
    # ---- Tier 2: MRT-gap analog counterfactual ----
    if "dist_mrt_m" in sz.columns:
        under=res[(res.dist_mrt_m>500)].copy()
        conn=res[(res.dist_mrt_m<350)].copy()
        for _,x in under.iterrows():   # every under-served populous subzone
            # analog: same region, closest population, well-connected
            pool=conn[conn.region==x["region"]]
            if len(pool)==0: pool=conn
            y=pool.iloc[(pool.pop_resident-x.pop_resident).abs().argsort().iloc[0]]
            F.append(dict(category="planning",kind="mrt_gap_analog",scale="subzone",entity=x["name"],
                stmt=f"WHAT-IF (model estimate, not a fact): {x['name']} has ~{x.pop_resident:,.0f} residents but sits "
                     f"~{x.dist_mrt_m:,.0f} m from the nearest MRT/LRT — under-served. A comparable, well-connected area "
                     f"in the same region, {y['name']} (~{y.dist_mrt_m:,.0f} m from rail), has a walkability score of "
                     f"{y.walkability_score:.2f} and commercial intensity {y.commercial_intensity:.2f}, vs {x['name']}'s "
                     f"{x.walkability_score:.2f} / {x.commercial_intensity:.2f}. INFERENCE: adding a station near {x['name']} "
                     f"would cut its access distance and, by analogy with {y['name']}, plausibly lift accessibility and commercial "
                     f"activity over time. Direction is well-grounded; the magnitude is uncertain and depends on land-use, feeders and demand.",
                prov=dict(under=x["subzone_c"],analog=y["subzone_c"],dist_mrt=float(x.dist_mrt_m))))
    # ---- Tier 2: supply-gap (per-1k vs national median) ----
    for k,label in GAPS.items():
        sc=f"sat_{k}_per_1k"
        if sc not in sz.columns: continue
        med=float(res[sc].median())
        low=res[res[sc]<med*0.5].dropna(subset=[sc])
        for _,r in low.iterrows():   # every materially under-supplied subzone per category
            F.append(dict(category="planning",kind=f"supply_gap_{k}",scale="subzone",entity=r["name"],
                stmt=f"SUPPLY-GAP (grounded): {r['name']} ({r['pa']}) has {r[sc]:.2f} {label} per 1,000 residents, "
                     f"below the national subzone median of {med:.2f}. INFERENCE: it is comparatively under-supplied for "
                     f"{label}; adding capacity here would close the gap toward the citywide norm — a defensible siting priority "
                     f"(holding demand assumptions constant).",
                prov=dict(col=sc,key=r["subzone_c"],value=float(r[sc]),median=med)))
    # ---- Tier 3: assumption-chain scenarios (structure, grounded norms) ----
    sch_per100k=float((res.school_count_total/res.pop_resident*1e5).median())
    chains=[
     ("A new BTO town of ~30,000 residents is planned on a greenfield site. What public infrastructure should follow, and why?",
      f"ASSUMPTION: 30k residents at Singapore norms. CHAIN: (1) transit — a town this size warrants an MRT/LRT link + bus interchange "
      f"(SG plans towns around rail); (2) schools — at the national median of ~{sch_per100k:.0f} schools per 100k residents, expect "
      f"~{sch_per100k*0.3:.0f} schools; (3) daily-needs — at least one supermarket + hawker/market + polyclinic/CHAS coverage within "
      f"walking distance; (4) parks & community nodes. CAVEAT: counts are planning heuristics from current averages, not a fixed blueprint."),
     ("If an existing MRT line is extended to a currently under-served residential area, what second-order effects are likely?",
      "CHAIN: improved accessibility -> shorter trips to jobs/CBD -> higher demand to live/work there -> upward pressure on resale prices "
      "and commercial activity near the station -> more feeder bus + amenity demand. CAVEAT: magnitudes depend on land-use zoning, "
      "station siting and parallel supply; this is the direction of effect, not a guaranteed figure."),
     ("A large new employment hub (e.g. a business park) opens in an outer region. How might commuting patterns shift?",
      "CHAIN: a new job centre attracts inbound commuters -> the area shifts toward a net commuter IMPORTER in OD terms -> AM inflow rises, "
      "PM outflow rises -> pressure on rail/road capacity on the approach corridors -> demand for nearby housing and lunchtime F&B. "
      "CAVEAT: depends on hub size, accessibility and housing nearby; directional reasoning only."),
    ]
    for q,a in chains:
        for _ in range(6):  # a few paraphrase seeds each
            F.append(dict(category="planning",kind="scenario_chain",scale="general",entity="Singapore",
                stmt=f"PLANNING SCENARIO. Q: {q} GROUNDED REASONING: {a}",
                prov=dict(kind="assumption_chain")))
    random.shuffle(F)
    for i,x in enumerate(F): x["fid"]=i
    return F

SYS=("You convert grounded Singapore PLANNING scenarios into natural what-if Q&A for a spatial-"
 "reasoning model. For EACH item write ONE question a planner/analyst would ask and an answer that "
 "is a clear REASONING CHAIN. CRITICAL RULES: (1) Use ONLY the facts/figures given — never invent a "
 "magnitude. (2) Preserve every CAVEAT and the 'estimate/projection/not a forecast/observed' framing — "
 "the model must learn that planning answers are directional and assumption-bound, not certainties. "
 "(3) 'reasoning' = the explicit chain (accessibility->demand->effect, or observed-change, or gap->add-supply). "
 "(4) For observed-change items, state it is a measured 2022-2024 change, not a prediction. (5) Vary phrasing. "
 "Return a JSON array: {\"fid\":int,\"question\":str,\"reasoning\":str,\"answer\":str}. JSON only.")

def call(batch,model,retries=4):
    txt="\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"ITEMS:\n{txt}"}],"temperature":0.75,"max_tokens":320*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-planning"})
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
    ap.add_argument("--batch",type=int,default=6);ap.add_argument("--concurrency",type=int,default=10)
    ap.add_argument("--model",default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out-dir",default="raw/full");ap.add_argument("--shard-size",type=int,default=5000)
    ap.add_argument("--dry-run",action="store_true");ap.add_argument("--pilot",type=int,default=0)
    args=ap.parse_args()
    FA=build()
    from collections import Counter
    c=Counter(f["kind"].split("_")[0] for f in FA)
    print(f"[facts] total={len(FA):,} {dict(c)}",file=sys.stderr)
    print(f"[est] ~${len(FA)*120/1e6*0.0983+len(FA)*150/1e6*0.1966:.2f}",file=sys.stderr)
    if args.dry_run:
        for f in FA[:6]: print("  •",f["stmt"][:240],file=sys.stderr); print(file=sys.stderr)
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
                rec=dict(category="planning",kind=f["kind"],scale=f["scale"],entity=f["entity"],
                    question=o["question"].strip(),reasoning=o.get("reasoning","").strip(),
                    answer=o["answer"].strip(),fact=f["stmt"],provenance=f["prov"])
                out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
            if (ok+bad)%1000<args.batch:print(f"  …ok={ok:,} ${tin/1e6*0.0983+tout/1e6*0.1966:.3f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,4),shards=sh+1)))
    print(f"[done] ok={ok:,} bad={bad} ${cost:.3f} {time.time()-t0:.0f}s",file=sys.stderr)

if __name__=="__main__":main()

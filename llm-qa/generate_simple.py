#!/usr/bin/env python3
"""
Plexis-Mind — SIMPLE/HUMAN register. Short, casual questions a normal resident would ask, with
brief conversational answers (NO long reasoning). Adds register diversity so the model handles
real users, not just analysts. Reuses existing deterministic facts (ground truth preserved).

Usage: python3 generate_simple.py --pilot 40 --out-dir simple/pilot | --n 18000 --out-dir simple/full
"""
import argparse, json, os, sys, time, random, urllib.request, glob, socket
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
random.seed(77); socket.setdefaulttimeout(120)
KEY=open(os.path.expanduser("~/notes/openrouter-llm-build-key.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"; MODEL="deepseek/deepseek-v4-flash"

# everyday kinds people actually ask about (skip technical: entropy/gpr/centrality/nl/lu_pct/od/roads)
EVERYDAY=("count_food","count_health","count_retail","count_edu","count_service_fitness","count_civic_religious",
 "exist_","attr_pop_resident","attr_pop_65plus","attr_pop_dorm","attr_mrt_station","attr_bus_stop",
 "attr_hawker_centre","attr_school_count","attr_walkability_score","attr_vibrancy_index",
 "attr_hdb_resale","attr_dominant_use","membership_subzone","membership_pa","mix_dominant","brand_count",
 "cmp_pop_resident","cmp_walkability_score","cmp_vibrancy_index","top5_highest_elder","top5_highest_walk")

def load_pool(root, n):
    pool=[]
    for p in glob.glob(f"{root}/*/raw/**/*.jsonl",recursive=True):
        if "pilot" in p: continue
        for l in open(p):
            try: r=json.loads(l)
            except: continue
            k=r.get("kind","")
            if any(k.startswith(e) for e in EVERYDAY) and r.get("fact"): pool.append(r)
    random.shuffle(pool); return pool[:n] if n else pool

SYS=("You turn a Singapore atlas FACT into a SHORT, CASUAL question-and-answer, like a regular "
 "resident chatting — NOT an analyst. RULES: (1) QUESTION: 4-12 words, natural and casual, the way a "
 "normal person actually asks (no jargon, no 'according to the atlas', no 'subzone'/'planning area' — "
 "just use the place name plainly, e.g. 'in Tampines'). (2) ANSWER: ONE short, friendly sentence giving "
 "just the key fact (you may round lightly, e.g. 'about 30'). Conversational, no preamble. (3) Use ONLY "
 "the fact — never invent. (4) NO reasoning. Vary phrasing; some yes/no, some 'how many', some 'which'. "
 "Return a JSON array, one per fact: {\"fid\":int,\"question\":str,\"answer\":str}. JSON only.")

def call(batch, retries=3):
    txt="\n".join(f'fid={f["fid"]}: {f["fact"]}' for f in batch)
    body=json.dumps({"model":MODEL,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"FACTS:\n{txt}"}],"temperature":0.8,"max_tokens":120*len(batch)}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-simple","Connection":"close"})
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
    ap.add_argument("--root",default=os.path.expanduser("~/da-sgp/llm-qa"))
    ap.add_argument("--out-dir",default="simple/full");ap.add_argument("--n",type=int,default=0)
    ap.add_argument("--pilot",type=int,default=0);ap.add_argument("--batch",type=int,default=12)
    ap.add_argument("--concurrency",type=int,default=12);ap.add_argument("--shard-size",type=int,default=10000)
    args=ap.parse_args()
    pool=load_pool(args.root, args.pilot or args.n)
    for i,f in enumerate(pool): f["fid"]=i
    print(f"[pool] {len(pool):,} everyday facts to casual-ify",file=sys.stderr)
    by={f["fid"]:f for f in pool}; B=[pool[i:i+args.batch] for i in range(0,len(pool),args.batch)]
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
            if not done: print(f"  …(waiting) ok={ok}",file=sys.stderr); continue
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
                        rec=dict(category=f["category"],kind="simple_"+f["kind"],scale=f.get("scale"),entity=f.get("entity"),
                                 question=q,reasoning="",answer=a,fact=f["fact"],provenance=f.get("provenance",{}),register="casual")
                        out.write(json.dumps(rec,ensure_ascii=False)+"\n");ok+=1;w+=1
                        if w>=args.shard_size:out.close();sh+=1;w=0;out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
                nb=next(it,None)
                if nb is not None: fmap[ex.submit(call,nb)]=nb
            if (ok+bad)%2000<args.batch*args.concurrency:
                print(f"  ok={ok} bad={bad} ${tin/1e6*0.0983+tout/1e6*0.1966:.2f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close();cost=tin/1e6*0.0983+tout/1e6*0.1966
    print(json.dumps(dict(ok=ok,bad=bad,cost_usd=round(cost,3))))

if __name__=="__main__": main()

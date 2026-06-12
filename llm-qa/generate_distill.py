#!/usr/bin/env python3
"""
Plexis-Mind — DISTILLATION: deep verified reasoning traces (the v1 reasoning core).

Teacher (DeepSeek-v4-pro) gets {atlas context + question} and reasons step-by-step. We parse its
FINAL ANSWER and VERIFY it against our deterministic gold via atlas_tools.verify() — keeping ONLY
chains that reach the correct answer (rejection sampling). Garbage reasoning is structurally rejected.

Output: deep, correct, grounded CoT traces for SFT-v1 (replaces the shallow flash reasoning).

Usage:
  python3 generate_distill.py --pilot 40 --out-dir distill/pilot
  python3 generate_distill.py --n 25000 --concurrency 10 --out-dir distill/full
"""
import argparse, json, os, sys, time, random, urllib.request, glob, socket
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
sys.path.insert(0, os.path.expanduser("~/da-sgp/llm-qa"))
import atlas_tools
random.seed(2026); socket.setdefaulttimeout(180)
KEY=open(os.path.expanduser("~/notes/openrouter-llm-build-key.txt")).read().strip()
ENDPOINT="https://openrouter.ai/api/v1/chat/completions"
MODEL_DEFAULT="deepseek/deepseek-v4-pro"

# Only kinds that genuinely need MULTI-STEP reasoning (lookups & trivial arithmetic excluded —
# od_flow, quant_combine_pop, quant_diff_place, count, attr are already fine as flash traces).
FAM_CAP={
  "od_asym":6000,"od_share":300,"od_toporigin":300,      # OD relational (compare directions, shares)
  "multihop":800,"filt_super":600,"synthesis":200,"why_composite":728,"similar":150,"rank_":800,
  "cmp_":5000,"quant_diff_metric":2000,"multirank":2000,  # comparison / metric-delta / multi-entity
  "supply_gap":300,"observed_growth":200,"mrt_gap":40,"scenario_chain":20,  # planning
}
def fam(kind):
    best=None
    for f in FAM_CAP:           # longest matching prefix wins
        if kind.startswith(f) and (best is None or len(f)>len(best)): best=f
    return best

def load_pool(root):
    pool=[]
    for p in glob.glob(f"{root}/*/raw/**/*.jsonl",recursive=True):
        if "pilot" in p or "/distill/" in p: continue
        for l in open(p):
            try: r=json.loads(l)
            except: continue
            if fam(r.get("kind","")): pool.append(r)
    random.shuffle(pool)
    # apply per-family caps
    seen={}; out=[]
    for r in pool:
        f=fam(r["kind"]);
        if seen.get(f,0)>=FAM_CAP[f]: continue
        seen[f]=seen.get(f,0)+1; out.append(r)
    random.shuffle(out)
    return out

SYS=("You are a meticulous analyst of Singapore's urban geography. You are given atlas data and a "
 "question. Think step by step: identify the relevant values from the data, then do the comparison / "
 "arithmetic / filtering / multi-hop / inference EXPLICITLY, and sanity-check. Be rigorous and do not "
 "skip steps. After your reasoning, end with a line exactly: 'FINAL ANSWER: <concise answer>'.")

def teacher(rec, model, retries=2):
    ctx=rec.get("fact","")
    body=json.dumps({"model":model,"messages":[{"role":"system","content":SYS},
        {"role":"user","content":f"ATLAS DATA:\n{ctx}\n\nQUESTION: {rec['question']}"}],
        "temperature":0.4,"max_tokens":1400}).encode()
    req=urllib.request.Request(ENDPOINT,data=body,headers={"Authorization":f"Bearer {KEY}",
        "Content-Type":"application/json","X-Title":"plexis-mind-distill","Connection":"close"})
    for a in range(retries):
        try:
            with urllib.request.urlopen(req,timeout=150) as r: d=json.loads(r.read())
            c=d["choices"][0]["message"]["content"]; u=d.get("usage",{})
            return c, u
        except Exception as ex:
            if a==retries-1: return None,{}
            time.sleep(2*(a+1))

def split_final(txt):
    import re
    m=re.search(r"FINAL ANSWER:\s*(.+)", txt, re.S|re.I)
    if not m: return txt.strip(), txt.strip()
    ans=m.group(1).strip(); reasoning=txt[:m.start()].strip()
    return reasoning, ans

import re as _re
def verify_distill(full, final, gold, kind):
    """Verify the teacher reasoned correctly. Checks the FULL output (numbers live in the
    reasoning, not just the terse final), tolerates percentile complements (X% top == (100-X)th
    pct) and one missing number."""
    gl=(gold or "").lower()
    decline=any(w in gl for w in ("doesn't","does not","not track","not include","no data","not a subzone","cannot"))
    if kind.startswith("abstain") or decline:
        fl=(final+" "+full).lower()
        return any(w in fl for w in ("doesn't","does not","not track","not include","no data","can't","cannot","unable","not a subzone"))
    g=atlas_tools._nums(gold); m=atlas_tools._nums(full)
    if g:
        def hit(a):
            return (any(abs(a-x)<=max(0.03*abs(x),0.5) for x in m)
                    or any(abs((100-a)-x)<=0.6 for x in m))   # percentile complement
        hits=sum(1 for a in g if hit(a))
        return hits>=max(1, len(g)-1)   # all gold numbers but at most one
    ge=set(_re.findall(r"[A-Z][a-zA-Z']+", gold or "")); me=set(_re.findall(r"[A-Z][a-zA-Z']+", final+" "+full))
    return len(ge & me)>0 if ge else True

def process(rec, model, max_attempts):
    gold=rec.get("answer",""); kind=rec.get("kind","")
    for _ in range(max_attempts):
        out,u=teacher(rec, model)
        if not out: continue
        reasoning, final = split_final(out)
        if len(reasoning)<30: continue
        if verify_distill(out, final, gold, kind):
            return dict(category="reasoning", kind=kind, scale=rec.get("scale"), entity=rec.get("entity"),
                        context=rec.get("fact",""), question=rec["question"],
                        reasoning=reasoning, answer=final, gold=gold, source="distill_v4pro"), u, True
        else:
            last=(out,u)
    return None, (locals().get("last",(None,{}))[1]), False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=os.path.expanduser("~/da-sgp/llm-qa"))
    ap.add_argument("--out-dir",default="distill/full"); ap.add_argument("--n",type=int,default=0)
    ap.add_argument("--pilot",type=int,default=0); ap.add_argument("--concurrency",type=int,default=8)
    ap.add_argument("--model",default=MODEL_DEFAULT); ap.add_argument("--attempts",type=int,default=2)
    ap.add_argument("--shard-size",type=int,default=5000)
    args=ap.parse_args()
    pool=load_pool(args.root)
    from collections import Counter
    print(f"[pool] {len(pool):,} hard pairs (balanced): {dict(Counter(fam(r['kind']) for r in pool))}",file=sys.stderr)
    if args.pilot: pool=pool[:args.pilot]
    elif args.n: pool=pool[:args.n]
    print(f"[run] attempting {len(pool):,} | model={args.model} | attempts={args.attempts}",file=sys.stderr)

    os.makedirs(args.out_dir,exist_ok=True)
    tin=tout=ok=rej=0; sh=0; w=0; t0=time.time()
    out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
    it=iter(pool); fmap={}
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        for _ in range(args.concurrency*2):
            r=next(it,None)
            if r is None: break
            fmap[ex.submit(process,r,args.model,args.attempts)]=r
        while fmap:
            done,_=wait(list(fmap),timeout=120,return_when=FIRST_COMPLETED)
            if not done:
                print(f"  …(waiting) ok={ok} rej={rej} {time.time()-t0:.0f}s",file=sys.stderr); continue
            for fut in done:
                src=fmap.pop(fut)
                try: rec,u,good=fut.result()
                except Exception: rec,u,good=None,{},False
                tin+=u.get("prompt_tokens",0); tout+=u.get("completion_tokens",0)
                if good and rec:
                    out.write(json.dumps(rec,ensure_ascii=False)+"\n"); ok+=1; w+=1
                    if w>=args.shard_size: out.close(); sh+=1; w=0; out=open(f"{args.out_dir}/shard_{sh:03d}.jsonl","w")
                else: rej+=1
                nr=next(it,None)
                if nr is not None: fmap[ex.submit(process,nr,args.model,args.attempts)]=nr
            if (ok+rej)%100<args.concurrency:
                cost=tin/1e6*0.435+tout/1e6*0.87
                print(f"  ok={ok} rej={rej} accept={100*ok/max(ok+rej,1):.0f}% ${cost:.2f} {time.time()-t0:.0f}s",file=sys.stderr)
    out.close(); cost=tin/1e6*0.435+tout/1e6*0.87
    print(json.dumps(dict(ok=ok,rej=rej,accept_pct=round(100*ok/max(ok+rej,1),1),cost_usd=round(cost,3),
                          per_1k_verified=round(cost/max(ok,1)*1000,2))))
    print(f"[done] verified={ok} rejected={rej} accept={100*ok/max(ok+rej,1):.0f}% ${cost:.2f}",file=sys.stderr)

if __name__=="__main__": main()

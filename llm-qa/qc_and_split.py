#!/usr/bin/env python3
"""
Plexis-Mind — QC + train/eval split across ALL categories.

QC (the verification gate the strategy promised):
  1. NUMERIC FIDELITY — every number in the ANSWER must trace to a number in the deterministic
     FACT (within tolerance). Catches the one real risk: the phraser inventing/altering a value.
  2. SANITY — non-empty Q & A, answer != question, minimum length.
  3. DEDUP — drop exact-duplicate questions.
Then an ENTITY-HOLDOUT split (hold out whole subzones/PAs so eval measures generalization,
not memorization) → train.jsonl / eval.jsonl + a report.

Usage: python3 qc_and_split.py --root ~/da-sgp/llm-qa --out ~/da-sgp/llm-qa/dataset
"""
import argparse, json, os, re, glob, random, hashlib
random.seed(101)
NUM=re.compile(r'-?\$?\d[\d,]*\.?\d*%?')
def nums(s):
    out=[]
    for t in NUM.findall(s or ""):
        t2=t.replace(",","").replace("$","").replace("%","")
        try: out.append(float(t2))
        except: pass
    return out
def _match(a, fn):
    # direct match to a fact number
    if any(abs(a-f)<=max(0.02*abs(f),0.5) or (f!=0 and abs(a-f)/abs(f)<0.02) for f in fn): return True
    # DERIVED values are legitimate reasoning (e.g. "65% below median" = 100*(1-0.19/0.55)):
    for i,f1 in enumerate(fn):
        for f2 in fn:
            if f2==0: continue
            for d in (100*(1-f1/f2), 100*(f1/f2-1), 100*f1/f2, f1/f2, f1-f2, f1+f2):
                if abs(a-d)<=max(0.02*abs(d),0.5): return True
    return False
def fidelity_ok(fact, answer):
    fn=nums(fact); an=nums(answer)
    if not an: return True   # no numbers in answer -> nothing to falsify
    return all(_match(a, fn) for a in an)

def load_all(root):
    rows=[]
    for path in glob.glob(f"{root}/*/raw/**/*.jsonl",recursive=True):
        if "/pilot" in path: continue
        for l in open(path):
            try: rows.append(json.loads(l))
            except: pass
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=os.path.expanduser("~/da-sgp/llm-qa"))
    ap.add_argument("--out",default=os.path.expanduser("~/da-sgp/llm-qa/dataset"))
    ap.add_argument("--eval-frac",type=float,default=0.06)
    args=ap.parse_args()
    os.makedirs(args.out,exist_ok=True)
    rows=load_all(args.root)
    print(f"loaded {len(rows):,} raw pairs")

    clean=[]; flagged=[]; seenq=set(); stats={}
    for r in rows:
        cat=r.get("category","?"); s=stats.setdefault(cat,dict(n=0,fid_fail=0,dup=0,sanity=0,kept=0))
        s["n"]+=1
        q=(r.get("question") or "").strip(); a=(r.get("answer") or "").strip()
        if len(q)<5 or len(a)<1 or q.lower()==a.lower(): s["sanity"]+=1; flagged.append({**r,"_flag":"sanity"}); continue
        if not fidelity_ok(r.get("fact",""), a): s["fid_fail"]+=1; flagged.append({**r,"_flag":"fidelity"}); continue
        key=hashlib.md5(q.lower().encode()).hexdigest()
        if key in seenq: s["dup"]+=1; continue
        seenq.add(key); s["kept"]+=1; clean.append(r)

    # entity-holdout: hold out whole entities (subzone/PA names) for eval
    ents=sorted({r.get("entity","") for r in clean if r.get("scale") in("subzone","pa")})
    random.shuffle(ents)
    hold=set(ents[:int(len(ents)*args.eval_frac)])
    train=[r for r in clean if r.get("entity") not in hold]
    ev=[r for r in clean if r.get("entity") in hold]

    with open(f"{args.out}/train.jsonl","w") as f:
        for r in train: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    with open(f"{args.out}/eval.jsonl","w") as f:
        for r in ev: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    with open(f"{args.out}/flagged.jsonl","w") as f:
        for r in flagged: f.write(json.dumps(r,ensure_ascii=False)+"\n")

    print("\n=== QC report (per category) ===")
    print(f"{'category':12s} {'raw':>7s} {'kept':>7s} {'fid_fail':>9s} {'dup':>6s} {'sanity':>7s} {'fid%':>6s}")
    for c,s in sorted(stats.items()):
        fidpct=100*(1-s['fid_fail']/max(s['n'],1))
        print(f"{c:12s} {s['n']:7,d} {s['kept']:7,d} {s['fid_fail']:9,d} {s['dup']:6,d} {s['sanity']:7,d} {fidpct:5.1f}%")
    print(f"\nCLEAN total: {len(clean):,}  | held-out entities: {len(hold)} -> train {len(train):,} / eval {len(ev):,}")
    print(f"written to {args.out}/{{train,eval,flagged}}.jsonl")
    json.dump(dict(raw=len(rows),clean=len(clean),train=len(train),eval=len(ev),
                   held_entities=sorted(hold),per_cat=stats),
              open(f"{args.out}/qc_report.json","w"),indent=2)

if __name__=="__main__": main()

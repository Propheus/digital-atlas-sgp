#!/usr/bin/env python3
"""
Plexis-Mind — curate + format the raw Q&A into an SFT-ready dataset.

Steps:
  1. Load every raw shard across all categories.
  2. DOWNSAMPLE the formulaic giants (hex8_multi, quant_*, hex8 attr) so no template dominates.
  3. QC: numeric-fidelity (answer numbers must trace to the fact, derived values allowed) + dedup.
  4. FORMAT into chat: ~70% reason-in-context (Context:{fact}) + ~30% closed-book; abstain/concept
     always closed-book. Loss is on the assistant turn only (handled at train time via a marker).
  5. ENTITY-HOLDOUT split (whole subzones/PAs held out) → train.jsonl / eval.jsonl + stats.

Output records (chat form): {messages:[{role,content}...], meta:{category,kind,scale,entity,mode}}

Usage: python3 curate_and_format.py --root ~/da-sgp/llm-qa --out ~/da-sgp/llm-qa/sft
"""
import argparse, json, os, re, glob, random, hashlib
random.seed(2025)

SYSTEM="You are Plexis-Mind, an assistant that reasons about Singapore's urban geography grounded in the Plexis atlas. Answer precisely; show brief reasoning; if asked about something the atlas does not cover, say so instead of inventing."

# per-kind caps (downsample formulaic; None = keep all). Matched by prefix.
CAPS=[("hex8_multi",15000),("quant_diff_place",6000),("quant_diff_metric",6000),
      ("quant_combine_pop",6000),("hex8_attr",10000)]
def cap_for(kind):
    for pre,c in CAPS:
        if kind.startswith(pre): return c
    return None
# Closed-book = ONLY stable recall + refusal + concepts (the parametric slice). Everything
# numeric/reasoning is reason-in-context, so the model never has to memorise volatile numbers.
def closed_book(kind):
    return (kind.startswith("abstain") or kind=="concept" or kind.startswith("membership")
            or kind in ("attr_dominant_use","attr_archetype_label"))
EXPLAINS_SELF={"concept"}  # closed kinds whose 'reasoning' is a self-contained explanation to keep
def is_abstain(kind): return kind.startswith("abstain")

NUM=re.compile(r'-?\$?\d[\d,]*\.?\d*%?')
def nums(s):
    out=[]
    for t in NUM.findall(s or ""):
        try: out.append(float(t.replace(",","").replace("$","").replace("%","")))
        except: pass
    return out
def _match(a,fn):
    if any(abs(a-f)<=max(0.02*abs(f),0.5) or (f!=0 and abs(a-f)/abs(f)<0.02) for f in fn): return True
    for f1 in fn:
        for f2 in fn:
            if f2==0: continue
            for d in (100*(1-f1/f2),100*(f1/f2-1),100*f1/f2,f1/f2,f1-f2,f1+f2):
                if abs(a-d)<=max(0.02*abs(d),0.5): return True
    return False
def fidelity_ok(fact,answer):
    fn=nums(fact); an=nums(answer)
    return all(_match(a,fn) for a in an) if an else True

def load_all(root):
    pats=[f"{root}/factual/raw/admin/*.jsonl",f"{root}/factual/raw/hex8/*.jsonl",
          f"{root}/places/raw/full/*.jsonl",f"{root}/reasoning/raw/full/*.jsonl",
          f"{root}/reasoning/raw/v2/*.jsonl",f"{root}/reasoning/raw/v3/*.jsonl",
          f"{root}/planning/raw/full/*.jsonl"]
    rows=[]
    for pat in pats:
        for p in glob.glob(pat):
            for l in open(p):
                try: rows.append(json.loads(l))
                except: pass
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=os.path.expanduser("~/da-sgp/llm-qa"))
    ap.add_argument("--out",default=os.path.expanduser("~/da-sgp/llm-qa/sft"))
    ap.add_argument("--eval-frac",type=float,default=0.05)
    args=ap.parse_args(); os.makedirs(args.out,exist_ok=True)
    rows=load_all(args.root); print(f"loaded {len(rows):,} raw")

    # 1) QC + dedup
    clean=[]; seen=set(); dropped={"fid":0,"dup":0,"sanity":0}
    for r in rows:
        q=(r.get("question") or "").strip(); a=(r.get("answer") or "").strip()
        if len(q)<5 or len(a)<1 or q.lower()==a.lower(): dropped["sanity"]+=1; continue
        if r.get("category")!="planning" and not r.get("kind","").startswith("abstain") and not fidelity_ok(r.get("fact",""),a):
            dropped["fid"]+=1; continue
        k=hashlib.md5(q.lower().encode()).hexdigest()
        if k in seen: dropped["dup"]+=1; continue
        seen.add(k); clean.append(r)
    print(f"after QC+dedup: {len(clean):,}  (dropped {dropped})")

    # 2) downsample formulaic per kind
    bykind={}
    for r in clean: bykind.setdefault(r["kind"],[]).append(r)
    curated=[]
    for kind,items in bykind.items():
        c=cap_for(kind)
        if c and len(items)>c: random.shuffle(items); items=items[:c]
        curated.extend(items)
    random.shuffle(curated)
    print(f"after downsample: {len(curated):,}")

    # 3) format to chat + assign mode
    out_recs=[]
    for r in curated:
        kind=r["kind"]; reasoning=(r.get("reasoning") or "").strip(); ans=r["answer"].strip()
        if closed_book(kind):
            m="closed"; user=r["question"]
            # recall kinds: answer only (no phantom-fact reasoning). abstain/concept: keep self-contained text.
            if is_abstain(kind) or kind in EXPLAINS_SELF:
                assistant=(reasoning+"\n\n"+ans).strip() if reasoning else ans
            else:
                assistant=ans
        else:
            m="context"
            assistant=(reasoning+"\n\n"+ans).strip() if reasoning else ans
            user=(f"Context (from the Plexis atlas):\n{r['fact']}\n\nQuestion: {r['question']}"
                  if r.get("fact") else r["question"])
        out_recs.append(dict(messages=[{"role":"system","content":SYSTEM},
                                        {"role":"user","content":user},
                                        {"role":"assistant","content":assistant}],
                             meta=dict(category=r["category"],kind=r["kind"],scale=r.get("scale"),
                                       entity=r.get("entity"),mode=m)))

    # 4) entity-holdout split (hold out whole subzone/PA entities)
    ents=sorted({rec["meta"]["entity"] for rec in out_recs if rec["meta"]["scale"] in("subzone","pa") and rec["meta"]["entity"]})
    random.shuffle(ents); hold=set(ents[:int(len(ents)*args.eval_frac)])
    train=[r for r in out_recs if r["meta"]["entity"] not in hold]
    ev=[r for r in out_recs if r["meta"]["entity"] in hold]
    with open(f"{args.out}/train.jsonl","w") as f:
        for r in train: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    with open(f"{args.out}/eval.jsonl","w") as f:
        for r in ev: f.write(json.dumps(r,ensure_ascii=False)+"\n")

    # 5) stats
    import collections
    cat=collections.Counter(r["meta"]["category"] for r in out_recs)
    fam=collections.Counter(r["meta"]["kind"].split("_")[0] for r in out_recs)
    md=collections.Counter(r["meta"]["mode"] for r in out_recs)
    print(f"\nFINAL: {len(out_recs):,} -> train {len(train):,} / eval {len(ev):,} ({len(hold)} held-out entities)")
    print("by category:", dict(cat))
    print("by family:", dict(fam.most_common()))
    print("by mode:", dict(md))
    json.dump(dict(total=len(out_recs),train=len(train),eval=len(ev),by_category=cat,
                   by_family=dict(fam),by_mode=md,held=sorted(hold)),
              open(f"{args.out}/curation_report.json","w"),indent=2)
    print(f"\nwritten to {args.out}/{{train,eval}}.jsonl")

if __name__=="__main__": main()

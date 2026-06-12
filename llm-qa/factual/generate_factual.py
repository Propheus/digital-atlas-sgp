#!/usr/bin/env python3
"""
Factual Q&A generator for the SGP spatial-reasoning LLM training set.

Principle (see docs/SGP_LLM_QA_STRATEGY.md): Python computes the ground-truth answer
deterministically from the atlas parquet; DeepSeek-v4-flash only *phrases* a natural
question + concise answer + one-line reasoning. The model never invents a number.

Stage 1 (facts) and Stage 3 (generation) for the Factual category only.

Usage:
  python3 generate_factual.py --n 25  --batch 8 --out raw/pilot.jsonl          # pilot
  python3 generate_factual.py --n 50000 --batch 10 --concurrency 8 --out raw/factual_50k.jsonl
"""
import argparse, json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ATLAS = "/home/azureuser/da-sgp/v4"
KEY = open(os.path.expanduser("~/notes/openrouter-kosha.txt")).read().strip()
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

# ---- metric label / unit dictionary (drives natural fact statements) -------------
METRICS = {
    "pop_resident":        ("resident population",                "people",   0),
    "pop_65plus":          ("residents aged 65+",                 "people",   0),
    "pop_dorm":            ("migrant-worker dormitory population","people",   0),
    "nonres_share":        ("non-resident share of population",   "ratio",    2),
    "lu_residential_pct":  ("residential land-use share",         "ratio",    2),
    "lu_commercial_pct":   ("commercial land-use share",          "ratio",    2),
    "lu_entropy":          ("land-use mix (entropy)",             "nats",     2),
    "avg_gpr":             ("average gross plot ratio",           "",         2),
    "bldg_count":          ("number of buildings",                "buildings",0),
    "bus_stop_count":      ("number of bus stops",                "stops",    0),
    "hawker_centre_count": ("number of hawker centres",           "centres",  0),
    "school_count_total":  ("number of schools",                  "schools",  0),
    "vibrancy_index":      ("vibrancy index",                     "0-1",      3),
    "walkability_score":   ("walkability score",                  "0-1",      3),
}

def fmt(v, dec):
    if dec == 0: return f"{round(v):,}"
    return f"{v:.{dec}f}"

def build_facts(limit=None):
    """Deterministic fact rows from the subzone master. Each carries provenance + a
    plain-language statement that is the *sole* ground truth handed to the phraser."""
    import pandas as pd
    sz = pd.read_parquet(f"{ATLAS}/hex/subzone_all_features.parquet")
    u  = pd.read_parquet(f"{ATLAS}/hex/hex9_universe.parquet")[
            ["parent_subzone","parent_subzone_name","parent_pa","parent_region"]
         ].drop_duplicates("parent_subzone")
    u.columns = ["subzone_c","name","pa","region"]
    df = sz.merge(u, on="subzone_c", how="left")
    df["name"]   = df["name"].str.title()
    df["region"] = df["region"].str.title()
    df["pa"]     = df["pa"].str.title()

    facts = []
    # (A) membership facts — closed-book safe (stable geography)
    for _, r in df.iterrows():
        facts.append({"kind":"membership_region","entity":r["name"],
            "stmt":f"The subzone {r['name']} is in the {r['pa']} planning area, in {r['region']} of Singapore.",
            "prov":{"file":"subzone_all_features.parquet","key":r["subzone_c"],"col":"parent_region"}})
    # (B) attribute lookups — evidence-grounded
    for _, r in df.iterrows():
        for col,(label,unit,dec) in METRICS.items():
            v = r[col]
            us = f" {unit}" if unit and unit not in ("ratio","0-1","nats","") else ""
            facts.append({"kind":f"attr_{col}","entity":r["name"],
                "stmt":f"According to the Singapore atlas, the subzone {r['name']} "
                       f"({r['pa']}, {r['region']}) has a {label} of {fmt(v,dec)}{us}.",
                "prov":{"file":"subzone_all_features.parquet","key":r["subzone_c"],"col":col,"value":float(v)}})
    # (C) superlatives within region + overall — ranking facts
    for col,(label,unit,dec) in METRICS.items():
        for scope_name, sub in [("Singapore", df)] + [(reg, df[df.region==reg]) for reg in df.region.unique()]:
            top = sub.loc[sub[col].idxmax()]; bot = sub.loc[sub[col].idxmin()]
            facts.append({"kind":f"max_{col}","entity":top["name"],
                "stmt":f"Among subzones in {scope_name}, {top['name']} has the highest {label} ({fmt(top[col],dec)}).",
                "prov":{"file":"subzone_all_features.parquet","key":top["subzone_c"],"col":col,"scope":scope_name,"rank":"max"}})
            facts.append({"kind":f"min_{col}","entity":bot["name"],
                "stmt":f"Among subzones in {scope_name}, {bot['name']} has the lowest {label} ({fmt(bot[col],dec)}).",
                "prov":{"file":"subzone_all_features.parquet","key":bot["subzone_c"],"col":col,"scope":scope_name,"rank":"min"}})
    if limit: facts = facts[:limit]
    for i,f in enumerate(facts): f["fid"] = i
    return facts

# ---- DeepSeek phrasing ------------------------------------------------------------
SYS = (
 "You convert atlas FACTS into natural-language training Q&A for a Singapore spatial-"
 "reasoning model. For EACH fact, write ONE question a real user would ask and a concise, "
 "correct answer. RULES: (1) Use ONLY the information in the fact — never add a number, "
 "place, or claim not present. (2) The answer must be directly supported by the fact. "
 "(3) 'reasoning' = one short sentence naming the value/source used. (4) Vary phrasing "
 "across items; some direct, some conversational. Return a JSON array, one object per fact, "
 "each: {\"fid\": <int>, \"question\": str, \"reasoning\": str, \"answer\": str}. JSON only."
)

def call(batch, model, retries=4):
    facts_txt = "\n".join(f'fid={f["fid"]}: {f["stmt"]}' for f in batch)
    body = json.dumps({
        "model": model,
        "messages":[{"role":"system","content":SYS},
                    {"role":"user","content":f"FACTS:\n{facts_txt}"}],
        "temperature":0.7, "max_tokens": 220*len(batch),
        "response_format":{"type":"json_object"} if False else None,
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Authorization":f"Bearer {KEY}", "Content-Type":"application/json",
        "X-Title":"sgp-llm-qa-factual"})
    for a in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read())
            txt = d["choices"][0]["message"]["content"]
            usage = d.get("usage",{})
            # tolerant JSON extraction
            s=txt.find("["); e=txt.rfind("]")
            arr = json.loads(txt[s:e+1]) if s>=0 else json.loads(txt)
            return arr, usage
        except Exception as ex:
            if a==retries-1: return {"error":str(ex)}, {}
            time.sleep(2*(a+1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out", default="raw/pilot.jsonl")
    ap.add_argument("--dump-facts", action="store_true")
    args = ap.parse_args()

    facts = build_facts(limit=args.n)
    if args.dump_facts:
        for f in facts[:20]: print(f["stmt"])
        print(f"... total facts available (n cap={args.n}): {len(facts)}"); return
    print(f"[facts] {len(facts)} facts | model={args.model} | batch={args.batch}", file=sys.stderr)
    by_fid = {f["fid"]: f for f in facts}
    batches = [facts[i:i+args.batch] for i in range(0, len(facts), args.batch)]

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    tin=tout=ok=bad=0; t0=time.time()
    with open(args.out,"w") as out, ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(call, b, args.model): b for b in batches}
        for fut in as_completed(futs):
            arr, usage = fut.result()
            tin += usage.get("prompt_tokens",0); tout += usage.get("completion_tokens",0)
            if isinstance(arr, dict):  # error
                bad += len(futs[fut]); continue
            for o in arr:
                f = by_fid.get(o.get("fid"))
                if not f or not o.get("question") or not o.get("answer"): bad+=1; continue
                rec = {"category":"factual","kind":f["kind"],"entity":f["entity"],
                       "question":o["question"].strip(),"reasoning":o.get("reasoning","").strip(),
                       "answer":o["answer"].strip(),"fact":f["stmt"],"provenance":f["prov"]}
                out.write(json.dumps(rec, ensure_ascii=False)+"\n"); ok+=1
    dt=time.time()-t0
    cost = tin/1e6*0.0983 + tout/1e6*0.1966
    print(f"[done] ok={ok} bad={bad} | prompt_tok={tin:,} compl_tok={tout:,} | "
          f"cost=${cost:.4f} | {dt:.1f}s | -> {args.out}", file=sys.stderr)
    print(json.dumps({"ok":ok,"bad":bad,"prompt_tok":tin,"compl_tok":tout,"cost_usd":round(cost,4),
                      "per_1k_pairs_usd":round(cost/max(ok,1)*1000,3)}))

if __name__ == "__main__":
    main()

"""
V2 #2 — LLM brand resolution over the still-unbranded places (conservative).
Returns a canonical chain brand ONLY for clear multi-outlet chains, else null.
Updates places/sgp_places_v2.parquet brand_norm in place; reports coverage.
"""
import json, re, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, pandas as pd

ROOT = Path("/home/azureuser/da-sgp/v5")
KEY = open("/home/azureuser/notes/openrouter-llm-build-key.txt").read().strip().split()[0]
MODEL = "anthropic/claude-3.5-haiku"

p = pd.read_parquet(ROOT/"places/sgp_places_v2.parquet")
need = p[p["brand_norm"].isna()].copy()
idx = need.index.tolist()
names = need["name"].fillna("(no name)").tolist()
cats = need["plexis_category"].fillna("").tolist()
print(f"unbranded to resolve: {len(names):,}", flush=True)

BATCH = 30
batches = [(i, list(zip(names[i:i+BATCH], cats[i:i+BATCH]))) for i in range(0, len(names), BATCH)]

SYS = ("You map Singapore place names to their CHAIN/FRANCHISE brand. Rules: return the "
       "canonical brand ONLY if the place is clearly an outlet of a known multi-outlet chain "
       "or franchise (e.g. 7-Eleven, McDonald's, Watsons, Challenger, Sheng Siong, Bata, "
       "Charles & Keith, OSIM, Decathlon, Tangs). If it is an independent/standalone business, "
       "a generic name, an address, or you are unsure -> return null. Be conservative — false "
       "brands are worse than nulls.")

def resolve(start, items):
    listing = "\n".join(f"{j+1}. {n[:70]} [{c}]" for j,(n,c) in enumerate(items))
    prompt = (f"{SYS}\n\nPlaces:\n{listing}\n\nReturn ONLY a JSON array of {len(items)} values "
              f"in order: the brand string, or null. No prose.")
    for _ in range(3):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {KEY}"},
                json={"model": MODEL, "messages":[{"role":"user","content":prompt}],
                      "max_tokens": 900, "temperature": 0}, timeout=60)
            if r.status_code != 200: time.sleep(2); continue
            txt = r.json()["choices"][0]["message"]["content"]
            m = re.search(r"\[.*\]", txt, re.S)
            arr = json.loads(m.group(0)) if m else []
            out = []
            for v in arr:
                if v is None or str(v).strip().lower() in ("null","none","",): out.append(None)
                else:
                    b = str(v).strip()
                    out.append(b if 1 < len(b) < 40 else None)
            return start, (out + [None]*len(items))[:len(items)]
        except Exception: time.sleep(2)
    return start, [None]*len(items)

t0 = time.time(); results = {}; done = 0
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = [ex.submit(resolve, s, it) for s, it in batches]
    for f in as_completed(futs):
        s, out = f.result(); results[s] = out; done += 1
        if done % 200 == 0: print(f"  {done}/{len(batches)} · {round(time.time()-t0)}s", flush=True)

brands = []
for s,_ in batches: brands.extend(results[s])
assert len(brands) == len(idx)
ser = pd.Series(brands, index=idx)
n_new = int(ser.notna().sum())
p.loc[idx, "brand_norm"] = ser.values
if "brand_source" in p.columns:
    p.loc[ser.dropna().index, "brand_source"] = "llm"
p.to_parquet(ROOT/"places/sgp_places_v2.parquet", index=False)
cov = int(p["brand_norm"].notna().sum())
print(f"\n=== LLM BRAND ===\nresolved {n_new:,} new brands · coverage {cov:,} ({100*cov/len(p):.1f}%) · {round(time.time()-t0)}s")
top = p.loc[idx][ser.notna().values]["brand_norm"].value_counts().head(15)
print("top newly-resolved brands:"); print(top.to_string())
json.dump({"resolved": n_new, "coverage": cov, "coverage_pct": round(100*cov/len(p),1),
           "secs": round(time.time()-t0)}, open(ROOT/"places/llm_brand_report.json","w"), indent=1)

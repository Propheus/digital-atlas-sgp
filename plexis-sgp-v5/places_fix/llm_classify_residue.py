"""
Stage 5b — LLM reclassification of the other_uncategorized residue (nous #7).
Batched (25/call) + concurrent Haiku over the expanded 26-category taxonomy.
Updates places/sgp_places_cleaned.parquet in place; reports reclassified vs residual.
"""
import json, re, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, pandas as pd

ROOT = Path("/home/azureuser/da-sgp/v5")
KEY = open("/home/azureuser/notes/openrouter-llm-build-key.txt").read().strip().split()[0]
MODEL = "anthropic/claude-3.5-haiku"
CATS = ["cafe_coffee","restaurant","fast_food","hawker","bakery","bar_nightlife",
        "convenience","supermarket","shopping_retail","health_medical","beauty_personal",
        "fitness_recreation","education","services","business_office","hotel_hospitality",
        "entertainment_culture","transportation","government_public","religious_worship",
        "industrial_mfg","residential","park_open","financial_services","automated_kiosk",
        "other_uncategorized"]
CATSET = set(CATS)
HINTS = ("Singapore context. durian/fruit stalls->supermarket; steakhouse/grill/bbq/"
         "hotpot/buffet/bistro->restaurant; gold/jewellery->shopping_retail; therapy/"
         "rehab/chiropractic/TCM->health_medical; study pod/enrichment/tuition->education; "
         "coworking/Pte Ltd/holdings->business_office; durian DELIVERY/online->services. "
         "Use other_uncategorized ONLY if truly impossible.")

p = pd.read_parquet(ROOT / "places/sgp_places_cleaned.parquet")
res = p[p["plexis_category"] == "other_uncategorized"].copy()
names = res["name"].fillna("(no name)").tolist()
idx = res.index.tolist()
print(f"residue to classify: {len(names):,}", flush=True)

BATCH = 25
batches = [(i, names[i:i+BATCH]) for i in range(0, len(names), BATCH)]

def classify_batch(start, batch):
    listing = "\n".join(f"{j+1}. {n[:80]}" for j, n in enumerate(batch))
    prompt = (f"Classify each Singapore place into ONE category from:\n{', '.join(CATS)}\n{HINTS}\n\n"
              f"Places:\n{listing}\n\nReturn ONLY a JSON array of {len(batch)} lowercase category "
              f"strings in order, no prose.")
    for attempt in range(3):
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {KEY}"},
                json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                      "max_tokens": 700, "temperature": 0}, timeout=60)
            if r.status_code != 200:
                time.sleep(2); continue
            txt = r.json()["choices"][0]["message"]["content"]
            m = re.search(r"\[.*\]", txt, re.S)
            arr = json.loads(m.group(0)) if m else []
            out = []
            for c in arr:
                c = str(c).strip().lower().replace(" ", "_")
                out.append(c if c in CATSET else "other_uncategorized")
            # pad/truncate to batch length
            out = (out + ["other_uncategorized"] * len(batch))[:len(batch)]
            return start, out
        except Exception:
            time.sleep(2)
    return start, ["other_uncategorized"] * len(batch)

t0 = time.time()
results = {}
done = 0
with ThreadPoolExecutor(max_workers=16) as ex:
    futs = [ex.submit(classify_batch, s, b) for s, b in batches]
    for f in as_completed(futs):
        s, out = f.result()
        results[s] = out
        done += 1
        if done % 50 == 0:
            print(f"  {done}/{len(batches)} batches · {round(time.time()-t0)}s", flush=True)

# apply
new_cats = []
for s, _ in batches:
    new_cats.extend(results[s])
assert len(new_cats) == len(idx)
res_new = pd.Series(new_cats, index=idx)
n_reclassed = int((res_new != "other_uncategorized").sum())
p.loc[idx, "plexis_category"] = res_new.values
# is_storefront stays as computed; refresh for newly-known commercial cats is fine
p.to_parquet(ROOT / "places/sgp_places_cleaned.parquet", index=False)

dist = res_new.value_counts().to_dict()
print(f"\n=== LLM RECLASSIFICATION ===")
print(f"residue {len(idx):,} -> reclassified {n_reclassed:,} · still other {len(idx)-n_reclassed:,} · {round(time.time()-t0)}s")
print("where they went:")
for c, n in sorted(dist.items(), key=lambda x: -x[1]):
    if c != "other_uncategorized":
        print(f"  {c:24s} {n:>6,}")
json.dump({"residue": len(idx), "reclassified": n_reclassed,
           "still_other": len(idx)-n_reclassed, "distribution": {k:int(v) for k,v in dist.items()},
           "secs": round(time.time()-t0)},
          open(ROOT / "places/llm_reclassify_report.json", "w"), indent=1)
print("report -> places/llm_reclassify_report.json")

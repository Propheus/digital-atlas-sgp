"""
Plexis SGP v4 — Stage 1b.2b — LLM classification of residue.
Calls OpenRouter/Gemini Flash with batches of ~50 places. Results cached to a
jsonl so the run is resumable.
"""
import os, json, time, hashlib, sys
from pathlib import Path
import pandas as pd
import urllib.request
import urllib.error

ROOT = Path(__file__).parent
IN_PQ = ROOT / "places/sgp_places_unresolved_after_heuristics.parquet"
CACHE = ROOT / "places/llm_category_cache.jsonl"
OUT_PQ = ROOT / "places/sgp_places_categorized.parquet"
REPORT = ROOT / "places/llm_report.json"

MODEL = "google/gemini-2.0-flash-001"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
BATCH = 50

TAXONOMY = [
    "cafe_coffee", "restaurant", "fast_food", "hawker", "bakery", "bar_nightlife",
    "convenience", "supermarket", "shopping_retail", "health_medical",
    "beauty_personal", "fitness_recreation", "education", "services",
    "business_office", "hotel_hospitality", "entertainment_culture",
    "transportation", "government_public", "religious_worship",
    "industrial_mfg", "residential", "park_open", "other_uncategorized",
]

PROMPT_SYSTEM = (
    "You classify Singapore places into one of these 24 categories. Return ONLY JSON. "
    "Categories:\n"
    "cafe_coffee | restaurant | fast_food | hawker | bakery | bar_nightlife | "
    "convenience | supermarket | shopping_retail | health_medical | beauty_personal | "
    "fitness_recreation | education | services | business_office | hotel_hospitality | "
    "entertainment_culture | transportation | government_public | religious_worship | "
    "industrial_mfg | residential | park_open | other_uncategorized\n\n"
    "Rules:\n"
    "- `hawker` = hawker stalls, food courts, kopitiams (Singapore-specific)\n"
    "- `services` = professional/personal services (repair, cleaning, law, consulting)\n"
    "- `business_office` = corporate HQ, banks, insurers, trading/holding companies\n"
    "- `industrial_mfg` = manufacturer, warehouse, wholesaler, construction, logistics\n"
    "- `transportation` = stops, stations, carparks, petrol, EV charging, jetties, street addresses with no venue\n"
    "- `residential` = HDB blocks, condos, apartments, serviced residences\n"
    "- `other_uncategorized` = only if truly unclassifiable\n\n"
    "Output JSON format: {\"results\": [{\"i\": <row_idx>, \"cat\": \"<category>\"}, ...]}"
)


def call_openrouter(messages):
    body = json.dumps({
        "model": MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://plexis.local",
            "X-Title": "Plexis SGP v4",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"]
    return json.loads(content)


def batch_key(rows):
    """Stable hash over the batch of (name, address) so cache is content-addressed."""
    h = hashlib.sha1()
    for r in rows:
        h.update((str(r.get("name") or "") + "|" + str(r.get("address") or "") + "\n").encode())
    return h.hexdigest()


def load_cache():
    cache = {}
    if CACHE.exists():
        with open(CACHE) as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    cache[rec["key"]] = rec["map"]
                except Exception:
                    pass
    return cache


def append_cache(key, mapping):
    with open(CACHE, "a") as f:
        f.write(json.dumps({"key": key, "map": mapping}) + "\n")


def classify_batch(rows):
    """rows: list of dicts with keys i, name, address. Returns {i: category}."""
    if not rows:
        return {}
    names = [{"i": r["i"], "name": (r.get("name") or "")[:120], "address": (r.get("address") or "")[:100]} for r in rows]
    user = "Classify each place:\n" + json.dumps(names, ensure_ascii=False)
    msgs = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user},
    ]
    for attempt in range(3):
        try:
            parsed = call_openrouter(msgs)
            out = {}
            for item in parsed.get("results", []):
                i = int(item.get("i"))
                cat = str(item.get("cat") or "").strip()
                if cat in TAXONOMY:
                    out[i] = cat
            return out
        except urllib.error.HTTPError as e:
            sys.stderr.write(f"\nHTTP error {e.code} (attempt {attempt+1}): {e.read()[:200].decode(errors='ignore')}\n")
            time.sleep(2 ** attempt)
        except Exception as e:
            sys.stderr.write(f"\nError (attempt {attempt+1}): {e}\n")
            time.sleep(2 ** attempt)
    return {}


def main():
    t0 = time.time()
    df_all = pd.read_parquet(OUT_PQ)
    df_residue = pd.read_parquet(IN_PQ)
    print(f"Full table: {len(df_all):,}")
    print(f"Residue to classify: {len(df_residue):,}")

    # Build batch queue (with stable integer keys = df_residue row index)
    items = []
    for i, row in df_residue.reset_index(drop=True).iterrows():
        items.append({
            "i": int(i),
            "name": row.get("name"),
            "address": row.get("address"),
            "place_id": row.get("id"),
        })

    cache = load_cache()
    print(f"Cache entries: {len(cache)}")

    results = {}  # place_id -> cat
    batches_processed = 0
    batches_cached = 0
    failures = 0
    for start in range(0, len(items), BATCH):
        batch = items[start:start + BATCH]
        key = batch_key(batch)
        if key in cache:
            m = cache[key]
            for it in batch:
                if str(it["i"]) in m:
                    results[it["place_id"]] = m[str(it["i"])]
            batches_cached += 1
            continue
        out = classify_batch(batch)
        if not out:
            failures += 1
            continue
        # Persist mapping by local index
        append_cache(key, {str(k): v for k, v in out.items()})
        for it in batch:
            cat = out.get(it["i"])
            if cat:
                results[it["place_id"]] = cat
        batches_processed += 1
        if batches_processed % 10 == 0:
            classified = len(results)
            rate = classified / (time.time() - t0)
            pct_done = 100 * (start + BATCH) / len(items)
            print(f"  {pct_done:5.1f}% | batches done={batches_processed} cached={batches_cached} | classified={classified:,} | {rate:.0f}/s | elapsed={(time.time()-t0)/60:.1f}m")

    print(f"\nBatches: processed={batches_processed} cached={batches_cached} failed={failures}")
    print(f"Classified via LLM: {len(results):,}")

    # Merge into main table
    id_to_cat = results
    mask = df_all["id"].isin(id_to_cat.keys()) & df_all["plexis_category"].isna()
    df_all.loc[mask, "plexis_category"] = df_all.loc[mask, "id"].map(id_to_cat)
    # Any remaining nulls -> other_uncategorized (can't decide)
    still_null = df_all["plexis_category"].isna().sum()
    if still_null:
        print(f"Filling {still_null:,} remaining nulls with 'other_uncategorized'")
        df_all["plexis_category"] = df_all["plexis_category"].fillna("other_uncategorized")

    df_all.to_parquet(OUT_PQ, index=False)
    cat_counts = df_all["plexis_category"].value_counts()
    print("\n=== Final Plexis category distribution ===")
    for cat, c in cat_counts.items():
        print(f"  {c:>7,}  {cat}")

    resolved = (df_all["plexis_category"] != "other_uncategorized").sum()
    print(f"\nFinal resolved (non-uncategorized): {resolved:,} / {len(df_all):,} = {100*resolved/len(df_all):.2f}%")

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "residue_in": len(df_residue),
        "classified_via_llm": len(results),
        "batches_processed": batches_processed,
        "batches_cached": batches_cached,
        "batches_failed": failures,
        "final_distribution": {k: int(v) for k, v in cat_counts.items()},
        "final_resolved_non_uncategorized": int(resolved),
        "final_resolution_rate_pct": round(100 * resolved / len(df_all), 4),
        "wall_clock_s": round(time.time() - t0, 2),
    }
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport: {REPORT}")


if __name__ == "__main__":
    main()

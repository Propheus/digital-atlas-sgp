"""
Plexis SGP v4 — S4 prep: geocode unique ACRA postal codes via OneMap.

SG postal codes are building-precise. 91,546 unique codes from
data/business/acra_entities.csv -> OneMap elastic search (free, no auth,
~250 req/min limit). Resume-safe: appends to a jsonl cache keyed by postal;
re-running skips cached codes. Expect ~6-7 h on first run.

Output: ../data/external/onemap_postal_cache.jsonl
        {"postal": "189648", "lat": 1.297, "lng": 103.852, "found": true}
"""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).parent
CACHE = ROOT.parent / "data/external/onemap_postal_cache.jsonl"
URL = ("https://www.onemap.gov.sg/api/common/elastic/search"
       "?searchVal={p}&returnGeom=Y&getAddrDetails=Y&pageNum=1")
# OneMap latency is ~3 s/request — sequential ran at 18/min (3.5 days).
# 12 workers ~= 240 req/min, just under the documented 250/min limit.
WORKERS = 12
RETRY_SLEEP = 30.0


def main():
    a = pd.read_csv(ROOT.parent / "data/business/acra_entities.csv",
                    usecols=["reg_postal_code"], dtype=str)
    pc = a["reg_postal_code"].dropna().str.zfill(6)
    postals = sorted(pc[pc.str.match(r"^\d{6}$")].unique())

    done = set()
    if CACHE.exists():
        with open(CACHE) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["postal"])
                except json.JSONDecodeError:
                    pass
    todo = [p for p in postals if p not in done]
    print(f"{len(postals):,} unique postals, {len(done):,} cached, {len(todo):,} to go")

    lock = threading.Lock()
    counter = {"n": 0}
    t0 = time.time()
    local = threading.local()

    def fetch(p):
        if not hasattr(local, "sess"):
            local.sess = requests.Session()
        rec = {"postal": p, "found": False}
        for attempt in range(4):
            try:
                r = local.sess.get(URL.format(p=p), timeout=15)
                if r.status_code == 429:
                    time.sleep(RETRY_SLEEP)
                    continue
                r.raise_for_status()
                res = r.json().get("results") or []
                hit = next((x for x in res if x.get("POSTAL") == p), None) \
                    or (res[0] if res else None)
                if hit:
                    rec.update(found=True, lat=float(hit["LATITUDE"]),
                               lng=float(hit["LONGITUDE"]))
                break
            except Exception:
                time.sleep(RETRY_SLEEP * (attempt + 1))
        with lock:
            out.write(json.dumps(rec) + "\n")
            counter["n"] += 1
            if counter["n"] % 1000 == 0:
                rate = counter["n"] / (time.time() - t0)
                eta_h = (len(todo) - counter["n"]) / rate / 3600
                print(f"  {counter['n']:,}/{len(todo):,}  {rate:.1f}/s  "
                      f"ETA {eta_h:.1f} h", flush=True)

    with open(CACHE, "a", buffering=1) as out:   # line-buffered: resume-safe
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            list(ex.map(fetch, todo))
    print("done")


if __name__ == "__main__":
    main()

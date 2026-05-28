"""Geocode MOM FEDA dorm list via OneMap, concurrently.

Cached to JSONL — restart-safe.
"""

import csv, json, re, sys, urllib.parse, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

INP = Path('data/external/mom/migrant-worker-dormitories.csv')
OUT = Path('data/external/mom/migrant-worker-dormitories.geocoded.jsonl')
CACHE = Path('data/external/mom/.onemap_cache.jsonl')

cache = {}
cache_lock = threading.Lock()

def load_cache(skip_bad=True):
    """Skip cached nulls for keys that look like junk (non-postal artifacts).
    Real successful hits are preserved; bad-postal nulls are dropped so they retry."""
    valid_postal = re.compile(r'^([012345678]\d{5})$')
    if not CACHE.exists(): return
    keep = []
    for line in CACHE.open():
        try: rec = json.loads(line)
        except Exception: continue
        k, v = rec['key'], rec['result']
        # If this is a postal-code-shaped key and result is null, drop it (retry)
        if skip_bad and v is None and valid_postal.match(k):
            continue
        cache[k] = v
        keep.append(rec)
    print(f'Loaded {len(cache)} cached hits (after pruning null-postal misses)')
    # rewrite cache
    if skip_bad:
        with CACHE.open('w') as f:
            for r in keep:
                f.write(json.dumps(r) + '\n')

def onemap(q):
    with cache_lock:
        if q in cache:
            return cache[q]
    url = f'https://www.onemap.gov.sg/api/common/elastic/search?searchVal={urllib.parse.quote(q)}&returnGeom=Y&getAddrDetails=Y&pageNum=1'
    result = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
                results = data.get('results') or []
                if results:
                    result = results[0]
                    break
                # No results — don't retry the same query
                break
        except Exception:
            import time as _t
            _t.sleep(0.3 + attempt * 0.5)
    with cache_lock:
        cache[q] = result
        with CACHE.open('a') as f:
            f.write(json.dumps({'key': q, 'result': result}) + '\n')
    return result

def primary_query(row):
    addr = (row['address'] or '').strip()
    # Singapore postal codes only valid when preceded by "SINGAPORE " — guards against
    # the regex matching survey/lot number fragments like "200231" inside "200231975W0087"
    m = re.search(r'SINGAPORE\s+(\d{6})\b', addr, re.IGNORECASE)
    if m:
        return m.group(1)
    # Sometimes addresses end with bare 6-digit postal code without "Singapore"
    m = re.search(r'\b(\d{6})\b\s*$', addr)
    if m and m.group(1)[:2] in ('01','02','03','04','05','06','07','08','09',
                                '10','11','12','13','14','15','16','17','18','19',
                                '20','21','22','23','24','25','26','27','28','29',
                                '30','31','32','33','34','35','36','37','38','39',
                                '40','41','42','43','44','45','46','47','48','49',
                                '50','51','52','53','54','55','56','57','58','59',
                                '60','61','62','63','64','65','66','67','68','69',
                                '70','71','72','73','74','75','76','77','78','79',
                                '80','81','82'):
        return m.group(1)
    # No postal — strip leading survey-mark blobs and search by remaining street text
    cleaned = re.sub(r'^[A-Z]{2}\d{2}[-\s][A-Z0-9,\s\.\(\)/]+?(?=\b[A-Z][a-z])', '', addr).strip(' ,')
    cleaned = re.sub(r'^\([A-Z]{3,4}\)\s*', '', cleaned).strip()  # strip (CTQ), (TOLQ) etc
    cleaned = re.sub(r'\(.+?\)', '', cleaned).strip()  # strip any parenthetical
    return cleaned or addr

def process(row):
    q = primary_query(row)
    r = onemap(q)
    out_row = dict(row)
    if r:
        out_row['lat'] = float(r['LATITUDE'])
        out_row['lng'] = float(r['LONGITUDE'])
        out_row['geocode_addr'] = r['ADDRESS']
        out_row['geocode_q'] = q
        out_row['geocode_method'] = 'postal' if re.match(r'^\d{6}$', q) else 'address'
    else:
        out_row['lat'] = None
        out_row['lng'] = None
        out_row['geocode_addr'] = ''
        out_row['geocode_q'] = q
        out_row['geocode_method'] = 'miss'
    return out_row

def main():
    load_cache(skip_bad=True)
    rows = list(csv.DictReader(INP.open()))
    print(f'Geocoding {len(rows)} dorms with 8 workers (gentle on OneMap)…')
    results = [None] * len(rows)
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(process, r): i for i, r in enumerate(rows)}
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            done += 1
            if done % 200 == 0:
                print(f'  {done}/{len(rows)}', flush=True)

    miss = sum(1 for r in results if r['lat'] is None)
    with OUT.open('w') as f:
        for r in results:
            f.write(json.dumps(r) + '\n')
    print(f'\nDone. Total: {len(results)}, missed: {miss} ({miss/len(results)*100:.1f}%)')
    print(f'Output: {OUT}')

if __name__ == '__main__':
    main()

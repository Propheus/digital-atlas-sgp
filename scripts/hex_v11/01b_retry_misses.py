"""Retry geocoding misses with a smarter street-name extractor.

Strategy: grab the trailing road/lane/street/avenue/drive/etc from addresses
that lack a postal code. Survey marks like "MK28-06542A" and lot IDs like
"199705919M0103" sit at the front; the actual street name is at the end.
"""

import json, re, urllib.parse, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

INP = Path('data/external/mom/migrant-worker-dormitories.geocoded.jsonl')
CACHE = Path('data/external/mom/.onemap_cache.jsonl')

cache = {}
cache_lock = threading.Lock()
if CACHE.exists():
    for line in CACHE.open():
        try:
            rec = json.loads(line)
            cache[rec['key']] = rec['result']
        except Exception:
            pass

STREET_RE = re.compile(
    r'((?:[A-Z][\w\d\']*\s+){0,4}'
    r'(?:Road|Rd|Street|St|Lane|Ln|Avenue|Ave|Drive|Dr|Crescent|Cres|Walk|Way|Loop|Link|Close|Park|Place|Highway|Hwy|Terrace|Quay|Industrial Park|Industrial Estate|Vista|View)'
    r'(?:\s+\d+\w*)?)', re.IGNORECASE)

def smart_street_query(addr):
    """Return the cleanest street/place name we can extract."""
    a = addr.strip()
    # Remove parentheticals
    a = re.sub(r'\(.+?\)', ' ', a)
    # Remove leading survey-mark / lot-number blobs
    a = re.sub(r'^[\dA-Z]+[A-Z]\d*[\s,]*', '', a)  # e.g. "199705919M0103, "
    # Remove "MKxx-xxxxx", "TSxx-xxxxx", "LTxx-xxxxx" survey markers
    a = re.sub(r'\b(MK|TS|LT|HG)\d{1,2}[-\s][A-Z0-9]+\s*[A-Z]*\s*&?\s*', ' ', a, flags=re.IGNORECASE)
    a = re.sub(r'\bPT\b', ' ', a)
    a = re.sub(r'\s+', ' ', a).strip(' ,')
    # Last comma chunk often has the cleanest street name
    last = a.split(',')[-1].strip(' .')
    # Try regex match on it
    m = STREET_RE.search(last)
    if m:
        return m.group(1).strip()
    # Else give the whole cleaned trailing chunk
    return last or a

def onemap(q):
    if not q or len(q) < 4: return None
    with cache_lock:
        if q in cache:
            return cache[q]
    url = f'https://www.onemap.gov.sg/api/common/elastic/search?searchVal={urllib.parse.quote(q)}&returnGeom=Y&getAddrDetails=Y&pageNum=1'
    result = None
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read())
            results = data.get('results') or []
            if results:
                result = results[0]
    except Exception:
        pass
    with cache_lock:
        cache[q] = result
        with CACHE.open('a') as f:
            f.write(json.dumps({'key': q, 'result': result}) + '\n')
    return result

def main():
    rows = [json.loads(l) for l in INP.open()]
    misses = [r for r in rows if r['lat'] is None]
    print(f'Retrying {len(misses)} misses with street extractor…')

    def process(r):
        q = smart_street_query(r['address'])
        if not q: return r, None, q
        res = onemap(q)
        return r, res, q

    recovered = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(process, r): r for r in misses}
        done = 0
        for fut in as_completed(futs):
            r, res, q = fut.result()
            done += 1
            if res:
                r['lat'] = float(res['LATITUDE'])
                r['lng'] = float(res['LONGITUDE'])
                r['geocode_addr'] = res['ADDRESS']
                r['geocode_q'] = q
                r['geocode_method'] = 'street_retry'
                recovered += 1
            if done % 200 == 0:
                print(f'  {done}/{len(misses)} | recovered {recovered}', flush=True)

    # rewrite full file
    with INP.open('w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')

    final_miss = sum(1 for r in rows if r['lat'] is None)
    print(f'\nRecovered {recovered}; final miss = {final_miss} ({final_miss/len(rows)*100:.1f}%)')

if __name__ == '__main__':
    main()

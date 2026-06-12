#!/usr/bin/env python3
"""Plexis-Mind training-set explorer — browse / filter / debate the Q&A.
   python3 browse_server.py [PORT]   (default 18090)"""
import json, glob, os, re, random, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]) if len(sys.argv)>1 else 18090
ROOT = os.path.expanduser("~/da-sgp/llm-qa")
SOURCES = [  # (glob, label, cap)
 ("factual/raw/admin/*.jsonl","factual",None),("factual/raw/hex8/*.jsonl","factual",None),
 ("places/raw/full/*.jsonl","flash",None),("reasoning/raw/full/*.jsonl","flash",None),
 ("reasoning/raw/v2/*.jsonl","flash",15000),("reasoning/raw/v3/*.jsonl","flash",None),
 ("planning/raw/full/*.jsonl","flash",None),("distill/full/*.jsonl","distilled",None),
 ("simple/full/*.jsonl","casual",None),("casual/full/*.jsonl","casual",None),
]
SRC_LABEL={"distilled":"distilled (v4-pro deep)","casual":"casual / human"}
DATA=[]; FACETS={"category":{}, "kind":{}, "source":{}}

def load():
    for pat,src,cap in SOURCES:
        rows=[]
        for p in glob.glob(f"{ROOT}/{pat}"):
            for l in open(p):
                try: r=json.loads(l)
                except: continue
                rows.append(r)
        if cap and len(rows)>cap: random.shuffle(rows); rows=rows[:cap]
        label=SRC_LABEL.get(src,"generated")
        for r in rows:
            rec=dict(category=r.get("category","?"), kind=r.get("kind","?"), scale=r.get("scale",""),
                     entity=r.get("entity",""), question=r.get("question",""),
                     reasoning=r.get("reasoning",""), answer=r.get("answer",""),
                     context=r.get("context") or r.get("fact",""),
                     source=label,
                     prov=json.dumps(r.get("provenance",{}))[:160])
            DATA.append(rec)
    random.shuffle(DATA)
    for r in DATA:
        for f in ("category","kind","source"): FACETS[f][r[f]]=FACETS[f].get(r[f],0)+1
    print(f"loaded {len(DATA):,} records")

def search(qs):
    cat=qs.get("category",[""])[0]; kind=qs.get("kind",[""])[0]; src=qs.get("source",[""])[0]
    q=qs.get("search",[""])[0].lower(); page=int(qs.get("page",["1"])[0]); size=int(qs.get("size",["20"])[0])
    res=[r for r in DATA
         if (not cat or r["category"]==cat) and (not kind or r["kind"]==kind)
         and (not src or r["source"]==src)
         and (not q or q in r["question"].lower() or q in r["answer"].lower() or q in r["entity"].lower() or q in r["reasoning"].lower())]
    return {"total":len(res), "page":page, "items":res[(page-1)*size:page*size]}

HTML = """<!doctype html><html><head><meta charset=utf-8><title>Plexis-Mind · Training-Set Explorer</title>
<meta name=viewport content="width=device-width,initial-scale=1"><style>
:root{--bg:#0b1220;--card:#141d2e;--b:#243049;--t1:#e6e9ef;--t2:#94a3b8;--acc:#fca311;--green:#2a9d8f;--blue:#5aa9e6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--t1);font:14px/1.5 ui-sans-serif,system-ui}
header{padding:18px 24px;border-bottom:1px solid var(--b);position:sticky;top:0;background:var(--bg);z-index:5}
h1{margin:0;font-size:20px}h1 span{color:var(--acc)}.sub{color:var(--t2);font-size:12px;margin-top:3px}
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
select,input{background:var(--card);color:var(--t1);border:1px solid var(--b);border-radius:8px;padding:8px 10px;font-size:13px}
input[type=text]{flex:1;min-width:220px}button{background:var(--acc);color:#1a1206;border:0;border-radius:8px;padding:8px 14px;font-weight:600;cursor:pointer}
button.ghost{background:var(--card);color:var(--t1);border:1px solid var(--b)}
.wrap{max-width:980px;margin:0 auto;padding:18px}
.stat{color:var(--t2);font-size:12px;margin:4px 0 14px}
.card{background:var(--card);border:1px solid var(--b);border-radius:12px;padding:16px;margin-bottom:12px}
.badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.tag{font-size:11px;padding:2px 8px;border-radius:20px;background:#1b2740;color:var(--t2)}
.tag.cat{background:#1f3b34;color:#8fe;}.tag.deep{background:#3a2a12;color:var(--acc)}
.q{font-weight:600;font-size:15px;margin:2px 0 8px}
.r{color:var(--t2);font-size:13px;white-space:pre-wrap;border-left:2px solid var(--b);padding-left:10px;margin:8px 0}
.a{color:var(--green);font-weight:600}.ctx{color:#6b7a99;font-size:12px;font-style:italic;margin-top:8px}
.prov{color:#475569;font-size:11px;margin-top:6px;font-family:ui-monospace,monospace}
.pg{display:flex;gap:8px;justify-content:center;align-items:center;margin:18px 0;color:var(--t2)}
details summary{cursor:pointer;color:var(--blue);font-size:12px}
</style></head><body>
<header><div class=wrap style=padding:0>
<h1>🧠 Plexis-Mind <span>· Training-Set Explorer</span></h1>
<div class=sub id=meta>loading…</div>
<div class=controls>
<select id=category onchange=go(1)></select>
<select id=kind onchange=go(1)></select>
<select id=source onchange=go(1)></select>
<input id=search type=text placeholder="search questions, answers, areas…" onkeydown="if(event.key=='Enter')go(1)">
<button onclick=go(1)>Search</button>
<button class=ghost onclick=surprise()>🎲 Surprise me</button>
</div></div></header>
<div class=wrap><div class=stat id=stat></div><div id=list></div>
<div class=pg><button class=ghost onclick=go(P-1)>‹ prev</button><span id=pageinfo></span><button class=ghost onclick=go(P+1)>next ›</button></div>
</div>
<script>
let P=1, TOTAL=0;
function opt(sel,obj,label){let e=document.getElementById(sel);let ks=Object.entries(obj).sort((a,b)=>b[1]-a[1]);
 e.innerHTML=`<option value="">${label} (all)</option>`+ks.map(([k,v])=>`<option value="${k}">${k} · ${v.toLocaleString()}</option>`).join('')}
async function meta(){let m=await (await fetch('/api/meta')).json();TOTAL=m.total;
 document.getElementById('meta').textContent=`${m.total.toLocaleString()} examples · deterministic answers · ${Object.keys(m.kind).length} question types · browse & debate`;
 opt('category',m.category,'category');opt('kind',m.kind,'kind');opt('source',m.source,'source');go(1)}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function go(p){if(p<1)p=1;P=p;let q=new URLSearchParams({category:category.value,kind:kind.value,source:source.value,search:search.value,page:p,size:20});
 let d=await (await fetch('/api/q?'+q)).json();
 document.getElementById('stat').textContent=`${d.total.toLocaleString()} matching`;
 document.getElementById('pageinfo').textContent=`page ${p} / ${Math.max(1,Math.ceil(d.total/20))}`;
 document.getElementById('list').innerHTML=d.items.map(card).join('')||'<div class=stat>no matches</div>';window.scrollTo(0,0)}
function card(r){let deep=r.source.includes('distilled');
 return `<div class=card><div class=badges>
 <span class="tag cat">${esc(r.category)}</span><span class=tag>${esc(r.kind)}</span>
 ${r.entity?`<span class=tag>📍 ${esc(r.entity)}</span>`:''}${deep?'<span class="tag deep">⚡ deep reasoning</span>':''}</div>
 <div class=q>${esc(r.question)}</div>
 ${r.reasoning?`<details ${deep?'open':''}><summary>reasoning</summary><div class=r>${esc(r.reasoning)}</div></details>`:''}
 <div class=a>→ ${esc(r.answer)}</div>
 ${r.context?`<div class=ctx>context: ${esc(r.context).slice(0,260)}</div>`:''}
 <div class=prov>${esc(r.prov)}</div></div>`}
async function surprise(){category.value='';kind.value='';source.value='';search.value='';
 let d=await (await fetch('/api/q?size=1&page='+(1+Math.floor(Math.random()*5000)))).json();
 if(d.items.length){document.getElementById('list').innerHTML=card(d.items[0]);document.getElementById('stat').textContent='random pick — hit 🎲 again';window.scrollTo(0,0)}}
meta()
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def _send(self,body,ct="application/json"):
        b=body if isinstance(body,bytes) else body.encode()
        self.send_response(200);self.send_header("Content-Type",ct);self.send_header("Access-Control-Allow-Origin","*");self.end_headers();self.wfile.write(b)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=="/": return self._send(HTML,"text/html")
        if u.path=="/api/meta": return self._send(json.dumps({"total":len(DATA),**FACETS}))
        if u.path=="/api/q": return self._send(json.dumps(search(parse_qs(u.query))))
        self._send("{}",404)
    def log_message(self,*a): pass

if __name__=="__main__":
    load()
    print(f"explorer on :{PORT}")
    HTTPServer(("0.0.0.0",PORT),H).serve_forever()

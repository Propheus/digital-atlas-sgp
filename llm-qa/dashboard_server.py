#!/usr/bin/env python3
"""Plexis-Mind SFT live dashboard — self-contained web page on an exposed port.
   python3 dashboard_server.py [PORT]   (default 7780)   -> RunPod proxy: https://<POD>-7780.proxy.runpod.net
"""
import re, io, os, sys, base64, subprocess, html
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG="/root/full.log"; TOTAL=15804; PORT=int(sys.argv[1]) if len(sys.argv)>1 else 7780

def parse():
    t=open(LOG,errors="ignore").read().replace("\r","\n") if os.path.exists(LOG) else ""
    losses=[float(x) for x in re.findall(r"'loss':\s*([\d.]+)",t)]
    evals=[float(x) for x in re.findall(r"'eval_loss':\s*([\d.]+)",t)]
    st=re.findall(r"(\d+)/%d \[([\d:]+)<([\d:]+),\s*([\d.]+)s/it"%TOTAL,t)
    cur,el,eta,sit=(int(st[-1][0]),st[-1][1],st[-1][2],st[-1][3]) if st else (0,"-","-","?")
    done="FULL_EXIT_0" in t; err=("Traceback" in t and not done)
    tail="\n".join(l for l in t.split("\n") if l.strip() and "Loading weights" not in l and "Map:" not in l)[-1200:]
    return losses,evals,cur,el,eta,sit,done,err,tail[-1200:]

def gpu():
    try: return subprocess.check_output(["nvidia-smi","--query-gpu=memory.used,memory.total,utilization.gpu","--format=csv,noheader"],text=True).strip()
    except: return "n/a"

def plot(losses,evals):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except: return ""
    if not losses and not evals: return ""
    fig=plt.figure(figsize=(8,3.2))
    if losses: plt.plot([(i+1)*20 for i in range(len(losses))],losses,lw=1,color="#2a9d8f",label="train")
    if evals:  plt.plot([(i+1)*500 for i in range(len(evals))],evals,"o-",color="#e76f51",label="eval")
    plt.xlabel("step");plt.ylabel("loss");plt.grid(alpha=.25);plt.legend();plt.tight_layout()
    b=io.BytesIO();plt.savefig(b,format="png",dpi=85);plt.close(fig)
    return "data:image/png;base64,"+base64.b64encode(b.getvalue()).decode()

def page():
    L,E,cur,el,eta,sit,done,err,tail=parse()
    pct=100*cur/TOTAL; img=plot(L,E)
    badge=("#e76f51","ERROR") if err else (("#2a9d8f","DONE ✓") if done else ("#457b9d","training…"))
    lossrow=f"{L[0]:.3f} → <b>{L[-1]:.3f}</b>" if L else "waiting for first log…"
    evalrow=f"{E[0]:.3f} → <b>{E[-1]:.3f}</b> ({len(E)})" if E else "—"
    return f"""<!doctype html><html><head><meta charset=utf-8><meta http-equiv=refresh content=15>
<title>Plexis-Mind SFT</title><style>
body{{background:#0d1b2a;color:#e0e1dd;font-family:ui-monospace,monospace;margin:0;padding:28px}}
.card{{max-width:860px;margin:auto}}h1{{font-size:20px;color:#fca311}}
.bar{{height:22px;background:#1b263b;border-radius:11px;overflow:hidden;margin:10px 0}}
.fill{{height:100%;background:linear-gradient(90deg,#2a9d8f,#fca311);width:{pct:.1f}%}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px 24px;margin:14px 0}}
.k{{color:#778da9}} .badge{{background:{badge[0]};padding:3px 10px;border-radius:6px;font-size:13px}}
pre{{background:#1b263b;padding:12px;border-radius:8px;font-size:11px;overflow:auto;max-height:220px;color:#a8dadc}}
img{{width:100%;border-radius:8px;background:#fff;margin:10px 0}}</style></head>
<body><div class=card>
<h1>🧠 Plexis-Mind SFT &nbsp;<span class=badge>{badge[1]}</span></h1>
<div>Gemma-4-12B · QLoRA r32 · RTX PRO 4500 (Blackwell)</div>
<div class=bar><div class=fill></div></div>
<div class=grid>
<div><span class=k>step</span> {cur:,} / {TOTAL:,} ({pct:.1f}%)</div><div><span class=k>speed</span> {sit}s/it</div>
<div><span class=k>elapsed</span> {el}</div><div><span class=k>ETA</span> {eta}</div>
<div><span class=k>train loss</span> {lossrow}</div><div><span class=k>eval loss</span> {evalrow}</div>
<div style=grid-column:1/3><span class=k>GPU</span> {gpu()}</div>
</div>
{('<img src="'+img+'">') if img else ''}
<div class=k>recent log</div><pre>{html.escape(tail)}</pre>
<div style=color:#778da9;font-size:11px>auto-refresh 15s</div>
</div></body></html>"""

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        try: body=page().encode()
        except Exception as e: body=f"<pre>{e}</pre>".encode()
        self.send_response(200);self.send_header("Content-Type","text/html");self.end_headers();self.wfile.write(body)
    def log_message(self,*a): pass

if __name__=="__main__":
    print(f"dashboard on :{PORT}")
    HTTPServer(("0.0.0.0",PORT),H).serve_forever()

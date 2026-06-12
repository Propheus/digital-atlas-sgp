#!/usr/bin/env python3
"""
Plexis-Mind SFT — live training dashboard. Parses /root/full.log.
  python3 monitor.py            # one snapshot
  python3 monitor.py --watch    # refresh every 30s
  python3 monitor.py --plot     # also write /root/loss_curve.png (view in Jupyter)
"""
import re, sys, time, os, subprocess

LOG = os.environ.get("LOG", "/root/full.log")
TOTAL = 15804

def parse():
    txt = open(LOG, errors="ignore").read().replace("\r", "\n")
    losses = [float(x) for x in re.findall(r"'loss': ([\d.]+)", txt)]
    evals  = [float(x) for x in re.findall(r"'eval_loss': ([\d.]+)", txt)]
    steps  = re.findall(r"(\d+)/%d \[([\d:]+)<([\d:]+)," % TOTAL, txt)
    cur, elapsed, eta = (int(steps[-1][0]), steps[-1][1], steps[-1][2]) if steps else (0,"-","-")
    sit = re.findall(r"([\d.]+)s/it", txt)
    return losses, evals, cur, elapsed, eta, (sit[-1] if sit else "?")

def gpu():
    try:
        return subprocess.check_output(["nvidia-smi","--query-gpu=memory.used,utilization.gpu","--format=csv,noheader"],text=True).strip()
    except: return "n/a"

def snapshot():
    losses, evals, cur, elapsed, eta, sit = parse()
    pct = 100*cur/TOTAL
    bar = "█"*int(pct/2.5) + "░"*(40-int(pct/2.5))
    print("\033[2J\033[H" if "--watch" in sys.argv else "")
    print("="*58)
    print(f"  PLEXIS-MIND SFT  ·  Gemma-4-12B QLoRA  ·  RTX PRO 4500")
    print("="*58)
    print(f"  step {cur:,}/{TOTAL:,}   {pct:4.1f}%   {sit}s/it")
    print(f"  [{bar}]")
    print(f"  elapsed {elapsed}   ETA {eta}")
    print(f"  GPU: {gpu()}")
    if losses:
        recent = losses[-6:]
        print(f"  train loss: {losses[0]:.3f} → {losses[-1]:.3f}   (last: {', '.join(f'{l:.3f}' for l in recent)})")
    if evals:
        print(f"  eval  loss: {evals[0]:.3f} → {evals[-1]:.3f}   ({len(evals)} evals)")
    done = "DONE ✓" if "FULL_EXIT_0" in open(LOG,errors='ignore').read() else "running…"
    print(f"  status: {done}")
    print("="*58)

def plot():
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except: print("(matplotlib not installed: pip install matplotlib)"); return
    losses, evals, *_ = parse()
    plt.figure(figsize=(9,4))
    if losses: plt.plot([ (i+1)*20 for i in range(len(losses))], losses, label="train loss", lw=1)
    if evals:  plt.plot([ (i+1)*500 for i in range(len(evals))], evals, "o-", label="eval loss")
    plt.xlabel("step"); plt.ylabel("loss"); plt.legend(); plt.grid(alpha=.3); plt.title("Plexis-Mind SFT")
    plt.tight_layout(); plt.savefig("/root/loss_curve.png", dpi=90)
    print("wrote /root/loss_curve.png")

if __name__ == "__main__":
    if "--watch" in sys.argv:
        while True:
            snapshot()
            if "--plot" in sys.argv: plot()
            time.sleep(30)
    else:
        snapshot()
        if "--plot" in sys.argv: plot()

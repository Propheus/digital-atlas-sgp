"""
Plexis-P1 — the full program, start small -> go big (run in screen on server).

Stage V0  : random 50K subset, 3 seeds, exam        (fast loop)
Stage FULL: all 190,591, 3 seeds, exam              (only if V0 sane)
Ship      : places/place_embedding_plexis_p1_64d.parquet from FULL seed 0
            (only if FULL exam VERDICT true)

Every stage appends to runs.jsonl.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent
PY = sys.executable


def sh(cmd):
    print("+", " ".join(cmd), flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=OUT, capture_output=True, text=True)
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit(f"FAILED: {cmd}")
    return time.time() - t0


def log(rec):
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(OUT / "runs.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")


def exam_verdict(stem):
    j = json.load(open(OUT / f"exam_{stem}.json"))
    return j["VERDICT"], j


def main():
    n = np.load(OUT / "X_A.npy", mmap_mode="r").shape[0]

    # ---- V0: 50K subset ----
    rng = np.random.default_rng(7)
    sub = np.sort(rng.choice(n, 50000, replace=False))
    np.save(OUT / "subset_v0.npy", sub)
    for s in range(3):
        dt = sh([PY, "train.py", "--seed", str(s), "--epochs", "30",
                 "--subset", "subset_v0.npy", "--out", f"Z_v0_s{s}.npy"])
        log({"stage": "v0", "seed": s, "secs": round(dt)})
    sh([PY, "exam.py", "Z_v0_s0.npy", "Z_v0_s1.npy", "Z_v0_s2.npy",
        "--subset", "subset_v0.npy"])
    v, j = exam_verdict("Z_v0_s0")
    log({"stage": "v0_exam", "verdict": v,
         "scores": {k: vv for k, vv in j.items() if k != "9_archetypes"}})
    print(f"\n=== V0 VERDICT: {v} ===\n", flush=True)

    # ---- FULL ----
    for s in range(3):
        dt = sh([PY, "train.py", "--seed", str(s), "--epochs", "20",
                 "--out", f"Z_p1_s{s}.npy"])
        log({"stage": "full", "seed": s, "secs": round(dt)})
    sh([PY, "exam.py", "Z_p1_s0.npy", "Z_p1_s1.npy", "Z_p1_s2.npy"])
    v, j = exam_verdict("Z_p1_s0")
    log({"stage": "full_exam", "verdict": v})
    print(f"\n=== FULL VERDICT: {v} ===\n", flush=True)

    if v:
        import pandas as pd
        ids = pd.read_parquet(OUT / "ids.parquet")
        Z = np.load(OUT / "Z_p1_s0.npy")
        df = pd.DataFrame(Z, columns=[f"d{i}" for i in range(Z.shape[1])])
        df.insert(0, "id", ids["id"].to_numpy())
        dest = OUT.parent / "places/place_embedding_plexis_p1_64d.parquet"
        df.to_parquet(dest, index=False)
        log({"stage": "ship", "path": str(dest), "shape": list(df.shape)})
        print("SHIPPED", dest, flush=True)
    else:
        print("FULL exam failed — NOT shipped (see failure ladder in design)",
              flush=True)


if __name__ == "__main__":
    main()

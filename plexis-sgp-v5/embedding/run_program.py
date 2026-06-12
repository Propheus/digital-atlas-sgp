"""
Plexis-E v1 — the full staged program, designed to run inside one screen.

  prep -> E0 (PCA-256 + full harness)
       -> E1 screening (small: 300 epochs, 8 configs)
       -> E1 finals (big: 1200 epochs, best config x 3 seeds, Procrustes)
       -> E2 (view-masking heads on best E1 config, screen + finals)
       -> winner selection vs PCA, final full-harness report

Progress -> program.log; every training eval -> runs.jsonl. Idempotent-ish:
artifacts written as they complete.
"""
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
LOG = open(HERE / "program.log", "a")


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.write(line + "\n"); LOG.flush()


def run(cmd):
    log("RUN " + " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=HERE)


def score(ev):
    """One number to rank configs: probes + twins + zone ARI."""
    return (ev.get("probe_hdb_psm_r2", 0) + ev.get("probe_od_r2", 0)
            + ev.get("probe_adq_r2", 0)) / 3 \
        + 0.5 * ev.get("twin_hitrate", 0) + 0.25 * ev.get("zone_ari", 0)


def last_eval(tag, seed=None):
    best = None
    for line in open(HERE / "runs.jsonl"):
        r = json.loads(line)
        if r["tag"] == tag and (seed is None or r["seed"] == seed):
            best = r
    return best


def main():
    log("=== Plexis-E v1 program start ===")
    run([sys.executable, "prep_features.py"])

    # ---- E0: PCA-256 ----
    from sklearn.decomposition import PCA
    from eval_harness import evaluate, procrustes_corr
    X = np.load(HERE / "X.npy")
    Zp = PCA(n_components=256, random_state=0).fit_transform(X)
    np.save(HERE / "Z_pca256.npy", Zp)
    e0 = evaluate(Zp, fast=False, X_raw=X)
    json.dump(e0, open(HERE / "eval_e0_pca.json", "w"), indent=1)
    log(f"E0 PCA: score={score(e0):.4f} {json.dumps({k: round(v,3) for k, v in e0.items() if isinstance(v, float)})}")

    # ---- E1 screening (small) ----
    grid = list(itertools.product([0.2, 0.3, 0.4], [0.1, 0.5]))  # mask x tau
    for i, (mask, tau) in enumerate(grid):
        run([sys.executable, "train.py", "--epochs", "300", "--mask", str(mask),
             "--tau", str(tau), "--eval-every", "150",
             "--tag", f"e1s_m{mask}_t{tau}"])
    cands = [(score(last_eval(f"e1s_m{m}_t{t}")), m, t) for m, t in grid]
    cands.sort(reverse=True)
    log(f"E1 screen ranking: {[(round(s,4), m, t) for s, m, t in cands[:4]]}")
    _, bm, bt = cands[0]

    # ---- E1 finals (big, 3 seeds) ----
    for seed in (0, 1, 2):
        run([sys.executable, "train.py", "--epochs", "1200", "--mask", str(bm),
             "--tau", str(bt), "--seed", str(seed), "--eval-every", "200",
             "--tag", "e1_final", "--out", f"Z_e1_s{seed}.npy"])
    Zs = [np.load(HERE / f"Z_e1_s{s}.npy") for s in (0, 1, 2)]
    pc = [procrustes_corr(Zs[0], Zs[1]), procrustes_corr(Zs[0], Zs[2]),
          procrustes_corr(Zs[1], Zs[2])]
    e1 = evaluate(Zs[0], fast=False, X_raw=X)
    e1["procrustes_min"] = min(pc)
    json.dump(e1, open(HERE / "eval_e1.json", "w"), indent=1)
    log(f"E1 final: score={score(e1):.4f} procrustes_min={min(pc):.3f}")

    # ---- E2: + view masking (small screen then finals) ----
    for vp in (0.3, 0.5):
        run([sys.executable, "train.py", "--epochs", "300", "--mask", str(bm),
             "--tau", str(bt), "--view-mask-prob", str(vp),
             "--eval-every", "150", "--tag", f"e2s_v{vp}"])
    v_best = max((0.3, 0.5), key=lambda v: score(last_eval(f"e2s_v{v}")))
    for seed in (0, 1, 2):
        run([sys.executable, "train.py", "--epochs", "1200", "--mask", str(bm),
             "--tau", str(bt), "--view-mask-prob", str(v_best),
             "--seed", str(seed), "--eval-every", "200",
             "--tag", "e2_final", "--out", f"Z_e2_s{seed}.npy"])
    Zs2 = [np.load(HERE / f"Z_e2_s{s}.npy") for s in (0, 1, 2)]
    pc2 = [procrustes_corr(Zs2[0], Zs2[1]), procrustes_corr(Zs2[0], Zs2[2]),
           procrustes_corr(Zs2[1], Zs2[2])]
    e2 = evaluate(Zs2[0], fast=False, X_raw=X)
    e2["procrustes_min"] = min(pc2)
    json.dump(e2, open(HERE / "eval_e2.json", "w"), indent=1)
    log(f"E2 final: score={score(e2):.4f} procrustes_min={min(pc2):.3f}")

    # ---- winner ----
    board = {"E0_pca": score(e0), "E1": score(e1), "E2": score(e2)}
    winner = max(board, key=board.get)
    # stability veto: neural must be stable to win
    if winner != "E0_pca" and (e1 if winner == "E1" else e2)["procrustes_min"] < 0.9:
        log(f"stability veto on {winner} -> falling back to next stable")
        winner = "E0_pca"
    summary = {"board": board, "winner": winner,
               "e1_cfg": {"mask": bm, "tau": bt},
               "e2_view_mask": v_best,
               "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump(summary, open(HERE / "program_summary.json", "w"), indent=1)
    log(f"=== DONE. board={board} winner={winner} ===")


if __name__ == "__main__":
    main()

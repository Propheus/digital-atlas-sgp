"""
Plexis-P1 — two-tower contrastive training (PLACE_EMBEDDING_DESIGN.md).

  tower A (essence+micrograph) -> 64d   <- THE embedding
  tower B (context)            -> 64d   <- discarded after training

Losses (InfoNCE, tau=0.5):
  scarf  1.0  — corrupt A-inputs (mask 0.3, in-batch column resample)
  chain  0.5  — same-brand outlet pairs (denylisted, capped pool from prep)
  cross  0.5  — zA(x) must agree with zB(context(x))
Hard negatives come free from batch construction: half of every batch is
same-category groups, so in-batch negatives include same-cat places.

python3 train.py --seed 0 --epochs 30 [--subset subset_idx.npy] --out Z_p1_s0.npy
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

OUT = Path(__file__).parent
TAU = 0.5
MASK = 0.3


def mlp(d_in, d_out=64):
    return nn.Sequential(nn.Linear(d_in, 256), nn.ReLU(),
                         nn.Linear(256, 256), nn.ReLU(),
                         nn.Linear(256, d_out))


def info_nce(za, zb):
    za, zb = F.normalize(za, dim=1), F.normalize(zb, dim=1)
    logits = za @ zb.T / TAU
    t = torch.arange(len(za), device=za.device)
    return 0.5 * (F.cross_entropy(logits, t) + F.cross_entropy(logits.T, t))


def scarf_corrupt(x, g):
    m = (torch.rand(x.shape, generator=g) < MASK)
    perm = torch.randperm(len(x), generator=g)
    return torch.where(m, x[perm], x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--subset", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    g = torch.Generator().manual_seed(args.seed)
    torch.set_num_threads(max(1, (torch.get_num_threads() or 8)))

    XA = torch.from_numpy(np.load(OUT / "X_A.npy"))
    XB = torch.from_numpy(np.load(OUT / "X_B.npy"))
    cp = np.load(OUT / "chain_pairs.npz")
    pairs = cp["pairs"]
    ids = __import__("pandas").read_parquet(OUT / "ids.parquet").reset_index(drop=True)
    cats = ids["plexis_category"].astype("category").cat.codes.to_numpy()

    if args.subset:
        sub = np.load(args.subset)
        pos = {int(s): i for i, s in enumerate(sub)}
        XA, XB, cats = XA[sub], XB[sub], cats[sub]
        pairs = np.array([(pos[i], pos[j]) for i, j in pairs
                          if i in pos and j in pos], dtype=np.int64)
    n = len(XA)
    cat_rows = {c: np.where(cats == c)[0] for c in np.unique(cats)}
    cat_pool = [c for c, r in cat_rows.items() if len(r) >= 8]
    print(f"train n={n}, dA={XA.shape[1]}, dB={XB.shape[1]}, chain_pairs={len(pairs)}")

    tA, tB = mlp(XA.shape[1]), mlp(XB.shape[1])
    opt = torch.optim.Adam(list(tA.parameters()) + list(tB.parameters()),
                           lr=1e-3, weight_decay=1e-5)
    rng = np.random.default_rng(args.seed)
    B = 1024
    steps = max(1, n // B)
    t0 = time.time()
    for ep in range(args.epochs):
        tot = 0.0
        for _ in range(steps):
            # hard-negative batch: half random, half same-category quads
            r1 = rng.choice(n, B // 2, replace=False)
            quads = [rng.choice(cat_rows[c], 4, replace=len(cat_rows[c]) < 4)
                     for c in rng.choice(cat_pool, B // 8)]
            idx = torch.from_numpy(np.concatenate([r1, *quads])[:B])

            xa = XA[idx]
            za = tA(xa)
            l_scarf = info_nce(za, tA(scarf_corrupt(xa, g)))
            l_cross = info_nce(za, tB(XB[idx]))
            pr = pairs[rng.choice(len(pairs), 256)]
            l_chain = info_nce(tA(XA[pr[:, 0]]), tA(XA[pr[:, 1]]))
            loss = 1.0 * l_scarf + 0.5 * l_chain + 0.5 * l_cross
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss)
        print(f"epoch {ep + 1}/{args.epochs} loss {tot / steps:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)

    with torch.no_grad():
        Z = torch.cat([F.normalize(tA(XA[s:s + 8192]), dim=1)
                       for s in range(0, n, 8192)]).numpy().astype(np.float32)
    np.save(OUT / args.out, Z)
    torch.save({"tA": tA.state_dict(), "tB": tB.state_dict(),
                "args": vars(args)}, OUT / (args.out + ".pt"))
    print(f"saved {args.out} {Z.shape} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

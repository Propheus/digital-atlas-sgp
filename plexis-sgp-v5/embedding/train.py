"""
Plexis-E v1 — masked-contrastive encoder (E1) + optional view-masking heads (E2).

SCARF-style: corrupt a random feature subset by resampling from the column's
marginal; positive pair = (clean, corrupted) encodings; InfoNCE in-batch
negatives; + denoising reconstruction; + (E2) whole-VIEW masking so the encoder
must predict a missing view from the others (the supply<->demand objective).

Frequent eval: quick harness every EVAL_EVERY epochs -> appended to runs.jsonl.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

HERE = Path(__file__).parent
torch.set_num_threads(8)


class Encoder(nn.Module):
    def __init__(self, d, dim=256, hidden=512, pdrop=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d, hidden), nn.LayerNorm(hidden), nn.GELU(),
            nn.Dropout(pdrop),
            nn.Linear(hidden, dim))
        self.proj = nn.Sequential(nn.Linear(dim, 128))
        self.dec = nn.Sequential(nn.Linear(dim, hidden), nn.GELU(),
                                 nn.Linear(hidden, d))

    def forward(self, x):
        z = self.net(x)
        return z, F.normalize(self.proj(z), dim=-1), self.dec(z)


def info_nce(p1, p2, tau):
    logits = p1 @ p2.T / tau
    labels = torch.arange(len(p1))
    return 0.5 * (F.cross_entropy(logits, labels)
                  + F.cross_entropy(logits.T, labels))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=1000)
    ap.add_argument("--mask", type=float, default=0.3)
    ap.add_argument("--tau", type=float, default=0.5)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--lam-recon", type=float, default=1.0)
    ap.add_argument("--view-mask-prob", type=float, default=0.0)  # E2 if > 0
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--eval-every", type=int, default=100)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    X = np.load(HERE / "X.npy")
    meta = json.load(open(HERE / "meta.json"))
    n, d = X.shape
    Xt = torch.tensor(X)

    # view index groups for E2 view-masking
    views = meta["views"]
    vgroups = {}
    for i, c in enumerate(meta["cols"]):
        vgroups.setdefault(views[c], []).append(i)
    maskable_views = [v for v in ("WHO", "WHAT", "FLOW", "PRICE", "WHERE")
                      if v in vgroups]

    model = Encoder(d)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)

    from eval_harness import evaluate
    runs = open(HERE / "runs.jsonl", "a")
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        perm = torch.randperm(n)
        tot = 0.0
        for s in range(0, n, args.batch):
            idx = perm[s:s + args.batch]
            x = Xt[idx]
            # SCARF corruption: resample masked entries from marginals
            m = torch.tensor(rng.random((len(idx), d)) < args.mask)
            donor = Xt[torch.randint(0, n, (len(idx),))]
            xc = torch.where(m, donor, x)
            # E2: with prob, additionally blank an entire view
            if args.view_mask_prob > 0 and rng.random() < args.view_mask_prob:
                v = maskable_views[rng.integers(len(maskable_views))]
                xc[:, vgroups[v]] = 0.0
                m[:, vgroups[v]] = True
            _, p1, _ = model(x)
            z2, p2, rec = model(xc)
            loss = info_nce(p1, p2, args.tau)
            if args.lam_recon > 0:
                loss = loss + args.lam_recon * F.mse_loss(rec[m], x[m])
            opt.zero_grad(); loss.backward(); opt.step()
            tot += float(loss) * len(idx)
        sched.step()

        if (ep + 1) % args.eval_every == 0 or ep == args.epochs - 1:
            model.eval()
            with torch.no_grad():
                Z = model(Xt)[0].numpy()
            ev = evaluate(Z, fast=True)
            rec_line = {"tag": args.tag, "seed": args.seed, "epoch": ep + 1,
                        "loss": round(tot / n, 4),
                        "cfg": {k: getattr(args, k) for k in
                                ("mask", "tau", "lr", "lam_recon",
                                 "view_mask_prob")},
                        **{k: (round(v, 4) if isinstance(v, float) else v)
                           for k, v in ev.items()},
                        "elapsed_s": round(time.time() - t0, 1)}
            runs.write(json.dumps(rec_line) + "\n"); runs.flush()
            print(json.dumps(rec_line))

    if args.out:
        model.eval()
        with torch.no_grad():
            Z = model(Xt)[0].numpy()
        np.save(HERE / args.out, Z)
        torch.save(model.state_dict(), HERE / (args.out + ".pt"))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Contrastive training toy demo — 5 hexes × 5 features.

Reproduces CONTRASTIVE_TRAINING_DEMO.md. Run:
    python3 scripts/contrastive_toy_demo.py
"""
from __future__ import annotations

import numpy as np

np.set_printoptions(precision=3, suppress=True)

HEX_NAMES = ["Toa Payoh", "Ang Mo Kio", "CBD Core", "Tuas Ind.", "Punggol"]
FEAT_NAMES = ["pop_res", "comm_int", "near_mrt", "cafe_press", "dt_ratio"]
X = np.array([
    [8000, 0.55, 1, 12, 0.90],
    [7500, 0.52, 1, 11, 0.85],
    [2000, 0.95, 1, 45, 2.50],
    [500, 0.15, 0, 2, 0.60],
    [9000, 0.45, 1, 8, 1.10],
], dtype=float)
N, D = X.shape
EMB_DIM = 2


def encode(x: np.ndarray, W: np.ndarray) -> np.ndarray:
    z = x @ W
    return z / (np.linalg.norm(z) + 1e-8)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b)


def mask_view(x: np.ndarray, mask_frac: float, rng: np.random.Generator):
    v = x.copy()
    n_mask = max(1, int(D * mask_frac))
    idx = rng.choice(D, size=n_mask, replace=False)
    v[idx] = 0.0
    return v, idx


def info_nce_loss(anchor_z, pos_z, neg_zs, tau=0.1):
    sim_pos = cosine_sim(anchor_z, pos_z) / tau
    sim_negs = np.array([cosine_sim(anchor_z, nz) / tau for nz in neg_zs])
    logits = np.concatenate([[sim_pos], sim_negs])
    logits -= logits.max()
    exp_l = np.exp(logits)
    loss = -np.log(exp_l[0] / exp_l.sum())
    return loss, sim_pos * tau, sim_negs * tau


def distance_matrix(Z, names):
    print("\n  Cosine similarity matrix (1=identical, -1=opposite):")
    print(f"  {'':14}", end="")
    for n in names:
        print(f"{n[:8]:>9}", end="")
    print()
    for i, ni in enumerate(names):
        print(f"  {ni:14}", end="")
        for j in range(len(names)):
            print(f"{cosine_sim(Z[i], Z[j]):9.3f}", end="")
        print()


def main():
    mu, sigma = X.mean(0), X.std(0) + 1e-8
    Xn = (X - mu) / sigma

    rng = np.random.default_rng(42)
    W = rng.normal(0, 0.3, size=(D, EMB_DIM))

    print("=" * 72)
    print("STEP 0 — Random encoder (untrained)")
    print("=" * 72)
    Z0 = np.array([encode(Xn[i], W) for i in range(N)])
    for i, name in enumerate(HEX_NAMES):
        print(f"  {name:14} z = [{Z0[i,0]:+.3f}, {Z0[i,1]:+.3f}]")
    distance_matrix(Z0, HEX_NAMES)

    print("\n" + "=" * 72)
    print("STEP 1 — One contrastive training step (anchor = Toa Payoh)")
    print("=" * 72)

    anchor_i = 0
    rng_step = np.random.default_rng(7)
    view1, masked1 = mask_view(Xn[anchor_i], 0.4, rng_step)
    view2, masked2 = mask_view(Xn[anchor_i], 0.4, rng_step)

    print(f"\n  View A — masked: {[FEAT_NAMES[k] for k in masked1]}")
    print(f"  View B — masked: {[FEAT_NAMES[k] for k in masked2]}")

    za = encode(view1, W)
    zp = encode(view2, W)
    neg_zs = [encode(Xn[i], W) for i in range(N) if i != anchor_i]
    loss, sim_pos, sim_negs = info_nce_loss(za, zp, neg_zs, tau=0.1)

    print(f"\n  Positive sim (TPY A ↔ TPY B): {sim_pos:+.3f}")
    for name, s in zip([n for j, n in enumerate(HEX_NAMES) if j != anchor_i], sim_negs):
        print(f"  Negative sim (TPY A ↔ {name:12}): {s:+.3f}")
    print(f"\n  InfoNCE loss = {loss:.3f}")

    lr, tau, eps = 0.5, 0.1, 1e-4
    grad_W = np.zeros_like(W)
    for di in range(D):
        for dj in range(EMB_DIM):
            W_plus = W.copy()
            W_plus[di, dj] += eps
            za_p = encode(view1, W_plus)
            zp_p = encode(view2, W_plus)
            neg_p = [encode(Xn[i], W_plus) for i in range(N) if i != anchor_i]
            l_p, _, _ = info_nce_loss(za_p, zp_p, neg_p, tau)
            grad_W[di, dj] = (l_p - loss) / eps
    W_new = W - lr * grad_W

    Za_after = encode(view1, W_new)
    Zp_after = encode(view2, W_new)
    neg_after = [encode(Xn[i], W_new) for i in range(N) if i != anchor_i]
    loss_after, sim_pos_after, sim_negs_after = info_nce_loss(
        Za_after, Zp_after, neg_after, tau
    )
    print(f"\n  After one gradient step:")
    print(f"  Loss: {loss:.3f} → {loss_after:.3f}")
    print(f"  Positive sim: {sim_pos:+.3f} → {sim_pos_after:+.3f}")
    print(f"  Mean negative sim: {sim_negs.mean():+.3f} → {np.mean(sim_negs_after):+.3f}")

    print("\n" + "=" * 72)
    print("STEP 2 — Train 200 steps")
    print("=" * 72)

    W_train = rng.normal(0, 0.3, size=(D, EMB_DIM))
    lr, tau = 0.3, 0.15
    losses = []

    for step in range(200):
        anchor_i = step % N
        v1, _ = mask_view(Xn[anchor_i], 0.4, rng)
        v2, _ = mask_view(Xn[anchor_i], 0.4, rng)
        za = encode(v1, W_train)
        zp = encode(v2, W_train)
        neg_idx = [i for i in range(N) if i != anchor_i]
        neg_zs = [encode(Xn[i], W_train) for i in neg_idx]

        sim_pos = cosine_sim(za, zp) / tau
        sim_negs = np.array([cosine_sim(za, nz) / tau for nz in neg_zs])
        logits = np.concatenate([[sim_pos], sim_negs])
        logits -= logits.max()
        exp_l = np.exp(logits)
        loss = -np.log(exp_l[0] / exp_l.sum())
        losses.append(loss)

        p = exp_l / exp_l.sum()
        grad_sim_pos = (p[0] - 1) / tau
        grad_sim_negs = p[1:] / tau
        gz_a = grad_sim_pos * zp + sum(g * nz for g, nz in zip(grad_sim_negs, neg_zs))
        gz_p = grad_sim_pos * za
        gz_negs = [g * za for g in grad_sim_negs]

        def grad_encode(x, Wm, upstream):
            raw = x @ Wm
            norm = np.linalg.norm(raw) + 1e-8
            unit = raw / norm
            return upstream * np.outer(x, unit - unit * (unit @ upstream))

        grad_W = grad_encode(v1, W_train, gz_a) + grad_encode(v2, W_train, gz_p)
        for i, ni in enumerate(neg_idx):
            grad_W -= grad_encode(Xn[ni], W_train, gz_negs[i])
        W_train -= lr * np.clip(grad_W, -1, 1)

    Z_final = np.array([encode(Xn[i], W_train) for i in range(N)])
    print(f"  Loss: {losses[0]:.3f} → {losses[-1]:.3f} (avg last 20: {np.mean(losses[-20:]):.3f})")
    print("\n  Final 2-d embeddings:")
    for i, name in enumerate(HEX_NAMES):
        print(f"    {name:14} z = [{Z_final[i,0]:+.3f}, {Z_final[i,1]:+.3f}]")
    distance_matrix(Z_final, HEX_NAMES)

    print("\n  Sanity checks:")
    print(f"    TPY ↔ AMK:   {cosine_sim(Z_final[0], Z_final[1]):+.3f}")
    print(f"    TPY ↔ Tuas:  {cosine_sim(Z_final[0], Z_final[3]):+.3f}")
    print(f"    CBD ↔ Tuas:  {cosine_sim(Z_final[2], Z_final[3]):+.3f}")
    print(f"    AMK ↔ Punggol:{cosine_sim(Z_final[1], Z_final[4]):+.3f}")


if __name__ == "__main__":
    main()
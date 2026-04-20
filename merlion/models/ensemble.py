"""
Ensemble strategies — compose outputs from multiple models.

Each takes list of [{"hex_id","score"}, ...] lists and returns a fused list.
"""
from collections import defaultdict


def rank_fusion_rrf(lists: list[list[dict]], k: int = 20, c: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion — score = sum(1/(c+rank)) across all input lists.
    Standard IR ensemble technique. c=60 is Cormack et al default.
    """
    rrf_scores = defaultdict(float)
    for lst in lists:
        for rank, item in enumerate(lst, start=1):
            rrf_scores[item["hex_id"]] += 1.0 / (c + rank)
    out = sorted(rrf_scores.items(), key=lambda x: -x[1])[:k]
    return [{"hex_id": h, "score": float(s)} for h, s in out]


def intersection(lists: list[list[dict]], k: int = 20) -> list[dict]:
    """Keep only hexes present in ALL lists. Score = mean of input scores."""
    if not lists:
        return []
    sets = [set(x["hex_id"] for x in lst) for lst in lists]
    common = set.intersection(*sets)
    # Average score across lists
    scores = defaultdict(list)
    for lst in lists:
        for x in lst:
            if x["hex_id"] in common:
                scores[x["hex_id"]].append(x["score"])
    out = sorted(
        ((h, sum(s) / len(s)) for h, s in scores.items()),
        key=lambda x: -x[1],
    )[:k]
    return [{"hex_id": h, "score": float(s)} for h, s in out]


def union_dedupe(lists: list[list[dict]], k: int = 20) -> list[dict]:
    """Union of all lists, dedupe by hex_id, keep max score."""
    best = {}
    for lst in lists:
        for x in lst:
            h, s = x["hex_id"], x["score"]
            if h not in best or s > best[h]:
                best[h] = s
    out = sorted(best.items(), key=lambda x: -x[1])[:k]
    return [{"hex_id": h, "score": float(s)} for h, s in out]


def filter_chain(candidates: list[dict], filter_fn, k: int = 20) -> list[dict]:
    """Apply filter_fn(hex_id) → bool; keep only matching."""
    return [c for c in candidates if filter_fn(c["hex_id"])][:k]

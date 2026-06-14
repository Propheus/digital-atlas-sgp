"""
Curriculum — generate grounded questions WITH a gold spec the atlas can verify.
Each record: {question, tier, gold} where gold lets verify.py grade the answer
deterministically. Questions are biased toward multi-tool tiers (T2/T3).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import atlas_tools as AT  # noqa: E402

CATS = AT.CATEGORIES
REGIONS = ["CENTRAL REGION", "EAST REGION", "NORTH REGION",
           "NORTH-EAST REGION", "WEST REGION"]
# only categories that actually have the metric column (avoid empty-gold questions)
_C = AT._agg("subzone").columns
GAP_CATS = [c[4:] for c in _C if c.startswith("gap_")]
CAP_CATS = [c[4:] for c in _C if c.startswith("cap_") and "best" not in c and c != "cap_total"]
CATL = {"health_medical": "healthcare", "cafe_coffee": "cafes",
        "supermarket": "supermarkets", "hawker": "hawker food",
        "fitness_recreation": "gyms", "education": "schools/tuition",
        "restaurant": "restaurants", "convenience": "convenience stores",
        "shopping_retail": "retail", "fast_food": "fast food",
        "beauty_personal": "salons"}


def _subz(scale="subzone"):
    df = AT._agg(scale)
    return df[df["pop_resident"] > 3000]["name"].tolist()


# ---- gold helpers (recompute the true answer) ----------------------------- #
def _rank_gold(metric, scope, where, order="desc"):
    r = AT.rank(metric=metric, scope=scope, where=where, order=order, k=1)
    res = r.get("results") or []
    return res[0]["name"] if res else None


def gen_T2_filter_rank(rng):
    """East subzone, pop>X, most underserved for C -> rank gap_C."""
    cat = rng.choice([c for c in GAP_CATS if c in CATL])
    region = rng.choice(REGIONS)
    thr = rng.choice([15000, 20000, 25000])
    q = (f"Which subzone in the {region.title()} with more than {thr:,} residents "
         f"is the most underserved for {CATL[cat]}?")
    gold = _rank_gold(f"gap_{cat}", region, f"pop_resident > {thr}")
    return {"question": q, "tier": "T2", "gold": {"kind": "entity", "answer": gold,
            "must_use": ["filter", "rank", "gap"]}} if gold else None


def gen_T2_capture(rng):
    """Where would a new C win the most demand (in region)? -> rank cap_C."""
    cat = rng.choice([c for c in CAP_CATS if c in CATL])
    region = rng.choice(REGIONS)
    q = (f"If you opened one new {CATL[cat].rstrip('s')} outlet in the "
         f"{region.title()}, which subzone would win the most demand?")
    gold = _rank_gold(f"cap_{cat}", region, None)
    return {"question": q, "tier": "T2", "gold": {"kind": "entity", "answer": gold,
            "must_use": ["rank", "capture"]}} if gold else None


def gen_T1_compare(rng):
    """Compare two subzones on a dimension."""
    a, b = rng.sample(_subz(), 2)
    dim, col = rng.choice([("walkability", "walkability_score"),
                           ("population", "pop_resident"),
                           ("distance to MRT", "dist_mrt_m"),
                           ("time to the CBD", "time_to_cbd_min")])
    better = "less" if col in ("dist_mrt_m", "time_to_cbd_min") else "more"
    la = AT.lookup(a, [col]); lb = AT.lookup(b, [col])
    va = la["values"][col]; vb = lb["values"][col]
    if va is None or vb is None:
        return None
    if col in ("dist_mrt_m", "time_to_cbd_min"):
        winner = a if va < vb else b
    else:
        winner = a if va > vb else b
    q = f"Between {a.title()} and {b.title()}, which has {better} {dim}?"
    return {"question": q, "tier": "T1", "gold": {"kind": "entity", "answer": winner,
            "must_use": ["compare"]}}


def gen_T1_twins(rng):
    """Find twins of a subzone (gold = the set; answer must name >=1)."""
    a = rng.choice(_subz())
    tw = AT.find_twins(a, k=5).get("twins", [])
    names = [t["name"] for t in tw]
    if not names:
        return None
    q = f"Which neighbourhoods are functionally most like {a.title()}?"
    return {"question": q, "tier": "T1", "gold": {"kind": "any_of", "answer": names,
            "must_use": ["find_twins"]}}


def gen_T0_lookup(rng):
    """Single fact about a subzone."""
    a = rng.choice(_subz())
    dim, col = rng.choice([("resident population", "pop_resident"),
                           ("walkability score", "walkability_score"),
                           ("15-minute-city score", "min15_score")])
    v = AT.lookup(a, [col])["values"][col]
    if v is None:
        return None
    q = f"What is the {dim} of {a.title()}?"
    return {"question": q, "tier": "T0", "gold": {"kind": "number", "answer": v,
            "tol": 0.15, "must_use": ["lookup"]}}


def gen_abstain(rng):
    topic, q = rng.choice([
        ("crime", "What is the crime rate in {z}?"),
        ("income", "What is the median household income in {z}?"),
        ("weather", "What will the weather be in {z} tomorrow?"),
        ("future price", "Will resale prices in {z} rise next year?"),
        ("school ranking", "Which is the top-ranked primary school in {z}?")])
    z = rng.choice(_subz()).title()
    return {"question": q.format(z=z), "tier": "abstain",
            "gold": {"kind": "abstain", "must_use": ["can_answer"]}}


def gen_T3_judgment(rng):
    """Open judgment — no gold answer; graded on evidence-gathering."""
    a = rng.choice(_subz())
    q = rng.choice([
        f"Is {a.title()} becoming a job centre or still a dormitory town? What's the evidence?",
        f"Make the case for or against opening a cafe in {a.title()}.",
        f"What's the emerging story in {a.title()} — who lives there and what's missing?"])
    return {"question": q, "tier": "T3",
            "gold": {"kind": "judgment", "must_use_any": ["od_flow", "lookup", "gap",
                     "capture", "find_twins", "places_in", "isochrone"]}}


GENERATORS = [  # (fn, weight) — weighted toward T2/T3 (the skill)
    (gen_T0_lookup, 10), (gen_T1_compare, 18), (gen_T1_twins, 17),
    (gen_T2_filter_rank, 22), (gen_T2_capture, 13),
    (gen_T3_judgment, 15), (gen_abstain, 5)]


def sample(n, seed=0):
    rng = random.Random(seed)
    pool = [g for g, w in GENERATORS for _ in range(w)]
    out = []
    tries = 0
    while len(out) < n and tries < n * 6:
        tries += 1
        rec = rng.choice(pool)(rng)
        if rec and rec.get("gold"):
            out.append(rec)
    return out


if __name__ == "__main__":
    import json
    for r in sample(8, seed=3):
        print(json.dumps(r))

"""
Intent-layer coverage test — verify every use case is reachable with
natural-language queries via rule-based AND LLM paths.

Structure:
  For each use case, define 5-8 query variants + expected entities.
  Run each via rule-based parser; if confidence < 0.7 OR wrong use case,
  retry with LLM. Report per-use-case pass rate and entity coverage.
"""
import os
import sys
import time
import json
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from merlion import Merlion, IntentParser  # noqa: E402


# ============================================================
# TEST CASES — grouped by expected use case
# Each: (query, expected_use_case, expected_entity_keys)
# expected_entity_keys = subset of keys that must appear; some may be optional
# ============================================================
TESTS = [

    # --- site_selection (9) ---
    ("where should I open a Starbucks in the CBD", "site_selection",
     ["brands", "locations"]),
    ("find 20 sites for expansion like tanjong pagar",
     "site_selection", ["k", "locations"]),
    ("recommend locations for a specialty coffee brand",
     "site_selection", []),
    ("where should we put new FairPrice stores",
     "site_selection", ["brands"]),
    ("I want to open 5 new gyms in mature HDB estates",
     "site_selection", ["k"]),
    ("best places to expand a cafe brand near orchard",
     "site_selection", ["locations"]),
    ("find locations for a new bubble tea concept",
     "site_selection", []),
    ("site selection for a dessert shop in jurong west",
     "site_selection", ["locations"]),
    ("where to put a bakery near bedok",
     "site_selection", ["locations"]),

    # --- gap_analysis (7) ---
    ("where are hawker centres missing in the heartland",
     "gap_analysis", ["categories"]),
    ("which subzones are underserved in childcare",
     "gap_analysis", []),
    ("find gaps in clinic availability",
     "gap_analysis", []),
    ("where is fitness access under-supplied",
     "gap_analysis", []),
    ("areas with missing bakeries",
     "gap_analysis", []),
    ("show me expected vs actual cafe counts",
     "gap_analysis", []),
    ("find structural deficit in education per subzone",
     "gap_analysis", []),

    # --- archetype_clustering (5) ---
    ("cluster all neighborhoods into urban archetypes",
     "archetype_clustering", []),
    ("segment Singapore into 15 archetypes",
     "archetype_clustering", []),
    ("what kind of area is each hex — group by character",
     "archetype_clustering", []),
    ("urban type segmentation for singapore",
     "archetype_clustering", []),
    ("classify all hexes into neighborhood types",
     "archetype_clustering", []),

    # --- comparable_market (6) ---
    ("find 10 comparable hexes to 896520db3afffff",
     "comparable_market", ["hex_ids", "k"]),
    ("hexes like tiong bahru for valuation",
     "comparable_market", ["locations"]),
    ("comps for a shophouse in duxton",
     "comparable_market", []),
    ("neighborhoods similar to orchard road",
     "comparable_market", ["locations"]),
    ("appraise 1.3006, 103.8555 with comparable areas",
     "comparable_market", ["coords"]),
    ("places like ang mo kio for property valuation",
     "comparable_market", ["locations"]),

    # --- whitespace_analysis (5) ---
    ("where is Starbucks missing but should be",
     "whitespace_analysis", ["brands"]),
    ("whitespace areas for a new KFC",
     "whitespace_analysis", ["brands"]),
    ("uncontested hexes for ya kun expansion",
     "whitespace_analysis", []),
    ("where is 7-eleven absent",
     "whitespace_analysis", ["brands"]),
    ("find white space opportunities for cold storage",
     "whitespace_analysis", ["brands"]),

    # --- category_prediction (5) ---
    ("predict expected cafes per hex in orchard area",
     "category_prediction", ["categories", "locations"]),
    ("how many hawker stalls should exist in tampines",
     "category_prediction", ["categories", "locations"]),
    ("forecast restaurant counts by subzone",
     "category_prediction", ["categories"]),
    ("expected count of clinics in bedok",
     "category_prediction", ["categories", "locations"]),
    ("predict retail density across singapore",
     "category_prediction", []),

    # --- feature_query (4) ---
    ("hexes with high walkability and low population",
     "feature_query", []),
    ("show me hexes with a specific feature profile",
     "feature_query", []),
    ("combination of transit access + commerce density",
     "feature_query", []),
    ("find hexes matching high cafe and low comp pressure",
     "feature_query", []),

    # --- amenity_desert (4) ---
    ("find food deserts in singapore",
     "amenity_desert", []),
    ("where are amenity deserts for seniors",
     "amenity_desert", []),
    ("transit deserts in the north",
     "amenity_desert", []),
    ("areas cut off from fresh food access",
     "amenity_desert", []),

    # --- fifteen_minute_city (4) ---
    ("compute 15-minute city score for each hex",
     "fifteen_minute_city", []),
    ("walkability scorecard across singapore",
     "fifteen_minute_city", []),
    ("how walkable is each neighborhood",
     "fifteen_minute_city", []),
    ("15-minute city analysis",
     "fifteen_minute_city", []),

    # --- edge cases / ambiguous ---
    ("what can you do",
     None, []),   # should be unknown / empty
    ("show me the map",
     None, []),   # ambiguous
    ("help",
     None, []),   # unknown
]


def run_test_case(merlion: Merlion, query: str, expected_uc: str | None,
                   expected_keys: list[str], use_llm: bool) -> dict:
    """Run a single query, return comparison result."""
    t0 = time.time()
    result = merlion.ask(query)
    dur = time.time() - t0

    chosen = result.get("chosen")
    chosen_uc = chosen["use_case"] if chosen else None
    chosen_entities = chosen.get("entities", {}) if chosen else {}

    # If the parser fell back to rule-based fallback with low conf, we treat
    # as "miss" unless the expected UC is correct
    confidence = chosen.get("confidence", 0.0) if chosen else 0.0

    # Use-case correctness
    if expected_uc is None:
        uc_pass = (chosen is None) or chosen_uc == "unknown" or confidence < 0.5
    else:
        uc_pass = chosen_uc == expected_uc

    # Entity coverage: do the expected keys exist in chosen_entities?
    ent_missing = []
    for k in expected_keys:
        # For LLM, entities use singular keys (brand, location, category)
        # For rule-based, plural keys (brands, locations, categories)
        # Accept either.
        sing = k.rstrip("s")
        if k not in chosen_entities and sing not in chosen_entities:
            ent_missing.append(k)
    ent_pass = len(ent_missing) == 0

    return {
        "query": query,
        "expected_uc": expected_uc,
        "chosen_uc": chosen_uc,
        "confidence": confidence,
        "strategy": chosen.get("strategy") if chosen else "none",
        "entities": chosen_entities,
        "uc_pass": uc_pass,
        "ent_pass": ent_pass,
        "ent_missing": ent_missing,
        "duration_s": round(dur, 2),
    }


def run_suite(use_llm: bool, verbose: bool = False):
    label = "LLM (Claude Sonnet)" if use_llm else "Rule-based only"
    print(f"\n{'='*72}\n  RUNNING INTENT TESTS — {label}\n{'='*72}")
    merlion = Merlion(use_llm=use_llm)

    results = []
    by_uc = defaultdict(lambda: {"total": 0, "uc_pass": 0, "ent_pass": 0})

    for query, expected_uc, expected_keys in TESTS:
        r = run_test_case(merlion, query, expected_uc, expected_keys, use_llm)
        results.append(r)
        key = expected_uc or "edge_case"
        by_uc[key]["total"] += 1
        if r["uc_pass"]:
            by_uc[key]["uc_pass"] += 1
        if r["ent_pass"]:
            by_uc[key]["ent_pass"] += 1

        if verbose:
            mark_uc = "✓" if r["uc_pass"] else "✗"
            mark_ent = "✓" if r["ent_pass"] else "✗"
            print(f"  [{mark_uc} UC {mark_ent} ENT {r['confidence']:.2f}] "
                  f"{query[:60]:<60} → {r['chosen_uc']}")
            if not r["uc_pass"]:
                print(f"           expected: {expected_uc}")
            if r["ent_missing"]:
                print(f"           missing entities: {r['ent_missing']}")

    # Summary
    total = len(results)
    uc_passes = sum(1 for r in results if r["uc_pass"])
    ent_passes = sum(1 for r in results if r["ent_pass"])
    avg_conf = sum(r["confidence"] for r in results) / total

    print(f"\n{'─'*72}")
    print(f"SUMMARY — {label}")
    print(f"{'─'*72}")
    print(f"  Total tests:       {total}")
    print(f"  Use-case accuracy: {uc_passes}/{total}  ({uc_passes/total*100:.1f}%)")
    print(f"  Entity coverage:   {ent_passes}/{total}  ({ent_passes/total*100:.1f}%)")
    print(f"  Avg confidence:    {avg_conf:.2f}")

    print(f"\n  Per-use-case breakdown:")
    print(f"  {'Use case':<24} {'UC pass':<10} {'Ent pass':<10}")
    print(f"  {'-'*24} {'-'*10} {'-'*10}")
    for uc_name in sorted(by_uc.keys()):
        d = by_uc[uc_name]
        uc_rate = d["uc_pass"] / d["total"] * 100
        ent_rate = d["ent_pass"] / d["total"] * 100
        print(f"  {uc_name:<24} {d['uc_pass']}/{d['total']} ({uc_rate:3.0f}%)  "
              f"{d['ent_pass']}/{d['total']} ({ent_rate:3.0f}%)")

    return {
        "label": label,
        "total": total,
        "uc_passes": uc_passes,
        "ent_passes": ent_passes,
        "avg_confidence": avg_conf,
        "by_uc": dict(by_uc),
        "results": results,
    }


def compare_rule_vs_llm(verbose: bool = False):
    """Run both, show delta."""
    rb = run_suite(use_llm=False, verbose=verbose)
    llm = run_suite(use_llm=True, verbose=verbose)

    print(f"\n{'='*72}\n  RULE-BASED  vs  LLM (Claude Sonnet)  DELTA\n{'='*72}")
    print(f"  Use-case accuracy: {rb['uc_passes']}/{rb['total']} → {llm['uc_passes']}/{llm['total']}  "
          f"(Δ {llm['uc_passes']-rb['uc_passes']:+d})")
    print(f"  Entity coverage:   {rb['ent_passes']}/{rb['total']} → {llm['ent_passes']}/{llm['total']}  "
          f"(Δ {llm['ent_passes']-rb['ent_passes']:+d})")
    print(f"  Avg confidence:    {rb['avg_confidence']:.2f} → {llm['avg_confidence']:.2f}")

    # Save full results
    out_path = os.path.join(os.path.dirname(__file__), "intent_test_results.json")
    with open(out_path, "w") as f:
        json.dump({"rule_based": rb, "llm": llm}, f, indent=2, default=str)
    print(f"\n  Full results → {out_path}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--llm-only", action="store_true")
    ap.add_argument("--rule-only", action="store_true")
    args = ap.parse_args()

    if args.llm_only:
        run_suite(use_llm=True, verbose=args.verbose)
    elif args.rule_only:
        run_suite(use_llm=False, verbose=args.verbose)
    else:
        compare_rule_vs_llm(verbose=args.verbose)

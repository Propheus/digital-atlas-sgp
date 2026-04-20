"""
Intent-layer coverage test — 220 queries across 9 use cases + edge cases.

Tests both rule-based and LLM (Claude Sonnet) routing; reports per-use-case
accuracy, entity coverage, and confidence. Runs in ~15 min for the full
LLM sweep.
"""
import os, sys, time, json
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Load .env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from merlion import Merlion  # noqa: E402


# Entity-key aliases so rule-based (plural) and LLM (singular) both accepted
ENTITY_ALIASES = {
    "categories": {"categories", "category"},
    "locations":  {"locations", "location"},
    "brands":     {"brands", "brand"},
    "hex_ids":    {"hex_ids", "target_hex", "anchor_hexes"},
    "coords":     {"coords"},
    "k":          {"k"},
    "profile":    {"profile"},
}


def check_entity_present(chosen_entities: dict, expected_key: str) -> bool:
    aliases = ENTITY_ALIASES.get(expected_key, {expected_key})
    return any(a in chosen_entities and chosen_entities[a] for a in aliases)


# ============================================================
# 220 TEST CASES
# Format: (query, expected_use_case, list_of_expected_entity_keys)
# expected_use_case=None means "should be unknown/rejected"
# ============================================================
TESTS = []

# ==================== site_selection (25) ====================
TESTS += [(q, "site_selection", k) for q, k in [
    ("where should I open a Starbucks in the CBD", ["brands", "locations"]),
    ("find 20 sites for expansion like tanjong pagar", ["k", "locations"]),
    ("recommend locations for a specialty coffee brand", []),
    ("where should we put new FairPrice stores", ["brands"]),
    ("I want to open 5 new gyms in mature HDB estates", ["k"]),
    ("best places to expand a cafe brand near orchard", ["locations", "categories"]),
    ("find locations for a new bubble tea concept", []),
    ("site selection for a dessert shop in jurong west", ["locations"]),
    ("where to put a bakery near bedok", ["locations", "categories"]),
    ("expand my coffee chain to 3 new neighborhoods", ["k"]),
    ("help me find sites for opening a new salon", []),
    ("where should the next McDonald's go in the heartland", ["brands"]),
    ("I'm opening a bookstore - where are the best sites", []),
    ("find locations similar to tiong bahru for a cafe", ["locations", "categories"]),
    ("expand KFC into the north of singapore", ["brands"]),
    ("20 best locations for a new restaurant concept", ["k", "categories"]),
    ("where to locate a new fitness studio in the central region", []),
    ("site selection for a pet store", []),
    ("open 10 new convenience stores in underserved areas", ["k", "categories"]),
    ("find neighborhoods to expand my ice cream business into", []),
    ("where should I build a new mall in the west", ["categories"]),
    ("locations for a new specialty grocery near the CBD", ["locations"]),
    ("top 15 hexes for a cafe expansion", ["k", "categories"]),
    ("where to open a hawker stall with good foot traffic", ["categories"]),
    ("best locations for expanding a beauty salon chain", ["categories"]),
]]

# ==================== gap_analysis (25) ====================
TESTS += [(q, "gap_analysis", k) for q, k in [
    ("where are hawker centres missing in the heartland", ["categories"]),
    ("which subzones are underserved in childcare", ["categories"]),
    ("find gaps in clinic availability", ["categories"]),
    ("where is fitness access under-supplied", []),
    ("areas with missing bakeries", ["categories"]),
    ("show me expected vs actual cafe counts", ["categories"]),
    ("find structural deficit in education per subzone", ["categories"]),
    ("underserved areas for kindergartens", ["categories"]),
    ("gap between expected and actual restaurants", ["categories"]),
    ("systematic undersupply of hospitals by planning area", ["categories"]),
    ("which subzones don't have enough bakeries", ["categories"]),
    ("amenity gaps for mature HDB residents", []),
    ("where does the model predict more cafes should exist", ["categories"]),
    ("find areas missing 7-eleven or similar", []),
    ("where is specialty retail under-supplied", []),
    ("show the gap between population and gym capacity", ["categories"]),
    ("hexes with systematic deficit in F&B", []),
    ("subzones missing enough schools relative to kids", ["categories"]),
    ("what categories are missing in tampines", ["locations"]),
    ("where are we under provisioned for clinics", ["categories"]),
    ("deficit analysis for hawker centres by subzone", ["categories"]),
    ("undersupplied neighborhoods for beauty salons", []),
    ("missing mall coverage in eastern singapore", ["categories"]),
    ("where are convenience stores below predicted levels", ["categories"]),
    ("amenity gap analysis by residential density", []),
]]

# ==================== archetype_clustering (22) ====================
TESTS += [(q, "archetype_clustering", k) for q, k in [
    ("cluster all neighborhoods into urban archetypes", []),
    ("segment singapore into 15 archetypes", ["k"]),
    ("what kind of area is each hex — group by character", []),
    ("urban type segmentation for singapore", []),
    ("classify all hexes into neighborhood types", []),
    ("group hexes into 10 clusters by urban character", ["k"]),
    ("archetype clustering for the whole city", []),
    ("categorize neighborhoods into types", []),
    ("urban typology for singapore", []),
    ("cluster hexes by their urban profile", []),
    ("create 20 archetypes from the hex embeddings", ["k"]),
    ("segmentation of hexes by character", []),
    ("find urban neighborhood archetypes", []),
    ("segment by neighborhood type", []),
    ("k-means clustering on hex embeddings", []),
    ("group areas by urban style", []),
    ("bucket hexes into character groups", []),
    ("typology of singapore neighborhoods", []),
    ("classify each hex by its urban kind", []),
    ("show me the 12 types of neighborhoods in SG", ["k"]),
    ("segment urban areas into archetypes for policy", []),
    ("what are the different neighborhood types in singapore", []),
]]

# ==================== comparable_market (22) ====================
TESTS += [(q, "comparable_market", k) for q, k in [
    ("find 10 comparable hexes to 896520db3afffff", ["hex_ids", "k"]),
    ("hexes like tiong bahru for valuation", ["locations"]),
    ("comps for a shophouse in duxton", []),
    ("appraise 1.3006, 103.8555 with comparable areas", ["coords"]),
    ("places like ang mo kio for property valuation", ["locations"]),
    ("valuation comps for a cafe location in holland village", []),
    ("comparable neighborhoods to orchard for appraisal", ["locations"]),
    ("real estate comps for hex 89652012345ffff", ["hex_ids"]),
    ("find comparable areas for commercial property analysis", []),
    ("property appraisal: what's similar to marine parade", ["locations"]),
    ("give me comparables for this hex — 8965201aa3bffff", ["hex_ids"]),
    ("appraisal comps for residential property near bukit timah", ["locations"]),
    ("find 8 similar hexes to serangoon for a valuation exercise", ["k", "locations"]),
    ("which areas compare to east coast for property pricing", []),
    ("REIT analyst needs comps to bugis", ["locations"]),
    ("comparable market analysis for kallang", ["locations"]),
    ("valuation exercise for clementi — find comps", ["locations"]),
    ("hexes most similar to bishan for comps", ["locations"]),
    ("give me 15 property comps near jurong east", ["k", "locations"]),
    ("for an apartment near novena, find comparable locations", ["locations"]),
    ("look up comparable shophouse neighborhoods", []),
    ("property valuation using comparable area analysis", []),
]]

# ==================== whitespace_analysis (20) ====================
TESTS += [(q, "whitespace_analysis", k) for q, k in [
    ("where is Starbucks missing but should be", ["brands"]),
    ("whitespace areas for a new KFC", ["brands"]),
    ("uncontested hexes for ya kun expansion", []),
    ("where is 7-eleven absent", ["brands"]),
    ("find white space opportunities for cold storage", ["brands"]),
    ("where should FairPrice expand with no competitors", ["brands"]),
    ("brand whitespace for Toast Box", ["brands"]),
    ("hexes with no Starbucks where one would fit", ["brands"]),
    ("find uncontested territory for McDonald's", ["brands"]),
    ("where is Giant supermarket not yet present", ["brands"]),
    ("whitespace map for Guardian pharmacy", ["brands"]),
    ("which areas lack a Sheng Siong but should have one", ["brands"]),
    ("no-competitor areas for a new cafe chain", []),
    ("hexes without a KFC that match KFC's profile", ["brands"]),
    ("find areas free of Starbucks where it would fit", ["brands"]),
    ("brand whitespace for a new bubble tea operator", []),
    ("where can we enter without facing incumbents", []),
    ("virgin territory for subway sandwiches", ["brands"]),
    ("white space hexes for expansion without competition", []),
    ("where are the brand absence pockets", []),
]]

# ==================== category_prediction (20) ====================
TESTS += [(q, "category_prediction", k) for q, k in [
    ("predict expected cafes per hex in orchard area", ["categories", "locations"]),
    ("how many hawker stalls should exist in tampines", ["categories", "locations"]),
    ("forecast restaurant counts by subzone", ["categories"]),
    ("expected count of clinics in bedok", ["categories", "locations"]),
    ("predict retail density across singapore", []),
    ("how many cafes does the model say a hex should have", ["categories"]),
    ("expected number of gyms in jurong west", ["categories", "locations"]),
    ("predict hospital demand per subzone", ["categories"]),
    ("what's the expected count of schools in each area", ["categories"]),
    ("forecast convenience store density", ["categories"]),
    ("expected fitness studios for each hex", ["categories"]),
    ("model-predicted count of restaurants per hex", ["categories"]),
    ("predict bakery density by area", ["categories"]),
    ("how many salons should exist in each subzone", ["categories"]),
    ("expected office density across singapore", []),
    ("predict hotel counts per subzone", ["categories"]),
    ("how many bars should be in each hex", ["categories"]),
    ("forecast mall density by region", []),
    ("expected childcare centre counts", []),
    ("model prediction of cafe saturation per hex", ["categories"]),
]]

# ==================== feature_query (18) ====================
TESTS += [(q, "feature_query", k) for q, k in [
    ("hexes with high walkability and low population", []),
    ("show me hexes with a specific feature profile", []),
    ("combination of high transit access and low commerce density", []),
    ("find hexes matching high cafe and low comp pressure", []),
    ("hexes with high MRT access but low retail", []),
    ("find hexes with high population density and good walkability", []),
    ("hexes matching a profile of high tourist draw and high walk score", []),
    ("combine high demand_diversity with low competitor pressure", []),
    ("find hexes scoring high on both residential and fitness", []),
    ("hexes with both high office density and good transit", []),
    ("multi-feature query: high cafe + low hawker", []),
    ("find hexes matching high culture + high hospitality", []),
    ("hexes scoring high on walkability and low on population", []),
    ("profile-based hex retrieval: low density + high MRT", []),
    ("retrieve hexes with specific feature constraints", []),
    ("hexes with high office count AND high mrt access AND low residential", []),
    ("multi-attribute hex query", []),
    ("find hexes matching a given set of feature values", []),
]]

# ==================== amenity_desert (18) ====================
TESTS += [(q, "amenity_desert", k) for q, k in [
    ("find food deserts in singapore", []),
    ("where are amenity deserts for seniors", []),
    ("transit deserts in the north", []),
    ("areas cut off from fresh food access", []),
    ("hexes where elderly can't reach basic amenities", []),
    ("find healthcare deserts", []),
    ("walkability deserts: where amenity access is poor", []),
    ("which areas are cut off from essential services", []),
    ("grocery deserts in the east", []),
    ("regions with poor access to daily needs", []),
    ("areas where low-income residents lack amenities", []),
    ("food desert map for singapore", []),
    ("which hexes are transit-isolated with no amenities", []),
    ("vulnerable populations in amenity-desert areas", []),
    ("identify neighborhoods cut off from hawker food", []),
    ("transit + food desert intersection", []),
    ("areas where seniors have low amenity access", []),
    ("flag amenity desert hexes for equity analysis", []),
]]

# ==================== fifteen_minute_city (15) ====================
TESTS += [(q, "fifteen_minute_city", k) for q, k in [
    ("compute 15-minute city score for each hex", []),
    ("walkability scorecard across singapore", []),
    ("how walkable is each neighborhood", []),
    ("15-minute city analysis", []),
    ("amenity access score per hex", []),
    ("how many categories are within 15 min walk from each hex", []),
    ("walkability heat map for singapore", []),
    ("15min city compliance for every subzone", []),
    ("walkable city score per area", []),
    ("how close are residents to daily needs", []),
    ("score each hex on 15 min accessibility", []),
    ("walkability report across the city", []),
    ("walk-score-style amenity accessibility for singapore", []),
    ("15 minute city audit", []),
    ("per-hex pedestrian access to services", []),
]]

# ==================== edge cases (unknown / ambiguous) (15) ====================
TESTS += [(q, None, []) for q in [
    "what can you do",
    "show me the map",
    "help",
    "hello",
    "who are you",
    "how does this work",
    "print the weather",
    "what is the GDP of singapore",
    "explain machine learning",
    "show me star trek episodes",
    "",     # empty
    "   ",  # whitespace
    "qwerty asdf",
    "random nonsense string 123",
    "tell me a joke",
]]


# ============================================================
# RUNNER
# ============================================================
def run_one(merlion: Merlion, query: str, expected_uc, expected_keys: list[str]) -> dict:
    t0 = time.time()
    try:
        result = merlion.ask(query)
    except Exception as e:
        return {"query": query, "expected_uc": expected_uc, "chosen_uc": None,
                "confidence": 0.0, "strategy": "error", "entities": {},
                "uc_pass": False, "ent_pass": False, "ent_missing": expected_keys,
                "duration_s": round(time.time() - t0, 2), "error": str(e)}

    chosen = result.get("chosen")
    chosen_uc = chosen["use_case"] if chosen else None
    chosen_entities = chosen.get("entities", {}) if chosen else {}
    confidence = chosen.get("confidence", 0.0) if chosen else 0.0

    if expected_uc is None:
        uc_pass = (chosen is None) or chosen_uc == "unknown" or confidence < 0.5
    else:
        uc_pass = chosen_uc == expected_uc

    ent_missing = [k for k in expected_keys if not check_entity_present(chosen_entities, k)]
    ent_pass = len(ent_missing) == 0

    return {"query": query, "expected_uc": expected_uc, "chosen_uc": chosen_uc,
            "confidence": confidence, "strategy": chosen.get("strategy") if chosen else "none",
            "entities": chosen_entities, "uc_pass": uc_pass, "ent_pass": ent_pass,
            "ent_missing": ent_missing, "duration_s": round(time.time() - t0, 2)}


def run_suite(use_llm: bool, progress_every: int = 20):
    label = "LLM (Claude Sonnet)" if use_llm else "Rule-based only"
    print(f"\n{'='*72}\n  RUNNING — {label}  |  {len(TESTS)} tests\n{'='*72}", flush=True)
    merlion = Merlion(use_llm=use_llm)

    results = []
    t0 = time.time()
    for i, (query, expected_uc, expected_keys) in enumerate(TESTS, 1):
        r = run_one(merlion, query, expected_uc, expected_keys)
        results.append(r)
        if i % progress_every == 0 or i == len(TESTS):
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed else 0
            eta = (len(TESTS) - i) / rate if rate else 0
            passes = sum(1 for x in results if x["uc_pass"])
            print(f"  [{i:>3}/{len(TESTS)}] elapsed {elapsed:.0f}s  "
                  f"rate {rate:.1f}/s  ETA {eta:.0f}s  "
                  f"UC pass rate {passes/i*100:.1f}%", flush=True)

    # Aggregate
    by_uc = defaultdict(lambda: {"total": 0, "uc_pass": 0, "ent_pass": 0, "samples": []})
    for r in results:
        key = r["expected_uc"] or "edge_case"
        by_uc[key]["total"] += 1
        if r["uc_pass"]:
            by_uc[key]["uc_pass"] += 1
        if r["ent_pass"]:
            by_uc[key]["ent_pass"] += 1
        if not r["uc_pass"] and len(by_uc[key]["samples"]) < 3:
            by_uc[key]["samples"].append({"q": r["query"][:70], "got": r["chosen_uc"]})

    total = len(results)
    uc_pass = sum(1 for r in results if r["uc_pass"])
    ent_pass = sum(1 for r in results if r["ent_pass"])
    avg_conf = sum(r["confidence"] for r in results) / total

    print(f"\n{'─'*72}\nSUMMARY — {label}\n{'─'*72}")
    print(f"  Total tests:       {total}")
    print(f"  Use-case accuracy: {uc_pass}/{total}  ({uc_pass/total*100:.1f}%)")
    print(f"  Entity coverage:   {ent_pass}/{total}  ({ent_pass/total*100:.1f}%)")
    print(f"  Avg confidence:    {avg_conf:.2f}")
    print(f"  Total time:        {time.time() - t0:.0f}s")

    print(f"\n  Per-use-case breakdown:")
    print(f"  {'Use case':<24} {'UC pass':<14} {'Ent pass':<14}")
    print(f"  {'-'*24} {'-'*14} {'-'*14}")
    for uc in sorted(by_uc.keys()):
        d = by_uc[uc]
        print(f"  {uc:<24} {d['uc_pass']:>3}/{d['total']:<3} ({d['uc_pass']/d['total']*100:3.0f}%)  "
              f"{d['ent_pass']:>3}/{d['total']:<3} ({d['ent_pass']/d['total']*100:3.0f}%)")

    # Show sample misroutes
    print(f"\n  Sample misroutes (up to 3 per use case):")
    for uc, d in by_uc.items():
        if d["samples"]:
            print(f"  {uc}:")
            for s in d["samples"]:
                print(f"    '{s['q']}' → {s['got']}")

    return {"label": label, "total": total, "uc_passes": uc_pass, "ent_passes": ent_pass,
            "avg_confidence": avg_conf, "by_uc": {k: dict(v) for k, v in by_uc.items()},
            "results": results, "duration_s": time.time() - t0}


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm-only", action="store_true")
    ap.add_argument("--rule-only", action="store_true")
    args = ap.parse_args()

    out = {}
    if not args.llm_only:
        out["rule_based"] = run_suite(use_llm=False)
    if not args.rule_only:
        out["llm"] = run_suite(use_llm=True)

    if "rule_based" in out and "llm" in out:
        rb, lm = out["rule_based"], out["llm"]
        print(f"\n{'='*72}\n  DELTA: rule-based → LLM\n{'='*72}")
        print(f"  UC accuracy:     {rb['uc_passes']}/{rb['total']} → {lm['uc_passes']}/{lm['total']}  "
              f"({rb['uc_passes']/rb['total']*100:.1f}% → {lm['uc_passes']/lm['total']*100:.1f}%, "
              f"Δ {lm['uc_passes']-rb['uc_passes']:+d})")
        print(f"  Entity coverage: {rb['ent_passes']}/{rb['total']} → {lm['ent_passes']}/{lm['total']}  "
              f"(Δ {lm['ent_passes']-rb['ent_passes']:+d})")
        print(f"  Avg confidence:  {rb['avg_confidence']:.2f} → {lm['avg_confidence']:.2f}")

    out_path = os.path.join(os.path.dirname(__file__), "intent_test_220_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n  Full results saved → {out_path}")


if __name__ == "__main__":
    main()

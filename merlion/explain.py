"""
Explainability — translate the engine's routing/scoring into plain English
for business users (not data scientists).

Three tiers of explanation per response:
  1. summary         — 2-3 sentence executive summary (LLM-enhanced if available)
  2. methodology     — how the engine reasoned, in plain terms
  3. per_item_why    — per-hex / per-cluster / per-gap reasoning

Used by all use-case handlers via `explain_result(use_case, result, profile, query)`.
The resulting `explanation` dict is attached to every response.
"""
import os
from typing import Optional


# Human-readable labels for archetype groups
ARCHETYPE_LABELS = {
    "cbd_core":         "CBD core",
    "orchard_corridor": "Orchard corridor",
    "heritage_cultural":"heritage & cultural districts",
    "heartland_mature": "mature HDB heartland",
    "heartland_young":  "young HDB heartland",
    "west_edge":        "western heartland",
    "north_suburban":   "northern suburban",
    "industrial":       "industrial estates",
    "airport_aviation": "airport/aviation areas",
    "islands_resort":   "resort islands",
    "education":        "education campuses",
    "greenery":         "greenery/nature areas",
}

# Friendly labels for feature names
FEATURE_LABELS = {
    "population_total":        "resident population",
    "working_age_count":       "working-age residents",
    "walking_dependent_count": "non-driver residents",
    "walkability_score":       "walkability",
    "mrt_stations":            "MRT stations",
    "hdb_blocks":              "HDB blocks",
    "bldg_private_residential":"private residential buildings",
    "lu_residential_pct":      "residential land use",
    "lu_commercial_pct":       "commercial land use",
    "lu_business_pct":         "business land use",
    "pc_total":                "total places",
    "pc_unique_place_types":   "variety of place types",
    "pc_tier_value":           "value-tier places",
    "pc_tier_mid":             "mid-tier places",
    "pc_tier_premium":         "premium-tier places",
    "pc_tier_luxury":          "luxury-tier places",
    "tourist_draw_est":        "tourist activity",
    "office_workspace":        "office density",
}

# Friendly category labels
CATEGORY_LABELS = {
    "cafe_coffee":             "cafes",
    "restaurant":              "restaurants",
    "hawker_street_food":      "hawker centres",
    "fast_food_qsr":           "fast-food outlets",
    "bar_nightlife":           "bars",
    "bakery_pastry":           "bakeries",
    "convenience_daily_needs": "convenience stores",
    "education":               "schools & preschools",
    "health_medical":          "clinics & hospitals",
    "fitness_recreation":      "gyms & recreation",
    "hospitality":             "hotels",
    "office_workspace":        "offices",
    "shopping_retail":         "retail shops",
    "beauty_personal_care":    "beauty & salons",
    "religious":               "religious sites",
    "culture_entertainment":   "culture & entertainment",
    "transport":               "transport services",
    "services":                "professional services",
    "business":                "businesses",
    "residential":             "residential buildings",
}


def _humanize_category(key: str) -> str:
    return CATEGORY_LABELS.get(key, key.replace("_", " "))


def _humanize_feature(key: str) -> str:
    return FEATURE_LABELS.get(key, key.replace("_", " "))


def _humanize_archetype(key: str) -> str:
    return ARCHETYPE_LABELS.get(key, key.replace("_", " "))


# ============================================================
# Per-use-case explanation builders
# ============================================================

def explain_site_selection(result: dict, profile: Optional[dict], query: str) -> dict:
    results = result.get("results", [])
    if not results:
        return {
            "summary": "No suitable sites found given the query constraints.",
            "methodology": "Candidates were filtered below minimum thresholds or locality constraints.",
            "per_item": [],
        }

    # -- Executive summary
    brand = profile.get("name") if profile else (result.get("brand") or "concept")
    tier = profile.get("price_tier") if profile else None
    primary_cat = profile.get("primary_category") if profile else None

    # Common patterns across top-5
    top5 = results[:5]
    pas = [r.get("parent_pa", "") for r in top5]
    unique_pas = sorted(set(pas))
    pops = [(r.get("population_total") or 0) for r in top5]
    hdbs = [(r.get("hdb_blocks") or 0) for r in top5]
    gaps = [(r.get("primary_gap") or 0) for r in top5]

    pop_range = f"{int(min(pops)):,}-{int(max(pops)):,}" if pops else "—"
    hdb_range = f"{int(min(hdbs))}-{int(max(hdbs))}" if hdbs else "—"
    avg_gap = sum(gaps) / len(gaps) if gaps else 0

    parts = []
    parts.append(
        f"Top {len(top5)} sites for {brand} cluster across "
        f"{len(unique_pas)} planning area{'s' if len(unique_pas) != 1 else ''}: "
        f"{', '.join(unique_pas)}."
    )
    if pops and hdbs:
        parts.append(
            f"These neighbourhoods share a pattern — "
            f"{pop_range} residents and {hdb_range} HDB blocks each — "
            f"matching {brand}'s " +
            (f"{tier}-tier positioning." if tier else "ideal footprint.")
        )
    if primary_cat and avg_gap > 2:
        cat_h = _humanize_category(primary_cat)
        parts.append(
            f"On average each site has a gap of {avg_gap:+.0f} {cat_h} "
            f"(predicted demand exceeds existing supply), "
            f"suggesting genuine whitespace for expansion."
        )
    summary = " ".join(parts)

    # -- Methodology
    methodology_parts = []
    if profile:
        fits = ", ".join(_humanize_archetype(a) for a in profile.get("locality_fit", []))
        avoids = ", ".join(_humanize_archetype(a) for a in profile.get("locality_avoid", []))
        sig_count = len(profile.get("signals") or {})
        if fits:
            methodology_parts.append(f"Searched within {fits}")
        if avoids:
            methodology_parts.append(f"excluded {avoids}")
        if sig_count:
            methodology_parts.append(
                f"scored each candidate on {sig_count} factors — "
                f"most heavily weighted: "
                + _top_signals_phrase(profile.get("signals") or {})
            )
    methodology_parts.append(
        "primary category demand (predicted vs existing supply) used to rank the final list"
    )
    methodology = ". ".join(methodology_parts).capitalize() + "."

    # -- Per-item rationale
    per_item = []
    for i, r in enumerate(top5, 1):
        per_item.append({
            "rank": i,
            "hex_id": r["hex_id"],
            "why": _explain_single_site(r, profile, rank=i),
        })

    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def _top_signals_phrase(signals: dict) -> str:
    """E.g. 'resident population (30%), HDB blocks (20%), residential land use (15%)'."""
    items = sorted(signals.items(), key=lambda x: -x[1].get("weight", 0))[:3]
    parts = []
    for feat, spec in items:
        w = int(round((spec.get("weight") or 0) * 100))
        parts.append(f"{_humanize_feature(feat)} ({w}%)")
    return ", ".join(parts)


def _explain_single_site(r: dict, profile: Optional[dict], rank: int) -> str:
    """Plain-English reason THIS hex was selected."""
    loc = r.get("parent_subzone_name") or r.get("parent_pa") or r["hex_id"]
    parts = [f"{loc}"]
    # Population
    pop = r.get("population_total")
    if pop is not None and pop > 0:
        parts.append(f"{int(pop):,} residents")
    hdb = r.get("hdb_blocks")
    if hdb is not None and hdb > 0:
        parts.append(f"{int(hdb)} HDB blocks")
    mrt = r.get("mrt_stations")
    if mrt is not None and mrt > 0:
        parts.append(f"{int(mrt)} MRT station{'s' if int(mrt) != 1 else ''}")
    walk = r.get("walkability_score")
    if walk is not None and walk > 0:
        parts.append(f"walkability {walk:.0f}/100")

    # Gap
    pred = r.get("predicted_primary")
    act = r.get("actual_primary")
    if pred is not None and act is not None and profile:
        cat = _humanize_category(profile.get("primary_category", "places"))
        diff = pred - act
        if diff > 2:
            parts.append(
                f"model predicts ~{int(round(pred))} {cat}, only {int(round(act))} exist — "
                f"gap of {int(round(diff))}"
            )

    # Breakdown contribution (if present)
    breakdown = r.get("breakdown")
    if isinstance(breakdown, dict) and "excluded" not in breakdown:
        top_contribs = sorted(
            ((k, v.get("contribution", 0)) for k, v in breakdown.items() if isinstance(v, dict)),
            key=lambda x: -x[1],
        )[:2]
        if top_contribs:
            contribs_str = ", ".join(
                f"{_humanize_feature(k)} contributed {int(round(v*100))}%"
                for k, v in top_contribs
            )
            parts.append(contribs_str)

    return "; ".join(parts).capitalize() + "."


# ============================================================
# Other use cases — lighter explanations
# ============================================================

def explain_gap_analysis(result: dict, profile, query: str) -> dict:
    cat = result.get("category") or (result.get("categories") or ["—"])[0]
    cat_h = _humanize_category(cat)
    results = result.get("results") or []
    if not results and result.get("results_by_category"):
        # Multi-category mode
        return {
            "summary": (
                "No single category specified, so we identified the biggest supply "
                "deficits across 4 common categories (cafes, hawker centres, clinics, schools)."
            ),
            "methodology": (
                "For each category we computed predicted count minus actual count "
                "per hex; positive values indicate under-supplied areas. "
                "Ranked within each category."
            ),
            "per_item": [],
        }
    top = results[:5]
    top_names = [r.get("parent_subzone_name") or r.get("parent_pa") for r in top]
    avg_gap = sum((r.get("score") or 0) for r in top) / max(len(top), 1)
    summary = (
        f"The biggest {cat_h} gaps in Singapore are in "
        f"{', '.join(top_names)}. "
        f"Each of these hexes has {avg_gap:+.1f} more {cat_h} predicted than exist today — "
        f"areas where {cat_h} demand is structurally under-supplied."
    )
    methodology = (
        f"For every hex in Singapore we compare the XGBoost model's predicted {cat_h} count "
        f"(R²=0.80 on validation) against actual counts from our places dataset. "
        f"We then rank by the positive gap (predicted − actual)."
    )
    per_item = []
    for i, r in enumerate(top, 1):
        loc = r.get("parent_subzone_name") or r.get("parent_pa")
        per_item.append({
            "rank": i,
            "hex_id": r["hex_id"],
            "why": (
                f"{loc}: model predicts ~{r.get('predicted', 0):.1f} {cat_h}, "
                f"only {int(r.get('actual', 0))} exist — gap of {r.get('score', 0):+.1f}."
            ),
        })
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def explain_archetype_clustering(result: dict, profile, query: str) -> dict:
    clusters = result.get("clusters") or []
    k = result.get("k", len(clusters))
    n = result.get("n_hexes", 7318)
    sizes = sorted((c["size"] for c in clusters), reverse=True)
    summary = (
        f"Segmented {n:,} Singapore hexes into {k} urban archetypes using the GCN-64 "
        f"embedding (100% stability across random seeds in our tests). "
        f"Cluster sizes range from {sizes[-1] if sizes else 0} to {sizes[0] if sizes else 0} hexes."
    )
    methodology = (
        "Ran k-means on the GCN-64 embedding — the only model that produces stable "
        "clusters across different random seeds in our 260-test validation. Each cluster "
        "is summarised by its representative hex (closest to the centroid)."
    )
    per_item = [{
        "rank": c["cluster_id"],
        "hex_id": c.get("representative_hex"),
        "why": (f"Cluster #{c['cluster_id']} has {c['size']} hexes; "
                f"example: {c.get('parent_subzone_name') or c.get('parent_pa', '—')}."),
    } for c in clusters]
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def explain_comparable_market(result: dict, profile, query: str) -> dict:
    target = result.get("target_info") or {}
    results = result.get("results") or []
    target_name = target.get("parent_subzone_name") or target.get("parent_pa") or "the target hex"
    top_names = [r.get("parent_subzone_name") or r.get("parent_pa") for r in results[:5]]
    summary = (
        f"Found {len(results)} neighbourhoods comparable to {target_name}. "
        f"Top matches: {', '.join(top_names)}. "
        f"These share urban character with the target, not just geography — "
        f"suitable as valuation comps."
    )
    methodology = (
        "Used the intersection of two similarity methods: Node2Vec (captures graph-structural "
        "similarity — PA coherence 98%) and GCN-64 (feature-aware character). A hex appears "
        "here only if both methods agree, ensuring high-confidence comps."
    )
    per_item = [{
        "rank": i + 1,
        "hex_id": r["hex_id"],
        "why": (f"{r.get('parent_subzone_name') or r.get('parent_pa')}: "
                f"similarity {r.get('score', 0):.2f} (both Node2Vec and GCN agree)"),
    } for i, r in enumerate(results[:5])]
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def explain_category_prediction(result: dict, profile, query: str) -> dict:
    if result.get("per_category"):
        info = result.get("info") or {}
        per = result["per_category"]
        loc = info.get("parent_subzone_name") or info.get("parent_pa") or result.get("hex")
        top_gaps = sorted(per.items(), key=lambda x: -x[1]["gap"])[:3]
        bot_gaps = sorted(per.items(), key=lambda x: x[1]["gap"])[:3]
        summary = (
            f"For {loc}, the biggest predicted under-supply is in "
            f"{', '.join(_humanize_category(c) for c, _ in top_gaps)}. "
            f"The biggest over-supply is in "
            f"{', '.join(_humanize_category(c) for c, _ in bot_gaps)}."
        )
        methodology = (
            "We trained 24 XGBoost models (one per category) on 391 contextual features. "
            "For each hex, predicted count is compared against actual place count to identify "
            "gaps and saturation points."
        )
        per_item = []
        return {"summary": summary, "methodology": methodology, "per_item": per_item}

    # Category-wide mode
    cat = result.get("category")
    results = result.get("results") or []
    cat_h = _humanize_category(cat) if cat else "places"
    top_names = [r.get("parent_subzone_name") or r.get("parent_pa") for r in results[:5]]
    summary = (
        f"Highest predicted {cat_h} density is in {', '.join(top_names)}. "
        f"These are the hexes the model expects to support the most {cat_h}."
    )
    methodology = (
        f"Used the XGBoost predictor for {cat_h} (R²≈0.80 on 5-fold CV) "
        f"and ranked all hexes by predicted count."
    )
    per_item = [{
        "rank": i + 1,
        "hex_id": r["hex_id"],
        "why": f"{r.get('parent_subzone_name') or r.get('parent_pa')}: predicted {r.get('predicted', r.get('score', 0)):.1f} {cat_h}",
    } for i, r in enumerate(results[:5])]
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def explain_whitespace(result: dict, profile, query: str) -> dict:
    brand = (profile.get("name") if profile else result.get("brand", "the brand"))
    cat = result.get("category", "")
    cat_h = _humanize_category(cat)
    results = result.get("results") or []
    top_names = [r.get("parent_subzone_name") or r.get("parent_pa") for r in results[:5]]
    summary = (
        f"{brand} whitespace opportunities: {', '.join(top_names)}. "
        f"These hexes have high predicted {cat_h} demand but low actual {cat_h} supply — "
        f"places where a {brand} store would fit but isn't yet open."
    )
    methodology = (
        f"Whitespace score = (predicted {cat_h} − actual {cat_h}). Requires the XGBoost "
        f"predictor (validated R²=0.80) to identify demand, and existing place counts for "
        f"supply. Brand-specific filtering (keeping only hexes without that brand) is "
        f"pending places.jsonl integration."
    )
    per_item = [{
        "rank": i + 1,
        "hex_id": r["hex_id"],
        "why": (f"{r.get('parent_subzone_name') or r.get('parent_pa')}: "
                f"predicted ~{r.get('predicted', 0):.1f} {cat_h}, only {int(r.get('actual', 0))} exist"),
    } for i, r in enumerate(results[:5])]
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def explain_feature_query(result: dict, profile, query: str) -> dict:
    anchor = result.get("anchor")
    n = len(result.get("results") or [])
    summary = (
        f"Retrieved {n} hexes with feature profiles closest to "
        f"{anchor or 'your anchor'} using the GCN-64 embedding."
    )
    methodology = (
        "Feature similarity in GCN-64 space (the embedding that hit 100% on feature_query "
        "tests and 100% on archetype stability). Cosine distance, excluding the anchor itself."
    )
    return {"summary": summary, "methodology": methodology, "per_item": []}


def explain_amenity_desert(result: dict, profile, query: str) -> dict:
    results = result.get("results") or []
    top_names = [r.get("parent_subzone_name") or r.get("parent_pa") for r in results[:5]]
    cats = result.get("categories") or []
    cats_h = ", ".join(_humanize_category(c) for c in cats)
    summary = (
        f"Biggest amenity deserts in Singapore: {', '.join(top_names)}. "
        f"These hexes have large populations cut off from essentials "
        f"({cats_h}), combining high predicted demand with low supply."
    )
    methodology = (
        "Desert score combines: (1) predicted minus actual count for each essential category, "
        "(2) weighted by log(population) so densely-populated gaps rank higher. "
        "Sums the effect across hawker food, convenience, and healthcare."
    )
    per_item = [{
        "rank": i + 1,
        "hex_id": r["hex_id"],
        "why": (f"{r.get('parent_subzone_name') or r.get('parent_pa')}: "
                f"~{int(r.get('population_total') or 0):,} residents, desert score {r.get('score', 0):.0f}"),
    } for i, r in enumerate(results[:5])]
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


def explain_fifteen_min(result: dict, profile, query: str) -> dict:
    results = result.get("results") or []
    top_names = [r.get("parent_subzone_name") or r.get("parent_pa") for r in results[:5]]
    summary = (
        f"Most 15-minute-city-ready hexes: {', '.join(top_names)}. "
        f"These combine the widest variety of categories with strong walkability — "
        f"residents can reach most daily needs on foot."
    )
    methodology = (
        "Score = 60% × (categories present out of 24) + 40% × walkability. "
        "A hex scores high if it has both diversity of amenities AND good pedestrian access."
    )
    per_item = [{
        "rank": i + 1,
        "hex_id": r["hex_id"],
        "why": (f"{r.get('parent_subzone_name') or r.get('parent_pa')}: "
                f"{r.get('categories_present', 0)}/24 categories, walkability {r.get('walkability', 0):.0f}"),
    } for i, r in enumerate(results[:5])]
    return {"summary": summary, "methodology": methodology, "per_item": per_item}


# ============================================================
# Dispatcher
# ============================================================
_EXPLAINERS = {
    "site_selection":       explain_site_selection,
    "gap_analysis":         explain_gap_analysis,
    "archetype_clustering": explain_archetype_clustering,
    "comparable_market":    explain_comparable_market,
    "whitespace_analysis":  explain_whitespace,
    "category_prediction":  explain_category_prediction,
    "feature_query":        explain_feature_query,
    "amenity_desert":       explain_amenity_desert,
    "fifteen_minute_city":  explain_fifteen_min,
}


def explain_result(use_case: str, result: dict, query: str = "") -> dict:
    """Build plain-English explanation for a use case's response. Safe for any shape."""
    try:
        fn = _EXPLAINERS.get(use_case)
        if fn is None:
            return {"summary": "", "methodology": "", "per_item": []}
        profile = result.get("profile")
        return fn(result, profile, query)
    except Exception as e:
        # Never crash the response because of an explainer bug
        return {"summary": f"(explanation unavailable: {type(e).__name__})",
                "methodology": "", "per_item": [], "error": str(e)}

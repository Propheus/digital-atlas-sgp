"""
Real handlers for each use case. Imported by registry.py at module load.

Each handler receives (params: dict, ctx: Merlion) and returns a dict with:
  results      — list of hex records (enriched with identity + score)
  meta         — routing info (populated by registry)
  explanation  — one-line what-we-did for UX
  counts       — numeric summaries where relevant

Design goals:
  - Every handler < 60 LOC
  - Clear separation: resolve → query models → fuse → enrich
  - Uniform result shape for the frontend
"""
from typing import Any

from ..models.hub import hub
from ..models import ensemble
from ..resolver import (
    resolve_anchor_hex, resolve_all_anchors, resolve_category,
    resolve_k, resolve_brand, resolve_location_name,
)
from ..concept import ConceptProfiler

# Singleton profiler (reads ANTHROPIC_API_KEY from env)
_profiler = ConceptProfiler()


# ============================================================
# Profile-based scoring helpers
# ============================================================
def _score_hex_by_profile(hex_id: str, profile) -> tuple[float, dict]:
    """
    Composite score for a hex against a concept profile's signals.
    Returns (score, breakdown). Signals with 'min' act as hard filters.
    """
    import numpy as np
    raw = hub.features.raw_df()
    row = raw[raw["hex_id"] == hex_id]
    if row.empty:
        return 0.0, {}
    row = row.iloc[0]

    breakdown = {}
    total = 0.0
    for feat, spec in profile.signals.items():
        if feat not in raw.columns:
            continue
        val = float(row[feat]) if row[feat] is not None else 0.0
        mn = spec.get("min")
        if mn is not None and val < mn:
            return 0.0, {"excluded": f"{feat} < min {mn}"}
        weight = float(spec.get("weight", 0))
        direction = spec.get("direction", "high")
        # Normalize to [0,1] via percentile within the full distribution
        col = raw[feat].dropna()
        if col.empty or col.max() == col.min():
            norm_val = 0.0
        else:
            norm_val = (val - col.min()) / (col.max() - col.min())
            if direction == "low":
                norm_val = 1.0 - norm_val
        contribution = weight * float(norm_val)
        total += contribution
        breakdown[feat] = {"value": val, "normalized": norm_val, "contribution": contribution}
    return total, breakdown


def _locality_filter(hex_id: str, profile) -> bool:
    """True if hex's PA is in locality_fit (or not in locality_avoid)."""
    from ..concept.profiler import pa_to_archetypes
    pa = hub.features.identity(hex_id).get("parent_pa", "")
    fams = pa_to_archetypes(pa)
    if profile.locality_avoid and any(f in fams for f in profile.locality_avoid):
        return False
    if profile.locality_fit:
        return any(f in fams for f in profile.locality_fit)
    return True


# ============================================================
# Shared enrichment
# ============================================================
def enrich_hex_list(items: list[dict], extra_fields: list[str] = None) -> list[dict]:
    """Add lat/lng, parent_subzone, parent_pa to each hex result. Preserves all original keys."""
    extra_fields = extra_fields or []
    out = []
    for it in items:
        ident = hub.features.identity(it["hex_id"])
        # Start with original item (preserves predicted/actual/breakdown/etc.)
        rec = dict(it)
        rec.update({
            "lat": ident.get("lat"),
            "lng": ident.get("lng"),
            "parent_subzone": ident.get("parent_subzone"),
            "parent_subzone_name": ident.get("parent_subzone_name"),
            "parent_pa": ident.get("parent_pa"),
        })
        for f in extra_fields:
            val = hub.features.get(it["hex_id"], f)
            if val is not None:
                rec[f] = val
        out.append(rec)
    return out


def no_anchor_response(reason: str = "No anchor hex / location found in query.") -> dict:
    return {"status": "needs_input", "reason": reason, "results": []}


# ============================================================
# 1. SITE SELECTION
# ============================================================
def handle_site_selection(params: dict, ctx: Any = None) -> dict:
    """
    Site selection with concept-profile awareness:
      1. If a brand/concept is named → build or fetch a structured profile
         (LLM-expanded: category, demographics, locality, signals, competitors)
      2. Generate candidates:
          - If anchors given → centroid similarity in node2vec+gcn
          - Else → filter by locality_fit + feasibility (primary_category pred > threshold)
      3. Score each candidate by composite profile signals
      4. Exclude locality_avoid PAs
      5. Return ranked list with scoring breakdown + profile shown to user
    """
    import numpy as np
    k = resolve_k(params, default=20)
    brand = resolve_brand(params)
    category = resolve_category(params)
    anchors = resolve_all_anchors(params, hub)

    # ==== Step 1: build concept profile ====
    profile = None
    if brand:
        profile = _profiler.profile(brand)
    elif category:
        # Build a shallow profile from the category
        profile = _profiler.profile(category)

    # ==== Step 2: candidate generation ====
    candidates = []
    candidate_source = ""
    if anchors:
        n2v_c = hub.node2vec.centroid(anchors)
        gcn_c = hub.gcn.centroid(anchors)
        n2v_top = hub.node2vec.similar_to_vector(n2v_c, k=k*4, exclude=set(anchors)) if n2v_c is not None else []
        gcn_top = hub.gcn.similar_to_vector(gcn_c, k=k*4, exclude=set(anchors)) if gcn_c is not None else []
        candidates = ensemble.rank_fusion_rrf([n2v_top, gcn_top], k=k*3)
        candidate_source = f"centroid of {len(anchors)} anchor{'s' if len(anchors)>1 else ''} (node2vec+gcn RRF)"
    elif profile:
        # No anchor: start from hexes in locality_fit PAs (NOT from CBD-heavy
        # predicted-category lists, which would be filtered out by locality_avoid).
        from ..concept.profiler import PA_ARCHETYPES
        fit_pas = set()
        for arch in profile.locality_fit:
            fit_pas.update(PA_ARCHETYPES.get(arch, set()))
        raw = hub.features.raw_df()
        fit_hexes = raw[raw["parent_pa"].isin(fit_pas)]["hex_id"].tolist() if fit_pas else raw["hex_id"].tolist()

        # Pre-filter by primary category's predicted count (demand signal)
        cat = profile.primary_category
        pred = hub.xgboost.predict_all_hexes(cat) if cat else None
        scored_initial = []
        for h in fit_hexes:
            p = float(pred.get(h, 0)) if pred is not None and not pred.empty else 0.0
            scored_initial.append({"hex_id": h, "score": p})
        scored_initial.sort(key=lambda x: -x["score"])
        candidates = scored_initial[:max(k*5, 200)]   # keep a large candidate pool for profile-scoring
        candidate_source = (f"{len(candidates)} hexes in locality_fit PAs "
                             f"(sorted by predicted {cat})" if cat else
                             f"{len(candidates)} hexes in locality_fit PAs")
    else:
        return no_anchor_response(
            "Please provide a brand/concept, category, anchor location, or hex_id.")

    # ==== Step 3: locality filter (avoid + fit) ====
    if profile:
        candidates = [c for c in candidates if _locality_filter(c["hex_id"], profile)]

    # ==== Step 4: profile-based composite scoring ====
    scored = []
    for c in candidates[:k*3]:
        score, breakdown = _score_hex_by_profile(c["hex_id"], profile) if profile else (c["score"], {})
        if profile and score <= 0 and "excluded" in breakdown:
            continue   # hard filter excluded
        # Blend candidate-source score with profile score
        blended = 0.5 * float(c.get("score", 0)) + 0.5 * score if profile else float(c.get("score", 0))
        scored.append({
            "hex_id": c["hex_id"],
            "score": blended,
            "profile_score": score if profile else None,
            "candidate_score": c.get("score"),
            "breakdown": breakdown if profile else {},
        })
    scored.sort(key=lambda x: -x["score"])
    fused = scored[:k]

    # ==== Step 5: enrich + return ====
    extras = ["walkability_score", "mrt_stations", "population_total", "hdb_blocks"]
    if profile and profile.primary_category:
        extras.append(f"pc_cat_{profile.primary_category}")
    results = enrich_hex_list(fused, extra_fields=extras)
    # Add predicted primary category + gap per hex
    if profile and profile.primary_category:
        for r in results:
            p = hub.xgboost.predict(r["hex_id"], [profile.primary_category])
            a = hub.xgboost.actual(r["hex_id"], [profile.primary_category])
            r["predicted_primary"] = p.get(profile.primary_category, 0.0)
            r["actual_primary"] = a.get(profile.primary_category, 0.0)
            r["primary_gap"] = r["predicted_primary"] - r["actual_primary"]

    expl_parts = []
    if profile:
        expl_parts.append(f"Profiled as '{profile.kind}' ({profile.price_tier} tier)")
    expl_parts.append(f"Candidates: {candidate_source}")
    if profile:
        expl_parts.append(f"Locality fit: {profile.locality_fit}")
        expl_parts.append(f"Scored by {len(profile.signals)} profile signals")
    expl = " · ".join(expl_parts)

    return {
        "status": "ok",
        "results": results,
        "k": k,
        "anchors": anchors or None,
        "brand": brand,
        "category": category,
        "profile": profile.to_dict() if profile else None,
        "candidate_source": candidate_source,
        "explanation": expl,
    }


# ============================================================
# 2. GAP ANALYSIS
# ============================================================
def handle_gap_analysis(params: dict, ctx: Any = None) -> dict:
    """Per-hex predicted - actual per category. If category specified, rank top-gap hexes."""
    category = resolve_category(params)
    k = resolve_k(params, default=20)

    if not category:
        # Default: summarize TOP-GAP hexes across most common categories
        cats = ["cafe_coffee", "hawker_street_food", "health_medical", "education"]
    else:
        cats = [category]

    results_by_cat = {}
    for c in cats:
        pred = hub.xgboost.predict_all_hexes(c)
        actual = hub.xgboost.actual_all_hexes(c)
        if pred.empty or actual.empty:
            continue
        # align on hex_id
        all_hex = hub.features.all_hex_ids()
        pred_vals = pred.reindex(all_hex, fill_value=0.0).values
        act_vals = actual.reindex(all_hex, fill_value=0.0).values
        gap = pred_vals - act_vals
        order = gap.argsort()[::-1][:k]
        top = [{"hex_id": all_hex[i],
                "score": float(gap[i]),
                "predicted": float(pred_vals[i]),
                "actual": float(act_vals[i])} for i in order]
        results_by_cat[c] = enrich_hex_list(top, extra_fields=["walkability_score"])

    if len(cats) == 1:
        return {"status": "ok", "category": cats[0],
                "results": results_by_cat.get(cats[0], []), "k": k,
                "explanation": f"Top {k} hexes ranked by (predicted − actual) for {cats[0]}"}
    return {"status": "ok", "results_by_category": results_by_cat, "categories": cats, "k": k,
            "explanation": f"Top-{k} gap hexes for common categories (no category given)"}


# ============================================================
# 3. ARCHETYPE CLUSTERING
# ============================================================
_ARCHETYPE_CACHE = {}

def handle_archetype_clustering(params: dict, ctx: Any = None) -> dict:
    """k-means on GCN-64; stable across seeds. Return labels + representative hexes per cluster."""
    k = int(params.get("k", 15))
    if k < 2 or k > 30:
        k = 15
    if k in _ARCHETYPE_CACHE:
        return _ARCHETYPE_CACHE[k]

    from sklearn.cluster import KMeans
    import numpy as np
    hub.gcn.load()
    Z = hub.gcn._Z  # pre-normalized
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(Z)
    labels = km.labels_
    hex_ids = hub.gcn._hex_ids

    # Representative hexes = closest to each centroid
    reps = []
    for c in range(k):
        mask = (labels == c)
        if not mask.any():
            continue
        idxs = np.where(mask)[0]
        # Nearest to centroid
        diffs = Z[idxs] - km.cluster_centers_[c]
        dists = (diffs * diffs).sum(axis=1)
        best = idxs[dists.argmin()]
        reps.append({
            "cluster_id": int(c),
            "size": int(mask.sum()),
            "representative_hex": hex_ids[best],
            **hub.features.identity(hex_ids[best]),
        })

    out = {
        "status": "ok", "k": k, "n_hexes": len(labels),
        "clusters": reps,
        "explanation": f"k-means with k={k} on GCN-64 (100% archetype stability in our tests)",
    }
    _ARCHETYPE_CACHE[k] = out
    return out


# ============================================================
# 4. COMPARABLE MARKET
# ============================================================
def handle_comparable_market(params: dict, ctx: Any = None) -> dict:
    """node2vec ∩ gcn — intersection for high-confidence comps."""
    target = resolve_anchor_hex(params, hub)
    if not target:
        return no_anchor_response("Please provide a target hex_id, address, or location.")
    k = resolve_k(params, default=10)

    n2v_top = hub.node2vec.similar(target, k=k*3)
    gcn_top = hub.gcn.similar(target, k=k*3)
    fused = ensemble.intersection([n2v_top, gcn_top], k=k)

    # If intersection is sparse, fall back to RRF
    if len(fused) < k // 2:
        fused = ensemble.rank_fusion_rrf([n2v_top, gcn_top], k=k)

    results = enrich_hex_list(fused, extra_fields=["walkability_score", "population_total"])
    return {"status": "ok", "target": target, "target_info": hub.features.identity(target),
            "k": k, "results": results,
            "explanation": f"Intersection of node2vec + gcn top-{k*3} (falls back to RRF if sparse)"}


# ============================================================
# 5. WHITESPACE ANALYSIS
# ============================================================
def handle_whitespace_analysis(params: dict, ctx: Any = None) -> dict:
    """GCN similarity filtered by brand absence. Approximation: require predicted_cat > threshold but a related category appears."""
    brand = resolve_brand(params) or "unspecified"
    category = resolve_category(params) or "cafe_coffee"   # default if not given
    k = resolve_k(params, default=20)

    # Strategy: find hexes with HIGH predicted count for the brand's category
    # AND LOW actual count (gap). These are where the brand would fit but isn't.
    # (Full brand-level presence data requires joining to places.jsonl; simplified here.)
    pred = hub.xgboost.predict_all_hexes(category)
    actual = hub.xgboost.actual_all_hexes(category)
    if pred.empty:
        return {"status": "error", "message": f"No XGBoost predictor for category: {category}"}
    all_hex = hub.features.all_hex_ids()
    p = pred.reindex(all_hex, fill_value=0.0).values
    a = actual.reindex(all_hex, fill_value=0.0).values

    # Whitespace score: predicted HIGH, actual LOW = biggest opportunity
    score = p - a
    order = score.argsort()[::-1][:k]
    top = [{"hex_id": all_hex[i], "score": float(score[i]),
            "predicted": float(p[i]), "actual": float(a[i])} for i in order]

    results = enrich_hex_list(top, extra_fields=["walkability_score"])
    return {"status": "ok", "brand": brand, "category": category, "k": k, "results": results,
            "explanation": (f"Whitespace = (predicted − actual) {category} "
                            f"(brand='{brand}' — per-brand filter requires places.jsonl join)")}


# ============================================================
# 6. CATEGORY PREDICTION
# ============================================================
def handle_category_prediction(params: dict, ctx: Any = None) -> dict:
    """Per-hex predicted counts. If hex specified → detailed; else top-N by category."""
    anchor = resolve_anchor_hex(params, hub)
    category = resolve_category(params)
    k = resolve_k(params, default=20)

    if anchor:
        preds = hub.xgboost.predict(anchor)
        actuals = hub.xgboost.actual(anchor)
        per_cat = {c: {"predicted": preds.get(c, 0.0),
                       "actual": actuals.get(c, 0.0),
                       "gap": preds.get(c, 0.0) - actuals.get(c, 0.0)}
                   for c in sorted(set(preds) | set(actuals))}
        return {"status": "ok", "hex": anchor, "info": hub.features.identity(anchor),
                "per_category": per_cat,
                "explanation": f"24-category predicted counts for this hex"}

    # No anchor: rank all hexes by predicted count for given category
    if not category:
        return no_anchor_response("Specify a hex or a category.")
    pred = hub.xgboost.predict_all_hexes(category)
    if pred.empty:
        return {"status": "error", "message": f"No predictor for category: {category}"}
    all_hex = hub.features.all_hex_ids()
    p = pred.reindex(all_hex, fill_value=0.0).values
    order = p.argsort()[::-1][:k]
    top = [{"hex_id": all_hex[i], "score": float(p[i]),
            "predicted": float(p[i])} for i in order]
    return {"status": "ok", "category": category, "k": k,
            "results": enrich_hex_list(top),
            "explanation": f"Top {k} hexes by predicted {category} count"}


# ============================================================
# 7. FEATURE QUERY
# ============================================================
def handle_feature_query(params: dict, ctx: Any = None) -> dict:
    """Find hexes matching a feature profile via GCN similarity on a synthetic centroid."""
    # For now: treat the anchor as the profile anchor
    anchor = resolve_anchor_hex(params, hub)
    k = resolve_k(params, default=20)
    if not anchor:
        return no_anchor_response(
            "Provide an example hex matching the profile, or we'll extend feature_query "
            "to synthesize profiles from raw feature constraints.")
    results = hub.gcn.similar(anchor, k=k)
    return {"status": "ok", "anchor": anchor, "k": k,
            "results": enrich_hex_list(results),
            "explanation": f"GCN-64 top-{k} similar to {anchor} (feature-profile retrieval)"}


# ============================================================
# 8. AMENITY DESERT
# ============================================================
def handle_amenity_desert(params: dict, ctx: Any = None) -> dict:
    """Amenity desert = high predicted × low actual × high population."""
    categories = ["hawker_street_food", "convenience_daily_needs", "health_medical"]
    k = resolve_k(params, default=20)

    import numpy as np
    all_hex = hub.features.all_hex_ids()
    pop = hub.features.raw_df().set_index("hex_id").reindex(all_hex).get("population_total")
    pop = pop.fillna(0).values if pop is not None else np.zeros(len(all_hex))

    # Aggregate gap × population across the 3 essentials
    desert_score = np.zeros(len(all_hex))
    for c in categories:
        pred = hub.xgboost.predict_all_hexes(c).reindex(all_hex, fill_value=0.0).values
        act = hub.xgboost.actual_all_hexes(c).reindex(all_hex, fill_value=0.0).values
        gap = np.maximum(0, pred - act)
        # population-weighted deficit
        desert_score += gap * np.log1p(pop)

    order = desert_score.argsort()[::-1][:k]
    top = [{"hex_id": all_hex[i], "score": float(desert_score[i])} for i in order]
    return {"status": "ok", "k": k, "categories": categories,
            "results": enrich_hex_list(top, extra_fields=["population_total", "walkability_score"]),
            "explanation": f"Desert score = Σ_cat max(0, pred−actual) × log(1+population) over {categories}"}


# ============================================================
# 9. FIFTEEN-MIN CITY
# ============================================================
def handle_fifteen_min_city(params: dict, ctx: Any = None) -> dict:
    """Per hex: weighted count of categories present + walkability."""
    import numpy as np
    k = resolve_k(params, default=20)

    df = hub.features.raw_df()
    cat_cols = [c for c in df.columns if c.startswith("pc_cat_")
                and c not in ("pc_cat_hhi", "pc_cat_entropy")]
    presence = (df[cat_cols] >= 1).sum(axis=1).values       # 0..24 categories present
    walk = df["walkability_score"].fillna(0).values if "walkability_score" in df.columns else np.zeros(len(df))
    # Score: 60% presence / 24, 40% walkability / 100
    score = 0.6 * (presence / 24.0 * 100) + 0.4 * walk
    hex_ids = df["hex_id"].astype(str).values
    order = score.argsort()[::-1][:k]
    top = [{"hex_id": hex_ids[i], "score": float(score[i]),
            "categories_present": int(presence[i]),
            "walkability": float(walk[i])} for i in order]
    return {"status": "ok", "k": k,
            "results": enrich_hex_list(top, extra_fields=[]),
            "explanation": ("15-min city score = 60% × (cats present / 24 × 100) "
                            "+ 40% × walkability_score (top-k shown)")}


# ============================================================
# Export mapping name → handler
# ============================================================
HANDLERS = {
    "site_selection":       handle_site_selection,
    "gap_analysis":         handle_gap_analysis,
    "archetype_clustering": handle_archetype_clustering,
    "comparable_market":    handle_comparable_market,
    "whitespace_analysis":  handle_whitespace_analysis,
    "category_prediction":  handle_category_prediction,
    "feature_query":        handle_feature_query,
    "amenity_desert":       handle_amenity_desert,
    "fifteen_minute_city":  handle_fifteen_min_city,
}

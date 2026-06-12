# Merlion Engine Audit — 50 Test Cases
## Real World Engine v0.1 — Test Results & Root Cause Analysis

**Date:** 2026-04-21  
**Engine:** Merlion (localhost:18700 backend, localhost:18701 frontend)  
**Result:** 27/50 pass (54%)  
**Verdict:** Intent routing works (84%). Model execution is broken for 4 of 9 use cases, and the remaining 5 use stale features.

---

## 1. Summary

| Category | Tests | Passed | Failed | Issue |
|---|---|---|---|---|
| Amenity desert | 5 | 2 | 3 | Returns CBD/Orchard instead of HDB estates |
| Site selection | 10 | 9 | 1 | Returns SAME hexes for all categories (no differentiation) |
| Gap analysis | 5 | 3 | 2 | Gaps in CBD (already oversaturated), some empty results |
| Whitespace | 5 | 2 | 3 | Routing confusion between whitespace and gap_analysis |
| Comparable market | 5 | 3 | 2 | Routing: "similar to X" sometimes routes to site_selection |
| Category prediction | 5 | 0 | 5 | **ALL EMPTY** — handler broken |
| 15-minute city | 5 | 5 | 0 | Works correctly |
| Archetype clustering | 5 | 0 | 5 | **ALL EMPTY** — handler broken |
| Feature query | 5 | 0 | 5 | **ALL EMPTY** — handler broken |

---

## 2. Critical Issue #1: Food Deserts Return Orchard/CBD

**Query:** "find food deserts in Singapore"  
**Expected:** Dense HDB estates with low F&B per capita (Woodlands East, Sengkang, Jurong West)  
**Got:** Novena (score 1569), Orchard (score 1221), Orchard (score 1008)

**Root cause:** The `amenity_desert` handler scores by absolute predicted-vs-actual gap. Commercial areas have the highest predicted counts (because XGBoost sees high features → predicts many places). The gap = predicted - actual is large in absolute terms, even though these areas already have 700-1,200 places.

**Fix needed:** Score by `gap / population_total` (per-capita need), not absolute gap. A hex with 42K residents and gap of 200 is more important than a hex with 0 residents and gap of 1,200. Our enriched hex-8 already has `saturation_fnb` and `gap_fnb` computed correctly with population_total denominator.

---

## 3. Critical Issue #2: Site Selection Returns Same Results for All Categories

**Queries returning identical top-3 (Rochor, Kallang, Geylang):**
- McDonald's, luxury restaurant, gym, Watsons, pet shop, bubble tea, tuition centre, coworking, 7-Eleven

**Only exception:** Starbucks → Downtown Core, Orchard (correctly uses brand anchor locations)

**Root cause:** The `site_selection` handler uses node2vec embeddings to find hexes similar to existing brand locations. For generic queries without a recognized brand, it falls back to a generic "good commercial location" profile — which is always the same dense commercial hexes (Rochor, Kallang, Geylang).

**What's missing:**
1. **Category-aware selection** — "open a gym" should filter for hexes where pull_residential is high and saturation_fitness is low. Currently the model doesn't use category-specific demand signals.
2. **Demand-match scoring** — our enriched features have `demand_match` per category, `saturation_own_category`, and `synergy_*` scores that should feed into ranking.
3. **Brand-specific anchors** — only works for brands in the training data (Starbucks, FairPrice). Generic categories need a different path.

**Fix needed:** For non-brand queries, use the enriched hex-8 features:
```python
# Instead of node2vec similarity, use:
score = pull_{primary_demand} × (1 - saturation_{category}) × transit_score × ecosystem_completeness
# Filtered by: population_total > threshold, correct archetype
```

---

## 4. Critical Issue #3: Three Use Cases Return Empty

### category_prediction (0/5)
All queries return `{"results": []}`.

**Likely cause:** The XGBoost model expects specific input format or the handler can't resolve location names ("Raffles Place", "Woodlands") to hex IDs. The entity extraction gets `{"category": "cafe", "location": "Raffles Place"}` but the handler doesn't have a location→hex resolver.

### archetype_clustering (0/5)
All queries return empty.

**Likely cause:** K-means clustering runs on-demand but may need specific model artifacts (cluster centers, scaler) that aren't loaded. Or the handler expects features in a format that doesn't match current data.

**Note:** We already computed archetypes in the enriched hex-8 stack (6 types, stored in `archetype` column). The handler should just look up the precomputed archetype, not re-cluster.

### feature_query (0/5)
Queries like "find high-density transit hubs" and "areas with most elderly" return empty.

**Likely cause:** The handler needs to parse natural language into feature filters (e.g., "high elderly" → `pct_elderly > 0.2`). The current implementation likely can't do this parsing, or the LLM entity extraction doesn't produce filter criteria.

**Fix needed:** Wire feature_query to DuckDB queries on the enriched parquets. Let the LLM generate SQL-like filter conditions:
```sql
SELECT * FROM hex8_final WHERE pct_elderly > 0.2 ORDER BY pct_elderly DESC LIMIT 20
```

---

## 5. Critical Issue #4: Gap Analysis Returns Commercial Areas

**Query:** "find cafe gaps in Singapore"  
**Got:** Downtown Core (gap 56.8), Orchard (gap 52.9), Orchard (gap 37.8)

These are the MOST cafe-dense areas in Singapore. The "gap" is that the XGBoost model predicts even MORE cafes should exist there (because features are extremely high). This is technically correct from the model's perspective but useless for decision-making.

**Root cause:** The gap model was trained to predict absolute category counts. It predicts highest where features are highest. The gap = predicted - actual is largest in already-dense areas.

**Fix needed:** Use the saturation model we built:
- `saturation_cafe < 0.5` AND `population_total > 5000` = genuine undersupply
- Rank by `gap_cafe × population_total` = population-weighted need
- Filter out hexes where saturation > 2.0 (already oversupplied)

---

## 6. What Works Well

### Intent routing (84% correct)
The NL → use case classification is solid. Rule-based + LLM entity extraction correctly identifies:
- "food desert" → amenity_desert (0.95 confidence)
- "open a Starbucks" → site_selection (0.95)
- "comparable to Orchard" → comparable_market (0.95)
- "15-minute city" → fifteen_minute_city (0.95)

The 16% misrouting is mostly "similar to X" being ambiguous between comparable_market and site_selection.

### 15-minute city (5/5)
Returns Outram, Rochor — mature central areas with high walkability. Correctly identifies areas where all amenities are within walking distance.

### Comparable market (when correctly routed)
- Orchard comparables → Newton, other Orchard hexes (correct — premium commercial)
- Tanjong Pagar → Downtown Core, Outram (correct — CBD fringe)
- Punggol → other Punggol hexes (correct but too self-referential — should find Sengkang, Tengah)

### Branded site selection
- Starbucks → Downtown Core, Orchard (correct — follows existing Starbucks locations)
- FairPrice → Toa Payoh, Serangoon, Yishun (correct — HDB estates matching FairPrice profile)

---

## 7. Models Currently in Use

| Model | Use cases | Data it uses | Issue |
|---|---|---|---|
| **node2vec** | site_selection, comparable_market, whitespace | Hex-9 v10 embeddings (old 471 features) | No category awareness |
| **GCN (64d)** | archetype, whitespace, feature_query | Hex-9 graph embeddings | Handlers broken |
| **XGBoost** | gap_analysis, category_prediction, amenity_desert | Hex-9 features | Scores by absolute gap, not per-capita |
| **UMAP** | feature_query (augment) | 2D projection | Handler broken |
| **raw_features** | fifteen_minute_city | Hex-9 walkability columns | Works correctly |

---

## 8. Recommended Fixes (prioritized)

### P0: Wire enriched hex-8 features into handlers
The biggest win. Our hex-8 (628 features) has saturation, demand pull, total population, archetypes, GTFS, network walk — everything the old models lack. Replace model-based scoring with feature-based scoring for:

- **amenity_desert:** `gap_{category} / population_total` ranked descending, filtered to pop > 5K
- **gap_analysis:** Same, using saturation < 0.5 filter
- **site_selection (generic):** `demand_match × (1 - saturation) × transit_score`, filtered by archetype
- **archetype_clustering:** Return precomputed `archetype` column from hex-8
- **feature_query:** DuckDB query on hex-8 parquet with LLM-generated filters

### P1: Fix category-aware site selection
For generic queries (not brand-specific), use the demand-match lookup table:
- Cafe → high pull_office + pull_transit, low saturation_cafe
- Gym → high pull_residential, low saturation_fitness
- Luxury restaurant → high pull_hotel, high hdb_median_psf
- Tuition → high pull_school, near schools_primary

### P2: Fix 3 broken handlers
- `category_prediction`: Wire to XGBoost with location resolver (name → hex-8 ID)
- `archetype_clustering`: Return precomputed hex-8 archetype + profile
- `feature_query`: DuckDB passthrough with LLM-generated WHERE clause

### P3: Improve comparable_market
- Currently too self-referential (Punggol returns Punggol)
- Should exclude same planning area, find similar archetypes elsewhere

---

## 9. Full Test Results

### Amenity Desert

| # | Query | Route | Conf | Top result | Score | Issue |
|---|---|---|---|---|---|---|
| 01 | find food deserts | amenity_desert | 0.95 | Novena, Orchard | 1569 | **CBD in desert** |
| 02 | grocery stores missing | gap_analysis | 0.90 | — | EMPTY | Wrong route + empty |
| 03 | no clinics nearby | amenity_desert | 0.92 | Novena, Orchard | 1569 | Returns commercial areas |
| 04 | elderly lack healthcare | amenity_desert | 0.93 | Novena, Orchard | 1569 | Returns commercial areas |
| 05 | no parks for families | amenity_desert | 0.82 | Novena, Orchard | 1569 | Returns commercial areas |

### Site Selection

| # | Query | Top result | Score | Issue |
|---|---|---|---|---|
| 06 | new Starbucks | Downtown Core, Orchard | 33.2 | ✓ Correct |
| 07 | new McDonald's | Rochor, Kallang, Geylang | 6.3 | Generic fallback |
| 08 | luxury restaurant | Rochor, Kallang, Geylang | 6.3 | Same as McDonald's! |
| 09 | gym | Rochor, Kallang, Geylang | 6.3 | Same |
| 10 | Watsons | Rochor, Kallang, Geylang | 6.3 | Same |
| 11 | pet shop | Rochor, Kallang, Geylang | 6.3 | Same |
| 12 | bubble tea | Rochor, Kallang, Geylang | 6.3 | Same |
| 13 | tuition centre | Rochor, Kallang, Geylang | 6.3 | Same |
| 14 | coworking | Rochor, Kallang, Geylang | 6.3 | Same |
| 15 | 7-Eleven | Rochor, Kallang, Geylang | 6.3 | Same |

### Gap Analysis

| # | Query | Top result | Score | Issue |
|---|---|---|---|---|
| 16 | hawker missing | Outram, Geylang, Kallang | 73.6 | CBD-heavy |
| 17 | more restaurants | Orchard, Outram | 223.9 | Already oversaturated |
| 18 | cafe gaps | Downtown Core, Orchard | 56.8 | Already oversaturated |
| 19 | pharmacies | — | EMPTY | Broken |
| 20 | bakery gaps | Orchard, Changi | 17.7 | Not new towns |

### Whitespace

| # | Query | Route | Top result | Issue |
|---|---|---|---|---|
| 21 | FairPrice | site_selection | Toa Payoh, Serangoon | ✓ Correct |
| 22 | Don Don Donki | whitespace | Downtown Core, Orchard | CBD not suburban |
| 23 | KFC missing | gap_analysis | Woodlands, Serangoon | Misrouted |
| 24 | Guardian | gap_analysis | — | EMPTY |
| 25 | Decathlon | site_selection | Rochor, Kallang | Generic fallback |

### Comparable Market

| # | Query | Top result | Issue |
|---|---|---|---|
| 26 | like Orchard | Newton, Orchard | ✓ Correct |
| 27 | like Tiong Bahru | Bukit Merah (score 0) | Misrouted to site_selection |
| 28 | like Tanjong Pagar | Downtown Core, Outram | ✓ Correct |
| 29 | like Jurong East | Jurong East (score 0) | Misrouted to site_selection |
| 30 | like Punggol | Punggol, Punggol | Too self-referential |

### Category Prediction (ALL BROKEN)

| # | Query | Result |
|---|---|---|
| 31-35 | All 5 queries | EMPTY (handler broken) |

### 15-Minute City (ALL CORRECT)

| # | Query | Top result | Score |
|---|---|---|---|
| 36-40 | All 5 queries | Outram (98.8), Rochor (98.0) | ✓ Correct |

### Archetype / Feature Query (ALL BROKEN)

| # | Query | Result |
|---|---|---|
| 41-50 | All 10 queries | EMPTY (handlers broken) |

---

## 10. Data Mismatch

The engine uses hex-9 v10 features (471 columns). Our enriched stack has:
- Hex-9: 603 features (network walk, GTFS, saturation, nightlights, WorldPop)
- Hex-8: 628 features (+ archetypes, composites, proxies, internal structure)
- Places: 114 features (competition, anchors, synergy, survivability)

None of these enrichments are used by the engine. Wiring them in would fix most issues.

---

*Audit v1.0 — 2026-04-21*
*Next: rewire handlers to use enriched hex-8/hex-9 features, fix 3 broken handlers, add category-aware site selection*

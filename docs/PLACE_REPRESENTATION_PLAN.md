# Place Representation — SGP Digital Atlas
## From 9 fields to 73 features per place

**Status:** Plan — ready to build
**Date:** 2026-04-18
**Depends on:** hex-9 (579 features), hex-8 (596 features) — both finalized

---

## The Problem

Current place data is thin:
```
{id, name, address, lat, lng, main_category, place_type, price_tier, segment}
```

9 fields about **what the place IS**, nothing about **where it sits, who it serves, what it competes with, or whether it fits its context.**

A Starbucks in Raffles Place and a Starbucks in Tuas industrial park have identical records. But they serve completely different demand, face different competition, have different survival odds. The place representation should capture this.

---

## Architecture: 6 Layers → 73 features per place

### Layer 1: Intrinsic (~10 features)
What the place IS — from the raw record.

| Feature | Source | Type |
|---------|--------|------|
| `category` | main_category | categorical |
| `sub_category` | place_type | categorical |
| `price_tier` | price_tier | ordinal (1-5) |
| `is_branded` | segment == 'branded' | bool |
| `brand_name` | segment field | string |
| `has_phone` | phone != null | bool |
| `has_website` | website != null | bool |
| `confidence` | confidence score | float |
| `source` | source field | categorical |
| `category_encoded` | one-hot or ordinal | numeric |

### Layer 2: Micro-context (~15 features)
What's within **100-300m** — the immediate neighborhood a customer sees.

| Feature | Computation | Why it matters |
|---------|-------------|----------------|
| `same_category_100m` | Count same main_category within 100m | Direct competition intensity |
| `same_category_300m` | Count same main_category within 300m | Extended competition |
| `same_brand_300m` | Count same brand within 300m | Cannibalization risk |
| `complementary_300m` | Count known-complementary categories within 300m | Cross-traffic potential |
| `anchor_count_300m` | MRT exits + hawker centres + malls within 300m | Footfall generators |
| `footfall_proxy_300m` | Transit taps + place density within 300m | Pedestrian traffic estimate |
| `price_tier_neighbors_mean` | Mean price tier of all places within 300m | Price positioning context |
| `price_tier_neighbors_std` | Std of price tiers within 300m | Price diversity (0 = homogeneous) |
| `category_diversity_300m` | Unique categories within 300m | Mono-cluster vs mixed-use |
| `nearest_competitor_m` | Distance to closest same-category place | Competitive proximity |
| `nearest_anchor_m` | Distance to closest MRT/hawker/mall | Demand magnet proximity |
| `street_level_proxy` | Is nearest road arterial or residential? | Visibility/frontage proxy |
| `cluster_size` | Total places within 300m | Location intensity |
| `branded_pct_300m` | Branded / total within 300m | Chain penetration locally |
| `density_band` | sp/mo/ur/su/ru classification | Urban density context |

### Layer 3: Hex context (~30 features)
Inherited from the hex-9/hex-8 the place sits in. **Selected, not all 579** — the subset relevant to commercial viability.

**Population & Demand:**
- `population_total` — total people (residents + workers + students)
- `pct_elderly` — age skew
- `nonresident_share` — worker-dominant vs residential
- `daytime_intensity` — net inflow ratio

**Demand Pull:**
- `pull_office` — office lunch/services demand
- `pull_residential` — daily needs demand
- `pull_transit` — commuter impulse demand
- `pull_hotel` — tourist spend demand
- `pull_total_pop` — combined demand from all people

**Supply Fit:**
- `saturation_{category}` — is this category oversupplied here?
- `gap_{category}` — expected minus actual for this category

**Transit Access:**
- `nwalk_mrt_m` — network walk to nearest MRT
- `nwalk_bus_m` — network walk to nearest bus
- `gtfs_headway_am_min` — best bus/MRT frequency
- `transit_daily_taps` — daily transit usage

**Competition Landscape:**
- `pc_cat_{same_category}` — how many same-category in this hex
- `pc_cat_entropy` — category diversity
- `pc_total` — total commercial intensity

**Cost Proxy:**
- `hdb_median_psf` — property price (rent proxy)

### Layer 4: Demand-match score (~8 features)
**Does this place fit its location?** The novel layer.

| Feature | Formula | Example |
|---------|---------|---------|
| `demand_match` | Category-demand alignment score | Cafe in high office-pull → 0.9; Cafe in zero-office residential → 0.5 |
| `price_fit` | Price tier vs area income proxy | Premium cafe in premium area → 1.0; Budget food in premium area → 0.3 |
| `temporal_fit` | Category hours vs area demand rhythm | Breakfast in CBD (high AM taps) → 1.0; Bar in industrial (zero night pop) → 0.1 |
| `segment_alignment` | Category vs dominant population segment | Tuition where kids >15% → 0.9; Tuition where elderly >25% → 0.2 |
| `synergy_capture` | Is the relevant synergy score high? | Cafe with high synergy_cafe_office → 0.8 |
| `gap_fill_score` | Does this place fill a supply gap? | Clinic where gap_health > 5 → 0.9; 15th restaurant where sat > 3 → 0.1 |
| `accessibility_score` | Reachability by the mode customers use | Transit-dependent near MRT → 0.9 |
| `survivability_index` | Composite: demand_match × (1 - saturation) × accessibility | Overall viability score |

**Demand-match lookup table (category → which pull matters):**

| Category | Primary pull | Secondary pull |
|----------|-------------|----------------|
| Cafe & Coffee | pull_office | pull_transit |
| Restaurant | pull_residential | pull_hotel |
| Fast Food / QSR | pull_transit | pull_residential |
| Convenience | pull_transit | pull_residential |
| Health & Medical | pull_residential | pull_total_pop |
| Education / Tuition | pull_school | pull_residential |
| Beauty & Personal Care | pull_residential | pull_office |
| Bar & Nightlife | pull_hotel | pull_office |
| Shopping & Retail | pull_transit | pull_hotel |
| Fitness & Recreation | pull_residential | pull_office |
| Hawker & Street Food | pull_residential | pull_transit |
| Bakery & Pastry | pull_transit | pull_residential |

### Layer 5: Competitive position (~10 features)
Not just "how many competitors" but "what's my strategic position."

| Feature | What it measures |
|---------|-----------------|
| `competitive_radius_m` | At what distance does competition affect this place? (200m for convenience, 2km for specialty) |
| `market_share_proxy` | 1 / n_competitors_in_radius |
| `differentiation_score` | How different from competitors? (different tier, sub-category, branded vs independent) |
| `cluster_position` | Centre or edge of category cluster? (centre = footfall, edge = less competition) |
| `brand_penetration_local` | For branded: what % of local market is this brand? |
| `substitution_risk` | Count of SIMILAR (not same) category places (bubble tea competes with cafe) |
| `anchor_dependency` | % of likely traffic from a single anchor (risky if anchor closes) |
| `co_tenancy_score` | Benefits from specific neighbors? (pharmacy next to clinic) |
| `isolation_score` | Alone in category within 500m? (good for essentials, bad for destination retail) |
| `category_lifecycle` | Category growing/stable/declining locally? |

### Layer 6: Embedding (~32-64d)
Dense vector for ML tasks.

- Concatenate numeric features from layers 1-5
- Normalize to [0,1]
- PCA or autoencoder to 32-64 dimensions
- Enables: similarity search, clustering, anomaly detection, recommendation

---

## Computation Architecture

```
For each of 174,713 places:
  1. Look up hex-9 and hex-8 → inherit ~30 selected features
  2. Spatial query: nearby places within 300m (KD-tree) → micro-context ~15 features
  3. Compute demand-match scores from hex features → ~8 features
  4. Compute competitive position from neighbor query → ~10 features
  5. Combine intrinsic features → ~10 features
  = ~73 features per place

  6. (Optional) Embed to 32-64d dense vector
```

**Performance:** KD-tree on 175K points, each querying ~50 neighbors within 300m. Total: ~8.7M distance calculations. Estimated runtime: 2-5 minutes.

---

## What This Enables

| Use case | Current | With place representation |
|----------|---------|--------------------------|
| Where to open a cafe? | Hex-level gap score | Specific lat/lng with demand-match + competitive position + survivability |
| Is this place at risk? | Nothing | Survivability index from saturation + demand-mismatch + isolation |
| Find similar locations | Manual | Embedding similarity search across 175K places |
| What's wrong here? | Descriptive stats | Binding constraint: "low demand-match: price tier mismatch" |
| Rate this location 1-10 | Nothing | Composite score with explainable sub-scores |
| Portfolio analysis | Nothing | All outlets of a brand scored + benchmarked |

---

## Co-location Synergy Pairs (SGP-specific)

Used in Layer 5 co_tenancy_score:

| Pair | Synergy name | Why it works | SGP example |
|------|-------------|--------------|-------------|
| Cafe + Office | synergy_cafe_office | Workers need coffee | Raffles Place Starbucks |
| Grocery + HDB | synergy_grocery_residential | Daily essentials walk | NTUC in estate mall |
| Convenience + MRT | synergy_conv_transit | Commuter impulse | 7-Eleven at MRT exit |
| Restaurant + Hotel | synergy_rest_hotel | Tourist dining | TST restaurant row |
| Gym + Cafe/Juice | synergy_lifestyle | Health-conscious cluster | Tanjong Pagar gym + poke |
| Pharmacy + Clinic | synergy_health | Medical ecosystem | HDB void deck medical row |
| Bar + Restaurant | synergy_nightlife | Pre/post dining + drinks | Clarke Quay |
| Tuition + School | synergy_education | After-school economy | Bukit Timah tuition belt |
| Bank + Office | synergy_financial | Business services | Central bank row |
| Bakery + MRT | synergy_morning | Morning commute routine | Ya Kun at MRT |
| Hawker + Wet Market | synergy_food_ecosystem | Morning market → lunch flow | Tiong Bahru Market |
| Bubble Tea + MRT | synergy_bbt_transit | Youth impulse | KOI/LiHO at every MRT |
| Kopitiam + HDB | synergy_social_hub | Neighbourhood social anchor | Every estate |

---

## Substitution Risk Map

Used in Layer 5 substitution_risk — categories that compete for same demand:

| Category | Substitutes |
|----------|-------------|
| Cafe & Coffee | Bakery, Hawker (kopi stalls), Bubble Tea |
| Restaurant | Hawker & Street Food, Fast Food |
| Fast Food / QSR | Hawker, Convenience (ready meals) |
| Convenience | Supermarket, Provision shop |
| Supermarket | Wet market, Convenience |
| Health & Medical | Pharmacy (for minor ailments) |
| Fitness & Recreation | Parks (free alternative) |
| Beauty & Personal Care | (low substitution — specialized) |
| Education / Tuition | (low substitution — specialized) |

---

## Data Requirements

**All data already exists.** No new API calls needed.

| Input | Source | Status |
|-------|--------|--------|
| Place records | sgp_places_v2.jsonl (174,713) | ✓ Ready |
| Hex-9 features | hex9_final.parquet (579 features) | ✓ Ready |
| Hex-8 features | hex8_final.parquet (596 features) | ✓ Ready |
| Place coordinates | lat/lng in places JSONL | ✓ Ready |
| Road network | roads.geojson (551K segments) | ✓ Ready (for street-level proxy) |

---

## Output

```
place_features_v1.parquet
  174,713 places × ~73 features
  + optional 32d embedding vector

place_features_v1.jsonl
  One JSON object per line, streamable
```

---

*Plan version: v1 — 2026-04-18*
*Next: build script, validate on 5 sample places across archetypes*

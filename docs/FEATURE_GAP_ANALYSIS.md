# Feature Gap Analysis — Plan vs Built

**Date:** 2026-03-29
**Plan:** `~/misc/sgp_subzone_feature_plan.md`
**Built:** `model/embeddings_v4/feature_matrix.parquet` (332 × 351)

---

## Executive Summary

The plan specifies ~131 carefully designed intrinsic + neighbor features for 332 subzones. We built 351 features — but from a different angle. The plan emphasizes **neighbor context and contrast** (70 features). We emphasize **micrograph structure** (156 features). Neither alone is complete. Combined they'd create ~435 features that capture both the internal character AND the neighborhood context of every subzone.

**Biggest gaps:** Neighbor ego-graph (55 planned, 1 built), boundary permeability (6 planned, 0 built), growth signals (4 planned, 0 built), multi-scale rings (10 planned, 0 built).

**Biggest surplus:** Micrograph features (156 built, 0 planned), demand/gravity (26 built, 0 planned), cross-boundary flows (4 built, 0 planned).

---

## Detailed Comparison

### Phase 2: Intrinsic Features

#### 2.1 Demographics (Plan: 9 → Built: 8 → Coverage: 89%)

| Plan Feature | Built? | Our Feature | Notes |
|---|---|---|---|
| `pop_total` | YES | `population` | |
| `pop_density_per_sqkm` | YES | `pop_density` | |
| `pop_pct_age_0_14` | NO | — | Have census data on server but not computed |
| `pop_pct_age_15_34` | NO | — | Same |
| `pop_pct_age_35_54` | NO | — | Same |
| `pop_pct_age_55_plus` | PARTIAL | `elderly_pct` | Only 55+, not 4-band breakdown |
| `avg_household_size` | NO | — | Census data exists |
| `pct_hdb_dwelling` | YES | `hdb_*_room_flats_pct` (5 features) | More detailed than plan |
| `median_income_band` | YES | `median_income` | Continuous, not ordinal |

**Gap:** Age band distribution (4 features). Data exists in `data/demographics/` but not aggregated.

#### 2.2 Land Use (Plan: 8 → Built: 10 → Coverage: 125%)

| Plan Feature | Built? | Our Feature |
|---|---|---|
| `pct_zone_residential` | YES | `lu_residential_pct` |
| `pct_zone_commercial` | YES | `lu_commercial_pct` |
| `pct_zone_industrial` | YES | `lu_industrial_pct` |
| `pct_zone_mixed` | YES | `lu_mixed_use_pct` |
| `pct_zone_greenspace` | YES | `lu_nature_pct` + `lu_open_space_pct` |
| `avg_gpr` | YES | `avg_gpr` |
| `building_coverage_ratio` | YES | `building_density` |
| `hdb_pct_of_residential` | APPROX | `hdb_*_pct` features | Different granularity |

**Extra built:** `lu_entropy`, `lu_institutional_pct`, `lu_transport_pct`, `lu_reserve_pct`, `lu_other_pct`. Exceeds plan.

#### 2.3 Commercial Composition (Plan: 12 → Built: ~30+ → Coverage: 250%)

| Plan Feature | Built? | Our Feature |
|---|---|---|
| `poi_count_total` | YES | `total_places`, `n_places` |
| `poi_density_per_sqkm` | YES | `place_density` |
| `poi_count_{category}` | YES | `n_restaurant`, `n_cafe_coffee`, ... (24 categories) |
| `poi_ratio_{category}` | NO | — | Have counts, not ratios |
| `hhi_concentration` | YES | `brand_hhi` |
| `shannon_entropy` | YES | `category_entropy`, `segment_entropy` |
| `anchor_tier1_count` | INDIRECT | Micrograph T1 stats per category |
| `anchor_tier2_count` | INDIRECT | Micrograph T2 stats per category |
| `anchor_tier3_count` | INDIRECT | Micrograph T3 stats per category |
| `anchor_tier4_count` | INDIRECT | Micrograph T4 stats per category |
| `chain_ratio` | YES | `chain_indie_ratio`, `branded_pct` |
| `fnb_density_per_sqkm` | YES | `fnb_coverage_ratio`, `food_drink_pct` |

**Extra built:** 156 micrograph features (context vectors, competitive pressure, walk times, density bands, T1 diversity per 12 categories). Also: 24 V2 category counts, price tier distribution, brand entropy, ACRA churn. Far exceeds plan.

**Gap:** Explicit anchor tier counts as simple features (not per-category micrograph). The plan's simplicity has value — a single `anchor_tier1_count` is more interpretable than 12 category-specific `mg_*_cv_transit` features.

#### 2.4 Accessibility (Plan: 10 → Built: 9 → Coverage: 90%)

| Plan Feature | Built? | Our Feature |
|---|---|---|
| `mrt_station_count` | YES | `mrt_stations_1km` |
| `mrt_line_count` | **NO** | — | Not computed |
| `has_interchange` | **NO** | — | High value, easy to add |
| `bus_stop_count` | YES | `bus_stop_count_1km` |
| `bus_stop_density` | YES | `bus_density` |
| `dist_to_nearest_mrt_m` | YES | `dist_nearest_mrt` |
| `dist_to_cbd_m` | **NO** | — | Important positioning feature |
| `dist_to_nearest_regional_center_m` | **NO** | — | Jurong, Tampines, Woodlands |
| `road_density_km_per_sqkm` | YES | `road_density` |
| `expressway_access` | **NO** | — | Binary, high signal |

**Gap:** 5 features. `dist_to_cbd_m` and `has_interchange` are particularly high-value — they position each subzone relative to Singapore's commercial gravity.

#### 2.5 Property Market (Plan: 6 → Built: 4 → Coverage: 67%)

| Plan Feature | Built? | Our Feature |
|---|---|---|
| `hdb_resale_median_psm` | YES | `median_hdb_psf` |
| `hdb_resale_yoy_change` | YES | `hdb_price_yoy` |
| `hdb_transaction_volume` | **NO** | — | Data exists on server |
| `private_median_psf` | **NO** | — | Data exists on server |
| `private_yoy_change` | **NO** | — | Data exists on server |
| `private_transaction_volume` | **NO** | — | Data exists on server |

**Gap:** 4 features. Transaction volume is a proxy for market liquidity. Private PSF captures the affluent segment. Data exists in `data/new_datasets/`.

#### 2.6 Amenity (Plan: 11 → Built: 9 → Coverage: 82%)

| Plan Feature | Built? | Our Feature |
|---|---|---|
| `school_primary_count` | INDIRECT | `schools_within_1km` (not by level) |
| `school_secondary_count` | **NO** | — |
| `school_tertiary_count` | **NO** | — |
| `enrichment_center_count` | YES | `n_education` (includes tuition centres) |
| `clinic_count` | YES | `chas_clinic_count` |
| `hospital_within_2km` | **NO** | `dist_nearest_*` but not binary |
| `park_area_sqkm` | PARTIAL | `green_ratio` |
| `park_pct_of_area` | YES | `green_ratio` |
| `sports_facility_count` | YES | `n_fitness_recreation` |
| `worship_place_count` | YES | `n_religious` |
| `cc_count` | **NO** | — | Community centres |

**Gap:** School by level, community centre count, hospital binary. The plan correctly distinguishes primary vs secondary schools — a preschool-heavy subzone has different demand than a JC-heavy one.

#### 2.7 Growth Signals (Plan: 4 → Built: 0 → Coverage: 0%)

| Plan Feature | Built? | Notes |
|---|---|---|
| `bto_units_upcoming` | **NO** | High value — predicts future population |
| `new_mrt_station_by_2030` | **NO** | High value — predicts future transit access |
| `gls_site_nearby` | **NO** | Government land sales = development signal |
| `enbloc_activity_3yr` | **NO** | Redevelopment signal |

**Gap:** ALL 4 missing. These are forward-looking features — they predict where demand WILL be, not where it IS. The plan correctly identifies this as a distinct signal class. Would need manual data curation.

---

### Phase 3: Neighbor Context Features

#### 3.2 Ego-Graph Summaries (Plan: 55 → Built: 1 → Coverage: 2%)

| Plan Feature Pattern | Built? | Notes |
|---|---|---|
| `nbr_mean_{X}` for 11 features | **NO** | Weighted neighbor averages |
| `nbr_max_{X}` for 11 features | **NO** | Strongest neighbor signal |
| `nbr_std_{X}` for 11 features | **NO** | Neighbor diversity |
| `contrast_{X}` for 11 features | **NO** | Self minus neighbor mean |
| `rank_{X}` for 11 features | **NO** | Rank among self + neighbors |

**Gap:** 54/55 features missing. This is the plan's most important contribution. The contrast features (`self_poi_density - nbr_mean_poi_density`) directly answer "am I over or under-served relative to my neighbors?" — which is the core question for gap analysis.

We have `adjacency_degree` (≈ nbr_count) and cross-boundary flows (4 features), but not the systematic ego-graph treatment.

#### 3.3 Boundary Profile (Plan: 6 → Built: 1 → Coverage: 17%)

| Plan Feature | Built? | Notes |
|---|---|---|
| `nbr_count` | YES | `adjacency_degree` |
| `pct_boundary_soft` | **NO** | Requires boundary classification |
| `pct_boundary_hard` | **NO** | Expressway/water boundaries |
| `avg_permeability` | **NO** | Weighted permeability score |
| `max_neighbor_poi_density` | **NO** | Strongest commercial neighbor |
| `dominant_neighbor_name` | **NO** | For debugging/interpretation |

**Gap:** 5/6 features. The plan's boundary classification (soft/expressway/water/park/rail) and permeability scoring is a novel insight — not all borders are equal. An expressway separates neighborhoods more than a street does.

#### 3.4 Multi-Scale Rings (Plan: ~10 → Built: 0 → Coverage: 0%)

| Plan Feature | Built? | Notes |
|---|---|---|
| Ring 2 (2-hop) aggregates | **NO** | Neighbors of neighbors |
| Planning area aggregates | **NO** | Macro positioning |

**Gap:** ALL missing. The plan correctly notes that different businesses compete at different scales — convenience stores at ring 1, malls at ring 2+. Our model treats all competition as single-scale.

---

## Coherence Assessment

### Where plan and built are COHERENT:
- **Demographics, land use, commercial composition** — strong overlap, we often exceed the plan
- **Transit and amenity proximity** — well covered with slight gaps
- **Property market** — partially covered, data exists to fill gaps

### Where they DIVERGE:
- **Plan emphasizes neighbor context; we emphasize micrograph structure** — these are complementary views of the same reality. The plan asks "how does this subzone compare to its neighbors?" while micrographs ask "how do individual places relate to nearby anchors?"
- **Plan has forward-looking signals; we're entirely backward-looking** — growth signals (BTO, new MRT) are absent from our model
- **Plan uses permeability-weighted adjacency; we use unweighted** — the plan's insight that expressway borders matter is missing

### Where the built EXCEEDS the plan:
- **156 micrograph features** — the plan didn't envision per-place spatial graphs at all
- **26 demand/gravity features** — buzz, synergy, tension, time-of-day demand
- **ACRA business survival** — churn rate, average business age
- **Cross-boundary micrograph flows** — 81K anchor connections between subzones

---

## Recommendation

Merge the two approaches. The plan's neighbor context features (Phase 3) are the highest-impact addition to our existing model:

| Priority | Addition | Features | Effort | Impact |
|---|---|---|---|---|
| **P0** | Ego-graph neighbor features | +55 | 3-4 hrs | Enables gap detection ("am I undersupplied vs neighbors?") |
| **P0** | Contrast features | (included in +55) | — | Core of gap analysis |
| **P1** | Boundary permeability | +6 | 2-3 hrs | Correct neighbor weighting |
| **P1** | Missing accessibility (CBD dist, interchange) | +5 | 1 hr | Macro positioning |
| **P2** | Multi-scale rings | +10 | 2 hrs | Regional competition |
| **P2** | Growth signals (BTO, new MRT) | +4 | 1-2 hrs (manual data) | Forward prediction |
| **P3** | Missing property (private PSF, volumes) | +4 | 1 hr | Market depth |
| **P3** | Age band breakdowns | +4 | 30 min | Demand segmentation |

**Current: 351 features → Target: ~435 features.** The neighbor context addition alone (P0) would be the most impactful single improvement to the model.

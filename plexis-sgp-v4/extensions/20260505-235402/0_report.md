# Atlas Extender Report

**Use case:** Where should we open a new specialty cafe targeting young professionals in Singapore?
**Generated:** 20260505-235402
**Atlas version (base):** 4.8.0
**New version:** 4.8.1

## Summary

| | Count |
|---|---|
| Proposed | 10 |
| KEEP | 2 |
| REVISE | 3 |
| REJECT | 5 |
| **Successfully added** | **5** |
| Build-failed | 0 |

## Use Case Spec

```json
{
  "use_case": "Identify optimal locations for a new specialty cafe targeting young professionals in Singapore",
  "target_variable": "location_suitability_score",
  "decision_type": "ranking",
  "scale": "hex9",
  "key_concepts": [
    "young professional population density",
    "office and coworking space proximity",
    "existing cafe competition saturation",
    "foot traffic patterns",
    "income levels and spending power",
    "public transport accessibility",
    "lunch and after-work activity zones"
  ],
  "constraints": [
    "avoid areas with high specialty cafe density",
    "prefer areas with commercial or mixed-use zoning",
    "minimum daytime population threshold"
  ],
  "evaluation_metric": "composite score combining target demographic density, competition gap, and accessibility metrics",
  "decision_horizon_months": 12,
  "stakeholder": "cafe business owner or F&B investment team"
}
```

## Per-feature decisions

### ✅ `mixed_use_cafe_appeal` — KEEP  *(priority 1)*

**Description:** Mixed-use land percentage weighted by commercial intensity for live-work-play cafe locations

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Mixed-use zones with commercial activity create all-day cafe demand from residents and workers alike.

**Decision justification:** Captures live-work-play zones with all-day demand; no direct redundancy and low implementation risk.

**Code:**
```python
df['mixed_use_cafe_appeal'] = (df['lu_mixed_use_pct'].fillna(0) * df['commercial_intensity'].fillna(0)).astype('float32')
```

**Dependencies:** `lu_mixed_use_pct, commercial_intensity`

**Strengths:** Mixed-use zones do generate all-day foot traffic from diverse sources, Weighting by commercial_intensity adds demand signal, Targets live-work-play areas which are prime specialty cafe locations

**Weaknesses:** lu_mixed_use_pct is often zero or very low in Singapore - sparse signal expected, Multiplicative combination with commercial_intensity is partially redundant - mixed-use already implies commercial presence, Does not distinguish between mixed-use types (residential-retail vs office-retail)

**Redundancy:** none  · **Risk:** low  · **Confidence:** 0.6

### 🔧 `lunch_rush_potential` — REVISE  *(priority 2)*

**Description:** Midday transit activity combined with food venue scarcity indicating lunch crowd opportunity

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** High midday foot traffic with limited food options indicates strong lunch-time cafe demand from office workers.

**Decision justification:** Strong concept but needs normalized inputs and should use arrivals not departures for midday presence.

**Code:**
```python
df['lunch_rush_potential'] = ((df['bus_taps_in_midday'].fillna(0) / (df['bus_taps_in_midday'].max() + 1) + df['gtfs_dep_midday'].fillna(0) / (df['gtfs_dep_midday'].max() + 1)) / (df['pc_cat_cafe_coffee'].fillna(0) + df['pc_cat_restaurant'].fillna(0) + 1)).astype('float32')
```

**Dependencies:** `bus_taps_in_midday, gtfs_dep_midday, pc_cat_cafe_coffee, pc_cat_restaurant`

**Strengths:** Combines midday transit activity with food venue scarcity - logical for lunch opportunity, Uses both bus and GTFS data for more complete transit picture, Denominator includes both cafes and restaurants for realistic competition assessment

**Weaknesses:** bus_taps_in_midday and gtfs_dep_midday have different units/scales - raw addition is meaningless without normalization, Midday departures measure people leaving, not arriving - may inversely correlate with lunch crowd presence, Industrial areas with bus routes but no food will score high despite being poor cafe locations

**Redundancy:** none  · **Risk:** medium  · **Confidence:** 0.55

### ✅ `mrt_exit_cafe_opportunity` — KEEP  *(priority 2)*

**Description:** MRT exit presence combined with cafe gap indicating high-traffic underserved locations

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** MRT exits with cafe gaps represent prime locations for capturing commuter foot traffic with specialty coffee.

**Decision justification:** Actionable signal for transit-node site selection; sparse but high-value where non-zero; no redundancy.

**Code:**
```python
df['mrt_exit_cafe_opportunity'] = (df['mrt_exit_count'].fillna(0) * np.maximum(0, df['gap_cafe_coffee'].fillna(0))).astype('float32')
```

**Dependencies:** `mrt_exit_count, gap_cafe_coffee`

**Strengths:** MRT exits are high-value locations for grab-and-go coffee, Combining with cafe gap identifies specific underserved transit nodes, Actionable for site selection near specific MRT stations

**Weaknesses:** np.maximum(0, gap_cafe_coffee) clips negative gaps but gap_cafe_coffee methodology may already handle this, mrt_exit_count is sparse - most hexes have 0 exits, making this feature mostly zeros, Does not account for exit quality - underground vs street-level, pedestrian flow direction

**Redundancy:** none  · **Risk:** low  · **Confidence:** 0.65

### 🔧 `specialty_cafe_competition_gap` — REVISE  *(priority 3)*

**Description:** Ratio of office workers to existing cafes indicating underserved specialty cafe market

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** High office count with few cafes signals unmet demand for specialty coffee among young professionals.

**Decision justification:** Useful office-to-cafe ratio concept but should incorporate spatial context from neighboring hexes to avoid false positives.

**Code:**
```python
df['specialty_cafe_competition_gap'] = (df['pc_cat_business_office'].fillna(0) / (df['pc_cat_cafe_coffee'].fillna(0) + df['gap_cafe_coffee'].clip(lower=0).fillna(0) * 0.5 + 1)).astype('float32')
```

**Dependencies:** `pc_cat_business_office, pc_cat_cafe_coffee`

**Strengths:** Simple interpretable ratio of demand proxy to supply, The +1 denominator correctly handles zero-cafe hexes, Identifies underserved office areas which is actionable for site selection

**Weaknesses:** Assumes linear relationship between office count and cafe demand - ignores office size/employee density, Does not account for nearby hexes' cafes - a hex with 0 cafes but 10 cafes in adjacent hex shows as underserved, Existing gap_cafe_coffee already captures cafe undersupply using more sophisticated population-based methodology

**Redundancy:** gap_cafe_coffee  · **Risk:** low  · **Confidence:** 0.45

### 🔧 `young_professional_residential_proxy` — REVISE  *(priority 4)*

**Description:** Non-HDB residential share combined with working-age population as proxy for young professional residents

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Non-HDB housing with working-age residents indicates higher-income young professionals who prefer specialty cafes.

**Decision justification:** Good concept but fillna(1) masks data gaps; should use explicit missing handling and narrower age band.

**Code:**
```python
df['young_professional_residential_proxy'] = (np.where(df['pop_hdb_share'].isna(), np.nan, (1 - df['pop_hdb_share'])) * df['pop_15_64'].fillna(0)).astype('float32')
```

**Dependencies:** `pop_hdb_share, pop_15_64`

**Strengths:** Non-HDB as affluence proxy is reasonable for Singapore context, Working-age population filter adds demographic relevance, Simple and interpretable calculation

**Weaknesses:** pop_hdb_share fillna(1) means missing data defaults to 100% HDB, yielding zero - may mask data gaps, Conflates condo residents with landed property owners - very different demographics, pop_15_64 is too broad - includes 60-year-olds who are not 'young professionals'

**Redundancy:** pop_non_hdb  · **Risk:** low  · **Confidence:** 0.5

### ❌ `afterwork_vibrancy` — REJECT  *(priority None)*

**Description:** Evening transit activity weighted by bar and entertainment presence indicating after-work social zones

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Areas with evening transit activity and nightlife attract young professionals for after-work socializing at cafes.

**Decision justification:** Specialty cafes close before evening rush; existing vibrancy_index already captures this with better methodology.

**Code:**
```python
df['afterwork_vibrancy'] = ((df['bus_taps_out_pm'].fillna(0) + df['gtfs_dep_pm'].fillna(0)) * (1 + df['pc_cat_bar_nightlife'].fillna(0) * 0.1)).astype('float32')
```

**Dependencies:** `bus_taps_out_pm, gtfs_dep_pm, pc_cat_bar_nightlife`

**Strengths:** Targets evening economy which is distinct from daytime office demand, Multiplicative weighting with nightlife presence adds relevant context, PM transit captures commuter outflow timing well

**Weaknesses:** The 0.1 multiplier on bar_nightlife is arbitrary and untested - why not 0.05 or 0.2?, Specialty cafes typically close by 6-8pm - afterwork vibrancy may be irrelevant for the stated use case, Existing vibrancy_index already captures evening activity patterns more comprehensively

**Redundancy:** vibrancy_index  · **Risk:** low  · **Confidence:** 0.4

### ❌ `coworking_proximity_score` — REJECT  *(priority None)*

**Description:** Density of business offices in walkable commercial zones indicating coworking and freelancer presence

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Walkable commercial areas with offices attract freelancers and remote workers who frequent specialty cafes.

**Decision justification:** Misleading name (not coworking-specific), triple multiplication yields sparse output, and largely redundant with commercial_intensity.

**Code:**
```python
df['coworking_proximity_score'] = (df['pc_cat_business_office'].fillna(0) * df['lu_commercial_pct'].fillna(0) / 100 * df['walkability_score'].fillna(0) / 100).astype('float32')
```

**Dependencies:** `pc_cat_business_office, lu_commercial_pct, walkability_score`

**Strengths:** Three-way interaction captures walkable commercial office zones well, Targets freelancer/remote worker segment which is high-value for specialty cafes, All three inputs are meaningful and complementary

**Weaknesses:** pc_cat_business_office counts all offices, not specifically coworking spaces - misleading feature name, Triple multiplication means any zero input kills the signal entirely - very sparse output expected, Existing commercial_intensity already captures commercial zone density; this adds marginal value

**Redundancy:** commercial_intensity  · **Risk:** low  · **Confidence:** 0.5

### ❌ `daytime_population_estimate` — REJECT  *(priority None)*

**Description:** Estimated daytime population combining residents, office workers proxy, and transit inflows

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Daytime population threshold is a key constraint; this estimates actual foot traffic potential during business hours.

**Decision justification:** Arbitrary magic numbers undermine validity; existing wp_pop provides more rigorous workplace population estimates.

**Code:**
```python
df['daytime_population_estimate'] = (df['pop_resident'].fillna(0) * 0.3 + df['pc_cat_business_office'].fillna(0) * 50 + df['daily_train_taps'].fillna(0) * 0.1 + df['daily_bus_taps'].fillna(0) * 0.1).astype('float32')
```

**Dependencies:** `pop_resident, pc_cat_business_office, daily_train_taps, daily_bus_taps`

**Strengths:** Attempts to solve the critical daytime vs resident population problem, Combines multiple demand signals (residents, offices, transit), Directly addresses a stated constraint in the use case

**Weaknesses:** Magic numbers (0.3, 50, 0.1, 0.1) are completely arbitrary - 50 employees per office POI is unsupported, Transit taps are double-counted if someone takes bus then train, wp_pop (workplace population) already exists and is likely more accurate than this heuristic

**Redundancy:** wp_pop  · **Risk:** medium  · **Confidence:** 0.4

### ❌ `office_transit_synergy` — REJECT  *(priority None)*

**Description:** Combined score of office density and transit accessibility indicating young professional commuter appeal

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Young professionals cluster near offices with good transit; this captures locations where both factors align for cafe demand.

**Decision justification:** Directly redundant with existing syn_office_x_transit which already captures this interaction pattern.

**Code:**
```python
df['office_transit_synergy'] = ((df['pc_cat_business_office'].fillna(0) / (df['pc_cat_business_office'].fillna(0).max() + 1)) * (df['transit_score'].fillna(0) / 100)).astype('float32')
```

**Dependencies:** `pc_cat_business_office, transit_score`

**Strengths:** Captures the intersection of two key demand drivers for specialty cafes - office workers and transit accessibility, Normalization approach prevents extreme values from dominating, Directly addresses the stated use case of young professional targeting

**Weaknesses:** Highly redundant with existing syn_office_x_transit which already captures office-transit interaction, Max-based normalization is unstable across data updates - a single outlier hex changes all values, Multiplicative combination means zero in either input yields zero output, losing partial signal

**Redundancy:** syn_office_x_transit  · **Risk:** low  · **Confidence:** 0.35

### ❌ `premium_location_indicator` — REJECT  *(priority None)*

**Description:** HDB resale price proxy for area affluence indicating spending power for specialty coffee

**Type:** derive  · **Scale:** hex9  · **Dtype:** float32

**Rationale:** Higher property values indicate affluent areas where residents can afford premium specialty coffee.

**Decision justification:** Minimal value over raw hdb_resale_4r_median_psm; fails in non-HDB premium areas like CBD.

**Code:**
```python
df['premium_location_indicator'] = (df['hdb_resale_4r_median_psm'].fillna(0) / (df['hdb_resale_4r_median_psm'].fillna(0).median() + 1)).astype('float32')
```

**Dependencies:** `hdb_resale_4r_median_psm`

**Strengths:** HDB resale prices are a strong affluence signal in Singapore, Median-based normalization is more robust than max-based, Simple and interpretable

**Weaknesses:** Only uses 4-room HDB prices - excludes areas with predominantly 3-room or 5-room flats, HDB prices are irrelevant in non-HDB areas (CBD, Sentosa) - these will show as zero despite being premium, Existing hdb_resale_4r_median_psm provides the raw signal; this normalization adds little value

**Redundancy:** hdb_resale_4r_median_psm  · **Risk:** low  · **Confidence:** 0.35

## Added to atlas

| Feature | dtype | non-null | median | min | max |
|---|---|---|---|---|---|
| `specialty_cafe_competition_gap` | float32 | 7,318 | 0.0 | 0.0 | 54.66666793823242 |
| `lunch_rush_potential` | float32 | 7,318 | 0.0 | 0.0 | 0.8156130909919739 |
| `young_professional_residential_proxy` | float32 | 7,318 | 0.01437666267156601 | 0.0 | 1478.3905029296875 |
| `mixed_use_cafe_appeal` | float32 | 7,318 | 0.0 | 0.0 | 0.33055049180984497 |
| `mrt_exit_cafe_opportunity` | float32 | 7,318 | 0.0 | 0.0 | 10.0 |

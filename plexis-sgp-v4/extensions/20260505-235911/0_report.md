# Atlas Extender Report

**Use case:** For Singapore hotels and hospitality businesses, identify and engineer the features that most impact daily occupancy rates and room pricing. Consider all dimensions: spatial location (proximity to attractions, MRT, business districts, airport), temporal patterns (day-of-week, public holidays, school holidays, seasonal demand), event-driven demand (F1 race weekend, National Day, large conferences, concerts, exhibitions, religious festivals like Lunar New Year and Deepavali), weather conditions (monsoon season, rainfall, temperature), and competitive landscape (nearby hotels, room supply, ARR benchmarks). The output should help hoteliers price dynamically and understand demand drivers.
**Generated:** 20260505-235911
**Atlas version (base):** 4.8.0
**New version:** 4.8.1

## Summary

| | Count |
|---|---|
| Proposed | 10 |
| KEEP | 1 |
| REVISE | 3 |
| REJECT | 6 |
| **Successfully added** | **4** |
| Build-failed | 0 |

## Use Case Spec

```json
{
  "use_case": "Engineer features that predict hotel occupancy rates and optimal room pricing by analyzing spatial, temporal, event-driven, weather, and competitive factors across Singapore's hospitality landscape",
  "target_variable": "daily_occupancy_rate_and_average_room_rate",
  "decision_type": "prediction",
  "scale": "place",
  "key_concepts": [
    "proximity to tourist attractions and MRT stations",
    "distance to CBD and Changi Airport",
    "event calendar impact including F1 GP and MICE events",
    "seasonal and holiday demand patterns",
    "monsoon weather and rainfall effects",
    "competitive hotel density and room supply",
    "day-of-week and public holiday temporal cycles"
  ],
  "constraints": [
    "pricing must comply with Singapore Tourism Board guidelines",
    "data availability limited to publicly observable hotel listings",
    "event calendars require integration with external sources"
  ],
  "evaluation_metric": "MAPE on occupancy prediction and revenue per available room (RevPAR) accuracy",
  "decision_horizon_months": 3,
  "stakeholder": "hotel revenue managers and hospitality asset owners"
}
```

## Per-feature decisions

### 🔧 `is_branded_hotel` — REVISE  *(priority 1)*

**Description:** Boolean indicating if hotel belongs to a recognized international brand chain

**Type:** derive  · **Scale:** place  · **Dtype:** bool

**Rationale:** Branded hotels have different pricing power and occupancy patterns versus independent properties

**Decision justification:** Brand affiliation is valuable but needs validation against known chains rather than just non-empty check.

**Code:**
```python
df['is_branded_hotel'] = (df['brand'].str.lower().str.contains('marriott|hilton|hyatt|accor|ihg|shangri|mandarin|fairmont|ritz|westin|sheraton|novotel|ibis|holiday inn|crowne|intercontinental', na=False) & (df['plexis_category'] == 'hotel_hospitality')).astype(bool)
```

**Dependencies:** `brand, plexis_category`

**Strengths:** Brand affiliation genuinely affects pricing power, distribution channels, and demand stability, Leverages existing brand column with minimal computation

**Weaknesses:** brand column quality unknown — does 'brand' contain 'Marriott' or 'JW Marriott Singapore'? Normalization needed, Code checks brand.notna() & brand != '' but doesn't validate against known hotel brands — 'ABC Pte Ltd' would pass, plexis_category filter assumes perfect categorization — miscategorized serviced apartments would be excluded

**Redundancy:** none  · **Risk:** medium  · **Confidence:** 0.55

### 🔧 `is_orchard_belt` — REVISE  *(priority 2)*

**Description:** Boolean indicating if hotel is within Orchard Road shopping belt area

**Type:** derive  · **Scale:** place  · **Dtype:** bool

**Rationale:** Orchard Road hotels command premium rates due to shopping tourism and retail accessibility

**Decision justification:** Valuable micro-market segmentation but bounding box excludes key Tanglin hotels; expanding coordinates to capture full Orchard market.

**Code:**
```python
df['is_orchard_belt'] = ((df['latitude'] >= 1.295) & (df['latitude'] <= 1.312) & (df['longitude'] >= 103.820) & (df['longitude'] <= 103.848)).astype(bool)
```

**Dependencies:** `latitude, longitude`

**Strengths:** Orchard Road is a distinct hotel micro-market with documented rate premiums, Binary flag enables clean segmentation for pricing models

**Weaknesses:** Hardcoded bounding box (1.298-1.310, 103.825-103.845) is arbitrary — excludes Tanglin hotels (Shangri-La, St. Regis) which are considered Orchard market, No validation that box actually captures Orchard Road hotels vs. nearby residential areas, Boolean loses gradient information — hotel at edge of Orchard vs. center of ION treated identically

**Redundancy:** none  · **Risk:** medium  · **Confidence:** 0.5

### ✅ `is_sentosa_area` — KEEP  *(priority 3)*

**Description:** Boolean indicating if hotel is located in or near Sentosa resort island

**Type:** derive  · **Scale:** place  · **Dtype:** bool

**Rationale:** Sentosa hotels have distinct leisure-driven demand patterns and seasonal pricing dynamics

**Decision justification:** Sentosa's geographic isolation and distinct leisure demand patterns justify binary flag despite low variance.

**Code:**
```python
df['is_sentosa_area'] = ((df['latitude'] >= 1.245) & (df['latitude'] <= 1.260) & (df['longitude'] >= 103.815) & (df['longitude'] <= 103.865)).astype(bool)
```

**Dependencies:** `latitude, longitude`

**Strengths:** Sentosa hotels have genuinely distinct demand patterns (leisure, weekend-heavy, event-driven), Clean geographic isolation makes binary classification defensible

**Weaknesses:** Bounding box (1.245-1.260, 103.815-103.865) may include Harbourfront hotels which have different demand profile than island resorts, Misses Sentosa Cove eastern edge hotels if coordinates are slightly off, Only ~15-20 hotels in Sentosa — feature will be extremely sparse with near-zero variance

**Redundancy:** none  · **Risk:** low  · **Confidence:** 0.6

### 🔧 `rating_premium_score` — REVISE  *(priority 4)*

**Description:** Normalized rating score indicating quality tier for pricing differentiation

**Type:** derive  · **Scale:** place  · **Dtype:** float32

**Rationale:** Higher-rated hotels can command premium rates; normalized score enables pricing tier segmentation

**Decision justification:** Useful quality tier signal but formula should handle full 1-5 range and avoid arbitrary fillna; using min-max normalization.

**Code:**
```python
df['rating_premium_score'] = ((df['rating'].clip(1, 5) - 1.0) / 4.0).where(df['rating'].notna(), np.nan).astype('float32')
```

**Dependencies:** `rating`

**Strengths:** Rating-based quality tiers are standard in hotel revenue management, Normalization to 0-1 range enables direct use in pricing models

**Weaknesses:** fillna(3.5) assumes missing ratings are average — but missing often means new/unlisted properties which skew higher or lower, Formula (rating - 3.0) / 2.0 assumes 3.0-5.0 range but Google ratings can be 1.0-5.0; a 2.5-rated hotel gets negative score before clip, Does not account for review count — a 4.8 with 5 reviews vs. 4.5 with 2000 reviews have different reliability

**Redundancy:** rating  · **Risk:** low  · **Confidence:** 0.5

### ❌ `daily_weather_rainfall_mm` — REJECT  *(priority None)*

**Description:** Daily rainfall amount in millimeters affecting tourist outdoor activities

**Type:** external  · **Scale:** place  · **Dtype:** float32

**Rationale:** Monsoon rainfall impacts tourist behavior and can affect occupancy especially for leisure-focused hotels

**Decision justification:** Temporal mismatch between daily weather and advance pricing decisions; place-level granularity nonsensical for Singapore's size.

**Strengths:** Weather does impact tourist behavior and last-minute booking patterns, NEA provides reliable weather data for Singapore

**Weaknesses:** Place-level rainfall makes no sense — Singapore is 50km across; NEA provides station-level data, not hotel-level, Rainfall affects same-day walk-ins but hotel pricing is set days/weeks ahead — temporal mismatch, Monsoon seasonality already captured by booking date features; daily noise adds little predictive value

**Redundancy:** none  · **Risk:** medium  · **Confidence:** 0.25

### ❌ `dist_changi_airport_km` — REJECT  *(priority None)*

**Description:** Euclidean distance from hotel location to Changi Airport in kilometers

**Type:** derive  · **Scale:** place  · **Dtype:** float32

**Rationale:** Airport proximity is critical for business travelers and transit tourists affecting occupancy patterns

**Decision justification:** Redundant with existing pull_airport feature which likely already captures airport accessibility.

**Code:**
```python
df['dist_changi_airport_km'] = (np.sqrt((df['latitude'] - 1.3644) ** 2 + (df['longitude'] - 103.9915) ** 2) * 111.32).astype('float32')
```

**Dependencies:** `latitude, longitude`

**Strengths:** Airport proximity is a genuine demand driver for transit hotels and business travelers, Simple, deterministic calculation with no external dependencies

**Weaknesses:** Euclidean distance ignores actual travel time — hotels near ECP vs. those requiring PIE detour have same distance but different accessibility, Single hardcoded coordinate (1.3644, 103.9915) doesn't account for multiple terminals spread over ~3km, 111.32 km/degree approximation introduces ~0.3% error at Singapore's latitude; minor but sloppy

**Redundancy:** pull_airport  · **Risk:** low  · **Confidence:** 0.6

### ❌ `dist_marina_bay_km` — REJECT  *(priority None)*

**Description:** Euclidean distance from hotel location to Marina Bay CBD center in kilometers

**Type:** derive  · **Scale:** place  · **Dtype:** float32

**Rationale:** CBD proximity drives corporate demand and premium pricing for business hotels

**Decision justification:** Redundant with existing pull_cbd feature; single-point CBD representation is too simplistic.

**Code:**
```python
df['dist_marina_bay_km'] = (np.sqrt((df['latitude'] - 1.2816) ** 2 + (df['longitude'] - 103.8636) ** 2) * 111.32).astype('float32')
```

**Dependencies:** `latitude, longitude`

**Strengths:** CBD proximity is a validated predictor of corporate hotel demand and ADR, Computationally trivial with existing lat/lng columns

**Weaknesses:** Single point (1.2816, 103.8636) poorly represents CBD which spans Raffles Place to Tanjong Pagar — ~2km spread, Euclidean distance meaningless for hotels separated by Marina Bay water body requiring bridge/tunnel access, Does not differentiate between CBD-facing (premium views) vs. CBD-adjacent (no view premium)

**Redundancy:** pull_cbd  · **Risk:** low  · **Confidence:** 0.55

### ❌ `event_calendar_impact` — REJECT  *(priority None)*

**Description:** Daily event intensity score from F1 GP, MICE events, and major conventions

**Type:** external  · **Scale:** place  · **Dtype:** float32

**Rationale:** Major events like F1 GP and MICE conventions cause demand spikes requiring dynamic pricing adjustments

**Decision justification:** High implementation risk with no unified API; temporal and spatial assignment logic unspecified.

**Strengths:** F1 GP and MICE events cause documented 2-3x rate spikes — high signal value, Temporal feature adds dimension not captured by static location features

**Weaknesses:** External source 'singapore_events_calendar_api' does not exist as a unified API — would require scraping STB, Sistic, MBS, etc., Description says 'daily' but hotel pricing is set weeks in advance — need forward-looking calendar, not current-day, Place-level assignment unclear — how does a Marina Bay event impact a Geylang hotel? Distance decay function unspecified

**Redundancy:** none  · **Risk:** high  · **Confidence:** 0.3

### ❌ `hotel_competitive_density` — REJECT  *(priority None)*

**Description:** Count of hotel/hospitality places within the same hex8 area indicating local competitive pressure

**Type:** external  · **Scale:** place  · **Dtype:** float32

**Rationale:** Competitive hotel density directly impacts occupancy rates and pricing power; requires room count data not just place counts

**Decision justification:** External source is vague, description contradicts rationale, and mg_hotel_hospitality_pressure_400m already provides competitive density signal.

**Strengths:** Room inventory data provides capacity-weighted competition signal that place counts cannot capture, Directly actionable for revenue management and pricing strategy decisions

**Weaknesses:** External source 'hotel_room_inventory_database' is vague — no clear API or data provider specified; likely requires expensive commercial data (STR, OTA scraping), Description says 'count of hotel/hospitality places' but rationale mentions 'room count data' — inconsistent specification, Hex8 aggregation may be too coarse for competitive analysis; hotels 500m apart in different hex8s would be missed

**Redundancy:** mg_hotel_hospitality_pressure_400m  · **Risk:** high  · **Confidence:** 0.35

### ❌ `review_volume_indicator` — REJECT  *(priority None)*

**Description:** Log-transformed review count as proxy for hotel popularity and booking volume

**Type:** derive  · **Scale:** place  · **Dtype:** float32

**Rationale:** Review volume correlates with booking frequency and can indicate demand levels for pricing

**Decision justification:** Redundant with existing review_bucket; source ambiguity and fillna(0) conflation issues reduce reliability.

**Code:**
```python
df['review_volume_indicator'] = np.log1p(df['reviews_count'].fillna(0)).astype('float32')
```

**Dependencies:** `reviews_count`

**Strengths:** Log-transform handles heavy-tailed distribution appropriately, Review count is a reasonable proxy for booking volume and property maturity

**Weaknesses:** reviews_count source unclear — Google reviews? Booking.com? TripAdvisor? Each has different coverage and bias, New hotels with excellent occupancy but few reviews will be systematically undervalued, fillna(0) then log1p means missing data treated same as genuinely zero-review properties

**Redundancy:** review_bucket  · **Risk:** low  · **Confidence:** 0.65

## Added to atlas

| Feature | dtype | non-null | median | min | max |
|---|---|---|---|---|---|
| `is_orchard_belt` | bool | 190,591 | 0.0 | 0.0 | 1.0 |
| `is_sentosa_area` | bool | 190,591 | 0.0 | 0.0 | 1.0 |
| `is_branded_hotel` | bool | 190,591 | 0.0 | 0.0 | 1.0 |
| `rating_premium_score` | float32 | 109,400 | 0.875 | 0.0 | 1.0 |

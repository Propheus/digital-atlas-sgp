# Digital Atlas SGP - Model Diagnosis & Improvement Plan

## Current Performance
- Mean R2: 0.597, Mean MAE: 3.38, MAPE: 50.4%
- Model is 2.8x better than naive baseline
- Best: Beauty (0.83), Convenience (0.77), Business (0.75)
- Worst: Hospitality (0.25), Bar (0.32), Culture (0.43)

---

## PROBLEM 1: Data Bugs (Critical)

**Dwelling percentages exceed 100%**
- Condominiums_pct: 22 subzones > 100% (max 1100%!)
- Landed Properties_pct: 2 subzones > 100%
- Others_pct: 2 subzones > 100%

This means the dwelling type data is using TOTAL DWELLING UNITS as denominator
but the population count as numerator (or vice versa). The percentages are
computed against the wrong base.

**Fix:** Recompute dwelling percentages using dwelling counts from the
dwellings_subzone file, not population counts.

**Impact:** High - corrupts 30% of demographic features

---

## PROBLEM 2: High Null Rate (30-35%)

- 30% nulls across ALL demographic features (age, gender, dwelling)
- 35% nulls in ALL property features (HDB prices)

The 30% nulls in demographics correspond to ~100 subzones that are
non-residential (industrial, military, nature, water). These subzones
genuinely have 0 population, so the null is correct - but filling with 0
and treating them the same as residential subzones hurts the model.

**Fix:**
1. Add a binary feature: is_residential (pop > 100)
2. Add a binary feature: is_viable (has commercial zoning AND population)
3. For non-viable subzones, set all predictions to 0 (dont train on them)
4. For HDB nulls, impute from planning area average

**Impact:** Medium-high - model currently wastes capacity on 100 subzones
where places cant meaningfully exist

---

## PROBLEM 3: Dense Subzones Dominate Error (Structural)

| Density Tier | Subzones | MAE |
|---|---|---|
| Sparse (<10) | 20 | 0.24 |
| Low (10-50) | 46 | 0.60 |
| Medium (50-200) | 141 | 1.50 |
| Dense (200+) | 119 | **5.66** |

The model struggles with dense subzones (Aljunied: MAE=44, Geylang East: MAE=31).
These are places with 1000-1800 POIs. The prediction error scales with count.

**Fix:**
1. Train on log-counts (already doing this) but also normalize by subzone total
2. Predict PROPORTIONS instead of counts: "what % should be cafes?"
3. Or use Poisson/NB loss instead of MSE (count data is not Gaussian)

**Impact:** High - top 10 worst subzones account for 40% of total error

---

## PROBLEM 4: Category Correlation (Structural)

Several categories are highly correlated (r > 0.85):
- Services <-> Shopping Retail (0.92)
- Business <-> Services (0.90)  
- Business <-> Office Workspace (0.89)
- Beauty <-> Convenience (0.89)
- Beauty <-> Cafe (0.87)

This means masking one category when its twin is visible is too easy.
The model just copies the correlated category.

**Fix:**
1. Mask correlated categories TOGETHER (if mask cafe, also mask beauty)
2. Or reduce to ~15 super-categories to reduce redundancy
3. Or use correlation-aware masking: higher mask prob for correlated pairs

**Impact:** Medium - inflates R2 for easy categories

---

## PROBLEM 5: Missing Demand Signal (Critical Gap)

The model has SUPPLY features (what exists) and PHYSICAL features
(roads, buildings, zoning) but almost NO DEMAND signal:

- No foot traffic (MRT passenger volumes need API key)
- No spending data (no commercial revenue)
- No mobile phone movement data
- No event/tourism flow

For Hospitality (R2=0.25) and Bar & Nightlife (R2=0.32), demand is
the primary driver. Hotels cluster around tourist/business demand,
bars cluster around nightlife demand. Physical features alone cant
predict these.

**Fix:**
1. Get LTA passenger volume data (API key needed)
2. Use hotel room count as tourism demand proxy (already have it)
3. Add "distance to CBD" as centrality measure
4. Add "distance to key destinations" (Orchard, Marina Bay, Clarke Quay)
5. Use review_count as demand proxy (more reviews = more foot traffic)

**Impact:** High - would significantly improve Hospitality and Bar

---

## PROBLEM 6: 105 Non-Viable Subzones Pollute Training

105 subzones (32%) are nature reserves, water catchment, military,
industrial parks with zero population. The model tries to learn
their composition but they dont follow urban composition rules.

**Fix:**
1. Exclude from training (train on ~227 viable subzones only)
2. OR add viability features and let model learn to predict 0

**Impact:** Medium - cleaner training signal, but fewer samples

---

## PROBLEM 7: No Interaction Features

The model takes 178 raw features but doesnt see interactions like:
- Population x Commercial Zoning = demand potential
- MRT proximity x Place density = transit-oriented development
- HDB price x Age distribution = purchasing power profile

**Fix:** Add engineered interaction features:
- demand_potential = pop_density * lu_commercial_pct
- transit_density_interaction = mrt_stations_1km * bus_density
- affluence_score = median_hdb_psf * (1 - hdb_1_2_room_pct/100)
- family_score = age_0_14_pct * dwelling_hdb_4_5_room_pct
- commercial_intensity = lu_commercial_pct * road_density

**Impact:** Medium - helps model see non-linear relationships

---

## PROBLEM 8: Model May Be Too Complex for 332 Samples

A GCN-MLP with ~50K parameters on 332 samples is borderline.
Maybe a simpler model would generalize better.

**Test:** Compare with:
1. XGBoost/LightGBM (gradient boosted trees)
2. Simple MLP without GNN
3. Linear regression baseline
4. GNN-only (no MLP encoder)

If XGBoost beats GCN-MLP, the graph structure isnt helping much.

**Impact:** Unknown - needs experiment

---

## IMPROVEMENT PRIORITY

| Priority | Fix | Expected R2 Gain | Effort |
|---|---|---|---|
| P0 | Fix dwelling percentage bugs | +0.02-0.05 | 1 hour |
| P0 | Exclude non-viable subzones from training | +0.03-0.08 | 1 hour |
| P0 | Predict proportions instead of counts | +0.05-0.10 | 2 hours |
| P1 | Add interaction features | +0.02-0.05 | 2 hours |
| P1 | Correlation-aware masking | +0.02-0.03 | 1 hour |
| P1 | Add centrality/destination features | +0.03-0.05 | 2 hours |
| P2 | Compare with XGBoost baseline | clarity | 2 hours |
| P2 | Poisson/NB loss | +0.02-0.05 | 2 hours |
| P3 | Get LTA passenger volumes | +0.05-0.10 | needs API key |

Expected total gain: R2 from 0.60 to ~0.75-0.80


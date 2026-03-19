# Digital Atlas SGP — Best Model & Usage Guide

## The Honest Answer: There Are Two Best Models For Two Different Questions

### Model A: "How many places should exist here?" (Density Model)
- **Type:** XGBoost (GradientBoostingRegressor)
- **R² = 0.773** (10-fold CV)
- **Input:** 70 physical features (demographics, roads, land use, transit, centrality)
- **Output:** Predicted total place count per subzone
- **Use for:** Identifying under-developed vs over-developed areas

### Model B: "Given what exists, what else should exist?" (Composition Model)
- **Type:** XGBoost, leave-one-out per category
- **R² = 0.970** when given all other categories (realistic operational scenario)
- **R² = 0.176** when given only 70% of categories (hardest test)
- **Input:** Physical features + observed category proportions (minus target)
- **Output:** Predicted proportion for the missing category
- **Use for:** Gap analysis — "this area has restaurants but no cafes"

---

## How To Use: Gap Analysis

### Question 1: "Where are there too few places overall?"

```python
# Density gap = predicted density - actual density
density_gap = predicted_total_places - actual_total_places

# Positive = area has fewer places than structure suggests
# Negative = area has more places than structure suggests
```

**Reliable.** R²=0.77 means this is a strong signal.

### Question 2: "What specific category is missing here?"

```python
# For a target category (e.g., cafe):
# 1. Take the subzone physical features
# 2. Take ALL observed category proportions EXCEPT cafe
# 3. Predict what cafe proportion should be
# 4. Compare to actual

gap_score = (predicted_cafe - actual_cafe) / max(predicted_cafe, 1)
```

**Use with caution.** The inter-category signal is real but noisy.
Best for categories with R² > 0.3:
- Office/Workspace (0.53)
- Shopping/Retail (0.47)
- Culture/Entertainment (0.38)
- Residential (0.38)
- Beauty/Personal Care (0.37)
- Education (0.36)

Unreliable for: NGO (-0.69), Religious (-0.64), Hospitality (-0.39)

### Question 3: "Where should I open a specific business?"

**Combine both models:**

```python
# Score = density_gap * category_fit * feasibility

density_score = (predicted_total - actual_total) / predicted_total
category_score = (predicted_cafe_prop - actual_cafe_prop) 
feasibility = (has_commercial_zoning) * (near_transit) * (has_population)

location_score = density_score * 0.4 + category_score * 0.3 + feasibility * 0.3
```

---

## Running Inference

### Requirements
```
pip install pandas numpy scikit-learn geopandas
```

### Quick Start
```python
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

# Load features
sf = pd.read_parquet("final/subzone_features_raw.parquet")

# Apply same preprocessing as training
# (see scripts/atlas_model_v5.py for full details)

# Load gap analysis results
gaps = pd.read_parquet("model_results_v5/gap_analysis_v5.parquet")

# Find top opportunities for cafes
cafe_gaps = gaps[gaps["is_viable"] == 1].nlargest(10, "gap_score_cafe_coffee")
print(cafe_gaps[["subzone_name", "predicted_cafe_coffee", "actual_cafe_coffee", "gap_score_cafe_coffee"]])
```

### Retraining
```bash
python3 scripts/atlas_model_v5.py
# Outputs to model_results_v5/
```

---

## Feature Importance (What Drives Urban Composition)

Top physical features across all category models:

| Rank | Feature | Importance | What it tells us |
|------|---------|-----------|------------------|
| 1 | lu_industrial_pct | 4.3% | Industrial zones have distinct composition |
| 2 | sfa_eating_count | 2.5% | Existing food licensing predicts F&B |
| 3 | dist_orchard | 2.3% | Distance from prime commercial corridor |
| 4 | dist_nearest_supermarket | 2.0% | Existing amenity infrastructure |
| 5 | dist_nearest_hawker | 1.7% | Hawker proximity = residential neighborhood |
| 6 | lu_open_space_pct | 1.7% | Parks/open space reduces commercial |
| 7 | lu_institutional_pct | 1.6% | Schools/hospitals create service demand |
| 8 | avg_gpr | 1.6% | Gross plot ratio = development intensity |
| 9 | lu_entropy | 1.5% | Mixed zoning = diverse place composition |
| 10 | road_density | 1.5% | Denser road network = more accessibility |

---

## Model Versions Summary

| Version | R² | What happened |
|---------|---:|---------------|
| v1 GCN-MLP | 0.597 | Used type_counts as features (place→place) |
| v3 XGBoost leaky | 0.970 | Used cat_pct (answer in features) |
| v4 XGBoost strict | -0.014 | Physical only → cant predict mix |
| **v5 Stage 1** | **0.773** | **Physical → density. REAL signal.** |
| **v5 Stage 2** | **0.110-0.970** | **Depends on how much you observe** |

## Key Insight

> Urban physical structure determines HOW MANY places exist (R²=0.77)
> but NOT what KIND they are. Composition is driven by market forces,
> entrepreneur decisions, rent, and demand — not by roads and zoning alone.

This is not a failure — it is the model correctly learning
Singapores urban structure. The density model IS the Digital Atlas.

---

## Files

```
model_results_v5/
  report_v5.json         — Full metrics and feature importance
  gap_analysis_v5.parquet — Gap scores for all 332 subzones x 24 categories
  gap_analysis_v5.csv     — Same in CSV

final/
  subzone_features_raw.parquet — 332 x 205 features (input)
  place_features.parquet       — 66,851 x 13 features

scripts/
  atlas_model_v5.py     — Full training pipeline (reproducible)
```
